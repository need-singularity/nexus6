#!/usr/bin/env python3
"""H367 Extension: Exploring Resonance Transition Points in Partial Similarity Weights

Continuously vary weight similarity from 0→1 to find synchronization transition points.
Kuramoto model prediction: sudden synchronization at K > K_c (phase transition)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn.functional as F
import numpy as np
import copy
from model_pure_field import PureFieldEngine

def interpolate_weights(model_a, model_b, alpha):
    """Interpolate two model weights with alpha. alpha=0→A, alpha=1→B."""
    model_c = copy.deepcopy(model_a)
    with torch.no_grad():
        for pa, pb, pc in zip(model_a.parameters(), model_b.parameters(), model_c.parameters()):
            pc.copy_(pa * (1 - alpha) + pb * alpha)
    return model_c

def measure_sync(model_ref, model_test, inputs, n=100):
    """Correlation of tension time series between two models."""
    t_ref, t_test = [], []
    model_ref.eval(); model_test.eval()
    with torch.no_grad():
        for x in inputs[:n]:
            _, tr = model_ref(x)
            _, tt = model_test(x)
            t_ref.append(tr.mean().item())
            t_test.append(tt.mean().item())
    r = np.corrcoef(t_ref, t_test)[0, 1]
    return r, t_ref, t_test

def weight_cosine(model_a, model_b):
    """Cosine similarity of entire model weights."""
    va = torch.cat([p.flatten() for p in model_a.parameters()])
    vb = torch.cat([p.flatten() for p in model_b.parameters()])
    return F.cosine_similarity(va.unsqueeze(0), vb.unsqueeze(0)).item()

if __name__ == '__main__':
    print("=" * 60)
    print("  H367 Extension: Partial Similarity → Synchronization Transition Point")
    print("=" * 60)

    # 2 reference models (completely independent)
    model_a = PureFieldEngine(784, 128, 10)
    model_b = PureFieldEngine(784, 128, 10)

    # Generate common inputs
    inputs = [torch.randn(1, 784) for _ in range(100)]

    # alpha sweep: 0 (=A) → 1 (=B)
    alphas = [0.0, 0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0]

    print(f"\n  {'alpha':>6} {'cos_sim':>8} {'corr_r':>8} {'sync':>20}")
    print(f"  {'─'*6} {'─'*8} {'─'*8} {'─'*20}")

    results = []
    for alpha in alphas:
        model_c = interpolate_weights(model_a, model_b, alpha)
        cos = weight_cosine(model_a, model_c)
        r, _, _ = measure_sync(model_a, model_c, inputs)

        bar_len = max(0, int(abs(r) * 20))
        bar = '█' * bar_len

        results.append((alpha, cos, r))
        print(f"  {alpha:>6.2f} {cos:>8.4f} {r:>8.4f} {bar}")

    # Search for transition point: first alpha where r exceeds 0.5
    transition = None
    for alpha, cos, r in results:
        if r > 0.5 and transition is None:
            transition = (alpha, cos, r)

    print(f"\n  === ASCII: cosine similarity vs correlation ===")
    print(f"  corr")
    print(f"  1.0 |", end="")
    rows, cols = 12, 30
    grid = [[' ' for _ in range(cols)] for _ in range(rows)]
    for alpha, cos, r in results:
        c = min(int(cos * cols), cols - 1)
        row = rows - 1 - min(int((r + 1) / 2 * rows), rows - 1)
        row = max(0, min(rows - 1, row))
        if 0 <= c < cols:
            grid[row][c] = '●'
    # diagonal guide
    for i in range(min(rows, cols)):
        r_idx = rows - 1 - i
        c_idx = int(i * cols / rows)
        if 0 <= r_idx < rows and 0 <= c_idx < cols and grid[r_idx][c_idx] == ' ':
            grid[r_idx][c_idx] = '·'

    for row in range(rows):
        val = 1.0 - row * 2.0 / (rows - 1)
        line = ''.join(grid[row])
        print(f"  {val:>+4.1f} |{line}|")
    print(f"  -1.0 +{'─' * cols}+")
    print(f"        0.0{' ' * (cols - 6)}1.0")
    print(f"             weight cosine similarity")

    print(f"\n  === Conclusion ===")
    if transition:
        print(f"  Transition point: alpha={transition[0]:.2f}, cos_sim={transition[1]:.4f}, r={transition[2]:.4f}")
        print(f"  → Synchronization starts at weight similarity ≥ {transition[1]:.2f}")
    else:
        print(f"  No transition point — gradual change (not a phase transition)")

    # Kuramoto order parameter
    print(f"\n  === Kuramoto order parameter R ===")
    for alpha, cos, r in results:
        R = max(0, r)  # negative correlations → R=0
        bar = '█' * int(R * 30)
        print(f"  cos={cos:>6.3f}: R={R:.3f} {bar}")