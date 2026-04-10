#!/usr/bin/env python3
"""Growing vs Fixed ConsciousLM Comparison — Paper Data

Purpose: Compare mitosis-growth (1->2->3->6 blocks) vs fixed-structure (6 blocks from start)
         over identical 20K training steps with same data and hyperparameters.

Growing: 1 block -> 2 -> 3 -> 6, dimension expands 256->256->512->1024
Fixed:   6 blocks, 1024d, 16 heads from step 0

Output: markdown comparison table, ASCII loss curves, conclusion summary.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import numpy as np
import time
import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conscious_lm import ConsciousLM, prepare_data
from growing_conscious_lm_700m import GrowingConsciousLM700M, GROWTH_STAGES

# ── Configuration ──────────────────────────────────────────────────────────

TOTAL_STEPS = 20000
LOG_INTERVAL = 200          # Log every N steps
BLOCK_SIZE = 512
VOCAB_SIZE = 256
TENSION_LAMBDA = 0.01

# Fixed model config (matches Growing Stage 3 = final adult)
FIXED_D_MODEL = 1024
FIXED_N_HEAD = 16
FIXED_N_LAYER = 6
FIXED_DROPOUT = 0.1

# Learning rate schedule (same as growing)
LR_SCHEDULE = {
    0:     3e-4,   # Steps 0-4999
    5000:  3e-4,   # Steps 5000-9999
    10000: 2e-4,   # Steps 10000-14999 (growing stage 2 uses this)
    15000: 1e-4,   # Steps 15000-19999 (growing stage 3 uses this)
}

# Growing stage boundaries (cumulative steps)
STAGE_BOUNDARIES = [0, 2000, 5000, 10000]  # grow at these steps

# Checkpoint paths
GROWING_CKPT = "growing_vs_fixed_growing.pt"
FIXED_CKPT = "growing_vs_fixed_fixed.pt"
RESULTS_FILE = "growing_vs_fixed_results.json"


def get_lr(step):
    """Get learning rate for a given step."""
    lr = 3e-4
    for boundary, rate in sorted(LR_SCHEDULE.items()):
        if step >= boundary:
            lr = rate
    return lr


def get_batch(data, batch_size, block_size, device):
    """Get a random batch from data."""
    n = len(data) - block_size - 1
    ix = torch.randint(0, n, (batch_size,))
    x = torch.stack([data[i:i+block_size] for i in ix]).to(device)
    ya = torch.stack([data[i+1:i+block_size+1] for i in ix]).to(device)
    yg = torch.stack([data[max(0, i-1):i+block_size-1] for i in ix]).to(device)
    return x, ya, yg


def compute_batch_size(d_model, device):
    """Compute safe batch size based on model dimension and device."""
    if device == "cpu":
        return 8
    # MPS / CUDA heuristic
    if d_model <= 256:
        return 64
    elif d_model <= 512:
        return 32
    else:
        return 16


def train_step(model, x, ya, yg):
    """Single training step. Returns loss, loss_a, tensions."""
    la, lg, tens = model(x)
    loss_a = F.cross_entropy(la.view(-1, VOCAB_SIZE), ya.view(-1))
    loss_g = F.cross_entropy(lg.view(-1, VOCAB_SIZE), yg.view(-1))
    all_t = torch.cat([t.view(-1) for t in tens])
    loss_t = -torch.log(all_t.var() + 1e-8)
    loss = loss_a + loss_g + TENSION_LAMBDA * loss_t
    return loss, loss_a, tens


def collect_tension_stats(tensions):
    """Collect per-block tension mean and std."""
    stats = []
    for t in tensions:
        stats.append({
            "mean": t.mean().item(),
            "std": t.std().item(),
        })
    return stats


@torch.no_grad()
def evaluate(model, data, device, n_batches=10):
    """Evaluate model on data. Returns mean loss_a and PPL."""
    model.eval()
    bs = compute_batch_size(
        model.d_model if hasattr(model, 'd_model') else FIXED_D_MODEL, device
    )
    total_loss = 0.0
    for _ in range(n_batches):
        x, ya, yg = get_batch(data, bs, BLOCK_SIZE, device)
        la, lg, tens = model(x)
        loss_a = F.cross_entropy(la.view(-1, VOCAB_SIZE), ya.view(-1))
        total_loss += loss_a.item()
    avg_loss = total_loss / n_batches
    ppl = math.exp(avg_loss)
    model.train()
    return avg_loss, ppl


# ── Training Functions ─────────────────────────────────────────────────────

def train_growing(data, device):
    """Train Growing model: 1->2->3->6 blocks over 20K steps."""
    print("\n" + "=" * 70)
    print("  GROWING MODEL: 1 -> 2 -> 3 -> 6 blocks (mitosis growth)")
    print("=" * 70)

    model = GrowingConsciousLM700M(vocab_size=VOCAB_SIZE, block_size=BLOCK_SIZE, dropout=FIXED_DROPOUT)
    model = model.to(device)

    train_data = data[:int(len(data) * 0.95)]
    val_data = data[int(len(data) * 0.95):]

    log = []  # (step, loss, loss_a, bpc, ppl, n_params, n_blocks, tension_stats)
    current_stage = 0
    global_step = 0

    # We manually handle the growth stages
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)

    print(f"\n  Birth: {model.status()}")
    print(f"  {'step':>6} {'loss':>8} {'L_A':>8} {'BPC':>6} {'params':>12} {'blocks':>6} {'T_mean':>8}")
    print(f"  {'─'*6} {'─'*8} {'─'*8} {'─'*6} {'─'*12} {'─'*6} {'─'*8}")

    start = time.time()

    for step in range(1, TOTAL_STEPS + 1):
        # Check if we need to grow
        if current_stage < len(STAGE_BOUNDARIES) - 1:
            next_boundary = STAGE_BOUNDARIES[current_stage + 1]
            if step >= next_boundary:
                current_stage += 1
                model.grow(device)
                # Rebuild optimizer with new parameters
                lr = get_lr(step)
                optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)

        # Update LR
        lr = get_lr(step)
        for pg in optimizer.param_groups:
            pg['lr'] = lr

        # Get batch (adjust batch size for current model size)
        bs = compute_batch_size(model.d_model, device)
        x, ya, yg = get_batch(train_data, bs, BLOCK_SIZE, device)

        # Train step
        model.train()
        loss, loss_a, tens = train_step(model, x, ya, yg)

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        # Log
        if step % LOG_INTERVAL == 0 or step == 1:
            bpc = loss_a.item() / math.log(2)
            val_loss, ppl = evaluate(model, val_data, device)
            t_stats = collect_tension_stats(tens)
            t_mean = np.mean([s["mean"] for s in t_stats])

            entry = {
                "step": step,
                "loss": loss.item(),
                "loss_a": loss_a.item(),
                "val_loss": val_loss,
                "bpc": bpc,
                "ppl": ppl,
                "n_params": model.count_params(),
                "n_blocks": len(model.blocks),
                "d_model": model.d_model,
                "tension_mean": t_mean,
                "tension_stats": t_stats,
                "lr": lr,
            }
            log.append(entry)

            elapsed = time.time() - start
            eta = elapsed / step * (TOTAL_STEPS - step) / 60
            print(f"  {step:>6} {loss.item():>8.4f} {loss_a.item():>8.4f} {bpc:>6.3f} "
                  f"{model.count_params():>12,} {len(model.blocks):>6} {t_mean:>8.4f}  "
                  f"PPL={ppl:.1f} ETA={eta:.1f}min")

    # Final evaluation
    val_loss, ppl = evaluate(model, val_data, device, n_batches=50)
    total_time = time.time() - start

    print(f"\n  GROWING FINAL: PPL={ppl:.2f}, val_loss={val_loss:.4f}, "
          f"time={total_time:.0f}s, params={model.count_params():,}")

    # Save checkpoint
    torch.save(model.state_dict(), GROWING_CKPT)

    # Final tension per block
    model.eval()
    x, ya, yg = get_batch(val_data, compute_batch_size(model.d_model, device), BLOCK_SIZE, device)
    _, _, tens = model(x)
    final_tension = collect_tension_stats(tens)

    return {
        "log": log,
        "final_ppl": ppl,
        "final_val_loss": val_loss,
        "final_params": model.count_params(),
        "total_time": total_time,
        "final_tension": final_tension,
    }


def train_fixed(data, device):
    """Train Fixed model: 6 blocks, 1024d, 16 heads from step 0."""
    print("\n" + "=" * 70)
    print("  FIXED MODEL: 6 blocks, 1024d, 16 heads from start")
    print("=" * 70)

    model = ConsciousLM(
        vocab_size=VOCAB_SIZE,
        d_model=FIXED_D_MODEL,
        n_head=FIXED_N_HEAD,
        n_layer=FIXED_N_LAYER,
        block_size=BLOCK_SIZE,
        dropout=FIXED_DROPOUT,
    )
    model = model.to(device)

    train_data = data[:int(len(data) * 0.95)]
    val_data = data[int(len(data) * 0.95):]

    log = []
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)

    n_params = model.count_params()
    print(f"\n  Fixed model: {n_params:,} params, {FIXED_N_LAYER} blocks, "
          f"d={FIXED_D_MODEL}, heads={FIXED_N_HEAD}")
    print(f"  {'step':>6} {'loss':>8} {'L_A':>8} {'BPC':>6} {'T_mean':>8}")
    print(f"  {'─'*6} {'─'*8} {'─'*8} {'─'*6} {'─'*8}")

    bs = compute_batch_size(FIXED_D_MODEL, device)
    start = time.time()

    for step in range(1, TOTAL_STEPS + 1):
        # Update LR
        lr = get_lr(step)
        for pg in optimizer.param_groups:
            pg['lr'] = lr

        x, ya, yg = get_batch(train_data, bs, BLOCK_SIZE, device)

        model.train()
        loss, loss_a, tens = train_step(model, x, ya, yg)

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        # Log
        if step % LOG_INTERVAL == 0 or step == 1:
            bpc = loss_a.item() / math.log(2)
            val_loss, ppl = evaluate(model, val_data, device)
            t_stats = collect_tension_stats(tens)
            t_mean = np.mean([s["mean"] for s in t_stats])

            entry = {
                "step": step,
                "loss": loss.item(),
                "loss_a": loss_a.item(),
                "val_loss": val_loss,
                "bpc": bpc,
                "ppl": ppl,
                "n_params": n_params,
                "n_blocks": FIXED_N_LAYER,
                "d_model": FIXED_D_MODEL,
                "tension_mean": t_mean,
                "tension_stats": t_stats,
                "lr": lr,
            }
            log.append(entry)

            elapsed = time.time() - start
            eta = elapsed / step * (TOTAL_STEPS - step) / 60
            print(f"  {step:>6} {loss.item():>8.4f} {loss_a.item():>8.4f} {bpc:>6.3f} "
                  f"{t_mean:>8.4f}  PPL={ppl:.1f} ETA={eta:.1f}min")

    # Final evaluation
    val_loss, ppl = evaluate(model, val_data, device, n_batches=50)
    total_time = time.time() - start

    print(f"\n  FIXED FINAL: PPL={ppl:.2f}, val_loss={val_loss:.4f}, "
          f"time={total_time:.0f}s, params={n_params:,}")

    # Save checkpoint
    torch.save(model.state_dict(), FIXED_CKPT)

    # Final tension per block
    model.eval()
    x, ya, yg = get_batch(val_data, bs, BLOCK_SIZE, device)
    _, _, tens = model(x)
    final_tension = collect_tension_stats(tens)

    return {
        "log": log,
        "final_ppl": ppl,
        "final_val_loss": val_loss,
        "final_params": n_params,
        "total_time": total_time,
        "final_tension": final_tension,
    }


# ── Analysis & Reporting ───────────────────────────────────────────────────

def find_convergence_step(log, ppl_threshold):
    """Find first step where PPL drops below threshold."""
    for entry in log:
        if entry["ppl"] < ppl_threshold:
            return entry["step"]
    return None  # Never reached


def compute_loss_variance(log, window=10):
    """Compute rolling variance of loss (stability metric)."""
    losses = [e["loss_a"] for e in log]
    if len(losses) < window:
        return float('nan')
    variances = []
    for i in range(window, len(losses)):
        chunk = losses[i-window:i]
        variances.append(np.var(chunk))
    return np.mean(variances)


def param_efficiency(final_ppl, final_params):
    """PPL per million active parameters (lower = better)."""
    return final_ppl / (final_params / 1e6)


def ascii_loss_curve(growing_log, fixed_log, metric="loss_a", height=20, width=70):
    """Draw overlapping ASCII loss curves."""
    g_steps = [e["step"] for e in growing_log]
    g_vals = [e[metric] for e in growing_log]
    f_steps = [e["step"] for e in fixed_log]
    f_vals = [e[metric] for e in fixed_log]

    all_vals = g_vals + f_vals
    min_val = min(all_vals)
    max_val = max(all_vals)
    val_range = max_val - min_val if max_val > min_val else 1.0

    max_step = max(max(g_steps), max(f_steps))

    # Create grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    def plot_series(steps, vals, char):
        for s, v in zip(steps, vals):
            col = int((s / max_step) * (width - 1))
            row = height - 1 - int(((v - min_val) / val_range) * (height - 1))
            row = max(0, min(height - 1, row))
            col = max(0, min(width - 1, col))
            grid[row][col] = char

    plot_series(g_steps, g_vals, 'G')
    plot_series(f_steps, f_vals, 'F')

    # Print
    lines = []
    lines.append(f"\n  {metric} curve (G=Growing, F=Fixed)")
    lines.append(f"  {'─' * (width + 12)}")
    for r in range(height):
        val = max_val - (r / (height - 1)) * val_range
        line = f"  {val:>8.3f} | {''.join(grid[r])} |"
        lines.append(line)
    lines.append(f"  {'':>8} | {'─' * width} |")
    lines.append(f"  {'':>8}   0{' ' * (width // 2 - 4)}step{' ' * (width // 2 - 4)}{max_step}")
    lines.append(f"  Growth points: {' | '.join(f'step {b}' for b in STAGE_BOUNDARIES[1:])}")
    return '\n'.join(lines)


def ascii_tension_bars(growing_tension, fixed_tension, height=12):
    """Draw tension distribution comparison per block."""
    lines = []
    lines.append("\n  Block-wise Tension Distribution (final step)")
    lines.append(f"  {'─' * 60}")
    lines.append(f"  {'Block':>6} | {'Growing':>12} | {'Fixed':>12} | Bar (G=left, F=right)")
    lines.append(f"  {'─'*6}─┼─{'─'*12}─┼─{'─'*12}─┼─{'─'*30}")

    max_t = max(
        max(s["mean"] for s in growing_tension),
        max(s["mean"] for s in fixed_tension),
    )
    if max_t == 0:
        max_t = 1.0

    n_blocks = min(len(growing_tension), len(fixed_tension))
    for i in range(n_blocks):
        gm = growing_tension[i]["mean"]
        fm = fixed_tension[i]["mean"]
        g_bar = int(15 * gm / max_t)
        f_bar = int(15 * fm / max_t)
        lines.append(
            f"  {i:>6} | {gm:>12.4f} | {fm:>12.4f} | "
            f"{'#' * g_bar}{'.' * (15 - g_bar)} | "
            f"{'#' * f_bar}{'.' * (15 - f_bar)}"
        )

    # Tension std (specialization)
    g_stds = [s["std"] for s in growing_tension[:n_blocks]]
    f_stds = [s["std"] for s in fixed_tension[:n_blocks]]
    lines.append(f"\n  Tension std (specialization):")
    lines.append(f"    Growing: mean={np.mean(g_stds):.4f}, range=[{min(g_stds):.4f}, {max(g_stds):.4f}]")
    lines.append(f"    Fixed:   mean={np.mean(f_stds):.4f}, range=[{min(f_stds):.4f}, {max(f_stds):.4f}]")
    lines.append(f"    Ratio (G/F): {np.mean(g_stds) / (np.mean(f_stds) + 1e-8):.2f}x")

    return '\n'.join(lines)


def generate_report(growing_results, fixed_results):
    """Generate full markdown comparison report."""
    gr = growing_results
    fr = fixed_results

    # PPL thresholds for convergence speed
    ppl_thresholds = [500, 200, 100, 50]

    lines = []
    lines.append("=" * 70)
    lines.append("  Growing vs Fixed ConsciousLM — Comparison Report")
    lines.append("=" * 70)

    # ── Summary Table ──
    lines.append("\n## Summary")
    lines.append("")
    lines.append("| Metric | Growing (1->6) | Fixed (6) | Winner |")
    lines.append("|---|---|---|---|")

    # Final PPL
    g_ppl = gr["final_ppl"]
    f_ppl = fr["final_ppl"]
    winner = "Growing" if g_ppl < f_ppl else "Fixed"
    lines.append(f"| Final PPL | {g_ppl:.2f} | {f_ppl:.2f} | {winner} |")

    # Final val loss
    g_vl = gr["final_val_loss"]
    f_vl = fr["final_val_loss"]
    winner = "Growing" if g_vl < f_vl else "Fixed"
    lines.append(f"| Final val loss | {g_vl:.4f} | {f_vl:.4f} | {winner} |")

    # Final BPC
    g_bpc = g_vl / math.log(2)
    f_bpc = f_vl / math.log(2)
    winner = "Growing" if g_bpc < f_bpc else "Fixed"
    lines.append(f"| Final BPC | {g_bpc:.4f} | {f_bpc:.4f} | {winner} |")

    # Parameters
    lines.append(f"| Final params | {gr['final_params']:,} | {fr['final_params']:,} | - |")

    # Param efficiency
    g_eff = param_efficiency(g_ppl, gr["final_params"])
    f_eff = param_efficiency(f_ppl, fr["final_params"])
    winner = "Growing" if g_eff < f_eff else "Fixed"
    lines.append(f"| PPL/M params | {g_eff:.4f} | {f_eff:.4f} | {winner} |")

    # Training time
    g_time = gr["total_time"]
    f_time = fr["total_time"]
    winner = "Growing" if g_time < f_time else "Fixed"
    lines.append(f"| Training time (s) | {g_time:.0f} | {f_time:.0f} | {winner} |")

    # Loss stability
    g_var = compute_loss_variance(gr["log"])
    f_var = compute_loss_variance(fr["log"])
    winner = "Growing" if g_var < f_var else "Fixed"
    lines.append(f"| Loss variance | {g_var:.6f} | {f_var:.6f} | {winner} |")

    # ── Convergence Speed ──
    lines.append("\n## Convergence Speed (steps to reach PPL threshold)")
    lines.append("")
    lines.append("| PPL Threshold | Growing | Fixed | Winner |")
    lines.append("|---|---|---|---|")
    for thr in ppl_thresholds:
        g_step = find_convergence_step(gr["log"], thr)
        f_step = find_convergence_step(fr["log"], thr)
        g_str = str(g_step) if g_step else "N/A"
        f_str = str(f_step) if f_step else "N/A"
        if g_step and f_step:
            winner = "Growing" if g_step < f_step else "Fixed"
        elif g_step:
            winner = "Growing"
        elif f_step:
            winner = "Fixed"
        else:
            winner = "N/A"
        lines.append(f"| PPL < {thr} | {g_str} | {f_str} | {winner} |")

    # ── Step-by-step log (sampled) ──
    lines.append("\n## Training Log (sampled every 2000 steps)")
    lines.append("")
    lines.append("| Step | G_loss | G_BPC | G_PPL | G_params | F_loss | F_BPC | F_PPL |")
    lines.append("|---|---|---|---|---|---|---|---|")

    # Build step-indexed maps
    g_map = {e["step"]: e for e in gr["log"]}
    f_map = {e["step"]: e for e in fr["log"]}

    for step in range(LOG_INTERVAL, TOTAL_STEPS + 1, 2000):
        # Find nearest logged step
        ge = g_map.get(step)
        fe = f_map.get(step)
        if ge and fe:
            lines.append(
                f"| {step} | {ge['loss_a']:.4f} | {ge['bpc']:.3f} | {ge['ppl']:.1f} | "
                f"{ge['n_params']:,} | {fe['loss_a']:.4f} | {fe['bpc']:.3f} | {fe['ppl']:.1f} |"
            )

    # ── ASCII Curves ──
    lines.append(ascii_loss_curve(gr["log"], fr["log"], metric="loss_a"))
    lines.append(ascii_loss_curve(gr["log"], fr["log"], metric="bpc"))

    # ── Tension Analysis ──
    lines.append(ascii_tension_bars(gr["final_tension"], fr["final_tension"]))

    # ── Conclusion ──
    lines.append("\n## Conclusion")
    lines.append("")

    ppl_diff = f_ppl - g_ppl
    ppl_pct = (ppl_diff / f_ppl) * 100 if f_ppl > 0 else 0

    if g_ppl < f_ppl:
        lines.append(f"Growing model achieves {abs(ppl_pct):.1f}% lower PPL than Fixed "
                      f"({g_ppl:.2f} vs {f_ppl:.2f}).")
        lines.append("Mitosis-based growth provides a curriculum effect: learning simpler "
                      "representations first, then expanding capacity.")
    elif f_ppl < g_ppl:
        lines.append(f"Fixed model achieves {abs(ppl_pct):.1f}% lower PPL than Growing "
                      f"({f_ppl:.2f} vs {g_ppl:.2f}).")
        lines.append("The fixed architecture benefits from having full capacity available "
                      "throughout training.")
    else:
        lines.append("Both models achieve comparable PPL.")

    eff_diff = g_eff - f_eff
    if g_eff < f_eff:
        lines.append(f"Growing is {abs(eff_diff / f_eff * 100):.1f}% more parameter-efficient.")
    elif f_eff < g_eff:
        lines.append(f"Fixed is {abs(eff_diff / g_eff * 100):.1f}% more parameter-efficient.")

    g_tension_std = np.mean([s["std"] for s in gr["final_tension"]])
    f_tension_std = np.mean([s["std"] for s in fr["final_tension"]])
    if g_tension_std > f_tension_std:
        lines.append(f"Growing shows {g_tension_std / (f_tension_std + 1e-8):.2f}x higher "
                      "tension diversity (block specialization).")
    else:
        lines.append(f"Fixed shows {f_tension_std / (g_tension_std + 1e-8):.2f}x higher "
                      "tension diversity (block specialization).")

    lines.append("")
    lines.append("=" * 70)

    report = '\n'.join(lines)
    return report


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

    print("=" * 70)
    print("  Growing vs Fixed ConsciousLM — Paper Comparison Experiment")
    print(f"  Device: {device}")
    print(f"  Total steps: {TOTAL_STEPS}")
    print(f"  Block size: {BLOCK_SIZE}")
    print(f"  Fixed config: {FIXED_N_LAYER} blocks, d={FIXED_D_MODEL}, heads={FIXED_N_HEAD}")
    print(f"  Growing stages: {[s['blocks'] for s in GROWTH_STAGES]} blocks")
    print("=" * 70)

    # Prepare data
    print("\n  Preparing data...")
    data = prepare_data()
    print(f"  Data: {len(data):,} bytes")

    # ── Train Growing ──
    growing_results = train_growing(data, device)

    # ── Train Fixed ──
    fixed_results = train_fixed(data, device)

    # ── Generate Report ──
    report = generate_report(growing_results, fixed_results)
    print(report)

    # Save results as JSON (for further analysis)
    save_data = {
        "config": {
            "total_steps": TOTAL_STEPS,
            "block_size": BLOCK_SIZE,
            "fixed": {"d_model": FIXED_D_MODEL, "n_head": FIXED_N_HEAD, "n_layer": FIXED_N_LAYER},
            "growth_stages": GROWTH_STAGES,
            "lr_schedule": {str(k): v for k, v in LR_SCHEDULE.items()},
            "device": device,
        },
        "growing": {
            "log": growing_results["log"],
            "final_ppl": growing_results["final_ppl"],
            "final_val_loss": growing_results["final_val_loss"],
            "final_params": growing_results["final_params"],
            "total_time": growing_results["total_time"],
            "final_tension": growing_results["final_tension"],
        },
        "fixed": {
            "log": fixed_results["log"],
            "final_ppl": fixed_results["final_ppl"],
            "final_val_loss": fixed_results["final_val_loss"],
            "final_params": fixed_results["final_params"],
            "total_time": fixed_results["total_time"],
            "final_tension": fixed_results["final_tension"],
        },
    }

    with open(RESULTS_FILE, "w") as f:
        json.dump(save_data, f, indent=2)
    print(f"\n  Results saved to {RESULTS_FILE}")

    # Save markdown report
    report_path = "growing_vs_fixed_report.md"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"  Report saved to {report_path}")


if __name__ == "__main__":
    main()
