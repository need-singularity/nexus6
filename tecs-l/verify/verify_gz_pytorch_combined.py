#!/usr/bin/env python3
"""GZ Offensive: Combined PyTorch Verification (MoE + Dropout + IB)
Lightweight MNIST tests for Golden Zone constants.
"""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import numpy as np
import torch
torch.set_num_threads(1)
import torch.nn as nn
import torch.nn.functional as F
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset
import sys
import time

sys.path.insert(0, "/Users/ghost/Dev/TECS-L")

torch.manual_seed(42)
np.random.seed(42)

GZ_CENTER = 1 / np.e       # 0.3679
GZ_UPPER = 0.5
GZ_LOWER = 0.5 - np.log(4/3)  # 0.2123

print("=" * 60)
print("GZ Offensive: Combined PyTorch Verification")
print(f"Golden Zone: [{GZ_LOWER:.4f}, {GZ_UPPER:.4f}], center=1/e={GZ_CENTER:.4f}")
print("=" * 60)

# ── Data ──────────────────────────────────────────────────────
transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
train_full = datasets.MNIST("/tmp/mnist", train=True, download=True, transform=transform)
test_full = datasets.MNIST("/tmp/mnist", train=False, download=True, transform=transform)

train_set = Subset(train_full, range(5000))
test_set = Subset(test_full, range(1000))

train_loader = DataLoader(train_set, batch_size=256, shuffle=True, num_workers=0)
test_loader = DataLoader(test_set, batch_size=256, shuffle=False, num_workers=0)

device = torch.device("cpu")


def evaluate(model, loader):
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            out = model(x.view(x.size(0), -1))
            pred = out.argmax(dim=1)
            correct += (pred == y).sum().item()
            total += y.size(0)
    return correct / total


# ══════════════════════════════════════════════════════════════
# Part 1: MoE k/N Sweep
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PART 1: MoE k/N Sweep (3 epochs)")
print("=" * 60)


class MoEModel(nn.Module):
    def __init__(self, n_experts, k):
        super().__init__()
        self.n_experts = n_experts
        self.k = k
        self.gate = nn.Linear(784, n_experts)
        self.experts = nn.ModuleList([
            nn.Sequential(nn.Linear(784, 64), nn.ReLU(), nn.Linear(64, 10))
            for _ in range(n_experts)
        ])

    def forward(self, x):
        gate_logits = self.gate(x)
        topk_vals, topk_idx = torch.topk(gate_logits, self.k, dim=1)
        topk_weights = F.softmax(topk_vals, dim=1)

        batch_size = x.size(0)
        output = torch.zeros(batch_size, 10, device=x.device)

        for i in range(self.k):
            expert_idx = topk_idx[:, i]
            weight = topk_weights[:, i].unsqueeze(1)
            for e in range(self.n_experts):
                mask = (expert_idx == e)
                if mask.any():
                    expert_out = self.experts[e](x[mask])
                    output[mask] += weight[mask] * expert_out
        return output


moe_results = []
expert_counts = [8, 16, 32]

for N in expert_counts:
    k_values = sorted(set([1, 2, round(N * 0.25), round(N * 0.33),
                           round(N * 0.37), round(N * 0.5)]))
    best_acc = 0
    best_k = 0
    row_results = []

    for k in k_values:
        torch.manual_seed(42)
        model = MoEModel(N, k).to(device)
        opt = torch.optim.Adam(model.parameters(), lr=1e-3)

        model.train()
        for epoch in range(3):
            for x, y in train_loader:
                x, y = x.to(device), y.to(device)
                x = x.view(x.size(0), -1)
                opt.zero_grad()
                out = model(x)
                loss = F.cross_entropy(out, y)
                loss.backward()
                opt.step()

        acc = evaluate(model, test_loader)
        ratio = k / N
        row_results.append((k, ratio, acc))
        if acc > best_acc:
            best_acc = acc
            best_k = k

    best_ratio = best_k / N
    moe_results.append((N, best_k, best_ratio, best_acc, row_results))

print(f"\n{'N':>4} | {'k':>3} | {'k/N':>6} | {'Acc':>7}")
print("-" * 35)
for N, best_k, best_ratio, best_acc, rows in moe_results:
    for k, ratio, acc in rows:
        marker = " <-- best" if k == best_k else ""
        print(f"{N:4d} | {k:3d} | {ratio:.4f} | {acc:.4f}{marker}")
    print("-" * 35)

print("\nMoE Summary:")
for N, best_k, best_ratio, best_acc, _ in moe_results:
    dist = abs(best_ratio - GZ_CENTER)
    in_gz = "IN GZ" if GZ_LOWER <= best_ratio <= GZ_UPPER else "OUTSIDE"
    print(f"  N={N:2d}: best k/N = {best_ratio:.4f} (k={best_k}), "
          f"acc={best_acc:.4f}, dist_to_1/e={dist:.4f} [{in_gz}]")


# ══════════════════════════════════════════════════════════════
# Part 2: Dropout Sweep
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PART 2: Dropout Sweep (5 epochs)")
print("=" * 60)


class DropoutMLP(nn.Module):
    def __init__(self, drop_rate):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(784, 256), nn.ReLU(), nn.Dropout(drop_rate),
            nn.Linear(256, 128), nn.ReLU(), nn.Dropout(drop_rate),
            nn.Linear(128, 10)
        )

    def forward(self, x):
        return self.net(x)


drop_rates = [0.0, 0.1, 0.2, 0.3, 0.35, 0.37, 0.4, 0.5]
dropout_results = []

for dr in drop_rates:
    torch.manual_seed(42)
    model = DropoutMLP(dr).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    model.train()
    for epoch in range(5):
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            x = x.view(x.size(0), -1)
            opt.zero_grad()
            out = model(x)
            loss = F.cross_entropy(out, y)
            loss.backward()
            opt.step()

    acc = evaluate(model, test_loader)
    dropout_results.append((dr, acc))

print(f"\n{'Dropout':>8} | {'Acc':>7} | {'In GZ':>6}")
print("-" * 35)
best_dr, best_acc = max(dropout_results, key=lambda x: x[1])
for dr, acc in dropout_results:
    in_gz = "YES" if GZ_LOWER <= dr <= GZ_UPPER else "no"
    marker = " <-- best" if dr == best_dr else ""
    print(f"{dr:8.2f} | {acc:.4f} | {in_gz:>6}{marker}")

dist = abs(best_dr - GZ_CENTER)
in_gz = "IN GZ" if GZ_LOWER <= best_dr <= GZ_UPPER else "OUTSIDE"
print(f"\nDropout Summary:")
print(f"  Best dropout = {best_dr:.4f}, acc={best_acc:.4f}, "
      f"dist_to_1/e={dist:.4f} [{in_gz}]")


# ══════════════════════════════════════════════════════════════
# Part 3: Information Bottleneck Curve
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PART 3: Information Bottleneck (20 epochs)")
print("=" * 60)


class IBNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(784, 128), nn.ReLU())
        self.bottleneck = nn.Linear(128, 16)
        self.decoder = nn.Linear(16, 10)

    def forward(self, x):
        h = self.encoder(x)
        t = self.bottleneck(h)
        return self.decoder(F.relu(t)), t


def estimate_mi_xt(activations, n_bins=30):
    """Estimate H(T) as proxy for MI(X;T) via binning."""
    acts = activations.numpy()
    # Bin each dimension independently, estimate joint entropy
    n_samples, n_dims = acts.shape
    total_h = 0.0
    for d in range(n_dims):
        col = acts[:, d]
        mn, mx = col.min(), col.max()
        if mx - mn < 1e-8:
            continue
        bins = np.linspace(mn, mx, n_bins + 1)
        counts, _ = np.histogram(col, bins=bins)
        probs = counts / counts.sum()
        probs = probs[probs > 0]
        total_h += -np.sum(probs * np.log(probs + 1e-12))
    return total_h


def estimate_mi_ty(activations, labels, n_bins=30):
    """Estimate MI(T;Y) via binned activations and labels."""
    acts = activations.numpy()
    labels_np = labels.numpy()
    n_samples, n_dims = acts.shape

    # Discretize activations: use first 3 dims for tractability
    use_dims = min(3, n_dims)
    codes = np.zeros(n_samples, dtype=np.int64)
    for d in range(use_dims):
        col = acts[:, d]
        mn, mx = col.min(), col.max()
        if mx - mn < 1e-8:
            digitized = np.zeros(n_samples, dtype=np.int64)
        else:
            digitized = np.clip(
                ((col - mn) / (mx - mn) * n_bins).astype(np.int64),
                0, n_bins - 1
            )
        codes = codes * n_bins + digitized

    # H(T)
    unique_codes, code_counts = np.unique(codes, return_counts=True)
    p_t = code_counts / code_counts.sum()
    h_t = -np.sum(p_t * np.log(p_t + 1e-12))

    # H(T|Y)
    h_t_given_y = 0.0
    for c in range(10):
        mask = labels_np == c
        if mask.sum() == 0:
            continue
        p_c = mask.sum() / n_samples
        sub_codes = codes[mask]
        unique_sub, sub_counts = np.unique(sub_codes, return_counts=True)
        p_t_y = sub_counts / sub_counts.sum()
        h_t_given_y += p_c * (-np.sum(p_t_y * np.log(p_t_y + 1e-12)))

    return h_t - h_t_given_y


torch.manual_seed(42)
ib_model = IBNet().to(device)
ib_opt = torch.optim.Adam(ib_model.parameters(), lr=1e-3)

ib_epochs = 20
mi_xt_list = []
mi_ty_list = []

for epoch in range(ib_epochs):
    ib_model.train()
    for x, y in train_loader:
        x, y = x.to(device), y.to(device)
        x = x.view(x.size(0), -1)
        ib_opt.zero_grad()
        out, _ = ib_model(x)
        loss = F.cross_entropy(out, y)
        loss.backward()
        ib_opt.step()

    # Collect bottleneck activations on train set
    ib_model.eval()
    all_t = []
    all_y = []
    with torch.no_grad():
        for x, y in train_loader:
            x = x.to(device).view(x.size(0), -1)
            _, t = ib_model(x)
            all_t.append(t.cpu())
            all_y.append(y)
    all_t = torch.cat(all_t)
    all_y = torch.cat(all_y)

    mi_xt = estimate_mi_xt(all_t)
    mi_ty = estimate_mi_ty(all_t, all_y)
    mi_xt_list.append(mi_xt)
    mi_ty_list.append(mi_ty)

# Detect compression onset: first epoch where MI(X;T) decreases
compression_epoch = None
for i in range(1, len(mi_xt_list)):
    if mi_xt_list[i] < mi_xt_list[i - 1]:
        compression_epoch = i + 1  # 1-indexed
        break

print(f"\n{'Epoch':>5} | {'MI(X;T)':>8} | {'MI(T;Y)':>8} | {'Acc':>7}")
print("-" * 40)

# Re-evaluate accuracy per epoch (we only have final model; show MI trajectory)
for i in range(ib_epochs):
    print(f"{i+1:5d} | {mi_xt_list[i]:8.4f} | {mi_ty_list[i]:8.4f}")

if compression_epoch is not None:
    onset_ratio = compression_epoch / ib_epochs
    dist = abs(onset_ratio - GZ_CENTER)
    in_gz = "IN GZ" if GZ_LOWER <= onset_ratio <= GZ_UPPER else "OUTSIDE"
    print(f"\nIB Summary:")
    print(f"  Compression onset at epoch {compression_epoch}/{ib_epochs}")
    print(f"  Onset ratio = {onset_ratio:.4f}, dist_to_1/e={dist:.4f} [{in_gz}]")
else:
    # Check if monotonically increasing — no compression phase observed
    # Try detecting largest drop instead
    diffs = [mi_xt_list[i] - mi_xt_list[i-1] for i in range(1, len(mi_xt_list))]
    min_diff_idx = int(np.argmin(diffs))
    onset_ratio = (min_diff_idx + 2) / ib_epochs  # 1-indexed
    dist = abs(onset_ratio - GZ_CENTER)
    in_gz = "IN GZ" if GZ_LOWER <= onset_ratio <= GZ_UPPER else "OUTSIDE"
    print(f"\nIB Summary (no strict compression; using min-growth epoch):")
    print(f"  Min growth at epoch {min_diff_idx+2}/{ib_epochs}")
    print(f"  Ratio = {onset_ratio:.4f}, dist_to_1/e={dist:.4f} [{in_gz}]")
    compression_epoch = min_diff_idx + 2


# ══════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("FINAL SUMMARY")
print("=" * 60)

results = []
for N, best_k, best_ratio, best_acc, _ in moe_results:
    results.append(("MoE k/N (N={})".format(N), best_ratio, abs(best_ratio - GZ_CENTER),
                    GZ_LOWER <= best_ratio <= GZ_UPPER))

results.append(("Dropout", best_dr, abs(best_dr - GZ_CENTER),
                GZ_LOWER <= best_dr <= GZ_UPPER))

ib_ratio = compression_epoch / ib_epochs if compression_epoch else None
if ib_ratio is not None:
    results.append(("IB onset ratio", ib_ratio, abs(ib_ratio - GZ_CENTER),
                    GZ_LOWER <= ib_ratio <= GZ_UPPER))

print(f"\n{'Test':>20} | {'Value':>7} | {'|v-1/e|':>7} | {'In GZ':>5}")
print("-" * 50)
in_gz_count = 0
for name, val, dist, in_gz in results:
    flag = "YES" if in_gz else "no"
    if in_gz:
        in_gz_count += 1
    print(f"{name:>20} | {val:.4f} | {dist:.4f} | {flag:>5}")

total = len(results)
print(f"\n  Golden Zone hits: {in_gz_count}/{total}")
print(f"  1/e = {GZ_CENTER:.4f}, GZ = [{GZ_LOWER:.4f}, {GZ_UPPER:.4f}]")

if in_gz_count >= total * 0.6:
    print("  Assessment: STRONG support for GZ hypothesis")
elif in_gz_count >= total * 0.4:
    print("  Assessment: MODERATE support for GZ hypothesis")
else:
    print("  Assessment: WEAK support for GZ hypothesis")

print("\nDone.")
