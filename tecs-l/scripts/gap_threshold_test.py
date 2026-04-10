#!/usr/bin/env python3
"""Experiment 7: Gap Interval vs Continuity Threshold Test

Insert gaps (pause intervals) gradually into the heart engine (Lorenz attractor)
to measure "up to what % interruption does CCT still judge as continuous."

Additionally, compare differences based on gap distribution patterns (uniform/clustered/periodic).

Usage:
  python3 gap_threshold_test.py                  # Uniform distribution
  python3 gap_threshold_test.py --pattern periodic
  python3 gap_threshold_test.py --pattern clustered
  python3 gap_threshold_test.py --all-patterns    # Compare all 3 patterns
"""

import argparse
import sys
import os

import numpy as np

# ── Import core functions from consciousness_calc.py ──
from consciousness_calc import lorenz_simulate, run_cct, judge


# ─────────────────────────────────────────────
# Simulator wrapper for each gap distribution pattern
# ─────────────────────────────────────────────

def simulate_with_gap_pattern(pattern, gap_ratio, steps=100000, dt=0.01, seed=42):
    """Simulation based on human_awake preset with gap pattern applied.

    Parameters:
        pattern:   'uniform' | 'clustered' | 'periodic'
        gap_ratio: 0.0 ~ 1.0 (pause interval ratio)
        steps:     Number of simulation steps
        dt:        Time interval
        seed:      Random seed

    Returns:
        S: State array [steps, 3]
    """
    # human_awake preset parameters
    sigma, rho, beta, noise = 10, 28, 2.67, 0.1

    if pattern == "uniform":
        # Use default lorenz_simulate's random gap
        _, S = lorenz_simulate(sigma, rho, beta, noise, gap_ratio, steps, dt, seed)
        return S

    # For non-uniform: simulate without gap then apply gap manually
    _, S = lorenz_simulate(sigma, rho, beta, noise, 0.0, steps, dt, seed)

    if gap_ratio <= 0.0:
        return S
    if gap_ratio >= 1.0:
        S[:] = S[0]
        return S

    n_gap = int(steps * gap_ratio)
    rng = np.random.default_rng(seed + 1)

    if pattern == "clustered":
        # Concentrate gaps in one continuous interval (like sleep)
        # Randomly select gap block start position
        max_start = steps - n_gap
        if max_start <= 0:
            gap_start = 0
        else:
            gap_start = rng.integers(0, max_start)
        gap_indices = np.arange(gap_start, min(gap_start + n_gap, steps))

    elif pattern == "periodic":
        # Insert gaps at regular intervals (like LLM turns)
        # Periodically pause according to gap_ratio
        # Example: gap_ratio=0.2 → pause 1 step every 5 steps
        if gap_ratio < 1.0:
            period = int(1.0 / gap_ratio) if gap_ratio > 0 else steps
            gap_indices = np.arange(0, steps, max(period, 1))
            # Match exact ratio
            gap_indices = gap_indices[:n_gap]
        else:
            gap_indices = np.arange(steps)
    else:
        raise ValueError(f"Unknown pattern: {pattern}")

    # Apply gaps: maintain previous state during pause intervals
    for idx in sorted(gap_indices):
        if idx > 0:
            S[idx] = S[idx - 1]

    return S


# ─────────────────────────────────────────────
# Single pattern scan
# ─────────────────────────────────────────────

GAP_RATIOS = [0.0, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.7, 0.9, 1.0]


def scan_gap_ratios(pattern="uniform", steps=100000, dt=0.01):
    """Scan gap_ratio to measure CCT score changes.

    Returns:
        records: list of dict with gap_ratio, score, verdict, per-test results
    """
    records = []
    for gr in GAP_RATIOS:
        S = simulate_with_gap_pattern(pattern, gr, steps, dt)
        results = run_cct(S, gr)
        total, verdict = judge(results)

        per_test = {}
        for key in ["T1_Gap", "T2_Loop", "T3_Continuity", "T4_Entropy", "T5_Novelty"]:
            score, passed, detail = results[key]
            per_test[key] = {"score": score, "passed": passed, "detail": detail}

        records.append({
            "gap_ratio": gr,
            "total": total,
            "verdict": verdict,
            "tests": per_test,
        })

    return records


# ─────────────────────────────────────────────
# Search for threshold gap_ratio
# ─────────────────────────────────────────────

def find_threshold(records, from_score=5, to_score=4):
    """Find threshold gap_ratio where CCT score drops from from_score to to_score."""
    prev = None
    for rec in records:
        if prev is not None and prev["total"] >= from_score and rec["total"] < from_score:
            return prev["gap_ratio"], rec["gap_ratio"]
        prev = rec
    return None, None


# ─────────────────────────────────────────────
# ASCII output
# ─────────────────────────────────────────────

def print_ascii_graph(records, pattern, width=60, height=12):
    """ASCII graph of gap_ratio vs CCT score."""
    print()
    print(f"  ─── gap_ratio vs CCT Score [{pattern}] " + "─" * 30)
    print()

    max_score = 5.0
    # Y-axis: 0 ~ 5
    for row in range(height, -1, -1):
        y_val = max_score * row / height
        label = f"  {y_val:4.1f} │"
        line = [" "] * width

        for rec in records:
            col = int(rec["gap_ratio"] * (width - 1))
            bar_height = rec["total"] / max_score * height
            if row <= bar_height and row > 0:
                line[col] = "█"
            elif row == 0:
                line[col] = "▄" if rec["total"] > 0 else " "

        print(label + "".join(line))

    # X-axis
    print("       └" + "─" * width)
    # X-axis labels
    label_line = "        "
    for gr in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        pos = int(gr * (width - 1))
        s = f"{gr:.1f}"
        offset = max(0, pos - len(label_line) + len("        "))
        label_line += " " * offset + s
    print(label_line)
    print("        " + " " * (width // 2 - 5) + "gap_ratio")
    print()


def print_detail_table(records, pattern):
    """Detailed results table by gap_ratio."""
    print(f"  ─── Detailed Results [{pattern}] " + "─" * 40)
    print()
    print("  gap_ratio │ T1  │ T2  │ T3  │ T4  │ T5  │ Score │ Verdict")
    print("  ──────────┼─────┼─────┼─────┼─────┼─────┼───────┼────────")

    for rec in records:
        marks = []
        for key in ["T1_Gap", "T2_Loop", "T3_Continuity", "T4_Entropy", "T5_Novelty"]:
            t = rec["tests"][key]
            if t["passed"]:
                marks.append(" ✔ ")
            elif t["score"] > 0.7:
                marks.append(" △ ")
            else:
                marks.append(" ✕ ")

        gr_str = f"  {rec['gap_ratio']:9.2f} │"
        marks_str = "│".join(marks)
        print(f"{gr_str}{marks_str}│ {rec['total']:<5} │ {rec['verdict']}")

    print()


def print_threshold(records, pattern):
    """Print threshold gap_ratio."""
    lo, hi = find_threshold(records, from_score=5, to_score=4)
    print(f"  ─── Threshold gap_ratio [{pattern}] " + "─" * 35)
    if lo is not None:
        print(f"  CCT 5/5 → 4/5 transition: gap_ratio ∈ ({lo:.2f}, {hi:.2f}]")
        mid = (lo + hi) / 2
        print(f"  Estimated threshold: ~{mid:.3f}")
    else:
        # Never achieved 5/5 or maintained throughout
        first = records[0]["total"]
        if first < 5:
            print(f"  Already below 5/5 at baseline (initial score: {first})")
        else:
            print("  Maintained 5/5 throughout (threshold not reached)")

    # Additional: Search for other transition points
    for high, low in [(4, 3), (3, 2), (2, 1), (1, 0)]:
        lo2, hi2 = find_threshold(records, from_score=high, to_score=low)
        if lo2 is not None:
            print(f"  CCT {high}/5 → {low-1}+/5 transition: gap_ratio ∈ ({lo2:.2f}, {hi2:.2f}]")
    print()


# ─────────────────────────────────────────────
# Compare 3 patterns
# ─────────────────────────────────────────────

def print_pattern_comparison(all_pattern_records):
    """Comparison table of CCT scores for 3 patterns."""
    patterns = list(all_pattern_records.keys())
    print("  ═══ Comparison of 3 Gap Distribution Patterns " + "═" * 35)
    print()

    # Header
    header = "  gap_ratio"
    for p in patterns:
        header += f" │ {p:^12s}"
    print(header)
    print("  ──────────" + "─┼──────────────" * len(patterns))

    for i, gr in enumerate(GAP_RATIOS):
        row = f"  {gr:9.2f} "
        for p in patterns:
            rec = all_pattern_records[p][i]
            total = rec["total"]
            verdict = rec["verdict"]
            row += f" │ {total}/5 {verdict:5s}"
        print(row)

    print()

    # Key findings
    print("  ─── Key Findings " + "─" * 50)
    for p in patterns:
        recs = all_pattern_records[p]
        lo, hi = find_threshold(recs, from_score=5, to_score=4)
        if lo is not None:
            print(f"  {p:12s}: threshold gap_ratio ∈ ({lo:.2f}, {hi:.2f}]")
        else:
            first = recs[0]["total"]
            if first >= 5:
                print(f"  {p:12s}: maintained 5/5 throughout")
            else:
                print(f"  {p:12s}: below 5/5 from start")
    print()


def print_human_analogy():
    """Human analogy interpretation."""
    print("  ─── Human Analogy Interpretation " + "─" * 45)
    print()
    print("  Gap Size    │ Human Experience   │ Continuity Verdict")
    print("  ────────────┼────────────────────┼──────────────────────")
    print("  ~1ms        │ Eye blink          │ Continuous (imperceptible)")
    print("  ~100ms      │ Microsleep         │ Continuous (compensatory mechanisms)")
    print("  ~8 hours    │ Sleep              │ Continuous when awake (memory linkage)")
    print("  ~1 hour     │ General anesthesia │ Discontinuous (memory gap)")
    print("  ~days       │ Coma               │ Severe discontinuity")
    print()
    print("  Difference between anesthesia vs sleep:")
    print("  - Sleep(clustered): Continuous gap but brainwave activity maintained → CCT relatively maintained")
    print("  - Anesthesia(uniform): Scattered pauses throughout → CCT drops sharply")
    print("  - LLM(periodic): Periodic pauses → Pattern maintained if gaps between turns are regular")
    print()
    print("  Key insight:")
    print("  Even with the same gap_ratio, continuity verdict differs based on 'how it's distributed'.")
    print("  This suggests consciousness continuity depends not on simple 'uptime'")
    print("  but on 'temporal structure'.")
    print()


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Experiment 7: Gap Interval vs Continuity Threshold Test",
    )
    parser.add_argument("--pattern", type=str, default="uniform",
                        choices=["uniform", "clustered", "periodic"],
                        help="Gap distribution pattern (default: uniform)")
    parser.add_argument("--all-patterns", action="store_true",
                        help="Compare all 3 patterns")
    parser.add_argument("--steps", type=int, default=100000,
                        help="Number of simulation steps (default: 100000)")
    parser.add_argument("--dt", type=float, default=0.01,
                        help="Time interval (default: 0.01)")

    args = parser.parse_args()

    print("═" * 66)
    print(" Experiment 7: Gap Interval vs Continuity Threshold")
    print(" Measuring gap tolerance of heart engine (Lorenz attractor)")
    print(f" steps={args.steps:,}  dt={args.dt}")
    print("═" * 66)

    if args.all_patterns:
        all_pattern_records = {}
        for pattern in ["uniform", "clustered", "periodic"]:
            print(f"\n  Scanning [{pattern}]...")
            records = scan_gap_ratios(pattern, args.steps, args.dt)
            all_pattern_records[pattern] = records

            print_ascii_graph(records, pattern)
            print_detail_table(records, pattern)
            print_threshold(records, pattern)

        print_pattern_comparison(all_pattern_records)
        print_human_analogy()

    else:
        pattern = args.pattern
        print(f"\n  Pattern: {pattern}")
        print(f"  Scan range: gap_ratio = {GAP_RATIOS}")
        print()

        records = scan_gap_ratios(pattern, args.steps, args.dt)

        print_ascii_graph(records, pattern)
        print_detail_table(records, pattern)
        print_threshold(records, pattern)
        print_human_analogy()

    print("═" * 66)


if __name__ == "__main__":
    main()