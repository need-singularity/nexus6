#!/usr/bin/env python3
"""Quantum Formula Search Engine — Quantum Mechanics Dimensionless Constants × Project Constants DFS Search

Automatically searches for mathematical target constant matches by combining
project constants (18) and quantum dimensionless constants (9).
Distinguishes chance vs structural discoveries with Texas Sharpshooter test.

Usage:
  python3 quantum_formula_engine.py                    # 2 combinations, within 0.1%
  python3 quantum_formula_engine.py --threshold 0.01   # Only within 0.01%
  python3 quantum_formula_engine.py --depth 3          # 3 combinations (slow)
  python3 quantum_formula_engine.py --cross-only        # Group A×B cross only
  python3 quantum_formula_engine.py --texas             # Include Texas Sharpshooter test
  python3 quantum_formula_engine.py --top 20            # Output top 20 only
"""

import argparse
import os
import warnings
from datetime import datetime
from itertools import combinations

import numpy as np

warnings.filterwarnings("ignore", category=RuntimeWarning)

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


# ─────────────────────────────────────────
# Group A: Project Constants (existing)
# ─────────────────────────────────────────
PROJECT_CONSTS = {
    "1/2": 0.5,
    "1/3": 1 / 3,
    "1/6": 1 / 6,
    "5/6": 5 / 6,
    "2": 2.0,
    "6": 6.0,
    "8": 8.0,
    "17": 17.0,
    "137": 137.0,
    "ln3": np.log(3),
    "ln4/3": np.log(4 / 3),
    "e": np.e,
    "1/e": 1 / np.e,
    "sqrt3": np.sqrt(3),
    "4/3": 4 / 3,
    "sigma6": 12.0,
    "tau6": 4.0,
    "28": 28.0,
    "496": 496.0,
}

# ─────────────────────────────────────────
# Group B: Quantum Constants (dimensionless)
# ─────────────────────────────────────────
QUANTUM_CONSTS = {
    "alpha": 1 / 137.035999084,
    "1/alpha": 137.035999084,
    "g_e-2": 0.00231930436256,
    "alpha_s": 0.1185,
    "sin2_thetaW": 0.23122,
    "m_e/m_p": 1 / 1836.15267343,
    "m_e/m_mu": 1 / 206.7682830,
    "N_gen": 3.0,
    "CMB": 2.7255,
}

# ─────────────────────────────────────────
# Target Constants (matching targets)
# ─────────────────────────────────────────
TARGETS = {
    "pi": np.pi,
    "pi/2": np.pi / 2,
    "pi/3": np.pi / 3,
    "pi/4": np.pi / 4,
    "pi/6": np.pi / 6,
    "sqrt2": np.sqrt(2),
    "sqrt3": np.sqrt(3),
    "sqrt5": np.sqrt(5),
    "ln2": np.log(2),
    "phi": (1 + np.sqrt(5)) / 2,
    "Catalan": 0.9159655941,
    "zeta3": 1.2020569031,
    "gamma_EM": 0.5772156649,
    "e^gamma": np.exp(0.5772156649),
    "1/alpha_exact": 137.035999084,
    # Include project constants as targets (for cross discovery)
    "1/2": 0.5,
    "1/3": 1 / 3,
    "1/6": 1 / 6,
    "5/6": 5 / 6,
    "1/e": 1 / np.e,
}


# ─────────────────────────────────────────
# Classification: Which group the combination belongs to
# ─────────────────────────────────────────
def classify_pair(name_a, name_b):
    """Classify the group combination of two constants."""
    a_proj = name_a in PROJECT_CONSTS
    b_proj = name_b in PROJECT_CONSTS
    if a_proj and b_proj:
        return "A*A"
    elif not a_proj and not b_proj:
        return "B*B"
    else:
        return "A*B"


def classify_triple(name_a, name_b, name_c):
    """Classify the group combination of three constants."""
    names = [name_a, name_b, name_c]
    n_proj = sum(1 for n in names if n in PROJECT_CONSTS)
    if n_proj == 3:
        return "A*A*A"
    elif n_proj == 0:
        return "B*B*B"
    elif n_proj == 2:
        return "A*A*B"
    else:
        return "A*B*B"


# ─────────────────────────────────────────
# Binary Operations (2 constants)
# ─────────────────────────────────────────
def binary_ops(na, va, nb, vb):
    """Return all operation results for two constants as (value, formula string) list."""
    results = []

    # a + b
    results.append((va + vb, f"{na}+{nb}"))
    # a - b
    results.append((va - vb, f"{na}-{nb}"))
    # b - a
    results.append((vb - va, f"{nb}-{na}"))
    # a * b
    results.append((va * vb, f"{na}*{nb}"))
    # a / b
    if vb != 0:
        results.append((va / vb, f"{na}/{nb}"))
    # b / a
    if va != 0:
        results.append((vb / va, f"{nb}/{na}"))

    # a^b (|b| < 20)
    if va > 0 and abs(vb) < 20:
        try:
            val = va ** vb
            if np.isfinite(val) and abs(val) < 1e15:
                results.append((val, f"{na}^{nb}"))
        except (OverflowError, ValueError):
            pass

    # b^a (|a| < 20)
    if vb > 0 and abs(va) < 20:
        try:
            val = vb ** va
            if np.isfinite(val) and abs(val) < 1e15:
                results.append((val, f"{nb}^{na}"))
        except (OverflowError, ValueError):
            pass

    # log_a(b) : a>0, a!=1, b>0
    if va > 0 and va != 1 and vb > 0:
        try:
            val = np.log(vb) / np.log(va)
            if np.isfinite(val) and abs(val) < 1e15:
                results.append((val, f"log_{na}({nb})"))
        except (ValueError, ZeroDivisionError):
            pass

    # log_b(a) : b>0, b!=1, a>0
    if vb > 0 and vb != 1 and va > 0:
        try:
            val = np.log(va) / np.log(vb)
            if np.isfinite(val) and abs(val) < 1e15:
                results.append((val, f"log_{nb}({na})"))
        except (ValueError, ZeroDivisionError):
            pass

    # exp(a*b) : |a*b| < 20
    if abs(va * vb) < 20:
        try:
            val = np.exp(va * vb)
            if np.isfinite(val) and abs(val) < 1e15:
                results.append((val, f"exp({na}*{nb})"))
        except OverflowError:
            pass

    # sqrt(a*b) : a*b > 0
    if va * vb > 0:
        val = np.sqrt(va * vb)
        if np.isfinite(val):
            results.append((val, f"sqrt({na}*{nb})"))

    # a^(1/b) : a>0, b!=0
    if va > 0 and vb != 0 and abs(1 / vb) < 20:
        try:
            val = va ** (1 / vb)
            if np.isfinite(val) and abs(val) < 1e15:
                results.append((val, f"{na}^(1/{nb})"))
        except (OverflowError, ValueError):
            pass

    # b^(1/a) : b>0, a!=0
    if vb > 0 and va != 0 and abs(1 / va) < 20:
        try:
            val = vb ** (1 / va)
            if np.isfinite(val) and abs(val) < 1e15:
                results.append((val, f"{nb}^(1/{na})"))
        except (OverflowError, ValueError):
            pass

    # Valid results only
    return [(v, expr) for v, expr in results
            if isinstance(v, (int, float)) and np.isfinite(v) and abs(v) < 1e15]


# ─────────────────────────────────────────
# Ternary Operations (3 constants)
# ─────────────────────────────────────────
def ternary_ops(na, va, nb, vb, nc, vc):
    """List of operation results for three constants."""
    results = []

    # a*b + c
    results.append((va * vb + vc, f"{na}*{nb}+{nc}"))
    # a*b - c
    results.append((va * vb - vc, f"{na}*{nb}-{nc}"))
    # a*b*c
    val = va * vb * vc
    if np.isfinite(val) and abs(val) < 1e15:
        results.append((val, f"{na}*{nb}*{nc}"))

    # a^b + c (|b| < 20)
    if va > 0 and abs(vb) < 20:
        try:
            val = va ** vb + vc
            if np.isfinite(val) and abs(val) < 1e15:
                results.append((val, f"{na}^{nb}+{nc}"))
        except (OverflowError, ValueError):
            pass

    # (a+b)*c
    results.append(((va + vb) * vc, f"({na}+{nb})*{nc}"))

    # a^b * c (|b| < 20)
    if va > 0 and abs(vb) < 20:
        try:
            val = va ** vb * vc
            if np.isfinite(val) and abs(val) < 1e15:
                results.append((val, f"{na}^{nb}*{nc}"))
        except (OverflowError, ValueError):
            pass

    # a / (b+c)
    if vb + vc != 0:
        results.append((va / (vb + vc), f"{na}/({nb}+{nc})"))

    # (a*b)^c (|c| < 20)
    if va * vb > 0 and abs(vc) < 20:
        try:
            val = (va * vb) ** vc
            if np.isfinite(val) and abs(val) < 1e15:
                results.append((val, f"({na}*{nb})^{nc}"))
        except (OverflowError, ValueError):
            pass

    return [(v, expr) for v, expr in results
            if isinstance(v, (int, float)) and np.isfinite(v) and abs(v) < 1e15]


# ─────────────────────────────────────────
# Search Engine
# ─────────────────────────────────────────
def search(depth=2, threshold=0.001, cross_only=False):
    """Search for formulas that create targets from constant combinations.

    Args:
        depth: Combination depth (2 or 3)
        threshold: Relative error threshold (0.001 = 0.1%)
        cross_only: If True, only A*B cross combinations

    Returns:
        matches: list of dict
        total_trials: Total number of attempts
    """
    all_consts = {}
    all_consts.update(PROJECT_CONSTS)
    all_consts.update(QUANTUM_CONSTS)

    names = list(all_consts.keys())
    vals = [all_consts[n] for n in names]

    matches = []
    total_trials = 0

    # ── 2 combinations ──
    for i in range(len(names)):
        for j in range(i, len(names)):
            na, va = names[i], vals[i]
            nb, vb = names[j], vals[j]

            cat = classify_pair(na, nb)
            if cross_only and cat != "A*B":
                continue

            ops = binary_ops(na, va, nb, vb)
            total_trials += len(ops)

            for val, expr in ops:
                for t_name, t_val in TARGETS.items():
                    if t_val == 0:
                        continue
                    rel_err = abs(val - t_val) / abs(t_val)
                    if rel_err < threshold:
                        # Skip trivial matches (self)
                        if expr == t_name or ('+' not in expr and '-' not in expr
                                              and '*' not in expr and '/' not in expr
                                              and '^' not in expr and 'log' not in expr
                                              and 'exp' not in expr and 'sqrt' not in expr):
                            continue
                        matches.append({
                            "target": t_name,
                            "target_val": t_val,
                            "formula": expr,
                            "formula_val": val,
                            "error": rel_err,
                            "error_pct": rel_err * 100,
                            "category": cat,
                            "depth": 2,
                        })

    # ── 3 combinations (optional) ──
    if depth >= 3:
        for i in range(len(names)):
            for j in range(i, len(names)):
                for k in range(j, len(names)):
                    na, va = names[i], vals[i]
                    nb, vb = names[j], vals[j]
                    nc, vc = names[k], vals[k]

                    cat = classify_triple(na, nb, nc)
                    if cross_only and "A" not in cat and "B" not in cat:
                        continue
                    if cross_only and (cat == "A*A*A" or cat == "B*B*B"):
                        continue

                    # All permutation combinations
                    perms = [
                        (na, va, nb, vb, nc, vc),
                        (na, va, nc, vc, nb, vb),
                        (nb, vb, nc, vc, na, va),
                    ]
                    for pa, pva, pb, pvb, pc, pvc in perms:
                        ops = ternary_ops(pa, pva, pb, pvb, pc, pvc)
                        total_trials += len(ops)

                        for val, expr in ops:
                            for t_name, t_val in TARGETS.items():
                                if t_val == 0:
                                    continue
                                rel_err = abs(val - t_val) / abs(t_val)
                                if rel_err < threshold:
                                    matches.append({
                                        "target": t_name,
                                        "target_val": t_val,
                                        "formula": expr,
                                        "formula_val": val,
                                        "error": rel_err,
                                        "error_pct": rel_err * 100,
                                        "category": cat,
                                        "depth": 3,
                                    })

    # Remove duplicates (same target+formula)
    seen = set()
    unique = []
    for m in matches:
        key = (m["target"], m["formula"])
        if key not in seen:
            seen.add(key)
            unique.append(m)

    # Sort by error
    unique.sort(key=lambda x: x["error_pct"])

    return unique, total_trials


# ─────────────────────────────────────────
# Texas Sharpshooter Test
# ─────────────────────────────────────────
def texas_sharpshooter(matches, total_trials, n_random=5000):
    """Calculate Bonferroni p-value for each discovery.

    Method:
    1. Estimate probability of hitting target with same precision using random constants in same operation form
    2. Total attempts x single probability = Bonferroni p-value
    3. Classification: p<0.01 structural, 0.01~0.05 weak evidence, >0.05 possibly chance

    Returns:
        list of dict with p_value and verdict added
    """
    rng = np.random.default_rng(42)

    # Estimate random hit probability for each target
    target_hit_probs = {}
    for t_name, t_val in TARGETS.items():
        if t_val == 0:
            continue
        hits = 0
        for _ in range(n_random):
            a = rng.uniform(0.01, 200)
            b = rng.uniform(0.01, 200)
            # Try 8 basic operations
            test_vals = [a + b, a - b, a * b]
            if b != 0:
                test_vals.append(a / b)
            if a > 0 and abs(b) < 20:
                try:
                    test_vals.append(a ** b)
                except (OverflowError, ValueError):
                    pass
            if a > 0 and a != 1 and b > 0:
                try:
                    test_vals.append(np.log(b) / np.log(a))
                except (ValueError, ZeroDivisionError):
                    pass
            if abs(a * b) < 20:
                try:
                    test_vals.append(np.exp(a * b))
                except OverflowError:
                    pass
            if a * b > 0:
                test_vals.append(np.sqrt(a * b))

            for v in test_vals:
                if isinstance(v, (int, float)) and np.isfinite(v) and t_val != 0:
                    if abs(v - t_val) / abs(t_val) < 0.001:
                        hits += 1
                        break

        target_hit_probs[t_name] = max(hits / n_random, 1e-6)

    # Bonferroni correction
    results = []
    n_significant = 0
    for m in matches:
        p_single = target_hit_probs.get(m["target"], 0.01)
        # Precision correction: lower probability for smaller errors
        precision_factor = m["error_pct"] / 0.1 if m["error_pct"] > 0 else 0.01
        p_adjusted = min(1.0, p_single * precision_factor * total_trials)

        if p_adjusted < 0.01:
            verdict = "structural"
            n_significant += 1
        elif p_adjusted < 0.05:
            verdict = "weak evidence"
            n_significant += 1
        else:
            verdict = "possibly chance"

        m_copy = dict(m)
        m_copy["p_value"] = p_adjusted
        m_copy["verdict"] = verdict
        results.append(m_copy)

    return results, n_significant


# ─────────────────────────────────────────
# Output
# ─────────────────────────────────────────
def print_results(matches, total_trials, threshold, depth, cross_only, top_n, texas=False):
    """ASCII output of results."""

    n_proj = len(PROJECT_CONSTS)
    n_quant = len(QUANTUM_CONSTS)
    n_total = n_proj + n_quant

    print()
    print("=" * 55)
    print(" Quantum Formula Engine v1.0")
    print(f" Constants: {n_proj}(project) + {n_quant}(quantum) = {n_total}")
    print(f" Operations: {'8 types(2)' if depth < 3 else '8 types(2)+8 types(3)'}, "
          f"Combinations: ~{total_trials:,}")
    mode = "Cross(A*B) only" if cross_only else "All"
    print(f" Mode: {mode}, Depth: {depth}, Threshold: {threshold * 100}%")
    print("=" * 55)

    if not matches:
        print()
        print(" No discoveries.")
        print("=" * 55)
        return

    display = matches[:top_n] if top_n else matches

    print()
    print(f" Discoveries (error <= {threshold * 100}%): {len(matches)}"
          + (f", showing top {top_n}" if top_n and top_n < len(matches) else ""))
    print(" " + "-" * 53)
    print(f" {'Error%':>7} | {'Formula':<28} | {'Value':>10} | {'Target':<10} | Cat")
    print(" " + "-" * 53)

    for m in display:
        err_str = f"{m['error_pct']:.4f}"
        val_str = f"{m['formula_val']:.5f}"
        formula = m["formula"]
        if len(formula) > 28:
            formula = formula[:25] + "..."

        # Grade indicator
        if m["error_pct"] < 0.001:
            star = "**"
        elif m["error_pct"] < 0.01:
            star = "* "
        elif m["error_pct"] < 0.05:
            star = ". "
        else:
            star = "  "

        cat = m.get("category", "?")
        print(f" {star}{err_str:>6} | {formula:<28} | {val_str:>10} | "
              f"{m['target']:<10} | {cat}")

    print(" " + "-" * 53)

    # Texas Sharpshooter test
    if texas:
        print()
        print(" Texas Sharpshooter Test:")
        texas_results, n_sig = texas_sharpshooter(matches, total_trials)
        n_structural = sum(1 for r in texas_results if r["verdict"] == "structural")
        n_weak = sum(1 for r in texas_results if r["verdict"] == "weak evidence")
        n_chance = sum(1 for r in texas_results if r["verdict"] == "possibly chance")

        print(f"  Total attempts: {total_trials:,}, "
              f"Discoveries within {threshold * 100}%: {len(matches)}")
        print(f"  Bonferroni significant: {n_sig}/{len(matches)} (p < 0.05)")
        print(f"   - Structural (p<0.01): {n_structural}")
        print(f"   - Weak evidence (p<0.05): {n_weak}")
        print(f"   - Possibly chance (p>=0.05): {n_chance}")

        # Show top structural discoveries
        structural = [r for r in texas_results if r["verdict"] == "structural"]
        if structural:
            structural.sort(key=lambda x: x["p_value"])
            print()
            print(" Structural discoveries (p < 0.01):")
            for r in structural[:10]:
                print(f"   p={r['p_value']:.4f} | {r['formula']:<28} -> "
                      f"{r['target']} (err {r['error_pct']:.4f}%)")

    print()
    print("=" * 55)


def save_results(matches, total_trials, threshold, depth):
    """Save results to results/ folder."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path = os.path.join(RESULTS_DIR, "quantum_formula_discovery.md")

    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n# Quantum Formula Search [{now}]\n\n")
        f.write(f"Constants {len(PROJECT_CONSTS) + len(QUANTUM_CONSTS)}, "
                f"Attempts {total_trials:,}, "
                f"Discoveries {len(matches)}, "
                f"Threshold {threshold * 100}%\n\n")
        f.write(f"| Error% | Formula | Value | Target | Cat |\n")
        f.write(f"|-------|---------|-------|--------|-----|\n")
        for m in matches[:30]:
            f.write(f"| {m['error_pct']:.4f} | {m['formula']} | "
                    f"{m['formula_val']:.6f} | {m['target']} | "
                    f"{m.get('category', '?')} |\n")
        f.write("\n---\n")

    return path


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Quantum Formula Search Engine — Quantum dimensionless constants x Project constants DFS",
    )
    parser.add_argument("--threshold", type=float, default=0.001,
                        help="Relative error threshold (default 0.001 = 0.1%%)")
    parser.add_argument("--depth", type=int, default=2, choices=[2, 3],
                        help="Combination depth (default 2, 3 is slow)")
    parser.add_argument("--cross-only", action="store_true",
                        help="Search only Group A x Group B cross combinations")
    parser.add_argument("--texas", action="store_true",
                        help="Include Texas Sharpshooter test")
    parser.add_argument("--top", type=int, default=None,
                        help="Output only top N")

    args = parser.parse_args()

    # Search
    matches, total_trials = search(
        depth=args.depth,
        threshold=args.threshold,
        cross_only=args.cross_only,
    )

    # Output
    print_results(
        matches,
        total_trials,
        threshold=args.threshold,
        depth=args.depth,
        cross_only=args.cross_only,
        top_n=args.top,
        texas=args.texas,
    )

    # Save
    path = save_results(matches, total_trials, args.threshold, args.depth)
    print(f" -> results/ saved: {path}")
    print()


if __name__ == "__main__":
    main()