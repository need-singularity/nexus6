#!/usr/bin/env python3
"""
master_ratio.py — Master Ratio & Dedekind Psi Calculator

Computes the 5-function master ratio:
    Ω(n) = σ(n)·ψ(n) / (n·τ(n)·φ(n))

and related quantities across perfect numbers, factorials, partitions,
Catalan numbers, and Ramanujan tau values.

Key identity: ψ(n)/φ(n) = n  iff n ∈ {1, 6}  (for n>1, only n=6).
"""

import argparse
import sys
from fractions import Fraction
from math import factorial, isqrt, log2
from functools import lru_cache


# ─────────────────────────────────────────────────────────
#  Core arithmetic functions (exact, using Fraction)
# ─────────────────────────────────────────────────────────

def factorize(n):
    """Return dict {prime: exponent} for n >= 1."""
    if n < 1:
        raise ValueError(f"factorize requires n >= 1, got {n}")
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
    """σ(n): sum of divisors."""
    if n < 1:
        raise ValueError("n must be >= 1")
    f = factorize(n)
    result = Fraction(1)
    for p, a in f.items():
        result *= Fraction(p**(a + 1) - 1, p - 1)
    return result


def tau(n):
    """τ(n): number of divisors."""
    if n < 1:
        raise ValueError("n must be >= 1")
    f = factorize(n)
    result = 1
    for a in f.values():
        result *= (a + 1)
    return Fraction(result)


def phi(n):
    """φ(n): Euler totient."""
    if n < 1:
        raise ValueError("n must be >= 1")
    f = factorize(n)
    result = Fraction(n)
    for p in f:
        result *= Fraction(p - 1, p)
    return result


def psi(n):
    """ψ(n): Dedekind psi function = n·∏(1 + 1/p) for p | n."""
    if n < 1:
        raise ValueError("n must be >= 1")
    f = factorize(n)
    result = Fraction(n)
    for p in f:
        result *= Fraction(p + 1, p)
    return result


def omega_small(n):
    """ω(n): number of distinct prime factors."""
    return len(factorize(n))


def Omega_big(n):
    """Ω(n): number of prime factors with multiplicity."""
    return sum(factorize(n).values())


def master_omega(n):
    """Ω(n) = σ(n)·ψ(n) / (n·τ(n)·φ(n))."""
    if n < 1:
        raise ValueError("n must be >= 1")
    s = sigma(n)
    t = tau(n)
    p = phi(n)
    ps = psi(n)
    numer = s * ps
    denom = Fraction(n) * t * p
    return numer / denom


# ─────────────────────────────────────────────────────────
#  Partition functions
# ─────────────────────────────────────────────────────────

@lru_cache(maxsize=None)
def partition_p(n):
    """p(n): unrestricted partition count."""
    if n < 0:
        return 0
    if n == 0:
        return 1
    total = 0
    k = 1
    while True:
        # Generalised pentagonal numbers
        g1 = k * (3 * k - 1) // 2
        g2 = k * (3 * k + 1) // 2
        sign = (-1) ** (k + 1)
        if g1 > n and g2 > n:
            break
        if g1 <= n:
            total += sign * partition_p(n - g1)
        if g2 <= n:
            total += sign * partition_p(n - g2)
        k += 1
    return total


@lru_cache(maxsize=None)
def partition_q(n):
    """q(n): partition into distinct parts."""
    if n < 0:
        return 0
    if n == 0:
        return 1
    total = 0
    k = 1
    while True:
        # Pentagonal-like recurrence for distinct partitions
        g1 = k * (3 * k - 1) // 2
        g2 = k * (3 * k + 1) // 2
        sign = (-1) ** (k + 1)
        if g1 > n:
            break
        total += sign * partition_q(n - g1)
        if g2 <= n:
            total += sign * partition_q(n - g2)
        k += 1
    return total


def partition_even(n):
    """p_even(n): number of partitions of n into even parts.
    Equals p(n/2) if n even, else 0."""
    if n % 2 != 0:
        return 0
    return partition_p(n // 2)


# ─────────────────────────────────────────────────────────
#  Catalan numbers
# ─────────────────────────────────────────────────────────

def catalan(n):
    """C_n = (2n)! / ((n+1)! · n!)."""
    from math import comb
    return comb(2 * n, n) // (n + 1)


# ─────────────────────────────────────────────────────────
#  Ramanujan tau
# ─────────────────────────────────────────────────────────

def ramanujan_tau(n):
    """Compute Ramanujan τ(n) via the definition:
    Σ τ(n)q^n = q·∏(1-q^k)^24,  using enough terms."""
    # Use a simple convolution approach for small n
    N = n + 1
    # Start with coefficients of q · prod(1-q^k)^24
    # = q · (Dedekind eta)^24
    # We compute coefficients of prod(1-q^k)^24 up to q^(n-1)
    # then shift by 1.
    coeffs = [0] * N
    coeffs[0] = 1

    for k in range(1, N):
        # Multiply by (1 - q^k)^24
        # We expand (1-q^k)^24 using binomial theorem
        # and convolve, but easier: multiply 24 times by (1-q^k)
        for _ in range(24):
            for j in range(N - 1, k - 1, -1):
                coeffs[j] -= coeffs[j - k]

    # coeffs[m] is the coefficient of q^m in prod(1-q^k)^24
    # tau(n) is the coefficient of q^n in q·prod = coeffs[n-1]
    if n - 1 < len(coeffs):
        return coeffs[n - 1]
    return None


# ─────────────────────────────────────────────────────────
#  Perfect / multiperfect number detection
# ─────────────────────────────────────────────────────────

def find_perfect_and_multiperfect(limit):
    """Find all n <= limit where σ(n)/n is an integer (k-perfect)."""
    results = []
    for n in range(1, limit + 1):
        s = sigma(n)
        if s % n == 0:
            k = int(s // n)
            results.append((n, k))
    return results


# ─────────────────────────────────────────────────────────
#  Display helpers
# ─────────────────────────────────────────────────────────

def frac_str(f):
    """Format a Fraction nicely."""
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def frac_float(f):
    """Fraction to float string."""
    return f"{float(f):.6f}"


def print_breakdown(n):
    """Print full breakdown for a single n."""
    s = sigma(n)
    t = tau(n)
    p = phi(n)
    ps = psi(n)
    om = master_omega(n)
    w = omega_small(n)
    W = Omega_big(n)
    facs = factorize(n)

    print(f"\n{'═' * 60}")
    print(f"  n = {n}")
    print(f"  factorization = {format_factorization(facs)}")
    print(f"{'─' * 60}")
    print(f"  σ(n)  = {frac_str(s):>12s}   (sum of divisors)")
    print(f"  τ(n)  = {frac_str(t):>12s}   (number of divisors)")
    print(f"  φ(n)  = {frac_str(p):>12s}   (Euler totient)")
    print(f"  ψ(n)  = {frac_str(ps):>12s}   (Dedekind psi)")
    print(f"  ω(n)  = {w:>12d}   (distinct primes)")
    print(f"  Ω(n)  = {W:>12d}   (primes with multiplicity)")
    print(f"{'─' * 60}")
    print(f"  Master ratio Ω(n) = σψ/(nτφ)")
    print(f"    = {frac_str(s)}·{frac_str(ps)} / ({n}·{frac_str(t)}·{frac_str(p)})")
    print(f"    = {frac_str(om)}  ≈ {frac_float(om)}")
    is_int = om.denominator == 1
    print(f"    integer? {'YES ✓' if is_int else 'no'}")
    print(f"{'═' * 60}")


def format_factorization(facs):
    """Pretty-print factorization dict."""
    if not facs:
        return "1"
    parts = []
    for p in sorted(facs):
        a = facs[p]
        if a == 1:
            parts.append(str(p))
        else:
            parts.append(f"{p}^{a}")
    return " · ".join(parts)


# ─────────────────────────────────────────────────────────
#  Mode: --omega N
# ─────────────────────────────────────────────────────────

def mode_omega(n):
    """Compute Ω(N) with full breakdown."""
    print_breakdown(n)


# ─────────────────────────────────────────────────────────
#  Mode: --psi-phi N
# ─────────────────────────────────────────────────────────

def mode_psi_phi(n):
    """Compute ψ/φ ratio and check if = n."""
    print(f"\n{'═' * 60}")
    print(f"  Checking ψ(n)/φ(n) = n  for n = 1..{n}")
    print(f"  (Identity holds iff n = 1 or n = 6 for n > 1)")
    print(f"{'═' * 60}")
    print(f"\n  {'n':>6s}  {'ψ(n)':>10s}  {'φ(n)':>10s}  {'ψ/φ':>14s}  {'= n?':>6s}")
    print(f"  {'─'*6}  {'─'*10}  {'─'*10}  {'─'*14}  {'─'*6}")

    matches = []
    for k in range(1, n + 1):
        ps = psi(k)
        p = phi(k)
        ratio = ps / p
        is_n = (ratio == Fraction(k))
        if is_n:
            matches.append(k)
        # Print all small n, plus any matches for large n
        if k <= 30 or is_n:
            marker = "YES ✓" if is_n else ""
            print(f"  {k:>6d}  {frac_str(ps):>10s}  {frac_str(p):>10s}  {frac_str(ratio):>14s}  {marker:>6s}")

    if n > 30:
        print(f"  ... (checked up to n = {n})")

    print(f"\n  Matches where ψ(n)/φ(n) = n:  {matches}")
    if 6 in matches:
        print(f"  → n = 6 is the ONLY n > 1 where ψ/φ = n  (from {len(matches)} match(es))")
    print()


# ─────────────────────────────────────────────────────────
#  Mode: --integer-omega N
# ─────────────────────────────────────────────────────────

def mode_integer_omega(limit):
    """Find all n <= N where Ω(n) is an integer."""
    print(f"\n{'═' * 60}")
    print(f"  Finding all n ≤ {limit} where Ω(n) = σψ/(nτφ) ∈ Z")
    print(f"{'═' * 60}\n")

    found = []
    for n in range(1, limit + 1):
        om = master_omega(n)
        if om.denominator == 1:
            found.append((n, int(om.numerator)))

    print(f"  {'n':>8s}  {'Ω(n)':>8s}  factorization")
    print(f"  {'─'*8}  {'─'*8}  {'─'*30}")
    for n, val in found:
        facs = factorize(n)
        print(f"  {n:>8d}  {val:>8d}  {format_factorization(facs)}")

    print(f"\n  Total: {len(found)} integers found in [1, {limit}]")
    ns = [n for n, _ in found]
    print(f"  Set: {{{', '.join(str(x) for x in ns)}}}")
    print()


# ─────────────────────────────────────────────────────────
#  Mode: --perfect N
# ─────────────────────────────────────────────────────────

def mode_perfect(limit):
    """Compute Ω at all perfect and multiperfect numbers ≤ N."""
    print(f"\n{'═' * 60}")
    print(f"  Master ratio at perfect & multiperfect numbers ≤ {limit}")
    print(f"{'═' * 60}\n")

    pm = find_perfect_and_multiperfect(limit)

    print(f"  {'n':>8s}  {'k':>4s}  {'σ(n)':>10s}  {'τ(n)':>6s}  {'φ(n)':>10s}  {'ψ(n)':>10s}  {'Ω(n)':>14s}")
    print(f"  {'─'*8}  {'─'*4}  {'─'*10}  {'─'*6}  {'─'*10}  {'─'*10}  {'─'*14}")

    for n, k in pm:
        if n == 1 and k == 1:
            # skip trivial n=1
            continue
        s = sigma(n)
        t = tau(n)
        p = phi(n)
        ps = psi(n)
        om = master_omega(n)
        int_mark = " ✓" if om.denominator == 1 else ""
        print(f"  {n:>8d}  {k:>4d}  {frac_str(s):>10s}  {frac_str(t):>6s}  {frac_str(p):>10s}  {frac_str(ps):>10s}  {frac_str(om):>14s}{int_mark}")

    print()


# ─────────────────────────────────────────────────────────
#  Mode: --factorial N
# ─────────────────────────────────────────────────────────

def mode_factorial(limit):
    """Compute Ω(n!) for n=1..N, check σφ = τ! identity."""
    print(f"\n{'═' * 60}")
    print(f"  Master ratio Ω(n!) and σ·φ vs (τ)! for n = 1..{limit}")
    print(f"{'═' * 60}\n")

    print(f"  {'n':>4s}  {'n!':>10s}  {'σ':>12s}  {'τ':>8s}  {'φ':>12s}  {'ψ':>12s}  {'Ω(n!)':>14s}  {'σ·φ':>14s}  {'τ!':>14s}  {'σφ=τ!?':>7s}")
    print(f"  {'─'*4}  {'─'*10}  {'─'*12}  {'─'*8}  {'─'*12}  {'─'*12}  {'─'*14}  {'─'*14}  {'─'*14}  {'─'*7}")

    for n in range(1, limit + 1):
        nf = factorial(n)
        s = sigma(nf)
        t = tau(nf)
        p = phi(nf)
        ps = psi(nf)
        om = master_omega(nf)
        sp = s * p
        t_int = int(t)
        try:
            tf = Fraction(factorial(t_int))
        except (OverflowError, ValueError):
            tf = None

        if tf is not None:
            match = "YES ✓" if sp == tf else "no"
            tf_str = str(tf) if tf < 10**12 else f"~10^{len(str(tf))-1}"
        else:
            match = "?"
            tf_str = "overflow"

        sp_str = str(sp) if sp < 10**12 else f"~10^{len(str(int(sp)))-1}"

        print(f"  {n:>4d}  {nf:>10d}  {frac_str(s):>12s}  {frac_str(t):>8s}  {frac_str(p):>12s}  {frac_str(ps):>12s}  {frac_str(om):>14s}  {sp_str:>14s}  {tf_str:>14s}  {match:>7s}")

    print()


# ─────────────────────────────────────────────────────────
#  Mode: --partition N
# ─────────────────────────────────────────────────────────

def mode_partition(limit):
    """Compute p(n), q(n), p_even(n) and compare with σ,τ,φ."""
    print(f"\n{'═' * 60}")
    print(f"  Partitions vs arithmetic functions for n = 1..{limit}")
    print(f"{'═' * 60}\n")

    print(f"  {'n':>4s}  {'p(n)':>8s}  {'q(n)':>8s}  {'p_e(n)':>8s}  {'σ(n)':>8s}  {'τ(n)':>6s}  {'φ(n)':>8s}  {'p/σ':>10s}  {'p/τ':>10s}  {'q/φ':>10s}")
    print(f"  {'─'*4}  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*6}  {'─'*8}  {'─'*10}  {'─'*10}  {'─'*10}")

    for n in range(1, limit + 1):
        pn = partition_p(n)
        qn = partition_q(n)
        pen = partition_even(n)
        s = sigma(n)
        t = tau(n)
        p = phi(n)

        p_over_s = Fraction(pn) / s
        p_over_t = Fraction(pn) / t
        q_over_p = Fraction(qn) / p

        print(f"  {n:>4d}  {pn:>8d}  {qn:>8d}  {pen:>8d}  {frac_str(s):>8s}  {frac_str(t):>6s}  {frac_str(p):>8s}  {frac_str(p_over_s):>10s}  {frac_str(p_over_t):>10s}  {frac_str(q_over_p):>10s}")

    # Highlight coincidences
    print(f"\n  Notable coincidences:")
    for n in range(1, limit + 1):
        pn = partition_p(n)
        qn = partition_q(n)
        s = sigma(n)
        t = tau(n)
        p = phi(n)
        if pn == int(s):
            print(f"    p({n}) = σ({n}) = {pn}")
        if pn == int(t):
            print(f"    p({n}) = τ({n}) = {pn}")
        if qn == int(p):
            print(f"    q({n}) = φ({n}) = {qn}")
        if pn == int(p):
            print(f"    p({n}) = φ({n}) = {pn}")

    print()


# ─────────────────────────────────────────────────────────
#  Mode: --catalan N
# ─────────────────────────────────────────────────────────

def mode_catalan(limit):
    """Catalan numbers vs τφ = σ set intersection."""
    print(f"\n{'═' * 60}")
    print(f"  Catalan numbers C_n vs arithmetic for n = 0..{limit}")
    print(f"{'═' * 60}\n")

    print(f"  {'n':>4s}  {'C_n':>12s}  {'τ(C_n)':>8s}  {'φ(C_n)':>12s}  {'σ(C_n)':>14s}  {'τ·φ':>14s}  {'τφ=σ?':>7s}")
    print(f"  {'─'*4}  {'─'*12}  {'─'*8}  {'─'*12}  {'─'*14}  {'─'*14}  {'─'*7}")

    matches = []
    for n in range(0, limit + 1):
        cn = catalan(n)
        if cn < 1:
            continue
        t = tau(cn)
        p = phi(cn)
        s = sigma(cn)
        tp = t * p
        is_match = (tp == s)
        if is_match:
            matches.append(n)
        marker = "YES ✓" if is_match else ""
        print(f"  {n:>4d}  {cn:>12d}  {frac_str(t):>8s}  {frac_str(p):>12s}  {frac_str(s):>14s}  {frac_str(tp):>14s}  {marker:>7s}")

    print(f"\n  Matches where τ(C_n)·φ(C_n) = σ(C_n): n ∈ {{{', '.join(str(x) for x in matches)}}}")
    print()


# ─────────────────────────────────────────────────────────
#  Mode: --ramanujan
# ─────────────────────────────────────────────────────────

def mode_ramanujan():
    """Compute first 12 Ramanujan τ_R values and compare with σφ."""
    print(f"\n{'═' * 60}")
    print(f"  Ramanujan tau τ_R(n) vs σ(n)·φ(n) for n = 1..12")
    print(f"{'═' * 60}\n")

    print(f"  {'n':>4s}  {'τ_R(n)':>14s}  {'σ(n)':>10s}  {'φ(n)':>10s}  {'σ·φ':>14s}  {'τ_R/σ':>12s}  {'τ_R/φ':>12s}  {'τ_R/(σφ)':>14s}")
    print(f"  {'─'*4}  {'─'*14}  {'─'*10}  {'─'*10}  {'─'*14}  {'─'*12}  {'─'*12}  {'─'*14}")

    for n in range(1, 13):
        tr = ramanujan_tau(n)
        s = sigma(n)
        p = phi(n)
        sp = s * p

        if tr is None or tr == 0:
            print(f"  {n:>4d}  {'?':>14s}")
            continue

        tr_f = Fraction(tr)
        r_s = tr_f / s
        r_p = tr_f / p
        r_sp = tr_f / sp

        print(f"  {n:>4d}  {tr:>14d}  {frac_str(s):>10s}  {frac_str(p):>10s}  {frac_str(sp):>14s}  {frac_str(r_s):>12s}  {frac_str(r_p):>12s}  {frac_str(r_sp):>14s}")

    # Known values for reference
    print(f"\n  Reference (OEIS A000594):")
    known = [1, -24, 252, -1472, 4830, -6048, -16744, 84480,
             -113643, -115920, 534612, -370944]
    for i, v in enumerate(known, 1):
        computed = ramanujan_tau(i)
        match = "✓" if computed == v else "✗"
        print(f"    τ_R({i:>2d}) = {v:>10d}  computed={computed}  {match}")

    print()


# ─────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Master Ratio Ω(n) = σψ/(nτφ) & Dedekind Psi Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s --omega 6           Full breakdown for n=6
  %(prog)s --psi-phi 100       Check ψ/φ = n for n ≤ 100
  %(prog)s --integer-omega 1000  Find integer Ω values
  %(prog)s --perfect 1000      Ω at perfect/multiperfect numbers
  %(prog)s --factorial 8       Ω(n!) and σφ vs τ! identity
  %(prog)s --partition 30      Partitions vs σ,τ,φ
  %(prog)s --catalan 15        Catalan vs τφ=σ
  %(prog)s --ramanujan         Ramanujan tau vs σφ
""")

    parser.add_argument("--omega", type=int, metavar="N",
                        help="Compute Ω(N) with full breakdown")
    parser.add_argument("--psi-phi", type=int, metavar="N",
                        help="Check ψ/φ = n for all n ≤ N")
    parser.add_argument("--integer-omega", type=int, metavar="N",
                        help="Find all n ≤ N where Ω(n) is integer")
    parser.add_argument("--perfect", type=int, metavar="N",
                        help="Ω at perfect/multiperfect numbers ≤ N")
    parser.add_argument("--factorial", type=int, metavar="N",
                        help="Ω(n!) for n=1..N, check σφ=τ! identity")
    parser.add_argument("--partition", type=int, metavar="N",
                        help="p(n), q(n), p_even(n) vs σ,τ,φ for n=1..N")
    parser.add_argument("--catalan", type=int, metavar="N",
                        help="Catalan C_n vs τφ=σ for n=0..N")
    parser.add_argument("--ramanujan", action="store_true",
                        help="Ramanujan τ_R(1..12) vs σφ")

    args = parser.parse_args()

    # If no mode selected, show help
    if not any([args.omega, args.psi_phi, args.integer_omega,
                args.perfect, args.factorial, args.partition,
                args.catalan, args.ramanujan]):
        parser.print_help()
        sys.exit(0)

    if args.omega:
        mode_omega(args.omega)
    if args.psi_phi:
        mode_psi_phi(args.psi_phi)
    if args.integer_omega:
        mode_integer_omega(args.integer_omega)
    if args.perfect:
        mode_perfect(args.perfect)
    if args.factorial:
        mode_factorial(args.factorial)
    if args.partition:
        mode_partition(args.partition)
    if args.catalan:
        mode_catalan(args.catalan)
    if args.ramanujan:
        mode_ramanujan()


if __name__ == "__main__":
    main()
