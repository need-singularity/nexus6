"""
Verification experiment for H-QUAD-1 open directions and H-PROB-1 extension.

H-QUAD-1 open directions:
  1. r_8(6) = 3136 = sigma(28)^2? (structural or coincidence?)
  2. Higher r_k(6) for k=24 (Leech dimension)?
  3. r_4(6) connection to modular forms (theta^4 Fourier coefficient check)

H-PROB-1 extension:
  - Push R(n)=1 uniqueness verification from 10^5 to 10^6
  - Attempt proof sketch: bound sigma(n)*phi(n) vs n*tau(n) for n > 6
"""

import math
from functools import lru_cache
from collections import defaultdict

# ─── Arithmetic functions ────────────────────────────────────────────────────

def factorize(n):
    """Return prime factorization as dict {p: e}."""
    factors = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors

def sigma(n):
    """Sum of divisors."""
    f = factorize(n)
    result = 1
    for p, e in f.items():
        result *= (p**(e+1) - 1) // (p - 1)
    return result

def phi(n):
    """Euler's totient."""
    f = factorize(n)
    result = n
    for p in f:
        result = result * (p - 1) // p
    return result

def tau(n):
    """Number of divisors."""
    f = factorize(n)
    result = 1
    for e in f.values():
        result *= (e + 1)
    return result

def R(n):
    """R(n) = sigma(n)*phi(n) / (n*tau(n))"""
    return sigma(n) * phi(n) / (n * tau(n))

# ─── r_k(n): representations as sum of k squares ────────────────────────────
# We use the direct count via Jacobi's formula for r_2, r_4, r_8,
# and brute-force for small n and small k.

def r_k_brute(n, k, max_val=None):
    """
    Count representations of n as sum of k squares (including negatives and zeros).
    For small n, k this is feasible.
    """
    if max_val is None:
        max_val = int(math.isqrt(n)) + 1

    count = 0
    def rec(remaining_k, remaining_n, min_abs):
        nonlocal count
        if remaining_k == 0:
            if remaining_n == 0:
                count += 1
            return
        # x ranges over -max_val..max_val
        for x in range(-max_val, max_val + 1):
            x2 = x * x
            if x2 > remaining_n:
                break
            rec(remaining_k - 1, remaining_n - x2, 0)

    rec(k, n, 0)
    return count

def r4_jacobi(n):
    """
    r_4(n) via Jacobi's four-square theorem:
      r_4(n) = 8 * sum(d | n, 4 does not divide d)
    """
    total = 0
    for d in range(1, n + 1):
        if n % d == 0 and d % 4 != 0:
            total += d
    return 8 * total

def r8_formula(n):
    """
    r_8(n) via the formula (Jacobi 1829):
      r_8(n) = 16 * sum_{d|n} (-1)^(n-d) * d^3
    """
    total = 0
    for d in range(1, n + 1):
        if n % d == 0:
            total += ((-1) ** (n - d)) * (d ** 3)
    return 16 * total

def r2_formula(n):
    """
    r_2(n) via the formula:
      r_2(n) = 4 * (d_1(n) - d_3(n))
    where d_1 = divisors ≡ 1 (mod 4), d_3 = divisors ≡ 3 (mod 4)
    """
    d1 = sum(1 for d in range(1, n+1) if n % d == 0 and d % 4 == 1)
    d3 = sum(1 for d in range(1, n+1) if n % d == 0 and d % 4 == 3)
    return 4 * (d1 - d3)

# ─── Part 1: H-QUAD-1 open direction #1: r_8(6) = sigma(28)^2 = 3136? ──────

print("=" * 65)
print("H-QUAD-1 VERIFICATION — Open Directions")
print("=" * 65)

n = 6
r8_val = r8_formula(n)
sig28 = sigma(28)
sig28_sq = sig28 ** 2

print(f"\n[Direction 1] r_8(6) vs sigma(28)^2")
print(f"  r_8(6)       = {r8_val}")
print(f"  sigma(28)    = {sig28}")
print(f"  sigma(28)^2  = {sig28_sq}")
print(f"  Match: {r8_val == sig28_sq}")

# Cross-check r_8 with brute force (slow but n=6, k=8 is feasible with cutoff)
print(f"\n  [Brute-force cross-check r_8(6) — counting 8-tuples...]")
r8_brute = r_k_brute(6, 8, max_val=3)
print(f"  r_8(6) brute force = {r8_brute}  (formula: {r8_val})")
print(f"  Brute/formula match: {r8_brute == r8_val}")

# Is this identity general? Check r_8(n) vs sigma(next_perfect(n))^2 for n=28
# r_8(28) vs sigma(496)^2?
r8_28 = r8_formula(28)
sig496 = sigma(496)
print(f"\n  [Generalization check] r_8(28) vs sigma(496)^2")
print(f"  r_8(28)       = {r8_28}")
print(f"  sigma(496)    = {sig496}")
print(f"  sigma(496)^2  = {sig496**2}")
print(f"  Match: {r8_28 == sig496**2}")

# What IS r_8(6) = 3136 equal to structurally?
print(f"\n  [Structural decomposition of r_8(6) = {r8_val}]")
print(f"  56^2 = {56**2}  [sigma(28)^2]")
print(f"  28^2 * 4 = {28**2 * 4}")
print(f"  2 * sigma(6)^3 = {2 * sigma(6)**3}")
print(f"  sigma(6) * tau(6) * 65 + ? ...")
# Let's systematically check: r_8(6) = A * sigma(6)^B for small A,B
sig6 = sigma(6)
tau6 = tau(6)
phi6 = phi(6)
for exp in range(1, 5):
    val = sig6 ** exp
    if r8_val % val == 0:
        print(f"  r_8(6) / sigma(6)^{exp} = {r8_val // val}")

# Check r_k(6) for k = 1..8
print(f"\n[Direction 2] r_k(6) for k = 1..8")
print(f"  Known: sigma(6)={sig6}, phi(6)={phi6}, tau(6)={tau6}")
print()
print(f"  {'k':>4} | {'r_k(6)':>10} | {'formula':>12} | Notes")
print(f"  {'─'*4}─+─{'─'*10}─+─{'─'*12}─+─{'─'*30}")
for k in range(1, 9):
    rk = r_k_brute(6, k, max_val=3)
    # Identify notable values
    notes = []
    if rk == sig6 * phi6:
        notes.append("= sigma*phi")
    if rk == 8 * sig6:
        notes.append("= 8*sigma (Jacobi)")
    if rk == sig28_sq:
        notes.append("= sigma(28)^2")
    if rk == 0:
        notes.append("= 0")
    if k == 4:
        rk_formula = r4_jacobi(6)
        notes.append(f"formula={rk_formula}")
    note_str = ", ".join(notes) if notes else ""
    print(f"  {k:>4} | {rk:>10} | {'—':>12} | {note_str}")

# ─── Part 2: Bernoulli denominator check ────────────────────────────────────
print(f"\n[Direction 3] Bernoulli denominator — 6 | denom(B_2k) for k=1..10")
print(f"  Von Staudt-Clausen verification:")
print()

# denom(B_2k) = prod of primes p where (p-1) | 2k
def bernoulli_denom_von_staudt(two_k):
    denom = 1
    for p in range(2, two_k + 3):
        # check if p is prime
        if all(p % d != 0 for d in range(2, int(p**0.5)+1)) or p == 2:
            if (p - 1) > 0 and two_k % (p - 1) == 0:
                denom *= p
    return denom

print(f"  {'2k':>4} | {'denom(B_2k)':>14} | {'6 | denom':>10} | {'28 | denom':>11}")
print(f"  {'─'*4}─+─{'─'*14}─+─{'─'*10}─+─{'─'*11}")
for k in range(1, 11):
    two_k = 2 * k
    d = bernoulli_denom_von_staudt(two_k)
    div6 = (d % 6 == 0)
    div28 = (d % 28 == 0)
    print(f"  {two_k:>4} | {d:>14} | {str(div6):>10} | {str(div28):>11}")

# ─── Part 3: H-PROB-1 extension — push R(n)=1 to 10^6 ──────────────────────
print()
print("=" * 65)
print("H-PROB-1 EXTENSION — R(n)=1 uniqueness up to 10^6")
print("=" * 65)
print()
print("  Searching n = 1 to 1,000,000 for R(n) = sigma*phi/(n*tau) = 1 ...")
print()

R1_solutions = []
milestone = 100_000
N_MAX = 1_000_000

for n in range(1, N_MAX + 1):
    s = sigma(n)
    p = phi(n)
    t = tau(n)
    # R(n) = s*p/(n*t) = 1 iff s*p = n*t
    if s * p == n * t:
        R1_solutions.append(n)
    if n == milestone:
        print(f"  Checked up to {n:,}: solutions so far = {R1_solutions}")
        milestone += 100_000

print(f"\n  Final solutions in [1, {N_MAX:,}]: {R1_solutions}")
print(f"  Count: {len(R1_solutions)}")

# ─── Part 4: Proof sketch — lower bound for R(n) when n > 6 ─────────────────
print()
print("=" * 65)
print("H-PROB-1 PROOF SKETCH — R(n) > 1 for n > 6 (sampling)")
print("=" * 65)
print()

# Known bounds:
#   sigma(n)/n >= H_k for "smooth" numbers (H_k = k-th harmonic)
#   phi(n)/n = prod(1 - 1/p) for primes p|n
#   tau(n) <= exp(c*ln(n)/ln(ln(n)))
#
# For R(n) = sigma(n)*phi(n)/(n*tau(n)):
# We use the identity: sigma(n)*phi(n) = n^2 * prod_p|n (1 - 1/p^2)  ... wait, not exact
# Actually: sigma(n)*phi(n) = n * prod_p|n (p^a - 1)(p^(a+1)-1)/(p-1)/(p)
#
# Simpler approach: check R(n) for all n up to 10^4 and find minimum excluding n=1,6
print("  Minimum R(n) values for n in [2, 10000], excluding n=1,6:")
min_R = float('inf')
min_n = -1
near_1 = []
for n in range(2, 10001):
    s = sigma(n)
    p = phi(n)
    t = tau(n)
    # Use rational arithmetic: s*p vs n*t
    num = s * p
    den = n * t
    if num == den:  # R = 1 exactly
        if n != 6:
            near_1.append((n, 1.0))
        continue
    r = num / den
    if r < min_R and n != 6:
        min_R = r
        min_n = n
    if r < 1.05 and n != 6:
        near_1.append((n, r))

near_1.sort(key=lambda x: x[1])
print(f"  Global minimum R(n) for n in [2,10000], n != 6:")
print(f"    n = {min_n}, R = {min_R:.6f}, factorization = {factorize(min_n)}")
print()
print(f"  All n in [2,10000] with R(n) < 1.05 (n != 6):")
print(f"  {'n':>8} | {'R(n)':>10} | factorization")
print(f"  {'─'*8}─+─{'─'*10}─+─{'─'*20}")
for n, r in near_1[:20]:
    print(f"  {n:>8} | {r:>10.6f} | {factorize(n)}")

# ─── Part 5: Texas Sharpshooter style p-value for r_8(6) = sigma(28)^2 ──────
print()
print("=" * 65)
print("TEXAS SHARPSHOOTER — r_8(6) = sigma(28)^2 coincidence test")
print("=" * 65)
print()
print("  Question: Is r_8(6) = 3136 = sigma(28)^2 a coincidence?")
print()
print("  Null hypothesis: r_8(6) is a 'random' large integer.")
print("  We check: how many perfect squares of sigma(P_k) fall near r_8(6)?")
print()
print("  r_8(6) = 3136")
print("  sigma(6)^2  =", sigma(6)**2, "  (=144)")
print("  sigma(28)^2 =", sigma(28)**2, " (=3136) <-- matches r_8(6)")
print("  sigma(496)^2=", sigma(496)**2)
print()

# Check: is r_8(6) = sigma(28)^2 derivable from Jacobi's formula?
# r_8(n) = 16 * sum_{d|n} (-1)^(n-d) * d^3
# For n=6, divisors are 1,2,3,6
divs_6 = [d for d in range(1,7) if 6 % d == 0]
print(f"  Jacobi r_8 formula for n=6, divisors={divs_6}:")
terms = []
total = 0
for d in divs_6:
    sign = (-1)**(6 - d)
    term = sign * d**3
    terms.append(f"({sign:+d})*{d}^3={term:+d}")
    total += term
print(f"  16 * [{', '.join(terms)}]")
print(f"  = 16 * {total} = {16*total}")
print()

# What is sigma(28) algebraically?
# sigma(28) = sigma(4)*sigma(7) = 7 * 8 = 56
# 56^2 = 3136
# r_8(6) = 16*(1^3 - 2^3 + 3^3 + 6^3) ... let's compute
val = sum((-1)**(6-d) * d**3 for d in divs_6)
print(f"  16 * sum = 16 * {val} = {16*val}")
print(f"  sigma(28) = sigma(4)*sigma(7) = {sigma(4)}*{sigma(7)} = {sigma(28)}")
print(f"  sigma(28)^2 = {sigma(28)**2}")
print()

# Is there an algebraic connection?
# sigma(28) = 56 = 8*7
# r_8(6) = 3136 = 56^2 = (8*7)^2
# From Jacobi: r_8(6) = 16*(1 - 8 + 27 + 216) = 16*196 = 3136
print(f"  sum of d^3 terms: {val} = {val}")
print(f"  196 = 14^2 = (sigma(6)+tau(6))^2 = {(sigma(6)+tau(6))**2}")
print(f"  196 = 4*49 = 4*7^2")
print(f"  sigma(6) = 12, tau(6) = 4, sigma(6)+tau(6) = 16, not 14")
print(f"  Actually 196 = 14^2. 14 = sigma(6)/tau(6)*? ... 12/4=3, no.")
print(f"  14 = sigma(28)/4 = {sigma(28)//4}")
print(f"  So r_8(6) = 16 * (sigma(28)/4)^2 = sigma(28)^2 / 1 ... let's verify:")
print(f"  16 * (sigma(28)/4)^2 = 16 * {(sigma(28)//4)**2} = {16*(sigma(28)//4)**2}")
print()

# Is sigma(28)/4 = 14 derivable from n=6 properties?
# sigma(28) = sigma(2^2 * 7) = (1+2+4)*(1+7) = 7*8 = 56
# 56/4 = 14
# 14 = 2*7, and 7 is the Mersenne prime for perfect number 28
# The connection to n=6: is there one?
# Jacobi sum for n=6: 1^3 - 2^3 + 3^3 + 6^3 = 1 - 8 + 27 + 216 = 236? let's recheck

jacobi_terms = []
for d in divs_6:
    sign = (-1)**(6-d)
    jacobi_terms.append(sign * d**3)
print(f"  Jacobi terms for d in {{1,2,3,6}}: {jacobi_terms}")
print(f"  Sum = {sum(jacobi_terms)}")
print(f"  16 * {sum(jacobi_terms)} = {16*sum(jacobi_terms)}")

# The sum is 196 = (1 - 8 + 27 + 216) -- let's check
print(f"  Breakdown: 1 - 8 + 27 + 216 = {1 - 8 + 27 + 216}")

print()
print("=" * 65)
print("SUMMARY")
print("=" * 65)
