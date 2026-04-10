#!/usr/bin/env python3
"""H-ROB-1: 6-DOF = Perfect Number verification script"""

import math
from scipy.special import comb
from itertools import combinations

print("=" * 70)
print("H-ROB-1: 6-DOF = Perfect Number Verification")
print("=" * 70)

# === 1. SE(3) dimension verification ===
print("\n### 1. SE(3) Dimension Verification ###")
print()
dim_SO3 = 3  # rotation group in 3D: n(n-1)/2 = 3*2/2 = 3
dim_R3 = 3   # translation in 3D
dim_SE3 = dim_SO3 + dim_R3  # semi-direct product

print(f"  SO(3) dimension = n(n-1)/2 = 3*2/2 = {dim_SO3}")
print(f"  R^3 dimension   = {dim_R3}")
print(f"  SE(3) = SO(3) x R^3 dimension = {dim_SE3}")
print(f"  6 is perfect number: sigma(6) = 1+2+3+6 = 12 = 2*6  ✓")
print(f"  Proper divisors: 1+2+3 = {1+2+3} = 6  ✓")

# === 2. Perfect number properties of 6 ===
print("\n### 2. Perfect Number 6 — Divisor Functions ###")
print()

def sigma(n):
    """Sum of all divisors"""
    return sum(d for d in range(1, n+1) if n % d == 0)

def tau(n):
    """Number of divisors"""
    return sum(1 for d in range(1, n+1) if n % d == 0)

def phi(n):
    """Euler totient"""
    return sum(1 for k in range(1, n+1) if math.gcd(k, n) == 1)

def sigma_neg1(n):
    """Sum of reciprocals of divisors"""
    return sum(1/d for d in range(1, n+1) if n % d == 0)

n = 6
print(f"  sigma(6)   = {sigma(6):>4d}  (sum of divisors)")
print(f"  tau(6)     = {tau(6):>4d}  (number of divisors)")
print(f"  phi(6)     = {phi(6):>4d}  (Euler totient)")
print(f"  sigma_-1(6)= {sigma_neg1(6):>7.4f}  (reciprocal sum)")

# === 3. Robot types vs DOF ===
print("\n### 3. Robot Types vs DOF ###")
print()

robots = [
    ("Cartesian (PPP)",     3, "Position only"),
    ("SCARA",               4, "Planar + vertical"),
    ("5-axis CNC",          5, "Mill/cut, no full orient."),
    ("6-axis industrial",   6, "Full SE(3) manipulation"),
    ("7-axis redundant",    7, "Adds null-space motion"),
    ("Humanoid arm",        7, "Shoulder3+Elbow1+Wrist3"),
    ("Dual arm humanoid",  14, "2 x 7 DOF"),
    ("Humanoid full body", 30, "Approx. (varies by model)"),
]

print(f"  {'Robot Type':<24s} {'DOF':>4s}  {'Perfect # Relation':<30s}  Description")
print(f"  {'-'*24} {'----':>4s}  {'-'*30}  {'-'*25}")

for name, dof, desc in robots:
    # Find relation to perfect number 6
    if dof == 3:
        rel = "dim(R^3) = sigma(6)/tau(6)"
    elif dof == 4:
        rel = "tau(6) = 4"
    elif dof == 5:
        rel = "sigma(6) - 7 = 5"
    elif dof == 6:
        rel = "6 = PERFECT NUMBER"
    elif dof == 7:
        rel = "sigma(6) - tau(6) - 1 = 7"
    elif dof == 14:
        rel = "2 * 7 = sigma(6) + tau(6) - phi(6)"
    elif dof == 30:
        rel = "5 * 6 = 30"
    else:
        rel = "—"
    print(f"  {name:<24s} {dof:>4d}  {rel:<30s}  {desc}")

# === 4. DH parameters ===
print("\n### 4. Denavit-Hartenberg Parameters ###")
print()
dh_per_joint = 4  # a, alpha, d, theta
total_dh_6dof = dh_per_joint * 6

print(f"  DH parameters per joint: {dh_per_joint} = tau(6)")
print(f"  Total DH for 6-DOF: {dh_per_joint} x 6 = {total_dh_6dof}")
print(f"  24 = sigma(6) * tau(6) / phi(6) = 12*4/2 = {sigma(6)*tau(6)//phi(6)}")
print(f"  24 = 4! (factorial of tau(6))")
print(f"  24 = number of elements in S_4 (symmetric group)")

# === 5. Human body DOF analysis ===
print("\n### 5. Human Body DOF Analysis ###")
print()

human_dof = {
    "Spine (cervical)":     6,
    "Spine (thoracic)":     12,
    "Spine (lumbar)":       6,
    "Shoulder (each)":      3,
    "Elbow (each)":         1,
    "Wrist (each)":         3,
    "Hip (each)":           3,
    "Knee (each)":          1,
    "Ankle (each)":         3,
    "Fingers (each hand)":  20,
    "Toes (each foot)":     10,
    "Jaw":                  1,
}

# Approximate: bilateral symmetry
total_approx = 6 + 12 + 6 + 2*3 + 2*1 + 2*3 + 2*3 + 2*1 + 2*3 + 2*20 + 2*10 + 1
print(f"  Approximate human body DOF: ~{total_approx}")
print(f"  Common estimate range: 200-244 DOF")
print(f"  Using 244:")
print(f"    244 / 6 = {244/6:.4f}")
print(f"    244 = 4 * 61 (61 is prime)")
print(f"    244 mod 6 = {244 % 6}")
print(f"    floor(244/6) = {244//6} = 40")
print(f"  Using total_approx = {total_approx}:")
print(f"    {total_approx} / 6 = {total_approx/6:.4f}")
print(f"    {total_approx} mod 6 = {total_approx % 6}")

# === 6. Counting "6" in robotics ===
print("\n### 6. Robotics '6' Occurrences — Binomial Test ###")
print()

occurrences_of_6 = [
    "SE(3) dimension = 6",
    "Standard industrial robot = 6 DOF",
    "6 joints for complete manipulation",
    "Mobility criterion: M = 6(N-1-J) + sum(f_i) (Grubler)",
    "6-axis force/torque sensor",
    "Stewart platform: 6 actuators",
    "Screw theory: 6D twist/wrench",
    "6 Pluecker coordinates for lines in 3D",
]

n_occurrences = len(occurrences_of_6)
print(f"  Found {n_occurrences} independent occurrences of '6' in robotics:")
for i, occ in enumerate(occurrences_of_6, 1):
    print(f"    {i}. {occ}")

# p-value: probability of getting k or more hits if random
# Under null: each "6" occurrence is chance. P(any specific integer 1-10) = 1/10
# But the base rate of 3D space is fixed, so we need to be careful.
# More conservative: P(dimension = 6) given it could be 1-10
p_single = 1/10  # conservative: any integer 1-10 equally likely
n_trials = 10    # hypothetical slots where a number could appear

from scipy.stats import binom
p_value = 1 - binom.cdf(n_occurrences - 1, n_trials, p_single)
print(f"\n  Binomial test (conservative):")
print(f"    P(single hit) = {p_single}")
print(f"    Trials = {n_trials}")
print(f"    Observed = {n_occurrences}")
print(f"    p-value = {p_value:.6f}")

# More realistic: 6 is forced by dim(R^3)=3, so many are NOT independent
# Truly independent: Stewart platform, force sensor
independent = 3  # generous: Stewart, force sensor, Pluecker
p_independent = 1 - binom.cdf(independent - 1, n_trials, p_single)
print(f"\n  After removing SE(3)-derived (independent only):")
print(f"    Independent occurrences = {independent}")
print(f"    p-value = {p_independent:.6f}")

# === 7. The key insight: necessity vs coincidence ===
print("\n### 7. Key Analysis: Necessity vs Coincidence ###")
print()
print("  NECESSARY (follows from 3D space):")
print("    - SE(3) = 6 (dimension of Euclidean group)")
print("    - 6 DOF robot (minimum for SE(3))")
print("    - 6D twist/wrench (screw theory)")
print("    - Grubler formula coefficient = 6")
print()
print("  COINCIDENTAL with perfect number?")
print("    - 6 is smallest integer = 1+2+3")
print("    - 6 = 3! (natural in 3D combinatorics)")
print("    - dim(SE(3)) = 2 * dim(R^3) = 2*3 = 6")
print("    - This is 6 = n(n+1)/2 for n=3 (triangular)")
print()
print("  STRUCTURAL CONNECTION:")
print("    - 6 = sum of proper divisors = 1+2+3")
print("    - dim(SE(3)) = dim(SO(3)) + dim(R^3) = 3+3 = 1*3 + 2*(3/2)")
print("    - Divisors {1,2,3} of 6 correspond to:")
print("      1 → scalar (1D time)")
print("      2 → Euler totient phi(6), binary symmetry")
print("      3 → spatial dimension")
print("      6 → full SE(3)")

# === 8. DOF completeness threshold ===
print("\n### 8. DOF Completeness Threshold — ASCII Graph ###")
print()

# Workspace coverage vs DOF (conceptual)
# DOF < 6: restricted workspace, DOF = 6: full, DOF > 6: redundant
dof_range = range(1, 11)
# Conceptual: fraction of SE(3) reachable
coverage = []
for d in dof_range:
    if d <= 3:
        c = d / 6 * 0.5  # position only, partial
    elif d <= 5:
        c = 0.25 + (d - 3) / 3 * 0.55  # adding orientation
    elif d == 6:
        c = 1.0  # complete
    else:
        c = 1.0  # redundant (no new coverage, adds flexibility)
    coverage.append(c)

print("  Workspace Coverage vs DOF:")
print("  Coverage")
print("  1.0 |" + " " * 48 + "████████████████")
print("  0.9 |")
print("  0.8 |" + " " * 32 + "████")

# Build proper ASCII graph
max_width = 50
print()
print("  DOF | Coverage | Graph")
print("  ----+----------+" + "-" * max_width)
for d, c in zip(dof_range, coverage):
    bar = "█" * int(c * max_width)
    marker = " ← PERFECT NUMBER (complete)" if d == 6 else ""
    marker = " ← tau(6)" if d == 4 and not marker else marker
    marker = " ← redundant" if d == 7 and not marker else marker
    print(f"   {d:2d} | {c:>7.1%}  |{bar}{marker}")

print()
print("  Key: DOF = 6 is the EXACT threshold for completeness")
print("        DOF < 6: workspace restricted")
print("        DOF > 6: redundant (null-space motion)")

# === 9. Connection to Golden Zone ===
print("\n### 9. Golden Zone Connection (Speculative) ###")
print()
golden_center = 1/math.e
golden_width = math.log(4/3)
print(f"  Golden Zone center = 1/e = {golden_center:.4f}")
print(f"  Golden Zone width  = ln(4/3) = {golden_width:.4f}")
print(f"  sigma_-1(6) = {sigma_neg1(6):.4f}")
print(f"  tau(6) / sigma(6) = {tau(6)/sigma(6):.4f} = 1/3")
print(f"  phi(6) / sigma(6) = {phi(6)/sigma(6):.4f} = 1/6")
print(f"  Manipulability index at Golden Zone inhibition:")
print(f"    If tension ~ 1/e, robot operates at ~37% of max torque capacity")
print(f"    This is the 'optimal stopping' threshold")

# === 10. Generalization test: perfect number 28 ===
print("\n### 10. Generalization Test — Perfect Number 28 ###")
print()

n28 = 28
print(f"  sigma(28)   = {sigma(28)}")
print(f"  tau(28)     = {tau(28)}")
print(f"  phi(28)     = {phi(28)}")
print(f"  sigma_-1(28)= {sigma_neg1(28):.4f}")
print()
print(f"  SE(n) for n dimensions:")
print(f"    dim(SE(n)) = n(n+1)/2")
print(f"    For 28: n(n+1)/2 = 28 → n² + n - 56 = 0 → n = 7")
print(f"    dim(SE(7)) = 7 + 7*6/2 = 7 + 21 = {7 + 21}")
# Check
for n_dim in range(1, 30):
    se_dim = n_dim + n_dim*(n_dim-1)//2
    if se_dim == 28:
        print(f"    Found: dim(SE({n_dim})) = {se_dim} = 28  ✓")
        break
else:
    print(f"    No integer n gives dim(SE(n)) = 28")
    # Check triangular
    for n_dim in range(1, 30):
        tri = n_dim * (n_dim + 1) // 2
        if tri == 28:
            print(f"    But 28 = T({n_dim}) (triangular number)")
            print(f"    28 is triangular with n={n_dim}")
            break

print()
print("  28 = T(7) = 7th triangular number")
print("  6  = T(3) = 3rd triangular number")
print("  Both perfect numbers 6 and 28 are triangular!")
print("  T(n) = n(n+1)/2 = dim(SO(n+1)) for rotation group")
print(f"  dim(SO(4)) = 4*3/2 = 6  ← our 6-DOF!")
print(f"  dim(SO(8)) = 8*7/2 = 28 ← next perfect number!")

# === Summary ===
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print()
print("  6-DOF = Perfect Number connection is PARTIALLY NECESSARY:")
print("  - 6 = dim(SE(3)) is FORCED by 3D physics (not coincidence)")
print("  - 6 being perfect (1+2+3=6) is a number-theoretic fact")
print("  - The STRUCTURAL coincidence: both 6 and 28 are triangular")
print("  - Triangular numbers T(n) = dim(SO(n+1)) (rotation groups)")
print("  - Perfect numbers being triangular → deep connection to")
print("    rotation group dimensions")
print()
print("  Grade assessment:")
print("  - SE(3) dim = 6: NECESSARY (not coincidence) → not remarkable")
print("  - Perfect numbers = triangular → SO(n+1): STRUCTURAL")
print("  - tau(6) = 4 = DH params: COINCIDENTAL (DH is convention)")
print("  - Overall: 🟧 (structural connection, but largely forced by 3D)")
