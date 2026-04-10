#!/usr/bin/env python3
"""Causal test: does artificially increasing tension CAUSE higher accuracy?

All current evidence is correlational (high tension <-> high accuracy, d=0.89).
This experiment tests causation by:

1. Training RepulsionFieldQuad on MNIST (10 epochs) normally
2. At test time, artificially scaling tension_scale by factors: 0.0, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0
   - No retraining -- just change the scale during inference
3. Measuring accuracy, per-digit accuracy, and mean tension at each scale
4. Key question: tension=0 (equilibrium only) vs original -- how much does tension contribute?
5. ASCII graph of scale factor vs accuracy
"""

import sys
import os
import torch
import torch.nn.functional as F
import numpy as np
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model_utils import load_mnist, train_and_evaluate, count_params
from model_meta_engine import RepulsionFieldQuad


def evaluate_with_tension_scale(model, test_loader, scale_factor):
    """Evaluate model with artificially modified tension_scale."""
    model.eval()

    # Save original tension_scale value
    original_scale = model.tension_scale.data.clone()

    # Set new scale
    model.tension_scale.data = original_scale * scale_factor

    correct = 0
    total = 0
    per_digit_correct = torch.zeros(10)
    per_digit_total = torch.zeros(10)
    tensions_content = []
    tensions_structure = []

    with torch.no_grad():
        for X, y in test_loader:
            X = X.view(X.size(0), -1)
            out = model(X)
            if isinstance(out, tuple):
                out = out[0]
            preds = out.argmax(1)
            correct += (preds == y).sum().item()
            total += y.size(0)

            for digit in range(10):
                mask = (y == digit)
                per_digit_correct[digit] += (preds[mask] == y[mask]).sum().item()
                per_digit_total[digit] += mask.sum().item()

            tensions_content.append(model.tension_content)
            tensions_structure.append(model.tension_structure)

    # Restore original
    model.tension_scale.data = original_scale

    acc = correct / total
    per_digit_acc = (per_digit_correct / (per_digit_total + 1e-8)).numpy()
    mean_t_content = np.mean(tensions_content)
    mean_t_structure = np.mean(tensions_structure)

    return {
        'accuracy': acc,
        'per_digit_acc': per_digit_acc,
        'tension_content': mean_t_content,
        'tension_structure': mean_t_structure,
        'effective_scale': (original_scale * scale_factor).item(),
    }


def ascii_graph(x_vals, y_vals, x_label, y_label, width=60, height=15):
    """Draw ASCII graph."""
    y_min = min(y_vals)
    y_max = max(y_vals)
    y_range = y_max - y_min if y_max > y_min else 0.01

    # Add some padding
    y_min_plot = y_min - y_range * 0.05
    y_max_plot = y_max + y_range * 0.05
    y_range_plot = y_max_plot - y_min_plot

    lines = []
    lines.append(f"\n  {y_label}")
    lines.append(f"  {y_max_plot*100:.1f}% |")

    canvas = [[' ' for _ in range(width)] for _ in range(height)]

    # Plot points
    for i, (x, y) in enumerate(zip(x_vals, y_vals)):
        col = int((i / max(len(x_vals) - 1, 1)) * (width - 1))
        row = int((1 - (y - y_min_plot) / y_range_plot) * (height - 1))
        row = max(0, min(height - 1, row))
        col = max(0, min(width - 1, col))
        canvas[row][col] = '*'

    # Connect with dashes if adjacent
    for row_data in canvas:
        lines.append(f"         |{''.join(row_data)}|")

    lines.append(f"  {y_min_plot*100:.1f}% |{'_' * width}|")

    # X axis labels
    x_labels = [f"{v:.1f}" for v in x_vals]
    label_line = "         "
    spacing = width // max(len(x_vals) - 1, 1)
    for i, lab in enumerate(x_labels):
        pos = i * spacing
        label_line += lab.center(spacing if i < len(x_labels) - 1 else 5)
    lines.append(label_line)
    lines.append(f"         {' ' * (width // 2 - len(x_label) // 2)}{x_label}")

    return '\n'.join(lines)


def main():
    print("=" * 70)
    print("  CAUSAL TEST: Does Tension CAUSE Higher Accuracy?")
    print("=" * 70)
    print()
    print("  Design: Train once, then vary tension_scale at inference time")
    print("  If causal: accuracy should peak at original scale (inverted-U)")
    print("  If correlational only: accuracy might not change much")
    print()

    # ── Step 1: Load data ──
    print("[1/3] Loading MNIST...")
    train_loader, test_loader = load_mnist(batch_size=128)

    # ── Step 2: Train model ──
    print("[2/3] Training RepulsionFieldQuad (10 epochs)...")
    model = RepulsionFieldQuad(input_dim=784, hidden_dim=48, output_dim=10)
    params = count_params(model)
    print(f"       Parameters: {params:,}")

    t0 = time.time()
    train_losses, test_accs = train_and_evaluate(
        model, train_loader, test_loader,
        epochs=10, lr=0.001, aux_lambda=0.1,
        flatten=True, verbose=True
    )
    train_time = time.time() - t0
    print(f"       Training time: {train_time:.1f}s")
    print(f"       Final accuracy: {test_accs[-1]*100:.2f}%")

    # Record learned tension_scale
    learned_scale = model.tension_scale.data.item()
    print(f"       Learned tension_scale: {learned_scale:.4f}")
    print()

    # ── Step 3: Causal intervention ──
    print("[3/3] Causal intervention: varying tension_scale at inference...")
    print()

    scale_factors = [0.0, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    results = {}

    for sf in scale_factors:
        res = evaluate_with_tension_scale(model, test_loader, sf)
        results[sf] = res
        effective = res['effective_scale']
        print(f"  scale={sf:>5.1f}x  (effective={effective:>7.4f})  "
              f"Acc={res['accuracy']*100:>6.2f}%  "
              f"T_content={res['tension_content']:.4f}  "
              f"T_structure={res['tension_structure']:.4f}")

    # ── Analysis ──
    print()
    print("=" * 70)
    print("  ANALYSIS")
    print("=" * 70)

    # Baseline (scale=1.0) vs zero tension
    acc_original = results[1.0]['accuracy']
    acc_zero = results[0.0]['accuracy']
    tension_contribution = acc_original - acc_zero

    print()
    print(f"  Tension contribution to accuracy:")
    print(f"    Original (scale=1.0):  {acc_original*100:.2f}%")
    print(f"    Zero tension (scale=0): {acc_zero*100:.2f}%")
    print(f"    Difference:             {tension_contribution*100:+.2f}pp")
    print()

    if tension_contribution > 0.005:
        print(f"    -> Tension CONTRIBUTES {tension_contribution*100:.2f}pp to accuracy")
        print(f"       (removing tension degrades performance)")
    elif tension_contribution < -0.005:
        print(f"    -> Tension HURTS accuracy by {-tension_contribution*100:.2f}pp")
        print(f"       (equilibrium alone is better!)")
    else:
        print(f"    -> Tension has NEGLIGIBLE causal effect (<0.5pp)")
        print(f"       (correlation without causation)")

    # Find optimal scale
    best_sf = max(results, key=lambda k: results[k]['accuracy'])
    best_acc = results[best_sf]['accuracy']
    print()
    print(f"  Optimal scale factor: {best_sf}x (Acc={best_acc*100:.2f}%)")
    if best_sf == 1.0:
        print(f"    -> Original learned scale is optimal (training found the right level)")
    elif best_sf < 1.0:
        print(f"    -> Less tension is better (model over-tenses)")
    else:
        print(f"    -> More tension is better (model under-tenses)")

    # Check for inverted-U
    accs = [results[sf]['accuracy'] for sf in scale_factors]
    peak_idx = accs.index(max(accs))
    if 0 < peak_idx < len(accs) - 1:
        print(f"    -> INVERTED-U detected: peak at scale={scale_factors[peak_idx]}x")
        print(f"       (too little OR too much tension hurts performance)")
    elif peak_idx == 0:
        print(f"    -> MONOTONICALLY DECREASING: less tension = better")
    elif peak_idx == len(accs) - 1:
        print(f"    -> MONOTONICALLY INCREASING: more tension = better")

    # ── Per-digit analysis ──
    print()
    print("  Per-digit accuracy (scale=0.0 vs 1.0 vs best):")
    print(f"  {'Digit':>5}  {'Zero':>8}  {'Original':>8}  {'Best('+str(best_sf)+'x)':>10}  {'Delta(1-0)':>10}")
    print(f"  {'-'*5}  {'-'*8}  {'-'*8}  {'-'*10}  {'-'*10}")
    for d in range(10):
        a0 = results[0.0]['per_digit_acc'][d]
        a1 = results[1.0]['per_digit_acc'][d]
        ab = results[best_sf]['per_digit_acc'][d]
        delta = a1 - a0
        marker = " <-- tension helps most" if delta > 0.01 else ""
        print(f"  {d:>5}  {a0*100:>7.2f}%  {a1*100:>7.2f}%  {ab*100:>9.2f}%  {delta*100:>+9.2f}pp{marker}")

    # ── ASCII Graph ──
    print()
    print("=" * 70)
    print("  SCALE FACTOR vs ACCURACY")
    print("=" * 70)

    x_vals = scale_factors
    y_vals = [results[sf]['accuracy'] for sf in scale_factors]

    # Simple ASCII bar chart (more readable)
    max_bar = 50
    for sf in scale_factors:
        acc = results[sf]['accuracy']
        bar_len = int((acc / max(y_vals)) * max_bar)
        marker = " <-- original" if sf == 1.0 else ""
        marker = " <-- best" if sf == best_sf and sf != 1.0 else marker
        if sf == best_sf and sf == 1.0:
            marker = " <-- original & best"
        print(f"  {sf:>5.1f}x | {'#' * bar_len} {acc*100:.2f}%{marker}")

    # Detailed ASCII scatter
    print(ascii_graph(x_vals, y_vals, "Scale Factor (x)", "Accuracy"))

    # ── Causal verdict ──
    print()
    print("=" * 70)
    print("  CAUSAL VERDICT")
    print("=" * 70)
    print()

    # Compute effect sizes
    effects = {}
    for sf in scale_factors:
        effects[sf] = results[sf]['accuracy'] - acc_zero

    if tension_contribution > 0.01:
        # Check if there's an inverted-U (both sides decline from peak)
        if 0 < peak_idx < len(accs) - 1:
            verdict = "CAUSAL + OPTIMAL DOSE"
            detail = (
                f"Tension causally improtes accuracy (+{tension_contribution*100:.1f}pp)\n"
                f"  BUT too much tension hurts (inverted-U at scale={scale_factors[peak_idx]}x)\n"
                f"  This is DOSE-DEPENDENT causation: tension is like a drug with optimal dose"
            )
        else:
            verdict = "CAUSAL (MONOTONIC)"
            detail = (
                f"Tension causally improves accuracy (+{tension_contribution*100:.1f}pp)\n"
                f"  Effect is monotonic (more tension = more/less accuracy)\n"
                f"  No inverted-U detected at tested scales"
            )
    elif tension_contribution < -0.01:
        verdict = "ANTI-CAUSAL"
        detail = (
            f"Tension HURTS accuracy ({tension_contribution*100:.1f}pp)\n"
            f"  The correlation was misleading -- equilibrium alone is better"
        )
    else:
        verdict = "NOT CAUSAL (CORRELATION ONLY)"
        detail = (
            f"Removing tension barely changes accuracy ({tension_contribution*100:+.1f}pp)\n"
            f"  The d=0.89 correlation was likely due to confounds,\n"
            f"  not tension directly causing accuracy"
        )

    print(f"  Verdict: {verdict}")
    print(f"  {detail}")
    print()

    # Summary table
    print("  Summary of all scale factors:")
    print(f"  {'Scale':>7} {'Accuracy':>9} {'vs Zero':>8} {'vs Orig':>8}")
    print(f"  {'-------':>7} {'--------':>9} {'-------':>8} {'-------':>8}")
    for sf in scale_factors:
        acc = results[sf]['accuracy']
        vs_zero = acc - acc_zero
        vs_orig = acc - acc_original
        print(f"  {sf:>6.1f}x {acc*100:>8.2f}% {vs_zero*100:>+7.2f}pp {vs_orig*100:>+7.2f}pp")
    print()


if __name__ == '__main__':
    main()
