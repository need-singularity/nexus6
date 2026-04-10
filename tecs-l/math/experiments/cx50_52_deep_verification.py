#!/usr/bin/env python3
"""Ralph 307: H-CX-50 Deep Verification + H-CX-52 tension_scale Product Experiment

H-CX-50 Deep:
  In R306, 6-block collapse score=9.566 (1st) vs 7-block=9.589 (2nd)
  Difference 0.023 → Need statistical significance check
  1) Repeat with 10 seeds → calculate p-value
  2) Track collapse score changes during training

H-CX-52 (New):
  R(n) = sigma*phi/(n*tau) is multiplicative: R(mn)=R(m)R(n) for gcd(m,n)=1
  R(6) = R(2)*R(3) = (3/4)*(4/3) = 1
  Prediction: Product of learned tension_scale values in 6-block model → converges to 1?
  Control: In other block counts, product ≠ 1
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
    """Generate patterned byte sequences."""
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


def measure_conv_collapse(model, device, n_trials=20):
    """H-CX-50: convolution collapse score."""
    model.eval()
    scores = []
    for trial in range(n_trials):
        x = generate_patterned_data(4, 32).to(device)
        with torch.no_grad():
            pos = torch.arange(32, device=device)
            h = model.drop(model.tok_emb(x) + model.pos_emb(pos))
            block_outputs = []
            for block in model.blocks:
                h, tension = block(h)
                block_outputs.append(h.mean(dim=(0, 1)).cpu().numpy())
            pair_scores = []
            for i in range(len(block_outputs) - 1):
                a = block_outputs[i]
                b = block_outputs[i + 1]
                pw = a * b
                fa = np.fft.fft(a)
                fb = np.fft.fft(b)
                xcorr = np.real(np.fft.ifft(fa * np.conj(fb)))
                diff = np.linalg.norm(pw - xcorr)
                pw_norm = np.linalg.norm(pw) + 1e-10
                pair_scores.append(diff / pw_norm)
            scores.append(np.mean(pair_scores))
    return np.array(scores)


def train_and_track(model, device, n_steps=500, lr=1e-3, track_interval=50):
    """Train while tracking collapse score + tension_scale."""
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=n_steps)

    losses = []
    collapse_track = []
    tscale_track = []

    for step in range(n_steps):
        x = generate_patterned_data(16, 33).to(device)
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

        if step % track_interval == 0 or step == n_steps - 1:
            # collapse score
            model.eval()
            cs = measure_conv_collapse(model, device, n_trials=5)
            collapse_track.append((step, cs.mean(), cs.std()))
            model.train()

            # tension_scale values
            scales = []
            for block in model.blocks:
                scales.append(block.ffn.tension_scale.item())
            tscale_track.append((step, scales.copy()))

    return losses, collapse_track, tscale_track


def experiment_cx50_deep(device):
    """H-CX-50 Deep: 10-seed repetition + training process tracking."""
    print("=" * 70)
    print("H-CX-50 Deep: Statistical Significance + Training Process Tracking")
    print("=" * 70)

    block_counts = [3, 4, 5, 6, 7, 8]
    n_seeds = 10

    # Part A: 10-seed repetition
    print(f"\n--- Part A: {n_seeds}-seed repetition (collapse score after 500 steps training) ---")
    all_scores = {nb: [] for nb in block_counts}

    for seed in range(n_seeds):
        for nb in block_counts:
            torch.manual_seed(seed * 1000 + nb)
            np.random.seed(seed * 1000 + nb)

            model = ConsciousLM(
                vocab_size=256, d_model=128, n_head=2,
                n_layer=nb, block_size=64, dropout=0.0
            ).to(device)

            # Fast training (300 steps)
            model.train()
            optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)
            for step in range(300):
                x = generate_patterned_data(16, 33).to(device)
                input_ids = x[:, :-1]
                target_next = x[:, 1:]
                target_prev = x[:, :-1].clone()
                target_prev[:, 1:] = x[:, :-2]
                target_prev[:, 0] = 0
                logits_a, logits_g, tensions = model(input_ids)
                loss = (F.cross_entropy(logits_a.view(-1, 256), target_next.reshape(-1)) +
                        F.cross_entropy(logits_g.view(-1, 256), target_prev.reshape(-1)))
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()

            # Measure collapse score
            cs = measure_conv_collapse(model, device, n_trials=10)
            all_scores[nb].append(cs.mean())

            del model
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()

        print(f"  Seed {seed}: done")

    # Statistics table
    print(f"\n--- Statistics (10 seeds) ---")
    print(f"{'blocks':>6} | {'mean':>10} {'std':>10} {'min':>10} {'max':>10} | {'#1st':>5}")
    print("-" * 60)

    # Count 1st place by seed
    rank1_count = {nb: 0 for nb in block_counts}
    for seed in range(n_seeds):
        seed_scores = {nb: all_scores[nb][seed] for nb in block_counts}
        winner = min(seed_scores, key=seed_scores.get)
        rank1_count[winner] += 1

    for nb in block_counts:
        scores = all_scores[nb]
        marker = " <<<" if nb == 6 else ""
        print(f"{nb:>6} | {np.mean(scores):>10.4f} {np.std(scores):>10.4f} "
              f"{np.min(scores):>10.4f} {np.max(scores):>10.4f} | {rank1_count[nb]:>5}{marker}")

    # Welch t-test: 6-block vs others
    from scipy import stats as sp_stats
    print(f"\n--- Welch t-test: 6-block vs each block ---")
    print(f"{'comparison':>12} | {'t-stat':>10} {'p-value':>10} | {'significant':>12}")
    print("-" * 55)
    for nb in block_counts:
        if nb == 6:
            continue
        t_stat, p_val = sp_stats.ttest_ind(all_scores[6], all_scores[nb], equal_var=False)
        sig = "p<0.05" if p_val < 0.05 else "n.s."
        print(f"  6 vs {nb:>2}    | {t_stat:>+10.4f} {p_val:>10.4f} | {sig:>12}")

    # 6-block vs all others
    others = []
    for nb in block_counts:
        if nb != 6:
            others.extend(all_scores[nb])
    t_all, p_all = sp_stats.ttest_ind(all_scores[6], others, equal_var=False)
    print(f"  6 vs rest  | {t_all:>+10.4f} {p_all:>10.4f} | {'p<0.05' if p_all < 0.05 else 'n.s.':>12}")

    # ASCII boxplot
    print(f"\n--- ASCII: Collapse Score Distribution (10 seeds) ---")
    for nb in block_counts:
        scores = sorted(all_scores[nb])
        q1 = scores[2]
        median = scores[5]
        q3 = scores[7]
        lo, hi = scores[0], scores[-1]
        # Scaling
        global_min = min(min(all_scores[nb]) for nb in block_counts)
        global_max = max(max(all_scores[nb]) for nb in block_counts)
        width = 50

        def pos(v):
            return int((v - global_min) / (global_max - global_min + 1e-10) * width)

        line = [' '] * (width + 1)
        line[pos(lo)] = '|'
        line[pos(hi)] = '|'
        for p in range(pos(q1), pos(q3) + 1):
            if p < len(line):
                line[p] = '='
        line[pos(median)] = '#'

        marker = " *** n=6" if nb == 6 else ""
        print(f"  {nb:>2} blocks: [{''.join(line)}] {np.mean(scores):.4f}{marker}")

    # Part B: Training process tracking (6-block only)
    print(f"\n--- Part B: 6-block training process collapse score tracking ---")
    torch.manual_seed(42)
    model6 = ConsciousLM(
        vocab_size=256, d_model=128, n_head=2,
        n_layer=6, block_size=64, dropout=0.0
    ).to(device)

    losses, collapse_track, tscale_track = train_and_track(model6, device, n_steps=500, track_interval=50)

    print(f"\n  Training process collapse score:")
    print(f"  {'step':>6} | {'collapse':>10} {'std':>8}")
    print("  " + "-" * 30)
    for step, mean, std in collapse_track:
        print(f"  {step:>6} | {mean:>10.4f} {std:>8.4f}")

    # Collapse change ASCII
    print(f"\n  ASCII: Collapse Score vs Training Steps")
    vals = [m for _, m, _ in collapse_track]
    vmin, vmax = min(vals), max(vals)
    for step, mean, std in collapse_track:
        if vmax > vmin:
            pos = int((mean - vmin) / (vmax - vmin) * 40)
        else:
            pos = 20
        bar = "." * pos + "#" + "." * (40 - pos)
        print(f"  step {step:>4}: [{bar}] {mean:.4f}")

    del model6

    return all_scores, collapse_track


def experiment_cx52_tension_scale_product(device):
    """H-CX-52: R(n) multiplicative structure ↔ tension_scale product.

    R(6) = R(2)*R(3) = (3/4)*(4/3) = 1
    Prediction: Product of learned tension_scales in 6-block → 1.0?
    """
    print("\n" + "=" * 70)
    print("H-CX-52: R(n) Multiplicative ↔ tension_scale Product")
    print("=" * 70)

    print("\n--- Arithmetic Background ---")
    print("  R(n) = sigma*phi/(n*tau) is a multiplicative function")
    print("  R(mn) = R(m)*R(n) for gcd(m,n)=1")
    print("  R(6) = R(2)*R(3) = (3/4)*(4/3) = 1")
    print("  R(28) = R(4)*R(7) = (7/8)*(8/7)*(... ) = 4")
    print()
    print("  Prediction: Product of learned tension_scale in 6-block model → 1.0")
    print("  Control: In other block counts, product ≠ 1")

    block_counts = [3, 4, 5, 6, 7, 8]
    n_seeds = 5

    results = {nb: [] for nb in block_counts}
    scale_details = {nb: [] for nb in block_counts}

    for seed in range(n_seeds):
        for nb in block_counts:
            torch.manual_seed(seed * 100 + nb)
            np.random.seed(seed * 100 + nb)

            model = ConsciousLM(
                vocab_size=256, d_model=128, n_head=2,
                n_layer=nb, block_size=64, dropout=0.0
            ).to(device)

            # Training
            model.train()
            optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)
            for step in range(500):
                x = generate_patterned_data(16, 33).to(device)
                input_ids = x[:, :-1]
                target_next = x[:, 1:]
                target_prev = x[:, :-1].clone()
                target_prev[:, 1:] = x[:, :-2]
                target_prev[:, 0] = 0
                logits_a, logits_g, tensions = model(input_ids)
                loss = (F.cross_entropy(logits_a.view(-1, 256), target_next.reshape(-1)) +
                        F.cross_entropy(logits_g.view(-1, 256), target_prev.reshape(-1)))
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()

            # Extract tension_scale values
            scales = [block.ffn.tension_scale.item() for block in model.blocks]
            product = np.prod(scales)
            results[nb].append(product)
            scale_details[nb].append(scales)

            del model
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()

        print(f"  Seed {seed}: done")

    # Results table
    print(f"\n--- tension_scale Product (5 seeds) ---")
    print(f"{'blocks':>6} | {'mean_prod':>10} {'std':>10} | {'|prod-1|':>10} | {'R(n)':>8}")
    print("-" * 60)

    def compute_R(n):
        divs = [d for d in range(1, n+1) if n % d == 0]
        sigma = sum(divs)
        tau = len(divs)
        phi = n
        temp = n
        d = 2
        while d * d <= temp:
            if temp % d == 0:
                phi = phi * (d - 1) // d
                while temp % d == 0:
                    temp //= d
            d += 1
        if temp > 1:
            phi = phi * (temp - 1) // temp
        return sigma * phi / (n * tau)

    for nb in block_counts:
        prods = results[nb]
        R_n = compute_R(nb)
        marker = " <<<" if nb == 6 else ""
        print(f"{nb:>6} | {np.mean(prods):>10.6f} {np.std(prods):>10.6f} | "
              f"{abs(np.mean(prods) - 1):>10.6f} | {R_n:>8.4f}{marker}")

    # Individual block tension_scale (6-block details)
    print(f"\n--- 6-block tension_scale Details (5 seeds) ---")
    print(f"  {'seed':>4} | {'b1':>8} {'b2':>8} {'b3':>8} {'b4':>8} {'b5':>8} {'b6':>8} | {'product':>10}")
    print("  " + "-" * 80)
    for seed in range(n_seeds):
        scales = scale_details[6][seed]
        prod = results[6][seed]
        print(f"  {seed:>4} | {' '.join(f'{s:>8.4f}' for s in scales)} | {prod:>10.6f}")

    # ASCII
    print(f"\n--- ASCII: |tension_scale Product - 1| (lower is closer to R(n)=1 match) ---")
    dists = {nb: abs(np.mean(results[nb]) - 1) for nb in block_counts}
    dmax = max(dists.values()) + 1e-10
    for nb in block_counts:
        d = dists[nb]
        bar_len = int(d / dmax * 40)
        bar = "#" * bar_len + "." * (40 - bar_len)
        marker = " *** R(6)=1" if nb == 6 else ""
        print(f"  {nb:>2} blocks: [{bar}] {d:.6f}{marker}")

    # R(n) vs tension product correlation
    print(f"\n--- R(n) vs tension_scale Product Correlation ---")
    R_vals = [compute_R(nb) for nb in block_counts]
    prod_vals = [np.mean(results[nb]) for nb in block_counts]
    corr = np.corrcoef(R_vals, prod_vals)[0, 1]
    print(f"  Pearson r = {corr:.4f}")
    print(f"  {'n':>4} | {'R(n)':>8} | {'ts_prod':>10}")
    print("  " + "-" * 30)
    for nb in block_counts:
        print(f"  {nb:>4} | {compute_R(nb):>8.4f} | {np.mean(results[nb]):>10.6f}")

    return results, scale_details


def main():
    print("=" * 70)
    print("Ralph 307: H-CX-50 Deep Verification + H-CX-52 tension_scale Product")
    print("=" * 70)

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Device: {device}")

    t0 = time.time()

    # H-CX-50 Deep
    cx50_scores, cx50_track = experiment_cx50_deep(device)

    # H-CX-52
    cx52_prods, cx52_details = experiment_cx52_tension_scale_product(device)

    elapsed = time.time() - t0
    print(f"\n Total experiment time: {elapsed:.1f}s")

    # Overall Assessment
    print("\n" + "=" * 70)
    print("Overall Assessment")
    print("=" * 70)

    # CX-50: How many times is 6-block 1st out of 10 seeds?
    rank1 = sum(1 for seed in range(10)
                if min(range(len([3,4,5,6,7,8])),
                       key=lambda i: cx50_scores[[3,4,5,6,7,8][i]][seed]) == 3)  # index of 6
    # Direct calculation
    block_counts = [3,4,5,6,7,8]
    r1_count = 0
    for seed in range(10):
        seed_scores = {nb: cx50_scores[nb][seed] for nb in block_counts}
        if min(seed_scores, key=seed_scores.get) == 6:
            r1_count += 1

    print(f"\n  H-CX-50: 6-block is 1st in {r1_count} out of 10 seeds")
    if r1_count >= 7:
        print(f"  → 🟩 STRONGLY CONFIRMED (>= 70%)")
    elif r1_count >= 4:
        print(f"  → 🟧 CONFIRMED ({r1_count*10}%)")
    elif r1_count >= 2:
        print(f"  → 🟨 WEAK ({r1_count*10}%)")
    else:
        print(f"  → ⬛ NOT CONFIRMED ({r1_count*10}%)")

    # CX-52: Is 6-block tension_scale product closest to 1?
    dists = {nb: abs(np.mean(cx52_prods[nb]) - 1) for nb in block_counts}
    closest = min(dists, key=dists.get)
    print(f"\n  H-CX-52: Block count with tension_scale product closest to 1: {closest}")
    print(f"  6-block |prod-1|: {dists[6]:.6f}")
    if closest == 6:
        print(f"  → 🟧 CONFIRMED: 6-block is closest to product=1!")
    else:
        print(f"  → ⚪ NOT CONFIRMED: {closest}-block is closer")


if __name__ == "__main__":
    main()