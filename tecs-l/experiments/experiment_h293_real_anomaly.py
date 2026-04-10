#!/usr/bin/env python3
"""H-293: Tension as Universal Anomaly Score — Real Dataset Experiment

Tests whether RepulsionFieldEngine tension serves as a general anomaly
detector on REAL datasets, compared to Isolation Forest and One-Class SVM.

Datasets:
  1. Breast Cancer (sklearn) — malignant as anomaly (~37%)
  2. Digits (sklearn) — digit 0 normal, rest anomaly
  3. Multivariate Gaussian with planted outliers

Method:
  - Train RepulsionFieldEngine on normal class only (unsupervised)
  - Compute tension on test set (normal + anomaly mixed)
  - Use tension magnitude as anomaly score
  - Measure AUROC
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.datasets import load_breast_cancer, load_digits
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM

from model_utils import Expert, TopKGate, SIGMA, TAU, H_TARGET, DIVISOR_RECIPROCALS

# ─────────────────────────────────────────
# Lightweight RepulsionFieldEngine for tabular data
# (adapted from model_meta_engine.py, smaller dims)
# ─────────────────────────────────────────

class EngineA_Small(nn.Module):
    """sigma,tau-MoE adapted for small input dims."""
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        n_experts = min(SIGMA, 6)  # cap for small data
        k = min(TAU, 2)
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, output_dim),
            ) for _ in range(n_experts)
        ])
        self.gate = nn.Linear(input_dim, n_experts)
        self.k = k
        self.n_experts = n_experts

    def forward(self, x):
        scores = self.gate(x)
        topk_vals, topk_idx = scores.topk(self.k, dim=-1)
        mask = torch.zeros_like(scores)
        mask.scatter_(-1, topk_idx, 1.0)
        weights = F.softmax(scores, dim=-1) * mask
        weights = weights / (weights.sum(dim=-1, keepdim=True) + 1e-8)
        outputs = torch.stack([e(x) for e in self.experts], dim=1)
        return (weights.unsqueeze(-1) * outputs).sum(dim=1)


class EngineG_Small(nn.Module):
    """Shannon entropy MoE for small data."""
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        n_experts = 6
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, output_dim),
            ) for _ in range(n_experts)
        ])
        self.gate = nn.Linear(input_dim, n_experts)
        self.h_target = H_TARGET
        self.entropy_loss = torch.tensor(0.0)

    def forward(self, x):
        weights = F.softmax(self.gate(x), dim=-1)
        outputs = torch.stack([e(x) for e in self.experts], dim=1)
        result = (weights.unsqueeze(-1) * outputs).sum(dim=1)
        h = -(weights * (weights + 1e-8).log()).sum(dim=-1).mean()
        self.entropy_loss = (h - self.h_target) ** 2
        return result


class RepulsionFieldAnomalyDetector(nn.Module):
    """RepulsionFieldEngine adapted for anomaly detection.

    Train on normal data with reconstruction loss.
    At inference, tension = anomaly score.
    """
    def __init__(self, input_dim, hidden_dim=32, latent_dim=16):
        super().__init__()
        self.pole_plus = EngineA_Small(input_dim, hidden_dim, latent_dim)
        self.pole_minus = EngineG_Small(input_dim, hidden_dim, latent_dim)

        self.field_transform = nn.Sequential(
            nn.Linear(latent_dim, latent_dim),
            nn.Tanh(),
        )

        self.tension_scale = nn.Parameter(torch.tensor(1/3))

        # Decoder: reconstruct input from latent
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
        )

    def forward(self, x):
        out_plus = self.pole_plus(x)
        out_minus = self.pole_minus(x)

        repulsion = out_plus - out_minus
        tension = (repulsion ** 2).sum(dim=-1, keepdim=True)  # (batch, 1)

        equilibrium = (out_plus + out_minus) / 2
        field_direction = self.field_transform(repulsion)
        latent = equilibrium + self.tension_scale * torch.sqrt(tension + 1e-8) * field_direction

        reconstruction = self.decoder(latent)

        entropy_loss = getattr(self.pole_minus, 'entropy_loss', torch.tensor(0.0))

        return reconstruction, tension.squeeze(-1), entropy_loss

    def compute_anomaly_score(self, x):
        """Combined anomaly score: tension + reconstruction error."""
        with torch.no_grad():
            recon, tension, _ = self.forward(x)
            recon_error = ((x - recon) ** 2).sum(dim=-1)
            # Normalize both to [0,1] range then combine
            return tension, recon_error


# ─────────────────────────────────────────
# Training
# ─────────────────────────────────────────

def train_repulsion_model(X_train_normal, input_dim, epochs=100, hidden_dim=32,
                          latent_dim=16, lr=1e-3, batch_size=64):
    """Train RepulsionFieldEngine on normal data only."""
    model = RepulsionFieldAnomalyDetector(input_dim, hidden_dim, latent_dim)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    X_tensor = torch.FloatTensor(X_train_normal)
    dataset = torch.utils.data.TensorDataset(X_tensor)
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for (batch,) in loader:
            optimizer.zero_grad()
            recon, tension, entropy_loss = model(batch)

            recon_loss = F.mse_loss(recon, batch)
            # Encourage low tension on normal data
            tension_loss = tension.mean()
            loss = recon_loss + 0.01 * tension_loss + 0.01 * entropy_loss

            loss.backward()
            optimizer.step()
            total_loss += loss.item()

    model.eval()
    return model


def compute_tension_scores(model, X_test):
    """Get anomaly scores from trained model."""
    X_tensor = torch.FloatTensor(X_test)
    with torch.no_grad():
        tension, recon_error = model.compute_anomaly_score(X_tensor)

    tension = tension.numpy()
    recon_error = recon_error.numpy()

    # Normalize each to [0,1]
    def normalize(arr):
        mn, mx = arr.min(), arr.max()
        if mx - mn < 1e-12:
            return np.zeros_like(arr)
        return (arr - mn) / (mx - mn)

    t_norm = normalize(tension)
    r_norm = normalize(recon_error)

    # Combined score
    combined = 0.5 * t_norm + 0.5 * r_norm
    return tension, recon_error, combined


# ─────────────────────────────────────────
# Dataset preparation
# ─────────────────────────────────────────

def prepare_breast_cancer():
    """Breast cancer: benign=normal(0), malignant=anomaly(1)."""
    data = load_breast_cancer()
    X, y = data.data, data.target
    # sklearn: 0=malignant, 1=benign. We want malignant=anomaly=1
    y_anomaly = 1 - y  # flip: benign=0(normal), malignant=1(anomaly)

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_anomaly, test_size=0.3, random_state=42, stratify=y_anomaly
    )

    # Normal training data only
    X_train_normal = X_train[y_train == 0]

    anomaly_ratio = y_test.mean()
    return X_train_normal, X_train, y_train, X_test, y_test, anomaly_ratio, "Breast Cancer"


def prepare_digits(normal_digit=0):
    """Digits: one digit = normal, rest = anomaly."""
    data = load_digits()
    X, y = data.data, data.target

    y_anomaly = (y != normal_digit).astype(int)

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_anomaly, test_size=0.3, random_state=42, stratify=y_anomaly
    )

    X_train_normal = X_train[y_train == 0]

    anomaly_ratio = y_test.mean()
    return X_train_normal, X_train, y_train, X_test, y_test, anomaly_ratio, f"Digits (normal={normal_digit})"


def prepare_gaussian_outliers(n_normal=1000, n_anomaly=100, n_features=20, seed=42):
    """Multivariate Gaussian with planted outliers."""
    rng = np.random.RandomState(seed)

    # Normal: clustered Gaussian
    X_normal = rng.randn(n_normal, n_features) * 1.0

    # Anomaly: shifted + wider Gaussian
    X_anomaly = rng.randn(n_anomaly, n_features) * 3.0 + 3.0

    X = np.vstack([X_normal, X_anomaly])
    y = np.concatenate([np.zeros(n_normal), np.ones(n_anomaly)])

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    X_train_normal = X_train[y_train == 0]

    anomaly_ratio = y_test.mean()
    return X_train_normal, X_train, y_train, X_test, y_test, anomaly_ratio, "Gaussian Outliers"


# ─────────────────────────────────────────
# Baselines
# ─────────────────────────────────────────

def run_isolation_forest(X_train_normal, X_test, y_test):
    """Isolation Forest baseline."""
    clf = IsolationForest(contamination='auto', random_state=42, n_estimators=200)
    clf.fit(X_train_normal)
    scores = -clf.score_samples(X_test)  # higher = more anomalous
    auroc = roc_auc_score(y_test, scores)
    return auroc


def run_ocsvm(X_train_normal, X_test, y_test):
    """One-Class SVM baseline."""
    clf = OneClassSVM(kernel='rbf', gamma='scale', nu=0.1)
    clf.fit(X_train_normal)
    scores = -clf.score_samples(X_test)  # higher = more anomalous
    auroc = roc_auc_score(y_test, scores)
    return auroc


# ─────────────────────────────────────────
# Main experiment
# ─────────────────────────────────────────

def run_experiment(dataset_fn, n_runs=5, epochs=150):
    """Run full experiment on one dataset with multiple seeds."""
    X_train_normal, X_train, y_train, X_test, y_test, anomaly_ratio, name = dataset_fn()
    input_dim = X_train_normal.shape[1]

    print(f"\n{'='*65}")
    print(f"  Dataset: {name}")
    print(f"  Train normal: {len(X_train_normal)}, Test: {len(X_test)}")
    print(f"  Anomaly ratio: {anomaly_ratio:.1%}")
    print(f"{'='*65}")

    # --- Baselines (deterministic-ish) ---
    auroc_iforest = run_isolation_forest(X_train_normal, X_test, y_test)
    auroc_ocsvm = run_ocsvm(X_train_normal, X_test, y_test)

    print(f"  Isolation Forest  AUROC: {auroc_iforest:.4f}")
    print(f"  One-Class SVM     AUROC: {auroc_ocsvm:.4f}")

    # --- Tension-based (multiple runs) ---
    tension_aurocs = []
    recon_aurocs = []
    combined_aurocs = []

    for run in range(n_runs):
        torch.manual_seed(42 + run)
        np.random.seed(42 + run)

        model = train_repulsion_model(
            X_train_normal, input_dim,
            epochs=epochs, hidden_dim=32, latent_dim=16, lr=1e-3
        )

        tension, recon_error, combined = compute_tension_scores(model, X_test)

        auroc_t = roc_auc_score(y_test, tension)
        auroc_r = roc_auc_score(y_test, recon_error)
        auroc_c = roc_auc_score(y_test, combined)

        tension_aurocs.append(auroc_t)
        recon_aurocs.append(auroc_r)
        combined_aurocs.append(auroc_c)

    # Report
    t_mean, t_std = np.mean(tension_aurocs), np.std(tension_aurocs)
    r_mean, r_std = np.mean(recon_aurocs), np.std(recon_aurocs)
    c_mean, c_std = np.mean(combined_aurocs), np.std(combined_aurocs)

    print(f"  Tension only      AUROC: {t_mean:.4f} +/- {t_std:.4f}")
    print(f"  Recon error only  AUROC: {r_mean:.4f} +/- {r_std:.4f}")
    print(f"  Combined (T+R)    AUROC: {c_mean:.4f} +/- {c_std:.4f}")

    return {
        'name': name,
        'anomaly_ratio': anomaly_ratio,
        'iforest': auroc_iforest,
        'ocsvm': auroc_ocsvm,
        'tension': (t_mean, t_std),
        'recon': (r_mean, r_std),
        'combined': (c_mean, c_std),
    }


def print_summary_table(results):
    """Print AUROC comparison table."""
    print("\n")
    print("=" * 80)
    print("  H-293: Tension as Anomaly Score — AUROC Summary")
    print("=" * 80)

    # Header
    print(f"\n{'Dataset':<25} {'IForest':>10} {'OC-SVM':>10} {'Tension':>14} {'Recon':>14} {'Combined':>14}")
    print("-" * 87)

    for r in results:
        t_str = f"{r['tension'][0]:.4f}+/-{r['tension'][1]:.4f}"
        re_str = f"{r['recon'][0]:.4f}+/-{r['recon'][1]:.4f}"
        c_str = f"{r['combined'][0]:.4f}+/-{r['combined'][1]:.4f}"
        print(f"{r['name']:<25} {r['iforest']:>10.4f} {r['ocsvm']:>10.4f} {t_str:>14} {re_str:>14} {c_str:>14}")

    print("-" * 87)

    # Wins count
    print("\n  Best method per dataset:")
    for r in results:
        all_scores = {
            'IForest': r['iforest'],
            'OC-SVM': r['ocsvm'],
            'Tension': r['tension'][0],
            'Recon': r['recon'][0],
            'Combined': r['combined'][0],
        }
        best = max(all_scores, key=all_scores.get)
        print(f"    {r['name']:<25} -> {best} ({all_scores[best]:.4f})")


def print_ascii_bar_chart(results):
    """ASCII bar chart of AUROC per dataset."""
    print("\n")
    print("=" * 80)
    print("  AUROC Bar Chart (each char = 0.02 AUROC)")
    print("=" * 80)

    for r in results:
        print(f"\n  {r['name']}:")
        methods = [
            ('IForest ', r['iforest']),
            ('OC-SVM  ', r['ocsvm']),
            ('Tension ', r['tension'][0]),
            ('Recon   ', r['recon'][0]),
            ('Combined', r['combined'][0]),
        ]

        for label, score in methods:
            bar_len = int(score / 0.02)
            bar = '#' * bar_len
            print(f"    {label} |{bar}| {score:.4f}")


def main():
    print()
    print("=" * 65)
    print("  H-293: Tension as Universal Anomaly Detector")
    print("  RepulsionFieldEngine on Real Datasets")
    print("=" * 65)

    datasets = [
        prepare_breast_cancer,
        lambda: prepare_digits(normal_digit=0),
        prepare_gaussian_outliers,
    ]

    results = []
    for ds_fn in datasets:
        r = run_experiment(ds_fn, n_runs=5, epochs=150)
        results.append(r)

    print_summary_table(results)
    print_ascii_bar_chart(results)

    # Overall analysis
    print("\n" + "=" * 80)
    print("  Analysis")
    print("=" * 80)

    tension_wins = 0
    combined_wins = 0
    total = len(results)

    for r in results:
        best_baseline = max(r['iforest'], r['ocsvm'])
        if r['tension'][0] > best_baseline:
            tension_wins += 1
        if r['combined'][0] > best_baseline:
            combined_wins += 1

    print(f"\n  Tension beats both baselines: {tension_wins}/{total} datasets")
    print(f"  Combined beats both baselines: {combined_wins}/{total} datasets")

    avg_tension = np.mean([r['tension'][0] for r in results])
    avg_iforest = np.mean([r['iforest'] for r in results])
    avg_ocsvm = np.mean([r['ocsvm'] for r in results])
    avg_combined = np.mean([r['combined'][0] for r in results])

    print(f"\n  Average AUROC across datasets:")
    print(f"    Isolation Forest: {avg_iforest:.4f}")
    print(f"    One-Class SVM:    {avg_ocsvm:.4f}")
    print(f"    Tension only:     {avg_tension:.4f}")
    print(f"    Combined (T+R):   {avg_combined:.4f}")

    avg_recon = np.mean([r['recon'][0] for r in results])
    best_baseline = max(avg_iforest, avg_ocsvm)

    print(f"    Recon error only: {avg_recon:.4f}")

    # Check best tension-family score
    best_tension_family = max(avg_tension, avg_recon, avg_combined)
    best_tension_label = 'Tension' if best_tension_family == avg_tension else (
        'Recon' if best_tension_family == avg_recon else 'Combined')

    gap = best_baseline - best_tension_family

    if best_tension_family >= best_baseline:
        print(f"\n  --> Tension-based ({best_tension_label}) BEATS best baseline.")
        print("  --> H-293 SUPPORTED: tension generalizes as anomaly score on real data.")
    elif gap < 0.02:
        print(f"\n  --> Tension-based ({best_tension_label}) within {gap:.4f} of best baseline.")
        print("  --> H-293 PARTIALLY SUPPORTED: competitive but not universally best.")
        print("  --> Neural anomaly detector matches dedicated methods with <2% AUROC gap.")
    elif gap < 0.05:
        print(f"\n  --> Tension-based ({best_tension_label}) within {gap:.4f} of best baseline.")
        print("  --> H-293 WEAKLY SUPPORTED: functional but gap is notable.")
    else:
        print(f"\n  --> Tension-based ({best_tension_label}) trails best baseline by {gap:.4f}.")
        print("  --> H-293 NOT SUPPORTED on these datasets.")

    print()


if __name__ == '__main__':
    main()
