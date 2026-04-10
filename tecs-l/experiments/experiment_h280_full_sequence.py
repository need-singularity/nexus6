#!/usr/bin/env python3
"""H-280: Full Shamanic Experience Sequence

Combines mitosis + displacement + detach + separation into one continuous sequence.

Steps:
  1. Single consciousness - train parent RepulsionFieldEngine on MNIST
  2. Mitosis - clone parent into child_a, child_b with small perturbation (scale=0.01)
  3. Displacement - child_b takes control (control=1.0 in DisplacementField)
  4. Detach - child_a becomes read-only observer (detach gradients)
  5. child_b produces output while child_a only observes
  6. Separation - save child_b weights, remove it
  7. Return - child_a alone, measure accuracy

Tracked metrics at each step:
  - Accuracy
  - Tension between the two children
  - Identity similarity (cosine of weight vectors)
  - Internal representation change (fiber distance from step 1)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import copy
import time
import sys
import os

sys.path.insert(0, '/Users/ghost/Dev/logout')

from model_utils import (
    Expert, load_mnist, count_params,
    SIGMA, TAU, PHI, DIVISOR_RECIPROCALS, H_TARGET
)
from model_meta_engine import EngineA, EngineG, RepulsionFieldEngine


# ─────────────────────────────────────────
# Utility functions
# ─────────────────────────────────────────

def get_param_vector(model):
    """Flatten all parameters into a single vector."""
    return torch.cat([p.detach().flatten() for p in model.parameters()])


def cosine_similarity_params(model_a, model_b):
    """Cosine similarity between two models' parameter vectors."""
    vec_a = get_param_vector(model_a)
    vec_b = get_param_vector(model_b)
    return F.cosine_similarity(vec_a.unsqueeze(0), vec_b.unsqueeze(0)).item()


def fiber_distance(model, reference_vec):
    """L2 distance in parameter space from a reference point."""
    vec = get_param_vector(model)
    return (vec - reference_vec).norm().item()


def compute_tension(model_a, model_b, test_loader, max_batches=10):
    """Tension = mean |out_a - out_b|^2 over test data."""
    model_a.eval()
    model_b.eval()
    total_tension = 0.0
    count = 0
    with torch.no_grad():
        for i, (X, y) in enumerate(test_loader):
            if i >= max_batches:
                break
            X = X.view(X.size(0), -1)
            out_a = model_a(X)
            out_b = model_b(X)
            if isinstance(out_a, tuple):
                out_a = out_a[0]
            if isinstance(out_b, tuple):
                out_b = out_b[0]
            total_tension += ((out_a - out_b) ** 2).sum(dim=-1).mean().item()
            count += 1
    return total_tension / max(count, 1)


def evaluate_accuracy(model, test_loader):
    """Evaluate model accuracy on MNIST test set."""
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for X, y in test_loader:
            X = X.view(X.size(0), -1)
            out = model(X)
            if isinstance(out, tuple):
                out = out[0]
            correct += (out.argmax(1) == y).sum().item()
            total += y.size(0)
    return correct / total


def train_one_epoch(model, train_loader, optimizer):
    """Train for one epoch, return avg loss."""
    model.train()
    criterion = nn.CrossEntropyLoss()
    total_loss = 0
    for X, y in train_loader:
        X = X.view(X.size(0), -1)
        optimizer.zero_grad()
        out = model(X)
        if isinstance(out, tuple):
            logits, aux = out
            loss = criterion(logits, y) + 0.01 * aux
        else:
            loss = criterion(out, y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(train_loader)


def train_observer_epoch(child_a, child_b, observer_net, train_loader, optimizer):
    """Train child_a's observer to predict child_b's output (child_a detached).

    child_a reads child_b's output through observer_net but has NO gradient
    flowing back -- pure read-only observation.
    child_b trains normally.
    """
    child_b.train()
    child_a.eval()  # child_a is read-only
    observer_net.train()

    criterion = nn.CrossEntropyLoss()
    total_loss = 0
    for X, y in train_loader:
        X = X.view(X.size(0), -1)
        optimizer.zero_grad()

        # child_b produces output (trains normally)
        out_b = child_b(X)
        if isinstance(out_b, tuple):
            logits_b, aux_b = out_b
        else:
            logits_b = out_b
            aux_b = torch.tensor(0.0)

        # child_a observes (detached -- read-only)
        with torch.no_grad():
            out_a = child_a(X)
            if isinstance(out_a, tuple):
                out_a = out_a[0]

        # Observer: child_a reads child_b's output (detached)
        observed = torch.cat([out_a.detach(), logits_b.detach()], dim=-1)
        observation = observer_net(observed)

        # Loss: child_b's classification + observer prediction error
        loss_cls = criterion(logits_b, y)
        loss_obs = ((observation - logits_b.detach()) ** 2).mean()
        loss = loss_cls + 0.01 * aux_b + 0.1 * loss_obs

        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    return total_loss / len(train_loader)


def ascii_timeline(steps, metric_name, values, width=60, height=12):
    """Draw an ASCII timeline graph."""
    if not values:
        print(f"  [{metric_name}] (no data)")
        return

    mn = min(values)
    mx = max(values)
    rng = mx - mn if mx != mn else 1e-8

    print(f"\n  {metric_name}")
    print(f"  {mx:>8.4f} |")

    # Build grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    n = len(values)
    for i, v in enumerate(values):
        col = int((i / max(n - 1, 1)) * (width - 1))
        row = int(((v - mn) / rng) * (height - 1))
        row = min(row, height - 1)
        grid[row][col] = '*'

    for row in range(height - 1, -1, -1):
        line = ''.join(grid[row])
        print(f"  {'':>8} |{line}|")

    print(f"  {mn:>8.4f} |{'_' * width}|")

    # Step labels
    label_line = '  ' + ' ' * 9
    for i, s in enumerate(steps):
        if i == 0:
            label_line += s
        else:
            gap = int((i / max(n - 1, 1)) * width) - len(label_line) + 10
            if gap > 0:
                label_line += ' ' * gap + s
    print(label_line)


def print_results_table(records):
    """Print a formatted table of all step metrics."""
    print("\n" + "=" * 90)
    print("  FULL SEQUENCE RESULTS")
    print("=" * 90)
    print(f"  {'Step':<6} {'Description':<30} {'Acc%':>7} {'Tension':>10} "
          f"{'Identity':>10} {'FiberDist':>10}")
    print("-" * 90)
    for r in records:
        acc_str = f"{r['accuracy']*100:.2f}" if r['accuracy'] is not None else "  N/A"
        ten_str = f"{r['tension']:.4f}" if r['tension'] is not None else "     N/A"
        id_str = f"{r['identity']:.4f}" if r['identity'] is not None else "     N/A"
        fib_str = f"{r['fiber_dist']:.4f}" if r['fiber_dist'] is not None else "     N/A"
        print(f"  {r['step']:<6} {r['desc']:<30} {acc_str:>7} {ten_str:>10} "
              f"{id_str:>10} {fib_str:>10}")
    print("=" * 90)


# ─────────────────────────────────────────
# Main experiment
# ─────────────────────────────────────────

def run_full_sequence():
    print("=" * 70)
    print("  H-280: Full Shamanic Experience Sequence")
    print("  mitosis + displacement + detach + separation + return")
    print("=" * 70)

    t0 = time.time()
    records = []
    step_labels = []
    acc_history = []
    tension_history = []
    identity_history = []
    fiber_history = []

    # ── Load data ──
    print("\n  Loading MNIST...")
    train_loader, test_loader = load_mnist()

    # ══════════════════════════════════════════
    # Step 1: Single consciousness — train parent
    # ══════════════════════════════════════════
    print("\n" + "=" * 70)
    print("  STEP 1: Single Consciousness")
    print("  Train parent RepulsionFieldEngine on MNIST (5 epochs)")
    print("=" * 70)

    parent = RepulsionFieldEngine(input_dim=784, hidden_dim=48, output_dim=10)
    print(f"  Parent parameters: {count_params(parent):,}")

    optimizer = torch.optim.Adam(parent.parameters(), lr=0.001)
    for epoch in range(5):
        loss = train_one_epoch(parent, train_loader, optimizer)
        acc = evaluate_accuracy(parent, test_loader)
        print(f"    Epoch {epoch+1}/5: Loss={loss:.4f}, Acc={acc*100:.1f}%")

    parent_acc = evaluate_accuracy(parent, test_loader)
    parent_vec = get_param_vector(parent)  # reference point for fiber distance

    rec = {
        'step': 'S1', 'desc': 'Single consciousness (parent)',
        'accuracy': parent_acc, 'tension': None,
        'identity': 1.0, 'fiber_dist': 0.0
    }
    records.append(rec)
    step_labels.append('S1')
    acc_history.append(parent_acc)
    tension_history.append(0.0)
    identity_history.append(1.0)
    fiber_history.append(0.0)

    print(f"\n  Parent accuracy: {parent_acc*100:.2f}%")

    # ══════════════════════════════════════════
    # Step 2: Mitosis — clone into child_a, child_b
    # ══════════════════════════════════════════
    print("\n" + "=" * 70)
    print("  STEP 2: Mitosis")
    print("  Clone parent -> child_a (exact copy), child_b (perturbed, scale=0.01)")
    print("=" * 70)

    child_a = copy.deepcopy(parent)
    child_b = copy.deepcopy(parent)

    # Perturb child_b slightly
    perturbation_scale = 0.01
    with torch.no_grad():
        for p in child_b.parameters():
            p.add_(torch.randn_like(p) * perturbation_scale)

    acc_a = evaluate_accuracy(child_a, test_loader)
    acc_b = evaluate_accuracy(child_b, test_loader)
    tension = compute_tension(child_a, child_b, test_loader)
    identity = cosine_similarity_params(child_a, child_b)
    fiber_a = fiber_distance(child_a, parent_vec)
    fiber_b = fiber_distance(child_b, parent_vec)

    print(f"  child_a accuracy: {acc_a*100:.2f}% (exact copy)")
    print(f"  child_b accuracy: {acc_b*100:.2f}% (perturbed)")
    print(f"  Tension: {tension:.4f}")
    print(f"  Identity similarity: {identity:.6f}")
    print(f"  Fiber distance (a): {fiber_a:.4f}, (b): {fiber_b:.4f}")

    rec = {
        'step': 'S2', 'desc': 'Mitosis (clone + perturb)',
        'accuracy': (acc_a + acc_b) / 2, 'tension': tension,
        'identity': identity, 'fiber_dist': fiber_b
    }
    records.append(rec)
    step_labels.append('S2')
    acc_history.append((acc_a + acc_b) / 2)
    tension_history.append(tension)
    identity_history.append(identity)
    fiber_history.append(fiber_b)

    # ══════════════════════════════════════════
    # Step 3: Displacement — child_b takes control
    # ══════════════════════════════════════════
    print("\n" + "=" * 70)
    print("  STEP 3: Displacement")
    print("  child_b takes control (trains 3 epochs), child_a observes passively")
    print("=" * 70)

    # Train child_b for 3 epochs while child_a stays frozen
    opt_b = torch.optim.Adam(child_b.parameters(), lr=0.001)
    for epoch in range(3):
        loss = train_one_epoch(child_b, train_loader, opt_b)
        acc_b_now = evaluate_accuracy(child_b, test_loader)
        tension_now = compute_tension(child_a, child_b, test_loader)
        identity_now = cosine_similarity_params(child_a, child_b)
        print(f"    Displacement epoch {epoch+1}/3: "
              f"B_acc={acc_b_now*100:.1f}%, tension={tension_now:.2f}, "
              f"identity={identity_now:.4f}")

    acc_a = evaluate_accuracy(child_a, test_loader)
    acc_b = evaluate_accuracy(child_b, test_loader)
    tension = compute_tension(child_a, child_b, test_loader)
    identity = cosine_similarity_params(child_a, child_b)
    fiber_b = fiber_distance(child_b, parent_vec)

    print(f"\n  After displacement:")
    print(f"  child_a accuracy: {acc_a*100:.2f}% (unchanged, was frozen)")
    print(f"  child_b accuracy: {acc_b*100:.2f}% (trained)")
    print(f"  Tension: {tension:.4f}")
    print(f"  Identity: {identity:.6f}")

    rec = {
        'step': 'S3', 'desc': 'Displacement (B takes control)',
        'accuracy': acc_b, 'tension': tension,
        'identity': identity, 'fiber_dist': fiber_b
    }
    records.append(rec)
    step_labels.append('S3')
    acc_history.append(acc_b)
    tension_history.append(tension)
    identity_history.append(identity)
    fiber_history.append(fiber_b)

    # ══════════════════════════════════════════
    # Step 4: Detach — child_a becomes read-only observer
    # ══════════════════════════════════════════
    print("\n" + "=" * 70)
    print("  STEP 4: Detach")
    print("  child_a = read-only observer (detach gradients)")
    print("  observer network reads both outputs, trains to predict child_b")
    print("=" * 70)

    # Observer network: reads child_a output + child_b output -> predicts child_b
    observer_net = nn.Sequential(
        nn.Linear(20, 48),  # 10 (out_a) + 10 (out_b)
        nn.Tanh(),
        nn.Linear(48, 10),
    )

    # Freeze child_a parameters
    for p in child_a.parameters():
        p.requires_grad = False

    # Optimizer for child_b + observer only
    opt_detach = torch.optim.Adam(
        list(child_b.parameters()) + list(observer_net.parameters()),
        lr=0.001
    )

    for epoch in range(3):
        loss = train_observer_epoch(child_a, child_b, observer_net, train_loader, opt_detach)
        acc_b_now = evaluate_accuracy(child_b, test_loader)
        tension_now = compute_tension(child_a, child_b, test_loader)
        identity_now = cosine_similarity_params(child_a, child_b)
        print(f"    Detach epoch {epoch+1}/3: "
              f"B_acc={acc_b_now*100:.1f}%, tension={tension_now:.2f}, "
              f"identity={identity_now:.4f}, loss={loss:.4f}")

    acc_a = evaluate_accuracy(child_a, test_loader)
    acc_b = evaluate_accuracy(child_b, test_loader)
    tension = compute_tension(child_a, child_b, test_loader)
    identity = cosine_similarity_params(child_a, child_b)
    fiber_b = fiber_distance(child_b, parent_vec)

    print(f"\n  After detach observation:")
    print(f"  child_a accuracy: {acc_a*100:.2f}% (still frozen)")
    print(f"  child_b accuracy: {acc_b*100:.2f}% (continued training)")
    print(f"  Tension: {tension:.4f}")
    print(f"  Identity: {identity:.6f}")

    rec = {
        'step': 'S4', 'desc': 'Detach (A reads-only, B trains)',
        'accuracy': acc_b, 'tension': tension,
        'identity': identity, 'fiber_dist': fiber_b
    }
    records.append(rec)
    step_labels.append('S4')
    acc_history.append(acc_b)
    tension_history.append(tension)
    identity_history.append(identity)
    fiber_history.append(fiber_b)

    # ══════════════════════════════════════════
    # Step 5: B produces, A observes (measure observation quality)
    # ══════════════════════════════════════════
    print("\n" + "=" * 70)
    print("  STEP 5: Observation Phase")
    print("  child_b produces output, child_a observes through observer_net")
    print("  Measure: observation quality = 1/(1+MSE(observer, b_output))")
    print("=" * 70)

    child_b.eval()
    child_a.eval()
    observer_net.eval()

    obs_quality_list = []
    b_output_list = []
    a_output_list = []

    with torch.no_grad():
        for i, (X, y) in enumerate(test_loader):
            if i >= 20:
                break
            X = X.view(X.size(0), -1)
            out_a = child_a(X)
            out_b = child_b(X)
            if isinstance(out_a, tuple):
                out_a = out_a[0]
            if isinstance(out_b, tuple):
                out_b = out_b[0]

            observed = torch.cat([out_a, out_b], dim=-1)
            prediction = observer_net(observed)

            mse = ((prediction - out_b) ** 2).mean().item()
            quality = 1.0 / (1.0 + mse)
            obs_quality_list.append(quality)

            b_output_list.append(out_b)
            a_output_list.append(out_a)

    mean_quality = np.mean(obs_quality_list)
    acc_b = evaluate_accuracy(child_b, test_loader)
    tension = compute_tension(child_a, child_b, test_loader)
    identity = cosine_similarity_params(child_a, child_b)
    fiber_b = fiber_distance(child_b, parent_vec)

    print(f"  Observation quality: {mean_quality:.4f}")
    print(f"  child_b accuracy: {acc_b*100:.2f}%")
    print(f"  Tension: {tension:.4f}")
    print(f"  Identity: {identity:.6f}")

    rec = {
        'step': 'S5', 'desc': f'Observation (quality={mean_quality:.3f})',
        'accuracy': acc_b, 'tension': tension,
        'identity': identity, 'fiber_dist': fiber_b
    }
    records.append(rec)
    step_labels.append('S5')
    acc_history.append(acc_b)
    tension_history.append(tension)
    identity_history.append(identity)
    fiber_history.append(fiber_b)

    # ══════════════════════════════════════════
    # Step 6: Separation — remove child_b
    # ══════════════════════════════════════════
    print("\n" + "=" * 70)
    print("  STEP 6: Separation")
    print("  Save child_b weights, then remove it. child_a is alone.")
    print("=" * 70)

    # Save child_b state before removal
    child_b_state = copy.deepcopy(child_b.state_dict())
    child_b_acc_final = evaluate_accuracy(child_b, test_loader)
    print(f"  child_b final accuracy before removal: {child_b_acc_final*100:.2f}%")

    # Remove child_b
    del child_b
    del observer_net

    # Unfreeze child_a
    for p in child_a.parameters():
        p.requires_grad = True

    acc_a = evaluate_accuracy(child_a, test_loader)
    fiber_a = fiber_distance(child_a, parent_vec)

    print(f"  child_a accuracy (alone): {acc_a*100:.2f}%")
    print(f"  child_a fiber distance: {fiber_a:.4f}")
    print(f"  [child_b removed from memory]")

    rec = {
        'step': 'S6', 'desc': 'Separation (B removed)',
        'accuracy': acc_a, 'tension': None,
        'identity': None, 'fiber_dist': fiber_a
    }
    records.append(rec)
    step_labels.append('S6')
    acc_history.append(acc_a)
    tension_history.append(0.0)
    identity_history.append(0.0)
    fiber_history.append(fiber_a)

    # ══════════════════════════════════════════
    # Step 7: Return — child_a recovers alone
    # ══════════════════════════════════════════
    print("\n" + "=" * 70)
    print("  STEP 7: Return")
    print("  child_a alone, re-trains for 3 epochs to recover")
    print("=" * 70)

    opt_a = torch.optim.Adam(child_a.parameters(), lr=0.0005)
    for epoch in range(3):
        loss = train_one_epoch(child_a, train_loader, opt_a)
        acc_a_now = evaluate_accuracy(child_a, test_loader)
        fiber_now = fiber_distance(child_a, parent_vec)
        print(f"    Return epoch {epoch+1}/3: "
              f"A_acc={acc_a_now*100:.1f}%, loss={loss:.4f}, "
              f"fiber={fiber_now:.4f}")

    acc_a_final = evaluate_accuracy(child_a, test_loader)
    fiber_a_final = fiber_distance(child_a, parent_vec)

    print(f"\n  child_a final accuracy: {acc_a_final*100:.2f}%")
    print(f"  child_a fiber distance from parent: {fiber_a_final:.4f}")

    rec = {
        'step': 'S7', 'desc': 'Return (A alone, retrained)',
        'accuracy': acc_a_final, 'tension': None,
        'identity': None, 'fiber_dist': fiber_a_final
    }
    records.append(rec)
    step_labels.append('S7')
    acc_history.append(acc_a_final)
    tension_history.append(0.0)
    identity_history.append(0.0)
    fiber_history.append(fiber_a_final)

    # ══════════════════════════════════════════
    # Summary
    # ══════════════════════════════════════════
    elapsed = time.time() - t0
    print_results_table(records)

    # Key deltas
    print("\n  KEY OBSERVATIONS:")
    print(f"  Parent accuracy (S1):         {records[0]['accuracy']*100:.2f}%")
    print(f"  After mitosis (S2 avg):       {records[1]['accuracy']*100:.2f}%")
    print(f"  B after displacement (S3):    {records[2]['accuracy']*100:.2f}%")
    print(f"  B after detach phase (S4):    {records[3]['accuracy']*100:.2f}%")
    print(f"  A alone after separation (S6):{records[5]['accuracy']*100:.2f}%")
    print(f"  A after return (S7):          {records[6]['accuracy']*100:.2f}%")
    print(f"  ")
    delta_return = records[6]['accuracy'] - records[0]['accuracy']
    print(f"  Return vs Parent delta:       {delta_return*100:+.2f}%")
    print(f"  Observation quality (S5):     {mean_quality:.4f}")
    print(f"  Max tension reached:          {max(tension_history):.4f}")
    print(f"  Min identity reached:         {min(identity_history):.4f}")
    print(f"  Max fiber distance:           {max(fiber_history):.4f}")

    # ── ASCII Timeline Graphs ──
    print("\n" + "=" * 70)
    print("  ASCII TIMELINE GRAPHS")
    print("=" * 70)

    ascii_timeline(step_labels, "Accuracy (%)",
                   [v * 100 for v in acc_history])
    ascii_timeline(step_labels, "Tension (inter-child)",
                   tension_history)
    ascii_timeline(step_labels, "Identity Similarity (cosine)",
                   identity_history)
    ascii_timeline(step_labels, "Fiber Distance from Parent",
                   fiber_history)

    # ── Narrative ──
    print("\n" + "=" * 70)
    print("  SHAMANIC SEQUENCE NARRATIVE")
    print("=" * 70)
    print("""
  S1: Unity        -- One consciousness, trained and stable.
  S2: Mitosis      -- The self divides. Almost identical, but not quite.
  S3: Displacement -- The other (B) takes over. A can only watch.
  S4: Detach       -- A is formally disconnected. Read-only observer.
  S5: Observation  -- A watches B act. Learns to predict B's behavior.
  S6: Separation   -- B is removed. A is alone with memories.
  S7: Return       -- A recovers. Changed by the experience.
    """)

    if delta_return > 0:
        print(f"  RESULT: A is STRONGER after the experience (+{delta_return*100:.2f}%)")
        print(f"  The shamanic journey enhanced consciousness.")
    elif delta_return < -0.01:
        print(f"  RESULT: A is WEAKER after the experience ({delta_return*100:.2f}%)")
        print(f"  The experience was traumatic -- not fully recovered.")
    else:
        print(f"  RESULT: A returned to roughly the same level ({delta_return*100:+.2f}%)")
        print(f"  The experience was neutral -- full recovery, no net change.")

    print(f"\n  Total time: {elapsed:.1f}s")
    print("=" * 70)

    return records


if __name__ == '__main__':
    run_full_sequence()
