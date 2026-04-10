#!/usr/bin/env python3
"""RC-8: Emotion = Tension Direction Mapping

Key question: Does the tension direction (normalize(A-G)) encode "what" or "how"?

Setup:
  1. Train PureFieldEngine on MNIST (10 epochs)
  2. For each test sample, extract tension direction = normalize(A-G) in R^10
  3. Map directions to 2D via PCA -> "emotion space"
  4. Analyze clustering by: (a) digit class, (b) correct/wrong, (c) tension magnitude
  5. If direction clusters by class -> direction encodes "what" (concept identity)
     If direction clusters by correct/wrong -> direction encodes "how" (emotion/confidence)

Metrics:
  - PCA explained variance ratio
  - Silhouette scores (class vs correct/wrong)
  - Cluster separation: confident-correct vs overconfident-wrong
  - Per-class direction centroids and angular distances
"""

import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torchvision import datasets, transforms
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from collections import defaultdict

from model_pure_field import PureFieldEngine


# ---------------------------------------------------------------------------
# ASCII visualization helpers
# ---------------------------------------------------------------------------

def ascii_scatter_2d(xs, ys, labels, title="", width=70, height=30):
    """ASCII scatter plot colored by label."""
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")

    xs, ys = np.array(xs), np.array(ys)
    unique_labels = sorted(set(labels))

    # Symbol map
    if len(unique_labels) <= 10:
        symbols = '0123456789'
    elif len(unique_labels) == 2:
        symbols = '.X'
    else:
        symbols = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

    label_to_sym = {l: symbols[i % len(symbols)] for i, l in enumerate(unique_labels)}

    x_min, x_max = xs.min(), xs.max()
    y_min, y_max = ys.min(), ys.max()
    x_range = x_max - x_min + 1e-8
    y_range = y_max - y_min + 1e-8

    grid = [[' ' for _ in range(width)] for _ in range(height)]

    for x, y, l in zip(xs, ys, labels):
        col = int((x - x_min) / x_range * (width - 1))
        row = int((1 - (y - y_min) / y_range) * (height - 1))
        col = max(0, min(width - 1, col))
        row = max(0, min(height - 1, row))
        grid[row][col] = label_to_sym[l]

    for row in grid:
        print('  |' + ''.join(row) + '|')

    # Legend
    legend_parts = [f"  {label_to_sym[l]}={l}" for l in unique_labels]
    print(f"  Legend: {' '.join(legend_parts)}")
    print()


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
        print(f"  {lo:7.3f}-{hi:7.3f} | {'#' * bar_len} ({count})")


# ---------------------------------------------------------------------------
# Training
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
# Extract tension directions
# ---------------------------------------------------------------------------

@torch.no_grad()
def extract_directions(model, test_ds, max_samples=10000):
    """Extract tension direction, magnitude, predictions for all test samples."""
    model.eval()
    loader = torch.utils.data.DataLoader(test_ds, batch_size=512, shuffle=False)

    all_directions = []
    all_tensions = []
    all_preds = []
    all_labels = []
    all_logits = []
    all_raw_repulsion = []

    for x, y in loader:
        out_a = model.engine_a(x)
        out_g = model.engine_g(x)

        repulsion = out_a - out_g
        tension = (repulsion ** 2).mean(dim=-1)
        direction = F.normalize(repulsion, dim=-1)

        output = model.tension_scale * torch.sqrt(tension.unsqueeze(-1) + 1e-8) * direction
        preds = output.argmax(dim=1)

        all_directions.append(direction.numpy())
        all_tensions.append(tension.numpy())
        all_preds.append(preds.numpy())
        all_labels.append(y.numpy())
        all_logits.append(output.numpy())
        all_raw_repulsion.append(repulsion.numpy())

        if sum(len(a) for a in all_labels) >= max_samples:
            break

    directions = np.concatenate(all_directions)[:max_samples]
    tensions = np.concatenate(all_tensions)[:max_samples]
    preds = np.concatenate(all_preds)[:max_samples]
    labels = np.concatenate(all_labels)[:max_samples]
    logits = np.concatenate(all_logits)[:max_samples]
    raw_repulsion = np.concatenate(all_raw_repulsion)[:max_samples]

    return directions, tensions, preds, labels, logits, raw_repulsion


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyze_pca(directions, tensions, preds, labels, logits):
    """PCA on direction space + cluster analysis."""
    n = len(directions)
    correct = (preds == labels).astype(int)
    acc = correct.mean() * 100

    print(f"\n{'=' * 70}")
    print(f"  RC-8: Emotion = Tension Direction Mapping")
    print(f"{'=' * 70}")
    print(f"  Test samples: {n}")
    print(f"  Test accuracy: {acc:.1f}%")
    print(f"  Correct: {correct.sum()}, Wrong: {n - correct.sum()}")

    # -----------------------------------------------------------------------
    # PCA on direction vectors
    # -----------------------------------------------------------------------
    pca = PCA(n_components=min(10, directions.shape[1]))
    dirs_pca_full = pca.fit_transform(directions)
    dirs_2d = dirs_pca_full[:, :2]

    print(f"\n  --- PCA Explained Variance ---")
    print(f"  {'PC':>4s}  {'Var Ratio':>10s}  {'Cumulative':>10s}")
    cum = 0
    for i, v in enumerate(pca.explained_variance_ratio_):
        cum += v
        bar = '#' * int(v * 50)
        print(f"  PC{i + 1:2d}  {v:10.4f}  {cum:10.4f}  {bar}")

    print(f"\n  Top-2 PCA captures {pca.explained_variance_ratio_[:2].sum() * 100:.1f}% of direction variance")

    # -----------------------------------------------------------------------
    # Silhouette scores: class vs correct/wrong
    # -----------------------------------------------------------------------
    print(f"\n  --- Silhouette Score Comparison ---")

    # Subsample for speed if needed
    if n > 5000:
        idx = np.random.RandomState(42).choice(n, 5000, replace=False)
    else:
        idx = np.arange(n)

    sil_class = silhouette_score(dirs_2d[idx], labels[idx], sample_size=min(2000, len(idx)))
    print(f"  By digit class (0-9):     {sil_class:.4f}")

    # Only compute correct/wrong silhouette if both groups exist
    if correct[idx].sum() > 0 and (1 - correct[idx]).sum() > 0:
        sil_cw = silhouette_score(dirs_2d[idx], correct[idx], sample_size=min(2000, len(idx)))
        print(f"  By correct/wrong:         {sil_cw:.4f}")
    else:
        sil_cw = 0.0
        print(f"  By correct/wrong:         N/A (all same class)")

    # -----------------------------------------------------------------------
    # Key metric: which clustering is stronger?
    # -----------------------------------------------------------------------
    print(f"\n  --- Key Finding ---")
    if sil_class > sil_cw:
        ratio = sil_class / max(abs(sil_cw), 1e-6)
        print(f"  Direction clusters MORE by CLASS than by correct/wrong")
        print(f"  Ratio (class/correct_wrong) = {ratio:.2f}x")
        print(f"  => Direction encodes 'WHAT' (concept identity), not 'HOW' (emotion)")
    elif sil_cw > sil_class:
        ratio = sil_cw / max(abs(sil_class), 1e-6)
        print(f"  Direction clusters MORE by CORRECT/WRONG than by class")
        print(f"  Ratio (correct_wrong/class) = {ratio:.2f}x")
        print(f"  => Direction encodes 'HOW' (emotion/confidence), not 'WHAT'")
    else:
        print(f"  Direction clusters equally by both -- mixed encoding")

    # -----------------------------------------------------------------------
    # ASCII scatter: by digit class
    # -----------------------------------------------------------------------
    # Subsample for ASCII
    plot_n = min(2000, n)
    plot_idx = np.random.RandomState(42).choice(n, plot_n, replace=False)

    ascii_scatter_2d(
        dirs_2d[plot_idx, 0], dirs_2d[plot_idx, 1],
        labels[plot_idx].tolist(),
        title="Emotion Space: colored by DIGIT CLASS",
        width=70, height=30,
    )

    # ASCII scatter: by correct/wrong
    cw_labels = ['correct' if c else 'WRONG' for c in correct[plot_idx]]
    ascii_scatter_2d(
        dirs_2d[plot_idx, 0], dirs_2d[plot_idx, 1],
        cw_labels,
        title="Emotion Space: colored by CORRECT (.) vs WRONG (X)",
        width=70, height=30,
    )

    # -----------------------------------------------------------------------
    # Tension magnitude analysis: correct vs wrong
    # -----------------------------------------------------------------------
    t_correct = tensions[correct == 1]
    t_wrong = tensions[correct == 0]

    print(f"\n  --- Tension Magnitude by Correctness ---")
    print(f"  {'Group':>20s}  {'N':>6s}  {'Mean':>8s}  {'Std':>8s}  {'Median':>8s}")
    print(f"  {'Correct':>20s}  {len(t_correct):6d}  {t_correct.mean():8.4f}  {t_correct.std():8.4f}  {np.median(t_correct):8.4f}")
    if len(t_wrong) > 0:
        print(f"  {'Wrong':>20s}  {len(t_wrong):6d}  {t_wrong.mean():8.4f}  {t_wrong.std():8.4f}  {np.median(t_wrong):8.4f}")
        ratio = t_wrong.mean() / max(t_correct.mean(), 1e-8)
        print(f"  Wrong/Correct tension ratio: {ratio:.3f}")
    else:
        print(f"  {'Wrong':>20s}  {0:6d}  N/A")

    ascii_histogram(t_correct, title="Tension: CORRECT predictions", bins=20, width=40)
    if len(t_wrong) > 0:
        ascii_histogram(t_wrong, title="Tension: WRONG predictions", bins=20, width=40)

    # -----------------------------------------------------------------------
    # Confident-correct vs overconfident-wrong analysis
    # -----------------------------------------------------------------------
    print(f"\n  --- Confident-Correct vs Overconfident-Wrong ---")

    # Confidence = softmax max probability
    probs = np.exp(logits - logits.max(axis=1, keepdims=True))
    probs = probs / probs.sum(axis=1, keepdims=True)
    confidence = probs.max(axis=1)

    # High confidence threshold = top quartile
    conf_threshold = np.percentile(confidence, 75)
    print(f"  Confidence threshold (75th percentile): {conf_threshold:.4f}")

    confident_correct_mask = (correct == 1) & (confidence >= conf_threshold)
    overconfident_wrong_mask = (correct == 0) & (confidence >= conf_threshold)

    n_cc = confident_correct_mask.sum()
    n_ow = overconfident_wrong_mask.sum()
    print(f"  Confident-correct:      {n_cc}")
    print(f"  Overconfident-wrong:    {n_ow}")

    if n_cc > 10 and n_ow > 5:
        # Direction centroid comparison
        cc_center = dirs_2d[confident_correct_mask].mean(axis=0)
        ow_center = dirs_2d[overconfident_wrong_mask].mean(axis=0)
        separation = np.linalg.norm(cc_center - ow_center)

        # Spread of each group
        cc_spread = np.std(np.linalg.norm(dirs_2d[confident_correct_mask] - cc_center, axis=1))
        ow_spread = np.std(np.linalg.norm(dirs_2d[overconfident_wrong_mask] - ow_center, axis=1))

        sep_ratio = separation / max(cc_spread + ow_spread, 1e-8)
        print(f"\n  Centroid separation (2D):  {separation:.4f}")
        print(f"  CC spread (std):          {cc_spread:.4f}")
        print(f"  OW spread (std):          {ow_spread:.4f}")
        print(f"  Separation ratio:         {sep_ratio:.4f}")
        print(f"  (ratio > 1 = clearly separable clusters)")

        # Tension comparison
        t_cc = tensions[confident_correct_mask]
        t_ow = tensions[overconfident_wrong_mask]
        print(f"\n  Tension:  CC mean={t_cc.mean():.4f}  OW mean={t_ow.mean():.4f}")
        if t_cc.mean() > 0:
            print(f"  OW/CC tension ratio: {t_ow.mean() / t_cc.mean():.3f}")
    else:
        print(f"  Insufficient overconfident-wrong samples for analysis")

    # -----------------------------------------------------------------------
    # Per-class direction centroids and angular distances
    # -----------------------------------------------------------------------
    print(f"\n  --- Per-Class Direction Centroids (10D) ---")
    centroids = {}
    for d in range(10):
        mask = labels == d
        if mask.sum() > 0:
            c = directions[mask].mean(axis=0)
            c_norm = c / (np.linalg.norm(c) + 1e-8)
            centroids[d] = c_norm

    # Angular distance matrix (cosine similarity)
    print(f"\n  Cosine Similarity Matrix (direction centroids):")
    header = "     " + "".join(f"  {d:5d}" for d in range(10))
    print(header)
    cos_sim_matrix = np.zeros((10, 10))
    for i in range(10):
        row = f"  {i:2d} "
        for j in range(10):
            if i in centroids and j in centroids:
                sim = np.dot(centroids[i], centroids[j])
                cos_sim_matrix[i, j] = sim
                row += f" {sim:5.2f} "
            else:
                row += "   N/A "
        print(row)

    # Average within-class vs between-class similarity
    within_sims = []
    between_sims = []
    for i in range(10):
        for j in range(i + 1, 10):
            between_sims.append(cos_sim_matrix[i, j])
    for d in range(10):
        mask = labels == d
        if mask.sum() > 1:
            d_dirs = directions[mask]
            # Pairwise cosine similarities (sample)
            sample_n = min(200, len(d_dirs))
            sample_idx = np.random.RandomState(d).choice(len(d_dirs), sample_n, replace=False)
            d_sample = d_dirs[sample_idx]
            norms = np.linalg.norm(d_sample, axis=1, keepdims=True) + 1e-8
            d_normed = d_sample / norms
            sim_matrix = d_normed @ d_normed.T
            # Upper triangle
            triu_idx = np.triu_indices(sample_n, k=1)
            within_sims.extend(sim_matrix[triu_idx].tolist())

    within_mean = np.mean(within_sims) if within_sims else 0
    between_mean = np.mean(between_sims) if between_sims else 0

    print(f"\n  Within-class mean cosine sim:  {within_mean:.4f}")
    print(f"  Between-class mean cosine sim: {between_mean:.4f}")
    print(f"  Separation (within - between): {within_mean - between_mean:.4f}")
    if within_mean > between_mean + 0.05:
        print(f"  => Directions cluster BY CLASS -> encodes 'WHAT'")
    elif within_mean < between_mean - 0.05:
        print(f"  => Directions DO NOT cluster by class")
    else:
        print(f"  => Weak or no class-based clustering in direction space")

    # -----------------------------------------------------------------------
    # Per-class accuracy and tension
    # -----------------------------------------------------------------------
    print(f"\n  --- Per-Class Accuracy and Tension ---")
    print(f"  {'Digit':>5s}  {'N':>5s}  {'Acc%':>6s}  {'T_mean':>8s}  {'T_std':>8s}  {'T_correct':>10s}  {'T_wrong':>10s}")
    for d in range(10):
        mask = labels == d
        nd = mask.sum()
        if nd == 0:
            continue
        acc_d = correct[mask].mean() * 100
        t_mean = tensions[mask].mean()
        t_std = tensions[mask].std()
        tc = tensions[mask & (correct == 1)]
        tw = tensions[mask & (correct == 0)]
        tc_str = f"{tc.mean():.4f}" if len(tc) > 0 else "N/A"
        tw_str = f"{tw.mean():.4f}" if len(tw) > 0 else "N/A"
        print(f"  {d:5d}  {nd:5d}  {acc_d:6.1f}  {t_mean:8.4f}  {t_std:8.4f}  {tc_str:>10s}  {tw_str:>10s}")

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print(f"\n{'=' * 70}")
    print(f"  RC-8 SUMMARY")
    print(f"{'=' * 70}")
    print(f"  PCA top-2 variance:           {pca.explained_variance_ratio_[:2].sum() * 100:.1f}%")
    print(f"  Silhouette (class):           {sil_class:.4f}")
    print(f"  Silhouette (correct/wrong):   {sil_cw:.4f}")
    print(f"  Within-class cos sim:         {within_mean:.4f}")
    print(f"  Between-class cos sim:        {between_mean:.4f}")
    if len(t_wrong) > 0:
        print(f"  Tension ratio (wrong/correct): {t_wrong.mean() / max(t_correct.mean(), 1e-8):.3f}")
    print(f"  Test accuracy:                {acc:.1f}%")
    print()
    if sil_class > sil_cw and within_mean > between_mean:
        print(f"  CONCLUSION: Direction primarily encodes CONCEPT (what),")
        print(f"              not emotion (how). The 'emotion space' is actually")
        print(f"              a 'concept space' -- each digit has its own direction.")
    elif sil_cw > sil_class:
        print(f"  CONCLUSION: Direction primarily encodes CONFIDENCE (how),")
        print(f"              not concept (what). This IS an emotion space --")
        print(f"              the engine's 'feeling' about its answer.")
    else:
        print(f"  CONCLUSION: Direction encodes a MIX of concept and confidence.")
        print(f"              Both 'what' and 'how' are entangled in direction space.")
    print(f"{'=' * 70}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    torch.manual_seed(42)
    np.random.seed(42)

    print("=" * 70)
    print("  RC-8: Emotion = Tension Direction Mapping")
    print("  Does tension direction encode 'what' (concept) or 'how' (emotion)?")
    print("=" * 70)

    # Load data
    print("\n  Loading MNIST...")
    train_ds, test_ds = load_mnist()

    # Build and train model
    model = PureFieldEngine(input_dim=784, hidden_dim=128, output_dim=10)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"  Model parameters: {n_params:,}")
    print(f"  Architecture: PureFieldEngine (engine_A vs engine_G)")
    print(f"  Output = tension_scale * sqrt(tension) * direction")
    print(f"  tension = |A(x) - G(x)|^2")
    print(f"  direction = normalize(A(x) - G(x))")
    print()

    print("  --- Training ---")
    model = train_pure_field(model, train_ds, epochs=10, batch_size=256, lr=1e-3)

    # Extract directions
    print("\n  --- Extracting tension directions ---")
    directions, tensions, preds, labels, logits, raw_repulsion = extract_directions(model, test_ds)
    print(f"  Extracted {len(directions)} samples")
    print(f"  Direction shape: {directions.shape}")
    print(f"  Tension range: [{tensions.min():.4f}, {tensions.max():.4f}]")

    # Full analysis
    analyze_pca(directions, tensions, preds, labels, logits)


if __name__ == '__main__':
    main()
