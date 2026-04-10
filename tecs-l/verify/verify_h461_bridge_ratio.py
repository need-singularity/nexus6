#!/usr/bin/env python3
"""H-CX-461: zeta(3) Maximum Bridge Hypothesis Verification

Hypothesis: zeta(3) (Apery constant, 1.2020569031) has the highest
bridge-to-independent ratio among the top 9 convergence points.

"Bridge" = cross-domain path (one constant from each of two different domains).
"Independent" = single-domain path (both constants from the same domain).

High ratio means: hard to reach from any single domain alone,
but easy to reach by combining two domains => inter-domain "glue".
"""

import sys
import os
import warnings
from collections import defaultdict
from itertools import combinations

import numpy as np

warnings.filterwarnings("ignore", category=RuntimeWarning)

# Import domain data
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convergence_engine import DOMAINS

# ═══════════════════════════════════════════════════════════════
# 9 convergence targets
# ═══════════════════════════════════════════════════════════════

TARGETS = {
    "sqrt(2)":   np.sqrt(2),
    "sqrt(3)":   np.sqrt(3),
    "5/6":       5/6,
    "e":         np.e,
    "zeta(3)":   1.2020569031,
    "ln(4/3)":   np.log(4/3),
    "ln(2)":     np.log(2),
    "gamma_EM":  0.5772156649,
    "1/2":       0.5,
}

# Binary operations
OPS = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b if b != 0 else np.nan,
    "r-": lambda a, b: b - a,
    "r/": lambda a, b: b / a if a != 0 else np.nan,
}

THRESHOLD = 0.001  # 0.1% relative error


def matches(result, target):
    """Check if result matches target within 0.1% relative error."""
    if np.isnan(result) or np.isinf(result) or target == 0:
        return abs(result - target) < 1e-10 if target == 0 else False
    return abs(result - target) / abs(target) < THRESHOLD


def count_single_domain_paths(target_val):
    """Count how many domains can reach the target using pairs within that domain."""
    domain_hits = set()
    path_count = 0
    for did, dinfo in DOMAINS.items():
        consts = list(dinfo["constants"].items())
        found = False
        for i in range(len(consts)):
            for j in range(len(consts)):
                if i == j:
                    continue
                a_name, a_val = consts[i]
                b_name, b_val = consts[j]
                for op_name, op_fn in OPS.items():
                    try:
                        res = op_fn(a_val, b_val)
                        if matches(res, target_val):
                            found = True
                            path_count += 1
                    except:
                        pass
        if found:
            domain_hits.add(did)
    return len(domain_hits), path_count


def count_bridge_paths(target_val):
    """Count cross-domain pairs that can reach the target."""
    domain_ids = list(DOMAINS.keys())
    pair_hits = set()
    path_count = 0
    pair_path_counts = defaultdict(int)

    for d1, d2 in combinations(domain_ids, 2):
        consts1 = list(DOMAINS[d1]["constants"].items())
        consts2 = list(DOMAINS[d2]["constants"].items())
        found = False
        for a_name, a_val in consts1:
            for b_name, b_val in consts2:
                for op_name, op_fn in OPS.items():
                    try:
                        res = op_fn(a_val, b_val)
                        if matches(res, target_val):
                            found = True
                            path_count += 1
                            pair_path_counts[(d1, d2)] += 1
                    except:
                        pass
        if found:
            pair_hits.add((d1, d2))

    return len(pair_hits), path_count, pair_path_counts


# ═══════════════════════════════════════════════════════════════
# Main verification
# ═══════════════════════════════════════════════════════════════

print("=" * 80)
print("H-CX-461: zeta(3) Maximum Bridge Hypothesis Verification")
print("=" * 80)
print(f"\nThreshold: {THRESHOLD*100}% relative error")
print(f"Domains: {len(DOMAINS)} ({', '.join(DOMAINS.keys())})")
print(f"Binary ops: {list(OPS.keys())}")
print(f"Targets: {len(TARGETS)}")
print()

# Count constants per domain
for did, dinfo in DOMAINS.items():
    print(f"  {did} ({dinfo['name']}): {len(dinfo['constants'])} constants")
print()

results = []
all_pair_paths = {}

for tname, tval in TARGETS.items():
    single_domains, single_paths = count_single_domain_paths(tval)
    bridge_pairs, bridge_paths, pair_counts = count_bridge_paths(tval)

    if single_domains == 0:
        ratio = float('inf') if bridge_pairs > 0 else 0
    else:
        ratio = bridge_pairs / single_domains

    results.append({
        "name": tname,
        "value": tval,
        "single_domains": single_domains,
        "single_paths": single_paths,
        "bridge_pairs": bridge_pairs,
        "bridge_paths": bridge_paths,
        "ratio": ratio,
    })
    all_pair_paths[tname] = pair_counts

# Sort by ratio descending
results.sort(key=lambda x: x["ratio"] if x["ratio"] != float('inf') else 999, reverse=True)

# ═══════════════════════════════════════════════════════════════
# Results table
# ═══════════════════════════════════════════════════════════════

print("=" * 90)
print(f"{'Target':<12} {'Value':>10} {'SingleDom':>10} {'SinglePath':>11} {'BridgePair':>11} {'BridgePath':>11} {'Ratio':>8}")
print("-" * 90)
for r in results:
    ratio_str = f"{r['ratio']:.1f}" if r['ratio'] != float('inf') else "inf"
    marker = " <<<" if r['name'] == "zeta(3)" else ""
    print(f"{r['name']:<12} {r['value']:>10.6f} {r['single_domains']:>10} {r['single_paths']:>11} "
          f"{r['bridge_pairs']:>11} {r['bridge_paths']:>11} {ratio_str:>8}{marker}")
print("-" * 90)

# ═══════════════════════════════════════════════════════════════
# Verification
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("VERIFICATION")
print("=" * 80)

# Find zeta(3) result
zeta3 = [r for r in results if r['name'] == 'zeta(3)'][0]
max_ratio = results[0]

print(f"\nzeta(3) ratio: {zeta3['ratio']:.2f}")
print(f"  single-domain hits: {zeta3['single_domains']}")
print(f"  bridge-pair hits:   {zeta3['bridge_pairs']}")

if max_ratio['name'] == 'zeta(3)':
    print(f"\n>>> CONFIRMED: zeta(3) has the HIGHEST bridge-to-independent ratio ({zeta3['ratio']:.1f})")
else:
    r_z = zeta3['ratio'] if zeta3['ratio'] != float('inf') else 'inf'
    r_m = max_ratio['ratio'] if max_ratio['ratio'] != float('inf') else 'inf'
    print(f"\n>>> NOT CONFIRMED: {max_ratio['name']} has higher ratio ({r_m}) vs zeta(3) ({r_z})")

# ═══════════════════════════════════════════════════════════════
# ASCII bar chart
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("Bridge-to-Independent Ratio (ASCII Bar Chart)")
print("=" * 80)

max_finite_ratio = max(r['ratio'] for r in results if r['ratio'] != float('inf'))
bar_width = 50

for r in results:
    ratio = r['ratio']
    if ratio == float('inf'):
        bar_len = bar_width
        bar = "#" * bar_len + " (inf)"
    else:
        bar_len = int(ratio / max_finite_ratio * bar_width) if max_finite_ratio > 0 else 0
        bar = "#" * max(bar_len, 1)
    marker = " ***" if r['name'] == 'zeta(3)' else ""
    print(f"  {r['name']:<12} |{bar}{marker}")

# ═══════════════════════════════════════════════════════════════
# zeta(3) deep dive: top domain pairs
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("zeta(3) Deep Dive: Top Domain Pairs")
print("=" * 80)

zeta3_pairs = all_pair_paths.get("zeta(3)", {})
sorted_pairs = sorted(zeta3_pairs.items(), key=lambda x: x[1], reverse=True)

if sorted_pairs:
    print(f"\n{'Rank':<6} {'Domain Pair':<40} {'Paths':>8}")
    print("-" * 56)
    for i, ((d1, d2), count) in enumerate(sorted_pairs[:10]):
        name1 = DOMAINS[d1]["name"]
        name2 = DOMAINS[d2]["name"]
        print(f"  {i+1:<4} {d1}({name1}) x {d2}({name2})  {count:>5}")

    # Show actual formulas for top pairs
    print("\n" + "-" * 80)
    print("Sample bridge formulas reaching zeta(3) = 1.2020569031:")
    print("-" * 80)
    shown = 0
    for (d1, d2), count in sorted_pairs[:5]:
        consts1 = list(DOMAINS[d1]["constants"].items())
        consts2 = list(DOMAINS[d2]["constants"].items())
        for a_name, a_val in consts1:
            for b_name, b_val in consts2:
                for op_name, op_fn in OPS.items():
                    try:
                        res = op_fn(a_val, b_val)
                        if matches(res, 1.2020569031):
                            err = abs(res - 1.2020569031) / 1.2020569031 * 100
                            name1 = DOMAINS[d1]["name"]
                            name2 = DOMAINS[d2]["name"]
                            print(f"  [{d1}]{a_name} {op_name} [{d2}]{b_name} = {res:.10f}  (err={err:.4f}%)")
                            shown += 1
                            if shown >= 15:
                                break
                    except:
                        pass
                if shown >= 15:
                    break
            if shown >= 15:
                break
        if shown >= 15:
            break

else:
    print("\n  No bridge paths found for zeta(3)!")

# ═══════════════════════════════════════════════════════════════
# Interpretation
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("INTERPRETATION")
print("=" * 80)

print("""
A high bridge-to-independent ratio means:
  - The constant is HARD to construct from within any single domain
  - But EASY to construct by combining constants from different domains
  - This makes it "inter-domain glue" -- it naturally appears at the
    intersection of different mathematical fields

If zeta(3) has the highest ratio, it means:
  - zeta(3) is the most "cross-disciplinary" constant among these 9
  - No single domain owns it, but many domain pairs can produce it
  - This aligns with zeta(3)'s known mathematical nature: it appears
    in number theory, analysis, quantum field theory, and knot theory
""")

# Summary statistics
print("=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)
finite_ratios = [r['ratio'] for r in results if r['ratio'] != float('inf')]
if finite_ratios:
    print(f"  Mean ratio:   {np.mean(finite_ratios):.2f}")
    print(f"  Median ratio: {np.median(finite_ratios):.2f}")
    print(f"  Std ratio:    {np.std(finite_ratios):.2f}")
    if zeta3['ratio'] != float('inf') and np.std(finite_ratios) > 0:
        z_score = (zeta3['ratio'] - np.mean(finite_ratios)) / np.std(finite_ratios)
        print(f"  zeta(3) Z-score: {z_score:.2f} (above mean)")

print("\nDone.")
