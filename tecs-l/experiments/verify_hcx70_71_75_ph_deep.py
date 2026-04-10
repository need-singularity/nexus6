#!/usr/bin/env python3
"""H-CX-70 + H-CX-71 + H-CX-75 Verification: PH Deep — Classifier, Time Axis, Aberration-Phase

H-CX-70: merge distance for confusion pair Precision@K
H-CX-71: epoch-wise merge order stability (Kendall tau)
H-CX-75: min_merge_dist vs class AUC
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr, kendalltau
from ripser import ripser
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data


def get_merge_events(D, Y, n_cls=10):
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
    cos_dist = np.clip(1 - means @ means.T, 0, 2)
    np.fill_diagonal(cos_dist, 0)

    # Single-linkage merge tracking
    sorted_edges = []
    for i in range(n_cls):
        for j in range(i+1, n_cls):
            sorted_edges.append((cos_dist[i, j], i, j))
    sorted_edges.sort()

    parent = list(range(n_cls))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        a, b = find(a), find(b)
        if a != b: parent[a] = b; return True
        return False

    merge_events = []
    for dist, i, j in sorted_edges:
        if union(i, j):
            merge_events.append((dist, min(i,j), max(i,j)))
    return merge_events, cos_dist


def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()
    n_cls = len(names)

    print(f"\n{'='*70}")
    print(f"  H-CX-70+71+75: PH Deep — {dataset_name.upper()}")
    print(f"{'='*70}")

    epoch_merges = []
    epoch_data = []

    for ep in range(epochs):
        model.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()

        model.eval()
        dirs_list, ys, mags, corrects, preds_list = [], [], [], [], []
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
                mags.extend(mag.numpy().tolist()); corrects.extend((pred==y).numpy().tolist())
                preds_list.extend(pred.numpy().tolist())

        D = np.concatenate(dirs_list); Y = np.array(ys)
        M = np.array(mags); C = np.array(corrects, dtype=float); P = np.array(preds_list)
        acc = C.mean() * 100

        merges, cos_dist = get_merge_events(D, Y, n_cls)
        epoch_merges.append(merges)
        epoch_data.append((ep+1, acc, D, Y, M, C, P, cos_dist))

        if (ep+1) % 5 == 0:
            print(f"  Epoch {ep+1}: acc={acc:.1f}%")

    # Final epoch data
    ep_f, acc_f, D_f, Y_f, M_f, C_f, P_f, cos_dist_f = epoch_data[-1]
    merges_f = epoch_merges[-1]

    # Confusion matrix
    conf_matrix = np.zeros((n_cls, n_cls), dtype=int)
    wrong_mask = P_f != Y_f
    for idx in np.where(wrong_mask)[0]:
        conf_matrix[Y_f[idx], P_f[idx]] += 1

    pair_confusion = {}
    for i in range(n_cls):
        for j in range(i+1, n_cls):
            pair_confusion[(i,j)] = conf_matrix[i,j] + conf_matrix[j,i]

    # === H-CX-70: Precision@K ===
    print(f"\n  === H-CX-70: PH Confusion Classifier ===")

    # Merge distance for all pairs
    pair_merge_dist = {}
    for dist, i, j in merges_f:
        pair_merge_dist[(i,j)] = dist

    # Sort pairs by merge distance (closest first = predicted confusion)
    sorted_by_merge = sorted(pair_merge_dist.items(), key=lambda x: x[1])
    sorted_by_conf = sorted(pair_confusion.items(), key=lambda x: -x[1])

    # Top-K confusion pairs (by frequency)
    total_confusion = sum(pair_confusion.values())
    cumulative = 0
    top_conf_set = set()
    for pair, cnt in sorted_by_conf:
        cumulative += cnt
        top_conf_set.add(pair)
        if cumulative >= total_confusion * 0.5:  # top 50% of confusion
            break

    print(f"  Top confusion pairs (50% of all errors): {len(top_conf_set)}")

    # Precision@K for K=3,5,7
    for K in [3, 5, 7, 9]:
        predicted_top = set(p for p, d in sorted_by_merge[:K])
        actual_top = set(p for p, c in sorted_by_conf[:K])
        precision = len(predicted_top & actual_top) / K
        recall = len(predicted_top & top_conf_set) / len(top_conf_set) if top_conf_set else 0
        print(f"  Precision@{K}: {precision:.2f}  Recall@{K}: {recall:.2f}  "
              f"({len(predicted_top & actual_top)}/{K} correct)")

    # Early prediction: epoch 5 merge → epoch 15 confusion
    print(f"\n  Early prediction (epoch 5 → epoch 15):")
    if len(epoch_merges) >= 5:
        merges_ep5 = epoch_merges[4]  # epoch 5
        sorted_ep5 = sorted([(d, (i,j)) for d,i,j in merges_ep5])
        for K in [3, 5]:
            pred_ep5 = set(p for d, p in sorted_ep5[:K])
            actual = set(p for p, c in sorted_by_conf[:K])
            prec = len(pred_ep5 & actual) / K
            print(f"  Epoch5→15 Precision@{K}: {prec:.2f}")

    # === H-CX-71: Merge order stability (Kendall tau) ===
    print(f"\n  === H-CX-71: Merge Order Stability ===")

    # Convert merge events to pair rank ordering
    def merge_to_rank(merges):
        return [(i,j) for d,i,j in sorted(merges, key=lambda x: x[0])]

    final_rank = merge_to_rank(merges_f)

    print(f"  {'Epoch':>5} {'tau_vs_final':>13} {'tau_vs_prev':>13} {'Acc%':>6}")
    print(f"  {'-'*40}")
    prev_rank = None
    taus_vs_final = []
    for ep_idx in range(len(epoch_merges)):
        rank = merge_to_rank(epoch_merges[ep_idx])
        # Kendall tau vs final
        # Convert to numeric ranks for comparison
        final_order = {p: i for i, p in enumerate(final_rank)}
        current_vals = [final_order.get(p, 99) for p in rank]
        tau_f, _ = kendalltau(list(range(len(rank))), current_vals)

        tau_p = 0
        if prev_rank is not None:
            prev_order = {p: i for i, p in enumerate(prev_rank)}
            prev_vals = [prev_order.get(p, 99) for p in rank]
            tau_p, _ = kendalltau(list(range(len(rank))), prev_vals)

        taus_vs_final.append(tau_f)
        acc_ep = epoch_data[ep_idx][1]

        if (ep_idx+1) % 3 == 0 or ep_idx == 0 or ep_idx == len(epoch_merges)-1:
            print(f"  {ep_idx+1:>5} {tau_f:>13.4f} {tau_p:>13.4f} {acc_ep:>6.1f}")
        prev_rank = rank

    # Stability threshold
    stable_epoch = None
    for i, tau in enumerate(taus_vs_final):
        if tau > 0.8 and all(t > 0.8 for t in taus_vs_final[i:]):
            stable_epoch = i + 1
            break
    print(f"\n  Stability epoch (tau > 0.8 sustained): {stable_epoch if stable_epoch else 'not reached'}")
    print(f"  Epoch 5 tau vs final: {taus_vs_final[4]:.4f}" if len(taus_vs_final) > 4 else "")
    print(f"  H-CX-71 prediction (ep5 tau > 0.8): {'SUPPORTED' if len(taus_vs_final) > 4 and taus_vs_final[4] > 0.8 else 'REJECTED'}")

    # ASCII tau trajectory
    print(f"\n  Tau vs final trajectory:")
    for i, tau in enumerate(taus_vs_final):
        bar = int(max(0, tau) * 30)
        print(f"  ep{i+1:>2} |{'█'*bar}{'░'*(30-bar)}| {tau:.3f}")

    # === H-CX-75: min_merge_dist vs class AUC ===
    print(f"\n  === H-CX-75: Aberration-Merge Alignment ===")

    # Per-class min merge distance and AUC
    class_min_dist = []
    for c in range(n_cls):
        dists = cos_dist_f[c].copy(); dists[c] = 999
        class_min_dist.append(np.min(dists))

    class_aucs = []
    for c in range(n_cls):
        mask = Y_f == c
        if mask.sum() > 10 and len(np.unique(C_f[mask])) > 1:
            class_aucs.append(roc_auc_score(C_f[mask], M_f[mask]))
        else:
            class_aucs.append(0.5)

    r_75, p_75 = spearmanr(class_min_dist, class_aucs)
    print(f"  Spearman(min_merge_dist, AUC): r={r_75:.4f}, p={p_75:.4f}")
    print(f"  H-CX-75 (r > 0.5): {'SUPPORTED' if r_75 > 0.5 else 'PARTIAL' if r_75 > 0.3 else 'REJECTED'}")
    # Note: H-CX-65 used isolation (same as min_dist), so compare
    print(f"  (Note: same metric as H-CX-65 isolation — expecting similar result)")

    print(f"\n  {'Class':>7} {'min_dist':>9} {'AUC':>7}")
    print(f"  {'-'*25}")
    for c in range(n_cls):
        print(f"  {names[c]:>7} {class_min_dist[c]:>9.4f} {class_aucs[c]:>7.3f}")

    return {
        'prec_at_5': len(set(p for p,d in sorted_by_merge[:5]) & set(p for p,c in sorted_by_conf[:5])) / 5,
        'stable_epoch': stable_epoch,
        'tau_ep5': taus_vs_final[4] if len(taus_vs_final) > 4 else 0,
        'r_75': r_75,
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
    for ds, r in results.items():
        print(f"  {ds}: P@5={r['prec_at_5']:.2f}, stable_ep={r['stable_epoch']}, "
              f"tau_ep5={r['tau_ep5']:.3f}, r_75={r['r_75']:.3f}")