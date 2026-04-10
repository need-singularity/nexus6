```python
#!/usr/bin/env python3
"""Hypothesis 302: Internal Tension vs Inter Tension x Classification vs Reconstruction — 2x2 Anomaly Detection Experiment

2x2 matrix:
  A) Classification + Internal tension
  B) Classification + Inter tension (mitosis)
  C) Reconstruction + Internal tension
  D) Reconstruction + Inter tension (mitosis)

Dataset: Breast Cancer (sklearn), 5 trials each
Anomaly = malignant, Normal = benign
"""

import sys
import os
import copy
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score


# ─────────────────────────────────────────────────────────
# Model: Simple RepulsionEngine (self-contained)
# ─────────────────────────────────────────────────────────

class RepulsionEngine(nn.Module):
    """Two-pole engine: engine_a and engine_g with tension."""
    def __init__(self, input_dim, hidden_dim=64, output_dim=2):
        super().__init__()
        self.engine_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2), nn.ReLU(),
            nn.Linear(hidden_dim // 2, output_dim)
        )
        self.engine_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2), nn.ReLU(),
            nn.Linear(hidden_dim // 2, output_dim)
        )
        self.eq = nn.Linear(input_dim, output_dim)

    def forward(self, x):
        a = self.engine_a(x)
        g = self.engine_g(x)
        tension = ((a - g) ** 2).mean(dim=-1)
        out = self.eq(x) + 0.3 * (a - g)
        return out, tension

    def internal_tension(self, x):
        """Return per-sample internal tension |a - g|^2."""
        a = self.engine_a(x)
        g = self.engine_g(x)
        return ((a - g) ** 2).mean(dim=-1)


def mitosis(parent, scale=0.01):
    """Split parent into two children with small perturbation."""
    child_a = copy.deepcopy(parent)
    child_b = copy.deepcopy(parent)
    with torch.no_grad():
        for p in child_a.parameters():
            p.add_(torch.randn_like(p) * scale)
        for p in child_b.parameters():
            p.add_(torch.randn_like(p) * scale)
    return child_a, child_b


# ─────────────────────────────────────────────────────────
# Data preparation
# ─────────────────────────────────────────────────────────

def prepare_data():
    """Breast Cancer: benign=normal(0), malignant=anomaly(1)."""
    data = load_breast_cancer()
    X, y = data.data, data.target
    # sklearn: 0=malignant, 1=benign. Flip so malignant=1 (anomaly)
    y_anomaly = 1 - y

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # Full labeled split for classification experiments
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_anomaly, test_size=0.3, random_state=42, stratify=y_anomaly
    )

    # Normal-only subset for reconstruction experiments
    X_train_normal = X_train[y_train == 0]

    return X_train, y_train, X_train_normal, X_test, y_test


# ─────────────────────────────────────────────────────────
# A) Classification + Internal Tension
# ─────────────────────────────────────────────────────────

def experiment_A(X_train, y_train, X_test, y_test, seed):
    """Train on ALL labeled data with CrossEntropy. Score = internal tension."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    input_dim = X_train.shape[1]
    model = RepulsionEngine(input_dim, hidden_dim=64, output_dim=2)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    X_t = torch.FloatTensor(X_train)
    y_t = torch.LongTensor(y_train)

    model.train()
    for ep in range(100):
        opt.zero_grad()
        logits, tension = model(X_t)
        loss = F.cross_entropy(logits, y_t) + 0.01 * tension.mean()
        loss.backward()
        opt.step()

    model.eval()
    with torch.no_grad():
        X_test_t = torch.FloatTensor(X_test)
        scores = model.internal_tension(X_test_t).numpy()

    auroc = roc_auc_score(y_test, scores)
    return auroc


# ─────────────────────────────────────────────────────────
# B) Classification + Inter Tension (Mitosis)
# ─────────────────────────────────────────────────────────

def experiment_B(X_train, y_train, X_test, y_test, seed):
    """Train parent with CE, mitosis -> 2 children, train independently with CE.
    Score = |child_a(x) - child_b(x)|^2."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    input_dim = X_train.shape[1]

    # Train parent
    parent = RepulsionEngine(input_dim, hidden_dim=64, output_dim=2)
    opt = torch.optim.Adam(parent.parameters(), lr=1e-3)

    X_t = torch.FloatTensor(X_train)
    y_t = torch.LongTensor(y_train)

    parent.train()
    for ep in range(60):
        opt.zero_grad()
        logits, tension = parent(X_t)
        loss = F.cross_entropy(logits, y_t) + 0.01 * tension.mean()
        loss.backward()
        opt.step()

    # Mitosis
    child_a, child_b = mitosis(parent, scale=0.01)

    # Train children independently on different halves
    perm = torch.randperm(len(X_t))
    half = len(perm) // 2
    idx_a, idx_b = perm[:half], perm[half:]

    opt_a = torch.optim.Adam(child_a.parameters(), lr=5e-4)
    opt_b = torch.optim.Adam(child_b.parameters(), lr=5e-4)

    for ep in range(40):
        child_a.train()
        opt_a.zero_grad()
        logits_a, t_a = child_a(X_t[idx_a])
        loss_a = F.cross_entropy(logits_a, y_t[idx_a]) + 0.01 * t_a.mean()
        loss_a.backward()
        opt_a.step()

        child_b.train()
        opt_b.zero_grad()
        logits_b, t_b = child_b(X_t[idx_b])
        loss_b = F.cross_entropy(logits_b, y_t[idx_b]) + 0.01 * t_b.mean()
        loss_b.backward()
        opt_b.step()

    # Evaluate: inter tension = |output_a - output_b|^2
    child_a.eval()
    child_b.eval()
    with torch.no_grad():
        X_test_t = torch.FloatTensor(X_test)
        out_a, _ = child_a(X_test_t)
        out_b, _ = child_b(X_test_t)
        inter_tension = ((out_a - out_b) ** 2).mean(dim=-1).numpy()

    auroc = roc_auc_score(y_test, inter_tension)
    return auroc


# ─────────────────────────────────────────────────────────
# C) Reconstruction + Internal Tension
# ─────────────────────────────────────────────────────────

def experiment_C(X_train_normal, X_test, y_test, seed):
    """Train on NORMAL only with MSE (autoencoder). Score = internal tension."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    input_dim = X_train_normal.shape[1]
    # output_dim = input_dim for reconstruction
    model = RepulsionEngine(input_dim, hidden_dim=64, output_dim=input_dim)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    X_t = torch.FloatTensor(X_train_normal)

    model.train()
    for ep in range(150):
        opt.zero_grad()
        recon, tension = model(X_t)
        loss = F.mse_loss(recon, X_t) + 0.01 * tension.mean()
        loss.backward()
        opt.step()

    model.eval()
    with torch.no_grad():
        X_test_t = torch.FloatTensor(X_test)
        scores = model.internal_tension(X_test_t).numpy()

    auroc = roc_auc_score(y_test, scores)
    return auroc


# ─────────────────────────────────────────────────────────
# D) Reconstruction + Inter Tension (Mitosis)
# ─────────────────────────────────────────────────────────

def experiment_D(X_train_normal, X_test, y_test, seed):
    """Train parent MSE on normal, mitosis, train children MSE independently.
    Score = |child_a(x) - child_b(x)|^2."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    input_dim = X_train_normal.shape[1]
    parent = RepulsionEngine(input_dim, hidden_dim=64, output_dim=input_dim)
    opt = torch.optim.Adam(parent.parameters(), lr=1e-3)

    X_t = torch.FloatTensor(X_train_normal)

    # Train parent on normal data
    parent.train()
    for ep in range(80):
        opt.zero_grad()
        recon, tension = parent(X_t)
        loss = F.mse_loss(recon, X_t) + 0.01 * tension.mean()
        loss.backward()
        opt.step()

    # Mitosis
    child_a, child_b = mitosis(parent, scale=0.01)

    # Train children on different halves of normal data
    perm = torch.randperm(len(X_t))
    half = len(perm) // 2
    batch_a = X_t[perm[:half]]
    batch_b = X_t[perm[half:]]

    opt_a = torch.optim.Adam(child_a.parameters(), lr=5e-4)
    opt_b = torch.optim.Adam(child_b.parameters(), lr=5e-4)

    for ep in range(50):
        child_a.train()
        opt_a.zero_grad()
        out_a, t_a = child_a(batch_a)
        loss_a = F.mse_loss(out_a, batch_a) + 0.01 * t_a.mean()
        loss_a.backward()
        opt_a.step()

        child_b.train()
        opt_b.zero_grad()
        out_b, t_b = child_b(batch_b)
        loss_b = F.mse_loss(out_b, batch_b) + 0.01 * t_b.mean()
        loss_b.backward()
        opt_b.step()

    # Evaluate: inter tension
    child_a.eval()
    child_b.eval()
    with torch.no_grad():
        X_test_t = torch.FloatTensor(X_test)
        out_a, _ = child_a(X_test_t)
        out_b, _ = child_b(X_test_t)
        inter_tension = ((out_a - out_b) ** 2).mean(dim=-1).numpy()

    auroc = roc_auc_score(y_test, inter_tension)
    return auroc


# ─────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  H-302: 2x2 Anomaly Detection Experiment")
    print("  Internal vs Inter Tension x Classification vs Reconstruction")
    print("=" * 70)

    X_train, y_train, X_train_normal, X_test, y_test = prepare_data()

    print(f"\n  Dataset: Breast Cancer (sklearn)")
    print(f"  Train (labeled): {len(X_train)}  (normal: {(y_train==0).sum()}, anomaly: {(y_train==1).sum()})")
    print(f"  Train (normal only): {len(X_train_normal)}")
    print(f"  Test: {len(X_test)}  (normal: {(y_test==0).sum()}, anomaly: {(y_test==1).sum()})")
    print(f"  Anomaly ratio (test): {y_test.mean():.1%}")
    print(f"  Trials: 5\n")

    n_trials = 5
    results = {
        'A': [],  # Classification + Internal
        'B': [],  # Classification + Inter
        'C': [],  # Reconstruction + Internal
        'D': [],  # Reconstruction + Inter
    }

    for trial in range(n_trials):
        seed = 42 + trial
        print(f"  Trial {trial+1}/{n_trials} (seed={seed})...", end="", flush=True)

        a = experiment_A(X_train, y_train, X_test, y_test, seed)
        b = experiment_B(X_train, y_train, X_test, y_test, seed)
        c = experiment_C(X_train_normal, X_test, y_test, seed)
        d = experiment_D(X_train_normal, X_test, y_test, seed)

        results['A'].append(a)
        results['B'].append(b)
        results['C'].append(c)
        results['D'].append(d)

        print(f"  A={a:.4f}  B={b:.4f}  C={c:.4f}  D={d:.4f}")

    # ─────────────────────────────────────────────────────
    # 2x2 Matrix
    # ─────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  2x2 AUROC Matrix (mean +/- std over 5 trials)")
    print("=" * 70)

    labels = {
        'A': 'Classif + Internal',
        'B': 'Classif + Inter',
        'C': 'Recon + Internal',
        'D': 'Recon + Inter',
    }

    means = {k: np.mean(v) for k, v in results.items()}
    stds = {k: np.std(v) for k, v in results.items()}

    print(f"\n  {'':>22} | {'Internal Tension':>20} | {'Inter Tension':>20}")
    print(f"  {'-'*22}+{'-'*22}+{'-'*22}")
    print(f"  {'Classification (CE)':>22} | {means['A']:>8.4f} +/- {stds['A']:.4f}   | {means['B']:>8.4f} +/- {stds['B']:.4f}")
    print(f"  {'Reconstruction (MSE)':>22} | {means['C']:>8.4f} +/- {stds['C']:.4f}   | {means['D']:>8.4f} +/- {stds['D']:.4f}")

    # ─────────────────────────────────────────────────────
    # Per-trial detail table
    # ─────────────────────────────────────────────────────
    print(f"\n  Per-trial AUROC:")
    print(f"  {'Trial':>7} | {'A (Cls+Int)':>12} | {'B (Cls+Inter)':>14} | {'C (Rec+Int)':>12} | {'D (Rec+Inter)':>14}")
    print(f"  {'-'*7}-+-{'-'*12}-+-{'-'*14}-+-{'-'*12}-+-{'-'*14}")
    for i in range(n_trials):
        print(f"  {i+1:>7} | {results['A'][i]:>12.4f} | {results['B'][i]:>14.4f} | {results['C'][i]:>12.4f} | {results['D'][i]:>14.4f}")
    print(f"  {'mean':>7} | {means['A']:>12.4f} | {means['B']:>14.4f} | {means['C']:>12.4f} | {means['D']:>14.4f}")
    print(f"  {'std':>7} | {stds['A']:>12.4f} | {stds['B']:>14.4f} | {stds['C']:>12.4f} | {stds['D']:>14.4f}")

    # ─────────────────────────────────────────────────────
    # ASCII Bar Chart
    # ─────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  AUROC Bar Chart (each # = 0.02 AUROC)")
    print(f"{'='*70}\n")

    for k in ['A', 'B', 'C', 'D']:
        m = means[k]
        bar_len = int(m / 0.02)
        bar = '#' * bar_len
        print(f"  {k}) {labels[k]:<22} |{bar}| {m:.4f} +/- {stds[k]:.4f}")

    # ─────────────────────────────────────────────────────
    # Analysis
    # ─────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  Analysis")
    print(f"{'='*70}")

    best_key = max(means, key=means.get)
    worst_key = min(means, key=means.get)

    print(f"\n  Best:  {best_key}) {labels[best_key]} = {means[best_key]:.4f}")
    print(f"  Worst: {worst_key}) {labels[worst_key]} = {means[worst_key]:.4f}")

    # Row analysis (classification vs reconstruction)
    cls_best = max(means['A'], means['B'])
    rec_best = max(means['C'], means['D'])
    print(f"\n  Classification row best: {cls_best:.4f}")
    print(f"  Reconstruction row best: {rec_best:.4f}")
    if cls_best > rec_best:
        print(f"  -> Classification > Reconstruction by {cls_best - rec_best:.4f}")
    else:
        print(f"  -> Reconstruction > Classification by {rec_best - cls_best:.4f}")

    # Column analysis (internal vs inter)
    int_best = max(means['A'], means['C'])
    inter_best = max(means['B'], means['D'])
    print(f"\n  Internal column best: {int_best:.4f}")
    print(f"  Inter column best:    {inter_best:.4f}")
    if int_best > inter_best:
        print(f"  -> Internal > Inter by {int_best - inter_best:.4f}")
    else:
        print(f"  -> Inter > Internal by {inter_best - int_best:.4f}")

    # Interaction effect
    print(f"\n  Interaction check:")
    cls_gap = means['B'] - means['A']
    rec_gap = means['D'] - means['C']
    print(f"    Classification: Inter - Internal = {cls_gap:+.4f}")
    print(f"    Reconstruction: Inter - Internal = {rec_gap:+.4f}")
    if (cls_gap > 0) != (rec_gap > 0):
        print(f"    -> INTERACTION: mitosis effect REVERSES between classification and reconstruction")
    elif abs(cls_gap - rec_gap) > 0.05:
        print(f"    -> INTERACTION: mitosis effect differs by >{abs(cls_gap - rec_gap):.4f}")
    else:
        print(f"    -> No strong interaction (similar gap)")

    # H302 verdict
    print(f"\n  H-302 Verdict:")
    print(f"    H287 reported: Classification + Internal AUROC ~ 1.0")
    print(f"    H296 reported: Reconstruction + Internal AUROC ~ 0.16, Inter ~ 0.81")
    print(f"    This experiment:")
    print(f"      A) Classif + Internal:  {means['A']:.4f}")
    print(f"      B) Classif + Inter:     {means['B']:.4f}")
    print(f"      C) Recon + Internal:    {means['C']:.4f}")
    print(f"      D) Recon + Inter:       {means['D']:.4f}")

    if means['A'] > 0.9 and means['C'] < 0.6:
        print(f"    -> CONFIRMED: Classification internal tension >> Reconstruction internal tension")
        print(f"    -> Learning objective is the dominant factor for internal tension quality")
    elif means['A'] > means['C']:
        print(f"    -> PARTIALLY CONFIRMED: Classification internal > Reconstruction internal")
    else:
        print(f"    -> CONTRADICTED: Reconstruction internal >= Classification internal")

    if means['D'] > means['C']:
        print(f"    -> Mitosis RESCUES reconstruction: Inter({means['D']:.4f}) > Internal({means['C']:.4f})")
    else:
        print(f"    -> Mitosis does NOT rescue reconstruction")

    print(f"\n  Done.")


if __name__ == '__main__':
    main()
```