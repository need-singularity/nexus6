#!/usr/bin/env python3
"""H-CX-62 v2 verification: Topological Precognition — Real Persistent Homology calculation with Ripser

v1 failure cause: Approximate PH function bug (persistence=0)
v2: Actual PH calculation with ripser library
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from sklearn.metrics import roc_auc_score
from ripser import ripser
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data


def compute_ph_features(D, Y, n_cls=10):
    """Calculate PH of class mean directions (Ripser)"""
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

    # Cosine distance matrix
    cos_sim = means @ means.T
    cos_dist = 1 - cos_sim
    np.fill_diagonal(cos_dist, 0)
    cos_dist = np.clip(cos_dist, 0, 2)  # ensure non-negative

    # Ripser PH computation
    result = ripser(cos_dist, maxdim=1, distance_matrix=True)
    diagrams = result['dgms']

    # H0 features (connected components)
    h0 = diagrams[0]
    h0_finite = h0[h0[:, 1] < np.inf]
    h0_persist = h0_finite[:, 1] - h0_finite[:, 0] if len(h0_finite) > 0 else np.array([0])

    # H1 features (loops)
    h1 = diagrams[1] if len(diagrams) > 1 else np.array([]).reshape(0, 2)
    h1_persist = h1[:, 1] - h1[:, 0] if len(h1) > 0 else np.array([0])

    features = {
        'h0_mean_persist': np.mean(h0_persist) if len(h0_persist) > 0 else 0,
        'h0_max_persist': np.max(h0_persist) if len(h0_persist) > 0 else 0,
        'h0_n_features': len(h0_finite),
        'h0_total_persist': np.sum(h0_persist),
        'h1_mean_persist': np.mean(h1_persist) if len(h1_persist) > 0 else 0,
        'h1_max_persist': np.max(h1_persist) if len(h1_persist) > 0 else 0,
        'h1_n_features': len(h1),
        'h1_total_persist': np.sum(h1_persist),
    }

    return features, diagrams, cos_dist


def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()

    print(f"\n{'='*70}")
    print(f"  H-CX-62 v2: Topological Precognition (Ripser) — {dataset_name.upper()}")
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

        # Compute PH with Ripser
        ph_feat, diagrams, cos_dist = compute_ph_features(D, Y)
        epoch_data.append((ep+1, acc, ph_feat, diagrams, cos_dist))

        if (ep+1) % 3 == 0 or ep == 0:
            print(f"  Epoch {ep+1:>2}: acc={acc:.1f}%  "
                  f"H0: n={ph_feat['h0_n_features']} mean={ph_feat['h0_mean_persist']:.4f} max={ph_feat['h0_max_persist']:.4f}  "
                  f"H1: n={ph_feat['h1_n_features']} mean={ph_feat['h1_mean_persist']:.4f}")

    # Epoch trajectory table
    print(f"\n  {'Ep':>3} {'Acc%':>6} {'H0_n':>5} {'H0_mean':>8} {'H0_max':>8} {'H0_total':>9} {'H1_n':>5} {'H1_mean':>8}")
    print(f"  {'-'*58}")
    accs = []
    h0_means, h0_maxs, h0_totals, h1_ns = [], [], [], []
    for ep, acc, feat, _, _ in epoch_data:
        print(f"  {ep:>3} {acc:>6.1f} {feat['h0_n_features']:>5} {feat['h0_mean_persist']:>8.4f} "
              f"{feat['h0_max_persist']:>8.4f} {feat['h0_total_persist']:>9.4f} "
              f"{feat['h1_n_features']:>5} {feat['h1_mean_persist']:>8.4f}")
        accs.append(acc)
        h0_means.append(feat['h0_mean_persist'])
        h0_maxs.append(feat['h0_max_persist'])
        h0_totals.append(feat['h0_total_persist'])
        h1_ns.append(feat['h1_n_features'])

    # Correlation analysis
    print(f"\n  Correlation analysis:")
    metrics = {
        'H0_mean_persist': h0_means,
        'H0_max_persist': h0_maxs,
        'H0_total_persist': h0_totals,
        'H1_n_features': h1_ns,
    }

    for name, vals in metrics.items():
        if np.std(vals) < 1e-10:
            print(f"  Corr({name}, accuracy): N/A (constant)")
            continue
        r = np.corrcoef(vals, accs)[0, 1]
        print(f"  Corr({name}, accuracy): {r:>7.4f}  {'STRONG' if abs(r) > 0.7 else 'MODERATE' if abs(r) > 0.4 else 'WEAK'}")

    # Predictive: persistence[N] vs accuracy[N+K]
    print(f"\n  Predictive correlation (H0_total[N] → accuracy[N+K]):")
    for k in [1, 2, 3, 5]:
        if k >= len(accs): continue
        p = h0_totals[:len(accs)-k]
        a = accs[k:]
        if len(p) > 3 and np.std(p) > 1e-10:
            r = np.corrcoef(p, a)[0, 1]
            print(f"  K={k}: r={r:>7.4f}  {'PREDICTIVE' if abs(r) > 0.5 else 'weak'}")

    # Birth-Death diagram (ASCII)
    _, _, feat_final, diag_final, dist_final = epoch_data[-1]
    h0_final = diag_final[0]
    h1_final = diag_final[1] if len(diag_final) > 1 else np.array([]).reshape(0, 2)

    print(f"\n  Birth-Death Diagram (final epoch):")
    print(f"  H0 (connected components): {len(h0_final)} features")
    for i, (b, d) in enumerate(h0_final):
        d_str = f"{d:.4f}" if d < np.inf else "inf"
        persist = d - b if d < np.inf else float('inf')
        bar_len = min(int(persist * 20), 40) if persist < np.inf else 40
        print(f"    [{b:.4f}, {d_str}] persist={persist:.4f if persist < np.inf else 'inf':>8} |{'█'*bar_len}|")

    if len(h1_final) > 0:
        print(f"  H1 (loops): {len(h1_final)} features")
        for i, (b, d) in enumerate(h1_final[:10]):
            persist = d - b
            bar_len = min(int(persist * 20), 40)
            print(f"    [{b:.4f}, {d:.4f}] persist={persist:.4f} |{'█'*bar_len}|")

    # Cosine distance matrix (final epoch)
    print(f"\n  Cosine Distance Matrix (final epoch):")
    print(f"  {'':>7}", end='')
    for n in names: print(f" {n[:5]:>6}", end='')
    print()
    for i in range(len(names)):
        print(f"  {names[i][:5]:>7}", end='')
        for j in range(len(names)):
            print(f" {dist_final[i,j]:>6.3f}", end='')
        print()

    # Summary
    r_same = np.corrcoef(h0_totals, accs)[0, 1] if np.std(h0_totals) > 1e-10 else 0
    print(f"\n  {'='*70}")
    print(f"  H-CX-62 v2 SUMMARY ({dataset_name.upper()})")
    print(f"  {'='*70}")
    print(f"  Same-epoch corr(H0_total, accuracy): {r_same:.4f}")
    print(f"  H-CX-62 prediction (r > 0.5): {'SUPPORTED' if r_same > 0.5 else 'PARTIAL' if r_same > 0.3 else 'REJECTED'}")

    return r_same, h0_totals[-1], accs[-1]

if __name__ == '__main__':
    for ds in ['mnist', 'fashion', 'cifar']:
        try:
            run_experiment(ds)
        except Exception as e:
            print(f"  {ds} failed: {e}")
            import traceback; traceback.print_exc()