#!/usr/bin/env python3
"""GZ Prediction Experiments — Lightweight PyTorch
Pre-registered predictions. Honest recording.

P1: MoE N=16, optimal k/N ≈ 1/e → k ≈ 6
P2: Dropout optimal ≈ 0.37 (1/e)
P3: Lottery Ticket winning density ≈ 37%
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset
import numpy as np
import copy, time, sys
sys.path.insert(0, "/Users/ghost/Dev/TECS-L")

torch.manual_seed(42)
torch.set_num_threads(4)
GZ = 1/np.e
B = "=" * 70

def P(m=""): print(m, flush=True)

# Data
tfm = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,),(0.3081,))])
train_ds = datasets.MNIST('data', train=True, download=True, transform=tfm)
test_ds = datasets.MNIST('data', train=False, transform=tfm)
train_ld = DataLoader(train_ds, batch_size=256, shuffle=True, num_workers=0)
test_ld = DataLoader(test_ds, batch_size=512, num_workers=0)

def evaluate(model):
    model.eval()
    c = t = 0
    with torch.no_grad():
        for x, y in test_ld:
            c += (model(x.view(x.size(0),-1)).argmax(1)==y).sum().item()
            t += y.size(0)
    return c/t

def train_model(model, epochs=5, lr=0.001):
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()
    for _ in range(epochs):
        model.train()
        for x, y in train_ld:
            x = x.view(x.size(0), -1)
            opt.zero_grad()
            loss_fn(model(x), y).backward()
            opt.step()

# ═══════════════════════════════════════════
# EXPERIMENT 1: MoE Top-K (N=16)
# PREDICTION: optimal k/N ≈ 1/e → k=6 (±1)
# ═══════════════════════════════════════════
P(B)
P("EXP 1: MoE Top-K Sweep (N=16)")
P(f"PREDICTION: optimal k = round(16/e) = {round(16/np.e)} (±1), k/N ≈ {GZ:.4f}")
P(B)

class SimpleMoE(nn.Module):
    def __init__(self, n_exp, k):
        super().__init__()
        self.k = k
        self.gate = nn.Linear(784, n_exp)
        self.experts = nn.ModuleList([
            nn.Sequential(nn.Linear(784,64), nn.ReLU(), nn.Linear(64,10))
            for _ in range(n_exp)
        ])
    def forward(self, x):
        g = self.gate(x)
        topk_v, topk_i = torch.topk(g, self.k, dim=-1)
        w = F.softmax(topk_v, dim=-1)
        out = torch.zeros(x.size(0), 10)
        for j in range(self.k):
            idx = topk_i[:, j]
            wt = w[:, j].unsqueeze(-1)
            for e_id in range(len(self.experts)):
                mask = (idx == e_id)
                if mask.any():
                    out[mask] += wt[mask] * self.experts[e_id](x[mask])
        return out

N = 16
ks = [1, 2, 3, 4, 5, 6, 7, 8]
moe_results = []
for k in ks:
    t0 = time.time()
    torch.manual_seed(42)
    model = SimpleMoE(N, k)
    train_model(model, epochs=3)
    acc = evaluate(model)
    dt = time.time() - t0
    ratio = k/N
    moe_results.append((k, ratio, acc, dt))
    P(f"  k={k:2d}  k/N={ratio:.4f}  acc={acc:.4f}  ({dt:.0f}s)")

best = max(moe_results, key=lambda r: r[2])
P(f"\n  BEST: k={best[0]}, k/N={best[1]:.4f}, acc={best[2]:.4f}")
P(f"  PREDICTED: k=6, k/N={6/16:.4f}")
P(f"  |best_k/N - 1/e| = {abs(best[1]-GZ):.4f}")
predicted_ok = abs(best[0] - 6) <= 1
P(f"  VERDICT: {'CONFIRMED' if predicted_ok else 'REFUTED'} (predicted k=6±1, got k={best[0]})")

# ═══════════════════════════════════════════
# EXPERIMENT 2: Dropout Sweep
# PREDICTION: optimal ≈ 0.37 [0.30, 0.45]
# ═══════════════════════════════════════════
P(f"\n{B}")
P("EXP 2: Dropout Sweep on MNIST")
P(f"PREDICTION: optimal dropout ≈ {GZ:.4f}, in [0.30, 0.45]")
P(B)

class MLPDrop(nn.Module):
    def __init__(self, dr):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(784,512), nn.ReLU(), nn.Dropout(dr),
            nn.Linear(512,256), nn.ReLU(), nn.Dropout(dr),
            nn.Linear(256,10)
        )
    def forward(self, x): return self.net(x)

drops = [0.0, 0.1, 0.2, 0.3, 0.35, 0.37, 0.4, 0.45, 0.5]
drop_results = []
for dr in drops:
    accs = []
    for seed in [42, 123, 999]:
        torch.manual_seed(seed)
        m = MLPDrop(dr)
        train_model(m, epochs=5)
        accs.append(evaluate(m))
    avg = np.mean(accs)
    drop_results.append((dr, avg, np.std(accs)))
    P(f"  drop={dr:.2f}  acc={avg:.4f} ±{np.std(accs):.4f}")

best_d = max(drop_results, key=lambda r: r[1])
P(f"\n  BEST: drop={best_d[0]:.2f}, acc={best_d[1]:.4f}")
P(f"  PREDICTED: drop≈0.37")
P(f"  |best - 1/e| = {abs(best_d[0]-GZ):.4f}")
in_range = 0.30 <= best_d[0] <= 0.45
P(f"  VERDICT: {'CONFIRMED' if in_range else 'REFUTED'} (predicted [0.30,0.45], got {best_d[0]:.2f})")

# ═══════════════════════════════════════════
# EXPERIMENT 3: Lottery Ticket
# PREDICTION: winning density ≈ 37% (1/e)
# ═══════════════════════════════════════════
P(f"\n{B}")
P("EXP 3: Lottery Ticket Pruning")
P(f"PREDICTION: winning ticket density ≈ {GZ:.4f} ({GZ*100:.1f}%)")
P(B)

class LTModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(784, 300)
        self.fc2 = nn.Linear(300, 100)
        self.fc3 = nn.Linear(100, 10)
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)

# Initial training
torch.manual_seed(42)
init_model = LTModel()
init_state = copy.deepcopy(init_model.state_dict())
train_model(init_model, epochs=5)
base_acc = evaluate(init_model)
P(f"  Baseline accuracy: {base_acc:.4f}")

# Iterative magnitude pruning
masks = {}
for name, p in init_model.named_parameters():
    if 'weight' in name:
        masks[name] = torch.ones_like(p)

densities = []
density = 1.0
prune_rate = 0.20

for round_i in range(12):
    # Prune: remove 20% of remaining weights (smallest magnitude)
    if round_i > 0:
        for name, p in init_model.named_parameters():
            if name in masks:
                alive = masks[name].bool()
                alive_weights = p.data[alive].abs()
                if alive_weights.numel() > 0:
                    threshold = torch.quantile(alive_weights, prune_rate)
                    new_mask = (p.data.abs() > threshold) | ~alive
                    masks[name] = new_mask.float() * masks[name]
        density = sum(m.sum().item() for m in masks.values()) / sum(m.numel() for m in masks.values())

    # Reset to init weights + apply mask
    model = LTModel()
    model.load_state_dict(init_state)
    with torch.no_grad():
        for name, p in model.named_parameters():
            if name in masks:
                p.data *= masks[name]

    # Train with mask
    opt = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_fn = nn.CrossEntropyLoss()
    for _ in range(5):
        model.train()
        for x, y in train_ld:
            x = x.view(x.size(0), -1)
            opt.zero_grad()
            loss = loss_fn(model(x), y)
            loss.backward()
            with torch.no_grad():
                for name, p in model.named_parameters():
                    if name in masks:
                        p.grad *= masks[name]
            opt.step()
            with torch.no_grad():
                for name, p in model.named_parameters():
                    if name in masks:
                        p.data *= masks[name]

    acc = evaluate(model)
    densities.append((density, acc))
    marker = " <-- 1/e" if abs(density - GZ) < 0.05 else ""
    P(f"  density={density:.3f}  acc={acc:.4f}  Δ={acc-base_acc:+.4f}{marker}")

    # Update model for next round's pruning
    init_model = model

# Find winning ticket threshold (acc drops below base - 0.02)
threshold_density = None
for d, a in densities:
    if a >= base_acc - 0.02:
        threshold_density = d

P(f"\n  Baseline: {base_acc:.4f}")
P(f"  Threshold density (acc >= base-2%): {threshold_density:.3f}" if threshold_density else "  No threshold found")
P(f"  PREDICTED: ~0.37")
if threshold_density:
    P(f"  |threshold - 1/e| = {abs(threshold_density-GZ):.4f}")
    confirmed = abs(threshold_density - GZ) < 0.10
    P(f"  VERDICT: {'CONFIRMED' if confirmed else 'REFUTED'}")
else:
    P("  VERDICT: INCONCLUSIVE")

# ═══════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════
P(f"\n{B}")
P("FINAL SUMMARY")
P(B)
P(f"  {'Experiment':>20} | {'Predicted':>10} | {'Observed':>10} | {'Verdict':>12}")
P(f"  {'-'*20}-+-{'-'*10}-+-{'-'*10}-+-{'-'*12}")
P(f"  {'MoE k/N':>20} | {'6/16=0.375':>10} | {f'{best[0]}/{N}={best[1]:.3f}':>10} | {'CONFIRMED' if predicted_ok else 'REFUTED':>12}")
P(f"  {'Dropout':>20} | {'0.37':>10} | {f'{best_d[0]:.2f}':>10} | {'CONFIRMED' if in_range else 'REFUTED':>12}")
td_str = f"{threshold_density:.3f}" if threshold_density else "N/A"
lt_verdict = 'CONFIRMED' if threshold_density and abs(threshold_density-GZ)<0.10 else 'REFUTED'
P(f"  {'Lottery Ticket':>20} | {'0.37':>10} | {td_str:>10} | {lt_verdict:>12}")
P(f"\nDone.")
