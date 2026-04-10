#!/usr/bin/env python3
"""H-CX-464: Convergence Hierarchy = Fundamentality Measure

Hypothesis: The number of independent domains that can reach a constant
via depth-1 binary operations is a measure of its "mathematical fundamentality".

Predictions:
  - 4-domain constants (sqrt(2), sqrt(3), e, 5/6, GZ_width) more fundamental than 3-domain
  - Small integers (1,2,3,4) should score high
  - Deep transcendentals (e, pi) should score high
  - Physics-specific constants (1/alpha, Feigenbaum) should score low
"""

import sys
import os
import warnings
from collections import defaultdict

import numpy as np

warnings.filterwarnings("ignore", category=RuntimeWarning)

# Import DOMAINS from convergence_engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convergence_engine import DOMAINS

# ═══════════════════════════════════════════════════════════════
# BROAD TARGET SET
# ═══════════════════════════════════════════════════════════════

TARGETS = {}

# Mathematical constants
TARGETS.update({
    "pi":           np.pi,
    "e":            np.e,
    "1/e":          1/np.e,
    "phi_gold":     (1+np.sqrt(5))/2,
    "sqrt(2)":      np.sqrt(2),
    "sqrt(3)":      np.sqrt(3),
    "sqrt(5)":      np.sqrt(5),
    "ln(2)":        np.log(2),
    "ln(3)":        np.log(3),
    "ln(10)":       np.log(10),
    "gamma_EM":     0.5772156649,       # Euler-Mascheroni
    "zeta(3)":      1.2020569031,       # Apery
    "Catalan_G":    0.9159655941,       # Catalan's constant
    "Khinchin_K":   2.6854520011,       # Khinchin's constant
    "pi^2/6":       np.pi**2/6,         # zeta(2)
    "pi/2":         np.pi/2,
    "pi/3":         np.pi/3,
    "pi/4":         np.pi/4,
    "pi/6":         np.pi/6,
    "e^2":          np.e**2,
    "ln(4/3)":      np.log(4/3),        # GZ width
})

# Fractions from the project
TARGETS.update({
    "1/2":    0.5,
    "1/3":    1/3,
    "1/6":    1/6,
    "5/6":    5/6,
    "2/3":    2/3,
    "3/4":    0.75,
    "4/3":    4/3,
})

# Integers 1-20
for n in range(1, 21):
    TARGETS[str(n)] = float(n)

# Physics constants
TARGETS.update({
    "1/alpha":          137.035999084,
    "alpha_s":          0.1185,
    "sin2_thetaW":      0.23122,
    "Feigenbaum_delta":  4.66920160910299,
    "Feigenbaum_alpha":  2.50290787509589,
    "CMB_T":             2.7255,
    "Onsager_Tc":        2/np.log(1+np.sqrt(2)),
    "lambda_c":          0.2700,        # Langton edge of chaos
})

# ═══════════════════════════════════════════════════════════════
# ENGINE: depth-1 binary ops within each domain
# ═══════════════════════════════════════════════════════════════

OPS = {
    '+': lambda a, b: a + b,
    '-': lambda a, b: a - b,
    '*': lambda a, b: a * b,
    '/': lambda a, b: a / b if abs(b) > 1e-15 else None,
}

THRESHOLD = 0.001  # 0.1%


def reachable_values_from_domain(domain_constants):
    """Generate all depth-1 binary op results from constants in one domain."""
    vals = list(domain_constants.values())
    names = list(domain_constants.keys())
    results = set()
    for i in range(len(vals)):
        results.add(vals[i])  # depth 0: the constant itself
        for j in range(len(vals)):
            if i == j:
                continue
            for op_name, op_fn in OPS.items():
                try:
                    r = op_fn(vals[i], vals[j])
                    if r is not None and np.isfinite(r):
                        results.add(r)
                except:
                    pass
    return results


def match_target(target_val, reachable_set, threshold=THRESHOLD):
    """Check if any value in reachable_set is within threshold of target."""
    for r in reachable_set:
        if abs(r) < 1e-15 and abs(target_val) < 1e-15:
            return True
        if abs(target_val) > 1e-15:
            if abs(r - target_val) / abs(target_val) < threshold:
                return True
    return False


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 75)
    print("H-CX-464: Convergence Hierarchy = Fundamentality Measure")
    print("=" * 75)
    print(f"\nDomains: {len(DOMAINS)}")
    print(f"Targets: {len(TARGETS)}")
    print(f"Threshold: {THRESHOLD*100:.1f}%")
    print(f"Depth: 1 (binary ops within each domain)\n")

    # Pre-compute reachable sets per domain
    domain_reachable = {}
    for dkey, dinfo in DOMAINS.items():
        reach = reachable_values_from_domain(dinfo["constants"])
        domain_reachable[dkey] = reach
        print(f"  Domain {dkey} ({dinfo['name']}): {len(dinfo['constants'])} constants -> {len(reach)} reachable values")

    print()

    # For each target, count independent domains
    results = []
    for tname, tval in TARGETS.items():
        matching_domains = []
        for dkey in DOMAINS:
            if match_target(tval, domain_reachable[dkey]):
                matching_domains.append(dkey)
        results.append((tname, tval, len(matching_domains), matching_domains))

    # Sort by domain count (descending), then alphabetically
    results.sort(key=lambda x: (-x[2], x[0]))

    # ═══ FULL RANKING TABLE ═══
    print("=" * 75)
    print("FULL RANKING: target | value | #domains | domains")
    print("=" * 75)

    tier_counts = defaultdict(int)
    for tname, tval, ndom, doms in results:
        tier_counts[ndom] += 1
        dom_str = ",".join(sorted(doms))
        if abs(tval) < 1000:
            print(f"  {tname:25s}  {tval:12.6f}  {ndom} domains  [{dom_str}]")
        else:
            print(f"  {tname:25s}  {tval:12.1f}  {ndom} domains  [{dom_str}]")

    # ═══ TIER SUMMARY ═══
    print("\n" + "=" * 75)
    print("TIER SUMMARY")
    print("=" * 75)
    for n in sorted(tier_counts.keys(), reverse=True):
        names_at_tier = [r[0] for r in results if r[2] == n]
        print(f"  {n}-domain ({tier_counts[n]} targets): {', '.join(names_at_tier[:15])}")
        if len(names_at_tier) > 15:
            print(f"    ... and {len(names_at_tier)-15} more")

    # ═══ PREDICTION TESTS ═══
    print("\n" + "=" * 75)
    print("PREDICTION TESTS")
    print("=" * 75)

    result_dict = {r[0]: r[2] for r in results}

    # Test 1: Small integers should score high
    print("\n--- Test 1: Small integers (1-6) should score high ---")
    int_scores = [(str(n), result_dict.get(str(n), 0)) for n in range(1, 7)]
    for name, score in int_scores:
        print(f"  {name:5s}: {score} domains")
    avg_small = np.mean([s for _, s in int_scores])
    print(f"  Average: {avg_small:.1f} domains")

    # Test 2: Deep transcendentals should score high
    print("\n--- Test 2: Deep transcendentals (e, pi, sqrt(2), ln(2)) ---")
    deep_names = ["e", "pi", "sqrt(2)", "ln(2)", "phi_gold", "sqrt(3)"]
    for name in deep_names:
        score = result_dict.get(name, 0)
        print(f"  {name:12s}: {score} domains")
    avg_deep = np.mean([result_dict.get(n, 0) for n in deep_names])
    print(f"  Average: {avg_deep:.1f} domains")

    # Test 3: Physics-specific constants should score low
    print("\n--- Test 3: Physics-specific constants (should score low) ---")
    phys_names = ["1/alpha", "alpha_s", "sin2_thetaW", "Feigenbaum_delta",
                  "Feigenbaum_alpha", "CMB_T"]
    for name in phys_names:
        score = result_dict.get(name, 0)
        print(f"  {name:20s}: {score} domains")
    avg_phys = np.mean([result_dict.get(n, 0) for n in phys_names])
    print(f"  Average: {avg_phys:.1f} domains")

    # Test 4: Project constants (GZ width, 5/6, 1/2, 1/3)
    print("\n--- Test 4: Project core constants ---")
    proj_names = ["ln(4/3)", "5/6", "1/2", "1/3", "1/6", "1/e"]
    for name in proj_names:
        score = result_dict.get(name, 0)
        print(f"  {name:12s}: {score} domains")
    avg_proj = np.mean([result_dict.get(n, 0) for n in proj_names])
    print(f"  Average: {avg_proj:.1f} domains")

    # ═══ STATISTICAL SUMMARY ═══
    print("\n" + "=" * 75)
    print("STATISTICAL COMPARISON")
    print("=" * 75)
    print(f"  Small integers (1-6):    avg {avg_small:.2f} domains")
    print(f"  Deep transcendentals:    avg {avg_deep:.2f} domains")
    print(f"  Project constants:       avg {avg_proj:.2f} domains")
    print(f"  Physics-specific:        avg {avg_phys:.2f} domains")

    gap = avg_deep - avg_phys
    print(f"\n  Deep - Physics gap:      {gap:+.2f} domains")

    # ═══ SURPRISE DISCOVERIES ═══
    print("\n" + "=" * 75)
    print("SURPRISE DISCOVERIES (unexpected high domain count)")
    print("=" * 75)

    # Targets with >= 4 domains that aren't integers or well-known
    well_known_high = {"1", "2", "3", "4", "5", "6", "8", "12", "13", "24",
                       "e", "pi", "sqrt(2)", "sqrt(3)", "ln(2)", "1/2", "1/3"}
    surprises = [(n, v, d, doms) for n, v, d, doms in results
                 if d >= 3 and n not in well_known_high]
    if surprises:
        for name, val, ndom, doms in surprises[:20]:
            print(f"  {name:25s} = {val:.6f}  -> {ndom} domains [{','.join(sorted(doms))}]")
    else:
        print("  (none with >= 3 domains outside well-known set)")

    # ═══ HYPOTHESIS VERDICT ═══
    print("\n" + "=" * 75)
    print("H-CX-464 VERDICT")
    print("=" * 75)

    # Check predictions
    pred1 = avg_small >= 2.0  # small ints reachable from many domains
    pred2 = avg_deep > avg_phys  # deep transcendentals > physics
    pred3 = avg_phys <= 2.0  # physics-specific low reach
    pred4 = gap >= 1.0  # meaningful gap

    tests_passed = sum([pred1, pred2, pred3, pred4])
    print(f"\n  Prediction 1 (small ints avg >= 2):        {'PASS' if pred1 else 'FAIL'} (avg={avg_small:.1f})")
    print(f"  Prediction 2 (transcendentals > physics):  {'PASS' if pred2 else 'FAIL'} ({avg_deep:.1f} vs {avg_phys:.1f})")
    print(f"  Prediction 3 (physics avg <= 2):           {'PASS' if pred3 else 'FAIL'} (avg={avg_phys:.1f})")
    print(f"  Prediction 4 (gap >= 1.0):                 {'PASS' if pred4 else 'FAIL'} (gap={gap:.1f})")
    print(f"\n  Result: {tests_passed}/4 predictions passed")

    if tests_passed >= 3:
        print("  Status: SUPPORTED - domain count correlates with fundamentality")
    elif tests_passed >= 2:
        print("  Status: PARTIAL - some evidence for hierarchy")
    else:
        print("  Status: NOT SUPPORTED - domain count does not track fundamentality")

    # ═══ ASCII HISTOGRAM ═══
    print("\n" + "=" * 75)
    print("DOMAIN COUNT DISTRIBUTION")
    print("=" * 75)
    max_dom = max(tier_counts.keys()) if tier_counts else 0
    for n in range(max_dom, -1, -1):
        if n in tier_counts:
            bar = "#" * tier_counts[n]
            print(f"  {n}-domain | {bar} ({tier_counts[n]})")

    print("\n" + "=" * 75)
    print("Done.")


if __name__ == "__main__":
    main()
