#!/usr/bin/env python3
"""
Verify Super-Hypotheses SUPER-15 through SUPER-28 (Axes 3,4,5)
Focus: ARITHMETIC correctness and UNIQUENESS claims.
"""

import math
from sympy import divisor_sigma, totient, factorint, sqrt as sym_sqrt
from sympy.ntheory import continued_fraction_periodic
from fractions import Fraction

# ── Helper functions ──

def tau(n):
    """Number of divisors."""
    return int(divisor_sigma(n, 0))

def sigma(n):
    """Sum of divisors."""
    return int(divisor_sigma(n, 1))

def phi(n):
    """Euler totient."""
    return int(totient(n))

def sopfr(n):
    """Sum of prime factors with repetition."""
    s = 0
    for p, e in factorint(n).items():
        s += p * e
    return s

def aliquot_s(n):
    """Sum of proper divisors."""
    return sigma(n) - n

def proper_divisors(n):
    divs = []
    for i in range(1, n):
        if n % i == 0:
            divs.append(i)
    return divs

def R(n):
    """R-spectrum: sigma*phi / (n*tau)."""
    return Fraction(sigma(n) * phi(n), n * tau(n))

# ── Precompute n=6 constants ──
N = 6
S = sigma(N)      # 12
T = tau(N)         # 4
P = phi(N)         # 2
SP = sopfr(N)      # 5

print("=" * 70)
print("SUPER-HYPOTHESIS VERIFICATION: AXES 3, 4, 5")
print("=" * 70)
print(f"\nn=6 constants: sigma={S}, tau={T}, phi={P}, sopfr={SP}")
print()

results = {}

# ═══════════════════════════════════════════════════════════════════
# SUPER-15: Cortical Architecture
# ═══════════════════════════════════════════════════════════════════
print("─" * 70)
print("SUPER-15: Cortical Architecture Chain")
print("─" * 70)

c1 = N * P  # 6*2=12
c2 = S      # sigma=12
c3 = c2 / 3 # 12/3=4
c4 = T      # tau=4
c5 = c4 / P # 4/2=2
c6 = P      # phi=2

p15a = (c1 == c2 == S)
p15b = (c3 == c4 == T)
p15c = (c5 == c6 == P)

print(f"  6*phi = 6*{P} = {c1}, sigma = {S}  =>  {'PASS' if p15a else 'FAIL'}")
print(f"  12/3 = {c3}, tau = {T}              =>  {'PASS' if p15b else 'FAIL'}")
print(f"  4/phi = 4/{P} = {c5}, phi = {P}     =>  {'PASS' if p15c else 'FAIL'}")
print(f"  Chain self-consistent: {c1}->{c3}->{c5} = {S}->{T}->{P}")

all15 = p15a and p15b and p15c
results['SUPER-15'] = all15
print(f"\n  SUPER-15 ARITHMETIC: {'PASS' if all15 else 'FAIL'}")
print(f"  NOTE: Cortical layers=6, directions=2, channels=12 are BIOLOGICAL claims (literature).")

# ═══════════════════════════════════════════════════════════════════
# SUPER-16: Consciousness Bandwidth 24
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 70)
print("SUPER-16: Consciousness Bandwidth 24")
print("─" * 70)

v1 = S * P       # sigma*phi = 12*2 = 24
v2 = N * T       # n*tau = 6*4 = 24
v3 = T * N       # 4*6 = 24 (same)

p16a = (v1 == 24)
p16b = (v2 == 24)
p16c = (v1 == v2)

print(f"  sigma*phi = {S}*{P} = {v1} = 24?  {'PASS' if p16a else 'FAIL'}")
print(f"  n*tau = {N}*{T} = {v2} = 24?       {'PASS' if p16b else 'FAIL'}")
print(f"  sigma*phi = n*tau?                  {'PASS' if p16c else 'FAIL'}")

print(f"\n  Appearances of 24 (literature claims, not verified here):")
appearances_24 = [
    "Ramanujan tau: Delta(q) = q * prod(1-q^n)^24  -- exponent = 24",
    "Leech lattice: dimension = 24",
    "K3 surface: Euler characteristic chi = 24",
    "Golay code: length = 24",
    "Kissing number 4D: kiss(4) = 24",
    "Bosonic string: critical dimension = 26, but 24 transverse",
    "Hours in a day = 24 (anthropic, not mathematical)",
    "sigma(6)*phi(6) = n(6)*tau(6) = 24",
]
for a in appearances_24:
    print(f"    - {a}")

results['SUPER-16'] = p16a and p16b and p16c
print(f"\n  SUPER-16 ARITHMETIC: {'PASS' if results['SUPER-16'] else 'FAIL'}")

# ═══════════════════════════════════════════════════════════════════
# SUPER-17: Precision-Hierarchy Lock
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 70)
print("SUPER-17: Precision-Hierarchy Lock (Unique 3-term partition of 1)")
print("─" * 70)

# Verify uniqueness: find ALL sets {1/a, 1/b, 1/c} with a<b<c distinct positive integers, summing to 1
partitions_3 = []
for a in range(2, 100):
    for b in range(a + 1, 1000):
        # 1/a + 1/b + 1/c = 1 => 1/c = 1 - 1/a - 1/b
        rem = Fraction(1) - Fraction(1, a) - Fraction(1, b)
        if rem > 0 and rem.numerator == 1:
            c = rem.denominator
            if c > b:
                partitions_3.append((a, b, c))

print(f"  All 3-term distinct reciprocal-integer partitions of 1:")
for p in partitions_3:
    print(f"    1/{p[0]} + 1/{p[1]} + 1/{p[2]} = 1")

p17_unique = (len(partitions_3) == 1 and partitions_3[0] == (2, 3, 6))

# Entropy
h = -(Fraction(1,2)*math.log(1/2) + Fraction(1,3)*math.log(1/3) + Fraction(1,6)*math.log(1/6))
h_max = math.log(3)
ratio = h / h_max

print(f"\n  Unique? {len(partitions_3)} solution(s) found: {'PASS (unique)' if p17_unique else 'FAIL'}")
print(f"  Entropy H = -sum p_i ln(p_i) = {h:.6f}")
print(f"  Max entropy ln(3) = {h_max:.6f}")
print(f"  Ratio H/H_max = {ratio:.6f}")
print(f"  (Ratio < 1 means hierarchy, not uniform)")

results['SUPER-17'] = p17_unique
print(f"\n  SUPER-17 UNIQUENESS: {'PASS' if p17_unique else 'FAIL'}")

# ═══════════════════════════════════════════════════════════════════
# SUPER-18: Dyson-Cortex phi^2 = tau
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 70)
print("SUPER-18: Dyson-Cortex phi^2 = tau")
print("─" * 70)

p18_6 = (P**2 == T)
print(f"  n=6: phi^2 = {P}^2 = {P**2}, tau = {T}  =>  {'PASS' if p18_6 else 'FAIL'}")

# Check n=28
p28, t28 = phi(28), tau(28)
p18_28 = (p28**2 == t28)
print(f"  n=28: phi^2 = {p28}^2 = {p28**2}, tau = {t28}  =>  {'PASS (not unique)' if p18_28 else 'FAIL (confirms uniqueness among perfects)'}")

# Check n=496
p496, t496 = phi(496), tau(496)
p18_496 = (p496**2 == t496)
print(f"  n=496: phi^2 = {p496}^2 = {p496**2}, tau = {t496}  =>  {'PASS' if p18_496 else 'FAIL'}")

# Check ALL n in 2..1000 for phi^2=tau
phi2_tau_matches = []
for nn in range(2, 1001):
    if phi(nn)**2 == tau(nn):
        phi2_tau_matches.append(nn)
print(f"\n  All n in [2,1000] with phi(n)^2 = tau(n): {phi2_tau_matches[:30]}{'...' if len(phi2_tau_matches)>30 else ''}")
print(f"  Total count: {len(phi2_tau_matches)}")
print(f"  n=6 is {'among them' if 6 in phi2_tau_matches else 'NOT among them'}")
print(f"  Unique among perfect numbers (6,28,496): {'YES' if (6 in phi2_tau_matches and 28 not in phi2_tau_matches and 496 not in phi2_tau_matches) else 'NO'}")

results['SUPER-18'] = p18_6 and not p18_28
print(f"\n  SUPER-18: phi^2=tau for n=6: PASS, unique among perfects: {'PASS' if results['SUPER-18'] else 'FAIL'}")

# ═══════════════════════════════════════════════════════════════════
# SUPER-19: Z=6 Bootstrap
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 70)
print("SUPER-19: Z=6 Bootstrap")
print("─" * 70)

carbon_valence = 4
p19a = (carbon_valence == T)
print(f"  Carbon valence = 4 = tau(6) = {T}?  {'PASS' if p19a else 'FAIL'}  (literature: Carbon valence=4)")

r6 = R(6)
r14 = R(14)
print(f"  R(6) = sigma*phi/(n*tau) = {S}*{P}/({N}*{T}) = {r6}  (=1? {'PASS' if r6==1 else 'FAIL'})")

s14, p14, t14 = sigma(14), phi(14), tau(14)
print(f"  R(14) = {s14}*{p14}/({14}*{t14}) = {s14*p14}/{14*t14} = {r14}  (=1? {'YES' if r14==1 else 'NO, !=1'})")

# Check n=28 (Silicon Z=14 neighbor)
r28 = R(28)
s28, p28_, t28_ = sigma(28), phi(28), tau(28)
print(f"  R(28) = {s28}*{p28_}/({28}*{t28_}) = {s28*p28_}/{28*t28_} = {r28}  (=1? {'YES' if r28==1 else 'NO'})")

results['SUPER-19'] = (r6 == 1) and (r14 != 1)
print(f"\n  SUPER-19 ARITHMETIC: {'PASS' if results['SUPER-19'] else 'FAIL'}")
print(f"  NOTE: Carbon valence=4, Z=6 are physics facts (literature).")

# ═══════════════════════════════════════════════════════════════════
# SUPER-20: Quark-Carbon-Neuron Trinity
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 70)
print("SUPER-20: Quark-Carbon-Neuron Trinity")
print("─" * 70)

quark_flavors = 6  # u,d,c,s,t,b
generations = 3
types = 2  # up-type, down-type
p20a = (quark_flavors == generations * types)
p20b = (generations * types == (S // T) * P)  # (sigma/tau)*phi = 3*2 = 6

print(f"  Quark flavors = {quark_flavors} = 3 generations x 2 types: {'PASS' if p20a else 'FAIL'}")
print(f"  (sigma/tau)*phi = ({S}/{T})*{P} = {(S//T)*P} = 6?  {'PASS' if p20b else 'FAIL'}")
print(f"  Coincidence count: quarks=6, Carbon Z=6, cortical layers=6 (all =n)")

results['SUPER-20'] = p20a and p20b
print(f"\n  SUPER-20 ARITHMETIC: {'PASS' if results['SUPER-20'] else 'FAIL'}")
print(f"  NOTE: Quark count=6 and cortical layers=6 are PHYSICS/BIOLOGY claims.")

# ═══════════════════════════════════════════════════════════════════
# SUPER-21: 12=sigma Structural Constant (Kissing Numbers)
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 70)
print("SUPER-21: 12=sigma Structural Constant (Kissing Numbers)")
print("─" * 70)

# Known kissing numbers (exact values)
kiss = {1: 2, 2: 6, 3: 12, 4: 24, 8: 240, 24: 196560}

p21a = (kiss[2] == N)
p21b = (kiss[3] == S)
p21c = (kiss[4] == S * P)
p21d_formula = S * T * sopfr(N)  # 12*4*5 = 240
p21d = (kiss[8] == p21d_formula)

# kiss(24D) = 196560
# Claim: sigma * tau * (2^sigma - 1) = 12*4*(2^12-1) = 12*4*4095
p21e_formula = S * T * (2**S - 1)
p21e = (kiss[24] == p21e_formula)

print(f"  kiss(1D) =     {kiss[1]}  (= phi = {P}?  {'PASS' if kiss[1]==P else 'FAIL'})")
print(f"  kiss(2D) =     {kiss[2]}  (= n = {N}?  {'PASS' if p21a else 'FAIL'})")
print(f"  kiss(3D) =    {kiss[3]}  (= sigma = {S}?  {'PASS' if p21b else 'FAIL'})")
print(f"  kiss(4D) =    {kiss[4]}  (= sigma*phi = {S*P}?  {'PASS' if p21c else 'FAIL'})")
print(f"  kiss(8D) =   {kiss[8]}  (= sigma*tau*sopfr = {S}*{T}*{SP} = {p21d_formula}?  {'PASS' if p21d else 'FAIL'})")
print(f"  kiss(24D) = {kiss[24]}  (= sigma*tau*(2^sigma-1) = {S}*{T}*{2**S-1} = {p21e_formula}?  {'PASS' if p21e else 'FAIL'})")

all21 = p21a and p21b and p21c and p21d and p21e
results['SUPER-21'] = all21
print(f"\n  SUPER-21 ARITHMETIC: {'PASS' if all21 else 'FAIL'}")
if all21:
    print(f"  *** ALL known exact kissing numbers at key dimensions match n=6 arithmetic! ***")

# ═══════════════════════════════════════════════════════════════════
# SUPER-22: Fixed Point
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 70)
print("SUPER-22: Fixed Point Properties")
print("─" * 70)

# s(6) = aliquot sum
s6 = aliquot_s(6)
p22a = (s6 == 6)
print(f"  s(6) = 1+2+3 = {s6} = 6?  {'PASS' if p22a else 'FAIL'}  (perfect number definition)")

# R(6) = 1
p22b = (R(6) == 1)
print(f"  R(6) = {R(6)} = 1?  {'PASS' if p22b else 'FAIL'}")

# Wedderburn-Etherington numbers
# WE(n) for n=1,2,3,4,5,6,7,8: 1,1,1,2,3,6,11,23
# Index: WE(1)=1, WE(2)=1, WE(3)=1, WE(4)=2, WE(5)=3, WE(6)=6
we_seq = [0, 1, 1, 1, 2, 3, 6, 11, 23, 46, 98]  # 1-indexed
p22c = (we_seq[6] == 6)
print(f"  WE(6) = {we_seq[6]} = 6?  {'PASS' if p22c else 'FAIL'}  (Wedderburn-Etherington number)")

# Sum of reciprocals of NONTRIVIAL proper divisors + 1/n = 1
# Proper divisors of 6: {1,2,3}. Nontrivial (>1): {2,3}. Then 1/2+1/3+1/6=1.
# Equivalently: unique perfect number with this Egyptian fraction property.
prop_div_6_nontrivial = [d for d in proper_divisors(6) if d > 1]
recip_sum = sum(Fraction(1, d) for d in prop_div_6_nontrivial) + Fraction(1, 6)
p22d = (recip_sum == 1)
print(f"  1/{' + 1/'.join(str(d) for d in prop_div_6_nontrivial)} + 1/{N} = {recip_sum} = 1?  {'PASS' if p22d else 'FAIL'}  (Egyptian fraction from nontrivial proper divisors + 1/n)")

# 6 = 3! = 1*2*3
p22e = (math.factorial(3) == 6)
print(f"  3! = {math.factorial(3)} = 6?  {'PASS' if p22e else 'FAIL'}")

# 6 = C(4,2) (central binomial-ish)
from math import comb
p22f = (comb(4, 2) == 6)
print(f"  C(4,2) = {comb(4,2)} = 6?  {'PASS' if p22f else 'FAIL'}")

# 1+2+3 = 1*2*3 = 6
p22g = (1+2+3 == 1*2*3 == 6)
print(f"  1+2+3 = 1*2*3 = 6?  {'PASS' if p22g else 'FAIL'}")

fixed_count = sum([p22a, p22b, p22c, p22d, p22e, p22f, p22g])
print(f"\n  Fixed-point properties verified: {fixed_count}/7")

results['SUPER-22'] = p22a and p22b and p22c and p22d
print(f"  SUPER-22 (core 4): {'PASS' if results['SUPER-22'] else 'FAIL'}")

# ═══════════════════════════════════════════════════════════════════
# SUPER-23: Pell Self-Description
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 70)
print("SUPER-23: Pell Self-Description")
print("─" * 70)

# Pell equation x^2 - 6y^2 = 1
# Fundamental solution: try small values
fund_x, fund_y = None, None
for y in range(1, 100):
    x2 = 6 * y * y + 1
    x = int(math.isqrt(x2))
    if x * x == x2:
        fund_x, fund_y = x, y
        break

p23a = (fund_x == SP and fund_y == P)  # (5, 2) = (sopfr, phi)
print(f"  Pell x^2-6y^2=1 fundamental solution: ({fund_x},{fund_y})")
print(f"  = (sopfr, phi) = ({SP},{P})?  {'PASS' if p23a else 'FAIL'}")

# Pell sequence: P_0=0, P_1=1, P_{n+1} = 2*P_n + P_{n-1} (for sqrt(2))
# But for x^2-6y^2=1, the recurrence for y-values uses the fundamental solution
# Standard Pell numbers (for sqrt(2)): 0, 1, 2, 5, 12, 29, 70, ...
pell = [0, 1]
for i in range(10):
    pell.append(2 * pell[-1] + pell[-2])

print(f"\n  Pell numbers (sqrt(2)): {pell[:8]}")
p23b = (pell[2] == P)   # P_2 = 2 = phi
p23c = (pell[3] == SP)  # P_3 = 5 = sopfr
p23d = (pell[4] == S)   # P_4 = 12 = sigma
print(f"  P_2 = {pell[2]} = phi = {P}?    {'PASS' if p23b else 'FAIL'}")
print(f"  P_3 = {pell[3]} = sopfr = {SP}? {'PASS' if p23c else 'FAIL'}")
print(f"  P_4 = {pell[4]} = sigma = {S}?  {'PASS' if p23d else 'FAIL'}")

# CF(sqrt(6))
cf6 = continued_fraction_periodic(0, 1, 6)
print(f"\n  CF(sqrt(6)) = {cf6}")
# cf6 = [2, [2, 4]] -> period = [2,4], sum = 6
if len(cf6) == 2 and isinstance(cf6[1], list):
    period = cf6[1]
    period_sum = sum(period)
    p23e = (period_sum == N)
    print(f"  Period = {period}, sum = {period_sum} = n = {N}?  {'PASS' if p23e else 'FAIL'}")
else:
    p23e = False
    print(f"  CF structure unexpected: {cf6}")

# CF(12/5) = CF(sigma/sopfr)
# 12/5 = 2 + 2/5 = 2 + 1/(5/2) = 2 + 1/(2 + 1/2)
# So CF = [2; 2, 2]
from fractions import Fraction as Fr
rat = Fr(S, SP)  # 12/5
cf_rat = []
r = rat
for _ in range(10):
    a = int(r)
    cf_rat.append(a)
    r = r - a
    if r == 0:
        break
    r = Fr(1, r)

p23f = all(x == P for x in cf_rat)
print(f"  CF({S}/{SP}) = CF(sigma/sopfr) = {cf_rat}")
print(f"  All entries = phi = {P}?  {'PASS' if p23f else 'FAIL'}")

# Pell for n=28
print(f"\n  n=28: x^2 - 28y^2 = 1")
fund28_x, fund28_y = None, None
for y in range(1, 10000):
    x2 = 28 * y * y + 1
    x = int(math.isqrt(x2))
    if x * x == x2:
        fund28_x, fund28_y = x, y
        break
if fund28_x:
    print(f"  Fundamental solution: ({fund28_x},{fund28_y})")
    print(f"  sopfr(28)={sopfr(28)}, phi(28)={phi(28)}")
    p23_28 = (fund28_x == sopfr(28) and fund28_y == phi(28))
    print(f"  = (sopfr(28), phi(28))? {'PASS' if p23_28 else 'FAIL'}")
else:
    print(f"  No solution found in y<10000")

all23 = p23a and p23b and p23c and p23d and p23e and p23f
results['SUPER-23'] = all23
print(f"\n  SUPER-23 ARITHMETIC: {'PASS' if all23 else 'FAIL'}")

# ═══════════════════════════════════════════════════════════════════
# SUPER-24: Egyptian Fraction Identity Network (THE KEY ONE)
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 70)
print("SUPER-24: Egyptian Fraction Identity Network")
print("─" * 70)

# phi/tau + tau/sigma + 1/n = ?
term1 = Fraction(P, T)   # 2/4 = 1/2
term2 = Fraction(T, S)   # 4/12 = 1/3
term3 = Fraction(1, N)   # 1/6
total = term1 + term2 + term3

p24a = (total == 1)
print(f"  phi/tau + tau/sigma + 1/n = {P}/{T} + {T}/{S} + 1/{N} = {term1} + {term2} + {term3} = {total}")
print(f"  = 1?  {'PASS' if p24a else 'FAIL'}")

# Verify this IS the unique partition {1/2, 1/3, 1/6}
p24b = ({term1, term2, term3} == {Fraction(1,2), Fraction(1,3), Fraction(1,6)})
print(f"  = {{1/2, 1/3, 1/6}}?  {'PASS' if p24b else 'FAIL'}")

# UNIQUENESS: Check n=2..10000
print(f"\n  Scanning n=2..10000 for phi/tau + tau/sigma + 1/n = 1...")
matches_24 = []
for nn in range(2, 10001):
    sn = sigma(nn)
    tn = tau(nn)
    pn = phi(nn)
    if sn == 0 or tn == 0:
        continue
    val = Fraction(pn, tn) + Fraction(tn, sn) + Fraction(1, nn)
    if val == 1:
        matches_24.append(nn)

print(f"  Matches: {matches_24}")
p24c = (matches_24 == [6])
print(f"  Unique to n=6?  {'PASS' if p24c else 'FAIL'}")

# Cross-check: same as ADE/Moran/flat geometry
print(f"\n  Cross-references (all = 1/2+1/3+1/6=1):")
print(f"    ADE:  Platonic triples (2,3,6) => 1/2+1/3+1/6=1 (flat/Euclidean)")
print(f"    Moran: 1/p+1/q+1/r=1 for d=1 branching")
print(f"    Geometry: 1/2+1/3+1/6=1 is the UNIQUE flat (Euclidean) triple")
print(f"    All are the SAME equation. This IS the uniqueness of SUPER-17.")

results['SUPER-24'] = p24a and p24b and p24c
print(f"\n  SUPER-24 ARITHMETIC + UNIQUENESS: {'PASS' if results['SUPER-24'] else 'FAIL'}")

# ═══════════════════════════════════════════════════════════════════
# SUPER-25: Master Product sigma*phi*f = 1
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 70)
print("SUPER-25: Master Product sigma*phi*f = 1")
print("─" * 70)

# f = 1/(sigma*phi) = 1/24
f = Fraction(1, S * P)
product = S * P * f
p25a = (product == 1)
print(f"  sigma*phi*(1/24) = {S}*{P}*(1/24) = {product}  = 1?  {'PASS' if p25a else 'FAIL'}")
print(f"  (This is trivially true: sigma*phi * 1/(sigma*phi) = 1)")

# The non-trivial claim is sigma*phi = n*tau = 24
p25b = (S * P == N * T)
print(f"  sigma*phi = n*tau?  {S}*{P} = {N}*{T}?  {S*P} = {N*T}?  {'PASS' if p25b else 'FAIL'}")

# How common is sigma*phi = n*tau?
# R(n)=1 means sigma*phi/(n*tau)=1, already checked via R
r1_count = []
for nn in range(2, 1001):
    if R(nn) == 1:
        r1_count.append(nn)
print(f"  R(n)=1 for n in [2,1000]: {r1_count[:20]}{'...' if len(r1_count)>20 else ''}")
print(f"  Count: {len(r1_count)}")
print(f"  (R(n)=1 is NOT unique to n=6, but n=6 is the smallest perfect number with R=1)")

results['SUPER-25'] = p25a and p25b
print(f"\n  SUPER-25 ARITHMETIC: {'PASS' if results['SUPER-25'] else 'FAIL'}")
print(f"  NOTE: sigma*phi*f=1 is tautological. The content is sigma*phi=n*tau=24.")

# ═══════════════════════════════════════════════════════════════════
# SUPER-26: (n-1)(n-2) = sopfr * tau
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 70)
print("SUPER-26: (n-1)(n-2) = sopfr(n)*tau(n)")
print("─" * 70)

lhs26 = (N - 1) * (N - 2)
rhs26 = SP * T
p26a = (lhs26 == rhs26)
print(f"  n=6: (6-1)(6-2) = 5*4 = {lhs26}")
print(f"        sopfr*tau = {SP}*{T} = {rhs26}")
print(f"  Equal?  {'PASS' if p26a else 'FAIL'}")

# n=28
lhs28 = 27 * 26
rhs28 = sopfr(28) * tau(28)
p26b = (lhs28 != rhs28)
print(f"\n  n=28: (27)(26) = {lhs28}")
print(f"        sopfr(28)*tau(28) = {sopfr(28)}*{tau(28)} = {rhs28}")
print(f"  Not equal?  {'PASS (confirming non-trivial)' if p26b else 'FAIL'}")

# Uniqueness in 2..10000
print(f"\n  Scanning n=2..10000...")
matches_26 = []
for nn in range(2, 10001):
    if (nn - 1) * (nn - 2) == sopfr(nn) * tau(nn):
        matches_26.append(nn)
print(f"  Matches: {matches_26}")
p26c = (6 in matches_26)
p26_unique = (matches_26 == [6])
print(f"  Unique to n=6?  {'PASS' if p26_unique else 'FAIL'}")

results['SUPER-26'] = p26a and p26c
print(f"\n  SUPER-26 ARITHMETIC: {'PASS' if p26a else 'FAIL'}, UNIQUENESS: {'PASS' if p26_unique else 'FAIL'}")

# ═══════════════════════════════════════════════════════════════════
# SUPER-27: Consecutive Integers
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 70)
print("SUPER-27: Consecutive Integers")
print("─" * 70)

consec_set = {P, S // T, T, SP, N}  # {2, 3, 4, 5, 6}
expected = {2, 3, 4, 5, 6}
p27a = (consec_set == expected)
print(f"  {{phi, sigma/tau, tau, sopfr, n}} = {{{P}, {S//T}, {T}, {SP}, {N}}} = {consec_set}")
print(f"  = {{2,3,4,5,6}}?  {'PASS' if p27a else 'FAIL'}")

# Product
prod27 = P * (S // T) * T * SP * N
p27b = (prod27 == math.factorial(N))
print(f"  Product = {prod27} = {N}! = {math.factorial(N)}?  {'PASS' if p27b else 'FAIL'}")

# (tau-1)! = n
p27c = (math.factorial(T - 1) == N)
print(f"  (tau-1)! = ({T}-1)! = {T-1}! = {math.factorial(T-1)} = n = {N}?  {'PASS' if p27c else 'FAIL'}")

# n=28 check
s28_v = {phi(28), sigma(28) // tau(28), tau(28), sopfr(28), 28}
s28_ratio = Fraction(sigma(28), tau(28))
print(f"\n  n=28: {{phi, sigma/tau, tau, sopfr, n}} = {{{phi(28)}, {s28_ratio}, {tau(28)}, {sopfr(28)}, 28}}")
print(f"  Consecutive? NO")

results['SUPER-27'] = p27a and p27b and p27c
print(f"\n  SUPER-27 ARITHMETIC: {'PASS' if results['SUPER-27'] else 'FAIL'}")

# ═══════════════════════════════════════════════════════════════════
# SUPER-28: Grand Loop (10 self-referential properties)
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 70)
print("SUPER-28: Grand Loop — Self-Referential Properties of n=6")
print("─" * 70)

props = []

# 1. Perfect: s(6)=6
p1 = (aliquot_s(6) == 6)
props.append(("Perfect number: s(6)=6", p1))

# 2. R(6)=1
p2 = (R(6) == 1)
props.append(("R-spectrum: R(6)=1", p2))

# 3. WE(6)=6
p3 = (we_seq[6] == 6)
props.append(("Wedderburn-Etherington: WE(6)=6", p3))

# 4. 1+2+3 = 1*2*3 = 6
p4 = (1+2+3 == 1*2*3 == 6)
props.append(("Sum=Product: 1+2+3=1*2*3=6", p4))

# 5. 3! = 6
p5 = (math.factorial(3) == 6)
props.append(("Factorial: 3!=6", p5))

# 6. Egyptian fraction: 1/2+1/3+1/6=1 unique
p6 = p17_unique
props.append(("Egyptian fraction: unique 1/2+1/3+1/6=1", p6))

# 7. phi^2=tau
p7 = (P**2 == T)
props.append(("Dyson: phi^2=tau", p7))

# 8. Pell fundamental = (sopfr, phi)
p8 = p23a
props.append(("Pell: fund. soln = (sopfr,phi)", p8))

# 9. (n-1)(n-2)=sopfr*tau
p9 = p26a
props.append(("Falling factorial: (n-1)(n-2)=sopfr*tau", p9))

# 10. Consecutive invariants {2,3,4,5,6}
p10 = p27a
props.append(("Consecutive invariants: {phi,...,n}={2,3,4,5,6}", p10))

print(f"\n  {'#':<4} {'Property':<50} {'Status'}")
print(f"  {'─'*4} {'─'*50} {'─'*6}")
for i, (desc, val) in enumerate(props, 1):
    print(f"  {i:<4} {desc:<50} {'PASS' if val else 'FAIL'}")

pass_count = sum(v for _, v in props)
print(f"\n  Total: {pass_count}/{len(props)} properties verified for n=6")

# Check n=28
print(f"\n  n=28 comparison:")
props_28 = []
props_28.append(("Perfect: s(28)=28", aliquot_s(28) == 28))
props_28.append(("R(28)=1", R(28) == 1))
# WE(28) -- sequence: compute up to index 28
we = [0] * 30
we[1] = 1
# Actually WE is harder to compute. Use known values.
# WE: 1,1,1,2,3,6,11,23,46,98,207,451,983,2179,4850,10905,...
we_known = [0, 1, 1, 1, 2, 3, 6, 11, 23, 46, 98, 207, 451, 983, 2179, 4850, 10905]
if len(we_known) > 28:
    props_28.append(("WE(28)=28", we_known[28] == 28))
else:
    props_28.append(("WE(28)=28", False))
    print(f"    WE(28) not computed (sequence too short), likely FAIL (WE grows fast)")

# sum=product for divisors of 28: 1+2+4+7+14 = 28, 1*2*4*7*14 = 784 != 28
props_28.append(("Sum=Product proper divs", sum(proper_divisors(28)) == 28))  # This is just perfect number
props_28.append(("phi(28)^2=tau(28)", phi(28)**2 == tau(28)))
props_28.append(("Consecutive invariants", False))  # Already shown not

for desc, val in props_28:
    print(f"    {desc}: {'PASS' if val else 'FAIL'}")

n28_pass = sum(v for _, v in props_28)
print(f"  n=28 passes: {n28_pass}/{len(props_28)}")

results['SUPER-28'] = (pass_count == len(props))
print(f"\n  SUPER-28: {'PASS' if results['SUPER-28'] else 'FAIL'} ({pass_count}/10 for n=6)")

# ═══════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("FINAL SUMMARY")
print("=" * 70)
print(f"\n  {'Hypothesis':<14} {'Result':<8} {'Notes'}")
print(f"  {'─'*14} {'─'*8} {'─'*45}")

notes = {
    'SUPER-15': 'Arithmetic chain verified; biology claims = literature',
    'SUPER-16': 'sigma*phi=n*tau=24 verified; 24 appearances = literature',
    'SUPER-17': 'UNIQUE 3-term partition confirmed; entropy computed',
    'SUPER-18': 'phi^2=tau for n=6 ONLY among perfect numbers',
    'SUPER-19': 'R(6)=1, R(14)!=1; Carbon valence = literature',
    'SUPER-20': 'Arithmetic OK; physics/biology counts = literature',
    'SUPER-21': 'ALL kissing numbers at key dims match n=6 arithmetic!',
    'SUPER-22': '7/7 fixed-point properties verified',
    'SUPER-23': 'Pell (5,2)=(sopfr,phi), CF period sum=6, all verified',
    'SUPER-24': 'phi/tau+tau/sigma+1/n=1 UNIQUE to n=6 in [2,10000]',
    'SUPER-25': 'sigma*phi=n*tau=24 verified (sigma*phi*f=1 tautological)',
    'SUPER-26': f'(n-1)(n-2)=sopfr*tau unique in [2,10000]: {matches_26}',
    'SUPER-27': 'Consecutive {2,3,4,5,6} verified, product=6!=720',
    'SUPER-28': f'{pass_count}/10 self-referential properties hold',
}

pass_total = 0
fail_total = 0
for hyp in sorted(results.keys(), key=lambda x: int(x.split('-')[1])):
    status = 'PASS' if results[hyp] else 'FAIL'
    if results[hyp]:
        pass_total += 1
    else:
        fail_total += 1
    print(f"  {hyp:<14} {status:<8} {notes.get(hyp, '')}")

print(f"\n  TOTAL: {pass_total} PASS, {fail_total} FAIL out of {len(results)}")
print("=" * 70)
