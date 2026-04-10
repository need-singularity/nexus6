#!/usr/bin/env python3
"""Are the inversion ratios of dual mechanisms related to golden zone constants?"""
import torch, torch.nn as nn, torch.nn.functional as F, numpy as np, copy, math
from sklearn.datasets import load_breast_cancer, load_iris, load_wine, load_digits
from sklearn.preprocessing import StandardScaler

class SimpleAE(nn.Module):
    def __init__(self, dim, h=64):
        super().__init__()
        self.ea = nn.Sequential(nn.Linear(dim,h), nn.ReLU(), nn.Linear(h,dim))
        self.eg = nn.Sequential(nn.Linear(dim,h), nn.ReLU(), nn.Linear(h,dim))
        self.eq = nn.Linear(dim, dim)
    def forward(self, x):
        a, g = self.ea(x), self.eg(x)
        return self.eq(x) + 0.3*(a-g), a, g

def analyze(name, X, y, normal_label, n_trials=5):
    scaler = StandardScaler(); X = scaler.fit_transform(X)
    Xn, Xa = X[y==normal_label], X[y!=normal_label]
    if len(Xa) > 300: Xa = Xa[:300]
    np.random.seed(42); idx = np.random.permutation(len(Xn))
    nt = max(int(0.7*len(Xn)), 20)
    Xt = torch.FloatTensor(Xn[idx[:nt]])
    Xtn = torch.FloatTensor(Xn[idx[nt:]]); Xta = torch.FloatTensor(Xa)
    dim = X.shape[1]
    
    int_ratios, inter_ratios = [], []
    for t in range(n_trials):
        p = SimpleAE(dim); o = torch.optim.Adam(p.parameters(), lr=0.001)
        for ep in range(50):
            o.zero_grad(); out, _, _ = p(Xt); F.mse_loss(out, Xt).backward(); o.step()
        ca, cb = copy.deepcopy(p), copy.deepcopy(p)
        with torch.no_grad():
            for pp in ca.parameters(): pp.add_(torch.randn_like(pp)*0.01)
            for pp in cb.parameters(): pp.add_(torch.randn_like(pp)*0.01)
        oa, ob = torch.optim.Adam(ca.parameters(), lr=0.001), torch.optim.Adam(cb.parameters(), lr=0.001)
        for ep in range(30):
            pm = torch.randperm(len(Xt)); h = len(pm)//2
            ca.train(); oa.zero_grad(); out_a, _, _ = ca(Xt[pm[:h]]); F.mse_loss(out_a, Xt[pm[:h]]).backward(); oa.step()
            cb.train(); ob.zero_grad(); out_b, _, _ = cb(Xt[pm[h:]]); F.mse_loss(out_b, Xt[pm[h:]]).backward(); ob.step()
        ca.eval(); cb.eval()
        with torch.no_grad():
            on, ea_n, eg_n = ca(Xtn); obn, _, _ = cb(Xtn)
            oa2, ea_a, eg_a = ca(Xta); oba, _, _ = cb(Xta)
            in_n = ((ea_n-eg_n)**2).mean(-1).mean().item()
            in_a = ((ea_a-eg_a)**2).mean(-1).mean().item()
            it_n = ((on-obn)**2).mean(-1).mean().item()
            it_a = ((oa2-oba)**2).mean(-1).mean().item()
        int_ratios.append(in_a/(in_n+1e-10))
        inter_ratios.append(it_a/(it_n+1e-10))
    
    return np.mean(int_ratios), np.std(int_ratios), np.mean(inter_ratios), np.std(inter_ratios)

print("="*60)
print("Dual Mechanism × Golden Zone Constant")
print("="*60)

datasets = [
    ("Cancer", *load_breast_cancer(return_X_y=True), 1),
    ("Iris", *load_iris(return_X_y=True), 0),
    ("Wine", *load_wine(return_X_y=True), 0),
    ("Digits(0v1)", *load_digits(return_X_y=True), 0),
]

print(f"\n  {'Dataset':>15} {'int_ratio':>10} {'±':>1} {'std':>6} {'inter_ratio':>12} {'±':>1} {'std':>6}")
print(f"  {'-'*55}")

all_int, all_inter = [], []
for name, X, y, nl in datasets:
    if name == "Digits(0v1)":
        mask = (y==0)|(y==1); X, y = X[mask], y[mask]
    ir_m, ir_s, jr_m, jr_s = analyze(name, X, y, nl)
    all_int.append(ir_m); all_inter.append(jr_m)
    print(f"  {name:>15} {ir_m:>10.4f} ± {ir_s:>6.4f} {jr_m:>12.4f} ± {jr_s:>6.4f}")

print(f"\n  Golden Zone Constant Comparison:")
print(f"    Mean int_ratio:   {np.mean(all_int):.4f}")
print(f"    1/e:              {1/math.e:.4f}")
print(f"    Error:            {abs(np.mean(all_int)-1/math.e):.4f} ({abs(np.mean(all_int)-1/math.e)/(1/math.e)*100:.1f}%)")
print(f"    1/2-ln(4/3):      {0.5-math.log(4/3):.4f} (Golden zone lower bound)")
print(f"    Mean inter_ratio: {np.mean(all_inter):.4f}")
print(f"    e:                {math.e:.4f}")
print(f"    Error:            {abs(np.mean(all_inter)-math.e):.4f}")
print(f"\nComplete")