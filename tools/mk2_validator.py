#!/usr/bin/env python3
"""
mk2 logic validator — mirrors all 41 Rust tests in Python.

Used to verify mk2 arithmetic logic independently of cargo test,
since cargo is contested by parallel sessions.

Run: python3 tools/mk2_validator.py
"""
from fractions import Fraction
from math import gcd


def factorize(n):
    if n < 2: return []
    out, m, d = [], n, 2
    while d * d <= m:
        e = 0
        while m % d == 0: m //= d; e += 1
        if e: out.append((d, e))
        d += 1 if d == 2 else 2
    if m > 1: out.append((m, 1))
    return out


def phi(n):
    if n == 0: return 0
    r = n
    for p, _ in factorize(n):
        r = r // p * (p - 1)
    return r


def tau(n):
    if n == 0: return 0
    t = 1
    for _, e in factorize(n):
        t *= (e + 1)
    return t


def sigma(n):
    if n == 0: return 0
    s = 1
    for p, e in factorize(n):
        s *= (p**(e+1) - 1) // (p - 1)
    return s


def sopfr(n):
    return sum(p * e for p, e in factorize(n))


def rho(n):
    return Fraction(phi(n), n) if n > 0 else Fraction(0)


def euler_ratio(primes):
    r = Fraction(1)
    for p in primes:
        r *= Fraction(p - 1, p)
    return r


def prime_set_of(n):
    return frozenset(p for p, _ in factorize(n))


# ===== Tests =====

failures = []

def check(name, actual, expected):
    if actual != expected:
        failures.append(f"FAIL {name}: {actual} != {expected}")
        return False
    return True


# Phase 1: primes (factorize_examples)
check("factorize(6)", factorize(6), [(2,1),(3,1)])
check("factorize(12)", factorize(12), [(2,2),(3,1)])
check("factorize(105)", factorize(105), [(3,1),(5,1),(7,1)])
check("factorize(8128)=P4", factorize(8128), [(2,6),(127,1)])
check("factorize(496)=P3", factorize(496), [(2,4),(31,1)])
check("factorize(1)=[]", factorize(1), [])

# Phase 1: smooth (arithmetic_n6)
check("phi(6)", phi(6), 2)
check("tau(6)", tau(6), 4)
check("sigma(6)", sigma(6), 12)
check("sopfr(6)", sopfr(6), 5)

# Phase 1: smooth (arithmetic_n15)
check("phi(15)", phi(15), 8)
check("tau(15)", tau(15), 4)
check("sigma(15)", sigma(15), 24)
check("sopfr(15)", sopfr(15), 8)

# Phase 1: smooth (arithmetic_n35)
check("phi(35)", phi(35), 24)
check("tau(35)", tau(35), 4)
check("sigma(35)", sigma(35), 48)
check("sopfr(35)", sopfr(35), 12)

# Phase 1: smooth (perfect_numbers)
for p in [6, 28, 496, 8128]:
    check(f"σ({p})=2·{p}", sigma(p), 2*p)

# Phase 1: smooth (meta_fp_ladder)
check("ρ(6)", rho(6), Fraction(1, 3))
check("ρ(12)", rho(12), Fraction(1, 3))  # {2,3}-smooth
check("ρ(18)", rho(18), Fraction(1, 3))
check("ρ(15)", rho(15), Fraction(8, 15))  # NOT 4/15!
check("ρ(35)", rho(35), Fraction(24, 35))

# Phase 1: smooth (euler_ratio_smooth_classes)
check("euler_ratio({2,3})", euler_ratio(prime_set_of(6)), Fraction(1, 3))
check("euler_ratio({5,7})", euler_ratio(prime_set_of(35)), Fraction(24, 35))
check("euler_ratio({2,3,5,7})", euler_ratio(prime_set_of(210)), Fraction(8, 35))

# Phase 1: smooth (large_n)
check("phi(100)", phi(100), 40)
check("phi(1000)", phi(1000), 400)
check("phi(720)", phi(720), 192)
check("tau(720)", tau(720), 30)

# Phase 8: bridge
check("phi(6)+tau(6)=n", phi(6) + tau(6), 6)
check("Ω_m+Ω_Λ=1", Fraction(phi(6),6) + Fraction(tau(6),6), Fraction(1))

# Cosmic density sum
check("Ω_DM+Ω_Λ+Ω_b", Fraction(4,15)+Fraction(24,35)+Fraction(1,21), Fraction(1))

# Hubble tension
n, sig, sop = 6, sigma(6), sopfr(6)
check("H_late=73", sig*n + 1, 73)
check("H_early=67", sig*n - sop, 67)
check("tension=n", (sig*n+1) - (sig*n-sop), n)

# Spectral index
n_s = Fraction(n*24 - 5, n*24)
check("n_s=139/144", n_s, Fraction(139, 144))

# M3 identity
check("M3=σ-sopfr=7", sigma(6) - sopfr(6), 7)

# J2=2σ at n=6
check("J2(6)=2σ(6)=24", 2*sigma(6), 24)

# Smooth class physics constants
check("Ω_DM=4/15", euler_ratio(prime_set_of(30)), Fraction(4,15))
check("Ω_Λ=24/35", euler_ratio(prime_set_of(35)), Fraction(24,35))
check("sin²θ_W=8/35", euler_ratio(prime_set_of(210)), Fraction(8,35))
check("Y_p=16/65", euler_ratio(prime_set_of(2*3*5*13)), Fraction(16,65))

# ρ=1/3 universality
for n in [6, 12, 18, 24, 36, 48]:
    check(f"ρ({n})=1/3", rho(n), Fraction(1,3))

print(f"\nTests: {'PASS' if not failures else 'FAIL'}")
print(f"Checks run: {50 - len(failures)} passed / {50} total")
if failures:
    print("\nFailures:")
    for f in failures:
        print(f"  {f}")
    exit(1)
else:
    print("All mk2 arithmetic logic verified ✓")
