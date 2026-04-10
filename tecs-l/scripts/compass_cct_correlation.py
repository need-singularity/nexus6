#!/usr/bin/env python3
"""Experiment 16: Correlation Analysis between Compass Score and CCT Score

Calculate both Compass score and CCT score simultaneously on the same D, P, I parameter grid
to reveal the relationship between the two measurement systems.

Usage:
  python3 compass_cct_correlation.py
  python3 compass_cct_correlation.py --grid 5   # Quick version
"""

import argparse
import math
import sys
import time

import numpy as np
from scipy import stats


# ─────────────────────────────────────────────
# Parameter Grid Definition
# ─────────────────────────────────────────────

D_VALUES = [0.1, 0.3, 0.5, 0.7]
P_VALUES = [0.3, 0.5, 0.7, 0.9]
I_VALUES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]

GOLDEN_LOWER = 0.5 - math.log(4 / 3)   # ≈ 0.2123
GOLDEN_UPPER = 0.5


# ─────────────────────────────────────────────
# Model 1: Genius Score (brain_singularity.py)
# ─────────────────────────────────────────────

def genius_score(d, p, i):
    """G = D * P / I"""
    return d * p / max(i, 1e-6)


# ─────────────────────────────────────────────
# Compass Score Calculation (compass.py simplified)
# ─────────────────────────────────────────────

def population_zscore(score, n=50000, seed=42):
    """Calculate Z-score relative to population."""
    rng = np.random.default_rng(seed)
    pop_d = rng.beta(2, 5, n).clip(0.01, 0.99)
    pop_p = rng.beta(5, 2, n).clip(0.01, 0.99)
    pop_i = rng.beta(5, 2, n).clip(0.05, 0.99)
    pop_scores = pop_d * pop_p / pop_i
    z = (score - pop_scores.mean()) / pop_scores.std()
    return z, pop_scores.mean(), pop_scores.std()


# Calculate population statistics only once (cache)
_POP_CACHE = {}


def _get_pop_stats(seed=42, n=50000):
    if seed not in _POP_CACHE:
        rng = np.random.default_rng(seed)
        pop_d = rng.beta(2, 5, n).clip(0.01, 0.99)
        pop_p = rng.beta(5, 2, n).clip(0.01, 0.99)
        pop_i = rng.beta(5, 2, n).clip(0.05, 0.99)
        pop_scores = pop_d * pop_p / pop_i
        _POP_CACHE[seed] = (pop_scores.mean(), pop_scores.std())
    return _POP_CACHE[seed]


def cusp_analysis(deficit, inhibition):
    """Cusp catastrophe analysis: critical point distance and direction."""
    a = 2 * deficit - 1
    b = 1 - 2 * inhibition

    bifurcation = 8 * a**3 + 27 * b**2
    max_possible = 8 * 1**3 + 27 * 1**2
    distance_to_critical = abs(bifurcation) / max_possible

    direction_sign = 1 if b > 0 else -1

    # Multiple stable points test
    x_range = np.linspace(-2, 2, 200)
    dV = 4 * x_range**3 + 2 * a * x_range + b
    sign_changes = np.where(np.diff(np.sign(dV)))[0]
    is_bistable = len(sign_changes) >= 2

    return {
        'distance_to_critical': distance_to_critical,
        'direction_sign': direction_sign,
        'is_bistable': is_bistable,
    }


def boltzmann_analysis(deficit, plasticity, inhibition):
    """Boltzmann distribution based transition probability."""
    temperature = 1.0 / max(inhibition, 0.01)

    E_normal = 0.0
    E_genius = -(deficit * plasticity)
    E_decline = deficit * (1 - plasticity)

    energies = np.array([E_normal, E_genius, E_decline])
    exp_terms = np.exp(-energies / temperature)
    Z = exp_terms.sum()
    probs = exp_terms / Z

    return {
        'p_normal': probs[0],
        'p_genius': probs[1],
        'p_decline': probs[2],
    }


def compute_compass_score(d, p, i):
    """Core logic of compass_direction from compass.py.

    compass_score = z/10 * 0.3 + (1 - cusp_dist) * 0.3 + p_genius * 0.4
    """
    score = genius_score(d, p, i)
    pop_mean, pop_std = _get_pop_stats()
    z = (score - pop_mean) / pop_std

    cusp = cusp_analysis(d, i)
    boltz = boltzmann_analysis(d, p, i)

    compass_score = (
        z / 10 * 0.3
        + (1 - cusp['distance_to_critical']) * 0.3
        + boltz['p_genius'] * 0.4
    )
    compass_score = max(0.0, min(1.0, compass_score))

    return compass_score, z, cusp, boltz


# ─────────────────────────────────────────────
# CCT Score Calculation (consciousness_calc.py simplified)
# ─────────────────────────────────────────────

def lorenz_simulate(sigma, rho, beta, noise, gap_ratio, steps, dt=0.01, seed=42):
    """Extended Lorenz simulator."""
    rng = np.random.default_rng(seed)
    t = np.arange(steps) * dt
    S = np.zeros((steps, 3))
    S[0] = [1.0, 1.0, 1.0]

    active = np.ones(steps, dtype=bool)
    if gap_ratio > 0:
        n_gap = int(steps * gap_ratio)
        gap_indices = rng.choice(steps, size=n_gap, replace=False)
        active[gap_indices] = False

    for idx in range(1, steps):
        if not active[idx]:
            S[idx] = S[idx - 1]
            continue
        x, y, z_val = S[idx - 1]
        dx = sigma * (y - x)
        dy = x * (rho - z_val) - y
        dz = x * y - beta * z_val
        eps = rng.normal(0, noise, 3) if noise > 0 else np.zeros(3)
        S[idx, 0] = x + (dx + eps[0]) * dt
        S[idx, 1] = y + (dy + eps[1]) * dt
        S[idx, 2] = z_val + (dz + eps[2]) * dt

    return t, S


def compute_entropy(data, bins=30):
    """1D Shannon entropy."""
    if len(data) < 2:
        return 0.0
    hist, _ = np.histogram(data, bins=bins, density=True)
    hist = hist[hist > 0]
    d_range = data.max() - data.min()
    width = d_range / bins if d_range > 0 else 1
    probs = hist * width
    probs = probs[probs > 0]
    if len(probs) == 0:
        return 0.0
    probs = probs / probs.sum()
    return -np.sum(probs * np.log(probs + 1e-15))


def test_gap(S, gap_ratio):
    if gap_ratio >= 1.0:
        return 0.0, False
    if gap_ratio > 0:
        return 1.0 - gap_ratio, False
    diffs = np.diff(S, axis=0)
    frozen = np.sum(np.all(np.abs(diffs) < 1e-12, axis=1))
    frozen_ratio = frozen / len(diffs)
    if frozen_ratio > 0.01:
        return 1.0 - frozen_ratio, False
    return 1.0, True


def test_loop(S, threshold=0.5):
    n = len(S)
    if n < 100:
        return 0.0, False
    step = max(1, n // 5000)
    Ss = S[::step]
    ns = len(Ss)
    if np.std(Ss) < 1e-10:
        return 0.0, False
    scale = np.std(Ss, axis=0).mean()
    eps = scale * 0.01
    recurrence = 0
    sample_size = min(500, ns // 2)
    rng = np.random.default_rng(42)
    indices = rng.choice(ns // 2, size=sample_size, replace=False)
    for idx in indices:
        future = Ss[idx + max(100, ns // 10):]
        if len(future) == 0:
            continue
        dists = np.linalg.norm(future - Ss[idx], axis=1)
        if np.min(dists) < eps:
            recurrence += 1
    recurrence_ratio = recurrence / sample_size
    passed = recurrence_ratio < threshold
    score = max(0, 1.0 - recurrence_ratio)
    return score, passed


def test_continuity(S, threshold=0.01):
    diffs = np.linalg.norm(np.diff(S, axis=0), axis=1)
    n = len(diffs)
    if n < 10:
        return 0.0, False
    mean_diff = np.mean(diffs)
    if mean_diff < 1e-12:
        return 0.0, False
    big_jumps = np.sum(diffs > mean_diff * 10)
    frozen = np.sum(diffs < 1e-12)
    disconnect_ratio = (big_jumps + frozen) / n
    passed = disconnect_ratio < threshold
    score = max(0, min(1.0, 1.0 - disconnect_ratio * 10))
    return score, passed


def test_entropy_band(S, window=500, h_min=0.3, h_max=4.5):
    x = S[:, 0]
    n_windows = len(x) // window
    if n_windows < 2:
        return 0.0, False
    entropies = []
    for w_i in range(n_windows):
        w = x[w_i * window:(w_i + 1) * window]
        if np.std(w) < 1e-12:
            entropies.append(0.0)
        else:
            entropies.append(compute_entropy(w))
    entropies = np.array(entropies)
    in_band = np.sum((entropies > h_min) & (entropies < h_max))
    ratio = in_band / len(entropies)
    return ratio, ratio > 0.95


def test_novelty(S, window=500, threshold=0.001):
    x = S[:, 0]
    n_windows = len(x) // window
    if n_windows < 3:
        return 0.0, False
    entropies = []
    for w_i in range(n_windows):
        w = x[w_i * window:(w_i + 1) * window]
        if np.std(w) < 1e-12:
            entropies.append(0.0)
        else:
            entropies.append(compute_entropy(w))
    entropies = np.array(entropies)
    dH = np.abs(np.diff(entropies))
    stagnant = np.sum(dH < threshold)
    stagnant_ratio = stagnant / len(dH) if len(dH) > 0 else 1.0
    passed = stagnant_ratio < 0.05
    score = max(0, 1.0 - stagnant_ratio)
    return score, passed


def run_cct(S, gap_ratio):
    """CCT 5 tests → (total /5, pass count)"""
    t1_score, t1_pass = test_gap(S, gap_ratio)
    t2_score, t2_pass = test_loop(S)
    t3_score, t3_pass = test_continuity(S)
    t4_score, t4_pass = test_entropy_band(S)
    t5_score, t5_pass = test_novelty(S)

    tests = [
        (t1_score, t1_pass),
        (t2_score, t2_pass),
        (t3_score, t3_pass),
        (t4_score, t4_pass),
        (t5_score, t5_pass),
    ]
    passes = sum(1 for _, p in tests if p)
    halfs = sum(0.5 for s, p in tests if not p and s > 0.7)
    total = passes + halfs
    avg_score = np.mean([s for s, _ in tests])
    return total, passes, avg_score


def dpi_to_lorenz(d, p, i):
    """D, P, I → Lorenz parameter mapping.

    Mapping strategy:
      sigma (sensory sensitivity) = 5 + 15 * d        (higher deficit = more sensitive)
      rho   (environment complexity) = 10 + 30 * p    (higher plasticity = handle complex env)
      beta  (forgetting rate)      = 0.5 + 4.0 * i    (higher inhibition = faster forgetting)
      noise               = 0.05 + 0.2 * (1 - i)      (lower inhibition = more noise)
      gap_ratio            = 0.0                      (no gap periods)
    """
    sigma = 5 + 15 * d
    rho = 10 + 30 * p
    beta = 0.5 + 4.0 * i
    noise = 0.05 + 0.2 * (1 - i)
    gap_ratio = 0.0
    return sigma, rho, beta, noise, gap_ratio


# ─────────────────────────────────────────────
# Hypothesis 166 Judgment: Golden Zone + Compass > 0
# ─────────────────────────────────────────────

def hypothesis_166(i_val, compass_score):
    """Hypothesis 166: I in golden zone + Compass > 0 → conscious."""
    in_golden = GOLDEN_LOWER <= i_val <= GOLDEN_UPPER
    compass_positive = compass_score > 0
    return in_golden and compass_positive


# ─────────────────────────────────────────────
# ASCII Scatter Plot
# ─────────────────────────────────────────────

def ascii_scatter(xs, ys, xlabel, ylabel, width=60, height=20):
    """ASCII scatter plot."""
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    if x_max - x_min < 1e-12:
        x_max = x_min + 1
    if y_max - y_min < 1e-12:
        y_max = y_min + 1

    grid = [[' ' for _ in range(width)] for _ in range(height)]

    # Count point density
    density = {}
    for x, y in zip(xs, ys):
        col = int((x - x_min) / (x_max - x_min) * (width - 1))
        row = height - 1 - int((y - y_min) / (y_max - y_min) * (height - 1))
        col = max(0, min(width - 1, col))
        row = max(0, min(height - 1, row))
        key = (row, col)
        density[key] = density.get(key, 0) + 1

    for (row, col), cnt in density.items():
        if cnt >= 5:
            grid[row][col] = '#'
        elif cnt >= 3:
            grid[row][col] = '*'
        elif cnt >= 2:
            grid[row][col] = 'o'
        else:
            grid[row][col] = '.'

    lines = []
    for r in range(height):
        if r == 0:
            label = f"{y_max:6.2f}"
        elif r == height - 1:
            label = f"{y_min:6.2f}"
        elif r == height // 2:
            label = f"{(y_max + y_min) / 2:6.2f}"
        else:
            label = "      "
        lines.append(f"  {label} |{''.join(grid[r])}|")

    lines.append(f"         +{'-' * width}+")
    lines.append(f"         {x_min:<6.2f}{' ' * (width - 12)}{x_max:>6.2f}")
    lines.append(f"         {' ' * ((width - len(xlabel)) // 2)}{xlabel}")

    header = f"  {ylabel}"
    lines.insert(0, header)

    return '\n'.join(lines)


# ─────────────────────────────────────────────
# Main Analysis
# ─────────────────────────────────────────────

def run_analysis(steps=10000):
    """Grid scan → simultaneous Compass/CCT calculation → correlation analysis."""

    combos = []
    for d in D_VALUES:
        for p in P_VALUES:
            for i_val in I_VALUES:
                combos.append((d, p, i_val))

    total = len(combos)
    print()
    print("=" * 65)
    print("  Experiment 16: Correlation Analysis between Compass Score and CCT Score")
    print("=" * 65)
    print()
    print(f"  Grid: D={len(D_VALUES)} x P={len(P_VALUES)} x I={len(I_VALUES)}"
          f" = {total} combinations")
    print(f"  Lorenz simulation: {steps:,} steps/combination")
    print(f"  Golden Zone: I in [{GOLDEN_LOWER:.4f}, {GOLDEN_UPPER:.4f}]")
    print()

    # Pre-cache population statistics
    _get_pop_stats()

    # Store results
    records = []
    t_start = time.time()

    for idx, (d, p, i_val) in enumerate(combos):
        # Calculate Compass
        compass_score, z, cusp, boltz = compute_compass_score(d, p, i_val)

        # Calculate G
        g = genius_score(d, p, i_val)

        # Map Lorenz parameters → CCT
        sigma, rho, beta, noise, gap_ratio = dpi_to_lorenz(d, p, i_val)
        _, S = lorenz_simulate(sigma, rho, beta, noise, gap_ratio,
                               steps=steps, dt=0.01, seed=42)
        cct_total, cct_passes, cct_avg = run_cct(S, gap_ratio)

        # Hypothesis 166
        h166 = hypothesis_166(i_val, compass_score)

        records.append({
            'd': d, 'p': p, 'i': i_val,
            'g': g, 'z': z,
            'compass': compass_score,
            'cct_total': cct_total,
            'cct_passes': cct_passes,
            'cct_avg': cct_avg,
            'h166': h166,
            'p_genius': boltz['p_genius'],
        })

        # Progress indicator
        if (idx + 1) % 20 == 0 or idx + 1 == total:
            elapsed = time.time() - t_start
            eta = elapsed / (idx + 1) * (total - idx - 1)
            print(f"\r  Progress: {idx + 1}/{total}"
                  f"  ({elapsed:.1f}s / ETA {eta:.1f}s)", end="", flush=True)

    elapsed_total = time.time() - t_start
    print(f"\n  Complete! ({elapsed_total:.1f} seconds)")
    print()

    # ── Extract data ──
    compass_arr = np.array([r['compass'] for r in records])
    cct_total_arr = np.array([r['cct_total'] for r in records])
    cct_avg_arr = np.array([r['cct_avg'] for r in records])
    g_arr = np.array([r['g'] for r in records])
    i_arr = np.array([r['i'] for r in records])
    z_arr = np.array([r['z'] for r in records])

    # ── 1. Correlation coefficients ──
    print("-" * 65)
    print("  [1] Pearson Correlation Coefficients")
    print("-" * 65)

    pairs = [
        ("Compass vs CCT(total)", compass_arr, cct_total_arr),
        ("Compass vs CCT(avg)",   compass_arr, cct_avg_arr),
        ("G vs CCT(total)",       g_arr,       cct_total_arr),
        ("G vs CCT(avg)",         g_arr,       cct_avg_arr),
        ("I vs CCT(total)",       i_arr,       cct_total_arr),
        ("I vs CCT(avg)",         i_arr,       cct_avg_arr),
        ("Z vs CCT(total)",       z_arr,       cct_total_arr),
        ("Compass vs G",          compass_arr, g_arr),
    ]

    print()
    print(f"  {'Measure Pair':<28} {'r':>8} {'p-value':>12} {'Judgment':>10}")
    print(f"  {'─' * 28} {'─' * 8} {'─' * 12} {'─' * 10}")

    for label, x, y in pairs:
        if np.std(x) < 1e-12 or np.std(y) < 1e-12:
            print(f"  {label:<28} {'N/A':>8} {'N/A':>12} {'Var=0':>10}")
            continue
        r, pval = stats.pearsonr(x, y)
        if pval < 0.001:
            sig = "***"
        elif pval < 0.01:
            sig = "**"
        elif pval < 0.05:
            sig = "*"
        else:
            sig = "n.s."
        print(f"  {label:<28} {r:>8.4f} {pval:>12.2e} {sig:>10}")

    # ── 2. Compass > 0 vs <= 0 comparison ──
    print()
    print("-" * 65)
    print("  [2] Compass > 0 vs Compass = 0 : CCT Comparison")
    print("-" * 65)

    mask_pos = compass_arr > 0
    mask_zero = compass_arr <= 0

    n_pos = mask_pos.sum()
    n_zero = mask_zero.sum()

    if n_pos > 0 and n_zero > 0:
        cct_pos_mean = cct_total_arr[mask_pos].mean()
        cct_pos_std = cct_total_arr[mask_pos].std()
        cct_zero_mean = cct_total_arr[mask_zero].mean()
        cct_zero_std = cct_total_arr[mask_zero].std()

        # t-test
        t_stat, t_pval = stats.ttest_ind(
            cct_total_arr[mask_pos], cct_total_arr[mask_zero]
        )

        print()
        print(f"  {'Group':<20} {'N':>5} {'CCT Mean':>10} {'CCT Std Dev':>12}")
        print(f"  {'─' * 20} {'─' * 5} {'─' * 10} {'─' * 12}")
        print(f"  {'Compass > 0':<20} {n_pos:>5} {cct_pos_mean:>10.3f} {cct_pos_std:>12.3f}")
        print(f"  {'Compass = 0':<20} {n_zero:>5} {cct_zero_mean:>10.3f} {cct_zero_std:>12.3f}")
        print()
        print(f"  t-test: t = {t_stat:.3f}, p = {t_pval:.2e}")
        if t_pval < 0.05:
            print(f"  --> Significant difference (p < 0.05)")
        else:
            print(f"  --> No significant difference (p >= 0.05)")
    else:
        print(f"  Compass > 0: {n_pos} items, Compass = 0: {n_zero} items")
        print(f"  One group is empty, comparison not possible")

    # ── 3. Hypothesis 166 vs CCT 5/5 agreement ──
    print()
    print("-" * 65)
    print("  [3] Hypothesis 166 Judgment vs CCT 5/5 Agreement")
    print("-" * 65)

    h166_arr = np.array([r['h166'] for r in records])
    cct55_arr = cct_total_arr >= 5.0

    # Confusion matrix
    tp = np.sum(h166_arr & cct55_arr)
    fp = np.sum(h166_arr & ~cct55_arr)
    fn = np.sum(~h166_arr & cct55_arr)
    tn = np.sum(~h166_arr & ~cct55_arr)

    accuracy = (tp + tn) / total
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print()
    print(f"                    CCT 5/5     CCT < 5")
    print(f"  H166 = True    {tp:>8}     {fp:>8}     (Predict: conscious)")
    print(f"  H166 = False   {fn:>8}     {tn:>8}     (Predict: non-conscious)")
    print()
    print(f"  Accuracy          = {accuracy:.4f}")
    print(f"  Precision         = {precision:.4f}")
    print(f"  Recall            = {recall:.4f}")
    print(f"  F1 Score          = {f1:.4f}")

    # Additional comparison with CCT >= 4 criterion
    cct4_arr = cct_total_arr >= 4.0
    tp4 = np.sum(h166_arr & cct4_arr)
    fp4 = np.sum(h166_arr & ~cct4_arr)
    fn4 = np.sum(~h166_arr & cct4_arr)
    tn4 = np.sum(~h166_arr & ~cct4_arr)
    acc4 = (tp4 + tn4) / total

    print()
    print(f"  (Reference: Accuracy with CCT >= 4 criterion = {acc4:.4f})")

    # ── 4. ASCII scatter plots ──
    print()
    print("-" * 65)
    print("  [4] ASCII Scatter Plot: Compass vs CCT(total)")
    print("-" * 65)
    print()
    print(ascii_scatter(
        compass_arr.tolist(), cct_total_arr.tolist(),
        xlabel="Compass Score",
        ylabel="  CCT Total (/5)",
    ))

    print()
    print("-" * 65)
    print("  [5] ASCII Scatter Plot: I vs CCT(total)")
    print("-" * 65)
    print()
    print(ascii_scatter(
        i_arr.tolist(), cct_total_arr.tolist(),
        xlabel="Inhibition (I)",
        ylabel="  CCT Total (/5)",
    ))

    # ── 5. CCT distribution by I interval ──
    print()
    print("-" * 65)
    print("  [6] CCT Average by I Interval")
    print("-" * 65)
    print()
    print(f"  {'I value':>6} {'N':>4} {'CCT Avg':>8} {'CCT Range':>14}"
          f" {'Golden Zone':>8} {'Compass Avg':>12}")
    print(f"  {'─' * 6} {'─' * 4} {'─' * 8} {'─' * 14}"
          f" {'─' * 8} {'─' * 12}")

    for iv in I_VALUES:
        mask = np.isclose(i_arr, iv)
        n_iv = mask.sum()
        if n_iv == 0:
            continue
        cct_mean = cct_total_arr[mask].mean()
        cct_min = cct_total_arr[mask].min()
        cct_max = cct_total_arr[mask].max()
        comp_mean = compass_arr[mask].mean()
        in_golden = "Yes" if GOLDEN_LOWER <= iv <= GOLDEN_UPPER else "No"
        print(f"  {iv:>6.2f} {n_iv:>4} {cct_mean:>8.2f}"
              f" {cct_min:>5.1f} ~ {cct_max:>5.1f}"
              f" {in_golden:>8} {comp_mean:>12.4f}")

    # ── 6. Conclusion ──
    print()
    print("=" * 65)
    print("  [Conclusion]")
    print("=" * 65)
    print()

    # Compass-CCT correlation judgment
    r_compass_cct, p_compass_cct = stats.pearsonr(compass_arr, cct_total_arr)
    r_i_cct, p_i_cct = stats.pearsonr(i_arr, cct_total_arr)

    if abs(r_compass_cct) > 0.7:
        rel = "Strong correlation (dependent)"
    elif abs(r_compass_cct) > 0.4:
        rel = "Moderate correlation (partially dependent)"
    elif abs(r_compass_cct) > 0.2:
        rel = "Weak correlation (weakly dependent)"
    else:
        rel = "Almost no correlation (near independent)"

    print(f"  Compass vs CCT: r = {r_compass_cct:.4f} (p = {p_compass_cct:.2e})")
    print(f"  --> {rel}")
    print()
    print(f"  I vs CCT:       r = {r_i_cct:.4f} (p = {p_i_cct:.2e})")
    if abs(r_i_cct) > abs(r_compass_cct):
        print(f"  --> I is more directly related to CCT than Compass")
    else:
        print(f"  --> Compass is more directly related to CCT than I")
    print()

    print(f"  Hypothesis 166 judgment vs CCT agreement: {accuracy:.1%}")
    if accuracy > 0.7:
        print(f"  --> Hypothesis 166's consciousness judgment highly agrees with CCT")
    else:
        print(f"  --> Hypothesis 166 and CCT measure different aspects")
    print()
    print("=" * 65)

    return records


def main():
    parser = argparse.ArgumentParser(
        description="Experiment 16: Correlation Analysis between Compass Score and CCT Score",
    )
    parser.add_argument("--grid", type=int, default=None,
                        help="Simplified grid (N steps per axis, default: predefined grid)")
    parser.add_argument("--steps", type=int, default=10000,
                        help="Number of Lorenz simulation steps (default: 10000)")
    args = parser.parse_args()

    if args.grid is not None:
        global D_VALUES, P_VALUES, I_VALUES
        D_VALUES = np.linspace(0.1, 0.7, args.grid).tolist()
        P_VALUES = np.linspace(0.3, 0.9, args.grid).tolist()
        I_VALUES = np.linspace(0.1, 0.7, args.grid).tolist()

    run_analysis(steps=args.steps)


if __name__ == "__main__":
    main()