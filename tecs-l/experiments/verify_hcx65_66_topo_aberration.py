```python
#!/usr/bin/env python3
"""H-CX-65 + H-CX-66 Verification: Aberration Phase Correction + Direction Phase Confusion Mapping

H-CX-65: Per-class isolation(nearest neighbor distance) vs per-class AUC
H-CX-66: PH merge order vs confusion frequency Spearman correlation
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr
from ripser import ripser
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data


def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()

    print(f"\n{'='*70}")
    print(f"  H-CX-65 + H-CX-66: Topo Aberration — {dataset_name.upper()}")
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

    # Collect data
    model.eval()
    all_dir, all_mag, all_y, all_pred = [], [], [], []
    n_cls = len(names)
    with torch.no_grad():
        for x, y in te:
            x_flat = x.view(-1, dim)
            a = model.engine_a(x_flat); g = model.engine_g(x_flat)
            rep = a - g
            mag = torch.sqrt((rep**2).mean(-1))
            d = F.normalize(rep, dim=-1)
            out = model.tension_scale * mag.unsqueeze(-1) * d
            pred = out.argmax(1)
            all_dir.append(d.numpy()); all_mag.append(mag.numpy())
            all_y.append(y.numpy()); all_pred.append(pred.numpy())

    D = np.concatenate(all_dir); M = np.concatenate(all_mag)
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

    # Cosine distance matrix
    cos_sim = class_means_n @ class_means_n.T
    cos_dist = np.clip(1 - cos_sim, 0, 2)
    np.fill_diagonal(cos_dist, 0)

    # === H-CX-65: Isolation vs Per-class AUC ===
    print(f"\n  === H-CX-65: Class Isolation vs Per-class AUC ===")

    # Per-class isolation = min distance to other class
    isolations = []
    for c in range(n_cls):
        dists = cos_dist[c].copy()
        dists[c] = 999
        isolations.append(np.min(dists))

    # Per-class precog AUC
    class_aucs = []
    for c in range(n_cls):
        mask = Y == c
        if mask.sum() > 10 and len(np.unique(correct[mask])) > 1:
            c_auc = roc_auc_score(correct[mask], M[mask])
        else:
            c_auc = 0.5
        class_aucs.append(c_auc)

    print(f"  {'Class':>7} {'Isolation':>10} {'AUC':>7} {'Acc%':>6} {'Nearest':>10}")
    print(f"  {'-'*45}")
    for c in range(n_cls):
        dists = cos_dist[c].copy(); dists[c] = 999
        nearest = names[np.argmin(dists)]
        acc_c = correct[Y == c].mean() * 100
        bar_iso = int(isolations[c] * 30)
        bar_auc = int(class_aucs[c] * 30)
        print(f"  {names[c]:>7} {isolations[c]:>10.4f} {class_aucs[c]:>7.3f} {acc_c:>6.1f} {nearest:>10}")

    r_iso_auc, p_iso_auc = spearmanr(isolations, class_aucs)
    print(f"\n  Spearman(isolation, AUC): r={r_iso_auc:.4f}, p={p_iso_auc:.4f}")
    print(f"  H-CX-65 (r > 0.5): {'SUPPORTED' if r_iso_auc > 0.5 else 'PARTIAL' if r_iso_auc > 0.3 else 'REJECTED'}")

    # ASCII scatter
    print(f"\n  Isolation vs AUC scatter:")
    print(f"  AUC")
    for level in [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]:
        line = f"  {level:.1f} |"
        for c in range(n_cls):
            if abs(class_aucs[c] - level) < 0.05:
                col = int(isolations[c] / max(isolations) * 30)
                line = line[:4+col] + names[c][0] + line[5+col:]
        if len(line) < 36:
            line += ' ' * (36 - len(line))
        print(line + '|')
    print(f"      +{'─'*30}→ Isolation")

    # === H-CX-66: PH Merge Order vs Confusion Frequency ===
    print(f"\n  === H-CX-66: PH Merge Order vs Confusion ===")

    # Ripser PH
    result = ripser(cos_dist, maxdim=1, distance_matrix=True)
    h0 = result['dgms'][0]
    h1 = result['dgms'][1] if len(result['dgms']) > 1 else np.array([]).reshape(0, 2)

    # Extract merge events from H0
    # In H0, each death corresponds to a merge of two components
    # Sort by death time (earliest merge first)
    h0_finite = h0[h0[:, 1] < np.inf]
    merge_order = np.argsort(h0_finite[:, 1])  # earliest death first

    # Build merge pairs from distance matrix
    # The merge at distance d means the two closest clusters at that point joined
    used = set()
    merge_pairs = []
    sorted_edges = []
    for i in range(n_cls):
        for j in range(i+1, n_cls):
            sorted_edges.append((cos_dist[i, j], i, j))
    sorted_edges.sort()

    # Simple single-linkage merge tracking
    parent = list(range(n_cls))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[a] = b
            return True
        return False

    merge_events = []
    for dist, i, j in sorted_edges:
        if union(i, j):
            merge_events.append((dist, i, j))

    # Confusion matrix
    conf_matrix = np.zeros((n_cls, n_cls), dtype=int)
    wrong_mask = P != Y
    for idx in np.where(wrong_mask)[0]:
        conf_matrix[Y[idx], P[idx]] += 1

    # Confusion frequency for each pair
    pair_confusion = {}
    for i in range(n_cls):
        for j in range(i+1, n_cls):
            pair_confusion[(i, j)] = conf_matrix[i, j] + conf_matrix[j, i]

    print(f"  Merge order (earliest = most confused):")
    print(f"  {'Order':>5} {'Dist':>7} {'Pair':>15} {'Confusion':>10}")
    print(f"  {'-'*40}")
    merge_dists = []
    merge_confs = []
    for idx, (dist, i, j) in enumerate(merge_events):
        conf = pair_confusion.get((min(i,j), max(i,j)), 0)
        merge_dists.append(dist)
        merge_confs.append(conf)
        print(f"  {idx+1:>5} {dist:>7.4f} {names[i]:>6}-{names[j]:<6} {conf:>10}")

    # Spearman: merge order (by distance) vs confusion
    # Earlier merge (smaller distance) should have MORE confusion
    r_merge, p_merge = spearmanr(merge_dists, merge_confs)
    print(f"\n  Spearman(merge_dist, confusion): r={r_merge:.4f}, p={p_merge:.4f}")
    print(f"  Expected: r < 0 (closer = more confused)")
    print(f"  H-CX-66 (r < -0.3): {'SUPPORTED' if r_merge < -0.3 else 'PARTIAL' if r_merge < 0 else 'REJECTED'}")

    # Top actual confusion pairs vs top merge pairs
    sorted_conf = sorted(pair_confusion.items(), key=lambda x: -x[1])
    top_conf_5 = set(sorted_conf[i][0] for i in range(min(5, len(sorted_conf))))
    top_merge_5 = set((min(i,j), max(i,j)) for _, i, j in merge_events[:5])
    overlap = len(top_conf_5 & top_merge_5)
    print(f"\n  Top-5 overlap (merge vs confusion): {overlap}/5")
    print(f"  Merge top-5: {[f'{names[a]}-{names[b]}' for a,b in sorted(top_merge_5)]}")
    print(f"  Confuse top-5: {[f'{names[a]}-{names[b]}' for a,b in sorted(top_conf_5)]}")

    # H1 loops = circular confusion?
    if len(h1) > 0:
        print(f"\n  H1 loops: {len(h1)} (potential circular confusion)")
        for i, (b, d) in enumerate(h1[:5]):
            print(f"    loop {i+1}: birth={b:.4f}, death={d:.4f}, persist={d-b:.4f}")
    else:
        print(f"\n  H1 loops: 0 (no circular confusion detected)")

    return r_iso_auc, r_merge, overlap

if __name__ == '__main__':
    for ds in ['mnist', 'fashion', 'cifar']:
        try:
            run_experiment(ds)
        except Exception as e:
            print(f"  {ds} failed: {e}")
            import traceback; traceback.print_exc()
```