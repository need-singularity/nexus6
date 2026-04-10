#!/usr/bin/env python3
"""Texas Sharpshooter test for 20 institutional/law/history hypotheses.

Tests: How many institutional facts match n=6 arithmetic by chance?
Monte Carlo with 10,000 trials across random "special numbers".

Usage:
    PYTHONPATH=. python3 verify/verify_institutions_texas.py
    PYTHONPATH=. python3 verify/verify_institutions_texas.py --trials 50000
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

def tau(n):
    """Number of divisors."""
    return len(divisors(n))

def phi(n):
    """Euler totient."""
    return sum(1 for k in range(1, n+1) if math.gcd(k, n) == 1)

def sigma_neg1(n):
    """Sum of reciprocals of divisors."""
    return sum(1/d for d in divisors(n))


# ── The 20 institutional claims ─────────────────────────────────
# Each claim: institutional fact, what n=6 function produces the match,
# match quality, and independence group.

CLAIMS = [
    # ═══ A. Legal Systems (5) ═══
    {
        'id': 'H-INST-001',
        'desc': 'Common law jury = 12 = sigma(6)',
        'fact_value': 12,
        'n6_function': 'sigma(6)',
        'n6_value': 12,
        'match': 'exact',
        'independence_group': 'jury_twelve',
        'category': 'Legal',
        'fact_source': 'English common law tradition, 12-person jury since at least 1166 (Assize of Clarendon)',
        'notes': '12 is extremely common in human systems (months, hours, dozens). '
                 'Jury size was likely influenced by 12 apostles or 12 tribes of Israel, '
                 'not by divisor sums. Still, exact match.',
    },
    {
        'id': 'H-INST-002',
        'desc': 'Petit jury in some US states = 6',
        'fact_value': 6,
        'n6_function': 'n itself',
        'n6_value': 6,
        'match': 'exact',
        'independence_group': 'jury_six',
        'category': 'Legal',
        'fact_source': 'Williams v. Florida (1970): SCOTUS ruled 6-person juries constitutional for non-capital cases',
        'notes': 'Derived from cost-saving, not number theory. But 6 and 12 both appear in jury systems.',
    },
    {
        'id': 'H-INST-003',
        'desc': 'US Supreme Court originally 6 justices (1789)',
        'fact_value': 6,
        'n6_function': 'n itself',
        'n6_value': 6,
        'match': 'exact',
        'independence_group': 'scotus_six',
        'category': 'Legal',
        'fact_source': 'Judiciary Act of 1789: 1 Chief Justice + 5 Associate Justices = 6',
        'notes': 'Changed to 5, 7, 9, 10, 7, 9 over history. Current 9 since 1869. '
                 'Original 6 was practical (circuit riding). Not n=6 driven.',
    },
    {
        'id': 'H-INST-004',
        'desc': 'Major legal traditions = 6 (civil, common, religious, customary, mixed, hybrid)',
        'fact_value': 6,
        'n6_function': 'n itself',
        'n6_value': 6,
        'match': 'approximate',
        'independence_group': 'legal_traditions',
        'category': 'Legal',
        'fact_source': 'JuriGlobe (U of Ottawa) lists 5 main systems; "6" requires adding hybrid as separate',
        'notes': 'CHERRY-PICKED. Classification depends on taxonomy. JuriGlobe uses 5 groups. '
                 'Some scholars count 3-4 (civil, common, religious, customary). '
                 'Getting to 6 requires a specific splitting choice. Grade: white circle.',
    },
    {
        'id': 'H-INST-005',
        'desc': 'UN Security Council permanent members = 5, total = 15 = sigma(6)+tau(6)-1',
        'fact_value': 15,
        'n6_function': 'sigma(6)+tau(6)-1 = 12+4-1',
        'n6_value': 15,
        'match': 'ad_hoc',
        'independence_group': 'unsc',
        'category': 'Legal',
        'fact_source': 'UN Charter Chapter V: 5 permanent + 10 non-permanent = 15',
        'notes': 'FORMULA IS AD HOC. sigma(6)+tau(6)-1 is cherry-picked arithmetic. '
                 'The -1 correction is a red flag. 15 = 3*5, no clean n=6 expression. '
                 'Grade: black square.',
    },
    # ═══ B. Government Structure (5) ═══
    {
        'id': 'H-INST-006',
        'desc': 'Separation of powers: 3 branches = divisor of 6',
        'fact_value': 3,
        'n6_function': 'divisor of 6',
        'n6_value': 3,
        'match': 'exact',
        'independence_group': 'three_branches',
        'category': 'Government',
        'fact_source': 'Montesquieu (1748), US Constitution (1789): legislative, executive, judicial',
        'notes': '3 is a divisor of 6, but 3 divides half of all integers. '
                 'Trias politica from Montesquieu, not number theory. '
                 'Match is real but 3 is too common to be meaningful.',
    },
    {
        'id': 'H-INST-007',
        'desc': 'Bicameral legislature = 2 chambers = phi(6)',
        'fact_value': 2,
        'n6_function': 'phi(6)',
        'n6_value': 2,
        'match': 'exact',
        'independence_group': 'bicameral',
        'category': 'Government',
        'fact_source': 'UK Parliament (Lords+Commons), US Congress (Senate+House), most democracies',
        'notes': '2 is the most trivial match possible. phi(n)=2 for any prime. '
                 'Bicameralism from practical compromise (large/small state representation). '
                 'Grade: white circle (trivially common number).',
    },
    {
        'id': 'H-INST-008',
        'desc': 'G6 was original summit group (1975)',
        'fact_value': 6,
        'n6_function': 'n itself',
        'n6_value': 6,
        'match': 'exact',
        'independence_group': 'g6',
        'category': 'Government',
        'fact_source': 'Rambouillet Summit 1975: France, US, UK, Germany, Japan, Italy = 6 nations',
        'notes': 'Canada joined 1976 (G7), Russia 1997 (G8), kicked out 2014 (back to G7). '
                 'Original 6 = largest Western economies at the time. Practical, not numerological. '
                 'But the fact that the initial natural grouping was 6 is a real historical fact.',
    },
    {
        'id': 'H-INST-009',
        'desc': 'NATO founding members = 12 = sigma(6)',
        'fact_value': 12,
        'n6_function': 'sigma(6)',
        'n6_value': 12,
        'match': 'exact',
        'independence_group': 'nato_founding',
        'category': 'Government',
        'fact_source': 'Washington Treaty 1949: US, Canada, UK, France, Belgium, Netherlands, '
                       'Luxembourg, Norway, Denmark, Iceland, Italy, Portugal = 12',
        'notes': 'Exact match. 12 founding members is a historical fact. '
                 'But 12 is common in human groupings (jurors, apostles, months).',
    },
    {
        'id': 'H-INST-010',
        'desc': 'EU founding members = 6 (Treaty of Rome 1957)',
        'fact_value': 6,
        'n6_function': 'n itself',
        'n6_value': 6,
        'match': 'exact',
        'independence_group': 'eu_six',
        'category': 'Government',
        'fact_source': 'France, Germany, Italy, Belgium, Netherlands, Luxembourg = 6',
        'notes': 'Inner Six of ECSC (1951) then EEC (1957). Historical fact. '
                 'Benelux 3 + 3 large = 6. Practical grouping.',
    },
    # ═══ C. Calendar/Time (5) ═══
    {
        'id': 'H-INST-011',
        'desc': '12 months = sigma(6)',
        'fact_value': 12,
        'n6_function': 'sigma(6)',
        'n6_value': 12,
        'match': 'exact',
        'independence_group': 'twelve_months',
        'category': 'Calendar',
        'fact_source': 'Babylonian calendar, adopted by Romans, now universal. '
                       '~12 lunar cycles per solar year (actual: 12.37)',
        'notes': '12 months comes from lunar cycle count (~354 days / 29.5 = 12.0). '
                 'NOT from sigma(6). Astronomical origin. '
                 'But 12 = sigma(6) is arithmetically true regardless of cause.',
    },
    {
        'id': 'H-INST-012',
        'desc': '24 hours = sigma(6) * phi(6)',
        'fact_value': 24,
        'n6_function': 'sigma(6) * phi(6) = 12 * 2',
        'n6_value': 24,
        'match': 'exact',
        'independence_group': 'twentyfour_hours',
        'category': 'Calendar',
        'fact_source': 'Egyptian/Babylonian: 12 daylight hours + 12 night hours = 24',
        'notes': '24 = 12*2. Derived from 12 (halving day/night). '
                 'sigma(6)*phi(6) = 12*2 = 24 is arithmetically clean. '
                 'But 24 follows from 12, so NOT independent of H-INST-011.',
    },
    {
        'id': 'H-INST-013',
        'desc': '60 minutes/hour = 6 * 10; base-60 = sexagesimal',
        'fact_value': 60,
        'n6_function': '6 * 10',
        'n6_value': 60,
        'match': 'exact',
        'independence_group': 'sexagesimal',
        'category': 'Calendar',
        'fact_source': 'Babylonian base-60 number system, adopted for time/angle measurement',
        'notes': 'Babylonians chose base 60 because it has many divisors (1,2,3,4,5,6,10,12,15,20,30,60). '
                 '60 = 6*10 is trivially true. But the real reason for 60 is divisor richness, '
                 'which IS related to 6 being perfect (highly composite neighborhood). '
                 'This is the strongest institutional connection to n=6 properties.',
    },
    {
        'id': 'H-INST-014',
        'desc': '7 days per week (NOT 6)',
        'fact_value': 7,
        'n6_function': 'none',
        'n6_value': None,
        'match': 'no_match',
        'independence_group': 'week_seven',
        'category': 'Calendar',
        'fact_source': '7-day week from Babylonian astronomy (7 celestial bodies visible to naked eye)',
        'notes': 'HONEST FAILURE. 7 is not a divisor of 6, not sigma, tau, or phi. '
                 'Some cultures had 6-day market weeks (ancient Rome nundinae = 8, Akan = 6). '
                 'But the dominant global standard is 7. No n=6 match.',
    },
    {
        'id': 'H-INST-015',
        'desc': '4 seasons = tau(6)',
        'fact_value': 4,
        'n6_function': 'tau(6)',
        'n6_value': 4,
        'match': 'exact',
        'independence_group': 'four_seasons',
        'category': 'Calendar',
        'fact_source': 'Axial tilt creates 4 seasons (spring, summer, autumn, winter) in temperate zones',
        'notes': '4 seasons from ~23.4 degree axial tilt creating solstice/equinox pairs. '
                 'Tropical regions have 2 (wet/dry). Some cultures count 6 seasons (India). '
                 'tau(6)=4 but tau(n)=4 for any n=p*q (semiprimes), very common.',
    },
    # ═══ D. Historical Patterns (5) ═══
    {
        'id': 'H-INST-016',
        'desc': 'Kondratiev waves ~50-60 year cycles, midpoint ~55 != 6*10',
        'fact_value': 55,
        'n6_function': '~6*10 = 60?',
        'n6_value': 60,
        'match': 'approximate',
        'independence_group': 'kondratiev',
        'category': 'Historical',
        'fact_source': 'Kondratiev (1925): long economic waves of 40-60 years. Highly debated.',
        'notes': 'CHERRY-PICKED. Range is 40-60 years, not exactly 60. '
                 'Many economists reject Kondratiev waves entirely. '
                 'Matching "~60" to "6*10" is post-hoc numerology. Grade: black square.',
    },
    {
        'id': 'H-INST-017',
        'desc': 'Strauss-Howe 4 turnings = tau(6)',
        'fact_value': 4,
        'n6_function': 'tau(6)',
        'n6_value': 4,
        'match': 'exact',
        'independence_group': 'four_turnings',
        'category': 'Historical',
        'fact_source': 'Strauss & Howe (1997): High, Awakening, Unraveling, Crisis = 4 generational archetypes',
        'notes': 'Strauss-Howe theory is NOT mainstream academic history. Considered pop-history. '
                 '4-phase cycle is common pattern (4 seasons analogy). tau(6)=4 is trivially common. '
                 'Grade: white circle.',
    },
    {
        'id': 'H-INST-018',
        'desc': 'Civilizational collapse (Tainter): diminishing returns',
        'fact_value': None,
        'n6_function': 'none (qualitative analogy)',
        'n6_value': None,
        'match': 'no_match',
        'independence_group': 'tainter',
        'category': 'Historical',
        'fact_source': 'Tainter (1988): The Collapse of Complex Societies',
        'notes': 'NO NUMERICAL MATCH. Tainter describes diminishing marginal returns on complexity. '
                 'One could force-fit "inhibition increases" but that is pure narrative, not arithmetic. '
                 'Grade: black square (no verifiable numerical claim).',
    },
    {
        'id': 'H-INST-019',
        'desc': 'Sexagesimal (base 60) = 6*10, used for angles/time worldwide',
        'fact_value': 60,
        'n6_function': '6 * 10',
        'n6_value': 60,
        'match': 'exact',
        'independence_group': 'sexagesimal',  # Same group as H-INST-013
        'category': 'Historical',
        'fact_source': 'Sumerian/Babylonian (~3000 BCE): base-60 for math, astronomy, time, angles',
        'notes': 'NOT independent of H-INST-013 (same base-60 fact). '
                 'Historically, 60 was chosen FOR its divisibility properties, and 6 being '
                 'the smallest perfect number is part of why 6 and 12 are "nice" bases. '
                 'This is arguably the one genuine structural connection.',
    },
    {
        'id': 'H-INST-020',
        'desc': 'Dozen (12) and gross (144=12^2) as trade units = sigma(6) and sigma(6)^2',
        'fact_value': 12,
        'n6_function': 'sigma(6)',
        'n6_value': 12,
        'match': 'exact',
        'independence_group': 'dozen_trade',
        'category': 'Historical',
        'fact_source': 'Dozen: from Latin duodecim (12). Universal in trade since antiquity. '
                       'Gross = 144 = 12*12 (bulk counting unit)',
        'notes': 'Same root as months (H-INST-011): 12 is useful because it has many divisors '
                 '(1,2,3,4,6,12). This connects to 6 being perfect. '
                 'But 12 appears so often that each individual match is weak.',
    },
]


# ── Institutional fact pool for Monte Carlo ──────────────────────
# Realistic numbers that appear in law, government, calendar, history.

INSTITUTIONAL_NUMBERS = [
    # Jury sizes historically used
    6, 8, 12,
    # Court sizes
    3, 5, 7, 9, 11, 13, 15,
    # Government branches
    2, 3, 4, 5,
    # International org member counts
    5, 6, 7, 8, 10, 12, 15, 20, 27, 28, 30, 31, 50, 51, 193,
    # Calendar numbers
    4, 7, 12, 24, 28, 29, 30, 31, 52, 60, 90, 120, 180, 360, 365,
    # Historical cycle lengths (years)
    4, 8, 10, 20, 25, 30, 40, 50, 55, 60, 80, 100,
    # Number bases historically used
    5, 10, 12, 16, 20, 60,
    # Trade counting units
    6, 12, 20, 60, 100, 144, 360,
    # Common small numbers in institutions
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
]

INSTITUTIONAL_NUMBERS_UNIQUE = sorted(set(INSTITUTIONAL_NUMBERS))


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
    outputs.add(s)       # sigma
    outputs.add(t)       # tau
    outputs.add(p)       # phi

    # Divisors
    for dd in d:
        outputs.add(dd)

    # Products of key functions
    funcs = [n, s, t, p]
    for i, a in enumerate(funcs):
        for b in funcs[i:]:
            outputs.add(a * b)

    # n * 10 (sexagesimal connection)
    outputs.add(n * 10)

    # sigma^2
    outputs.add(s * s)

    return outputs


def count_matches(n, numbers):
    """Count how many institutional numbers match n's arithmetic outputs."""
    outputs = n_arithmetic_outputs(n)
    matches = 0
    matched_items = []
    for c in numbers:
        if c in outputs:
            matches += 1
            matched_items.append(c)
    return matches, matched_items


def independence_analysis():
    """Analyze which of the 20 claims are truly independent."""
    print("\n" + "=" * 70)
    print("  INDEPENDENCE ANALYSIS: 20 Institutional Hypotheses")
    print("=" * 70)

    groups = {}
    for c in CLAIMS:
        g = c['independence_group']
        if g not in groups:
            groups[g] = []
        groups[g].append(c['id'])

    print(f"\n  20 claims collapse into {len(groups)} independence groups:\n")
    for g, members in sorted(groups.items()):
        print(f"    {g:25s} : {', '.join(members)}")

    # Count match types
    exact = sum(1 for c in CLAIMS if c['match'] == 'exact')
    approx = sum(1 for c in CLAIMS if c['match'] == 'approximate')
    no_match = sum(1 for c in CLAIMS if c['match'] == 'no_match')
    ad_hoc = sum(1 for c in CLAIMS if c['match'] == 'ad_hoc')

    print(f"\n  Match types:")
    print(f"    Exact:        {exact}")
    print(f"    Approximate:  {approx}")
    print(f"    Ad hoc (-1):  {ad_hoc}")
    print(f"    No match:     {no_match}")
    print(f"\n  Independent groups: {len(groups)}")
    print(f"  Redundant claims:  {20 - len(groups)}")

    return groups


def monte_carlo_test(n_trials=10000, seed=42):
    """Monte Carlo: compare n=6 match count to random numbers n=2..100."""
    print("\n" + "=" * 70)
    print("  TEXAS SHARPSHOOTER: Monte Carlo Test")
    print("=" * 70)

    # Actual matches for n=6
    real_matches, real_items = count_matches(6, INSTITUTIONAL_NUMBERS_UNIQUE)
    print(f"\n  n=6 matches {real_matches}/{len(INSTITUTIONAL_NUMBERS_UNIQUE)} institutional numbers")
    print(f"\n  Matched items: {real_items}")

    # Test all n=2..100
    print(f"\n  Comparison with n=2..100:")
    print(f"  {'n':>4s}  {'matches':>7s}  {'outputs':>7s}")
    print(f"  {'─'*4}  {'─'*7}  {'─'*7}")

    all_counts = []
    for n in range(2, 101):
        m, _ = count_matches(n, INSTITUTIONAL_NUMBERS_UNIQUE)
        all_counts.append(m)
        if m >= real_matches or n in [6, 12, 28, 496]:
            tag = " <== PERFECT" if n in [6, 28, 496] else ""
            tag += " ***" if m >= real_matches else ""
            print(f"  {n:4d}  {m:7d}  {len(n_arithmetic_outputs(n)):7d}{tag}")

    avg = sum(all_counts) / len(all_counts)
    std = (sum((x - avg)**2 for x in all_counts) / len(all_counts)) ** 0.5
    rank = sum(1 for x in all_counts if x >= real_matches)

    print(f"\n  ── Statistics ──")
    print(f"  n=6 matches:     {real_matches}")
    print(f"  Average (n=2-100): {avg:.1f} +/- {std:.1f}")
    print(f"  n=6 Z-score:     {(real_matches - avg) / std:.2f}" if std > 0 else "  Z-score: N/A")
    print(f"  Rank (out of 99): {rank} numbers match >= {real_matches}")
    print(f"  p-value (rank):  {rank/99:.4f}")

    # Random number Monte Carlo
    print(f"\n  ── Monte Carlo with {n_trials} random 'special numbers' ──")
    rng = random.Random(seed)
    random_counts = []
    for _ in range(n_trials):
        n = rng.randint(2, 200)
        m, _ = count_matches(n, INSTITUTIONAL_NUMBERS_UNIQUE)
        random_counts.append(m)

    mc_avg = sum(random_counts) / len(random_counts)
    mc_std = (sum((x - mc_avg)**2 for x in random_counts) / len(random_counts)) ** 0.5
    mc_exceed = sum(1 for x in random_counts if x >= real_matches)

    print(f"  Random average:  {mc_avg:.1f} +/- {mc_std:.1f}")
    print(f"  n=6 matches:     {real_matches}")
    print(f"  Random >= n=6:   {mc_exceed}/{n_trials} ({mc_exceed/n_trials*100:.1f}%)")
    print(f"  MC p-value:      {mc_exceed/n_trials:.4f}" if mc_exceed > 0 else f"  MC p-value:      < {1/n_trials:.6f}")

    return real_matches, avg, std, mc_exceed / n_trials


def grade_hypotheses():
    """Grade each hypothesis honestly."""
    print("\n" + "=" * 70)
    print("  GRADING: 20 Institutional Hypotheses")
    print("=" * 70)

    grades = {
        'green': [],   # Exact match, arithmetically proven
        'orange': [],  # Approximate but structurally interesting
        'white': [],   # Correct but trivial/coincidence
        'black': [],   # Wrong, ad hoc, or no match
    }

    GRADE_MAP = {
        # H-INST-001: jury=12=sigma(6). Exact but 12 is common.
        'H-INST-001': ('green', '12 = sigma(6) exact. But 12 is culturally ubiquitous.'),
        'H-INST-002': ('green', '6-person jury exists. n=6 exact.'),
        'H-INST-003': ('green', 'Original SCOTUS = 6. Historical fact, n=6 exact.'),
        'H-INST-004': ('white', 'Legal tradition count varies 3-7 depending on taxonomy. Cherry-picked to 6.'),
        'H-INST-005': ('black', 'sigma(6)+tau(6)-1 = 15 is ad hoc. The -1 is a correction flag.'),
        'H-INST-006': ('white', '3 branches. 3 divides 6 but 3 is trivially common.'),
        'H-INST-007': ('white', '2 chambers = phi(6). But 2 is the most common small number.'),
        'H-INST-008': ('green', 'G6 original grouping = 6. Historical fact.'),
        'H-INST-009': ('green', 'NATO 12 founders = sigma(6). Historical fact.'),
        'H-INST-010': ('green', 'EU 6 founders. Historical fact, n=6 exact.'),
        'H-INST-011': ('green', '12 months = sigma(6). But astronomical origin (lunar cycles).'),
        'H-INST-012': ('white', '24 hours = sigma(6)*phi(6) = 12*2. Derived from 12, not independent.'),
        'H-INST-013': ('orange', '60 = 6*10. Babylonian base-60 chosen for divisor richness of 6.'),
        'H-INST-014': ('black', '7 days/week. No n=6 match. Honest failure.'),
        'H-INST-015': ('white', '4 seasons = tau(6). But tau(n)=4 for any semiprime.'),
        'H-INST-016': ('black', 'Kondratiev ~40-60 years. Range too wide, theory disputed.'),
        'H-INST-017': ('white', 'Strauss-Howe 4 turnings = tau(6). Pop-history, 4 is common.'),
        'H-INST-018': ('black', 'Tainter collapse: no numerical match at all.'),
        'H-INST-019': ('green', 'Sexagesimal base-60 = 6*10. Same as H-INST-013 (not independent).'),
        'H-INST-020': ('green', 'Dozen=12=sigma(6) in trade. Same 12 as months (weak independence).'),
    }

    for claim in CLAIMS:
        cid = claim['id']
        grade, reason = GRADE_MAP[cid]
        grades[grade].append((cid, reason))

    emoji_map = {'green': '[GREEN]', 'orange': '[ORANGE]', 'white': '[WHITE]', 'black': '[BLACK]'}
    for grade_name in ['green', 'orange', 'white', 'black']:
        print(f"\n  {emoji_map[grade_name]} ({len(grades[grade_name])} hypotheses):")
        for cid, reason in grades[grade_name]:
            print(f"    {cid}: {reason}")

    print(f"\n  ── Summary ──")
    print(f"  GREEN  (exact, real):   {len(grades['green'])}")
    print(f"  ORANGE (structural):    {len(grades['orange'])}")
    print(f"  WHITE  (trivial/coinc): {len(grades['white'])}")
    print(f"  BLACK  (wrong/ad hoc):  {len(grades['black'])}")

    return grades


def smallnum_warning():
    """Strong Law of Small Numbers check."""
    print("\n" + "=" * 70)
    print("  STRONG LAW OF SMALL NUMBERS WARNING")
    print("=" * 70)
    print("""
  Most matched values are SMALL numbers: 2, 3, 4, 6, 12, 24, 60.
  Small numbers appear everywhere. The chance of "matching" is inflated.

  Key concern: {2, 3, 4, 6, 12} are the divisors of 12 (and 6).
  These numbers are DESIGNED to appear in human systems because
  humans CHOSE bases 6, 12, 60 for their nice divisibility.

  This is NOT evidence that institutions encode n=6 unconsciously.
  It IS evidence that humans prefer highly-divisible numbers,
  and 6 being perfect is WHY 6 and 12 became culturally important.

  Causal direction: 6 is perfect -> 6/12/60 are useful -> humans adopt them
  NOT: institutions -> mysteriously encode n=6
    """)


def generalization_test():
    """Does this work for perfect number 28?"""
    print("\n" + "=" * 70)
    print("  GENERALIZATION: Perfect number 28")
    print("=" * 70)

    m6, items6 = count_matches(6, INSTITUTIONAL_NUMBERS_UNIQUE)
    m28, items28 = count_matches(28, INSTITUTIONAL_NUMBERS_UNIQUE)

    print(f"\n  n=6  matches: {m6}  items: {items6}")
    print(f"  n=28 matches: {m28} items: {items28}")

    # sigma(28) = 56, tau(28) = 6, phi(28) = 12
    print(f"\n  n=28 properties: sigma={sigma(28)}, tau={tau(28)}, phi={phi(28)}")
    print(f"  n=6  properties: sigma={sigma(6)}, tau={tau(6)}, phi={phi(6)}")

    if m28 < m6:
        print(f"\n  n=28 matches FEWER ({m28} < {m6}). Pattern does NOT generalize.")
        print(f"  This suggests the matches are specific to 6's cultural role,")
        print(f"  not a universal perfect-number property.")
    else:
        print(f"\n  n=28 matches similarly ({m28} vs {m6}). Pattern may generalize.")

    return m6, m28


def main():
    parser = argparse.ArgumentParser(description='Texas Sharpshooter: Institutional Hypotheses')
    parser.add_argument('--trials', type=int, default=10000, help='Monte Carlo trials')
    args = parser.parse_args()

    print("=" * 70)
    print("  VERIFICATION: 20 Institutional / Law / History Hypotheses")
    print("  Framework: n=6, sigma(6)=12, tau(6)=4, phi(6)=2")
    print("=" * 70)

    groups = independence_analysis()
    real_matches, avg, std, mc_pval = monte_carlo_test(args.trials)
    grades = grade_hypotheses()
    smallnum_warning()
    m6, m28 = generalization_test()

    # ── Final Verdict ──
    print("\n" + "=" * 70)
    print("  FINAL VERDICT")
    print("=" * 70)

    n_green = len(grades['green'])
    n_orange = len(grades['orange'])
    n_white = len(grades['white'])
    n_black = len(grades['black'])
    n_groups = len(groups)

    print(f"""
  Claims:        20
  Independent:   {n_groups} groups
  Grades:        {n_green} GREEN, {n_orange} ORANGE, {n_white} WHITE, {n_black} BLACK

  Texas Sharpshooter:
    n=6 matches:   {real_matches} institutional numbers
    Random avg:    {avg:.1f} +/- {std:.1f}
    MC p-value:    {mc_pval:.4f}

  Generalization: n=28 matches {m28} (vs n=6: {m6})

  INTERPRETATION:
    The GREEN matches (jury=12, SCOTUS=6, EU=6, NATO=12, months=12, etc.)
    are ARITHMETICALLY CORRECT. These are real historical facts.

    However, the causal explanation is CULTURAL, not mathematical:
    - Humans adopted base-12/60 because 6 is perfect (many divisors)
    - Institutions inherited these cultural preferences
    - 6 and 12 appear in human systems BECAUSE humans like them

    The one genuinely interesting connection is SEXAGESIMAL (base-60):
    Babylonians chose 60 explicitly for its divisibility, and this
    traces to 6 being the smallest perfect number with factor richness.

    Overall: PATTERN REAL but CAUSALLY MUNDANE.
    Not mysterious. Not Golden Zone dependent.
    Just: humans like the number 6 because it is mathematically nice.
    """)


if __name__ == '__main__':
    main()
