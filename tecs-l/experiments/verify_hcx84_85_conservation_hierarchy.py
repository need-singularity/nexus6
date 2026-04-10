#!/usr/bin/env python3
"""H-CX-84 + H-CX-85 Verification: Conservation→Synergy Condition + dendrogram hierarchy

H-CX-84: CV(ts×H0) vs synergy negative correlation
H-CX-85: dendrogram subtree = semantic category
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from ripser import ripser
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data


def compute_h0_total(D, Y, n_cls=10):
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
    result = ripser(cos_dist, maxdim=0, distance_matrix=True)
    h0 = result['dgms'][0]
    h0_finite = h0[h0[:, 1] < np.inf]
    return np.sum(h0_finite[:, 1] - h0_finite[:, 0]) if len(h0_finite) > 0 else 0


def build_dendrogram(D, Y, names, n_cls=10):
    """Single-linkage dendrogram from cosine distance."""
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

    # Single-linkage clustering
    sorted_edges = sorted([(cos_dist[i,j], i, j) for i in range(n_cls) for j in range(i+1, n_cls)])

    parent = list(range(n_cls))
    clusters = {i: {i} for i in range(n_cls)}

    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x

    merge_history = []
    for dist, i, j in sorted_edges:
        ri, rj = find(i), find(j)
        if ri != rj:
            # Merge clusters
            merged = clusters[ri] | clusters[rj]
            parent[ri] = rj
            clusters[rj] = merged
            if ri in clusters and ri != rj: del clusters[ri]
            cluster_names = sorted([names[c] for c in merged])
            merge_history.append((dist, cluster_names))

    return merge_history, cos_dist


def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()
    n_cls = len(names)

    print(f"\n{'='*70}")
    print(f"  H-CX-84+85: Conservation & Hierarchy — {dataset_name.upper()}")
    print(f"{'='*70}")

    ts_list, h0_list = [], []

    for ep in range(epochs):
        model.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()

        if (ep+1) % 3 == 0 or ep == 0:
            model.eval()
            dirs_list, ys = [], []
            with torch.no_grad():
                for x, y in te:
                    x_flat = x.view(-1, dim)
                    rep = model.engine_a(x_flat) - model.engine_g(x_flat)
                    d = F.normalize(rep, dim=-1)
                    dirs_list.append(d.numpy()); ys.extend(y.numpy().tolist())
            D = np.concatenate(dirs_list); Y = np.array(ys)
            h0 = compute_h0_total(D, Y)
            ts = model.tension_scale.item()
            ts_list.append(ts); h0_list.append(h0)

        if (ep+1) % 5 == 0:
            model.eval(); correct = total = 0
            with torch.no_grad():
                for x, y in te:
                    o, _ = model(x.view(-1, dim))
                    correct += (o.argmax(1)==y).sum().item(); total += y.size(0)
            print(f"  Epoch {ep+1}: acc={correct/total*100:.1f}%")

    # Final features for synergy
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

    # Compute synergy
    class_means = np.zeros((n_cls, D.shape[1]))
    for c in range(n_cls):
        mask = (Y == c) & (correct == 1)
        if mask.sum() > 0: class_means[c] = D[mask].mean(0)
    norms = np.linalg.norm(class_means, axis=1, keepdims=True)
    class_means_n = class_means / np.clip(norms, 1e-8, None)

    dir_conf = np.array([(D[i] * class_means_n[int(P[i])]).sum() for i in range(len(D))])
    dir_gap = np.zeros(len(D))
    for i in range(len(D)):
        cosines = [(D[i] * class_means_n[c]).sum() for c in range(n_cls)]
        s = sorted(cosines, reverse=True)
        dir_gap[i] = s[0] - s[1]

    mag_auc = roc_auc_score(correct, M) if len(np.unique(correct)) > 1 else 0.5
    gap_auc = roc_auc_score(correct, dir_gap) if len(np.unique(correct)) > 1 else 0.5
    best_ind = max(mag_auc, gap_auc)

    X = np.column_stack([(M-M.mean())/(M.std()+1e-8),
                          (dir_conf-dir_conf.mean())/(dir_conf.std()+1e-8),
                          (dir_gap-dir_gap.mean())/(dir_gap.std()+1e-8)])
    try:
        lr = LogisticRegression(max_iter=1000); lr.fit(X, correct)
        lr_auc = roc_auc_score(correct, lr.predict_proba(X)[:,1])
    except: lr_auc = best_ind
    synergy = lr_auc - best_ind

    # === H-CX-84: Conservation vs Synergy ===
    print(f"\n  === H-CX-84: Conservation → Synergy ===")
    ts_arr = np.array(ts_list); h0_arr = np.array(h0_list)
    product = ts_arr * h0_arr
    cv_prod = np.std(product) / np.mean(product) if np.mean(product) > 0 else 999

    print(f"  CV(ts×H0): {cv_prod:.4f}")
    print(f"  Synergy:   {synergy:+.4f}")
    print(f"  Conserved (CV < 0.1): {'YES' if cv_prod < 0.1 else 'NO'}")
    print(f"  Synergy > 3%p: {'YES' if synergy > 0.03 else 'NO'}")

    # === H-CX-85: Dendrogram Hierarchy ===
    print(f"\n  === H-CX-85: Merge Dendrogram = Concept Hierarchy ===")
    merge_history, _ = build_dendrogram(D, Y, names, n_cls)

    print(f"\n  Dendrogram (bottom-up):")
    for i, (dist, cluster) in enumerate(merge_history):
        indent = "  " * (i + 1)
        print(f"    d={dist:.4f} → [{', '.join(cluster)}]")

    # Check semantic categories
    if dataset_name == 'cifar':
        animals = {'bird', 'cat', 'deer', 'dog', 'frog', 'horse'}
        vehicles = {'plane', 'auto', 'ship', 'truck'}
        # Find if any subtree is pure animal or pure vehicle
        pure_count = 0
        for dist, cluster in merge_history:
            cluster_set = set(cluster)
            if len(cluster_set) >= 2:
                if cluster_set.issubset(animals) or cluster_set.issubset(vehicles):
                    pure_count += 1
                    print(f"    PURE semantic cluster: {cluster}")
        purity = pure_count / len(merge_history) * 100
        print(f"\n  Semantic purity: {pure_count}/{len(merge_history)} subtrees pure ({purity:.0f}%)")

    elif dataset_name == 'fashion':
        tops = {'Tshirt', 'Pullvr', 'Coat', 'Shirt', 'Dress'}
        shoes = {'Sandal', 'Sneakr', 'Boot'}
        pure_count = 0
        for dist, cluster in merge_history:
            cluster_set = set(cluster)
            if len(cluster_set) >= 2:
                if cluster_set.issubset(tops) or cluster_set.issubset(shoes) or cluster_set == {'Trouser', 'Dress'}:
                    pure_count += 1
                    print(f"    PURE semantic cluster: {cluster}")
        purity = pure_count / len(merge_history) * 100
        print(f"\n  Semantic purity: {pure_count}/{len(merge_history)} subtrees pure ({purity:.0f}%)")

    elif dataset_name == 'mnist':
        # Digits: round(0,6,8,9), straight(1,7), angular(2,3,5), mixed(4)
        round_digits = {'0', '6', '8', '9'}
        straight = {'1', '7'}
        angular = {'2', '3', '5'}
        pure_count = 0
        for dist, cluster in merge_history:
            cluster_set = set(cluster)
            if len(cluster_set) >= 2:
                if cluster_set.issubset(round_digits) or cluster_set.issubset(straight) or cluster_set.issubset(angular):
                    pure_count += 1
                    print(f"    PURE shape cluster: {cluster}")
        purity = pure_count / len(merge_history) * 100
        print(f"\n  Shape purity: {pure_count}/{len(merge_history)} subtrees pure ({purity:.0f}%)")

    return {
        'cv_prod': cv_prod, 'synergy': synergy,
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

    # H-CX-84
    print(f"\n  H-CX-84 (CV → Synergy):")
    cvs = [r['cv_prod'] for r in results.values()]
    syns = [r['synergy'] for r in results.values()]
    r_84 = np.corrcoef(cvs, syns)[0, 1] if len(cvs) == 3 else 0
    for ds, r in results.items():
        print(f"    {ds}: CV={r['cv_prod']:.4f}, synergy={r['synergy']:+.4f}")
    print(f"  Corr(CV, synergy): {r_84:.4f} (expect < 0)")
    print(f"  H-CX-84: {'SUPPORTED' if r_84 < -0.5 else 'REJECTED'}")