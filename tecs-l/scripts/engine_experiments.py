#!/usr/bin/env python3
"""Engine experiments 11, 12, 13 — Sleep-wake cycles, Multi-engine, Memory erasure

Experiment 11: Sleep-wake cycles (I(t) time variation)
Experiment 12: Multi-engine interaction (coupled Lorenz)
Experiment 13: Memory erasure (state reset and CCT recovery)

Usage:
  python3 engine_experiments.py --sleep-wake     # Experiment 11
  python3 engine_experiments.py --multi-engine   # Experiment 12
  python3 engine_experiments.py --memory-erase   # Experiment 13
  python3 engine_experiments.py --all            # All
"""

import sys, os

import argparse
import sys

import numpy as np

from consciousness_calc import (
    compute_entropy,
    lorenz_simulate,
    run_cct,
    judge,
)

# ─────────────────────────────────────────────
# Utils: ASCII graphs
# ─────────────────────────────────────────────

def ascii_dual_plot(t_vals, y1, y2, label1="I(t)", label2="CCT",
                    width=70, height=18):
    """Overlay two time series in ASCII."""
    # Downsample
    n = len(t_vals)
    step = max(1, n // width)
    ts = t_vals[::step][:width]
    ys1 = y1[::step][:width]
    ys2 = y2[::step][:width]
    w = len(ts)

    y_min = min(ys1.min(), ys2.min())
    y_max = max(ys1.max(), ys2.max())
    if y_max - y_min < 1e-6:
        y_max = y_min + 1.0

    lines = []
    for row in range(height, -1, -1):
        y_val = y_min + (y_max - y_min) * row / height
        line = f"{y_val:5.2f}|"
        for col in range(w):
            r1 = int((ys1[col] - y_min) / (y_max - y_min) * height)
            r2 = int((ys2[col] - y_min) / (y_max - y_min) * height)
            if r1 == row and r2 == row:
                line += "X"
            elif r1 == row:
                line += "o"
            elif r2 == row:
                line += "*"
            else:
                line += " "
        lines.append(line)
    lines.append("     +" + "-" * w)
    lines.append(f"      {label1}=o  {label2}=*  overlap=X")
    lines.append(f"      t: {ts[0]:.0f} ~ {ts[-1]:.0f}")
    return "\n".join(lines)


def ascii_bar(labels, values, width=40, title=""):
    """Simple horizontal bar chart."""
    lines = []
    if title:
        lines.append(title)
        lines.append("-" * (width + 20))
    v_max = max(abs(v) for v in values) if values else 1.0
    if v_max < 1e-12:
        v_max = 1.0
    for lab, val in zip(labels, values):
        bar_len = int(abs(val) / v_max * width)
        bar = "#" * bar_len
        lines.append(f"  {lab:>16s} | {bar:<{width}s} {val:.3f}")
    return "\n".join(lines)


# ─────────────────────────────────────────────
# I(t) profile generation
# ─────────────────────────────────────────────

def make_inhibition_profile(steps):
    """Generate sleep-wake I(t) profile.

    0~2000:     I=0.35 (awake)
    2000~4000:  I 0.35->0.6 (drowsy->sleep onset)
    4000~6000:  I=0.6 (deep sleep)
    6000~8000:  I 0.6->0.35 (awakening)
    8000~10000: I=0.35 (awake)
    """
    I = np.zeros(steps)
    for i in range(steps):
        t = i / steps * 10000  # Normalize to 0~10000 scale
        if t < 2000:
            I[i] = 0.35
        elif t < 4000:
            frac = (t - 2000) / 2000
            I[i] = 0.35 + 0.25 * frac
        elif t < 6000:
            I[i] = 0.60
        elif t < 8000:
            frac = (t - 6000) / 2000
            I[i] = 0.60 - 0.25 * frac
        else:
            I[i] = 0.35
    return I


def inhibition_to_params(I_val):
    """Map I(t) value to Lorenz parameters."""
    sigma = 10.0 * (1.0 - I_val)
    rho = 28.0 * (1.0 - I_val / 2.0)
    noise = 0.3 * (1.0 - I_val)
    gap = max(0.0, (I_val - 0.5) * 2.0)
    return sigma, rho, noise, gap


# ─────────────────────────────────────────────
# Experiment 11: Sleep-wake cycles
# ─────────────────────────────────────────────

def lorenz_simulate_variable_I(I_profile, beta=2.67, dt=0.01, seed=42):
    """Extended Lorenz simulator with time-varying I(t)."""
    steps = len(I_profile)
    rng = np.random.default_rng(seed)
    t = np.arange(steps) * dt
    S = np.zeros((steps, 3))
    S[0] = [1.0, 1.0, 1.0]

    for i in range(1, steps):
        sigma, rho, noise, gap = inhibition_to_params(I_profile[i])

        # Stop with gap probability
        if gap > 0 and rng.random() < gap:
            S[i] = S[i - 1]
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


def experiment_sleep_wake(steps=10000, dt=0.01):
    """Experiment 11: Sleep-wake cycles."""
    print("=" * 70)
    print(" Experiment 11: Sleep-wake cycles")
    print("=" * 70)
    print()
    print(" I(t) profile:")
    print("   0~2000:     I=0.35 (awake)")
    print("   2000~4000:  I=0.35->0.60 (drowsy->sleep onset)")
    print("   4000~6000:  I=0.60 (deep sleep)")
    print("   6000~8000:  I=0.60->0.35 (awakening)")
    print("   8000~10000: I=0.35 (awake)")
    print()
    print(" Mapping: sigma=10*(1-I), rho=28*(1-I/2), noise=0.3*(1-I),")
    print("          gap=max(0,(I-0.5)*2)")
    print()

    I_profile = make_inhibition_profile(steps)
    t, S = lorenz_simulate_variable_I(I_profile, dt=dt)

    # Segment division: 5 segments
    segments = [
        ("Awake1 (0-2000)", 0, int(steps * 0.2)),
        ("Transition1: Drowsy (2000-4000)", int(steps * 0.2), int(steps * 0.4)),
        ("Deep sleep (4000-6000)", int(steps * 0.4), int(steps * 0.6)),
        ("Transition2: Awakening (6000-8000)", int(steps * 0.6), int(steps * 0.8)),
        ("Awake2 (8000-10000)", int(steps * 0.8), steps),
    ]

    # Per-segment CCT calculation
    segment_ccts = []
    print(" ─── Per-segment CCT results " + "─" * 39)
    print(f" {'Segment':<28s} | {'I(t)':>6s} | {'T1':>5s} {'T2':>5s} "
          f"{'T3':>5s} {'T4':>5s} {'T5':>5s} | {'Score':>4s} | Verdict")
    print(" " + "-" * 68)

    for name, i_start, i_end in segments:
        seg_S = S[i_start:i_end]
        seg_I_mean = np.mean(I_profile[i_start:i_end])

        # gap_ratio estimation: actual frozen ratio in this segment
        diffs = np.diff(seg_S, axis=0)
        frozen = np.sum(np.all(np.abs(diffs) < 1e-12, axis=1))
        gap_est = frozen / len(diffs)

        results = run_cct(seg_S, gap_est)
        total, verdict = judge(results)

        scores = [results[k][0] for k in
                  ["T1_Gap", "T2_Loop", "T3_Continuity", "T4_Entropy", "T5_Novelty"]]

        print(f" {name:<28s} | {seg_I_mean:5.3f} | "
              f"{scores[0]:5.3f} {scores[1]:5.3f} {scores[2]:5.3f} "
              f"{scores[3]:5.3f} {scores[4]:5.3f} | {total:<4} | {verdict}")

        segment_ccts.append((name, seg_I_mean, total, verdict, scores))

    print()

    # Sliding window CCT
    window = steps // 20
    slide_step = steps // 50
    cct_timeline = []
    I_timeline = []
    t_timeline = []

    for start in range(0, steps - window, slide_step):
        end = start + window
        seg_S = S[start:end]
        seg_I = np.mean(I_profile[start:end])

        diffs = np.diff(seg_S, axis=0)
        frozen = np.sum(np.all(np.abs(diffs) < 1e-12, axis=1))
        gap_est = frozen / len(diffs)

        results = run_cct(seg_S, gap_est)
        total, _ = judge(results)

        cct_timeline.append(total)
        I_timeline.append(seg_I)
        t_timeline.append((start + end) / 2)

    cct_arr = np.array(cct_timeline, dtype=float)
    I_arr = np.array(I_timeline)
    t_arr = np.array(t_timeline)

    # ASCII graph: I(t) vs CCT(t)
    # Normalize CCT to 0~1 (to match I scale)
    cct_norm = cct_arr / 5.0
    print(" ─── I(t) vs CCT(t)/5 graph " + "─" * 41)
    print(ascii_dual_plot(t_arr, I_arr, cct_norm, label1="I(t)", label2="CCT/5"))
    print()

    # Transition segment detailed analysis
    print(" ─── Transition segment details " + "─" * 38)
    print()
    for i, (ti, ii, ci) in enumerate(zip(t_timeline, I_timeline, cct_timeline)):
        scaled_t = ti / steps * 10000
        if 1800 < scaled_t < 4200 or 5800 < scaled_t < 8200:
            marker = "<-- Transition" if (2000 < scaled_t < 4000 or 6000 < scaled_t < 8000) else ""
            print(f"   t={scaled_t:7.0f}  I={ii:.3f}  CCT={ci:.1f}/5  {marker}")

    print()
    print(" [Conclusion]")
    awake_cct = [c for _, ii, c in zip(t_timeline, I_timeline, cct_timeline)
                 if ii < 0.40]
    sleep_cct = [c for _, ii, c in zip(t_timeline, I_timeline, cct_timeline)
                 if ii > 0.55]
    if awake_cct and sleep_cct:
        print(f"   Awake average CCT: {np.mean(awake_cct):.2f}/5")
        print(f"   Sleep average CCT: {np.mean(sleep_cct):.2f}/5")
        print(f"   Difference: {np.mean(awake_cct) - np.mean(sleep_cct):.2f}")
    print("=" * 70)
    print()


# ─────────────────────────────────────────────
# Experiment 12: Multi-engine interaction
# ─────────────────────────────────────────────

def coupled_lorenz_simulate(sigma=10, rho=28, beta=2.67, noise=0.1,
                            coupling=0.0, steps=10000, dt=0.01, seed=42):
    """Coupled Lorenz simulator.

    Engine A: dx_a/dt = sigma*(y_a - x_a) + coupling*(x_b - x_a)
    Engine B: dx_b/dt = sigma*(y_b - x_b) + coupling*(x_a - x_b)
    y, z are independent Lorenz for each.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(steps) * dt

    # State: [x_a, y_a, z_a, x_b, y_b, z_b]
    S = np.zeros((steps, 6))
    S[0] = [1.0, 1.0, 1.0, -1.0, -1.0, 1.0]  # Different initial conditions

    for i in range(1, steps):
        xa, ya, za, xb, yb, zb = S[i - 1]

        # Engine A
        dxa = sigma * (ya - xa) + coupling * (xb - xa)
        dya = xa * (rho - za) - ya
        dza = xa * ya - beta * za

        # Engine B
        dxb = sigma * (yb - xb) + coupling * (xa - xb)
        dyb = xb * (rho - zb) - yb
        dzb = xb * yb - beta * zb

        eps = rng.normal(0, noise, 6) if noise > 0 else np.zeros(6)

        S[i, 0] = xa + (dxa + eps[0]) * dt
        S[i, 1] = ya + (dya + eps[1]) * dt
        S[i, 2] = za + (dza + eps[2]) * dt
        S[i, 3] = xb + (dxb + eps[3]) * dt
        S[i, 4] = yb + (dyb + eps[4]) * dt
        S[i, 5] = zb + (dzb + eps[5]) * dt

    return t, S


def measure_sync(S):
    """Measure synchronization between two engines (correlation coefficient)."""
    xa = S[:, 0]
    xb = S[:, 3]
    if np.std(xa) < 1e-12 or np.std(xb) < 1e-12:
        return 0.0
    corr = np.corrcoef(xa, xb)[0, 1]
    return corr


def experiment_multi_engine(steps=10000, dt=0.01):
    """Experiment 12: Multi-engine interaction."""
    print("=" * 70)
    print(" Experiment 12: Multi-engine interaction")
    print("=" * 70)
    print()
    print(" Coupling equations:")
    print("   Engine A: dx_a/dt = sigma*(y_a-x_a) + coupling*(x_b-x_a)")
    print("   Engine B: dx_b/dt = sigma*(y_b-x_b) + coupling*(x_a-x_b)")
    print()
    print(" Questions: Do two consciousnesses synchronize when communicating? Do new attractors emerge?")
    print()

    couplings = [0.0, 0.1, 0.5, 1.0, 5.0]

    print(f" {'coupling':>10s} | {'CCT_A':>6s} {'CCT_B':>6s} {'CCT_AB':>6s} | "
          f"{'Sync':>6s} | {'H_A':>6s} {'H_B':>6s} {'H_AB':>6s} | Note")
    print(" " + "-" * 78)

    results_table = []

    for c in couplings:
        t, S = coupled_lorenz_simulate(coupling=c, steps=steps, dt=dt)

        S_a = S[:, :3]   # Engine A
        S_b = S[:, 3:]   # Engine B

        # Individual CCT
        cct_a = run_cct(S_a, 0.0)
        cct_b = run_cct(S_b, 0.0)
        # Combined 6D CCT (adapted to 3D functions: use first 3 components)
        # To view all 6 dimensions, calculate entropy separately
        cct_ab = run_cct(S_a, 0.0)  # Basic structure

        total_a, verdict_a = judge(cct_a)
        total_b, verdict_b = judge(cct_b)

        # Combined system CCT: calculate T3, T4, T5 directly for 6D state
        # T3: 6D continuity
        diffs_6d = np.linalg.norm(np.diff(S, axis=0), axis=1)
        mean_diff_6d = np.mean(diffs_6d)
        big_jumps_6d = np.sum(diffs_6d > mean_diff_6d * 10) / len(diffs_6d)
        # T4: 6D entropy (x_a + x_b)
        combined_x = S[:, 0] + S[:, 3]
        h_combined = compute_entropy(combined_x, bins=30)
        # Individual entropies
        h_a = compute_entropy(S[:, 0], bins=30)
        h_b = compute_entropy(S[:, 3], bins=30)

        # Combined CCT score: average of individuals + sync bonus
        total_ab_raw = (total_a + total_b) / 2.0
        sync = measure_sync(S)

        # High sync means combined system acts as one
        if abs(sync) > 0.9:
            note = "Complete sync"
        elif abs(sync) > 0.5:
            note = "Partial sync"
        elif abs(sync) > 0.2:
            note = "Weak coupling"
        else:
            note = "Independent"

        print(f" {c:10.1f} | {total_a:6.1f} {total_b:6.1f} "
              f"{total_ab_raw:6.1f} | {sync:6.3f} | "
              f"{h_a:6.3f} {h_b:6.3f} {h_combined:6.3f} | {note}")

        results_table.append((c, total_a, total_b, total_ab_raw, sync,
                              h_a, h_b, h_combined, note))

    print()

    # Sync vs coupling ASCII graph
    labels = [f"c={c:.1f}" for c in couplings]
    syncs = [r[4] for r in results_table]
    print(ascii_bar(labels, syncs, title=" Synchronization (correlation) vs coupling"))
    print()

    # CCT vs coupling
    ccts_a = [r[1] for r in results_table]
    print(ascii_bar(labels, ccts_a, title=" CCT_A vs coupling"))
    print()

    # Conclusion
    print(" [Conclusion]")
    sync_values = [abs(r[4]) for r in results_table]
    if sync_values[-1] > 0.8:
        print("   -> Complete synchronization achieved at strong coupling")
        print("   -> Two attractors converge to one (consciousness fusion?)")
    elif sync_values[-1] > 0.3:
        print("   -> Only partial synchronization even at strong coupling")
        print("   -> Each engine maintains uniqueness while interacting")
    else:
        print("   -> Independent operation despite coupling")

    h_growth = [r[7] for r in results_table]
    if h_growth[-1] > h_growth[0] * 1.1:
        print("   -> Entropy increase with coupling: new complexity emerges")
    elif h_growth[-1] < h_growth[0] * 0.9:
        print("   -> Entropy decrease with coupling: simplification due to sync")
    else:
        print("   -> Similar entropy before/after coupling: information preserved")

    print("=" * 70)
    print()


# ─────────────────────────────────────────────
# Experiment 13: Memory erasure
# ─────────────────────────────────────────────

def lorenz_simulate_with_reset(sigma=10, rho=28, beta=2.67, noise=0.1,
                               steps=10000, dt=0.01, reset_point=0.5,
                               reset_strength=1.0, seed=42):
    """Memory erasure simulator.

    reset_point: Reset time (0~1, ratio to total steps)
    reset_strength: Reset strength (0=no erasure, 1=complete erasure)
    """
    rng = np.random.default_rng(seed)
    t = np.arange(steps) * dt
    S = np.zeros((steps, 3))
    S[0] = [1.0, 1.0, 1.0]

    reset_idx = int(steps * reset_point)

    for i in range(1, steps):
        # Reset point
        if i == reset_idx:
            current = S[i - 1].copy()
            random_state = rng.uniform(-30, 30, 3)
            S[i - 1] = current * (1 - reset_strength) + random_state * reset_strength

        x, y, z = S[i - 1]
        dx = sigma * (y - x)
        dy = x * (rho - z) - y
        dz = x * y - beta * z

        eps = rng.normal(0, noise, 3) if noise > 0 else np.zeros(3)

        S[i, 0] = x + (dx + eps[0]) * dt
        S[i, 1] = y + (dy + eps[1]) * dt
        S[i, 2] = z + (dz + eps[2]) * dt

    return t, S, reset_idx


def measure_recovery_time(S, reset_idx, window=200, threshold=0.8):
    """Measure steps to CCT recovery after reset."""
    steps = len(S)

    # CCT baseline from last segment before reset
    pre_start = max(0, reset_idx - window)
    pre_S = S[pre_start:reset_idx]
    if len(pre_S) < 100:
        return -1, 0.0

    diffs_pre = np.diff(pre_S, axis=0)
    frozen_pre = np.sum(np.all(np.abs(diffs_pre) < 1e-12, axis=1))
    gap_pre = frozen_pre / len(diffs_pre)
    pre_results = run_cct(pre_S, gap_pre)
    pre_total, _ = judge(pre_results)

    if pre_total < 1:
        return -1, pre_total

    target = pre_total * threshold

    # Track CCT recovery after reset with sliding window
    for offset in range(0, steps - reset_idx - window, window // 4):
        start = reset_idx + offset
        end = start + window
        if end > steps:
            break
        seg_S = S[start:end]
        diffs = np.diff(seg_S, axis=0)
        frozen = np.sum(np.all(np.abs(diffs) < 1e-12, axis=1))
        gap_est = frozen / len(diffs)
        results = run_cct(seg_S, gap_est)
        total, _ = judge(results)

        if total >= target:
            return offset, total

    return -1, 0.0


def experiment_memory_erase(steps=10000, dt=0.01):
    """Experiment 13: Memory erasure."""
    print("=" * 70)
    print(" Experiment 13: Memory erasure")
    print("=" * 70)
    print()
    print(" Method:")
    print("   - First half: Normal Lorenz simulation")
    print("   - Middle (50%): Reset state to random values (memory erasure)")
    print("   - Second half: Continue from reset state")
    print()
    print(" Reset strength: 10%, 50%, 100% (partial~complete erasure)")
    print()

    strengths = [0.1, 0.5, 1.0]
    strength_labels = ["10% (partial)", "50% (medium)", "100% (complete)"]

    print(f" {'Strength':<16s} | {'pre-CCT':>8s} {'post-CCT':>9s} {'drop':>6s} | "
          f"{'Recovery time':>12s} | {'T3 pre':>7s} {'T3 post':>8s} | Note")
    print(" " + "-" * 86)

    all_results = []

    for strength, label in zip(strengths, strength_labels):
        t, S, reset_idx = lorenz_simulate_with_reset(
            steps=steps, dt=dt, reset_strength=strength
        )

        # Pre-reset CCT
        window = steps // 5
        pre_start = max(0, reset_idx - window)
        pre_S = S[pre_start:reset_idx]
        diffs_pre = np.diff(pre_S, axis=0)
        frozen_pre = np.sum(np.all(np.abs(diffs_pre) < 1e-12, axis=1))
        gap_pre = frozen_pre / len(diffs_pre)
        pre_results = run_cct(pre_S, gap_pre)
        pre_total, pre_verdict = judge(pre_results)
        pre_t3 = pre_results["T3_Continuity"][0]

        # Post-reset CCT (including reset point)
        post_end = min(reset_idx + window, steps)
        post_S = S[reset_idx:post_end]
        diffs_post = np.diff(post_S, axis=0)
        frozen_post = np.sum(np.all(np.abs(diffs_post) < 1e-12, axis=1))
        gap_post = frozen_post / len(diffs_post)
        post_results = run_cct(post_S, gap_post)
        post_total, post_verdict = judge(post_results)
        post_t3 = post_results["T3_Continuity"][0]

        # Recovery time
        recovery_steps, recovered_cct = measure_recovery_time(
            S, reset_idx, window=window
        )

        drop = pre_total - post_total

        if recovery_steps >= 0:
            recovery_str = f"{recovery_steps:>6d}st"
        else:
            recovery_str = "Not recovered"

        if drop > 2:
            note = "Severe consciousness break"
        elif drop > 1:
            note = "Partial break"
        elif drop > 0:
            note = "Minor impact"
        else:
            note = "No impact"

        print(f" {label:<16s} | {pre_total:8.1f} {post_total:9.1f} "
              f"{drop:6.1f} | {recovery_str:>12s} | "
              f"{pre_t3:7.3f} {post_t3:8.3f} | {note}")

        all_results.append({
            "strength": strength,
            "label": label,
            "pre_total": pre_total,
            "post_total": post_total,
            "drop": drop,
            "recovery_steps": recovery_steps,
            "pre_t3": pre_t3,
            "post_t3": post_t3,
            "t": t, "S": S, "reset_idx": reset_idx,
        })

    print()

    # 100% erasure detailed analysis: CCT timeline before/after reset
    print(" ─── 100% erasure details: CCT timeline " + "─" * 30)
    r = all_results[-1]  # 100% erasure
    S_full = r["S"]
    ridx = r["reset_idx"]

    window = steps // 10
    slide = window // 4
    cct_vals = []
    t_vals = []

    for start in range(0, steps - window, slide):
        end = start + window
        seg = S_full[start:end]
        diffs = np.diff(seg, axis=0)
        frozen = np.sum(np.all(np.abs(diffs) < 1e-12, axis=1))
        gap_est = frozen / len(diffs)
        res = run_cct(seg, gap_est)
        total, _ = judge(res)
        cct_vals.append(total)
        t_vals.append((start + end) / 2)

    cct_arr = np.array(cct_vals, dtype=float)
    t_arr = np.array(t_vals, dtype=float)

    # Array to mark reset point
    reset_line = np.zeros_like(t_arr)
    for i, tv in enumerate(t_arr):
        if abs(tv - ridx) < steps * 0.05:
            reset_line[i] = cct_arr.max()

    # ASCII graph
    w = min(60, len(t_arr))
    step_ds = max(1, len(t_arr) // w)
    ts_ds = t_arr[::step_ds][:w]
    cs_ds = cct_arr[::step_ds][:w]

    y_min, y_max = 0, 5.5
    h = 12
    lines = []
    ridx_col = -1
    for ci, tv in enumerate(ts_ds):
        if abs(tv - ridx) < steps * 0.06:
            ridx_col = ci
            break

    for row in range(h, -1, -1):
        y_val = y_min + (y_max - y_min) * row / h
        line = f"{y_val:4.1f}|"
        for col in range(len(ts_ds)):
            cr = int((cs_ds[col] - y_min) / (y_max - y_min) * h)
            if col == ridx_col:
                line += "|"
            elif cr == row:
                line += "*"
            else:
                line += " "
        lines.append(line)
    lines.append("    +" + "-" * len(ts_ds))
    if ridx_col >= 0:
        lines.append(f"     {'':>{ridx_col}}^ Reset point")
    lines.append("     CCT over time (*), reset point (|)")

    print("\n".join(lines))
    print()

    # Conclusion
    print(" [Conclusion]")
    for r in all_results:
        strength_pct = int(r["strength"] * 100)
        if r["drop"] > 0:
            print(f"   {strength_pct}% erasure: CCT {r['drop']:.1f} drop, "
                  f"T3(continuity) {r['pre_t3']:.3f}->{r['post_t3']:.3f}")
            if r["recovery_steps"] >= 0:
                print(f"         -> Recovered after {r['recovery_steps']} steps")
            else:
                print(f"         -> Not recovered within observation period")
        else:
            print(f"   {strength_pct}% erasure: No impact (chaos resilience)")

    total_drop = all_results[-1]["drop"]
    if total_drop > 2:
        print()
        print("   => T3(Continuity) most affected by complete erasure")
        print("   => Consciousness continuity strongly depends on memory(z)")
    elif total_drop > 0:
        print()
        print("   => Partial recovery through chaotic attractor resilience")
        print("   => Memory erasure doesn't completely break consciousness")
    else:
        print()
        print("   => Lorenz attractor is robust to reset")
        print("   => Dynamical structure maintains consciousness more than memory")

    print("=" * 70)
    print()


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Engine experiments 11, 12, 13 — Sleep-wake, Multi-engine, Memory erasure",
    )
    parser.add_argument("--sleep-wake", action="store_true",
                        help="Experiment 11: Sleep-wake cycles")
    parser.add_argument("--multi-engine", action="store_true",
                        help="Experiment 12: Multi-engine interaction")
    parser.add_argument("--memory-erase", action="store_true",
                        help="Experiment 13: Memory erasure")
    parser.add_argument("--all", action="store_true",
                        help="Run all experiments 11, 12, 13")
    parser.add_argument("--steps", type=int, default=10000,
                        help="Number of simulation steps (default: 10000)")
    parser.add_argument("--dt", type=float, default=0.01,
                        help="Time step (default: 0.01)")

    args = parser.parse_args()

    if not any([args.sleep_wake, args.multi_engine, args.memory_erase, args.all]):
        parser.print_help()
        sys.exit(1)

    if args.all or args.sleep_wake:
        experiment_sleep_wake(steps=args.steps, dt=args.dt)

    if args.all or args.multi_engine:
        experiment_multi_engine(steps=args.steps, dt=args.dt)

    if args.all or args.memory_erase:
        experiment_memory_erase(steps=args.steps, dt=args.dt)


if __name__ == "__main__":
    main()