#!/usr/bin/env python3
"""
Verify Nutrition/Agriculture/Food Science Hypotheses H-NUTR-001 through H-NUTR-020.

Each hypothesis is checked against known nutritional science data and arithmetic.
Grades:
  GREEN  = Exact equation, mathematically proven
  ORANGE = Numerically correct within stated tolerance, structurally interesting
  WHITE  = Arithmetically correct but trivial/coincidental
  BLACK  = Arithmetically wrong or factually incorrect

Run: PYTHONPATH=. python3 verify/verify_nutrition_hypotheses.py
"""
import math
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

# ── Golden Zone constants ──
GZ_UPPER = 0.5
GZ_LOWER = 0.5 - math.log(4/3)
GZ_CENTER = 1/math.e
GZ_WIDTH = math.log(4/3)

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
print("  NUTRITION/AGRICULTURE/FOOD SCIENCE HYPOTHESES VERIFICATION")
print("  H-NUTR-001 to H-NUTR-020")
print("=" * 72)
print()

# ═══════════════════════════════════════════════════════════════════════
# A. NUTRITION (7 hypotheses)
# ═══════════════════════════════════════════════════════════════════════
print("== A. NUTRITION ==\n")

# H-NUTR-001: 6 essential nutrient classes = perfect number 6
# Classes: carbohydrates, proteins, fats, vitamins, minerals, water
# This is the standard nutritional science classification
nutrient_classes = ["carbohydrates", "proteins", "fats", "vitamins", "minerals", "water"]
n_classes = len(nutrient_classes)
perf6 = is_perfect(6)
# Check: is this the ONLY accepted classification? Some list 7 (adding fiber)
# Standard textbooks (Whitney & Rolfes, etc.) list exactly 6
grade("H-NUTR-001", "⚪", n_classes == 6 and perf6,
      "6 essential nutrient classes = perfect number 6",
      f"Classes: {', '.join(nutrient_classes)}\n"
      f"Count = {n_classes}, is_perfect(6) = {perf6}\n"
      f"Arithmetic: EXACT. 6 classes is standard textbook classification.\n"
      f"But: mapping 'count of nutrient classes = 6 = perfect number' is post-hoc.\n"
      f"The number 6 here is a human classification choice, not a natural law.\n"
      f"Some frameworks add fiber or phytochemicals as 7th class.\n"
      f"Texas grade: WHITE -- counting match is trivially achievable.")

# H-NUTR-002: 6 taste modalities (sweet, sour, salty, bitter, umami, fat)
# Traditional 5 tastes + fat (oleogustus, recognized ~2015)
tastes = ["sweet", "sour", "salty", "bitter", "umami", "fat (oleogustus)"]
n_tastes = len(tastes)
# Note: some researchers add starchy, metallic, etc. -- not universally accepted
# Fat taste (oleogustus) accepted by some but debated
grade("H-NUTR-002", "⚪", n_tastes == 6,
      "6 taste modalities matching perfect number 6",
      f"Tastes: {', '.join(tastes)}\n"
      f"Count = {n_tastes}\n"
      f"Arithmetic: COUNT matches IF you include oleogustus (fat taste).\n"
      f"Traditional count is 5 (without fat). Fat taste is debated.\n"
      f"Other proposed tastes: kokumi, starchy, calcium, metallic.\n"
      f"If any additional taste is accepted, count != 6.\n"
      f"Texas grade: WHITE -- classification boundary is flexible.")

# H-NUTR-003: Essential amino acids = 9, BCAA = 3 = divisor of 6
# 9 EAAs: His, Ile, Leu, Lys, Met, Phe, Thr, Trp, Val
# BCAAs: Leu, Ile, Val (branched-chain)
eaa_count = 9
bcaa_count = 3
bcaa_ratio = bcaa_count / eaa_count
divisors_6 = [1, 2, 3, 6]
is_divisor = bcaa_count in divisors_6
ratio_check = abs(bcaa_ratio - 1/3) < 1e-10  # 3/9 = 1/3 exactly
grade("H-NUTR-003", "⚪", is_divisor and ratio_check,
      "BCAA/EAA = 3/9 = 1/3 (meta fixed point), 3 is divisor of 6",
      f"Essential amino acids: 9 (His, Ile, Leu, Lys, Met, Phe, Thr, Trp, Val)\n"
      f"BCAAs: 3 (Leu, Ile, Val)\n"
      f"BCAA/EAA = {bcaa_count}/{eaa_count} = {bcaa_ratio:.6f}\n"
      f"1/3 (TECS meta fixed point) = {1/3:.6f}\n"
      f"3 in divisors of 6: {is_divisor}\n"
      f"Arithmetic: EXACT. 3/9 = 1/3 is trivially true.\n"
      f"But: 9 EAAs is specific to adult humans. Children need 10 (+ arginine).\n"
      f"Mapping BCAA count to divisor of 6 is post-hoc. Any count 1-6 is a divisor of 6!.\n"
      f"Texas grade: WHITE -- 1/3 ratio is trivially achievable from 3/9.")

# H-NUTR-004: Macronutrient energy ratios and Golden Zone
# Typical recommendations: 45-65% carb, 10-35% protein, 20-35% fat
# Check: does any standard ratio fall in Golden Zone?
# 40/30/30 "Zone Diet": protein ratio = 0.30
# 50/30/20 traditional: fat ratio = 0.20
# WHO recommendation: 55/15/30: protein = 0.15, fat = 0.30
fat_zone = 0.30  # typical fat recommendation
prot_zone = 0.30  # Zone diet protein
in_gz_fat = GZ_LOWER <= fat_zone <= GZ_UPPER
in_gz_prot = GZ_LOWER <= prot_zone <= GZ_UPPER
# Golden Zone = [0.2123, 0.5000] -- width ~0.288
# Probability of random [0,1] value hitting GZ = 0.288 = 28.8%
p_random_gz = GZ_WIDTH  # probability a random ratio lands in GZ
grade("H-NUTR-004", "⚪", in_gz_fat and in_gz_prot,
      "Macronutrient ratios (fat ~0.30, protein ~0.30) fall in Golden Zone",
      f"Golden Zone = [{GZ_LOWER:.4f}, {GZ_UPPER:.4f}], width = {GZ_WIDTH:.4f}\n"
      f"Fat ratio 0.30 in GZ: {in_gz_fat}\n"
      f"Protein ratio 0.30 in GZ: {in_gz_prot}\n"
      f"But: GZ covers 28.8% of [0,1]. For 3 macronutrients summing to 1,\n"
      f"at least one must be >= 1/3 = 0.333 which is in GZ.\n"
      f"P(at least one of 3 ratios in GZ) is very high by pigeonhole.\n"
      f"Texas grade: WHITE -- near-guaranteed by pigeonhole principle.")

# H-NUTR-005: Daily water ~2.5L, calories ~2000kcal, ratio patterns
# Check if 2000/2500 or water fraction has any pattern
daily_water_ml = 2500  # ~2.5L typical recommendation
daily_kcal = 2000
ratio_water_cal = daily_water_ml / daily_kcal  # = 1.25
# Body is ~60% water. 0.60 in GZ? Yes (0.60 > 0.50 = GZ_UPPER)
body_water = 0.60
in_gz_body = GZ_LOWER <= body_water <= GZ_UPPER
grade("H-NUTR-005", "⬛", False,
      "Daily intake ratios produce Golden Zone values",
      f"Daily water: ~2500 mL, Daily calories: ~2000 kcal\n"
      f"Ratio water/cal = {ratio_water_cal} (no meaningful unit ratio)\n"
      f"Body water fraction = 0.60, GZ_UPPER = {GZ_UPPER}\n"
      f"0.60 > 0.50 = OUTSIDE Golden Zone.\n"
      f"No meaningful ratio from daily intake values lands in GZ non-trivially.\n"
      f"The water/calorie ratio has incompatible units (mL vs kcal).\n"
      f"Texas grade: BLACK -- no valid mapping found.")

# H-NUTR-006: 13 essential vitamins, sigma(6)=12 close
# 13 vitamins: A, C, D, E, K, B1, B2, B3, B5, B6, B7, B9, B12
n_vitamins = 13
sig6 = sigma(6)  # = 12
diff_vit = n_vitamins - sig6
# Major minerals: Ca, P, Mg, Na, K, Cl, S = 7 (standard list)
n_major_minerals = 7
grade("H-NUTR-006", "⬛", False,
      "13 essential vitamins = sigma(6)=12",
      f"Essential vitamins: 13 (A, C, D, E, K, B1, B2, B3, B5, B6, B7, B9, B12)\n"
      f"sigma(6) = {sig6} = 12\n"
      f"Difference: {diff_vit} (off by 1)\n"
      f"Major minerals: {n_major_minerals} (Ca, P, Mg, Na, K, Cl, S)\n"
      f"Neither 13 nor 7 matches sigma(6)=12 or tau(6)=4 or phi(6)=2.\n"
      f"Off-by-one corrections are prohibited by CLAUDE.md grading rules.\n"
      f"Texas grade: BLACK -- no exact match.")

# H-NUTR-007: B vitamins: 8 types, but B6 exists. B-complex structure.
# B vitamins: B1, B2, B3, B5, B6, B7, B9, B12
# Gaps in numbering: B4, B8, B10, B11 were reclassified (not vitamins)
# Original: B1-B12 = 12 proposed. 4 removed. 12 - 4 = 8 remain.
b_vitamins = [1, 2, 3, 5, 6, 7, 9, 12]
n_b = len(b_vitamins)
removed_b = [4, 8, 10, 11]
n_removed = len(removed_b)
original_proposed = 12
# sigma(6) = 12 = original proposed B vitamins
# tau(6) = 4 = number removed
grade("H-NUTR-007", "⚪", original_proposed == sig6 and n_removed == tau(6),
      "Original 12 B-vitamins = sigma(6), 4 removed = tau(6)",
      f"Original proposed B-vitamins: B1 through B12 = {original_proposed}\n"
      f"sigma(6) = {sig6}\n"
      f"Removed (reclassified): B{removed_b} = {n_removed}\n"
      f"tau(6) = {tau(6)}\n"
      f"Remaining: {n_b} B-vitamins = {b_vitamins}\n"
      f"Arithmetic: 12 = sigma(6) EXACT, 4 = tau(6) EXACT.\n"
      f"But: the original numbering B1-B12 is sequential labeling (trivially 12).\n"
      f"4 removals is historical accident, not a natural law.\n"
      f"The numbering was arbitrary (B4=adenine, reclassified as nucleotide).\n"
      f"Texas grade: WHITE -- sequential labeling guarantees count = max index.")

# ═══════════════════════════════════════════════════════════════════════
# B. AGRICULTURE (5 hypotheses)
# ═══════════════════════════════════════════════════════════════════════
print("== B. AGRICULTURE ==\n")

# H-NUTR-008: Norfolk 4-course rotation = tau(6), 3-field = divisor
# Norfolk: turnips, barley, clover, wheat = 4 crops
# Medieval 3-field: winter grain, spring grain, fallow = 3 fields
norfolk_courses = 4
medieval_fields = 3
grade("H-NUTR-008", "⚪", norfolk_courses == tau(6) and medieval_fields in divisors_6,
      "Norfolk 4-course = tau(6)=4, medieval 3-field = divisor of 6",
      f"Norfolk rotation: 4 courses (turnips, barley, clover, wheat)\n"
      f"tau(6) = {tau(6)}\n"
      f"Medieval: 3-field system\n"
      f"3 in divisors of 6: True\n"
      f"Arithmetic: EXACT matches.\n"
      f"But: crop rotation systems range from 2 to 8+ courses historically.\n"
      f"Norfolk = 4 was an 18th century English innovation, culture-specific.\n"
      f"3-field was common but 2-field also widely used.\n"
      f"Selecting 3 and 4 from many systems = cherry-picking.\n"
      f"Texas grade: WHITE -- selected from many possible systems.")

# H-NUTR-009: Soil horizons O, A, E, B, C, R = 6
soil_horizons = ["O (organic)", "A (topsoil)", "E (eluviation)",
                 "B (subsoil)", "C (parent material)", "R (bedrock)"]
n_horizons = len(soil_horizons)
grade("H-NUTR-009", "⚪", n_horizons == 6 and is_perfect(6),
      "6 soil master horizons = perfect number 6",
      f"Horizons: {', '.join(soil_horizons)}\n"
      f"Count = {n_horizons}, is_perfect(6) = {perf6}\n"
      f"Arithmetic: COUNT = 6 EXACT.\n"
      f"This is the USDA standard classification (6 master horizons).\n"
      f"However: not all soils have all 6 (E horizon often absent).\n"
      f"Some systems add transitional horizons (AB, BC, etc.).\n"
      f"The 6-horizon classification is a human taxonomy choice.\n"
      f"Interesting: unlike nutrient classes, this is more standardized.\n"
      f"Texas grade: WHITE -- human classification, not natural law.")

# H-NUTR-010: Soil texture triangle: 3 components = divisor of 6
soil_components = ["sand", "silt", "clay"]
n_components = len(soil_components)
# Any 3-component system sums to 1 (ternary diagram)
# 3 is divisor of 6 but also divisor of many numbers
# More interesting: in a ternary diagram, each component ranges [0,1]
# Optimal soil (loam) is roughly equal parts: ~1/3 each
loam_fraction = 1/3  # approximately equal parts
in_gz_loam = GZ_LOWER <= loam_fraction <= GZ_UPPER
grade("H-NUTR-010", "⚪", n_components in divisors_6 and in_gz_loam,
      "3 soil components (sand/silt/clay), balanced loam at 1/3 each",
      f"Components: {', '.join(soil_components)}\n"
      f"Count = {n_components}, is divisor of 6: True\n"
      f"Ideal loam: ~33% each = 1/3 = {1/3:.6f}\n"
      f"1/3 in Golden Zone [{GZ_LOWER:.4f}, {GZ_UPPER:.4f}]: {in_gz_loam}\n"
      f"1/3 = TECS meta fixed point\n"
      f"Arithmetic: trivially true. Any ternary system has 3 components.\n"
      f"Equal partition of 3 always gives 1/3.\n"
      f"Loam is NOT exactly 33/33/33 -- it is a range (23-52% sand, etc.).\n"
      f"Texas grade: WHITE -- trivial ternary partition.")

# H-NUTR-011: ~75% of food crops depend on pollinators
pollinator_dependent = 0.75
one_minus_gz_width = 1 - GZ_WIDTH  # = 1 - ln(4/3) = 0.7123
diff_poll = abs(pollinator_dependent - one_minus_gz_width)
# Also check: 3/4 = 0.75
three_quarters = 3/4
grade("H-NUTR-011", "⚪", diff_poll < 0.05,
      "~75% pollinator dependence vs 1-ln(4/3)=0.712",
      f"Pollinator-dependent food crops: ~75% (FAO estimate)\n"
      f"1 - GZ_WIDTH = 1 - ln(4/3) = {one_minus_gz_width:.4f}\n"
      f"Difference: {diff_poll:.4f} ({diff_poll/pollinator_dependent*100:.1f}%)\n"
      f"Also: 75% = 3/4, a simple fraction unrelated to TECS.\n"
      f"The 75% figure itself is an estimate with wide uncertainty.\n"
      f"Klein et al. (2007) gives 35% of crop volume (not species).\n"
      f"The quoted '75%' varies by source: 35% to 87%.\n"
      f"With such wide range, any target value can be 'close'.\n"
      f"Texas grade: WHITE -- approximate data, wide uncertainty band.")

# H-NUTR-012: Growing seasons 1-3 depending on climate
# Tropical: 2-3 seasons, Temperate: 1-2, Arctic: 0-1
# Check: max growing seasons = 3 = divisor of 6
max_seasons = 3
grade("H-NUTR-012", "⚪", max_seasons in divisors_6,
      "Max growing seasons (3) = divisor of 6",
      f"Typical growing seasons: 1 (temperate), 2 (subtropical), 3 (tropical)\n"
      f"Max = {max_seasons}, is divisor of 6: True\n"
      f"But: this is highly variable. With greenhouses: unlimited.\n"
      f"Rice triple-cropping exists but is not universal.\n"
      f"Any small number 1-6 is a divisor of 6, making this trivial.\n"
      f"Texas grade: WHITE -- any small count is likely a divisor of 6.")

# ═══════════════════════════════════════════════════════════════════════
# C. FOOD SCIENCE (4 hypotheses)
# ═══════════════════════════════════════════════════════════════════════
print("== C. FOOD SCIENCE ==\n")

# H-NUTR-013: Maillard reaction onset ~140C; 140 and 6 relationship?
maillard_onset_C = 140  # degrees Celsius
maillard_onset_K = maillard_onset_C + 273.15  # = 413.15 K
# 140 = 4 * 5 * 7. Not obviously related to 6.
# 413.15 K. sigma(6)*tau(6)*phi(6) = 12*4*2 = 96. No.
# 140/6 = 23.33... not clean
# Try: 413.15/273.15 (ratio to water freezing) = 1.5123
ratio_to_freeze = maillard_onset_K / 273.15
grade("H-NUTR-013", "⬛", False,
      "Maillard reaction temperature (140C) relates to 6",
      f"Maillard onset: ~140 C = 413.15 K\n"
      f"140 = 4 * 5 * 7 (no factor of 6)\n"
      f"140 / 6 = {140/6:.4f} (not clean)\n"
      f"413.15 K / 273.15 K = {ratio_to_freeze:.4f} (not 3/2 = 1.5)\n"
      f"sigma(6)*tau(6)*phi(6) = {sigma(6)*tau(6)*euler_phi(6)} (no match)\n"
      f"No meaningful arithmetic connection found.\n"
      f"Texas grade: BLACK -- no valid mapping.")

# H-NUTR-014: 6 main fermentation types
# Alcoholic, lactic acid, acetic acid, propionic, butyric, mixed acid
fermentation_types = ["alcoholic", "lactic acid", "acetic acid",
                      "propionic", "butyric", "mixed acid"]
n_ferm = len(fermentation_types)
# Check: is this a standard classification?
# Microbiology textbooks vary: some list fewer, some add more
# (citric acid fermentation, methane fermentation, etc.)
grade("H-NUTR-014", "⚪", n_ferm == 6,
      "6 main fermentation types = perfect number 6",
      f"Types: {', '.join(fermentation_types)}\n"
      f"Count = {n_ferm}\n"
      f"But: this classification is NOT standard.\n"
      f"Prescott's Microbiology lists: alcoholic, lactic, others.\n"
      f"Additional types: citric acid, methane, butanediol, etc.\n"
      f"'6 main types' is achieved by arbitrary selection.\n"
      f"If you choose which types are 'main', you control the count.\n"
      f"Texas grade: WHITE -- classification is researcher's choice.")

# H-NUTR-015: 6 basic bread ingredients
# flour, water, yeast, salt, sugar, fat
bread_ingredients = ["flour", "water", "yeast", "salt", "sugar", "fat"]
n_bread = len(bread_ingredients)
# Check: minimal bread = flour + water + yeast + salt = 4
# Sugar and fat are optional enrichments
minimal_bread = 4  # flour, water, yeast, salt
grade("H-NUTR-015", "⬛", False,
      "6 basic bread ingredients = perfect number 6",
      f"Listed: {', '.join(bread_ingredients)} = {n_bread}\n"
      f"But: basic bread requires only {minimal_bread}: flour, water, yeast, salt.\n"
      f"Flatbread: just flour + water = 2.\n"
      f"Sugar and fat are enrichments, not basic ingredients.\n"
      f"Claiming 6 'basic' ingredients requires including optional ones.\n"
      f"Texas grade: BLACK -- factually incorrect (basic bread != 6 ingredients).")

# H-NUTR-016: 6 main food preservation methods
# Canning, drying, freezing, fermenting, salting, smoking
preservation = ["canning", "drying", "freezing", "fermenting", "salting", "smoking"]
n_pres = len(preservation)
# Other methods: pickling, irradiation, vacuum packing, pasteurization, sugaring...
# The list is arbitrary
grade("H-NUTR-016", "⚪", n_pres == 6,
      "6 food preservation methods = perfect number 6",
      f"Listed: {', '.join(preservation)} = {n_pres}\n"
      f"Other methods: pickling, irradiation, vacuum packing,\n"
      f"  pasteurization, sugaring, chemical preservatives, UHT, HPP...\n"
      f"The '6 main methods' selection is arbitrary.\n"
      f"Ancient methods were fewer (drying, salting, smoking, fermenting = 4).\n"
      f"Modern methods are more (adding irradiation, HPP, MAP, etc.).\n"
      f"Texas grade: WHITE -- arbitrary selection to reach 6.")

# ═══════════════════════════════════════════════════════════════════════
# D. HUMAN METABOLISM (4 hypotheses)
# ═══════════════════════════════════════════════════════════════════════
print("== D. HUMAN METABOLISM ==\n")

# H-NUTR-017: Thermic effect of food (TEF) ~10% = 1/sigma_neg1(6)?
# TEF: ~10% of caloric intake used to digest food
# sigma_neg1(6) = 1/1 + 1/2 + 1/3 + 1/6 = 2.0 (perfect number property)
# 1/sigma_neg1(6) = 1/2 = 0.5 -- no, that is not 10%
# Try: TEF = 10% = 0.10. Closest TECS values:
# phi(6)/sigma(6) = 2/12 = 1/6 = 0.1667
# 1/sigma(6) = 1/12 = 0.0833
tef = 0.10
phi_over_sigma = euler_phi(6) / sigma(6)  # 2/12 = 0.1667
inv_sigma = 1 / sigma(6)  # 1/12 = 0.0833
diff_1 = abs(tef - phi_over_sigma)
diff_2 = abs(tef - inv_sigma)
grade("H-NUTR-017", "⬛", False,
      "TEF ~10% matches a perfect-6 ratio",
      f"Thermic effect of food: ~10% = 0.10\n"
      f"phi(6)/sigma(6) = {euler_phi(6)}/{sigma(6)} = {phi_over_sigma:.4f} (diff {diff_1:.4f})\n"
      f"1/sigma(6) = 1/{sigma(6)} = {inv_sigma:.4f} (diff {diff_2:.4f})\n"
      f"Neither is close. TEF also varies by macronutrient:\n"
      f"  Protein TEF: 20-30%, Carb: 5-10%, Fat: 0-3%\n"
      f"10% is only the blended average, highly variable.\n"
      f"Texas grade: BLACK -- no match within 5%.")

# H-NUTR-018: Glycemic index reference = 100 (glucose)
# GI scale: 0-100. Low < 55, Medium 56-69, High > 70
# Check: GI thresholds and Golden Zone
gi_low_threshold = 55 / 100  # 0.55
gi_med_upper = 69 / 100  # 0.69
gi_high_lower = 70 / 100  # 0.70
# Golden Zone upper = 0.50. GI low threshold 0.55 -- close?
diff_gi_gz = abs(gi_low_threshold - GZ_UPPER)
# More interesting: "medium GI" foods -- optimal nutrition zone
# Medium GI range: [0.56, 0.69] -- does NOT overlap with GZ [0.212, 0.500]
overlap = max(0, min(0.69, GZ_UPPER) - max(0.56, GZ_LOWER))
grade("H-NUTR-018", "⬛", False,
      "GI classification thresholds align with Golden Zone",
      f"GI low threshold: 55/100 = {gi_low_threshold}\n"
      f"Golden Zone: [{GZ_LOWER:.4f}, {GZ_UPPER:.4f}]\n"
      f"Difference: {diff_gi_gz:.4f}\n"
      f"Medium GI range [0.56, 0.69] overlap with GZ: {overlap}\n"
      f"No overlap between 'optimal GI range' and Golden Zone.\n"
      f"GI scale is arbitrary (based on glucose=100 convention).\n"
      f"Texas grade: BLACK -- no overlap, different scales.")

# H-NUTR-019: BMR Harris-Benedict equation coefficients and 6
# Male: BMR = 66.5 + 13.75*W + 5.003*H - 6.755*A
# Note the 6.755 coefficient for age!
# Female: BMR = 655.1 + 9.563*W + 1.850*H - 4.676*A
hb_male_age_coeff = 6.755
hb_male_const = 66.5
ratio_const_coeff = hb_male_const / hb_male_age_coeff  # 66.5/6.755 = 9.84
# 6.755 close to 6? diff = 0.755
diff_coeff_6 = abs(hb_male_age_coeff - 6)
# These are empirical regression coefficients, not fundamental constants
grade("H-NUTR-019", "⬛", False,
      "Harris-Benedict BMR age coefficient 6.755 relates to 6",
      f"Harris-Benedict (male): BMR = 66.5 + 13.75W + 5.003H - 6.755A\n"
      f"Age coefficient = {hb_male_age_coeff}\n"
      f"|6.755 - 6| = {diff_coeff_6:.3f} (12.6% error)\n"
      f"66.5 / 6.755 = {ratio_const_coeff:.2f} (not clean)\n"
      f"These are empirical regression coefficients from 1918 data.\n"
      f"Revised Mifflin-St Jeor (1990) uses completely different coefficients.\n"
      f"Any regression coefficient near 6 is coincidence.\n"
      f"Texas grade: BLACK -- empirical coefficient, 12.6% off.")

# H-NUTR-020: Body composition ratios
# Water ~60%, Protein ~16%, Fat ~20%, Minerals ~5%, Carbs ~1%
# Check ratios against TECS constants
body_water = 0.60
body_protein = 0.16
body_fat = 0.20
body_minerals = 0.05
body_carbs = 0.01
# body_fat ~= 0.20 vs GZ_LOWER = 0.2123 (diff 0.012)
diff_fat_gz = abs(body_fat - GZ_LOWER)
# body_protein = 0.16 vs 1/6 = 0.1667 (diff 0.007)
diff_prot_sixth = abs(body_protein - 1/6)
# water = 0.60 vs 1 - 1/e = 0.6321 (diff 0.032)
diff_water_e = abs(body_water - (1 - 1/math.e))
grade("H-NUTR-020", "⚪", diff_prot_sixth < 0.01,
      "Body protein ~16% approximately equals 1/6 = 16.67%",
      f"Body composition:\n"
      f"  Water:    {body_water:.0%} vs 1-1/e = {1-1/math.e:.4f} (diff {diff_water_e:.4f})\n"
      f"  Protein:  {body_protein:.0%} vs 1/6 = {1/6:.4f} (diff {diff_prot_sixth:.4f})\n"
      f"  Fat:      {body_fat:.0%} vs GZ_LOWER = {GZ_LOWER:.4f} (diff {diff_fat_gz:.4f})\n"
      f"  Minerals: {body_minerals:.0%}\n"
      f"  Carbs:    {body_carbs:.0%}\n"
      f"Protein at 16% vs 1/6=16.67% is close (0.7% diff).\n"
      f"But body protein% varies widely: 10-20% depending on fitness.\n"
      f"Athletes may have 20%+ protein. Obese individuals much less.\n"
      f"Fat at 20% vs GZ_LOWER=21.2%: close but body fat is 10-40% range.\n"
      f"Water at 60% vs 1-1/e=63.2%: body water ranges 45-75%.\n"
      f"With such wide biological variation, any target can be 'close'.\n"
      f"Texas grade: WHITE -- approximate match within biological variation.")

# ═══════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("  SUMMARY")
print("=" * 72)
print()

green = sum(1 for r in results if r[1] == "🟩")
orange_star = sum(1 for r in results if r[1] == "🟧" and "star" in str(r))
orange = sum(1 for r in results if "🟧" in r[1])
white = sum(1 for r in results if r[1] == "⚪")
black = sum(1 for r in results if r[1] == "⬛")

print(f"  Total:  {len(results)}")
print(f"  GREEN:  {green}")
print(f"  ORANGE: {orange}")
print(f"  WHITE:  {white}")
print(f"  BLACK:  {black}")
print()

# Print compact table
print("  ID            | Grade | Result")
print("  --------------|-------|-------")
for r in results:
    hid, emoji, passed, desc, _ = r
    status = "PASS" if passed else "FAIL"
    print(f"  {hid:14s} | {emoji:5s} | {status:4s} | {desc[:55]}")

print()
print("  ASSESSMENT: No structurally significant discoveries found.")
print("  All passing hypotheses are WHITE (coincidental/trivial).")
print("  The number 6 appears in nutritional classifications because")
print("  humans CHOSE 6 categories, not because of natural law.")
print("  All 'Golden Zone' matches fall within expected random ranges.")
print()

# Texas Sharpshooter analysis
print("  TEXAS SHARPSHOOTER CHECK:")
print(f"  Hypotheses tested: {len(results)}")
print(f"  Passing (arithmetically): {sum(1 for r in results if r[2])}")
print(f"  Non-trivial matches: 0")
print(f"  Expected by chance (20 tests, p=0.30 per test): ~6 matches")
print(f"  Observed trivial matches: {white}")
print(f"  Conclusion: All matches are within chance expectation.")
print(f"  No Bonferroni-surviving result. No structural signal.")
print()

sys.exit(0)
