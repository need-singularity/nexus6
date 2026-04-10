#!/usr/bin/env python3
"""H-CX-462: Bridge/Independent Ratio Meaning Verification

Hypothesis: Low bridge/independent ratio = "intrinsic" constant (easily reachable
from individual domains). High ratio = "interface" constant (lives between domains).
GZ_width=ln(4/3) has the lowest ratio (4.5) = most intrinsic.

Method:
  1. For each of the 9 convergence targets, compute:
     a. Single-domain reachability (depth-1 binary ops, 0.1% threshold)
     b. Cross-domain reachability (domain pairs)
     c. Ratio = cross / single
  2. Classify: Intrinsic (<5), Balanced (5-7), Interface (>7)
  3. Test: Is GZ_width really the most intrinsic?
  4. Correlate ratio with independent domain count from H-CX-453
"""

import sys
import os
import numpy as np
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convergence_engine import DOMAINS

# ═════════════════════════════════════════════════════════════════
# 9 convergence targets from H-CX-453
# ═════════════════════════════════════════════════════════════════

TARGETS = {
    "sqrt(2)":    np.sqrt(2),
    "sqrt(3)":    np.sqrt(3),
    "5/6":        5/6,
    "e":          np.e,
    "zeta(3)":    1.2020569031,
    "GZ_width":   np.log(4/3),
    "ln(2)":      np.log(2),
    "gamma_EM":   0.5772156649,
    "1/2":        0.5,
}

# Independent domain counts from H-CX-453 results
INDEP_DOMAINS = {
    "sqrt(2)":   4,  # A+I+N+T
    "sqrt(3)":   4,  # A+C+G+N
    "5/6":       4,  # A+N+Q+T
    "e":         4,  # A+I+N+Q
    "zeta(3)":   3,  # A+C+I
    "GZ_width":  4,  # A+C+I+N
    "ln(2)":     3,  # I+N+Q
    "gamma_EM":  3,  # A+G+N
    "1/2":       3,  # A+I+N
}

# Bridge counts from H-CX-453
BRIDGES = {
    "sqrt(2)":   25,
    "sqrt(3)":   22,
    "5/6":       25,
    "e":         21,
    "zeta(3)":   26,
    "GZ_width":  18,
    "ln(2)":     21,
    "gamma_EM":  19,
    "1/2":       17,
}

THRESHOLD = 0.001  # 0.1%

# Binary operations
OPS = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b if abs(b) > 1e-15 else None,
    "^": lambda a, b: a ** b if abs(a) < 1e6 and abs(b) < 10 else None,
}


def matches_target(val, target):
    """Check if val is within 0.1% of target."""
    if val is None or not np.isfinite(val) or abs(val) < 1e-15:
        return False
    return abs(val - target) / abs(target) < THRESHOLD


def compute_single_domain_reachability(target_val):
    """How many of the 8 domains can reach target using only their own constants (depth 1)."""
    reaching_domains = []
    for dkey, dinfo in DOMAINS.items():
        consts = list(dinfo["constants"].values())
        names = list(dinfo["constants"].keys())
        reached = False
        # Single constant
        for v in consts:
            if matches_target(v, target_val):
                reached = True
                break
        if not reached:
            # Depth 1: binary op on pairs from same domain
            for i in range(len(consts)):
                if reached:
                    break
                for j in range(len(consts)):
                    if reached:
                        break
                    if i == j:
                        continue
                    for op_name, op_fn in OPS.items():
                        try:
                            result = op_fn(consts[i], consts[j])
                            if matches_target(result, target_val):
                                reached = True
                                break
                        except (ValueError, OverflowError, ZeroDivisionError):
                            pass
        if reached:
            reaching_domains.append(dkey)
    return reaching_domains


def compute_cross_domain_reachability(target_val):
    """How many of the 28 domain pairs can reach target using cross-domain binary ops."""
    domain_keys = list(DOMAINS.keys())
    reaching_pairs = []
    for d1, d2 in combinations(domain_keys, 2):
        consts1 = list(DOMAINS[d1]["constants"].values())
        consts2 = list(DOMAINS[d2]["constants"].values())
        reached = False
        for v1 in consts1:
            if reached:
                break
            for v2 in consts2:
                if reached:
                    break
                for op_name, op_fn in OPS.items():
                    try:
                        result = op_fn(v1, v2)
                        if matches_target(result, target_val):
                            reached = True
                            break
                    except (ValueError, OverflowError, ZeroDivisionError):
                        pass
                    if not reached:
                        try:
                            result = op_fn(v2, v1)
                            if matches_target(result, target_val):
                                reached = True
                                break
                        except (ValueError, OverflowError, ZeroDivisionError):
                            pass
        if reached:
            reaching_pairs.append(f"{d1}+{d2}")
    return reaching_pairs


def main():
    print("=" * 72)
    print("  H-CX-462: Bridge/Independent Ratio Meaning Verification")
    print("=" * 72)
    print()
    print(f"  Domains: {len(DOMAINS)} | Targets: {len(TARGETS)}")
    print(f"  Threshold: {THRESHOLD*100}% | Ops: +, -, *, /, ^")
    print(f"  Domain pairs: {len(list(combinations(DOMAINS.keys(), 2)))}")
    print()

    results = {}

    for tname, tval in TARGETS.items():
        print(f"  Computing {tname} = {tval:.6f} ...", end=" ", flush=True)
        single = compute_single_domain_reachability(tval)
        cross = compute_cross_domain_reachability(tval)
        n_single = len(single)
        n_cross = len(cross)
        ratio = n_cross / n_single if n_single > 0 else float("inf")
        results[tname] = {
            "value": tval,
            "single_domains": single,
            "cross_pairs": cross,
            "n_single": n_single,
            "n_cross": n_cross,
            "ratio": ratio,
            "indep_domains": INDEP_DOMAINS[tname],
            "bridges_453": BRIDGES[tname],
        }
        print(f"single={n_single}, cross={n_cross}, ratio={ratio:.2f}")

    # ═════════════════════════════════════════════════════════════════
    # Results Table
    # ═════════════════════════════════════════════════════════════════
    print()
    print("=" * 72)
    print("  RESULTS: Single-Domain vs Cross-Domain Reachability")
    print("=" * 72)
    print()
    print(f"  {'Target':<12} {'Value':>10} {'Single':>7} {'Cross':>6} {'Ratio':>7} {'Class':<12} {'Indep(453)':>10}")
    print(f"  {'─'*12} {'─'*10} {'─'*7} {'─'*6} {'─'*7} {'─'*12} {'─'*10}")

    sorted_results = sorted(results.items(), key=lambda x: x[1]["ratio"])

    for tname, r in sorted_results:
        if r["ratio"] < 5:
            cls = "Intrinsic"
        elif r["ratio"] > 7:
            cls = "Interface"
        else:
            cls = "Balanced"
        r["classification"] = cls
        print(f"  {tname:<12} {r['value']:>10.6f} {r['n_single']:>7d} {r['n_cross']:>6d} "
              f"{r['ratio']:>7.2f} {cls:<12} {r['indep_domains']:>10d}")

    # ═════════════════════════════════════════════════════════════════
    # Single-domain detail
    # ═════════════════════════════════════════════════════════════════
    print()
    print("=" * 72)
    print("  DETAIL: Which domains reach each target (single-domain)")
    print("=" * 72)
    print()
    for tname, r in sorted_results:
        doms = ", ".join(r["single_domains"]) if r["single_domains"] else "(none)"
        print(f"  {tname:<12} [{r['n_single']}] {doms}")

    # ═════════════════════════════════════════════════════════════════
    # Test: Is GZ_width the most intrinsic?
    # ═════════════════════════════════════════════════════════════════
    print()
    print("=" * 72)
    print("  TEST: Is GZ_width = ln(4/3) the most intrinsic?")
    print("=" * 72)
    print()
    gz_ratio = results["GZ_width"]["ratio"]
    min_ratio_name = sorted_results[0][0]
    min_ratio_val = sorted_results[0][1]["ratio"]
    print(f"  GZ_width ratio:  {gz_ratio:.2f}")
    print(f"  Lowest ratio:    {min_ratio_name} = {min_ratio_val:.2f}")
    if min_ratio_name == "GZ_width":
        print(f"  --> CONFIRMED: GZ_width has the lowest ratio (most intrinsic)")
    else:
        print(f"  --> NOT CONFIRMED: {min_ratio_name} has a lower ratio than GZ_width")
        gz_rank = [i+1 for i, (n, _) in enumerate(sorted_results) if n == "GZ_width"][0]
        print(f"  --> GZ_width ranks #{gz_rank} out of {len(sorted_results)}")

    # ═════════════════════════════════════════════════════════════════
    # Correlation: ratio vs independent domain count
    # ═════════════════════════════════════════════════════════════════
    print()
    print("=" * 72)
    print("  CORRELATION: Ratio vs Independent Domain Count (H-CX-453)")
    print("=" * 72)
    print()

    ratios = np.array([results[t]["ratio"] for t in TARGETS])
    indeps = np.array([results[t]["indep_domains"] for t in TARGETS])
    bridges = np.array([results[t]["bridges_453"] for t in TARGETS])

    # Filter out inf ratios for correlation
    finite_mask = np.isfinite(ratios)
    if finite_mask.sum() >= 3:
        r_ratio_indep = np.corrcoef(ratios[finite_mask], indeps[finite_mask])[0, 1]
        r_ratio_bridges = np.corrcoef(ratios[finite_mask], bridges[finite_mask])[0, 1]
        r_single_indep = np.corrcoef(
            np.array([results[t]["n_single"] for t in TARGETS])[finite_mask],
            indeps[finite_mask]
        )[0, 1]

        print(f"  Pearson r(ratio, indep_domains):  {r_ratio_indep:+.4f}")
        print(f"  Pearson r(ratio, bridges_453):     {r_ratio_bridges:+.4f}")
        print(f"  Pearson r(single_reach, indep):    {r_single_indep:+.4f}")
        print()

        if r_ratio_indep < -0.3:
            print("  --> Negative correlation: higher ratio = fewer independent domains")
            print("     This supports the hypothesis that intrinsic constants")
            print("     are reachable from more independent domains.")
        elif r_ratio_indep > 0.3:
            print("  --> Positive correlation: UNEXPECTED direction.")
            print("     Higher ratio associates with MORE independent domains.")
        else:
            print("  --> Weak/no correlation between ratio and independent domain count.")
    else:
        print("  Not enough finite ratios for correlation.")

    # ═════════════════════════════════════════════════════════════════
    # ASCII visualization: ratio by target
    # ═════════════════════════════════════════════════════════════════
    print()
    print("=" * 72)
    print("  VISUALIZATION: Bridge/Independent Ratio (sorted)")
    print("=" * 72)
    print()
    max_ratio = max(r["ratio"] for _, r in sorted_results if np.isfinite(r["ratio"]))
    bar_width = 40
    for tname, r in sorted_results:
        if np.isfinite(r["ratio"]):
            bar_len = int(r["ratio"] / max_ratio * bar_width)
        else:
            bar_len = bar_width
        cls = r.get("classification", "?")
        marker = " <-- MOST INTRINSIC" if tname == sorted_results[0][0] else ""
        print(f"  {tname:<12} |{'#' * bar_len:<{bar_width}}| {r['ratio']:>6.2f}  [{cls}]{marker}")

    # ═════════════════════════════════════════════════════════════════
    # Scatter: ratio vs indep domains
    # ═════════════════════════════════════════════════════════════════
    print()
    print("  Scatter: Ratio (x) vs Independent Domains (y)")
    print()
    # Simple text scatter
    all_ratios = [(tname, results[tname]["ratio"], results[tname]["indep_domains"])
                  for tname in TARGETS if np.isfinite(results[tname]["ratio"])]
    min_r = min(x[1] for x in all_ratios)
    max_r = max(x[1] for x in all_ratios)
    width = 50
    for indep_val in [4, 3]:
        points_at_level = [(n, r) for n, r, i in all_ratios if i == indep_val]
        row = [" "] * width
        labels = []
        for name, ratio in points_at_level:
            pos = int((ratio - min_r) / (max_r - min_r + 0.01) * (width - 1))
            row[pos] = "*"
            labels.append(f"{name}({ratio:.1f})")
        print(f"  indep={indep_val} |{''.join(row)}|  {', '.join(labels)}")
    print(f"          {'':>1}{'low ratio':.<25}{'high ratio':.>25}")

    # ═════════════════════════════════════════════════════════════════
    # Summary
    # ═════════════════════════════════════════════════════════════════
    print()
    print("=" * 72)
    print("  SUMMARY")
    print("=" * 72)
    print()

    intrinsic = [(n, r) for n, r in sorted_results if r.get("classification") == "Intrinsic"]
    balanced = [(n, r) for n, r in sorted_results if r.get("classification") == "Balanced"]
    interface = [(n, r) for n, r in sorted_results if r.get("classification") == "Interface"]

    print(f"  Intrinsic (ratio < 5):  {len(intrinsic)} targets")
    for n, r in intrinsic:
        print(f"    - {n} (ratio={r['ratio']:.2f})")
    print(f"  Balanced  (5 <= ratio <= 7): {len(balanced)} targets")
    for n, r in balanced:
        print(f"    - {n} (ratio={r['ratio']:.2f})")
    print(f"  Interface (ratio > 7):  {len(interface)} targets")
    for n, r in interface:
        print(f"    - {n} (ratio={r['ratio']:.2f})")

    print()
    if min_ratio_name == "GZ_width":
        print("  VERDICT: CONFIRMED -- GZ_width = ln(4/3) is the most intrinsic constant")
        print("           (lowest bridge/independent ratio among all 9 targets)")
    else:
        print(f"  VERDICT: PARTIALLY REFUTED -- {min_ratio_name} is more intrinsic than GZ_width")
        print(f"           GZ_width ratio = {gz_ratio:.2f}, {min_ratio_name} ratio = {min_ratio_val:.2f}")

    if finite_mask.sum() >= 3:
        print(f"  CORRELATION: r(ratio, indep) = {r_ratio_indep:+.4f}")
        if abs(r_ratio_indep) > 0.5:
            print("    Strong correlation detected -- ratio is meaningfully related to independence")
        elif abs(r_ratio_indep) > 0.3:
            print("    Moderate correlation -- some relationship exists")
        else:
            print("    Weak correlation -- ratio and independence are largely orthogonal")

    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
