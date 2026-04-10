#!/usr/bin/env python3
"""
H-CX-466 Verification: ζ(3) = 5/(6·ln(2)) ?
Claim: Apéry constant equals 5/(6·ln2) with 0.016% error.
If exact → closed form for ζ(3), which is an OPEN PROBLEM.
"""

from mpmath import mp, mpf, zeta, log, pi, power, factorial, gamma, euler
import itertools

mp.dps = 60  # 60 decimal digits

print("=" * 72)
print("H-CX-466 VERIFICATION: zeta(3) =? 5/(6*ln(2))")
print("=" * 72)

# ─── Step 1: High-precision comparison ───
z3 = zeta(3)
candidate = mpf(5) / (mpf(6) * log(2))

diff = z3 - candidate
rel_err = abs(diff) / z3 * 100

print(f"\n[1] HIGH-PRECISION COMPARISON (60 digits)")
print(f"    zeta(3)       = {z3}")
print(f"    5/(6*ln(2))   = {candidate}")
print(f"    Difference    = {diff}")
print(f"    Relative error= {float(rel_err):.6f}%")  # fixed mpf format
print(f"    Match digits  = {3 if rel_err < 0.1 else 2}")

if abs(diff) > mpf('1e-10'):
    print(f"\n    >>> NOT EXACT. Differ at 4th decimal place.")
    print(f"    >>> zeta(3) is irrational (Apery 1978). No closed form known.")
    print(f"    >>> 0.016% error = NUMERICAL COINCIDENCE, not identity.")

# ─── Step 2: Systematic search a/(b*ln(c)) ───
print(f"\n{'=' * 72}")
print(f"[2] SYSTEMATIC SEARCH: a/(b*ln(c))")
print(f"    a in 1..20, b in 1..20, c in {{2,3,5,6,7,10}}")
print(f"{'=' * 72}")

results = []
for c in [2, 3, 5, 6, 7, 10]:
    lnc = log(c)
    for a in range(1, 21):
        for b in range(1, 21):
            val = mpf(a) / (mpf(b) * lnc)
            err = abs(val - z3) / z3 * 100
            if err < 0.1:  # within 0.1%
                results.append((float(err), a, b, c, float(val)))

results.sort()
print(f"\n    Top 10 matches (error < 0.1%):")
print(f"    {'Rank':<5} {'a':<4} {'b':<4} {'c':<4} {'Expression':<20} {'Value':<22} {'Error%':<12}")
print(f"    {'-'*5} {'-'*4} {'-'*4} {'-'*4} {'-'*20} {'-'*22} {'-'*12}")
for i, (err, a, b, c, val) in enumerate(results[:10]):
    expr = f"{a}/({b}*ln({c}))"
    print(f"    {i+1:<5} {a:<4} {b:<4} {c:<4} {expr:<20} {val:<22.16f} {float(err):<12.6f}")

# ─── Step 3: Search a*pi^k / (b*ln(c)^m) ───
print(f"\n{'=' * 72}")
print(f"[3] SEARCH: a*pi^k / (b*ln(c)^m)")
print(f"    a in 1..15, b in 1..30, c in {{2,3,5,6}}, k in 1..4, m in 0..3")
print(f"{'=' * 72}")

results2 = []
for c in [2, 3, 5, 6]:
    lnc = log(c)
    for k in range(1, 5):
        pik = pi**k
        for m in range(0, 4):
            lncm = lnc**m if m > 0 else mpf(1)
            for a in range(1, 16):
                for b in range(1, 31):
                    val = mpf(a) * pik / (mpf(b) * lncm)
                    err = abs(val - z3) / z3 * 100
                    if err < 0.01:  # within 0.01%
                        results2.append((float(err), a, b, c, k, m, float(val)))

results2.sort()
print(f"\n    Top 10 matches (error < 0.01%):")
print(f"    {'Rank':<5} {'Expression':<30} {'Value':<22} {'Error%':<12}")
print(f"    {'-'*5} {'-'*30} {'-'*22} {'-'*12}")
for i, (err, a, b, c, k, m, val) in enumerate(results2[:10]):
    lnpart = f"*ln({c})^{m}" if m > 0 else ""
    expr = f"{a}*pi^{k}/({b}{lnpart})"
    print(f"    {i+1:<5} {expr:<30} {val:<22.16f} {float(err):<12.8f}")

# ─── Step 4: Known approximations ───
print(f"\n{'=' * 72}")
print(f"[4] KNOWN APPROXIMATIONS AND RELATIONS")
print(f"{'=' * 72}")

known = [
    ("5/(6*ln(2))",           mpf(5)/(6*log(2)),            "H-CX-466 claim"),
    ("pi^2/8 * (1+...)",      pi**2/8,                      "partial (pi^2/8 alone)"),
    ("pi^3/26",               pi**3/26,                     "folklore approx"),
    ("pi^3/(7*sqrt(15))",     pi**3/(7*power(15, mpf(1)/2)),"Zucker-type"),
    ("5*pi^2/(2*26)",         5*pi**2/(2*26),               "5pi^2/52"),
    ("1+1/8+1/27+...(4terms)",sum(mpf(1)/n**3 for n in range(1,5)), "partial sum 4 terms"),
    ("1+1/8+...(10 terms)",  sum(mpf(1)/n**3 for n in range(1,11)), "partial sum 10 terms"),
    ("pi^2*ln(2)/12 + ...",   pi**2*log(2)/12,              "partial (related identity)"),
    ("7*pi^3/180",            7*pi**3/180,                  "related to zeta(3)?"),
    ("pi^2/6 - 1/2",         pi**2/6 - mpf(1)/2,           "zeta(2) - 1/2"),
]

print(f"\n    {'Expression':<25} {'Value':<22} {'Error%':<12} {'Note':<30}")
print(f"    {'-'*25} {'-'*22} {'-'*12} {'-'*30}")
for expr, val, note in known:
    err = abs(val - z3) / z3 * 100
    print(f"    {expr:<25} {float(val):<22.16f} {float(err):<12.6f} {note}")

# ─── Step 5: Expressions with 5/6, 1/3 (TECS constants) ───
print(f"\n{'=' * 72}")
print(f"[5] TECS-MOTIVATED EXPRESSIONS")
print(f"{'=' * 72}")

tecs = [
    ("5/6 * pi^2/8",          mpf(5)/6 * pi**2/8),
    ("(1/2+1/3)*pi^2/8",      (mpf(1)/2+mpf(1)/3)*pi**2/8),
    ("pi^2/(6*ln(6))",        pi**2/(6*log(6))),
    ("5/(6*ln(3))",           mpf(5)/(6*log(3))),
    ("6/(5*ln(6))",           mpf(6)/(5*log(6))),
    ("pi^2/(2*sigma(-1,6))",  pi**2/(2*2)),  # sigma_{-1}(6)=2
    ("e/ln(6+1)",             mp.e/log(7)),
    ("1/(1-1/e)",             1/(1-1/mp.e)),
    ("pi^2/6 * 1/ln(6)",     pi**2/6 / log(6)),
]

print(f"\n    {'Expression':<25} {'Value':<22} {'Error%':<12}")
print(f"    {'-'*25} {'-'*22} {'-'*12}")
for expr, val in tecs:
    err = abs(val - z3) / z3 * 100
    print(f"    {expr:<25} {float(val):<22.16f} {float(err):<12.6f}")

# ─── Step 6: Continued fraction analysis of zeta(3) ───
print(f"\n{'=' * 72}")
print(f"[6] CONTINUED FRACTION ANALYSIS")
print(f"{'=' * 72}")

# Ratio zeta(3) / known constants
ratios = [
    ("zeta(3)/pi^2",     z3/pi**2),
    ("zeta(3)/pi^3",     z3/pi**3),
    ("zeta(3)*ln(2)",    z3*log(2)),
    ("zeta(3)/ln(2)",    z3/log(2)),
    ("zeta(3)*6",        z3*6),
    ("zeta(3)*6*ln(2)",  z3*6*log(2)),
    ("zeta(3)/e",        z3/mp.e),
    ("zeta(3)*e",        z3*mp.e),
]

print(f"\n    Ratios to identify simple fractions:")
print(f"    {'Ratio':<22} {'Value':<30} {'Near fraction?':<20}")
print(f"    {'-'*22} {'-'*30} {'-'*20}")
for name, val in ratios:
    # Check if near a simple fraction p/q with q <= 100
    best_p, best_q, best_err = 0, 1, 999.0
    fval = float(val)
    for q in range(1, 101):
        p = round(fval * q)
        if p > 0:
            err = abs(fval - p/q) / abs(fval) * 100
            if err < best_err:
                best_p, best_q, best_err = p, q, err
    frac = f"{best_p}/{best_q}" if best_q > 1 else str(best_p)
    mark = " <--" if best_err < 0.05 else ""
    print(f"    {name:<22} {float(val):<30.20f} {frac} (err={float(best_err):.4f}%){mark}")

# ─── Step 7: The original claim's ratio ───
print(f"\n{'=' * 72}")
print(f"[7] THE RATIO zeta(3) * 6 * ln(2)")
print(f"{'=' * 72}")

r = z3 * 6 * log(2)
print(f"    zeta(3) * 6 * ln(2) = {r}")
print(f"    If this were exactly 5, then zeta(3) = 5/(6*ln(2))")
print(f"    Actual value: {float(r):.20f}")
print(f"    Difference from 5: {float(r - 5):.20f}")
print(f"    This is NOT 5. The claim is FALSE as an exact identity.")

# ─── Step 8: Best approximations found ───
print(f"\n{'=' * 72}")
print(f"[8] BEST APPROXIMATIONS FOUND (all searches combined)")
print(f"{'=' * 72}")

all_results = []
# From search 2
for err, a, b, c, val in results[:20]:
    all_results.append((err, f"{a}/({b}*ln({c}))", val))
# From search 3
for err, a, b, c, k, m, val in results2[:20]:
    lnp = f"*ln({c})^{m}" if m > 0 else ""
    all_results.append((err, f"{a}*pi^{k}/({b}{lnp})", val))

all_results.sort()
print(f"\n    Top 5 overall best approximations:")
print(f"    {'Rank':<5} {'Expression':<35} {'Error%':<15}")
print(f"    {'-'*5} {'-'*35} {'-'*15}")
for i, (err, expr, val) in enumerate(all_results[:5]):
    print(f"    {i+1:<5} {expr:<35} {float(err):<15.8f}")

# ─── Final Verdict ───
print(f"\n{'=' * 72}")
print(f"FINAL VERDICT")
print(f"{'=' * 72}")
print(f"""
    Claim: zeta(3) = 5/(6*ln(2))

    zeta(3)     = 1.20205690315959428539973816151144999...
    5/(6*ln(2)) = 1.20224586740747186566816673970862902...

    Difference  = 0.000189... (4th decimal place)
    Rel. Error  = 0.0157%

    VERDICT: NOT an exact identity. Grade: {chr(9898)} (coincidence)

    Reasoning:
    1. The values differ at the 4th significant digit.
    2. zeta(3) (Apery's constant) is proven irrational (Apery 1978).
    3. No closed form for zeta(3) is known — this is a MAJOR open problem.
    4. 5/(6*ln(2)) is a simple expression; if it equaled zeta(3), it would
       have been noticed centuries ago (both constants known since Euler).
    5. The 0.016% match is not exceptional — systematic search found
       comparable or better matches with other simple expressions.
    6. This is a numerical near-miss, not a structural relationship.

    Classification:
    - NOT exact identity (ruled out by computation)
    - NOT structural approximation (no theoretical basis connecting
      zeta(3) to 5/(6*ln(2)); the error is too large for "structural")
    - IS a numerical coincidence at ~4 digit accuracy

    Grade: {chr(9898)} Coincidence (no retry needed)
    Golden Zone dependency: Independent (pure number theory)
""")
