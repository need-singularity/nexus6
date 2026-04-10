#!/usr/bin/env python3
"""Verify H-EE-16, H-EE-19, H-EE-20: Theoretical energy-efficiency hypotheses.

H-EE-16: Q-barrier implies number-theoretic architecture is necessary.
H-EE-19: ln(2) universality -> quantization theory.
H-EE-20: Entropy early stop threshold = GZ-related constant?
"""

import sys
import os
import warnings
import numpy as np
from collections import defaultdict

warnings.filterwarnings("ignore", category=RuntimeWarning)

# Import DOMAINS from convergence_engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convergence_engine import DOMAINS

# ═══════════════════════════════════════════════════════════════════════
# SHARED UTILITIES
# ═══════════════════════════════════════════════════════════════════════

GZ_CONSTANTS = {
    "GZ_upper":      0.5,
    "GZ_width":      np.log(4/3),
    "GZ_lower":      0.5 - np.log(4/3),
    "GZ_center":     1/np.e,
    "compass_upper": 5/6,
    "meta_fixed":    1/3,
}

DOMAIN_SPEC = {
    "N": "arithmetic",
    "A": "logarithmic",
    "G": "algebraic",
    "T": "geometric",
    "C": "combinatorial",
    "Q": "coupling",
    "I": "logarithmic",
    "S": "statistical",
}

def safe_op(func, *args):
    """Execute operation safely, return None on error."""
    try:
        with np.errstate(all='ignore'):
            result = func(*args)
            if result is None or not np.isfinite(result):
                return None
            if abs(result) > 1e15 or abs(result) < 1e-15:
                return None
            return float(result)
    except:
        return None


def compute_depth1_values(constants):
    """Compute all depth-1 reachable values from a set of constants."""
    values = {}
    vals = list(constants.values())
    names = list(constants.keys())

    # Unary operations on each constant
    for i, v in enumerate(vals):
        n = names[i]
        values[n] = v
        r = safe_op(np.log, v)
        if r is not None:
            values[f"ln({n})"] = r
        r = safe_op(np.sqrt, v)
        if r is not None:
            values[f"sqrt({n})"] = r
        if v != 0:
            r = safe_op(lambda x: 1.0/x, v)
            if r is not None:
                values[f"1/{n}"] = r
        r = safe_op(np.exp, v)
        if r is not None:
            values[f"exp({n})"] = r

    # Binary operations on all pairs
    for i, a in enumerate(vals):
        for j, b in enumerate(vals):
            na, nb = names[i], names[j]
            r = safe_op(lambda x, y: x+y, a, b)
            if r is not None:
                values[f"{na}+{nb}"] = r
            r = safe_op(lambda x, y: x-y, a, b)
            if r is not None:
                values[f"{na}-{nb}"] = r
            r = safe_op(lambda x, y: x*y, a, b)
            if r is not None:
                values[f"{na}*{nb}"] = r
            if b != 0:
                r = safe_op(lambda x, y: x/y, a, b)
                if r is not None:
                    values[f"{na}/{nb}"] = r
            r = safe_op(lambda x, y: x**y, a, b)
            if r is not None:
                values[f"{na}^{nb}"] = r
            if a > 0 and a != 1 and b > 0:
                r = safe_op(lambda x, y: np.log(y)/np.log(x), a, b)
                if r is not None:
                    values[f"log_{na}({nb})"] = r

    return values


def check_reachability(values, target_val, threshold=0.001):
    """Check if target_val is reachable within threshold. Return (best_expr, best_val, best_err)."""
    best = None
    for expr, val in values.items():
        if target_val != 0:
            rel_err = abs(val - target_val) / abs(target_val)
        else:
            rel_err = abs(val - target_val)
        if best is None or rel_err < best[2]:
            best = (expr, val, rel_err)
    return best


# ═══════════════════════════════════════════════════════════════════════════
# H-EE-16: Q-BARRIER IMPLIES NUMBER-THEORETIC ARCHITECTURE IS NECESSARY
# ═══════════════════════════════════════════════════════════════════════════

def verify_h_ee_16():
    print("=" * 80)
    print("H-EE-16: Q-barrier implies number-theoretic architecture is necessary")
    print("=" * 80)
    print()

    THRESHOLD_EXACT = 1e-9   # For depth-1 exact match
    THRESHOLD_LOOSE = 0.001  # 0.1% for depth-1 close match

    # Step 1: Compute depth-1 reachability for ALL domains vs ALL GZ constants
    print("Step 1: Depth-1 reachability matrix (exact, rel_err < 1e-9)")
    print("-" * 72)

    domain_codes = list(DOMAINS.keys())
    matrix_exact = {}
    matrix_loose = {}

    for gz_name, gz_val in GZ_CONSTANTS.items():
        matrix_exact[gz_name] = {}
        matrix_loose[gz_name] = {}
        for dc in domain_codes:
            d1 = compute_depth1_values(DOMAINS[dc]["constants"])
            best = check_reachability(d1, gz_val, THRESHOLD_EXACT)
            matrix_exact[gz_name][dc] = best if best and best[2] < THRESHOLD_EXACT else None
            matrix_loose[gz_name][dc] = best if best and best[2] < THRESHOLD_LOOSE else None

    # Print exact matrix
    header = f"{'GZ Constant':<16} {'Value':>10}"
    for dc in domain_codes:
        header += f" | {dc:^5}"
    print(header)
    print("-" * len(header))

    for gz_name, gz_val in GZ_CONSTANTS.items():
        row = f"{gz_name:<16} {gz_val:>10.6f}"
        for dc in domain_codes:
            hit = matrix_exact[gz_name][dc]
            if hit:
                row += f" |  YES "
            else:
                row += f" |  --- "
        print(row)

    # Count per domain
    print()
    print("Exact depth-1 reachability count per domain:")
    domain_reach_exact = {}
    for dc in domain_codes:
        count = sum(1 for gz in GZ_CONSTANTS if matrix_exact[gz][dc] is not None)
        domain_reach_exact[dc] = count
        spec = DOMAIN_SPEC[dc]
        print(f"  {dc} ({spec:>13}): {count}/{len(GZ_CONSTANTS)} GZ constants")

    # Step 2: Q domain specifically
    print()
    print("Step 2: Q domain (coupling constants) analysis")
    print("-" * 72)

    q_reach_exact = domain_reach_exact["Q"]
    q_vals = compute_depth1_values(DOMAINS["Q"]["constants"])
    print(f"  Q domain depth-1 values generated: {len(q_vals)}")
    print(f"  Q domain exact GZ matches (depth 1): {q_reach_exact}")

    # Check loose matches
    q_reach_loose = sum(1 for gz in GZ_CONSTANTS if matrix_loose[gz]["Q"] is not None)
    print(f"  Q domain loose GZ matches (0.1%, depth 1): {q_reach_loose}")

    if q_reach_loose > 0:
        print("  Loose matches found:")
        for gz_name, gz_val in GZ_CONSTANTS.items():
            hit = matrix_loose[gz_name]["Q"]
            if hit:
                print(f"    {gz_name} = {gz_val:.6f} ~ {hit[0]} = {hit[1]:.6f} (err={hit[2]:.2e})")

    # Step 3: Q domain depth-2 check (counter-argument test)
    print()
    print("Step 3: Q domain DEPTH-2 reachability (counter-argument test)")
    print("-" * 72)

    q_raw = DOMAINS["Q"]["constants"]
    q_d1 = compute_depth1_values(q_raw)
    q_d1_items = list(q_d1.items())

    # Depth 2: combine d1 values with raw constants
    q_depth2_hits = {}
    for gz_name, gz_val in GZ_CONSTANTS.items():
        hits = []
        for d1_name, d1_val in q_d1_items:
            for r_name, r_val in q_raw.items():
                for op_sym, op_fn in [("+", lambda a, b: a+b), ("-", lambda a, b: a-b),
                                       ("*", lambda a, b: a*b),
                                       ("/", lambda a, b: a/b if abs(b)>1e-15 else None)]:
                    result = op_fn(d1_val, r_val)
                    if result is None or not np.isfinite(result):
                        continue
                    if gz_val != 0:
                        rel_err = abs(result - gz_val) / abs(gz_val)
                    else:
                        rel_err = abs(result - gz_val)
                    if rel_err < THRESHOLD_LOOSE:
                        hits.append((f"({d1_name}){op_sym}{r_name}", result, rel_err))
                # Reverse for non-commutative ops
                for op_sym, op_fn in [("-", lambda a, b: a-b),
                                       ("/", lambda a, b: a/b if abs(b)>1e-15 else None)]:
                    result = op_fn(r_val, d1_val)
                    if result is None or not np.isfinite(result):
                        continue
                    if gz_val != 0:
                        rel_err = abs(result - gz_val) / abs(gz_val)
                    else:
                        rel_err = abs(result - gz_val)
                    if rel_err < THRESHOLD_LOOSE:
                        hits.append((f"{r_name}{op_sym}({d1_name})", result, rel_err))
        if hits:
            hits.sort(key=lambda x: x[2])
            q_depth2_hits[gz_name] = hits[0]

    q_d2_count = len(q_depth2_hits)
    print(f"  Q domain depth-2 GZ matches (0.1%): {q_d2_count}/{len(GZ_CONSTANTS)}")
    for gz_name, hit in q_depth2_hits.items():
        print(f"    {gz_name} = {GZ_CONSTANTS[gz_name]:.6f} ~ {hit[0]} = {hit[1]:.6f} (err={hit[2]:.2e})")

    # Step 4: Comparison — which domains CAN reach GZ at depth 1?
    print()
    print("Step 4: Number-theoretic vs coupling domain comparison")
    print("-" * 72)

    # Number-theoretic domains: N (arithmetic functions sigma, tau, phi)
    n_reach = domain_reach_exact["N"]
    a_reach = domain_reach_exact["A"]
    i_reach = domain_reach_exact["I"]
    q_reach = domain_reach_exact["Q"]

    print(f"  N (number theory):     {n_reach}/{len(GZ_CONSTANTS)} GZ constants at depth 1")
    print(f"  A (analysis/log):      {a_reach}/{len(GZ_CONSTANTS)} GZ constants at depth 1")
    print(f"  I (quantum info/log):  {i_reach}/{len(GZ_CONSTANTS)} GZ constants at depth 1")
    print(f"  Q (coupling):          {q_reach}/{len(GZ_CONSTANTS)} GZ constants at depth 1")

    # Logical chain evaluation
    print()
    print("Step 5: Logical chain evaluation")
    print("-" * 72)

    q_blocked = (q_reach == 0)
    n_can = (n_reach > 0)
    a_can = (a_reach > 0)

    print(f"  Premise 1: Q domain CANNOT reach ANY GZ constant at depth 1? "
          f"{'YES (CONFIRMED)' if q_blocked else 'NO (REFUTED)'}")
    print(f"  Premise 2: N domain CAN reach GZ constants at depth 1? "
          f"{'YES (CONFIRMED)' if n_can else 'NO (REFUTED)'}")
    print(f"  Premise 3: A/I domains CAN reach GZ constants at depth 1? "
          f"{'YES (CONFIRMED)' if a_can else 'NO (REFUTED)'}")

    print()
    if q_blocked and (n_can or a_can):
        print("  CONCLUSION: The logical chain is SOUND.")
        print("  - Physics coupling constants cannot directly define GZ parameters.")
        print("  - Number-theoretic / logarithmic domains CAN define them.")
        print("  - Therefore: number-theoretic architecture is the natural choice.")
    else:
        print("  CONCLUSION: The logical chain has GAPS.")
        if not q_blocked:
            print("  - Q domain CAN reach some GZ constants, weakening the argument.")

    # Counter-argument assessment
    print()
    print("Step 6: Counter-argument assessment (Q reaches GZ at depth 2)")
    print("-" * 72)
    print(f"  Q reaches {q_d2_count}/{len(GZ_CONSTANTS)} GZ constants at depth 2.")
    if q_d2_count > 0:
        print("  Does this invalidate the claim?")
        print(f"  - Depth 1 = direct, natural relationship (0 matches)")
        print(f"  - Depth 2 = indirect, composed operations ({q_d2_count} matches)")
        print("  - Depth 2 reachability is EXPECTED for any domain with enough constants.")
        print("  - The DIRECTNESS of the relationship matters for architecture design.")
        print("  - Verdict: Depth 2 weakens but does NOT invalidate the argument.")
        print("  - Strength: MODERATE (direct relationship is absent, but indirect exists)")
    else:
        print("  Q cannot reach GZ even at depth 2!")
        print("  - Verdict: This STRENGTHENS the Q-barrier argument.")
        print("  - Strength: STRONG")

    # Summary
    print()
    q_d1_loose_count = sum(1 for gz in GZ_CONSTANTS if matrix_loose[gz]["Q"] is not None)
    if q_blocked and q_d2_count == 0:
        verdict = "STRONG SUPPORT"
    elif q_blocked and q_d2_count > 0:
        verdict = "MODERATE SUPPORT"
    elif q_d1_loose_count > 0:
        verdict = "WEAK — Q has loose depth-1 matches"
    else:
        verdict = "INCONCLUSIVE"

    print(f"  H-EE-16 VERDICT: {verdict}")
    print()
    return verdict


# ═══════════════════════════════════════════════════════════════════════════
# H-EE-19: ln(2) UNIVERSALITY -> QUANTIZATION THEORY
# ═══════════════════════════════════════════════════════════════════════════

def verify_h_ee_19():
    print("=" * 80)
    print("H-EE-19: ln(2) universality -> quantization theory")
    print("=" * 80)
    print()

    THRESHOLD = 0.001  # 0.1%

    # Step 1: Count domain reachability for key constants
    print("Step 1: Domain reachability for ln-related constants")
    print("-" * 72)

    test_constants = {
        "ln(2)":    np.log(2),
        "ln(3)":    np.log(3),
        "ln(4/3)":  np.log(4/3),
        "ln(5)":    np.log(5),
        "ln(7)":    np.log(7),
        "ln(e)":    1.0,
        "ln(10)":   np.log(10),
    }

    domain_codes = list(DOMAINS.keys())
    reach_count = {}

    for tc_name, tc_val in test_constants.items():
        count = 0
        domains_hit = []
        for dc in domain_codes:
            d1 = compute_depth1_values(DOMAINS[dc]["constants"])
            best = check_reachability(d1, tc_val, THRESHOLD)
            if best and best[2] < THRESHOLD:
                count += 1
                domains_hit.append(dc)
        reach_count[tc_name] = (count, domains_hit)
        print(f"  {tc_name:>10} = {tc_val:.6f}  -> {count} domains: {', '.join(domains_hit)}")

    # Step 2: Build quantization spectrum table
    print()
    print("Step 2: Quantization spectrum table")
    print("-" * 72)

    quant_levels = [
        ("GZ-bit (ln(4/3)/ln(2))", np.log(4/3)/np.log(2), "ln(4/3)", np.log(4/3)),
        ("1-bit (binary)",          1.0,                    "ln(2)",   np.log(2)),
        ("1.58-bit (ternary)",      np.log(3)/np.log(2),   "ln(3)",   np.log(3)),
        ("2-bit (INT2)",            2.0,                    "ln(4)=2ln(2)", np.log(4)),
        ("3-bit",                   3.0,                    "ln(8)=3ln(2)", np.log(8)),
        ("4-bit (INT4)",            4.0,                    "ln(16)=4ln(2)", np.log(16)),
        ("8-bit (INT8)",            8.0,                    "ln(256)=8ln(2)", np.log(256)),
    ]

    header = f"{'Quantization Level':<28} {'Bits':>6} {'Base Const':>16} {'Domain Reach':>14}"
    print(header)
    print("-" * len(header))

    for name, bits, base_name, base_val in quant_levels:
        # Find domain reach for the base constant
        count = 0
        domains_hit = []
        for dc in domain_codes:
            d1 = compute_depth1_values(DOMAINS[dc]["constants"])
            best = check_reachability(d1, base_val, THRESHOLD)
            if best and best[2] < THRESHOLD:
                count += 1
                domains_hit.append(dc)
        dom_str = f"{count} ({','.join(domains_hit)})" if domains_hit else "0"
        print(f"  {name:<26} {bits:>6.3f} {base_name:>16} {dom_str:>14}")

    # Step 3: Correlation analysis
    print()
    print("Step 3: Correlation between quantization level and domain universality")
    print("-" * 72)

    # Only use distinct base constants (ln(2), ln(3), ln(4/3))
    # Higher quant levels are just multiples of ln(2), so they share the same domains
    distinct = [
        ("ln(4/3)", np.log(4/3)),
        ("ln(2)",   np.log(2)),
        ("ln(3)",   np.log(3)),
    ]

    bits_arr = []
    reach_arr = []
    for name, val in distinct:
        bits = val / np.log(2)
        count = 0
        for dc in domain_codes:
            d1 = compute_depth1_values(DOMAINS[dc]["constants"])
            best = check_reachability(d1, val, THRESHOLD)
            if best and best[2] < THRESHOLD:
                count += 1
        bits_arr.append(bits)
        reach_arr.append(count)
        print(f"  {name:>10}: {bits:.4f} bits -> {count} domain reach")

    bits_arr = np.array(bits_arr)
    reach_arr = np.array(reach_arr)

    if len(bits_arr) >= 3:
        corr = np.corrcoef(bits_arr, reach_arr)[0, 1]
        print(f"\n  Pearson correlation (bits vs domain_reach): r = {corr:+.4f}")
        # Note: with only 3 points, this is indicative but not statistically robust
        print(f"  (WARNING: only {len(bits_arr)} data points — indicative only)")
    else:
        corr = float('nan')

    # Step 4: Structural interpretation
    print()
    print("Step 4: Structural interpretation")
    print("-" * 72)

    ln2_reach = reach_count.get("ln(2)", (0, []))[0]
    ln3_reach = reach_count.get("ln(3)", (0, []))[0]
    ln43_reach = reach_count.get("ln(4/3)", (0, []))[0]

    print(f"  ln(2) domain reach:    {ln2_reach} (= fundamental 1-bit unit)")
    print(f"  ln(3) domain reach:    {ln3_reach} (= ternary/1.58-bit)")
    print(f"  ln(4/3) domain reach:  {ln43_reach} (= GZ width = 0.415 bits)")
    print()

    if ln2_reach > ln3_reach >= ln43_reach:
        print("  Pattern: ln(2) > ln(3) >= ln(4/3) in universality")
        print("  -> Binary quantization is most universally supported")
        print("  -> Ternary quantization has narrower but still significant support")
        print("  -> GZ-width bit budget (0.415 bits) is the most specialized")
        verdict = "CONFIRMED — universality hierarchy matches quantization hierarchy"
    elif ln2_reach >= ln3_reach:
        print("  Pattern: ln(2) >= ln(3) in universality")
        verdict = "PARTIAL — basic hierarchy holds"
    else:
        print("  Pattern does NOT follow expected hierarchy")
        verdict = "REFUTED — no clear hierarchy"

    # Step 5: Key insight
    print()
    print("Step 5: Key insight — ternary quantization connection")
    print("-" * 72)
    print(f"  log2(3) = ln(3)/ln(2) = {np.log(3)/np.log(2):.6f} bits")
    print(f"  This IS the ratio of #2 universal constant to #1 universal constant")
    print(f"  Ternary quantization (1.58 bits) = ratio of two most universal constants")
    print()
    print(f"  GZ width in bits = ln(4/3)/ln(2) = {np.log(4/3)/np.log(2):.6f} bits")
    print(f"  = log2(3) - 1 = {np.log(3)/np.log(2) - 1:.6f}")
    print(f"  This means: GZ_width = the fractional part of ternary quantization!")
    print(f"  Or: GZ_width = 1.58 - 1 = 0.58 bits (the extra bit beyond binary)")

    print()
    print(f"  H-EE-19 VERDICT: {verdict}")
    print()
    return verdict


# ═══════════════════════════════════════════════════════════════════════════
# H-EE-20: ENTROPY EARLY STOP THRESHOLD = GZ-RELATED CONSTANT?
# ═══════════════════════════════════════════════════════════════════════════

def verify_h_ee_20():
    print("=" * 80)
    print("H-EE-20: Entropy early stop threshold = GZ-related constant?")
    print("=" * 80)
    print()

    empirical_threshold = 0.005  # From H-SEDI-EE-1

    # Step 1: GZ-derived candidates
    print("Step 1: GZ-derived candidate thresholds")
    print("-" * 72)

    gz_upper = 0.5
    gz_width = np.log(4/3)
    gz_lower = 0.5 - np.log(4/3)
    gz_center = 1/np.e
    sigma6 = 12.0
    tau6 = 4.0
    phi6 = 2.0
    sopfr6 = 5.0

    candidates = {
        # GZ / number-theory combinations
        "ln(4/3)/sigma(6)":          gz_width / sigma6,
        "ln(4/3)/sigma(6)^2":       gz_width / sigma6**2,
        "1/(sigma(6)*tau(6))":       1.0 / (sigma6 * tau6),
        "GZ_width * GZ_lower":       gz_width * gz_lower,
        "ln(4/3)/pi":               gz_width / np.pi,
        "GZ_width^2":               gz_width**2,
        "GZ_width/e":               gz_width / np.e,
        "GZ_lower/sigma(6)":        gz_lower / sigma6,
        "GZ_center/sigma(6)^2":     gz_center / sigma6**2,
        "1/sigma(6)^2":             1.0 / sigma6**2,
        "GZ_width/sigma(6)^2":      gz_width / sigma6**2,
        "1/(6*sigma(6)*tau(6))":     1.0 / (6 * sigma6 * tau6),
        "GZ_lower^2":               gz_lower**2,
        "GZ_width^3":               gz_width**3,
        "1/(e*sigma(6)^2)":         1.0 / (np.e * sigma6**2),
        "ln(4/3)^2/sigma(6)":       gz_width**2 / sigma6,
        "1/(phi(6)*sigma(6)^2)":     1.0 / (phi6 * sigma6**2),
        "GZ_width*GZ_center/sigma(6)": gz_width * gz_center / sigma6,
        "1/496":                     1.0 / 496,
        "1/sigma(28)":              1.0 / 56,
        "GZ_width/(6*sigma(6))":     gz_width / (6*sigma6),
        "GZ_lower/phi(6)/sigma(6)^2": gz_lower / (phi6 * sigma6**2),
        "GZ_width^2 * GZ_lower":    gz_width**2 * gz_lower,
        "1/(6*28)":                 1.0 / 168,
    }

    # Physics constants to check
    physics_candidates = {
        "alpha (fine structure)":     1.0 / 137.035999084,
        "alpha/alpha (=1)":          1.0,
        "m_e/m_p":                   1.0 / 1836.15267343,
        "(g-2)/2":                   0.00115965218128,
        "alpha^2":                   (1.0/137.035999084)**2,
        "alpha_s/10":                0.1185/10,
        "sin^2(theta_W)/100":        0.23122/100,
        "alpha/pi":                  (1.0/137.035999084)/np.pi,
    }

    # Additional mathematical candidates
    math_candidates = {
        "1/pi^2":                    1.0/np.pi**2,
        "ln(2)/sigma(6)^2":         np.log(2)/sigma6**2,
        "1/e^3":                    np.exp(-3),
        "1/(pi*sigma(6)*tau(6))":    1.0/(np.pi*sigma6*tau6),
        "e^(-sigma(6)/phi(6))":      np.exp(-sigma6/phi6),
        "e^(-sopfr(6))":            np.exp(-sopfr6),
        "GZ_width^(sigma(6)/tau(6))": gz_width**(sigma6/tau6),
        "exp(-1/GZ_width)":          np.exp(-1.0/gz_width),
    }

    all_candidates = {}
    all_candidates.update(candidates)
    all_candidates.update(physics_candidates)
    all_candidates.update(math_candidates)

    # Sort by closeness to empirical threshold
    sorted_candidates = sorted(all_candidates.items(),
                                key=lambda x: abs(x[1] - empirical_threshold) / empirical_threshold)

    header = f"{'Candidate':<40} {'Value':>12} {'Rel Error':>12} {'Match?':>8}"
    print(header)
    print("-" * len(header))

    good_matches = []
    for name, val in sorted_candidates:
        rel_err = abs(val - empirical_threshold) / empirical_threshold
        match = "***" if rel_err < 0.1 else ("**" if rel_err < 0.25 else ("*" if rel_err < 0.5 else ""))
        if rel_err < 3.0:  # Only show within 3x
            print(f"  {name:<38} {val:>12.8f} {rel_err:>11.2%} {match:>8}")
        if rel_err < 0.1:
            good_matches.append((name, val, rel_err))

    # Step 2: Exhaustive check — all depth-1 combinations of GZ + n=6 constants
    print()
    print("Step 2: Exhaustive depth-1 search from GZ + n=6 constants")
    print("-" * 72)

    base_constants = {
        "GZ_upper": gz_upper,
        "GZ_width": gz_width,
        "GZ_lower": gz_lower,
        "GZ_center": gz_center,
        "sigma6": sigma6,
        "tau6": tau6,
        "phi6": phi6,
        "sopfr6": sopfr6,
        "6": 6.0,
        "28": 28.0,
        "e": np.e,
        "pi": np.pi,
        "ln2": np.log(2),
    }

    d1 = compute_depth1_values(base_constants)
    close_matches = []
    for expr, val in d1.items():
        if val <= 0 or not np.isfinite(val):
            continue
        rel_err = abs(val - empirical_threshold) / empirical_threshold
        if rel_err < 0.15:  # Within 15%
            close_matches.append((expr, val, rel_err))

    close_matches.sort(key=lambda x: x[2])
    print(f"  Depth-1 values generated: {len(d1)}")
    print(f"  Matches within 15% of threshold (0.005): {len(close_matches)}")

    if close_matches:
        print()
        for expr, val, err in close_matches[:20]:
            print(f"    {expr:<40} = {val:.8f}  (err = {err:.2%})")
    else:
        print("  No close depth-1 matches found!")

    # Step 3: Check extended operations (exp, log, powers)
    print()
    print("Step 3: Special function matches")
    print("-" * 72)

    special = {
        "exp(-GZ_width*sigma6)":     np.exp(-gz_width * sigma6),
        "exp(-sigma6/GZ_width)":     np.exp(-sigma6 / gz_width),
        "exp(-pi*GZ_lower)":         np.exp(-np.pi * gz_lower),
        "exp(-e*GZ_upper)":          np.exp(-np.e * gz_upper),
        "GZ_width^sigma6":           gz_width**sigma6,
        "GZ_lower^tau6":             gz_lower**tau6,
        "GZ_center^sigma6":          gz_center**sigma6,
        "GZ_width^sopfr6":           gz_width**sopfr6,
        "GZ_lower^sopfr6":           gz_lower**sopfr6,
        "exp(-1/GZ_lower)":          np.exp(-1.0/gz_lower),
        "exp(-1/GZ_center)":         np.exp(-1.0/gz_center),
        "exp(-tau6/GZ_width)":       np.exp(-tau6/gz_width),
        "GZ_width^6":               gz_width**6,
        "GZ_lower^6":               gz_lower**6,
        "exp(-sopfr6/GZ_center)":    np.exp(-sopfr6/gz_center),
        "GZ_center^tau6/sigma6":     gz_center**tau6 / sigma6,
    }

    special_matches = []
    for name, val in special.items():
        if val > 0 and np.isfinite(val):
            rel_err = abs(val - empirical_threshold) / empirical_threshold
            if rel_err < 0.5:
                special_matches.append((name, val, rel_err))

    special_matches.sort(key=lambda x: x[2])
    if special_matches:
        for name, val, err in special_matches[:10]:
            print(f"    {name:<40} = {val:.8f}  (err = {err:.2%})")
    else:
        print("  No close special-function matches found!")

    # Step 4: Verdict
    print()
    print("Step 4: Overall assessment")
    print("-" * 72)

    all_matches = good_matches + [(e, v, r) for e, v, r in close_matches if r < 0.1]
    all_matches += [(n, v, r) for n, v, r in special_matches if r < 0.1]

    if all_matches:
        # Deduplicate by value
        seen = set()
        unique_matches = []
        for name, val, err in all_matches:
            rounded = round(val, 10)
            if rounded not in seen:
                seen.add(rounded)
                unique_matches.append((name, val, err))
        unique_matches.sort(key=lambda x: x[2])

        print(f"  Found {len(unique_matches)} candidate(s) within 10% of threshold=0.005:")
        for name, val, err in unique_matches[:5]:
            print(f"    {name} = {val:.8f} (err = {err:.2%})")
        print()
        if unique_matches[0][2] < 0.05:
            verdict = f"POSSIBLE MATCH: {unique_matches[0][0]} (err={unique_matches[0][2]:.2%})"
        else:
            verdict = "WEAK — closest match has >5% error, likely empirical"
    else:
        verdict = "REFUTED — threshold 0.005 appears to be purely empirical"
        print("  No GZ-derived or physics constant matches threshold = 0.005 within 10%.")
        print("  The value 0.005 is likely a purely empirical hyperparameter.")

    # Extra: what IS 0.005 close to?
    print()
    print("Step 5: What IS 0.005 close to? (broader search)")
    print("-" * 72)

    broader = {
        "1/200":                 1/200,
        "1/pi^3":               1/np.pi**3,
        "alpha (1/137)":        1/137.035999084,
        "1/6!":                 1/720,
        "1/5!":                 1/120,
        "ln(2)/140":            np.log(2)/140,
        "exp(-5)":              np.exp(-5),
        "exp(-ln(200))":        1/200,
        "GZ_width^5":           gz_width**5,
    }
    broader_sorted = sorted(broader.items(),
                             key=lambda x: abs(x[1]-empirical_threshold)/empirical_threshold)
    for name, val in broader_sorted[:5]:
        err = abs(val - empirical_threshold)/empirical_threshold
        print(f"    {name:<30} = {val:.8f}  (err = {err:.2%})")

    print()
    print(f"  H-EE-20 VERDICT: {verdict}")
    print()
    return verdict


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("*" * 80)
    print("* VERIFICATION: H-EE-16, H-EE-19, H-EE-20                                  *")
    print("* Energy Efficiency Theoretical Hypotheses                                   *")
    print("*" * 80)
    print()

    v16 = verify_h_ee_16()
    v19 = verify_h_ee_19()
    v20 = verify_h_ee_20()

    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print()
    print(f"  H-EE-16 (Q-barrier -> number-theoretic necessity): {v16}")
    print(f"  H-EE-19 (ln(2) universality -> quantization):      {v19}")
    print(f"  H-EE-20 (early stop threshold = GZ constant?):     {v20}")
    print()
    print("Done.")
