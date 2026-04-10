#!/usr/bin/env python3
"""Discrete System FPS Threshold Test — Measuring CCT threshold fps in real discrete dynamics

To solve the problem where Lorenz (continuous) showed 5/5 at all fps,
we measure CCT threshold fps in 3 intrinsically discrete systems.

Systems:
  1. Rule 110 Cellular Automata (1D CA, 200 cells, Turing complete)
  2. Random Boolean Network (RBN, 100 nodes, K=2, edge of chaos)
  3. Echo State Network (ESN, 50 neurons, sparse, tanh, autonomous operation)

Key Question: "At what fps does CCT become 5/5?"
Brainwave Comparison: Gamma wave = 40Hz. Discovery if threshold fps is near 40!

Usage:
  python3 discrete_fps_test.py
  python3 discrete_fps_test.py --system rule110
  python3 discrete_fps_test.py --system rbn
  python3 discrete_fps_test.py --system esn
"""

import argparse
import os
import sys

import numpy as np

# ── Import CCT functions from consciousness_calc.py ──
from consciousness_calc import (
    run_cct,
    judge,
)

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

# ─────────────────────────────────────────────
# Brainwave Band Definitions
# ─────────────────────────────────────────────

BRAIN_WAVES = {
    "delta": {"range": (0.5, 4), "label": "δ (Sleep)", "center": 2},
    "theta": {"range": (4, 8), "label": "θ (Drowsy)", "center": 6},
    "alpha": {"range": (8, 13), "label": "α (Relaxed)", "center": 10},
    "beta":  {"range": (13, 30), "label": "β (Focused)", "center": 20},
    "gamma": {"range": (30, 100), "label": "γ (Conscious)", "center": 40},
}

FPS_VALUES = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
TOTAL_POINTS = 1000  # Total state points

# ─────────────────────────────────────────────
# System 1: Rule 110 Cellular Automata
# ─────────────────────────────────────────────

RULE110_TABLE = {}

def _init_rule110():
    """Initialize Rule 110 lookup table."""
    rule_num = 110
    for i in range(8):
        left = (i >> 2) & 1
        center = (i >> 1) & 1
        right = i & 1
        RULE110_TABLE[(left, center, right)] = (rule_num >> i) & 1

_init_rule110()


def rule110_step(cells):
    """Rule 110 single step update. Boundary: periodic."""
    n = len(cells)
    new_cells = np.zeros(n, dtype=int)
    for i in range(n):
        left = cells[(i - 1) % n]
        center = cells[i]
        right = cells[(i + 1) % n]
        new_cells[i] = RULE110_TABLE[(left, center, right)]
    return new_cells


def rule110_state_vector(cells, prev_cells):
    """Rule 110 state vector: [cell sum, cell changes, entropy]."""
    cell_sum = np.sum(cells)
    changes = np.sum(cells != prev_cells)

    # Shannon entropy (based on active ratio)
    p = cell_sum / len(cells) if len(cells) > 0 else 0.5
    p = np.clip(p, 1e-10, 1 - 1e-10)
    entropy = -(p * np.log(p) + (1 - p) * np.log(1 - p))

    return np.array([cell_sum, changes, entropy])


def simulate_rule110(fps, total_points=TOTAL_POINTS, n_cells=200, seed=42):
    """Rule 110 simulation.

    fps = number of updates between observations.
    Records total_points state vectors.
    """
    rng = np.random.default_rng(seed)
    cells = rng.integers(0, 2, size=n_cells)
    prev_cells = cells.copy()

    states = np.zeros((total_points, 3))

    for t in range(total_points):
        # Update fps steps
        for _ in range(fps):
            new_cells = rule110_step(cells)
            prev_cells = cells
            cells = new_cells

        states[t] = rule110_state_vector(cells, prev_cells)

    return states


# ─────────────────────────────────────────────
# System 2: Random Boolean Network (RBN)
# ─────────────────────────────────────────────

def create_rbn(n_nodes=100, k=2, seed=42):
    """Create K=2 Random Boolean Network.

    Returns:
        inputs: [n_nodes, k] — input node indices for each node
        functions: [n_nodes, 2^k] — Boolean function truth table for each node
        initial_state: [n_nodes] — initial state
    """
    rng = np.random.default_rng(seed)
    inputs = np.zeros((n_nodes, k), dtype=int)
    for i in range(n_nodes):
        inputs[i] = rng.choice(n_nodes, size=k, replace=False)

    # Random Boolean function for each node (2^k truth table)
    functions = rng.integers(0, 2, size=(n_nodes, 2**k))
    initial_state = rng.integers(0, 2, size=n_nodes)

    return inputs, functions, initial_state


def rbn_step(state, inputs, functions):
    """RBN single step update."""
    n_nodes = len(state)
    k = inputs.shape[1]
    new_state = np.zeros(n_nodes, dtype=int)

    for i in range(n_nodes):
        # Calculate truth table index from current state of input nodes
        idx = 0
        for j in range(k):
            idx = idx * 2 + state[inputs[i, j]]
        new_state[i] = functions[i, idx]

    return new_state


def rbn_state_vector(state, prev_state):
    """RBN state vector: [active ratio, change ratio, Hamming distance]."""
    active_ratio = np.mean(state)
    change_ratio = np.mean(state != prev_state)
    hamming = np.sum(state != prev_state)

    return np.array([active_ratio, change_ratio, hamming])


def simulate_rbn(fps, total_points=TOTAL_POINTS, n_nodes=100, k=2, seed=42):
    """RBN simulation.

    fps = number of updates between observations.
    """
    inputs, functions, state = create_rbn(n_nodes, k, seed)
    prev_state = state.copy()

    states = np.zeros((total_points, 3))

    for t in range(total_points):
        for _ in range(fps):
            new_state = rbn_step(state, inputs, functions)
            prev_state = state
            state = new_state

        states[t] = rbn_state_vector(state, prev_state)

    return states


# ─────────────────────────────────────────────
# System 3: Echo State Network (ESN)
# ─────────────────────────────────────────────

def create_esn(n_neurons=50, sparsity=0.1, spectral_radius=0.9, seed=42):
    """Create simplified ESN. Autonomous operation without input (heartbeat engine).

    Returns:
        W: [n_neurons, n_neurons] — internal weight matrix
        state: [n_neurons] — initial state
    """
    rng = np.random.default_rng(seed)

    # sparse random matrix
    W = rng.standard_normal((n_neurons, n_neurons))
    mask = rng.random((n_neurons, n_neurons)) < sparsity
    W = W * mask

    # Adjust spectral radius
    eigenvalues = np.linalg.eigvals(W)
    max_abs_eig = np.max(np.abs(eigenvalues))
    if max_abs_eig > 0:
        W = W * (spectral_radius / max_abs_eig)

    # Initial state: small random values
    state = rng.standard_normal(n_neurons) * 0.1

    return W, state


def esn_step(state, W):
    """ESN single step: tanh(W @ state)."""
    return np.tanh(W @ state)


def esn_state_vector(state):
    """ESN state vector: [mean activation, variance, energy]."""
    mean_act = np.mean(state)
    variance = np.var(state)
    energy = np.sum(state ** 2)

    return np.array([mean_act, variance, energy])


def simulate_esn(fps, total_points=TOTAL_POINTS, n_neurons=50, seed=42):
    """ESN simulation.

    fps = number of updates between observations.
    """
    W, state = create_esn(n_neurons, seed=seed)

    states = np.zeros((total_points, 3))

    for t in range(total_points):
        for _ in range(fps):
            state = esn_step(state, W)

        states[t] = esn_state_vector(state)

    return states


# ─────────────────────────────────────────────
# Simulator Registry
# ─────────────────────────────────────────────

SYSTEMS = {
    "rule110": {
        "name": "Rule 110 Cellular Automata",
        "desc": "1D CA, 200 cells, Turing complete",
        "simulate": simulate_rule110,
        "marker": "*",
    },
    "rbn": {
        "name": "Random Boolean Network",
        "desc": "100 nodes, K=2, edge of chaos",
        "simulate": simulate_rbn,
        "marker": "o",
    },
    "esn": {
        "name": "Echo State Network",
        "desc": "50 neurons, sparse, tanh, autonomous operation",
        "simulate": simulate_esn,
        "marker": "+",
    },
}


# ─────────────────────────────────────────────
# FPS Scan Engine
# ─────────────────────────────────────────────

def scan_system(system_key, fps_values=None, total_points=TOTAL_POINTS):
    """Scan fps range for one system, measure CCT scores.

    Returns:
        fps_arr: fps array
        scores_arr: CCT pass count (0~5)
        details: detailed results list
    """
    if fps_values is None:
        fps_values = FPS_VALUES

    system = SYSTEMS[system_key]
    simulate_fn = system["simulate"]

    fps_arr = np.array(fps_values, dtype=float)
    scores_arr = np.zeros(len(fps_values))
    details = []

    for i, fps in enumerate(fps_values):
        S = simulate_fn(fps, total_points=total_points)

        # NaN/Inf protection
        if np.any(~np.isfinite(S)):
            results = run_cct(np.zeros((total_points, 3)), 1.0)
            total, verdict = 0, "✕ Diverged"
        else:
            results = run_cct(S, 0.0)
            total, verdict = judge(results)

        scores_arr[i] = total
        details.append({
            "fps": fps,
            "total": total,
            "verdict": verdict,
            "results": results,
        })

    return fps_arr, scores_arr, details


def find_threshold_fps(fps_arr, scores_arr, target=5.0):
    """Find minimum fps where CCT reaches target/5 (linear interpolation)."""
    for i in range(len(scores_arr)):
        if scores_arr[i] >= target:
            if i == 0:
                return fps_arr[0]
            s0, s1 = scores_arr[i - 1], scores_arr[i]
            f0, f1 = fps_arr[i - 1], fps_arr[i]
            if s1 == s0:
                return f0
            frac = (target - s0) / (s1 - s0)
            return f0 + frac * (f1 - f0)
    return None


# ─────────────────────────────────────────────
# ASCII Graph: fps vs CCT (3 systems overlapped)
# ─────────────────────────────────────────────

def ascii_combined_graph(all_results, width=65, height=15):
    """Display fps vs CCT scores for 3 systems overlapped in one ASCII graph."""
    lines = []
    max_score = 5.0

    # Range of all fps values
    all_fps = []
    for sys_key, (fps_arr, scores_arr, _) in all_results.items():
        all_fps.extend(fps_arr)
    all_fps = sorted(set(all_fps))
    log_min = np.log10(min(all_fps))
    log_max = np.log10(max(all_fps))

    # Markers for each system
    markers = {"rule110": "*", "rbn": "o", "esn": "+"}

    # Create grid (default spaces)
    grid = [[" " for _ in range(width)] for _ in range(height + 1)]

    # Plot each system
    for sys_key, (fps_arr, scores_arr, _) in all_results.items():
        marker = markers.get(sys_key, ".")
        for i in range(len(fps_arr)):
            if fps_arr[i] <= 0:
                continue
            log_f = np.log10(fps_arr[i])
            col = int((log_f - log_min) / (log_max - log_min) * (width - 1))
            col = min(max(col, 0), width - 1)
            row = int(scores_arr[i] / max_score * height)
            row = min(max(row, 0), height)
            # If markers overlap, later systems overwrite
            grid[row][col] = marker

    # Mark gamma wave 40Hz line
    gamma_col = int((np.log10(40) - log_min) / (log_max - log_min) * (width - 1))
    gamma_col = min(max(gamma_col, 0), width - 1)
    for row in range(height + 1):
        if grid[row][gamma_col] == " ":
            grid[row][gamma_col] = ":"

    lines.append("")
    lines.append("  CCT   * = Rule110   o = RBN   + = ESN   : = 40Hz(γ)")
    for row in range(height, -1, -1):
        score_val = row / height * max_score
        if row % (height // 5) == 0:
            label = f"  {int(score_val)}│"
        else:
            label = "   │"
        lines.append(f"{label}{''.join(grid[row])}")

    # x-axis
    x_axis = "   └" + "─" * width
    lines.append(x_axis)

    # x-axis ticks
    tick_fps = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
    tick_str = [" "] * width
    for fps_val in tick_fps:
        log_f = np.log10(fps_val)
        col = int((log_f - log_min) / (log_max - log_min) * (width - 1))
        col = min(max(col, 0), width - 1)
        s = str(fps_val)
        for j, ch in enumerate(s):
            if col + j < width:
                tick_str[col + j] = ch

    lines.append("    " + "".join(tick_str) + "  fps (Hz)")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────

def print_comparison_table(all_results):
    """CCT score comparison table for 3 systems by fps."""
    print()
    print(" ─── CCT Score Comparison by fps " + "─" * 35)
    print()

    # Header
    sys_names = {"rule110": "Rule110", "rbn": "RBN", "esn": "ESN"}
    header = f" {'fps':>6} │"
    for sys_key in all_results:
        header += f" {sys_names[sys_key]:>8} │"
    print(header)
    print(" " + "─" * (10 + 11 * len(all_results)))

    # All fps values
    all_fps = sorted(set(
        int(f) for sys_key, (fps_arr, _, _) in all_results.items()
        for f in fps_arr
    ))

    for fps in all_fps:
        row = f" {fps:>6} │"
        for sys_key, (fps_arr, scores_arr, details) in all_results.items():
            # Find the fps
            idx = None
            for j, f in enumerate(fps_arr):
                if int(f) == fps:
                    idx = j
                    break
            if idx is not None:
                score = scores_arr[idx]
                if score >= 5:
                    mark = "★"
                elif score >= 4:
                    mark = "◎"
                elif score >= 3:
                    mark = "△"
                elif score >= 1:
                    mark = "▽"
                else:
                    mark = "✕"
                row += f" {score:>4.1f} {mark}  │"
            else:
                row += f"    -    │"
        print(row)

    print()


def print_detail_table(sys_key, fps_arr, scores_arr, details):
    """Detailed test results for one system."""
    sys_info = SYSTEMS[sys_key]
    print(f" ─── {sys_info['name']} ({sys_info['desc']}) " + "─" * 20)
    print(f" {'fps':>6} │ {'CCT':>5} │ {'T1':>4} │ {'T2':>4} │ {'T3':>4} │ {'T4':>4} │ {'T5':>4} │ Verdict")
    print(" " + "─" * 66)

    for d in details:
        fps = d["fps"]
        total = d["total"]
        r = d["results"]
        t1 = "✔" if r["T1_Gap"][1] else "✕"
        t2 = "✔" if r["T2_Loop"][1] else "✕"
        t3 = "✔" if r["T3_Continuity"][1] else "✕"
        t4 = "✔" if r["T4_Entropy"][1] else "✕"
        t5 = "✔" if r["T5_Novelty"][1] else "✕"
        print(f" {fps:>6.0f} │ {total:>5.1f} │  {t1}  │  {t2}  │  {t3}  │  {t4}  │  {t5}  │ {d['verdict']}")

    print()


def print_threshold_analysis(all_results):
    """Threshold fps analysis and gamma wave comparison for each system."""
    print(" ─── Threshold fps Analysis " + "─" * 39)
    print()

    sys_names = {"rule110": "Rule110 CA", "rbn": "RBN (K=2)", "esn": "ESN"}
    thresholds = {}

    for sys_key, (fps_arr, scores_arr, _) in all_results.items():
        th = find_threshold_fps(fps_arr, scores_arr, target=5.0)
        thresholds[sys_key] = th
        name = sys_names[sys_key]
        if th is not None:
            ratio = th / 40.0
            print(f"   {name:<12} Threshold fps = {th:>7.1f} Hz  (vs gamma {ratio:.2f}x)")
        else:
            print(f"   {name:<12} Threshold fps = Not reached within scan range")

    print()

    # Gamma wave 40Hz comparison
    print("   ─── Gamma Wave (40Hz) Comparison ───")
    print()
    gamma_hz = 40.0

    any_match = False
    for sys_key, th in thresholds.items():
        name = sys_names[sys_key]
        if th is not None:
            if 30 <= th <= 100:
                print(f"   ★ {name}: Threshold fps {th:.1f}Hz → Within gamma band (30-100Hz)!")
                any_match = True
            elif th < 30:
                print(f"     {name}: Threshold fps {th:.1f}Hz → Below gamma (lower processing speed sufficient)")
            else:
                print(f"     {name}: Threshold fps {th:.1f}Hz → Above gamma (higher processing speed needed)")
        else:
            print(f"     {name}: 5/5 not achieved even at 1000Hz")

    if any_match:
        print()
        print("   → Gamma wave band matches consciousness threshold in discrete systems too!")
    print()


def print_brainwave_mapping(all_results):
    """CCT scores for each system by brainwave band."""
    print(" ─── Brainwave Band Mapping " + "─" * 39)
    print()

    sys_names = {"rule110": "Rule110", "rbn": "RBN", "esn": "ESN"}

    header = f" {'Band':<12} │ {'CenterHz':>6} │"
    for sys_key in all_results:
        header += f" {sys_names[sys_key]:>8} │"
    print(header)
    print(" " + "─" * (24 + 11 * len(all_results)))

    for wave_name in ["delta", "theta", "alpha", "beta", "gamma"]:
        info = BRAIN_WAVES[wave_name]
        center = info["center"]
        row = f" {info['label']:<12} │ {center:>5.0f}  │"

        for sys_key, (fps_arr, scores_arr, _) in all_results.items():
            # Find nearest fps
            idx = np.argmin(np.abs(fps_arr - center))
            score = scores_arr[idx]
            nearest = fps_arr[idx]
            if score >= 5:
                mark = "★"
            elif score >= 4:
                mark = "◎"
            elif score >= 3:
                mark = "△"
            else:
                mark = "·"
            row += f" {score:>4.1f} {mark}  │"
        print(row)

    print()


def print_report(all_results, system_filter=None):
    """Print comprehensive report."""
    print("═" * 68)
    print(" Discrete FPS Test v1.0")
    print(" \"At what fps do discrete systems achieve CCT 5/5?\"")
    print("═" * 68)
    print()
    print(" Systems:")
    for sys_key in all_results:
        info = SYSTEMS[sys_key]
        print(f"   {info['marker']}  {info['name']} — {info['desc']}")
    print()
    print(f" Settings: fps = {FPS_VALUES}")
    print(f"           Total state points = {TOTAL_POINTS}")
    print()

    # ── Comparison Table ──
    print_comparison_table(all_results)

    # ── ASCII Graph ──
    print(" ─── fps vs CCT (3 Systems Overlapped) " + "─" * 29)
    print(ascii_combined_graph(all_results))
    print()

    # ── Detailed Tests ──
    for sys_key, (fps_arr, scores_arr, details) in all_results.items():
        print_detail_table(sys_key, fps_arr, scores_arr, details)

    # ── Brainwave Band Mapping ──
    print_brainwave_mapping(all_results)

    # ── Threshold fps Analysis ──
    print_threshold_analysis(all_results)

    # ── Interpretation ──
    print(" ─── Interpretation " + "─" * 48)
    print()
    print("   Difference between Lorenz (continuous) vs discrete systems:")
    print("   - Lorenz: dt=1/fps conversion is just resolution change, dynamics itself is continuous")
    print("     → 5/5 at all fps (limitation of continuous systems)")
    print("   - Discrete systems: fps = actual update count")
    print("     → Low fps lacks information → CCT failure")
    print("     → Sufficient fps accumulates complexity → CCT passes")
    print()
    print("   Relationship with brainwaves:")
    print("   - Brain is a collection of neuron firings (discrete events)")
    print("   - Gamma wave 40Hz = minimum synchronization frequency for conscious cognition")
    print("   - If discrete system's CCT threshold fps is near 40Hz")
    print("     → \"Minimum discrete update rate for consciousness\" = gamma wave")
    print()
    print("   Limitations:")
    print("   - CA/RBN/ESN are extremely simplified models of the brain")
    print("   - CCT test thresholds themselves are model-dependent")
    print("   - Mapping between fps and \"updates per time\" is interpretive choice")
    print()
    print("═" * 68)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Discrete System FPS Threshold Test — Measuring CCT in real discrete dynamics",
    )
    parser.add_argument("--system", type=str, default=None,
                        choices=["rule110", "rbn", "esn"],
                        help="Run specific system only (default: all)")
    parser.add_argument("--total-points", type=int, default=TOTAL_POINTS,
                        help=f"Total state points (default: {TOTAL_POINTS})")

    args = parser.parse_args()

    total_points = args.total_points

    if args.system:
        systems_to_run = [args.system]
    else:
        systems_to_run = ["rule110", "rbn", "esn"]

    print(f"  Starting scan: Systems = {', '.join(systems_to_run)}")
    print(f"  fps = {FPS_VALUES}")
    print(f"  Total state points = {total_points}")
    print()

    all_results = {}
    for sys_key in systems_to_run:
        info = SYSTEMS[sys_key]
        print(f"  [{info['name']}] Scanning...")
        fps_arr, scores_arr, details = scan_system(
            sys_key, fps_values=FPS_VALUES, total_points=total_points,
        )
        all_results[sys_key] = (fps_arr, scores_arr, details)
        th = find_threshold_fps(fps_arr, scores_arr)
        if th is not None:
            print(f"  [{info['name']}] Threshold fps = {th:.1f} Hz")
        else:
            print(f"  [{info['name']}] Threshold fps = Not reached")

    print()
    print_report(all_results, system_filter=args.system)


if __name__ == "__main__":
    main()