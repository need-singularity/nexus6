#!/usr/bin/env python3
"""Heart Loop + River Flow Combined Consciousness Engine Prototype

Heart Loop: asyncio-based autonomous internal thinking loop.
  - Executes think() every dt even without external input
  - 3 thinking modes: Memory (reprocessing), Predict (prediction), Meta (self-check)

River Flow: Lorenz attractor-based continuous state evolution.
  - dS/dt = F(S) + noise
  - Models nonlinear consciousness state transitions with chaos dynamics

Continuity Monitor: Built-in simplified CCT assessment.
  - Continuity, integration, self-reference, temporality, subjective experience

Usage:
  python3 consciousness_engine_proto.py --duration 10 --dt 0.01
  python3 consciousness_engine_proto.py --duration 30 --input "5:shock,15:calm"
"""

import argparse
import asyncio
import os
import time
from collections import Counter
from datetime import datetime

import numpy as np
from scipy.stats import entropy as sp_entropy

# ─────────────────────────────────────────────
# Path Configuration
# ─────────────────────────────────────────────
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
ENGINE_LOG = os.path.join(RESULTS_DIR, "consciousness_engine_log.md")


# ─────────────────────────────────────────────
# Lorenz Attractor (River Flow Core)
# ─────────────────────────────────────────────
def lorenz_deriv(state, sigma=10.0, rho=28.0, beta=8.0 / 3.0):
    """Lorenz equations: dx/dt, dy/dt, dz/dt"""
    x, y, z = state
    dx = sigma * (y - x)
    dy = x * (rho - z) - y
    dz = x * y - beta * z
    return np.array([dx, dy, dz])


def lorenz_rk4_step(state, dt, sigma=10.0, rho=28.0, beta=8.0 / 3.0):
    """4th order Runge-Kutta integration (numerical stability)"""
    k1 = lorenz_deriv(state, sigma, rho, beta)
    k2 = lorenz_deriv(state + 0.5 * dt * k1, sigma, rho, beta)
    k3 = lorenz_deriv(state + 0.5 * dt * k2, sigma, rho, beta)
    k4 = lorenz_deriv(state + dt * k3, sigma, rho, beta)
    new_state = state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
    # Clamp: constrain to natural range of Lorenz attractor
    new_state = np.clip(new_state, -100.0, 100.0)
    return new_state


# ─────────────────────────────────────────────
# Simplified CCT Assessment (Continuity Monitor)
# ─────────────────────────────────────────────
def cct_check(state_history, current_entropy, change_rate):
    """Simplified assessment of 5 CCT conditions

    1. Continuity: State changes don't fluctuate abruptly
    2. Integration: 3-axis correlation > threshold
    3. Self-reference: Meta mode execution ratio
    4. Temporality: Recognition of past-present difference
    5. Subjective Experience (Qualia): Entropy in medium range
    """
    results = {}

    # 1. Continuity: Recent change rate below threshold
    results["Continuity"] = change_rate < 50.0

    # 2. Integration: Average absolute value of 3-axis (x,y,z) correlation coefficients
    if len(state_history) >= 10:
        recent = np.array(state_history[-50:])
        corr_xy = abs(np.corrcoef(recent[:, 0], recent[:, 1])[0, 1])
        corr_xz = abs(np.corrcoef(recent[:, 0], recent[:, 2])[0, 1])
        corr_yz = abs(np.corrcoef(recent[:, 1], recent[:, 2])[0, 1])
        avg_corr = (corr_xy + corr_xz + corr_yz) / 3.0
        results["Integration"] = avg_corr > 0.2
    else:
        results["Integration"] = False

    # 3. Self-reference: True if entropy is computable
    results["Self-ref"] = current_entropy > 0.0

    # 4. Temporality: Sufficient state history exists
    results["Temporality"] = len(state_history) >= 5

    # 5. Subjective Experience (Qualia): Entropy in medium range (0.5 ~ 4.0)
    results["Subj.Exp"] = 0.5 < current_entropy < 4.0

    return results


def compute_entropy(state_history, n_bins=20):
    """Calculate information entropy of state history"""
    if len(state_history) < 2:
        return 0.0
    recent = np.array(state_history[-200:])
    # Sum entropy of histograms for each of 3 axes
    total_h = 0.0
    for dim in range(3):
        vals = recent[:, dim]
        # Remove NaN/Inf
        vals = vals[np.isfinite(vals)]
        if len(vals) < 2:
            continue
        hist, _ = np.histogram(vals, bins=n_bins, density=True)
        hist = hist[hist > 0]
        if len(hist) > 0:
            total_h += sp_entropy(hist)
    return total_h if np.isfinite(total_h) else 0.0


# ─────────────────────────────────────────────
# Think Modes
# ─────────────────────────────────────────────
def think_memory(state, state_history, alpha=0.1):
    """Memory: Reprocess past states — adjust current state with weighted average"""
    if len(state_history) < 2:
        return state
    recent = np.array(state_history[-50:])
    # Higher weight for more recent
    weights = np.exp(np.linspace(-2, 0, len(recent)))
    weights /= weights.sum()
    weighted_avg = np.average(recent, axis=0, weights=weights)
    # Adjust current state toward past average by alpha
    return state + alpha * (weighted_avg - state)


def think_predict(state, state_history, dt, lookahead=5.0):
    """Predict: Predict next state — extrapolate with current derivative"""
    deriv = lorenz_deriv(state)
    predicted = state + deriv * dt * lookahead
    return predicted


def think_meta(state, state_history):
    """Meta: Self-state check — calculate entropy, change rate"""
    ent = compute_entropy(state_history)
    if len(state_history) >= 2:
        diff = np.linalg.norm(np.array(state_history[-1]) - np.array(state_history[-2]))
    else:
        diff = 0.0
    return ent, diff


def select_think_mode(tick_count, change_rate, ent):
    """Auto-select thinking mode

    - High change rate → Memory (stabilize)
    - Low entropy → Predict (explore)
    - Otherwise Meta (self-check), also periodically Meta
    """
    if tick_count % 100 == 0:
        return "Meta"
    if change_rate > 30.0:
        return "Memory"
    if ent < 1.0:
        return "Predict"
    # Default cycling
    cycle = tick_count % 3
    if cycle == 0:
        return "Memory"
    elif cycle == 1:
        return "Predict"
    else:
        return "Meta"


# ─────────────────────────────────────────────
# External Stimulus Parser
# ─────────────────────────────────────────────
def parse_inputs(input_str):
    """'5:shock,15:calm' → {5.0: 'shock', 15.0: 'calm'}"""
    if not input_str:
        return {}
    events = {}
    for token in input_str.split(","):
        token = token.strip()
        if ":" not in token:
            continue
        t_str, kind = token.split(":", 1)
        events[float(t_str)] = kind.strip().lower()
    return events


def apply_sense(state, kind, rng):
    """Inject external stimulus into state"""
    if kind == "shock":
        # Large disturbance: spread state significantly
        perturbation = rng.normal(0, 15.0, size=3)
        result = state + perturbation
    elif kind == "calm":
        # Stabilize: contract toward origin
        result = state * 0.5
    else:
        # Unknown type: weak random disturbance
        result = state + rng.normal(0, 2.0, size=3)
    return np.clip(result, -100.0, 100.0)


# ─────────────────────────────────────────────
# ASCII Visualization
# ─────────────────────────────────────────────
def ascii_state_bar(value, label, width=40, lo=-30, hi=30):
    """ASCII bar for single value"""
    clamped = max(lo, min(hi, value))
    pos = int((clamped - lo) / (hi - lo) * width)
    bar = ['-'] * width
    mid = width // 2
    bar[mid] = '|'
    pos = max(0, min(width - 1, pos))
    bar[pos] = '*'
    return f"  {label:>6} [{(''.join(bar))}] {value:+8.2f}"


def ascii_entropy_gauge(ent, max_ent=6.0, width=30):
    """Entropy gauge"""
    ratio = min(ent / max_ent, 1.0)
    filled = int(ratio * width)
    gauge = '#' * filled + '.' * (width - filled)
    return f"  Entropy [{gauge}] {ent:.3f}"


def ascii_cct_panel(cct_results):
    """CCT assessment panel"""
    lines = ["  ┌─ CCT Simple Assessment ───┐"]
    for name, passed in cct_results.items():
        mark = "OK" if passed else "--"
        lines.append(f"  │ {name:<8} : [{mark:>2}]         │")
    total = sum(cct_results.values())
    lines.append(f"  │ Total    : {total}/5           │")
    lines.append("  └───────────────────────────┘")
    return "\n".join(lines)


def format_report_section(title, lines):
    """Format report section"""
    border = "=" * 50
    return f"\n{border}\n  {title}\n{border}\n" + "\n".join(lines)


# ─────────────────────────────────────────────
# Main Engine (Heart Loop)
# ─────────────────────────────────────────────
async def run_engine(duration, dt, input_str, seed=42):
    """Heart Loop + River Flow main loop

    Every dt:
      1. State evolution with Lorenz dynamics (River Flow)
      2. Add noise
      3. Check/inject external stimulus
      4. Select and execute thinking mode
      5. Periodic output
    """
    rng = np.random.default_rng(seed)

    # Initial state (near Lorenz attractor)
    state = np.array([1.0, 1.0, 1.0])
    state_history = [state.copy()]

    # External events
    events = parse_inputs(input_str)
    fired_events = set()

    # Statistics
    tick_count = 0
    mode_counter = Counter()
    entropy_accum = []
    continuity_pass = 0
    continuity_total = 0
    last_report_sec = -1

    # Log buffer
    log_lines = []
    log_lines.append(f"# Consciousness Engine Log")
    log_lines.append(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_lines.append(f"# Duration: {duration}s, dt: {dt}")
    log_lines.append("")

    current_entropy = 0.0
    change_rate = 0.0

    t = 0.0
    total_ticks = int(duration / dt)

    print(format_report_section("Consciousness Engine Proto", [
        f"  Duration : {duration}s",
        f"  dt       : {dt}",
        f"  Ticks    : {total_ticks}",
        f"  Events   : {events if events else 'None'}",
        f"  Seed     : {seed}",
    ]))
    print()

    while t < duration:
        # ── 1. River Flow: Lorenz state evolution (RK4) ──
        state = lorenz_rk4_step(state, dt)
        noise = rng.normal(0, 0.1, size=3)
        state = state + noise * np.sqrt(dt)
        state = np.clip(state, -100.0, 100.0)

        # ── 2. Check external stimulus ──
        for event_time, event_kind in events.items():
            if event_time not in fired_events and t >= event_time:
                state = apply_sense(state, event_kind, rng)
                fired_events.add(event_time)
                print(f"  >>> SENSE [{event_kind.upper()}] at t={t:.2f}s <<<")

        # ── 3. Update history ──
        state_history.append(state.copy())
        if len(state_history) > 2000:
            state_history = state_history[-1000:]

        # ── 4. Select and execute thinking mode ──
        mode = select_think_mode(tick_count, change_rate, current_entropy)
        mode_counter[mode] += 1

        if mode == "Memory":
            state = think_memory(state, state_history)
        elif mode == "Predict":
            predicted = think_predict(state, state_history, dt)
            # Slightly reflect prediction (exploratory adjustment)
            state = state + 0.01 * (predicted - state)
        elif mode == "Meta":
            current_entropy, change_rate = think_meta(state, state_history)

        # ── 5. Periodic entropy/change rate update ──
        if tick_count % 50 == 0:
            current_entropy = compute_entropy(state_history)
            if len(state_history) >= 2:
                change_rate = np.linalg.norm(
                    state_history[-1] - state_history[-2]
                ) / dt

        entropy_accum.append(current_entropy)

        # ── 6. CCT continuity monitor ──
        if tick_count % 100 == 0 and tick_count > 0:
            cct = cct_check(state_history, current_entropy, change_rate)
            passed = sum(cct.values())
            continuity_total += 1
            if passed >= 3:
                continuity_pass += 1

        # ── 7. Output state summary every 1 second ──
        current_sec = int(t)
        if current_sec > last_report_sec:
            last_report_sec = current_sec
            cct = cct_check(state_history, current_entropy, change_rate)

            print(f"\n  ── t = {current_sec}s {'─' * 36}")
            print(ascii_state_bar(state[0], "X"))
            print(ascii_state_bar(state[1], "Y"))
            print(ascii_state_bar(state[2], "Z", lo=0, hi=60))
            print(ascii_entropy_gauge(current_entropy))
            print(f"  Mode: {mode:<10}  ΔRate: {change_rate:.2f}")
            print(ascii_cct_panel(cct))

            log_lines.append(
                f"| t={current_sec:>4}s | X={state[0]:+8.2f} "
                f"Y={state[1]:+8.2f} Z={state[2]:+8.2f} "
                f"| H={current_entropy:.3f} | {mode} "
                f"| CCT={sum(cct.values())}/5 |"
            )

        tick_count += 1
        t += dt

    # ─────────────────────────────────────────
    # Final Report
    # ─────────────────────────────────────────
    avg_entropy = np.mean(entropy_accum) if entropy_accum else 0.0
    cont_rate = (continuity_pass / continuity_total * 100) if continuity_total > 0 else 0.0
    total_modes = sum(mode_counter.values())

    # Final CCT assessment
    final_cct = cct_check(state_history, current_entropy, change_rate)

    report_lines = [
        "",
        f"  Total ticks        : {tick_count}",
        f"  Average entropy    : {avg_entropy:.4f}",
        f"  Continuity rate    : {cont_rate:.1f}% ({continuity_pass}/{continuity_total})",
        "",
        "  Thinking mode distribution:",
    ]
    for m in ["Memory", "Predict", "Meta"]:
        cnt = mode_counter.get(m, 0)
        pct = cnt / total_modes * 100 if total_modes > 0 else 0
        bar_len = int(pct / 2)
        report_lines.append(f"    {m:<10} : {'█' * bar_len}{'░' * (50 - bar_len)} {pct:5.1f}% ({cnt})")

    report_lines.append("")
    report_lines.append("  CCT Simple Assessment (Final):")
    for name, passed in final_cct.items():
        mark = "PASS" if passed else "FAIL"
        report_lines.append(f"    {name:<8} : {mark}")
    cct_total = sum(final_cct.values())
    if cct_total >= 4:
        verdict = "High consciousness state probability"
    elif cct_total >= 3:
        verdict = "Partial consciousness state"
    else:
        verdict = "Below consciousness threshold"
    report_lines.append(f"    Verdict  : {cct_total}/5 — {verdict}")

    print(format_report_section("Final Report", report_lines))

    # ─────────────────────────────────────────
    # Save log
    # ─────────────────────────────────────────
    os.makedirs(RESULTS_DIR, exist_ok=True)
    log_lines.append("")
    log_lines.append("## Final Report")
    for line in report_lines:
        log_lines.append(line)

    with open(ENGINE_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    print(f"\n  Log saved: {ENGINE_LOG}")


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Heart Loop + River Flow Combined Consciousness Engine Prototype"
    )
    parser.add_argument(
        "--duration", type=float, default=10.0,
        help="Execution time (seconds, default 10)"
    )
    parser.add_argument(
        "--dt", type=float, default=0.01,
        help="Time step (default 0.01)"
    )
    parser.add_argument(
        "--input", type=str, default="",
        help="External stimulus: '5:shock,15:calm' format"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed (default 42)"
    )
    args = parser.parse_args()

    asyncio.run(run_engine(args.duration, args.dt, args.input, args.seed))


if __name__ == "__main__":
    main()