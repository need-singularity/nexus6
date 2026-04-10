#!/usr/bin/env python3
"""
H-CX-463 Verification: Do low-participation domains (S, G, T) reach
convergence targets at depth 3 that they cannot reach at depth 2?

Targeted search:
  - For each domain, generate depth-1 (binary ops on all pairs) = "level1"
  - Generate depth-2 (level1 x base, binary ops) = "level2"
  - Check 9 target convergence values at each depth
  - Report which targets each domain can independently reach at depth 2 vs 3

Domains tested:
  S = Statistical Mechanics (6 constants)
  G = Algebra/Groups (9 constants)
  T = Topology/Geometry (8 constants)
"""

import numpy as np
from itertools import combinations
import warnings
warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════
# DOMAIN DEFINITIONS
# ═══════════════════════════════════════════════════════════

DOMAINS = {
    "S": {
        "name": "Statistical Mechanics",
        "constants": {
            "lambda_c":   0.2700,
            "Onsager_Tc": 2 / np.log(1 + np.sqrt(2)),
            "nu_3D":      0.6301,
            "beta_3D":    0.3265,
            "gamma_3D":   1.2372,
            "delta_3D":   4.789,
        },
    },
    "G": {
        "name": "Algebra/Groups",
        "constants": {
            "dim_SU2":  3.0,
            "dim_SU3":  8.0,
            "dim_SU5":  24.0,
            "dim_SO10": 45.0,
            "dim_E6":   78.0,
            "dim_E7":   133.0,
            "dim_E8":   248.0,
            "rank_E8":  8.0,
            "Out_S6":   2.0,
        },
    },
    "T": {
        "name": "Topology/Geometry",
        "constants": {
            "kissing_3":  12.0,
            "kissing_4":  24.0,
            "kissing_8":  240.0,
            "kissing_24": 196560.0,
            "chi_S2":     2.0,
            "d_bosonic":  26.0,
            "d_super":    10.0,
            "d_M":        11.0,
        },
    },
}

# ═══════════════════════════════════════════════════════════
# TARGET CONVERGENCE VALUES (9 targets from the project)
# ═══════════════════════════════════════════════════════════

TARGETS = {
    "sqrt(2)":   np.sqrt(2),
    "sqrt(3)":   np.sqrt(3),
    "5/6":       5.0 / 6.0,
    "e":         np.e,
    "zeta(3)":   1.2020569031,
    "ln(4/3)":   np.log(4.0 / 3.0),
    "ln(2)":     np.log(2),
    "gamma_EM":  0.5772156649,
    "1/2":       0.5,
}

THRESHOLD = 0.001  # 0.1% relative error

# ═══════════════════════════════════════════════════════════
# BINARY OPS (from convergence_engine.py)
# ═══════════════════════════════════════════════════════════

def binary_ops(na, va, nb, vb):
    """All binary operations on two values. Returns [(value, expr), ...]"""
    results = []

    def _add(v, expr):
        if isinstance(v, (int, float)) and np.isfinite(v) and 1e-15 < abs(v) < 1e12:
            results.append((v, expr))

    _add(va + vb, f"({na}+{nb})")
    _add(va - vb, f"({na}-{nb})")
    _add(vb - va, f"({nb}-{na})")
    _add(va * vb, f"({na}*{nb})")

    if vb != 0:
        _add(va / vb, f"({na}/{nb})")
    if va != 0:
        _add(vb / va, f"({nb}/{na})")

    if va > 0 and abs(vb) < 20:
        try:
            _add(va ** vb, f"({na}^{nb})")
        except (OverflowError, ValueError):
            pass
    if vb > 0 and abs(va) < 20:
        try:
            _add(vb ** va, f"({nb}^{na})")
        except (OverflowError, ValueError):
            pass

    if va > 0 and va != 1 and vb > 0:
        try:
            _add(np.log(vb) / np.log(va), f"log_{na}({nb})")
        except (ValueError, ZeroDivisionError):
            pass
    if vb > 0 and vb != 1 and va > 0:
        try:
            _add(np.log(va) / np.log(vb), f"log_{nb}({na})")
        except (ValueError, ZeroDivisionError):
            pass

    if abs(va * vb) < 20:
        try:
            _add(np.exp(va * vb), f"exp({na}*{nb})")
        except OverflowError:
            pass

    if va * vb > 0:
        _add(np.sqrt(va * vb), f"sqrt({na}*{nb})")

    if va > 0 and vb != 0 and abs(1 / vb) < 20:
        try:
            _add(va ** (1 / vb), f"{na}^(1/{nb})")
        except (OverflowError, ValueError):
            pass
    if vb > 0 and va != 0 and abs(1 / va) < 20:
        try:
            _add(vb ** (1 / va), f"{nb}^(1/{na})")
        except (OverflowError, ValueError):
            pass

    return results


# ═══════════════════════════════════════════════════════════
# DEPTH GENERATION
# ═══════════════════════════════════════════════════════════

def generate_level1(constants):
    """Depth 1: all binary ops on all pairs of base constants.
    Also include unary ops on individual constants."""
    results = {}  # value -> (expr, value)

    # Unary on base
    for na, va in constants.items():
        results[f"_base_{na}"] = (na, va)
        if va > 0:
            results[f"ln({na})"] = (f"ln({na})", np.log(va))
            results[f"sqrt({na})"] = (f"sqrt({na})", np.sqrt(va))
        if va != 0:
            results[f"1/{na}"] = (f"1/{na}", 1.0 / va)
        if va < 500:
            ev = np.exp(va)
            if np.isfinite(ev) and abs(ev) < 1e12:
                results[f"exp({na})"] = (f"exp({na})", ev)

    # Binary on all pairs
    names = list(constants.keys())
    values = list(constants.values())
    for i in range(len(names)):
        for j in range(len(names)):
            if i == j:
                continue
            ops = binary_ops(names[i], values[i], names[j], values[j])
            for v, expr in ops:
                results[expr] = (expr, v)

    return results


def generate_level2(level1, base_constants):
    """Depth 2: binary ops between level1 results and base constants.
    This is depth-3 from the original base (base -> level1 -> level2)."""
    results = {}

    l1_items = list(level1.values())  # (expr, value) pairs
    base_items = list(base_constants.items())  # (name, value) pairs

    total = len(l1_items) * len(base_items)
    print(f"    Level2 combinations: {len(l1_items)} x {len(base_items)} = {total} pairs")

    count = 0
    for l1_expr, l1_val in l1_items:
        for b_name, b_val in base_items:
            ops = binary_ops(l1_expr, l1_val, b_name, b_val)
            for v, expr in ops:
                # Keep best expression per approximate value (deduplicate)
                key = round(v, 8)
                if key not in results or len(expr) < len(results[key][0]):
                    results[key] = (expr, v)
            count += 1

    print(f"    Level2 unique values: {len(results)}")
    return results


def check_targets(value_dict, targets, threshold=THRESHOLD):
    """Check which targets are matched within threshold.
    Returns dict: target_name -> (best_expr, best_error)"""
    matches = {}

    for tname, tval in targets.items():
        best_err = float("inf")
        best_expr = None

        for key, (expr, val) in value_dict.items():
            if tval == 0:
                continue
            rel_err = abs(val - tval) / abs(tval)
            if rel_err < best_err:
                best_err = rel_err
                best_expr = expr

        if best_err < threshold:
            matches[tname] = (best_expr, best_err)

    return matches


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    print("=" * 72)
    print("H-CX-463 VERIFICATION: Domain Depth Reach Analysis")
    print("=" * 72)
    print(f"\nTargets (9): {', '.join(TARGETS.keys())}")
    print(f"Threshold: {THRESHOLD * 100}% relative error")
    print(f"Domains: S (StatMech), G (Algebra), T (Topology)")
    print()

    # Results storage
    all_results = {}

    for dom_id, dom in DOMAINS.items():
        print("-" * 72)
        print(f"  DOMAIN {dom_id}: {dom['name']}")
        print(f"  Constants ({len(dom['constants'])}): {', '.join(dom['constants'].keys())}")
        print("-" * 72)

        base = dom["constants"]

        # --- Depth 1 (unary + binary on pairs) ---
        print("\n  [Depth 1] Generating unary + all-pair binary ops...")
        level1 = generate_level1(base)
        print(f"    Level1 values: {len(level1)}")

        matches_d1 = check_targets(level1, TARGETS)
        print(f"    Depth-1 matches: {len(matches_d1)}/9")
        for tname, (expr, err) in sorted(matches_d1.items()):
            print(f"      {tname:10s} = {TARGETS[tname]:.6f}  <-  {expr}  (err={err:.6e})")

        # --- Depth 2 (level1 x base) ---
        print(f"\n  [Depth 2] Generating level1 x base binary ops...")
        level2 = generate_level2(level1, base)

        # Merge level1 into level2 for checking (depth 2 includes depth 1)
        merged_d2 = dict(level1)
        for k, v in level2.items():
            merged_d2[k] = v

        matches_d2 = check_targets(merged_d2, TARGETS)
        print(f"    Depth-2 matches: {len(matches_d2)}/9")
        for tname, (expr, err) in sorted(matches_d2.items()):
            marker = " [NEW at depth 2]" if tname not in matches_d1 else ""
            print(f"      {tname:10s} = {TARGETS[tname]:.6f}  <-  {expr}  (err={err:.6e}){marker}")

        # New at depth 2
        new_at_d2 = set(matches_d2.keys()) - set(matches_d1.keys())
        print(f"\n    ** New targets reached at depth 2: {len(new_at_d2)}")
        if new_at_d2:
            for t in sorted(new_at_d2):
                expr, err = matches_d2[t]
                print(f"       {t}: {expr} (err={err:.6e})")

        # Store
        all_results[dom_id] = {
            "d1": matches_d1,
            "d2": matches_d2,
            "new_d2": new_at_d2,
            "n_level1": len(level1),
            "n_level2": len(level2),
        }
        print()

    # ═══════════════════════════════════════════════════════════
    # SUMMARY TABLE
    # ═══════════════════════════════════════════════════════════

    print("=" * 72)
    print("SUMMARY: Depth Reach by Domain")
    print("=" * 72)

    target_names = sorted(TARGETS.keys())

    # Header
    hdr = f"{'Target':12s} {'Value':>10s}"
    for dom_id in ["S", "G", "T"]:
        hdr += f"  {dom_id}_d1  {dom_id}_d2"
    print(hdr)
    print("-" * len(hdr))

    for tname in target_names:
        row = f"{tname:12s} {TARGETS[tname]:10.6f}"
        for dom_id in ["S", "G", "T"]:
            d1_hit = tname in all_results[dom_id]["d1"]
            d2_hit = tname in all_results[dom_id]["d2"]
            d1_str = " YES " if d1_hit else "  -  "
            if d2_hit and not d1_hit:
                d2_str = " NEW "
            elif d2_hit:
                d2_str = " YES "
            else:
                d2_str = "  -  "
            row += f"  {d1_str} {d2_str}"
        print(row)

    print("-" * len(hdr))

    # Totals
    tot = f"{'TOTAL':12s} {'':>10s}"
    for dom_id in ["S", "G", "T"]:
        n1 = len(all_results[dom_id]["d1"])
        n2 = len(all_results[dom_id]["d2"])
        nn = len(all_results[dom_id]["new_d2"])
        tot += f"  {n1:3d}/9  {n2:3d}/9"
    print(tot)

    new_row = f"{'NEW at d2':12s} {'':>10s}"
    for dom_id in ["S", "G", "T"]:
        nn = len(all_results[dom_id]["new_d2"])
        new_row += f"        +{nn:d}   "
    print(new_row)

    # ═══════════════════════════════════════════════════════════
    # HYPOTHESIS VERDICT
    # ═══════════════════════════════════════════════════════════

    print("\n" + "=" * 72)
    print("H-CX-463 VERDICT")
    print("=" * 72)

    for dom_id in ["S", "G", "T"]:
        r = all_results[dom_id]
        n1 = len(r["d1"])
        n2 = len(r["d2"])
        nn = len(r["new_d2"])
        name = DOMAINS[dom_id]["name"]
        print(f"\n  {dom_id} ({name}):")
        print(f"    Depth 1: {n1}/9 targets reached")
        print(f"    Depth 2: {n2}/9 targets reached ({nn} new)")
        if nn > 0:
            print(f"    -> CONFIRMED: {dom_id} gains {nn} new convergence target(s) at depth 2")
            print(f"       (= depth 3 from base, consistent with H-CX-463)")
        else:
            print(f"    -> No new targets at depth 2 (depth 3 from base)")

    s_new = len(all_results["S"]["new_d2"])
    g_new = len(all_results["G"]["new_d2"])
    t_new = len(all_results["T"]["new_d2"])
    total_new = s_new + g_new + t_new

    print(f"\n  Overall: {total_new} new target(s) unlocked at depth 3 across S/G/T")
    if total_new > 0:
        print("  H-CX-463: SUPPORTED -- low-participation domains reach new")
        print("  convergence targets at depth 3 that they cannot reach at depth 2.")
    else:
        print("  H-CX-463: NOT SUPPORTED -- no new targets unlocked at depth 3.")

    print("\n" + "=" * 72)
    print("Search space sizes:")
    for dom_id in ["S", "G", "T"]:
        r = all_results[dom_id]
        print(f"  {dom_id}: level1={r['n_level1']}, level2={r['n_level2']}")
    print("=" * 72)


if __name__ == "__main__":
    main()
