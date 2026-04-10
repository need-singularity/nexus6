#!/usr/bin/env python3
"""Dual Brain Corpus Callosum Simulator — Dual Brain Corpus Callosum Model

Models the left hemisphere (analytical) and right hemisphere (intuitive) of the human brain 
as Lorenz attractors, connected by corpus callosum coupling κ to analyze consciousness continuity.

Mathematical Model:
  Left hemisphere: dx_L/dt = σ_L(y_L - x_L) + κ(x_R - x_L)  [σ=10, ρ=28, β=2.67, noise=0.05]
  Right hemisphere: dx_R/dt = σ_R(y_R - x_R) + κ(x_L - x_R)  [σ=12, ρ=32, β=2.2,  noise=0.2]
  κ: corpus callosum bandwidth (0=split brain, 0.5=normal, 5.0=oversynchronized)

Usage:
  python3 dual_brain_callosum.py                    # κ scan (default)
  python3 dual_brain_callosum.py --split-brain       # split-brain experiment
  python3 dual_brain_callosum.py --agenesis          # callosal agenesis
  python3 dual_brain_callosum.py --lateralize left   # left hemisphere dominant
  python3 dual_brain_callosum.py --lateralize right  # right hemisphere dominant
  python3 dual_brain_callosum.py --kappa 0.5         # specific κ value
  python3 dual_brain_callosum.py --delay 10          # transmission delay
  python3 dual_brain_callosum.py --all               # all experiments
  python3 dual_brain_callosum.py --plot              # save matplotlib plots
"""

import sys, os

import argparse
import os
import sys
from datetime import datetime

import numpy as np
from scipy import stats

# Import from consciousness_calc.py
from consciousness_calc import run_cct, judge, compute_entropy

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

# ─────────────────────────────────────────────
# Hemisphere parameter definitions
# ─────────────────────────────────────────────

LEFT_HEMISPHERE = {
    "sigma": 10, "rho": 28, "beta": 2.67, "noise": 0.05,
    "description": "Left hemisphere (analytical, sequential)",
}

RIGHT_HEMISPHERE = {
    "sigma": 12, "rho": 32, "beta": 2.2, "noise": 0.2,
    "description": "Right hemisphere (intuitive, holistic)",
}

# κ scan default values
KAPPA_SCAN_VALUES = [0.0, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]


# ─────────────────────────────────────────────
# Dual Brain Simulator
# ─────────────────────────────────────────────

def dual_brain_simulate(left=None, right=None, kappa=0.5,
                        kappa_lr=None, kappa_rl=None,
                        delay=0, steps=50000, dt=0.01, seed=42,
                        kappa_schedule=None):
    """Dual brain coupled Lorenz simulator.

    Parameters:
        left:   left hemisphere parameters dict (sigma, rho, beta, noise)
        right:  right hemisphere parameters dict
        kappa:  symmetric coupling strength (default 0.5)
        kappa_lr: left→right transmission strength (uses kappa if None)
        kappa_rl: right→left transmission strength (uses kappa if None)
        delay:  transmission delay step count (0=immediate)
        steps:  simulation step count
        dt:     time interval
        seed:   random seed
        kappa_schedule: callable(t_index) -> kappa value (time-varying κ, for split-brain)

    Returns:
        t:  time array [steps]
        S:  state array [steps, 6] (x_L, y_L, z_L, x_R, y_R, z_R)
        kappas: κ time series [steps] (when using schedule)
    """
    if left is None:
        left = LEFT_HEMISPHERE
    if right is None:
        right = RIGHT_HEMISPHERE

    # Asymmetric coupling
    k_lr = kappa_lr if kappa_lr is not None else kappa
    k_rl = kappa_rl if kappa_rl is not None else kappa

    rng = np.random.default_rng(seed)
    t = np.arange(steps) * dt
    S = np.zeros((steps, 6))
    # Different initial conditions for left and right
    S[0] = [1.0, 1.0, 1.0, -1.0, 0.5, 1.5]

    kappas = np.full(steps, kappa, dtype=float)

    σ_L, ρ_L, β_L = left["sigma"], left["rho"], left["beta"]
    σ_R, ρ_R, β_R = right["sigma"], right["rho"], right["beta"]
    n_L, n_R = left["noise"], right["noise"]

    for i in range(1, steps):
        # Time-varying κ (for split-brain experiment)
        if kappa_schedule is not None:
            cur_k = kappa_schedule(i)
            kappas[i] = cur_k
            k_lr_cur = cur_k
            k_rl_cur = cur_k
        else:
            k_lr_cur = k_lr
            k_rl_cur = k_rl

        xL, yL, zL, xR, yR, zR = S[i - 1]

        # Transmission delay: use opposite hemisphere values from delay steps ago
        if delay > 0 and i > delay:
            xR_d, yR_d, zR_d = S[i - 1 - delay, 3], S[i - 1 - delay, 4], S[i - 1 - delay, 5]
            xL_d, yL_d, zL_d = S[i - 1 - delay, 0], S[i - 1 - delay, 1], S[i - 1 - delay, 2]
        else:
            xR_d, yR_d, zR_d = xR, yR, zR
            xL_d, yL_d, zL_d = xL, yL, zL

        # Left hemisphere (analytical)
        dxL = σ_L * (yL - xL) + k_rl_cur * (xR_d - xL)
        dyL = xL * (ρ_L - zL) - yL + k_rl_cur * (yR_d - yL)
        dzL = xL * yL - β_L * zL + k_rl_cur * (zR_d - zL)

        # Right hemisphere (intuitive)
        dxR = σ_R * (yR - xR) + k_lr_cur * (xL_d - xR)
        dyR = xR * (ρ_R - zR) - yR + k_lr_cur * (yL_d - yR)
        dzR = xR * yR - β_R * zR + k_lr_cur * (zL_d - zR)

        # Noise (left: low noise, right: high noise)
        epsL = rng.normal(0, n_L, 3) if n_L > 0 else np.zeros(3)
        epsR = rng.normal(0, n_R, 3) if n_R > 0 else np.zeros(3)

        S[i, 0] = xL + (dxL + epsL[0]) * dt
        S[i, 1] = yL + (dyL + epsL[1]) * dt
        S[i, 2] = zL + (dzL + epsL[2]) * dt
        S[i, 3] = xR + (dxR + epsR[0]) * dt
        S[i, 4] = yR + (dyR + epsR[1]) * dt
        S[i, 5] = zR + (dzR + epsR[2]) * dt

    return t, S, kappas


# ─────────────────────────────────────────────
# Measurement functions
# ─────────────────────────────────────────────

def measure_sync(S):
    """Left-right hemisphere synchronization: corr(x_L, x_R)."""
    xL = S[:, 0]
    xR = S[:, 3]
    if np.std(xL) < 1e-12 or np.std(xR) < 1e-12:
        return 0.0
    return np.corrcoef(xL, xR)[0, 1]


def transfer_entropy(source, target, bins=10, lag=1):
    """Transfer Entropy: source → target.

    TE(S→T) = H(T_future | T_past) - H(T_future | T_past, S_past)
    Approximated with conditional entropy after discretization.
    """
    n = len(source) - lag
    if n < 100:
        return 0.0

    s_past = source[:n]
    t_past = target[:n]
    t_future = target[lag:lag + n]

    # Discretization
    s_bins = np.digitize(s_past, np.linspace(s_past.min(), s_past.max(), bins + 1)[:-1])
    t_bins_past = np.digitize(t_past, np.linspace(t_past.min(), t_past.max(), bins + 1)[:-1])
    t_bins_future = np.digitize(t_future, np.linspace(t_future.min(), t_future.max(), bins + 1)[:-1])

    # Calculate joint probabilities
    # H(T_f, T_p) - H(T_p)
    def joint_entropy_2(a, b, nbins):
        hist = np.histogram2d(a, b, bins=nbins)[0]
        p = hist / hist.sum()
        p = p[p > 0]
        return -np.sum(p * np.log2(p + 1e-15))

    def joint_entropy_3(a, b, c, nbins):
        # 3D histogram
        sample = np.column_stack([a, b, c])
        hist, _ = np.histogramdd(sample, bins=nbins)
        p = hist / hist.sum()
        p = p[p > 0]
        return -np.sum(p * np.log2(p + 1e-15))

    h_tf_tp = joint_entropy_2(t_bins_future, t_bins_past, bins)
    h_tp = compute_entropy(t_past.astype(float), bins=bins)
    h_tf_tp_sp = joint_entropy_3(t_bins_future, t_bins_past, s_bins, bins)
    h_tp_sp = joint_entropy_2(t_bins_past, s_bins, bins)

    # TE = H(T_f | T_p) - H(T_f | T_p, S_p)
    #    = [H(T_f, T_p) - H(T_p)] - [H(T_f, T_p, S_p) - H(T_p, S_p)]
    te = (h_tf_tp - h_tp) - (h_tf_tp_sp - h_tp_sp)
    return max(0.0, te)  # TE >= 0


def joint_entropy_2d(x, y, bins=30):
    """2D joint entropy H(X, Y)."""
    hist = np.histogram2d(x, y, bins=bins)[0]
    p = hist / hist.sum()
    p = p[p > 0]
    return -np.sum(p * np.log(p + 1e-15))


def asymmetry_index(cct_L, cct_R):
    """Left-right asymmetry index: |CCT_L - CCT_R| / (CCT_L + CCT_R)."""
    total = cct_L + cct_R
    if total < 1e-12:
        return 0.0
    return abs(cct_L - cct_R) / total


def measure_all(S, gap_ratio=0.0):
    """Calculate all measurements at once.

    Returns:
        dict with keys: cct_L, cct_R, cct_combined, sync, te_lr, te_rl,
                         joint_h, sum_h, asymmetry, verdict_L, verdict_R, verdict_combined
    """
    S_L = S[:, :3]
    S_R = S[:, 3:]

    # Individual CCT
    results_L = run_cct(S_L, gap_ratio)
    results_R = run_cct(S_R, gap_ratio)

    total_L, verdict_L = judge(results_L)
    total_R, verdict_R = judge(results_R)

    # Combined CCT: project 6D state to 3D and run CCT
    # Method: sum left and right x,y,z to treat as single attractor
    S_combined = np.column_stack([
        S[:, 0] + S[:, 3],  # x_L + x_R
        S[:, 1] + S[:, 4],  # y_L + y_R
        S[:, 2] + S[:, 5],  # z_L + z_R
    ])
    results_combined = run_cct(S_combined, gap_ratio)
    total_combined, verdict_combined = judge(results_combined)

    # Synchronization
    sync = measure_sync(S)

    # Transfer Entropy (downsample for speed)
    step = max(1, len(S) // 10000)
    xL_ds = S[::step, 0]
    xR_ds = S[::step, 3]
    te_lr = transfer_entropy(xL_ds, xR_ds, bins=8, lag=1)
    te_rl = transfer_entropy(xR_ds, xL_ds, bins=8, lag=1)

    # Joint entropy
    h_L = compute_entropy(S[:, 0], bins=30)
    h_R = compute_entropy(S[:, 3], bins=30)
    h_joint = joint_entropy_2d(S[:, 0], S[:, 3], bins=30)
    h_sum = h_L + h_R

    # Asymmetry
    asym = asymmetry_index(total_L, total_R)

    return {
        "cct_L": total_L, "verdict_L": verdict_L,
        "cct_R": total_R, "verdict_R": verdict_R,
        "cct_combined": total_combined, "verdict_combined": verdict_combined,
        "sync": sync,
        "te_lr": te_lr, "te_rl": te_rl,
        "h_joint": h_joint, "h_sum": h_sum,
        "asymmetry": asym,
        "results_L": results_L,
        "results_R": results_R,
        "results_combined": results_combined,
    }


# ─────────────────────────────────────────────
# Judgment logic
# ─────────────────────────────────────────────

def kappa_verdict(sync, te_lr, te_rl):
    """κ state judgment."""
    if abs(sync) > 0.9:
        return "Oversynchronized"
    elif abs(sync) > 0.7:
        return "Normal"
    elif abs(sync) > 0.3:
        return "Weakly coupled"
    elif abs(sync) > 0.1:
        return "Minimal"
    else:
        return "Split"


# ─────────────────────────────────────────────
# Experiment A: κ scan
# ─────────────────────────────────────────────

def experiment_kappa_scan(steps=50000, dt=0.01, kappas=None):
    """Experiment A: Corpus callosum strength scan."""
    if kappas is None:
        kappas = KAPPA_SCAN_VALUES

    print("=" * 90)
    print(" Experiment A: Corpus Callosum Bandwidth (κ) Scan — Corpus Callosum Bandwidth")
    print("=" * 90)
    print()
    print(" Left hemisphere: σ=10, ρ=28, β=2.67, noise=0.05 (analytical, precise)")
    print(" Right hemisphere: σ=12, ρ=32, β=2.2,  noise=0.2  (intuitive, creative)")
    print()

    header = (f"  {'κ':>5s} │ {'CCT_L':>5s} │ {'CCT_R':>5s} │ {'CCT_sum':>6s} │ "
              f"{'Sync':>6s} │ {'TE_L→R':>6s} │ {'TE_R→L':>6s} │ "
              f"{'Asymm':>6s} │ Verdict")
    sep = "  ─────┼───────┼───────┼────────┼────────┼────────┼────────┼────────┼─────────"
    print(header)
    print(sep)

    all_results = []

    for k in kappas:
        _, S, _ = dual_brain_simulate(kappa=k, steps=steps, dt=dt)
        m = measure_all(S)
        verdict = kappa_verdict(m["sync"], m["te_lr"], m["te_rl"])

        print(f"  {k:5.2f} │ {m['cct_L']:5.1f} │ {m['cct_R']:5.1f} │ "
              f"{m['cct_combined']:6.1f} │ {m['sync']:6.3f} │ "
              f"{m['te_lr']:6.3f} │ {m['te_rl']:6.3f} │ "
              f"{m['asymmetry']:6.3f} │ {verdict}")

        all_results.append((k, m, verdict))

    print()

    # Find optimal κ
    best_k = None
    best_score = -1
    for k, m, v in all_results:
        # Optimal: high CCT_sum + moderate sync (0.3~0.8) + low asymmetry
        if 0.3 < abs(m["sync"]) < 0.85:
            score = m["cct_combined"] - m["asymmetry"] * 2
            if score > best_score:
                best_score = score
                best_k = k

    print(" ─── Key Findings ───")
    if best_k is not None:
        print(f"  Optimal κ = {best_k} (sync-diversity balance)")
    else:
        print("  Optimal κ: Unable to determine (all κ outside sync range)")

    # Find threshold: minimum κ where sync > 0.5
    threshold_k = None
    for k, m, v in all_results:
        if abs(m["sync"]) > 0.5 and threshold_k is None:
            threshold_k = k
    if threshold_k is not None:
        print(f"  Integration threshold κ ≈ {threshold_k} (sync > 0.5 — 'unified consciousness' candidate)")

    # TE asymmetry analysis
    for k, m, v in all_results:
        if k == 0.5:  # normal corpus callosum
            if m["te_rl"] > m["te_lr"] * 1.2:
                print(f"  κ=0.5 information flow: R→L dominant (TE_R→L={m['te_rl']:.3f} > TE_L→R={m['te_lr']:.3f})")
            elif m["te_lr"] > m["te_rl"] * 1.2:
                print(f"  κ=0.5 information flow: L→R dominant (TE_L→R={m['te_lr']:.3f} > TE_R→L={m['te_rl']:.3f})")
            else:
                print(f"  κ=0.5 information flow: Symmetric (TE_L→R={m['te_lr']:.3f} ≈ TE_R→L={m['te_rl']:.3f})")

    print("=" * 90)
    return all_results


# ─────────────────────────────────────────────
# Experiment B: Split-brain
# ─────────────────────────────────────────────

def experiment_split_brain(steps=50000, dt=0.01):
    """Experiment B: Sperry split-brain experiment reproduction.

    1. Start with κ=0.5 (normal)
    2. Cut to κ=0 at t=steps//2
    3. Compare CCT before and after cut
    """
    cut_step = steps // 2

    def kappa_schedule(i):
        return 0.5 if i < cut_step else 0.0

    print("=" * 90)
    print(" Experiment B: Split-Brain — Sperry Experiment Reproduction")
    print("=" * 90)
    print()
    print(f" Protocol: κ=0.5 (0~{cut_step} steps) → κ=0.0 ({cut_step}~{steps} steps)")
    print(f" Cut point: t = {cut_step * dt:.0f} (step {cut_step})")
    print()

    _, S, kappas = dual_brain_simulate(
        kappa=0.5, steps=steps, dt=dt, kappa_schedule=kappa_schedule
    )

    # Analyze before/after cut separately
    S_before = S[:cut_step]
    S_after = S[cut_step:]

    m_before = measure_all(S_before)
    m_after = measure_all(S_after)

    print(" ─── Before Cut (κ=0.5, normal corpus callosum) ───")
    print(f"  CCT_L={m_before['cct_L']:.1f}/5  CCT_R={m_before['cct_R']:.1f}/5  "
          f"CCT_sum={m_before['cct_combined']:.1f}/5")
    print(f"  Sync={m_before['sync']:.3f}  TE_L→R={m_before['te_lr']:.3f}  "
          f"TE_R→L={m_before['te_rl']:.3f}")
    print()

    print(" ─── After Cut (κ=0.0, corpus callosum severed) ───")
    print(f"  CCT_L={m_after['cct_L']:.1f}/5  CCT_R={m_after['cct_R']:.1f}/5  "
          f"CCT_sum={m_after['cct_combined']:.1f}/5")
    print(f"  Sync={m_after['sync']:.3f}  TE_L→R={m_after['te_lr']:.3f}  "
          f"TE_R→L={m_after['te_rl']:.3f}")
    print()

    # ASCII timeline
    print(" ─── Synchronization Timeline ───")
    _print_sync_timeline(S, cut_step, steps, dt)
    print()

    # Key findings
    print(" ─── Key Findings ───")
    sync_drop = abs(m_before["sync"]) - abs(m_after["sync"])
    print(f"  Sync drop: {m_before['sync']:.3f} → {m_after['sync']:.3f} "
          f"(Δ = {sync_drop:.3f})")

    if m_after["cct_L"] >= 3 and m_after["cct_R"] >= 3:
        print("  → Both hemispheres maintain independent CCT = Two consciousnesses?")
    elif m_after["cct_L"] >= 3 or m_after["cct_R"] >= 3:
        print("  → Only one hemisphere maintains CCT — Asymmetric consciousness split")
    else:
        print("  → Both hemispheres show decreased CCT — Corpus callosum-dependent consciousness")

    print("=" * 90)
    return m_before, m_after, S, kappas


def _print_sync_timeline(S, cut_step, steps, dt):
    """Print synchronization change ASCII timeline."""
    n_windows = 40
    window_size = steps // n_windows

    syncs = []
    for w in range(n_windows):
        start = w * window_size
        end = start + window_size
        chunk = S[start:end]
        s = measure_sync(chunk)
        syncs.append(s)

    syncs = np.array(syncs)
    height = 10

    print(f"  Sync")
    for row in range(height, -1, -1):
        val = row / height
        line = f"  {val:4.1f}│"
        for col in range(n_windows):
            mid = col * window_size + window_size // 2
            mapped = int(max(0, syncs[col]) * height + 0.5)
            if mapped == row:
                line += "█"
            elif col * window_size <= cut_step < (col + 1) * window_size:
                line += "│"
            else:
                line += " "
        lines_out = line
        print(lines_out)

    cut_col = cut_step // window_size
    ruler = "  " + "    └" + "─" * cut_col + "┼" + "─" * (n_windows - cut_col - 1)
    print(ruler)
    print("  " + " " * (5 + cut_col) + "cut")


# ─────────────────────────────────────────────
# Experiment C: Callosal Agenesis
# ─────────────────────────────────────────────

def experiment_agenesis(steps=50000, dt=0.01):
    """Experiment C: Congenital corpus callosum absence.

    κ=0 throughout, but compensatory mechanism with increased noise (alternative pathway simulation).
    """
    print("=" * 90)
    print(" Experiment C: Callosal Agenesis")
    print("=" * 90)
    print()
    print(" Condition: κ=0 (no corpus callosum from birth)")
    print(" Alternative pathway: anterior commissure → approximated by increased noise")
    print()

    conditions = [
        ("Normal brain", 0.5, LEFT_HEMISPHERE, RIGHT_HEMISPHERE),
        ("Callosal agenesis (no comp.)", 0.0, LEFT_HEMISPHERE, RIGHT_HEMISPHERE),
        ("Callosal agenesis (comp: noise↑)", 0.0,
         {**LEFT_HEMISPHERE, "noise": 0.15},
         {**RIGHT_HEMISPHERE, "noise": 0.4}),
        ("Callosal agenesis (comp: noise↑↑)", 0.0,
         {**LEFT_HEMISPHERE, "noise": 0.3},
         {**RIGHT_HEMISPHERE, "noise": 0.6}),
    ]

    header = (f"  {'Condition':>28s} │ {'κ':>4s} │ {'CCT_L':>5s} │ {'CCT_R':>5s} │ "
              f"{'CCT_sum':>6s} │ {'Sync':>6s} │ {'Asymm':>6s}")
    sep = "  " + "─" * 28 + "┼──────┼───────┼───────┼────────┼────────┼────────"
    print(header)
    print(sep)

    for name, k, left, right in conditions:
        _, S, _ = dual_brain_simulate(left=left, right=right, kappa=k,
                                       steps=steps, dt=dt)
        m = measure_all(S)
        print(f"  {name:>28s} │ {k:4.1f} │ {m['cct_L']:5.1f} │ {m['cct_R']:5.1f} │ "
              f"{m['cct_combined']:6.1f} │ {m['sync']:6.3f} │ {m['asymmetry']:6.3f}")

    print()
    print(" ─── Interpretation ───")
    print("  Real callosal agenesis patients: normal IQ, normal consciousness (compensatory pathways exist)")
    print("  Simulation: increased noise approximates alternative pathways (anterior commissure etc.)")
    print("  Key: Can consciousness continuity be maintained without corpus callosum?")
    print("=" * 90)


# ─────────────────────────────────────────────
# Experiment D: Lateralization
# ─────────────────────────────────────────────

def experiment_lateralize(direction="left", steps=50000, dt=0.01):
    """Experiment D: Asymmetric corpus callosum — Left/right hemisphere dominance.

    Left dominance: κ_LR=0.3 (left→right weak), κ_RL=0.7 (right→left strong)
    Right dominance: κ_LR=0.7 (left→right strong), κ_RL=0.3 (right→left weak)
    """
    print("=" * 90)
    print(f" Experiment D: Corpus Callosum Asymmetry — {direction.upper()} Hemisphere Dominance")
    print("=" * 90)
    print()

    conditions = []

    if direction == "left":
        # Left dominance: right→left info strong (left receives more)
        conditions = [
            ("Symmetric (control)", 0.5, 0.5),
            ("Slight left dominance", 0.4, 0.6),
            ("Left dominance", 0.3, 0.7),
            ("Strong left dominance", 0.2, 0.8),
        ]
    else:
        # Right dominance: left→right info strong
        conditions = [
            ("Symmetric (control)", 0.5, 0.5),
            ("Slight right dominance", 0.6, 0.4),
            ("Right dominance", 0.7, 0.3),
            ("Strong right dominance", 0.8, 0.2),
        ]

    print(f"  {'Condition':>16s} │ {'κ_LR':>5s} │ {'κ_RL':>5s} │ {'CCT_L':>5s} │ "
          f"{'CCT_R':>5s} │ {'Sync':>6s} │ {'TE_L→R':>6s} │ {'TE_R→L':>6s} │ {'Asymm':>6s}")
    sep = "  " + "─" * 16 + "┼───────┼───────┼───────┼───────┼────────┼────────┼────────┼────────"
    print(sep)

    for name, k_lr, k_rl in conditions:
        _, S, _ = dual_brain_simulate(
            kappa_lr=k_lr, kappa_rl=k_rl, steps=steps, dt=dt
        )
        m = measure_all(S)
        print(f"  {name:>16s} │ {k_lr:5.2f} │ {k_rl:5.2f} │ {m['cct_L']:5.1f} │ "
              f"{m['cct_R']:5.1f} │ {m['sync']:6.3f} │ "
              f"{m['te_lr']:6.3f} │ {m['te_rl']:6.3f} │ {m['asymmetry']:6.3f}")

    print()
    print(" ─── Interpretation ───")
    if direction == "left":
        print("  Left dominance: enhanced language processing, logical thinking")
        print("  R→L transmission enhanced = increased ability to convert intuition to analysis")
    else:
        print("  Right dominance: enhanced spatial processing, artistic intuition")
        print("  L→R transmission enhanced = converting analysis to holistic intuition")
    print("=" * 90)


# ─────────────────────────────────────────────
# Single κ run
# ─────────────────────────────────────────────

def run_single_kappa(kappa=0.5, kappa_lr=None, kappa_rl=None,
                     delay=0, steps=50000, dt=0.01):
    """Full analysis with single κ value."""
    print("=" * 90)
    if kappa_lr is not None and kappa_rl is not None:
        print(f" Dual Brain Analysis — κ_LR={kappa_lr}, κ_RL={kappa_rl}, delay={delay}")
    else:
        print(f" Dual Brain Analysis — κ={kappa}, delay={delay}")
    print("=" * 90)
    print()

    _, S, _ = dual_brain_simulate(
        kappa=kappa, kappa_lr=kappa_lr, kappa_rl=kappa_rl,
        delay=delay, steps=steps, dt=dt
    )
    m = measure_all(S)

    # Left hemisphere details
    print(" ─── Left Hemisphere (Analytical) ───")
    print(f"  Parameters: σ=10, ρ=28, β=2.67, noise=0.05")
    _print_cct_detail(m["results_L"], m["cct_L"], m["verdict_L"])

    print()
    print(" ─── Right Hemisphere (Intuitive) ───")
    print(f"  Parameters: σ=12, ρ=32, β=2.2, noise=0.2")
    _print_cct_detail(m["results_R"], m["cct_R"], m["verdict_R"])

    print()
    print(" ─── Combined System (6D → 3D projection) ───")
    _print_cct_detail(m["results_combined"], m["cct_combined"], m["verdict_combined"])

    print()
    print(" ─── Corpus Callosum Metrics ───")
    print(f"  Synchronization corr(x_L, x_R) = {m['sync']:.4f}")
    print(f"  Transfer Entropy L→R  = {m['te_lr']:.4f}")
    print(f"  Transfer Entropy R→L  = {m['te_rl']:.4f}")
    print(f"  Joint Entropy H(L,R)  = {m['h_joint']:.4f}")
    print(f"  Independent sum H(L)+H(R)    = {m['h_sum']:.4f}")
    redundancy = max(0, m['h_sum'] - m['h_joint'])
    print(f"  Redundancy (redundancy)= {redundancy:.4f}")
    print(f"  Left-right asymmetry index      = {m['asymmetry']:.4f}")

    verdict = kappa_verdict(m["sync"], m["te_lr"], m["te_rl"])
    print(f"\n  Overall verdict: {verdict}")
    print("=" * 90)

    return m, S


def _print_cct_detail(results, total, verdict):
    """Print CCT test details."""
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
        print(f"  {label} │ {mark} {status} │ {score:.3f} │ {detail}")
    print(f"  {'─' * 56}")
    print(f"  Overall: {total}/5 {verdict}")


# ─────────────────────────────────────────────
# matplotlib plotting
# ─────────────────────────────────────────────

def plot_kappa_scan(all_results):
    """Save κ scan results as matplotlib graph."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  [Warning] matplotlib not found, skipping --plot")
        return None

    kappas = [r[0] for r in all_results]
    cct_L = [r[1]["cct_L"] for r in all_results]
    cct_R = [r[1]["cct_R"] for r in all_results]
    cct_C = [r[1]["cct_combined"] for r in all_results]
    syncs = [r[1]["sync"] for r in all_results]
    te_lr = [r[1]["te_lr"] for r in all_results]
    te_rl = [r[1]["te_rl"] for r in all_results]
    asyms = [r[1]["asymmetry"] for r in all_results]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Dual Brain Corpus Callosum — κ Scan", fontsize=14, fontweight="bold")

    # 1. CCT vs κ
    ax = axes[0, 0]
    ax.plot(kappas, cct_L, "b-o", label="CCT Left (analytic)", markersize=4)
    ax.plot(kappas, cct_R, "r-s", label="CCT Right (intuitive)", markersize=4)
    ax.plot(kappas, cct_C, "g-^", label="CCT Combined", markersize=4)
    ax.set_xlabel("κ (corpus callosum bandwidth)")
    ax.set_ylabel("CCT Score (/5)")
    ax.set_title("CCT vs Coupling Strength")
    ax.legend(fontsize=8)
    ax.set_xscale("symlog", linthresh=0.01)
    ax.grid(True, alpha=0.3)

    # 2. Synchronization vs κ
    ax = axes[0, 1]
    ax.plot(kappas, syncs, "purple", marker="o", markersize=4)
    ax.axhline(0.5, color="red", ls="--", alpha=0.5, label="Integration threshold")
    ax.set_xlabel("κ")
    ax.set_ylabel("Synchronization corr(x_L, x_R)")
    ax.set_title("Hemisphere Synchronization")
    ax.set_xscale("symlog", linthresh=0.01)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # 3. Transfer Entropy vs κ
    ax = axes[1, 0]
    ax.plot(kappas, te_lr, "b-o", label="TE L→R", markersize=4)
    ax.plot(kappas, te_rl, "r-s", label="TE R→L", markersize=4)
    ax.set_xlabel("κ")
    ax.set_ylabel("Transfer Entropy (bits)")
    ax.set_title("Information Flow")
    ax.set_xscale("symlog", linthresh=0.01)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # 4. Asymmetry vs κ
    ax = axes[1, 1]
    ax.plot(kappas, asyms, "darkorange", marker="o", markersize=4)
    ax.set_xlabel("κ")
    ax.set_ylabel("Asymmetry Index")
    ax.set_title("Left-Right Asymmetry")
    ax.set_xscale("symlog", linthresh=0.01)
    ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    os.makedirs(RESULTS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(RESULTS_DIR, f"dual_brain_kappa_scan_{ts}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_split_brain(S, kappas, cut_step, steps, dt):
    """Save split-brain experiment matplotlib graph."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  [Warning] matplotlib not found, skipping --plot")
        return None

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Split-Brain Experiment", fontsize=14, fontweight="bold")

    t = np.arange(steps) * dt
    ds = max(1, steps // 5000)

    # 1. x_L, x_R trajectories
    ax = axes[0, 0]
    ax.plot(t[::ds], S[::ds, 0], "b-", lw=0.5, alpha=0.7, label="x_L")
    ax.plot(t[::ds], S[::ds, 3], "r-", lw=0.5, alpha=0.7, label="x_R")
    ax.axvline(cut_step * dt, color="black", ls="--", lw=2, label="cut")
    ax.set_xlabel("Time")
    ax.set_ylabel("x")
    ax.set_title("Hemisphere Trajectories")
    ax.legend(fontsize=8)

    # 2. κ time series
    ax = axes[0, 1]
    ax.plot(t[::ds], kappas[::ds], "green", lw=2)
    ax.set_xlabel("Time")
    ax.set_ylabel("κ")
    ax.set_title("Corpus Callosum Bandwidth")
    ax.set_ylim(-0.1, 1.0)

    # 3. Window-wise synchronization
    ax = axes[1, 0]
    n_windows = 50
    window_size = steps // n_windows
    sync_t = []
    sync_v = []
    for w in range(n_windows):
        start = w * window_size
        end = start + window_size
        chunk = S[start:end]
        sync_t.append((start + end) / 2 * dt)
        sync_v.append(measure_sync(chunk))
    ax.plot(sync_t, sync_v, "purple", marker=".", markersize=3)
    ax.axvline(cut_step * dt, color="black", ls="--", lw=2, label="cut")
    ax.set_xlabel("Time")
    ax.set_ylabel("Synchronization")
    ax.set_title("Sync Over Time")
    ax.legend(fontsize=8)

    # 4. Window-wise entropy
    ax = axes[1, 1]
    h_L_t = []
    h_R_t = []
    for w in range(n_windows):
        start = w * window_size
        end = start + window_size
        chunk = S[start:end]
        h_L_t.append(compute_entropy(chunk[:, 0], bins=30))
        h_R_t.append(compute_entropy(chunk[:, 3], bins=30))
    ax.plot(sync_t, h_L_t, "b-", label="H(Left)")
    ax.plot(sync_t, h_R_t, "r-", label="H(Right)")
    ax.axvline(cut_step * dt, color="black", ls="--", lw=2, label="cut")
    ax.set_xlabel("Time")
    ax.set_ylabel("Entropy")
    ax.set_title("Hemisphere Entropy")
    ax.legend(fontsize=8)

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    os.makedirs(RESULTS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(RESULTS_DIR, f"dual_brain_split_{ts}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Dual Brain Corpus Callosum Simulator — Dual Brain Corpus Callosum Model",
    )
    parser.add_argument("--kappa", type=float, default=None,
                        help="Analyze with specific κ value (default: κ scan)")
    parser.add_argument("--split-brain", action="store_true",
                        help="Experiment B: Split-brain (Sperry experiment)")
    parser.add_argument("--agenesis", action="store_true",
                        help="Experiment C: Callosal agenesis")
    parser.add_argument("--lateralize", type=str, choices=["left", "right"], default=None,
                        help="Experiment D: Left/right hemisphere dominance")
    parser.add_argument("--delay", type=int, default=0,
                        help="Transmission delay step count (default: 0)")
    parser.add_argument("--all", action="store_true",
                        help="All experiments (A+B+C+D)")
    parser.add_argument("--steps", type=int, default=50000,
                        help="Simulation step count (default: 50000)")
    parser.add_argument("--dt", type=float, default=0.01,
                        help="Time interval (default: 0.01)")
    parser.add_argument("--plot", action="store_true",
                        help="Save matplotlib graphs")

    args = parser.parse_args()

    # If no options, run κ scan
    run_scan = not any([args.kappa is not None, args.split_brain,
                        args.agenesis, args.lateralize, args.all])

    if args.all or run_scan:
        results = experiment_kappa_scan(steps=args.steps, dt=args.dt)
        if args.plot:
            path = plot_kappa_scan(results)
            if path:
                print(f"\n  [plot] Saved: {path}")
        print()

    if args.all or args.split_brain:
        m_before, m_after, S, kappas = experiment_split_brain(
            steps=args.steps, dt=args.dt
        )
        if args.plot:
            cut_step = args.steps // 2
            path = plot_split_brain(S, kappas, cut_step, args.steps, args.dt)
            if path:
                print(f"\n  [plot] Saved: {path}")
        print()

    if args.all or args.agenesis:
        experiment_agenesis(steps=args.steps, dt=args.dt)
        print()

    if args.all or args.lateralize == "left":
        experiment_lateralize("left", steps=args.steps, dt=args.dt)
        print()

    if args.all or args.lateralize == "right":
        experiment_lateralize("right", steps=args.steps, dt=args.dt)
        print()

    if args.kappa is not None and not args.all:
        m, S = run_single_kappa(
            kappa=args.kappa, delay=args.delay,
            steps=args.steps, dt=args.dt
        )


if __name__ == "__main__":
    main()