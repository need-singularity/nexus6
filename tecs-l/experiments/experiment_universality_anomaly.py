#!/usr/bin/env python3
"""Universality test: Mitosis inter-tension anomaly detection across 4 datasets.

Compares mitosis inter-tension AUROC vs Isolation Forest and One-Class SVM.
Datasets: Breast Cancer, MNIST (0 vs 1), Iris (setosa vs versicolor), Wine (1 vs 3).
N=2 children, MSE autoencoder, 3 trials each.
"""

import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import copy
from sklearn.datasets import load_breast_cancer, load_iris, load_wine
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

class AutoencoderRepulsion(nn.Module):
    """Simple autoencoder with internal A/G tension."""
    def __init__(self, input_dim, hidden_dim=64, bottleneck=16):
        super().__init__()
        self.engine_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, bottleneck), nn.ReLU(),
            nn.Linear(bottleneck, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
        )
        self.engine_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, bottleneck), nn.ReLU(),
            nn.Linear(bottleneck, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
        )

    def forward(self, x):
        a = self.engine_a(x)
        g = self.engine_g(x)
        out = (a + g) / 2
        tension = ((a - g) ** 2).mean(dim=-1)
        return out, tension


def mitosis(parent, scale=0.01):
    c_a = copy.deepcopy(parent)
    c_b = copy.deepcopy(parent)
    with torch.no_grad():
        for p in c_a.parameters():
            p.add_(torch.randn_like(p) * scale)
        for p in c_b.parameters():
            p.add_(torch.randn_like(p) * scale)
    return c_a, c_b


# ---------------------------------------------------------------------------
# Dataset loaders  (all return X_train_normal, X_test, y_test with 1=anomaly)
# ---------------------------------------------------------------------------

def load_breast_cancer_data():
    data = load_breast_cancer()
    X, y = data.data, data.target  # 1=benign, 0=malignant
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    X_normal = X[y == 1]
    X_anomaly = X[y == 0]
    idx = np.random.permutation(len(X_normal))
    n_train = int(0.7 * len(X_normal))
    X_train = X_normal[idx[:n_train]]
    X_test_n = X_normal[idx[n_train:]]
    X_test = np.vstack([X_test_n, X_anomaly])
    y_test = np.array([0] * len(X_test_n) + [1] * len(X_anomaly))
    return X_train, X_test, y_test, "Breast Cancer"


def load_mnist_01():
    """MNIST digit 0=normal, digit 1=anomaly. Use a small subset."""
    try:
        from sklearn.datasets import fetch_openml
        mnist = fetch_openml('mnist_784', version=1, as_frame=False, parser='auto')
        X_all, y_all = mnist.data, mnist.target.astype(int)
    except Exception:
        # Fallback: generate synthetic "MNIST-like" data
        print("  [MNIST fallback: using synthetic 784-dim data]")
        np.random.seed(999)
        n0, n1 = 800, 200
        X0 = np.random.randn(n0, 784) * 0.3
        X1 = np.random.randn(n1, 784) * 0.3 + 0.5
        X_all = np.vstack([X0, X1])
        y_all = np.array([0] * n0 + [1] * n1)
        scaler = StandardScaler()
        X_all = scaler.fit_transform(X_all)
        X_normal = X_all[y_all == 0]
        X_anomaly = X_all[y_all == 1]
        idx = np.random.permutation(len(X_normal))
        n_train = int(0.7 * len(X_normal))
        X_train = X_normal[idx[:n_train]]
        X_test_n = X_normal[idx[n_train:]]
        X_test = np.vstack([X_test_n, X_anomaly])
        y_test = np.array([0] * len(X_test_n) + [1] * len(X_anomaly))
        return X_train, X_test, y_test, "MNIST(0v1)"

    mask = (y_all == 0) | (y_all == 1)
    X, y = X_all[mask], y_all[mask]
    # Subsample for speed: 1000 normal, 200 anomaly
    idx0 = np.where(y == 0)[0]
    idx1 = np.where(y == 1)[0]
    np.random.shuffle(idx0)
    np.random.shuffle(idx1)
    idx0 = idx0[:1000]
    idx1 = idx1[:200]
    X_normal = X[idx0]
    X_anomaly = X[idx1]
    scaler = StandardScaler()
    X_normal = scaler.fit_transform(X_normal)
    X_anomaly = scaler.transform(X_anomaly)
    idx = np.random.permutation(len(X_normal))
    n_train = int(0.7 * len(X_normal))
    X_train = X_normal[idx[:n_train]]
    X_test_n = X_normal[idx[n_train:]]
    X_test = np.vstack([X_test_n, X_anomaly])
    y_test = np.array([0] * len(X_test_n) + [1] * len(X_anomaly))
    return X_train, X_test, y_test, "MNIST(0v1)"


def load_iris_data():
    data = load_iris()
    X, y = data.data, data.target
    # setosa=0 normal, versicolor=1 anomaly, remove virginica=2
    mask = y != 2
    X, y = X[mask], y[mask]
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    X_normal = X[y == 0]
    X_anomaly = X[y == 1]
    idx = np.random.permutation(len(X_normal))
    n_train = int(0.7 * len(X_normal))
    X_train = X_normal[idx[:n_train]]
    X_test_n = X_normal[idx[n_train:]]
    X_test = np.vstack([X_test_n, X_anomaly])
    y_test = np.array([0] * len(X_test_n) + [1] * len(X_anomaly))
    return X_train, X_test, y_test, "Iris"


def load_wine_data():
    data = load_wine()
    X, y = data.data, data.target
    # class 0 (label 1)=normal, class 2 (label 3)=anomaly
    mask = (y == 0) | (y == 2)
    X, y = X[mask], y[mask]
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    X_normal = X[y == 0]
    X_anomaly = X[y == 2]
    idx = np.random.permutation(len(X_normal))
    n_train = int(0.7 * len(X_normal))
    X_train = X_normal[idx[:n_train]]
    X_test_n = X_normal[idx[n_train:]]
    X_test = np.vstack([X_test_n, X_anomaly])
    y_test = np.array([0] * len(X_test_n) + [1] * len(X_anomaly))
    return X_train, X_test, y_test, "Wine"


# ---------------------------------------------------------------------------
# Mitosis anomaly pipeline
# ---------------------------------------------------------------------------

def run_mitosis_anomaly(X_train, X_test, y_test, parent_epochs=50, child_epochs=30, scale=0.01):
    """Train parent MSE, mitosis, train children, return dict of AUROC scores."""
    input_dim = X_train.shape[1]
    hidden = min(64, max(16, input_dim // 2))
    bottleneck = min(16, max(4, input_dim // 4))

    X_train_t = torch.FloatTensor(X_train)
    X_test_t = torch.FloatTensor(X_test)

    # Train parent
    parent = AutoencoderRepulsion(input_dim, hidden, bottleneck)
    opt = torch.optim.Adam(parent.parameters(), lr=0.001)
    for ep in range(parent_epochs):
        parent.train()
        opt.zero_grad()
        out, _ = parent(X_train_t)
        loss = F.mse_loss(out, X_train_t)
        loss.backward()
        opt.step()

    # Mitosis
    child_a, child_b = mitosis(parent, scale=scale)

    # Train children independently on different mini-batches
    opt_a = torch.optim.Adam(child_a.parameters(), lr=0.001)
    opt_b = torch.optim.Adam(child_b.parameters(), lr=0.001)
    for ep in range(child_epochs):
        child_a.train()
        child_b.train()
        perm = torch.randperm(len(X_train_t))
        half = len(perm) // 2
        batch_a = X_train_t[perm[:half]]
        batch_b = X_train_t[perm[half:]]

        opt_a.zero_grad()
        out_a, _ = child_a(batch_a)
        F.mse_loss(out_a, batch_a).backward()
        opt_a.step()

        opt_b.zero_grad()
        out_b, _ = child_b(batch_b)
        F.mse_loss(out_b, batch_b).backward()
        opt_b.step()

    # Evaluate multiple scores
    child_a.eval()
    child_b.eval()
    with torch.no_grad():
        out_a, tension_a = child_a(X_test_t)
        out_b, tension_b = child_b(X_test_t)

        # Inter-tension: disagreement between children
        inter_tension = ((out_a - out_b) ** 2).mean(dim=-1).numpy()

        # Reconstruction error (average of both children)
        recon_err_a = ((out_a - X_test_t) ** 2).mean(dim=-1).numpy()
        recon_err_b = ((out_b - X_test_t) ** 2).mean(dim=-1).numpy()
        recon_err = (recon_err_a + recon_err_b) / 2

        # Combined: recon_err + inter_tension
        combined = recon_err + inter_tension

    # Compute AUROC, handle inverted scores with max(auroc, 1-auroc) for raw,
    # but also report raw direction
    auroc_inter_raw = roc_auc_score(y_test, inter_tension)
    auroc_recon = roc_auc_score(y_test, recon_err)
    auroc_combined = roc_auc_score(y_test, combined)

    # Direction-corrected: if AUROC < 0.5, the score is anticorrelated, flip it
    auroc_inter_corr = max(auroc_inter_raw, 1 - auroc_inter_raw)

    return {
        'inter_raw': auroc_inter_raw,
        'inter_corr': auroc_inter_corr,
        'recon': auroc_recon,
        'combined': auroc_combined,
    }


# ---------------------------------------------------------------------------
# Baselines
# ---------------------------------------------------------------------------

def run_isolation_forest(X_train, X_test, y_test):
    clf = IsolationForest(n_estimators=100, contamination='auto', random_state=None)
    clf.fit(X_train)
    scores = -clf.decision_function(X_test)  # higher = more anomalous
    return roc_auc_score(y_test, scores)


def run_ocsvm(X_train, X_test, y_test):
    clf = OneClassSVM(kernel='rbf', gamma='scale', nu=0.1)
    clf.fit(X_train)
    scores = -clf.decision_function(X_test)
    return roc_auc_score(y_test, scores)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    N_TRIALS = 3
    PARENT_EP = 50
    CHILD_EP = 30
    SCALE = 0.01

    print("=" * 72)
    print("UNIVERSALITY TEST: Mitosis Inter-Tension Anomaly Detection")
    print(f"  N=2 children | MSE AE | parent {PARENT_EP}ep | child {CHILD_EP}ep | scale {SCALE}")
    print(f"  {N_TRIALS} trials each | Baselines: IsolationForest, One-Class SVM")
    print("=" * 72)

    loaders = [
        load_breast_cancer_data,
        load_mnist_01,
        load_iris_data,
        load_wine_data,
    ]

    all_results = {}  # dataset_name -> {method: [aurocs]}

    for load_fn in loaders:
        print(f"\n{'─' * 60}")
        first_call = load_fn()
        ds_name = first_call[3]
        print(f"Dataset: {ds_name}  (train={first_call[0].shape}, test={first_call[1].shape})")
        print(f"  normal in test: {(first_call[2]==0).sum()}, anomaly in test: {(first_call[2]==1).sum()}")

        results = {
            'MIT-InterRaw': [], 'MIT-InterCorr': [],
            'MIT-Recon': [], 'MIT-Combined': [],
            'IsolationForest': [], 'OneClassSVM': [],
        }

        for trial in range(N_TRIALS):
            np.random.seed(42 + trial * 7)
            torch.manual_seed(42 + trial * 7)
            X_train, X_test, y_test, _ = load_fn()

            # Mitosis inter-tension (returns dict)
            mit_scores = run_mitosis_anomaly(X_train, X_test, y_test,
                                             parent_epochs=PARENT_EP,
                                             child_epochs=CHILD_EP,
                                             scale=SCALE)
            results['MIT-InterRaw'].append(mit_scores['inter_raw'])
            results['MIT-InterCorr'].append(mit_scores['inter_corr'])
            results['MIT-Recon'].append(mit_scores['recon'])
            results['MIT-Combined'].append(mit_scores['combined'])

            # Baselines
            auroc_if = run_isolation_forest(X_train, X_test, y_test)
            results['IsolationForest'].append(auroc_if)

            auroc_svm = run_ocsvm(X_train, X_test, y_test)
            results['OneClassSVM'].append(auroc_svm)

            print(f"  trial {trial+1}: InterRaw={mit_scores['inter_raw']:.4f} "
                  f"Recon={mit_scores['recon']:.4f} Comb={mit_scores['combined']:.4f} "
                  f"IF={auroc_if:.4f} SVM={auroc_svm:.4f}")

        all_results[ds_name] = results

        # Per-dataset summary
        print(f"\n  {'Method':>18} {'Mean':>8} {'Std':>8}")
        print(f"  {'─'*36}")
        for m in results:
            mu = np.mean(results[m])
            sd = np.std(results[m])
            print(f"  {m:>18} {mu:>8.4f} {sd:>8.4f}")

    # ===================================================================
    # Cross-dataset AUROC table
    # ===================================================================
    print("\n" + "=" * 72)
    print("CROSS-DATASET AUROC SUMMARY (mean +/- std over 3 trials)")
    print("=" * 72)

    # For the cross-dataset table, focus on key methods
    key_methods = ['MIT-InterRaw', 'MIT-Recon', 'MIT-Combined', 'IsolationForest', 'OneClassSVM']
    ds_names = list(all_results.keys())

    # Header
    header = f"{'Dataset':>16}"
    for m in key_methods:
        header += f" | {m:>16}"
    print(header)
    print("-" * len(header))

    # Rows
    wins = {m: 0 for m in key_methods}
    for ds in ds_names:
        row = f"{ds:>16}"
        means = {}
        for m in key_methods:
            mu = np.mean(all_results[ds][m])
            sd = np.std(all_results[ds][m])
            means[m] = mu
            row += f" | {mu:>7.4f}+/-{sd:.4f}"
        print(row)
        best_m = max(means, key=means.get)
        wins[best_m] += 1

    print("-" * len(header))
    win_row = f"{'Wins':>16}"
    for m in key_methods:
        win_row += f" | {wins[m]:>16}"
    print(win_row)

    # Direction analysis
    print("\n" + "=" * 72)
    print("INTER-TENSION DIRECTION ANALYSIS")
    print("  Raw AUROC < 0.5 means tension is LOWER for anomalies (inverted)")
    print("=" * 72)
    for ds in ds_names:
        raw_mu = np.mean(all_results[ds]['MIT-InterRaw'])
        corr_mu = np.mean(all_results[ds]['MIT-InterCorr'])
        direction = "NORMAL" if raw_mu >= 0.5 else "INVERTED"
        print(f"  {ds:>16}: raw={raw_mu:.4f}  corr={corr_mu:.4f}  direction={direction}")

    # ===================================================================
    # ASCII bar chart per dataset
    # ===================================================================
    chart_methods = ['MIT-Recon', 'MIT-Combined', 'IsolationForest', 'OneClassSVM']
    print("\n" + "=" * 72)
    print("AUROC BAR CHART (per dataset)")
    print("=" * 72)
    BAR_WIDTH = 40

    for ds in ds_names:
        print(f"\n  {ds}:")
        for m in chart_methods:
            mu = np.mean(all_results[ds][m])
            bar_len = int(mu * BAR_WIDTH)
            bar = '#' * bar_len + '.' * (BAR_WIDTH - bar_len)
            print(f"    {m:>18} |{bar}| {mu:.4f}")

    # ===================================================================
    # Grand summary
    # ===================================================================
    print("\n" + "=" * 72)
    print("GRAND AVERAGE AUROC")
    print("=" * 72)
    for m in key_methods:
        all_vals = []
        for ds in ds_names:
            all_vals.extend(all_results[ds][m])
        grand_mu = np.mean(all_vals)
        grand_sd = np.std(all_vals)
        bar_len = int(grand_mu * BAR_WIDTH)
        bar = '#' * bar_len + '.' * (BAR_WIDTH - bar_len)
        print(f"  {m:>18} |{bar}| {grand_mu:.4f} +/- {grand_sd:.4f}")

    best_mit = max('MIT-Recon', 'MIT-Combined',
                   key=lambda m: np.mean([np.mean(all_results[ds][m]) for ds in ds_names]))
    best_mit_wins = sum(1 for ds in ds_names
                        if np.mean(all_results[ds][best_mit]) == max(
                            np.mean(all_results[ds][m]) for m in key_methods))
    print(f"\n  Best mitosis method: {best_mit}")
    print(f"  IsolationForest wins: {wins['IsolationForest']}/{len(ds_names)}")
    print(f"  OneClassSVM wins: {wins['OneClassSVM']}/{len(ds_names)}")
    print("\nDone.")


if __name__ == '__main__':
    main()
