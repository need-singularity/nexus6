#!/usr/bin/env python3
"""Arithmetic identity auto-discovery tool.

Discovers identities of the form F1(n)*F2(n) = F3(n)*F4(n) where each Fi
is drawn from {sigma, tau, phi, n, id, lambda, omega, Omega, mu, sigma_k}.

Known identities:
  sigma*phi = n*tau  <==>  {1, 6}
  tau*phi   = sigma  <==>  {1, 3, 14, 42}
  phi*phi   = phi    <==>  {1, 3, 10, 30}  (phi^2 = phi*phi pointwise vs convolution)

Usage:
  python3 identity_finder.py --scan 10000
  python3 identity_finder.py --verify "sigma*phi=n*tau" 100000
  python3 identity_finder.py --cancellation "sigma*phi=n*tau"
  python3 identity_finder.py --local-factors "sigma*phi=n*tau" --prime-range 30
  python3 identity_finder.py --generalize 5
"""
import argparse
import math
import sys
from fractions import Fraction
from collections import defaultdict
from itertools import product as itertools_product


# ─────────────────────────────────────────────────────────
# Arithmetic functions
# ─────────────────────────────────────────────────────────

def factorize(n):
    """Return dict {prime: exponent}."""
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


def sigma_k(n, k):
    """Sum of k-th powers of divisors."""
    if n < 1:
        return 0
    s = 0
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            s += i**k
            if i * i != n:
                s += (n // i)**k
    return s


def tau(n):
    """Number of divisors."""
    if n < 1:
        return 0
    t = 0
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            t += 1
            if i * i != n:
                t += 1
    return t


def phi(n):
    """Euler totient."""
    if n < 1:
        return 0
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


def lambda_func(n):
    """Carmichael lambda function."""
    if n < 1:
        return 0
    if n <= 2:
        return 1
    facts = factorize(n)
    result = 1
    for p, a in facts.items():
        if p == 2:
            if a <= 2:
                lam = phi(2**a)
            else:
                lam = phi(2**a) // 2
        else:
            lam = (p - 1) * p**(a - 1)
        result = lcm(result, lam)
    return result


def lcm(a, b):
    return abs(a * b) // math.gcd(a, b) if a and b else 0


def omega_func(n):
    """Number of distinct prime factors."""
    if n < 2:
        return 0
    return len(factorize(n))


def big_omega(n):
    """Number of prime factors with multiplicity."""
    if n < 2:
        return 0
    return sum(factorize(n).values())


def mu(n):
    """Mobius function."""
    if n < 1:
        return 0
    if n == 1:
        return 1
    facts = factorize(n)
    for a in facts.values():
        if a >= 2:
            return 0
    return (-1)**len(facts)


def identity(n):
    """Identity function: id(n) = n."""
    return n


def const_one(n):
    """Constant function: 1(n) = 1."""
    return 1


# Function registry
FUNC_MAP = {
    'sigma': sigma,
    's': sigma,
    'tau': tau,
    't': tau,
    'phi': phi,
    'p': phi,
    'n': identity,
    'id': const_one,
    'lambda': lambda_func,
    'lam': lambda_func,
    'omega': omega_func,
    'w': omega_func,
    'Omega': big_omega,
    'W': big_omega,
    'mu': mu,
    'sigma2': lambda n: sigma_k(n, 2),
    'sigma3': lambda n: sigma_k(n, 3),
    'sigma0': tau,  # sigma_0 = tau
}

# Short labels for scan mode (core functions only)
SCAN_FUNCS = ['sigma', 'tau', 'phi', 'n', 'id']
SCAN_LABELS = {'sigma': 'sig', 'tau': 'tau', 'phi': 'phi', 'n': 'n', 'id': '1'}


# ─────────────────────────────────────────────────────────
# Expression parser
# ─────────────────────────────────────────────────────────

def parse_expr(expr_str):
    """Parse expression like 'sigma*phi' or 'n^2*tau' into evaluator.

    Returns (func, label) where func(n) evaluates the expression.
    Supports: function names, *, /, ^integer
    """
    expr_str = expr_str.strip()
    if not expr_str or expr_str == '1' or expr_str == 'id':
        return const_one, '1'

    # Tokenize: split on * and /
    # First handle ^ (power)
    tokens = []
    ops = []

    parts = []
    current = ''
    for ch in expr_str:
        if ch in '*/':
            parts.append(current.strip())
            parts.append(ch)
            current = ''
        else:
            current += ch
    parts.append(current.strip())

    # Parse each part
    funcs = []
    operations = []  # True = multiply, False = divide
    for i, part in enumerate(parts):
        if part in '*/':
            operations.append(part == '*')
            continue
        if not part:
            continue
        # Handle power: func^k
        if '^' in part:
            base, exp = part.split('^', 1)
            base = base.strip()
            exp = int(exp.strip())
            if base in FUNC_MAP:
                f = FUNC_MAP[base]
                funcs.append((f, exp, base))
            else:
                raise ValueError(f"Unknown function: {base}")
        else:
            if part in FUNC_MAP:
                funcs.append((FUNC_MAP[part], 1, part))
            else:
                raise ValueError(f"Unknown function: {part}")

    if not operations:
        operations = [True] * (len(funcs) - 1)

    def evaluator(n):
        if not funcs:
            return 1
        result = Fraction(funcs[0][0](n) ** funcs[0][1])
        for i, op in enumerate(operations):
            val = Fraction(funcs[i + 1][0](n) ** funcs[i + 1][1])
            if op:
                result *= val
            else:
                if val == 0:
                    return None  # division by zero
                result /= val
        return result

    return evaluator, expr_str


def parse_identity(identity_str):
    """Parse 'EXPR1=EXPR2' into two evaluators."""
    if '=' not in identity_str:
        raise ValueError(f"Identity must contain '=': {identity_str}")
    lhs_str, rhs_str = identity_str.split('=', 1)
    lhs_func, lhs_label = parse_expr(lhs_str)
    rhs_func, rhs_label = parse_expr(rhs_str)
    return lhs_func, rhs_func, lhs_label, rhs_label


# ─────────────────────────────────────────────────────────
# Core algorithms
# ─────────────────────────────────────────────────────────

def find_solutions(lhs_func, rhs_func, N, start=1):
    """Find all n in [start, N] where LHS(n) == RHS(n)."""
    solutions = []
    for n in range(max(start, 1), N + 1):
        lv = lhs_func(n)
        rv = rhs_func(n)
        if lv is not None and rv is not None and lv == rv:
            solutions.append(n)
    return solutions


def compute_local_factors(lhs_func, rhs_func, prime_range=50, max_exp=6):
    """Compute f(p,a) = LHS(p^a) / RHS(p^a) for primes p up to prime_range."""
    primes = sieve(prime_range)
    results = {}
    for p in primes:
        results[p] = {}
        pa = 1
        for a in range(1, max_exp + 1):
            pa *= p
            lv = lhs_func(pa)
            rv = rhs_func(pa)
            if rv is not None and rv != 0 and lv is not None:
                results[p][a] = Fraction(lv, rv)
            else:
                break
    return results


def sieve(limit):
    """Simple sieve of Eratosthenes."""
    if limit < 2:
        return []
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if is_prime[i]:
            for j in range(i * i, limit + 1, i):
                is_prime[j] = False
    return [i for i in range(2, limit + 1) if is_prime[i]]


def find_cancellation_prime(local_factors):
    """Find (p, a) pairs where f(p,a) < 1 and the cancellation prime q.

    For multiplicative identities, the product of f(p,1) over primes dividing n
    must equal 1 at solutions. If f(2,1)<1 (deficit), find q where f(2,1)*f(q,1)=1.
    """
    sub_unity = []
    super_unity = []

    for p, exps in sorted(local_factors.items()):
        if 1 in exps:
            f = exps[1]
            if f < 1:
                sub_unity.append((p, f))
            elif f > 1:
                super_unity.append((p, f))

    # Find cancellation pairs
    cancellations = []
    for p1, f1 in sub_unity:
        for p2, f2 in super_unity:
            if f1 * f2 == 1:
                cancellations.append((p1, p2, f1, f2))

    return sub_unity, super_unity, cancellations


def estimate_finiteness(solutions, N, tail_fraction=0.5):
    """Heuristic: if no solutions in the upper tail_fraction of [1,N], likely finite."""
    if not solutions:
        return True, 0
    max_sol = max(solutions)
    threshold = N * tail_fraction
    no_tail = max_sol < threshold
    density = len(solutions) / N
    return no_tail, density


def texas_pvalue(n_solutions, N, n_funcs_tried):
    """Texas sharpshooter p-value with Bonferroni correction.

    Under null: each n independently matches with probability ~1/n (heuristic).
    Expected matches ~ ln(N). If observed << expected for random, p is low.
    """
    # More careful: for random multiplicative functions, prob of match at n
    # is roughly 1/n for large n. Expected count ~ sum(1/k, k=1..N) ~ ln(N).
    # But our functions are structured, so use empirical null:
    # We count how many of the n_funcs_tried combinations had <= n_solutions solutions.
    # Simple approach: binomial with p = n_solutions/N per trial.
    if N == 0:
        return 1.0
    p_per_n = max(n_solutions, 1) / N
    # Bonferroni: multiply by number of hypotheses tested
    raw_p = p_per_n ** max(n_solutions, 1)
    corrected = min(1.0, raw_p * n_funcs_tried)
    return corrected


# ─────────────────────────────────────────────────────────
# Output formatting
# ─────────────────────────────────────────────────────────

def format_factor_table(local_factors, max_primes=15, max_exp=4):
    """Format local factors as markdown table with ASCII bar."""
    primes = sorted(local_factors.keys())[:max_primes]
    if not primes:
        return "No factors computed."

    # Header
    cols = ['p'] + [f'a={a}' for a in range(1, max_exp + 1)] + ['bar (a=1)']
    header = '| ' + ' | '.join(cols) + ' |'
    sep = '|' + '|'.join(['---'] * len(cols)) + '|'

    rows = [header, sep]
    for p in primes:
        exps = local_factors[p]
        vals = []
        for a in range(1, max_exp + 1):
            if a in exps:
                f = exps[a]
                vals.append(f'{float(f):.6f}')
            else:
                vals.append('-')

        # ASCII bar for a=1
        if 1 in exps:
            f1 = float(exps[1])
            bar_len = int(abs(f1 - 1.0) * 40)
            if f1 < 1:
                bar = '<' + '=' * min(bar_len, 20)
            elif f1 > 1:
                bar = '=' * min(bar_len, 20) + '>'
            else:
                bar = '|'  # exactly 1
        else:
            bar = '-'

        row = f'| {p} | ' + ' | '.join(vals) + f' | `{bar}` |'
        rows.append(row)

    return '\n'.join(rows)


def format_solutions(solutions, lhs_func, rhs_func, lhs_label, rhs_label, max_show=30):
    """Format solution set as markdown table with function values."""
    if not solutions:
        return "No solutions found."

    show = solutions[:max_show]
    header = f'| n | {lhs_label} | {rhs_label} | sigma | tau | phi |'
    sep = '|---|---|---|---|---|---|'
    rows = [header, sep]
    for n in show:
        lv = lhs_func(n)
        rv = rhs_func(n)
        s = sigma(n)
        t = tau(n)
        p = phi(n)
        rows.append(f'| {n} | {lv} | {rv} | {s} | {t} | {p} |')
    if len(solutions) > max_show:
        rows.append(f'| ... | ({len(solutions) - max_show} more) | | | | |')
    return '\n'.join(rows)


def format_ascii_factor_profile(local_factors, max_primes=20):
    """ASCII visualization of f(p,1) profile across primes."""
    primes = sorted(local_factors.keys())[:max_primes]
    if not primes:
        return ""

    lines = ["\nFactor profile f(p,1):"]
    lines.append("  p  | f(p,1)   | profile")
    lines.append("-----+----------+" + "-" * 42)

    for p in primes:
        if 1 not in local_factors[p]:
            continue
        f = float(local_factors[p][1])
        # Scale: 1.0 is center (col 20), each 0.05 = 1 char
        center = 20
        pos = center + int((f - 1.0) * 40)
        pos = max(0, min(41, pos))
        bar = [' '] * 42
        bar[center] = '|'
        if pos < center:
            for i in range(pos, center):
                bar[i] = '-'
            bar[pos] = '<'
        elif pos > center:
            for i in range(center + 1, pos + 1):
                bar[i] = '-'
            bar[pos] = '>'
        else:
            bar[center] = '*'
        line = f"  {p:>3} | {f:>8.5f} | {''.join(bar)}"
        lines.append(line)

    lines.append("     |          |" + " " * 19 + "^1.0")
    return '\n'.join(lines)


# ─────────────────────────────────────────────────────────
# Modes
# ─────────────────────────────────────────────────────────

def mode_scan(N, extended=False):
    """Try all combinations and find identities with finite solution sets."""
    func_names = SCAN_FUNCS
    if extended:
        func_names = list(FUNC_MAP.keys())
        # deduplicate aliases
        seen = set()
        unique = []
        for name in func_names:
            fobj = FUNC_MAP[name]
            fid = id(fobj)
            # For lambdas use name
            key = name if callable(fobj) and hasattr(fobj, '__name__') else name
            if key not in seen:
                seen.add(key)
                unique.append(name)
        func_names = unique

    print(f"Scanning identities up to N={N} using functions: {func_names}")
    print(f"Trying LHS=a*b, RHS=c*d combinations...")
    print()

    # Precompute function values
    print("Precomputing function values...", end=' ', flush=True)
    cache = {}
    for name in func_names:
        f = FUNC_MAP[name]
        vals = [None] * (N + 1)
        for n in range(1, N + 1):
            vals[n] = f(n)
        cache[name] = vals
    print("done.")

    # Generate all LHS * RHS pairs (products of 1 or 2 functions)
    # LHS = f1*f2, RHS = f3*f4
    # To avoid duplicates: normalize by sorting each side, and LHS <= RHS lexically
    pairs = []
    for i, a in enumerate(func_names):
        for b in func_names[i:]:
            pairs.append((a, b))

    print(f"Testing {len(pairs)} x {len(pairs)} = {len(pairs)**2} identity candidates...")
    print()

    discoveries = []
    n_tested = 0

    for i, (a, b) in enumerate(pairs):
        for j, (c, d) in enumerate(pairs):
            if (a, b) == (c, d):
                continue
            if j < i:
                continue  # avoid duplicate identity a*b=c*d and c*d=a*b

            n_tested += 1

            # Quick scan: check how many solutions exist
            solutions = []
            for n in range(1, N + 1):
                lhs = cache[a][n] * cache[b][n]
                rhs = cache[c][n] * cache[d][n]
                if lhs == rhs:
                    solutions.append(n)

            if not solutions:
                continue

            # Interesting if finite-looking: few solutions relative to N
            ratio = len(solutions) / N
            if ratio > 0.1:
                continue  # too many solutions, likely always true or trivially dense

            is_finite, density = estimate_finiteness(solutions, N)

            label = f"{a}*{b}={c}*{d}"
            discoveries.append({
                'label': label,
                'solutions': solutions,
                'count': len(solutions),
                'max_sol': max(solutions),
                'likely_finite': is_finite,
                'density': density,
            })

    # Sort by count (fewer = more interesting) then by max solution
    # Filter: remove trivial {1}-only identities
    nontrivial = [d for d in discoveries if d['count'] > 1 or d['max_sol'] > 1]
    trivial_count = len(discoveries) - len(nontrivial)
    discoveries = nontrivial

    discoveries.sort(key=lambda d: (d['count'], d['max_sol']))

    # Report
    print(f"Tested {n_tested} combinations.")
    print(f"Found {len(discoveries)} nontrivial identities (filtered {trivial_count} trivial {{1}}-only).\n")

    if not discoveries:
        print("No identities found.")
        return

    # Markdown table
    print("## Discovered Identities\n")
    print("| # | Identity | Solutions | Count | Max | Finite? |")
    print("|---|----------|----------|-------|-----|---------|")
    for idx, d in enumerate(discoveries[:80], 1):
        sols_str = ', '.join(str(s) for s in d['solutions'][:10])
        if len(d['solutions']) > 10:
            sols_str += '...'
        finite = 'YES' if d['likely_finite'] else 'no'
        print(f"| {idx} | `{d['label']}` | {{{sols_str}}} | {d['count']} | {d['max_sol']} | {finite} |")

    # Highlight the most interesting (finite with few solutions)
    finite_discoveries = [d for d in discoveries if d['likely_finite'] and d['count'] <= 20]
    if finite_discoveries:
        print(f"\n## Most Interesting (likely finite, <=20 solutions)\n")
        for d in finite_discoveries:
            sols_str = ', '.join(str(s) for s in d['solutions'])
            print(f"  {d['label']:30s}  -->  {{{sols_str}}}")

    return discoveries


def mode_verify(identity_str, N):
    """Verify a specific identity up to N."""
    lhs_func, rhs_func, lhs_label, rhs_label = parse_identity(identity_str)
    label = f"{lhs_label} = {rhs_label}"
    print(f"Verifying: {label} for n = 1..{N}\n")

    solutions = find_solutions(lhs_func, rhs_func, N)
    is_finite, density = estimate_finiteness(solutions, N)

    print(f"Solutions found: {len(solutions)}")
    if solutions:
        print(f"Solution set: {{{', '.join(str(s) for s in solutions)}}}")
    print(f"Likely finite: {'YES' if is_finite else 'NO'}")
    print(f"Density: {density:.2e}")
    print()

    # Solution details table
    print(format_solutions(solutions, lhs_func, rhs_func, lhs_label, rhs_label))
    print()

    # Ratio R(n) = LHS/RHS for non-solutions near solutions
    if solutions:
        print("## Ratio LHS/RHS near solutions\n")
        check_range = set()
        for s in solutions[:5]:
            for delta in range(-2, 8):
                n = s + delta
                if n >= 1:
                    check_range.add(n)
        check_range = sorted(check_range)[:40]
        print("| n | LHS/RHS | decimal |")
        print("|---|---------|---------|")
        for n in check_range:
            lv = lhs_func(n)
            rv = rhs_func(n)
            if rv and rv != 0:
                r = Fraction(lv, rv)
                marker = ' <-- SOLUTION' if n in solutions else ''
                print(f"| {n} | {r} | {float(r):.6f}{marker} |")

    # Local factors
    print("\n## Local Factors f(p,a) = LHS(p^a)/RHS(p^a)\n")
    local_factors = compute_local_factors(lhs_func, rhs_func, prime_range=50)
    print(format_factor_table(local_factors))
    print(format_ascii_factor_profile(local_factors))

    return solutions, local_factors


def mode_cancellation(identity_str):
    """Find cancellation structure for an identity."""
    lhs_func, rhs_func, lhs_label, rhs_label = parse_identity(identity_str)
    label = f"{lhs_label} = {rhs_label}"
    print(f"Cancellation analysis: {label}\n")

    local_factors = compute_local_factors(lhs_func, rhs_func, prime_range=200, max_exp=6)

    sub_unity, super_unity, cancellations = find_cancellation_prime(local_factors)

    print("## Sub-unity factors (f(p,1) < 1):\n")
    if sub_unity:
        for p, f in sub_unity:
            print(f"  p={p}: f(p,1) = {f} = {float(f):.6f}")
    else:
        print("  (none)")

    print("\n## Super-unity factors (f(p,1) > 1):\n")
    if super_unity:
        for p, f in super_unity[:20]:
            print(f"  p={p}: f(p,1) = {f} = {float(f):.6f}")
        if len(super_unity) > 20:
            print(f"  ... and {len(super_unity) - 20} more")
    else:
        print("  (none)")

    print("\n## Cancellation pairs (f(p1,1) * f(p2,1) = 1):\n")
    if cancellations:
        for p1, p2, f1, f2 in cancellations:
            print(f"  p={p1} x p={p2}: {f1} x {f2} = {f1 * f2}")
    else:
        print("  (none found)")

    # Check product of all f(p,1) for solution factorizations
    print("\n## Factor product check at solutions:\n")
    solutions = find_solutions(lhs_func, rhs_func, 10000)
    if solutions:
        for n in solutions:
            facts = factorize(n)
            if not facts:
                print(f"  n={n}: trivial (n=1)")
                continue
            product = Fraction(1)
            parts = []
            for p, a in sorted(facts.items()):
                if p in local_factors and a in local_factors[p]:
                    f = local_factors[p][a]
                    product *= f
                    parts.append(f"f({p},{a})={f}")
                else:
                    parts.append(f"f({p},{a})=?")
            print(f"  n={n} = {'*'.join(f'{p}^{a}' for p,a in sorted(facts.items()))}")
            print(f"    factors: {' * '.join(parts)} = {product} = {float(product):.6f}")
    else:
        print("  No solutions found up to 10000.")

    # ASCII visualization
    print(format_ascii_factor_profile(local_factors, max_primes=30))


def mode_local_factors(identity_str, prime_range=50):
    """Compute and display local factors."""
    lhs_func, rhs_func, lhs_label, rhs_label = parse_identity(identity_str)
    label = f"{lhs_label} = {rhs_label}"
    print(f"Local factors for: {label}\n")

    local_factors = compute_local_factors(lhs_func, rhs_func, prime_range=prime_range)

    print(format_factor_table(local_factors, max_primes=40, max_exp=5))
    print(format_ascii_factor_profile(local_factors, max_primes=40))

    # Analysis
    print("\n## Factor analysis:\n")
    for p in sorted(local_factors.keys())[:40]:
        exps = local_factors[p]
        if 1 not in exps:
            continue
        f1 = exps[1]
        # Check if f(p,a) = f(p,1)^a (completely multiplicative)
        is_mult = True
        for a in range(2, 5):
            if a in exps:
                expected = f1**a
                if exps[a] != expected:
                    is_mult = False
                    break
        mult_str = "multiplicative" if is_mult else "NOT multiplicative"
        # Closed form attempt
        if f1 == Fraction(1):
            form = "= 1 (trivial)"
        elif f1.denominator == 1:
            form = f"= {f1.numerator}"
        else:
            form = f"= {f1.numerator}/{f1.denominator}"

        status = ""
        if f1 < 1:
            status = " ** SUB-UNITY **"
        print(f"  p={p:>3}: f(p,1) {form:>12s}  [{mult_str}]{status}")


def mode_generalize(q):
    """Given a cancellation prime q, find which identities it appears in."""
    print(f"Searching identities where p={q} is a cancellation prime...\n")

    func_names = SCAN_FUNCS
    N = 10000  # verification range

    # Precompute
    cache = {}
    for name in func_names:
        f = FUNC_MAP[name]
        vals = {}
        # We only need prime powers
        for p in sieve(50):
            for a in range(1, 6):
                pa = p**a
                if pa <= 10**8:
                    vals[pa] = f(pa)
        cache[name] = vals

    pairs = []
    for i, a in enumerate(func_names):
        for b in func_names[i:]:
            pairs.append((a, b))

    matches = []
    for i, (a, b) in enumerate(pairs):
        for j, (c, d) in enumerate(pairs):
            if (a, b) == (c, d):
                continue
            if j < i:
                continue

            # Check f(q, 1) for this identity
            lhs_q = cache[a].get(q, None)
            rhs_q = cache[c].get(q, None)
            lhs_q2 = cache[b].get(q, None)
            rhs_q2 = cache[d].get(q, None)

            if any(v is None for v in [lhs_q, rhs_q, lhs_q2, rhs_q2]):
                continue

            lhs_val = lhs_q * lhs_q2
            rhs_val = rhs_q * rhs_q2

            if rhs_val == 0:
                continue

            f_q = Fraction(lhs_val, rhs_val)

            # Check if q participates in cancellation
            # Need f(2,1) and see if f(2,1)*f(q,1) == 1
            lhs_2 = cache[a].get(2, 1) * cache[b].get(2, 1)
            rhs_2 = cache[c].get(2, 1) * cache[d].get(2, 1)
            if rhs_2 == 0:
                continue
            f_2 = Fraction(lhs_2, rhs_2)

            if f_2 * f_q == 1 and f_2 != 1:
                label = f"{a}*{b}={c}*{d}"
                matches.append({
                    'label': label,
                    'f_2': f_2,
                    'f_q': f_q,
                })

    if matches:
        print(f"## Identities where f(2,1)*f({q},1) = 1:\n")
        print(f"| Identity | f(2,1) | f({q},1) | Product |")
        print(f"|----------|--------|----------|---------|")
        for m in matches:
            prod = m['f_2'] * m['f_q']
            print(f"| `{m['label']}` | {m['f_2']} ({float(m['f_2']):.4f}) | {m['f_q']} ({float(m['f_q']):.4f}) | {prod} |")
    else:
        print(f"No identities found where p={q} is a cancellation prime for f(2,1).")

    # Also check: for which identities is f(q,1) < 1?
    sub_q = []
    for i, (a, b) in enumerate(pairs):
        for j, (c, d) in enumerate(pairs):
            if (a, b) == (c, d):
                continue
            if j < i:
                continue

            lhs_q = cache[a].get(q, None)
            rhs_q = cache[c].get(q, None)
            lhs_q2 = cache[b].get(q, None)
            rhs_q2 = cache[d].get(q, None)
            if any(v is None for v in [lhs_q, rhs_q, lhs_q2, rhs_q2]):
                continue
            lhs_val = lhs_q * lhs_q2
            rhs_val = rhs_q * rhs_q2
            if rhs_val == 0:
                continue
            f_q = Fraction(lhs_val, rhs_val)
            if f_q < 1:
                label = f"{a}*{b}={c}*{d}"
                sub_q.append((label, f_q))

    if sub_q:
        print(f"\n## Identities where f({q},1) < 1 (sub-unity at p={q}):\n")
        for label, f in sub_q:
            print(f"  {label:30s}  f({q},1) = {f} = {float(f):.6f}")

    return matches


# ─────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Arithmetic identity auto-discovery tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --scan 10000
  %(prog)s --scan 10000 --extended
  %(prog)s --verify "sigma*phi=n*tau" 100000
  %(prog)s --cancellation "sigma*phi=n*tau"
  %(prog)s --local-factors "sigma*phi=n*tau" --prime-range 100
  %(prog)s --generalize 5

Functions: sigma, tau, phi, n (identity), id (constant 1),
           lambda/lam, omega/w, Omega/W, mu, sigma2, sigma3
        """)

    parser.add_argument('--scan', type=int, metavar='RANGE',
                        help='Scan all f1*f2=f3*f4 identities up to RANGE')
    parser.add_argument('--extended', action='store_true',
                        help='Use extended function set in scan mode')
    parser.add_argument('--verify', nargs=2, metavar=('EXPR', 'N'),
                        help='Verify identity EXPR up to N (e.g., "sigma*phi=n*tau" 100000)')
    parser.add_argument('--cancellation', type=str, metavar='EXPR',
                        help='Find cancellation prime for identity')
    parser.add_argument('--local-factors', type=str, metavar='EXPR',
                        help='Compute local factors f(p,a)')
    parser.add_argument('--prime-range', type=int, default=50,
                        help='Prime range for local factor computation (default: 50)')
    parser.add_argument('--generalize', type=int, metavar='PRIME',
                        help='Find identities where PRIME is cancellation prime')

    args = parser.parse_args()

    if args.scan:
        mode_scan(args.scan, extended=args.extended)
    elif args.verify:
        expr, n_str = args.verify
        mode_verify(expr, int(n_str))
    elif args.cancellation:
        mode_cancellation(args.cancellation)
    elif args.local_factors:
        mode_local_factors(args.local_factors, prime_range=args.prime_range)
    elif args.generalize:
        mode_generalize(args.generalize)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
