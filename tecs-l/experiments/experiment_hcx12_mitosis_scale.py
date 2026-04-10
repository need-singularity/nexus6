#!/usr/bin/env python3
"""H-CX-12 Experiment: Mitosis Differentiation Rate vs Scale

Key question: Is T_ab(final) constant regardless of mitosis scale?
- If T_ab(final) is constant -> property of architecture
- If ratio = T_ab(final)/T_ab(initial) is constant -> proportional differentiation
- If ratio ~ 27 for all scales -> H-CX-12 (sigma/tau)^3 confirmed

Protocol:
  1. Train parent RepulsionFieldEngine on MNIST for 10 epochs
  2. For each scale in [0.001, 0.005, 0.01, 0.05, 0.1, 0.5]:
     a) Mitosis: deepcopy + Gaussian noise * scale
     b) Measure T_ab(0) immediately after split
     c) Train children independently for 10 epochs
     d) Measure T_ab(final)
     e) Compute ratio = T_ab(final) / T_ab(0)
  3. Analyze: constant T_ab(final)? constant ratio? ratio ~ 27?
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import copy
import time
import sys

sys.path.insert(0, '/Users/ghost/Dev/logout')
from model_utils import load_mnist, count_params
from model_meta_engine import RepulsionFieldEngine


def compute_tension(model_a, model_b, test_loader, max_batches=10):
    """T_ab = mean |out_a - out_b|^2 over test data."""
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
    """Evaluate model accuracy on test set."""
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
    total_loss = 0.0
    for X, y in train_loader:
        X = X.view(X.size(0), -1)
        optimizer.zero_grad()
        out = model(X)
        if isinstance(out, tuple):
            logits, aux = out
            loss = criterion(logits, y) + 0.1 * aux
        else:
            loss = criterion(out, y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(train_loader)


def mitosis(parent, scale):
    """Split parent into two children with Gaussian perturbation."""
    child_a = copy.deepcopy(parent)
    child_b = copy.deepcopy(parent)
    with torch.no_grad():
        for pa, pb in zip(child_a.parameters(), child_b.parameters()):
            noise = torch.randn_like(pa) * scale
            pa.add_(noise)
            pb.add_(-noise)  # opposite direction
    return child_a, child_b


def main():
    print("=" * 70)
    print("  H-CX-12: Mitosis Differentiation Rate vs Scale")
    print("=" * 70)
    print()

    # Fix seed for reproducibility
    torch.manual_seed(42)
    np.random.seed(42)

    # Load MNIST
    print("[1] Loading MNIST...")
    train_loader, test_loader = load_mnist(batch_size=128)
    print(f"    Train: {len(train_loader.dataset)}, Test: {len(test_loader.dataset)}")

    # Train parent
    print("\n[2] Training parent RepulsionFieldEngine (10 epochs)...")
    parent = RepulsionFieldEngine(input_dim=784, hidden_dim=48, output_dim=10)
    print(f"    Parameters: {count_params(parent):,}")
    optimizer = torch.optim.Adam(parent.parameters(), lr=0.001)
    for epoch in range(10):
        loss = train_one_epoch(parent, train_loader, optimizer)
        if (epoch + 1) % 2 == 0 or epoch == 0:
            acc = evaluate_accuracy(parent, test_loader)
            print(f"    Epoch {epoch+1:>2}/10: Loss={loss:.4f}, Acc={acc*100:.1f}%")

    parent_acc = evaluate_accuracy(parent, test_loader)
    print(f"    Parent final accuracy: {parent_acc*100:.1f}%")

    # Mitosis at different scales
    scales = [0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
    results = []

    print(f"\n[3] Mitosis at {len(scales)} scales, each with 10 epoch child training...")
    print()

    for si, scale in enumerate(scales):
        print(f"  --- Scale {scale} ({si+1}/{len(scales)}) ---")
        t0 = time.time()

        # Reset seed per scale for fair comparison
        torch.manual_seed(42 + si)

        # Mitosis
        child_a, child_b = mitosis(parent, scale)

        # T_ab immediately after split
        t_ab_initial = compute_tension(child_a, child_b, test_loader)

        # Accuracy right after split
        acc_a_init = evaluate_accuracy(child_a, test_loader)
        acc_b_init = evaluate_accuracy(child_b, test_loader)

        print(f"    T_ab(0)={t_ab_initial:.6f}, Acc_a={acc_a_init*100:.1f}%, Acc_b={acc_b_init*100:.1f}%")

        # Train children independently for 10 epochs
        opt_a = torch.optim.Adam(child_a.parameters(), lr=0.001)
        opt_b = torch.optim.Adam(child_b.parameters(), lr=0.001)

        t_ab_trajectory = [t_ab_initial]

        for epoch in range(10):
            train_one_epoch(child_a, train_loader, opt_a)
            train_one_epoch(child_b, train_loader, opt_b)

            t_ab = compute_tension(child_a, child_b, test_loader)
            t_ab_trajectory.append(t_ab)

            if (epoch + 1) % 5 == 0:
                acc_a = evaluate_accuracy(child_a, test_loader)
                acc_b = evaluate_accuracy(child_b, test_loader)
                print(f"    Epoch {epoch+1:>2}: T_ab={t_ab:.4f}, Acc_a={acc_a*100:.1f}%, Acc_b={acc_b*100:.1f}%")

        t_ab_final = t_ab_trajectory[-1]
        ratio = t_ab_final / t_ab_initial if t_ab_initial > 1e-10 else float('inf')
        acc_a_final = evaluate_accuracy(child_a, test_loader)
        acc_b_final = evaluate_accuracy(child_b, test_loader)

        elapsed = time.time() - t0
        print(f"    T_ab(final)={t_ab_final:.4f}, ratio={ratio:.2f}, time={elapsed:.1f}s")
        print()

        results.append({
            'scale': scale,
            't_ab_initial': t_ab_initial,
            't_ab_final': t_ab_final,
            'ratio': ratio,
            'acc_a': acc_a_final,
            'acc_b': acc_b_final,
            'trajectory': t_ab_trajectory,
        })

    # ───────────────────────────────────────
    # Results table
    # ───────────────────────────────────────
    print("=" * 70)
    print("  RESULTS TABLE")
    print("=" * 70)
    print()
    print(f"  {'Scale':>8} | {'T_ab(0)':>12} | {'T_ab(final)':>12} | {'Ratio':>8} | {'Acc_A':>6} | {'Acc_B':>6}")
    print(f"  {'-'*8}-+-{'-'*12}-+-{'-'*12}-+-{'-'*8}-+-{'-'*6}-+-{'-'*6}")
    for r in results:
        print(f"  {r['scale']:>8.3f} | {r['t_ab_initial']:>12.6f} | {r['t_ab_final']:>12.4f} | {r['ratio']:>8.2f} | {r['acc_a']*100:>5.1f}% | {r['acc_b']*100:>5.1f}%")

    # ───────────────────────────────────────
    # Analysis
    # ───────────────────────────────────────
    print()
    print("=" * 70)
    print("  ANALYSIS")
    print("=" * 70)

    finals = [r['t_ab_final'] for r in results]
    ratios = [r['ratio'] for r in results]
    initials = [r['t_ab_initial'] for r in results]

    mean_final = np.mean(finals)
    std_final = np.std(finals)
    cv_final = std_final / mean_final if mean_final > 0 else float('inf')

    mean_ratio = np.mean(ratios)
    std_ratio = np.std(ratios)
    cv_ratio = std_ratio / mean_ratio if mean_ratio > 0 else float('inf')

    print(f"\n  T_ab(final): mean={mean_final:.4f}, std={std_final:.4f}, CV={cv_final:.4f}")
    print(f"  Ratio:       mean={mean_ratio:.2f},   std={std_ratio:.2f},   CV={cv_ratio:.4f}")
    print()

    # Check hypotheses
    print("  Hypothesis checks:")
    if cv_final < 0.1:
        print(f"    [STRONG] T_ab(final) is approximately CONSTANT (CV={cv_final:.4f} < 0.1)")
        print(f"             -> T_ab(final) is an architectural property!")
    elif cv_final < 0.3:
        print(f"    [WEAK]   T_ab(final) is roughly constant (CV={cv_final:.4f} < 0.3)")
    else:
        print(f"    [NO]     T_ab(final) varies with scale (CV={cv_final:.4f})")

    if cv_ratio < 0.1:
        print(f"    [STRONG] Ratio is approximately CONSTANT (CV={cv_ratio:.4f} < 0.1)")
        print(f"             -> Differentiation is proportional to initial perturbation!")
    elif cv_ratio < 0.3:
        print(f"    [WEAK]   Ratio is roughly constant (CV={cv_ratio:.4f} < 0.3)")
    else:
        print(f"    [NO]     Ratio varies with scale (CV={cv_ratio:.4f})")

    # Check if ratio ~ 27
    if abs(mean_ratio - 27) / 27 < 0.3:
        print(f"    [YES]    Mean ratio {mean_ratio:.2f} ~ 27 = (sigma/tau)^3  (error {abs(mean_ratio-27)/27*100:.1f}%)")
    else:
        print(f"    [NO]     Mean ratio {mean_ratio:.2f} != 27 (error {abs(mean_ratio-27)/27*100:.1f}%)")

    # ───────────────────────────────────────
    # ASCII graph: T_ab(final) vs scale
    # ───────────────────────────────────────
    print()
    print("=" * 70)
    print("  ASCII GRAPH: T_ab(final) vs Scale")
    print("=" * 70)

    max_val = max(finals)
    min_val = min(finals)
    bar_width = 40

    for r in results:
        if max_val > min_val:
            bar_len = int((r['t_ab_final'] - min_val) / (max_val - min_val) * bar_width)
        else:
            bar_len = bar_width // 2
        bar = '#' * max(bar_len, 1)
        print(f"  s={r['scale']:<6.3f} |{bar:<{bar_width}}| {r['t_ab_final']:.4f}")

    # ───────────────────────────────────────
    # ASCII graph: Ratio vs scale
    # ───────────────────────────────────────
    print()
    print("=" * 70)
    print("  ASCII GRAPH: Ratio (T_ab_final / T_ab_initial) vs Scale")
    print("=" * 70)

    max_r = max(ratios)
    min_r = min(ratios)

    for r in results:
        if max_r > min_r:
            bar_len = int((r['ratio'] - min_r) / (max_r - min_r) * bar_width)
        else:
            bar_len = bar_width // 2
        bar = '#' * max(bar_len, 1)
        print(f"  s={r['scale']:<6.3f} |{bar:<{bar_width}}| {r['ratio']:.2f}")

    # ───────────────────────────────────────
    # ASCII graph: T_ab trajectory over epochs (selected scales)
    # ───────────────────────────────────────
    print()
    print("=" * 70)
    print("  ASCII GRAPH: T_ab Trajectory (epoch 0..10)")
    print("=" * 70)

    # Show trajectory for min, mid, max scale
    show_indices = [0, len(scales)//2, len(scales)-1]
    all_trajs = [results[i]['trajectory'] for i in show_indices]
    global_max = max(max(t) for t in all_trajs)
    global_min = min(min(t) for t in all_trajs)
    height = 15

    labels = [f"s={results[i]['scale']}" for i in show_indices]
    symbols = ['*', 'o', '+']

    # Build grid
    grid = [[' ' for _ in range(11)] for _ in range(height)]
    for ti, traj in enumerate(all_trajs):
        for epoch, val in enumerate(traj):
            if global_max > global_min:
                row = int((val - global_min) / (global_max - global_min) * (height - 1))
            else:
                row = height // 2
            row = height - 1 - row  # invert
            if 0 <= row < height and 0 <= epoch < 11:
                grid[row][epoch] = symbols[ti]

    # Print
    for row_i, row in enumerate(grid):
        if global_max > global_min:
            val = global_max - row_i * (global_max - global_min) / (height - 1)
        else:
            val = global_max
        line = ''.join(row)
        print(f"  {val:>10.3f} |{line}|")
    print(f"  {'':>10} +{'-'*11}+")
    print(f"  {'':>10}  {'0':>1}{'':>4}{'5':>1}{'':>4}{'10':>2}")

    print(f"\n  Legend: {'  '.join(f'{s}={labels[i]}' for i, s in enumerate(symbols))}")

    # ───────────────────────────────────────
    # Correlation analysis
    # ───────────────────────────────────────
    print()
    print("=" * 70)
    print("  CORRELATION: log(scale) vs log(T_ab)")
    print("=" * 70)

    log_scales = np.log10([r['scale'] for r in results])
    log_initials = np.log10([r['t_ab_initial'] for r in results])
    log_finals = np.log10([max(r['t_ab_final'], 1e-10) for r in results])

    # Linear fit: log(T_ab_initial) vs log(scale)
    slope_init, intercept_init = np.polyfit(log_scales, log_initials, 1)
    # Linear fit: log(T_ab_final) vs log(scale)
    slope_final, intercept_final = np.polyfit(log_scales, log_finals, 1)

    print(f"\n  log(T_ab_initial) = {slope_init:.3f} * log(scale) + {intercept_init:.3f}")
    print(f"    -> T_ab(0) ~ scale^{slope_init:.2f}")
    print(f"    -> Expected: scale^2 (if noise adds linearly to each param)")

    print(f"\n  log(T_ab_final)   = {slope_final:.3f} * log(scale) + {intercept_final:.3f}")
    if abs(slope_final) < 0.3:
        print(f"    -> T_ab(final) ~ scale^{slope_final:.2f} ~ CONSTANT (slope near 0)")
        print(f"    -> ARCHITECTURAL PROPERTY CONFIRMED")
    else:
        print(f"    -> T_ab(final) ~ scale^{slope_final:.2f}")
        if abs(slope_final - slope_init) < 0.3:
            print(f"    -> Similar scaling as initial -> ratio is constant")

    # Final verdict
    print()
    print("=" * 70)
    print("  VERDICT")
    print("=" * 70)
    print()

    if cv_final < 0.15:
        print("  T_ab(final) IS CONSTANT regardless of mitosis scale.")
        print(f"  Value: {mean_final:.4f} +/- {std_final:.4f}")
        print("  -> Differentiation is an ARCHITECTURAL PROPERTY.")
        verdict = "CONSTANT_FINAL"
    elif cv_ratio < 0.15:
        print("  Ratio T_ab(final)/T_ab(0) IS CONSTANT.")
        print(f"  Value: {mean_ratio:.2f} +/- {std_ratio:.2f}")
        if abs(mean_ratio - 27) / 27 < 0.3:
            print(f"  -> Ratio ~ 27 = (sigma/tau)^3  CONFIRMED!")
        else:
            print(f"  -> Ratio = {mean_ratio:.2f} (not 27)")
        verdict = "CONSTANT_RATIO"
    else:
        print("  Neither T_ab(final) nor ratio is constant.")
        print(f"  T_ab(final) CV={cv_final:.3f}, Ratio CV={cv_ratio:.3f}")
        print(f"  -> Scale DOES affect differentiation dynamics.")
        verdict = "SCALE_DEPENDENT"

    print(f"\n  Verdict: {verdict}")
    print("=" * 70)


if __name__ == '__main__':
    main()
