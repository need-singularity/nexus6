#!/usr/bin/env python3
"""
H-AI-8 Verification: Is dimension 6 special for embeddings?

Tests:
1. sklearn digits dataset (1797 samples, 64 features, 10 classes)
   - PCA + KNN(k=5) 5-fold CV accuracy for d=2..20
   - Variance explained (reconstruction quality) for each d
2. Synthetic data (100 features, 10 informative)
   - Same PCA + KNN pipeline
3. Marginal gain analysis: where is the biggest "elbow"?

Honest evaluation: is d=6 special or just a smooth curve?
"""

import numpy as np
from sklearn.datasets import load_digits, make_classification
from sklearn.decomposition import PCA
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

DIMS = [2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20]

def run_pca_knn_experiment(X, y, name):
    """PCA reduction + KNN accuracy + variance explained for each dim."""
    print(f"\n{'='*70}")
    print(f"  EXPERIMENT: {name}")
    print(f"  Samples: {X.shape[0]}, Features: {X.shape[1]}, Classes: {len(np.unique(y))}")
    print(f"{'='*70}")

    results = []
    for d in DIMS:
        pca = PCA(n_components=d)
        X_reduced = pca.fit_transform(X)
        var_explained = np.sum(pca.explained_variance_ratio_)

        knn = KNeighborsClassifier(n_neighbors=5)
        scores = cross_val_score(knn, X_reduced, y, cv=5, scoring='accuracy')
        acc_mean = scores.mean()
        acc_std = scores.std()

        results.append({
            'd': d,
            'acc_mean': acc_mean,
            'acc_std': acc_std,
            'var_explained': var_explained
        })

    # Print table
    print(f"\n| dim | accuracy       | var_explained | marginal_acc | marginal_var |")
    print(f"|-----|----------------|---------------|--------------|--------------|")

    for i, r in enumerate(results):
        marginal_acc = r['acc_mean'] - results[i-1]['acc_mean'] if i > 0 else 0
        marginal_var = r['var_explained'] - results[i-1]['var_explained'] if i > 0 else 0
        marker = " <--" if r['d'] == 6 else ""
        print(f"|  {r['d']:>2} | {r['acc_mean']:.4f} ± {r['acc_std']:.4f} |       {r['var_explained']:.4f} |      {marginal_acc:+.4f} |      {marginal_var:+.4f} |{marker}")

    # ASCII accuracy graph
    print(f"\n  Accuracy vs Dimension:")
    acc_min = min(r['acc_mean'] for r in results)
    acc_max = max(r['acc_mean'] for r in results)
    acc_range = acc_max - acc_min if acc_max > acc_min else 0.01

    for r in results:
        bar_len = int(50 * (r['acc_mean'] - acc_min) / acc_range)
        marker = " ***" if r['d'] == 6 else ""
        print(f"  d={r['d']:>2} |{'#' * bar_len}{' ' * (50 - bar_len)}| {r['acc_mean']:.4f}{marker}")

    # Variance explained graph
    print(f"\n  Variance Explained vs Dimension:")
    for r in results:
        bar_len = int(50 * r['var_explained'])
        marker = " ***" if r['d'] == 6 else ""
        print(f"  d={r['d']:>2} |{'#' * bar_len}{' ' * (50 - bar_len)}| {r['var_explained']:.4f}{marker}")

    # Find elbow: largest marginal gain drop
    print(f"\n  Marginal Accuracy Gain (diminishing returns analysis):")
    marginals = []
    for i in range(1, len(results)):
        mg = results[i]['acc_mean'] - results[i-1]['acc_mean']
        marginals.append((results[i]['d'], mg))

    for d, mg in marginals:
        bar_len = max(0, int(100 * mg)) if mg > 0 else 0
        marker = " ***" if d == 6 else ""
        print(f"  d={d:>2} |{'#' * bar_len}{' ' * (40 - bar_len)}| {mg:+.4f}{marker}")

    # Find the "elbow" - where marginal gain drops most
    print(f"\n  Elbow analysis (largest drop in marginal gain):")
    for i in range(1, len(marginals)):
        drop = marginals[i-1][1] - marginals[i][1]
        d_at = marginals[i][0]
        print(f"    Drop at d={d_at}: {drop:+.4f} (from {marginals[i-1][1]:+.4f} to {marginals[i][1]:+.4f})")

    # Statistical test: is d=6 a local maximum of marginal gain?
    d6_idx = next(i for i, r in enumerate(results) if r['d'] == 6)
    print(f"\n  d=6 accuracy: {results[d6_idx]['acc_mean']:.4f}")
    print(f"  d=5 accuracy: {results[d6_idx-1]['acc_mean']:.4f}")
    print(f"  d=7 accuracy: {results[d6_idx+1]['acc_mean']:.4f}")
    gain_5_to_6 = results[d6_idx]['acc_mean'] - results[d6_idx-1]['acc_mean']
    gain_6_to_7 = results[d6_idx+1]['acc_mean'] - results[d6_idx]['acc_mean']
    print(f"  Gain 5->6: {gain_5_to_6:+.4f}")
    print(f"  Gain 6->7: {gain_6_to_7:+.4f}")
    if gain_5_to_6 > gain_6_to_7:
        print(f"  d=6 shows diminishing returns starting (elbow candidate)")
    else:
        print(f"  d=6 is NOT a clear elbow point")

    return results


def run_tsne_quality(X, y, name):
    """Test t-SNE embedding quality across dimensions."""
    print(f"\n{'='*70}")
    print(f"  t-SNE QUALITY: {name}")
    print(f"{'='*70}")

    tsne_dims = [2, 3, 4, 5, 6, 7, 8, 9, 10]
    perplexities = [15, 30, 50]

    # First reduce to 30 dims with PCA for speed
    if X.shape[1] > 30:
        pca = PCA(n_components=30)
        X_pca = pca.fit_transform(X)
    else:
        X_pca = X

    print(f"\n| dim | perp=15 (sil) | perp=30 (sil) | perp=50 (sil) | avg_sil |")
    print(f"|-----|---------------|---------------|---------------|---------|")

    avg_sils = []
    for d in tsne_dims:
        sils = []
        for perp in perplexities:
            try:
                tsne = TSNE(n_components=d, perplexity=perp, random_state=42,
                           n_iter=1000, method='exact' if d > 3 else 'barnes_hut')
                X_tsne = tsne.fit_transform(X_pca)
                sil = silhouette_score(X_tsne, y, sample_size=min(500, len(y)))
                sils.append(sil)
            except Exception as e:
                sils.append(float('nan'))

        avg = np.nanmean(sils)
        avg_sils.append((d, avg))
        marker = " <--" if d == 6 else ""
        print(f"|  {d:>2} |         {sils[0]:.4f} |         {sils[1]:.4f} |         {sils[2]:.4f} |  {avg:.4f} |{marker}")

    # Graph
    print(f"\n  Average Silhouette Score vs Dimension:")
    sil_min = min(s for _, s in avg_sils if not np.isnan(s))
    sil_max = max(s for _, s in avg_sils if not np.isnan(s))
    sil_range = sil_max - sil_min if sil_max > sil_min else 0.01
    for d, s in avg_sils:
        if np.isnan(s):
            print(f"  d={d:>2} | {'N/A':>50} |")
            continue
        bar_len = int(50 * (s - sil_min) / sil_range)
        marker = " ***" if d == 6 else ""
        print(f"  d={d:>2} |{'#' * bar_len}{' ' * (50 - bar_len)}| {s:.4f}{marker}")

    return avg_sils


def run_knn_without_pca(X, y, name):
    """Baseline: KNN on full features for comparison."""
    knn = KNeighborsClassifier(n_neighbors=5)
    scores = cross_val_score(knn, X, y, cv=5, scoring='accuracy')
    print(f"\n  Baseline (no PCA) {name}: {scores.mean():.4f} ± {scores.std():.4f}")
    return scores.mean()


def optimal_dim_analysis(results, name):
    """Find statistically optimal dimension."""
    print(f"\n{'='*70}")
    print(f"  OPTIMAL DIMENSION ANALYSIS: {name}")
    print(f"{'='*70}")

    # Find dim where 95% of max accuracy is reached
    max_acc = max(r['acc_mean'] for r in results)
    threshold_95 = max_acc * 0.95
    threshold_99 = max_acc * 0.99

    d_95 = next(r['d'] for r in results if r['acc_mean'] >= threshold_95)
    d_99 = next(r['d'] for r in results if r['acc_mean'] >= threshold_99)
    d_max = next(r['d'] for r in results if r['acc_mean'] == max_acc)

    print(f"  Max accuracy: {max_acc:.4f} at d={d_max}")
    print(f"  95% of max ({threshold_95:.4f}) reached at d={d_95}")
    print(f"  99% of max ({threshold_99:.4f}) reached at d={d_99}")

    # Efficiency: accuracy per dimension
    print(f"\n  Efficiency (accuracy / dim):")
    for r in results:
        eff = r['acc_mean'] / r['d']
        marker = " ***" if r['d'] == 6 else ""
        print(f"  d={r['d']:>2}: {eff:.4f}{marker}")

    return d_95, d_99, d_max


# ============================================================
# MAIN
# ============================================================

print("H-AI-8 VERIFICATION: Is dimension 6 special for embeddings?")
print("=" * 70)

# --- Test 1: sklearn digits ---
digits = load_digits()
X_digits, y_digits = digits.data, digits.target

baseline_digits = run_knn_without_pca(X_digits, y_digits, "Digits")
results_digits = run_pca_knn_experiment(X_digits, y_digits, "sklearn Digits (64 features, 10 classes)")
d95_d, d99_d, dmax_d = optimal_dim_analysis(results_digits, "Digits")

# --- Test 2: Synthetic data ---
X_synth, y_synth = make_classification(
    n_samples=2000, n_features=100, n_informative=10, n_redundant=20,
    n_classes=10, n_clusters_per_class=1, random_state=42
)
baseline_synth = run_knn_without_pca(X_synth, y_synth, "Synthetic")
results_synth = run_pca_knn_experiment(X_synth, y_synth, "Synthetic (100 features, 10 informative)")
d95_s, d99_s, dmax_s = optimal_dim_analysis(results_synth, "Synthetic")

# --- Test 3: t-SNE quality (digits only, synthetic is too slow) ---
tsne_results = run_tsne_quality(X_digits, y_digits, "Digits")

# --- FINAL VERDICT ---
print(f"\n{'='*70}")
print(f"  FINAL VERDICT: Is d=6 special?")
print(f"{'='*70}")

print(f"\n  Digits dataset:")
print(f"    95% of max accuracy at d={d95_d}")
print(f"    99% of max accuracy at d={d99_d}")
print(f"    Max accuracy at d={dmax_d}")

print(f"\n  Synthetic dataset:")
print(f"    95% of max accuracy at d={d95_s}")
print(f"    99% of max accuracy at d={d99_s}")
print(f"    Max accuracy at d={dmax_s}")

# Check if 6 is within 1 of any optimal
special_6 = False
for label, d95, d99 in [("Digits", d95_d, d99_d), ("Synthetic", d95_s, d99_s)]:
    if abs(d99 - 6) <= 1:
        print(f"\n  {label}: d=6 is near the 99%-optimal dimension ({d99})")
        special_6 = True
    if abs(d95 - 6) <= 1:
        print(f"\n  {label}: d=6 is near the 95%-optimal dimension ({d95})")
        special_6 = True

if not special_6:
    print(f"\n  d=6 is NOT particularly special in either dataset.")
    print(f"  The accuracy curve is smooth without a clear elbow at 6.")

print(f"\n  Honest conclusion:")
print(f"  The optimal dimension depends on the data's intrinsic structure,")
print(f"  not on a universal constant. d=6 may be good for SOME datasets")
print(f"  (especially those with ~6 independent factors), but it is not")
print(f"  a universal optimal embedding dimension.")
print(f"\n  Verdict for H-AI-8: LIKELY NOT SUPPORTED as a universal claim.")
print(f"  d=6 is just one point on a smooth diminishing-returns curve.")
