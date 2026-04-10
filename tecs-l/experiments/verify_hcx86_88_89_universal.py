#!/usr/bin/env python3
"""H-CX-86 + H-CX-88 + H-CX-89 Verification: Zero-shot PH + Universal Topology + Data Inherent

H-CX-86: Random init (epoch 0) PH vs final confusion
H-CX-88: Dense MLP vs PureField confusion comparison
H-CX-89: Raw data class center distances → Source of everything?
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr, kendalltau
from ripser import ripser
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data


def get_merges_from_dist(cos_dist, n_cls=10):
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
    return merges


def class_cosine_dist(D, Y, n_cls=10):
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
    return cos_dist, means


def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    n_cls = len(names)

    print(f"\n{'='*70}")
    print(f"  H-CX-86+88+89: Universal — {dataset_name.upper()}")
    print(f"{'='*70}")

    # === H-CX-89: Raw data class centers ===
    print(f"\n  === H-CX-89: Raw Data Class Centers ===")
    raw_data, raw_labels = [], []
    for x, y in te:
        raw_data.append(x.view(x.size(0), -1).numpy())
        raw_labels.append(y.numpy())
    raw_X = np.concatenate(raw_data); raw_Y = np.concatenate(raw_labels)

    raw_dist, raw_means = class_cosine_dist(raw_X, raw_Y, n_cls)
    raw_merges = get_merges_from_dist(raw_dist, n_cls)

    print(f"  Raw data merge order:")
    for dist, i, j in raw_merges:
        print(f"    {names[i]:>6}-{names[j]:<6} dist={dist:.4f}")

    # === H-CX-86: Epoch 0 (random init) ===
    print(f"\n  === H-CX-86: Random Init (Epoch 0) PH ===")

    seed_results = []
    for seed in [42, 123, 777]:
        torch.manual_seed(seed)
        model0 = PureFieldEngine(dim, 128, 10)
        model0.eval()
        dirs0 = []
        with torch.no_grad():
            for x, y in te:
                x_flat = x.view(-1, dim)
                rep = model0.engine_a(x_flat) - model0.engine_g(x_flat)
                d = F.normalize(rep, dim=-1)
                dirs0.append(d.numpy())
        D0 = np.concatenate(dirs0)
        dist0, _ = class_cosine_dist(D0, raw_Y, n_cls)
        merges0 = get_merges_from_dist(dist0, n_cls)
        seed_results.append((merges0, dist0))

    # === Train PureField for final comparison ===
    torch.manual_seed(42)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()

    for ep in range(epochs):
        model.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()
        if (ep+1) % 5 == 0:
            model.eval(); c = t_ = 0
            with torch.no_grad():
                for x, y in te:
                    o, _ = model(x.view(-1, dim))
                    c += (o.argmax(1)==y).sum().item(); t_ += y.size(0)
            print(f"  PureField Epoch {ep+1}: acc={c/t_*100:.1f}%")

    # Final PureField confusion
    model.eval()
    dirs_f, ys_f, preds_f = [], [], []
    with torch.no_grad():
        for x, y in te:
            x_flat = x.view(-1, dim)
            rep = model.engine_a(x_flat) - model.engine_g(x_flat)
            d = F.normalize(rep, dim=-1)
            out = model.tension_scale * torch.sqrt((rep**2).mean(-1, keepdim=True)+1e-8) * d
            dirs_f.append(d.numpy()); ys_f.extend(y.numpy().tolist())
            preds_f.extend(out.argmax(1).numpy().tolist())
    D_f = np.concatenate(dirs_f); Y_f = np.array(ys_f); P_f = np.array(preds_f)

    conf_pf = np.zeros((n_cls, n_cls), dtype=int)
    for idx in np.where(P_f != Y_f)[0]:
        conf_pf[Y_f[idx], P_f[idx]] += 1
    pair_conf_pf = {}
    for i in range(n_cls):
        for j in range(i+1, n_cls):
            pair_conf_pf[(i,j)] = conf_pf[i,j] + conf_pf[j,i]
    sorted_conf_pf = sorted(pair_conf_pf.items(), key=lambda x: -x[1])

    dist_f, _ = class_cosine_dist(D_f, Y_f, n_cls)
    merges_f = get_merges_from_dist(dist_f, n_cls)

    # === H-CX-88: Dense MLP comparison ===
    print(f"\n  === H-CX-88: Dense MLP Comparison ===")
    dense = nn.Sequential(
        nn.Linear(dim, 128), nn.ReLU(), nn.Dropout(0.3), nn.Linear(128, 10)
    )
    opt_d = torch.optim.Adam(dense.parameters(), lr=1e-3)
    for ep in range(epochs):
        dense.train()
        for x, y in tl:
            opt_d.zero_grad()
            out = dense(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt_d.step()
        if (ep+1) % 5 == 0:
            dense.eval(); c = t_ = 0
            with torch.no_grad():
                for x, y in te:
                    o = dense(x.view(-1, dim))
                    c += (o.argmax(1)==y).sum().item(); t_ += y.size(0)
            print(f"  Dense Epoch {ep+1}: acc={c/t_*100:.1f}%")

    dense.eval()
    preds_d = []
    with torch.no_grad():
        for x, y in te:
            o = dense(x.view(-1, dim))
            preds_d.extend(o.argmax(1).numpy().tolist())
    P_d = np.array(preds_d)

    conf_d = np.zeros((n_cls, n_cls), dtype=int)
    for idx in np.where(P_d != Y_f)[0]:
        conf_d[Y_f[idx], P_d[idx]] += 1
    pair_conf_d = {}
    for i in range(n_cls):
        for j in range(i+1, n_cls):
            pair_conf_d[(i,j)] = conf_d[i,j] + conf_d[j,i]
    sorted_conf_d = sorted(pair_conf_d.items(), key=lambda x: -x[1])

    # Compare PureField vs Dense confusion
    pf_top5 = set(p for p, c in sorted_conf_pf[:5])
    d_top5 = set(p for p, c in sorted_conf_d[:5])
    overlap_88 = len(pf_top5 & d_top5)

    # Confusion frequency correlation
    all_pairs = sorted(pair_conf_pf.keys())
    pf_vals = [pair_conf_pf[p] for p in all_pairs]
    d_vals = [pair_conf_d[p] for p in all_pairs]
    r_88, p_88 = spearmanr(pf_vals, d_vals)

    print(f"  PureField top-5: {[f'{names[a]}-{names[b]}' for a,b in sorted(pf_top5)]}")
    print(f"  Dense top-5:     {[f'{names[a]}-{names[b]}' for a,b in sorted(d_top5)]}")
    print(f"  Overlap: {overlap_88}/5")
    print(f"  Spearman(PF_conf, Dense_conf): r={r_88:.4f}, p={p_88:.6f}")
    print(f"  H-CX-88 (r > 0.7): {'SUPPORTED' if r_88 > 0.7 else 'PARTIAL' if r_88 > 0.5 else 'REJECTED'}")

    # === H-CX-86: Epoch 0 vs Final ===
    print(f"\n  === H-CX-86: Epoch 0 (Random) vs Final Confusion ===")

    for si, (merges0, dist0) in enumerate(seed_results):
        merge_dists0 = [(d, (min(i,j),max(i,j))) for d,i,j in merges0]
        merge_dists0.sort()
        confs0 = [(pair_conf_pf.get(p, 0)) for d, p in merge_dists0]
        dists0 = [d for d, p in merge_dists0]
        r0, p0 = spearmanr(dists0, confs0)
        top3_0 = set(p for d, p in merge_dists0[:3])
        actual_top3 = set(p for p, c in sorted_conf_pf[:3])
        p_at_3 = len(top3_0 & actual_top3) / 3
        print(f"  Seed {[42,123,777][si]}: r={r0:.4f} p={p0:.4f}  P@3={p_at_3:.2f}")

    # Merge order stability across seeds
    seed_orders = []
    for merges0, _ in seed_results:
        order = [(min(i,j),max(i,j)) for d,i,j in sorted(merges0, key=lambda x: x[0])]
        seed_orders.append(order)
    # Kendall tau between seeds
    for i in range(len(seed_orders)):
        for j in range(i+1, len(seed_orders)):
            o1 = {p: k for k, p in enumerate(seed_orders[i])}
            vals = [o1.get(p, 99) for p in seed_orders[j]]
            tau, _ = kendalltau(list(range(len(seed_orders[j]))), vals)
            print(f"  Seed {i} vs {j} Kendall tau: {tau:.4f}")

    # === H-CX-89: Raw data distance vs learned distance ===
    print(f"\n  === H-CX-89: Raw Data Distance → Learned ===")

    # Raw merge vs final confusion
    raw_merge_dists = [(d, (min(i,j),max(i,j))) for d,i,j in raw_merges]
    raw_merge_dists.sort()
    raw_confs = [pair_conf_pf.get(p, 0) for d, p in raw_merge_dists]
    raw_dists = [d for d, p in raw_merge_dists]
    r_raw, p_raw = spearmanr(raw_dists, raw_confs)

    print(f"  Raw data merge vs final confusion: r={r_raw:.4f}, p={p_raw:.4f}")

    # Raw merge order vs learned merge order
    raw_order = [(min(i,j),max(i,j)) for d,i,j in sorted(raw_merges, key=lambda x: x[0])]
    learned_order = [(min(i,j),max(i,j)) for d,i,j in sorted(merges_f, key=lambda x: x[0])]
    raw_rank = {p: k for k, p in enumerate(raw_order)}
    learned_vals = [raw_rank.get(p, 99) for p in learned_order]
    tau_rl, _ = kendalltau(list(range(len(learned_order))), learned_vals)
    print(f"  Raw vs learned merge order tau: {tau_rl:.4f}")

    # Raw dendrogram semantic check
    print(f"\n  Raw data merge order:")
    for dist, i, j in raw_merges:
        conf = pair_conf_pf.get((min(i,j),max(i,j)), 0)
        print(f"    {names[i]:>6}-{names[j]:<6} raw_dist={dist:.4f}  final_conf={conf}")

    # Amplification ratio: learned_dist / raw_dist
    print(f"\n  Amplification (learned/raw distance):")
    for (rd, ri, rj), (ld, li, lj) in zip(raw_merges, merges_f):
        rp = (min(ri,rj), max(ri,rj))
        lp = (min(li,lj), max(li,lj))
        amp = dist_f[li,lj] / max(raw_dist[ri,rj], 1e-8) if rp == lp else 0
        if rp == lp:
            print(f"    {names[ri]:>6}-{names[rj]:<6}: raw={raw_dist[ri,rj]:.4f} → learned={dist_f[li,lj]:.4f}  amp={amp:.2f}x")

    print(f"\n  H-CX-89 (raw→confusion r > 0.7): {'SUPPORTED' if abs(r_raw) > 0.7 else 'PARTIAL' if abs(r_raw) > 0.5 else 'REJECTED'}")

    return {
        'r_86_seed0': spearmanr([d for d,p in [(d,(min(i,j),max(i,j))) for d,i,j in seed_results[0][0]]],
                                [pair_conf_pf.get(p,0) for d,p in [(d,(min(i,j),max(i,j))) for d,i,j in seed_results[0][0]]])[0],
        'r_88': r_88, 'overlap_88': overlap_88,
        'r_89_raw': r_raw, 'tau_raw_learned': tau_rl,
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
    print(f"  Round 6 SUMMARY")
    print(f"{'='*70}")
    for ds, r in results.items():
        print(f"  {ds}: r86={r['r_86_seed0']:.3f}, r88={r['r_88']:.3f}({r['overlap_88']}/5), "
              f"r89={r['r_89_raw']:.3f}, tau_rl={r['tau_raw_learned']:.3f}")