#!/usr/bin/env python3
"""N6 Constants — Single Source of Truth for all n=6 derived constants.

Central hub for mathematical constants derived from perfect number 6.
All repos import from here. No hardcoding elsewhere.

Usage:
    import sys; sys.path.insert(0, '.shared')
    from n6_constants import *

    # Or specific imports:
    from n6_constants import SIGMA, TAU, PHI, DOMAINS, ISLANDS, TARGETS
"""

import math
from fractions import Fraction

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False


# ═════════════════════════════════════════════════════════════════
# BASE ARITHMETIC — n=6 number-theoretic functions
# ═════════════════════════════════════════════════════════════════

N = 6                    # first perfect number
SIGMA = 12               # sigma(6) = 1+2+3+6
TAU = 4                  # tau(6) = |{1,2,3,6}|
PHI = 2                  # phi(6) = |{1,5}|
SIGMA_INV = 2            # sigma_{-1}(6) = 1/1+1/2+1/3+1/6
SOPFR = 5                # sum of prime factors: 2+3
RADICAL = 6              # rad(6) = 2*3
MOBIUS_MU = 1            # mu(6) = (-1)^2 (squarefree, 2 primes)
CARMICHAEL_LAMBDA = 2    # lambda(6) = lcm(1,2)
DEDEKIND_PSI = 12        # psi(6) = 6*(3/2)*(4/3)
JORDAN_J2 = 24           # J_2(6) = 36*(3/4)*(8/9)
LEECH_DIM = SIGMA * PHI  # 12*2 = 24
DIVISOR_RECIPROCALS = [1/2, 1/3, 1/6]  # sum=1, probability distribution
H_TARGET = sum(-p * math.log(p) for p in DIVISOR_RECIPROCALS)  # Shannon entropy

# Second perfect number (n=28)
SIGMA_28 = 56
TAU_28 = 6
PHI_28 = 12


# ═════════════════════════════════════════════════════════════════
# GOLDEN ZONE — edge of chaos constants
# ═════════════════════════════════════════════════════════════════

GZ_UPPER = 0.5                    # 1/2 — Riemann critical line
GZ_CENTER = 1.0 / math.e         # 1/e ~ 0.3679
GZ_WIDTH = math.log(4/3)         # ln(4/3) ~ 0.2877
GZ_LOWER = 0.5 - math.log(4/3)   # ~ 0.2123


# ═════════════════════════════════════════════════════════════════
# ATLAS DERIVED — from sigma*phi = n*tau theorem
# ═════════════════════════════════════════════════════════════════

FFN_RATIO = Fraction(TAU**2, SIGMA)           # 4/3
MoE_TOP_K = PHI                                # 2
EGYPTIAN = (Fraction(1,2), Fraction(1,3), Fraction(1,6))  # sum=1

# Powers of 2 from n=6 differences
BYTE = 2 ** (SIGMA - TAU)          # 2^8 = 256
AES_BITS = 2 ** (SIGMA - SOPFR)    # 2^7 = 128
RSA_BITS = 2 ** (SIGMA - MOBIUS_MU) # 2^11 = 2048
CHACHA_ROUNDS = JORDAN_J2 - TAU     # 24-4 = 20

# Standard Model structure
SM_QUARKS = 6
SM_LEPTONS = 6
SM_GAUGE_BOSONS = TAU               # 4
SM_HIGGS = MOBIUS_MU                 # 1
SM_TOTAL = SM_QUARKS + SM_LEPTONS + SM_GAUGE_BOSONS + SM_HIGGS  # 17
SM_GAUGE_GENERATORS = SIGMA          # 8+3+1 = 12


# ═════════════════════════════════════════════════════════════════
# THERMODYNAMIC / PHYSICAL PREDICTIONS
# ═════════════════════════════════════════════════════════════════

R_BALANCE = Fraction(SIGMA * PHI, N * TAU)  # = 1 (unique at n=6)
MERTENS_DROPOUT = math.log(4/3)              # ~ 0.288
BOLTZMANN_SPARSITY = 1.0 / math.e            # ~ 0.368
MP_ME_RATIO = N * math.pi ** 5               # ~ 1836.118 (0.002% error)
HUBBLE_H0 = SIGMA * N + MOBIUS_MU            # = 73 (SH0ES: 73.04)
WEINBERG_ANGLE = Fraction(3, SIGMA + MOBIUS_MU)  # 3/13 ~ 0.2308


# ═════════════════════════════════════════════════════════════════
# CONSCIOUSNESS BRIDGE CONSTANTS
# ═════════════════════════════════════════════════════════════════

META_FIXED_POINT = Fraction(1, 3)   # contraction mapping convergence
PNP_GAP_RATIO = 1 - 1/math.e       # transition cost
COMPASS_UPPER = Fraction(5, 6)      # incompleteness 1/6
AMPLIFICATION_17 = 17               # Fermat prime (theta=pi)
RATE_SMALL_N = Fraction(7, 8)       # (n+1)/(tau*phi)
RATE_LARGE_N = Fraction(2, 5)       # phi/sopfr
RATE_PRODUCT = Fraction(7, 20)      # r0*r_inf invariant (Law 82)


# ═════════════════════════════════════════════════════════════════
# DFS ENGINE — Island classification for constant combination search
# ═════════════════════════════════════════════════════════════════

def _build_islands():
    """Island constants for DFS/convergence search (requires numpy)."""
    if not _HAS_NUMPY:
        return {}
    return {
        'A': {  # Rational/fractions (greens)
            '1/2':   0.5,
            '1/3':   1/3,
            '1/6':   1/6,
            '5/6':   5/6,
            '2/3':   2/3,
        },
        'B': {  # Integer/structural (stars)
            'I*':    GZ_LOWER,
            'sigma': float(SIGMA),
            'tau':   float(TAU),
            'eH':    2**(2/3) * 3**(1/2),  # Hardy-Ramanujan
            '17':    17.0,
            '137':   137.0,
            '8':     8.0,
            '6':     float(N),
        },
        'C': {  # Log/Entropy (blues)
            'ln(4/3)': np.log(4/3),
            'ln2':     np.log(2),
            'ln3':     np.log(3),
            'ln17':    np.log(17),
            'ln137':   np.log(137),
        },
        'D': {  # Transcendental
            'e':     np.e,
            '1/e':   1/np.e,
            'pi':    np.pi,
            'phi':   (1 + np.sqrt(5)) / 2,
        },
    }


def _build_targets():
    """Target constants for discovery matching (requires numpy)."""
    if not _HAS_NUMPY:
        return {}

    targets = {}

    # Mathematical constants
    _math = {
        'pi':         np.pi,
        'pi/2':       np.pi / 2,
        'pi/4':       np.pi / 4,
        'pi/6':       np.pi / 6,
        'pi^2/6':     np.pi**2 / 6,
        'e':          np.e,
        '1/e':        1 / np.e,
        'e^2':        np.e**2,
        'phi':        (1 + np.sqrt(5)) / 2,
        'sqrt(2)':    np.sqrt(2),
        'sqrt(3)':    np.sqrt(3),
        'sqrt(5)':    np.sqrt(5),
        'ln2':        np.log(2),
        'ln3':        np.log(3),
        'ln10':       np.log(10),
        'gamma_EM':   0.5772156649,
        'zeta(3)':    1.2020569031,
        'Catalan_G':  0.9159655941,
        'Khinchin':   2.6854520011,
    }
    for i in range(1, 21):
        _math[str(i)] = float(i)
    for a in range(1, 13):
        for b in range(a + 1, 13):
            key = f'{a}/{b}'
            if key not in _math:
                _math[key] = a / b

    # Physical constants
    _phys = {
        '1/alpha':     137.036,
        'alpha':       1/137.036,
        'alpha_s':     0.118,
        'sin2_thetaW': 0.231,
        'T_CMB':       2.72548,
        'Omega_DE':    0.683,
        'Omega_DM':    0.268,
        'Omega_b':     0.049,
    }

    targets.update(_math)
    targets.update(_phys)
    return targets


def _build_domains():
    """8-domain constant pool for convergence engine (requires numpy)."""
    if not _HAS_NUMPY:
        return {}
    return {
        "N": {
            "name": "Number Theory",
            "constants": {
                "sigma(6)":    float(SIGMA),
                "tau(6)":      float(TAU),
                "phi(6)":      float(PHI),
                "s(6)":        float(N),
                "sopfr(6)":    float(SOPFR),
                "mu(6)":       float(MOBIUS_MU),
                "sigma_-1(6)": float(SIGMA_INV),
                "6":           float(N),
                "28":          28.0,
                "496":         496.0,
                "sigma(28)":   float(SIGMA_28),
                "tau(28)":     float(TAU_28),
                "phi(28)":     float(PHI_28),
                "1/2":         0.5,
                "1/3":         1/3,
                "1/6":         1/6,
                "5/6":         5/6,
            },
        },
        "A": {
            "name": "Analysis",
            "constants": {
                "e":          np.e,
                "1/e":        1/np.e,
                "pi":         np.pi,
                "pi/2":       np.pi/2,
                "pi/6":       np.pi/6,
                "gamma_EM":   0.5772156649,
                "zeta(3)":    1.2020569031,
                "pi^2/6":     np.pi**2/6,
                "ln(2)":      np.log(2),
                "ln(3)":      np.log(3),
                "ln(4/3)":    np.log(4/3),
                "sqrt(2)":    np.sqrt(2),
                "sqrt(3)":    np.sqrt(3),
                "phi_gold":   (1+np.sqrt(5))/2,
            },
        },
        "G": {
            "name": "Algebra/Groups",
            "constants": {
                "dim_SU2":    3.0,
                "dim_SU3":    8.0,
                "dim_SU5":    24.0,
                "dim_SO10":   45.0,
                "dim_E6":     78.0,
                "dim_E7":     133.0,
                "dim_E8":     248.0,
                "rank_E8":    8.0,
                "Out_S6":     2.0,
            },
        },
        "T": {
            "name": "Topology/Geometry",
            "constants": {
                "kissing_3":   12.0,
                "kissing_4":   24.0,
                "kissing_8":   240.0,
                "kissing_24":  196560.0,
                "chi_S2":      2.0,
                "d_bosonic":   26.0,
                "d_super":     10.0,
                "d_M":         11.0,
            },
        },
        "C": {
            "name": "Combinatorics",
            "constants": {
                "F(6)":              8.0,
                "F(7)":              13.0,
                "C(6,3)":            20.0,
                "Catalan_3":         5.0,
                "Bell_3":            5.0,
                "T(6)":              21.0,
                "4/3":               4/3,
                "Feigenbaum_delta":  4.66920160910299,
                "Feigenbaum_alpha":  2.50290787509589,
            },
        },
        "Q": {
            "name": "Quantum Mechanics",
            "constants": {
                "1/alpha":      137.035999084,
                "alpha":        1/137.035999084,
                "alpha_s":      0.1185,
                "sin2_thetaW":  0.23122,
                "g_e-2":        0.00231930436256,
                "m_e/m_p":      1/1836.15267343,
                "m_e/m_mu":     1/206.7682830,
                "N_gen":        3.0,
                "CMB":          2.7255,
                "17":           17.0,
            },
        },
        "I": {
            "name": "Quantum Information",
            "constants": {
                "ln2_info":  np.log(2),
                "log2_e":    np.log2(np.e),
                "S_qubit":   np.log(2),
                "S_qutrit":  np.log(3),
                "2ln2":      2*np.log(2),
            },
        },
        "S": {
            "name": "Statistical Mechanics",
            "constants": {
                "lambda_c":   0.2700,
                "Onsager_Tc": 2/np.log(1+np.sqrt(2)),
                "nu_3D":      0.6301,
                "beta_3D":    0.3265,
                "gamma_3D":   1.2372,
                "delta_3D":   4.789,
            },
        },
    }


def _build_known_values():
    """Known discovery values for convergence engine novelty scoring."""
    if not _HAS_NUMPY:
        return {}
    return {
        "GZ_upper":    0.5,
        "GZ_center":   1/np.e,
        "GZ_lower":    0.5 - np.log(4/3),
        "GZ_width":    np.log(4/3),
        "meta_fp":     1/3,
        "compass":     5/6,
        "H_target":    H_TARGET,
        "ln2":         np.log(2),
        "1/e":         1/np.e,
    }


# Lazy-build on first access
ISLANDS = _build_islands()
TARGETS = _build_targets()
DOMAINS = _build_domains()
KNOWN_VALUES = _build_known_values()


# ═════════════════════════════════════════════════════════════════
# CONVENIENCE — all base constants as a dict
# ═════════════════════════════════════════════════════════════════

BASE_CONSTANTS = {
    'n': N, 'sigma': SIGMA, 'tau': TAU, 'phi': PHI,
    'sopfr': SOPFR, 'radical': RADICAL, 'mu': MOBIUS_MU,
    'lambda': CARMICHAEL_LAMBDA, 'psi': DEDEKIND_PSI,
    'J2': JORDAN_J2, 'sigma_inv': SIGMA_INV,
}

GZ_CONSTANTS = {
    'upper': GZ_UPPER, 'center': GZ_CENTER,
    'width': GZ_WIDTH, 'lower': GZ_LOWER,
}


if __name__ == '__main__':
    print("N6 Constants — Single Source of Truth")
    print(f"  Base: n={N}, σ={SIGMA}, τ={TAU}, φ={PHI}, sopfr={SOPFR}")
    print(f"  GZ: [{GZ_LOWER:.4f}, {GZ_UPPER}], center={GZ_CENTER:.4f}, width={GZ_WIDTH:.4f}")
    print(f"  R(6) = σφ/(nτ) = {SIGMA*PHI}/{N*TAU} = {SIGMA*PHI/(N*TAU)}")
    print(f"  Islands: {len(ISLANDS)} groups, {sum(len(v) for v in ISLANDS.values())} constants")
    print(f"  Targets: {len(TARGETS)} matching targets")
    print(f"  Domains: {len(DOMAINS)} domains, {sum(len(d['constants']) for d in DOMAINS.values())} constants")
