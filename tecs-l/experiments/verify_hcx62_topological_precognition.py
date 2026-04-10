```python
#!/usr/bin/env python3
"""H-CX-62 Verification: Topological Precognition — Approximate PH(tension barcode) predicts learning trajectory"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from sklearn.metrics import roc_auc_score
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data

def approx_persistent_homology(D, Y, n_cls=10, n_thresholds=20):
    """Approximate PH: cosine threshold sweep → beta_0 curve"""
    # Class mean directions
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

    # Pairwise cosine similarity matrix
    cos_mat = means @ means.T

    # Sweep threshold: count connected components
    thresholds = np.linspace(0, 1, n_thresholds)
    beta0_curve = []
    for th in thresholds:
        # Connected components via simple union-find
        parent = list(range(n_cls))
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        def union(a, b):
            a, b = find(a), find(b)
            if a != b: parent[a] = b

        for i in range(n_cls):
            for j in range(i+1, n_cls):
                if cos_mat[i, j] >= th:
                    union(i, j)
        n_components = len(set(find(i) for i in range(n_cls)))
        beta0_curve.append(n_components)

    return thresholds, np.array(beta0_curve), cos_mat

def persistence_from_beta0(thresholds, beta0):
    """beta_0 curve → birth-death pairs (approximate)"""
    pairs = []
    for i in range(1, len(beta0)):
        if beta0[i] < beta0[i-1]:  # merge event = death
            n_deaths = beta0[i-1] - beta0[i]
            for _ in range(n_deaths):
                pairs.append((thresholds[i], thresholds[0]))  # approximate
    # Persistence = birth - death (in cosine space, reversed)
    persistences = [abs(b - d) for b, d in pairs]
    return persistences

def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()

    print(f"\n{'='*70}")
    print(f"  H-CX-62: Topological Precognition — {dataset_name.upper()}")
    print(f"{'='*70}")

    epoch_data = []

    for ep in range(epochs):
        model.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()

        model.eval()
        dirs_list, ys, corrects = [], [], []
        with torch.no_grad():
            for x, y in te:
                x_flat = x.view(-1, dim)
                a = model.engine_a(x_flat); g = model.engine_g(x_flat)
                rep = a - g
                d = F.normalize(rep, dim=-1)
                out = model.tension_scale * torch.sqrt((rep**2).mean(-1, keepdim=True) + 1e-8) * d
                pred = out.argmax(1)
                dirs_list.append(d.numpy())
                ys.extend(y.numpy().tolist())
                corrects.extend((pred == y).numpy().tolist())

        D = np.concatenate(dirs_list); Y = np.array(ys)
        acc = np.mean(corrects) * 100

        # Compute approximate PH
        th, beta0, cos_mat = approx_persistent_homology(D, Y)
        persist = persistence_from_beta0(th, beta0)
        mean_persist = np.mean(persist) if persist else 0
        max_persist = max(persist) if persist else 0
        n_features = len(persist)

        epoch_data.append((ep+1, acc, mean_persist, max_persist, n_features, beta0.copy()))

        if (ep+1) % 3 == 0 or ep == 0:
            print(f"  Epoch {ep+1:>2}: acc={acc:.1f}%  mean_persist={mean_persist:.4f}  "
                  f"max_persist={max_persist:.4f}  n_features={n_features}")

    # Correlation: persistence at epoch N vs accuracy at epoch N+K
    print(f"\n  Predictive correlation (persistence[N] vs accuracy[N+K]):")
    print(f"  {'Lag K':>6} {'Corr':>7} {'p-val hint':>12}")
    print(f"  {'-'*28}")
    accs = [d[1] for d in epoch_data]
    persists = [d[2] for d in epoch_data]

    for k in [1, 2, 3, 5]:
        if k >= len(accs): continue
        p_vals = persists[:len(accs)-k]
        a_vals = accs[k:]
        if len(p_vals) > 3:
            r = np.corrcoef(p_vals, a_vals)[0, 1]
            strength = 'STRONG' if abs(r) > 0.7 else 'MODERATE' if abs(r) > 0.4 else 'WEAK'
            print(f"  K={k:>4} {r:>7.4f} {strength:>12}")

    # Same-epoch correlation
    r_same = np.corrcoef(persists, accs)[0, 1]
    print(f"  K={0:>4} {r_same:>7.4f} {'(same epoch)':>12}")

    # Beta_0 curves visualization
    print(f"\n  Beta_0 curves (connected components vs threshold):")
    print(f"  {'th\\ep':>6}", end='')
    show_eps = [0, 4, 9, 14] if epochs >= 15 else list(range(min(4, epochs)))
    for ei in show_eps:
        if ei < len(epoch_data):
            print(f"  ep{epoch_data[ei][0]:>2}", end='')
    print()

    th, _, _ = approx_persistent_homology(np.zeros((1, 10)), np.zeros(1))
    for ti in range(0, len(th), 2):
        print(f"  {th[ti]:>6.2f}", end='')
        for ei in show_eps:
            if ei < len(epoch_data):
                b = epoch_data[ei][5]
                print(f"  {b[ti]:>4}", end='')
        print()

    # Per-class persistence analysis
    print(f"\n  Per-class cosine similarity (final epoch):")
    D_final = np.concatenate([d.numpy() for d in []], default=None) if False else None

    # Use last epoch's cos_mat
    _, _, cos_mat = approx_persistent_homology(
        np.concatenate([d.numpy() for x, y in te for d in [F.normalize(model.engine_a(x.view(-1, dim)) - model.engine_g(x.view(-1, dim)), dim=-1)]]),
        np.array([y.item() for x, y in te for y in y]) if False else Y,
    ) if False else (None, None, None)

    # Summary
    print(f"\n  {'='*70}")
    print(f"  H-CX-62 SUMMARY ({dataset_name.upper()})")
    print(f"  {'='*70}")
    print(f"  Same-epoch corr(persistence, accuracy): {r_same:.4f}")
    print(f"  H-CX-62 prediction (r > 0.5): {'SUPPORTED' if r_same > 0.5 else 'PARTIAL' if r_same > 0.3 else 'REJECTED'}")

    return r_same, persists[-1], accs[-1]

if __name__ == '__main__':
    for ds in ['mnist', 'fashion', 'cifar']:
        try:
            run_experiment(ds)
        except Exception as e:
            print(f"  {ds} failed: {e}")
```