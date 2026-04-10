#!/usr/bin/env python3
"""H-CX-15: MoE optimal activation ratio = 1-1/e ?

Hypothesis: In Mixture of Experts, optimal activation ratio (k/N) converges to 1-1/e ~ 0.632.
            Golden zone P!=NP gap ratio = 1-1/e = transition cost.
            Also: Dense model optimal dropout ~ 1/e ~ 0.368 (inactive ratio).

Experiment:
  Part 1 - MoE activation ratio: N=8, k=1..8, 3 trials x 10 epochs, MNIST
  Part 2 - Dense dropout: drop={0,0.1,0.2,0.3,0.37,0.5,0.7}, 3 trials x 10 epochs
"""

import sys
import os
import time
import math

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torchvision import datasets, transforms
from torch.utils.data import DataLoader

DEVICE = torch.device('cpu')
INV_E = 1.0 / math.e
ONE_MINUS_INV_E = 1.0 - INV_E


class SimpleMoE(nn.Module):
    def __init__(self, input_dim=784, hidden=64, output_dim=10, n_experts=8, k=5):
        super().__init__()
        self.n_experts = n_experts
        self.k = k
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(input_dim, hidden),
                nn.ReLU(),
                nn.Linear(hidden, output_dim)
            ) for _ in range(n_experts)
        ])
        self.gate = nn.Linear(input_dim, n_experts)

    def forward(self, x):
        scores = self.gate(x)
        topk_v, topk_i = scores.topk(self.k, dim=-1)
        mask = torch.zeros_like(scores).scatter(-1, topk_i, 1.0)
        weights = F.softmax(scores, dim=-1) * mask
        weights = weights / (weights.sum(-1, keepdim=True) + 1e-8)
        outs = torch.stack([e(x) for e in self.experts], dim=1)
        return (weights.unsqueeze(-1) * outs).sum(1)

    def active_params(self):
        ep = sum(p.numel() for p in self.experts[0].parameters())
        gp = sum(p.numel() for p in self.gate.parameters())
        return self.k * ep + gp

    def total_params(self):
        return sum(p.numel() for p in self.parameters())


class DenseMLP(nn.Module):
    def __init__(self, hidden=512, drop=0.0):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(784, hidden),
            nn.ReLU(),
            nn.Dropout(drop),
            nn.Linear(hidden, 10)
        )

    def forward(self, x):
        return self.net(x)


def get_mnist(batch_size=128):
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    train_ds = datasets.MNIST('/tmp/data', train=True, download=True, transform=transform)
    test_ds = datasets.MNIST('/tmp/data', train=False, transform=transform)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=512, shuffle=False, num_workers=0)
    return train_loader, test_loader


def train_and_eval(model, train_loader, test_loader, epochs=10, lr=1e-3):
    model.to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        for bx, by in train_loader:
            bx = bx.view(bx.size(0), -1).to(DEVICE)
            by = by.to(DEVICE)
            optimizer.zero_grad()
            loss = criterion(model(bx), by)
            loss.backward()
            optimizer.step()

    model.eval()
    correct = total = 0
    with torch.no_grad():
        for bx, by in test_loader:
            bx = bx.view(bx.size(0), -1).to(DEVICE)
            by = by.to(DEVICE)
            pred = model(bx).argmax(dim=-1)
            correct += (pred == by).sum().item()
            total += by.size(0)
    return correct / total * 100.0


def main():
    t0 = time.time()
    print(f"Device: {DEVICE}")
    print(f"1/e = {INV_E:.4f}, 1-1/e = {ONE_MINUS_INV_E:.4f}\n")

    train_loader, test_loader = get_mnist()

    # ============================================================
    # Part 1: MoE Activation Ratio Sweep
    # ============================================================
    print("=" * 65)
    print("Part 1: MoE Activation Ratio Sweep (N=8, k=1..8, 3 trials)")
    print("=" * 65)

    N = 8
    moe_results = []

    for k in range(1, N + 1):
        ratio = k / N
        accs = []
        for trial in range(3):
            torch.manual_seed(42 + trial * 100 + k)
            np.random.seed(42 + trial * 100 + k)
            model = SimpleMoE(784, 64, 10, n_experts=N, k=k)
            acc = train_and_eval(model, train_loader, test_loader, epochs=10)
            accs.append(acc)
            print(f"  k={k}/8 ratio={ratio:.3f} trial {trial+1}: {acc:.2f}%")

        active_p = model.active_params()
        total_p = model.total_params()
        mean_acc = np.mean(accs)
        std_acc = np.std(accs)
        efficiency = mean_acc / (active_p / 1000.0)

        moe_results.append({
            'k': k, 'ratio': ratio,
            'mean': mean_acc, 'std': std_acc,
            'accs': accs,
            'active_params': active_p, 'total_params': total_p,
            'efficiency': efficiency,
        })

    # Table
    print("\n" + "=" * 80)
    print("MoE Results: k vs Accuracy (N=8 experts, hidden=64)")
    print("=" * 80)
    print(f"{'k':>3} | {'ratio':>6} | {'mean%':>7} | {'std':>5} | {'active_p':>9} | {'eff(acc/kP)':>11} | note")
    print("-" * 80)

    best_k = max(moe_results, key=lambda r: r['mean'])['k']
    best_eff_k = max(moe_results, key=lambda r: r['efficiency'])['k']

    for r in moe_results:
        note = ""
        if r['k'] == best_k:
            note = "BEST-ACC"
        if r['k'] == best_eff_k:
            note += " BEST-EFF" if note else "BEST-EFF"
        if abs(r['ratio'] - ONE_MINUS_INV_E) < 0.07:
            note += " ~1-1/e"
        print(f"{r['k']:3d} | {r['ratio']:6.3f} | {r['mean']:7.2f} | {r['std']:5.2f} | {r['active_params']:9,d} | {r['efficiency']:11.4f} | {note}")

    br = next(r for r in moe_results if r['k'] == best_k)
    print(f"\n1-1/e = {ONE_MINUS_INV_E:.4f}")
    print(f"Best accuracy:   k={best_k}/8, ratio={br['ratio']:.3f}, acc={br['mean']:.2f}%")
    print(f"Delta from 1-1/e: {abs(br['ratio'] - ONE_MINUS_INV_E):.4f}")

    # ASCII accuracy graph
    print(f"\n{'='*65}")
    print("ASCII Graph: Activation Ratio vs Accuracy")
    print(f"{'='*65}")
    all_means = [r['mean'] for r in moe_results]
    lo, hi = min(all_means), max(all_means)
    W = 45

    for r in moe_results:
        if hi > lo:
            bar_len = int((r['mean'] - lo) / (hi - lo) * W)
        else:
            bar_len = W
        mark = " <-- 1-1/e" if abs(r['ratio'] - ONE_MINUS_INV_E) < 0.07 else ""
        best_mark = " <<<" if r['k'] == best_k else ""
        print(f"  k={r['k']}({r['ratio']:.2f}) |{'#' * bar_len}{'.' * (W - bar_len)}| {r['mean']:.2f}%{best_mark}{mark}")

    # ASCII efficiency graph
    print(f"\n{'='*65}")
    print("ASCII Graph: Activation Ratio vs Param Efficiency")
    print(f"{'='*65}")
    all_effs = [r['efficiency'] for r in moe_results]
    lo_e, hi_e = min(all_effs), max(all_effs)

    for r in moe_results:
        if hi_e > lo_e:
            bar_len = int((r['efficiency'] - lo_e) / (hi_e - lo_e) * W)
        else:
            bar_len = W
        mark = " <-- 1-1/e" if abs(r['ratio'] - ONE_MINUS_INV_E) < 0.07 else ""
        best_mark = " <<<" if r['k'] == best_eff_k else ""
        print(f"  k={r['k']}({r['ratio']:.2f}) |{'#' * bar_len}{'.' * (W - bar_len)}| {r['efficiency']:.4f}{best_mark}{mark}")

    # ============================================================
    # Part 2: Dense Dropout Sweep
    # ============================================================
    print(f"\n\n{'='*65}")
    print("Part 2: Dense Model Dropout Sweep (hidden=512, 3 trials)")
    print("=" * 65)

    dropouts = [0.0, 0.1, 0.2, 0.3, 0.37, 0.5, 0.7]
    drop_results = []

    for dp in dropouts:
        accs = []
        for trial in range(3):
            torch.manual_seed(42 + trial * 100 + int(dp * 1000))
            np.random.seed(42 + trial * 100 + int(dp * 1000))
            model = DenseMLP(hidden=512, drop=dp)
            acc = train_and_eval(model, train_loader, test_loader, epochs=10)
            accs.append(acc)
            print(f"  dropout={dp:.2f} trial {trial+1}: {acc:.2f}%")

        mean_acc = np.mean(accs)
        drop_results.append({
            'drop': dp, 'mean': mean_acc, 'std': np.std(accs), 'accs': accs
        })

    # Table
    print(f"\n{'='*50}")
    print("Dropout Results: dropout_rate vs Accuracy")
    print("=" * 50)
    print(f"{'dropout':>8} | {'mean%':>7} | {'std':>5} | note")
    print("-" * 50)

    best_dp = max(drop_results, key=lambda r: r['mean'])['drop']

    for r in drop_results:
        note = ""
        if r['drop'] == best_dp:
            note = "BEST"
        if abs(r['drop'] - INV_E) < 0.04:
            note += " ~1/e"
        print(f"{r['drop']:8.2f} | {r['mean']:7.2f} | {r['std']:5.2f} | {note}")

    bd = next(r for r in drop_results if r['drop'] == best_dp)
    print(f"\n1/e = {INV_E:.4f}")
    print(f"Best dropout: {best_dp:.2f}, acc={bd['mean']:.2f}%")
    print(f"Delta from 1/e: {abs(best_dp - INV_E):.4f}")

    # ASCII dropout graph
    print(f"\n{'='*65}")
    print("ASCII Graph: Dropout Rate vs Accuracy")
    print(f"{'='*65}")
    all_d_means = [r['mean'] for r in drop_results]
    lo_d, hi_d = min(all_d_means), max(all_d_means)

    for r in drop_results:
        if hi_d > lo_d:
            bar_len = int((r['mean'] - lo_d) / (hi_d - lo_d) * W)
        else:
            bar_len = W
        mark = " <-- 1/e" if abs(r['drop'] - INV_E) < 0.04 else ""
        best_mark = " <<<" if r['drop'] == best_dp else ""
        print(f"  dp={r['drop']:.2f} |{'#' * bar_len}{'.' * (W - bar_len)}| {r['mean']:.2f}%{best_mark}{mark}")

    # ============================================================
    # Final Summary
    # ============================================================
    elapsed = time.time() - t0
    print(f"\n\n{'='*65}")
    print("SUMMARY: H-CX-15 Activation Ratio Hypothesis")
    print("=" * 65)
    print(f"Total time: {elapsed:.1f}s\n")

    print("MoE (N=8 experts):")
    print(f"  Predicted optimal ratio:  1-1/e = {ONE_MINUS_INV_E:.4f}")
    print(f"  Best accuracy:  k={best_k}/8, ratio={br['ratio']:.3f}, acc={br['mean']:.2f}%")
    moe_delta = abs(br['ratio'] - ONE_MINUS_INV_E)
    moe_match = moe_delta < 0.15
    print(f"  Match: {'YES' if moe_match else 'NO'} (delta={moe_delta:.4f})")

    print(f"\nDropout:")
    print(f"  Predicted optimal dropout: 1/e = {INV_E:.4f}")
    print(f"  Best dropout: {best_dp:.2f}, acc={bd['mean']:.2f}%")
    dp_delta = abs(best_dp - INV_E)
    dp_match = dp_delta < 0.15
    print(f"  Match: {'YES' if dp_match else 'NO'} (delta={dp_delta:.4f})")

    if moe_match and dp_match:
        print("\n  >> BOTH predictions confirmed. 1-1/e is the activation sweet spot.")
    elif moe_match or dp_match:
        print("\n  >> PARTIAL confirmation. One of two predictions matched.")
    else:
        print("\n  >> Neither prediction confirmed. Hypothesis not supported.")


if __name__ == '__main__':
    main()
