#!/usr/bin/env python3
"""Texas Sharpshooter test for 12 GREEN chemistry hypotheses.

Tests: How many chemistry facts would match random "special number" arithmetic
by chance? Monte Carlo with 10,000 trials.

Usage:
    PYTHONPATH=. python3 verify/verify_chem_texas.py
    PYTHONPATH=. python3 verify/verify_chem_texas.py --trials 50000
"""

import math
import random
import argparse
from collections import Counter

# ── n=6 arithmetic functions ──────────────────────────────────────

def divisors(n):
    return [d for d in range(1, n+1) if n % d == 0]

def sigma(n):
    """Sum of divisors."""
    return sum(divisors(n))

def sigma_neg1(n):
    """Sum of reciprocals of divisors."""
    return sum(1/d for d in divisors(n))

def tau(n):
    """Number of divisors."""
    return len(divisors(n))

def phi(n):
    """Euler totient."""
    return sum(1 for k in range(1, n+1) if math.gcd(k, n) == 1)

def is_perfect(n):
    return sigma(n) == 2 * n

# ── The 12 GREEN chemistry claims ────────────────────────────────
# Each claim is a chemistry fact that matches some n=6 arithmetic output.
# We encode: the chemistry value (fixed), and what n=6 function produced the match.

GREEN_CLAIMS = [
    {
        'id': 'H-CHEM-001',
        'desc': 'Carbon Z=6 is a perfect number',
        'chem_value': 6,
        'n6_function': 'n itself',
        'n6_value': 6,
        'match': 'exact',
        'independence_group': 'Z=6',
    },
    {
        'id': 'H-CHEM-002',
        'desc': 'sp3 cos(109.47) = -1/3 = -1/tau(6)',
        'chem_value': -1/3,
        'n6_function': '-1/tau(n)',
        'n6_value': -1/4,  # For n=6: -1/tau(6) = -1/4. Wait -- tau(6)=4, so -1/4 != -1/3
        'match': 'exact',  # Actually maps to meta fixed point 1/3, not tau
        'independence_group': 'tetrahedral_angle',
    },
    {
        'id': 'H-CHEM-010',
        'desc': 'Carbon at half-shell position (4/8 = 1/2)',
        'chem_value': 0.5,
        'n6_function': '1/2 (GZ upper)',
        'n6_value': 0.5,
        'match': 'exact',
        'independence_group': 'position_fraction',
    },
    {
        'id': 'H-CHEM-011',
        'desc': 'Benzene D6h order = 24 = sigma(6)*sigma_{-1}(6)',
        'chem_value': 24,
        'n6_function': 'sigma(n)*sigma_{-1}(n)',
        'n6_value': 24,  # 12 * 2 = 24
        'match': 'exact',
        'independence_group': 'symmetry_24',
    },
    {
        'id': 'H-CHEM-012',
        'desc': 'Octahedron 12 edges = sigma(6)',
        'chem_value': 12,
        'n6_function': 'sigma(n)',
        'n6_value': 12,
        'match': 'exact',
        'independence_group': 'twelve',
    },
    {
        'id': 'H-CHEM-014',
        'desc': 'Methane Td order=24, bonds=tau(6)=4',
        'chem_value': 24,
        'n6_function': 'sigma(n)*sigma_{-1}(n)',
        'n6_value': 24,
        'match': 'exact',
        'independence_group': 'symmetry_24',  # Same as H-CHEM-011
    },
    {
        'id': 'H-CHEM-015',
        'desc': 'Cyclohexane 12H = sigma(6)',
        'chem_value': 12,
        'n6_function': 'sigma(n)',
        'n6_value': 12,
        'match': 'exact',
        'independence_group': 'twelve',  # Same as H-CHEM-012
    },
    {
        'id': 'H-CHEM-016',
        'desc': 'Arrhenius 1/e fraction at T*=Ea/R',
        'chem_value': 1/math.e,
        'n6_function': '1/e (GZ center)',
        'n6_value': 1/math.e,
        'match': 'tautology',
        'independence_group': 'exponential_1e',
    },
    {
        'id': 'H-CHEM-017',
        'desc': 'Equilibrium forward fraction = 1/2 at K=1',
        'chem_value': 0.5,
        'n6_function': '1/2 (GZ upper)',
        'n6_value': 0.5,
        'match': 'tautology',
        'independence_group': 'half',
    },
    {
        'id': 'H-CHEM-026',
        'desc': 'Graphene unit cell = phi(6) = 2',
        'chem_value': 2,
        'n6_function': 'phi(n)',
        'n6_value': 2,
        'match': 'exact',
        'independence_group': 'two',
    },
    {
        'id': 'H-CHEM-027',
        'desc': 'Diamond 2nd neighbors = sigma(6) = 12',
        'chem_value': 12,
        'n6_function': 'sigma(n)',
        'n6_value': 12,
        'match': 'exact',
        'independence_group': 'twelve',  # Same as H-CHEM-012, 015
    },
    {
        'id': 'H-CHEM-029',
        'desc': 'C60 pentagons=12=sigma(6), Euler char=2=sigma_{-1}(6)',
        'chem_value': 12,
        'n6_function': 'sigma(n)',
        'n6_value': 12,
        'match': 'exact',
        'independence_group': 'twelve',  # 12 part same; Euler=2 is universal
    },
]

# ── Chemistry fact pool for Monte Carlo ──────────────────────────
# We need a realistic pool of "chemistry numbers" that could be matched.
# These are actual numbers that appear frequently in chemistry.

CHEMISTRY_NUMBERS = [
    # Coordination numbers
    2, 3, 4, 5, 6, 7, 8, 9, 12,
    # Common symmetry group orders
    1, 2, 3, 4, 6, 8, 12, 16, 24, 48, 120,
    # Polyhedron properties (vertices, edges, faces for common shapes)
    4, 6, 8, 12, 20,  # vertices of platonic solids
    6, 12, 12, 30, 30,  # edges
    4, 8, 6, 20, 12,  # faces
    # Common electron counts, bond counts
    1, 2, 3, 4, 5, 6, 7, 8,
    # Atomic numbers of important elements
    1, 6, 7, 8, 15, 16, 26, 29,
    # Unit cell atom counts
    1, 2, 4, 8,
    # Neighbor counts in crystals
    4, 6, 8, 12,
    # C60 specific
    12, 20, 60, 90, 32,
    # Common fractions in chemistry
    0.5, 1/3, 2/3, 1/4, 3/4, 1/math.e,
    # Euler characteristic (always 2 for convex polyhedra)
    2,
]

# Deduplicate
CHEMISTRY_NUMBERS_UNIQUE = sorted(set(CHEMISTRY_NUMBERS))


def n_arithmetic_outputs(n):
    """Generate the set of 'interesting' arithmetic outputs from number n."""
    d = divisors(n)
    s = sigma(n)
    s_neg1 = sum(1/dd for dd in d)
    t = tau(n)
    p = phi(n)

    outputs = set()
    # Direct values
    outputs.add(n)
    outputs.add(s)         # sigma
    outputs.add(t)         # tau
    outputs.add(p)         # phi
    outputs.add(s * s_neg1 if s_neg1 == int(s_neg1) else round(s * s_neg1, 6))

    # Reciprocals and simple fractions
    for dd in d:
        outputs.add(dd)
        outputs.add(1/dd)

    # sigma_{-1}
    outputs.add(round(s_neg1, 6))

    # Products of pairs
    funcs = [n, s, t, p, round(s_neg1, 6)]
    for i, a in enumerate(funcs):
        for b in funcs[i:]:
            outputs.add(round(a * b, 6))

    # Common TECS constants
    outputs.add(0.5)            # GZ upper
    outputs.add(1/math.e)       # GZ center
    outputs.add(math.log(4/3))  # GZ width
    outputs.add(1/3)            # meta fixed point

    return outputs


def count_matches(n, chem_numbers):
    """Count how many chemistry numbers match n's arithmetic outputs."""
    outputs = n_arithmetic_outputs(n)
    matches = 0
    matched_items = []
    for c in chem_numbers:
        # Exact match (for integers) or within 1% (for fractions)
        for o in outputs:
            if isinstance(c, int) or (isinstance(c, float) and c == int(c)):
                if c == o or (abs(c) > 0 and abs(c - o) / abs(c) < 0.01):
                    matches += 1
                    matched_items.append((c, o))
                    break
            else:
                if abs(c - o) < 0.001 or (abs(c) > 0.001 and abs(c - o) / abs(c) < 0.01):
                    matches += 1
                    matched_items.append((c, o))
                    break
    return matches, matched_items


def independence_analysis():
    """Analyze which of the 12 GREEN claims are truly independent."""
    print("\n" + "=" * 70)
    print("  INDEPENDENCE ANALYSIS: 12 GREEN Chemistry Hypotheses")
    print("=" * 70)

    groups = {}
    for c in GREEN_CLAIMS:
        g = c['independence_group']
        if g not in groups:
            groups[g] = []
        groups[g].append(c['id'])

    print(f"\n  12 claims collapse into {len(groups)} independence groups:\n")
    for g, members in sorted(groups.items()):
        print(f"    {g:25s} : {', '.join(members)}")

    print(f"\n  Independence groups: {len(groups)}")
    print(f"  Redundant claims:   {12 - len(groups)}")

    # Detailed breakdown
    print("\n  ── Dependency details ──")
    print("""
    GROUP 'twelve' (4 claims, 1 fact):
      H-CHEM-012: Octahedron edges = 12
      H-CHEM-015: Cyclohexane H-count = 12 (= 2*6, trivial from CnH2n)
      H-CHEM-027: Diamond 2nd neighbors = 12
      H-CHEM-029: C60 pentagons = 12
      All map to sigma(6)=12. Three are about carbon structures
      (carbon = element 6), so they share a root cause.
      Octahedron edges = 12 is geometry, independent of carbon.
      C60 pentagons = 12 follows from Euler's formula for any
      sphere tiled by hexagons+pentagons.
      Sub-independence: ~2 independent facts (geometry vs carbon chemistry)

    GROUP 'symmetry_24' (2 claims, 1 fact):
      H-CHEM-011: D6h order = 24
      H-CHEM-014: Td order = 24
      Different symmetry groups but same number.
      D6h = dihedral of hexagon (because benzene has 6 carbons).
      Td = tetrahedral (because carbon makes 4 bonds).
      Both ultimately trace to carbon's properties.
      Sub-independence: 1-2 (D6h requires 6-fold ring; Td is about 4 bonds)

    GROUP 'Z=6' (1 claim):
      H-CHEM-001: Carbon Z=6 is perfect.
      ROOT CAUSE for many others. Not independent of carbon facts.

    GROUP 'tetrahedral_angle' (1 claim):
      H-CHEM-002: cos(109.47) = -1/3
      Pure geometry of regular tetrahedron. Independent of Z=6.
      But 1/3 maps to "meta fixed point" which is just a common fraction.

    GROUP 'position_fraction' (1 claim):
      H-CHEM-010: 4/8 = 1/2. Extremely trivial.

    GROUP 'exponential_1e' (1 claim):
      H-CHEM-016: exp(-1)=1/e. Mathematical tautology, not chemistry.

    GROUP 'half' (1 claim):
      H-CHEM-017: kf/(kf+kr)=1/2 at K=1. Mathematical tautology.

    GROUP 'two' (1 claim):
      H-CHEM-026: Graphene 2 atoms/cell = phi(6).
      phi(6)=2, and 2 is the most common small number.
      Graphene's 2-atom cell comes from honeycomb lattice geometry.
    """)

    # Tautology count
    tautologies = [c for c in GREEN_CLAIMS if c['match'] == 'tautology']
    print(f"  Tautologies (math identities, not chemistry): {len(tautologies)}")
    for t in tautologies:
        print(f"    {t['id']}: {t['desc']}")

    return groups


def monte_carlo_test(n_trials=10000, seed=42):
    """Monte Carlo: how often does a random number match 12+ chemistry facts?"""
    print("\n" + "=" * 70)
    print("  TEXAS SHARPSHOOTER: Monte Carlo Test")
    print("=" * 70)

    # First, count actual matches for n=6
    real_matches, real_items = count_matches(6, CHEMISTRY_NUMBERS_UNIQUE)
    print(f"\n  n=6 arithmetic matches {real_matches}/{len(CHEMISTRY_NUMBERS_UNIQUE)} chemistry numbers")
    print(f"  Chemistry number pool: {len(CHEMISTRY_NUMBERS_UNIQUE)} unique values")
    print(f"\n  Matched items:")
    for chem, arith in real_items:
        print(f"    chem={chem:10g}  <-->  n=6 output={arith:10g}")

    # Now test random numbers
    rng = random.Random(seed)
    random_match_counts = []
    candidates = list(range(2, 101))  # Test n=2 through 100

    print(f"\n  Testing n=2..100 (which n values match as well as n=6?):")
    n_match_counts = {}
    for n in candidates:
        m, _ = count_matches(n, CHEMISTRY_NUMBERS_UNIQUE)
        n_match_counts[n] = m

    # Sort by match count
    sorted_n = sorted(n_match_counts.items(), key=lambda x: -x[1])
    print(f"\n  {'n':>5s}  {'matches':>8s}  {'perfect?':>9s}  {'arithmetic outputs':>20s}")
    print(f"  {'-'*5}  {'-'*8}  {'-'*9}  {'-'*20}")
    for n, m in sorted_n[:20]:
        perf = "YES" if is_perfect(n) else ""
        outputs = n_arithmetic_outputs(n)
        int_outputs = sorted([int(x) for x in outputs if x == int(x) and 0 < x < 200])
        print(f"  {n:5d}  {m:8d}  {perf:>9s}  {int_outputs[:8]}")

    n6_matches = n_match_counts[6]
    better_or_equal = sum(1 for n, m in n_match_counts.items() if m >= n6_matches)
    print(f"\n  n=6 matches: {n6_matches}")
    print(f"  Numbers matching >= {n6_matches}: {better_or_equal}/{len(candidates)}")
    print(f"  Rank of n=6: {sum(1 for n, m in n_match_counts.items() if m > n6_matches) + 1}/{len(candidates)}")

    # Monte Carlo with random "special number" sets
    print(f"\n  ── Monte Carlo: random special number sets ({n_trials} trials) ──")
    print(f"  Each trial: pick a random n in [2,1000], compute arithmetic outputs,")
    print(f"  count matches against chemistry pool.")

    random_matches = []
    for _ in range(n_trials):
        n = rng.randint(2, 1000)
        m, _ = count_matches(n, CHEMISTRY_NUMBERS_UNIQUE)
        random_matches.append(m)

    mean_random = sum(random_matches) / len(random_matches)
    std_random = (sum((x - mean_random)**2 for x in random_matches) / len(random_matches)) ** 0.5
    max_random = max(random_matches)

    print(f"\n  Random n matches:  mean={mean_random:.2f}  std={std_random:.2f}  max={max_random}")
    print(f"  n=6 matches:       {n6_matches}")

    if std_random > 0:
        z_score = (n6_matches - mean_random) / std_random
    else:
        z_score = 0
    p_value = sum(1 for x in random_matches if x >= n6_matches) / n_trials

    print(f"  Z-score:           {z_score:.2f}")
    print(f"  p-value:           {p_value:.4f}")

    # Distribution histogram
    hist = Counter(random_matches)
    max_count = max(hist.values())
    print(f"\n  Distribution of random match counts:")
    print(f"  {'matches':>8s}  {'count':>6s}  histogram")
    for k in range(max(hist.keys()) + 1):
        count = hist.get(k, 0)
        bar = '#' * int(50 * count / max_count) if max_count > 0 else ''
        marker = " <-- n=6" if k == n6_matches else ""
        print(f"  {k:8d}  {count:6d}  {bar}{marker}")

    return n6_matches, mean_random, std_random, p_value, z_score


def carbon_centrality_analysis():
    """How many of the 12 are specifically about carbon?"""
    print("\n" + "=" * 70)
    print("  CARBON CENTRALITY ANALYSIS")
    print("=" * 70)

    carbon_specific = []
    general_chem = []
    pure_math = []

    for c in GREEN_CLAIMS:
        cid = c['id']
        desc = c['desc']
        if cid in ['H-CHEM-001', 'H-CHEM-015', 'H-CHEM-026', 'H-CHEM-027', 'H-CHEM-029']:
            carbon_specific.append(c)
        elif cid in ['H-CHEM-002', 'H-CHEM-010', 'H-CHEM-011', 'H-CHEM-012', 'H-CHEM-014']:
            # These involve carbon but the math fact is geometry
            carbon_specific.append(c)
        elif cid in ['H-CHEM-016', 'H-CHEM-017']:
            pure_math.append(c)
        else:
            general_chem.append(c)

    print(f"\n  Carbon-specific:  {len(carbon_specific)}/12")
    for c in carbon_specific:
        print(f"    {c['id']}: {c['desc']}")

    print(f"\n  General chemistry: {len(general_chem)}/12")
    for c in general_chem:
        print(f"    {c['id']}: {c['desc']}")

    print(f"\n  Pure math tautologies: {len(pure_math)}/12")
    for c in pure_math:
        print(f"    {c['id']}: {c['desc']}")

    print(f"""
  Conclusion:
    10/12 GREEN claims are about carbon or carbon compounds.
    2/12 are mathematical tautologies (exp(-1)=1/e, kf/(kf+kr)=1/2).
    0/12 are about non-carbon chemistry.

    This is expected: carbon IS element 6, so any property of carbon
    or its compounds can potentially be expressed using 6's arithmetic.
    The question is whether the SPECIFIC numbers (12, 24, 2, 4) that
    appear are surprising or inevitable given Z=6.
    """)


def anti_examples():
    """Chemistry facts that SHOULD match n=6 but DON'T."""
    print("\n" + "=" * 70)
    print("  ANTI-EXAMPLES: Chemistry facts that DON'T match n=6")
    print("=" * 70)

    anti = [
        ("Water bond angle", 104.5, "Should relate to 6-arithmetic but doesn't cleanly map"),
        ("CO2 bond angle", 180, "Linear, no 6 connection"),
        ("Diamond band gap (eV)", 5.47, "Not a simple 6-function"),
        ("Graphite interlayer (pm)", 335, "No 6-arithmetic match"),
        ("Benzene C-C bond length (pm)", 140, "Not sigma(6) or tau(6)"),
        ("C60 vertices", 60, "60 = 10*6, but 10 is not a divisor function of 6"),
        ("C60 hexagons", 20, "Not a standard n=6 output"),
        ("Carbon electronegativity", 2.55, "No clean mapping"),
        ("Diamond density (g/cc)", 3.51, "No clean mapping"),
        ("Methane bond angle", 109.47, "cos=-1/3 maps, but angle itself=109.47 doesn't"),
        ("Benzene pi electrons", 6, "= n itself, but that's trivially circular"),
        ("Carbon covalent radius (pm)", 77, "Prime, no 6-arithmetic match"),
        ("Graphene band gap", 0, "Zero, trivial"),
        ("CO bond order", 3, "Divisor of 6, but trivially common"),
        ("Carbon allotropes", "5+", "More than tau(6)=4, claim H-CHEM-024 was refuted"),
    ]

    print(f"\n  {'Property':40s}  {'Value':>10s}  Note")
    print(f"  {'-'*40}  {'-'*10}  {'-'*40}")
    for name, val, note in anti:
        print(f"  {name:40s}  {str(val):>10s}  {note}")

    print(f"\n  Anti-example count: {len(anti)}")
    print(f"  GREEN match count:  12")
    print(f"  Match ratio:        12/(12+{len(anti)}) = {12/(12+len(anti)):.1%}")
    print(f"""
  With {len(anti)} anti-examples vs 12 matches, the selection effect is clear.
  Many carbon chemistry numbers do NOT match n=6 arithmetic.
  The 12 that do were selected post-hoc from a much larger space.
    """)


def main():
    parser = argparse.ArgumentParser(description='Texas Sharpshooter test for chemistry hypotheses')
    parser.add_argument('--trials', type=int, default=10000, help='Monte Carlo trials')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()

    # 1. Independence analysis
    groups = independence_analysis()

    # 2. Carbon centrality
    carbon_centrality_analysis()

    # 3. Anti-examples
    anti_examples()

    # 4. Monte Carlo Texas Sharpshooter
    n6_matches, mean_rand, std_rand, p_value, z_score = monte_carlo_test(
        n_trials=args.trials, seed=args.seed
    )

    # 5. Summary
    print("\n" + "=" * 70)
    print("  FINAL SUMMARY")
    print("=" * 70)
    print(f"""
  12 GREEN chemistry hypotheses analysis:

  Independence:
    12 claims  -->  {len(groups)} independence groups
    4 claims share the "twelve" group (sigma(6)=12 appears everywhere)
    2 claims share the "symmetry_24" group
    2 claims are mathematical tautologies (not chemistry)

  Effective independent claims: ~6-7 (generous), ~4-5 (strict)

  Carbon centrality:
    10/12 are about carbon or carbon compounds
    This is EXPECTED since carbon = element 6

  Anti-examples:
    15 carbon chemistry facts that DON'T match n=6 arithmetic
    Match ratio: 12/27 = 44% (not overwhelming)

  Texas Sharpshooter (Monte Carlo):
    n=6 matches {n6_matches} chemistry numbers from pool
    Random n matches {mean_rand:.1f} +/- {std_rand:.1f}
    Z-score: {z_score:.2f}
    p-value: {p_value:.4f}

  Interpretation:
    {"SIGNIFICANT (p < 0.05): n=6 matches more than chance" if p_value < 0.05 else "NOT SIGNIFICANT (p >= 0.05): n=6 does not match more than random numbers"}
    {"But: much of the signal comes from carbon BEING element 6 (circular)" if p_value < 0.05 else "The 12 GREEN claims are real chemistry facts with ad-hoc number mappings"}
    """)


if __name__ == '__main__':
    main()
