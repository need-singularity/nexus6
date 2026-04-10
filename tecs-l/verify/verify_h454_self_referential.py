#!/usr/bin/env python3
"""
H-CX-454: Self-Referential Algebra of Convergence Points
Verify claimed algebraic relations among 9 convergence points,
then run Texas Sharpshooter test against random constant sets.
"""

import numpy as np
from scipy import stats
import math

# === 1. Define the 9 convergence points ===
constants = {
    "1/2":       0.5,
    "1/3":       1/3,
    "1/e":       1/math.e,
    "ln(2)":     math.log(2),
    "ln(4/3)":   math.log(4/3),  # GZ_width
    "5/6":       5/6,
    "gamma":     0.5772156649015329,  # Euler-Mascheroni
    "sqrt(2)":   math.sqrt(2),
    "sqrt(3)":   math.sqrt(3),
}

# Additional constants needed for claims
zeta3 = 1.2020569031595942  # Apery's constant zeta(3)

print("=" * 70)
print("H-CX-454: Self-Referential Algebra of Convergence Points")
print("=" * 70)

# === 2. Verify each claimed relation ===
print("\n--- Claimed Relations: Exact Errors ---\n")

claims = [
    ("sqrt(3) * ln(2) ~ zeta(3)",
     math.sqrt(3) * math.log(2), zeta3),
    ("zeta(3) * ln(2) ~ 5/6",
     zeta3 * math.log(2), 5/6),
    ("zeta(3) * gamma ~ ln(2)",
     zeta3 * 0.5772156649015329, math.log(2)),
    ("5/6 * ln(2) ~ gamma",
     (5/6) * math.log(2), 0.5772156649015329),
    ("5/6 + gamma ~ sqrt(2)",
     5/6 + 0.5772156649015329, math.sqrt(2)),
    ("gamma * 1/2 ~ GZ_width (ln(4/3))",
     0.5772156649015329 * 0.5, math.log(4/3)),
    ("sqrt(3) / gamma ~ 3",
     math.sqrt(3) / 0.5772156649015329, 3.0),
]

print(f"{'Relation':<40} {'LHS':>12} {'RHS':>12} {'AbsErr':>10} {'RelErr%':>10}")
print("-" * 86)

real_match_count = 0
THRESHOLD = 0.05  # 5% relative error for claimed relations display

for label, lhs, rhs in claims:
    abs_err = abs(lhs - rhs)
    rel_err = abs_err / abs(rhs) * 100
    flag = "OK" if rel_err < 5.0 else "MISS"
    print(f"{label:<40} {lhs:>12.8f} {rhs:>12.8f} {abs_err:>10.6f} {rel_err:>9.4f}%  {flag}")

# === 3. Texas Sharpshooter Test ===
print("\n" + "=" * 70)
print("Texas Sharpshooter Test")
print("=" * 70)

# Use the 9 constants + zeta(3) as the real set (10 values)
real_values = list(constants.values()) + [zeta3]
real_names = list(constants.keys()) + ["zeta(3)"]

def count_pairwise_matches(values, threshold_pct=0.5):
    """
    For a set of values, try all pairwise {+, -, *, /} combinations.
    Count how many results match ANY value in the set within threshold_pct%.
    """
    n = len(values)
    matches = 0
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            a, b = values[i], values[j]
            results = [a + b, a - b, a * b]
            if b != 0:
                results.append(a / b)
            if a != 0:
                results.append(b / a)
            for r in results:
                if abs(r) < 1e-10:
                    continue
                for k in range(n):
                    if abs(values[k]) < 1e-10:
                        continue
                    rel = abs(r - values[k]) / abs(values[k]) * 100
                    if rel < threshold_pct:
                        matches += 1
    return matches

# Count real matches
MATCH_THRESHOLD = 0.5  # 0.5% relative error
real_matches = count_pairwise_matches(real_values, MATCH_THRESHOLD)
print(f"\nReal set ({len(real_values)} constants), threshold={MATCH_THRESHOLD}%:")
print(f"  Pairwise operation matches: {real_matches}")

# Show which ones match
print("\n  Matching relations found:")
n = len(real_values)
ops = {'+': lambda a,b: a+b, '-': lambda a,b: a-b,
       '*': lambda a,b: a*b, '/': lambda a,b: a/b if b!=0 else None}
shown = set()
for i in range(n):
    for j in range(n):
        if i == j:
            continue
        a, b = real_values[i], real_values[j]
        for op_name, op_fn in ops.items():
            r = op_fn(a, b)
            if r is None or abs(r) < 1e-10:
                continue
            for k in range(n):
                if abs(real_values[k]) < 1e-10:
                    continue
                rel = abs(r - real_values[k]) / abs(real_values[k]) * 100
                if rel < MATCH_THRESHOLD:
                    key = tuple(sorted([i,j,k,hash(op_name)]))
                    if key not in shown:
                        shown.add(key)
                        print(f"    {real_names[i]} {op_name} {real_names[j]} = {r:.8f}"
                              f"  ~  {real_names[k]} = {real_values[k]:.8f}"
                              f"  (err={rel:.4f}%)")

# Monte Carlo: random constant sets
print(f"\nMonte Carlo: 10000 random sets of {len(real_values)} constants in [0.1, 3.0]")
print("  Computing... ", end="", flush=True)

N_TRIALS = 10000
rng = np.random.default_rng(42)
random_matches = np.zeros(N_TRIALS, dtype=int)

for t in range(N_TRIALS):
    rand_vals = rng.uniform(0.1, 3.0, size=len(real_values)).tolist()
    random_matches[t] = count_pairwise_matches(rand_vals, MATCH_THRESHOLD)

print("done.")

mean_rand = np.mean(random_matches)
std_rand = np.std(random_matches)
z_score = (real_matches - mean_rand) / std_rand if std_rand > 0 else 0
p_value = 1 - stats.norm.cdf(z_score)

print(f"\n--- Results ---")
print(f"  Real matches:      {real_matches}")
print(f"  Random mean:       {mean_rand:.2f} +/- {std_rand:.2f}")
print(f"  Random median:     {np.median(random_matches):.0f}")
print(f"  Random max:        {np.max(random_matches)}")
print(f"  Z-score:           {z_score:.2f}")
print(f"  p-value:           {p_value:.6f}")

# Empirical p-value
emp_p = np.sum(random_matches >= real_matches) / N_TRIALS
print(f"  Empirical p-value: {emp_p:.6f}")

# Distribution histogram (ASCII)
print("\n--- Random Match Distribution (ASCII) ---")
bins = np.arange(0, max(np.max(random_matches), real_matches) + 3)
hist, bin_edges = np.histogram(random_matches, bins=bins)
max_bar = max(hist) if max(hist) > 0 else 1
for i in range(len(hist)):
    bar_len = int(hist[i] / max_bar * 50)
    marker = " <-- REAL" if int(bin_edges[i]) == real_matches else ""
    if hist[i] > 0 or marker:
        print(f"  {int(bin_edges[i]):3d} | {'#' * bar_len} ({hist[i]}){marker}")

if real_matches > np.max(random_matches):
    print(f"  {real_matches:3d} |  <-- REAL (beyond random range)")

# Verdict
print("\n--- Verdict ---")
if p_value < 0.01:
    grade = "Structural (p < 0.01)"
    emoji = "STRONG"
elif p_value < 0.05:
    grade = "Weak evidence (p < 0.05)"
    emoji = "WEAK"
else:
    grade = "Not significant (p >= 0.05)"
    emoji = "FAIL"

print(f"  Grade: {emoji} -- {grade}")
print(f"  Z={z_score:.2f}, p={p_value:.6f}, empirical_p={emp_p:.6f}")

# Check individual claim quality
good_claims = sum(1 for _, lhs, rhs in claims
                  if abs(lhs - rhs) / abs(rhs) * 100 < 5.0)
print(f"  Individual claims within 5%: {good_claims}/{len(claims)}")
bad_claims = sum(1 for _, lhs, rhs in claims
                 if abs(lhs - rhs) / abs(rhs) * 100 > 10.0)
if bad_claims > 0:
    print(f"  WARNING: {bad_claims} claims have >10% error (likely false)")

print("\n" + "=" * 70)
print("Verification complete.")
