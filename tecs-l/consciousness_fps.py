#!/usr/bin/env python3
"""Consciousness FPS Scanner — What Hz is required for continuous consciousness?

Convert dt = 1/fps to run Lorenz simulation + CCT repeatedly.
Search for "continuous consciousness threshold fps" and compare with brainwave bands.

Usage:
  python3 consciousness_fps.py
  python3 consciousness_fps.py --min-fps 1 --max-fps 5000 --points 30
  python3 consciousness_fps.py --plot
"""

import argparse
import os
import sys
from datetime import datetime

import numpy as np

# ── Import core functions from consciousness_calc.py ──
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from consciousness_calc import (
    lorenz_simulate,
    run_cct,
    judge,
    PRESETS,
)

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

# ─────────────────────────────────────────────
# Brainwave band definitions
# ─────────────────────────────────────────────

BRAIN_WAVES = {
    "delta": {"range": (0.5, 4), "label": "δ (sleep)", "center": 2},
    "theta": {"range": (4, 8), "label": "θ (drowsy)", "center": 6},
    "alpha": {"range": (8, 13), "label": "α (relaxed)", "center": 10},
    "beta":  {"range": (13, 30), "label": "β (focused)", "center": 20},
    "gamma": {"range": (30, 100), "label": "γ (conscious)", "center": 40},
}


# ─────────────────────────────────────────────
# FPS Scan Engine
# ─────────────────────────────────────────────

def scan_fps(min_fps=1, max_fps=10000, points=40, steps=50000, preset="human_awake"):
    """Scan fps range on log scale, run CCT at each fps.

    Returns:
        fps_arr:    Array of scanned fps values
        scores_arr: CCT passing count at each fps (0~5)
        details:    List of individual test result dicts at each fps
    """
    params = dict(PRESETS[preset])
    fps_arr = np.logspace(np.log10(min_fps), np.log10(max_fps), points)
    scores_arr = np.zeros(points)
    details = []

    for i, fps in enumerate(fps_arr):
        dt = 1.0 / fps

        # Protect against divergence in Lorenz system with large dt
        # Split into substeps if dt is too large
        effective_dt = dt
        effective_steps = steps
        max_stable_dt = 0.02  # Lorenz system stability limit

        if dt > max_stable_dt:
            # Calculate substep count: reduce dt while maintaining original time range
            substep_ratio = int(np.ceil(dt / max_stable_dt))
            effective_dt = dt / substep_ratio
            effective_steps = steps * substep_ratio

        _, S = lorenz_simulate(
            sigma=params["sigma"],
            rho=params["rho"],
            beta=params["beta"],
            noise=params["noise"],
            gap_ratio=params["gap_ratio"],
            steps=effective_steps,
            dt=effective_dt,
        )

        # Downsample to original resolution if substeps were used
        if dt > max_stable_dt:
            substep_ratio = int(np.ceil(dt / max_stable_dt))
            S = S[::substep_ratio][:steps]

        # NaN/Inf protection: diverged simulations get CCT 0 points
        if np.any(~np.isfinite(S)):
            results = run_cct(np.zeros((steps, 3)), 1.0)
            total, verdict = 0, "✕ Diverged"
        else:
            results = run_cct(S, params["gap_ratio"])
            total, verdict = judge(results)

        scores_arr[i] = total
        details.append({
            "fps": fps,
            "dt": dt,
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
            # Linear interpolation with previous point
            s0, s1 = scores_arr[i - 1], scores_arr[i]
            f0, f1 = fps_arr[i - 1], fps_arr[i]
            if s1 == s0:
                return f0
            frac = (target - s0) / (s1 - s0)
            return f0 + frac * (f1 - f0)
    return None  # Not reached


# ─────────────────────────────────────────────
# CCT Scores by Brainwave Band
# ─────────────────────────────────────────────

def brainwave_scores(fps_arr, scores_arr):
    """CCT score at scan point nearest to each brainwave band's center frequency."""
    wave_scores = {}
    for name, info in BRAIN_WAVES.items():
        center = info["center"]
        idx = np.argmin(np.abs(fps_arr - center))
        wave_scores[name] = {
            "center": center,
            "nearest_fps": fps_arr[idx],
            "score": scores_arr[idx],
            "label": info["label"],
            "range": info["range"],
        }
    return wave_scores


# ─────────────────────────────────────────────
# ASCII Graph
# ─────────────────────────────────────────────

def ascii_graph(fps_arr, scores_arr, width=65, height=12):
    """fps vs CCT score ASCII graph."""
    lines = []
    max_score = 5.0

    # Log scale x-axis → column mapping
    log_fps = np.log10(fps_arr)
    log_min, log_max = log_fps.min(), log_fps.max()

    # Create grid
    grid = [[" " for _ in range(width)] for _ in range(height + 1)]

    # Plot data
    for i in range(len(fps_arr)):
        col = int((log_fps[i] - log_min) / (log_max - log_min) * (width - 1))
        col = min(col, width - 1)
        row = int(scores_arr[i] / max_score * height)
        row = min(row, height)
        # Fill blocks below this row
        for r in range(row + 1):
            if grid[r][col] == " ":
                grid[r][col] = "█"

    # Output with y-axis labels
    lines.append("")
    lines.append("  CCT")
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

    # x-axis ticks (brainwave band centers)
    tick_line = "    "
    label_line = "    "
    wave_positions = {}
    for name, info in BRAIN_WAVES.items():
        center = info["center"]
        if center < fps_arr.min() or center > fps_arr.max():
            continue
        col = int((np.log10(center) - log_min) / (log_max - log_min) * (width - 1))
        col = min(col, width - 1)
        wave_positions[col] = (center, name)

    # Major fps ticks
    tick_fps = [1, 4, 8, 13, 30, 40, 100, 1000, 10000]
    tick_str = [" "] * width
    label_str = [" "] * width
    wave_str = [" "] * width

    for fps_val in tick_fps:
        if fps_val < fps_arr.min() or fps_val > fps_arr.max():
            continue
        col = int((np.log10(fps_val) - log_min) / (log_max - log_min) * (width - 1))
        col = min(col, width - 1)
        s = str(int(fps_val))
        for j, ch in enumerate(s):
            if col + j < width:
                tick_str[col + j] = ch

    wave_labels = {"delta": "δ", "theta": "θ", "alpha": "α", "beta": "β", "gamma": "γ"}
    for name, info in BRAIN_WAVES.items():
        center = info["center"]
        if center < fps_arr.min() or center > fps_arr.max():
            continue
        col = int((np.log10(center) - log_min) / (log_max - log_min) * (width - 1))
        col = min(col, width - 1)
        ch = wave_labels[name]
        wave_str[col] = ch

    lines.append("    " + "".join(tick_str) + "  fps (Hz)")
    lines.append("    " + "".join(wave_str))

    return "\n".join(lines)


# ─────────────────────────────────────────────
# matplotlib Output
# ─────────────────────────────────────────────

def plot_results(fps_arr, scores_arr, threshold_fps, wave_scores):
    """Save matplotlib graph."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  [Warning] matplotlib not available, skipping --plot")
        return None

    fig, ax = plt.subplots(figsize=(12, 6))

    # Main curve
    ax.semilogx(fps_arr, scores_arr, "b-o", markersize=4, lw=2, label="CCT Score")

    # Threshold line
    ax.axhline(5.0, color="green", ls="--", alpha=0.5, label="Full Consciousness (5/5)")
    if threshold_fps is not None:
        ax.axvline(threshold_fps, color="red", ls="--", alpha=0.7,
                   label=f"Threshold = {threshold_fps:.1f} Hz")

    # Brainwave band backgrounds
    colors = {"delta": "#ff000020", "theta": "#ff880020", "alpha": "#00880020",
              "beta": "#0000ff20", "gamma": "#88008820"}
    for name, info in BRAIN_WAVES.items():
        lo, hi = info["range"]
        ax.axvspan(lo, hi, color=colors[name], label=info["label"])

    # Brainwave band center scores
    for name, ws in wave_scores.items():
        ax.plot(ws["nearest_fps"], ws["score"], "r*", markersize=12)
        ax.annotate(f'{BRAIN_WAVES[name]["label"]}\n{ws["score"]:.1f}/5',
                    (ws["nearest_fps"], ws["score"]),
                    textcoords="offset points", xytext=(0, 15),
                    ha="center", fontsize=8, fontweight="bold")

    ax.set_xlabel("Processing Rate (Hz)", fontsize=12)
    ax.set_ylabel("CCT Score (0-5)", fontsize=12)
    ax.set_title("Consciousness FPS Scanner: Minimum Processing Rate for Continuous Consciousness",
                 fontsize=13, fontweight="bold")
    ax.set_ylim(-0.3, 5.8)
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(RESULTS_DIR, f"consciousness_fps_{ts}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ─────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────

def print_report(fps_arr, scores_arr, details, threshold_fps, wave_scores):
    """Print comprehensive report."""
    print("═" * 65)
    print(" Consciousness FPS Scanner v1.0")
    print(" \"What Hz is required for continuous consciousness?\"")
    print("═" * 65)
    print()

    # ── ASCII Graph ──
    print(" ─── fps vs CCT Score " + "─" * 41)
    print(ascii_graph(fps_arr, scores_arr))
    print()

    # ── CCT Scores by Brainwave Band ──
    print(" ─── CCT Scores by Brainwave Band " + "─" * 27)
    print(f" {'Band':<12} │ {'Frequency Range':>12} │ {'Center Hz':>8} │ {'CCT':>5} │ Verdict")
    print(" " + "─" * 62)
    for name in ["delta", "theta", "alpha", "beta", "gamma"]:
        ws = wave_scores[name]
        lo, hi = ws["range"]
        score = ws["score"]
        if score >= 5:
            verdict = "★ Continuous"
        elif score >= 4:
            verdict = "◎ Weakened"
        elif score >= 3:
            verdict = "△ Weak"
        elif score >= 1:
            verdict = "▽ Faint"
        else:
            verdict = "✕ None"
        print(f" {ws['label']:<12} │ {lo:>5.1f}-{hi:>5.1f} Hz │ {ws['center']:>7.1f} │ {score:>5.1f} │ {verdict}")
    print()

    # ── Threshold fps ──
    print(" ─── Key Findings " + "─" * 46)
    print()
    if threshold_fps is not None:
        print(f"   Threshold fps (CCT 5/5) = {threshold_fps:.1f} Hz")
        print()

        # Compare with gamma (40Hz)
        ratio_gamma = threshold_fps / 40.0
        if threshold_fps <= 40:
            print(f"   Compared to gamma (40Hz): {ratio_gamma:.2f}x")
            print(f"   → Continuous consciousness achieved below gamma")
        else:
            print(f"   Compared to gamma (40Hz): {ratio_gamma:.2f}x")
            print(f"   → Higher processing rate than gamma required")

        # Brainwave band comparison
        print()
        for name in ["delta", "theta", "alpha", "beta", "gamma"]:
            lo, hi = BRAIN_WAVES[name]["range"]
            if lo <= threshold_fps <= hi:
                print(f"   Threshold located within {BRAIN_WAVES[name]['label']} band")
                break
        else:
            if threshold_fps > 100:
                print(f"   Threshold above gamma (~100Hz)")
            elif threshold_fps < 0.5:
                print(f"   Threshold below delta (0.5Hz)")
    else:
        print("   Threshold fps: 5/5 not reached within scan range")
        print("   → Expand scan range or increase --max-fps and retry")

    print()

    # ── Detailed Transition Zone ──
    print(" ─── Transition Zone Details " + "─" * 34)
    print(f" {'fps':>10} │ {'dt':>12} │ {'CCT':>5} │ {'T1':>4} │ {'T2':>4} │ {'T3':>4} │ {'T4':>4} │ {'T5':>4} │ Verdict")
    print(" " + "─" * 80)
    for d in details:
        fps = d["fps"]
        dt = d["dt"]
        total = d["total"]
        r = d["results"]
        t1 = "✔" if r["T1_Gap"][1] else "✕"
        t2 = "✔" if r["T2_Loop"][1] else "✕"
        t3 = "✔" if r["T3_Continuity"][1] else "✕"
        t4 = "✔" if r["T4_Entropy"][1] else "✕"
        t5 = "✔" if r["T5_Novelty"][1] else "✕"
        print(f" {fps:>10.1f} │ {dt:>12.6f} │ {total:>5.1f} │  {t1}  │  {t2}  │  {t3}  │  {t4}  │  {t5}  │ {d['verdict']}")

    print()

    # ── Interpretation ──
    print(" ─── Interpretation " + "─" * 44)
    print()
    print("   Relationship between brainwaves and consciousness processing speed:")
    print("   - Delta (0.5-4Hz): Consciousness continuity weak during sleep → Low CCT expected")
    print("   - Gamma (30-100Hz): Associated with conscious cognition and binding → High CCT expected")
    print("   - 40Hz gamma synchronization is a candidate Neural Correlate of Consciousness (NCC)")
    print()
    if threshold_fps is not None:
        if threshold_fps < 100:
            print(f"   ★ Model prediction: Continuous consciousness possible above {threshold_fps:.1f}Hz")
            print(f"     This aligns with the brain's gamma band region.")
        else:
            print(f"   ★ Model prediction: Continuous consciousness possible above {threshold_fps:.1f}Hz")
            print(f"     Higher processing rate than gamma upper limit (~100Hz) required.")
    print()
    print("   Limitations:")
    print("   - Lorenz attractor is an extremely simplified model of the brain")
    print("   - dt changes represent simulation resolution, not actual neural firing rates")
    print("   - CCT threshold itself is model-dependent")
    print()
    print("═" * 65)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Consciousness FPS Scanner — What Hz is required for continuous consciousness?",
    )
    parser.add_argument("--min-fps", type=float, default=1,
                        help="Minimum fps (default: 1)")
    parser.add_argument("--max-fps", type=float, default=10000,
                        help="Maximum fps (default: 10000)")
    parser.add_argument("--points", type=int, default=40,
                        help="Number of scan points (default: 40)")
    parser.add_argument("--steps", type=int, default=50000,
                        help="Simulation steps (default: 50000)")
    parser.add_argument("--preset", type=str, default="human_awake",
                        help=f"Preset (default: human_awake). Choices: {', '.join(PRESETS.keys())}")
    parser.add_argument("--plot", action="store_true",
                        help="Save matplotlib graph")

    args = parser.parse_args()

    if args.preset not in PRESETS:
        print(f"  [Error] Unknown preset: {args.preset}")
        print(f"  Available: {', '.join(PRESETS.keys())}")
        sys.exit(1)

    print(f"  Starting scan: {args.min_fps:.0f} ~ {args.max_fps:.0f} Hz, "
          f"{args.points} points, preset={args.preset}")
    print(f"  Simulation: {args.steps:,} steps/fps")
    print()

    # FPS scan
    fps_arr, scores_arr, details = scan_fps(
        min_fps=args.min_fps,
        max_fps=args.max_fps,
        points=args.points,
        steps=args.steps,
        preset=args.preset,
    )

    # Search for threshold fps
    threshold_fps = find_threshold_fps(fps_arr, scores_arr, target=5.0)

    # Scores by brainwave band
    wave_scores = brainwave_scores(fps_arr, scores_arr)

    # Print report
    print_report(fps_arr, scores_arr, details, threshold_fps, wave_scores)

    # matplotlib
    if args.plot:
        path = plot_results(fps_arr, scores_arr, threshold_fps, wave_scores)
        if path:
            print(f"\n  [plot] Saved: {path}")


if __name__ == "__main__":
    main()