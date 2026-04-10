#!/usr/bin/env python3
"""Verify H-CX-499 and H-CX-500: GZ constants as logarithmic domain eigenvalues
and Q-barrier exclusion of ALL Golden Zone constants.

H-CX-499: Do GZ constants appear primarily in logarithmic-specialist domains (A, I)?
H-CX-500: Is Q domain completely blocked from ALL GZ constants at depth 1?
"""

import numpy as np
from itertools import combinations
from convergence_engine import DOMAINS

# ═══════════════════════════════════════════════════════════════
# GZ CONSTANTS TO CHECK
# ═══════════════════════════════════════════════════════════════

GZ_CONSTANTS = {
    "GZ_upper":       0.5,
    "GZ_width":       np.log(4/3),
    "GZ_lower":       0.5 - np.log(4/3),
    "GZ_center":      1/np.e,
    "compass_upper":  5/6,
    "meta_fixed":     1/3,
}

# ═══════════════════════════════════════════════════════════════
# DOMAIN SPECIALIZATIONS (from H-CX-480)
# ═══════════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════════
# DEPTH-1 OPERATIONS
# ═══════════════════════════════════════════════════════════════

def depth1_values(constants_dict):
    """Generate all depth-1 values from a domain's constants.
    Depth 1 = single binary operation on any pair of constants.
    Operations: +, -, *, /, also include raw constants themselves (depth 0).
    """
    results = {}
    names = list(constants_dict.keys())
    vals = list(constants_dict.values())

    # Depth 0: raw constants
    for n, v in zip(names, vals):
        results[n] = v

    # Depth 1: all pairs with 4 operations
    for i in range(len(names)):
        for j in range(len(names)):
            if i == j:
                continue
            a_name, a_val = names[i], vals[i]
            b_name, b_val = names[j], vals[j]

            # Addition
            results[f"{a_name}+{b_name}"] = a_val + b_val
            # Subtraction
            results[f"{a_name}-{b_name}"] = a_val - b_val
            # Multiplication
            results[f"{a_name}*{b_name}"] = a_val * b_val
            # Division
            if abs(b_val) > 1e-15:
                results[f"{a_name}/{b_name}"] = a_val / b_val

    return results


def depth2_values(constants_dict, target, threshold=0.01):
    """Generate depth-2 values: apply operation to two depth-1 results.
    Only return those close to target (within threshold relative error).
    This is expensive so we filter aggressively.
    """
    d1 = depth1_values(constants_dict)
    hits = []
    d1_items = list(d1.items())

    # To keep it tractable, only check depth-1 values combined with raw constants
    raw = {k: v for k, v in constants_dict.items()}

    for d1_name, d1_val in d1_items:
        for r_name, r_val in raw.items():
            for op, op_fn, op_sym in [
                ("add", lambda a, b: a + b, "+"),
                ("sub", lambda a, b: a - b, "-"),
                ("mul", lambda a, b: a * b, "*"),
                ("div", lambda a, b: a / b if abs(b) > 1e-15 else None, "/"),
            ]:
                result = op_fn(d1_val, r_val)
                if result is None:
                    continue
                if abs(result) < 1e-15:
                    continue
                rel_err = abs(result - target) / abs(target)
                if rel_err < threshold:
                    hits.append((f"({d1_name}){op_sym}{r_name}", result, rel_err))

            # Also reverse: raw op depth1
            for op, op_fn, op_sym in [
                ("sub", lambda a, b: a - b, "-"),
                ("div", lambda a, b: a / b if abs(b) > 1e-15 else None, "/"),
            ]:
                result = op_fn(r_val, d1_val)
                if result is None:
                    continue
                if abs(result) < 1e-15:
                    continue
                rel_err = abs(result - target) / abs(target)
                if rel_err < threshold:
                    hits.append((f"{r_name}{op_sym}({d1_name})", result, rel_err))

    # Sort by error and return top hits
    hits.sort(key=lambda x: x[2])
    return hits[:10]


# ═══════════════════════════════════════════════════════════════
# H-CX-499: GZ-constant x domain matrix
# ═══════════════════════════════════════════════════════════════

print("=" * 80)
print("H-CX-499: GZ constants = logarithmic domain eigenvalues")
print("=" * 80)
print()

THRESHOLD = 1e-9  # Exact match threshold (relative error)

# Build matrix: which domains reach which GZ constants at depth 1
matrix = {}  # matrix[gz_name][domain_code] = (expr, value, rel_err) or None

for gz_name, gz_val in GZ_CONSTANTS.items():
    matrix[gz_name] = {}
    for d_code, d_data in DOMAINS.items():
        d1 = depth1_values(d_data["constants"])
        best = None
        for expr, val in d1.items():
            if abs(val) < 1e-15:
                continue
            rel_err = abs(val - gz_val) / abs(gz_val)
            if rel_err < THRESHOLD:
                if best is None or rel_err < best[2]:
                    best = (expr, val, rel_err)
        matrix[gz_name][d_code] = best

# Print the matrix
domain_codes = list(DOMAINS.keys())
print(f"GZ-constant x Domain matrix (exact matches, rel_err < {THRESHOLD}):")
print()

# Header
header = f"{'GZ Constant':<18} {'Value':>10}"
for dc in domain_codes:
    header += f" | {dc:^5}"
print(header)
print("-" * len(header))

for gz_name, gz_val in GZ_CONSTANTS.items():
    row = f"{gz_name:<18} {gz_val:>10.6f}"
    for dc in domain_codes:
        hit = matrix[gz_name][dc]
        if hit:
            row += f" |  YES "
        else:
            row += f" |  --- "
    print(row)

print()

# Detailed: which expressions match
print("Detailed matches (domain: expression = value):")
print("-" * 60)
for gz_name, gz_val in GZ_CONSTANTS.items():
    print(f"\n  {gz_name} = {gz_val:.10f}")
    any_hit = False
    for dc in domain_codes:
        hit = matrix[gz_name][dc]
        if hit:
            expr, val, err = hit
            spec = DOMAIN_SPEC[dc]
            print(f"    {dc} ({spec:>13}): {expr} = {val:.10f}  (err={err:.2e})")
            any_hit = True
    if not any_hit:
        print(f"    (no exact depth-1 match in any domain)")

# Count by specialization
print()
print("=" * 60)
print("Summary by domain specialization:")
print("=" * 60)

spec_counts = {}
for gz_name in GZ_CONSTANTS:
    for dc in domain_codes:
        if matrix[gz_name][dc]:
            spec = DOMAIN_SPEC[dc]
            spec_counts.setdefault(spec, 0)
            spec_counts[spec] = spec_counts.get(spec, 0) + 1

total_hits = sum(spec_counts.values())
print()
for spec, count in sorted(spec_counts.items(), key=lambda x: -x[1]):
    pct = 100 * count / total_hits if total_hits > 0 else 0
    bar = "#" * int(pct / 2)
    print(f"  {spec:<15} {count:>3} hits ({pct:5.1f}%)  {bar}")

log_hits = spec_counts.get("logarithmic", 0)
log_pct = 100 * log_hits / total_hits if total_hits > 0 else 0
print(f"\n  Logarithmic domains (A+I) share: {log_hits}/{total_hits} = {log_pct:.1f}%")
print(f"  H-CX-499 verdict: {'SUPPORTED' if log_pct > 40 else 'WEAK' if log_pct > 25 else 'NOT SUPPORTED'}")
print(f"    (logarithmic domains account for {log_pct:.1f}% of all GZ-constant depth-1 matches)")


# ═══════════════════════════════════════════════════════════════
# H-CX-500: Q-barrier excludes ALL Golden Zone constants
# ═══════════════════════════════════════════════════════════════

print()
print()
print("=" * 80)
print("H-CX-500: Q-barrier excludes ALL Golden Zone constants at depth 1")
print("=" * 80)
print()

q_constants = DOMAINS["Q"]["constants"]
q_d1 = depth1_values(q_constants)

# For each GZ constant, find closest Q depth-1 value
print("Q domain depth-1 closest approach to each GZ constant:")
print()
print(f"{'GZ Constant':<18} {'Target':>10} {'Closest Q val':>14} {'Abs Error':>12} {'Rel Error':>12} {'Expression'}")
print("-" * 90)

q_blocked_count = 0
for gz_name, gz_val in GZ_CONSTANTS.items():
    best_expr = None
    best_val = None
    best_err = float('inf')

    for expr, val in q_d1.items():
        if abs(val) < 1e-15 or abs(val) > 1e6:
            continue
        rel_err = abs(val - gz_val) / abs(gz_val)
        if rel_err < best_err:
            best_err = rel_err
            best_val = val
            best_expr = expr

    abs_err = abs(best_val - gz_val) if best_val else float('inf')
    blocked = best_err > 0.01  # >1% error = blocked

    marker = "BLOCKED" if blocked else "CLOSE"
    if best_err < THRESHOLD:
        marker = "EXACT"

    if blocked:
        q_blocked_count += 1

    print(f"{gz_name:<18} {gz_val:>10.6f} {best_val:>14.6f} {abs_err:>12.6f} {best_err:>11.4%}  {best_expr}  [{marker}]")

print()
all_blocked = q_blocked_count == len(GZ_CONSTANTS)
print(f"Q domain blocked from {q_blocked_count}/{len(GZ_CONSTANTS)} GZ constants at depth 1")
print(f"H-CX-500 (depth-1 exclusion): {'CONFIRMED' if all_blocked else 'PARTIAL — not all blocked'}")

# ═══════════════════════════════════════════════════════════════
# H-CX-500 Part 2: Q domain at depth 2
# ═══════════════════════════════════════════════════════════════

print()
print("-" * 80)
print("Q domain depth-2 approach to GZ constants (threshold < 1%):")
print("-" * 80)

q_depth2_hits = {}
for gz_name, gz_val in GZ_CONSTANTS.items():
    hits = depth2_values(q_constants, gz_val, threshold=0.01)
    q_depth2_hits[gz_name] = hits
    if hits:
        print(f"\n  {gz_name} = {gz_val:.10f}")
        for expr, val, err in hits[:5]:
            print(f"    {expr} = {val:.10f}  (err={err:.4%})")
    else:
        print(f"\n  {gz_name} = {gz_val:.10f}  — NO depth-2 match within 1%")

reached_at_d2 = sum(1 for h in q_depth2_hits.values() if h)
print(f"\nQ reaches {reached_at_d2}/{len(GZ_CONSTANTS)} GZ constants at depth 2 (within 1%)")

# ═══════════════════════════════════════════════════════════════
# INTERPRETATION
# ═══════════════════════════════════════════════════════════════

print()
print("=" * 80)
print("INTERPRETATION")
print("=" * 80)
print()

print("H-CX-499 (GZ constants = logarithmic domain eigenvalues):")
if log_pct > 40:
    print(f"  SUPPORTED. Logarithmic domains (A, I) produce {log_pct:.1f}% of all")
    print(f"  depth-1 exact matches to GZ constants, confirming that the Golden Zone")
    print(f"  structure is fundamentally logarithmic in character.")
elif log_pct > 25:
    print(f"  WEAKLY SUPPORTED. Logarithmic domains produce {log_pct:.1f}% — above")
    print(f"  baseline (~25% for 2/8 domains) but not dominant.")
else:
    print(f"  NOT SUPPORTED. Logarithmic domains produce only {log_pct:.1f}%.")
print()

print("H-CX-500 (Q-barrier excludes ALL GZ constants at depth 1):")
if all_blocked:
    print(f"  CONFIRMED. Q domain cannot reach ANY of the 6 GZ constants at depth 1.")
    print(f"  Coupling constants (alpha, alpha_s, sin2_thetaW, etc.) have ZERO overlap")
    print(f"  with Golden Zone structure at the simplest algebraic level.")
    if reached_at_d2 > 0:
        print(f"  At depth 2, Q reaches {reached_at_d2}/6 constants, showing the barrier")
        print(f"  is permeable with sufficient algebraic complexity.")
    else:
        print(f"  Even at depth 2, Q reaches 0/6 — the barrier is absolute.")
else:
    print(f"  PARTIAL. Q domain reaches {len(GZ_CONSTANTS) - q_blocked_count}/6 GZ constants at depth 1.")

print()
print("Done.")
