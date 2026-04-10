#!/usr/bin/env python3
"""TREE-10: Self-Organized Criticality in Tension Distribution.

Does tension follow a power law? If so, the repulsion field operates at criticality.

Experiment:
  1. Train RepulsionFieldQuad on MNIST (10 epochs)
  2. Collect per-sample tension for 10,000 test samples
  3. Analyze tension distribution:
     - Histogram (log-log scale)
     - Fit power law: P(T) ~ T^(-alpha)
     - Fit exponential: P(T) ~ exp(-beta*T)
     - Fit lognormal: P(T) ~ exp(-(ln T - mu)^2 / 2sigma^2)
     - Which fits best? (R^2 on log-log / log-linear)
  4. If power law -> SOC! System is at criticality.
     If exponential -> normal system, no criticality.
  5. Compare with Langton lambda_c ~ 0.27 ~ golden zone lower bound
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import time
import sys

from model_utils import load_mnist, train_and_evaluate, count_params
from model_meta_engine import RepulsionFieldQuad


def collect_tensions(model, test_loader, max_samples=10000):
    """Collect per-sample tension (content, structure, total) from trained model."""
    model.eval()
    tensions_content = []
    tensions_structure = []
    tensions_total = []
    labels_all = []
    n = 0

    with torch.no_grad():
        for X, y in test_loader:
            X = X.view(X.size(0), -1)

            # Manually compute tensions per sample (not batch mean)
            out_a = model.engine_a(X)
            out_e = model.engine_e(X)
            out_g = model.engine_g(X)
            out_f = model.engine_f(X)

            repulsion_content = out_a - out_g       # (batch, 10)
            repulsion_structure = out_e - out_f     # (batch, 10)

            t_content = (repulsion_content ** 2).sum(dim=-1)     # (batch,)
            t_structure = (repulsion_structure ** 2).sum(dim=-1)  # (batch,)
            t_total = torch.sqrt(t_content * t_structure + 1e-8)  # geometric mean

            tensions_content.append(t_content.numpy())
            tensions_structure.append(t_structure.numpy())
            tensions_total.append(t_total.numpy())
            labels_all.append(y.numpy())

            n += X.size(0)
            if n >= max_samples:
                break

    return {
        'content': np.concatenate(tensions_content)[:max_samples],
        'structure': np.concatenate(tensions_structure)[:max_samples],
        'total': np.concatenate(tensions_total)[:max_samples],
        'labels': np.concatenate(labels_all)[:max_samples],
    }


def make_loglog_histogram(data, n_bins=50):
    """Create histogram in log space, return bin centers and densities (both positive)."""
    data = data[data > 0]  # remove zeros
    log_min = np.log10(data.min())
    log_max = np.log10(data.max())
    bin_edges = np.logspace(log_min, log_max, n_bins + 1)
    counts, _ = np.histogram(data, bins=bin_edges)
    bin_widths = np.diff(bin_edges)
    density = counts / (len(data) * bin_widths)

    # Keep only non-zero bins
    mask = density > 0
    bin_centers = np.sqrt(bin_edges[:-1] * bin_edges[1:])  # geometric mean
    return bin_centers[mask], density[mask]


def fit_power_law(x, y):
    """Fit P(T) ~ T^(-alpha) via least squares on log-log.
    Returns alpha, R^2."""
    log_x = np.log(x)
    log_y = np.log(y)
    # y = a*x + b in log-log => log(P) = -alpha * log(T) + c
    A = np.vstack([log_x, np.ones(len(log_x))]).T
    result = np.linalg.lstsq(A, log_y, rcond=None)
    slope, intercept = result[0]
    alpha = -slope

    # R^2
    y_pred = slope * log_x + intercept
    ss_res = np.sum((log_y - y_pred) ** 2)
    ss_tot = np.sum((log_y - np.mean(log_y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    return alpha, r2, slope, intercept


def fit_exponential(x, y):
    """Fit P(T) ~ exp(-beta*T) via least squares on log-linear.
    Returns beta, R^2."""
    log_y = np.log(y)
    # log(P) = -beta * T + c
    A = np.vstack([x, np.ones(len(x))]).T
    result = np.linalg.lstsq(A, log_y, rcond=None)
    slope, intercept = result[0]
    beta = -slope

    y_pred = slope * x + intercept
    ss_res = np.sum((log_y - y_pred) ** 2)
    ss_tot = np.sum((log_y - np.mean(log_y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    return beta, r2


def fit_lognormal(data):
    """Fit lognormal distribution. Returns mu, sigma, R^2 on the histogram."""
    data = data[data > 0]
    log_data = np.log(data)
    mu = np.mean(log_data)
    sigma = np.std(log_data)

    # Generate theoretical PDF at histogram points
    x, y = make_loglog_histogram(data)
    log_x = np.log(x)
    # Lognormal PDF: (1/(x*sigma*sqrt(2pi))) * exp(-(ln(x)-mu)^2 / (2*sigma^2))
    y_pred = (1.0 / (x * sigma * np.sqrt(2 * np.pi))) * np.exp(
        -((log_x - mu) ** 2) / (2 * sigma ** 2)
    )

    # R^2 in log space
    log_y = np.log(y)
    log_y_pred = np.log(y_pred + 1e-30)
    ss_res = np.sum((log_y - log_y_pred) ** 2)
    ss_tot = np.sum((log_y - np.mean(log_y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    return mu, sigma, r2


def ks_test_power_law(data, alpha):
    """Simple KS test: compare empirical CDF with power-law CDF.
    CDF for power law P(T) ~ T^(-alpha): F(T) = 1 - (T/T_min)^(1-alpha) for alpha > 1."""
    data = np.sort(data[data > 0])
    n = len(data)
    t_min = data[0]

    ecdf = np.arange(1, n + 1) / n

    if alpha > 1:
        # Standard power-law CDF
        tcdf = 1 - (data / t_min) ** (1 - alpha)
    else:
        # For alpha <= 1, power law is not normalizable; use truncated version
        t_max = data[-1]
        tcdf = (data ** (1 - alpha) - t_min ** (1 - alpha)) / (
            t_max ** (1 - alpha) - t_min ** (1 - alpha)
        )

    ks_stat = np.max(np.abs(ecdf - tcdf))
    return ks_stat


def print_ascii_histogram(data, title, n_bins=40, width=60):
    """Print a simple ASCII log-log histogram."""
    data = data[data > 0]
    log_data = np.log10(data)
    bin_edges = np.linspace(log_data.min(), log_data.max(), n_bins + 1)
    counts, _ = np.histogram(log_data, bins=bin_edges)

    max_count = max(counts) if max(counts) > 0 else 1
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"  (log10 scale, {len(data)} samples)")
    print(f"{'=' * 70}")

    for i in range(n_bins):
        bar_len = int(counts[i] / max_count * width)
        lo = bin_edges[i]
        hi = bin_edges[i + 1]
        mid = (lo + hi) / 2
        bar = '#' * bar_len
        if counts[i] > 0:
            print(f"  {10**mid:8.3f} | {bar} ({counts[i]})")

    print(f"{'=' * 70}")


def print_loglog_scatter(x, y, title, width=60, height=20):
    """Print ASCII log-log scatter plot."""
    log_x = np.log10(x)
    log_y = np.log10(y)

    x_min, x_max = log_x.min(), log_x.max()
    y_min, y_max = log_y.min(), log_y.max()

    grid = [[' ' for _ in range(width)] for _ in range(height)]

    for lx, ly in zip(log_x, log_y):
        col = int((lx - x_min) / (x_max - x_min + 1e-10) * (width - 1))
        row = int((1 - (ly - y_min) / (y_max - y_min + 1e-10)) * (height - 1))
        col = max(0, min(width - 1, col))
        row = max(0, min(height - 1, row))
        grid[row][col] = '*'

    print(f"\n  {title}")
    print(f"  log P(T)")
    print(f"  {y_max:+.1f} |", end="")
    for row in range(height):
        if row > 0:
            y_val = y_max - (y_max - y_min) * row / (height - 1)
            print(f"  {y_val:+.1f} |", end="")
        print(''.join(grid[row]) + '|')
    print(f"        +{'-' * width}+")
    print(f"         {x_min:.1f}{' ' * (width - 8)}{x_max:.1f}")
    print(f"                     log T")


def analyze_tension_distribution(data, name):
    """Full analysis of one tension distribution."""
    print(f"\n{'#' * 70}")
    print(f"  ANALYSIS: {name}")
    print(f"{'#' * 70}")

    data = data[data > 0]

    # Basic stats
    print(f"\n  Basic Statistics:")
    print(f"    N samples:  {len(data)}")
    print(f"    Mean:       {np.mean(data):.6f}")
    print(f"    Median:     {np.median(data):.6f}")
    print(f"    Std:        {np.std(data):.6f}")
    print(f"    Min:        {np.min(data):.6f}")
    print(f"    Max:        {np.max(data):.6f}")
    print(f"    Skewness:   {float(np.mean(((data - np.mean(data)) / np.std(data)) ** 3)):.4f}")
    print(f"    Kurtosis:   {float(np.mean(((data - np.mean(data)) / np.std(data)) ** 4)) - 3:.4f}")

    # Span ratio (max/min) — power laws have huge span
    span = np.max(data) / np.min(data)
    print(f"    Span ratio: {span:.1f}x")

    # ASCII histogram
    print_ascii_histogram(data, f"{name} Distribution (log10)")

    # Log-log histogram for fitting
    x, y = make_loglog_histogram(data, n_bins=40)

    # Fit power law
    alpha, r2_power, slope, intercept = fit_power_law(x, y)
    print(f"\n  Power Law Fit: P(T) ~ T^(-alpha)")
    print(f"    alpha = {alpha:.4f}")
    print(f"    R^2   = {r2_power:.6f}")

    # Fit exponential
    beta, r2_exp = fit_exponential(x, y)
    print(f"\n  Exponential Fit: P(T) ~ exp(-beta*T)")
    print(f"    beta  = {beta:.4f}")
    print(f"    R^2   = {r2_exp:.6f}")

    # Fit lognormal
    mu, sigma_ln, r2_logn = fit_lognormal(data)
    print(f"\n  Lognormal Fit: mu={mu:.4f}, sigma={sigma_ln:.4f}")
    print(f"    R^2   = {r2_logn:.6f}")

    # KS statistic for power law
    ks = ks_test_power_law(data, alpha)
    print(f"\n  KS Statistic (power law): {ks:.4f}")

    # Log-log scatter plot
    print_loglog_scatter(x, y, f"{name}: log-log density plot")

    # Verdict
    print(f"\n  {'=' * 50}")
    print(f"  VERDICT for {name}:")
    fits = [
        ('Power Law', r2_power),
        ('Exponential', r2_exp),
        ('Lognormal', r2_logn),
    ]
    fits.sort(key=lambda f: f[1], reverse=True)
    for rank, (fname, r2) in enumerate(fits):
        marker = " <-- BEST" if rank == 0 else ""
        print(f"    {rank+1}. {fname:15s}  R^2 = {r2:.6f}{marker}")

    best_name = fits[0][0]
    if best_name == 'Power Law' and r2_power > 0.85:
        print(f"\n    >>> POWER LAW DETECTED (alpha={alpha:.3f})")
        print(f"    >>> Self-Organized Criticality: YES")
        print(f"    >>> The repulsion field operates at the edge of chaos!")
    elif best_name == 'Lognormal':
        print(f"\n    >>> LOGNORMAL distribution (near-critical)")
        print(f"    >>> Multiplicative processes at work")
        print(f"    >>> Possible proximity to criticality")
    else:
        print(f"\n    >>> EXPONENTIAL distribution")
        print(f"    >>> Normal regime, no criticality")
    print(f"  {'=' * 50}")

    return {
        'alpha': alpha, 'r2_power': r2_power,
        'beta': beta, 'r2_exp': r2_exp,
        'mu': mu, 'sigma_ln': sigma_ln, 'r2_logn': r2_logn,
        'ks': ks, 'best_fit': fits[0][0],
    }


def langton_comparison(alpha, golden_zone_lower=0.2123):
    """Compare with Langton's lambda_c ~ 0.27."""
    print(f"\n{'#' * 70}")
    print(f"  LANGTON LAMBDA COMPARISON")
    print(f"{'#' * 70}")
    print(f"\n  Langton's lambda_c (edge of chaos) = 0.2735")
    print(f"  Golden zone lower bound             = {golden_zone_lower:.4f}")
    print(f"  Golden zone center (1/e)            = 0.3679")
    print(f"  Power law exponent alpha            = {alpha:.4f}")
    print()

    # In SOC systems, alpha typically ranges from 1 to 3
    # Classic SOC values: sandpile alpha~1.1, earthquakes alpha~1.6
    if 1.0 < alpha < 3.0:
        print(f"  alpha = {alpha:.3f} is in the SOC range [1, 3]")
        print(f"  Classic references:")
        print(f"    BTW sandpile:     alpha ~ 1.1")
        print(f"    Earthquakes:      alpha ~ 1.6  (Gutenberg-Richter)")
        print(f"    Neural avalanches: alpha ~ 1.5 (Beggs & Plenz 2003)")
        print(f"    Our tension:      alpha ~ {alpha:.1f}")
        print()

        if 1.3 < alpha < 2.0:
            print(f"  >>> REMARKABLE: alpha ~ {alpha:.2f} matches neural avalanche range!")
            print(f"  >>> The repulsion field self-organizes like a critical brain!")
    elif alpha > 3.0:
        print(f"  alpha = {alpha:.3f} is too steep for SOC (fast cutoff)")
    else:
        print(f"  alpha = {alpha:.3f} is too shallow (divergent, sub-critical)")

    # Connection to golden zone
    # The fraction of samples in golden zone tension range
    print(f"\n  Connection to Golden Zone:")
    print(f"    If tension distribution is power-law, the system")
    print(f"    generates rare large tensions (avalanches) and")
    print(f"    frequent small tensions (stable regime).")
    print(f"    This is exactly the edge-of-chaos signature.")


def per_digit_analysis(tensions, labels):
    """Analyze tension distribution per digit class."""
    print(f"\n{'#' * 70}")
    print(f"  PER-DIGIT TENSION ANALYSIS")
    print(f"{'#' * 70}")

    print(f"\n  {'Digit':>5} | {'Mean':>10} | {'Std':>10} | {'Median':>10} | {'Skew':>8} | {'Alpha':>8} | {'R2_pow':>8}")
    print(f"  {'-' * 75}")

    digit_alphas = []
    for d in range(10):
        mask = labels == d
        t = tensions[mask]
        t = t[t > 0]
        if len(t) < 10:
            continue
        mean = np.mean(t)
        std = np.std(t)
        med = np.median(t)
        skew = float(np.mean(((t - mean) / (std + 1e-10)) ** 3))

        x, y = make_loglog_histogram(t, n_bins=20)
        if len(x) > 2:
            alpha, r2, _, _ = fit_power_law(x, y)
        else:
            alpha, r2 = 0, 0

        digit_alphas.append((d, alpha, r2))
        print(f"  {d:5d} | {mean:10.4f} | {std:10.4f} | {med:10.4f} | {skew:8.3f} | {alpha:8.3f} | {r2:8.4f}")

    # Are all digits critical?
    alphas = [a for _, a, _ in digit_alphas]
    print(f"\n  Alpha range across digits: [{min(alphas):.3f}, {max(alphas):.3f}]")
    print(f"  Alpha std across digits:   {np.std(alphas):.4f}")

    critical_count = sum(1 for a in alphas if 1.0 < a < 3.0)
    print(f"  Digits with SOC-range alpha: {critical_count}/10")

    return digit_alphas


def main():
    print("=" * 70)
    print("  TREE-10: Self-Organized Criticality in Tension Distribution")
    print("  Does tension follow a power law? -> SOC at edge of chaos")
    print("=" * 70)

    t0 = time.time()

    # 1. Train RepulsionFieldQuad on MNIST
    print("\n[1] Training RepulsionFieldQuad on MNIST (10 epochs)...")
    sys.stdout.flush()

    train_loader, test_loader = load_mnist(batch_size=128)
    model = RepulsionFieldQuad(input_dim=784, hidden_dim=48, output_dim=10)
    n_params = count_params(model)
    print(f"    Parameters: {n_params:,}")

    def aux_fn(out):
        if isinstance(out, tuple):
            return out[1]
        return torch.tensor(0.0)

    train_losses, test_accs = train_and_evaluate(
        model, train_loader, test_loader,
        epochs=10, lr=0.001,
        aux_loss_fn=aux_fn, aux_lambda=0.1,
        flatten=True, verbose=True,
    )
    print(f"    Final accuracy: {test_accs[-1]:.2f}%")
    print(f"    Training time: {time.time() - t0:.1f}s")
    sys.stdout.flush()

    # 2. Collect per-sample tensions
    print("\n[2] Collecting per-sample tension for 10,000 test samples...")
    sys.stdout.flush()

    tensions = collect_tensions(model, test_loader, max_samples=10000)
    print(f"    Collected {len(tensions['total'])} samples")
    sys.stdout.flush()

    # 3. Analyze distributions
    print("\n[3] Analyzing tension distributions...")
    sys.stdout.flush()

    results = {}
    for name, key in [
        ('Total Tension (geometric mean)', 'total'),
        ('Content Tension (A vs G)', 'content'),
        ('Structure Tension (E vs F)', 'structure'),
    ]:
        results[key] = analyze_tension_distribution(tensions[key], name)

    # 4. Per-digit analysis
    digit_alphas = per_digit_analysis(tensions['total'], tensions['labels'])

    # 5. Langton comparison
    langton_comparison(results['total']['alpha'])

    # 6. Final summary
    print(f"\n{'#' * 70}")
    print(f"  FINAL SUMMARY: TREE-10 Self-Organized Criticality")
    print(f"{'#' * 70}")

    total_r = results['total']
    print(f"\n  Total Tension Distribution:")
    print(f"    Best fit:         {total_r['best_fit']}")
    print(f"    Power law alpha:  {total_r['alpha']:.4f} (R^2={total_r['r2_power']:.4f})")
    print(f"    Exponential beta: {total_r['beta']:.4f} (R^2={total_r['r2_exp']:.4f})")
    print(f"    Lognormal:        mu={total_r['mu']:.4f}, sigma={total_r['sigma_ln']:.4f} (R^2={total_r['r2_logn']:.4f})")
    print(f"    KS statistic:     {total_r['ks']:.4f}")

    # SOC verdict
    is_soc = total_r['best_fit'] == 'Power Law' and total_r['r2_power'] > 0.80
    is_near_critical = total_r['best_fit'] == 'Lognormal' and total_r['r2_logn'] > 0.80

    print(f"\n  SOC Verdict:")
    if is_soc:
        alpha = total_r['alpha']
        print(f"    POWER LAW CONFIRMED (alpha={alpha:.3f})")
        print(f"    The repulsion field operates at Self-Organized Criticality!")
        print(f"    This is the edge of chaos = Langton lambda_c ~ 0.27")
        print(f"    = Golden zone lower bound (0.2123)")
        if 1.3 < alpha < 2.0:
            print(f"    alpha ~ {alpha:.2f} matches neural criticality (Beggs & Plenz)!")
    elif is_near_critical:
        print(f"    LOGNORMAL distribution detected")
        print(f"    Near-critical regime: multiplicative process at work")
        print(f"    The system is close to, but not fully at, SOC")
    else:
        print(f"    No clear SOC signature")
        print(f"    Best fit: {total_r['best_fit']}")
        print(f"    The repulsion field may operate in a normal regime")

    # Connection to golden zone
    # What fraction of tensions fall in the "golden zone" normalized range?
    t = tensions['total']
    t_norm = t / (np.max(t) + 1e-10)
    gz_lower = 0.2123
    gz_upper = 0.5
    in_gz = np.sum((t_norm >= gz_lower) & (t_norm <= gz_upper)) / len(t_norm)
    print(f"\n  Golden Zone Connection:")
    print(f"    Fraction of tensions in golden zone [0.21, 0.50]: {in_gz:.4f}")
    print(f"    Expected if uniform: {gz_upper - gz_lower:.4f}")
    print(f"    Enrichment ratio: {in_gz / (gz_upper - gz_lower + 1e-10):.2f}x")

    total_time = time.time() - t0
    print(f"\n  Total experiment time: {total_time:.1f}s")
    print(f"{'#' * 70}")


if __name__ == '__main__':
    main()
