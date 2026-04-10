#!/usr/bin/env python3
"""
verify_36_extreme.py -- Extreme verification of all 36 "unique to n=6" equations
                        up to n = 10,000,000 (ten million).

Uses multiplicative sieve for all arithmetic functions (no per-number factorization).
Requires numpy for speed.

Usage:
  source n6-replication/.venv/bin/activate
  PYTHONPATH=. python3 verify/verify_36_extreme.py
"""

import time
import numpy as np
import sys

LIMIT = 10_000_000

# ══════════════════════════════════════════════════════════════════════
#  PART 1: Multiplicative Sieve for Arithmetic Functions
# ══════════════════════════════════════════════════════════════════════

def sieve_all(N):
    """
    Precompute arithmetic functions for n = 0..N using sieve approach.
    Returns dict of numpy arrays (int64 where possible).

    Functions computed:
      sigma[n]  - sum of divisors
      tau[n]    - number of divisors
      phi[n]    - Euler totient
      omega[n]  - number of distinct prime factors
      sopfr[n]  - sum of prime factors with multiplicity
      rad[n]    - radical (product of distinct prime factors)
    """
    print(f"  Sieving arithmetic functions for n up to {N:,} ...")
    t0 = time.time()

    # Step 1: Sieve of Eratosthenes for primes
    is_prime = np.ones(N + 1, dtype=np.bool_)
    is_prime[0] = False
    is_prime[1] = False
    p = 2
    while p * p <= N:
        if is_prime[p]:
            is_prime[p*p::p] = False
        p += 1
    primes = np.nonzero(is_prime)[0]
    print(f"    Prime sieve: {time.time()-t0:.1f}s  ({len(primes)} primes)")
    t1 = time.time()

    # Step 2: phi via Euler product sieve (iterate over primes)
    phi_arr = np.arange(N + 1, dtype=np.int64)
    for p in primes:
        p = int(p)
        phi_arr[p::p] = phi_arr[p::p] // p * (p - 1)
    print(f"    Phi sieve: {time.time()-t1:.1f}s")
    t2 = time.time()

    # Step 3: omega and rad via prime sieve
    omega_arr = np.zeros(N + 1, dtype=np.int32)
    rad_arr = np.ones(N + 1, dtype=np.int64)
    for p in primes:
        p = int(p)
        omega_arr[p::p] += 1
        rad_arr[p::p] *= p
    print(f"    Omega/rad sieve: {time.time()-t2:.1f}s")
    t3 = time.time()

    # Step 4: sopfr via prime power sieve
    sopfr_arr = np.zeros(N + 1, dtype=np.int64)
    for p in primes:
        p = int(p)
        pk = p
        while pk <= N:
            sopfr_arr[pk::pk] += p
            if pk > N // p:
                break
            pk *= p
    print(f"    Sopfr sieve: {time.time()-t3:.1f}s")
    t4 = time.time()

    # Step 5: sigma and tau via multiplicative sieve
    # For each prime p, process prime powers p^a from highest to lowest.
    # Numbers with v_p(n) = a get sigma *= (p^(a+1)-1)/(p-1), tau *= (a+1).
    sigma_arr = np.ones(N + 1, dtype=np.int64)
    tau_arr = np.ones(N + 1, dtype=np.int32)

    # We'll use a "mark from top" approach:
    # For each prime p, first find all exponents. Then process from
    # highest a downward. At each level p^a, the numbers that are
    # multiples of p^a but have NOT been processed at a higher level
    # have v_p(n) = a exactly.
    #
    # Implementation: use a boolean "processed" array per prime (too expensive).
    #
    # Better: process a from highest to lowest using a temporary array.
    # Actually simplest correct approach: for each n, use SPF to factorize.
    # But that's O(N * avg_factors).
    #
    # Fastest numpy approach: incremental multiplication.
    # For each prime p:
    #   sigma[p::p] *= (1 + p)          # assume v_p = 1
    #   sigma[p^2::p^2] *= (1+p+p^2)/(1+p)  # correct v_p >= 2
    #   sigma[p^3::p^3] *= (1+p+p^2+p^3)/(1+p+p^2)  # correct v_p >= 3
    #   ...
    # Each correction is an integer: sigma(p^a)/sigma(p^(a-1)) = p^a
    # Wait: sigma(p^a) = 1+p+...+p^a, sigma(p^{a-1}) = 1+p+...+p^{a-1}
    # Ratio = sigma(p^a)/sigma(p^{a-1}) is NOT generally integer.
    # But: sigma(p^a) = sigma(p^{a-1}) + p^a
    # So we can't do simple multiplication correction.
    #
    # Correct incremental approach for tau (simpler since tau(p^a) = a+1):
    #   tau[p::p] *= 2        (all multiples of p get factor 2)
    #   tau[p^2::p^2] *= 3/2  (NOT integer!)
    # So incremental doesn't work for tau either.
    #
    # SOLUTION: Use the divisor-sum sieve but in chunks to stay fast.
    # sigma[n] = sum_{d|n} d.  Equivalently: for d=1..N, sigma[d::d] += d.
    # tau[n] = #{d|n}. For d=1..N, tau[d::d] += 1.
    # This is O(N ln N) ~ 1.7e8 for N=10^7.
    # With numpy slice operations, each iteration is fast (C-level loop).

    sigma_arr = np.zeros(N + 1, dtype=np.int64)
    tau_arr = np.zeros(N + 1, dtype=np.int32)

    for d in range(1, N + 1):
        sigma_arr[d::d] += d
        tau_arr[d::d] += 1

    print(f"    Sigma/tau divisor sieve: {time.time()-t4:.1f}s")

    total = time.time() - t0
    print(f"  Total sieve time: {total:.1f}s")

    return {
        'sigma': sigma_arr,
        'tau':   tau_arr,
        'phi':   phi_arr,
        'omega': omega_arr,
        'sopfr': sopfr_arr,
        'rad':   rad_arr,
    }


# ══════════════════════════════════════════════════════════════════════
#  PART 2: The 36 Equations (vectorized with numpy)
# ══════════════════════════════════════════════════════════════════════

def check_all_equations(funcs, N):
    """
    Check all 36 equations for n = 2..N.
    Returns list of (eq_number, name, solutions_other_than_6, time_taken).
    """
    n = np.arange(N + 1, dtype=np.int64)
    s = funcs['sigma']
    t = funcs['tau'].astype(np.int64)
    p = funcs['phi']
    w = funcs['omega'].astype(np.int64)
    sp = funcs['sopfr']
    r = funcs['rad']

    # Precompute factorials for small values (tau is small)
    # max tau for n <= 10^7: tau(720720) = 240, but tau! would overflow
    # We only need factorial comparison for eq8: (n-1)(n+1) = tau! + 11
    # and eq24 (no factorial needed).
    # For eq8, tau(n) is typically small. tau! is huge for tau > 20.
    # We precompute factorial up to max possible tau value.
    max_tau = int(t[2:N+1].max())
    fact = np.zeros(max_tau + 1, dtype=np.int64)
    fact[0] = 1
    overflow_at = max_tau + 1
    for i in range(1, max_tau + 1):
        if fact[i-1] > 10**18 // max(i, 1):
            overflow_at = i
            break
        fact[i] = fact[i-1] * i
    # For tau values >= overflow_at, factorial overflows int64.
    # (n-1)(n+1) = n^2 - 1 <= (10^7)^2 = 10^14, well within int64.
    # tau! for tau >= 21: 21! = 5.1*10^19 > 10^14. So no match possible.
    # We'll handle this carefully.

    # Helper: for factorial-based equations, cap at overflow threshold
    tau_fact = np.zeros(N + 1, dtype=np.int64)
    for i in range(N + 1):
        tv = t[i]
        if tv < overflow_at:
            tau_fact[i] = fact[tv]
        else:
            tau_fact[i] = -1  # sentinel: overflow, won't match any LHS

    results = []

    # Define all 36 equations
    # Each: (eq_number, name, condition_array[2:N+1])
    # We slice [2:N+1] at the end to check n=2..N

    equations = []

    # ── Family I: tau-n identities (7) ──
    equations.append((1,  "n - 2 = tau(n)",
                      n - 2 == t))
    equations.append((2,  "n - tau(n) = 2",
                      n - t == 2))
    equations.append((3,  "(n-2)^2 = tau(n)^2",
                      (n - 2)**2 == t**2))
    equations.append((5,  "n + tau(n) = 10",
                      n + t == 10))
    equations.append((6,  "n * tau(n) = 24",
                      n * t == 24))
    equations.append((7,  "n^2 - tau(n)^2 = 20",
                      n**2 - t**2 == 20))
    equations.append((8,  "(n-1)(n+1) = tau(n)! + 11",
                      (n - 1) * (n + 1) == tau_fact + 11))

    # ── Family II: sigma-phi identities (6) ──
    equations.append((9,  "sigma(n)/n = phi(n)  [i.e. sigma = n*phi]",
                      s == n * p))
    equations.append((10, "sigma(n) = n*phi(n)",
                      s == n * p))
    equations.append((11, "sigma(n) - phi(n) = 10",
                      s - p == 10))
    equations.append((15, "sigma(n) - n*phi(n) = 0",
                      s - n * p == 0))
    equations.append((17, "sigma(n)^2 - phi(n)^2 = 140",
                      s**2 - p**2 == 140))
    equations.append((20, "sigma(n)*phi(n)/n = 4  [i.e. sigma*phi = 4n]",
                      s * p == 4 * n))

    # ── Family III: sigma-tau-phi combined (5) ──
    equations.append((22, "tau(n) = phi(n)^2",
                      t == p**2))
    equations.append((24, "sigma*phi/(n*tau) = 1  [i.e. sigma*phi = n*tau]",
                      s * p == n * t))
    equations.append((29, "tau^2 + phi^2 = sigma + 8",
                      t**2 + p**2 == s + 8))
    equations.append((33, "phi*sigma/tau = 6  [i.e. phi*sigma = 6*tau]",
                      p * s == 6 * t))
    equations.append((34, "tau + phi + sigma = 18",
                      t + p + s == 18))

    # ── Family IV: rad-sigma identities (8+1=9) ──
    equations.append((36, "rad(n) = sigma(n) - n",
                      r == s - n))
    equations.append((37, "sigma(n) = 2*rad(n)",
                      s == 2 * r))
    equations.append((38, "rad(n) + n = sigma(n)",
                      r + n == s))
    equations.append((39, "2*rad(n) = sigma(n)",
                      2 * r == s))
    equations.append((40, "rad(n)=n AND sigma(n)=2n",
                      (r == n) & (s == 2 * n)))
    equations.append((41, "sigma(n)/rad(n) = 2  [i.e. sigma = 2*rad]",
                      s == 2 * r))
    equations.append((42, "sigma(n) - rad(n) = n",
                      s - r == n))
    equations.append((43, "2*rad(n)^2 = n*sigma(n)",
                      2 * r**2 == n * s))
    equations.append((46, "rad(n) - phi(n) = tau(n)",
                      r - p == t))

    # ── Family V: omega-phi identities (5) ──
    # Note: eq47 has no omega>=2 guard, eq48+ do.
    equations.append((47, "phi*omega = phi + omega",
                      p * w == p + w))
    # For omega>=2 guarded equations, we set condition to False where omega < 2
    w_ge2 = w >= 2
    equations.append((48, "phi = omega [omega>=2]",
                      w_ge2 & (p == w)))
    equations.append((51, "phi/omega = 1 [omega>=2]",
                      w_ge2 & (p == w)))
    equations.append((52, "omega^2 = phi^2 [omega>=2]",
                      w_ge2 & (w**2 == p**2)))
    equations.append((53, "omega! = phi! [omega>=2]",
                      w_ge2 & (p == w)))  # omega! = phi! iff omega = phi (for positive ints)

    # ── Family VI: sopfr-mixed identities (4) ──
    equations.append((57, "sopfr(n) + 1 = n",
                      sp + 1 == n))
    equations.append((58, "sopfr(n) = n - 1 [omega>=2]",
                      w_ge2 & (sp == n - 1)))
    equations.append((65, "sopfr + tau = sigma - 3",
                      sp + t == s - 3))
    equations.append((66, "sopfr^2 = n*tau + 1",
                      sp**2 == n * t + 1))

    assert len(equations) == 36, f"Expected 36 equations, got {len(equations)}"

    print(f"\n{'='*78}")
    print(f"  Checking all 36 equations for n = 2 to {N:,}")
    print(f"{'='*78}\n")

    counterexamples = []
    all_ok = True

    for eq_num, name, cond_full in equations:
        t0 = time.time()
        # Extract n=2..N
        cond = cond_full[2:N+1]
        solutions = np.nonzero(cond)[0] + 2  # +2 because index 0 = n=2

        elapsed = time.time() - t0

        if len(solutions) == 1 and solutions[0] == 6:
            status = f"UNIQUE to n=6 up to {N:,}"
            marker = "OK"
        elif len(solutions) == 0:
            status = f"ERROR: n=6 NOT a solution!"
            marker = "FAIL"
            all_ok = False
            counterexamples.append((eq_num, name, "n=6 missing", []))
        elif 6 in solutions and len(solutions) > 1:
            others = solutions[solutions != 6]
            status = f"COUNTEREXAMPLE! {len(others)} other solution(s)"
            marker = "CRIT"
            all_ok = False
            # Show first few
            shown = others[:10]
            counterexamples.append((eq_num, name, "extra solutions", others.tolist()))
        else:
            status = f"n=6 not in solutions: {solutions[:5]}"
            marker = "FAIL"
            all_ok = False
            counterexamples.append((eq_num, name, "n=6 missing", solutions.tolist()))

        print(f"  [{marker:4s}] Eq {eq_num:2d}: {name:45s}  {status}  ({elapsed:.3f}s)")
        if marker == "CRIT":
            shown = others[:20]
            print(f"         First counterexamples: {shown.tolist()}")

        results.append((eq_num, name, marker, elapsed))

    return results, counterexamples, all_ok


# ══════════════════════════════════════════════════════════════════════
#  PART 3: Perfect Number Check (n = 6, 28, 496, 8128)
# ══════════════════════════════════════════════════════════════════════

def check_perfect_numbers(funcs):
    """Check which of the 36 equations hold for n = 6, 28, 496, 8128."""
    perfects = [6, 28, 496, 8128]

    print(f"\n{'='*78}")
    print(f"  Perfect Number Check: which of 36 equations hold at n = 6, 28, 496, 8128?")
    print(f"{'='*78}\n")

    s = funcs['sigma']
    t = funcs['tau'].astype(np.int64)
    p = funcs['phi']
    w = funcs['omega'].astype(np.int64)
    sp = funcs['sopfr']
    r = funcs['rad']

    # For factorial: precompute small values
    import math

    def check_one(nn):
        """Return list of equation numbers that hold at n=nn."""
        sv, tv, pv, wv, spv, rv = s[nn], int(t[nn]), p[nn], int(w[nn]), sp[nn], r[nn]
        holds = []

        # Family I
        if nn - 2 == tv: holds.append(1)
        if nn - tv == 2: holds.append(2)
        if (nn-2)**2 == tv**2: holds.append(3)
        if nn + tv == 10: holds.append(5)
        if nn * tv == 24: holds.append(6)
        if nn**2 - tv**2 == 20: holds.append(7)
        if (nn-1)*(nn+1) == math.factorial(tv) + 11: holds.append(8)

        # Family II
        if sv == nn * pv: holds.append(9)
        if sv == nn * pv: holds.append(10)
        if sv - pv == 10: holds.append(11)
        if sv - nn * pv == 0: holds.append(15)
        if sv**2 - pv**2 == 140: holds.append(17)
        if sv * pv == 4 * nn: holds.append(20)

        # Family III
        if tv == pv**2: holds.append(22)
        if sv * pv == nn * tv: holds.append(24)
        if tv**2 + pv**2 == sv + 8: holds.append(29)
        if pv * sv == 6 * tv: holds.append(33)
        if tv + pv + sv == 18: holds.append(34)

        # Family IV
        if rv == sv - nn: holds.append(36)
        if sv == 2 * rv: holds.append(37)
        if rv + nn == sv: holds.append(38)
        if 2 * rv == sv: holds.append(39)
        if rv == nn and sv == 2 * nn: holds.append(40)
        if sv == 2 * rv: holds.append(41)
        if sv - rv == nn: holds.append(42)
        if 2 * rv**2 == nn * sv: holds.append(43)
        if rv - pv == tv: holds.append(46)

        # Family V
        if pv * wv == pv + wv: holds.append(47)
        if wv >= 2 and pv == wv: holds.append(48)
        if wv >= 2 and pv == wv: holds.append(51)
        if wv >= 2 and wv**2 == pv**2: holds.append(52)
        if wv >= 2 and pv == wv: holds.append(53)

        # Family VI
        if spv + 1 == nn: holds.append(57)
        if wv >= 2 and spv == nn - 1: holds.append(58)
        if spv + tv == sv - 3: holds.append(65)
        if spv**2 == nn * tv + 1: holds.append(66)

        return holds

    for nn in perfects:
        if nn > len(s) - 1:
            print(f"  n = {nn}: outside sieve range, skipping")
            continue
        holds = check_one(nn)
        sv, tv, pv, wv, spv, rv = s[nn], int(t[nn]), p[nn], int(w[nn]), sp[nn], r[nn]
        print(f"  n = {nn}:")
        print(f"    sigma={sv}, tau={tv}, phi={pv}, omega={wv}, sopfr={spv}, rad={rv}")
        print(f"    Equations satisfied: {holds if holds else 'NONE'}")
        print(f"    Count: {len(holds)}/36")
        print()


# ══════════════════════════════════════════════════════════════════════
#  PART 4: TOP 8 Theorems — Special Focus
# ══════════════════════════════════════════════════════════════════════

def top8_focus(funcs, N):
    """Extra detail on the 8 core theorems."""
    print(f"\n{'='*78}")
    print(f"  TOP 8 THEOREMS — Special Focus (verified to {N:,})")
    print(f"{'='*78}\n")

    n = np.arange(N + 1, dtype=np.int64)
    s = funcs['sigma']
    t = funcs['tau'].astype(np.int64)
    p = funcs['phi']
    w = funcs['omega'].astype(np.int64)
    sp = funcs['sopfr']
    r = funcs['rad']

    top8 = [
        (1,  "Thm 1: n - 2 = tau(n)",              n - 2 == t),
        (9,  "Thm 2: sigma(n) = n*phi(n)",          s == n * p),
        (36, "Thm 3: rad(n) = sigma(n) - n",        r == s - n),
        (22, "Thm 4: tau(n) = phi(n)^2",            t == p**2),
        (47, "Thm 5: phi*omega = phi + omega",       p * w == p + w),
        (37, "Thm 6: sigma(n) = 2*rad(n)",          s == 2 * r),
        (24, "Thm 7: sigma*phi = n*tau",             s * p == n * t),
        (57, "Thm 8: sopfr(n) + 1 = n",             sp + 1 == n),
    ]

    for eq_num, name, cond_full in top8:
        cond = cond_full[2:N+1]
        solutions = np.nonzero(cond)[0] + 2

        if len(solutions) == 1 and solutions[0] == 6:
            verdict = "UNIQUE to n=6"
        elif len(solutions) == 0:
            verdict = "ERROR: no solutions found"
        else:
            others = solutions[solutions != 6]
            if len(others) > 0:
                verdict = f"COUNTEREXAMPLE at n={others[0]}"
            else:
                verdict = "UNIQUE to n=6"

        print(f"  Eq {eq_num:2d}  {name}")
        print(f"         Solutions in [2, {N:,}]: {solutions.tolist() if len(solutions) <= 10 else f'{solutions[:5].tolist()} ... ({len(solutions)} total)'}")
        print(f"         Verdict: {verdict}")
        print()


# ══════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    overall_start = time.time()

    print("=" * 78)
    print("  EXTREME VERIFICATION: 36 Equations Unique to n=6")
    print(f"  Range: n = 2 to {LIMIT:,} (ten million)")
    print("=" * 78)
    print()

    # Step 1: Sieve
    funcs = sieve_all(LIMIT)

    # Quick sanity check
    assert funcs['sigma'][6] == 12, f"sigma(6) = {funcs['sigma'][6]}, expected 12"
    assert funcs['tau'][6] == 4, f"tau(6) = {funcs['tau'][6]}, expected 4"
    assert funcs['phi'][6] == 2, f"phi(6) = {funcs['phi'][6]}, expected 2"
    assert funcs['omega'][6] == 2, f"omega(6) = {funcs['omega'][6]}, expected 2"
    assert funcs['sopfr'][6] == 5, f"sopfr(6) = {funcs['sopfr'][6]}, expected 5"
    assert funcs['rad'][6] == 6, f"rad(6) = {funcs['rad'][6]}, expected 6"
    # Check n=28 too
    assert funcs['sigma'][28] == 56, f"sigma(28) = {funcs['sigma'][28]}, expected 56"
    assert funcs['tau'][28] == 6, f"tau(28) = {funcs['tau'][28]}, expected 6"
    assert funcs['phi'][28] == 12, f"phi(28) = {funcs['phi'][28]}, expected 12"
    print("  Sanity checks passed.\n")

    # Step 2: Check all 36 equations
    results, counterexamples, all_ok = check_all_equations(funcs, LIMIT)

    # Step 3: Top 8 special focus
    top8_focus(funcs, LIMIT)

    # Step 4: Perfect number check
    check_perfect_numbers(funcs)

    # ── Summary ──
    total_time = time.time() - overall_start
    print("=" * 78)
    print("  FINAL SUMMARY")
    print("=" * 78)
    print()

    ok_count = sum(1 for _, _, m, _ in results if m == "OK")
    fail_count = sum(1 for _, _, m, _ in results if m != "OK")
    total_eq_time = sum(e for _, _, _, e in results)

    print(f"  Range checked:    n = 2 to {LIMIT:,}")
    print(f"  Equations tested: 36")
    print(f"  UNIQUE to n=6:    {ok_count}/36")
    print(f"  FAILURES:         {fail_count}/36")
    print()

    if counterexamples:
        print("  *** COUNTEREXAMPLES FOUND ***")
        for eq_num, name, kind, sols in counterexamples:
            if kind == "extra solutions":
                shown = sols[:20]
                print(f"    Eq {eq_num}: {name}")
                print(f"      {kind}: {shown}{'...' if len(sols) > 20 else ''} ({len(sols)} total)")
            else:
                print(f"    Eq {eq_num}: {name} -- {kind}")
        print()
    else:
        print("  NO COUNTEREXAMPLES FOUND.")
        print("  All 36 equations are uniquely satisfied by n=6 up to 10,000,000.")
        print()

    print(f"  Equation check time: {total_eq_time:.1f}s")
    print(f"  Total runtime:       {total_time:.1f}s")
    print("=" * 78)

    if counterexamples:
        sys.exit(1)


if __name__ == "__main__":
    main()
