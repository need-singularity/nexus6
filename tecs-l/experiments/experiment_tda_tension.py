#!/usr/bin/env python3
"""TDA on Tension Fingerprints — Topological Data Analysis without external libraries.

Experiment:
  1. Train RepulsionFieldQuad on MNIST (10 epochs)
  2. Extract 20-dim tension fingerprints for 2000 test samples
  3. Compute pairwise distance matrix
  4. Simple persistent homology: sweep epsilon, count connected components
  5. Find merge thresholds: at what epsilon do digit clusters merge?
  6. Build dendrogram-like structure from tension space

Implementation: BFS-based connected components at varying epsilon thresholds.
No external TDA libraries — only numpy and torch.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import time
import sys

from model_utils import load_mnist, train_and_evaluate, count_params
from model_meta_engine import RepulsionFieldQuad, EngineA, EngineE, EngineG, EngineF


# ─────────────────────────────────────────
# Tension Fingerprint Extractor
# ─────────────────────────────────────────

class TensionExtractor(nn.Module):
    """Wraps RepulsionFieldQuad to extract 20-dim tension fingerprints.

    Fingerprint = [repulsion_content(10) | repulsion_structure(10)]
    These are the raw repulsion vectors before field_transform.
    """
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.fingerprints = None

    def extract(self, x):
        """Extract tension fingerprint without computing full forward."""
        with torch.no_grad():
            out_a = self.model.engine_a(x)
            out_e = self.model.engine_e(x)
            out_g = self.model.engine_g(x)
            out_f = self.model.engine_f(x)

            # Content repulsion: A vs G
            repulsion_content = out_a - out_g      # (batch, 10)
            # Structure repulsion: E vs F
            repulsion_structure = out_e - out_f    # (batch, 10)

            # 20-dim tension fingerprint
            fingerprint = torch.cat([repulsion_content, repulsion_structure], dim=-1)
        return fingerprint


# ─────────────────────────────────────────
# Simple Persistent Homology (no external libs)
# ─────────────────────────────────────────

def count_components(dist_matrix, epsilon):
    """Count connected components at distance threshold epsilon using BFS."""
    n = len(dist_matrix)
    visited = [False] * n
    components = 0
    for i in range(n):
        if not visited[i]:
            components += 1
            queue = [i]
            while queue:
                node = queue.pop(0)
                if visited[node]:
                    continue
                visited[node] = True
                for j in range(n):
                    if not visited[j] and dist_matrix[node][j] < epsilon:
                        queue.append(j)
    return components


def count_components_by_label(dist_matrix, labels, epsilon):
    """Count components, tracking which digit labels are in each component."""
    n = len(dist_matrix)
    visited = [False] * n
    component_labels = []  # list of sets of digit labels per component

    for i in range(n):
        if not visited[i]:
            # BFS to find all nodes in this component
            component_members = []
            queue = [i]
            while queue:
                node = queue.pop(0)
                if visited[node]:
                    continue
                visited[node] = True
                component_members.append(node)
                for j in range(n):
                    if not visited[j] and dist_matrix[node][j] < epsilon:
                        queue.append(j)
            # Track which labels are in this component
            member_labels = set(int(labels[m]) for m in component_members)
            component_labels.append((member_labels, len(component_members)))

    return component_labels


def compute_persistence_barcode(dist_matrix, labels, n_epsilons=80):
    """Sweep epsilon and track component count + digit merges."""
    max_dist = np.max(dist_matrix)
    min_dist = np.min(dist_matrix[dist_matrix > 0]) if np.any(dist_matrix > 0) else 0.01

    epsilons = np.linspace(min_dist * 0.5, max_dist * 0.6, n_epsilons)

    results = []
    print(f"\n  Sweeping {n_epsilons} epsilon values from {epsilons[0]:.4f} to {epsilons[-1]:.4f}")
    print(f"  Distance range: min={min_dist:.4f}, max={max_dist:.4f}")

    for i, eps in enumerate(epsilons):
        n_comp = count_components(dist_matrix, eps)
        results.append({'epsilon': eps, 'n_components': n_comp})
        if (i + 1) % 20 == 0 or i == 0:
            print(f"    eps={eps:.4f}: {n_comp} components")

    return epsilons, results


def find_merge_events(dist_matrix, labels, n_epsilons=50):
    """Find at which epsilon different digit classes start sharing components."""
    max_dist = np.max(dist_matrix)
    min_dist = np.min(dist_matrix[dist_matrix > 0]) if np.any(dist_matrix > 0) else 0.01

    epsilons = np.linspace(min_dist * 0.5, max_dist * 0.5, n_epsilons)

    # Per-digit: at what epsilon does each digit first merge with another?
    digit_merge_eps = {d: None for d in range(10)}
    # Pairwise: at what epsilon do digit i and digit j first share a component?
    pair_merge_eps = {}

    print(f"\n  Tracking digit merge events across {n_epsilons} thresholds...")

    for eps in epsilons:
        comp_labels = count_components_by_label(dist_matrix, labels, eps)

        # Check which digit pairs share a component
        for member_labels, size in comp_labels:
            if len(member_labels) > 1:
                for d1 in member_labels:
                    if digit_merge_eps[d1] is None:
                        digit_merge_eps[d1] = eps
                    for d2 in member_labels:
                        if d1 < d2:
                            pair = (d1, d2)
                            if pair not in pair_merge_eps:
                                pair_merge_eps[pair] = eps

    return digit_merge_eps, pair_merge_eps


def per_digit_centroids(fingerprints, labels):
    """Compute centroid of each digit in tension space."""
    centroids = {}
    for d in range(10):
        mask = labels == d
        if mask.sum() > 0:
            centroids[d] = fingerprints[mask].mean(axis=0)
    return centroids


def centroid_distance_matrix(centroids):
    """Distance matrix between digit centroids."""
    n = len(centroids)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            D[i][j] = np.linalg.norm(centroids[i] - centroids[j])
    return D


def build_dendrogram(centroid_dists):
    """Build a simple agglomerative dendrogram from centroid distances.

    Returns merge history: list of (cluster_i, cluster_j, distance).
    """
    n = len(centroid_dists)
    # Each cluster starts as a single digit
    clusters = {i: [i] for i in range(n)}
    active = set(range(n))
    merges = []

    dist = centroid_dists.copy()
    np.fill_diagonal(dist, np.inf)

    while len(active) > 1:
        # Find closest pair
        min_dist = np.inf
        min_i, min_j = -1, -1
        active_list = sorted(active)
        for i in active_list:
            for j in active_list:
                if i < j and dist[i][j] < min_dist:
                    min_dist = dist[i][j]
                    min_i, min_j = i, j

        if min_i < 0:
            break

        merges.append((clusters[min_i][:], clusters[min_j][:], min_dist))

        # Merge j into i (average linkage)
        new_cluster = clusters[min_i] + clusters[min_j]
        clusters[min_i] = new_cluster
        del clusters[min_j]
        active.remove(min_j)

        # Update distances (average linkage)
        for k in active:
            if k != min_i:
                dist[min_i][k] = (dist[min_i][k] + dist[min_j][k]) / 2
                dist[k][min_i] = dist[min_i][k]

        # Invalidate min_j
        for k in range(n):
            dist[min_j][k] = np.inf
            dist[k][min_j] = np.inf

    return merges


def draw_ascii_barcode(epsilons, results, width=70):
    """Draw ASCII persistence barcode."""
    print("\n" + "=" * 75)
    print("  PERSISTENCE BARCODE (connected components vs epsilon)")
    print("=" * 75)

    # Sample at most 30 rows
    step = max(1, len(results) // 30)
    max_comp = max(r['n_components'] for r in results)

    print(f"  {'epsilon':>8}  {'#comp':>6}  bar")
    print(f"  {'':>8}  {'':>6}  |{'.' * width}|")

    for i in range(0, len(results), step):
        r = results[i]
        bar_len = int(r['n_components'] / max_comp * width) if max_comp > 0 else 0
        bar = '#' * bar_len
        print(f"  {r['epsilon']:>8.4f}  {r['n_components']:>6}  |{bar:<{width}}|")

    # End state
    r = results[-1]
    bar_len = int(r['n_components'] / max_comp * width) if max_comp > 0 else 0
    bar = '#' * bar_len
    print(f"  {r['epsilon']:>8.4f}  {r['n_components']:>6}  |{bar:<{width}}|")
    print(f"  {'':>8}  {'':>6}  |{'.' * width}|")
    print()


def draw_ascii_dendrogram(merges):
    """Print dendrogram merge history."""
    print("\n" + "=" * 75)
    print("  TENSION SPACE DENDROGRAM (agglomerative clustering of digit centroids)")
    print("=" * 75)
    print(f"  {'Step':>4}  {'Merge':>30}  {'Distance':>10}  Visual")
    print("-" * 75)

    max_dist = max(m[2] for m in merges) if merges else 1
    bar_width = 40

    for i, (c1, c2, d) in enumerate(merges):
        c1_str = ','.join(str(x) for x in sorted(c1))
        c2_str = ','.join(str(x) for x in sorted(c2))
        merge_str = f"{{{c1_str}}} + {{{c2_str}}}"
        bar_len = int(d / max_dist * bar_width)
        bar = '=' * bar_len + '|'
        print(f"  {i+1:>4}  {merge_str:>30}  {d:>10.4f}  {bar}")

    print()


def draw_digit_separation(centroid_dists):
    """Draw a heatmap-like display of inter-digit distances."""
    print("\n" + "=" * 75)
    print("  INTER-DIGIT CENTROID DISTANCES IN TENSION SPACE")
    print("=" * 75)

    max_d = np.max(centroid_dists[centroid_dists < np.inf])
    min_d = np.min(centroid_dists[centroid_dists > 0])

    # Header
    print(f"  {'':>4}", end='')
    for j in range(10):
        print(f"  {j:>6}", end='')
    print()

    symbols = ' ._-=+*#@'

    for i in range(10):
        print(f"  {i:>4}", end='')
        for j in range(10):
            if i == j:
                print(f"  {'---':>6}", end='')
            else:
                d = centroid_dists[i][j]
                # Normalized intensity
                norm = (d - min_d) / (max_d - min_d) if max_d > min_d else 0
                sym_idx = int(norm * (len(symbols) - 1))
                sym = symbols[min(sym_idx, len(symbols) - 1)]
                print(f"  {d:>5.2f}{sym}", end='')
        print()

    print(f"\n  Distance range: {min_d:.4f} (closest) to {max_d:.4f} (farthest)")

    # Find closest and farthest pairs
    pairs = []
    for i in range(10):
        for j in range(i + 1, 10):
            pairs.append((centroid_dists[i][j], i, j))
    pairs.sort()

    print(f"\n  Closest 5 digit pairs (most confusable in tension space):")
    for d, i, j in pairs[:5]:
        print(f"    {i}-{j}: {d:.4f}")
    print(f"\n  Farthest 5 digit pairs (most separated):")
    for d, i, j in pairs[-5:]:
        print(f"    {i}-{j}: {d:.4f}")


def analyze_tension_statistics(fingerprints, labels):
    """Per-digit statistics of tension fingerprints."""
    print("\n" + "=" * 75)
    print("  PER-DIGIT TENSION STATISTICS")
    print("=" * 75)

    print(f"  {'Digit':>5} {'Count':>6} {'|Content|':>10} {'|Struct|':>10} "
          f"{'Norm':>8} {'StdNorm':>8}")
    print("-" * 65)

    for d in range(10):
        mask = labels == d
        fp = fingerprints[mask]
        content_norm = np.linalg.norm(fp[:, :10], axis=1)
        struct_norm = np.linalg.norm(fp[:, 10:], axis=1)
        total_norm = np.linalg.norm(fp, axis=1)

        print(f"  {d:>5} {mask.sum():>6} {content_norm.mean():>10.4f} "
              f"{struct_norm.mean():>10.4f} {total_norm.mean():>8.4f} "
              f"{total_norm.std():>8.4f}")


def analyze_content_vs_structure(fingerprints, labels):
    """Analyze whether content or structure axis separates digits better."""
    print("\n" + "=" * 75)
    print("  CONTENT vs STRUCTURE AXIS ANALYSIS")
    print("  (Which repulsion axis separates digits better?)")
    print("=" * 75)

    content_fp = fingerprints[:, :10]
    struct_fp = fingerprints[:, 10:]

    # Compute inter-class / intra-class distance ratio for each axis
    for name, fp in [("Content (A vs G)", content_fp), ("Structure (E vs F)", struct_fp),
                     ("Combined (20-dim)", fingerprints)]:
        centroids = {}
        for d in range(10):
            mask = labels == d
            if mask.sum() > 0:
                centroids[d] = fp[mask].mean(axis=0)

        # Inter-class distance
        inter_dists = []
        for i in range(10):
            for j in range(i + 1, 10):
                inter_dists.append(np.linalg.norm(centroids[i] - centroids[j]))

        # Intra-class distance (average distance to centroid)
        intra_dists = []
        for d in range(10):
            mask = labels == d
            if mask.sum() > 0:
                dists = np.linalg.norm(fp[mask] - centroids[d], axis=1)
                intra_dists.append(dists.mean())

        inter_mean = np.mean(inter_dists)
        intra_mean = np.mean(intra_dists)
        separation = inter_mean / (intra_mean + 1e-8)

        print(f"\n  {name}:")
        print(f"    Inter-class mean dist: {inter_mean:.4f}")
        print(f"    Intra-class mean dist: {intra_mean:.4f}")
        print(f"    Separation ratio:      {separation:.4f}  "
              f"({'GOOD' if separation > 2 else 'MODERATE' if separation > 1 else 'POOR'})")


# ─────────────────────────────────────────
# Main Experiment
# ─────────────────────────────────────────

def main():
    print()
    print("=" * 75)
    print("   EXPERIMENT: Topological Data Analysis on Tension Fingerprints")
    print("   RepulsionFieldQuad 4-pole tension -> 20-dim fingerprints -> TDA")
    print("=" * 75)

    t0 = time.time()

    # ── Step 1: Train RepulsionFieldQuad ──
    print("\n[Step 1] Training RepulsionFieldQuad on MNIST (10 epochs)...")
    train_loader, test_loader = load_mnist(batch_size=128)
    input_dim, hidden_dim, output_dim = 784, 48, 10

    model = RepulsionFieldQuad(input_dim, hidden_dim, output_dim)
    print(f"  Parameters: {count_params(model):,}")

    losses, accs = train_and_evaluate(
        model, train_loader, test_loader, epochs=10, aux_lambda=0.01
    )
    print(f"  Final accuracy: {accs[-1]*100:.2f}%")
    print(f"  Tension content: {model.tension_content:.4f}")
    print(f"  Tension structure: {model.tension_structure:.4f}")

    # ── Step 2: Extract tension fingerprints ──
    print("\n[Step 2] Extracting 20-dim tension fingerprints for 2000 test samples...")
    extractor = TensionExtractor(model)
    model.eval()

    all_fingerprints = []
    all_labels = []
    n_samples = 0
    max_samples = 2000

    for X, y in test_loader:
        X_flat = X.view(X.size(0), -1)
        fp = extractor.extract(X_flat)
        all_fingerprints.append(fp.numpy())
        all_labels.append(y.numpy())
        n_samples += len(y)
        if n_samples >= max_samples:
            break

    fingerprints = np.concatenate(all_fingerprints, axis=0)[:max_samples]
    labels = np.concatenate(all_labels, axis=0)[:max_samples]

    print(f"  Extracted {len(fingerprints)} fingerprints, shape={fingerprints.shape}")
    print(f"  Label distribution: {dict(zip(*np.unique(labels, return_counts=True)))}")

    # ── Step 3: Per-digit statistics ──
    print("\n[Step 3] Analyzing tension statistics per digit...")
    analyze_tension_statistics(fingerprints, labels)

    # ── Step 4: Content vs Structure axis analysis ──
    print("\n[Step 4] Content vs Structure axis separation...")
    analyze_content_vs_structure(fingerprints, labels)

    # ── Step 5: Centroid distances + dendrogram ──
    print("\n[Step 5] Computing digit centroids and distances...")
    centroids = per_digit_centroids(fingerprints, labels)
    centroid_array = np.array([centroids[d] for d in range(10)])
    centroid_dists = centroid_distance_matrix(centroid_array)

    draw_digit_separation(centroid_dists)

    # ── Step 6: Dendrogram ──
    print("\n[Step 6] Building dendrogram from tension space centroids...")
    merges = build_dendrogram(centroid_dists)
    draw_ascii_dendrogram(merges)

    # ── Step 7: Persistence barcode (subsample for speed) ──
    print("\n[Step 7] Computing persistence barcode (subsampled)...")
    # Subsample to 500 for distance matrix computation speed
    n_sub = 500
    idx = np.random.RandomState(42).choice(len(fingerprints), n_sub, replace=False)
    fp_sub = fingerprints[idx]
    labels_sub = labels[idx]

    print(f"  Subsampled to {n_sub} points for distance matrix...")
    # Compute pairwise distance matrix
    dist_matrix = np.zeros((n_sub, n_sub))
    for i in range(n_sub):
        diff = fp_sub - fp_sub[i]
        dist_matrix[i] = np.sqrt((diff ** 2).sum(axis=1))

    print(f"  Distance matrix: {dist_matrix.shape}")
    print(f"  Distance stats: min={dist_matrix[dist_matrix>0].min():.4f}, "
          f"max={dist_matrix.max():.4f}, mean={dist_matrix[dist_matrix>0].mean():.4f}")

    # ── Step 8: Sweep epsilon for persistence ──
    print("\n[Step 8] Sweeping epsilon for persistence barcode...")
    epsilons, barcode_results = compute_persistence_barcode(
        dist_matrix, labels_sub, n_epsilons=60
    )
    draw_ascii_barcode(epsilons, barcode_results)

    # ── Step 9: Digit merge events ──
    print("\n[Step 9] Tracking digit merge events...")
    digit_merge, pair_merge = find_merge_events(
        dist_matrix, labels_sub, n_epsilons=40
    )

    print("\n  First merge epsilon per digit:")
    for d in range(10):
        eps = digit_merge[d]
        if eps is not None:
            print(f"    Digit {d}: eps={eps:.4f}")
        else:
            print(f"    Digit {d}: never merged (isolated)")

    if pair_merge:
        print(f"\n  Earliest digit pair merges (sorted):")
        sorted_merges = sorted(pair_merge.items(), key=lambda x: x[1])
        for (d1, d2), eps in sorted_merges[:15]:
            print(f"    {d1}-{d2}: eps={eps:.4f}")

        print(f"\n  Latest digit pair merges:")
        for (d1, d2), eps in sorted_merges[-5:]:
            print(f"    {d1}-{d2}: eps={eps:.4f}")

    # ── Step 10: Key findings summary ──
    elapsed = time.time() - t0
    print("\n" + "=" * 75)
    print("  SUMMARY: TDA ON TENSION FINGERPRINTS")
    print("=" * 75)

    print(f"\n  Model: RepulsionFieldQuad (4-pole), accuracy={accs[-1]*100:.2f}%")
    print(f"  Fingerprint dim: 20 (content:10 + structure:10)")
    print(f"  Samples analyzed: {len(fingerprints)}")
    print(f"  Time elapsed: {elapsed:.1f}s")

    # Key insight: which digits are topologically closest?
    if pair_merge:
        sorted_merges = sorted(pair_merge.items(), key=lambda x: x[1])
        earliest = sorted_merges[0]
        latest = sorted_merges[-1]
        print(f"\n  Topologically closest digits: {earliest[0][0]}-{earliest[0][1]} "
              f"(merge at eps={earliest[1]:.4f})")
        print(f"  Topologically farthest digits: {latest[0][0]}-{latest[0][1]} "
              f"(merge at eps={latest[1]:.4f})")

    # Dendrogram summary
    if merges:
        print(f"\n  Dendrogram merge order (first to last):")
        for i, (c1, c2, d) in enumerate(merges):
            c1s = ','.join(str(x) for x in sorted(c1))
            c2s = ','.join(str(x) for x in sorted(c2))
            print(f"    {i+1}. {{{c1s}}} + {{{c2s}}} at d={d:.4f}")

    # Persistence insight
    comp_10 = None
    comp_1 = None
    for r in barcode_results:
        if comp_10 is None and r['n_components'] <= 10:
            comp_10 = r['epsilon']
        if comp_1 is None and r['n_components'] <= 1:
            comp_1 = r['epsilon']

    if comp_10:
        print(f"\n  Epsilon for <=10 components: {comp_10:.4f}")
    if comp_1:
        print(f"  Epsilon for 1 component:     {comp_1:.4f}")
    if comp_10 and comp_1:
        print(f"  Persistence range (10->1):   {comp_1 - comp_10:.4f}")
        print(f"  Ratio:                       {comp_1/comp_10:.2f}x")

    print(f"\n  Interpretation:")
    print(f"    - Tension fingerprints encode how 4 engines disagree on each input")
    print(f"    - Topological structure reveals which digits create similar engine conflicts")
    print(f"    - Early merges = digits that 'feel the same' to the repulsion field")
    print(f"    - Late merges = digits with fundamentally different tension signatures")
    print()


if __name__ == '__main__':
    main()
