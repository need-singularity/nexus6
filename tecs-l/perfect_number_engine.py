#!/usr/bin/env python3
"""Perfect Number Divisor Function Engine — Automated exploration of physical constants via σ, τ, φ combinations

Systematically combines divisor functions (σ, τ, φ, etc.) of perfect numbers
to search for matches with physical constants.
Uses Texas sharpshooter test to distinguish between chance vs structural discoveries.

Usage:
  python3 perfect_number_engine.py                 # Full search
  python3 perfect_number_engine.py --target 137    # Specific target
  python3 perfect_number_engine.py --cross         # Cross perfect numbers only
  python3 perfect_number_engine.py --depth 3       # 3-function combinations
"""

import argparse
import os
import warnings
from datetime import datetime
from itertools import combinations, permutations
from math import comb, factorial

import numpy as np

warnings.filterwarnings("ignore", category=RuntimeWarning)

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


# ─────────────────────────────────────────
# Perfect Numbers + Divisor Functions
# ─────────────────────────────────────────
PERFECT_NUMBERS = {
    6: {"sigma": 12, "tau": 4, "phi": 2, "prime_factors": [2, 3]},
    28: {"sigma": 56, "tau": 6, "phi": 12, "prime_factors": [2, 7]},
    496: {"sigma": 992, "tau": 10, "phi": 240, "prime_factors": [2, 31]},
    8128: {"sigma": 16256, "tau": 14, "phi": 4096, "prime_factors": [2, 127]},
}


def build_atom_pool():
    """Create atomic pool of divisor functions for each perfect number.

    For each perfect number P:
      P, σ(P), τ(P), φ(P), σ₋₁(P)=2, prime factors
    """
    atoms = {}  # name -> value
    for p, info in PERFECT_NUMBERS.items():
        tag = f"P{p}"
        atoms[tag] = float(p)
        atoms[f"s({tag})"] = float(info["sigma"])      # σ
        atoms[f"t({tag})"] = float(info["tau"])         # τ
        atoms[f"ph({tag})"] = float(info["phi"])        # φ
        atoms[f"s-1({tag})"] = 2.0                      # σ₋₁ = 2 (perfect number definition)
        for pf in info["prime_factors"]:
            name = f"pf{pf}({tag})"
            atoms[name] = float(pf)
    return atoms


ATOMS = build_atom_pool()


# ─────────────────────────────────────────
# Physical Constant Targets
# ─────────────────────────────────────────
PHYSICS_TARGETS = {
    "alpha_inv": 137.035999084,
    "m_p/m_e": 1836.15267343,
    "m_mu/m_e": 206.7682830,
    "m_tau/m_e": 3477.48,
    "sin2_theta_W": 0.23122,
    "alpha_s": 0.1185,
    "137": 137.0,
    "496": 496.0,
    "10": 10.0,
    "26": 26.0,
}


# ─────────────────────────────────────────
# Extract which perfect number an atom originates from
# ─────────────────────────────────────────
def origin_pn(name):
    """Extract perfect number from atom name."""
    for p in PERFECT_NUMBERS:
        if f"P{p}" in name:
            return p
    return None


def is_cross(name_a, name_b):
    """Do the two atoms originate from different perfect numbers?"""
    return origin_pn(name_a) != origin_pn(name_b)


# ─────────────────────────────────────────
# Non-triviality Score
# ─────────────────────────────────────────
def triviality_score(formula, target_name, target_val, formula_val):
    """Non-triviality score (0=trivial, higher=more interesting).

    Penalty factors:
    - Identity mapping (P496 -> 496)
    - Single atom
    - Integer division (28/4=7 etc obvious)

    Bonus factors:
    - Cross perfect numbers
    - Multiple divisor functions mixed
    - Small error
    """
    score = 5  # Base score

    # Identity mapping penalty
    if f"P{int(target_val)}" in formula and formula.count("(") <= 1:
        score -= 4

    # Single atom penalty
    operators = ["+", "-", "*", "/", "^", "C(", "T("]
    has_op = any(op in formula for op in operators)
    if not has_op:
        score -= 3

    # Cross perfect number bonus
    pns_in_formula = set()
    for p in PERFECT_NUMBERS:
        if f"P{p}" in formula:
            pns_in_formula.add(p)
    if len(pns_in_formula) >= 2:
        score += 2
    if len(pns_in_formula) >= 3:
        score += 1

    # Diverse divisor functions bonus
    func_types = 0
    if "s(" in formula:
        func_types += 1
    if "t(" in formula:
        func_types += 1
    if "ph(" in formula:
        func_types += 1
    if "pf" in formula:
        func_types += 1
    if func_types >= 2:
        score += 1

    return max(0, score)


# ─────────────────────────────────────────
# Binary Operations (2 atoms)
# ─────────────────────────────────────────
def binary_ops(na, va, nb, vb):
    """Return all operation results for two atoms as (value, formula) list."""
    results = []

    # Basic arithmetic
    results.append((va + vb, f"{na}+{nb}"))
    results.append((va - vb, f"{na}-{nb}"))
    results.append((vb - va, f"{nb}-{na}"))
    results.append((va * vb, f"{na}*{nb}"))

    if vb != 0:
        results.append((va / vb, f"{na}/{nb}"))
    if va != 0:
        results.append((vb / va, f"{nb}/{na}"))

    # Powers
    if va > 0 and 0 < abs(vb) < 20:
        try:
            val = va ** vb
            if np.isfinite(val) and abs(val) < 1e15:
                results.append((val, f"{na}^{nb}"))
        except (OverflowError, ValueError):
            pass
    if vb > 0 and 0 < abs(va) < 20:
        try:
            val = vb ** va
            if np.isfinite(val) and abs(val) < 1e15:
                results.append((val, f"{nb}^{na}"))
        except (OverflowError, ValueError):
            pass

    # Combinations C(a, b) — integers only
    if va == int(va) and vb == int(vb):
        a_int, b_int = int(va), int(vb)
        if 0 <= b_int <= a_int <= 200:
            try:
                val = float(comb(a_int, b_int))
                if val < 1e15:
                    results.append((val, f"C({na},{nb})"))
            except (ValueError, OverflowError):
                pass
        if 0 <= a_int <= b_int <= 200:
            try:
                val = float(comb(b_int, a_int))
                if val < 1e15:
                    results.append((val, f"C({nb},{na})"))
            except (ValueError, OverflowError):
                pass

    # Triangular number T(a+b+1) = (a+b+1)(a+b)/2
    s = va + vb + 1
    if s > 0 and s == int(s) and s < 1000:
        val = s * (s - 1) / 2
        if abs(val) < 1e15:
            results.append((val, f"T({na}+{nb}+1)"))

    # sqrt(a*b)
    if va * vb > 0:
        val = np.sqrt(va * vb)
        if np.isfinite(val):
            results.append((val, f"sqrt({na}*{nb})"))

    # log
    if va > 0 and va != 1 and vb > 0:
        try:
            val = np.log(vb) / np.log(va)
            if np.isfinite(val) and abs(val) < 1e15:
                results.append((val, f"log_{na}({nb})"))
        except (ValueError, ZeroDivisionError):
            pass
    if vb > 0 and vb != 1 and va > 0:
        try:
            val = np.log(va) / np.log(vb)
            if np.isfinite(val) and abs(val) < 1e15:
                results.append((val, f"log_{nb}({na})"))
        except (ValueError, ZeroDivisionError):
            pass

    return [(v, expr) for v, expr in results
            if isinstance(v, (int, float)) and np.isfinite(v) and abs(v) < 1e15]


# ─────────────────────────────────────────
# Ternary Operations (3 atoms)
# ─────────────────────────────────────────
def ternary_ops(na, va, nb, vb, nc, vc):
    """Operation results for three atoms."""
    results = []

    # a*b + c, a*b - c
    results.append((va * vb + vc, f"{na}*{nb}+{nc}"))
    results.append((va * vb - vc, f"{na}*{nb}-{nc}"))

    # a*b*c
    val = va * vb * vc
    if np.isfinite(val) and abs(val) < 1e15:
        results.append((val, f"{na}*{nb}*{nc}"))

    # (a+b)*c
    results.append(((va + vb) * vc, f"({na}+{nb})*{nc}"))

    # (a-b)*c
    results.append(((va - vb) * vc, f"({na}-{nb})*{nc}"))

    # a^b + c
    if va > 0 and abs(vb) < 20:
        try:
            val = va ** vb + vc
            if np.isfinite(val) and abs(val) < 1e15:
                results.append((val, f"{na}^{nb}+{nc}"))
        except (OverflowError, ValueError):
            pass

    # a^b * c
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

    # a / (b*c)
    if vb * vc != 0:
        results.append((va / (vb * vc), f"{na}/({nb}*{nc})"))

    # (a*b)^c
    if va * vb > 0 and abs(vc) < 20:
        try:
            val = (va * vb) ** vc
            if np.isfinite(val) and abs(val) < 1e15:
                results.append((val, f"({na}*{nb})^{nc}"))
        except (OverflowError, ValueError):
            pass

    # C(a*b, c) — integers only
    ab = va * vb
    if ab == int(ab) and vc == int(vc):
        ab_int, c_int = int(ab), int(vc)
        if 0 <= c_int <= ab_int <= 200:
            try:
                val = float(comb(ab_int, c_int))
                if val < 1e15:
                    results.append((val, f"C({na}*{nb},{nc})"))
            except (ValueError, OverflowError):
                pass

    return [(v, expr) for v, expr in results
            if isinstance(v, (int, float)) and np.isfinite(v) and abs(v) < 1e15]


# ─────────────────────────────────────────
# Search Engine
# ─────────────────────────────────────────
def search(targets, depth=2, cross_only=False, threshold=0.01):
    """Search for formulas that produce targets using perfect number divisor function combinations.

    Args:
        targets: {name: value} dict
        depth: Combination depth (2 or 3)
        cross_only: If True, only cross different perfect numbers
        threshold: Relative error threshold

    Returns:
        matches: list of dict
        total_trials: Total number of attempts
    """
    names = list(ATOMS.keys())
    vals = [ATOMS[n] for n in names]

    matches = []
    total_trials = 0

    # ── Single atom (unary) ──
    for i in range(len(names)):
        na, va = names[i], vals[i]
        total_trials += 1
        for t_name, t_val in targets.items():
            if t_val == 0:
                continue
            rel_err = abs(va - t_val) / abs(t_val)
            if rel_err < threshold:
                matches.append({
                    "target": t_name,
                    "target_val": t_val,
                    "formula": na,
                    "formula_val": va,
                    "error": rel_err,
                    "error_pct": rel_err * 100,
                    "depth": 1,
                    "origins": {origin_pn(na)},
                })

    # ── 2-combinations ──
    for i in range(len(names)):
        for j in range(i, len(names)):
            na, va = names[i], vals[i]
            nb, vb = names[j], vals[j]

            if cross_only and not is_cross(na, nb):
                continue

            ops = binary_ops(na, va, nb, vb)
            total_trials += len(ops)

            for val, expr in ops:
                for t_name, t_val in targets.items():
                    if t_val == 0:
                        continue
                    rel_err = abs(val - t_val) / abs(t_val)
                    if rel_err < threshold:
                        # Skip trivial identity
                        if expr == t_name:
                            continue
                        origins = set()
                        o1, o2 = origin_pn(na), origin_pn(nb)
                        if o1:
                            origins.add(o1)
                        if o2:
                            origins.add(o2)
                        matches.append({
                            "target": t_name,
                            "target_val": t_val,
                            "formula": expr,
                            "formula_val": val,
                            "error": rel_err,
                            "error_pct": rel_err * 100,
                            "depth": 2,
                            "origins": origins,
                        })

    # ── 3-combinations ──
    if depth >= 3:
        for i in range(len(names)):
            for j in range(i, len(names)):
                for k in range(j, len(names)):
                    na, va = names[i], vals[i]
                    nb, vb = names[j], vals[j]
                    nc, vc = names[k], vals[k]

                    if cross_only:
                        pns = set(filter(None, [origin_pn(na), origin_pn(nb), origin_pn(nc)]))
                        if len(pns) < 2:
                            continue

                    # 3 permutations
                    perms = [
                        (na, va, nb, vb, nc, vc),
                        (na, va, nc, vc, nb, vb),
                        (nb, vb, nc, vc, na, va),
                    ]
                    for pa, pva, pb, pvb, pc, pvc in perms:
                        ops = ternary_ops(pa, pva, pb, pvb, pc, pvc)
                        total_trials += len(ops)

                        for val, expr in ops:
                            for t_name, t_val in targets.items():
                                if t_val == 0:
                                    continue
                                rel_err = abs(val - t_val) / abs(t_val)
                                if rel_err < threshold:
                                    origins = set(filter(None, [
                                        origin_pn(pa), origin_pn(pb), origin_pn(pc)
                                    ]))
                                    matches.append({
                                        "target": t_name,
                                        "target_val": t_val,
                                        "formula": expr,
                                        "formula_val": val,
                                        "error": rel_err,
                                        "error_pct": rel_err * 100,
                                        "depth": 3,
                                        "origins": origins,
                                    })

    # Remove duplicates
    seen = set()
    unique = []
    for m in matches:
        key = (m["target"], m["formula"])
        if key not in seen:
            seen.add(key)
            unique.append(m)

    # Add non-triviality scores
    for m in unique:
        m["nontrivial"] = triviality_score(
            m["formula"], m["target"], m["target_val"], m["formula_val"]
        )

    # Sort by error
    unique.sort(key=lambda x: x["error_pct"])

    return unique, total_trials


# ─────────────────────────────────────────
# Texas Sharpshooter Test
# ─────────────────────────────────────────
def texas_sharpshooter(matches, total_trials, n_random=5000):
    """Bonferroni p-value based test."""
    rng = np.random.default_rng(42)

    # Estimate random hit probability for each target
    target_hit_probs = {}
    unique_targets = {m["target"]: m["target_val"] for m in matches}

    for t_name, t_val in unique_targets.items():
        if t_val == 0:
            continue
        hits = 0
        for _ in range(n_random):
            a = rng.uniform(1, 500)
            b = rng.uniform(1, 500)
            test_vals = [a + b, a - b, a * b]
            if b != 0:
                test_vals.append(a / b)
            if a > 0 and abs(b) < 20:
                try:
                    test_vals.append(a ** b)
                except (OverflowError, ValueError):
                    pass
            if a * b > 0:
                test_vals.append(np.sqrt(a * b))

            for v in test_vals:
                if isinstance(v, (int, float)) and np.isfinite(v) and t_val != 0:
                    if abs(v - t_val) / abs(t_val) < 0.01:
                        hits += 1
                        break

        target_hit_probs[t_name] = max(hits / n_random, 1e-6)

    # Bonferroni correction
    results = []
    n_significant = 0
    for m in matches:
        p_single = target_hit_probs.get(m["target"], 0.01)
        precision_factor = m["error_pct"] / 0.1 if m["error_pct"] > 0 else 0.01
        p_adjusted = min(1.0, p_single * precision_factor * total_trials)

        if p_adjusted < 0.01:
            verdict = "Structural"
            n_significant += 1
        elif p_adjusted < 0.05:
            verdict = "Weak evidence"
            n_significant += 1
        else:
            verdict = "Possibly chance"

        m_copy = dict(m)
        m_copy["p_value"] = p_adjusted
        m_copy["verdict"] = verdict
        results.append(m_copy)

    return results, n_significant


# ─────────────────────────────────────────
# Perfect Number Contribution Analysis
# ─────────────────────────────────────────
def contribution_analysis(matches):
    """Analyze which perfect numbers appear most frequently."""
    counter = {}
    for p in PERFECT_NUMBERS:
        counter[p] = {"total": 0, "nontrivial": 0, "best_err": float("inf")}

    for m in matches:
        for p in m.get("origins", set()):
            if p in counter:
                counter[p]["total"] += 1
                if m.get("nontrivial", 0) >= 4:
                    counter[p]["nontrivial"] += 1
                counter[p]["best_err"] = min(counter[p]["best_err"], m["error_pct"])

    return counter


# ─────────────────────────────────────────
# Cross-relationship Analysis
# ─────────────────────────────────────────
def cross_analysis(matches):
    """Cross-relationships connecting different perfect numbers."""
    cross_matches = []
    for m in matches:
        origins = m.get("origins", set())
        if len(origins) >= 2:
            cross_matches.append(m)
    cross_matches.sort(key=lambda x: x["error_pct"])
    return cross_matches


# ─────────────────────────────────────────
# Output
# ─────────────────────────────────────────
def print_results(matches, total_trials, targets, depth, cross_only,
                  threshold, texas=False):
    """ASCII result output."""

    n_atoms = len(ATOMS)
    n_pn = len(PERFECT_NUMBERS)

    print()
    print("=" * 65)
    print("  Perfect Number Engine v1.0")
    print(f"  Perfect numbers: {n_pn}, Atoms: {n_atoms}, Targets: {len(targets)}")
    print(f"  Operation combinations: ~{total_trials:,}, Depth: {depth}, Threshold: {threshold * 100}%")
    mode = "Cross (P_i x P_j) only" if cross_only else "Full"
    print(f"  Mode: {mode}")
    print("=" * 65)

    if not matches:
        print()
        print("  No discoveries.")
        print("=" * 65)
        return

    # ── Discovery table (sorted by error) ──
    # Show non-trivial first
    nontrivial = [m for m in matches if m.get("nontrivial", 0) >= 3]
    trivial = [m for m in matches if m.get("nontrivial", 0) < 3]

    print()
    print(f"  Non-trivial discoveries: {len(nontrivial)}, Trivial: {len(trivial)}")
    print()

    if nontrivial:
        print("  --- Non-trivial discoveries (by error) ---")
        print(f"  {'Error%':>8} | {'Formula':<35} | {'Value':>12} | {'Target':<12} | NT")
        print("  " + "-" * 78)
        for m in nontrivial[:40]:
            err_str = f"{m['error_pct']:.4f}"
            val_str = f"{m['formula_val']:.5f}"
            formula = m["formula"]
            if len(formula) > 35:
                formula = formula[:32] + "..."
            nt = m.get("nontrivial", 0)

            if m["error_pct"] < 0.001:
                star = "**"
            elif m["error_pct"] < 0.01:
                star = "* "
            elif m["error_pct"] < 0.1:
                star = ". "
            else:
                star = "  "

            print(f"  {star}{err_str:>6} | {formula:<35} | {val_str:>12} | "
                  f"{m['target']:<12} | {nt}")
        print("  " + "-" * 78)

    # ── Perfect number contributions ──
    contrib = contribution_analysis(matches)
    print()
    print("  --- Contributions by perfect number ---")
    print(f"  {'Perfect#':>8} | {'Total':>8} | {'Nontrivial':>8} | {'Min Error%':>10}")
    print("  " + "-" * 45)
    for p in sorted(contrib.keys()):
        c = contrib[p]
        best = f"{c['best_err']:.4f}" if c['best_err'] < float("inf") else "-"
        print(f"  {p:>8} | {c['total']:>8} | {c['nontrivial']:>8} | {best:>10}")
    print("  " + "-" * 45)

    # ── Cross-relationships ──
    cross = cross_analysis(matches)
    if cross:
        print()
        print(f"  --- Cross-relationships (P_i x P_j): {len(cross)} ---")
        for m in cross[:15]:
            origins_str = " x ".join(f"P{p}" for p in sorted(m["origins"]))
            print(f"    {m['error_pct']:>7.4f}% | {m['formula']:<35} -> "
                  f"{m['target']} [{origins_str}]")

    # ── Texas sharpshooter test ──
    if texas and matches:
        print()
        print("  --- Texas Sharpshooter Test ---")
        texas_results, n_sig = texas_sharpshooter(matches, total_trials)
        n_structural = sum(1 for r in texas_results if r["verdict"] == "Structural")
        n_weak = sum(1 for r in texas_results if r["verdict"] == "Weak evidence")
        n_chance = sum(1 for r in texas_results if r["verdict"] == "Possibly chance")

        print(f"  Total attempts: {total_trials:,}, "
              f"Discoveries within {threshold * 100}%: {len(matches)}")
        print(f"  Bonferroni significant: {n_sig}/{len(matches)} (p < 0.05)")
        print(f"   - Structural (p<0.01): {n_structural}")
        print(f"   - Weak evidence (p<0.05): {n_weak}")
        print(f"   - Possibly chance (p>=0.05): {n_chance}")

        structural = [r for r in texas_results if r["verdict"] == "Structural"]
        if structural:
            structural.sort(key=lambda x: x["p_value"])
            print()
            print("  Structural discoveries (p < 0.01):")
            for r in structural[:10]:
                print(f"    p={r['p_value']:.4f} | {r['formula']:<35} -> "
                      f"{r['target']} (err {r['error_pct']:.4f}%)")

    print()
    print("=" * 65)


def save_results(matches, total_trials, targets, threshold, depth):
    """Save results to results/ folder."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path = os.path.join(RESULTS_DIR, "perfect_number_discovery.md")

    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n# Perfect Number Divisor Function Search [{now}]\n\n")
        f.write(f"Perfect numbers {len(PERFECT_NUMBERS)}, Atoms {len(ATOMS)}, "
                f"Targets {len(targets)}, "
                f"Attempts {total_trials:,}, "
                f"Discoveries {len(matches)}, "
                f"Threshold {threshold * 100}%\n\n")

        nontrivial = [m for m in matches if m.get("nontrivial", 0) >= 3]

        f.write("| Error% | Formula | Value | Target | NT |\n")
        f.write("|-------|------|-----|------|----|\n")
        for m in nontrivial[:30]:
            f.write(f"| {m['error_pct']:.4f} | {m['formula']} | "
                    f"{m['formula_val']:.6f} | {m['target']} | "
                    f"{m.get('nontrivial', 0)} |\n")

        # Cross-relationships
        cross = cross_analysis(matches)
        if cross:
            f.write(f"\n## Cross-relationships ({len(cross)})\n\n")
            for m in cross[:15]:
                origins_str = " x ".join(f"P{p}" for p in sorted(m["origins"]))
                f.write(f"- {m['error_pct']:.4f}% | {m['formula']} -> "
                        f"{m['target']} [{origins_str}]\n")

        f.write("\n---\n")

    return path


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Perfect Number Divisor Function Engine — Search for physical constants using sigma, tau, phi combinations",
    )
    parser.add_argument("--target", type=float, default=None,
                        help="Search for formulas that produce specific value")
    parser.add_argument("--depth", type=int, default=2, choices=[2, 3],
                        help="Combination depth (default 2, 3 is slow)")
    parser.add_argument("--cross", action="store_true",
                        help="Search only cross-combinations of different perfect numbers")
    parser.add_argument("--threshold", type=float, default=0.01,
                        help="Relative error threshold (default 0.01 = 1%%)")
    parser.add_argument("--texas", action="store_true",
                        help="Include Texas sharpshooter test")
    parser.add_argument("--top", type=int, default=None,
                        help="Show only top N results")

    args = parser.parse_args()

    # Determine targets
    if args.target is not None:
        targets = {f"target={args.target}": args.target}
    else:
        targets = PHYSICS_TARGETS

    # Search
    matches, total_trials = search(
        targets=targets,
        depth=args.depth,
        cross_only=args.cross,
        threshold=args.threshold,
    )

    # Filter top N
    if args.top and len(matches) > args.top:
        matches = matches[:args.top]

    # Output
    print_results(
        matches,
        total_trials,
        targets=targets,
        depth=args.depth,
        cross_only=args.cross,
        threshold=args.threshold,
        texas=args.texas,
    )

    # Save
    path = save_results(matches, total_trials, targets, args.threshold, args.depth)
    print(f"  -> Saved to results/: {path}")
    print()


if __name__ == "__main__":
    main()