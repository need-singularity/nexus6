#!/usr/bin/env python3
"""H-PSY-001 to H-PSY-025: Psychology Hypothesis Verification + Texas Sharpshooter

Verifies all 25 psychology/emotion/cognition hypotheses against n=6 framework.
Runs Monte Carlo Texas Sharpshooter test to assess whether the number of
matches exceeds chance expectation.

Usage:
    PYTHONPATH=. python3 verify/verify_psy_001_025.py
    PYTHONPATH=. python3 verify/verify_psy_001_025.py --trials 50000
"""

import math
import random
import argparse
from collections import Counter

# ── n=6 arithmetic ──────────────────────────────────────────────────

def divisors(n):
    return [d for d in range(1, n + 1) if n % d == 0]

def sigma(n):
    return sum(divisors(n))

def tau(n):
    return len(divisors(n))

def phi(n):
    return sum(1 for k in range(1, n + 1) if math.gcd(k, n) == 1)

# n=6 constants
N = 6
SIGMA_6 = sigma(6)   # 12
TAU_6 = tau(6)        # 4
PHI_6 = phi(6)        # 2
INV_E = 1 / math.e    # 0.36788...
GZ_UPPER = 0.5
GZ_LOWER = 0.5 - math.log(4/3)  # 0.21227...
GZ_CENTER = INV_E
META_FP = 1/3

# ── Target values from n=6 ─────────────────────────────────────────
# These are the "special" numbers the model predicts
N6_TARGETS = {
    'n': 6,
    'sigma': 12,
    'tau': 4,
    'phi': 2,
    '1/e': INV_E,
    '1/3': META_FP,
    '2/3': 2/3,
    'gz_upper': GZ_UPPER,
    'gz_lower': GZ_LOWER,
    'divisors': {1, 2, 3, 6},
    'sigma-tau': 8,
    'tau*phi': 8,
    '5/6': 5/6,
    '1/6': 1/6,
}

# ── 25 Psychology claims ───────────────────────────────────────────

CLAIMS = [
    # A. Basic Emotions
    {
        'id': 'H-PSY-001', 'cat': 'Emotions',
        'desc': "Ekman's 6 basic emotions = n=6",
        'psych_value': 6, 'target': 'n', 'target_value': 6,
        'match_type': 'exact_count',
        'honest_note': 'Small number, researcher-defined taxonomy',
    },
    {
        'id': 'H-PSY-002', 'cat': 'Emotions',
        'desc': "Plutchik's 4 emotion pairs = tau(6)",
        'psych_value': 4, 'target': 'tau', 'target_value': 4,
        'match_type': 'exact_count',
        'honest_note': '4 pairs from 8 items is trivial',
    },
    {
        'id': 'H-PSY-003', 'cat': 'Emotions',
        'desc': "Valence-Arousal 2 dimensions = phi(6)",
        'psych_value': 2, 'target': 'phi', 'target_value': 2,
        'match_type': 'exact_count',
        'honest_note': 'Any dichotomy = 2, trivially common',
    },
    {
        'id': 'H-PSY-004', 'cat': 'Emotions',
        'desc': "FACS ~12 core AUs = sigma(6)",
        'psych_value': 12, 'target': 'sigma', 'target_value': 12,
        'match_type': 'approximate_count',
        'honest_note': '12 is cherry-picked; literature says 12-20',
    },
    {
        'id': 'H-PSY-005', 'cat': 'Emotions',
        'desc': "Fore avg error 21.8% ~ GZ lower (21.2%)",
        'psych_value': 0.218, 'target': 'gz_lower', 'target_value': GZ_LOWER,
        'match_type': 'approximate_ratio',
        'honest_note': 'Post-hoc, sample-dependent',
    },
    # B. Memory & Attention
    {
        'id': 'H-PSY-006', 'cat': 'Memory',
        'desc': "Cowan's 4 chunks = tau(6)",
        'psych_value': 4, 'target': 'tau', 'target_value': 4,
        'match_type': 'exact_count',
        'honest_note': 'Robust empirical finding, but small number',
    },
    {
        'id': 'H-PSY-007', 'cat': 'Memory',
        'desc': "Ebbinghaus 1/e in forgetting curve",
        'psych_value': INV_E, 'target': '1/e', 'target_value': INV_E,
        'match_type': 'trivial_math',
        'honest_note': '1/e appears in ALL exponential decays, not n=6 specific',
    },
    {
        'id': 'H-PSY-008', 'cat': 'Memory',
        'desc': "Spacing effect ratio = 1/3",
        'psych_value': 0.15, 'target': '1/3', 'target_value': META_FP,
        'match_type': 'refuted',
        'honest_note': 'Actual ratio ~0.10-0.20, NOT 1/3. REFUTED.',
    },
    {
        'id': 'H-PSY-009', 'cat': 'Attention',
        'desc': "Attentional blink ratio in GZ",
        'psych_value': 0.545, 'target': 'gz_upper', 'target_value': GZ_UPPER,
        'match_type': 'approximate_ratio',
        'honest_note': 'Post-hoc ratio construction',
    },
    {
        'id': 'H-PSY-010', 'cat': 'Cognition',
        'desc': "Dual process 2 systems = phi(6)",
        'psych_value': 2, 'target': 'phi', 'target_value': 2,
        'match_type': 'exact_count',
        'honest_note': 'Trivially binary',
    },
    # C. Development & Personality
    {
        'id': 'H-PSY-011', 'cat': 'Development',
        'desc': "Erikson 8 stages = sigma(6)-tau(6)",
        'psych_value': 8, 'target': 'sigma-tau', 'target_value': 8,
        'match_type': 'constructed',
        'honest_note': '8 constructible many ways from {12,4,2,6}',
    },
    {
        'id': 'H-PSY-012', 'cat': 'Development',
        'desc': "Piaget 4 stages = tau(6)",
        'psych_value': 4, 'target': 'tau', 'target_value': 4,
        'match_type': 'exact_count',
        'honest_note': '4 is common developmental model count',
    },
    {
        'id': 'H-PSY-013', 'cat': 'Personality',
        'desc': "HEXACO 6 factors = n=6",
        'psych_value': 6, 'target': 'n', 'target_value': 6,
        'match_type': 'exact_count',
        'honest_note': 'Empirically derived via factor analysis, stronger than taxonomy',
    },
    {
        'id': 'H-PSY-014', 'cat': 'Development',
        'desc': "Kohlberg 6 stages = 3 levels x 2 = n=6",
        'psych_value': 6, 'target': 'n', 'target_value': 6,
        'match_type': 'structural',
        'honest_note': '6=3x2 structural match, but Stage 6 debated',
    },
    {
        'id': 'H-PSY-015', 'cat': 'Development',
        'desc': "Maslow 5 or 8 levels",
        'psych_value': 5, 'target': 'n', 'target_value': 6,
        'match_type': 'no_match',
        'honest_note': 'Neither 5 nor 8 maps cleanly',
    },
    # D. Perception & Psychophysics
    {
        'id': 'H-PSY-016', 'cat': 'Perception',
        'desc': "Weber fractions for taste/smell in GZ",
        'psych_value': 0.20, 'target': 'gz_lower', 'target_value': GZ_LOWER,
        'match_type': 'approximate_ratio',
        'honest_note': 'Most modalities outside GZ; cherry-picked',
    },
    {
        'id': 'H-PSY-017', 'cat': 'Psychophysics',
        'desc': "Stevens brightness=0.33~1/3, loudness=0.67~2/3",
        'psych_value': 0.33, 'target': '1/3', 'target_value': META_FP,
        'match_type': 'approximate_ratio',
        'honest_note': 'Scale-dependent exponents; two most-studied match',
    },
    {
        'id': 'H-PSY-018', 'cat': 'Perception',
        'desc': "3 cone types = divisor of 6",
        'psych_value': 3, 'target': 'divisor', 'target_value': 3,
        'match_type': 'exact_count',
        'honest_note': '3 is trivially common in biology',
    },
    {
        'id': 'H-PSY-019', 'cat': 'Perception',
        'desc': "6 Gestalt principles = n=6",
        'psych_value': 6, 'target': 'n', 'target_value': 6,
        'match_type': 'approximate_count',
        'honest_note': 'Count varies 6-10 by source',
    },
    {
        'id': 'H-PSY-020', 'cat': 'Perception',
        'desc': "2 depth cue categories = phi(6)",
        'psych_value': 2, 'target': 'phi', 'target_value': 2,
        'match_type': 'exact_count',
        'honest_note': 'Trivially binary (monocular vs binocular)',
    },
    # E. Social Psychology
    {
        'id': 'H-PSY-021', 'cat': 'Social',
        'desc': "Six degrees of separation = n=6",
        'psych_value': 5.5, 'target': 'n', 'target_value': 6,
        'match_type': 'approximate_count',
        'honest_note': 'Approximate (~5.5), decreasing with internet',
    },
    {
        'id': 'H-PSY-022', 'cat': 'Social',
        'desc': "Dunbar 150 = sigma(6) * ?",
        'psych_value': 150, 'target': 'sigma', 'target_value': 12,
        'match_type': 'refuted',
        'honest_note': '150/12=12.5, no clean mapping. REFUTED.',
    },
    {
        'id': 'H-PSY-023', 'cat': 'Social',
        'desc': "Neocortex ratio 4.1 ~ tau(6)=4",
        'psych_value': 4.1, 'target': 'tau', 'target_value': 4,
        'match_type': 'approximate_ratio',
        'honest_note': 'Large measurement uncertainty (3.2-4.6)',
    },
    {
        'id': 'H-PSY-024', 'cat': 'Social',
        'desc': "Asch conformity peaks at 3-4, rate~1/3",
        'psych_value': 0.32, 'target': '1/3', 'target_value': META_FP,
        'match_type': 'approximate_ratio',
        'honest_note': 'Multi-level match (group size + rate)',
    },
    {
        'id': 'H-PSY-025', 'cat': 'Social',
        'desc': "Bystander 31/85=0.365 ~ 1/e",
        'psych_value': 31/85, 'target': '1/e', 'target_value': INV_E,
        'match_type': 'approximate_ratio',
        'honest_note': 'Numerically striking (0.3% error) but single study',
    },
]


def verify_single(claim):
    """Verify a single claim. Returns (pass, grade, detail)."""
    cid = claim['id']
    mt = claim['match_type']
    pv = claim['psych_value']
    tv = claim['target_value']

    if mt == 'refuted':
        return False, 'REFUTED', f"{pv} does not match {tv}"

    if mt == 'no_match':
        return False, 'NO_MATCH', f"{pv} != {tv}"

    if mt == 'trivial_math':
        return True, 'TRIVIAL', f"1/e in any exponential — not n=6 specific"

    if mt == 'exact_count':
        match = (pv == tv) or (isinstance(tv, set) and pv in tv)
        if match:
            # Check if trivially small
            if pv <= 3:
                return True, 'TRIVIAL_MATCH', f"{pv} = {claim['target']} but trivially small"
            else:
                return True, 'EXACT', f"{pv} = {claim['target']}"
        return False, 'MISMATCH', f"{pv} != {tv}"

    if mt == 'approximate_count':
        if isinstance(tv, (int, float)):
            err = abs(pv - tv)
            pct = err / max(abs(tv), 1e-15) * 100
            if pct < 10:
                return True, 'APPROX', f"{pv} ~ {tv} (err {pct:.1f}%)"
            return False, 'TOO_FAR', f"{pv} vs {tv} (err {pct:.1f}%)"

    if mt == 'approximate_ratio':
        if isinstance(tv, (int, float)):
            err = abs(pv - tv)
            pct = err / max(abs(tv), 1e-15) * 100
            if pct < 10:
                return True, 'APPROX', f"{pv:.4f} ~ {tv:.4f} (err {pct:.1f}%)"
            elif pct < 20:
                return True, 'WEAK_APPROX', f"{pv:.4f} ~ {tv:.4f} (err {pct:.1f}%)"
            return False, 'TOO_FAR', f"{pv:.4f} vs {tv:.4f} (err {pct:.1f}%)"

    if mt in ('constructed', 'structural'):
        return True, 'STRUCTURAL', f"{pv} = {claim['target']} (post-hoc construction)"

    return False, 'UNKNOWN', f"Unknown match type: {mt}"


def grade_claim(claim, passed, grade_str):
    """Assign emoji grade. STRICT grading — penalize trivial matches and cherry-picking."""
    mt = claim['match_type']
    cid = claim['id']
    if mt == 'refuted':
        return '⬛'
    if mt == 'no_match':
        return '⚪'
    if mt == 'trivial_math':
        return '⚪'
    if grade_str == 'TRIVIAL_MATCH':
        return '⚪'
    if grade_str in ('STRUCTURAL', 'CONSTRUCTED'):
        return '⚪'
    if grade_str == 'WEAK_APPROX':
        return '⚪'

    # Specific overrides for honest grading
    # Plutchik 4 pairs: trivial (4 pairs from 8 items)
    if cid == 'H-PSY-002':
        return '⚪'
    # FACS 12: cherry-picked from 12-20 range
    if cid == 'H-PSY-004':
        return '⚪'
    # Fore error: post-hoc, sample-dependent
    if cid == 'H-PSY-005':
        return '⚪'
    # Piaget 4: common count for developmental models
    if cid == 'H-PSY-012':
        return '⚪'
    # Gestalt 6: count varies 6-10 by source
    if cid == 'H-PSY-019':
        return '⚪'
    # Neocortex ratio: huge measurement uncertainty
    if cid == 'H-PSY-023':
        return '⚪'
    # Six degrees: approximate and decreasing
    if cid == 'H-PSY-021':
        return '🟧'
    # AB ratio: forced
    if cid == 'H-PSY-009':
        return '⚪'

    if grade_str == 'EXACT' and claim['psych_value'] in (4, 6):
        return '🟧'
    if grade_str == 'APPROX':
        pv = claim['psych_value']
        tv = claim['target_value']
        if isinstance(tv, (int, float)):
            err = abs(pv - tv) / max(abs(tv), 1e-15)
            if err < 0.05:
                return '🟧'
            return '⚪'
    if not passed:
        return '⚪' if mt != 'refuted' else '⬛'
    return '⚪'


# ── Texas Sharpshooter Monte Carlo ─────────────────────────────────

def count_matches_random(targets, n_claims, rng):
    """
    For each claim, generate a random psychology value and check if
    it matches any n=6 target by chance.

    For count-type claims (integers): random int from 2-12.
    For ratio-type claims (floats): random float from 0 to 1.
    """
    matches = 0
    for i in range(n_claims):
        claim_type = rng.choice(['count', 'ratio'])
        if claim_type == 'count':
            val = rng.randint(2, 12)
            # Check against integer targets
            int_targets = {6, 12, 4, 2, 8, 3, 1}  # n, sigma, tau, phi, sigma-tau, divisors
            if val in int_targets:
                matches += 1
        else:
            val = rng.random()
            # Check against ratio targets (within 5% relative error)
            ratio_targets = [INV_E, META_FP, 2/3, GZ_UPPER, GZ_LOWER, 5/6, 1/6]
            for t in ratio_targets:
                if abs(val - t) / max(abs(t), 1e-15) < 0.05:
                    matches += 1
                    break
    return matches


def texas_sharpshooter(n_trials=10000, seed=42):
    """Run Monte Carlo Texas Sharpshooter test."""
    rng = random.Random(seed)

    # Count our actual matches
    actual_matches = 0
    for c in CLAIMS:
        passed, grade_str, _ = verify_single(c)
        g = grade_claim(c, passed, grade_str)
        if g == '🟧':
            actual_matches += 1

    # Monte Carlo
    random_counts = []
    for _ in range(n_trials):
        mc = count_matches_random(N6_TARGETS, len(CLAIMS), rng)
        random_counts.append(mc)

    avg = sum(random_counts) / len(random_counts)
    std = (sum((x - avg) ** 2 for x in random_counts) / len(random_counts)) ** 0.5
    p_value = sum(1 for x in random_counts if x >= actual_matches) / n_trials

    return actual_matches, avg, std, p_value, random_counts


# ── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Verify H-PSY-001 to H-PSY-025')
    parser.add_argument('--trials', type=int, default=10000, help='Monte Carlo trials')
    args = parser.parse_args()

    print("=" * 70)
    print("H-PSY-001 to H-PSY-025: Psychology Hypothesis Verification")
    print("=" * 70)
    print()
    print(f"n=6 constants: sigma={SIGMA_6}, tau={TAU_6}, phi={PHI_6}")
    print(f"Golden Zone: [{GZ_LOWER:.4f}, {GZ_UPPER:.4f}], center=1/e={INV_E:.4f}")
    print(f"Meta fixed point: 1/3 = {META_FP:.4f}")
    print()

    # ── Verify each claim ──────────────────────────────────────────
    print("-" * 70)
    print(f"{'ID':<12} {'Grade':<6} {'Status':<15} {'Detail'}")
    print("-" * 70)

    grades = Counter()
    for c in CLAIMS:
        passed, grade_str, detail = verify_single(c)
        emoji = grade_claim(c, passed, grade_str)
        grades[emoji] += 1
        print(f"{c['id']:<12} {emoji:<6} {grade_str:<15} {detail}")

    print("-" * 70)
    print()

    # ── Grade summary ──────────────────────────────────────────────
    print("GRADE SUMMARY")
    print(f"  🟧 Weak evidence (structural): {grades.get('🟧', 0)}")
    print(f"  ⚪ Coincidence / trivial:       {grades.get('⚪', 0)}")
    print(f"  ⬛ Refuted:                     {grades.get('⬛', 0)}")
    print(f"  🟩 Proven:                      {grades.get('🟩', 0)}")
    total = sum(grades.values())
    print(f"  Total:                          {total}")
    print()

    # ── Texas Sharpshooter ─────────────────────────────────────────
    print("=" * 70)
    print(f"TEXAS SHARPSHOOTER TEST ({args.trials:,} trials)")
    print("=" * 70)
    print()

    actual, avg, std, p_val, dist = texas_sharpshooter(args.trials)

    print(f"  Actual 🟧 matches:   {actual}")
    print(f"  Random average:      {avg:.1f} +/- {std:.1f}")
    print(f"  Z-score:             {(actual - avg) / max(std, 1e-15):.2f}")
    print(f"  p-value:             {p_val:.4f}")
    print()

    # Histogram
    ctr = Counter(dist)
    max_count = max(ctr.values())
    print("  Distribution of random matches:")
    for k in sorted(ctr.keys()):
        bar_len = int(ctr[k] / max_count * 40)
        marker = " <-- ACTUAL" if k == actual else ""
        print(f"    {k:2d} | {'#' * bar_len} ({ctr[k]}){marker}")
    print()

    # ── Interpretation ─────────────────────────────────────────────
    if p_val < 0.01:
        verdict = "SIGNIFICANT (p < 0.01) — matches exceed chance"
    elif p_val < 0.05:
        verdict = "MARGINAL (p < 0.05) — weak evidence above chance"
    else:
        verdict = "NOT SIGNIFICANT (p >= 0.05) — consistent with chance"

    print(f"  VERDICT: {verdict}")
    print()

    # ── Bonferroni correction ──────────────────────────────────────
    bonf_p = min(p_val * 25, 1.0)
    print(f"  Bonferroni-corrected p-value (25 tests): {bonf_p:.4f}")
    if bonf_p < 0.05:
        print("  After Bonferroni: STILL SIGNIFICANT")
    else:
        print("  After Bonferroni: NOT SIGNIFICANT")
    print()

    # ── Per-claim honest assessment ────────────────────────────────
    print("=" * 70)
    print("HONEST ASSESSMENT (per claim)")
    print("=" * 70)
    for c in CLAIMS:
        passed, grade_str, _ = verify_single(c)
        emoji = grade_claim(c, passed, grade_str)
        print(f"  {emoji} {c['id']}: {c['desc']}")
        print(f"     Note: {c['honest_note']}")
    print()

    # ── Top candidates ─────────────────────────────────────────────
    print("=" * 70)
    print("TOP CANDIDATES (by quality of match)")
    print("=" * 70)
    ranked = [
        ("H-PSY-025", "Bystander 31/85 = 0.365 ~ 1/e", "0.3% error, single study"),
        ("H-PSY-017", "Stevens brightness=1/3, loudness=2/3", "Classic psychophysics, scale-dependent"),
        ("H-PSY-024", "Asch conformity at 3-4, rate~1/3", "Multi-level match"),
        ("H-PSY-013", "HEXACO 6 factors = n", "Empirically derived from factor analysis"),
        ("H-PSY-006", "Cowan's 4 chunks = tau(6)", "Robust empirical, but small number"),
    ]
    for i, (cid, desc, note) in enumerate(ranked, 1):
        print(f"  {i}. {cid}: {desc}")
        print(f"     {note}")
    print()
    print("=" * 70)
    print("DONE")


if __name__ == '__main__':
    main()
