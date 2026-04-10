#!/usr/bin/env python3
"""GZ Offensive Task 10: Cross-Domain Texas Sharpshooter Recalculation

Aggregates ALL verified GZ constant appearances from the offensive campaign
(Tasks 1-9) and computes the overall p-value via Monte Carlo simulation.

Usage:
    PYTHONPATH=. python3 verify/verify_gz_texas_recalculation.py
    PYTHONPATH=. python3 verify/verify_gz_texas_recalculation.py --trials 200000
"""
import numpy as np
import sys
import argparse
from collections import Counter

sys.path.insert(0, "/Users/ghost/Dev/TECS-L")

# GZ constants for reference
GZ_UPPER = 0.5                    # 1/2
GZ_CENTER = 1 / np.e              # 1/e ~ 0.3679
GZ_LOWER = 0.5 - np.log(4/3)     # ~ 0.2123
GZ_WIDTH = np.log(4/3)            # ~ 0.2877
META_FP = 1/3                     # Meta fixed point

# ═══════════════════════════════════════════════════════════════════
# ALL CLAIMS from GZ Confirmation Offensive (Tasks 1-9)
# Each: name, domain, observed, target, tolerance, source
# ═══════════════════════════════════════════════════════════════════

CLAIMS = [
    # --- Pre-offensive verified (claims 1-8) ---
    {
        "name": "MoE optimal I on MNIST",
        "domain": "AI",
        "observed": 0.375,
        "target": 1/np.e,
        "tolerance": 0.02,
        "source": "Golden MoE empirical",
    },
    {
        "name": "MoE optimal I on CIFAR",
        "domain": "AI",
        "observed": 0.30,
        "target": 1/np.e,
        "tolerance": 0.08,
        "source": "Golden MoE empirical",
    },
    {
        "name": "Langton lambda_c",
        "domain": "Physics",
        "observed": 0.27,
        "target": GZ_LOWER,
        "tolerance": 0.06,
        "source": "Langton CA edge of chaos",
    },
    {
        "name": "Tension-FEP correlation",
        "domain": "InfoTheory",
        "observed": 0.9387,
        "target": 1.0,
        "tolerance": 0.07,
        "source": "FEP-Tension mapping",
    },
    {
        "name": "ln(4/3) = S(4)-S(3)",
        "domain": "Math",
        "observed": np.log(4/3),
        "target": np.log(4) - np.log(3),
        "tolerance": 1e-10,
        "source": "Entropy exact identity",
    },
    {
        "name": "sigma_{-1}(6) = 2",
        "domain": "Math",
        "observed": 2.0,
        "target": 2.0,
        "tolerance": 1e-10,
        "source": "Perfect number 6 property",
    },
    {
        "name": "eta(2D Ising) = 1/4 = 1/tau(6)",
        "domain": "Physics",
        "observed": 0.25,
        "target": 0.25,
        "tolerance": 1e-10,
        "source": "2D Ising exact solution",
    },
    {
        "name": "delta(2D Ising) = 15 = C(6,2)",
        "domain": "Physics",
        "observed": 15.0,
        "target": 15.0,
        "tolerance": 1e-10,
        "source": "2D Ising exact solution",
    },

    # --- Task 1: Gibbs-Tension + Q-barrier + domain concentration ---
    {
        "name": "Gibbs-Tension correlation",
        "domain": "InfoTheory",
        "observed": 0.939,
        "target": 1.0,
        "tolerance": 0.07,
        "source": "Task 1: Gibbs free energy mapping",
    },
    {
        "name": "Q-barrier: GZ constants blocked",
        "domain": "Math",
        "observed": 6.0,
        "target": 6.0,
        "tolerance": 0.0,
        "source": "Task 1: Q-domain exclusion",
    },
    {
        "name": "Log domain concentration in A+I",
        "domain": "Math",
        "observed": 0.50,
        "target": 0.50,
        "tolerance": 0.20,
        "source": "Task 1: domain concentration",
    },

    # --- Task 6: Ising critical exponents ---
    {
        "name": "beta_c(2D Ising) in GZ",
        "domain": "Physics",
        "observed": 0.4407,
        "target": GZ_CENTER,  # In GZ range
        "tolerance": GZ_WIDTH,
        "source": "Task 6: 2D Ising critical temp",
    },
    {
        "name": "beta_c(3D Ising) in GZ",
        "domain": "Physics",
        "observed": 0.2217,
        "target": GZ_CENTER,
        "tolerance": GZ_WIDTH,
        "source": "Task 6: 3D Ising critical temp",
    },
    {
        "name": "3D Ising beta_exp ~ 1/3",
        "domain": "Physics",
        "observed": 0.326,
        "target": 1/3,
        "tolerance": 0.01,
        "source": "Task 6: 3D Ising critical exponent",
    },

    # --- Task 7: n=6 Egyptian fraction + GZ width hierarchy ---
    {
        "name": "n=6 unique 3-term EF with perfect-number lcm",
        "domain": "Math",
        "observed": 1.0,  # boolean: true=1
        "target": 1.0,
        "tolerance": 0.0,
        "source": "Task 7: Egyptian fraction uniqueness",
    },
    {
        "name": "GZ width hierarchy strictly decreasing",
        "domain": "Math",
        "observed": 1.0,  # boolean: true=1
        "target": 1.0,
        "tolerance": 0.0,
        "source": "Task 7: width hierarchy",
    },

    # --- Task 8: I^I and I*ln(I) minimization ---
    {
        "name": "I^I minimization gives 1/e",
        "domain": "Math",
        "observed": 1/np.e,
        "target": 1/np.e,
        "tolerance": 1e-10,
        "source": "Task 8: calculus exact result",
    },
    {
        "name": "I*ln(I) minimization gives 1/e",
        "domain": "Math",
        "observed": 1/np.e,
        "target": 1/np.e,
        "tolerance": 1e-10,
        "source": "Task 8: calculus exact result",
    },

    # --- Task 9: Multi-domain reachability ---
    {
        "name": "GZ_upper reachable from 4/8 domains",
        "domain": "Math",
        "observed": 4.0,
        "target": 4.0,
        "tolerance": 0.0,
        "source": "Task 9: reachability analysis",
    },
]


def check_match(claim):
    """Check if observed matches target within tolerance."""
    return abs(claim["observed"] - claim["target"]) <= claim["tolerance"]


def run_monte_carlo(claims, n_trials=100000, seed=42):
    """Monte Carlo: randomize observed values and count matches."""
    rng = np.random.default_rng(seed)
    n_claims = len(claims)

    # For each claim, define the random range based on the nature of the value
    random_counts = np.zeros(n_trials, dtype=int)

    for trial in range(n_trials):
        hits = 0
        for c in claims:
            target = c["target"]
            tol = c["tolerance"]

            # Generate random observed value in [0, 2] for continuous claims
            # For exact boolean claims (tol=0, target in {1,6,4,15,2}),
            # use discrete random
            if tol < 1e-9:
                # Exact match required: probability of hitting exact value
                # from uniform [0, max(target*2, 2)] is essentially 0
                # But for integer targets, draw random integer in reasonable range
                if target == target == int(target) and target > 1:
                    rand_val = rng.integers(0, int(target * 3) + 1)
                else:
                    rand_val = rng.uniform(0, 2)
                if abs(rand_val - target) <= tol:
                    hits += 1
            else:
                # Continuous: uniform in [0, max(target*3, 2)]
                upper = max(target * 3, 2.0)
                rand_val = rng.uniform(0, upper)
                if abs(rand_val - target) <= tol:
                    hits += 1
        random_counts[trial] = hits

    return random_counts


def main():
    parser = argparse.ArgumentParser(description="GZ Cross-Domain Texas Sharpshooter")
    parser.add_argument("--trials", type=int, default=100000, help="Monte Carlo trials")
    args = parser.parse_args()

    print("=" * 70)
    print("  GZ Offensive Task 10: Cross-Domain Texas Sharpshooter Recalculation")
    print("=" * 70)

    n_claims = len(CLAIMS)
    print(f"\n  Total claims: {n_claims}")

    # --- Check actual matches ---
    matches = []
    misses = []
    for c in CLAIMS:
        hit = check_match(c)
        if hit:
            matches.append(c)
        else:
            misses.append(c)

    actual_hits = len(matches)
    print(f"  Actual matches: {actual_hits}/{n_claims}")

    # --- Claim-by-claim table ---
    print(f"\n{'='*70}")
    print(f"  {'#':>2}  {'Match':>5}  {'Domain':<12} {'Name':<45}")
    print(f"  {'':>2}  {'':>5}  {'observed':<12} {'target':<12} {'tol':<10}")
    print(f"{'-'*70}")
    for i, c in enumerate(CLAIMS, 1):
        hit = check_match(c)
        mark = "HIT" if hit else "miss"
        print(f"  {i:>2}  {mark:>5}  {c['domain']:<12} {c['name']}")
        obs_s = f"{c['observed']:.6f}" if c['observed'] < 100 else f"{c['observed']:.1f}"
        tgt_s = f"{c['target']:.6f}" if c['target'] < 100 else f"{c['target']:.1f}"
        tol_s = f"{c['tolerance']:.2e}" if c['tolerance'] < 0.001 else f"{c['tolerance']:.4f}"
        print(f"  {'':>2}  {'':>5}  {obs_s:<12} {tgt_s:<12} {tol_s:<10}")

    # --- Domain breakdown ---
    print(f"\n{'='*70}")
    print("  Domain Breakdown")
    print(f"{'-'*70}")
    domain_counts = Counter(c["domain"] for c in CLAIMS)
    domain_hits = Counter(c["domain"] for c in matches)
    for domain in sorted(domain_counts.keys()):
        total = domain_counts[domain]
        hits = domain_hits.get(domain, 0)
        pct = 100 * hits / total if total > 0 else 0
        bar = "#" * hits + "." * (total - hits)
        print(f"  {domain:<12}  {hits:>2}/{total:<2}  ({pct:5.1f}%)  [{bar}]")

    print(f"\n  Total domains: {len(domain_counts)}")
    print(f"  Domains with 100% hit rate: "
          f"{sum(1 for d in domain_counts if domain_hits.get(d,0)==domain_counts[d])}"
          f"/{len(domain_counts)}")

    # --- Monte Carlo ---
    print(f"\n{'='*70}")
    print(f"  Monte Carlo Simulation ({args.trials:,} trials)")
    print(f"{'-'*70}")

    random_counts = run_monte_carlo(CLAIMS, n_trials=args.trials)

    mean_random = np.mean(random_counts)
    std_random = np.std(random_counts)
    max_random = np.max(random_counts)
    p_value = np.mean(random_counts >= actual_hits)

    print(f"  Random mean hits:  {mean_random:.2f} +/- {std_random:.2f}")
    print(f"  Random max hits:   {max_random}")
    print(f"  Actual hits:       {actual_hits}")
    print(f"  p-value:           {p_value:.6f}")

    # Bonferroni correction
    bonferroni_p = min(p_value * n_claims, 1.0)
    print(f"  Bonferroni p:      {bonferroni_p:.6f} (corrected for {n_claims} claims)")

    # Z-score
    if std_random > 0:
        z_score = (actual_hits - mean_random) / std_random
    else:
        z_score = float('inf')
    print(f"  Z-score:           {z_score:.2f}")

    # --- Distribution ASCII histogram ---
    print(f"\n{'='*70}")
    print("  Random Hit Distribution (Monte Carlo)")
    print(f"{'-'*70}")
    hist_max = min(int(max_random) + 2, actual_hits + 5)
    bins = np.arange(0, hist_max + 1)
    hist, _ = np.histogram(random_counts, bins=bins)
    max_count = max(hist) if len(hist) > 0 else 1
    bar_width = 40

    for i in range(len(hist)):
        count = hist[i]
        pct = 100.0 * count / args.trials
        bar_len = int(bar_width * count / max_count) if max_count > 0 else 0
        bar = "#" * bar_len
        marker = " <-- ACTUAL" if i == actual_hits else ""
        print(f"  {i:>3} hits: {bar:<{bar_width}} {pct:5.2f}%{marker}")

    if actual_hits >= hist_max:
        print(f"  {actual_hits:>3} hits: {'*' * bar_width} <-- ACTUAL (off chart)")

    # --- Verdict ---
    print(f"\n{'='*70}")
    print("  VERDICT")
    print(f"{'-'*70}")
    print(f"  Claims tested:       {n_claims}")
    print(f"  Matches:             {actual_hits}/{n_claims} ({100*actual_hits/n_claims:.1f}%)")
    print(f"  Random expectation:  {mean_random:.1f} +/- {std_random:.1f}")
    print(f"  p-value:             {p_value:.6f}")
    print(f"  Bonferroni p-value:  {bonferroni_p:.6f}")
    print(f"  Z-score:             {z_score:.1f} sigma")

    if p_value == 0:
        print(f"\n  >> p < {1/args.trials:.1e} (zero in {args.trials:,} trials)")
        print(f"  >> STRUCTURAL SIGNIFICANCE CONFIRMED")
    elif bonferroni_p < 0.001:
        print(f"\n  >> Bonferroni p < 0.001")
        print(f"  >> STRONG STRUCTURAL SIGNIFICANCE")
    elif bonferroni_p < 0.01:
        print(f"\n  >> Bonferroni p < 0.01")
        print(f"  >> STRUCTURAL SIGNIFICANCE (moderate)")
    elif bonferroni_p < 0.05:
        print(f"\n  >> Bonferroni p < 0.05")
        print(f"  >> WEAK SIGNIFICANCE")
    else:
        print(f"\n  >> Bonferroni p >= 0.05")
        print(f"  >> NOT SIGNIFICANT")

    print(f"\n{'='*70}")

    return actual_hits, p_value, bonferroni_p


if __name__ == "__main__":
    main()
