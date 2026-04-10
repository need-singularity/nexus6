```python
#!/usr/bin/env python3
"""H-CX-110~115: Zodiac 12 Mathematics Hypothesis Integrated Verification

H-CX-110: σ(6)=12 perfect partition — 10/12/13 class PH comparison
H-CX-111: 13th = observer — 12cls train → 13th OOD tension
H-CX-112: ln(13/12) information jump — N-state width comparison
H-CX-113: 12 Expert MoE — expert sweep
H-CX-114: dendrogram root = metacognition
H-CX-115: kissing number — directional most dense arrangement
"""
import sys, math
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from scipy.stats import spearmanr
from ripser import ripser
from model_pure_field import PureFieldEngine
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset


def compute_ph(D, Y, n_cls):
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
    result = ripser(cos_dist, maxdim=1, distance_matrix=True)
    h0 = result['dgms'][0]
    h1 = result['dgms'][1] if len(result['dgms']) > 1 else np.array([]).reshape(0, 2)
    h0_finite = h0[h0[:, 1] < np.inf]
    h0_total = np.sum(h0_finite[:, 1] - h0_finite[:, 0]) if len(h0_finite) > 0 else 0
    h1_total = np.sum(h1[:, 1] - h1[:, 0]) if len(h1) > 0 else 0
    return h0_total, len(h0_finite), h1_total, len(h1), cos_dist, means


def train_and_extract(model, dim, tl, te, n_cls, epochs=10):
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
            out = model.tension_scale * torch.sqrt(t.unsqueeze(-1) + 1e-8) * d
            dirs.append(d.numpy()); ys.extend(y.numpy())
            preds.extend(out.argmax(1).numpy()); tensions.extend(t.numpy())
    return np.concatenate(dirs), np.array(ys), np.array(preds), np.array(tensions)


def load_combined_12_13():
    """MNIST(10) + FashionMNIST first 3 classes = 13 class dataset"""
    t = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])

    mnist_tr = datasets.MNIST('/tmp/data', train=True, download=True, transform=t)
    mnist_te = datasets.MNIST('/tmp/data', train=False, transform=t)

    fashion_tr = datasets.FashionMNIST('/tmp/data', train=True, download=True, transform=t)
    fashion_te = datasets.FashionMNIST('/tmp/data', train=False, transform=t)

    # Fashion 0,1,2 → relabel as 10,11,12
    fashion_tr_sub = [(x, y + 10) for x, y in fashion_tr if y < 3]
    fashion_te_sub = [(x, y + 10) for x, y in fashion_te if y < 3]

    # Combined
    combined_tr = list(mnist_tr) + fashion_tr_sub
    combined_te = list(mnist_te) + fashion_te_sub

    return combined_tr, combined_te


def run_experiment():
    print(f"\n{'='*70}")
    print(f"  H-CX-110~115: Zodiac 12 Mathematics")
    print(f"{'='*70}")

    # === H-CX-112: N-state width comparison (pure math) ===
    print(f"\n  === H-CX-112: N-state Width ln((N+1)/N) ===")
    print(f"  {'N':>4} {'N+1':>4} {'ln((N+1)/N)':>12} {'Special Point':>8}")
    print(f"  {'-'*35}")
    widths = []
    for N in range(2, 20):
        w = math.log((N+1)/N)
        special = ''
        if N == 6: special = 'σ₋₁(6)=2'
        elif N == 12: special = 'σ(6)=12'
        elif N == 13: special = '13=prime'
        elif N == 3: special = 'τ(6)-1'
        elif N == 5: special = '6-1'
        widths.append((N, w))
        print(f"  {N:>4} {N+1:>4} {w:>12.6f} {special:>8}")

    # Is 12→13 special? Compare to neighbors
    w_11_12 = math.log(12/11)
    w_12_13 = math.log(13/12)
    w_13_14 = math.log(14/13)
    print(f"\n  11→12: {w_11_12:.6f}")
    print(f"  12→13: {w_12_13:.6f}  (σ(6)→prime)")
    print(f"  13→14: {w_13_14:.6f}")
    print(f"  12→13 / golden_width: {w_12_13 / math.log(4/3):.6f}")
    print(f"  12→13 × 12: {w_12_13 * 12:.6f} (≈1? = {abs(w_12_13 * 12 - 1):.6f})")
    # ln(13/12) * 12 = 12*ln(13/12) ≈ ln((13/12)^12) = ln(13^12/12^12)

    # === H-CX-110: 10 vs 12 vs 13 class PH ===
    print(f"\n  === H-CX-110: Class Count vs PH Topology ===")

    # Use MNIST (10cls) and combined (13cls)
    t = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
    mnist_tr = datasets.MNIST('/tmp/data', train=True, download=True, transform=t)
    mnist_te = datasets.MNIST('/tmp/data', train=False, transform=t)
    tl_10 = DataLoader(mnist_tr, 256, True)
    te_10 = DataLoader(mnist_te, 512)

    # 10-class
    torch.manual_seed(42)
    model_10 = PureFieldEngine(784, 128, 10)
    D10, Y10, P10, T10 = train_and_extract(model_10, 784, tl_10, te_10, 10, epochs=10)
    h0_10, h0n_10, h1_10, h1n_10, _, _ = compute_ph(D10, Y10, 10)
    acc_10 = (P10 == Y10).mean() * 100
    print(f"  10cls: acc={acc_10:.1f}%  H0_total={h0_10:.4f}({h0n_10})  H1_total={h1_10:.4f}({h1n_10})")

    # 12-class (MNIST 10 + Fashion 2)
    fashion_tr = datasets.FashionMNIST('/tmp/data', train=True, download=True, transform=t)
    fashion_te = datasets.FashionMNIST('/tmp/data', train=False, transform=t)

    combined_12_tr = [(x, y) if y < 10 else None for x, y in mnist_tr]
    combined_12_tr = [(x, y) for x, y in mnist_tr]
    # Add fashion 0,1 as class 10,11
    f_tr_2 = [(x, torch.tensor(y.item() + 10) if isinstance(y, torch.Tensor) else y + 10)
              for x, y in fashion_tr if (y.item() if isinstance(y, torch.Tensor) else y) < 2]
    f_te_2 = [(x, torch.tensor(y.item() + 10) if isinstance(y, torch.Tensor) else y + 10)
              for x, y in fashion_te if (y.item() if isinstance(y, torch.Tensor) else y) < 2]

    combined_12_tr_list = list(mnist_tr) + f_tr_2
    combined_12_te_list = list(mnist_te) + f_te_2
    tl_12 = DataLoader(combined_12_tr_list, 256, True)
    te_12 = DataLoader(combined_12_te_list, 512)

    torch.manual_seed(42)
    model_12 = PureFieldEngine(784, 128, 12)
    D12, Y12, P12, T12 = train_and_extract(model_12, 784, tl_12, te_12, 12, epochs=10)
    h0_12, h0n_12, h1_12, h1n_12, _, _ = compute_ph(D12, Y12, 12)
    acc_12 = (P12 == Y12).mean() * 100
    print(f"  12cls: acc={acc_12:.1f}%  H0_total={h0_12:.4f}({h0n_12})  H1_total={h1_12:.4f}({h1n_12})")

    # 13-class (MNIST 10 + Fashion 3)
    f_tr_3 = [(x, torch.tensor(y.item() + 10) if isinstance(y, torch.Tensor) else y + 10)
              for x, y in fashion_tr if (y.item() if isinstance(y, torch.Tensor) else y) < 3]
    f_te_3 = [(x, torch.tensor(y.item() + 10) if isinstance(y, torch.Tensor) else y + 10)
              for x, y in fashion_te if (y.item() if isinstance(y, torch.Tensor) else y) < 3]

    combined_13_tr_list = list(mnist_tr) + f_tr_3
    combined_13_te_list = list(mnist_te) + f_te_3
    tl_13 = DataLoader(combined_13_tr_list, 256, True)
    te_13 = DataLoader(combined_13_te_list, 512)

    torch.manual_seed(42)
    model_13 = PureFieldEngine(784, 128, 13)
    D13, Y13, P13, T13 = train_and_extract(model_13, 784, tl_13, te_13, 13, epochs=10)
    h0_13, h0n_13, h1_13, h1n_13, _, _ = compute_ph(D13, Y13, 13)
    acc_13 = (P13 == Y13).mean() * 100
    print(f"  13cls: acc={acc_13:.1f}%  H0_total={h0_13:.4f}({h0n_13})  H1_total={h1_13:.4f}({h1n_13})")

    print(f"\n  H1 loop comparison (H-CX-110 prediction: 13cls has more H1):")
    print(f"    10cls H1: {h1n_10} loops (total={h1_10:.4f})")
    print(f"    12cls H1: {h1n_12} loops (total={h1_12:.4f})")
    print(f"    13cls H1: {h1n_13} loops (total={h1_13:.4f})")
    print(f"    H-CX-110 (13 > 12 H1): {'SUPPORTED' if h1n_13 > h1n_12 else 'REJECTED'}")

    # === H-CX-111: 13th class = observer (OOD tension) ===
    print(f"\n  === H-CX-111: 13th Class = Observer (OOD Tension) ===")

    # Use 10-class model, feed Fashion data as OOD
    model_10.eval()
    ood_tensions = []
    with torch.no_grad():
        for x, y in DataLoader(list(fashion_te)[:1000], 256):
            x_flat = x.view(-1, 784)
            rep = model_10.engine_a(x_flat) - model_10.engine_g(x_flat)
            t = (rep**2).mean(-1)
            ood_tensions.extend(t.numpy())

    id_tensions = T10  # in-distribution tensions
    ood_t = np.array(ood_tensions)

    print(f"  In-distribution tension:  mean={id_tensions.mean():.4f}  std={id_tensions.std():.4f}")
    print(f"  OOD (Fashion) tension:    mean={ood_t.mean():.4f}  std={ood_t.std():.4f}")
    print(f"  Ratio (OOD/ID):           {ood_t.mean() / id_tensions.mean():.2f}x")
    print(f"  H-CX-111 (OOD tension > ID): {'SUPPORTED' if ood_t.mean() > id_tensions.mean() else 'REJECTED'}")

    # === H-CX-114: Dendrogram root = metacognition ===
    print(f"\n  === H-CX-114: Dendrogram Root Analysis ===")
    names_13 = [str(i) for i in range(10)] + ['F-Tshirt', 'F-Trouser', 'F-Pullvr']

    _, _, _, _, cos_dist_13, means_13 = compute_ph(D13, Y13, 13)

    # Build dendrogram
    sorted_edges = sorted([(cos_dist_13[i,j], min(i,j), max(i,j))
                           for i in range(13) for j in range(i+1, 13)])
    parent = list(range(13))
    clusters = {i: {i} for i in range(13)}
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            merged = clusters[a] | clusters[b]
            parent[a] = b; clusters[b] = merged
            if a in clusters and a != b: del clusters[a]
            return merged
        return None

    print(f"  13-class dendrogram:")
    last_merge = None
    for dist, i, j in sorted_edges:
        merged = union(i, j)
        if merged and len(merged) >= 2:
            cnames = sorted([names_13[c] for c in merged])
            if len(cnames) <= 6:
                print(f"    d={dist:.4f} → [{', '.join(cnames)}]")
            last_merge = (dist, cnames)

    if last_merge:
        print(f"    ROOT d={last_merge[0]:.4f} → [{', '.join(last_merge[1][:5])}...]")
        # The root merge = the final split = the most fundamental distinction
        # Is it MNIST vs Fashion (digit vs clothing)?
        print(f"    Root split = digits vs clothing? (metacognition = seeing different DOMAINS)")

    # === H-CX-115: Kissing number / direction packing ===
    print(f"\n  === H-CX-115: Direction Packing Density ===")
    for n_cls, D_data, Y_data, label in [(10, D10, Y10, "10cls"), (12, D12, Y12, "12cls"), (13, D13, Y13, "13cls")]:
        _, _, _, _, cos_dist_n, means_n = compute_ph(D_data, Y_data, n_cls)
        # Minimum pairwise cosine distance = how tightly packed
        min_dists = []
        for i in range(n_cls):
            row = cos_dist_n[i].copy(); row[i] = 999
            min_dists.append(row.min())
        avg_min = np.mean(min_dists)
        global_min = min(min_dists)
        print(f"  {label}: avg_min_dist={avg_min:.4f}  global_min={global_min:.4f}  "
              f"{'TIGHT' if global_min < 0.1 else 'NORMAL'}")

    print(f"\n  H-CX-115 (13cls more tight): "
          f"check if 13cls global_min < 12cls global_min")

    # === H-CX-113: Expert sweep (simplified with output_dim) ===
    print(f"\n  === H-CX-113: Expert Count Sweep (via output_dim proxy) ===")
    # Use MNIST, vary output dimensions as proxy for expert count
    for n_out in [6, 8, 10, 12, 13, 16]:
        torch.manual_seed(42)
        # Map 10 MNIST classes into n_out outputs (if n_out >= 10)
        if n_out < 10:
            continue
        m = PureFieldEngine(784, 128, n_out)
        opt = torch.optim.Adam(m.parameters(), lr=1e-3)
        ce = nn.CrossEntropyLoss()
        for ep in range(10):
            m.train()
            for x, y in tl_10:
                opt.zero_grad()
                out, t = m(x.view(-1, 784))
                loss = ce(out[:, :10], y); loss.backward(); opt.step()
        m.eval(); c = t_ = 0
        with torch.no_grad():
            for x, y in te_10:
                o, _ = m(x.view(-1, 784))
                c += (o[:, :10].argmax(1)==y).sum().item(); t_ += y.size(0)
        acc = c / t_ * 100
        ts = m.tension_scale.item()
        print(f"  n_out={n_out:>2}: acc={acc:.1f}%  ts={ts:.4f}")

    # Summary
    print(f"\n{'='*70}")
    print(f"  ZODIAC SUMMARY")
    print(f"{'='*70}")
    print(f"  H-CX-110: 10cls H1={h1n_10}, 12cls H1={h1n_12}, 13cls H1={h1n_13}")
    print(f"  H-CX-111: OOD/ID tension ratio = {ood_t.mean()/id_tensions.mean():.2f}x")
    print(f"  H-CX-112: ln(13/12)={w_12_13:.6f}, 12*ln(13/12)={w_12_13*12:.6f}")


if __name__ == '__main__':
    run_experiment()
```