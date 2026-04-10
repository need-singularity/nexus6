#!/usr/bin/env python3
"""GZ Prediction: CIFAR-10 MoE k/N ≈ 1/e
PREDICTION: optimal k = round(16/e) = 6 (±1) on CIFAR-10
"""
import torch, torch.nn as nn, torch.nn.functional as F
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import numpy as np, time, sys
sys.path.insert(0, "/Users/ghost/Dev/TECS-L")
torch.manual_seed(42); torch.set_num_threads(4)
GZ = 1/np.e

tfm = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,0.5,0.5),(0.5,0.5,0.5))])
train_ld = DataLoader(datasets.CIFAR10('data',train=True,download=True,transform=tfm), batch_size=256, shuffle=True, num_workers=0)
test_ld = DataLoader(datasets.CIFAR10('data',train=False,transform=tfm), batch_size=512, num_workers=0)

class Expert(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(3072,128), nn.ReLU(), nn.Linear(128,10))
    def forward(self, x): return self.net(x)

class MoE(nn.Module):
    def __init__(self, n, k):
        super().__init__()
        self.k = k
        self.gate = nn.Linear(3072, n)
        self.experts = nn.ModuleList([Expert() for _ in range(n)])
    def forward(self, x):
        g = self.gate(x)
        tv, ti = torch.topk(g, self.k, dim=-1)
        w = F.softmax(tv, dim=-1)
        out = torch.zeros(x.size(0), 10, device=x.device)
        for j in range(self.k):
            idx = ti[:, j]; wt = w[:, j].unsqueeze(-1)
            for e in range(len(self.experts)):
                m = (idx == e)
                if m.any(): out[m] += wt[m] * self.experts[e](x[m])
        return out

print("=" * 70, flush=True)
print("CIFAR-10 MoE k/N Prediction (N=16)", flush=True)
print(f"PREDICTION: optimal k=6 (±1), k/N≈{GZ:.4f}", flush=True)
print("=" * 70, flush=True)

N = 16
results = []
for k in [1,2,3,4,5,6,7,8]:
    t0 = time.time()
    torch.manual_seed(42)
    model = MoE(N, k)
    opt = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_fn = nn.CrossEntropyLoss()
    for _ in range(5):
        model.train()
        for x, y in train_ld:
            x = x.view(x.size(0), -1)
            opt.zero_grad(); loss_fn(model(x), y).backward(); opt.step()
    model.eval(); c = t = 0
    with torch.no_grad():
        for x, y in test_ld:
            c += (model(x.view(x.size(0),-1)).argmax(1)==y).sum().item(); t += y.size(0)
    acc = c/t; dt = time.time()-t0
    results.append((k, k/N, acc))
    print(f"  k={k:2d}  k/N={k/N:.4f}  acc={acc:.4f}  ({dt:.0f}s)", flush=True)

best = max(results, key=lambda r: r[2])
print(f"\n  BEST: k={best[0]}, k/N={best[1]:.4f}, acc={best[2]:.4f}", flush=True)
print(f"  |best_k/N - 1/e| = {abs(best[1]-GZ):.4f}", flush=True)
ok = abs(best[0] - 6) <= 1
print(f"  VERDICT: {'CONFIRMED' if ok else 'REFUTED'} (predicted k=6±1, got k={best[0]})", flush=True)
