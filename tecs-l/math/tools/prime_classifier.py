#!/usr/bin/env python3
"""Prime classifier & arithmetic function profiler

Usage:
  python3 prime_classifier.py --profile 768
  python3 prime_classifier.py --ml-dim 768
  python3 prime_classifier.py --classify 100
  python3 prime_classifier.py --perfect
  python3 prime_classifier.py --compare 6 28
  python3 prime_classifier.py --batch numbers.txt

All arithmetic uses fractions.Fraction for exact rational results.
Designed for DFS exploration of number-theoretic structure.
"""
import argparse
import math
import sys
from fractions import Fraction
from collections import OrderedDict

# ═══════════════════════════════════════════════════════════════
#  Core arithmetic functions (exact)
# ═══════════════════════════════════════════════════════════════

def factorize(n):
    """Return OrderedDict {prime: exponent} sorted by prime."""
    if n < 2:
        return OrderedDict()
    factors = OrderedDict()
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
    """Sum of divisors sigma_1(n)."""
    if n < 1:
        return 0
    s = 0
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            s += i
            if i * i != n:
                s += n // i
    return s


def sigma_from_factors(factors):
    """sigma(n) from factorization, using product formula."""
    result = 1
    for p, a in factors.items():
        result *= (p**(a + 1) - 1) // (p - 1)
    return result


def tau(n):
    """Number of divisors tau(n)."""
    if n < 1:
        return 0
    t = 0
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            t += 1
            if i * i != n:
                t += 1
    return t


def tau_from_factors(factors):
    """tau(n) from factorization."""
    result = 1
    for a in factors.values():
        result *= (a + 1)
    return result


def phi(n):
    """Euler totient phi(n)."""
    if n < 1:
        return 0
    result = n
    temp = n
    p = 2
    while p * p <= temp:
        if temp % p == 0:
            while temp % p == 0:
                temp //= p
            result -= result // p
        p += 1
    if temp > 1:
        result -= result // temp
    return result


def phi_from_factors(factors):
    """phi(n) from factorization."""
    result = 1
    for p, a in factors.items():
        result *= (p - 1) * p**(a - 1)
    return result


def divisors(n):
    """Return sorted list of all divisors of n."""
    divs = []
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            divs.append(i)
            if i * i != n:
                divs.append(n // i)
    return sorted(divs)


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


# ═══════════════════════════════════════════════════════════════
#  Derived ratios (all exact Fraction)
# ═══════════════════════════════════════════════════════════════

def R(n):
    """R(n) = sigma(n)*phi(n) / (n*tau(n))"""
    return Fraction(sigma(n) * phi(n), n * tau(n))


def S(n):
    """S(n) = sigma(n)*tau(n) / (n*phi(n))"""
    return Fraction(sigma(n) * tau(n), n * phi(n))


def B(n):
    """B(n) = sigma(n)*phi(n) / n^2"""
    return Fraction(sigma(n) * phi(n), n * n)


def RS(n):
    """RS(n) = (sigma(n)/n)^2 = R(n)*S(n)"""
    s = Fraction(sigma(n), n)
    return s * s


def sigma_minus1(n):
    """sigma_{-1}(n) = sigma(n)/n  (sum of reciprocals of divisors)."""
    return Fraction(sigma(n), n)


# ═══════════════════════════════════════════════════════════════
#  B-infinity for prime signatures
# ═══════════════════════════════════════════════════════════════

def B_infinity(factors):
    """Limiting B for n = prod p_i^a_i as a_i -> inf with same primes.
    B_inf = prod_p (1 - 1/p^2) for each distinct prime p dividing n.
    This is the asymptotic B value for the prime signature family.
    """
    result = Fraction(1)
    for p in factors:
        result *= Fraction(p * p - 1, p * p)
    return result


def B_exact_from_factors(factors):
    """Exact B(n) computed from factorization using product formula.
    B(n) = prod_p [(p^(a+1)-1)(p^a - p^(a-1))] / [p^(2a)(p-1)]
         = prod_p [(p^(a+1)-1)(p-1)p^(a-1)] / [p^(2a)(p-1)]
         = prod_p [(p^(a+1)-1)] / [p^(a+1)]
    Actually: sigma(p^a) = (p^(a+1)-1)/(p-1), phi(p^a) = p^a - p^(a-1)
    B(p^a) = sigma(p^a)*phi(p^a)/p^(2a)
           = [(p^(a+1)-1)/(p-1)] * [p^(a-1)(p-1)] / p^(2a)
           = (p^(a+1)-1) * p^(a-1) / p^(2a)
           = (p^(a+1)-1) / p^(a+1)
           = 1 - 1/p^(a+1)
    So B(n) = prod_p (1 - 1/p^(a+1)).
    """
    result = Fraction(1)
    for p, a in factors.items():
        result *= Fraction(p**(a + 1) - 1, p**(a + 1))
    return result


# ═══════════════════════════════════════════════════════════════
#  Formatting helpers
# ═══════════════════════════════════════════════════════════════

def fmt_factorization(factors):
    """Pretty-print factorization: 2^8 x 3"""
    if not factors:
        return "1"
    parts = []
    for p, a in factors.items():
        if a == 1:
            parts.append(str(p))
        else:
            parts.append(f"{p}^{a}")
    return " x ".join(parts)


def fmt_fraction(f, max_decimal=6):
    """Format Fraction as 'p/q = decimal' or just integer."""
    if f.denominator == 1:
        return str(f.numerator)
    dec = float(f)
    return f"{f.numerator}/{f.denominator} = {dec:.{max_decimal}f}"


def fmt_fraction_short(f):
    """Short format for tables."""
    if f.denominator == 1:
        return str(f.numerator)
    return f"{float(f):.6f}"


def prime_signature(factors):
    """Return sorted tuple of exponents (prime signature)."""
    return tuple(sorted(factors.values(), reverse=True))


def signature_label(factors):
    """Human-readable label for the prime signature family."""
    if not factors:
        return "1"
    parts = []
    primes_sorted = sorted(factors.keys())
    for p in primes_sorted:
        a = factors[p]
        if a == 1:
            parts.append(str(p))
        else:
            parts.append(f"{p}^{a}")
    return " x ".join(parts)


# ═══════════════════════════════════════════════════════════════
#  ASCII visualization
# ═══════════════════════════════════════════════════════════════

def ascii_factor_tree(n, factors):
    """ASCII visualization of factor structure."""
    lines = []
    lines.append(f"  {n}")
    divs = divisors(n)

    # Show divisor lattice summary
    lines.append(f"  |")
    lines.append(f"  +-- divisors ({len(divs)}): {', '.join(str(d) for d in divs[:20])}"
                 + ("..." if len(divs) > 20 else ""))

    # Factor tree
    lines.append(f"  |")
    lines.append(f"  +-- prime decomposition:")
    for p, a in factors.items():
        bar = "█" * a + "░" * max(0, 10 - a)
        lines.append(f"  |   p={p:>6d}  a={a:>2d}  {bar}  p^(a+1)={p**(a+1)}")

    # B contribution per prime
    lines.append(f"  |")
    lines.append(f"  +-- B contribution per prime (1 - 1/p^(a+1)):")
    for p, a in factors.items():
        b_p = Fraction(p**(a + 1) - 1, p**(a + 1))
        lines.append(f"  |   p={p:>6d}: B_p = {fmt_fraction(b_p)}")

    return "\n".join(lines)


def ascii_bar(value, width=40, label=""):
    """Simple horizontal ASCII bar."""
    filled = int(value * width)
    filled = max(0, min(width, filled))
    bar = "█" * filled + "░" * (width - filled)
    return f"  {bar} {label}"


def R_class_label(r_val):
    """Classify R value."""
    seven_sixths = Fraction(7, 6)
    if r_val < 1:
        return "R < 1 (sub-unitary)"
    elif r_val == 1:
        return "R = 1 (e.g. perfect number 6)"
    elif r_val < seven_sixths:
        return "1 < R < 7/6"
    elif r_val == seven_sixths:
        return "R = 7/6 (semiprime pq)"
    else:
        return "R > 7/6"


def R_class_short(r_val):
    """Short R class for tables."""
    seven_sixths = Fraction(7, 6)
    if r_val < 1:
        return "R<1"
    elif r_val == 1:
        return "R=1"
    elif r_val < seven_sixths:
        return "1<R<7/6"
    elif r_val == seven_sixths:
        return "R=7/6"
    else:
        return "R>7/6"


# ═══════════════════════════════════════════════════════════════
#  Mode: --profile N
# ═══════════════════════════════════════════════════════════════

def profile(n):
    """Full arithmetic profile of a single number."""
    factors = factorize(n)
    s = sigma(n)
    t = tau(n)
    p = phi(n)
    r = R(n)
    s_val = S(n)
    b = B(n)
    rs = RS(n)
    sm1 = sigma_minus1(n)
    b_inf = B_infinity(factors)
    b_exact = B_exact_from_factors(factors)

    print(f"\n{'='*60}")
    print(f"  PROFILE: n = {n}")
    print(f"{'='*60}")
    print()

    # Factorization
    print(f"  n = {n} = {fmt_factorization(factors)}")
    if is_prime(n):
        print(f"  *** PRIME ***")
    if s == 2 * n:
        print(f"  *** PERFECT NUMBER (sigma = 2n) ***")
    print()

    # Core functions
    print(f"  sigma(n)     = {s}")
    print(f"  tau(n)       = {t}")
    print(f"  phi(n)       = {p}")
    print(f"  sigma_{-1}(n) = sigma/n = {fmt_fraction(sm1)}")
    print()

    # Derived ratios
    print(f"  R(n)  = sigma*phi/(n*tau) = {fmt_fraction(r)}")
    print(f"  S(n)  = sigma*tau/(n*phi) = {fmt_fraction(s_val)}")
    print(f"  B(n)  = sigma*phi/n^2     = {fmt_fraction(b)}")
    print(f"  RS(n) = (sigma/n)^2       = {fmt_fraction(rs)}")
    print()

    # Classification
    print(f"  R-class: {R_class_label(r)}")
    print(f"  B-class: {'B < 1 (deficient-type)' if b < 1 else 'B = 1' if b == 1 else 'B > 1'}")
    print()

    # B analysis
    print(f"  B(n) decomposition: B = prod(1 - 1/p^(a+1))")
    print(f"  B_exact = {fmt_fraction(b_exact)}")
    print(f"  B_inf (a->inf) = prod(1 - 1/p^2) = {fmt_fraction(b_inf)}")
    print()

    # Factor tree
    print(ascii_factor_tree(n, factors))
    print()

    # B bar visualization
    print(f"  B(n) = {float(b):.6f}")
    print(ascii_bar(float(b), 40, f"B = {float(b):.4f}"))
    print(ascii_bar(float(b_inf), 40, f"B_inf = {float(b_inf):.4f}"))
    print()

    # Divisor pairs (head x dim for ML)
    pairs = []
    for d in divisors(n):
        pairs.append((d, n // d))
    print(f"  Divisor pairs ({len(pairs)}):")
    for a, b_val in pairs:
        print(f"    {a:>8d} x {b_val:<8d}")
    print()

    return {
        'n': n, 'factors': factors, 'sigma': s, 'tau': t, 'phi': p,
        'R': r, 'S': s_val, 'B': b, 'RS': rs, 'B_inf': b_inf,
    }


# ═══════════════════════════════════════════════════════════════
#  Mode: --ml-dim N
# ═══════════════════════════════════════════════════════════════

def ml_dim_analysis(n):
    """ML dimension analysis: B(d), tau(d), head x dim pairs."""
    factors = factorize(n)
    b = B(n)
    b_inf = B_infinity(factors)
    t = tau(n)

    # Nearest power of 2
    log2 = math.log2(n)
    lower_pow = 2 ** int(log2)
    upper_pow = 2 ** (int(log2) + 1)
    nearest_2k = lower_pow if abs(n - lower_pow) <= abs(n - upper_pow) else upper_pow

    print(f"\n{'='*60}")
    print(f"  ML DIMENSION ANALYSIS: d = {n}")
    print(f"{'='*60}")
    print()

    print(f"  d = {n} = {fmt_factorization(factors)}")
    print(f"  Nearest 2^k = {nearest_2k} = 2^{int(math.log2(nearest_2k))}")
    print()

    # Core metrics
    print(f"  tau(d)  = {t:>6d}   (number of head x dim splits)")
    print(f"  B(d)    = {fmt_fraction_short(b):>12s}   (arithmetic quality)")
    print(f"  B_inf   = {fmt_fraction_short(b_inf):>12s}   (family limit)")
    print()

    # Compare with nearest 2^k
    n2 = nearest_2k
    factors2 = factorize(n2)
    b2 = B(n2)
    t2 = tau(n2)
    print(f"  Comparison: d={n} vs d={n2}")
    print(f"  {'':>12s} {'d='+str(n):>12s} {'d='+str(n2):>12s} {'delta':>12s}")
    print(f"  {'tau':>12s} {t:>12d} {t2:>12d} {t-t2:>+12d}")
    print(f"  {'B':>12s} {float(b):>12.6f} {float(b2):>12.6f} {float(b-b2):>+12.6f}")
    print()

    # Head x dim pairs table
    pairs = []
    for d in divisors(n):
        pairs.append((d, n // d))

    print(f"  head x dim pairs ({len(pairs)} configurations):")
    print(f"  {'heads':>8s} {'dim':>8s} {'B(heads)':>10s} {'B(dim)':>10s} {'tau(dim)':>8s}")
    print(f"  {'-'*8:>8s} {'-'*8:>8s} {'-'*10:>10s} {'-'*10:>10s} {'-'*8:>8s}")
    for h, d in pairs:
        bh = B(h) if h > 1 else Fraction(1)
        bd = B(d) if d > 1 else Fraction(1)
        td = tau(d) if d > 1 else 1
        print(f"  {h:>8d} {d:>8d} {float(bh):>10.6f} {float(bd):>10.6f} {td:>8d}")
    print()

    # B(d) prime signature analysis
    print(f"  B(d) dependence on prime signature:")
    print(f"  B(n) = prod_p (1 - 1/p^(a+1))")
    print()
    print(f"  {'prime p':>8s} {'exp a':>6s} {'1-1/p^(a+1)':>14s} {'cumulative B':>14s}")
    print(f"  {'-'*8:>8s} {'-'*6:>6s} {'-'*14:>14s} {'-'*14:>14s}")
    cum = Fraction(1)
    for p, a in factors.items():
        contrib = Fraction(p**(a + 1) - 1, p**(a + 1))
        cum *= contrib
        print(f"  {p:>8d} {a:>6d} {float(contrib):>14.8f} {float(cum):>14.8f}")
    print()

    # Which primes push B below 1?
    print(f"  Primes pushing B below 1:")
    print(f"  (B is always < 1 for n > 1; smaller primes reduce B more)")
    cum = Fraction(1)
    for p, a in sorted(factors.items()):
        before = cum
        contrib = Fraction(p**(a + 1) - 1, p**(a + 1))
        cum *= contrib
        deficit = Fraction(1) - contrib
        print(f"    p={p}, a={a}: factor = {float(contrib):.8f}, deficit = {float(deficit):.2e}"
              f"  (B so far: {float(cum):.8f})")
    print()

    # Prime signature family
    sig = prime_signature(factors)
    print(f"  Prime signature: {sig}")
    print(f"  B_inf for this family = {fmt_fraction(b_inf)} = {float(b_inf):.8f}")
    print(f"  B(d) / B_inf = {float(b / b_inf):.8f}  (convergence to limit)")
    print()


# ═══════════════════════════════════════════════════════════════
#  Mode: --classify RANGE
# ═══════════════════════════════════════════════════════════════

def classify_range(N):
    """Classify all n in [2..N] by R-type."""
    seven_sixths = Fraction(7, 6)

    classes = {
        'R<1': [],
        'R=1': [],
        '1<R<7/6': [],
        'R=7/6': [],
        'R>7/6': [],
    }
    counts = {k: 0 for k in classes}

    print(f"\n{'='*60}")
    print(f"  R-CLASSIFICATION: n = 2..{N}")
    print(f"{'='*60}")
    print()

    for n in range(2, N + 1):
        r = R(n)
        cls = R_class_short(r)
        key = cls.replace('=', '=').replace('<', '<').replace('>', '>')
        # Map to dict key
        if r < 1:
            k = 'R<1'
        elif r == 1:
            k = 'R=1'
        elif r < seven_sixths:
            k = '1<R<7/6'
        elif r == seven_sixths:
            k = 'R=7/6'
        else:
            k = 'R>7/6'
        counts[k] += 1
        if len(classes[k]) < 20:  # Store first 20 examples
            classes[k].append(n)

    total = N - 1
    print(f"  {'Class':>12s} {'Count':>8s} {'%':>8s} {'First examples'}")
    print(f"  {'-'*12:>12s} {'-'*8:>8s} {'-'*8:>8s} {'-'*30}")
    for k in ['R<1', 'R=1', '1<R<7/6', 'R=7/6', 'R>7/6']:
        c = counts[k]
        pct = 100.0 * c / total if total > 0 else 0
        examples = ', '.join(str(x) for x in classes[k][:10])
        if len(classes[k]) > 10:
            examples += "..."
        print(f"  {k:>12s} {c:>8d} {pct:>7.2f}% {examples}")
    print(f"  {'TOTAL':>12s} {total:>8d}")
    print()

    # Distribution bar chart
    print(f"  Distribution:")
    max_count = max(counts.values()) if counts.values() else 1
    for k in ['R<1', 'R=1', '1<R<7/6', 'R=7/6', 'R>7/6']:
        c = counts[k]
        bar_len = int(40 * c / max_count) if max_count > 0 else 0
        bar = "█" * bar_len
        print(f"  {k:>12s} |{bar} {c}")
    print()

    # R=1 analysis (should be prime powers)
    if classes['R=1']:
        print(f"  R=1 numbers (prime powers):")
        for n in classes['R=1'][:20]:
            f = factorize(n)
            print(f"    {n:>8d} = {fmt_factorization(f)}")
        if counts['R=1'] > 20:
            print(f"    ... ({counts['R=1']} total)")
    print()


# ═══════════════════════════════════════════════════════════════
#  Mode: --perfect
# ═══════════════════════════════════════════════════════════════

KNOWN_PERFECT = [6, 28, 496, 8128, 33550336]


def analyze_perfect():
    """Analyze all known small perfect numbers."""
    print(f"\n{'='*60}")
    print(f"  PERFECT NUMBER ANALYSIS")
    print(f"{'='*60}")
    print()

    # Table header
    print(f"  {'n':>12s} {'factorization':>20s} {'sigma':>12s} {'tau':>6s} "
          f"{'phi':>12s} {'R':>14s} {'S':>14s} {'B':>14s} {'RS':>14s}")
    print(f"  {'-'*12} {'-'*20} {'-'*12} {'-'*6} {'-'*12} {'-'*14} {'-'*14} {'-'*14} {'-'*14}")

    results = []
    for n in KNOWN_PERFECT:
        factors = factorize(n)
        s = sigma(n)
        t = tau(n)
        p = phi(n)
        r = R(n)
        sv = S(n)
        b = B(n)
        rs = RS(n)

        fact_str = fmt_factorization(factors)
        print(f"  {n:>12d} {fact_str:>20s} {s:>12d} {t:>6d} "
              f"{p:>12d} {fmt_fraction_short(r):>14s} {fmt_fraction_short(sv):>14s} "
              f"{fmt_fraction_short(b):>14s} {fmt_fraction_short(rs):>14s}")
        results.append({
            'n': n, 'factors': factors, 'sigma': s, 'tau': t, 'phi': p,
            'R': r, 'S': sv, 'B': b, 'RS': rs,
        })
    print()

    # Perfect number structure: 2^(p-1) * (2^p - 1)
    print(f"  Structure: n = 2^(p-1) * (2^p - 1) where 2^p - 1 is Mersenne prime")
    print()
    print(f"  {'n':>12s} {'p':>4s} {'2^p-1':>12s} {'sigma_{-1}':>12s} {'B(n)':>14s} {'B_inf':>14s}")
    print(f"  {'-'*12} {'-'*4} {'-'*12} {'-'*12} {'-'*14} {'-'*14}")

    for res in results:
        n = res['n']
        factors = res['factors']
        # Extract Mersenne prime structure
        if 2 in factors:
            exp2 = factors[2]
            mersenne = 2**(exp2 + 1) - 1
            p_val = exp2 + 1
        else:
            p_val = 0
            mersenne = 0

        sm1 = sigma_minus1(n)
        b_inf = B_infinity(factors)
        print(f"  {n:>12d} {p_val:>4d} {mersenne:>12d} "
              f"{fmt_fraction_short(sm1):>12s} "
              f"{fmt_fraction_short(res['B']):>14s} "
              f"{fmt_fraction_short(b_inf):>14s}")
    print()

    # Exact R values for perfect numbers
    print(f"  Exact R values (Fraction):")
    for res in results:
        n = res['n']
        r = res['R']
        print(f"    R({n}) = {r.numerator}/{r.denominator} = {float(r):.10f}")
    print()

    # Key identities for n=6
    print(f"  Key identities for n=6 (the unique perfect number with sigma_{{-1}} = 2):")
    n = 6
    print(f"    sigma(6)   = {sigma(n)} = 2*6")
    print(f"    tau(6)     = {tau(n)}")
    print(f"    phi(6)     = {phi(n)}")
    print(f"    R(6)       = {R(n)} = {float(R(n))}")
    print(f"    S(6)       = {S(n)} = {float(S(n))}")
    print(f"    B(6)       = {B(n)} = {float(B(n))}")
    print(f"    1/2+1/3+1/6 = {Fraction(1,2)+Fraction(1,3)+Fraction(1,6)} (reciprocal divisors)")
    print()


# ═══════════════════════════════════════════════════════════════
#  Mode: --compare N1 N2
# ═══════════════════════════════════════════════════════════════

def compare(n1, n2):
    """Side-by-side comparison of two numbers."""
    data = {}
    for n in [n1, n2]:
        factors = factorize(n)
        data[n] = {
            'factors': factors,
            'sigma': sigma(n),
            'tau': tau(n),
            'phi': phi(n),
            'R': R(n),
            'S': S(n),
            'B': B(n),
            'RS': RS(n),
            'B_inf': B_infinity(factors),
            'sigma_m1': sigma_minus1(n),
            'divisors': divisors(n),
        }

    d1, d2 = data[n1], data[n2]

    print(f"\n{'='*60}")
    print(f"  COMPARISON: {n1} vs {n2}")
    print(f"{'='*60}")
    print()

    print(f"  {'Property':>16s} {'n='+str(n1):>20s} {'n='+str(n2):>20s}")
    print(f"  {'-'*16} {'-'*20} {'-'*20}")
    print(f"  {'factorization':>16s} {fmt_factorization(d1['factors']):>20s} {fmt_factorization(d2['factors']):>20s}")
    print(f"  {'prime?':>16s} {str(is_prime(n1)):>20s} {str(is_prime(n2)):>20s}")
    print(f"  {'perfect?':>16s} {str(d1['sigma']==2*n1):>20s} {str(d2['sigma']==2*n2):>20s}")
    print(f"  {'sigma':>16s} {d1['sigma']:>20d} {d2['sigma']:>20d}")
    print(f"  {'tau':>16s} {d1['tau']:>20d} {d2['tau']:>20d}")
    print(f"  {'phi':>16s} {d1['phi']:>20d} {d2['phi']:>20d}")
    print(f"  {'sigma/n':>16s} {fmt_fraction_short(d1['sigma_m1']):>20s} {fmt_fraction_short(d2['sigma_m1']):>20s}")
    print(f"  {'R':>16s} {fmt_fraction_short(d1['R']):>20s} {fmt_fraction_short(d2['R']):>20s}")
    print(f"  {'S':>16s} {fmt_fraction_short(d1['S']):>20s} {fmt_fraction_short(d2['S']):>20s}")
    print(f"  {'B':>16s} {fmt_fraction_short(d1['B']):>20s} {fmt_fraction_short(d2['B']):>20s}")
    print(f"  {'RS':>16s} {fmt_fraction_short(d1['RS']):>20s} {fmt_fraction_short(d2['RS']):>20s}")
    print(f"  {'B_inf':>16s} {fmt_fraction_short(d1['B_inf']):>20s} {fmt_fraction_short(d2['B_inf']):>20s}")
    print(f"  {'R-class':>16s} {R_class_short(d1['R']):>20s} {R_class_short(d2['R']):>20s}")
    print()

    # Signature comparison
    sig1 = prime_signature(d1['factors'])
    sig2 = prime_signature(d2['factors'])
    print(f"  Prime signatures: {sig1} vs {sig2}")
    same_sig = sig1 == sig2
    print(f"  Same signature: {same_sig}")
    print()

    # Divisor pair comparison
    div1 = d1['divisors']
    div2 = d2['divisors']
    common = sorted(set(div1) & set(div2))
    print(f"  Divisors of {n1} ({len(div1)}): {', '.join(str(d) for d in div1[:15])}"
          + ("..." if len(div1) > 15 else ""))
    print(f"  Divisors of {n2} ({len(div2)}): {', '.join(str(d) for d in div2[:15])}"
          + ("..." if len(div2) > 15 else ""))
    print(f"  Common divisors ({len(common)}): {', '.join(str(d) for d in common[:15])}"
          + ("..." if len(common) > 15 else ""))
    print()


# ═══════════════════════════════════════════════════════════════
#  Mode: --batch FILE
# ═══════════════════════════════════════════════════════════════

def batch_profile(filepath):
    """Read numbers from file, profile each."""
    try:
        with open(filepath, 'r') as f:
            numbers = []
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                try:
                    numbers.append(int(line))
                except ValueError:
                    # Try comma/space separated
                    for tok in line.replace(',', ' ').split():
                        try:
                            numbers.append(int(tok))
                        except ValueError:
                            pass
    except FileNotFoundError:
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    if not numbers:
        print("No valid numbers found in file.", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  BATCH PROFILE: {len(numbers)} numbers from {filepath}")
    print(f"{'='*60}")
    print()

    # Summary table
    print(f"  {'n':>12s} {'factorization':>24s} {'sigma':>10s} {'tau':>6s} "
          f"{'phi':>10s} {'R':>12s} {'B':>12s} {'class':>10s}")
    print(f"  {'-'*12} {'-'*24} {'-'*10} {'-'*6} {'-'*10} {'-'*12} {'-'*12} {'-'*10}")

    for n in numbers:
        if n < 1:
            continue
        factors = factorize(n)
        s = sigma(n)
        t = tau(n)
        p = phi(n)
        r = R(n)
        b = B(n)
        fact_str = fmt_factorization(factors)
        print(f"  {n:>12d} {fact_str:>24s} {s:>10d} {t:>6d} "
              f"{p:>10d} {fmt_fraction_short(r):>12s} {fmt_fraction_short(b):>12s} "
              f"{R_class_short(r):>10s}")
    print()


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(
        description='Prime classifier & arithmetic function profiler',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 prime_classifier.py --profile 768
  python3 prime_classifier.py --ml-dim 768
  python3 prime_classifier.py --classify 100
  python3 prime_classifier.py --perfect
  python3 prime_classifier.py --compare 6 28
  python3 prime_classifier.py --batch numbers.txt

Functions computed:
  sigma(n) = sum of divisors
  tau(n)   = number of divisors
  phi(n)   = Euler totient
  R(n)     = sigma*phi/(n*tau)
  S(n)     = sigma*tau/(n*phi)
  B(n)     = sigma*phi/n^2 = prod(1 - 1/p^(a+1))
  RS(n)    = (sigma/n)^2
""")
    p.add_argument('--profile', type=int, metavar='N',
                   help='Full profile of single number')
    p.add_argument('--ml-dim', type=int, metavar='N',
                   help='ML dimension analysis (B, tau, head x dim)')
    p.add_argument('--classify', type=int, metavar='RANGE',
                   help='Classify all n in [2..RANGE] by R-type')
    p.add_argument('--perfect', action='store_true',
                   help='Analyze known perfect numbers')
    p.add_argument('--compare', type=int, nargs=2, metavar=('N1', 'N2'),
                   help='Side-by-side comparison of two numbers')
    p.add_argument('--batch', type=str, metavar='FILE',
                   help='Read numbers from file, profile each')

    args = p.parse_args()

    if not any([args.profile, args.ml_dim, args.classify, args.perfect,
                args.compare, args.batch]):
        p.print_help()
        sys.exit(0)

    if args.profile:
        profile(args.profile)

    if args.ml_dim:
        ml_dim_analysis(args.ml_dim)

    if args.classify:
        classify_range(args.classify)

    if args.perfect:
        analyze_perfect()

    if args.compare:
        compare(args.compare[0], args.compare[1])

    if args.batch:
        batch_profile(args.batch)


if __name__ == '__main__':
    main()
