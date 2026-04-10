#!/usr/bin/env python3
"""
Verify Sports/Biomechanics Hypotheses H-SPORT-001 through H-SPORT-020.

Each hypothesis is checked against known anatomy/sports/biomechanics data.
Grades:
  GREEN  = Exact equation, mathematically proven
  ORANGE_STAR = Numerically correct + structurally non-trivial (p < 0.01)
  ORANGE = Numerically correct + weak structural evidence (p < 0.05)
  WHITE  = Arithmetically correct but likely coincidental (p > 0.05)
  BLACK  = Arithmetically wrong or factually incorrect

Run: PYTHONPATH=. python3 verify/verify_sport_biomechanics.py
"""
import math
import random
import sys

# ── Number-theoretic helpers for perfect number 6 ──
def sigma(n):
    """Sum of divisors."""
    return sum(d for d in range(1, n+1) if n % d == 0)

def sigma_neg1(n):
    """Sum of reciprocals of divisors."""
    return sum(1.0/d for d in range(1, n+1) if n % d == 0)

def tau(n):
    """Number of divisors."""
    return sum(1 for d in range(1, n+1) if n % d == 0)

def euler_phi(n):
    """Euler totient."""
    return sum(1 for k in range(1, n+1) if math.gcd(k, n) == 1)

def is_perfect(n):
    """Check if n is a perfect number (sigma(n) = 2n)."""
    return sigma(n) == 2 * n

def divisors(n):
    return [d for d in range(1, n+1) if n % d == 0]

# ── Golden Zone constants ──
GZ_UPPER = 0.5
GZ_LOWER = 0.5 - math.log(4/3)
GZ_CENTER = 1/math.e
GZ_WIDTH = math.log(4/3)

# ── Texas Sharpshooter ──
def texas_sharpshooter_p(observed_matches, total_tests, n_sims=100000):
    """
    Monte Carlo p-value: probability of getting >= observed_matches
    by random chance from a pool of common integers.
    Pool: integers 1-30 (reasonable range for body/sport counts).
    Targets: {6, 12, 4, 2, 1, 2, 3} = divisors of 6 + sigma(6) + phi(6) + tau(6).
    """
    targets = {1, 2, 3, 4, 6, 12}  # divisors of 6 + sigma(6)
    pool = list(range(1, 31))
    count_ge = 0
    for _ in range(n_sims):
        picks = random.choices(pool, k=total_tests)
        matches = sum(1 for p in picks if p in targets)
        if matches >= observed_matches:
            count_ge += 1
    return count_ge / n_sims

# ── Results tracking ──
results = []

def grade(hid, emoji, passed, desc, detail=""):
    results.append((hid, emoji, passed, desc, detail))
    status = "PASS" if passed else "FAIL"
    print(f"  {emoji} {hid}: {status} -- {desc}")
    if detail:
        for line in detail.strip().split("\n"):
            print(f"       {line}")
    print()

# =============================================================================
print("=" * 72)
print("  SPORTS/BIOMECHANICS HYPOTHESES VERIFICATION (H-SPORT-001 to 020)")
print("=" * 72)
print()

# ═══════════════════════════════════════════════════════════════
# A. HUMAN BODY STRUCTURE (001-005)
# ═══════════════════════════════════════════════════════════════
print("== A. HUMAN BODY STRUCTURE ==\n")

# H-SPORT-001: Cervical vertebrae
# FACT: ALL mammals have 7 cervical vertebrae (except manatee=6, sloth=6-9).
# Claim: C1-C6 mobile, C7 transitional => "functional 6"
# VERIFICATION: C7 (vertebra prominens) IS mobile -- it flexes/extends.
# C7 is NOT just transitional. It has a spinous process but full mobility.
# The "functional 6" claim is a stretch.
c_vert = 7
c_mobile_claim = 6
# In reality: C1 (atlas) - rotation, C2 (axis) - rotation, C3-C7 all flex/extend
# C7 is fully mobile, just has a longer spinous process
c7_mobile = True  # C7 IS mobile
grade("H-SPORT-001", "WHITE" if c7_mobile else "ORANGE",
      not c7_mobile,  # Fails because C7 IS mobile
      f"Cervical vertebrae: 7 in mammals, claim 'functional 6' -- C7 IS mobile",
      f"Cervical count = {c_vert}, not 6.\n"
      f"C7 (vertebra prominens) has longer spinous process but full mobility.\n"
      f"C1-C7 all participate in neck movement. 'Functional 6' is ad hoc.\n"
      f"Strong Law of Small Numbers: single-digit anatomy count, easy to force-fit.\n"
      f"Grade: WHITE -- factually the count is 7, not 6.")

# H-SPORT-002: Thoracic vertebrae = 12 = sigma(6)
# FACT: Humans have 12 thoracic vertebrae. sigma(6) = 1+2+3+6 = 12.
s6 = sigma(6)
thoracic = 12
match_002 = (thoracic == s6)
# But: 12 is extremely common (months, hours, zodiac signs...).
# How many integers 1-30 equal 12? Just 1 out of 30.
# But 12 appears in MANY contexts -- selection bias.
grade("H-SPORT-002", "WHITE",
      match_002,
      f"Thoracic vertebrae = {thoracic} = sigma(6) = {s6}",
      f"Arithmetic: 12 == 12. EXACT MATCH.\n"
      f"But 12 is ubiquitous (months, hours, zodiac, etc.).\n"
      f"No causal mechanism connecting vertebral development to sigma(6).\n"
      f"Embryology: thoracic count is Hox gene driven, not number-theoretic.\n"
      f"Grade: WHITE -- correct arithmetic, no structural significance.")

# H-SPORT-003: Ribs = 12 pairs = sigma(6)
# FACT: 12 pairs of ribs. Same sigma(6) = 12.
ribs_pairs = 12
match_003 = (ribs_pairs == s6)
# Note: ribs and thoracic vertebrae are CORRELATED (each rib attaches to a vertebra)
# So this is NOT an independent data point from H-SPORT-002!
grade("H-SPORT-003", "WHITE",
      match_003,
      f"Rib pairs = {ribs_pairs} = sigma(6) = {s6}",
      f"Arithmetic: 12 == 12. EXACT MATCH.\n"
      f"CRITICAL: Ribs attach to thoracic vertebrae 1:1.\n"
      f"This is NOT independent from H-SPORT-002!\n"
      f"12 ribs BECAUSE 12 thoracic vertebrae (same Hox genes).\n"
      f"Counting both as separate 'matches' is double-counting.\n"
      f"Grade: WHITE -- dependent on H-SPORT-002, not independent evidence.")

# H-SPORT-004: Cranial nerves = 12 = sigma(6)
# FACT: 12 pairs of cranial nerves (I-XII). sigma(6) = 12.
cranial_nerves = 12
match_004 = (cranial_nerves == s6)
# Note: CN count IS developmentally independent from vertebrae/ribs.
# But 12 is still a very common number. And CN0 (terminal nerve) exists
# in many species, making it arguably 13.
grade("H-SPORT-004", "WHITE",
      match_004,
      f"Cranial nerves = {cranial_nerves} = sigma(6) = {s6}",
      f"Arithmetic: 12 == 12. EXACT MATCH.\n"
      f"Developmentally independent from vertebrae (different origin).\n"
      f"But: CN0 (terminal nerve) exists in many vertebrates.\n"
      f"Historical: originally described as 7 (Willis 1664), later expanded to 12.\n"
      f"The number 12 is partly a classification choice.\n"
      f"No causal link between cranial nerve development and sigma(6).\n"
      f"Grade: WHITE -- arithmetic match, but 12 is common + classification dependent.")

# H-SPORT-005: Phalanges per finger = 3 (divisor of 6)
# FACT: Each finger has 3 phalanges (proximal, middle, distal). Thumb has 2.
# Divisors of 6: {1, 2, 3, 6}. 3 is a divisor.
phalanges_finger = 3
phalanges_thumb = 2
div6 = divisors(6)
match_005a = phalanges_finger in div6
match_005b = phalanges_thumb in div6
# Total phalanges per hand = 4*3 + 2 = 14. Not a divisor-related number.
total_phalanges = 4 * phalanges_finger + phalanges_thumb
grade("H-SPORT-005", "WHITE",
      match_005a and match_005b,
      f"Phalanges: finger={phalanges_finger}, thumb={phalanges_thumb}, both divisors of 6",
      f"Divisors of 6 = {div6}.\n"
      f"3 in divisors: {match_005a}, 2 in divisors: {match_005b}.\n"
      f"But divisors of 6 cover {{1,2,3,6}} = 4 out of first 6 integers.\n"
      f"Probability of a small integer (1-6) being a divisor of 6 = 4/6 = 67%.\n"
      f"Total phalanges per hand = {total_phalanges} (not special).\n"
      f"Fingers per hand = 5 (NOT a divisor of 6).\n"
      f"Grade: WHITE -- trivially easy to match when 4/6 small integers are divisors.")

# ═══════════════════════════════════════════════════════════════
# B. TEAM SPORTS (006-010)
# ═══════════════════════════════════════════════════════════════
print("== B. TEAM SPORTS ==\n")

# H-SPORT-006: Volleyball = 6 players per team
# FACT: Indoor volleyball = 6 per team. Beach = 2.
volleyball = 6
match_006 = (volleyball == 6)
# Note: volleyball was INVENTED by William Morgan in 1895.
# Original rules had no fixed team size. FIVB standardized 6 in 1947.
# The number 6 is a HUMAN DESIGN CHOICE, not a natural constant.
grade("H-SPORT-006", "WHITE",
      match_006,
      f"Volleyball players = {volleyball} = 6",
      f"Exact match with n=6.\n"
      f"But this is a HUMAN DESIGN CHOICE by FIVB (1947).\n"
      f"Original volleyball (1895) had no fixed team size.\n"
      f"Beach volleyball = 2 players. Snow volleyball = 3.\n"
      f"The '6' was chosen for court geometry, not mathematics.\n"
      f"Grade: WHITE -- human design choice, not natural constant.")

# H-SPORT-007: Ice hockey = 6 players (5 skaters + 1 goalie)
hockey = 6
match_007 = (hockey == 6)
# Ice hockey rules evolved. Originally 7-9 players per side (1870s).
# Reduced to 6 by NHL in 1911 for pace/safety.
grade("H-SPORT-007", "WHITE",
      match_007,
      f"Ice hockey players = {hockey} = 6 (5+1)",
      f"Exact match with n=6.\n"
      f"Original rules: 7-9 players (1870s-1900s).\n"
      f"NHL standardized 6 in 1911 for rink size/pace.\n"
      f"Human design choice. Could have been 5 or 7.\n"
      f"Grade: WHITE -- historical convention, not fundamental.")

# H-SPORT-008: Basketball = 5 per team (NOT 6)
basketball = 5
match_008 = (basketball == 6)
grade("H-SPORT-008", "WHITE",
      not match_008,  # We note it does NOT match
      f"Basketball players = {basketball}, NOT 6",
      f"Basketball = 5 per team. Does NOT match n=6.\n"
      f"5 = number of fingers (anthropometric?) but not divisor-related.\n"
      f"Originally 9 per team (Naismith 1891), then reduced.\n"
      f"Honest recording: basketball breaks the pattern.\n"
      f"Grade: WHITE -- does not match, recorded as honest failure.")

# H-SPORT-009: Soccer = 11, but claim: 11 = sigma(6) - 1?
soccer = 11
claim_009 = s6 - 1  # 12 - 1 = 11
match_009 = (soccer == claim_009)
# WARNING: -1 correction is PROHIBITED for star grading per CLAUDE.md
grade("H-SPORT-009", "WHITE",
      match_009,
      f"Soccer players = {soccer} = sigma(6)-1 = {claim_009}",
      f"Arithmetic: 12 - 1 = 11 = {soccer}. Correct.\n"
      f"BUT: -1 correction present. Per CLAUDE.md rules, ad hoc +/-1 = warning.\n"
      f"Original soccer had no fixed team size (1860s).\n"
      f"11 standardized by FA in 1897.\n"
      f"If we allow +/-1, ANY number near 6 or 12 'matches'.\n"
      f"Grade: WHITE -- ad hoc -1 correction, human design choice.")

# H-SPORT-010: Cricket over = 6 balls, Baseball inning = 6 outs
cricket_over = 6
baseball_outs_per_inning = 6  # 3 outs per half-inning * 2
match_010a = (cricket_over == 6)
match_010b = (baseball_outs_per_inning == 6)
# Cricket: overs were 4 balls (until 1889), then 5, then 6 (1900 in Australia,
# 1939/1947 international). Even 8-ball overs existed in Australia until 1979.
# Baseball: 3 outs since 1845 Knickerbocker Rules. 3*2=6 is just doubling.
grade("H-SPORT-010", "WHITE",
      match_010a and match_010b,
      f"Cricket over = {cricket_over}, Baseball inning outs = {baseball_outs_per_inning} = 6",
      f"Both equal 6. Arithmetic correct.\n"
      f"Cricket: overs were 4-ball, 5-ball, 8-ball historically.\n"
      f"  6-ball over only standardized internationally in 1979.\n"
      f"Baseball: 3 outs per half * 2 halves = 6. The '3' is the design choice.\n"
      f"Both are HUMAN DESIGN CHOICES that changed over time.\n"
      f"Grade: WHITE -- human conventions, not fundamental constants.")

# ═══════════════════════════════════════════════════════════════
# C. ATHLETIC PERFORMANCE (011-015)
# ═══════════════════════════════════════════════════════════════
print("== C. ATHLETIC PERFORMANCE ==\n")

# H-SPORT-011: Training zones typically 5-6
# Common models: 3-zone, 5-zone (Seiler), 6-zone, 7-zone (Coggan)
# No single standard. The number depends on the coach/system.
zone_models = [3, 5, 6, 7]  # Various systems
match_011 = 6 in zone_models
grade("H-SPORT-011", "WHITE",
      match_011,
      f"Training zones: varies by model {zone_models}, 6 is ONE option",
      f"Seiler 3-zone, ACSM 5-zone, some 6-zone, Coggan 7-zone.\n"
      f"No consensus on '6 zones'. It depends on the training system.\n"
      f"Cherry-picking the 6-zone model from many options.\n"
      f"Grade: WHITE -- multiple models exist, selecting 6 is cherry-picking.")

# H-SPORT-012: Heart rate zones = 5 (Karvonen method)
hr_zones = 5
match_012 = (hr_zones in divisors(6))
# 5 is NOT a divisor of 6. Divisors = {1,2,3,6}.
grade("H-SPORT-012", "WHITE",
      False,
      f"Heart rate zones = {hr_zones}, NOT a divisor of 6",
      f"Standard 5-zone HR model (50-60, 60-70, 70-80, 80-90, 90-100%).\n"
      f"5 is NOT a divisor of 6. Divisors of 6 = {div6}.\n"
      f"Honest failure. Does not match any n=6 structure.\n"
      f"Grade: WHITE -- does not match.")

# H-SPORT-013: Critical power model has 2 parameters = phi(6)
cp_params = 2  # W' (anaerobic work capacity) and CP (critical power)
p6 = euler_phi(6)
match_013 = (cp_params == p6)
# phi(6) = 2. CP model: P(t) = CP + W'/t. Two parameters.
# But MANY simple models have 2 parameters (y = mx + b, etc.)
# A 2-parameter model is the simplest non-trivial fit.
grade("H-SPORT-013", "WHITE",
      match_013,
      f"Critical power parameters = {cp_params} = phi(6) = {p6}",
      f"CP model: P(t) = CP + W'/t. Parameters: CP and W'.\n"
      f"phi(6) = {p6}. Arithmetic match.\n"
      f"But 2-parameter models are EXTREMELY common in all of science.\n"
      f"Linear regression = 2 params. Michaelis-Menten = 2 params.\n"
      f"Probability of a simple model having 2 params is very high.\n"
      f"Grade: WHITE -- trivially common for simple models to have 2 parameters.")

# H-SPORT-014: Lactate threshold at ~80% max HR
# Check if 0.80 is in Golden Zone [0.212, 0.500]
lt_fraction = 0.80  # typical: 75-85% of max HR
in_gz = GZ_LOWER <= lt_fraction <= GZ_UPPER
# 0.80 is WAY above the Golden Zone upper bound of 0.500
grade("H-SPORT-014", "WHITE",
      False,
      f"Lactate threshold ~{lt_fraction} NOT in Golden Zone [{GZ_LOWER:.3f}, {GZ_UPPER:.3f}]",
      f"Lactate threshold typically at 75-85% of max HR.\n"
      f"Golden Zone = [{GZ_LOWER:.4f}, {GZ_UPPER:.4f}].\n"
      f"0.80 >> 0.500 (upper bound). DOES NOT MATCH.\n"
      f"Even 1-LT = 0.20 is just below GZ_LOWER = 0.212.\n"
      f"No meaningful connection to Golden Zone.\n"
      f"Grade: WHITE -- clear mismatch with Golden Zone.")

# H-SPORT-015: Fast/slow twitch fiber ratio
# Elite sprinters: ~80% fast-twitch. Endurance: ~80% slow-twitch.
# General population: ~50/50.
# Check if any ratio is in Golden Zone
general_ratio = 0.50  # 50% fast-twitch in general pop
sprinter_fast = 0.80
endurance_slow = 0.80
match_015_general = GZ_LOWER <= general_ratio <= GZ_UPPER
# 0.50 is exactly GZ_UPPER. Boundary hit.
# But this is just saying "50/50" which is the most generic ratio possible.
grade("H-SPORT-015", "WHITE",
      match_015_general,
      f"Muscle fiber ratio: general pop = {general_ratio} at GZ upper boundary",
      f"General population: ~50% fast / 50% slow twitch.\n"
      f"0.50 = GZ_UPPER = 1/2 (Riemann critical line).\n"
      f"But 50/50 is the DEFAULT for any binary split.\n"
      f"It's the maximum entropy distribution, not a discovery.\n"
      f"Sprinters: 80/20 (not in GZ). Endurance: 20/80 (0.20, just below GZ).\n"
      f"Grade: WHITE -- 50/50 is trivially the default ratio.")

# ═══════════════════════════════════════════════════════════════
# D. BIOMECHANICS (016-020)
# ═══════════════════════════════════════════════════════════════
print("== D. BIOMECHANICS ==\n")

# H-SPORT-016: Gait cycle phi(6)=2 phases (stance + swing)
gait_phases = 2  # stance + swing
match_016 = (gait_phases == p6)
# Any cyclic motion divides into 2 phases (action + recovery).
# Walking, breathing, heartbeat, pendulum...
grade("H-SPORT-016", "WHITE",
      match_016,
      f"Gait cycle phases = {gait_phases} = phi(6) = {p6}",
      f"Stance phase + Swing phase = 2 main phases.\n"
      f"phi(6) = 2. Arithmetic match.\n"
      f"But ANY cyclic motion has 2 phases (positive/negative half-cycle).\n"
      f"Heartbeat: systole + diastole = 2. Breathing: inhale + exhale = 2.\n"
      f"This is a property of ALL oscillatory systems, not specific to 6.\n"
      f"Grade: WHITE -- trivially true for any cyclic motion.")

# H-SPORT-017: Saunders' 6 determinants of gait
# FACT: Saunders, Inman & Eberhart (1953) described 6 determinants of gait:
# 1. Pelvic rotation, 2. Pelvic tilt, 3. Knee flexion in stance,
# 4. Foot mechanisms, 5. Knee mechanisms, 6. Lateral pelvic displacement
saunders_det = 6
match_017 = (saunders_det == 6)
# HOWEVER: This framework has been CHALLENGED.
# Della Croce et al. (2001): questioned whether all 6 actually minimize COM displacement
# Kuo (2007): showed some determinants don't reduce metabolic cost
# Modern biomechanics often uses different frameworks.
grade("H-SPORT-017", "WHITE",
      match_017,
      f"Saunders' gait determinants = {saunders_det} = 6",
      f"Saunders, Inman & Eberhart (1953): 6 determinants.\n"
      f"Exact match with n=6.\n"
      f"BUT: This is a CLASSIFICATION CHOICE by the authors.\n"
      f"Della Croce et al. (2001) challenged validity of this framework.\n"
      f"Kuo (2007) showed some 'determinants' don't reduce metabolic cost.\n"
      f"Modern textbooks often use 3-determinant or energy-based models.\n"
      f"The '6' is an author's taxonomic decision, not a natural constant.\n"
      f"Grade: WHITE -- author classification choice, contested framework.")

# H-SPORT-018: Shoulder DOF = 3, Hip DOF = 3
# Ball-and-socket joints have 3 DOF (flexion/extension, abduction/adduction, rotation)
shoulder_dof = 3
hip_dof = 3
knee_dof = 1  # primarily (also some rotation when flexed, but primarily 1)
ankle_dof = 1  # primarily dorsi/plantarflexion (also some inversion/eversion)
total_lower = hip_dof + knee_dof + ankle_dof  # 3+1+1 = 5
total_upper = shoulder_dof + 1 + 1  # elbow=1 hinge, wrist=2 (but let's use analogous)
match_018_shoulder = shoulder_dof in div6
match_018_hip = hip_dof in div6
# 3 is a divisor of 6. But 3 DOF is required by the geometry of 3D space.
# Any ball-and-socket joint in 3D MUST have 3 rotational DOF. It's geometry, not 6.
grade("H-SPORT-018", "WHITE",
      match_018_shoulder and match_018_hip,
      f"Shoulder DOF={shoulder_dof}, Hip DOF={hip_dof}, both divisors of 6",
      f"Ball-and-socket joints: 3 DOF = 3 rotational axes in 3D space.\n"
      f"3 is a divisor of 6, but 3 DOF comes from 3D EUCLIDEAN GEOMETRY.\n"
      f"ANY ball-and-socket joint MUST have 3 DOF in 3D space.\n"
      f"This is dim(SO(3))=3, not a property of perfect number 6.\n"
      f"Knee={knee_dof} DOF, Ankle={ankle_dof} DOF (not 3).\n"
      f"Total lower limb DOF = {total_lower} (not 6).\n"
      f"Grade: WHITE -- 3 DOF is 3D geometry, not number theory.")

# H-SPORT-019: Running cadence 180 steps/min = 3 * 60
# Daniels (1985) observed elite runners ~180 spm. Often cited.
cadence = 180
# 180 = 6 * 30 = 3 * 60 = 2 * 90
# Factorization: 180 = 2^2 * 3^2 * 5
match_019 = (cadence % 6 == 0)
# 180 is divisible by 6, but also by 2, 3, 4, 5, 9, 10, 12, 15, 20, 30, 36, 45, 60, 90
# However: 180 spm is NOT universal. Range is 160-200 spm.
# Recreational runners: 150-170 spm. The "180" is a rough guideline.
grade("H-SPORT-019", "WHITE",
      match_019,
      f"Running cadence {cadence} = 6 x 30, divisible by 6",
      f"180 / 6 = 30. Divisible by 6.\n"
      f"But 180 is divisible by MANY numbers: 2,3,4,5,6,9,10,12,15,...\n"
      f"180 = 2^2 * 3^2 * 5. Highly composite number.\n"
      f"Elite cadence varies: 176-190 spm. '180' is approximate.\n"
      f"Recreational runners: 150-170 spm (NOT divisible by 6 for 155, 165).\n"
      f"The '180' is a rough coaching guideline, not a constant.\n"
      f"Grade: WHITE -- highly composite number, approximate guideline.")

# H-SPORT-020: Vertical jump ground contact/flight time ratio
# Standing vertical jump: ground contact ~0.3-0.4s, flight time ~0.5-0.6s
# Ratio: contact/flight ~ 0.3/0.5 = 0.6 or 0.4/0.6 = 0.67
# In Golden Zone [0.212, 0.500]?
# For countermovement jump: propulsion phase ~0.25-0.35s, flight ~0.5s
# Ratio ~ 0.25/0.50 = 0.50 to 0.35/0.50 = 0.70
contact = 0.30  # typical propulsion phase
flight = 0.55   # typical flight time
ratio_020 = contact / flight
in_gz_020 = GZ_LOWER <= ratio_020 <= GZ_UPPER
# ratio ~ 0.545 -- above GZ upper bound
# But with different numbers: 0.25/0.60 = 0.417, which IS in GZ
# The variability is too large to claim a match.
contact_low = 0.25
flight_high = 0.60
ratio_020_alt = contact_low / flight_high
in_gz_020_alt = GZ_LOWER <= ratio_020_alt <= GZ_UPPER
grade("H-SPORT-020", "WHITE",
      in_gz_020 or in_gz_020_alt,
      f"Jump contact/flight ratio: {ratio_020:.3f} or {ratio_020_alt:.3f}",
      f"Contact time: 0.25-0.35s. Flight time: 0.50-0.60s.\n"
      f"Ratio range: {contact_low/flight_high:.3f} to {contact/flight:.3f}.\n"
      f"Golden Zone: [{GZ_LOWER:.4f}, {GZ_UPPER:.4f}].\n"
      f"Some values fall in GZ ({ratio_020_alt:.3f}), some don't ({ratio_020:.3f}).\n"
      f"Range is too wide to claim a 'match' -- it spans GZ and beyond.\n"
      f"Individual variation dominates any pattern.\n"
      f"Grade: WHITE -- too much variability, no clean match.")


# ═══════════════════════════════════════════════════════════════
# TEXAS SHARPSHOOTER TEST
# ═══════════════════════════════════════════════════════════════
print("=" * 72)
print("  TEXAS SHARPSHOOTER TEST")
print("=" * 72)
print()

# Count how many of 20 hypotheses have exact numeric matches to {1,2,3,4,6,12}
# (regardless of whether they're meaningful)
exact_matches = 0
match_details = []
# H-002: 12=sigma(6) YES
# H-003: 12=sigma(6) YES (but dependent on 002)
# H-004: 12=sigma(6) YES
# H-005: 3,2 divisors YES
# H-006: 6 YES
# H-007: 6 YES
# H-010: 6 YES (both)
# H-013: 2=phi(6) YES
# H-016: 2=phi(6) YES
# H-017: 6 YES
# H-018: 3 YES
# H-019: divisible by 6 (weaker)
# Strict count (exact = to a target):
strict_matches = 12  # H-002,003,004,005(x2),006,007,010,013,016,017,018
total_hypotheses = 20

# But subtract dependent ones (H-003 depends on H-002)
independent_matches = strict_matches - 1  # = 11
# And subtract trivially common ones (2-parameter model, 2-phase cycle, 3 DOF from 3D)
# = 11 - 3 = 8 non-trivial independent matches
nontrivial_independent = independent_matches - 3  # = 8

print(f"  Strict exact matches to {{1,2,3,4,6,12}}: {strict_matches}/{total_hypotheses}")
print(f"  After removing dependent (H-003): {independent_matches}/{total_hypotheses}")
print(f"  After removing trivially explained: {nontrivial_independent}/{total_hypotheses}")
print()

# Monte Carlo: if we pick 20 random integers from 1-30, how many hit {1,2,3,4,6,12}?
random.seed(42)
p_strict = texas_sharpshooter_p(strict_matches, total_hypotheses)
p_independent = texas_sharpshooter_p(independent_matches, total_hypotheses - 1)  # 19 tests
p_nontrivial = texas_sharpshooter_p(nontrivial_independent, total_hypotheses - 4)  # 16 tests

print(f"  Texas Sharpshooter p-values (Monte Carlo, 100K sims):")
print(f"    Strict:     p = {p_strict:.4f} ({strict_matches}/{total_hypotheses} matches)")
print(f"    Independent: p = {p_independent:.4f} ({independent_matches}/{total_hypotheses-1} matches)")
print(f"    Non-trivial: p = {p_nontrivial:.4f} ({nontrivial_independent}/{total_hypotheses-4} matches)")
print()

# Expected matches from uniform random
# P(hit) = |{1,2,3,4,6,12}| / 30 = 6/30 = 0.2
p_hit = 6 / 30
expected = total_hypotheses * p_hit
print(f"  Expected matches (uniform 1-30): {expected:.1f}")
print(f"  Observed (strict): {strict_matches}")
print(f"  Ratio: {strict_matches/expected:.1f}x expected")
print()

# KEY INSIGHT: Most matches are human design choices or geometric necessities
print("  CRITICAL ANALYSIS:")
print("  ──────────────────")
print("  - Body counts (12 vertebrae, 12 ribs, 12 nerves): 12 is common in biology")
print("    and ribs are DEPENDENT on vertebrae count")
print("  - Sport counts (6 in volleyball/hockey/cricket): HUMAN DESIGN CHOICES")
print("    that changed over history")
print("  - 2-phase cycles: ANY oscillation has 2 phases (trivial)")
print("  - 3 DOF: Required by 3D geometry (dim SO(3) = 3)")
print("  - 2-parameter models: Simplest non-trivial parametric model")
print()
print("  VERDICT: High match count but LOW significance.")
print("  Every match has a simpler explanation (design choice, geometry, or ubiquity of 12).")
print()

# ═══════════════════════════════════════════════════════════════
# SUMMARY TABLE
# ═══════════════════════════════════════════════════════════════
print("=" * 72)
print("  SUMMARY TABLE")
print("=" * 72)
print()
print(f"  {'ID':<14} {'Grade':<8} {'Pass':<6} {'Description'}")
print(f"  {'─'*14} {'─'*8} {'─'*6} {'─'*50}")

green = orange_star = orange = white = black = 0
for hid, emoji, passed, desc, _ in results:
    pstr = "YES" if passed else "NO"
    print(f"  {hid:<14} {emoji:<8} {pstr:<6} {desc[:60]}")
    if emoji == "GREEN" or emoji == "\U0001f7e9":
        green += 1
    elif emoji == "ORANGE_STAR" or emoji == "\U0001f7e7\u2b50":
        orange_star += 1
    elif emoji == "ORANGE" or emoji == "\U0001f7e7":
        orange += 1
    elif emoji == "WHITE":
        white += 1
    elif emoji == "BLACK" or emoji == "\u2b1b":
        black += 1

print()
print(f"  TOTALS: GREEN={green}  ORANGE_STAR={orange_star}  ORANGE={orange}  WHITE={white}  BLACK={black}")
print(f"  All {len(results)} hypotheses graded WHITE (coincidental/trivial).")
print()
print("  No hypothesis reaches ORANGE or GREEN grade.")
print("  The n=6 framework does not produce non-trivial predictions in sports/biomechanics.")
print()

sys.exit(0)
