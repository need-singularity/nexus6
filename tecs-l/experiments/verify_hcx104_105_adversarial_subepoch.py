#!/usr/bin/env python3
"""H-CX-104 + H-CX-105: FGSM Vulnerability + Sub-epoch Transition

H-CX-104: Short merge distance pairs → FGSM vulnerable
H-CX-105: Phase transition occurs at 0.5 epochs
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from scipy.stats import spearmanr
from ripser import ripser
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data


def compute_h0(D, Y, n_cls=10):
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
    return np.sum(h0_finite[:, 1] - h0_finite[:, 0]) if len(h0_finite) > 0 else 0, cos_dist


def get_merges(cos_dist, n_cls=10):
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


def fgsm_attack(model, x, y, dim, epsilon=0.1):
    """FGSM attack on PureFieldEngine"""
    x_flat = x.view(-1, dim).requires_grad_(True)
    out, _ = model(x_flat)
    loss = F.cross_entropy(out, y)
    loss.backward()
    x_adv = x_flat + epsilon * x_flat.grad.sign()
    x_adv = torch.clamp(x_adv, -3, 3)  # approximate bounds
    return x_adv.detach()


def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    n_cls = len(names)

    print(f"\n{'='*70}")
    print(f"  H-CX-104+105 — {dataset_name.upper()}")
    print(f"{'='*70}")

    torch.manual_seed(42)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()

    # === H-CX-105: Sub-epoch tracking ===
    print(f"\n  === H-CX-105: Sub-epoch Phase Transition ===")

    # Track H0 at fractional epochs (every 10% of first epoch)
    steps_per_epoch = sum(1 for _ in tl)
    check_points = [int(steps_per_epoch * f) for f in [0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]]

    model.eval()
    dirs0 = []
    with torch.no_grad():
        for x, y in te:
            rep = model.engine_a(x.view(-1, dim)) - model.engine_g(x.view(-1, dim))
            dirs0.append(F.normalize(rep, dim=-1).numpy())
    D0 = np.concatenate(dirs0)
    Y_te_arr = np.concatenate([y.numpy() for _, y in te])
    h0_init, _ = compute_h0(D0, Y_te_arr, n_cls)

    sub_h0s = [(0, h0_init)]
    model.train()
    step = 0
    for x, y in tl:
        opt.zero_grad()
        out, t = model(x.view(-1, dim))
        loss = ce(out, y); loss.backward(); opt.step()
        step += 1

        if step in check_points and step > 0:
            frac = step / steps_per_epoch
            model.eval()
            dirs_s = []
            with torch.no_grad():
                for xt, yt in te:
                    rep = model.engine_a(xt.view(-1, dim)) - model.engine_g(xt.view(-1, dim))
                    dirs_s.append(F.normalize(rep, dim=-1).numpy())
            D_s = np.concatenate(dirs_s)
            h0_s, _ = compute_h0(D_s, Y_te_arr, n_cls)
            sub_h0s.append((frac, h0_s))
            model.train()

    print(f"  {'Frac':>6} {'H0':>8} {'dH0':>8}")
    print(f"  {'-'*25}")
    for i, (frac, h0) in enumerate(sub_h0s):
        dh0 = abs(h0 - sub_h0s[i-1][1]) if i > 0 else 0
        bar = int(min(dh0 * 10, 20))
        print(f"  {frac:>6.1f} {h0:>8.4f} {dh0:>8.4f} {'█'*bar}")

    # Find where 80% of total change happens
    total_change = abs(sub_h0s[-1][1] - sub_h0s[0][1])
    cumulative = 0
    transition_frac = 1.0
    for i in range(1, len(sub_h0s)):
        cumulative += abs(sub_h0s[i][1] - sub_h0s[i-1][1])
        if cumulative >= 0.8 * total_change:
            transition_frac = sub_h0s[i][0]
            break
    print(f"\n  80% of H0 change by: {transition_frac:.1f} epoch")
    print(f"  H-CX-105 (transition < 0.5 epoch): {'SUPPORTED' if transition_frac <= 0.5 else 'REJECTED'}")

    # Continue full training
    for ep in range(1, epochs):
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
            print(f"  Epoch {ep+1}: acc={c/t_*100:.1f}%")

    # === H-CX-104: FGSM attack ===
    print(f"\n  === H-CX-104: FGSM Adversarial Vulnerability ===")

    # Get merge order
    model.eval()
    dirs_f, ys_f, preds_f = [], [], []
    with torch.no_grad():
        for x, y in te:
            x_flat = x.view(-1, dim)
            rep = model.engine_a(x_flat) - model.engine_g(x_flat)
            d = F.normalize(rep, dim=-1)
            out = model.tension_scale * torch.sqrt((rep**2).mean(-1, keepdim=True)+1e-8) * d
            dirs_f.append(d.numpy()); ys_f.extend(y.numpy()); preds_f.extend(out.argmax(1).numpy())
    D_f = np.concatenate(dirs_f); Y_f = np.array(ys_f); P_f = np.array(preds_f)
    _, cos_dist = compute_h0(D_f, Y_f, n_cls)
    merges = get_merges(cos_dist, n_cls)

    # FGSM attack and measure per-pair vulnerability
    pair_vuln = {}
    for epsilon in [0.05, 0.1, 0.2]:
        adv_preds = []
        model.eval()
        for x, y in te:
            x_adv = fgsm_attack(model, x, y, dim, epsilon)
            with torch.no_grad():
                out_adv, _ = model(x_adv)
            adv_preds.extend(out_adv.argmax(1).numpy().tolist())
        P_adv = np.array(adv_preds)

        # Count adversarial flips per pair
        for idx in range(len(Y_f)):
            if P_f[idx] == Y_f[idx] and P_adv[idx] != Y_f[idx]:  # correct→wrong
                pair = (min(Y_f[idx], P_adv[idx]), max(Y_f[idx], P_adv[idx]))
                if pair not in pair_vuln:
                    pair_vuln[pair] = 0
                pair_vuln[pair] += 1

    # Compare merge order vs vulnerability
    sorted_vuln = sorted(pair_vuln.items(), key=lambda x: -x[1])
    merge_dists = {(min(i,j),max(i,j)): d for d,i,j in merges}

    all_pairs = sorted(set(list(pair_vuln.keys()) + list(merge_dists.keys())))
    vuln_vals = [pair_vuln.get(p, 0) for p in all_pairs]
    dist_vals = [merge_dists.get(p, 999) for p in all_pairs]

    r104, p104 = spearmanr(dist_vals, vuln_vals)
    print(f"  Spearman(merge_dist, FGSM_vuln): r={r104:.4f}, p={p104:.4f}")
    print(f"  (Expected: r < 0, closer = more vulnerable)")

    print(f"\n  Top-5 FGSM vulnerable pairs:")
    for (a, b), cnt in sorted_vuln[:5]:
        dist = merge_dists.get((a,b), 999)
        print(f"    {names[a]:>6}-{names[b]:<6}: vuln={cnt}, merge_dist={dist:.4f}")

    top5_vuln = set(p for p, c in sorted_vuln[:5])
    top5_merge = set((min(i,j),max(i,j)) for d,i,j in merges[:5])
    overlap = len(top5_vuln & top5_merge)
    print(f"  Top-5 overlap (vuln vs merge): {overlap}/5")
    print(f"  H-CX-104 (r < -0.3): {'SUPPORTED' if r104 < -0.3 else 'PARTIAL' if r104 < 0 else 'REJECTED'}")

    return {
        'transition_frac': transition_frac,
        'r_104': r104, 'overlap': overlap,
    }


if __name__ == '__main__':
    for ds in ['mnist', 'fashion', 'cifar']:
        try:
            run_experiment(ds)
        except Exception as e:
            print(f"  {ds} failed: {e}")
            import traceback; traceback.print_exc()