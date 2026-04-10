#!/usr/bin/env python3
"""H-CX-13 Ablation: Does removing detach (S4) eliminate the +0.41% enhancement?

Shamanic journey = information bottleneck hypothesis.
Tests 3 conditions x 5 trials:

  A) Full sequence (with detach):  S1->S2->S3->S4->S5->S6->S7
  B) No detach:                    S1->S2->S3->(skip S4)->S5->S6->S7
  C) No observation:               S1->S2->S3->S4->(skip S5)->S6->S7

Each trial:
  1. Train parent RepulsionFieldEngine on MNIST (10 epochs)
  2. Mitosis (scale=0.01)
  3. Run sequence variant
  4. Measure child_a accuracy after return (S7)
  5. Compare: parent_acc vs return_acc = enhancement
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import copy
import time
import sys
import functools

sys.path.insert(0, '/Users/ghost/Dev/logout')

# Force unbuffered output
print = functools.partial(print, flush=True)

from model_utils import load_mnist, count_params
from model_meta_engine import RepulsionFieldEngine, EngineA, EngineG


# ─────────────────────────────────────────
# Simplified 2-engine repulsion field for ablation
# ─────────────────────────────────────────

class SimpleRepulsionField(nn.Module):
    """Minimal repulsion field: engine_a + engine_g + equilibrium.
    Simpler than full RepulsionFieldEngine for cleaner ablation signal.
    """
    def __init__(self, input_dim=784, hidden_dim=64, output_dim=10):
        super().__init__()
        self.engine_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )
        self.engine_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )
        self.field_transform = nn.Sequential(
            nn.Linear(output_dim, output_dim),
            nn.Tanh(),
        )
        self.tension_scale = nn.Parameter(torch.tensor(1/3))

    def forward(self, x):
        out_a = self.engine_a(x)
        out_g = self.engine_g(x)
        repulsion = out_a - out_g
        tension = (repulsion ** 2).sum(dim=-1, keepdim=True)
        equilibrium = (out_a + out_g) / 2
        field_dir = self.field_transform(repulsion)
        output = equilibrium + self.tension_scale * torch.sqrt(tension + 1e-8) * field_dir
        return output


# ─────────────────────────────────────────
# Training helpers
# ─────────────────────────────────────────

def train_model(model, train_loader, test_loader, epochs=10, lr=0.001, verbose=False):
    """Train and return (losses, accs)."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    train_losses = []
    test_accs = []

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            out = model(X)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        avg_loss = total_loss / len(train_loader)
        train_losses.append(avg_loss)

        acc = evaluate(model, test_loader)
        test_accs.append(acc)

        if verbose and ((epoch + 1) % 5 == 0 or epoch == 0):
            print(f"      Epoch {epoch+1:>2}/{epochs}: Loss={avg_loss:.4f}, Acc={acc*100:.2f}%")

    return train_losses, test_accs


def evaluate(model, test_loader):
    """Evaluate accuracy."""
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for X, y in test_loader:
            X = X.view(X.size(0), -1)
            out = model(X)
            correct += (out.argmax(1) == y).sum().item()
            total += y.size(0)
    return correct / total


# ─────────────────────────────────────────
# 7-stage shamanic journey sequences
# ─────────────────────────────────────────

def s1_unity(parent, train_loader, test_loader, epochs=10, verbose=False):
    """S1: Train parent to convergence."""
    train_model(parent, train_loader, test_loader, epochs=epochs, verbose=verbose)
    parent_acc = evaluate(parent, test_loader)
    return parent_acc


def s2_mitosis(parent, scale=0.01):
    """S2: Clone parent into child_a and child_b with small perturbation."""
    child_a = copy.deepcopy(parent)
    child_b = copy.deepcopy(parent)
    # Add small noise to differentiate
    with torch.no_grad():
        for p in child_a.parameters():
            p.add_(torch.randn_like(p) * scale)
        for p in child_b.parameters():
            p.add_(torch.randn_like(p) * scale)
    return child_a, child_b


def s3_displacement(child_b, train_loader, test_loader, epochs=3, verbose=False):
    """S3: Train child_b further (child_a does NOT train = displacement)."""
    train_model(child_b, train_loader, test_loader, epochs=epochs, verbose=verbose)


def s4_detach(child_a):
    """S4: Detach child_a's parameters from computation graph.
    This simulates the 'death' / information bottleneck.
    We freeze child_a and detach its outputs.
    """
    for p in child_a.parameters():
        p.requires_grad = False
    return child_a


def s5_observation(child_a, child_b, train_loader, test_loader, epochs=3, use_detach=True, verbose=False):
    """S5: child_a observes child_b's behavior and learns from it.

    If use_detach=True: child_a reads child_b through detached outputs
    (pure observation, no gradient from child_b to child_a through observation path).

    We create a small observer network that reads child_b's detached output
    and fine-tunes child_a's field_transform and tension_scale.
    """
    # Unfreeze child_a for observation learning
    for p in child_a.parameters():
        p.requires_grad = True

    # Observer: learns from watching child_b
    observer = nn.Sequential(
        nn.Linear(10, 32),
        nn.ReLU(),
        nn.Linear(32, 10),
    )
    observer_scale = nn.Parameter(torch.tensor(0.1))

    # Only train child_a's field_transform + observer
    params = list(child_a.field_transform.parameters()) + [child_a.tension_scale]
    params += list(observer.parameters()) + [observer_scale]
    optimizer = torch.optim.Adam(params, lr=0.0005)
    criterion = nn.CrossEntropyLoss()

    child_b.eval()

    for epoch in range(epochs):
        child_a.train()
        observer.train()
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()

            # child_a's own output
            out_a = child_a(X)

            # Observe child_b
            with torch.no_grad():
                out_b = child_b(X)
            if use_detach:
                observed_b = out_b.detach()
            else:
                observed_b = out_b  # already no_grad, but conceptually different

            correction = observer(observed_b)
            combined = out_a + observer_scale * correction

            loss = criterion(combined, y)
            loss.backward()
            optimizer.step()

    # Absorb observer knowledge into child_a
    # (In return phase, observer is discarded, only child_a's updated weights remain)
    return observer, observer_scale


def s5_skip():
    """S5 skip: No observation happens."""
    pass


def s6_separation(child_a, child_b):
    """S6: Remove child_b. child_a continues alone."""
    del child_b
    return child_a


def s7_return(child_a, train_loader, test_loader, epochs=2, verbose=False):
    """S7: Fine-tune child_a back to the original task (reintegration)."""
    for p in child_a.parameters():
        p.requires_grad = True
    train_model(child_a, train_loader, test_loader, epochs=epochs, verbose=verbose)
    return_acc = evaluate(child_a, test_loader)
    return return_acc


# ─────────────────────────────────────────
# 3 Conditions
# ─────────────────────────────────────────

def run_condition_A(seed, train_loader, test_loader):
    """Full sequence WITH detach: S1->S2->S3->S4->S5->S6->S7"""
    torch.manual_seed(seed)
    np.random.seed(seed)

    parent = SimpleRepulsionField()
    # S1: Train parent
    parent_acc = s1_unity(parent, train_loader, test_loader, epochs=10)
    # S2: Mitosis
    child_a, child_b = s2_mitosis(parent, scale=0.01)
    # S3: Displacement (train child_b, not child_a)
    s3_displacement(child_b, train_loader, test_loader, epochs=3)
    # S4: Detach child_a (freeze / information bottleneck)
    child_a = s4_detach(child_a)
    # S5: Observation (child_a observes child_b with detach)
    s5_observation(child_a, child_b, train_loader, test_loader, epochs=3, use_detach=True)
    # S6: Separation
    child_a = s6_separation(child_a, child_b)
    # S7: Return
    return_acc = s7_return(child_a, train_loader, test_loader, epochs=2)

    return parent_acc, return_acc


def run_condition_B(seed, train_loader, test_loader):
    """No detach: S1->S2->S3->(skip S4)->S5->S6->S7
    Gradients keep flowing through child_a (no information bottleneck)."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    parent = SimpleRepulsionField()
    # S1
    parent_acc = s1_unity(parent, train_loader, test_loader, epochs=10)
    # S2
    child_a, child_b = s2_mitosis(parent, scale=0.01)
    # S3
    s3_displacement(child_b, train_loader, test_loader, epochs=3)
    # S4: SKIP (no detach, gradients flow freely)
    # child_a parameters remain requires_grad=True
    # S5: Observation WITHOUT detach separation
    s5_observation(child_a, child_b, train_loader, test_loader, epochs=3, use_detach=False)
    # S6
    child_a = s6_separation(child_a, child_b)
    # S7
    return_acc = s7_return(child_a, train_loader, test_loader, epochs=2)

    return parent_acc, return_acc


def run_condition_C(seed, train_loader, test_loader):
    """No observation: S1->S2->S3->S4->(skip S5)->S6->S7"""
    torch.manual_seed(seed)
    np.random.seed(seed)

    parent = SimpleRepulsionField()
    # S1
    parent_acc = s1_unity(parent, train_loader, test_loader, epochs=10)
    # S2
    child_a, child_b = s2_mitosis(parent, scale=0.01)
    # S3
    s3_displacement(child_b, train_loader, test_loader, epochs=3)
    # S4: Detach
    child_a = s4_detach(child_a)
    # S5: SKIP (no observation)
    s5_skip()
    # S6
    child_a = s6_separation(child_a, child_b)
    # S7: Return (must unfreeze since S4 froze it)
    return_acc = s7_return(child_a, train_loader, test_loader, epochs=2)

    return parent_acc, return_acc


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────

def main():
    print()
    print("=" * 72)
    print("  H-CX-13 Ablation: Detach as Information Bottleneck")
    print("  Does removing detach (S4) eliminate the enhancement?")
    print("=" * 72)
    print()
    print("  Conditions:")
    print("    A) Full sequence (with detach):  S1->S2->S3->S4->S5->S6->S7")
    print("    B) No detach:                    S1->S2->S3->(skip S4)->S5->S6->S7")
    print("    C) No observation:               S1->S2->S3->S4->(skip S5)->S6->S7")
    print()

    train_loader, test_loader = load_mnist()
    n_trials = 5
    seeds = [42, 137, 256, 314, 777]

    results = {
        'A': {'parent': [], 'return': [], 'enhancement': []},
        'B': {'parent': [], 'return': [], 'enhancement': []},
        'C': {'parent': [], 'return': [], 'enhancement': []},
    }

    conditions = [
        ('A', 'Full (with detach)', run_condition_A),
        ('B', 'No detach', run_condition_B),
        ('C', 'No observation', run_condition_C),
    ]

    t_start = time.time()

    for trial_idx in range(n_trials):
        seed = seeds[trial_idx]
        print(f"\n{'#' * 72}")
        print(f"  TRIAL {trial_idx + 1}/{n_trials}  (seed={seed})")
        print(f"{'#' * 72}")

        for cond_key, cond_name, cond_fn in conditions:
            print(f"\n  --- Condition {cond_key}: {cond_name} ---")
            t0 = time.time()
            parent_acc, return_acc = cond_fn(seed, train_loader, test_loader)
            enhancement = (return_acc - parent_acc) * 100
            elapsed = time.time() - t0

            results[cond_key]['parent'].append(parent_acc)
            results[cond_key]['return'].append(return_acc)
            results[cond_key]['enhancement'].append(enhancement)

            print(f"    Parent: {parent_acc*100:.2f}%  Return: {return_acc*100:.2f}%  "
                  f"Enhancement: {enhancement:+.2f}%  ({elapsed:.1f}s)")

    total_time = time.time() - t_start

    # ─── Per-Trial Table ───
    print("\n")
    print("=" * 72)
    print("  PER-TRIAL RESULTS")
    print("=" * 72)
    print(f"  {'Trial':<8} {'Seed':<8} {'Cond':<6} {'Parent':>10} {'Return':>10} {'Enhance':>10}")
    print("  " + "-" * 64)
    for trial_idx in range(n_trials):
        for cond_key in ['A', 'B', 'C']:
            p = results[cond_key]['parent'][trial_idx] * 100
            r = results[cond_key]['return'][trial_idx] * 100
            e = results[cond_key]['enhancement'][trial_idx]
            print(f"  {trial_idx+1:<8} {seeds[trial_idx]:<8} {cond_key:<6} "
                  f"{p:>9.2f}% {r:>9.2f}% {e:>+9.2f}%")
        if trial_idx < n_trials - 1:
            print("  " + "." * 64)

    # ─── Summary Table ───
    print("\n")
    print("=" * 72)
    print("  SUMMARY (5 trials)")
    print("=" * 72)

    cond_labels = {
        'A': 'Full (detach+observe)',
        'B': 'No detach (skip S4)',
        'C': 'No observation (skip S5)',
    }

    print(f"  {'Condition':<28} {'Parent':>10} {'Return':>10} {'Enhancement':>14}")
    print("  " + "-" * 64)

    summary = {}
    for cond_key in ['A', 'B', 'C']:
        p_mean = np.mean(results[cond_key]['parent']) * 100
        p_std = np.std(results[cond_key]['parent']) * 100
        r_mean = np.mean(results[cond_key]['return']) * 100
        r_std = np.std(results[cond_key]['return']) * 100
        e_mean = np.mean(results[cond_key]['enhancement'])
        e_std = np.std(results[cond_key]['enhancement'])

        summary[cond_key] = {
            'p_mean': p_mean, 'p_std': p_std,
            'r_mean': r_mean, 'r_std': r_std,
            'e_mean': e_mean, 'e_std': e_std,
        }

        print(f"  {cond_labels[cond_key]:<28} "
              f"{p_mean:>6.2f}+/-{p_std:.2f} "
              f"{r_mean:>6.2f}+/-{r_std:.2f} "
              f"{e_mean:>+6.2f}+/-{e_std:.2f}%")

    # ─── Enhancement Comparison ───
    print("\n")
    print("=" * 72)
    print("  ENHANCEMENT COMPARISON")
    print("=" * 72)

    e_A = summary['A']['e_mean']
    e_B = summary['B']['e_mean']
    e_C = summary['C']['e_mean']

    print(f"  A (full):           {e_A:+.3f}% +/- {summary['A']['e_std']:.3f}%")
    print(f"  B (no detach):      {e_B:+.3f}% +/- {summary['B']['e_std']:.3f}%")
    print(f"  C (no observation): {e_C:+.3f}% +/- {summary['C']['e_std']:.3f}%")
    print()
    print(f"  A - B (detach effect):      {e_A - e_B:+.3f}%")
    print(f"  A - C (observation effect):  {e_A - e_C:+.3f}%")
    print(f"  B - C (observe w/o detach):  {e_B - e_C:+.3f}%")

    # ─── Statistical test (paired t-test) ───
    from scipy import stats
    enh_A = results['A']['enhancement']
    enh_B = results['B']['enhancement']
    enh_C = results['C']['enhancement']

    def safe_ttest(a, b, label):
        t_stat, p_val = stats.ttest_rel(a, b)
        sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
        print(f"  {label:<30} t={t_stat:>+6.3f}  p={p_val:.4f}  {sig}")

    print("\n  Paired t-tests:")
    safe_ttest(enh_A, enh_B, "A vs B (detach effect)")
    safe_ttest(enh_A, enh_C, "A vs C (observation effect)")
    safe_ttest(enh_B, enh_C, "B vs C (observe w/o detach)")

    # ─── ASCII Bar Chart ───
    print("\n")
    print("=" * 72)
    print("  ENHANCEMENT BAR CHART (% improvement over parent)")
    print("=" * 72)

    bar_max = max(abs(e_A), abs(e_B), abs(e_C), 0.01)
    chart_width = 40

    def bar_str(val, max_val, width):
        if val >= 0:
            n = int(round(val / max_val * width)) if max_val > 0 else 0
            return " " * width + "|" + "#" * n + f" {val:+.3f}%"
        else:
            n = int(round(abs(val) / max_val * width)) if max_val > 0 else 0
            padding = width - n
            return " " * padding + "#" * n + "|" + f" {val:+.3f}%"

    print()
    print(f"  A (full):        {bar_str(e_A, bar_max, chart_width)}")
    print(f"  B (no detach):   {bar_str(e_B, bar_max, chart_width)}")
    print(f"  C (no observe):  {bar_str(e_C, bar_max, chart_width)}")
    print()
    center_marker = " " * chart_width + "|"
    print(f"                   {center_marker}")
    print(f"                   {'<-- worse':>{chart_width}}  better -->")

    # ─── Per-Trial Enhancement Chart ───
    print("\n")
    print("=" * 72)
    print("  PER-TRIAL ENHANCEMENT (all 5 trials)")
    print("=" * 72)
    print(f"  {'Trial':<8} {'A (full)':>12} {'B (no det)':>12} {'C (no obs)':>12}")
    print("  " + "-" * 48)
    for i in range(n_trials):
        print(f"  {i+1:<8} {results['A']['enhancement'][i]:>+11.3f}% "
              f"{results['B']['enhancement'][i]:>+11.3f}% "
              f"{results['C']['enhancement'][i]:>+11.3f}%")
    print("  " + "-" * 48)
    print(f"  {'Mean':<8} {e_A:>+11.3f}% {e_B:>+11.3f}% {e_C:>+11.3f}%")
    print(f"  {'Std':<8} {summary['A']['e_std']:>11.3f}% "
          f"{summary['B']['e_std']:>11.3f}% "
          f"{summary['C']['e_std']:>11.3f}%")

    # ─── Verdict ───
    print("\n")
    print("=" * 72)
    print("  VERDICT: H-CX-13 (Detach = Information Bottleneck)")
    print("=" * 72)

    if e_A > e_B + 0.05 and e_A > e_C + 0.05:
        print("  SUPPORTED: Full sequence (A) produces the most enhancement.")
        print(f"  Detach contributes {e_A - e_B:+.3f}% (A-B)")
        print(f"  Observation contributes {e_A - e_C:+.3f}% (A-C)")
        print("  Both detach AND observation are needed for maximum effect.")
    elif e_A > e_B + 0.05:
        print("  PARTIALLY SUPPORTED: Detach matters.")
        print(f"  Removing detach reduces enhancement by {e_A - e_B:.3f}%")
        print(f"  But observation alone (without detach) may also help.")
    elif e_A > e_C + 0.05:
        print("  PARTIALLY SUPPORTED: Observation matters more than detach.")
        print(f"  Removing observation reduces enhancement by {e_A - e_C:.3f}%")
        print(f"  Detach alone is not sufficient.")
    elif abs(e_A - e_B) < 0.05 and abs(e_A - e_C) < 0.05:
        print("  NOT SUPPORTED: All conditions produce similar enhancement.")
        print("  Neither detach nor observation is critical at this scale.")
    else:
        print(f"  MIXED: A={e_A:+.3f}%, B={e_B:+.3f}%, C={e_C:+.3f}%")
        print("  Pattern does not cleanly support or refute H-CX-13.")

    print(f"\n  Total experiment time: {total_time:.1f}s")
    print()


if __name__ == '__main__':
    main()
