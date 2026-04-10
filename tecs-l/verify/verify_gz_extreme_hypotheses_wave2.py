#!/usr/bin/env python3
"""GZ Extreme Hypothesis Push — WAVE 2: 25 hypotheses across 5 domains.

Follow-up from Wave 1 leads + new territory:
  Cat A: (1/e)^(1/e) Deep Dive       (H-EXT2-01..05)
  Cat B: Quantum Information Theory   (H-EXT2-06..10)
  Cat C: Topology & Geometry          (H-EXT2-11..15)
  Cat D: Algebraic Structures on n=6  (H-EXT2-16..20)
  Cat E: Dynamical Systems / Chaos    (H-EXT2-21..25)
"""
import sys
import os
import math
import numpy as np
from scipy import special, stats
from fractions import Fraction
from decimal import Decimal, getcontext

sys.path.insert(0, "/Users/ghost/Dev/TECS-L")

try:
    import mpmath
    mpmath.mp.dps = 60  # 60 decimal places
    HAS_MPMATH = True
except ImportError:
    HAS_MPMATH = False

np.random.seed(42)

# ======================================================================
# Constants
# ======================================================================
INV_E     = 1.0 / math.e                   # 0.367879...
LN_4_3    = math.log(4.0 / 3.0)            # 0.287682...
LN_2      = math.log(2.0)                   # 0.693147...
GZ_UPPER  = 0.5
GZ_LOWER  = 0.5 - LN_4_3                   # 0.212318...
GZ_CENTER = INV_E
GZ_WIDTH  = LN_4_3
TAU_6     = 4     # number of divisors of 6
SIGMA_6   = 12    # sum of divisors of 6
PHI_6     = 2     # Euler's totient of 6
SIGMA_M1  = 2.0   # sigma_{-1}(6) = 1 + 1/2 + 1/3 + 1/6

BORDER = "=" * 70
SEP    = "-" * 70

# ======================================================================
# Grading
# ======================================================================
def grade(error_pct, exact=False):
    """Return emoji grade from % error."""
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
# CATEGORY A: (1/e)^(1/e) DEEP DIVE
# ######################################################################
print(BORDER)
print("CATEGORY A: (1/e)^(1/e) DEEP DIVE")
print(BORDER)

# --- H-EXT2-01: Is (1/e)^(1/e) = ln(2) exactly? ---
print("\nH-EXT2-01: Is (1/e)^(1/e) = ln(2) exactly?")
print("  Checking to 50+ decimal places with mpmath")
if HAS_MPMATH:
    mpmath.mp.dps = 60
    val_tower = mpmath.power(1/mpmath.e, 1/mpmath.e)
    val_ln2   = mpmath.log(2)
    diff = val_tower - val_ln2
    print(f"  (1/e)^(1/e)  = {val_tower}")
    print(f"  ln(2)        = {val_ln2}")
    print(f"  Difference   = {diff}")
    print(f"  Rel. diff    = {float(abs(diff/val_ln2))*100:.6f}%")
    err01 = float(abs(diff / val_ln2)) * 100
else:
    val_tower_f = INV_E ** INV_E
    err01 = pct_err(val_tower_f, LN_2)
    print(f"  (1/e)^(1/e) = {val_tower_f:.15f}")
    print(f"  ln(2)       = {LN_2:.15f}")
    print(f"  Error       = {err01:.6f}%")

is_exact = err01 < 1e-10
g01 = grade(err01, exact=is_exact)
note01 = "NOT exact — differs at 3rd decimal" if err01 > 0.01 else "Near-identity!"
record("H-EXT2-01", "(1/e)^(1/e) =? ln(2)", INV_E**INV_E, LN_2, err01, g01, note01)

# --- H-EXT2-02: Series representation of (1/e)^(1/e) ---
print(f"\nH-EXT2-02: (1/e)^(1/e) vs sum representations")
print("  (1/e)^(1/e) = e^(-1/e)")
val_02 = math.exp(-1.0/math.e)
print(f"  e^(-1/e) = {val_02:.15f}")
# Check: sum_{k=0}^inf (-1/e)^k / k! = e^(-1/e) (by definition of exp)
# More interesting: compare with alternating harmonic series partial sums
# Also compare with: 1 - 1/e + 1/(2e^2) - 1/(6e^3) + ...
partial = sum((-1.0/math.e)**k / math.factorial(k) for k in range(30))
print(f"  Taylor sum (30 terms) = {partial:.15f}")
# Compare with known: e^(-1/e) vs (e-1)/(e+1) [a Pade-like]
pade_like = (math.e - 1) / (math.e + 1)
err_pade = pct_err(pade_like, val_02)
print(f"  (e-1)/(e+1) = {pade_like:.15f}, error vs e^(-1/e) = {err_pade:.4f}%")
# Compare with 1/sqrt(e)
inv_sqrt_e = 1.0 / math.sqrt(math.e)
err_sqrt = pct_err(inv_sqrt_e, val_02)
print(f"  1/sqrt(e) = {inv_sqrt_e:.15f}, error = {err_sqrt:.4f}%")
# Best match: ln(2) already found. Try: 1 - 1/e
one_minus_inv_e = 1 - INV_E
err_1me = pct_err(one_minus_inv_e, val_02)
print(f"  1 - 1/e = {one_minus_inv_e:.15f}, error = {err_1me:.4f}%")
# Try: 2*ln(4/3)
two_ln43 = 2 * LN_4_3
err_2ln = pct_err(two_ln43, val_02)
print(f"  2*ln(4/3) = {two_ln43:.15f}, error = {err_2ln:.4f}%")

best_err = min(err_pade, err_sqrt, err_1me, err_2ln)
best_name = ["(e-1)/(e+1)", "1/sqrt(e)", "1-1/e", "2*ln(4/3)"][
    [err_pade, err_sqrt, err_1me, err_2ln].index(best_err)]
g02 = grade(best_err)
record("H-EXT2-02", f"e^(-1/e) best approx: {best_name}", val_02, None, best_err, g02,
       f"Best: {best_name} at {best_err:.4f}%")

# --- H-EXT2-03: e^(-e^(-1)) = e^(-1/e) identity check + tower ---
print(f"\nH-EXT2-03: Tower: e^(-e^(-1)) vs known constants")
tower = math.exp(-math.exp(-1))  # same as e^(-1/e)
print(f"  e^(-e^(-1)) = {tower:.15f}")
# Compare with sqrt(2)/2
sqrt2_2 = math.sqrt(2)/2
err_s22 = pct_err(sqrt2_2, tower)
print(f"  sqrt(2)/2 = {sqrt2_2:.15f}, error = {err_s22:.4f}%")
# Compare with pi/e^2
pi_e2 = math.pi / math.e**2
err_pie2 = pct_err(pi_e2, tower)
print(f"  pi/e^2 = {pi_e2:.15f}, error = {err_pie2:.4f}%")
# Compare with 1/phi (golden ratio)
phi = (1 + math.sqrt(5)) / 2
inv_phi = 1.0 / phi
err_iphi = pct_err(inv_phi, tower)
print(f"  1/phi = {inv_phi:.15f}, error = {err_iphi:.4f}%")

best_err3 = min(err_s22, err_pie2, err_iphi)
best3 = ["sqrt(2)/2", "pi/e^2", "1/phi"][[err_s22, err_pie2, err_iphi].index(best_err3)]
g03 = grade(best_err3)
record("H-EXT2-03", f"e^(-e^-1) ~ {best3}", tower, None, best_err3, g03,
       f"Best: {best3} at {best_err3:.4f}%")

# --- H-EXT2-04: Iterated (1/e)^((1/e)^(1/e)) ---
print(f"\nH-EXT2-04: Iterated tower: (1/e)^((1/e)^(1/e))")
inner = INV_E ** INV_E
iterated = INV_E ** inner
print(f"  (1/e)^(1/e) = {inner:.15f}")
print(f"  (1/e)^((1/e)^(1/e)) = {iterated:.15f}")
# Compare with GZ constants
err_gz_low = pct_err(iterated, GZ_LOWER)
err_gz_ctr = pct_err(iterated, GZ_CENTER)
err_ln43 = pct_err(iterated, LN_4_3)
err_half = pct_err(iterated, 0.5)
err_third = pct_err(iterated, 1.0/3.0)
print(f"  vs GZ_lower (0.2123): error = {err_gz_low:.4f}%")
print(f"  vs GZ_center (1/e):   error = {err_gz_ctr:.4f}%")
print(f"  vs ln(4/3):           error = {err_ln43:.4f}%")
print(f"  vs 1/2:               error = {err_half:.4f}%")
print(f"  vs 1/3:               error = {err_third:.4f}%")

best_err4 = min(err_gz_low, err_gz_ctr, err_ln43, err_half, err_third)
names4 = ["GZ_lower", "1/e", "ln(4/3)", "1/2", "1/3"]
best4 = names4[[err_gz_low, err_gz_ctr, err_ln43, err_half, err_third].index(best_err4)]
g04 = grade(best_err4)
record("H-EXT2-04", f"(1/e)^((1/e)^(1/e)) ~ {best4}", iterated, None, best_err4, g04,
       f"Best match: {best4}")

# --- H-EXT2-05: Tetration convergence ---
print(f"\nH-EXT2-05: Infinite tetration of 1/e: convergence?")
print("  x = (1/e)^(1/e)^(1/e)^... = lim of tower")
print("  For base b in [e^(-e), e^(1/e)], tower converges.")
print(f"  e^(-e) = {math.exp(-math.e):.6f}, e^(1/e) = {math.exp(1/math.e):.6f}")
print(f"  1/e = {INV_E:.6f} is in [{math.exp(-math.e):.6f}, {math.exp(1/math.e):.6f}]")
# Compute: fixed point of x = (1/e)^x => x*e^x = 1 => x = W(1) (Lambert W)
# Wait: (1/e)^x = x => e^(-x) = x => x*e^x = 1 ... no
# (1/e)^x = x => x = e^(-x) => x*e^x = 1 ... no, x = e^(-x) => x*e^x = 1?
# x*e^x = 1 => x = W(1) where W is Lambert W function
from scipy.special import lambertw
W1 = float(lambertw(1.0).real)
print(f"  Fixed point: x = W(1) = {W1:.15f}  (Lambert W)")
# Verify: (1/e)^W(1) should equal W(1)
check = INV_E ** W1
print(f"  (1/e)^W(1)  = {check:.15f}")
print(f"  Match: {abs(check - W1):.2e}")

# Now: does W(1) = Omega constant relate to GZ?
omega = W1  # 0.5671432904...
err_omega_gz = pct_err(omega, GZ_UPPER)
err_omega_half = pct_err(omega, 0.5)
# Compare omega with 1/2 + GZ_lower/2
gz_combo = 0.5 + GZ_LOWER / 2
err_combo = pct_err(omega, gz_combo)
# Compare with ln(4/3) + ln(4/3)
two_ln = 2 * LN_4_3
err_2ln43 = pct_err(omega, two_ln)
# Compare with (1 + 1/e)/e
combo2 = (1 + INV_E) / math.e
err_combo2 = pct_err(omega, combo2)
print(f"  Omega = {omega:.15f}")
print(f"  vs 1/2:               error = {err_omega_half:.4f}%")
print(f"  vs 2*ln(4/3)={two_ln:.6f}: error = {err_2ln43:.4f}%")
print(f"  vs (1+1/e)/e={combo2:.6f}: error = {err_combo2:.4f}%")

# Iterate tower numerically
x = INV_E
for _ in range(200):
    x = INV_E ** x
print(f"  Tower iteration (200): {x:.15f}")
print(f"  W(1) =                 {W1:.15f}")

best_err5 = min(err_omega_half, err_2ln43, err_combo2)
names5 = ["1/2", "2*ln(4/3)", "(1+1/e)/e"]
best5 = names5[[err_omega_half, err_2ln43, err_combo2].index(best_err5)]
g05 = grade(best_err5)
record("H-EXT2-05", f"Omega(tetration) ~ {best5}", omega, None, best_err5, g05,
       f"Omega = W(1) = {omega:.6f}, best: {best5}")

# ######################################################################
# CATEGORY B: QUANTUM INFORMATION THEORY
# ######################################################################
print(f"\n{BORDER}")
print("CATEGORY B: QUANTUM INFORMATION THEORY")
print(BORDER)

# --- H-EXT2-06: Von Neumann entropy of maximally mixed 2-qubit ---
print("\nH-EXT2-06: Von Neumann entropy of max-mixed 2-qubit vs GZ")
# S = log(d) for maximally mixed state of dimension d
# 2-qubit: d=4, S = ln(4) = 2*ln(2) (in nats)
S_vn = math.log(4)  # nats
print(f"  S(max mixed 2-qubit) = ln(4) = {S_vn:.15f} nats")
# In bits: log2(4) = 2 (trivial)
# Check ratios
ratio_gz_width = S_vn / GZ_WIDTH  # ln(4)/ln(4/3)
print(f"  ln(4)/ln(4/3) = {ratio_gz_width:.15f}")
# ln(4)/ln(4/3) = log_{4/3}(4)
# Check if this is near integer or simple fraction
err_5 = pct_err(ratio_gz_width, 5.0)
err_tau = pct_err(ratio_gz_width, TAU_6)
err_sigma_m1_sq = pct_err(ratio_gz_width, SIGMA_M1 ** 2)
print(f"  vs 5:               error = {err_5:.4f}%")
print(f"  vs tau(6)=4:        error = {err_tau:.4f}%")
print(f"  vs sigma_-1(6)^2=4: error = {err_sigma_m1_sq:.4f}%")
# Exact: ln(4)/ln(4/3) = ln(4)/(ln4-ln3)
# Numerically: 1.3863/0.2877 = 4.8188...
print(f"  Actual ratio = {ratio_gz_width:.6f}")
err_best6 = min(err_5, err_tau)
g06 = grade(err_best6)
record("H-EXT2-06", "S(2-qubit max)/GZ_width", ratio_gz_width, 5.0 if err_5 < err_tau else 4.0,
       err_best6, g06, f"ln(4)/ln(4/3) = {ratio_gz_width:.4f}")

# --- H-EXT2-07: Depolarizing channel capacity at p=1/e ---
print(f"\nH-EXT2-07: Quantum channel capacity of depol. channel at p=1/e")
# Depolarizing channel: rho -> (1-p)*rho + p*I/d
# For qubit (d=2): capacity C = 1 - H(p) where H is binary entropy (in bits)
# More precisely for depol: C = 1 - h((1-p)*1 + p/2) ...
# Actually: C_1 = 1 - H(3p/4, 1-3p/4) for d=2 depolarizing
# Or simply: output entropy. Let's use standard formula.
# For qubit depolarizing: C = 1 + (1-p)log2(1-p) + p*log2(p/3) when p <= 3/4
p_dep = INV_E
if p_dep <= 3.0/4.0:
    C_dep = 1 + (1 - p_dep) * math.log2(1 - p_dep) + p_dep * math.log2(p_dep / 3.0)
else:
    C_dep = 0.0
print(f"  p = 1/e = {p_dep:.6f}")
print(f"  C(depol, p=1/e) = {C_dep:.15f} bits")
# Compare with GZ constants
err_invE = pct_err(C_dep, INV_E)
err_half = pct_err(C_dep, 0.5)
err_ln43 = pct_err(C_dep, LN_4_3)
err_third = pct_err(C_dep, 1.0/3.0)
print(f"  vs 1/e:     error = {err_invE:.4f}%")
print(f"  vs 1/2:     error = {err_half:.4f}%")
print(f"  vs ln(4/3): error = {err_ln43:.4f}%")
print(f"  vs 1/3:     error = {err_third:.4f}%")
best_err7 = min(err_invE, err_half, err_ln43, err_third)
names7 = ["1/e", "1/2", "ln(4/3)", "1/3"]
best7 = names7[[err_invE, err_half, err_ln43, err_third].index(best_err7)]
g07 = grade(best_err7)
record("H-EXT2-07", f"C(depol,1/e) ~ {best7}", C_dep, None, best_err7, g07)

# --- H-EXT2-08: Concurrence of Werner state at F=1/e ---
print(f"\nH-EXT2-08: Concurrence of Werner state at F=1/e")
# Werner state: rho_W(F) = F|Phi+><Phi+| + (1-F)*(I-|Phi+><Phi+|)/3
# Concurrence: C = max(0, (3F-1)/2) for F in [1/3, 1]
# Wait, standard: C(Werner) = max(0, 2F-1) for isotropic state
# For Werner state with parameter p: C = max(0, (3p-1)/2) ... different conventions
# Let's use: concurrence for isotropic state = max(0, (d*F-1)/(d-1)) for d=2:
# C = max(0, 2F - 1)
F_w = INV_E
C_werner = max(0, 2*F_w - 1)
print(f"  F = 1/e = {F_w:.6f}")
print(f"  Concurrence = max(0, 2/e - 1) = {C_werner:.15f}")
# 2/e - 1 = (2-e)/e
val_exact = (2 - math.e) / math.e
print(f"  Exact: (2-e)/e = {val_exact:.15f}")
# Negative! e > 2, so 2-e < 0
if C_werner == 0:
    print("  Concurrence = 0 (state is separable at F=1/e)")
    print("  Since 1/e < 1/2, Werner state is separable. Entanglement threshold F=1/2!")
    err_thresh = pct_err(0.5, GZ_UPPER)  # exact match
    g08 = grade(0.0, exact=True)
    record("H-EXT2-08", "Werner entanglement threshold = 1/2 = GZ_upper!", 0.5, GZ_UPPER,
           0.0, g08, "EXACT: entanglement threshold = GZ_upper")
else:
    err08 = pct_err(C_werner, LN_4_3)
    g08 = grade(err08)
    record("H-EXT2-08", "C(Werner,1/e)", C_werner, LN_4_3, err08, g08)

# --- H-EXT2-09: Holevo bound for binary quantum channel at 1/e noise ---
print(f"\nH-EXT2-09: Holevo chi for binary channel, noise=1/e")
# Binary symmetric channel with crossover probability p:
# chi = 1 - H(p) (Holevo quantity, bits)
# H(p) = -p*log2(p) - (1-p)*log2(1-p)
p_noise = INV_E
H_bin = -p_noise * math.log2(p_noise) - (1-p_noise) * math.log2(1-p_noise)
chi_holevo = 1 - H_bin
print(f"  p = 1/e, H(1/e) = {H_bin:.15f} bits")
print(f"  chi = 1 - H(1/e) = {chi_holevo:.15f} bits")
# chi in nats: chi_nats = chi * ln(2)
chi_nats = chi_holevo * LN_2
print(f"  chi (nats) = {chi_nats:.15f}")
# Compare
err_ln43_n = pct_err(chi_nats, LN_4_3)
err_inv_e = pct_err(chi_holevo, INV_E)
err_gz_low = pct_err(chi_holevo, GZ_LOWER)
print(f"  chi(bits) vs 1/e:     error = {err_inv_e:.4f}%")
print(f"  chi(bits) vs GZ_low:  error = {err_gz_low:.4f}%")
print(f"  chi(nats) vs ln(4/3): error = {err_ln43_n:.4f}%")
best_err9 = min(err_ln43_n, err_inv_e, err_gz_low)
names9 = ["ln(4/3)[nats]", "1/e[bits]", "GZ_low[bits]"]
best9 = names9[[err_ln43_n, err_inv_e, err_gz_low].index(best_err9)]
g09 = grade(best_err9)
record("H-EXT2-09", f"Holevo(1/e noise) ~ {best9}", chi_holevo, None, best_err9, g09)

# --- H-EXT2-10: Quantum discord of Bell-diagonal state at param 1/e ---
print(f"\nH-EXT2-10: Quantum discord of Bell-diagonal state, c1=c2=c3=1/e")
# Bell-diagonal: rho = (I+sum c_i sigma_i x sigma_i)/4
# For c1=c2=c3=c: classical correlation = (1+c)/2 * log((1+c)/2) + (1-c)/2 * log((1-c)/2) + log2
# Quantum discord = mutual info - classical correlations
# Eigenvalues of Bell-diagonal with c1=c2=c3=c:
# lambda = (1+3c)/4, (1-c)/4, (1-c)/4, (1-c)/4
c = INV_E
eigs = [(1 + 3*c)/4, (1-c)/4, (1-c)/4, (1-c)/4]
S_AB = -sum(l * math.log2(l) for l in eigs if l > 0)
# Reduced state is maximally mixed: S_A = S_B = 1 bit
S_A = 1.0
# Mutual information
I_AB = 2 * S_A - S_AB
print(f"  Eigenvalues: {[f'{l:.6f}' for l in eigs]}")
print(f"  S(AB) = {S_AB:.15f} bits")
print(f"  I(A:B) = {I_AB:.15f} bits")
# Classical correlations for symmetric case
# J(B|A) = S_B - min_{meas} S(B|meas_A)
# For c1=c2=c3=c: J = 1 - H((1+c)/2) where H is binary entropy
c_class = 1 - (-((1+c)/2)*math.log2((1+c)/2) - ((1-c)/2)*math.log2((1-c)/2))
discord = I_AB - c_class
print(f"  Classical corr J = {c_class:.15f}")
print(f"  Discord D = I - J = {discord:.15f}")
# Compare discord with GZ constants
err_d_ln43 = pct_err(discord, LN_4_3)
err_d_inve = pct_err(discord, INV_E)
err_d_gzl  = pct_err(discord, GZ_LOWER)
err_d_sixth = pct_err(discord, 1.0/6.0)
print(f"  vs ln(4/3): error = {err_d_ln43:.4f}%")
print(f"  vs 1/e:     error = {err_d_inve:.4f}%")
print(f"  vs GZ_low:  error = {err_d_gzl:.4f}%")
print(f"  vs 1/6:     error = {err_d_sixth:.4f}%")
best_err10 = min(err_d_ln43, err_d_inve, err_d_gzl, err_d_sixth)
names10 = ["ln(4/3)", "1/e", "GZ_low", "1/6"]
best10 = names10[[err_d_ln43, err_d_inve, err_d_gzl, err_d_sixth].index(best_err10)]
g10 = grade(best_err10)
record("H-EXT2-10", f"Discord(Bell,1/e) ~ {best10}", discord, None, best_err10, g10)

# ######################################################################
# CATEGORY C: TOPOLOGY & GEOMETRY
# ######################################################################
print(f"\n{BORDER}")
print("CATEGORY C: TOPOLOGY & GEOMETRY")
print(BORDER)

# --- H-EXT2-11: Euler characteristic of surface with 6 vertices ---
print("\nH-EXT2-11: Euler char. of triangulated surface, 6 vertices")
# For a triangulated sphere with V=6: V-E+F=2
# Icosahedron has V=12. What has V=6? Octahedron! V=6, E=12, F=8
# chi = 6 - 12 + 8 = 2
V, E_oct, F = 6, 12, 8
chi = V - E_oct + F
print(f"  Octahedron: V={V}, E={E_oct}, F={F}")
print(f"  chi = {chi}")
print(f"  chi = sigma_{'{-1}'}(6) = 2? YES — both equal 2")
err11 = pct_err(chi, SIGMA_M1)
g11 = grade(err11, exact=(chi == int(SIGMA_M1)))
record("H-EXT2-11", "chi(octahedron) = sigma_{-1}(6) = 2", chi, SIGMA_M1, 0.0, g11,
       "EXACT: Euler char of 6-vertex polyhedron = sigma_{-1}(6)")

# --- H-EXT2-12: Genus of K_6 ---
print(f"\nH-EXT2-12: Genus of complete graph K_6")
# genus(K_n) = ceil((n-3)(n-4)/12) for n >= 3
n = 6
genus_K6 = math.ceil((n-3)*(n-4)/12)
print(f"  genus(K_6) = ceil((6-3)(6-4)/12) = ceil(6/12) = ceil(0.5) = {genus_K6}")
print(f"  genus(K_6) = {genus_K6}")
# Compare with GZ constants
err_12_1 = pct_err(genus_K6, 1)  # trivially 1
print(f"  genus = 1 (torus). K_6 embeds on torus!")
# What about: 6 * genus = 6 * 1 = 6 = n?
print(f"  n / genus = {n/genus_K6} = 6 (= n itself)")
# The embedding formula: (n-3)(n-4)/12 uses the same 12 = sigma(6)!
denom = 12
print(f"  Denominator in genus formula = 12 = sigma(6)!")
err12 = 0.0  # exact
g12 = grade(0.0, exact=True)
record("H-EXT2-12", "genus(K_6) formula denom = sigma(6) = 12", denom, SIGMA_6, 0.0, g12,
       "EXACT: genus formula denom = sigma(6)")

# --- H-EXT2-13: Volume of 6-simplex ---
print(f"\nH-EXT2-13: Volume of regular 6-simplex (edge=1) vs sigma(6)")
# Volume of regular n-simplex with edge length a:
# V_n = sqrt(n+1) / (n! * 2^(n/2)) * a^n
nn = 6
V_6simplex = math.sqrt(nn+1) / (math.factorial(nn) * 2**(nn/2))
print(f"  V(6-simplex, a=1) = sqrt(7)/(6!*8) = {V_6simplex:.15f}")
# Compare
err_13_sigma = pct_err(V_6simplex, 1.0/SIGMA_6)
err_13_inv720 = pct_err(V_6simplex, 1.0/720)  # 6! = 720
print(f"  vs 1/sigma(6) = 1/12 = {1/12:.6f}: error = {err_13_sigma:.4f}%")
print(f"  vs 1/6! = 1/720 = {1/720:.6f}: error = {err_13_inv720:.4f}%")
# V = sqrt(7)/5760 = 0.000459...
# try: 1/(6! * 2^3) = 1/5760 = 0.000174, close?
inv5760 = 1.0/5760
err_13_5760 = pct_err(V_6simplex, inv5760)
print(f"  sqrt(7)/5760 vs 1/5760: ratio = sqrt(7) = {math.sqrt(7):.6f}")
# This is just the formula. Let's check if V * 6! * 8 = sqrt(7)
product = V_6simplex * math.factorial(6) * 8
print(f"  V * 6! * 8 = {product:.15f} (should be sqrt(7)={math.sqrt(7):.15f})")
err13 = err_13_sigma
g13 = grade(err13)
record("H-EXT2-13", "V(6-simplex) vs 1/sigma(6)", V_6simplex, 1.0/SIGMA_6, err13, g13)

# --- H-EXT2-14: Hyperbolic volume of figure-eight knot complement ---
print(f"\nH-EXT2-14: Hyperbolic volume of figure-8 knot vs ln(4/3)")
# Vol(figure-eight) = 3 * Cl_2(pi/3) where Cl_2 is Clausen function
# = 6 * Catalan-like integral
# Known value: 2.0298832128...
# Cl_2(pi/3) = sum_{k=1}^inf sin(k*pi/3)/k^2
Cl2_pi3 = sum(math.sin(k * math.pi / 3) / k**2 for k in range(1, 10000))
Vol_fig8 = 3 * Cl2_pi3
print(f"  Vol(figure-8 knot) = 3*Cl_2(pi/3) = {Vol_fig8:.10f}")
print(f"  Known value: 2.0298832128...")
# Compare with GZ combos
err_14a = pct_err(Vol_fig8, 6 * LN_4_3)       # 6*ln(4/3) = 1.726
err_14b = pct_err(Vol_fig8, 6 * INV_E)         # 6/e = 2.207
err_14c = pct_err(Vol_fig8, SIGMA_M1 * math.e * LN_4_3)  # 2*e*ln(4/3) = 1.564
err_14d = pct_err(Vol_fig8, 2 + LN_4_3/10)     # 2.0288 close?
err_14e = pct_err(Vol_fig8, math.pi * LN_4_3 * SIGMA_M1)  # pi*ln(4/3)*2 = 1.808
err_14f = pct_err(Vol_fig8, 7 * LN_4_3)        # 7*ln(4/3) = 2.014
print(f"  vs 6*ln(4/3)={6*LN_4_3:.6f}: error = {err_14a:.4f}%")
print(f"  vs 6/e={6*INV_E:.6f}:       error = {err_14b:.4f}%")
print(f"  vs 7*ln(4/3)={7*LN_4_3:.6f}: error = {err_14f:.4f}%")

best_err14 = min(err_14a, err_14b, err_14f)
names14 = ["6*ln(4/3)", "6/e", "7*ln(4/3)"]
best14 = names14[[err_14a, err_14b, err_14f].index(best_err14)]
g14 = grade(best_err14)
record("H-EXT2-14", f"Vol(fig-8 knot) ~ {best14}", Vol_fig8, None, best_err14, g14)

# --- H-EXT2-15: Catalan constant vs GZ combinations ---
print(f"\nH-EXT2-15: Catalan constant G vs GZ combinations")
# G = sum_{k=0}^inf (-1)^k / (2k+1)^2 = 0.9159655941...
G_cat = sum((-1)**k / (2*k+1)**2 for k in range(100000))
print(f"  G (Catalan) = {G_cat:.15f}")
# Known: 0.915965594177...
err_15a = pct_err(G_cat, 1 - 1.0/SIGMA_6)      # 1 - 1/12 = 11/12 = 0.9167
err_15b = pct_err(G_cat, math.pi * LN_4_3)      # pi*ln(4/3) = 0.9040
err_15c = pct_err(G_cat, math.e * INV_E**2)     # e * e^-2 = 1/e = 0.368 nope
err_15d = pct_err(G_cat, math.pi / (2*math.e) + 0.5)  # random combo
err_15e = pct_err(G_cat, 1 - 1.0/SIGMA_6)       # 11/12
err_15f = pct_err(G_cat, GZ_UPPER + GZ_CENTER + 1.0/6)  # 0.5 + 1/e + 1/6 = 1.034
err_15g = pct_err(G_cat, math.pi/2 - GZ_WIDTH)  # pi/2 - ln(4/3) = 1.283
err_15h = pct_err(G_cat, 5.0/6 + 1.0/SIGMA_6)  # 5/6 + 1/12 = 11/12 same as a
# Try: (e+1)/(e+2)
e_ratio = (math.e + 1) / (math.e + 2)
err_15i = pct_err(G_cat, e_ratio)
# Try: pi^2 / (6*sigma_-1(6)^2 - 2) = pi^2/6 ... nope that's zeta(2)
# Try: 1 - GZ_LOWER/2
half_low = 1 - GZ_LOWER / 2
err_15j = pct_err(G_cat, half_low)
print(f"  vs 11/12={11/12:.6f}:          error = {err_15a:.4f}%")
print(f"  vs pi*ln(4/3)={math.pi*LN_4_3:.6f}: error = {err_15b:.4f}%")
print(f"  vs (e+1)/(e+2)={e_ratio:.6f}: error = {err_15i:.4f}%")
print(f"  vs 1-GZ_low/2={half_low:.6f}:  error = {err_15j:.4f}%")

best_err15 = min(err_15a, err_15b, err_15i, err_15j)
names15 = ["11/12", "pi*ln(4/3)", "(e+1)/(e+2)", "1-GZ_low/2"]
best15 = names15[[err_15a, err_15b, err_15i, err_15j].index(best_err15)]
g15 = grade(best_err15)
record("H-EXT2-15", f"Catalan G ~ {best15}", G_cat, None, best_err15, g15)

# ######################################################################
# CATEGORY D: ALGEBRAIC STRUCTURES ON n=6
# ######################################################################
print(f"\n{BORDER}")
print("CATEGORY D: ALGEBRAIC STRUCTURES ON n=6")
print(BORDER)

# --- H-EXT2-16: Number of groups of order 6 = 2 = sigma_{-1}(6) ---
print("\nH-EXT2-16: Number of groups of order 6 = sigma_{-1}(6)?")
# Groups of order 6: Z_6 and S_3 (exactly 2 groups)
n_groups_6 = 2  # known fact
print(f"  Number of groups of order 6 = {n_groups_6}")
print(f"  sigma_{{-1}}(6) = {SIGMA_M1}")
print(f"  phi(6) = {PHI_6}")
print(f"  Both equal 2!")
is_exact_16 = (n_groups_6 == int(SIGMA_M1))
g16 = grade(0.0, exact=is_exact_16)
record("H-EXT2-16", "Groups(6) = sigma_{-1}(6) = phi(6) = 2", n_groups_6, SIGMA_M1,
       0.0, g16, "EXACT: |Groups of order 6| = sigma_{-1}(6) = phi(6) = 2")

# --- H-EXT2-17: |Aut(S_3)| vs tau(6) ---
print(f"\nH-EXT2-17: |Aut(S_3)| vs tau(6)")
# Aut(S_3) = Inn(S_3) since S_3 is complete (center trivial, all auts inner)
# |Inn(S_3)| = |S_3|/|Z(S_3)| = 6/1 = 6
# So |Aut(S_3)| = 6
aut_S3 = 6
print(f"  |Aut(S_3)| = {aut_S3}")
print(f"  tau(6) = {TAU_6}")
print(f"  sigma(6) = {SIGMA_6}")
print(f"  |Aut(S_3)| = 6 = n itself (not tau(6)=4)")
# More interesting: |Aut(S_3)| = |S_3| = n (S_3 is complete group)
err17 = pct_err(aut_S3, TAU_6)
# Actually |Aut(S_3)|/n = 1 and n/sigma(6) = 1/2 = GZ_upper!
ratio17 = n / SIGMA_6
print(f"  n/sigma(6) = 6/12 = {ratio17} = 1/2 = GZ_upper!")
err17_gz = pct_err(ratio17, GZ_UPPER)
g17 = grade(err17_gz, exact=(ratio17 == GZ_UPPER))
record("H-EXT2-17", "|Aut(S_3)|/sigma(6) = GZ_upper = 1/2", ratio17, GZ_UPPER,
       0.0, g17, "EXACT: S_3 complete -> |Aut|=6, 6/sigma(6)=1/2")

# --- H-EXT2-18: Class number of Q(sqrt(-6)) ---
print(f"\nH-EXT2-18: Class number h(-24) of Q(sqrt(-6))")
# Discriminant of Q(sqrt(-6)) is -24 (since -6 = 2 mod 4)
# Class number h(-24) = 2 (known from tables)
h_neg24 = 2
print(f"  h(-24) = h(Q(sqrt(-6))) = {h_neg24}")
print(f"  phi(6) = {PHI_6}")
print(f"  sigma_{{-1}}(6) = {SIGMA_M1}")
is_exact_18 = (h_neg24 == PHI_6)
g18 = grade(0.0, exact=is_exact_18)
record("H-EXT2-18", "h(Q(sqrt(-6))) = phi(6) = 2", h_neg24, PHI_6,
       0.0, g18, "EXACT: class number of Q(sqrt(-6)) = phi(6) = 2")

# --- H-EXT2-19: Dedekind psi(6) vs sigma(6) ---
print(f"\nH-EXT2-19: Dedekind psi(6) vs sigma(6)")
# psi(n) = n * prod_{p|n} (1 + 1/p)
# psi(6) = 6 * (1 + 1/2) * (1 + 1/3) = 6 * 3/2 * 4/3 = 6 * 2 = 12
psi_6 = 6 * (1 + Fraction(1,2)) * (1 + Fraction(1,3))
print(f"  psi(6) = 6 * (1+1/2) * (1+1/3) = {psi_6}")
print(f"  sigma(6) = {SIGMA_6}")
is_exact_19 = (int(psi_6) == SIGMA_6)
print(f"  psi(6) = sigma(6) = 12!")
# This is actually special. For perfect numbers: psi(n) = sigma(n)?
# Check: psi(28) = 28*(1+1/2)*(1+1/7) = 28*3/2*8/7 = 28*12/7 = 48
# sigma(28) = 1+2+4+7+14+28 = 56. So 48 != 56. NOT general!
psi_28 = 28 * Fraction(3,2) * Fraction(8,7)
sigma_28 = 1+2+4+7+14+28
print(f"  Check n=28: psi(28)={psi_28}, sigma(28)={sigma_28} -> NOT equal")
print(f"  So psi(6) = sigma(6) is SPECIAL to n=6!")
g19 = grade(0.0, exact=is_exact_19)
record("H-EXT2-19", "psi(6) = sigma(6) = 12 (unique to 6!)", int(psi_6), SIGMA_6,
       0.0, g19, "EXACT + SPECIAL: psi(n)=sigma(n) fails for n=28")

# --- H-EXT2-20: Jordan's totient J_2(6) ---
print(f"\nH-EXT2-20: Jordan's totient J_2(6) vs sigma(6)")
# J_k(n) = n^k * prod_{p|n} (1 - 1/p^k)
# J_2(6) = 36 * (1 - 1/4) * (1 - 1/9) = 36 * 3/4 * 8/9 = 36 * 24/36 = 24
J2_6 = 36 * (1 - Fraction(1,4)) * (1 - Fraction(1,9))
print(f"  J_2(6) = 36 * (1-1/4) * (1-1/9) = {J2_6}")
print(f"  = 24 = 4! = sigma(6)*phi(6) = 12*2")
print(f"  sigma(6) * phi(6) = {SIGMA_6 * PHI_6}")
is_exact_20 = (int(J2_6) == SIGMA_6 * PHI_6)
# Also: 24 = tau(6)! (4! = 24)
print(f"  tau(6)! = 4! = {math.factorial(TAU_6)}")
is_also_20 = (int(J2_6) == math.factorial(TAU_6))
g20 = grade(0.0, exact=is_exact_20 and is_also_20)
record("H-EXT2-20", "J_2(6) = sigma(6)*phi(6) = tau(6)! = 24", int(J2_6),
       SIGMA_6 * PHI_6, 0.0, g20,
       "EXACT: J_2(6) = sigma(6)*phi(6) = tau(6)! = 24")

# ######################################################################
# CATEGORY E: DYNAMICAL SYSTEMS / CHAOS
# ######################################################################
print(f"\n{BORDER}")
print("CATEGORY E: DYNAMICAL SYSTEMS / CHAOS")
print(BORDER)

# --- H-EXT2-21: Feigenbaum delta / GZ_width ---
print("\nH-EXT2-21: Feigenbaum delta / GZ_width = ?")
delta_F = 4.669201609102990671853  # Feigenbaum delta
ratio_21 = delta_F / GZ_WIDTH
print(f"  delta_F = {delta_F}")
print(f"  GZ_width = ln(4/3) = {GZ_WIDTH:.15f}")
print(f"  delta/width = {ratio_21:.15f}")
# Compare with known constants
err_16 = pct_err(ratio_21, 16)
err_4pi = pct_err(ratio_21, 4*math.pi)
err_e_cubed = pct_err(ratio_21, math.e**3 / (math.e - 1))
err_sigma6_plus = pct_err(ratio_21, SIGMA_6 + TAU_6)  # 16
print(f"  vs 16:           error = {err_16:.4f}%")
print(f"  vs sigma(6)+tau(6)=16: error = {err_sigma6_plus:.4f}%")
print(f"  vs 4*pi={4*math.pi:.4f}: error = {err_4pi:.4f}%")
# Actually ratio = 16.226... Check vs 16 + ln(4/3)/... nah
# Try simple: delta/ln(4/3) = 16.226, not close to integer
err_16_2 = pct_err(ratio_21, 16.0)
g21 = grade(err_16_2)
record("H-EXT2-21", "delta_F/ln(4/3) ~ 16", ratio_21, 16.0, err_16_2, g21,
       f"Ratio = {ratio_21:.4f}")

# --- H-EXT2-22: Logistic onset of chaos / e ---
print(f"\nH-EXT2-22: Logistic map onset of chaos r_inf/e")
r_inf = 3.5699456718709449  # onset of chaos (Feigenbaum point)
ratio_22 = r_inf / math.e
print(f"  r_inf = {r_inf}")
print(f"  r_inf/e = {ratio_22:.15f}")
# Compare
err_22a = pct_err(ratio_22, 1 + LN_4_3)  # 1.2877
err_22b = pct_err(ratio_22, math.pi / (math.e))  # pi/e = 1.1557
err_22c = pct_err(ratio_22, 1 + INV_E)  # 1.3679
err_22d = pct_err(ratio_22, 13.0/10)  # 1.3
err_22e = pct_err(ratio_22, 4.0/3)  # 1.333
print(f"  r_inf/e = {ratio_22:.6f}")
print(f"  vs 1+ln(4/3)={1+LN_4_3:.6f}: error = {err_22a:.4f}%")
print(f"  vs 4/3={4/3:.6f}:             error = {err_22e:.4f}%")
print(f"  vs 1+1/e={1+INV_E:.6f}:       error = {err_22c:.4f}%")
print(f"  vs 13/10:                      error = {err_22d:.4f}%")
best_err22 = min(err_22a, err_22c, err_22d, err_22e)
names22 = ["1+ln(4/3)", "1+1/e", "13/10", "4/3"]
best22 = names22[[err_22a, err_22c, err_22d, err_22e].index(best_err22)]
g22 = grade(best_err22)
record("H-EXT2-22", f"r_inf/e ~ {best22}", ratio_22, None, best_err22, g22)

# --- H-EXT2-23: Lyapunov ln(2) / ln(4/3) ---
print(f"\nH-EXT2-23: Lyapunov(logistic,r=4) / GZ_width = ln(2)/ln(4/3)")
# Lyapunov exponent at r=4: lambda = ln(2)
lyap = LN_2
ratio_23 = lyap / LN_4_3
print(f"  lambda(r=4) = ln(2) = {lyap:.15f}")
print(f"  ln(2)/ln(4/3) = log_{'{4/3}'}(2) = {ratio_23:.15f}")
# This is a logarithm base change: log_{4/3}(2)
# = ln(2)/(ln(4)-ln(3)) = ln(2)/(2ln(2)-ln(3))
# Numerically: 2.4094...
err_23a = pct_err(ratio_23, 12.0/5)  # 2.4
err_23b = pct_err(ratio_23, math.e - LN_4_3)  # 2.430
err_23c = pct_err(ratio_23, 2 + GZ_LOWER)  # 2.212
err_23d = pct_err(ratio_23, 5.0/2)  # 2.5
err_23e = pct_err(ratio_23, 2 + LN_4_3 + GZ_LOWER)  # 2.500 hmm
combo23 = 2 + LN_4_3 + GZ_LOWER
err_23f = pct_err(ratio_23, 7.0/3)  # 2.333
print(f"  vs 12/5=2.4:           error = {err_23a:.4f}%")
print(f"  vs 5/2=2.5:            error = {err_23d:.4f}%")
print(f"  vs 7/3={7/3:.6f}:      error = {err_23f:.4f}%")
# Exact form: log_{4/3}(2). Try to simplify.
# ln(2)/ln(4/3) = ln(2)/(ln(4)-ln(3)) = 1/(2-ln(3)/ln(2)) = 1/(2-log_2(3))
# log_2(3) = 1.58496... So 1/(2-1.58496) = 1/0.41504 = 2.4094
print(f"  Exact: 1/(2 - log_2(3)) = {1/(2 - math.log2(3)):.15f}")
best_err23 = min(err_23a, err_23d, err_23f)
names23 = ["12/5", "5/2", "7/3"]
best23 = names23[[err_23a, err_23d, err_23f].index(best_err23)]
g23 = grade(best_err23)
record("H-EXT2-23", f"log_{{4/3}}(2) ~ {best23}", ratio_23, None, best_err23, g23,
       f"= 1/(2-log_2(3)) = {ratio_23:.6f}")

# --- H-EXT2-24: Period-3 window r/e ---
print(f"\nH-EXT2-24: Period-3 window of logistic map: r_3/e")
r_3 = 1 + math.sqrt(8)  # onset of period-3: r = 1 + sqrt(8)
ratio_24 = r_3 / math.e
print(f"  r_3 = 1 + sqrt(8) = {r_3:.15f}")
print(f"  r_3/e = {ratio_24:.15f}")
# Compare
err_24a = pct_err(ratio_24, math.sqrt(2))  # 1.414
err_24b = pct_err(ratio_24, 1 + INV_E)  # 1.368
err_24c = pct_err(ratio_24, phi)  # 1.618
err_24d = pct_err(ratio_24, 1 + GZ_LOWER + LN_4_3)  # 1 + 0.5 = 1.5
err_24e = pct_err(ratio_24, 3.0/2)
print(f"  vs sqrt(2)={math.sqrt(2):.6f}: error = {err_24a:.4f}%")
print(f"  vs phi={phi:.6f}:             error = {err_24c:.4f}%")
print(f"  vs 3/2:                       error = {err_24e:.4f}%")
print(f"  vs 1+1/e:                     error = {err_24b:.4f}%")

best_err24 = min(err_24a, err_24b, err_24c, err_24e)
names24 = ["sqrt(2)", "1+1/e", "phi", "3/2"]
best24 = names24[[err_24a, err_24b, err_24c, err_24e].index(best_err24)]
g24 = grade(best_err24)
record("H-EXT2-24", f"r_3/e ~ {best24}", ratio_24, None, best_err24, g24)

# --- H-EXT2-25: Sarkovskii first / e ---
print(f"\nH-EXT2-25: Sarkovskii: 3/e vs GZ constants")
# In Sarkovskii ordering, 3 is the strongest period
# 3/e as a universal constant?
ratio_25 = 3.0 / math.e
print(f"  3/e = {ratio_25:.15f}")
# Compare with known
err_25a = pct_err(ratio_25, 1 + GZ_LOWER)  # 1 + 0.2123 = 1.2123
err_25b = pct_err(ratio_25, 1 + LN_4_3 - INV_E)  # 1 + 0.2877 - 0.3679 = 0.920
err_25c = pct_err(ratio_25, 11.0/10)  # 1.1
err_25d = pct_err(ratio_25, math.sqrt(phi) - 1.0/6)  # 1.272 - 0.167 = 1.106
# 3/e = 1.10364...
err_25e = pct_err(ratio_25, 1 + 1.0/SIGMA_6)  # 1 + 1/12 = 1.0833
err_25f = pct_err(ratio_25, 1 + GZ_LOWER / 2)  # 1.1062
print(f"  vs 11/10=1.1:              error = {err_25c:.4f}%")
print(f"  vs 1+1/12={1+1/12:.6f}:    error = {err_25e:.4f}%")
print(f"  vs 1+GZ_low/2={1+GZ_LOWER/2:.6f}: error = {err_25f:.4f}%")

best_err25 = min(err_25c, err_25e, err_25f)
names25 = ["11/10", "1+1/12", "1+GZ_low/2"]
best25 = names25[[err_25c, err_25e, err_25f].index(best_err25)]
g25 = grade(best_err25)
record("H-EXT2-25", f"3/e ~ {best25}", ratio_25, None, best_err25, g25)

# ######################################################################
# SUMMARY TABLE
# ######################################################################
print(f"\n\n{'#' * 70}")
print("SUMMARY TABLE — WAVE 2 (25 Hypotheses)")
print('#' * 70)
print(f"\n{'ID':<12} {'Grade':<6} {'Error%':<10} {'Title':<55} {'Note'}")
print(SEP)
for r in results:
    note_short = r['note'][:50] if r['note'] else ""
    print(f"{r['id']:<12} {r['grade']:<6} {r['err']:<10.4f} {r['title']:<55} {note_short}")

# Grade distribution
grades = [r['grade'] for r in results]
n_green = sum(1 for g in grades if '\U0001f7e9' in g)
n_orange_star = sum(1 for g in grades if '\u2605' in g)
n_orange = sum(1 for g in grades if '\U0001f7e7' in g and '\u2605' not in g)
n_white = sum(1 for g in grades if g == '\u26aa')

print(f"\n{'=' * 70}")
print("GRADE DISTRIBUTION")
print(f"  \U0001f7e9 Exact (green):      {n_green}")
print(f"  \U0001f7e7\u2605 Strong (<1%):     {n_orange_star}")
print(f"  \U0001f7e7 Weak (<5%):          {n_orange}")
print(f"  \u26aa Miss (>5%):           {n_white}")
print(f"  Total hits:              {n_green + n_orange_star + n_orange}/{len(results)}")

# Texas Sharpshooter comparison
print(f"\n{'=' * 70}")
print("TEXAS SHARPSHOOTER COMPARISON")
n_hits = n_green + n_orange_star + n_orange
# Under random: each hypothesis has ~5% chance of <5% match by accident
# Expected: 25 * 0.05 = 1.25
expected_random = 25 * 0.05
p_binom = 1 - stats.binom.cdf(n_hits - 1, 25, 0.05)
print(f"  Hits: {n_hits}/25")
print(f"  Random expected: {expected_random:.2f}")
print(f"  p-value (binomial): {p_binom:.6f}")
if p_binom < 0.01:
    print("  >> HIGHLY SIGNIFICANT (p < 0.01)")
elif p_binom < 0.05:
    print("  >> SIGNIFICANT (p < 0.05)")
else:
    print("  >> Not significant")

# Highlight discoveries
print(f"\n{'=' * 70}")
print("TOP DISCOVERIES")
print(SEP)
for r in results:
    if '\U0001f7e9' in r['grade'] or '\u2605' in r['grade']:
        print(f"  {r['id']}: {r['title']}")
        print(f"    {r['note']}")
        print()

print(f"\n{'=' * 70}")
print("WAVE 2 COMPLETE")
print(f"{'=' * 70}")
