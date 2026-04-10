#!/usr/bin/env python3
"""BitNet b1.58 × Golden MoE — Dual Constraint Experiment

Tests whether combining ternary weights {-1, 0, 1} (BitNet b1.58)
with Golden Zone activation (Boltzmann T=e, 70%) creates synergy.

5 configurations:
  1. Dense (baseline)
  2. Top-K MoE (K=2, 25% active)
  3. Golden MoE (T=e, 70% active)
  4. BitNet Dense (ternary weights, 100% active)
  5. BitNet × Golden MoE (ternary weights + Golden Zone)

Information-theoretic analysis:
  - BitNet: 1.58 bits per weight (log2(3))
  - Golden Zone width: ln(4/3) ≈ 0.2877
  - Connection: log2(3) × ln(4/3) ≈ 0.4557 ≈ 1/2 - 1/e²?
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import numpy as np
import time
import math
import sys


# ─────────────────────────────────────────
# BitNet b1.58: Ternary Quantization + STE
# ─────────────────────────────────────────
def ternary_quantize(w):
    """Quantize weights to {-1, 0, 1} using absmean as threshold (BitNet b1.58 method)."""
    alpha = w.abs().mean()
    w_ternary = torch.sign(w) * (w.abs() > alpha * 0.5).float()
    return w_ternary


class TernaryWeight(torch.autograd.Function):
    """Straight-Through Estimator for ternary quantization."""
    @staticmethod
    def forward(ctx, w):
        return ternary_quantize(w)

    @staticmethod
    def backward(ctx, grad_output):
        # STE: pass gradients through unchanged
        return grad_output


class TernaryLinear(nn.Module):
    """Linear layer with ternary weights {-1, 0, 1} during forward pass.
    Full-precision weights maintained for gradient updates (STE)."""
    def __init__(self, in_features, out_features, bias=True):
        super().__init__()
        self.linear = nn.Linear(in_features, out_features, bias=bias)
        # Track quantization stats
        self.last_sparsity = 0.0
        self.last_ternary_dist = None

    def forward(self, x):
        # Quantize weights to {-1, 0, 1} with STE
        w_ternary = TernaryWeight.apply(self.linear.weight)

        # Track stats
        with torch.no_grad():
            self.last_sparsity = (w_ternary == 0).float().mean().item()
            n_neg = (w_ternary == -1).float().mean().item()
            n_zero = (w_ternary == 0).float().mean().item()
            n_pos = (w_ternary == 1).float().mean().item()
            self.last_ternary_dist = (n_neg, n_zero, n_pos)

        return F.linear(x, w_ternary, self.linear.bias)

    def get_effective_bits(self):
        """Calculate actual bits per weight based on ternary distribution."""
        if self.last_ternary_dist is None:
            return math.log2(3)
        probs = [p for p in self.last_ternary_dist if p > 0]
        entropy = -sum(p * math.log2(p) for p in probs)
        return entropy


# ─────────────────────────────────────────
# Routers (same as golden_moe_torch.py)
# ─────────────────────────────────────────
class TopKGate(nn.Module):
    def __init__(self, input_dim, n_experts, k=2):
        super().__init__()
        self.gate = nn.Linear(input_dim, n_experts)
        self.k = k

    def forward(self, x):
        scores = self.gate(x)
        topk_vals, topk_idx = scores.topk(self.k, dim=-1)
        mask = torch.zeros_like(scores)
        mask.scatter_(-1, topk_idx, 1.0)
        weights = F.softmax(scores, dim=-1) * mask
        weights = weights / (weights.sum(dim=-1, keepdim=True) + 1e-8)
        return weights


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
        return weights


# ─────────────────────────────────────────
# Expert (standard and ternary variants)
# ─────────────────────────────────────────
class Expert(nn.Module):
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


class TernaryExpert(nn.Module):
    """Expert with ternary {-1, 0, 1} weights (BitNet b1.58 style)."""
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.5):
        super().__init__()
        self.fc1 = TernaryLinear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = TernaryLinear(hidden_dim, output_dim)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)
        return x

    def get_weight_stats(self):
        stats = {}
        for name, layer in [('fc1', self.fc1), ('fc2', self.fc2)]:
            stats[name] = {
                'sparsity': layer.last_sparsity,
                'ternary_dist': layer.last_ternary_dist,
                'effective_bits': layer.get_effective_bits(),
            }
        return stats


# ─────────────────────────────────────────
# MoE Model (extended for ternary)
# ─────────────────────────────────────────
class MoEModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, n_experts=8,
                 gate_type='boltzmann', k=2, temperature=np.e,
                 active_ratio=0.7, dropout=0.5, ternary=False):
        super().__init__()
        ExpertClass = TernaryExpert if ternary else Expert
        self.experts = nn.ModuleList([
            ExpertClass(input_dim, hidden_dim, output_dim, dropout)
            for _ in range(n_experts)
        ])
        self.n_experts = n_experts
        self.gate_type = gate_type
        self.ternary = ternary

        if gate_type == 'topk':
            self.gate = TopKGate(input_dim, n_experts, k)
        elif gate_type == 'boltzmann':
            self.gate = BoltzmannGate(input_dim, n_experts, temperature, active_ratio)
        else:  # dense
            self.gate = None

        self.expert_usage = torch.zeros(n_experts)
        self.active_counts = []

    def forward(self, x):
        expert_outputs = torch.stack([e(x) for e in self.experts], dim=1)

        if self.gate is None:  # Dense
            output = expert_outputs.mean(dim=1)
            self.active_counts.append(self.n_experts)
        else:
            weights = self.gate(x)
            output = (weights.unsqueeze(-1) * expert_outputs).sum(dim=1)

            with torch.no_grad():
                active = (weights > 0).float().sum(dim=-1).mean().item()
                self.active_counts.append(active)
                self.expert_usage += (weights > 0).float().sum(dim=0).mean(dim=0).cpu()

        return output

    def get_metrics(self):
        usage = self.expert_usage / max(self.expert_usage.sum().item(), 1)
        avg_active = np.mean(self.active_counts) if self.active_counts else 0
        metrics = {
            'avg_active': avg_active,
            'active_ratio': avg_active / self.n_experts,
            'usage_std': usage.std().item(),
            'usage_dist': usage.numpy(),
            'I_effective': 1 - avg_active / self.n_experts,
        }

        # Ternary weight stats
        if self.ternary:
            all_sparsity = []
            all_bits = []
            for expert in self.experts:
                if hasattr(expert, 'get_weight_stats'):
                    stats = expert.get_weight_stats()
                    for layer_stats in stats.values():
                        all_sparsity.append(layer_stats['sparsity'])
                        all_bits.append(layer_stats['effective_bits'])
            metrics['weight_sparsity'] = np.mean(all_sparsity) if all_sparsity else 0
            metrics['effective_bits'] = np.mean(all_bits) if all_bits else math.log2(3)
            # Ternary distribution (averaged)
            dists = []
            for expert in self.experts:
                if hasattr(expert, 'get_weight_stats'):
                    for layer_stats in expert.get_weight_stats().values():
                        if layer_stats['ternary_dist']:
                            dists.append(layer_stats['ternary_dist'])
            if dists:
                avg_dist = tuple(np.mean([d[i] for d in dists]) for i in range(3))
                metrics['ternary_dist'] = avg_dist

        return metrics


# ─────────────────────────────────────────
# Training + Evaluation
# ─────────────────────────────────────────
def train_model(model, train_loader, test_loader, epochs=10, lr=0.001):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    train_losses = []
    test_accs = []

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            out = model(X)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        train_losses.append(avg_loss)

        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for X, y in test_loader:
                X = X.view(X.size(0), -1)
                out = model(X)
                pred = out.argmax(dim=1)
                correct += (pred == y).sum().item()
                total += y.size(0)

        acc = correct / total
        test_accs.append(acc)

        if (epoch + 1) % 2 == 0 or epoch == 0:
            print(f"    Epoch {epoch+1:>2}/{epochs}: Loss={avg_loss:.4f}, Acc={acc*100:.2f}%")

    return train_losses, test_accs


# ─────────────────────────────────────────
# Information-Theoretic Analysis
# ─────────────────────────────────────────
def information_analysis(results):
    """Analyze information-theoretic connections between BitNet and Golden Zone."""
    print(f"\n{'=' * 70}")
    print(f"  INFORMATION-THEORETIC ANALYSIS")
    print(f"{'=' * 70}")

    # Core constants
    log2_3 = math.log2(3)         # 1.58496 bits (ternary)
    ln_4_3 = math.log(4/3)        # 0.28768 (Golden Zone width)
    golden_center = 1/math.e      # 0.36788 (Golden Zone center)
    golden_upper = 0.5            # Riemann critical line

    print(f"\n  Core Constants:")
    print(f"    log2(3)       = {log2_3:.6f}  (bits per ternary weight)")
    print(f"    ln(4/3)       = {ln_4_3:.6f}  (Golden Zone width)")
    print(f"    1/e           = {golden_center:.6f}  (Golden Zone center)")
    print(f"    1/2           = {golden_upper:.6f}  (Golden Zone upper)")

    # Relationship exploration
    print(f"\n  Relationship Exploration:")

    # Product
    product = log2_3 * ln_4_3
    print(f"    log2(3) * ln(4/3) = {product:.6f}")
    print(f"      vs 1/2 - 1/e^2  = {0.5 - 1/math.e**2:.6f}  (diff: {abs(product - (0.5 - 1/math.e**2)):.6f})")
    print(f"      vs 1/ln(pi)     = {1/math.log(math.pi):.6f}  (diff: {abs(product - 1/math.log(math.pi)):.6f})")

    # Ratio
    ratio = log2_3 / ln_4_3
    print(f"    log2(3) / ln(4/3) = {ratio:.6f}")
    print(f"      vs e^(3/2)      = {math.e**1.5:.6f}  (diff: {abs(ratio - math.e**1.5):.6f})")
    print(f"      vs 2*e - pi     = {2*math.e - math.pi:.6f}  (diff: {abs(ratio - (2*math.e - math.pi)):.6f})")

    # Sum
    sumval = log2_3 + ln_4_3
    print(f"    log2(3) + ln(4/3) = {sumval:.6f}")
    print(f"      vs e/sqrt(2pi)  = {math.e/math.sqrt(2*math.pi):.6f}  (diff: {abs(sumval - math.e/math.sqrt(2*math.pi)):.6f})")

    # Information budget analysis
    print(f"\n  Information Budget Analysis:")
    print(f"    Standard FP16 weight: 16 bits")
    print(f"    Ternary weight:       {log2_3:.4f} bits ({log2_3/16*100:.1f}% of FP16)")
    print(f"    Information saved:    {16 - log2_3:.4f} bits/weight ({(16-log2_3)/16*100:.1f}%)")

    # Dual constraint information
    print(f"\n  Dual Constraint Information Analysis:")
    for name, r in results.items():
        I = r.get('I_effective', 0)
        bits = r.get('effective_bits', 16.0)
        if r.get('ternary_dist'):
            dist = r['ternary_dist']
            print(f"\n    [{name}]")
            print(f"      Ternary distribution: -1={dist[0]:.3f}, 0={dist[1]:.3f}, +1={dist[2]:.3f}")
            print(f"      Effective bits/weight: {bits:.4f}")
            print(f"      Inhibition (I):        {I:.4f}")
            print(f"      Weight sparsity:       {r.get('weight_sparsity', 0):.4f}")
            # Total information constraint
            weight_info_ratio = bits / math.log2(3)  # vs theoretical max
            activation_info_ratio = 1 - I  # active ratio
            total_constraint = weight_info_ratio * activation_info_ratio
            print(f"      Weight info ratio:     {weight_info_ratio:.4f}")
            print(f"      Activation info ratio: {activation_info_ratio:.4f}")
            print(f"      Total info flow:       {total_constraint:.4f}")

    # Connection to perfect number 6
    print(f"\n  Connection to n=6 Framework:")
    print(f"    sigma_{{-1}}(6) = 1/1 + 1/2 + 1/3 + 1/6 = 2")
    print(f"    Ternary states = 3 = sigma(6)/2 = 12/4")
    print(f"    log2(3) = {log2_3:.6f} = log2(sigma(6)/4) + 1")
    bits_per_zone = log2_3 * ln_4_3
    print(f"    log2(3) * ln(4/3) = {bits_per_zone:.6f} bits*nats")
    print(f"      (information per ternary weight per Golden Zone unit)")


# ─────────────────────────────────────────
# Main Experiment
# ─────────────────────────────────────────
def run_experiment(dataset='mnist'):
    if dataset == 'mnist':
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,))
        ])
        train_data = datasets.MNIST('./data', train=True, download=True, transform=transform)
        test_data = datasets.MNIST('./data', train=False, transform=transform)
        input_dim = 784
        hidden_dim = 64
        epochs = 10
        dataset_label = "MNIST"
    else:  # cifar10
        transform_train = transforms.Compose([
            transforms.RandomHorizontalFlip(),
            transforms.RandomCrop(32, padding=4),
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616))
        ])
        transform_test = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616))
        ])
        train_data = datasets.CIFAR10('./data', train=True, download=True, transform=transform_train)
        test_data = datasets.CIFAR10('./data', train=False, transform=transform_test)
        input_dim = 3072
        hidden_dim = 128
        epochs = 15
        dataset_label = "CIFAR-10"

    output_dim = 10
    n_experts = 8

    train_loader = DataLoader(train_data, batch_size=128, shuffle=True)
    test_loader = DataLoader(test_data, batch_size=256, shuffle=False)

    print(f"\n{'=' * 70}")
    print(f"  BitNet b1.58 x Golden MoE — {dataset_label}")
    print(f"  input={input_dim}, hidden={hidden_dim}, experts={n_experts}, epochs={epochs}")
    print(f"{'=' * 70}")

    configs = [
        ('Dense (FP32)',            'dense',     {},                                          False),
        ('Top-K (K=2)',             'topk',      {'k': 2},                                   False),
        ('Golden MoE (T=e)',        'boltzmann', {'temperature': np.e, 'active_ratio': 0.7}, False),
        ('BitNet Dense',            'dense',     {},                                          True),
        ('BitNet x Golden MoE',     'boltzmann', {'temperature': np.e, 'active_ratio': 0.7}, True),
    ]

    results = {}

    for name, gate_type, kwargs, ternary in configs:
        print(f"\n{'─' * 70}")
        print(f"  [{name}] {'(ternary weights)' if ternary else '(FP32 weights)'}")
        print(f"{'─' * 70}")

        model = MoEModel(
            input_dim, hidden_dim, output_dim,
            n_experts=n_experts, gate_type=gate_type,
            dropout=0.5, ternary=ternary, **kwargs
        )

        param_count = sum(p.numel() for p in model.parameters())
        print(f"  Parameters: {param_count:,}")

        start = time.time()
        losses, accs = train_model(model, train_loader, test_loader, epochs=epochs)
        elapsed = time.time() - start

        metrics = model.get_metrics()
        results[name] = {
            'accuracy': accs[-1],
            'best_accuracy': max(accs),
            'final_loss': losses[-1],
            'time': elapsed,
            'params': param_count,
            'losses': losses,
            'accs': accs,
            'ternary': ternary,
            **metrics,
        }

        if ternary:
            print(f"  Weight sparsity: {metrics.get('weight_sparsity', 0):.3f}")
            print(f"  Effective bits/weight: {metrics.get('effective_bits', 0):.4f}")
            if 'ternary_dist' in metrics:
                d = metrics['ternary_dist']
                print(f"  Ternary dist: -1={d[0]:.3f}, 0={d[1]:.3f}, +1={d[2]:.3f}")

    # ─── Comparison Table ───
    print(f"\n{'=' * 70}")
    print(f"  {dataset_label} — Overall Comparison")
    print(f"{'=' * 70}")

    header = f"  {'Metric':22} |"
    for name in results:
        header += f" {name[:16]:>16} |"
    print(header)
    print(f"  {'─'*22}─+" + ("─" * 18 + "+") * len(results))

    rows = [
        ('Final Accuracy',    'accuracy',       lambda x: f"{x*100:.2f}%"),
        ('Best Accuracy',     'best_accuracy',   lambda x: f"{x*100:.2f}%"),
        ('Final Loss',        'final_loss',      lambda x: f"{x:.4f}"),
        ('Training Time',     'time',            lambda x: f"{x:.1f}s"),
        ('Active Ratio',      'active_ratio',    lambda x: f"{x*100:.0f}%"),
        ('Effective I',       'I_effective',     lambda x: f"{x:.3f}"),
        ('Expert Balance s',  'usage_std',       lambda x: f"{x:.4f}"),
        ('Weight Sparsity',   'weight_sparsity', lambda x: f"{x:.3f}" if x else "N/A"),
        ('Bits/Weight',       'effective_bits',  lambda x: f"{x:.4f}" if x else "16.0"),
    ]

    for label, key, fmt in rows:
        line = f"  {label:22} |"
        for name, r in results.items():
            val = r.get(key, 0)
            line += f" {fmt(val):>16} |"
        print(line)

    # Golden Zone determination
    print(f"\n  Golden Zone Status:")
    for name, r in results.items():
        I = r['I_effective']
        if 0.213 <= I <= 0.500:
            zone = "Golden Zone"
        elif I < 0.213:
            zone = "Below"
        else:
            zone = "Outside"
        G = 0.5 * 0.85 / max(I, 0.01)
        ternary_tag = " [1.58-bit]" if r.get('ternary') else " [FP32]"
        print(f"    {name:25}: I={I:.3f} G={G:.2f} {zone}{ternary_tag}")

    # Key comparisons
    print(f"\n  Key Comparisons:")
    golden = results.get('Golden MoE (T=e)', {})
    topk = results.get('Top-K (K=2)', {})
    dense = results.get('Dense (FP32)', {})
    bitnet_dense = results.get('BitNet Dense', {})
    bitnet_golden = results.get('BitNet x Golden MoE', {})

    if golden and topk:
        diff = golden['best_accuracy'] - topk['best_accuracy']
        print(f"    Golden MoE vs Top-K:         {diff*100:+.2f}%")
    if bitnet_golden and bitnet_dense:
        diff = bitnet_golden['best_accuracy'] - bitnet_dense['best_accuracy']
        print(f"    BitNet Golden vs BitNet Dense:{diff*100:+.2f}%")
    if bitnet_golden and golden:
        diff = bitnet_golden['best_accuracy'] - golden['best_accuracy']
        print(f"    BitNet Golden vs FP32 Golden: {diff*100:+.2f}%")
    if bitnet_dense and dense:
        diff = bitnet_dense['best_accuracy'] - dense['best_accuracy']
        print(f"    BitNet Dense vs FP32 Dense:   {diff*100:+.2f}%")

    # SYNERGY TEST: Is dual constraint > sum of individual constraints?
    if all([dense, golden, bitnet_dense, bitnet_golden]):
        baseline = dense['best_accuracy']
        golden_gain = golden['best_accuracy'] - baseline
        bitnet_gain = bitnet_dense['best_accuracy'] - baseline
        dual_gain = bitnet_golden['best_accuracy'] - baseline
        expected_additive = golden_gain + bitnet_gain
        synergy = dual_gain - expected_additive

        print(f"\n  SYNERGY TEST (vs Dense baseline {baseline*100:.2f}%):")
        print(f"    Golden Zone gain:     {golden_gain*100:+.2f}%")
        print(f"    BitNet gain:          {bitnet_gain*100:+.2f}%")
        print(f"    Expected (additive):  {expected_additive*100:+.2f}%")
        print(f"    Actual dual gain:     {dual_gain*100:+.2f}%")
        print(f"    SYNERGY:              {synergy*100:+.2f}%")
        if synergy > 0.001:
            print(f"    --> POSITIVE SYNERGY: dual constraint > sum of parts")
        elif synergy < -0.001:
            print(f"    --> NEGATIVE SYNERGY: constraints interfere")
        else:
            print(f"    --> ADDITIVE: constraints are independent")

    # Accuracy trajectory
    print(f"\n  Accuracy Trajectory (Best per epoch):")
    max_epochs = max(len(r['accs']) for r in results.values())
    print(f"  {'Epoch':>5} |", end="")
    for name in results:
        print(f" {name[:14]:>14} |", end="")
    print()
    print(f"  {'─'*5}─+" + ("─" * 16 + "+") * len(results))
    for epoch in range(max_epochs):
        line = f"  {epoch+1:>5} |"
        for name, r in results.items():
            if epoch < len(r['accs']):
                line += f" {r['accs'][epoch]*100:>13.2f}% |"
            else:
                line += f" {'':>14} |"
        print(line)

    return results


def main():
    print()
    print("=" * 70)
    print("  BitNet b1.58 x Golden MoE — Dual Constraint Experiment")
    print("  'Less is More' x 'Less is More' = ?")
    print("=" * 70)

    mode = sys.argv[1] if len(sys.argv) > 1 else 'both'

    all_results = {}

    if mode in ('mnist', 'both'):
        all_results['mnist'] = run_experiment('mnist')

    if mode in ('cifar', 'both'):
        all_results['cifar'] = run_experiment('cifar10')

    # Cross-dataset scale analysis
    if 'mnist' in all_results and 'cifar' in all_results:
        print(f"\n{'=' * 70}")
        print(f"  SCALE ANALYSIS: MNIST vs CIFAR-10")
        print(f"{'=' * 70}")

        print(f"\n  {'Config':25} | {'MNIST Best':>12} | {'CIFAR Best':>12} | {'Scale Diff':>12}")
        print(f"  {'─'*25}─+{'─'*14}+{'─'*14}+{'─'*14}")

        for name in all_results['mnist']:
            if name in all_results['cifar']:
                m = all_results['mnist'][name]['best_accuracy']
                c = all_results['cifar'][name]['best_accuracy']
                diff = c - m
                print(f"  {name:25} | {m*100:>11.2f}% | {c*100:>11.2f}% | {diff*100:>+11.2f}%")

        # Scale synergy comparison
        print(f"\n  Scale Effect on Synergy:")
        for ds_name, ds_results in all_results.items():
            dense = ds_results.get('Dense (FP32)', {})
            golden = ds_results.get('Golden MoE (T=e)', {})
            bitnet_dense = ds_results.get('BitNet Dense', {})
            bitnet_golden = ds_results.get('BitNet x Golden MoE', {})

            if all([dense, golden, bitnet_dense, bitnet_golden]):
                baseline = dense['best_accuracy']
                golden_gain = golden['best_accuracy'] - baseline
                bitnet_gain = bitnet_dense['best_accuracy'] - baseline
                dual_gain = bitnet_golden['best_accuracy'] - baseline
                synergy = dual_gain - (golden_gain + bitnet_gain)
                print(f"    {ds_name.upper():8}: synergy = {synergy*100:+.3f}%")

    # Information analysis
    last_results = all_results.get('cifar', all_results.get('mnist', {}))
    if last_results:
        information_analysis(last_results)

    print(f"\n{'=' * 70}")
    print(f"  Experiment Complete")
    print(f"{'=' * 70}\n")


if __name__ == '__main__':
    main()
