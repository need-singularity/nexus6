#!/usr/bin/env python3
"""
H-CX-465 Verification: gamma * sqrt(3) ≈ 1
Does Euler-Mascheroni gamma = 1/sqrt(3)? (Would be a closed form — open problem)
"""

from mpmath import mp, mpf, sqrt, log, pi, euler, e as E, fabs

mp.dps = 60  # 60 decimal digits internal, display 50

print("=" * 72)
print("H-CX-465 VERIFICATION: gamma x sqrt(3) =? 1")
print("=" * 72)

gamma = euler
sqrt3 = sqrt(3)
sqrt2 = sqrt(2)
ln2 = log(2)

print(f"\n[1] HIGH-PRECISION VALUES (50 digits)")
print(f"  gamma  = {mp.nstr(gamma, 50)}")
print(f"  sqrt3  = {mp.nstr(sqrt3, 50)}")
print(f"  1/sqrt3= {mp.nstr(1/sqrt3, 50)}")

print(f"\n[2] gamma x sqrt(3) at 50-digit precision")
product = gamma * sqrt3
print(f"  gamma * sqrt(3) = {mp.nstr(product, 50)}")
deviation = product - 1
print(f"  deviation from 1 = {mp.nstr(deviation, 20)}")
pct_error = float(fabs(deviation)) * 100
print(f"  |error|           = {pct_error:.6f}%")
print(f"  Claimed 0.023%    -> Actual: {pct_error:.4f}%")

print(f"\n[3] gamma vs 1/sqrt(3): exact gap")
gap = gamma - 1/sqrt3
print(f"  gamma - 1/sqrt(3) = {mp.nstr(gap, 50)}")
print(f"  |gap|/gamma       = {float(fabs(gap)/gamma)*100:.6f}%")
print(f"  Is gamma EXACTLY 1/sqrt(3)? {'YES' if gap == 0 else 'NO'}")
if gap != 0:
    print(f"  Gap starts at digit: the values differ immediately")

print(f"\n[4] KNOWN NEAR-MISS APPROXIMATIONS involving sqrt(3)")
print(f"  {'Expression':<35} {'Value':>22} {'Error%':>12} {'ppm':>10}")
print(f"  {'-'*35} {'-'*22} {'-'*12} {'-'*10}")

approximations = [
    ("1/sqrt(3)",              1/sqrt3),
    ("sqrt(3)/3",              sqrt3/3),
    ("(sqrt(3)-1)/sqrt(e)",    (sqrt3 - 1)/sqrt(E)),
    ("ln(sqrt(3)) = ln(3)/2", log(sqrt3)),
    ("1/(sqrt(3) + 1/pi)",    1/(sqrt3 + 1/pi)),
    ("(sqrt(3)-1)/(sqrt(3)+1)", (sqrt3-1)/(sqrt3+1)),
    ("sqrt(3) - 1",           sqrt3 - 1),
    ("sqrt(3)/pi",            sqrt3/pi),
    ("pi/sqrt(3)/pi",         1/sqrt3),  # same as 1/sqrt3
    ("(sqrt(3)-1)/2",         (sqrt3-1)/2),
    ("ln(3)/2 - 1/12",        log(3)/2 - mpf(1)/12),
    ("sqrt(3) - pi/e",        sqrt3 - pi/E),
]

results = []
for name, val in approximations:
    err = float(fabs(val - gamma) / gamma) * 100
    ppm = err * 10000
    results.append((name, val, err, ppm))
    print(f"  {name:<35} {mp.nstr(val, 18):>22} {err:>11.6f}% {ppm:>9.1f}")

print(f"\n[5] SEARCH: Best simple expression for gamma (target: <0.001% error)")
print(f"  Searching combinations of sqrt(3), sqrt(2), ln(2), pi, e, integers...")

# Systematic search
candidates = []

# a*sqrt(3) + b forms
for a_num in range(-5, 6):
    for a_den in range(1, 13):
        for b_num in range(-10, 11):
            for b_den in range(1, 13):
                a = mpf(a_num) / a_den
                b = mpf(b_num) / b_den
                val = a * sqrt3 + b
                if val > 0:
                    err = float(fabs(val - gamma) / gamma)
                    if err < 1e-5:  # < 0.001%
                        candidates.append((f"({a_num}/{a_den})*sqrt(3) + ({b_num}/{b_den})", val, err*100))

# a/sqrt(b) forms already covered in Texas test below

# Combinations with pi, ln2
special_bases = {
    "sqrt(3)": sqrt3, "sqrt(2)": sqrt2, "ln(2)": ln2,
    "pi": pi, "1/pi": 1/pi, "1/e": 1/E,
    "sqrt(3)/pi": sqrt3/pi, "pi/sqrt(3)": pi/sqrt3,
    "ln(2)*sqrt(3)": ln2*sqrt3, "sqrt(2)/sqrt(3)": sqrt2/sqrt3,
    "pi*ln(2)": pi*ln2, "sqrt(6)": sqrt(6),
}

for name1, v1 in special_bases.items():
    for p in range(-3, 4):
        for q in range(1, 7):
            val = v1 * mpf(p) / q
            if val > 0:
                err = float(fabs(val - gamma) / gamma)
                if err < 1e-5:
                    candidates.append((f"{p}/{q} * {name1}", val, err*100))

# More exotic: a*X + b*Y
combos = [
    ("sqrt(3)", sqrt3), ("sqrt(2)", sqrt2), ("ln(2)", ln2),
    ("1/pi", 1/pi), ("1/e", 1/E),
]
for i, (n1, v1) in enumerate(combos):
    for n2, v2 in combos[i+1:]:
        for a in range(-5, 6):
            for b in range(-5, 6):
                for d in range(1, 7):
                    val = (a * v1 + b * v2) / d
                    if val > 0:
                        err = float(fabs(val - gamma) / gamma)
                        if err < 1e-5:
                            candidates.append((f"({a}*{n1} + {b}*{n2})/{d}", val, err*100))

# Sort by error
candidates.sort(key=lambda x: x[2])
# Deduplicate by rounding value
seen = set()
unique = []
for name, val, err in candidates:
    key = mp.nstr(val, 12)
    if key not in seen:
        seen.add(key)
        unique.append((name, val, err))

print(f"\n  Top 15 best approximations (error < 0.001%):")
print(f"  {'Expression':<45} {'Error%':>12} {'ppm':>8}")
print(f"  {'-'*45} {'-'*12} {'-'*8}")
for name, val, err in unique[:15]:
    print(f"  {name:<45} {err:>11.7f}% {err*10000:>7.2f}")

print(f"\n[6] TEXAS SHARPSHOOTER TEST")
print(f"  Among a/sqrt(b) for a in 1..10, b in {{2,3,5,6,7}}:")
print(f"  How many approximate gamma within 0.023%?")

threshold = 0.00023  # 0.023%
hits = []
total = 0
for a in range(1, 11):
    for b in [2, 3, 5, 6, 7]:
        val = mpf(a) / sqrt(b)
        err = float(fabs(val - gamma) / gamma)
        total += 1
        if err < threshold:
            hits.append((a, b, val, err*100))

print(f"\n  Total candidates tested: {total}")
print(f"  Hits within 0.023%: {len(hits)}")
if hits:
    for a, b, val, err in hits:
        print(f"    {a}/sqrt({b}) = {mp.nstr(val, 15):<20} error = {err:.6f}%")
else:
    print(f"    (none)")

# Broader Texas test: a*sqrt(b)/c for small integers
print(f"\n  Broader test: a*sqrt(b)/c for a in 1..5, b in 2..7, c in 1..10:")
hits2 = []
total2 = 0
for a in range(1, 6):
    for b in range(2, 8):
        for c in range(1, 11):
            val = mpf(a) * sqrt(b) / c
            err = float(fabs(val - gamma) / gamma)
            total2 += 1
            if err < threshold:
                hits2.append((a, b, c, val, err*100))

print(f"  Total candidates: {total2}")
print(f"  Hits within 0.023%: {len(hits2)}")
for a, b, c, val, err in hits2:
    print(f"    {a}*sqrt({b})/{c} = {mp.nstr(val, 15):<20} error = {err:.6f}%")

# Expected hits by chance
import random
expected_rate = threshold * 2  # fraction of real line within 0.023% of gamma
print(f"\n  Expected hit rate (uniform): ~{expected_rate*100:.3f}% of candidates")
print(f"  Expected hits in {total} trials: ~{total * expected_rate:.2f}")
print(f"  Expected hits in {total2} trials: ~{total2 * expected_rate:.2f}")
print(f"  Actual hits: {len(hits)} (narrow), {len(hits2)} (broad)")

if len(hits) <= 1:
    print(f"\n  => 1/sqrt(3) is the ONLY hit in narrow test.")
    print(f"     But this is expected: ~{total*expected_rate:.1f} hits expected by chance.")
    if total * expected_rate >= 0.5:
        print(f"     NOT statistically surprising (p ~ {1 - (1-expected_rate)**total:.3f})")
    else:
        print(f"     Mildly notable but still plausible by chance.")

print(f"\n{'=' * 72}")
print(f"VERDICT")
print(f"{'=' * 72}")
print(f"""
  gamma * sqrt(3) = {mp.nstr(product, 20)}
  Error from 1    = {pct_error:.4f}%  (claimed 0.023% -- {'CONFIRMED' if abs(pct_error - 0.023) < 0.01 else 'DIFFERS'})

  Is gamma = 1/sqrt(3)?  NO.
  The gap is {mp.nstr(fabs(gap), 10)} -- nonzero from the very first digits.

  gamma is NOT known to have any closed form. If gamma = 1/sqrt(3),
  that would solve a major open problem. The 0.02% proximity is a
  NUMERICAL COINCIDENCE, not an identity.

  Grade: The approximation gamma ≈ 1/sqrt(3) has ~0.02% error.
  This is a known near-miss. It is NOT special among simple expressions.

  Texas Sharpshooter: With {total2} candidates of form a*sqrt(b)/c,
  we expect ~{total2*expected_rate:.1f} hits within 0.023%. Getting {len(hits2)} is
  {'unremarkable' if len(hits2) <= max(2, total2*expected_rate*3) else 'notable'}.
""")
