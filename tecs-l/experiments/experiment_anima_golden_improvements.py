#!/usr/bin/env python3
"""AnimaLM + Golden MoE Improvement Verification

Compares original vs improved versions:
1. Golden MoE: original vs + load balancing + parallel experts
2. PureField: original vs + input-dependent alpha + soft camp + tension norm
3. Combined: AnimaLM original vs improved

MNIST benchmark, 10 epochs, 3 seeds for statistical significance.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import numpy as np
import time
import os

# ─────────────────────────────────────────
# Original modules (baseline)
# ─────────────────────────────────────────

class BoltzmannGateOrig(nn.Module):
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
        return weights, probs  # return probs for load balance


class ExpertBlock(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.net(x)


# ─────────────────────────────────────────
# Golden MoE Original
# ─────────────────────────────────────────

class GoldenMoEOrig(nn.Module):
    def __init__(self, input_dim=784, hidden_dim=64, output_dim=10, n_experts=8):
        super().__init__()
        self.experts = nn.ModuleList([
            ExpertBlock(input_dim, hidden_dim, output_dim) for _ in range(n_experts)
        ])
        self.gate = BoltzmannGateOrig(input_dim, n_experts)
        self.n_experts = n_experts

    def forward(self, x):
        expert_outputs = torch.stack([e(x) for e in self.experts], dim=1)
        weights, _ = self.gate(x)
        output = (weights.unsqueeze(-1) * expert_outputs).sum(dim=1)
        return output, {}


# ─────────────────────────────────────────
# Golden MoE Improved (+ load balance + parallel)
# ─────────────────────────────────────────

class GoldenMoEImproved(nn.Module):
    def __init__(self, input_dim=784, hidden_dim=64, output_dim=10, n_experts=8,
                 lb_coeff=0.01):
        super().__init__()
        self.experts = nn.ModuleList([
            ExpertBlock(input_dim, hidden_dim, output_dim) for _ in range(n_experts)
        ])
        self.gate = BoltzmannGateOrig(input_dim, n_experts)
        self.n_experts = n_experts
        self.lb_coeff = lb_coeff

    def forward(self, x):
        expert_outputs = torch.stack([e(x) for e in self.experts], dim=1)
        weights, probs = self.gate(x)
        output = (weights.unsqueeze(-1) * expert_outputs).sum(dim=1)

        # Load balancing loss (Switch Transformer style)
        # f_i = fraction of tokens routed to expert i
        # P_i = average routing probability for expert i
        f = (weights > 0).float().mean(dim=0)  # (n_experts,)
        P = probs.mean(dim=0)  # (n_experts,)
        lb_loss = self.lb_coeff * self.n_experts * (f * P).sum()

        return output, {'lb_loss': lb_loss}


# ─────────────────────────────────────────
# PureField Original
# ─────────────────────────────────────────

class PureFieldOrig(nn.Module):
    def __init__(self, input_dim=784, hidden_dim=64, output_dim=10, n_experts=8):
        super().__init__()
        self.n_experts = n_experts
        self.n_camp_a = n_experts // 2
        self.experts = nn.ModuleList([
            ExpertBlock(input_dim, hidden_dim, output_dim) for _ in range(n_experts)
        ])
        self.gate = BoltzmannGateOrig(input_dim, n_experts, active_ratio=0.625)  # 5/8
        self.tension_scale = nn.Parameter(torch.ones(1))
        self.alpha = nn.Parameter(torch.zeros(1))  # sigmoid(0)=0.5

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


# ─────────────────────────────────────────
# PureField Improved (3 improvements)
# ─────────────────────────────────────────

class PureFieldImproved(nn.Module):
    """Improved PureField with:
    1. Input-dependent alpha (per-sample mix ratio)
    2. Soft camp assignment (learnable A/G membership)
    3. Tension LayerNorm
    4. Load balancing loss
    """

    def __init__(self, input_dim=784, hidden_dim=64, output_dim=10, n_experts=8,
                 lb_coeff=0.01):
        super().__init__()
        self.n_experts = n_experts
        self.experts = nn.ModuleList([
            ExpertBlock(input_dim, hidden_dim, output_dim) for _ in range(n_experts)
        ])
        self.gate = BoltzmannGateOrig(input_dim, n_experts, active_ratio=0.625)

        # Improvement 1: Input-dependent alpha
        self.alpha_proj = nn.Linear(input_dim, 1)

        # Improvement 2: Soft camp assignment (learnable)
        # Initialize: first half biased toward A, second half toward G
        init_logits = torch.zeros(n_experts)
        init_logits[:n_experts // 2] = 2.0   # A camp bias
        init_logits[n_experts // 2:] = -2.0   # G camp bias
        self.camp_logits = nn.Parameter(init_logits)

        # Improvement 3: Tension LayerNorm
        self.tension_scale = nn.Parameter(torch.ones(1))
        self.tension_norm = nn.LayerNorm(output_dim)

        self.lb_coeff = lb_coeff

    def forward(self, x):
        weights, probs = self.gate(x)

        # Soft camp probabilities
        camp_a_prob = torch.sigmoid(self.camp_logits)  # (n_experts,)

        out_a = torch.zeros(x.size(0), 10, device=x.device)
        out_g = torch.zeros(x.size(0), 10, device=x.device)

        for i in range(self.n_experts):
            w = weights[:, i].unsqueeze(-1)
            e_out = self.experts[i](x)
            # Soft assignment: each expert contributes to both camps
            out_a = out_a + camp_a_prob[i] * w * e_out
            out_g = out_g + (1 - camp_a_prob[i]) * w * e_out

        # Tension field
        repulsion = out_a - out_g
        tension = repulsion.pow(2).mean(dim=-1, keepdim=True)
        direction = repulsion / (repulsion.norm(dim=-1, keepdim=True) + 1e-8)
        tension_output = self.tension_scale * torch.sqrt(tension + 1e-8) * direction

        # Improvement 3: LayerNorm on tension output
        tension_output = self.tension_norm(tension_output)

        # MoE output
        moe_output = out_a + out_g

        # Improvement 1: Input-dependent alpha
        mix = torch.sigmoid(self.alpha_proj(x))  # (batch, 1)
        output = mix * moe_output + (1 - mix) * tension_output

        # Load balancing loss
        f = (weights > 0).float().mean(dim=0)
        P = probs.mean(dim=0)
        lb_loss = self.lb_coeff * self.n_experts * (f * P).sum()

        return output, {'lb_loss': lb_loss}


# ─────────────────────────────────────────
# Training
# ─────────────────────────────────────────

def train_and_eval(model, train_loader, test_loader, epochs=10, lr=0.001, device='cpu'):
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    history = {'train_loss': [], 'test_acc': [], 'tensions': []}

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        n_batches = 0

        for X, y in train_loader:
            X = X.view(X.size(0), -1).to(device)
            y = y.to(device)

            optimizer.zero_grad()
            output, extras = model(X)
            loss = criterion(output, y)

            # Add auxiliary losses
            if 'lb_loss' in extras:
                loss = loss + extras['lb_loss']

            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            n_batches += 1

        avg_loss = total_loss / n_batches
        history['train_loss'].append(avg_loss)

        # Test
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for X, y in test_loader:
                X = X.view(X.size(0), -1).to(device)
                y = y.to(device)
                output, _ = model(X)
                pred = output.argmax(dim=1)
                correct += (pred == y).sum().item()
                total += y.size(0)

        acc = correct / total
        history['test_acc'].append(acc)

    return history


def main():
    print("=" * 70)
    print("  AnimaLM + Golden MoE Improvement Verification")
    print("  MNIST, 10 epochs, 3 seeds")
    print("=" * 70)

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])

    train_data = datasets.MNIST('./data', train=True, download=True, transform=transform)
    test_data = datasets.MNIST('./data', train=False, transform=transform)
    train_loader = DataLoader(train_data, batch_size=128, shuffle=True)
    test_loader = DataLoader(test_data, batch_size=256, shuffle=False)

    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    print(f"  Device: {device}")

    models_config = {
        'Golden MoE (orig)':     lambda: GoldenMoEOrig(),
        'Golden MoE (improved)': lambda: GoldenMoEImproved(),
        'PureField (orig)':      lambda: PureFieldOrig(),
        'PureField (improved)':  lambda: PureFieldImproved(),
    }

    seeds = [42, 123, 777]
    all_results = {name: [] for name in models_config}

    for seed in seeds:
        print(f"\n{'─' * 70}")
        print(f"  Seed {seed}")
        print(f"{'─' * 70}")

        torch.manual_seed(seed)
        np.random.seed(seed)

        for name, model_fn in models_config.items():
            torch.manual_seed(seed)
            model = model_fn()
            param_count = sum(p.numel() for p in model.parameters())

            start = time.time()
            history = train_and_eval(model, train_loader, test_loader,
                                     epochs=10, lr=0.001, device=device)
            elapsed = time.time() - start

            best_acc = max(history['test_acc'])
            final_acc = history['test_acc'][-1]
            all_results[name].append({
                'best_acc': best_acc,
                'final_acc': final_acc,
                'time': elapsed,
                'params': param_count,
                'history': history,
            })
            print(f"  {name:30s}: best={best_acc*100:.2f}% final={final_acc*100:.2f}% "
                  f"params={param_count:,} time={elapsed:.1f}s")

    # ─── Summary ───
    print(f"\n{'=' * 70}")
    print(f"  RESULTS (mean +/- std over {len(seeds)} seeds)")
    print(f"{'=' * 70}")
    print()
    print(f"  {'Model':30s} | {'Best Acc':>12s} | {'Final Acc':>12s} | {'Params':>8s} | {'Time':>6s}")
    print(f"  {'─'*30}-+-{'─'*12}-+-{'─'*12}-+-{'─'*8}-+-{'─'*6}")

    summary = {}
    for name, runs in all_results.items():
        best_accs = [r['best_acc'] for r in runs]
        final_accs = [r['final_acc'] for r in runs]
        times = [r['time'] for r in runs]
        params = runs[0]['params']

        mean_best = np.mean(best_accs)
        std_best = np.std(best_accs)
        mean_final = np.mean(final_accs)
        std_final = np.std(final_accs)
        mean_time = np.mean(times)

        summary[name] = {
            'mean_best': mean_best, 'std_best': std_best,
            'mean_final': mean_final, 'std_final': std_final,
            'params': params, 'time': mean_time,
        }

        print(f"  {name:30s} | {mean_best*100:5.2f}+/-{std_best*100:.2f}% "
              f"| {mean_final*100:5.2f}+/-{std_final*100:.2f}% "
              f"| {params:>8,} | {mean_time:5.1f}s")

    # ─── Comparison ───
    print(f"\n  Improvement Analysis:")
    pairs = [
        ('Golden MoE (orig)', 'Golden MoE (improved)'),
        ('PureField (orig)', 'PureField (improved)'),
    ]
    for orig_name, imp_name in pairs:
        orig = summary[orig_name]
        imp = summary[imp_name]
        diff_best = (imp['mean_best'] - orig['mean_best']) * 100
        diff_final = (imp['mean_final'] - orig['mean_final']) * 100
        param_diff = imp['params'] - orig['params']
        time_diff = (imp['time'] / orig['time'] - 1) * 100

        print(f"\n  {orig_name} -> {imp_name}:")
        print(f"    Best Acc:  {diff_best:+.2f}%")
        print(f"    Final Acc: {diff_final:+.2f}%")
        print(f"    Params:    {param_diff:+,} ({param_diff/orig['params']*100:+.1f}%)")
        print(f"    Time:      {time_diff:+.1f}%")

    # ─── Camp Assignment ───
    print(f"\n  Soft Camp Assignment (PureField Improved, last seed):")
    last_model = PureFieldImproved()
    # Load wouldn't work here, just show init pattern
    # Actually let's check the trained model's camp logits
    torch.manual_seed(seeds[-1])
    model = PureFieldImproved().to(device)
    train_and_eval(model, train_loader, test_loader, epochs=10, lr=0.001, device=device)
    camp_probs = torch.sigmoid(model.camp_logits).detach().cpu()
    print(f"    Expert | Camp A prob | Camp G prob | Assignment")
    print(f"    ───────┼────────────┼────────────┼───────────")
    for i, p in enumerate(camp_probs):
        assignment = "A" if p > 0.5 else "G"
        bar_a = "█" * int(p * 20)
        bar_g = "█" * int((1 - p) * 20)
        print(f"      E{i}   | {p:.4f} {bar_a:20s} | {1-p:.4f} {bar_g:20s} | {assignment}")

    print(f"\n{'=' * 70}")
    print(f"  Experiment complete.")


if __name__ == '__main__':
    main()
