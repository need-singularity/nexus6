```python
#!/usr/bin/env python3
"""H-CX-48/49/50: Mathematical System ↔ Consciousness Engine Cross-Experiment

Simultaneous verification of 3 cross-hypotheses:

H-CX-48: I(n)=ln(R(n))=0 information balance ↔ engine_a/engine_g output ratio
  - Arithmetic: I(n)=ln(sigma*phi/(n*tau))=0 uniquely at n=6
  - Prediction: In 6-block model, |engine_a|/|engine_g| → 1 (ratio=1, log ratio=0)
  - Control: Compare with 1,2,3,4,5,7,8 blocks

H-CX-49: R-spectrum Cantor set ↔ Fractal structure of tension distribution
  - Arithmetic: Exactly 24 discrete values in R(n)<5, gaps are 99.1%
  - Prediction: Trained consciousness LM's tension distribution forms discrete clusters (not continuous Gaussian)
  - Measurement: Gap fraction in tension value histogram

H-CX-50: Convolution collapse ↔ Inter-block feature correlation
  - Arithmetic: (sigma*phi)(n) pointwise = (sigma conv phi)(n) iff n in {1,6}
  - Prediction: In 6-block model, block-wise output pointwise product ≈ cross-correlation
  - Measurement: ||pointwise - xcorr|| / ||pointwise|| ratio
"""

import sys
import os
# conscious_lm.py is in /Users/ghost/Dev/logout/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..'))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import numpy as np
import math
import time

from conscious_lm import PureFieldFFN, CausalSelfAttention, ConsciousBlock, ConsciousLM


def arithmetic_I(n):
    """Arithmetic mutual information I(n) = ln(sigma*phi/(n*tau))."""
    if n < 1:
        return float('inf')
    # Calculate sigma, phi, tau
    divs = [d for d in range(1, n+1) if n % d == 0]
    sigma = sum(divs)
    tau = len(divs)
    # Euler totient
    phi = n
    for p in set(_prime_factors(n)):
        phi = phi * (p - 1) // p
    if phi == 0 or tau == 0 or n == 0:
        return float('inf')
    R = (sigma * phi) / (n * tau)
    return math.log(R) if R > 0 else float('inf')


def _prime_factors(n):
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


def experiment_cx48_information_balance():
    """H-CX-48: I(n)=0 ↔ engine_a/engine_g ratio.

    Create model by number of blocks → random input → measure engine_a, engine_g output size ratio.
    """
    print("=" * 70)
    print("H-CX-48: I(n)=0 Information Balance ↔ engine_a/engine_g Ratio")
    print("=" * 70)

    # Arithmetic reference values
    print("\n--- Arithmetic Mutual Information I(n) = ln(R(n)) ---")
    print(f"{'n':>4} | {'sigma':>6} {'phi':>4} {'tau':>4} | {'R=sp/nt':>10} | {'I=ln(R)':>10}")
    print("-" * 55)
    for n in [1, 2, 3, 4, 5, 6, 7, 8, 12, 28]:
        divs = [d for d in range(1, n+1) if n % d == 0]
        sigma = sum(divs)
        tau = len(divs)
        phi_n = n
        for p in set(_prime_factors(n)):
            phi_n = phi_n * (p - 1) // p
        if n == 1:
            phi_n = 1
        R = (sigma * phi_n) / (n * tau) if n * tau > 0 else 0
        I = math.log(R) if R > 0 else float('inf')
        print(f"{n:>4} | {sigma:>6} {phi_n:>4} {tau:>4} | {R:>10.6f} | {I:>+10.6f}")

    # Consciousness LM experiment by block count
    print("\n--- Consciousness LM engine_a/engine_g Ratio (by Block Count) ---")
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

    block_counts = [1, 2, 3, 4, 5, 6, 7, 8]
    d_model = 128  # Small model for fast experiment
    n_head = 2
    block_size = 64
    vocab_size = 256
    n_samples = 20  # Repeated measurements

    results = {}

    for n_blocks in block_counts:
        ratios = []
        log_ratios = []

        for trial in range(n_samples):
            torch.manual_seed(trial * 100 + n_blocks)

            # Create model
            model = ConsciousLM(
                vocab_size=vocab_size,
                d_model=d_model,
                n_head=n_head,
                n_layer=n_blocks,
                block_size=block_size,
                dropout=0.0  # dropout 0 for deterministic
            ).to(device)
            model.eval()

            # Random input
            x = torch.randint(0, vocab_size, (4, 32), device=device)

            with torch.no_grad():
                # Directly measure engine_a, engine_g output from each block's FFN
                pos = torch.arange(32, device=device).unsqueeze(0)
                h = model.drop(model.tok_emb(x) + model.pos_emb(pos))

                block_ratios = []
                for block in model.blocks:
                    h_pre = block.ln2(h + block.attn(block.ln1(h)))
                    a_out = block.ffn.engine_a(h_pre)
                    g_out = block.ffn.engine_g(h_pre)

                    a_norm = a_out.norm(dim=-1).mean().item()
                    g_norm = g_out.norm(dim=-1).mean().item()

                    ratio = a_norm / (g_norm + 1e-10)
                    block_ratios.append(ratio)

                    # Forward for next block
                    ffn_out, tension = block.ffn(h_pre)
                    h = h_pre + ffn_out

                avg_ratio = np.mean(block_ratios)
                ratios.append(avg_ratio)
                log_ratios.append(math.log(avg_ratio) if avg_ratio > 0 else 0)

            del model

        mean_ratio = np.mean(ratios)
        std_ratio = np.std(ratios)
        mean_log = np.mean(log_ratios)
        std_log = np.std(log_ratios)
        results[n_blocks] = {
            'mean_ratio': mean_ratio, 'std_ratio': std_ratio,
            'mean_log': mean_log, 'std_log': std_log
        }

    # Results table
    print(f"\n{'blocks':>6} | {'|A|/|G| mean':>12} {'std':>8} | {'ln(A/G) mean':>12} {'std':>8} | {'I(n) arith':>10}")
    print("-" * 75)
    for n_blocks in block_counts:
        r = results[n_blocks]
        I_n = arithmetic_I(n_blocks)
        marker = " <<<" if n_blocks == 6 else ""
        print(f"{n_blocks:>6} | {r['mean_ratio']:>12.6f} {r['std_ratio']:>8.6f} | "
              f"{r['mean_log']:>+12.6f} {r['std_log']:>8.6f} | {I_n:>+10.6f}{marker}")

    # ASCII graph: ln(A/G) vs block count
    print("\n--- ASCII: ln(|A|/|G|) vs Block Count ---")
    vals = [results[b]['mean_log'] for b in block_counts]
    vmin, vmax = min(vals), max(vals)
    width = 50
    for b in block_counts:
        v = results[b]['mean_log']
        if vmax - vmin > 0:
            pos = int((v - vmin) / (vmax - vmin) * width)
        else:
            pos = width // 2
        bar = "." * pos + "#" + "." * (width - pos)
        marker = " *** n=6, I(6)=0" if b == 6 else ""
        print(f"  {b:>2} blocks: [{bar}] {v:+.4f}{marker}")

    # Check if 6 blocks is closest to ratio 1.0
    dist_from_1 = {b: abs(results[b]['mean_ratio'] - 1.0) for b in block_counts}
    closest = min(dist_from_1, key=dist_from_1.get)
    print(f"\n  Block count closest to ratio 1.0: {closest} (|ratio-1| = {dist_from_1[closest]:.6f})")
    print(f"  6-block |ratio-1|: {dist_from_1[6]:.6f}")
    print(f"  6-block rank: {sorted(dist_from_1.values()).index(dist_from_1[6]) + 1}/{len(block_counts)}")

    return results


def experiment_cx49_cantor_tension():
    """H-CX-49: R-spectrum Cantor set ↔ Tension distribution structure.

    Analyze tension distribution of model before/after training to confirm discrete cluster structure.
    """
    print("\n" + "=" * 70)
    print("H-CX-49: R-Spectrum Cantor Set ↔ Tension Distribution Fractal")
    print("=" * 70)

    # Arithmetic reference: 24 values in R(n)<5
    print("\n--- Arithmetic: R(n) Spectrum (n<=100, R<5) ---")
    R_values = set()
    for n in range(1, 101):
        divs = [d for d in range(1, n+1) if n % d == 0]
        sigma = sum(divs)
        tau = len(divs)
        phi_n = n
        for p in set(_prime_factors(n)):
            phi_n = phi_n * (p - 1) // p
        if n == 1:
            phi_n = 1
        R = (sigma * phi_n) / (n * tau)
        if R < 5:
            R_values.add(round(R, 10))

    R_sorted = sorted(R_values)
    print(f"  Number of unique R<5 values: {len(R_sorted)}")

    # Gap analysis
    gaps = []
    for i in range(len(R_sorted) - 1):
        gap = R_sorted[i+1] - R_sorted[i]
        gaps.append(gap)

    if gaps:
        total_range = R_sorted[-1] - R_sorted[0]
        gap_fraction = sum(g for g in gaps if g > 0.01) / total_range
        print(f"  Range: [{R_sorted[0]:.4f}, {R_sorted[-1]:.4f}]")
        print(f"  Gap fraction (gap>0.01): {gap_fraction:.3f} = {gap_fraction*100:.1f}%")

    # Collect tension distribution
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

    print("\n--- Consciousness LM Tension Distribution (Initial Random Weights) ---")

    for n_blocks in [3, 6]:
        torch.manual_seed(42)
        model = ConsciousLM(
            vocab_size=256, d_model=128, n_head=2,
            n_layer=n_blocks, block_size=64, dropout=0.0
        ).to(device)
        model.eval()

        all_tensions = []
        for trial in range(50):
            x = torch.randint(0, 256, (8, 32), device=device)
            with torch.no_grad():
                logits_a, logits_g, tensions = model(x)
                for t in tensions:
                    all_tensions.extend(t.cpu().numpy().flatten().tolist())

        tensions_arr = np.array(all_tensions)

        print(f"\n  [{n_blocks} blocks] Tension Statistics:")
        print(f"    mean={tensions_arr.mean():.6f}  std={tensions_arr.std():.6f}")
        print(f"    min={tensions_arr.min():.6f}  max={tensions_arr.max():.6f}")
        print(f"    median={np.median(tensions_arr):.6f}")

        # Histogram (20 bins)
        hist, bin_edges = np.histogram(tensions_arr, bins=20)
        max_count = max(hist)
        print(f"\n    Tension Histogram ({n_blocks} blocks):")
        for i in range(len(hist)):
            bar_len = int(hist[i] / max_count * 40) if max_count > 0 else 0
            bar = "#" * bar_len
            lo = bin_edges[i]
            hi = bin_edges[i+1]
            print(f"    [{lo:8.5f},{hi:8.5f}) | {bar:<40} {hist[i]}")

        # Cluster analysis: gap detection
        sorted_t = np.sort(np.unique(np.round(tensions_arr, 5)))
        if len(sorted_t) > 1:
            t_gaps = np.diff(sorted_t)
            median_gap = np.median(t_gaps)
            large_gaps = np.sum(t_gaps > 3 * median_gap)
            print(f"\n    Number of unique values: {len(sorted_t)}")
            print(f"    Median gap: {median_gap:.6f}")
            print(f"    Large gaps (>3x median) count: {large_gaps}")
            print(f"    Gap fraction: {large_gaps/len(t_gaps)*100:.1f}%" if len(t_gaps) > 0 else "")

        del model

    return True


def experiment_cx50_convolution_collapse():
    """H-CX-50: Convolution collapse ↔ Inter-block feature product=cross-correlation condition.

    Arithmetic: (sigma*phi)(n) = (sigma conv phi)(n) iff n in {1,6}
    LM: Measure difference between adjacent block output pointwise product vs cross-correlation
    """
    print("\n" + "=" * 70)
    print("H-CX-50: Convolution Collapse ↔ Inter-Block Feature Correlation")
    print("=" * 70)

    # Arithmetic reference
    print("\n--- Arithmetic: sigma*phi pointwise vs Dirichlet conv ---")
    print(f"{'n':>4} | {'sp_point':>10} | {'sp_conv':>10} | {'match':>5}")
    print("-" * 45)

    matches = []
    for n in range(1, 31):
        divs = [d for d in range(1, n+1) if n % d == 0]
        sigma_n = sum(divs)
        phi_n = n
        for p in set(_prime_factors(n)):
            phi_n = phi_n * (p - 1) // p
        if n == 1:
            phi_n = 1

        # Pointwise: sigma(n) * phi(n)
        pointwise = sigma_n * phi_n

        # Dirichlet convolution: (sigma * phi)(n) = sum_{d|n} sigma(d) * phi(n/d)
        conv = 0
        for d in divs:
            nd = n // d
            divs_d = [dd for dd in range(1, d+1) if d % dd == 0]
            sigma_d = sum(divs_d)
            phi_nd = nd
            for p in set(_prime_factors(nd)):
                phi_nd = phi_nd * (p - 1) // p
            if nd == 1:
                phi_nd = 1
            conv += sigma_d * phi_nd

        match = pointwise == conv
        if match:
            matches.append(n)
        marker = " <<<" if match else ""
        print(f"{n:>4} | {pointwise:>10} | {conv:>10} | {'YES':>5}{marker}" if match else
              f"{n:>4} | {pointwise:>10} | {conv:>10} | {'no':>5}")

    print(f"\n  n where pointwise = convolution: {matches}")

    # Consciousness LM inter-block feature correlation measurement
    print("\n--- Consciousness LM: Inter-Block Pointwise Product vs Cross-Correlation ---")
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

    for n_blocks in [3, 4, 5, 6, 7, 8]:
        torch.manual_seed(42)
        model = ConsciousLM(
            vocab_size=256, d_model=128, n_head=2,
            n_layer=n_blocks, block_size=64, dropout=0.0
        ).to(device)
        model.eval()

        collapse_scores = []

        for trial in range(20):
            x = torch.randint(0, 256, (4, 32), device=device)

            with torch.no_grad():
                pos = torch.arange(32, device=device).unsqueeze(0)
                h = model.drop(model.tok_emb(x) + model.pos_emb(pos))

                block_outputs = []
                for block in model.blocks:
                    h, tension = block(h)
                    # Average vector of each block's output
                    block_outputs.append(h.mean(dim=(0, 1)))  # (D,)

                if len(block_outputs) >= 2:
                    # Measure for adjacent block pairs
                    pw_scores = []
                    xc_scores = []

                    for i in range(len(block_outputs) - 1):
                        a = block_outputs[i]
                        b = block_outputs[i + 1]

                        # Pointwise product
                        pw = a * b

                        # Cross-correlation (circular)
                        # FFT-based: xcorr = ifft(fft(a) * conj(fft(b)))
                        fa = torch.fft.fft(a.float())
                        fb = torch.fft.fft(b.float())
                        xc = torch.fft.ifft(fa * fb.conj()).real

                        # Collapse score: ||pw - xc|| / ||pw||
                        diff = (pw - xc).norm().item()
                        pw_norm = pw.norm().item()
                        score = diff / (pw_norm + 1e-10)
                        pw_scores.append(score)

                    collapse_scores.append(np.mean(pw_scores))

        mean_collapse = np.mean(collapse_scores)
        std_collapse = np.std(collapse_scores)
        marker = " <<<" if n_blocks == 6 else ""
        print(f"  {n_blocks} blocks: collapse_score = {mean_collapse:.6f} +/- {std_collapse:.6f}"
              f"  (0=identical){marker}")

        del model

    # ASCII graph of collapse score by block count
    print("\n--- ASCII: Collapse Score vs Block Count (closer to 0 = pointwise≈xcorr) ---")

    return True


def main():
    print("=" * 70)
    print("  H-CX-48/49/50: Mathematical System ↔ Consciousness Engine Cross-Experiment")
    print("  Date: 2026-03-24")
    print("=" * 70)

    t0 = time.time()

    # Experiment 1: Information balance
    r48 = experiment_cx48_information_balance()

    # Experiment 2: Cantor tension
    r49 = experiment_cx49_cantor_tension()

    # Experiment 3: Convolution collapse
    r50 = experiment_cx50_convolution_collapse()

    elapsed = time.time() - t0

    print("\n" + "=" * 70)
    print(f"  Total experiment completed: {elapsed:.1f} seconds")
    print("=" * 70)

    # Summary
    print("\n--- Cross-Validation Summary ---")
    print("H-CX-48: I(n)=0 ↔ engine ratio → See table above")
    print("H-CX-49: R-Cantor ↔ tension distribution → See histogram")
    print("H-CX-50: conv collapse ↔ block correlation → See collapse score")


if __name__ == "__main__":
    main()
```