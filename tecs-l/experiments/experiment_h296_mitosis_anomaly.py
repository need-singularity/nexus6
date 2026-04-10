#!/usr/bin/env python3
"""Hypothesis 296: Mitosis + Anomaly Detection — Is tension between split engines a better anomaly score"""

import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import copy
from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

class SimpleRepulsion(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, output_dim=2):
        super().__init__()
        self.engine_a = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, output_dim))
        self.engine_g = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, output_dim))
        self.eq = nn.Linear(input_dim, output_dim)

    def forward(self, x):
        a = self.engine_a(x)
        g = self.engine_g(x)
        tension = ((a - g) ** 2).mean(dim=-1)
        eq = self.eq(x)
        return eq + 0.3 * (a - g), tension

def mitosis(parent, scale=0.01):
    c_a = copy.deepcopy(parent)
    c_b = copy.deepcopy(parent)
    with torch.no_grad():
        for p in c_a.parameters(): p.add_(torch.randn_like(p) * scale)
        for p in c_b.parameters(): p.add_(torch.randn_like(p) * scale)
    return c_a, c_b

def main():
    print("=" * 70)
    print("Hypothesis 296: Mitosis + Anomaly Detection")
    print("=" * 70)

    # Load breast cancer
    data = load_breast_cancer()
    X, y = data.data, data.target  # 1=benign(normal), 0=malignant(anomaly)

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # Split: train on normal only
    X_normal = X[y == 1]
    X_anomaly = X[y == 0]

    np.random.seed(42)
    idx = np.random.permutation(len(X_normal))
    n_train = int(0.7 * len(X_normal))
    X_train = X_normal[idx[:n_train]]
    X_test_normal = X_normal[idx[n_train:]]

    X_test = np.vstack([X_test_normal, X_anomaly])
    y_test = np.array([0]*len(X_test_normal) + [1]*len(X_anomaly))  # 1=anomaly

    X_train_t = torch.FloatTensor(X_train)
    X_test_t = torch.FloatTensor(X_test)

    input_dim = X.shape[1]
    results_all = {'internal': [], 'inter': [], 'combined': []}

    for trial in range(5):
        # Train parent
        parent = SimpleRepulsion(input_dim, 64, input_dim)
        opt = torch.optim.Adam(parent.parameters(), lr=0.001)
        for ep in range(50):
            parent.train()
            opt.zero_grad()
            out, _ = parent(X_train_t)
            loss = F.mse_loss(out, X_train_t)
            loss.backward()
            opt.step()

        # Mitosis
        child_a, child_b = mitosis(parent, scale=0.01)

        # Train children independently
        opt_a = torch.optim.Adam(child_a.parameters(), lr=0.001)
        opt_b = torch.optim.Adam(child_b.parameters(), lr=0.001)
        for ep in range(30):
            child_a.train(); child_b.train()
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

        # Evaluate
        child_a.eval(); child_b.eval(); parent.eval()
        with torch.no_grad():
            _, t_internal_a = child_a(X_test_t)
            _, t_internal_b = child_b(X_test_t)
            out_a, _ = child_a(X_test_t)
            out_b, _ = child_b(X_test_t)
            t_inter = ((out_a - out_b) ** 2).mean(dim=-1)

        t_internal = (t_internal_a + t_internal_b) / 2
        t_combined = t_internal + t_inter

        auroc_int = roc_auc_score(y_test, t_internal.numpy())
        auroc_inter = roc_auc_score(y_test, t_inter.numpy())
        auroc_comb = roc_auc_score(y_test, t_combined.numpy())

        results_all['internal'].append(auroc_int)
        results_all['inter'].append(auroc_inter)
        results_all['combined'].append(auroc_comb)

    print(f"\nBreast Cancer (5 trials):")
    print(f"  {'method':>15} {'AUROC mean':>12} {'std':>8}")
    print(f"  {'-'*38}")
    for k, v in results_all.items():
        print(f"  {k:>15} {np.mean(v):>12.4f} {np.std(v):>8.4f}")

    best_int = np.mean(results_all['internal'])
    best_inter = np.mean(results_all['inter'])
    best_comb = np.mean(results_all['combined'])

    print(f"\n  Analysis:")
    if best_inter > best_int:
        print(f"    Inter-child tension > internal tension: {best_inter:.4f} > {best_int:.4f}")
        print(f"    → H296 supported: Mitosis improves anomaly detection performance")
    else:
        print(f"    Inter-child tension ≤ internal tension: {best_inter:.4f} ≤ {best_int:.4f}")
        print(f"    → H296 refuted: Mitosis provides no additional contribution to anomaly detection")

    if best_comb > max(best_int, best_inter):
        print(f"    Combined is best: {best_comb:.4f}")
        print(f"    → Internal + inter tension information is complementary")

    # ASCII bar chart
    print(f"\n  AUROC Comparison:")
    for k, v in results_all.items():
        m = np.mean(v)
        bar = '#' * int(m * 50)
        print(f"    {k:>10} |{bar}| {m:.4f}")

    print(f"\nComplete")

if __name__ == '__main__':
    main()