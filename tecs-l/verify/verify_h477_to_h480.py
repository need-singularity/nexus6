#!/usr/bin/env python3
"""Verify H-CX-477 through H-CX-480: Domain reachability analysis.

H-CX-477: pi isolation to Analysis domain
H-CX-478: Q-barrier = coupling constants vs algebraic irrationals
H-CX-479: S -> ln(3) = Ising -> qutrit entropy
H-CX-480: Domain role classification matrix
"""

import numpy as np
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════
# Import domains from convergence_engine
# ═══════════════════════════════════════════════════════════════
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convergence_engine import DOMAINS

THRESHOLD = 0.001  # 0.1%

# Binary ops
def binary_ops(a, b):
    results = []
    results.append((a + b, f"({{}}) + ({{}})"))
    results.append((a - b, f"({{}}) - ({{}})"))
    results.append((b - a, f"({{}}) - ({{}})"))
    results.append((a * b, f"({{}}) * ({{}})"))
    if b != 0:
        results.append((a / b, f"({{}}) / ({{}})"))
    if a != 0:
        results.append((b / a, f"({{}}) / ({{}})"))
    # Power (safe range)
    if a > 0 and abs(b) < 20:
        try:
            v = a ** b
            if np.isfinite(v) and abs(v) < 1e12:
                results.append((v, f"({{}}) ^ ({{}})"))
        except:
            pass
    if b > 0 and abs(a) < 20:
        try:
            v = b ** a
            if np.isfinite(v) and abs(v) < 1e12:
                results.append((v, f"({{}}) ^ ({{}})"))
        except:
            pass
    return results

# Unary ops
def unary_ops(name, val):
    results = [(val, name)]
    if val > 0:
        results.append((np.sqrt(val), f"sqrt({name})"))
        results.append((np.log(val), f"ln({name})"))
    results.append((np.exp(val) if val < 50 else None, f"exp({name})"))
    results = [(v, n) for v, n in results if v is not None and np.isfinite(v)]
    if val != 0:
        results.append((1/val, f"1/({name})"))
    results.append((val**2, f"({name})^2"))
    return results


def check_match(val, target, threshold=THRESHOLD):
    if target == 0:
        return abs(val) < threshold
    return abs(val - target) / abs(target) < threshold


def get_domain_constants(domain_id):
    """Return list of (name, value) for a domain."""
    return list(DOMAINS[domain_id]["constants"].items())


def depth1_reachable(domain_id):
    """All values reachable at depth 1 (unary on singles + binary on pairs)."""
    consts = get_domain_constants(domain_id)
    reached = {}  # value_key -> (value, expr)

    # Unary on each constant
    for name, val in consts:
        for uval, uexpr in unary_ops(name, val):
            reached[f"{uexpr}"] = (uval, uexpr)

    # Binary on all pairs (including self-pairs)
    for i, (n1, v1) in enumerate(consts):
        for j, (n2, v2) in enumerate(consts):
            if i <= j:
                for bval, btemplate in binary_ops(v1, v2):
                    expr = btemplate.format(n1, n2) if "{}" in btemplate else btemplate
                    # Fix: manually format
                    expr = f"op({n1}, {n2})"
                    reached[f"{n1}_{n2}_{bval:.10f}"] = (bval, f"bin({n1}, {n2})")

    return reached


def depth1_binary_reachable_detailed(domain_id):
    """Return list of (value, expr_string) for all depth-1 binary ops on pairs."""
    consts = get_domain_constants(domain_id)
    results = []

    # Also include unary ops on individual constants
    for name, val in consts:
        for uval, uexpr in unary_ops(name, val):
            results.append((uval, uexpr))

    # Binary ops on all ordered pairs
    for i, (n1, v1) in enumerate(consts):
        for j, (n2, v2) in enumerate(consts):
            # a + b
            results.append((v1 + v2, f"{n1} + {n2}"))
            # a - b
            results.append((v1 - v2, f"{n1} - {n2}"))
            # a * b
            results.append((v1 * v2, f"{n1} * {n2}"))
            # a / b
            if v2 != 0:
                results.append((v1 / v2, f"{n1} / {n2}"))
            # a ^ b (safe)
            if v1 > 0 and abs(v2) < 20:
                try:
                    v = v1 ** v2
                    if np.isfinite(v) and abs(v) < 1e12:
                        results.append((v, f"{n1} ^ {n2}"))
                except:
                    pass

    return results


def find_matches(results_list, target_val, target_name, threshold=THRESHOLD):
    """Find all expressions matching a target value."""
    matches = []
    for val, expr in results_list:
        if check_match(val, target_val, threshold):
            err = abs(val - target_val) / abs(target_val) * 100 if target_val != 0 else abs(val) * 100
            matches.append((expr, val, err))
    # Sort by error
    matches.sort(key=lambda x: x[2])
    return matches


# ═══════════════════════════════════════════════════════════════
# H-CX-477: pi isolation to Analysis domain
# ═══════════════════════════════════════════════════════════════
def verify_h477():
    print("=" * 72)
    print("H-CX-477: pi is isolated to Analysis domain")
    print("=" * 72)

    pi_targets = {
        "pi":   np.pi,
        "pi/2": np.pi / 2,
        "pi/3": np.pi / 3,
        "pi/4": np.pi / 4,
        "pi/6": np.pi / 6,
    }

    domain_ids = list(DOMAINS.keys())
    print(f"\nDomains: {domain_ids}")
    print(f"Threshold: {THRESHOLD*100:.1f}%\n")

    # Header
    print(f"{'Domain':<6} {'Name':<25}", end="")
    for t in pi_targets:
        print(f" {t:>8}", end="")
    print()
    print("-" * 72)

    reach_matrix = {}  # (domain, target) -> best match or None

    for did in domain_ids:
        dname = DOMAINS[did]["name"]
        results = depth1_binary_reachable_detailed(did)
        print(f"{did:<6} {dname:<25}", end="")

        for tname, tval in pi_targets.items():
            matches = find_matches(results, tval, tname)
            if matches:
                reach_matrix[(did, tname)] = matches[0]
                print(f" {'YES':>8}", end="")
            else:
                reach_matrix[(did, tname)] = None
                print(f" {'--':>8}", end="")
        print()

    # Show best expressions for non-A domains that reach pi-related values
    print("\n--- Detailed matches (showing expressions) ---")
    for did in domain_ids:
        results = depth1_binary_reachable_detailed(did)
        for tname, tval in pi_targets.items():
            matches = find_matches(results, tval, tname)
            if matches:
                best = matches[0]
                print(f"  {did}.{tname}: {best[0]} = {best[1]:.8f} (err={best[2]:.4f}%)")

    # Verdict
    pi_domains = [did for did in domain_ids if reach_matrix.get((did, "pi")) is not None]
    print(f"\nDomains reaching pi: {pi_domains}")
    if pi_domains == ["A"]:
        print("VERDICT: CONFIRMED - pi is isolated to Analysis domain A")
    else:
        print(f"VERDICT: REFUTED - pi reachable from domains: {pi_domains}")

    return reach_matrix


# ═══════════════════════════════════════════════════════════════
# H-CX-478: Q-barrier = coupling constants vs algebraic irrationals
# ═══════════════════════════════════════════════════════════════
def verify_h478():
    print("\n" + "=" * 72)
    print("H-CX-478: Q-barrier = coupling constants vs algebraic irrationals")
    print("=" * 72)

    algebraic_irr = {
        "sqrt(2)": np.sqrt(2),
        "sqrt(3)": np.sqrt(3),
        "sqrt(5)": np.sqrt(5),
        "phi":     (1 + np.sqrt(5)) / 2,
    }

    transcendental = {
        "pi":    np.pi,
        "e":     np.e,
        "ln(2)": np.log(2),
        "gamma": 0.5772156649,
    }

    q_consts = get_domain_constants("Q")
    print(f"\nQ domain constants:")
    for name, val in q_consts:
        print(f"  {name} = {val}")

    # Depth 1
    print("\n--- Depth 1 (unary + binary on Q constants) ---")
    d1_results = depth1_binary_reachable_detailed("Q")

    print(f"\n{'Target':<12} {'Category':<22} {'Reached?':<10} {'Best expr':<40} {'Value':<14} {'Error%'}")
    print("-" * 110)

    for category_name, targets in [("Algebraic irrational", algebraic_irr), ("Transcendental", transcendental)]:
        for tname, tval in targets.items():
            matches = find_matches(d1_results, tval, tname)
            if matches:
                best = matches[0]
                print(f"{tname:<12} {category_name:<22} {'YES':<10} {best[0]:<40} {best[1]:<14.8f} {best[2]:.4f}%")
            else:
                print(f"{tname:<12} {category_name:<22} {'NO':<10}")

    # Depth 2: level1 x base
    print("\n--- Depth 2 (depth1_result op base_constant) ---")
    d2_results = []
    for v1, e1 in d1_results:
        for n2, v2 in q_consts:
            d2_results.append((v1 + v2, f"({e1}) + {n2}"))
            d2_results.append((v1 - v2, f"({e1}) - {n2}"))
            d2_results.append((v2 - v1, f"{n2} - ({e1})"))
            d2_results.append((v1 * v2, f"({e1}) * {n2}"))
            if v2 != 0:
                d2_results.append((v1 / v2, f"({e1}) / {n2}"))
            if v1 != 0:
                d2_results.append((v2 / v1, f"{n2} / ({e1})"))

    print(f"\nDepth-2 expressions generated: {len(d2_results)}")
    print(f"\n{'Target':<12} {'Category':<22} {'D1?':<6} {'D2?':<6} {'D2 Best expr':<50} {'Error%'}")
    print("-" * 120)

    d1_alg = 0
    d1_trans = 0
    d2_alg = 0
    d2_trans = 0

    for category_name, targets in [("Algebraic irrational", algebraic_irr), ("Transcendental", transcendental)]:
        for tname, tval in targets.items():
            d1_match = find_matches(d1_results, tval, tname)
            d2_match = find_matches(d2_results, tval, tname)

            d1_flag = "YES" if d1_match else "NO"
            d2_flag = "YES" if d2_match else "NO"

            if category_name == "Algebraic irrational":
                if d1_match: d1_alg += 1
                if d2_match: d2_alg += 1
            else:
                if d1_match: d1_trans += 1
                if d2_match: d2_trans += 1

            d2_expr = d2_match[0][0][:48] if d2_match else ""
            d2_err = f"{d2_match[0][2]:.4f}%" if d2_match else ""

            print(f"{tname:<12} {category_name:<22} {d1_flag:<6} {d2_flag:<6} {d2_expr:<50} {d2_err}")

    print(f"\nSummary:")
    print(f"  Algebraic irrationals: D1={d1_alg}/4, D2={d2_alg}/4")
    print(f"  Transcendentals:       D1={d1_trans}/4, D2={d2_trans}/4")

    if d2_alg == 0 and d2_trans > 0:
        print("VERDICT: CONFIRMED - Q-barrier is specifically against algebraic irrationals")
    elif d2_alg < d2_trans:
        print("VERDICT: PARTIAL - Q reaches fewer algebraic irrationals than transcendentals")
    else:
        print("VERDICT: REFUTED - No clear barrier against algebraic irrationals")


# ═══════════════════════════════════════════════════════════════
# H-CX-479: S -> ln(3) = Ising -> qutrit entropy
# ═══════════════════════════════════════════════════════════════
def verify_h479():
    print("\n" + "=" * 72)
    print("H-CX-479: S -> ln(3) = Ising -> qutrit entropy")
    print("=" * 72)

    s_consts = get_domain_constants("S")
    print(f"\nS domain constants:")
    for name, val in s_consts:
        print(f"  {name} = {val:.10f}")

    ln3 = np.log(3)
    ln2 = np.log(2)
    print(f"\nTargets: ln(3) = {ln3:.10f}, ln(2) = {ln2:.10f}")

    # Exhaustive search: unary ops
    print("\n--- Unary ops on S constants ---")
    for name, val in s_consts:
        for uval, uexpr in unary_ops(name, val):
            if check_match(uval, ln3):
                print(f"  ln(3) MATCH: {uexpr} = {uval:.10f} (err={abs(uval-ln3)/ln3*100:.6f}%)")
            if check_match(uval, ln2):
                print(f"  ln(2) MATCH: {uexpr} = {uval:.10f} (err={abs(uval-ln2)/ln2*100:.6f}%)")

    # Exhaustive search: binary ops on all pairs
    print("\n--- Binary ops on S constant pairs ---")
    ln3_matches = []
    ln2_matches = []

    for i, (n1, v1) in enumerate(s_consts):
        for j, (n2, v2) in enumerate(s_consts):
            ops = [
                (v1 + v2, f"{n1} + {n2}"),
                (v1 - v2, f"{n1} - {n2}"),
                (v1 * v2, f"{n1} * {n2}"),
            ]
            if v2 != 0:
                ops.append((v1 / v2, f"{n1} / {n2}"))
            if v1 > 0 and abs(v2) < 20:
                try:
                    v = v1 ** v2
                    if np.isfinite(v) and abs(v) < 1e12:
                        ops.append((v, f"{n1} ^ {n2}"))
                except:
                    pass

            for val, expr in ops:
                if np.isfinite(val):
                    if check_match(val, ln3):
                        err = abs(val - ln3) / ln3 * 100
                        ln3_matches.append((expr, val, err))
                    if check_match(val, ln2):
                        err = abs(val - ln2) / ln2 * 100
                        ln2_matches.append((expr, val, err))

    # Also try unary(binary) combinations
    print("\n--- Unary(Binary) on S constant pairs ---")
    for i, (n1, v1) in enumerate(s_consts):
        for j, (n2, v2) in enumerate(s_consts):
            bin_ops = [
                (v1 + v2, f"{n1} + {n2}"),
                (v1 - v2, f"{n1} - {n2}"),
                (v1 * v2, f"{n1} * {n2}"),
            ]
            if v2 != 0:
                bin_ops.append((v1 / v2, f"{n1} / {n2}"))

            for bval, bexpr in bin_ops:
                if np.isfinite(bval) and bval > 0:
                    for uval, uexpr_template in [(np.sqrt(bval), "sqrt"), (np.log(bval), "ln"),
                                                  (np.exp(bval) if bval < 50 else None, "exp"),
                                                  (1/bval if bval != 0 else None, "1/"),
                                                  (bval**2, "sq")]:
                        if uval is not None and np.isfinite(uval):
                            expr = f"{uexpr_template}({bexpr})"
                            if check_match(uval, ln3):
                                err = abs(uval - ln3) / ln3 * 100
                                ln3_matches.append((expr, uval, err))
                            if check_match(uval, ln2):
                                err = abs(uval - ln2) / ln2 * 100
                                ln2_matches.append((expr, uval, err))

    ln3_matches.sort(key=lambda x: x[2])
    ln2_matches.sort(key=lambda x: x[2])

    print(f"\nln(3) matches from S domain ({len(ln3_matches)} found):")
    for expr, val, err in ln3_matches[:10]:
        print(f"  {expr} = {val:.10f} (err={err:.6f}%)")

    print(f"\nln(2) matches from S domain ({len(ln2_matches)} found):")
    for expr, val, err in ln2_matches[:10]:
        print(f"  {expr} = {val:.10f} (err={err:.6f}%)")

    if ln3_matches:
        best = ln3_matches[0]
        print(f"\nBest path to ln(3): {best[0]} = {best[1]:.10f} (err={best[2]:.6f}%)")
        if best[2] < 0.01:
            print("VERDICT: CONFIRMED - S domain reaches ln(3) (qutrit entropy)")
        else:
            print("VERDICT: APPROXIMATE - S reaches ln(3) within 0.1% but not exact")
    else:
        print("VERDICT: REFUTED - S domain cannot reach ln(3) at depth 1")

    if ln2_matches:
        best = ln2_matches[0]
        print(f"ln(2) reachability: {best[0]} = {best[1]:.10f} (err={best[2]:.6f}%)")
    else:
        print("ln(2): NOT reachable from S domain at depth 1")


# ═══════════════════════════════════════════════════════════════
# H-CX-480: Domain role classification matrix
# ═══════════════════════════════════════════════════════════════
def verify_h480():
    print("\n" + "=" * 72)
    print("H-CX-480: Domain role classification matrix")
    print("=" * 72)

    categories = {
        "Algebraic": {
            "sqrt(2)": np.sqrt(2),
            "sqrt(3)": np.sqrt(3),
            "sqrt(5)": np.sqrt(5),
            "phi":     (1 + np.sqrt(5)) / 2,
        },
        "Transcend": {
            "e":       np.e,
            "pi":      np.pi,
            "gamma":   0.5772156649,
            "zeta(3)": 1.2020569031,
        },
        "Logarithm": {
            "ln(2)":    np.log(2),
            "ln(3)":    np.log(3),
            "ln(4/3)":  np.log(4/3),
        },
        "Project": {
            "GZ_width": np.log(4/3),
            "1/e":      1 / np.e,
            "GZ_lower": 0.5 - np.log(4/3),
            "5/6":      5/6,
            "1/3":      1/3,
        },
    }

    domain_ids = list(DOMAINS.keys())

    # Build matrix: domain x category -> count of targets reached
    matrix = {}  # (domain_id, category) -> list of target names reached
    detail = {}  # (domain_id, target_name) -> best expression

    for did in domain_ids:
        results = depth1_binary_reachable_detailed(did)
        for cat_name, targets in categories.items():
            reached = []
            for tname, tval in targets.items():
                matches = find_matches(results, tval, tname)
                if matches:
                    reached.append(tname)
                    detail[(did, tname)] = matches[0]
            matrix[(did, cat_name)] = reached

    # Print matrix
    cat_names = list(categories.keys())
    print(f"\n{'Domain':<6} {'Name':<22}", end="")
    for c in cat_names:
        n_targets = len(categories[c])
        print(f" {c+'('+str(n_targets)+')':>14}", end="")
    print(f" {'Total':>8}")
    print("-" * 82)

    for did in domain_ids:
        dname = DOMAINS[did]["name"]
        total = 0
        print(f"{did:<6} {dname:<22}", end="")
        for cat in cat_names:
            n = len(matrix[(did, cat)])
            n_max = len(categories[cat])
            total += n
            bar = "*" * n + "." * (n_max - n)
            print(f" {bar:>14}", end="")
        print(f" {total:>8}")

    # Detailed: which targets each domain reaches
    print("\n--- Detailed reach per domain ---")
    for did in domain_ids:
        dname = DOMAINS[did]["name"]
        all_reached = []
        for cat in cat_names:
            for t in matrix[(did, cat)]:
                all_reached.append(f"{t}")
        if all_reached:
            print(f"  {did} ({dname}): {', '.join(all_reached)}")
        else:
            print(f"  {did} ({dname}): (none)")

    # Show best expressions for each match
    print("\n--- Best expressions ---")
    for did in domain_ids:
        for cat in cat_names:
            for tname in matrix[(did, cat)]:
                expr, val, err = detail[(did, tname)]
                print(f"  {did}.{tname}: {expr} = {val:.8f} (err={err:.4f}%)")

    # Specialization analysis
    print("\n--- Specialization patterns ---")
    for did in domain_ids:
        dname = DOMAINS[did]["name"]
        scores = {}
        for cat in cat_names:
            n = len(matrix[(did, cat)])
            n_max = len(categories[cat])
            scores[cat] = n / n_max if n_max > 0 else 0

        best_cat = max(scores, key=scores.get) if any(v > 0 for v in scores.values()) else "none"
        best_score = scores.get(best_cat, 0)
        if best_score > 0:
            print(f"  {did} ({dname}): specializes in {best_cat} ({best_score*100:.0f}%)")
        else:
            print(f"  {did} ({dname}): no non-trivial targets reached")


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 72)
    print("  VERIFICATION: H-CX-477 to H-CX-480")
    print("  Domain Reachability Analysis")
    print("=" * 72)

    verify_h477()
    verify_h478()
    verify_h479()
    verify_h480()

    print("\n" + "=" * 72)
    print("  ALL VERIFICATIONS COMPLETE")
    print("=" * 72)
