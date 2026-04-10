"""
H-CROSS-1: Universal Crossing Point Theorem Verification
Search for crossing points of recurrence sequences vs arithmetic/polynomial functions.
"""
import math
from sympy import fibonacci, lucas, isprime, factorint, totient, divisor_sigma, binomial

# -----------------------------------------------------------------------
# Helper: arithmetic functions
# -----------------------------------------------------------------------

def sigma(n):
    """Sum of divisors."""
    return int(divisor_sigma(n, 1))

def tau(n):
    """Number of divisors."""
    return int(divisor_sigma(n, 0))

def phi(n):
    """Euler's totient."""
    return int(totient(n))

def fib(n):
    return int(fibonacci(n))

def lucas_n(n):
    return int(lucas(n))

# Pell numbers: P(0)=0, P(1)=1, P(n)=2*P(n-1)+P(n-2)
def pell(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, 2*b + a
    return a

# Tribonacci: T(0)=0, T(1)=0, T(2)=1, T(n)=T(n-1)+T(n-2)+T(n-3)
def tribonacci(n):
    if n == 0: return 0
    if n == 1: return 0
    if n == 2: return 1
    a, b, c = 0, 0, 1
    for _ in range(n - 2):
        a, b, c = b, c, a + b + c
    return c

# Motzkin: M(0)=1, M(1)=1, M(n) = ((2n+2)*M(n-1) + 3*M(n-2)) / (n+3)
def motzkin(n):
    if n == 0: return 1
    if n == 1: return 1
    a, b = 1, 1
    for k in range(2, n+1):
        a, b = b, ((2*k+2)*b + 3*a) // (k+3)
    return b

# Bell numbers
def bell(n):
    # Build Bell triangle
    if n == 0: return 1
    row = [1]
    for _ in range(n):
        new_row = [row[-1]]
        for i in range(len(row)):
            new_row.append(new_row[-1] + row[i])
        row = new_row
    return row[0]

# Catalan: C(n) = binomial(2n, n) / (n+1)
def catalan(n):
    return int(binomial(2*n, n)) // (n + 1)

# Narayana N(n, 2) = C(n-1, 1) * C(n-1, 1) / ...
# Narayana(n,k) = (1/n) * C(n,k) * C(n,k-1)
def narayana(n, k):
    if n == 0: return 1 if k == 0 else 0
    return int(binomial(n, k) * binomial(n, k-1)) // n

# Padovan: P(0)=1, P(1)=1, P(2)=1, P(n)=P(n-2)+P(n-3)
def padovan(n):
    if n <= 2: return 1
    a, b, c = 1, 1, 1
    for _ in range(n - 2):
        a, b, c = b, c, a + b
    return c

# -----------------------------------------------------------------------
# Known crossings (verification)
# -----------------------------------------------------------------------
print("=" * 70)
print("KNOWN CROSSINGS VERIFICATION")
print("=" * 70)

print("\n1. F_n vs n^2: cross at n=12=sigma(6)?")
for n in range(1, 20):
    f = fib(n)
    p = n**2
    if abs(f - p) <= 1 or (n > 1 and fib(n-1) < (n-1)**2 and fib(n+1) > (n+1)**2):
        print(f"   n={n}: F_{n}={f}, n^2={p}, diff={f-p}")

print("\n2. L_n vs 2n+6: cross at n=6?")
for n in range(1, 15):
    l = lucas_n(n)
    f = 2*n + 6
    print(f"   n={n}: L_{n}={l}, 2n+6={f}, diff={l-f}")

print("\n3. Padovan vs sigma: cross at n=10=sigma-phi?")
for n in range(1, 20):
    p = padovan(n)
    s = sigma(n)
    print(f"   n={n}: Pad={p}, sigma={s}, diff={p-s}")

# -----------------------------------------------------------------------
# New crossing searches
# -----------------------------------------------------------------------
print("\n" + "=" * 70)
print("NEW CROSSING SEARCHES")
print("=" * 70)

N_MAX = 30

print("\n--- Test 1: Pell_n vs 3n ---")
print("  (sigma(6)=12, tau(6)=4, sigma/tau=3)")
prev_diff = None
for n in range(0, N_MAX):
    p = pell(n)
    f = 3 * n
    diff = p - f
    if prev_diff is not None and prev_diff * diff <= 0:
        print(f"  *** CROSSING at n={n}: Pell_{n}={p}, 3n={f}, diff={diff}")
    elif n <= 15:
        pass  # just track
    prev_diff = diff
# Show table
print("  n | Pell_n | 3n | diff")
for n in range(0, 20):
    p = pell(n)
    f = 3 * n
    marker = " <--" if abs(p - f) <= max(1, p//10) else ""
    print(f"  {n:2d}| {p:6d} | {f:3d} | {p-f:6d}{marker}")

print("\n--- Test 2: Tribonacci_n vs sigma*phi = 24 ---")
print("  sigma(6)*phi(6)=12*2=24, or sigma(6)+phi(6)=12+2=14")
print("  When does Trib first reach 24?")
for n in range(0, 25):
    t = tribonacci(n)
    print(f"  n={n:2d}: Trib={t:6d}  (vs 24: {'>=24' if t>=24 else '<24'})")
    if t > 50:
        break

print("\n--- Test 3: Motzkin_n vs T(n) = n(n+1)/2 ---")
prev_diff = None
cross_n = []
for n in range(1, 25):
    m = motzkin(n)
    t = n*(n+1)//2
    diff = m - t
    if prev_diff is not None and prev_diff * diff < 0:
        cross_n.append(n)
        print(f"  *** CROSSING at n={n}: Motzkin={m}, T(n)={t}, diff={diff}")
    prev_diff = diff
print("  n | Motzkin | T(n)=n(n+1)/2 | diff")
for n in range(1, 20):
    m = motzkin(n)
    t = n*(n+1)//2
    print(f"  {n:2d}| {m:7d} | {t:13d} | {m-t:7d}")

print("\n--- Test 4: Bell_n vs 2^n ---")
prev_diff = None
cross_n = []
print("  n | Bell_n | 2^n | diff")
for n in range(0, 20):
    b = bell(n)
    p = 2**n
    diff = b - p
    if prev_diff is not None and prev_diff * diff < 0:
        cross_n.append(n)
        print(f"  *** CROSSING at n={n}")
    prev_diff = diff
    print(f"  {n:2d}| {b:8d} | {p:5d} | {diff:8d}")

print(f"\n  Crossing points: {cross_n}")

print("\n--- Test 5: Catalan_n vs n^3 ---")
prev_diff = None
cross_n = []
print("  n | Catalan | n^3 | diff")
for n in range(1, 20):
    c = catalan(n)
    p = n**3
    diff = c - p
    if prev_diff is not None and prev_diff * diff < 0:
        cross_n.append(n)
        print(f"  *** CROSSING at n={n}")
    prev_diff = diff
    print(f"  {n:2d}| {c:8d} | {p:5d} | {diff:8d}")

print(f"\n  Crossing points: {cross_n}")

print("\n--- Test 6: Narayana N(n,2) vs sigma(n) ---")
prev_diff = None
cross_n = []
print("  n | N(n,2) | sigma(n) | diff")
for n in range(2, 25):
    nar = narayana(n, 2)
    s = sigma(n)
    diff = nar - s
    if prev_diff is not None and prev_diff * diff < 0:
        cross_n.append(n)
        print(f"  *** CROSSING at n={n}: N(n,2)={nar}, sigma={s}")
    prev_diff = diff
    print(f"  {n:2d}| {nar:7d} | {s:8d} | {diff:7d}")

print(f"\n  Crossing points: {cross_n}")

print("\n--- Test 7: Pell_n vs sigma(n) ---")
prev_diff = None
cross_n = []
print("  n | Pell_n | sigma(n) | diff")
for n in range(1, 25):
    p = pell(n)
    s = sigma(n)
    diff = p - s
    if prev_diff is not None and prev_diff * diff < 0:
        cross_n.append(n)
        print(f"  *** CROSSING at n={n}: Pell={p}, sigma={s}")
    prev_diff = diff
    print(f"  {n:2d}| {p:7d} | {s:8d} | {diff:7d}")

print(f"\n  Crossing points: {cross_n}")

print("\n--- Test 8: F_n vs sigma(n) ---")
prev_diff = None
cross_n = []
print("  n | F_n | sigma(n) | diff")
for n in range(1, 25):
    f = fib(n)
    s = sigma(n)
    diff = f - s
    if prev_diff is not None and prev_diff * diff < 0:
        cross_n.append(n)
        print(f"  *** CROSSING at n={n}: F_n={f}, sigma={s}")
    prev_diff = diff
    print(f"  {n:2d}| {f:7d} | {s:8d} | {diff:7d}")

print(f"\n  Crossing points: {cross_n}")

print("\n--- Test 9: L_n vs n*tau(n) ---")
prev_diff = None
cross_n = []
print("  n | L_n | n*tau(n) | diff")
for n in range(1, 25):
    l = lucas_n(n)
    t = n * tau(n)
    diff = l - t
    if prev_diff is not None and prev_diff * diff < 0:
        cross_n.append(n)
        print(f"  *** CROSSING at n={n}: L_n={l}, n*tau={t}")
    prev_diff = diff
    print(f"  {n:2d}| {l:7d} | {t:8d} | {diff:7d}")

print(f"\n  Crossing points: {cross_n}")

print("\n--- Test 10: Padovan_n vs phi(n) ---")
prev_diff = None
cross_n = []
print("  n | Padovan | phi(n) | diff")
for n in range(1, 25):
    p = padovan(n)
    ph = phi(n)
    diff = p - ph
    if prev_diff is not None and prev_diff * diff < 0:
        cross_n.append(n)
        print(f"  *** CROSSING at n={n}: Padovan={p}, phi={p}, diff={diff}")
    prev_diff = diff
    print(f"  {n:2d}| {p:7d} | {ph:6d} | {diff:7d}")

print(f"\n  Crossing points: {cross_n}")

# -----------------------------------------------------------------------
# Summary: check which crossings involve 6, 12, sigma(6), phi(6), tau(6)
# -----------------------------------------------------------------------
print("\n" + "=" * 70)
print("SUMMARY: Crossing Points & Relation to 6")
print("=" * 70)

# Arithmetic functions of 6
sig6 = sigma(6)   # = 12
tau6 = tau(6)     # = 4
phi6 = phi(6)     # = 2
print(f"\nArithmetic functions of 6:")
print(f"  sigma(6) = {sig6}")
print(f"  tau(6)   = {tau6}")
print(f"  phi(6)   = {phi6}")
print(f"  sigma(6)/tau(6) = {sig6//tau6}")
print(f"  sigma(6)/phi(6) = {sig6//phi6}")

# Check perfect-number neighbors: sigma(6)=12, sigma(28)=56, ...
print(f"\n  sigma(12)={sigma(12)}, tau(12)={tau(12)}, phi(12)={phi(12)}")
print(f"  sigma(28)={sigma(28)}, tau(28)={tau(28)}, phi(28)={phi(28)}")

# Direct crossing: Fibonacci at n=6
print(f"\nFibonacci at n=6: F_6={fib(6)}, sigma(6)={sig6}")
print(f"Lucas at n=6: L_6={lucas_n(6)}")
print(f"Pell at n=6: P_6={pell(6)}")
print(f"Tribonacci at n=6: T_6={tribonacci(6)}")
print(f"Motzkin at n=6: M_6={motzkin(6)}")
print(f"Bell at n=6: B_6={bell(6)}")
print(f"Catalan at n=6: C_6={catalan(6)}")
print(f"Padovan at n=6: Pad_6={padovan(6)}")

# -----------------------------------------------------------------------
# Statistical analysis: what fraction of crossing points = 6 or sigma(6)?
# -----------------------------------------------------------------------
print("\n" + "=" * 70)
print("STATISTICAL ANALYSIS")
print("=" * 70)

print("\nCollecting all crossing points from the 10 tests...")
print("(Manual review needed - see tables above)")

# Expected: if n uniform in [1,20], P(n in {6,12}) = 2/20 = 0.1
# Expected crossings involving 6 or sigma(6) = 0
# Will be filled from table analysis

# Scan once more cleanly
all_crossings = {}

tests = {
    "Pell vs 3n": (lambda n: pell(n), lambda n: 3*n),
    "Trib vs 24": (lambda n: tribonacci(n), lambda n: 24),
    "Motzkin vs T(n)": (lambda n: motzkin(n), lambda n: n*(n+1)//2),
    "Bell vs 2^n": (lambda n: bell(n), lambda n: 2**n),
    "Catalan vs n^3": (lambda n: catalan(n), lambda n: n**3),
    "Narayana vs sigma": (lambda n: narayana(n,2), lambda n: sigma(n)),
    "Pell vs sigma": (lambda n: pell(n), lambda n: sigma(n)),
    "Fib vs sigma": (lambda n: fib(n), lambda n: sigma(n)),
    "Lucas vs n*tau": (lambda n: lucas_n(n), lambda n: n*tau(n)),
    "Padovan vs phi": (lambda n: padovan(n), lambda n: phi(n)),
}

special = {6, 12, 4, 2, 1, 28}  # sigma(6)=12, tau(6)=4, phi(6)=2, sigma(6)/tau(6)=3

print(f"\n{'Test':<22} | {'Crossings':<30} | {'Involves 6?'}")
print("-" * 75)

total_crossings = 0
special_crossings = 0

for name, (f_seq, f_arith) in tests.items():
    crosses = []
    prev_diff = None
    for n in range(1, 30):
        try:
            a = f_seq(n)
            b = f_arith(n)
            diff = a - b
            if prev_diff is not None and prev_diff * diff < 0:
                crosses.append(n)
            elif prev_diff is not None and prev_diff == 0:
                crosses.append(n-1)
            prev_diff = diff
        except:
            break

    # Also check exact equality
    exact = []
    for n in range(1, 30):
        try:
            if f_seq(n) == f_arith(n):
                exact.append(n)
        except:
            break

    involves = any(c in special or c == 6 for c in crosses + exact)
    note = [str(c) for c in sorted(set(crosses + exact))]

    for c in set(crosses + exact):
        total_crossings += 1
        if c in special or c == 6:
            special_crossings += 1

    all_crossings[name] = sorted(set(crosses + exact))
    mark = "*** YES ***" if involves else "no"
    print(f"{name:<22} | {', '.join(note) if note else 'none':<30} | {mark}")

print(f"\nTotal distinct crossing points found: {total_crossings}")
print(f"Crossing points involving {{6, 12, 4, 2}}: {special_crossings}")
if total_crossings > 0:
    frac = special_crossings / total_crossings
    print(f"Fraction: {frac:.3f}")

    # Under null: P(n in {6,12}) = 2/20 = 0.1 for n in [1,20]
    p_null = 3/20  # include 6, 12, 4
    from math import comb
    p_val = sum(comb(total_crossings, k) * p_null**k * (1-p_null)**(total_crossings-k)
                for k in range(special_crossings, total_crossings+1))
    print(f"p-value (binomial, p_null={p_null}): {p_val:.6f}")

print("\n" + "=" * 70)
print("EXACT CROSSING POINTS: n where a_n == f(n)")
print("=" * 70)
for name, crosses in all_crossings.items():
    print(f"  {name:<25}: {crosses}")
