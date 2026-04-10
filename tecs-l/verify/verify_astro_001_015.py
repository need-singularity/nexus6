#!/usr/bin/env python3
"""
Verify 15 Astronomy/Cosmology Hypotheses Connecting to n=6
==========================================================
Perfect number framework: n=6, sigma(6)=12, tau(6)=4, phi(6)=2, sigma_{-1}(6)=2
Golden Zone: [0.2123, 0.5], center 1/e ~ 0.3679
"""

import math
import random
import statistics

# ──────────────────────────────────────────────────────────────────
# n=6 constants
# ──────────────────────────────────────────────────────────────────
N = 6
SIGMA = 12          # sum of divisors
TAU = 4             # number of divisors
PHI = 2             # Euler totient
SIGMA_NEG1 = 2.0    # sum of reciprocal divisors: 1+1/2+1/3+1/6
DIVISORS = [1, 2, 3, 6]
GZ_UPPER = 0.5
GZ_LOWER = 0.5 - math.log(4/3)  # 0.2123
GZ_CENTER = 1/math.e             # 0.3679
GZ_WIDTH = math.log(4/3)         # 0.2877

# ──────────────────────────────────────────────────────────────────
# Texas Sharpshooter test
# ──────────────────────────────────────────────────────────────────
def texas_test(observed, predicted, n_candidates=15, n_trials=100000):
    """Compute p-value: probability a random pick from n_candidates
    constants hits within |observed-predicted|/observed of any target."""
    error = abs(observed - predicted) / observed if observed != 0 else abs(observed - predicted)
    # How many of n_candidates random uniform constants in [0, max(observed*3, 100)]
    # would match within this error tolerance?
    rng = random.Random(42)
    hits = 0
    hi = max(observed * 3, 100)
    for _ in range(n_trials):
        rand_val = rng.uniform(0, hi)
        if abs(rand_val - observed) / observed <= error if observed != 0 else abs(rand_val - observed) <= abs(observed - predicted):
            hits += 1
    p = hits / n_trials
    # Bonferroni correction
    p_corrected = min(1.0, p * n_candidates)
    return error, p_corrected


def grade(error_pct, p_value, exact=False, ad_hoc=False):
    """Assign grade based on verification rules."""
    if exact and not ad_hoc:
        return "GREEN"  # exact equation proven
    if ad_hoc:
        if p_value < 0.05:
            return "ORANGE"  # weak with ad-hoc
        return "WHITE"
    if error_pct < 0.1 and p_value < 0.01:
        return "ORANGE_STAR"  # structural
    if error_pct < 1.0 and p_value < 0.01:
        return "ORANGE_STAR"
    if error_pct < 2.0 and p_value < 0.05:
        return "ORANGE"
    if error_pct < 5.0 and p_value < 0.05:
        return "ORANGE"
    return "WHITE"


GRADE_EMOJI = {
    "GREEN": "🟩",
    "ORANGE_STAR": "🟧⭐",
    "ORANGE": "🟧",
    "WHITE": "⚪",
    "BLACK": "⬛",
}

# ──────────────────────────────────────────────────────────────────
# Hypothesis definitions and verification
# ──────────────────────────────────────────────────────────────────
results = []

print("=" * 72)
print("  ASTRONOMY/COSMOLOGY HYPOTHESES — n=6 CONNECTION VERIFICATION")
print("=" * 72)

# ──────────────────────────────────────────────
# SOLAR SYSTEM (5 hypotheses)
# ──────────────────────────────────────────────

# H-ASTRO-001: Lagrange points per body pair = 5 = sigma(6)-tau(6)-phi(6)
print("\n--- H-ASTRO-001: Lagrange Points = sigma - tau - phi ---")
lagrange_points = 5  # well-known: L1..L5
predicted = SIGMA - TAU - PHI  # 12 - 4 - 2 = 6
predicted_alt = N - 1  # 6 - 1 = 5
error_pct = abs(lagrange_points - predicted_alt) / lagrange_points * 100
print(f"  Observed: {lagrange_points} Lagrange points per body pair")
print(f"  Predicted (n-1): {predicted_alt} = {N}-1")
print(f"  Predicted (sigma-tau-phi): {predicted} = {SIGMA}-{TAU}-{PHI}")
print(f"  n-1 = 5: exact match")
print(f"  sigma-tau-phi = 6: off by 1 (ad-hoc)")
# The n-1=5 mapping is exact but trivial (n-1 works for any n)
# The sigma-tau-phi=6 mapping needs +1/-1 correction
# Grade: WHITE (trivially true for any n that happens to be 6; 5=n-1 is generic)
g = "WHITE"
print(f"  Grade: {GRADE_EMOJI[g]} — n-1=5 is exact but trivial (works for any n)")
results.append(("H-ASTRO-001", "Lagrange points = n-1 = 5", 0.0, 1.0, g))

# H-ASTRO-002: Jupiter-Saturn orbital resonance 5:2, 5/2 = sigma(6)/tau(6)*phi(6)/N?
print("\n--- H-ASTRO-002: Jupiter-Saturn Great Inequality 5:2 ---")
js_ratio = 5/2  # 2.5, near-resonance
# Can we express 5/2 from n=6 arithmetic?
# tau(6) + 1 = 5, phi(6) = 2 → (tau+1)/phi = 5/2 — ad-hoc (+1)
# sigma(6)/tau(6) = 12/4 = 3, not 2.5
# N/phi(6) = 6/2 = 3, not 2.5
# (sigma-tau+phi-1)/(tau-phi) = (12-4+2-1)/(4-2) = 9/2 — nope
# Honest: no clean expression
expr_val = (TAU + 1) / PHI  # 5/2 but +1 is ad-hoc
print(f"  Jupiter-Saturn near-resonance: {js_ratio}")
print(f"  Best n=6 expression: (tau+1)/phi = ({TAU}+1)/{PHI} = {expr_val}")
print(f"  Requires +1 ad-hoc correction")
g = "WHITE"
print(f"  Grade: {GRADE_EMOJI[g]} — ad-hoc +1 required, no clean n=6 expression")
results.append(("H-ASTRO-002", "Jupiter-Saturn 5:2 from n=6", 0.0, 1.0, g))

# H-ASTRO-003: Earth's axial tilt 23.44 deg ~ sigma(6)*phi(6) = 24?
print("\n--- H-ASTRO-003: Earth's Axial Tilt ~ sigma*phi? ---")
axial_tilt = 23.44  # degrees, current epoch
pred_a = SIGMA * PHI  # 24
error_pct = abs(axial_tilt - pred_a) / axial_tilt * 100
print(f"  Observed axial tilt: {axial_tilt} deg")
print(f"  sigma(6)*phi(6) = {SIGMA}*{PHI} = {pred_a}")
print(f"  Error: {error_pct:.2f}%")
print(f"  Note: Axial tilt varies 22.1-24.5 over Milankovitch cycle (41kyr)")
print(f"  24 falls within Milankovitch range but is not special")
# Texas test
random.seed(42)
# How likely is a random integer 1-50 to be within 2.4% of 23.44? P ~ 1/50 ~ 2%
# With 15 hypotheses Bonferroni: ~30%
p_val = 0.30  # estimated
g = "WHITE"
print(f"  p-value (Bonferroni): ~{p_val:.2f}")
print(f"  Grade: {GRADE_EMOJI[g]} — 2.4% error, axial tilt is unstable (Milankovitch), coincidence")
results.append(("H-ASTRO-003", "Axial tilt ~ sigma*phi = 24", error_pct, p_val, g))

# H-ASTRO-004: Moon orbital period 27.32 days ~ e^(sigma(6)/tau(6)) = e^3 = 20.09? No.
# Better: 27.32 ~ sigma(6)*phi(6) + tau(6) - 1 = 24+4-1 = 27? Ad-hoc.
# Or: 27.32 ~ 3^3 = 27? That's not n=6 specific.
# Honest attempt: sigma(6) + tau(6)*phi(6)^2 = 12 + 4*4 = 28? close but contrived
# Let's try: N! / (sigma(6) + tau(6)) = 720/16 = 45. No.
# N^2 - tau(6)*phi(6) = 36-8 = 28. Close to 27.32 but still ad-hoc.
print("\n--- H-ASTRO-004: Moon Sidereal Period ~ n=6 expression ---")
moon_period = 27.322  # days (sidereal)
# Candidates
cands = {
    "sigma+tau*phi^2": SIGMA + TAU * PHI**2,  # 12+16=28
    "N^2-tau*phi": N**2 - TAU*PHI,            # 36-8=28
    "3^3": 27,                                 # not n=6 specific
    "sigma*phi+tau-1": SIGMA*PHI+TAU-1,        # 24+4-1=27, ad-hoc -1
}
print(f"  Moon sidereal period: {moon_period} days")
for expr, val in cands.items():
    err = abs(moon_period - val) / moon_period * 100
    print(f"    {expr} = {val}, error = {err:.2f}%")
# Best: 3^3=27 (2.4% error) but not n=6 specific
# N^2-tau*phi=28 (2.5% error) and uses n=6 but contrived
g = "WHITE"
print(f"  Grade: {GRADE_EMOJI[g]} — all expressions are contrived or not n=6 specific")
results.append(("H-ASTRO-004", "Moon period from n=6", 2.4, 1.0, g))

# H-ASTRO-005: Number of classical planets visible to naked eye = 5 = N-1
# Mercury, Venus, Mars, Jupiter, Saturn = 5
# With Earth = 6 = N (the 6 planets known to ancients including Earth)
print("\n--- H-ASTRO-005: Classical Planets = 6 (including Earth) ---")
classical_planets = 6  # Mercury, Venus, Earth, Mars, Jupiter, Saturn
print(f"  Classical planets (naked-eye + Earth): {classical_planets}")
print(f"  n = {N}")
print(f"  Exact match: {classical_planets == N}")
print(f"  But: this is a selection effect (naked-eye limit), not fundamental")
print(f"  Uranus is barely visible at mag 5.7; if eyes were slightly better, count=7")
print(f"  Historical: ancients listed 7 'planets' (Sun+Moon+5 wanderers)")
# With 7 "classical celestial wanderers" the match breaks
g = "WHITE"
print(f"  Grade: {GRADE_EMOJI[g]} — observational selection effect, not fundamental")
results.append(("H-ASTRO-005", "Classical planets = 6", 0.0, 1.0, g))

# ──────────────────────────────────────────────
# STELLAR PHYSICS (5 hypotheses)
# ──────────────────────────────────────────────

# H-ASTRO-006: Chandrasekhar limit 1.44 M_sun ~ sigma_{-1}(6)/sqrt(e)?
print("\n--- H-ASTRO-006: Chandrasekhar Limit from n=6 ---")
chandra = 1.44  # solar masses (actual range 1.39-1.46 depending on composition)
# sigma_{-1}(6) = 2
# 2/sqrt(e) = 2/1.6487 = 1.2131 — no
# sqrt(sigma_{-1}) = sqrt(2) = 1.414 — close! 1.8% error
# phi(6)^(1/phi(6)) = 2^(1/2) = sqrt(2) = 1.414
pred_sqrt2 = math.sqrt(2)
error_pct = abs(chandra - pred_sqrt2) / chandra * 100
print(f"  Chandrasekhar limit: {chandra} M_sun")
print(f"  sqrt(sigma_{{-1}}(6)) = sqrt(2) = {pred_sqrt2:.4f}")
print(f"  Also: phi(6)^(1/phi(6)) = 2^(1/2) = {pred_sqrt2:.4f}")
print(f"  Error: {error_pct:.2f}%")
print(f"  Note: sqrt(2) appears in Chandrasekhar's actual derivation")
print(f"  (from electron degeneracy pressure, involves sqrt(2) naturally)")
print(f"  This is physics giving sqrt(2), not n=6")
# The sqrt(2) is inherent in the physics (Fermi-Dirac statistics),
# not from perfect number 6
g = "WHITE"
print(f"  Grade: {GRADE_EMOJI[g]} — sqrt(2) comes from physics, not n=6")
results.append(("H-ASTRO-006", "Chandrasekhar ~ sqrt(2) ~ phi^(1/phi)", error_pct, 0.5, g))

# H-ASTRO-007: Star formation efficiency 1-10%, center ~3% ~ 1/N! * 100?
# 1/720 = 0.14% — no. sigma_{-1}/N! — no. Try: tau(6)/sigma(6)^2 — no.
# Better: observed SFE ~1-3% per free-fall time. 1/sigma(6)^2 = 1/144 = 0.69% — meh
# phi(6)/N! nope. tau(6)% = 4% — close to upper SFE but trivial
print("\n--- H-ASTRO-007: Star Formation Efficiency ~ n=6 ---")
sfe_typical = 0.02  # 2% per free-fall time (Krumholz & McKee 2005)
sfe_range = (0.01, 0.10)
cands = {
    "1/N^2": 1/N**2,            # 1/36 = 2.78%
    "phi/sigma": PHI/SIGMA,     # 2/12 = 16.7% — no
    "1/(N*N-1)": 1/(N*(N-1)),   # 1/30 = 3.33%
    "GZ_lower/tau": GZ_LOWER/TAU,  # 0.053
}
print(f"  Typical SFE per free-fall time: ~{sfe_typical*100:.0f}%")
print(f"  Range: {sfe_range[0]*100:.0f}-{sfe_range[1]*100:.0f}%")
for expr, val in cands.items():
    err = abs(sfe_typical - val) / sfe_typical * 100
    print(f"    {expr} = {val:.4f} ({val*100:.2f}%), error from 2%: {err:.1f}%")
# 1/N^2 = 2.78% is within the broad range but not precise
g = "WHITE"
print(f"  Grade: {GRADE_EMOJI[g]} — SFE range is too broad (1-10%), any constant fits")
results.append(("H-ASTRO-007", "Star formation efficiency ~ 1/N^2", 39.0, 1.0, g))

# H-ASTRO-008: HR diagram: 7 spectral types, but tau(6)+phi(6)+1=7? ad-hoc
# More interesting: main sequence lifetime scaling T ~ M^(-2.5)
# 2.5 = 5/2. Already tried in H-ASTRO-002. Not clean.
# Try: HR diagram divides stars into ~6 luminosity classes (Ia, Ib, II, III, IV, V, VI/sd)
# Actually standard is 8 (0, Ia, Iab, Ib, II, III, IV, V). Or simplified: 6 (I-VI).
print("\n--- H-ASTRO-008: Yerkes Luminosity Classes = 6 ---")
# MKK/Yerkes: I(supergiants), II(bright giants), III(giants), IV(subgiants), V(main seq), VI(subdwarfs)
# Some sources add 0(hypergiants) and VII(white dwarfs) = 8 total
# Standard Morgan-Keenan uses I-V = 5, extended I-VI = 6
lum_classes_standard = 6  # I through VI (Roman numeral classification)
print(f"  Yerkes luminosity classes (I-VI): {lum_classes_standard}")
print(f"  n = {N}")
print(f"  Match: {'exact' if lum_classes_standard == N else 'no'}")
print(f"  Caveat: class VI (subdwarfs) was a later addition")
print(f"  Caveat: some systems use 5 (I-V) or 8 (0-VII)")
print(f"  The count depends on classification system choice")
g = "WHITE"
print(f"  Grade: {GRADE_EMOJI[g]} — count depends on chosen classification system")
results.append(("H-ASTRO-008", "Luminosity classes = 6", 0.0, 1.0, g))

# H-ASTRO-009: Solar neutrino flavors. Actually 3 neutrino flavors = divisor of 6.
# 3 generations of matter = divisor of 6 (this is particle physics, covered elsewhere?)
# Better stellar: pp chain has 3 branches (ppI, ppII, ppIII)
# CNO cycle has 2 branches (CNO-I, CNO-II)
# Total major fusion pathways in stars: pp(3) + CNO(2) + triple-alpha(1) = 6
print("\n--- H-ASTRO-009: Major Stellar Fusion Pathways = 6 ---")
# pp chain: ppI, ppII, ppIII = 3
# CNO cycle: CNO-I (CN cycle), CNO-II (NO cycle) = 2
# Helium burning: triple-alpha = 1
# Total: 3 + 2 + 1 = 6
pp_branches = 3
cno_branches = 2
he_burning = 1
total = pp_branches + cno_branches + he_burning
print(f"  pp chain branches: {pp_branches} (ppI, ppII, ppIII)")
print(f"  CNO cycle branches: {cno_branches} (CN, NO)")
print(f"  Helium burning: {he_burning} (triple-alpha)")
print(f"  Total: {total}")
print(f"  n = {N}")
print(f"  Match: {'exact' if total == N else 'no'}")
print(f"  Also: 3+2+1 = 1+2+3 = sigma(6)/2 = sum of proper divisors of 6")
print(f"  Caveat: 'major' is subjective — could add C-burning, O-burning, Si-burning")
print(f"  With advanced burning stages: 6+3 = 9. Selection effect.")
g = "WHITE"
print(f"  Grade: {GRADE_EMOJI[g]} — selection of 'major' pathways is subjective")
results.append(("H-ASTRO-009", "Stellar fusion pathways = 6", 0.0, 1.0, g))

# H-ASTRO-010: Stellar evolution stages for massive star: 6
# Main sequence -> Red giant -> He burning -> C/O burning -> Si burning -> Supernova
# That's exactly 6 stages!
print("\n--- H-ASTRO-010: Massive Star Evolution Stages = 6 ---")
stages = [
    "1. Main sequence (H burning)",
    "2. Red giant/supergiant (H shell)",
    "3. Helium core burning",
    "4. Carbon/Oxygen burning",
    "5. Silicon burning",
    "6. Core collapse / Supernova",
]
print(f"  Massive star (>8 M_sun) evolution stages:")
for s in stages:
    print(f"    {s}")
print(f"  Count: {len(stages)}")
print(f"  n = {N}")
print(f"  Match: {'exact' if len(stages) == N else 'no'}")
print(f"  Caveat: granularity is arbitrary")
print(f"    Coarser: MS -> giant -> supernova = 3 stages")
print(f"    Finer: add neon burning, oxygen burning separately = 8+ stages")
print(f"  The 'onion shell' model has 6 burning layers: H, He, C, Ne, O, Si")
print(f"  This IS standard and well-defined (not arbitrary)")
onion_layers = 6
print(f"  Onion shell burning layers: {onion_layers} = n = {N} (EXACT)")
print(f"  The 6-layer onion structure is a robust observational fact")
g = "WHITE"
print(f"  Grade: {GRADE_EMOJI[g]} — 6 layers is standard but number of burning")
print(f"  stages depends on which elements fuse (physics, not n=6)")
results.append(("H-ASTRO-010", "Onion shell burning layers = 6", 0.0, 1.0, g))

# ──────────────────────────────────────────────
# COSMOLOGY (5 hypotheses)
# ──────────────────────────────────────────────

# H-ASTRO-011: Spatial dimensions = 3 = N/phi(6) = 6/2
print("\n--- H-ASTRO-011: Spatial Dimensions = N/phi(6) ---")
spatial_dims = 3
pred = N // PHI  # 6/2 = 3
print(f"  Spatial dimensions: {spatial_dims}")
print(f"  N/phi(6) = {N}/{PHI} = {pred}")
print(f"  Match: exact")
print(f"  Also: 3 is a proper divisor of 6")
print(f"  But: N/phi(N)=N/2 gives 3 for ANY even number, not just 6")
print(f"  And: 3 = largest proper divisor of 6 (structural)")
print(f"  Anthropic argument: d=3 is the only dimension allowing")
print(f"  stable orbits + stable atoms simultaneously (Ehrenfest)")
print(f"  Question: does the n=6 structure REQUIRE d=3?")
# sigma(6) divisors include 3. 6 = 2*3. These are structural.
# But the claim that d=3 BECAUSE of n=6 is unfounded.
g = "WHITE"
print(f"  Grade: {GRADE_EMOJI[g]} — 3 divides 6, but N/2=3 works for any even N")
results.append(("H-ASTRO-011", "d=3 spatial dimensions = N/phi", 0.0, 1.0, g))

# H-ASTRO-012: CMB temperature 2.7255 K ~ e (2.7183)
print("\n--- H-ASTRO-012: CMB Temperature ~ e ---")
T_cmb = 2.7255  # K (FIRAS measurement, Fixsen 2009)
T_cmb_err = 0.0006  # 1-sigma
pred_e = math.e
error_pct = abs(T_cmb - pred_e) / T_cmb * 100
print(f"  T_CMB = {T_cmb} +/- {T_cmb_err} K")
print(f"  e = {pred_e:.4f}")
print(f"  Error: {error_pct:.3f}%")
print(f"  This is {abs(T_cmb - pred_e)/T_cmb_err:.1f} sigma away from e")
print(f"  Already noted in TECS-L formula discovery (T_CMB formulas)")
# Connection to n=6: e is our Golden Zone center constant
# But T_CMB = T_0 * (1+z_dec) / (1+z_dec) at z=0, depends on baryon density etc.
# T_CMB ~ e is already known in project. New angle: WHY?
# T_CMB = (15*c^2*hbar^3 / (pi^2*k_B^4) * rho_gamma)^(1/4)
# rho_gamma depends on photon density from Big Bang. No reason to be e.
# But 0.27% error is genuinely small.
# Texas test: probability that a physical constant in range [0.1, 100]
# would be within 0.27% of e
n_phys_constants_astronomy = 50  # rough number of astronomical constants one could try
p_single = 2 * 0.0027  # +/- 0.27% of e in uniform on [0,100] = 0.0054/100*e*2 ~ 0.03%
p_corrected = min(1.0, p_single * n_phys_constants_astronomy)
print(f"  Bonferroni p-value estimate: {p_corrected:.3f}")
print(f"  ALREADY KNOWN in TECS-L — not a new discovery")
g = "ORANGE"
print(f"  Grade: {GRADE_EMOJI[g]} — known result, 0.27% is notable but not n=6 specific")
results.append(("H-ASTRO-012", "T_CMB ~ e (0.27% error)", error_pct, p_corrected, g))

# H-ASTRO-013: Dark energy fraction 68.3% ~ 1-1/e = 63.2%? No, already H-118 uses 2/3.
# NEW angle: dark energy + baryon = 68.3 + 4.9 = 73.2% ~ 73.2%?
# Or: dark matter / baryon = 26.8/4.9 = 5.47 ~ tau(6)+phi(6)-1? No.
# Better: baryon-to-photon ratio eta = 6.1e-10. The 6.1 is close to 6!
print("\n--- H-ASTRO-013: Baryon-to-Photon Ratio eta ~ 6e-10 ---")
eta_obs = 6.10e-10  # Planck 2018 (6.10 +/- 0.04) x 10^-10
eta_pred = 6.0e-10  # exact 6
mantissa = eta_obs / 1e-10
error_pct = abs(mantissa - 6.0) / mantissa * 100
print(f"  Baryon-to-photon ratio eta = ({mantissa:.2f} +/- 0.04) x 10^-10")
print(f"  n = {N}")
print(f"  Mantissa error from 6: {error_pct:.2f}%")
print(f"  This is {abs(mantissa - 6.0)/0.04:.1f} sigma from exactly 6")
print(f"  Note: 6.10 is 2.5 sigma from 6.00, so NOT consistent with exactly 6")
print(f"  The exponent -10 has no n=6 connection")
print(f"  If mantissa were exactly 6.00, this would be striking")
print(f"  But 6.10 +/- 0.04 excludes 6.00 at 2.5 sigma")
g = "WHITE"
print(f"  Grade: {GRADE_EMOJI[g]} — close but statistically excluded (2.5 sigma from 6)")
results.append(("H-ASTRO-013", "Baryon/photon eta mantissa ~ 6", error_pct, 0.35, g))

# H-ASTRO-014: Observable universe age / Hubble time ratio
# Age = 13.787 Gyr, Hubble time = 1/H0 = 14.4 Gyr (H0=67.4)
# Ratio = 13.787/14.4 = 0.957 ~ 1-1/sigma(6)? = 1-1/12 = 0.9167? No.
# Better: T_age * H0 = 0.957 (dimensionless). Not close to n=6 constants.
# Try: spectral index ns = 0.9649. In Golden Zone? GZ=[0.212, 0.5] — no.
# Try: ns = 1 - 1/sigma(6) - 1/N! = 1-1/12-1/720 = 0.9319. No (3.4% off).
# ns = 1 - phi(6)/N^2 = 1 - 2/36 = 0.9444. Still 2.1% off.
# Actually: ns - 1 = -0.0351. This is the spectral tilt.
# -1/N^2 + 1/N!? = -1/36 + 1/720 = -0.0264. Not matching.
print("\n--- H-ASTRO-014: Spectral Index ns from n=6 ---")
ns_obs = 0.9649  # Planck 2018 scalar spectral index
ns_err = 0.0042
# Try various expressions
cands = {
    "1-1/sigma": 1 - 1/SIGMA,         # 0.9167
    "1-1/(N*N)": 1 - 1/N**2,           # 0.9722
    "1-phi/N^2": 1 - PHI/N**2,         # 0.9444
    "1-1/(N^2-1)": 1 - 1/(N**2 - 1),  # 0.9714
    "1-1/tau!": 1 - 1/math.factorial(TAU),  # 1-1/24 = 0.9583
}
print(f"  Planck ns = {ns_obs} +/- {ns_err}")
best_expr = None
best_err = float('inf')
for expr, val in cands.items():
    err = abs(ns_obs - val)
    sigma_dist = err / ns_err
    print(f"    {expr} = {val:.4f}, |delta| = {err:.4f} ({sigma_dist:.1f} sigma)")
    if err < best_err:
        best_err = err
        best_expr = expr
print(f"  Best: {best_expr} but still >1 sigma away")
g = "WHITE"
print(f"  Grade: {GRADE_EMOJI[g]} — no clean n=6 expression matches within 1 sigma")
results.append(("H-ASTRO-014", "Spectral index ns from n=6", best_err/ns_obs*100, 1.0, g))

# H-ASTRO-015: Cosmological coincidence — we observe at epoch where
# matter/radiation equality z_eq ~ 3400 and dark-energy/matter equality z_de ~ 0.3
# z_de ~ 1/e (0.368)? or ~ GZ_center?
print("\n--- H-ASTRO-015: Dark Energy-Matter Equality Redshift ~ 1/e ---")
# Dark energy = matter equality: Omega_Lambda * (1+z)^0 = Omega_m * (1+z)^3
# (0.683) = (0.317) * (1+z)^3
# (1+z)^3 = 0.683/0.317 = 2.155
# 1+z = 2.155^(1/3) = 1.293
# z = 0.293
z_de = (0.683 / 0.317) ** (1/3) - 1
print(f"  Dark energy-matter equality redshift: z_eq = {z_de:.4f}")
print(f"  1/e = {1/math.e:.4f}")
print(f"  GZ_center = {GZ_CENTER:.4f}")
print(f"  GZ_width = {GZ_WIDTH:.4f}")
print(f"  GZ_lower = {GZ_LOWER:.4f}")
error_1e = abs(z_de - 1/math.e) / z_de * 100
error_gz_width = abs(z_de - GZ_WIDTH) / z_de * 100
error_gz_lower = abs(z_de - GZ_LOWER) / z_de * 100
print(f"  Error from 1/e: {error_1e:.2f}%")
print(f"  Error from GZ_width: {error_gz_width:.2f}%")
print(f"  Error from GZ_lower: {error_gz_lower:.2f}%")
# z_de = 0.293 is closest to GZ_width = 0.2877 (1.8% error)
# or GZ_lower = 0.2123 (27.5% error)
# 1/e = 0.3679 is 25.6% off
if error_gz_width < error_1e:
    print(f"  Closest match: GZ_width = ln(4/3) = {GZ_WIDTH:.4f} ({error_gz_width:.1f}% error)")
else:
    print(f"  Closest match: 1/e = {1/math.e:.4f} ({error_1e:.1f}% error)")
# z_de depends on Omega_Lambda which is measured. This is a derived quantity.
# Texas test: 1.8% match from 15 candidates * ~5 target constants
p_est = 0.15  # rough
g = "WHITE"
print(f"  Grade: {GRADE_EMOJI[g]} — z_de ~ GZ_width at 1.8%, but derived from H-118's Omega_Lambda")
print(f"  Not independent of existing H-118 hypothesis")
results.append(("H-ASTRO-015", "z_DE-matter ~ ln(4/3)", error_gz_width, p_est, g))


# ══════════════════════════════════════════════════════════════════
# SUMMARY TABLE
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("  SUMMARY TABLE")
print("=" * 72)
print(f"  {'ID':<14} {'Hypothesis':<45} {'Err%':>6} {'Grade'}")
print(f"  {'─'*14} {'─'*45} {'─'*6} {'─'*10}")

grade_counts = {"GREEN": 0, "ORANGE_STAR": 0, "ORANGE": 0, "WHITE": 0, "BLACK": 0}
for hid, desc, err, p, g in results:
    grade_counts[g] += 1
    emoji = GRADE_EMOJI[g]
    print(f"  {hid:<14} {desc:<45} {err:>5.1f}% {emoji}")

print(f"\n  ── Grade Distribution ──")
for g, count in grade_counts.items():
    if count > 0:
        print(f"  {GRADE_EMOJI[g]} {g}: {count}")

total_hypotheses = len(results)
print(f"\n  Total: {total_hypotheses} hypotheses")
print(f"  Honest assessment: {grade_counts['WHITE']}/{total_hypotheses} are coincidence (WHITE)")
print(f"  {grade_counts['ORANGE']}/{total_hypotheses} weak evidence (ORANGE)")
print(f"  {grade_counts['ORANGE_STAR']}/{total_hypotheses} structural (ORANGE STAR)")
print(f"  {grade_counts['GREEN']}/{total_hypotheses} proven (GREEN)")

print("\n" + "=" * 72)
print("  OVERALL VERDICT")
print("=" * 72)
print("""
  The perfect number 6 does NOT have privileged connections to
  astronomical structures beyond what one would expect from:
  1. Small-number bias (3, 6, 12 appear everywhere)
  2. Selection effects (choosing which items to count)
  3. Post-hoc fitting (many n=6 expressions to try)

  The ONLY notable result is T_CMB ~ e (0.27% error), which was
  already known in TECS-L and is not specific to n=6.

  The baryon-to-photon ratio eta ~ 6e-10 is tantalizing but the
  mantissa 6.10 is 2.5 sigma away from exactly 6.00.

  Astronomy is NOT a fruitful domain for n=6 connections.
  The strong results remain in pure mathematics and information theory.
""")
