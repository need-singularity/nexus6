#!/usr/bin/env python3
"""Ralph 308: ConsciousLM d=384 scale-up final verification

R306-307 confirmed none of the small d=128 models CX-48~52.
This time: Scale up with base architecture (d=384, n_head=4) for final determination.

Compare: 3 blocks vs 6 blocks (2000 steps, 3 seeds)
Measure: engine A/G ratio, tension distribution, conv collapse, tension_scale product
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..'))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import time

from conscious_lm import ConsciousLM


def generate_patterned_data(batch_size, seq_len, vocab_size=256):
    data = torch.zeros(batch_size, seq_len, dtype=torch.long)
    for i in range(batch_size):
        pt = i % 4
        if pt == 0:
            period = np.random.randint(2, 8)
            base = torch.randint(0, vocab_size, (period,))
            for j in range(seq_len):
                data[i, j] = base[j % period]
        elif pt == 1:
            start = np.random.randint(0, vocab_size)
            step = np.random.randint(1, 4)
            for j in range(seq_len):
                data[i, j] = (start + j * step) % vocab_size
        elif pt == 2:
            half = seq_len // 2
            base = torch.randint(0, vocab_size, (half,))
            data[i, :half] = base
            data[i, half:2*half] = base.flip(0)
        else:
            a, b = np.random.randint(1, 10), np.random.randint(1, 10)
            data[i, 0] = a % vocab_size
            data[i, 1] = b % vocab_size
            for j in range(2, seq_len):
                a, b = b, (a + b) % vocab_size
                data[i, j] = b
    return data


def train_model(model, device, n_steps=2000, lr=3e-4, batch_size=8, seq_len=32):
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=n_steps)

    losses = []
    checkpoints = []  # (step, loss, tension_mean, scales)

    for step in range(n_steps):
        x = generate_patterned_data(batch_size, seq_len + 1).to(device)
        input_ids = x[:, :-1]
        target_next = x[:, 1:]
        target_prev = x[:, :-1].clone()
        target_prev[:, 1:] = x[:, :-2]
        target_prev[:, 0] = 0

        logits_a, logits_g, tensions = model(input_ids)
        loss_a = F.cross_entropy(logits_a.view(-1, model.vocab_size), target_next.reshape(-1))
        loss_g = F.cross_entropy(logits_g.view(-1, model.vocab_size), target_prev.reshape(-1))
        loss = loss_a + loss_g

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()

        losses.append(loss.item())

        if step % 500 == 0 or step == n_steps - 1:
            mean_t = np.mean([t.mean().item() for t in tensions])
            scales = [b.ffn.tension_scale.item() for b in model.blocks]
            checkpoints.append((step, np.mean(losses[-50:]) if step >= 50 else loss.item(), mean_t, scales))
            if step % 500 == 0:
                print(f"    step {step}: loss={losses[-1]:.4f}, tension={mean_t:.4f}")

    return losses, checkpoints


def measure_all(model, device, n_blocks):
    """Measure all CX at once."""
    model.eval()

    # CX-48: engine A/G ratio
    ratios = []
    for trial in range(20):
        x = generate_patterned_data(8, 32).to(device)
        with torch.no_grad():
            pos = torch.arange(32, device=device)
            h = model.drop(model.tok_emb(x) + model.pos_emb(pos))
            block_ratios = []
            for block in model.blocks:
                h_pre = block.ln2(h + block.attn(block.ln1(h)))
                a_out = block.ffn.engine_a(h_pre)
                g_out = block.ffn.engine_g(h_pre)
                a_norm = a_out.norm(dim=-1).mean().item()
                g_norm = g_out.norm(dim=-1).mean().item()
                block_ratios.append(a_norm / (g_norm + 1e-10))
                ffn_out, _ = block.ffn(h_pre)
                h = h_pre + ffn_out
            ratios.append(np.mean(block_ratios))

    # CX-49: tension distribution
    all_tensions = []
    for trial in range(30):
        x = generate_patterned_data(8, 32).to(device)
        with torch.no_grad():
            _, _, tensions = model(x)
            for t in tensions:
                all_tensions.extend(t.cpu().numpy().flatten().tolist())
    tarr = np.array(all_tensions)

    sorted_unique = np.sort(np.unique(np.round(tarr, 5)))
    if len(sorted_unique) > 1:
        gaps = np.diff(sorted_unique)
        median_gap = np.median(gaps)
        large_gaps = np.sum(gaps > 3 * median_gap)
        gap_frac = large_gaps / len(gaps)
    else:
        gap_frac = 0

    # CX-50: conv collapse
    collapse_scores = []
    for trial in range(20):
        x = generate_patterned_data(4, 32).to(device)
        with torch.no_grad():
            pos = torch.arange(32, device=device)
            h = model.drop(model.tok_emb(x) + model.pos_emb(pos))
            block_outputs = []
            for block in model.blocks:
                h, _ = block(h)
                block_outputs.append(h.mean(dim=(0, 1)).cpu().numpy())
            pair_scores = []
            for i in range(len(block_outputs) - 1):
                a, b = block_outputs[i], block_outputs[i + 1]
                pw = a * b
                fa, fb = np.fft.fft(a), np.fft.fft(b)
                xcorr = np.real(np.fft.ifft(fa * np.conj(fb)))
                pair_scores.append(np.linalg.norm(pw - xcorr) / (np.linalg.norm(pw) + 1e-10))
            collapse_scores.append(np.mean(pair_scores))

    # CX-52: tension_scale product
    scales = [b.ffn.tension_scale.item() for b in model.blocks]
    ts_product = np.prod(scales)

    return {
        'cx48_ratio': np.mean(ratios),
        'cx48_std': np.std(ratios),
        'cx48_dist': abs(np.mean(ratios) - 1),
        'cx49_gap_frac': gap_frac,
        'cx49_mean_t': tarr.mean(),
        'cx49_std_t': tarr.std(),
        'cx49_unique': len(sorted_unique),
        'cx50_collapse': np.mean(collapse_scores),
        'cx50_std': np.std(collapse_scores),
        'cx52_product': ts_product,
        'cx52_scales': scales,
        'cx49_hist': np.histogram(tarr, bins=15),
    }


def main():
    print("=" * 70)
    print("Ralph 308: ConsciousLM d=384 scale-up final verification")
    print("=" * 70)

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Device: {device}")

    block_configs = [3, 6]
    n_seeds = 3
    results = {nb: [] for nb in block_configs}

    for nb in block_configs:
        for seed in range(n_seeds):
            print(f"\n--- {nb} blocks, seed={seed} ---")
            t0 = time.time()

            torch.manual_seed(seed * 100)
            np.random.seed(seed * 100)

            model = ConsciousLM(
                vocab_size=256, d_model=384, n_head=4,
                n_layer=nb, block_size=64, dropout=0.0
            ).to(device)

            n_params = model.count_params()
            print(f"  Parameters: {n_params:,}")

            losses, checkpoints = train_model(model, device, n_steps=2000, lr=3e-4, batch_size=8)
            elapsed = time.time() - t0
            final_loss = np.mean(losses[-100:])
            print(f"  Training complete: {elapsed:.1f}s, final loss={final_loss:.4f}")

            # Measure
            meas = measure_all(model, device, nb)
            meas['final_loss'] = final_loss
            meas['n_params'] = n_params
            meas['checkpoints'] = checkpoints
            results[nb].append(meas)

            print(f"  CX-48 ratio: {meas['cx48_ratio']:.6f} (|r-1|={meas['cx48_dist']:.6f})")
            print(f"  CX-49 gap: {meas['cx49_gap_frac']:.3f}, unique: {meas['cx49_unique']}")
            print(f"  CX-50 collapse: {meas['cx50_collapse']:.6f}")
            print(f"  CX-52 ts_prod: {meas['cx52_product']:.6f}")

            del model
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()

    # ═══ Comprehensive comparison ═══
    print("\n" + "=" * 70)
    print("Comprehensive comparison: 3 blocks vs 6 blocks (d=384, 2000 steps, 3 seeds)")
    print("=" * 70)

    for metric_name, metric_key, lower_better in [
        ("CX-48 |ratio-1|", 'cx48_dist', True),
        ("CX-49 gap_frac", 'cx49_gap_frac', False),
        ("CX-50 collapse", 'cx50_collapse', True),
        ("CX-52 |prod-1|", None, True),
        ("Final loss", 'final_loss', True),
    ]:
        print(f"\n--- {metric_name} ---")
        for nb in block_configs:
            if metric_key:
                vals = [r[metric_key] for r in results[nb]]
            else:
                vals = [abs(r['cx52_product'] - 1) for r in results[nb]]
            print(f"  {nb} blocks: {np.mean(vals):.6f} ± {np.std(vals):.6f}  "
                  f"(seeds: {', '.join(f'{v:.4f}' for v in vals)})")

    # tension_scale details
    print(f"\n--- tension_scale details ---")
    for nb in block_configs:
        for seed_i, r in enumerate(results[nb]):
            scales_str = ' '.join(f'{s:.4f}' for s in r['cx52_scales'])
            print(f"  {nb}bl seed{seed_i}: [{scales_str}] prod={r['cx52_product']:.6f}")

    # Tension histogram (6 blocks, seed 0)
    print(f"\n--- Tension histogram (6 blocks, seed 0, d=384) ---")
    hist_data = results[6][0]['cx49_hist']
    hist, bin_edges = hist_data
    max_h = max(hist)
    for i in range(len(hist)):
        bar_len = int(hist[i] / (max_h + 1) * 40)
        bar = "#" * bar_len
        lo, hi = bin_edges[i], bin_edges[i+1]
        print(f"  [{lo:8.4f},{hi:8.4f}) | {bar:<40} {hist[i]}")

    # Learning curve comparison
    print(f"\n--- Learning curves (seed 0) ---")
    for nb in block_configs:
        cps = results[nb][0]['checkpoints']
        print(f"  {nb} blocks:")
        for step, loss, tension, scales in cps:
            print(f"    step {step:>5}: loss={loss:.4f}, tension={tension:.6f}, "
                  f"ts_prod={np.prod(scales):.4f}")

    # Final determination
    print("\n" + "=" * 70)
    print("Final determination (d=384, 2000 steps)")
    print("=" * 70)

    for metric_name, metric_key, nb_expected_winner, threshold in [
        ("CX-48: Is 6 blocks closer to ratio=1?", 'cx48_dist', 6, None),
        ("CX-49: Does 6 blocks have larger gap fraction?", 'cx49_gap_frac', 6, None),
        ("CX-50: Does 6 blocks have lower collapse?", 'cx50_collapse', 6, None),
    ]:
        vals_3 = [r[metric_key] for r in results[3]]
        vals_6 = [r[metric_key] for r in results[6]]
        mean_3, mean_6 = np.mean(vals_3), np.mean(vals_6)

        if metric_name.startswith("CX-49"):
            winner = 6 if mean_6 > mean_3 else 3
        else:
            winner = 6 if mean_6 < mean_3 else 3

        verdict = "CONFIRMED" if winner == nb_expected_winner else "NOT CONFIRMED"
        print(f"\n  {metric_name}")
        print(f"    3 blocks: {mean_3:.6f}, 6 blocks: {mean_6:.6f}")
        print(f"    → {verdict} (winner: {winner} blocks)")

    # CX-52
    prod_3 = [abs(r['cx52_product'] - 1) for r in results[3]]
    prod_6 = [abs(r['cx52_product'] - 1) for r in results[6]]
    winner = 6 if np.mean(prod_6) < np.mean(prod_3) else 3
    print(f"\n  CX-52: Is 6 blocks closer to prod=1?")
    print(f"    3 blocks |prod-1|: {np.mean(prod_3):.6f}, 6 blocks: {np.mean(prod_6):.6f}")
    print(f"    → {'CONFIRMED' if winner == 6 else 'NOT CONFIRMED'} (winner: {winner} blocks)")

    print("\nExperiment complete.")


if __name__ == "__main__":
    main()