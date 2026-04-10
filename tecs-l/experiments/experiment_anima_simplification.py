#!/usr/bin/env python3
"""AnimaLM Simplification Verification

Core question: Is moe_output(A+G) redundant?
H-334 showed Pure Field >= equilibrium+field.

Tests on MNIST + CIFAR-10:
1. Original: mix*(A+G) + (1-mix)*scale*sqrt*dir
2. Pure tension: scale * sqrt(tension) * direction  (no moe_output)
3. Raw repulsion: A - G  (maximally simple)
4. Scaled repulsion: scale * (A - G)  (one learnable param)
5. Golden MoE baseline: weighted sum only (no tension)
"""
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import numpy as np
import time

print = lambda *a, **k: (sys.stdout.write(' '.join(map(str, a)) + k.get('end', '\n')), sys.stdout.flush())


class Expert(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )
    def forward(self, x):
        return self.net(x)


class Expert3L(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )
    def forward(self, x):
        return self.net(x)


class BoltzmannGate(nn.Module):
    def __init__(self, input_dim, n_experts, temperature=np.e, active_ratio=0.625):
        super().__init__()
        self.gate = nn.Linear(input_dim, n_experts)
        self.temperature = temperature
        self.n_active = max(1, int(n_experts * active_ratio))

    def forward(self, x):
        scores = self.gate(x) / self.temperature
        probs = F.softmax(scores, dim=-1)
        topk_vals, topk_idx = probs.topk(self.n_active, dim=-1)
        mask = torch.zeros_like(probs)
        mask.scatter_(-1, topk_idx, 1.0)
        weights = probs * mask
        return weights / (weights.sum(dim=-1, keepdim=True) + 1e-8)


def get_ag_outputs(experts, gate, x, n_camp_a):
    weights = gate(x)
    out_a = torch.zeros(x.size(0), experts[0].net[-1].out_features, device=x.device)
    out_g = torch.zeros_like(out_a)
    for i, expert in enumerate(experts):
        w = weights[:, i].unsqueeze(-1)
        e_out = expert(x)
        if i < n_camp_a:
            out_a = out_a + w * e_out
        else:
            out_g = out_g + w * e_out
    return out_a, out_g


# ─── 1. Original AnimaLM ───
class AnimaOriginal(nn.Module):
    """mix*(A+G) + (1-mix)*scale*sqrt(tension)*dir"""
    def __init__(self, input_dim, hidden_dim, output_dim, n_experts=8, ExpertCls=Expert):
        super().__init__()
        self.n_camp_a = n_experts // 2
        self.experts = nn.ModuleList([ExpertCls(input_dim, hidden_dim, output_dim) for _ in range(n_experts)])
        self.gate = BoltzmannGate(input_dim, n_experts)
        self.tension_scale = nn.Parameter(torch.ones(1))
        self.alpha = nn.Parameter(torch.zeros(1))

    def forward(self, x):
        out_a, out_g = get_ag_outputs(self.experts, self.gate, x, self.n_camp_a)
        repulsion = out_a - out_g
        tension = repulsion.pow(2).mean(dim=-1, keepdim=True)
        direction = repulsion / (repulsion.norm(dim=-1, keepdim=True) + 1e-8)
        tension_output = self.tension_scale * torch.sqrt(tension + 1e-8) * direction
        moe_output = out_a + out_g
        mix = torch.sigmoid(self.alpha)
        return mix * moe_output + (1 - mix) * tension_output


# ─── 2. Pure Tension (no moe_output) ───
class AnimaPureTension(nn.Module):
    """scale * sqrt(tension) * direction — NO A+G mixing"""
    def __init__(self, input_dim, hidden_dim, output_dim, n_experts=8, ExpertCls=Expert):
        super().__init__()
        self.n_camp_a = n_experts // 2
        self.experts = nn.ModuleList([ExpertCls(input_dim, hidden_dim, output_dim) for _ in range(n_experts)])
        self.gate = BoltzmannGate(input_dim, n_experts)
        self.tension_scale = nn.Parameter(torch.ones(1))

    def forward(self, x):
        out_a, out_g = get_ag_outputs(self.experts, self.gate, x, self.n_camp_a)
        repulsion = out_a - out_g
        tension = repulsion.pow(2).mean(dim=-1, keepdim=True)
        direction = repulsion / (repulsion.norm(dim=-1, keepdim=True) + 1e-8)
        return self.tension_scale * torch.sqrt(tension + 1e-8) * direction


# ─── 3. Raw Repulsion (A - G, nothing else) ───
class AnimaRawRepulsion(nn.Module):
    """output = A - G. Maximum simplicity."""
    def __init__(self, input_dim, hidden_dim, output_dim, n_experts=8, ExpertCls=Expert):
        super().__init__()
        self.n_camp_a = n_experts // 2
        self.experts = nn.ModuleList([ExpertCls(input_dim, hidden_dim, output_dim) for _ in range(n_experts)])
        self.gate = BoltzmannGate(input_dim, n_experts)

    def forward(self, x):
        out_a, out_g = get_ag_outputs(self.experts, self.gate, x, self.n_camp_a)
        return out_a - out_g


# ─── 4. Scaled Repulsion ───
class AnimaScaledRepulsion(nn.Module):
    """output = scale * (A - G). One learnable param."""
    def __init__(self, input_dim, hidden_dim, output_dim, n_experts=8, ExpertCls=Expert):
        super().__init__()
        self.n_camp_a = n_experts // 2
        self.experts = nn.ModuleList([ExpertCls(input_dim, hidden_dim, output_dim) for _ in range(n_experts)])
        self.gate = BoltzmannGate(input_dim, n_experts)
        self.scale = nn.Parameter(torch.ones(1))

    def forward(self, x):
        out_a, out_g = get_ag_outputs(self.experts, self.gate, x, self.n_camp_a)
        return self.scale * (out_a - out_g)


# ─── 5. Golden MoE (no tension, A+G only) ───
class GoldenMoEOnly(nn.Module):
    """output = A + G. Standard MoE weighted sum."""
    def __init__(self, input_dim, hidden_dim, output_dim, n_experts=8, ExpertCls=Expert):
        super().__init__()
        self.experts = nn.ModuleList([ExpertCls(input_dim, hidden_dim, output_dim) for _ in range(n_experts)])
        self.gate = BoltzmannGate(input_dim, n_experts, active_ratio=0.7)

    def forward(self, x):
        weights = self.gate(x)
        outputs = torch.stack([e(x) for e in self.experts], dim=1)
        return (weights.unsqueeze(-1) * outputs).sum(dim=1)


def train_eval(model, train_loader, test_loader, epochs, lr=0.001, device='cpu'):
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    accs = []

    for epoch in range(epochs):
        model.train()
        for X, y in train_loader:
            X = X.view(X.size(0), -1).to(device)
            y = y.to(device)
            optimizer.zero_grad()
            out = model(X)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()

        model.eval()
        correct = total = 0
        with torch.no_grad():
            for X, y in test_loader:
                X = X.view(X.size(0), -1).to(device)
                y = y.to(device)
                correct += (model(X).argmax(1) == y).sum().item()
                total += y.size(0)
        acc = correct / total
        accs.append(acc)

    return accs


def run_benchmark(dataset_name, input_dim, hidden_dim, epochs, ExpertCls, device):
    if dataset_name == 'MNIST':
        transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
        train_data = datasets.MNIST('./data', train=True, download=True, transform=transform)
        test_data = datasets.MNIST('./data', train=False, transform=transform)
    else:
        transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,0.5,0.5), (0.5,0.5,0.5))])
        train_data = datasets.CIFAR10('./data', train=True, download=True, transform=transform)
        test_data = datasets.CIFAR10('./data', train=False, transform=transform)

    train_loader = DataLoader(train_data, batch_size=128, shuffle=True)
    test_loader = DataLoader(test_data, batch_size=256)

    models = {
        'Golden MoE (A+G)':     lambda: GoldenMoEOnly(input_dim, hidden_dim, 10, ExpertCls=ExpertCls),
        'Original (mix)':       lambda: AnimaOriginal(input_dim, hidden_dim, 10, ExpertCls=ExpertCls),
        'Pure Tension':         lambda: AnimaPureTension(input_dim, hidden_dim, 10, ExpertCls=ExpertCls),
        'Raw Repulsion (A-G)':  lambda: AnimaRawRepulsion(input_dim, hidden_dim, 10, ExpertCls=ExpertCls),
        'Scaled (s*(A-G))':     lambda: AnimaScaledRepulsion(input_dim, hidden_dim, 10, ExpertCls=ExpertCls),
    }

    seeds = [42, 123]
    results = {name: [] for name in models}

    for seed in seeds:
        for name, model_fn in models.items():
            torch.manual_seed(seed)
            np.random.seed(seed)
            model = model_fn()
            params = sum(p.numel() for p in model.parameters())

            start = time.time()
            accs = train_eval(model, train_loader, test_loader, epochs, device=device)
            elapsed = time.time() - start

            results[name].append({
                'best': max(accs), 'final': accs[-1],
                'params': params, 'time': elapsed,
            })

    return results


def print_results(dataset_name, results):
    print(f"\n{'=' * 70}")
    print(f"  {dataset_name} Results (mean of 2 seeds)")
    print(f"{'=' * 70}")
    print(f"\n  {'Model':24s} | {'Best':>8s} | {'Final':>8s} | {'Params':>8s} | {'Time':>6s}")
    print(f"  {'─'*24}-+-{'─'*8}-+-{'─'*8}-+-{'─'*8}-+-{'─'*6}")

    sorted_models = sorted(results.items(),
                          key=lambda x: np.mean([r['best'] for r in x[1]]),
                          reverse=True)

    for name, runs in sorted_models:
        mb = np.mean([r['best'] for r in runs]) * 100
        mf = np.mean([r['final'] for r in runs]) * 100
        p = runs[0]['params']
        t = np.mean([r['time'] for r in runs])
        # Mark winner
        marker = ' <-- BEST' if name == sorted_models[0][0] else ''
        print(f"  {name:24s} | {mb:6.2f}% | {mf:6.2f}% | {p:>8,} | {t:5.0f}s{marker}")

    # Show deltas vs Raw Repulsion
    raw_best = np.mean([r['best'] for r in results['Raw Repulsion (A-G)']])
    print(f"\n  Delta vs Raw Repulsion (A-G):")
    for name, runs in sorted_models:
        mb = np.mean([r['best'] for r in runs])
        diff = (mb - raw_best) * 100
        print(f"    {name:24s}: {diff:+.2f}%")


def main():
    print("=" * 70)
    print("  AnimaLM Simplification Test")
    print("  Q: Is moe_output(A+G) redundant?")
    print("  Q: Is scale*sqrt*normalize redundant?")
    print("  Q: Is 'A - G' all you need?")
    print("=" * 70)

    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    print(f"  Device: {device}")

    # MNIST
    print(f"\n  Running MNIST (10 epochs)...")
    mnist_results = run_benchmark('MNIST', 784, 64, 10, Expert, device)
    print_results('MNIST', mnist_results)

    # CIFAR-10
    print(f"\n  Running CIFAR-10 (15 epochs)...")
    cifar_results = run_benchmark('CIFAR', 3072, 128, 15, Expert3L, device)
    print_results('CIFAR-10', cifar_results)

    # Final verdict
    print(f"\n{'=' * 70}")
    print(f"  VERDICT")
    print(f"{'=' * 70}")

    for ds, res in [('MNIST', mnist_results), ('CIFAR', cifar_results)]:
        bests = {name: np.mean([r['best'] for r in runs]) for name, runs in res.items()}
        winner = max(bests, key=bests.get)
        raw = bests['Raw Repulsion (A-G)']
        orig = bests['Original (mix)']
        golden = bests['Golden MoE (A+G)']

        print(f"\n  {ds}:")
        print(f"    Winner: {winner} ({bests[winner]*100:.2f}%)")
        print(f"    Raw(A-G) vs Original: {(raw-orig)*100:+.2f}%")
        print(f"    Raw(A-G) vs GoldenMoE: {(raw-golden)*100:+.2f}%")

        if abs(raw - orig) < 0.003:
            print(f"    --> moe_output + scale + sqrt + normalize are ALL REDUNDANT")
            print(f"    --> 'A - G' is sufficient")
        elif raw > orig:
            print(f"    --> Simpler is BETTER. Remove complexity.")
        else:
            print(f"    --> Original mixing adds value on this dataset.")

    print(f"\n{'=' * 70}")


if __name__ == '__main__':
    main()
