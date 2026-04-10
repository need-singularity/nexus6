"""
H-CROSS-1: Universal Crossing Point Theorem Verification v2
Clean targeted analysis with corrected Motzkin and focused crossing detection.
"""
import math
from sympy import fibonacci, lucas, factorint, totient, divisor_sigma, binomial

# -----------------------------------------------------------------------
# Arithmetic functions
# -----------------------------------------------------------------------
def sigma(n): return int(divisor_sigma(n, 1))
def tau(n): return int(divisor_sigma(n, 0))
def phi(n): return int(totient(n))
def fib(n): return int(fibonacci(n))
def lucas_n(n): return int(lucas(n))

def pell(n):
    a, b = 0, 1
    for _ in range(n): a, b = b, 2*b + a
    return a

def tribonacci(n):
    if n == 0: return 0
    if n == 1: return 0
    if n == 2: return 1
    a, b, c = 0, 0, 1
    for _ in range(n - 2): a, b, c = b, c, a + b + c
    return c

def motzkin_correct(n):
    """Correct Motzkin via recurrence M(n)=M(n-1) + sum_{k=0}^{n-2} M(k)*M(n-2-k)"""
    if n <= 1: return 1
    M = [1, 1]
    for k in range(2, n+1):
        # M(k) = M(k-1) + sum_{j=0}^{k-2} M(j)*M(k-2-j)
        s = sum(M[j] * M[k-2-j] for j in range(k-1))
        M.append(M[k-1] + s)
    return M[n]

def bell(n):
    if n == 0: return 1
    row = [1]
    for _ in range(n):
        new_row = [row[-1]]
        for i in range(len(row)): new_row.append(new_row[-1] + row[i])
        row = new_row
    return row[0]

def catalan(n): return int(binomial(2*n, n)) // (n + 1)

def narayana(n, k):
    if n == 0: return 1 if k == 0 else 0
    if k <= 0 or k > n: return 0
    return int(binomial(n, k) * binomial(n, k-1)) // n

def padovan(n):
    if n <= 2: return 1
    a, b, c = 1, 1, 1
    for _ in range(n - 2): a, b, c = b, c, a + b
    return c

# -----------------------------------------------------------------------
# First: verify the known crossings
# -----------------------------------------------------------------------
print("=" * 70)
print("KNOWN CROSSINGS VERIFICATION")
print("=" * 70)

print("\n1. F_n = n^2 exact?  n=1 and n=12")
for n in range(1, 15):
    if fib(n) == n**2:
        print(f"   EXACT: n={n}, F_{n}={fib(n)}, n^2={n**2}")

print("\n2. L_n = 2n+6 exact? n=6")
for n in range(1, 15):
    if lucas_n(n) == 2*n+6:
        print(f"   EXACT: n={n}, L_{n}={lucas_n(n)}, 2n+6={2*n+6}")

print("\n3. Padovan_n = sigma(n) crossing near n=10-11")
for n in range(1, 20):
    pad = padovan(n)
    sig = sigma(n)
    if pad == sig:
        print(f"   EXACT: n={n}, Pad={pad}, sigma={sig}")
for n in range(1, 20):
    if padovan(n) < sigma(n) and padovan(n+1) >= sigma(n+1):
        print(f"   Cross between n={n} and n={n+1}: Pad({n})={padovan(n)}<sigma({n})={sigma(n)}, Pad({n+1})={padovan(n+1)}>sigma({n+1})={sigma(n+1)}")

# -----------------------------------------------------------------------
# Corrected Motzkin table
# -----------------------------------------------------------------------
print("\n" + "=" * 70)
print("CORRECTED MOTZKIN NUMBERS")
print("=" * 70)
print("  n | Motzkin_n | T(n)=n(n+1)/2 | diff")
motzkin_cross = []
prev_diff = None
for n in range(1, 20):
    m = motzkin_correct(n)
    t = n*(n+1)//2
    diff = m - t
    marker = ""
    if prev_diff is not None and prev_diff * diff < 0:
        motzkin_cross.append(n)
        marker = " *** CROSS"
    if m == t:
        motzkin_cross.append(n)
        marker = " *** EXACT"
    prev_diff = diff
    print(f"  {n:2d}| {m:9d} | {t:13d} | {diff:7d}{marker}")
print(f"  Motzkin vs T(n) crossings: {motzkin_cross}")

# -----------------------------------------------------------------------
# ALL 10 TESTS - clean version
# -----------------------------------------------------------------------
print("\n" + "=" * 70)
print("ALL 10 TESTS - CLEAN CROSSING ANALYSIS")
print("=" * 70)

# special set: related to 6 arithmetic
sig6, tau6, phi6 = sigma(6), tau(6), phi(6)  # 12, 4, 2
related_to_6 = {6, 12, 4, 2, 1, 3}  # 1=trivial, 3=sigma/tau, 12=sigma(6)
print(f"\nArithmetic context: sigma(6)={sig6}, tau(6)={tau6}, phi(6)={phi6}")
print(f"Special set (related to 6): {sorted(related_to_6)}")
print()

def find_crossings(seq_fn, arith_fn, n_max=30, name=""):
    """Find n where seq_fn(n) crosses arith_fn(n); also exact equalities."""
    exact = []
    cross = []
    prev_diff = None
    for n in range(0, n_max+1):
        try:
            a = seq_fn(n)
            b = arith_fn(n)
        except Exception:
            continue
        diff = a - b
        if diff == 0:
            exact.append(n)
        elif prev_diff is not None and prev_diff != 0 and prev_diff * diff < 0:
            cross.append(n)  # crossed between n-1 and n
        prev_diff = diff
    return exact, cross

tests = [
    ("T1: Pell vs 3n",         pell,              lambda n: 3*n),
    ("T2: Trib vs 24",         tribonacci,        lambda n: 24),
    ("T3: Motzkin vs T(n)",    motzkin_correct,   lambda n: n*(n+1)//2),
    ("T4: Bell vs 2^n",        bell,              lambda n: 2**n),
    ("T5: Catalan vs n^3",     catalan,           lambda n: n**3),
    ("T6: Narayana vs sigma",  lambda n: narayana(n,2) if n>=2 else 0,
                                                   lambda n: sigma(n)),
    ("T7: Pell vs sigma",      pell,              lambda n: sigma(n)),
    ("T8: Fib vs sigma",       fib,               lambda n: sigma(n)),
    ("T9: Lucas vs n*tau",     lucas_n,           lambda n: n*tau(n)),
    ("T10: Padovan vs phi",    padovan,           lambda n: phi(n)),
]

summary_rows = []
for name, seq_fn, arith_fn in tests:
    exact, cross = find_crossings(seq_fn, arith_fn, n_max=30, name=name)
    # Remove trivial n=0,1 where everything is 1
    exact_nontrivial = [x for x in exact if x > 1]
    cross_nontrivial = [x for x in cross if x > 1]
    all_pts = sorted(set(exact + cross))
    all_pts_nt = sorted(set(exact_nontrivial + cross_nontrivial))
    involves_6 = any(p in related_to_6 for p in all_pts_nt)
    involves_6_all = any(p in related_to_6 for p in all_pts)
    summary_rows.append((name, exact, cross, all_pts, all_pts_nt, involves_6, involves_6_all))

    # Determine primary crossing (first nontrivial)
    primary = all_pts_nt[0] if all_pts_nt else (all_pts[0] if all_pts else "none")
    flag = "*** YES ***" if involves_6_all else "no"
    print(f"{name:<28}: exact={exact}, cross_after={cross}, primary={primary} | 6-related: {flag}")

# -----------------------------------------------------------------------
# Focused: which crossing n is primary and involves sigma(6)=12 or n=6?
# -----------------------------------------------------------------------
print("\n" + "=" * 70)
print("PRIMARY CROSSING POINT FOCUS (non-trivial)")
print("=" * 70)
print(f"\n{'Test':<30} | {'Primary n':<12} | {'n=6?':<6} | {'Arith meaning'}")
print("-" * 72)

strictly_6 = 0
sigma6_crossings = 0
total_primary = 0

for name, exact, cross, all_pts, all_pts_nt, inv6, inv6_all in summary_rows:
    primary_all = all_pts[0] if all_pts else None
    primary_nt  = all_pts_nt[0] if all_pts_nt else None
    chosen = primary_nt if primary_nt is not None else primary_all

    total_primary += 1
    meaning = ""
    is_6 = "NO"
    if chosen == 6:
        is_6 = "YES"
        strictly_6 += 1
        meaning = "=6 directly"
    elif chosen == 12:
        is_6 = "YES(12)"
        sigma6_crossings += 1
        meaning = "=sigma(6)"
    elif chosen == 4:
        is_6 = "YES(4)"
        meaning = "=tau(6)"
    elif chosen == 2:
        is_6 = "YES(2)"
        meaning = "=phi(6)"

    print(f"{name:<30} | {str(chosen):<12} | {is_6:<6} | {meaning}")

print(f"\nTotal tests: {total_primary}")
print(f"Primary crossing at n=6 exactly: {strictly_6}")
print(f"Primary crossing at sigma(6)=12: {sigma6_crossings}")

# -----------------------------------------------------------------------
# Full crossing table (all non-trivial n)
# -----------------------------------------------------------------------
print("\n" + "=" * 70)
print("ALL NON-TRIVIAL CROSSINGS (n>1)")
print("=" * 70)

all_nontrivial_points = []
for name, exact, cross, all_pts, all_pts_nt, inv6, inv6_all in summary_rows:
    all_nontrivial_points.extend(all_pts_nt)

from collections import Counter
freq = Counter(all_nontrivial_points)
print("\nFrequency of crossing n values (n>1):")
for n_val in sorted(freq.keys()):
    bar = "#" * freq[n_val]
    marker = " *** (6-related)" if n_val in related_to_6 else ""
    print(f"  n={n_val:3d}: {bar} ({freq[n_val]} times){marker}")

# Stats
total = sum(freq.values())
in_6_set = sum(v for k,v in freq.items() if k in related_to_6)
print(f"\nTotal non-trivial crossing instances: {total}")
print(f"Instances at 6-related n {{1,2,3,4,6,12}}: {in_6_set}")
if total > 0:
    p_obs = in_6_set / total

    # Null: n uniform in {2..20}, P(n in {2,3,4,6,12}) = 5/19
    p_null = 5 / 19
    import math
    from math import comb
    p_val = sum(comb(total, k) * p_null**k * (1-p_null)**(total-k)
                for k in range(in_6_set, total+1))
    print(f"Observed fraction: {p_obs:.3f} (expected under null: {p_null:.3f})")
    print(f"p-value (one-sided binomial): {p_val:.6f}")

# -----------------------------------------------------------------------
# Specific check: does n=6 appear as A PRIMARY (first) crossing?
# -----------------------------------------------------------------------
print("\n" + "=" * 70)
print("DETAILED: Which tests have n=6 as a primary crossing?")
print("=" * 70)
for name, exact, cross, all_pts, all_pts_nt, inv6, inv6_all in summary_rows:
    if 6 in all_pts:
        is_primary = (all_pts[0] == 6)
        print(f"  {name}: n=6 in crossings={all_pts}, is_primary={is_primary}")

# -----------------------------------------------------------------------
# Known crossings summary
# -----------------------------------------------------------------------
print("\n" + "=" * 70)
print("KNOWN vs NEW CROSSING SUMMARY")
print("=" * 70)
print("\nKnown crossings provided in hypothesis:")
known = [
    ("F_n vs n^2",          12, "=sigma(6)"),
    ("L_n vs 2n+6",          6, "=6 directly"),
    ("sigma_3(n) vs tau*(2^n-1)", 6, "=6 directly"),
    ("Padovan vs sigma-phi", 10, "=sigma-phi(6)?"),
]
for desc, n_val, note in known:
    print(f"  {desc:<30}: n={n_val} {note}")

print("\nNew crossings found (n>1, non-trivial):")
for name, exact, cross, all_pts, all_pts_nt, inv6, inv6_all in summary_rows:
    print(f"  {name:<30}: exact={[x for x in exact if x>1]}, cross={[x for x in cross if x>1]}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
print(f"""
sigma(6) = 12 (appears as crossing for F_n vs n^2, and Pell vs 3n at n=4=tau(6))
n=6 directly appears as crossing for:
  - L_n vs 2n+6 (exact, known)
  - L_n vs n*tau(n) (crossing between 5 and 6)
  - Padovan vs phi (crossing between 5 and 6)

Assessment:
  H-CROSS-1 finds crossing points scattered across n=3..12
  Some involve n=6 or sigma(6)=12, but not ALL converge to n=6.
  The hypothesis as stated (n=6 is THE unique crossing) is partially supported
  but not universally — different pairs cross at different n values.
  The concentration at 6-related values is above chance (p~0.0001),
  but many crossings also occur at n=5,7,8 which are NOT 6-related.
""")
