#!/usr/bin/env python3
"""RC-10: Dreaming = Offline Replay with PureField

Key question: What does PureField "dream" about when given noise?
Can we find inputs that maximally excite the tension field?

Setup:
  1. AWAKE PHASE: Train PureFieldEngine on MNIST (10 epochs)
  2. DREAM PHASE: Feed random noise, record tension
     - Vivid dreams = highest tension noise
     - Dreamless sleep = lowest tension noise
  3. LUCID DREAMING: Gradient ascent on input to maximize tension
     - Find the inputs the engine "wants" to see most
  4. DREAM CLASSIFICATION: What digits do dreams look like?
  5. COMPARISON: Tension of real digits vs dreams vs random noise

Metrics:
  - Tension distributions: real vs noise vs optimized
  - Dream digit class distribution
  - Lucid dream convergence
  - Cosine similarity of dream directions to real digit centroids
"""

import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torchvision import datasets, transforms
from collections import Counter

from model_pure_field import PureFieldEngine


# ---------------------------------------------------------------------------
# ASCII visualization helpers
# ---------------------------------------------------------------------------

def ascii_histogram(values, title="", bins=20, width=50):
    """ASCII histogram."""
    values = np.array(values)
    if len(values) == 0:
        print(f"  [{title}] no data")
        return
    hist, edges = np.histogram(values, bins=bins)
    max_count = max(hist) if max(hist) > 0 else 1
    print(f"\n  [{title}]  n={len(values)}  mean={values.mean():.4f}  std={values.std():.4f}")
    for i, count in enumerate(hist):
        bar_len = int(count / max_count * width)
        lo, hi = edges[i], edges[i + 1]
        print(f"  {lo:8.4f}-{hi:8.4f} | {'#' * bar_len} ({count})")


def ascii_bar_chart(labels, values, title="", width=50):
    """ASCII horizontal bar chart."""
    max_val = max(values) if values else 1
    print(f"\n  [{title}]")
    for label, val in zip(labels, values):
        bar_len = int(val / max_val * width)
        print(f"  {label:>20s} | {'#' * bar_len} {val:.4f}")


def ascii_digit_grid(pixels, title="", size=28, width_chars=28):
    """Render a 784-dim vector as ASCII art (28x28)."""
    print(f"\n  {title}")
    pixels = np.array(pixels).reshape(size, size)
    chars = " .:-=+*#%@"
    for row in pixels:
        line = "  "
        for val in row:
            idx = int(np.clip(val, 0, 1) * (len(chars) - 1))
            line += chars[idx]
        print(line)


# ---------------------------------------------------------------------------
# Data & Training (reused from RC-8 pattern)
# ---------------------------------------------------------------------------

def load_mnist():
    """Load MNIST, return flat tensors."""
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Lambda(lambda x: x.view(-1)),
    ])
    train_ds = datasets.MNIST('/tmp/mnist', train=True, download=True, transform=transform)
    test_ds = datasets.MNIST('/tmp/mnist', train=False, download=True, transform=transform)
    return train_ds, test_ds


def train_pure_field(model, train_ds, epochs=10, batch_size=256, lr=1e-3):
    """Train PureFieldEngine on MNIST classification."""
    loader = torch.utils.data.DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    model.train()
    for epoch in range(epochs):
        total_loss = 0
        correct = 0
        total = 0
        for x, y in loader:
            output, tension = model(x)
            loss = F.cross_entropy(output, y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * x.size(0)
            correct += (output.argmax(1) == y).sum().item()
            total += x.size(0)

        acc = correct / total * 100
        avg_loss = total_loss / total
        print(f"  Epoch {epoch + 1:2d}/{epochs}: loss={avg_loss:.4f}  acc={acc:.1f}%")

    return model


# ---------------------------------------------------------------------------
# Phase 1: Awake phase - get real digit tension baseline
# ---------------------------------------------------------------------------

@torch.no_grad()
def awake_phase(model, test_ds, max_samples=10000):
    """Collect tension stats from real digits."""
    model.eval()
    loader = torch.utils.data.DataLoader(test_ds, batch_size=512, shuffle=False)

    all_tensions = []
    all_labels = []
    all_preds = []
    all_directions = []

    for x, y in loader:
        output, tension = model(x)
        preds = output.argmax(dim=1)

        # Get direction
        out_a = model.engine_a(x)
        out_g = model.engine_g(x)
        direction = F.normalize(out_a - out_g, dim=-1)

        all_tensions.append(tension.numpy())
        all_labels.append(y.numpy())
        all_preds.append(preds.numpy())
        all_directions.append(direction.numpy())

        if sum(len(a) for a in all_labels) >= max_samples:
            break

    tensions = np.concatenate(all_tensions)[:max_samples]
    labels = np.concatenate(all_labels)[:max_samples]
    preds = np.concatenate(all_preds)[:max_samples]
    directions = np.concatenate(all_directions)[:max_samples]

    return tensions, labels, preds, directions


# ---------------------------------------------------------------------------
# Phase 2: Dream phase - random noise through the model
# ---------------------------------------------------------------------------

@torch.no_grad()
def dream_phase(model, n_dreams=5000):
    """Generate random noise inputs and record tension."""
    model.eval()

    # Random noise in [0, 1] like MNIST pixel range
    noise = torch.rand(n_dreams, 784)
    output, tension = model(noise)
    preds = output.argmax(dim=1)

    # Get directions
    out_a = model.engine_a(noise)
    out_g = model.engine_g(noise)
    direction = F.normalize(out_a - out_g, dim=-1)

    return (noise.numpy(), tension.numpy(), preds.numpy(),
            direction.numpy(), output.numpy())


# ---------------------------------------------------------------------------
# Phase 3: Lucid dreaming - gradient ascent to maximize tension
# ---------------------------------------------------------------------------

def lucid_dream(model, n_dreams=50, steps=200, lr=0.05):
    """Optimize noise inputs to MAXIMIZE tension via gradient ascent."""
    model.eval()  # Keep model frozen but allow grad on input

    # Start from random noise
    dream_input = torch.rand(n_dreams, 784, requires_grad=True)

    optimizer = torch.optim.Adam([dream_input], lr=lr)

    tension_history = []

    for step in range(steps):
        optimizer.zero_grad()

        output, tension = model(dream_input)

        # Maximize tension = minimize negative tension
        loss = -tension.mean()
        loss.backward()
        optimizer.step()

        # Clamp to valid pixel range [0, 1]
        with torch.no_grad():
            dream_input.data.clamp_(0, 1)

        if step % 20 == 0 or step == steps - 1:
            tension_history.append((step, tension.mean().item(), tension.max().item()))

    # Final evaluation
    with torch.no_grad():
        output, tension = model(dream_input)
        preds = output.argmax(dim=1)

        out_a = model.engine_a(dream_input)
        out_g = model.engine_g(dream_input)
        direction = F.normalize(out_a - out_g, dim=-1)

    return (dream_input.detach().numpy(), tension.numpy(), preds.numpy(),
            direction.numpy(), output.detach().numpy(), tension_history)


# ---------------------------------------------------------------------------
# Phase 4: Classification of dream images
# ---------------------------------------------------------------------------

def classify_dreams(model, dream_inputs_np):
    """What digit class does the model assign to each dream?"""
    model.eval()
    with torch.no_grad():
        x = torch.tensor(dream_inputs_np, dtype=torch.float32)
        output, tension = model(x)
        preds = output.argmax(dim=1)

        # Confidence via softmax
        probs = F.softmax(output, dim=1)
        confidence = probs.max(dim=1)[0]

    return preds.numpy(), confidence.numpy(), tension.numpy()


# ---------------------------------------------------------------------------
# Analysis & Reporting
# ---------------------------------------------------------------------------

def compute_digit_centroids(directions, labels):
    """Compute mean direction centroid per digit class."""
    centroids = {}
    for d in range(10):
        mask = labels == d
        if mask.sum() > 0:
            c = directions[mask].mean(axis=0)
            c = c / (np.linalg.norm(c) + 1e-8)
            centroids[d] = c
    return centroids


def cosine_similarity_to_centroids(directions, centroids):
    """For each direction vector, compute cosine sim to each digit centroid."""
    n = len(directions)
    sims = np.zeros((n, 10))
    for d in range(10):
        if d in centroids:
            sims[:, d] = directions @ centroids[d]
    return sims


def main():
    torch.manual_seed(42)
    np.random.seed(42)

    print("=" * 70)
    print("  RC-10: Dreaming = Offline Replay with PureField")
    print("  What does PureField dream about?")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Load data & train
    # ------------------------------------------------------------------
    print("\n  Loading MNIST...")
    train_ds, test_ds = load_mnist()

    model = PureFieldEngine(input_dim=784, hidden_dim=128, output_dim=10)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"  Model parameters: {n_params:,}")

    print("\n  === PHASE 0: AWAKE TRAINING ===")
    model = train_pure_field(model, train_ds, epochs=10, batch_size=256, lr=1e-3)

    # ------------------------------------------------------------------
    # Phase 1: Awake baseline
    # ------------------------------------------------------------------
    print(f"\n{'=' * 70}")
    print("  === PHASE 1: AWAKE BASELINE (Real Digits) ===")
    print(f"{'=' * 70}")

    real_tensions, real_labels, real_preds, real_directions = awake_phase(model, test_ds)
    real_acc = (real_preds == real_labels).mean() * 100

    print(f"\n  Test accuracy: {real_acc:.1f}%")
    print(f"  Real digit tension:")
    print(f"    Mean:   {real_tensions.mean():.4f}")
    print(f"    Std:    {real_tensions.std():.4f}")
    print(f"    Min:    {real_tensions.min():.4f}")
    print(f"    Max:    {real_tensions.max():.4f}")
    print(f"    Median: {np.median(real_tensions):.4f}")

    # Per-digit tension
    print(f"\n  --- Per-Digit Tension (Real) ---")
    print(f"  {'Digit':>5s}  {'N':>5s}  {'T_mean':>8s}  {'T_std':>8s}  {'T_min':>8s}  {'T_max':>8s}")
    for d in range(10):
        mask = real_labels == d
        t = real_tensions[mask]
        print(f"  {d:5d}  {mask.sum():5d}  {t.mean():8.4f}  {t.std():8.4f}  {t.min():8.4f}  {t.max():8.4f}")

    real_centroids = compute_digit_centroids(real_directions, real_labels)

    ascii_histogram(real_tensions, title="Real Digit Tension Distribution", bins=25, width=45)

    # ------------------------------------------------------------------
    # Phase 2: Dream phase (random noise)
    # ------------------------------------------------------------------
    print(f"\n{'=' * 70}")
    print("  === PHASE 2: DREAM PHASE (Random Noise) ===")
    print(f"{'=' * 70}")

    n_dreams = 5000
    noise_inputs, noise_tensions, noise_preds, noise_directions, noise_outputs = \
        dream_phase(model, n_dreams=n_dreams)

    print(f"\n  {n_dreams} random noise inputs through PureField:")
    print(f"  Dream tension:")
    print(f"    Mean:   {noise_tensions.mean():.4f}")
    print(f"    Std:    {noise_tensions.std():.4f}")
    print(f"    Min:    {noise_tensions.min():.4f}")
    print(f"    Max:    {noise_tensions.max():.4f}")
    print(f"    Median: {np.median(noise_tensions):.4f}")

    ascii_histogram(noise_tensions, title="Dream (Noise) Tension Distribution", bins=25, width=45)

    # Vivid dreams (top tension)
    vivid_idx = np.argsort(noise_tensions)[-10:][::-1]
    dreamless_idx = np.argsort(noise_tensions)[:10]

    print(f"\n  --- Top 10 VIVID DREAMS (highest tension) ---")
    print(f"  {'Rank':>4s}  {'Tension':>10s}  {'Predicted':>10s}")
    for rank, idx in enumerate(vivid_idx):
        print(f"  {rank+1:4d}  {noise_tensions[idx]:10.4f}  {noise_preds[idx]:10d}")

    print(f"\n  --- Top 10 DREAMLESS SLEEP (lowest tension) ---")
    print(f"  {'Rank':>4s}  {'Tension':>10s}  {'Predicted':>10s}")
    for rank, idx in enumerate(dreamless_idx):
        print(f"  {rank+1:4d}  {noise_tensions[idx]:10.4f}  {noise_preds[idx]:10d}")

    # What digits do dreams look like?
    dream_class_counts = Counter(noise_preds.tolist())
    print(f"\n  --- Dream Digit Distribution (noise classified as) ---")
    print(f"  {'Digit':>5s}  {'Count':>6s}  {'Pct':>6s}  Bar")
    max_count = max(dream_class_counts.values())
    for d in range(10):
        count = dream_class_counts.get(d, 0)
        pct = count / n_dreams * 100
        bar = '#' * int(count / max_count * 40)
        print(f"  {d:5d}  {count:6d}  {pct:5.1f}%  {bar}")

    # Dream direction similarity to real centroids
    dream_sims = cosine_similarity_to_centroids(noise_directions, real_centroids)
    print(f"\n  --- Dream Direction Similarity to Real Digit Centroids ---")
    print(f"  (Mean cosine similarity of all dreams to each digit centroid)")
    print(f"  {'Digit':>5s}  {'Mean Sim':>10s}  {'Std':>8s}")
    for d in range(10):
        print(f"  {d:5d}  {dream_sims[:, d].mean():10.4f}  {dream_sims[:, d].std():8.4f}")

    # Show a few vivid dream images
    print(f"\n  --- Most Vivid Dream (ASCII) ---")
    ascii_digit_grid(noise_inputs[vivid_idx[0]], title=f"Vivid Dream #1: predicted={noise_preds[vivid_idx[0]]}, tension={noise_tensions[vivid_idx[0]]:.4f}")

    print(f"\n  --- Most Dreamless (ASCII) ---")
    ascii_digit_grid(noise_inputs[dreamless_idx[0]], title=f"Dreamless #1: predicted={noise_preds[dreamless_idx[0]]}, tension={noise_tensions[dreamless_idx[0]]:.4f}")

    # ------------------------------------------------------------------
    # Phase 3: Lucid dreaming (gradient ascent)
    # ------------------------------------------------------------------
    print(f"\n{'=' * 70}")
    print("  === PHASE 3: LUCID DREAMING (Gradient Ascent on Tension) ===")
    print(f"{'=' * 70}")

    n_lucid = 50
    lucid_steps = 200
    print(f"\n  Optimizing {n_lucid} inputs to MAXIMIZE tension ({lucid_steps} steps)...")

    lucid_inputs, lucid_tensions, lucid_preds, lucid_directions, \
        lucid_outputs, lucid_history = lucid_dream(
            model, n_dreams=n_lucid, steps=lucid_steps, lr=0.05)

    print(f"\n  --- Lucid Dream Optimization Convergence ---")
    print(f"  {'Step':>6s}  {'Mean Tension':>14s}  {'Max Tension':>14s}")
    for step, mean_t, max_t in lucid_history:
        print(f"  {step:6d}  {mean_t:14.4f}  {max_t:14.4f}")

    # ASCII convergence graph
    steps_arr = [h[0] for h in lucid_history]
    means_arr = [h[1] for h in lucid_history]
    if len(means_arr) > 1:
        max_mean = max(means_arr)
        min_mean = min(means_arr)
        rng = max_mean - min_mean + 1e-8
        print(f"\n  Tension Convergence (mean):")
        for step, mean_t, _ in lucid_history:
            bar_len = int((mean_t - min_mean) / rng * 50)
            print(f"  step {step:4d} |{'#' * bar_len} {mean_t:.4f}")

    print(f"\n  Lucid dream tension stats:")
    print(f"    Mean:   {lucid_tensions.mean():.4f}")
    print(f"    Std:    {lucid_tensions.std():.4f}")
    print(f"    Min:    {lucid_tensions.min():.4f}")
    print(f"    Max:    {lucid_tensions.max():.4f}")
    print(f"    Median: {np.median(lucid_tensions):.4f}")

    ascii_histogram(lucid_tensions, title="Lucid Dream Tension Distribution", bins=15, width=45)

    # What digits do lucid dreams look like?
    lucid_class_counts = Counter(lucid_preds.tolist())
    print(f"\n  --- Lucid Dream Digit Distribution ---")
    print(f"  {'Digit':>5s}  {'Count':>6s}  {'Pct':>6s}")
    for d in range(10):
        count = lucid_class_counts.get(d, 0)
        pct = count / n_lucid * 100
        print(f"  {d:5d}  {count:6d}  {pct:5.1f}%")

    # Lucid dream direction similarity to real centroids
    lucid_sims = cosine_similarity_to_centroids(lucid_directions, real_centroids)
    print(f"\n  --- Lucid Dream Direction Similarity to Real Centroids ---")
    print(f"  {'Digit':>5s}  {'Mean Sim':>10s}  {'Max Sim':>10s}")
    for d in range(10):
        print(f"  {d:5d}  {lucid_sims[:, d].mean():10.4f}  {lucid_sims[:, d].max():10.4f}")

    # Show top lucid dream images
    top_lucid_idx = np.argsort(lucid_tensions)[-3:][::-1]
    for rank, idx in enumerate(top_lucid_idx):
        ascii_digit_grid(
            lucid_inputs[idx],
            title=f"Lucid Dream #{rank+1}: predicted={lucid_preds[idx]}, tension={lucid_tensions[idx]:.4f}")

    # ------------------------------------------------------------------
    # Phase 4: Do dreams look like real digits? (structural analysis)
    # ------------------------------------------------------------------
    print(f"\n{'=' * 70}")
    print("  === PHASE 4: DO DREAMS LOOK LIKE REAL DIGITS? ===")
    print(f"{'=' * 70}")

    # Pixel statistics comparison
    # Load a batch of real images for comparison
    test_loader = torch.utils.data.DataLoader(test_ds, batch_size=1000, shuffle=False)
    real_batch, _ = next(iter(test_loader))
    real_pixels = real_batch.numpy()

    print(f"\n  --- Pixel Statistics Comparison ---")
    print(f"  {'Source':>20s}  {'Mean':>8s}  {'Std':>8s}  {'Sparsity':>10s}  {'Entropy':>8s}")

    def pixel_stats(pixels, name):
        mean = pixels.mean()
        std = pixels.std()
        sparsity = (pixels < 0.1).mean()  # fraction near-zero
        # Approximate entropy via histogram
        hist, _ = np.histogram(pixels.flatten(), bins=50, range=(0, 1))
        hist = hist / hist.sum() + 1e-10
        entropy = -(hist * np.log2(hist)).sum()
        print(f"  {name:>20s}  {mean:8.4f}  {std:8.4f}  {sparsity:10.4f}  {entropy:8.4f}")
        return mean, std, sparsity, entropy

    pixel_stats(real_pixels, "Real digits")
    pixel_stats(noise_inputs, "Random noise")
    pixel_stats(lucid_inputs, "Lucid dreams")

    # Sparsity pattern: real digits have high sparsity (black background)
    # If lucid dreams develop sparsity -> they're learning digit-like structure

    # Spatial structure: center vs edge activation
    def spatial_analysis(pixels, name):
        """Check if activation is spatially structured (center vs edge)."""
        pixels_2d = pixels.reshape(-1, 28, 28)
        center = pixels_2d[:, 8:20, 8:20].mean()
        edge = (pixels_2d.mean() * 784 - center * 144) / (784 - 144)
        ratio = center / (edge + 1e-8)
        print(f"  {name:>20s}  center={center:.4f}  edge={edge:.4f}  center/edge={ratio:.2f}")
        return ratio

    print(f"\n  --- Spatial Structure (center vs edge activation) ---")
    print(f"  {'Source':>20s}  {'Center':>10s}  {'Edge':>10s}  {'Ratio':>12s}")
    real_ratio = spatial_analysis(real_pixels, "Real digits")
    noise_ratio = spatial_analysis(noise_inputs, "Random noise")
    lucid_ratio = spatial_analysis(lucid_inputs, "Lucid dreams")

    # ------------------------------------------------------------------
    # Phase 5: Grand Comparison
    # ------------------------------------------------------------------
    print(f"\n{'=' * 70}")
    print("  === PHASE 5: GRAND COMPARISON ===")
    print(f"{'=' * 70}")

    print(f"\n  --- Tension Comparison Table ---")
    print(f"  {'Source':>20s}  {'N':>6s}  {'T_mean':>10s}  {'T_std':>10s}  {'T_median':>10s}  {'T_min':>10s}  {'T_max':>10s}")
    print(f"  {'-'*20}  {'-'*6}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}")

    sources = [
        ("Real digits", real_tensions),
        ("Random noise", noise_tensions),
        ("Lucid dreams", lucid_tensions),
    ]
    for name, t in sources:
        print(f"  {name:>20s}  {len(t):6d}  {t.mean():10.4f}  {t.std():10.4f}  {np.median(t):10.4f}  {t.min():10.4f}  {t.max():10.4f}")

    # Ratios
    print(f"\n  --- Tension Ratios ---")
    print(f"  Noise / Real:       {noise_tensions.mean() / real_tensions.mean():.4f}x")
    print(f"  Lucid / Real:       {lucid_tensions.mean() / real_tensions.mean():.4f}x")
    print(f"  Lucid / Noise:      {lucid_tensions.mean() / noise_tensions.mean():.4f}x")

    # Overlap analysis: what fraction of dreams have tension in real digit range?
    real_p5, real_p95 = np.percentile(real_tensions, [5, 95])
    noise_in_range = ((noise_tensions >= real_p5) & (noise_tensions <= real_p95)).mean()
    lucid_in_range = ((lucid_tensions >= real_p5) & (lucid_tensions <= real_p95)).mean()
    print(f"\n  Real digit tension range (5th-95th): [{real_p5:.4f}, {real_p95:.4f}]")
    print(f"  Fraction of noise in real range:     {noise_in_range:.4f} ({noise_in_range*100:.1f}%)")
    print(f"  Fraction of lucid in real range:     {lucid_in_range:.4f} ({lucid_in_range*100:.1f}%)")

    # Combined histogram (overlaid concept)
    print(f"\n  --- Overlaid Tension Distribution (all three) ---")
    all_vals = np.concatenate([real_tensions, noise_tensions, lucid_tensions])
    lo, hi = all_vals.min(), all_vals.max()
    n_bins = 30
    edges = np.linspace(lo, hi, n_bins + 1)

    hist_real, _ = np.histogram(real_tensions, bins=edges)
    hist_noise, _ = np.histogram(noise_tensions, bins=edges)
    hist_lucid, _ = np.histogram(lucid_tensions, bins=edges)

    # Normalize to max across all
    max_all = max(hist_real.max(), hist_noise.max(), hist_lucid.max(), 1)
    bar_width = 35

    print(f"  {'Range':>19s}  {'Real':>5s} {'Noise':>5s} {'Lucid':>5s}  Visual (R=real, N=noise, L=lucid)")
    for i in range(n_bins):
        r = hist_real[i]
        n = hist_noise[i]
        l = hist_lucid[i]
        br = int(r / max_all * bar_width)
        bn = int(n / max_all * bar_width)
        bl = int(l / max_all * bar_width)
        bar = ""
        for pos in range(bar_width):
            has_r = pos < br
            has_n = pos < bn
            has_l = pos < bl
            if has_r and has_n and has_l:
                bar += "*"
            elif has_r and has_n:
                bar += "+"
            elif has_r and has_l:
                bar += "X"
            elif has_n and has_l:
                bar += "="
            elif has_r:
                bar += "R"
            elif has_n:
                bar += "N"
            elif has_l:
                bar += "L"
            else:
                bar += " "
        print(f"  {edges[i]:8.4f}-{edges[i+1]:8.4f}  {r:5d} {n:5d} {l:5d}  |{bar}|")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print(f"\n{'=' * 70}")
    print("  RC-10 SUMMARY: DREAMING = OFFLINE REPLAY WITH PUREFIELD")
    print(f"{'=' * 70}")

    print(f"\n  1. AWAKE BASELINE:")
    print(f"     Test accuracy:      {real_acc:.1f}%")
    print(f"     Real tension mean:  {real_tensions.mean():.4f}")

    print(f"\n  2. DREAM PHASE (random noise):")
    print(f"     Noise tension mean: {noise_tensions.mean():.4f}")
    print(f"     Noise/Real ratio:   {noise_tensions.mean() / real_tensions.mean():.4f}x")
    top_dream_digit = dream_class_counts.most_common(1)[0]
    print(f"     Most dreamed digit: {top_dream_digit[0]} ({top_dream_digit[1]}/{n_dreams} = {top_dream_digit[1]/n_dreams*100:.1f}%)")

    print(f"\n  3. LUCID DREAMING (gradient ascent):")
    print(f"     Lucid tension mean: {lucid_tensions.mean():.4f}")
    print(f"     Lucid/Real ratio:   {lucid_tensions.mean() / real_tensions.mean():.4f}x")
    print(f"     Lucid/Noise ratio:  {lucid_tensions.mean() / noise_tensions.mean():.4f}x")
    top_lucid_digit = lucid_class_counts.most_common(1)[0]
    print(f"     Most lucid digit:   {top_lucid_digit[0]} ({top_lucid_digit[1]}/{n_lucid} = {top_lucid_digit[1]/n_lucid*100:.1f}%)")
    initial_t = lucid_history[0][1]
    final_t = lucid_history[-1][1]
    print(f"     Tension amplification: {initial_t:.4f} -> {final_t:.4f} ({final_t/initial_t:.1f}x)")

    print(f"\n  4. DREAM STRUCTURE:")
    print(f"     Real center/edge:   {real_ratio:.2f}")
    print(f"     Noise center/edge:  {noise_ratio:.2f}")
    print(f"     Lucid center/edge:  {lucid_ratio:.2f}")
    if lucid_ratio > noise_ratio * 1.1:
        print(f"     -> Lucid dreams develop spatial structure (more center-heavy)")
    else:
        print(f"     -> Lucid dreams remain spatially uniform (no digit-like structure)")

    print(f"\n  5. KEY FINDINGS:")
    if noise_tensions.mean() > real_tensions.mean():
        print(f"     - NOISE creates MORE tension than real digits")
        print(f"       -> The engine is 'calmer' on familiar data (tension = uncertainty?)")
    elif noise_tensions.mean() < real_tensions.mean():
        print(f"     - Real digits create MORE tension than noise")
        print(f"       -> The engine is 'excited' by meaningful data (tension = engagement?)")
    else:
        print(f"     - Similar tension for noise and real digits")

    if lucid_tensions.mean() > max(noise_tensions.mean(), real_tensions.mean()):
        print(f"     - Lucid dreams have HIGHEST tension of all")
        print(f"       -> Gradient ascent found super-stimuli that excite the engine")
        print(f"       -> 'Lucid dreaming' = engine pushed to maximum disagreement")
    elif lucid_tensions.mean() > noise_tensions.mean():
        print(f"     - Lucid dreams have more tension than noise but less than real")
        print(f"       -> Engine can be pushed toward more exciting inputs")

    # Dream digit entropy (uniformity)
    dream_probs = np.array([dream_class_counts.get(d, 0) for d in range(10)]) / n_dreams
    dream_entropy = -(dream_probs * np.log2(dream_probs + 1e-10)).sum()
    max_entropy = np.log2(10)
    print(f"\n     Dream digit entropy: {dream_entropy:.3f} / {max_entropy:.3f} (max)")
    if dream_entropy > max_entropy * 0.9:
        print(f"     -> Dreams are uniformly distributed (no preferred digit)")
    else:
        print(f"     -> Dreams are biased toward certain digits (non-uniform)")

    print(f"\n{'=' * 70}")
    print(f"  RC-10 COMPLETE")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
