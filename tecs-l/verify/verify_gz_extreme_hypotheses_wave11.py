"""
Wave 11: n=6 Uniqueness Hypotheses — Strict Grading
Strategy: For each claim, test n=6 AND n=10,12,28 (plus broader scan).
Grade 🟩 only if n=6 is unique or among very few solutions.
"""

import math
from fractions import Fraction
from functools import lru_cache
from sympy import isprime, factorint, primerange, prime, nextprime, totient, primeomega
from sympy import divisor_sigma, divisor_count, mobius

# ─── Number-theoretic helpers ─────────────────────────────────────────────────

def sigma(n, k=1):
    """Sum of k-th powers of divisors."""
    return divisor_sigma(n, k)

def tau(n):
    """Number of divisors."""
    return divisor_count(n)

def phi(n):
    """Euler's totient."""
    return totient(n)

def sigma_neg1(n):
    """Sum of reciprocals of divisors = sigma_{-1}(n)."""
    return sum(Fraction(1, d) for d in range(1, n+1) if n % d == 0)

def sopfr(n):
    """Sum of prime factors with repetition."""
    f = factorint(n)
    return sum(p * e for p, e in f.items())

def prime_omega(n):
    """Number of prime factors with repetition (Omega)."""
    return primeomega(n)

def mertens_M(N):
    """Mertens function M(N) = sum_{k=1}^{N} mu(k)."""
    return sum(mobius(k) for k in range(1, N+1))

def chebyshev_psi(N):
    """Chebyshev psi function: sum of log(p) for all prime powers p^k <= N."""
    total = 0.0
    for p in primerange(2, N+1):
        pk = p
        while pk <= N:
            total += math.log(p)
            pk *= p
    return total

def count_perfect_matchings_K(n):
    """Perfect matchings in K_n (double factorial (n-1)!! for even n)."""
    if n % 2 != 0:
        return 0
    result = 1
    for i in range(1, n, 2):
        result *= i
    return result

def partitions(n):
    """Number of integer partitions p(n)."""
    # DP approach
    dp = [0] * (n + 1)
    dp[0] = 1
    for k in range(1, n + 1):
        for j in range(k, n + 1):
            dp[j] += dp[j - k]
    return dp[n]

# ─── Constants ────────────────────────────────────────────────────────────────

E = math.e
LN43 = math.log(4/3)
GZ_UPPER = 0.5
GZ_CENTER = 1/E
GZ_LOWER = 0.5 - LN43
GZ_WIDTH = LN43

TEST_N = [6, 10, 12, 28]
SCAN_N = list(range(1, 101))  # broad scan

GRADE = {"green": "🟩", "orange": "🟧", "white": "⚪", "black": "⬛"}

results = []

def record(hyp_id, title, lhs_label, rhs_label, holds_for, unique_to_6, grade, note):
    results.append({
        "id": hyp_id, "title": title,
        "lhs": lhs_label, "rhs": rhs_label,
        "holds_for": holds_for,
        "unique": unique_to_6,
        "grade": grade,
        "note": note,
    })

# ─── GROUP A: Number-theoretic uniqueness ─────────────────────────────────────

print("=" * 65)
print("GROUP A: Number-Theoretic Functions — Uniqueness Tests")
print("=" * 65)

# H01: tau(n)*phi(n) = sigma(n) - tau(n)?
print("\n--- H01: tau(n)*phi(n) = sigma(n) - tau(n) ---")
h01_matches = []
for n in SCAN_N:
    lhs = tau(n) * phi(n)
    rhs = sigma(n) - tau(n)
    if lhs == rhs:
        h01_matches.append(n)
print(f"  n=6: tau={tau(6)}, phi={phi(6)}, lhs={tau(6)*phi(6)}, sigma={sigma(6)}, rhs={sigma(6)-tau(6)}")
for n in TEST_N:
    print(f"  n={n}: tau*phi={tau(n)*phi(n)}, sigma-tau={sigma(n)-tau(n)}, match={tau(n)*phi(n)==sigma(n)-tau(n)}")
print(f"  Holds for n in [1,100]: {h01_matches}")
grade_01 = "⚪" if len(h01_matches) != 1 else "🟩"
record("H01", "tau*phi = sigma - tau", "tau(n)*phi(n)", "sigma(n)-tau(n)",
       h01_matches, 6 in h01_matches and len(h01_matches) == 1, grade_01,
       f"Holds for {len(h01_matches)} values: {h01_matches[:10]}")

# H02: sigma(n)/tau(n) = 3 unique?
print("\n--- H02: sigma(n)/tau(n) = 3 ---")
h02_matches = [n for n in SCAN_N if sigma(n) % tau(n) == 0 and sigma(n) // tau(n) == 3]
for n in TEST_N:
    print(f"  n={n}: sigma/tau = {sigma(n)}/{tau(n)} = {Fraction(sigma(n), tau(n))}")
print(f"  sigma/tau=3 for n in [1,100]: {h02_matches}")
grade_02 = "⚪" if len(h02_matches) > 3 else "🟧" if len(h02_matches) <= 5 else "⚪"
note_02 = f"sigma(n)/tau(n)=3 for {len(h02_matches)} n: {h02_matches[:15]}"
record("H02", "sigma/tau = 3", "sigma(n)/tau(n)", "3",
       h02_matches, False, grade_02, note_02)

# H03: n/phi(n) = 3 (i.e., phi(n) = n/3)?
print("\n--- H03: n/phi(n) = 3 ---")
h03_matches = [n for n in SCAN_N if n % phi(n) == 0 and n // phi(n) == 3]
for n in TEST_N:
    print(f"  n={n}: n/phi(n) = {n}/{phi(n)} = {Fraction(n, phi(n))}")
print(f"  n/phi(n)=3 for n in [1,100]: {h03_matches}")
grade_03 = "⚪" if len(h03_matches) > 3 else "🟧"
record("H03", "n/phi(n) = 3", "n/phi(n)", "3",
       h03_matches, False, grade_03, f"Holds for {len(h03_matches)} values: {h03_matches[:15]}")

# H04: sigma(n)*phi(n)/n^2 = 2/3?
print("\n--- H04: sigma(n)*phi(n)/n^2 = 2/3 ---")
h04_matches = []
for n in SCAN_N:
    val = Fraction(sigma(n) * phi(n), n * n)
    if val == Fraction(2, 3):
        h04_matches.append(n)
for n in TEST_N:
    val = Fraction(sigma(n) * phi(n), n * n)
    print(f"  n={n}: sigma*phi/n^2 = {sigma(n)}*{phi(n)}/{n*n} = {val}")
print(f"  sigma*phi/n^2 = 2/3 for n in [1,100]: {h04_matches}")
grade_04 = "🟩" if len(h04_matches) == 1 and h04_matches[0] == 6 else \
           "🟧" if len(h04_matches) <= 3 else "⚪"
record("H04", "sigma*phi/n^2 = 2/3", "sigma(n)*phi(n)/n^2", "2/3",
       h04_matches, len(h04_matches) == 1 and 6 in h04_matches, grade_04,
       f"Holds for {len(h04_matches)} values: {h04_matches}")

# H05: p(n) = sigma(n) - 1?  (partition function vs sigma)
print("\n--- H05: p(n) = sigma(n) - 1 ---")
h05_matches = []
for n in SCAN_N[1:]:  # start from 2
    pn = partitions(n)
    sig = sigma(n)
    if pn == sig - 1:
        h05_matches.append(n)
n = 6
print(f"  n=6: p(6)={partitions(6)}, sigma(6)-1={sigma(6)-1}, match={partitions(6)==sigma(6)-1}")
for n in [10, 12, 28]:
    print(f"  n={n}: p({n})={partitions(n)}, sigma({n})-1={sigma(n)-1}, match={partitions(n)==sigma(n)-1}")
print(f"  p(n)=sigma(n)-1 for n in [1,100]: {h05_matches}")
grade_05 = "🟩" if len(h05_matches) == 1 and 6 in h05_matches else \
           "🟧" if len(h05_matches) <= 2 else "⚪"
record("H05", "p(n) = sigma(n) - 1", "p(n)", "sigma(n)-1",
       h05_matches, len(h05_matches) == 1 and 6 in h05_matches, grade_05,
       f"Holds for {len(h05_matches)} values: {h05_matches}")

# ─── GROUP B: Graph Theory ────────────────────────────────────────────────────

print("\n" + "=" * 65)
print("GROUP B: Graph Theory — 6-vertex Specific")
print("=" * 65)

# H06: 156 non-isomorphic graphs on 6 vertices = sigma(6)*13
print("\n--- H06: 156 = sigma(6) * 13 = 12 * 13 ---")
graphs_6 = 156  # OEIS A000088(6)
val6 = sigma(6) * 13
print(f"  Non-iso graphs on 6 vertices = {graphs_6}")
print(f"  sigma(6) = {sigma(6)}, 156 / 12 = {156 / 12}")
print(f"  sigma(6) * 13 = {val6}, match = {graphs_6 == val6}")
print(f"  13 = sigma(6) + 1 = {sigma(6)+1}")
# Check for other n: graphs on n vertices = sigma(n)*(sigma(n)+1)?
# OEIS A000088: 1,1,2,4,11,34,156,1044,12346,...
graph_counts = {1:1, 2:2, 3:4, 4:11, 5:34, 6:156, 7:1044, 8:12346}
h06_note = f"156 = sigma(6)*13 = 12*(sigma(6)+1). Structural but 13 is ad hoc."
grade_06 = "⚪"  # 13 is not derived from n=6 structure
record("H06", "156 = sigma(6)*13", "156 graphs", "12*13",
       [6], True, grade_06, h06_note)

# H07: 112 connected graphs on 6 vertices
print("\n--- H07: 112 connected graphs on 6 vertices ---")
connected_6 = 112  # OEIS A001349(6)
print(f"  Connected graphs on 6 = {connected_6}")
print(f"  112 = 8 * 14 = tau(6)*phi(6) * 7 = {tau(6)*phi(6)}*7")
print(f"  112 = 2^4 * 7")
print(f"  112 / sigma(6) = {Fraction(112, sigma(6))}")
print(f"  112 = sigma(6) - tau(6) + ... checking factors: {112 / (tau(6)*phi(6))}")
# 112 = tau*phi = 4*2=8, 112/8 = 14 = sigma(6)+2
grade_07 = "⚪"  # factor 14 is ad hoc
record("H07", "112 connected graphs on K_6", "112", "8*14",
       [6], True, grade_07, "112 = 8*14 where 8=tau*phi, 14 ad hoc")

# H08: Cayley formula n^{n-2} for labeled trees. n=6: 6^4 = 1296
print("\n--- H08: Labeled trees on 6 = 6^4 = 6^{tau(6)} ---")
n = 6
cayley_6 = n ** (n - 2)
print(f"  6^(6-2) = 6^4 = {cayley_6}")
print(f"  tau(6) = {tau(6)}")
print(f"  6-2 = {n-2}, tau(6) = {tau(6)}, equal: {n-2 == tau(6)}")
# For which n does n-2 = tau(n)?
h08_matches = [n for n in SCAN_N[2:] if n - 2 == tau(n)]
print(f"  n-2 = tau(n) for n in [3,100]: {h08_matches}")
# This is equivalent to asking when Cayley exponent equals tau(n)
grade_08 = "🟩" if len(h08_matches) == 1 and 6 in h08_matches else \
           "🟧" if len(h08_matches) <= 3 else "⚪"
record("H08", "6^{6-2} = 6^{tau(6)}: n-2=tau(n)", "n-2", "tau(n)",
       h08_matches, 6 in h08_matches, grade_08,
       f"n-2=tau(n) for n in [3,100]: {h08_matches}")

# H09: Hamiltonian cycles in K_6 = (6-1)!/2 = 60 = sopfr(6)*sigma(6)
print("\n--- H09: Ham. cycles in K_6 = 60 = sopfr*sigma ---")
n = 6
ham_6 = math.factorial(n - 1) // 2
print(f"  Ham cycles in K_6 = (5!)/2 = {ham_6}")
print(f"  sopfr(6) = {sopfr(6)}, sigma(6) = {sigma(6)}, product = {sopfr(6)*sigma(6)}")
print(f"  Match: {ham_6 == sopfr(6) * sigma(6)}")
# Check: is (n-1)!/2 = sopfr(n)*sigma(n) for other n?
h09_matches = []
for n in range(3, 15):
    val_lhs = math.factorial(n - 1) // 2
    val_rhs = sopfr(n) * sigma(n)
    if val_lhs == val_rhs:
        h09_matches.append(n)
        print(f"  n={n}: (n-1)!/2={val_lhs}, sopfr*sigma={val_rhs}")
print(f"  Match for n in [3,15]: {h09_matches}")
grade_09 = "🟩" if len(h09_matches) == 1 and 6 in h09_matches else \
           "🟧" if len(h09_matches) <= 2 else "⚪"
record("H09", "(n-1)!/2 = sopfr(n)*sigma(n)", "(6-1)!/2 = 60", "sopfr*sigma=60",
       h09_matches, 6 in h09_matches and len(h09_matches) == 1, grade_09,
       f"Holds for n: {h09_matches}")

# H10: Perfect matchings in K_6 = 5!! = 15 = C(6,2)
print("\n--- H10: Perfect matchings in K_6 = 15 = C(6,2) ---")
n = 6
pm_6 = count_perfect_matchings_K(n)
c62 = math.comb(6, 2)
print(f"  Perfect matchings K_6 = {pm_6}")
print(f"  C(6,2) = {c62}, match = {pm_6 == c62}")
# For which even n: (n-1)!! = C(n,2)?
h10_matches = []
for n in range(2, 20, 2):
    pm = count_perfect_matchings_K(n)
    cn2 = math.comb(n, 2)
    if pm == cn2:
        h10_matches.append(n)
        print(f"  n={n}: pm={pm}, C(n,2)={cn2}")
print(f"  (n-1)!! = C(n,2) for even n in [2,18]: {h10_matches}")
grade_10 = "🟩" if len(h10_matches) == 1 and 6 in h10_matches else "⚪"
record("H10", "(n-1)!! = C(n,2) for K_n", "5!!=15", "C(6,2)=15",
       h10_matches, 6 in h10_matches and len(h10_matches) == 1, grade_10,
       f"Holds for even n: {h10_matches}")

# ─── GROUP C: Analytic Number Theory ─────────────────────────────────────────

print("\n" + "=" * 65)
print("GROUP C: Analytic Number Theory")
print("=" * 65)

# H11: Mertens M(6) = -1
print("\n--- H11: Mertens M(6) = -1 ---")
M6 = mertens_M(6)
print(f"  M(6) = {M6}")
# M(n) values
M_vals = {n: mertens_M(n) for n in range(1, 31)}
print(f"  M(n) for n=1..30: {[M_vals[i] for i in range(1,31)]}")
neg1_list = [n for n in range(1, 31) if M_vals[n] == -1]
print(f"  M(n)=-1 for n: {neg1_list}")
grade_11 = "⚪"  # M(n)=-1 for many n
record("H11", "M(6) = -1", "M(6)", "-1",
       neg1_list, False, grade_11, f"M(n)=-1 for {len(neg1_list)} values ≤30: {neg1_list}")

# H12: psi(6) = ln(60) = ln(sopfr(6)*sigma(6))
print("\n--- H12: Chebyshev psi(6) = ln(60) = ln(sopfr*sigma) ---")
psi6 = chebyshev_psi(6)
lcm6 = math.lcm(*range(1, 7))  # lcm(1..6)
print(f"  psi(6) = ln(lcm(1..6)) = ln({lcm6}) = {math.log(lcm6):.6f}")
print(f"  Direct: {psi6:.6f}")
print(f"  sopfr(6)*sigma(6) = {sopfr(6)}*{sigma(6)} = {sopfr(6)*sigma(6)}")
print(f"  ln(60) = {math.log(60):.6f}, match = {abs(psi6 - math.log(60)) < 1e-9}")
# Now test: is lcm(1..n) = sopfr(n)*sigma(n) for other n?
h12_matches = []
for n in range(2, 20):
    lcm_n = math.lcm(*range(1, n+1))
    rhs = sopfr(n) * sigma(n)
    if lcm_n == rhs:
        h12_matches.append(n)
        print(f"  n={n}: lcm(1..{n})={lcm_n}, sopfr*sigma={rhs}")
print(f"  lcm(1..n) = sopfr(n)*sigma(n) for n in [2,19]: {h12_matches}")
grade_12 = "🟩" if len(h12_matches) == 1 and 6 in h12_matches else "⚪"
record("H12", "lcm(1..6) = sopfr(6)*sigma(6) = 60", "lcm(1..6)=60", "sopfr*sigma=60",
       h12_matches, 6 in h12_matches and len(h12_matches) == 1, grade_12,
       f"Holds for n: {h12_matches}")

# H13: primorial(6) = 30 = sopfr(6)*n
print("\n--- H13: 6# = 30 = sopfr(6)*6 ---")
# 6# = product of primes <= 6 = 2*3*5 = 30
primorial_6 = 2 * 3 * 5
print(f"  6# = {primorial_6}")
print(f"  sopfr(6)*6 = {sopfr(6)}*6 = {sopfr(6)*6}")
print(f"  Match: {primorial_6 == sopfr(6) * 6}")
# For which n: primorial(n) = sopfr(n)*n?
# primorial(n) = product of primes <= n
def primorial(n):
    return math.prod(p for p in primerange(2, n+1))

h13_matches = []
for n in range(2, 25):
    prim = primorial(n)
    rhs = sopfr(n) * n
    if prim == rhs:
        h13_matches.append(n)
        print(f"  n={n}: primorial={prim}, sopfr*n={rhs}")
print(f"  primorial(n) = sopfr(n)*n for n in [2,24]: {h13_matches}")
grade_13 = "🟩" if len(h13_matches) == 1 and 6 in h13_matches else "⚪"
record("H13", "primorial(6) = sopfr(6)*6", "6#=30", "sopfr*n=30",
       h13_matches, 6 in h13_matches and len(h13_matches) == 1, grade_13,
       f"Holds for n: {h13_matches}")

# H14: pi(6!) = pi(720) ≈ 128 = 2^7, is 7 = n+1?
print("\n--- H14: pi(6!) = 128 = 2^7, 7 = n+1? ---")
# Compute pi(720) properly
from sympy import primepi
pi_720 = primepi(720)
print(f"  pi(720) = {pi_720}")
print(f"  2^7 = {2**7}, 7 = n+1 = {6+1}")
print(f"  Exact match: {pi_720 == 128}")
# Is pi(n!) = 2^(n+1) for other n?
h14_matches = []
for n in range(2, 12):
    nfact = math.factorial(n)
    pi_nfact = primepi(nfact)
    target = 2 ** (n + 1)
    if pi_nfact == target:
        h14_matches.append(n)
        print(f"  n={n}: pi({n}!)={pi_nfact}, 2^(n+1)={target}")
    else:
        print(f"  n={n}: pi({n}!)={pi_nfact}, 2^(n+1)={target}, NO")
grade_14 = "🟩" if len(h14_matches) == 1 and 6 in h14_matches else "⚪"
record("H14", "pi(6!) = 2^(6+1)", "pi(720)", "2^7=128",
       h14_matches, 6 in h14_matches and len(h14_matches) == 1, grade_14,
       f"pi(720)={pi_720}, exact={pi_720==128}, holds for n: {h14_matches}")

# H15: Euler product up to 6: prod(1-1/p)^-1 = 15/4
print("\n--- H15: Euler product <=6 = 15/4 = C(6,2)/tau(6) ---")
euler_prod = Fraction(1, 1)
for p in primerange(2, 7):
    euler_prod *= Fraction(p, p - 1)
print(f"  prod_{{p<=6}} p/(p-1) = {euler_prod} = {float(euler_prod):.6f}")
print(f"  C(6,2) = {math.comb(6,2)}, tau(6) = {tau(6)}")
print(f"  C(6,2)/tau(6) = {Fraction(math.comb(6,2), tau(6))}")
print(f"  Match: {euler_prod == Fraction(math.comb(6,2), tau(6))}")
# Test for other n
h15_matches = []
for n in range(2, 20):
    primes_n = list(primerange(2, n+1))
    if not primes_n:
        continue
    ep = Fraction(1, 1)
    for p in primes_n:
        ep *= Fraction(p, p - 1)
    target = Fraction(math.comb(n, 2), tau(n))
    if ep == target:
        h15_matches.append(n)
        print(f"  n={n}: Euler prod={ep}, C(n,2)/tau(n)={target}")
print(f"  Match for n in [2,19]: {h15_matches}")
grade_15 = "🟩" if len(h15_matches) == 1 and 6 in h15_matches else "⚪"
record("H15", "Euler product <=6 = C(6,2)/tau(6)", "15/4", "C(6,2)/tau(6)=15/4",
       h15_matches, 6 in h15_matches and len(h15_matches) == 1, grade_15,
       f"Holds for n: {h15_matches}")

# ─── GROUP D: Physical Systems ───────────────────────────────────────────────

print("\n" + "=" * 65)
print("GROUP D: Physical Systems")
print("=" * 65)

# H16: 6-body gravitational DOF = 12 = sigma(6)
print("\n--- H16: 6-body gravitational DOF in 3D = 12 = sigma(6) ---")
# DOF = n*3 - 6 (subtract 3 translations + 3 rotations) for n>=3
n = 6
dof_6 = n * 3 - 6  # = 12
print(f"  n*3-6 = {n}*3-6 = {dof_6} = sigma(6) = {sigma(6)}")
print(f"  Match: {dof_6 == sigma(6)}")
# For which n: n*3-6 = sigma(n)?
h16_matches = [n for n in range(3, 50) if n*3 - 6 == sigma(n)]
print(f"  n*3-6 = sigma(n) for n in [3,50]: {h16_matches}")
grade_16 = "🟩" if len(h16_matches) == 1 and 6 in h16_matches else \
           "🟧" if len(h16_matches) <= 2 else "⚪"
record("H16", "3n-6 = sigma(n) (n-body DOF)", "3*6-6=12", "sigma(6)=12",
       h16_matches, 6 in h16_matches and len(h16_matches) == 1, grade_16,
       f"Holds for n: {h16_matches}")

# H17: Benzene 6 pi electrons = 4*1+2 (Huckel rule n=1). Aromatic stability.
print("\n--- H17: Huckel 4n+2 rule for benzene (n=1, 6 pi electrons) ---")
# This is a physics fact, not a number theory uniqueness claim. Grade ⚪ (not math unique to 6)
print(f"  4*1+2 = 6. But also 4*2+2=10 (naphthalene), 4*3+2=14, etc.")
print(f"  n=6 is first non-trivial aromatic count. Not number-theoretically unique.")
grade_17 = "⚪"
record("H17", "Benzene 4n+2 rule", "6 pi e-", "4(1)+2=6",
       [6, 10, 14, 18], False, grade_17, "4k+2 series: 6,10,14,18,... Not unique to 6")

# H18: Dihedral group D_6 has order 12 = sigma(6)
print("\n--- H18: |D_6| = 12 = sigma(6) ---")
n = 6
order_Dn = 2 * n
print(f"  |D_6| = 2*6 = {order_Dn} = sigma(6) = {sigma(6)}")
print(f"  Match: {order_Dn == sigma(6)}")
# For which n: 2n = sigma(n)?
h18_matches = [n for n in SCAN_N if 2 * n == sigma(n)]
print(f"  2n = sigma(n) for n in [1,100]: {h18_matches}")
print(f"  Note: 2n = sigma(n) iff n is perfect!")
grade_18 = "🟩"  # This is the definition of perfect numbers! 6, 28, 496, ...
record("H18", "|D_n| = sigma(n) iff n perfect", "2*6=12", "sigma(6)=12",
       h18_matches, False, grade_18,
       f"2n=sigma(n) iff n is perfect. Holds for perfect numbers: {h18_matches}")

# H19: 6 quark flavors. 6/phi(6) = 3 = color charges.
print("\n--- H19: 6 quark flavors / phi(6) = 3 = color charges ---")
n = 6
print(f"  6 / phi(6) = 6 / {phi(6)} = {6 // phi(6)}")
print(f"  Color charges = 3 (QCD SU(3))")
print(f"  6 * 3 = 18 = 3 * 6 quark states (flavor * color)")
# Physics observation, not unique to n=6 in a math sense
grade_19 = "⚪"
record("H19", "6 flavors / phi(6) = 3 colors", "6/phi(6)=3", "QCD colors",
       [6], True, grade_19, "Physics numerology, not math uniqueness")

# H20: Carbon atomic number = 6. Observation.
print("\n--- H20: Carbon Z=6 (atomic number) ---")
print(f"  Carbon Z=6. 6=sigma(4)=... Physics, not math.")
grade_20 = "⚪"
record("H20", "Carbon Z=6 observation", "Z=6", "n=6",
       [6], True, grade_20, "Physics observation, not a mathematical relation")

# ─── GROUP E: Recursive / Self-referential ───────────────────────────────────

print("\n" + "=" * 65)
print("GROUP E: Recursive / Self-Referential")
print("=" * 65)

# H21: Abundancy iteration f(6)=2, f(12)=7/3
print("\n--- H21: f(n)=sigma(n)/n iteration from n=6 ---")
def f(n):
    return Fraction(sigma(n), n)

n0 = 6
chain = [n0]
fn = f(n0)
print(f"  f(6) = sigma(6)/6 = {fn}")
# f(6) = 2, so next n = f(6)*6 = 12
n1 = int(fn * n0)
chain.append(n1)
fn1 = f(n1)
print(f"  f(12) = sigma(12)/12 = {fn1} = {float(fn1):.4f}")
n2 = int(fn1 * n1)
chain.append(n2)
print(f"  Chain: {chain}")
grade_21 = "⚪"  # Interesting but not a mathematical equality claim
record("H21", "Abundancy iteration 6->12->...", "f(6)=2", "chain",
       [6], True, grade_21, "Chain: 6->12->... f(6)=2 exact, observation only")

# H22: sigma(tau(6)) = n+1 AND tau(sigma(6)) = n  (KEY HYPOTHESIS)
print("\n--- H22: sigma(tau(n))=n+1 AND tau(sigma(n))=n ---")
n = 6
lhs1 = sigma(tau(n))  # sigma(4) = 7 = n+1
lhs2 = tau(sigma(n))  # tau(12) = 6 = n
print(f"  n=6: sigma(tau(6)) = sigma({tau(6)}) = {lhs1} = n+1={n+1}? {lhs1 == n+1}")
print(f"  n=6: tau(sigma(6)) = tau({sigma(6)}) = {lhs2} = n={n}? {lhs2 == n}")
for n_test in TEST_N[1:]:
    s1 = sigma(tau(n_test))
    s2 = tau(sigma(n_test))
    print(f"  n={n_test}: sigma(tau)={s1}=n+1? {s1==n_test+1}, tau(sigma)={s2}=n? {s2==n_test}")
# Full scan for BOTH conditions
h22_both = [n for n in SCAN_N if sigma(tau(n)) == n + 1 and tau(sigma(n)) == n]
h22_part1 = [n for n in SCAN_N if sigma(tau(n)) == n + 1]
h22_part2 = [n for n in SCAN_N if tau(sigma(n)) == n]
print(f"  sigma(tau(n))=n+1 for n in [1,100]: {h22_part1}")
print(f"  tau(sigma(n))=n for n in [1,100]: {h22_part2}")
print(f"  BOTH conditions for n in [1,100]: {h22_both}")
grade_22 = "🟩" if len(h22_both) == 1 and 6 in h22_both else \
           "🟧" if len(h22_both) <= 2 else "⚪"
record("H22", "sigma(tau(n))=n+1 AND tau(sigma(n))=n", "sigma(tau(6))=7=n+1, tau(sigma(6))=6=n",
       "both", h22_both, 6 in h22_both and len(h22_both) == 1, grade_22,
       f"Both: {h22_both}, sigma(tau)=n+1: {h22_part1}, tau(sigma)=n: {h22_part2}")

# H23: phi(sigma(n)) = tau(n) AND sigma(phi(n)) = n/phi(n)
print("\n--- H23: phi(sigma(6))=tau(6) AND sigma(phi(6))=6/phi(6) ---")
n = 6
phisig = phi(sigma(n))   # phi(12) = 4 = tau(6)
sigphi = sigma(phi(n))   # sigma(2) = 3 = 6/2 = n/phi(n)
print(f"  phi(sigma(6)) = phi({sigma(6)}) = {phisig}, tau(6) = {tau(6)}, match = {phisig == tau(6)}")
print(f"  sigma(phi(6)) = sigma({phi(6)}) = {sigphi}, 6/phi(6) = {n//phi(n)}, match = {sigphi == n // phi(n)}")
# Both conditions
for n_test in TEST_N[1:]:
    ps = phi(sigma(n_test))
    sp = sigma(phi(n_test))
    print(f"  n={n_test}: phi(sigma)={ps}=tau? {ps==tau(n_test)}, sigma(phi)={sp}=n/phi? {n_test//phi(n_test) if n_test%phi(n_test)==0 else 'N/A'}, match={sp==(n_test//phi(n_test)) if n_test%phi(n_test)==0 else False}")
h23_both = []
for n in SCAN_N:
    c1 = phi(sigma(n)) == tau(n)
    c2 = (n % phi(n) == 0) and (sigma(phi(n)) == n // phi(n))
    if c1 and c2:
        h23_both.append(n)
h23_c1 = [n for n in SCAN_N if phi(sigma(n)) == tau(n)]
h23_c2 = [n for n in SCAN_N if n % phi(n) == 0 and sigma(phi(n)) == n // phi(n)]
print(f"  phi(sigma(n))=tau(n) for n in [1,100]: {h23_c1}")
print(f"  sigma(phi(n))=n/phi(n) for n in [1,100]: {h23_c2}")
print(f"  BOTH for n in [1,100]: {h23_both}")
grade_23 = "🟩" if len(h23_both) == 1 and 6 in h23_both else \
           "🟧" if len(h23_both) <= 3 else "⚪"
record("H23", "phi(sigma(n))=tau(n) AND sigma(phi(n))=n/phi(n)", "phi(12)=4=tau(6), sigma(2)=3=6/2",
       "both", h23_both, 6 in h23_both and len(h23_both) == 1, grade_23,
       f"Both: {h23_both}; c1: {h23_c1}; c2: {h23_c2}")

# H24: sigma(sigma(6)) = sigma(12) = 28 = P_2 (second perfect number)
print("\n--- H24: sigma(sigma(6)) = 28 = P_2 (second perfect) ---")
n = 6
ss6 = sigma(sigma(n))
print(f"  sigma(sigma(6)) = sigma({sigma(6)}) = {ss6}")
print(f"  Is 28 perfect? sigma(28) = {sigma(28)}, 2*28 = 56, perfect: {sigma(28) == 2*28}")
# For which n: sigma(sigma(n)) is a perfect number?
perfect_nums = {6, 28, 496, 8128}
h24_matches = [n for n in range(1, 50) if sigma(sigma(n)) in perfect_nums]
print(f"  sigma(sigma(n)) is perfect for n in [1,50]: {h24_matches}")
# Stronger: sigma(sigma(n)) = next perfect after n
h24_chain = [n for n in range(2, 30) if sigma(sigma(n)) == 28 and n != 28]
print(f"  sigma(sigma(n)) = 28 for n in [2,29]: {h24_chain}")
grade_24 = "🟧" if len(h24_chain) <= 2 else "⚪"
if 6 in h24_chain and len(h24_chain) == 1:
    grade_24 = "🟩"
record("H24", "sigma(sigma(6)) = 28 = P_2", "sigma(12)=28", "second perfect",
       h24_chain, 6 in h24_chain and len(h24_chain) == 1, grade_24,
       f"sigma(sigma(n))=28 for n: {h24_chain}")

# H25: Is 6 the ONLY n where sigma(tau(n))=n+1 AND tau(sigma(n))=n?
# (This is H22 with explicit strict uniqueness check extended to larger range)
print("\n--- H25: Uniqueness check H22 extended to n in [1,10000] ---")
h25_both = []
for n in range(1, 10001):
    if sigma(tau(n)) == n + 1 and tau(sigma(n)) == n:
        h25_both.append(n)
        if len(h25_both) > 5:
            break
print(f"  sigma(tau(n))=n+1 AND tau(sigma(n))=n for n in [1,10000]: {h25_both}")
grade_25 = "🟩" if len(h25_both) == 1 and h25_both[0] == 6 else "⚪"
record("H25", "H22 uniqueness: scan [1,10000]", "sigma(tau(n))=n+1 & tau(sigma(n))=n", "n=6 only?",
       h25_both, len(h25_both) == 1 and 6 in h25_both, grade_25,
       f"Extended scan: {h25_both}")

# ─── SUMMARY ─────────────────────────────────────────────────────────────────

print("\n" + "=" * 65)
print("WAVE 11 SUMMARY")
print("=" * 65)

green  = [r for r in results if r["grade"] == "🟩"]
orange = [r for r in results if r["grade"] == "🟧"]
white  = [r for r in results if r["grade"] == "⚪"]
black  = [r for r in results if r["grade"] == "⬛"]

print(f"\n  🟩 {len(green)} | 🟧 {len(orange)} | ⚪ {len(white)} | ⬛ {len(black)}")
print(f"  Hit rate (🟩+🟧): {(len(green)+len(orange))/len(results)*100:.1f}%")

print("\n  🟩 GREEN (verified unique/proven):")
for r in green:
    print(f"    {r['id']}: {r['title']}")
    print(f"         {r['lhs']} = {r['rhs']}")
    print(f"         Unique for n: {r['holds_for']}")
    print(f"         Note: {r['note']}")

print("\n  🟧 ORANGE (structural, limited scope):")
for r in orange:
    print(f"    {r['id']}: {r['title']}")
    print(f"         {r['note']}")

print("\n  ⚪ WHITE (not unique / common):")
for r in white:
    print(f"    {r['id']}: {r['title']} — {r['note'][:80]}")

print("\n  ⬛ BLACK (refuted):")
for r in black:
    print(f"    {r['id']}: {r['title']}")

# Detailed table
print("\n" + "=" * 65)
print("FULL RESULTS TABLE")
print("=" * 65)
print(f"{'ID':>4}  {'Grade':5}  {'Unique':6}  {'Title'}")
print("-" * 65)
for r in results:
    unique_str = "YES" if r["unique"] else "no"
    print(f"  {r['id']}  {r['grade']}     {unique_str:6}  {r['title']}")

print("\nDone.")
