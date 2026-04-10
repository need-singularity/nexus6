#!/usr/bin/env python3
"""H-CX-446b: Spectral-PH bridge cross-dataset verification

H-CX-446 found SG <-> PH H0 Pearson=0.87 on MNIST.
Test: Does this hold on Fashion-MNIST and CIFAR-10?
If yes, it's a universal bridge between linear algebra and topology.

Also tests per-layer spectral gap (H-CX-445 found layer 0 dominates).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from scipy.stats import pearsonr, spearmanr
from model_pure_field import PureFieldEngine
from torchvision import datasets, transforms


def load_dataset(name, bs=256):
    if name == 'fashion':
        t = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.2860,),(0.3530,))])
        tr = torch.utils.data.DataLoader(datasets.FashionMNIST('~/.cache/fmnist', train=True, download=True, transform=t), batch_size=bs, shuffle=True)
        te = torch.utils.data.DataLoader(datasets.FashionMNIST('~/.cache/fmnist', train=False, transform=t), batch_size=bs)
        dim = 784
        names = ['Tshirt','Trouser','Pullvr','Dress','Coat','Sandal','Shirt','Sneaker','Bag','Boot']
    elif name == 'cifar':
        t_tr = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.4914,0.4822,0.4465),(0.2470,0.2435,0.2616))])
        t_te = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.4914,0.4822,0.4465),(0.2470,0.2435,0.2616))])
        tr = torch.utils.data.DataLoader(datasets.CIFAR10('~/.cache/cifar10', train=True, download=True, transform=t_tr), batch_size=bs, shuffle=True)
        te = torch.utils.data.DataLoader(datasets.CIFAR10('~/.cache/cifar10', train=False, transform=t_te), batch_size=bs)
        dim = 3072
        names = ['plane','car','bird','cat','deer','dog','frog','horse','ship','truck']
    else:  # mnist
        t = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,),(0.3081,))])
        tr = torch.utils.data.DataLoader(datasets.MNIST('~/.cache/mnist', train=True, download=True, transform=t), batch_size=bs, shuffle=True)
        te = torch.utils.data.DataLoader(datasets.MNIST('~/.cache/mnist', train=False, transform=t), batch_size=bs)
        dim = 784
        names = [str(i) for i in range(10)]
    return tr, te, dim, names


def spectral_gaps_per_layer(model):
    """Return dict of layer_name -> SVD gap."""
    gaps = {}
    for name, param in model.named_parameters():
        if 'weight' in name and param.dim() == 2:
            s = torch.linalg.svdvals(param.data)
            if len(s) >= 2:
                gaps[name] = (s[0] - s[1]).item()
    return gaps


def ph_h0_lifetime(cos_dist):
    n = len(cos_dist)
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    edges = sorted([(cos_dist[i,j], i, j) for i in range(n) for j in range(i+1, n)])
    total = 0.0
    for d, i, j in edges:
        ri, rj = find(i), find(j)
        if ri != rj:
            total += d
            parent[ri] = rj
    return total


def class_cosine_dist(reps, labels, n_cls=10):
    means = []
    for c in range(n_cls):
        mask = labels == c
        if mask.sum() > 0:
            m = reps[mask].mean(0)
            n = np.linalg.norm(m)
            means.append(m / max(n, 1e-8))
        else:
            means.append(np.zeros(reps.shape[1]))
    means = np.array(means)
    cos_dist = np.clip(1 - means @ means.T, 0, 2)
    np.fill_diagonal(cos_dist, 0)
    return cos_dist


def run_dataset(dataset_name):
    print(f"\n{'='*70}")
    print(f"  H-CX-446b: Spectral-PH Bridge — {dataset_name.upper()}")
    print(f"{'='*70}")

    torch.manual_seed(42)
    tr, te, dim, names = load_dataset(dataset_name)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()

    epochs = 15
    records = []

    for ep in range(epochs + 1):
        if ep > 0:
            model.train()
            for x, y in tr:
                opt.zero_grad()
                out, t = model(x.view(-1, dim))
                loss = ce(out, y); loss.backward(); opt.step()

        # Metrics
        layer_gaps = spectral_gaps_per_layer(model)
        sg_mean = np.mean(list(layer_gaps.values()))

        model.eval()
        all_reps, all_labels = [], []
        correct, total = 0, 0
        with torch.no_grad():
            for x, y in te:
                rep = model.engine_a(x.view(-1, dim)) - model.engine_g(x.view(-1, dim))
                d = F.normalize(rep, dim=-1)
                all_reps.append(d.numpy())
                all_labels.append(y.numpy())
                out, _ = model(x.view(-1, dim))
                correct += (out.argmax(1) == y).sum().item()
                total += len(y)

        reps = np.concatenate(all_reps)
        labels = np.concatenate(all_labels)
        cos_dist = class_cosine_dist(reps, labels)
        h0 = ph_h0_lifetime(cos_dist)
        acc = correct / total * 100

        records.append({'epoch': ep, 'sg_mean': sg_mean, 'h0': h0, 'acc': acc, 'layer_gaps': layer_gaps})

        if ep % 5 == 0 or ep == epochs:
            print(f"  Ep {ep:2d}: acc={acc:.1f}%  SG={sg_mean:.4f}  H0={h0:.4f}")

    # Correlations
    sgs = [r['sg_mean'] for r in records]
    h0s = [r['h0'] for r in records]

    pr, pp = pearsonr(sgs, h0s)
    sr, sp = spearmanr(sgs, h0s)

    print(f"\n  SG <-> H0: Pearson r={pr:.4f} (p={pp:.2e}), Spearman r={sr:.4f} (p={sp:.2e})")

    # Per-layer analysis
    print(f"\n  Per-layer Spectral Gap <-> PH H0 correlation:")
    layer_names = list(records[0]['layer_gaps'].keys())
    for lname in layer_names:
        layer_sgs = [r['layer_gaps'][lname] for r in records]
        lr, lp = pearsonr(layer_sgs, h0s)
        strength = "STRONG" if abs(lr) > 0.8 else "WEAK" if abs(lr) > 0.5 else "NONE"
        print(f"    {lname:<30} Pearson={lr:.4f} [{strength}]")

    return {'dataset': dataset_name, 'pearson': pr, 'spearman': sr,
            'p_pearson': pp, 'p_spearman': sp, 'records': records}


def main():
    print("=" * 70)
    print("  H-CX-446b: Cross-Dataset Spectral-PH Bridge Verification")
    print("=" * 70)

    results = {}
    for ds in ['mnist', 'fashion', 'cifar']:
        results[ds] = run_dataset(ds)

    # Summary
    print(f"\n{'='*70}")
    print(f"  CROSS-DATASET SUMMARY")
    print(f"{'='*70}")
    print(f"\n  {'Dataset':<10} {'Pearson r':>10} {'p-value':>10} {'Spearman r':>11} {'p-value':>10}")
    print(f"  {'-'*51}")
    for ds in ['mnist', 'fashion', 'cifar']:
        r = results[ds]
        print(f"  {ds:<10} {r['pearson']:>10.4f} {r['p_pearson']:>10.2e} {r['spearman']:>11.4f} {r['p_spearman']:>10.2e}")

    # Universal?
    all_strong = all(abs(results[ds]['pearson']) > 0.7 for ds in results)
    print(f"\n  Universal bridge (all Pearson > 0.7): {'YES' if all_strong else 'NO'}")

if __name__ == '__main__':
    main()
