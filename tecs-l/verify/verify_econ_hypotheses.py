#!/usr/bin/env python3
"""
Economics & Game Theory Hypotheses Verification (H-ECON-001 to H-ECON-015)

Tests each hypothesis connecting economic/game-theoretic constants to n=6 framework.
Perfect number 6: sigma(6)=12, tau(6)=4, phi(6)=2, sigma_{-1}(6)=2
Golden Zone: [0.2123, 0.5], center=1/e=0.3679, width=ln(4/3)=0.2877

Grades:
  GREEN  = Exact equation, mathematically proven
  ORANGE_STAR = Numerically close, Texas p < 0.01 (structural)
  ORANGE = Numerically close, Texas p < 0.05 (weak evidence)
  WHITE  = Arithmetically correct but coincidental (p > 0.05)
  BLACK  = Arithmetically wrong or factually incorrect

Run: PYTHONPATH=. python3 verify/verify_econ_hypotheses.py
"""

import math
import numpy as np
from collections import OrderedDict

# ── Constants from the TECS-L system ──
SIGMA_6 = 12           # sigma(6) = 1+2+3+6
SIGMA_INV_6 = 2.0      # sigma_{-1}(6) = 1 + 1/2 + 1/3 + 1/6
TAU_6 = 4              # number of divisors of 6
PHI_6 = 2              # Euler totient phi(6)
GZ_UPPER = 0.5
GZ_LOWER = 0.5 - math.log(4/3)   # 0.21230...
GZ_CENTER = 1/math.e              # 0.36788...
GZ_WIDTH = math.log(4/3)          # 0.28768...
LN2 = math.log(2)
LN3 = math.log(3)

# Search space for Texas Sharpshooter: number of well-known mathematical constants
# we could possibly compare against (conservative estimate)
N_CONSTANTS = 50   # e, pi, ln2, ln3, phi, 1/2, 1/3, 1/6, etc.
N_HYPOTHESES = 15  # Bonferroni correction

results = OrderedDict()
detail_lines = []  # Collect output for summary


def grade(name, g, reason, p_value=None):
    """Record a grade with optional p-value."""
    results[name] = (g, reason, p_value)


def texas_p(measured, target, tolerance=0.05, search_space=N_CONSTANTS):
    """Simple Texas Sharpshooter p-value.
    Probability of a random draw from [0,1] landing within tolerance of target."""
    distance = abs(measured - target)
    if distance > tolerance:
        return 1.0
    # P(|X - target| < tolerance) for uniform on [0,1]
    p_single = 2 * tolerance
    # Correct for multiple comparisons: n_constants we could match
    p_bonf = min(p_single * search_space, 1.0)
    return p_bonf


def pct_error(measured, target):
    if target == 0:
        return float('inf')
    return abs(measured - target) / abs(target) * 100


def report(tag, lines):
    """Print and store report lines."""
    for line in lines:
        print(f"  [{tag}] {line}")
        detail_lines.append(f"  [{tag}] {line}")


# ═══════════════════════════════════════════════════════════════
# A. MARKET / FINANCE (H-ECON-001 to H-ECON-005)
# ═══════════════════════════════════════════════════════════════

def verify_econ001():
    """H-ECON-001: Benford's Law P(d=1) = log10(2) lands in Golden Zone.

    Benford's law: P(d) = log10(1 + 1/d).
    P(d=1) = log10(2) = 0.30103...
    Golden Zone = [0.2123, 0.5].
    Claim: log10(2) is inside the Golden Zone.
    """
    p1 = math.log10(2)  # 0.30103
    in_gz = GZ_LOWER <= p1 <= GZ_UPPER
    dist_to_center = abs(p1 - GZ_CENTER)
    pct = pct_error(p1, GZ_CENTER)

    report("ECON-001", [
        f"Benford P(d=1) = log10(2) = {p1:.6f}",
        f"Golden Zone = [{GZ_LOWER:.4f}, {GZ_UPPER:.4f}]",
        f"In GZ? {in_gz}",
        f"Distance to GZ center (1/e={GZ_CENTER:.4f}): {dist_to_center:.4f} ({pct:.1f}%)",
        f"GZ width = {GZ_WIDTH:.4f}, relative position = {(p1 - GZ_LOWER)/GZ_WIDTH:.3f}",
    ])

    # Texas test: is landing in GZ meaningful?
    # GZ covers 0.2877 of [0,1] -- about 28.8% of the unit interval
    gz_coverage = GZ_WIDTH  # 0.2877
    # Any random value in [0,1] has 28.8% chance of landing in GZ
    # But Benford P(1) is not random -- it IS log10(2), a specific constant
    # The question: is log10(2) being in GZ structurally meaningful?
    # p-value: coverage of GZ as fraction of [0,1]
    p_val = gz_coverage  # ~0.29 (not significant -- GZ is wide!)

    report("ECON-001", [
        f"Texas p-value (GZ covers {gz_coverage:.1%} of [0,1]): p={p_val:.3f}",
        f"GZ is wide enough that ~29% of any constant in [0,1] would land inside.",
        f"log10(2) is NOT close to 1/e: error = {pct:.1f}%",
    ])

    # Additional: does log10(2) match ANY n=6 constant?
    candidates = {
        "1/e": 1/math.e,
        "GZ_LOWER": GZ_LOWER,
        "ln(4/3)": math.log(4/3),
        "1/3": 1/3,
        "1/2-1/6": 1/2-1/6,
    }
    for name, val in candidates.items():
        report("ECON-001", [f"  vs {name}={val:.5f}: err={pct_error(p1, val):.1f}%"])

    # Closest is 1/3 = 0.3333, error 9.7%. Not impressive.
    grade("H-ECON-001", "WHITE",
          f"log10(2)={p1:.5f} IS in GZ but GZ covers 28.8% of [0,1]. "
          f"Not close to 1/e (err={pct:.1f}%). No structural connection. "
          f"Coincidental membership.", p_val)


def verify_econ002():
    """H-ECON-002: Pareto 80/20 Rule -- 20% threshold vs GZ lower bound.

    Pareto principle: 20% of inputs cause 80% of outputs.
    The 20% threshold = 0.20.
    GZ lower = 1/2 - ln(4/3) = 0.2123.
    Claim: Pareto's 20% approximates the GZ lower boundary.
    """
    pareto_threshold = 0.20
    dist = abs(pareto_threshold - GZ_LOWER)
    pct = pct_error(pareto_threshold, GZ_LOWER)

    report("ECON-002", [
        f"Pareto threshold = {pareto_threshold}",
        f"GZ lower = {GZ_LOWER:.6f}",
        f"Distance = {dist:.5f}, error = {pct:.1f}%",
    ])

    # The "80/20 rule" is a rough heuristic, not exact
    # Actual Pareto distributions have parameter alpha
    # For Pareto(alpha), the fraction x contributing fraction y:
    # y = 1 - (1-x)^(1-1/alpha) ... for alpha = ln(5)/ln(4) ~ 1.161
    alpha_pareto = math.log(5) / math.log(4)  # Classic 80/20
    report("ECON-002", [
        f"Pareto alpha for 80/20: ln5/ln4 = {alpha_pareto:.4f}",
        f"This is a specific alpha, not a universal law",
        f"20% is a round-number approximation, real threshold varies",
    ])

    # Texas: 0.20 vs 0.2123, difference = 0.012 = 6.1%
    p_val = texas_p(pareto_threshold, GZ_LOWER, tolerance=0.015)
    report("ECON-002", [
        f"Texas p-value (tol=0.015): p={p_val:.3f}",
        f"Error 6.1% -- not a close match",
    ])

    grade("H-ECON-002", "WHITE",
          f"Pareto 0.20 vs GZ lower 0.2123: error {pct:.1f}%. "
          f"80/20 is a rough heuristic (varies by domain). "
          f"6% gap with no mechanism. Coincidental.", p_val)


def verify_econ003():
    """H-ECON-003: Kelly Criterion optimal fraction in Golden Zone.

    Kelly criterion: f* = (bp - q) / b where b=odds, p=win prob, q=1-p.
    For fair odds (b=1): f* = 2p - 1.
    For p in [0.6, 0.75], f* in [0.2, 0.5] -- overlaps GZ.
    Claim: Kelly optimal betting fraction naturally lives in the Golden Zone
    for realistic edge scenarios.
    """
    report("ECON-003", [
        "Kelly criterion: f* = (bp - q) / b",
        "For even odds (b=1): f* = 2p - 1",
    ])

    # Scan: for what p values does f* land in GZ?
    p_range = np.linspace(0.5, 1.0, 100)
    f_stars = 2 * p_range - 1  # for b=1
    in_gz = (f_stars >= GZ_LOWER) & (f_stars <= GZ_UPPER)
    p_in_gz = p_range[in_gz]

    report("ECON-003", [
        f"For b=1: f* in GZ when p in [{p_in_gz[0]:.3f}, {p_in_gz[-1]:.3f}]",
        f"That's p in [{p_in_gz[0]:.3f}, {p_in_gz[-1]:.3f}], width={p_in_gz[-1]-p_in_gz[0]:.3f}",
        f"GZ width={GZ_WIDTH:.4f} maps to p-range width={GZ_WIDTH/2:.4f}",
    ])

    # For general b, f* = (bp-q)/b = p - q/b = p - (1-p)/b
    # The key question: does 1/e appear as optimal Kelly fraction?
    # f* = 1/e when (bp - q)/b = 1/e
    # For b=1: 2p-1 = 1/e => p = (1+1/e)/2 = 0.684
    p_for_1e = (1 + 1/math.e) / 2
    report("ECON-003", [
        f"f* = 1/e when p = {p_for_1e:.4f} (for even odds)",
        f"Is p=0.684 a special value? Not particularly.",
    ])

    # The issue: GZ covers [0.21, 0.50] which is 28.8% of [0,1]
    # Kelly f* for any p in [0.606, 0.750] lands in GZ -- that's a 14.4% range
    # No structural reason; just width overlap
    p_val = GZ_WIDTH  # ~0.29 -- same as ECON-001

    report("ECON-003", [
        f"GZ is 28.8% of [0,1], so ~28.8% of possible f* values land there.",
        f"No special connection between Kelly formula and n=6.",
        f"Texas p={p_val:.3f} (not significant)",
    ])

    grade("H-ECON-003", "WHITE",
          f"Kelly f* overlaps GZ for p in [0.606, 0.750] -- "
          f"just because GZ covers 28.8% of [0,1]. "
          f"No structural link to n=6.", p_val)


def verify_econ004():
    """H-ECON-004: Black-Scholes d1/d2 and sigma*sqrt(T) ~ GZ width.

    Black-Scholes: d1 = [ln(S/K) + (r + sigma^2/2)T] / (sigma*sqrt(T))
    At-the-money (S=K), r=0: d1 = sigma*sqrt(T)/2, d2 = -sigma*sqrt(T)/2.
    Typical sigma ~ 20-30%, T=1yr.
    Claim: sigma*sqrt(T) for typical equities ~ ln(4/3) = GZ width.
    """
    gz_w = GZ_WIDTH  # 0.2877
    # Typical equity volatility
    sigmas = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
    Ts = [0.25, 0.5, 1.0, 2.0]

    report("ECON-004", [
        f"GZ width = ln(4/3) = {gz_w:.4f}",
        "sigma*sqrt(T) for various (sigma, T):",
    ])

    matches = []
    for s in sigmas:
        for T in Ts:
            val = s * math.sqrt(T)
            err = pct_error(val, gz_w)
            if err < 10:
                matches.append((s, T, val, err))
                report("ECON-004", [f"  sigma={s:.0%}, T={T}yr: sigma*sqrt(T)={val:.4f}, err={err:.1f}%"])

    report("ECON-004", [
        f"Found {len(matches)} combinations within 10% of GZ width.",
        f"But sigma*sqrt(T) takes ANY value depending on params.",
        f"We can always find sigma,T to match any target -- not structural.",
    ])

    # Texas: how many (sigma,T) combos are there in realistic range?
    # sigma in [0.1, 0.5], T in [0.1, 5], continuous -- infinite choices
    # This is classic cherry-picking
    p_val = 1.0  # Not meaningful

    grade("H-ECON-004", "WHITE",
          f"sigma*sqrt(T) is a free parameter product. "
          f"Any target can be matched by choosing sigma and T. "
          f"No predictive content. Cherry-picking.", p_val)


def verify_econ005():
    """H-ECON-005: Optimal portfolio diversification and sigma(6)=12.

    Empirical finance: diversification benefit plateaus around 12-30 stocks.
    sigma(6) = 12.
    Claim: sigma(6) predicts optimal minimum portfolio size.
    """
    # Literature values for diversification plateau
    # Evans & Archer (1968): ~10-15 stocks for most diversification benefit
    # Statman (1987): 30-40 stocks for full benefit
    # Modern view: 20-30 stocks capture >90% of diversification
    lit_values = {
        "Evans & Archer (1968)": (10, 15),
        "Elton & Gruber (1977)": (15, 20),
        "Statman (1987)": (30, 40),
        "Campbell et al (2001)": (40, 50),
        "Modern consensus": (20, 30),
    }

    report("ECON-005", [
        f"sigma(6) = {SIGMA_6}",
        "Literature on optimal portfolio size:",
    ])

    for study, (lo, hi) in lit_values.items():
        contains_12 = lo <= 12 <= hi
        report("ECON-005", [f"  {study}: {lo}-{hi} stocks, contains 12? {contains_12}"])

    # Only Evans & Archer's range contains 12
    # Most studies suggest 15-40 -- 12 is on the low end
    report("ECON-005", [
        f"12 is at the LOW end of the range. Most studies suggest 20-30.",
        f"The 'minimum' for significant benefit ~ 10-15 (close to 12)",
        f"But the claim conflates minimum vs optimal.",
    ])

    # Also: sigma(6)=12 is just the number 12. Many things equal 12.
    # Months in a year, hours on a clock, eggs in a dozen...
    p_val = 0.5  # Very generous; really should be ~1.0

    grade("H-ECON-005", "WHITE",
          f"12 stocks is at the low end of diversification ranges (15-40 typical). "
          f"12 is a common number (months, dozens). "
          f"No mechanism linking sigma(6) to portfolio theory.", p_val)


# ═══════════════════════════════════════════════════════════════
# B. GAME THEORY (H-ECON-006 to H-ECON-010)
# ═══════════════════════════════════════════════════════════════

def verify_econ006():
    """H-ECON-006: Nash equilibrium mixed strategy in 2x2 symmetric games.

    In a 2x2 symmetric game, the mixed strategy Nash equilibrium
    has probability p* = (d-c)/(a-b-c+d) for payoff matrix [[a,b],[c,d]].
    Claim: For structurally natural games, p* ~ 1/e or 1/3.
    """
    # Prisoner's Dilemma canonical: a=3, b=0, c=5, d=1 (T>R>P>S)
    # p* = (d-c)/(a-b-c+d) = (1-5)/(3-0-5+1) = -4/-1 = 4
    # p* > 1 means pure strategy (always defect). No mixed equilibrium!
    a, b, c, d = 3, 0, 5, 1
    denom = a - b - c + d
    if denom != 0:
        p_star_pd = (d - c) / denom
    else:
        p_star_pd = float('inf')

    report("ECON-006", [
        f"Prisoner's Dilemma [[3,0],[5,1]]: p* = (1-5)/(3-0-5+1) = {p_star_pd:.3f}",
        f"p* > 1 => pure strategy Nash (always defect). No mixed eq.",
    ])

    # Hawk-Dove game: a=0, b=3, c=1, d=2 (or V=4, C=6 variant)
    # Standard: V/C is the mixed strategy probability
    V, C_hd = 4, 6
    p_hawk = V / C_hd
    report("ECON-006", [
        f"Hawk-Dove (V={V}, C={C_hd}): p(Hawk) = V/C = {p_hawk:.4f}",
        f"V/C = 2/3 = {2/3:.4f}. Complement 1/3 = {1/3:.4f} (n=6 constant!)",
    ])

    # But V and C are free parameters -- p* = V/C can be anything
    # For V/C = 1/e: V=1, C=e -- contrived
    report("ECON-006", [
        f"p* = V/C is a ratio of free parameters.",
        f"Can get 1/3 or 1/e by choosing V,C appropriately.",
        f"No constraint forces p* to a specific value.",
    ])

    # Battle of the Sexes: p* depends on payoff values
    # Matching pennies: p* = 1/2 always (by symmetry)
    report("ECON-006", [
        f"Matching Pennies: p* = 1/2 always (symmetry) -- matches GZ upper.",
        f"But 1/2 appears everywhere in symmetric games by definition.",
    ])

    p_val = 1.0
    grade("H-ECON-006", "WHITE",
          f"Mixed strategy p* depends on arbitrary payoff values. "
          f"1/2 appears in symmetric games trivially. "
          f"V/C in Hawk-Dove is free. No structural link to n=6.", p_val)


def verify_econ007():
    """H-ECON-007: Prisoner's Dilemma payoff structure and divisors of 6.

    Standard PD: T > R > P > S, with 2R > T + S.
    Canonical: T=5, R=3, P=1, S=0. Sum = 9.
    Or: T=6, R=4, P=2, S=1. Sum = 13.
    Claim: Natural PD payoffs relate to divisors of 6 {1, 2, 3, 6}.
    """
    divisors_6 = [1, 2, 3, 6]
    # Test: can divisors of 6 form a valid PD?
    # Need T > R > P > S and 2R > T + S
    from itertools import permutations
    valid_pd = []
    for perm in permutations(divisors_6):
        T, R, P, S = perm
        if T > R > P > S and 2*R > T + S:
            valid_pd.append(perm)

    report("ECON-007", [
        f"Divisors of 6: {divisors_6}",
        f"Valid PD orderings from divisors of 6:",
    ])

    for pd in valid_pd:
        T, R, P, S = pd
        report("ECON-007", [f"  T={T}, R={R}, P={P}, S={S} | 2R={2*R} > T+S={T+S}? {2*R > T+S}"])

    if not valid_pd:
        report("ECON-007", ["  No valid PD from divisors of 6!"])

    # Check canonical PD payoffs
    report("ECON-007", [
        f"Canonical PD (T=5,R=3,P=1,S=0): not all are divisors of 6",
        f"5 is not a divisor of 6. 0 is not a divisor of 6.",
    ])

    # The divisors {1,2,3,6} have gaps (no 4,5) that limit payoff structures
    # 24 permutations, testing how many form valid PD
    n_valid = len(valid_pd)
    n_total = math.factorial(4)
    report("ECON-007", [
        f"Of {n_total} permutations of {{1,2,3,6}}, {n_valid} form valid PD.",
    ])

    p_val = 1.0
    grade("H-ECON-007", "WHITE",
          f"{n_valid} valid PDs from divisors of 6. "
          f"Canonical PD uses {5,3,1,0} which aren't divisors. "
          f"No structural connection.", p_val)


def verify_econ008():
    """H-ECON-008: Vickrey auction revenue and 1/e.

    Second-price auction (Vickrey): revenue = E[2nd highest bid].
    For n bidders uniform on [0,1]: E[2nd highest] = (n-1)/(n+1).
    For n=6: E[2nd] = 5/7 = 0.7143.
    For n=4 (=tau(6)): E[2nd] = 3/5 = 0.6.
    Claim: Connection to n=6 constants.
    """
    for n in [2, 3, 4, 5, 6, 12]:
        e_2nd = (n - 1) / (n + 1)
        report("ECON-008", [f"  n={n:2d} bidders: E[2nd highest] = {n-1}/{n+1} = {e_2nd:.4f}"])

    # For n=6: 5/7 = 0.7143
    val_6 = 5/7
    # Check against n=6 constants
    candidates = {"5/6": 5/6, "1-1/e": 1-1/math.e, "1-1/6": 5/6, "sigma_inv/e": SIGMA_INV_6/math.e}
    report("ECON-008", [f"  n=6 result: 5/7 = {val_6:.5f}"])
    for name, val in candidates.items():
        report("ECON-008", [f"    vs {name} = {val:.5f}: err = {pct_error(val_6, val):.1f}%"])

    # 5/7 doesn't match any n=6 constant well
    # What about the seller's revenue ratio? E[revenue]/E[max]
    # E[max|n] = n/(n+1), E[2nd|n] = (n-1)/(n+1)
    # Ratio = (n-1)/n = 1 - 1/n
    # For n=6: ratio = 5/6 = 0.8333 -- THIS IS a key n=6 constant!
    ratio_6 = 5/6
    report("ECON-008", [
        f"Revenue efficiency: E[2nd]/E[max] = (n-1)/n = 1 - 1/n",
        f"For n=6: 1 - 1/6 = 5/6 = {ratio_6:.4f} -- matches Compass upper!",
        f"But this is trivially (n-1)/n evaluated at n=6.",
        f"Any formula involving n yields n=6 constants when you plug in 6.",
    ])

    p_val = 1.0  # Tautological
    grade("H-ECON-008", "WHITE",
          f"(n-1)/n at n=6 = 5/6 is tautological (plugging 6 into formula). "
          f"5/7 doesn't match any system constant. "
          f"No structural insight.", p_val)


def verify_econ009():
    """H-ECON-009: Evolutionary Stable Strategy (ESS) and 1/e threshold.

    In Hawk-Dove, ESS frequency of Hawks = V/C.
    In replicator dynamics, the basin of attraction boundary
    for a 2-strategy game at p* can relate to fitness landscape.
    Claim: The ESS invasion barrier relates to 1/e.
    """
    # Replicator dynamics: dx/dt = x(1-x)(f1(x) - f2(x))
    # The fixed points are x=0, x=1, and x=p* where f1=f2
    # Basin of attraction: depends on payoff matrix
    # No universal constant appears

    # Axelrod's tournament: tit-for-tat won.
    # In iterated PD with discount factor w (prob of next round):
    # TFT is Nash iff w >= (T-R)/(T-P) = (5-3)/(5-1) = 1/2 for canonical PD
    w_threshold = (5-3)/(5-1)
    report("ECON-009", [
        f"Axelrod TFT cooperation threshold: w >= (T-R)/(T-P)",
        f"Canonical PD: w >= {w_threshold} = 1/2",
        f"1/2 = GZ upper bound",
        f"But 1/2 here comes from specific payoff values (5,3,1,0)",
    ])

    # For general payoffs, threshold varies
    # T=4, R=3, P=1, S=0: w >= 1/3
    w2 = (4-3)/(4-1)
    report("ECON-009", [
        f"Alternative PD (T=4,R=3,P=1,S=0): w >= {w2:.4f} = 1/3",
        f"1/3 is also an n=6 constant!",
        f"But the threshold depends entirely on payoff choice.",
    ])

    # ESS invasion barrier: in finite populations, probability of fixation
    # of a mutant with fitness advantage s in population N:
    # P_fix = (1 - 1/r) / (1 - 1/r^N) where r = 1+s
    # For neutral (s=0): P_fix = 1/N
    # Does 1/6 appear? Only if N=6 -- tautological
    report("ECON-009", [
        f"Fixation probability in population N: 1/N for neutral",
        f"For N=6: P_fix = 1/6 -- tautological",
        f"No universal 1/e threshold in ESS theory",
    ])

    p_val = 1.0
    grade("H-ECON-009", "WHITE",
          f"TFT threshold = (T-R)/(T-P) depends on payoffs. "
          f"Gets 1/2 or 1/3 for specific PD variants but by payoff choice. "
          f"Fixation P=1/N at N=6 is tautological. No structural link.", p_val)


def verify_econ010():
    """H-ECON-010: Mechanism Design -- VCG payment and 6 as smallest structure.

    VCG mechanism: payment = externality imposed on others.
    With n agents, each excluded agent's welfare changes.
    Claim: 6 agents is the minimal "complete" mechanism design setting
    because sigma(6)/6 = 2 (harmonic completeness).
    """
    # VCG mechanism works for any n >= 2
    # The payment structure doesn't depend on n being perfect
    report("ECON-010", [
        f"VCG works for any n >= 2. No special role for n=6.",
        f"sigma(n)/n for small n:",
    ])

    for n in range(1, 13):
        sigma_n = sum(d for d in range(1, n+1) if n % d == 0)
        report("ECON-010", [f"  n={n:2d}: sigma={sigma_n:3d}, sigma/n={sigma_n/n:.3f}"])

    # sigma(n)/n = 2 only for perfect numbers (6, 28, 496, ...)
    # But this is the definition of perfect number -- not mechanism design
    report("ECON-010", [
        f"sigma(6)/6 = 2 is the DEFINITION of perfect number.",
        f"No connection to mechanism design properties.",
        f"6 agents is not special in VCG -- any n works.",
    ])

    p_val = 1.0
    grade("H-ECON-010", "WHITE",
          f"VCG works for any n >= 2. sigma(6)/6=2 is the definition of "
          f"perfect numbers, not a mechanism design property. "
          f"No structural connection.", p_val)


# ═══════════════════════════════════════════════════════════════
# C. ECONOMIC CONSTANTS (H-ECON-011 to H-ECON-015)
# ═══════════════════════════════════════════════════════════════

def verify_econ011():
    """H-ECON-011: Okun's Law coefficient ~ sigma_{-1}(6) = 2.

    Okun's Law: 1% rise in unemployment => ~2% drop in GDP.
    Coefficient ranges 2-3 in literature.
    sigma_{-1}(6) = 1 + 1/2 + 1/3 + 1/6 = 2.
    Claim: Okun coefficient = sigma_{-1}(6).
    """
    okun_empirical = {
        "Okun (1962)": 3.0,
        "Ball et al (2013)": 2.0,
        "US 1950-2010": 2.0,
        "US 2000-2019": 1.8,
        "OECD average": 2.5,
        "Japan": 3.0,
        "Germany": 1.5,
    }

    report("ECON-011", [
        f"sigma_{{-1}}(6) = 1 + 1/2 + 1/3 + 1/6 = {SIGMA_INV_6}",
        "Okun's law coefficient estimates:",
    ])

    for study, val in okun_empirical.items():
        err = pct_error(val, SIGMA_INV_6)
        report("ECON-011", [f"  {study}: {val:.1f} (err vs 2.0: {err:.1f}%)"])

    # Average
    avg = np.mean(list(okun_empirical.values()))
    report("ECON-011", [
        f"Average Okun coefficient: {avg:.2f}",
        f"Error vs sigma_inv(6)=2: {pct_error(avg, SIGMA_INV_6):.1f}%",
        f"Range: 1.5 to 3.0 -- varies by country and period",
        f"2.0 is within the range but so are 1.5, 2.5, 3.0",
    ])

    # The coefficient is not a universal constant -- it's empirical and varies
    p_val = 0.5  # Not testable as a point prediction
    grade("H-ECON-011", "WHITE",
          f"Okun coefficient ranges 1.5-3.0, varies by country/period. "
          f"US estimate ~2.0 matches sigma_inv(6)=2 but this is a rough "
          f"empirical ratio, not a precise constant. "
          f"No mechanism linking GDP/unemployment to divisor sums.", p_val)


def verify_econ012():
    """H-ECON-012: Fiscal multiplier ~ 1.5 and 3/2.

    Government spending multiplier ~ 1.0-2.5, central estimate ~1.5.
    3/2 = 1.5 (ratio of consecutive divisors of 6: 3/2).
    Also: sigma(6)/tau(6)^2 = 12/16 = 0.75 = 3/4. Not matching.
    Claim: Fiscal multiplier = 3/2, a ratio from divisors of 6.
    """
    multiplier_estimates = {
        "Blanchard & Leigh (2013)": 1.5,
        "Ramey (2019)": 0.8,
        "Auerbach & Gorodnichenko (recession)": 2.5,
        "Auerbach & Gorodnichenko (expansion)": 0.5,
        "IMF consensus": 1.5,
        "CBO estimate": 1.4,
    }

    report("ECON-012", [
        f"Target: 3/2 = 1.5 (divisor ratio: 3 and 2 are divisors of 6)",
        "Fiscal multiplier estimates:",
    ])

    for study, val in multiplier_estimates.items():
        err = pct_error(val, 1.5)
        report("ECON-012", [f"  {study}: {val:.1f} (err vs 1.5: {err:.1f}%)"])

    report("ECON-012", [
        f"Multiplier varies from 0.5 to 2.5 depending on conditions!",
        f"3/2 is a ratio that appears in many contexts (not unique to n=6).",
        f"3/2 comes from any pair of consecutive integers, not special to 6.",
        f"Also: 3/2 = 6/4 = sigma(6)/tau(6)^2... but that's post-hoc algebra.",
    ])

    p_val = 1.0
    grade("H-ECON-012", "WHITE",
          f"Fiscal multiplier ranges 0.5-2.5, highly context-dependent. "
          f"3/2 is not unique to divisors of 6 -- it's just consecutive integers. "
          f"No mechanism or predictive power.", p_val)


def verify_econ013():
    """H-ECON-013: Golden Rule savings rate s* = 1/3 (Solow model).

    Solow model: golden rule savings rate s* = alpha (capital share).
    Empirically alpha ~ 0.3-0.4, often quoted as ~1/3.
    1/3 is the Meta Fixed Point in our system.
    Claim: Golden rule savings rate = 1/3 connects to TECS meta fixed point.
    """
    alpha_empirical = {
        "US (Gollin 2002)": 0.33,
        "OECD average": 0.35,
        "Developing countries": 0.40,
        "Piketty (2014)": 0.30,
        "Standard textbook": 0.33,
    }

    report("ECON-013", [
        f"TECS meta fixed point = 1/3 = {1/3:.6f}",
        f"Solow golden rule: s* = alpha (capital share of income)",
        "Capital share estimates:",
    ])

    for study, val in alpha_empirical.items():
        err = pct_error(val, 1/3)
        report("ECON-013", [f"  {study}: {val:.3f} (err vs 1/3: {err:.1f}%)"])

    avg_alpha = np.mean(list(alpha_empirical.values()))
    err_avg = pct_error(avg_alpha, 1/3)
    report("ECON-013", [
        f"Average alpha: {avg_alpha:.3f}, error vs 1/3: {err_avg:.1f}%",
        f"1/3 is a GOOD match for capital share (error ~4.8%)",
    ])

    # But is this meaningful?
    # 1/3 appears as a natural fraction in many contexts
    # Capital-labor split being ~1/3 vs ~2/3 is well-established
    # Is there a mechanism linking it to the fixed point of f(I)=0.7I+0.1?
    report("ECON-013", [
        f"The connection is INTERESTING but likely coincidental:",
        f"  - 1/3 is a ubiquitous simple fraction",
        f"  - Capital share ~1/3 reflects technology/institutions, not n=6",
        f"  - The TECS fixed point 1/3 comes from f(I)=0.7I+0.1",
        f"  - Different origins, same number = common fraction coincidence",
    ])

    # Texas test: 0.342 vs 1/3 = 0.333
    p_val = texas_p(avg_alpha, 1/3, tolerance=0.01)
    report("ECON-013", [f"Texas p-value: {p_val:.3f}"])

    grade("H-ECON-013", "WHITE",
          f"alpha~0.34 close to 1/3 (err 4.8%) but 1/3 is ubiquitous. "
          f"Capital share is empirical and varies. "
          f"Different origin from TECS fixed point. "
          f"Interesting numerological match but no mechanism.", p_val)


def verify_econ014():
    """H-ECON-014: Zipf's Law exponent = 1 and sigma_{-1}(6)/2 = 1.

    Zipf's law: rank r, size ~ 1/r^alpha, with alpha ~ 1.
    sigma_{-1}(6)/2 = 2/2 = 1.
    Also: sigma_{-1}(6) = 2, which is the harmonic series partial sum.
    Claim: Zipf exponent = sigma_{-1}(6)/2.
    """
    zipf_alpha = 1.0  # theoretical
    sigma_inv_half = SIGMA_INV_6 / 2  # 1.0

    report("ECON-014", [
        f"Zipf exponent (theoretical): {zipf_alpha}",
        f"sigma_{{-1}}(6)/2 = {sigma_inv_half}",
        f"Match: exact!",
    ])

    # But wait -- this is cherry-picked algebra
    # sigma_{-1}(6) = 2, and 2/2 = 1. That's trivially 1.
    # We could also write: tau(6)/4 = 1, phi(6)/2 = 1, 6/6 = 1, etc.
    # The number 1 can be produced from ANY integer by dividing by itself!

    ways_to_get_1 = [
        "sigma_{-1}(6)/2 = 2/2 = 1",
        "tau(6)/tau(6) = 4/4 = 1",
        "phi(6)/phi(6) = 2/2 = 1",
        "6/6 = 1",
        "sigma(6)/sigma(6) = 12/12 = 1",
        "ANY_CONSTANT / SAME_CONSTANT = 1",
    ]

    report("ECON-014", [
        f"Ways to produce 1 from n=6 system:",
    ])
    for w in ways_to_get_1:
        report("ECON-014", [f"  {w}"])

    report("ECON-014", [
        f"The number 1 is trivially derivable from anything.",
        f"Also: Zipf's alpha is NOT exactly 1 in real data.",
        f"City sizes: alpha ~ 0.8-1.1 depending on country/cutoff.",
        f"Word frequencies: alpha ~ 1.0-1.1.",
        f"Income: alpha ~ 1.5-2.5 (Pareto tail, different from Zipf body).",
    ])

    p_val = 1.0  # Trivial identity
    grade("H-ECON-014", "WHITE",
          f"sigma_inv(6)/2 = 1 is a trivial identity (anything/itself = 1). "
          f"Zipf alpha=1 is only approximate in real data. "
          f"No structural content.", p_val)


def verify_econ015():
    """H-ECON-015: Benford P(d=1) = log10(2) as optimal information threshold.

    DEEPER ANALYSIS of log10(2) = 0.30103:
    - Lies in Golden Zone [0.2123, 0.5]
    - Close to 1/3 = 0.3333 (error 9.7%)
    - Close to 1/e = 0.3679 (error 18.1%)
    - Is it close to ln(4/3) = 0.2877? Error 4.7%!

    Actually: log10(2) vs ln(4/3):
    log10(2) = 0.30103, ln(4/3) = 0.28768
    Distance = 0.01335, error = 4.4% from GZ width!

    Claim: Benford's leading digit law encodes the same information-theoretic
    transition that defines GZ width.
    """
    log10_2 = math.log10(2)  # 0.30103
    ln_4_3 = math.log(4/3)   # 0.28768

    dist = abs(log10_2 - ln_4_3)
    err = pct_error(log10_2, ln_4_3)

    report("ECON-015", [
        f"log10(2) = {log10_2:.6f}",
        f"ln(4/3)  = {ln_4_3:.6f}",
        f"Distance = {dist:.6f}",
        f"Error    = {err:.2f}%",
    ])

    # Are these related? Let's check analytically
    # log10(2) = ln(2)/ln(10)
    # ln(4/3) = ln(4) - ln(3) = 2*ln(2) - ln(3)
    # Ratio: log10(2) / ln(4/3) = [ln2/ln10] / [2*ln2 - ln3]
    ratio = log10_2 / ln_4_3
    report("ECON-015", [
        f"Ratio log10(2)/ln(4/3) = {ratio:.6f}",
        f"Not a simple fraction.",
    ])

    # What is the analytical relationship?
    # log10(2) = ln(2)/ln(10) = 0.30103
    # ln(4/3) = 2*ln(2) - ln(3) = 0.28768
    # These share ln(2) but the connection is thin
    # The 4.4% match is decent but:
    # In a search of ~50 constants, how many pairs have <5% error?

    # Monte Carlo: draw 50 random values in [0,1], count pairs within 5%
    rng = np.random.default_rng(42)
    n_trials = 10000
    n_consts = 50
    close_pair_counts = []
    for _ in range(n_trials):
        vals = rng.uniform(0, 1, n_consts)
        n_close = 0
        for i in range(n_consts):
            for j in range(i+1, n_consts):
                if abs(vals[i] - vals[j]) / max(abs(vals[j]), 1e-10) < 0.05:
                    n_close += 1
        close_pair_counts.append(n_close)

    avg_close = np.mean(close_pair_counts)
    report("ECON-015", [
        f"Monte Carlo: 50 random constants, avg pairs within 5%: {avg_close:.1f}",
        f"Out of C(50,2) = {50*49//2} possible pairs",
        f"Expected by chance: ~{avg_close:.0f} pairs within 5%",
        f"So finding ONE pair at 4.4% is not unusual.",
    ])

    # Texas p-value
    p_val = texas_p(log10_2, ln_4_3, tolerance=abs(dist))
    report("ECON-015", [f"Texas p-value: {p_val:.3f}"])

    report("ECON-015", [
        f"log10(2) and ln(4/3) share ln(2) in their definitions.",
        f"But the match is within random expectation for 50 constants.",
        f"No deep information-theoretic mechanism established.",
    ])

    grade("H-ECON-015", "WHITE",
          f"log10(2) vs ln(4/3): {err:.1f}% error. "
          f"Shares ln(2) analytically but match is within random expectation. "
          f"No established mechanism. Interesting proximity, not structural.", p_val)


# ═══════════════════════════════════════════════════════════════
# MAIN: Run all verifications and print summary
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 72)
    print("  ECONOMICS & GAME THEORY HYPOTHESES VERIFICATION")
    print("  H-ECON-001 through H-ECON-015")
    print("=" * 72)
    print()

    verifiers = [
        verify_econ001, verify_econ002, verify_econ003, verify_econ004,
        verify_econ005, verify_econ006, verify_econ007, verify_econ008,
        verify_econ009, verify_econ010, verify_econ011, verify_econ012,
        verify_econ013, verify_econ014, verify_econ015,
    ]

    for v in verifiers:
        name = v.__name__.replace("verify_", "").upper()
        print(f"\n{'─' * 60}")
        print(f"  {name}: {v.__doc__.strip().split(chr(10))[0]}")
        print(f"{'─' * 60}")
        v()

    # ── Summary ──
    print("\n" + "=" * 72)
    print("  SUMMARY")
    print("=" * 72)

    grade_counts = {"GREEN": 0, "ORANGE_STAR": 0, "ORANGE": 0, "WHITE": 0, "BLACK": 0}
    print(f"\n  {'Hypothesis':<15} {'Grade':<14} {'Reason'}")
    print(f"  {'─'*15} {'─'*14} {'─'*45}")

    for name, (g, reason, p) in results.items():
        grade_counts[g] = grade_counts.get(g, 0) + 1
        emoji = {"GREEN": "G", "ORANGE_STAR": "O*", "ORANGE": "O",
                 "WHITE": "W", "BLACK": "B"}.get(g, "?")
        p_str = f"p={p:.3f}" if p is not None else ""
        short_reason = reason[:55] + "..." if len(reason) > 55 else reason
        print(f"  {name:<15} [{emoji:>2}] {p_str:>8}  {short_reason}")

    print(f"\n  Grade Distribution:")
    for g, cnt in grade_counts.items():
        bar = "#" * (cnt * 4)
        print(f"    {g:<14}: {cnt:2d} {bar}")

    total = sum(grade_counts.values())
    print(f"\n  Total: {total} hypotheses")
    print(f"  Honest result: ALL WHITE (no structural connections found)")
    print(f"\n  Key insight: The Golden Zone covers ~29% of [0,1],")
    print(f"  so any constant has a ~29% chance of landing inside it.")
    print(f"  Economic constants are empirical (vary by country/period)")
    print(f"  and cannot serve as precise targets for matching.")
    print()

    return grade_counts


if __name__ == "__main__":
    counts = main()
