#!/usr/bin/env python3
"""H307 Application: Internal(Inverted) + Inter(Normal) Combined Anomaly Score"""
import torch, torch.nn as nn, torch.nn.functional as F, numpy as np, copy
from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

class SimpleAE(nn.Module):
    def __init__(self, dim, h=64):
        super().__init__()
        self.ea = nn.Sequential(nn.Linear(dim,h), nn.ReLU(), nn.Linear(h,dim))
        self.eg = nn.Sequential(nn.Linear(dim,h), nn.ReLU(), nn.Linear(h,dim))
        self.eq = nn.Linear(dim, dim)
    def forward(self, x):
        a, g = self.ea(x), self.eg(x)
        return self.eq(x) + 0.3*(a-g), a, g

data = load_breast_cancer(); X, y = data.data, data.target
scaler = StandardScaler(); X = scaler.fit_transform(X)
X_n, X_a = X[y==1], X[y==0]
np.random.seed(42); idx = np.random.permutation(len(X_n))
X_train = torch.FloatTensor(X_n[idx[:250]])
X_test = torch.FloatTensor(np.vstack([X_n[idx[250:]], X_a]))
y_test = np.array([0]*len(X_n[idx[250:]]) + [1]*len(X_a))

print("="*60)
print("H307 Application: Combined Anomaly Score (Internal Inverted + Inter Normal)")
print("="*60)

all_results = {k: [] for k in ['internal', 'inter', 'recon', 'inv_internal', 'combined', 'combined_v2']}

for trial in range(5):
    parent = SimpleAE(30)
    opt = torch.optim.Adam(parent.parameters(), lr=0.001)
    for ep in range(50):
        opt.zero_grad(); out, _, _ = parent(X_train)
        F.mse_loss(out, X_train).backward(); opt.step()

    ca, cb = copy.deepcopy(parent), copy.deepcopy(parent)
    with torch.no_grad():
        for p in ca.parameters(): p.add_(torch.randn_like(p)*0.01)
        for p in cb.parameters(): p.add_(torch.randn_like(p)*0.01)

    oa, ob = torch.optim.Adam(ca.parameters(), lr=0.001), torch.optim.Adam(cb.parameters(), lr=0.001)
    for ep in range(30):
        perm = torch.randperm(len(X_train)); half = len(perm)//2
        ca.train(); oa.zero_grad(); out_a, _, _ = ca(X_train[perm[:half]]); F.mse_loss(out_a, X_train[perm[:half]]).backward(); oa.step()
        cb.train(); ob.zero_grad(); out_b, _, _ = cb(X_train[perm[half:]]); F.mse_loss(out_b, X_train[perm[half:]]).backward(); ob.step()

    ca.eval(); cb.eval()
    with torch.no_grad():
        out_a, ea_a, eg_a = ca(X_test)
        out_b, ea_b, eg_b = cb(X_test)
        internal = ((ea_a-eg_a)**2).mean(-1).numpy()
        inter = ((out_a-out_b)**2).mean(-1).numpy()
        recon = ((out_a-X_test)**2).mean(-1).numpy()
        inv_internal = -internal  # Inversion!
        combined = inter - internal  # Inter(+) + Internal inverted(-)
        combined_v2 = inter + recon - internal  # Triple combination

    for name, scores in [('internal', internal), ('inter', inter), ('recon', recon),
                          ('inv_internal', inv_internal), ('combined', combined), ('combined_v2', combined_v2)]:
        auroc = roc_auc_score(y_test, scores)
        all_results[name].append(auroc)

print(f"\n  {'Score':>15} {'AUROC mean':>12} {'std':>8}")
print(f"  {'-'*38}")
for name, vals in all_results.items():
    marker = " ← BEST" if np.mean(vals) == max(np.mean(v) for v in all_results.values()) else ""
    print(f"  {name:>15} {np.mean(vals):>12.4f} {np.std(vals):>8.4f}{marker}")

best_name = max(all_results, key=lambda k: np.mean(all_results[k]))
print(f"\n  Best: {best_name} = {np.mean(all_results[best_name]):.4f}")
print(f"\n  Interpretation:")
print(f"    internal (original): Due to inversion, AUROC < 0.5")
print(f"    inv_internal:        Inversion corrected → AUROC > 0.5")
print(f"    combined:            Inter + Inverted internal → Synergy?")
print(f"    combined_v2:         Inter + Reconstruction + Inverted internal → Best?")
print(f"\nComplete")