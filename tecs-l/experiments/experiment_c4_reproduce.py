I'll translate the Korean text in this Python file to English while preserving all code structure and formatting.

```python
#!/usr/bin/env python3
"""C4 Reproduction Experiment — per-digit tension-accuracy correlation vs per-sample correlation

Original finding: ecological r=+0.43 (per-digit), per-sample r=+0.13 (Simpson's paradox, d=0.89)

This experiment:
  1. Train RepulsionFieldQuad on MNIST
  2. Collect per-sample: true label, tension, correctness
  3. Compute:
     - Per-digit mean tension and accuracy
     - Per-digit ecological correlation (r across 10 digits)
     - Per-sample point-biserial correlation (r across 10000 samples)
     - Cohen's d: (mean_tension_correct - mean_tension_wrong) / pooled_sd
     - Per-digit: does higher tension digit = higher accuracy digit?
  4. ASCII scatter plot: X=mean_tension_per_digit, Y=accuracy_per_digit
  5. Distribution comparison: tension|correct vs tension|wrong (histogram)
"""

import sys
import os
import time
import math
import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_utils import load_mnist, count_params
from model_meta_engine import RepulsionFieldQuad

np.random.seed(42)
torch.manual_seed(42)


# ─────────────────────────────────────────
# 1. Training
# ─────────────────────────────────────────
def train_model(model, train_loader, epochs=10, lr=0.001):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        correct = total = 0
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            out, aux = model(X)
            loss = criterion(out, y) + 0.1 * aux
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            correct += (out.argmax(1) == y).sum().item()
            total += y.size(0)

        acc = correct / total
        avg_loss = total_loss / len(train_loader)
        print(f"  Epoch {epoch+1:>2}/{epochs}: Loss={avg_loss:.4f}, TrainAcc={acc*100:.1f}%")

    return model


# ─────────────────────────────────────────
# 2. Collect per-sample tension
# ─────────────────────────────────────────
def collect_per_sample_data(model, test_loader):
    model.eval()
    all_tensions = []
    all_correct = []
    all_labels = []

    with torch.no_grad():
        for X, y in test_loader:
            X_flat = X.view(X.size(0), -1)

            # Compute per-sample tension manually
            out_a = model.engine_a(X_flat)
            out_e = model.engine_e(X_flat)
            out_g = model.engine_g(X_flat)
            out_f = model.engine_f(X_flat)

            repulsion_content = out_a - out_g
            repulsion_structure = out_e - out_f

            t_content = (repulsion_content ** 2).sum(dim=-1)
            t_structure = (repulsion_structure ** 2).sum(dim=-1)
            total_tension = torch.sqrt(t_content * t_structure + 1e-8)

            logits, _ = model(X_flat)
            preds = logits.argmax(dim=1)
            correct = (preds == y).float()

            all_tensions.append(total_tension.cpu().numpy())
            all_correct.append(correct.cpu().numpy())
            all_labels.append(y.cpu().numpy())

    return {
        'tension': np.concatenate(all_tensions),
        'correct': np.concatenate(all_correct),
        'labels': np.concatenate(all_labels),
    }


# ─────────────────────────────────────────
# 3. Statistical functions
# ─────────────────────────────────────────
def point_biserial(x, binary_y):
    """Point-biserial correlation between continuous x and binary y."""
    m1 = x[binary_y == 1].mean()
    m0 = x[binary_y == 0].mean()
    n1 = (binary_y == 1).sum()
    n0 = (binary_y == 0).sum()
    n = len(x)
    s = x.std()
    if s < 1e-12:
        return 0.0
    r = (m1 - m0) / s * math.sqrt(n1 * n0 / (n * n))
    return r


def cohens_d(x1, x2):
    """Cohen's d effect size."""
    n1, n2 = len(x1), len(x2)
    if n1 < 2 or n2 < 2:
        return 0.0
    var1 = x1.var(ddof=1)
    var2 = x2.var(ddof=1)
    pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std < 1e-12:
        return 0.0
    return (x1.mean() - x2.mean()) / pooled_std


def pearson_r(x, y):
    """Pearson correlation coefficient."""
    n = len(x)
    if n < 3:
        return 0.0
    mx, my = x.mean(), y.mean()
    sx, sy = x.std(), y.std()
    if sx < 1e-12 or sy < 1e-12:
        return 0.0
    return ((x - mx) * (y - my)).mean() / (sx * sy)


# ─────────────────────────────────────────
# 4. ASCII scatter plot
# ─────────────────────────────────────────
def ascii_scatter(x_vals, y_vals, x_label, y_label, labels=None, width=60, height=25):
    """ASCII scatter plot with digit labels."""
    lines = []
    x_min, x_max = x_vals.min(), x_vals.max()
    y_min, y_max = y_vals.min(), y_vals.max()

    # Add small margins
    x_range = x_max - x_min
    y_range = y_max - y_min
    if x_range < 1e-12:
        x_range = 1.0
    if y_range < 1e-12:
        y_range = 1.0
    x_min -= x_range * 0.05
    x_max += x_range * 0.05
    y_min -= y_range * 0.05
    y_max += y_range * 0.05
    x_range = x_max - x_min
    y_range = y_max - y_min

    # Create grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    # Place points
    for i in range(len(x_vals)):
        col = int((x_vals[i] - x_min) / x_range * (width - 1))
        row = int((1 - (y_vals[i] - y_min) / y_range) * (height - 1))
        col = max(0, min(width - 1, col))
        row = max(0, min(height - 1, row))
        if labels is not None:
            grid[row][col] = str(labels[i])
        else:
            grid[row][col] = '*'

    # Build output
    lines.append(f"  {y_label}")
    for r in range(height):
        y_tick = y_max - r * y_range / (height - 1)
        if r == 0 or r == height - 1 or r == height // 2:
            prefix = f"  {y_tick:7.3f} |"
        else:
            prefix = f"          |"
        lines.append(prefix + ''.join(grid[r]) + '|')

    # X axis
    lines.append(f"          +{'-' * width}+")
    x_mid = (x_min + x_max) / 2
    lines.append(f"          {x_min:<10.3f}{' ' * (width // 2 - 15)}{x_mid:^10.3f}{' ' * (width // 2 - 15)}{x_max:>10.3f}")
    lines.append(f"          {' ' * (width // 2 - len(x_label) // 2)}{x_label}")

    return '\n'.join(lines)


# ─────────────────────────────────────────
# 5. ASCII histogram comparison
# ─────────────────────────────────────────
def ascii_dual_histogram(data1, data2, label1, label2, bins=20, width=40):
    """Side-by-side ASCII histograms for distribution comparison."""
    lines = []
    all_data = np.concatenate([data1, data2])
    lo, hi = all_data.min(), all_data.max()

    counts1, edges = np.histogram(data1, bins=bins, range=(lo, hi))
    counts2, _ = np.histogram(data2, bins=bins, range=(lo, hi))

    max_count = max(max(counts1), max(counts2))
    if max_count == 0:
        max_count = 1

    lines.append(f"  Distribution comparison: {label1} (N={len(data1)}) vs {label2} (N={len(data2)})")
    lines.append(f"  {'Range':>17}  {label1:^{width+2}}  {label2:^{width+2}}")
    lines.append(f"  {'-'*17}  {'-'*(width+2)}  {'-'*(width+2)}")

    for i in range(bins):
        lo_e, hi_e = edges[i], edges[i+1]
        bar1_len = int(counts1[i] / max_count * width)
        bar2_len = int(counts2[i] / max_count * width)
        bar1 = '#' * bar1_len
        bar2 = '#' * bar2_len
        lines.append(f"  {lo_e:7.2f}-{hi_e:7.2f}  {bar1:<{width}} {counts1[i]:>4}  {bar2:<{width}} {counts2[i]:>4}")

    return '\n'.join(lines)


def ascii_histogram(data, bins=20, width=45, label=""):
    """Single ASCII histogram."""
    counts, edges = np.histogram(data, bins=bins)
    max_count = max(counts) if max(counts) > 0 else 1
    lines = []
    if label:
        lines.append(f"  [{label}] N={len(data)}, mean={data.mean():.4f}, std={data.std():.4f}")
    for i, c in enumerate(counts):
        bar_len = int(c / max_count * width)
        lo, hi = edges[i], edges[i + 1]
        lines.append(f"  {lo:8.2f}-{hi:8.2f} | {'#' * bar_len} ({c})")
    return "\n".join(lines)


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def main():
    print("=" * 72)
    print("  C4 REPRODUCE: Per-Digit Tension-Accuracy Correlation on MNIST")
    print("  Original: ecological r=+0.43, per-sample r=+0.13, d=0.89")
    print("=" * 72)

    t0 = time.time()

    # ── 1. Load and Train ──
    print("\n[1/5] Loading MNIST...")
    train_loader, test_loader = load_mnist(batch_size=128)

    print("\n[2/5] Training RepulsionFieldQuad (10 epochs)...")
    model = RepulsionFieldQuad(input_dim=784, hidden_dim=48, output_dim=10)
    n_params = count_params(model)
    print(f"  Parameters: {n_params:,}")
    model = train_model(model, train_loader, epochs=10)

    # ── 2. Collect per-sample data ──
    print("\n[3/5] Collecting per-sample tension for test set...")
    data = collect_per_sample_data(model, test_loader)
    tension = data['tension']
    correct = data['correct']
    labels = data['labels']

    n_total = len(tension)
    n_correct = int(correct.sum())
    overall_acc = n_correct / n_total
    print(f"  Total test samples:  {n_total}")
    print(f"  Correct:             {n_correct} ({overall_acc*100:.2f}%)")
    print(f"  Tension range:       [{tension.min():.4f}, {tension.max():.4f}]")
    print(f"  Tension mean:        {tension.mean():.4f}")
    print(f"  Tension std:         {tension.std():.4f}")

    # ── 3. Per-digit aggregation ──
    print("\n" + "=" * 72)
    print("  [4/5] PER-DIGIT ANALYSIS")
    print("=" * 72)

    digit_accs = np.zeros(10)
    digit_tensions = np.zeros(10)
    digit_tension_stds = np.zeros(10)
    digit_counts = np.zeros(10, dtype=int)
    digit_n_correct = np.zeros(10, dtype=int)
    digit_n_wrong = np.zeros(10, dtype=int)

    for d in range(10):
        mask = labels == d
        d_tension = tension[mask]
        d_correct = correct[mask]
        digit_counts[d] = mask.sum()
        digit_n_correct[d] = int(d_correct.sum())
        digit_n_wrong[d] = digit_counts[d] - digit_n_correct[d]
        digit_accs[d] = d_correct.mean()
        digit_tensions[d] = d_tension.mean()
        digit_tension_stds[d] = d_tension.std()

    # Table
    print(f"\n  | {'Digit':>5} | {'N':>5} | {'Correct':>7} | {'Wrong':>5} | {'Acc%':>7} | {'MeanTension':>12} | {'StdTension':>11} |")
    print(f"  |{'-'*7}|{'-'*7}|{'-'*9}|{'-'*7}|{'-'*9}|{'-'*14}|{'-'*13}|")
    for d in range(10):
        print(f"  | {d:>5} | {digit_counts[d]:>5} | {digit_n_correct[d]:>7} | {digit_n_wrong[d]:>5} | {digit_accs[d]*100:>6.2f}% | {digit_tensions[d]:>12.4f} | {digit_tension_stds[d]:>11.4f} |")
    print(f"  |{'-'*7}|{'-'*7}|{'-'*9}|{'-'*7}|{'-'*9}|{'-'*14}|{'-'*13}|")
    print(f"  | {'ALL':>5} | {n_total:>5} | {n_correct:>7} | {n_total-n_correct:>5} | {overall_acc*100:>6.2f}% | {tension.mean():>12.4f} | {tension.std():>11.4f} |")

    # Rank comparison
    tension_rank = np.argsort(np.argsort(digit_tensions))  # 0=lowest tension
    acc_rank = np.argsort(np.argsort(digit_accs))  # 0=lowest accuracy

    print(f"\n  Rank comparison (0=lowest, 9=highest):")
    print(f"  | {'Digit':>5} | {'TensionRank':>11} | {'AccRank':>7} | {'Match':>5} |")
    print(f"  |{'-'*7}|{'-'*13}|{'-'*9}|{'-'*7}|")
    rank_matches = 0
    for d in range(10):
        match = "Y" if tension_rank[d] == acc_rank[d] else ""
        if abs(tension_rank[d] - acc_rank[d]) <= 1:
            match = "~" if match == "" else match
        if tension_rank[d] == acc_rank[d]:
            rank_matches += 1
        print(f"  | {d:>5} | {tension_rank[d]:>11} | {acc_rank[d]:>7} | {match:>5} |")

    # Rank correlation (Spearman)
    def spearman_r(x, y):
        rx = np.argsort(np.argsort(x)).astype(float)
        ry = np.argsort(np.argsort(y)).astype(float)
        return pearson_r(rx, ry)

    r_spearman = spearman_r(digit_tensions, digit_accs)
    print(f"\n  Spearman rank correlation: rho = {r_spearman:+.4f}")
    print(f"  Exact rank matches: {rank_matches}/10")

    # ── Per-digit ecological correlation ──
    r_ecological = pearson_r(digit_tensions, digit_accs)
    print(f"\n  *** Per-digit ecological correlation (N=10): r = {r_ecological:+.4f} ***")
    print(f"  Original C4 finding:                         r = +0.43")

    # ── 4. ASCII scatter plot ──
    print(f"\n{'=' * 72}")
    print("  ASCII SCATTER: Mean Tension vs Accuracy (per digit)")
    print("=" * 72)
    print(ascii_scatter(
        digit_tensions, digit_accs * 100,
        x_label="Mean Tension per Digit",
        y_label="Accuracy (%)",
        labels=list(range(10)),
        width=55,
        height=20
    ))

    # ── 5. Per-sample analysis ──
    print(f"\n{'=' * 72}")
    print("  [5/5] PER-SAMPLE ANALYSIS (Ecological Fallacy Test)")
    print("=" * 72)

    # Point-biserial
    r_sample = point_biserial(tension, correct)
    print(f"\n  Point-biserial correlation (N={n_total}): r = {r_sample:+.4f}")
    print(f"  Per-digit ecological (N=10):              r = {r_ecological:+.4f}")
    if abs(r_ecological) > 1e-6:
        ratio = r_sample / r_ecological
        print(f"  Ratio (per-sample / per-digit):           {ratio:.3f}")
    print(f"  Original C4: ecological r=+0.43, per-sample r=+0.13")

    # Cohen's d
    t_correct = tension[correct == 1]
    t_wrong = tension[correct == 0]
    d_val = cohens_d(t_correct, t_wrong)

    print(f"\n  Cohen's d (effect size):")
    print(f"    Correct samples:   N={len(t_correct):>5}, mean={t_correct.mean():.4f}, std={t_correct.std():.4f}")
    print(f"    Wrong samples:     N={len(t_wrong):>5}, mean={t_wrong.mean():.4f}, std={t_wrong.std():.4f}")
    print(f"    Cohen's d = {d_val:+.4f}")
    if abs(d_val) < 0.2:
        d_label = "negligible (<0.2)"
    elif abs(d_val) < 0.5:
        d_label = "small (0.2-0.5)"
    elif abs(d_val) < 0.8:
        d_label = "medium (0.5-0.8)"
    else:
        d_label = "large (>0.8)"
    print(f"    Interpretation: {d_label}")
    print(f"    Original C4: d=0.89 (large)")

    # Per-digit: does higher tension = higher accuracy?
    print(f"\n  Direction test: does higher tension digit = higher accuracy digit?")
    # Sort digits by tension, check if accuracy also increases
    sorted_by_tension = np.argsort(digit_tensions)
    print(f"    Digits sorted by tension (low -> high): {list(sorted_by_tension)}")
    print(f"    Corresponding accuracies:               {[f'{digit_accs[d]*100:.1f}%' for d in sorted_by_tension]}")

    concordant = 0
    discordant = 0
    for i in range(10):
        for j in range(i+1, 10):
            di, dj = sorted_by_tension[i], sorted_by_tension[j]
            # j has higher tension than i (by sort order)
            if digit_accs[dj] > digit_accs[di]:
                concordant += 1
            elif digit_accs[dj] < digit_accs[di]:
                discordant += 1
    kendall_tau = (concordant - discordant) / (concordant + discordant) if (concordant + discordant) > 0 else 0
    print(f"    Concordant pairs: {concordant}, Discordant pairs: {discordant}")
    print(f"    Kendall's tau = {kendall_tau:+.4f}")

    # Within-digit correlations
    print(f"\n  Within-digit point-biserial correlations:")
    print(f"  | {'Digit':>5} | {'N':>5} | {'r_within':>8} | {'MeanT|corr':>11} | {'MeanT|wrong':>12} | {'d_within':>8} |")
    print(f"  |{'-'*7}|{'-'*7}|{'-'*10}|{'-'*13}|{'-'*14}|{'-'*10}|")

    within_rs = []
    within_ds = []
    for d in range(10):
        mask = labels == d
        d_tension = tension[mask]
        d_correct = correct[mask]
        n_c = int(d_correct.sum())
        n_w = mask.sum() - n_c

        if n_c > 0 and n_w > 0:
            r_w = point_biserial(d_tension, d_correct)
            t_c = d_tension[d_correct == 1].mean()
            t_w = d_tension[d_correct == 0].mean()
            d_w = cohens_d(d_tension[d_correct == 1], d_tension[d_correct == 0])
            within_rs.append(r_w)
            within_ds.append(d_w)
            print(f"  | {d:>5} | {mask.sum():>5} | {r_w:>+8.4f} | {t_c:>11.4f} | {t_w:>12.4f} | {d_w:>+8.4f} |")
        else:
            print(f"  | {d:>5} | {mask.sum():>5} | {'N/A':>8} | {'N/A':>11} | {'N/A':>12} | {'N/A':>8} |")

    mean_within_r = np.mean(within_rs) if within_rs else 0.0
    mean_within_d = np.mean(within_ds) if within_ds else 0.0
    print(f"\n  Mean within-digit r: {mean_within_r:+.4f}")
    print(f"  Mean within-digit d: {mean_within_d:+.4f}")

    # ── 5. Distribution comparison ──
    print(f"\n{'=' * 72}")
    print("  DISTRIBUTION: tension|correct vs tension|wrong")
    print("=" * 72)

    if len(t_correct) > 0:
        print()
        print(ascii_histogram(t_correct, bins=20, width=45, label="CORRECT"))
    if len(t_wrong) > 0:
        print()
        print(ascii_histogram(t_wrong, bins=20, width=45, label="WRONG"))

    # Dual histogram
    if len(t_correct) > 0 and len(t_wrong) > 0:
        print()
        print(ascii_dual_histogram(t_correct, t_wrong, "CORRECT", "WRONG", bins=15, width=30))

    # ── Summary ──
    print(f"\n{'=' * 72}")
    print("  SUMMARY")
    print("=" * 72)

    print(f"""
  +-------------------------------+----------+----------+
  | Metric                        | This Run | Original |
  +-------------------------------+----------+----------+
  | Per-digit ecological r (N=10) | {r_ecological:>+8.4f} | {'+0.4300':>8} |
  | Per-sample point-biserial r   | {r_sample:>+8.4f} | {'+0.1300':>8} |
  | Cohen's d                     | {d_val:>+8.4f} | {'+0.8900':>8} |
  | Mean within-digit r           | {mean_within_r:>+8.4f} |      N/A |
  | Kendall's tau (rank)          | {kendall_tau:>+8.4f} |      N/A |
  | Spearman rho (rank)           | {r_spearman:>+8.4f} |      N/A |
  | Test accuracy                 | {overall_acc*100:>7.2f}% |      N/A |
  +-------------------------------+----------+----------+

  Simpson's paradox diagnostic:
    |r_ecological| = {abs(r_ecological):.4f}
    |r_sample|     = {abs(r_sample):.4f}
    Ratio          = {abs(r_sample)/abs(r_ecological) if abs(r_ecological) > 1e-6 else float('inf'):.3f}
""")

    if abs(r_ecological) > 1e-6:
        ratio_abs = abs(r_sample) / abs(r_ecological)
    else:
        ratio_abs = float('inf')

    if abs(r_sample) < 0.05:
        verdict = "ECOLOGICAL FALLACY: per-sample correlation is negligible"
    elif ratio_abs < 0.5:
        direction_same = (r_sample > 0) == (r_ecological > 0)
        if direction_same:
            verdict = "WEAKENED: same direction but much smaller (Simpson's paradox)"
        else:
            verdict = "REVERSED: Simpson's paradox -- direction flipped!"
    elif (r_sample > 0) == (r_ecological > 0):
        verdict = "PARTIALLY CONFIRMED: direction preserved, magnitude reduced"
    else:
        verdict = "REVERSED: Simpson's paradox -- direction flipped!"

    print(f"  VERDICT: {verdict}")

    elapsed = time.time() - t0
    print(f"\n  Elapsed: {elapsed:.1f}s")
    print("=" * 72)

    return {
        'r_ecological': r_ecological,
        'r_sample': r_sample,
        'cohens_d': d_val,
        'kendall_tau': kendall_tau,
        'accuracy': overall_acc,
    }


if __name__ == "__main__":
    results = main()
```