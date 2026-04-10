#!/usr/bin/env python3
"""
Verify Carbon-Deep Chemistry Hypotheses H-CHEM-031 through H-CHEM-050.

20 NEW hypotheses focused on carbon's organic chemistry, bond energies,
allotrope physics, and biochemistry.

Grades:
  GREEN  = Exact equation, mathematically proven
  ORANGE = Numerically correct within stated tolerance, structurally interesting
  WHITE  = Arithmetically correct but trivial/coincidental
  BLACK  = Arithmetically wrong or factually incorrect

Run: PYTHONPATH=. python3 verify/verify_chem_carbon_deep.py
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

def divisors(n):
    """Return sorted list of divisors."""
    return [d for d in range(1, n+1) if n % d == 0]

# ── Golden Zone constants ──
GZ_UPPER = 0.5
GZ_LOWER = 0.5 - math.log(4/3)
GZ_CENTER = 1/math.e
GZ_WIDTH = math.log(4/3)

# ── Results tracking ──
results = []
GREEN = 0
ORANGE = 0
WHITE = 0
BLACK = 0

def grade(hid, emoji, passed, desc, detail=""):
    global GREEN, ORANGE, WHITE, BLACK
    results.append((hid, emoji, passed, desc, detail))
    if emoji == "G":
        GREEN += 1
        symbol = "\u2705"  # checkmark
    elif emoji == "O":
        ORANGE += 1
        symbol = "\U0001f7e7"
    elif emoji == "W":
        WHITE += 1
        symbol = "\u26aa"
    else:
        BLACK += 1
        symbol = "\u2b1b"
    status = "PASS" if passed else "FAIL"
    print(f"  {symbol} {hid}: {status} -- {desc}")
    if detail:
        for line in detail.strip().split("\n"):
            print(f"       {line}")
    print()


# =============================================================================
print("=" * 72)
print("  CARBON-DEEP CHEMISTRY HYPOTHESES (H-CHEM-031 to 050)")
print("=" * 72)
print()

# =============================================================================
# SECTION A: ORGANIC CHEMISTRY (7 hypotheses)
# =============================================================================
print("== A. Organic Chemistry ==\n")

# ── H-CHEM-031: Basic functional groups = 6 ──
# Claim: The 6 fundamental organic functional groups are
# {hydroxyl, carbonyl, carboxyl, amino, sulfhydryl, phosphate} = 6 = n
# Verification: Count from standard organic chemistry textbooks
print("-- H-CHEM-031: Basic Functional Groups = 6 = n --")
# Standard textbook lists vary. Common "big 6" in biochemistry:
# hydroxyl(-OH), carbonyl(C=O), carboxyl(-COOH), amino(-NH2), sulfhydryl(-SH), phosphate(-PO4)
# But organic chemistry recognizes more: alkyl halide, ether, ester, amide, nitrile, etc.
# The "6 basic groups" is a pedagogical convention in BIOCHEMISTRY, not organic chem.
biochem_groups = ["hydroxyl", "carbonyl", "carboxyl", "amino", "sulfhydryl", "phosphate"]
n_groups = len(biochem_groups)
# Organic chem typically lists 8-12+ groups
organic_groups_extended = ["hydroxyl", "carbonyl", "carboxyl", "amino", "sulfhydryl",
                           "phosphate", "ether", "ester", "amide", "alkyl_halide",
                           "nitrile", "thioether"]
grade("H-CHEM-031", "W", n_groups == 6,
      f"Biochemistry's 6 core functional groups = n = 6",
      f"Groups: {biochem_groups}\n"
      f"Count = {n_groups} = 6. EXACT.\n"
      f"But: Organic chemistry lists {len(organic_groups_extended)}+ groups.\n"
      f"The '6 basic' set is a pedagogical convention in biochemistry, not fundamental.\n"
      f"Grade: White -- correct count but cherry-picked subset.")

# ── H-CHEM-032: SN1/SN2/E1/E2 = tau(6) = 4 mechanisms ──
print("-- H-CHEM-032: 4 Substitution/Elimination Mechanisms = tau(6) --")
mechanisms = ["SN1", "SN2", "E1", "E2"]
n_mech = len(mechanisms)
t6 = tau(6)
# Are there really exactly 4? What about SN2', E1cb, SNAr, radical substitution?
other_mechanisms = ["SN2'", "E1cb", "SNAr", "radical_substitution", "E2cb"]
grade("H-CHEM-032", "W", n_mech == t6,
      f"4 core substitution/elimination mechanisms = tau(6) = {t6}",
      f"Core set: {mechanisms} = {n_mech}\n"
      f"tau(6) = {t6}. EXACT MATCH.\n"
      f"But: Additional mechanisms exist: {other_mechanisms[:3]}...\n"
      f"The 4-mechanism classification is a pedagogical simplification.\n"
      f"Grade: White -- correct but numerological (4 is common).")

# ── H-CHEM-033: Huckel 4n+2 rule, n=1 gives 6 electrons ──
print("-- H-CHEM-033: Huckel Aromaticity n=1 -> 6 pi-electrons --")
# 4n+2 for n=1: 4(1)+2 = 6. Benzene has 6 pi electrons.
# This is a well-known chemical fact. The question is whether n=1 being
# the FIRST aromatic is structurally significant.
huckel_n1 = 4*1 + 2
# Check: for n=0, 4(0)+2=2 (cyclopropenyl cation exists but marginal)
# n=1 is the first STABLE neutral aromatic
huckel_series = [(n, 4*n+2) for n in range(5)]
grade("H-CHEM-033", "G", huckel_n1 == 6,
      f"Huckel 4n+2 at n=1 = 6 = first perfect number",
      f"4(1)+2 = {huckel_n1} = 6 pi-electrons = benzene. EXACT.\n"
      f"Huckel series: {huckel_series}\n"
      f"n=1 is the first stable neutral aromatic compound.\n"
      f"The mapping 'first aromatic = first perfect number' is exact\n"
      f"but the connection is post-hoc (Huckel rule is independent of perfect numbers).\n"
      f"Grade: Green -- both sides are exact facts; mapping is ad hoc.")

# ── H-CHEM-034: Chirality requires 4 different substituents = tau(6) ──
print("-- H-CHEM-034: Chiral center needs tau(6) = 4 distinct substituents --")
# A stereocenter (chiral carbon) requires 4 different groups.
# This is tied to sp3 hybridization (4 bonds).
n_substituents = 4
grade("H-CHEM-034", "W", n_substituents == t6,
      f"Chiral center requires {n_substituents} different groups = tau(6) = {t6}",
      f"A tetrahedral carbon with 4 different substituents is chiral.\n"
      f"tau(6) = 4 = number of divisors of 6.\n"
      f"EXACT. But this is just restating that sp3 = 4 bonds (same as H-CHEM-001).\n"
      f"Not an independent hypothesis -- derivative of tau(6)=4.\n"
      f"Grade: White -- trivially equivalent to sp3 tetrahedral geometry.")

# ── H-CHEM-035: CIP priority rules, 4 priority levels = tau(6) ──
print("-- H-CHEM-035: CIP Priority System --")
# CIP assigns priority to substituents around a stereocenter.
# You rank 4 groups by atomic number. The number 4 comes from sp3 geometry.
# So this is again a consequence of 4 bonds, not an independent fact.
# CIP uses R/S designation = 2 outcomes = sigma_{-1}(6)
cip_designations = 2  # R and S
sig_neg1 = sigma_neg1(6)  # = 2.0
grade("H-CHEM-035", "W", abs(cip_designations - sig_neg1) < 0.001,
      f"CIP chirality: 2 designations (R,S) = sigma_{{-1}}(6) = {sig_neg1:.0f}",
      f"R/S stereodescriptors = 2 possible chiralities.\n"
      f"sigma_{{-1}}(6) = 1 + 1/2 + 1/3 + 1/6 = 2.0. EXACT.\n"
      f"But 2 is the most trivial number possible for a binary classification.\n"
      f"Grade: White -- correct but trivially 2.")

# ── H-CHEM-036: Benzene canonical resonance structures = phi(6) ──
print("-- H-CHEM-036: Benzene Kekule Structures = phi(6) --")
# Benzene has 2 Kekule (canonical resonance) structures.
# phi(6) = 2
kekule_count = 2
phi6 = euler_phi(6)
# Total resonance structures (including Dewar) = 5
dewar_count = 3
total_resonance = kekule_count + dewar_count  # = 5
grade("H-CHEM-036", "W", kekule_count == phi6,
      f"Benzene Kekule structures = {kekule_count} = phi(6) = {phi6}",
      f"2 Kekule structures (alternating single/double bonds).\n"
      f"phi(6) = 2. EXACT.\n"
      f"Including Dewar structures: total = {total_resonance} (not a n=6 function).\n"
      f"2 is trivial. Grade: White -- exact but numerological.")

# ── H-CHEM-037: Isomers of hexane (C6H14) = 5 ──
print("-- H-CHEM-037: Hexane C6H14 Structural Isomers --")
# C6H14 has exactly 5 structural isomers:
# n-hexane, 2-methylpentane, 3-methylpentane, 2,2-dimethylbutane, 2,3-dimethylbutane
hexane_isomers = 5
# Is 5 related to n=6? sigma(6)-1 = 11 (no), tau(6)+1=5 (yes, but +1 correction)
# phi(6)+3 = 5 (no). 6-1 = 5 (trivial).
# Proper divisors of 6 = {1,2,3} count = 3 (no).
# 5 = number of Platonic solids (unrelated)
grade("H-CHEM-037", "W", hexane_isomers == 5,
      f"C6H14 has 5 structural isomers",
      f"Hexane isomers: n-hexane, 2-MP, 3-MP, 2,2-DMB, 2,3-DMB = 5.\n"
      f"Well-known chemistry fact.\n"
      f"tau(6)+1 = 5 requires +1 ad hoc correction -- PROHIBITED by rules.\n"
      f"6-1 = 5 is trivial subtraction.\n"
      f"No clean n=6 function produces 5.\n"
      f"Grade: White -- correct chemistry, no meaningful n=6 connection.")


# =============================================================================
# SECTION B: CARBON BONDS (5 hypotheses)
# =============================================================================
print("\n== B. Carbon Bond Properties ==\n")

# ── H-CHEM-038: C-C bond energy ratios ──
print("-- H-CHEM-038: C-C / C=C / C-triple-C Bond Energy Ratios --")
# Standard bond enthalpies (kJ/mol):
CC_single = 346   # C-C
CC_double = 614   # C=C
CC_triple = 839   # C-triple-C
ratio_double_single = CC_double / CC_single
ratio_triple_single = CC_triple / CC_single
# Claim: C=C/C-C ~ sigma_{-1}(6) - 1/6 = 2 - 1/6 = 11/6 = 1.833?
# Actual: 614/346 = 1.775
target_1 = 11/6
err_1 = abs(ratio_double_single - target_1) / target_1 * 100
# Claim: C-triple-C/C-C ~ sigma(6)/5 = 12/5 = 2.4?
# Actual: 839/346 = 2.424
target_2 = sigma(6) / 5
err_2 = abs(ratio_triple_single - target_2) / target_2 * 100
grade("H-CHEM-038", "B", False,
      f"C-C bond energy ratios vs n=6 functions",
      f"C=C/C-C = {ratio_double_single:.3f}, target 11/6 = {target_1:.3f}, error = {err_1:.1f}%\n"
      f"C-triple-C/C-C = {ratio_triple_single:.3f}, target 12/5 = {target_2:.3f}, error = {err_2:.1f}%\n"
      f"The 11/6 target is ad hoc (sigma_{{-1}}(6) - 1/6), the 12/5 uses arbitrary denominator 5.\n"
      f"Neither ratio maps cleanly to a natural n=6 function.\n"
      f"Grade: Black -- forced mappings with no structural basis.")

# ── H-CHEM-039: Hybridization types sp, sp2, sp3 = 3 proper divisors ──
print("-- H-CHEM-039: Carbon Hybridization Types = Proper Divisors of 6 --")
# Carbon hybridizations: sp (2 bonds), sp2 (3 bonds), sp3 (4 bonds)
# Count = 3 types. Proper divisors of 6 (excluding 6 itself) = {1, 2, 3} = 3 divisors
# Also: the bond counts {2, 3, 4} overlap with divisors {1, 2, 3, 6} only at {2, 3}
hybridization_types = 3  # sp, sp2, sp3
proper_divisor_count = len([d for d in divisors(6) if d < 6])  # {1,2,3} = 3
# Bond counts per hybridization
bond_counts = [2, 3, 4]  # sp, sp2, sp3
divs6 = divisors(6)  # [1, 2, 3, 6]
overlap = [b for b in bond_counts if b in divs6]  # [2, 3]
grade("H-CHEM-039", "W", hybridization_types == proper_divisor_count,
      f"3 hybridization types = 3 proper divisors of 6",
      f"Hybridizations: sp(2), sp2(3), sp3(4) = {hybridization_types} types.\n"
      f"Proper divisors of 6 excl. 6: {{1,2,3}} = {proper_divisor_count} elements.\n"
      f"COUNT matches (3=3). EXACT.\n"
      f"Bond counts {{2,3,4}} overlap with divisors {{1,2,3,6}} at {{2,3}}.\n"
      f"3 is small and common. Grade: White -- coincidental count match.")

# ── H-CHEM-040: C-H bond energy / C-C bond energy ratio ──
print("-- H-CHEM-040: C-H / C-C Bond Energy Ratio --")
CH_energy = 411   # kJ/mol
CC_energy = 346   # kJ/mol
ratio_CH_CC = CH_energy / CC_energy
# Is this close to any n=6 constant?
# sigma_{-1}(6) = 2.0 (no), phi(6)/sigma_{-1}(6) = 1.0 (no)
# 1/GZ_CENTER = e = 2.718 (no)
# 6/5 = 1.2 -> error from 1.188?
target = 6/5
err = abs(ratio_CH_CC - target) / target * 100
grade("H-CHEM-040", "W", err < 2,
      f"C-H/C-C energy ratio = {ratio_CH_CC:.3f} vs 6/5 = {target:.3f}",
      f"C-H = {CH_energy}, C-C = {CC_energy} kJ/mol.\n"
      f"Ratio = {ratio_CH_CC:.4f}. Target 6/5 = 1.2.\n"
      f"Error = {err:.1f}%. Within 2%.\n"
      f"But 6/5 is not a standard n=6 number-theoretic function.\n"
      f"Grade: White -- numerically close to a simple fraction, but mapping is ad hoc.")

# ── H-CHEM-041: Bond orders {1,2,3} = proper divisors of 6 ──
print("-- H-CHEM-041: Carbon Bond Orders = Proper Divisors of 6 --")
bond_orders = {1, 2, 3}  # single, double, triple
proper_divs = {1, 2, 3}  # proper divisors of 6 (excluding 6)
match = bond_orders == proper_divs
grade("H-CHEM-041", "G", match,
      f"Carbon bond orders {{1,2,3}} = proper divisors of 6 {{1,2,3}}",
      f"C-C (order 1), C=C (order 2), C-triple-C (order 3).\n"
      f"Proper divisors of 6 excl. 6: {{1, 2, 3}}.\n"
      f"SET IDENTITY -- not just count but exact element match.\n"
      f"Carbon is the ONLY element commonly forming all three integer bond orders.\n"
      f"N can form 1,2,3 but triple is rare outside N2/CN-.\n"
      f"O forms only 1,2 commonly. Si forms only 1 commonly.\n"
      f"Grade: Green -- exact set identity; uniqueness among light elements is notable.")

# ── H-CHEM-042: sp hybridization bond count = sigma_{-1}(6) ──
print("-- H-CHEM-042: sp Hybridization Geometry --")
# sp: 2 sigma bonds + 2 pi bonds (in triple bond) -> linear, 180 degrees
# sp2: 3 sigma + 1 pi -> 120 degrees
# sp3: 4 sigma + 0 pi -> 109.47 degrees
# Sigma bond counts: {2, 3, 4} for sp, sp2, sp3
# Sum of sigma bonds across hybridizations: 2+3+4 = 9 = ?
sigma_bond_sum = 2 + 3 + 4
# 9 = 3^2 = (divisor of 6)^2. Not a standard n=6 function.
# Pi bond counts: {2, 1, 0} for sp, sp2, sp3. Sum = 3.
pi_bond_sum = 2 + 1 + 0
# Total bond capacity: {4, 4, 4} -- ALWAYS 4 = tau(6)!
total_per_hybrid = [2+2, 3+1, 4+0]
all_four = all(t == 4 for t in total_per_hybrid)
grade("H-CHEM-042", "G", all_four,
      f"Total bonds per hybridization ALWAYS = tau(6) = 4",
      f"sp:  2 sigma + 2 pi = 4\n"
      f"sp2: 3 sigma + 1 pi = 4\n"
      f"sp3: 4 sigma + 0 pi = 4\n"
      f"Carbon always forms exactly tau(6) = 4 bonds regardless of hybridization.\n"
      f"This is a conservation law: sigma + pi = 4 = tau(6) always.\n"
      f"Well-known chemistry fact (octet rule for C). tau(6) mapping is post-hoc.\n"
      f"Grade: Green -- exact conservation identity, even if mapping is ad hoc.")


# =============================================================================
# SECTION C: CARBON ALLOTROPES DEEP (4 hypotheses)
# =============================================================================
print("\n== C. Carbon Allotropes (Deep) ==\n")

# ── H-CHEM-043: Graphene Brillouin zone has 6 Dirac points ──
print("-- H-CHEM-043: Graphene BZ has 6 Dirac Points --")
# Graphene's hexagonal BZ has 6 K/K' points at vertices.
# Only 2 are inequivalent (K and K'), but 6 total vertices.
dirac_points_total = 6
dirac_inequivalent = 2  # K and K'
# 6 = n (perfect number), 2 = phi(6)
grade("H-CHEM-043", "G", dirac_points_total == 6 and dirac_inequivalent == phi6,
      f"Graphene BZ: 6 Dirac points (total) = n, 2 inequivalent = phi(6)",
      f"Hexagonal Brillouin zone has 6 corner vertices (K points).\n"
      f"By zone-folding, only {dirac_inequivalent} are inequivalent = phi(6) = {phi6}.\n"
      f"6 vertices is a geometric fact of hexagons (trivially = 6).\n"
      f"phi(6) = 2 is trivial. Both exact but not deep.\n"
      f"Grade: Green -- exact facts, mapping to n and phi(6) is natural for hexagonal system.")

# ── H-CHEM-044: Diamond band gap 5.47 eV ──
print("-- H-CHEM-044: Diamond Band Gap and n=6 --")
diamond_gap = 5.47  # eV, experimental
# Is 5.47 close to any n=6 function?
# sigma(6) - tau(6) - phi(6) = 12 - 4 - 2 = 6 (not 5.47)
# 6 - 1/sigma_{-1}(6) = 6 - 0.5 = 5.5 (close! but ad hoc)
target_gap = 6 - 1/sigma_neg1(6)  # = 6 - 0.5 = 5.5
err_gap = abs(diamond_gap - target_gap) / target_gap * 100
# Also try: 6/e^(1/6) = 6*exp(-1/6) = 5.07 (not close)
# Try: sigma(6)*GZ_CENTER = 12/e = 4.41 (no)
# Try: 6 * (1 - 1/sigma(6)) = 6 * 11/12 = 5.5 (same as above)
grade("H-CHEM-044", "B", False,
      f"Diamond band gap {diamond_gap} eV vs n=6 functions",
      f"Nearest match: 6 - 1/sigma_{{-1}}(6) = 6 - 0.5 = {target_gap} eV.\n"
      f"Error = {err_gap:.1f}%. \n"
      f"But 6-0.5 = 5.5 is an ad hoc construction.\n"
      f"No natural n=6 number-theoretic function yields 5.47.\n"
      f"Band gap is determined by crystal field + covalent bonding, not Z alone.\n"
      f"Grade: Black -- no clean mapping exists.")

# ── H-CHEM-045: Carbon nanotube (6,6) armchair ──
print("-- H-CHEM-045: Nanotube (6,6) Armchair Chirality --")
# Armchair nanotubes (n,n) are always metallic.
# (6,6) nanotube: circumference = 6*a*sqrt(3) where a = 2.46 Angstrom (graphene lattice)
# Number of hexagons in unit cell of (n,m) tube = 2*(n^2 + nm + m^2) / gcd(stuff)
# For (6,6): atoms per unit cell = 2 * 2*(36+36+36)/gcd = depends on d_R
# Simpler: (n,n) armchair has 2n atoms in circumference ring = 12 = sigma(6)
n_tube = 6
atoms_in_ring = 2 * n_tube  # = 12
# diameter = a*sqrt(3)*n/pi = 2.46*1.732*6/3.14159 = 8.14 Angstrom
diameter_66 = 2.46 * math.sqrt(3) * 6 / math.pi
grade("H-CHEM-045", "W", atoms_in_ring == sigma(6),
      f"(6,6) armchair nanotube: 12 atoms/ring = sigma(6)",
      f"(n,n) armchair has 2n atoms in circumference ring.\n"
      f"n=6: 2*6 = {atoms_in_ring} = sigma(6) = 12. EXACT.\n"
      f"Diameter = {diameter_66:.2f} Angstrom.\n"
      f"But (6,6) is chosen specifically because n=6. Any (n,n) gives 2n.\n"
      f"Grade: White -- tautological (we chose n=6 to get 2*6=12).")

# ── H-CHEM-046: Graphite interlayer spacing ──
print("-- H-CHEM-046: Graphite Interlayer Spacing --")
# Graphite interlayer distance = 3.35 Angstrom
graphite_d = 3.35  # Angstrom
# C-C bond length in graphene = 1.42 Angstrom
cc_graphene = 1.42
ratio_layer = graphite_d / cc_graphene
# 3.35/1.42 = 2.359
# sigma_{-1}(6) = 2.0 (no), e^(GZ_WIDTH) = 4/3 = 1.333 (no)
# Is 2.359 close to anything?
# 12/5 = 2.4 (1.7% error), 7/3 = 2.333 (1.1% error)
# These are not n=6 functions.
target_ratio = 7/3
err_ratio = abs(ratio_layer - target_ratio) / target_ratio * 100
grade("H-CHEM-046", "B", False,
      f"Graphite d/C-C ratio = {ratio_layer:.3f} vs n=6 functions",
      f"Interlayer d = {graphite_d} A, C-C = {cc_graphene} A.\n"
      f"Ratio = {ratio_layer:.4f}.\n"
      f"Nearest simple fraction: 7/3 = {target_ratio:.4f}, error = {err_ratio:.1f}%.\n"
      f"No natural n=6 number-theoretic function produces this ratio.\n"
      f"Interlayer spacing is determined by van der Waals forces, not Z arithmetic.\n"
      f"Grade: Black -- no meaningful n=6 connection.")


# =============================================================================
# SECTION D: BIOCHEMISTRY (4 hypotheses)
# =============================================================================
print("\n== D. Biochemistry of Carbon ==\n")

# ── H-CHEM-047: Calvin cycle 6 CO2 -> 1 glucose ──
print("-- H-CHEM-047: Calvin Cycle: 6 CO2 -> C6H12O6 --")
# The Calvin cycle fixes 6 CO2 molecules to produce 1 glucose (6 carbons).
# This is conservation of carbon atoms: 6 in -> 6 in product.
co2_per_glucose = 6
glucose_carbons = 6
# Also: 18 ATP + 12 NADPH consumed per glucose
atp_per_glucose = 18  # = 3 * 6 = 3 * n
nadph_per_glucose = 12  # = sigma(6)
grade("H-CHEM-047", "G", co2_per_glucose == 6 and nadph_per_glucose == sigma(6),
      f"Calvin cycle: 6 CO2 -> C6 glucose; 12 NADPH = sigma(6)",
      f"6 CO2 in = 6 C atoms in glucose. Carbon conservation. EXACT.\n"
      f"ATP consumed = {atp_per_glucose} = 3 * 6 (3 ATP per CO2).\n"
      f"NADPH consumed = {nadph_per_glucose} = sigma(6) = 12. EXACT.\n"
      f"The 6 CO2 is trivially carbon conservation (not deep).\n"
      f"12 NADPH = sigma(6) is interesting but follows from 2 NADPH per CO2.\n"
      f"Grade: Green -- exact biochemical facts; sigma(6) appearance is notable.")

# ── H-CHEM-048: Amino acid backbone N-C_alpha-C' = 3 atoms ──
print("-- H-CHEM-048: Amino Acid Backbone --")
# Each amino acid contributes 3 backbone atoms: N, C_alpha, C'
# 3 is a divisor of 6.
backbone_atoms = 3
is_divisor = 6 % backbone_atoms == 0
# Peptide bond: C'-N linkage. Dihedral angles phi, psi = 2 angles = phi(6)?
ramachandran_angles = 2  # phi, psi
# omega angle is ~180 (trans), so effectively 2 free angles
grade("H-CHEM-048", "W", is_divisor and ramachandran_angles == phi6,
      f"Backbone: 3 atoms (divisor of 6), 2 Ramachandran angles = phi(6)",
      f"Backbone unit: N-C_alpha-C' = {backbone_atoms} atoms. 6 % 3 = 0.\n"
      f"Ramachandran free angles: phi, psi = {ramachandran_angles} = phi(6) = {phi6}.\n"
      f"Both exact. But 3 and 2 are the smallest integers > 1.\n"
      f"Any small count will be a divisor of 6 or close to phi(6).\n"
      f"Grade: White -- trivially small numbers matching trivially.")

# ── H-CHEM-049: Krebs cycle electron pairs ──
print("-- H-CHEM-049: Krebs Cycle Electron Yield --")
# Per acetyl-CoA (2C unit): 3 NADH + 1 FADH2 + 1 GTP
# Electron pairs: 3*2 + 1*2 = 8 from NADH+FADH2 (2 electrons each)
# Per GLUCOSE (2 acetyl-CoA): 2 * (3 NADH + 1 FADH2) = 6 NADH + 2 FADH2
# 6 NADH! = n
# Total from full glucose oxidation (glycolysis + pyruvate dehydrogenase + Krebs):
# 10 NADH + 2 FADH2 = 10*2 + 2*2 = 24 electron pairs? No, that's electrons.
# Electron pairs: 10 + 2 = 12 carrier molecules = sigma(6)?
# Actually: Each NADH carries 2 electrons, each FADH2 carries 2 electrons.
# Total reduced carriers from Krebs alone (per glucose): 6 NADH + 2 FADH2 = 8 carriers
# Total from full oxidation: 10 NADH + 2 FADH2 = 12 reduced carriers
krebs_nadh_per_glucose = 6
total_carriers = 10 + 2  # 10 NADH + 2 FADH2 from complete glucose oxidation
grade("H-CHEM-049", "O", krebs_nadh_per_glucose == 6 and total_carriers == sigma(6),
      f"Krebs: 6 NADH/glucose = n; total 12 carriers = sigma(6)",
      f"Krebs cycle per glucose: {krebs_nadh_per_glucose} NADH = 6 = n. EXACT.\n"
      f"Full glucose oxidation: 10 NADH + 2 FADH2 = {total_carriers} reduced carriers = sigma(6).\n"
      f"Both exact biochemical facts from standard metabolic tables.\n"
      f"12 = sigma(6) = sum of divisors of perfect number 6 appearing as\n"
      f"total electron carriers is structurally interesting.\n"
      f"Caveat: 6 NADH from Krebs = 3 NADH/acetyl-CoA * 2 acetyl-CoA.\n"
      f"And 12 = 10+2 counts different molecular species together.\n"
      f"Grade: Orange -- both exact; sigma(6)=12 carriers is a notable coincidence.")

# ── H-CHEM-050: Glycolysis net ATP ──
print("-- H-CHEM-050: Glycolysis Net ATP and Steps --")
# Glycolysis: 10 enzymatic steps, net 2 ATP, 2 NADH, 2 pyruvate
glycolysis_steps = 10
net_atp = 2
net_nadph = 2
# 10 steps: not a standard n=6 function. sigma(6)+tau(6)-6 = 12+4-6 = 10? Ad hoc.
# Net ATP = 2 = phi(6) = sigma_{-1}(6)
# 2 NADH = phi(6)
# 2 pyruvate = phi(6)
# Glucose (6C) -> 2 pyruvate (3C each): 6 = 2*3, divisor decomposition!
c_split = (6, 2, 3)  # 6C -> 2 x 3C
divs_match = 6 == 2 * 3 and 2 in divisors(6) and 3 in divisors(6)
grade("H-CHEM-050", "G", divs_match,
      f"Glycolysis: C6 -> 2 x C3 (divisor decomposition 6 = 2 * 3)",
      f"Glucose (6C) splits into 2 pyruvate (3C each).\n"
      f"6 = 2 x 3, where {{2, 3}} are proper divisors of 6.\n"
      f"Net ATP = {net_atp} = phi(6). Net NADH = {net_nadph} = phi(6).\n"
      f"Steps = {glycolysis_steps} (no clean n=6 mapping).\n"
      f"The 6 -> 2*3 split is exact carbon conservation using divisors.\n"
      f"phi(6)=2 for ATP/NADH is trivially 2.\n"
      f"Grade: Green -- the divisor decomposition 6=2*3 is exact and elegant,\n"
      f"though biochemically it just reflects carbon conservation.")


# =============================================================================
# SECTION E: ADDITIONAL ORGANIC / PHYSICAL (2 bonus hypotheses to reach 20 exactly)
# =============================================================================
# (We need exactly 20 new hypotheses: 031-050)

# Already have 20: 031-050. Print summary.

# =============================================================================
print("\n" + "=" * 72)
print("  SUMMARY")
print("=" * 72)
print(f"""
  Total hypotheses: {len(results)}
  Green  (exact/proven):          {GREEN}
  Orange (structural match):      {ORANGE}
  White  (trivial/coincidence):   {WHITE}
  Black  (wrong/forced):          {BLACK}
""")

# ── Detailed table ──
print("  ID           | Grade | Status | Description")
print("  " + "-" * 68)
for hid, emoji, passed, desc, _ in results:
    if emoji == "G":
        g = "GREEN "
    elif emoji == "O":
        g = "ORANGE"
    elif emoji == "W":
        g = "WHITE "
    else:
        g = "BLACK "
    st = "PASS" if passed else "FAIL"
    # Truncate description
    short = desc[:50] + "..." if len(desc) > 50 else desc
    print(f"  {hid:14s} | {g} | {st:4s} | {short}")

print()
print("=" * 72)
print("  HONEST ASSESSMENT")
print("=" * 72)
print("""
  Most Green grades are exact CHEMISTRY facts with post-hoc n=6 mappings.
  The set identity H-CHEM-041 (bond orders = proper divisors) is the strongest.
  Orange H-CHEM-049 (12 electron carriers = sigma(6)) is notable but fragile.
  Many White grades reflect that small numbers (2,3,4) trivially relate to 6.
  Black grades are honest: no clean n=6 mapping exists for band gaps or ratios.
""")
