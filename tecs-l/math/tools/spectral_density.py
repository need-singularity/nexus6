#!/usr/bin/env python3
"""Spectral density analyzer for R(n)=sigma*phi/(n*tau) and S(n)=sigma*tau/(n*phi).

Analyzes the Cantor-like gap structure of R-spectrum, R-vs-S asymmetry,
density growth, and local prime-power factors.

Usage:
  python3 spectral_density.py --density 5 100000
  python3 spectral_density.py --gaps 5 100000
  python3 spectral_density.py --compare 5 100000
  python3 spectral_density.py --cantor 100000
  python3 spectral_density.py --histogram 5 100000
  python3 spectral_density.py --asymmetry 100000
  python3 spectral_density.py --growth 100000
  python3 spectral_density.py --local-factors 50 10
"""

import argparse
import math
import sys
from fractions import Fraction
from collections import defaultdict

# ---------------------------------------------------------------------------
# Arithmetic functions
# ---------------------------------------------------------------------------

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


def S(n):
    """S(n) = sigma(n)*tau(n) / (n*phi(n)) as exact Fraction."""
    return Fraction(sigma(n) * tau(n), n * phi(n))


# ---------------------------------------------------------------------------
# Collectors
# ---------------------------------------------------------------------------

def collect_R_values(N, bound=None):
    """Return sorted list of distinct R(n) values for n=2..N, optionally < bound."""
    vals = set()
    for n in range(2, N + 1):
        v = R(n)
        if bound is None or v < bound:
            vals.add(v)
    return sorted(vals)


def collect_S_values(N, bound=None):
    """Return sorted list of distinct S(n) values for n=2..N, optionally < bound."""
    vals = set()
    for n in range(2, N + 1):
        v = S(n)
        if bound is None or v < bound:
            vals.add(v)
    return sorted(vals)


def collect_both(N, bound=None):
    """Return (R_set, S_set) of distinct values for n=2..N."""
    rset = set()
    sset = set()
    for n in range(2, N + 1):
        rv = R(n)
        sv = S(n)
        if bound is None or rv < bound:
            rset.add(rv)
        if bound is None or sv < bound:
            sset.add(sv)
    return sorted(rset), sorted(sset)


# ---------------------------------------------------------------------------
# Gap analysis
# ---------------------------------------------------------------------------

def find_gaps(vals, lo, hi):
    """Find gaps in sorted vals within [lo, hi). Returns list of (start, end, width)."""
    gaps = []
    prev = Fraction(lo)
    for v in vals:
        if v <= prev:
            continue
        if v > hi:
            break
        gap_width = v - prev
        if gap_width > 0:
            gaps.append((prev, v, gap_width))
        prev = v
    if prev < hi:
        gaps.append((prev, Fraction(hi), Fraction(hi) - prev))
    return gaps


# ---------------------------------------------------------------------------
# ASCII visualization helpers
# ---------------------------------------------------------------------------

def ascii_histogram(vals, lo, hi, bins=40, width=60):
    """ASCII histogram of value density across [lo, hi)."""
    bin_width = Fraction(hi - lo, bins)
    counts = [0] * bins
    for v in vals:
        if v < lo or v >= hi:
            continue
        idx = int((v - lo) / bin_width)
        if idx >= bins:
            idx = bins - 1
        counts[idx] += 1

    max_count = max(counts) if counts else 1
    lines = []
    lines.append(f"  Histogram of values in [{float(lo):.2f}, {float(hi):.2f})  "
                 f"({len(vals)} distinct values, {bins} bins)")
    lines.append(f"  {'Interval':>14s} | {'Count':>5s} | Bar")
    lines.append(f"  {'-'*14}-+-{'-'*5}-+-{'-'*width}")
    for i in range(bins):
        a = float(lo + i * bin_width)
        b = float(lo + (i + 1) * bin_width)
        c = counts[i]
        bar_len = int(c / max_count * width) if max_count > 0 else 0
        bar = '#' * bar_len
        lines.append(f"  [{a:6.3f},{b:6.3f}) | {c:5d} | {bar}")
    return '\n'.join(lines)


def ascii_spectrum_line(vals, lo, hi, width=80):
    """One-line ASCII visualization: dots for values, spaces for gaps."""
    if not vals:
        return ' ' * width
    interval = Fraction(hi - lo)
    chars = [' '] * width
    for v in vals:
        if v < lo or v >= hi:
            continue
        pos = int(float((v - lo) / interval) * (width - 1))
        pos = max(0, min(width - 1, pos))
        chars[pos] = '.'
    return ''.join(chars)


# ---------------------------------------------------------------------------
# Mode implementations
# ---------------------------------------------------------------------------

def mode_density(bound, N):
    """Count distinct R values < BOUND for n<=N, show density per unit interval."""
    bound_frac = Fraction(bound)
    vals = collect_R_values(N, bound_frac)
    total = len(vals)

    print(f"=== R-Spectrum Density: R < {bound}, n <= {N} ===")
    print(f"  Total distinct R values: {total}")
    print()

    # Per unit interval
    hi = int(math.ceil(float(bound_frac)))
    print(f"  {'Interval':>14s} | {'Count':>6s} | {'Density':>10s} | Spectrum")
    print(f"  {'-'*14}-+-{'-'*6}-+-{'-'*10}-+-{'-'*40}")
    for i in range(hi):
        lo_i = Fraction(i)
        hi_i = Fraction(i + 1)
        in_range = [v for v in vals if lo_i <= v < hi_i]
        count = len(in_range)
        density = count  # per unit interval
        spec = ascii_spectrum_line(in_range, lo_i, hi_i, 40)
        print(f"  [{i:5d},{i+1:5d})    | {count:6d} | {density:10d} | {spec}")

    print()
    overall = total / float(bound_frac) if float(bound_frac) > 0 else 0
    print(f"  Overall density: {total} values / {float(bound_frac):.1f} interval "
          f"= {overall:.2f} values/unit")


def mode_gaps(bound, N):
    """Find all gaps in R spectrum below BOUND."""
    bound_frac = Fraction(bound)
    vals = collect_R_values(N, bound_frac)

    print(f"=== R-Spectrum Gaps: R < {bound}, n <= {N} ===")
    print(f"  Distinct values: {len(vals)}")
    print()

    all_gaps = find_gaps(vals, 0, bound_frac)
    total_gap = sum(g[2] for g in all_gaps)
    total_interval = bound_frac

    print(f"  Total gaps: {len(all_gaps)}")
    print(f"  Gap measure: {float(total_gap):.6f} / {float(total_interval):.1f} "
          f"= {float(total_gap / total_interval) * 100:.2f}%")
    print()

    # Show largest gaps
    all_gaps.sort(key=lambda g: g[2], reverse=True)
    top_n = min(30, len(all_gaps))
    print(f"  Top {top_n} largest gaps:")
    print(f"  {'#':>3s} | {'Start':>12s} | {'End':>12s} | {'Width':>12s} | {'Width(float)':>12s}")
    print(f"  {'-'*3}-+-{'-'*12}-+-{'-'*12}-+-{'-'*12}-+-{'-'*12}")
    for i, (a, b, w) in enumerate(all_gaps[:top_n]):
        a_s = f"{a.numerator}/{a.denominator}" if a.denominator != 1 else str(a.numerator)
        b_s = f"{b.numerator}/{b.denominator}" if b.denominator != 1 else str(b.numerator)
        w_s = f"{w.numerator}/{w.denominator}" if w.denominator != 1 else str(w.numerator)
        print(f"  {i+1:3d} | {a_s:>12s} | {b_s:>12s} | {w_s:>12s} | {float(w):12.6f}")

    # Notable known gaps
    print()
    print("  Known structural gaps check:")
    for name, lo_f, hi_f in [("(3/4, 1)", Fraction(3, 4), Fraction(1)),
                              ("(1, 7/6)", Fraction(1), Fraction(7, 6))]:
        in_gap = [v for v in vals if lo_f < v < hi_f]
        status = "EMPTY" if len(in_gap) == 0 else f"{len(in_gap)} values found"
        print(f"    {name}: {status}")


def mode_compare(bound, N):
    """Side-by-side R vs S density comparison."""
    bound_frac = Fraction(bound)
    rvals, svals = collect_both(N, bound_frac)

    print(f"=== R vs S Density Comparison: values < {bound}, n <= {N} ===")
    print(f"  R distinct: {len(rvals)}")
    print(f"  S distinct: {len(svals)}")
    ratio = len(svals) / len(rvals) if len(rvals) > 0 else float('inf')
    print(f"  Asymmetry ratio S/R: {ratio:.1f}x")
    print()

    hi = int(math.ceil(float(bound_frac)))
    print(f"  {'Interval':>14s} | {'R count':>8s} | {'S count':>8s} | {'S/R':>8s} | R spectrum           | S spectrum")
    print(f"  {'-'*14}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}-+-{'-'*21}-+-{'-'*21}")

    for i in range(hi):
        lo_i = Fraction(i)
        hi_i = Fraction(i + 1)
        r_in = [v for v in rvals if lo_i <= v < hi_i]
        s_in = [v for v in svals if lo_i <= v < hi_i]
        rc = len(r_in)
        sc = len(s_in)
        sr = f"{sc/rc:.1f}" if rc > 0 else "inf"
        r_spec = ascii_spectrum_line(r_in, lo_i, hi_i, 20)
        s_spec = ascii_spectrum_line(s_in, lo_i, hi_i, 20)
        print(f"  [{i:5d},{i+1:5d})    | {rc:8d} | {sc:8d} | {sr:>8s} | {r_spec} | {s_spec}")

    print()
    print("  Summary:")
    print(f"    R: sparse, discrete, Cantor-like ({len(rvals)} values)")
    print(f"    S: dense, near-continuous ({len(svals)} values)")
    print(f"    Asymmetry: S has {ratio:.0f}x more distinct values than R")


def mode_cantor(N):
    """Cantor-like analysis: measure of gaps vs values in [0, 10]."""
    bound = Fraction(10)
    vals = collect_R_values(N, bound)

    print(f"=== Cantor-Like Analysis: R spectrum in [0, 10], n <= {N} ===")
    print(f"  Distinct R values in [0,10]: {len(vals)}")
    print()

    all_gaps = find_gaps(vals, 0, bound)
    total_gap = sum(g[2] for g in all_gaps)
    gap_pct = float(total_gap / bound) * 100

    print(f"  Gap measure:   {float(total_gap):.6f} / 10.0 = {gap_pct:.2f}%")
    print(f"  Value measure: {10.0 - float(total_gap):.6f} / 10.0 = {100 - gap_pct:.2f}%")
    print()

    # Cantor set comparison
    # Cantor set has measure 0 (100% gaps). How close is R-spectrum?
    print(f"  Cantor set comparison:")
    print(f"    Classical Cantor set: 100.00% gaps (measure zero)")
    print(f"    R-spectrum:           {gap_pct:.2f}% gaps")
    print(f"    Interpretation: ", end="")
    if gap_pct > 99:
        print("Very Cantor-like! Almost all of [0,10] is gaps.")
    elif gap_pct > 90:
        print("Strongly Cantor-like. Most of [0,10] is gaps.")
    elif gap_pct > 50:
        print("Moderately sparse. More gap than value.")
    else:
        print("Not very Cantor-like. Relatively dense.")
    print()

    # Gap size distribution
    gap_sizes = [float(g[2]) for g in all_gaps]
    if gap_sizes:
        gap_sizes.sort(reverse=True)
        print(f"  Gap size distribution:")
        print(f"    Largest gap:  {gap_sizes[0]:.6f}")
        print(f"    Median gap:   {gap_sizes[len(gap_sizes)//2]:.6f}")
        print(f"    Smallest gap: {gap_sizes[-1]:.6f}")
        print(f"    Total gaps:   {len(gap_sizes)}")
        print()

        # Histogram of gap sizes (log scale buckets)
        print(f"  Gap size histogram (log10 buckets):")
        log_min = math.floor(math.log10(gap_sizes[-1])) if gap_sizes[-1] > 0 else -6
        log_max = math.ceil(math.log10(gap_sizes[0])) if gap_sizes[0] > 0 else 1
        print(f"  {'Size range':>20s} | {'Count':>5s} | Bar")
        print(f"  {'-'*20}-+-{'-'*5}-+-{'-'*40}")
        max_c = 0
        buckets = []
        for e in range(log_min, log_max + 1):
            lo_e = 10 ** e
            hi_e = 10 ** (e + 1)
            count = sum(1 for g in gap_sizes if lo_e <= g < hi_e)
            buckets.append((e, count))
            max_c = max(max_c, count)
        for e, count in buckets:
            bar_len = int(count / max_c * 40) if max_c > 0 else 0
            print(f"  [10^{e:+d}, 10^{e+1:+d})     | {count:5d} | {'#' * bar_len}")

    # Per-unit breakdown
    print()
    print(f"  Per-unit interval breakdown:")
    print(f"  {'Interval':>10s} | {'Values':>6s} | {'Gaps':>5s} | {'Gap%':>7s} | Spectrum")
    print(f"  {'-'*10}-+-{'-'*6}-+-{'-'*5}-+-{'-'*7}-+-{'-'*50}")
    for i in range(10):
        lo_i = Fraction(i)
        hi_i = Fraction(i + 1)
        in_range = [v for v in vals if lo_i <= v < hi_i]
        vc = len(in_range)
        unit_gaps = find_gaps(in_range, i, i + 1)
        unit_gap_measure = sum(g[2] for g in unit_gaps)
        gpct = float(unit_gap_measure) * 100
        spec = ascii_spectrum_line(in_range, lo_i, hi_i, 50)
        print(f"  [{i:3d},{i+1:3d})    | {vc:6d} | {len(unit_gaps):5d} | {gpct:6.2f}% | {spec}")


def mode_histogram(bound, N):
    """ASCII histogram of R-value distribution."""
    bound_frac = Fraction(bound)
    vals = collect_R_values(N, bound_frac)

    print(f"=== R-Spectrum Histogram: R < {bound}, n <= {N} ===")
    print(f"  Distinct values: {len(vals)}")
    print()
    print(ascii_histogram(vals, Fraction(0), bound_frac, bins=min(50, int(bound * 10)), width=60))

    # Also show a multiplicity histogram: how many n map to each R value
    print()
    print("  Value multiplicity (how many n produce each R value):")
    r_counts = defaultdict(int)
    for n in range(2, N + 1):
        v = R(n)
        if v < bound_frac:
            r_counts[v] += 1

    mults = sorted(r_counts.values(), reverse=True)
    if mults:
        print(f"    Most common R value: {float(max(r_counts, key=r_counts.get)):.6f} "
              f"(appears {mults[0]} times)")
        print(f"    Top 10 by multiplicity:")
        top_items = sorted(r_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        print(f"    {'R value':>14s} | {'Fraction':>14s} | {'Count':>6s}")
        print(f"    {'-'*14}-+-{'-'*14}-+-{'-'*6}")
        for v, c in top_items:
            frac_s = f"{v.numerator}/{v.denominator}" if v.denominator != 1 else str(v.numerator)
            print(f"    {float(v):14.6f} | {frac_s:>14s} | {c:6d}")


def mode_asymmetry(N):
    """Compute R-S asymmetry ratio at various thresholds."""
    print(f"=== R-S Asymmetry Analysis: n <= {N} ===")
    print()

    thresholds = [Fraction(1), Fraction(2), Fraction(3), Fraction(5),
                  Fraction(10), Fraction(20), Fraction(50)]

    # Precompute all R and S values
    all_r = []
    all_s = []
    for n in range(2, N + 1):
        all_r.append(R(n))
        all_s.append(S(n))

    print(f"  {'Threshold':>10s} | {'R distinct':>10s} | {'S distinct':>10s} | "
          f"{'S/R ratio':>10s} | {'R density':>10s} | {'S density':>10s}")
    print(f"  {'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")

    for t in thresholds:
        rset = set(v for v in all_r if v < t)
        sset = set(v for v in all_s if v < t)
        rc = len(rset)
        sc = len(sset)
        ratio = sc / rc if rc > 0 else float('inf')
        rd = rc / float(t) if float(t) > 0 else 0
        sd = sc / float(t) if float(t) > 0 else 0
        ratio_s = f"{ratio:.1f}x" if ratio != float('inf') else "inf"
        print(f"  {float(t):10.0f} | {rc:10d} | {sc:10d} | {ratio_s:>10s} | "
              f"{rd:10.1f} | {sd:10.1f}")

    print()
    print("  Interpretation:")
    print("    R-spectrum is sparse/discrete (few distinct rational values)")
    print("    S-spectrum is dense (many distinct values, near-continuous)")
    print("    The asymmetry grows because R has multiplicative structure")
    print("    that collapses many n to the same value, while S does not.")


def mode_growth(N):
    """How density grows with N. Is R<5=24 truly fixed?"""
    print(f"=== R-Spectrum Growth Analysis: n up to {N} ===")
    print()

    checkpoints = []
    step = max(1, N // 20)
    for k in range(step, N + 1, step):
        checkpoints.append(k)
    if checkpoints[-1] != N:
        checkpoints.append(N)

    bound5 = Fraction(5)
    bound10 = Fraction(10)

    print(f"  {'N':>8s} | {'R<5 distinct':>12s} | {'R<10 distinct':>13s} | "
          f"{'R<5 new?':>8s} | R<5 spectrum")
    print(f"  {'-'*8}-+-{'-'*12}-+-{'-'*13}-+-{'-'*8}-+-{'-'*40}")

    prev_r5 = set()
    r5_set = set()
    r10_set = set()
    cp_idx = 0

    for n in range(2, N + 1):
        rv = R(n)
        if rv < bound5:
            r5_set.add(rv)
        if rv < bound10:
            r10_set.add(rv)

        if cp_idx < len(checkpoints) and n == checkpoints[cp_idx]:
            new = r5_set - prev_r5
            new_str = f"+{len(new)}" if new else "0"
            spec = ascii_spectrum_line(sorted(r5_set), Fraction(0), bound5, 40)
            print(f"  {n:8d} | {len(r5_set):12d} | {len(r10_set):13d} | "
                  f"{new_str:>8s} | {spec}")
            prev_r5 = r5_set.copy()
            cp_idx += 1

    print()
    # Show the actual R<5 values
    r5_sorted = sorted(r5_set)
    print(f"  All {len(r5_sorted)} distinct R values < 5 (n <= {N}):")
    for i, v in enumerate(r5_sorted):
        frac_s = f"{v.numerator}/{v.denominator}" if v.denominator != 1 else str(v.numerator)
        print(f"    {i+1:3d}. {frac_s:>14s} = {float(v):.8f}")

    print()
    if len(r5_sorted) == 24:
        print(f"  Result: R<5 = 24 values, CONFIRMED stable up to N={N}")
    else:
        print(f"  Result: R<5 = {len(r5_sorted)} values (expected 24)")


def mode_local_factors(P_MAX, A_MAX):
    """Enumerate all f(p,a) = R(p^a) for primes p<=P_MAX, a<=A_MAX.

    For prime powers n=p^a:
      sigma(p^a) = (p^(a+1)-1)/(p-1)
      tau(p^a)   = a+1
      phi(p^a)   = p^a - p^(a-1) = p^(a-1)*(p-1)
      R(p^a) = sigma*phi/(n*tau)
    """
    print(f"=== Local Factor Analysis: R(p^a) for p <= {P_MAX}, a <= {A_MAX} ===")
    print()

    # Sieve primes
    is_prime = [True] * (P_MAX + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(P_MAX**0.5) + 1):
        if is_prime[i]:
            for j in range(i * i, P_MAX + 1, i):
                is_prime[j] = False
    primes = [p for p in range(2, P_MAX + 1) if is_prime[p]]

    # Header
    a_cols = list(range(1, A_MAX + 1))
    header = f"  {'p':>4s} |"
    for a in a_cols:
        header += f" {'a='+str(a):>16s} |"
    print(header)
    print(f"  {'-'*4}-+" + ("-" * 17 + "-+") * len(a_cols))

    all_r_values = set()

    for p in primes:
        row = f"  {p:4d} |"
        for a in a_cols:
            n = p ** a
            s = Fraction(pow(p, a + 1) - 1, p - 1)
            t = a + 1
            ph = pow(p, a - 1) * (p - 1)
            rv = Fraction(s * ph, n * t)
            all_r_values.add(rv)
            frac_s = f"{rv.numerator}/{rv.denominator}" if rv.denominator != 1 else str(rv.numerator)
            # Truncate if too long
            if len(frac_s) > 14:
                frac_s = f"{float(rv):.6f}"
            row += f" {frac_s:>16s} |"
        print(row)

    print()
    print(f"  Distinct R(p^a) values: {len(all_r_values)}")
    print()

    # Show sorted unique values
    sorted_vals = sorted(all_r_values)
    print(f"  All distinct R(p^a) values (sorted):")
    for i, v in enumerate(sorted_vals[:50]):  # cap at 50
        frac_s = f"{v.numerator}/{v.denominator}" if v.denominator != 1 else str(v.numerator)
        print(f"    {i+1:3d}. {frac_s:>20s} = {float(v):.8f}")
    if len(sorted_vals) > 50:
        print(f"    ... ({len(sorted_vals) - 50} more)")

    print()
    print("  Note: R(n) for general n is determined by these local factors.")
    print("  For n = p1^a1 * p2^a2 * ..., R(n) is a product of contributions")
    print("  from each prime power, which constrains R to a sparse set of rationals.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Spectral density analyzer for R(n) and S(n)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s --density 5 10000       Count distinct R < 5 for n <= 10000
  %(prog)s --gaps 5 10000          Find gaps in R spectrum below 5
  %(prog)s --compare 5 10000       R vs S side-by-side comparison
  %(prog)s --cantor 10000          Cantor-like analysis in [0, 10]
  %(prog)s --histogram 5 10000     ASCII histogram of R distribution
  %(prog)s --asymmetry 10000       R-S asymmetry at various thresholds
  %(prog)s --growth 100000         Track how R<5 count grows with N
  %(prog)s --local-factors 50 10   R(p^a) for primes p<=50, a<=10
""")

    parser.add_argument('--density', nargs=2, metavar=('BOUND', 'N'),
                        help='Count distinct R values < BOUND for n<=N')
    parser.add_argument('--gaps', nargs=2, metavar=('BOUND', 'N'),
                        help='Find all gaps in R spectrum below BOUND')
    parser.add_argument('--compare', nargs=2, metavar=('BOUND', 'N'),
                        help='Side-by-side R vs S density comparison')
    parser.add_argument('--cantor', type=int, metavar='N',
                        help='Cantor-like analysis in [0, 10] for n<=N')
    parser.add_argument('--histogram', nargs=2, metavar=('BOUND', 'N'),
                        help='ASCII histogram of R-value distribution')
    parser.add_argument('--asymmetry', type=int, metavar='N',
                        help='R-S asymmetry ratio at various thresholds')
    parser.add_argument('--growth', type=int, metavar='N',
                        help='Track how R<5 distinct count grows with N')
    parser.add_argument('--local-factors', nargs=2, metavar=('P_MAX', 'A_MAX'),
                        help='Enumerate R(p^a) for primes p<=P_MAX, a<=A_MAX')

    args = parser.parse_args()

    if args.density:
        mode_density(Fraction(args.density[0]), int(args.density[1]))
    elif args.gaps:
        mode_gaps(Fraction(args.gaps[0]), int(args.gaps[1]))
    elif args.compare:
        mode_compare(Fraction(args.compare[0]), int(args.compare[1]))
    elif args.cantor is not None:
        mode_cantor(args.cantor)
    elif args.histogram:
        mode_histogram(Fraction(args.histogram[0]), int(args.histogram[1]))
    elif args.asymmetry is not None:
        mode_asymmetry(args.asymmetry)
    elif args.growth is not None:
        mode_growth(args.growth)
    elif args.local_factors:
        mode_local_factors(int(args.local_factors[0]), int(args.local_factors[1]))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
