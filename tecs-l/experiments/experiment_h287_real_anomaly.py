#!/usr/bin/env python3
"""H-287: Tension as Anomaly Detector — Real Dataset Validation

Hypothesis: Tension-based anomaly detection achieves high AUROC on real data,
not just synthetic blobs (where it scored 1.0).

Datasets:
  1. make_moons (sklearn) — nonlinear boundary
  2. make_circles (sklearn) — concentric circles
  3. Iris one-class-out (setosa normal, versicolor+virginica anomaly)
  4. Iris reversed (versicolor+virginica normal, setosa anomaly)
  5. Breast Cancer (malignant as anomaly)
  6. Wine (class 0 normal, rest anomaly)

Baselines: Isolation Forest, One-Class SVM, LOF

Method:
  - Train RepulsionFieldAutoencoder on normal class only
  - Compute tension on mixed test set
  - AUROC as metric
  - 5 seeds per dataset
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.datasets import (
    make_moons, make_circles, load_iris, load_breast_cancer, load_wine, load_digits
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor

# ─────────────────────────────────────────
# RepulsionFieldAutoencoder (self-contained)
# ─────────────────────────────────────────

class PoleNetwork(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.net(x)


class RepulsionFieldAutoencoder(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, latent_dim=32):
        super().__init__()
        self.pole_plus = PoleNetwork(input_dim, hidden_dim, latent_dim)
        self.pole_minus = PoleNetwork(input_dim, hidden_dim, latent_dim)
        self.field_transform = nn.Sequential(
            nn.Linear(latent_dim, latent_dim),
            nn.Tanh(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
        )
        self.tension_scale = nn.Parameter(torch.tensor(1.0 / 3.0))
        self.repulsion_weight = 0.1

    def forward(self, x):
        out_plus = self.pole_plus(x)
        out_minus = self.pole_minus(x)
        repulsion = out_plus - out_minus
        tension = (repulsion ** 2).sum(dim=-1, keepdim=True)
        equilibrium = (out_plus + out_minus) / 2.0
        field_direction = self.field_transform(repulsion)
        latent = equilibrium + self.tension_scale * torch.sqrt(tension + 1e-8) * field_direction
        reconstruction = self.decoder(latent)
        return reconstruction, tension.squeeze(-1)

    def compute_loss(self, x):
        recon, tension = self.forward(x)
        recon_loss = F.mse_loss(recon, x)
        tension_reg = tension.mean()
        total_loss = recon_loss + self.repulsion_weight * tension_reg
        return total_loss, recon_loss.item(), tension.mean().item()


# ─────────────────────────────────────────
# Training and scoring
# ─────────────────────────────────────────

def train_model(X_train_normal, input_dim, epochs=150, hidden_dim=64, latent_dim=32,
                lr=1e-3, batch_size=64):
    model = RepulsionFieldAutoencoder(input_dim, hidden_dim, latent_dim)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    X_tensor = torch.FloatTensor(X_train_normal)
    dataset = torch.utils.data.TensorDataset(X_tensor)
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model.train()
    for epoch in range(epochs):
        for (batch,) in loader:
            optimizer.zero_grad()
            loss, _, _ = model.compute_loss(batch)
            loss.backward()
            optimizer.step()

    model.eval()
    return model


def get_anomaly_scores(model, X_test):
    X_tensor = torch.FloatTensor(X_test)
    with torch.no_grad():
        recon, tension = model.forward(X_tensor)
        recon_error = ((X_tensor - recon) ** 2).sum(dim=-1)

    tension = tension.numpy()
    recon_error = recon_error.numpy()

    def normalize(arr):
        mn, mx = arr.min(), arr.max()
        if mx - mn < 1e-12:
            return np.zeros_like(arr)
        return (arr - mn) / (mx - mn)

    combined = 0.5 * normalize(tension) + 0.5 * normalize(recon_error)
    return tension, recon_error, combined


# ─────────────────────────────────────────
# Dataset preparation functions
# ─────────────────────────────────────────

def prepare_moons(n_samples=1000, noise=0.1, seed=42):
    """make_moons: class 0 = normal, class 1 = anomaly."""
    X, y = make_moons(n_samples=n_samples, noise=noise, random_state=seed)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=seed, stratify=y)
    X_train_normal = X_train[y_train == 0]
    return X_train_normal, X_test, y_test, "make_moons"


def prepare_circles(n_samples=1000, noise=0.05, seed=42):
    """make_circles: inner circle = normal, outer = anomaly."""
    X, y = make_circles(n_samples=n_samples, noise=noise, factor=0.3, random_state=seed)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=seed, stratify=y)
    X_train_normal = X_train[y_train == 0]
    return X_train_normal, X_test, y_test, "make_circles"


def prepare_iris_setosa(seed=42):
    """Iris: setosa = normal, others = anomaly."""
    data = load_iris()
    X, y = data.data, data.target
    y_anomaly = (y != 0).astype(int)  # setosa=0 is normal
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X, y_anomaly, test_size=0.3, random_state=seed, stratify=y_anomaly)
    X_train_normal = X_train[y_train == 0]
    return X_train_normal, X_test, y_test, "Iris (setosa=normal)"


def prepare_iris_reversed(seed=42):
    """Iris: versicolor+virginica = normal, setosa = anomaly."""
    data = load_iris()
    X, y = data.data, data.target
    y_anomaly = (y == 0).astype(int)  # setosa=anomaly
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X, y_anomaly, test_size=0.3, random_state=seed, stratify=y_anomaly)
    X_train_normal = X_train[y_train == 0]
    return X_train_normal, X_test, y_test, "Iris (setosa=anomaly)"


def prepare_breast_cancer(seed=42):
    """Breast cancer: benign=normal, malignant=anomaly."""
    data = load_breast_cancer()
    X, y = data.data, data.target
    y_anomaly = 1 - y  # benign=0, malignant=1
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X, y_anomaly, test_size=0.3, random_state=seed, stratify=y_anomaly)
    X_train_normal = X_train[y_train == 0]
    return X_train_normal, X_test, y_test, "Breast Cancer"


def prepare_wine(seed=42):
    """Wine: class 0 = normal, rest = anomaly."""
    data = load_wine()
    X, y = data.data, data.target
    y_anomaly = (y != 0).astype(int)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X, y_anomaly, test_size=0.3, random_state=seed, stratify=y_anomaly)
    X_train_normal = X_train[y_train == 0]
    return X_train_normal, X_test, y_test, "Wine (class0=normal)"


def prepare_digits_0(seed=42):
    """Digits: digit 0 = normal, rest = anomaly (hard: 10% normal)."""
    data = load_digits()
    X, y = data.data, data.target
    y_anomaly = (y != 0).astype(int)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X, y_anomaly, test_size=0.3, random_state=seed, stratify=y_anomaly)
    X_train_normal = X_train[y_train == 0]
    return X_train_normal, X_test, y_test, "Digits (0=normal)"


# ─────────────────────────────────────────
# Baseline methods
# ─────────────────────────────────────────

def run_baselines(X_train_normal, X_test, y_test):
    results = {}

    # Isolation Forest
    clf = IsolationForest(contamination='auto', random_state=42, n_estimators=200)
    clf.fit(X_train_normal)
    scores = -clf.score_samples(X_test)
    results['IForest'] = roc_auc_score(y_test, scores)

    # One-Class SVM
    clf = OneClassSVM(kernel='rbf', gamma='scale', nu=0.1)
    clf.fit(X_train_normal)
    scores = -clf.score_samples(X_test)
    results['OC-SVM'] = roc_auc_score(y_test, scores)

    # LOF (novelty detection mode)
    clf = LocalOutlierFactor(n_neighbors=20, contamination='auto', novelty=True)
    clf.fit(X_train_normal)
    scores = -clf.score_samples(X_test)
    results['LOF'] = roc_auc_score(y_test, scores)

    return results


# ─────────────────────────────────────────
# Main experiment
# ─────────────────────────────────────────

def run_dataset(prepare_fn, n_seeds=5, epochs=150):
    """Run experiment on one dataset with multiple seeds."""
    # Use seed=42 for data prep (consistent splits)
    X_train_normal, X_test, y_test, name = prepare_fn(seed=42)
    input_dim = X_train_normal.shape[1]
    anomaly_ratio = y_test.mean()
    n_normal_train = len(X_train_normal)
    n_test = len(X_test)

    print(f"\n  {'='*65}")
    print(f"  Dataset: {name}")
    print(f"  Train normal: {n_normal_train}, Test: {n_test}, Anomaly ratio: {anomaly_ratio:.1%}")
    print(f"  Input dim: {input_dim}")
    print(f"  {'='*65}")

    # Baselines
    baselines = run_baselines(X_train_normal, X_test, y_test)
    for method, auroc in baselines.items():
        print(f"    {method:<12} AUROC: {auroc:.4f}")

    # Tension-based (multiple seeds)
    tension_aurocs = []
    recon_aurocs = []
    combined_aurocs = []
    tension_stats = []

    for seed in range(n_seeds):
        torch.manual_seed(42 + seed)
        np.random.seed(42 + seed)

        model = train_model(X_train_normal, input_dim, epochs=epochs,
                           hidden_dim=max(32, input_dim), latent_dim=max(16, input_dim // 2))
        tension, recon_error, combined = get_anomaly_scores(model, X_test)

        # Compute stats
        normal_mask = y_test == 0
        anomaly_mask = y_test == 1
        t_normal = tension[normal_mask].mean()
        t_anomaly = tension[anomaly_mask].mean()
        ratio = t_anomaly / (t_normal + 1e-8)

        auroc_t = roc_auc_score(y_test, tension)
        auroc_r = roc_auc_score(y_test, recon_error)
        auroc_c = roc_auc_score(y_test, combined)

        tension_aurocs.append(auroc_t)
        recon_aurocs.append(auroc_r)
        combined_aurocs.append(auroc_c)
        tension_stats.append({'normal': t_normal, 'anomaly': t_anomaly, 'ratio': ratio})

    t_mean, t_std = np.mean(tension_aurocs), np.std(tension_aurocs)
    r_mean, r_std = np.mean(recon_aurocs), np.std(recon_aurocs)
    c_mean, c_std = np.mean(combined_aurocs), np.std(combined_aurocs)

    avg_ratio = np.mean([s['ratio'] for s in tension_stats])
    avg_t_normal = np.mean([s['normal'] for s in tension_stats])
    avg_t_anomaly = np.mean([s['anomaly'] for s in tension_stats])

    print(f"    Tension      AUROC: {t_mean:.4f} +/- {t_std:.4f}")
    print(f"    Recon error  AUROC: {r_mean:.4f} +/- {r_std:.4f}")
    print(f"    Combined     AUROC: {c_mean:.4f} +/- {c_std:.4f}")
    print(f"    Tension normal={avg_t_normal:.4f}, anomaly={avg_t_anomaly:.4f}, ratio={avg_ratio:.1f}x")

    return {
        'name': name,
        'input_dim': input_dim,
        'n_train': n_normal_train,
        'n_test': n_test,
        'anomaly_ratio': anomaly_ratio,
        'baselines': baselines,
        'tension': (t_mean, t_std),
        'recon': (r_mean, r_std),
        'combined': (c_mean, c_std),
        'tension_ratio': avg_ratio,
        't_normal': avg_t_normal,
        't_anomaly': avg_t_anomaly,
    }


def print_summary(results):
    """Print AUROC comparison table."""
    print("\n\n" + "=" * 95)
    print("  H-287: Tension Anomaly Detection — AUROC Summary (5 seeds)")
    print("=" * 95)

    print(f"\n  {'Dataset':<25} {'IForest':>8} {'OC-SVM':>8} {'LOF':>8} "
          f"{'Tension':>14} {'Combined':>14} {'T-ratio':>8}")
    print("  " + "-" * 91)

    for r in results:
        t_str = f"{r['tension'][0]:.4f}+/-{r['tension'][1]:.4f}"
        c_str = f"{r['combined'][0]:.4f}+/-{r['combined'][1]:.4f}"
        print(f"  {r['name']:<25} {r['baselines']['IForest']:>8.4f} "
              f"{r['baselines']['OC-SVM']:>8.4f} {r['baselines']['LOF']:>8.4f} "
              f"{t_str:>14} {c_str:>14} {r['tension_ratio']:>7.1f}x")

    print("  " + "-" * 91)

    # Averages
    avg_if = np.mean([r['baselines']['IForest'] for r in results])
    avg_svm = np.mean([r['baselines']['OC-SVM'] for r in results])
    avg_lof = np.mean([r['baselines']['LOF'] for r in results])
    avg_t = np.mean([r['tension'][0] for r in results])
    avg_c = np.mean([r['combined'][0] for r in results])
    avg_ratio = np.mean([r['tension_ratio'] for r in results])

    print(f"  {'AVERAGE':<25} {avg_if:>8.4f} {avg_svm:>8.4f} {avg_lof:>8.4f} "
          f"{'':>14} {'':>14} {avg_ratio:>7.1f}x")
    print(f"  {'(mean AUROC)':<25} {'':<8} {'':<8} {'':<8} "
          f"{avg_t:>14.4f} {avg_c:>14.4f}")


def print_ascii_chart(results):
    """ASCII bar chart."""
    print("\n\n" + "=" * 80)
    print("  AUROC Bar Chart (each # = 0.02)")
    print("=" * 80)

    for r in results:
        print(f"\n  {r['name']}:")
        methods = [
            ('IForest ', r['baselines']['IForest']),
            ('OC-SVM  ', r['baselines']['OC-SVM']),
            ('LOF     ', r['baselines']['LOF']),
            ('Tension ', r['tension'][0]),
            ('Combined', r['combined'][0]),
        ]
        for label, score in methods:
            bar_len = int(score / 0.02)
            bar = '#' * bar_len
            print(f"    {label} |{bar}| {score:.4f}")


def print_tension_profile(results):
    """Print tension normal/anomaly profile."""
    print("\n\n" + "=" * 80)
    print("  Tension Profile: Normal vs Anomaly")
    print("=" * 80)

    print(f"\n  {'Dataset':<25} {'T(normal)':>10} {'T(anomaly)':>11} {'Ratio':>8} {'AUROC':>8}")
    print("  " + "-" * 65)
    for r in results:
        print(f"  {r['name']:<25} {r['t_normal']:>10.4f} {r['t_anomaly']:>11.4f} "
              f"{r['tension_ratio']:>7.1f}x {r['tension'][0]:>7.4f}")
    print("  " + "-" * 65)

    # ASCII: tension ratio comparison
    print("\n  Tension Ratio (anomaly/normal):")
    for r in results:
        ratio = min(r['tension_ratio'], 50)  # cap for display
        bar_len = int(ratio / 1.0)
        bar = '#' * bar_len
        print(f"    {r['name']:<25} |{bar}| {r['tension_ratio']:.1f}x")


def main():
    print("=" * 80)
    print("  H-287: Tension as Anomaly Detector — Real Dataset Validation")
    print("  Goal: Compare to synthetic AUROC=1.0 baseline")
    print("=" * 80)

    dataset_fns = [
        prepare_moons,
        prepare_circles,
        prepare_iris_setosa,
        prepare_iris_reversed,
        prepare_breast_cancer,
        prepare_wine,
        prepare_digits_0,
    ]

    results = []
    for fn in dataset_fns:
        r = run_dataset(fn, n_seeds=5, epochs=150)
        results.append(r)

    print_summary(results)
    print_ascii_chart(results)
    print_tension_profile(results)

    # ─── Final Analysis ───
    print("\n\n" + "=" * 80)
    print("  FINAL ANALYSIS")
    print("=" * 80)

    # Compare tension vs baselines
    best_baseline_name = 'IForest'
    tension_wins = 0
    combined_wins = 0
    tension_competitive = 0  # within 0.03 of best baseline

    for r in results:
        best_bl = max(r['baselines'].values())
        if r['tension'][0] > best_bl:
            tension_wins += 1
        if r['combined'][0] > best_bl:
            combined_wins += 1
        if best_bl - max(r['tension'][0], r['combined'][0]) < 0.03:
            tension_competitive += 1

    total = len(results)

    print(f"\n  Tension beats all baselines:   {tension_wins}/{total} datasets")
    print(f"  Combined beats all baselines:  {combined_wins}/{total} datasets")
    print(f"  Tension competitive (<0.03):   {tension_competitive}/{total} datasets")

    avg_t = np.mean([r['tension'][0] for r in results])
    avg_c = np.mean([r['combined'][0] for r in results])
    avg_best_bl = np.mean([max(r['baselines'].values()) for r in results])

    print(f"\n  Average AUROC:")
    print(f"    Best baseline:  {avg_best_bl:.4f}")
    print(f"    Tension:        {avg_t:.4f}")
    print(f"    Combined:       {avg_c:.4f}")

    gap = avg_best_bl - max(avg_t, avg_c)

    # Compare to synthetic baseline (AUROC=1.0)
    print(f"\n  vs Synthetic baseline (AUROC=1.0):")
    print(f"    Real data avg:  {max(avg_t, avg_c):.4f}")
    print(f"    Drop:           {1.0 - max(avg_t, avg_c):.4f}")

    # Verdict
    print("\n  " + "-" * 60)
    if max(avg_t, avg_c) >= 0.85 and tension_competitive >= total - 1:
        print("  VERDICT: STRONG SUPPORT")
        print("  Tension is a reliable anomaly detector on real data.")
        print("  H-287 status: confirmed")
    elif max(avg_t, avg_c) >= 0.75 and tension_competitive >= total // 2:
        print("  VERDICT: MODERATE SUPPORT")
        print("  Tension works on real data but not always best.")
        print("  H-287 status: partial")
    elif max(avg_t, avg_c) >= 0.65:
        print("  VERDICT: WEAK SUPPORT")
        print("  Tension has some anomaly detection capability.")
        print("  H-287 status: weak")
    else:
        print("  VERDICT: NOT SUPPORTED")
        print("  Tension does not generalize from synthetic to real data.")
        print("  H-287 status: refuted")

    # Practical recommendation
    print("\n  Practical: tension is best when:")
    good = [r['name'] for r in results if r['tension'][0] > max(r['baselines'].values())]
    bad = [r['name'] for r in results if r['tension'][0] < min(r['baselines'].values())]
    print(f"    Best: {', '.join(good) if good else 'none'}")
    print(f"    Worst: {', '.join(bad) if bad else 'none'}")

    print("\n" + "=" * 80)
    print("  Experiment complete.")
    print("=" * 80)


if __name__ == '__main__':
    main()
