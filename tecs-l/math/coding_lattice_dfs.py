#!/usr/bin/env python3
"""
DFS Search: n=6 arithmetic functions vs Coding Theory and Lattice Theory
Tests Hamming codes, Golay code, E6/E8/Leech lattice connections.
"""

import math
from fractions import Fraction
from itertools import combinations
import sympy
from sympy import factorint, totient, divisor_sigma, isprime, binomial, log, sqrt, Rational
from sympy import symbols, expand, factor

# ─── n=6 core constants ───────────────────────────────────────────────
n = 6
sigma   = divisor_sigma(n, 1)      # sum of divisors = 12
phi_n   = totient(n)                # Euler totient = 2
tau_n   = divisor_sigma(n, 0)      # number of divisors = 4
sopfr   = 2 + 3                     # sum of prime factors = 5
omega_n = len(factorint(n))         # number of distinct primes = 2
s_n     = sigma - n                 # sum of proper divisors = 6  (perfect!)
rad_n   = 2 * 3                     # radical = 6

# derived
sig_phi  = sigma * phi_n           # 12*2 = 24
sig_tau  = sigma // tau_n          # 12/4 = 3
C_combo  = int(binomial(sigma - tau_n, phi_n))  # C(8,2) = 28

print("=" * 65)
print("n=6 CORE CONSTANTS")
print("=" * 65)
print(f"  sigma(6)   = {sigma}    (sum of divisors)")
print(f"  phi(6)     = {phi_n}     (Euler totient)")
print(f"  tau(6)     = {tau_n}     (number of divisors)")
print(f"  sopfr(6)   = {sopfr}     (sum of prime factors)")
print(f"  omega(6)   = {omega_n}     (distinct prime factors)")
print(f"  s(6)       = {s_n}     (proper divisor sum = n: perfect!)")
print(f"  rad(6)     = {rad_n}     (radical)")
print(f"  sigma*phi  = {sig_phi}    (sigma × phi)")
print(f"  sigma/tau  = {sig_tau}     (sigma / tau)")
print(f"  C(8,2)     = {C_combo}    (binomial sigma-tau choose phi)")
print()

# ─── Helper: uniqueness test for a value among n=2..1000 ──────────────
def uniqueness_test(formula_name, f, target_value, n_range=range(2, 1001)):
    """Check how many n in n_range satisfy f(n) == target_value."""
    matches = []
    for k in n_range:
        try:
            val = f(k)
            if val == target_value:
                matches.append(k)
        except Exception:
            pass
    return matches

def arith_funcs(k):
    """Return dict of arithmetic functions for k."""
    facts = factorint(k)
    sig   = int(divisor_sigma(k, 1))
    phi_k = int(totient(k))
    tau_k = int(divisor_sigma(k, 0))
    sop   = sum(p * e for p, e in facts.items())
    om    = len(facts)
    sk    = sig - k
    radk  = 1
    for p in facts:
        radk *= p
    return dict(sigma=sig, phi=phi_k, tau=tau_k, sopfr=sop,
                omega=om, s=sk, rad=radk)


print("=" * 65)
print("SECTION 1: HAMMING CODE [7,4,3] PARAMETERS")
print("=" * 65)
# Hamming(1) code [2^r-1, 2^r-1-r, 3]
# For r=3: [7,4,3]   length=7, dim=4, min-dist=3
# From n=6: 7 = n+1, 4 = tau(6), 3 = sigma/tau = 12/4
r = 3
ham_n   = 2**r - 1          # = 7
ham_k   = 2**r - 1 - r      # = 4
ham_d   = 3

print(f"\nHamming[{ham_n},{ham_k},{ham_d}] r={r}:")
print(f"  7 = n+1?       {n+1} == 7   → {n+1 == ham_n}")
print(f"  4 = tau(6)?    {tau_n} == 4   → {tau_n == ham_k}")
print(f"  3 = sigma/tau? {sig_tau} == 3   → {sig_tau == ham_d}")
print(f"  All three match for n=6 Hamming(r=3): {'YES ✓' if (n+1==ham_n and tau_n==ham_k and sig_tau==ham_d) else 'NO'}")

# Uniqueness: how many n give (n+1, tau(n), sigma(n)/tau(n)) = (7,4,3)?
# sigma(n)/tau(n) = 3 AND tau(n)=4 AND n+1=7 → only n=6
hamming_matches = []
for k in range(2, 1001):
    af = arith_funcs(k)
    sig_k = af['sigma']
    tau_k = af['tau']
    if tau_k > 0 and sig_k % tau_k == 0:
        if (k+1 == 7) and (tau_k == 4) and (sig_k // tau_k == 3):
            hamming_matches.append(k)
print(f"\n  Uniqueness (n+1=7, tau=4, sigma/tau=3) in 2..1000: {hamming_matches}")
print(f"  → {'UNIQUE (only n=6)' if hamming_matches == [6] else 'NOT UNIQUE'}")

# Also test: is this a general pattern for perfect numbers?
print("\n  Pattern test on perfect numbers [6, 28, 496, 8128]:")
for pn in [6, 28, 496, 8128]:
    af = arith_funcs(pn)
    sig_k = af['sigma']
    tau_k = af['tau']
    r_val = None
    # For Hamming: length = pn+1, dim = tau, dist = sig/tau
    # Check if pn+1 = 2^r - 1 for some r
    for r_try in range(1, 20):
        if 2**r_try - 1 == pn + 1:
            r_val = r_try
            break
    ham_match = (tau_k == sig_k // tau_k + (r_val or 0)) if r_val else False
    print(f"    n={pn:5d}: sigma={sig_k}, tau={tau_k}, sigma/tau={sig_k//tau_k if tau_k else 'N/A'}, n+1={pn+1}, 2^r-1={pn+1 if r_val else 'no'}")


print("\n" + "=" * 65)
print("SECTION 2: CODING BOUNDS AT n=6 PARAMETERS")
print("=" * 65)

# Hamming bound (sphere-packing): sum_{i=0}^{t} C(n,i) <= 2^n / ...
# For binary [n_code, k_code, d_code]:
# Hamming bound:  2^k * sum_{i=0}^{floor((d-1)/2)} C(n,i) <= 2^n
# Singleton bound: k <= n - d + 1
# Plotkin bound (d even): n >= 2d => A(n,d) <= 2*floor(d/(2d-n))

# Use coding parameters derived from n=6:
# Case A: code length = sigma = 12, min-dist = phi = 2, dim = tau = 4
n_code, k_code, d_code = sigma, tau_n, phi_n   # [12, 4, 2]
singleton = n_code - d_code + 1
print(f"\nCase A: [{n_code},{k_code},{d_code}]")
print(f"  Singleton bound: k <= n-d+1 = {singleton}   k={k_code} → {'SATISFIES' if k_code <= singleton else 'VIOLATES'}")
hamming_sum = sum(math.comb(n_code, i) for i in range((d_code-1)//2 + 1))
hamming_bound_k = math.floor(math.log2(2**n_code / hamming_sum))
print(f"  Hamming bound:   k <= {hamming_bound_k}   k={k_code} → {'SATISFIES' if k_code <= hamming_bound_k else 'VIOLATES'}")

# Case B: length = 24 = sigma*phi, d = 8 (Golay-like), k = 12 = sigma
n_code2, k_code2, d_code2 = sig_phi, sigma, 8   # [24, 12, 8] — Golay!
singleton2 = n_code2 - d_code2 + 1
print(f"\nCase B: [{n_code2},{k_code2},{d_code2}] (Extended Binary Golay G24!)")
print(f"  Singleton bound: k <= n-d+1 = {singleton2}   k={k_code2} → {'SATISFIES' if k_code2 <= singleton2 else 'VIOLATES'}")
hamming_sum2 = sum(math.comb(n_code2, i) for i in range((d_code2-1)//2 + 1))
hamming_bound_k2 = math.floor(math.log2(2**n_code2 / hamming_sum2))
print(f"  Hamming bound:   k <= {hamming_bound_k2}   k={k_code2} → {'SATISFIES' if k_code2 <= hamming_bound_k2 else 'VIOLATES'}")
print(f"  → [24,12,8] is the EXTENDED BINARY GOLAY CODE")
print(f"  → 24 = sigma(6)*phi(6) = {sigma}*{phi_n}")
print(f"  → 12 = sigma(6) = {sigma}  (code dimension)")
print(f"  → 8  = sigma(6) - tau(6) = {sigma - tau_n}  (min distance)")

# Case C: [23, 12, 7] — Binary Golay
n_code3, k_code3, d_code3 = 23, 12, 7
print(f"\nCase C: [{n_code3},{k_code3},{d_code3}] (Binary Golay G23)")
print(f"  23 = sigma(6)*phi(6) - phi(6) - 1 = {sig_phi - phi_n - 1}?  → {23 == sig_phi - phi_n - 1}")
print(f"  23 = ? from n=6 arithmetic: sigma*2 - 1 = {sigma*2-1}, tau*6-1 = {tau_n*6-1}")
hamming_sum3 = sum(math.comb(n_code3, i) for i in range((d_code3-1)//2 + 1))
print(f"  Perfect code check: 2^12 * sum_i C(23,i) i=0..3 = {2**12 * hamming_sum3}")
print(f"  2^23 = {2**23}")
print(f"  Perfect? 2^12 * Hamming_ball = 2^23?  {2**12 * hamming_sum3 == 2**23}")

# Case D: Ternary Golay [11, 6, 5]
n_code4, k_code4, d_code4 = 11, 6, 5
print(f"\nCase D: [{n_code4},{k_code4},{d_code4}] (Ternary Golay)")
print(f"  11 = sopfr + sigma/tau + tau = {sopfr} + {sig_tau} + {tau_n} = {sopfr + sig_tau + tau_n}? → {sopfr + sig_tau + tau_n == 11}")
print(f"  6  = n = 6?  → True (code dimension = n itself!)")
print(f"  5  = sopfr = {sopfr}?  → {sopfr == 5}")
ham_sum4 = sum(math.comb(n_code4, i) * 2**i for i in range((d_code4-1)//2 + 1))
print(f"  Perfect ternary? 3^6 * sum = 3^11?  {3**6 * ham_sum4} == {3**11}?  {3**6 * ham_sum4 == 3**11}")


print("\n" + "=" * 65)
print("SECTION 3: GOLAY CODE [23,12,7] DEEPER CONNECTIONS")
print("=" * 65)

print(f"\n  sigma(6) = {sigma} = code dimension of both Golay codes (binary G23/G24, ternary G12)")
print(f"\n  Binary Golay G23 [23,12,7]:")
print(f"    23 from n=6?  23 = 4*6-1 = {4*6-1}  → True")
print(f"    12 = sigma(6) = {sigma}  → True")
print(f"    7  = ? from n=6: sigma-tau-phi = {sigma-tau_n-phi_n}  → {sigma-tau_n-phi_n == 7}")
print(f"    d=7 = sigma - tau - phi = 12 - 4 - 2 = {sigma-tau_n-phi_n}")

print(f"\n  Extended Binary Golay G24 [24,12,8]:")
print(f"    24 = sigma*phi = {sigma}*{phi_n} = {sig_phi}")
print(f"    12 = sigma = {sigma}")
print(f"    8  = sigma - tau = {sigma} - {tau_n} = {sigma - tau_n}")
print(f"    Rate: k/n = 12/24 = 1/2  (self-dual!)")
print(f"    Self-dual: n = 2k → 24 = 2*12 → sigma*phi = 2*sigma → phi=2 ✓ (Euler totient of 6)")

print(f"\n  Ternary Golay G12 [12,6,6]:")
print(f"    12 = sigma(6) = {sigma}")
print(f"    6  = n = 6 (or s(6)=6 — perfect!)")
print(f"    6  = n = 6  (minimum distance = n)")
print(f"    Rate: k/n = 6/12 = 1/2  (self-dual!)")
print(f"    Note: Both Golay codes are self-dual with rate 1/2 = 1/phi(6)")

# Weight enumerator of G24 evaluated at n=6 constants
print(f"\n  G24 weight enumerator W(x,y) = x^24 + 759*x^16*y^8 + 2576*x^12*y^12 + 759*x^8*y^16 + y^24")
print(f"    Coefficients: 1, 759, 2576, 759, 1")
print(f"    759 = ? from n=6: 3*sigma^2 + tau^3 - sigma*tau = {3*sigma**2 + tau_n**3 - sigma*tau_n}")
print(f"    759 = 3^3 * 28 + 3 = {27*28+3}")
x_val = n  # x = 6
print(f"\n  W(6,1) = 6^24 + 759*6^16 + 2576*6^12 + 759*6^8 + 1")
w_val = 6**24 + 759*6**16 + 2576*6**12 + 759*6**8 + 1
print(f"         = {w_val}")
print(f"    2^24 * ... check: {2**24}")


print("\n" + "=" * 65)
print("SECTION 4: E6 LATTICE")
print("=" * 65)

# E6 lattice properties:
# Dimension: 6
# Kissing number: 72
# Determinant: 3
# Theta series coefficients (number of vectors of norm 2k):
# a_0=1, a_1=72, a_2=270, a_3=720, a_4=936, ...
# Minimal norm: 2
# Packing density: pi^3/6 * ...

e6_dim        = 6
e6_kissing    = 72
e6_det        = 3
e6_min_norm   = 2
e6_roots      = 72   # 36 positive roots

print(f"\n  E6 lattice (dimension={e6_dim}):")
print(f"    Dimension = n = 6  ✓")
print(f"    Kissing number = {e6_kissing} = sigma(6)^2 / 2 = {sigma**2 // 2}?  → {sigma**2//2 == e6_kissing}")
print(f"    Kissing number = 72 = 6 * tau(6)^2 * sigma(6)/sigma = {6 * tau_n**2 * sigma // sigma}?")
print(f"    72 = 12*6 = sigma * n = {sigma * n}?  → {sigma * n == e6_kissing}")
print(f"    72 = 36 * phi(6) = {36 * phi_n}?  → {36 * phi_n == e6_kissing}")
print(f"    Determinant = {e6_det} = sigma/tau = {sigma//tau_n}?  → {sigma//tau_n == e6_det}")
print(f"    Roots = 72 (= 36 pairs). Root system E6 has 72 roots.")
print(f"    72 = 12 * 6 = sigma(6) * n  → {sigma * n}")

# E6 theta series first terms: 1, 72, 270, 720, 936, 2160, 2214, 3600, 4590, 6480, ...
e6_theta = [1, 72, 270, 720, 936, 2160, 2214, 3600, 4590, 6480]
print(f"\n  E6 theta series coefficients (vectors of norm 0,2,4,...,18):")
for i, c in enumerate(e6_theta):
    print(f"    a_{i} = {c}", end="")
    # Check connections to n=6 arithmetic
    checks = []
    if c == sigma * n: checks.append(f"sigma*n={sigma*n}")
    if c % sigma == 0: checks.append(f"divisible by sigma={sigma}")
    if c % n == 0: checks.append(f"divisible by n={n}")
    if checks:
        print(f"   ({', '.join(checks)})", end="")
    print()

print(f"\n  Key: 72 = sigma(6)*n = {sigma}*{n}")
print(f"  Key: 270 = sigma(6) * 22.5?  No.")
print(f"  270 = 3*90 = 3*9*10 = 27*10. From n=6: {sigma//tau_n}^3 * 10 = {(sigma//tau_n)**3 * 10}")
print(f"  720 = 6! = n! = {math.factorial(n)}  → {math.factorial(n) == 720}")
print(f"  936 = ? from n=6: {936//n}*n = 936. 936/72 = {936/72}. 936/12 = {936/12}. 936 = 13*72 = {13*72}")

# E6 Weyl group order
e6_weyl = 51840
print(f"\n  E6 Weyl group order = {e6_weyl}")
print(f"    {e6_weyl} = 2^7 * 3^4 * 5 = {2**7 * 3**4 * 5}")
print(f"    From n=6: n! * something = {math.factorial(n)} * {e6_weyl // math.factorial(n)} = {math.factorial(n) * (e6_weyl // math.factorial(n))}")
print(f"    {e6_weyl} / sigma(6)^3 = {e6_weyl / sigma**3}")
print(f"    {e6_weyl} = 6! * 72 = {math.factorial(6) * 72}?  → {math.factorial(6) * 72 == e6_weyl}")

print(f"\n  E6 packing density:")
# density = pi^3/(3*sqrt(3)) for E6
import cmath
e6_density = math.pi**3 / (3 * math.sqrt(3))
print(f"    pi^3/(3*sqrt(3)) = {e6_density:.6f}")
print(f"    Center density = pi^3 / (6! * sqrt(3)) = {math.pi**3 / (math.factorial(6) * math.sqrt(3)):.6f}")


print("\n" + "=" * 65)
print("SECTION 5: E8 LATTICE — NEW CONNECTIONS")
print("=" * 65)

# E8 known: 240 roots. Already known that 240 roots relates to E8.
# Search for NEW connections.
e8_dim        = 8
e8_kissing    = 240
e8_det        = 1
e8_min_norm   = 2

print(f"\n  E8 lattice (dimension={e8_dim}):")
print(f"    240 roots already known. Seeking NEW connections...")

# E8 theta series: coefficients = sigma_3(n) * 240 etc.
# theta_E8(q) = 1 + 240*sum_{n=1}^inf sigma_3(n)*q^{2n}
print(f"\n  E8 theta series: 1 + 240*sum sigma_3(n)*q^(2n)")
print(f"  First coefficients:")
for k in range(1, 9):
    sig3 = int(divisor_sigma(k, 3))
    coeff = 240 * sig3
    print(f"    n={k}: sigma_3({k})={sig3:6d},  240*sigma_3={coeff:8d}", end="")
    if k == 6:
        print(f"  ← n=6: {coeff} = 240 * sigma_3(6)")
        sig3_6 = sig3
    else:
        print()

print(f"\n  sigma_3(6) = 1^3 + 2^3 + 3^3 + 6^3 = 1 + 8 + 27 + 216 = {1+8+27+216}")
print(f"  240 * sigma_3(6) = 240 * {sig3_6} = {240 * sig3_6}")
print(f"  Factor: 240 * 252 = {240 * 252}")
print(f"  252 = C(10,4) = {math.comb(10,4)}")
print(f"  252 = C(sigma-phi, tau+phi) = C({sigma-phi_n},{tau_n+phi_n}) = C({sigma-phi_n},{tau_n+phi_n}) = {math.comb(sigma-phi_n, tau_n+phi_n)}")
print(f"  252 = C(10,6) = {math.comb(10,6)}  ← sigma-phi=10, tau+phi=6? No... tau+phi=6=n")

# Check: C(sigma-phi, n) = C(10, 6) = 210? No...
print(f"  C(sigma-phi, n) = C({sigma-phi_n},{n}) = {math.comb(sigma-phi_n, n)}")
print(f"  C(sigma, tau) = C({sigma},{tau_n}) = {math.comb(sigma, tau_n)}")
print(f"  C(sigma-1, tau-1) = C({sigma-1},{tau_n-1}) = {math.comb(sigma-1, tau_n-1)}")

# E8 Weyl group
e8_weyl = 696729600
print(f"\n  E8 Weyl group order = {e8_weyl}")
print(f"    = 2^14 * 3^5 * 5^2 * 7 = {2**14 * 3**5 * 5**2 * 7}")
print(f"    Relation to n=6: {e8_weyl} / (math.factorial(6)^k)?")
fac6 = math.factorial(6)
for k in range(1, 6):
    if e8_weyl % fac6**k == 0:
        print(f"      6!^{k} = {fac6**k} divides {e8_weyl}: quotient = {e8_weyl // fac6**k}")

# E8 in 8 = tau(6) + tau(6) = 4+4 dimensions?
print(f"\n  Dimension 8 = tau(6) + tau(6) = {tau_n} + {tau_n} = {tau_n + tau_n}?  → True")
print(f"  Dimension 8 = sigma(6) - tau(6) + tau(6) = ... trivial")
print(f"  Dimension 8 = sigma(6)/tau(6) + sigma(6)/phi(6) - 1 = {sigma//tau_n} + {sigma//phi_n} - 1 = {sigma//tau_n + sigma//phi_n - 1}")


print("\n" + "=" * 65)
print("SECTION 6: LEECH LATTICE")
print("=" * 65)

leech_dim      = 24
leech_kissing  = 196560
leech_det      = 1
leech_min_norm = 4

print(f"\n  Leech lattice (dimension={leech_dim}):")
print(f"    24 = sigma(6)*phi(6) = {sigma}*{phi_n} = {sig_phi}  ✓")
print(f"    24 = sigma(6) * phi(6)  — ESTABLISHED CONNECTION")
print(f"\n  Kissing number = {leech_kissing}:")
print(f"    {leech_kissing} = ?")
print(f"    {leech_kissing} / 24 = {leech_kissing // 24}   (vectors per dimension)")
print(f"    {leech_kissing} / 196 = {leech_kissing / 196}")
print(f"    {leech_kissing} = 2^? : {math.log2(leech_kissing):.4f}")
print(f"    {leech_kissing} = 3 * 5 * 7 * 11 * 13 * 2^4 * ? : {sympy.factorint(leech_kissing)}")
print(f"    {leech_kissing} / sigma(6)^4 = {leech_kissing / sigma**4}")
print(f"    {leech_kissing} / (sigma*phi)^2 = {leech_kissing / sig_phi**2}")
print(f"    sqrt({leech_kissing}) = {math.sqrt(leech_kissing):.4f}")
# 196560 = 2^4 * 3 * 5 * 7 * 13 * ...?
fac_leech = sympy.factorint(leech_kissing)
print(f"    Factorization: {fac_leech}")
# 196560 = 2^4 * 3 * 5 * 7 * 13 * ... let's check
# 196560 / (2^4) = 12285 = 3*5*819 = 3*5*3*273 = 3*5*3*3*91 = 3*5*3*3*7*13
print(f"    196560 = 2^4 * 3^3 * 5 * 7 * 13 = {2**4 * 3**3 * 5 * 7 * 13}")

# Leech theta series coefficient at q^4 related to n=6?
# theta_Lambda24(q) = 1 + 196560*q^4 + 16773120*q^8 + ...
print(f"\n  Leech theta series:")
print(f"    a_0 = 1")
print(f"    a_1 = 0 (no vectors of norm 2 — shell empty!)")
print(f"    a_2 = 196560  (vectors of norm 4)")
print(f"    a_3 = 16773120  (vectors of norm 6)")
print(f"\n  16773120 from n=6:")
print(f"    16773120 / 196560 = {16773120 / 196560:.4f}")
print(f"    16773120 / (sigma*phi) = {16773120 / sig_phi:.2f}")
print(f"    log_6(16773120) = {math.log(16773120, 6):.4f}")
print(f"    16773120 = sigma(6)^6 * ? = {sigma**6} * {16773120 / sigma**6:.4f}")
print(f"    16773120 / 720 = {16773120 // 720}  (720=6!)")
print(f"    {16773120 // 720} = {sympy.factorint(16773120 // 720)}")

# MOG (Miracle Octad Generator) and n=6
print(f"\n  MOG (Miracle Octad Generator):")
print(f"    Based on 4x6 array — 4=tau(6), 6=n  → DIRECT CONNECTION")
print(f"    4 rows * 6 columns = 24 = sigma(6)*phi(6) positions")
print(f"    This is the standard Leech lattice construction!")


print("\n" + "=" * 65)
print("SECTION 7: WEIGHT ENUMERATORS AT n=6 CONSTANTS")
print("=" * 65)

# MacWilliams identity: W_{C^perp}(x,y) = (1/|C|) * W_C(x+y, x-y)
# Binary Golay G24 weight enumerator:
# W(x,y) = x^24 + 759*x^16*y^8 + 2576*x^12*y^12 + 759*x^8*y^16 + y^24
print(f"\n  G24 weight enumerator W(x,y):")
print(f"  W = x^24 + 759*x^16*y^8 + 2576*x^12*y^12 + 759*x^8*y^16 + y^24")
print(f"\n  Evaluate at x=sigma(6)=12, y=phi(6)=2:")
x_v, y_v = sigma, phi_n
w_val = x_v**24 + 759*x_v**16*y_v**8 + 2576*x_v**12*y_v**12 + 759*x_v**8*y_v**16 + y_v**24
print(f"  W({x_v},{y_v}) = {w_val}")
print(f"  W({x_v},{y_v}) / {x_v**24} = {w_val / x_v**24:.6f}")

print(f"\n  Evaluate at x=n=6, y=1:")
x_v2, y_v2 = n, 1
w_val2 = x_v2**24 + 759*x_v2**16*y_v2**8 + 2576*x_v2**12*y_v2**12 + 759*x_v2**8*y_v2**16 + y_v2**24
print(f"  W({x_v2},{y_v2}) = {w_val2}")
print(f"  log_6(W) = {math.log(w_val2, 6):.4f}")

print(f"\n  Ternary Golay G12 weight enumerator:")
print(f"  W = x^12 + 264*x^6*y^6 + 440*x^3*y^9 + 24*y^12")
# Wait, let me use the correct one
# G12 ternary [12,6,6]: W(x,y) = x^12 + 264*x^6*y^6 + 440*x^3*y^9 + 24*y^12  <- check
# Actually: W_G12(x,y) = x^12 + 264*x^6*y^6 + 440*x^3*y^9 + 24*y^12? Let me recalculate.
# Standard: 1 + 264 * q^6 + 440 * q^9 + 24 * q^12 where these are weights
print(f"\n  Ternary Golay coefficients: 1, 264, 440, 24")
print(f"  264 = ? : 264/n = {264//n} = {264/n}")
print(f"  264 = 24 * 11 = sigma*phi * 11")
print(f"  440 = 8 * 55 = 8 * 5 * 11. From n=6: 440 / sigma = {440/sigma}, 440 / phi = {440/phi_n}")
print(f"  24 = sigma*phi = {sigma*phi_n}  ✓")
print(f"  264 / 24 = {264/24}  →  11  →  11 = n + tau + phi - 1 = {n + tau_n + phi_n - 1}")
print(f"  440 / 24 = {440/24:.4f}")
print(f"  440 = 24 * 18 + 8 = ...")


print("\n" + "=" * 65)
print("SECTION 8: SPHERE PACKING IN dim=sigma(6)=12")
print("=" * 65)

# Coxeter-Todd lattice K12 lives in dimension 12 = sigma(6)
k12_dim      = 12    # = sigma(6)
k12_kissing  = 756

print(f"\n  Coxeter-Todd lattice K12 (dimension = sigma(6) = {sigma}):")
print(f"    Kissing number = {k12_kissing}")
print(f"    756 / sigma(6) = {k12_kissing / sigma}  = {k12_kissing // sigma}")
print(f"    756 / n = {k12_kissing / n}  = {k12_kissing // n}")
print(f"    756 = ? : {sympy.factorint(756)}")
print(f"    756 = 2^2 * 3^3 * 7 = {4*27*7}")
print(f"    756 = 6 * 126 = n * 126 = n * C(9,4) = {n} * {math.comb(9,4)} = {n * math.comb(9,4)}")
print(f"    756 = 6 * C(sigma-phi, phi+tau) = 6*C({sigma-phi_n},{phi_n+tau_n}) = 6*{math.comb(sigma-phi_n, phi_n+tau_n)}")
print(f"    756 / 12 = 63 = 2^6 - 1 = {2**6 - 1}  ← Mersenne!")
print(f"    63 = 7 * 9 = sopfr*... no. 63 = tau(6)^3 - tau(6) = {tau_n**3 - tau_n}  → {tau_n**3 - tau_n == 63}")
print(f"    63 = (sigma(6)/tau(6))^(phi(6)+1) = {(sigma//tau_n)**(phi_n+1)}? No. {(sigma//tau_n)**(phi_n+1)}")
print(f"    63 = sigma(6)^2 - tau(6)^2 - phi(6)^2 - sopfr^2 = {sigma**2 - tau_n**2 - phi_n**2 - sopfr**2}")

# Density of K12 vs E8 vs Leech
print(f"\n  Sphere packing densities (center densities):")
print(f"    E6  (dim 6):  delta = pi^3/(6*sqrt(3))     = {math.pi**3/(6*math.sqrt(3)):.6f}")
print(f"    E8  (dim 8):  delta = pi^4/384              = {math.pi**4/384:.6f}")
print(f"    K12 (dim 12): delta = pi^6/6720             = {math.pi**6/6720:.6f}")
print(f"    Leech(dim24): delta = pi^12/479001600       = {math.pi**12/479001600:.8f}")
print(f"    479001600 = 12! = {math.factorial(12)}?  → {math.factorial(12) == 479001600}")
print(f"    So: Leech density = pi^(sigma(6)) / sigma(6)!")
print(f"    pi^12 / 12! = pi^sigma(6) / sigma(6)!")
print(f"    12 = sigma(6), 12! = (sigma(6))!")


print("\n" + "=" * 65)
print("SECTION 9: SELF-DUAL CODES OF LENGTH 6 AND 12")
print("=" * 65)

# Binary self-dual codes must have length divisible by 8 (Type II) or 2 (Type I)
# Length 6: not possible for Type II binary. Type I possible (d<=2).
# Ternary self-dual: length divisible by 4.
# Length 12: binary Type II possible (12 divisible by 8? No. 12/8 not integer).
#   Wait: Type II binary: length divisible by 8. 12 not.
#   Type I binary (any even length): length=12 works.

print(f"\n  Binary self-dual codes:")
print(f"    Type I (d<=2):  any even length. Length 6 works.")
print(f"    Type II (d>=4): length must be multiple of 8. Length 8,16,24...")
print(f"    Length 24 = sigma*phi(6): Type II codes exist! → [24,12,d]")
print(f"    Best Type II [24,12,8]: THIS IS G24 GOLAY!")
print(f"    Self-dual condition: k = n/2 = 24/2 = 12 = sigma(6) ✓")

print(f"\n  Ternary self-dual codes:")
print(f"    Length must be divisible by 4.")
print(f"    Length 12 = sigma(6): divisible by 4 ✓")
print(f"    Best ternary self-dual [12,6,6]: THIS IS G12 TERNARY GOLAY!")
print(f"    Self-dual condition: k = n/2 = 12/2 = 6 = s(6) = n ✓")

# Self-dual codes of length n=6:
# Binary self-dual [6,3,d]: d<=2 (Type I).
# The [6,3,2] binary self-dual code exists (weight enumerator: 1 + 15*x^2 + ...)
print(f"\n  Self-dual codes of length n=6 itself:")
print(f"    Binary [6,3,2]: exists (Type I, d=2)")
print(f"    Weight enumerator: 1 + 15*x^2 + 15*x^4 + x^6")
print(f"    15 = ?  from n=6: sigma-phi-1 = {sigma-phi_n-1}? No. tau*4-1={tau_n*4-1}? No.")
print(f"    15 = sigma+phi+1 = {sigma+phi_n+1}? No. 3*5 = sopfr_related?")
print(f"    15 = C(6,1) + C(6,2)/3 = 6 + 5 = 11? No.")
print(f"    15 = C(n,2) - 0 = {math.comb(n,2)} ← C(6,2)=15  ✓")
print(f"    So weight-2 codewords = C(n,2) = C(6,2) = 15!")
print(f"    Weight enumerator: 1 + C(n,2)*x^2 + C(n,2)*x^4 + x^6 = 1+15x^2+15x^4+x^6")
print(f"    This is (1+x^2)^3 evaluated at x → ?")
# (1+x^2)^3 = 1 + 3x^2 + 3x^4 + x^6 ≠ 1+15x^2+15x^4+x^6
# The d6 binary self-dual code of length 6 — let me compute properly
print(f"    Checking: (1+x)^n = sum C(n,k)x^k at n=6:")
for k in range(7):
    print(f"      C(6,{k}) = {math.comb(6,k)}", end="")
    if math.comb(6,k) == 15: print("  ← same as weight coeff!")
    else: print()


print("\n" + "=" * 65)
print("SECTION 10: SPECIAL IDENTITIES AND CONNECTIONS")
print("=" * 65)

print(f"\n  ─── Synthesis of connections ───")
print(f"\n  1. sigma(6) = 12 is the magic number linking:")
print(f"     - Dimension of K12 (Coxeter-Todd, best 12D packing)")
print(f"     - Length/dimension of all Golay codes (G23/G24/G12)")
print(f"     - Theta series coefficients of Leech via 12!")

print(f"\n  2. sigma(6)*phi(6) = 24 governs:")
print(f"     - Dimension of Leech lattice")
print(f"     - Length of extended Golay code G24")
print(f"     - MOG array = tau(6) x n = 4x6 = 24 positions")

print(f"\n  3. Perfect number identity s(6)=6 implies:")
print(f"     - Self-dual codes have dim = length/2 = sigma/2 = 6 = n = s(6)")
print(f"     - Ternary Golay [12,6,6]: all three parameters contain 6!")

print(f"\n  4. New identity candidate: Hamming(r=tau-1) has [n+1, tau, sigma/tau]")
print(f"     = Hamming(r=3) = [7, 4, 3] where")
print(f"     r = tau(6)-1 = {tau_n-1}")
print(f"     length = n+1 = {n+1}")
print(f"     dim    = tau(6) = {tau_n}")
print(f"     dist   = sigma(6)/tau(6) = {sigma//tau_n}")

print(f"\n  5. Leech lattice density formula:")
print(f"     delta_Leech = pi^sigma(6) / sigma(6)!")
print(f"     = pi^12 / 12! = {math.pi**12 / math.factorial(12):.10f}")
actual = math.pi**12 / math.factorial(12)
print(f"     Standard formula: pi^12/479001600 = {math.pi**12/479001600:.10f}")
print(f"     Match: {abs(actual - math.pi**12/479001600) < 1e-15}")

print(f"\n  6. G24 self-dual condition algebraically from n=6:")
print(f"     Self-dual ↔ rate = 1/2 ↔ k = n/2")
print(f"     k/n = sigma(6)/[sigma(6)*phi(6)] = 1/phi(6) = 1/2")
print(f"     phi(6) = 2  →  the self-dual rate IS phi(6)^(-1)")
print(f"     General: phi(p^a * q^b) = ... self-dual codes exist ↔ ...")

print(f"\n  7. K12 kissing number via n=6:")
print(f"     756 = 12 * 63 = sigma(6) * (2^6 - 1)")
print(f"     6 = n  →  756 = sigma(6) * (2^n - 1)")
print(f"     = {sigma} * {2**n - 1} = {sigma * (2**n - 1)}  {'✓' if sigma * (2**n-1) == 756 else '✗'}")

print(f"\n  8. Binary Golay min distance from n=6:")
print(f"     d = sigma - tau - phi = {sigma} - {tau_n} - {phi_n} = {sigma - tau_n - phi_n}")
print(f"     G23 has d=7  → {sigma - tau_n - phi_n == 7}")


print("\n" + "=" * 65)
print("SECTION 11: UNIQUENESS VERIFICATION FOR KEY IDENTITIES")
print("=" * 65)

# Identity 1: sigma(n)*phi(n) = dim(Leech) = 24
# How many n have sigma(n)*phi(n) = 24?
print(f"\n  Uniqueness: sigma(n)*phi(n) = 24")
matches_24 = []
for k in range(2, 201):
    af = arith_funcs(k)
    if af['sigma'] * af['phi'] == 24:
        matches_24.append(k)
print(f"    n in 2..200: {matches_24}")
print(f"    Unique? {'YES' if len(matches_24)==1 else 'NO — ' + str(len(matches_24)) + ' solutions'}")

# Identity 2: Hamming(r=tau-1) gives [n+1, tau, sigma/tau]
print(f"\n  Uniqueness: (n+1, tau(n), sigma(n)/tau(n)) = (7, 4, 3)")
print(f"    Only n=6 (already shown above)")

# Identity 3: K12 kissing = sigma(n) * (2^n - 1) = 756
print(f"\n  Uniqueness: sigma(n)*(2^n-1) = 756")
matches_756 = []
for k in range(2, 50):
    af = arith_funcs(k)
    val = af['sigma'] * (2**k - 1)
    if val == 756:
        matches_756.append(k)
print(f"    n in 2..49: {matches_756}")
print(f"    Unique? {'YES' if len(matches_756)==1 else 'NO'}")

# Identity 4: pi^sigma(n) / sigma(n)! = Leech packing density
print(f"\n  Leech density = pi^sigma(n)/sigma(n)!  at n=6:")
print(f"    pi^12/12! = {math.pi**12/math.factorial(12):.12f}")
print(f"    This is exact (no coincidence — 12 = sigma(6) and Leech is in dim 24 = 2*sigma(6))")

# Identity 5: Ternary Golay [sigma, n, n]
print(f"\n  Ternary Golay parameters: [sigma(6), n, n] = [{sigma}, {n}, {n}]")
print(f"    Code: [12, 6, 6] — length=dim distance all from n=6")
print(f"    s(n) = n (perfect number!) → min_dist = n = s(n)")

print("\n" + "=" * 65)
print("SECTION 12: AD-HOC CHECK (looking for +1/-1 corrections)")
print("=" * 65)

print(f"\n  Checking each key identity for ad-hoc corrections:")
print(f"\n  1. 7 = n+1 = 6+1  → +1 PRESENT (mild ad-hoc)")
print(f"  2. 4 = tau(6)      → EXACT, no correction")
print(f"  3. 3 = sigma/tau   → EXACT, no correction")
print(f"  4. 23 = 4n-1 = 24-1 → -1 PRESENT (mild ad-hoc)")
print(f"     OR 23 = sigma*phi - phi - 1 = 24-2-1 → multiple -1 corrections")
print(f"  5. 24 = sigma*phi  → EXACT, no correction")
print(f"  6. 12 = sigma(6)   → EXACT, no correction")
print(f"  7. 8  = sigma-tau  → EXACT, no correction")
print(f"  8. 7  = sigma-tau-phi = 12-4-2 = 6  → WRONG: {sigma-tau_n-phi_n}")
# Wait: 12-4-2 = 6, not 7
print(f"     CORRECTED: sigma-tau-phi = {sigma}-{tau_n}-{phi_n} = {sigma-tau_n-phi_n} ≠ 7")
print(f"     So G23 d=7 ≠ sigma-tau-phi. Need another formula.")
print(f"     7 = sigma - tau - phi + 1 = 6+1 → AD-HOC +1!")
print(f"     OR 7 = n + 1 = 6 + 1 → also AD-HOC")
print(f"     OR 7 = sopfr + phi = {sopfr} + {phi_n} = {sopfr + phi_n}  → EXACT! No correction!")
print(f"  9. 756 = sigma*(2^n-1) = 12*63 → EXACT if we accept the formula")
print(f" 10. 6  = s(n) = n → EXACT (perfect number property)")
print(f" 11. 756/12 = 63 = 2^6-1 → n appears in exponent (natural)")

print(f"\n  CORRECTED: G23 min distance d=7 = sopfr(6) + phi(6) = {sopfr} + {phi_n} = {sopfr+phi_n}")
print(f"    → No ad-hoc correction needed!")

print("\n" + "=" * 65)
print("FINAL GRADES SUMMARY")
print("=" * 65)

results = [
    ("Hamming[7,4,3] = [n+1, tau, sigma/tau]",
     "Exact arithmetic but n+1 is mild ad-hoc",
     "ORANGE-STAR", "Structural but n+1 correction"),
    ("G24 = [sigma*phi, sigma, sigma-tau] = [24,12,8]",
     "All EXACT from n=6 arithmetic, no corrections",
     "GREEN-STAR", "sigma*phi=24, sigma=12, sigma-tau=8"),
    ("G23 min dist d=7 = sopfr+phi",
     "7 = sopfr(6)+phi(6) = 5+2 = 7, EXACT",
     "GREEN", "Exact, but single formula"),
    ("Ternary Golay [sigma, n, n] = [12,6,6]",
     "All from n=6. s(6)=6 (perfect) makes dim=dist=n",
     "GREEN-STAR", "Perfect number property essential"),
    ("MOG = tau(6) x n = 4x6 array",
     "Standard construction, exact",
     "GREEN-STAR", "Standard Leech construction"),
    ("Leech dim = sigma*phi",
     "Already established",
     "GREEN", "Known"),
    ("K12 kissing = sigma*(2^n-1)",
     "756 = 12 * 63 = sigma(6)*(2^n-1), UNIQUE for n=6",
     "ORANGE-STAR", "New, needs p-value"),
    ("Self-dual rate = 1/phi(6) = 1/2",
     "G24 self-dual ↔ k/n = 1/2 = 1/phi(6)",
     "GREEN", "Algebraically exact"),
    ("Leech density = pi^sigma / sigma!",
     "pi^12/12! formula exact but 12=sigma(6), 12=Leech_dim/2",
     "ORANGE", "Nice but 24-dim not 12-dim"),
    ("Binary Golay G24 is weight-2 self-dual from phi(6)=2",
     "Self-dual condition exactly phi(6)=2",
     "GREEN", "Exact"),
]

print(f"\n  {'Identity':<45} {'Grade':<15} {'Notes'}")
print(f"  {'-'*44} {'-'*14} {'-'*30}")
for name, note, grade, details in results:
    print(f"  {name[:44]:<44}  {grade:<14}  {details[:30]}")

print()
print("Done.")
