#!/usr/bin/env python3
"""H-CX-459: Only sqrt(2) and sqrt(3) converge (sqrt(n) selectivity)

Hypothesis: Only sqrt of prime factors of perfect number 6 (i.e. 2, 3)
appear as multi-domain convergence points among sqrt(n) values.

Extended test: sqrt(7) should also converge if the pattern extends to
perfect number 28 = 2^2 * 7 (prime factors 2 and 7).

Method:
  For each sqrt(n), for each of the 8 domains, try ALL binary operations
  on pairs of domain-internal constants. Count how many domains can
  independently reach sqrt(n) within 0.1% error.
"""

import sys
import os
import numpy as np
from itertools import combinations_with_replacement

# Import domains from convergence_engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convergence_engine import DOMAINS

# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

THRESHOLD = 0.001  # 0.1% relative error
TEST_NS = [2, 3, 5, 6, 7, 8, 10, 11, 13]
TARGETS = {n: np.sqrt(n) for n in TEST_NS}

# Binary operations
OPS = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b if b != 0 else None,
    "^": lambda a, b: a ** b if abs(b) < 20 and abs(a) < 1e6 else None,
}


def check_domain_reaches(domain_id, domain_data, target_val):
    """Check if a domain can reach target_val via binary op on 2 internal constants.

    Returns list of (expr, value) that match within threshold.
    """
    consts = domain_data["constants"]
    names = list(consts.keys())
    vals = [consts[n] for n in names]
    hits = []

    for i in range(len(names)):
        for j in range(len(names)):
            a_name, a_val = names[i], vals[i]
            b_name, b_val = names[j], vals[j]

            for op_sym, op_fn in OPS.items():
                try:
                    result = op_fn(a_val, b_val)
                    if result is None or not np.isfinite(result) or result <= 0:
                        continue
                    rel_err = abs(result - target_val) / target_val
                    if rel_err < THRESHOLD:
                        expr = f"{a_name} {op_sym} {b_name}"
                        hits.append((expr, result, rel_err))
                except (OverflowError, ZeroDivisionError, ValueError):
                    continue

    # Also try unary sqrt on each constant
    for i in range(len(names)):
        a_name, a_val = names[i], vals[i]
        if a_val > 0:
            result = np.sqrt(a_val)
            rel_err = abs(result - target_val) / target_val
            if rel_err < THRESHOLD:
                hits.append((f"sqrt({a_name})", result, rel_err))

    return hits


# ═══════════════════════════════════════════════════════════════
# Main verification
# ═══════════════════════════════════════════════════════════════

print("=" * 75)
print("H-CX-459: sqrt(n) Selectivity Verification")
print("=" * 75)
print(f"Threshold: {THRESHOLD*100}% relative error")
print(f"Domains: {len(DOMAINS)} ({', '.join(DOMAINS.keys())})")
print(f"Test targets: sqrt(n) for n in {TEST_NS}")
print()

# Perfect number prime factor info
pf6 = {2, 3}       # 6 = 2 * 3
pf28 = {2, 7}      # 28 = 2^2 * 7
pf_union = pf6 | pf28  # {2, 3, 7}

results = {}  # n -> {domain_id: [hits]}

for n in TEST_NS:
    target = TARGETS[n]
    results[n] = {}
    for did, dom in DOMAINS.items():
        hits = check_domain_reaches(did, dom, target)
        results[n][did] = hits

# ═══════════════════════════════════════════════════════════════
# Results table
# ═══════════════════════════════════════════════════════════════

print("-" * 75)
print(f"{'sqrt(n)':>8} | {'value':>8} | {'domains':>7} | {'PF6?':>4} | {'PF28?':>5} | domain list")
print("-" * 75)

domain_counts = {}
for n in TEST_NS:
    target = TARGETS[n]
    matching_domains = []
    for did in DOMAINS:
        if results[n][did]:
            matching_domains.append(did)
    domain_counts[n] = len(matching_domains)

    is_pf6 = "YES" if n in pf6 else ""
    is_pf28 = "YES" if n in pf28 else ""
    dlist = ", ".join(matching_domains) if matching_domains else "(none)"
    print(f"sqrt({n:>2}) | {target:>8.5f} | {len(matching_domains):>7} | {is_pf6:>4} | {is_pf28:>5} | {dlist}")

print("-" * 75)
print()

# ═══════════════════════════════════════════════════════════════
# Detailed hits for multi-domain convergers
# ═══════════════════════════════════════════════════════════════

print("=" * 75)
print("DETAILED HITS (domains reaching each sqrt(n))")
print("=" * 75)

for n in TEST_NS:
    target = TARGETS[n]
    matching = [(did, results[n][did]) for did in DOMAINS if results[n][did]]
    if not matching:
        continue
    print(f"\nsqrt({n}) = {target:.6f}  [{len(matching)} domains]")
    for did, hits in matching:
        dname = DOMAINS[did]["name"]
        # Show best 3 hits per domain
        sorted_hits = sorted(hits, key=lambda x: x[2])[:3]
        for expr, val, err in sorted_hits:
            print(f"  [{did}] {dname:25s}  {expr:40s} = {val:.6f}  (err={err*100:.4f}%)")

# ═══════════════════════════════════════════════════════════════
# ASCII bar chart
# ═══════════════════════════════════════════════════════════════

print()
print("=" * 75)
print("DOMAIN COUNT BAR CHART")
print("=" * 75)
max_count = max(domain_counts.values()) if domain_counts else 1
for n in TEST_NS:
    cnt = domain_counts[n]
    bar = "#" * (cnt * 4)
    pf_tag = ""
    if n in pf6:
        pf_tag = " <-- PF(6)"
    if n in pf28 and n not in pf6:
        pf_tag = " <-- PF(28)"
    print(f"  sqrt({n:>2}) | {bar:40s} {cnt}{pf_tag}")

# ═══════════════════════════════════════════════════════════════
# Hypothesis evaluation
# ═══════════════════════════════════════════════════════════════

print()
print("=" * 75)
print("HYPOTHESIS EVALUATION")
print("=" * 75)

# H-CX-459: Only sqrt(2) and sqrt(3) should have multi-domain convergence
multi_domain_ns = [n for n in TEST_NS if domain_counts[n] >= 3]
pf6_multi = [n for n in multi_domain_ns if n in pf6]
non_pf6_multi = [n for n in multi_domain_ns if n not in pf6]

print(f"\nMulti-domain convergence (>= 3 domains): {multi_domain_ns}")
print(f"  Among PF(6)={{2,3}}:   {pf6_multi}")
print(f"  Non-PF(6):             {non_pf6_multi}")

if pf6_multi and not non_pf6_multi:
    print("\n  --> H-CX-459 SUPPORTED: Only sqrt of PF(6) show multi-domain convergence")
elif pf6_multi:
    print(f"\n  --> H-CX-459 PARTIALLY SUPPORTED: PF(6) converge but so do {non_pf6_multi}")
else:
    print("\n  --> H-CX-459 NOT SUPPORTED: No clear selectivity for PF(6)")

# Extended: Perfect number 28 test
print(f"\n--- Extended test: Perfect number 28 (PF={{2,7}}) ---")
sqrt7_domains = domain_counts.get(7, 0)
sqrt2_domains = domain_counts.get(2, 0)
print(f"  sqrt(2): {sqrt2_domains} domains (shared PF)")
print(f"  sqrt(7): {sqrt7_domains} domains")

if sqrt7_domains >= 3:
    print("  --> sqrt(7) ALSO converges: Pattern extends to PF(28)!")
    print("  --> GENERALIZED: sqrt(prime factors of ANY perfect number) = convergence point")
else:
    print(f"  --> sqrt(7) has only {sqrt7_domains} domain(s): Pattern may be specific to n=6")

# Summary statistics
print()
print("=" * 75)
print("SUMMARY STATISTICS")
print("=" * 75)

avg_non_pf = np.mean([domain_counts[n] for n in TEST_NS if n not in pf_union])
avg_pf6 = np.mean([domain_counts[n] for n in TEST_NS if n in pf6])
avg_pf28_only = domain_counts.get(7, 0)  # only 7 is unique to PF(28)

print(f"  Average domains for PF(6) sqrt:        {avg_pf6:.1f}")
print(f"  Average domains for PF(28)-only sqrt:   {avg_pf28_only:.1f}")
print(f"  Average domains for non-PF sqrt:        {avg_non_pf:.1f}")
print(f"  Selectivity ratio (PF6 / non-PF):       {avg_pf6/avg_non_pf:.2f}x" if avg_non_pf > 0 else "  (no non-PF hits)")

print()
print("Done.")
