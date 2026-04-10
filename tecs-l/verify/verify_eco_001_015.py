#!/usr/bin/env python3
"""
Verification of Ecology/Evolution Hypotheses H-ECO-001 through H-ECO-015.

Maps ecological constants to TECS-L framework:
  perfect number 6, sigma(6)=12, tau(6)=4, phi(6)=2,
  Golden Zone [0.212, 0.500], center 1/e ~ 0.3679

Runs Texas Sharpshooter test on each claimed match.
"""
import math
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

# ── TECS-L constants ────────────────────────────────────────────────────
N6         = 6
SIGMA6     = 12          # sigma(6) = 1+2+3+6
TAU6       = 4           # number of divisors of 6
PHI6       = 2           # Euler's totient of 6
GZ_LO      = 0.5 - math.log(4/3)   # 0.2123
GZ_HI      = 0.5
GZ_CENTER  = 1/math.e              # 0.3679
GZ_WIDTH   = math.log(4/3)         # 0.2877
ONE_SIXTH  = 1/6
ONE_THIRD  = 1/3
FIVE_SIXTH = 5/6
LN2        = math.log(2)
LN3        = math.log(3)

# ── Known ecological/evolutionary constants ─────────────────────────────
# All values sourced from standard textbooks and literature

# A. Population Dynamics
LOGISTIC_CHAOS_R   = 3.56995      # Feigenbaum onset of chaos
LOTKA_VOLTERRA_PERIOD_RATIO = None  # depends on params, no universal const
R_K_STRATEGIES     = 2            # r-selected vs K-selected
ALLEE_THRESHOLD_TYPICAL = 0.20    # ~20% of carrying capacity (Courchamp 1999)
CARRYING_CAP_LOGISTIC = None      # K is system-specific

# B. Food Web / Ecosystem
TROPHIC_LEVELS_TYPICAL = (4, 5)   # Pimm 1982: mean ~4-5
ENERGY_TRANSFER_RATE   = 0.10     # Lindeman 10% law
SHANNON_MAX_LN_S       = None     # depends on S (species count)
CONNECTANCE_TYPICAL    = (0.10, 0.30)  # Martinez 1992
KEYSTONE_FRACTION      = None     # qualitative concept

# C. Evolution
POINT_MUTATION_TYPES = 6          # 2 transitions + 4 transversions
MASS_EXTINCTIONS     = 5          # "Big Five" (Raup & Sepkoski 1982)
HW_TERMS             = 3          # p^2 + 2pq + q^2
NEUTRAL_MUTATION_RATE_PER_NT = 1e-8  # ~1e-8 per nt per generation (human)
CAMBRIAN_MYA         = 541.0      # millions of years ago


def texas_sharpshooter(measured, target, search_space, tolerance=0.05):
    """Simplified Texas Sharpshooter p-value."""
    distance = abs(measured - target)
    rel_error = distance / max(abs(target), 1e-15)
    hit = rel_error <= tolerance
    # probability of landing within tolerance of target by chance
    # in a uniform search space of given size
    p_single = 2 * tolerance * abs(target) / max(search_space, 1e-15)
    return {
        "measured": measured,
        "target": target,
        "distance": distance,
        "rel_error": rel_error,
        "hit": hit,
        "p_single": min(p_single, 1.0),
    }


def grade(p, is_exact=False, has_adhoc=False):
    """Grade per DFS rules."""
    if is_exact and p < 0.05 and not has_adhoc:
        return "green"   # exact proven
    if not is_exact and p < 0.01 and not has_adhoc:
        return "orange_star"
    if not is_exact and p < 0.05:
        return "orange"
    if p >= 0.05:
        return "white"   # coincidence
    return "black"


GRADE_EMOJI = {
    "green": "\U0001f7e9",
    "orange_star": "\U0001f7e7\u2605",
    "orange": "\U0001f7e7",
    "white": "\u26aa",
    "black": "\u2b1b",
}


def print_header(num, title):
    print(f"\n{'='*65}")
    print(f"  H-ECO-{num:03d}: {title}")
    print(f"{'='*65}")


def print_result(measured, target, label, p, g, note=""):
    emoji = GRADE_EMOJI[g]
    print(f"  Measured:  {measured}")
    print(f"  Target:    {target}  ({label})")
    print(f"  Rel error: {abs(measured - target)/max(abs(target),1e-15)*100:.2f}%")
    print(f"  p-value:   {p:.6f}")
    print(f"  Grade:     {emoji} {g}")
    if note:
        print(f"  Note:      {note}")


# ========================================================================
# A. POPULATION DYNAMICS (H-ECO-001 to H-ECO-005)
# ========================================================================

def eco_001_logistic_chaos():
    """Logistic map chaos onset r=3.5699 vs n=6 constants."""
    print_header(1, "Logistic Map Chaos Onset vs n=6 Constants")

    r_c = LOGISTIC_CHAOS_R  # 3.56995

    # Candidate mappings
    candidates = [
        ("sigma(6)/tau(6) = 12/4 = 3.0", SIGMA6/TAU6),
        ("6/phi(6) = 6/2 = 3.0", N6/PHI6),
        ("sigma(6)/pi = 12/pi = 3.8197", SIGMA6/math.pi),
        ("6*ln(2) - 6*1/6 = 3.159", 6*LN2 - 1),
        ("sigma(6)*ln(4/3) = 12*0.2877 = 3.452", SIGMA6*GZ_WIDTH),
        ("2+phi_gold = 3.618", 2 + (1+math.sqrt(5))/2),
        ("e + 5/6 = 3.568", math.e + FIVE_SIXTH),
    ]

    print(f"\n  Chaos onset: r_c = {r_c:.5f}")
    print(f"\n  {'Candidate':<45} {'Value':>8} {'Error%':>8}")
    print(f"  {'-'*45} {'-'*8} {'-'*8}")

    best_p = 1.0
    best_name = ""
    best_val = 0
    for name, val in candidates:
        err = abs(val - r_c)/r_c * 100
        print(f"  {name:<45} {val:8.5f} {err:7.3f}%")
        if err < abs(best_val - r_c)/max(r_c,1e-15)*100 or best_val == 0:
            best_val = val
            best_name = name

    # Best candidate: e + 5/6 = 3.568 vs 3.570 (0.05% error)
    best_measured = math.e + FIVE_SIXTH
    ts = texas_sharpshooter(best_measured, r_c, search_space=10.0, tolerance=0.01)
    # But this is cherry-picked from 7 candidates: Bonferroni
    p_corrected = min(ts["p_single"] * 7, 1.0)

    print(f"\n  Best match: e + 5/6 = {best_measured:.5f}")
    print(f"  Distance: {abs(best_measured - r_c):.5f}")
    print(f"  p (single): {ts['p_single']:.6f}")
    print(f"  p (Bonferroni x7): {p_corrected:.6f}")

    # Has ad-hoc: we tried 7 combinations
    g = grade(p_corrected, is_exact=False, has_adhoc=True)
    print_result(best_measured, r_c, "e + 5/6", p_corrected, g,
                 "Ad hoc: tried 7 candidate expressions. "
                 "e+5/6 close but likely coincidence from multiple trials.")
    return g


def eco_002_lotka_volterra():
    """Lotka-Volterra: period structure vs n=6."""
    print_header(2, "Lotka-Volterra Cycle Period Ratios")

    # LV equations: dx/dt = ax - bxy, dy/dt = -cy + dxy
    # Period T = 2*pi / sqrt(a*c) for linearized system
    # No universal constant here -- it depends on parameters a, c.
    # Claim: for typical ecosystems, predator/prey ratio at equilibrium = d/b
    # This is parameter-dependent, NOT a universal constant.

    print("\n  Lotka-Volterra has NO universal dimensionless constant.")
    print("  Period and equilibrium depend on system parameters (a, b, c, d).")
    print("  Any match to n=6 constants would be parameter-tuning.")
    print()
    print("  The conservation law H = d*x - c*ln(x) + b*y - a*ln(y) = const")
    print("  is structurally analogous to G*I = D*P (product conservation),")
    print("  but this is generic to all Hamiltonian systems.")
    print()

    g = "white"
    print(f"  Grade: {GRADE_EMOJI[g]} {g}")
    print(f"  Note: No testable numerical claim. Structural analogy only.")
    return g


def eco_003_r_k_strategy():
    """r vs K strategy: 2 types = phi(6)?"""
    print_header(3, "r/K Strategy Dichotomy = phi(6) = 2")

    # phi(6) = 2 (integers < 6 coprime to 6: {1, 5})
    # r vs K = 2 strategies

    print(f"\n  r/K strategies: 2 types")
    print(f"  phi(6) = {PHI6}")
    print(f"  Match: exact (2 = 2)")
    print()
    print(f"  However: '2' is the most common small integer.")
    print(f"  Binary dichotomies are ubiquitous in biology:")
    print(f"    male/female, prokaryote/eukaryote, DNA/RNA,")
    print(f"    predator/prey, autotroph/heterotroph, ...")
    print(f"  Also: modern ecology uses r-K-A continuum (3 types),")
    print(f"  or Grime's CSR triangle (3 strategies).")
    print()

    # Texas Sharpshooter: probability that a random small integer matches
    # Search space: integers 1-10, hitting 2 by chance = 1/10
    p = 0.10  # very generous
    g = grade(p, is_exact=True, has_adhoc=False)
    print_result(2, PHI6, "phi(6)", p, g,
                 "Trivial match: 2=2. Small integer coincidence. "
                 "Modern ecology has 3+ strategy types.")
    return g


def eco_004_allee_threshold():
    """Allee effect threshold ~20% of K vs GZ lower bound 0.2123."""
    print_header(4, "Allee Effect Threshold vs GZ Lower Bound")

    # Allee effect: below some threshold, per capita growth rate declines
    # Threshold varies enormously by species: 5%-50% of K
    # "~20%" is a rough central tendency (Courchamp et al. 1999)

    allee_est = 0.20  # fraction of K
    target = GZ_LO    # 0.2123

    print(f"\n  Allee threshold (typical): ~{allee_est:.0%} of K")
    print(f"  GZ lower bound: {target:.4f}")
    print(f"  Difference: {abs(allee_est - target):.4f}")
    print()
    print(f"  Problem: Allee threshold is NOT a universal constant.")
    print(f"  It ranges from 5% to 50% depending on species.")
    print(f"  Picking '20%' is already cherry-picking the estimate.")
    print()

    ts = texas_sharpshooter(allee_est, target, search_space=1.0, tolerance=0.05)
    p = ts["p_single"]
    g = grade(p, is_exact=False, has_adhoc=True)
    print_result(allee_est, target, "GZ lower", p, g,
                 "Allee threshold is species-specific (5-50%), not universal. "
                 "Picking 20% is ad hoc.")
    return g


def eco_005_carrying_capacity():
    """Carrying capacity K: structural analogy to GZ upper bound."""
    print_header(5, "Carrying Capacity Structural Analogy")

    print("\n  In logistic growth: dN/dt = rN(1 - N/K)")
    print(f"  K is the upper bound of population, analogous to")
    print(f"  GZ upper bound = 1/2 as maximum 'sustainable' inhibition.")
    print()
    print(f"  But K is system-specific, not a universal constant.")
    print(f"  The logistic form (1 - x/max) is generic saturation.")
    print(f"  No numerical test possible.")
    print()

    g = "white"
    print(f"  Grade: {GRADE_EMOJI[g]} {g}")
    print(f"  Note: Structural analogy only. No testable numerical claim.")
    return g


# ========================================================================
# B. FOOD WEB / ECOSYSTEM (H-ECO-006 to H-ECO-010)
# ========================================================================

def eco_006_trophic_levels():
    """Trophic levels typically 4-5 vs tau(6)=4."""
    print_header(6, "Trophic Levels vs tau(6) = 4")

    # Pimm (1982): terrestrial food chains avg ~4 trophic levels
    # Aquatic: 4-5. Some: up to 6.
    # Post & Pace (2004): mean 4.0 for lakes
    trophic_mean = 4.0

    print(f"\n  Mean trophic levels (terrestrial): ~{trophic_mean:.1f}")
    print(f"  tau(6) = {TAU6}")
    print(f"  Match: {trophic_mean} = {TAU6} (exact for mean)")
    print()
    print(f"  But trophic levels range from 2 to 6 across ecosystems.")
    print(f"  The mean ~ 4 is set by energetic constraints (10% rule),")
    print(f"  not by number theory.")
    print()
    print(f"  tau(6) = 4 is just 'number of divisors of 6'.")
    print(f"  Matching '4' -- a very common small integer -- is weak.")

    # p-value: hitting 4 out of range [2, 6], search space = 5
    p = 1.0 / 5.0  # 0.20
    g = grade(p, is_exact=True, has_adhoc=False)
    print_result(trophic_mean, TAU6, "tau(6)", p, g,
                 "Small integer match (4=4). Energetic, not number-theoretic origin.")
    return g


def eco_007_energy_transfer():
    """Lindeman 10% energy transfer vs 1/sigma(6) or 1/12."""
    print_header(7, "Energy Transfer Rate vs 1/sigma(6)")

    # Lindeman's 10% law: ~10% energy passes to next trophic level
    lindeman = 0.10
    target_12 = 1/SIGMA6       # 1/12 = 0.0833
    target_6  = 1/N6           # 1/6  = 0.1667
    target_e  = 1/math.e**2    # 1/e^2 = 0.1353

    print(f"\n  Lindeman efficiency: {lindeman:.2%}")
    print(f"  1/sigma(6) = 1/12 = {target_12:.4f} ({abs(lindeman-target_12)/lindeman*100:.1f}% off)")
    print(f"  1/6              = {target_6:.4f} ({abs(lindeman-target_6)/lindeman*100:.1f}% off)")
    print(f"  1/e^2            = {target_e:.4f} ({abs(lindeman-target_e)/lindeman*100:.1f}% off)")
    print()
    print(f"  10% is closer to 1/12 (8.3%) than to 1/6 (16.7%).")
    print(f"  But 10% is a rough average; actual range is 5-20%.")

    # Best match is 1/12 = 0.0833 vs 0.10 = 17% error
    ts = texas_sharpshooter(lindeman, target_12, search_space=1.0, tolerance=0.05)
    p = min(ts["p_single"] * 3, 1.0)  # Bonferroni for 3 candidates
    g = grade(p, is_exact=False, has_adhoc=True)
    print_result(lindeman, target_12, "1/sigma(6)=1/12", p, g,
                 "17% relative error. Lindeman 10% itself is approximate (5-20% range).")
    return g


def eco_008_shannon_biodiversity():
    """Shannon index H = -sum(p_i ln p_i). Max = ln(S)."""
    print_header(8, "Shannon Biodiversity Index Structure")

    # Shannon index: H = -sum(p_i * ln(p_i))
    # For S equally abundant species: H_max = ln(S)
    # For S=6: H_max = ln(6) = 1.7918
    # For S=12: H_max = ln(12) = 2.4849

    h_6 = math.log(N6)       # ln(6) = 1.7918
    h_12 = math.log(SIGMA6)  # ln(12) = 2.4849

    # Evenness J = H / H_max. For Golden Zone optimal diversity:
    # If J = 1/e, then H = ln(S)/e

    print(f"\n  Shannon index properties:")
    print(f"  H_max(S=6)  = ln(6)  = {h_6:.4f}")
    print(f"  H_max(S=12) = ln(12) = {h_12:.4f}")
    print(f"  ln(12) - ln(6) = ln(2) = {h_12-h_6:.4f} = {LN2:.4f}")
    print()
    print(f"  This is just ln(12/6) = ln(2). A tautology, not a discovery.")
    print(f"  Shannon index uses natural log by definition.")
    print(f"  Any relationship with e or ln is built-in, not emergent.")
    print()
    print(f"  Evenness J = 1/e is not a known ecological principle.")
    print(f"  Typical J values range 0.4-0.9 depending on community.")
    print()

    g = "white"
    print(f"  Grade: {GRADE_EMOJI[g]} {g}")
    print(f"  Note: Tautological (Shannon uses ln by definition). "
          f"No empirical constant to match.")
    return g


def eco_009_connectance():
    """Ecological network connectance C ~ 0.1-0.3 vs Golden Zone."""
    print_header(9, "Ecological Network Connectance vs Golden Zone")

    # Connectance C = L / S^2 where L = links, S = species
    # Martinez (1992): C ~ 0.1-0.3 for most food webs
    # Dunne et al (2002): mean C ~ 0.11 for 16 food webs
    # Montoya & Sole (2003): C ~ 0.05-0.32

    c_mean = 0.11   # Dunne 2002
    c_range = (0.05, 0.32)

    print(f"\n  Connectance (Dunne 2002 mean): C = {c_mean}")
    print(f"  Connectance range: {c_range}")
    print(f"  Golden Zone: [{GZ_LO:.4f}, {GZ_HI:.4f}]")
    print()
    print(f"  The range [0.05, 0.32] partially overlaps GZ [{GZ_LO:.3f}, {GZ_HI:.3f}].")
    print(f"  But the mean C = 0.11 is BELOW the GZ lower bound (0.212).")
    print()

    # Check if C_mean is in GZ
    in_gz = GZ_LO <= c_mean <= GZ_HI
    print(f"  C_mean in GZ? {in_gz}")
    print(f"  GZ overlap: connectance range [0.212, 0.32] is only part of range.")
    print()

    # Also: 1/sigma(6) = 1/12 = 0.0833, close to some connectance values
    print(f"  1/sigma(6) = {1/SIGMA6:.4f} -- close to C_mean but still 24% off")

    # Texas test: does C_mean match any TECS-L constant?
    candidates = [GZ_LO, GZ_CENTER, 1/SIGMA6, ONE_SIXTH]
    best_dist = min(abs(c_mean - c) for c in candidates)
    best_c = min(candidates, key=lambda c: abs(c_mean - c))
    err = abs(c_mean - best_c) / c_mean * 100

    p = 0.30  # connectance range is wide, overlap is partial
    g = grade(p, is_exact=False, has_adhoc=True)
    print_result(c_mean, best_c, "nearest TECS-L const", p, g,
                 f"C_mean=0.11 is below GZ. Best match 1/12=0.083 still {err:.0f}% off. "
                 f"Range overlap is partial and not specific.")
    return g


def eco_010_keystone_species():
    """Keystone species proportion in ecosystems."""
    print_header(10, "Keystone Species Proportion")

    # Keystone species: disproportionate effect relative to abundance
    # Paine (1969): concept from Pisaster in intertidal
    # No universal numeric constant for "fraction of keystone species"
    # Estimates: ~5-15% of species are keystone (Power et al 1996)
    # This is qualitative, not a precise constant

    print(f"\n  Keystone species fraction: roughly 5-15% (qualitative)")
    print(f"  No universal constant established in literature.")
    print(f"  Comparison to 1/6 = 16.7% or 1/12 = 8.3% is meaningless")
    print(f"  without a precise empirical value.")
    print()

    g = "white"
    print(f"  Grade: {GRADE_EMOJI[g]} {g}")
    print(f"  Note: No universal constant. Qualitative concept only.")
    return g


# ========================================================================
# C. EVOLUTION (H-ECO-011 to H-ECO-015)
# ========================================================================

def eco_011_point_mutations():
    """6 types of point mutations = n=6."""
    print_header(11, "Point Mutation Types = 6 = n")

    # DNA: 4 bases (A, T, G, C)
    # Transitions: purine<->purine (A<->G), pyrimidine<->pyrimidine (C<->T) = 2
    # Transversions: purine<->pyrimidine = 4 types per base x 2 / 2 = 8, wait...
    # Actually: each base can mutate to 3 others = 12 total mutations
    # But grouped: 2 transitions + 4 transversions = 6 categories? No.
    # Correct: transitions = 4 (A->G, G->A, C->T, T->C)
    #          transversions = 8 (A->C, A->T, G->C, G->T, and reverses)
    #          total = 12 directed mutations
    # If undirected: transitions = 2 pairs, transversions = 4 pairs = 6 total pairs

    print(f"\n  DNA substitution types (undirected pairs):")
    print(f"    Transitions:   A<->G, C<->T          = 2 pairs")
    print(f"    Transversions: A<->C, A<->T, G<->C, G<->T = 4 pairs")
    print(f"    Total undirected pairs: 2 + 4 = 6")
    print()
    print(f"  n = {N6}")
    print(f"  Match: 6 = 6 (exact)")
    print()
    print(f"  BUT: This is combinatorics of 4 bases, not number theory.")
    print(f"  C(4,2) = 6 undirected pairs from 4 objects.")
    print(f"  If DNA had 5 bases, we'd get C(5,2) = 10 pairs.")
    print(f"  The '6' comes from C(4,2), not from perfect number 6.")
    print()
    print(f"  Also: directed mutations = 4*3 = 12 = sigma(6).")
    print(f"  C(4,2) = 6, 4*3 = 12: these are just binomial coefficients.")
    print()
    print(f"  Transition/Transversion ratio: 2/4 = 1/2")
    print(f"  This equals GZ upper = 1/2. But 2/4 = 1/2 is trivial.")

    # C(4,2) = 6 is a combinatorial identity, not related to perfect numbers
    # 12 directed = 4*3 = P(4,2), also combinatorial
    p = 0.10  # common small integer
    g = grade(p, is_exact=True, has_adhoc=False)
    print_result(6, 6, "n=6 (perfect number)", p, g,
                 "6 = C(4,2) from 4 DNA bases. Combinatorial origin, "
                 "not number-theoretic. Coincidence.")
    return g


def eco_012_mass_extinctions():
    """Mass extinctions: Big Five (or Six?) vs n=6 or tau(6)+1."""
    print_header(12, "Mass Extinctions: Big Five vs n=6")

    # Raup & Sepkoski (1982): Big Five mass extinctions
    # 1. End-Ordovician (445 Ma)
    # 2. Late Devonian (375 Ma)
    # 3. End-Permian (252 Ma) -- the Great Dying
    # 4. End-Triassic (201 Ma)
    # 5. End-Cretaceous (66 Ma)
    # Some argue Holocene/Anthropocene = 6th, but that's ongoing/contested

    n_extinctions = 5  # established scientific consensus

    print(f"\n  Established mass extinctions: {n_extinctions} (Big Five)")
    print(f"  n = {N6}, tau(6) = {TAU6}, tau(6)+1 = {TAU6+1}")
    print()
    print(f"  5 != 6.  To make it 6, one must include the ongoing")
    print(f"  Holocene extinction, which is scientifically contested")
    print(f"  as a 'mass extinction' (Barnosky et al 2011: 'potential').")
    print()
    print(f"  5 = tau(6) + 1 requires ad-hoc +1 correction.")
    print(f"  5 = 6 - 1 also requires ad-hoc -1.")
    print()

    # Even if we accepted 6, matching n=6 is trivial
    p = 0.15
    g = "white"
    print(f"  Grade: {GRADE_EMOJI[g]} {g}")
    print(f"  Note: Big Five = 5, not 6. Ad-hoc to force match. "
          f"Holocene 6th is contested.")
    return g


def eco_013_hardy_weinberg():
    """Hardy-Weinberg: 3 terms = tau(6)-1 or 3 divisors of 6 minus 6."""
    print_header(13, "Hardy-Weinberg Equilibrium Structure")

    # HW: p^2 + 2pq + q^2 = 1 for 2 alleles
    # 3 genotype terms (AA, Aa, aa)
    # For n alleles: n(n+1)/2 genotypes
    # For 2 alleles: 2*3/2 = 3

    hw_terms = 3
    tau6 = TAU6  # 4
    proper_divisors_6 = [1, 2, 3]  # 3 proper divisors

    print(f"\n  HW genotype terms (2 alleles): {hw_terms}")
    print(f"  Proper divisors of 6: {proper_divisors_6} (count: {len(proper_divisors_6)})")
    print(f"  tau(6) - 1 = {tau6} - 1 = {tau6 - 1}")
    print()
    print(f"  Match: 3 = 3 (proper divisor count)")
    print(f"  But 3 terms come from 2 alleles: n(n+1)/2 = 3.")
    print(f"  For 3 alleles: 6 genotypes. For 4 alleles: 10 genotypes.")
    print(f"  The '3' is from C(2+1,2), not from perfect number 6.")
    print()
    print(f"  Also: HW has 2 allele frequencies (p, q) summing to 1.")
    print(f"  2 = phi(6). But again, 2 alleles is the simplest case.")
    print()
    print(f"  Deeper: the '= 1' in p^2+2pq+q^2 = (p+q)^2 = 1")
    print(f"  is algebraic identity, not a conservation law.")

    p_val = 0.15
    g = "white"
    print(f"  Grade: {GRADE_EMOJI[g]} {g}")
    print(f"  Note: Small integer match (3=3). "
          f"Combinatorial origin from 2 alleles, not n=6.")
    return g


def eco_014_neutral_mutation():
    """Neutral theory: mutation rate ~1e-8/nt/gen vs TECS-L constants."""
    print_header(14, "Neutral Theory Mutation Rate")

    # Kimura's neutral theory: most mutations are selectively neutral
    # Human mutation rate: ~1.2e-8 per nucleotide per generation
    # Drosophila: ~3.5e-9 per nt per gen
    # E. coli: ~2.2e-10 per nt per gen

    mu_human = 1.2e-8
    mu_drosophila = 3.5e-9

    print(f"\n  Human mutation rate: {mu_human:.1e} per nt per generation")
    print(f"  Drosophila: {mu_drosophila:.1e}")
    print()
    print(f"  These are empirical rates varying 100-fold across species.")
    print(f"  No universal dimensionless constant here.")
    print(f"  Cannot meaningfully compare to [0, 1] range constants.")
    print()
    print(f"  One could take -log10(mu_human) = {-math.log10(mu_human):.2f}")
    print(f"  and note {-math.log10(mu_human):.2f} is close to 8,")
    print(f"  but 8 is not a TECS-L constant. This is numerology.")

    g = "white"
    print(f"  Grade: {GRADE_EMOJI[g]} {g}")
    print(f"  Note: Mutation rate is species-specific, dimensional, "
          f"and varies 100-fold. No meaningful comparison.")
    return g


def eco_015_cambrian_explosion():
    """Cambrian explosion ~541 Ma: any connection to n=6?"""
    print_header(15, "Cambrian Explosion Timing")

    cambrian = CAMBRIAN_MYA  # 541

    # Wild attempts:
    # 541 / 6 = 90.17
    # 541 / 12 = 45.08
    # 541 / 360 = 1.503 (360 = degrees in circle)
    # ln(541) = 6.293 -- close to 6? within 5%?

    ln_541 = math.log(cambrian)
    err_6 = abs(ln_541 - 6) / 6 * 100

    print(f"\n  Cambrian explosion: {cambrian} Ma")
    print(f"  ln({cambrian}) = {ln_541:.4f}")
    print(f"  n = {N6}")
    print(f"  |ln(541) - 6| / 6 = {err_6:.2f}%")
    print()
    print(f"  ln(541) = 6.29, so 541 ~ e^6 = {math.exp(6):.1f}")
    print(f"  e^6 = {math.exp(6):.1f} vs 541: {abs(math.exp(6)-541)/541*100:.1f}% error")
    print()
    print(f"  But: Cambrian date has uncertainty +/- ~1 Ma.")
    print(f"  And e^6 = 403, not 541. That's 25% off.")
    print(f"  541 is closer to e^(6.29). The '6' is not exact.")
    print()
    print(f"  More importantly: 541 Ma is in Earth-specific geology,")
    print(f"  not a universal constant. Other planets would have")
    print(f"  different evolutionary timelines.")

    # e^6 = 403.4 vs 541: 25% error
    ts = texas_sharpshooter(math.exp(6), cambrian, search_space=4000, tolerance=0.05)
    p = ts["p_single"]
    g = grade(p, is_exact=False, has_adhoc=True)
    print_result(math.exp(6), cambrian, "e^6 vs 541 Ma", p, g,
                 "25% error. Earth-specific date, not universal. "
                 "Forced comparison.")
    return g


# ========================================================================
# SUMMARY
# ========================================================================

def main():
    print("=" * 65)
    print("  TECS-L Ecology/Evolution Hypothesis Verification")
    print("  H-ECO-001 through H-ECO-015")
    print("  Framework: n=6, sigma(6)=12, tau(6)=4, phi(6)=2, GZ, 1/e")
    print("=" * 65)

    results = {}
    tests = [
        (1,  "Logistic chaos r_c vs n=6 constants", eco_001_logistic_chaos),
        (2,  "Lotka-Volterra cycle structure",       eco_002_lotka_volterra),
        (3,  "r/K strategy = phi(6) = 2",            eco_003_r_k_strategy),
        (4,  "Allee threshold vs GZ lower",          eco_004_allee_threshold),
        (5,  "Carrying capacity analogy",            eco_005_carrying_capacity),
        (6,  "Trophic levels = tau(6) = 4",          eco_006_trophic_levels),
        (7,  "Energy transfer 10% vs 1/12",          eco_007_energy_transfer),
        (8,  "Shannon index structure",              eco_008_shannon_biodiversity),
        (9,  "Network connectance vs GZ",            eco_009_connectance),
        (10, "Keystone species proportion",          eco_010_keystone_species),
        (11, "Point mutation types = 6",             eco_011_point_mutations),
        (12, "Mass extinctions Big Five vs 6",       eco_012_mass_extinctions),
        (13, "Hardy-Weinberg 3 terms",               eco_013_hardy_weinberg),
        (14, "Neutral mutation rate",                eco_014_neutral_mutation),
        (15, "Cambrian explosion timing",            eco_015_cambrian_explosion),
    ]

    for num, title, func in tests:
        g = func()
        results[num] = (title, g)

    # ── Summary Table ──────────────────────────────────────────────────
    print("\n\n" + "=" * 65)
    print("  SUMMARY TABLE")
    print("=" * 65)
    print(f"\n  {'#':<6} {'Hypothesis':<42} {'Grade':<8}")
    print(f"  {'-'*6} {'-'*42} {'-'*8}")

    grade_counts = {"green": 0, "orange_star": 0, "orange": 0, "white": 0, "black": 0}
    for num in sorted(results):
        title, g = results[num]
        emoji = GRADE_EMOJI[g]
        grade_counts[g] += 1
        print(f"  {num:<6} {title:<42} {emoji}")

    print(f"\n  ── Grade Distribution ──")
    print(f"  {GRADE_EMOJI['green']}  Proven (exact):        {grade_counts['green']}")
    print(f"  {GRADE_EMOJI['orange_star']}  Structural (p<0.01):  {grade_counts['orange_star']}")
    print(f"  {GRADE_EMOJI['orange']}  Weak evidence (p<0.05):{grade_counts['orange']}")
    print(f"  {GRADE_EMOJI['white']}  Coincidence / no test:  {grade_counts['white']}")
    print(f"  {GRADE_EMOJI['black']}  Refuted:               {grade_counts['black']}")

    total = sum(grade_counts.values())
    white_plus = grade_counts["white"] + grade_counts["black"]
    print(f"\n  Honest assessment: {white_plus}/{total} hypotheses are white circles")
    print(f"  (coincidence, no testable claim, or ad-hoc matching).")
    print(f"  Ecology/evolution has few universal dimensionless constants,")
    print(f"  making meaningful numerical matches to n=6 framework unlikely.")

    # ── ASCII grade histogram ──────────────────────────────────────────
    print(f"\n  ── Grade Histogram ──")
    max_count = max(grade_counts.values())
    for g_name in ["green", "orange_star", "orange", "white", "black"]:
        bar = "#" * (grade_counts[g_name] * 3)
        print(f"  {GRADE_EMOJI[g_name]} |{bar} {grade_counts[g_name]}")

    print(f"\n{'='*65}")
    print(f"  Verification complete. All grades honest.")
    print(f"{'='*65}")


if __name__ == "__main__":
    main()
