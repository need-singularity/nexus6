#!/usr/bin/env python3
"""CIFAR-10: AnimaLM + Golden MoE Improvement Verification

MNIST was ceiling-bound (97.8%). CIFAR-10 has more headroom (~53%).
Tests: Golden MoE orig vs improved, PureField orig vs improved.
15 epochs, 2 seeds (CIFAR is slower).
"""
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import numpy as np
import time

# Force unbuffered output
print = lambda *a, **k: (sys.stdout.write(' '.join(map(str, a)) + k.get('end', '\n')), sys.stdout.flush())


class Expert3L(nn.Module):
    """3-layer expert matching CIFAR golden_moe_cifar.py architecture."""
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.net(x)


class BoltzmannGate(nn.Module):
    def __init__(self, input_dim, n_experts, temperature=np.e, active_ratio=0.7):
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
        weights = weights / (weights.sum(dim=-1, keepdim=True) + 1e-8)
        return weights, probs


# ─── Golden MoE Original ───
class GoldenMoEOrig(nn.Module):
    def __init__(self, input_dim=3072, hidden_dim=128, output_dim=10, n_experts=8):
        super().__init__()
        self.experts = nn.ModuleList([
            Expert3L(input_dim, hidden_dim, output_dim) for _ in range(n_experts)
        ])
        self.gate = BoltzmannGate(input_dim, n_experts)

    def forward(self, x):
        outputs = torch.stack([e(x) for e in self.experts], dim=1)
        weights, _ = self.gate(x)
        return (weights.unsqueeze(-1) * outputs).sum(dim=1), {}


# ─── Golden MoE Improved ───
class GoldenMoEImproved(nn.Module):
    def __init__(self, input_dim=3072, hidden_dim=128, output_dim=10, n_experts=8):
        super().__init__()
        self.experts = nn.ModuleList([
            Expert3L(input_dim, hidden_dim, output_dim) for _ in range(n_experts)
        ])
        self.gate = BoltzmannGate(input_dim, n_experts)
        self.n_experts = n_experts

    def forward(self, x):
        outputs = torch.stack([e(x) for e in self.experts], dim=1)
        weights, probs = self.gate(x)
        output = (weights.unsqueeze(-1) * outputs).sum(dim=1)

        # Load balancing loss
        f = (weights > 0).float().mean(dim=0)
        P = probs.mean(dim=0)
        lb_loss = 0.01 * self.n_experts * (f * P).sum()

        return output, {'lb_loss': lb_loss}


# ─── PureField Original (CIFAR) ───
class PureFieldOrig(nn.Module):
    def __init__(self, input_dim=3072, hidden_dim=128, output_dim=10, n_experts=8):
        super().__init__()
        self.n_experts = n_experts
        self.n_camp_a = n_experts // 2
        self.experts = nn.ModuleList([
            Expert3L(input_dim, hidden_dim, output_dim) for _ in range(n_experts)
        ])
        self.gate = BoltzmannGate(input_dim, n_experts, active_ratio=0.625)
        self.tension_scale = nn.Parameter(torch.ones(1))
        self.alpha = nn.Parameter(torch.zeros(1))

    def forward(self, x):
        weights, _ = self.gate(x)
        out_a = torch.zeros(x.size(0), 10, device=x.device)
        out_g = torch.zeros(x.size(0), 10, device=x.device)

        for i in range(self.n_experts):
            w = weights[:, i].unsqueeze(-1)
            e_out = self.experts[i](x)
            if i < self.n_camp_a:
                out_a = out_a + w * e_out
            else:
                out_g = out_g + w * e_out

        repulsion = out_a - out_g
        tension = repulsion.pow(2).mean(dim=-1, keepdim=True)
        direction = repulsion / (repulsion.norm(dim=-1, keepdim=True) + 1e-8)
        tension_output = self.tension_scale * torch.sqrt(tension + 1e-8) * direction

        moe_output = out_a + out_g
        mix = torch.sigmoid(self.alpha)
        output = mix * moe_output + (1.0 - mix) * tension_output
        return output, {}


# ─── PureField Improved (CIFAR) ───
class PureFieldImproved(nn.Module):
    def __init__(self, input_dim=3072, hidden_dim=128, output_dim=10, n_experts=8):
        super().__init__()
        self.n_experts = n_experts
        self.experts = nn.ModuleList([
            Expert3L(input_dim, hidden_dim, output_dim) for _ in range(n_experts)
        ])
        self.gate = BoltzmannGate(input_dim, n_experts, active_ratio=0.625)

        # Improvement 1: Input-dependent alpha
        self.alpha_proj = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )

        # Improvement 2: Soft camp
        init_logits = torch.zeros(n_experts)
        init_logits[:n_experts // 2] = 2.0
        init_logits[n_experts // 2:] = -2.0
        self.camp_logits = nn.Parameter(init_logits)

        # Improvement 3: Tension norm
        self.tension_scale = nn.Parameter(torch.ones(1))
        self.tension_norm = nn.LayerNorm(output_dim)

    def forward(self, x):
        weights, probs = self.gate(x)
        camp_a_prob = torch.sigmoid(self.camp_logits)

        out_a = torch.zeros(x.size(0), 10, device=x.device)
        out_g = torch.zeros(x.size(0), 10, device=x.device)

        for i in range(self.n_experts):
            w = weights[:, i].unsqueeze(-1)
            e_out = self.experts[i](x)
            out_a = out_a + camp_a_prob[i] * w * e_out
            out_g = out_g + (1 - camp_a_prob[i]) * w * e_out

        repulsion = out_a - out_g
        tension = repulsion.pow(2).mean(dim=-1, keepdim=True)
        direction = repulsion / (repulsion.norm(dim=-1, keepdim=True) + 1e-8)
        tension_output = self.tension_scale * torch.sqrt(tension + 1e-8) * direction
        tension_output = self.tension_norm(tension_output)

        moe_output = out_a + out_g
        mix = torch.sigmoid(self.alpha_proj(x))
        output = mix * moe_output + (1 - mix) * tension_output

        # Load balance
        f = (weights > 0).float().mean(dim=0)
        P = probs.mean(dim=0)
        lb_loss = 0.01 * self.n_experts * (f * P).sum()

        return output, {'lb_loss': lb_loss}


# ─── Top-K baseline ───
class TopKMoE(nn.Module):
    def __init__(self, input_dim=3072, hidden_dim=128, output_dim=10, n_experts=8, k=2):
        super().__init__()
        self.experts = nn.ModuleList([
            Expert3L(input_dim, hidden_dim, output_dim) for _ in range(n_experts)
        ])
        self.gate_linear = nn.Linear(input_dim, n_experts)
        self.k = k

    def forward(self, x):
        scores = self.gate_linear(x)
        topk_vals, topk_idx = scores.topk(self.k, dim=-1)
        mask = torch.zeros_like(scores)
        mask.scatter_(-1, topk_idx, 1.0)
        weights = F.softmax(scores, dim=-1) * mask
        weights = weights / (weights.sum(dim=-1, keepdim=True) + 1e-8)

        outputs = torch.stack([e(x) for e in self.experts], dim=1)
        return (weights.unsqueeze(-1) * outputs).sum(dim=1), {}


def train_eval(model, train_loader, test_loader, epochs=15, lr=0.001, device='cpu'):
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
            out, extras = model(X)
            loss = criterion(out, y)
            if 'lb_loss' in extras:
                loss = loss + extras['lb_loss']
            loss.backward()
            optimizer.step()

        model.eval()
        correct = total = 0
        with torch.no_grad():
            for X, y in test_loader:
                X = X.view(X.size(0), -1).to(device)
                y = y.to(device)
                out, _ = model(X)
                correct += (out.argmax(1) == y).sum().item()
                total += y.size(0)
        acc = correct / total
        accs.append(acc)
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"    Epoch {epoch+1:>2}: {acc*100:.1f}%")

    return accs


def main():
    print("=" * 70)
    print("  CIFAR-10: AnimaLM + Golden MoE Improvement Verification")
    print("  15 epochs, 2 seeds")
    print("=" * 70)

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])

    train_data = datasets.CIFAR10('./data', train=True, download=True, transform=transform)
    test_data = datasets.CIFAR10('./data', train=False, transform=transform)
    train_loader = DataLoader(train_data, batch_size=128, shuffle=True)
    test_loader = DataLoader(test_data, batch_size=256)

    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    print(f"  Device: {device}")

    models_config = {
        'Top-K (K=2)':              lambda: TopKMoE(),
        'Golden MoE (orig)':        lambda: GoldenMoEOrig(),
        'Golden MoE (improved)':    lambda: GoldenMoEImproved(),
        'PureField (orig)':         lambda: PureFieldOrig(),
        'PureField (improved)':     lambda: PureFieldImproved(),
    }

    seeds = [42, 123]
    all_results = {name: [] for name in models_config}

    for seed in seeds:
        print(f"\n--- Seed {seed} ---")
        for name, model_fn in models_config.items():
            torch.manual_seed(seed)
            np.random.seed(seed)
            model = model_fn()
            params = sum(p.numel() for p in model.parameters())

            print(f"\n  [{name}] params={params:,}")
            start = time.time()
            accs = train_eval(model, train_loader, test_loader, epochs=15, device=device)
            elapsed = time.time() - start

            all_results[name].append({
                'best': max(accs), 'final': accs[-1],
                'time': elapsed, 'params': params, 'accs': accs,
            })
            print(f"  -> best={max(accs)*100:.2f}% final={accs[-1]*100:.2f}% time={elapsed:.0f}s")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"  RESULTS (mean over {len(seeds)} seeds)")
    print(f"{'=' * 70}")
    print(f"\n  {'Model':28s} | {'Best Acc':>10s} | {'Final':>10s} | {'Params':>8s}")
    print(f"  {'─'*28}-+-{'─'*10}-+-{'─'*10}-+-{'─'*8}")

    for name, runs in all_results.items():
        mb = np.mean([r['best'] for r in runs])
        mf = np.mean([r['final'] for r in runs])
        p = runs[0]['params']
        print(f"  {name:28s} | {mb*100:8.2f}%  | {mf*100:8.2f}%  | {p:>8,}")

    # Deltas
    print(f"\n  Improvements:")
    pairs = [
        ('Top-K (K=2)', 'Golden MoE (orig)', 'Golden Zone effect'),
        ('Golden MoE (orig)', 'Golden MoE (improved)', 'Load balance'),
        ('PureField (orig)', 'PureField (improved)', 'Soft camp + adaptive alpha + norm'),
        ('Top-K (K=2)', 'PureField (improved)', 'Full improvement vs baseline'),
    ]
    for orig, imp, desc in pairs:
        do = np.mean([r['best'] for r in all_results[orig]])
        di = np.mean([r['best'] for r in all_results[imp]])
        print(f"    {desc:45s}: {(di-do)*100:+.2f}%")

    # Camp assignment
    print(f"\n  Soft Camp (PureField Improved, last run):")
    torch.manual_seed(seeds[-1])
    model = PureFieldImproved().to(device)
    train_eval(model, train_loader, test_loader, epochs=15, device=device)
    cp = torch.sigmoid(model.camp_logits).detach().cpu()
    for i, p in enumerate(cp):
        tag = "A" if p > 0.5 else "G"
        print(f"    E{i}: A={p:.3f} G={1-p:.3f} [{tag}]")

    # Alpha distribution
    print(f"\n  Input-dependent alpha distribution (sample):")
    model.eval()
    with torch.no_grad():
        sample_x = next(iter(test_loader))[0][:100].view(100, -1).to(device)
        alphas = torch.sigmoid(model.alpha_proj(sample_x)).cpu().squeeze()
        print(f"    mean={alphas.mean():.3f} std={alphas.std():.3f} "
              f"min={alphas.min():.3f} max={alphas.max():.3f}")

    print(f"\n{'=' * 70}")


if __name__ == '__main__':
    main()
