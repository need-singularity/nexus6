#!/usr/bin/env python3
"""R(n)=sigma*phi/(n*tau) congruence-class filter and distribution analyzer.

Restricts R(n) computation to specific number-theoretic subsets
and analyzes the spectral gap structure within each subset.

Usage:
  python3 congruence_filter.py --filter 6 0 1000        # n=0 mod 6, n<=1000
  python3 congruence_filter.py --all-classes 6 1000      # all residue classes mod 6
  python3 congruence_filter.py --prime-form "2^a*3^b" 1000  # 6-smooth
  python3 congruence_filter.py --smooth 5 1000           # 5-smooth numbers
  python3 congruence_filter.py --squarefree 1000         # squarefree n
  python3 congruence_filter.py --prime-power 1000        # prime powers p^a
  python3 congruence_filter.py --perfect-power 10000     # perfect powers m^k, k>=2
  python3 congruence_filter.py --arithmetic 1 6 1000     # AP: 1,7,13,19,...
  python3 congruence_filter.py --coprime-to 6 1000       # gcd(n,6)=1
"""
import argparse
import math
import sys
from fractions import Fraction
from collections import defaultdict

# ── Arithmetic primitives ─────────────────────────────────────────

def factorize(n):
    """Return dict {p: e} of prime factorization."""
    if n < 2:
        return {}
    f = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            f[d] = f.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        f[n] = f.get(n, 0) + 1
    return f


def sigma(n):
    """Sum of divisors."""
    s = 0
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            s += i + (n // i if i * i != n else 0)
    return s


def tau(n):
    """Number of divisors."""
    t = 0
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            t += 1 + (1 if i * i != n else 0)
    return t


def phi(n):
    """Euler totient."""
    r = n
    t = n
    p = 2
    while p * p <= t:
        if t % p == 0:
            while t % p == 0:
                t //= p
            r -= r // p
        p += 1
    if t > 1:
        r -= r // t
    return r


def R(n):
    """R(n) = sigma(n)*phi(n) / (n*tau(n)) as exact Fraction."""
    return Fraction(sigma(n) * phi(n), n * tau(n))


def is_smooth(n, k):
    """True if n is k-smooth (all prime factors <= k)."""
    if n < 2:
        return True
    f = factorize(n)
    return all(p <= k for p in f)


def is_squarefree(n):
    """True if n has no squared prime factor."""
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % (d * d) == 0:
            return False
        d += 1
    return True


def is_prime_power(n):
    """True if n = p^a for prime p, a >= 1. Returns (p, a) or None."""
    if n < 2:
        return None
    f = factorize(n)
    if len(f) == 1:
        p, a = next(iter(f.items()))
        return (p, a)
    return None


def is_perfect_power(n):
    """True if n = m^k for some m >= 2, k >= 2."""
    if n < 4:
        return False
    for k in range(2, n.bit_length() + 1):
        m = round(n ** (1.0 / k))
        for candidate in (m - 1, m, m + 1):
            if candidate >= 2 and candidate ** k == n:
                return True
    return False


def sieve_primes(limit):
    """Simple sieve of Eratosthenes up to limit."""
    if limit < 2:
        return []
    is_p = [True] * (limit + 1)
    is_p[0] = is_p[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if is_p[i]:
            for j in range(i * i, limit + 1, i):
                is_p[j] = False
    return [i for i in range(2, limit + 1) if is_p[i]]


def generate_smooth(k, N):
    """Generate all k-smooth numbers <= N in sorted order."""
    primes = sieve_primes(k)
    if not primes:
        return [1] if N >= 1 else []
    result = set()

    def _gen(idx, cur):
        if cur > N:
            return
        result.add(cur)
        for i in range(idx, len(primes)):
            nxt = cur * primes[i]
            if nxt > N:
                break
            _gen(i, nxt)

    _gen(0, 1)
    return sorted(result)


# ── Analysis engine ───────────────────────────────────────────────

def analyze_r_values(label, ns):
    """Given a label and sorted list of n values (>=2), compute and display R analysis."""
    ns = [n for n in ns if n >= 2]
    if not ns:
        print(f"\n=== {label} ===")
        print("  No valid n values (need n >= 2).")
        return

    r_values = []
    r_to_n = {}
    for n in ns:
        rv = R(n)
        r_values.append((n, rv))
        if rv not in r_to_n:
            r_to_n[rv] = n

    distinct = sorted(r_to_n.keys())
    floats = [float(rv) for _, rv in r_values]

    # Interval buckets
    max_bucket = max(1, int(max(floats)) + 1)
    buckets = defaultdict(int)
    for f in floats:
        buckets[int(f)] += 1

    # Spectral gap check: [3/4, 1) and [1, 7/6)
    gap_low = Fraction(3, 4)
    gap_high = Fraction(7, 6)
    in_gap_34_1 = [rv for rv in distinct if gap_low <= rv < 1]
    in_gap_1_76 = [rv for rv in distinct if 1 < rv < gap_high]
    # R=1 exactly
    r_eq_1 = [n for n, rv in r_values if rv == 1]

    # Print
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  n count:          {len(ns)}")
    print(f"  distinct R:       {len(distinct)}")
    if distinct:
        print(f"  min R:            {distinct[0]} = {float(distinct[0]):.6f}  (n={r_to_n[distinct[0]]})")
        print(f"  max R:            {distinct[-1]} = {float(distinct[-1]):.6f}  (n={r_to_n[distinct[-1]]})")
        mean = Fraction(sum(rv for _, rv in r_values), len(r_values))
        print(f"  mean R:           {float(mean):.6f}")
    print()

    # Distribution by unit intervals
    print("  Distribution by interval:")
    for b in range(max_bucket + 1):
        c = buckets.get(b, 0)
        if c > 0:
            bar = '#' * min(c, 60)
            extra = f" +{c-60}" if c > 60 else ""
            print(f"    [{b},{b+1})  {c:6d}  {bar}{extra}")
    print()

    # Spectral gap analysis
    print("  Spectral gap analysis:")
    print(f"    R in [3/4, 1):   {len(in_gap_34_1)} distinct values", end="")
    if in_gap_34_1:
        print(f"  (examples: {', '.join(str(v) for v in in_gap_34_1[:5])})")
    else:
        print("  -> GAP PRESERVED")

    print(f"    R in (1, 7/6):   {len(in_gap_1_76)} distinct values", end="")
    if in_gap_1_76:
        print(f"  (examples: {', '.join(str(v) for v in in_gap_1_76[:5])})")
    else:
        print("  -> GAP PRESERVED")

    print(f"    R = 1 exactly:   {len(r_eq_1)} values", end="")
    if r_eq_1:
        print(f"  (n = {r_eq_1[:10]}{'...' if len(r_eq_1)>10 else ''})")
    else:
        print()
    print()

    # ASCII histogram of R values (fine-grained, bin width 1/12)
    bin_width = Fraction(1, 12)
    hist = defaultdict(int)
    for _, rv in r_values:
        b = int(rv / bin_width)
        hist[b] += 1

    if hist:
        max_bin = max(hist.keys())
        min_bin = min(hist.keys())
        max_count = max(hist.values())
        scale = 50.0 / max_count if max_count > 0 else 1

        print("  Histogram (bin width = 1/12):")
        for b in range(min_bin, max_bin + 1):
            lo = float(b * bin_width)
            c = hist.get(b, 0)
            bar_len = int(c * scale + 0.5)
            bar = '#' * bar_len
            if c > 0:
                print(f"    {lo:6.3f} | {bar} {c}")
        print()

    # Top 10 most common R values
    r_counts = defaultdict(int)
    for _, rv in r_values:
        r_counts[rv] += 1
    top = sorted(r_counts.items(), key=lambda x: -x[1])[:10]
    print("  Top 10 most common R values:")
    for rv, cnt in top:
        print(f"    R = {str(rv):>12}  ({float(rv):.6f})  count = {cnt}")
    print()

    # Smallest 10 distinct R
    print("  Smallest 10 distinct R:")
    for rv in distinct[:10]:
        print(f"    R = {str(rv):>12}  ({float(rv):.6f})  first n = {r_to_n[rv]}")
    print()


# ── Number generators ─────────────────────────────────────────────

def gen_congruence(mod, res, N):
    start = res if res >= 2 else res + mod * math.ceil((2 - res) / mod)
    if start < 2:
        start += mod
    return list(range(start, N + 1, mod))


def gen_squarefree(N):
    return [n for n in range(2, N + 1) if is_squarefree(n)]


def gen_prime_powers(N):
    return [n for n in range(2, N + 1) if is_prime_power(n) is not None]


def gen_perfect_powers(N):
    return [n for n in range(4, N + 1) if is_perfect_power(n)]


def gen_arithmetic(a, d, N):
    start = a if a >= 2 else a + d * math.ceil((2 - a) / d)
    if start < 2:
        start += d
    return list(range(start, N + 1, d))


def gen_coprime_to(m, N):
    return [n for n in range(2, N + 1) if math.gcd(n, m) == 1]


# ── Main ──────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description='R(n) congruence-class filter and distribution analyzer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    p.add_argument('--filter', nargs=3, metavar=('MOD', 'RES', 'N'),
                   type=int, help='R(n) for n = RES mod MOD, n <= N')
    p.add_argument('--all-classes', nargs=2, metavar=('MOD', 'N'),
                   type=int, help='R distribution for each residue class mod MOD')
    p.add_argument('--prime-form', nargs=2, metavar=('FORM', 'N'),
                   help='R for numbers of given form, e.g. "2^a*3^b" N')
    p.add_argument('--smooth', nargs=2, metavar=('K', 'N'),
                   type=int, help='R for K-smooth numbers <= N')
    p.add_argument('--squarefree', type=int, metavar='N',
                   help='R for squarefree n <= N')
    p.add_argument('--prime-power', type=int, metavar='N',
                   help='R for prime powers p^a <= N')
    p.add_argument('--perfect-power', type=int, metavar='N',
                   help='R for perfect powers m^k (k>=2) <= N')
    p.add_argument('--arithmetic', nargs=3, metavar=('A', 'D', 'N'),
                   type=int, help='R for arithmetic progression a, a+d, a+2d, ... <= N')
    p.add_argument('--coprime-to', nargs=2, metavar=('M', 'N'),
                   type=int, help='R for n coprime to M, n <= N')

    args = p.parse_args()

    if args.filter:
        mod, res, N = args.filter
        ns = gen_congruence(mod, res, N)
        analyze_r_values(f"n = {res} mod {mod}, n <= {N}", ns)

    elif args.all_classes:
        mod, N = args.all_classes
        print(f"All residue classes mod {mod}, n <= {N}")
        print(f"{'='*60}")
        for res in range(mod):
            ns = gen_congruence(mod, res, N)
            if ns:
                analyze_r_values(f"n = {res} mod {mod}", ns)
        # Summary comparison
        print(f"\n{'='*60}")
        print(f"  SUMMARY: spectral gap preservation by class mod {mod}")
        print(f"{'='*60}")
        print(f"  {'class':>8}  {'count':>6}  {'distinct':>8}  {'gap [3/4,1)':>12}  {'gap (1,7/6)':>12}")
        gap_low = Fraction(3, 4)
        gap_high = Fraction(7, 6)
        for res in range(mod):
            ns = gen_congruence(mod, res, N)
            ns = [n for n in ns if n >= 2]
            if not ns:
                continue
            rv_set = set()
            for n in ns:
                rv_set.add(R(n))
            in_34 = sum(1 for rv in rv_set if gap_low <= rv < 1)
            in_76 = sum(1 for rv in rv_set if 1 < rv < gap_high)
            print(f"  {res:>8}  {len(ns):>6}  {len(rv_set):>8}  {in_34:>12}  {in_76:>12}")

    elif args.prime_form:
        form_str, N_str = args.prime_form
        N = int(N_str)
        # Parse form like "2^a*3^b" -> extract base primes
        # Support: "2^a*3^b", "2^a*3^b*5^c", etc.
        import re
        bases = re.findall(r'(\d+)\^', form_str)
        if not bases:
            print(f"Error: cannot parse form '{form_str}'. Use format like '2^a*3^b'.")
            sys.exit(1)
        k = max(int(b) for b in bases)
        # Generate k-smooth and filter to only use the specified primes
        allowed = set(int(b) for b in bases)
        ns = []
        for n in generate_smooth(k, N):
            if n < 2:
                continue
            f = factorize(n)
            if all(p in allowed for p in f):
                ns.append(n)
        analyze_r_values(f"n of form {form_str}, n <= {N}", ns)

    elif args.smooth:
        k, N = args.smooth
        ns = [n for n in generate_smooth(k, N) if n >= 2]
        analyze_r_values(f"{k}-smooth numbers, n <= {N}", ns)

    elif args.squarefree:
        N = args.squarefree
        ns = gen_squarefree(N)
        analyze_r_values(f"squarefree n <= {N}", ns)

    elif args.prime_power:
        N = args.prime_power
        ns = gen_prime_powers(N)
        analyze_r_values(f"prime powers p^a <= {N}", ns)

    elif args.perfect_power:
        N = args.perfect_power
        ns = gen_perfect_powers(N)
        analyze_r_values(f"perfect powers m^k (k>=2) <= {N}", ns)

    elif args.arithmetic:
        a, d, N = args.arithmetic
        ns = gen_arithmetic(a, d, N)
        analyze_r_values(f"AP: a={a}, d={d}, n <= {N}", ns)

    elif args.coprime_to:
        m, N = args.coprime_to
        ns = gen_coprime_to(m, N)
        analyze_r_values(f"n coprime to {m}, n <= {N}", ns)

    else:
        p.print_help()


if __name__ == '__main__':
    main()
