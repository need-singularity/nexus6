#!/usr/bin/env python3
"""H-305: Contrastive Learning + Mitosis Anomaly Detection

Compare 3 learning objectives with inter-child tension (N=2 mitosis):
  A) MSE reconstruction + inter tension (baseline from H302: ~0.80)
  B) Contrastive (NT-Xent) + inter tension
  C) Triplet + inter tension

Dataset: Breast Cancer (sklearn), 5 trials
Anomaly score = inter tension |child_a(x) - child_b(x)|^2
"""

import sys
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
# Model: RepulsionEngine (self-contained)
# ─────────────────────────────────────────────────────────

class RepulsionEngine(nn.Module):
    """Two-pole engine with engine_a, engine_g, eq."""
    def __init__(self, input_dim, hidden_dim=64):
        super().__init__()
        self.engine_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, input_dim)
        )
        self.engine_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, input_dim)
        )
        self.eq = nn.Linear(input_dim, input_dim)

    def forward(self, x):
        a = self.engine_a(x)
        g = self.engine_g(x)
        tension = ((a - g) ** 2).mean(dim=-1)
        out = self.eq(x) + 0.3 * (a - g)
        return out, tension

    def encode(self, x):
        """Return combined representation for contrastive/triplet losses."""
        a = self.engine_a(x)
        g = self.engine_g(x)
        return self.eq(x) + 0.3 * (a - g)


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


def inter_tension_score(child_a, child_b, X):
    """Anomaly score = |child_a(x) - child_b(x)|^2 (inter-child tension)."""
    child_a.eval()
    child_b.eval()
    with torch.no_grad():
        out_a, _ = child_a(X)
        out_b, _ = child_b(X)
        return ((out_a - out_b) ** 2).mean(dim=-1).numpy()


# ─────────────────────────────────────────────────────────
# Data
# ─────────────────────────────────────────────────────────

def prepare_data():
    """Breast Cancer: benign=normal(0), malignant=anomaly(1)."""
    data = load_breast_cancer()
    X, y = data.data, data.target
    y_anomaly = 1 - y  # sklearn: 0=malignant, 1=benign -> flip

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_anomaly, test_size=0.3, random_state=42, stratify=y_anomaly
    )

    # Normal-only for unsupervised training
    X_train_normal = X_train[y_train == 0]

    return X_train, y_train, X_train_normal, X_test, y_test


def augment(x, sigma=0.1):
    """Gaussian noise augmentation."""
    return x + torch.randn_like(x) * sigma


# ─────────────────────────────────────────────────────────
# NT-Xent loss (SimCLR-style)
# ─────────────────────────────────────────────────────────

def nt_xent_loss(z_i, z_j, temperature=0.5):
    """NT-Xent loss for positive pairs (z_i, z_j).
    z_i, z_j: (batch, dim) - representations of two augmented views.
    """
    batch_size = z_i.shape[0]
    z = torch.cat([z_i, z_j], dim=0)  # (2B, dim)
    z = F.normalize(z, dim=1)

    # Similarity matrix (2B x 2B)
    sim = torch.mm(z, z.t()) / temperature  # (2B, 2B)

    # Mask out self-similarity
    mask = torch.eye(2 * batch_size, dtype=torch.bool)
    sim.masked_fill_(mask, -1e9)

    # Positive pairs: (i, i+B) and (i+B, i)
    pos_i = torch.arange(batch_size)
    pos_j = pos_i + batch_size
    labels = torch.cat([pos_j, pos_i], dim=0)  # (2B,)

    loss = F.cross_entropy(sim, labels)
    return loss


# ─────────────────────────────────────────────────────────
# Triplet loss with hardest negative mining
# ─────────────────────────────────────────────────────────

def triplet_loss_hard(anchor, positive, margin=1.0):
    """Triplet loss with hardest negative mining within batch.
    anchor: (B, dim) - original sample encoding
    positive: (B, dim) - augmented sample encoding
    Negative = hardest negative from other anchors in batch.
    """
    anchor_n = F.normalize(anchor, dim=1)
    positive_n = F.normalize(positive, dim=1)

    # Positive distances
    d_pos = ((anchor_n - positive_n) ** 2).sum(dim=1)  # (B,)

    # All pairwise distances among anchors -> find hardest negative
    dist_matrix = torch.cdist(anchor_n, anchor_n, p=2) ** 2  # (B, B)
    # Mask self (set to large value so we don't pick self as negative)
    dist_matrix.fill_diagonal_(1e9)
    # Hardest negative = closest different sample
    d_neg, _ = dist_matrix.min(dim=1)  # (B,)

    loss = F.relu(d_pos - d_neg + margin).mean()
    return loss


# ─────────────────────────────────────────────────────────
# A) MSE Reconstruction + Inter Tension (baseline)
# ─────────────────────────────────────────────────────────

def experiment_A(X_normal, X_test, y_test, seed):
    """MSE reconstruction on normal data -> mitosis -> inter tension."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    input_dim = X_normal.shape[1]
    parent = RepulsionEngine(input_dim)
    opt = torch.optim.Adam(parent.parameters(), lr=1e-3)
    X_t = torch.FloatTensor(X_normal)

    # Train parent
    parent.train()
    for ep in range(80):
        opt.zero_grad()
        recon, tension = parent(X_t)
        loss = F.mse_loss(recon, X_t) + 0.01 * tension.mean()
        loss.backward()
        opt.step()

    # Mitosis
    child_a, child_b = mitosis(parent, scale=0.01)

    # Train children independently on different halves
    perm = torch.randperm(len(X_t))
    half = len(perm) // 2
    batch_a, batch_b = X_t[perm[:half]], X_t[perm[half:]]

    opt_a = torch.optim.Adam(child_a.parameters(), lr=5e-4)
    opt_b = torch.optim.Adam(child_b.parameters(), lr=5e-4)

    for ep in range(30):
        child_a.train()
        opt_a.zero_grad()
        out_a, t_a = child_a(batch_a)
        la = F.mse_loss(out_a, batch_a) + 0.01 * t_a.mean()
        la.backward()
        opt_a.step()

        child_b.train()
        opt_b.zero_grad()
        out_b, t_b = child_b(batch_b)
        lb = F.mse_loss(out_b, batch_b) + 0.01 * t_b.mean()
        lb.backward()
        opt_b.step()

    X_test_t = torch.FloatTensor(X_test)
    scores = inter_tension_score(child_a, child_b, X_test_t)
    return roc_auc_score(y_test, scores)


# ─────────────────────────────────────────────────────────
# B) Contrastive (NT-Xent) + Inter Tension
# ─────────────────────────────────────────────────────────

def experiment_B(X_normal, X_test, y_test, seed):
    """SimCLR-style contrastive on normal data -> mitosis -> inter tension."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    input_dim = X_normal.shape[1]
    parent = RepulsionEngine(input_dim)
    opt = torch.optim.Adam(parent.parameters(), lr=1e-3)
    X_t = torch.FloatTensor(X_normal)

    # Train parent with NT-Xent
    parent.train()
    batch_size = min(128, len(X_t))
    for ep in range(80):
        opt.zero_grad()
        # Sample a batch
        idx = torch.randperm(len(X_t))[:batch_size]
        x_batch = X_t[idx]

        # Two augmented views
        x_i = augment(x_batch, sigma=0.1)
        x_j = augment(x_batch, sigma=0.1)

        z_i = parent.encode(x_i)
        z_j = parent.encode(x_j)

        # Also compute internal tension for regularization
        _, tension = parent(x_batch)

        loss = nt_xent_loss(z_i, z_j, temperature=0.5) + 0.01 * tension.mean()
        loss.backward()
        opt.step()

    # Mitosis
    child_a, child_b = mitosis(parent, scale=0.01)

    # Train children independently with contrastive
    perm = torch.randperm(len(X_t))
    half = len(perm) // 2
    batch_a_data, batch_b_data = X_t[perm[:half]], X_t[perm[half:]]

    opt_a = torch.optim.Adam(child_a.parameters(), lr=5e-4)
    opt_b = torch.optim.Adam(child_b.parameters(), lr=5e-4)

    for ep in range(30):
        # Child A
        child_a.train()
        opt_a.zero_grad()
        bs_a = min(64, len(batch_a_data))
        idx_a = torch.randperm(len(batch_a_data))[:bs_a]
        xa = batch_a_data[idx_a]
        zi_a = child_a.encode(augment(xa, sigma=0.1))
        zj_a = child_a.encode(augment(xa, sigma=0.1))
        _, ta = child_a(xa)
        la = nt_xent_loss(zi_a, zj_a, temperature=0.5) + 0.01 * ta.mean()
        la.backward()
        opt_a.step()

        # Child B
        child_b.train()
        opt_b.zero_grad()
        bs_b = min(64, len(batch_b_data))
        idx_b = torch.randperm(len(batch_b_data))[:bs_b]
        xb = batch_b_data[idx_b]
        zi_b = child_b.encode(augment(xb, sigma=0.1))
        zj_b = child_b.encode(augment(xb, sigma=0.1))
        _, tb = child_b(xb)
        lb = nt_xent_loss(zi_b, zj_b, temperature=0.5) + 0.01 * tb.mean()
        lb.backward()
        opt_b.step()

    X_test_t = torch.FloatTensor(X_test)
    scores = inter_tension_score(child_a, child_b, X_test_t)
    return roc_auc_score(y_test, scores)


# ─────────────────────────────────────────────────────────
# C) Triplet + Inter Tension
# ─────────────────────────────────────────────────────────

def experiment_C(X_normal, X_test, y_test, seed):
    """Triplet loss on normal data -> mitosis -> inter tension."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    input_dim = X_normal.shape[1]
    parent = RepulsionEngine(input_dim)
    opt = torch.optim.Adam(parent.parameters(), lr=1e-3)
    X_t = torch.FloatTensor(X_normal)

    # Train parent with triplet loss
    parent.train()
    batch_size = min(128, len(X_t))
    for ep in range(80):
        opt.zero_grad()
        idx = torch.randperm(len(X_t))[:batch_size]
        x_batch = X_t[idx]

        # Anchor = original, Positive = augmented same sample
        anchor_enc = parent.encode(x_batch)
        positive_enc = parent.encode(augment(x_batch, sigma=0.1))

        _, tension = parent(x_batch)

        loss = triplet_loss_hard(anchor_enc, positive_enc, margin=1.0) + 0.01 * tension.mean()
        loss.backward()
        opt.step()

    # Mitosis
    child_a, child_b = mitosis(parent, scale=0.01)

    # Train children independently with triplet
    perm = torch.randperm(len(X_t))
    half = len(perm) // 2
    batch_a_data, batch_b_data = X_t[perm[:half]], X_t[perm[half:]]

    opt_a = torch.optim.Adam(child_a.parameters(), lr=5e-4)
    opt_b = torch.optim.Adam(child_b.parameters(), lr=5e-4)

    for ep in range(30):
        # Child A
        child_a.train()
        opt_a.zero_grad()
        bs_a = min(64, len(batch_a_data))
        idx_a = torch.randperm(len(batch_a_data))[:bs_a]
        xa = batch_a_data[idx_a]
        anc_a = child_a.encode(xa)
        pos_a = child_a.encode(augment(xa, sigma=0.1))
        _, ta = child_a(xa)
        la = triplet_loss_hard(anc_a, pos_a, margin=1.0) + 0.01 * ta.mean()
        la.backward()
        opt_a.step()

        # Child B
        child_b.train()
        opt_b.zero_grad()
        bs_b = min(64, len(batch_b_data))
        idx_b = torch.randperm(len(batch_b_data))[:bs_b]
        xb = batch_b_data[idx_b]
        anc_b = child_b.encode(xb)
        pos_b = child_b.encode(augment(xb, sigma=0.1))
        _, tb = child_b(xb)
        lb = triplet_loss_hard(anc_b, pos_b, margin=1.0) + 0.01 * tb.mean()
        lb.backward()
        opt_b.step()

    X_test_t = torch.FloatTensor(X_test)
    scores = inter_tension_score(child_a, child_b, X_test_t)
    return roc_auc_score(y_test, scores)


# ─────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  H-305: Contrastive Learning + Mitosis Anomaly Detection")
    print("  MSE vs NT-Xent vs Triplet, all with Inter-Child Tension")
    print("=" * 70)

    X_train, y_train, X_train_normal, X_test, y_test = prepare_data()

    print(f"\n  Dataset: Breast Cancer (sklearn)")
    print(f"  Train (all):    {len(X_train)}  (normal={(y_train==0).sum()}, anomaly={(y_train==1).sum()})")
    print(f"  Train (normal): {len(X_train_normal)}")
    print(f"  Test:           {len(X_test)}  (normal={(y_test==0).sum()}, anomaly={(y_test==1).sum()})")
    print(f"  Anomaly ratio:  {y_test.mean():.1%}")
    print(f"  Trials: 5")
    print(f"\n  Architecture: engine_a,engine_g = Linear({X_train.shape[1]},64)->ReLU->Linear(64,{X_train.shape[1]})")
    print(f"                eq = Linear({X_train.shape[1]},{X_train.shape[1]})")
    print(f"  Parent epochs: 80, Child epochs: 30, Mitosis scale: 0.01")
    print(f"  Augmentation: Gaussian noise sigma=0.1")
    print(f"  NT-Xent temperature: 0.5")
    print(f"  Triplet margin: 1.0")

    n_trials = 5
    results = {'A': [], 'B': [], 'C': []}
    labels = {
        'A': 'MSE Recon + Inter',
        'B': 'NT-Xent + Inter',
        'C': 'Triplet + Inter',
    }

    print(f"\n{'─'*70}")
    print(f"  Running trials...")
    print(f"{'─'*70}")

    for trial in range(n_trials):
        seed = 42 + trial
        print(f"\n  Trial {trial+1}/{n_trials} (seed={seed}):")

        a = experiment_A(X_train_normal, X_test, y_test, seed)
        results['A'].append(a)
        print(f"    A) MSE Recon + Inter:  {a:.4f}")

        b = experiment_B(X_train_normal, X_test, y_test, seed)
        results['B'].append(b)
        print(f"    B) NT-Xent + Inter:    {b:.4f}")

        c = experiment_C(X_train_normal, X_test, y_test, seed)
        results['C'].append(c)
        print(f"    C) Triplet + Inter:    {c:.4f}")

    # ─────────────────────────────────────────────────────
    # Summary statistics
    # ─────────────────────────────────────────────────────
    means = {k: np.mean(v) for k, v in results.items()}
    stds = {k: np.std(v) for k, v in results.items()}
    mins = {k: np.min(v) for k, v in results.items()}
    maxs = {k: np.max(v) for k, v in results.items()}

    # ─────────────────────────────────────────────────────
    # AUROC Comparison Table
    # ─────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  AUROC Comparison Table")
    print(f"{'='*70}")

    print(f"\n  | Method              |  Mean  |  Std   |  Min   |  Max   |")
    print(f"  |---------------------|--------|--------|--------|--------|")
    for k in ['A', 'B', 'C']:
        print(f"  | {labels[k]:<19} | {means[k]:.4f} | {stds[k]:.4f} | {mins[k]:.4f} | {maxs[k]:.4f} |")

    # ─────────────────────────────────────────────────────
    # Per-trial detail
    # ─────────────────────────────────────────────────────
    print(f"\n  Per-Trial AUROC:")
    print(f"  | Trial | A) MSE Recon | B) NT-Xent  | C) Triplet  |")
    print(f"  |-------|-------------|-------------|-------------|")
    for i in range(n_trials):
        print(f"  |   {i+1}   |   {results['A'][i]:.4f}    |   {results['B'][i]:.4f}    |   {results['C'][i]:.4f}    |")
    print(f"  | Mean  |   {means['A']:.4f}    |   {means['B']:.4f}    |   {means['C']:.4f}    |")
    print(f"  | Std   |   {stds['A']:.4f}    |   {stds['B']:.4f}    |   {stds['C']:.4f}    |")

    # ─────────────────────────────────────────────────────
    # ASCII Bar Chart
    # ─────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  AUROC Bar Chart (each # = 0.01)")
    print(f"{'='*70}\n")

    # Find range for chart
    all_means = [means[k] for k in ['A', 'B', 'C']]
    chart_min = max(0, min(all_means) - 0.05)

    for k in ['A', 'B', 'C']:
        m = means[k]
        bar_len = int((m - chart_min) / 0.01)
        bar = '#' * max(bar_len, 1)
        print(f"  {k}) {labels[k]:<19} |{bar}| {m:.4f} +/- {stds[k]:.4f}")

    # Also show per-trial spread
    print(f"\n  Per-trial spread (. = trial, | = mean):")
    for k in ['A', 'B', 'C']:
        line = [' '] * 60
        m = means[k]
        for v in results[k]:
            pos = int((v - chart_min) / 0.01)
            pos = max(0, min(pos, 59))
            line[pos] = '.'
        mean_pos = int((m - chart_min) / 0.01)
        mean_pos = max(0, min(mean_pos, 59))
        line[mean_pos] = '|'
        line_str = ''.join(line)
        print(f"  {k}) {labels[k]:<19} [{line_str}] {chart_min:.2f}-{chart_min+0.60:.2f}")

    # ─────────────────────────────────────────────────────
    # Pairwise comparisons
    # ─────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  Pairwise Comparisons (delta = row - col)")
    print(f"{'='*70}")

    pairs = [('B', 'A'), ('C', 'A'), ('C', 'B')]
    for k1, k2 in pairs:
        deltas = [results[k1][i] - results[k2][i] for i in range(n_trials)]
        delta_mean = np.mean(deltas)
        delta_std = np.std(deltas)
        wins = sum(1 for d in deltas if d > 0)
        print(f"\n  {labels[k1]} vs {labels[k2]}:")
        print(f"    Delta mean: {delta_mean:+.4f} +/- {delta_std:.4f}")
        print(f"    Win rate:   {wins}/{n_trials}")
        per_trial = "  ".join([f"{d:+.4f}" for d in deltas])
        print(f"    Per trial:  {per_trial}")

    # ─────────────────────────────────────────────────────
    # Analysis
    # ─────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  Analysis")
    print(f"{'='*70}")

    best_key = max(means, key=means.get)
    worst_key = min(means, key=means.get)

    print(f"\n  Best:  {best_key}) {labels[best_key]} = {means[best_key]:.4f} +/- {stds[best_key]:.4f}")
    print(f"  Worst: {worst_key}) {labels[worst_key]} = {means[worst_key]:.4f} +/- {stds[worst_key]:.4f}")
    print(f"  Gap (best-worst): {means[best_key] - means[worst_key]:+.4f}")

    # Check if contrastive/triplet beat MSE baseline
    print(f"\n  vs MSE Baseline (A):")
    for k in ['B', 'C']:
        diff = means[k] - means['A']
        pct = diff / max(means['A'], 1e-9) * 100
        direction = "BETTER" if diff > 0 else "WORSE"
        print(f"    {labels[k]}: {diff:+.4f} ({pct:+.1f}%) -> {direction}")

    # Consistency check
    print(f"\n  Consistency (std as % of mean):")
    for k in ['A', 'B', 'C']:
        cv = stds[k] / max(means[k], 1e-9) * 100
        stable = "STABLE" if cv < 10 else "UNSTABLE" if cv > 25 else "MODERATE"
        print(f"    {labels[k]}: CV={cv:.1f}% -> {stable}")

    # H305 verdict
    print(f"\n{'='*70}")
    print(f"  H-305 Verdict")
    print(f"{'='*70}")
    print(f"\n  Hypothesis: Contrastive objectives (NT-Xent, Triplet) produce")
    print(f"  better inter-child tension anomaly scores than MSE reconstruction.")
    print(f"\n  Results:")
    print(f"    A) MSE Recon + Inter:  {means['A']:.4f} +/- {stds['A']:.4f}")
    print(f"    B) NT-Xent + Inter:    {means['B']:.4f} +/- {stds['B']:.4f}")
    print(f"    C) Triplet + Inter:    {means['C']:.4f} +/- {stds['C']:.4f}")

    b_vs_a = means['B'] - means['A']
    c_vs_a = means['C'] - means['A']

    if b_vs_a > 0.02 or c_vs_a > 0.02:
        winner = 'B' if b_vs_a > c_vs_a else 'C'
        print(f"\n  -> CONFIRMED: {labels[winner]} beats MSE baseline by {max(b_vs_a,c_vs_a):+.4f}")
        print(f"     Contrastive learning improves inter-child anomaly detection")
    elif b_vs_a > 0 or c_vs_a > 0:
        print(f"\n  -> WEAKLY CONFIRMED: marginal improvement ({max(b_vs_a,c_vs_a):+.4f})")
        print(f"     Effect too small to be conclusive")
    elif b_vs_a < -0.02 and c_vs_a < -0.02:
        print(f"\n  -> CONTRADICTED: Both contrastive methods WORSE than MSE")
        print(f"     MSE reconstruction remains the stronger objective for mitosis anomaly")
    else:
        print(f"\n  -> INCONCLUSIVE: differences within noise margin")

    print(f"\n  Done.")


if __name__ == '__main__':
    main()
