#!/usr/bin/env python3
"""H-CX-63 Verification: Multi-Lens Precognition Interference — Dual vs Quad Precognition AUC Comparison"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from sklearn.metrics import roc_auc_score
from model_pure_field import PureFieldEngine, PureFieldQuad
from calc.direction_analyzer import load_data

def train_and_collect(model, dim, tl, te, epochs=15, name="model"):
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()

    for ep in range(epochs):
        model.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()

    model.eval()
    tensions, corrects, labels, preds = [], [], [], []
    with torch.no_grad():
        for x, y in te:
            out, t = model(x.view(-1, dim))
            pred = out.argmax(1)
            tensions.extend(t.numpy().tolist())
            corrects.extend((pred == y).numpy().tolist())
            labels.extend(y.numpy().tolist())
            preds.extend(pred.numpy().tolist())

    T = np.array(tensions); C = np.array(corrects, dtype=float)
    Y = np.array(labels); P = np.array(preds)

    acc = C.mean() * 100
    auc = roc_auc_score(C, T) if len(np.unique(C)) > 1 else 0.5
    ts = model.tension_scale.item()

    return T, C, Y, P, acc, auc, ts

def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)

    print(f"\n{'='*70}")
    print(f"  H-CX-63: Multi-Lens Precognition — {dataset_name.upper()}")
    print(f"{'='*70}")

    # Dual (2-engine)
    print(f"\n  --- PureFieldEngine (Dual, 2-engine) ---")
    dual = PureFieldEngine(dim, 128, 10)
    dual_params = sum(p.numel() for p in dual.parameters())
    T2, C2, Y2, P2, acc2, auc2, ts2 = train_and_collect(dual, dim, tl, te, epochs)
    print(f"  Params: {dual_params:,}  Acc: {acc2:.1f}%  Precog AUC: {auc2:.4f}  t_scale: {ts2:.4f}")

    # Quad (4-engine)
    print(f"\n  --- PureFieldQuad (Quad, 4-engine) ---")
    quad = PureFieldQuad(dim, 64, 10)  # smaller hidden to match params
    quad_params = sum(p.numel() for p in quad.parameters())
    T4, C4, Y4, P4, acc4, auc4, ts4 = train_and_collect(quad, dim, tl, te, epochs)
    print(f"  Params: {quad_params:,}  Acc: {acc4:.1f}%  Precog AUC: {auc4:.4f}  t_scale: {ts4:.4f}")

    # Comparison
    print(f"\n  {'='*50}")
    print(f"  COMPARISON")
    print(f"  {'='*50}")
    print(f"  {'':>15} {'Dual':>10} {'Quad':>10} {'Delta':>10}")
    print(f"  {'-'*45}")
    print(f"  {'Parameters':>15} {dual_params:>10,} {quad_params:>10,} {quad_params-dual_params:>+10,}")
    print(f"  {'Accuracy':>15} {acc2:>10.1f} {acc4:>10.1f} {acc4-acc2:>+10.1f}")
    print(f"  {'Precog AUC':>15} {auc2:>10.4f} {auc4:>10.4f} {auc4-auc2:>+10.4f}")
    print(f"  {'t_scale':>15} {ts2:>10.4f} {ts4:>10.4f} {ts4-ts2:>+10.4f}")

    # Amplification ratio
    amp = auc4 / auc2 if auc2 > 0 else 0
    print(f"\n  Amplification ratio (Quad/Dual AUC): {amp:.4f}")

    # Per-class comparison
    print(f"\n  Per-class Precognition AUC:")
    print(f"  {'Class':>7} {'Dual':>7} {'Quad':>7} {'Delta':>7} {'Winner':>7}")
    print(f"  {'-'*40}")
    quad_wins = 0
    for c in range(10):
        mask2 = Y2 == c; mask4 = Y4 == c
        auc2c = roc_auc_score(C2[mask2], T2[mask2]) if len(np.unique(C2[mask2])) > 1 else 0.5
        auc4c = roc_auc_score(C4[mask4], T4[mask4]) if len(np.unique(C4[mask4])) > 1 else 0.5
        winner = 'Quad' if auc4c > auc2c else 'Dual'
        if auc4c > auc2c: quad_wins += 1
        print(f"  {names[c]:>7} {auc2c:>7.3f} {auc4c:>7.3f} {auc4c-auc2c:>+7.3f} {winner:>7}")

    print(f"\n  Quad wins {quad_wins}/10 classes")

    # Quad engine pair analysis (6 pairs)
    print(f"\n  --- Quad Engine Pair Tensions ---")
    quad.eval()
    pair_tensions = {f"e{i}-e{j}": [] for i in range(4) for j in range(i+1, 4)}
    all_correct_q = []

    with torch.no_grad():
        for x, y in te:
            x_flat = x.view(-1, dim)
            outs = [e(x_flat) for e in quad.engines]
            pred_out, _ = quad(x_flat)
            pred = pred_out.argmax(1)
            all_correct_q.extend((pred == y).numpy().tolist())

            for i in range(4):
                for j in range(i+1, 4):
                    pair_t = ((outs[i] - outs[j])**2).mean(-1)
                    pair_tensions[f"e{i}-e{j}"].extend(pair_t.numpy().tolist())

    C_q = np.array(all_correct_q, dtype=float)
    print(f"  {'Pair':>7} {'Mean_T':>8} {'Precog_AUC':>11} {'Type':>10}")
    print(f"  {'-'*40}")

    direct_pairs = ['e0-e2', 'e1-e3']  # A-G, E-F analog
    cross_pairs = ['e0-e1', 'e0-e3', 'e1-e2', 'e2-e3']

    direct_aucs, cross_aucs = [], []
    for pair_name, pair_t in pair_tensions.items():
        pt = np.array(pair_t)
        p_auc = roc_auc_score(C_q, pt) if len(np.unique(C_q)) > 1 else 0.5
        ptype = 'DIRECT' if pair_name in direct_pairs else 'CROSS'
        if ptype == 'DIRECT':
            direct_aucs.append(p_auc)
        else:
            cross_aucs.append(p_auc)
        print(f"  {pair_name:>7} {pt.mean():>8.3f} {p_auc:>11.4f} {ptype:>10}")

    mean_direct = np.mean(direct_aucs) if direct_aucs else 0
    mean_cross = np.mean(cross_aucs) if cross_aucs else 0
    print(f"\n  Mean direct AUC: {mean_direct:.4f}")
    print(f"  Mean cross AUC:  {mean_cross:.4f}")
    print(f"  H-CX-63 prediction (cross > direct): {'SUPPORTED' if mean_cross > mean_direct else 'REJECTED'}")

    # Interference pattern: correlation between pair tensions
    print(f"\n  Pair tension correlation matrix:")
    pair_names = list(pair_tensions.keys())
    pair_arrays = [np.array(pair_tensions[p]) for p in pair_names]
    corr_mat = np.corrcoef(pair_arrays)

    print(f"  {'':>7}", end='')
    for p in pair_names: print(f" {p:>7}", end='')
    print()
    for i, p in enumerate(pair_names):
        print(f"  {p:>7}", end='')
        for j in range(len(pair_names)):
            print(f" {corr_mat[i,j]:>7.3f}", end='')
        print()

    return auc2, auc4, amp

if __name__ == '__main__':
    results = {}
    for ds in ['mnist', 'fashion', 'cifar']:
        try:
            auc2, auc4, amp = run_experiment(ds)
            results[ds] = (auc2, auc4, amp)
        except Exception as e:
            print(f"  {ds} failed: {e}")
            results[ds] = (0, 0, 0)

    print(f"\n{'='*70}")
    print(f"  H-CX-63 CROSS-DATASET SUMMARY")
    print(f"{'='*70}")
    print(f"  {'Dataset':>10} {'Dual_AUC':>9} {'Quad_AUC':>9} {'Amp':>7} {'Winner':>7}")
    print(f"  {'-'*45}")
    for ds, (a2, a4, amp) in results.items():
        winner = 'Quad' if a4 > a2 else 'Dual'
        print(f"  {ds:>10} {a2:>9.4f} {a4:>9.4f} {amp:>7.4f} {winner:>7}")