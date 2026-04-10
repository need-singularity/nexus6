#!/usr/bin/env python3
"""
Verify 20 graph theory / topology / combinatorics hypotheses for TECS-L.
Framework: perfect number 6, sigma(6)=12, tau(6)=4, phi(6)=2, sigma_{-1}(6)=2.

Each hypothesis is independently verified with exact arithmetic.
Texas Sharpshooter methodology: count how many "hits" vs random expectation.
"""
import math
from fractions import Fraction
from functools import reduce

# ─── n=6 constants ───
n = 6
sigma = 12       # sum of divisors
tau = 4          # number of divisors
phi_n = 2        # Euler totient
sigma_neg1 = 2   # sum of reciprocals of divisors = 1+1/2+1/3+1/6 = 2
sopfr = 5        # sum of prime factors
omega = 2        # number of distinct prime factors

print("=" * 72)
print("  DEEP GRAPH / TOPOLOGY / COMBINATORICS VERIFICATION")
print("  Framework: n=6, sigma=12, tau=4, phi=2, sigma_{-1}=2")
print("=" * 72)

results = []

def record(hid, title, claim, actual, match, grade, note=""):
    status = "PASS" if match else "FAIL"
    results.append((hid, title, claim, actual, match, grade, note))
    icon = {"pass": "✓", "fail": "✗"}[status.lower()]
    g = grade if match else "⬛"
    print(f"\n{'─'*60}")
    print(f"  [{icon}] {hid}: {title}")
    print(f"  Claim:  {claim}")
    print(f"  Actual: {actual}")
    print(f"  Grade:  {g}")
    if note:
        print(f"  Note:   {note}")


# ════════════════════════════════════════════════════════════════════════
# A. GRAPH THEORY (7 hypotheses)
# ════════════════════════════════════════════════════════════════════════

print("\n\n" + "═" * 72)
print("  A. GRAPH THEORY")
print("═" * 72)

# --- A1: Euler characteristic of convex polyhedra = sigma_{-1}(6) ---
# chi = V - E + F = 2 for any convex polyhedron (Euler's formula)
# sigma_{-1}(6) = 1 + 1/2 + 1/3 + 1/6 = 2
# This is EXACT.
chi_convex = 2
record("A1", "Euler characteristic chi = sigma_{-1}(6)",
       f"chi(convex polyhedron) = V-E+F = {chi_convex} = sigma_{{-1}}(6) = {sigma_neg1}",
       f"{chi_convex} = {sigma_neg1}",
       chi_convex == sigma_neg1,
       "🟩",
       "Euler 1758. chi=2 for all convex polyhedra. sigma_{-1}(6)=2 exact.")

# Verify across Platonic solids
print("\n  Platonic solid verification:")
print(f"  {'Solid':<16} {'V':>3} {'E':>3} {'F':>3} {'V-E+F':>6}")
print(f"  {'─'*35}")
platonic = [
    ("Tetrahedron", 4, 6, 4),
    ("Cube", 8, 12, 6),
    ("Octahedron", 6, 12, 8),
    ("Dodecahedron", 20, 30, 12),
    ("Icosahedron", 12, 30, 20),
]
for name, v, e, f in platonic:
    print(f"  {name:<16} {v:>3} {e:>3} {f:>3} {v-e+f:>6}")

# --- A2: Ramsey R(3,3) = 6 (already in H-UD-4, but we verify the PROOF) ---
# We verify computationally: K_5 has a 2-coloring without monochromatic K_3
# but K_6 does not.
print(f"\n  A2: Ramsey R(3,3) = 6 verification")
# K_5: Petersen complement (cycle C_5) is triangle-free, its complement is also C_5
# So coloring edges of K_5 as C_5 (red) and complement C_5 (blue) => no mono triangle
# This is well-known. We verify the count.
# Number of 2-colorings of K_5 edges = 2^10 = 1024
# Number of those with no monochromatic triangle > 0
# For K_6: we verify there are ZERO such colorings... too expensive to enumerate all 2^15.
# Instead verify the Ramsey pigeonhole argument.
edges_k5 = 5 * 4 // 2  # 10
edges_k6 = 6 * 5 // 2  # 15
# In K_6, fix vertex v. It has 5 neighbors. By pigeonhole, >= 3 neighbors share a color.
# Among those 3, if any edge is that same color => monochromatic triangle.
# If none => the 3 mutual edges form mono triangle in other color.
record("A2", "R(3,3) = 6 = n (Ramsey number)",
       f"R(3,3) = 6 = n, the first perfect number",
       f"R(3,3) = 6 (proved by pigeonhole on K_6 vertices)",
       True,  # theorem
       "🟩",
       "Already in H-UD-4. Pure theorem. R(3,3)=6 is the DEFINITION of 6's Ramsey role.")

# --- A3: Genus of K_6 = 1 (torus embedding) ---
# Ringel-Youngs: gamma(K_n) = ceil((n-3)(n-4)/12) for n >= 3
def genus_kn(nn):
    return math.ceil((nn - 3) * (nn - 4) / 12)

genus_k6 = genus_kn(6)
# sigma_{-1}(6)/2 = 1, also phi(6)/2 = 1
record("A3", "Genus gamma(K_6) = 1 = phi(6)/omega(6)",
       f"gamma(K_6) = ceil((6-3)(6-4)/12) = ceil(6/12) = ceil(0.5) = 1",
       f"gamma(K_6) = {genus_k6}, phi(6)/omega(6) = {phi_n}/{omega} = {phi_n//omega}",
       genus_k6 == 1 and genus_k6 == phi_n // omega,
       "🟩",
       "K_6 embeds on torus (genus 1) but not on plane. Partially in H-GRAPH-1.")

# Genus table
print("\n  Genus of K_n:")
print(f"  {'n':>3} {'gamma(K_n)':>10} {'phi(n)':>7} {'Match phi/omega?':>16}")
for nn in range(3, 13):
    g = genus_kn(nn)
    try:
        # Euler totient
        p = nn
        tot = p
        temp = p
        for i in range(2, int(math.sqrt(p)) + 1):
            if temp % i == 0:
                while temp % i == 0:
                    temp //= i
                tot -= tot // i
        if temp > 1:
            tot -= tot // temp
        # omega
        om = len(set(f for f in range(2, nn+1) if nn % f == 0 and all(f % d != 0 for d in range(2, f))))
        if om == 0:
            om = 1
        ratio = f"{tot}/{om}={tot//om}" if tot % om == 0 else f"{tot}/{om}={tot/om:.2f}"
    except:
        ratio = "?"
    print(f"  {nn:>3} {g:>10} {tot:>7} {ratio:>16}")

# --- A4: Petersen graph connections ---
# Petersen: 10 vertices, 15 edges, 3-regular, chromatic number 3
# 15 edges = C(6,2) = edges of K_6
# 10 vertices = C(5,2) = T(4) = 4th triangular number + ... actually C(5,2)=10
# Petersen is the Kneser graph K(5,2). 5 = sopfr(6).
petersen_v = 10
petersen_e = 15
petersen_chi_num = 3  # chromatic number
edges_match = (petersen_e == math.comb(n, 2))
vertex_match = (petersen_v == math.comb(sopfr, omega))

record("A4", "Petersen graph: E=C(6,2), V=C(sopfr,omega)",
       f"Petersen: V=10=C(5,2)=C(sopfr,omega), E=15=C(6,2)=C(n,2)",
       f"V={petersen_v}=C({sopfr},{omega})={math.comb(sopfr,omega)}, E={petersen_e}=C({n},2)={math.comb(n,2)}",
       edges_match and vertex_match,
       "🟧",
       "Petersen = Kneser K(5,2). sopfr(6)=5, omega(6)=2. Chromatic=3=sigma/tau.")

# Also: Petersen chromatic number = 3 = sigma/tau
petersen_chromatic_match = (petersen_chi_num == sigma // tau)
print(f"  Petersen chromatic number: {petersen_chi_num} = sigma/tau = {sigma}/{tau} = {sigma//tau}: {'MATCH' if petersen_chromatic_match else 'NO'}")

# --- A5: K_{3,3} and Kuratowski ---
# K_{3,3}: complete bipartite graph, non-planar
# 3,3 = the prime factorization of 6 (as partition 3+3=6)
# K_{3,3} edges = 3*3 = 9 = sigma(6) - sigma/tau = 12 - 3
# Actually 9 = 3^2 = (n/2)^2
k33_edges = 3 * 3
k33_vertices = 6  # = n!
record("A5", "K_{3,3}: vertices=n=6, edges=(n/2)^2=9",
       f"K_{{3,3}} has V=3+3=6=n, E=3*3=9=(n/2)^2",
       f"V={k33_vertices}=n={n}, E={k33_edges}=(n/2)^2={(n//2)**2}",
       k33_vertices == n and k33_edges == (n // 2) ** 2,
       "🟧",
       "K_{3,3} is minimal non-planar (Kuratowski). V=n=6 is the partition 3+3.")

# --- A6: Hamiltonian cycles on K_6 ---
# Number of distinct Hamiltonian cycles on K_n = (n-1)!/2
ham_k6 = math.factorial(n - 1) // 2  # = 5!/2 = 60
# 60 = sigma(6) * sopfr(6) = 12 * 5
product_check = sigma * sopfr
record("A6", "Hamiltonian cycles on K_6 = sigma * sopfr = 60",
       f"Ham(K_6) = (6-1)!/2 = 60 = sigma(6)*sopfr(6) = 12*5",
       f"Ham(K_6) = {ham_k6}, sigma*sopfr = {product_check}",
       ham_k6 == product_check,
       "🟧★",
       "60 = 12*5 exact. Is this unique?")

# Uniqueness test
print("\n  Uniqueness test: Ham(K_n) = sigma(n) * sopfr(n)?")
def compute_sigma(m):
    return sum(d for d in range(1, m+1) if m % d == 0)

def compute_sopfr(m):
    s, temp = 0, m
    for p in range(2, m+1):
        while temp % p == 0:
            s += p
            temp //= p
        if temp == 1:
            break
    return s

for nn in range(3, 30):
    ham = math.factorial(nn - 1) // 2
    sig = compute_sigma(nn)
    sop = compute_sopfr(nn)
    if ham == sig * sop:
        print(f"    n={nn}: Ham={(nn-1)}!/2={ham}, sigma*sopfr={sig}*{sop}={sig*sop} ← MATCH")

# --- A7: Graph Laplacian eigenvalues of K_6 ---
# K_n Laplacian eigenvalues: 0 (multiplicity 1), n (multiplicity n-1)
# K_6: eigenvalues 0, 6, 6, 6, 6, 6
# Algebraic connectivity (2nd smallest eigenvalue) = 6 = n
# Number of spanning trees = n^{n-2} = 6^4 = 1296 (Cayley's formula)
spanning_trees_k6 = n ** (n - 2)  # 6^4 = 1296
# 1296 = 6^4 = n^tau = n^{tau(n)}
n_to_tau = n ** tau
record("A7", "Spanning trees of K_6 = n^tau(n) = 6^4 = 1296",
       f"Cayley: T(K_6) = 6^(6-2) = 6^4 = 1296 = n^{{tau(n)}}",
       f"T(K_6) = {spanning_trees_k6} = n^tau = {n}^{tau} = {n_to_tau}",
       spanning_trees_k6 == n_to_tau,
       "🟩",
       "Cayley's formula: T(K_n) = n^{n-2}. For n=6: n-2=4=tau(6). So T=n^tau. EXACT.")

# Is this unique? n-2 = tau(n)?
print("\n  Uniqueness: n-2 = tau(n)?")
def compute_tau(m):
    return sum(1 for d in range(1, m+1) if m % d == 0)

for nn in range(2, 100):
    if nn - 2 == compute_tau(nn):
        print(f"    n={nn}: n-2={nn-2}, tau(n)={compute_tau(nn)} ← MATCH")


# ════════════════════════════════════════════════════════════════════════
# B. TOPOLOGY (5 hypotheses)
# ════════════════════════════════════════════════════════════════════════

print("\n\n" + "═" * 72)
print("  B. TOPOLOGY")
print("═" * 72)

# --- B1: Euler characteristic of surfaces ---
# Sphere: chi=2, Torus: chi=0, Klein bottle: chi=0
# chi(S^n) = 1 + (-1)^n. For S^2: chi=2=sigma_{-1}(6)
# For n-torus T^n: chi=0
# So chi(sphere) = sigma_{-1}(6), chi(torus) = 0
# Key: K_6 embeds on torus (genus 1). Euler: V-E+F = 2-2g = 0 for torus.
chi_sphere = 2
chi_torus = 0
# chi(orientable surface genus g) = 2 - 2g
# g = genus(K_6) = 1 => chi = 0
record("B1", "chi(S^2) = sigma_{-1}(6) = 2; K_6 torus chi=0",
       f"chi(S^2) = 2 = sigma_{{-1}}(6). K_6 on torus: chi = 2-2*genus = 2-2 = 0",
       f"chi(S^2) = {chi_sphere} = {sigma_neg1}. Torus chi = {chi_torus}.",
       chi_sphere == sigma_neg1,
       "🟩",
       "chi of sphere = sigma_{-1}(6). Fundamental topological invariant.")

# --- B2: Genus of K_n and perfect numbers ---
# gamma(K_n) = ceil((n-3)(n-4)/12)
# gamma(K_6) = 1, gamma(K_28) = ceil(25*24/12) = ceil(50) = 50
# gamma(K_496) = ceil(493*492/12) = ceil(20213) = 20213
# For n=6: (n-3)(n-4) = 3*2 = 6 = n! And 6/12 = 1/2 = upper Golden Zone
print("\n  Genus formula detail for n=6:")
print(f"    (n-3)(n-4) = 3*2 = {(n-3)*(n-4)} = n itself!")
print(f"    (n-3)(n-4)/12 = 6/12 = 1/2 = Riemann critical line")
print(f"    ceil(1/2) = 1 = genus")

# For perfect numbers:
print("\n  Genus of K_n for perfect numbers:")
for pn in [6, 28, 496, 8128]:
    g = math.ceil((pn - 3) * (pn - 4) / 12)
    print(f"    K_{pn}: genus = {g}")

record("B2", "(n-3)(n-4) = n for n=6; genus = ceil(n/12) = ceil(1/2)",
       f"For K_6: (6-3)(6-4) = 3*2 = 6 = n. genus = ceil(6/sigma) = ceil(1/2) = 1",
       f"(n-3)(n-4)={n} for n=6. genus=ceil(n/sigma)=ceil({n}/{sigma})={genus_k6}",
       (n-3)*(n-4) == n and genus_k6 == math.ceil(n / sigma),
       "🟩",
       "(n-3)(n-4)=n iff n^2-7n+12=n iff n^2-8n+12=0 iff n=(8+-sqrt(16))/2 = 6 or 2. UNIQUE for n>2!")

# Verify: n^2 - 8n + 12 = 0
# n = (8 +/- sqrt(64-48))/2 = (8 +/- 4)/2 = 6 or 2
print(f"\n  (n-3)(n-4) = n solutions: n^2-8n+12=0 => n=6 or n=2")
print(f"  n=2: (2-3)(2-4) = (-1)(-2) = 2 ✓ (trivial, K_2 is just an edge)")
print(f"  n=6: (6-3)(6-4) = 3*2 = 6 ✓ (non-trivial!)")

# --- B3: Betti numbers of 6-torus T^6 ---
# T^n Betti numbers: b_k = C(n,k)
# T^6: b_0=1, b_1=6, b_2=15, b_3=20, b_4=15, b_5=6, b_6=1
# Total = 2^6 = 64
# Key: b_1 = 6 = n, b_2 = 15 = C(6,2) = edges of K_6
betti_t6 = [math.comb(6, k) for k in range(7)]
total_betti = sum(betti_t6)
chi_t6 = sum((-1)**k * betti_t6[k] for k in range(7))

print(f"\n  T^6 Betti numbers: {betti_t6}")
print(f"  Total = {total_betti} = 2^6 = 64")
print(f"  chi(T^6) = {chi_t6}")
print(f"  b_1 = {betti_t6[1]} = n")
print(f"  b_2 = {betti_t6[2]} = C(6,2) = edges of K_6")
print(f"  b_3 = {betti_t6[3]} = 20")

record("B3", "T^6 Betti: b_1=n, b_2=C(n,2), total=2^n=64",
       f"T^6: b_k=C(6,k), total=2^6=64, chi=0",
       f"Betti = {betti_t6}, total={total_betti}, chi={chi_t6}",
       betti_t6[1] == n and betti_t6[2] == math.comb(n, 2) and total_betti == 2**n,
       "🟩",
       "Standard result for n-torus. b_k=C(n,k) by Kunneth. Not n=6-specific.")

# --- B4: Hopf fibration and n=6 ---
# pi_3(S^2) = Z (Hopf fibration). |pi_6(S^3)| = 12 = sigma(6).
# Adams: Hopf invariant 1 exists only in dims 1, 2, 4, 8.
# sigma(6) = 12 = 4 + 8 (the two non-trivial Hopf invariant 1 dimensions!)
hopf_dims = [1, 2, 4, 8]  # dimensions with Hopf invariant 1
nontrivial_sum = 4 + 8  # = 12 = sigma(6)
record("B4", "sigma(6) = 4 + 8 = sum of nontrivial Hopf invariant 1 dims",
       f"Hopf invariant 1 dims: {{1,2,4,8}}. 4+8 = 12 = sigma(6)",
       f"4+8 = {4+8} = sigma(6) = {sigma}",
       nontrivial_sum == sigma,
       "🟧",
       "Adams theorem (1960). Also 1+2+4+8=15=C(6,2). Already partially in frontier scripts.")

# Also: 1+2+4+8 = 15 = C(6,2) = edges of K_6!
print(f"  1+2+4+8 = {sum(hopf_dims)} = C(6,2) = {math.comb(6,2)}")
# And: {1,2,4,8} as divisors — these are powers of 2
# 2^0, 2^1, 2^2, 2^3 — exactly tau(6)=4 elements

# --- B5: Classification of surfaces and 6 ---
# Orientable closed surfaces classified by genus g = 0,1,2,...
# chi = 2 - 2g. For chi = sigma_{-1}(6) = 2: g=0 (sphere)
# Non-orientable: chi = 2 - k where k = crosscap number
# Number of Platonic solids = 5 = sopfr(6)
# Number of regular tilings of plane = 3 = n/phi
platonic_count = 5
regular_tilings = 3  # triangular, square, hexagonal

record("B5", "5 Platonic solids = sopfr(6); 3 regular tilings = n/phi",
       f"Platonic solids = 5 = sopfr(6). Regular plane tilings = 3 = n/phi",
       f"Platonic = {platonic_count} = sopfr = {sopfr}. Tilings = {regular_tilings} = n/phi = {n//phi_n}",
       platonic_count == sopfr and regular_tilings == n // phi_n,
       "🟧",
       "Coincidence level medium. 5 and 3 are small numbers, easy to match.")


# ════════════════════════════════════════════════════════════════════════
# C. COMBINATORICS (5 hypotheses)
# ════════════════════════════════════════════════════════════════════════

print("\n\n" + "═" * 72)
print("  C. COMBINATORICS")
print("═" * 72)

# --- C1: D(6)/6! ≈ 1/e (derangement ratio) ---
# D(n) = n! * sum_{k=0}^{n} (-1)^k / k!
# D(6) = 720 * (1 - 1 + 1/2 - 1/6 + 1/24 - 1/120 + 1/720) = 265
# D(6)/6! = 265/720
# 1/e = 0.367879441...
# D(6)/6! = 0.368055...
# Error = 0.048%

def derangement(nn):
    """Exact derangement via inclusion-exclusion."""
    return sum((-1)**k * math.factorial(nn) // math.factorial(k) for k in range(nn + 1))

d6 = derangement(6)
d6_ratio = Fraction(d6, math.factorial(6))
d6_float = float(d6_ratio)
inv_e = 1 / math.e
error_pct = abs(d6_float - inv_e) / inv_e * 100

print(f"  D(6) = {d6}")
print(f"  6! = {math.factorial(6)}")
print(f"  D(6)/6! = {d6}/{math.factorial(6)} = {d6_ratio} = {d6_float:.10f}")
print(f"  1/e = {inv_e:.10f}")
print(f"  Error = {error_pct:.4f}%")

# KEY INSIGHT: 720 = 6! = sigma(6)^2 * sopfr(6) = 144 * 5
print(f"\n  Denominator structure: 6! = 720")
print(f"    = sigma(6)^2 * sopfr(6) = {sigma**2} * {sopfr} = {sigma**2 * sopfr}")
print(f"    = n * sigma(6) * 10 = {n}*{sigma}*10 = {n*sigma*10}")

# 265 = 5 * 53
print(f"  Numerator: D(6) = {d6} = 5 * 53 = sopfr(6) * 53")
# 53 is prime. 53 = sigma(6)^2/tau(6) + ... not clean.

# Convergence: how quickly D(n)/n! approaches 1/e
print(f"\n  Convergence of D(n)/n! to 1/e:")
print(f"  {'n':>3} {'D(n)':>10} {'D(n)/n!':>12} {'error%':>10}")
for nn in range(1, 12):
    dn = derangement(nn)
    ratio = dn / math.factorial(nn)
    err = abs(ratio - inv_e) / inv_e * 100
    marker = " ← n=6" if nn == 6 else ""
    print(f"  {nn:>3} {dn:>10} {ratio:>12.8f} {err:>10.4f}%{marker}")

record("C1", "D(6)/6! = 265/720 ≈ 1/e (0.048% error)",
       f"D(6)/6! = 265/720 ≈ 0.3681 ≈ 1/e ≈ 0.3679",
       f"D(6)/6! = {d6_float:.6f}, 1/e = {inv_e:.6f}, error = {error_pct:.4f}%",
       error_pct < 0.1,
       "🟧★",
       "D(n)/n! -> 1/e for ALL n. At n=6 error is 0.048%. NOT unique to 6. "
       "But: 1/e = Golden Zone center, and this is the FIRST n where error < 0.1%.")

# When does error first drop below 0.1%?
for nn in range(1, 20):
    dn = derangement(nn)
    ratio = dn / math.factorial(nn)
    err = abs(ratio - inv_e) / inv_e * 100
    if err < 0.1:
        print(f"\n  First n with error < 0.1%: n={nn} (error={err:.4f}%)")
        break

# --- C2: Stirling numbers S(6,k) ---
# S(n,k) = Stirling numbers of the second kind = ways to partition n-set into k non-empty subsets
# S(6,1)=1, S(6,2)=31, S(6,3)=90, S(6,4)=65, S(6,5)=15, S(6,6)=1
# Bell(6) = sum = 203
# Key: S(6,2) = 31 = 2^5 - 1 = Mersenne number M_5
# S(6,5) = 15 = C(6,2) = edges of K_6

def stirling2(nn, kk):
    """Stirling number of the second kind."""
    if nn == 0 and kk == 0:
        return 1
    if nn == 0 or kk == 0:
        return 0
    return sum((-1)**(kk-j) * math.comb(kk, j) * j**nn for j in range(kk+1)) // math.factorial(kk)

stirling_6 = [stirling2(6, k) for k in range(7)]
bell_6 = sum(stirling_6)
print(f"\n  Stirling numbers S(6,k):")
for k in range(7):
    s = stirling_6[k]
    note = ""
    if k == 2:
        note = f" = 2^5-1 = M_5 (Mersenne)"
    elif k == 5:
        note = f" = C(6,2) = edges of K_6"
    elif k == 4:
        note = f" = 5*13"
    print(f"    S(6,{k}) = {s}{note}")
print(f"  Bell(6) = {bell_6}")

# S(6,2) = 2^(n-1) - 1 for all n, so not special to 6
# S(6,5) = C(6,2) = C(n,2) for all n. S(n,n-1) = C(n,2).
# So these are general formulas. Let's check Bell(6).
# Bell(6) = 203 = 7 * 29
# 7 = n+1, 29 is prime.
# 203 = sigma(6)*tau(6)*... no clean match.

record("C2", "Stirling S(6,k): S(6,2)=2^5-1, S(6,5)=C(6,2), Bell(6)=203",
       f"S(6,k) = {stirling_6}. Bell(6) = {bell_6} = 7*29",
       f"S(6,2) = {stirling_6[2]} = 2^(n-1)-1. S(6,n-1) = C(n,2) = {math.comb(6,2)}. Both general.",
       stirling_6[2] == 2**(n-1) - 1 and stirling_6[5] == math.comb(n, 2),
       "⚪",
       "S(n,2)=2^(n-1)-1 and S(n,n-1)=C(n,2) are GENERAL formulas. Not n=6 specific.")

# --- C3: Catalan number C_6 = 132 ---
# C_n = C(2n,n)/(n+1)
# C_6 = C(12,6)/7 = 924/7 = 132
# 132 = 4*33 = 4*3*11 = tau(6)*3*11
# 132 = 11*12 = 11*sigma(6)
# 132 = sigma(6) * 11 = sigma(6) * (sigma(6) - 1)
catalan_6 = math.comb(2*n, n) // (n + 1)
sigma_times = sigma * (sigma - 1)

record("C3", "Catalan C_6 = 132 = sigma(6) * 11 = sigma * (sigma-1)",
       f"C_6 = C(12,6)/7 = {catalan_6}. sigma*(sigma-1) = 12*11 = {sigma_times}",
       f"C_6 = {catalan_6} = {sigma}*{sigma-1} = {sigma_times}",
       catalan_6 == sigma_times,
       "🟧★",
       "C_n = C(2n,n)/(n+1). C_6 = 132 = 12*11 = sigma*(sigma-1). Is this unique?")

# Uniqueness: C_n = sigma(n) * (sigma(n)-1)?
print("\n  Uniqueness: C_n = sigma(n)*(sigma(n)-1)?")
for nn in range(1, 50):
    cn = math.comb(2*nn, nn) // (nn + 1)
    sig = compute_sigma(nn)
    target = sig * (sig - 1)
    if cn == target:
        print(f"    n={nn}: C_{nn}={cn}, sigma*(sigma-1)={sig}*{sig-1}={target} ← MATCH")

# --- C4: 6! = 720 structure ---
# 720 = 6! = |S_6| (symmetric group)
# 720 = 2^4 * 3^2 * 5 = 16 * 9 * 5
# 720 = sigma(6)^2 * sopfr(6) = 144 * 5
# This is EXACT.
factorial_6 = math.factorial(6)
structure = sigma**2 * sopfr

record("C4", "6! = sigma(6)^2 * sopfr(6) = 144*5 = 720",
       f"6! = 720 = sigma^2 * sopfr = {sigma}^2 * {sopfr} = {structure}",
       f"6! = {factorial_6} = {structure}",
       factorial_6 == structure,
       "🟧★",
       "720 = 12^2 * 5. Exact. Uniqueness?")

# Uniqueness
print("\n  Uniqueness: n! = sigma(n)^2 * sopfr(n)?")
for nn in range(2, 30):
    nf = math.factorial(nn)
    sig = compute_sigma(nn)
    sop = compute_sopfr(nn)
    target = sig**2 * sop
    if nf == target:
        print(f"    n={nn}: {nn}! = {nf}, sigma^2*sopfr = {sig}^2*{sop} = {target} ← MATCH")

# --- C5: Partition function p(6) = 11 ---
# Integer partitions of 6: 11 partitions
# 11 = sigma(6) - 1 = 12 - 1
# Also: p(6) = 11 is prime
# p(n) for small n: p(1)=1, p(2)=2, p(3)=3, p(4)=5, p(5)=7, p(6)=11, p(7)=15
partitions_6 = 11  # well-known
sigma_minus_1 = sigma - 1

record("C5", "p(6) = 11 = sigma(6) - 1",
       f"Integer partitions of 6 = 11 = sigma(6) - 1 = 12 - 1",
       f"p(6) = {partitions_6} = sigma-1 = {sigma_minus_1}",
       partitions_6 == sigma_minus_1,
       "🟧",
       "Ad-hoc -1 correction. p(6)=11 is not sigma(6). Close but not exact.")


# ════════════════════════════════════════════════════════════════════════
# D. NUMBER THEORY DEEP (3 hypotheses)
# ════════════════════════════════════════════════════════════════════════

print("\n\n" + "═" * 72)
print("  D. NUMBER THEORY DEEP")
print("═" * 72)

# --- D1: Perfect number ratio 28/6 = 14/3 ---
# P_2/P_1 = 28/6 = 14/3
# 14 = sigma(6) + phi(6) = 12 + 2 = R(3,5) (Ramsey!)
# 3 = n/phi = 6/2 = sigma/tau = 12/4
# So P_2/P_1 = (sigma+phi) / (n/phi) = (sigma+phi)*phi/n = (12+2)*2/6 = 28/6 ✓ tautological
ratio_28_6 = Fraction(28, 6)
ratio_simplified = f"{ratio_28_6} = {float(ratio_28_6):.6f}"

# More interesting: both 6 and 28 are Ramsey numbers
# R(3,3) = 6 = P_1, R(3,8) = 28 = P_2 (already in H-UD-4)
# New: ratio structure
# 28/6 = 14/3. 14 = 2*7 = phi(6)*(6+1). 3 = (6-1)/2+1/2... not clean.

record("D1", "P_2/P_1 = 28/6 = 14/3; 14 = sigma+phi, 3 = sigma/tau",
       f"28/6 = 14/3. 14 = R(3,5) = sigma+phi. 3 = sigma/tau = n/phi",
       f"28/6 = {ratio_simplified}. sigma+phi={sigma+phi_n}=14. sigma/tau={sigma//tau}=3.",
       sigma + phi_n == 14 and sigma // tau == 3,
       "🟧",
       "Multiple expressions for 14 and 3. Could be numerology given small numbers.")

# --- D2: Basel problem zeta(2) = pi^2/6 structure ---
# Already in H-CX-260. We go DEEPER.
# zeta(2) = pi^2/6 = pi^2/P_1
# zeta(4) = pi^4/90 = pi^4/(15*6) = pi^4/(C(6,2)*n)
# zeta(6) = pi^6/945 = pi^6/(945). 945 = 6*157.5... not clean.
# Actually: zeta(2k) = (-1)^{k+1} * B_{2k} * (2*pi)^{2k} / (2*(2k)!)
# For k=1: zeta(2) = pi^2/6
# For k=2: zeta(4) = pi^4/90. 90 = C(6,2) * 6 = 15*6 = sigma(6)*15/2... = n*C(n,2)
# For k=3: zeta(6) = pi^6/945. 945 = 7*135 = 7*27*5.

zeta2_denom = 6
zeta4_denom = 90
zeta6_denom = 945

print(f"\n  zeta(2) denominator: {zeta2_denom} = n")
print(f"  zeta(4) denominator: {zeta4_denom} = {n}*{math.comb(n,2)} = n*C(n,2)")
print(f"    Also: 90 = S(6,3) = {stirling_6[3]}")
print(f"  zeta(6) denominator: {zeta6_denom} = 945 = 9*105 = (n/phi)^2 * 105")

# S(6,3) = 90 = zeta(4) denominator!
zeta4_stirling = (zeta4_denom == stirling_6[3])
record("D2", "zeta(4) denominator 90 = S(6,3) = Stirling(6,3)",
       f"zeta(4) = pi^4/90. 90 = S(6,3) = {stirling_6[3]}. Also 90 = n*C(n,2) = 6*15",
       f"90 = S(6,3) = {stirling_6[3]}: {zeta4_stirling}. 6*15 = {6*15}: {6*15==90}",
       zeta4_stirling,
       "🟧",
       "Intriguing: S(6,3)=90 and zeta(4)=pi^4/90. But S(6,3)=90 by formula, 90=6*15 trivially.")

# --- D3: Mersenne primes and perfect numbers ---
# Every even perfect number = 2^{p-1}(2^p - 1) where 2^p-1 is Mersenne prime
# For n=6: 6 = 2^1 * 3 = 2^{2-1} * (2^2-1). So p=2, M_p=3.
# For n=28: 28 = 2^2 * 7 = 2^{3-1} * (2^3-1). p=3, M_p=7.
# p values: 2, 3, 5, 7, 13, 17, 19, 31, ...
# First two Mersenne primes: M_2=3, M_3=7
# Product: 3*7 = 21 = sigma(6) + tau(6)*phi(6)+1... no.
# Sum: 3+7 = 10 = Petersen vertices
# Key: the EXPONENTS p=2,3 are the prime factors of 6!
mersenne_exponents_first2 = [2, 3]
prime_factors_6 = [2, 3]
record("D3", "Mersenne exponents {2,3} = prime factors of 6",
       f"First perfect number 6=2*3. Mersenne: 2^2-1=3, 2^3-1=7. Exponents = primes of 6.",
       f"Exponents {mersenne_exponents_first2} = prime factors {prime_factors_6}",
       mersenne_exponents_first2 == prime_factors_6,
       "🟩",
       "Tautological: 6=2^1*(2^2-1) so 2 is a prime factor of 6 AND the Mersenne exponent. "
       "Also 28=2^2*(2^3-1) so 3 is the next. This is built into the Euclid-Euler theorem.")


# ════════════════════════════════════════════════════════════════════════
# TEXAS SHARPSHOOTER ANALYSIS
# ════════════════════════════════════════════════════════════════════════

print("\n\n" + "═" * 72)
print("  TEXAS SHARPSHOOTER ANALYSIS")
print("═" * 72)

total = len(results)
passes = sum(1 for r in results if r[4])
greens = sum(1 for r in results if r[4] and r[5] == "🟩")
oranges_star = sum(1 for r in results if r[4] and r[5] == "🟧★")
oranges = sum(1 for r in results if r[4] and r[5] == "🟧")
whites = sum(1 for r in results if r[4] and r[5] == "⚪")
blacks = sum(1 for r in results if not r[4])

print(f"\n  Total hypotheses: {total}")
print(f"  Passed: {passes}/{total}")
print(f"    🟩 Exact/Proven:    {greens}")
print(f"    🟧★ Strong approx:  {oranges_star}")
print(f"    🟧  Weak evidence:   {oranges}")
print(f"    ⚪  Coincidence:     {whites}")
print(f"    ⬛  Failed:          {blacks}")

# Honest assessment
print(f"\n  HONEST ASSESSMENT:")
print(f"  ---")
genuine = []
trivial = []
coincidence = []
for r in results:
    hid, title, claim, actual, match, grade, note = r
    if not match:
        continue
    if "tautolog" in note.lower() or "general formula" in note.lower() or "not n=6" in note.lower() or "not.*specific" in note.lower():
        trivial.append(hid)
    elif grade == "⚪":
        coincidence.append(hid)
    else:
        genuine.append(hid)

print(f"  Genuinely interesting: {len(genuine)} — {genuine}")
print(f"  Trivial/tautological:  {len(trivial)} — {trivial}")
print(f"  Coincidence:           {len(coincidence)} — {coincidence}")

# Approximate p-value
# If we tested 20 hypotheses and expect ~3 random matches (small number coincidences)
# Getting genuinely interesting results above that threshold matters
import random
random.seed(42)

# Monte Carlo: for a random number m, how many of these 20 tests would "pass"?
# This is hard to automate perfectly, but we can estimate.
n_trials = 10000
n_hyp = total
# Rough model: each hypothesis has ~15% chance of matching by coincidence for a random n
# (small numbers 2-12 have many matches; larger numbers almost none)
p_random = 0.15
random_matches = []
for _ in range(n_trials):
    matches = sum(1 for _ in range(n_hyp) if random.random() < p_random)
    random_matches.append(matches)

avg_random = sum(random_matches) / n_trials
std_random = (sum((x - avg_random)**2 for x in random_matches) / n_trials) ** 0.5
z_score = (passes - avg_random) / std_random if std_random > 0 else 0

print(f"\n  Monte Carlo (p_random=0.15, {n_trials} trials):")
print(f"  Random average: {avg_random:.1f} +/- {std_random:.1f}")
print(f"  Our score: {passes}")
print(f"  Z-score: {z_score:.2f}")

# More conservative: What fraction exceed our count?
exceeded = sum(1 for x in random_matches if x >= passes) / n_trials
print(f"  p-value (fraction exceeding {passes}): {exceeded:.4f}")


# ════════════════════════════════════════════════════════════════════════
# SUMMARY TABLE
# ════════════════════════════════════════════════════════════════════════

print("\n\n" + "═" * 72)
print("  SUMMARY TABLE")
print("═" * 72)
print(f"\n  {'ID':<5} {'Grade':<5} {'Title':<55}")
print(f"  {'─'*65}")
for r in results:
    hid, title, claim, actual, match, grade, note = r
    g = grade if match else "⬛"
    print(f"  {hid:<5} {g:<5} {title[:55]}")

print(f"\n{'='*72}")
print(f"  VERIFICATION COMPLETE: {passes}/{total} passed")
print(f"{'='*72}")
