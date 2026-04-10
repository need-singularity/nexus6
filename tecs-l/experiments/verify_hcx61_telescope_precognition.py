#!/usr/bin/env python3
"""H-CX-61 Verification: Gravitational Telescope Precognition — (tension_scale, direction_spread) 2D Observation Space"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from sklearn.metrics import roc_auc_score
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data

def direction_spread(D, Y, n_cls=10):
    """Average cosine distance between class mean directions = spread"""
    means = []
    for c in range(n_cls):
        mask = Y == c
        if mask.sum() > 0:
            m = D[mask].mean(0)
            n = np.linalg.norm(m)
            means.append(m / max(n, 1e-8))
        else:
            means.append(np.zeros(D.shape[1]))
    means = np.array(means)
    # Average pairwise cosine distance
    cos_dists = []
    for i in range(n_cls):
        for j in range(i+1, n_cls):
            cos_dists.append(1 - (means[i] * means[j]).sum())
    return np.mean(cos_dists) if cos_dists else 0

def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()

    print(f"\n{'='*70}")
    print(f"  H-CX-61: Telescope Precognition — {dataset_name.upper()}")
    print(f"{'='*70}")

    trajectory = []  # (epoch, tension_scale, direction_spread, precog_auc, acc)

    for ep in range(epochs):
        model.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()

        model.eval()
        tensions, corrects, dirs_list, ys = [], [], [], []
        with torch.no_grad():
            for x, y in te:
                x_flat = x.view(-1, dim)
                a = model.engine_a(x_flat); g = model.engine_g(x_flat)
                rep = a - g
                d = F.normalize(rep, dim=-1)
                out = model.tension_scale * torch.sqrt((rep**2).mean(-1, keepdim=True) + 1e-8) * d
                pred = out.argmax(1)
                tensions.extend(torch.sqrt((rep**2).mean(-1) + 1e-8).numpy().tolist())
                corrects.extend((pred == y).numpy().tolist())
                dirs_list.append(d.numpy())
                ys.extend(y.numpy().tolist())

        T = np.array(tensions); C = np.array(corrects, dtype=float)
        D = np.concatenate(dirs_list); Y = np.array(ys)
        ts = model.tension_scale.item()
        spread = direction_spread(D, Y)
        auc = roc_auc_score(C, T) if len(np.unique(C)) > 1 else 0.5
        acc = C.mean() * 100
        trajectory.append((ep+1, ts, spread, auc, acc))

    # Print trajectory
    print(f"\n  {'Epoch':>5} {'t_scale':>8} {'spread':>8} {'AUC':>7} {'Acc%':>7}")
    print(f"  {'-'*40}")
    for ep, ts, sp, auc, acc in trajectory:
        print(f"  {ep:>5} {ts:>8.4f} {sp:>8.4f} {auc:>7.4f} {acc:>7.1f}")

    # ASCII trajectory plot
    print(f"\n  Trajectory in (tension_scale, spread) space:")
    ts_vals = [t[1] for t in trajectory]
    sp_vals = [t[2] for t in trajectory]
    auc_vals = [t[3] for t in trajectory]

    ts_min, ts_max = min(ts_vals), max(ts_vals)
    sp_min, sp_max = min(sp_vals), max(sp_vals)

    grid_h, grid_w = 15, 40
    grid = [[' ' for _ in range(grid_w)] for _ in range(grid_h)]

    for i, (ep, ts, sp, auc, acc) in enumerate(trajectory):
        if ts_max > ts_min:
            row = grid_h - 1 - int((ts - ts_min) / (ts_max - ts_min) * (grid_h - 1))
        else:
            row = grid_h // 2
        if sp_max > sp_min:
            col = int((sp - sp_min) / (sp_max - sp_min) * (grid_w - 1))
        else:
            col = grid_w // 2
        row = max(0, min(grid_h-1, row))
        col = max(0, min(grid_w-1, col))
        marker = str(ep+1) if ep < 9 else chr(ord('A') + ep - 9)
        grid[row][col] = marker

    print(f"  t_scale ^")
    for i, row in enumerate(grid):
        ts_label = ts_min + (ts_max - ts_min) * (grid_h - 1 - i) / max(grid_h - 1, 1)
        print(f"  {ts_label:>6.3f} |{''.join(row)}|")
    print(f"  {'':>6} +{'─'*grid_w}→ spread")
    print(f"  {'':>7} {sp_min:.3f}{' '*(grid_w-12)}{sp_max:.3f}")

    # Correlation analysis
    print(f"\n  Correlation analysis:")
    r_ts_auc = np.corrcoef(ts_vals, auc_vals)[0, 1]
    r_sp_auc = np.corrcoef(sp_vals, auc_vals)[0, 1]
    r_product = np.corrcoef(np.array(ts_vals) * np.array(sp_vals), auc_vals)[0, 1]
    print(f"  Corr(t_scale, AUC):         {r_ts_auc:>7.4f}")
    print(f"  Corr(spread, AUC):          {r_sp_auc:>7.4f}")
    print(f"  Corr(t_scale*spread, AUC):  {r_product:>7.4f}  ← telescope product")

    print(f"\n  H-CX-61 prediction (product corr > individual): "
          f"{'SUPPORTED' if abs(r_product) > max(abs(r_ts_auc), abs(r_sp_auc)) else 'REJECTED'}")

    return trajectory[-1][1], trajectory[-1][2], trajectory[-1][3]

if __name__ == '__main__':
    results = {}
    for ds in ['mnist', 'fashion', 'cifar']:
        try:
            ts, sp, auc = run_experiment(ds)
            results[ds] = (ts, sp, auc)
        except Exception as e:
            print(f"  {ds} failed: {e}")
            results[ds] = (0, 0, 0)

    print(f"\n{'='*70}")
    print(f"  H-CX-61 CROSS-DATASET SUMMARY")
    print(f"{'='*70}")
    print(f"  {'Dataset':>10} {'t_scale':>8} {'spread':>8} {'AUC':>7} {'product':>8}")
    print(f"  {'-'*45}")
    for ds, (ts, sp, auc) in results.items():
        print(f"  {ds:>10} {ts:>8.4f} {sp:>8.4f} {auc:>7.4f} {ts*sp:>8.4f}")