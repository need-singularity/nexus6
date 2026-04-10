#!/usr/bin/env python3
"""
H-CX-476: {ζ(3), ln(2)} as Minimal Generator Pair
Verify generating relations and exhaustive search for best generator pairs/triples.
"""

from mpmath import mp, mpf, zeta, log, sqrt, euler, pi, exp, power, fabs
from itertools import combinations

mp.dps = 60  # 60 digits internal, report 50

# ============================================================
# 1. HIGH PRECISION VERIFICATION OF GENERATING RELATIONS
# ============================================================
print("=" * 70)
print("H-CX-476: {zeta(3), ln(2)} as Minimal Generator Pair")
print("=" * 70)

z3 = zeta(3)
ln2 = log(2)
gamma = euler
sqrt3 = sqrt(3)
five_sixths = mpf(5) / mpf(6)

print("\n--- Fundamental Constants (50 digits) ---")
print(f"  zeta(3)   = {mp.nstr(z3, 50)}")
print(f"  ln(2)     = {mp.nstr(ln2, 50)}")
print(f"  gamma     = {mp.nstr(gamma, 50)}")
print(f"  sqrt(3)   = {mp.nstr(sqrt3, 50)}")
print(f"  5/6       = {mp.nstr(five_sixths, 50)}")

print("\n--- Relation Verification ---")

relations = [
    ("zeta(3) * ln(2)", z3 * ln2, five_sixths, "5/6"),
    ("zeta(3) / ln(2)", z3 / ln2, sqrt3, "sqrt(3)"),
    ("zeta(3) * ln(2)^2", z3 * ln2**2, gamma, "gamma (Euler-Mascheroni)"),
    ("5/6 * ln(2)", five_sixths * ln2, gamma, "gamma (Euler-Mascheroni)"),
]

for name, computed, target, target_name in relations:
    diff = computed - target
    rel_err = fabs(diff / target) * 100
    print(f"\n  {name} =? {target_name}")
    print(f"    Computed: {mp.nstr(computed, 50)}")
    print(f"    Target:   {mp.nstr(target, 50)}")
    print(f"    Diff:     {mp.nstr(diff, 30)}")
    print(f"    Rel err:  {mp.nstr(rel_err, 10)}%")
    if rel_err < 0.001:
        tag = "EXTREMELY CLOSE"
    elif rel_err < 0.01:
        tag = "VERY CLOSE"
    elif rel_err < 0.1:
        tag = "CLOSE"
    elif rel_err < 1.0:
        tag = "APPROXIMATE"
    else:
        tag = "NOT CLOSE"
    print(f"    Verdict:  {tag}")

# ============================================================
# 2. KEY RELATION: gamma =? zeta(3) * ln(2)^2
# ============================================================
print("\n" + "=" * 70)
print("KEY RELATION DEEP ANALYSIS: gamma =? zeta(3) * ln(2)^2")
print("=" * 70)

prod = z3 * ln2**2
print(f"\n  zeta(3) * ln(2)^2 = {mp.nstr(prod, 50)}")
print(f"  gamma             = {mp.nstr(gamma, 50)}")
print(f"  Difference        = {mp.nstr(prod - gamma, 50)}")
print(f"  Ratio prod/gamma  = {mp.nstr(prod / gamma, 50)}")
print(f"  Rel error         = {mp.nstr(fabs(prod - gamma) / gamma * 100, 15)}%")

# Check if ratio is a simple fraction
ratio = prod / gamma
print(f"\n  Checking if ratio is a simple fraction p/q:")
for p in range(1, 30):
    for q in range(1, 30):
        if fabs(ratio - mpf(p)/mpf(q)) < mpf('1e-4'):
            err = fabs(ratio - mpf(p)/mpf(q))
            print(f"    {p}/{q} = {mp.nstr(mpf(p)/mpf(q), 15)}, err = {mp.nstr(err, 10)}")

print(f"\n  Known relation status:")
print(f"    gamma, zeta(3), and ln(2) are all related to the Riemann zeta function")
print(f"    but NO exact algebraic relation gamma = zeta(3)*ln(2)^2 is known.")
print(f"    The 0.057% proximity is a numerical near-miss, not an identity.")

# ============================================================
# 3. EXHAUSTIVE GENERATOR PAIR SEARCH
# ============================================================
print("\n" + "=" * 70)
print("EXHAUSTIVE GENERATOR PAIR SEARCH: C(9,2) = 36 pairs")
print("=" * 70)

# Define 9 convergence points
constants = {
    "1/e":       1/exp(1),
    "ln(4/3)":   log(mpf(4)/3),
    "1/3":       mpf(1)/3,
    "1/2":       mpf(1)/2,
    "5/6":       mpf(5)/6,
    "gamma":     gamma,
    "zeta(3)":   z3,
    "ln(2)":     ln2,
    "sqrt(3)":   sqrt3,
}

names = list(constants.keys())
vals = list(constants.values())

def count_generated(pair_indices, threshold=0.005):
    """Given generator indices, count how many OTHER constants are generated
    by depth-1 operations: a+b, a-b, b-a, a*b, a/b, b/a, a^b, b^a"""
    gens = [vals[i] for i in pair_indices]
    generated_products = set()

    # All depth-1 binary ops between all pairs of generators
    gen_vals = []
    for i, a in enumerate(gens):
        for j, b in enumerate(gens):
            if i == j:
                continue
            gen_vals.extend([a+b, a-b, a*b, a/b])
            if fabs(b) < 10 and fabs(a) > 0:
                try:
                    gen_vals.append(power(a, b))
                except:
                    pass
    # Also include generators themselves
    for g in gens:
        gen_vals.append(g)

    matched = set()
    for idx in range(len(vals)):
        if idx in pair_indices:
            continue
        target = vals[idx]
        if fabs(target) < mpf('1e-30'):
            continue
        for gv in gen_vals:
            if fabs(gv) < mpf('1e-30'):
                continue
            rel = fabs((gv - target) / target)
            if rel < threshold:
                matched.add(idx)
                break
    return matched

print(f"\n  Threshold: 0.5% relative error")
print(f"  Constants: {names}")
print(f"\n  {'Pair':<30} {'Matched':>7}  Targets")
print(f"  {'-'*30} {'-'*7}  {'-'*30}")

pair_results = []
for i, j in combinations(range(len(names)), 2):
    matched = count_generated([i, j], threshold=0.005)
    matched_names = [names[k] for k in matched]
    pair_results.append((len(matched), names[i], names[j], matched_names))

pair_results.sort(key=lambda x: -x[0])

for count, a, b, targets in pair_results[:15]:
    pair_str = f"{{{a}, {b}}}"
    print(f"  {pair_str:<30} {count:>7}  {targets}")

print(f"\n  BEST PAIR: {{{pair_results[0][1]}, {pair_results[0][2]}}} -> {pair_results[0][0]} matches")

# ============================================================
# 4. EXHAUSTIVE GENERATOR TRIPLE SEARCH
# ============================================================
print("\n" + "=" * 70)
print("EXHAUSTIVE GENERATOR TRIPLE SEARCH: C(9,3) = 84 triples")
print("=" * 70)

triple_results = []
for i, j, k in combinations(range(len(names)), 3):
    matched = count_generated([i, j, k], threshold=0.005)
    matched_names = [names[m] for m in matched]
    triple_results.append((len(matched), names[i], names[j], names[k], matched_names))

triple_results.sort(key=lambda x: -x[0])

print(f"\n  {'Triple':<40} {'Matched':>7}  Targets")
print(f"  {'-'*40} {'-'*7}  {'-'*30}")

for count, a, b, c, targets in triple_results[:15]:
    triple_str = f"{{{a}, {b}, {c}}}"
    print(f"  {triple_str:<40} {count:>7}  {targets}")

print(f"\n  BEST TRIPLE: {{{triple_results[0][1]}, {triple_results[0][2]}, {triple_results[0][3]}}} -> {triple_results[0][0]} matches")

# ============================================================
# 5. CAN {zeta(3), ln(2)} GENERATE sqrt(2), e, 1/2, GZ_width?
# ============================================================
print("\n" + "=" * 70)
print("EXTENDED GENERATION TEST: {zeta(3), ln(2)} -> other constants?")
print("=" * 70)

extra_targets = {
    "sqrt(2)":   sqrt(2),
    "e":         exp(1),
    "1/2":       mpf(1)/2,
    "GZ_width":  log(mpf(4)/3),
    "pi":        pi,
    "1/3":       mpf(1)/3,
    "5/6":       mpf(5)/6,
    "1/e":       1/exp(1),
    "gamma":     gamma,
    "sqrt(3)":   sqrt3,
}

# Depth-1: a op b
depth1 = {
    "z3 + ln2": z3 + ln2,
    "z3 - ln2": z3 - ln2,
    "ln2 - z3": ln2 - z3,
    "z3 * ln2": z3 * ln2,
    "z3 / ln2": z3 / ln2,
    "ln2 / z3": ln2 / z3,
    "z3 ^ ln2": power(z3, ln2),
    "ln2 ^ z3": power(ln2, z3),
    "z3 * ln2^2": z3 * ln2**2,
    "z3^2 * ln2": z3**2 * ln2,
    "z3 / ln2^2": z3 / ln2**2,
    "z3^2 / ln2": z3**2 / ln2,
    "z3^2": z3**2,
    "ln2^2": ln2**2,
    "1/z3": 1/z3,
    "1/ln2": 1/ln2,
    "z3+ln2^2": z3 + ln2**2,
    "z3-ln2^2": z3 - ln2**2,
}

# Depth-2: (a op b) op (c op d) where a,b,c,d in {z3, ln2}
d1_items = list(depth1.items())
depth2 = {}
for n1, v1 in d1_items:
    for n2, v2 in d1_items:
        if n1 == n2:
            continue
        for op_name, op_fn in [("+", lambda a,b: a+b), ("-", lambda a,b: a-b),
                                ("*", lambda a,b: a*b), ("/", lambda a,b: a/b if fabs(b)>1e-30 else None)]:
            result = op_fn(v1, v2)
            if result is not None:
                depth2[f"({n1}) {op_name} ({n2})"] = result

print(f"\n  Depth-1 expressions: {len(depth1)}")
print(f"  Depth-2 expressions: {len(depth2)}")

all_exprs = {**depth1, **depth2}

print(f"\n  {'Target':<12} {'Best Match':<45} {'Rel Err':>12}")
print(f"  {'-'*12} {'-'*45} {'-'*12}")

for tname, tval in extra_targets.items():
    best_err = mpf('1e10')
    best_expr = ""
    for ename, eval_ in all_exprs.items():
        if eval_ is None or fabs(eval_) < mpf('1e-30'):
            continue
        rel = fabs((eval_ - tval) / tval)
        if rel < best_err:
            best_err = rel
            best_expr = ename
    pct = best_err * 100
    tag = ""
    if pct < 0.01:
        tag = " *** EXACT"
    elif pct < 0.1:
        tag = " ** VERY CLOSE"
    elif pct < 1.0:
        tag = " * CLOSE"
    print(f"  {tname:<12} {best_expr:<45} {mp.nstr(pct, 6):>10}%{tag}")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("""
  1. zeta(3) * ln(2)   ~ 5/6      : ~0.016% error (very close)
  2. zeta(3) / ln(2)   ~ sqrt(3)  : ~0.12% error (close)
  3. zeta(3) * ln(2)^2 ~ gamma    : ~0.057% error (close but NOT exact)
  4. 5/6 * ln(2)       ~ gamma    : ~0.07% error (follows from #1 and #3)

  KEY FINDING: gamma = zeta(3) * ln(2)^2 is NOT an exact identity.
  No such relation is known in the literature. The ~0.057% proximity
  is a numerical near-miss among transcendental constants.

  The exhaustive pair/triple search results above reveal whether
  {zeta(3), ln(2)} is truly the best minimal generator pair.
""")

print("Done.")
