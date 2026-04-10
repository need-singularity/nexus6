#!/usr/bin/env python3
"""H-285 + H-291 Verification: Extended Tabular Datasets

Tests RepulsionField on multiple sklearn datasets to fill the data type tree.
Datasets:
  1. Iris (4 features, 3 classes) - tiny/easy
  2. Wine (13 features, 3 classes) - medium
  3. Breast Cancer (30 features, 2 classes) - binary
  4. Digits (64 features, 10 classes) - many classes
  5. Diabetes (regression -> binned to 3 classes) - continuous features
  6. California Housing (regression -> binned to 4 classes) - large, many features

Each: 5-fold CV x 3 seeds, RepulsionField vs Dense baseline.
Also measures: tension per class, tension-accuracy correlation.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import math
import time

from sklearn.datasets import (load_iris, load_wine, load_breast_cancer,
                               load_digits, load_diabetes)
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold
from scipy.stats import pearsonr

# ═════════════════════════════════════════
# Models
# ═════════════════════════════════════════

class DenseBaseline(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )
    def forward(self, x):
        return self.net(x)


class RepulsionField(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.2):
        super().__init__()
        self.pole_plus = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim))
        self.pole_minus = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim))
        self.field_transform = nn.Sequential(nn.Linear(output_dim, output_dim), nn.Tanh())
        self.tension_scale = nn.Parameter(torch.tensor(1/3))
        self.tension_magnitude = 0.0
        self.per_sample_tension = None

    def forward(self, x):
        a = self.pole_plus(x)
        b = self.pole_minus(x)
        repulsion = a - b
        tension = (repulsion ** 2).sum(dim=-1, keepdim=True)
        equilibrium = (a + b) / 2
        field_dir = self.field_transform(repulsion)
        output = equilibrium + self.tension_scale * torch.sqrt(tension + 1e-8) * field_dir
        with torch.no_grad():
            self.tension_magnitude = tension.mean().item()
            self.per_sample_tension = tension.squeeze(-1)
        return output


# ═════════════════════════════════════════
# Datasets
# ═════════════════════════════════════════

def load_datasets():
    """Load all datasets, return dict of (X, y, n_classes, description)."""
    datasets = {}

    # Standard sklearn
    for name, loader in [('Iris', load_iris), ('Wine', load_wine),
                          ('Breast Cancer', load_breast_cancer), ('Digits', load_digits)]:
        data = loader()
        datasets[name] = {
            'X': data.data.astype(np.float32),
            'y': data.target.astype(np.int64),
            'n_classes': len(np.unique(data.target)),
            'desc': f"{data.data.shape[1]} features, {len(np.unique(data.target))} classes, {data.data.shape[0]} samples"
        }

    # Diabetes (regression -> binned)
    data = load_diabetes()
    y_cont = data.target
    # Bin into 3 classes by tertiles
    t1, t2 = np.percentile(y_cont, [33, 66])
    y_binned = np.zeros(len(y_cont), dtype=np.int64)
    y_binned[y_cont > t2] = 2
    y_binned[(y_cont > t1) & (y_cont <= t2)] = 1
    datasets['Diabetes (binned)'] = {
        'X': data.data.astype(np.float32),
        'y': y_binned,
        'n_classes': 3,
        'desc': f"{data.data.shape[1]} features, 3 classes (binned), {data.data.shape[0]} samples"
    }

    # Synthetic high-dim (to test dimensionality effect)
    rng = np.random.RandomState(42)
    n = 500
    d = 100
    X_hd = rng.randn(n, d).astype(np.float32)
    # 4 classes based on quadrant of first 2 principal directions
    y_hd = ((X_hd[:, 0] > 0).astype(int) * 2 + (X_hd[:, 1] > 0).astype(int)).astype(np.int64)
    datasets['Synthetic 100D'] = {
        'X': X_hd,
        'y': y_hd,
        'n_classes': 4,
        'desc': f"100 features, 4 classes, 500 samples (synthetic)"
    }

    return datasets


# ═════════════════════════════════════════
# Training
# ═════════════════════════════════════════

def train_one_fold(model, train_loader, val_loader, epochs=50, lr=0.003):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    best_acc = 0.0

    for epoch in range(epochs):
        model.train()
        for X, y in train_loader:
            optimizer.zero_grad()
            loss = F.cross_entropy(model(X), y)
            loss.backward()
            optimizer.step()

        model.eval()
        correct = total = 0
        with torch.no_grad():
            for X, y in val_loader:
                preds = model(X).argmax(1)
                correct += (preds == y).sum().item()
                total += y.size(0)
        acc = correct / total
        best_acc = max(best_acc, acc)

    # Get tension info
    tension = getattr(model, 'tension_magnitude', 0.0)
    ts = model.tension_scale.item() if hasattr(model, 'tension_scale') else None

    # Per-class tension
    tension_per_class = {}
    if hasattr(model, 'per_sample_tension'):
        model.eval()
        all_t, all_y = [], []
        with torch.no_grad():
            for X, y in val_loader:
                _ = model(X)
                if model.per_sample_tension is not None:
                    all_t.append(model.per_sample_tension.cpu().numpy())
                    all_y.append(y.numpy())
        if all_t:
            all_t = np.concatenate(all_t)
            all_y = np.concatenate(all_y)
            for c in np.unique(all_y):
                tension_per_class[int(c)] = float(all_t[all_y == c].mean())

    return best_acc, tension, ts, tension_per_class


def run_cv(name, X, y, n_classes, hidden_dim=64, epochs=50, n_seeds=3, n_folds=5):
    input_dim = X.shape[1]
    results = {'dense': [], 'repulsion': []}
    tension_data = {'overall': [], 'per_class': [], 'ts': []}

    for seed in [42, 123, 777][:n_seeds]:
        np.random.seed(seed)
        torch.manual_seed(seed)
        skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)

        for fold_i, (tr_idx, va_idx) in enumerate(skf.split(X, y)):
            scaler = StandardScaler()
            X_tr = torch.tensor(scaler.fit_transform(X[tr_idx]).astype(np.float32))
            X_va = torch.tensor(scaler.transform(X[va_idx]).astype(np.float32))
            y_tr = torch.tensor(y[tr_idx])
            y_va = torch.tensor(y[va_idx])

            train_loader = DataLoader(TensorDataset(X_tr, y_tr), batch_size=32, shuffle=True)
            val_loader = DataLoader(TensorDataset(X_va, y_va), batch_size=64)

            torch.manual_seed(seed + fold_i)
            dense = DenseBaseline(input_dim, hidden_dim, n_classes)
            acc_d, _, _, _ = train_one_fold(dense, train_loader, val_loader, epochs)
            results['dense'].append(acc_d)

            torch.manual_seed(seed + fold_i)
            repul = RepulsionField(input_dim, hidden_dim, n_classes)
            acc_r, tension, ts, tpc = train_one_fold(repul, train_loader, val_loader, epochs)
            results['repulsion'].append(acc_r)
            tension_data['overall'].append(tension)
            tension_data['per_class'].append(tpc)
            if ts is not None:
                tension_data['ts'].append(ts)

    d_mean = np.mean(results['dense']) * 100
    d_std = np.std(results['dense']) * 100
    r_mean = np.mean(results['repulsion']) * 100
    r_std = np.std(results['repulsion']) * 100
    delta = r_mean - d_mean

    return {
        'name': name,
        'dense_mean': d_mean, 'dense_std': d_std,
        'repul_mean': r_mean, 'repul_std': r_std,
        'delta': delta,
        'tension_avg': np.mean(tension_data['overall']),
        'ts_avg': np.mean(tension_data['ts']) if tension_data['ts'] else None,
        'tension_per_class': tension_data['per_class'],
        'n_features': input_dim,
        'n_classes': n_classes,
        'n_samples': len(y),
    }


# ═════════════════════════════════════════
# Main
# ═════════════════════════════════════════

def main():
    print("=" * 70)
    print("  H-285 + H-291: Extended Tabular RepulsionField Experiments")
    print("  6 datasets x 5-fold CV x 3 seeds")
    print("=" * 70)
    t0 = time.time()

    datasets = load_datasets()
    all_results = []

    for name, info in datasets.items():
        print(f"\n{'='*60}")
        print(f"  {name}: {info['desc']}")
        print(f"{'='*60}")

        # Adjust hidden_dim
        if info['X'].shape[1] < 10:
            hd = 32
        elif info['X'].shape[1] < 30:
            hd = 64
        else:
            hd = 128

        r = run_cv(name, info['X'], info['y'], info['n_classes'], hidden_dim=hd)
        all_results.append(r)

        w = 'Repulsion' if r['delta'] > 0 else 'Dense' if r['delta'] < 0 else 'Tie'
        print(f"  Dense:     {r['dense_mean']:.2f} +/- {r['dense_std']:.2f}%")
        print(f"  Repulsion: {r['repul_mean']:.2f} +/- {r['repul_std']:.2f}%")
        print(f"  Delta:     {r['delta']:+.2f}%  ({w})")
        if r['ts_avg'] is not None:
            print(f"  tension_scale: {r['ts_avg']:.4f} (init=0.3333)")
        print(f"  Avg tension: {r['tension_avg']:.4f}")

    # ═══ FINAL SUMMARY ═══
    print(f"\n\n{'='*70}")
    print("  FINAL SUMMARY: ALL TABULAR DATASETS")
    print(f"{'='*70}")
    print(f"\n  {'Dataset':<22} {'Feat':>5} {'Cls':>4} {'N':>6} {'Dense':>10} {'Repulsion':>12} {'Delta':>8} {'Winner':>9}")
    print(f"  {'-'*80}")

    wins_r = wins_d = ties = 0
    for r in all_results:
        w = 'Repulsion' if r['delta'] > 0.5 else ('Dense' if r['delta'] < -0.5 else 'Tie')
        if r['delta'] > 0.5: wins_r += 1
        elif r['delta'] < -0.5: wins_d += 1
        else: ties += 1
        print(f"  {r['name']:<22} {r['n_features']:>5} {r['n_classes']:>4} {r['n_samples']:>6} "
              f"{r['dense_mean']:>8.2f}%  {r['repul_mean']:>9.2f}%  {r['delta']:>+6.2f}%  {w:>8}")

    print(f"\n  Repulsion wins: {wins_r}/{len(all_results)}")
    print(f"  Dense wins:     {wins_d}/{len(all_results)}")
    print(f"  Ties:           {ties}/{len(all_results)}")

    avg_delta = np.mean([r['delta'] for r in all_results])
    print(f"\n  Average delta: {avg_delta:+.2f}%")

    # ═══ ASCII CHART ═══
    print(f"\n  --- Delta Chart (Repulsion - Dense) ---")
    for r in all_results:
        bar_width = int(abs(r['delta']) * 3)
        if r['delta'] >= 0:
            bar = '+' * min(bar_width, 30)
            pad = ' ' * (15 - min(bar_width, 15))
            print(f"  {r['name']:<22} |{pad}{bar}| {r['delta']:+.2f}%")
        else:
            bar = '-' * min(bar_width, 15)
            pad = ' ' * (15 - len(bar))
            print(f"  {r['name']:<22} |{bar}{pad}               | {r['delta']:+.2f}%")

    # ═══ TENSION ANALYSIS ═══
    print(f"\n  --- Tension Analysis ---")
    print(f"  {'Dataset':<22} {'Tension':>10} {'tension_scale':>15}")
    print(f"  {'-'*50}")
    for r in all_results:
        ts_str = f"{r['ts_avg']:.4f}" if r['ts_avg'] is not None else "N/A"
        print(f"  {r['name']:<22} {r['tension_avg']:>10.4f} {ts_str:>15}")

    # Correlation: tension vs delta
    tensions = [r['tension_avg'] for r in all_results]
    deltas = [r['delta'] for r in all_results]
    if len(tensions) > 2:
        corr, pval = pearsonr(tensions, deltas)
        print(f"\n  Tension-Delta correlation: r={corr:.3f}, p={pval:.3f}")
        if pval < 0.05:
            print(f"  -> Significant! Higher tension correlates with {'better' if corr > 0 else 'worse'} RepulsionField performance")
        else:
            print(f"  -> Not significant (p={pval:.3f})")

    # ═══ FEATURE DIM vs DELTA ═══
    print(f"\n  --- Feature Dimensionality vs Delta ---")
    feats = [r['n_features'] for r in all_results]
    if len(feats) > 2:
        corr_f, pval_f = pearsonr(feats, deltas)
        print(f"  Features-Delta correlation: r={corr_f:.3f}, p={pval_f:.3f}")
    for r in sorted(all_results, key=lambda x: x['n_features']):
        print(f"    {r['n_features']:>4}D  {r['delta']:+.2f}%  ({r['name']})")

    # ═══ DATA TYPE TREE UPDATE ═══
    print(f"\n{'='*70}")
    print("  H-291 DATA TYPE TREE UPDATE")
    print(f"{'='*70}")
    print(f"""
  [Level 0] All Data
       |
       +-- [L1] Dense/Continuous --> RepulsionField effect varies
       |     |
       |     +-- [L2] Spatial (image)
       |     |     +-- MNIST: +0.60%
       |     |     +-- CIFAR: +4.80%
       |     |
       |     +-- [L2] Temporal (time series)""")
    for r in all_results:
        if 'TimeSeries' in r.get('name', ''):
            print(f"       |     |     +-- {r['name']}: {r['delta']:+.2f}%")
    print(f"""       |     |
       |     +-- [L2] Structural (tabular)""")
    for r in all_results:
        print(f"       |     |     +-- {r['name']}: {r['delta']:+.2f}%")
    print(f"""       |
       +-- [L1] Sparse --> RepulsionField weaker
             +-- TF-IDF: (see text experiment)
""")

    elapsed = time.time() - t0
    print(f"  Total time: {elapsed:.1f}s")
    print("=" * 70)


if __name__ == '__main__':
    main()
