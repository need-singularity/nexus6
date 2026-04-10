#!/usr/bin/env python3
"""H-283: Tension Nonlinear Threshold — Finding the accuracy breakpoint.

Tests at what base accuracy level tension starts helping by:
1. Training with N samples (100..60000) to create a range of base accuracies
2. For each N, trains TWO RepulsionFieldQuad models:
   - With tension (normal)
   - Without tension (tension_scale forced to 0 every step)
3. Records tension_effect = acc_with - acc_without at each data size
4. Plots ASCII graph: X=base_accuracy, Y=tension_effect

Expected: near-linear below ~70%, sharp increase above ~80%
"""

import sys
import os
import time
import copy

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torch.utils.data import DataLoader, Subset

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_utils import load_mnist, count_params
from model_meta_engine import RepulsionFieldQuad


def train_model(model, train_loader, test_loader, epochs=10, lr=0.001,
                zero_tension=False, verbose=False):
    """Train RepulsionFieldQuad. If zero_tension, clamp tension_scale to 0 each step."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            out = model(X)
            if isinstance(out, tuple):
                logits, aux = out
                loss = criterion(logits, y) + 0.1 * aux
            else:
                logits = out
                loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

            # Force tension_scale to 0 after each optimizer step
            if zero_tension:
                with torch.no_grad():
                    model.tension_scale.fill_(0.0)

        if verbose and ((epoch + 1) % 5 == 0 or epoch == 0):
            acc = evaluate(model, test_loader)
            tag = "[NO-TENSION]" if zero_tension else "[WITH-TENSION]"
            print(f"      {tag} Epoch {epoch+1:>2}/{epochs}: "
                  f"Loss={total_loss/len(train_loader):.4f}, Acc={acc*100:.1f}%")

    return evaluate(model, test_loader)


def evaluate(model, test_loader):
    """Return accuracy."""
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


def make_subset_loader(full_dataset, n_samples, batch_size=128):
    """Create a DataLoader with only n_samples from the full dataset."""
    indices = torch.randperm(len(full_dataset))[:n_samples].tolist()
    subset = Subset(full_dataset, indices)
    return DataLoader(subset, batch_size=batch_size, shuffle=True, num_workers=0)


def ascii_graph(x_vals, y_vals, x_label="Base Accuracy (%)", y_label="Tension Effect (pp)",
                width=60, height=20):
    """Print ASCII scatter/line plot."""
    if not x_vals:
        return

    x_min, x_max = min(x_vals), max(x_vals)
    y_min, y_max = min(y_vals), max(y_vals)

    # Add margin
    y_range = y_max - y_min if y_max != y_min else 1.0
    y_min -= y_range * 0.05
    y_max += y_range * 0.05
    y_range = y_max - y_min

    x_range = x_max - x_min if x_max != x_min else 1.0

    # Create grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    # Plot zero line if in range
    if y_min <= 0 <= y_max:
        zero_row = height - 1 - int((0 - y_min) / y_range * (height - 1))
        if 0 <= zero_row < height:
            for c in range(width):
                grid[zero_row][c] = '-'

    # Plot points
    for x, y in zip(x_vals, y_vals):
        col = int((x - x_min) / x_range * (width - 1)) if x_range > 0 else width // 2
        row = height - 1 - int((y - y_min) / y_range * (height - 1))
        col = max(0, min(width - 1, col))
        row = max(0, min(height - 1, row))
        grid[row][col] = '*'

    # Print
    print(f"\n  {y_label}")
    for r in range(height):
        y_val = y_max - r * y_range / (height - 1)
        label = f"{y_val:>7.2f}"
        row_str = ''.join(grid[r])
        print(f"  {label} |{row_str}|")

    print(f"  {' ' * 7} +{'-' * width}+")
    # X axis labels
    x_labels = f"  {' ' * 8}{x_min:.0f}%{' ' * (width // 2 - 8)}" \
               f"{(x_min + x_max) / 2:.0f}%{' ' * (width // 2 - 8)}{x_max:.0f}%"
    print(x_labels)
    print(f"  {' ' * 20}{x_label}")


def main():
    print("=" * 70)
    print("  H-283: Tension Nonlinear Threshold Experiment")
    print("  Finding the accuracy breakpoint where tension stops being useful")
    print("=" * 70)

    torch.manual_seed(42)
    np.random.seed(42)

    # Load full MNIST
    from torchvision import datasets, transforms
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    full_train_ds = datasets.MNIST('data', train=True, download=True, transform=transform)
    test_ds = datasets.MNIST('data', train=False, transform=transform)
    test_loader = DataLoader(test_ds, batch_size=256, shuffle=False, num_workers=0)

    sample_sizes = [100, 500, 1000, 2000, 5000, 10000, 30000, 60000]
    epochs = 10
    n_runs = 3  # Average over 3 runs for stability

    results = []

    for n_samples in sample_sizes:
        print(f"\n{'─' * 60}")
        print(f"  N = {n_samples:,} training samples")
        print(f"{'─' * 60}")

        accs_with = []
        accs_without = []

        for run in range(n_runs):
            seed = 42 + run * 1000
            torch.manual_seed(seed)
            np.random.seed(seed)

            train_loader = make_subset_loader(full_train_ds, n_samples, batch_size=128)

            # Model WITH tension
            torch.manual_seed(seed)
            model_with = RepulsionFieldQuad(input_dim=784, hidden_dim=48, output_dim=10)
            acc_with = train_model(model_with, train_loader, test_loader,
                                   epochs=epochs, lr=0.001,
                                   zero_tension=False, verbose=(run == 0))

            # Model WITHOUT tension (same seed for fair comparison)
            torch.manual_seed(seed)
            model_without = RepulsionFieldQuad(input_dim=784, hidden_dim=48, output_dim=10)
            acc_without = train_model(model_without, train_loader, test_loader,
                                      epochs=epochs, lr=0.001,
                                      zero_tension=True, verbose=(run == 0))

            accs_with.append(acc_with)
            accs_without.append(acc_without)

            print(f"    Run {run+1}/{n_runs}: with={acc_with*100:.2f}%, "
                  f"without={acc_without*100:.2f}%, "
                  f"delta={((acc_with - acc_without)*100):+.2f}pp")

        mean_with = np.mean(accs_with)
        mean_without = np.mean(accs_without)
        std_with = np.std(accs_with)
        std_without = np.std(accs_without)
        delta = mean_with - mean_without

        results.append({
            'n_samples': n_samples,
            'acc_with': mean_with,
            'acc_without': mean_without,
            'std_with': std_with,
            'std_without': std_without,
            'delta': delta,
            'base_acc': mean_without,  # base = no-tension accuracy
        })

        print(f"  >> Mean: with={mean_with*100:.2f}% (+/-{std_with*100:.2f}), "
              f"without={mean_without*100:.2f}% (+/-{std_without*100:.2f}), "
              f"delta={delta*100:+.2f}pp")

    # ═══════════════════════════════════════════
    # Results table
    # ═══════════════════════════════════════════
    print("\n" + "=" * 80)
    print("  RESULTS TABLE")
    print("=" * 80)
    print(f"  {'N':>7} | {'Base Acc':>9} | {'With Tension':>13} | {'No Tension':>12} | {'Delta (pp)':>11} | {'Std W':>7} | {'Std N':>7}")
    print(f"  {'-'*7}-+-{'-'*9}-+-{'-'*13}-+-{'-'*12}-+-{'-'*11}-+-{'-'*7}-+-{'-'*7}")
    for r in results:
        print(f"  {r['n_samples']:>7,} | {r['base_acc']*100:>8.2f}% | {r['acc_with']*100:>12.2f}% | "
              f"{r['acc_without']*100:>11.2f}% | {r['delta']*100:>+10.2f}pp | "
              f"{r['std_with']*100:>6.2f} | {r['std_without']*100:>6.2f}")

    # ═══════════════════════════════════════════
    # ASCII Graph: Base Accuracy vs Tension Effect
    # ═══════════════════════════════════════════
    x_vals = [r['base_acc'] * 100 for r in results]
    y_vals = [r['delta'] * 100 for r in results]

    print("\n" + "=" * 80)
    print("  ASCII GRAPH: Base Accuracy vs Tension Effect")
    print("  X = Base accuracy (no-tension model, %)")
    print("  Y = Tension effect (with - without, percentage points)")
    print("=" * 80)
    ascii_graph(x_vals, y_vals,
                x_label="Base Accuracy (%)",
                y_label="Tension Effect (pp)",
                width=60, height=20)

    # ═══════════════════════════════════════════
    # Analysis: Find the breakpoint
    # ═══════════════════════════════════════════
    print("\n" + "=" * 80)
    print("  ANALYSIS: Breakpoint Detection")
    print("=" * 80)

    # Find where delta transitions from negative/zero to positive
    positive_deltas = [(r['base_acc'], r['delta']) for r in results if r['delta'] > 0.001]
    negative_deltas = [(r['base_acc'], r['delta']) for r in results if r['delta'] <= 0.001]

    if positive_deltas:
        breakpoint_acc = min(acc for acc, _ in positive_deltas) * 100
        print(f"  Tension starts helping at base accuracy ~{breakpoint_acc:.1f}%")
        max_effect = max(d for _, d in positive_deltas) * 100
        max_effect_acc = [acc for acc, d in positive_deltas if d * 100 == max_effect][0] * 100
        print(f"  Maximum tension effect: {max_effect:+.2f}pp at base accuracy {max_effect_acc:.1f}%")
    else:
        print("  Tension never showed positive effect in this experiment.")

    if negative_deltas:
        worst_effect = min(d for _, d in negative_deltas) * 100
        worst_acc = [acc for acc, d in negative_deltas if d * 100 == worst_effect][0] * 100
        print(f"  Worst tension effect: {worst_effect:+.2f}pp at base accuracy {worst_acc:.1f}%")

    # Check for nonlinearity
    if len(results) >= 4:
        deltas = [r['delta'] * 100 for r in results]
        first_half = np.mean(deltas[:len(deltas)//2])
        second_half = np.mean(deltas[len(deltas)//2:])
        print(f"\n  Low-accuracy regime mean delta:  {first_half:+.2f}pp")
        print(f"  High-accuracy regime mean delta: {second_half:+.2f}pp")
        if second_half > first_half + 0.5:
            print("  >> NONLINEAR: tension helps MORE at higher base accuracy")
        elif abs(second_half - first_half) < 0.5:
            print("  >> APPROXIMATELY LINEAR: tension effect roughly constant")
        else:
            print("  >> INVERSE: tension helps MORE at lower base accuracy")

    # Second ASCII graph: N_samples vs both accuracies
    print("\n" + "=" * 80)
    print("  ASCII GRAPH: Training Samples vs Accuracy (both models)")
    print("=" * 80)
    print(f"\n  {'N':>7} | With  | Without | Bar (With=# Without=.)")
    print(f"  {'-'*7}-+-------+---------+{'─'*40}")
    for r in results:
        bar_with = int(r['acc_with'] * 40)
        bar_without = int(r['acc_without'] * 40)
        bar = ''
        for i in range(40):
            if i < min(bar_with, bar_without):
                bar += '#'
            elif i < bar_with:
                bar += '#'
            elif i < bar_without:
                bar += '.'
            else:
                bar += ' '
        # Mark the divergence
        if bar_with > bar_without:
            diff_bar = '.' * bar_without + '+' * (bar_with - bar_without)
            diff_bar = diff_bar + ' ' * (40 - len(diff_bar))
        else:
            diff_bar = bar

        with_str = f"{r['acc_with']*100:.1f}%"
        without_str = f"{r['acc_without']*100:.1f}%"
        n_str = f"{r['n_samples']:>7,}"
        print(f"  {n_str} | {with_str:>5} | {without_str:>7} | {'#' * bar_with}{'.' * max(0, bar_without - bar_with)}")

    print(f"\n  Done. Total time measured per-model in training loop.")
    print("=" * 80)


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"\n  Total wall time: {time.time() - t0:.1f}s")
