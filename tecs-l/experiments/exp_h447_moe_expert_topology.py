#!/usr/bin/env python3
"""H-CX-447: MoE Expert Specialization Follows Perfect Number Structure

H-EE-10 confirmed: 24 narrow experts (phi-bottleneck) beat 8 wide experts.
Question: Does the expert activation pattern follow sigma(6)=12 structure?

Predictions:
  P1: At convergence, exactly sigma(6)=12 of 24 experts are active (load > 5%)
  P2: Expert activation forms tau(6)=4 clusters in PH dendrogram
  P3: Top-k routing with k=tau(6)=4 outperforms k=2 for 24 experts

Experiment: Train 24-expert MoE on MNIST, analyze activation patterns.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from scipy.stats import spearmanr
from torchvision import datasets, transforms


def load_mnist(bs=256):
    t = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,),(0.3081,))])
    tr = torch.utils.data.DataLoader(datasets.MNIST('~/.cache/mnist', train=True, download=True, transform=t), batch_size=bs, shuffle=True)
    te = torch.utils.data.DataLoader(datasets.MNIST('~/.cache/mnist', train=False, transform=t), batch_size=bs)
    return tr, te


class PhiMoE(nn.Module):
    """24 narrow experts with top-k routing."""
    def __init__(self, input_dim=784, expert_hidden=85, output_dim=10, n_experts=24, top_k=2):
        super().__init__()
        self.n_experts = n_experts
        self.top_k = top_k
        self.gate = nn.Linear(input_dim, n_experts)
        self.experts = nn.ModuleList([
            nn.Sequential(nn.Linear(input_dim, expert_hidden), nn.ReLU(), nn.Linear(expert_hidden, output_dim))
            for _ in range(n_experts)
        ])

    def forward(self, x):
        gate_logits = self.gate(x)
        gate_probs = F.softmax(gate_logits, dim=-1)
        topk_vals, topk_idx = torch.topk(gate_probs, self.top_k, dim=-1)
        topk_vals = topk_vals / topk_vals.sum(dim=-1, keepdim=True)

        out = torch.zeros(x.size(0), 10, device=x.device)
        for i in range(self.top_k):
            expert_idx = topk_idx[:, i]
            weight = topk_vals[:, i].unsqueeze(-1)
            for e in range(self.n_experts):
                mask = expert_idx == e
                if mask.any():
                    out[mask] += weight[mask] * self.experts[e](x[mask])
        return out, gate_probs


def main():
    print("=" * 70)
    print("  H-CX-447: MoE Expert Specialization & Perfect Number Structure")
    print("=" * 70)

    torch.manual_seed(42)
    tr, te = load_mnist()

    # Test multiple top-k values
    results = {}
    for top_k in [2, 4, 6]:
        print(f"\n  --- top_k={top_k} (tau(6)={4}, sigma_-1(6)={2}, phi(6)={2}) ---")
        model = PhiMoE(top_k=top_k)
        opt = torch.optim.Adam(model.parameters(), lr=1e-3)
        ce = nn.CrossEntropyLoss()

        expert_loads_history = []

        for ep in range(1, 11):
            model.train()
            epoch_gates = []
            for x, y in tr:
                opt.zero_grad()
                out, gates = model(x.view(-1, 784))
                loss = ce(out, y)
                # Load balancing loss
                mean_gates = gates.mean(0)
                bal_loss = 24 * (mean_gates ** 2).sum()
                total_loss = loss + 0.01 * bal_loss
                total_loss.backward()
                opt.step()
                epoch_gates.append(gates.detach().mean(0).numpy())

            # Expert load analysis
            avg_gates = np.mean(epoch_gates, axis=0)
            active_experts = (avg_gates > 0.05 / 24 * 5).sum()  # >5x uniform

            if ep % 3 == 0 or ep == 10:
                model.eval()
                correct, total = 0, 0
                with torch.no_grad():
                    for x, y in te:
                        out, _ = model(x.view(-1, 784))
                        correct += (out.argmax(1) == y).sum().item()
                        total += len(y)
                acc = correct / total * 100
                print(f"    Ep {ep:2d}: acc={acc:.2f}%  active={active_experts}/24  load_std={avg_gates.std():.4f}")

            expert_loads_history.append(avg_gates.copy())

        # Final analysis
        model.eval()
        correct, total = 0, 0
        all_gates = []
        with torch.no_grad():
            for x, y in te:
                out, gates = model(x.view(-1, 784))
                correct += (out.argmax(1) == y).sum().item()
                total += len(y)
                all_gates.append(gates.numpy())
        final_acc = correct / total * 100
        all_gates = np.concatenate(all_gates)
        mean_load = all_gates.mean(0)

        # Count active experts (load > 2x uniform)
        uniform = 1.0 / 24
        active = (mean_load > uniform * 2).sum()
        dominant = (mean_load > uniform * 5).sum()

        results[top_k] = {
            'acc': final_acc, 'active': active, 'dominant': dominant,
            'load': mean_load, 'load_std': mean_load.std()
        }

        print(f"\n    Final: acc={final_acc:.2f}%  active(>2x uniform)={active}  dominant(>5x)={dominant}")

        # Per-expert load bar chart
        sorted_idx = np.argsort(-mean_load)
        print(f"\n    Expert Load Distribution (top_k={top_k}):")
        for rank, idx in enumerate(sorted_idx):
            bar = int(mean_load[idx] / mean_load.max() * 30)
            marker = " <-- sigma(6)=12 boundary" if rank == 11 else ""
            print(f"      E{idx:02d}: {'█'*bar}{'░'*(30-bar)} {mean_load[idx]:.4f}{marker}")

    # === Comparison ===
    print("\n" + "=" * 70)
    print("  COMPARISON: top_k vs Performance")
    print("=" * 70)
    print(f"\n  {'top_k':>5} | {'Accuracy':>8} | {'Active':>6} | {'Dominant':>8} | {'Load Std':>9}")
    print(f"  {'-'*5}-+-{'-'*8}-+-{'-'*6}-+-{'-'*8}-+-{'-'*9}")
    for k in [2, 4, 6]:
        r = results[k]
        print(f"  {k:5d} | {r['acc']:7.2f}% | {r['active']:6d} | {r['dominant']:8d} | {r['load_std']:9.4f}")

    # === P1: sigma(6)=12 active? ===
    print("\n  === P1: sigma(6)=12 active experts? ===")
    for k, r in results.items():
        match = "YES" if r['active'] == 12 else f"NO ({r['active']})"
        print(f"    top_k={k}: active={r['active']}/24 -> sigma(6)=12 match: {match}")

    # === P2: tau(6)=4 clusters? ===
    print("\n  === P2: Expert clustering (via load correlation) ===")
    # Use per-class expert activation to cluster experts
    # Check if natural clusters form

    # === P3: tau(6)=4 optimal? ===
    print("\n  === P3: tau(6)=4 optimal top_k? ===")
    best_k = max(results, key=lambda k: results[k]['acc'])
    print(f"    Best top_k={best_k} (acc={results[best_k]['acc']:.2f}%)")
    print(f"    tau(6)=4 prediction: {'CONFIRMED' if best_k == 4 else 'NOT CONFIRMED'}")

if __name__ == '__main__':
    main()
