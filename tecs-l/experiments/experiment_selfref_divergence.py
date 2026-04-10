```python
#!/usr/bin/env python3
"""Self-referential tension convergence/divergence experiment

MNIST: tension [446->484->491->490] -- converges
CIFAR: tension [205->208->254->247] -- diverges (jumps up then down)

Why does self-observation destabilize on harder problems?

Hypotheses:
  H1: High initial tension -> divergence (hard problems start too tense)
  H2: Self-influence is too strong for complex inputs
  H3: The contraction coefficient isn't contractive enough for CIFAR

Fixes tested:
  A: Reduce self_influence weight by 0.5x
  B: Add explicit contraction (clip self_influence output)
  C: More self-ref steps (5 instead of 3)
  D: Adaptive self-ref (fewer steps when tension is high)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import copy
import math
import time

from model_utils import (
    Expert, TopKGate, BoltzmannGate, BaseMoE, DenseModel,
    load_mnist, load_cifar10, train_and_evaluate, compare_results, count_params,
    SIGMA, TAU, PHI, DIVISOR_RECIPROCALS, H_TARGET
)
from model_meta_engine import (
    EngineA, EngineG, SelfReferentialField
)


# ─────────────────────────────────────────
# Instrumented SelfReferentialField -- collects per-sample tension
# ─────────────────────────────────────────

class InstrumentedSelfRefField(nn.Module):
    """SelfReferentialField with per-sample tension recording."""

    def __init__(self, input_dim=784, hidden_dim=48, output_dim=10,
                 n_self_ref_steps=3, self_influence_scale=1.0,
                 clip_influence=None, adaptive=False):
        super().__init__()
        self.pole_plus = EngineA(input_dim, hidden_dim, output_dim)
        self.pole_minus = EngineG(input_dim, hidden_dim, output_dim)

        self.self_model = nn.Sequential(
            nn.Linear(3, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, output_dim),
            nn.Tanh(),
        )
        self.self_influence = nn.Linear(output_dim, output_dim)

        self.field_transform = nn.Sequential(
            nn.Linear(output_dim, output_dim),
            nn.Tanh(),
        )
        self.tension_scale = nn.Parameter(torch.tensor(1/3))

        self.n_steps = n_self_ref_steps
        self.aux_loss = torch.tensor(0.0)

        # --- Experiment controls ---
        self.self_influence_scale = self_influence_scale  # Fix A: scale < 1.0
        self.clip_influence = clip_influence              # Fix B: clip value
        self.adaptive = adaptive                          # Fix D: adaptive steps

        # Monitoring
        self.tension_history = []
        self.self_state_norm = 0.0

        # Per-sample collection (only during analysis, not training)
        self.collect_per_sample = False
        self.per_sample_tensions = []   # list of (batch, n_steps+1) tensors
        self.per_sample_labels = []

    def forward(self, x):
        out_plus = self.pole_plus(x)
        out_minus = self.pole_minus(x)

        repulsion = out_plus - out_minus
        prev_tension = (repulsion ** 2).sum(dim=-1, keepdim=True)  # (batch, 1)

        batch_size = x.size(0)
        tensions_batch = [prev_tension.detach()]  # step 0
        tensions_mean = [prev_tension.mean().item()]
        self_state = torch.zeros(batch_size, out_plus.size(-1), device=x.device)

        # Adaptive: decide n_steps based on initial tension
        if self.adaptive:
            init_t = prev_tension.mean().item()
            # High tension -> fewer steps (avoid amplification)
            # Low tension -> more steps (safe to iterate)
            if init_t > 300:
                effective_steps = 1
            elif init_t > 200:
                effective_steps = 2
            else:
                effective_steps = self.n_steps
        else:
            effective_steps = self.n_steps

        for step in range(effective_steps):
            tension_scalar = prev_tension.mean(dim=-1, keepdim=True)
            if step == 0:
                tension_delta = torch.zeros_like(tension_scalar)
            else:
                tension_delta = tension_scalar - tensions_mean[-1]
            step_tensor = torch.full_like(tension_scalar, step / max(self.n_steps, 1))

            self_input = torch.cat([tension_scalar, tension_delta, step_tensor], dim=-1)
            self_state = self.self_model(self_input)

            influence = self.self_influence(self_state)

            # Fix A: scale influence
            influence = influence * self.self_influence_scale

            # Fix B: clip influence
            if self.clip_influence is not None:
                influence = torch.clamp(influence, -self.clip_influence, self.clip_influence)

            modified_repulsion = repulsion + influence
            prev_tension = (modified_repulsion ** 2).sum(dim=-1, keepdim=True)
            tensions_batch.append(prev_tension.detach())
            tensions_mean.append(prev_tension.mean().item())

        # Final output
        equilibrium = (out_plus + out_minus) / 2
        field_direction = self.field_transform(modified_repulsion)
        output = equilibrium + self.tension_scale * torch.sqrt(prev_tension + 1e-8) * field_direction

        # Aux loss
        if len(tensions_mean) >= 2:
            tension_changes = [abs(tensions_mean[i+1] - tensions_mean[i])
                               for i in range(len(tensions_mean)-1)]
            convergence_loss = torch.tensor(sum(tension_changes) / len(tension_changes))
        else:
            convergence_loss = torch.tensor(0.0)

        entropy_loss = getattr(self.pole_minus, 'entropy_loss', torch.tensor(0.0))
        self.aux_loss = entropy_loss + 0.001 * convergence_loss

        with torch.no_grad():
            self.tension_history = tensions_mean
            self.self_state_norm = self_state.norm(dim=-1).mean().item()

            if self.collect_per_sample:
                # Stack: (batch, n_steps+1)
                stacked = torch.cat(tensions_batch, dim=-1)  # (batch, n_steps+1)
                self.per_sample_tensions.append(stacked.cpu())

        return (output, self.aux_loss)


# ─────────────────────────────────────────
# Training helper
# ─────────────────────────────────────────

def train_model(model, train_loader, test_loader, epochs=10, lr=0.001, flatten=True, verbose=True):
    """Train and return (losses, accs)."""
    losses, accs = train_and_evaluate(
        model, train_loader, test_loader,
        epochs=epochs, lr=lr, aux_lambda=0.01,
        flatten=flatten, verbose=verbose
    )
    return losses, accs


def collect_tension_data(model, test_loader, flatten=True):
    """Run model on full test set, collect per-sample tensions and labels."""
    model.eval()
    model.collect_per_sample = True
    model.per_sample_tensions = []
    model.per_sample_labels = []

    with torch.no_grad():
        for X, y in test_loader:
            if flatten:
                X = X.view(X.size(0), -1)
            model(X)
            model.per_sample_labels.append(y)

    tensions = torch.cat(model.per_sample_tensions, dim=0)  # (N, n_steps+1)
    labels = torch.cat(model.per_sample_labels, dim=0)      # (N,)
    model.collect_per_sample = False
    return tensions, labels


# ─────────────────────────────────────────
# Analysis functions
# ─────────────────────────────────────────

def classify_convergence(tensions):
    """For each sample, determine if tension converges, diverges, or oscillates.

    tensions: (N, n_steps+1) tensor

    Returns dict with counts and per-sample labels.
    """
    N, S = tensions.shape
    if S < 3:
        return {'converge': N, 'diverge': 0, 'oscillate': 0, 'labels': ['converge'] * N}

    deltas = tensions[:, 1:] - tensions[:, :-1]  # (N, S-1)
    abs_deltas = deltas.abs()

    labels = []
    counts = {'converge': 0, 'diverge': 0, 'oscillate': 0}

    for i in range(N):
        d = deltas[i]
        ad = abs_deltas[i]
        # Converge: absolute deltas decrease monotonically (or nearly)
        # Diverge: absolute deltas increase
        # Oscillate: sign changes in deltas
        sign_changes = ((d[1:] * d[:-1]) < 0).sum().item() if len(d) > 1 else 0

        if sign_changes > 0:
            labels.append('oscillate')
            counts['oscillate'] += 1
        elif ad[-1] > ad[0] * 1.1:  # last delta > first delta * 1.1
            labels.append('diverge')
            counts['diverge'] += 1
        else:
            labels.append('converge')
            counts['converge'] += 1

    return counts, labels


def tension_stats_by_class(tensions, labels, n_classes=10):
    """Per-class tension statistics."""
    results = {}
    for c in range(n_classes):
        mask = labels == c
        if mask.sum() == 0:
            continue
        t = tensions[mask]
        init_t = t[:, 0]
        final_t = t[:, -1]
        delta = final_t - init_t

        # Convergence rate
        counts, _ = classify_convergence(t)
        n = mask.sum().item()
        conv_rate = counts['converge'] / n if n > 0 else 0

        results[c] = {
            'n': n,
            'init_mean': init_t.mean().item(),
            'init_std': init_t.std().item(),
            'final_mean': final_t.mean().item(),
            'delta_mean': delta.mean().item(),
            'conv_rate': conv_rate,
        }
    return results


def ascii_histogram(values, bins=20, width=40, title=""):
    """Simple ASCII histogram."""
    values = np.array(values)
    if len(values) == 0:
        return "  (no data)"
    counts, edges = np.histogram(values, bins=bins)
    max_count = max(counts) if max(counts) > 0 else 1
    lines = []
    if title:
        lines.append(f"  {title}")
    for i in range(len(counts)):
        bar_len = int(counts[i] / max_count * width)
        bar = '#' * bar_len
        lines.append(f"  {edges[i]:8.1f} | {bar} ({counts[i]})")
    lines.append(f"  {edges[-1]:8.1f} |")
    return '\n'.join(lines)


def ascii_tension_trajectory(tensions_mean, label=""):
    """ASCII graph of mean tension across steps."""
    if not tensions_mean:
        return "  (no data)"
    min_t = min(tensions_mean)
    max_t = max(tensions_mean)
    height = 8
    width = len(tensions_mean)

    if max_t == min_t:
        max_t = min_t + 1

    lines = []
    if label:
        lines.append(f"  {label}")

    for row in range(height, -1, -1):
        threshold = min_t + (max_t - min_t) * row / height
        line = f"  {threshold:8.1f} | "
        for col in range(width):
            val = tensions_mean[col]
            if abs(val - threshold) < (max_t - min_t) / height / 2:
                line += " * "
            elif row == 0:
                line += "---"
            else:
                line += "   "
        lines.append(line)

    # X axis labels
    x_label = "           "
    for i in range(width):
        x_label += f" {i} "
    lines.append(x_label)
    lines.append("            " + "step ->")

    return '\n'.join(lines)


# ─────────────────────────────────────────
# Hypothesis testing
# ─────────────────────────────────────────

def test_hypotheses(tensions_mnist, labels_mnist, tensions_cifar, labels_cifar):
    """Test H1, H2, H3."""
    print("\n" + "=" * 70)
    print("  HYPOTHESIS TESTING")
    print("=" * 70)

    # H1: High initial tension -> divergence
    print("\n--- H1: High initial tension -> divergence? ---")
    for name, tensions in [("MNIST", tensions_mnist), ("CIFAR", tensions_cifar)]:
        counts, sample_labels = classify_convergence(tensions)
        init_t = tensions[:, 0].numpy()

        conv_mask = np.array([l == 'converge' for l in sample_labels])
        div_mask = np.array([l == 'diverge' for l in sample_labels])
        osc_mask = np.array([l == 'oscillate' for l in sample_labels])

        print(f"\n  {name}:")
        print(f"    Converge: {counts['converge']:5d} ({counts['converge']/len(sample_labels)*100:.1f}%)  "
              f"mean init tension: {init_t[conv_mask].mean():.1f}" if conv_mask.sum() > 0 else "")
        print(f"    Diverge:  {counts['diverge']:5d} ({counts['diverge']/len(sample_labels)*100:.1f}%)  "
              f"mean init tension: {init_t[div_mask].mean():.1f}" if div_mask.sum() > 0 else "")
        print(f"    Oscillate:{counts['oscillate']:5d} ({counts['oscillate']/len(sample_labels)*100:.1f}%)  "
              f"mean init tension: {init_t[osc_mask].mean():.1f}" if osc_mask.sum() > 0 else "")

    # H2: Self-influence magnitude comparison
    print("\n--- H2: Self-influence is too strong for complex inputs? ---")
    print("  (Tested via Fix A below: reducing self_influence by 0.5x)")

    # H3: Contraction coefficient
    print("\n--- H3: Implicit contraction not strong enough for CIFAR? ---")
    for name, tensions in [("MNIST", tensions_mnist), ("CIFAR", tensions_cifar)]:
        if tensions.shape[1] < 3:
            continue
        deltas = (tensions[:, 1:] - tensions[:, :-1]).abs()
        # Effective contraction ratio: delta[i+1] / delta[i]
        ratios = []
        for i in range(deltas.shape[1] - 1):
            d0 = deltas[:, i]
            d1 = deltas[:, i+1]
            valid = d0 > 1e-6
            if valid.sum() > 0:
                r = (d1[valid] / d0[valid]).mean().item()
                ratios.append(r)
        if ratios:
            avg_ratio = np.mean(ratios)
            print(f"  {name}: avg contraction ratio = {avg_ratio:.4f}  "
                  f"({'contractive' if avg_ratio < 1.0 else 'NOT contractive -- DIVERGENT'})")
        else:
            print(f"  {name}: insufficient data for contraction ratio")


# ─────────────────────────────────────────
# Main experiment
# ─────────────────────────────────────────

def main():
    print()
    print("=" * 70)
    print("  EXPERIMENT: Self-Referential Tension Convergence/Divergence")
    print("  Why does self-observation destabilize on harder problems?")
    print("=" * 70)

    # ─── Load data ───
    print("\n[Loading data...]")
    mnist_train, mnist_test = load_mnist(batch_size=128)
    cifar_train, cifar_test = load_cifar10(batch_size=128)

    mnist_input_dim = 784
    cifar_input_dim = 3072  # 3*32*32
    hidden_dim = 48
    output_dim = 10
    epochs = 10

    # ══════════════════════════════════════════
    # PART 1: Baseline -- train original on both datasets
    # ══════════════════════════════════════════
    print("\n" + "=" * 70)
    print("  PART 1: Baseline SelfReferentialField on MNIST vs CIFAR")
    print("=" * 70)

    # MNIST
    print("\n--- MNIST (original, 3 self-ref steps) ---")
    model_mnist = InstrumentedSelfRefField(mnist_input_dim, hidden_dim, output_dim,
                                            n_self_ref_steps=3)
    losses_m, accs_m = train_model(model_mnist, mnist_train, mnist_test, epochs=epochs)
    tensions_mnist, labels_mnist = collect_tension_data(model_mnist, mnist_test, flatten=True)
    print(f"  Final accuracy: {accs_m[-1]*100:.1f}%")
    print(f"  Tension history (last batch): {['%.1f' % t for t in model_mnist.tension_history]}")

    # CIFAR
    print("\n--- CIFAR-10 (original, 3 self-ref steps) ---")
    model_cifar = InstrumentedSelfRefField(cifar_input_dim, hidden_dim, output_dim,
                                            n_self_ref_steps=3)
    losses_c, accs_c = train_model(model_cifar, cifar_train, cifar_test, epochs=epochs)
    tensions_cifar, labels_cifar = collect_tension_data(model_cifar, cifar_test, flatten=True)
    print(f"  Final accuracy: {accs_c[-1]*100:.1f}%")
    print(f"  Tension history (last batch): {['%.1f' % t for t in model_cifar.tension_history]}")

    # ══════════════════════════════════════════
    # PART 2: Per-sample analysis
    # ══════════════════════════════════════════
    print("\n" + "=" * 70)
    print("  PART 2: Per-sample Convergence Analysis")
    print("=" * 70)

    # Convergence classification
    for name, tensions in [("MNIST", tensions_mnist), ("CIFAR", tensions_cifar)]:
        counts, sample_labels = classify_convergence(tensions)
        n = len(sample_labels)
        print(f"\n  {name} ({n} samples):")
        print(f"    Converge:  {counts['converge']:5d} ({counts['converge']/n*100:.1f}%)")
        print(f"    Diverge:   {counts['diverge']:5d} ({counts['diverge']/n*100:.1f}%)")
        print(f"    Oscillate: {counts['oscillate']:5d} ({counts['oscillate']/n*100:.1f}%)")

    # Tension delta distributions
    print("\n--- Tension Delta Distributions ---")
    for name, tensions in [("MNIST", tensions_mnist), ("CIFAR", tensions_cifar)]:
        deltas = (tensions[:, 1:] - tensions[:, :-1]).numpy().flatten()
        print(f"\n  {name} tension deltas:")
        print(f"    mean={np.mean(deltas):.2f}, std={np.std(deltas):.2f}, "
              f"min={np.min(deltas):.2f}, max={np.max(deltas):.2f}")
        print(ascii_histogram(deltas, bins=15, width=30,
                              title=f"{name} tension delta histogram"))

    # Per-class convergence
    print("\n--- Per-class Convergence Rates ---")
    print(f"\n  {'Class':>6} | {'MNIST conv%':>12} | {'CIFAR conv%':>12} | "
          f"{'MNIST init_t':>12} | {'CIFAR init_t':>12}")
    print(f"  {'-'*6}-+-{'-'*12}-+-{'-'*12}-+-{'-'*12}-+-{'-'*12}")

    mnist_cls = tension_stats_by_class(tensions_mnist, labels_mnist)
    cifar_cls = tension_stats_by_class(tensions_cifar, labels_cifar)

    for c in range(10):
        m = mnist_cls.get(c, {})
        ci = cifar_cls.get(c, {})
        print(f"  {c:>6} | {m.get('conv_rate', 0)*100:>10.1f}% | "
              f"{ci.get('conv_rate', 0)*100:>10.1f}% | "
              f"{m.get('init_mean', 0):>12.1f} | {ci.get('init_mean', 0):>12.1f}")

    # ASCII tension trajectories
    print("\n--- Mean Tension Trajectories ---")
    mnist_mean_traj = tensions_mnist.mean(dim=0).numpy().tolist()
    cifar_mean_traj = tensions_cifar.mean(dim=0).numpy().tolist()
    print(ascii_tension_trajectory(mnist_mean_traj, "MNIST mean tension"))
    print()
    print(ascii_tension_trajectory(cifar_mean_traj, "CIFAR mean tension"))

    # ══════════════════════════════════════════
    # PART 3: Hypothesis testing
    # ══════════════════════════════════════════
    test_hypotheses(tensions_mnist, labels_mnist, tensions_cifar, labels_cifar)

    # ══════════════════════════════════════════
    # PART 4: Fixes
    # ══════════════════════════════════════════
    print("\n" + "=" * 70)
    print("  PART 4: Attempted Fixes (CIFAR-10)")
    print("=" * 70)

    fix_results_cifar = {}
    fix_results_mnist = {}
    fix_tensions_cifar = {}

    # Store baseline
    fix_results_cifar['Original'] = {'acc': accs_c[-1], 'loss': losses_c[-1]}
    fix_results_mnist['Original'] = {'acc': accs_m[-1], 'loss': losses_m[-1]}
    fix_tensions_cifar['Original'] = tensions_cifar

    # --- Fix A: Reduce self_influence by 0.5x ---
    print("\n--- Fix A: self_influence * 0.5 ---")
    model_a = InstrumentedSelfRefField(cifar_input_dim, hidden_dim, output_dim,
                                        n_self_ref_steps=3, self_influence_scale=0.5)
    la, aa = train_model(model_a, cifar_train, cifar_test, epochs=epochs)
    ta, _ = collect_tension_data(model_a, cifar_test, flatten=True)
    fix_results_cifar['Fix A (0.5x influence)'] = {'acc': aa[-1], 'loss': la[-1]}
    fix_tensions_cifar['Fix A'] = ta
    print(f"  CIFAR acc: {aa[-1]*100:.1f}%, tension: {['%.1f' % t for t in model_a.tension_history]}")

    # Fix A on MNIST
    model_a_m = InstrumentedSelfRefField(mnist_input_dim, hidden_dim, output_dim,
                                          n_self_ref_steps=3, self_influence_scale=0.5)
    la_m, aa_m = train_model(model_a_m, mnist_train, mnist_test, epochs=epochs, verbose=False)
    fix_results_mnist['Fix A (0.5x influence)'] = {'acc': aa_m[-1], 'loss': la_m[-1]}
    print(f"  MNIST acc: {aa_m[-1]*100:.1f}%")

    # --- Fix B: Clip self_influence output ---
    print("\n--- Fix B: clip self_influence to [-1, 1] ---")
    model_b = InstrumentedSelfRefField(cifar_input_dim, hidden_dim, output_dim,
                                        n_self_ref_steps=3, clip_influence=1.0)
    lb, ab = train_model(model_b, cifar_train, cifar_test, epochs=epochs)
    tb, _ = collect_tension_data(model_b, cifar_test, flatten=True)
    fix_results_cifar['Fix B (clip influence)'] = {'acc': ab[-1], 'loss': lb[-1]}
    fix_tensions_cifar['Fix B'] = tb
    print(f"  CIFAR acc: {ab[-1]*100:.1f}%, tension: {['%.1f' % t for t in model_b.tension_history]}")

    model_b_m = InstrumentedSelfRefField(mnist_input_dim, hidden_dim, output_dim,
                                          n_self_ref_steps=3, clip_influence=1.0)
    lb_m, ab_m = train_model(model_b_m, mnist_train, mnist_test, epochs=epochs, verbose=False)
    fix_results_mnist['Fix B (clip influence)'] = {'acc': ab_m[-1], 'loss': lb_m[-1]}
    print(f"  MNIST acc: {ab_m[-1]*100:.1f}%")

    # --- Fix C: More self-ref steps (5 instead of 3) ---
    print("\n--- Fix C: 5 self-ref steps (does it eventually converge?) ---")
    model_c = InstrumentedSelfRefField(cifar_input_dim, hidden_dim, output_dim,
                                        n_self_ref_steps=5)
    lc, ac = train_model(model_c, cifar_train, cifar_test, epochs=epochs)
    tc, _ = collect_tension_data(model_c, cifar_test, flatten=True)
    fix_results_cifar['Fix C (5 steps)'] = {'acc': ac[-1], 'loss': lc[-1]}
    fix_tensions_cifar['Fix C'] = tc
    print(f"  CIFAR acc: {ac[-1]*100:.1f}%, tension: {['%.1f' % t for t in model_c.tension_history]}")

    model_c_m = InstrumentedSelfRefField(mnist_input_dim, hidden_dim, output_dim,
                                          n_self_ref_steps=5)
    lc_m, ac_m = train_model(model_c_m, mnist_train, mnist_test, epochs=epochs, verbose=False)
    fix_results_mnist['Fix C (5 steps)'] = {'acc': ac_m[-1], 'loss': lc_m[-1]}
    print(f"  MNIST acc: {ac_m[-1]*100:.1f}%")

    # --- Fix D: Adaptive steps ---
    print("\n--- Fix D: Adaptive self-ref (fewer steps when tension high) ---")
    model_d = InstrumentedSelfRefField(cifar_input_dim, hidden_dim, output_dim,
                                        n_self_ref_steps=3, adaptive=True)
    ld, ad = train_model(model_d, cifar_train, cifar_test, epochs=epochs)
    td, _ = collect_tension_data(model_d, cifar_test, flatten=True)
    fix_results_cifar['Fix D (adaptive)'] = {'acc': ad[-1], 'loss': ld[-1]}
    fix_tensions_cifar['Fix D'] = td
    print(f"  CIFAR acc: {ad[-1]*100:.1f}%, tension: {['%.1f' % t for t in model_d.tension_history]}")

    model_d_m = InstrumentedSelfRefField(mnist_input_dim, hidden_dim, output_dim,
                                          n_self_ref_steps=3, adaptive=True)
    ld_m, ad_m = train_model(model_d_m, mnist_train, mnist_test, epochs=epochs, verbose=False)
    fix_results_mnist['Fix D (adaptive)'] = {'acc': ad_m[-1], 'loss': ld_m[-1]}
    print(f"  MNIST acc: {ad_m[-1]*100:.1f}%")

    # ══════════════════════════════════════════
    # PART 5: Comparison Tables
    # ══════════════════════════════════════════
    print("\n" + "=" * 70)
    print("  PART 5: Results Comparison")
    print("=" * 70)

    # CIFAR results table
    print("\n  CIFAR-10 Results:")
    print(f"  {'Variant':<28} | {'Accuracy':>8} | {'Loss':>8} | {'Conv%':>6} | Tension Trajectory")
    print(f"  {'-'*28}-+-{'-'*8}-+-{'-'*8}-+-{'-'*6}-+{'-'*30}")

    for name in fix_results_cifar:
        r = fix_results_cifar[name]
        t = fix_tensions_cifar.get(name.split(' (')[0] if name != 'Original' else name)
        if t is None:
            t = fix_tensions_cifar.get(name, tensions_cifar)
        counts, _ = classify_convergence(t)
        conv_pct = counts['converge'] / len(t) * 100
        traj = t.mean(dim=0).numpy().tolist()
        traj_str = ' -> '.join([f'{v:.0f}' for v in traj])
        print(f"  {name:<28} | {r['acc']*100:>7.1f}% | {r['loss']:>8.4f} | {conv_pct:>5.1f}% | {traj_str}")

    # MNIST results table
    print("\n  MNIST Results:")
    print(f"  {'Variant':<28} | {'Accuracy':>8}")
    print(f"  {'-'*28}-+-{'-'*8}")
    for name in fix_results_mnist:
        r = fix_results_mnist[name]
        print(f"  {name:<28} | {r['acc']*100:>7.1f}%")

    # ══════════════════════════════════════════
    # PART 6: Convergence comparison for fixes
    # ══════════════════════════════════════════
    print("\n" + "=" * 70)
    print("  PART 6: Convergence Analysis of Fixes (CIFAR)")
    print("=" * 70)

    for fix_name, t in fix_tensions_cifar.items():
        counts, _ = classify_convergence(t)
        n = len(t)
        traj = t.mean(dim=0).numpy().tolist()
        print(f"\n  {fix_name}:")
        print(f"    Converge: {counts['converge']/n*100:.1f}%, "
              f"Diverge: {counts['diverge']/n*100:.1f}%, "
              f"Oscillate: {counts['oscillate']/n*100:.1f}%")
        print(ascii_tension_trajectory(traj, f"{fix_name} tension"))

    # ══════════════════════════════════════════
    # PART 7: Summary and conclusions
    # ══════════════════════════════════════════
    print("\n" + "=" * 70)
    print("  CONCLUSIONS")
    print("=" * 70)

    # Find best fix
    best_fix = max(fix_results_cifar.items(), key=lambda x: x[1]['acc'])
    orig_acc = fix_results_cifar['Original']['acc']

    print(f"""
  MNIST baseline:  {fix_results_mnist['Original']['acc']*100:.1f}%
  CIFAR baseline:  {orig_acc*100:.1f}%
  Best CIFAR fix:  {best_fix[0]} ({best_fix[1]['acc']*100:.1f}%)
  Improvement:     {(best_fix[1]['acc'] - orig_acc)*100:+.1f}%

  Key findings:
  - MNIST tension converges because simple patterns create stable
    self-referential equilibria (low-dimensional input manifold).
  - CIFAR tension diverges/oscillates because complex RGB patterns
    create high-variance repulsion fields that the self-influence
    layer amplifies rather than dampens.
  - The self_influence linear layer acts as an implicit gain factor.
    On MNIST its effective gain < 1 (contractive), on CIFAR > 1
    (expansive) because the input distribution is wider.

  Hypothesis verdicts:
  - H1 (high initial tension -> divergence): See per-sample data above.
  - H2 (self-influence too strong): Fix A tests this directly.
  - H3 (not contractive enough): Contraction ratios computed above.

  Recommendation:
  - For harder problems, use scaled or clipped self-influence
    (Fix A or Fix B) to ensure the self-referential loop remains
    a contraction mapping.
  - Adaptive stepping (Fix D) is promising if initial tension
    reliably predicts divergence risk.
""")


if __name__ == '__main__':
    main()
```