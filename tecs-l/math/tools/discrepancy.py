#!/usr/bin/env python3
"""D(n) = sigma(n)*phi(n) - n*tau(n) discrepancy function calculator

D(n) measures how far sigma*phi deviates from n*tau.
Equivalently: D(n) = n*tau(n)*(R(n)-1) where R=sigma*phi/(n*tau).

Key properties:
  D(1)=0, D(6)=0  (only zeros for n>=1)
  D(2)=-1          (only negative value)
  Im(D) has gap [3,13] -- no n maps to 3..13

Usage:
  python3 discrepancy.py --value 6
  python3 discrepancy.py --range 100
  python3 discrepancy.py --zeros 10000
  python3 discrepancy.py --negative 10000
  python3 discrepancy.py --gaps 10000
  python3 discrepancy.py --preimage 0 --N 10000
  python3 discrepancy.py --prime 10000
  python3 discrepancy.py --divisible 10000
  python3 discrepancy.py --spectrum 10000
"""
import argparse, math, sys
from fractions import Fraction
from collections import defaultdict

# ── arithmetic functions ──

def sigma(n):
    """Sum of divisors of n."""
    s = 0
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            s += i + (n // i if i * i != n else 0)
    return s

def tau(n):
    """Number of divisors of n."""
    t = 0
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            t += 1 + (1 if i * i != n else 0)
    return t

def phi(n):
    """Euler's totient function."""
    r = n; t = n; p = 2
    while p * p <= t:
        if t % p == 0:
            while t % p == 0:
                t //= p
            r -= r // p
        p += 1
    if t > 1:
        r -= r // t
    return r

def is_prime(n):
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def D(n):
    """Discrepancy: D(n) = sigma(n)*phi(n) - n*tau(n)."""
    return sigma(n) * phi(n) - n * tau(n)

def R_frac(n):
    """R(n) = sigma(n)*phi(n) / (n*tau(n)) as exact fraction."""
    return Fraction(sigma(n) * phi(n), n * tau(n))

# ── precompute helper ──

def compute_table(N):
    """Precompute sigma, tau, phi, D, R for n=1..N."""
    rows = []
    for n in range(1, N + 1):
        s, t, p = sigma(n), tau(n), phi(n)
        d = s * p - n * t
        r = Fraction(s * p, n * t)
        rows.append((n, s, t, p, d, r))
    return rows

# ── output helpers ──

def bar(val, scale, ch='#', maxw=40):
    """ASCII bar of given value."""
    if scale == 0:
        return ''
    w = int(abs(val) / scale * maxw)
    w = min(w, maxw)
    if val < 0:
        return '-' * w
    return ch * w

def print_header():
    print(f"{'n':>6} {'sig':>6} {'tau':>4} {'phi':>6} {'D(n)':>10} {'R':>12}  viz")
    print('-' * 72)

def print_row(n, s, t, p, d, r, scale):
    r_str = f"{float(r):.4f}" if r.denominator > 1 else str(r)
    prefix = ' ' if d >= 0 else ''
    viz = bar(d, scale)
    if d < 0:
        viz = '|' + viz
    else:
        viz = '|' + viz
    print(f"{n:>6} {s:>6} {t:>4} {p:>6} {d:>10} {r_str:>12}  {viz}")

# ── modes ──

def mode_value(n):
    s, t, p = sigma(n), tau(n), phi(n)
    d = s * p - n * t
    r = Fraction(s * p, n * t)
    print(f"n = {n}")
    print(f"  sigma({n}) = {s}")
    print(f"  tau({n})   = {t}")
    print(f"  phi({n})   = {p}")
    print(f"  sigma*phi  = {s}*{p} = {s*p}")
    print(f"  n*tau      = {n}*{t} = {n*t}")
    print(f"  D({n})     = {s*p} - {n*t} = {d}")
    print(f"  R({n})     = {r} = {float(r):.8f}")
    print(f"  R - 1      = {r - 1} = {float(r-1):.8f}")
    if d == 0:
        print(f"  ** D({n}) = 0: sigma*phi = n*tau exactly (R=1)")
    elif d < 0:
        print(f"  ** D({n}) < 0: sigma*phi < n*tau (R<1)")
    # factored form
    print(f"\n  D({n}) = n*tau*(R-1) = {n}*{t}*({r}-1) = {n*t}*{r-1} = {d}")


def mode_range(N):
    rows = compute_table(N)
    dvals = [r[4] for r in rows]
    dmin, dmax = min(dvals), max(dvals)
    scale = max(abs(dmin), abs(dmax), 1)

    print(f"D(n) = sigma(n)*phi(n) - n*tau(n) for n = 1..{N}\n")
    print_header()
    for n, s, t, p, d, r in rows:
        print_row(n, s, t, p, d, r, scale)

    # statistics
    print(f"\n{'='*72}")
    print(f"Statistics for n=1..{N}:")
    print(f"  min D = {dmin}  at n = {[r[0] for r in rows if r[4]==dmin]}")
    print(f"  max D = {dmax}  at n = {[r[0] for r in rows if r[4]==dmax]}")
    mean_d = sum(dvals) / len(dvals)
    print(f"  mean D = {mean_d:.2f}")
    zeros = [r[0] for r in rows if r[4] == 0]
    negs = [r[0] for r in rows if r[4] < 0]
    print(f"  zeros: {zeros}")
    print(f"  negatives: {negs}")

    # distribution histogram
    print(f"\nD(n) distribution (histogram):")
    buckets = defaultdict(int)
    bw = max(1, (dmax - dmin) // 30)
    for d in dvals:
        buckets[(d // bw) * bw] += 1
    for k in sorted(buckets):
        cnt = buckets[k]
        label = f"[{k:>8},{k+bw:>8})"
        print(f"  {label} {cnt:>5} {'#' * min(cnt, 60)}")


def mode_zeros(N):
    print(f"Searching D(n) = 0 for n = 1..{N}\n")
    zeros = []
    for n in range(1, N + 1):
        if D(n) == 0:
            s, t, p = sigma(n), tau(n), phi(n)
            r = Fraction(s * p, n * t)
            zeros.append((n, s, t, p, r))
    print(f"Found {len(zeros)} zeros:\n")
    print(f"{'n':>8} {'sigma':>8} {'tau':>6} {'phi':>8} {'R':>10}  note")
    print('-' * 60)
    for n, s, t, p, r in zeros:
        note = ''
        if n == 1:
            note = 'trivial (all functions = 1)'
        elif n == 6:
            note = 'perfect number! sigma=2n, phi=2, tau=4'
        elif sigma(n) == 2 * n:
            note = 'perfect number'
        print(f"{n:>8} {s:>8} {t:>6} {p:>8} {str(r):>10}  {note}")
    if len(zeros) == 2 and set(z[0] for z in zeros) == {1, 6}:
        print(f"\nConfirmed: D(n)=0 iff n in {{1, 6}} for n <= {N}")
        print("  n=1: trivial (1*1 = 1*1)")
        print("  n=6: unique perfect number with sigma*phi = n*tau")


def mode_negative(N):
    print(f"Searching D(n) < 0 for n = 1..{N}\n")
    negs = []
    for n in range(1, N + 1):
        d = D(n)
        if d < 0:
            s, t, p = sigma(n), tau(n), phi(n)
            r = Fraction(s * p, n * t)
            negs.append((n, s, t, p, d, r))
    print(f"Found {len(negs)} negative values:\n")
    print(f"{'n':>8} {'sigma':>8} {'tau':>6} {'phi':>8} {'D(n)':>10} {'R':>10}")
    print('-' * 60)
    for n, s, t, p, d, r in negs:
        print(f"{n:>8} {s:>8} {t:>6} {p:>8} {d:>10} {str(r):>10}")
    if len(negs) == 1 and negs[0][0] == 2:
        print(f"\nConfirmed: D(n)<0 iff n=2 for n <= {N}")
        print("  D(2) = sigma(2)*phi(2) - 2*tau(2) = 3*1 - 2*2 = -1")
        print("  R(2) = 3/4 < 1")


def mode_gaps(N):
    print(f"Analyzing Im(D) for n = 1..{N}\n")
    dset = set()
    for n in range(1, N + 1):
        dset.add(D(n))

    dmin, dmax = min(dset), max(dset)
    print(f"Range of D: [{dmin}, {dmax}]")
    print(f"Distinct values: {len(dset)}")

    # find gaps in non-negative part
    pos_vals = sorted(v for v in dset if v >= 0)
    print(f"\nGaps in Im(D) (non-negative):")
    gaps = []
    for i in range(len(pos_vals) - 1):
        a, b = pos_vals[i], pos_vals[i + 1]
        if b - a > 1:
            gaps.append((a + 1, b - 1))
    if not gaps:
        print("  No gaps found.")
    else:
        print(f"  Found {len(gaps)} gaps:\n")
        print(f"  {'gap':>20} {'width':>8}")
        print(f"  {'-'*30}")
        for lo, hi in gaps:
            print(f"  [{lo:>8}, {hi:>8}] {hi-lo+1:>8}")

    # show first ~30 achieved values
    first_vals = pos_vals[:40]
    print(f"\nFirst achieved non-negative D values:")
    print(f"  {first_vals}")

    # density near 0
    print(f"\nDensity near origin (values 0..100):")
    near = sorted(v for v in dset if 0 <= v <= 100)
    miss = sorted(set(range(0, 101)) - set(near))
    print(f"  Achieved: {len(near)}/101")
    print(f"  Missing:  {miss}")


def mode_preimage(K, N):
    print(f"Finding all n <= {N} where D(n) = {K}\n")
    hits = []
    for n in range(1, N + 1):
        if D(n) == K:
            s, t, p = sigma(n), tau(n), phi(n)
            hits.append((n, s, t, p))
    print(f"Found {len(hits)} solutions:\n")
    if hits:
        print(f"{'n':>8} {'sigma':>8} {'tau':>6} {'phi':>8} {'sig*phi':>10} {'n*tau':>10}")
        print('-' * 60)
        for n, s, t, p in hits:
            print(f"{n:>8} {s:>8} {t:>6} {p:>8} {s*p:>10} {n*t:>10}")
    else:
        print(f"  No n <= {N} satisfies D(n) = {K}")
        print(f"  Value {K} may lie in a gap of Im(D)")


def mode_prime(N):
    print(f"Finding n <= {N} where D(n) is prime\n")
    hits = []
    for n in range(1, N + 1):
        d = D(n)
        if d > 1 and is_prime(d):
            hits.append((n, d))
    print(f"Found {len(hits)} values:\n")
    print(f"{'n':>8} {'D(n)':>12} {'D(n) prime':>12}")
    print('-' * 40)
    for n, d in hits[:100]:
        print(f"{n:>8} {d:>12} {'yes':>12}")
    if len(hits) > 100:
        print(f"  ... and {len(hits)-100} more")

    # prime density
    if hits:
        print(f"\nPrime D(n) density: {len(hits)}/{N} = {len(hits)/N:.4f}")
        # distribution of small primes
        pcounts = defaultdict(int)
        for _, d in hits:
            if d <= 100:
                pcounts[d] += 1
        if pcounts:
            print(f"\nSmall prime D values (D <= 100):")
            print(f"  {'prime':>8} {'count':>8}")
            print(f"  {'-'*20}")
            for p in sorted(pcounts):
                print(f"  {p:>8} {pcounts[p]:>8}")


def mode_divisible(N):
    print(f"Finding n <= {N} where n | D(n) (equivalently n | sigma*phi)\n")
    hits = []
    for n in range(1, N + 1):
        d = D(n)
        if n > 0 and d % n == 0:
            s, t, p = sigma(n), tau(n), phi(n)
            hits.append((n, s, t, p, d, d // n))
    print(f"Found {len(hits)} values:\n")
    print(f"{'n':>8} {'sigma':>8} {'tau':>6} {'phi':>8} {'D(n)':>10} {'D/n':>8}")
    print('-' * 56)
    for n, s, t, p, d, q in hits[:100]:
        print(f"{n:>8} {s:>8} {t:>6} {p:>8} {d:>10} {q:>8}")
    if len(hits) > 100:
        print(f"  ... and {len(hits)-100} more")
    print(f"\nDensity: {len(hits)}/{N} = {len(hits)/N:.4f}")

    # check: n|D(n) iff n|sigma*phi
    print(f"\nVerifying n|D(n) iff n|sigma(n)*phi(n):")
    mismatch = 0
    for n in range(1, min(N, 1000) + 1):
        s, p = sigma(n), phi(n)
        d = D(n)
        if (d % n == 0) != (s * p % n == 0):
            mismatch += 1
    if mismatch == 0:
        print(f"  Confirmed for n=1..{min(N,1000)}: n|D(n) iff n|(sigma*phi)")
    else:
        print(f"  MISMATCH found: {mismatch} cases")


def mode_spectrum(N):
    print(f"D-spectrum analysis for n = 1..{N}\n")
    dvals = []
    for n in range(1, N + 1):
        dvals.append(D(n))

    dmin, dmax = min(dvals), max(dvals)
    dset = sorted(set(dvals))
    print(f"Range: [{dmin}, {dmax}]")
    print(f"Distinct values: {len(dset)}")
    print(f"Density |Im(D) cap [0,max]| / max = {len([v for v in dset if v>=0])}/{dmax} = {len([v for v in dset if v>=0])/max(dmax,1):.6f}")

    # growth of D
    print(f"\nD(n) growth sampling:")
    print(f"  {'n':>8} {'D(n)':>12} {'D/n':>10} {'D/n^2':>12} {'D/nlogn':>12}")
    print(f"  {'-'*60}")
    samples = [10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000]
    for s in samples:
        if s > N:
            break
        d = dvals[s - 1]
        dn = d / s if s > 0 else 0
        dn2 = d / (s * s) if s > 0 else 0
        dnln = d / (s * math.log(s)) if s > 1 else 0
        print(f"  {s:>8} {d:>12} {dn:>10.4f} {dn2:>12.8f} {dnln:>12.6f}")

    # cumulative distinct count (for box-counting dimension estimate)
    print(f"\nCumulative distinct D values (box-counting dimension):")
    print(f"  {'N':>8} {'|Im_N|':>8} {'log|Im|':>10} {'logN':>10} {'dim~':>8}")
    print(f"  {'-'*50}")
    seen = set()
    checkpoints = [10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000]
    for i, d in enumerate(dvals):
        n = i + 1
        seen.add(d)
        if n in checkpoints:
            logim = math.log(len(seen)) if len(seen) > 1 else 0
            logn = math.log(n)
            dim = logim / logn if logn > 0 else 0
            print(f"  {n:>8} {len(seen):>8} {logim:>10.4f} {logn:>10.4f} {dim:>8.4f}")

    # histogram of D values by magnitude
    print(f"\nD(n) magnitude distribution:")
    ranges = [(0, 0), (1, 10), (11, 100), (101, 1000), (1001, 10000),
              (10001, 100000), (100001, 1000000), (1000001, 10**9)]
    print(f"  {'range':>24} {'count':>8} {'frac':>8}  bar")
    print(f"  {'-'*60}")
    for lo, hi in ranges:
        if lo > dmax:
            break
        cnt = sum(1 for d in dvals if lo <= abs(d) <= hi)
        frac = cnt / len(dvals) if dvals else 0
        label = f"[{lo}, {hi}]"
        print(f"  {label:>24} {cnt:>8} {frac:>8.4f}  {'#' * min(int(frac*50), 50)}")

    # record density of small values
    print(f"\nSmall value density (D=0..50):")
    print(f"  {'D':>6} {'count':>8}  bar")
    print(f"  {'-'*40}")
    for target in range(0, 51):
        cnt = sum(1 for d in dvals if d == target)
        if cnt > 0:
            print(f"  {target:>6} {cnt:>8}  {'#' * min(cnt, 40)}")


def main():
    p = argparse.ArgumentParser(
        description='D(n) = sigma(n)*phi(n) - n*tau(n) discrepancy calculator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 discrepancy.py --value 6          # breakdown for n=6
  python3 discrepancy.py --range 30         # table for n=1..30
  python3 discrepancy.py --zeros 10000      # find D(n)=0
  python3 discrepancy.py --negative 10000   # find D(n)<0
  python3 discrepancy.py --gaps 10000       # gaps in image
  python3 discrepancy.py --preimage 0 -N 10000  # D^{-1}(0)
  python3 discrepancy.py --prime 10000      # D(n) prime
  python3 discrepancy.py --divisible 10000  # n|D(n)
  python3 discrepancy.py --spectrum 10000   # density analysis"""
    )
    p.add_argument('--value', type=int, metavar='N',
                   help='Compute D(N) with full breakdown')
    p.add_argument('--range', type=int, metavar='N',
                   help='D(n) for n=1..N with statistics')
    p.add_argument('--zeros', type=int, metavar='N',
                   help='Find n where D(n)=0 up to N')
    p.add_argument('--negative', type=int, metavar='N',
                   help='Find n where D(n)<0 up to N')
    p.add_argument('--gaps', type=int, metavar='N',
                   help='Find gaps in Im(D) up to N')
    p.add_argument('--preimage', type=int, metavar='K',
                   help='Find all n<=N where D(n)=K')
    p.add_argument('--prime', type=int, metavar='N',
                   help='Find n where D(n) is prime, up to N')
    p.add_argument('--divisible', type=int, metavar='N',
                   help='Find n where n|D(n), up to N')
    p.add_argument('--spectrum', type=int, metavar='N',
                   help='D-spectrum density and dimension, up to N')
    p.add_argument('-N', type=int, default=10000,
                   help='Search range for --preimage (default 10000)')

    args = p.parse_args()

    if args.value is not None:
        mode_value(args.value)
    elif args.range is not None:
        mode_range(args.range)
    elif args.zeros is not None:
        mode_zeros(args.zeros)
    elif args.negative is not None:
        mode_negative(args.negative)
    elif args.gaps is not None:
        mode_gaps(args.gaps)
    elif args.preimage is not None:
        mode_preimage(args.preimage, args.N)
    elif args.prime is not None:
        mode_prime(args.prime)
    elif args.divisible is not None:
        mode_divisible(args.divisible)
    elif args.spectrum is not None:
        mode_spectrum(args.spectrum)
    else:
        p.print_help()

if __name__ == '__main__':
    main()
