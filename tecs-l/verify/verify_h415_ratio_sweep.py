#!/usr/bin/env python3
"""H-415 Verification: Does Golden Zone ALWAYS improve BitNet info efficiency?
Sweep active_ratio from 0.3 to 0.9 to find if efficiency peaks in Golden Zone."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import numpy as np
import math

# ── Minimal implementation ──
def ternary_quantize(w):
    alpha = w.abs().mean()
    return torch.sign(w) * (w.abs() > alpha * 0.5).float()

class TW(torch.autograd.Function):
    @staticmethod
    def forward(ctx, w): return ternary_quantize(w)
    @staticmethod
    def backward(ctx, g): return g

class TL(nn.Module):
    def __init__(self, i, o):
        super().__init__()
        self.l = nn.Linear(i, o)
        self.sp = 0; self.bits = math.log2(3)
    def forward(self, x):
        wt = TW.apply(self.l.weight)
        with torch.no_grad():
            self.sp = (wt == 0).float().mean().item()
            ps = [(wt==-1).float().mean().item(), (wt==0).float().mean().item(), (wt==1).float().mean().item()]
            ps = [p for p in ps if p > 0]
            self.bits = -sum(p * math.log2(p) for p in ps) if ps else math.log2(3)
        return F.linear(x, wt, self.l.bias)

class BG(nn.Module):
    def __init__(self, d, n, T=np.e, ar=0.7):
        super().__init__()
        self.g = nn.Linear(d, n); self.T = T; self.na = max(1, int(n*ar))
    def forward(self, x):
        p = F.softmax(self.g(x)/self.T, -1)
        _, idx = p.topk(self.na, -1)
        m = torch.zeros_like(p).scatter_(-1, idx, 1.0)
        w = p * m
        return w / (w.sum(-1, keepdim=True)+1e-8)

class TE(nn.Module):
    def __init__(self, d, h, o):
        super().__init__()
        self.f1 = TL(d,h); self.f2 = TL(h,o); self.dr = nn.Dropout(0.5)
    def forward(self, x): return self.f2(self.dr(F.relu(self.f1(x))))
    def get_bits(self): return np.mean([self.f1.bits, self.f2.bits])

class BitMoE(nn.Module):
    def __init__(self, d, h, o, n=8, ar=0.7):
        super().__init__()
        self.experts = nn.ModuleList([TE(d,h,o) for _ in range(n)])
        self.gate = BG(d, n, np.e, ar) if ar < 1.0 else None
        self.n = n; self.ar = ar
    def forward(self, x):
        eo = torch.stack([e(x) for e in self.experts], 1)
        if self.gate is None: return eo.mean(1)
        w = self.gate(x)
        return (w.unsqueeze(-1)*eo).sum(1)
    def get_info(self):
        bits = np.mean([e.get_bits() for e in self.experts])
        I = 1 - (self.ar if self.ar < 1.0 else 1.0)
        flow = (bits / math.log2(3)) * (1 - I)
        return bits, I, flow

def train_eval(model, trl, tel, epochs=10):
    opt = torch.optim.Adam(model.parameters(), 0.001)
    crit = nn.CrossEntropyLoss()
    best = 0
    for _ in range(epochs):
        model.train()
        for X, y in trl:
            opt.zero_grad(); crit(model(X.view(X.size(0),-1)), y).backward(); opt.step()
        model.eval()
        c = t = 0
        with torch.no_grad():
            for X, y in tel:
                c += (model(X.view(X.size(0),-1)).argmax(1)==y).sum().item(); t += y.size(0)
        best = max(best, c/t)
    return best

def main():
    print("=" * 70)
    print("  H-415 Verification: Active Ratio Sweep (BitNet MoE)")
    print("  Does info efficiency peak in Golden Zone?")
    print("=" * 70)

    # Load MNIST + FashionMNIST
    tf = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,),(0.5,))])
    datasets_list = [
        ('MNIST', datasets.MNIST('./data', train=True, download=True, transform=tf), datasets.MNIST('./data', train=False, transform=tf), 784),
        ('Fashion', datasets.FashionMNIST('./data', train=True, download=True, transform=tf), datasets.FashionMNIST('./data', train=False, transform=tf), 784),
    ]

    ratios = [0.25, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]

    for ds_name, tr_ds, te_ds, dim in datasets_list:
        trl = DataLoader(tr_ds, 128, True)
        tel = DataLoader(te_ds, 256)

        print(f"\n{'─'*70}")
        print(f"  [{ds_name}] Active Ratio Sweep")
        print(f"{'─'*70}")
        print(f"  {'Active%':>8} | {'I':>6} | {'Best Acc':>9} | {'Bits':>6} | {'InfoFlow':>9} | {'Eff':>8} | {'Zone':>12}")
        print(f"  {'─'*8}─+{'─'*8}+{'─'*11}+{'─'*8}+{'─'*11}+{'─'*10}+{'─'*14}")

        results = []
        for ar in ratios:
            torch.manual_seed(42); np.random.seed(42)
            model = BitMoE(dim, 64, 10, 8, ar)
            acc = train_eval(model, trl, tel, 10)
            bits, I, flow = model.get_info()

            eff = acc / max(flow, 0.01)
            zone = "Golden Zone" if 0.213 <= I <= 0.500 else ("Below" if I < 0.213 else "Outside")
            if ar >= 1.0:
                zone = "Dense"
                I = 0.0
                flow = bits / math.log2(3)
                eff = acc / max(flow, 0.01)

            results.append((ar, I, acc, bits, flow, eff, zone))
            marker = " <<<" if zone == "Golden Zone" else ""
            print(f"  {ar*100:>7.0f}% | {I:>6.3f} | {acc*100:>8.2f}% | {bits:>6.4f} | {flow:>9.4f} | {eff:>8.2f} | {zone:>12}{marker}")

        # Find peak efficiency
        peak = max(results, key=lambda x: x[5])
        print(f"\n  Peak efficiency: active={peak[0]*100:.0f}%, I={peak[1]:.3f}, eff={peak[5]:.2f}")
        print(f"  Peak in Golden Zone? {'YES' if 0.213 <= peak[1] <= 0.500 else 'NO'}")

        # ASCII graph
        print(f"\n  Info Efficiency vs Active Ratio ({ds_name}):")
        max_eff = max(r[5] for r in results)
        min_eff = min(r[5] for r in results)
        eff_range = max_eff - min_eff if max_eff > min_eff else 1

        for r in results:
            bar_len = int((r[5] - min_eff) / eff_range * 40)
            gz = "*" if 0.213 <= r[1] <= 0.500 else " "
            print(f"    {r[0]*100:>3.0f}%{gz}|{'#' * bar_len:40} {r[5]:.2f}")
        print(f"         {'|':>1}{'─'*40}")
        print(f"         Golden Zone: 50-79% active (I=0.21-0.50)")

    print(f"\n{'='*70}")
    print(f"  Sweep complete")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
