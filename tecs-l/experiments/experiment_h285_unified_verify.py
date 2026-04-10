#!/usr/bin/env python3
"""H-285 Unified Verification: RepulsionField beyond image classification

Tests:
  1. Tabular (dense): Wine (13F, 3C), Breast Cancer (30F, 2C)
  2. Text (sparse): 20newsgroups TF-IDF (1000-dim)
  3. Text (dense):  20newsgroups CountVectorizer + TruncatedSVD (64-dim)
  4. Time series:   Synthetic sine wave classification (3 classes)

Each: 5-fold CV x 3 seeds, RepulsionField vs Dense baseline.
Measures: accuracy, tension profile per class.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import time

from sklearn.datasets import load_wine, load_breast_cancer, fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold
from scipy.stats import pearsonr


# =============================================
# Models
# =============================================

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
    """Two-pole repulsion field (A vs G poles)."""
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.2):
        super().__init__()
        self.pole_plus = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim))
        self.pole_minus = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim))
        self.field_transform = nn.Sequential(
            nn.Linear(output_dim, output_dim), nn.Tanh())
        self.tension_scale = nn.Parameter(torch.tensor(1.0 / 3.0))
        self.tension_magnitude = 0.0
        self.per_sample_tension = None

    def forward(self, x):
        a = self.pole_plus(x)
        b = self.pole_minus(x)
        repulsion = a - b
        tension = (repulsion ** 2).sum(dim=-1, keepdim=True)
        equilibrium = (a + b) / 2.0
        field_dir = self.field_transform(repulsion)
        output = equilibrium + self.tension_scale * torch.sqrt(tension + 1e-8) * field_dir
        with torch.no_grad():
            self.tension_magnitude = tension.mean().item()
            self.per_sample_tension = tension.squeeze(-1)
        return output


# =============================================
# Training
# =============================================

def train_one_fold(model, train_loader, val_loader, epochs=50, lr=0.003):
    """Train model, return best accuracy and tension info."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    best_acc = 0.0

    for epoch in range(epochs):
        model.train()
        for xb, yb in train_loader:
            optimizer.zero_grad()
            loss = F.cross_entropy(model(xb), yb)
            loss.backward()
            optimizer.step()

        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for xb, yb in val_loader:
                preds = model(xb).argmax(1)
                correct += (preds == yb).sum().item()
                total += yb.size(0)
        acc = correct / total
        if acc > best_acc:
            best_acc = acc

    # Collect tension info
    tension = getattr(model, 'tension_magnitude', 0.0)
    ts_val = model.tension_scale.item() if hasattr(model, 'tension_scale') else None

    # Per-class tension
    tension_per_class = {}
    if hasattr(model, 'per_sample_tension') and model.per_sample_tension is not None:
        model.eval()
        all_t = []
        all_y = []
        with torch.no_grad():
            for xb, yb in val_loader:
                _ = model(xb)
                if model.per_sample_tension is not None:
                    all_t.append(model.per_sample_tension.cpu().numpy())
                    all_y.append(yb.numpy())
        if len(all_t) > 0:
            all_t = np.concatenate(all_t)
            all_y = np.concatenate(all_y)
            for c in np.unique(all_y):
                tension_per_class[int(c)] = float(all_t[all_y == c].mean())

    return best_acc, tension, ts_val, tension_per_class


def run_cv(name, X, y, n_classes, hidden_dim=64, epochs=50, n_seeds=3, n_folds=5, lr=0.003):
    """Run cross-validated comparison."""
    input_dim = X.shape[1]
    results = {'dense': [], 'repulsion': []}
    tension_data = {'overall': [], 'per_class': [], 'ts': []}

    seeds = [42, 123, 777][:n_seeds]

    for seed in seeds:
        np.random.seed(seed)
        torch.manual_seed(seed)
        skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)

        for fold_i, (tr_idx, va_idx) in enumerate(skf.split(X, y)):
            scaler = StandardScaler()
            X_tr = torch.tensor(scaler.fit_transform(X[tr_idx]).astype(np.float32))
            X_va = torch.tensor(scaler.transform(X[va_idx]).astype(np.float32))
            y_tr = torch.tensor(y[tr_idx])
            y_va = torch.tensor(y[va_idx])

            train_loader = DataLoader(
                TensorDataset(X_tr, y_tr), batch_size=32, shuffle=True)
            val_loader = DataLoader(
                TensorDataset(X_va, y_va), batch_size=64)

            # Dense baseline
            torch.manual_seed(seed + fold_i)
            dense_model = DenseBaseline(input_dim, hidden_dim, n_classes)
            acc_d, _, _, _ = train_one_fold(
                dense_model, train_loader, val_loader, epochs, lr)
            results['dense'].append(acc_d)

            # RepulsionField
            torch.manual_seed(seed + fold_i)
            repul_model = RepulsionField(input_dim, hidden_dim, n_classes)
            acc_r, tension, ts, tpc = train_one_fold(
                repul_model, train_loader, val_loader, epochs, lr)
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


# =============================================
# Dataset Loaders
# =============================================

def load_tabular_datasets():
    """Wine + Breast Cancer."""
    datasets = {}
    for dname, loader in [('Wine', load_wine), ('Breast Cancer', load_breast_cancer)]:
        data = loader()
        datasets[dname] = {
            'X': data.data.astype(np.float32),
            'y': data.target.astype(np.int64),
            'n_classes': len(np.unique(data.target)),
            'desc': "{} features, {} classes, {} samples".format(
                data.data.shape[1], len(np.unique(data.target)), data.data.shape[0]),
        }
    return datasets


def load_text_datasets():
    """20newsgroups: TF-IDF (sparse) and CountVectorizer+TruncatedSVD (dense)."""
    cats = ['sci.space', 'rec.sport.baseball', 'comp.graphics', 'talk.politics.guns']
    n_classes = len(cats)

    print("  Loading 20 Newsgroups (4 categories)...")
    all_data = fetch_20newsgroups(
        subset='all', categories=cats,
        remove=('headers', 'footers', 'quotes'))

    X_texts = all_data.data
    y = all_data.target.astype(np.int64)
    print("  Total samples: {}".format(len(X_texts)))

    # TF-IDF (sparse, 1000-dim)
    tfidf = TfidfVectorizer(max_features=1000, stop_words='english')
    X_tfidf = tfidf.fit_transform(X_texts).toarray().astype(np.float32)

    # CountVectorizer + TruncatedSVD (dense, 64-dim)
    count_vec = CountVectorizer(max_features=5000, stop_words='english')
    X_count = count_vec.fit_transform(X_texts)
    svd = TruncatedSVD(n_components=64, random_state=42)
    X_svd = svd.fit_transform(X_count).astype(np.float32)

    datasets = {
        'Text TF-IDF (sparse 1000D)': {
            'X': X_tfidf,
            'y': y,
            'n_classes': n_classes,
            'desc': "1000 TF-IDF features, 4 classes, {} samples".format(len(y)),
        },
        'Text SVD (dense 64D)': {
            'X': X_svd,
            'y': y,
            'n_classes': n_classes,
            'desc': "64 SVD features, 4 classes, {} samples".format(len(y)),
        },
    }
    return datasets


def load_timeseries_dataset():
    """Synthetic sine wave classification: 3 classes based on frequency band."""
    rng = np.random.RandomState(42)
    n_per_class = 200
    seq_len = 64
    t = np.linspace(0, 4 * np.pi, seq_len)

    X_all = []
    y_all = []

    for i in range(n_per_class):
        phase = rng.uniform(0, 2 * np.pi)
        noise = 0.15

        # Class 0: low frequency sine (0.5-1.0 Hz relative)
        freq = rng.uniform(0.5, 1.0)
        w = np.sin(freq * t + phase) + rng.randn(seq_len) * noise
        X_all.append(w)
        y_all.append(0)

        # Class 1: medium frequency sine (1.5-2.5 Hz relative)
        freq = rng.uniform(1.5, 2.5)
        w = np.sin(freq * t + phase) + rng.randn(seq_len) * noise
        X_all.append(w)
        y_all.append(1)

        # Class 2: high frequency sine (3.0-5.0 Hz relative)
        freq = rng.uniform(3.0, 5.0)
        w = np.sin(freq * t + phase) + rng.randn(seq_len) * noise
        X_all.append(w)
        y_all.append(2)

    X = np.array(X_all, dtype=np.float32)
    y = np.array(y_all, dtype=np.int64)

    # Normalize per sample
    xmean = X.mean(axis=1, keepdims=True)
    xstd = X.std(axis=1, keepdims=True) + 1e-8
    X = (X - xmean) / xstd

    # Shuffle
    idx = rng.permutation(len(y))
    X = X[idx]
    y = y[idx]

    datasets = {
        'TimeSeries Sine (3-class)': {
            'X': X,
            'y': y,
            'n_classes': 3,
            'desc': "64 timesteps, 3 freq classes, {} samples".format(len(y)),
        },
    }
    return datasets


# =============================================
# Main
# =============================================

def main():
    print("=" * 70)
    print("  H-285 UNIFIED VERIFICATION")
    print("  RepulsionField (2-pole A vs G) vs Dense Baseline")
    print("  5-fold CV x 3 seeds per dataset")
    print("=" * 70)
    t0 = time.time()

    all_results = []

    # --- 1. Tabular ---
    print("\n" + "=" * 70)
    print("  PART 1: TABULAR DATA (Wine, Breast Cancer)")
    print("=" * 70)

    tabular = load_tabular_datasets()
    for dname, info in tabular.items():
        print("\n  --- {} ---".format(dname))
        print("  {}".format(info['desc']))
        hd = 64 if info['X'].shape[1] < 20 else 128
        r = run_cv(dname, info['X'], info['y'], info['n_classes'],
                   hidden_dim=hd, epochs=50, lr=0.003)
        all_results.append(r)
        winner = 'Repulsion' if r['delta'] > 0 else 'Dense'
        print("  Dense:     {:.2f} +/- {:.2f}%".format(r['dense_mean'], r['dense_std']))
        print("  Repulsion: {:.2f} +/- {:.2f}%".format(r['repul_mean'], r['repul_std']))
        print("  Delta:     {:+.2f}%  ({})".format(r['delta'], winner))
        if r['ts_avg'] is not None:
            print("  tension_scale: {:.4f}".format(r['ts_avg']))
        print("  Avg tension: {:.4f}".format(r['tension_avg']))

    # --- 2. Text ---
    print("\n" + "=" * 70)
    print("  PART 2: TEXT DATA (20newsgroups TF-IDF vs SVD)")
    print("=" * 70)

    text_ds = load_text_datasets()
    for dname, info in text_ds.items():
        print("\n  --- {} ---".format(dname))
        print("  {}".format(info['desc']))
        hd = 128
        r = run_cv(dname, info['X'], info['y'], info['n_classes'],
                   hidden_dim=hd, epochs=30, lr=0.001)
        all_results.append(r)
        winner = 'Repulsion' if r['delta'] > 0 else 'Dense'
        print("  Dense:     {:.2f} +/- {:.2f}%".format(r['dense_mean'], r['dense_std']))
        print("  Repulsion: {:.2f} +/- {:.2f}%".format(r['repul_mean'], r['repul_std']))
        print("  Delta:     {:+.2f}%  ({})".format(r['delta'], winner))
        if r['ts_avg'] is not None:
            print("  tension_scale: {:.4f}".format(r['ts_avg']))
        print("  Avg tension: {:.4f}".format(r['tension_avg']))

    # --- 3. Time Series ---
    print("\n" + "=" * 70)
    print("  PART 3: TIME SERIES (Synthetic Sine)")
    print("=" * 70)

    ts_ds = load_timeseries_dataset()
    for dname, info in ts_ds.items():
        print("\n  --- {} ---".format(dname))
        print("  {}".format(info['desc']))
        r = run_cv(dname, info['X'], info['y'], info['n_classes'],
                   hidden_dim=48, epochs=40, lr=0.003)
        all_results.append(r)
        winner = 'Repulsion' if r['delta'] > 0 else 'Dense'
        print("  Dense:     {:.2f} +/- {:.2f}%".format(r['dense_mean'], r['dense_std']))
        print("  Repulsion: {:.2f} +/- {:.2f}%".format(r['repul_mean'], r['repul_std']))
        print("  Delta:     {:+.2f}%  ({})".format(r['delta'], winner))
        if r['ts_avg'] is not None:
            print("  tension_scale: {:.4f}".format(r['ts_avg']))
        print("  Avg tension: {:.4f}".format(r['tension_avg']))

    # =============================================
    # FINAL SUMMARY
    # =============================================
    print("\n\n" + "=" * 70)
    print("  FINAL SUMMARY: ALL DATA TYPES")
    print("=" * 70)

    header = "  {:<30} {:>5} {:>4} {:>6} {:>10} {:>12} {:>8} {:>9}".format(
        'Dataset', 'Feat', 'Cls', 'N', 'Dense', 'Repulsion', 'Delta', 'Winner')
    print(header)
    print("  " + "-" * 88)

    wins_r = 0
    wins_d = 0
    ties = 0
    for r in all_results:
        if r['delta'] > 0.5:
            w = 'Repulsion'
            wins_r += 1
        elif r['delta'] < -0.5:
            w = 'Dense'
            wins_d += 1
        else:
            w = 'Tie'
            ties += 1
        print("  {:<30} {:>5} {:>4} {:>6} {:>8.2f}%  {:>9.2f}%  {:>+6.2f}%  {:>8}".format(
            r['name'], r['n_features'], r['n_classes'], r['n_samples'],
            r['dense_mean'], r['repul_mean'], r['delta'], w))

    # Add prior image results for context
    print("  " + "-" * 88)
    print("  {:<30} {:>5} {:>4} {:>6} {:>8.2f}%  {:>9.2f}%  {:>+6.2f}%  {:>8}".format(
        'MNIST (prior)', 784, 10, 60000, 97.10, 97.70, 0.60, 'Repulsion'))
    print("  {:<30} {:>5} {:>4} {:>6} {:>8.2f}%  {:>9.2f}%  {:>+6.2f}%  {:>8}".format(
        'CIFAR-10 (prior)', 3072, 10, 50000, 48.20, 53.00, 4.80, 'Repulsion'))

    print("\n  Repulsion wins: {}/{}".format(wins_r, len(all_results)))
    print("  Dense wins:     {}/{}".format(wins_d, len(all_results)))
    print("  Ties:           {}/{}".format(ties, len(all_results)))

    avg_delta = np.mean([r['delta'] for r in all_results])
    print("\n  Average delta (new domains): {:+.2f}%".format(avg_delta))

    # ASCII bar chart
    print("\n  --- Delta Chart (Repulsion - Dense) ---")
    for r in all_results:
        bar_width = int(abs(r['delta']) * 5)
        if r['delta'] >= 0:
            bar = '+' * min(bar_width, 30)
            print("  {:<30} |{:>30}| {:+.2f}%".format(r['name'], bar, r['delta']))
        else:
            bar = '-' * min(bar_width, 30)
            print("  {:<30} |{:<30}| {:+.2f}%".format(r['name'], bar, r['delta']))

    # Tension analysis
    print("\n  --- Tension Analysis ---")
    print("  {:<30} {:>10} {:>15}".format('Dataset', 'Tension', 'tension_scale'))
    print("  " + "-" * 58)
    for r in all_results:
        ts_str = "{:.4f}".format(r['ts_avg']) if r['ts_avg'] is not None else "N/A"
        print("  {:<30} {:>10.4f} {:>15}".format(r['name'], r['tension_avg'], ts_str))

    # Tension-delta correlation
    tensions = [r['tension_avg'] for r in all_results]
    deltas = [r['delta'] for r in all_results]
    if len(tensions) > 2:
        corr, pval = pearsonr(tensions, deltas)
        print("\n  Tension-Delta correlation: r={:.3f}, p={:.3f}".format(corr, pval))

    # Per-class tension profiles
    print("\n  --- Per-Class Tension Profiles (last fold) ---")
    for r in all_results:
        if r['tension_per_class'] and len(r['tension_per_class']) > 0:
            last_tpc = r['tension_per_class'][-1]
            if last_tpc:
                parts = ["c{}={:.3f}".format(c, v) for c, v in sorted(last_tpc.items())]
                print("  {:<30} {}".format(r['name'], '  '.join(parts)))

    # Feature-dim vs delta
    print("\n  --- Feature Dimensionality vs Delta ---")
    feats = [r['n_features'] for r in all_results]
    if len(feats) > 2:
        corr_f, pval_f = pearsonr(feats, deltas)
        print("  Features-Delta correlation: r={:.3f}, p={:.3f}".format(corr_f, pval_f))
    for r in sorted(all_results, key=lambda x: x['n_features']):
        print("    {:>5}D  {:+.2f}%  ({})".format(r['n_features'], r['delta'], r['name']))

    # Data type tree
    print("\n" + "=" * 70)
    print("  H-285 DATA TYPE TREE")
    print("=" * 70)
    print("""
  [All Data]
     |
     +-- [Tabular/Dense]
     |     +-- Wine (13F, 3C):          delta = {:+.2f}%
     |     +-- Breast Cancer (30F, 2C): delta = {:+.2f}%
     |
     +-- [Text]
     |     +-- TF-IDF sparse (1000D):   delta = {:+.2f}%
     |     +-- SVD dense (64D):         delta = {:+.2f}%
     |
     +-- [Time Series]
     |     +-- Sine 3-class (64 steps): delta = {:+.2f}%
     |
     +-- [Image] (prior results)
           +-- MNIST:                   delta = +0.60%
           +-- CIFAR-10:                delta = +4.80%
""".format(
        all_results[0]['delta'], all_results[1]['delta'],
        all_results[2]['delta'], all_results[3]['delta'],
        all_results[4]['delta']))

    elapsed = time.time() - t0
    print("  Total time: {:.1f}s".format(elapsed))
    print("=" * 70)


if __name__ == '__main__':
    main()
