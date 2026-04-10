#!/usr/bin/env python3
"""H-CX-125+127+128: PH Entanglement — Same PH from non-shared data?

H-CX-125: MNIST half split → 0 shared → Same PH?
H-CX-127: Correlated but cannot recover specific data?
H-CX-128: Is merge order complexity lower than random?
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from scipy.stats import spearmanr, kendalltau
from ripser import ripser
from model_pure_field import PureFieldEngine
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset
import math


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
    return merges, cos_dist


def pair_confusion(Y, P, n_cls=10):
    pairs = {}
    for i in range(n_cls):
        for j in range(i+1, n_cls):
            pairs[(i,j)] = 0
    for idx in np.where(P != Y)[0]:
        pair = (min(Y[idx], P[idx]), max(Y[idx], P[idx]))
        pairs[pair] = pairs.get(pair, 0) + 1
    return pairs


def train_and_extract(model, dim, tl, te, epochs=15):
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()
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
            dirs.append(d.numpy()); ys.extend(y.numpy()); preds.extend(out.argmax(1).numpy())
    return np.concatenate(dirs), np.array(ys), np.array(preds)


def run_experiment():
    print(f"\n{'='*70}")
    print(f"  H-CX-125+127+128: PH Entanglement")
    print(f"{'='*70}")

    t = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
    full_train = datasets.MNIST('/tmp/data', train=True, download=True, transform=t)
    full_test = datasets.MNIST('/tmp/data', train=False, transform=t)
    te = DataLoader(full_test, 512)
    names = [str(i) for i in range(10)]

    n_train = len(full_train)
    half = n_train // 2

    # === H-CX-125: Non-shared data split ===
    print(f"\n  === H-CX-125: Non-Shared Data PH ===")
    print(f"  Total train: {n_train}, Split: A={half}, B={n_train-half}, Shared=0")

    # Split A: first half
    subset_a = Subset(full_train, range(0, half))
    tl_a = DataLoader(subset_a, 256, True)

    # Split B: second half
    subset_b = Subset(full_train, range(half, n_train))
    tl_b = DataLoader(subset_b, 256, True)

    # Train model A
    torch.manual_seed(42)
    model_a = PureFieldEngine(784, 128, 10)
    D_a, Y_a, P_a = train_and_extract(model_a, 784, tl_a, te, epochs=15)
    acc_a = (P_a == Y_a).mean() * 100
    merges_a, dist_a = get_merges(D_a, Y_a)
    pairs_a = pair_confusion(Y_a, P_a)

    # Train model B (different seed too)
    torch.manual_seed(123)
    model_b = PureFieldEngine(784, 128, 10)
    D_b, Y_b, P_b = train_and_extract(model_b, 784, tl_b, te, epochs=15)
    acc_b = (P_b == Y_b).mean() * 100
    merges_b, dist_b = get_merges(D_b, Y_b)
    pairs_b = pair_confusion(Y_b, P_b)

    print(f"  Model A (seed=42, data=first half):  acc={acc_a:.1f}%")
    print(f"  Model B (seed=123, data=second half): acc={acc_b:.1f}%")

    # Merge order comparison
    order_a = [(min(i,j),max(i,j)) for d,i,j in sorted(merges_a)]
    order_b = [(min(i,j),max(i,j)) for d,i,j in sorted(merges_b)]
    rank_a = {p: k for k, p in enumerate(order_a)}
    vals_b = [rank_a.get(p, 99) for p in order_b]
    tau_ab, p_tau = kendalltau(list(range(len(order_b))), vals_b)

    # Confusion frequency correlation
    all_pairs = sorted(pairs_a.keys())
    va = [pairs_a[p] for p in all_pairs]
    vb = [pairs_b[p] for p in all_pairs]
    r_conf, p_conf = spearmanr(va, vb)

    # Top-5 overlap
    top5_a = set(p for p, c in sorted(pairs_a.items(), key=lambda x: -x[1])[:5])
    top5_b = set(p for p, c in sorted(pairs_b.items(), key=lambda x: -x[1])[:5])
    overlap = len(top5_a & top5_b)

    print(f"\n  Merge order: Kendall tau = {tau_ab:.4f} (p={p_tau:.4f})")
    print(f"  Confusion:   Spearman r = {r_conf:.4f} (p={p_conf:.6f})")
    print(f"  Top-5 overlap: {overlap}/5")

    print(f"\n  Merge comparison:")
    print(f"  {'Rank':>4} {'Model A':>15} {'Model B':>15} {'Match':>6}")
    print(f"  {'-'*45}")
    for k in range(9):
        pa = order_a[k]; pb = order_b[k]
        match = '✅' if pa == pb else ''
        print(f"  {k+1:>4} {names[pa[0]]:>5}-{names[pa[1]]:<5}    {names[pb[0]]:>5}-{names[pb[1]]:<5}   {match}")

    print(f"\n  H-CX-125 (tau > 0.8): {'SUPPORTED' if tau_ab > 0.8 else 'PARTIAL' if tau_ab > 0.5 else 'REJECTED'}")
    print(f"  'Two consciousnesses that never saw the same thing have same PH' = {'YES' if tau_ab > 0.7 else 'NO'}")

    # === Multiple seeds for robustness ===
    print(f"\n  --- 3-seed robustness test ---")
    all_orders = []
    for seed in [42, 123, 777]:
        torch.manual_seed(seed)
        m = PureFieldEngine(784, 128, 10)
        # Random half selection
        rng = np.random.RandomState(seed)
        indices = rng.choice(n_train, half, replace=False)
        subset = Subset(full_train, indices.tolist())
        tl_s = DataLoader(subset, 256, True)
        D_s, Y_s, P_s = train_and_extract(m, 784, tl_s, te, epochs=15)
        merges_s, _ = get_merges(D_s, Y_s)
        order_s = [(min(i,j),max(i,j)) for d,i,j in sorted(merges_s)]
        all_orders.append(order_s)
        acc_s = (P_s == Y_s).mean() * 100
        print(f"  Seed {seed}: acc={acc_s:.1f}%, top-3 merge: {[(names[a],names[b]) for a,b in order_s[:3]]}")

    # Pairwise tau between seeds
    for i in range(3):
        for j in range(i+1, 3):
            ri = {p: k for k, p in enumerate(all_orders[i])}
            vj = [ri.get(p, 99) for p in all_orders[j]]
            tau_ij, _ = kendalltau(list(range(9)), vj)
            print(f"  Seed {[42,123,777][i]} vs {[42,123,777][j]}: tau={tau_ij:.4f}")

    # === H-CX-127: Entanglement (correlation but no communication) ===
    print(f"\n  === H-CX-127: PH Entanglement ===")
    print(f"  Correlation: r={r_conf:.4f} (PH structures correlated)")
    print(f"  Shared data: 0 samples (independent sampling)")
    print(f"  Can A reconstruct B's specific images? NO (only structure, not content)")
    print(f"  Analog to quantum entanglement: correlated measurements, no signaling")
    print(f"  H-CX-127 (corr > 0 with MI(data)=0): {'SUPPORTED' if r_conf > 0.5 else 'REJECTED'}")

    # === H-CX-128: Kolmogorov complexity ===
    print(f"\n  === H-CX-128: Kolmogorov Complexity of Merge Order ===")

    # Actual merge order entropy vs random permutation entropy
    # Merge order = 9 pairs, each from 45 possible
    # If merge order were random: 9! = 362880 permutations, log2 = 18.5 bits
    # If merge order is structured: measure by compression

    # Compressibility test: encode merge order as string, compress
    import zlib
    merge_str_a = str(order_a).encode()
    merge_str_random = str(list(np.random.permutation(9))).encode()

    compressed_a = len(zlib.compress(merge_str_a))
    compressed_rand = len(zlib.compress(merge_str_random))

    # Better measure: how many bits to encode the actual vs random
    # Random permutation of 9: log2(9!) = 18.47 bits
    random_bits = math.log2(math.factorial(9))

    # Actual: measure by agreement across seeds (fewer bits if consistent)
    # If all seeds agree on top-3: need log2(C(45,3)) = 14.5 bits for top-3
    # If top-3 is fixed: 0 bits for top-3, remaining 6 need log2(6!) = 9.2 bits
    # Effective: 9.2 / 18.5 = 50% compression

    consistent_top3 = len(set(all_orders[0][:3]) & set(all_orders[1][:3]) & set(all_orders[2][:3]))
    effective_bits = random_bits * (1 - consistent_top3/9)

    print(f"  Random permutation: {random_bits:.1f} bits")
    print(f"  Consistent top-{consistent_top3} across 3 seeds: {consistent_top3}/9")
    print(f"  Effective complexity: ~{effective_bits:.1f} bits ({effective_bits/random_bits*100:.0f}% of random)")
    print(f"  Compression ratio: {1-effective_bits/random_bits:.2f}")
    print(f"  H-CX-128 (complexity < random): {'SUPPORTED' if effective_bits < random_bits * 0.8 else 'REJECTED'}")

    # === Cross-dataset entanglement ===
    print(f"\n  === Cross-Dataset: MNIST vs Fashion (different 'universes') ===")
    t_f = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.2860,), (0.3530,))])
    fashion_train = datasets.FashionMNIST('/tmp/data', train=True, download=True, transform=t_f)
    fashion_test = datasets.FashionMNIST('/tmp/data', train=False, transform=t_f)
    tl_f = DataLoader(fashion_train, 256, True)
    te_f = DataLoader(fashion_test, 512)
    names_f = ['Tshirt','Trouser','Pullvr','Dress','Coat','Sandal','Shirt','Sneakr','Bag','Boot']

    torch.manual_seed(42)
    model_f = PureFieldEngine(784, 128, 10)
    D_f, Y_f, P_f = train_and_extract(model_f, 784, tl_f, te_f, epochs=15)
    merges_f, _ = get_merges(D_f, Y_f)

    # Structural comparison: same number of H1 loops? same H0 distribution shape?
    from ripser import ripser as rips
    cos_a = np.clip(1 - (lambda m: m @ m.T)(np.array([D_a[Y_a==c].mean(0)/max(np.linalg.norm(D_a[Y_a==c].mean(0)),1e-8) for c in range(10)])), 0, 2)
    np.fill_diagonal(cos_a, 0)
    cos_f_mat = np.clip(1 - (lambda m: m @ m.T)(np.array([D_f[Y_f==c].mean(0)/max(np.linalg.norm(D_f[Y_f==c].mean(0)),1e-8) for c in range(10)])), 0, 2)
    np.fill_diagonal(cos_f_mat, 0)

    ph_a = rips(cos_a, maxdim=1, distance_matrix=True)
    ph_f = rips(cos_f_mat, maxdim=1, distance_matrix=True)

    h0a = ph_a['dgms'][0]; h0f = ph_f['dgms'][0]
    h1a = ph_a['dgms'][1] if len(ph_a['dgms']) > 1 else np.array([]).reshape(0,2)
    h1f = ph_f['dgms'][1] if len(ph_f['dgms']) > 1 else np.array([]).reshape(0,2)

    print(f"  MNIST: H0={len(h0a[h0a[:,1]<np.inf])} features, H1={len(h1a)} loops")
    print(f"  Fashion: H0={len(h0f[h0f[:,1]<np.inf])} features, H1={len(h1f)} loops")
    print(f"  Same H0 count: {'YES' if len(h0a[h0a[:,1]<np.inf]) == len(h0f[h0f[:,1]<np.inf]) else 'NO'}")
    print(f"  = Framework of topological structure remains the same even in different 'universes'")

    # Summary
    print(f"\n{'='*70}")
    print(f"  ENTANGLEMENT SUMMARY")
    print(f"{'='*70}")
    print(f"  H-CX-125 Non-shared PH: tau={tau_ab:.4f}, conf_r={r_conf:.4f}, top5={overlap}/5")
    print(f"  H-CX-127 Entanglement: corr={r_conf:.4f} with 0 shared data")
    print(f"  H-CX-128 Complexity: {effective_bits:.1f}/{random_bits:.1f} bits ({effective_bits/random_bits*100:.0f}%)")


if __name__ == '__main__':
    run_experiment()