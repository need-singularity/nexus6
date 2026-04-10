#!/usr/bin/env python3
"""H-CX-10: Sparsity → Tension → Entropy Experiment

Hypothesis: The lower the frequency of a specific class in training data (the sparser it is),
      the higher the tension for that class during testing.
      Information theory: I(x) = -ln(p), therefore tension ~ freq^(-beta), beta ~ 1 for log.

Experimental design:
  Artificially adjust the number of training samples for digit 0:
    A: 10 (extremely sparse)
    B: 100
    C: 500
    D: 3000 (half)
    E: ~5400 (normal, balanced)

  Train RepulsionFieldEngine with each setting, then measure per-digit tension on test set.
  Key verification: Is digit 0's tension higher when training frequency is lower?
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import time

from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset

from model_meta_engine import RepulsionFieldEngine


def create_imbalanced_mnist(target_digit=0, target_count=None, batch_size=128, data_dir='data'):
    """Create imbalanced MNIST where target_digit has target_count samples."""
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    train_ds = datasets.MNIST(data_dir, train=True, download=True, transform=transform)
    test_ds = datasets.MNIST(data_dir, train=False, transform=transform)

    if target_count is not None:
        targets = np.array(train_ds.targets)
        target_indices = np.where(targets == target_digit)[0]
        other_indices = np.where(targets != target_digit)[0]

        # Subsample target digit
        if target_count < len(target_indices):
            np.random.seed(42)
            selected = np.random.choice(target_indices, target_count, replace=False)
        else:
            selected = target_indices

        combined = np.concatenate([selected, other_indices])
        np.random.shuffle(combined)
        train_ds = Subset(train_ds, combined.tolist())

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    return train_loader, test_loader


def train_model(model, train_loader, epochs=10, lr=0.001):
    """Train RepulsionFieldEngine."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            logits, aux = model(X)
            loss = criterion(logits, y) + 0.1 * aux
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"    Epoch {epoch+1:>2}/{epochs}: Loss={avg_loss:.4f}")


def measure_per_digit_tension(model, test_loader):
    """Measure per-digit tension on test set."""
    model.eval()
    digit_tensions = {d: [] for d in range(10)}
    digit_correct = {d: 0 for d in range(10)}
    digit_total = {d: 0 for d in range(10)}

    with torch.no_grad():
        for X, y in test_loader:
            X_flat = X.view(X.size(0), -1)

            # Forward pass to get logits
            out_plus = model.pole_plus(X_flat)
            out_minus = model.pole_minus(X_flat)
            repulsion = out_plus - out_minus
            tension = (repulsion ** 2).sum(dim=-1)  # per-sample tension

            # Also get predictions
            logits, _ = model(X_flat)
            preds = logits.argmax(dim=1)

            for i in range(len(y)):
                d = y[i].item()
                digit_tensions[d].append(tension[i].item())
                digit_total[d] += 1
                if preds[i].item() == d:
                    digit_correct[d] += 1

    results = {}
    for d in range(10):
        t_arr = np.array(digit_tensions[d])
        acc = digit_correct[d] / digit_total[d] if digit_total[d] > 0 else 0
        results[d] = {
            'mean_tension': t_arr.mean(),
            'std_tension': t_arr.std(),
            'median_tension': np.median(t_arr),
            'accuracy': acc,
            'n_test': digit_total[d],
        }
    return results


def run_experiment():
    print("=" * 70)
    print("H-CX-10: Sparsity -> Tension -> Entropy Experiment")
    print("=" * 70)
    print()

    # Experiment conditions: digit 0 training count
    conditions = {
        'A (10)':   10,
        'B (100)':  100,
        'C (500)':  500,
        'D (3000)': 3000,
        'E (full)': None,  # None = all available (~5923)
    }

    all_results = {}
    digit0_data = []  # (train_count, mean_tension, std_tension, accuracy)

    for label, count in conditions.items():
        print(f"\n{'─' * 50}")
        print(f"  Experiment {label}: digit 0 = {count if count else 'full (~5923)'} samples")
        print(f"{'─' * 50}")

        train_loader, test_loader = create_imbalanced_mnist(
            target_digit=0, target_count=count, batch_size=128
        )

        # Count actual digit 0 in training
        actual_count = 0
        total_train = 0
        for _, y in train_loader:
            actual_count += (y == 0).sum().item()
            total_train += len(y)
        print(f"  Actual digit 0 count: {actual_count} / {total_train} total")

        model = RepulsionFieldEngine(input_dim=784, hidden_dim=48, output_dim=10)
        torch.manual_seed(42)

        t0 = time.time()
        train_model(model, train_loader, epochs=10, lr=0.001)
        elapsed = time.time() - t0
        print(f"  Training time: {elapsed:.1f}s")

        results = measure_per_digit_tension(model, test_loader)
        all_results[label] = results

        d0 = results[0]
        digit0_data.append((actual_count, d0['mean_tension'], d0['std_tension'], d0['accuracy']))
        print(f"  Digit 0 tension: {d0['mean_tension']:.2f} +/- {d0['std_tension']:.2f}")
        print(f"  Digit 0 accuracy: {d0['accuracy']*100:.1f}%")

    # ─────────────────────────────────────────
    # Full per-digit tension table
    # ─────────────────────────────────────────
    print("\n")
    print("=" * 70)
    print("FULL PER-DIGIT TENSION TABLE")
    print("=" * 70)

    header = f"{'Digit':>6} |"
    for label in conditions:
        header += f" {label:>12} |"
    print(header)
    print("-" * len(header))

    for d in range(10):
        row = f"  {d:>4} |"
        for label in conditions:
            t = all_results[label][d]['mean_tension']
            row += f" {t:>12.2f} |"
        print(row)

    # Per-digit accuracy table
    print()
    print("PER-DIGIT ACCURACY TABLE")
    print("=" * 70)
    header = f"{'Digit':>6} |"
    for label in conditions:
        header += f" {label:>12} |"
    print(header)
    print("-" * len(header))

    for d in range(10):
        row = f"  {d:>4} |"
        for label in conditions:
            a = all_results[label][d]['accuracy']
            row += f" {a*100:>11.1f}% |"
        print(row)

    # ─────────────────────────────────────────
    # Core analysis: digit 0 sparsity vs tension
    # ─────────────────────────────────────────
    print("\n")
    print("=" * 70)
    print("CORE ANALYSIS: Digit 0 Training Count vs Tension")
    print("=" * 70)

    print(f"\n{'Train Count':>12} | {'Mean Tension':>14} | {'Std Tension':>12} | {'Accuracy':>10} | {'log(count)':>10}")
    print("-" * 70)
    for cnt, mt, st, acc in digit0_data:
        print(f"{cnt:>12} | {mt:>14.2f} | {st:>12.2f} | {acc*100:>9.1f}% | {np.log(cnt):>10.3f}")

    # ─────────────────────────────────────────
    # ASCII scatter plot: log(train_count) vs tension
    # ─────────────────────────────────────────
    print("\n")
    print("ASCII SCATTER: log(train_count) vs Mean Tension for Digit 0")
    print("=" * 70)

    counts = [d[0] for d in digit0_data]
    tensions = [d[1] for d in digit0_data]
    log_counts = [np.log(c) for c in counts]

    # Normalize for ASCII plot
    plot_width = 60
    plot_height = 20

    x_min, x_max = min(log_counts), max(log_counts)
    y_min, y_max = min(tensions), max(tensions)
    y_range = y_max - y_min if y_max > y_min else 1.0
    x_range = x_max - x_min if x_max > x_min else 1.0

    # Create grid
    grid = [[' ' for _ in range(plot_width)] for _ in range(plot_height)]

    # Plot points
    for i, (lc, t) in enumerate(zip(log_counts, tensions)):
        col = int((lc - x_min) / x_range * (plot_width - 1))
        row = int((1 - (t - y_min) / y_range) * (plot_height - 1))
        col = max(0, min(plot_width - 1, col))
        row = max(0, min(plot_height - 1, row))
        grid[row][col] = chr(ord('A') + i)  # A, B, C, D, E

    # Print with Y axis
    for r in range(plot_height):
        y_val = y_max - r / (plot_height - 1) * y_range
        if r == 0 or r == plot_height - 1 or r == plot_height // 2:
            label = f"{y_val:>8.1f} |"
        else:
            label = "         |"
        print(label + ''.join(grid[r]))

    # X axis
    print(f"         +{'─' * plot_width}")
    x_labels = f"         {x_min:.1f}" + " " * (plot_width - 10) + f"{x_max:.1f}"
    print(x_labels)
    print(f"         {'log(train_count)':^{plot_width}}")
    print()
    print("  Legend: A=10, B=100, C=500, D=3000, E=full(~5923)")

    # ─────────────────────────────────────────
    # Power law fit: tension = c * freq^(-beta)
    # ─────────────────────────────────────────
    print("\n")
    print("=" * 70)
    print("POWER LAW FIT: tension = c * count^(-beta)")
    print("=" * 70)

    log_c = np.array(log_counts)
    log_t = np.log(np.array(tensions))

    # Linear regression: log(tension) = log(c) - beta * log(count)
    # y = a + b*x where y=log(tension), x=log(count), b=-beta
    n = len(log_c)
    sx = log_c.sum()
    sy = log_t.sum()
    sxx = (log_c ** 2).sum()
    sxy = (log_c * log_t).sum()

    b = (n * sxy - sx * sy) / (n * sxx - sx ** 2)
    a = (sy - b * sx) / n

    beta = -b
    c_fit = np.exp(a)

    # R-squared
    y_pred = a + b * log_c
    ss_res = ((log_t - y_pred) ** 2).sum()
    ss_tot = ((log_t - log_t.mean()) ** 2).sum()
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    print(f"\n  Fitted: tension = {c_fit:.4f} * count^(-{beta:.4f})")
    print(f"  beta = {beta:.4f}")
    print(f"  R^2  = {r_squared:.4f}")
    print()

    # Comparison with information theory
    print("  Information theory comparison:")
    print(f"    If tension ~ -ln(p) ~ ln(N/count): beta should be ~1 for pure log relationship")
    print(f"    Observed beta = {beta:.4f}")
    if beta > 0.8 and beta < 1.2:
        print(f"    --> CLOSE TO 1: consistent with I(x) = -ln(p) !")
    elif beta > 0:
        print(f"    --> POSITIVE: sparsity increases tension (direction matches)")
        if beta < 0.8:
            print(f"    --> beta < 1: sublinear -- tension grows slower than -ln(p)")
        else:
            print(f"    --> beta > 1: superlinear -- tension grows faster than -ln(p)")
    else:
        print(f"    --> NEGATIVE: sparsity DECREASES tension (contradicts hypothesis!)")

    # Residuals
    print(f"\n  Fit residuals:")
    print(f"  {'Count':>8} | {'Actual log(T)':>14} | {'Predicted':>14} | {'Residual':>10}")
    print(f"  {'-'*55}")
    for i in range(n):
        print(f"  {counts[i]:>8} | {log_t[i]:>14.4f} | {y_pred[i]:>14.4f} | {log_t[i]-y_pred[i]:>10.4f}")

    # ─────────────────────────────────────────
    # Alternative fit: tension = a - b * ln(count)  (log model)
    # ─────────────────────────────────────────
    print("\n")
    print("ALTERNATIVE FIT: tension = a - b * ln(count)")
    print("=" * 70)

    t_arr = np.array(tensions)
    # Linear regression: tension = a + b * log(count), expect b < 0
    sy2 = t_arr.sum()
    sxy2 = (log_c * t_arr).sum()
    b2 = (n * sxy2 - sx * sy2) / (n * sxx - sx ** 2)
    a2 = (sy2 - b2 * sx) / n

    y_pred2 = a2 + b2 * log_c
    ss_res2 = ((t_arr - y_pred2) ** 2).sum()
    ss_tot2 = ((t_arr - t_arr.mean()) ** 2).sum()
    r_squared2 = 1 - ss_res2 / ss_tot2 if ss_tot2 > 0 else 0

    print(f"\n  Fitted: tension = {a2:.4f} + ({b2:.4f}) * ln(count)")
    print(f"  slope  = {b2:.4f} (expect negative)")
    print(f"  R^2    = {r_squared2:.4f}")

    # ─────────────────────────────────────────
    # Control: other digits (should NOT change much)
    # ─────────────────────────────────────────
    print("\n")
    print("=" * 70)
    print("CONTROL: Other digits' tension stability")
    print("=" * 70)
    print("  (Should remain roughly constant since only digit 0 was manipulated)")
    print()

    cond_labels = list(conditions.keys())
    for d in [1, 5, 9]:  # Sample control digits
        row = f"  Digit {d}: "
        vals = []
        for label in cond_labels:
            t = all_results[label][d]['mean_tension']
            vals.append(t)
            row += f"{label}={t:.1f}  "
        cv = np.std(vals) / np.mean(vals) * 100 if np.mean(vals) > 0 else 0
        row += f"  CV={cv:.1f}%"
        print(row)

    # ─────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────
    print("\n")
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    monotonic = all(tensions[i] >= tensions[i+1] for i in range(len(tensions)-1))
    print(f"\n  Hypothesis: sparser digit 0 -> higher tension")
    print(f"  Monotonic decrease with count? {'YES' if monotonic else 'NO'}")
    print(f"  Power law fit: tension = {c_fit:.2f} * count^(-{beta:.4f}), R^2 = {r_squared:.4f}")
    print(f"  Linear-log fit: tension = {a2:.2f} + ({b2:.2f}) * ln(count), R^2 = {r_squared2:.4f}")
    print(f"  Better fit: {'power law' if r_squared > r_squared2 else 'linear-log'}")
    print()

    # Tension ratio: most sparse vs balanced
    if tensions[-1] > 0:
        ratio = tensions[0] / tensions[-1]
        print(f"  Tension ratio (10 vs full): {ratio:.2f}x")
        expected_info_ratio = np.log(counts[-1] / 10) / np.log(counts[-1] / counts[-1])
        print(f"  If beta={beta:.2f}: predicted ratio = (5923/10)^{beta:.2f} = {(counts[-1]/10)**beta:.2f}x")
    print()
    print(f"  Verdict: ", end="")
    if beta > 0 and r_squared > 0.7:
        print("STRONG SUPPORT -- sparsity drives tension (R^2 > 0.7)")
    elif beta > 0 and r_squared > 0.4:
        print("MODERATE SUPPORT -- trend exists but noisy")
    elif beta > 0:
        print("WEAK SUPPORT -- positive direction but poor fit")
    else:
        print("NOT SUPPORTED -- beta <= 0")

    print()
    print("Done.")


if __name__ == '__main__':
    run_experiment()