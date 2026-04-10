#!/usr/bin/env python3
"""GZ Offensive Task 5: Cellular Automata Lambda Sweep
Measures Langton's lambda parameter for 256 elementary CA rules.
Tests whether rules exhibiting complex (Class IV) behavior have lambda in GZ.

Hypothesis: Class IV (complex/edge-of-chaos) rules have lambda in [0.2123, 0.5000].
Reference: H-139 confirmed lambda_c ≈ 0.27 for Langton, which is in GZ.
"""

import numpy as np
import sys
sys.path.insert(0, "/Users/ghost/Dev/TECS-L")

np.random.seed(42)

GZ_CENTER = 1 / np.e
GZ_UPPER = 0.5
GZ_LOWER = 0.5 - np.log(4/3)

# ── Elementary CA simulation ──
def run_ca(rule_num, width=201, steps=200):
    """Run elementary CA and return state history."""
    rule_bits = [(rule_num >> i) & 1 for i in range(8)]
    grid = np.zeros((steps, width), dtype=int)
    grid[0, width // 2] = 1  # single cell seed

    for t in range(1, steps):
        for i in range(1, width - 1):
            neighborhood = grid[t-1, i-1] * 4 + grid[t-1, i] * 2 + grid[t-1, i+1]
            grid[t, i] = rule_bits[neighborhood]
    return grid

def langton_lambda(rule_num, k=2):
    """Langton's lambda for k-state 1D CA rule."""
    rule_bits = [(rule_num >> i) & 1 for i in range(8)]
    n_quiescent = sum(1 for b in rule_bits if b == 0)  # quiescent = state 0
    return 1.0 - n_quiescent / 8.0

def classify_ca(grid):
    """Heuristic classification of CA behavior.
    Returns: 1 (uniform), 2 (periodic), 3 (chaotic), 4 (complex)
    """
    steps, width = grid.shape
    # Use last 50 rows for analysis
    last = grid[-50:]

    # Check uniform (all same)
    if np.all(last == last[0]):
        return 1

    # Check entropy of columns
    col_entropies = []
    for c in range(10, width - 10):
        vals, counts = np.unique(last[:, c], return_counts=True)
        p = counts / counts.sum()
        col_entropies.append(-np.sum(p * np.log2(p + 1e-12)))
    mean_entropy = np.mean(col_entropies)

    # Check periodicity
    for period in range(1, 10):
        if steps > 2 * period + 50:
            if np.array_equal(grid[-period:], grid[-2*period:-period]):
                return 2

    # Entropy-based: low = periodic, high = chaotic, medium = complex
    if mean_entropy < 0.3:
        return 2
    elif mean_entropy > 0.9:
        return 3
    else:
        return 4

if __name__ == '__main__':
    print("=" * 70)
    print("GZ OFFENSIVE: CA LAMBDA SWEEP (256 ELEMENTARY RULES)")
    print("=" * 70)
    print(f"  GZ = [{GZ_LOWER:.4f}, {GZ_UPPER:.4f}], center = {GZ_CENTER:.4f}")
    print()

    results = []
    class_counts = {1: 0, 2: 0, 3: 0, 4: 0}

    for rule in range(256):
        lam = langton_lambda(rule)
        grid = run_ca(rule)
        cls = classify_ca(grid)
        class_counts[cls] += 1
        results.append({'rule': rule, 'lambda': lam, 'class': cls,
                        'in_gz': GZ_LOWER <= lam <= GZ_UPPER})

    # ── Results by class ──
    class_names = {1: "Uniform", 2: "Periodic", 3: "Chaotic", 4: "Complex"}
    print(f"\n  Class distribution: {class_counts}")

    for cls in [1, 2, 3, 4]:
        cls_rules = [r for r in results if r['class'] == cls]
        if not cls_rules:
            continue
        lambdas = [r['lambda'] for r in cls_rules]
        in_gz = [r for r in cls_rules if r['in_gz']]
        print(f"\n  Class {cls} ({class_names[cls]}): {len(cls_rules)} rules")
        print(f"    Lambda: mean={np.mean(lambdas):.4f}, std={np.std(lambdas):.4f}, "
              f"range=[{min(lambdas):.4f}, {max(lambdas):.4f}]")
        print(f"    In GZ: {len(in_gz)}/{len(cls_rules)} ({100*len(in_gz)/len(cls_rules):.0f}%)")

    # ── Key test: Class IV lambda distribution ──
    print("\n" + "=" * 70)
    print("KEY TEST: CLASS IV (COMPLEX) RULES vs GOLDEN ZONE")
    print("=" * 70)

    class4 = [r for r in results if r['class'] == 4]
    if class4:
        c4_lambdas = [r['lambda'] for r in class4]
        c4_in_gz = [r for r in class4 if r['in_gz']]
        c4_mean = np.mean(c4_lambdas)

        print(f"\n  Class IV rules: {len(class4)}")
        print(f"  Lambda in GZ: {len(c4_in_gz)}/{len(class4)} ({100*len(c4_in_gz)/len(class4):.0f}%)")
        print(f"  Mean lambda: {c4_mean:.4f} (GZ center = {GZ_CENTER:.4f})")
        print(f"  |mean - 1/e|: {abs(c4_mean - GZ_CENTER):.4f}")

        # Compare with non-Class-IV
        non_c4 = [r for r in results if r['class'] != 4]
        non_c4_in_gz = [r for r in non_c4 if r['in_gz']]
        print(f"\n  Non-Class-IV in GZ: {len(non_c4_in_gz)}/{len(non_c4)} "
              f"({100*len(non_c4_in_gz)/len(non_c4):.0f}%)")

        # Fisher exact test equivalent
        expected_gz_frac = (GZ_UPPER - GZ_LOWER)  # = ln(4/3) ≈ 0.288 of [0,1]
        print(f"  Expected random GZ fraction: {expected_gz_frac:.4f}")

        if len(c4_in_gz) / len(class4) > expected_gz_frac * 1.5:
            print("\n  VERDICT: SUPPORTED — Class IV lambda concentrates in GZ")
        else:
            print("\n  VERDICT: NOT SUPPORTED — Class IV not GZ-enriched")
    else:
        print("\n  No Class IV rules detected (heuristic may need tuning)")

    # ── Lambda histogram (ASCII) ──
    print("\n--- Lambda Distribution (all 256 rules) ---")
    bins = np.linspace(0, 1, 21)
    for i in range(len(bins) - 1):
        count = sum(1 for r in results if bins[i] <= r['lambda'] < bins[i+1])
        bar = "#" * count
        gz_marker = " <-- GZ" if GZ_LOWER <= (bins[i] + bins[i+1])/2 <= GZ_UPPER else ""
        print(f"  {bins[i]:.2f}-{bins[i+1]:.2f} | {bar}{gz_marker}")

    print("\nDone.")
