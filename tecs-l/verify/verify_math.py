#!/usr/bin/env python3
"""Verification of unverified mathematical hypotheses"""

import numpy as np
from scipy import stats, integrate
from scipy.special import beta as beta_func
import os
from datetime import datetime

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def verify_one_third_law():
    """Hypothesis A: Analytical verification of the 1/3 law"""
    print("═" * 60)
    print("  Hypothesis A: Analytical verification of the 1/3 law")
    print("═" * 60)

    # Population statistics (based on Beta distribution)
    samples = [10000, 50000, 200000, 1000000]
    results = []

    for n in samples:
        rng = np.random.default_rng(42)
        d = rng.beta(2, 5, n).clip(0.01, 0.99)
        p = rng.beta(5, 2, n).clip(0.01, 0.99)
        i = rng.beta(5, 2, n).clip(0.05, 0.99)
        g = d * p / i
        mu, sigma = g.mean(), g.std()
        threshold = mu + 2 * sigma

        # Calculate ratio on uniform grid
        grid = 100
        ds = np.linspace(0.01, 0.99, grid)
        ps = np.linspace(0.01, 0.99, grid)
        ii = np.linspace(0.05, 0.99, grid)
        D, P, I = np.meshgrid(ds, ps, ii, indexing='ij')
        G = D * P / I
        ratio = (G > threshold).sum() / G.size

        results.append({'n': n, 'mu': mu, 'sigma': sigma, 'threshold': threshold, 'ratio': ratio})
        print(f"  n={n:>10,}: μ={mu:.4f}, σ={sigma:.4f}, threshold={threshold:.4f}, ratio={ratio:.4f} ({ratio*100:.2f}%)")

    # Convergence analysis
    ratios = [r['ratio'] for r in results]
    print(f"\n  Convergence value: {ratios[-1]:.6f}")
    print(f"  1/3            : {1/3:.6f}")
    print(f"  Error          : {abs(ratios[-1] - 1/3):.6f} ({abs(ratios[-1] - 1/3)/( 1/3)*100:.2f}%)")

    is_one_third = abs(ratios[-1] - 1/3) < 0.01
    print(f"\n  Verdict: {'✅ Approximates 1/3' if is_one_third else '❌ Not 1/3'} (error {abs(ratios[-1]-1/3)*100:.2f}%)")
    return ratios[-1]


def verify_z_max():
    """Hypothesis B: Z-Score upper bound convergence value"""
    print("\n" + "═" * 60)
    print("  Hypothesis B: Z-Score upper bound convergence value")
    print("═" * 60)

    samples_list = [10000, 50000, 200000, 1000000]
    z_maxes = []

    for n in samples_list:
        rng = np.random.default_rng(42)
        d = rng.beta(2, 5, n).clip(0.01, 0.99)
        p = rng.beta(5, 2, n).clip(0.01, 0.99)
        i = rng.beta(5, 2, n).clip(0.05, 0.99)
        g = d * p / i
        mu, sigma = g.mean(), g.std()

        # Theoretical maximum: D=0.99, P=0.99, I=0.05
        g_max = 0.99 * 0.99 / 0.05
        z_max = (g_max - mu) / sigma
        z_maxes.append(z_max)
        print(f"  n={n:>10,}: G_max={g_max:.2f}, Z_max={z_max:.2f}σ")

    print(f"\n  Theoretical G_max = 0.99×0.99/0.05 = {0.99*0.99/0.05:.2f}")
    print(f"  Z_max convergence value ≈ {z_maxes[-1]:.2f}σ")
    print(f"  Difference from 80σ: {abs(z_maxes[-1] - 80):.2f}")
    print(f"  = G_max/σ ≈ {0.99*0.99/0.05:.2f}/σ")
    return z_maxes[-1]


def verify_entropy_ln3():
    """Hypothesis C: Entropy = ln(3) invariant"""
    print("\n" + "═" * 60)
    print("  Hypothesis C: Entropy = ln(3) invariant")
    print("═" * 60)

    ln3 = np.log(3)
    print(f"  ln(3) = {ln3:.6f}\n")

    test_params = [
        (0.3, 0.5, 0.7),
        (0.7, 0.8, 0.15),
        (0.5, 0.6, 0.36),
        (0.9, 0.95, 0.05),
        (0.1, 0.1, 0.9),
        (0.5, 0.5, 0.5),
        (0.8, 0.9, 0.30),
        (0.2, 0.3, 0.8),
    ]

    entropies = []
    print(f"  {'D':>5} {'P':>5} {'I':>5} │ {'Entropy':>8} │ {'Diff from ln(3)':>12} │ {'Match?':>5}")
    print(f"  {'─'*5} {'─'*5} {'─'*5}─┼─{'─'*8}─┼─{'─'*12}─┼─{'─'*5}")

    for d, p, i in test_params:
        T = 1.0 / max(i, 0.01)
        E_normal = 0.0
        E_genius = -(d * p)
        E_decline = d * (1 - p)
        energies = np.array([E_normal, E_genius, E_decline])
        exp_terms = np.exp(-energies / T)
        Z = exp_terms.sum()
        probs = exp_terms / Z
        entropy = -np.sum(probs * np.log(probs + 1e-10))
        entropies.append(entropy)
        diff = abs(entropy - ln3)
        match = "✅" if diff < 0.01 else "❌"
        print(f"  {d:>5.2f} {p:>5.2f} {i:>5.2f} │ {entropy:>8.6f} │ {diff:>12.6f} │ {match:>5}")

    mean_s = np.mean(entropies)
    std_s = np.std(entropies)
    print(f"\n  Mean entropy: {mean_s:.6f} ± {std_s:.6f}")
    print(f"  ln(3)       : {ln3:.6f}")
    print(f"  Mean error  : {abs(mean_s - ln3):.6f}")

    # Large-scale verification: 1000 random parameters
    rng = np.random.default_rng(42)
    ds = rng.uniform(0.01, 0.99, 10000)
    ps = rng.uniform(0.01, 0.99, 10000)
    ii = rng.uniform(0.01, 0.99, 10000)

    all_entropies = []
    for d, p, i in zip(ds, ps, ii):
        T = 1.0 / max(i, 0.01)
        energies = np.array([0.0, -(d*p), d*(1-p)])
        exp_terms = np.exp(-energies / T)
        Z = exp_terms.sum()
        probs = exp_terms / Z
        s = -np.sum(probs * np.log(probs + 1e-10))
        all_entropies.append(s)

    all_entropies = np.array(all_entropies)
    print(f"\n  Large-scale verification (10,000 random parameters):")
    print(f"    Mean: {all_entropies.mean():.6f}")
    print(f"    Std Dev: {all_entropies.std():.6f}")
    print(f"    Min/Max: {all_entropies.min():.6f} / {all_entropies.max():.6f}")
    print(f"    Error from ln(3): {abs(all_entropies.mean() - ln3):.6f}")

    is_ln3 = abs(all_entropies.mean() - ln3) < 0.01
    is_invariant = all_entropies.std() < 0.05
    print(f"\n  Verdict:")
    print(f"    ln(3) approximation: {'✅' if is_ln3 else '❌'}")
    print(f"    Invariant:          {'✅ (σ < 0.05)' if is_invariant else '❌ Has variation (σ=' + f'{all_entropies.std():.4f})'}")
    return all_entropies.mean(), all_entropies.std()


def verify_diffusion():
    """Hypothesis D: Convergence speed ∝ (ΔI)² — Diffusion equation"""
    print("\n" + "═" * 60)
    print("  Hypothesis D: Convergence speed ∝ (ΔI)² diffusion law")
    print("═" * 60)

    # Measured data
    data = [
        ('Golden MoE', 0.008, 3),
        ('GPT-4', 0.132, 8),
        ('Mixtral', 0.507, 21),
        ('GPT-2', 0.507, 39),
    ]

    print(f"\n  {'Model':12} │ {'ΔI':>6} │ {'ΔI²':>8} │ {'τ(measured)':>7} │ {'τ∝ΔI²':>7} │ {'τ∝ΔI':>6}")
    print(f"  {'─'*12}─┼─{'─'*6}─┼─{'─'*8}─┼─{'─'*7}─┼─{'─'*7}─┼─{'─'*6}")

    # ΔI² model fitting (based on Golden MoE)
    base_di2 = data[0][1]**2
    base_tau = data[0][2]
    k_di2 = base_tau / max(base_di2, 1e-6)

    base_di = data[0][1]
    k_di = base_tau / max(base_di, 1e-6)

    errors_sq = []
    errors_lin = []

    for name, di, tau in data:
        tau_sq = k_di2 * di**2
        tau_lin = k_di * di
        err_sq = abs(tau - tau_sq) / tau * 100
        err_lin = abs(tau - tau_lin) / tau * 100
        errors_sq.append(err_sq)
        errors_lin.append(err_lin)
        print(f"  {name:12} │ {di:>6.3f} │ {di**2:>8.5f} │ {tau:>7} │ {tau_sq:>7.1f} │ {tau_lin:>6.1f}")

    print(f"\n  Average error:")
    print(f"    τ ∝ ΔI² (diffusion): {np.mean(errors_sq):.1f}%")
    print(f"    τ ∝ ΔI  (linear): {np.mean(errors_lin):.1f}%")

    # R² calculation
    dis = np.array([d[1] for d in data])
    taus = np.array([d[2] for d in data])

    # ΔI² model
    slope_sq, intercept_sq, r_sq, _, _ = stats.linregress(dis**2, taus)
    # ΔI model
    slope_lin, intercept_lin, r_lin, _, _ = stats.linregress(dis, taus)

    print(f"\n  R² (coefficient of determination):")
    print(f"    τ vs ΔI² : R² = {r_sq**2:.4f}")
    print(f"    τ vs ΔI  : R² = {r_lin**2:.4f}")

    better = "Diffusion (ΔI²)" if r_sq**2 > r_lin**2 else "Linear (ΔI)"
    print(f"\n  Verdict: {better} model is more suitable (R²={max(r_sq**2, r_lin**2):.4f})")
    return r_sq**2, r_lin**2


def verify_golden_width():
    """Hypothesis E: Golden Zone width = exactly 1/4"""
    print("\n" + "═" * 60)
    print("  Hypothesis E: Golden Zone width = 1/4, upper/lower = 2")
    print("═" * 60)

    # Measure Golden Zone boundaries at various grid resolutions
    grids = [20, 30, 50, 80]
    results = []

    for grid in grids:
        n_samples = 50000
        rng = np.random.default_rng(42)
        pop_d = rng.beta(2, 5, n_samples).clip(0.01, 0.99)
        pop_p = rng.beta(5, 2, n_samples).clip(0.01, 0.99)
        pop_i = rng.beta(5, 2, n_samples).clip(0.05, 0.99)
        pop_g = pop_d * pop_p / pop_i
        pop_mean, pop_std = pop_g.mean(), pop_g.std()

        deficits = np.linspace(0.05, 0.95, grid)
        plasticities = np.linspace(0.1, 0.95, grid)
        inhibitions = np.linspace(0.05, 0.95, grid)

        # Measure I range of triple consensus region
        triple_is = []
        for di in deficits:
            for pi in plasticities:
                for ii in inhibitions:
                    g = di * pi / ii
                    z = (g - pop_mean) / pop_std

                    # Triple consensus conditions (simplified)
                    a = 2 * di - 1
                    b = 1 - 2 * ii
                    cusp_dist = abs(8*a**3 + 27*b**2) / 35
                    m1 = abs(z) > 2.0
                    m2 = cusp_dist < 0.2 and b > 0
                    T = 1.0 / max(ii, 0.01)
                    energies = np.array([0.0, -(di*pi), di*(1-pi)])
                    exp_terms = np.exp(-energies / T)
                    Z_part = exp_terms.sum()
                    probs = exp_terms / Z_part
                    m3 = probs[1] > probs[0] and probs[1] > probs[2]

                    if m1 and m2 and m3:
                        triple_is.append(ii)

        if triple_is:
            i_min = min(triple_is)
            i_max = max(triple_is)
            width = i_max - i_min
            ratio = i_max / i_min if i_min > 0 else float('inf')
            results.append({'grid': grid, 'i_min': i_min, 'i_max': i_max, 'width': width, 'ratio': ratio})
            print(f"  grid={grid:>3}: I=[{i_min:.4f}, {i_max:.4f}], width={width:.4f}, upper/lower={ratio:.4f}")

    if results:
        avg_width = np.mean([r['width'] for r in results])
        avg_ratio = np.mean([r['ratio'] for r in results])
        print(f"\n  Average width: {avg_width:.4f}")
        print(f"  1/4         : {0.25:.4f}")
        print(f"  Error       : {abs(avg_width - 0.25):.4f}")
        print(f"\n  Average upper/lower ratio: {avg_ratio:.4f}")
        print(f"  Difference from 2.0      : {abs(avg_ratio - 2.0):.4f}")

        is_quarter = abs(avg_width - 0.25) < 0.03
        is_double = abs(avg_ratio - 2.0) < 0.3
        print(f"\n  Verdict:")
        print(f"    Width = 1/4: {'✅' if is_quarter else '❌'} (error {abs(avg_width-0.25):.4f})")
        print(f"    Ratio = 2  : {'✅' if is_double else '❌'} (error {abs(avg_ratio-2.0):.4f})")
    return results


def verify_genius_distribution():
    """Hypothesis G: Genius Score distribution identification"""
    print("\n" + "═" * 60)
    print("  Hypothesis G: Genius Score distribution identification")
    print("═" * 60)

    n = 1000000
    rng = np.random.default_rng(42)
    d = rng.beta(2, 5, n).clip(0.01, 0.99)
    p = rng.beta(5, 2, n).clip(0.01, 0.99)
    i = rng.beta(5, 2, n).clip(0.05, 0.99)
    g = d * p / i

    print(f"\n  G = D×P/I distribution (n={n:,})")
    print(f"  Mean: {g.mean():.4f}")
    print(f"  Std Dev: {g.std():.4f}")
    print(f"  Skewness: {stats.skew(g):.4f}")
    print(f"  Kurtosis: {stats.kurtosis(g):.4f}")
    print(f"  Min/Max: {g.min():.4f} / {g.max():.4f}")

    # Distribution fitting tests
    distributions = {
        'lognormal': stats.lognorm,
        'gamma': stats.gamma,
        'beta_prime': stats.betaprime,
        'f': stats.f,
        'invgamma': stats.invgamma,
    }

    print(f"\n  Distribution fitting (KS test):")
    print(f"  {'Distribution':15} │ {'KS statistic':>10} │ {'p-value':>10} │ Verdict")
    print(f"  {'─'*15}─┼─{'─'*10}─┼─{'─'*10}─┼─{'─'*10}")

    best_name = ""
    best_pval = 0
    g_sample = rng.choice(g, 5000, replace=False)  # Subsample for KS test

    for name, dist in distributions.items():
        try:
            params = dist.fit(g_sample)
            ks_stat, p_val = stats.kstest(g_sample, dist.cdf, args=params)
            match = "✅" if p_val > 0.05 else "❌"
            print(f"  {name:15} │ {ks_stat:>10.4f} │ {p_val:>10.6f} │ {match}")
            if p_val > best_pval:
                best_pval = p_val
                best_name = name
        except Exception as e:
            print(f"  {name:15} │ {'Failed':>10} │ {'─':>10} │ {str(e)[:20]}")

    print(f"\n  Best distribution: {best_name} (p={best_pval:.6f})")

    # ASCII histogram
    print(f"\n  Distribution shape:")
    hist, edges = np.histogram(g, bins=40, range=(0, 3))
    max_h = hist.max()
    for i in range(len(hist)):
        bar = "█" * int(hist[i] / max_h * 40)
        print(f"  {edges[i]:>5.2f} │{bar}")

    return best_name, best_pval


def main():
    print()
    print("▓" * 60)
    print("  Batch verification of mathematical unverified hypotheses")
    print("▓" * 60)

    results = {}

    results['A'] = verify_one_third_law()
    results['B'] = verify_z_max()
    results['C'] = verify_entropy_ln3()
    results['D'] = verify_diffusion()
    results['E'] = verify_golden_width()
    results['G'] = verify_genius_distribution()

    # Summary
    print("\n" + "▓" * 60)
    print("  Summary verdict")
    print("▓" * 60)

    print(f"""
  A. 1/3 law        : ratio = {results['A']:.4f} ({'✅ Approximate' if abs(results['A']-1/3)<0.01 else '❌'})
  B. Z_max convergence: {results['B']:.2f}σ
  C. Entropy = ln(3): mean = {results['C'][0]:.4f}, σ = {results['C'][1]:.4f} ({'✅' if results['C'][1]<0.05 else '❌ Variable'})
  D. Diffusion law  : R²(ΔI²) = {results['D'][0]:.4f}, R²(ΔI) = {results['D'][1]:.4f}
  E. Width = 1/4    : Measuring
  G. Genius dist    : {results['G'][0]} (p={results['G'][1]:.6f})
""")

    # Save report
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "math_verification.md"), 'w', encoding='utf-8') as f:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"# Mathematical Unverified Hypothesis Verification Results [{now}]\n\n")
        f.write(f"| Hypothesis | Result |\n|---|---|\n")
        f.write(f"| A. 1/3 law | {results['A']:.4f} |\n")
        f.write(f"| B. Z_max | {results['B']:.2f}σ |\n")
        f.write(f"| C. Entropy | {results['C'][0]:.4f} ± {results['C'][1]:.4f} |\n")
        f.write(f"| D. Diffusion R² | ΔI²={results['D'][0]:.4f}, ΔI={results['D'][1]:.4f} |\n")
        f.write(f"| G. Distribution | {results['G'][0]} |\n")

    print(f"  📁 Verification results → results/math_verification.md")
    print()


if __name__ == '__main__':
    main()