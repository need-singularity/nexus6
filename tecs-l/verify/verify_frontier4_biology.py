#!/usr/bin/env python3
"""
verify_frontier4_biology.py — Verify 20 biology/chemistry hypotheses (H-BIO-301..320)
against n=6 arithmetic functions.

n=6 arithmetic:
  sigma(6)=12, tau(6)=4, phi(6)=2, sopfr(6)=5, omega(6)=2, sigma*phi=24
"""

import math

# ─── n=6 constants ───
N = 6
SIGMA = 12        # sum of divisors
TAU = 4           # number of divisors
PHI = 2           # Euler totient
SOPFR = 5         # sum of prime factors with multiplicity (2+3)
OMEGA = 2         # number of distinct prime factors
SIGMA_PHI = SIGMA * PHI  # 24

CONST_MAP = {
    "n": N,
    "sigma": SIGMA,
    "tau": TAU,
    "phi": PHI,
    "sopfr": SOPFR,
    "omega": OMEGA,
    "sigma*phi": SIGMA_PHI,
    "n^2": N**2,
}

SEP = "=" * 78


def header(hid, title):
    print(f"\n{SEP}")
    print(f"  {hid}: {title}")
    print(SEP)


def fact(label, value, note=""):
    tag = f"  [FACT] {label} = {value}"
    if note:
        tag += f"  ({note})"
    print(tag)


def match(label, value, const_name):
    target = CONST_MAP[const_name]
    ok = (value == target) if isinstance(value, int) else math.isclose(value, target, rel_tol=0.05)
    status = "MATCH" if ok else "MISMATCH"
    sym = "v" if ok else "X"
    print(f"  [{sym}] {label} = {value}  ->  {const_name}={target}  [{status}]")
    return ok


def match_approx(label, value, target, target_name, tol=0.1):
    ok = math.isclose(value, target, rel_tol=tol)
    status = "APPROX MATCH" if ok else "MISMATCH"
    sym = "~" if ok else "X"
    print(f"  [{sym}] {label} = {value}  ~  {target_name}={target}  [{status}]")
    return ok


def grade(stars, texas):
    labels = {3: "***  (exact, structural)", 2: "**   (exact, some selection)", 1: "*    (approximate or cherry-picked)"}
    print(f"  GRADE:       {'*' * stars}  {labels[stars]}")
    print(f"  TEXAS RISK:  {texas}")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-301: Photosynthesis equation
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-301", "Photosynthesis 6CO2 + 6H2O -> C6H12O6 + 6O2")

print("\n  Balanced equation: 6CO2 + 6H2O -> C6H12O6 + 6O2")
print("  Stoichiometric coefficients: 6, 6, 1, 6")
print("  Glucose subscripts (atoms): C=6, H=12, O=6")

fact("Reactant coefficients", "6, 6", "both = n")
fact("Product coefficients", "1, 6", "O2 coeff = n, glucose coeff = 1")
fact("Glucose subscript set", "{6, 12, 6}", "uses n and sigma only")
fact("Glucose subscript sum", 6+12+6, "= 24 = sigma*phi")
fact("Total C atoms each side", 6, "= n")
fact("Total O atoms each side", "6*2 + 6*1 = 18 (left), 6+6+6*2 = 24 (right)")

# Verify atom balance
print("\n  Atom balance check:")
# Left: 6CO2 + 6H2O => C:6, O:12+6=18, H:12
# Right: C6H12O6 + 6O2 => C:6, H:12, O:6+12=18
fact("C left/right", "6/6", "balanced")
fact("H left/right", "12/12", "balanced")
fact("O left/right", "18/18", "balanced")

m1 = match("CO2 coefficient", 6, "n")
m2 = match("H2O coefficient", 6, "n")
m3 = match("O2 coefficient", 6, "n")
m4 = match("Glucose C subscript", 6, "n")
m5 = match("Glucose H subscript", 12, "sigma")
m6 = match("Glucose O subscript", 6, "n")
m7 = match("Glucose subscript sum", 24, "sigma*phi")

print()
print("  NOTE: The equation coefficients are {6,6,1,6}, NOT {6,6,6,12,6,6}.")
print("  The subscripts inside glucose are {6,12,6} but those are not coefficients.")
print("  Hypothesis overstates by conflating subscripts with coefficients.")
print("  However, '6' genuinely dominates: 3 of 4 coefficients = 6,")
print("  and glucose subscripts use only n=6 and sigma=12.")
grade(2, "medium — 6 is forced by carbon count, not free parameter")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-302: Benzene C6H6
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-302", "Benzene C6H6: atoms, bonds, pi-electrons")

fact("Carbon atoms", 6)
fact("Hydrogen atoms", 6)
fact("Total atoms", 12)
fact("Pi electrons", 6, "3 double bonds x 2e each")
fact("C-C bonds", 6, "ring")
fact("C-H bonds", 6, "one per carbon")
fact("Total bonds", 12)

m1 = match("C atoms", 6, "n")
m2 = match("H atoms", 6, "n")
m3 = match("Total atoms", 12, "sigma")
m4 = match("Pi electrons", 6, "n")
m5 = match("C-C bonds", 6, "n")
m6 = match("C-H bonds", 6, "n")
m7 = match("Total bonds", 12, "sigma")

print()
print("  NOTE: C6H6 is structurally determined — hexagonal ring requires 6 C.")
print("  H count = C count for monocyclic CnHn. So n=6 => everything follows.")
print("  Still, benzene IS the canonical aromatic, and 6 is special (Huckel 4n+2, n=1).")
grade(2, "medium — all counts derived from ring size 6")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-303: Glucose C6H12O6
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-303", "Glucose C6H12O6: subscript sums")

fact("C subscript", 6)
fact("H subscript", 12)
fact("O subscript", 6)
fact("Total atoms", 6+12+6)

m1 = match("C", 6, "n")
m2 = match("H", 12, "sigma")
m3 = match("O", 6, "n")
m4 = match("Total atoms", 24, "sigma*phi")
m5 = match("Subscript sum", 6+12+6, "sigma*phi")

print()
print("  NOTE: Glucose = C6(H2O)6 = hydrated 6-carbon. H=2*6=12, O=6.")
print("  The 12 and 24 are forced by the aldohexose formula CnH2nOn with n=6.")
print("  sigma=12=2n and sigma*phi=24=4n are just multiples of 6.")
grade(2, "medium — all forced by hexose carbon count")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-304: Glycolysis ATP/NADH
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-304", "Glycolysis: net ATP, gross ATP, NADH")

fact("Net ATP per glucose", 2, "textbook: 4 produced - 2 invested")
fact("Gross ATP produced", 4, "substrate-level phosphorylation")
fact("ATP invested", 2, "hexokinase + PFK-1")
fact("NADH produced", 2)
fact("Pyruvate molecules", 2, "glucose split into 2 x C3")

m1 = match("Net ATP", 2, "phi")
m2 = match("Gross ATP", 4, "tau")
m3 = match("NADH", 2, "phi")
m4 = match("ATP invested", 2, "phi")

print()
print("  NOTE: Glucose (C6) splits into 2 pyruvate (C3). The '2' is 6/3.")
print("  Net ATP=2 is a real biochemical constant. tau=4 for gross ATP is exact.")
print("  But small numbers (2,4) are common; matching phi/tau is easy.")
grade(1, "high — small numbers 2 and 4 match many things")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-305: Theoretical max ATP from glucose oxidation
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-305", "Theoretical ATP yield per glucose = 36 = n^2?")

print("\n  Textbook values vary by source and assumptions:")
fact("Old textbook value", 36, "assuming 3 ATP/NADH, 2 ATP/FADH2")
fact("Old textbook value (alt)", 38, "some texts count 38")
fact("Modern revised estimate", "30-32", "P/O ratios: 2.5 ATP/NADH, 1.5 ATP/FADH2")
fact("Most cited modern", 30, "Biochemistry by Berg et al.")
fact("n^2", 36)

print()
print("  The '36' value comes from older textbooks using integer P/O ratios.")
print("  Modern biochemistry gives ~30-32 ATP (non-integer coupling ratios).")
print("  36 = n^2 matches the OLDER estimate, which is now considered inaccurate.")
m1 = match("Old ATP yield", 36, "n^2")
print()
print("  VERDICT: The matched value (36) is outdated. Modern value is 30-32.")
grade(1, "high — matches outdated number; modern value is 30-32")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-306: Krebs cycle outputs per glucose
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-306", "Krebs cycle: NADH, FADH2, GTP per glucose")

print("\n  Krebs cycle runs TWICE per glucose (2 acetyl-CoA).")
fact("NADH per turn", 3)
fact("FADH2 per turn", 1)
fact("GTP per turn", 1)
fact("CO2 per turn", 2)
fact("Total products per turn", "3+1+1+2=7", "not 5")

fact("NADH per glucose (2 turns)", 6)
fact("FADH2 per glucose", 2)
fact("GTP per glucose", 2)
fact("CO2 per glucose (Krebs only)", 4)

m1 = match("NADH per glucose", 6, "n")
m2 = match("FADH2 per glucose", 2, "phi")
m3 = match("GTP per glucose", 2, "phi")

print()
print("  NOTE: Products per turn = 7 (not 5=sopfr). The hypothesis says 5,")
print("  but actual count is 3 NADH + 1 FADH2 + 1 GTP + 2 CO2 = 7.")
print("  If excluding CO2 (counting only energy carriers): 3+1+1=5=sopfr per turn.")
print("  That selective counting is debatable.")
m4 = match("Energy carriers per turn (selective)", 5, "sopfr")
grade(2, "medium — NADH=6 is solid; 'products=5' requires selective counting")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-307: Circadian rhythm = 24h
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-307", "Circadian: 24h = sigma*phi, clock genes, feedback loops")

fact("Hours in day", 24)
fact("Core clock genes (mammals)", "~10-15", "CLOCK, BMAL1, PER1-3, CRY1-2, REV-ERBa/b, RORa/b/c, etc.")
fact("Core feedback loops", "2-3", "main TTFL + auxiliary loops")

m1 = match("Hours in day", 24, "sigma*phi")

print()
print("  NOTE: 24 hours = Earth's rotation period. This is astronomy, not biology.")
print("  Clock genes: depending on how you count, 6-15. '~6' is cherry-picking.")
print("  Feedback loops: 2-3 depending on definition. Calling it phi=2 is a stretch.")
print("  The 24h match is cute but astronomically determined, not biological.")
grade(1, "high — 24h is astronomical; gene count is cherry-picked")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-308: Icosahedral virus capsid
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-308", "Icosahedral virus: pentamers=12, T=1 subunits=60")

fact("Pentamers (vertices)", 12, "icosahedron has 12 vertices — Euler's formula")
fact("Faces of icosahedron", 20)
fact("Edges of icosahedron", 30)
fact("T=1 capsid subunits", 60, "12 pentamers x 5 subunits each")
fact("sigma * sopfr", SIGMA * SOPFR)

m1 = match("Pentamers", 12, "sigma")
m2 = match("T=1 subunits", 60, "n")  # 60 != 6

print()
print("  Euler formula for convex polyhedra: V - E + F = 2")
print("  Icosahedron: V=12, E=30, F=20. Check: 12-30+20=2. Correct.")
print()
print("  12 pentamers: This is a topological NECESSITY (Euler constraint).")
print("  Any closed surface with hexagons+pentagons needs exactly 12 pentagons.")
print("  (Same reason soccer balls have 12 pentagons.)")
print()
fact("sigma * sopfr", 12*5, "= 60")
m3 = match_approx("T=1 subunits", 60, 60, "sigma*sopfr=60")

print()
print("  NOTE: 12 pentamers is topology (Euler), not biology.")
print("  60 = 12*5 = sigma*sopfr is numerically correct.")
print("  But 60 = icosahedral symmetry group order, a math fact.")
grade(2, "low — 12 pentamers is a proven topological necessity")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-309: Water / Ice hexagonal
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-309", "Water coordination=4, ice hexagonal=6, snowflake arms=6")

fact("Water coordination number", 4, "tetrahedral: 2 H-bond donors + 2 acceptors")
fact("Ice Ih ring size", 6, "hexagonal ice — 6-membered rings")
fact("Snowflake symmetry", 6, "6-fold rotational (C6)")

m1 = match("Water coordination", 4, "tau")
m2 = match("Ice ring size", 6, "n")
m3 = match("Snowflake arms", 6, "n")

print()
print("  NOTE: Water coordination=4 is due to sp3-like geometry (2 lone pairs + 2 bonds).")
print("  Ice hexagonal rings arise from tetrahedral bonding angles (109.5 deg ~ 120 deg).")
print("  6-fold snowflake symmetry is real and well-known crystallography.")
print("  These are physical/chemical facts, not arbitrary.")
grade(2, "medium — tau=4 and n=6 match, but driven by tetrahedral chemistry")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-310: DNA groove dimensions
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-310", "DNA B-form: major groove ~12A, minor ~6A, ratio ~2")

fact("Major groove width (B-DNA)", "11.7 A", "textbook: ~11.6-12.0 A")
fact("Minor groove width (B-DNA)", "5.7 A", "textbook: ~5.7-6.0 A")
fact("Ratio major/minor", round(11.7/5.7, 2))

m1 = match_approx("Major groove", 11.7, 12, "sigma=12", tol=0.05)
m2 = match_approx("Minor groove", 5.7, 6, "n=6", tol=0.06)
m3 = match_approx("Ratio", 11.7/5.7, 2, "phi=2", tol=0.05)

print()
print("  NOTE: Groove widths are ~11.7 and ~5.7 A, close to 12 and 6 but not exact.")
print("  The ratio 11.7/5.7 = 2.05, close to 2.")
print("  These are determined by the 10 bp/turn helical geometry.")
grade(1, "high — approximate match with rounding; physical origin is helix geometry")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-311: Genetic code degeneracy
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-311", "Codon degeneracy: max=6, distinct values={1,2,3,4,6}")

# Standard genetic code degeneracy
# Amino acid : number of codons
degeneracy = {
    'Met': 1, 'Trp': 1,
    'Phe': 2, 'Tyr': 2, 'His': 2, 'Gln': 2, 'Asn': 2, 'Lys': 2,
    'Asp': 2, 'Glu': 2, 'Cys': 2,
    'Ile': 3,
    'Val': 4, 'Pro': 4, 'Thr': 4, 'Ala': 4, 'Gly': 4,
    'Leu': 6, 'Arg': 6, 'Ser': 6,
    'Stop': 3,
}

deg_values = sorted(set(degeneracy.values()))
aa_with_6 = [aa for aa, d in degeneracy.items() if d == 6]

fact("Max degeneracy", max(degeneracy.values()))
fact("AAs with 6 codons", f"{len(aa_with_6)}: {aa_with_6}")
fact("Distinct degeneracy values", deg_values)
fact("Number of distinct values", len(deg_values))
fact("Stop codon degeneracy", 3)

m1 = match("Max degeneracy", 6, "n")
m2 = match("AAs with 6 codons", 3, "n")  # 3 != n=6, but 3 is n/2

print()
print("  Distinct degeneracy values = {1, 2, 3, 4, 6}")
print("  These are exactly the DIVISORS of 6 minus nothing... wait:")
print(f"  Divisors of 6 = {{1, 2, 3, 6}}. Degeneracy has {{1, 2, 3, 4, 6}}.")
print("  4 is NOT a divisor of 6. So it's not the divisor set.")
print(f"  Count of distinct values = {len(deg_values)}")
m3 = match("Distinct degeneracy count", len(deg_values), "sopfr")

print()
print("  NOTE: Max degeneracy = 6 is a real fact (Leu, Arg, Ser).")
print("  3 AAs with 6-fold: matches n/2, not n. Hypothesis said 3, that's correct.")
print("  Distinct values = {1,2,3,4,6} — count is 5 = sopfr. Interesting.")
print("  But 5 distinct values for 20+1 items with max=6 is not surprising.")
grade(2, "medium — max=6 is genuine; count=5 is borderline")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-312: Benzene MOs (Huckel theory)
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-312", "Benzene MOs: 6 orbitals, 3 bonding + 3 antibonding")

print("\n  Huckel MO energies: E_k = alpha + 2*beta*cos(2*pi*k/6), k=0..5")
energies = []
for k in range(6):
    ek = 2 * math.cos(2 * math.pi * k / 6)
    energies.append(ek)
    btype = "bonding" if ek > 0 else ("nonbonding" if ek == 0 else "antibonding")
    print(f"    k={k}: E = alpha + {ek:+.4f}*beta  [{btype}]")

bonding = sum(1 for e in energies if e > 0.001)
antibonding = sum(1 for e in energies if e < -0.001)
nonbonding = sum(1 for e in energies if abs(e) < 0.001)

fact("Total MOs", 6)
fact("Bonding MOs", bonding)
fact("Antibonding MOs", antibonding)
fact("Nonbonding MOs", nonbonding)

m1 = match("Total MOs", 6, "n")
# Actually: k=0 gives +2beta (bonding), k=1,5 give +1beta (bonding),
# k=2,4 give -1beta (antibonding), k=3 gives -2beta (antibonding)
# So 3 bonding + 3 antibonding
print()
print("  NOTE: 6 p-orbitals -> 6 MOs is trivially forced by the atom count.")
print("  3 bonding + 3 antibonding is a general property of even-membered rings.")
print("  Huckel 4n+2 rule: benzene is aromatic because 6 = 4(1)+2.")
grade(2, "low — this is textbook quantum chemistry, structurally exact")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-313: Cell cycle phases and checkpoints
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-313", "Cell cycle: 4 phases, 3 checkpoints, CDK4/6")

fact("Cell cycle phases", "4: G1, S, G2, M")
fact("Major checkpoints", "3: G1/S, G2/M, spindle assembly")
fact("CDK4/6", "real kinase, drives G1 progression")

m1 = match("Phases", 4, "tau")
# 3 checkpoints — what n=6 function gives 3? n/2=3
print(f"  [~] Checkpoints = 3 = n/2  (not a standard arithmetic function of 6)")
print(f"  [v] CDK4/6 — the name literally contains 4 and 6 = tau and n")

print()
print("  NOTE: 4 phases is standard cell biology. CDK4/6 is a real protein.")
print("  3 checkpoints: depends on counting (some say 2 major + 1 minor).")
print("  CDK naming: CDK4 and CDK6 are separate kinases, often grouped as CDK4/6.")
grade(1, "high — 4 phases is basic biology; CDK numbering is historical")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-314: Periodic table blocks
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-314", "p-block=6 wide, s-block=2, Carbon at Z=6")

fact("p-block width", 6, "6 p-orbitals per shell")
fact("s-block width", 2, "2 s-orbitals per shell")
fact("d-block width", 10)
fact("f-block width", 14)
fact("Carbon atomic number", 6)

m1 = match("p-block width", 6, "n")
m2 = match("s-block width", 2, "phi")
m3 = match("Carbon Z", 6, "n")

print()
print("  NOTE: Block widths are 2l+1 orbitals x 2 electrons = 2(2l+1).")
print("  s: l=0 -> 2, p: l=1 -> 6, d: l=2 -> 10, f: l=3 -> 14.")
print("  These are quantum mechanical necessities, not coincidences.")
print("  Carbon at Z=6 is a tautology (we CHOSE n=6 partly because of carbon).")
grade(1, "high — block widths are QM; Z=6 is circular reasoning")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-315: Protein secondary structure
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-315", "alpha-helix H-bond i->i+4, beta-sheet shift=2")

fact("Alpha-helix H-bond pattern", "i -> i+4", "carbonyl O(i) to amide NH(i+4)")
fact("Residues per turn (alpha)", 3.6, "not exactly 4")
fact("Beta-sheet H-bond", "between adjacent strands", "shift varies by parallel/anti")
fact("Beta-strand residue repeat", 2, "alternating side chains up/down")

m1 = match("H-bond span", 4, "tau")
m2 = match("Beta repeat", 2, "phi")

print()
print("  NOTE: i->i+4 is correct for alpha-helix. 3.6 residues/turn.")
print("  Beta-sheet 'shift=2' refers to the pleated repeat of 2 residues.")
print("  These are determined by backbone dihedral angles, not number theory.")
grade(1, "high — small numbers (2,4) match many arithmetic functions")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-316: Kok cycle (photosynthetic water oxidation)
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-316", "Kok cycle: 5 S-states, 4 electrons, OEC Mn=4 (not 5)")

fact("S-states", "5: S0, S1, S2, S3, S4", "Kok 1970")
fact("Electrons per O2", 4, "2H2O -> O2 + 4H+ + 4e-")
fact("OEC composition", "Mn4CaO5 cluster", "4 Mn + 1 Ca + 5 oxo bridges")
fact("Mn atoms in OEC", 4, "NOT 5")
fact("Total metal atoms in OEC", 5, "4 Mn + 1 Ca")

m1 = match("S-states", 5, "sopfr")
m2 = match("Electrons per O2", 4, "tau")
m3 = match("Total metals in OEC", 5, "sopfr")

print()
print("  NOTE: Hypothesis says 'OEC metals=5=sopfr' — this is correct if counting")
print("  4 Mn + 1 Ca = 5 total metal atoms. But often only Mn is counted (4).")
print("  5 S-states = sopfr is interesting but S-states are S0..S4 (starts at 0).")
print("  4 electrons = tau is correct (water oxidation half-reaction).")
grade(2, "medium — S-states=5 and electrons=4 are exact biochemical constants")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-317: 3D kissing number = 12
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-317", "3D kissing number = 12 = sigma(6)")

fact("3D kissing number", 12, "PROVED by Schutte & van der Waerden 1953")
fact("This is pure mathematics", "topology/geometry")
fact("Newton-Gregory dispute", "Newton said 12, Gregory said 13. Newton was right.")

m1 = match("Kissing number (3D)", 12, "sigma")

print()
print("  NOTE: This is a PROVEN mathematical theorem, not biology.")
print("  12 = sigma(6) is numerically true.")
print("  But kissing number has nothing to do with perfect numbers.")
print("  It's coincidental that both equal 12.")
print("  Still, it's a genuine deep geometric constant = sigma(6).")
grade(2, "medium — proven math theorem; sigma(6)=12 match is numerically exact")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-318: Pyranose ring
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-318", "Pyranose ring: 6 atoms, 12 chair positions")

fact("Ring atoms", 6, "5C + 1O in pyranose")
fact("Axial positions", 6, "one per ring atom")
fact("Equatorial positions", 6, "one per ring atom")
fact("Total substituent positions", 12, "6 axial + 6 equatorial")

m1 = match("Ring atoms", 6, "n")
m2 = match("Axial positions", 6, "n")
m3 = match("Equatorial positions", 6, "n")
m4 = match("Total positions", 12, "sigma")

print()
print("  NOTE: Pyranose = 6-membered ring by definition (pyran + -ose).")
print("  Chair conformation: each atom has 1 axial + 1 equatorial = 12 total.")
print("  This is geometry of 6-membered chair, not coincidence.")
print("  Genuine structural fact: n atoms -> 2n positions = sigma when n=6.")
grade(2, "low — exact geometric fact of 6-membered chair")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-319: Food chain length
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-319", "Max food chain ~ 6 trophic levels")

fact("Typical food chain", "3-5 trophic levels")
fact("Maximum observed", "~5-7", "varies by ecosystem")
fact("Often cited max", "5", "most textbooks")
fact("Theoretical limit", "~5-6", "based on ~10% energy transfer")

# 10% rule: 0.1^n remaining. At n=6: 0.1^6 = 1e-6 (1 millionth)
for n in range(3, 8):
    pct = 100 * (0.1 ** n)
    print(f"    Level {n}: {pct:.4f}% of original energy remains")

print()
print("  NOTE: '~6 levels' is approximate. Most real chains have 4-5 levels.")
print("  Saying max=6 is generous. 6 is within range but not the typical number.")
grade(1, "high — approximate match; typical value is 4-5, not exactly 6")


# ═══════════════════════════════════════════════════════════════════════
# H-BIO-320: Electron Transport Chain
# ═══════════════════════════════════════════════════════════════════════
header("H-BIO-320", "ETC: 5 complexes, Complex I pumps 4H+, Complex IV pumps 2H+")

fact("ETC complexes", "4 or 5", "I, II, III, IV + ATP synthase (V)")
fact("Complex I (NADH dehydrogenase) H+ pumped", 4)
fact("Complex III (cytochrome bc1) H+ pumped", 4, "via Q-cycle")
fact("Complex IV (cytochrome c oxidase) H+ pumped", 2)
fact("Complex II H+ pumped", 0, "succinate dehydrogenase, no pumping")
fact("ATP synthase (Complex V)", "not a proton pump — uses gradient")

print()
print("  Counting 'complexes':")
print("    Strict ETC: 4 complexes (I-IV)")
print("    With ATP synthase: 5 (I-V)")
print("    CoQ and Cyt c are mobile carriers, not complexes")

if True:
    # Is it 5=sopfr? Only if we count ATP synthase as complex V
    m1 = match("Complexes (with ATP synthase)", 5, "sopfr")
    m2 = match("Complex I H+ pumped", 4, "tau")
    m3 = match("Complex IV H+ pumped", 2, "phi")

print()
print("  NOTE: Complex count depends on whether ATP synthase is included.")
print("  Proton pumping: I=4, III=4, IV=2 are standard textbook values.")
print("  Complex III pumps 4 (not mentioned in hypothesis — same as Complex I).")
print("  Selective reporting: why highlight I and IV but not III?")
grade(1, "high — selective reporting of which complexes to highlight")


# ═══════════════════════════════════════════════════════════════════════
# SUMMARY TABLE
# ═══════════════════════════════════════════════════════════════════════
print(f"\n\n{'=' * 78}")
print("  SUMMARY TABLE: H-BIO-301 through H-BIO-320")
print(f"{'=' * 78}\n")

results = [
    ("H-BIO-301", "Photosynthesis coefficients",        "**",  "med",  "Glucose subscripts use n,sigma; coeff conflation"),
    ("H-BIO-302", "Benzene C6H6",                       "**",  "med",  "All derived from ring size 6"),
    ("H-BIO-303", "Glucose C6H12O6",                    "**",  "med",  "Forced by hexose formula CnH2nOn"),
    ("H-BIO-304", "Glycolysis ATP/NADH",                "*",   "high", "Small numbers 2,4 easily matched"),
    ("H-BIO-305", "ATP yield = 36 = n^2",               "*",   "high", "OUTDATED value; modern = 30-32"),
    ("H-BIO-306", "Krebs cycle products",               "**",  "med",  "NADH=6 solid; products=5 needs selective count"),
    ("H-BIO-307", "Circadian 24h",                      "*",   "high", "Astronomical, not biological"),
    ("H-BIO-308", "Virus capsid pentamers=12",          "**",  "low",  "Topological necessity (Euler)"),
    ("H-BIO-309", "Water/ice hexagonal",                "**",  "med",  "Tetrahedral chemistry -> hex rings"),
    ("H-BIO-310", "DNA grooves ~12,~6 A",               "*",   "high", "Approximate, not exact"),
    ("H-BIO-311", "Codon degeneracy max=6",             "**",  "med",  "Max=6 genuine; count=5 borderline"),
    ("H-BIO-312", "Benzene MOs 3+3",                    "**",  "low",  "Textbook QM, structurally exact"),
    ("H-BIO-313", "Cell cycle 4 phases",                "*",   "high", "Basic biology; CDK naming historical"),
    ("H-BIO-314", "p-block=6, s-block=2, C=6",          "*",   "high", "QM block widths; Z=6 circular"),
    ("H-BIO-315", "Helix i->i+4, beta=2",              "*",   "high", "Small numbers; backbone geometry"),
    ("H-BIO-316", "Kok cycle S=5, e=4",                 "**",  "med",  "Exact biochem constants"),
    ("H-BIO-317", "Kissing number=12",                  "**",  "med",  "Proven theorem; coincidental =sigma"),
    ("H-BIO-318", "Pyranose 6+6=12 positions",          "**",  "low",  "Exact geometry of 6-ring chair"),
    ("H-BIO-319", "Food chain ~6 levels",               "*",   "high", "Approximate; typical is 4-5"),
    ("H-BIO-320", "ETC 5 complexes, I=4H+, IV=2H+",    "*",   "high", "Selective reporting"),
]

print(f"  {'ID':<12} {'Topic':<35} {'Grade':<6} {'Texas':<6} {'Note'}")
print(f"  {'-'*12} {'-'*35} {'-'*6} {'-'*6} {'-'*40}")
for r in results:
    print(f"  {r[0]:<12} {r[1]:<35} {r[2]:<6} {r[3]:<6} {r[4]}")

# Count grades
stars3 = sum(1 for r in results if r[2] == "***")
stars2 = sum(1 for r in results if r[2] == "**")
stars1 = sum(1 for r in results if r[2] == "*")
low_texas = sum(1 for r in results if r[3] == "low")
med_texas = sum(1 for r in results if r[3] == "med")
high_texas = sum(1 for r in results if r[3] == "high")

print(f"\n  Grade distribution:  *** = {stars3},  ** = {stars2},  * = {stars1}")
print(f"  Texas risk:          low = {low_texas},  med = {med_texas},  high = {high_texas}")

print(f"""
  ─────────────────────────────────────────────────────────────
  OVERALL ASSESSMENT:
  ─────────────────────────────────────────────────────────────

  The n=6 arithmetic (sigma=12, tau=4, phi=2, sopfr=5) does appear
  across biology and chemistry with surprising frequency. However:

  1. STRUCTURAL (low Texas risk): H-BIO-308, 312, 318
     These are mathematically/geometrically FORCED by 6-fold symmetry.
     They confirm that 6-fold structures propagate n=6 arithmetic,
     but this is tautological rather than mysterious.

  2. GENUINE but DERIVATIVE: H-BIO-301-303, 306, 309, 311, 316, 317
     Real matches, but most derive from carbon being element 6
     and hexose sugars being C6. Once you pick n=6, derivatives follow.

  3. WEAK/CHERRY-PICKED: H-BIO-304, 305, 307, 310, 313-315, 319-320
     Small numbers (2,4) match many things. Approximate values rounded
     to fit. Selective counting of which items to include.

  KEY INSIGHT: The strong matches cluster around HEXAGONAL CHEMISTRY
  (benzene, glucose, ice, pyranose) — which is expected because carbon
  chemistry favors 6-membered rings (strain-free sp3/sp2 geometry).
  The n=6 pattern in biology is really the n=6 pattern in carbon chemistry.
""")


if __name__ == "__main__":
    pass
