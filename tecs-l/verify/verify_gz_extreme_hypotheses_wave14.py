"""
WAVE 14 — SYMMETRIC FUNCTIONS, MODULAR ARITHMETIC, TOPOLOGY,
           COMBINATORIAL GAME THEORY, ANALYTIC SPECIAL FUNCTIONS
Strict grading: ⚪ for tautologies. 🟩 only if unique to n=6 (test n=10,12,28).
221/325 cumulative. Keep pushing.
"""

import math
from fractions import Fraction
from functools import reduce
from itertools import combinations
import sympy
from sympy import (
    divisors, totient, factorint, isprime, nextprime,
    Rational, pi as sympi, E as symE, gcd, Integer,
    gamma as sym_gamma, zeta as sym_zeta, log as sym_log,
    sqrt, binomial, factorial, isprime, primerange, primorial
)
from sympy.ntheory.factor_ import divisor_sigma, divisor_count
from sympy import Poly, Symbol, resultant, discriminant
from sympy.abc import x as sym_x
from sympy import carmichael

# ── Constants ──────────────────────────────────────────────────────────────────
GZ_UPPER  = 0.5
GZ_CENTER = math.exp(-1)          # 1/e ≈ 0.3679
GZ_LOWER  = 0.5 - math.log(4/3)  # ≈ 0.2123
GZ_WIDTH  = math.log(4/3)        # ln(4/3)
META      = 1/3
COMPASS   = 5/6
CURIOSITY = 1/6

# n=6 properties
N = 6
DIVS6  = [1, 2, 3, 6]
SIGMA6 = 12  # sum of divisors
TAU6   = 4   # number of divisors
PHI6   = 2   # Euler totient
SOPFR6 = 5   # sum of prime factors with repetition (2+3)
P6     = 11  # partition number p(6)
OMEGA6 = 2   # number of distinct prime factors
B6     = Fraction(1, 42)  # Bernoulli number B_6

results = []

def record(num, title, grade, detail, uniqueness=""):
    results.append({"num": num, "title": title, "grade": grade,
                    "detail": detail, "uniqueness": uniqueness})

def in_gz(x):
    return GZ_LOWER <= x <= GZ_UPPER

# ═══════════════════════════════════════════════════════════════════════════════
# A: SYMMETRIC FUNCTIONS & INVARIANTS
# ═══════════════════════════════════════════════════════════════════════════════

# H01: Elementary symmetric polynomials of {1,2,3,6}
def h01_elementary_symmetric():
    d = [1, 2, 3, 6]
    e1 = sum(d)                                      # 12 = sigma(6)
    e2 = sum(d[i]*d[j] for i in range(4) for j in range(i+1,4))
    e3 = sum(d[i]*d[j]*d[k] for i in range(4) for j in range(i+1,4) for k in range(j+1,4))
    e4 = d[0]*d[1]*d[2]*d[3]                        # = 6! / something?
    # e2 = 1*2+1*3+1*6+2*3+2*6+3*6 = 2+3+6+6+12+18 = 47
    # e3 = 1*2*3+1*2*6+1*3*6+2*3*6 = 6+12+18+36 = 72
    # e4 = 36
    # Check: e4 = 36 = 6^2 = n^2 = sigma(6)^2/4 = tau*sopfr*...?
    # More interesting: n^(tau/2) = 6^(4/2) = 36 — that's in the prompt
    n_tau_half = N**(TAU6//2)  # 6^2 = 36
    sigma_sq_over_4 = SIGMA6**2 // 4  # 36

    # Is e2 = 47? Let's check if it relates to anything
    # For n=28: divisors {1,2,4,7,14,28}, e1=56=sigma(28), e4=28*14*7*4*2*1 (too many divisors)
    # For n=6, 4 divisors so well-defined elementary sym polys up to e4

    # Key identity: e1*e3 - e2*e2? No. Check generating polynomial
    # (x-1)(x-2)(x-3)(x-6) coefficients via Vieta = alternating e_k
    # = x^4 - e1*x^3 + e2*x^2 - e3*x + e4
    # = x^4 - 12x^3 + 47x^2 - 72x + 36

    # n^2 = e4 = 36: e4 = product of divisors of 6 = n^(tau/2) is GENERAL identity
    # For any perfect number n: product(divisors) = n^(tau/2)
    # This holds for all n, not just 6. Test n=28: product(divs(28)) = 28^(tau(28)/2)
    n28_divs = [1,2,4,7,14,28]
    n28_prod = 1
    for d28 in n28_divs: n28_prod *= d28
    n28_check = 28**(len(n28_divs)//2)  # 28^3 = 21952

    detail = (f"e1={e1}=sigma(6), e2={e2}, e3={e3}, e4={e4}=n^(tau/2)={n_tau_half}\n"
              f"  Generating poly: x^4 - 12x^3 + 47x^2 - 72x + 36\n"
              f"  e4=n^(tau/2) is GENERAL for all n (n=28: {n28_prod}={n28_check}? {n28_prod==n28_check})\n"
              f"  e2=47: no obvious GZ connection. e3=72=6*12=n*sigma(n)=n*sigma")

    # n*sigma = 6*12 = 72 = e3: is this general? n=28: 28*56=1568, e3 for 28?
    n28_e3 = sum(n28_divs[i]*n28_divs[j]*n28_divs[k]
                 for i in range(6) for j in range(i+1,6) for k in range(j+1,6))
    n28_nsigma = 28 * sum(n28_divs)

    detail += f"\n  e3=n*sigma(n)? n=6: 6*12=72=e3 YES. n=28: e3={n28_e3} vs n*sigma={n28_nsigma} {'YES' if n28_e3==n28_nsigma else 'NO'}"

    if e3 == N * SIGMA6 and n28_e3 != n28_nsigma:
        grade = "🟩"
        detail += "\n  UNIQUE TO N=6: e3(divisors(6)) = n*sigma(n)"
    elif e3 == N * SIGMA6 and n28_e3 == n28_nsigma:
        grade = "⚪"
        detail += "\n  General identity, not unique to n=6"
    else:
        grade = "⚪"

    record("W14-A01", "Elem sym poly e3=n*sigma", grade, detail)

h01_elementary_symmetric()

# H02: Power sums — (Σ1/d²) = (7/6)² = ((n+1)/n)²?
def h02_power_sums():
    d = [1, 2, 3, 6]
    # k=-2: sum of 1/d^2
    sum_inv_sq = sum(Fraction(1, di**2) for di in d)
    # = 1 + 1/4 + 1/9 + 1/36 = 36/36 + 9/36 + 4/36 + 1/36 = 50/36 = 25/18

    # Prompt says 49/36 — let's verify carefully
    val = float(sum_inv_sq)

    # (n+1)^2/n^2 = 49/36 for n=6
    formula_val = Fraction((N+1)**2, N**2)  # 49/36

    detail = f"Σ1/d² for d|6 = {sum_inv_sq} = {float(sum_inv_sq):.6f}\n"
    detail += f"  (n+1)²/n² = {formula_val} = {float(formula_val):.6f}\n"

    if sum_inv_sq == formula_val:
        # Check n=10: divisors {1,2,5,10}
        s10 = sum(Fraction(1, di**2) for di in [1,2,5,10])
        f10 = Fraction(11**2, 10**2)
        # n=28
        s28 = sum(Fraction(1, di**2) for di in [1,2,4,7,14,28])
        f28 = Fraction(29**2, 28**2)
        detail += f"  n=10: Σ1/d²={s10}={float(s10):.4f}, (n+1)²/n²={f10}={float(f10):.4f} {'MATCH' if s10==f10 else 'NO'}\n"
        detail += f"  n=28: Σ1/d²={s28}={float(s28):.4f}, (n+1)²/n²={f28}={float(f28):.4f} {'MATCH' if s28==f28 else 'NO'}"
        if s10 == f10 or s28 == f28:
            grade = "⚪"
            detail += "\n  General pattern holds for other n → not unique"
        else:
            grade = "🟩"
            detail += "\n  UNIQUE to perfect number n=6!"
    else:
        detail += f"  Claim FALSE: {sum_inv_sq} ≠ {formula_val}"
        # What is the actual value?
        detail += f"\n  Actual = 25/18, not 49/36"

        # Hmm, let me reconsider. What DOES sum_inv_sq equal for perfect numbers?
        # For n=6 (perfect): sigma_{-1}(6) = 2, so Σ 1/d = 2
        # sigma_{-2}(6) = Σ 1/d^2
        sigma_m2 = sum(Fraction(1, d**2) for d in [1,2,3,6])
        detail += f"\n  sigma_{{-2}}(6) = {sigma_m2} = {float(sigma_m2):.6f}"
        grade = "⚪"

    record("W14-A02", "Σ1/d²=(n+1)²/n² for divisors of 6", grade, detail)

h02_power_sums()

# H03: Newton's identities linking e_k and p_k for divisors of 6
def h03_newtons_identity():
    d = [1, 2, 3, 6]
    e = [0, 12, 47, 72, 36]  # e[k] = k-th elem sym poly (e[0]=1 unused)
    p = [sum(di**k for di in d) for k in range(5)]  # p[0]=4=tau, p[1]=12, p[2]=50, ...

    # Newton's identities: p_k - e_1*p_{k-1} + ... + (-1)^{k-1} e_{k-1} p_1 + (-1)^k k*e_k = 0
    # p1 = e1 = 12 ✓
    # p2 - e1*p1 + 2*e2 = 0 → 50 - 12*12 + 2*47 = 50-144+94 = 0 ✓
    # p3 - e1*p2 + e2*p1 - 3*e3 = 0 → 1+8+27+216 - 12*50 + 47*12 - 3*72
    p3 = sum(di**3 for di in d)  # 1+8+27+216 = 252
    newton3_check = p3 - e[1]*p[2] + e[2]*p[1] - 3*e[3]

    detail = (f"p_k = {[sum(di**k for di in d) for k in range(5)]}\n"
              f"  e = {e[1:]}\n"
              f"  Newton check p3: {p3} - {e[1]}*{p[2]} + {e[2]}*{p[1]} - 3*{e[3]} = {newton3_check}\n"
              f"  GZ constants in p_k: none obvious\n"
              f"  p[0]=tau=4, p[1]=sigma=12, p[-1]=sigma_{{-1}}=2 — known identities")

    grade = "⚪"
    record("W14-A03", "Newton identities for divisors(6)", grade, detail,
           "Tautological — Newton identities hold for all sets")

h03_newtons_identity()

# H04: Discriminant of (x-1)(x-2)(x-3)(x-6)
def h04_discriminant():
    d = [1, 2, 3, 6]
    # Discriminant = ∏_{i<j} (d_j - d_i)^2
    pairs = [(d[j]-d[i]) for i in range(4) for j in range(i+1, 4)]
    disc = 1
    for p in pairs: disc *= p**2

    # pairs: (2-1),(3-1),(6-1),(3-2),(6-2),(6-3) = 1,2,5,1,4,3
    # disc = 1*4*25*1*16*9 = 14400
    # 14400 = 120^2 = (5!)^2 = (6!/6)^2 ?
    fact5 = math.factorial(5)  # 120
    fact6 = math.factorial(6)  # 720

    detail = (f"Disc({d}) = ∏(d_j-d_i)² = {disc}\n"
              f"  pairs diffs: {pairs}\n"
              f"  120² = {120**2}, 5!² = {fact5**2}, 6!/5 = {fact6//5}\n"
              f"  disc = {disc} = {int(math.sqrt(disc))}²\n"
              f"  sqrt(disc) = {int(math.sqrt(disc))} = ?")

    sqrt_disc = int(math.sqrt(disc))
    detail += f"\n  sqrt(disc) = {sqrt_disc}"

    # Is 120 = 5! special for n=6?
    # For n=10: divisors {1,2,5,10}, diffs = 1,4,9,3,8,5
    d10 = [1,2,5,10]
    disc10 = 1
    for i in range(4):
        for j in range(i+1, 4):
            disc10 *= (d10[j]-d10[i])**2
    detail += f"\n  n=10 disc = {disc10}, sqrt = {int(math.sqrt(disc10)) if disc10>0 else 'NA'}"

    # disc(6) = 14400 = 120^2. Is 120 = |M_{0,6}| related? Or just 5!?
    # 14400 = 12^2 * 100 = sigma^2 * 100. Coincidence?
    sigma_sq = SIGMA6**2  # 144
    detail += f"\n  sigma(6)^2 = {sigma_sq}, disc/sigma² = {disc//sigma_sq}"

    grade = "⚪"
    detail += "\n  No unique GZ connection — numerical coincidence"
    record("W14-A04", "Discriminant of divisor polynomial = 14400", grade, detail)

h04_discriminant()

# H05: Resultant of (x-1)(x-2)(x-3) and (x-6) = (6-1)(6-2)(6-3) = 60
def h05_resultant():
    # Res(f,g) where f=(x-1)(x-2)(x-3), g=(x-6)
    # = ∏ f(roots of g) = f(6) = (6-1)(6-2)(6-3) = 5*4*3 = 60
    val = 5 * 4 * 3
    lcm_1_to_6 = 60  # lcm(1,2,3,4,5,6)

    # Verify lcm(1..6)
    import math
    lcm6 = 1
    for i in range(1, 7): lcm6 = lcm6 * i // math.gcd(lcm6, i)

    detail = (f"Res((x-1)(x-2)(x-3), (x-6)) = (6-1)(6-2)(6-3) = 5*4*3 = {val}\n"
              f"  lcm(1..6) = {lcm6}\n"
              f"  val = lcm(1..6) = {val} {'YES' if val==lcm6 else 'NO'}\n"
              f"  This holds because lcm(1,2,3,4,5,6) = 60 by coincidence")

    # Test uniqueness: for general n, Res((x-1)...(x-(n-1)), (x-n)) = (n-1)!
    # For n=6: (n-1)! = 5! = 120 ≠ 60. Wait — only 3 factors (1,2,3) not all 5.
    # So we're looking at first half of proper divisors vs n itself.
    # For n=6: proper divisors < n/2 = {1,2,3} and n=6. Product = 3! * something?
    # (n-1)(n-2)(n-3) = 5*4*3 = 60 = lcm(1..6). Is this just coincidence?

    # For n=28: (28-1)(28-2)(28-3) = 27*26*25 = 17550 vs lcm(1..28)?
    lcm28 = 1
    for i in range(1, 29): lcm28 = lcm28 * i // math.gcd(lcm28, i)
    prod28 = 27*26*25
    detail += f"\n  n=28: (n-1)(n-2)(n-3) = {prod28} vs lcm(1..28) = {lcm28} {'MATCH' if prod28==lcm28 else 'NO'}"

    # So it's specific to n=6 that (n-1)(n-2)(n-3) = lcm(1..n)
    if prod28 != lcm28:
        grade = "🟩"
        # But wait — is this algebraically meaningful or just numerical coincidence?
        # lcm(1..6) = 2^2 * 3 * 5 = 60. (n-1)(n-2)(n-3) = 5*4*3 = 60.
        # This is a NUMBER COINCIDENCE not an algebraic identity. Downgrade.
        grade = "🟧"
        detail += "\n  Unique to n=6 numerically but no algebraic reason → 🟧 (numerical coincidence)"
    else:
        grade = "⚪"

    record("W14-A05", "Res(d<n poly, x-n) = lcm(1..n) for n=6", grade, detail)

h05_resultant()

# ═══════════════════════════════════════════════════════════════════════════════
# B: MODULAR ARITHMETIC PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════

# H06: ord_7(2) = 3 = n/phi(n)
def h06_multiplicative_order():
    # ord_7(2): smallest k with 2^k ≡ 1 (mod 7)
    k = 1
    while pow(2, k, 7) != 1: k += 1
    ord72 = k  # should be 3

    n_over_phi = N // PHI6  # 6/2 = 3

    # Check uniqueness: is ord_{n+1}(2) = n/phi(n) for other n?
    def mult_order(a, m):
        if math.gcd(a, m) != 1: return None
        k = 1
        while pow(a, k, m) != 1: k += 1
        return k

    results_check = {}
    for n in [6, 10, 12, 28]:
        next_p = sympy.nextprime(n)
        phi_n = int(totient(n))
        if n % phi_n == 0:
            ratio = n // phi_n
            ord_val = mult_order(2, next_p)
            results_check[n] = (next_p, ratio, ord_val, ord_val == ratio)

    detail = (f"ord_7(2) = {ord72}, n/phi(n) = {n_over_phi}\n"
              f"  Match: {ord72 == n_over_phi}\n"
              f"  Checking for other n:")
    for n, (p, ratio, ord_v, match) in results_check.items():
        detail += f"\n    n={n}: nextprime={p}, n/phi={ratio}, ord_p(2)={ord_v}, match={match}"

    # This is an algebraic fact: ord_7(2)=3 is specific to the prime 7
    # and not directly related to n=6 properties beyond next-prime coincidence
    matches = sum(1 for _, (_, _, _, m) in results_check.items() if m)
    if matches <= 1:
        grade = "🟧"
        detail += f"\n  Only matches for n=6 among tested. Suggestive but not algebraic."
    else:
        grade = "⚪"
        detail += f"\n  Matches for {matches} values of n → not unique"

    record("W14-B06", "ord_{n+1}(2) = n/phi(n) at n=6", grade, detail)

h06_multiplicative_order()

# H07: Carmichael lambda(6) = 2 = phi(6)
def h07_carmichael():
    # carmichael(6) from sympy
    try:
        lam6 = int(carmichael(6))
    except Exception:
        # manual: lambda(6) = lcm(lambda(2), lambda(3)) = lcm(1,2) = 2
        lam6 = 2
    phi6_val = int(totient(6))

    detail = (f"lambda(6) = {lam6}, phi(6) = {phi6_val}\n"
              f"  lambda(6) = phi(6) = 2\n"
              f"  This is general: lambda(n) = phi(n) for all squarefree n with at most 2 prime factors\n"
              f"  6 = 2*3 (squarefree, 2 primes) → tautological")

    grade = "⚪"
    record("W14-B07", "lambda(6) = phi(6)", grade, detail,
           "General for squarefree semiprimes")

h07_carmichael()

# H08: Wilson quotient W_7 = (6!+1)/7 = 103, primality
def h08_wilson_quotient():
    p = 7
    fact6 = math.factorial(6)  # 720
    wq = (fact6 + 1) // p  # (720+1)/7 = 721/7
    exact = (fact6 + 1) % p == 0
    is_prime_wq = sympy.isprime(wq)

    detail = (f"Wilson quotient W_7 = (6!+1)/7 = (720+1)/7 = {721//7} r{721%7}\n"
              f"  Exact division: {exact}\n"
              f"  W_7 = {wq}, is prime: {is_prime_wq}\n"
              f"  By Wilson's theorem (p-1)! ≡ -1 (mod p) for prime p\n"
              f"  p=7: 6! = 720 ≡ -1 ≡ 6 (mod 7). 720+1=721=7*103. W_7=103.")

    # 103 is prime — but this is a number-theoretic fact about p=7, not about n=6
    # The connection is: p=n+1=7, and W_p is prime. Is W_{n+1} prime unique to n=6?
    def wilson_quotient(p):
        if not sympy.isprime(p): return None
        fn = math.factorial(p-1)
        if (fn + 1) % p != 0: return None
        return (fn + 1) // p

    wq_check = {}
    for n in [4, 6, 10, 12]:  # n+1 must be prime
        p_candidate = n + 1
        if sympy.isprime(p_candidate):
            wq_val = wilson_quotient(p_candidate)
            wq_check[n] = (p_candidate, wq_val, sympy.isprime(wq_val) if wq_val else False)

    detail += f"\n  W_{{n+1}} primality for various n:"
    for n, (p, wq_v, is_p) in wq_check.items():
        detail += f"\n    n={n}: p={p}, W_p={wq_v}, prime={is_p}"

    grade = "⚪"
    detail += "\n  No algebraic identity — numerical property of p=7"
    record("W14-B08", "Wilson quotient W_7 = 103 is prime", grade, detail)

h08_wilson_quotient()

# H09: Digital root of n! = 9 for n >= 6
def h09_digital_root():
    def digital_root(n):
        if n == 0: return 0
        r = n % 9
        return r if r != 0 else 9

    results_dr = {}
    for n in range(0, 15):
        fn = math.factorial(n)
        dr = digital_root(fn)
        results_dr[n] = (fn, dr)

    detail = "Digital roots of n!:\n"
    for n, (fn, dr) in results_dr.items():
        detail += f"  {n}! = {fn}, digital_root = {dr}\n"

    # For n>=5, n! is divisible by 9 (since 5! = 120, 3 and 6 in factors)
    # Actually for n>=6: 1*2*3*4*5*6 includes two factors of 3 (3 and 6), so 9|6!
    # So digital_root(n!) = 9 for all n>=6? Let's verify
    all_9 = all(dr == 9 for n, (fn, dr) in results_dr.items() if n >= 6)
    # But also n=9: 9! divisible by 9 certainly
    # n=5: 5!=120, dr=3 (1+2+0=3)
    # n=6: 6!=720, dr=9 (7+2+0=9) ✓

    detail += f"\n  All n>=6 have digital_root(n!) = 9: {all_9}"
    detail += f"\n  5! digital root = {digital_root(120)} (not 9)"
    detail += f"\n  6 is smallest n where digital_root(n!) = 9"

    # Is this unique to n=6? No — it holds for all n>=6. But n=6 is the THRESHOLD.
    # The threshold being exactly 6 (the smallest perfect number) — is this meaningful?
    # Algebraic reason: n>=6 ensures 3 and 6 both appear in 1..n, so 9|n!
    # Actually: need two factors of 3 in n!. v_3(n!) = floor(n/3)+floor(n/9)+...
    # v_3(6!) = 2+0 = 2 → 9|6!. v_3(5!) = 1 → 9∤5!
    # So threshold is actually at n where v_3(n!)>=2, which is n=6. Coincides with perfect number.

    # Test: is digital_root(n!)=9 unique threshold at n=6 (perfect)?
    # For n=10 (not perfect): digital_root(10!) also = 9 (since 10>=6)
    # So the property holds broadly — the threshold n=6 coincides with perfect number but isn't "because" perfect

    grade = "⚪"
    detail += "\n  Threshold n=6 is where v_3(n!)>=2. Algebraic coincidence with perfectness."
    record("W14-B09", "n=6 is threshold for digital_root(n!)=9", grade, detail)

h09_digital_root()

# H10: Number of solutions to x^6 ≡ 1 (mod p)
def h10_sixth_power_roots():
    # x^6 ≡ 1 (mod p): number of solutions = gcd(6, p-1) for prime p
    primes_test = [7, 13, 19, 31, 37, 43]
    results_h10 = {}
    for p in primes_test:
        num_sol = math.gcd(6, p-1)
        results_h10[p] = (p-1, num_sol)

    detail = "x^6 ≡ 1 (mod p): #solutions = gcd(6, p-1)\n"
    for p, (pm1, nsol) in results_h10.items():
        detail += f"  p={p}: p-1={pm1}, gcd(6,p-1)={nsol}\n"

    detail += (f"  Pattern: p≡1(mod 6) → 6 solutions, p≡1(mod 3) → 3 solutions, etc.\n"
               f"  This is general theory (cyclic group Z/(p-1)Z), not specific to n=6.\n"
               f"  gcd(n, p-1) formula works for any n.")

    grade = "⚪"
    record("W14-B10", "x^n≡1(mod p) count = gcd(n,p-1)", grade, detail,
           "General theorem for cyclic groups mod prime")

h10_sixth_power_roots()

# ═══════════════════════════════════════════════════════════════════════════════
# C: TOPOLOGICAL INVARIANTS
# ═══════════════════════════════════════════════════════════════════════════════

# H11: Euler characteristic of Conf(6, R²)
def h11_conf_euler_char():
    # Configuration space Conf(n, R²) of n distinct ordered points in R²
    # χ(Conf(n, R²)) = (-1)^(n-1) * (n-1)!
    n = 6
    chi = ((-1)**(n-1)) * math.factorial(n-1)  # (-1)^5 * 120 = -120

    # |chi| = 120 = 5! = (n-1)!
    fact_nm1 = math.factorial(n-1)  # 120

    # Is 120 = 6!/6 = n!/n? Yes: 720/6 = 120. Also = sigma(6)*10? 12*10=120.
    # More relevantly: is there a GZ connection?
    # 120 = 5! is a standard combinatorial number. Not GZ specific.

    detail = (f"χ(Conf(6, R²)) = (-1)^5 * 5! = {chi}\n"
              f"  |χ| = {abs(chi)} = 5! = (n-1)!\n"
              f"  = n!/n = {math.factorial(n)//n}\n"
              f"  General formula: χ(Conf(n,R²)) = (-1)^(n-1)(n-1)!\n"
              f"  Not specific to n=6")

    grade = "⚪"
    record("W14-C11", "χ(Conf(6,R²)) = -120", grade, detail,
           "General formula for configuration spaces")

h11_conf_euler_char()

# H12: First Betti number of Conf(6, R²) = sopfr(6) = 5
def h12_betti_conf():
    # Conf(n, R²) = n*(n-1)/2 independent generators (real codim 1 hyperplanes removed)
    # Actually the complement of braid arrangement: n*(n-1)/2 hyperplanes
    n = 6
    b1 = n*(n-1)//2  # first Betti number = number of hyperplanes = 15 for n=6

    # Wait — the 1-skeleton: actually π_1(Conf(n,R²)) is the pure braid group
    # b_1 = n*(n-1)/2 for Conf(n, R²)? That's the rank.
    # For n=6: b1 = 15, not 5.
    # But the prompt says b_1 = 5 = sopfr(6). Let me check.
    # b_1 of Conf(n, R²): For ordered config space in R², the space has
    # H_1 rank = n*(n-1)/2 (from the deleted hyperplane arrangement).

    detail = (f"b_1(Conf(6, R²)) = n*(n-1)/2 = {b1} (standard result)\n"
              f"  sopfr(6) = 5 (2+3)\n"
              f"  Claim b_1 = 5 = sopfr: FALSE. b_1 = 15.\n"
              f"  Note: perhaps confused with something else.")

    # Alternative: Conf(n, R²) / S_n = unordered config, different Betti numbers
    # Or Conf(n, S^1): circle. b_1(Conf(2, R²)) = 1. b_1(Conf(3,R²)) = 3. b_1(Conf(6,R²))=15
    grade = "⚪"
    detail += "\n  Hypothesis incorrect: b_1=15, not 5. No connection to sopfr."
    record("W14-C12", "b_1(Conf(6,R²)) = sopfr(6)", grade, detail)

h12_betti_conf()

# H13: H_1 of lens space L(6,1) = Z/6Z, order = 6 = n
def h13_lens_space():
    # L(p,q) has H_1 = Z/pZ, so |H_1(L(6,1))| = 6 = n ✓ (by definition)
    detail = (f"|H_1(L(6,1))| = 6 = n (by definition of lens space L(n,1))\n"
              f"  H_1(L(n,1)) = Z/nZ for any n — tautological\n"
              f"  Not specific to n=6")
    grade = "⚪"
    record("W14-C13", "|H_1(L(6,1))| = n", grade, detail,
           "Tautological — true for all lens spaces L(n,1)")

h13_lens_space()

# H14: Dehn twist in mapping class group of genus 2 surface (phi(6)=2)
def h14_mapping_class():
    # Genus g=2 surface: MCG(Σ_2) is generated by Dehn twists
    # The mapping class group has finite presentation.
    # Key fact: MCG(Σ_g) has order... infinite (it's infinite for g≥1)
    # But hyperelliptic involution of genus 2 has order 2 = phi(6).
    # More concrete: the center of MCG(Σ_2) is Z/2Z, order = phi(6) = 2.
    # This connection: g = phi(n) = 2 for n=6.

    # For g=2: center(MCG(Σ_2)) = Z/2Z (the hyperelliptic involution)
    # phi(6) = 2 = order of center
    # For n=10: phi(10) = 4, genus 4 surface, center of MCG(Σ_4) = Z/2Z (still!)
    # For n=28: phi(28) = 12, MCG(Σ_{12}) center = Z/2Z
    # So center is always Z/2Z regardless of genus. Not unique to n=6.

    detail = (f"phi(6) = {PHI6} = genus of surface\n"
              f"  center(MCG(Σ_2)) = Z/2Z (hyperelliptic involution)\n"
              f"  Order = 2 = phi(6)\n"
              f"  But center(MCG(Σ_g)) = Z/2Z for ALL g>=1\n"
              f"  phi(n)=2 makes g=2, and center has order 2=phi(n) by coincidence\n"
              f"  Not unique to n=6 in any algebraic sense")
    grade = "⚪"
    record("W14-C14", "Order of center MCG(Σ_{phi(6)}) = phi(6)", grade, detail)

h14_mapping_class()

# H15: |χ(M_{0,6})| = (6-3)! = 3! = 6 = n
def h15_moduli_space_euler():
    # χ(M_{0,n}) for genus 0, n marked points
    # Formula: χ(M_{0,n}) = (-1)^(n-3) * (n-3)! for n>=3 (one formulation)
    # Alternatively: |χ(M_{0,n})| = (n-3)!
    n = 6
    chi_val = math.factorial(n-3)  # 3! = 6

    # |χ(M_{0,6})| = 6 = n

    # Check other n:
    # n=10: |χ(M_{0,10})| = 7! = 5040 vs n=10: NO
    # n=7: |χ(M_{0,7})| = 4! = 24 vs n=7: NO
    # n=4: |χ(M_{0,4})| = 1! = 1 vs n=4: NO
    # Only n=6: (n-3)! = 3! = 6 = n ↔ n-3 = 3 ↔ n=6. Unique!

    check = {}
    for n_test in [4, 5, 6, 7, 8, 10, 12, 28]:
        chi_t = math.factorial(n_test - 3)
        check[n_test] = (chi_t, chi_t == n_test)

    detail = (f"|χ(M_{{0,6}})| = (6-3)! = 3! = {chi_val} = n? {chi_val == n}\n"
              f"  Formula: |χ(M_{{0,n}})| = (n-3)!\n"
              f"  Check (n-3)! = n ↔ n!/6 = n? No, (n-3)!=n iff n=6 (since 3!=6)\n\n"
              f"  n-tests:\n")
    for n_test, (chi_t, match) in check.items():
        detail += f"    n={n_test}: |χ|={chi_t}, =n? {match}\n"

    all_match = [n_test for n_test, (_, m) in check.items() if m]
    if all_match == [6]:
        grade = "🟩"
        detail += f"\n  UNIQUE: only n=6 satisfies (n-3)! = n among all tested n"
        detail += f"\n  Algebraic proof: (n-3)! = n → n=6 is only solution for n integer >= 4"
        detail += f"\n  (n-3)! = n: for n=4: 1=4 NO, n=5: 2=5 NO, n=6: 6=6 YES, n=7: 24=7 NO, monotone increasing"
    else:
        grade = "⚪"

    record("W14-C15", "|χ(M_{0,n})| = n only at n=6", grade, detail)

h15_moduli_space_euler()

# ═══════════════════════════════════════════════════════════════════════════════
# D: COMBINATORIAL GAME THEORY
# ═══════════════════════════════════════════════════════════════════════════════

# H16: Nim-value of pile 6 is trivially 6. Skip to something interesting.
def h16_nim_value():
    # For single pile Nim, Grundy(n) = n. So Grundy(6) = 6 = n. Tautological.
    detail = "Grundy value of single Nim pile of 6 = 6 = n (tautological for all n)"
    grade = "⚪"
    record("W14-D16", "Nim Grundy(6)=6", grade, detail)

h16_nim_value()

# H17: Tower of Hanoi — min moves = 2^6-1 = 63 = 7*9
def h17_tower_hanoi():
    n = 6
    min_moves = 2**n - 1  # 63

    # 63 = 7 * 9 = (n+1) * (n+3)?? n+1=7, n+3=9. YES!
    factored = (n+1) * (n+3)  # 7*9=63

    # For general n: 2^n - 1 = (n+1)(n+3)?
    # n=4: 15 vs 5*7=35 NO
    # n=5: 31 vs 6*8=48 NO
    # n=6: 63 vs 7*9=63 YES
    # n=7: 127 vs 8*10=80 NO

    check_vals = {}
    for n_test in [4, 5, 6, 7, 8, 10, 12]:
        lhs = 2**n_test - 1
        rhs = (n_test+1)*(n_test+3)
        check_vals[n_test] = (lhs, rhs, lhs==rhs)

    detail = f"Min moves for n=6 Hanoi = 2^6-1 = {min_moves}\n"
    detail += f"  63 = 7*9 = (n+1)*(n+3) = {factored}\n\n"
    detail += "  Check 2^n-1 = (n+1)(n+3) for various n:\n"
    for n_test, (lhs, rhs, match) in check_vals.items():
        detail += f"    n={n_test}: 2^n-1={lhs}, (n+1)(n+3)={rhs}, match={match}\n"

    matches = [n_test for n_test, (_, _, m) in check_vals.items() if m]
    if matches == [6]:
        grade = "🟧"
        detail += f"\n  Unique to n=6: 2^6-1 = 7*9 = (n+1)(n+3)"
        detail += f"\n  But numerical coincidence — no algebraic reason"
    else:
        grade = "⚪"

    record("W14-D17", "2^n-1 = (n+1)(n+3) at n=6", grade, detail)

h17_tower_hanoi()

# H18: Number of domino tilings of 2×n board
def h18_domino_tilings():
    # T(2×n) = Fibonacci(n+1). T(2×6) = Fibonacci(7) = 13
    # Fibonacci: F(1)=1, F(2)=1, F(3)=2, F(4)=3, F(5)=5, F(6)=8, F(7)=13
    def fib(k):
        a, b = 1, 1
        for _ in range(k-2): a, b = b, a+b
        return b

    tilings_2x6 = fib(7)  # 13
    sigma_plus_1 = SIGMA6 + 1  # 12 + 1 = 13

    detail = (f"Domino tilings of 2×6 board = Fib(7) = {tilings_2x6}\n"
              f"  sigma(6) + 1 = {sigma_plus_1}\n"
              f"  13 = sigma(6)+1? {tilings_2x6 == sigma_plus_1}")

    # Check uniqueness: Fib(n+1) = sigma(n)+1?
    # n=10: Fib(11)=89, sigma(10)=1+2+5+10=18, 18+1=19 ≠ 89. NO
    # n=4:  Fib(5)=5, sigma(4)=1+2+4=7, 7+1=8 ≠ 5. NO
    # So 13 = sigma(6)+1 is a numerical coincidence unique to n=6

    check2 = {}
    for n_test in [4, 5, 6, 8, 10, 12]:
        fib_val = fib(n_test+1)
        sig_val = int(divisor_sigma(n_test))
        check2[n_test] = (fib_val, sig_val+1, fib_val == sig_val+1)

    detail += "\n  Check Fib(n+1) = sigma(n)+1:\n"
    for n_test, (fv, sv, match) in check2.items():
        detail += f"    n={n_test}: Fib({n_test+1})={fv}, sigma+1={sv}, match={match}\n"

    matches = [n_test for n_test, (_, _, m) in check2.items() if m]
    if matches == [6]:
        grade = "🟧"
        detail += "\n  Unique but numerical coincidence"
    else:
        grade = "⚪"

    record("W14-D18", "Fib(n+1) = sigma(n)+1 at n=6 (domino tilings)", grade, detail)

h18_domino_tilings()

# H19: 1×n tilings with 1×1 and 1×2 tiles = Fibonacci(n+1)
def h19_strip_tilings():
    # T(1×n) = Fib(n+1) (same recurrence as domino tilings of 2×n)
    # Wait: actually T(1×n) = Fib(n+1) where Fib(1)=1,Fib(2)=1,...
    # For n=6: Fib(7)=13 again
    # For H18 we already handled this. Let's verify and note the equivalence.

    # Actually T(1×n) via {1,2}-compositions: number of compositions of n into parts 1,2
    # This equals Fibonacci(n+1). For n=6: Fib(7)=13. Same as H18. Identical result.

    def tiling_count(n):
        """Count tilings of 1×n with 1×1 and 1×2 tiles (DP)"""
        if n <= 0: return 1
        dp = [0] * (n+1)
        dp[0] = 1
        if n >= 1: dp[1] = 1
        for i in range(2, n+1):
            dp[i] = dp[i-1] + dp[i-2]
        return dp[n]

    t6 = tiling_count(6)  # should be 13

    detail = (f"Tilings of 1×6 strip = {t6} = Fib(7)\n"
              f"  Same result as H18 (domino/strip tilings both = Fib(n+1))\n"
              f"  sigma(6)+1 = 13 — same numerical coincidence as H18\n"
              f"  Graded ⚪ as equivalent to H18 result")
    grade = "⚪"
    record("W14-D19", "1×6 strip tilings = 13 = sigma(6)+1", grade, detail,
           "Duplicate of H18 result")

h19_strip_tilings()

# H20: Actually compute Chomp on 2×6 board Grundy value
def h20_chomp():
    # Chomp on 2×n: First player wins for all n>=2 (strategy stealing argument)
    # The actual Grundy values are hard to compute and well-studied
    # For 2×n Chomp: 2×1 = P-position (lose), 2×n for n>=2: N-position (win)
    # The connection to n=6: 2×6 is a win for first player.
    # Grundy value of 2×6 Chomp: not simply related to n.

    # Let's use a different approach: Wythoff's game
    # Wythoff (a,b) losing positions: a=floor(phi*k), b=floor(phi^2*k) for k=0,1,2,...
    # phi = golden ratio ≈ 1.618...
    phi = (1 + math.sqrt(5)) / 2

    # First 10 Wythoff P-positions (losing positions)
    wythoff_positions = []
    for k in range(1, 15):
        a = int(phi * k)
        b = int(phi**2 * k)
        wythoff_positions.append((a, b))

    # Is (2,6) or (6, something) a Wythoff P-position?
    has_6 = [(a, b) for a, b in wythoff_positions if a == 6 or b == 6]

    detail = (f"Wythoff P-positions (first 14): {wythoff_positions[:14]}\n"
              f"  Positions involving 6: {has_6}\n"
              f"  (a,b) with 6: the pair containing 6 is {has_6[0] if has_6 else 'none in first 14'}\n")

    if has_6:
        a6, b6 = has_6[0]
        other = b6 if a6 == 6 else a6
        detail += f"  6 appears paired with {other} in Wythoff game\n"
        # b = floor(phi^2 * k). If a=6, k=? floor(phi*k)=6 → k≈3.7 → k=4: floor(6.47)=6 ✓
        # b = floor(phi^2*4) = floor(10.47) = 10
        detail += f"  Wythoff pair: (6, 10). Note 10 = sigma(6)-2? No. 10 = 6+4?\n"
        detail += f"  phi^2 * 4 = {phi**2 * 4:.4f} → floor = {int(phi**2 * 4)}\n"
        # (6, 10): sum = 16, diff = 4. 4 = tau(6). 16 = sigma(6)+4?
        diff = abs(a6 - b6) if a6 != b6 else 0
        s = a6 + b6
        detail += f"  (6,10): diff={diff}=tau(6)? {diff==TAU6}. sum={s}.\n"
        if diff == TAU6:
            # Check uniqueness: does n pair with something at distance tau(n)?
            # For n=10: k s.t. floor(phi*k)=10. phi*k=10 → k≈6.18, try k=7: floor(11.33)=11≠10, k=6: floor(9.71)=9≠10
            # Actually Wythoff pairs are indexed differently. Let me just check (10, 10+tau(10))=(10,14)
            # Check if (10,14) is a Wythoff P-position
            wythoff_set = set(tuple(sorted(p)) for p in wythoff_positions[:20])
            check_pairs = []
            for n_test in [6, 10, 12, 28]:
                tau_n = int(divisor_count(n_test))
                candidate = tuple(sorted((n_test, n_test + tau_n)))
                check_pairs.append((n_test, tau_n, candidate, candidate in wythoff_set))
            detail += "  Check (n, n+tau(n)) is Wythoff P-position:\n"
            for n_test, tau_n, cand, is_p in check_pairs:
                detail += f"    n={n_test}: {cand}, is P-position: {is_p}\n"

            n6_unique = all(not is_p for (nt, _, _, is_p) in check_pairs if nt != 6) and \
                        any(is_p for (nt, _, _, is_p) in check_pairs if nt == 6)
            if n6_unique:
                grade = "🟧"
                detail += "  Unique to n=6: Wythoff pair distance = tau(n)"
            else:
                grade = "⚪"
        else:
            grade = "⚪"
    else:
        grade = "⚪"

    record("W14-D20", "Wythoff game: n=6 paired at distance tau(6)", grade, detail)

h20_chomp()

# ═══════════════════════════════════════════════════════════════════════════════
# E: ANALYTIC FUNCTIONS AT SPECIAL POINTS
# ═══════════════════════════════════════════════════════════════════════════════

# H21: Riemann xi function ξ(1/2)
def h21_xi_at_half():
    # ξ(s) = s(s-1)/2 * π^(-s/2) * Γ(s/2) * ζ(s)
    # At s=1/2 (GZ_upper):
    # ξ(1/2) = (1/2)(-1/2)/2 * π^(-1/4) * Γ(1/4) * ζ(1/2)
    # ζ(1/2) ≈ -1.4603545...

    try:
        import mpmath
        mpmath.mp.dps = 30
        # Compute xi(s) = s(s-1)/2 * pi^(-s/2) * Gamma(s/2) * zeta(s)
        s = mpmath.mpf('0.5')
        zeta_half = float(mpmath.zeta(s))
        # xi(1/2) = (1/2)(-1/2)/2 * pi^(-1/4) * Gamma(1/4) * zeta(1/2)
        xi_half = float(s*(s-1)/2 * mpmath.pi**(-s/2) * mpmath.gamma(s/2) * mpmath.zeta(s))

        detail = (f"ξ(1/2) = {xi_half:.10f}\n"
                  f"  ζ(1/2) = {zeta_half:.10f}\n"
                  f"  ξ(s) = ξ(1-s) by functional equation, so ξ(1/2) is real\n"
                  f"  GZ_upper = 1/2 is the fixed point of s → 1-s\n"
                  f"  ξ(1/2) ≈ {xi_half:.6f}")

        # Is ξ(1/2) related to 1/e or other GZ constants?
        ratio_to_inv_e = xi_half / GZ_CENTER
        detail += f"\n  ξ(1/2) / (1/e) = {ratio_to_inv_e:.6f}"
        detail += f"\n  No algebraic identity connecting ξ(1/2) to GZ constants"

    except ImportError:
        detail = "mpmath not available for ξ(1/2) computation"

    grade = "⚪"
    detail += "\n  ξ(1/2) is well-known but not specifically tied to n=6"
    record("W14-E21", "xi(1/2) at GZ upper", grade, detail)

h21_xi_at_half()

# H22-H25: Special values of modular forms
def h22_to_h25_modular():
    # These require high-precision complex analysis. We compute what we can
    # and grade based on whether n=6 properties emerge.

    try:
        import mpmath
        mpmath.mp.dps = 30

        # H22: θ_3(0, e^{-π}) and connection to GZ
        # Jacobi theta: θ_3(0, q) = Σ q^{n²}
        # At q = e^{-π}: θ_3(0, e^{-π}) = π^{1/4}/Γ(3/4) (known exact value)
        theta3_known = float(mpmath.pi**(0.25) / mpmath.gamma(0.75))
        theta3_computed = float(mpmath.jtheta(3, 0, mpmath.exp(-mpmath.pi)))

        # H23: Dedekind eta at τ=i: η(i) = Γ(1/4)/(2π^{3/4})
        eta_i_known = float(mpmath.gamma(0.25) / (2 * mpmath.pi**(0.75)))
        eta_i_computed = abs(complex(mpmath.eta(1j)))

        # η(6i): at τ=6i (involves n=6)
        eta_6i = complex(mpmath.eta(6j))
        eta_6i_abs = abs(eta_6i)

        detail22 = (f"H22: θ_3(0, e^{{-π}}) = π^(1/4)/Γ(3/4)\n"
                    f"  Known = {theta3_known:.8f}, Computed = {theta3_computed:.8f}\n"
                    f"  Match: {abs(theta3_known - theta3_computed) < 1e-10}\n"
                    f"  No specific n=6 connection — general formula")

        detail23 = (f"H23: η(i) = Γ(1/4)/(2π^(3/4))\n"
                    f"  Known = {eta_i_known:.8f}, Computed = {abs(eta_i_computed):.8f}\n"
                    f"  η(6i) = {eta_6i_abs:.8f} (absolute value)\n"
                    f"  Ratio η(6i)/η(i) = {eta_6i_abs/abs(eta_i_computed):.8f}")

        # η(nτ)/η(τ) ratios appear in modular equations of level n
        # For n=6: this is a level-6 modular form. Any special value?
        eta_ratio = eta_6i_abs / abs(eta_i_computed)
        detail23 += f"\n  |η(6i)/η(i)| = {eta_ratio:.6f}"
        detail23 += f"\n  No simple GZ constant emerges"

        # H24: j-invariant at τ=i√6
        try:
            j_val = complex(mpmath.jtheta(3, 0, mpmath.exp(1j * mpmath.pi * mpmath.sqrt(6))))
            detail24 = f"H24: j(i√6) computation attempted\n  j-invariant at CM point τ=i√6\n  Class number h(-24)=2 → j satisfies quadratic over Q"
        except Exception as e:
            detail24 = f"H24: j(i√6) — CM theory: τ=i√6, disc=-24, h(-24)=2\n  j satisfies x^2 + ax + b = 0 over Q (degree 2 class poly)\n  Not computed due to complexity"

        # H25: Weierstrass ℘ on Z+Z·i√6
        detail25 = (f"H25: ℘ function on lattice Λ = Z + Z·i√6\n"
                    f"  This is a CM lattice (imaginary quadratic field Q(√-6))\n"
                    f"  Periods involve special values of Γ and Lemniscate\n"
                    f"  For CM lattice with disc -D, periods ~ Γ values at fractions\n"
                    f"  Connection to n=6: √6 involves both prime factors of 6")

    except ImportError:
        detail22 = "mpmath not available"
        detail23 = "mpmath not available"
        detail24 = "mpmath not available"
        detail25 = "mpmath not available"

    record("W14-E22", "θ_3(0,e^{-π}) = π^(1/4)/Γ(3/4)", "⚪", detail22,
           "General theta function identity, not n=6 specific")
    record("W14-E23", "η(6i) modular form at n=6", "⚪", detail23)
    record("W14-E24", "j(i√6) CM value, disc=-24, h=2", "⚪", detail24,
           "CM theory — degree 2 because class number h(-24)=2")
    record("W14-E25", "Weierstrass ℘ on Z+Z·i√6 CM lattice", "⚪", detail25)

h22_to_h25_modular()

# ═══════════════════════════════════════════════════════════════════════════════
# BONUS: Dig deeper on 🟩 candidates
# ═══════════════════════════════════════════════════════════════════════════════

# Extra: verify H15 algebraically more carefully
def h15_extra_verification():
    """(n-3)! = n has unique solution n=6 among integers n>=4"""
    # Proof:
    # n=4: 1!=1≠4
    # n=5: 2!=2≠5
    # n=6: 3!=6=6 ✓
    # n=7: 4!=24≠7
    # For n>=7: (n-3)! >= 4! = 24 > 7, and grows faster than n → no more solutions

    # So the identity (n-3)! = n has a UNIQUE solution n=6. Algebraically provable.
    solutions = [n for n in range(1, 50) if math.factorial(max(0, n-3)) == n]
    detail = (f"Equation (n-3)! = n: solutions = {solutions}\n"
              f"  Only n=6 satisfies this for n>=4\n"
              f"  Proof: n>=7 → (n-3)!>=4!=24>n for n<24, then (n-3)! grows as factorial >> linear\n"
              f"  This means: only n=6 has |χ(M_{{0,n}})| = n")
    record("W14-C15b", "Algebraic proof: (n-3)!=n unique at n=6", "🟩", detail)

h15_extra_verification()

# Extra: Verify H05 more carefully
def h05_extra():
    """(6-1)(6-2)(6-3) = lcm(1..6) = 60"""
    # Verify: lcm(1..6) = lcm(1,2,3,4,5,6)
    # = 2^2 * 3 * 5 = 60
    # (n-1)(n-2)(n-3) for n=6: 5*4*3 = 60 ✓
    # But WHY?
    # lcm(1..6) = lcm(1..5) * 6/gcd(lcm(1..5), 6)
    # lcm(1..5) = 60, gcd(60, 6) = 6, so lcm(1..6) = 60 * 6/6 = 60
    # Interesting: lcm(1..6) = lcm(1..5) because 6=2*3 and both 2,3 already in lcm(1..5)
    # So lcm(1..6) = lcm(1..5) = 60
    # And (n-1)(n-2)(n-3) = 5*4*3 = 60. Is this a coincidence?
    # (n-1)(n-2)(n-3) = (n-1)!/(n-4)! = P(n-1, 3) = falling factorial
    # For n=6: P(5,3) = 5*4*3 = 60 = lcm(1..6)
    # For n=5: P(4,3) = 4*3*2 = 24. lcm(1..5) = 60. 24≠60.
    # So specific to n=6.
    import math
    lcm_6 = 1
    for i in range(1, 7): lcm_6 = lcm_6 * i // math.gcd(lcm_6, i)

    detail = (f"(n-1)(n-2)(n-3) = 5*4*3 = 60 = lcm(1..6) = {lcm_6}\n"
              f"  Key: lcm(1..6) = lcm(1..5) = 60 (since 6=2*3, both already in lcm)\n"
              f"  P(n-1, 3) = (n-1)(n-2)(n-3) = 60 for n=6\n"
              f"  This is numerical coincidence between falling factorial and lcm\n"
              f"  No algebraic identity — just both equal 60 for n=6")
    grade = "⚪"
    detail += "\n  Reclassified ⚪: no algebraic reason beyond shared value"
    record("W14-A05b", "(n-1)(n-2)(n-3) = lcm(1..n) reclassified", grade, detail)

h05_extra()

# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

def print_summary():
    grade_counts = {}
    for r in results:
        g = r['grade']
        grade_counts[g] = grade_counts.get(g, 0) + 1

    print("\n" + "="*70)
    print("WAVE 14 RESULTS")
    print("="*70)

    for r in results:
        print(f"\n[{r['num']}] {r['grade']} {r['title']}")
        for line in r['detail'].split('\n'):
            print(f"  {line}")
        if r['uniqueness']:
            print(f"  >> {r['uniqueness']}")

    print("\n" + "="*70)
    print("GRADE SUMMARY")
    print("="*70)
    for grade, count in sorted(grade_counts.items()):
        print(f"  {grade}: {count}")

    total = len(results)
    green = grade_counts.get("🟩", 0)
    orange_star = grade_counts.get("🟧★", 0)
    orange = grade_counts.get("🟧", 0)
    white = grade_counts.get("⚪", 0)

    print(f"\n  Total: {total}")
    print(f"  Non-trivial (🟩+🟧★+🟧): {green + orange_star + orange}")
    print(f"  Trivial/Tautological (⚪): {white}")

    # Previous cumulative
    prev_cum = 221
    new_green = green + orange_star
    new_total = total
    print(f"\n  This wave new discoveries: {new_green} 🟩/🟧★")
    print(f"  Previous cumulative: {prev_cum}/325")
    print(f"  Wave 14 hypotheses tested: {new_total}")

print_summary()
