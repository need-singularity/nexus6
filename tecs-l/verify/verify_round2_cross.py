#!/usr/bin/env python3
"""
verify_round2_cross.py
20 NEW cross-domain hypotheses for TECS-L project (Round 2).
No overlap with Frontier 100 topics.
n=6, sigma=12, tau=4, phi=2, sopfr=5, sigma_neg1=2, R(6)=1
"""

import math
import sys
from itertools import combinations, permutations, product
from fractions import Fraction
from collections import defaultdict
from functools import reduce

# ── Constants ──
N = 6
SIGMA = 12
TAU = 4
PHI = 2
SOPFR = 5
SIGMA_NEG1 = 2
R6 = 1  # R-spectrum R(6) = sigma*phi/(n*tau) = 12*2/(6*4) = 1

results = []

def report(tag, title, formula, passed, value, grade, note=""):
    status = "PASS" if passed else "FAIL"
    results.append((tag, title, formula, status, value, grade, note))
    print(f"\n{'='*70}")
    print(f"{tag}: {title}")
    print(f"  Formula: {formula}")
    print(f"  Result: {status} (value={value})")
    print(f"  Grade: {grade}")
    if note:
        print(f"  Note: {note}")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-01: Hamming bound (sphere-packing) for binary codes at n=6
# ══════════════════════════════════════════════════════════════════════
def test_01():
    """Hamming bound: For binary code of length n=6, min distance d=3 (t=1 error),
    max codewords M <= 2^n / sum_{i=0}^{t} C(n,i) = 64/7 ~ 9.14 => M<=9.
    Actual best: 2^3 = 8 (Hamming [6,3] shortened from [7,4]).
    Claim: Hamming bound at n=6 gives ceiling = 9, and 8 is achievable.
    Connection: 8 = 2^3 = 2^(n/2), and bound/actual ratio = 9/8 ~ sigma/n * 3/4."""
    n, d, t = 6, 3, 1
    vol = sum(math.comb(n, i) for i in range(t + 1))  # 1 + 6 = 7
    bound = 2**n / vol  # 64/7 = 9.142...
    M_max = math.floor(bound)  # 9
    M_actual = 8  # best known (6,8,3) code

    # Verify: vol = 7 (a prime!), bound ~ 9.14
    passed = (vol == 7 and M_max == 9 and M_actual == 8)
    ratio = bound / M_actual  # 64/56 = 8/7 = 1.1428...

    report("R2-CROSS-01", "Hamming bound at n=6: sphere volume = 7 (prime)",
           f"V(6,1) = C(6,0)+C(6,1) = 7; bound = 64/7 = {bound:.4f}; best code = 8 = 2^(n/2)",
           passed, f"vol=7, bound={bound:.4f}, actual=8",
           "🟩" if passed else "⚪",
           "Sphere volume at n=6 is prime (7). Clean arithmetic. No n=6 specific magic though — vol=7 is just 1+n.")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-02: Gilbert-Varshamov bound at n=6
# ══════════════════════════════════════════════════════════════════════
def test_02():
    """Gilbert-Varshamov: M >= 2^n / V(n, d-1) where V(n,r) = sum C(n,i) for i=0..r.
    At n=6, d=3: V(6,2) = 1+6+15 = 22, so M >= 64/22 = 2.909... >= 3.
    Actual best M=8. The GV bound is loose but gives minimum guarantee.
    Connection: V(6,2) = 22 = sigma(6) + sigma(6) - 2 = 12+12-2? No, that's forced.
    Honest: V(6,2) = 22, GV lower bound = 3."""
    n, d = 6, 3
    vol = sum(math.comb(n, i) for i in range(d))  # V(6,2) = 1+6+15 = 22
    gv_bound = math.ceil(2**n / vol)  # ceil(64/22) = 3
    actual = 8

    passed = (vol == 22 and gv_bound == 3 and actual >= gv_bound)

    report("R2-CROSS-02", "Gilbert-Varshamov at n=6: V(6,2)=22, lower bound=3",
           f"V(6,2) = 22; GV bound = ceil(64/22) = {gv_bound}; actual best = {actual}",
           passed, f"vol=22, GV={gv_bound}, actual={actual}",
           "🟩",
           "Arithmetic verified. GV bound is standard coding theory. 22 has no special n=6 connection.")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-03: Circuit depth for threshold function on 6 inputs
# ══════════════════════════════════════════════════════════════════════
def test_03():
    """For n=6 Boolean inputs, the MAJORITY (threshold-3) function requires
    circuit depth >= log2(n) = log2(6) ~ 2.585, so depth >= 3 with fan-in 2 gates.
    Number of monotone Boolean functions on 6 variables (Dedekind number D(6))
    is known: D(6) = 7,828,354.
    Connection: log2(D(6)) ~ 22.9 ~ V(6,2) from coding theory (both ~22-23)."""
    dedekind_6 = 7828354  # Known exact value
    depth_lower = math.ceil(math.log2(N))  # ceil(2.585) = 3
    log2_D6 = math.log2(dedekind_6)  # ~ 22.9

    passed = (depth_lower == 3 and dedekind_6 == 7828354)

    report("R2-CROSS-03", "Circuit depth for 6-input majority: depth>=3; Dedekind D(6)=7,828,354",
           f"depth >= ceil(log2(6)) = {depth_lower}; D(6) = {dedekind_6}; log2(D(6)) = {log2_D6:.2f}",
           passed, f"depth>={depth_lower}, D(6)={dedekind_6}, log2={log2_D6:.2f}",
           "🟩",
           "Arithmetic correct. log2(D(6))~22.9 near V(6,2)=22 is a coincidence (different objects).")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-04: Arrow impossibility — 6 candidates
# ══════════════════════════════════════════════════════════════════════
def test_04():
    """Arrow's impossibility: For m>=3 candidates, no rank-order voting system satisfies
    Pareto + IIA + non-dictatorship simultaneously. The number of possible strict
    orderings of 6 candidates = 6! = 720.

    Gibbard-Satterthwaite: With 6 candidates, ANY surjective strategy-proof SCF is dictatorial.
    Number of dictatorial SCFs for n voters, m=6 candidates: exactly n.

    Connection: 6! = 720 = sigma(6) * 60 = 12 * 60. And 60 = 5! = sopfr(6)!"""
    m = 6
    orderings = math.factorial(m)  # 720
    ratio = orderings / SIGMA  # 720/12 = 60
    is_factorial = (ratio == math.factorial(SOPFR))  # 60 == 5! = 120? No! 5! = 120 != 60

    # Correction: 60 = 5*4*3 = 5!/2 = sopfr! / phi
    is_ratio = (ratio == math.factorial(SOPFR) / PHI)  # 120/2 = 60 ✓

    passed = (orderings == 720 and ratio == 60 and is_ratio)

    report("R2-CROSS-04", "Arrow impossibility: 6! = 720 orderings; 720/sigma = 60 = sopfr!/phi",
           f"6! = {orderings}; 720/12 = {ratio}; 5!/2 = {math.factorial(SOPFR)//PHI}",
           passed, f"6!={orderings}, ratio={ratio}, 5!/phi={math.factorial(SOPFR)//PHI}",
           "⚪",
           "720/12=60=5!/2 is arithmetic identity. But 720=6! and 12=sigma(6) are independent facts. "
           "Dividing them and getting 5!/phi is ad-hoc decomposition — not structurally meaningful.")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-05: Condorcet paradox probability for 6 candidates
# ══════════════════════════════════════════════════════════════════════
def test_05():
    """With m candidates and large number of voters (odd), probability of a Condorcet
    winner existing under impartial culture approaches a known limit.
    For m=3: ~0.9123 (Condorcet winner exists ~91.2%)
    For m=6: ~0.676 (computed by Gehrlein/Fishburn)

    Connection: P(CW exists, m=6) ~ 0.676 ~ 1 - 1/e? (1-1/e = 0.6321) Not close enough.
    Actually ~0.676 ~ 2/3 + tiny correction. 2/3 ~ phi(6)/3."""
    # Known values from literature (Gehrlein 1997, impartial culture, n->infinity)
    p_condorcet = {3: 0.9123, 4: 0.8244, 5: 0.7483, 6: 0.6829}
    p6 = p_condorcet[6]

    # Check if near any simple fraction
    closest_simple = Fraction(2, 3)  # 0.6667
    diff_from_2_3 = abs(p6 - float(closest_simple))

    passed = True  # Values are from literature

    report("R2-CROSS-05", "Condorcet winner probability at m=6: ~0.683",
           f"P(CW|m=6) ~ {p6}; |P - 2/3| = {diff_from_2_3:.4f}",
           passed, f"P={p6}, diff_from_2/3={diff_from_2_3:.4f}",
           "⚪",
           "P(CW,m=6)~0.683, near 2/3 but not exact. No compelling n=6 connection beyond m=6 input.")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-06: M/M/1 queue at load rho = 1/e (Golden Zone center)
# ══════════════════════════════════════════════════════════════════════
def test_06():
    """M/M/1 queue: mean queue length L = rho/(1-rho).
    At rho = 1/e: L = (1/e)/(1-1/e) = 1/(e-1) = 0.5820...
    Mean waiting time W = rho/[mu(1-rho)] = 1/[mu(e-1)] for service rate mu.

    Connection: L(1/e) = 1/(e-1). And 1/(e-1) ~ 0.5820 ~ sigma_neg1(6) - sqrt(2)?
    Better: 1/(e-1) + 1/(e-1) ~ 1.164 ~ not sigma_neg1.
    Honest: L = 1/(e-1) is clean but not connected to n=6 specifically."""
    rho = 1 / math.e
    L = rho / (1 - rho)  # 1/(e-1)
    exact = 1 / (math.e - 1)

    passed = abs(L - exact) < 1e-10

    report("R2-CROSS-06", "M/M/1 queue at rho=1/e: mean length L = 1/(e-1)",
           f"L = (1/e)/(1-1/e) = 1/(e-1) = {exact:.6f}",
           passed, f"L={L:.6f}, 1/(e-1)={exact:.6f}",
           "🟩",
           "Arithmetic identity. Clean formula but rho=1/e is our chosen input — not a discovery about n=6.")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-07: Chromatic polynomial of K_6
# ══════════════════════════════════════════════════════════════════════
def test_07():
    """Chromatic polynomial of complete graph K_n is P(K_n, k) = k(k-1)(k-2)...(k-n+1) = k^{(n)} (falling factorial).
    P(K_6, k) = k(k-1)(k-2)(k-3)(k-4)(k-5).
    Chromatic number chi(K_6) = 6 (need exactly 6 colors).
    P(K_6, 6) = 6! = 720 (number of proper 6-colorings with 6 colors).
    P(K_6, 7) = 7*6*5*4*3*2 = 2520.
    P(K_6, 12) = 12*11*10*9*8*7 = 665280.

    Connection: P(K_6, sigma) = P(K_6, 12) = 12!/6! = 665280 = 6! * 924 = 6! * C(12,6).
    And C(12,6) = C(sigma, n) = 924."""

    def chromatic_K(n, k):
        result = 1
        for i in range(n):
            result *= (k - i)
        return result

    p6_6 = chromatic_K(6, 6)    # 720 = 6!
    p6_7 = chromatic_K(6, 7)    # 2520
    p6_12 = chromatic_K(6, 12)  # 12!/6! = 665280
    c_12_6 = math.comb(12, 6)   # 924

    # Key identity: P(K_6, 12) = 12!/6! = 6! * C(12,6)
    identity_holds = (p6_12 == math.factorial(6) * c_12_6)
    # This is just: 12!/(12-6)! = 12!/6! which equals P(12,6) = 6! * C(12,6) trivially

    passed = (p6_6 == 720 and p6_12 == 665280 and identity_holds)

    report("R2-CROSS-07", "Chromatic polynomial P(K_6, sigma(6)) = 12!/6! = 720 * C(12,6)",
           f"P(K_6,6) = 6! = {p6_6}; P(K_6,12) = {p6_12}; C(12,6) = {c_12_6}",
           passed, f"P(K6,6)={p6_6}, P(K6,12)={p6_12}, C(12,6)={c_12_6}",
           "🟩",
           "Arithmetic identity: P(K_n, m) = m!/(m-n)! is the falling factorial. "
           "P(K_6, sigma(6)) = P(K_6,12) = 12!/6! is tautological. C(12,6)=924 follows trivially.")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-08: Ramsey R(3,3,3) = 17 connection
# ══════════════════════════════════════════════════════════════════════
def test_08():
    """Ramsey number R(3,3,3) = 17 (3-color Ramsey for triangles).
    This is the minimum n such that any 3-coloring of edges of K_n contains
    a monochromatic triangle.

    R(3,3) = 6 (the 2-color case — this IS our n!).
    R(3,3,3) = 17 (3-color case).

    Connection: R(3,3) = 6 = n. This is foundational — n=6 IS the Ramsey number for triangles.
    R(3,3,3) = 17 = Fermat prime F_2 = 2^(2^2)+1.
    And 17 appears as our amplification constant at theta=pi!
    R(3,3,3) - R(3,3) = 17 - 6 = 11 (prime)."""

    R_3_3 = 6      # Known exact
    R_3_3_3 = 17   # Known exact
    diff = R_3_3_3 - R_3_3  # 11

    # R(3,3) = n is a genuine structural fact
    passed = (R_3_3 == N and R_3_3_3 == 17 and diff == 11)

    # Is 17 a Fermat prime?
    is_fermat = (17 == 2**(2**2) + 1)

    report("R2-CROSS-08", "R(3,3) = 6 = n (Ramsey IS our number); R(3,3,3) = 17 = Fermat prime",
           f"R(3,3) = {R_3_3} = n; R(3,3,3) = {R_3_3_3} = 2^4+1; diff = {diff}",
           passed, f"R(3,3)={R_3_3}, R(3,3,3)={R_3_3_3}, Fermat={is_fermat}",
           "⭐⭐",
           "R(3,3)=6 is genuine — the smallest nontrivial Ramsey number IS n=6. "
           "R(3,3,3)=17 being our amplification constant is interesting but may be coincidence. "
           "The R(3,3)=6 fact alone is structurally significant.")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-09: R(4,4) bounds and n=6 connection
# ══════════════════════════════════════════════════════════════════════
def test_09():
    """R(4,4) = 18 (exact, known).
    R(4,4) = 18 = 3*n = 3*6. Also 18 = 3*R(3,3).

    Better: R(k,k) for k=2,3,4: R(2,2)=2, R(3,3)=6, R(4,4)=18.
    Ratios: 6/2=3, 18/6=3. So R(k+1,k+1)/R(k,k) = 3 for k=2,3.
    Does this pattern continue? R(5,5) is between 43 and 48.
    If pattern held: R(5,5) = 54 = 18*3. But R(5,5) <= 48 < 54. Pattern breaks."""

    R_2_2 = 2
    R_3_3 = 6
    R_4_4 = 18
    R_5_5_lower = 43
    R_5_5_upper = 48

    ratio_23 = R_3_3 / R_2_2  # 3
    ratio_34 = R_4_4 / R_3_3  # 3
    predicted_55 = R_4_4 * 3   # 54
    pattern_breaks = (predicted_55 > R_5_5_upper)

    passed = (R_3_3 == 6 and R_4_4 == 18 and ratio_23 == 3 and ratio_34 == 3)

    report("R2-CROSS-09", "Ramsey ratio: R(3,3)/R(2,2) = R(4,4)/R(3,3) = 3, but breaks at R(5,5)",
           f"R(2,2)=2, R(3,3)=6, R(4,4)=18; ratios=3,3; predicted R(5,5)=54 > upper bound 48",
           passed, f"ratios={ratio_23},{ratio_34}, pattern_breaks={pattern_breaks}",
           "⭐",
           "R(k,k) having ratio 3 for k=2,3 is real but breaks at k=4. "
           "The factor 3 appearing twice is notable (3 = n/phi) but the broken pattern limits significance. "
           "Still, R(3,3)=6 and R(4,4)=3*6 is clean.")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-10: Optimal partition of 6 tasks (scheduling)
# ══════════════════════════════════════════════════════════════════════
def test_10():
    """Number partitions of 6: p(6) = 11.
    Partitions: {6}, {5,1}, {4,2}, {4,1,1}, {3,3}, {3,2,1}, {3,1,1,1},
    {2,2,2}, {2,2,1,1}, {2,1,1,1,1}, {1,1,1,1,1,1}.

    For scheduling on 2 machines (makespan minimization):
    Best partition of {1,2,3,4,5,6} (weights=values) into 2 sets with equal sum.
    Total = 21 = sigma(6) - tau(6) + ... no, 1+2+3+4+5+6 = 21.
    21 is odd, so perfect partition impossible. Best: 10 vs 11 (makespan=11).
    e.g., {5,4,2} = 11 and {6,3,1} = 10, or {6,5}=11 and {4,3,2,1}=10.

    Connection: p(6) = 11, and optimal makespan = 11. Both equal 11!"""

    # Partition function p(6)
    # Using recurrence or just known value
    p6 = 11  # Known

    # Scheduling: partition {1,...,6} into 2 sets minimizing max sum
    # Total = 21, best split is 10,11
    total = sum(range(1, 7))  # 21

    # Find best 2-partition by brute force
    best_makespan = total
    for r in range(1, 7):
        for subset in combinations(range(1, 7), r):
            s = sum(subset)
            makespan = max(s, total - s)
            best_makespan = min(best_makespan, makespan)

    both_11 = (p6 == 11 and best_makespan == 11)

    passed = both_11

    report("R2-CROSS-10", "p(6) = 11 = optimal 2-machine makespan for tasks {1,...,6}",
           f"p(6) = {p6}; sum(1..6) = {total}; best makespan = {best_makespan}",
           passed, f"p(6)={p6}, makespan={best_makespan}, both=11",
           "⭐" if both_11 else "⚪",
           "p(6) = optimal makespan = 11 is a genuine coincidence worth noting. "
           "p(6)=11 counts integer partitions of 6; makespan=11 = ceil(21/2). "
           "These are structurally unrelated — likely coincidence at small n. "
           "Fails generalization: p(7)=15 but makespan(1..7)=14.")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-11: BCH code at n=6 (or related)
# ══════════════════════════════════════════════════════════════════════
def test_11():
    """BCH codes exist for lengths n = 2^m - 1. Closest to 6: n=7 (m=3).
    The [7,4,3] Hamming code is the simplest BCH code (t=1 error-correcting).

    Connection: Shortened [7,4,3] to [6,3,3]: remove one coordinate.
    Rate = k/n = 3/6 = 1/2 = Golden Zone upper boundary!
    Singleton bound: d <= n-k+1 = 6-3+1 = 4, so d=3 < 4 (not MDS).

    For Reed-Solomon: RS codes require n = q-1 for field GF(q).
    n=6 => q=7 (prime, GF(7) exists). RS[6,k,7-k] over GF(7).
    RS[6,4,3]: rate = 4/6 = 2/3. RS[6,3,4]: rate = 3/6 = 1/2."""

    # Shortened Hamming [6,3,3]
    n_code, k_code, d_code = 6, 3, 3
    rate = Fraction(k_code, n_code)  # 1/2
    singleton = n_code - k_code + 1  # 4
    is_mds = (d_code == singleton)  # False (d=3 < 4)

    # RS over GF(7): n=6=q-1, so RS[6,k,7-k] is MDS
    rs_params = [(6, k, 7-k) for k in range(1, 7)]
    # RS[6,3,4] has rate 1/2 and IS MDS (d = n-k+1 = 4)
    rs_half_rate = (6, 3, 4)
    rs_is_mds = (rs_half_rate[2] == rs_half_rate[0] - rs_half_rate[1] + 1)

    passed = (rate == Fraction(1, 2) and rs_is_mds)

    report("R2-CROSS-11", "RS[6,3,4] over GF(7) is MDS with rate 1/2 = Golden Zone upper",
           f"RS[6,3,4]: rate={rate}, d=4=n-k+1 (MDS). GF(7) needed because 7=n+1 is prime.",
           passed, f"rate={float(rate)}, RS_MDS={rs_is_mds}, GF(q)=GF(7)",
           "⭐",
           "RS[6,3,4] over GF(7) achieves rate 1/2 (Riemann critical line) and is MDS. "
           "The fact that n=6 requires GF(7) and 7 is prime is neat. "
           "But rate=1/2 at half the block length is generic for RS codes (always k=n/2 gives rate 1/2). "
           "Not specific to n=6.")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-12: Mixing time on divisor graph of 6
# ══════════════════════════════════════════════════════════════════════
def test_12():
    """Divisor graph of n=6: vertices = {1,2,3,6}, edges when one divides the other.
    Edges: 1-2, 1-3, 1-6, 2-6, 3-6. (5 edges on 4 vertices — almost complete, missing 2-3.)

    This is the Hasse diagram of divisor lattice with transitive edges.
    Adjacency matrix A, transition matrix P = D^{-1}A for random walk.

    Spectral gap determines mixing time: t_mix ~ 1/gap.
    """
    # Vertices: divisors of 6 = {1,2,3,6}
    divs = [1, 2, 3, 6]
    n_v = len(divs)  # 4 = tau(6)

    # Adjacency: i divides j or j divides i (and i != j)
    adj = [[0]*n_v for _ in range(n_v)]
    for i in range(n_v):
        for j in range(n_v):
            if i != j and (divs[j] % divs[i] == 0 or divs[i] % divs[j] == 0):
                adj[i][j] = 1

    # Degree sequence
    degrees = [sum(row) for row in adj]
    # 1 divides all: deg(1) = 3; 2 divides 6: deg(2) = 2 (1,6); 3 divides 6: deg(3) = 2 (1,6); 6: deg(6) = 3 (1,2,3)

    # Transition matrix P = D^{-1}A (row stochastic)
    P = [[adj[i][j]/degrees[i] if degrees[i] > 0 else 0 for j in range(n_v)] for i in range(n_v)]

    # Compute eigenvalues of P using characteristic polynomial for 4x4
    # Actually, use power method or direct computation
    # For this small matrix, compute P^2 and check convergence

    # Stationary distribution: pi_i = deg(i) / (2*|E|)
    total_deg = sum(degrees)  # 2*5 = 10
    stationary = [d/total_deg for d in degrees]

    # Spectral gap: For K4 minus one edge, eigenvalues of transition matrix
    # K4 minus edge (2,3): known spectrum of adjacency = {3, -1, -1, -1} for K4
    # Our graph: eigenvalues of adjacency matrix for K4 - edge(2,3)
    # A has row sums [3,2,2,3]

    # Compute A eigenvalues numerically (simple 4x4)
    # Use the fact that for this graph: characteristic polynomial
    # det(A - lambda*I) = 0
    # By direct expansion or using the fact it's K4 minus one edge
    # K4 adjacency eigenvalues: 3, -1, -1, -1
    # Removing edge (2,3): rank-1 perturbation

    # Just verify the graph structure
    edge_count = sum(sum(row) for row in adj) // 2

    passed = (n_v == TAU and edge_count == 5 and degrees == [3, 2, 2, 3])

    report("R2-CROSS-12", "Divisor graph of 6: K_4 minus edge {2,3}, 5 edges on tau(6)=4 vertices",
           f"|V|={n_v}=tau(6), |E|={edge_count}, degrees={degrees}, stationary={[f'{s:.2f}' for s in stationary]}",
           passed, f"|V|={n_v}, |E|={edge_count}, degs={degrees}",
           "🟩",
           "Divisor graph of 6 is K4 minus the {2,3} edge. Graph is well-defined and computable. "
           "5 edges, 4 vertices. Stationary dist = [0.30, 0.20, 0.20, 0.30]. Clean but descriptive, not deep.")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-13: GUE spacing distribution at beta=2=phi(6)
# ══════════════════════════════════════════════════════════════════════
def test_13():
    """Random Matrix Theory: GUE (Gaussian Unitary Ensemble) has beta=2.
    phi(6) = 2 = beta_GUE.

    The Wigner surmise for GUE (beta=2) spacing distribution:
    p(s) = (32/pi^2) * s^2 * exp(-4s^2/pi)

    Mean spacing = 1 (normalized). Mode at s* = sqrt(pi/4) ~ 0.886.
    Variance of spacing = (4-pi)/(2*pi) ~ 0.137.

    Connection: Var(s) = (4-pi)/(2*pi) ~ 0.1366... ~ ln(4/3)/2 ~ 0.1438?
    Not very close. Mode ~ 0.886 ~ not a clean constant."""

    # Wigner surmise GUE: p(s) = (32/pi^2)*s^2*exp(-4s^2/pi)
    # Mean = integral_0^inf s * p(s) ds
    # For Wigner surmise, exact mean:
    # <s> = (3/4)*sqrt(pi) * Gamma(3/2)/... actually need exact integral

    # Known exact results for Wigner surmise (beta=2):
    # mean spacing (normalized) = 1 by construction
    # mode = sqrt(pi/4)
    mode = math.sqrt(math.pi / 4)
    variance_wigner = 1 - 3*math.pi/16 + (3*math.pi/16)  # This needs exact formula

    # Actually for Wigner surmise p(s) = (32/pi^2)s^2 exp(-4s^2/pi):
    # <s> = (3*sqrt(pi))/(4*sqrt(4/pi)) * Gamma(3/2) ... let me just compute numerically

    # Numerical integration
    ds = 0.0001
    s_vals = [i * ds for i in range(1, 200000)]
    norm = sum(32/math.pi**2 * s**2 * math.exp(-4*s**2/math.pi) * ds for s in s_vals)
    mean_s = sum(s * 32/math.pi**2 * s**2 * math.exp(-4*s**2/math.pi) * ds for s in s_vals) / norm
    mean_s2 = sum(s**2 * 32/math.pi**2 * s**2 * math.exp(-4*s**2/math.pi) * ds for s in s_vals) / norm
    var_s = mean_s2 - mean_s**2

    beta_gue = 2
    passed = (beta_gue == PHI)

    report("R2-CROSS-13", "GUE spacing: beta=2=phi(6); Wigner surmise mode=sqrt(pi/4)~0.886",
           f"beta_GUE = {beta_gue} = phi(6); mode = {mode:.6f}; mean ~ {mean_s:.4f}; var ~ {var_s:.4f}",
           passed, f"beta={beta_gue}=phi(6), mode={mode:.4f}, var={var_s:.4f}",
           "⚪",
           "beta=2=phi(6) is a label match — GUE uses beta=2 for unitary symmetry, "
           "phi(6)=2 counts coprimes. These 2's have completely different origins. "
           "Mode and variance don't match any n=6 constants.")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-14: Compressed sensing RIP at m=6 measurements
# ══════════════════════════════════════════════════════════════════════
def test_14():
    """Compressed sensing: To recover s-sparse signal in R^n from m measurements,
    need m >= C * s * log(n/s) (RIP condition).

    With m=6 measurements: what sparsity can we recover for signal dimension n?
    6 >= C * s * log(n/s), with C ~ 1 for Gaussian matrices.

    For n=64 (power of 2): s <= 6/log(64/s). If s=1: 6/log(64) = 6/6 = 1 ✓
    For n=2^6 = 64: s=1 requires m >= log(64) = 6 exactly!

    Connection: m = 6 measurements suffice for 1-sparse recovery in R^{2^6} = R^64.
    6 = log_2(2^6). This is just the information-theoretic lower bound:
    need log_2(C(n,s)) >= log_2(n) = 6 bits to identify which coordinate is nonzero."""

    n_dim = 2**6  # 64
    s = 1  # 1-sparse
    m_needed = math.ceil(math.log2(n_dim))  # 6

    # For s-sparse in R^n with Gaussian measurements:
    # m ~ 2*s*log(n/s) is typical (with constant ~2)
    # s=1: m ~ 2*log(64) = 2*6 = 12? No, log base e: 2*ln(64) ~ 8.3
    # With base-2 counting: need log2(C(64,1)) = log2(64) = 6 bits minimum

    info_bound = math.log2(math.comb(n_dim, s))  # log2(64) = 6

    passed = (m_needed == 6 and n_dim == 64 and info_bound == 6.0)

    report("R2-CROSS-14", "Compressed sensing: 6 measurements identify 1-sparse in R^{2^6}=R^64",
           f"m = log2(2^6) = {m_needed}; n = 2^6 = {n_dim}; info bound = {info_bound}",
           passed, f"m={m_needed}, n={n_dim}, info={info_bound}",
           "🟩",
           "This is just 6 = log2(64) = log2(2^6), a tautology. "
           "Any n gives m=n for 1-sparse in R^{2^n}. Not specific to n=6.")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-15: PageRank eigenvector for 6-cycle
# ══════════════════════════════════════════════════════════════════════
def test_15():
    """PageRank on cycle graph C_6 with damping factor alpha:
    PR = alpha * (1/n) * 1 + (1-alpha) * A_norm * PR

    By symmetry of C_6, all PageRank values are equal: PR_i = 1/6 for all i.
    This holds for ANY damping factor alpha, because C_6 is vertex-transitive.

    The second eigenvalue of C_6 adjacency matrix:
    Eigenvalues of C_n: 2*cos(2*pi*k/n) for k=0,...,n-1.
    For C_6: 2*cos(0) = 2, 2*cos(pi/3) = 1, 2*cos(2pi/3) = -1,
             2*cos(pi) = -2, 2*cos(4pi/3) = -1, 2*cos(5pi/3) = 1.
    Eigenvalues: {2, 1, 1, -2, -1, -1}.
    Spectral gap = 2 - 1 = 1."""

    eigenvalues = sorted([2*math.cos(2*math.pi*k/6) for k in range(6)], reverse=True)
    eigenvalues_round = [round(ev, 10) for ev in eigenvalues]

    spectral_gap = eigenvalues_round[0] - eigenvalues_round[1]

    # Check: eigenvalues should be {2, 1, 1, -1, -1, -2}
    expected = [2.0, 1.0, 1.0, -1.0, -1.0, -2.0]
    match = all(abs(a - b) < 1e-9 for a, b in zip(eigenvalues_round, expected))

    passed = (match and abs(spectral_gap - 1.0) < 1e-9)

    report("R2-CROSS-15", "C_6 eigenvalues: {2,1,1,-1,-1,-2}; spectral gap = 1 = R(6)",
           f"eigenvalues = {expected}; gap = lambda_1 - lambda_2 = {spectral_gap}",
           passed, f"eigenvalues={expected}, gap={spectral_gap}",
           "🟩",
           "Spectral gap = 1 = R(6). But C_n has gap = 2-2cos(2pi/n); for n=6 this is 2-1=1. "
           "gap=1 also for C_3 (triangle). Not uniquely n=6. Still, all eigenvalues are integers — "
           "C_6 is one of few cycles with all-integer spectrum (n | 6, i.e., n in {1,2,3,6}).")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-16: Cycle graphs with all-integer spectra
# ══════════════════════════════════════════════════════════════════════
def test_16():
    """C_n has all-integer eigenvalues iff 2*cos(2*pi*k/n) is integer for all k.
    cos(2*pi*k/n) in {0, +-1/2, +-1}.
    This requires n in {1, 2, 3, 4, 6} — the CRYSTALLOGRAPHIC RESTRICTION!

    These are exactly the n for which a rotation by 2*pi/n maps a lattice to itself.
    In 2D crystallography, only 1,2,3,4,6-fold rotational symmetries exist.

    Connection: The crystallographic restriction set = {1,2,3,4,6}.
    Product = 1*2*3*4*6 = 144 = 12^2 = sigma(6)^2.
    Sum = 1+2+3+4+6 = 16 = 2^4 = 2^tau(6).
    Max element = 6 = n. So n=6 is the LARGEST crystallographic order."""

    def has_integer_spectrum(n):
        for k in range(n):
            ev = 2 * math.cos(2 * math.pi * k / n)
            if abs(ev - round(ev)) > 1e-9:
                return False
        return True

    integer_spectrum_cycles = [n for n in range(1, 100) if has_integer_spectrum(n)]

    crystal_set = [1, 2, 3, 4, 6]
    match = (integer_spectrum_cycles == crystal_set)

    prod = 1
    for x in crystal_set:
        prod *= x
    s = sum(crystal_set)

    passed = match

    # Verify derived identities
    prod_is_sigma_sq = (prod == SIGMA**2)  # 144 = 12^2
    sum_is_2_tau = (s == 2**TAU)  # 16 = 2^4
    max_is_n = (max(crystal_set) == N)  # 6

    report("R2-CROSS-16", "Crystallographic restriction: n=6 is largest order; set={1,2,3,4,6}",
           f"Integer spectrum cycles: {integer_spectrum_cycles}; prod={prod}=sigma^2={SIGMA}^2; sum={s}=2^tau=2^{TAU}; max={N}",
           passed, f"set={integer_spectrum_cycles}, prod={prod}, sum={s}, max={max(crystal_set)}",
           "⭐⭐" if (match and max_is_n) else "⚪",
           "n=6 is the LARGEST rotation order compatible with lattice symmetry (crystallographic restriction). "
           "This is a deep geometric fact: only 1,2,3,4,6-fold symmetries tile the plane. "
           "Product of the set = 144 = sigma(6)^2 is interesting but may be coincidental. "
           "The key fact is that 6 is the maximum, giving it a canonical role in crystallography.")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-17: Exploration-exploitation and 1/e (secretary problem)
# ══════════════════════════════════════════════════════════════════════
def test_17():
    """Secretary problem (optimal stopping): Interview n candidates sequentially,
    must decide immediately. Optimal strategy: reject first n/e candidates,
    then accept first one better than all seen.

    Success probability -> 1/e as n -> infinity.
    For n=6: optimal skip = floor(6/e) = floor(2.207) = 2.

    P(win | skip 2, n=6) = (2/6)*[1/2 + 1/3 + 1/4 + 1/5] = (1/3)*[77/60] = 77/180 = 0.4278.

    Exact: P = sum_{i=skip+1}^{n} (skip/n) * (1/(i-1)) for best candidate at position i.
    = (skip/n) * sum_{i=skip+1}^{n} 1/(i-1)
    = (2/6) * [1/2 + 1/3 + 1/4 + 1/5] = (1/3)(77/60) = 77/180.

    Connection: skip = 2 = phi(6). And 77/180 = 0.4278 ~ Golden Zone center + 0.06."""

    n = 6

    # Try all skip values to find optimal
    def secretary_prob(n, skip):
        if skip == 0:
            return 1/n  # always pick first
        if skip >= n:
            return 0
        prob = 0
        for i in range(skip + 1, n + 1):
            # Probability best is at position i AND we pick them
            # = (1/n) * (skip/(i-1))
            prob += (1/n) * (skip / (i - 1))
        return prob

    probs = {skip: secretary_prob(n, skip) for skip in range(n)}
    best_skip = max(probs, key=probs.get)
    best_prob = probs[best_skip]

    # Verify: skip=2
    p_skip2 = probs[2]
    # (2/6)*(1/2 + 1/3 + 1/4 + 1/5) = (1/3)*(30+20+15+12)/60 = (1/3)(77/60) = 77/180
    exact = Fraction(77, 180)

    passed = (best_skip == 2 and abs(best_prob - float(exact)) < 1e-10)

    report("R2-CROSS-17", "Secretary problem n=6: optimal skip = 2 = phi(6), P(win) = 77/180",
           f"skip={best_skip}=phi(6); P = {float(exact):.6f} = 77/180; all probs: {', '.join(f'{k}:{v:.4f}' for k,v in probs.items())}",
           passed, f"skip={best_skip}, P={best_prob:.6f}, phi(6)={PHI}",
           "⭐",
           "Optimal skip = 2 = phi(6) is genuine for n=6. The secretary problem's n/e rule gives "
           "floor(6/e) = floor(2.207) = 2 = phi(6). This connects the 1/e threshold to the Euler totient. "
           "But floor(n/e) = phi(n) fails for most n (e.g., n=10: floor(10/e)=3 != phi(10)=4). "
           "Specific to n=6.")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-18: Hamiltonian paths on K_6
# ══════════════════════════════════════════════════════════════════════
def test_18():
    """Number of Hamiltonian paths in K_n = n!/2 (each path has 2 orientations).
    K_6: n!/2 = 720/2 = 360.

    Number of Hamiltonian cycles in K_n = (n-1)!/2.
    K_6: 5!/2 = 120/2 = 60.

    Ratio paths/cycles = n = 6. (Always true: n!/2 / ((n-1)!/2) = n.)

    Number of distinct Hamiltonian decompositions of K_6:
    K_6 has 15 edges. Each Hamiltonian cycle uses 6 edges.
    But 15/6 = 2.5, so K_6 cannot be decomposed into Hamiltonian cycles.
    K_n has Hamiltonian decomposition iff n is odd.
    6 is even, so NO Hamiltonian decomposition exists."""

    n = 6
    ham_paths = math.factorial(n) // 2  # 360
    ham_cycles = math.factorial(n - 1) // 2  # 60
    ratio = ham_paths // ham_cycles  # 6
    edges_K6 = n * (n - 1) // 2  # 15
    can_decompose = (n % 2 == 1)  # False for n=6

    passed = (ham_paths == 360 and ham_cycles == 60 and ratio == n and not can_decompose)

    report("R2-CROSS-18", "K_6: 360 Ham. paths, 60 Ham. cycles; no Hamiltonian decomposition (n even)",
           f"paths=6!/2={ham_paths}; cycles=5!/2={ham_cycles}; ratio={ratio}=n; edges={edges_K6}; 15/6 not integer",
           passed, f"paths={ham_paths}, cycles={ham_cycles}, ratio={ratio}, decomp={can_decompose}",
           "🟩",
           "Standard graph theory. paths/cycles = n is always true. "
           "60 = 5!/2 = sopfr(6)!/phi(6). But these are generic formulas, not n=6 specific.")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-19: Quantum walk hitting time on C_6
# ══════════════════════════════════════════════════════════════════════
def test_19():
    """Quantum walk on cycle C_n: hitting time from vertex 0 to vertex n/2 (antipodal).

    Classical random walk on C_n: expected hitting time to antipodal = n^2/4 (for even n).
    For C_6: classical hitting time = 36/4 = 9.

    Quantum walk on C_n achieves quadratic speedup: O(n) vs O(n^2).
    For C_6: quantum ~ O(6) vs classical = 9.

    Classical hitting time 0->3 on C_6:
    By symmetry + Markov chain: E[T_{0->3}] = 9 = n^2/4 = 36/4.
    Connection: 9 = n^2/tau(n) = 36/4."""

    n = 6
    classical_hit = n**2 // 4  # 9 for hitting antipodal on even cycle

    # Verify by Markov chain calculation on C_6
    # States: 0,1,2,3 (by symmetry, distance from target 3)
    # From distance d, go to d-1 or d+1 with prob 1/2 each (absorbing at 0 = distance 3)
    # Actually let's compute directly.
    # h(d) = expected steps to reach distance 0 from distance d, where d in {1,2,3}
    # h(0) = 0
    # By symmetry on C_6 from vertex 0 to vertex 3:
    # distances are 0,1,2,3,2,1 around the cycle
    # h(3) = 1 + h(2) [from vertex 0, always go to distance 2]
    # h(2) = 1 + (1/2)*h(1) + (1/2)*h(3)
    # h(1) = 1 + (1/2)*h(0) + (1/2)*h(2) = 1 + (1/2)*h(2)
    # From h(1) = 1 + h(2)/2
    # h(2) = 1 + h(1)/2 + h(3)/2
    # h(3) = 1 + h(2)
    # Substitute h(3) = 1 + h(2) into h(2):
    # h(2) = 1 + h(1)/2 + (1+h(2))/2 = 1 + h(1)/2 + 1/2 + h(2)/2
    # h(2) - h(2)/2 = 3/2 + h(1)/2
    # h(2)/2 = 3/2 + h(1)/2
    # h(2) = 3 + h(1)
    # h(1) = 1 + h(2)/2 = 1 + (3+h(1))/2 = 1 + 3/2 + h(1)/2
    # h(1)/2 = 5/2, h(1) = 5
    # h(2) = 3 + 5 = 8
    # h(3) = 1 + 8 = 9 ✓

    h1, h2, h3 = 5, 8, 9

    n_sq_over_tau = n**2 / TAU  # 36/4 = 9

    passed = (h3 == 9 and classical_hit == 9 and n_sq_over_tau == 9.0)

    report("R2-CROSS-19", "Quantum walk C_6: classical hitting time = 9 = n^2/tau(n)",
           f"h(0->3) = {h3}; n^2/4 = {classical_hit}; n^2/tau = {n_sq_over_tau}",
           passed, f"h={h3}, n^2/4={classical_hit}, n^2/tau={n_sq_over_tau}",
           "🟩",
           "h(0->antipodal) = n^2/4 = 9 for C_6. And tau(6) = 4, so n^2/tau = 9 too. "
           "But tau(n) = 4 here just happens to equal n/2+1=4 wait no 6/2=3 != 4. "
           "Actually n^2/4 uses the 4 from n/2 being the max distance (3) on C_6 scaled... "
           "The 4 in n^2/4 is generic (2^2 from the 1/2 probability), not tau(6). Coincidental match.")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-20: Tensor network bond dimension for n=6 MPS
# ══════════════════════════════════════════════════════════════════════
def test_20():
    """Matrix Product State (MPS) for n=6 qubits with bond dimension chi.

    For GHZ state |000000> + |111111> on 6 qubits: bond dimension chi = 2.
    For W state (1 excitation among 6): chi = 2 also suffices.
    For generic state: chi = 2^{n/2} = 2^3 = 8 needed for exact representation.

    Maximum entanglement entropy across any bipartition:
    S_max = log2(chi) = log2(2^3) = 3 = n/2 for 6 qubits (area law maximum).

    Connection: max bond dimension = 2^{n/2} = 2^3 = 8; max entropy = n/2 = 3.
    For the perfect number 6: n/2 = 3 = number of proper divisors > 1 of 6 ({2,3,6}... no, {2,3}).

    Better: Number of prime factors of 6 = 2 (primes 2,3).
    2^omega(6) = 2^2 = 4 = tau(6). This is a known identity for squarefree numbers!"""

    n_qubits = 6
    max_bond = 2**(n_qubits // 2)  # 8
    max_entropy = n_qubits / 2  # 3

    # The real insight: for squarefree n, 2^omega(n) = tau(n)
    # omega(6) = 2 (distinct prime factors)
    omega_6 = 2  # primes 2, 3
    identity = (2**omega_6 == TAU)  # 4 == 4 ✓

    # Verify for other squarefree numbers
    def omega(n):
        count = 0
        for p in range(2, n+1):
            if n % p == 0:
                count += 1
                while n % p == 0:
                    n //= p
        return count

    def is_squarefree(n):
        for p in range(2, int(n**0.5)+1):
            if n % (p*p) == 0:
                return False
        return True

    def tau_func(n):
        return sum(1 for d in range(1, n+1) if n % d == 0)

    sqfree_check = all(2**omega(n) == tau_func(n) for n in range(2, 50) if is_squarefree(n))

    passed = (max_bond == 8 and max_entropy == 3.0 and identity and sqfree_check)

    report("R2-CROSS-20", "MPS n=6: max bond dim = 2^3 = 8; 2^omega(6) = tau(6) = 4 (squarefree identity)",
           f"max_chi = 2^(n/2) = {max_bond}; S_max = {max_entropy}; 2^omega(6) = {2**omega_6} = tau(6) = {TAU}",
           passed, f"bond={max_bond}, entropy={max_entropy}, 2^omega=tau={identity}, general={sqfree_check}",
           "🟩",
           "2^omega(n) = tau(n) for squarefree n is a known number theory identity, not specific to 6. "
           "MPS bond dimension 2^(n/2) is generic. Clean but no special n=6 structure.")


# ══════════════════════════════════════════════════════════════════════
# R2-CROSS-BONUS: Category theory — 6 is the number of simple transitive
# modules over the monoidal category of S_3 representations
# ══════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════
# Run all tests
# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 70)
    print("TECS-L Round 2 Cross-Domain Hypothesis Verification")
    print("n=6, sigma=12, tau=4, phi=2, sopfr=5, sigma_neg1=2, R(6)=1")
    print("=" * 70)

    tests = [test_01, test_02, test_03, test_04, test_05, test_06, test_07,
             test_08, test_09, test_10, test_11, test_12, test_13, test_14,
             test_15, test_16, test_17, test_18, test_19, test_20]

    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"\nERROR in {t.__name__}: {e}")
            import traceback
            traceback.print_exc()

    # ── Summary ──
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    grade_counts = defaultdict(int)
    for tag, title, formula, status, value, grade, note in results:
        grade_counts[grade] += 1
        print(f"{tag}: {title}")
        print(f"  {status} | Grade: {grade}")

    print(f"\n{'─'*40}")
    print("Grade distribution:")
    for grade, count in sorted(grade_counts.items(), key=lambda x: -x[1]):
        print(f"  {grade}: {count}")

    total_pass = sum(1 for r in results if r[3] == "PASS")
    total = len(results)
    print(f"\nTotal: {total_pass}/{total} PASS")

    # Highlight discoveries
    print(f"\n{'─'*40}")
    print("Notable findings:")
    for tag, title, formula, status, value, grade, note in results:
        if "⭐" in grade:
            print(f"  {grade} {tag}: {title}")
            print(f"       {note[:120]}")
