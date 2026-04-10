#!/usr/bin/env python3
"""
H-297: Mitosis Ensemble Diversity -> Anomaly Detection
=======================================================
Tests whether more children (N-way mitosis) yields better anomaly detection.

Dataset: Breast Cancer (sklearn) — malignant=anomaly, benign=normal
Model:   Simple 2-engine repulsion autoencoder
         engine_a(Linear->ReLU->Linear), engine_g(same), eq(Linear)
         output = eq(x) + scale * (engine_a(x) - engine_g(x))

Protocol:
  - Train parent on normal class only (MSE reconstruction)
  - For N in [1,2,4,8,16]:
    N=1: parent internal tension as anomaly score
    N>1: mitosis into N children (gaussian noise scale=0.01),
         train each on different mini-batches for 30 epochs,
         anomaly score = mean pairwise |child_i(x) - child_j(x)|^2
  - 3 trials per N, report mean +/- std AUROC
"""

import numpy as np
import torch
import torch.nn as nn
from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
import copy
import math
import sys

# Reproducibility base seed
BASE_SEED = 42

# ─── Model ───────────────────────────────────────────────────────────────

class TwoEngineModel(nn.Module):
    """Simple 2-engine repulsion model (autoencoder-style)."""

    def __init__(self, input_dim, hidden_dim=32, repulsion_scale=0.1):
        super().__init__()
        self.engine_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
        )
        self.engine_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
        )
        self.eq = nn.Linear(input_dim, input_dim)
        self.repulsion_scale = repulsion_scale

    def forward(self, x):
        a = self.engine_a(x)
        g = self.engine_g(x)
        out = self.eq(x) + self.repulsion_scale * (a - g)
        return out

    def tension(self, x):
        """Internal tension = ||engine_a(x) - engine_g(x)||^2 per sample."""
        a = self.engine_a(x)
        g = self.engine_g(x)
        return ((a - g) ** 2).mean(dim=1)


# ─── Training ────────────────────────────────────────────────────────────

def train_model(model, X_train, epochs=100, lr=1e-3, batch_size=64):
    """Train model with MSE reconstruction loss on normal data."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    dataset = torch.utils.data.TensorDataset(X_train)
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model.train()
    for epoch in range(epochs):
        for (batch,) in loader:
            optimizer.zero_grad()
            recon = model(batch)
            loss = ((recon - batch) ** 2).mean()
            loss.backward()
            optimizer.step()
    return model


def mitosis(parent, n_children, noise_scale=0.01, seed=0):
    """Create N children by copying parent + gaussian noise on weights."""
    rng = torch.Generator()
    rng.manual_seed(seed)
    children = []
    for i in range(n_children):
        child = copy.deepcopy(parent)
        with torch.no_grad():
            for p in child.parameters():
                noise = torch.randn(p.shape, generator=rng) * noise_scale
                p.add_(noise)
        children.append(child)
    return children


def train_children_on_splits(children, X_train, epochs=30, lr=1e-3, batch_size=64):
    """Train each child on a different mini-batch split."""
    n = len(children)
    indices = np.arange(len(X_train))
    np.random.shuffle(indices)
    splits = np.array_split(indices, n)

    for i, child in enumerate(children):
        subset = X_train[splits[i]]
        train_model(child, subset, epochs=epochs, lr=lr, batch_size=batch_size)
    return children


# ─── Anomaly Scoring ─────────────────────────────────────────────────────

def anomaly_score_tension(model, X):
    """N=1: use parent's internal tension as anomaly score."""
    model.eval()
    with torch.no_grad():
        scores = model.tension(X)
    return scores.numpy()


def anomaly_score_pairwise(children, X):
    """N>1: mean pairwise ||child_i(x) - child_j(x)||^2."""
    model_outputs = []
    for child in children:
        child.eval()
        with torch.no_grad():
            out = child(X)
        model_outputs.append(out)

    n = len(children)
    n_pairs = n * (n - 1) // 2
    scores = torch.zeros(len(X))

    for i in range(n):
        for j in range(i + 1, n):
            diff = ((model_outputs[i] - model_outputs[j]) ** 2).mean(dim=1)
            scores += diff

    scores = scores / max(n_pairs, 1)
    return scores.numpy()


# ─── Main Experiment ─────────────────────────────────────────────────────

def run_single_trial(N, X_train_normal, X_test, y_test, trial_seed):
    """Run one trial for a given N value."""
    torch.manual_seed(trial_seed)
    np.random.seed(trial_seed)

    input_dim = X_train_normal.shape[1]

    # Train parent
    parent = TwoEngineModel(input_dim, hidden_dim=32, repulsion_scale=0.1)
    parent = train_model(parent, X_train_normal, epochs=100, lr=1e-3)

    if N == 1:
        scores = anomaly_score_tension(parent, X_test)
    else:
        children = mitosis(parent, N, noise_scale=0.01, seed=trial_seed)
        children = train_children_on_splits(
            children, X_train_normal, epochs=30, lr=1e-3
        )
        scores = anomaly_score_pairwise(children, X_test)

    auroc = roc_auc_score(y_test, scores)
    return auroc


def main():
    print("=" * 70)
    print("H-297: Mitosis Ensemble Diversity -> Anomaly Detection")
    print("=" * 70)

    # Load data
    data = load_breast_cancer()
    X, y = data.data, data.target
    # In sklearn: 0=malignant (anomaly), 1=benign (normal)
    # Flip so anomaly=1 for AUROC convention
    y_anomaly = 1 - y  # 1=malignant(anomaly), 0=benign(normal)

    print(f"\nDataset: Breast Cancer (n={len(X)}, features={X.shape[1]})")
    print(f"  Normal (benign):    {(y_anomaly == 0).sum()}")
    print(f"  Anomaly (malignant): {(y_anomaly == 1).sum()}")

    # Scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Split: train on normal only, test on all
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_anomaly, test_size=0.3, random_state=BASE_SEED, stratify=y_anomaly
    )

    # Keep only normal samples for training
    normal_mask = y_train == 0
    X_train_normal = torch.tensor(X_train[normal_mask], dtype=torch.float32)
    X_test_t = torch.tensor(X_test, dtype=torch.float32)

    print(f"  Train (normal only): {len(X_train_normal)}")
    print(f"  Test (all):          {len(X_test)}")

    N_values = [1, 2, 4, 8, 16]
    n_trials = 3
    results = {}

    print(f"\nRunning {n_trials} trials per N...")
    print("-" * 50)

    for N in N_values:
        aurocs = []
        for trial in range(n_trials):
            trial_seed = BASE_SEED + trial * 1000 + N
            auroc = run_single_trial(
                N, X_train_normal, X_test_t, y_test, trial_seed
            )
            aurocs.append(auroc)
            print(f"  N={N:2d}, trial={trial+1}: AUROC={auroc:.4f}")

        mean_auroc = np.mean(aurocs)
        std_auroc = np.std(aurocs)
        results[N] = (mean_auroc, std_auroc, aurocs)
        print(f"  N={N:2d} => mean={mean_auroc:.4f} +/- {std_auroc:.4f}")
        print()

    # ─── Results Table ────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("RESULTS: N vs AUROC")
    print("=" * 70)
    print(f"{'N':>4} | {'AUROC mean':>11} | {'std':>7} | {'trials':>20}")
    print("-" * 55)
    for N in N_values:
        m, s, trials = results[N]
        trial_str = ", ".join(f"{t:.4f}" for t in trials)
        print(f"{N:4d} | {m:11.4f} | {s:7.4f} | {trial_str}")
    print("-" * 55)

    # ─── ASCII Graph ──────────────────────────────────────────────────
    print("\nASCII Graph: N vs AUROC")
    print("-" * 55)

    means = [results[N][0] for N in N_values]
    stds = [results[N][1] for N in N_values]
    y_min = max(0, min(means) - max(stds) - 0.02)
    y_max = min(1, max(means) + max(stds) + 0.02)

    graph_height = 20
    graph_width = 50

    for row in range(graph_height, -1, -1):
        y_val = y_min + (y_max - y_min) * row / graph_height
        if row % 5 == 0:
            label = f"{y_val:.3f} |"
        else:
            label = "       |"
        line = list(" " * graph_width)

        for i, N in enumerate(N_values):
            col = int(i * (graph_width - 1) / max(len(N_values) - 1, 1))
            m, s, _ = results[N]

            # Error bar range
            if abs(y_val - m) < (y_max - y_min) / graph_height / 2:
                line[col] = "O"
            elif m - s <= y_val <= m + s:
                line[col] = "|"

        print(label + "".join(line))

    x_axis = "       +" + "-" * graph_width
    print(x_axis)
    x_labels = "        "
    for i, N in enumerate(N_values):
        col = int(i * (graph_width - 1) / max(len(N_values) - 1, 1))
        x_labels_list = list(x_labels.ljust(60))
        pos = 8 + col
        lbl = f"N={N}"
        for ci, ch in enumerate(lbl):
            if pos + ci < len(x_labels_list):
                x_labels_list[pos + ci] = ch
        x_labels = "".join(x_labels_list)
    print(x_labels)

    # ─── Exponential Saturation Fit ──────────────────────────────────
    print("\n" + "=" * 70)
    print("Exponential Saturation Fit: AUROC = A - B * exp(-C * N)")
    print("=" * 70)

    # Fit AUROC = A - B * exp(-C * N) using least squares grid search
    N_arr = np.array(N_values, dtype=float)
    M_arr = np.array(means)

    best_loss = float("inf")
    best_params = (0, 0, 0)

    for A in np.linspace(min(means) - 0.05, 1.0, 200):
        for C in np.linspace(0.01, 2.0, 100):
            # Given A and C, solve for B analytically:
            # AUROC_i = A - B * exp(-C * N_i)
            # B = (A - AUROC_i) / exp(-C * N_i)  in LS sense
            exp_vals = np.exp(-C * N_arr)
            residuals_a = A - M_arr
            # B = sum(residuals_a * exp_vals) / sum(exp_vals^2)
            denom = np.sum(exp_vals ** 2)
            if denom < 1e-12:
                continue
            B = np.sum(residuals_a * exp_vals) / denom
            if B < 0:
                continue
            pred = A - B * np.exp(-C * N_arr)
            loss = np.sum((pred - M_arr) ** 2)
            if loss < best_loss:
                best_loss = loss
                best_params = (A, B, C)

    A, B, C = best_params
    pred_fit = A - B * np.exp(-C * N_arr)
    residuals = M_arr - pred_fit
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((M_arr - np.mean(M_arr)) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 1e-12 else 0

    print(f"\n  Fitted: AUROC = {A:.4f} - {B:.4f} * exp(-{C:.4f} * N)")
    print(f"  R^2 = {r_squared:.4f}")
    print(f"  Saturation level (A) = {A:.4f}")
    print(f"  Initial gap (B) = {B:.4f}")
    print(f"  Growth rate (C) = {C:.4f}")

    print(f"\n  {'N':>4} | {'Observed':>9} | {'Predicted':>9} | {'Residual':>9}")
    print("  " + "-" * 42)
    for i, N in enumerate(N_values):
        print(f"  {N:4d} | {M_arr[i]:9.4f} | {pred_fit[i]:9.4f} | {residuals[i]:+9.4f}")

    # Extrapolation
    print(f"\n  Extrapolation:")
    for N_ext in [32, 64, 128]:
        pred_ext = A - B * math.exp(-C * N_ext)
        print(f"    N={N_ext:3d}: predicted AUROC = {pred_ext:.4f}")

    # ─── Summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    best_N = N_values[np.argmax(means)]
    worst_N = N_values[np.argmin(means)]
    improvement = means[-1] - means[0]  # N=16 vs N=1

    print(f"  Best N:  {best_N} (AUROC={results[best_N][0]:.4f})")
    print(f"  Worst N: {worst_N} (AUROC={results[worst_N][0]:.4f})")
    print(f"  N=16 vs N=1 improvement: {improvement:+.4f}")
    print(f"  Saturation curve R^2: {r_squared:.4f}")

    if improvement > 0.01:
        print(f"\n  CONCLUSION: More children => better anomaly detection (H-297 SUPPORTED)")
    elif improvement > -0.01:
        print(f"\n  CONCLUSION: Marginal effect — N has weak influence (H-297 INCONCLUSIVE)")
    else:
        print(f"\n  CONCLUSION: More children => worse detection (H-297 REJECTED)")

    print(f"\n  Hypothesis: 'Mitosis ensemble diversity improves anomaly detection'")
    print(f"  Mechanism: Diverse children disagree more on anomalies than normals")
    print("=" * 70)


if __name__ == "__main__":
    main()
