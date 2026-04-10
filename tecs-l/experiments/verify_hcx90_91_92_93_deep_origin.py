```python
#!/usr/bin/env python3
"""H-CX-90~93 Integrated Verification: Origin of Confusion

H-CX-90: Epoch 0→1 phase transition
H-CX-91: k-NN confusion = neural network confusion?
H-CX-92: dendrogram depth = learning difficulty
H-CX-93: confusion PCA = semantic axis
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from sklearn.metrics import roc_auc_score, confusion_matrix as sk_confusion
from sklearn.neighbors import KNeighborsClassifier
from sklearn.decomposition import PCA
from scipy.stats import spearmanr, kendalltau
from ripser import ripser
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data


def get_merges(D, Y, n_cls=10):
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

    result = ripser(cos_dist, maxdim=0, distance_matrix=True)
    h0 = result['dgms'][0]
    h0_finite = h0[h0[:, 1] < np.inf]
    h0_total = np.sum(h0_finite[:, 1] - h0_finite[:, 0]) if len(h0_finite) > 0 else 0

    return merges, h0_total, cos_dist


def pair_confusion_from_preds(Y, P, n_cls):
    conf = np.zeros((n_cls, n_cls), dtype=int)
    for idx in np.where(P != Y)[0]:
        conf[Y[idx], P[idx]] += 1
    pairs = {}
    for i in range(n_cls):
        for j in range(i+1, n_cls):
            pairs[(i,j)] = conf[i,j] + conf[j,i]
    return pairs, conf


def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    n_cls = len(names)

    print(f"\n{'='*70}")
    print(f"  H-CX-90~93: Deep Origin — {dataset_name.upper()}")
    print(f"{'='*70}")

    # Collect raw data
    raw_X_tr, raw_Y_tr = [], []
    for x, y in tl:
        raw_X_tr.append(x.view(x.size(0), -1).numpy())
        raw_Y_tr.append(y.numpy())
    X_tr = np.concatenate(raw_X_tr); Y_tr = np.concatenate(raw_Y_tr)

    raw_X_te, raw_Y_te = [], []
    for x, y in te:
        raw_X_te.append(x.view(x.size(0), -1).numpy())
        raw_Y_te.append(y.numpy())
    X_te = np.concatenate(raw_X_te); Y_te = np.concatenate(raw_Y_te)

    # === H-CX-91: k-NN confusion ===
    print(f"\n  === H-CX-91: k-NN Confusion ===")
    knn_pairs = {}
    for k in [1, 3, 5]:
        knn = KNeighborsClassifier(n_neighbors=k, n_jobs=-1)
        knn.fit(X_tr[:10000], Y_tr[:10000])  # subsample for speed
        P_knn = knn.predict(X_te)
        pairs_knn, _ = pair_confusion_from_preds(Y_te, P_knn, n_cls)
        knn_pairs[k] = pairs_knn
        acc_knn = (P_knn == Y_te).mean() * 100
        print(f"  k={k}: acc={acc_knn:.1f}%")

    # === Train PureField ===
    torch.manual_seed(42)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()

    # Track epoch 0
    model.eval()
    dirs0 = []
    with torch.no_grad():
        for x, y in te:
            rep = model.engine_a(x.view(-1, dim)) - model.engine_g(x.view(-1, dim))
            dirs0.append(F.normalize(rep, dim=-1).numpy())
    D0 = np.concatenate(dirs0)
    merges0, h0_0, _ = get_merges(D0, Y_te, n_cls)
    ts_0 = model.tension_scale.item()

    epoch_merges = [(merges0, h0_0, ts_0)]
    epoch_accs = []

    for ep in range(epochs):
        model.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()

        model.eval()
        dirs, ys, preds = [], [], []
        with torch.no_grad():
            for x, y in te:
                x_flat = x.view(-1, dim)
                rep = model.engine_a(x_flat) - model.engine_g(x_flat)
                d = F.normalize(rep, dim=-1)
                out = model.tension_scale * torch.sqrt((rep**2).mean(-1, keepdim=True)+1e-8) * d
                dirs.append(d.numpy()); ys.extend(y.numpy().tolist())
                preds.extend(out.argmax(1).numpy().tolist())
        D = np.concatenate(dirs); Y = np.array(ys); P = np.array(preds)
        acc = (P == Y).mean() * 100
        epoch_accs.append(acc)

        merges_ep, h0_ep, _ = get_merges(D, Y, n_cls)
        ts_ep = model.tension_scale.item()
        epoch_merges.append((merges_ep, h0_ep, ts_ep))

        if (ep+1) % 5 == 0 or ep == 0:
            print(f"  Epoch {ep+1}: acc={acc:.1f}%  H0={h0_ep:.4f}  ts={ts_ep:.4f}")

    # Final confusion
    pairs_pf, conf_pf = pair_confusion_from_preds(Y, P, n_cls)
    sorted_pf = sorted(pairs_pf.items(), key=lambda x: -x[1])

    # === H-CX-90: Phase transition ===
    print(f"\n  === H-CX-90: Epoch 0→1 Phase Transition ===")

    h0_changes = []
    ts_changes = []
    for i in range(len(epoch_merges) - 1):
        dh0 = abs(epoch_merges[i+1][1] - epoch_merges[i][1])
        dts = abs(epoch_merges[i+1][2] - epoch_merges[i][2])
        h0_changes.append(dh0)
        ts_changes.append(dts)

    # Merge order tau between consecutive epochs
    tau_changes = []
    for i in range(len(epoch_merges) - 1):
        order_i = [(min(a,b), max(a,b)) for d,a,b in sorted(epoch_merges[i][0], key=lambda x: x[0])]
        order_j = [(min(a,b), max(a,b)) for d,a,b in sorted(epoch_merges[i+1][0], key=lambda x: x[0])]
        rank_i = {p: k for k, p in enumerate(order_i)}
        vals = [rank_i.get(p, 99) for p in order_j]
        tau, _ = kendalltau(list(range(len(order_j))), vals)
        tau_changes.append(tau)

    print(f"  {'Transition':>12} {'dH0':>8} {'dts':>8} {'tau':>8}")
    print(f"  {'-'*40}")
    for i in range(min(5, len(h0_changes))):
        label = f"ep{i}→{i+1}"
        print(f"  {label:>12} {h0_changes[i]:>8.4f} {ts_changes[i]:>8.4f} {tau_changes[i]:>8.4f}")

    # Phase transition: ep0→1 vs average of ep1→2...ep14→15
    if len(h0_changes) > 1:
        dh0_01 = h0_changes[0]
        dh0_rest = np.mean(h0_changes[1:])
        ratio_h0 = dh0_01 / dh0_rest if dh0_rest > 0 else 999
        tau_01 = tau_changes[0]
        tau_rest = np.mean(tau_changes[1:])
        print(f"\n  dH0(ep0→1): {dh0_01:.4f}  avg(ep1→...): {dh0_rest:.4f}  ratio: {ratio_h0:.2f}x")
        print(f"  tau(ep0→1): {tau_01:.4f}  avg(ep1→...): {tau_rest:.4f}")
        print(f"  H-CX-90 (ratio > 2): {'SUPPORTED' if ratio_h0 > 2 else 'PARTIAL' if ratio_h0 > 1.5 else 'REJECTED'}")

    # === H-CX-91: k-NN vs PureField ===
    print(f"\n  === H-CX-91: k-NN vs PureField Confusion ===")
    all_pairs = sorted(pairs_pf.keys())
    pf_vals = [pairs_pf[p] for p in all_pairs]

    for k in [1, 3, 5]:
        knn_vals = [knn_pairs[k].get(p, 0) for p in all_pairs]
        r_knn, p_knn = spearmanr(pf_vals, knn_vals)
        knn_top5 = set(p for p, c in sorted(knn_pairs[k].items(), key=lambda x: -x[1])[:5])
        pf_top5 = set(p for p, c in sorted_pf[:5])
        overlap = len(knn_top5 & pf_top5)
        print(f"  k={k}: Spearman r={r_knn:.4f} p={p_knn:.6f}  top-5 overlap={overlap}/5")

    # Best k-NN result
    best_k = max([1,3,5], key=lambda k: spearmanr(pf_vals, [knn_pairs[k].get(p,0) for p in all_pairs])[0])
    r_best, _ = spearmanr(pf_vals, [knn_pairs[best_k].get(p,0) for p in all_pairs])
    print(f"  Best k={best_k}: r={r_best:.4f}")
    print(f"  H-CX-91 (r > 0.8): {'SUPPORTED' if r_best > 0.8 else 'PARTIAL' if r_best > 0.6 else 'REJECTED'}")

    # Print top-5 comparison
    print(f"\n  Top-5 confusion pairs:")
    print(f"  {'PureField':>30} {'k-NN(k={best_k})':>30}")
    for i in range(5):
        pf_p = sorted_pf[i]
        knn_sorted = sorted(knn_pairs[best_k].items(), key=lambda x: -x[1])
        knn_p = knn_sorted[i]
        pf_str = f"{names[pf_p[0][0]]}-{names[pf_p[0][1]]} ({pf_p[1]})"
        knn_str = f"{names[knn_p[0][0]]}-{names[knn_p[0][1]]} ({knn_p[1]})"
        print(f"  {pf_str:>30} {knn_str:>30}")

    # === H-CX-92: Dendrogram depth = difficulty ===
    print(f"\n  === H-CX-92: Dendrogram Depth = Difficulty ===")
    final_merges = epoch_merges[-1][0]
    # Per-class: first merge distance
    first_merge = {}
    for dist, i, j in sorted(final_merges, key=lambda x: x[0]):
        if i not in first_merge: first_merge[i] = dist
        if j not in first_merge: first_merge[j] = dist

    class_accs = []
    first_dists = []
    for c in range(n_cls):
        mask = Y == c
        c_acc = (P[mask] == Y[mask]).mean() * 100
        class_accs.append(c_acc)
        first_dists.append(first_merge.get(c, 0))

    r_92, p_92 = spearmanr(first_dists, class_accs)
    print(f"  {'Class':>7} {'1st_merge':>10} {'Acc%':>7}")
    print(f"  {'-'*28}")
    for c in range(n_cls):
        print(f"  {names[c]:>7} {first_dists[c]:>10.4f} {class_accs[c]:>7.1f}")
    print(f"\n  Spearman(1st_merge, acc): r={r_92:.4f}, p={p_92:.4f}")
    print(f"  H-CX-92 (r > 0.5): {'SUPPORTED' if r_92 > 0.5 else 'PARTIAL' if r_92 > 0.3 else 'REJECTED'}")

    # === H-CX-93: Confusion PCA ===
    print(f"\n  === H-CX-93: Confusion Matrix PCA ===")
    # Symmetric confusion: (conf + conf.T) / 2
    conf_sym = (conf_pf + conf_pf.T) / 2.0
    np.fill_diagonal(conf_sym, 0)

    pca = PCA(n_components=3)
    conf_pca = pca.fit_transform(conf_sym)
    explained = pca.explained_variance_ratio_

    print(f"  Explained variance: PC1={explained[0]:.3f}, PC2={explained[1]:.3f}, PC3={explained[2]:.3f}")
    print(f"\n  PC1 loadings (main semantic axis?):")
    pc1 = conf_pca[:, 0]
    sorted_pc1 = sorted(range(n_cls), key=lambda c: pc1[c])
    for c in sorted_pc1:
        bar_len = int(abs(pc1[c]) / max(abs(pc1)) * 20)
        sign = '+' if pc1[c] > 0 else '-'
        print(f"  {names[c]:>7} {sign}{'█'*bar_len}{'░'*(20-bar_len)} {pc1[c]:>8.3f}")

    # Check semantic split
    if dataset_name == 'cifar':
        animals = {0, 2, 3, 4, 5, 7}  # plane=0 NO, bird=2, cat=3, deer=4, dog=5, horse=7
        # Actually: plane=0, auto=1, bird=2, cat=3, deer=4, dog=5, frog=6, horse=7, ship=8, truck=9
        animals = {2, 3, 4, 5, 6, 7}  # bird, cat, deer, dog, frog, horse
        vehicles = {0, 1, 8, 9}  # plane, auto, ship, truck
        pc1_animals = [pc1[c] for c in animals]
        pc1_vehicles = [pc1[c] for c in vehicles]
        sep = min(pc1_animals) > max(pc1_vehicles) or max(pc1_animals) < min(pc1_vehicles)
        print(f"\n  Animals PC1 range: [{min(pc1_animals):.3f}, {max(pc1_animals):.3f}]")
        print(f"  Vehicles PC1 range: [{min(pc1_vehicles):.3f}, {max(pc1_vehicles):.3f}]")
        print(f"  Clean separation: {'YES' if sep else 'NO (overlap)'}")

    elif dataset_name == 'fashion':
        tops = {0, 2, 3, 4, 6}  # Tshirt, Pullover, Dress, Coat, Shirt
        shoes = {5, 7, 9}  # Sandal, Sneaker, Boot
        pc1_tops = [pc1[c] for c in tops]
        pc1_shoes = [pc1[c] for c in shoes]
        sep = min(pc1_tops) > max(pc1_shoes) or max(pc1_tops) < min(pc1_shoes)
        print(f"\n  Tops PC1 range: [{min(pc1_tops):.3f}, {max(pc1_tops):.3f}]")
        print(f"  Shoes PC1 range: [{min(pc1_shoes):.3f}, {max(pc1_shoes):.3f}]")
        print(f"  Clean separation: {'YES' if sep else 'NO (overlap)'}")

    return {
        'h0_ratio': ratio_h0 if len(h0_changes) > 1 else 0,
        'r_knn_best': r_best,
        'r_92': r_92,
        'pc1_var': explained[0],
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
    print(f"  Round 7 SUMMARY")
    print(f"{'='*70}")
    for ds, r in results.items():
        print(f"  {ds}: h0_ratio={r['h0_ratio']:.2f}x, knn_r={r['r_knn_best']:.3f}, "
              f"depth_r={r['r_92']:.3f}, pc1={r['pc1_var']:.3f}")
```