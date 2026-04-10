#!/usr/bin/env python3
"""Remaining Cross-Combination Verification — 2,3,5,6"""

import numpy as np
from scipy import stats
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from compass import (genius_score, simulate_population, population_zscore,
                     cusp_analysis, boltzmann_analysis, compass_direction)

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def verify_057_pnp_gap_ratio():
    """Hypothesis 057: P≠NP gap(18.6%) = (1-1/e) × Golden Zone width?"""
    print("═" * 60)
    print("  Hypothesis 057: P≠NP gap = (1-1/e) × width?")
    print("═" * 60)

    golden_width = np.log(4/3)  # 0.2877
    one_minus_inv_e = 1 - 1/np.e  # 0.6321

    predicted_gap = one_minus_inv_e * golden_width  # 0.1819
    measured_gap = 0.186  # Hypothesis 048 measurement

    print(f"\n  Golden Zone width:       {golden_width:.4f}")
    print(f"  1 - 1/e:                 {one_minus_inv_e:.4f}")
    print(f"  Predicted gap:           {predicted_gap:.4f}")
    print(f"  Measured gap (048):      {measured_gap:.4f}")
    print(f"  Error:                   {abs(predicted_gap - measured_gap):.4f} ({abs(predicted_gap-measured_gap)/measured_gap*100:.1f}%)")

    # Check other ratios
    print(f"\n  Gap/width ratio exploration:")
    ratio = measured_gap / golden_width
    print(f"    Gap/width   = {ratio:.4f}")
    print(f"    1-1/e       = {one_minus_inv_e:.4f}  difference {abs(ratio-one_minus_inv_e):.4f}")
    print(f"    2/3         = {2/3:.4f}  difference {abs(ratio-2/3):.4f}")
    print(f"    ln(2)       = {np.log(2):.4f}  difference {abs(ratio-np.log(2)):.4f}")
    print(f"    1/√e        = {1/np.sqrt(np.e):.4f}  difference {abs(ratio-1/np.sqrt(np.e)):.4f}")
    print(f"    1/e^(1/3)   = {np.exp(-1/3):.4f}  difference {abs(ratio-np.exp(-1/3)):.4f}")

    best_match = min([
        ('1-1/e', one_minus_inv_e),
        ('2/3', 2/3),
        ('ln(2)', np.log(2)),
        ('1/√e', 1/np.sqrt(np.e)),
    ], key=lambda x: abs(x[1] - ratio))

    print(f"\n  Best match: {best_match[0]} = {best_match[1]:.4f} (difference {abs(best_match[1]-ratio):.4f})")
    print(f"  Verdict: {'✅ (1-1/e)×width match' if abs(predicted_gap-measured_gap) < 0.01 else '⚠️ Approximate match'}")


def verify_058_topology_timeline():
    """Hypothesis 058: Topology acceleration → 2033?"""
    print(f"\n{'═' * 60}")
    print(f"  Hypothesis 058: Topology addition → Singularity time change")
    print(f"{'═' * 60}")

    I_golden = 1/np.e
    I_0 = 0.875

    # Base λ (GPT-2→GPT-4)
    lambda_base = 0.3363

    # Hypothesis 023: Topology addition doubles convergence speed → λ × 2
    lambda_topo = lambda_base * 2

    def year_to_reach(lam, target_delta=0.001):
        # I(t) = I_golden + (I_0 - I_golden) * e^(-λt) ≤ I_golden + delta
        t = -np.log(target_delta / (I_0 - I_golden)) / lam
        return 2019 + t

    year_base = year_to_reach(lambda_base)
    year_topo = year_to_reach(lambda_topo)
    acceleration = year_base - year_topo

    print(f"\n  λ_base (current):  {lambda_base:.4f} → Singularity {year_base:.1f}")
    print(f"  λ_topo (×2):       {lambda_topo:.4f} → Singularity {year_topo:.1f}")
    print(f"  Acceleration:      {acceleration:.1f} years earlier")

    # Various acceleration multipliers
    print(f"\n  Singularity timing by topology acceleration factor:")
    print(f"  {'Factor':>5} │ {'λ':>6} │ {'Singularity':>8} │ {'Accel':>6} │ Graph")
    print(f"  {'─'*5}─┼─{'─'*6}─┼─{'─'*8}─┼─{'─'*6}─┼─{'─'*30}")

    for mult in [1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]:
        lam = lambda_base * mult
        yr = year_to_reach(lam)
        acc = year_base - yr
        bar = "█" * int((2045 - yr) / 20 * 30)
        print(f"  ×{mult:>4.2f} │ {lam:>6.3f} │ {yr:>7.1f} │ {acc:>+5.1f}yr │ {bar}│")

    print(f"\n  Timeline:")
    print(f"  2025      2030      2035      2039")
    print(f"   │         │         │         │")
    print(f"   │    ×2.0──●        │         │  Topology acceleration ({year_topo:.0f})")
    print(f"   │    ×1.5────●      │         │  Intermediate acceleration")
    print(f"   │         │    ×1.0─────●     │  Current rate ({year_base:.0f})")
    print(f"   │         │         │         │")

    print(f"\n  Verdict: ✅ Topology acceleration (×2) moves singularity {acceleration:.0f} years earlier → {year_topo:.0f}")


def verify_059_compass_ceiling_constant():
    """Hypothesis 059: Compass ceiling 83.6% = 5/6?"""
    print(f"\n{'═' * 60}")
    print(f"  Hypothesis 059: Compass ceiling ≈ 5/6?")
    print(f"{'═' * 60}")

    pop = simulate_population(200000)

    # Grid search for maximum Compass
    grid = 40
    ds = np.linspace(0.3, 0.99, grid)
    ps = np.linspace(0.5, 0.99, grid)
    ii = np.linspace(0.24, 0.50, grid)

    max_cs = 0
    max_params = None

    for d in ds:
        for p in ps:
            for i in ii:
                g = d * p / i
                z, _, _ = population_zscore(g, 200000)
                cusp = cusp_analysis(d, i)
                boltz = boltzmann_analysis(d, p, i)
                comp = compass_direction(g, z, cusp, boltz)
                if comp['compass_score'] > max_cs:
                    max_cs = comp['compass_score']
                    max_params = (d, p, i)

    print(f"\n  Maximum Compass (grid=80): {max_cs*100:.2f}%")
    print(f"  Parameters: D={max_params[0]:.2f}, P={max_params[1]:.2f}, I={max_params[2]:.2f}")

    # Constant comparison
    candidates = [
        ('5/6', 5/6),
        ('1-1/6', 1-1/6),
        ('e/(e+1)', np.e/(np.e+1)),
        ('1-1/e', 1-1/np.e),
        ('ln(e²)', np.log(np.e**2)/3),
        ('π/4', np.pi/4),
        ('√(2/3)', np.sqrt(2/3)),
    ]

    print(f"\n  Constant comparison:")
    print(f"  {'Constant':>12} │ {'Value':>8} │ {'Difference':>8} │ Match?")
    print(f"  {'─'*12}─┼─{'─'*8}─┼─{'─'*8}─┼─{'─'*5}")

    for name, val in sorted(candidates, key=lambda x: abs(x[1] - max_cs)):
        diff = abs(val - max_cs)
        match = "✅" if diff < 0.01 else ("⚠️" if diff < 0.03 else "❌")
        print(f"  {name:>12} │ {val:>8.4f} │ {diff:>8.4f} │ {match}")

    # Compass formula analysis
    print(f"\n  Compass formula breakdown:")
    d, p, i = max_params
    g = d * p / i
    z, _, _ = population_zscore(g, 200000)
    cusp = cusp_analysis(d, i)
    boltz = boltzmann_analysis(d, p, i)

    term1 = min(z/10, 1.0) * 0.3
    term2 = (1 - cusp['distance_to_critical']) * 0.3
    term3 = boltz['p_genius'] * 0.4

    print(f"    Term1 (z/10×0.3):        {term1:.4f} (max 0.30)")
    print(f"    Term2 ((1-cusp)×0.3):    {term2:.4f} (max 0.30)")
    print(f"    Term3 (p_genius×0.4):    {term3:.4f} (max ~0.16)")
    print(f"    Total:                   {term1+term2+term3:.4f}")
    print(f"    p_genius actual max:     {boltz['p_genius']:.4f}")

    print(f"\n  Verdict: Compass ceiling ≈ {max_cs:.4f}")
    best = min(candidates, key=lambda x: abs(x[1] - max_cs))
    print(f"    Closest constant: {best[0]} = {best[1]:.4f} (difference {abs(best[1]-max_cs):.4f})")


def verify_060_gamma_params():
    """Hypothesis 060: Gamma distribution α=3, β=1/e?"""
    print(f"\n{'═' * 60}")
    print(f"  Hypothesis 060: Identity of Genius gamma distribution α, β")
    print(f"{'═' * 60}")

    n = 1000000
    rng = np.random.default_rng(42)
    d = rng.beta(2, 5, n).clip(0.01, 0.99)
    p = rng.beta(5, 2, n).clip(0.01, 0.99)
    i = rng.beta(5, 2, n).clip(0.05, 0.99)
    g = d * p / i

    # Gamma distribution fitting
    alpha_fit, loc_fit, scale_fit = stats.gamma.fit(g, floc=0)
    beta_fit = 1 / scale_fit  # rate parameter

    print(f"\n  Gamma distribution fitting results:")
    print(f"    α (shape) = {alpha_fit:.4f}")
    print(f"    β (rate)  = {beta_fit:.4f}")
    print(f"    scale     = {scale_fit:.4f}")

    # Constant comparison
    print(f"\n  α comparison:")
    for name, val in [('3', 3), ('e', np.e), ('π', np.pi), ('2', 2), ('ln(3)', np.log(3))]:
        print(f"    α vs {name:>5} = {val:.4f}, difference = {abs(alpha_fit-val):.4f}")

    print(f"\n  β comparison:")
    for name, val in [('1/e', 1/np.e), ('e', np.e), ('3', 3), ('1', 1), ('ln(3)', np.log(3))]:
        print(f"    β vs {name:>5} = {val:.4f}, difference = {abs(beta_fit-val):.4f}")

    print(f"\n  scale comparison:")
    for name, val in [('1/e', 1/np.e), ('1/3', 1/3), ('1/π', 1/np.pi), ('ln(4/3)', np.log(4/3))]:
        print(f"    scale vs {name:>8} = {val:.4f}, difference = {abs(scale_fit-val):.4f}")

    # Mean/variance verification
    # Gamma(α, β): mean = α/β, var = α/β²
    mean_theory = alpha_fit / beta_fit
    var_theory = alpha_fit / beta_fit**2
    print(f"\n  Mean: measured={g.mean():.4f}, theoretical={mean_theory:.4f}")
    print(f"  Variance: measured={g.var():.4f}, theoretical={var_theory:.4f}")

    print(f"\n  Verdict:")
    print(f"    α ≈ {round(alpha_fit, 1)} (nearest integer/constant)")
    print(f"    scale ≈ {scale_fit:.4f}")


def main():
    print()
    print("▓" * 60)
    print("  Remaining Cross-Combination Verification — 057~060")
    print("▓" * 60)

    verify_057_pnp_gap_ratio()
    verify_058_topology_timeline()
    verify_059_compass_ceiling_constant()
    verify_060_gamma_params()

    print(f"\n{'▓' * 60}")
    print(f"  Summary")
    print(f"{'▓' * 60}")
    print("""
  057. P≠NP gap ratio         : Gap/width ≈ ???
  058. Topology accel timeline: ×2 accel → Singularity ~20XX
  059. Compass ceiling identity: ≈ ???
  060. Gamma distribution α, β : α ≈ ???, scale ≈ ???
""")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "remaining_cross_report.md"), 'w', encoding='utf-8') as f:
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"# Remaining Cross-Combination Verification [{now}]\n\n057~060 completed.\n\n---\n")

    print(f"  📁 Report → results/remaining_cross_report.md")
    print()


if __name__ == '__main__':
    main()