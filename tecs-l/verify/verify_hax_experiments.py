#!/usr/bin/env python3
"""
H-AX-10/11/12 Deep Experimental Verification

EXP 1 (H-AX-12): Tension setpoint sweep — is 1.0 truly optimal?
EXP 2 (H-AX-10): Direction PH merge order × R(rank) correlation
EXP 3 (H-AX-11): R-spectrum at growth stages + consciousness proxy
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import numpy as np
import math
from fractions import Fraction
import sys
import os

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# Arithmetic functions
# ============================================================
def factorize(n):
    factors = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors

def sigma(n):
    f = factorize(n)
    r = 1
    for p, a in f.items():
        r *= (p**(a+1)-1)//(p-1)
    return r

def phi(n):
    f = factorize(n)
    r = n
    for p in f:
        r = r*(p-1)//p
    return r

def tau(n):
    f = factorize(n)
    r = 1
    for a in f.values():
        r *= (a+1)
    return r

def R_float(n):
    return float(Fraction(sigma(n)*phi(n), n*tau(n)))

# ============================================================
# PureField Engine (from model_pure_field.py)
# ============================================================
class PureFieldEngine(nn.Module):
    def __init__(self, input_dim=784, hidden_dim=128, output_dim=10,
                 tension_setpoint=1.0):
        super().__init__()
        self.engine_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Dropout(0.3), nn.Linear(hidden_dim, output_dim)
        )
        self.engine_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Dropout(0.3), nn.Linear(hidden_dim, output_dim)
        )
        self.tension_scale = nn.Parameter(torch.ones(1))
        self.setpoint = tension_setpoint

    def forward(self, x):
        a = self.engine_a(x)
        g = self.engine_g(x)
        rep = a - g
        tension = (rep ** 2).mean(dim=-1)
        return rep, tension

    def get_directions(self, x):
        """Extract direction vectors and magnitudes."""
        with torch.no_grad():
            a = self.engine_a(x)
            g = self.engine_g(x)
            rep = a - g
            mag = torch.sqrt((rep**2).mean(-1))
            direction = F.normalize(rep, dim=-1)
        return direction, mag, rep

# ============================================================
# Data loading
# ============================================================
def load_mnist(batch_size=256):
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    train_ds = datasets.MNIST('data', train=True, download=True, transform=transform)
    test_ds = datasets.MNIST('data', train=False, transform=transform)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)
    return train_loader, test_loader

# ============================================================
# Training function
# ============================================================
def train_model(model, train_loader, test_loader, epochs=10, lr=1e-3, quiet=False):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    for ep in range(epochs):
        model.train()
        total_loss = 0
        for x, y in train_loader:
            optimizer.zero_grad()
            out, tension = model(x.view(-1, 784))
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

    # Final eval
    model.eval()
    correct = 0
    total = 0
    all_tension = []
    with torch.no_grad():
        for x, y in test_loader:
            out, tension = model(x.view(-1, 784))
            pred = out.argmax(1)
            correct += (pred == y).sum().item()
            total += y.size(0)
            all_tension.append(tension.numpy())

    acc = correct / total
    mean_tension = np.concatenate(all_tension).mean()
    if not quiet:
        print(f"    Acc={acc*100:.2f}%, mean_tension={mean_tension:.4f}")
    return acc, mean_tension

print("=" * 80)
print("H-AX EXPERIMENTAL VERIFICATION")
print("=" * 80)

# Load data once
print("\nLoading MNIST...")
train_loader, test_loader = load_mnist()
print("Done.")

# ============================================================
# EXP 1 (H-AX-12): TENSION SETPOINT SWEEP
# ============================================================
print("\n" + "=" * 80)
print("EXP 1 (H-AX-12): TENSION SETPOINT SWEEP")
print("  Is tension=1.0 truly the optimal setpoint?")
print("=" * 80)

# Train with different setpoints by adding homeostasis regularization
setpoints = [0.1, 0.3, 0.5, 0.7, 1.0, 1.3, 1.5, 2.0, 3.0, 5.0]
results_exp1 = []

for sp in setpoints:
    print(f"\n  Setpoint = {sp}:")
    model = PureFieldEngine(784, 128, 10, tension_setpoint=sp)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()

    for ep in range(10):
        model.train()
        for x, y in train_loader:
            optimizer.zero_grad()
            out, tension = model(x.view(-1, 784))
            ce_loss = criterion(out, y)
            # Homeostasis regularization: push tension toward setpoint
            homeo_loss = ((tension - sp) ** 2).mean() * 0.1
            loss = ce_loss + homeo_loss
            loss.backward()
            optimizer.step()

    model.eval()
    correct = 0
    total = 0
    all_tension = []
    with torch.no_grad():
        for x, y in test_loader:
            out, tension = model(x.view(-1, 784))
            pred = out.argmax(1)
            correct += (pred == y).sum().item()
            total += y.size(0)
            all_tension.append(tension.numpy())

    acc = correct / total
    mt = np.concatenate(all_tension).mean()
    results_exp1.append((sp, acc, mt))
    print(f"    Acc={acc*100:.2f}%, actual_tension={mt:.4f}")

# Find optimal
best = max(results_exp1, key=lambda x: x[1])
print(f"\n  === SETPOINT SWEEP RESULTS ===")
print(f"  {'Setpoint':<10} {'Acc%':<10} {'Act.Tension':<12} {'R(setpoint) if int':<20}")
print(f"  {'-'*52}")
for sp, acc, mt in results_exp1:
    r_val = ""
    if sp == int(sp) and sp >= 1:
        r_val = f"R({int(sp)})={R_float(int(sp)):.4f}"
    marker = " ★ BEST" if acc == best[1] else ""
    print(f"  {sp:<10.1f} {acc*100:<10.2f} {mt:<12.4f} {r_val:<20}{marker}")

# Is 1.0 the best?
sp1_acc = [a for s,a,_ in results_exp1 if s == 1.0][0]
print(f"\n  Setpoint=1.0 accuracy: {sp1_acc*100:.2f}%")
print(f"  Best setpoint: {best[0]} at {best[1]*100:.2f}%")
if best[0] == 1.0:
    print(f"  ★ CONFIRMED: tension=1.0 IS optimal!")
else:
    diff = (best[1] - sp1_acc) * 100
    print(f"  ✗ Setpoint={best[0]} beats 1.0 by {diff:.2f}pp")

# ============================================================
# EXP 2 (H-AX-10): DIRECTION PH × R(RANK)
# ============================================================
print("\n" + "=" * 80)
print("EXP 2 (H-AX-10): DIRECTION PH MERGE ORDER × R(RANK)")
print("=" * 80)

# Train a good model first
print("\n  Training PureField on MNIST (15 epochs)...")
model = PureFieldEngine(784, 128, 10)
acc, mt = train_model(model, train_loader, test_loader, epochs=15)
print(f"  Final: acc={acc*100:.2f}%, tension={mt:.4f}")

# Extract class-mean direction vectors
print("\n  Extracting direction vectors...")
all_dirs = []
all_labels = []
model.eval()
with torch.no_grad():
    for x, y in test_loader:
        d, m, r = model.get_directions(x.view(-1, 784))
        all_dirs.append(d.numpy())
        all_labels.append(y.numpy())

dirs = np.concatenate(all_dirs)
labels = np.concatenate(all_labels)

# Compute class means
n_classes = 10
class_means = np.zeros((n_classes, 10))
for c in range(n_classes):
    mask = labels == c
    class_means[c] = dirs[mask].mean(axis=0)
    class_means[c] /= np.linalg.norm(class_means[c])  # normalize

# Cosine distance matrix
cos_dist = np.zeros((n_classes, n_classes))
for i in range(n_classes):
    for j in range(n_classes):
        cos_dist[i, j] = 1 - np.dot(class_means[i], class_means[j])

print(f"\n  Cosine distance matrix (class means):")
print(f"      ", end="")
for j in range(10):
    print(f"  {j:5d}", end="")
print()
for i in range(10):
    print(f"  {i}: ", end="")
    for j in range(10):
        print(f"  {cos_dist[i,j]:5.3f}", end="")
    print()

# PH merge order (single-linkage)
pairs = []
for i in range(n_classes):
    for j in range(i+1, n_classes):
        pairs.append((cos_dist[i,j], i, j))
pairs.sort()

print(f"\n  PH Merge Order (single-linkage):")
print(f"  {'Rank':<6} {'Pair':<10} {'Distance':<10} {'R(rank)':<12}")
print(f"  {'-'*38}")

merge_ranks = []
r_values = []
for rank, (dist, i, j) in enumerate(pairs, 1):
    r_val = R_float(rank)
    merge_ranks.append(rank)
    r_values.append(r_val)
    if rank <= 15:
        print(f"  {rank:<6} ({i},{j}){'':<5} {dist:<10.4f} {r_val:<12.4f}")

# Confusion matrix
model.eval()
confusion = np.zeros((n_classes, n_classes))
with torch.no_grad():
    for x, y in test_loader:
        out, _ = model(x.view(-1, 784))
        pred = out.argmax(1).numpy()
        for true, p in zip(y.numpy(), pred):
            if true != p:
                confusion[true, p] += 1

# Confusion rates for each pair
confusion_rates = []
for rank, (dist, i, j) in enumerate(pairs, 1):
    c_rate = confusion[i,j] + confusion[j,i]
    confusion_rates.append(c_rate)

# Spearman correlation: merge_rank vs confusion_rate
def spearman(x, y):
    n = len(x)
    def rank_data(d):
        s = sorted(range(n), key=lambda i: d[i])
        r = [0]*n
        for i, idx in enumerate(s):
            r[idx] = i+1
        return r
    rx = rank_data(x)
    ry = rank_data(y)
    d2 = sum((a-b)**2 for a,b in zip(rx,ry))
    return 1 - 6*d2/(n*(n**2-1))

# Core H-CX-66 reproduction
rho_merge_confusion = spearman(
    [d for d,_,_ in pairs],  # merge distance
    confusion_rates           # confusion rate
)
print(f"\n  H-CX-66 Reproduction:")
print(f"  Spearman(merge_distance, confusion_rate) = {rho_merge_confusion:.4f}")

# NEW: H-AX-10 test — R(rank) vs confusion_rate
rho_r_confusion = spearman(r_values, confusion_rates)
print(f"\n  ★ H-AX-10 TEST:")
print(f"  Spearman(R(merge_rank), confusion_rate) = {rho_r_confusion:.4f}")

# Also test: R(rank) vs merge_distance
rho_r_dist = spearman(r_values, [d for d,_,_ in pairs])
print(f"  Spearman(R(merge_rank), merge_distance) = {rho_r_dist:.4f}")

# What about R of the PAIR PRODUCT?
print(f"\n  Alternative: R(i×j+1) for each pair:")
pair_r_values = []
for rank, (dist, i, j) in enumerate(pairs[:10], 1):
    n_pair = i * j + 1  # avoid 0
    if n_pair < 1: n_pair = 1
    r_pair = R_float(n_pair)
    pair_r_values.append(r_pair)
    print(f"    ({i},{j}) → n={n_pair}, R={r_pair:.4f}")

if len(pair_r_values) >= 5:
    rho_pair = spearman(pair_r_values, confusion_rates[:10])
    print(f"  Spearman(R(i*j+1), confusion) = {rho_pair:.4f}")

# ============================================================
# EXP 3 (H-AX-11): MULTI-CELL CONSCIOUSNESS PROXY
# ============================================================
print("\n" + "=" * 80)
print("EXP 3 (H-AX-11): MULTI-CELL R-SPECTRUM CONSCIOUSNESS PROXY")
print("=" * 80)

# Use ensemble of PureField models to simulate cells
# Phi proxy = mutual information between cell outputs
cell_counts = [1, 2, 3, 6, 12]

print(f"\n  Training ensembles at each growth stage...")
print(f"  {'Cells':<8} {'R(n)':<10} {'Acc%':<10} {'Mean_T':<10} {'Ensemble_Acc':<12} {'Agreement':<10} {'Phi_proxy'}")
print(f"  {'-'*70}")

for n_cells in cell_counts:
    r_val = R_float(n_cells)

    # Train n_cells independent models
    models = []
    for c in range(n_cells):
        m = PureFieldEngine(784, 128, 10)
        train_model(m, train_loader, test_loader, epochs=8, quiet=True)
        models.append(m)

    # Evaluate ensemble
    all_preds = [[] for _ in range(n_cells)]
    all_correct = []
    all_tensions = [[] for _ in range(n_cells)]

    for x, y in test_loader:
        x_flat = x.view(-1, 784)
        cell_outputs = []
        for c, m in enumerate(models):
            m.eval()
            with torch.no_grad():
                out, tension = m(x_flat)
                cell_outputs.append(out)
                all_preds[c].append(out.argmax(1).numpy())
                all_tensions[c].append(tension.numpy())

        # Ensemble: average logits
        ensemble_out = sum(cell_outputs) / n_cells
        ensemble_pred = ensemble_out.argmax(1)
        all_correct.append((ensemble_pred == y).float().numpy())

    # Metrics
    individual_accs = []
    for c in range(n_cells):
        preds_c = np.concatenate(all_preds[c])
        # Need true labels
        true_labels = []
        for _, y in test_loader:
            true_labels.append(y.numpy())
        true_labels = np.concatenate(true_labels)
        acc_c = (preds_c == true_labels).mean()
        individual_accs.append(acc_c)

    mean_individual = np.mean(individual_accs)
    ensemble_acc = np.concatenate(all_correct).mean()
    mean_tension = np.mean([np.concatenate(t).mean() for t in all_tensions])

    # Agreement (Phi proxy): fraction of test samples where all cells agree
    all_pred_arrays = [np.concatenate(p) for p in all_preds]
    if n_cells > 1:
        agreement = np.mean([
            np.all([all_pred_arrays[c] == all_pred_arrays[0]
                    for c in range(1, n_cells)], axis=0)
        ])
    else:
        agreement = 1.0

    # Phi proxy: inter-cell disagreement entropy
    if n_cells > 1:
        # For each sample, count unique predictions
        stacked = np.stack(all_pred_arrays, axis=0)  # (n_cells, n_samples)
        n_unique = np.array([len(set(stacked[:, i])) for i in range(stacked.shape[1])])
        phi_proxy = np.log(n_unique.mean())  # Higher = more integration needed
    else:
        phi_proxy = 0.0

    marker = " ★ R=1!" if abs(r_val - 1) < 0.01 else ""
    print(f"  {n_cells:<8} {r_val:<10.4f} {mean_individual*100:<10.2f} {mean_tension:<10.4f} {ensemble_acc*100:<12.2f} {agreement:<10.4f} {phi_proxy:<.4f}{marker}")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 80)
print("EXPERIMENTAL SUMMARY")
print("=" * 80)
print(f"""
  EXP 1 (H-AX-12): Tension setpoint sweep
    → Is setpoint=1.0 optimal?

  EXP 2 (H-AX-10): Direction PH × R(rank)
    → H-CX-66 reproduced?
    → R(rank) correlates with confusion?

  EXP 3 (H-AX-11): Multi-cell growth stages
    → 6-cell shows peak performance?
    → R=1 stages (1,6) differ from R≠1 stages?
""")
print("Done.")
