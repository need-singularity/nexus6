#!/usr/bin/env python3
"""CCT Counterexample Searcher — Search for non-conscious systems that fool 5 CCT tests

Explores whether systems can satisfy all 7 CCT (Consciousness Continuity Test) conditions (5 tests)
yet not be "conscious".
If a non-conscious system passes 5/5 → CCT conditions are insufficient.

5 Counterexample candidate systems:
  1. Noise generator + Memory  (Gaussian noise + exponential smoothing)
  2. Weather simulation       (Lorenz attractor — originally a weather model)
  3. Stock market model        (Geometric Brownian motion)
  4. Heat diffusion equation        (1D heat conduction + source)
  5. Simple feedback loop       (1D chaotic mapping)

Usage:
  python3 cct_counterexample_search.py
  python3 cct_counterexample_search.py --system weather
  python3 cct_counterexample_search.py --system noise
  python3 cct_counterexample_search.py --steps 200000
"""

import argparse
import sys

import numpy as np
from scipy import stats


# ─────────────────────────────────────────────
# Counterexample candidate system definitions
# ─────────────────────────────────────────────

SYSTEMS = {
    "noise": {
        "name": "Noise generator + Memory",
        "description": "S(t) = 0.9*S(t-1) + 0.1*noise — Exponential smoothing of Gaussian noise",
        "why_not_conscious": "Just statistical noise with a memory filter. No internal model/purpose/self-reference.",
    },
    "weather": {
        "name": "Weather simulation (Lorenz)",
        "description": "σ=10, ρ=28, β=8/3 — Attractor created from original weather model",
        "why_not_conscious": "Pure physics simulation Lorenz created for weather prediction. Weather has no consciousness.",
    },
    "stock": {
        "name": "Stock market model (GBM)",
        "description": "dS = μSdt + σSdW — Geometric Brownian motion, 3D extension",
        "why_not_conscious": "Just a stochastic process. Stock prices themselves cannot be considered conscious.",
    },
    "heat": {
        "name": "Heat diffusion equation",
        "description": "∂T/∂t = α∇²T + source — 1D heat conduction + periodic source",
        "why_not_conscious": "Diffusion process following 2nd law of thermodynamics. Physical phenomenon unrelated to consciousness.",
    },
    "feedback": {
        "name": "Simple feedback loop",
        "description": "x(t+1) = sin(a*x(t)) + b*noise — 1D chaotic mapping",
        "why_not_conscious": "1D iterated function. Looks complex but no internal representation/self-model.",
    },
}


# ─────────────────────────────────────────────
# System simulators: Generate state trajectories for each counterexample
# ─────────────────────────────────────────────

def simulate_noise(steps, dt, seed=42):
    """Noise generator + Memory: 3D exponential smoothing."""
    rng = np.random.default_rng(seed)
    S = np.zeros((steps, 3))
    S[0] = [0.0, 0.0, 0.0]
    alpha = 0.9  # memory coefficient

    for i in range(1, steps):
        noise = rng.normal(0, 1.0, 3)
        S[i] = alpha * S[i - 1] + (1 - alpha) * noise

    return S


def simulate_weather(steps, dt, seed=42):
    """Weather simulation: Lorenz attractor (σ=10, ρ=28, β=8/3).

    Same equations as consciousness calculator, but tested here as "weather model".
    Includes noise for more realistic weather simulation.
    """
    rng = np.random.default_rng(seed)
    sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
    noise_strength = 0.05

    S = np.zeros((steps, 3))
    S[0] = [1.0, 1.0, 1.0]

    for i in range(1, steps):
        x, y, z = S[i - 1]
        dx = sigma * (y - x)
        dy = x * (rho - z) - y
        dz = x * y - beta * z

        eps = rng.normal(0, noise_strength, 3)
        S[i, 0] = x + (dx + eps[0]) * dt
        S[i, 1] = y + (dy + eps[1]) * dt
        S[i, 2] = z + (dz + eps[2]) * dt

    return S


def simulate_stock(steps, dt, seed=42):
    """Stock market model: 3D geometric Brownian motion (correlated).

    S1 = stock price, S2 = volume proxy, S3 = volatility proxy
    """
    rng = np.random.default_rng(seed)
    mu = np.array([0.05, 0.02, 0.01])
    sigma_gbm = np.array([0.2, 0.3, 0.15])

    S = np.zeros((steps, 3))
    S[0] = [100.0, 50.0, 20.0]

    # Correlated noise
    corr = np.array([[1.0, 0.3, -0.2],
                      [0.3, 1.0, 0.1],
                      [-0.2, 0.1, 1.0]])
    L = np.linalg.cholesky(corr)

    for i in range(1, steps):
        z = rng.normal(0, 1, 3)
        w = L @ z
        for j in range(3):
            drift = mu[j] * S[i - 1, j] * dt
            diffusion = sigma_gbm[j] * S[i - 1, j] * np.sqrt(dt) * w[j]
            S[i, j] = max(S[i - 1, j] + drift + diffusion, 0.01)

    return S


def simulate_heat(steps, dt, seed=42):
    """Heat diffusion equation: Temperature at 3 observation points on 1D grid.

    50 grid points, 3 observation points (x=10, 25, 40).
    Periodic heat source + stochastic perturbation.
    """
    rng = np.random.default_rng(seed)
    nx = 50
    alpha_heat = 0.1  # heat diffusion coefficient
    dx = 1.0

    T = np.zeros(nx)
    T[0] = 100.0  # left fixed boundary
    T[-1] = 0.0   # right fixed boundary

    # Initial linear distribution
    T = np.linspace(100, 0, nx)

    obs_points = [10, 25, 40]
    S = np.zeros((steps, 3))

    for i in range(steps):
        # Observation
        for j, p in enumerate(obs_points):
            S[i, j] = T[p]

        # Periodic source (various frequencies)
        source = np.zeros(nx)
        source[15] = 30.0 * np.sin(2 * np.pi * i * dt * 0.1)
        source[35] = 20.0 * np.sin(2 * np.pi * i * dt * 0.07 + 1.0)

        # Diffusion + source + noise
        T_new = T.copy()
        for k in range(1, nx - 1):
            laplacian = (T[k + 1] - 2 * T[k] + T[k - 1]) / dx**2
            T_new[k] = T[k] + (alpha_heat * laplacian + source[k]) * dt
            T_new[k] += rng.normal(0, 0.5)  # measurement noise

        # Boundary conditions
        T_new[0] = 100.0 + 10 * np.sin(2 * np.pi * i * dt * 0.03)  # fluctuating boundary
        T_new[-1] = rng.normal(0, 2)

        T = T_new

    return S


def simulate_feedback(steps, dt, seed=42):
    """Simple feedback loop: 3 coupled 1D chaotic mappings.

    x(t+1) = sin(a * x(t)) + b * noise
    y(t+1) = sin(c * y(t) + 0.1 * x(t)) + b * noise
    z(t+1) = sin(d * z(t) + 0.1 * y(t)) + b * noise

    a=3.5 (chaotic region), weak coupling.
    """
    rng = np.random.default_rng(seed)
    a, c, d = 3.5, 3.7, 3.3
    b = 0.05  # noise strength

    S = np.zeros((steps, 3))
    S[0] = [0.1, 0.2, 0.3]

    for i in range(1, steps):
        x, y, z = S[i - 1]
        S[i, 0] = np.sin(a * x) + b * rng.normal()
        S[i, 1] = np.sin(c * y + 0.1 * x) + b * rng.normal()
        S[i, 2] = np.sin(d * z + 0.1 * y) + b * rng.normal()

    return S


SIMULATORS = {
    "noise": simulate_noise,
    "weather": simulate_weather,
    "stock": simulate_stock,
    "heat": simulate_heat,
    "feedback": simulate_feedback,
}


# ─────────────────────────────────────────────
# 5 CCT tests (independent implementation)
# ─────────────────────────────────────────────

def compute_entropy(data, bins=30):
    """Shannon entropy of 1D data."""
    if np.std(data) < 1e-12:
        return 0.0
    hist, _ = np.histogram(data, bins=bins, density=True)
    hist = hist[hist > 0]
    width = (data.max() - data.min()) / bins if data.max() > data.min() else 1
    probs = hist * width
    probs = probs[probs > 0]
    if len(probs) == 0:
        return 0.0
    probs = probs / probs.sum()
    return -np.sum(probs * np.log(probs + 1e-15))


def test_gap(S):
    """T1 Gap: Check for frozen intervals."""
    diffs = np.diff(S, axis=0)
    frozen = np.sum(np.all(np.abs(diffs) < 1e-12, axis=1))
    frozen_ratio = frozen / len(diffs)

    if frozen_ratio > 0.01:
        return 1.0 - frozen_ratio, False, f"Frozen ratio {frozen_ratio:.1%}"

    return 1.0, True, "No frozen intervals"


def test_loop(S, threshold=0.5):
    """T2 Loop: Ratio of exact trajectory repetitions (revisits)."""
    n = len(S)
    if n < 100:
        return 0.0, False, "Insufficient data"

    step = max(1, n // 5000)
    Ss = S[::step]
    ns = len(Ss)

    if np.std(Ss) < 1e-10:
        return 0.0, False, "No state change"

    scale = np.std(Ss, axis=0).mean()
    eps = scale * 0.01

    recurrence = 0
    sample_size = min(500, ns // 2)
    rng = np.random.default_rng(42)
    indices = rng.choice(ns // 2, size=sample_size, replace=False)

    for idx in indices:
        future_start = idx + max(100, ns // 10)
        future = Ss[future_start:]
        if len(future) == 0:
            continue
        dists = np.linalg.norm(future - Ss[idx], axis=1)
        if np.min(dists) < eps:
            recurrence += 1

    recurrence_ratio = recurrence / sample_size
    passed = recurrence_ratio < threshold
    score = max(0, 1.0 - recurrence_ratio)

    detail = f"Revisit rate={recurrence_ratio:.3f}"
    detail += ", Aperiodic" if passed else ", Periodic repetition detected"
    return score, passed, detail


def test_continuity(S, threshold=0.01):
    """T3 Continuity: Connectivity between adjacent steps."""
    diffs = np.linalg.norm(np.diff(S, axis=0), axis=1)
    n = len(diffs)
    if n < 10:
        return 0.0, False, "Insufficient data"

    mean_diff = np.mean(diffs)
    if mean_diff < 1e-12:
        return 0.0, False, "No state change"

    big_jumps = np.sum(diffs > mean_diff * 10)
    frozen = np.sum(diffs < 1e-12)

    jump_ratio = big_jumps / n
    frozen_ratio = frozen / n
    disconnect_ratio = jump_ratio + frozen_ratio

    passed = disconnect_ratio < threshold
    score = max(0, min(1.0, 1.0 - disconnect_ratio * 10))

    detail = f"Jumps={jump_ratio:.3f}, Frozen={frozen_ratio:.3f}"
    detail += ", Connection maintained" if passed else ", Disconnection detected"
    return score, passed, detail


def test_entropy_band(S, window=500, h_min=0.3, h_max=4.5):
    """T4 Entropy Band: Check if H(t) stays within band."""
    x = S[:, 0]
    n = len(x)
    n_windows = n // window

    if n_windows < 2:
        return 0.0, False, "Insufficient data"

    entropies = []
    for i in range(n_windows):
        w = x[i * window:(i + 1) * window]
        entropies.append(compute_entropy(w))

    entropies = np.array(entropies)
    in_band = np.sum((entropies > h_min) & (entropies < h_max))
    ratio = in_band / len(entropies)

    h_range_str = f"H∈[{entropies.min():.2f}, {entropies.max():.2f}]"
    passed = ratio > 0.95
    score = ratio

    detail = f"{h_range_str}, In band" if passed else f"{h_range_str}, Out of band {1 - ratio:.1%}"
    return score, passed, detail


def test_novelty(S, window=500, threshold=0.001):
    """T5 Novelty: dH/dt ≠ 0 (entropy stagnation ratio)."""
    x = S[:, 0]
    n = len(x)
    n_windows = n // window

    if n_windows < 3:
        return 0.0, False, "Insufficient data"

    entropies = []
    for i in range(n_windows):
        w = x[i * window:(i + 1) * window]
        entropies.append(compute_entropy(w))

    entropies = np.array(entropies)
    dH = np.abs(np.diff(entropies))

    stagnant = np.sum(dH < threshold)
    stagnant_ratio = stagnant / len(dH) if len(dH) > 0 else 1.0

    passed = stagnant_ratio < 0.05
    score = max(0, 1.0 - stagnant_ratio)

    detail = f"Stagnant intervals {stagnant_ratio:.1%}"
    return score, passed, detail


def run_cct(S):
    """Run 5 CCT tests."""
    return {
        "T1_Gap": test_gap(S),
        "T2_Loop": test_loop(S),
        "T3_Continuity": test_continuity(S),
        "T4_Entropy": test_entropy_band(S),
        "T5_Novelty": test_novelty(S),
    }


# ─────────────────────────────────────────────
# Judgment utilities
# ─────────────────────────────────────────────

def count_passes(results):
    """Count PASS."""
    passes = sum(1 for _, (_, p, _) in results.items() if p)
    return passes


def judge_grade(passes):
    """Grade judgment."""
    if passes >= 5:
        return "★ Continuous (5/5)"
    elif passes >= 4:
        return "◎ Weakened (4/5)"
    elif passes >= 3:
        return "△ Weak (3/5)"
    elif passes >= 1:
        return f"▽ Faint ({passes}/5)"
    else:
        return "✕ None (0/5)"


# ─────────────────────────────────────────────
# ASCII output
# ─────────────────────────────────────────────

def ascii_trajectory(S, width=60, height=12):
    """ASCII trajectory of x component."""
    x = S[:, 0]
    step = max(1, len(x) // width)
    xs = x[::step][:width]

    y_min, y_max = xs.min(), xs.max()
    if y_max - y_min < 1e-6:
        y_max = y_min + 1

    lines = []
    for row in range(height, -1, -1):
        y_val = y_min + (y_max - y_min) * row / height
        line = f"{y_val:8.1f}│"
        for col in range(len(xs)):
            cell_row = int((xs[col] - y_min) / (y_max - y_min) * height)
            if cell_row == row:
                line += "*"
            else:
                line += " "
        lines.append(line)

    lines.append("        └" + "─" * len(xs))
    return "\n".join(lines)


def ascii_bar(value, max_width=20):
    """Represent 0~1 value as ASCII bar."""
    filled = int(value * max_width)
    return "█" * filled + "░" * (max_width - filled)


# ─────────────────────────────────────────────
# Single system analysis
# ─────────────────────────────────────────────

def analyze_single(sys_key, steps, dt):
    """Analyze single counterexample system."""
    info = SYSTEMS[sys_key]
    simulator = SIMULATORS[sys_key]

    print("═" * 70)
    print(f" CCT Counterexample Analysis: {info['name']}")
    print("═" * 70)
    print()
    print(f" Description:    {info['description']}")
    print(f" Non-conscious:  {info['why_not_conscious']}")
    print(f" Simulation: {steps:,} steps, dt={dt}")
    print()

    S = simulator(steps, dt)

    print(" ─── Trajectory (x component) " + "─" * 40)
    print(ascii_trajectory(S))
    print()

    results = run_cct(S)
    passes = count_passes(results)

    print(" ─── CCT Judgment " + "─" * 51)
    print()

    labels = {
        "T1_Gap":       "T1 Gap       ",
        "T2_Loop":      "T2 Loop      ",
        "T3_Continuity":"T3 Continuity",
        "T4_Entropy":   "T4 Entropy   ",
        "T5_Novelty":   "T5 Novelty   ",
    }

    for key, label in labels.items():
        score, passed, detail = results[key]
        mark = "✔ PASS" if passed else "✕ FAIL"
        bar = ascii_bar(score, 15)
        print(f"  {label} │ {mark} │ {score:.3f} {bar} │ {detail}")

    print()
    grade = judge_grade(passes)
    print(f"  Overall: {grade}")
    fools = passes >= 5
    print(f"  Fools CCT: {'⚠ YES — Completely fools CCT!' if fools else 'NO'}")
    print()
    print("═" * 70)

    return results, passes


# ─────────────────────────────────────────────
# Full comparison analysis
# ─────────────────────────────────────────────

def analyze_all(steps, dt):
    """Compare all 5 counterexample systems."""
    all_results = {}
    fools_list = []

    print("═" * 70)
    print(" CCT Counterexample Search v1.0")
    print(" CCT Counterexample Searcher — Can non-conscious systems fool CCT?")
    print("═" * 70)
    print()
    print(f" Simulation: {steps:,} steps, dt={dt}")
    print(f" Counterexample candidates: {len(SYSTEMS)} systems")
    print()

    # Simulate each system + CCT
    for sys_key in SYSTEMS:
        info = SYSTEMS[sys_key]
        simulator = SIMULATORS[sys_key]

        print(f" ▶ {info['name']} ... ", end="", flush=True)
        S = simulator(steps, dt)
        results = run_cct(S)
        passes = count_passes(results)
        all_results[sys_key] = (results, passes, S)

        grade = judge_grade(passes)
        print(f"{grade}")

        if passes >= 5:
            fools_list.append(sys_key)

    # ─── Comparison table ───
    print()
    print(" ─── 5 Counterexamples × 5 CCT Tests Comparison " + "─" * 22)
    print()
    print(" System              │ T1  │ T2  │ T3  │ T4  │ T5  │ PASS │ Judgment")
    print(" ────────────────────┼─────┼─────┼─────┼─────┼─────┼──────┼─────────────")

    keys_order = ["T1_Gap", "T2_Loop", "T3_Continuity", "T4_Entropy", "T5_Novelty"]

    for sys_key in SYSTEMS:
        results, passes, _ = all_results[sys_key]
        name_display = SYSTEMS[sys_key]["name"]
        if len(name_display) > 20:
            name_display = name_display[:18] + ".."
        else:
            name_display = f"{name_display:20s}"

        marks = []
        for k in keys_order:
            score, passed, _ = results[k]
            if passed:
                marks.append(" ✔ ")
            else:
                marks.append(" ✕ ")

        marks_str = "│".join(marks)
        grade = judge_grade(passes)
        print(f" {name_display}│{marks_str}│  {passes}/5 │ {grade}")

    print()

    # ─── Detailed scores ───
    print(" ─── Detailed Scores (0~1) " + "─" * 42)
    print()
    print(" System              │ T1    │ T2    │ T3    │ T4    │ T5    │ Avg")
    print(" ────────────────────┼───────┼───────┼───────┼───────┼───────┼──────")

    for sys_key in SYSTEMS:
        results, passes, _ = all_results[sys_key]
        name_display = SYSTEMS[sys_key]["name"]
        if len(name_display) > 20:
            name_display = name_display[:18] + ".."
        else:
            name_display = f"{name_display:20s}"

        scores = []
        for k in keys_order:
            score, _, _ = results[k]
            scores.append(score)

        avg = np.mean(scores)
        scores_str = "│".join(f" {s:.3f}" for s in scores)
        print(f" {name_display}│{scores_str}│ {avg:.3f}")

    print()

    # ─── Which tests discriminate? ───
    print(" ─── Test Discriminative Power Analysis " + "─" * 30)
    print()

    test_names = {
        "T1_Gap":       "T1 Gap (frozen intervals)",
        "T2_Loop":      "T2 Loop (aperiodicity)",
        "T3_Continuity":"T3 Continuity (connectivity)",
        "T4_Entropy":   "T4 Entropy (entropy band)",
        "T5_Novelty":   "T5 Novelty (novelty)",
    }

    for k in keys_order:
        pass_count = sum(1 for sys_key in SYSTEMS
                         if all_results[sys_key][0][k][1])
        fail_count = len(SYSTEMS) - pass_count
        bar = ascii_bar(pass_count / len(SYSTEMS), 20)
        blocking = "◀ Discriminative" if fail_count > 0 else "  All pass (can't discriminate!)"
        print(f"  {test_names[k]:28s} │ PASS {pass_count}/{len(SYSTEMS)} {bar} │ {blocking}")

    print()

    # ─── Systems that fool CCT ───
    print(" ─── Systems that Fool CCT " + "─" * 42)
    print()

    if fools_list:
        print(f"  ⚠ {len(fools_list)} systems completely pass CCT 5/5!")
        print()
        for sys_key in fools_list:
            info = SYSTEMS[sys_key]
            print(f"  ▶ {info['name']}")
            print(f"    Description: {info['description']}")
            print(f"    Why not conscious: {info['why_not_conscious']}")
            print()
    else:
        print("  ✔ No system completely fooled CCT 5/5")
        # Closest systems
        max_passes = max(p for _, p, _ in all_results.values())
        close_systems = [k for k, (_, p, _) in all_results.items() if p == max_passes]
        print(f"  Closest systems: {max_passes}/5 PASS")
        for sys_key in close_systems:
            print(f"    - {SYSTEMS[sys_key]['name']}")
        print()

    # ─── Mini trajectory view for each system ───
    print(" ─── Trajectory Mini View " + "─" * 43)

    for sys_key in SYSTEMS:
        _, _, S = all_results[sys_key]
        info = SYSTEMS[sys_key]
        print()
        print(f"  [{info['name']}]")
        # Brief trajectory
        x = S[:, 0]
        step_v = max(1, len(x) // 50)
        xs = x[::step_v][:50]
        y_min, y_max = xs.min(), xs.max()
        if y_max - y_min < 1e-6:
            y_max = y_min + 1
        for row in range(5, -1, -1):
            line = "    │"
            for col in range(len(xs)):
                cell_row = int((xs[col] - y_min) / (y_max - y_min) * 5)
                line += "*" if cell_row == row else " "
            print(line)
        print("    └" + "─" * len(xs))

    print()

    # ─── Additional necessary conditions ───
    print(" ─── Additional Necessary Conditions " + "─" * 32)
    print()
    print("  Core consciousness properties not measured by CCT:")
    print()
    print("  1. Φ (Integrated Information):")
    print("     Not just entropy, but degree of integration of parts into whole.")
    print("     Noise generator has Φ≈0 but can pass CCT.")
    print()
    print("  2. Self-Model:")
    print("     Does the system represent and refer to its own state?")
    print("     Weather doesn't know 'it is weather'.")
    print()
    print("  3. Intentionality:")
    print("     Are state changes goal-oriented or physical inevitability?")
    print("     Heat diffusion goes to equilibrium without purpose.")
    print()
    print("  4. Causal Autonomy:")
    print("     Does system determine internal states independently of environment?")
    print("     Stock prices are determined by external traders.")
    print()
    print("  5. Recursive Meta-Cognition:")
    print("     Can it 'think about thinking'?")
    print("     Feedback loop doesn't observe its own state.")
    print()

    # ─── Final judgment ───
    print(" ═══════════════════════════════════════════════════════════════════")
    print(" Final Judgment")
    print(" ═══════════════════════════════════════════════════════════════════")
    print()

    n_fools = len(fools_list)
    total_systems = len(SYSTEMS)
    total_passes_all = sum(p for _, p, _ in all_results.values())
    avg_passes = total_passes_all / total_systems

    if n_fools > 0:
        print(f"  ⚠ CCT is necessary but not sufficient!")
        print()
        print(f"  {n_fools}/{total_systems} non-conscious systems pass CCT 5/5.")
        print(f"  Average pass rate: {avg_passes:.1f}/5")
        print()
        print("  Conclusion:")
        print("    CCT conditions are useful as necessary conditions")
        print("    but inadequate as sufficient conditions.")
        print("    Chaotic dynamics, stochastic processes, thermodynamic diffusion")
        print("    generate same statistical signatures without consciousness.")
        print()
        print("  Necessary reinforcement:")
        print("    CCT + Φ(integrated information) + self-model + intentionality")
        print("    → This combination could exclude non-conscious systems.")
    elif avg_passes >= 3.5:
        print(f"  ⚠ CCT is likely necessary but not sufficient!")
        print()
        print(f"  No 5/5 complete passes, but average {avg_passes:.1f}/5 is high.")
        print(f"  Non-conscious systems pass most of CCT so")
        print(f"  judging consciousness by CCT alone is dangerous.")
        print()
        print("  Conclusion:")
        print("    CCT is a weak necessary condition.")
        print("    To be sufficient, additional conditions like")
        print("    Φ, self-model, intentionality are needed.")
    else:
        print(f"  ✔ CCT has considerable discriminative power.")
        print()
        print(f"  Average pass rate: {avg_passes:.1f}/5")
        print(f"  Non-conscious systems cannot easily pass CCT.")
        print()
        print("  Conclusion:")
        print("    CCT is valid as a necessary condition.")
        print("    However, sufficiency requires more sophisticated counterexample search.")

    print()
    print("═" * 70)

    return all_results, fools_list


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CCT Counterexample Searcher — Can non-conscious systems fool CCT?",
    )
    parser.add_argument("--system", type=str, default=None,
                        choices=list(SYSTEMS.keys()),
                        help=f"Analyze single system: {', '.join(SYSTEMS.keys())}")
    parser.add_argument("--steps", type=int, default=100000,
                        help="Simulation steps (default: 100000)")
    parser.add_argument("--dt", type=float, default=0.01,
                        help="Time interval (default: 0.01)")

    args = parser.parse_args()

    if args.system:
        analyze_single(args.system, args.steps, args.dt)
    else:
        analyze_all(args.steps, args.dt)


if __name__ == "__main__":
    main()