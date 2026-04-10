#!/usr/bin/env python3
"""H-286: Topological Data Analysis on Tension Fingerprints.

Experiment:
  1. Train RepulsionFieldQuad on MNIST (10 epochs)
  2. Extract 10-dim tension fingerprints (per-class tension) for 1000 test samples
  3. Compute persistent homology:
     - H0 (connected components): MST-based exact computation
     - H1 (loops): approximate via Euler characteristic at varying thresholds
  4. Per-digit Betti numbers b0, b1
  5. Per-digit persistence (how long features last)
  6. Test: b0 ~ 10 (one cluster per digit)?
  7. Compare digit topological complexity
  8. Pairwise centroid distances vs confusion matrix topology match

Uses ripser if available, otherwise efficient scipy/MST fallback.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn.functional as F
import numpy as np
import time

from model_utils import load_mnist, train_and_evaluate, count_params
from model_meta_engine import RepulsionFieldQuad

from scipy.spatial.distance import pdist, squareform
from scipy.sparse.csgraph import minimum_spanning_tree, connected_components
from scipy.sparse import csr_matrix
from scipy.cluster.hierarchy import linkage
from scipy.stats import spearmanr

# ── Check for ripser ──
USE_RIPSER = False
try:
    from ripser import ripser as ripser_fn
    USE_RIPSER = True
    print("[INFO] ripser available -- using full persistent homology")
except ImportError:
    print("[INFO] ripser not available -- using scipy/MST fallback")


# ─────────────────────────────────────────
# Tension Fingerprint Extraction (10-dim)
# ─────────────────────────────────────────

def extract_tension_fingerprints(model, test_loader, max_samples=1000):
    """Extract 10-dim tension fingerprints: per-class std across 4 engines."""
    model.eval()
    all_fps = []
    all_labels = []
    n = 0

    with torch.no_grad():
        for X, y in test_loader:
            X_flat = X.view(X.size(0), -1)
            out_a = model.engine_a(X_flat)
            out_e = model.engine_e(X_flat)
            out_g = model.engine_g(X_flat)
            out_f = model.engine_f(X_flat)

            stacked = torch.stack([out_a, out_e, out_g, out_f], dim=0)  # (4, batch, 10)
            tension_fp = stacked.std(dim=0)  # (batch, 10)

            all_fps.append(tension_fp.numpy())
            all_labels.append(y.numpy())
            n += len(y)
            if n >= max_samples:
                break

    fps = np.concatenate(all_fps)[:max_samples]
    labels = np.concatenate(all_labels)[:max_samples]
    return fps, labels


# ─────────────────────────────────────────
# Persistent Homology (MST-based, efficient)
# ─────────────────────────────────────────

def mst_persistence_h0(dist_matrix_full):
    """Exact H0 persistence diagram from MST.

    Each MST edge = death of one component. O(n^2) for dense input.
    Returns H0 diagram: array of (birth, death) pairs.
    """
    mst = minimum_spanning_tree(csr_matrix(dist_matrix_full)).toarray()
    edges = []
    rows, cols = np.nonzero(mst)
    for r, c in zip(rows, cols):
        if r < c:  # avoid duplicates
            edges.append(mst[r, c])
    edges = sorted(edges)

    h0_dgm = [[0.0, e] for e in edges]
    h0_dgm.append([0.0, np.inf])  # last component lives forever
    return np.array(h0_dgm)


def approx_h1_persistence(dist_matrix_full, n_epsilons=30):
    """Approximate H1 (loops) via Euler characteristic sweep.

    At each threshold eps:
      edges(eps) = number of edges with weight <= eps
      components(eps) = connected components at eps
      approx_h1(eps) = edges - n + components  (from Euler: V - E + F = chi)

    Track birth/death of H1 features by monitoring approx_h1 changes.
    """
    n = len(dist_matrix_full)
    # Get upper triangle distances
    dists_upper = []
    for i in range(n):
        for j in range(i + 1, n):
            dists_upper.append(dist_matrix_full[i, j])
    dists_upper = np.array(dists_upper)

    p10 = np.percentile(dists_upper, 10)
    p90 = np.percentile(dists_upper, 90)
    epsilons = np.linspace(p10 * 0.5, p90, n_epsilons)

    h1_values = []
    for eps in epsilons:
        adj = (dist_matrix_full <= eps) & (dist_matrix_full > 0)
        n_edges = adj.sum() // 2
        n_comp = connected_components(csr_matrix(adj.astype(float)), directed=False)[0]
        h1_approx = max(0, n_edges - n + n_comp)
        h1_values.append((eps, h1_approx, n_edges, n_comp))

    # Convert to persistence-like diagram: track when H1 features appear/disappear
    h1_dgm = []
    prev_h1 = 0
    active_births = []
    for eps, h1, ne, nc in h1_values:
        if h1 > prev_h1:
            # New loops born
            for _ in range(h1 - prev_h1):
                active_births.append(eps)
        elif h1 < prev_h1:
            # Loops died (filled in)
            for _ in range(prev_h1 - h1):
                if active_births:
                    birth = active_births.pop(0)
                    h1_dgm.append([birth, eps])
        prev_h1 = h1

    # Remaining active loops: they persist to infinity (or end of range)
    for birth in active_births:
        h1_dgm.append([birth, epsilons[-1]])

    if h1_dgm:
        return np.array(h1_dgm)
    return np.empty((0, 2))


def compute_ph(points, maxdim=1):
    """Compute persistent homology. Uses ripser if available, else MST fallback."""
    if USE_RIPSER:
        result = ripser_fn(points, maxdim=maxdim)
        return result['dgms']

    dist_condensed = pdist(points)
    dist_full = squareform(dist_condensed)

    h0_dgm = mst_persistence_h0(dist_full)
    h1_dgm = approx_h1_persistence(dist_full, n_epsilons=30) if maxdim >= 1 else np.empty((0, 2))

    return [h0_dgm, h1_dgm]


def persistence_stats(dgm):
    """Stats for one dimension's persistence diagram."""
    finite = dgm[np.isfinite(dgm[:, 1])]
    if len(finite) == 0:
        return {'count': 0, 'mean_pers': 0.0, 'max_pers': 0.0, 'total_pers': 0.0}
    lifetimes = finite[:, 1] - finite[:, 0]
    return {
        'count': len(finite),
        'mean_pers': float(np.mean(lifetimes)),
        'max_pers': float(np.max(lifetimes)),
        'total_pers': float(np.sum(lifetimes)),
    }


# ─────────────────────────────────────────
# Per-digit analysis
# ─────────────────────────────────────────

def per_digit_analysis(fps, labels):
    """Per-digit persistent homology."""
    results = {}
    for d in range(10):
        mask = labels == d
        pts = fps[mask]
        if len(pts) < 5:
            results[d] = None
            continue

        # Subsample large digit classes for speed
        if len(pts) > 150:
            idx = np.random.RandomState(d).choice(len(pts), 150, replace=False)
            pts = pts[idx]

        dgms = compute_ph(pts, maxdim=1)
        h0_stats = persistence_stats(dgms[0])
        h1_stats = persistence_stats(dgms[1]) if len(dgms) > 1 else {'count': 0, 'mean_pers': 0, 'max_pers': 0, 'total_pers': 0}

        results[d] = {
            'n_samples': int(mask.sum()),
            'n_analyzed': len(pts),
            'h0': h0_stats,
            'h1': h1_stats,
        }

    return results


def confusion_topology_match(centroid_dists, fps, labels):
    """Check if close centroids = high confusion (tension overlap)."""
    pairs_by_dist = []
    for i in range(10):
        for j in range(i + 1, 10):
            pairs_by_dist.append((centroid_dists[i, j], i, j))
    pairs_by_dist.sort()

    centroids = {}
    for d in range(10):
        mask = labels == d
        if mask.sum() > 0:
            centroids[d] = fps[mask].mean(axis=0)

    confusion_scores = {}
    for i in range(10):
        for j in range(i + 1, 10):
            if i not in centroids or j not in centroids:
                continue
            mask_i = labels == i
            pts_i = fps[mask_i]
            dist_to_i = np.linalg.norm(pts_i - centroids[i], axis=1)
            dist_to_j = np.linalg.norm(pts_i - centroids[j], axis=1)
            overlap_i = (dist_to_j < dist_to_i).mean()

            mask_j = labels == j
            pts_j = fps[mask_j]
            dist_to_i2 = np.linalg.norm(pts_j - centroids[i], axis=1)
            dist_to_j2 = np.linalg.norm(pts_j - centroids[j], axis=1)
            overlap_j = (dist_to_i2 < dist_to_j2).mean()

            confusion_scores[(i, j)] = (overlap_i + overlap_j) / 2

    return pairs_by_dist, confusion_scores


# ─────────────────────────────────────────
# ASCII Visualization
# ─────────────────────────────────────────

def draw_persistence_diagram(dgms, title=""):
    """ASCII persistence diagram."""
    print(f"\n{'=' * 75}")
    print(f"  PERSISTENCE DIAGRAM {title}")
    print(f"{'=' * 75}")

    for dim, dgm in enumerate(dgms):
        finite = dgm[np.isfinite(dgm[:, 1])]
        if len(finite) == 0:
            print(f"\n  H{dim}: no finite features")
            continue

        births = finite[:, 0]
        deaths = finite[:, 1]
        lifetimes = deaths - births

        print(f"\n  H{dim}: {len(finite)} features")
        print(f"    Birth range:  [{births.min():.4f}, {births.max():.4f}]")
        print(f"    Death range:  [{deaths.min():.4f}, {deaths.max():.4f}]")
        print(f"    Persistence:  mean={lifetimes.mean():.4f}, max={lifetimes.max():.4f}, "
              f"total={lifetimes.sum():.4f}")

        # Histogram of lifetimes
        n_bins = min(20, max(5, len(finite) // 5))
        hist, bin_edges = np.histogram(lifetimes, bins=n_bins)
        max_count = max(hist) if max(hist) > 0 else 1
        bar_width = 40

        print(f"\n    Lifetime histogram (H{dim}):")
        print(f"    {'lifetime':>10}  {'count':>5}  bar")
        for k in range(n_bins):
            if hist[k] > 0:
                bar_len = int(hist[k] / max_count * bar_width)
                bar = '#' * max(bar_len, 1)
                mid = (bin_edges[k] + bin_edges[k + 1]) / 2
                print(f"    {mid:>10.4f}  {hist[k]:>5}  {bar}")


def draw_betti_table(digit_results):
    """Per-digit Betti number table."""
    print(f"\n{'=' * 75}")
    print(f"  PER-DIGIT BETTI NUMBERS AND PERSISTENCE")
    print(f"{'=' * 75}")

    print(f"\n  {'Digit':>5} {'N':>5} {'Nsub':>5} {'#H0':>6} {'#H1':>6} "
          f"{'H0 mean':>9} {'H1 mean':>9} {'H0 max':>8} {'H1 max':>8} {'H0 tot':>8} {'H1 tot':>8}")
    print(f"  {'-' * 88}")

    for d in range(10):
        r = digit_results.get(d)
        if r is None:
            print(f"  {d:>5} {'N/A':>5}")
            continue
        h0 = r['h0']
        h1 = r['h1']
        print(f"  {d:>5} {r['n_samples']:>5} {r['n_analyzed']:>5} "
              f"{h0['count']:>6} {h1['count']:>6} "
              f"{h0['mean_pers']:>9.4f} {h1['mean_pers']:>9.4f} "
              f"{h0['max_pers']:>8.4f} {h1['max_pers']:>8.4f} "
              f"{h0['total_pers']:>8.2f} {h1['total_pers']:>8.2f}")


def draw_complexity_ranking(digit_results):
    """Rank digits by topological complexity."""
    print(f"\n{'=' * 75}")
    print(f"  TOPOLOGICAL COMPLEXITY RANKING")
    print(f"  (total persistence H0+H1 = topological richness)")
    print(f"{'=' * 75}")

    complexities = []
    for d in range(10):
        r = digit_results.get(d)
        if r is None:
            continue
        total = r['h0']['total_pers'] + r['h1']['total_pers']
        complexities.append((d, total, r['h0']['total_pers'], r['h1']['total_pers'],
                             r['h0']['count'], r['h1']['count']))

    complexities.sort(key=lambda x: x[1], reverse=True)
    max_total = complexities[0][1] if complexities else 1

    print(f"\n  {'Rank':>4} {'Digit':>5} {'Total':>8} {'H0 tot':>8} {'H1 tot':>8} "
          f"{'#H0':>5} {'#H1':>5}  bar")
    print(f"  {'-' * 70}")

    for rank, (d, total, h0t, h1t, h0c, h1c) in enumerate(complexities, 1):
        bar_len = int(total / max_total * 40) if max_total > 0 else 0
        bar = '#' * max(bar_len, 1)
        print(f"  {rank:>4} {d:>5} {total:>8.2f} {h0t:>8.2f} {h1t:>8.2f} "
              f"{h0c:>5} {h1c:>5}  {bar}")


def draw_centroid_heatmap(dists):
    """ASCII heatmap of inter-digit centroid distances."""
    print(f"\n{'=' * 75}")
    print(f"  INTER-DIGIT CENTROID DISTANCES IN TENSION SPACE")
    print(f"{'=' * 75}")

    max_d = np.max(dists[dists < np.inf])
    min_d = np.min(dists[dists > 0]) if np.any(dists > 0) else 0

    print(f"\n  {'':>4}", end='')
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
                d = dists[i, j]
                norm = (d - min_d) / (max_d - min_d) if max_d > min_d else 0
                sym_idx = int(norm * (len(symbols) - 1))
                sym = symbols[min(sym_idx, len(symbols) - 1)]
                print(f" {d:>5.3f}{sym}", end='')
        print()

    print(f"\n  Range: {min_d:.4f} (closest) to {max_d:.4f} (farthest)")


def draw_confusion_topology(pairs_by_dist, confusion_scores):
    """Show topology vs confusion match."""
    print(f"\n{'=' * 75}")
    print(f"  TOPOLOGY vs CONFUSION MATCH")
    print(f"  (Do close centroids = high confusion?)")
    print(f"{'=' * 75}")

    print(f"\n  {'Rank':>4} {'Pair':>6} {'CentDist':>9} {'Overlap%':>9}  Interpretation")
    print(f"  {'-' * 60}")

    for rank, (dist, i, j) in enumerate(pairs_by_dist[:15], 1):
        overlap = confusion_scores.get((i, j), 0) * 100
        interp = "HIGH CONFUSION" if overlap > 5 else "moderate" if overlap > 1 else "well separated"
        print(f"  {rank:>4}  {i}-{j:>3} {dist:>9.4f} {overlap:>8.1f}%  {interp}")

    # Spearman correlation
    dist_ranks = []
    overlap_ranks = []
    for dist, i, j in pairs_by_dist:
        if (i, j) in confusion_scores:
            dist_ranks.append(dist)
            overlap_ranks.append(confusion_scores[(i, j)])

    if len(dist_ranks) > 2:
        corr, pval = spearmanr(dist_ranks, overlap_ranks)
        print(f"\n  Spearman correlation (distance vs overlap): r={corr:.4f}, p={pval:.4f}")
        if corr < -0.3 and pval < 0.05:
            print(f"  --> CONFIRMED: closer centroids = more confusion (negative correlation)")
        elif corr > 0.3 and pval < 0.05:
            print(f"  --> ANTI-CORRELATION: farther centroids have more overlap (unexpected)")
        elif abs(corr) < 0.2:
            print(f"  --> No clear linear relationship")
        else:
            print(f"  --> Weak relationship (|r| < 0.3 or p > 0.05)")


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────

def main():
    t0 = time.time()

    print()
    print("=" * 75)
    print("   H-286: Topological Data Analysis on Tension Fingerprints")
    print("   RepulsionFieldQuad -> 10-dim tension -> persistent homology")
    print(f"   TDA backend: {'ripser' if USE_RIPSER else 'scipy/MST fallback'}")
    print("=" * 75)

    # ── Step 1: Train RepulsionFieldQuad ──
    print("\n[Step 1] Training RepulsionFieldQuad on MNIST (10 epochs)...")
    train_loader, test_loader = load_mnist(batch_size=128)
    model = RepulsionFieldQuad(784, 48, 10)
    print(f"  Parameters: {count_params(model):,}")

    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs=10, aux_lambda=0.01)
    print(f"  Final accuracy: {accs[-1]*100:.2f}%")
    print(f"  Tension content:   {model.tension_content:.4f}")
    print(f"  Tension structure: {model.tension_structure:.4f}")

    # ── Step 2: Extract fingerprints ──
    print("\n[Step 2] Extracting 10-dim tension fingerprints for 1000 test samples...")
    fps, labels = extract_tension_fingerprints(model, test_loader, max_samples=1000)
    print(f"  Shape: {fps.shape}")
    unique, counts = np.unique(labels, return_counts=True)
    print(f"  Labels: {dict(zip(unique.astype(int), counts))}")
    print(f"  Fingerprint stats: mean={fps.mean():.4f}, std={fps.std():.4f}, "
          f"min={fps.min():.4f}, max={fps.max():.4f}")

    # ── Step 3: Global persistent homology (subsampled for speed) ──
    n_global = min(500, len(fps))
    print(f"\n[Step 3] Computing persistent homology on {n_global} points (subsampled)...")
    idx_global = np.random.RandomState(42).choice(len(fps), n_global, replace=False)
    fps_sub = fps[idx_global]
    labels_sub = labels[idx_global]

    t_ph = time.time()
    dgms_global = compute_ph(fps_sub, maxdim=1)
    print(f"  PH computation time: {time.time() - t_ph:.1f}s")

    draw_persistence_diagram(dgms_global, title=f"(GLOBAL, {n_global} points)")

    h0_global = persistence_stats(dgms_global[0])
    h1_global = persistence_stats(dgms_global[1]) if len(dgms_global) > 1 else {'count': 0, 'mean_pers': 0, 'max_pers': 0, 'total_pers': 0}

    print(f"\n  GLOBAL TOPOLOGY SUMMARY:")
    print(f"    H0 features (components): {h0_global['count']}")
    print(f"    H1 features (loops):      {h1_global.get('count', 0)}")

    # ── b0 ~ 10 test via lifetime gap analysis ──
    print(f"\n  B0 ~ 10 HYPOTHESIS TEST:")
    finite_h0 = dgms_global[0][np.isfinite(dgms_global[0][:, 1])]
    if len(finite_h0) > 0:
        lifetimes = finite_h0[:, 1] - finite_h0[:, 0]
        sorted_lifetimes = np.sort(lifetimes)[::-1]

        print(f"    Top 15 longest-lived H0 features (clusters):")
        for k, lt in enumerate(sorted_lifetimes[:15], 1):
            marker = ""
            if k > 1 and sorted_lifetimes[k - 2] / (lt + 1e-12) > 2:
                marker = " <-- gap"
            print(f"      #{k}: lifetime={lt:.4f}{marker}")

        if len(sorted_lifetimes) > 1:
            ratios = sorted_lifetimes[:-1] / (sorted_lifetimes[1:] + 1e-12)
            gap_idx = np.argmax(ratios)
            n_clusters = gap_idx + 1
            print(f"\n    Biggest lifetime gap after feature #{n_clusters}")
            print(f"    Gap ratio: {ratios[gap_idx]:.2f}x")
            print(f"    Estimated number of natural clusters: {n_clusters}")
            if n_clusters == 10:
                print(f"    --> MATCHES b0=10 hypothesis!")
            elif 8 <= n_clusters <= 12:
                print(f"    --> Close to 10 (within +/-2)")
            else:
                print(f"    --> Does NOT match b0=10 (got {n_clusters})")

    # ── Sweep: components at varying thresholds ──
    print(f"\n  COMPONENT COUNT vs THRESHOLD (epsilon sweep):")
    dist_full = squareform(pdist(fps_sub))
    max_dist = np.percentile(dist_full[dist_full > 0], 95)
    min_dist = np.percentile(dist_full[dist_full > 0], 5)
    sweep_eps = np.linspace(min_dist * 0.5, max_dist * 0.8, 25)

    print(f"    {'epsilon':>10}  {'#comp':>6}  bar")
    print(f"    {'':>10}  {'':>6}  |{'.' * 50}|")

    comp_at_10 = None
    for eps in sweep_eps:
        adj = (dist_full <= eps) & (dist_full > 0)
        n_comp = connected_components(csr_matrix(adj.astype(float)), directed=False)[0]
        bar_len = min(50, int(n_comp / n_global * 50))
        bar = '#' * bar_len
        print(f"    {eps:>10.4f}  {n_comp:>6}  |{bar:<50}|")
        if comp_at_10 is None and n_comp <= 10:
            comp_at_10 = eps

    if comp_at_10 is not None:
        print(f"\n    Epsilon for <=10 components: {comp_at_10:.4f}")

    # ── Step 4: Per-digit PH ──
    print(f"\n[Step 4] Computing per-digit persistent homology (subsampled to 150/digit)...")
    t_pd = time.time()
    digit_results = per_digit_analysis(fps, labels)
    print(f"  Per-digit PH time: {time.time() - t_pd:.1f}s")

    draw_betti_table(digit_results)

    # ── Step 5: Complexity ranking ──
    print(f"\n[Step 5] Ranking digits by topological complexity...")
    draw_complexity_ranking(digit_results)

    # ── Step 6: Centroid distances ──
    print(f"\n[Step 6] Computing inter-digit centroid distances...")
    centroids = {}
    for d in range(10):
        mask = labels == d
        if mask.sum() > 0:
            centroids[d] = fps[mask].mean(axis=0)

    centroid_array = np.array([centroids[d] for d in range(10)])
    centroid_dists = np.zeros((10, 10))
    for i in range(10):
        for j in range(10):
            centroid_dists[i, j] = np.linalg.norm(centroid_array[i] - centroid_array[j])

    draw_centroid_heatmap(centroid_dists)

    pairs = []
    for i in range(10):
        for j in range(i + 1, 10):
            pairs.append((centroid_dists[i, j], i, j))
    pairs.sort()

    print(f"\n  5 CLOSEST digit pairs (most similar tension):")
    for d, i, j in pairs[:5]:
        print(f"    {i}-{j}: {d:.4f}")
    print(f"\n  5 FARTHEST digit pairs (most different tension):")
    for d, i, j in pairs[-5:]:
        print(f"    {i}-{j}: {d:.4f}")

    # ── Step 7: Topology vs confusion ──
    print(f"\n[Step 7] Checking if topology matches confusion patterns...")
    pairs_by_dist, confusion_scores = confusion_topology_match(centroid_dists, fps, labels)
    draw_confusion_topology(pairs_by_dist, confusion_scores)

    # ── Step 8: Dendrogram ──
    print(f"\n{'=' * 75}")
    print(f"  CENTROID DENDROGRAM (average linkage)")
    print(f"{'=' * 75}")

    condensed = pdist(centroid_array)
    Z = linkage(condensed, method='average')

    print(f"\n  {'Step':>4} {'Merge':>30} {'Distance':>10}  Visual")
    print(f"  {'-' * 70}")

    max_merge_dist = Z[:, 2].max()
    bar_width = 40

    clusters = {i: [i] for i in range(10)}
    next_id = 10

    for step in range(len(Z)):
        c1, c2, dist, size = Z[step]
        c1, c2 = int(c1), int(c2)
        members1 = clusters.get(c1, [c1])
        members2 = clusters.get(c2, [c2])
        m1_str = ','.join(str(x) for x in sorted(members1))
        m2_str = ','.join(str(x) for x in sorted(members2))
        merge_str = f"{{{m1_str}}} + {{{m2_str}}}"

        bar_len = int(dist / max_merge_dist * bar_width)
        bar = '=' * bar_len + '|'
        print(f"  {step+1:>4} {merge_str:>30} {dist:>10.4f}  {bar}")

        clusters[next_id] = sorted(members1 + members2)
        next_id += 1

    # ── Step 9: Per-digit intra-class spread ──
    print(f"\n{'=' * 75}")
    print(f"  PER-DIGIT INTRA-CLASS SPREAD (tension space radius)")
    print(f"{'=' * 75}")

    print(f"\n  {'Digit':>5} {'N':>5} {'MeanDist':>10} {'StdDist':>10} {'MaxDist':>10}  bar")
    print(f"  {'-' * 60}")

    spreads = []
    for d in range(10):
        mask = labels == d
        pts = fps[mask]
        if len(pts) < 2:
            continue
        dists_to_cent = np.linalg.norm(pts - centroids[d], axis=1)
        mean_d = dists_to_cent.mean()
        std_d = dists_to_cent.std()
        max_d = dists_to_cent.max()
        spreads.append((d, mean_d, std_d, max_d))

    max_spread = max(s[1] for s in spreads) if spreads else 1
    for d, mean_d, std_d, max_d in spreads:
        bar_len = int(mean_d / max_spread * 40)
        bar = '#' * max(bar_len, 1)
        print(f"  {d:>5} {int((labels == d).sum()):>5} {mean_d:>10.4f} {std_d:>10.4f} {max_d:>10.4f}  {bar}")

    # ── Summary ──
    elapsed = time.time() - t0
    print(f"\n{'=' * 75}")
    print(f"  SUMMARY: H-286 TDA ON TENSION FINGERPRINTS")
    print(f"{'=' * 75}")

    print(f"\n  Model: RepulsionFieldQuad, accuracy={accs[-1]*100:.2f}%")
    print(f"  Fingerprint: 10-dim (per-class tension = std across 4 engines)")
    print(f"  Samples: {len(fps)} ({n_global} used for global PH)")
    print(f"  TDA backend: {'ripser' if USE_RIPSER else 'scipy/MST fallback'}")
    print(f"  Time: {elapsed:.1f}s")

    print(f"\n  KEY FINDINGS:")
    print(f"    Global H0 features: {h0_global['count']}")
    print(f"    Global H1 features: {h1_global.get('count', 0)}")
    print(f"    H0 max persistence: {h0_global['max_pers']:.4f}")
    print(f"    H1 max persistence: {h1_global.get('max_pers', 0):.4f}")

    if digit_results:
        max_h1_digit = max(
            ((d, r['h1']['total_pers']) for d, r in digit_results.items() if r is not None),
            key=lambda x: x[1], default=(None, 0)
        )
        min_h1_digit = min(
            ((d, r['h1']['total_pers']) for d, r in digit_results.items() if r is not None),
            key=lambda x: x[1], default=(None, 0)
        )
        max_h0_digit = max(
            ((d, r['h0']['total_pers']) for d, r in digit_results.items() if r is not None),
            key=lambda x: x[1], default=(None, 0)
        )
        min_h0_digit = min(
            ((d, r['h0']['total_pers']) for d, r in digit_results.items() if r is not None),
            key=lambda x: x[1], default=(None, 0)
        )

        print(f"\n  PER-DIGIT EXTREMES:")
        if max_h0_digit[0] is not None:
            print(f"    Most H0 (spread):   digit {max_h0_digit[0]} (total_pers={max_h0_digit[1]:.2f})")
            print(f"    Least H0 (compact): digit {min_h0_digit[0]} (total_pers={min_h0_digit[1]:.2f})")
        if max_h1_digit[0] is not None:
            print(f"    Most H1 (loopy):    digit {max_h1_digit[0]} (total_pers={max_h1_digit[1]:.2f})")
            print(f"    Least H1 (simple):  digit {min_h1_digit[0]} (total_pers={min_h1_digit[1]:.2f})")

    print(f"\n  HYPOTHESIS TESTS:")
    print(f"    b0~10 (one cluster per digit): see gap analysis in Step 3")
    print(f"    Topology predicts confusion:   see Spearman correlation in Step 7")

    # Quick per-digit H1 complexity interpretation
    print(f"\n  INTERPRETATION:")
    print(f"    - H0: measures how many disconnected clusters exist per digit in tension space")
    print(f"    - H1: measures loops/cycles -- digits with more complex tension topology")
    print(f"    - High H1: the 4 engines create varied disagreement patterns (rich structure)")
    print(f"    - Low H1: engines disagree uniformly (simple, convex cluster)")
    print(f"    - Centroid distance predicts which digits the model may confuse")

    print()


if __name__ == '__main__':
    main()
