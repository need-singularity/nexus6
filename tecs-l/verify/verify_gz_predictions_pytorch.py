#!/usr/bin/env python3
"""GZ Prediction Experiments — PROPER PyTorch on Mac
Pre-registered predictions tested honestly.

Experiment 1: MoE k/N at N=64 — PREDICTION: optimal k = 24 (+-3)
Experiment 2: Dropout Sweep     — PREDICTION: optimal dropout ~ 0.37 [0.30, 0.45]
Experiment 3: Lottery Ticket    — PREDICTION: winning ticket density ~ 37%
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import numpy as np
import time
import copy
import sys
sys.path.insert(0, "/Users/ghost/Dev/TECS-L")

torch.manual_seed(42)
torch.set_num_threads(4)

GZ_CENTER = 1 / np.e  # 0.3679...
BORDER = "=" * 70

def P(msg=""):
    """Print with flush."""
    print(msg, flush=True)

# --- Data Loading --------------------------------------------------------

def get_mnist(batch_size=256):
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    train_ds = datasets.MNIST("/tmp/mnist", train=True, download=True, transform=transform)
    test_ds = datasets.MNIST("/tmp/mnist", train=False, download=True, transform=transform)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=1024, shuffle=False, num_workers=0)
    return train_loader, test_loader


def evaluate(model, test_loader, device="cpu", forward_kwargs=None):
    model.eval()
    correct = 0
    total = 0
    if forward_kwargs is None:
        forward_kwargs = {}
    with torch.no_grad():
        for x, y in test_loader:
            x, y = x.to(device), y.to(device)
            out = model(x.view(x.size(0), -1), **forward_kwargs)
            pred = out.argmax(dim=1)
            correct += (pred == y).sum().item()
            total += y.size(0)
    return correct / total


# =====================================================================
# EXPERIMENT 1: MoE Top-K Sweep (N=64 experts)
# PREDICTION: optimal k = round(64/e) = 24 (+-3), i.e. k in [21, 27]
# =====================================================================

class MoEModel(nn.Module):
    """Vectorized MoE — no Python loop over experts."""
    def __init__(self, n_experts=64, input_dim=784, hidden=32, output_dim=10):
        super().__init__()
        self.n_experts = n_experts
        self.hidden = hidden
        self.output_dim = output_dim
        self.gate = nn.Linear(input_dim, n_experts)
        # Expert parameters as 3D tensors for vectorized ops
        self.expert_w1 = nn.Parameter(torch.randn(n_experts, input_dim, hidden) * 0.01)
        self.expert_b1 = nn.Parameter(torch.zeros(n_experts, hidden))
        self.expert_w2 = nn.Parameter(torch.randn(n_experts, hidden, output_dim) * 0.01)
        self.expert_b2 = nn.Parameter(torch.zeros(n_experts, output_dim))

    def forward(self, x, k=24):
        B = x.size(0)
        gate_logits = self.gate(x)                          # (B, N)
        topk_vals, topk_idx = torch.topk(gate_logits, k, dim=1)  # (B, k)
        topk_weights = F.softmax(topk_vals, dim=1)          # (B, k)

        # Vectorized: compute ALL experts at once, then select top-k
        # h1 = x @ W1 + b1 for all experts
        # x: (B, 784) -> (B, 1, 784), W1: (N, 784, 32) -> broadcast
        h1 = torch.einsum('bi,nih->bnh', x, self.expert_w1) + self.expert_b1  # (B, N, 32)
        h1 = F.relu(h1)
        h2 = torch.einsum('bnh,nho->bno', h1, self.expert_w2) + self.expert_b2  # (B, N, 10)

        # Gather top-k expert outputs: (B, k, 10)
        topk_idx_exp = topk_idx.unsqueeze(-1).expand(-1, -1, self.output_dim)  # (B, k, 10)
        selected = torch.gather(h2, 1, topk_idx_exp)       # (B, k, 10)

        # Weighted sum
        output = (topk_weights.unsqueeze(-1) * selected).sum(dim=1)  # (B, 10)
        return output


def run_experiment_1():
    P(BORDER)
    P("EXPERIMENT 1: MoE Top-K Sweep (N=64 experts)")
    P(f"PREDICTION: optimal k = round(64/e) = {round(64/np.e)} (+/-3)")
    P(f"  i.e. k in [{round(64/np.e)-3}, {round(64/np.e)+3}]")
    P(BORDER)

    k_values = [4, 8, 12, 16, 20, 24, 28, 32, 40, 48]
    results = {}

    train_loader, test_loader = get_mnist(batch_size=256)

    for k in k_values:
        torch.manual_seed(42)
        model = MoEModel(n_experts=64)
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

        t0 = time.time()
        for epoch in range(5):
            model.train()
            for x, y in train_loader:
                x = x.view(x.size(0), -1)
                out = model(x, k=k)
                loss = F.cross_entropy(out, y)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

        acc = evaluate(model, test_loader, forward_kwargs={"k": k}) * 100
        elapsed = time.time() - t0
        results[k] = acc
        ratio = k / 64
        P(f"  k={k:3d}  (k/N={ratio:.3f})  acc={acc:.2f}%  [{elapsed:.0f}s]")

    # Find best
    best_k = max(results, key=results.get)
    best_acc = results[best_k]

    P()
    P(f"  Best k = {best_k}  (k/N = {best_k/64:.3f})  acc = {best_acc:.2f}%")
    P(f"  1/e = {GZ_CENTER:.4f},  predicted k/N = {round(64*GZ_CENTER)/64:.4f}")
    P()

    # ASCII bar chart
    P("  Accuracy by k:")
    min_acc = min(results.values())
    max_acc = max(results.values())
    for k in k_values:
        acc = results[k]
        bar_len = int((acc - min_acc) / max(max_acc - min_acc, 0.01) * 40)
        marker = " <-- 1/e" if k == 24 else ""
        star = " ***BEST***" if k == best_k else ""
        P(f"  k={k:3d} |{'#' * bar_len:<40s}| {acc:.2f}%{marker}{star}")

    # Verdict
    predicted_k = round(64 / np.e)
    in_range = abs(best_k - predicted_k) <= 3
    P()
    if in_range:
        P(f"  VERDICT: CONFIRMED -- best k={best_k} within "
          f"[{predicted_k-3},{predicted_k+3}]")
    else:
        P(f"  VERDICT: REFUTED -- best k={best_k}, predicted "
          f"{predicted_k} (+/-3)")

    return results, best_k


# =====================================================================
# EXPERIMENT 2: Dropout Sweep on MNIST
# PREDICTION: optimal dropout ~ 0.37 (1/e), within [0.30, 0.45]
# =====================================================================

class DropoutMLP(nn.Module):
    def __init__(self, dropout_rate=0.5):
        super().__init__()
        self.fc1 = nn.Linear(784, 512)
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, 10)
        self.drop1 = nn.Dropout(dropout_rate)
        self.drop2 = nn.Dropout(dropout_rate)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.drop1(x)
        x = F.relu(self.fc2(x))
        x = self.drop2(x)
        x = self.fc3(x)
        return x


def run_experiment_2():
    P()
    P(BORDER)
    P("EXPERIMENT 2: Dropout Sweep on MNIST MLP")
    P(f"PREDICTION: optimal dropout ~ {GZ_CENTER:.4f} (1/e), "
      f"within [0.30, 0.45]")
    P(BORDER)

    dropout_values = [0.0, 0.1, 0.2, 0.25, 0.3, 0.35, 0.37, 0.4, 0.45, 0.5, 0.6]
    seeds = [42, 123, 777]
    results = {}

    train_loader, test_loader = get_mnist(batch_size=128)

    for dr in dropout_values:
        accs = []
        t0 = time.time()
        for seed in seeds:
            torch.manual_seed(seed)
            model = DropoutMLP(dropout_rate=dr)
            optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

            for epoch in range(10):
                model.train()
                for x, y in train_loader:
                    x = x.view(x.size(0), -1)
                    out = model(x)
                    loss = F.cross_entropy(out, y)
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()

            acc = evaluate(model, test_loader) * 100
            accs.append(acc)

        mean_acc = np.mean(accs)
        std_acc = np.std(accs)
        elapsed = time.time() - t0
        results[dr] = (mean_acc, std_acc)
        P(f"  dropout={dr:.2f}  acc={mean_acc:.2f}% +/- {std_acc:.2f}%  "
          f"[seeds: {', '.join(f'{a:.2f}' for a in accs)}]  [{elapsed:.0f}s]")

    best_dr = max(results, key=lambda d: results[d][0])
    best_acc, best_std = results[best_dr]

    P()
    P(f"  Best dropout = {best_dr:.2f}  acc = {best_acc:.2f}% "
      f"+/- {best_std:.2f}%")
    P(f"  1/e = {GZ_CENTER:.4f}")
    P()

    # ASCII bar chart
    P("  Accuracy by dropout rate:")
    min_acc = min(v[0] for v in results.values())
    max_acc = max(v[0] for v in results.values())
    for dr in dropout_values:
        acc = results[dr][0]
        bar_len = int((acc - min_acc) / max(max_acc - min_acc, 0.01) * 40)
        marker = " <-- 1/e" if dr == 0.37 else ""
        star = " ***BEST***" if dr == best_dr else ""
        P(f"  {dr:.2f} |{'#' * bar_len:<40s}| {acc:.2f}%{marker}{star}")

    # Verdict
    in_range = 0.30 <= best_dr <= 0.45
    P()
    if in_range:
        P(f"  VERDICT: CONFIRMED -- best dropout={best_dr:.2f} "
          f"within [0.30, 0.45]")
    else:
        P(f"  VERDICT: REFUTED -- best dropout={best_dr:.2f}, "
          f"predicted [0.30, 0.45]")

    return results, best_dr


# =====================================================================
# EXPERIMENT 3: Lottery Ticket at 37% Density
# PREDICTION: winning ticket density ~ 37% (1/e) of original weights
# Threshold: accuracy drops below (original - 5%)
# =====================================================================

class LotteryMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(784, 300)
        self.fc2 = nn.Linear(300, 100)
        self.fc3 = nn.Linear(100, 10)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x


def get_masks(model):
    masks = {}
    for name, param in model.named_parameters():
        if 'weight' in name:
            masks[name] = torch.ones_like(param, dtype=torch.bool)
    return masks


def apply_masks(model, masks):
    with torch.no_grad():
        for name, param in model.named_parameters():
            if name in masks:
                param.mul_(masks[name].float())


def prune_lowest(model, masks, prune_frac=0.2):
    """Prune the lowest prune_frac of remaining weights globally."""
    all_weights = []
    for name, param in model.named_parameters():
        if name in masks:
            alive = param[masks[name]].abs()
            all_weights.append(alive)

    all_weights = torch.cat(all_weights)
    n_prune = int(prune_frac * all_weights.numel())
    if n_prune == 0:
        return masks

    threshold = torch.topk(all_weights, n_prune, largest=False).values[-1]

    new_masks = {}
    for name, param in model.named_parameters():
        if name in masks:
            new_masks[name] = masks[name] & (param.abs() > threshold)

    return new_masks


def mask_density(masks):
    total = sum(m.numel() for m in masks.values())
    alive = sum(m.sum().item() for m in masks.values())
    return alive / total


def run_experiment_3():
    P()
    P(BORDER)
    P("EXPERIMENT 3: Lottery Ticket — Iterative Magnitude Pruning")
    P(f"PREDICTION: winning ticket density ~ {GZ_CENTER:.4f} (1/e)")
    P(f"  Threshold: accuracy drops below (original - 5%)")
    P(BORDER)

    train_loader, test_loader = get_mnist(batch_size=128)

    # Train original model to get baseline
    torch.manual_seed(42)
    model = LotteryMLP()
    init_state = copy.deepcopy(model.state_dict())  # save initial weights
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    P("  Training baseline model (10 epochs)...")
    for epoch in range(10):
        model.train()
        for x, y in train_loader:
            x = x.view(x.size(0), -1)
            out = model(x)
            loss = F.cross_entropy(out, y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    baseline_acc = evaluate(model, test_loader) * 100
    threshold_acc = baseline_acc - 5.0
    total_w = sum(p.numel() for n, p in model.named_parameters() if 'weight' in n)
    P(f"  Baseline accuracy: {baseline_acc:.2f}%")
    P(f"  Threshold (baseline - 5%): {threshold_acc:.2f}%")
    P(f"  Total weight params: {total_w}")
    P()

    # Iterative pruning
    masks = get_masks(model)
    results = []

    # Record baseline
    d = mask_density(masks)
    results.append((d * 100, baseline_acc))
    P(f"  density={d*100:6.1f}%  acc={baseline_acc:.2f}%  [baseline]")

    n_rounds = 8  # 0.8^8 = 0.168, goes well below 37%
    for r in range(n_rounds):
        t0 = time.time()
        # Prune based on trained weights
        masks = prune_lowest(model, masks, prune_frac=0.2)

        # Reset to initial weights (lottery ticket hypothesis)
        model.load_state_dict(init_state)
        apply_masks(model, masks)

        # Retrain with masks
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
        for epoch in range(10):
            model.train()
            for x, y in train_loader:
                x = x.view(x.size(0), -1)
                out = model(x)
                loss = F.cross_entropy(out, y)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            apply_masks(model, masks)  # re-zero pruned weights after each epoch

        acc = evaluate(model, test_loader) * 100
        d = mask_density(masks)
        elapsed = time.time() - t0
        results.append((d * 100, acc))
        status = "OK" if acc >= threshold_acc else "BELOW THRESHOLD"
        P(f"  density={d*100:6.1f}%  acc={acc:.2f}%  [{status}]  [{elapsed:.0f}s]")

    P()

    # Find threshold density
    threshold_density = None
    winning_density = None
    for i in range(len(results)):
        d_pct, acc = results[i]
        if acc < threshold_acc:
            threshold_density = d_pct
            if i > 0:
                winning_density = results[i - 1][0]
            else:
                winning_density = 100.0
            break

    if threshold_density is None:
        winning_density = results[-1][0]
        P(f"  Never dropped below threshold! Lowest density "
          f"tested: {results[-1][0]:.1f}%")

    # ASCII chart
    P("  Accuracy vs Density:")
    min_acc = min(r[1] for r in results)
    max_acc = max(r[1] for r in results)
    for d_pct, acc in results:
        bar_len = int((acc - min_acc + 0.1) / max(max_acc - min_acc + 0.1, 0.01) * 40)
        marker = ""
        if abs(d_pct - 37) < 5:
            marker = " <-- ~1/e zone"
        if acc < threshold_acc:
            marker += " [BELOW]"
        P(f"  {d_pct:5.1f}% |{'#' * bar_len:<40s}| {acc:.2f}%{marker}")

    P(f"  {'':5s}  threshold = {threshold_acc:.2f}%")

    P()
    if threshold_density is not None:
        P(f"  Winning ticket density: {winning_density:.1f}%")
        P(f"  First failure density:  {threshold_density:.1f}%")
        P(f"  1/e = {GZ_CENTER * 100:.1f}%")
        in_range = 25 <= winning_density <= 50
        if in_range:
            P(f"  VERDICT: CONFIRMED -- winning density {winning_density:.1f}% "
              f"near 1/e={GZ_CENTER * 100:.1f}%")
        else:
            P(f"  VERDICT: REFUTED -- winning density {winning_density:.1f}%, "
              f"predicted ~37%")
    else:
        P(f"  VERDICT: INCONCLUSIVE -- model never dropped below threshold")
        P(f"  at lowest tested density {results[-1][0]:.1f}%")

    return results, winning_density


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    P(BORDER)
    P("GZ PREDICTION EXPERIMENTS — PyTorch on Mac CPU")
    P(f"torch {torch.__version__}, numpy {np.__version__}")
    P(f"Device: CPU (4 threads)")
    P(f"1/e = {GZ_CENTER:.6f}")
    P(BORDER)

    t_total = time.time()

    r1, best_k = run_experiment_1()
    r2, best_dr = run_experiment_2()
    r3, win_density = run_experiment_3()

    elapsed = time.time() - t_total
    P()
    P(BORDER)
    P("SUMMARY")
    P(BORDER)
    P(f"  Exp 1 (MoE k/N):     best k = {best_k}, "
      f"k/N = {best_k / 64:.3f}, predicted 24/64 = 0.375")
    P(f"  Exp 2 (Dropout):      best = {best_dr:.2f}, "
      f"predicted 0.37 (1/e)")
    P(f"  Exp 3 (Lottery):      winning density = "
      f"{win_density:.1f}% (predicted 37%)")
    P(f"  Total time: {elapsed:.0f}s ({elapsed / 60:.1f} min)")
    P(BORDER)
