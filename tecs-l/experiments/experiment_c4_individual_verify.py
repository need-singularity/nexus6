```python
#!/usr/bin/env python3
"""C4 Individual Sample Verification — tension-accuracy correlation ecological fallacy check

C4 claim: tension-accuracy correlation r=+0.43 (per-digit, N=10)
C5 lesson: per-digit r=-0.79 -> per-sample r=-0.26 (ecological fallacy)

This experiment: Train RepulsionFieldQuad on MNIST then
  - Collect tension and correctness for each of 10,000 test samples
  - Point-biserial correlation, logistic regression, AUC, Bootstrap CI
  - Per-digit internal vs between-digit decomposition
"""

import sys
import os
import time
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model_utils import load_mnist, count_params
from model_meta_engine import RepulsionFieldQuad

np.random.seed(42)
torch.manual_seed(42)


# ─────────────────────────────────────────
# 1. Train RepulsionFieldQuad
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
    """Extract per-sample tension, prediction correctness, label, logits."""
    model.eval()
    all_tensions = []
    all_correct = []
    all_labels = []
    all_t_content = []
    all_t_structure = []

    with torch.no_grad():
        for X, y in test_loader:
            X_flat = X.view(X.size(0), -1)

            # Manually compute forward to get per-sample tension
            out_a = model.engine_a(X_flat)
            out_e = model.engine_e(X_flat)
            out_g = model.engine_g(X_flat)
            out_f = model.engine_f(X_flat)

            repulsion_content = out_a - out_g
            repulsion_structure = out_e - out_f

            t_content = (repulsion_content ** 2).sum(dim=-1)   # (batch,)
            t_structure = (repulsion_structure ** 2).sum(dim=-1)  # (batch,)
            total_tension = torch.sqrt(t_content * t_structure + 1e-8)  # (batch,)

            # Get predictions via normal forward
            logits, _ = model(X_flat)
            preds = logits.argmax(dim=1)
            correct = (preds == y).float()

            all_tensions.append(total_tension.cpu().numpy())
            all_correct.append(correct.cpu().numpy())
            all_labels.append(y.cpu().numpy())
            all_t_content.append(t_content.cpu().numpy())
            all_t_structure.append(t_structure.cpu().numpy())

    return {
        'tension': np.concatenate(all_tensions),
        'correct': np.concatenate(all_correct),
        'labels': np.concatenate(all_labels),
        't_content': np.concatenate(all_t_content),
        't_structure': np.concatenate(all_t_structure),
    }


# ─────────────────────────────────────────
# 3. Statistical analysis
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


def bootstrap_correlation(x, y, n_boot=1000, ci=0.95):
    """Bootstrap CI for point-biserial correlation."""
    rng = np.random.RandomState(42)
    n = len(x)
    rs = []
    for _ in range(n_boot):
        idx = rng.choice(n, n, replace=True)
        r = point_biserial(x[idx], y[idx])
        rs.append(r)
    rs = np.sort(rs)
    lo = rs[int((1 - ci) / 2 * n_boot)]
    hi = rs[int((1 + ci) / 2 * n_boot)]
    return np.mean(rs), lo, hi


def logistic_regression_simple(x, y, lr=0.01, steps=2000):
    """Simple logistic regression: P(y=1) = sigmoid(a + b*x)."""
    x_norm = (x - x.mean()) / (x.std() + 1e-12)
    a = 0.0
    b = 0.0
    n = len(x)
    for _ in range(steps):
        z = a + b * x_norm
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -20, 20)))
        grad_a = (p - y).mean()
        grad_b = ((p - y) * x_norm).mean()
        a -= lr * grad_a
        b -= lr * grad_b
    # Return predictions on original scale
    z_final = a + b * x_norm
    p_final = 1.0 / (1.0 + np.exp(-np.clip(z_final, -20, 20)))
    return a, b, p_final


def compute_auc(y_true, y_score):
    """Compute AUC using the trapezoidal rule."""
    # Sort by score descending
    order = np.argsort(-y_score)
    y_sorted = y_true[order]

    n_pos = y_true.sum()
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5

    tpr_prev = 0.0
    fpr_prev = 0.0
    auc = 0.0
    tp = 0
    fp = 0

    for i in range(len(y_sorted)):
        if y_sorted[i] == 1:
            tp += 1
        else:
            fp += 1
        tpr = tp / n_pos
        fpr = fp / n_neg
        auc += (fpr - fpr_prev) * (tpr + tpr_prev) / 2
        tpr_prev = tpr
        fpr_prev = fpr

    return auc


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


def ascii_histogram(data, bins=20, width=40, label=""):
    """ASCII histogram."""
    counts, edges = np.histogram(data, bins=bins)
    max_count = max(counts) if max(counts) > 0 else 1
    lines = []
    if label:
        lines.append(f"  [{label}] N={len(data)}, mean={data.mean():.4f}, std={data.std():.4f}")
    for i, c in enumerate(counts):
        bar_len = int(c / max_count * width)
        lo, hi = edges[i], edges[i + 1]
        lines.append(f"  {lo:7.2f}-{hi:7.2f} | {'#' * bar_len} ({c})")
    return "\n".join(lines)


def overlap_coefficient(x1, x2, bins=100):
    """Overlap coefficient between two distributions."""
    lo = min(x1.min(), x2.min())
    hi = max(x1.max(), x2.max())
    h1, _ = np.histogram(x1, bins=bins, range=(lo, hi), density=True)
    h2, _ = np.histogram(x2, bins=bins, range=(lo, hi), density=True)
    h1 = h1 / (h1.sum() + 1e-12)
    h2 = h2 / (h2.sum() + 1e-12)
    return np.minimum(h1, h2).sum()


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def main():
    print("=" * 70)
    print("  C4 Individual Sample Verification")
    print("  Tension-Accuracy Correlation: Per-Digit vs Per-Sample")
    print("=" * 70)

    t0 = time.time()

    # Load data
    print("\n[1/5] Loading MNIST...")
    train_loader, test_loader = load_mnist(batch_size=128)

    # Train model
    print("\n[2/5] Training RepulsionFieldQuad (10 epochs)...")
    model = RepulsionFieldQuad(input_dim=784, hidden_dim=48, output_dim=10)
    n_params = count_params(model)
    print(f"  Parameters: {n_params:,}")
    model = train_model(model, train_loader, epochs=10)

    # Collect per-sample data
    print("\n[3/5] Collecting per-sample tension for 10,000 test samples...")
    data = collect_per_sample_data(model, test_loader)
    tension = data['tension']
    correct = data['correct']
    labels = data['labels']

    n_total = len(tension)
    n_correct = int(correct.sum())
    overall_acc = n_correct / n_total
    print(f"  Total samples: {n_total}")
    print(f"  Correct: {n_correct} ({overall_acc*100:.1f}%)")
    print(f"  Tension range: [{tension.min():.4f}, {tension.max():.4f}]")
    print(f"  Tension mean={tension.mean():.4f}, std={tension.std():.4f}")

    # ─────────────────────────────────────
    # 4. Per-digit aggregation (reproduce C4)
    # ─────────────────────────────────────
    print("\n[4/5] Per-digit analysis (reproducing C4)...")
    print("\n### Per-Digit Summary (C4 original level)")
    print(f"  {'Digit':>5} {'N':>5} {'Acc%':>7} {'MeanTens':>10} {'StdTens':>10}")
    print(f"  {'-'*5:>5} {'-'*5:>5} {'-'*7:>7} {'-'*10:>10} {'-'*10:>10}")

    digit_accs = []
    digit_tensions = []

    for d in range(10):
        mask = labels == d
        d_tension = tension[mask]
        d_correct = correct[mask]
        d_acc = d_correct.mean()
        d_mean_t = d_tension.mean()
        digit_accs.append(d_acc)
        digit_tensions.append(d_mean_t)
        print(f"  {d:>5} {mask.sum():>5} {d_acc*100:>7.2f} {d_mean_t:>10.4f} {d_tension.std():>10.4f}")

    digit_accs = np.array(digit_accs)
    digit_tensions = np.array(digit_tensions)

    # Per-digit correlation (C4 original)
    r_digit = np.corrcoef(digit_tensions, digit_accs)[0, 1]
    print(f"\n  Per-digit correlation (N=10): r = {r_digit:+.4f}")
    print(f"  C4 claimed: r = +0.43")

    # ─────────────────────────────────────
    # 5. Per-sample analysis (ecological fallacy test)
    # ─────────────────────────────────────
    print("\n[5/5] Per-sample analysis (ecological fallacy test)...")

    # Point-biserial correlation
    r_sample = point_biserial(tension, correct)
    print(f"\n### Point-Biserial Correlation")
    print(f"  Per-sample (N={n_total}):  r = {r_sample:+.4f}")
    print(f"  Per-digit  (N=10):     r = {r_digit:+.4f}")
    ratio = r_sample / r_digit if abs(r_digit) > 1e-6 else float('inf')
    print(f"  Ratio (sample/digit):  {ratio:.2f}")

    # Bootstrap CI
    print(f"\n### Bootstrap CI (1000 resamples)")
    boot_mean, boot_lo, boot_hi = bootstrap_correlation(tension, correct, n_boot=1000)
    print(f"  Bootstrap mean: r = {boot_mean:+.4f}")
    print(f"  95% CI: [{boot_lo:+.4f}, {boot_hi:+.4f}]")

    # Logistic regression
    print(f"\n### Logistic Regression: P(correct) = sigmoid(a + b*tension)")
    a, b, p_pred = logistic_regression_simple(tension, correct)
    print(f"  Intercept (a): {a:+.4f}")
    print(f"  Slope (b):     {b:+.4f}")
    direction = "higher tension -> more correct" if b > 0 else "higher tension -> less correct"
    print(f"  Direction:     {direction}")

    # AUC
    auc = compute_auc(correct.astype(int), tension)
    print(f"\n### AUC (tension alone predicting correctness)")
    print(f"  AUC = {auc:.4f}")
    auc_interp = "better than chance" if auc > 0.5 else "worse than chance (inverted)" if auc < 0.5 else "chance level"
    print(f"  Interpretation: {auc_interp}")
    print(f"  (0.5 = random, 1.0 = perfect, <0.5 = inverted relationship)")

    # Cohen's d
    t_correct = tension[correct == 1]
    t_incorrect = tension[correct == 0]
    d_effect = cohens_d(t_correct, t_incorrect)
    print(f"\n### Cohen's d (effect size)")
    print(f"  Correct samples:   mean={t_correct.mean():.4f}, std={t_correct.std():.4f}, N={len(t_correct)}")
    print(f"  Incorrect samples: mean={t_incorrect.mean():.4f}, std={t_incorrect.std():.4f}, N={len(t_incorrect)}")
    print(f"  Cohen's d = {d_effect:+.4f}")
    if abs(d_effect) < 0.2:
        d_label = "negligible"
    elif abs(d_effect) < 0.5:
        d_label = "small"
    elif abs(d_effect) < 0.8:
        d_label = "medium"
    else:
        d_label = "large"
    print(f"  Effect size: {d_label}")

    # Distribution overlap
    if len(t_incorrect) > 0:
        overlap = overlap_coefficient(t_correct, t_incorrect)
        print(f"\n### Distribution Overlap")
        print(f"  Overlap coefficient = {overlap:.4f}")
        print(f"  (1.0 = identical distributions, 0.0 = no overlap)")

    # ASCII histograms
    print(f"\n### Tension Distribution: Correct vs Incorrect")
    if len(t_correct) > 0:
        print(ascii_histogram(t_correct, bins=15, width=35, label="CORRECT"))
    if len(t_incorrect) > 0:
        print()
        print(ascii_histogram(t_incorrect, bins=15, width=35, label="INCORRECT"))

    # ─────────────────────────────────────
    # Within-digit correlations
    # ─────────────────────────────────────
    print(f"\n### Within-Digit Correlations")
    print(f"  (Is tension correlated with correctness WITHIN each digit?)")
    print(f"  {'Digit':>5} {'N':>5} {'r_within':>10} {'MeanT_corr':>12} {'MeanT_incorr':>14} {'d':>8}")
    print(f"  {'-'*5:>5} {'-'*5:>5} {'-'*10:>10} {'-'*12:>12} {'-'*14:>14} {'-'*8:>8}")

    within_rs = []
    for d in range(10):
        mask = labels == d
        d_tension = tension[mask]
        d_correct = correct[mask]
        n_d = mask.sum()
        n_corr = int(d_correct.sum())
        n_incorr = n_d - n_corr

        if n_corr > 0 and n_incorr > 0:
            r_w = point_biserial(d_tension, d_correct)
            t_c = d_tension[d_correct == 1].mean()
            t_i = d_tension[d_correct == 0].mean()
            d_w = cohens_d(d_tension[d_correct == 1], d_tension[d_correct == 0])
            within_rs.append(r_w)
            print(f"  {d:>5} {n_d:>5} {r_w:>+10.4f} {t_c:>12.4f} {t_i:>14.4f} {d_w:>+8.4f}")
        else:
            print(f"  {d:>5} {n_d:>5} {'N/A':>10} {'N/A':>12} {'N/A':>14} {'N/A':>8}")

    if within_rs:
        mean_within = np.mean(within_rs)
        print(f"\n  Mean within-digit r = {mean_within:+.4f}")
        print(f"  Between-digit r     = {r_digit:+.4f}")
        print(f"  Overall per-sample r = {r_sample:+.4f}")

    # ─────────────────────────────────────
    # Ecological fallacy diagnosis
    # ─────────────────────────────────────
    print(f"\n{'=' * 70}")
    print(f"  ECOLOGICAL FALLACY DIAGNOSIS")
    print(f"{'=' * 70}")
    print(f"  Per-digit r (C4 original, N=10):     {r_digit:+.4f}")
    print(f"  Per-sample r (this test, N={n_total}):  {r_sample:+.4f}")
    print(f"  Bootstrap 95% CI:                     [{boot_lo:+.4f}, {boot_hi:+.4f}]")
    if within_rs:
        print(f"  Mean within-digit r:                  {mean_within:+.4f}")
    print(f"  AUC:                                  {auc:.4f}")
    print(f"  Cohen's d:                            {d_effect:+.4f} ({d_label})")

    # Verdict
    print(f"\n  VERDICT:")
    if abs(r_sample) < 0.05:
        print(f"  -> Per-sample correlation is NEGLIGIBLE (|r| < 0.05)")
        print(f"  -> C4 per-digit r={r_digit:+.4f} is likely ECOLOGICAL FALLACY")
        verdict = "ECOLOGICAL_FALLACY"
    elif abs(r_sample) < abs(r_digit) * 0.5:
        print(f"  -> Per-sample r is MUCH WEAKER than per-digit r")
        print(f"  -> C4 is WEAKENED (Simpson's paradox / ecological fallacy)")
        verdict = "WEAKENED"
    elif (r_sample > 0) == (r_digit > 0):
        print(f"  -> Direction preserved, magnitude reduced")
        print(f"  -> C4 is PARTIALLY SUPPORTED at individual level")
        verdict = "PARTIALLY_SUPPORTED"
    else:
        print(f"  -> Direction REVERSED at individual level!")
        print(f"  -> C4 is REVERSED (Simpson's paradox)")
        verdict = "REVERSED"

    if within_rs:
        if abs(mean_within) < 0.05 and abs(r_digit) > 0.2:
            print(f"  -> Within-digit r ~ 0 but between-digit r = {r_digit:+.4f}")
            print(f"  -> The correlation is ENTIRELY driven by between-digit differences")
            print(f"  -> (digits with higher avg tension also have higher avg accuracy)")
        elif abs(mean_within) > 0.05:
            print(f"  -> Within-digit r = {mean_within:+.4f} shows GENUINE per-sample effect")

    elapsed = time.time() - t0
    print(f"\n  Elapsed: {elapsed:.1f}s")
    print(f"{'=' * 70}")

    return verdict


if __name__ == "__main__":
    verdict = main()
```