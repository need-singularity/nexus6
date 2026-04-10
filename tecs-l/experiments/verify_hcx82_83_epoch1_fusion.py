#!/usr/bin/env python3
"""H-CX-82 + H-CX-83 verification: Epoch1 confusion map + orthogonality-topology integration

H-CX-82: Epoch 1 PH merge → Epoch 15 confusion prediction
H-CX-83: LR(mag,conf,gap,H0_total) → AUC > 0.95?
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from scipy.stats import spearmanr
from ripser import ripser
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data


def get_merge_and_h0(D, Y, n_cls=10):
    means = []
    for c in range(n_cls):
        mask = Y == c
        if mask.sum() > 0:
            m = D[mask].mean(0); n = np.linalg.norm(m)
            means.append(m / max(n, 1e-8))
        else:
            means.append(np.zeros(D.shape[1]))
    means = np.array(means)
    cos_dist = np.clip(1 - means @ means.T, 0, 2)
    np.fill_diagonal(cos_dist, 0)

    # Merge events
    sorted_edges = sorted([(cos_dist[i,j], min(i,j), max(i,j))
                           for i in range(n_cls) for j in range(i+1, n_cls)])
    parent = list(range(n_cls))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a, b):
        a, b = find(a), find(b)
        if a != b: parent[a] = b; return True
        return False
    merges = []
    for dist, i, j in sorted_edges:
        if union(i, j): merges.append((dist, i, j))

    # H0 total
    result = ripser(cos_dist, maxdim=0, distance_matrix=True)
    h0 = result['dgms'][0]
    h0_finite = h0[h0[:, 1] < np.inf]
    h0_total = np.sum(h0_finite[:, 1] - h0_finite[:, 0]) if len(h0_finite) > 0 else 0

    return merges, h0_total, cos_dist


def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()
    n_cls = len(names)

    print(f"\n{'='*70}")
    print(f"  H-CX-82+83: Epoch1 Map + Fusion — {dataset_name.upper()}")
    print(f"{'='*70}")

    epoch_merges = []
    epoch_h0 = []

    for ep in range(epochs):
        model.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()

        model.eval()
        dirs_list, ys, mags_list, corrects, preds_list = [], [], [], [], []
        with torch.no_grad():
            for x, y in te:
                x_flat = x.view(-1, dim)
                a = model.engine_a(x_flat); g = model.engine_g(x_flat)
                rep = a - g
                mag = torch.sqrt((rep**2).mean(-1))
                d = F.normalize(rep, dim=-1)
                out = model.tension_scale * mag.unsqueeze(-1) * d
                pred = out.argmax(1)
                dirs_list.append(d.numpy()); ys.extend(y.numpy().tolist())
                mags_list.extend(mag.numpy().tolist())
                corrects.extend((pred==y).numpy().tolist())
                preds_list.extend(pred.numpy().tolist())

        D = np.concatenate(dirs_list); Y = np.array(ys)
        M = np.array(mags_list); C = np.array(corrects, dtype=float); P = np.array(preds_list)

        merges, h0t, _ = get_merge_and_h0(D, Y, n_cls)
        epoch_merges.append(merges)
        epoch_h0.append(h0t)

        if (ep+1) % 5 == 0 or ep == 0:
            print(f"  Epoch {ep+1}: acc={C.mean()*100:.1f}%  H0={h0t:.4f}")

    # Final confusion matrix
    conf_matrix = np.zeros((n_cls, n_cls), dtype=int)
    wrong_mask = P != Y
    for idx in np.where(wrong_mask)[0]:
        conf_matrix[Y[idx], P[idx]] += 1
    pair_confusion = {}
    for i in range(n_cls):
        for j in range(i+1, n_cls):
            pair_confusion[(i,j)] = conf_matrix[i,j] + conf_matrix[j,i]
    sorted_conf = sorted(pair_confusion.items(), key=lambda x: -x[1])

    # === H-CX-82: Epoch 1 prediction ===
    print(f"\n  === H-CX-82: Epoch 1 PH → Final Confusion ===")

    for check_ep in [1, 2, 3, 5]:
        if check_ep > len(epoch_merges): continue
        ep_merges = epoch_merges[check_ep - 1]
        merge_dists = [(d, (min(i,j), max(i,j))) for d,i,j in ep_merges]
        merge_dists.sort()

        # Spearman: merge dist vs confusion
        merge_conf_pairs = []
        for d, pair in merge_dists:
            merge_conf_pairs.append((d, pair_confusion.get(pair, 0)))

        dists_arr = [x[0] for x in merge_conf_pairs]
        confs_arr = [x[1] for x in merge_conf_pairs]
        r, p = spearmanr(dists_arr, confs_arr)

        # P@K
        pred_top3 = set(p for d, p in merge_dists[:3])
        actual_top3 = set(p for p, c in sorted_conf[:3])
        p_at_3 = len(pred_top3 & actual_top3) / 3

        pred_top5 = set(p for d, p in merge_dists[:5])
        actual_top5 = set(p for p, c in sorted_conf[:5])
        p_at_5 = len(pred_top5 & actual_top5) / 5

        print(f"  Epoch {check_ep}: Spearman r={r:.4f} p={p:.4f}  P@3={p_at_3:.2f}  P@5={p_at_5:.2f}")

    # Epoch 1 merge order
    ep1_merges = epoch_merges[0]
    print(f"\n  Epoch 1 merge order:")
    for dist, i, j in sorted(ep1_merges, key=lambda x: x[0]):
        conf = pair_confusion.get((min(i,j), max(i,j)), 0)
        print(f"    {names[i]:>6}-{names[j]:<6} dist={dist:.4f}  final_confusion={conf}")

    # === H-CX-83: 4-feature fusion ===
    print(f"\n  === H-CX-83: Orthogonality-Topology Fusion ===")

    # Collect final features
    class_means = np.zeros((n_cls, D.shape[1]))
    for c in range(n_cls):
        mask = (Y == c) & (C == 1)
        if mask.sum() > 0: class_means[c] = D[mask].mean(0)
    norms = np.linalg.norm(class_means, axis=1, keepdims=True)
    class_means_n = class_means / np.clip(norms, 1e-8, None)

    dir_conf = np.array([(D[i] * class_means_n[int(P[i])]).sum() for i in range(len(D))])
    dir_gap = np.zeros(len(D))
    for i in range(len(D)):
        cosines = [(D[i] * class_means_n[c]).sum() for c in range(n_cls)]
        s = sorted(cosines, reverse=True)
        dir_gap[i] = s[0] - s[1]

    # Per-sample H0-proxy: distance to nearest class boundary
    # Use cosine distance to nearest non-predicted class mean
    h0_proxy = np.zeros(len(D))
    for i in range(len(D)):
        pred_c = int(P[i])
        min_dist = 999
        for c in range(n_cls):
            if c != pred_c:
                d = 1 - (D[i] * class_means_n[c]).sum()
                if d < min_dist: min_dist = d
        h0_proxy[i] = min_dist

    # 3-feature baseline
    X3 = np.column_stack([
        (M - M.mean()) / (M.std() + 1e-8),
        (dir_conf - dir_conf.mean()) / (dir_conf.std() + 1e-8),
        (dir_gap - dir_gap.mean()) / (dir_gap.std() + 1e-8),
    ])
    cv3 = cross_val_score(LogisticRegression(max_iter=1000), X3, C, cv=5, scoring='roc_auc')
    auc3 = cv3.mean()

    # 4-feature with H0 proxy
    X4 = np.column_stack([X3, (h0_proxy - h0_proxy.mean()) / (h0_proxy.std() + 1e-8)])
    cv4 = cross_val_score(LogisticRegression(max_iter=1000), X4, C, cv=5, scoring='roc_auc')
    auc4 = cv4.mean()

    # 5-feature with epoch H0 total (broadcast)
    h0_final = epoch_h0[-1]
    X5 = np.column_stack([X4, np.full(len(D), h0_final)])
    cv5 = cross_val_score(LogisticRegression(max_iter=1000), X5, C, cv=5, scoring='roc_auc')
    auc5 = cv5.mean()

    print(f"  3-feat (mag,conf,gap):          AUC={auc3:.4f} (±{cv3.std():.4f})")
    print(f"  4-feat (+h0_proxy):             AUC={auc4:.4f} (±{cv4.std():.4f})")
    print(f"  5-feat (+H0_total):             AUC={auc5:.4f} (±{cv5.std():.4f})")
    print(f"  Gain from h0_proxy:             {auc4-auc3:+.4f}")
    print(f"  H-CX-83 target (>0.95):         {'ACHIEVED' if auc4 > 0.95 else 'NOT YET' if auc4 > 0.92 else 'MISSED'}")

    # Feature correlation with H0 proxy
    corrs = [np.corrcoef(M, h0_proxy)[0,1],
             np.corrcoef(dir_conf, h0_proxy)[0,1],
             np.corrcoef(dir_gap, h0_proxy)[0,1]]
    print(f"\n  h0_proxy correlations:")
    print(f"    with mag:      {corrs[0]:.4f}")
    print(f"    with dir_conf: {corrs[1]:.4f}")
    print(f"    with dir_gap:  {corrs[2]:.4f}")
    print(f"    mean |corr|:   {np.mean(np.abs(corrs)):.4f} ({'independent' if np.mean(np.abs(corrs)) < 0.3 else 'correlated'})")

    return {
        'ep1_r': spearmanr([x[0] for x in [(d, pair_confusion.get((min(i,j),max(i,j)),0)) for d,i,j in epoch_merges[0]]],
                          [x[1] for x in [(d, pair_confusion.get((min(i,j),max(i,j)),0)) for d,i,j in epoch_merges[0]]])[0],
        'auc3': auc3, 'auc4': auc4, 'gain': auc4 - auc3,
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
    print(f"  Round 5 SUMMARY")
    print(f"{'='*70}")
    for ds, r in results.items():
        print(f"  {ds}: ep1_r={r['ep1_r']:.3f}, AUC3={r['auc3']:.4f}, AUC4={r['auc4']:.4f}, gain={r['gain']:+.4f}")