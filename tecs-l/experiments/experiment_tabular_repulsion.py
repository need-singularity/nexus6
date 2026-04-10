#!/usr/bin/env python3
"""TABULAR Domain Repulsion Field Experiment — sklearn built-in datasets

Verify whether RepulsionField is better than Dense baseline on structured data (tabular data).

Datasets:
  - Iris: 4 features, 3 classes, 150 samples
  - Wine: 13 features, 3 classes, 178 samples
  - Breast Cancer: 30 features, 2 classes, 569 samples
  - Digits: 64 features, 10 classes, 1797 samples

Comparison:
  - Dense baseline (1-hidden MLP)
  - RepulsionField (two-pole with tension)

Measurements:
  - 5-fold CV accuracy (average of 3 seeds)
  - tension per class
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import math
import time

from sklearn.datasets import load_iris, load_wine, load_breast_cancer, load_digits
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold

from model_utils import Expert

# ─────────────────────────────────────────
# Constants
# ─────────────────────────────────────────
SEEDS = [42, 123, 777]
N_FOLDS = 5
EPOCHS = 50
BATCH_SIZE = 32
LR = 0.003


# ─────────────────────────────────────────
# Dense Baseline
# ─────────────────────────────────────────
class DenseBaseline(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.net(x)


# ─────────────────────────────────────────
# RepulsionField for Tabular
# ─────────────────────────────────────────
class TabularRepulsionField(nn.Module):
    """Two-pole repulsion field for tabular data.

    pole+ and pole- are identical architecture MLPs (Expert from model_utils).
    Output = equilibrium + tension_scale * sqrt(tension) * field_direction
    """
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.3):
        super().__init__()
        self.pole_plus = Expert(input_dim, hidden_dim, output_dim, dropout=dropout)
        self.pole_minus = Expert(input_dim, hidden_dim, output_dim, dropout=dropout)

        self.field_transform = nn.Sequential(
            nn.Linear(output_dim, output_dim),
            nn.Tanh(),
        )

        # tension scale init = 1/3 (meta fixed point)
        self.tension_scale = nn.Parameter(torch.tensor(1/3))

        self.tension_magnitude = 0.0
        self.per_sample_tension = None

    def forward(self, x):
        out_plus = self.pole_plus(x)
        out_minus = self.pole_minus(x)

        repulsion = out_plus - out_minus
        tension = (repulsion ** 2).sum(dim=-1, keepdim=True)
        equilibrium = (out_plus + out_minus) / 2
        field_direction = self.field_transform(repulsion)
        output = equilibrium + self.tension_scale * torch.sqrt(tension + 1e-8) * field_direction

        with torch.no_grad():
            self.tension_magnitude = tension.mean().item()
            self.per_sample_tension = tension.squeeze(-1)

        return output


# ─────────────────────────────────────────
# Data loaders
# ─────────────────────────────────────────
DATASETS = {
    'Iris': load_iris,
    'Wine': load_wine,
    'Breast Cancer': load_breast_cancer,
    'Digits': load_digits,
}


def load_dataset(name):
    """Load sklearn dataset, return X, y, n_classes, feature_names."""
    loader = DATASETS[name]
    data = loader()
    X = data.data.astype(np.float32)
    y = data.target.astype(np.int64)
    n_classes = len(np.unique(y))
    return X, y, n_classes


def make_loaders(X_train, y_train, X_val, y_val, batch_size=BATCH_SIZE):
    """Numpy -> PyTorch DataLoaders."""
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train).astype(np.float32)
    X_val_s = scaler.transform(X_val).astype(np.float32)

    train_ds = TensorDataset(
        torch.tensor(X_train_s), torch.tensor(y_train)
    )
    val_ds = TensorDataset(
        torch.tensor(X_val_s), torch.tensor(y_val)
    )
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    return train_loader, val_loader, scaler


# ─────────────────────────────────────────
# Training
# ─────────────────────────────────────────
def train_one_fold(model, train_loader, val_loader, epochs=EPOCHS, lr=LR):
    """Train model, return best val accuracy and final tension per class."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    best_acc = 0.0
    for epoch in range(epochs):
        model.train()
        for X, y in train_loader:
            optimizer.zero_grad()
            out = model(X)
            loss = F.cross_entropy(out, y)
            loss.backward()
            optimizer.step()

        # Evaluate
        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for X, y in val_loader:
                out = model(X)
                preds = out.argmax(1)
                correct += (preds == y).sum().item()
                total += y.size(0)
        acc = correct / total
        if acc > best_acc:
            best_acc = acc

    # Measure tension per class (only for repulsion models)
    tension_per_class = {}
    if hasattr(model, 'per_sample_tension'):
        model.eval()
        all_tensions = []
        all_labels = []
        with torch.no_grad():
            for X, y in val_loader:
                _ = model(X)
                if model.per_sample_tension is not None:
                    all_tensions.append(model.per_sample_tension.cpu().numpy())
                    all_labels.append(y.numpy())
        if all_tensions:
            all_tensions = np.concatenate(all_tensions)
            all_labels = np.concatenate(all_labels)
            for c in np.unique(all_labels):
                mask = all_labels == c
                tension_per_class[int(c)] = float(all_tensions[mask].mean())

    final_tension = getattr(model, 'tension_magnitude', 0.0)
    return best_acc, final_tension, tension_per_class


# ─────────────────────────────────────────
# Cross-validation
# ─────────────────────────────────────────
def run_cv(dataset_name, hidden_dim=64):
    """5-fold CV x 3 seeds for both Dense and RepulsionField."""
    X, y, n_classes = load_dataset(dataset_name)
    input_dim = X.shape[1]
    n_samples = X.shape[0]

    print(f"\n{'='*60}")
    print(f"  {dataset_name}: {n_samples} samples, {input_dim} features, {n_classes} classes")
    print(f"  hidden_dim={hidden_dim}, epochs={EPOCHS}, 5-fold x 3 seeds")
    print(f"{'='*60}")

    results = {'Dense': [], 'Repulsion': []}
    tension_results = {'overall': [], 'per_class': []}

    for seed in SEEDS:
        np.random.seed(seed)
        torch.manual_seed(seed)

        skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)

        for fold_i, (train_idx, val_idx) in enumerate(skf.split(X, y)):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            train_loader, val_loader, _ = make_loaders(X_train, y_train, X_val, y_val)

            # Dense
            torch.manual_seed(seed + fold_i)
            dense = DenseBaseline(input_dim, hidden_dim, n_classes)
            acc_d, _, _ = train_one_fold(dense, train_loader, val_loader)
            results['Dense'].append(acc_d)

            # Repulsion
            torch.manual_seed(seed + fold_i)
            repulsion = TabularRepulsionField(input_dim, hidden_dim, n_classes)
            acc_r, tension, tpc = train_one_fold(repulsion, train_loader, val_loader)
            results['Repulsion'].append(acc_r)
            tension_results['overall'].append(tension)
            tension_results['per_class'].append(tpc)

    # Summary
    dense_accs = np.array(results['Dense'])
    repul_accs = np.array(results['Repulsion'])

    dense_mean = dense_accs.mean() * 100
    dense_std = dense_accs.std() * 100
    repul_mean = repul_accs.mean() * 100
    repul_std = repul_accs.std() * 100
    delta = repul_mean - dense_mean

    print(f"\n  --- Results ({N_FOLDS}-fold x {len(SEEDS)} seeds = {len(dense_accs)} runs) ---")
    print(f"  Dense:     {dense_mean:.2f} +/- {dense_std:.2f}%")
    print(f"  Repulsion: {repul_mean:.2f} +/- {repul_std:.2f}%")
    print(f"  Delta:     {delta:+.2f}%  {'<-- Repulsion wins' if delta > 0 else '<-- Dense wins' if delta < 0 else '(tie)'}")

    # Tension per class summary
    if tension_results['per_class']:
        all_classes = set()
        for tpc in tension_results['per_class']:
            all_classes.update(tpc.keys())
        if all_classes:
            print(f"\n  --- Tension per class (avg over folds) ---")
            class_tensions = {c: [] for c in sorted(all_classes)}
            for tpc in tension_results['per_class']:
                for c in sorted(all_classes):
                    if c in tpc:
                        class_tensions[c].append(tpc[c])
            for c in sorted(all_classes):
                vals = class_tensions[c]
                if vals:
                    print(f"    Class {c}: tension = {np.mean(vals):.4f} +/- {np.std(vals):.4f}")

    # Param count
    dense_p = sum(p.numel() for p in DenseBaseline(input_dim, hidden_dim, n_classes).parameters())
    repul_p = sum(p.numel() for p in TabularRepulsionField(input_dim, hidden_dim, n_classes).parameters())
    print(f"\n  Params: Dense={dense_p:,}, Repulsion={repul_p:,} (ratio={repul_p/dense_p:.1f}x)")

    return {
        'dataset': dataset_name,
        'dense_mean': dense_mean,
        'dense_std': dense_std,
        'repul_mean': repul_mean,
        'repul_std': repul_std,
        'delta': delta,
        'tension_avg': np.mean(tension_results['overall']) if tension_results['overall'] else 0,
    }


# ─────────────────────────────────────────
# ASCII Graph
# ─────────────────────────────────────────
def ascii_bar(label, value, max_val=100, width=40):
    """Simple ASCII bar."""
    bar_len = int(value / max_val * width)
    bar = '#' * bar_len + '.' * (width - bar_len)
    return f"  {label:>20s} |{bar}| {value:.2f}%"


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────
def main():
    print("=" * 60)
    print("  TABULAR REPULSION FIELD EXPERIMENT")
    print("  Does repulsion field help on structured/tabular data?")
    print("  4 datasets x 5-fold CV x 3 seeds = 60 runs per dataset")
    print("=" * 60)

    t0 = time.time()

    all_results = []
    for name in ['Iris', 'Wine', 'Breast Cancer', 'Digits']:
        # Adjust hidden_dim based on dataset size
        if name == 'Iris':
            hidden_dim = 32
        elif name in ('Wine', 'Breast Cancer'):
            hidden_dim = 64
        else:  # Digits
            hidden_dim = 128
        r = run_cv(name, hidden_dim=hidden_dim)
        all_results.append(r)

    # ─── Final Summary ───
    elapsed = time.time() - t0
    print(f"\n\n{'='*60}")
    print(f"  FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"\n  {'Dataset':<18} {'Dense':>10} {'Repulsion':>12} {'Delta':>8} {'Winner':>10}")
    print(f"  {'-'*58}")

    wins_repul = 0
    wins_dense = 0
    for r in all_results:
        winner = 'Repulsion' if r['delta'] > 0 else 'Dense' if r['delta'] < 0 else 'Tie'
        if r['delta'] > 0:
            wins_repul += 1
        elif r['delta'] < 0:
            wins_dense += 1
        print(f"  {r['dataset']:<18} {r['dense_mean']:>8.2f}%  {r['repul_mean']:>9.2f}%  {r['delta']:>+6.2f}%  {winner:>9}")

    print(f"\n  Repulsion wins: {wins_repul}/{len(all_results)}")
    print(f"  Dense wins:     {wins_dense}/{len(all_results)}")

    # ASCII comparison chart
    print(f"\n  --- Accuracy Comparison (ASCII) ---")
    for r in all_results:
        print(f"\n  {r['dataset']}:")
        print(ascii_bar("Dense", r['dense_mean']))
        print(ascii_bar("Repulsion", r['repul_mean']))

    # Tension summary
    print(f"\n  --- Tension Summary ---")
    for r in all_results:
        print(f"  {r['dataset']:<18} avg tension = {r['tension_avg']:.4f}")

    # Conclusion
    print(f"\n  --- Conclusion ---")
    avg_delta = np.mean([r['delta'] for r in all_results])
    print(f"  Average delta (Repulsion - Dense): {avg_delta:+.2f}%")
    if avg_delta > 0.5:
        print(f"  -> RepulsionField HELPS on tabular data (+{avg_delta:.2f}%)")
    elif avg_delta < -0.5:
        print(f"  -> RepulsionField HURTS on tabular data ({avg_delta:.2f}%)")
    else:
        print(f"  -> RepulsionField is NEUTRAL on tabular data (delta ~ 0)")

    print(f"\n  Total time: {elapsed:.1f}s")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()