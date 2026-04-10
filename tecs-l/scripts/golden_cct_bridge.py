```python
#!/usr/bin/env python3
"""Golden Zone-CCT Bridge — Simulation of the relationship between I values and CCT scores

Scans the Inhibition(I) value of the G=D×P/I model in the 0~1 range,
mapping corresponding Lorenz parameters for each I and running 5 CCT tests.

Verifies whether CCT scores are maximized within the Golden Zone (I=0.213~0.500),
and whether the fixed point I=1/3 is truly optimal.

Usage:
  python3 golden_cct_bridge.py
  python3 golden_cct_bridge.py --grid 100
  python3 golden_cct_bridge.py --plot

Golden Zone dependency: YES (I range definition depends on Golden Zone)
"""

import argparse
import math
import os
import sys
from datetime import datetime

import numpy as np

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

# ─────────────────────────────────────────────
# Golden Zone constants
# ─────────────────────────────────────────────
GOLDEN_UPPER = 0.5                        # Riemann critical line
GOLDEN_LOWER = 0.5 - math.log(4 / 3)     # ≈ 0.2123
GOLDEN_CENTER = 1 / math.e               # ≈ 0.3679
FIXED_POINT = 1 / 3                       # Meta fixed point


# ─────────────────────────────────────────────
# I → Lorenz parameter mapping
# ─────────────────────────────────────────────
def i_to_lorenz(I):
    """Map Inhibition value to Lorenz simulator parameters.

    Mapping rationale:
      - sigma = 10*(1-I):  Higher inhibition dulls sensation
      - rho   = 28*(1-I/2): Higher inhibition reduces complexity
      - beta  = 2.67:       Fixed (forgetting rate)
      - noise = 0.3*(1-I):  Higher inhibition reduces noise
      - gap_ratio = max(0, (I-0.5)*2): Gap starts when I>0.5
    """
    sigma = 10.0 * (1.0 - I)
    rho = 28.0 * (1.0 - I / 2.0)
    beta = 2.67
    noise = 0.3 * (1.0 - I)
    gap_ratio = max(0.0, (I - 0.5) * 2.0)
    return {
        "sigma": sigma,
        "rho": rho,
        "beta": beta,
        "noise": noise,
        "gap_ratio": gap_ratio,
    }


# ─────────────────────────────────────────────
# Lorenz simulator (same as consciousness_calc.py)
# ─────────────────────────────────────────────
def lorenz_simulate(sigma, rho, beta, noise, gap_ratio, steps=50000, dt=0.01, seed=42):
    """Extended Lorenz simulator."""
    rng = np.random.default_rng(seed)
    S = np.zeros((steps, 3))
    S[0] = [1.0, 1.0, 1.0]

    active = np.ones(steps, dtype=bool)
    if gap_ratio > 0:
        n_gap = int(steps * gap_ratio)
        if n_gap > 0:
            gap_indices = rng.choice(steps, size=min(n_gap, steps), replace=False)
            active[gap_indices] = False

    for i in range(1, steps):
        if not active[i]:
            S[i] = S[i - 1]
            continue

        x, y, z = S[i - 1]
        dx = sigma * (y - x)
        dy = x * (rho - z) - y
        dz = x * y - beta * z

        eps = rng.normal(0, noise, 3) if noise > 0 else np.zeros(3)

        S[i, 0] = x + (dx + eps[0]) * dt
        S[i, 1] = y + (dy + eps[1]) * dt
        S[i, 2] = z + (dz + eps[2]) * dt

    return S


# ─────────────────────────────────────────────
# CCT 5 tests (based on consciousness_calc.py)
# ─────────────────────────────────────────────
def compute_entropy(data, bins=30):
    """Shannon entropy of 1D data."""
    if np.std(data) < 1e-12:
        return 0.0
    hist, _ = np.histogram(data, bins=bins, density=True)
    hist = hist[hist > 0]
    width = (data.max() - data.min()) / bins if data.max() > data.min() else 1
    probs = hist * width
    probs = probs[probs > 0]
    if len(probs) == 0:
        return 0.0
    probs = probs / probs.sum()
    return -np.sum(probs * np.log(probs + 1e-15))


def test_gap(S, gap_ratio):
    """T1 Gap: Presence of frozen periods."""
    if gap_ratio >= 1.0:
        return 0.0
    if gap_ratio > 0:
        return 1.0 - gap_ratio

    diffs = np.diff(S, axis=0)
    frozen = np.sum(np.all(np.abs(diffs) < 1e-12, axis=1))
    frozen_ratio = frozen / len(diffs)
    return max(0.0, 1.0 - frozen_ratio)


def test_loop(S):
    """T2 Loop: Trajectory revisitation (periodicity) ratio."""
    n = len(S)
    if n < 100:
        return 0.0

    step = max(1, n // 5000)
    Ss = S[::step]
    ns = len(Ss)

    if np.std(Ss) < 1e-10:
        return 0.0

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
    return max(0.0, 1.0 - recurrence_ratio)


def test_continuity(S):
    """T3 Continuity: Connectivity between adjacent steps."""
    diffs = np.linalg.norm(np.diff(S, axis=0), axis=1)
    n = len(diffs)
    if n < 10:
        return 0.0

    mean_diff = np.mean(diffs)
    if mean_diff < 1e-12:
        return 0.0

    big_jumps = np.sum(diffs > mean_diff * 10)
    frozen = np.sum(diffs < 1e-12)
    disconnect_ratio = (big_jumps + frozen) / n
    score = max(0.0, 1.0 - disconnect_ratio * 10)
    return min(1.0, score)


def test_entropy_band(S, window=500, h_min=0.3, h_max=4.5):
    """T4 Entropy Band: Is H(t) within the band?"""
    x = S[:, 0]
    n_windows = len(x) // window
    if n_windows < 2:
        return 0.0

    entropies = []
    for i in range(n_windows):
        w = x[i * window:(i + 1) * window]
        entropies.append(compute_entropy(w))
    entropies = np.array(entropies)
    in_band = np.sum((entropies > h_min) & (entropies < h_max))
    return in_band / len(entropies)


def test_novelty(S, window=500, threshold=0.001):
    """T5 Novelty: dH/dt != 0 (entropy stagnation ratio)."""
    x = S[:, 0]
    n_windows = len(x) // window
    if n_windows < 3:
        return 0.0

    entropies = []
    for i in range(n_windows):
        w = x[i * window:(i + 1) * window]
        entropies.append(compute_entropy(w))
    entropies = np.array(entropies)
    dH = np.abs(np.diff(entropies))

    stagnant = np.sum(dH < threshold)
    stagnant_ratio = stagnant / len(dH) if len(dH) > 0 else 1.0
    return max(0.0, 1.0 - stagnant_ratio)


def run_cct(S, gap_ratio):
    """Run 5 CCT tests, return total score (0~5)."""
    scores = {
        "T1_Gap": test_gap(S, gap_ratio),
        "T2_Loop": test_loop(S),
        "T3_Continuity": test_continuity(S),
        "T4_Entropy": test_entropy_band(S),
        "T5_Novelty": test_novelty(S),
    }
    return scores


# ─────────────────────────────────────────────
# I scan
# ─────────────────────────────────────────────
def scan_i_range(grid, steps=50000, dt=0.01):
    """Scan I=0~1, run CCT at each I.

    Returns:
        i_values: array of I values
        cct_totals: array of total CCT scores (0~5)
        cct_details: list of per-test score dicts
    """
    # I=0 exactly causes division-by-zero, so start slightly above
    i_values = np.linspace(0.01, 0.99, grid)
    cct_totals = np.zeros(grid)
    cct_details = []

    for idx, I in enumerate(i_values):
        params = i_to_lorenz(I)
        S = lorenz_simulate(
            sigma=params["sigma"],
            rho=params["rho"],
            beta=params["beta"],
            noise=params["noise"],
            gap_ratio=params["gap_ratio"],
            steps=steps,
            dt=dt,
            seed=42,
        )
        scores = run_cct(S, params["gap_ratio"])
        total = sum(scores.values())
        cct_totals[idx] = total
        cct_details.append(scores)

        # Progress display
        pct = (idx + 1) / grid * 100
        bar_len = 30
        filled = int(bar_len * (idx + 1) / grid)
        bar = "█" * filled + "░" * (bar_len - filled)
        sys.stdout.write(f"\r  Scanning: [{bar}] {pct:5.1f}% (I={I:.3f})")
        sys.stdout.flush()

    sys.stdout.write("\r" + " " * 70 + "\r")
    sys.stdout.flush()

    return i_values, cct_totals, cct_details


# ─────────────────────────────────────────────
# ASCII graph
# ─────────────────────────────────────────────
def ascii_graph(i_values, cct_totals, width=60, height=20):
    """I vs CCT total score ASCII graph.

    Displays Golden Zone and fixed point.
    """
    lines = []

    y_min = 0.0
    y_max = 5.0
    x_min = i_values[0]
    x_max = i_values[-1]

    # Create canvas
    canvas = [[" " for _ in range(width)] for _ in range(height)]

    # Plot data points
    for i, (iv, cv) in enumerate(zip(i_values, cct_totals)):
        col = int((iv - x_min) / (x_max - x_min) * (width - 1))
        col = max(0, min(col, width - 1))
        row = int((cv - y_min) / (y_max - y_min) * (height - 1))
        row = max(0, min(row, height - 1))
        row = height - 1 - row  # Invert top-bottom
        canvas[row][col] = "█"

    # Mark Golden Zone boundaries (vertical dotted lines)
    col_lower = int((GOLDEN_LOWER - x_min) / (x_max - x_min) * (width - 1))
    col_upper = int((GOLDEN_UPPER - x_min) / (x_max - x_min) * (width - 1))
    col_fixed = int((FIXED_POINT - x_min) / (x_max - x_min) * (width - 1))
    col_lower = max(0, min(col_lower, width - 1))
    col_upper = max(0, min(col_upper, width - 1))
    col_fixed = max(0, min(col_fixed, width - 1))

    for row in range(height):
        if canvas[row][col_lower] == " ":
            canvas[row][col_lower] = "┊"
        if canvas[row][col_upper] == " ":
            canvas[row][col_upper] = "┊"
        if canvas[row][col_fixed] == " ":
            canvas[row][col_fixed] = "│"

    # Y-axis labels + canvas assembly
    lines.append("")
    lines.append("  CCT Score vs Inhibition (I)")
    lines.append("")
    for row in range(height):
        y_val = y_max - (y_max - y_min) * row / (height - 1)
        if row == 0:
            label = f" {y_val:.1f}"
        elif row == height - 1:
            label = f" {y_val:.1f}"
        elif row == height // 2:
            y_mid = y_max - (y_max - y_min) * row / (height - 1)
            label = f" {y_mid:.1f}"
        else:
            label = "    "
        lines.append(f" {label:>4}│{''.join(canvas[row])}")

    # X-axis
    lines.append(f"     └{'─' * width}")

    # X-axis labels: 0, golden lower, 1/3, golden upper, 1.0
    x_label_line = "      "
    markers = [
        (0.0, "0"),
        (GOLDEN_LOWER, f"{GOLDEN_LOWER:.3f}"),
        (FIXED_POINT, "1/3"),
        (GOLDEN_UPPER, "0.500"),
        (1.0, "1.0"),
    ]

    # Simple position markers
    x_positions = []
    for val, lbl in markers:
        pos = int((val - x_min) / (x_max - x_min) * (width - 1))
        pos = max(0, min(pos, width - 1))
        x_positions.append((pos, lbl))

    tick_line = list(" " * (width + 6))
    for pos, lbl in x_positions:
        start = pos + 6
        for ci, ch in enumerate(lbl):
            if 0 <= start + ci < len(tick_line):
                tick_line[start + ci] = ch

    lines.append("".join(tick_line))

    # Golden Zone range display
    mid_col = (col_lower + col_upper) // 2 + 6
    zone_line = list(" " * (width + 10))
    # Lower bound mark
    if col_lower + 6 < len(zone_line):
        zone_line[col_lower + 6] = "└"
    # Upper bound mark
    if col_upper + 6 < len(zone_line):
        zone_line[col_upper + 6] = "┘"
    # Middle dash
    for c in range(col_lower + 7, col_upper + 6):
        if 0 <= c < len(zone_line):
            zone_line[c] = "─"
    # Label
    label = " Golden Zone "
    lstart = mid_col - len(label) // 2
    for ci, ch in enumerate(label):
        if 0 <= lstart + ci < len(zone_line):
            zone_line[lstart + ci] = ch

    lines.append("".join(zone_line))
    lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# Analysis and report
# ─────────────────────────────────────────────
def analyze_results(i_values, cct_totals, cct_details):
    """Analyze scan results: optimal point, Golden Zone statistics, fixed point score."""
    # Overall maximum
    best_idx = np.argmax(cct_totals)
    best_i = i_values[best_idx]
    best_score = cct_totals[best_idx]

    # Golden Zone mask
    golden_mask = (i_values >= GOLDEN_LOWER) & (i_values <= GOLDEN_UPPER)
    outside_mask = ~golden_mask

    golden_scores = cct_totals[golden_mask]
    outside_scores = cct_totals[outside_mask]

    golden_mean = np.mean(golden_scores) if len(golden_scores) > 0 else 0.0
    outside_mean = np.mean(outside_scores) if len(outside_scores) > 0 else 0.0
    golden_max = np.max(golden_scores) if len(golden_scores) > 0 else 0.0
    outside_max = np.max(outside_scores) if len(outside_scores) > 0 else 0.0

    # Fixed point I=1/3 vicinity
    fixed_idx = np.argmin(np.abs(i_values - FIXED_POINT))
    fixed_score = cct_totals[fixed_idx]
    fixed_details = cct_details[fixed_idx]

    # Golden Zone center I=1/e vicinity
    center_idx = np.argmin(np.abs(i_values - GOLDEN_CENTER))
    center_score = cct_totals[center_idx]

    # Boundary analysis: difference just outside vs inside Golden Zone
    lower_boundary_inside = cct_totals[golden_mask][:3] if np.sum(golden_mask) >= 3 else np.array([])
    lower_boundary_outside = cct_totals[outside_mask & (i_values < GOLDEN_LOWER)]
    lower_boundary_outside = lower_boundary_outside[-3:] if len(lower_boundary_outside) >= 3 else lower_boundary_outside

    upper_boundary_inside = cct_totals[golden_mask][-3:] if np.sum(golden_mask) >= 3 else np.array([])
    upper_boundary_outside = cct_totals[outside_mask & (i_values > GOLDEN_UPPER)]
    upper_boundary_outside = upper_boundary_outside[:3] if len(upper_boundary_outside) >= 3 else upper_boundary_outside

    return {
        "best_i": best_i,
        "best_score": best_score,
        "golden_mean": golden_mean,
        "outside_mean": outside_mean,
        "golden_max": golden_max,
        "outside_max": outside_max,
        "fixed_i": i_values[fixed_idx],
        "fixed_score": fixed_score,
        "fixed_details": fixed_details,
        "center_i": i_values[center_idx],
        "center_score": center_score,
        "lower_drop": np.mean(lower_boundary_inside) - np.mean(lower_boundary_outside) if len(lower_boundary_inside) > 0 and len(lower_boundary_outside) > 0 else 0.0,
        "upper_drop": np.mean(upper_boundary_inside) - np.mean(upper_boundary_outside) if len(upper_boundary_inside) > 0 and len(upper_boundary_outside) > 0 else 0.0,
    }


def print_report(i_values, cct_totals, cct_details, analysis, grid):
    """Print results report."""
    print()
    print("═" * 65)
    print("  Golden Zone-CCT Bridge v1.0")
    print("  Relationship between I value and CCT Consciousness Continuity Score in G=D×P/I model")
    print("═" * 65)
    print()
    print(f"  Resolution: grid={grid} ({len(i_values)} I values scanned)")
    print(f"  Golden Zone: I ∈ [{GOLDEN_LOWER:.4f}, {GOLDEN_UPPER:.4f}]")
    print(f"  Fixed Point: I = 1/3 ≈ {FIXED_POINT:.4f}")
    print(f"  Golden Zone Center: I = 1/e ≈ {GOLDEN_CENTER:.4f}")
    print()

    # ASCII graph
    print(ascii_graph(i_values, cct_totals))

    # Key findings
    print("─" * 65)
    print("  [ Key Findings ]")
    print("─" * 65)
    print()

    # 1. Optimal point
    print(f"  1. Overall Maximum CCT Score")
    print(f"     I = {analysis['best_i']:.4f},  CCT = {analysis['best_score']:.3f} / 5.000")
    in_golden = GOLDEN_LOWER <= analysis['best_i'] <= GOLDEN_UPPER
    if in_golden:
        print(f"     → Located within Golden Zone ✔")
    else:
        print(f"     → Located outside Golden Zone ✕")
    print()

    # 2. Golden Zone vs Outside
    print(f"  2. Golden Zone Inside vs Outside")
    print(f"     Golden Zone mean CCT = {analysis['golden_mean']:.3f}")
    print(f"     Golden Zone max CCT = {analysis['golden_max']:.3f}")
    print(f"     Outside mean CCT = {analysis['outside_mean']:.3f}")
    print(f"     Outside max CCT = {analysis['outside_max']:.3f}")
    diff = analysis['golden_mean'] - analysis['outside_mean']
    if diff > 0:
        print(f"     → Golden Zone is {diff:.3f} points higher on average ✔")
    else:
        print(f"     → Golden Zone is {abs(diff):.3f} points lower on average ✕")
    print()

    # 3. Fixed point I=1/3
    print(f"  3. Fixed Point I=1/3 Analysis")
    print(f"     I = {analysis['fixed_i']:.4f},  CCT = {analysis['fixed_score']:.3f}")
    fixed_rank_pct = np.sum(cct_totals <= analysis['fixed_score']) / len(cct_totals) * 100
    print(f"     Overall percentile: top {100 - fixed_rank_pct:.1f}%")
    if analysis['fixed_score'] >= analysis['best_score'] * 0.95:
        print(f"     → 95% or more of optimal, near-optimal ✔")
    else:
        print(f"     → {analysis['fixed_score']/analysis['best_score']*100:.1f}% of optimal")
    print()

    # 4. Fixed point detailed scores
    print(f"  4. I=1/3 CCT Details (5 tests)")
    fd = analysis["fixed_details"]
    for key in ["T1_Gap", "T2_Loop", "T3_Continuity", "T4_Entropy", "T5_Novelty"]:
        bar_len = 20
        filled = int(fd[key] * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"     {key:15s} [{bar}] {fd[key]:.3f}")
    print()

    # 5. Boundary drop-off
    print(f"  5. Golden Zone Boundary Drop-off Analysis")
    print(f"     Lower boundary (I≈0.213): inside→outside CCT diff = {analysis['lower_drop']:+.3f}")
    print(f"     Upper boundary (I≈0.500): inside→outside CCT diff = {analysis['upper_drop']:+.3f}")
    if analysis['lower_drop'] > 0.3 or analysis['upper_drop'] > 0.3:
        print(f"     → Sharp drop observed at boundary ✔")
    elif analysis['lower_drop'] > 0 or analysis['upper_drop'] > 0:
        print(f"     → Gradual drop observed at boundary")
    else:
        print(f"     → Weak boundary effect")
    print()

    # 6. Golden Zone center 1/e
    print(f"  6. Golden Zone Center I=1/e")
    print(f"     I = {analysis['center_i']:.4f},  CCT = {analysis['center_score']:.3f}")
    print()

    # Overall verdict
    print("═" * 65)
    print("  [ Overall Verdict ]")
    print()
    verdict_count = 0
    if in_golden:
        print(f"  ✔ Optimal point located within Golden Zone")
        verdict_count += 1
    if diff > 0:
        print(f"  ✔ Golden Zone mean CCT > Outside mean CCT")
        verdict_count += 1
    if analysis['fixed_score'] >= analysis['best_score'] * 0.90:
        print(f"  ✔ Fixed point I=1/3 is near-optimal ({analysis['fixed_score']/analysis['best_score']*100:.1f}% of optimal)")
        verdict_count += 1
    if analysis['lower_drop'] > 0 or analysis['upper_drop'] > 0:
        print(f"  ✔ CCT drop observed at Golden Zone boundaries")
        verdict_count += 1

    print()
    if verdict_count >= 3:
        print(f"  → Conclusion: Golden Zone-CCT Bridge strongly established ({verdict_count}/4)")
    elif verdict_count >= 2:
        print(f"  → Conclusion: Golden Zone-CCT Bridge partially established ({verdict_count}/4)")
    else:
        print(f"  → Conclusion: Golden Zone-CCT Bridge weak ({verdict_count}/4)")
    print("═" * 65)
    print()


# ─────────────────────────────────────────────
# Detailed table output
# ─────────────────────────────────────────────
def print_detail_table(i_values, cct_totals, cct_details):
    """Detailed table by I value (key points only)."""
    print()
    print("─" * 75)
    print("  [ CCT Details by I Value (Key Points) ]")
    print("─" * 75)
    print(f"  {'I':>6} │ {'σ':>5} │ {'ρ':>5} │ {'noise':>5} │ {'gap':>4} │"
          f" {'T1':>5} │ {'T2':>5} │ {'T3':>5} │ {'T4':>5} │ {'T5':>5} │ {'Total':>5} │ Position")
    print(f"  {'─'*6}─┼─{'─'*5}─┼─{'─'*5}─┼─{'─'*5}─┼─{'─'*4}─┼─"
          f"{'─'*5}─┼─{'─'*5}─┼─{'─'*5}─┼─{'─'*5}─┼─{'─'*5}─┼─{'─'*5}─┼─{'─'*8}")

    # Select key points
    key_points = [
        (0.05, "Very low inhib"),
        (0.10, ""),
        (GOLDEN_LOWER, "Golden lower"),
        (0.25, ""),
        (FIXED_POINT, "★Fixed point"),
        (GOLDEN_CENTER, "1/e center"),
        (0.45, ""),
        (GOLDEN_UPPER, "Golden upper"),
        (0.60, ""),
        (0.70, ""),
        (0.80, ""),
        (0.90, "High inhib"),
    ]

    for target_i, label in key_points:
        idx = np.argmin(np.abs(i_values - target_i))
        I = i_values[idx]
        params = i_to_lorenz(I)
        d = cct_details[idx]
        total = cct_totals[idx]
        print(f"  {I:6.3f} │ {params['sigma']:5.1f} │ {params['rho']:5.1f} │"
              f" {params['noise']:5.2f} │ {params['gap_ratio']:4.2f} │"
              f" {d['T1_Gap']:5.3f} │ {d['T2_Loop']:5.3f} │"
              f" {d['T3_Continuity']:5.3f} │ {d['T4_Entropy']:5.3f} │"
              f" {d['T5_Novelty']:5.3f} │ {total:5.3f} │ {label}")

    print("─" * 75)
    print()


# ─────────────────────────────────────────────
# matplotlib output
# ─────────────────────────────────────────────
def plot_results(i_values, cct_totals, cct_details, analysis):
    """Save matplotlib graphs."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  [Warning] matplotlib not available, skipping --plot")
        return None

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Golden Zone - CCT Bridge", fontsize=14, fontweight="bold")

    # 1. I vs CCT total
    ax1 = axes[0, 0]
    ax1.plot(i_values, cct_totals, color="royalblue", lw=1.5, label="CCT Total")
    ax1.axvspan(GOLDEN_LOWER, GOLDEN_UPPER, alpha=0.15, color="gold", label="Golden Zone")
    ax1.axvline(FIXED_POINT, color="red", ls="--", alpha=0.7, label="I=1/3")
    ax1.axvline(GOLDEN_CENTER, color="green", ls=":", alpha=0.7, label="I=1/e")
    ax1.set_xlabel("Inhibition (I)")
    ax1.set_ylabel("CCT Total Score")
    ax1.set_title("I vs CCT Total Score")
    ax1.legend(fontsize=8)
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 5.5)
    ax1.grid(True, alpha=0.3)

    # 2. Individual test scores
    ax2 = axes[0, 1]
    test_keys = ["T1_Gap", "T2_Loop", "T3_Continuity", "T4_Entropy", "T5_Novelty"]
    colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6"]
    for key, color in zip(test_keys, colors):
        vals = [d[key] for d in cct_details]
        ax2.plot(i_values, vals, color=color, lw=1, alpha=0.8, label=key)
    ax2.axvspan(GOLDEN_LOWER, GOLDEN_UPPER, alpha=0.1, color="gold")
    ax2.axvline(FIXED_POINT, color="red", ls="--", alpha=0.5)
    ax2.set_xlabel("Inhibition (I)")
    ax2.set_ylabel("Score")
    ax2.set_title("Individual CCT Test Scores")
    ax2.legend(fontsize=7)
    ax2.set_xlim(0, 1)
    ax2.set_ylim(-0.1, 1.1)
    ax2.grid(True, alpha=0.3)

    # 3. Lorenz parameters vs I
    ax3 = axes[1, 0]
    sigmas = [10.0 * (1 - I) for I in i_values]
    rhos = [28.0 * (1 - I / 2) for I in i_values]
    noises = [0.3 * (1 - I) for I in i_values]
    gaps = [max(0, (I - 0.5) * 2) for I in i_values]
    ax3.plot(i_values, sigmas, label="sigma", lw=1.5)
    ax3.plot(i_values, rhos, label="rho", lw=1.5)
    ax3.plot(i_values, [n * 30 for n in noises], label="noise×30", lw=1, ls="--")
    ax3.plot(i_values, [g * 10 for g in gaps], label="gap×10", lw=1, ls=":")
    ax3.axvspan(GOLDEN_LOWER, GOLDEN_UPPER, alpha=0.1, color="gold")
    ax3.set_xlabel("Inhibition (I)")
    ax3.set_ylabel("Parameter Value")
    ax3.set_title("Lorenz Parameters vs I")
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3)

    # 4. Golden Zone inside/outside comparison bar chart
    ax4 = axes[1, 1]
    golden_mask = (i_values >= GOLDEN_LOWER) & (i_values <= GOLDEN_UPPER)
    for ki, key in enumerate(test_keys):
        golden_vals = [cct_details[i][key] for i in range(len(i_values)) if golden_mask[i]]
        outside_vals = [cct_details[i][key] for i in range(len(i_values)) if not golden_mask[i]]
        g_mean = np.mean(golden_vals) if golden_vals else 0
        o_mean = np.mean(outside_vals) if outside_vals else 0
        ax4.bar(ki - 0.2, g_mean, width=0.35, color="gold", alpha=0.8,
                label="Golden Zone" if ki == 0 else "")
        ax4.bar(ki + 0.2, o_mean, width=0.35, color="steelblue", alpha=0.8,
                label="Outside" if ki == 0 else "")
    ax4.set_xticks(range(len(test_keys)))
    ax4.set_xticklabels(["T1", "T2", "T3", "T4", "T5"])
    ax4.set_ylabel("Mean Score")
    ax4.set_title("Golden Zone vs Outside (per test)")
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.3, axis="y")

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    os.makedirs(RESULTS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(RESULTS_DIR, f"golden_cct_bridge_{ts}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Golden Zone-CCT Bridge: Simulation of the relationship between I values and CCT consciousness continuity scores",
    )
    parser.add_argument("--grid", type=int, default=50,
                        help="I value scan resolution (default 50, fast 20, precise 100)")
    parser.add_argument("--steps", type=int, default=50000,
                        help="Lorenz simulation step count (default 50000)")
    parser.add_argument("--dt", type=float, default=0.01,
                        help="Time interval (default 0.01)")
    parser.add_argument("--plot", action="store_true",
                        help="Save matplotlib 4-panel graph")
    parser.add_argument("--detail", action="store_true",
                        help="Output detailed table for key points")

    args = parser.parse_args()

    print()
    print(f"  Golden Zone-CCT Bridge simulation starting")
    print(f"  grid={args.grid}, steps={args.steps}, dt={args.dt}")
    print()

    # Scan
    i_values, cct_totals, cct_details = scan_i_range(
        grid=args.grid, steps=args.steps, dt=args.dt,
    )

    # Analyze
    analysis = analyze_results(i_values, cct_totals, cct_details)

    # Report
    print_report(i_values, cct_totals, cct_details, analysis, args.grid)

    # Detailed table
    if args.detail or args.grid <= 50:
        print_detail_table(i_values, cct_totals, cct_details)

    # Plot
    if args.plot:
        path = plot_results(i_values, cct_totals, cct_details, analysis)
        if path:
            print(f"  [plot] Saved to: {path}")
            print()


if __name__ == "__main__":
    main()
```