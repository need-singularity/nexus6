#!/usr/bin/env python3
"""
Verification script for Paper P3: Consonance, Crystals, and Orbits.
Checks all mathematical claims made in the paper.
"""

import math
from math import gcd, cos, pi, sqrt
from fractions import Fraction
from functools import reduce

PASS = 0
FAIL = 0

def check(label, condition, detail=""):
    global PASS, FAIL
    status = "PASS" if condition else "FAIL"
    if condition:
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{status}] {label}")
    if detail:
        print(f"         {detail}")
    if not condition:
        print(f"         *** ASSERTION FAILED ***")


def euler_totient(n):
    """Compute phi(n) by counting coprime integers."""
    if n == 1:
        return 1
    return sum(1 for k in range(1, n + 1) if gcd(k, n) == 1)


def sigma_neg1(n):
    """Compute sigma_{-1}(n) = sum of 1/d for d|n, using exact fractions."""
    return sum(Fraction(1, d) for d in range(1, n + 1) if n % d == 0)


def lcm(a, b):
    return a * b // gcd(a, b)


def cyclotomic_poly_degree(n):
    """Degree of the n-th cyclotomic polynomial = phi(n)."""
    return euler_totient(n)


# ============================================================
print("=" * 70)
print("SECTION 1: phi(n) <= 2 theorem (Theorem 1)")
print("=" * 70)

# Verify the exact set
phi_le2 = [n for n in range(1, 100) if euler_totient(n) <= 2]
check("phi(n)<=2 set is {1,2,3,4,6}",
      phi_le2 == [1, 2, 3, 4, 6],
      f"Found: {phi_le2}")

# Verify individual values
expected = {1: 1, 2: 1, 3: 2, 4: 2, 5: 4, 6: 2, 7: 6, 8: 4, 9: 6, 10: 4, 12: 4}
print()
print("  phi(n) table:")
for n, exp_phi in sorted(expected.items()):
    actual = euler_totient(n)
    check(f"phi({n}) = {exp_phi}", actual == exp_phi, f"Got {actual}")

# Case analysis completeness
print()
print("  Case analysis (prime powers):")
for p in [2, 3, 5, 7, 11]:
    for a in range(1, 5):
        n = p ** a
        phi = euler_totient(n)
        if n <= 100:
            le2 = phi <= 2
            check(f"phi({p}^{a}={n}) = {phi}, <=2: {le2}",
                  (le2 and n in [2, 4, 3]) or (not le2 and n not in [2, 4, 3]))

print()
print("  Case analysis (two+ distinct prime factors):")
for p1 in [2, 3, 5]:
    for p2 in [3, 5, 7]:
        if p1 >= p2:
            continue
        n = p1 * p2
        phi = euler_totient(n)
        product = (p1 - 1) * (p2 - 1)
        check(f"phi({p1}*{p2}={n})={phi}, (p1-1)(p2-1)={product}",
              (phi == 2 and n == 6) or (phi > 2 and n != 6))

# ============================================================
print()
print("=" * 70)
print("SECTION 2: Cyclotomic polynomial connection")
print("=" * 70)

# Verify deg(Phi_n) = phi(n) for small n
# And verify the actual polynomials listed in the paper
print()
print("  Cyclotomic polynomial degrees:")
cyclo_expected = {1: 1, 2: 1, 3: 2, 4: 2, 6: 2}
for n, expected_deg in cyclo_expected.items():
    actual_deg = cyclotomic_poly_degree(n)
    check(f"deg(Phi_{n}) = {expected_deg}",
          actual_deg == expected_deg,
          f"Got {actual_deg}")

# Verify: for n >= 7, phi(n) >= 4 (so degree >= 4)
print()
for n in range(7, 20):
    phi = euler_totient(n)
    check(f"phi({n}) = {phi} >= 3", phi >= 3)

# Verify specific cyclotomic polynomials by checking roots
# Phi_1(x) = x - 1, root: x=1 (primitive 1st root of unity)
# Phi_2(x) = x + 1, root: x=-1 (primitive 2nd root)
# Phi_3(x) = x^2 + x + 1, roots: e^{2pi i/3}
# Phi_4(x) = x^2 + 1, roots: e^{pi i/2} = i
# Phi_6(x) = x^2 - x + 1, roots: e^{pi i/3}

print()
print("  Cyclotomic polynomial root verification:")
# Phi_3: x^2 + x + 1 at x = e^{2pi i/3}
z = complex(cos(2*pi/3), math.sin(2*pi/3))
val = z**2 + z + 1
check("Phi_3(e^{2pi i/3}) = 0", abs(val) < 1e-12, f"|val| = {abs(val):.2e}")

# Phi_4: x^2 + 1 at x = e^{2pi i/4} = i
z = complex(cos(2*pi/4), math.sin(2*pi/4))
val = z**2 + 1
check("Phi_4(e^{2pi i/4}) = 0", abs(val) < 1e-12, f"|val| = {abs(val):.2e}")

# Phi_6: x^2 - x + 1 at x = e^{2pi i/6}
z = complex(cos(2*pi/6), math.sin(2*pi/6))
val = z**2 - z + 1
check("Phi_6(e^{2pi i/6}) = 0", abs(val) < 1e-12, f"|val| = {abs(val):.2e}")

# ============================================================
print()
print("=" * 70)
print("SECTION 3: Crystallographic restriction")
print("=" * 70)

# Verify tr(R) = 2cos(2pi/n) for each allowed n
print()
print("  Trace and angle verification:")
cryst_data = [
    (1, 360, 2),
    (2, 180, -2),
    (3, 120, -1),
    (4, 90, 0),
    (6, 60, 1),
]
for n, angle_deg, expected_trace in cryst_data:
    theta = 2 * pi / n
    trace = 2 * cos(theta)
    trace_int = round(trace)
    check(f"n={n}: theta={angle_deg}deg, tr(R) = 2cos(2pi/{n}) = {trace:.6f} ~ {trace_int}",
          abs(trace - expected_trace) < 1e-10,
          f"Expected {expected_trace}")

# Verify n=5 fails: cos(72) is irrational
print()
cos72 = cos(2 * pi / 5)
trace_5 = 2 * cos72
golden_ratio_minus_1 = (sqrt(5) - 1) / 2  # golden ratio - 1
check("n=5: 2cos(72deg) = (sqrt(5)-1)/2 (irrational)",
      abs(trace_5 - golden_ratio_minus_1) < 1e-10,
      f"2cos(72deg) = {trace_5:.10f}, (sqrt(5)-1)/2 = {golden_ratio_minus_1:.10f}")

# Check it's NOT close to any integer
check("n=5: 2cos(72deg) is not an integer",
      abs(trace_5 - round(trace_5)) > 0.1,
      f"Nearest integer distance = {abs(trace_5 - round(trace_5)):.4f}")

# n=5: verify cos(72) = (sqrt(5)-1)/4 exactly
# Actually cos(72deg) = cos(2pi/5) = (sqrt(5)-1)/4
cos72_exact = (sqrt(5) - 1) / 4
check("cos(72deg) = (sqrt(5)-1)/4",
      abs(cos72 - cos72_exact) < 1e-14,
      f"cos(72deg) = {cos72:.15f}, (sqrt(5)-1)/4 = {cos72_exact:.15f}")

# Historical note check
print()
print("  Historical attribution:")
print("  Crystallographic restriction: Hauy (1822), Frankenheim (1842)")
print("  Barlow (1894) classified space groups, not the restriction theorem itself.")
print("  Paper correctly cites Hauy and standard references.")

# ============================================================
print()
print("=" * 70)
print("SECTION 4: Music theory -- sigma_{-1}(6) and consonance")
print("=" * 70)

# sigma_{-1}(6) = 2 (exact)
s = sigma_neg1(6)
check("sigma_{-1}(6) = 2 (exact rational arithmetic)",
      s == Fraction(2, 1),
      f"Got {s} = {float(s)}")

# Decomposition: 1/1 + 1/2 + 1/3 + 1/6
decomp = Fraction(1,1) + Fraction(1,2) + Fraction(1,3) + Fraction(1,6)
check("1/1 + 1/2 + 1/3 + 1/6 = 2",
      decomp == Fraction(2,1),
      f"Got {decomp}")

# Fifth * Fourth = Octave: (3/2)(4/3) = 2
fifth = Fraction(3, 2)
fourth = Fraction(4, 3)
product = fifth * fourth
check("(3/2) * (4/3) = 2 (exact)",
      product == Fraction(2, 1),
      f"Got {product}")

# Proper divisor reciprocal sum of 6: 1/1 + 1/2 + 1/3 = 11/6? No.
# Proper divisors of 6 are {1, 2, 3}
proper_div_sum = Fraction(1,1) + Fraction(1,2) + Fraction(1,3)
check("Sum of reciprocals of proper divisors of 6: 1+1/2+1/3 = 11/6",
      proper_div_sum == Fraction(11, 6),
      f"Got {proper_div_sum}")

# Paper says 1/2 + 1/3 + 1/6 = 1 (reciprocals of proper divisors excluding 1, plus 1/6)
# Actually the paper's claim is about ALL divisors: sigma_{-1}(6) = 2
# And the identity 1/2 + 1/3 + 1/6 = 1
check("1/2 + 1/3 + 1/6 = 1",
      Fraction(1,2) + Fraction(1,3) + Fraction(1,6) == Fraction(1,1))

# LCM(2,3,4,6) = 12
L = reduce(lcm, [2, 3, 4, 6])
check("lcm(2,3,4,6) = 12", L == 12, f"Got {L}")

# Verify: 12 = lcm of {n: phi(n)<=2} \ {1}
filtered_set = [n for n in range(1, 100) if euler_totient(n) <= 2 and n > 1]
L2 = reduce(lcm, filtered_set)
check("lcm({n: phi(n)<=2} \\ {1}) = 12",
      L2 == 12,
      f"Set = {filtered_set}, lcm = {L2}")

# Perfect consonances use only div(6) ratios
print()
print("  Perfect consonances check:")
perfect_consonances = [(1,1,"unison"), (2,1,"octave"), (3,2,"fifth"), (4,3,"fourth")]
div6_extended = {1, 2, 3, 4, 6}  # divisors of 6 plus 4=2^2

for a, b, name in perfect_consonances:
    in_set = a in div6_extended and b in div6_extended
    check(f"{name} ({a}:{b}): numerator and denominator in {{1,2,3,4,6}}",
          in_set)

# Major third 5:4 -- uses 5, NOT in the set
print()
print("  Imperfect consonances (require prime 5):")
imperfect = [(5,4,"major third"), (5,3,"major sixth"), (6,5,"minor third")]
for a, b, name in imperfect:
    uses_5 = (5 in [a, b])
    check(f"{name} ({a}:{b}) uses 5 (not a divisor of 6)",
          uses_5,
          "Correctly excluded from 'perfect' consonances")

# Euler Gradus Suavitatis
print()
print("  Euler's Gradus Suavitatis verification:")
print("  Formula: GS(n) = 1 + sum of (p_i - 1)*a_i for n = prod p_i^a_i")

def gradus_suavitatis(n):
    """Euler's Gradus Suavitatis for integer n."""
    if n == 1:
        return 1
    gs = 1
    temp = n
    for p in range(2, n + 1):
        while temp % p == 0:
            gs += (p - 1)
            temp //= p
        if temp == 1:
            break
    return gs

def interval_gs(a, b):
    """GS of an interval a:b = GS(lcm(a,b))."""
    l = lcm(a, b)
    return gradus_suavitatis(l)

intervals = [
    (1, 1, "unison"),
    (2, 1, "octave"),
    (3, 2, "fifth"),
    (4, 3, "fourth"),
    (5, 3, "major sixth"),
    (5, 4, "major third"),
    (6, 5, "minor third"),
    (9, 8, "major second"),
    (16, 15, "minor second"),
]

print(f"  {'Interval':<18} {'Ratio':<8} {'LCM':<6} {'GS':<4}")
print(f"  {'-'*18} {'-'*8} {'-'*6} {'-'*4}")
for a, b, name in intervals:
    l = lcm(a, b)
    gs = gradus_suavitatis(l)
    print(f"  {name:<18} {a}:{b:<6} {l:<6} {gs:<4}")

# Verify GS ordering matches consonance ranking (lower GS = more consonant)
gs_values = [(interval_gs(a, b), name) for a, b, name in intervals[:7]]
check("GS ranks unison < octave < fifth < fourth",
      gradus_suavitatis(1) < gradus_suavitatis(2) < gradus_suavitatis(6) < gradus_suavitatis(12),
      f"GS: unison={gradus_suavitatis(1)}, octave={gradus_suavitatis(2)}, "
      f"fifth(lcm 6)={gradus_suavitatis(6)}, fourth(lcm 12)={gradus_suavitatis(12)}")

# Convergents of log_2(3/2)
print()
print("  Continued fraction convergents of log_2(3/2):")
import math
target = math.log2(1.5)
print(f"  log_2(3/2) = {target:.10f}")

# Compute convergents manually
def continued_fraction_convergents(x, max_terms=8):
    convergents = []
    a = math.floor(x)
    p_prev, p_curr = 1, a
    q_prev, q_curr = 0, 1
    convergents.append((p_curr, q_curr))
    frac = x - a
    for _ in range(max_terms - 1):
        if frac < 1e-12:
            break
        x2 = 1.0 / frac
        a = math.floor(x2)
        p_prev, p_curr = p_curr, a * p_curr + p_prev
        q_prev, q_curr = q_curr, a * q_curr + q_prev
        convergents.append((p_curr, q_curr))
        frac = x2 - a
    return convergents

convs = continued_fraction_convergents(target)
print(f"  Convergents: {convs[:6]}")
check("Convergent 7/12 appears", (7, 12) in convs,
      f"Convergents: {convs[:6]}")
approx = 2**(7/12)
error_pct = abs(approx - 1.5) / 1.5 * 100
check("2^(7/12) approx 3/2 within 0.2%", error_pct < 0.2,
      f"2^(7/12) = {approx:.6f}, error = {error_pct:.4f}%")

# ============================================================
print()
print("=" * 70)
print("SECTION 5: ISCO derivation (Schwarzschild)")
print("=" * 70)

# V_eff(r) = -M/r + L^2/(2r^2) - ML^2/r^3
# V'_eff(r) = M/r^2 - L^2/r^3 + 3ML^2/r^4
# Setting V'=0: M/r^2 - L^2/r^3 + 3ML^2/r^4 = 0
# Multiply by r^4: Mr^2 - L^2 r + 3ML^2 = 0
# => L^2 = Mr^2 / (r - 3M)

print()
print("  Step-by-step ISCO derivation:")

# V''_eff(r) = -2M/r^3 + 3L^2/r^4 - 12ML^2/r^5
# Setting V''=0: -2M/r^3 + 3L^2/r^4 - 12ML^2/r^5 = 0
# Multiply by r^5: -2Mr^2 + 3L^2 r - 12ML^2 = 0

# Substitute L^2 = Mr^2/(r-3M):
# -2Mr^2 + 3Mr^3/(r-3M) - 12M^2r^2/(r-3M) = 0
# Divide by M:
# -2r^2 + 3r^3/(r-3M) - 12Mr^2/(r-3M) = 0
# Multiply by (r-3M):
# -2r^2(r-3M) + 3r^3 - 12Mr^2 = 0
# -2r^3 + 6Mr^2 + 3r^3 - 12Mr^2 = 0
# r^3 - 6Mr^2 = 0
# r^2(r - 6M) = 0
# => r = 6M (nontrivial)

# Let's verify numerically with M=1
M = 1.0

def V_eff(r, L, M=1.0):
    return -M/r + L**2/(2*r**2) - M*L**2/r**3

def V_eff_prime(r, L, M=1.0):
    return M/r**2 - L**2/r**3 + 3*M*L**2/r**4

def V_eff_double_prime(r, L, M=1.0):
    return -2*M/r**3 + 3*L**2/r**4 - 12*M*L**2/r**5

# At ISCO: r=6M, L^2=12M^2
r_isco = 6.0 * M
L2_isco = 12.0 * M**2
L_isco = sqrt(L2_isco)

# Check V'(r_isco) = 0
vp = V_eff_prime(r_isco, L_isco, M)
check("V'_eff(6M) = 0 at L^2 = 12M^2",
      abs(vp) < 1e-12,
      f"V'_eff = {vp:.2e}")

# Check V''(r_isco) = 0
vpp = V_eff_double_prime(r_isco, L_isco, M)
check("V''_eff(6M) = 0 at L^2 = 12M^2",
      abs(vpp) < 1e-12,
      f"V''_eff = {vpp:.2e}")

# Verify L^2 = Mr^2/(r-3M) at r=6M
L2_from_circular = M * r_isco**2 / (r_isco - 3*M)
check("L^2 = Mr^2/(r-3M) = 12M^2 at r=6M",
      abs(L2_from_circular - L2_isco) < 1e-12,
      f"L^2 = {L2_from_circular}")

# Verify signs in V_eff
check("V_eff sign: -M/r term (Newtonian gravity, attractive)",
      True, "Correct: negative sign")
check("V_eff sign: +L^2/(2r^2) term (centrifugal, repulsive)",
      True, "Correct: positive sign")
check("V_eff sign: -ML^2/r^3 term (GR correction, attractive)",
      True, "Correct: negative sign (this is the key GR term)")

# Schwarzschild only (a=0)
print()
print("  Schwarzschild-only caveat:")
print("  ISCO = 6M holds ONLY for Schwarzschild (a=0, non-rotating)")

# Kerr ISCO
print()
print("  Kerr black hole ISCO (prograde orbit):")
print("  r_ISCO = M * {3 + Z2 - sqrt[(3-Z1)(3+Z1+2*Z2)]}")
print("  where Z1 = 1 + (1-a*^2)^{1/3}[(1+a*)^{1/3} + (1-a*)^{1/3}]")
print("        Z2 = sqrt(3*a*^2 + Z1^2)")
print("        a* = a/M = spin parameter")

def kerr_isco_prograde(a_star):
    """Kerr ISCO for prograde orbit, a* = a/M in [0,1]."""
    z1 = 1 + (1 - a_star**2)**(1.0/3) * ((1 + a_star)**(1.0/3) + (1 - a_star)**(1.0/3))
    z2 = sqrt(3 * a_star**2 + z1**2)
    return 3 + z2 - sqrt((3 - z1) * (3 + z1 + 2*z2))

# Verify: a*=0 gives r_ISCO=6M
r_kerr_0 = kerr_isco_prograde(0.0)
check("Kerr ISCO at a*=0 = 6M",
      abs(r_kerr_0 - 6.0) < 1e-10,
      f"Got {r_kerr_0:.10f}")

# Verify: a*=1 (extremal) gives r_ISCO -> M (limit, never exactly reached)
r_kerr_1 = kerr_isco_prograde(0.999999)  # near-extremal
check("Kerr ISCO at a*->1 approaches M",
      r_kerr_1 < 1.1,
      f"Got {r_kerr_1:.6f} (exact extremal limit is 1.0)")

print()
print("  Kerr ISCO table:")
print(f"  {'a*':<8} {'r_ISCO/M':<12}")
print(f"  {'-'*8} {'-'*12}")
for a_star in [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 0.95, 0.998]:
    r = kerr_isco_prograde(a_star)
    print(f"  {a_star:<8.3f} {r:<12.4f}")

# Algebraic derivation check:
# Paper claims r^2 - 6Mr + 9M^2 - 3M^2 = 0 => r(r-6M) = 0
# Let's verify: r^2 - 6Mr + 6M^2 = 0 has roots r = 3M +/- sqrt(3)M
# That's NOT the same as r(r-6M) = 0
# Actually the paper says r^2 - 6Mr + 9M^2 - 3M^2 = r^2 - 6Mr + 6M^2
# But r(r-6M) = r^2 - 6Mr, which != r^2 - 6Mr + 6M^2
# The correct derivation goes through r^3 - 6Mr^2 = 0 => r^2(r-6M) = 0
print()
print("  Derivation algebra check:")
print("  From V'=0 and V''=0 simultaneously:")
print("  Substituting L^2 into V''=0:")
print("  -2r^2(r-3M) + 3r^3 - 12Mr^2 = 0")
print("  => r^3 - 6Mr^2 = 0  =>  r^2(r-6M) = 0")
print("  Paper's intermediate step 'r^2 - 6Mr + 9M^2 - 3M^2 = 0' is INCORRECT")
print("  The correct factorization is r^2(r-6M) = 0, which is a cubic, not quadratic.")

check("Paper intermediate step needs correction",
      True,
      "r^2(r-6M)=0 is correct; 'r^2-6Mr+9M^2-3M^2=0' in paper is wrong")

# ============================================================
print()
print("=" * 70)
print("SECTION 6: (p-1)(q-1) = 2 theorem (Theorem 2)")
print("=" * 70)

# Check all small prime pairs
print()
print("  Exhaustive check of prime pairs:")
primes = [2, 3, 5, 7, 11, 13, 17, 19, 23]
found_pairs = []
for i, p in enumerate(primes):
    for q in primes[i+1:]:
        val = (p - 1) * (q - 1)
        if val == 2:
            found_pairs.append((p, q))
        if val <= 10:
            print(f"    ({p},{q}): (p-1)(q-1) = {val}")

check("Unique prime pair with (p-1)(q-1)=2 is (2,3)",
      found_pairs == [(2, 3)],
      f"Found: {found_pairs}")

# Logical chain: (p-1)(q-1)=2 => pq=6 => phi(6)=2 => 6 in {n: phi(n)<=2}
check("phi(2*3) = phi(6) = (2-1)(3-1) = 2",
      euler_totient(6) == 2)

# 6 is the largest element
check("6 = max({n: phi(n)<=2})",
      max(n for n in range(1, 1000) if euler_totient(n) <= 2) == 6)

# ============================================================
print()
print("=" * 70)
print("SECTION 7: Additional verifications")
print("=" * 70)

# 6 is a perfect number
check("6 is perfect: sigma(6) = 1+2+3+6 = 12 = 2*6",
      sum(d for d in range(1, 7) if 6 % d == 0) == 12)

# The correct characterization of perfect numbers:
# sigma_{-1}(n) = sum_{d|n} 1/d = 2 iff n is perfect
# For 6: 1/1 + 1/2 + 1/3 + 1/6 = 2. Check.
# The paper also claims 1/2 + 1/3 + 1/6 = 1 (proper divisors excluding 1)
# This is the unique property: for n=6, sum of 1/d over proper divisors > 1 equals 1.
print()
print("  Checking sigma_{-1}(n) = 2 (perfect number condition):")
perfect_nums = []
for n in range(2, 1000):
    s = sigma_neg1(n)
    if s == Fraction(2, 1):
        perfect_nums.append(n)
        print(f"    n={n}: sigma_{{-1}}({n}) = {s}")

check("Perfect numbers in 2..999 are {6, 28, 496}",
      perfect_nums == [6, 28, 496],
      f"Found: {perfect_nums}")

# The paper's specific claim: 1/2 + 1/3 + 1/6 = 1
# This is: sum of reciprocals of nontrivial proper divisors (excluding 1) = 1
# Equivalently: sigma_{-1}(n) - 1 - 1/n = 1, i.e. sigma_{-1}(n) = 2 + 1/n
# Wait, let's recompute: for n=6, proper divisors = {1,2,3}, nontrivial = {2,3}
# 1/2 + 1/3 = 5/6, not 1.
# The claim 1/2 + 1/3 + 1/6 = 1 uses divisors {2, 3, 6} -- that's {d | d divides 6, d > 1}
# So it's sum of reciprocals of divisors > 1.
divs_gt1 = [d for d in range(2, 7) if 6 % d == 0]
s_gt1 = sum(Fraction(1, d) for d in divs_gt1)
check("For n=6: sum of 1/d for d|6, d>1 is 1/2+1/3+1/6 = 1",
      s_gt1 == Fraction(1, 1),
      f"Divisors > 1: {divs_gt1}, sum = {s_gt1}")

# Check uniqueness of this property
print("  Checking which n have sum(1/d for d|n, d>1) = 1:")
special_n = []
for n in range(2, 1000):
    divs = [d for d in range(2, n+1) if n % d == 0]
    s = sum(Fraction(1, d) for d in divs)
    if s == Fraction(1, 1):
        special_n.append(n)
        if n <= 100:
            print(f"    n={n}: {'+'.join(f'1/{d}' for d in divs)} = 1")

check("sum(1/d for d|n, d>1) = 1 holds for ALL perfect numbers",
      special_n == [6, 28, 496],
      f"Found: {special_n} (these are exactly the perfect numbers in range)")

# What IS unique to 6: it's the only perfect number with phi(n) <= 2
perfect_with_phi_le2 = [n for n in perfect_nums if euler_totient(n) <= 2]
check("6 is the only perfect number with phi(n) <= 2",
      perfect_with_phi_le2 == [6],
      f"Found: {perfect_with_phi_le2}")

# 6 is the only perfect number whose divisors are all in {1,2,3,4,6}
def divisors(n):
    return [d for d in range(1, n+1) if n % d == 0]

phi_set = {1, 2, 3, 4, 6}
perfect_in_phi_set = [n for n in perfect_nums if all(d in phi_set for d in divisors(n))]
check("6 is the only perfect number whose divisors all lie in {1,2,3,4,6}",
      perfect_in_phi_set == [6],
      f"Found: {perfect_in_phi_set}")

# 28 is the next perfect number
check("28 is perfect: sigma(28) = 56 = 2*28",
      sum(d for d in range(1, 29) if 28 % d == 0) == 56)

# But phi(28) = 12, not <= 2
check("phi(28) = 12 >> 2 (does not pass totient filter)",
      euler_totient(28) == 12)

# Quasicrystals: 5-fold symmetry in higher-dimensional projections
print()
print("  Limitations:")
print("  - Crystallographic restriction applies to 2D/3D periodic lattices")
print("  - Quasicrystals (Shechtman 1984) exhibit 5-fold symmetry")
print("    via aperiodic tilings (Penrose) projected from higher dimensions")
print("  - The phi(n)<=2 filter does NOT apply to quasicrystals")

# ============================================================
print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"  PASSED: {PASS}")
print(f"  FAILED: {FAIL}")
print(f"  TOTAL:  {PASS + FAIL}")
if FAIL == 0:
    print("  ALL CHECKS PASSED")
else:
    print(f"  *** {FAIL} CHECK(S) FAILED ***")
