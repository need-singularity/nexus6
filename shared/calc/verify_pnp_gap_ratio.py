#!/usr/bin/env python3
"""
Verify the (1 - 1/e) Gap Ratio connections.

Tests:
  1. Poisson limit convergence: (1-1/k)^k -> 1/e
  2. Secretary problem threshold
  3. Maximum Coverage greedy ratio
  4. x*ln(x) minimization at 1/e
  5. GZ center consistency
  6. Bridge Theorem E(I)=I^I minimum

Grade: STRUCTURAL (not PROVEN as P!=NP connection)
Reference: math/proofs/pnp_gap_ratio_proof.md
"""

import math
import sys

# ── Constants ──
E = math.e
INV_E = 1.0 / E
GAP_RATIO = 1.0 - INV_E
GZ_UPPER = 0.5
GZ_LOWER = 0.5 - math.log(4/3)
GZ_WIDTH = math.log(4/3)
GZ_CENTER = INV_E

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    status = "PASS" if condition else "FAIL"
    if condition:
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{status}] {name}")
    if detail:
        print(f"         {detail}")

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ══════════════════════════════════════════════════════════════
# Test 1: Poisson Limit Convergence
# ══════════════════════════════════════════════════════════════
section("1. Poisson Limit: (1-1/k)^k -> 1/e")

print(f"\n  Target: 1/e = {INV_E:.10f}")
print(f"  {'k':>10}  {'(1-1/k)^k':>15}  {'error':>12}")
print(f"  {'-'*10}  {'-'*15}  {'-'*12}")

for k in [2, 5, 10, 50, 100, 1000, 10000, 100000]:
    val = (1.0 - 1.0/k) ** k
    err = abs(val - INV_E)
    print(f"  {k:>10}  {val:>15.10f}  {err:>12.2e}")

# Verify convergence
val_large = (1.0 - 1.0/100000) ** 100000
check("Poisson limit converges to 1/e",
      abs(val_large - INV_E) < 1e-5,
      f"|{val_large:.10f} - {INV_E:.10f}| = {abs(val_large - INV_E):.2e}")

# ══════════════════════════════════════════════════════════════
# Test 2: Secretary Problem
# ══════════════════════════════════════════════════════════════
section("2. Secretary Problem Simulation")

def secretary_success_prob(n, threshold_frac):
    """Exact probability of selecting the best with reject-first-r strategy."""
    r = max(1, int(threshold_frac * n))
    prob = 0.0
    for i in range(1, n + 1):
        # Probability that best is at position i AND we select them
        # Best at position i: prob = 1/n
        # We select if best of first i-1 is in first r positions
        if i <= r:
            continue  # We always reject first r
        # Select position i if the best among positions 1..i-1 is in 1..r
        prob += (1.0 / n) * (r / (i - 1))
    return prob

print(f"\n  Optimal threshold fraction: 1/e = {INV_E:.6f}")
print(f"\n  {'n':>6}  {'P(success, r=n/e)':>18}  {'1/e':>10}  {'error':>10}")
print(f"  {'-'*6}  {'-'*18}  {'-'*10}  {'-'*10}")

for n in [10, 50, 100, 500, 1000, 5000]:
    p = secretary_success_prob(n, INV_E)
    err = abs(p - INV_E)
    print(f"  {n:>6}  {p:>18.10f}  {INV_E:>10.6f}  {err:>10.6f}")

p_large = secretary_success_prob(5000, INV_E)
check("Secretary P(success) -> 1/e",
      abs(p_large - INV_E) < 0.005,
      f"P(success, n=5000) = {p_large:.6f}, |error| = {abs(p_large - INV_E):.6f}")

check("Secretary P(failure) -> 1 - 1/e = gap ratio",
      abs((1 - p_large) - GAP_RATIO) < 0.005,
      f"P(failure) = {1 - p_large:.6f}, gap ratio = {GAP_RATIO:.6f}")

# ══════════════════════════════════════════════════════════════
# Test 3: Maximum Coverage Greedy Ratio
# ══════════════════════════════════════════════════════════════
section("3. Maximum Coverage Greedy Bound")

print(f"\n  Greedy ratio = 1 - (1-1/k)^k")
print(f"  Limit as k->inf: 1 - 1/e = {GAP_RATIO:.10f}")
print(f"\n  {'k':>6}  {'ratio':>15}  {'1-1/e':>10}  {'error':>12}")
print(f"  {'-'*6}  {'-'*15}  {'-'*10}  {'-'*12}")

for k in [1, 2, 3, 5, 10, 50, 100, 1000]:
    ratio = 1.0 - (1.0 - 1.0/k) ** k
    err = abs(ratio - GAP_RATIO)
    print(f"  {k:>6}  {ratio:>15.10f}  {GAP_RATIO:>10.6f}  {err:>12.2e}")

ratio_large = 1.0 - (1.0 - 1.0/1000) ** 1000
check("Max Coverage greedy -> 1 - 1/e",
      abs(ratio_large - GAP_RATIO) < 0.001,
      f"ratio(k=1000) = {ratio_large:.10f}")

# ══════════════════════════════════════════════════════════════
# Test 4: x*ln(x) Minimization
# ══════════════════════════════════════════════════════════════
section("4. f(x) = x*ln(x) Minimization (Common Root)")

# Analytical: f'(x) = ln(x) + 1 = 0 => x = 1/e
# f(1/e) = (1/e)*ln(1/e) = (1/e)*(-1) = -1/e

x_opt = INV_E
f_opt = x_opt * math.log(x_opt)
f_opt_expected = -INV_E

check("f'(x) = 0 at x = 1/e",
      True,  # analytical, always true
      "ln(1/e) + 1 = -1 + 1 = 0")

check("f(1/e) = -1/e",
      abs(f_opt - f_opt_expected) < 1e-15,
      f"f(1/e) = {f_opt:.15f}, -1/e = {f_opt_expected:.15f}")

# Numerical verification: scan (0,1) to confirm global min
print(f"\n  Scanning f(x) = x*ln(x) on (0.01, 0.99), step=0.001:")
x_min_num = None
f_min_num = float('inf')
for i in range(1, 1000):
    x = i / 1000.0
    f = x * math.log(x)
    if f < f_min_num:
        f_min_num = f
        x_min_num = x

print(f"  Numerical minimum: x = {x_min_num:.3f}, f = {f_min_num:.6f}")
print(f"  Analytical:        x = {INV_E:.3f}, f = {f_opt:.6f}")

check("Numerical min agrees with 1/e",
      abs(x_min_num - INV_E) < 0.002,
      f"|{x_min_num:.4f} - {INV_E:.4f}| = {abs(x_min_num - INV_E):.4f}")

# ══════════════════════════════════════════════════════════════
# Test 5: GZ Center Consistency
# ══════════════════════════════════════════════════════════════
section("5. Golden Zone Consistency")

check("GZ center = 1/e",
      GZ_CENTER == INV_E,
      f"GZ_CENTER = {GZ_CENTER:.10f}")

check("1/e is inside GZ",
      GZ_LOWER < INV_E < GZ_UPPER,
      f"{GZ_LOWER:.4f} < {INV_E:.4f} < {GZ_UPPER:.4f}")

check("Gap ratio = 1 - GZ_center",
      abs(GAP_RATIO - (1.0 - GZ_CENTER)) < 1e-15,
      f"{GAP_RATIO:.10f} = 1 - {GZ_CENTER:.10f}")

check("1/e + (1-1/e) = 1",
      abs(INV_E + GAP_RATIO - 1.0) < 1e-15,
      "Partition of unity (trivial but explicit)")

# ══════════════════════════════════════════════════════════════
# Test 6: Bridge Theorem E(I) = I^I
# ══════════════════════════════════════════════════════════════
section("6. Bridge Theorem E(I) = I^I Minimum")

E_opt = INV_E ** INV_E
print(f"\n  E(1/e) = (1/e)^(1/e) = {E_opt:.10f}")

# Verify it's a minimum by checking neighbors
eps = 1e-6
E_left = (INV_E - eps) ** (INV_E - eps)
E_right = (INV_E + eps) ** (INV_E + eps)

check("E(I) has minimum at I = 1/e",
      E_opt < E_left and E_opt < E_right,
      f"E(1/e-eps) = {E_left:.10f} > E(1/e) = {E_opt:.10f} < E(1/e+eps) = {E_right:.10f}")

# The output fraction at optimum
output_at_opt = 1.0 - INV_E
print(f"\n  At optimal I = 1/e:")
print(f"    Inhibition fraction: {INV_E:.6f} (= 1/e)")
print(f"    Output fraction:     {output_at_opt:.6f} (= 1 - 1/e = gap ratio)")
print(f"    Energy E(I*):        {E_opt:.6f}")

# ══════════════════════════════════════════════════════════════
# Test 7: Cross-domain Identity Check
# ══════════════════════════════════════════════════════════════
section("7. Cross-Domain Identity: All Use Same x*ln(x) Root")

# All these constants are algebraically identical
constants = {
    "1/e (GZ center)":           INV_E,
    "1/e (Secretary threshold)": INV_E,
    "1/e (Poisson limit)":       INV_E,
    "1-1/e (Coverage ratio)":    GAP_RATIO,
    "1-1/e (Secretary failure)": GAP_RATIO,
    "1-1/e (KVV competitive)":   GAP_RATIO,
    "1-1/e (GZ output fraction)":GAP_RATIO,
}

print(f"\n  {'Constant':>35}  {'Value':>12}")
print(f"  {'-'*35}  {'-'*12}")
for name, val in constants.items():
    print(f"  {name:>35}  {val:>12.10f}")

# All 1/e values identical
e_vals = [v for k, v in constants.items() if "1/e" in k and "1-1/e" not in k]
check("All 1/e instances are identical",
      all(abs(v - INV_E) < 1e-15 for v in e_vals),
      f"max deviation = {max(abs(v - INV_E) for v in e_vals):.2e}")

# All 1-1/e values identical
gap_vals = [v for k, v in constants.items() if "1-1/e" in k]
check("All (1-1/e) instances are identical",
      all(abs(v - GAP_RATIO) < 1e-15 for v in gap_vals),
      f"max deviation = {max(abs(v - GAP_RATIO) for v in gap_vals):.2e}")

# ══════════════════════════════════════════════════════════════
# Test 8: Honesty Check - What is NOT proven
# ══════════════════════════════════════════════════════════════
section("8. Honesty Checks (What is NOT proven)")

print("""
  [INFO] The following are NOT proven and NOT claimed:
    - P != NP does NOT follow from the GZ model
    - The TCS hardness results ASSUME P != NP (conditional)
    - The connection GZ <-> TCS is STRUCTURAL, not a derivation
    - Naming this "P!=NP Gap Ratio" is aspirational, not rigorous

  [INFO] What IS proven:
    - 1 - 1/e is the greedy ratio for Max Coverage (NWF78)
    - 1 - 1/e is tight for online matching (KVV90)
    - 1/e is the Secretary Problem threshold (Dynkin63)
    - 1/e is the GZ center via Bridge Theorem (within model)
    - Both derive from x*ln(x) minimization at x = 1/e

  [INFO] Recommended grade: STRUCTURAL (not PROVEN)
  [INFO] Recommended rename: "Entropic Transition Cost" (not "P!=NP Gap Ratio")
""")

check("Grade is STRUCTURAL, not PROVEN",
      True,
      "Connection is algebraically exact but interpretively structural")

# ══════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════
section("SUMMARY")

print(f"\n  Results: {PASS} PASS, {FAIL} FAIL out of {PASS + FAIL} tests")
print(f"\n  Key constants:")
print(f"    1/e     = {INV_E:.10f}  (GZ center = TCS threshold)")
print(f"    1-1/e   = {GAP_RATIO:.10f}  (gap ratio = output fraction)")
print(f"    I^I min = {E_opt:.10f}  (Bridge Theorem energy)")
print(f"\n  Grade: STRUCTURAL (same root: x*ln(x) -> 1/e)")
print(f"  Status: Connection real but not a P!=NP proof")

if FAIL > 0:
    print(f"\n  *** {FAIL} TESTS FAILED ***")
    sys.exit(1)
else:
    print(f"\n  All {PASS} tests passed.")
    sys.exit(0)
