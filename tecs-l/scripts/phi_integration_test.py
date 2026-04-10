#!/usr/bin/env python3
"""Integrated Information (Phi) Test — 6th CCT Test Candidate

Calculates simplified Phi from IIT (Integrated Information Theory) to
resolve epilepsy inconsistency that cannot be distinguished by 5 CCT tests.

Phi_approx = MI(x,y,z) - (MI(x,y) + MI(y,z) + MI(x,z)) / 3

Where MI is mutual information, x=sensory, y=prediction, z=memory.
"Pure integration surplus" from 3-variable total integration minus average pairwise information.

Usage:
  python3 phi_integration_test.py
  python3 phi_integration_test.py --steps 50000
"""

import argparse
import sys
import os

import numpy as np

# Import core functions/constants from consciousness_calc.py
from consciousness_calc import lorenz_simulate, run_cct, PRESETS, judge


# ─────────────────────────────────────────────
# Epilepsy Preset (derived from I=0.15)
# ─────────────────────────────────────────────

EPILEPSY_PRESET = {
    "sigma": 8.5,       # 10 * (1 - 0.15)
    "rho": 25.9,        # 28 * (1 - 0.15/2)
    "beta": 2.67,
    "noise": 0.255,     # 0.3 * (1 - 0.15)
    "gap_ratio": 0.0,
    "description": "Epileptic brain (I=0.15)",
}


# ─────────────────────────────────────────────
# MI Calculation: Histogram binning
# ─────────────────────────────────────────────

def entropy_1d(x, bins=30):
    """1D Shannon entropy (nats)."""
    hist, edges = np.histogram(x, bins=bins, density=False)
    probs = hist / hist.sum()
    probs = probs[probs > 0]
    return -np.sum(probs * np.log(probs + 1e-15))


def entropy_2d(x, y, bins=30):
    """2D joint entropy."""
    hist, _, _ = np.histogram2d(x, y, bins=bins, density=False)
    probs = hist.flatten() / hist.sum()
    probs = probs[probs > 0]
    return -np.sum(probs * np.log(probs + 1e-15))


def entropy_3d(x, y, z, bins=20):
    """3D joint entropy."""
    data = np.column_stack([x, y, z])
    hist, _ = np.histogramdd(data, bins=bins, density=False)
    probs = hist.flatten() / hist.sum()
    probs = probs[probs > 0]
    return -np.sum(probs * np.log(probs + 1e-15))


def mutual_info_2d(a, b, bins=30):
    """MI(a, b) = H(a) + H(b) - H(a, b)."""
    return entropy_1d(a, bins) + entropy_1d(b, bins) - entropy_2d(a, b, bins)


def mutual_info_3d(x, y, z, bins=20):
    """MI(x, y, z) = H(x) + H(y) + H(z) - H(x, y, z).

    3-variable total mutual information (multivariate MI).
    """
    return (entropy_1d(x, bins) + entropy_1d(y, bins) + entropy_1d(z, bins)
            - entropy_3d(x, y, z, bins))


# ─────────────────────────────────────────────
# Phi_approx Calculation
# ─────────────────────────────────────────────

def phi_approx(x, y, z, bins_2d=30, bins_3d=20):
    """Simplified integrated information Phi.

    Phi = MI(x,y,z) - (MI(x,y) + MI(y,z) + MI(x,z)) / 3

    Positive: 3-variable integration greater than pairwise information (true integration)
    Near 0: No integration surplus
    Negative: Pairwise information greater than 3-variable integration (separated system)
    """
    mi3 = mutual_info_3d(x, y, z, bins=bins_3d)
    mi_xy = mutual_info_2d(x, y, bins=bins_2d)
    mi_yz = mutual_info_2d(y, z, bins=bins_2d)
    mi_xz = mutual_info_2d(x, z, bins=bins_2d)
    pairwise_avg = (mi_xy + mi_yz + mi_xz) / 3.0
    return mi3 - pairwise_avg


def phi_timeseries(S, window=2000, stride=500, bins_2d=30, bins_3d=20):
    """Calculate Phi time series.

    Track Phi_approx over time with sliding window.

    Returns:
        t_centers: Center time index for each window
        phis: Array of Phi values
    """
    n = len(S)
    t_centers = []
    phis = []

    start = 0
    while start + window <= n:
        seg = S[start:start + window]
        x, y, z = seg[:, 0], seg[:, 1], seg[:, 2]
        phi = phi_approx(x, y, z, bins_2d=bins_2d, bins_3d=bins_3d)
        t_centers.append(start + window // 2)
        phis.append(phi)
        start += stride

    return np.array(t_centers), np.array(phis)


# ─────────────────────────────────────────────
# Phi-based T6 Test
# ─────────────────────────────────────────────

def test_phi(S, phi_threshold=0.3, window=2000, stride=500):
    """T6 Phi Test: Ratio of intervals where integrated information exceeds threshold.

    Parameters:
        S: State array [steps, 3]
        phi_threshold: Phi passing threshold
        window: Sliding window size
        stride: Window movement interval

    Returns:
        (score, passed, detail) tuple
    """
    t_centers, phis = phi_timeseries(S, window=window, stride=stride)

    if len(phis) == 0:
        return 0.0, False, "Insufficient data"

    mean_phi = np.mean(phis)
    std_phi = np.std(phis)
    above = np.sum(phis >= phi_threshold)
    ratio = above / len(phis)

    passed = ratio >= 0.5 and mean_phi >= phi_threshold
    score = min(1.0, mean_phi / phi_threshold) if phi_threshold > 0 else 0.0

    detail = f"Phi_mean={mean_phi:.3f}, std={std_phi:.3f}, above_thresh={ratio:.1%}"
    if passed:
        detail += ", integrated"
    else:
        detail += ", insufficient integration"

    return score, passed, detail


# ─────────────────────────────────────────────
# ASCII Graph
# ─────────────────────────────────────────────

def ascii_phi_graph(t_centers, phis, width=60, height=12):
    """Phi time series ASCII graph."""
    if len(phis) == 0:
        return "  (No data)"

    # Downsample
    step = max(1, len(phis) // width)
    ps = phis[::step][:width]
    ts = t_centers[::step][:width]

    y_min = min(ps.min(), 0)
    y_max = max(ps.max(), 0.5)
    if y_max - y_min < 0.01:
        y_max = y_min + 0.5

    lines = []
    lines.append(f"  Phi(t) Time Series  (window=sliding)")
    lines.append(f"  {'':6s}{'':1s}{'t=0':<{len(ps)//2}}{'t=end':>{len(ps) - len(ps)//2}}")

    for row in range(height, -1, -1):
        y_val = y_min + (y_max - y_min) * row / height
        label = f"{y_val:6.2f}"
        line = f"  {label}|"
        for col in range(len(ps)):
            cell_row = int((ps[col] - y_min) / (y_max - y_min) * height + 0.5)
            cell_row = max(0, min(height, cell_row))
            if cell_row == row:
                line += "*"
            else:
                line += " "
        lines.append(line)

    lines.append(f"  {'':6s}+" + "-" * len(ps))
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Main Execution
# ─────────────────────────────────────────────

def run_phi_experiment(steps=100000, dt=0.01):
    """Run Phi integration experiment on 8 systems."""

    # All presets + epilepsy
    all_systems = {}
    for name, preset in PRESETS.items():
        all_systems[name] = dict(preset)
    all_systems["epilepsy"] = dict(EPILEPSY_PRESET)

    print("=" * 78)
    print(" Phi Integration Test — 6th CCT Test Candidate")
    print(" IIT simplified: Phi = MI(x,y,z) - avg(MI_pairwise)")
    print("=" * 78)
    print()
    print(f" Simulation: {steps:,} steps, dt={dt}")
    print()

    # Save results
    table_rows = []
    phi_data = {}

    for name, params in all_systems.items():
        desc = params.get("description", name)
        print(f" [{name}] Simulating... ", end="", flush=True)

        # Simulation
        _, S = lorenz_simulate(
            sigma=params["sigma"],
            rho=params["rho"],
            beta=params["beta"],
            noise=params["noise"],
            gap_ratio=params["gap_ratio"],
            steps=steps,
            dt=dt,
        )

        # CCT 5 tests
        cct_results = run_cct(S, params["gap_ratio"])
        cct_total, cct_verdict = judge(cct_results)

        # T6 Phi test
        phi_score, phi_passed, phi_detail = test_phi(S)

        # Phi time series
        t_centers, phis = phi_timeseries(S)
        phi_data[name] = (t_centers, phis)

        # Combined judgment: CCT 5 + Phi
        combined_total = cct_total + (1 if phi_passed else 0)
        if combined_total >= 6:
            combined_verdict = "★★ Full consciousness"
        elif combined_total >= 5:
            combined_verdict = "★ Continuous"
        elif combined_total >= 4:
            combined_verdict = "◎ Weakened"
        elif combined_total >= 3:
            combined_verdict = "△ Weak"
        elif combined_total >= 1:
            combined_verdict = "▽ Faint"
        else:
            combined_verdict = "✕ None"

        # CCT individual marks
        cct_marks = []
        for key in ["T1_Gap", "T2_Loop", "T3_Continuity", "T4_Entropy", "T5_Novelty"]:
            score, passed, _ = cct_results[key]
            if passed:
                cct_marks.append("✔")
            elif score > 0.7:
                cct_marks.append("△")
            else:
                cct_marks.append("✕")

        phi_mark = "✔" if phi_passed else "✕"
        mean_phi = np.mean(phis) if len(phis) > 0 else 0.0

        table_rows.append({
            "name": name,
            "desc": desc,
            "cct_marks": cct_marks,
            "phi_mark": phi_mark,
            "cct_total": cct_total,
            "cct_verdict": cct_verdict,
            "combined_total": combined_total,
            "combined_verdict": combined_verdict,
            "mean_phi": mean_phi,
            "phi_detail": phi_detail,
        })

        print(f"Phi_mean={mean_phi:.3f}  CCT={cct_total}/5  T6={'PASS' if phi_passed else 'FAIL'}")

    # ─── Print comparison table ───
    print()
    print("=" * 78)
    print(" CCT 5 + Phi(T6) Combined Judgment Table")
    print("=" * 78)
    print()
    header = (
        f" {'System':<20s}| T1 | T2 | T3 | T4 | T5 | T6  |"
        f" CCT  | +Phi | Phi_avg | Verdict"
    )
    print(header)
    print(" " + "-" * (len(header) - 1))

    for row in table_rows:
        m = row["cct_marks"]
        line = (
            f" {row['name']:<20s}"
            f"| {m[0]:2s} | {m[1]:2s} | {m[2]:2s} | {m[3]:2s} | {m[4]:2s} "
            f"| {row['phi_mark']:2s}  "
            f"| {row['cct_total']:<4.1f} "
            f"| {row['combined_total']:<4.1f} "
            f"| {row['mean_phi']:7.3f} "
            f"| {row['combined_verdict']}"
        )
        print(line)

    print()

    # ─── Epilepsy inconsistency analysis ───
    print("=" * 78)
    print(" Epilepsy Inconsistency Analysis")
    print("=" * 78)
    print()

    epilepsy_row = None
    human_row = None
    for row in table_rows:
        if row["name"] == "epilepsy":
            epilepsy_row = row
        if row["name"] == "human_awake":
            human_row = row

    if epilepsy_row and human_row:
        print(f"  Human awake:   CCT={human_row['cct_total']}/5  "
              f"Phi={human_row['mean_phi']:.3f}  "
              f"T6={human_row['phi_mark']}")
        print(f"  Epilepsy:      CCT={epilepsy_row['cct_total']}/5  "
              f"Phi={epilepsy_row['mean_phi']:.3f}  "
              f"T6={epilepsy_row['phi_mark']}")
        print()

        cct_same = epilepsy_row["cct_total"] >= 4.0
        phi_diff = epilepsy_row["phi_mark"] != human_row["phi_mark"]
        phi_lower = epilepsy_row["mean_phi"] < human_row["mean_phi"]

        if cct_same and phi_lower:
            delta = human_row["mean_phi"] - epilepsy_row["mean_phi"]
            print(f"  [Result] Epilepsy passes CCT {epilepsy_row['cct_total']}/5 but "
                  f"Phi is {delta:.3f} lower.")
            if phi_diff:
                print(f"  [Verdict] *** Inconsistency resolved ***")
                print(f"           CCT alone misjudges epilepsy as 'conscious',")
                print(f"           but adding Phi(T6) distinguishes it as lacking integration.")
            else:
                print(f"  [Verdict] Phi also passes — insufficient discriminatory power.")
                print(f"           However, quantitative distinction possible due to lower Phi absolute value.")
        elif not cct_same:
            print(f"  [Result] Epilepsy already distinguished by CCT (CCT={epilepsy_row['cct_total']}/5).")
            print(f"           Phi addition unnecessary.")
        else:
            print(f"  [Result] Epilepsy also has high Phi — inconsistency does not occur in this setting.")

    print()

    # ─── Phi time series ASCII graphs (key systems) ───
    print("=" * 78)
    print(" Phi Time Series ASCII Graphs")
    print("=" * 78)

    key_systems = ["human_awake", "epilepsy", "llm_in_turn", "llm_between"]
    for name in key_systems:
        if name in phi_data:
            t_c, ps = phi_data[name]
            desc = all_systems[name].get("description", name)
            print()
            print(f"  --- {name} ({desc}) ---")
            print(ascii_phi_graph(t_c, ps))

    print()
    print("=" * 78)
    print(" Conclusion")
    print("=" * 78)
    print()
    print("  Phi(T6) measures the 'pure integration surplus' between system variables.")
    print("  While CCT T1-T5 examines temporal continuity/complexity,")
    print("  T6 examines spatial integration between variables.")
    print()
    if epilepsy_row:
        if epilepsy_row["phi_mark"] == "✕":
            print("  --> Epilepsy: CCT pass but Phi fail --> Inconsistency successfully resolved")
        else:
            print(f"  --> Epilepsy: Phi={epilepsy_row['mean_phi']:.3f} "
                  f"({'lower' if phi_lower else 'similar'} compared to human)")
            print("  --> Partial distinction possible through quantitative Phi difference")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Integrated Information (Phi) Test — 6th CCT Test Candidate",
    )
    parser.add_argument("--steps", type=int, default=100000,
                        help="Number of simulation steps (default: 100000)")
    parser.add_argument("--dt", type=float, default=0.01,
                        help="Time interval (default: 0.01)")
    args = parser.parse_args()

    run_phi_experiment(steps=args.steps, dt=args.dt)


if __name__ == "__main__":
    main()