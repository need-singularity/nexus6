#!/usr/bin/env python3
"""H-414 Texas Sharpshooter test: Is log_3(2) ~ 1-1/e a real connection?
Also sweeps active_ratio to test info_flow convergence."""

import math
import numpy as np
import random

def texas_sharpshooter_test(target_diff, n_trials=100000):
    """Monte Carlo test: How often do two random 'nice' constants come within target_diff?"""
    # Pool of mathematically significant constants
    constants = [
        1/2, 1/3, 1/6, 1/math.e, math.log(2), math.log(3), math.log(4/3),
        math.pi/6, math.pi/4, math.pi/3, math.pi/2, math.pi,
        math.e, math.sqrt(2), math.sqrt(3), math.sqrt(5),
        (1+math.sqrt(5))/2,  # golden ratio
        math.log(2)/math.log(3),  # log_3(2)
        1 - 1/math.e,  # transition cost
        0.5772156649,  # Euler-Mascheroni
        1/math.sqrt(2*math.pi),  # Gaussian normalization
        math.e/math.pi,
        2/math.pi,  # Buffon
        math.log(math.pi),
        1/math.log(2),  # log_2(e)
        math.log(10)/math.log(2),  # log_2(10)
        0.9159655941,  # Catalan
        0.6627434193,  # twin prime
        0.26149721,  # Mertens
        1.2020569031,  # Apery zeta(3)
        2*math.pi,
        math.e**2,
        1/math.pi,
    ]

    n_constants = len(constants)
    count_close = 0

    for _ in range(n_trials):
        i, j = random.sample(range(n_constants), 2)
        c1, c2 = constants[i], constants[j]
        if c1 > 0 and c2 > 0:
            # Compare as fractions of the larger value
            rel_diff = abs(c1 - c2) / max(c1, c2)
            if rel_diff < target_diff:
                count_close += 1

    return count_close / n_trials


def info_flow_sweep():
    """Simulate info_flow = (bits/log2(3)) * (1-I) for various active ratios."""
    print(f"\n{'='*70}")
    print(f"  INFO FLOW vs ACTIVE RATIO SWEEP")
    print(f"{'='*70}")

    log2_3 = math.log2(3)
    log3_2 = 1 / log2_3
    one_minus_inv_e = 1 - 1/math.e

    print(f"\n  Target constants:")
    print(f"    log_3(2) = {log3_2:.6f}")
    print(f"    1 - 1/e  = {one_minus_inv_e:.6f}")

    # Assume effective_bits stays near 1.56 (empirically observed)
    eff_bits = 1.56
    bit_ratio = eff_bits / log2_3

    print(f"\n  Fixed: effective_bits = {eff_bits}, bit_ratio = {bit_ratio:.4f}")
    print(f"\n  {'Active%':>8} | {'I':>6} | {'InfoFlow':>10} | {'vs log3(2)':>11} | {'vs 1-1/e':>11} | {'Zone':>12}")
    print(f"  {'─'*8}─+{'─'*8}+{'─'*12}+{'─'*13}+{'─'*13}+{'─'*14}")

    best_match_log = (999, 0, 0)
    best_match_e = (999, 0, 0)

    for active_pct in range(30, 95, 5):
        ar = active_pct / 100
        I = 1 - ar
        info_flow = bit_ratio * ar

        diff_log = abs(info_flow - log3_2)
        diff_e = abs(info_flow - one_minus_inv_e)

        if 0.213 <= I <= 0.500:
            zone = "Golden Zone"
        elif I < 0.213:
            zone = "Below"
        else:
            zone = "Outside"

        marker = ""
        if diff_log < best_match_log[0]:
            best_match_log = (diff_log, active_pct, info_flow)
        if diff_e < best_match_e[0]:
            best_match_e = (diff_e, active_pct, info_flow)
        if diff_log < 0.01 or diff_e < 0.01:
            marker = " <<<"

        print(f"  {active_pct:>7}% | {I:>6.3f} | {info_flow:>10.6f} | {diff_log:>+11.6f} | {diff_e:>+11.6f} | {zone:>12}{marker}")

    print(f"\n  Best match to log_3(2): active={best_match_log[1]}%, flow={best_match_log[2]:.6f}, diff={best_match_log[0]:.6f}")
    print(f"  Best match to 1-1/e:   active={best_match_e[1]}%, flow={best_match_e[2]:.6f}, diff={best_match_e[0]:.6f}")

    # Exact solution: what active_ratio gives info_flow = log_3(2)?
    exact_ar_log = log3_2 / bit_ratio
    exact_ar_e = one_minus_inv_e / bit_ratio
    print(f"\n  Exact active_ratio for info_flow = log_3(2): {exact_ar_log*100:.2f}% (I = {1-exact_ar_log:.4f})")
    print(f"  Exact active_ratio for info_flow = 1-1/e:   {exact_ar_e*100:.2f}% (I = {1-exact_ar_e:.4f})")
    print(f"  Golden Zone: I in [0.213, 0.500]")
    in_gz_log = 0.213 <= (1-exact_ar_log) <= 0.500
    in_gz_e = 0.213 <= (1-exact_ar_e) <= 0.500
    print(f"  log_3(2) solution in Golden Zone? {'YES' if in_gz_log else 'NO'}")
    print(f"  1-1/e solution in Golden Zone?    {'YES' if in_gz_e else 'NO'}")


def constant_analysis():
    """Deep analysis of log_3(2) ~ 1-1/e relationship."""
    print(f"\n{'='*70}")
    print(f"  CONSTANT RELATIONSHIP ANALYSIS")
    print(f"{'='*70}")

    log3_2 = math.log(2) / math.log(3)
    one_minus_inv_e = 1 - 1/math.e

    diff = abs(log3_2 - one_minus_inv_e)
    rel_diff = diff / one_minus_inv_e

    print(f"\n  Primary comparison:")
    print(f"    log_3(2)        = {log3_2:.10f}")
    print(f"    1 - 1/e         = {one_minus_inv_e:.10f}")
    print(f"    Absolute diff:    {diff:.10f}")
    print(f"    Relative diff:    {rel_diff*100:.4f}%")

    # Is this known?
    print(f"\n  Algebraic exploration:")
    print(f"    log_3(2) = ln(2)/ln(3)")
    print(f"    1-1/e = (e-1)/e")
    print(f"    Ratio: log_3(2) / (1-1/e) = {log3_2/one_minus_inv_e:.10f}")
    print(f"    Diff expressed: 1-1/e - log_3(2) = {one_minus_inv_e - log3_2:.10f}")
    print(f"    = (e-1)/e - ln(2)/ln(3)")

    # Other near-misses in the TECS-L constant system
    print(f"\n  TECS-L constant proximity check:")
    tecs_constants = {
        '1/2': 0.5,
        '1/3': 1/3,
        '1/6': 1/6,
        '1/e': 1/math.e,
        'ln(4/3)': math.log(4/3),
        '1-1/e': 1-1/math.e,
        'log_3(2)': math.log(2)/math.log(3),
        'log_2(3)': math.log2(3),
        'e/pi': math.e/math.pi,
        '2/pi': 2/math.pi,
        'pi/6': math.pi/6,
        '5/6': 5/6,
        'gamma': 0.5772156649,
        'sqrt(1/2pi)': 1/math.sqrt(2*math.pi),
    }

    pairs = []
    keys = list(tecs_constants.keys())
    for i in range(len(keys)):
        for j in range(i+1, len(keys)):
            v1, v2 = tecs_constants[keys[i]], tecs_constants[keys[j]]
            if v1 > 0 and v2 > 0:
                rd = abs(v1 - v2) / max(v1, v2)
                if rd < 0.03:  # within 3%
                    pairs.append((keys[i], keys[j], v1, v2, rd))

    pairs.sort(key=lambda x: x[4])
    print(f"\n  Near-miss pairs (< 3% relative difference):")
    print(f"  {'Constant A':>12} | {'Constant B':>12} | {'Value A':>10} | {'Value B':>10} | {'Rel Diff':>8}")
    print(f"  {'─'*12}─+{'─'*12}─+{'─'*10}─+{'─'*10}─+{'─'*10}")
    for a, b, va, vb, rd in pairs:
        marker = " ***" if (a == 'log_3(2)' and b == '1-1/e') or (a == '1-1/e' and b == 'log_3(2)') else ""
        print(f"  {a:>12} | {b:>12} | {va:>10.6f} | {vb:>10.6f} | {rd*100:>7.3f}%{marker}")


def main():
    print("=" * 70)
    print("  H-414 Verification: Texas Sharpshooter + Constant Analysis")
    print("=" * 70)

    # 1. Texas Sharpshooter
    print(f"\n  Running Texas Sharpshooter Monte Carlo (100k trials)...")
    target_diff = 0.0019  # 0.19% relative difference (log_3(2) vs 1-1/e)

    random.seed(42)
    p_value = texas_sharpshooter_test(target_diff, n_trials=100000)

    print(f"\n  Texas Sharpshooter Results:")
    print(f"    Target relative difference: {target_diff*100:.2f}%")
    print(f"    Probability of random near-miss: {p_value:.4f} ({p_value*100:.2f}%)")
    print(f"    Number of constant pairs tested: C(33,2) = 528")
    print(f"    Bonferroni-corrected p-value: {min(p_value * 528, 1.0):.4f}")

    if p_value * 528 < 0.01:
        print(f"    --> SIGNIFICANT (p_corrected < 0.01): Not a coincidence")
    elif p_value * 528 < 0.05:
        print(f"    --> MARGINALLY SIGNIFICANT (p_corrected < 0.05)")
    else:
        print(f"    --> NOT SIGNIFICANT: Could be coincidence among many comparisons")

    # 2. Info flow sweep
    info_flow_sweep()

    # 3. Constant analysis
    constant_analysis()

    print(f"\n{'='*70}")
    print(f"  Verification complete")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
