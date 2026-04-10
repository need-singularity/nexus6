#!/usr/bin/env python3
"""Perfect number generalization tester.

Tests whether identities discovered for n=6 hold for 28, 496, 8128, ...
Computes full arithmetic profiles, finds multiperfect/amicable/near-perfect numbers.

Usage:
  python3 perfect_chain.py --all-perfect 5
  python3 perfect_chain.py --verify-theorem sigma_phi
  python3 perfect_chain.py --generalize 6
  python3 perfect_chain.py --test-identity "sigma(n)*phi(n)==n*tau(n)" 6
  python3 perfect_chain.py --multiperfect 3 100000
  python3 perfect_chain.py --near-perfect 10000
  python3 perfect_chain.py --amicable 100000
  python3 perfect_chain.py --abundant-deficient 10000
"""

import argparse
import math
import sys
from fractions import Fraction
from collections import defaultdict

# ─────────────────────────────────────────────────────────────
# Known Mersenne primes: 2^p - 1 is prime for these p values
# Perfect number = 2^(p-1) * (2^p - 1)
# ─────────────────────────────────────────────────────────────
MERSENNE_EXPONENTS = [2, 3, 5, 7, 13, 17, 19, 31]

def mersenne_perfect(p):
    """Return the perfect number 2^(p-1) * (2^p - 1)."""
    return (1 << (p - 1)) * ((1 << p) - 1)

PERFECT_NUMBERS = [mersenne_perfect(p) for p in MERSENNE_EXPONENTS]
# [6, 28, 496, 8128, 33550336, 8589869056, 137438691328, 2305843008139952128]


# ─────────────────────────────────────────────────────────────
# Core arithmetic functions (exact, using Fraction where needed)
# ─────────────────────────────────────────────────────────────

def factorize(n):
    """Return prime factorization as dict {prime: exponent}."""
    if n < 2:
        return {}
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
    """Sum of divisors sigma(n)."""
    if n < 1:
        return 0
    s = 0
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            s += i
            if i != n // i:
                s += n // i
    return s


def sigma_frac(n):
    """sigma(n) as Fraction."""
    return Fraction(sigma(n))


def tau(n):
    """Number of divisors tau(n)."""
    if n < 1:
        return 0
    t = 0
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            t += 1
            if i != n // i:
                t += 1
    return t


def phi(n):
    """Euler's totient phi(n)."""
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


def sigma_minus1(n):
    """sigma_{-1}(n) = sum of 1/d for d|n = sigma(n)/n."""
    return Fraction(sigma(n), n)


def is_perfect(n):
    """Check if n is a perfect number: sigma(n) = 2n."""
    return sigma(n) == 2 * n


def R(n):
    """R(n) = sigma(n)*phi(n) / (n*tau(n))."""
    return Fraction(sigma(n) * phi(n), n * tau(n))


def S(n):
    """S(n) = sigma(n)*tau(n) / (n*phi(n))."""
    return Fraction(sigma(n) * tau(n), n * phi(n))


def B(n):
    """B(n) = R(n) * S(n) = (sigma(n)/n)^2."""
    return Fraction(sigma(n) * sigma(n), n * n)


def abundancy(n):
    """Abundancy index sigma(n)/n."""
    return Fraction(sigma(n), n)


# ─────────────────────────────────────────────────────────────
# Full profile for a number
# ─────────────────────────────────────────────────────────────

def full_profile(n):
    """Compute full arithmetic profile for n."""
    s = sigma(n)
    t = tau(n)
    p = phi(n)
    r = Fraction(s * p, n * t)
    sv = Fraction(s * t, n * p)
    b = r * sv
    sm1 = Fraction(s, n)
    facts = factorize(n)
    return {
        'n': n,
        'sigma': s,
        'tau': t,
        'phi': p,
        'sigma_m1': sm1,
        'R': r,
        'S': sv,
        'RS': b,
        'factors': facts,
        'is_perfect': s == 2 * n,
    }


# ─────────────────────────────────────────────────────────────
# Theorems to verify
# ─────────────────────────────────────────────────────────────

THEOREMS = {}

def theorem(name, description):
    """Decorator to register a theorem."""
    def decorator(func):
        THEOREMS[name] = (func, description)
        return func
    return decorator


@theorem('sigma_phi', 'sigma(n)*phi(n) = n*tau(n)  iff  n in {1,6}')
def thm_sigma_phi(n):
    """sigma*phi == n*tau characterizes n=6."""
    lhs = sigma(n) * phi(n)
    rhs = n * tau(n)
    return lhs == rhs, Fraction(lhs, rhs)


@theorem('dual', 'sigma(n)*tau(n) = n*phi(n)  iff  n in {1,28}')
def thm_dual(n):
    """sigma*tau == n*phi characterizes n=28."""
    lhs = sigma(n) * tau(n)
    rhs = n * phi(n)
    return lhs == rhs, Fraction(lhs, rhs)


@theorem('RS_eq_4', 'R(n)*S(n) = 4  for perfect numbers (sigma/n=2)')
def thm_rs_eq_4(n):
    """For perfect n, RS = (sigma/n)^2 = 4."""
    rs = B(n)
    return rs == 4, rs


@theorem('sigma_m1_eq_2', 'sigma_{-1}(n) = 2  iff  n is perfect')
def thm_sigma_m1(n):
    """sigma_{-1}(n) = sum(1/d) = 2 iff perfect."""
    sm1 = sigma_minus1(n)
    return sm1 == 2, sm1


@theorem('R_less_n', 'R(n) < n  for all n >= 2')
def thm_r_less_n(n):
    """R(n) < n for all n >= 2."""
    r = R(n)
    return r < n, r


@theorem('gap', 'R(6)=1, R(28)!=1: gap between consecutive perfects')
def thm_gap(n):
    """R(n) == 1 only for n in {1, 6}."""
    r = R(n)
    return r == 1, r


@theorem('phi_tau_ratio', 'phi(n)/tau(n) pattern across perfect numbers')
def thm_phi_tau_ratio(n):
    """Compute phi/tau ratio for structure analysis."""
    t = tau(n)
    p = phi(n)
    ratio = Fraction(p, t)
    # For perfect n = 2^(k-1)(2^k-1): phi = 2^(k-2)(2^k-2), tau = 2k
    # No fixed target; report ratio
    return True, ratio


@theorem('sigma_over_phi', 'sigma(n)/phi(n) pattern across perfect numbers')
def thm_sigma_over_phi(n):
    """sigma/phi ratio."""
    s = sigma(n)
    p = phi(n)
    return True, Fraction(s, p)


@theorem('abundance_chain', 'sigma(n)/n = 2 chain across perfect numbers')
def thm_abundance_chain(n):
    """Verify abundancy = 2 for all perfect numbers."""
    ab = abundancy(n)
    return ab == 2, ab


@theorem('tau_formula', 'tau(2^(p-1)(2^p-1)) = 2p for Mersenne perfect numbers')
def thm_tau_formula(n):
    """For even perfect n = 2^(p-1)(2^p-1), tau(n) = 2p."""
    facts = factorize(n)
    if 2 not in facts:
        return False, Fraction(0)
    k = facts[2]  # p-1
    p = k + 1
    mersenne = (1 << p) - 1
    if n != (1 << k) * mersenne:
        return False, Fraction(tau(n))
    expected = 2 * p
    actual = tau(n)
    return actual == expected, Fraction(actual, expected)


@theorem('phi_formula', 'phi(2^(p-1)(2^p-1)) = 2^(p-2)(2^p-2) for Mersenne perfect')
def thm_phi_formula(n):
    """For even perfect n = 2^(p-1)(2^p-1), phi(n) = 2^(p-2)*(2^p-2)."""
    facts = factorize(n)
    if 2 not in facts:
        return False, Fraction(0)
    k = facts[2]  # p-1
    p = k + 1
    mersenne = (1 << p) - 1
    if n != (1 << k) * mersenne:
        return False, Fraction(phi(n))
    expected = (1 << (p - 2)) * ((1 << p) - 2)
    actual = phi(n)
    return actual == expected, Fraction(actual, expected)


# ─────────────────────────────────────────────────────────────
# Mode: --all-perfect K
# ─────────────────────────────────────────────────────────────

def cmd_all_perfect(k):
    """Compute full profile for first K perfect numbers."""
    nums = PERFECT_NUMBERS[:k]
    print(f"## Full Profile for First {k} Perfect Numbers\n")

    # Header
    print(f"| {'n':>15} | {'p':>3} | {'sigma':>15} | {'tau':>6} | {'phi':>15} "
          f"| {'R':>12} | {'S':>12} | {'RS':>4} | {'sigma_m1':>4} |")
    print(f"|{'-'*17}|{'-'*5}|{'-'*17}|{'-'*8}|{'-'*17}"
          f"|{'-'*14}|{'-'*14}|{'-'*6}|{'-'*6}|")

    for i, n in enumerate(nums):
        prof = full_profile(n)
        p = MERSENNE_EXPONENTS[i]
        r_f = float(prof['R'])
        s_f = float(prof['S'])
        rs_f = float(prof['RS'])
        sm1_f = float(prof['sigma_m1'])
        print(f"| {n:>15} | {p:>3} | {prof['sigma']:>15} | {prof['tau']:>6} "
              f"| {prof['phi']:>15} | {r_f:>12.6f} | {s_f:>12.6f} "
              f"| {rs_f:>4.1f} | {sm1_f:>4.1f} |")

    # R value analysis
    print(f"\n### R(n) Values (exact fractions)\n")
    for i, n in enumerate(nums):
        r = R(n)
        s = S(n)
        print(f"  n={n}: R = {r} = {float(r):.10f}")
        print(f"  {' '*len(str(n))}  S = {s} = {float(s):.10f}")
        print(f"  {' '*len(str(n))}  RS = {r*s} = {float(r*s):.6f}")
        print()

    # ASCII chart of R values
    print("### R(n) Across Perfect Numbers (ASCII)\n")
    r_vals = [(n, float(R(n))) for n in nums]
    max_r = max(v for _, v in r_vals)
    bar_width = 50
    for n, rv in r_vals:
        bar_len = int(rv / max_r * bar_width) if max_r > 0 else 0
        bar = '#' * bar_len
        print(f"  n={n:>15} | {bar:<{bar_width}} | R={rv:.6f}")

    # Check R=1 uniqueness
    print(f"\n### R(n)=1 Check\n")
    for n in nums:
        r = R(n)
        status = "PASS (R=1)" if r == 1 else f"FAIL (R={r} = {float(r):.6f})"
        print(f"  n={n}: {status}")
    r1_set = [n for n in nums if R(n) == 1]
    print(f"\n  R(n)=1 holds only for: {r1_set}")
    if r1_set == [6]:
        print("  --> Confirms: sigma*phi = n*tau characterizes n=6 among perfect numbers")


# ─────────────────────────────────────────────────────────────
# Mode: --verify-theorem
# ─────────────────────────────────────────────────────────────

def cmd_verify_theorem(name):
    """Verify a specific theorem across perfect numbers."""
    if name == 'list':
        print("## Available Theorems\n")
        for tname, (_, desc) in sorted(THEOREMS.items()):
            print(f"  {tname:20s} : {desc}")
        return

    if name == 'all':
        for tname in sorted(THEOREMS.keys()):
            cmd_verify_theorem(tname)
            print()
        return

    if name not in THEOREMS:
        print(f"Unknown theorem: {name}")
        print(f"Available: {', '.join(sorted(THEOREMS.keys()))}")
        return

    func, desc = THEOREMS[name]
    print(f"## Theorem: {name}")
    print(f"   {desc}\n")

    print(f"| {'n':>15} | {'Pass':>6} | {'Value':>20} | {'Float':>14} |")
    print(f"|{'-'*17}|{'-'*8}|{'-'*22}|{'-'*16}|")

    all_pass = True
    results = []
    for n in PERFECT_NUMBERS[:8]:
        try:
            passed, value = func(n)
        except (ZeroDivisionError, OverflowError) as e:
            passed, value = False, Fraction(0)
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        val_str = str(value) if len(str(value)) <= 20 else f"{float(value):.10f}"
        print(f"| {n:>15} | {status:>6} | {val_str:>20} | {float(value):>14.8f} |")
        results.append((n, passed, value))

    print()
    if all_pass:
        print(f"  Result: ALL PASS -- theorem holds for all tested perfect numbers")
    else:
        passing = [n for n, p, _ in results if p]
        failing = [n for n, p, _ in results if not p]
        print(f"  Passing: {passing}")
        print(f"  Failing: {failing}")


# ─────────────────────────────────────────────────────────────
# Mode: --generalize N
# ─────────────────────────────────────────────────────────────

def cmd_generalize(base_n):
    """Given identities hold at base_n, check if they hold for other perfect numbers."""
    print(f"## Generalization Test: Identities from n={base_n}\n")

    targets = [n for n in PERFECT_NUMBERS[:6] if n != base_n][:5]

    # Collect base profile
    bp = full_profile(base_n)
    print(f"Base profile (n={base_n}):")
    print(f"  sigma={bp['sigma']}, tau={bp['tau']}, phi={bp['phi']}")
    print(f"  R={bp['R']} ({float(bp['R']):.6f})")
    print(f"  S={bp['S']} ({float(bp['S']):.6f})")
    print(f"  RS={bp['RS']} ({float(bp['RS']):.6f})")
    print(f"  sigma_m1={bp['sigma_m1']} ({float(bp['sigma_m1']):.6f})")
    print()

    # Identity tests
    identities = [
        ('sigma*phi == n*tau (R=1)',
         lambda n: sigma(n) * phi(n) == n * tau(n),
         lambda n: Fraction(sigma(n) * phi(n), n * tau(n))),
        ('sigma*tau == n*phi (S=1)',
         lambda n: sigma(n) * tau(n) == n * phi(n),
         lambda n: Fraction(sigma(n) * tau(n), n * phi(n))),
        ('RS == 4',
         lambda n: B(n) == 4,
         lambda n: B(n)),
        ('sigma/n == 2',
         lambda n: sigma(n) == 2 * n,
         lambda n: Fraction(sigma(n), n)),
        ('sigma_{-1} == 2',
         lambda n: sigma_minus1(n) == 2,
         lambda n: sigma_minus1(n)),
        ('tau == 2p (Mersenne form)',
         lambda n: _check_tau_2p(n),
         lambda n: Fraction(tau(n))),
    ]

    print(f"| {'Identity':>30} | {'n=' + str(base_n):>8} |", end='')
    for t in targets:
        print(f" {'n=' + str(t):>8} |", end='')
    print()

    sep = f"|{'-'*32}|{'-'*10}|"
    for _ in targets:
        sep += f"{'-'*10}|"
    print(sep)

    all_nums = [base_n] + targets
    for desc, test_fn, val_fn in identities:
        row = f"| {desc:>30} |"
        for num in all_nums:
            try:
                tp = test_fn(num)
                tv = val_fn(num)
                if tp:
                    row += f" {'PASS':>8} |"
                else:
                    fv = float(tv)
                    row += f" {fv:>8.4f} |"
            except Exception:
                row += f" {'ERR':>8} |"
        print(row)

    # Generalization summary
    print(f"\n### Summary\n")
    for desc, test_fn, val_fn in identities:
        holds_at = [n for n in all_nums if test_fn(n)]
        print(f"  {desc}")
        print(f"    Holds at: {holds_at}")
        if len(holds_at) == 1:
            print(f"    --> UNIQUE to n={holds_at[0]} (characterization!)")
        elif len(holds_at) == len(all_nums):
            print(f"    --> UNIVERSAL across all {len(all_nums)} tested perfect numbers")
        else:
            print(f"    --> PARTIAL: holds at {len(holds_at)}/{len(all_nums)} tested")
        print()


def _check_tau_2p(n):
    """Check if tau(n) = 2p for Mersenne form n = 2^(p-1)(2^p-1)."""
    facts = factorize(n)
    if 2 not in facts:
        return False
    k = facts[2]
    p = k + 1
    return tau(n) == 2 * p


# ─────────────────────────────────────────────────────────────
# Mode: --test-identity
# ─────────────────────────────────────────────────────────────

def cmd_test_identity(expr, base_n):
    """Test a symbolic expression across perfect numbers.

    The expression can use: n, sigma(n), tau(n), phi(n), R(n), S(n), B(n),
    sigma_m1(n), Fraction, math functions.
    """
    print(f"## Test Identity: {expr}")
    print(f"   Base number: {base_n}\n")

    # Build evaluation namespace
    ns = {
        'Fraction': Fraction,
        'math': math,
        'sigma': sigma,
        'tau': tau,
        'phi': phi,
        'R': R,
        'S': S,
        'B': B,
        'sigma_m1': sigma_minus1,
        'sigma_minus1': sigma_minus1,
        'factorize': factorize,
        'log': math.log,
        'sqrt': math.sqrt,
        'pi': math.pi,
        'e': math.e,
    }

    test_nums = [base_n] + [p for p in PERFECT_NUMBERS[:6] if p != base_n]

    print(f"| {'n':>15} | {'LHS':>20} | {'RHS':>20} | {'Pass':>6} | {'Ratio':>12} |")
    print(f"|{'-'*17}|{'-'*22}|{'-'*22}|{'-'*8}|{'-'*14}|")

    # Parse expr: expect "LHS==RHS" or "LHS=RHS" or just "EXPR" (test if truthy)
    if '==' in expr:
        lhs_expr, rhs_expr = expr.split('==', 1)
    elif '=' in expr and '!=' not in expr and '<=' not in expr and '>=' not in expr:
        lhs_expr, rhs_expr = expr.split('=', 1)
    else:
        lhs_expr = expr
        rhs_expr = None

    for n in test_nums:
        ns['n'] = n
        try:
            lhs_val = eval(lhs_expr.strip(), ns)
            if rhs_expr is not None:
                rhs_val = eval(rhs_expr.strip(), ns)
                passed = (lhs_val == rhs_val)
                if isinstance(lhs_val, (int, Fraction)) and isinstance(rhs_val, (int, Fraction)):
                    ratio = Fraction(lhs_val, rhs_val) if rhs_val != 0 else 'inf'
                else:
                    ratio = lhs_val / rhs_val if rhs_val != 0 else float('inf')
            else:
                rhs_val = 'N/A'
                passed = bool(lhs_val)
                ratio = lhs_val

            lhs_s = str(lhs_val) if len(str(lhs_val)) <= 20 else f"{float(lhs_val):.6f}"
            rhs_s = str(rhs_val) if len(str(rhs_val)) <= 20 else f"{float(rhs_val):.6f}"
            ratio_s = str(ratio) if len(str(ratio)) <= 12 else f"{float(ratio):.6f}"
            status = "PASS" if passed else "FAIL"
            print(f"| {n:>15} | {lhs_s:>20} | {rhs_s:>20} | {status:>6} | {ratio_s:>12} |")
        except Exception as e:
            print(f"| {n:>15} | {'ERROR':>20} | {str(e)[:20]:>20} | {'ERR':>6} | {'N/A':>12} |")

    print()


# ─────────────────────────────────────────────────────────────
# Mode: --multiperfect K N
# ─────────────────────────────────────────────────────────────

def cmd_multiperfect(k, limit):
    """Find k-perfect numbers (sigma(n) = k*n) up to limit."""
    print(f"## {k}-Perfect Numbers up to {limit}\n")

    found = []
    for n in range(1, limit + 1):
        if sigma(n) == k * n:
            found.append(n)

    if not found:
        print(f"  No {k}-perfect numbers found up to {limit}.")
        return

    print(f"  Found {len(found)} numbers: {found[:20]}")
    if len(found) > 20:
        print(f"  ... and {len(found)-20} more")
    print()

    print(f"| {'n':>12} | {'sigma':>12} | {'tau':>6} | {'phi':>12} "
          f"| {'R':>12} | {'S':>12} | {'RS':>8} |")
    print(f"|{'-'*14}|{'-'*14}|{'-'*8}|{'-'*14}"
          f"|{'-'*14}|{'-'*14}|{'-'*10}|")

    for n in found[:30]:
        r = R(n)
        s = S(n)
        rs = r * s
        print(f"| {n:>12} | {sigma(n):>12} | {tau(n):>6} | {phi(n):>12} "
              f"| {float(r):>12.6f} | {float(s):>12.6f} | {float(rs):>8.4f} |")

    # RS pattern
    print(f"\n### RS Values for {k}-perfect numbers\n")
    print(f"  For k-perfect: sigma/n = k, so RS = (sigma/n)^2 = k^2 = {k**2}")
    for n in found[:10]:
        rs = B(n)
        status = "PASS" if rs == k * k else "FAIL"
        print(f"  n={n}: RS = {rs} = {float(rs):.4f}  [{status}]")


# ─────────────────────────────────────────────────────────────
# Mode: --near-perfect N
# ─────────────────────────────────────────────────────────────

def cmd_near_perfect(limit, epsilon=0.01):
    """Find numbers where |R(n) - 1| < epsilon."""
    print(f"## Near-Perfect Numbers (|R-1| < {epsilon}) up to {limit}\n")

    results = []
    for n in range(2, limit + 1):
        r = R(n)
        diff = abs(float(r) - 1.0)
        if diff < epsilon:
            results.append((n, r, diff))

    results.sort(key=lambda x: x[2])

    print(f"  Found {len(results)} numbers\n")
    print(f"| {'n':>10} | {'R(n)':>15} | {'|R-1|':>12} | {'Perfect?':>8} | {'Factors':>25} |")
    print(f"|{'-'*12}|{'-'*17}|{'-'*14}|{'-'*10}|{'-'*27}|")

    for n, r, diff in results[:40]:
        facts = factorize(n)
        fact_str = ' * '.join(f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(facts.items()))
        perf = "YES" if is_perfect(n) else ""
        r_str = str(r) if len(str(r)) <= 15 else f"{float(r):.10f}"
        print(f"| {n:>10} | {r_str:>15} | {diff:>12.8f} | {perf:>8} | {fact_str:>25} |")

    # R=1 exact
    exact = [(n, r) for n, r, d in results if d == 0.0 and r == 1]
    if exact:
        print(f"\n  Exact R(n)=1: {[n for n,_ in exact]}")
    else:
        print(f"\n  No exact R(n)=1 found in range (known: n=1, n=6)")

    # Distribution histogram
    if results:
        print(f"\n### |R-1| Distribution (ASCII)\n")
        bins = [0, 0.001, 0.002, 0.003, 0.005, 0.01]
        for i in range(len(bins) - 1):
            count = sum(1 for _, _, d in results if bins[i] <= d < bins[i+1])
            bar = '#' * min(count, 60)
            print(f"  [{bins[i]:.3f}, {bins[i+1]:.3f}) : {count:>4} {bar}")


# ─────────────────────────────────────────────────────────────
# Mode: --amicable N
# ─────────────────────────────────────────────────────────────

def cmd_amicable(limit):
    """Find amicable pairs up to limit and compute their R values."""
    print(f"## Amicable Pairs up to {limit}\n")

    # Precompute sigma
    sigma_cache = {}
    for n in range(1, limit + 1):
        sigma_cache[n] = sigma(n)

    pairs = []
    for a in range(2, limit + 1):
        b = sigma_cache[a] - a  # sum of proper divisors
        if b > a and b <= limit:
            sb = sigma_cache[b] - b
            if sb == a:
                pairs.append((a, b))

    if not pairs:
        print(f"  No amicable pairs found up to {limit}.")
        print(f"  (First amicable pair is (220, 284). Try --amicable 300)")
        return

    print(f"  Found {len(pairs)} amicable pairs\n")
    print(f"| {'a':>8} | {'b':>8} | {'R(a)':>12} | {'R(b)':>12} "
          f"| {'S(a)':>12} | {'S(b)':>12} | {'RS(a)':>8} | {'RS(b)':>8} |")
    print(f"|{'-'*10}|{'-'*10}|{'-'*14}|{'-'*14}"
          f"|{'-'*14}|{'-'*14}|{'-'*10}|{'-'*10}|")

    for a, b in pairs[:30]:
        ra, rb = R(a), R(b)
        sa, sb_v = S(a), S(b)
        rsa, rsb = B(a), B(b)
        print(f"| {a:>8} | {b:>8} | {float(ra):>12.6f} | {float(rb):>12.6f} "
              f"| {float(sa):>12.6f} | {float(sb_v):>12.6f} "
              f"| {float(rsa):>8.4f} | {float(rsb):>8.4f} |")

    # Abundancy analysis
    print(f"\n### Abundancy of Amicable Pairs\n")
    for a, b in pairs[:10]:
        ab_a = abundancy(a)
        ab_b = abundancy(b)
        print(f"  ({a}, {b}): sigma(a)/a = {ab_a} = {float(ab_a):.6f}, "
              f"sigma(b)/b = {ab_b} = {float(ab_b):.6f}")
        print(f"            sum = {float(ab_a + ab_b):.6f}")


# ─────────────────────────────────────────────────────────────
# Mode: --abundant-deficient N
# ─────────────────────────────────────────────────────────────

def cmd_abundant_deficient(limit):
    """Classify numbers and compare R distributions."""
    print(f"## Abundant/Deficient/Perfect Classification up to {limit}\n")

    abundant = []
    deficient = []
    perfect = []

    r_abundant = []
    r_deficient = []
    r_perfect = []

    for n in range(2, limit + 1):
        s = sigma(n)
        r = Fraction(s * phi(n), n * tau(n))
        if s > 2 * n:
            abundant.append(n)
            r_abundant.append(float(r))
        elif s < 2 * n:
            deficient.append(n)
            r_deficient.append(float(r))
        else:
            perfect.append(n)
            r_perfect.append(float(r))

    print(f"| Category   | Count | Fraction | Mean R    | Min R     | Max R     |")
    print(f"|------------|-------|----------|-----------|-----------|-----------|")

    total = len(abundant) + len(deficient) + len(perfect)
    for label, nums, r_vals in [
        ('Abundant', abundant, r_abundant),
        ('Deficient', deficient, r_deficient),
        ('Perfect', perfect, r_perfect),
    ]:
        if r_vals:
            mean_r = sum(r_vals) / len(r_vals)
            min_r = min(r_vals)
            max_r = max(r_vals)
        else:
            mean_r = min_r = max_r = 0
        frac = len(nums) / total if total > 0 else 0
        print(f"| {label:<10} | {len(nums):>5} | {frac:>8.4f} "
              f"| {mean_r:>9.6f} | {min_r:>9.6f} | {max_r:>9.6f} |")

    # R distribution histogram
    print(f"\n### R Distribution by Category (ASCII)\n")
    bins = [0, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 50.0, 200.0]
    max_bar = 50

    for label, r_vals in [('Abundant', r_abundant), ('Deficient', r_deficient)]:
        print(f"  {label}:")
        counts = []
        for i in range(len(bins) - 1):
            c = sum(1 for v in r_vals if bins[i] <= v < bins[i+1])
            counts.append(c)
        max_c = max(counts) if counts else 1
        for i, c in enumerate(counts):
            bar_len = int(c / max_c * max_bar) if max_c > 0 else 0
            bar = '#' * bar_len
            print(f"    [{bins[i]:>5.1f}, {bins[i+1]:>5.1f}) : {c:>5} {bar}")
        print()

    # Perfect numbers detail
    if perfect:
        print(f"  Perfect numbers found: {perfect}")
        for n in perfect:
            r = R(n)
            s = S(n)
            print(f"    n={n}: R={r} ({float(r):.6f}), S={s} ({float(s):.6f})")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Perfect number generalization tester',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all-perfect 5
  %(prog)s --verify-theorem all
  %(prog)s --verify-theorem sigma_phi
  %(prog)s --verify-theorem list
  %(prog)s --generalize 6
  %(prog)s --test-identity "sigma(n)*phi(n)==n*tau(n)" 6
  %(prog)s --multiperfect 2 10000
  %(prog)s --near-perfect 10000
  %(prog)s --amicable 100000
  %(prog)s --abundant-deficient 10000
        """)

    parser.add_argument('--all-perfect', type=int, metavar='K',
                        help='Compute full profile for first K perfect numbers')
    parser.add_argument('--verify-theorem', type=str, metavar='NAME',
                        help='Verify theorem (name, "all", or "list")')
    parser.add_argument('--generalize', type=int, metavar='N',
                        help='Test identities from n=N across other perfect numbers')
    parser.add_argument('--test-identity', nargs=2, metavar=('EXPR', 'N'),
                        help='Test expression across perfect numbers (base N)')
    parser.add_argument('--multiperfect', nargs=2, type=int, metavar=('K', 'N'),
                        help='Find k-perfect numbers up to N')
    parser.add_argument('--near-perfect', type=int, metavar='N',
                        help='Find numbers where |R-1| < epsilon up to N')
    parser.add_argument('--amicable', type=int, metavar='N',
                        help='Find amicable pairs up to N')
    parser.add_argument('--abundant-deficient', type=int, metavar='N',
                        help='Classify numbers up to N')
    parser.add_argument('--epsilon', type=float, default=0.01,
                        help='Epsilon for near-perfect (default 0.01)')

    args = parser.parse_args()

    if args.all_perfect:
        cmd_all_perfect(args.all_perfect)
    elif args.verify_theorem:
        cmd_verify_theorem(args.verify_theorem)
    elif args.generalize:
        cmd_generalize(args.generalize)
    elif args.test_identity:
        expr, base = args.test_identity
        cmd_test_identity(expr, int(base))
    elif args.multiperfect:
        k, n = args.multiperfect
        cmd_multiperfect(k, n)
    elif args.near_perfect:
        cmd_near_perfect(args.near_perfect, args.epsilon)
    elif args.amicable:
        cmd_amicable(args.amicable)
    elif args.abundant_deficient:
        cmd_abundant_deficient(args.abundant_deficient)
    else:
        # Default: run a quick overview
        print("# Perfect Chain — Quick Overview\n")
        cmd_all_perfect(5)
        print("\n" + "=" * 70 + "\n")
        cmd_verify_theorem('all')


if __name__ == '__main__':
    main()
