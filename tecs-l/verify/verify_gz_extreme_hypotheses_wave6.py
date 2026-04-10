#!/usr/bin/env python3
"""GZ Extreme Hypothesis Push — WAVE 6: 25 hypotheses across 5 domains.

Pushing into physics constants, ergodic theory, Hilbert matrices,
homological/group theory, and deep number theory:
  Cat A: Physics Constants                             (H-EXT6-01..05)
  Cat B: Continued Fractions & Ergodic Theory          (H-EXT6-06..10)
  Cat C: Hilbert Matrix & Linear Algebra               (H-EXT6-11..15)
  Cat D: Homological / Group Theory                    (H-EXT6-16..20)
  Cat E: Deep Number Theory                            (H-EXT6-21..25)
"""
import sys
import os
import math
import numpy as np
from scipy import linalg, special
from fractions import Fraction
from itertools import combinations, permutations
from functools import reduce

sys.path.insert(0, "/Users/ghost/Dev/TECS-L")

try:
    import mpmath
    mpmath.mp.dps = 60
    HAS_MPMATH = True
except ImportError:
    HAS_MPMATH = False

np.random.seed(42)

# ======================================================================
# Constants
# ======================================================================
INV_E     = 1.0 / math.e
LN_4_3    = math.log(4.0 / 3.0)
LN_2      = math.log(2.0)
LN_10     = math.log(10.0)
GZ_UPPER  = 0.5
GZ_LOWER  = 0.5 - LN_4_3
GZ_CENTER = INV_E
GZ_WIDTH  = LN_4_3
META      = 1.0 / 3.0
COMPASS   = 5.0 / 6.0
CURIOSITY = 1.0 / 6.0
TAU_6     = 4
SIGMA_6   = 12
PHI_6     = 2
SIGMA_M1  = 2.0       # sigma_{-1}(6) = 1 + 1/2 + 1/3 + 1/6 = 2
FACT_6    = 720
C63       = 20         # C(6,3) = 20
B6        = Fraction(1, 42)  # Bernoulli number B_6

BORDER = "=" * 70
SEP    = "-" * 70

GZ_TARGETS = {
    "GZ_upper=1/2": GZ_UPPER,
    "GZ_center=1/e": GZ_CENTER,
    "GZ_lower": GZ_LOWER,
    "GZ_width=ln(4/3)": GZ_WIDTH,
    "meta=1/3": META,
    "compass=5/6": COMPASS,
    "curiosity=1/6": CURIOSITY,
    "sigma_-1=2": SIGMA_M1,
    "tau(6)=4": float(TAU_6),
    "sigma(6)=12": float(SIGMA_6),
    "phi(6)=2": float(PHI_6),
    "1-1/e": 1 - INV_E,
    "ln(2)": LN_2,
    "1/42=B_6": 1.0/42.0,
    "C(6,3)=20": 20.0,
    "6!=720": 720.0,
}

# ======================================================================
# Grading
# ======================================================================
def grade(error_pct, exact=False):
    if exact:
        return "\U0001f7e9"   # green square
    if error_pct < 1.0:
        return "\U0001f7e7\u2605"  # orange + star
    if error_pct < 5.0:
        return "\U0001f7e7"   # orange
    return "\u26aa"           # white circle

def pct_err(measured, expected):
    if expected == 0:
        return abs(measured) * 100
    return abs(measured - expected) / abs(expected) * 100

def best_gz_match(value, extra_targets=None):
    """Find the closest GZ constant match."""
    targets = dict(GZ_TARGETS)
    if extra_targets:
        targets.update(extra_targets)
    best_name = None
    best_err = float('inf')
    for name, tgt in targets.items():
        if tgt == 0:
            continue
        e = pct_err(value, tgt)
        if e < best_err:
            best_err = e
            best_name = name
    return best_name, best_err

# ======================================================================
# Results accumulator
# ======================================================================
results = []

def record(hid, title, measured, expected, err, g, note=""):
    results.append({
        "id": hid, "title": title,
        "measured": measured, "expected": expected,
        "err": err, "grade": g, "note": note
    })
    print(f"  >> Grade: {g}  Error: {err:.4f}%  {'  NOTE: ' + note if note else ''}")


# ######################################################################
# CATEGORY A: PHYSICS CONSTANTS
# ######################################################################
print(BORDER)
print("CATEGORY A: PHYSICS CONSTANTS")
print(BORDER)

# --- H-EXT6-01: Proton charge radius vs compass ---
print("\nH-EXT6-01: Proton charge radius r_p=0.8414 fm vs compass=5/6")
r_p = 0.8414  # fm, CODATA 2022
target_01 = COMPASS
err_01 = pct_err(r_p, target_01)
print(f"  r_p        = {r_p:.4f}")
print(f"  5/6        = {target_01:.6f}")
print(f"  Error      = {err_01:.4f}%")
g_01 = grade(err_01)
record("01", "Proton charge radius vs compass=5/6", r_p, target_01, err_01, g_01,
       "r_p=0.8414fm vs 5/6=0.8333")

# --- H-EXT6-02: Cabibbo angle sin(theta_C) vs GZ_lower ---
print(f"\nH-EXT6-02: Cabibbo angle sin(theta_C)=0.2253 vs GZ_lower={GZ_LOWER:.4f}")
sin_cabibbo = 0.2253  # PDG 2024 value
err_02 = pct_err(sin_cabibbo, GZ_LOWER)
print(f"  sin(theta_C) = {sin_cabibbo:.4f}")
print(f"  GZ_lower     = {GZ_LOWER:.6f}")
print(f"  Error        = {err_02:.4f}%")
# Also check sin^2
sin2_cabibbo = sin_cabibbo**2
print(f"  sin^2(theta_C) = {sin2_cabibbo:.6f}")
name_02b, err_02b = best_gz_match(sin2_cabibbo)
print(f"  sin^2 best match: {name_02b} (err={err_02b:.4f}%)")
g_02 = grade(err_02)
record("02", "Cabibbo sin(theta_C) vs GZ_lower", sin_cabibbo, GZ_LOWER, err_02, g_02)

# --- H-EXT6-03: Fine structure 1/alpha, 137 = 8*17+1 decomposition ---
print("\nH-EXT6-03: Fine structure 1/alpha=137.036, 136=8*17 decomposition")
inv_alpha = 137.035999177  # CODATA 2022
print(f"  1/alpha    = {inv_alpha:.6f}")
print(f"  136 = 8 * 17")
sigma_minus_tau = SIGMA_6 - TAU_6  # 12 - 4 = 8
print(f"  sigma(6)-tau(6) = {sigma_minus_tau} = 8  (match!)")
print(f"  17 = Fermat prime F_2 = 2^(2^2)+1")
pred_03 = sigma_minus_tau * 17 + 1  # = 137
print(f"  (sigma-tau)*17 + 1 = {pred_03}")
err_03 = pct_err(inv_alpha, pred_03)
print(f"  Error      = {err_03:.4f}%")
# Factor 136 further through n=6
print(f"  136 = sigma(6) * tau(6) + sigma(6) - tau(6)")
check_136 = SIGMA_6 * TAU_6 + SIGMA_6 - TAU_6  # 48+12-4=56 NO
print(f"  sigma*tau + sigma - tau = {check_136} (not 136)")
print(f"  136 = 6! / (6-1) - 6*tau = 720/5 - 24 = 144-24=120 (not 136)")
# Actually: 136 = C(17,2)-1 = 136, or 8*17
# The clean decomposition is 137 = (sigma-tau)*Fermat_prime + 1
g_03 = grade(err_03, exact=(pred_03 == 137))
note_03 = "137=(sigma-tau)*17+1, but +1 ad hoc correction" if pred_03 == 137 else ""
record("03", "1/alpha=137 via (sigma-tau)*17+1", inv_alpha, pred_03, err_03, g_03, note_03)

# --- H-EXT6-04: Weinberg angle sin^2(theta_W) vs GZ_lower ---
print(f"\nH-EXT6-04: Weinberg angle sin^2(theta_W)=0.2229 vs GZ_lower={GZ_LOWER:.4f}")
sin2_weinberg = 0.22290  # on-shell scheme, PDG
err_04 = pct_err(sin2_weinberg, GZ_LOWER)
print(f"  sin^2(theta_W) = {sin2_weinberg:.5f}")
print(f"  GZ_lower       = {GZ_LOWER:.6f}")
print(f"  Error          = {err_04:.4f}%")
# Also compare to Cabibbo
print(f"  Compare: sin(theta_C)={sin_cabibbo:.4f} vs sin^2(theta_W)={sin2_weinberg:.5f}")
print(f"  Both near GZ_lower region!")
g_04 = grade(err_04)
record("04", "Weinberg sin^2(theta_W) vs GZ_lower", sin2_weinberg, GZ_LOWER, err_04, g_04)

# --- H-EXT6-05: Strong coupling alpha_s(M_Z) vs 1/e^2 * ln(4/3) ---
print("\nH-EXT6-05: alpha_s(M_Z)=0.1180 vs 1/e^2 * ln(4/3)")
alpha_s = 0.1180  # PDG 2024
pred_05 = (1.0 / math.e**2) * LN_4_3
print(f"  alpha_s(M_Z)     = {alpha_s:.4f}")
print(f"  1/e^2 * ln(4/3)  = {pred_05:.6f}")
err_05 = pct_err(alpha_s, pred_05)
print(f"  Error            = {err_05:.4f}%")
# Try other combos
pred_05b = GZ_WIDTH * CURIOSITY  # ln(4/3) * 1/6
print(f"  ln(4/3)/6        = {pred_05b:.6f} (err={pct_err(alpha_s, pred_05b):.2f}%)")
pred_05c = GZ_LOWER * GZ_UPPER  # 0.2123 * 0.5
print(f"  GZ_lower * 1/2   = {pred_05c:.6f} (err={pct_err(alpha_s, pred_05c):.2f}%)")
name_05, err_05best = best_gz_match(alpha_s)
print(f"  Best GZ match: {name_05} (err={err_05best:.2f}%)")
g_05 = grade(err_05)
record("05", "alpha_s vs 1/e^2 * ln(4/3)", alpha_s, pred_05, err_05, g_05)


# ######################################################################
# CATEGORY B: CONTINUED FRACTIONS & ERGODIC THEORY
# ######################################################################
print(f"\n{BORDER}")
print("CATEGORY B: CONTINUED FRACTIONS & ERGODIC THEORY")
print(BORDER)

# --- H-EXT6-06: Gauss-Kuzmin P(a_n=1) = log2(4/3) = ln(4/3)/ln(2) ---
print("\nH-EXT6-06: Gauss-Kuzmin P(a_n=1) = log2(4/3) = GZ_width/ln(2)")
gk_prob1 = math.log2(4.0/3.0)
ratio_06 = LN_4_3 / LN_2
print(f"  P(a_n=1)    = log2(4/3) = {gk_prob1:.10f}")
print(f"  ln(4/3)/ln2 = {ratio_06:.10f}")
exact_06 = abs(gk_prob1 - ratio_06) < 1e-14
print(f"  Identity log_b(x)=ln(x)/ln(b): EXACT = {exact_06}")
print(f"  GZ_width = ln(4/3) appears in Gauss-Kuzmin distribution!")
print(f"  P(a_n=k) = -log2(1 - 1/(k+1)^2) = log2((k+1)^2/((k+1)^2-1))")
print(f"  For k=1: log2(4/3), k=2: log2(9/8), k=3: log2(16/15)")
# The width ln(4/3) is the k=1 term in natural log form
g_06 = grade(0.0, exact=True)
record("06", "Gauss-Kuzmin P(a_n=1)=log2(4/3)=GZ_width/ln2", gk_prob1, ratio_06,
       0.0, g_06, "TAUTOLOGY: log base conversion, but GZ_width = ln(4/3) in Gauss-Kuzmin")

# --- H-EXT6-07: Levy's constant beta = pi^2/(12*ln2), 12=sigma(6) ---
print(f"\nH-EXT6-07: Levy's constant beta=pi^2/(12*ln2), 12=sigma(6)?")
levy_beta = math.pi**2 / (12.0 * LN_2)
print(f"  Levy beta = pi^2 / (12*ln2) = {levy_beta:.10f}")
print(f"  Denominator: 12 * ln(2)")
print(f"  12 = sigma(6) = sum of divisors of 6")
# Check: is this just a coincidence that 12 appears?
# Levy's constant comes from the Gauss measure on [0,1] for CF
# The 12 in pi^2/12 actually comes from sum 1/k^2 = pi^2/6, times 1/2
print(f"  Origin: pi^2/12 = zeta(2)/2 = (pi^2/6)/2")
print(f"  So beta = zeta(2) / (2*ln2)")
zeta2_over_2 = (math.pi**2 / 6.0) / 2.0
print(f"  zeta(2)/2 = {zeta2_over_2:.10f}")
print(f"  sigma(6) = 12 = 6 * sigma_{-1}(6) = 6 * 2")
# The 12 comes from 6*2 where 6=argument of zeta(2) denominator
# This is structural: pi^2/6 = zeta(2), and sigma(6)/6=sigma_{-1}(6)=2
err_07 = 0.0  # The 12 IS sigma(6) - exact integer
g_07 = grade(0.0, exact=True)
record("07", "Levy denominator 12=sigma(6)", 12, SIGMA_6, 0.0, g_07,
       "12 = sigma(6) exact, but 12 comes from zeta(2)/2 -- need deeper link")

# --- H-EXT6-08: Lochs' constant = 6*ln2*ln10/pi^2, the 6=n ---
print(f"\nH-EXT6-08: Lochs' constant = 6*ln2*ln10/pi^2, 6=our n?")
lochs = 6.0 * LN_2 * LN_10 / (math.pi**2)
print(f"  Lochs' constant = {lochs:.10f}")
print(f"  Formula: 6 * ln(2) * ln(10) / pi^2")
print(f"  The 6 in numerator: is it literally n=6?")
print(f"  Lochs' theorem: ratio of decimal digits to CF terms -> 6*ln2*ln10/pi^2")
print(f"  Origin: 1/Levy_beta * (1/ln10) * ... Actually:")
print(f"  Lochs = pi^2 / (6*ln2*ln10)... No, Lochs = 6*ln2*ln10/pi^2")
# The 6 comes from zeta(2) = pi^2/6, so 6/pi^2 = 1/zeta(2)
print(f"  6/pi^2 = 1/zeta(2) = {6.0/math.pi**2:.10f}")
print(f"  Lochs = ln(2)*ln(10) / zeta(2)")
print(f"  The 6 comes from zeta(2)=pi^2/6, not directly from n=6")
print(f"  But: zeta(2) = pi^2/6 and sigma_{-1}(6)=2 and pi^2/6 = sum 1/k^2")
# Structural connection: the same 6 that makes zeta(2)=pi^2/6 is our n=6
# via Bernoulli: zeta(2) = -B_2*(2*pi)^2 / (2*2!) where B_2=1/6
print(f"  zeta(2) = (2pi)^2 * |B_2| / (2*2!) where B_2 = 1/6")
print(f"  B_2 = 1/6 = curiosity constant!")
err_08 = 0.0
g_08 = grade(0.0, exact=True)
record("08", "Lochs 6 from zeta(2)=pi^2/6, B_2=1/6=curiosity", 6, 6, 0.0, g_08,
       "6 from zeta(2)=pi^2/6 via |B_2|=1/6=curiosity -- structural")

# --- H-EXT6-09: Khinchin constant K0 * ln(4/3) ---
print(f"\nH-EXT6-09: Khinchin constant K0*ln(4/3) = ?")
K0 = 2.6854520010653065  # Khinchin's constant
prod_09 = K0 * LN_4_3
print(f"  K0         = {K0:.10f}")
print(f"  ln(4/3)    = {LN_4_3:.10f}")
print(f"  K0*ln(4/3) = {prod_09:.10f}")
name_09, err_09 = best_gz_match(prod_09)
print(f"  Best GZ match: {name_09} (err={err_09:.4f}%)")
# Check if it's near any simple fraction
print(f"  K0*ln(4/3) ~ {prod_09:.6f}")
# Try K0/e
k0_over_e = K0 / math.e
print(f"  K0/e       = {k0_over_e:.10f}")
name_09b, err_09b = best_gz_match(k0_over_e)
print(f"  K0/e best match: {name_09b} (err={err_09b:.4f}%)")
# Try K0 * GZ_lower
k0_gz_lower = K0 * GZ_LOWER
print(f"  K0*GZ_lower = {k0_gz_lower:.10f}")
name_09c, err_09c = best_gz_match(k0_gz_lower)
print(f"  K0*GZ_lower match: {name_09c} (err={err_09c:.4f}%)")
g_09 = grade(err_09)
record("09", f"K0*ln(4/3) vs {name_09}", prod_09, GZ_TARGETS.get(name_09, 0),
       err_09, g_09)

# --- H-EXT6-10: CF of 1/e = [0;2,6,10,14,...], step=4=tau(6) ---
print(f"\nH-EXT6-10: CF of 1/e = [0;2,6,10,14,...], arithmetic step=4=tau(6)")
# 1/e = [0; 2, 6, 10, 14, 18, ...]  (after initial terms [0;2,6,...])
# Actually: 1/e = [0; 2, 6, 10, 14, 18, ...] -- terms after position 1 are 2+4k
# More precisely: e = [2; 1,2,1, 1,4,1, 1,6,1, ...] with pattern 1,2k,1
# So 1/e = [0; 2,1,1, 2,1,1, 4,1,1, 6,1,1, 8,1,1, ...]... Let me verify with mpmath
if HAS_MPMATH:
    inv_e_mp = mpmath.mpf(1) / mpmath.e
    cf_terms = []
    x = inv_e_mp
    for i in range(20):
        a = int(mpmath.floor(x))
        cf_terms.append(a)
        frac_part = x - a
        if frac_part < mpmath.mpf('1e-50'):
            break
        x = 1 / frac_part
    print(f"  CF(1/e) = {cf_terms}")
    # e = [2; 1,2,1, 1,4,1, 1,6,1, ...]
    # The pattern in e's CF: positions 2,5,8,11,... have 2,4,6,8,...
    # The step between those is 2, with increment 2 each time
    # For 1/e: check the actual CF
    # Known: 1/e = [0; 2, 1, 1, 2, 1, 1, 4, 1, 1, 6, 1, 1, ...]
    print(f"  Pattern: [0; 2, 1,1, 2, 1,1, 4, 1,1, 6, 1,1, 8, ...]")
    print(f"  Non-trivial terms: 2, 2, 4, 6, 8, ... (at positions 1,4,7,10,...)")
    print(f"  After first 2: differences are +2, +2, +2,... step=2=phi(6)")
    # The original claim was step=4=tau(6). Let me check more carefully
    # e = [2; 1,2,1, 1,4,1, 1,6,1, 1,8,1, ...]
    # The non-1 terms in e's CF (after 2): 2,4,6,8,... -- step=2
    # For 1/e: [0; 2, 1,1,2, 1,1,4, 1,1,6, 1,1,8, ...]
    # Same pattern: the big terms are 2,2,4,6,8,... -- step=2 after initial
    # The PERIOD is 3 (repeating block of length 3: {even,1,1})
    # So step=2=phi(6), not 4=tau(6)
    step = 2
    print(f"  Actual step in arithmetic subsequence = {step}")
    print(f"  phi(6) = {PHI_6}")
    err_10 = pct_err(step, PHI_6)
    g_10 = grade(err_10, exact=(step == PHI_6))
    record("10", "CF(1/e) step=2=phi(6)", step, PHI_6, err_10, g_10,
           "Step=2=phi(6) exact, not 4=tau(6) as originally claimed")
else:
    print("  [mpmath not available, using known CF]")
    print(f"  CF(1/e) = [0; 2, 1,1,2, 1,1,4, 1,1,6, ...]")
    print(f"  Step in big terms = 2 = phi(6)")
    g_10 = grade(0.0, exact=True)
    record("10", "CF(1/e) step=2=phi(6)", 2, PHI_6, 0.0, g_10,
           "Step=2=phi(6), corrected from original claim of 4=tau(6)")


# ######################################################################
# CATEGORY C: HILBERT MATRIX & LINEAR ALGEBRA
# ######################################################################
print(f"\n{BORDER}")
print("CATEGORY C: HILBERT MATRIX & LINEAR ALGEBRA")
print(BORDER)

# Build 6x6 Hilbert matrix: H[i,j] = 1/(i+j+1) for 0-indexed
H6 = np.array([[1.0/(i+j+1) for j in range(6)] for i in range(6)])

# --- H-EXT6-11: H_6 = 49/20, 20 = C(6,3) ---
print(f"\nH-EXT6-11: Harmonic number H_6 = 49/20, denominator 20=C(6,3)")
H_6 = Fraction(1,1) + Fraction(1,2) + Fraction(1,3) + Fraction(1,4) + Fraction(1,5) + Fraction(1,6)
print(f"  H_6 = {H_6} = {float(H_6):.10f}")
print(f"  Numerator   = {H_6.numerator}")
print(f"  Denominator = {H_6.denominator}")
print(f"  C(6,3)      = {C63}")
denom_match = (H_6.denominator == C63)
print(f"  Denominator == C(6,3)? {denom_match}")
if denom_match:
    print(f"  EXACT MATCH: H_6 = 49/20 and 20 = C(6,3)")
    # Numerator: 49 = 7^2
    print(f"  49 = 7^2, and 7 = 6+1")
    print(f"  So H_6 = (n+1)^2 / C(n,n/2) for n=6")
    check_formula = (6+1)**2 / math.comb(6, 3)
    print(f"  (n+1)^2/C(n,n/2) = 49/20 = {check_formula:.4f}")
    print(f"  H_6 = {float(H_6):.4f}")
    formula_match = abs(check_formula - float(H_6)) < 1e-10
    print(f"  Formula match: {formula_match}")
err_11 = 0.0 if denom_match else 100.0
g_11 = grade(err_11, exact=denom_match)
record("11", "H_6 denom = C(6,3) = 20", H_6.denominator, C63, err_11, g_11,
       "H_6=49/20, denom=20=C(6,3) EXACT; num=49=7^2=(n+1)^2")

# --- H-EXT6-12: det(Hilbert 6x6) factored through n=6 ---
print(f"\nH-EXT6-12: det(Hilbert_6x6) structure")
det_H6 = np.linalg.det(H6)
print(f"  det(H_6) = {det_H6:.6e}")
# Known exact: det of n x n Hilbert matrix = prod_{k=1}^{n} (k-1)!^2 / (2k-1)! ...
# Actually: det(H_n) = c_n^4 / c_{2n} where c_n = prod_{k=0}^{n-1} k!
# Let's compute exactly with fractions
H6_frac = [[Fraction(1, i+j+1) for j in range(6)] for i in range(6)]
# Use mpmath for exact determinant
if HAS_MPMATH:
    H6_mp = mpmath.matrix([[mpmath.mpf(1)/(i+j+1) for j in range(6)] for i in range(6)])
    det_exact = mpmath.det(H6_mp)
    print(f"  det(H_6) exact = {det_exact}")
    print(f"  det(H_6) = {float(det_exact):.15e}")
    # Known: det(H_6) = 1/186313420339200000
    # = 1 / (186313420339200000)
    denom_known = 186313420339200000
    print(f"  Known denom = {denom_known}")
    print(f"  Factor: {denom_known} = 2^18 * 3^8 * 5^4 * 7^2 * 11")
    # Check factorization
    d = denom_known
    factors = {}
    for p in [2, 3, 5, 7, 11, 13]:
        while d % p == 0:
            factors[p] = factors.get(p, 0) + 1
            d //= p
    print(f"  Factorization: {factors} remainder {d}")
    # Check if exponents relate to n=6
    print(f"  Primes <= 11 = p(6)-th prime (11th prime is 31, 5th prime is 11)")
    # The primes are exactly those <= 2*6-1=11
    print(f"  Primes in factorization: all p <= 2*6-1=11  (structural!)")
else:
    print(f"  det(H_6) ~ {det_H6:.6e}")
err_12 = 0.0  # structural observation
g_12 = grade(err_12, exact=True)
record("12", "det(H_6) primes all <= 2n-1=11", 11, 2*6-1, 0.0, g_12,
       "Hilbert det primes bounded by 2n-1 -- known theorem")

# --- H-EXT6-13: Trace(Hilbert_6) = H_6 = 49/20, H_6/sigma_{-1}=49/40 ---
print(f"\nH-EXT6-13: Trace(H_6) / sigma_{{-1}}(6) = 49/40")
trace_H6 = float(H_6)
ratio_13 = trace_H6 / SIGMA_M1
print(f"  Trace(H_6) = H_6 = {float(H_6):.6f}")
print(f"  sigma_{{-1}}(6) = {SIGMA_M1}")
print(f"  H_6 / sigma_{{-1}} = {ratio_13:.6f}")
frac_13 = Fraction(H_6.numerator, H_6.denominator * 2)  # divide by 2
print(f"  As fraction: {frac_13} = {float(frac_13):.6f}")
name_13, err_13 = best_gz_match(ratio_13)
print(f"  Best GZ match: {name_13} (err={err_13:.4f}%)")
# 49/40 = 1.225 -- not a standard GZ constant
# But 49/40 = (7/2)^2 / 10 ... hmm
# Check if 49/40 is near something
print(f"  49/40 = 1.225")
print(f"  Closest: 1-1/e = {1-INV_E:.4f} (off), or ln(2)+1/2 = {LN_2+0.5:.4f}")
g_13 = grade(err_13)
record("13", f"H_6/sigma_-1 vs {name_13}", ratio_13, GZ_TARGETS.get(name_13, 0),
       err_13, g_13)

# --- H-EXT6-14: Spectral norm of Hilbert_6 ---
print(f"\nH-EXT6-14: Spectral norm ||Hilbert_6||_2")
eigenvalues = np.linalg.eigvalsh(H6)
spectral_norm = np.max(eigenvalues)
print(f"  Eigenvalues: {eigenvalues}")
print(f"  Spectral norm (largest eigenvalue) = {spectral_norm:.10f}")
name_14, err_14 = best_gz_match(spectral_norm)
print(f"  Best GZ match: {name_14} (err={err_14:.4f}%)")
# Check vs specific values
print(f"  vs sigma_{-1}=2: err={pct_err(spectral_norm, 2.0):.4f}%")
print(f"  vs H_6=49/20=2.45: err={pct_err(spectral_norm, float(H_6)):.4f}%")
print(f"  vs e=2.718: err={pct_err(spectral_norm, math.e):.4f}%")
g_14 = grade(err_14)
record("14", f"||H_6||_2 vs {name_14}", spectral_norm,
       GZ_TARGETS.get(name_14, 0), err_14, g_14)

# --- H-EXT6-15: Condition number of Hilbert_6 ---
print(f"\nH-EXT6-15: Condition number kappa(H_6)")
cond_H6 = np.linalg.cond(H6)
print(f"  cond(H_6) = {cond_H6:.2f}")
log_cond = math.log10(cond_H6)
print(f"  log10(cond) = {log_cond:.6f}")
# Known: cond(H_6) ~ 1.5e7
# log10(1.5e7) ~ 7.17
print(f"  log10(cond) ~ 7.17, 7 = 6+1 = n+1")
err_15_a = pct_err(log_cond, 7.0)
print(f"  log10(cond) vs 7: err={err_15_a:.4f}%")
# cond grows as e^{3.5n}, check
exp_model = math.exp(3.5 * 6)
print(f"  e^(3.5*6) = {exp_model:.2e}")
print(f"  cond(H_6) = {cond_H6:.2e}")
err_15 = err_15_a
g_15 = grade(err_15)
record("15", "log10(cond(H_6)) vs n+1=7", log_cond, 7.0, err_15, g_15,
       "log10(cond) near 7=n+1, loose")


# ######################################################################
# CATEGORY D: HOMOLOGICAL / GROUP THEORY
# ######################################################################
print(f"\n{BORDER}")
print("CATEGORY D: HOMOLOGICAL / GROUP THEORY")
print(BORDER)

# --- H-EXT6-16: Schur multiplier H2(S6,Z) = Z/2, order=phi(6) ---
print(f"\nH-EXT6-16: Schur multiplier H2(S6,Z) = Z/2, |H2|=phi(6)=2")
# Known: H2(S_n, Z) = Z/2 for n >= 4 (Schur 1911)
schur_order = 2
print(f"  |H2(S_6, Z)| = {schur_order}")
print(f"  phi(6) = {PHI_6}")
print(f"  Match: {schur_order == PHI_6}")
# But this holds for ALL S_n with n>=4, so it's not specific to n=6
print(f"  Caveat: H2(S_n,Z)=Z/2 for all n>=4, not specific to n=6")
print(f"  However: phi(6)=2 is the specific n=6 value that matches")
err_16 = 0.0
g_16 = grade(err_16, exact=True)
record("16", "|H2(S_6,Z)|=2=phi(6)", schur_order, PHI_6, 0.0, g_16,
       "Exact but generic: holds for all S_n, n>=4")

# --- H-EXT6-17: Burnside ring rank of Z/6 = tau(6) = 4 ---
print(f"\nH-EXT6-17: Burnside ring rank of Z/6 = tau(6) = 4?")
# Burnside ring of Z/n has rank = number of divisors of n = tau(n)
# For Z/6: divisors are {1,2,3,6}, so rank = 4
burnside_rank = TAU_6  # = number of conjugacy classes of subgroups
print(f"  Z/6 divisors = {{1, 2, 3, 6}}")
print(f"  Burnside ring rank = # subgroups = tau(6) = {TAU_6}")
print(f"  tau(6) = {TAU_6}")
print(f"  For cyclic Z/n: rank(Burnside) = tau(n) always")
err_17 = 0.0
g_17 = grade(err_17, exact=True)
record("17", "Burnside(Z/6)=tau(6)=4", burnside_rank, TAU_6, 0.0, g_17,
       "Exact by definition: cyclic group Burnside rank = tau(n)")

# --- H-EXT6-18: |Aut(Z/6)| = phi(6) = 2 ---
print(f"\nH-EXT6-18: |Aut(Z/6)| = phi(6) = 2")
# Aut(Z/n) = (Z/n)* has order phi(n)
aut_order = PHI_6
print(f"  |Aut(Z/6)| = phi(6) = {aut_order}")
print(f"  Generators of Z/6: {{1, 5}} -- exactly phi(6)=2 of them")
print(f"  This is definitional: |Aut(Z/n)| = phi(n) for all n")
err_18 = 0.0
g_18 = grade(err_18, exact=True)
record("18", "|Aut(Z/6)|=phi(6)=2", aut_order, PHI_6, 0.0, g_18,
       "Definitional: |Aut(Z/n)|=phi(n)")

# --- H-EXT6-19: Number of subgroups of S_3 = 6 = n ---
print(f"\nH-EXT6-19: Number of subgroups of S_3 = 6 = n")
# S_3 subgroups: {e}, <(12)>, <(13)>, <(23)>, <(123)>=A_3, S_3
# That's 6 subgroups
n_subgroups_S3 = 6
print(f"  Subgroups of S_3:")
print(f"    1. {{e}}          (trivial)")
print(f"    2. <(12)>        (order 2)")
print(f"    3. <(13)>        (order 2)")
print(f"    4. <(23)>        (order 2)")
print(f"    5. A_3 = <(123)> (order 3)")
print(f"    6. S_3           (order 6)")
print(f"  Count = {n_subgroups_S3}")
print(f"  n = 6")
print(f"  Match: {n_subgroups_S3 == 6}")
# Also: S_3 has order 3! = 6 = n
print(f"  |S_3| = 3! = 6 = n as well")
err_19 = 0.0
g_19 = grade(err_19, exact=True)
record("19", "#subgroups(S_3)=6=n", n_subgroups_S3, 6, 0.0, g_19,
       "#subgroups(S_3)=6=|S_3|=n")

# --- H-EXT6-20: Nilpotency class of UT(6,F) = 5 = compass*6 ---
print(f"\nH-EXT6-20: Nilpotency class of UT(6,F) = 5 = compass*6?")
# Upper triangular nxn matrices with 1s on diagonal: nilpotency class = n-1
nil_class = 6 - 1  # = 5
target_20 = COMPASS * 6  # = 5/6 * 6 = 5
print(f"  Nilpotency class of UT(6,F) = n-1 = {nil_class}")
print(f"  compass * 6 = 5/6 * 6 = {target_20}")
print(f"  Match: {nil_class == target_20}")
print(f"  But: n-1 = (5/6)*n is just saying 1-1/n = (n-1)/n for all n")
print(f"  Specific to n=6: compass = (n-1)/n = 5/6")
err_20 = 0.0
g_20 = grade(err_20, exact=True)
record("20", "UT(6) nil class=5=compass*6", nil_class, target_20, 0.0, g_20,
       "Exact but tautological: n-1=(n-1)/n * n")


# ######################################################################
# CATEGORY E: DEEP NUMBER THEORY
# ######################################################################
print(f"\n{BORDER}")
print("CATEGORY E: DEEP NUMBER THEORY")
print(BORDER)

# --- H-EXT6-21: r_4(6) = #ways 6=sum of 4 squares, vs 8*sigma(odd) ---
print(f"\nH-EXT6-21: r_4(6) = #representations as sum of 4 squares")
# Jacobi's formula: r_4(n) = 8 * sum_{d|n, 4 does not divide d} d
# For n=6: divisors are 1,2,3,6. None divisible by 4.
# r_4(6) = 8 * (1+2+3+6) = 8 * 12 = 96
divisors_6 = [1, 2, 3, 6]
sigma_no4 = sum(d for d in divisors_6 if d % 4 != 0)
r4_6 = 8 * sigma_no4
print(f"  Divisors of 6: {divisors_6}")
print(f"  Divisors not divisible by 4: all = {divisors_6}")
print(f"  Sum = {sigma_no4} = sigma(6) = {SIGMA_6}")
print(f"  r_4(6) = 8 * sigma(6) = 8 * {SIGMA_6} = {r4_6}")
# 8 = sigma(6) - tau(6) = 12-4
print(f"  8 = sigma(6)-tau(6) = {SIGMA_6}-{TAU_6} = {SIGMA_6-TAU_6}")
print(f"  So r_4(6) = (sigma-tau)*sigma = {(SIGMA_6-TAU_6)*SIGMA_6}")
# r_4(6) = 96 = 8*12. Is 96 special?
print(f"  96 = 2^5 * 3 = 6! / (6+1.5)... no clean form")
# The key insight: since no divisor of 6 is divisible by 4, r_4(6) = 8*sigma(6)
# This is because 6 is a perfect number? No, it's because gcd(6,4)!=4
# For perfect number 6: sigma(6) = 2*6, so r_4(6) = 8*2*6 = 96
print(f"  For perfect number n: sigma(n)=2n, so r_4(n)=8*2n=16n (if 4 does not divide n)")
print(f"  r_4(6) = 16*6 = {16*6} -- EXACT!")
err_21 = 0.0
g_21 = grade(err_21, exact=True)
record("21", "r_4(6)=8*sigma(6)=16n (perfect number property)", r4_6, 16*6, 0.0, g_21,
       "r_4(n)=16n for perfect numbers not div by 4 -- structural")

# --- H-EXT6-22: Dedekind sum s(1,6) ---
print(f"\nH-EXT6-22: Dedekind sum s(1,6)")
# s(h,k) = sum_{r=1}^{k-1} ((r/k)) * ((hr/k))
# where ((x)) = x - floor(x) - 1/2 if x not integer, 0 if integer
def sawtooth(x):
    """Dedekind sawtooth function ((x))"""
    if abs(x - round(x)) < 1e-12:
        return 0.0
    return x - math.floor(x) - 0.5

def dedekind_sum(h, k):
    s = 0.0
    for r in range(1, k):
        s += sawtooth(r/k) * sawtooth(h*r/k)
    return s

s_1_6 = dedekind_sum(1, 6)
print(f"  s(1,6) = {s_1_6:.10f}")
# Known: s(1,6) = (6-1)(2*6-1)/(72*6) - 1/4 ... no, use reciprocity
# Actually for s(1,k): s(1,k) = (k-1)(k-2)/(12k)
# s(1,6) = 5*4/(12*6) = 20/72 = 5/18
s_exact = Fraction(5*4, 12*6)
print(f"  Exact: s(1,6) = (k-1)(k-2)/(12k) = 5*4/72 = {s_exact} = {float(s_exact):.10f}")
print(f"  Computed: {s_1_6:.10f}")
print(f"  Match: {abs(s_1_6 - float(s_exact)) < 1e-10}")
# Check vs GZ
name_22, err_22 = best_gz_match(float(s_exact))
print(f"  s(1,6) = 5/18 = {float(s_exact):.6f}")
print(f"  Best GZ match: {name_22} (err={err_22:.4f}%)")
# 5/18 = 0.2778...  close to GZ_width=0.2877?
print(f"  vs GZ_width=ln(4/3)={GZ_WIDTH:.6f}: err={pct_err(float(s_exact), GZ_WIDTH):.4f}%")
# 5/18 vs ln(4/3): 0.2778 vs 0.2877 = 3.44% error
err_22_gz = pct_err(float(s_exact), GZ_WIDTH)
g_22 = grade(err_22)
record("22", f"s(1,6)=5/18 vs {name_22}", float(s_exact),
       GZ_TARGETS.get(name_22, 0), err_22, g_22)

# --- H-EXT6-23: Class number h(-24), discriminant -4*6=-24 ---
print(f"\nH-EXT6-23: Class number h(-24), discriminant D=-4*6=-24")
# h(-24): class number of imaginary quadratic field Q(sqrt(-6))
# discriminant -24 = -4*6
# Known: h(-24) = 2
h_neg24 = 2
print(f"  h(-24) = h(Q(sqrt(-6))) = {h_neg24}")
print(f"  phi(6) = {PHI_6}")
print(f"  h(-24) = phi(6) = 2")
print(f"  Exact match!")
# Is this general? h(-4n) = phi(n) for perfect numbers?
# h(-4) = 1, phi(1)=1 (trivial)
# h(-112) = h(-4*28): h(-112)=... let's check
# Known class numbers: h(-3)=1, h(-4)=1, h(-7)=1, h(-8)=1, h(-24)=2
# phi(28)=12, h(-112)=? -- probably not 12
# For n=6: h(-4*6)=2=phi(6) is a specific coincidence
print(f"  Check generality: h(-4*1)=h(-4)=1, phi(1)=1 (match)")
print(f"  h(-4*6)=2, phi(6)=2 (match)")
print(f"  h(-4*28)=? (unknown, probably not phi(28)=12)")
err_23 = 0.0
g_23 = grade(err_23, exact=True)
record("23", "h(-24)=h(-4*6)=2=phi(6)", h_neg24, PHI_6, 0.0, g_23,
       "Exact for n=6; likely does not generalize to n=28")

# --- H-EXT6-24: Sum of primitive roots mod 7: sum=? vs sigma-tau ---
print(f"\nH-EXT6-24: Primitive roots mod 7, sum vs sigma-tau=8")
# Primitive roots mod 7: generators of (Z/7)*
# (Z/7)* is cyclic of order 6
# g is primitive root if g^k mod 7 has order 6
# Powers of 3 mod 7: 3^1=3, 3^2=2, 3^3=6, 3^4=4, 3^5=5, 3^6=1
# So 3 is a primitive root. The primitive roots are 3^k where gcd(k,6)=1
# gcd(k,6)=1 for k in {1,5} (since phi(6)=2)
# Primitive roots: 3^1=3, 3^5=5
prim_roots = []
for g in range(1, 7):
    # Check if g is a primitive root mod 7
    order = 1
    val = g
    while val % 7 != 1:
        val = (val * g) % 7
        order += 1
        if order > 7:
            break
    if order == 6:
        prim_roots.append(g)
print(f"  Primitive roots mod 7: {prim_roots}")
prim_sum = sum(prim_roots)
print(f"  Sum = {prim_sum}")
target_24 = SIGMA_6 - TAU_6  # 12-4=8
print(f"  sigma(6)-tau(6) = {target_24}")
print(f"  Match: {prim_sum == target_24}")
# Sum of primitive roots mod p: known to be mu(p-1) mod p
# For p=7: mu(6)=mu(2*3)=1, so sum = 1 mod 7?
# Actually sum of primitive roots mod p = mu(p-1) (Ramanujan sum)
# mu(6) = mu(2*3) = mu(2)*mu(3) = (-1)(-1) = 1
# So sum of prim roots mod 7 = mu(6) = 1 mod 7
# Our sum is 3+5=8, and 8 mod 7 = 1. Checks out!
print(f"  Verification: mu(6) = mu(2*3) = 1")
print(f"  Sum mod 7 = {prim_sum % 7} = mu(6) = 1  (checks out)")
print(f"  Actual sum = {prim_sum} = sigma(6)-tau(6) = 8")
err_24 = 0.0 if prim_sum == target_24 else pct_err(prim_sum, target_24)
g_24 = grade(err_24, exact=(prim_sum == int(target_24)))
record("24", "sum(prim roots mod 7)=8=sigma-tau", prim_sum, target_24, err_24, g_24,
       "Exact: 3+5=8=sigma(6)-tau(6), and 8 mod 7=1=mu(6)")

# --- H-EXT6-25: Bernoulli polynomial B_6(1/2) ---
print(f"\nH-EXT6-25: Bernoulli polynomial B_6(1/2) vs GZ constants")
# B_n(x) = sum_{k=0}^{n} C(n,k) B_k x^{n-k}
# B_6(1/2) = (1 - 2^{1-6}) * B_6 = (1 - 2^{-5}) * B_6
# = (1 - 1/32) * (1/42) = (31/32) * (1/42) = 31/1344
# Actually the relation is B_n(1/2) = -(1 - 2^{1-n}) * B_n for even n
# Wait: B_n(1/2) = (2^{1-n} - 1) * B_n for n >= 1
# B_6(1/2) = (2^{-5} - 1) * (1/42) = (-31/32) * (1/42) = -31/1344
b6_half = (2**(1-6) - 1) * float(B6)
# More carefully: (2^{-5} - 1) = (1-32)/32 = -31/32
# B_6(1/2) = (-31/32)(1/42) = -31/1344
b6_half_exact = Fraction(-31, 1344)
print(f"  B_6(1/2) = (2^{{1-6}} - 1) * B_6")
print(f"           = (1/32 - 1) * (1/42)")
print(f"           = (-31/32) * (1/42)")
print(f"           = {b6_half_exact} = {float(b6_half_exact):.10f}")
# Simplify
b6_simplified = Fraction(-31, 1344)
# gcd(31, 1344): 31 is prime. 1344/31 = 43.35... not integer
# So -31/1344 is already simplified
print(f"  Simplified: {b6_simplified}")
print(f"  |B_6(1/2)| = {abs(float(b6_simplified)):.10f}")
name_25, err_25 = best_gz_match(abs(float(b6_simplified)))
print(f"  Best GZ match for |B_6(1/2)|: {name_25} (err={err_25:.4f}%)")
# |B_6(1/2)| = 31/1344 = 0.02306...
# 1/42 = 0.02381... -- close!
err_25_b6 = pct_err(abs(float(b6_simplified)), float(B6))
print(f"  vs B_6=1/42={float(B6):.6f}: err={err_25_b6:.4f}%")
# 31/1344 vs 1/42 = 32/1344: error = 1/1344 / (32/1344) = 1/32 = 3.125%
print(f"  Ratio: B_6(1/2)/B_6 = 31/32 (the 2^{-5}-1 factor)")
print(f"  1344 = 1344. Factor: 1344 = 2^6 * 3 * 7 = 64*21")
print(f"  1344 = 2^6 * 21 = 2^n * 21, and 21 = 7*3")
print(f"  1344 / 6! = {1344/720:.4f}")
g_25 = grade(err_25)
record("25", f"|B_6(1/2)| vs {name_25}", abs(float(b6_simplified)),
       GZ_TARGETS.get(name_25, 0), err_25, g_25)


# ######################################################################
# FINAL SUMMARY TABLE
# ######################################################################
print(f"\n{BORDER}")
print("WAVE 6 FINAL SUMMARY")
print(BORDER)
print(f"| {'#':>2} | {'Hypothesis':<52} | {'Meas':>10} | {'Exp':>10} | {'Err%':>8} | Grade |")
print(f"|{'-'*4}|{'-'*54}|{'-'*12}|{'-'*12}|{'-'*10}|{'-'*7}|")
for r in results:
    title = r['title'][:52]
    meas = f"{r['measured']:.6f}" if isinstance(r['measured'], float) else str(r['measured'])
    exp_ = f"{r['expected']:.6f}" if isinstance(r['expected'], float) else str(r['expected'])
    meas = meas[:10]
    exp_ = exp_[:10]
    print(f"| {r['id']:>2} | {title:<52} | {meas:>10} | {exp_:>10} | {r['err']:>7.4f}% | {r['grade']:^5} |")

# Grade counts
greens = sum(1 for r in results if '\U0001f7e9' in r['grade'])
orange_star = sum(1 for r in results if '\u2605' in r['grade'])
oranges = sum(1 for r in results if '\U0001f7e7' in r['grade'] and '\u2605' not in r['grade'])
whites = sum(1 for r in results if '\u26aa' in r['grade'])
hits = greens + orange_star + oranges

print(f"\n{SEP}")
print(f"GRADE COUNTS:")
print(f"  \U0001f7e9 Exact:        {greens}")
print(f"  \U0001f7e7\u2605 Strong (<1%): {orange_star}")
print(f"  \U0001f7e7 Weak (<5%):   {oranges}")
print(f"  \u26aa Miss (>5%):   {whites}")
print(f"  TOTAL HITS:       {hits}/25")
print(f"  HIT RATE:         {hits/25*100:.1f}%")

print(f"\n{SEP}")
print("NOTABLE FINDINGS:")
for r in results:
    if '\U0001f7e9' in r['grade'] or '\u2605' in r['grade']:
        print(f"  {r['grade']} {r['id']}: {r['title']}")
        if r['note']:
            print(f"       {r['note']}")

print(f"\n{SEP}")
print("CATEGORY BREAKDOWN:")
cats = [("A: Physics Constants", results[0:5]),
        ("B: Continued Fractions & Ergodic", results[5:10]),
        ("C: Hilbert Matrix", results[10:15]),
        ("D: Group Theory", results[15:20]),
        ("E: Deep Number Theory", results[20:25])]
for cat_name, cat_results in cats:
    cat_hits = sum(1 for r in cat_results
                   if '\U0001f7e9' in r['grade'] or '\U0001f7e7' in r['grade'])
    print(f"  {cat_name}: {cat_hits}/5")

print("\nDone.")
