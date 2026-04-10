#!/usr/bin/env python3
"""H-413 Multi-seed verification: Is synergy statistically significant?
Runs 5 seeds x 3 datasets x 5 configs = 75 experiments."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import numpy as np
import math
import time

# ── Minimal BitNet+Golden MoE implementation ──
def ternary_quantize(w):
    alpha = w.abs().mean()
    return torch.sign(w) * (w.abs() > alpha * 0.5).float()

class TernaryWeight(torch.autograd.Function):
    @staticmethod
    def forward(ctx, w): return ternary_quantize(w)
    @staticmethod
    def backward(ctx, g): return g

class TernaryLinear(nn.Module):
    def __init__(self, inf, outf):
        super().__init__()
        self.linear = nn.Linear(inf, outf)
    def forward(self, x):
        return F.linear(x, TernaryWeight.apply(self.linear.weight), self.linear.bias)

class TopKGate(nn.Module):
    def __init__(self, d, n, k=2):
        super().__init__()
        self.gate = nn.Linear(d, n); self.k = k
    def forward(self, x):
        s = self.gate(x)
        _, idx = s.topk(self.k, dim=-1)
        m = torch.zeros_like(s).scatter_(-1, idx, 1.0)
        w = F.softmax(s, dim=-1) * m
        return w / (w.sum(-1, keepdim=True) + 1e-8)

class BoltzmannGate(nn.Module):
    def __init__(self, d, n, T=np.e, ar=0.7):
        super().__init__()
        self.gate = nn.Linear(d, n); self.T = T
        self.na = max(1, int(n * ar))
    def forward(self, x):
        p = F.softmax(self.gate(x) / self.T, dim=-1)
        _, idx = p.topk(self.na, dim=-1)
        m = torch.zeros_like(p).scatter_(-1, idx, 1.0)
        w = p * m
        return w / (w.sum(-1, keepdim=True) + 1e-8)

class Expert(nn.Module):
    def __init__(self, d, h, o):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d,h), nn.ReLU(), nn.Dropout(0.5), nn.Linear(h,o))
    def forward(self, x): return self.net(x)

class TernaryExpert(nn.Module):
    def __init__(self, d, h, o):
        super().__init__()
        self.fc1 = TernaryLinear(d,h); self.fc2 = TernaryLinear(h,o)
        self.drop = nn.Dropout(0.5)
    def forward(self, x): return self.fc2(self.drop(F.relu(self.fc1(x))))

class MoE(nn.Module):
    def __init__(self, d, h, o, n=8, gt='boltzmann', ternary=False, **kw):
        super().__init__()
        EC = TernaryExpert if ternary else Expert
        self.experts = nn.ModuleList([EC(d,h,o) for _ in range(n)])
        self.n = n
        if gt == 'topk': self.gate = TopKGate(d, n, kw.get('k',2))
        elif gt == 'boltzmann': self.gate = BoltzmannGate(d, n, kw.get('temperature', np.e), kw.get('active_ratio', 0.7))
        else: self.gate = None
    def forward(self, x):
        eo = torch.stack([e(x) for e in self.experts], dim=1)
        if self.gate is None: return eo.mean(dim=1)
        w = self.gate(x)
        return (w.unsqueeze(-1) * eo).sum(dim=1)

def train_eval(model, trl, tel, epochs):
    opt = torch.optim.Adam(model.parameters(), lr=0.001)
    crit = nn.CrossEntropyLoss()
    best = 0
    for ep in range(epochs):
        model.train()
        for X, y in trl:
            opt.zero_grad(); crit(model(X.view(X.size(0),-1)), y).backward(); opt.step()
        model.eval()
        c = t = 0
        with torch.no_grad():
            for X, y in tel:
                c += (model(X.view(X.size(0),-1)).argmax(1) == y).sum().item()
                t += y.size(0)
        best = max(best, c/t)
    return best

def load_ds(name):
    tf = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,),(0.5,))])
    if name == 'mnist':
        tr = datasets.MNIST('./data', True, download=True, transform=tf)
        te = datasets.MNIST('./data', False, transform=tf)
        return DataLoader(tr,128,True), DataLoader(te,256), 784, 'MNIST'
    elif name == 'fashion':
        tr = datasets.FashionMNIST('./data', True, download=True, transform=tf)
        te = datasets.FashionMNIST('./data', False, transform=tf)
        return DataLoader(tr,128,True), DataLoader(te,256), 784, 'FashionMNIST'
    elif name == 'cifar':
        tf1 = transforms.Compose([transforms.RandomHorizontalFlip(), transforms.RandomCrop(32,4),
               transforms.ToTensor(), transforms.Normalize((0.4914,0.4822,0.4465),(0.247,0.243,0.261))])
        tf2 = transforms.Compose([transforms.ToTensor(),
               transforms.Normalize((0.4914,0.4822,0.4465),(0.247,0.243,0.261))])
        tr = datasets.CIFAR10('./data', True, download=True, transform=tf1)
        te = datasets.CIFAR10('./data', False, transform=tf2)
        return DataLoader(tr,128,True), DataLoader(te,256), 3072, 'CIFAR-10'

def main():
    seeds = [1, 2, 3, 4, 5]
    ds_names = ['mnist', 'fashion', 'cifar']
    configs = [
        ('Dense',       'dense',     {}, False),
        ('TopK',        'topk',      {'k':2}, False),
        ('Golden',      'boltzmann', {'temperature':np.e,'active_ratio':0.7}, False),
        ('BitNet-D',    'dense',     {}, True),
        ('BitNet+G',    'boltzmann', {'temperature':np.e,'active_ratio':0.7}, True),
    ]

    print("=" * 70)
    print("  H-413 Multi-Seed Verification (5 seeds x 3 datasets x 5 configs)")
    print("=" * 70)

    all_data = {}  # {ds: {config: [acc_per_seed]}}

    for ds in ds_names:
        trl, tel, dim, label = load_ds(ds)
        h = 64 if dim == 784 else 128
        ep = 10 if dim == 784 else 15
        all_data[ds] = {}

        print(f"\n{'─'*70}")
        print(f"  [{label}] dim={dim}, epochs={ep}")
        print(f"{'─'*70}")

        for cname, gt, kw, tern in configs:
            accs = []
            for seed in seeds:
                torch.manual_seed(seed); np.random.seed(seed)
                model = MoE(dim, h, 10, 8, gt, tern, **kw)
                acc = train_eval(model, trl, tel, ep)
                accs.append(acc)
                print(f"    {cname:10} seed={seed}: {acc*100:.2f}%")
            all_data[ds][cname] = accs
            print(f"    {cname:10} mean={np.mean(accs)*100:.2f}% +/- {np.std(accs)*100:.2f}%")

    # ── SYNERGY ANALYSIS ──
    print(f"\n\n{'='*70}")
    print(f"  SYNERGY STATISTICAL ANALYSIS")
    print(f"{'='*70}")

    for ds in ds_names:
        label = {'mnist':'MNIST','fashion':'FashionMNIST','cifar':'CIFAR-10'}[ds]
        d = all_data[ds]
        synergies = []
        recoveries = []
        for i in range(len(seeds)):
            base = d['Dense'][i]
            g_gain = d['Golden'][i] - base
            b_gain = d['BitNet-D'][i] - base
            dual_gain = d['BitNet+G'][i] - base
            syn = dual_gain - (g_gain + b_gain)
            synergies.append(syn)
            b_loss = base - d['BitNet-D'][i]
            d_loss = base - d['BitNet+G'][i]
            rec = (b_loss - d_loss) / b_loss if b_loss > 0.001 else 0
            recoveries.append(rec)

        syn_mean = np.mean(synergies)
        syn_std = np.std(synergies)
        syn_se = syn_std / np.sqrt(len(synergies))
        # t-test: is synergy significantly > 0?
        t_stat = syn_mean / syn_se if syn_se > 0 else 0
        # p-value approximation (one-sided, df=4)
        # Using t-distribution critical values: t(4,0.05)=2.132, t(4,0.01)=3.747
        if abs(t_stat) > 3.747: sig = "p<0.01 ***"
        elif abs(t_stat) > 2.132: sig = "p<0.05 *"
        elif abs(t_stat) > 1.533: sig = "p<0.10 ."
        else: sig = "n.s."

        rec_mean = np.mean(recoveries)
        rec_std = np.std(recoveries)

        print(f"\n  [{label}]")
        print(f"    Synergy per seed: {['%+.2f%%' % (s*100) for s in synergies]}")
        print(f"    Mean synergy:     {syn_mean*100:+.3f}% +/- {syn_std*100:.3f}%")
        print(f"    t-statistic:      {t_stat:.3f}  ({sig})")
        print(f"    95% CI:           [{(syn_mean-2.776*syn_se)*100:+.3f}%, {(syn_mean+2.776*syn_se)*100:+.3f}%]")
        print(f"    Recovery rate:    {rec_mean*100:.1f}% +/- {rec_std*100:.1f}%")

        # All seeds positive?
        all_pos = all(s > 0 for s in synergies)
        print(f"    All seeds positive: {'YES' if all_pos else 'NO'}")

    # ── CROSS-DATASET SUMMARY ──
    print(f"\n{'='*70}")
    print(f"  SUMMARY TABLE")
    print(f"{'='*70}")
    print(f"  {'Dataset':15} | {'Mean Acc Dense':>14} | {'Mean Acc B+G':>12} | {'Synergy':>10} | {'Sig':>10} | {'Recovery':>10}")
    print(f"  {'─'*15}─+{'─'*16}+{'─'*14}+{'─'*12}+{'─'*12}+{'─'*12}")
    for ds in ds_names:
        label = {'mnist':'MNIST','fashion':'FashionMNIST','cifar':'CIFAR-10'}[ds]
        d = all_data[ds]
        dense_m = np.mean(d['Dense'])
        bg_m = np.mean(d['BitNet+G'])
        syns = []
        recs = []
        for i in range(len(seeds)):
            base = d['Dense'][i]
            syn = (d['BitNet+G'][i] - base) - ((d['Golden'][i] - base) + (d['BitNet-D'][i] - base))
            syns.append(syn)
            bl = base - d['BitNet-D'][i]
            dl = base - d['BitNet+G'][i]
            recs.append((bl-dl)/bl if bl > 0.001 else 0)
        sm = np.mean(syns); ss = np.std(syns); se = ss/np.sqrt(len(syns))
        t = sm/se if se > 0 else 0
        if abs(t) > 3.747: sig = "p<0.01***"
        elif abs(t) > 2.132: sig = "p<0.05*"
        else: sig = "n.s."
        print(f"  {label:15} | {dense_m*100:>13.2f}% | {bg_m*100:>11.2f}% | {sm*100:>+9.3f}% | {sig:>10} | {np.mean(recs)*100:>9.1f}%")

    print(f"\n{'='*70}")
    print(f"  Experiment complete")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
