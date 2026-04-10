#!/usr/bin/env python3
"""H-CX-67 + H-CX-68 Verification: Synergy Golden Zone + Precognition Conservation Law

H-CX-67: Integrated precognition synergy is maximum in the mid-tension range
H-CX-68: mag_AUC + dir_AUC ≈ const (conservation law)
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data


def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()
    n_cls = len(names)

    print(f"\n{'='*70}")
    print(f"  H-CX-67 + H-CX-68: Synergy & Conservation — {dataset_name.upper()}")
    print(f"{'='*70}")

    for ep in range(epochs):
        model.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()
        if (ep+1) % 5 == 0:
            model.eval(); correct = total = 0
            with torch.no_grad():
                for x, y in te:
                    o, _ = model(x.view(-1, dim))
                    correct += (o.argmax(1)==y).sum().item(); total += y.size(0)
            print(f"  Epoch {ep+1}: acc={correct/total*100:.1f}%")

    # Collect features
    model.eval()
    all_mag, all_dir, all_y, all_pred = [], [], [], []
    with torch.no_grad():
        for x, y in te:
            x_flat = x.view(-1, dim)
            a = model.engine_a(x_flat); g = model.engine_g(x_flat)
            rep = a - g
            mag = torch.sqrt((rep**2).mean(-1))
            d = F.normalize(rep, dim=-1)
            out = model.tension_scale * mag.unsqueeze(-1) * d
            pred = out.argmax(1)
            all_mag.append(mag.numpy()); all_dir.append(d.numpy())
            all_y.append(y.numpy()); all_pred.append(pred.numpy())

    M = np.concatenate(all_mag); D = np.concatenate(all_dir)
    Y = np.concatenate(all_y); P = np.concatenate(all_pred)
    correct = (P == Y).astype(float)

    # Class mean directions
    class_means = np.zeros((n_cls, D.shape[1]))
    for c in range(n_cls):
        mask = (Y == c) & (P == c)
        if mask.sum() > 0:
            class_means[c] = D[mask].mean(0)
    norms = np.linalg.norm(class_means, axis=1, keepdims=True)
    class_means_n = class_means / np.clip(norms, 1e-8, None)

    # Direction confidence
    dir_conf = np.array([(D[i] * class_means_n[P[i]]).sum() for i in range(len(D))])
    # Direction gap
    dir_gap = np.zeros(len(D))
    for i in range(len(D)):
        cosines = [(D[i] * class_means_n[c]).sum() for c in range(n_cls)]
        s = sorted(cosines, reverse=True)
        dir_gap[i] = s[0] - s[1]

    # === H-CX-67: Quintile Synergy ===
    print(f"\n  === H-CX-67: Quintile Synergy Analysis ===")

    quintiles = np.percentile(M, [0, 20, 40, 60, 80, 100])
    print(f"  {'Quintile':>10} {'N':>5} {'mag_AUC':>8} {'dir_AUC':>8} {'gap_AUC':>8} {'LR_AUC':>7} {'Synergy':>8}")
    print(f"  {'-'*55}")

    synergies = []
    q_mids = []
    for i in range(5):
        lo, hi = quintiles[i], quintiles[i+1]
        mask = (M >= lo) & (M <= hi + (0.001 if i == 4 else 0))
        n = mask.sum()
        if n < 30 or len(np.unique(correct[mask])) < 2:
            synergies.append(0)
            q_mids.append((lo+hi)/2)
            continue

        m_auc = roc_auc_score(correct[mask], M[mask])
        d_auc = roc_auc_score(correct[mask], dir_conf[mask]) if len(np.unique(correct[mask])) > 1 else 0.5
        g_auc = roc_auc_score(correct[mask], dir_gap[mask]) if len(np.unique(correct[mask])) > 1 else 0.5

        # LR on quintile
        X_q = np.column_stack([
            (M[mask] - M[mask].mean()) / (M[mask].std() + 1e-8),
            (dir_conf[mask] - dir_conf[mask].mean()) / (dir_conf[mask].std() + 1e-8),
            (dir_gap[mask] - dir_gap[mask].mean()) / (dir_gap[mask].std() + 1e-8),
        ])
        try:
            lr = LogisticRegression(max_iter=1000)
            lr.fit(X_q, correct[mask])
            lr_prob = lr.predict_proba(X_q)[:, 1]
            lr_auc = roc_auc_score(correct[mask], lr_prob)
        except:
            lr_auc = max(m_auc, d_auc)

        best_ind = max(m_auc, d_auc, g_auc)
        synergy = lr_auc - best_ind
        synergies.append(synergy)
        q_mids.append((lo + hi) / 2)

        print(f"  Q{i+1} [{lo:>6.1f},{hi:>6.1f}] {n:>5} {m_auc:>8.3f} {d_auc:>8.3f} {g_auc:>8.3f} {lr_auc:>7.3f} {synergy:>+8.3f}")

    # Where is max synergy?
    max_syn_q = np.argmax(synergies)
    print(f"\n  Max synergy at Q{max_syn_q+1} (mid-tension={q_mids[max_syn_q]:.2f})")
    t_range = quintiles[-1] - quintiles[0]
    relative_pos = (q_mids[max_syn_q] - quintiles[0]) / t_range if t_range > 0 else 0
    print(f"  Relative position in tension range: {relative_pos:.4f}")
    print(f"  Golden zone center (1/e): {1/np.e:.4f}")
    print(f"  Delta from 1/e: {abs(relative_pos - 1/np.e):.4f}")
    print(f"  H-CX-67 (mid-Q max synergy): {'SUPPORTED' if max_syn_q in [1, 2, 3] else 'REJECTED'}")

    # ASCII synergy by quintile
    print(f"\n  Synergy by Quintile:")
    max_s = max(abs(s) for s in synergies) if synergies else 1
    for i, s in enumerate(synergies):
        bar = int(abs(s) / max_s * 30) if max_s > 0 else 0
        sign = '+' if s > 0 else '-'
        marker = ' ← MAX' if i == max_syn_q else ''
        print(f"  Q{i+1} |{'█'*bar}{'░'*(30-bar)}| {s:>+.4f}{marker}")

    # === H-CX-68: Conservation Law ===
    print(f"\n  === H-CX-68: Precognition Conservation ===")

    mag_aucs, dir_aucs = [], []
    for c in range(n_cls):
        mask = Y == c
        if mask.sum() < 10 or len(np.unique(correct[mask])) < 2:
            mag_aucs.append(0.5); dir_aucs.append(0.5)
            continue
        m_auc = roc_auc_score(correct[mask], M[mask])
        d_auc = roc_auc_score(correct[mask], dir_conf[mask])
        mag_aucs.append(m_auc)
        dir_aucs.append(d_auc)

    mag_arr = np.array(mag_aucs)
    dir_arr = np.array(dir_aucs)
    sum_arr = mag_arr + dir_arr
    prod_arr = mag_arr * dir_arr

    cv_mag = np.std(mag_arr) / np.mean(mag_arr) if np.mean(mag_arr) > 0 else 999
    cv_dir = np.std(dir_arr) / np.mean(dir_arr) if np.mean(dir_arr) > 0 else 999
    cv_sum = np.std(sum_arr) / np.mean(sum_arr) if np.mean(sum_arr) > 0 else 999
    cv_prod = np.std(prod_arr) / np.mean(prod_arr) if np.mean(prod_arr) > 0 else 999

    print(f"  Per-class AUC breakdown:")
    print(f"  {'Class':>7} {'mag_AUC':>8} {'dir_AUC':>8} {'Sum':>8} {'Product':>8}")
    print(f"  {'-'*42}")
    for c in range(n_cls):
        print(f"  {names[c]:>7} {mag_arr[c]:>8.3f} {dir_arr[c]:>8.3f} {sum_arr[c]:>8.3f} {prod_arr[c]:>8.3f}")

    print(f"\n  Variability (CV = std/mean):")
    print(f"  {'Metric':>12} {'CV':>8} {'Std':>8} {'Mean':>8}")
    print(f"  {'-'*38}")
    print(f"  {'mag_AUC':>12} {cv_mag:>8.4f} {np.std(mag_arr):>8.4f} {np.mean(mag_arr):>8.4f}")
    print(f"  {'dir_AUC':>12} {cv_dir:>8.4f} {np.std(dir_arr):>8.4f} {np.mean(dir_arr):>8.4f}")
    print(f"  {'Sum':>12} {cv_sum:>8.4f} {np.std(sum_arr):>8.4f} {np.mean(sum_arr):>8.4f}")
    print(f"  {'Product':>12} {cv_prod:>8.4f} {np.std(prod_arr):>8.4f} {np.mean(prod_arr):>8.4f}")

    # Tradeoff correlation
    r_tradeoff = np.corrcoef(mag_arr, dir_arr)[0, 1]
    print(f"\n  Corr(mag_AUC, dir_AUC): {r_tradeoff:.4f}")
    print(f"  Tradeoff (r < 0): {'YES' if r_tradeoff < 0 else 'NO'}")

    # Conservation check
    conservation_sum = cv_sum < min(cv_mag, cv_dir)
    conservation_prod = cv_prod < min(cv_mag, cv_dir)
    print(f"\n  Sum conservation (CV_sum < CV_individual): {'SUPPORTED' if conservation_sum else 'REJECTED'}")
    print(f"  Product conservation (CV_prod < CV_individual): {'SUPPORTED' if conservation_prod else 'REJECTED'}")
    print(f"  H-CX-68 overall: {'SUPPORTED' if conservation_sum or conservation_prod else 'REJECTED'}")

    return {
        'max_syn_q': max_syn_q,
        'relative_pos': relative_pos,
        'cv_sum': cv_sum,
        'cv_mag': cv_mag,
        'cv_dir': cv_dir,
        'r_tradeoff': r_tradeoff,
        'conservation_sum': conservation_sum,
    }

if __name__ == '__main__':
    results = {}
    for ds in ['mnist', 'fashion', 'cifar']:
        try:
            results[ds] = run_experiment(ds)
        except Exception as e:
            print(f"  {ds} failed: {e}")
            import traceback; traceback.print_exc()

    print(f"\n{'='*70}")
    print(f"  CROSS-DATASET SUMMARY")
    print(f"{'='*70}")
    print(f"\n  H-CX-67 (Synergy Golden Zone):")
    for ds, r in results.items():
        print(f"    {ds}: max synergy at Q{r['max_syn_q']+1}, relative pos={r['relative_pos']:.4f} (1/e={1/np.e:.4f})")

    print(f"\n  H-CX-68 (Conservation):")
    for ds, r in results.items():
        print(f"    {ds}: CV_sum={r['cv_sum']:.4f} < CV_mag={r['cv_mag']:.4f}? {r['conservation_sum']}, tradeoff r={r['r_tradeoff']:.4f}")