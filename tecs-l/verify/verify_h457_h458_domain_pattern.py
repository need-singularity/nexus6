#!/usr/bin/env python3
"""H-CX-457: Statistical Mechanics isolation
   H-CX-458: Quantum Mechanics selective participation

Verifies:
  1. Per-domain expressiveness (how many of 92 TARGETS reachable within 0.1%)
  2. Q domain selectivity: does it reach info-theoretic targets but not geometric?
  3. Inter-domain distance matrix (shared reachable targets)
"""

import sys
import os
import numpy as np
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convergence_engine import DOMAINS, TARGETS, binary_ops


def compute_reachable(domain_key, threshold_pct=0.1):
    """Compute which TARGETS are reachable using depth-1 binary ops on domain constants."""
    consts = DOMAINS[domain_key]["constants"]
    items = list(consts.items())

    reachable_values = set()  # store (target_name, value)

    # First: raw constants themselves
    generated = []
    for name, val in items:
        generated.append((val, name))

    # Depth 1: all pairs
    for i in range(len(items)):
        for j in range(i, len(items)):
            na, va = items[i]
            nb, vb = items[j]
            generated.extend(binary_ops(na, va, nb, vb))

    # Match against targets
    matched = {}
    for tname, tval in TARGETS.items():
        if tval == 0:
            continue
        for gval, gexpr in generated:
            rel_err = abs(gval - tval) / abs(tval) * 100
            if rel_err < threshold_pct:
                if tname not in matched or rel_err < matched[tname][1]:
                    matched[tname] = (gexpr, rel_err)

    return matched


def categorize_target(tname):
    """Categorize a target as info-theoretic, geometric, number-theoretic, or other."""
    info_keys = {"ln(2)", "ln(3)", "ln(10)", "e", "1/e", "e^2",
                 "GZ_width", "GZ_center", "GZ_upper", "GZ_lower",
                 "gamma_EM", "zeta(3)", "Catalan_G", "Khinchin"}
    geom_keys = {"pi", "pi/2", "pi/3", "pi/4", "pi/6", "pi^2/6",
                 "sqrt(2)", "sqrt(3)", "sqrt(5)", "phi_gold"}

    if tname in info_keys:
        return "INFO"
    if tname in geom_keys:
        return "GEOM"

    # Check if integer
    try:
        v = float(tname)
        if v == int(v):
            return "INT"
    except ValueError:
        pass

    # Check fraction
    if "/" in tname and tname.count("/") == 1:
        parts = tname.split("/")
        try:
            int(parts[0]); int(parts[1])
            return "FRAC"
        except ValueError:
            pass

    # Physics
    phys_keys = {"1/alpha", "alpha", "alpha_s", "sin2_thetaW", "T_CMB",
                 "Omega_DE", "Omega_DM", "Omega_b", "m_p/m_e", "m_mu/m_e"}
    if tname in phys_keys:
        return "PHYS"

    # Project
    proj_keys = {"meta_fixed", "compass_upper"}
    if tname in proj_keys:
        return "PROJ"

    return "OTHER"


def main():
    print("=" * 70)
    print("H-CX-457 / H-CX-458: Domain Expressiveness & Selectivity Analysis")
    print("=" * 70)
    print(f"\nTotal TARGETS: {len(TARGETS)}")
    print(f"Threshold: 0.1% relative error")
    print(f"Method: Depth-1 binary ops on pairs within each domain\n")

    domain_keys = sorted(DOMAINS.keys())
    domain_matched = {}

    # ═══ TASK 1: Per-domain expressiveness ═══
    print("-" * 70)
    print("TASK 1: Per-Domain Expressiveness Ranking")
    print("-" * 70)

    for dk in domain_keys:
        matched = compute_reachable(dk)
        domain_matched[dk] = matched

    # Sort by count
    ranking = sorted(domain_matched.items(), key=lambda x: len(x[1]), reverse=True)

    print(f"\n{'Rank':<5} {'Domain':<5} {'Name':<25} {'Reach':>6} {'%':>7}")
    print("-" * 52)
    for rank, (dk, matched) in enumerate(ranking, 1):
        pct = len(matched) / len(TARGETS) * 100
        print(f"{rank:<5} {dk:<5} {DOMAINS[dk]['name']:<25} {len(matched):>6} {pct:>6.1f}%")

    print(f"\n{'':5} {'Total unique targets':<30} {len(TARGETS):>6}")

    # Show what each domain can reach
    print("\n" + "-" * 70)
    print("Detailed: targets reached by each domain")
    print("-" * 70)
    for dk, matched in ranking:
        tnames = sorted(matched.keys())
        print(f"\n  {dk} ({DOMAINS[dk]['name']}, {len(matched)} targets):")
        # group by category
        by_cat = {}
        for tn in tnames:
            cat = categorize_target(tn)
            by_cat.setdefault(cat, []).append(tn)
        for cat in ["INFO", "GEOM", "INT", "FRAC", "PHYS", "PROJ", "OTHER"]:
            if cat in by_cat:
                items_str = ", ".join(by_cat[cat])
                print(f"    [{cat:>5}] {items_str}")

    # ═══ TASK 2: Q domain selectivity ═══
    print("\n" + "=" * 70)
    print("TASK 2: Q (Quantum Mechanics) Selectivity Analysis")
    print("=" * 70)

    q_matched = domain_matched["Q"]
    q_by_cat = {}
    for tn in q_matched:
        cat = categorize_target(tn)
        q_by_cat.setdefault(cat, []).append(tn)

    info_targets = {tn for tn in TARGETS if categorize_target(tn) == "INFO"}
    geom_targets = {tn for tn in TARGETS if categorize_target(tn) == "GEOM"}
    int_targets  = {tn for tn in TARGETS if categorize_target(tn) == "INT"}
    frac_targets = {tn for tn in TARGETS if categorize_target(tn) == "FRAC"}
    phys_targets = {tn for tn in TARGETS if categorize_target(tn) == "PHYS"}

    print(f"\n  Category        Total   Q-reach   Rate")
    print(f"  {'-'*45}")
    for cat_name, cat_set in [("INFO-THEORETIC", info_targets),
                               ("GEOMETRIC", geom_targets),
                               ("INTEGER", int_targets),
                               ("FRACTION", frac_targets),
                               ("PHYSICS", phys_targets)]:
        reached = cat_set & set(q_matched.keys())
        rate = len(reached) / len(cat_set) * 100 if cat_set else 0
        print(f"  {cat_name:<16} {len(cat_set):>5}   {len(reached):>5}   {rate:>5.1f}%")
        if reached:
            for tn in sorted(reached):
                expr, err = q_matched[tn]
                print(f"    -> {tn:<15} = {expr:<35} (err={err:.4f}%)")

    # Selectivity ratio
    info_rate = len(info_targets & set(q_matched.keys())) / max(len(info_targets), 1)
    geom_rate = len(geom_targets & set(q_matched.keys())) / max(len(geom_targets), 1)
    print(f"\n  Selectivity: INFO rate / GEOM rate = ", end="")
    if geom_rate > 0:
        print(f"{info_rate/geom_rate:.2f}x")
    else:
        print(f"INF (GEOM rate = 0)")
    print(f"  Q selectively reaches info but not geometric? ", end="")
    print("YES" if info_rate > geom_rate else "NO")

    # ═══ TASK 3: Inter-domain distance matrix ═══
    print("\n" + "=" * 70)
    print("TASK 3: Inter-Domain Overlap Matrix (shared reachable targets)")
    print("=" * 70)

    # Build sets
    domain_sets = {dk: set(domain_matched[dk].keys()) for dk in domain_keys}

    # Header
    print(f"\n{'':>5}", end="")
    for dk in domain_keys:
        print(f" {dk:>5}", end="")
    print(f" {'Self':>5}")
    print("  " + "-" * (6 * (len(domain_keys) + 1) + 3))

    for d1 in domain_keys:
        print(f"  {d1:<3}", end="")
        for d2 in domain_keys:
            if d1 == d2:
                print(f" {'--':>5}", end="")
            else:
                shared = len(domain_sets[d1] & domain_sets[d2])
                print(f" {shared:>5}", end="")
        print(f" {len(domain_sets[d1]):>5}")

    # Isolation score: domain with fewest shared targets
    print(f"\nIsolation scores (lower = more isolated):")
    print(f"  {'Domain':<5} {'Max overlap':>12} {'Avg overlap':>12} {'Self':>6}")
    print(f"  {'-'*38}")
    for dk in domain_keys:
        overlaps = []
        for dk2 in domain_keys:
            if dk != dk2:
                overlaps.append(len(domain_sets[dk] & domain_sets[dk2]))
        max_ov = max(overlaps) if overlaps else 0
        avg_ov = np.mean(overlaps) if overlaps else 0
        print(f"  {dk:<5} {max_ov:>12} {avg_ov:>12.1f} {len(domain_sets[dk]):>6}")

    # ═══ SUMMARY ═══
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    # H-CX-457: Is S (Statistical Mechanics) isolated?
    s_overlaps = [len(domain_sets["S"] & domain_sets[dk]) for dk in domain_keys if dk != "S"]
    s_max_overlap = max(s_overlaps)
    s_avg_overlap = np.mean(s_overlaps)
    all_avg_overlaps = []
    for dk in domain_keys:
        ovs = [len(domain_sets[dk] & domain_sets[dk2]) for dk2 in domain_keys if dk != dk2]
        all_avg_overlaps.append(np.mean(ovs))
    overall_avg = np.mean(all_avg_overlaps)

    print(f"\n  H-CX-457 (Statistical Mechanics Isolation):")
    print(f"    S expressiveness:    {len(domain_sets['S'])} / {len(TARGETS)} targets")
    print(f"    S avg overlap:       {s_avg_overlap:.1f} (overall avg: {overall_avg:.1f})")
    print(f"    S max overlap:       {s_max_overlap}")
    is_isolated = s_avg_overlap < overall_avg
    print(f"    Isolated?            {'YES' if is_isolated else 'NO'} (avg overlap {'<' if is_isolated else '>='} overall avg)")

    # H-CX-458: Does Q selectively reach info targets?
    print(f"\n  H-CX-458 (Quantum Mechanics Selective Participation):")
    print(f"    Q expressiveness:    {len(domain_sets['Q'])} / {len(TARGETS)} targets")
    print(f"    INFO reach rate:     {info_rate*100:.1f}%")
    print(f"    GEOM reach rate:     {geom_rate*100:.1f}%")
    if geom_rate > 0:
        print(f"    Selectivity ratio:   {info_rate/geom_rate:.2f}x")
    else:
        print(f"    Selectivity ratio:   INF")
    print(f"    Selective?           {'YES' if info_rate > geom_rate else 'NO'}")


if __name__ == "__main__":
    main()
