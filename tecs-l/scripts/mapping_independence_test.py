#!/usr/bin/env python3
"""Mapping Independence Verification — Is "Maximum CCT in Golden Zone" a Structural Discovery?

By generating 1000 random mapping formulas, we verify whether the result
"CCT is maximum in Golden Zone" is due to the specificity of our mapping
(i_to_lorenz) or a structural property of the Lorenz system itself.

Experiment:
  - 1000 random mappings: sigma, rho, noise, gap = f(I) (random coefficients)
  - For each mapping, scan I=0~1 → record optimal I value for CCT
  - Measure the ratio of optimal I values falling in Golden Zone (0.213~0.500)
  - Compare with random expected value (28.7%) → binomial test

Golden Zone dependency: YES (verification target itself is Golden Zone)

Usage:
  python3 mapping_independence_test.py
  python3 mapping_independence_test.py --n-mappings 500 --grid 15
  python3 mapping_independence_test.py --quick
"""

import sys, os

import argparse
import math
import sys
import time

import numpy as np
from scipy import stats as sp_stats

from consciousness_calc import lorenz_simulate, run_cct

# ─────────────────────────────────────────────
# Golden Zone Constants
# ─────────────────────────────────────────────
GOLDEN_UPPER = 0.5
GOLDEN_LOWER = 0.5 - math.log(4 / 3)   # ≈ 0.2123
GOLDEN_WIDTH = GOLDEN_UPPER - GOLDEN_LOWER  # ≈ 0.2877
GOLDEN_EXPECTED = GOLDEN_WIDTH / (0.99 - 0.01)  # Based on scan range 0.01~0.99


# ─────────────────────────────────────────────
# Random Mapping Generation
# ─────────────────────────────────────────────
def generate_random_mapping(rng):
    """Generate random mapping coefficients.

    Each parameter = a + b * I^c form.
    Range constraints: sigma ∈ [0.1, 20], rho ∈ [1, 50], noise ∈ [0, 1], gap ∈ [0, 1]

    Returns:
        dict with keys 'sigma_abc', 'rho_abc', 'noise_abc', 'gap_abc'
        Each value is (a, b, c) tuple
    """
    def rand_abc(a_range, b_range, c_range):
        a = rng.uniform(*a_range)
        b = rng.uniform(*b_range)
        c = rng.uniform(*c_range)
        return (a, b, c)

    return {
        # sigma: 0.1~20 range. a ∈ [0.1, 15], b ∈ [-15, 15], c ∈ [0.2, 3]
        "sigma_abc": rand_abc((0.1, 15.0), (-15.0, 15.0), (0.2, 3.0)),
        # rho: 1~50 range. a ∈ [1, 40], b ∈ [-30, 30], c ∈ [0.2, 3]
        "rho_abc": rand_abc((1.0, 40.0), (-30.0, 30.0), (0.2, 3.0)),
        # noise: 0~1 range. a ∈ [0, 0.5], b ∈ [-0.5, 0.5], c ∈ [0.2, 3]
        "noise_abc": rand_abc((0.0, 0.5), (-0.5, 0.5), (0.2, 3.0)),
        # gap: 0~1 range. a ∈ [-0.5, 0.3], b ∈ [-0.5, 0.5], c ∈ [0.2, 3]
        "gap_abc": rand_abc((-0.5, 0.3), (-0.5, 0.5), (0.2, 3.0)),
    }


def apply_mapping(mapping, I):
    """Convert I to Lorenz parameters using mapping coefficients."""
    def calc(abc, I_val):
        a, b, c = abc
        return a + b * (I_val ** c)

    sigma = np.clip(calc(mapping["sigma_abc"], I), 0.1, 20.0)
    rho = np.clip(calc(mapping["rho_abc"], I), 1.0, 50.0)
    noise = np.clip(calc(mapping["noise_abc"], I), 0.0, 1.0)
    gap = np.clip(calc(mapping["gap_abc"], I), 0.0, 1.0)
    beta = 2.67

    return {
        "sigma": float(sigma),
        "rho": float(rho),
        "beta": beta,
        "noise": float(noise),
        "gap_ratio": float(gap),
    }


def generate_inverted_mapping(rng):
    """Inverted mapping: Generate mapping in opposite direction from original.

    sigma = a + b*I (b > 0, i.e., sigma increases as I increases — opposite of original)
    rho   = a + b*I (b > 0)
    noise = a + b*I (b > 0)
    gap   = a + b*I (b < 0, i.e., gap decreases as I increases)
    """
    return {
        "sigma_abc": (rng.uniform(0.5, 5.0), rng.uniform(5.0, 15.0), 1.0),
        "rho_abc": (rng.uniform(5.0, 15.0), rng.uniform(10.0, 30.0), 1.0),
        "noise_abc": (rng.uniform(0.0, 0.1), rng.uniform(0.1, 0.5), 1.0),
        "gap_abc": (rng.uniform(0.0, 0.5), rng.uniform(-0.8, -0.2), 1.0),
    }


# ─────────────────────────────────────────────
# CCT Scan
# ─────────────────────────────────────────────
def scan_mapping(mapping, grid, steps, dt):
    """Scan I=0.01~0.99 for one mapping to get CCT total score.

    Returns:
        best_i: I value with maximum CCT
        best_score: Maximum CCT total score
        has_gap: Whether gap > 0 exists for any I value in this mapping
    """
    i_values = np.linspace(0.01, 0.99, grid)
    best_i = 0.0
    best_score = -1.0
    has_gap = False

    for I in i_values:
        params = apply_mapping(mapping, I)
        if params["gap_ratio"] > 0.01:
            has_gap = True

        try:
            _, S = lorenz_simulate(
                sigma=params["sigma"],
                rho=params["rho"],
                beta=params["beta"],
                noise=params["noise"],
                gap_ratio=params["gap_ratio"],
                steps=steps,
                dt=dt,
                seed=42,
            )

            results = run_cct(S, params["gap_ratio"])
            # run_cct returns dict of (score, passed, detail) tuples
            total = sum(score for score, _, _ in results.values())

            if total > best_score:
                best_score = total
                best_i = I
        except Exception:
            continue

    return best_i, best_score, has_gap


# ─────────────────────────────────────────────
# ASCII Histogram
# ─────────────────────────────────────────────
def ascii_histogram(values, bins=20, width=50, title=""):
    """Return ASCII histogram of value distribution."""
    lines = []
    if title:
        lines.append(f"  {title}")
        lines.append("")

    hist, edges = np.histogram(values, bins=bins, range=(0.0, 1.0))
    max_count = max(hist) if max(hist) > 0 else 1

    for i in range(len(hist)):
        lo = edges[i]
        hi = edges[i + 1]
        bar_len = int(hist[i] / max_count * width)
        bar = "█" * bar_len

        # Mark if within Golden Zone
        mid = (lo + hi) / 2
        in_golden = GOLDEN_LOWER <= mid <= GOLDEN_UPPER
        marker = " ◀" if in_golden else ""

        lines.append(f"  {lo:.2f}-{hi:.2f} │{bar:<{width}} {hist[i]:>4}{marker}")

    lines.append(f"  {'─' * 10}┘{'─' * width}")
    lines.append(f"  Golden Zone range: {GOLDEN_LOWER:.3f} ~ {GOLDEN_UPPER:.3f}")
    lines.append("")
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Binomial Test
# ─────────────────────────────────────────────
def binomial_test(n_in_golden, n_total, expected_rate):
    """Calculate p-value using binomial test."""
    result = sp_stats.binomtest(n_in_golden, n_total, expected_rate, alternative="greater")
    return result.pvalue


# ─────────────────────────────────────────────
# Main Experiment
# ─────────────────────────────────────────────
def run_experiment(n_mappings, grid, steps, dt, seed=12345):
    """Run entire experiment."""
    rng = np.random.default_rng(seed)

    # Normal random mappings (80%) + inverted mappings (20%)
    n_inverted = n_mappings // 5
    n_normal = n_mappings - n_inverted

    all_best_i = []
    all_has_gap = []
    all_mapping_type = []  # 'normal' or 'inverted'

    t_start = time.time()

    print(f"  Experiment Settings:")
    print(f"    Total mappings:     {n_mappings}")
    print(f"    Normal mappings:    {n_normal}")
    print(f"    Inverted mappings:  {n_inverted}")
    print(f"    I scan resolution:  grid={grid}")
    print(f"    Simulation:         steps={steps}, dt={dt}")
    print(f"    Golden Zone:        [{GOLDEN_LOWER:.4f}, {GOLDEN_UPPER:.4f}]")
    print(f"    Golden Zone width:  {GOLDEN_WIDTH:.4f}")
    print(f"    Random expected ratio: {GOLDEN_EXPECTED:.4f} ({GOLDEN_EXPECTED*100:.1f}%)")
    print()

    for i in range(n_mappings):
        if i < n_normal:
            mapping = generate_random_mapping(rng)
            mtype = "normal"
        else:
            mapping = generate_inverted_mapping(rng)
            mtype = "inverted"

        best_i, best_score, has_gap = scan_mapping(mapping, grid, steps, dt)
        all_best_i.append(best_i)
        all_has_gap.append(has_gap)
        all_mapping_type.append(mtype)

        # Progress (every 100 or every 10%)
        if (i + 1) % max(1, n_mappings // 10) == 0 or (i + 1) == n_mappings:
            elapsed = time.time() - t_start
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (n_mappings - i - 1) / rate if rate > 0 else 0
            pct = (i + 1) / n_mappings * 100
            bar_len = 30
            filled = int(bar_len * (i + 1) / n_mappings)
            bar = "█" * filled + "░" * (bar_len - filled)
            sys.stdout.write(
                f"\r  Progress: [{bar}] {pct:5.1f}% ({i+1}/{n_mappings}) "
                f"ETA: {eta:.0f}s"
            )
            sys.stdout.flush()

    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()

    elapsed = time.time() - t_start
    print(f"  Complete: {n_mappings} mappings, {elapsed:.1f}s elapsed")
    print()

    # numpy conversion
    all_best_i = np.array(all_best_i)
    all_has_gap = np.array(all_has_gap)
    all_mapping_type = np.array(all_mapping_type)

    return all_best_i, all_has_gap, all_mapping_type


def analyze_and_report(all_best_i, all_has_gap, all_mapping_type):
    """Analyze and report results."""
    n_total = len(all_best_i)

    # 1. Overall analysis
    in_golden = (all_best_i >= GOLDEN_LOWER) & (all_best_i <= GOLDEN_UPPER)
    n_in_golden = np.sum(in_golden)
    ratio_golden = n_in_golden / n_total

    # Binomial test
    p_value = binomial_test(int(n_in_golden), n_total, GOLDEN_EXPECTED)

    print("═" * 65)
    print("  Mapping Independence Verification — Golden Zone CCT Optimization Test")
    print("═" * 65)
    print()

    # Histogram
    print(ascii_histogram(all_best_i, bins=20, title="Optimal I Value Distribution (Overall)"))

    # Key results
    print("─" * 65)
    print("  [ Key Results ]")
    print("─" * 65)
    print()
    print(f"  Total mappings:          {n_total}")
    print(f"  Optimal I in Golden Zone: {n_in_golden} ({ratio_golden*100:.1f}%)")
    print(f"  Random expected:         {GOLDEN_EXPECTED*100:.1f}%")
    print(f"  Excess ratio:            {(ratio_golden - GOLDEN_EXPECTED)*100:+.1f}%p")
    print(f"  Binomial test p-value:   {p_value:.6f}")
    if p_value < 0.001:
        print(f"  Significance level:      p < 0.001 ★★★")
    elif p_value < 0.01:
        print(f"  Significance level:      p < 0.01  ★★")
    elif p_value < 0.05:
        print(f"  Significance level:      p < 0.05  ★")
    else:
        print(f"  Significance level:      Not significant (p >= 0.05)")
    print()

    # 2. Analysis by mapping type
    normal_mask = all_mapping_type == "normal"
    inverted_mask = all_mapping_type == "inverted"

    print("─" * 65)
    print("  [ Analysis by Mapping Type ]")
    print("─" * 65)
    print()

    for label, mask in [("Normal mappings", normal_mask), ("Inverted mappings", inverted_mask)]:
        if np.sum(mask) == 0:
            continue
        subset = all_best_i[mask]
        n_sub = len(subset)
        n_sub_golden = np.sum((subset >= GOLDEN_LOWER) & (subset <= GOLDEN_UPPER))
        r_sub = n_sub_golden / n_sub if n_sub > 0 else 0
        p_sub = binomial_test(int(n_sub_golden), n_sub, GOLDEN_EXPECTED) if n_sub > 0 else 1.0
        print(f"  {label}:")
        print(f"    Count:              {n_sub}")
        print(f"    Golden Zone ratio:  {n_sub_golden}/{n_sub} ({r_sub*100:.1f}%)")
        print(f"    p-value:            {p_sub:.6f}")
        print()

    # 3. Analysis by gap presence
    print("─" * 65)
    print("  [ Analysis by Gap Presence ]")
    print("─" * 65)
    print()

    for label, mask in [("Mappings with gap", all_has_gap), ("Mappings without gap", ~all_has_gap)]:
        if np.sum(mask) == 0:
            print(f"  {label}: None")
            print()
            continue
        subset = all_best_i[mask]
        n_sub = len(subset)
        n_sub_golden = np.sum((subset >= GOLDEN_LOWER) & (subset <= GOLDEN_UPPER))
        r_sub = n_sub_golden / n_sub if n_sub > 0 else 0
        p_sub = binomial_test(int(n_sub_golden), n_sub, GOLDEN_EXPECTED) if n_sub > 0 else 1.0
        print(f"  {label}:")
        print(f"    Count:              {n_sub}")
        print(f"    Golden Zone ratio:  {n_sub_golden}/{n_sub} ({r_sub*100:.1f}%)")
        print(f"    p-value:            {p_sub:.6f}")
        mean_i = np.mean(subset)
        std_i = np.std(subset)
        print(f"    Optimal I mean±std: {mean_i:.3f} ± {std_i:.3f}")
        print()

    # Histogram for mappings without gap only
    no_gap_mask = ~all_has_gap
    if np.sum(no_gap_mask) > 10:
        print(ascii_histogram(
            all_best_i[no_gap_mask], bins=20,
            title="Optimal I Value Distribution (Mappings without gap only)",
        ))

    # 4. Texas Sharpshooter Test Summary
    print("─" * 65)
    print("  [ Texas Sharpshooter Test ]")
    print("─" * 65)
    print()
    print(f"  H0: Golden Zone concentration of optimal I is by chance (expected={GOLDEN_EXPECTED*100:.1f}%)")
    print(f"  H1: Golden Zone concentration is structural (exceeds expected)")
    print()
    print(f"  Observed:   {n_in_golden}/{n_total} ({ratio_golden*100:.1f}%)")
    print(f"  Expected:   {GOLDEN_EXPECTED*n_total:.1f}/{n_total} ({GOLDEN_EXPECTED*100:.1f}%)")
    print(f"  p-value:    {p_value:.6f}")
    print()

    # 5. Final Verdict
    print("═" * 65)
    print("  [ Final Verdict ]")
    print("═" * 65)
    print()

    if p_value < 0.05 and ratio_golden > GOLDEN_EXPECTED * 1.5:
        verdict = "Structural Discovery"
        detail = (
            f"Golden Zone optimal I ratio ({ratio_golden*100:.1f}%) "
            f"significantly exceeds random expected ({GOLDEN_EXPECTED*100:.1f}%).\n"
            f"  The Lorenz system itself tends to maximize CCT in Golden Zone regardless of mapping formula."
        )
    elif p_value < 0.05:
        verdict = "Weak Structural Discovery"
        detail = (
            f"Statistically significant (p={p_value:.4f}) but small effect size.\n"
            f"  Golden Zone effect exists but is highly mapping-dependent."
        )
    elif ratio_golden > GOLDEN_EXPECTED * 1.2:
        verdict = "Judgment Reserved"
        detail = (
            f"Golden Zone ratio ({ratio_golden*100:.1f}%) is slightly higher than expected "
            f"but not statistically significant (p={p_value:.4f}).\n"
            f"  Re-verification needed with more mappings (n > 5000)."
        )
    else:
        verdict = "Product of Mapping"
        detail = (
            f"Golden Zone optimal I ratio ({ratio_golden*100:.1f}%) is "
            f"similar to random expected ({GOLDEN_EXPECTED*100:.1f}%).\n"
            f"  'Maximum CCT in Golden Zone' is likely a product of mapping formula design."
        )

    print(f"  Verdict: {verdict}")
    print(f"  Basis: {detail}")
    print()

    # Additional verdict for mappings without gap
    if np.sum(~all_has_gap) > 10:
        no_gap_best = all_best_i[~all_has_gap]
        ng_in_golden = np.sum((no_gap_best >= GOLDEN_LOWER) & (no_gap_best <= GOLDEN_UPPER))
        ng_ratio = ng_in_golden / len(no_gap_best)
        ng_p = binomial_test(int(ng_in_golden), len(no_gap_best), GOLDEN_EXPECTED)
        print(f"  Addition: Golden Zone effect {'exists' if ng_p < 0.05 else 'absent'} even in mappings without gap"
              f" (ratio={ng_ratio*100:.1f}%, p={ng_p:.4f})")
        if ng_p < 0.05:
            print(f"  → Golden Zone effect exists without gap mechanism = Stronger evidence")
        print()

    print("═" * 65)
    print()


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Mapping Independence Verification: Verify if Golden Zone CCT optimization is a product of mapping or a structural discovery",
    )
    parser.add_argument("--n-mappings", type=int, default=1000,
                        help="Number of random mappings (default 1000)")
    parser.add_argument("--grid", type=int, default=20,
                        help="I scan resolution (default 20)")
    parser.add_argument("--steps", type=int, default=10000,
                        help="Lorenz simulation step count (default 10000, speed priority)")
    parser.add_argument("--dt", type=float, default=0.01,
                        help="Time interval (default 0.01)")
    parser.add_argument("--quick", action="store_true",
                        help="Quick run (100 mappings, grid=10)")
    parser.add_argument("--seed", type=int, default=12345,
                        help="Random seed (default 12345)")

    args = parser.parse_args()

    if args.quick:
        args.n_mappings = 100
        args.grid = 10

    print()
    print("═" * 65)
    print("  Starting Mapping Independence Verification")
    print("═" * 65)
    print()

    all_best_i, all_has_gap, all_mapping_type = run_experiment(
        n_mappings=args.n_mappings,
        grid=args.grid,
        steps=args.steps,
        dt=args.dt,
        seed=args.seed,
    )

    analyze_and_report(all_best_i, all_has_gap, all_mapping_type)


if __name__ == "__main__":
    main()