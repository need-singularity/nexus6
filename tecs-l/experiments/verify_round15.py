```python
#!/usr/bin/env python3
"""Round 15: r=1.000 Deep Dive + Resonance/Consensus Integration

H-CX-170: Why cross-dataset merge distribution r=1.000? N-class universal law?
H-CX-171: H0_ep1 difficulty prediction — Additional datasets (breast_cancer, iris, wine)
H-CX-172: Tension resonance r=0.951 = Silent consensus cos=0.986? Same phenomenon?
H-CX-173: dendrogram fixed step — Batch-wise tracking
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from scipy.stats import spearmanr
from ripser import ripser
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data
from sklearn.datasets import load_iris, load_wine, load_breast_cancer
from torch.utils.data import DataLoader, TensorDataset


def get_merges(D, Y, n_cls):
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


def train_quick(dim, tl, te, n_cls, epochs=15, seed=42):
    torch.manual_seed(seed)
    model = PureFieldEngine(dim, 128, n_cls)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()
    for ep in range(epochs):
        model.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()
    model.eval()
    dirs, ys, preds, tensions = [], [], [], []
    with torch.no_grad():
        for x, y in te:
            x_flat = x.view(-1, dim)
            rep = model.engine_a(x_flat) - model.engine_g(x_flat)
            d = F.normalize(rep, dim=-1)
            t = (rep**2).mean(-1)
            out = model.tension_scale * torch.sqrt(t.unsqueeze(-1)+1e-8) * d
            dirs.append(d.numpy()); ys.extend(y.numpy())
            preds.extend(out.argmax(1).numpy()); tensions.extend(t.numpy())
    return np.concatenate(dirs), np.array(ys), np.array(preds), np.array(tensions), model


def sklearn_to_loader(X, y, batch_size=64):
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    X = StandardScaler().fit_transform(X).astype(np.float32)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, random_state=42)
    tl = DataLoader(TensorDataset(torch.tensor(X_tr), torch.tensor(y_tr, dtype=torch.long)), batch_size, True)
    te = DataLoader(TensorDataset(torch.tensor(X_te), torch.tensor(y_te, dtype=torch.long)), batch_size)
    return X.shape[1], tl, te, len(set(y))


def run_all():
    print(f"\n{'='*70}")
    print(f"  Round 15: r=1.000 Deep Dive")
    print(f"{'='*70}")

    # === H-CX-171: H0_ep1 on more datasets ===
    print(f"\n  === H-CX-171: H0_ep1 Learnability — Extended ===")

    results = []

    # Standard datasets
    for ds in ['mnist', 'fashion', 'cifar']:
        dim, tl, te, names = load_data(ds)
        # 1 epoch
        torch.manual_seed(42)
        m = PureFieldEngine(dim, 128, 10)
        opt = torch.optim.Adam(m.parameters(), lr=1e-3)
        ce = nn.CrossEntropyLoss()
        m.train()
        step = 0
        for x, y in tl:
            opt.zero_grad()
            out, t = m(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()
            step += 1
            if step >= 50: break  # partial epoch for speed
        m.eval()
        dirs = []
        ys_list = []
        with torch.no_grad():
            for x, y in te:
                rep = m.engine_a(x.view(-1, dim)) - m.engine_g(x.view(-1, dim))
                dirs.append(F.normalize(rep, dim=-1).numpy())
                ys_list.extend(y.numpy())
        D = np.concatenate(dirs); Y = np.array(ys_list)
        _, h0, _ = get_merges(D, Y, 10)

        # Full train for acc
        D_f, Y_f, P_f, _, _ = train_quick(dim, tl, te, 10)
        acc = (P_f == Y_f).mean() * 100
        results.append((ds, h0, acc))

    # Sklearn datasets
    for name, loader in [('iris', load_iris), ('wine', load_wine), ('cancer', load_breast_cancer)]:
        data = loader()
        dim, tl, te, n_cls = sklearn_to_loader(data.data, data.target)
        torch.manual_seed(42)
        m = PureFieldEngine(dim, 64, n_cls)
        opt = torch.optim.Adam(m.parameters(), lr=1e-3)
        ce = nn.CrossEntropyLoss()
        m.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = m(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()
        m.eval()
        dirs = []; ys_list = []
        with torch.no_grad():
            for x, y in te:
                rep = m.engine_a(x) - m.engine_g(x)
                dirs.append(F.normalize(rep, dim=-1).numpy())
                ys_list.extend(y.numpy())
        D = np.concatenate(dirs); Y = np.array(ys_list)
        _, h0, _ = get_merges(D, Y, n_cls)

        # Full train
        D_f, Y_f, P_f, _, _ = train_quick(dim, tl, te, n_cls, epochs=30)
        acc = (P_f == Y_f).mean() * 100
        results.append((name, h0, acc))

    print(f"  {'Dataset':>10} {'H0_ep1':>8} {'Final_acc':>10}")
    print(f"  {'-'*30}")
    for ds, h0, acc in results:
        print(f"  {ds:>10} {h0:>8.4f} {acc:>10.1f}")

    h0s = [r[1] for r in results]
    accs = [r[2] for r in results]
    r171, p171 = spearmanr(h0s, accs)
    print(f"\n  Spearman(H0_ep1, acc) across {len(results)} datasets: r={r171:.4f}")
    print(f"  H-CX-171 (r > 0.8 on 6 datasets): {'SUPPORTED' if r171 > 0.8 else 'PARTIAL'}")

    # === H-CX-172: Resonance = Consensus? ===
    print(f"\n  === H-CX-172: Resonance = Consensus? ===")

    dim, tl, te, names = load_data('mnist')

    # Train 3 models
    models = []
    for seed in [42, 123, 777]:
        D, Y, P, T, m = train_quick(dim, tl, te, 10, seed=seed)
        models.append((D, Y, P, T, m))

    # For each pair: tension corr AND direction cosine
    print(f"  {'Pair':>10} {'T_corr':>8} {'Dir_cos':>8} {'Match':>8}")
    print(f"  {'-'*36}")
    t_corrs = []; d_coses = []
    for i in range(3):
        for j in range(i+1, 3):
            r_t, _ = spearmanr(models[i][3], models[j][3])
            # Class mean direction cosine
            cos_vals = []
            for c in range(10):
                mi = models[i][0][models[i][1]==c].mean(0)
                mj = models[j][0][models[j][1]==c].mean(0)
                mi /= max(np.linalg.norm(mi), 1e-8)
                mj /= max(np.linalg.norm(mj), 1e-8)
                cos_vals.append((mi * mj).sum())
            mean_cos = np.mean(cos_vals)
            t_corrs.append(r_t); d_coses.append(mean_cos)
            print(f"  {[42,123,777][i]}v{[42,123,777][j]:>6} {r_t:>8.4f} {mean_cos:>8.4f}")

    r_172, _ = spearmanr(t_corrs, d_coses)
    print(f"\n  Corr(tension_resonance, direction_consensus): {r_172:.4f}")
    print(f"  H-CX-172 (same phenomenon): {'SUPPORTED' if abs(r_172) > 0.8 else 'PARTIAL'}")

    # === H-CX-170: Why r=1.000 cross-dataset? ===
    print(f"\n  === H-CX-170: Cross-Dataset r=1.000 Origin ===")

    # Get merge distances for all 3 image datasets
    all_dists = {}
    for ds in ['mnist', 'fashion', 'cifar']:
        dim, tl, te, names = load_data(ds)
        D, Y, P, _, _ = train_quick(dim, tl, te, 10)
        merges, _, _ = get_merges(D, Y, 10)
        dists = sorted([d for d, i, j in merges])
        all_dists[ds] = dists

    # Pairwise correlation of sorted merge distances
    print(f"  Sorted merge distance correlations:")
    for ds1 in ['mnist', 'fashion', 'cifar']:
        for ds2 in ['mnist', 'fashion', 'cifar']:
            if ds1 >= ds2: continue
            r, _ = spearmanr(all_dists[ds1], all_dists[ds2])
            print(f"  {ds1} vs {ds2}: r={r:.4f}")

    # Check: is it just because both have 9 merges with monotonic distances?
    # Random comparison
    random_dists = sorted(np.random.rand(9))
    r_rand, _ = spearmanr(all_dists['mnist'], random_dists)
    print(f"  mnist vs random: r={r_rand:.4f}")
    print(f"  Note: sorted merge dists are always monotonic → high r is trivial!")
    print(f"  Real test: unsorted pair-wise distances")

    # Unsorted: all 45 pairwise distances
    all_pair_dists = {}
    for ds in ['mnist', 'fashion', 'cifar']:
        dim, tl, te, names = load_data(ds)
        D, Y, P, _, _ = train_quick(dim, tl, te, 10)
        _, _, cos_dist = get_merges(D, Y, 10)
        pair_d = []
        for i in range(10):
            for j in range(i+1, 10):
                pair_d.append(cos_dist[i, j])
        all_pair_dists[ds] = pair_d

    print(f"\n  45 pairwise distance correlations (unsorted, true test):")
    for ds1 in ['mnist', 'fashion', 'cifar']:
        for ds2 in ['mnist', 'fashion', 'cifar']:
            if ds1 >= ds2: continue
            r, p = spearmanr(all_pair_dists[ds1], all_pair_dists[ds2])
            print(f"  {ds1} vs {ds2}: r={r:.4f} p={p:.6f}")

    print(f"\n{'='*70}")
    print(f"  Round 15 SUMMARY")
    print(f"{'='*70}")
    print(f"  H-CX-170: cross-dataset true r = see above")
    print(f"  H-CX-171: H0_ep1 vs acc (6 datasets): r={r171:.4f}")
    print(f"  H-CX-172: resonance~consensus corr: {r_172:.4f}")


if __name__ == '__main__':
    run_all()
```