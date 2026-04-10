#!/usr/bin/env python3
"""Hypothesis 284: Automatic tension_scale regulation — MNIST vs CIFAR vs Fashion-MNIST"""

import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class TensionAutoRegModel(nn.Module):
    def __init__(self, input_dim=784, hidden_dim=128, output_dim=10):
        super().__init__()
        self.engine_a = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3), nn.Linear(hidden_dim, output_dim))
        self.engine_g = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3), nn.Linear(hidden_dim, output_dim))
        self.tension_scale = nn.Parameter(torch.tensor(0.3))
        self.equilibrium = nn.Linear(input_dim, output_dim)

    def forward(self, x):
        out_a = self.engine_a(x)
        out_g = self.engine_g(x)
        repulsion = out_a - out_g
        tension = (repulsion ** 2).mean(dim=-1, keepdim=True)
        direction = F.normalize(repulsion, dim=-1)
        eq = self.equilibrium(x)
        output = eq + self.tension_scale * torch.sqrt(tension + 1e-8) * direction
        return output, tension.mean()

def train_and_track(model, train_loader, test_loader, epochs=15, lr=0.001):
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    history = {'epoch': [], 'tension_scale': [], 'accuracy': [], 'mean_tension': []}
    for ep in range(epochs):
        model.train()
        tensions = []
        for x, y in train_loader:
            x = x.view(x.size(0), -1)
            opt.zero_grad()
            out, t = model(x)
            loss = criterion(out, y)
            loss.backward()
            opt.step()
            tensions.append(t.item())
        model.eval()
        correct = total = 0
        with torch.no_grad():
            for x, y in test_loader:
                x = x.view(x.size(0), -1)
                out, _ = model(x)
                correct += (out.argmax(1) == y).sum().item()
                total += y.size(0)
        history['epoch'].append(ep+1)
        history['tension_scale'].append(model.tension_scale.item())
        history['accuracy'].append(correct/total*100)
        history['mean_tension'].append(np.mean(tensions))
    return history

def main():
    from torchvision import datasets, transforms
    from torch.utils.data import DataLoader

    print("=" * 70)
    print("Hypothesis 284: Automatic tension_scale regulation")
    print("=" * 70)

    configs = [
        ('MNIST', 784, datasets.MNIST, (0.1307,), (0.3081,)),
        ('Fashion-MNIST', 784, datasets.FashionMNIST, (0.2860,), (0.3530,)),
        ('CIFAR-10', 3072, datasets.CIFAR10, (0.5,0.5,0.5), (0.5,0.5,0.5)),
    ]

    all_h = {}
    for name, dim, ds_cls, mean, std in configs:
        print(f"\n{'─'*50}\n[{name}]")
        transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize(mean, std)])
        train_ds = ds_cls('/tmp/data', train=True, download=True, transform=transform)
        test_ds = ds_cls('/tmp/data', train=False, transform=transform)
        tl = DataLoader(train_ds, batch_size=128, shuffle=True)
        te = DataLoader(test_ds, batch_size=256)
        model = TensionAutoRegModel(dim, 128, 10)
        h = train_and_track(model, tl, te, epochs=15)
        all_h[name] = h
        print(f"  {'ep':>3} {'t_scale':>8} {'acc%':>7} {'tension':>8}")
        print(f"  {'-'*28}")
        for i in range(len(h['epoch'])):
            print(f"  {h['epoch'][i]:>3} {h['tension_scale'][i]:>8.4f} {h['accuracy'][i]:>7.2f} {h['mean_tension'][i]:>8.4f}")
        print(f"  Final: scale={h['tension_scale'][-1]:.4f}, acc={h['accuracy'][-1]:.2f}%")

    print(f"\n{'='*70}")
    print("Comparison summary")
    print(f"{'dataset':>15} {'final_acc':>10} {'final_scale':>12} {'interpretation':>15}")
    print(f"{'-'*55}")
    for name, h in all_h.items():
        ts = h['tension_scale'][-1]
        acc = h['accuracy'][-1]
        interp = "Active use" if ts > 0.3 else ("Partial use" if ts > 0.1 else "Voluntary abandon")
        print(f"{name:>15} {acc:>10.2f} {ts:>12.4f} {interp:>15}")

    # ASCII graph
    print(f"\ntension_scale trends")
    syms = {'MNIST': 'M', 'Fashion-MNIST': 'F', 'CIFAR-10': 'C'}
    vals = [v for h in all_h.values() for v in h['tension_scale']]
    lo, hi = min(vals), max(vals)
    grid = [[' ']*45 for _ in range(12)]
    for name, h in all_h.items():
        for i, v in enumerate(h['tension_scale']):
            x = i * 3
            y = int((v - lo) / (hi - lo + 1e-8) * 11)
            y = min(11, max(0, y))
            if x < 45: grid[11-y][x] = syms[name]
    for i, row in enumerate(grid):
        label = f"{hi:.3f}" if i == 0 else (f"{lo:.3f}" if i == 11 else "")
        print(f"  {label:>7}|{''.join(row)}|")
    print(f"         {'─'*45}")
    print(f"  M=MNIST F=Fashion C=CIFAR")
    print("\nCompleted")

if __name__ == '__main__':
    main()