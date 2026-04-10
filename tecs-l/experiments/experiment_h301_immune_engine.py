#!/usr/bin/env python3
"""Hypothesis 301: Adaptive Immune Engine for Anomaly Detection

Biological immune system analogy applied to mitosis-based anomaly detection:
  A) Basic: mean pairwise T_ij across 8 clones as anomaly score
  B) Negative selection: remove clones with high tension on normal validation data
  C) Clonal expansion: copy best-detecting clone, replace worst

Dataset: Breast Cancer (sklearn), benign=normal, malignant=anomaly
Self-contained, no external model imports. 5 trials each.
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
from sklearn.metrics import roc_auc_score


# ─────────────────────────────────────────────────────────
# Model: RepulsionEngine (self-contained)
# ─────────────────────────────────────────────────────────

class RepulsionEngine(nn.Module):
    """Two-pole engine with internal tension."""
    def __init__(self, input_dim, hidden_dim=64, output_dim=None):
        super().__init__()
        if output_dim is None:
            output_dim = input_dim  # autoencoder mode
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


def mitosis_n(parent, n=8, scale=0.01):
    """Split parent into n clones with small perturbation."""
    clones = []
    for _ in range(n):
        child = copy.deepcopy(parent)
        with torch.no_grad():
            for p in child.parameters():
                p.add_(torch.randn_like(p) * scale)
        clones.append(child)
    return clones


# ─────────────────────────────────────────────────────────
# Data preparation
# ─────────────────────────────────────────────────────────

def prepare_data(seed=42):
    """Breast Cancer: benign=normal, malignant=anomaly.
    Returns train_normal, val_normal, test_all, y_test, anomaly_subset."""
    data = load_breast_cancer()
    X, y = data.data, data.target
    # sklearn: 0=malignant, 1=benign

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    X_normal = X[y == 1]   # benign
    X_anomaly = X[y == 0]  # malignant

    rng = np.random.RandomState(seed)
    idx_n = rng.permutation(len(X_normal))
    n_train = int(0.6 * len(X_normal))
    n_val = int(0.2 * len(X_normal))

    X_train = X_normal[idx_n[:n_train]]
    X_val = X_normal[idx_n[n_train:n_train + n_val]]
    X_test_normal = X_normal[idx_n[n_train + n_val:]]

    # Test set: remaining normals + all anomalies
    X_test = np.vstack([X_test_normal, X_anomaly])
    y_test = np.array([0] * len(X_test_normal) + [1] * len(X_anomaly))

    return X_train, X_val, X_test, y_test, X_anomaly


# ─────────────────────────────────────────────────────────
# Training
# ─────────────────────────────────────────────────────────

def train_parent(X_train_t, input_dim, epochs=50, lr=0.001, seed=0):
    """Train parent on normal data (MSE reconstruction)."""
    torch.manual_seed(seed)
    parent = RepulsionEngine(input_dim, hidden_dim=64)
    opt = torch.optim.Adam(parent.parameters(), lr=lr)
    for ep in range(epochs):
        parent.train()
        opt.zero_grad()
        out, _ = parent(X_train_t)
        loss = F.mse_loss(out, X_train_t)
        loss.backward()
        opt.step()
    return parent


def train_clone(clone, X_train_t, epochs=30, lr=0.001):
    """Train a single clone on a random subset of normal data."""
    opt = torch.optim.Adam(clone.parameters(), lr=lr)
    n = len(X_train_t)
    for ep in range(epochs):
        clone.train()
        # Random mini-batch (60% of data each epoch for diversity)
        perm = torch.randperm(n)
        batch_size = max(1, int(0.6 * n))
        batch = X_train_t[perm[:batch_size]]
        opt.zero_grad()
        out, _ = clone(batch)
        loss = F.mse_loss(out, batch)
        loss.backward()
        opt.step()
    return clone


# ─────────────────────────────────────────────────────────
# Pairwise tension computation
# ─────────────────────────────────────────────────────────

def compute_pairwise_tension(clones, X_t):
    """Compute mean pairwise output divergence across all clone pairs.
    Returns per-sample anomaly score (N,)."""
    n_clones = len(clones)
    outputs = []
    for c in clones:
        c.eval()
        with torch.no_grad():
            out, _ = c(X_t)
        outputs.append(out)

    # Mean pairwise L2 divergence
    N = X_t.shape[0]
    score = torch.zeros(N)
    count = 0
    for i in range(n_clones):
        for j in range(i + 1, n_clones):
            diff = ((outputs[i] - outputs[j]) ** 2).mean(dim=-1)
            score += diff
            count += 1
    if count > 0:
        score /= count
    return score.numpy()


def compute_clone_tension_on_set(clone, X_t):
    """Mean tension of a single clone on a dataset (scalar)."""
    clone.eval()
    with torch.no_grad():
        _, tension = clone(X_t)
    return tension.mean().item()


# ─────────────────────────────────────────────────────────
# Mode A: Basic — mean pairwise T_ij
# ─────────────────────────────────────────────────────────

def mode_a_basic(clones, X_test_t, y_test):
    scores = compute_pairwise_tension(clones, X_test_t)
    auroc = roc_auc_score(y_test, scores)
    return auroc, scores


# ─────────────────────────────────────────────────────────
# Mode B: Negative Selection — remove high-tension-on-normal clones
# ─────────────────────────────────────────────────────────

def mode_b_negative_selection(clones, X_val_t, X_test_t, y_test, remove_frac=0.25):
    """Remove top 25% clones by tension on normal validation data."""
    # Compute each clone's mean tension on normal validation set
    tensions = []
    for c in clones:
        t = compute_clone_tension_on_set(c, X_val_t)
        tensions.append(t)
    tensions = np.array(tensions)

    # Remove top 25% (highest tension on normals = false positive prone)
    n_remove = max(1, int(len(clones) * remove_frac))
    keep_idx = np.argsort(tensions)[:len(clones) - n_remove]
    selected = [clones[i] for i in keep_idx]

    if len(selected) < 2:
        # Need at least 2 for pairwise
        selected = [clones[i] for i in np.argsort(tensions)[:2]]

    scores = compute_pairwise_tension(selected, X_test_t)
    auroc = roc_auc_score(y_test, scores)
    return auroc, scores, len(selected), tensions


# ─────────────────────────────────────────────────────────
# Mode C: Clonal Expansion — copy best-detecting clone
# ─────────────────────────────────────────────────────────

def mode_c_clonal_expansion(clones, X_test_t, y_test, X_anomaly_t, known_frac=0.2):
    """Use first 20% of anomalies as 'known'. Find best clone, replace worst."""
    n_known = max(1, int(len(X_anomaly_t) * known_frac))
    X_known = X_anomaly_t[:n_known]

    # Find which clone has highest tension on known anomalies
    clone_scores = []
    for c in clones:
        t = compute_clone_tension_on_set(c, X_known)
        clone_scores.append(t)
    clone_scores = np.array(clone_scores)

    best_idx = np.argmax(clone_scores)
    worst_idx = np.argmin(clone_scores)

    # Replace worst with a perturbed copy of best
    expanded_clones = list(clones)  # shallow copy of list
    expanded_clones[worst_idx] = copy.deepcopy(clones[best_idx])
    # Small perturbation so it's not identical
    with torch.no_grad():
        for p in expanded_clones[worst_idx].parameters():
            p.add_(torch.randn_like(p) * 0.001)

    scores = compute_pairwise_tension(expanded_clones, X_test_t)
    auroc = roc_auc_score(y_test, scores)
    return auroc, scores, best_idx, worst_idx, clone_scores


# ─────────────────────────────────────────────────────────
# False positive rate at threshold
# ─────────────────────────────────────────────────────────

def false_positive_rate(scores, y_test, percentile=90):
    """FPR at a given score percentile threshold."""
    threshold = np.percentile(scores, percentile)
    predicted = (scores >= threshold).astype(int)
    normal_mask = y_test == 0
    if normal_mask.sum() == 0:
        return 0.0
    fpr = predicted[normal_mask].sum() / normal_mask.sum()
    return fpr


# ─────────────────────────────────────────────────────────
# Main experiment
# ─────────────────────────────────────────────────────────

def run_trial(trial_seed):
    """Run one full trial. Returns dict of results."""
    X_train, X_val, X_test, y_test, X_anomaly = prepare_data(seed=42)

    X_train_t = torch.FloatTensor(X_train)
    X_val_t = torch.FloatTensor(X_val)
    X_test_t = torch.FloatTensor(X_test)
    X_anomaly_t = torch.FloatTensor(X_anomaly)
    input_dim = X_train.shape[1]

    # 1. Train parent
    parent = train_parent(X_train_t, input_dim, epochs=50, seed=trial_seed)

    # 2. Mitosis -> 8 clones
    clones = mitosis_n(parent, n=8, scale=0.01)

    # 3. Train each clone independently (different mini-batches via random permutation)
    for i, c in enumerate(clones):
        torch.manual_seed(trial_seed * 100 + i)
        clones[i] = train_clone(c, X_train_t, epochs=30)

    # Mode A: Basic
    auroc_a, scores_a = mode_a_basic(clones, X_test_t, y_test)
    fpr_a = false_positive_rate(scores_a, y_test)

    # Mode B: Negative Selection
    auroc_b, scores_b, n_kept, val_tensions = mode_b_negative_selection(
        clones, X_val_t, X_test_t, y_test, remove_frac=0.25
    )
    fpr_b = false_positive_rate(scores_b, y_test)

    # Mode C: Clonal Expansion
    auroc_c, scores_c, best_idx, worst_idx, clone_scores = mode_c_clonal_expansion(
        clones, X_test_t, y_test, X_anomaly_t, known_frac=0.2
    )
    fpr_c = false_positive_rate(scores_c, y_test)

    return {
        'auroc_a': auroc_a, 'auroc_b': auroc_b, 'auroc_c': auroc_c,
        'fpr_a': fpr_a, 'fpr_b': fpr_b, 'fpr_c': fpr_c,
        'n_kept_b': n_kept, 'best_clone_c': best_idx, 'worst_clone_c': worst_idx,
        'val_tensions': val_tensions, 'clone_scores_c': clone_scores,
    }


def main():
    print("=" * 72)
    print("  Hypothesis 301: Adaptive Immune Engine for Anomaly Detection")
    print("=" * 72)
    print()
    print("  Dataset: Breast Cancer (sklearn)")
    print("  Normal: benign (357) | Anomaly: malignant (212)")
    print("  Parent: 50 epochs MSE reconstruction on normal only")
    print("  Mitosis: 8 clones (scale=0.01), each trained 30 epochs")
    print()
    print("  Mode A: Basic — mean pairwise T_ij across 8 clones")
    print("  Mode B: Negative selection — remove top 25% FP-prone clones")
    print("  Mode C: Clonal expansion — copy best detector, replace worst")
    print()

    N_TRIALS = 5
    results = []

    for trial in range(N_TRIALS):
        print(f"  Trial {trial + 1}/{N_TRIALS} ...", end=" ", flush=True)
        r = run_trial(trial_seed=trial * 7 + 42)
        results.append(r)
        print(f"A={r['auroc_a']:.4f}  B={r['auroc_b']:.4f}  C={r['auroc_c']:.4f}")

    # ─── Aggregate ───
    aurocs_a = [r['auroc_a'] for r in results]
    aurocs_b = [r['auroc_b'] for r in results]
    aurocs_c = [r['auroc_c'] for r in results]
    fprs_a = [r['fpr_a'] for r in results]
    fprs_b = [r['fpr_b'] for r in results]
    fprs_c = [r['fpr_c'] for r in results]

    print()
    print("=" * 72)
    print("  AUROC Comparison (5 trials)")
    print("=" * 72)
    print()
    print(f"  {'Mode':<30} {'Mean':>8} {'Std':>8} {'Min':>8} {'Max':>8}")
    print(f"  {'-'*62}")
    print(f"  {'A) Basic (8 clones)':<30} {np.mean(aurocs_a):>8.4f} {np.std(aurocs_a):>8.4f} {np.min(aurocs_a):>8.4f} {np.max(aurocs_a):>8.4f}")
    print(f"  {'B) Negative Selection':<30} {np.mean(aurocs_b):>8.4f} {np.std(aurocs_b):>8.4f} {np.min(aurocs_b):>8.4f} {np.max(aurocs_b):>8.4f}")
    print(f"  {'C) Clonal Expansion':<30} {np.mean(aurocs_c):>8.4f} {np.std(aurocs_c):>8.4f} {np.min(aurocs_c):>8.4f} {np.max(aurocs_c):>8.4f}")

    print()
    print("=" * 72)
    print("  False Positive Rate at 90th percentile threshold")
    print("=" * 72)
    print()
    print(f"  {'Mode':<30} {'Mean FPR':>10} {'Std':>8}")
    print(f"  {'-'*50}")
    print(f"  {'A) Basic':<30} {np.mean(fprs_a):>10.4f} {np.std(fprs_a):>8.4f}")
    print(f"  {'B) Negative Selection':<30} {np.mean(fprs_b):>10.4f} {np.std(fprs_b):>8.4f}")
    print(f"  {'C) Clonal Expansion':<30} {np.mean(fprs_c):>10.4f} {np.std(fprs_c):>8.4f}")

    # ─── Per-trial detail ───
    print()
    print("=" * 72)
    print("  Per-Trial Detail")
    print("=" * 72)
    print()
    print(f"  {'Trial':>5} | {'AUROC-A':>8} {'AUROC-B':>8} {'AUROC-C':>8} | {'FPR-A':>6} {'FPR-B':>6} {'FPR-C':>6} | {'Kept(B)':>7} {'Best(C)':>7} {'Worst(C)':>8}")
    print(f"  {'-'*90}")
    for i, r in enumerate(results):
        print(f"  {i+1:>5} | {r['auroc_a']:>8.4f} {r['auroc_b']:>8.4f} {r['auroc_c']:>8.4f} | "
              f"{r['fpr_a']:>6.3f} {r['fpr_b']:>6.3f} {r['fpr_c']:>6.3f} | "
              f"{r['n_kept_b']:>7} {r['best_clone_c']:>7} {r['worst_clone_c']:>8}")

    # ─── Clone tension profiles (last trial) ───
    print()
    print("=" * 72)
    print("  Clone Analysis (last trial)")
    print("=" * 72)
    last = results[-1]
    print()
    print("  Validation tensions (higher = more FP-prone, removed in B):")
    vt = last['val_tensions']
    for i, t in enumerate(vt):
        bar = '#' * int(t * 200)
        removed = " <-- REMOVED" if t >= np.percentile(vt, 75) else ""
        print(f"    Clone {i}: {t:>8.5f} |{bar}{removed}")

    print()
    print("  Anomaly detection scores per clone (higher = better detector):")
    cs = last['clone_scores_c']
    for i, s in enumerate(cs):
        bar = '#' * int(s * 200)
        tag = ""
        if i == last['best_clone_c']:
            tag = " <-- BEST (expanded)"
        elif i == last['worst_clone_c']:
            tag = " <-- WORST (replaced)"
        print(f"    Clone {i}: {s:>8.5f} |{bar}{tag}")

    # ─── ASCII chart ───
    print()
    print("=" * 72)
    print("  AUROC Comparison — ASCII Chart")
    print("=" * 72)
    print()

    means = {
        'A) Basic':     np.mean(aurocs_a),
        'B) Neg.Sel.':  np.mean(aurocs_b),
        'C) Clonal':    np.mean(aurocs_c),
    }

    # Scale: 0.5 to 1.0 mapped to 0-50 chars
    lo = 0.5
    hi = 1.0
    width = 50

    print(f"  {'':>14} {lo:<5}{'':>{width//2-5}}{(lo+hi)/2:.2f}{'':>{width//2-5}}{hi:>5}")
    print(f"  {'':>14} |{''.join(['-' if i % 10 == 0 else ' ' for i in range(width)])}|")
    for label, val in means.items():
        pos = int((val - lo) / (hi - lo) * width)
        pos = max(0, min(width, pos))
        bar = '#' * pos
        print(f"  {label:>14} |{bar:<{width}}| {val:.4f}")
    print(f"  {'':>14} |{''.join(['-' if i % 10 == 0 else ' ' for i in range(width)])}|")

    # ─── FPR comparison chart ───
    print()
    print("  FPR at 90th percentile (lower is better):")
    print()
    fpr_means = {
        'A) Basic':     np.mean(fprs_a),
        'B) Neg.Sel.':  np.mean(fprs_b),
        'C) Clonal':    np.mean(fprs_c),
    }
    for label, val in fpr_means.items():
        bar = '#' * int(val * 100)
        print(f"  {label:>14} |{bar:<20}| {val:.4f}")

    # ─── Analysis ───
    print()
    print("=" * 72)
    print("  Analysis")
    print("=" * 72)
    print()

    mean_a = np.mean(aurocs_a)
    mean_b = np.mean(aurocs_b)
    mean_c = np.mean(aurocs_c)
    fpr_mean_a = np.mean(fprs_a)
    fpr_mean_b = np.mean(fprs_b)
    fpr_mean_c = np.mean(fprs_c)

    # B vs A
    diff_ba = mean_b - mean_a
    if diff_ba > 0.005:
        print(f"  Negative Selection (B) improves AUROC by +{diff_ba:.4f} over Basic (A)")
    elif diff_ba < -0.005:
        print(f"  Negative Selection (B) hurts AUROC by {diff_ba:.4f} vs Basic (A)")
    else:
        print(f"  Negative Selection (B) ~ same AUROC as Basic (A) (delta={diff_ba:+.4f})")

    fpr_diff_ba = fpr_mean_b - fpr_mean_a
    if fpr_diff_ba < -0.005:
        print(f"  Negative Selection REDUCES false positives: FPR {fpr_mean_a:.4f} -> {fpr_mean_b:.4f} ({fpr_diff_ba:+.4f})")
    else:
        print(f"  Negative Selection FPR effect: {fpr_mean_a:.4f} -> {fpr_mean_b:.4f} ({fpr_diff_ba:+.4f})")

    print()

    # C vs A
    diff_ca = mean_c - mean_a
    if diff_ca > 0.005:
        print(f"  Clonal Expansion (C) improves AUROC by +{diff_ca:.4f} over Basic (A)")
    elif diff_ca < -0.005:
        print(f"  Clonal Expansion (C) hurts AUROC by {diff_ca:.4f} vs Basic (A)")
    else:
        print(f"  Clonal Expansion (C) ~ same AUROC as Basic (A) (delta={diff_ca:+.4f})")

    fpr_diff_ca = fpr_mean_c - fpr_mean_a
    if fpr_diff_ca < -0.005:
        print(f"  Clonal Expansion REDUCES false positives: FPR {fpr_mean_a:.4f} -> {fpr_mean_c:.4f} ({fpr_diff_ca:+.4f})")
    else:
        print(f"  Clonal Expansion FPR effect: {fpr_mean_a:.4f} -> {fpr_mean_c:.4f} ({fpr_diff_ca:+.4f})")

    print()

    # C vs B
    diff_cb = mean_c - mean_b
    print(f"  C vs B: AUROC delta = {diff_cb:+.4f}")

    # Best overall
    best_label = ['A) Basic', 'B) Neg.Sel.', 'C) Clonal'][np.argmax([mean_a, mean_b, mean_c])]
    best_auroc = max(mean_a, mean_b, mean_c)
    print()
    print(f"  BEST MODE: {best_label} (AUROC={best_auroc:.4f})")

    # Immune analogy summary
    print()
    print("  Immune System Analogy:")
    print("    Mitosis = Clonal generation (V(D)J-like diversification)")
    print("    Mode B = Negative selection (thymic deletion of self-reactive)")
    print("    Mode C = Clonal expansion (amplify best responder)")
    b_works = diff_ba > 0.001
    c_works = diff_ca > 0.001
    if b_works and c_works:
        print("    -> Both immune mechanisms improve detection. Full analogy holds.")
    elif b_works:
        print("    -> Negative selection works. Clonal expansion neutral/harmful.")
    elif c_works:
        print("    -> Clonal expansion works. Negative selection neutral/harmful.")
    else:
        print("    -> Neither mechanism clearly improves over basic mitosis diversity.")

    print()
    print("=" * 72)
    print("  Experiment complete.")
    print("=" * 72)


if __name__ == '__main__':
    main()
