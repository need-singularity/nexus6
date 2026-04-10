#!/usr/bin/env python3
"""
Systematic search for arithmetic identities uniquely satisfied by n=6.

Explores combinations of standard number-theoretic functions:
  tau(n)    — number of divisors
  sigma(n)  — sum of divisors
  phi(n)    — Euler's totient
  omega(n)  — number of distinct prime factors
  Omega(n)  — number of prime factors with multiplicity
  mu(n)     — Mobius function
  rad(n)    — radical (product of distinct prime factors)

Searches for f(n) = g(n) where f,g are simple expressions in n and the above,
and n=6 is the UNIQUE solution (or one of very few).

Also proves n-2 = tau(n) has n=6 as unique solution via analytic bound.
"""

import math
from collections import defaultdict
from sympy import factorint, totient, divisor_count, divisor_sigma, mobius, isprime
from sympy import sqrt as sym_sqrt


# ──────────────────────────────────────────────────
#  Arithmetic functions
# ──────────────────────────────────────────────────

def tau(n):
    """Number of divisors."""
    return divisor_count(n)

def sigma(n):
    """Sum of divisors."""
    return divisor_sigma(n)

def sigma_minus1(n):
    """Sum of reciprocals of divisors = sigma(n)/n."""
    return divisor_sigma(n, -1)

def phi(n):
    """Euler's totient."""
    return totient(n)

def omega(n):
    """Number of distinct prime factors."""
    return len(factorint(n))

def big_omega(n):
    """Number of prime factors with multiplicity."""
    return sum(factorint(n).values())

def mu(n):
    """Mobius function."""
    return mobius(n)

def rad(n):
    """Radical = product of distinct prime factors."""
    result = 1
    for p in factorint(n):
        result *= p
    return result

def factorial(n):
    """n!"""
    return math.factorial(n)


# ──────────────────────────────────────────────────
#  1. PROOF: n-2 = tau(n) uniqueness
# ──────────────────────────────────────────────────

def prove_n_minus_2_equals_tau():
    """
    Prove n=6 is the unique solution of n - 2 = tau(n) for n >= 1.

    Analytic bound: tau(n) <= 2*sqrt(n) for all n >= 1.
    If n - 2 = tau(n), then n - 2 <= 2*sqrt(n).
    Let x = sqrt(n): x^2 - 2*x - 2 <= 0 => x <= 1 + sqrt(3) ~ 2.732
    So n <= (1+sqrt(3))^2 = 4 + 2*sqrt(3) ~ 7.46
    Thus n <= 7. Check n=1..7 exhaustively.
    """
    print("=" * 70)
    print("  PROOF: n - 2 = tau(n) has unique solution n = 6")
    print("=" * 70)
    print()
    print("Analytic bound:")
    print("  tau(n) <= 2*sqrt(n) for all n >= 1  [classical]")
    print("  If n - 2 = tau(n), then n - 2 <= 2*sqrt(n)")
    print("  => n - 2*sqrt(n) - 2 <= 0")
    bound = 1 + math.sqrt(3)
    print(f"  => sqrt(n) <= 1 + sqrt(3) = {bound:.6f}")
    print(f"  => n <= (1+sqrt(3))^2 = 4 + 2*sqrt(3) = {bound**2:.6f}")
    print(f"  => n <= 7")
    print()
    print("Exhaustive check n = 1 .. 7:")
    print(f"  {'n':>3}  {'n-2':>5}  {'tau(n)':>6}  {'Match':>6}")
    print(f"  {'---':>3}  {'---':>5}  {'---':>6}  {'---':>6}")

    solutions = []
    for n in range(1, 8):
        t = int(tau(n))
        match = (n - 2 == t)
        if match:
            solutions.append(n)
        print(f"  {n:>3}  {n-2:>5}  {t:>6}  {'YES' if match else 'no':>6}")

    print()
    print(f"  Solutions: {solutions}")
    print(f"  n = 6 is the UNIQUE solution.  QED")
    print()

    # Also verify exhaustively up to 1000 (belt and suspenders)
    print("Exhaustive verification up to n = 10,000:")
    all_solutions = []
    for n in range(1, 10001):
        if n - 2 == int(tau(n)):
            all_solutions.append(n)
    print(f"  Solutions in [1, 10000]: {all_solutions}")
    print()

    return solutions


# ──────────────────────────────────────────────────
#  2. Cayley's formula consequence
# ──────────────────────────────────────────────────

def cayley_consequence():
    """
    T(K_n) = n^{n-2} spanning trees of complete graph.
    At n=6: n-2 = tau(n) = 4, so T(K_6) = 6^{tau(6)} = 6^4 = 1296.
    K_6 is the ONLY complete graph where T(K_n) = n^{tau(n)}.
    """
    print("=" * 70)
    print("  CAYLEY'S FORMULA CONSEQUENCE")
    print("=" * 70)
    print()
    print("  Cayley: T(K_n) = n^{n-2}  (spanning trees of complete graph)")
    print("  If n-2 = tau(n), then T(K_n) = n^{tau(n)}")
    print()
    print(f"  At n=6: T(K_6) = 6^4 = {6**4}")
    print(f"  tau(6) = {int(tau(6))}, so 6^{{tau(6)}} = 6^4 = {6**int(tau(6))}")
    print()
    print("  Since n=6 is the unique solution of n-2=tau(n),")
    print("  K_6 is the ONLY complete graph where")
    print("  (spanning tree count) = n^(divisor count)")
    print()

    # Show how far off other n are
    print(f"  {'n':>3}  {'n^(n-2)':>12}  {'n^tau(n)':>12}  {'Match':>6}")
    print(f"  {'---':>3}  {'---':>12}  {'---':>12}  {'---':>6}")
    for n in range(2, 13):
        cayley = n ** (n - 2)
        t = int(tau(n))
        n_tau = n ** t
        match = (cayley == n_tau)
        print(f"  {n:>3}  {cayley:>12}  {n_tau:>12}  {'YES' if match else 'no':>6}")
    print()


# ──────────────────────────────────────────────────
#  3. Genus of K_n
# ──────────────────────────────────────────────────

def genus_analysis():
    """
    gamma(K_n) = ceil((n-3)(n-4)/12) for n >= 3
    At n=6: (3)(2)/12 = 6/12 = 1/2 exactly, ceil = 1
    K_6 is the unique K_n where (n-3)(n-4)/12 = 1/2 exactly.
    """
    print("=" * 70)
    print("  GENUS OF K_n: THE 1/2 THAT APPEARS")
    print("=" * 70)
    print()
    print("  Ringel-Youngs: gamma(K_n) = ceil((n-3)(n-4)/12) for n >= 3")
    print()
    print(f"  {'n':>3}  {'(n-3)(n-4)/12':>16}  {'genus':>6}  {'Frac part':>10}")
    print(f"  {'---':>3}  {'---':>16}  {'---':>6}  {'---':>10}")

    half_solutions = []
    for n in range(3, 20):
        numer = (n - 3) * (n - 4)
        exact = numer / 12
        genus = math.ceil(exact)
        frac = exact - int(exact)
        marker = ""
        if abs(frac - 0.5) < 1e-10:
            marker = " <-- 1/2!"
            half_solutions.append(n)
        print(f"  {n:>3}  {exact:>16.4f}  {genus:>6}  {frac:>10.4f}{marker}")

    print()
    print(f"  Values of n where fractional part = 1/2: {half_solutions}")
    print()
    # Solve (n-3)(n-4) mod 12 = 6
    # (n-3)(n-4) = n^2 - 7n + 12
    # Need n^2 - 7n + 12 = 6 mod 12 => n^2 - 7n + 6 = 0 mod 12
    # => (n-1)(n-6) = 0 mod 12
    # Solutions: n=1 mod 12 or n=6 mod 12 (but also other residues)
    print("  Algebraic analysis: (n-3)(n-4)/12 has fractional part 1/2")
    print("  iff (n-3)(n-4) = 6 mod 12")
    print()
    print("  Checking residues mod 12:")
    residue_solutions = []
    for r in range(12):
        val = (r - 3) * (r - 4) % 12
        if val == 6:
            residue_solutions.append(r)
    print(f"  n mod 12 in {residue_solutions} gives frac = 1/2")
    print()
    print("  So n=6 is the SMALLEST n >= 3 where frac = 1/2,")
    print("  but n=10 also has frac = 1/2 (genus formula gives 7/2).")
    print("  The 1/2 connection is suggestive but NOT unique to n=6.")
    print()


# ──────────────────────────────────────────────────
#  4. Independence from perfectness
# ──────────────────────────────────────────────────

def independence_check():
    """Check that n-2=tau(n) is independent of being perfect."""
    print("=" * 70)
    print("  INDEPENDENCE FROM PERFECTNESS")
    print("=" * 70)
    print()

    perfects = [6, 28, 496, 8128]
    print("  Perfect numbers and their tau values:")
    print(f"  {'n':>6}  {'n-2':>6}  {'tau(n)':>6}  {'n-2=tau?':>8}  {'sigma=2n?':>9}")
    print(f"  {'---':>6}  {'---':>6}  {'---':>6}  {'---':>8}  {'---':>9}")
    for n in perfects:
        t = int(tau(n))
        sig = int(sigma(n))
        print(f"  {n:>6}  {n-2:>6}  {t:>6}  {'YES' if n-2==t else 'no':>8}  {'YES' if sig==2*n else 'no':>9}")

    print()
    print("  n=28: 28-2=26, tau(28)=6. NOT equal.")
    print("  n=496: 496-2=494, tau(496)=10. NOT equal.")
    print()
    print("  => n-2=tau(n) does NOT follow from perfectness.")
    print("  => Perfectness does NOT follow from n-2=tau(n).")
    print("  => These are INDEPENDENT characterizations.")
    print("  => n=6 sits at their INTERSECTION.")
    print()


# ──────────────────────────────────────────────────
#  5. Systematic search for equations uniquely satisfied by n=6
# ──────────────────────────────────────────────────

def systematic_search(N=200):
    """
    Search for f(n) = g(n) identities where n=6 is the unique solution in [2, N].

    We build a library of "terms" (simple expressions in n and arithmetic functions),
    then check all pairs (f, g) for how many n in [2, N] satisfy f(n) = g(n).
    Report those where the ONLY solution is n=6.
    """
    print("=" * 70)
    print(f"  SYSTEMATIC SEARCH: Equations uniquely satisfied by n=6  [2..{N}]")
    print("=" * 70)
    print()

    # Precompute arithmetic functions for n in [2, N]
    print("  Precomputing arithmetic functions...")
    data = {}
    for n in range(2, N + 1):
        data[n] = {
            'n': n,
            'tau': int(tau(n)),
            'sigma': int(sigma(n)),
            'phi': int(phi(n)),
            'omega': omega(n),
            'Omega': big_omega(n),
            'mu': int(mu(n)),
            'rad': rad(n),
        }
    print("  Done.")
    print()

    # Build term library: each term is (name, function)
    # We use lambdas over the precomputed data
    terms = []

    # Basic
    terms.append(("n", lambda d: d['n']))
    terms.append(("n-1", lambda d: d['n'] - 1))
    terms.append(("n-2", lambda d: d['n'] - 2))
    terms.append(("n+1", lambda d: d['n'] + 1))
    terms.append(("n+2", lambda d: d['n'] + 2))
    terms.append(("2n", lambda d: 2 * d['n']))
    terms.append(("3n", lambda d: 3 * d['n']))
    terms.append(("n^2", lambda d: d['n'] ** 2))
    terms.append(("n/2", lambda d: d['n'] / 2))
    terms.append(("n/3", lambda d: d['n'] / 3))

    # Arithmetic functions
    for fname in ['tau', 'sigma', 'phi', 'omega', 'Omega', 'rad']:
        terms.append((fname, lambda d, f=fname: d[f]))
        terms.append((f"{fname}+1", lambda d, f=fname: d[f] + 1))
        terms.append((f"{fname}-1", lambda d, f=fname: d[f] - 1))
        terms.append((f"{fname}*2", lambda d, f=fname: d[f] * 2))
        terms.append((f"{fname}^2", lambda d, f=fname: d[f] ** 2))
        if fname not in ('omega', 'Omega'):
            terms.append((f"n/{fname}", lambda d, f=fname: d['n'] / d[f] if d[f] != 0 else None))
            terms.append((f"{fname}/n", lambda d, f=fname: d[f] / d['n']))

    # Cross-function products/ratios
    pairs = [('tau', 'phi'), ('tau', 'omega'), ('sigma', 'phi'),
             ('sigma', 'tau'), ('phi', 'omega'), ('phi', 'rad')]
    for f1, f2 in pairs:
        terms.append((f"{f1}*{f2}", lambda d, a=f1, b=f2: d[a] * d[b]))
        terms.append((f"{f1}+{f2}", lambda d, a=f1, b=f2: d[a] + d[b]))
        if f2 not in ('omega', 'Omega'):
            terms.append((f"{f1}/{f2}", lambda d, a=f1, b=f2: d[a] / d[b] if d[b] != 0 else None))

    # Special combinations
    terms.append(("sigma/n", lambda d: d['sigma'] / d['n']))
    terms.append(("n/phi", lambda d: d['n'] / d['phi'] if d['phi'] != 0 else None))
    terms.append(("tau!", lambda d: math.factorial(d['tau']) if d['tau'] <= 20 else None))
    terms.append(("tau!/(tau-1)!", lambda d: d['tau']))  # = tau itself
    terms.append(("sigma-n", lambda d: d['sigma'] - d['n']))  # = sum of proper divisors
    terms.append(("(sigma-n)/n", lambda d: (d['sigma'] - d['n']) / d['n']))
    terms.append(("tau*phi/n", lambda d: d['tau'] * d['phi'] / d['n']))
    terms.append(("n*omega", lambda d: d['n'] * d['omega']))
    terms.append(("phi+tau", lambda d: d['phi'] + d['tau']))
    terms.append(("phi*tau", lambda d: d['phi'] * d['tau']))
    terms.append(("sigma-phi", lambda d: d['sigma'] - d['phi']))
    terms.append(("n-phi", lambda d: d['n'] - d['phi']))
    terms.append(("sigma/phi", lambda d: d['sigma'] / d['phi'] if d['phi'] != 0 else None))
    terms.append(("n+tau", lambda d: d['n'] + d['tau']))
    terms.append(("n*tau", lambda d: d['n'] * d['tau']))
    terms.append(("n-tau", lambda d: d['n'] - d['tau']))
    terms.append(("sigma-tau", lambda d: d['sigma'] - d['tau']))
    terms.append(("rad*omega", lambda d: d['rad'] * d['omega']))
    terms.append(("n-rad", lambda d: d['n'] - d['rad']))

    # Constants
    for c in [1, 2, 3, 4, 5, 6, 8, 10, 12]:
        terms.append((str(c), lambda d, v=c: v))

    print(f"  Term library: {len(terms)} terms")
    print(f"  Checking {len(terms) * (len(terms) - 1) // 2} pairs...")
    print()

    # Evaluate all terms for all n
    term_values = {}
    for name, func in terms:
        vals = {}
        for n in range(2, N + 1):
            try:
                v = func(data[n])
                if v is not None and not (isinstance(v, float) and (math.isinf(v) or math.isnan(v))):
                    vals[n] = v
            except:
                pass
        term_values[name] = vals

    # Find pairs where n=6 is the unique solution
    unique_6 = []
    few_solutions = []  # n=6 plus at most 2 others

    term_names = [name for name, _ in terms]

    for i in range(len(term_names)):
        for j in range(i + 1, len(term_names)):
            f_name = term_names[i]
            g_name = term_names[j]
            f_vals = term_values[f_name]
            g_vals = term_values[g_name]

            solutions = []
            for n in range(2, N + 1):
                if n in f_vals and n in g_vals:
                    fv = f_vals[n]
                    gv = g_vals[n]
                    # Use approximate equality for floats
                    if isinstance(fv, float) or isinstance(gv, float):
                        if abs(float(fv) - float(gv)) < 1e-10:
                            solutions.append(n)
                    else:
                        if fv == gv:
                            solutions.append(n)

            if 6 in solutions:
                if len(solutions) == 1:
                    unique_6.append((f_name, g_name, solutions))
                elif len(solutions) <= 3:
                    few_solutions.append((f_name, g_name, solutions))

    # Filter out trivially equivalent or tautological equations
    # (e.g., "tau" == "tau!/(tau-1)!" which is always true)
    def is_trivial(f, g):
        trivial_pairs = {
            frozenset({"tau", "tau!/(tau-1)!"}),
        }
        return frozenset({f, g}) in trivial_pairs

    unique_6 = [(f, g, s) for f, g, s in unique_6 if not is_trivial(f, g)]
    few_solutions = [(f, g, s) for f, g, s in few_solutions if not is_trivial(f, g)]

    # Sort by "interest" — prefer those involving different function families
    def interest_score(f, g):
        score = 0
        funcs = ['tau', 'sigma', 'phi', 'omega', 'Omega', 'rad']
        f_funcs = set(fn for fn in funcs if fn in f)
        g_funcs = set(fn for fn in funcs if fn in g)
        if f_funcs != g_funcs:
            score += 2
        if 'n' in f or 'n' in g:
            score += 1
        return score

    unique_6.sort(key=lambda x: -interest_score(x[0], x[1]))

    print(f"  EQUATIONS WITH UNIQUE SOLUTION n=6 ({len(unique_6)} found):")
    print(f"  {'LHS':>25} = {'RHS':<25}  Solutions")
    print(f"  {'-'*25}   {'-'*25}  {'-'*15}")
    for f_name, g_name, sols in unique_6:
        print(f"  {f_name:>25} = {g_name:<25}  {sols}")

    print()
    print(f"  EQUATIONS WITH n=6 + FEW OTHERS ({len(few_solutions)} found):")
    print(f"  {'LHS':>25} = {'RHS':<25}  Solutions")
    print(f"  {'-'*25}   {'-'*25}  {'-'*15}")
    for f_name, g_name, sols in few_solutions[:50]:  # cap output
        print(f"  {f_name:>25} = {g_name:<25}  {sols}")

    print()
    return unique_6, few_solutions


# ──────────────────────────────────────────────────
#  6. Sigma/n = phi check
# ──────────────────────────────────────────────────

def sigma_over_n_equals_phi():
    """Check: sigma(n)/n = phi(n). At n=6: 12/6=2=phi(6)."""
    print("=" * 70)
    print("  CHECK: sigma(n)/n = phi(n)")
    print("=" * 70)
    print()
    solutions = []
    for n in range(2, 1001):
        s = int(sigma(n))
        p = int(phi(n))
        if s == n * p:
            solutions.append(n)
    print(f"  sigma(n)/n = phi(n) solutions in [2,1000]: {solutions}")
    if 6 in solutions:
        if len(solutions) == 1:
            print("  => UNIQUE to n=6!")
        else:
            print(f"  => Also holds for {[x for x in solutions if x != 6]}")
    print()


# ──────────────────────────────────────────────────
#  7. Summary and ASCII visualization
# ──────────────────────────────────────────────────

def summary_visualization():
    """Visual summary of n=6 properties."""
    print("=" * 70)
    print("  n=6 PROPERTY LANDSCAPE")
    print("=" * 70)
    print()
    print("  Property                    Unique to 6?   Also holds for")
    print("  " + "-" * 65)
    print("  n-2 = tau(n)                YES             (none)")
    print("  sigma(n) = 2n (perfect)     no              28, 496, 8128, ...")
    print("  sigma_{-1}(n) = 2           no              28, 496, 8128, ...")
    print("  n = 1+2+3 (triangular)      no              1, 3, 10, 15, ...")
    print("  n = 2*3 (primorial)         no              2, 30, 210, ...")
    print("  n = 3! (factorial)          no              1, 2, 24, 120, ...")
    print("  genus(K_n) frac = 1/2       no              10, 18, 22, ...")
    print()
    print("  ASCII: How tau(n) compares to n-2")
    print()
    print("  tau(n)")
    print("   12 |")
    print("   10 |                              *  ")
    print("    8 |                  *         *     ")
    print("    6 |           *  *     *  *         *")
    print("    4 |     *  *  *  *  *  *  *  *  *  *")
    print("    3 |  *                               ")
    print("    2 |  *  *  *  *  *  *  *  *  *  *  *")
    print("    1 |  *                               ")
    print("    0 +--+--+--+--+--+--+--+--+--+--+--+-> n")
    print("       2  3  4  5  6  7  8  9 10 11 12")
    print()
    print("  n-2:")
    print("    0  1  2  3  4  5  6  7  8  9 10")
    print()
    print("  The line n-2 rockets upward while tau(n) grows ~ O(n^eps).")
    print("  They cross exactly once, at n=6: 4 = 4.")
    print()

    # Detailed ASCII graph
    print("  Detailed comparison (n=2..30):")
    print()
    max_val = 30
    for n in range(2, 31):
        t = int(tau(n))
        nm2 = n - 2
        bar_t = "*" * min(t, 50)
        bar_n = "#" * min(nm2, 50)
        marker = " <-- MATCH!" if t == nm2 else ""
        print(f"  n={n:>2}  tau={t:>2} {bar_t}")
        print(f"        n-2={nm2:>2} {bar_n}{marker}")
    print()


# ──────────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────────

if __name__ == "__main__":
    print()
    print("*" * 70)
    print("*  DEEP INVESTIGATION: n-2 = tau(n) and uniqueness of n=6        *")
    print("*" * 70)
    print()

    # 1. Proof of uniqueness
    prove_n_minus_2_equals_tau()

    # 2. Cayley's formula consequence
    cayley_consequence()

    # 3. Genus analysis
    genus_analysis()

    # 4. Independence from perfectness
    independence_check()

    # 5. sigma(n)/n = phi(n) check
    sigma_over_n_equals_phi()

    # 6. Systematic search
    unique_eqs, few_eqs = systematic_search(N=200)

    # 7. Summary
    summary_visualization()

    # Final count
    print("=" * 70)
    print(f"  FINAL TALLY")
    print("=" * 70)
    print(f"  Equations uniquely satisfied by n=6 in [2,200]: {len(unique_eqs)}")
    print(f"  Equations with n=6 + few others:                {len(few_eqs)}")
    print()
    print("  The identity n-2 = tau(n) is a CLEAN, INDEPENDENT")
    print("  characterization of 6 among all positive integers.")
    print("  Combined with perfectness (sigma=2n), n=6 sits at a")
    print("  unique intersection of number-theoretic properties.")
    print()
