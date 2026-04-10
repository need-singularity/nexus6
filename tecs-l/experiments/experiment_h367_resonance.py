#!/usr/bin/env python3
"""H367: Resonance Synchronization Model — Telepathy Simulation

Do identical-weight PureFieldEngines synchronize their tension oscillations
when fed the same input sequence? Compare with random-weight pairs.

Metric: Pearson correlation of tension time series between pairs.
  - Pair A (clone): models 0,1 — identical weights
  - Pair B (random): models 2,3 — independent random init

Prediction: corr(clone) >> corr(random)
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import torch
import numpy as np
from model_pure_field import PureFieldEngine
import copy

np.random.seed(42)
torch.manual_seed(42)

N_INPUTS = 100
INPUT_DIM = 784
HIDDEN_DIM = 128
OUTPUT_DIM = 10

# ── Create 4 engines ──────────────────────────────────
base_clone = PureFieldEngine(INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM)
clone_copy = copy.deepcopy(base_clone)

random_a = PureFieldEngine(INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM)
random_b = PureFieldEngine(INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM)

models = [base_clone, clone_copy, random_a, random_b]
labels = ["Clone-A", "Clone-B", "Rand-C", "Rand-D"]

# Verify weight identity / difference
def weight_cosine(m1, m2):
    v1 = torch.cat([p.detach().flatten() for p in m1.parameters()])
    v2 = torch.cat([p.detach().flatten() for p in m2.parameters()])
    return torch.nn.functional.cosine_similarity(v1.unsqueeze(0), v2.unsqueeze(0)).item()

cos_clone = weight_cosine(models[0], models[1])
cos_rand  = weight_cosine(models[2], models[3])
print(f"Weight cosine similarity — Clone pair: {cos_clone:.6f}, Random pair: {cos_rand:.6f}")

# ── Generate shared input sequence ────────────────────
inputs = [torch.randn(1, INPUT_DIM) for _ in range(N_INPUTS)]

# ── Collect tension time series ───────────────────────
tension_series = {i: [] for i in range(4)}

for m in models:
    m.eval()

with torch.no_grad():
    for t, x in enumerate(inputs):
        for i, m in enumerate(models):
            out, tension = m(x)
            tension_series[i].append(tension.item())

tensions = {i: np.array(tension_series[i]) for i in range(4)}

# ── Phase coherence (Kuramoto order parameter) ────────
def phase_from_tension(t_arr):
    """theta_k = atan2(T - mean, dT/dt)"""
    dt = np.gradient(t_arr)
    mean_t = t_arr.mean()
    return np.arctan2(t_arr - mean_t, dt)

phases = {i: phase_from_tension(tensions[i]) for i in range(4)}

def kuramoto_R(ph1, ph2):
    """R_sync = |mean(exp(i*delta_theta))|"""
    delta = ph1 - ph2
    return np.abs(np.mean(np.exp(1j * delta)))

R_clone = kuramoto_R(phases[0], phases[1])
R_rand  = kuramoto_R(phases[2], phases[3])

# ── Pearson correlation ───────────────────────────────
def pearson(a, b):
    return np.corrcoef(a, b)[0, 1]

corr_clone = pearson(tensions[0], tensions[1])
corr_rand  = pearson(tensions[2], tensions[3])
corr_cross = pearson(tensions[0], tensions[2])

# ── Full correlation matrix ───────────────────────────
corr_matrix = np.zeros((4, 4))
for i in range(4):
    for j in range(4):
        corr_matrix[i, j] = pearson(tensions[i], tensions[j])

# ── Statistics ────────────────────────────────────────
print("\n" + "=" * 60)
print("  H367: Resonance Synchronization Experiment")
print("=" * 60)

print(f"\n  N inputs: {N_INPUTS}")
print(f"  Input dim: {INPUT_DIM}, Hidden: {HIDDEN_DIM}, Output: {OUTPUT_DIM}")

print("\n── Tension Statistics ──")
for i in range(4):
    t = tensions[i]
    print(f"  {labels[i]:>8}: mean={t.mean():.4f}  std={t.std():.4f}  min={t.min():.4f}  max={t.max():.4f}")

print("\n── Synchronization Metrics ──")
print(f"  {'Pair':<20} {'Pearson r':>10} {'Kuramoto R':>12}")
print(f"  {'-'*42}")
print(f"  {'Clone (A,B)':<20} {corr_clone:>10.6f} {R_clone:>12.6f}")
print(f"  {'Random (C,D)':<20} {corr_rand:>10.6f} {R_rand:>12.6f}")
print(f"  {'Cross (A,C)':<20} {corr_cross:>10.6f} {'':>12}")
print(f"\n  Delta (clone-rand): r={corr_clone - corr_rand:+.6f}  R={R_clone - R_rand:+.6f}")

# ── Correlation Matrix ────────────────────────────────
print("\n── Correlation Matrix ──")
print(f"  {'':>10}", end="")
for l in labels:
    print(f" {l:>8}", end="")
print()
for i in range(4):
    print(f"  {labels[i]:>10}", end="")
    for j in range(4):
        print(f" {corr_matrix[i,j]:>8.4f}", end="")
    print()

# ── ASCII: Tension Time Series (first 60 steps) ──────
print("\n── Tension Time Series (first 60 steps) ──")
show = min(60, N_INPUTS)
all_vals = np.concatenate([tensions[i][:show] for i in range(4)])
vmin, vmax = all_vals.min(), all_vals.max()
HEIGHT = 12
CHARS = ['.', '+', 'x', 'o']

def to_row(v):
    if vmax == vmin:
        return 0
    return int((v - vmin) / (vmax - vmin) * (HEIGHT - 1))

for i in range(4):
    print(f"\n  {labels[i]} ({CHARS[i]}):")
    grid = [[' '] * show for _ in range(HEIGHT)]
    for t in range(show):
        r = to_row(tensions[i][t])
        grid[HEIGHT - 1 - r][t] = CHARS[i]
    for row in grid:
        print("  |" + "".join(row) + "|")
    print("  +" + "-" * show + "+")

# ── ASCII: Clone overlay ─────────────────────────────
print("\n── Clone Pair Overlay (. = A, + = B, * = overlap) ──")
grid = [[' '] * show for _ in range(HEIGHT)]
for t in range(show):
    r0 = to_row(tensions[0][t])
    r1 = to_row(tensions[1][t])
    if r0 == r1:
        grid[HEIGHT - 1 - r0][t] = '*'
    else:
        grid[HEIGHT - 1 - r0][t] = '.'
        grid[HEIGHT - 1 - r1][t] = '+'
overlap_count = sum(1 for t in range(show) if to_row(tensions[0][t]) == to_row(tensions[1][t]))
for row in grid:
    print("  |" + "".join(row) + "|")
print("  +" + "-" * show + "+")
print(f"  Pixel overlap: {overlap_count}/{show} ({100*overlap_count/show:.0f}%)")

# ── ASCII: Random pair overlay ────────────────────────
print("\n── Random Pair Overlay (x = C, o = D, * = overlap) ──")
grid = [[' '] * show for _ in range(HEIGHT)]
for t in range(show):
    r2 = to_row(tensions[2][t])
    r3 = to_row(tensions[3][t])
    if r2 == r3:
        grid[HEIGHT - 1 - r2][t] = '*'
    else:
        grid[HEIGHT - 1 - r2][t] = 'x'
        grid[HEIGHT - 1 - r3][t] = 'o'
overlap_rand = sum(1 for t in range(show) if to_row(tensions[2][t]) == to_row(tensions[3][t]))
for row in grid:
    print("  |" + "".join(row) + "|")
print("  +" + "-" * show + "+")
print(f"  Pixel overlap: {overlap_rand}/{show} ({100*overlap_rand/show:.0f}%)")

# ── Verdict ───────────────────────────────────────────
print("\n" + "=" * 60)
print("  VERDICT")
print("=" * 60)
sync_confirmed = corr_clone > 0.99 and corr_rand < 0.5
if sync_confirmed:
    tag = "CONFIRMED"
elif corr_clone > corr_rand + 0.3:
    tag = "PARTIAL — clone sync stronger"
else:
    tag = "NOT CONFIRMED"
print(f"  H367 Resonance Synchronization: {tag}")
print(f"  Clone pair r = {corr_clone:.6f}")
print(f"  Random pair r = {corr_rand:.6f}")
print(f"  Ratio: {corr_clone / max(abs(corr_rand), 1e-9):.1f}x")
print("=" * 60)
