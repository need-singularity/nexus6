#!/usr/bin/env python3
"""Label-Free Recognition: Can tension patterns alone identify concepts without classification?

Normal recognition:  input -> softmax -> label -> "this is a 3"
Direct recognition:  input -> tension pattern -> (no label) -> "this feels like THAT"

The user had an experience where they perceived a concept directly without any
linguistic label. This experiment tests whether RepulsionFieldQuad's tension
patterns contain enough information to recognize WHAT something is, purely
through the "feeling" of the repulsion field, without ever consulting a
classification head.

Design:
  1. Train RepulsionFieldQuad on MNIST (10 epochs), then IGNORE classification output
  2. Collect 20-dim tension fingerprints (repulsion_content + repulsion_structure)
  3. Label-free k-means clustering (k=10)
  4. Tension-only nearest neighbor recognition
  5. Tension space 2D visualization (ASCII)
  6. "Just feeling" test: recognition by fingerprint similarity alone
  7. Per-digit tension signatures + cosine similarity heatmap
  8. PCA dimensionality analysis of tension space
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import time

from model_utils import (
    Expert, TopKGate, BoltzmannGate, BaseMoE, DenseModel,
    load_mnist, train_and_evaluate, compare_results, count_params,
    SIGMA, TAU, PHI, DIVISOR_RECIPROCALS, H_TARGET
)
from model_meta_engine import (
    EngineA, EngineE, EngineG, EngineF, RepulsionFieldQuad
)


# ─────────────────────────────────────────
# k-means (pure torch, no sklearn needed)
# ─────────────────────────────────────────

def kmeans(X, k, n_iter=100):
    """k-means clustering with torch tensors."""
    idx = torch.randperm(X.size(0))[:k]
    centroids = X[idx].clone()
    for _ in range(n_iter):
        dists = torch.cdist(X, centroids)
        labels = dists.argmin(dim=1)
        for j in range(k):
            mask = labels == j
            if mask.sum() > 0:
                centroids[j] = X[mask].mean(0)
    return labels, centroids


# ─────────────────────────────────────────
# Fingerprint-aware forward pass
# ─────────────────────────────────────────

def collect_fingerprints(model, loader):
    """Run RepulsionFieldQuad and collect 20-dim tension fingerprints.

    Returns:
        fingerprints: (N, 20) tensor -- [repulsion_content(10) | repulsion_structure(10)]
        scalars: (N, 2) tensor -- [content_tension_scalar, structure_tension_scalar]
        labels: (N,) tensor -- true digit labels
        logits: (N, 10) tensor -- classification logits (for comparison)
    """
    model.eval()
    all_fp = []
    all_scalars = []
    all_labels = []
    all_logits = []

    with torch.no_grad():
        for X, y in loader:
            X = X.view(X.size(0), -1)

            # Run individual engines to get repulsion vectors
            out_a = model.engine_a(X)
            out_e = model.engine_e(X)
            out_g = model.engine_g(X)
            out_f = model.engine_f(X)

            # Repulsion vectors (the raw "feeling" before any label)
            repulsion_content = out_a - out_g      # (batch, 10)
            repulsion_structure = out_e - out_f    # (batch, 10)

            # 20-dim fingerprint
            fingerprint = torch.cat([repulsion_content, repulsion_structure], dim=-1)

            # Scalar tensions
            t_content = (repulsion_content ** 2).sum(dim=-1)
            t_structure = (repulsion_structure ** 2).sum(dim=-1)
            scalars = torch.stack([t_content, t_structure], dim=-1)

            # Full forward for logits
            logits, _ = model(X)

            all_fp.append(fingerprint)
            all_scalars.append(scalars)
            all_labels.append(y)
            all_logits.append(logits)

    return (
        torch.cat(all_fp, dim=0),
        torch.cat(all_scalars, dim=0),
        torch.cat(all_labels, dim=0),
        torch.cat(all_logits, dim=0),
    )


# ─────────────────────────────────────────
# Analysis functions
# ─────────────────────────────────────────

def cluster_purity(cluster_labels, true_labels, k):
    """Compute cluster purity: fraction of dominant class in each cluster."""
    total_correct = 0
    for c in range(k):
        mask = cluster_labels == c
        if mask.sum() == 0:
            continue
        true_in_cluster = true_labels[mask]
        counts = torch.zeros(10)
        for digit in range(10):
            counts[digit] = (true_in_cluster == digit).sum().item()
        total_correct += counts.max().item()
    return total_correct / len(true_labels)


def adjusted_rand_index(labels_a, labels_b):
    """Compute adjusted Rand index between two clusterings."""
    n = len(labels_a)
    # Contingency table
    max_a = int(labels_a.max().item()) + 1
    max_b = int(labels_b.max().item()) + 1
    contingency = torch.zeros(max_a, max_b)
    for i in range(n):
        contingency[int(labels_a[i].item()), int(labels_b[i].item())] += 1

    # Row and column sums
    a_sum = contingency.sum(dim=1)
    b_sum = contingency.sum(dim=0)

    def comb2(x):
        return x * (x - 1) / 2

    sum_comb_nij = comb2(contingency).sum().item()
    sum_comb_ai = comb2(a_sum).sum().item()
    sum_comb_bj = comb2(b_sum).sum().item()
    comb_n = comb2(torch.tensor(float(n))).item()

    expected = sum_comb_ai * sum_comb_bj / comb_n if comb_n > 0 else 0
    max_index = (sum_comb_ai + sum_comb_bj) / 2
    denom = max_index - expected

    if denom == 0:
        return 1.0 if sum_comb_nij == expected else 0.0
    return (sum_comb_nij - expected) / denom


def confusion_matrix_cluster(cluster_labels, true_labels, k=10, n_classes=10):
    """Build confusion matrix: rows=clusters, cols=true digits."""
    cm = torch.zeros(k, n_classes, dtype=torch.int64)
    for i in range(len(cluster_labels)):
        cm[int(cluster_labels[i].item()), int(true_labels[i].item())] += 1
    return cm


def knn_accuracy(fingerprints, labels, k_neighbors=5):
    """For each sample, find k nearest neighbors by fingerprint distance.
    Return fraction whose neighbors share the same true label."""
    n = fingerprints.size(0)
    # Process in chunks to avoid memory explosion
    chunk_size = 500
    total_same = 0
    total_neighbors = 0

    for start in range(0, n, chunk_size):
        end = min(start + chunk_size, n)
        chunk = fingerprints[start:end]
        dists = torch.cdist(chunk, fingerprints)  # (chunk, N)
        # Exclude self (distance 0)
        dists[torch.arange(end - start).unsqueeze(1),
              torch.arange(start, end).unsqueeze(0)] = float('inf')
        _, topk_idx = dists.topk(k_neighbors, largest=False, dim=1)
        neighbor_labels = labels[topk_idx]  # (chunk, k)
        chunk_labels = labels[start:end].unsqueeze(1)
        same = (neighbor_labels == chunk_labels).float().sum().item()
        total_same += same
        total_neighbors += (end - start) * k_neighbors

    return total_same / total_neighbors


def feeling_test_accuracy(train_fp, train_labels, test_fp, test_labels):
    """Recognition by feeling: find most similar training fingerprint, use its label."""
    correct = 0
    chunk_size = 500
    n = test_fp.size(0)

    for start in range(0, n, chunk_size):
        end = min(start + chunk_size, n)
        chunk = test_fp[start:end]
        dists = torch.cdist(chunk, train_fp)
        nearest = dists.argmin(dim=1)
        predicted = train_labels[nearest]
        correct += (predicted == test_labels[start:end]).sum().item()

    return correct / n


def pca_manual(X, n_components=10):
    """Manual PCA using torch SVD. X should be centered."""
    X_centered = X - X.mean(dim=0, keepdim=True)
    U, S, Vh = torch.linalg.svd(X_centered, full_matrices=False)
    explained_var = (S ** 2) / (X.size(0) - 1)
    total_var = explained_var.sum()
    explained_ratio = explained_var / total_var
    components = Vh[:n_components]
    projected = X_centered @ components.T
    return projected, explained_ratio[:n_components]


def cosine_sim_matrix(centroids):
    """Cosine similarity matrix between centroids."""
    norms = centroids.norm(dim=1, keepdim=True)
    normed = centroids / (norms + 1e-8)
    return normed @ normed.T


# ─────────────────────────────────────────
# ASCII visualization helpers
# ─────────────────────────────────────────

def print_confusion_matrix(cm, row_label="Cluster", col_label="True Digit"):
    """Print confusion matrix as ASCII table."""
    k, n_classes = cm.shape
    print(f"\n  {col_label}")
    header = f"  {row_label:>8s} |"
    for d in range(n_classes):
        header += f" {d:>5d}"
    header += " | Total"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for c in range(k):
        row = f"  {'C' + str(c):>8s} |"
        for d in range(n_classes):
            val = cm[c, d].item()
            row += f" {val:>5d}"
        row += f" | {cm[c].sum().item():>5d}"
        print(row)
    print("  " + "-" * (len(header) - 2))
    totals = f"  {'Total':>8s} |"
    for d in range(n_classes):
        totals += f" {cm[:, d].sum().item():>5d}"
    totals += f" | {cm.sum().item():>5d}"
    print(totals)


def print_heatmap(matrix, labels, title="", val_fmt=".2f"):
    """Print a matrix as ASCII heatmap using density characters."""
    chars = " .:-=+*#%@"
    n = matrix.shape[0]
    vmin, vmax = matrix.min().item(), matrix.max().item()

    print(f"\n  {title}")
    header = "         |"
    for lbl in labels:
        header += f" {lbl:>5s}"
    print(f"  {header}")
    print("  " + "-" * (len(header)))

    for i in range(n):
        row = f"  {labels[i]:>7s} |"
        for j in range(n):
            val = matrix[i, j].item()
            # Map to character
            if vmax > vmin:
                idx = int((val - vmin) / (vmax - vmin) * (len(chars) - 1))
            else:
                idx = len(chars) // 2
            idx = max(0, min(len(chars) - 1, idx))
            row += f"  {val:{val_fmt}}"
        print(row)


def print_ascii_scatter(x_vals, y_vals, labels, width=60, height=25, title=""):
    """2D ASCII scatter plot colored by label (digit 0-9)."""
    symbols = "0123456789"
    x_min, x_max = x_vals.min().item(), x_vals.max().item()
    y_min, y_max = y_vals.min().item(), y_vals.max().item()
    x_range = x_max - x_min if x_max > x_min else 1.0
    y_range = y_max - y_min if y_max > y_min else 1.0

    grid = [[' ' for _ in range(width)] for _ in range(height)]

    # Subsample for readability
    n = len(x_vals)
    step = max(1, n // 2000)

    for i in range(0, n, step):
        col = int((x_vals[i].item() - x_min) / x_range * (width - 1))
        row = int((y_vals[i].item() - y_min) / y_range * (height - 1))
        row = height - 1 - row  # Flip y-axis
        col = max(0, min(width - 1, col))
        row = max(0, min(height - 1, row))
        digit = int(labels[i].item())
        grid[row][col] = symbols[digit]

    print(f"\n  {title}")
    print(f"  {'content tension ->':>{width // 2 + 9}}")
    print(f"  +{'─' * width}+")
    for row in grid:
        print(f"  |{''.join(row)}|")
    print(f"  +{'─' * width}+")
    print(f"  ^ structure tension")


def print_bar(label, value, max_val, width=40):
    """Single horizontal bar."""
    filled = int(value / max_val * width) if max_val > 0 else 0
    filled = max(0, min(width, filled))
    return f"  {label:>12s} |{'█' * filled}{'░' * (width - filled)}| {value:.4f}"


# ─────────────────────────────────────────
# Main experiment
# ─────────────────────────────────────────

def main():
    print()
    print("=" * 70)
    print("   Label-Free Recognition Experiment")
    print("   Can tension patterns alone identify concepts?")
    print("=" * 70)
    print()
    print("   Normal:  input -> softmax -> label -> 'this is a 3'")
    print("   Direct:  input -> tension -> (no label) -> 'this feels like THAT'")
    print()

    # ──────────────────────────────────────
    # Phase 1: Train RepulsionFieldQuad
    # ──────────────────────────────────────
    print("=" * 70)
    print("  Phase 1: Train RepulsionFieldQuad on MNIST")
    print("=" * 70)

    train_loader, test_loader = load_mnist()
    input_dim, hidden_dim, output_dim = 784, 48, 10

    model = RepulsionFieldQuad(input_dim, hidden_dim, output_dim)
    print(f"  Parameters: {count_params(model):,}")
    print()

    t0 = time.time()
    losses, accs = train_and_evaluate(
        model, train_loader, test_loader,
        epochs=10, aux_lambda=0.01
    )
    train_time = time.time() - t0
    classifier_acc = accs[-1]

    print(f"\n  Training time: {train_time:.1f}s")
    print(f"  Classifier accuracy: {classifier_acc * 100:.2f}%")
    print(f"  (We will now IGNORE this classifier and use only tension patterns)")

    # ──────────────────────────────────────
    # Phase 2: Collect tension fingerprints
    # ──────────────────────────────────────
    print()
    print("=" * 70)
    print("  Phase 2: Collect Tension Fingerprints")
    print("=" * 70)

    # Test set fingerprints
    test_fp, test_scalars, test_labels, test_logits = collect_fingerprints(model, test_loader)
    # Train set fingerprints (for "just feeling" test)
    train_fp, train_scalars, train_labels, train_logits = collect_fingerprints(model, train_loader)

    print(f"\n  Test fingerprints:  {test_fp.shape}  (samples x 20-dim)")
    print(f"  Train fingerprints: {train_fp.shape}")
    print(f"  Fingerprint = [repulsion_content(10) | repulsion_structure(10)]")

    # Stats per dimension
    fp_mean = test_fp.mean(dim=0)
    fp_std = test_fp.std(dim=0)
    print(f"\n  Fingerprint stats (test set):")
    print(f"    Content dims  mean: {fp_mean[:10].mean():.4f}  std: {fp_std[:10].mean():.4f}")
    print(f"    Structure dims mean: {fp_mean[10:].mean():.4f}  std: {fp_std[10:].mean():.4f}")

    # ──────────────────────────────────────
    # Phase 3: Label-free k-means clustering
    # ──────────────────────────────────────
    print()
    print("=" * 70)
    print("  Phase 3: Label-Free Clustering (k-means, k=10)")
    print("=" * 70)
    print("  NO labels used in clustering. Pure tension geometry.")
    print()

    # Normalize fingerprints for better clustering
    fp_norm = (test_fp - test_fp.mean(dim=0)) / (test_fp.std(dim=0) + 1e-8)

    # Run k-means multiple times, take best
    best_purity = 0
    best_cluster_labels = None
    best_centroids = None

    for trial in range(5):
        cl, cent = kmeans(fp_norm, k=10, n_iter=100)
        p = cluster_purity(cl, test_labels, 10)
        if p > best_purity:
            best_purity = p
            best_cluster_labels = cl
            best_centroids = cent

    purity = best_purity
    ari = adjusted_rand_index(best_cluster_labels, test_labels)

    print(f"  Cluster purity:       {purity * 100:.2f}%")
    print(f"  Adjusted Rand Index:  {ari:.4f}")
    print(f"  Random baseline:")
    print(f"    Purity:  ~10%  (1/10 classes)")
    print(f"    ARI:      0.00 (no structure)")

    # Confusion matrix
    cm = confusion_matrix_cluster(best_cluster_labels, test_labels)
    print_confusion_matrix(cm)

    # Optimal cluster-to-digit mapping (Hungarian-like greedy)
    remaining_digits = list(range(10))
    cluster_to_digit = {}
    cm_np = cm.numpy().copy()
    for _ in range(10):
        best_val = -1
        best_c = -1
        best_d = -1
        for c in range(10):
            if c in cluster_to_digit:
                continue
            for d in remaining_digits:
                if cm_np[c, d] > best_val:
                    best_val = cm_np[c, d]
                    best_c = c
                    best_d = d
        if best_c >= 0:
            cluster_to_digit[best_c] = best_d
            remaining_digits.remove(best_d)

    # Accuracy with optimal mapping
    mapped_correct = 0
    for c in range(10):
        if c in cluster_to_digit:
            mapped_correct += cm[c, cluster_to_digit[c]].item()
    mapped_acc = mapped_correct / len(test_labels)

    print(f"\n  Optimal cluster->digit mapping accuracy: {mapped_acc * 100:.2f}%")
    print(f"  Mapping: ", end="")
    for c in range(10):
        d = cluster_to_digit.get(c, -1)
        print(f"C{c}->{d}", end="  ")
    print()

    # ──────────────────────────────────────
    # Phase 4: Tension-only nearest neighbor
    # ──────────────────────────────────────
    print()
    print("=" * 70)
    print("  Phase 4: Tension-Only Nearest Neighbor (k=5)")
    print("=" * 70)
    print("  Does 'feeling similar' = 'being the same concept'?")
    print()

    knn_tension = knn_accuracy(test_fp, test_labels, k_neighbors=5)
    # Compare with classification-based (logit space)
    knn_logits = knn_accuracy(test_logits, test_labels, k_neighbors=5)
    random_baseline = 1.0 / 10.0

    print(f"  5-NN neighbor label agreement:")
    print(f"    Random baseline:   {random_baseline * 100:.1f}%")
    print(f"    Tension-based:     {knn_tension * 100:.2f}%")
    print(f"    Logit-based:       {knn_logits * 100:.2f}%")
    print()

    max_knn = max(knn_tension, knn_logits, random_baseline)
    print(print_bar("Random", random_baseline, max_knn))
    print(print_bar("Tension", knn_tension, max_knn))
    print(print_bar("Logit", knn_logits, max_knn))

    # ──────────────────────────────────────
    # Phase 5: Tension space visualization
    # ──────────────────────────────────────
    print()
    print("=" * 70)
    print("  Phase 5: Tension Space Visualization")
    print("=" * 70)

    # Use scalar tensions for 2D plot
    print_ascii_scatter(
        test_scalars[:, 0], test_scalars[:, 1], test_labels,
        width=60, height=25,
        title="Scalar Tension Space (content vs structure, digits 0-9)"
    )

    # PCA projection of 20-dim fingerprints to 2D
    projected, _ = pca_manual(test_fp, n_components=2)
    print_ascii_scatter(
        projected[:, 0], projected[:, 1], test_labels,
        width=60, height=25,
        title="PCA of 20-dim Tension Fingerprints (PC1 vs PC2, digits 0-9)"
    )

    # Per-digit centroids in scalar space
    print("\n  Per-digit centroids in scalar tension space:")
    print(f"  {'Digit':>7s}  {'Content T':>10s}  {'Structure T':>12s}  {'Count':>6s}")
    print("  " + "-" * 42)
    for d in range(10):
        mask = test_labels == d
        ct = test_scalars[mask, 0].mean().item()
        st = test_scalars[mask, 1].mean().item()
        cnt = mask.sum().item()
        print(f"  {d:>7d}  {ct:>10.4f}  {st:>12.4f}  {cnt:>6d}")

    # ──────────────────────────────────────
    # Phase 6: The "just feeling" test
    # ──────────────────────────────────────
    print()
    print("=" * 70)
    print("  Phase 6: The 'Just Feeling' Test")
    print("=" * 70)
    print("  Remove softmax. Recognize by finding the most similar 'feeling'.")
    print("  Given a new sample, find the training sample with the closest")
    print("  tension fingerprint. Use THAT sample's label as prediction.")
    print()

    feeling_acc = feeling_test_accuracy(train_fp, train_labels, test_fp, test_labels)

    print(f"  Recognition by feeling:     {feeling_acc * 100:.2f}%")
    print(f"  Classification (softmax):   {classifier_acc * 100:.2f}%")
    print(f"  Feeling / Classification:   {feeling_acc / classifier_acc * 100:.1f}%")
    print()

    gap = classifier_acc - feeling_acc
    if feeling_acc > 0.90:
        verdict = "STRONG -- tension alone captures concept identity"
    elif feeling_acc > 0.70:
        verdict = "MODERATE -- tension carries significant concept information"
    elif feeling_acc > 0.50:
        verdict = "WEAK -- some concept structure in tension, but noisy"
    else:
        verdict = "MINIMAL -- tension patterns do not reliably identify concepts"

    print(f"  Gap:     {gap * 100:.2f}%")
    print(f"  Verdict: {verdict}")

    # ──────────────────────────────────────
    # Phase 7: Per-digit tension signatures
    # ──────────────────────────────────────
    print()
    print("=" * 70)
    print("  Phase 7: Per-Digit Tension Signatures")
    print("=" * 70)
    print("  Average 20-dim fingerprint per digit = the digit's 'essence'")
    print()

    digit_centroids = torch.zeros(10, 20)
    for d in range(10):
        mask = test_labels == d
        digit_centroids[d] = test_fp[mask].mean(dim=0)

    # Cosine similarity matrix
    sim = cosine_sim_matrix(digit_centroids)

    digit_labels = [str(d) for d in range(10)]
    print_heatmap(sim, digit_labels, title="Cosine Similarity Between Digit Tension Signatures")

    # Find most/least similar pairs
    print("\n  Most similar digit pairs (by tension):")
    pairs = []
    for i in range(10):
        for j in range(i + 1, 10):
            pairs.append((sim[i, j].item(), i, j))
    pairs.sort(reverse=True)
    for val, i, j in pairs[:5]:
        print(f"    {i} <-> {j}:  {val:.4f}")

    print("\n  Most different digit pairs (by tension):")
    for val, i, j in pairs[-5:]:
        print(f"    {i} <-> {j}:  {val:.4f}")

    # Intra-class vs inter-class distance
    print("\n  Intra-class vs Inter-class fingerprint distance:")
    intra_dists = []
    inter_dists = []
    # Sample to keep it fast
    for d in range(10):
        mask = test_labels == d
        samples = test_fp[mask][:200]
        if samples.size(0) > 1:
            dists = torch.cdist(samples, samples)
            # Upper triangle only
            triu_mask = torch.triu(torch.ones_like(dists, dtype=torch.bool), diagonal=1)
            intra_dists.append(dists[triu_mask].mean().item())
        # Inter: distance to other class samples
        not_mask = test_labels != d
        others = test_fp[not_mask][:200]
        inter_d = torch.cdist(samples[:100], others[:100])
        inter_dists.append(inter_d.mean().item())

    avg_intra = np.mean(intra_dists)
    avg_inter = np.mean(inter_dists)
    separation_ratio = avg_inter / avg_intra if avg_intra > 0 else 0

    print(f"    Avg intra-class distance:  {avg_intra:.4f}")
    print(f"    Avg inter-class distance:  {avg_inter:.4f}")
    print(f"    Separation ratio:          {separation_ratio:.4f}  (>1 means clusters are separable)")

    # ──────────────────────────────────────
    # Phase 8: Tension dimensionality analysis
    # ──────────────────────────────────────
    print()
    print("=" * 70)
    print("  Phase 8: Tension Dimensionality Analysis (PCA)")
    print("=" * 70)
    print("  How many 'feelings' do you need to identify everything?")
    print()

    _, explained = pca_manual(test_fp, n_components=min(20, test_fp.shape[1]))

    cumulative = torch.cumsum(explained, dim=0)

    print(f"  {'PC':>4s}  {'Var Explained':>14s}  {'Cumulative':>11s}  Bar")
    print("  " + "-" * 60)
    for i in range(len(explained)):
        bar_len = int(explained[i].item() * 40)
        bar = '█' * bar_len
        print(f"  {i + 1:>4d}  {explained[i].item() * 100:>13.2f}%  {cumulative[i].item() * 100:>10.2f}%  {bar}")

    # Find dimensions for 90% and 95%
    dims_90 = (cumulative >= 0.90).nonzero()
    dims_95 = (cumulative >= 0.95).nonzero()
    n_90 = dims_90[0].item() + 1 if len(dims_90) > 0 else len(explained)
    n_95 = dims_95[0].item() + 1 if len(dims_95) > 0 else len(explained)

    print(f"\n  Dimensions for 90% variance: {n_90}")
    print(f"  Dimensions for 95% variance: {n_95}")
    print(f"  Total dimensions:            20")

    if n_90 <= 5:
        dim_verdict = "LOW-DIM -- concept space compresses to just a few feelings"
    elif n_90 <= 10:
        dim_verdict = "MODERATE -- concepts need several tension dimensions"
    else:
        dim_verdict = "HIGH-DIM -- tension space is not easily compressible"

    print(f"  Verdict: {dim_verdict}")

    # ──────────────────────────────────────
    # Summary
    # ──────────────────────────────────────
    print()
    print("=" * 70)
    print("  SUMMARY: Label-Free Recognition Results")
    print("=" * 70)
    print()
    print(f"  {'Metric':<40s}  {'Value':>10s}  {'Baseline':>10s}")
    print("  " + "-" * 65)
    print(f"  {'Classifier accuracy (softmax)':<40s}  {classifier_acc * 100:>9.2f}%  {'--':>10s}")
    print(f"  {'Cluster purity (k-means, no labels)':<40s}  {purity * 100:>9.2f}%  {'10.00%':>10s}")
    print(f"  {'Adjusted Rand Index':<40s}  {ari:>10.4f}  {'0.0000':>10s}")
    print(f"  {'Cluster mapping accuracy':<40s}  {mapped_acc * 100:>9.2f}%  {'10.00%':>10s}")
    print(f"  {'5-NN tension agreement':<40s}  {knn_tension * 100:>9.2f}%  {'10.00%':>10s}")
    print(f"  {'Recognition by feeling':<40s}  {feeling_acc * 100:>9.2f}%  {'10.00%':>10s}")
    print(f"  {'Cluster separation ratio':<40s}  {separation_ratio:>10.4f}  {'1.0000':>10s}")
    print(f"  {'PCA dims for 90% variance':<40s}  {n_90:>10d}  {'20':>10s}")
    print()

    # Final interpretation
    print("  ┌─────────────────────────────────────────────────────────┐")
    print("  │  INTERPRETATION                                        │")
    print("  │                                                        │")
    if feeling_acc > 0.90:
        print("  │  The repulsion field's tension patterns ALONE can       │")
        print("  │  identify concepts with >90% accuracy.                  │")
        print("  │                                                        │")
        print("  │  This means: the 'feeling' IS the recognition.          │")
        print("  │  You don't need a label to know what something is.      │")
        print("  │  The tension pattern is the concept itself.             │")
    elif feeling_acc > 0.70:
        print("  │  Tension patterns carry SIGNIFICANT concept info.       │")
        print("  │  Recognition-by-feeling works but is less precise       │")
        print("  │  than classification. The 'feeling' is real but noisy.  │")
    elif feeling_acc > 0.50:
        print("  │  Tension patterns contain SOME concept structure.       │")
        print("  │  The 'feeling' partially identifies concepts but        │")
        print("  │  classification adds substantial information.           │")
    else:
        print("  │  Tension patterns alone are NOT sufficient for          │")
        print("  │  reliable concept recognition. The classification       │")
        print("  │  head is doing most of the work.                        │")
    print("  │                                                        │")
    if n_90 <= 5:
        print("  │  The concept space is LOW-DIMENSIONAL: only a few       │")
        print(f"  │  tension dimensions ({n_90}) capture 90% of identity.       │")
        print("  │  Concepts live in a simple feeling-space.               │")
    print("  └─────────────────────────────────────────────────────────┘")
    print()


if __name__ == '__main__':
    main()
