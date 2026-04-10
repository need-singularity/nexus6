#!/usr/bin/env python3
"""
Verify H-CX-495 and H-CX-498
  H-CX-495: GZ_width = Information Deficit S(4)-S(3)
  H-CX-498: GZ_width intrinsicness = ln(2) + ln(3) universality
"""

import numpy as np
import sys
sys.path.insert(0, "/Users/ghost/Dev/TECS-L")

# ═══════════════════════════════════════════════════════════════
# H-CX-495: GZ_width = Information Deficit S(4) - S(3)
# ═══════════════════════════════════════════════════════════════

print("=" * 70)
print("H-CX-495: GZ_width = Information Deficit S(4) - S(3)")
print("=" * 70)

# --- Part 1: Algebraic identity ---
print("\n--- Part 1: Algebraic Identity ---")
print("  S(n) = ln(n) for uniform distribution over n states")
print("  S(4) - S(3) = ln(4) - ln(3) = ln(4/3)")
print("  Also: ln(4) = 2*ln(2), so ln(4/3) = 2*ln(2) - ln(3)")
print()

S4 = np.log(4)
S3 = np.log(3)
ln_4_3 = np.log(4/3)
two_ln2_minus_ln3 = 2*np.log(2) - np.log(3)

print(f"  S(4) = ln(4)     = {S4:.15f}")
print(f"  S(3) = ln(3)     = {S3:.15f}")
print(f"  S(4) - S(3)      = {S4 - S3:.15f}")
print(f"  ln(4/3)           = {ln_4_3:.15f}")
print(f"  2*ln(2) - ln(3)  = {two_ln2_minus_ln3:.15f}")
print(f"  GZ_width          = {ln_4_3:.15f}")
print()
print(f"  |S(4)-S(3) - ln(4/3)|       = {abs((S4-S3) - ln_4_3):.2e}")
print(f"  |2ln(2)-ln(3) - ln(4/3)|    = {abs(two_ln2_minus_ln3 - ln_4_3):.2e}")

eps = 1e-14
assert abs((S4 - S3) - ln_4_3) < eps, "FAIL: S(4)-S(3) != ln(4/3)"
assert abs(two_ln2_minus_ln3 - ln_4_3) < eps, "FAIL: 2ln(2)-ln(3) != ln(4/3)"
print("  => EXACT identity confirmed (to machine precision)")

# --- Part 2: General formula ---
print("\n--- Part 2: Generalization S(n+1) - S(n) = ln((n+1)/n) ---")
print()
print("  Proof: S(n) = ln(n)  =>  S(n+1) - S(n) = ln(n+1) - ln(n) = ln((n+1)/n)")
print("  This holds for ALL n >= 1. QED.")
print()
print("  GZ_width = ln(4/3) is the SPECIFIC case n=3.")
print("  Why n=3? Because tau(6) = 4 (divisor count of P_1 = 6)")
print("  So the transition is tau(P_1)-1 = 3  ->  tau(P_1) = 4")
print()

# Verify numerically for n=1..10
print("  | n  | S(n+1)-S(n) | ln((n+1)/n) | Match  |")
print("  |----|-------------|-------------|--------|")
for n in range(1, 11):
    diff = np.log(n+1) - np.log(n)
    formula = np.log((n+1)/n)
    match = abs(diff - formula) < 1e-14
    marker = " <-- GZ_width (P1=6)" if n == 3 else ""
    print(f"  | {n:2d} | {diff:.10f}  | {formula:.10f}  | {'YES' if match else 'NO':6s} |{marker}")

# --- Part 3: Perfect number series ---
print("\n--- Part 3: GZ_width for Perfect Numbers P1, P2, P3 ---")
print()

perfect_numbers = [
    (1, 6, 4),      # P1=6, tau(6)=4
    (2, 28, 6),     # P2=28, tau(28)=6
    (3, 496, 10),   # P3=496, tau(496)=10
    (4, 8128, 14),  # P4=8128, tau(8128)=14
]

print("  | P_k | n     | tau(n) | Transition       | GZ_width_k = ln(tau/(tau-1))  | In nats      | In bits      |")
print("  |-----|-------|--------|------------------|-------------------------------|--------------|--------------|")
for k, n, tau in perfect_numbers:
    width = np.log(tau / (tau - 1))
    width_bits = width / np.log(2)
    print(f"  | P{k}  | {n:5d} | {tau:5d}  | {tau-1:2d} -> {tau:2d}           | ln({tau}/{tau-1}) = {width:.10f}       | {width:.10f} | {width_bits:.10f} |")

# --- Part 5: GZ widths in bits ---
print("\n--- Part 5: All GZ_widths in Bits ---")
print()
print("  | P_k | Width (nats)  | Width (bits)  | Interpretation                     |")
print("  |-----|---------------|---------------|------------------------------------|")
for k, n, tau in perfect_numbers:
    w_nats = np.log(tau / (tau - 1))
    w_bits = w_nats / np.log(2)
    print(f"  | P{k}  | {w_nats:.10f}  | {w_bits:.10f}  | Cost of adding divisor #{tau:2d} to n={n:<5d} |")

print()
print("  Observation: GZ_width DECREASES as perfect numbers grow.")
print(f"  P1 width: {np.log(4/3)/np.log(2):.6f} bits")
print(f"  P2 width: {np.log(6/5)/np.log(2):.6f} bits")
print(f"  P3 width: {np.log(10/9)/np.log(2):.6f} bits")
print(f"  P4 width: {np.log(14/13)/np.log(2):.6f} bits")
print(f"  Limit:    ln(1) = 0 bits (information cost vanishes)")

# --- Part 6: Physical interpretation ---
print("\n--- Part 6: Physical Interpretation ---")
print()
print("  GZ_width for P_k = ln(tau(P_k) / (tau(P_k) - 1))")
print("  = information cost (in nats) of adding ONE MORE divisor")
print("    to the divisor count of perfect number P_k.")
print()
print("  For P_1 = 6: adding the 4th divisor (6 itself) to {1,2,3}")
print("    costs exactly ln(4/3) nats = GZ_width.")
print("  This connects GZ_width to the combinatorial structure of 6.")
print()

print("\n" + "=" * 70)
print("H-CX-495 VERDICT: PROVEN (exact algebraic identity)")
print("  ln(4/3) = S(4)-S(3) = 2ln(2)-ln(3)")
print("  Generalizes to all perfect numbers via tau(P_k)")
print("=" * 70)


# ═══════════════════════════════════════════════════════════════
# H-CX-498: GZ_width intrinsicness = ln(2) + ln(3) universality
# ═══════════════════════════════════════════════════════════════

print("\n\n" + "=" * 70)
print("H-CX-498: GZ_width Intrinsicness via ln(2) + ln(3) Universality")
print("=" * 70)

from convergence_engine import DOMAINS, binary_ops

TARGET_LN2 = np.log(2)
TARGET_LN3 = np.log(3)
TARGET_LN43 = np.log(4/3)
THRESHOLD = 1e-10  # exact match threshold

def check_depth1_reachability(domain_id, target, threshold=THRESHOLD):
    """Check if target is reachable at depth 1 (one binary op on two domain constants)."""
    consts = DOMAINS[domain_id]["constants"]
    names = list(consts.keys())
    vals = [consts[n] for n in names]

    # Check if target is directly a constant
    for i, v in enumerate(vals):
        if abs(v - target) < threshold:
            return True, f"Direct: {names[i]} = {v}"

    # Check all pairs with binary ops
    for i in range(len(names)):
        for j in range(len(names)):
            if i == j:
                continue
            results = binary_ops(names[i], vals[i], names[j], vals[j])
            for rv, rn in results:
                if abs(rv - target) < threshold:
                    return True, f"{rn} = {rv}"

    return False, None

print("\n--- Step 1-2: Domain Reachability at Depth 1 ---")
print()

domain_ids = list(DOMAINS.keys())
reach_ln2 = {}
reach_ln3 = {}
reach_ln43 = {}

for did in domain_ids:
    r2, e2 = check_depth1_reachability(did, TARGET_LN2)
    r3, e3 = check_depth1_reachability(did, TARGET_LN3)
    r43, e43 = check_depth1_reachability(did, TARGET_LN43)
    reach_ln2[did] = (r2, e2)
    reach_ln3[did] = (r3, e3)
    reach_ln43[did] = (r43, e43)

print("  | Domain | Name                  | ln(2)  | ln(3)  | ln(4/3) |")
print("  |--------|-----------------------|--------|--------|---------|")
for did in domain_ids:
    name = DOMAINS[did]["name"]
    r2 = "YES" if reach_ln2[did][0] else " - "
    r3 = "YES" if reach_ln3[did][0] else " - "
    r43 = "YES" if reach_ln43[did][0] else " - "
    print(f"  |   {did}    | {name:21s} | {r2:6s} | {r3:6s} | {r43:7s} |")

# --- Step 3-4: Check subset relation ---
print("\n--- Step 3-4: Subset Relation ---")
print()

domains_with_both = set()
domains_with_ln43 = set()

for did in domain_ids:
    if reach_ln2[did][0] and reach_ln3[did][0]:
        domains_with_both.add(did)
    if reach_ln43[did][0]:
        domains_with_ln43.add(did)

print(f"  Domains reaching ln(2) AND ln(3):  {sorted(domains_with_both)}")
print(f"  Domains reaching ln(4/3):          {sorted(domains_with_ln43)}")
print()

# Check: domains_with_ln43 ⊆ domains_with_both?
subset_check = domains_with_ln43.issubset(domains_with_both)
print(f"  ln(4/3)-reachable SUBSET OF (ln2 AND ln3)-reachable? {subset_check}")

# Check: exact equality?
exact_match = domains_with_ln43 == domains_with_both
print(f"  Exact match (ln(4/3) reachable = ln(2) AND ln(3) reachable)? {exact_match}")

# --- Step 5: Detailed expressions ---
print("\n--- Step 5: How Each Domain Reaches the Targets ---")
print()

for did in sorted(domains_with_both | domains_with_ln43):
    name = DOMAINS[did]["name"]
    print(f"  Domain {did} ({name}):")
    if reach_ln2[did][0]:
        print(f"    ln(2) via: {reach_ln2[did][1]}")
    if reach_ln3[did][0]:
        print(f"    ln(3) via: {reach_ln3[did][1]}")
    if reach_ln43[did][0]:
        print(f"    ln(4/3) via: {reach_ln43[did][1]}")
    else:
        print(f"    ln(4/3): NOT reachable at depth 1")
    print()

# --- Analysis ---
print("\n--- Analysis ---")
print()

if exact_match:
    print("  RESULT: GZ_width reachability = EXACTLY the intersection")
    print("          of ln(2) and ln(3) reachability at depth 1.")
    print("  => ln(4/3) = 2ln(2) - ln(3) is intrinsically available")
    print("     in every domain that has access to both ln(2) and ln(3).")
elif subset_check:
    only_both = domains_with_both - domains_with_ln43
    print("  RESULT: ln(4/3) reachable is a STRICT SUBSET of (ln2 AND ln3) reachable.")
    print(f"  Domains with both ln(2),ln(3) but NOT ln(4/3): {sorted(only_both)}")
    print("  => Some domains have the ingredients but cannot combine them")
    print("     at depth 1 to produce ln(4/3).")
    print()
    # Check if those domains can reach ln(4/3) at depth 2
    print("  Note: ln(4/3) = 2ln(2) - ln(3) requires depth 2 in those domains")
    print("  (first compute 2*ln(2), then subtract ln(3)).")
else:
    extra = domains_with_ln43 - domains_with_both
    print("  RESULT: ln(4/3) reachable is NOT a subset of (ln2 AND ln3) reachable!")
    print(f"  Domains reaching ln(4/3) but NOT both ln(2),ln(3): {sorted(extra)}")
    print("  => ln(4/3) can be reached through other paths.")

# --- Check depth-2 for domains with both but not ln(4/3) ---
if not exact_match and subset_check:
    only_both = domains_with_both - domains_with_ln43
    print("\n--- Depth-2 Check for Missing Domains ---")
    for did in sorted(only_both):
        name = DOMAINS[did]["name"]
        consts = DOMAINS[did]["constants"]
        cnames = list(consts.keys())
        cvals = [consts[n] for n in cnames]

        # Generate all depth-1 results
        depth1 = list(zip(cnames, cvals))
        for i in range(len(cnames)):
            for j in range(len(cnames)):
                if i == j:
                    continue
                for rv, rn in binary_ops(cnames[i], cvals[i], cnames[j], cvals[j]):
                    depth1.append((rn, rv))

        # Now try depth-1 results combined with originals
        found = False
        for rn, rv in depth1:
            for cn, cv in zip(cnames, cvals):
                for rv2, rn2 in binary_ops(rn, rv, cn, cv):
                    if abs(rv2 - TARGET_LN43) < THRESHOLD:
                        print(f"  Domain {did} ({name}): ln(4/3) at depth 2 via {rn2}")
                        found = True
                        break
                if found:
                    break
            if found:
                break
        if not found:
            print(f"  Domain {did} ({name}): ln(4/3) NOT reachable even at depth 2")

print("\n" + "=" * 70)
print("H-CX-498 VERDICT:")
if exact_match:
    print("  PROVEN: GZ_width depth-1 reachability = EXACTLY intersection")
    print("  of ln(2) and ln(3) depth-1 reachability.")
elif subset_check:
    print("  PARTIALLY CONFIRMED: ln(4/3) reachable is a subset of")
    print("  (ln(2) AND ln(3)) reachable. Some domains need depth 2.")
else:
    print("  NUANCED: ln(4/3) has independent reachability paths.")
print("  ln(4/3) = 2ln(2) - ln(3) confirms it is built from ln(2) and ln(3).")
print("=" * 70)

print("\n\nDone.")
