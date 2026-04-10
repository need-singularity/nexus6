#!/usr/bin/env python3
"""
H-298: Mitosis Temporal Anomaly Detection — Optimal Differentiation Time

Hypothesis: After mitosis, children need K epochs of independent training
to develop complementary views. T_ab = mean|child_a(x) - child_b(x)|^2
should show an inverted-U curve as anomaly score vs K.

- K=0: children identical → T_ab=0, no discrimination
- K=small: children diverge on normal data → anomalies stand out
- K=large: children overfit independently → T_ab noisy, AUROC drops

Dataset: Breast Cancer (sklearn), normal=benign, anomaly=malignant
"""

import numpy as np
import torch
import torch.nn as nn
import copy
from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

torch.manual_seed(42)
np.random.seed(42)

# ─── Model ───────────────────────────────────────────────────────────
class SimpleAE(nn.Module):
    def __init__(self, dim, hidden=64):
        super().__init__()
        self.ea = nn.Sequential(nn.Linear(dim, hidden), nn.ReLU(), nn.Linear(hidden, dim))
        self.eg = nn.Sequential(nn.Linear(dim, hidden), nn.ReLU(), nn.Linear(hidden, dim))
        self.eq = nn.Linear(dim, dim)

    def forward(self, x):
        a, g = self.ea(x), self.eg(x)
        t = ((a - g) ** 2).mean(-1)
        return self.eq(x) + 0.3 * (a - g), t


# ─── Data ────────────────────────────────────────────────────────────
data = load_breast_cancer()
X, y = data.data, data.target  # 1=benign(normal), 0=malignant(anomaly)

scaler = StandardScaler()
X = scaler.fit_transform(X)
X = torch.tensor(X, dtype=torch.float32)
y = torch.tensor(y, dtype=torch.long)

# Split: train on normal only, test on both
X_normal = X[y == 1]
X_anomaly = X[y == 0]

X_train_norm, X_test_norm = train_test_split(X_normal.numpy(), test_size=0.3, random_state=42)
X_train_norm = torch.tensor(X_train_norm, dtype=torch.float32)
X_test_norm = torch.tensor(X_test_norm, dtype=torch.float32)

# Test set: normal + anomaly
X_test = torch.cat([X_test_norm, X_anomaly], dim=0)
y_test = torch.cat([torch.zeros(len(X_test_norm)), torch.ones(len(X_anomaly))], dim=0)
# labels: 0=normal, 1=anomaly

dim = X.shape[1]  # 30

print("=" * 70)
print("H-298: Mitosis Temporal Anomaly Detection")
print("=" * 70)
print(f"Features: {dim}")
print(f"Train (normal only): {len(X_train_norm)}")
print(f"Test normal: {len(X_test_norm)}, Test anomaly: {len(X_anomaly)}")
print(f"Anomaly ratio in test: {len(X_anomaly)/(len(X_test_norm)+len(X_anomaly)):.3f}")
print()


# ─── Train parent ────────────────────────────────────────────────────
def train_parent(seed=0):
    torch.manual_seed(seed)
    model = SimpleAE(dim, hidden=64)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    for epoch in range(50):
        model.train()
        idx = torch.randperm(len(X_train_norm))
        for i in range(0, len(idx), 64):
            batch = X_train_norm[idx[i:i+64]]
            recon, tension = model(batch)
            loss = ((recon - batch) ** 2).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
    return model


# ─── Mitosis ─────────────────────────────────────────────────────────
def mitosis(parent, scale=0.01):
    child_a = copy.deepcopy(parent)
    child_b = copy.deepcopy(parent)
    with torch.no_grad():
        for pa, pb in zip(child_a.parameters(), child_b.parameters()):
            pa.add_(torch.randn_like(pa) * scale)
            pb.add_(torch.randn_like(pb) * scale)
    return child_a, child_b


# ─── Train child for K epochs ───────────────────────────────────────
def train_child(model, epochs, seed_offset=0):
    if epochs == 0:
        return model
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    for epoch in range(epochs):
        model.train()
        torch.manual_seed(seed_offset * 1000 + epoch)
        idx = torch.randperm(len(X_train_norm))
        for i in range(0, len(idx), 64):
            batch = X_train_norm[idx[i:i+64]]
            recon, tension = model(batch)
            loss = ((recon - batch) ** 2).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
    return model


# ─── Evaluate T_ab as anomaly score ─────────────────────────────────
@torch.no_grad()
def evaluate(child_a, child_b, X_eval, y_eval):
    child_a.eval()
    child_b.eval()
    out_a, _ = child_a(X_eval)
    out_b, _ = child_b(X_eval)
    T_ab = ((out_a - out_b) ** 2).mean(dim=-1)  # per-sample

    T_ab_mean = T_ab.mean().item()
    T_ab_normal = T_ab[y_eval == 0].mean().item()
    T_ab_anomaly = T_ab[y_eval == 1].mean().item()

    auroc = roc_auc_score(y_eval.numpy(), T_ab.numpy())
    return T_ab_mean, T_ab_normal, T_ab_anomaly, auroc


# ─── Main experiment ─────────────────────────────────────────────────
K_values = [0, 1, 2, 5, 10, 20, 50]
n_trials = 3

results = {}  # K -> list of (T_ab_mean, T_ab_normal, T_ab_anomaly, auroc)

for K in K_values:
    results[K] = []
    for trial in range(n_trials):
        parent = train_parent(seed=trial * 7)
        child_a, child_b = mitosis(parent, scale=0.01)

        # Train children on DIFFERENT mini-batches (different seed offsets)
        child_a = train_child(child_a, K, seed_offset=trial * 2)
        child_b = train_child(child_b, K, seed_offset=trial * 2 + 1)

        T_mean, T_norm, T_anom, auroc = evaluate(child_a, child_b, X_test, y_test)
        results[K].append((T_mean, T_norm, T_anom, auroc))
        print(f"  K={K:3d} trial={trial} | T_ab={T_mean:.6f} T_norm={T_norm:.6f} T_anom={T_anom:.6f} | AUROC={auroc:.4f}")

print()

# ─── Summary table ───────────────────────────────────────────────────
print("=" * 70)
print("SUMMARY: K vs T_ab vs AUROC (mean +/- std over 3 trials)")
print("=" * 70)
print(f"{'K':>4s} | {'T_ab_mean':>12s} | {'T_ab_normal':>12s} | {'T_ab_anomaly':>12s} | {'AUROC':>12s}")
print("-" * 70)

summary = {}
for K in K_values:
    vals = results[K]
    T_means = [v[0] for v in vals]
    T_norms = [v[1] for v in vals]
    T_anoms = [v[2] for v in vals]
    aurocs = [v[3] for v in vals]

    summary[K] = {
        'T_mean': (np.mean(T_means), np.std(T_means)),
        'T_norm': (np.mean(T_norms), np.std(T_norms)),
        'T_anom': (np.mean(T_anoms), np.std(T_anoms)),
        'auroc': (np.mean(aurocs), np.std(aurocs)),
    }

    print(f"{K:4d} | {np.mean(T_means):9.6f}+/-{np.std(T_means):.4f} | "
          f"{np.mean(T_norms):9.6f}+/-{np.std(T_norms):.4f} | "
          f"{np.mean(T_anoms):9.6f}+/-{np.std(T_anoms):.4f} | "
          f"{np.mean(aurocs):7.4f}+/-{np.std(aurocs):.4f}")

print()

# ─── ASCII Graph: AUROC vs K ─────────────────────────────────────────
print("=" * 70)
print("ASCII Graph: AUROC vs K (differentiation epochs)")
print("=" * 70)

auroc_means = [summary[K]['auroc'][0] for K in K_values]
auroc_min = min(auroc_means) - 0.02
auroc_max = max(auroc_means) + 0.02

graph_width = 50
graph_height = 15

# Find best K
best_K = K_values[np.argmax(auroc_means)]
best_auroc = max(auroc_means)

print(f"Best K = {best_K}, AUROC = {best_auroc:.4f}")
print()

for row in range(graph_height, -1, -1):
    val = auroc_min + (auroc_max - auroc_min) * row / graph_height
    line = f"{val:.3f} |"
    for i, K in enumerate(K_values):
        a = summary[K]['auroc'][0]
        a_row = int((a - auroc_min) / (auroc_max - auroc_min) * graph_height + 0.5)
        col_pos = int(i * graph_width / (len(K_values) - 1))
        if a_row == row:
            line += " " * (col_pos - len(line) + 7) + "*"
        elif row == 0:
            line += " " * (col_pos - len(line) + 7) + "|"
    print(line)

label_line = "       "
for i, K in enumerate(K_values):
    col_pos = int(i * graph_width / (len(K_values) - 1))
    label_line += " " * (col_pos - len(label_line) + 7) + f"{K}"
print("      +" + "-" * (graph_width + 2))
print(label_line)
print(" " * 25 + "K (differentiation epochs)")
print()

# ─── ASCII Graph: T_ab (normal vs anomaly) vs K ─────────────────────
print("=" * 70)
print("ASCII Graph: T_ab by class vs K")
print("  N = normal,  A = anomaly")
print("=" * 70)

T_norm_vals = [summary[K]['T_norm'][0] for K in K_values]
T_anom_vals = [summary[K]['T_anom'][0] for K in K_values]
all_T = T_norm_vals + T_anom_vals
T_min_plot = 0
T_max_plot = max(all_T) * 1.1

for row in range(graph_height, -1, -1):
    val = T_min_plot + (T_max_plot - T_min_plot) * row / graph_height
    line = f"{val:.5f} |"
    for i, K in enumerate(K_values):
        col_pos = int(i * graph_width / (len(K_values) - 1))
        tn = summary[K]['T_norm'][0]
        ta = summary[K]['T_anom'][0]
        tn_row = int((tn - T_min_plot) / (T_max_plot - T_min_plot) * graph_height + 0.5) if T_max_plot > T_min_plot else 0
        ta_row = int((ta - T_min_plot) / (T_max_plot - T_min_plot) * graph_height + 0.5) if T_max_plot > T_min_plot else 0
        spacing = col_pos - len(line) + 9
        if spacing < 1:
            spacing = 1
        if tn_row == row and ta_row == row:
            line += " " * spacing + "X"  # overlap
        elif tn_row == row:
            line += " " * spacing + "N"
        elif ta_row == row:
            line += " " * spacing + "A"
    print(line)

print("         +" + "-" * (graph_width + 2))
label_line = "          "
for i, K in enumerate(K_values):
    col_pos = int(i * graph_width / (len(K_values) - 1))
    label_line += " " * (col_pos - len(label_line) + 10) + f"{K}"
print(label_line)
print(" " * 25 + "K (differentiation epochs)")
print()

# ─── Separation ratio ───────────────────────────────────────────────
print("=" * 70)
print("Separation Ratio: T_anomaly / T_normal")
print("=" * 70)
print(f"{'K':>4s} | {'T_anom/T_norm':>14s} | {'bar':>30s}")
print("-" * 55)

ratios = []
for K in K_values:
    tn = summary[K]['T_norm'][0]
    ta = summary[K]['T_anom'][0]
    ratio = ta / tn if tn > 1e-10 else float('inf')
    ratios.append(ratio)
    bar_len = int(min(ratio, 10) * 3)
    bar = "#" * bar_len
    print(f"{K:4d} | {ratio:14.4f} | {bar}")

print()
print(f"Best separation at K={K_values[np.argmax(ratios)]}, ratio={max(ratios):.4f}")
print()

# ─── Final verdict ───────────────────────────────────────────────────
print("=" * 70)
print("VERDICT")
print("=" * 70)

auroc_at_0 = summary[0]['auroc'][0]
auroc_at_best = summary[best_K]['auroc'][0]
auroc_at_50 = summary[50]['auroc'][0]

print(f"AUROC at K=0:    {auroc_at_0:.4f}")
print(f"AUROC at K={best_K}:  {auroc_at_best:.4f}  (best)")
print(f"AUROC at K=50:   {auroc_at_50:.4f}")
print()

if auroc_at_best > auroc_at_0 and auroc_at_best > auroc_at_50:
    print(">>> INVERTED-U CONFIRMED: optimal K exists between extremes")
elif auroc_at_best == auroc_at_0:
    print(">>> NO DIFFERENTIATION BENEFIT: K=0 already optimal")
elif np.argmax(auroc_means) == len(K_values) - 1:
    print(">>> MONOTONIC INCREASE: more differentiation = better (no peak yet)")
else:
    print(f">>> PEAK at K={best_K}: partial inverted-U pattern")

improvement = (auroc_at_best - auroc_at_0) / max(auroc_at_0, 0.001) * 100
print(f"Improvement over K=0: {improvement:+.2f}%")
print()
print("Done.")
