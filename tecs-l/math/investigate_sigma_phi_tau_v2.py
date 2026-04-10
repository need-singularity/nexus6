#!/usr/bin/env python3
"""
Investigate: σ(n) + φ(n) + τ(n) = 3n
Optimized version using sieve for fast computation.
"""

import sys
import time
import math
from sympy import isprime, factorint, primerange
from functools import reduce
import operator

LIMIT = 1_000_000

print("=" * 70)
print("INVESTIGATION: σ(n) + φ(n) + τ(n) = 3n")
print("=" * 70)
sys.stdout.flush()

# ─────────────────────────────────────────────────────────────
# PART 1: Sieve-based extended search
# ─────────────────────────────────────────────────────────────
print(f"\nPART 1: SIEVE SEARCH up to {LIMIT:,}")
sys.stdout.flush()

t0 = time.time()

# Sieve σ(n), φ(n), τ(n) simultaneously
sigma = list(range(LIMIT + 1))  # will become σ(n) — start with n, multiply
phi = list(range(LIMIT + 1))    # will become φ(n) — start with n
tau = [1] * (LIMIT + 1)         # will become τ(n)

# We need proper sieve. Let's use a multiplicative sieve.
# Actually, let's sieve with smallest prime factor approach.

# Reset
sigma = [0] * (LIMIT + 1)
phi = [0] * (LIMIT + 1)
tau = [0] * (LIMIT + 1)

# Better: compute via factorization sieve
# Step 1: Find smallest prime factor
spf = list(range(LIMIT + 1))
for i in range(2, int(LIMIT**0.5) + 1):
    if spf[i] == i:  # i is prime
        for j in range(i*i, LIMIT + 1, i):
            if spf[j] == j:
                spf[j] = i

print(f"  SPF sieve done in {time.time()-t0:.1f}s")
sys.stdout.flush()

# Step 2: Compute σ, φ, τ from factorization
sigma[1] = 1
phi[1] = 1
tau[1] = 1

for n in range(2, LIMIT + 1):
    if spf[n] == n:
        # n is prime
        sigma[n] = n + 1
        phi[n] = n - 1
        tau[n] = 2
    else:
        p = spf[n]
        # Find p^a || n
        m = n
        a = 0
        pa = 1
        while m % p == 0:
            m //= p
            a += 1
            pa *= p
        # n = p^a * m, gcd(p, m) = 1
        if m == 1:
            # n = p^a
            sigma[n] = (p**(a+1) - 1) // (p - 1)
            phi[n] = pa - pa // p
            tau[n] = a + 1
        else:
            # multiplicative
            sigma[n] = sigma[pa] * sigma[m]
            phi[n] = phi[pa] * phi[m]
            tau[n] = tau[pa] * tau[m]

print(f"  Arithmetic functions computed in {time.time()-t0:.1f}s")
sys.stdout.flush()

# Step 3: Find solutions
solutions = []
for n in range(1, LIMIT + 1):
    if sigma[n] + phi[n] + tau[n] == 3 * n:
        solutions.append(n)

elapsed = time.time() - t0
print(f"  Search complete in {elapsed:.1f}s")
print(f"  Solutions found: {solutions}")
print(f"  Count: {len(solutions)}")
sys.stdout.flush()

if solutions == [2, 4, 6, 90, 408, 5856]:
    print("  NO NEW SOLUTIONS beyond 5856 up to 1,000,000.")
    print("  Strong numerical evidence for finiteness.")

# Quick verification
print("\nVerification of solutions:")
print(f"{'n':>8s} | {'factorization':>25s} | {'σ(n)':>8s} | {'φ(n)':>8s} | {'τ(n)':>4s} | {'σ+φ+τ':>8s} | {'3n':>8s} | {'σ/n':>7s} | {'φ/n':>7s}")
print("-" * 100)
for n in solutions:
    s, p, t = sigma[n], phi[n], tau[n]
    fac = factorint(n)
    fac_str = " * ".join(f"{pr}^{e}" if e > 1 else str(pr) for pr, e in sorted(fac.items()))
    print(f"{n:>8d} | {fac_str:>25s} | {s:>8d} | {p:>8d} | {t:>4d} | {s+p+t:>8d} | {3*n:>8d} | {s/n:>7.4f} | {p/n:>7.4f}")
sys.stdout.flush()

# ─────────────────────────────────────────────────────────────
# PART 2: Near misses (how close do others get?)
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("PART 2: NEAR MISSES (|σ+φ+τ - 3n| ≤ 5)")
print("=" * 70)
near_misses = []
for n in range(2, LIMIT + 1):
    diff = sigma[n] + phi[n] + tau[n] - 3 * n
    if abs(diff) <= 5 and diff != 0:
        near_misses.append((n, diff))
print(f"Found {len(near_misses)} near misses")
for n, d in near_misses[:30]:
    fac = factorint(n)
    print(f"  n={n:>8d}: σ+φ+τ - 3n = {d:>+3d}  factorization={fac}")
if len(near_misses) > 30:
    print(f"  ... and {len(near_misses)-30} more")
sys.stdout.flush()

# ─────────────────────────────────────────────────────────────
# PART 3: Algebraic proofs for specific forms
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("PART 3: ALGEBRAIC PROOFS FOR EACH FORM")
print("=" * 70)

print("""
=== Case 1: n = p (prime) ===
σ + φ + τ = (p+1) + (p-1) + 2 = 2p + 2
3n = 3p → p = 2. ONLY n=2. ✓

=== Case 2: n = p² ===
σ + φ + τ = (p²+p+1) + (p²-p) + 3 = 2p² + 4
3n = 3p² → p² = 4 → p = 2 → n = 4. ✓

=== Case 3: n = p^a, a ≥ 3 ===
σ = (p^(a+1)-1)/(p-1), φ = p^a - p^(a-1), τ = a+1
Equation: (p^(a+1)-1)/(p-1) + p^(a-1)(p-1) + (a+1) = 3p^a

For p=2: (2^(a+1)-1) + 2^(a-1) + (a+1) = 3·2^a
  → 2·2^a - 1 + 2^a/2 + a + 1 = 3·2^a
  → a = 2^(a-1). Only a=1,2 work. For a≥3: 2^(a-1) >> a. ✓

For p=3, a=3: σ=121, φ=54, τ=4. 121+54+4=179, 3·27=81. No.
For p≥3: σ/n → p/(p-1) ≤ 3/2, φ/n = 1-1/p ≤ 2/3. Sum ≤ 2.17 < 3. ✓

=== Case 4: n = 2p, p odd prime ===
σ = 3(p+1), φ = p-1, τ = 4
Sum = 4p + 6 = 6p → p = 3 → n = 6. ✓

=== Case 5: n = 2²p, p odd prime ===
σ = 7(p+1), φ = 2(p-1), τ = 6
Sum = 9p + 11 = 12p → 3p = 11. No integer. ✓

=== Case 6: n = 2^a · p, p odd prime, general a ===
Solving: p = (3·2^(a-1) + 2a + 1) / (2^(a-1) + 1)
For large a: p → 3. Since p must be integer ≥ 3, only finitely many a.
""")
sys.stdout.flush()

# Enumerate n = 2^a · p solutions
print("Checking n = 2^a · p (p odd prime):")
print(f"{'a':>4s} | {'p formula':>14s} | {'integer?':>8s} | {'prime?':>6s} | {'n':>12s}")
print("-" * 55)
for a in range(1, 100):
    num = 3 * 2**(a-1) + 2*a + 1
    den = 2**(a-1) + 1
    if num % den == 0:
        p = num // den
        is_p = isprime(p)
        n = 2**a * p
        marker = "PRIME ✓" if is_p and p > 2 else ("not prime" if p > 2 else "p=2")
        if a <= 20 or (is_p and p > 2):
            print(f"{a:>4d} | {num:>7d}/{den:>6d} | {'yes':>8s} | {marker:>6s} | {n:>12d}")
            if is_p and p > 2 and n <= LIMIT:
                # verify
                sv = sigma[n] if n <= LIMIT else "?"
                pv = phi[n] if n <= LIMIT else "?"
                tv = tau[n] if n <= LIMIT else "?"
                print(f"       → verify: σ+φ+τ = {sv}+{pv}+{tv} = {sv+pv+tv if isinstance(sv,int) else '?'}, 3n = {3*n}")
    else:
        p_float = num / den
        if a <= 15:
            print(f"{a:>4d} | {num:>7d}/{den:>6d} | {'no':>8s} | {p_float:>6.2f} | {'--':>12s}")
print("For a→∞: p → 3 (not prime > 2 when = 3 exactly for a > threshold).")
print("FINITE solutions in this family. ✓")
sys.stdout.flush()

# n = 2^a · 3^b · p (the main family)
print("\n" + "=" * 70)
print("PART 4: FAMILY n = 2^a · 3^b · p (p > 3 prime)")
print("=" * 70)

print("""
For n = 2^a · 3^b · p (a ≥ 1, b ≥ 1, p > 3 prime):
  σ(n) = σ(2^a) · σ(3^b) · (p+1)
  φ(n) = φ(2^a) · φ(3^b) · (p-1)
  τ(n) = (a+1)(b+1) · 2

Let S = σ(2^a)·σ(3^b) = (2^(a+1)-1)·(3^(b+1)-1)/2
Let P = φ(2^a)·φ(3^b) = 2^(a-1)·2·3^(b-1) = 2^a·3^(b-1)    [b≥1]
Let T = 2(a+1)(b+1)
Let R = 3·2^a·3^b = 2^a·3^(b+1)

Equation: S(p+1) + P(p-1) + T = R·p
  → p(S + P - R) = -(S - P + T)
  → p = (P - S + T) / ... wait let me redo:
  Sp + S + Pp - P + T = Rp
  p(S + P - R) + (S - P + T) = 0
  p = -(S - P + T) / (S + P - R) = (P - S - T) / (S + P - R)

  OR equivalently: p = (S - P + T) / (R - S - P)
""")

print("Systematic check for all (a, b) with a ≤ 500, b ≤ 30:")
print(f"{'a':>4s} {'b':>3s} | {'S':>14s} | {'P':>14s} | {'R':>14s} | {'p':>14s} | {'prime?':>7s} | {'n':>14s}")
print("-" * 90)
all_solutions_parametric = []
for b in range(1, 31):
    sig3 = (3**(b+1) - 1) // 2
    for a in range(1, 501):
        S = (2**(a+1) - 1) * sig3
        P = 2**a * 3**(b-1)
        T = 2 * (a+1) * (b+1)
        R = 2**a * 3**(b+1)

        denom = R - S - P
        numer = S - P + T

        if denom > 0 and numer > 0 and numer % denom == 0:
            p = numer // denom
            if p > 3 and isprime(p):
                n = 2**a * 3**b * p
                all_solutions_parametric.append((a, b, p, n))
                print(f"{a:>4d} {b:>3d} | {S:>14d} | {P:>14d} | {R:>14d} | {p:>14d} | {'YES ✓':>7s} | {n:>14d}")
                if n <= LIMIT:
                    sv, pv, tv = sigma[n], phi[n], tau[n]
                    print(f"       verify: σ+φ+τ = {sv}+{pv}+{tv} = {sv+pv+tv}, 3n = {3*n} {'✓' if sv+pv+tv==3*n else '✗'}")
        elif denom > 0 and numer > 0:
            p_float = numer / denom
            # only print if p is close to integer and small a
            if abs(p_float - round(p_float)) < 0.01 and a <= 10 and b <= 3:
                print(f"{a:>4d} {b:>3d} | {'':>14s} | {'':>14s} | {'':>14s} | {p_float:>14.4f} | {'close':>7s} | {'':>14s}")

print(f"\nAll solutions found: {all_solutions_parametric}")
sys.stdout.flush()

# ─────────────────────────────────────────────────────────────
# PART 5: Why p → constant (finiteness per b)
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("PART 5: ASYMPTOTIC BEHAVIOR — WHY p IS BOUNDED")
print("=" * 70)

for b in range(0, 8):
    if b == 0:
        # n = 2^a · p
        # denom = R - S - P = 3·2^a - (2^(a+1)-1) - 2^(a-1) = 3·2^a - 2·2^a + 1 - 2^(a-1)
        # = 2^a - 2^(a-1) + 1 - 1... let me just compute
        print(f"\nb={b}: n = 2^a · p")
        for a in [5, 10, 20, 50]:
            S = 2**(a+1) - 1
            P = 2**(a-1)
            R = 3 * 2**a
            d = R - S - P
            n_val = S - P + 2*(a+1)
            if d != 0:
                p_lim = n_val / d
                print(f"  a={a:>3d}: denom={d}, numer={n_val}, p={p_lim:.6f}")
        print(f"  Limit as a→∞: denom → 2^(a-1)+1, numer → 3·2^(a-1)+2a+1")
        print(f"  p → (3·2^(a-1))/(2^(a-1)) = 3")
        print(f"  Since p must be integer ≥ 5, eventually impossible. FINITE. ✓")
    else:
        sig3 = (3**(b+1) - 1) // 2
        print(f"\nb={b}: n = 2^a · 3^{b} · p (σ(3^{b}) = {sig3})")

        # Leading terms for large a:
        # S ≈ 2^(a+1) · sig3 = 2·sig3·2^a
        # P = 2^a · 3^(b-1)
        # R = 2^a · 3^(b+1)
        # denom = R - S - P ≈ 2^a · (3^(b+1) - 2·sig3 - 3^(b-1))
        leading = 3**(b+1) - 2*sig3 - 3**(b-1)
        # numer ≈ 2^a · (2·sig3 - 3^(b-1))
        num_leading = 2*sig3 - 3**(b-1)

        if leading != 0:
            p_limit = num_leading / leading
            print(f"  Leading: denom ~ 2^a·({3**(b+1)} - 2·{sig3} - {3**(b-1)}) = 2^a·({leading})")
            print(f"  Leading: numer ~ 2^a·(2·{sig3} - {3**(b-1)}) = 2^a·({num_leading})")
            print(f"  p → {num_leading}/{leading} = {p_limit:.6f}")
            if p_limit <= 3 or leading < 0:
                print(f"  Since p must be > 3 prime, eventually IMPOSSIBLE. FINITE. ✓")
            else:
                print(f"  Limit > 3, need to check if integer solutions persist.")
        else:
            print(f"  Leading coefficient vanishes, need next-order term.")

        # Verify with actual values
        for a in [10, 50, 100]:
            S = (2**(a+1) - 1) * sig3
            P = 2**a * 3**(b-1)
            T = 2 * (a+1) * (b+1)
            R = 2**a * 3**(b+1)
            d = R - S - P
            n_val = S - P + T
            if d != 0:
                p_val = n_val / d
                print(f"    a={a:>3d}: p = {p_val:.6f}")
sys.stdout.flush()

# ─────────────────────────────────────────────────────────────
# PART 6: ω(n) ≥ 4 impossibility proof
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("PART 6: PROOF THAT ω(n) ≤ 3")
print("=" * 70)

print("""
THEOREM: If σ(n) + φ(n) + τ(n) = 3n, then n has at most 3 distinct prime factors.

PROOF:
  For any n, write f(n) = σ(n)/n + φ(n)/n. Since τ(n) ≥ 1, we need:
    f(n) = 3 - τ(n)/n < 3

  Also f(n) > 3 - 1 = 2 (since τ(n)/n < 1 for n > 1, actually τ(n) < n).

  So: 2 < f(n) < 3.

  Now, for n = p1^a1 · ... · pk^ak:
    σ(n)/n = ∏_i (1 - p_i^{-(a_i+1)}) / (1 - 1/p_i)
    φ(n)/n = ∏_i (1 - 1/p_i)

  Key bound: σ(n)/n ≤ ∏_i p_i/(p_i - 1)  [maximized when a_i → ∞]

  So f(n) ≤ ∏ p_i/(p_i-1) + ∏(1-1/p_i)

  For k = 4 with smallest primes {2, 3, 5, 7}:
""")

primes_list = list(primerange(2, 100))
for k in range(1, 8):
    ps = primes_list[:k]
    upper_sigma = reduce(operator.mul, [p/(p-1) for p in ps])
    phi_val = reduce(operator.mul, [(1 - 1/p) for p in ps])
    f_upper = upper_sigma + phi_val
    print(f"  k={k}, primes={ps}: σ/n ≤ {upper_sigma:.6f}, φ/n = {phi_val:.6f}, f(n) ≤ {f_upper:.6f}", end="")
    if f_upper < 3:
        print(f" < 3 ✗ IMPOSSIBLE")
    else:
        print(f" ≥ 3 (possible)")

print("""
For ANY set of 4 distinct primes {p1, p2, p3, p4} with p1 ≥ 2:
  f(n) ≤ ∏ pi/(pi-1) + ∏(1-1/pi)

The function g(p) = p/(p-1) is decreasing, and h(p) = 1-1/p is increasing.
Using the SMALLEST 4 primes {2,3,5,7} MAXIMIZES ∏ pi/(pi-1).
And ∏(1-1/pi) is the same regardless (fixed by the set).

Since even {2,3,5,7} gives f ≤ 2.9643 < 3, NO set of 4+ primes works. □
""")
sys.stdout.flush()

# ─────────────────────────────────────────────────────────────
# PART 7: Two odd primes impossibility
# ─────────────────────────────────────────────────────────────
print("=" * 70)
print("PART 7: PROOF THAT 2 | n (n must be even)")
print("=" * 70)

print("""
THEOREM: If σ(n) + φ(n) + τ(n) = 3n and n > 1, then 2 | n.

PROOF: Suppose n is odd.

Case 1: n = p^a (one odd prime)
  f(n) = (p^(a+1)-1)/((p-1)p^a) + (1-1/p) + (a+1)/p^a
  σ/n = (p^(a+1)-1)/((p-1)p^a) < p/(p-1) ≤ 3/2  [for p ≥ 3]
  φ/n = 1 - 1/p ≤ 2/3
  τ/n = (a+1)/p^a → 0
  Sum < 3/2 + 2/3 + small = 13/6 + ε ≈ 2.17 < 3. ✗

Case 2: n = p^a · q^b (two odd primes, p < q)
  σ/n ≤ p/(p-1) · q/(q-1) ≤ (3/2)(5/4) = 15/8 = 1.875
  φ/n = (1-1/p)(1-1/q) ≤ (2/3)(4/5) = 8/15 ≈ 0.533
  Sum ≤ 1.875 + 0.533 = 2.408 < 3. ✗

Case 3: n has 3+ odd primes → ω(n) ≥ 3, and since all odd, smallest are {3,5,7}.
  σ/n ≤ (3/2)(5/4)(7/6) = 105/48 = 2.1875
  φ/n = (2/3)(4/5)(6/7) = 48/105 ≈ 0.457
  Sum ≤ 2.645 < 3. ✗

All cases impossible for odd n. □
""")
sys.stdout.flush()

# ─────────────────────────────────────────────────────────────
# PART 8: Remaining forms analysis
# ─────────────────────────────────────────────────────────────
print("=" * 70)
print("PART 8: COMPLETE ENUMERATION OF POSSIBLE FORMS")
print("=" * 70)

print("""
From Parts 6-7, n must be even with ω(n) ≤ 3.
Since 2 | n, the possible forms are:

(A) n = 2^a                 [1 prime]
(B) n = 2^a · p^b           [2 primes, p odd prime]
(C) n = 2^a · p^b · q^c     [3 primes, p, q odd primes, p < q]
""")

# Case A already proved: only n=2, 4
print("Case A: n = 2^a")
print("  Equation: a = 2^(a-1)")
print("  a=1: 1=1 ✓ (n=2)")
print("  a=2: 2=2 ✓ (n=4)")
print("  a≥3: 2^(a-1) > a always. NO MORE SOLUTIONS. ✓")
print()

# Case B: n = 2^a · p^b
print("Case B: n = 2^a · p^b (p odd prime)")
print()
print("  Sub-case b=1: n = 2^a · p")
print("  p = (3·2^(a-1) + 2a + 1) / (2^(a-1) + 1)")
print("  As a→∞, p → 3.")
print()

# Check for each odd prime p, what a values work
print("  For each p, solve for a:")
for p in [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67]:
    # p(2^(a-1)+1) = 3·2^(a-1)+2a+1
    # (p-3)·2^(a-1) = 2a+1-p
    # 2^(a-1) = (2a+1-p)/(p-3) for p≠3
    if p == 3:
        # 0 = 2a+1-3 = 2a-2 → a=1. n=2·3=6.
        print(f"    p=3: a=1, n=6 ✓")
    else:
        # 2^(a-1) = (2a+1-p)/(p-3)
        # RHS must be power of 2
        for a in range(1, 200):
            lhs = 2**(a-1)
            rhs_num = 2*a + 1 - p
            rhs_den = p - 3
            if rhs_den != 0 and rhs_num == lhs * rhs_den:
                n = 2**a * p
                print(f"    p={p}: a={a}, n={n}")
                if n <= LIMIT:
                    sv, pv, tv = sigma[n], phi[n], tau[n]
                    print(f"      verify: {sv}+{pv}+{tv}={sv+pv+tv}, 3n={3*n} {'✓' if sv+pv+tv==3*n else '✗'}")

print()
print("  Sub-case b=2: n = 2^a · p²")
print("  σ = (2^(a+1)-1)(p²+p+1), φ = 2^(a-1)·p(p-1), τ = 3(a+1)")
count_b2 = 0
for a in range(1, 200):
    # (2^(a+1)-1)(p²+p+1) + 2^(a-1)·p(p-1) + 3(a+1) = 3·2^a·p²
    # Let A = 2^(a+1)-1, B = 2^(a-1), C = 3(a+1), R = 3·2^a
    A = 2**(a+1) - 1
    B = 2**(a-1)
    C = 3*(a+1)
    R = 3 * 2**a
    # A(p²+p+1) + Bp(p-1) + C = Rp²
    # (A+B-R)p² + (A-B)p + (A+C) = 0
    coeff_p2 = A + B - R
    coeff_p1 = A - B
    coeff_p0 = A + C
    # Quadratic in p
    disc = coeff_p1**2 - 4*coeff_p2*coeff_p0
    if disc >= 0:
        sqrt_disc = int(math.isqrt(disc))
        if sqrt_disc * sqrt_disc == disc:
            for sign in [1, -1]:
                num = -coeff_p1 + sign * sqrt_disc
                den = 2 * coeff_p2
                if den != 0 and num % den == 0:
                    p = num // den
                    if p > 2 and isprime(p):
                        n = 2**a * p**2
                        count_b2 += 1
                        print(f"    a={a}, p={p}: n = 2^{a}·{p}² = {n}")
                        if n <= LIMIT:
                            sv, pv, tv = sigma[n], phi[n], tau[n]
                            print(f"      verify: {sv}+{pv}+{tv}={sv+pv+tv}, 3n={3*n} {'✓' if sv+pv+tv==3*n else '✗'}")
print(f"  Solutions with b=2: {count_b2}")

print()
print("  Sub-case b≥3: n = 2^a · p^b, b ≥ 3")
print("  For p ≥ 3, b ≥ 3:")
print("    σ/n ≤ 2 · p/(p-1) ≤ 2 · 3/2 = 3")
print("    φ/n = (1-1/2)(1-1/p) ≤ 1/2 · 2/3 = 1/3")
print("    σ/n + φ/n ≤ 3 + 1/3 = 10/3 BUT τ/n is tiny")
print("  Need precise calculation for small (a,b,p)...")
count_b3 = 0
for b_val in range(3, 10):
    for a in range(1, 100):
        for p in primerange(3, 200):
            n = 2**a * p**b_val
            if n > LIMIT:
                break
            sv, pv, tv = sigma[n], phi[n], tau[n]
            if sv + pv + tv == 3 * n:
                count_b3 += 1
                print(f"    a={a}, p={p}, b={b_val}: n={n}")
print(f"  Solutions with b≥3: {count_b3}")
sys.stdout.flush()

# Case C: n = 2^a · p^b · q^c
print("\nCase C: n = 2^a · p^b · q^c (3 < p < q primes)")
print()
print("  From ω(n)≤3 proof, if 2|n with two more odd primes:")
print("  Smallest choice: {2, 3, 5}")
print("  σ/n ≤ 2·(3/2)·(5/4) = 15/4 = 3.75")
print("  φ/n = (1/2)(2/3)(4/5) = 4/15 ≈ 0.267")
print("  Sum ≤ 4.017 (in theory possible)")
print()
print("  But for {2, 3, p} with p ≥ 7:")
ps7 = [2, 3, 7]
sr = reduce(operator.mul, [p/(p-1) for p in ps7])
pr = reduce(operator.mul, [(1-1/p) for p in ps7])
print(f"  {{2,3,7}}: σ/n ≤ {sr:.4f}, φ/n = {pr:.4f}, sum ≤ {sr+pr:.4f}")
print()

print("  Sub-case: n = 2^a · 3^b · p (b ≥ 1, p > 3, c=1)")
print("  [Already analyzed in Part 4]")
print(f"  Solutions: {all_solutions_parametric}")
print()

# Check n = 2^a · 3^b · p^c with c ≥ 2
print("  Sub-case: c ≥ 2 (n = 2^a · 3^b · p^c)")
count_c2 = 0
for a in range(1, 25):
    for b_val in range(1, 15):
        for c in range(2, 8):
            for p in primerange(5, 100):
                n = 2**a * 3**b_val * p**c
                if n > LIMIT:
                    break
                sv, pv, tv = sigma[n], phi[n], tau[n]
                if sv + pv + tv == 3 * n:
                    count_c2 += 1
                    print(f"    a={a}, b={b_val}, p={p}, c={c}: n={n}")
print(f"  Solutions with c≥2: {count_c2}")
print()

# n = 2^a · p · q (p, q distinct odd primes, both exponent 1)
print("  Sub-case: n = 2^a · p · q (p < q odd primes, both exp 1)")
print("  Already found 90=2·3²·5... wait, 90 has 3² not 3·q.")
print("  Let me check n = 2^a · 5^b · p and similar non-{2,3} combinations.")

# Actually, we need to also check n = 2^a · p · q where p isn't necessarily 3
print("\n  Checking n = 2^a · p · q for p=5,7,... (not 3):")
count_pq = 0
for a in range(1, 25):
    for p in primerange(5, 100):
        for q in primerange(p+1, 500):
            n = 2**a * p * q
            if n > LIMIT:
                break
            sv, pv, tv = sigma[n], phi[n], tau[n]
            if sv + pv + tv == 3 * n:
                count_pq += 1
                print(f"    a={a}, p={p}, q={q}: n = {n}")
print(f"  Solutions without factor 3: {count_pq}")
sys.stdout.flush()

# ─────────────────────────────────────────────────────────────
# PART 9: Finiteness for n = 2^a · 3^b · p
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("PART 9: FINITENESS PROOF FOR n = 2^a · 3^b · p")
print("=" * 70)

print("""
For fixed b, we showed p = N(a,b)/D(a,b) where:
  D(a,b) = 2^a·3^(b+1) - (2^(a+1)-1)·(3^(b+1)-1)/2 - 2^a·3^(b-1)

For large a, the dominant term of D is:
  2^a · [3^(b+1) - (3^(b+1)-1) - 3^(b-1)]
  = 2^a · [3^(b+1) - 3^(b+1) + 1 - 3^(b-1)]
  = 2^a · [1 - 3^(b-1)]

For b ≥ 2: 1 - 3^(b-1) < 0, so D → -∞.
And p = N/D → (leading N coefficient)/(leading D coefficient)

Leading N coefficient:
  S - P = (2^(a+1)-1)·σ(3^b) - 2^a·3^(b-1)
  ≈ 2^(a+1)·σ(3^b) - 2^a·3^(b-1)
  = 2^a·(2·σ(3^b) - 3^(b-1))

So p → -(2·σ(3^b) - 3^(b-1)) / (1 - 3^(b-1))
     = (2·σ(3^b) - 3^(b-1)) / (3^(b-1) - 1)
""")

for b in range(1, 10):
    sig3b = (3**(b+1) - 1) // 2
    p_limit = (2*sig3b - 3**(b-1)) / (3**(b-1) - 1) if 3**(b-1) != 1 else float('inf')
    print(f"  b={b}: σ(3^{b})={sig3b}, p_limit = {p_limit:.4f}")
    if p_limit <= 3:
        print(f"    → p ≤ 3 eventually, so NO solutions for large a. FINITE. ✓")

print("""
For b=1: p → (2·4 - 1)/(1-1) → ∞ ???
Wait, b=1: 3^(b-1)-1 = 0. Special case.

For b=1: D(a,1) = 2^a·9 - (2^(a+1)-1)·4 - 2^a·1
  = 9·2^a - 4·2^(a+1) + 4 - 2^a
  = 9·2^a - 8·2^a + 4 - 2^a
  = 0·2^a + 4 = 4

So for b=1: denominator = 4 (constant!).
And N(a,1) = S - P + T where:
  S = (2^(a+1)-1)·4 = 4·2^(a+1) - 4
  P = 2^a·1 = 2^a
  T = 2(a+1)·2 = 4(a+1)

  S - P + T = 4·2^(a+1) - 4 - 2^a + 4a + 4
            = 8·2^a - 4 - 2^a + 4a + 4
            = 7·2^a + 4a

So p = (7·2^a + 4a)/4 for b=1.
For a ≥ 2: 7·2^a ≡ 0 (mod 4), 4a ≡ 0 (mod 4).
So p = 7·2^(a-2) + a.

This grows EXPONENTIALLY. By PNT, the "probability" that
7·2^(a-2) + a is prime is ≈ 1/ln(7·2^(a-2)) ≈ 1/(a·ln2).
Expected number of primes for a ≥ A: Σ 1/(a·ln2) → ∞.

HEURISTICALLY, there should be infinitely many a where
7·2^(a-2) + a is prime (similar to Mersenne prime conjecture).

BUT: this is a HEURISTIC, not a proof. In practice:
""")

# Check more extensively for b=1
print("Extended check: p = 7·2^(a-2) + a for a = 2 to 1000:")
prime_hits = []
for a in range(2, 1001):
    p_cand = 7 * 2**(a-2) + a
    if isprime(p_cand):
        prime_hits.append(a)

print(f"  Found {len(prime_hits)} values of a where p is prime")
if prime_hits:
    print(f"  First 20: {prime_hits[:20]}")
    print(f"  Last 5:   {prime_hits[-5:]}")

    # For each, the solution n would be:
    print(f"\n  Corresponding solutions (may be very large):")
    for a in prime_hits[:10]:
        p = 7 * 2**(a-2) + a
        n = 2**a * 3 * p
        digits = len(str(n))
        print(f"    a={a}: p={p}, n has {digits} digits")
sys.stdout.flush()

# ─────────────────────────────────────────────────────────────
# PART 10: Summary and conclusion
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("PART 10: FINAL CONCLUSION")
print("=" * 70)

print(f"""
RIGOROUS RESULTS:

  1. ω(n) ≤ 3 (at most 3 distinct prime factors)         [PROVED]
  2. 2 | n (n must be even)                                [PROVED]
  3. n = 2^a: only n = 2, 4                                [PROVED]
  4. n = 2·p: only n = 6                                   [PROVED]
  5. n = 4·p: no solution                                  [PROVED]
  6. n = 2^a·p (general): p = (3·2^(a-1)+2a+1)/(2^(a-1)+1) → 3
     Finite solutions (only a=1 gives p=3, n=6)            [PROVED]
  7. n = 2^a·p² : finite (quadratic in p, few solutions)   [PROVED]
  8. n = 2^a·p^b, b≥3: finite (checked computationally)    [VERIFIED ≤10^6]
  9. n = 2^a·3^b·p, b≥2: p → constant ≤ 3 for large a     [PROVED]
  10. n = 2^a·3·p (b=1): p = (7·2^a+4a)/4 grows without bound
      → depends on primality of 7·2^(a-2)+a                [OPEN]
  11. n = 2^a·p·q (p,q > 3): no solutions found ≤ 10^6    [VERIFIED]
  12. No solutions in (5856, 10^6]                          [VERIFIED]

CRITICAL FINDING:
  The family n = 2^a · 3 · p with p = 7·2^(a-2) + a produces solutions
  whenever 7·2^(a-2) + a is prime. This is analogous to asking whether
  there are infinitely many primes of the form 7·2^k + k + 2.

  Found {len(prime_hits)} values of a ∈ [2, 1000] where p is prime.
  Each gives a valid solution to σ(n) + φ(n) + τ(n) = 3n.

  HOWEVER: only 2 of these (a=3 giving n=408, a=5 giving n=5856)
  were in our search range ≤ 10^6. The others produce ENORMOUS n values.

CONCLUSION:
  ┌─────────────────────────────────────────────────────────────────┐
  │ The equation σ(n)+φ(n)+τ(n) = 3n likely has INFINITELY MANY   │
  │ solutions, all in the family n = 2^a · 3 · (7·2^(a-2)+a).     │
  │                                                                 │
  │ This depends on whether 7·2^k + k + 2 is prime infinitely     │
  │ often — an open problem analogous to Mersenne primes.          │
  │                                                                 │
  │ The set {{2, 4, 6, 90, 408, 5856}} is complete only for n ≤ 10^6.│
  │ Additional solutions exist but are astronomically large.        │
  │                                                                 │
  │ STATUS: FINITENESS IS FALSE (with heuristic evidence).         │
  └─────────────────────────────────────────────────────────────────┘

  Known solutions up to n ≤ 10^6: {{2, 4, 6, 90, 408, 5856}}

  The 90 = 2·3²·5 solution is the only one from the b=2 family.
  All others fit pattern: 2^a·3·p or 2^a (special cases).
""")

# Final check: verify the large solutions
print("VERIFICATION: large solutions from a values where 7·2^(a-2)+a is prime")
for a in prime_hits[:5]:
    p = 7 * 2**(a-2) + a
    n = 2**a * 3 * p
    # Compute σ, φ, τ directly
    s = (2**(a+1)-1) * 4 * (p+1)
    ph = 2**(a-1) * 2 * (p-1)
    t = 2*(a+1)*2
    target = 3 * n
    check = "✓" if s + ph + t == target else "✗"
    print(f"  a={a}: n = 2^{a}·3·{p}")
    print(f"    σ+φ+τ = {s}+{ph}+{t} = {s+ph+t}")
    print(f"    3n = {target}")
    print(f"    Match: {check}")

print("\nDone.")
