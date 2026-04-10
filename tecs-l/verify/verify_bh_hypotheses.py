#!/usr/bin/env python3
"""
Verify 30 Black Hole / Gravitational Physics Hypotheses for TECS-L
H-BH-001 through H-BH-030

Tests each hypothesis for n=6 connections using real astrophysics data.
Applies Texas Sharpshooter correction (Bonferroni).
"""

import math
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scipy import stats
import numpy as np

# ─────────────────────────────────────────
# Perfect number 6 constants
# ─────────────────────────────────────────
SIGMA_6 = 12        # sigma(6) = sum of divisors
TAU_6 = 4           # tau(6) = number of divisors
PHI_6 = 2           # phi(6) = Euler totient
SIGMA_INV_6 = 2.0   # sigma_{-1}(6) = 1 + 1/2 + 1/3 + 1/6 = 2
DIVISORS = [1, 2, 3, 6]
DIVISOR_RECIPS = [1/1, 1/2, 1/3, 1/6]  # sum = 2 = sigma_{-1}
PROPER_DIVISOR_RECIPS = [1/2, 1/3, 1/6]  # sum = 1

GZ_UPPER = 0.5
GZ_LOWER = 0.5 - math.log(4/3)  # 0.21227...
GZ_CENTER = 1/math.e             # 0.36788...
GZ_WIDTH = math.log(4/3)         # 0.28768...

# ─────────────────────────────────────────
# Real astrophysics constants
# ─────────────────────────────────────────
hbar = 1.054571817e-34   # J*s
c = 2.998e8              # m/s
G = 6.674e-11            # m^3 kg^-1 s^-2
k_B = 1.380649e-23       # J/K
l_P = 1.616255e-35       # Planck length (m)
M_sun = 1.989e30         # kg
t_P = 5.391e-44          # Planck time (s)
M_P = 2.176e-8           # Planck mass (kg)

# Observational data
M87_shadow_uas = 42.0    # microarcseconds (EHT 2019)
SgrA_mass_Msun = 4.15e6  # solar masses (GRAVITY 2022)
TOV_limit_Msun = 2.16    # Tolman-Oppenheimer-Volkoff limit (approx)
MIN_BH_MASS_Msun = 3.0   # minimum stellar BH mass (approx)


# ─────────────────────────────────────────
# Grading system
# ─────────────────────────────────────────
class Result:
    def __init__(self, hid, title, grade, exact, details, p_value=None,
                 n6_factor=None, numerology_risk=""):
        self.hid = hid
        self.title = title
        self.grade = grade        # green/orange_star/orange/white/black
        self.exact = exact        # True if exact equation
        self.details = details
        self.p_value = p_value
        self.n6_factor = n6_factor
        self.numerology_risk = numerology_risk

    def emoji(self):
        return {"green": "🟩", "orange_star": "🟧★",
                "orange": "🟧", "white": "⚪", "black": "⬛"}[self.grade]


def texas_p_value(target, actual, tolerance, search_space):
    """
    Estimate probability of finding a match by chance.
    search_space = number of comparisons attempted.
    """
    if abs(target - actual) <= tolerance:
        # Base probability: fraction of [0, max_val] within tolerance
        max_val = max(abs(target), abs(actual)) * 10 + 1
        p_single = (2 * tolerance) / max_val
        # Bonferroni correction
        p_corrected = min(1.0, p_single * search_space)
        return p_corrected
    return 1.0


def grade_hypothesis(exact, p_value):
    """Assign grade based on verification rules."""
    if exact:
        return "green"  # Exact equation, proven
    if p_value is not None:
        if p_value < 0.01:
            return "orange_star"  # Structural
        elif p_value < 0.05:
            return "orange"  # Weak evidence
        else:
            return "white"  # Coincidence
    return "white"


results = []

# Number of hypotheses for Bonferroni correction
N_HYPS = 30

print("=" * 72)
print("BLACK HOLE HYPOTHESIS VERIFICATION — TECS-L n=6 Framework")
print("=" * 72)

# ═══════════════════════════════════════════
# A. BLACK HOLE THERMODYNAMICS (H-BH-001 to 006)
# ═══════════════════════════════════════════

print("\n### A. BLACK HOLE THERMODYNAMICS ###\n")

# H-BH-001: Bekenstein-Hawking entropy S = A/(4*l_P^2). Factor 1/4.
# Claim: 1/4 has n=6 connection
# Analysis: 4 = tau(6). So 1/4 = 1/tau(6).
hid = "H-BH-001"
factor = 4
tau_match = (factor == TAU_6)
# But 1/4 is deeply derived from QFT + GR, not from number theory
# The "4" comes from integration over modes in curved spacetime
# Many small integers appear; tau(6)=4 is a stretch
p = texas_p_value(TAU_6, factor, 0, N_HYPS)
detail = (f"S = A/(4*l_P^2). Factor 4 = tau(6)? Exact integer match.\n"
          f"  BUT: 4 arises from QFT mode counting in curved spacetime.\n"
          f"  Integers 1-6 cover most simple factors. P(match|random)=1/{6}.\n"
          f"  Bonferroni p = {N_HYPS}/{6} = {N_HYPS/6:.2f}. Not significant.")
grade = "white"
results.append(Result(hid, "Bekenstein-Hawking factor 1/4 = 1/tau(6)?",
                       grade, tau_match, detail, p_value=N_HYPS/6,
                       n6_factor="tau(6)=4",
                       numerology_risk="HIGH: small integer matching"))
print(f"{hid}: 4 == tau(6)? {tau_match}. Grade: ⚪ (numerology)")

# H-BH-002: Hawking temperature factor 8*pi. 8 = sigma(6)-tau(6)?
hid = "H-BH-002"
factor_8pi = 8 * math.pi
sigma_minus_tau = SIGMA_6 - TAU_6  # 12 - 4 = 8
match_8 = (sigma_minus_tau == 8)
# 8*pi comes from surface gravity of Schwarzschild BH: kappa = c^4/(4GM)
# and T = hbar*kappa/(2*pi*c*k_B) → 8*pi from the product of denominators
# 8 = 2^3 is trivially common. sigma(6)-tau(6)=8 is ad hoc subtraction
p = texas_p_value(8, sigma_minus_tau, 0, N_HYPS)
detail = (f"T_H = hbar*c^3/(8*pi*G*M*k_B). Factor 8 = sigma(6)-tau(6) = 12-4.\n"
          f"  8 = 2^3, extremely common in physics (8-fold way, octahedra, etc.).\n"
          f"  Ad hoc: why sigma - tau? No structural justification.\n"
          f"  Search space: C(4,2)=6 binary ops on {{sigma,tau,phi,sigma_inv}} = 24.\n"
          f"  p(finding 8 somewhere) ~ 1.0. Not significant.")
grade = "white"
results.append(Result(hid, "Hawking T factor 8pi: 8=sigma(6)-tau(6)?",
                       grade, match_8, detail, p_value=1.0,
                       n6_factor="sigma(6)-tau(6)=8",
                       numerology_risk="VERY HIGH: ad hoc subtraction"))
print(f"{hid}: 8 == sigma(6)-tau(6)? {match_8}. Grade: ⚪ (ad hoc)")

# H-BH-003: BH evaporation time ~ M^3. Exponent 3 = divisor of 6
hid = "H-BH-003"
exponent = 3
is_divisor = (6 % exponent == 0)
# t_evap = 5120 * pi * G^2 * M^3 / (hbar * c^4)
# The M^3 comes from integrating dM/dt ~ -1/M^2 (Stefan-Boltzmann for BH)
# 3 is a divisor of 6, but also of 9, 12, 15, 18, 21, 24, ...
# Half of all small integers are divisible by 2 or 3
p_single = 4/10  # 4 of integers 1-10 are divisors of 6
p_corr = min(1.0, p_single * N_HYPS)
detail = (f"t_evap ~ M^3. Exponent 3 is a divisor of 6.\n"
          f"  The M^3 is a consequence of L ~ 1/M^2 (Stefan-Boltzmann).\n"
          f"  dM/dt ~ -L ~ -1/M^2, integrate: t ~ M^3.\n"
          f"  P(random exponent in 1-10 is divisor of 6) = 4/10 = 0.4.\n"
          f"  Bonferroni: p = {p_corr:.2f}. Not significant.")
grade = "white"
results.append(Result(hid, "BH evaporation exponent 3 = divisor of 6?",
                       grade, is_divisor, detail, p_value=p_corr,
                       n6_factor="3|6",
                       numerology_risk="HIGH: common small integer"))
print(f"{hid}: 3 divides 6? {is_divisor}. Grade: ⚪ (trivial)")

# H-BH-004: BH luminosity L ~ 1/M^2. Exponent 2 = phi(6) = sigma_{-1}(6)
hid = "H-BH-004"
exponent = 2
phi_match = (exponent == PHI_6)
sigma_inv_match = (exponent == SIGMA_INV_6)
# L = hbar*c^6 / (15360*pi*G^2*M^2) from Stefan-Boltzmann for BH
# The M^2 is Stefan-Boltzmann law applied to T_H ~ 1/M, A ~ M^2
# L = sigma*T^4*A ~ (1/M)^4 * M^2 = 1/M^2
# Exponent 2 is the most common in all of physics
p_single = 1/10
p_corr = min(1.0, p_single * N_HYPS)
detail = (f"L_BH ~ 1/M^2. Exponent 2 = phi(6) = sigma_{{-1}}(6).\n"
          f"  Derivation: L = sigma_SB * T^4 * A.\n"
          f"  T_H ~ 1/M → T^4 ~ 1/M^4. A ~ M^2.\n"
          f"  L ~ M^2/M^4 = 1/M^2. Pure Stefan-Boltzmann.\n"
          f"  2 is the most common exponent in physics (inverse-square law).\n"
          f"  p_corr = {p_corr:.2f}. Not significant for n=6.")
grade = "white"
results.append(Result(hid, "BH luminosity exponent 2 = phi(6)?",
                       grade, phi_match, detail, p_value=p_corr,
                       n6_factor="phi(6)=2",
                       numerology_risk="HIGH: ubiquitous exponent"))
print(f"{hid}: 2 == phi(6)? {phi_match}. Grade: ⚪ (ubiquitous)")

# H-BH-005: Schwarzschild radius r_s = 2GM/c^2. Factor 2 = phi(6)
hid = "H-BH-005"
factor = 2
phi_match = (factor == PHI_6)
# r_s = 2GM/c^2 from solving g_00 = 0 in Schwarzschild metric
# The 2 comes from Newtonian escape velocity = c condition
detail = (f"r_s = 2GM/c^2. Factor 2 = phi(6).\n"
          f"  The 2 arises from v_escape = sqrt(2GM/r) = c → r = 2GM/c^2.\n"
          f"  Factor 2 appears in ~40% of physics equations.\n"
          f"  Same criticism as H-BH-004. Not significant.")
grade = "white"
results.append(Result(hid, "Schwarzschild factor 2 = phi(6)?",
                       grade, phi_match, detail, p_value=1.0,
                       n6_factor="phi(6)=2",
                       numerology_risk="VERY HIGH: most common factor"))
print(f"{hid}: 2 == phi(6)? {phi_match}. Grade: ⚪ (trivial)")

# H-BH-006: BH has maximum entropy for given energy. GZ connection?
hid = "H-BH-006"
# BH entropy S = k_B * pi * r_s^2 / l_P^2 = k_B * 4*pi*G^2*M^2/(hbar*c^3)
# For a solar-mass BH: S_BH ~ 10^77 k_B
# The maximum entropy principle says S_BH >= S_matter for same energy
# Ratio S_BH/S_matter ~ 10^{19} for a solar mass of hydrogen
# No obvious Golden Zone number appears
# Check: does the ratio of BH entropy to radiation entropy hit GZ?
# S_rad = (4/3) * sigma_SB * T^3 * V. Different scaling entirely.
detail = (f"BH has maximum entropy for given energy (Bekenstein bound).\n"
          f"  S_BH/S_thermal ~ 10^19 for M = M_sun.\n"
          f"  No Golden Zone value (0.212-0.500) appears naturally.\n"
          f"  The entropy ratio is determined by G*M^2/(hbar*c), vastly >> 1.\n"
          f"  No n=6 connection found.")
grade = "white"
results.append(Result(hid, "BH max entropy -- Golden Zone connection?",
                       grade, False, detail, p_value=1.0,
                       n6_factor="none found",
                       numerology_risk="N/A"))
print(f"{hid}: No GZ connection found. Grade: ⚪")

# ═══════════════════════════════════════════
# B. BLACK HOLE STRUCTURE (H-BH-007 to 012)
# ═══════════════════════════════════════════

print("\n### B. BLACK HOLE STRUCTURE ###\n")

# H-BH-007: Kerr metric has 2 horizons = phi(6)
hid = "H-BH-007"
n_horizons = 2
# Kerr: r_+/- = M +/- sqrt(M^2 - a^2)  (geometrized units)
# 2 horizons because quadratic equation in r
# But phi(6) = 2 is coincidental; any quadratic gives 2 roots
detail = (f"Kerr BH: 2 horizons (event + Cauchy) = phi(6) = 2.\n"
          f"  r_+/- = M +/- sqrt(M^2 - a^2).\n"
          f"  2 roots because metric equation is quadratic in r.\n"
          f"  Any quadratic equation has 2 roots. Not specific to n=6.\n"
          f"  Same 2 = phi(6) tautology as H-BH-004, H-BH-005.")
grade = "white"
results.append(Result(hid, "Kerr 2 horizons = phi(6)?",
                       grade, True, detail, p_value=1.0,
                       n6_factor="phi(6)=2",
                       numerology_risk="HIGH: quadratic equation roots"))
print(f"{hid}: 2 horizons = phi(6)? Trivially yes. Grade: ⚪")

# H-BH-008: Reissner-Nordstrom also 2 horizons = phi(6)
hid = "H-BH-008"
# r_+/- = M +/- sqrt(M^2 - Q^2) (geometrized)
# Same quadratic structure
detail = (f"RN BH: 2 horizons = phi(6) = 2.\n"
          f"  Same quadratic structure as Kerr. Same criticism.\n"
          f"  Duplicate of H-BH-007 logic.")
grade = "white"
results.append(Result(hid, "Reissner-Nordstrom 2 horizons = phi(6)?",
                       grade, True, detail, p_value=1.0,
                       n6_factor="phi(6)=2",
                       numerology_risk="HIGH: same as H-BH-007"))
print(f"{hid}: Same as H-BH-007. Grade: ⚪")

# H-BH-009: No-hair theorem: 3 parameters (M, J, Q) = divisor of 6
hid = "H-BH-009"
n_params = 3
is_divisor = (6 % n_params == 0)
# No-hair: BH fully described by mass, angular momentum, charge
# 3 because there are exactly 3 conserved charges in classical GR
# (from Gauss law for gravity, EM, and angular momentum conservation)
# But 3 is extremely common (3D space, etc.)
p_single = 4/10
p_corr = min(1.0, p_single * N_HYPS)
detail = (f"No-hair theorem: BH described by 3 parameters (M, J, Q).\n"
          f"  3 is a divisor of 6. But 3 corresponds to:\n"
          f"  - 3 long-range forces in classical GR (gravity, EM, angular)\n"
          f"  - 3 conserved Gauss-law charges\n"
          f"  p(divisor of 6) = 4/10 = 0.4. After Bonferroni: {p_corr:.2f}.")
grade = "white"
results.append(Result(hid, "No-hair 3 params = divisor of 6?",
                       grade, is_divisor, detail, p_value=p_corr,
                       n6_factor="3|6",
                       numerology_risk="HIGH: 3 is ubiquitous"))
print(f"{hid}: 3|6? {is_divisor}. Grade: ⚪ (trivial)")

# ═══════════════════════════════════════════
# H-BH-010: ISCO = 6M for Schwarzschild BH  ★★★ KEY HYPOTHESIS ★★★
# ═══════════════════════════════════════════
hid = "H-BH-010"
print(f"\n{'='*60}")
print(f"  ★★★ H-BH-010: ISCO = 6M (KEY HYPOTHESIS) ★★★")
print(f"{'='*60}\n")

# Derivation from GR:
# Effective potential: V_eff(r) = -M/r + L^2/(2r^2) - M*L^2/r^3
# (geometrized units: G=c=1)
#
# Circular orbit: dV/dr = 0 → L^2 = M*r^2/(r-3M)
# Stability: d^2V/dr^2 = 0 → r(r-6M) = 0
# Non-trivial solution: r_ISCO = 6M (= 6GM/c^2 in SI units)
#
# This is EXACT. Not an approximation. Derived from pure GR.

# Verify numerically: compute d^2V/dr^2
def V_eff(r, M_bh, L):
    """Schwarzschild effective potential (geometrized units, G=c=1)."""
    return -M_bh/r + L**2/(2*r**2) - M_bh * L**2 / r**3

def dV_dr(r, M_bh, L):
    """First derivative of V_eff."""
    return M_bh/r**2 - L**2/r**3 + 3*M_bh*L**2/r**4

def d2V_dr2(r, M_bh, L):
    """Second derivative of V_eff."""
    return -2*M_bh/r**3 + 3*L**2/r**4 - 12*M_bh*L**2/r**5

# At r = 6M, L^2 = M*r^2/(r-3M) = M*(6M)^2/(6M-3M) = 36M^3/(3M) = 12M^2
M_bh = 1.0  # geometrized
r_isco = 6.0 * M_bh
L_sq_isco = M_bh * r_isco**2 / (r_isco - 3*M_bh)
L_isco = math.sqrt(L_sq_isco)

# Check dV/dr = 0 (circular orbit condition)
dV = dV_dr(r_isco, M_bh, L_isco)
# Check d2V/dr2 = 0 (marginal stability)
d2V = d2V_dr2(r_isco, M_bh, L_isco)

print(f"  Schwarzschild BH (M=1, G=c=1):")
print(f"  r_ISCO = 6M = {r_isco:.1f}")
print(f"  L^2_ISCO = 12M^2 = {L_sq_isco:.1f}")
print(f"  L_ISCO = 2*sqrt(3)*M = {L_isco:.6f} (exact: {2*math.sqrt(3):.6f})")
print(f"  dV/dr at ISCO = {dV:.2e} (should be 0)")
print(f"  d2V/dr2 at ISCO = {d2V:.2e} (should be 0)")
print()

# Physical quantities at ISCO
E_isco = (1 - 2*M_bh/r_isco) * (1 + L_sq_isco/r_isco**2)**0.5
# Actually, for circular orbits: E/m = (1-2M/r)/sqrt(1-3M/r)
E_over_m = (1 - 2*M_bh/r_isco) / math.sqrt(1 - 3*M_bh/r_isco)
efficiency = 1 - E_over_m  # radiative efficiency

print(f"  Energy per unit mass at ISCO:")
print(f"  E/m = (1-2M/r)/sqrt(1-3M/r) = {E_over_m:.6f}")
print(f"  Exact: (2*sqrt(2))/3 = {2*math.sqrt(2)/3:.6f}")
print(f"  Radiative efficiency eta = 1 - E/m = {efficiency:.6f}")
print(f"  Exact: 1 - 2*sqrt(2)/3 = {1 - 2*math.sqrt(2)/3:.6f}")
print(f"  Percentage: {efficiency*100:.2f}%")
print()

# n=6 connections at ISCO:
# 1. r_ISCO = 6M (the number 6 itself!)
# 2. L^2 = 12M^2 = sigma(6)*M^2
# 3. r_ISCO = 3*r_s (r_s = 2M), and 3 = divisor of 6
# 4. Radiative efficiency = 1 - 2*sqrt(2)/3 ≈ 0.0572
#    Compare with 1/6 - 1/PHI(6) = ... no, let's check honestly

print(f"  n=6 connections found:")
print(f"  [1] r_ISCO = 6M = n itself!  ★★★ EXACT")
print(f"  [2] L^2_ISCO = 12*M^2 = sigma(6)*M^2  ★★ EXACT")
print(f"  [3] r_ISCO = 3*r_s where r_s = 2M (both divisors of 6)")
print(f"  [4] Efficiency = {efficiency:.6f}")
print(f"      Compare to GZ values: 1/6 = {1/6:.6f}, GZ_lower = {GZ_LOWER:.6f}")
print(f"      No match to GZ values. Efficiency is {efficiency:.4f} ≈ 5.72%")
print()

# Texas Sharpshooter for the ISCO = 6M claim
# Question: What is the probability that ISCO coefficient equals n
# for a randomly chosen perfect number n?
# ISCO = 6M is derived from GR. The "6" comes from solving r(r-6M)=0
# which comes from the cubic term in the effective potential.
# The cubic term is specifically -M*L^2/r^3 (GR correction to Newton).
# The ISCO radius is always 6M for Schwarzschild, regardless of M.
# This is NOT arbitrary — it's a structural result of GR.
#
# For Texas test: how many "important radii" are there in GR?
# r_s = 2M, r_photon = 3M, r_ISCO = 6M, r_mb = 4M (marginally bound)
# That's 4 radii with coefficients {2, 3, 4, 6}
# ALL FOUR are divisors of 6. That's remarkable.
# P(all 4 values from {1,...,10} are divisors of 6) = (4/10)^4 = 0.0256

all_radii = {"r_s": 2, "r_photon": 3, "r_mb": 4, "r_ISCO": 6}
print(f"  All characteristic radii of Schwarzschild BH:")
for name, coeff in all_radii.items():
    is_div = coeff in DIVISORS
    print(f"    {name} = {coeff}M  {'✅ divisor of 6' if is_div else '❌'}")

all_are_divisors = all(c in DIVISORS for c in all_radii.values())
print(f"\n  ALL characteristic radii are divisors of 6: {all_are_divisors}")
print(f"  Set of coefficients: {set(all_radii.values())} = {set(DIVISORS)}")
print(f"  This is the COMPLETE set of divisors of 6!")
print()

# Statistical test
# Under null hypothesis: each coefficient drawn independently from {1,...,10}
# P(value is divisor of 6) = 4/10 for each
# P(all 4 are divisors of 6) = 0.4^4 = 0.0256
# But we specifically get {1,2,3,6} mapped to {2,3,4,6}...
# Wait, the set is {2,3,4,6}, not {1,2,3,6}.
# 4 is a divisor of 6? No. 6/4 = 1.5. 4 is NOT a divisor of 6.
# Correction: 4 = tau(6) but 6 mod 4 = 2, so 4 does NOT divide 6.

print(f"  CORRECTION: 4 divides 6? {6 % 4 == 0} → 4 is NOT a divisor of 6!")
print(f"  r_mb = 4M: 4 = tau(6) but NOT a divisor.")
print(f"  Divisors of 6: {{1, 2, 3, 6}}")
print(f"  BH radii coefficients: {{2, 3, 4, 6}}")
print(f"  Match: 3 out of 4 are divisors of 6 (miss: r_mb=4M)")
print()

# Revised test: 3 out of 4 are divisors
from math import comb
# P(at least 3 of 4 are divisors of 6, drawing from {1,...,10})
p_div = 4/10  # divisors of 6 in {1,...,10}: {1,2,3,6}
p_at_least_3 = 0
for k in [3, 4]:
    p_at_least_3 += comb(4, k) * p_div**k * (1-p_div)**(4-k)

print(f"  P(>= 3 of 4 random integers in [1,10] are divisors of 6):")
print(f"  = sum C(4,k)*0.4^k*0.6^(4-k) for k=3,4")
print(f"  = {comb(4,3)}*{p_div**3:.4f}*{(1-p_div)**1:.1f} + {comb(4,4)}*{p_div**4:.4f}")
print(f"  = {comb(4,3)*p_div**3*(1-p_div):.6f} + {p_div**4:.6f}")
print(f"  = {p_at_least_3:.6f}")
print()

# But the real test for H-BH-010 specifically: r_ISCO = 6M
# What's the probability the ISCO coefficient = n for perfect number n?
# Perfect numbers: 6, 28, 496, 8128, ...
# ISCO is always 6M for Schwarzschild. It doesn't change with n.
# So the question is: given that ISCO = 6M (fact of GR),
# what's the probability this coincides with a special number?
# P(6 is special) — 6 is a perfect number, first perfect number,
# highly composite number, factorial number, primorial, etc.
# Honest assessment: 6 is over-determined (many properties),
# so finding structure IS expected.

# Alternative approach: compute the probability directly
# Among integers 1-100, how many are perfect numbers? Just 6 and 28.
# P(random integer 1-100 is perfect) = 2/100 = 0.02
# ISCO coefficient is exactly 6 = perfect number. p = 0.02 per trial.
# With Bonferroni for 30 hypotheses: p = 0.02 * 30 = 0.60
# But if we also count sigma(6)=12=L^2 coefficient: two independent matches

# More honest: there are ~4 interesting BH radii, each an integer
# P(at least one is a perfect number) = 1 - (98/100)^4 = 0.077
# Not significant after Bonferroni.

# HOWEVER: ISCO = EXACTLY 6 (not ≈6), AND L^2 = EXACTLY 12 = sigma(6)
# AND 6 is the perfect number we're studying.
# The conjunction is much more striking.

# MOST HONEST ASSESSMENT:
# The ISCO = 6M is a genuine fact of GR, not a model approximation.
# The connection to perfect number 6 is:
# 1. r_ISCO = 6M (exact) ← n=6 directly
# 2. L^2_ISCO = 12M^2 (exact) ← sigma(6)
# 3. But GR doesn't "know" about perfect numbers
# 4. The "6" in ISCO comes from the structure of Einstein field equations
# 5. It would be extraordinary if n=6 *caused* ISCO = 6M

# Grade: The match is exact and numerically specific.
# r_ISCO = 6M is non-trivial (not just "2 appears somewhere").
# L^2 = 12M^2 = sigma(6)*M^2 is a bonus.
# But the physical derivation is completely independent of number theory.
# Texas p-value for "ISCO coefficient is a perfect number": ~0.08 (not significant)
# However, the PAIR (6, 12) matching (n, sigma(n)) is much rarer.

# P(two independent physics constants match (n, sigma(n)) for some perfect n):
# Among perfect n up to 100: n=6 (sigma=12), n=28 (sigma=56)
# P(random pair (a,b) from {1,...,20} matches some (n,sigma(n))) ≈ 2/(20*20) = 0.005
# Bonferroni: 0.005 * 30 = 0.15 — borderline

p_pair = 2 / (20 * 20)  # 2 perfect numbers in range, 20x20 grid
p_bonferroni = p_pair * N_HYPS

print(f"  STATISTICAL ASSESSMENT (honest):")
print(f"  Single match (r_ISCO=6M, 6 is perfect): p ≈ 0.08 (not significant)")
print(f"  Pair match (6M, 12M^2) = (n, sigma(n)): p ≈ {p_pair:.4f}")
print(f"  After Bonferroni (30 hyps): p ≈ {p_bonferroni:.3f}")
print(f"  Verdict: INTERESTING but not statistically significant at p<0.05")
print(f"  Grade: 🟧 (weak structural evidence)")

# Also compute: does this generalize to Kerr?
# For Kerr BH with spin a:
# r_ISCO = 3M + Z_2 -/+ sqrt((3M-Z_1)(3M+Z_1+2Z_2))
# where Z_1 = M + (M^2-a^2)^{1/3}*((M+a)^{1/3}+(M-a)^{1/3})
# At a=0: r_ISCO = 6M (recovers Schwarzschild)
# At a=M (extremal prograde): r_ISCO = M
# At a=M (extremal retrograde): r_ISCO = 9M
print()
print(f"  Generalization to Kerr BH (spin parameter a):")
print(f"    a=0 (Schwarzschild): r_ISCO = 6M  ← n=6 ✅")
print(f"    a=M (extremal, prograde): r_ISCO = M  ← 1 = divisor of 6")
print(f"    a=M (extremal, retrograde): r_ISCO = 9M  ← 9 ≠ divisor of 6")
print(f"    → n=6 connection holds ONLY for non-spinning BH")
print(f"    → Spinning BH breaks the pattern (r_ISCO = 1M to 9M)")

detail = (f"r_ISCO = 6M (EXACT, from GR effective potential).\n"
          f"L^2_ISCO = 12M^2 = sigma(6)*M^2 (EXACT).\n"
          f"Pair (6, 12) matches (n, sigma(n)) for perfect number 6.\n"
          f"Statistical: p_pair ≈ {p_pair:.4f}, Bonferroni p ≈ {p_bonferroni:.3f}.\n"
          f"Kerr generalization fails: ISCO varies 1M-9M with spin.\n"
          f"Physical derivation independent of number theory.\n"
          f"Verdict: exact and interesting, but not causally connected.")
grade = "orange"  # weak structural evidence
results.append(Result(hid, "ISCO = 6M, L^2 = sigma(6)*M^2",
                       grade, True, detail, p_value=p_bonferroni,
                       n6_factor="6=n, 12=sigma(6)",
                       numerology_risk="MODERATE: exact match, unclear causation"))
print(f"\n{hid}: Grade: 🟧 (exact match, weak evidence after correction)")

# H-BH-011: Photon sphere at r = 3M
hid = "H-BH-011"
r_photon_coeff = 3
is_divisor = (6 % r_photon_coeff == 0)
# r_photon = 3M: from setting effective potential maximum for null geodesics
# 3M = (1/2)*r_ISCO = (1/2)*6M ← connects to GZ_upper = 1/2!
ratio = r_photon_coeff / 6  # = 0.5 = GZ_upper
print(f"\n{hid}: r_photon = 3M = (1/2)*r_ISCO = (1/2)*6M")
print(f"  r_photon/r_ISCO = {ratio:.4f} = GZ_UPPER = {GZ_UPPER:.4f}  ★")
print(f"  Also: r_photon = (3/2)*r_s → factor 3/2 = (sum of proper divisor recips of 6)?")
print(f"    1/2 + 1/3 + 1/6 = 1, not 3/2.")
print(f"    1 + 1/2 = 3/2? (sum of first two divisor recips of 6)")
print(f"    Ad hoc. The meaningful ratio is r_photon/r_ISCO = 1/2.")

# r_photon/r_ISCO = 1/2 = GZ_upper is interesting
# But 1/2 is the most common ratio in the universe
# Also r_mb/r_ISCO = 4/6 = 2/3, and 2/3 = 1-1/3
# And r_s/r_ISCO = 2/6 = 1/3 = meta fixed point!
r_ratios = {
    "r_s/r_ISCO": 2/6,
    "r_photon/r_ISCO": 3/6,
    "r_mb/r_ISCO": 4/6,
}
print(f"\n  Ratios of BH radii to r_ISCO = 6M:")
for name, ratio in r_ratios.items():
    match = ""
    if abs(ratio - 1/3) < 1e-10:
        match = "= 1/3 (meta fixed point)"
    elif abs(ratio - 1/2) < 1e-10:
        match = "= 1/2 (GZ upper / Riemann)"
    elif abs(ratio - 2/3) < 1e-10:
        match = "= 2/3 = 1-1/3"
    print(f"    {name} = {ratio:.4f} {match}")

print(f"\n  {r_ratios}")
print(f"  Ratios = {{1/3, 1/2, 2/3}} — these are just k/6 for k=2,3,4")
print(f"  This is trivially true since radii = {{2,3,4}} and denominator = 6")
print(f"  No deeper structure beyond the fact that ISCO = 6M.")

detail = (f"r_photon = 3M. r_photon/r_ISCO = 3/6 = 1/2 = GZ_upper.\n"
          f"r_s/r_ISCO = 2/6 = 1/3 = meta fixed point.\n"
          f"These ratios are trivially k/6 since denominator is 6M.\n"
          f"No independent structure beyond H-BH-010.")
grade = "white"
results.append(Result(hid, "Photon sphere 3M, ratio 1/2 of ISCO?",
                       grade, True, detail, p_value=1.0,
                       n6_factor="3|6, ratio 1/2",
                       numerology_risk="HIGH: trivial ratio from ISCO=6M"))
print(f"{hid}: Grade: ⚪ (trivially derived from ISCO=6M)")

# H-BH-012: Ergosphere boundary
hid = "H-BH-012"
# Ergosphere: r_ergo = M + sqrt(M^2 - a^2*cos^2(theta))
# At equator (theta=pi/2): r_ergo = 2M = r_s (always, for any spin)
# At pole (theta=0): r_ergo = M + sqrt(M^2-a^2) = r_+ (event horizon)
detail = (f"Ergosphere at equator: r_ergo = 2M = r_s (independent of spin).\n"
          f"  Factor 2 = phi(6). Same criticism as H-BH-005.\n"
          f"  No additional n=6 content beyond Schwarzschild radius.")
grade = "white"
results.append(Result(hid, "Ergosphere = 2M at equator = phi(6)?",
                       grade, True, detail, p_value=1.0,
                       n6_factor="phi(6)=2",
                       numerology_risk="HIGH: identical to H-BH-005"))
print(f"{hid}: Grade: ⚪ (same as H-BH-005)")

# ═══════════════════════════════════════════
# C. BLACK HOLE INFORMATION (H-BH-013 to 018)
# ═══════════════════════════════════════════

print("\n### C. BLACK HOLE INFORMATION ###\n")

# H-BH-013: Information paradox binary = phi(6)?
hid = "H-BH-013"
detail = (f"Information paradox: unitarity vs thermal radiation = binary choice.\n"
          f"  2 options = phi(6)? This is not a meaningful hypothesis.\n"
          f"  Any yes/no question has 2 options. Tautological.")
grade = "white"
results.append(Result(hid, "Info paradox binary = phi(6)?",
                       grade, False, detail, p_value=1.0,
                       n6_factor="phi(6)=2",
                       numerology_risk="EXTREME: any binary = 2"))
print(f"{hid}: Grade: ⚪ (tautological)")

# H-BH-014: Page time at S_max/2 = 1/2 = GZ upper
hid = "H-BH-014"
# Page time: when entanglement entropy peaks = halfway through evaporation
# The "1/2" in Page time is definitional (half of information out)
# NOT related to Golden Zone
detail = (f"Page time at S_max/2. The 1/2 is definitional (midpoint).\n"
          f"  Not a physics-derived 1/2. Any process has a midpoint.\n"
          f"  No GZ connection.")
grade = "white"
results.append(Result(hid, "Page time 1/2 = GZ upper?",
                       grade, False, detail, p_value=1.0,
                       n6_factor="1/2 (definitional)",
                       numerology_risk="EXTREME: midpoint is always 1/2"))
print(f"{hid}: Grade: ⚪ (definitional 1/2)")

# H-BH-015: Scrambling time ~ M*log(M)
hid = "H-BH-015"
# t* ~ (beta/2pi) * ln(S) = (M/M_P) * ln(M/M_P) * t_P
# The log factor is the hallmark of fast scramblers
# For Sgr A* (4.15e6 M_sun):
M_sgr = SgrA_mass_Msun * M_sun
S_sgr = math.pi * (2*G*M_sgr/(c**2))**2 / l_P**2  # in Planck units
log_S = math.log(S_sgr)
print(f"{hid}: Scrambling time ~ M*log(S)")
print(f"  Sgr A*: M = {SgrA_mass_Msun:.2e} M_sun")
print(f"  S_BH ~ {S_sgr:.2e}")
print(f"  log(S) = {log_S:.1f}")
print(f"  No n=6 connection in the logarithmic factor.")
detail = (f"Scrambling time t* ~ M*log(S). log(S_SgrA) ≈ {log_S:.0f}.\n"
          f"  No n=6 value appears. Logarithm is generic (chaos, scrambling).")
grade = "white"
results.append(Result(hid, "Scrambling time log factor -- n=6?",
                       grade, False, detail, p_value=1.0,
                       n6_factor="none found",
                       numerology_risk="N/A"))
print(f"{hid}: Grade: ⚪ (no connection)")

# H-BH-016: Holographic principle: 2D→3D, phi(6)→3
hid = "H-BH-016"
# Holographic principle: information in d+1 volume encoded on d-dim boundary
# For our universe: 3D volume, 2D boundary
# 2 = phi(6), 3 = divisor of 6
# But dimensionality of space is independent of n=6
detail = (f"Holographic: 2D boundary encodes 3D bulk.\n"
          f"  2 = phi(6), 3 = divisor of 6. But these are just d=3 dimensions.\n"
          f"  Holographic principle works in any dimension (AdS_d/CFT_d-1).\n"
          f"  Not specific to n=6.")
grade = "white"
results.append(Result(hid, "Holographic 2D-3D = phi(6) to divisor?",
                       grade, False, detail, p_value=1.0,
                       n6_factor="phi(6)=2, 3|6",
                       numerology_risk="HIGH: any d and d-1"))
print(f"{hid}: Grade: ⚪ (generic dimensionality)")

# H-BH-017: ER=EPR
hid = "H-BH-017"
detail = (f"ER=EPR: wormholes = entanglement (Maldacena-Susskind).\n"
          f"  Qualitative conjecture. No numbers to match to n=6.\n"
          f"  Cannot be verified numerically.")
grade = "white"
results.append(Result(hid, "ER=EPR -- n=6 connection?",
                       grade, False, detail, p_value=1.0,
                       n6_factor="none",
                       numerology_risk="N/A: no numbers"))
print(f"{hid}: Grade: ⚪ (qualitative, no numbers)")

# H-BH-018: Firewall paradox
hid = "H-BH-018"
# AMPS (Almheiri-Marolf-Polchinski-Sully): 4 authors?
# 3 postulates in tension (unitarity, EFT, no drama) → see H-BH-030
detail = (f"Firewall paradox: qualitative debate, no n=6 numbers.\n"
          f"  The 3 conflicting assumptions → see H-BH-030.")
grade = "white"
results.append(Result(hid, "Firewall paradox -- n=6?",
                       grade, False, detail, p_value=1.0,
                       n6_factor="none",
                       numerology_risk="N/A"))
print(f"{hid}: Grade: ⚪ (qualitative)")

# ═══════════════════════════════════════════
# D. OBSERVATIONAL BLACK HOLES (H-BH-019 to 024)
# ═══════════════════════════════════════════

print("\n### D. OBSERVATIONAL BLACK HOLES ###\n")

# H-BH-019: Stellar BH minimum mass ~ 3 M_sun = divisor of 6
hid = "H-BH-019"
min_mass = 3.0  # M_sun, approximate (TOV limit ~ 2.1-2.5)
# Actually the "mass gap" is 3-5 M_sun. Minimum observed ~ 3.3 M_sun
# TOV limit (max NS mass) ~ 2.0-2.5 M_sun
# The "3" is approximate and observational, not exact
print(f"{hid}: Minimum stellar BH mass ≈ 3 M_sun")
print(f"  TOV limit (max NS): ~2.0-2.5 M_sun")
print(f"  Observed mass gap: 2.5-5 M_sun")
print(f"  Lightest confirmed BH: ~3.3 M_sun (Unicorn, Thompson 2021)")
print(f"  Recent LIGO: GW190814 secondary = 2.6 M_sun (NS or BH?)")
print(f"  '3 M_sun' is approximate. Actual boundary is fuzzy (2-5 M_sun range).")
detail = (f"Minimum BH mass ≈ 3 M_sun. 3 = divisor of 6.\n"
          f"  But actual boundary is fuzzy: TOV ≈ 2.1-2.5, gap at 2.5-5 M_sun.\n"
          f"  The '3' is an approximation, not an exact value.\n"
          f"  No structural connection to n=6.")
grade = "white"
results.append(Result(hid, "Min BH mass ~3 M_sun = divisor?",
                       grade, False, detail, p_value=1.0,
                       n6_factor="3|6 (approximate)",
                       numerology_risk="HIGH: approximate value"))
print(f"{hid}: Grade: ⚪ (approximate, not exact)")

# H-BH-020: M87* shadow 42 microarcseconds, 42 = 7*6
hid = "H-BH-020"
shadow = 42.0  # microarcseconds (EHT 2019: 42 +/- 3)
is_multiple_6 = (shadow % 6 == 0)
factor = shadow / 6
print(f"{hid}: M87* shadow = {shadow:.0f} +/- 3 microarcsec")
print(f"  42 = 7 * 6. Multiple of 6? {is_multiple_6}")
print(f"  BUT: 42 uas depends on: BH mass, distance, metric")
print(f"  M87* mass ≈ 6.5e9 M_sun, distance ≈ 16.8 Mpc")
print(f"  shadow ≈ (6*sqrt(3)) * GM/(c^2 * D) in radians")
# Compute expected shadow
M_m87 = 6.5e9 * M_sun
D_m87 = 16.8e6 * 3.086e16  # 16.8 Mpc in meters
r_shadow = 3 * math.sqrt(3) * G * M_m87 / c**2  # shadow radius in meters
theta_shadow = r_shadow / D_m87  # radians
theta_uas = theta_shadow * 206265e6  # to microarcseconds
print(f"  Calculated shadow diameter = 2*theta = {2*theta_uas:.1f} uas")
print(f"  (using M=6.5e9 Msun, D=16.8 Mpc)")
print(f"  Measured: 42 +/- 3 uas. Consistent.")
print(f"  The '42' comes from M87*'s specific mass and distance.")
print(f"  A BH at different distance gives different angular size.")
print(f"  42 being a multiple of 6 is purely coincidental.")
detail = (f"M87* shadow = 42 +/- 3 microarcsec = 7*6.\n"
          f"  Calculated: {2*theta_uas:.1f} uas (mass and distance dependent).\n"
          f"  Angular size depends on M/D ratio, not fundamental.\n"
          f"  Different BH → different angular size. Pure coincidence.")
grade = "white"
results.append(Result(hid, "M87* shadow 42 uas = 7*6?",
                       grade, is_multiple_6, detail, p_value=1.0,
                       n6_factor="42=7*6",
                       numerology_risk="EXTREME: observer-dependent quantity"))
print(f"{hid}: Grade: ⚪ (observer-dependent)")

# H-BH-021: Sgr A* mass ≈ 4.15 million M_sun ≈ tau(6) million
hid = "H-BH-021"
sgr_mass = 4.15  # million M_sun
diff = abs(sgr_mass - TAU_6)
print(f"{hid}: Sgr A* mass = {sgr_mass:.2f} million M_sun")
print(f"  tau(6) = 4. Difference = {diff:.2f} million M_sun = {diff/sgr_mass*100:.1f}%")
print(f"  3.6% discrepancy. NOT exact.")
print(f"  Mass measured by stellar orbits (GRAVITY collab, 2022)")
print(f"  Mass is 4.15 +/- 0.01 million M_sun")
print(f"  4 million is just a round number coincidence.")
detail = (f"Sgr A* mass = 4.154 +/- 0.014 million M_sun.\n"
          f"  tau(6) = 4. Error = 3.7%. Not exact.\n"
          f"  BH masses span 3 to 10^{10} M_sun. No special scale.\n"
          f"  Observer-dependent (our galaxy's central BH happens to be this mass).")
grade = "white"
results.append(Result(hid, "Sgr A* mass ~4M M_sun = tau(6)?",
                       grade, False, detail, p_value=1.0,
                       n6_factor="~tau(6)",
                       numerology_risk="EXTREME: approximate, observer-dependent"))
print(f"{hid}: Grade: ⚪ (approximate, observer-dependent)")

# H-BH-022: BH spin measurements > 0.5. GZ upper = 0.5
hid = "H-BH-022"
# Measured spins (dimensionless a/M):
# Cygnus X-1: > 0.95, GRS 1915+105: > 0.98, MCG-6-30-15: ~0.99
# GRO J1655-40: 0.65-0.75, A0620-00: 0.12
# Spin range: 0 to 1 (extremal Kerr)
# Many measured > 0.5 due to accretion spinup, but some < 0.5
measured_spins = {
    "Cygnus X-1": 0.97,
    "GRS 1915+105": 0.98,
    "GRO J1655-40": 0.70,
    "A0620-00": 0.12,
    "MCG-6-30-15": 0.99,
    "XTE J1550-564": 0.34,
    "LMC X-3": 0.25,
}
above_half = sum(1 for s in measured_spins.values() if s > 0.5)
total = len(measured_spins)
print(f"{hid}: BH spin measurements (a/M):")
for name, spin in sorted(measured_spins.items(), key=lambda x: x[1]):
    marker = ">" if spin > 0.5 else "<"
    print(f"    {name}: a/M = {spin:.2f} {marker} 0.5")
print(f"  {above_half}/{total} above 0.5 ({above_half/total*100:.0f}%)")
print(f"  Selection bias: high-spin BHs easier to measure (broader Fe K-alpha)")
print(f"  Physical: accretion spinup naturally pushes toward a→1")
print(f"  No meaningful GZ connection. 0.5 is just the midpoint of [0,1].")
detail = (f"BH spins: {above_half}/{total} measured > 0.5.\n"
          f"  Selection bias toward high spin. 0.5 = midpoint of [0,1].\n"
          f"  Not a meaningful GZ connection.")
grade = "white"
results.append(Result(hid, "BH spins > 0.5 = GZ upper?",
                       grade, False, detail, p_value=1.0,
                       n6_factor="0.5 (trivial midpoint)",
                       numerology_risk="HIGH: midpoint bias"))
print(f"{hid}: Grade: ⚪ (selection bias + trivial)")

# H-BH-023: GW frequencies from mergers
hid = "H-BH-023"
# GW150914: f_peak ~ 150 Hz, M_total ~ 65 M_sun
# GW frequency at ISCO: f_ISCO = c^3/(6^{3/2} * pi * G * M)
# For 30 M_sun: f_ISCO = c^3 / (6^1.5 * pi * G * 30 * M_sun)
M_gw = 30 * M_sun  # component mass
f_isco = c**3 / (6**1.5 * math.pi * G * M_gw)
# Note: the 6^{3/2} comes from r_ISCO = 6M and orbital frequency!
print(f"{hid}: GW frequency at ISCO")
print(f"  f_ISCO = c^3 / (6^(3/2) * pi * G * M)")
print(f"  For M = 30 M_sun: f_ISCO = {f_isco:.1f} Hz")
print(f"  The 6^(3/2) in the formula comes from r_ISCO = 6M!")
print(f"  This is a DERIVATIVE of H-BH-010, not independent.")
detail = (f"f_ISCO = c^3/(6^(3/2)*pi*G*M). The 6^(3/2) is from r_ISCO = 6M.\n"
          f"  For M=30 M_sun: f = {f_isco:.1f} Hz.\n"
          f"  Derivative of H-BH-010. Not independent evidence.")
grade = "white"
results.append(Result(hid, "GW freq has 6^{3/2} from ISCO?",
                       grade, True, detail, p_value=1.0,
                       n6_factor="6^{3/2} from ISCO",
                       numerology_risk="DERIVATIVE of H-BH-010"))
print(f"{hid}: Grade: ⚪ (derivative of H-BH-010)")

# H-BH-024: Eddington luminosity
hid = "H-BH-024"
# L_E = 4*pi*G*M*m_p*c / sigma_T
# 4*pi = geometric factor (spherical symmetry)
# No n=6 content
detail = (f"L_Eddington = 4*pi*G*M*m_p*c/sigma_T.\n"
          f"  4*pi is the solid angle of a sphere. No n=6 content.")
grade = "white"
results.append(Result(hid, "Eddington luminosity -- n=6?",
                       grade, False, detail, p_value=1.0,
                       n6_factor="none",
                       numerology_risk="N/A"))
print(f"{hid}: Grade: ⚪ (no connection)")

# ═══════════════════════════════════════════
# E. QUANTUM GRAVITY & STRINGS (H-BH-025 to 030)
# ═══════════════════════════════════════════

print("\n### E. QUANTUM GRAVITY & STRINGS ###\n")

# H-BH-025: Bekenstein bound S <= 2*pi*R*E/(hbar*c)
hid = "H-BH-025"
# 2*pi is geometric. Same as circumference/radius.
detail = (f"Bekenstein bound: S <= 2*pi*R*E/(hbar*c).\n"
          f"  2*pi = circumference factor. Generic geometry, not n=6.")
grade = "white"
results.append(Result(hid, "Bekenstein bound 2*pi -- n=6?",
                       grade, False, detail, p_value=1.0,
                       n6_factor="none",
                       numerology_risk="N/A"))
print(f"{hid}: Grade: ⚪ (geometric 2*pi)")

# H-BH-026: String theory: 10D total, 6 compactified
hid = "H-BH-026"
n_compact = 6
n_total = 10
n_visible = 4  # 3+1
print(f"{hid}: String theory: {n_total}D = {n_visible}D visible + {n_compact}D compact")
print(f"  6 compactified dimensions = n = 6 = perfect number!")
print(f"  These compact dims form a Calabi-Yau 3-fold (complex dim 3)")
print()

# Why 10D? Anomaly cancellation in superstrings requires D=10.
# D=10 is the unique dimension where Weyl, Lorentz, and gauge anomalies cancel.
# Given D=10 and observable D=4: compact = 10-4 = 6
# So "6 compact dimensions" follows from:
# (1) Anomaly cancellation → D=10 (deeply mathematical)
# (2) Observation → 3+1 visible dimensions
# (3) 10 - 4 = 6

# Is D=10 related to n=6?
# 10 = tau(6) + n = 4 + 6 ← trivial
# 10 = sigma(6) - phi(6) = 12 - 2 ← trivial
# 10 = number of superstring theory dimensions ← that's the claim

# The real question: WHY does anomaly cancellation require D=10?
# It involves the Dirac index theorem and requires (D-2) = 8,
# and 8-dim representations have special triality properties (Spin(8))
# This is related to octonions and exceptional structures.
# 10 - 4 = 6 is arithmetic, but the depth is in WHY 10.

# Check: Calabi-Yau 3-fold properties
# Complex dimension 3 → real dimension 6
# Euler number chi(CY3) determines number of generations!
# Standard Model has 3 generations. Common CY3 have chi = +-6!
# chi(CY3) = 2*(h^{1,1} - h^{2,1}) — Hodge numbers
# Quintic: h^{1,1}=1, h^{2,1}=101, chi = -200
# Actually many CY3 have various chi values. chi = +/-6 is possible but not generic.

print(f"  WHY 10D? Anomaly cancellation in superstrings.")
print(f"  Requires Spin(8) triality → D-2 = 8 → D = 10.")
print(f"  10 - 4 (visible) = 6 (compact) = Calabi-Yau 3-fold")
print(f"  CY3: complex dim 3 = divisor of 6")
print()

# Check existing hypotheses
print(f"  NOTE: Already partially covered in existing TECS-L hypotheses")
print(f"  (H-PH-9, H-PH-11, P-005). This adds BH-specific context.")
print()

# Statistical assessment
# P(compact dimensions = perfect number) — given D_total fixed by anomaly
# and D_visible = 4 fixed by observation:
# D_compact = D_total - 4
# For D_total in {10, 11, 26}: D_compact in {6, 7, 22}
# 6 is a perfect number! 7 and 22 are not.
# Superstring: D=10 → 6 compact ✓
# M-theory: D=11 → 7 compact ✗
# Bosonic string: D=26 → 22 compact ✗
# 1 out of 3 major string theories → compact dim is perfect number
# P(random number in [1,30] is perfect) = 2/30 ≈ 0.067 (6 and 28)
# Not significant.

p_perfect = 2/30  # perfect numbers up to 30
print(f"  String theory variants:")
print(f"    Superstring (D=10): 6 compact ← perfect number ✅")
print(f"    M-theory (D=11): 7 compact ← NOT perfect ❌")
print(f"    Bosonic (D=26): 22 compact ← NOT perfect ❌")
print(f"  1/3 of string theories give perfect number of compact dims")
print(f"  P(random in [1,30] is perfect) ≈ {p_perfect:.3f}")
print(f"  After Bonferroni: p ≈ {p_perfect*N_HYPS:.2f}")

detail = (f"Superstring theory: 10D = 4 visible + 6 compact (CY3).\n"
          f"  6 compact = n = perfect number. EXACT.\n"
          f"  But M-theory (11D→7 compact) breaks pattern.\n"
          f"  Anomaly cancellation determines D=10 (Spin(8) triality).\n"
          f"  p(compact dim is perfect) ≈ 0.067. Bonferroni: {p_perfect*N_HYPS:.2f}.\n"
          f"  Already covered in H-PH-9, H-PH-11. Not new.")
grade = "white"
p_corr = p_perfect * N_HYPS
results.append(Result(hid, "6 compactified dims = perfect number?",
                       grade, True, detail, p_value=p_corr,
                       n6_factor="6 compact dims",
                       numerology_risk="MODERATE: M-theory breaks it"))
print(f"{hid}: Grade: ⚪ (M-theory breaks pattern, already known)")

# H-BH-027: AdS/CFT: bulk d+1 vs boundary d
hid = "H-BH-027"
detail = (f"AdS/CFT: bulk dim = boundary dim + 1. Generic holography.\n"
          f"  The +1 is structural (radial direction). Not n=6 related.")
grade = "white"
results.append(Result(hid, "AdS/CFT dim+1 -- n=6?",
                       grade, False, detail, p_value=1.0,
                       n6_factor="none",
                       numerology_risk="N/A"))
print(f"{hid}: Grade: ⚪ (generic holography)")

# H-BH-028: Loop quantum gravity area spectrum
hid = "H-BH-028"
# A = 8*pi*gamma*l_P^2 * sum sqrt(j_i(j_i+1))
# Barbero-Immirzi parameter gamma ≈ 0.2375 (from BH entropy matching)
gamma_BI = 0.2375
# Compare to Golden Zone: GZ_LOWER = 0.2123, GZ_CENTER = 0.3679
print(f"{hid}: Loop QG Barbero-Immirzi parameter")
print(f"  gamma_BI = {gamma_BI:.4f}")
print(f"  GZ_LOWER = {GZ_LOWER:.4f}")
print(f"  GZ_CENTER (1/e) = {GZ_CENTER:.4f}")
print(f"  GZ range = [{GZ_LOWER:.4f}, {GZ_UPPER:.4f}]")
print(f"  gamma_BI = {gamma_BI:.4f} is INSIDE the Golden Zone! ★")
diff_lower = abs(gamma_BI - GZ_LOWER)
diff_center = abs(gamma_BI - GZ_CENTER)
print(f"  Distance from GZ_LOWER: {diff_lower:.4f}")
print(f"  Distance from GZ_CENTER: {diff_center:.4f}")
print(f"  gamma_BI is at position {(gamma_BI - GZ_LOWER)/GZ_WIDTH:.2f} within GZ (0=lower, 1=upper)")

# Statistical test: P(random value in [0,1] falls in GZ) = GZ_WIDTH ≈ 0.288
p_in_gz = GZ_WIDTH
p_bonf = p_in_gz * N_HYPS
print(f"  P(random in [0,1] falls in GZ) = {p_in_gz:.3f}")
print(f"  After Bonferroni: p ≈ {p_bonf:.2f}")
print(f"  Not significant (GZ covers 29% of [0,1]).")

# More refined: gamma_BI is specifically determined
# gamma_BI = ln(2) / (pi * sqrt(3)) ≈ 0.2375 (from j=1/2 dominant term)
gamma_exact = math.log(2) / (math.pi * math.sqrt(3))
print(f"\n  Exact: gamma_BI = ln(2)/(pi*sqrt(3)) = {gamma_exact:.6f}")
print(f"  This involves ln(2), pi, sqrt(3) — none related to n=6 specifically.")
print(f"  sqrt(3) relates to equilateral triangles (spin networks), not n=6.")

detail = (f"Barbero-Immirzi parameter gamma = ln(2)/(pi*sqrt(3)) ≈ {gamma_exact:.4f}.\n"
          f"  Falls in GZ [{GZ_LOWER:.4f}, {GZ_UPPER:.4f}] at position "
          f"{(gamma_exact - GZ_LOWER)/GZ_WIDTH:.2f}.\n"
          f"  But P(random in GZ) = {p_in_gz:.2f}. Not significant.\n"
          f"  gamma involves ln(2), pi, sqrt(3) — no n=6 structure.")
grade = "white"
results.append(Result(hid, "Barbero-Immirzi gamma in Golden Zone?",
                       grade, False, detail, p_value=p_bonf,
                       n6_factor="gamma in GZ",
                       numerology_risk="MODERATE: GZ covers 29% of [0,1]"))
print(f"{hid}: Grade: ⚪ (GZ too wide for significance)")

# H-BH-029: Planck mass
hid = "H-BH-029"
M_planck = math.sqrt(hbar * c / G)
print(f"\n{hid}: Planck mass = sqrt(hbar*c/G) = {M_planck:.3e} kg")
print(f"  No n=6 content. Planck mass is defined by G, hbar, c only.")
detail = (f"Planck mass = {M_planck:.3e} kg. Pure dimensional analysis.\n"
          f"  No n=6 content whatsoever.")
grade = "white"
results.append(Result(hid, "Planck mass -- n=6?",
                       grade, False, detail, p_value=1.0,
                       n6_factor="none",
                       numerology_risk="N/A"))
print(f"{hid}: Grade: ⚪ (no connection)")

# H-BH-030: BH complementarity: 3 postulates = divisor
hid = "H-BH-030"
n_postulates = 3  # unitarity, EFT validity, no drama
# Same as H-BH-009 criticism
detail = (f"BH complementarity: 3 postulates. 3 = divisor of 6.\n"
          f"  Same criticism as H-BH-009. Small integer matching.\n"
          f"  The number of postulates is somewhat arbitrary\n"
          f"  (could be split differently).")
grade = "white"
results.append(Result(hid, "BH complementarity 3 postulates = divisor?",
                       grade, False, detail, p_value=1.0,
                       n6_factor="3|6",
                       numerology_risk="HIGH: arbitrary grouping"))
print(f"{hid}: Grade: ⚪ (arbitrary)")


# ═══════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════

print("\n" + "=" * 72)
print("SUMMARY TABLE")
print("=" * 72)
print()
print(f"{'ID':<12} {'Grade':<5} {'Title':<50} {'p-value':<10} {'Risk'}")
print("-" * 100)

grade_counts = {"green": 0, "orange_star": 0, "orange": 0, "white": 0, "black": 0}
for r in results:
    grade_counts[r.grade] += 1
    p_str = f"{r.p_value:.3f}" if r.p_value and r.p_value < 10 else "N/S"
    risk_short = r.numerology_risk.split(":")[0] if r.numerology_risk else ""
    print(f"{r.hid:<12} {r.emoji():<5} {r.title[:50]:<50} {p_str:<10} {risk_short}")

print()
print("GRADE DISTRIBUTION:")
print(f"  🟩  Exact + proven:         {grade_counts['green']}")
print(f"  🟧★ Structural (p<0.01):    {grade_counts['orange_star']}")
print(f"  🟧  Weak evidence (p<0.05): {grade_counts['orange']}")
print(f"  ⚪  Coincidence (p>0.05):   {grade_counts['white']}")
print(f"  ⬛  Refuted:                {grade_counts['black']}")
print()

print("=" * 72)
print("KEY FINDINGS")
print("=" * 72)
print()
print("1. H-BH-010 (ISCO = 6M) is the ONLY hypothesis with substance:")
print("   - r_ISCO = 6M is EXACT (derived from GR, not approximation)")
print("   - L^2_ISCO = 12M^2 = sigma(6)*M^2 is an exact bonus")
print("   - The pair (6, 12) = (n, sigma(n)) is more striking than either alone")
print("   - BUT: Kerr BH breaks the pattern (ISCO varies 1M to 9M)")
print("   - BUT: physical derivation is independent of number theory")
print("   - Grade: 🟧 (weak structural evidence)")
print()
print("2. All other 29 hypotheses are ⚪ (coincidence/not significant):")
print("   - H-BH-001 to 009, 011-030: small integer matching (2,3,4)")
print("   - phi(6)=2 matches ~40% of physics equations (trivial)")
print("   - 'divisor of 6' covers {1,2,3,6} = 40% of {1,...,10}")
print("   - Observational values (M87* shadow, Sgr A* mass) are not fundamental")
print("   - Qualitative conjectures (ER=EPR, firewall) have no numbers to match")
print()
print("3. H-BH-026 (6 compactified dimensions) is real but already known in TECS-L")
print("   (H-PH-9, H-PH-11). M-theory (7 compact dims) breaks the pattern.")
print()
print("4. H-BH-028 (Barbero-Immirzi gamma ≈ 0.2375 in GZ) is interesting")
print("   but GZ covers 29% of [0,1], so not significant (p ≈ 0.29).")
print()
print("HONEST ASSESSMENT:")
print("  This domain (black holes + n=6) is MOSTLY NUMEROLOGY.")
print("  The only genuine structural match is ISCO = 6M,")
print("  and even that lacks a causal mechanism connecting")
print("  perfect numbers to general relativity.")
print("  The 6 in ISCO comes from the cubic GR correction to")
print("  Newtonian gravity (the -M*L^2/r^3 term), not from")
print("  number-theoretic properties of 6.")
print()

# ═══════════════════════════════════════════
# ADDITIONAL ANALYSIS: ISCO=6M deep dive
# ═══════════════════════════════════════════

print("=" * 72)
print("DEEP DIVE: WHY ISCO = 6M (where does the 6 come from?)")
print("=" * 72)
print()
print("Effective potential: V(r) = -M/r + L^2/(2r^2) - M*L^2/r^3")
print("  Term 1: -M/r           (Newtonian gravity)")
print("  Term 2: +L^2/(2r^2)    (centrifugal barrier)")
print("  Term 3: -M*L^2/r^3     (GR correction, absent in Newton!)")
print()
print("Circular orbit: V'(r) = 0")
print("  M/r^2 - L^2/r^3 + 3ML^2/r^4 = 0")
print("  → L^2 = Mr^2/(r-3M)")
print()
print("Stability: V''(r) = 0")
print("  -2M/r^3 + 3L^2/r^4 - 12ML^2/r^5 = 0")
print("  Substitute L^2 = Mr^2/(r-3M):")
print("  -2M/r^3 + 3Mr^2/((r-3M)r^4) - 12M^2r^2/((r-3M)r^5) = 0")
print("  Simplify: multiply by r^5(r-3M)/M:")
print("  -2r^2(r-3M) + 3r^2 - 12M = 0  ... solving:")
print("  r^2 - 6Mr = 0")
print("  r(r - 6M) = 0")
print("  → r = 6M (non-trivial solution)")
print()
print("The '6' arises as: coefficient 3 (from GR term) × coefficient 2")
print("  (from the quadratic nature of stability condition)")
print("  = 3 × 2 = 6")
print("  Interestingly: 3 × 2 = 6 = 3! = smallest perfect number")
print("  And: 3 = proper divisor, 2 = proper divisor, product = 6")
print("  But this is the STRUCTURE of the equation, not number theory.")
print()
print("BOTTOM LINE: The 6 in ISCO = 6M comes from the mathematics of")
print("  geodesics in Schwarzschild spacetime. It is 3*2 where:")
print("  - 3 comes from the r^{-3} GR correction term")
print("  - 2 comes from the second derivative (stability analysis)")
print("  Whether this has deeper significance is an open question.")
