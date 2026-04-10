#!/usr/bin/env python3
"""Verify H-CX-468 through H-CX-473 (five hypotheses together)

H-CX-468: 4-Quadrant Mathematical Phase Map
H-CX-469: Quantum-Geometry Barrier (depth 2)
H-CX-470: Convergence Point Ratios = Perfect Number Divisor Reciprocals
H-CX-472: zeta(3) as PORTAL (unique?)
H-CX-473: Divisor Reciprocal Sum = 1
"""

import sys
import os
import warnings
import random
from collections import defaultdict
from itertools import combinations, product

import numpy as np

warnings.filterwarnings("ignore", category=RuntimeWarning)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convergence_engine import DOMAINS

# ═══════════════════════════════════════════════════════════════
# Common: 9 convergence targets + operations
# ═══════════════════════════════════════════════════════════════

TARGETS = {
    "sqrt(2)":   np.sqrt(2),
    "sqrt(3)":   np.sqrt(3),
    "5/6":       5/6,
    "e":         np.e,
    "zeta(3)":   1.2020569031,
    "GZ_width":  np.log(4/3),   # ln(4/3)
    "ln(2)":     np.log(2),
    "gamma_EM":  0.5772156649,
    "1/2":       0.5,
}

OPS = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b if abs(b) > 1e-15 else np.nan,
}

THRESHOLD = 0.001  # 0.1% relative error


def matches(result, target):
    if np.isnan(result) or np.isinf(result):
        return False
    if target == 0:
        return abs(result) < 1e-10
    return abs(result - target) / abs(target) < THRESHOLD


def count_paths(target_val, threshold=THRESHOLD):
    """Count independent domain paths and bridge ratio for a target."""
    domain_keys = list(DOMAINS.keys())
    independent = set()  # domains that can reach target alone
    bridge_count = 0

    # Single domain (independent paths)
    for dk in domain_keys:
        consts = list(DOMAINS[dk]["constants"].values())
        found = False
        for i, a in enumerate(consts):
            for j, b in enumerate(consts):
                if i == j:
                    continue
                for op_fn in OPS.values():
                    try:
                        r = op_fn(a, b)
                        if matches(r, target_val):
                            found = True
                            break
                    except:
                        pass
                if found:
                    break
            if found:
                break
        if found:
            independent.add(dk)

    # Cross-domain (bridge paths)
    for d1, d2 in combinations(domain_keys, 2):
        c1 = list(DOMAINS[d1]["constants"].values())
        c2 = list(DOMAINS[d2]["constants"].values())
        found = False
        for a in c1:
            for b in c2:
                for op_fn in OPS.values():
                    try:
                        r = op_fn(a, b)
                        if matches(r, target_val):
                            found = True
                            break
                    except:
                        pass
                if found:
                    break
            if found:
                break
        if found:
            bridge_count += 1

    return len(independent), bridge_count


# ═══════════════════════════════════════════════════════════════
# H-CX-468: 4-Quadrant Phase Map
# ═══════════════════════════════════════════════════════════════

def verify_h468():
    print("=" * 70)
    print("H-CX-468: 4-Quadrant Mathematical Phase Map")
    print("=" * 70)

    expected_quadrants = {
        "CORE":   ["5/6", "GZ_width"],
        "BRIDGE": ["sqrt(2)", "sqrt(3)", "e"],
        "LOCAL":  ["ln(2)", "gamma_EM", "1/2"],
        "PORTAL": ["zeta(3)"],
    }

    # Thresholds: independence >= 4 = high, ratio > 3 = high
    INDEP_THRESH = 4
    RATIO_THRESH = 3

    results = {}
    for name, val in TARGETS.items():
        indep, bridge = count_paths(val)
        ratio = bridge / indep if indep > 0 else float('inf')
        results[name] = (indep, bridge, ratio)

    print(f"\n{'Target':<12} {'Indep':>6} {'Bridge':>7} {'Ratio':>7}  Quadrant")
    print("-" * 55)

    classifications = {}
    for name in sorted(TARGETS.keys()):
        indep, bridge, ratio = results[name]
        # Classify
        hi_indep = indep >= INDEP_THRESH
        hi_ratio = ratio > RATIO_THRESH
        if hi_indep and not hi_ratio:
            q = "CORE"
        elif hi_indep and hi_ratio:
            q = "BRIDGE"
        elif not hi_indep and not hi_ratio:
            q = "LOCAL"
        else:
            q = "PORTAL"
        classifications[name] = q
        print(f"{name:<12} {indep:>6} {bridge:>7} {ratio:>7.2f}  {q}")

    # ASCII scatter plot: x = independence, y = ratio
    print("\n  ASCII Scatter: x=independence, y=bridge/indep ratio")
    print("  " + "-" * 42)

    max_indep = max(r[0] for r in results.values()) + 1
    max_ratio = max(r[2] for r in results.values() if r[2] != float('inf')) + 1

    # Grid: 40 wide x 15 tall
    W, H = 40, 15
    grid = [[' ' for _ in range(W)] for _ in range(H)]

    # Draw quadrant lines
    indep_line = int(INDEP_THRESH / max_indep * (W - 1))
    ratio_line = H - 1 - int(RATIO_THRESH / max_ratio * (H - 1))
    for row in range(H):
        if 0 <= indep_line < W:
            grid[row][indep_line] = '|'
    for col in range(W):
        if 0 <= ratio_line < H:
            grid[ratio_line][col] = '-'

    # Plot points
    symbols = {
        "CORE": "C", "BRIDGE": "B", "LOCAL": "L", "PORTAL": "P"
    }
    for name, (indep, bridge, ratio) in results.items():
        if ratio == float('inf'):
            continue
        x = int(indep / max_indep * (W - 1))
        y = H - 1 - int(ratio / max_ratio * (H - 1))
        x = max(0, min(W - 1, x))
        y = max(0, min(H - 1, y))
        sym = symbols.get(classifications[name], "?")
        grid[y][x] = sym

    for row in grid:
        print("  |" + "".join(row) + "|")
    print("  " + "-" * 42)
    print("  Legend: C=CORE, B=BRIDGE, L=LOCAL, P=PORTAL")
    print(f"  Dashed lines: indep={INDEP_THRESH} (vertical), ratio={RATIO_THRESH} (horizontal)")

    # Verify against expected
    print("\n  Quadrant verification:")
    all_match = True
    for q_name, expected_members in expected_quadrants.items():
        actual = [n for n, qc in classifications.items() if qc == q_name]
        match = set(actual) == set(expected_members)
        status = "MATCH" if match else "MISMATCH"
        if not match:
            all_match = False
        print(f"    {q_name:>7}: expected={expected_members}, actual={actual} -> {status}")

    print(f"\n  Overall H-CX-468: {'CONFIRMED' if all_match else 'PARTIAL MATCH'}")
    return all_match


# ═══════════════════════════════════════════════════════════════
# H-CX-469: Quantum-Geometry Barrier at depth 2
# ═══════════════════════════════════════════════════════════════

def verify_h469():
    print("\n" + "=" * 70)
    print("H-CX-469: Quantum-Geometry Barrier (depth 2)")
    print("=" * 70)

    Q_consts = DOMAINS["Q"]["constants"]
    Q_vals = list(Q_consts.values())
    Q_names = list(Q_consts.keys())

    geom_targets = {
        "sqrt(2)":  np.sqrt(2),
        "sqrt(3)":  np.sqrt(3),
        "pi":       np.pi,
        "pi/2":     np.pi / 2,
        "pi/3":     np.pi / 3,
        "pi/6":     np.pi / 6,
        "phi_gold": (1 + np.sqrt(5)) / 2,
    }

    print(f"\n  Q domain constants ({len(Q_vals)}):")
    for k, v in Q_consts.items():
        print(f"    {k:>20s} = {v}")

    # Depth 1: all binary ops on Q pairs
    level0 = list(Q_vals)  # base constants
    level1 = set()
    for i, a in enumerate(Q_vals):
        for j, b in enumerate(Q_vals):
            if i == j:
                continue
            for op_fn in OPS.values():
                try:
                    r = op_fn(a, b)
                    if not np.isnan(r) and not np.isinf(r) and abs(r) < 1e10:
                        level1.add(r)
                except:
                    pass
    level1 = list(level1)
    print(f"\n  Depth 1 results: {len(level1)} unique values from Q x Q")

    # Depth 2: level1 x Q_base
    level2 = set()
    for a in level1:
        for b in Q_vals:
            for op_fn in OPS.values():
                try:
                    r = op_fn(a, b)
                    if not np.isnan(r) and not np.isinf(r) and abs(r) < 1e10:
                        level2.add(r)
                except:
                    pass
    # Also Q_base x level1
    for a in Q_vals:
        for b in level1:
            for op_fn in OPS.values():
                try:
                    r = op_fn(a, b)
                    if not np.isnan(r) and not np.isinf(r) and abs(r) < 1e10:
                        level2.add(r)
                except:
                    pass
    level2 = list(level2)
    print(f"  Depth 2 results: {len(level2)} unique values from (Q x Q) x Q")

    # Check targets
    all_values = set(level0) | set(level1) | set(level2)
    print(f"  Total searchable values: {len(all_values)}")

    print(f"\n  {'Target':<12} {'Value':>10} {'Depth1':>8} {'Depth2':>8} {'Reached':>8}")
    print("  " + "-" * 52)

    barrier_holds = True
    for tname, tval in geom_targets.items():
        d1_hit = any(matches(v, tval) for v in level1)
        d2_hit = any(matches(v, tval) for v in level2)
        reached = d1_hit or d2_hit
        if reached:
            barrier_holds = False
        print(f"  {tname:<12} {tval:>10.6f} {'HIT' if d1_hit else 'MISS':>8} {'HIT' if d2_hit else 'MISS':>8} {'YES' if reached else 'NO':>8}")

    print(f"\n  Quantum-Geometry barrier at depth 2: {'HOLDS' if barrier_holds else 'BROKEN'}")
    print(f"  H-CX-469: {'CONFIRMED' if barrier_holds else 'REFUTED'}")
    return barrier_holds


# ═══════════════════════════════════════════════════════════════
# H-CX-470: Convergence Point Ratios = {1/2, 1/3, 1/6}
# ═══════════════════════════════════════════════════════════════

def verify_h470():
    print("\n" + "=" * 70)
    print("H-CX-470: Convergence Point Ratios = Perfect Number Divisor Reciprocals")
    print("=" * 70)

    gamma = 0.5772156649
    sqrt3 = np.sqrt(3)
    GZ = np.log(4/3)  # GZ_width

    ratios = {
        "gamma/sqrt(3)": (gamma / sqrt3, 1/3),
        "GZ/gamma":      (GZ / gamma, 1/2),
        "GZ/sqrt(3)":    (GZ / sqrt3, 1/6),
    }

    print(f"\n  {'Ratio':<20} {'Actual':>12} {'Target':>10} {'Error%':>10}")
    print("  " + "-" * 55)
    for name, (actual, target) in ratios.items():
        err = abs(actual - target) / abs(target) * 100
        print(f"  {name:<20} {actual:>12.8f} {target:>10.6f} {err:>9.4f}%")

    # Texas Sharpshooter Test
    print("\n  Texas Sharpshooter Test:")
    print("  Generate 9 random values in [0.1, 3.0], count pairwise ratios")
    print("  matching 1/2, 1/3, or 1/6 within 0.5%")

    # Our count: from the 9 convergence points
    conv_vals = list(TARGETS.values())
    our_count = 0
    divisor_recips = [1/2, 1/3, 1/6]
    for i in range(len(conv_vals)):
        for j in range(len(conv_vals)):
            if i == j:
                continue
            r = conv_vals[i] / conv_vals[j] if conv_vals[j] != 0 else np.nan
            if np.isnan(r):
                continue
            for dr in divisor_recips:
                if abs(r - dr) / abs(dr) < 0.005:
                    our_count += 1

    print(f"  Our convergence points: {our_count} pairwise ratios match")

    N_TRIALS = 10000
    random.seed(42)
    counts = []
    for _ in range(N_TRIALS):
        vals = [random.uniform(0.1, 3.0) for _ in range(9)]
        c = 0
        for i in range(9):
            for j in range(9):
                if i == j:
                    continue
                r = vals[i] / vals[j]
                for dr in divisor_recips:
                    if abs(r - dr) / abs(dr) < 0.005:
                        c += 1
        counts.append(c)

    mean_c = np.mean(counts)
    std_c = np.std(counts)
    p_val = np.mean([c >= our_count for c in counts])

    print(f"  Random baseline: mean={mean_c:.2f} +/- {std_c:.2f}")
    print(f"  p-value (random >= ours): {p_val:.6f}")
    print(f"  Z-score: {(our_count - mean_c) / std_c:.2f}" if std_c > 0 else "  Z-score: N/A")

    confirmed = p_val < 0.05
    print(f"\n  H-CX-470: {'SIGNIFICANT (p<0.05)' if confirmed else 'NOT SIGNIFICANT'}")
    return confirmed


# ═══════════════════════════════════════════════════════════════
# H-CX-472: zeta(3) uniquely PORTAL
# ═══════════════════════════════════════════════════════════════

def verify_h472():
    print("\n" + "=" * 70)
    print("H-CX-472: zeta(3) as Unique PORTAL")
    print("=" * 70)

    INDEP_THRESH = 4
    RATIO_THRESH = 3

    results = {}
    for name, val in TARGETS.items():
        indep, bridge = count_paths(val)
        ratio = bridge / indep if indep > 0 else float('inf')
        hi_indep = indep >= INDEP_THRESH
        hi_ratio = ratio > RATIO_THRESH
        if hi_indep and not hi_ratio:
            q = "CORE"
        elif hi_indep and hi_ratio:
            q = "BRIDGE"
        elif not hi_indep and not hi_ratio:
            q = "LOCAL"
        else:
            q = "PORTAL"
        results[name] = {"indep": indep, "bridge": bridge, "ratio": ratio, "quadrant": q}

    portals = [n for n, r in results.items() if r["quadrant"] == "PORTAL"]
    print(f"\n  PORTAL members: {portals}")
    is_unique = portals == ["zeta(3)"]

    if "zeta(3)" in results:
        zr = results["zeta(3)"]
        print(f"\n  zeta(3) properties:")
        print(f"    Independence:  {zr['indep']} (threshold: {INDEP_THRESH})")
        print(f"    Bridge count:  {zr['bridge']}")
        print(f"    Ratio:         {zr['ratio']:.2f} (threshold: {RATIO_THRESH})")
        print(f"    Quadrant:      {zr['quadrant']}")

        print(f"\n  Comparison with other targets:")
        print(f"  {'Target':<12} {'Indep':>6} {'Bridge':>7} {'Ratio':>7} {'Quadrant':>10}")
        print("  " + "-" * 45)
        for name in sorted(results.keys()):
            r = results[name]
            marker = " <-- PORTAL" if r["quadrant"] == "PORTAL" else ""
            print(f"  {name:<12} {r['indep']:>6} {r['bridge']:>7} {r['ratio']:>7.2f} {r['quadrant']:>10}{marker}")

    print(f"\n  zeta(3) is unique PORTAL: {is_unique}")
    print(f"  QFT loop analogy: zeta(3) appears in 1-loop Feynman integrals")
    print(f"  PORTAL = low internal reachability, high cross-domain connectivity")
    print(f"  This mirrors QFT: loop integrals connect domains (UV/IR) that are")
    print(f"  individually unreachable.")
    print(f"\n  H-CX-472: {'CONFIRMED' if is_unique else 'REFUTED'}")
    return is_unique


# ═══════════════════════════════════════════════════════════════
# H-CX-473: Divisor Reciprocal Sum = 1
# ═══════════════════════════════════════════════════════════════

def verify_h473():
    print("\n" + "=" * 70)
    print("H-CX-473: Divisor Reciprocal Sum = 1")
    print("=" * 70)

    gamma = 0.5772156649
    sqrt3 = np.sqrt(3)
    GZ = np.log(4/3)

    r1 = gamma / sqrt3
    r2 = GZ / gamma
    r3 = GZ / sqrt3

    s = r1 + r2 + r3
    err = abs(s - 1.0) / 1.0 * 100

    print(f"\n  gamma/sqrt(3) = {r1:.10f}  (target 1/3 = {1/3:.10f})")
    print(f"  GZ/gamma      = {r2:.10f}  (target 1/2 = {0.5:.10f})")
    print(f"  GZ/sqrt(3)    = {r3:.10f}  (target 1/6 = {1/6:.10f})")
    print(f"\n  Sum           = {s:.10f}")
    print(f"  Target        = 1.0000000000")
    print(f"  Error         = {err:.6f}%")

    # Check if 1/3 + 1/2 + 1/6 = 1 (exact)
    exact_sum = 1/3 + 1/2 + 1/6
    print(f"\n  Exact 1/3 + 1/2 + 1/6 = {exact_sum:.15f} (={exact_sum})")

    # Search for other 3-combinations with sum close to 1
    print("\n  Searching other 3-element ratio combinations with sum ~ 1:")
    conv_names = list(TARGETS.keys())
    conv_vals = list(TARGETS.values())
    n = len(conv_vals)

    near_one = []
    for triple in combinations(range(n), 3):
        i, j, k = triple
        # Try all 6 ordered pairs for ratios a/b, c/d, e/f
        # from 3 values we pick ordered pairs of 2
        vals_3 = [conv_vals[i], conv_vals[j], conv_vals[k]]
        names_3 = [conv_names[i], conv_names[j], conv_names[k]]

        # All permutations of 3 values as (a/b, c/d, e/f) doesn't make sense
        # with only 3 values. Instead: all ratios among 3 values, pick 3 ratios summing to 1
        # Generate all 6 ordered ratios from 3 values
        ratio_list = []
        for a_idx in range(3):
            for b_idx in range(3):
                if a_idx == b_idx:
                    continue
                r = vals_3[a_idx] / vals_3[b_idx] if vals_3[b_idx] != 0 else np.nan
                if not np.isnan(r):
                    ratio_list.append((r, f"{names_3[a_idx]}/{names_3[b_idx]}"))

        # Pick 3 ratios from these 6
        for combo in combinations(ratio_list, 3):
            s_test = sum(c[0] for c in combo)
            if abs(s_test - 1.0) < 0.01:  # within 1%
                desc = " + ".join(c[1] for c in combo)
                near_one.append((abs(s_test - 1.0), s_test, desc))

    near_one.sort()
    if near_one:
        print(f"  Found {len(near_one)} combinations within 1% of sum=1:")
        for err_v, s_v, desc in near_one[:10]:
            print(f"    {desc} = {s_v:.8f}  (err={err_v*100:.4f}%)")
    else:
        print("  No other 3-ratio combinations found near sum=1")

    # Is our specific combination the best?
    our_err = abs(s - 1.0)
    if near_one:
        rank = sum(1 for e, _, _ in near_one if e < our_err) + 1
        print(f"\n  Our combination (gamma/sqrt3 + GZ/gamma + GZ/sqrt3) ranks #{rank}/{len(near_one)}")
        is_best = rank == 1
    else:
        is_best = True

    print(f"\n  H-CX-473: {'CONFIRMED' if err < 5 else 'REFUTED'} (error={err:.4f}%)")
    return err < 5


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("  HYPOTHESIS VERIFICATION: H-CX-468 to H-CX-473")
    print("  5 Hypotheses | Convergence Point Analysis")
    print("=" * 70)

    results = {}
    results["H-CX-468"] = verify_h468()
    results["H-CX-469"] = verify_h469()
    results["H-CX-470"] = verify_h470()
    results["H-CX-472"] = verify_h472()
    results["H-CX-473"] = verify_h473()

    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    for h, result in results.items():
        status = "CONFIRMED" if result else "REFUTED/PARTIAL"
        print(f"  {h}: {status}")
    print("=" * 70)


if __name__ == "__main__":
    main()
