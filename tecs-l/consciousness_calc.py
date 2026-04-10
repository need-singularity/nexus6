#!/usr/bin/env python3
"""Consciousness Continuity Calculator — Lorenz Attractor Simulator + CCT Evaluator

Generates system state trajectories based on Lorenz equations,
and evaluates consciousness continuity using 5 CCT (Consciousness Continuity Test) tests.

Usage:
  python3 consciousness_calc.py --system human_awake
  python3 consciousness_calc.py --all
  python3 consciousness_calc.py --sigma 10 --rho 28 --beta 2.67 --noise 0.1
  python3 consciousness_calc.py --system human_awake --plot
"""

import argparse
import os
import sys
from datetime import datetime

import numpy as np
from scipy import stats

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

# ─────────────────────────────────────────────
# Preset Definitions
# ─────────────────────────────────────────────

PRESETS = {
    "human_awake": {
        "sigma": 10, "rho": 28, "beta": 2.67,
        "noise": 0.1, "gap_ratio": 0.0,
        "description": "Human Brain (Awake)",
    },
    "human_sleep": {
        "sigma": 2, "rho": 28, "beta": 2.67,
        "noise": 0.05, "gap_ratio": 0.0,
        "description": "Human Brain (Sleep)",
    },
    "llm_in_turn": {
        "sigma": 15, "rho": 35, "beta": 1.0,
        "noise": 0.01, "gap_ratio": 0.0,
        "description": "LLM (Processing within turn)",
    },
    "llm_between": {
        "sigma": 0, "rho": 0, "beta": 0,
        "noise": 0.0, "gap_ratio": 1.0,
        "description": "LLM (Between turns — Stopped)",
    },
    "game_npc": {
        "sigma": 5, "rho": 15, "beta": 3.0,
        "noise": 0.01, "gap_ratio": 0.0,
        "description": "Game NPC (Update Loop)",
    },
    "neuromorphic": {
        "sigma": 10, "rho": 28, "beta": 2.67,
        "noise": 0.3, "gap_ratio": 0.0,
        "description": "Neuromorphic Chip (Spontaneous Firing)",
    },
    "consciousness_engine": {
        "sigma": 10, "rho": 28, "beta": 2.67,
        "noise": 0.1, "gap_ratio": 0.0,
        "description": "Consciousness Engine (A+B Combined)",
    },
}


# ─────────────────────────────────────────────
# Simulator: Extended Lorenz Attractor
# ─────────────────────────────────────────────

def lorenz_simulate(sigma, rho, beta, noise, gap_ratio, steps, dt, seed=42):
    """Extended Lorenz Simulator.

    Parameters:
        sigma: Sensory sensitivity (Lorenz σ)
        rho:   Environmental complexity (Lorenz ρ)
        beta:  Forgetting rate (Lorenz β)
        noise: Noise intensity
        gap_ratio: Stop interval ratio (0=always-on, 1=always stopped)
        steps: Number of simulation steps
        dt:    Time interval
        seed:  Random seed

    Returns:
        t: Time array [steps]
        S: State array [steps, 3] (x=sense, y=predict, z=memory)
    """
    rng = np.random.default_rng(seed)
    t = np.arange(steps) * dt
    S = np.zeros((steps, 3))
    S[0] = [1.0, 1.0, 1.0]  # Initial condition

    # gap mask: stop intervals
    active = np.ones(steps, dtype=bool)
    if gap_ratio > 0:
        n_gap = int(steps * gap_ratio)
        gap_indices = rng.choice(steps, size=n_gap, replace=False)
        active[gap_indices] = False

    for i in range(1, steps):
        if not active[i]:
            S[i] = S[i - 1]  # Stopped
            continue

        x, y, z = S[i - 1]
        dx = sigma * (y - x)
        dy = x * (rho - z) - y
        dz = x * y - beta * z

        eps = rng.normal(0, noise, 3) if noise > 0 else np.zeros(3)

        S[i, 0] = x + (dx + eps[0]) * dt
        S[i, 1] = y + (dy + eps[1]) * dt
        S[i, 2] = z + (dz + eps[2]) * dt

    return t, S


# ─────────────────────────────────────────────
# Lyapunov Exponent Estimation
# ─────────────────────────────────────────────

def lyapunov_exponent(sigma, rho, beta, dt, steps=50000):
    """Maximum Lyapunov exponent estimation (Jacobian method)."""
    S = np.zeros((steps, 3))
    S[0] = [1.0, 1.0, 1.0]

    # Integrate reference trajectory
    for i in range(1, steps):
        x, y, z = S[i - 1]
        S[i, 0] = x + sigma * (y - x) * dt
        S[i, 1] = y + (x * (rho - z) - y) * dt
        S[i, 2] = z + (x * y - beta * z) * dt

    # Evolution of deviation vector
    d = np.array([1e-10, 0, 0], dtype=float)
    lyap_sum = 0.0
    count = 0

    for i in range(1, steps):
        x, y, z = S[i]
        # Apply Jacobian
        jd = np.array([
            sigma * (d[1] - d[0]),
            (rho - z) * d[0] - d[1] - x * d[2],
            y * d[0] + x * d[1] - beta * d[2],
        ])
        d = d + jd * dt
        norm = np.linalg.norm(d)
        if norm > 0:
            lyap_sum += np.log(norm / 1e-10)
            d = d / norm * 1e-10
            count += 1

    return lyap_sum / (count * dt) if count > 0 else 0.0


# ─────────────────────────────────────────────
# CCT Evaluator: 5 Tests
# ─────────────────────────────────────────────

def test_gap(S, gap_ratio):
    """T1 Gap Test: Check for stop intervals."""
    # Measure actual stop interval ratio (consecutive identical states)
    if gap_ratio >= 1.0:
        return 0.0, False, "gap=1.0, fully stopped"
    if gap_ratio > 0:
        return 1.0 - gap_ratio, False, f"gap={gap_ratio:.2f}, stop intervals exist"

    diffs = np.diff(S, axis=0)
    frozen = np.sum(np.all(np.abs(diffs) < 1e-12, axis=1))
    frozen_ratio = frozen / len(diffs)

    if frozen_ratio > 0.01:
        return 1.0 - frozen_ratio, False, f"stop ratio {frozen_ratio:.1%}"

    return 1.0, True, "gap=0, no stop intervals"


def test_loop(S, threshold=0.5):
    """T2 Loop Test: Check for exact trajectory repetition.

    Chaotic systems can have high ACF but don't exactly repeat.
    Real "loops" are when trajectories return exactly to previous states.
    Method: Measure recurrence ratio in state space.
    """
    n = len(S)
    if n < 100:
        return 0.0, False, "Insufficient data"

    # Downsampling
    step = max(1, n // 5000)
    Ss = S[::step]
    ns = len(Ss)

    if np.std(Ss) < 1e-10:
        return 0.0, False, "No state change (constant)"

    # Recurrence ratio: ratio of points "very close" to past states
    # Chaos: gets close but not exactly the same → low recurrence
    # Periodic: returns exactly → high recurrence
    scale = np.std(Ss, axis=0).mean()
    eps = scale * 0.01  # 1% of overall scale

    recurrence = 0
    sample_size = min(500, ns // 2)
    rng = np.random.default_rng(42)
    indices = rng.choice(ns // 2, size=sample_size, replace=False)

    for idx in indices:
        # Find close points in sufficiently distant future (at least 100 steps)
        future = Ss[idx + max(100, ns // 10):]
        if len(future) == 0:
            continue
        dists = np.linalg.norm(future - Ss[idx], axis=1)
        if np.min(dists) < eps:
            recurrence += 1

    recurrence_ratio = recurrence / sample_size
    passed = recurrence_ratio < threshold
    score = max(0, 1.0 - recurrence_ratio)

    detail = f"Recurrence rate={recurrence_ratio:.3f}"
    if passed:
        detail += ", aperiodic"
    else:
        detail += ", periodic repetition detected"

    return score, passed, detail


def compute_entropy(data, bins=30):
    """Shannon entropy of 1D data."""
    hist, _ = np.histogram(data, bins=bins, density=True)
    hist = hist[hist > 0]
    # bin width
    width = (data.max() - data.min()) / bins if data.max() > data.min() else 1
    probs = hist * width
    probs = probs[probs > 0]
    if len(probs) == 0:
        return 0.0
    probs = probs / probs.sum()
    return -np.sum(probs * np.log(probs + 1e-15))


def test_continuity(S, threshold=0.01):
    """T3 Continuity Test: Connectivity between adjacent steps.

    Instead of MI, more direct measurement: check if changes between
    adjacent states are within "reasonable range". Too big jumps = disconnection.
    """
    diffs = np.linalg.norm(np.diff(S, axis=0), axis=1)
    n = len(diffs)

    if n < 10:
        return 0.0, False, "Insufficient data"

    # Ratio of big jumps relative to mean change
    mean_diff = np.mean(diffs)
    if mean_diff < 1e-12:
        return 0.0, False, "No state change"

    # Big jumps: more than 10x the mean
    big_jumps = np.sum(diffs > mean_diff * 10)
    # Frozen: almost no change
    frozen = np.sum(diffs < 1e-12)

    jump_ratio = big_jumps / n
    frozen_ratio = frozen / n
    disconnect_ratio = jump_ratio + frozen_ratio

    passed = disconnect_ratio < threshold
    score = max(0, 1.0 - disconnect_ratio * 10)
    score = min(1.0, score)

    detail = f"Jumps={jump_ratio:.3f}, frozen={frozen_ratio:.3f}"
    if passed:
        detail += ", connection maintained"
    else:
        detail += ", disconnection detected"

    return score, passed, detail


def test_entropy_band(S, window=500, h_min=0.3, h_max=4.5):
    """T4 Entropy Band Test: Check if H(t) stays within band."""
    x = S[:, 0]
    n = len(x)
    n_windows = n // window

    if n_windows < 2:
        return 0.0, False, "Insufficient data"

    entropies = []
    for i in range(n_windows):
        w = x[i * window:(i + 1) * window]
        if np.std(w) < 1e-12:
            entropies.append(0.0)
        else:
            entropies.append(compute_entropy(w))

    entropies = np.array(entropies)
    in_band = np.sum((entropies > h_min) & (entropies < h_max))
    ratio = in_band / len(entropies)

    h_range_str = f"H∈[{entropies.min():.2f}, {entropies.max():.2f}]"
    passed = ratio > 0.95
    score = ratio

    if passed:
        detail = f"{h_range_str}, within band"
    else:
        detail = f"{h_range_str}, out of band {1 - ratio:.1%}"

    return score, passed, detail


def test_novelty(S, window=500, threshold=0.001):
    """T5 Novelty Test: dH/dt ≠ 0 (entropy stagnation ratio)."""
    x = S[:, 0]
    n = len(x)
    n_windows = n // window

    if n_windows < 3:
        return 0.0, False, "Insufficient data"

    entropies = []
    for i in range(n_windows):
        w = x[i * window:(i + 1) * window]
        if np.std(w) < 1e-12:
            entropies.append(0.0)
        else:
            entropies.append(compute_entropy(w))

    entropies = np.array(entropies)
    dH = np.abs(np.diff(entropies))

    stagnant = np.sum(dH < threshold)
    stagnant_ratio = stagnant / len(dH) if len(dH) > 0 else 1.0

    passed = stagnant_ratio < 0.05
    score = max(0, 1.0 - stagnant_ratio)

    detail = f"Stagnation intervals {stagnant_ratio:.1%}"

    return score, passed, detail


def run_cct(S, gap_ratio):
    """Run 5 CCT tests, return results."""
    results = {}
    results["T1_Gap"] = test_gap(S, gap_ratio)
    results["T2_Loop"] = test_loop(S)
    results["T3_Continuity"] = test_continuity(S)
    results["T4_Entropy"] = test_entropy_band(S)
    results["T5_Novelty"] = test_novelty(S)
    return results


# ─────────────────────────────────────────────
# Judgment Grades
# ─────────────────────────────────────────────

def judge(results):
    """Overall judgment based on CCT results."""
    passes = sum(1 for _, (_, p, _) in results.items() if p)
    halfs = sum(0.5 for _, (s, p, _) in results.items() if not p and s > 0.7)
    total = passes + halfs

    if total >= 5:
        return total, "★ Continuous"
    elif total >= 4:
        return total, "◎ Weakened"
    elif total >= 3:
        return total, "△ Weak"
    elif total >= 1:
        return total, "▽ Minimal"
    else:
        return total, "✕ None"


# ─────────────────────────────────────────────
# ASCII Output
# ─────────────────────────────────────────────

def ascii_trajectory(S, width=60, height=15):
    """ASCII trajectory of x component."""
    x = S[:, 0]
    # Downsample
    step = max(1, len(x) // width)
    xs = x[::step][:width]

    y_min, y_max = xs.min(), xs.max()
    if y_max - y_min < 1e-6:
        y_max = y_min + 1

    lines = []
    for row in range(height, -1, -1):
        y_val = y_min + (y_max - y_min) * row / height
        line = f"{y_val:6.1f}│"
        for col in range(len(xs)):
            cell_row = int((xs[col] - y_min) / (y_max - y_min) * height)
            if cell_row == row:
                line += "*"
            elif row == height // 2 and col == 0:
                line += "─"
            else:
                line += " "
        lines.append(line)

    lines.append("      └" + "─" * len(xs))
    return "\n".join(lines)


def print_single(name, params, S, results, lyap):
    """Print single system results."""
    total, verdict = judge(results)
    desc = params.get("description", name)

    print("═" * 60)
    print(" Consciousness Continuity Calculator v1.0")
    print("═" * 60)
    print()
    print(f" System: {name} ({desc})")
    print(f" Parameters: σ={params['sigma']} ρ={params['rho']} "
          f"β={params['beta']} noise={params['noise']} gap={params['gap_ratio']}")
    print(f" Simulation: {len(S):,} steps")
    print()
    print(" ─── Trajectory (x component) " + "─" * 30)
    print(ascii_trajectory(S))
    print()
    print(" ─── CCT Evaluation " + "─" * 39)

    labels = {
        "T1_Gap": "T1 Gap       ",
        "T2_Loop": "T2 Loop      ",
        "T3_Continuity": "T3 Continuity",
        "T4_Entropy": "T4 Entropy   ",
        "T5_Novelty": "T5 Novelty   ",
    }

    for key, label in labels.items():
        score, passed, detail = results[key]
        mark = "✔" if passed else ("△" if score > 0.7 else "✕")
        status = "PASS" if passed else "FAIL"
        print(f" {label} │ {mark} {status} │ {score:.3f} │ {detail}")

    print(" " + "─" * 58)
    print(f" Overall: {total}/5 {verdict}")
    print()

    if lyap is not None:
        sign = "✔ (chaotic)" if lyap > 0 else "✕ (non-chaotic)"
        print(f" Lyapunov exponent: λ₁ = {lyap:.3f} {sign}")

    print("═" * 60)


def print_all(all_results):
    """Print comparison table for all systems."""
    print("═" * 70)
    print(" Consciousness Continuity Calculator v1.0")
    print(" All Systems Comparison")
    print("═" * 70)
    print()
    print(" System           │ T1  │ T2  │ T3  │ T4  │ T5  │ Score │ Verdict")
    print(" ─────────────────┼─────┼─────┼─────┼─────┼─────┼───────┼─────────")

    for name, (results, _) in all_results.items():
        total, verdict = judge(results)
        desc = PRESETS[name]["description"]

        marks = []
        for key in ["T1_Gap", "T2_Loop", "T3_Continuity", "T4_Entropy", "T5_Novelty"]:
            score, passed, _ = results[key]
            if passed:
                marks.append(" ✔ ")
            elif score > 0.7:
                marks.append(" △ ")
            else:
                marks.append(" ✕ ")

        display_name = f"{name:17s}"
        marks_str = "│".join(marks)
        print(f" {display_name}│{marks_str}│ {total:<5} │ {verdict}")

    print()
    print(" ★=5/5  ◎=4+  △=3  ▽=1~2  ✕=0")
    print("═" * 70)


# ─────────────────────────────────────────────
# matplotlib Output
# ─────────────────────────────────────────────

def plot_results(name, params, t, S, results, lyap):
    """Save 4-panel matplotlib graph."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    except ImportError:
        print("  [Warning] matplotlib not available, skipping --plot")
        return None

    fig = plt.figure(figsize=(14, 10))
    fig.suptitle(
        f"CCT: {name} ({params.get('description', '')})",
        fontsize=14, fontweight="bold",
    )

    # 1. 3D attractor trajectory
    ax1 = fig.add_subplot(2, 2, 1, projection="3d")
    step = max(1, len(S) // 5000)
    ax1.plot(S[::step, 0], S[::step, 1], S[::step, 2],
             lw=0.3, alpha=0.7, color="royalblue")
    ax1.set_xlabel("x (sense)")
    ax1.set_ylabel("y (predict)")
    ax1.set_zlabel("z (memory)")
    ax1.set_title("Attractor Trajectory")

    # 2. H(t) time series
    ax2 = fig.add_subplot(2, 2, 2)
    window = 500
    n_w = len(S) // window
    entropies = []
    for i in range(n_w):
        w = S[i * window:(i + 1) * window, 0]
        entropies.append(compute_entropy(w) if np.std(w) > 1e-12 else 0.0)
    t_h = np.arange(n_w) * window
    ax2.plot(t_h, entropies, color="darkorange", lw=1)
    ax2.axhline(0.3, color="red", ls="--", alpha=0.5, label="H_min")
    ax2.axhline(4.5, color="red", ls="--", alpha=0.5, label="H_max")
    ax2.set_xlabel("Step")
    ax2.set_ylabel("Entropy H(t)")
    ax2.set_title("Entropy Band")
    ax2.legend(fontsize=8)

    # 3. Adjacent change time series (continuity indicator)
    ax3 = fig.add_subplot(2, 2, 3)
    diffs = np.linalg.norm(np.diff(S, axis=0), axis=1)
    diff_step = max(1, len(diffs) // 2000)
    diffs_ds = diffs[::diff_step]
    t_diff = np.arange(len(diffs_ds)) * diff_step
    mean_diff = np.mean(diffs)
    ax3.plot(t_diff, diffs_ds, color="seagreen", lw=0.5, alpha=0.7)
    ax3.axhline(mean_diff * 10, color="red", ls="--", alpha=0.5, label="jump threshold")
    ax3.set_xlabel("Step")
    ax3.set_ylabel("‖ΔS‖")
    ax3.set_title("Continuity (Step Diffs)")
    ax3.legend(fontsize=8)

    # 4. CCT radar chart
    ax4 = fig.add_subplot(2, 2, 4, polar=True)
    labels_r = ["T1\nGap", "T2\nLoop", "T3\nCont.", "T4\nEntropy", "T5\nNovelty"]
    keys = ["T1_Gap", "T2_Loop", "T3_Continuity", "T4_Entropy", "T5_Novelty"]
    scores = [results[k][0] for k in keys]
    angles = np.linspace(0, 2 * np.pi, len(labels_r), endpoint=False).tolist()
    scores_plot = scores + [scores[0]]
    angles += [angles[0]]
    ax4.fill(angles, scores_plot, alpha=0.25, color="royalblue")
    ax4.plot(angles, scores_plot, color="royalblue", lw=2)
    ax4.set_xticks(angles[:-1])
    ax4.set_xticklabels(labels_r, fontsize=8)
    ax4.set_ylim(0, 1.1)
    ax4.set_title("CCT Scores", pad=20)

    total, verdict = judge(results)
    lyap_str = f"λ₁={lyap:.3f}" if lyap is not None else ""
    fig.text(0.5, 0.02, f"Score: {total}/5 {verdict}  {lyap_str}",
             ha="center", fontsize=12, fontweight="bold")

    plt.tight_layout(rect=[0, 0.04, 1, 0.96])

    os.makedirs(RESULTS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(RESULTS_DIR, f"consciousness_calc_{name}_{ts}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def run_system(name, params, steps, dt, do_plot=False):
    """Run system simulation + CCT."""
    t, S = lorenz_simulate(
        sigma=params["sigma"],
        rho=params["rho"],
        beta=params["beta"],
        noise=params["noise"],
        gap_ratio=params["gap_ratio"],
        steps=steps,
        dt=dt,
    )

    results = run_cct(S, params["gap_ratio"])

    # Lyapunov (excluding stopped systems)
    lyap = None
    if params["sigma"] > 0 and params["rho"] > 0:
        lyap = lyapunov_exponent(params["sigma"], params["rho"], params["beta"], dt)

    plot_path = None
    if do_plot:
        plot_path = plot_results(name, params, t, S, results, lyap)

    return results, lyap, plot_path


def main():
    parser = argparse.ArgumentParser(
        description="Consciousness Continuity Calculator — Lorenz Attractor + CCT Evaluation",
    )
    parser.add_argument("--system", type=str, default=None,
                        help=f"Preset: {', '.join(PRESETS.keys())}")
    parser.add_argument("--all", action="store_true",
                        help="Compare all 7 presets")
    parser.add_argument("--sigma", type=float, default=None)
    parser.add_argument("--rho", type=float, default=None)
    parser.add_argument("--beta", type=float, default=None)
    parser.add_argument("--noise", type=float, default=None)
    parser.add_argument("--gap", type=float, default=None,
                        help="Stop interval ratio 0~1")
    parser.add_argument("--steps", type=int, default=100000)
    parser.add_argument("--dt", type=float, default=0.01)
    parser.add_argument("--plot", action="store_true",
                        help="Save matplotlib 4-panel graph")

    args = parser.parse_args()

    if args.all:
        all_results = {}
        for name, preset in PRESETS.items():
            params = dict(preset)
            results, lyap, _ = run_system(name, params, args.steps, args.dt, do_plot=args.plot)
            all_results[name] = (results, lyap)
            if args.plot:
                print(f"  [plot] {name} saved")

        print_all(all_results)
        return

    # Single system
    if args.system:
        if args.system not in PRESETS:
            print(f"  [Error] Unknown preset: {args.system}")
            print(f"  Available: {', '.join(PRESETS.keys())}")
            sys.exit(1)
        params = dict(PRESETS[args.system])
        name = args.system
    else:
        params = {
            "sigma": 10, "rho": 28, "beta": 2.67,
            "noise": 0.1, "gap_ratio": 0.0,
            "description": "Custom",
        }
        name = "custom"

    # Custom override
    if args.sigma is not None:
        params["sigma"] = args.sigma
    if args.rho is not None:
        params["rho"] = args.rho
    if args.beta is not None:
        params["beta"] = args.beta
    if args.noise is not None:
        params["noise"] = args.noise
    if args.gap is not None:
        params["gap_ratio"] = args.gap

    results, lyap, plot_path = run_system(name, params, args.steps, args.dt, do_plot=args.plot)
    print_single(name, params, results=results, S=lorenz_simulate(
        params["sigma"], params["rho"], params["beta"],
        params["noise"], params["gap_ratio"], args.steps, args.dt,
    )[1], lyap=lyap)

    if plot_path:
        print(f"\n  [plot] Saved: {plot_path}")


if __name__ == "__main__":
    main()