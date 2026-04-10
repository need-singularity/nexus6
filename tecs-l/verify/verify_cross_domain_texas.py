#!/usr/bin/env python3
"""Cross-domain unified Texas Sharpshooter test: Is n=6 genuinely special?

Collects ALL verified GREEN facts from every domain (chemistry, crystallography,
music, math, biology, medicine, physics, institutions) and tests whether n=6
matches more of them than any other n in [2,100].

Monte Carlo: 100,000 trials of random n to get distribution and p-value.
Control comparisons: n=12, n=24, n=60 (highly composite numbers).
Carbon removal test: is n=6 still special without carbon chemistry?

Usage:
    PYTHONPATH=. python3 verify/verify_cross_domain_texas.py
    PYTHONPATH=. python3 verify/verify_cross_domain_texas.py --trials 200000
"""

import math
import random
import argparse
from collections import Counter, defaultdict


# ══════════════════════════════════════════════════════════════════════
#  Number-theoretic functions
# ══════════════════════════════════════════════════════════════════════

def divisors(n):
    """All divisors of n."""
    d = []
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            d.append(i)
            if i != n // i:
                d.append(n // i)
    return sorted(d)


def sigma(n):
    return sum(divisors(n))


def tau(n):
    return len(divisors(n))


def phi(n):
    result = n
    p = 2
    temp = n
    while p * p <= temp:
        if temp % p == 0:
            while temp % p == 0:
                temp //= p
            result -= result // p
        p += 1
    if temp > 1:
        result -= result // temp
    return result


def sigma_neg1(n):
    return sum(1.0 / d for d in divisors(n))


def is_perfect(n):
    return sigma(n) == 2 * n


def lcm(a, b):
    return a * b // math.gcd(a, b)


# ══════════════════════════════════════════════════════════════════════
#  Arithmetic target set for a given n
# ══════════════════════════════════════════════════════════════════════

def arithmetic_targets(n):
    """Generate the set of 'natural' arithmetic outputs from n.

    We include: n, divisors, sigma, tau, phi, sigma_{-1},
    products/quotients of pairs of these, powers up to n^2,
    LCM and GCD of divisor pairs, and simple derived quantities.
    This must be the SAME function for all n -- no n=6 special casing.
    """
    d = divisors(n)
    s = sigma(n)
    t = tau(n)
    p = phi(n)
    sn1 = sigma_neg1(n)

    targets = set()

    # Direct values
    targets.add(n)
    targets.add(s)
    targets.add(t)
    targets.add(p)
    targets.add(round(sn1, 8))

    # All divisors and their reciprocals
    for dd in d:
        targets.add(dd)
        targets.add(round(1.0 / dd, 8))

    # n - d for each divisor (differences)
    for dd in d:
        targets.add(n - dd)

    # Powers
    targets.add(n * n)
    targets.add(n ** 3)

    # 2^k for k = divisors
    for dd in d:
        if dd <= 20:
            targets.add(2 ** dd)

    # Products of core functions (all pairs)
    core = [n, s, t, p, round(sn1, 8)]
    for i, a in enumerate(core):
        for b in core[i:]:
            targets.add(round(a * b, 8))
            if b != 0:
                targets.add(round(a / b, 8))
            if a != 0:
                targets.add(round(b / a, 8))

    # LCM of divisor pairs
    for i, a in enumerate(d):
        for b in d[i + 1:]:
            targets.add(lcm(a, b))

    # Factorial of small divisors
    for dd in d:
        if dd <= 10:
            targets.add(math.factorial(dd))

    # sigma(n) / n  (abundancy)
    targets.add(round(s / n, 8))

    # n - tau(n)  (appears in some claims)
    targets.add(n - t)

    # Discard negatives and very large numbers (> 10000) to keep fair
    targets = {x for x in targets if isinstance(x, (int, float))
               and -1 <= x <= 10000 and not (isinstance(x, float) and math.isnan(x))}

    return targets


# ══════════════════════════════════════════════════════════════════════
#  ALL verified GREEN facts across domains
# ══════════════════════════════════════════════════════════════════════
#  Each fact: numeric value, domain, description, whether it's carbon-specific

FACTS = [
    # ═══ CHEMISTRY ═══
    {'val': 6,    'domain': 'chemistry', 'desc': 'Carbon atomic number Z=6',
     'carbon': True, 'indep': 'carbon_Z'},
    {'val': 4,    'domain': 'chemistry', 'desc': 'sp3 bonds = 4 (tetrahedral)',
     'carbon': True, 'indep': 'sp3_bonds'},
    {'val': 24,   'domain': 'chemistry', 'desc': 'Benzene D6h symmetry order = 24',
     'carbon': True, 'indep': 'D6h_order'},
    {'val': 12,   'domain': 'chemistry', 'desc': 'Octahedron edges = 12',
     'carbon': False, 'indep': 'oct_edges'},
    {'val': 24,   'domain': 'chemistry', 'desc': 'Methane Td symmetry order = 24',
     'carbon': True, 'indep': 'Td_order'},
    {'val': 12,   'domain': 'chemistry', 'desc': 'Cyclohexane has 12 H atoms',
     'carbon': True, 'indep': 'cyclohexane_H'},
    {'val': 2,    'domain': 'chemistry', 'desc': 'Graphene unit cell = 2 atoms',
     'carbon': True, 'indep': 'graphene_cell'},
    {'val': 12,   'domain': 'chemistry', 'desc': 'Diamond 2nd-neighbor count = 12',
     'carbon': True, 'indep': 'diamond_12'},
    {'val': 12,   'domain': 'chemistry', 'desc': 'C60 has 12 pentagons',
     'carbon': True, 'indep': 'C60_pent'},
    {'val': 3,    'domain': 'chemistry', 'desc': 'Max bond order = 3 (triple bond)',
     'carbon': False, 'indep': 'bond_order_3'},
    {'val': 4,    'domain': 'chemistry', 'desc': 'sigma + pi orbital types in organics = 4 (s,px,py,pz)',
     'carbon': True, 'indep': 'orbital_4'},
    {'val': 6,    'domain': 'chemistry', 'desc': 'CHNOPS = 6 life elements',
     'carbon': True, 'indep': 'CHNOPS'},
    {'val': 6,    'domain': 'chemistry', 'desc': 'Max orbital degeneracy (f) = 2l+1 = 7... d=5, p=3; but max for first 36 elements: d-orbital deg=5',
     'carbon': False, 'indep': 'max_degen'},
    # glycolysis
    {'val': 6,    'domain': 'chemistry', 'desc': 'Glycolysis: glucose C6 splits to 2x C3',
     'carbon': True, 'indep': 'glycolysis'},
    {'val': 6,    'domain': 'chemistry', 'desc': '6 reading frames (3 forward + 3 reverse)',
     'carbon': False, 'indep': 'reading_frames'},

    # ═══ CRYSTALLOGRAPHY ═══
    {'val': 6,    'domain': 'crystal', 'desc': 'Kissing number K(2D) = 6',
     'carbon': False, 'indep': 'kiss_2d'},
    {'val': 12,   'domain': 'crystal', 'desc': 'Kissing number K(3D) = 12',
     'carbon': False, 'indep': 'kiss_3d'},
    {'val': 24,   'domain': 'crystal', 'desc': 'Kissing number K(4D) = 24',
     'carbon': False, 'indep': 'kiss_4d'},
    {'val': 2,    'domain': 'crystal', 'desc': 'Kissing number K(1D) = 2',
     'carbon': False, 'indep': 'kiss_1d'},
    {'val': 6,    'domain': 'crystal', 'desc': 'Cube edges = 12, faces = 6',
     'carbon': False, 'indep': 'cube_faces'},
    {'val': 12,   'domain': 'crystal', 'desc': 'Platonic solid: all have E = 6k edges (k=1..5)',
     'carbon': False, 'indep': 'platonic_edges'},

    # ═══ MUSIC ═══
    {'val': 12,   'domain': 'music', 'desc': '12 semitones per octave',
     'carbon': False, 'indep': 'semitones'},
    {'val': 2,    'domain': 'music', 'desc': 'Octave = frequency ratio 2:1',
     'carbon': False, 'indep': 'octave_ratio'},
    {'val': 3,    'domain': 'music', 'desc': 'Perfect fifth = 3:2 ratio (3 is divisor of 6)',
     'carbon': False, 'indep': 'fifth_ratio'},
    {'val': 12,   'domain': 'music', 'desc': 'LCM of consonance ratios uses 12 = LCM(2,3,4,6)',
     'carbon': False, 'indep': 'lcm_12'},

    # ═══ MATHEMATICS ═══
    {'val': 2,    'domain': 'math', 'desc': 'n=6: n - tau(n) = 6 - 4 = 2 = phi(6)',
     'carbon': False, 'indep': 'n_minus_tau'},
    {'val': 6,    'domain': 'math', 'desc': 'R(3,3) = 6 (Ramsey number)',
     'carbon': False, 'indep': 'ramsey'},
    {'val': 720,  'domain': 'math', 'desc': '6! = 720, D(6)/6! ~ 1/e',
     'carbon': False, 'indep': 'derangement'},
    {'val': 2,    'domain': 'math', 'desc': 'sigma(6)/6 = 2 = sigma_{-1}(6) (perfect number)',
     'carbon': False, 'indep': 'perfect'},
    {'val': 2,    'domain': 'math', 'desc': 'Euler formula V-E+F = 2 (Euler characteristic)',
     'carbon': False, 'indep': 'euler_char'},
    {'val': 132,  'domain': 'math', 'desc': 'Catalan(6) = 132',
     'carbon': False, 'indep': 'catalan'},
    {'val': 1,    'domain': 'math', 'desc': '1/1 + 1/2 + 1/3 + 1/6 = 2 = sigma_{-1}(6) exactly',
     'carbon': False, 'indep': 'harmonic_div'},

    # ═══ BIOLOGY ═══
    {'val': 6,    'domain': 'biology', 'desc': 'Telomere repeat TTAGGG = 6 nucleotides',
     'carbon': False, 'indep': 'telomere'},
    {'val': 64,   'domain': 'biology', 'desc': 'Genetic code: 64 = 2^6 codons',
     'carbon': False, 'indep': 'codons'},
    {'val': 6,    'domain': 'biology', 'desc': 'ATP synthase is a hexamer (6 subunits)',
     'carbon': False, 'indep': 'atp_hex'},
    {'val': 6,    'domain': 'biology', 'desc': '6 major CYP450 families in human drug metabolism',
     'carbon': False, 'indep': 'cyp450'},

    # ═══ MEDICINE ═══
    {'val': 6,    'domain': 'medicine', 'desc': 'SOFA score: 6 organ systems',
     'carbon': False, 'indep': 'sofa'},
    {'val': 12,   'domain': 'medicine', 'desc': 'GCS range = 15-3 = 12 possible scores',
     'carbon': False, 'indep': 'gcs_range'},

    # ═══ PHYSICS ═══
    {'val': 6,    'domain': 'physics', 'desc': 'ISCO radius = 6M (Schwarzschild)',
     'carbon': False, 'indep': 'isco'},
    {'val': 12,   'domain': 'physics', 'desc': 'ISCO L^2 = 12M^2 (angular momentum)',
     'carbon': False, 'indep': 'isco_L'},

    # ═══ INSTITUTIONS ═══
    {'val': 12,   'domain': 'institution', 'desc': '12 months in a year',
     'carbon': False, 'indep': 'months'},
    {'val': 24,   'domain': 'institution', 'desc': '24 hours in a day',
     'carbon': False, 'indep': 'hours'},
    {'val': 60,   'domain': 'institution', 'desc': '60 seconds/minutes (sexagesimal)',
     'carbon': False, 'indep': 'sexagesimal'},
    {'val': 12,   'domain': 'institution', 'desc': 'Common law jury = 12',
     'carbon': False, 'indep': 'jury'},
    {'val': 6,    'domain': 'institution', 'desc': 'Petit jury = 6 (US states)',
     'carbon': False, 'indep': 'petit_jury'},
]


# ══════════════════════════════════════════════════════════════════════
#  Matching logic
# ══════════════════════════════════════════════════════════════════════

def matches_targets(fact_val, targets):
    """Check if fact_val matches any value in targets.
    Integer facts require exact match.
    Float facts allow 1% tolerance.
    """
    for t in targets:
        if isinstance(fact_val, int) or (isinstance(fact_val, float) and fact_val == int(fact_val)):
            if fact_val == t:
                return True
            # Also check float representation
            if abs(fact_val - t) < 0.0001:
                return True
        else:
            if abs(fact_val) > 0.001:
                if abs(fact_val - t) / abs(fact_val) < 0.01:
                    return True
            else:
                if abs(fact_val - t) < 0.001:
                    return True
    return False


def count_matches_for_n(n, facts):
    """Count how many facts match arithmetic targets of n."""
    targets = arithmetic_targets(n)
    count = 0
    matched = []
    for f in facts:
        if matches_targets(f['val'], targets):
            count += 1
            matched.append(f)
    return count, matched


# ══════════════════════════════════════════════════════════════════════
#  Main analysis
# ══════════════════════════════════════════════════════════════════════

def rank_all_n(facts, n_range=(2, 101)):
    """Rank all n by match count."""
    results = {}
    for n in range(n_range[0], n_range[1]):
        count, matched = count_matches_for_n(n, facts)
        results[n] = {
            'count': count,
            'matched': matched,
            'sigma': sigma(n),
            'tau': tau(n),
            'phi': phi(n),
            'perfect': is_perfect(n),
            'target_size': len(arithmetic_targets(n)),
        }
    return results


def monte_carlo(facts, n_trials=100000, seed=42):
    """Monte Carlo: random n in [2,100], count matches."""
    rng = random.Random(seed)
    counts = []
    for _ in range(n_trials):
        n = rng.randint(2, 100)
        c, _ = count_matches_for_n(n, facts)
        counts.append(c)
    return counts


def print_domain_breakdown(matched_facts):
    """Print breakdown by domain."""
    domains = defaultdict(list)
    for f in matched_facts:
        domains[f['domain']].append(f['desc'])
    for dom in sorted(domains.keys()):
        print(f"    {dom:15s}: {len(domains[dom])} matches")
        for desc in domains[dom]:
            print(f"      - {desc}")


def main():
    parser = argparse.ArgumentParser(description='Cross-domain unified Texas Sharpshooter')
    parser.add_argument('--trials', type=int, default=100000, help='Monte Carlo trials')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()

    total_facts = len(FACTS)
    carbon_facts = sum(1 for f in FACTS if f['carbon'])
    non_carbon_facts = total_facts - carbon_facts

    print("=" * 75)
    print("  CROSS-DOMAIN UNIFIED TEXAS SHARPSHOOTER TEST")
    print("  Is n=6 genuinely special across ALL domains?")
    print("=" * 75)

    print(f"\n  Total GREEN facts collected: {total_facts}")
    print(f"  Carbon-specific facts:      {carbon_facts}")
    print(f"  Non-carbon facts:           {non_carbon_facts}")
    print(f"  Domains: {len(set(f['domain'] for f in FACTS))}")

    domain_counts = Counter(f['domain'] for f in FACTS)
    for dom, cnt in sorted(domain_counts.items(), key=lambda x: -x[1]):
        print(f"    {dom:15s}: {cnt}")

    # ── 1. Rank all n=2..100 ──────────────────────────────────────
    print("\n" + "=" * 75)
    print("  SECTION 1: RANKING n=2..100 (ALL FACTS)")
    print("=" * 75)

    results = rank_all_n(FACTS)
    sorted_results = sorted(results.items(), key=lambda x: -x[1]['count'])

    print(f"\n  {'Rank':>4s}  {'n':>4s}  {'Matches':>7s}  {'sigma':>6s}  {'tau':>4s}  {'phi':>4s}  {'Perf':>5s}  {'Targets':>7s}")
    print(f"  {'----':>4s}  {'----':>4s}  {'-------':>7s}  {'-----':>6s}  {'---':>4s}  {'---':>4s}  {'----':>5s}  {'-------':>7s}")
    for rank, (n, info) in enumerate(sorted_results[:30], 1):
        perf_mark = "YES" if info['perfect'] else ""
        marker = " <---" if n == 6 else ""
        marker = " [12]" if n == 12 else marker
        marker = " [24]" if n == 24 else marker
        marker = " [60]" if n == 60 else marker
        print(f"  {rank:4d}  {n:4d}  {info['count']:7d}  {info['sigma']:6d}  {info['tau']:4d}  {info['phi']:4d}  {perf_mark:>5s}  {info['target_size']:7d}{marker}")

    n6_count = results[6]['count']
    n6_rank = sum(1 for n, info in results.items() if info['count'] > n6_count) + 1
    print(f"\n  n=6 rank: {n6_rank}/{len(results)} (matches {n6_count}/{total_facts} facts)")

    # ── 2. n=6 detailed breakdown ─────────────────────────────────
    print("\n" + "=" * 75)
    print("  SECTION 2: n=6 DETAILED MATCH BREAKDOWN")
    print("=" * 75)

    _, matched_6 = count_matches_for_n(6, FACTS)
    print(f"\n  n=6 matches {len(matched_6)}/{total_facts} facts:")
    print_domain_breakdown(matched_6)

    # Which facts does n=6 MISS?
    missed = [f for f in FACTS if f not in matched_6]
    if missed:
        print(f"\n  n=6 MISSES {len(missed)} facts:")
        for f in missed:
            print(f"    [{f['domain']:12s}] val={f['val']:>6g}  {f['desc']}")

    # ── 3. Control comparisons ────────────────────────────────────
    print("\n" + "=" * 75)
    print("  SECTION 3: CONTROL COMPARISONS (n=6 vs n=12, 24, 28, 60)")
    print("=" * 75)

    controls = [6, 12, 24, 28, 60]
    for cn in controls:
        count, matched = count_matches_for_n(cn, FACTS)
        perf = " (PERFECT)" if is_perfect(cn) else ""
        divs = divisors(cn)
        print(f"\n  n={cn}{perf}")
        print(f"    Divisors: {divs}")
        print(f"    sigma={sigma(cn)}, tau={tau(cn)}, phi={phi(cn)}, sigma_{{-1}}={sigma_neg1(cn):.4f}")
        print(f"    Matches: {count}/{total_facts}")
        print(f"    Target set size: {len(arithmetic_targets(cn))}")

    # ── 4. Monte Carlo ────────────────────────────────────────────
    print("\n" + "=" * 75)
    print(f"  SECTION 4: MONTE CARLO ({args.trials:,} trials)")
    print("=" * 75)

    print(f"\n  Drawing random n in [2,100], counting matches against {total_facts} facts...")
    mc_counts = monte_carlo(FACTS, n_trials=args.trials, seed=args.seed)

    mean_mc = sum(mc_counts) / len(mc_counts)
    std_mc = (sum((x - mean_mc)**2 for x in mc_counts) / len(mc_counts)) ** 0.5
    max_mc = max(mc_counts)
    min_mc = min(mc_counts)

    print(f"\n  Random n match distribution:")
    print(f"    Mean:   {mean_mc:.2f}")
    print(f"    StdDev: {std_mc:.2f}")
    print(f"    Min:    {min_mc}")
    print(f"    Max:    {max_mc}")

    z_score = (n6_count - mean_mc) / std_mc if std_mc > 0 else 0
    p_value = sum(1 for x in mc_counts if x >= n6_count) / args.trials

    print(f"\n  n=6 matches:  {n6_count}")
    print(f"  Z-score:      {z_score:.3f}")
    print(f"  p-value:      {p_value:.6f}")

    if p_value == 0:
        print(f"  p-value:      < {1.0/args.trials:.1e} (none in {args.trials:,} trials)")

    # Histogram
    hist = Counter(mc_counts)
    max_hist = max(hist.values())
    print(f"\n  {'Matches':>8s}  {'Count':>7s}  {'Pct':>6s}  Histogram")
    print(f"  {'-------':>8s}  {'-----':>7s}  {'---':>6s}  ---------")
    for k in range(min(hist.keys()), max(hist.keys()) + 2):
        count = hist.get(k, 0)
        pct = 100.0 * count / args.trials
        bar_len = int(50 * count / max_hist) if max_hist > 0 else 0
        bar = '#' * bar_len
        marker = " <-- n=6" if k == n6_count else ""
        print(f"  {k:8d}  {count:7d}  {pct:5.1f}%  {bar}{marker}")

    # ── 5. Carbon removal test ────────────────────────────────────
    print("\n" + "=" * 75)
    print("  SECTION 5: CARBON REMOVAL TEST")
    print("  After removing all carbon-specific facts, is n=6 still special?")
    print("=" * 75)

    non_carbon = [f for f in FACTS if not f['carbon']]
    print(f"\n  Non-carbon facts: {len(non_carbon)}/{total_facts}")

    results_nc = rank_all_n(non_carbon)
    sorted_nc = sorted(results_nc.items(), key=lambda x: -x[1]['count'])

    n6_nc = results_nc[6]['count']
    n6_rank_nc = sum(1 for n, info in results_nc.items() if info['count'] > n6_nc) + 1

    print(f"\n  {'Rank':>4s}  {'n':>4s}  {'Matches':>7s}  {'Perf':>5s}")
    print(f"  {'----':>4s}  {'----':>4s}  {'-------':>7s}  {'----':>5s}")
    for rank, (n, info) in enumerate(sorted_nc[:20], 1):
        perf_mark = "YES" if info['perfect'] else ""
        marker = " <---" if n == 6 else ""
        marker = " [12]" if n == 12 else marker
        marker = " [24]" if n == 24 else marker
        marker = " [60]" if n == 60 else marker
        print(f"  {rank:4d}  {n:4d}  {info['count']:7d}  {perf_mark:>5s}{marker}")

    print(f"\n  n=6 rank (no carbon): {n6_rank_nc}/{len(results_nc)} (matches {n6_nc}/{len(non_carbon)})")

    # Monte Carlo without carbon
    print(f"\n  Monte Carlo without carbon ({args.trials:,} trials)...")
    mc_nc = monte_carlo(non_carbon, n_trials=args.trials, seed=args.seed)
    mean_nc = sum(mc_nc) / len(mc_nc)
    std_nc = (sum((x - mean_nc)**2 for x in mc_nc) / len(mc_nc)) ** 0.5
    z_nc = (n6_nc - mean_nc) / std_nc if std_nc > 0 else 0
    p_nc = sum(1 for x in mc_nc if x >= n6_nc) / args.trials

    print(f"    Mean: {mean_nc:.2f}, Std: {std_nc:.2f}")
    print(f"    n=6 matches: {n6_nc}, Z-score: {z_nc:.3f}, p-value: {p_nc:.6f}")
    if p_nc == 0:
        print(f"    p-value: < {1.0/args.trials:.1e}")

    # ── 6. Target set fairness check ──────────────────────────────
    print("\n" + "=" * 75)
    print("  SECTION 6: FAIRNESS CHECK -- TARGET SET SIZES")
    print("  Does n=6 win just because it generates more targets?")
    print("=" * 75)

    sizes = [(n, len(arithmetic_targets(n))) for n in range(2, 101)]
    sizes.sort(key=lambda x: -x[1])
    n6_size = len(arithmetic_targets(6))
    n6_size_rank = sum(1 for n, s in sizes if s > n6_size) + 1

    print(f"\n  Top 15 by target set size:")
    print(f"  {'n':>4s}  {'Targets':>7s}  {'Match':>5s}")
    print(f"  {'--':>4s}  {'-------':>7s}  {'-----':>5s}")
    for n, sz in sizes[:15]:
        m = results[n]['count']
        marker = " <---" if n == 6 else ""
        print(f"  {n:4d}  {sz:7d}  {m:5d}{marker}")

    print(f"\n  n=6 target set size: {n6_size} (rank {n6_size_rank}/99)")

    # Match rate = matches / target_size
    print(f"\n  Match efficiency (matches per target):")
    efficiencies = [(n, results[n]['count'] / results[n]['target_size'])
                    for n in range(2, 101) if results[n]['target_size'] > 0]
    efficiencies.sort(key=lambda x: -x[1])
    print(f"  {'n':>4s}  {'Match':>5s}  {'Targets':>7s}  {'Efficiency':>10s}")
    print(f"  {'--':>4s}  {'-----':>5s}  {'-------':>7s}  {'----------':>10s}")
    for n, eff in efficiencies[:15]:
        marker = " <---" if n == 6 else ""
        print(f"  {n:4d}  {results[n]['count']:5d}  {results[n]['target_size']:7d}  {eff:10.4f}{marker}")

    # ── 7. Domain-specific ranking ────────────────────────────────
    print("\n" + "=" * 75)
    print("  SECTION 7: DOMAIN-SPECIFIC n=6 RANKING")
    print("=" * 75)

    domains = sorted(set(f['domain'] for f in FACTS))
    for dom in domains:
        dom_facts = [f for f in FACTS if f['domain'] == dom]
        dom_results = {}
        for n in range(2, 101):
            c, _ = count_matches_for_n(n, dom_facts)
            dom_results[n] = c

        n6_dom = dom_results[6]
        n6_dom_rank = sum(1 for v in dom_results.values() if v > n6_dom) + 1
        top3 = sorted(dom_results.items(), key=lambda x: -x[1])[:3]

        print(f"\n  {dom:15s} ({len(dom_facts)} facts): "
              f"n=6 matches {n6_dom}/{len(dom_facts)}, rank {n6_dom_rank}/99")
        print(f"    Top 3: ", end="")
        print(", ".join(f"n={n}({c})" for n, c in top3))

    # ══════════════════════════════════════════════════════════════
    #  FINAL VERDICT
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 75)
    print("  FINAL VERDICT")
    print("=" * 75)

    print(f"""
  Total facts:          {total_facts}
  n=6 matches:          {n6_count}/{total_facts}
  n=6 rank (all):       {n6_rank}/99

  Monte Carlo (all facts, {args.trials:,} trials):
    Mean matches:       {mean_mc:.2f} +/- {std_mc:.2f}
    n=6 Z-score:        {z_score:.3f}
    n=6 p-value:        {p_value:.6f}

  Without carbon ({len(non_carbon)} facts):
    n=6 matches:        {n6_nc}/{len(non_carbon)}
    n=6 rank:           {n6_rank_nc}/99
    n=6 Z-score:        {z_nc:.3f}
    n=6 p-value:        {p_nc:.6f}

  Controls:
    n=12 matches:       {results[12]['count']}/{total_facts} (highly composite)
    n=24 matches:       {results[24]['count']}/{total_facts}
    n=28 matches:       {results[28]['count']}/{total_facts} (perfect number)
    n=60 matches:       {results[60]['count']}/{total_facts}
""")

    # Honest assessment
    if z_score > 3:
        print("  ASSESSMENT: n=6 is HIGHLY SPECIAL (Z > 3, p < 0.001)")
        print("  The concentration of facts around n=6 arithmetic is unlikely by chance.")
    elif z_score > 2:
        print("  ASSESSMENT: n=6 is SPECIAL (Z > 2, p < 0.05)")
        print("  Statistically significant, but could partly reflect selection bias.")
    elif z_score > 1:
        print("  ASSESSMENT: n=6 is MILDLY SPECIAL (Z > 1)")
        print("  Above average, but not statistically significant.")
    else:
        print("  ASSESSMENT: n=6 is NOT SPECIAL (Z < 1)")
        print("  Its match count is within normal range for any small number.")

    # Carbon dependency
    if z_nc > 2 and z_score > 2:
        print("\n  CARBON INDEPENDENCE: YES -- n=6 remains special without carbon.")
    elif z_nc < 1 and z_score > 2:
        print("\n  CARBON INDEPENDENCE: NO -- n=6's specialness depends heavily on carbon.")
        print("  Remove carbon, and n=6 becomes ordinary.")
    else:
        print(f"\n  CARBON INDEPENDENCE: PARTIAL -- Z drops from {z_score:.1f} to {z_nc:.1f}")

    # Small number bias check
    small_n_matches = [results[n]['count'] for n in range(2, 11)]
    large_n_matches = [results[n]['count'] for n in range(50, 101)]
    mean_small = sum(small_n_matches) / len(small_n_matches)
    mean_large = sum(large_n_matches) / len(large_n_matches)
    print(f"\n  SMALL NUMBER BIAS CHECK:")
    print(f"    Mean matches n=2..10:   {mean_small:.1f}")
    print(f"    Mean matches n=50..100: {mean_large:.1f}")
    if mean_small > mean_large * 1.5:
        print(f"    WARNING: Small numbers match {mean_small/mean_large:.1f}x more than large ones.")
        print(f"    This suggests small-number bias inflates n=6's score.")
    else:
        print(f"    Ratio: {mean_small/mean_large:.1f}x -- moderate small-number advantage.")

    print("\n" + "=" * 75)


if __name__ == '__main__':
    main()
