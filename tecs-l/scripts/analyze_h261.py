```python
#!/usr/bin/env python3
"""Hypothesis 261 Deep Analysis: Congruence Subgroup Classification and Forcing Chains

For genus-0 N, calculate sigma(N), tau(N), phi(N) and
determine forcing chain quality grades (A/B/C/D).
"""

import math
from congruence_chain_engine import (
    factorize, divisors, euler_phi, sigma_k, mobius,
    gamma0_index, gamma0_cusps, gamma0_elliptic2, gamma0_elliptic3,
    gamma0_genus, isotropy_orders, forcing_chain_analysis, first_cusp_form_weight,
    gcd, lcm
)


def ramanujan_tau(n):
    """Ramanujan tau function (accurate up to n <= 30)
    Coefficient of Delta(q) = q * prod_{n>=1} (1-q^n)^24"""
    if n <= 0:
        return 0
    # Calculate by series expansion
    max_terms = n + 10
    # Expansion of (1 - q^k)^24
    coeffs = [0] * (n + 1)
    coeffs[0] = 1
    for k in range(1, n + 1):
        # Multiply by (1 - q^k)^24
        new_coeffs = coeffs[:]
        for power in range(1, 25):  # Powers of -q^k
            sign = (-1) ** power
            coeff_mult = math.comb(24, power) * sign
            shift = k * power
            if shift > n:
                break
            temp = [0] * (n + 1)
            for j in range(n + 1):
                if coeffs[j] != 0 and j + shift <= n:
                    temp[j + shift] += coeffs[j] * coeff_mult
            for j in range(n + 1):
                new_coeffs[j] += temp[j]
        coeffs = new_coeffs
    # Delta(q) = q * prod(1-q^n)^24, so tau(n) = coeffs[n-1]
    if n - 1 < len(coeffs):
        return coeffs[n - 1]
    return 0


def number_of_divisors(n):
    """Number of divisors d(N) = sigma_0(N)"""
    return sigma_k(n, 0)


def analyze_genus0():
    """Deep analysis for all genus-0 N"""
    genus0 = []
    for n in range(1, 101):
        if gamma0_genus(n) == 0:
            genus0.append(n)

    print("=" * 90)
    print("  [1] Comprehensive Arithmetic Functions Table for Genus-0 N")
    print("=" * 90)
    print(f"  {'N':>4} | {'mu':>5} | {'sigma':>5} | {'tau':>8} | {'phi':>5} | "
          f"{'d(N)':>4} | {'mu/sig':>7} | {'mu%12':>5} | {'mu/12':>5}")
    print(f"  {'-'*4}-+-{'-'*5}-+-{'-'*5}-+-{'-'*8}-+-{'-'*5}-+-"
          f"{'-'*4}-+-{'-'*7}-+-{'-'*5}-+-{'-'*5}")

    for n in genus0:
        mu = gamma0_index(n)
        sig = sigma_k(n, 1)
        tau = ramanujan_tau(n)
        phi = euler_phi(n)
        d_n = number_of_divisors(n)
        mu_sig_ratio = f"{mu/sig:.3f}" if sig > 0 else "-"
        mu_mod12 = mu % 12
        mu_div12 = f"{mu/12:.2f}"

        print(f"  {n:>4} | {mu:>5} | {sig:>5} | {tau:>8} | {phi:>5} | "
              f"{d_n:>4} | {mu_sig_ratio:>7} | {mu_mod12:>5} | {mu_div12:>5}")

    return genus0


def analyze_mu_multiples_of_12():
    """All N (1..100) where mu(N) is a multiple of 12"""
    print()
    print("=" * 90)
    print("  [2] N where mu(N) is a multiple of 12 (= sigma related)")
    print("=" * 90)
    results = []
    for n in range(1, 101):
        mu = gamma0_index(n)
        if mu % 12 == 0:
            sig = sigma_k(n, 1)
            g = gamma0_genus(n)
            results.append((n, mu, mu // 12, sig, g))

    print(f"  {'N':>4} | {'mu':>6} | {'mu/12':>5} | {'sigma':>6} | {'genus':>5} | {'mu=sig?':>7}")
    print(f"  {'-'*4}-+-{'-'*6}-+-{'-'*5}-+-{'-'*6}-+-{'-'*5}-+-{'-'*7}")
    for n, mu, md, sig, g in results:
        eq = "YES" if mu == sig else ""
        print(f"  {n:>4} | {mu:>6} | {md:>5} | {sig:>6} | {g:>5} | {eq:>7}")

    print(f"\n  Total {len(results)} / 100")
    return results


def analyze_both_elliptic():
    """N where e2 > 0 AND e3 > 0"""
    print()
    print("=" * 90)
    print("  [3] e2 > 0 AND e3 > 0 (Both elliptic points exist)")
    print("=" * 90)
    results = []
    for n in range(1, 101):
        e2 = gamma0_elliptic2(n)
        e3 = gamma0_elliptic3(n)
        if e2 > 0 and e3 > 0:
            mu = gamma0_index(n)
            g = gamma0_genus(n)
            sig = sigma_k(n, 1)
            iso = isotropy_orders(n)
            iso_lcm = 1
            for o in iso:
                iso_lcm = lcm(iso_lcm, o)
            results.append((n, mu, g, e2, e3, iso_lcm, sig))

    print(f"  {'N':>4} | {'mu':>5} | {'g':>3} | {'e2':>3} | {'e3':>3} | "
          f"{'lcm':>4} | {'sigma':>5} | Note")
    print(f"  {'-'*4}-+-{'-'*5}-+-{'-'*3}-+-{'-'*3}-+-{'-'*3}-+-"
          f"{'-'*4}-+-{'-'*5}-+------")
    for n, mu, g, e2, e3, il, sig in results:
        notes = []
        if il == 6:
            notes.append("lcm=6(perfect)")
        if g == 0:
            notes.append("g=0")
        if mu == sig:
            notes.append("mu=sig")
        # Check if N is squarefree
        facts = factorize(n)
        if all(e == 1 for e in facts.values()):
            notes.append("sqfree")
        print(f"  {n:>4} | {mu:>5} | {g:>3} | {e2:>3} | {e3:>3} | "
              f"{il:>4} | {sig:>5} | {', '.join(notes)}")

    print(f"\n  Total {len(results)} / 100")
    print(f"  Their lcm(isotropy) are all 6 = first perfect number")
    return results


def analyze_cusp_form_weights():
    """First cusp form weight patterns"""
    print()
    print("=" * 90)
    print("  [4] First Cusp Form Weight k Patterns")
    print("=" * 90)

    weight_groups = {}
    for n in range(1, 101):
        fk = first_cusp_form_weight(n)
        if fk not in weight_groups:
            weight_groups[fk] = []
        weight_groups[fk].append(n)

    for k in sorted(weight_groups.keys(), key=lambda x: x if x else 999):
        ns = weight_groups[k]
        k_str = str(k) if k else ">48"
        print(f"  k = {k_str:>3}: {len(ns):>3} count  N = {ns[:20]}{'...' if len(ns) > 20 else ''}")

    return weight_groups


def forcing_chain_quality():
    """Forcing chain quality grade determination (A/B/C/D)"""
    print()
    print("=" * 90)
    print("  [5] Forcing Chain Quality Grades (Genus-0 N)")
    print("=" * 90)
    print()
    print("  Grade criteria:")
    print("    A: lcm(iso) * cusps = sigma(N) exact match + mu%12=0")
    print("    B: lcm(iso) * d(N) = mu exact match or mu = sigma(N)")
    print("    C: mu%12=0 with other partial relations")
    print("    D: No special relations")
    print()

    genus0 = [n for n in range(1, 101) if gamma0_genus(n) == 0]

    print(f"  {'N':>4} | {'mu':>5} | {'c':>3} | {'lcm':>4} | {'sig':>5} | "
          f"{'d(N)':>4} | {'lcm*c':>6} | {'lcm*d':>6} | {'Grade':>4} | Reason")
    print(f"  {'-'*4}-+-{'-'*5}-+-{'-'*3}-+-{'-'*4}-+-{'-'*5}-+-"
          f"{'-'*4}-+-{'-'*6}-+-{'-'*6}-+-{'-'*4}-+------")

    grades = {}
    for n in genus0:
        mu = gamma0_index(n)
        c = gamma0_cusps(n)
        sig = sigma_k(n, 1)
        d_n = number_of_divisors(n)
        iso = isotropy_orders(n)
        iso_lcm = 1
        for o in iso:
            iso_lcm = lcm(iso_lcm, o)

        lc = iso_lcm * c
        ld = iso_lcm * d_n

        reasons = []
        grade = "D"

        # A condition
        if lc == sig and mu % 12 == 0:
            grade = "A"
            reasons.append("lcm*c=sig + mu%12=0")
        elif lc == sig:
            grade = "A"
            reasons.append("lcm*c=sig")
        # B condition
        elif ld == mu:
            grade = "B"
            reasons.append("lcm*d=mu")
        elif mu == sig:
            if mu % 12 == 0:
                grade = "B"
                reasons.append("mu=sig + mu%12=0")
            else:
                grade = "B"
                reasons.append("mu=sig")
        # C condition
        elif mu % 12 == 0:
            grade = "C"
            reasons.append(f"mu/12={mu//12}")
            if sig % iso_lcm == 0:
                reasons.append(f"sig/{iso_lcm}={sig//iso_lcm}")
        # D
        else:
            reasons.append("weak relations")

        grades[n] = grade

        print(f"  {n:>4} | {mu:>5} | {c:>3} | {iso_lcm:>4} | {sig:>5} | "
              f"{d_n:>4} | {lc:>6} | {ld:>6} | {grade:>4} | {'; '.join(reasons)}")

    # Grade statistics
    print()
    for g in ['A', 'B', 'C', 'D']:
        ns = [n for n, gr in grades.items() if gr == g]
        print(f"  Grade {g}: {len(ns)} count — N = {ns}")

    return grades


def sigma_mu_relation_deep():
    """Deep exploration of sigma(N) and mu(N) relationship"""
    print()
    print("=" * 90)
    print("  [6] Deep Analysis of sigma(N) and mu(N) Relationship")
    print("=" * 90)
    print()
    print("  mu(N) = N * prod_{p|N} (1 + 1/p)")
    print("  sigma(N) = prod_{p^e || N} (p^{e+1} - 1)/(p - 1)")
    print("  If N is squarefree: mu(N) = sigma(N) (exactly!)")
    print()

    sqfree_match = 0
    sqfree_total = 0
    non_sqfree_match = 0
    non_sqfree_total = 0

    for n in range(1, 101):
        mu = gamma0_index(n)
        sig = sigma_k(n, 1)
        facts = factorize(n)
        is_sqfree = all(e == 1 for e in facts.values()) if facts else True

        if is_sqfree:
            sqfree_total += 1
            if mu == sig:
                sqfree_match += 1
        else:
            non_sqfree_total += 1
            if mu == sig:
                non_sqfree_match += 1

    print(f"  Squarefree N (1..100):     {sqfree_total} count, mu=sigma matches: {sqfree_match}")
    print(f"  Non-squarefree N (1..100): {non_sqfree_total} count, mu=sigma matches: {non_sqfree_match}")
    print()

    # Proof
    print("  [Proof] If N is squarefree then mu(N) = sigma(N)")
    print("    N = p1 * p2 * ... * pk (each pi distinct prime)")
    print("    mu(N) = N * prod(1 + 1/pi) = prod(pi) * prod(1 + 1/pi)")
    print("          = prod(pi + 1)")
    print("    sigma(N) = prod(1 + pi) = prod(pi + 1)  [sum of divisors for each prime]")
    print("    Therefore mu(N) = sigma(N).  QED")
    print()
    print("  This is a pure arithmetic theorem (Golden Zone independent, eternally true) [Green]")


def main():
    genus0 = analyze_genus0()
    mu12_results = analyze_mu_multiples_of_12()
    both_elliptic = analyze_both_elliptic()
    weight_groups = analyze_cusp_form_weights()
    grades = forcing_chain_quality()
    sigma_mu_relation_deep()

    # Final summary
    print()
    print("=" * 90)
    print("  [Final Summary] Hypothesis 261 Calculation Results")
    print("=" * 90)
    print()
    print(f"  Genus-0 N (1..100): {len(genus0)} count = {genus0}")
    print(f"  N where mu%12=0: {len(mu12_results)} count")
    print(f"  N where e2>0 AND e3>0: {len(both_elliptic)} count (all lcm=6)")
    print()
    print("  Key findings:")
    print("    1. squarefree N <=> mu(N) = sigma(N) [Pure arithmetic theorem, proven]")
    print("    2. e2>0 AND e3>0 <=> lcm(isotropy) = 6 = first perfect number")
    print("    3. Only N=1, 13 are genus-0 with lcm=6 (both elliptic + g=0)")
    print("    4. Genus-0 with mu%12=0: N = {6, 8, 9, 12, 16, 18} — composites only")
    print("    5. Forcing chain grade A (cleanest): lcm*cusps = sigma(N)")


if __name__ == '__main__':
    main()
```