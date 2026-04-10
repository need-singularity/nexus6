#!/usr/bin/env python3
"""
Verify H-CX-467 (Universal Saturation at Depth 3) and H-CX-471 (Null Baseline).

H-CX-467: ANY set of 6+ independent constants can reach all 9 fundamental targets at depth 3.
H-CX-471: Do RANDOM constants also saturate? (Null baseline test)

If random constants also reach 9/9, the claim is trivial (combinatorial explosion).
If random constants reach only 3-5/9, then structured constants are special.
"""

import math
import random
import time
import numpy as np
from itertools import combinations

# ============================================================
# 9 Fundamental Targets
# ============================================================
TARGETS = {
    'sqrt2':   math.sqrt(2),      # 1.41421356...
    'sqrt3':   math.sqrt(3),      # 1.73205081...
    '5/6':     5.0 / 6.0,         # 0.83333...
    'e':       math.e,             # 2.71828...
    'zeta3':   1.2020569,          # Apery's constant
    'ln4/3':   math.log(4.0/3.0), # 0.28768...
    'ln2':     math.log(2),        # 0.69315...
    'gamma':   0.5772156649,       # Euler-Mascheroni
    '1/2':     0.5,
}

TARGET_LIST = list(TARGETS.items())
TARGET_VALS = np.array([v for _, v in TARGET_LIST])
NUM_TARGETS = len(TARGET_LIST)

TOLERANCE = 0.001  # 0.1% relative tolerance

# ============================================================
# Operations
# ============================================================

def safe_val(x):
    """Check if value is finite and in a reasonable range."""
    if x is None or not math.isfinite(x):
        return False
    return 1e-6 < abs(x) < 1e6

def binary_ops(a, b):
    """Return list of results from binary operations on a, b."""
    results = []
    # +, -, *, /
    results.append(a + b)
    results.append(a - b)
    results.append(b - a)
    if abs(b) > 1e-10:
        results.append(a / b)
    if abs(a) > 1e-10:
        results.append(b / a)
    results.append(a * b)
    # Power (limited range to avoid overflow)
    if a > 0 and abs(b) < 20 and abs(b * math.log(a + 1e-30)) < 50:
        try:
            results.append(a ** b)
        except:
            pass
    if b > 0 and abs(a) < 20 and abs(a * math.log(b + 1e-30)) < 50:
        try:
            results.append(b ** a)
        except:
            pass
    # log_a(b) and log_b(a)
    if a > 0 and b > 0 and abs(math.log(a)) > 1e-10:
        try:
            results.append(math.log(b) / math.log(a))
        except:
            pass
    if a > 0 and b > 0 and abs(math.log(b)) > 1e-10:
        try:
            results.append(math.log(a) / math.log(b))
        except:
            pass
    return [r for r in results if safe_val(r)]

def unary_ops(a):
    """Return list of results from unary operations on a."""
    results = [a]
    if a > 0:
        results.append(math.sqrt(a))
        results.append(math.log(a))
    results.append(1.0 / a if abs(a) > 1e-10 else None)
    results.append(a ** 2)
    return [r for r in results if r is not None and safe_val(r)]

def compute_depth1(constants):
    """Compute all depth-1 values: unary(c) + binary(c1, c2)."""
    vals = set()
    # Unary on each constant
    for c in constants:
        for v in unary_ops(c):
            vals.add(v)
    # Binary on all pairs
    for i in range(len(constants)):
        for j in range(len(constants)):
            if i != j:
                for v in binary_ops(constants[i], constants[j]):
                    vals.add(v)
    return vals

def compute_depth2(constants, depth1_vals, max_level1=500):
    """Compute depth-2 values: binary(depth1, base) and binary(depth1, depth1)."""
    # Cap depth1 values
    d1_list = list(depth1_vals)
    if len(d1_list) > max_level1:
        d1_list = random.sample(d1_list, max_level1)

    vals = set(depth1_vals)

    # depth1 x base constants
    for v1 in d1_list:
        for c in constants:
            for v in binary_ops(v1, c):
                vals.add(v)

    # depth1 x depth1 (sample to keep tractable)
    d1_sample = d1_list[:200] if len(d1_list) > 200 else d1_list
    for i in range(len(d1_sample)):
        for j in range(i + 1, min(i + 50, len(d1_sample))):
            for v in binary_ops(d1_sample[i], d1_sample[j]):
                vals.add(v)

    return vals

def count_targets_reached(vals, tolerance=TOLERANCE):
    """Count how many of the 9 targets are reached within relative tolerance."""
    reached = set()
    for name, target in TARGET_LIST:
        for v in vals:
            if abs(v - target) / abs(target) < tolerance:
                reached.add(name)
                break
    return reached

def evaluate_constants(constants, label="", verbose=False):
    """Full evaluation: depth 1 and depth 2."""
    d1 = compute_depth1(constants)
    reached_d1 = count_targets_reached(d1)

    d2 = compute_depth2(constants, d1)
    reached_d2 = count_targets_reached(d2)

    if verbose:
        print(f"  {label}")
        print(f"    Depth 1: {len(d1):,} values, {len(reached_d1)}/9 targets")
        print(f"    Depth 2: {len(d2):,} values, {len(reached_d2)}/9 targets")
        if len(reached_d2) < 9:
            missed = set(TARGETS.keys()) - reached_d2
            print(f"    Missed: {missed}")

    return len(reached_d1), len(reached_d2)

# ============================================================
# Main
# ============================================================

def main():
    random.seed(42)
    np.random.seed(42)

    print("=" * 70)
    print("H-CX-467 / H-CX-471 VERIFICATION")
    print("Universal Saturation at Depth 3 + Null Baseline")
    print("=" * 70)
    print()
    print(f"Targets (9): {list(TARGETS.keys())}")
    print(f"Target values: {[f'{v:.6f}' for v in TARGET_VALS]}")
    print(f"Tolerance: {TOLERANCE*100}% relative")
    print()

    # ----------------------------------------------------------
    # Part 1: STRUCTURED CONSTANTS
    # ----------------------------------------------------------
    print("=" * 70)
    print("PART 1: STRUCTURED CONSTANTS (S, G, T domains)")
    print("=" * 70)

    S_constants = [0.27, 2.269, 0.6301, 0.3265, 1.2372, 4.789]
    G_constants = [3, 8, 24, 45, 78, 133]
    T_constants = [12, 24, 240, 2, 26, 10]

    print(f"\nS domain: {S_constants}")
    d1_s, d2_s = evaluate_constants(S_constants, "S domain", verbose=True)

    print(f"\nG domain: {G_constants}")
    d1_g, d2_g = evaluate_constants([float(x) for x in G_constants], "G domain", verbose=True)

    print(f"\nT domain: {T_constants}")
    d1_t, d2_t = evaluate_constants([float(x) for x in T_constants], "T domain", verbose=True)

    # Also test math constants
    math_constants = [math.pi, math.e, 1.0, 2.0, 3.0, 6.0]
    print(f"\nMath constants: {math_constants}")
    d1_m, d2_m = evaluate_constants(math_constants, "Math constants", verbose=True)

    # ----------------------------------------------------------
    # Part 2: NULL BASELINE (Random Constants)
    # ----------------------------------------------------------
    print()
    print("=" * 70)
    print("PART 2: NULL BASELINE — 1000 Random Sets of 6 Constants")
    print("Each constant ~ Uniform[0.01, 10.0]")
    print("=" * 70)

    N_TRIALS = 1000
    d1_counts = []
    d2_counts = []

    t0 = time.time()
    for trial in range(N_TRIALS):
        if trial % 100 == 0 and trial > 0:
            elapsed = time.time() - t0
            eta = elapsed / trial * (N_TRIALS - trial)
            print(f"  Trial {trial}/{N_TRIALS} ({elapsed:.0f}s elapsed, ~{eta:.0f}s remaining)")

        rand_consts = [random.uniform(0.01, 10.0) for _ in range(6)]

        d1 = compute_depth1(rand_consts)
        reached_d1 = count_targets_reached(d1)

        d2 = compute_depth2(rand_consts, d1)
        reached_d2 = count_targets_reached(d2)

        d1_counts.append(len(reached_d1))
        d2_counts.append(len(reached_d2))

    elapsed = time.time() - t0
    print(f"\n  Completed {N_TRIALS} trials in {elapsed:.1f}s")

    d1_arr = np.array(d1_counts)
    d2_arr = np.array(d2_counts)

    print()
    print("-" * 50)
    print("NULL BASELINE RESULTS (depth 1 = 2 ops, depth 2 = 3 ops)")
    print("-" * 50)
    print(f"  Depth 1: mean={d1_arr.mean():.2f}, std={d1_arr.std():.2f}, "
          f"min={d1_arr.min()}, max={d1_arr.max()}")
    print(f"  Depth 2: mean={d2_arr.mean():.2f}, std={d2_arr.std():.2f}, "
          f"min={d2_arr.min()}, max={d2_arr.max()}")
    print()

    # Distribution
    print("  Depth-2 distribution (targets reached):")
    for k in range(10):
        count = np.sum(d2_arr == k)
        bar = '#' * (count * 50 // N_TRIALS)
        print(f"    {k}/9: {count:4d} ({count/N_TRIALS*100:5.1f}%) {bar}")

    frac_9 = np.sum(d2_arr == 9) / N_TRIALS
    print()
    print(f"  Fraction reaching 9/9 at depth 2: {frac_9*100:.1f}%")
    print(f"  Fraction reaching 8+/9 at depth 2: {np.sum(d2_arr >= 8)/N_TRIALS*100:.1f}%")
    print(f"  Fraction reaching 7+/9 at depth 2: {np.sum(d2_arr >= 7)/N_TRIALS*100:.1f}%")

    # ----------------------------------------------------------
    # Part 3: VERDICT
    # ----------------------------------------------------------
    print()
    print("=" * 70)
    print("VERDICT")
    print("=" * 70)
    print()

    if frac_9 > 0.5:
        print("  H-CX-467: TRIVIAL — random constants also saturate at depth 2.")
        print("  H-CX-471 NULL TEST: POSITIVE — random = structured.")
        print("  Conclusion: Saturation is a property of COMBINATORIAL EXPLOSION,")
        print("  not of the constants being special.")
    elif frac_9 > 0.05:
        print("  H-CX-467: WEAK — random constants sometimes saturate.")
        print(f"  Random 9/9 rate: {frac_9*100:.1f}% vs structured: check above.")
        print("  Partial combinatorial effect.")
    else:
        if d2_s == 9 or d2_g == 9 or d2_t == 9:
            print("  H-CX-467: SUPPORTED — structured constants reach 9/9")
            print(f"  but random constants rarely do ({frac_9*100:.1f}%).")
            print("  The constants ARE special, not just combinatorial explosion.")
        else:
            print("  H-CX-467: NOT SUPPORTED — even structured constants")
            print("  don't reach 9/9 at depth 2.")

    print()
    print(f"  Summary table:")
    print(f"  {'Set':<20} {'Depth1':<10} {'Depth2':<10}")
    print(f"  {'-'*20} {'-'*10} {'-'*10}")
    print(f"  {'S domain':<20} {d1_s:<10} {d2_s:<10}")
    print(f"  {'G domain':<20} {d1_g:<10} {d2_g:<10}")
    print(f"  {'T domain':<20} {d1_t:<10} {d2_t:<10}")
    print(f"  {'Math constants':<20} {d1_m:<10} {d2_m:<10}")
    print(f"  {'Random (mean)':<20} {d1_arr.mean():<10.1f} {d2_arr.mean():<10.1f}")
    print(f"  {'Random (std)':<20} {d1_arr.std():<10.1f} {d2_arr.std():<10.1f}")
    print(f"  {'Random 9/9 frac':<20} {'':10} {frac_9*100:.1f}%")
    print()

    # Per-target difficulty
    print("  Per-target reachability at depth 2 (random baseline):")
    # Re-run a smaller sample to get per-target stats
    per_target_reached = {name: 0 for name in TARGETS}
    N_SAMPLE = 200
    for trial in range(N_SAMPLE):
        rand_consts = [random.uniform(0.01, 10.0) for _ in range(6)]
        d1 = compute_depth1(rand_consts)
        d2 = compute_depth2(rand_consts, d1)
        reached = count_targets_reached(d2)
        for name in reached:
            per_target_reached[name] += 1

    print(f"  {'Target':<10} {'Value':<12} {'Reached':<10} {'Rate':<8}")
    print(f"  {'-'*10} {'-'*12} {'-'*10} {'-'*8}")
    for name, val in sorted(TARGET_LIST, key=lambda x: per_target_reached[x[0]]):
        count = per_target_reached[name]
        print(f"  {name:<10} {val:<12.6f} {count:<10} {count/N_SAMPLE*100:5.1f}%")

if __name__ == "__main__":
    main()
