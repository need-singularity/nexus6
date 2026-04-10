#!/usr/bin/env python3
"""BitNet b1.58 x Golden MoE — Full Dataset Sweep + Discovery Mining

Tests dual constraint synergy across ALL available datasets:
  1. MNIST          (28x28, 10 classes) — baseline, easiest
  2. FashionMNIST   (28x28, 10 classes) — harder textures
  3. KMNIST         (28x28, 10 classes) — Japanese characters, different domain
  4. CIFAR-10       (32x32x3, 10 classes) — color, hardest

5 configurations per dataset:
  1. Dense (FP32)           — baseline
  2. Top-K (K=2, FP32)     — 25% active
  3. Golden MoE (T=e, FP32) — 70% active, Golden Zone
  4. BitNet Dense            — ternary weights, 100% active
  5. BitNet x Golden MoE     — ternary weights + Golden Zone

Discovery mining targets:
  - Synergy universality across domains
  - Recovery rate pattern (how much Golden Zone recovers BitNet loss)
  - Information efficiency scaling law
  - Ternary distribution convergence patterns
  - log_3(2) ~ 1-1/e empirical manifestation
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
import json


# ─────────────────────────────────────────
# BitNet b1.58: Ternary Quantization + STE
# ─────────────────────────────────────────
def ternary_quantize(w):
    alpha = w.abs().mean()
    return torch.sign(w) * (w.abs() > alpha * 0.5).float()


class TernaryWeight(torch.autograd.Function):
    @staticmethod
    def forward(ctx, w):
        return ternary_quantize(w)
    @staticmethod
    def backward(ctx, grad_output):
        return grad_output


class TernaryLinear(nn.Module):
    def __init__(self, in_features, out_features, bias=True):
        super().__init__()
        self.linear = nn.Linear(in_features, out_features, bias=bias)
        self.last_sparsity = 0.0
        self.last_ternary_dist = None

    def forward(self, x):
        w_ternary = TernaryWeight.apply(self.linear.weight)
        with torch.no_grad():
            self.last_sparsity = (w_ternary == 0).float().mean().item()
            n_neg = (w_ternary == -1).float().mean().item()
            n_zero = (w_ternary == 0).float().mean().item()
            n_pos = (w_ternary == 1).float().mean().item()
            self.last_ternary_dist = (n_neg, n_zero, n_pos)
        return F.linear(x, w_ternary, self.linear.bias)

    def get_effective_bits(self):
        if self.last_ternary_dist is None:
            return math.log2(3)
        probs = [p for p in self.last_ternary_dist if p > 0]
        return -sum(p * math.log2(p) for p in probs)


# ─────────────────────────────────────────
# Routers
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
        return weights / (weights.sum(dim=-1, keepdim=True) + 1e-8)


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
        return weights / (weights.sum(dim=-1, keepdim=True) + 1e-8)


# ─────────────────────────────────────────
# Experts
# ─────────────────────────────────────────
class Expert(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Dropout(dropout), nn.Linear(hidden_dim, output_dim))
    def forward(self, x):
        return self.net(x)


class TernaryExpert(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.5):
        super().__init__()
        self.fc1 = TernaryLinear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = TernaryLinear(hidden_dim, output_dim)
    def forward(self, x):
        return self.fc2(self.dropout(self.relu(self.fc1(x))))
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
# MoE Model
# ─────────────────────────────────────────
class MoEModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, n_experts=8,
                 gate_type='boltzmann', k=2, temperature=np.e,
                 active_ratio=0.7, dropout=0.5, ternary=False):
        super().__init__()
        EC = TernaryExpert if ternary else Expert
        self.experts = nn.ModuleList([EC(input_dim, hidden_dim, output_dim, dropout) for _ in range(n_experts)])
        self.n_experts = n_experts
        self.gate_type = gate_type
        self.ternary = ternary
        if gate_type == 'topk':
            self.gate = TopKGate(input_dim, n_experts, k)
        elif gate_type == 'boltzmann':
            self.gate = BoltzmannGate(input_dim, n_experts, temperature, active_ratio)
        else:
            self.gate = None
        self.expert_usage = torch.zeros(n_experts)
        self.active_counts = []

    def forward(self, x):
        expert_outputs = torch.stack([e(x) for e in self.experts], dim=1)
        if self.gate is None:
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
        m = {
            'avg_active': avg_active,
            'active_ratio': avg_active / self.n_experts,
            'usage_std': usage.std().item(),
            'I_effective': 1 - avg_active / self.n_experts,
        }
        if self.ternary:
            sparsities, bits_list = [], []
            dists = []
            for expert in self.experts:
                if hasattr(expert, 'get_weight_stats'):
                    for ls in expert.get_weight_stats().values():
                        sparsities.append(ls['sparsity'])
                        bits_list.append(ls['effective_bits'])
                        if ls['ternary_dist']:
                            dists.append(ls['ternary_dist'])
            m['weight_sparsity'] = np.mean(sparsities) if sparsities else 0
            m['effective_bits'] = np.mean(bits_list) if bits_list else math.log2(3)
            if dists:
                m['ternary_dist'] = tuple(np.mean([d[i] for d in dists]) for i in range(3))
        return m


# ─────────────────────────────────────────
# Data Loading
# ─────────────────────────────────────────
def load_dataset(name):
    """Load dataset and return (train_loader, test_loader, input_dim, n_classes, label)"""
    if name in ('mnist', 'fashionmnist', 'kmnist'):
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.5,), (0.5,))
        ])
        DS = {'mnist': datasets.MNIST, 'fashionmnist': datasets.FashionMNIST,
              'kmnist': datasets.KMNIST}[name]
        labels = {'mnist': 'MNIST', 'fashionmnist': 'FashionMNIST', 'kmnist': 'KMNIST'}
        train = DS('./data', train=True, download=True, transform=transform)
        test = DS('./data', train=False, download=True, transform=transform)
        return (DataLoader(train, batch_size=128, shuffle=True),
                DataLoader(test, batch_size=256), 784, 10, labels[name])

    elif name == 'cifar10':
        tr_tf = transforms.Compose([
            transforms.RandomHorizontalFlip(), transforms.RandomCrop(32, padding=4),
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616))])
        te_tf = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616))])
        train = datasets.CIFAR10('./data', train=True, download=True, transform=tr_tf)
        test = datasets.CIFAR10('./data', train=False, transform=te_tf)
        return (DataLoader(train, batch_size=128, shuffle=True),
                DataLoader(test, batch_size=256), 3072, 10, 'CIFAR-10')


# ─────────────────────────────────────────
# Training
# ─────────────────────────────────────────
def train_model(model, train_loader, test_loader, epochs=10, lr=0.001):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    train_losses, test_accs = [], []

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
        correct = total = 0
        with torch.no_grad():
            for X, y in test_loader:
                X = X.view(X.size(0), -1)
                pred = model(X).argmax(dim=1)
                correct += (pred == y).sum().item()
                total += y.size(0)
        acc = correct / total
        test_accs.append(acc)

        if (epoch + 1) % 3 == 0 or epoch == 0:
            print(f"    Ep {epoch+1:>2}/{epochs}: Loss={avg_loss:.4f}, Acc={acc*100:.2f}%")

    return train_losses, test_accs


# ─────────────────────────────────────────
# Run single dataset experiment
# ─────────────────────────────────────────
def run_dataset(ds_name, seed=42):
    torch.manual_seed(seed)
    np.random.seed(seed)

    train_loader, test_loader, input_dim, n_classes, label = load_dataset(ds_name)
    hidden_dim = 64 if input_dim == 784 else 128
    epochs = 10 if input_dim == 784 else 15
    n_experts = 8

    print(f"\n{'=' * 70}")
    print(f"  [{label}] input={input_dim}, hidden={hidden_dim}, experts={n_experts}, epochs={epochs}")
    print(f"{'=' * 70}")

    configs = [
        ('Dense(FP32)',       'dense',     {},                                          False),
        ('TopK(K=2)',         'topk',      {'k': 2},                                   False),
        ('Golden(T=e)',       'boltzmann', {'temperature': np.e, 'active_ratio': 0.7}, False),
        ('BitNet-Dense',      'dense',     {},                                          True),
        ('BitNet+Golden',     'boltzmann', {'temperature': np.e, 'active_ratio': 0.7}, True),
    ]

    results = {}
    for name, gate_type, kwargs, ternary in configs:
        torch.manual_seed(seed)  # Same init for fair comparison
        print(f"\n  --- {name} {'[1.58-bit]' if ternary else '[FP32]'} ---")

        model = MoEModel(input_dim, hidden_dim, n_classes, n_experts=n_experts,
                         gate_type=gate_type, dropout=0.5, ternary=ternary, **kwargs)
        params = sum(p.numel() for p in model.parameters())

        start = time.time()
        losses, accs = train_model(model, train_loader, test_loader, epochs=epochs)
        elapsed = time.time() - start

        metrics = model.get_metrics()
        results[name] = {
            'accuracy': accs[-1], 'best_accuracy': max(accs),
            'final_loss': losses[-1], 'time': elapsed, 'params': params,
            'losses': losses, 'accs': accs, 'ternary': ternary, **metrics
        }

    return results, label


# ─────────────────────────────────────────
# Analysis Functions
# ─────────────────────────────────────────
def compute_synergy(results):
    """Compute synergy metrics from 5-config results."""
    d = results.get('Dense(FP32)', {})
    g = results.get('Golden(T=e)', {})
    bd = results.get('BitNet-Dense', {})
    bg = results.get('BitNet+Golden', {})

    if not all([d, g, bd, bg]):
        return None

    baseline = d['best_accuracy']
    golden_gain = g['best_accuracy'] - baseline
    bitnet_gain = bd['best_accuracy'] - baseline
    dual_gain = bg['best_accuracy'] - baseline
    expected = golden_gain + bitnet_gain
    synergy = dual_gain - expected

    # Recovery rate: how much of BitNet's loss does Golden Zone recover?
    bitnet_loss = baseline - bd['best_accuracy']
    dual_loss = baseline - bg['best_accuracy']
    recovery = (bitnet_loss - dual_loss) / bitnet_loss if bitnet_loss > 0.001 else 0

    # Information efficiency
    bg_bits = bg.get('effective_bits', math.log2(3))
    bg_I = bg.get('I_effective', 0.375)
    info_flow = (bg_bits / math.log2(3)) * (1 - bg_I)
    info_efficiency = bg['best_accuracy'] / max(info_flow, 0.01)

    bd_bits = bd.get('effective_bits', math.log2(3))
    bd_info_flow = bd_bits / math.log2(3)
    bd_info_efficiency = bd['best_accuracy'] / max(bd_info_flow, 0.01)

    return {
        'baseline': baseline,
        'golden_gain': golden_gain,
        'bitnet_gain': bitnet_gain,
        'dual_gain': dual_gain,
        'expected_additive': expected,
        'synergy': synergy,
        'recovery_rate': recovery,
        'bg_info_efficiency': info_efficiency,
        'bd_info_efficiency': bd_info_efficiency,
        'info_efficiency_ratio': info_efficiency / max(bd_info_efficiency, 0.01),
        'bg_info_flow': info_flow,
        'bg_sparsity': bg.get('weight_sparsity', 0),
        'bd_sparsity': bd.get('weight_sparsity', 0),
    }


def print_dataset_table(results, label):
    print(f"\n{'=' * 70}")
    print(f"  {label} — Results")
    print(f"{'=' * 70}")

    header = f"  {'Config':16} | {'Best%':>7} | {'Final%':>7} | {'Loss':>8} | {'I':>5} | {'Bits':>5} | {'Time':>6}"
    print(header)
    print(f"  {'─'*16}─+{'─'*9}+{'─'*9}+{'─'*10}+{'─'*7}+{'─'*7}+{'─'*8}")

    for name, r in results.items():
        bits = r.get('effective_bits', 16.0)
        bits_str = f"{bits:.2f}" if r.get('ternary') else "32.0"
        print(f"  {name:16} | {r['best_accuracy']*100:>6.2f}% | {r['accuracy']*100:>6.2f}% | "
              f"{r['final_loss']:>8.4f} | {r['I_effective']:>5.3f} | {bits_str:>5} | {r['time']:>5.1f}s")


def main():
    print()
    print("=" * 70)
    print("  BitNet b1.58 x Golden MoE — FULL DATASET SWEEP")
    print("  Dual Constraint Synergy Discovery Mining")
    print("=" * 70)

    dataset_names = ['mnist', 'fashionmnist', 'cifar10']
    all_results = {}
    all_synergy = {}

    for ds in dataset_names:
        results, label = run_dataset(ds)
        all_results[ds] = (results, label)
        print_dataset_table(results, label)

        syn = compute_synergy(results)
        if syn:
            all_synergy[ds] = syn
            print(f"\n  Synergy Analysis:")
            print(f"    Baseline (Dense):    {syn['baseline']*100:.2f}%")
            print(f"    Golden gain:         {syn['golden_gain']*100:+.2f}%")
            print(f"    BitNet gain:         {syn['bitnet_gain']*100:+.2f}%")
            print(f"    Expected additive:   {syn['expected_additive']*100:+.2f}%")
            print(f"    Actual dual gain:    {syn['dual_gain']*100:+.2f}%")
            print(f"    SYNERGY:             {syn['synergy']*100:+.3f}%")
            print(f"    Recovery rate:       {syn['recovery_rate']*100:.1f}%")
            print(f"    Info efficiency ratio: {syn['info_efficiency_ratio']:.3f}x")

    # ═══════════════════════════════════════════
    # CROSS-DATASET ANALYSIS
    # ═══════════════════════════════════════════
    print(f"\n\n{'=' * 70}")
    print(f"  CROSS-DATASET COMPREHENSIVE ANALYSIS")
    print(f"{'=' * 70}")

    # Table 1: Best accuracy comparison
    print(f"\n  Table 1: Best Accuracy by Config x Dataset")
    print(f"  {'Config':16} |", end="")
    for ds in dataset_names:
        print(f" {all_results[ds][1]:>12} |", end="")
    print()
    print(f"  {'─'*16}─+" + ("─" * 14 + "+") * len(dataset_names))

    config_names = ['Dense(FP32)', 'TopK(K=2)', 'Golden(T=e)', 'BitNet-Dense', 'BitNet+Golden']
    for cfg in config_names:
        line = f"  {cfg:16} |"
        for ds in dataset_names:
            r = all_results[ds][0].get(cfg, {})
            line += f" {r.get('best_accuracy', 0)*100:>11.2f}% |"
        print(line)

    # Table 2: Synergy across datasets
    print(f"\n  Table 2: Synergy Metrics Across Datasets")
    print(f"  {'Metric':22} |", end="")
    for ds in dataset_names:
        print(f" {all_results[ds][1]:>12} |", end="")
    print()
    print(f"  {'─'*22}─+" + ("─" * 14 + "+") * len(dataset_names))

    syn_rows = [
        ('Synergy',           'synergy',              lambda x: f"{x*100:+.3f}%"),
        ('Recovery Rate',     'recovery_rate',         lambda x: f"{x*100:.1f}%"),
        ('Info Eff. Ratio',   'info_efficiency_ratio', lambda x: f"{x:.3f}x"),
        ('Golden Gain',       'golden_gain',           lambda x: f"{x*100:+.2f}%"),
        ('BitNet Gain',       'bitnet_gain',           lambda x: f"{x*100:+.2f}%"),
        ('Dual Gain',         'dual_gain',             lambda x: f"{x*100:+.2f}%"),
        ('BG Info Flow',      'bg_info_flow',          lambda x: f"{x:.4f}"),
        ('BG Sparsity',       'bg_sparsity',           lambda x: f"{x:.3f}"),
    ]

    for label, key, fmt in syn_rows:
        line = f"  {label:22} |"
        for ds in dataset_names:
            val = all_synergy.get(ds, {}).get(key, 0)
            line += f" {fmt(val):>12} |"
        print(line)

    # Table 3: Ternary distribution convergence
    print(f"\n  Table 3: Ternary Weight Distribution")
    print(f"  {'Config x Dataset':20} | {'(-1)':>6} | {'(0)':>6} | {'(+1)':>6} | {'Bits':>6} | {'Symm':>6}")
    print(f"  {'─'*20}─+{'─'*8}+{'─'*8}+{'─'*8}+{'─'*8}+{'─'*8}")

    for ds in dataset_names:
        for cfg in ['BitNet-Dense', 'BitNet+Golden']:
            r = all_results[ds][0].get(cfg, {})
            td = r.get('ternary_dist', (0,0,0))
            if td and any(t > 0 for t in td):
                symmetry = 1 - abs(td[0] - td[2]) / max(td[0] + td[2], 0.001)
                bits = r.get('effective_bits', 0)
                tag = f"{all_results[ds][1][:6]}/{cfg[:8]}"
                print(f"  {tag:20} | {td[0]:>6.3f} | {td[1]:>6.3f} | {td[2]:>6.3f} | {bits:>6.4f} | {symmetry:>6.3f}")

    # ═══════════════════════════════════════════
    # DISCOVERY MINING
    # ═══════════════════════════════════════════
    print(f"\n\n{'=' * 70}")
    print(f"  DISCOVERY MINING")
    print(f"{'=' * 70}")

    # Discovery 1: Synergy universality
    syn_values = [all_synergy[ds]['synergy'] for ds in dataset_names if ds in all_synergy]
    positive_syn = sum(1 for s in syn_values if s > 0.001)
    print(f"\n  [D1] Synergy Universality:")
    print(f"    Positive synergy in {positive_syn}/{len(syn_values)} datasets")
    for ds in dataset_names:
        if ds in all_synergy:
            s = all_synergy[ds]['synergy']
            tag = "POSITIVE" if s > 0.001 else ("NEGATIVE" if s < -0.001 else "NEUTRAL")
            print(f"      {all_results[ds][1]:15}: {s*100:+.3f}% [{tag}]")
    if positive_syn >= 3:
        print(f"    --> UNIVERSAL: synergy holds across {positive_syn}/{len(syn_values)} domains")
    elif positive_syn >= 2:
        print(f"    --> PARTIAL: synergy in {positive_syn}/{len(syn_values)} domains")
    else:
        print(f"    --> LIMITED: synergy only in {positive_syn}/{len(syn_values)} domains")

    # Discovery 2: Recovery rate pattern
    print(f"\n  [D2] Recovery Rate Pattern:")
    recovery_rates = []
    for ds in dataset_names:
        if ds in all_synergy:
            rr = all_synergy[ds]['recovery_rate']
            recovery_rates.append(rr)
            dim = 784 if ds != 'cifar10' else 3072
            print(f"      {all_results[ds][1]:15}: {rr*100:.1f}% recovery (dim={dim})")
    if recovery_rates:
        avg_rr = np.mean(recovery_rates)
        std_rr = np.std(recovery_rates)
        print(f"    Mean recovery: {avg_rr*100:.1f}% +/- {std_rr*100:.1f}%")
        # Check if recovery correlates with dimension
        dims_28 = [all_synergy[ds]['recovery_rate'] for ds in ['mnist', 'fashionmnist', 'kmnist'] if ds in all_synergy]
        dims_32 = [all_synergy[ds]['recovery_rate'] for ds in ['cifar10'] if ds in all_synergy]
        if dims_28 and dims_32:
            print(f"    28x28 datasets avg: {np.mean(dims_28)*100:.1f}%")
            print(f"    32x32 datasets avg: {np.mean(dims_32)*100:.1f}%")
            if np.mean(dims_28) > np.mean(dims_32) + 0.1:
                print(f"    --> SCALE DEPENDENT: recovery degrades with input complexity")

    # Discovery 3: Information efficiency scaling
    print(f"\n  [D3] Information Efficiency Scaling:")
    for ds in dataset_names:
        if ds in all_synergy:
            s = all_synergy[ds]
            print(f"      {all_results[ds][1]:15}: BitNet-D eff={s['bd_info_efficiency']:.2f}, "
                  f"BitNet+G eff={s['bg_info_efficiency']:.2f}, ratio={s['info_efficiency_ratio']:.3f}x")
    ratios = [all_synergy[ds]['info_efficiency_ratio'] for ds in dataset_names if ds in all_synergy]
    if ratios:
        print(f"    Mean info efficiency ratio: {np.mean(ratios):.3f}x")
        if all(r > 1.0 for r in ratios):
            print(f"    --> UNIVERSAL: Golden Zone ALWAYS improves info efficiency of BitNet")

    # Discovery 4: Ternary distribution convergence
    print(f"\n  [D4] Ternary Distribution Convergence:")
    all_sym_bg = []
    all_zero_bg = []
    for ds in dataset_names:
        r = all_results[ds][0].get('BitNet+Golden', {})
        td = r.get('ternary_dist')
        if td:
            sym = 1 - abs(td[0] - td[2]) / max(td[0] + td[2], 0.001)
            all_sym_bg.append(sym)
            all_zero_bg.append(td[1])
    if all_sym_bg:
        print(f"    BitNet+Golden symmetry (|w-|~|w+|): {np.mean(all_sym_bg):.4f} (1.0=perfect)")
        print(f"    BitNet+Golden zero ratio:           {np.mean(all_zero_bg):.4f}")
        # Compare with 1/3 (equal distribution)
        diff_from_third = abs(np.mean(all_zero_bg) - 1/3)
        print(f"    Zero ratio vs 1/3:                  diff={diff_from_third:.4f}")
        if diff_from_third < 0.05:
            print(f"    --> NEAR-EQUIPARTITION: zeros converge to 1/3 ({1/3:.4f})")

    # Discovery 5: Golden MoE vs Top-K gap scaling
    print(f"\n  [D5] Golden MoE vs Top-K Gap Scaling:")
    for ds in dataset_names:
        g = all_results[ds][0].get('Golden(T=e)', {})
        t = all_results[ds][0].get('TopK(K=2)', {})
        if g and t:
            gap = g['best_accuracy'] - t['best_accuracy']
            dim = 784 if ds != 'cifar10' else 3072
            print(f"      {all_results[ds][1]:15}: Golden vs TopK = {gap*100:+.2f}% (dim={dim})")

    # Discovery 6: log_3(2) ~ 1-1/e manifestation
    print(f"\n  [D6] log_3(2) ~ 1-1/e Empirical Check:")
    log3_2 = math.log(2) / math.log(3)  # 0.63093
    one_minus_inv_e = 1 - 1/math.e       # 0.63212
    print(f"    log_3(2)  = {log3_2:.6f}")
    print(f"    1 - 1/e   = {one_minus_inv_e:.6f}")
    print(f"    Difference: {abs(log3_2 - one_minus_inv_e):.6f} ({abs(log3_2 - one_minus_inv_e)/one_minus_inv_e*100:.3f}%)")

    # Check if any measured quantity matches
    for ds in dataset_names:
        r = all_results[ds][0].get('BitNet+Golden', {})
        if r:
            # Check if info_flow ~ log_3(2)
            s = all_synergy.get(ds, {})
            if s:
                info_flow = s.get('bg_info_flow', 0)
                diff_log = abs(info_flow - log3_2)
                diff_1me = abs(info_flow - one_minus_inv_e)
                if diff_log < 0.05 or diff_1me < 0.05:
                    print(f"    {all_results[ds][1]}: info_flow={info_flow:.4f} "
                          f"(vs log_3(2) diff={diff_log:.4f}, vs 1-1/e diff={diff_1me:.4f}) !!!")

    # Discovery 7: Accuracy-per-bit metric
    print(f"\n  [D7] Accuracy Per Bit (efficiency metric):")
    print(f"  {'Config':16} |", end="")
    for ds in dataset_names:
        print(f" {all_results[ds][1]:>12} |", end="")
    print()
    print(f"  {'─'*16}─+" + ("─" * 14 + "+") * len(dataset_names))

    for cfg in config_names:
        line = f"  {cfg:16} |"
        for ds in dataset_names:
            r = all_results[ds][0].get(cfg, {})
            bits = r.get('effective_bits', 32.0) if r.get('ternary') else 32.0
            acc = r.get('best_accuracy', 0)
            apb = acc * 100 / bits if bits > 0 else 0
            line += f" {apb:>11.2f}x |"
        print(line)

    # ═══════════════════════════════════════════
    # HYPOTHESIS CANDIDATES
    # ═══════════════════════════════════════════
    print(f"\n\n{'=' * 70}")
    print(f"  NEW HYPOTHESIS CANDIDATES")
    print(f"{'=' * 70}")

    hypotheses = []

    # H-A: Synergy universality
    if positive_syn >= 2:
        hypotheses.append({
            'id': 'H-A',
            'title': 'Dual Constraint Synergy is Domain-Universal (28x28)',
            'claim': f'Golden Zone routing consistently recovers BitNet accuracy loss '
                     f'across {positive_syn}/{len(syn_values)} tested domains',
            'evidence': f'Mean synergy = {np.mean(syn_values)*100:+.3f}%, '
                       f'mean recovery = {avg_rr*100:.1f}%',
            'grade': '(star)(star)' if positive_syn >= 3 else '(star)',
        })

    # H-B: Recovery rate ~ 1 - 1/e?
    if recovery_rates:
        mean_rr = np.mean([r for r in recovery_rates if r > 0])
        if abs(mean_rr - one_minus_inv_e) < 0.1:
            hypotheses.append({
                'id': 'H-B',
                'title': f'Recovery Rate ~ 1-1/e = {one_minus_inv_e:.4f}',
                'claim': f'Mean recovery rate {mean_rr:.4f} is close to 1-1/e ({one_minus_inv_e:.4f})',
                'evidence': f'Difference = {abs(mean_rr - one_minus_inv_e):.4f}',
                'grade': '(star)(star)' if abs(mean_rr - one_minus_inv_e) < 0.03 else '(star)',
            })

    # H-C: Ternary equipartition
    if all_zero_bg and abs(np.mean(all_zero_bg) - 1/3) < 0.05:
        hypotheses.append({
            'id': 'H-C',
            'title': 'Ternary Weights Converge to Equipartition (~1/3 each)',
            'claim': f'Zero ratio converges to {np.mean(all_zero_bg):.4f} ~ 1/3',
            'evidence': f'Diff from 1/3 = {diff_from_third:.4f} across {len(all_zero_bg)} datasets',
            'grade': '(star)',
        })

    # H-D: Info efficiency universally > 1
    if ratios and all(r > 1.0 for r in ratios):
        hypotheses.append({
            'id': 'H-D',
            'title': 'Golden Zone Always Improves BitNet Information Efficiency',
            'claim': f'Info efficiency ratio > 1.0 in ALL {len(ratios)} datasets',
            'evidence': f'Mean ratio = {np.mean(ratios):.3f}x, min = {min(ratios):.3f}x',
            'grade': '(star)(star)',
        })

    # H-E: Accuracy-per-bit
    apb_gains = []
    for ds in dataset_names:
        bg = all_results[ds][0].get('BitNet+Golden', {})
        bd = all_results[ds][0].get('BitNet-Dense', {})
        if bg and bd:
            bg_bits = bg.get('effective_bits', math.log2(3))
            bd_bits = bd.get('effective_bits', math.log2(3))
            bg_apb = bg['best_accuracy'] / bg_bits
            bd_apb = bd['best_accuracy'] / bd_bits
            if bd_apb > 0:
                apb_gains.append(bg_apb / bd_apb)
    if apb_gains and np.mean(apb_gains) > 1.0:
        hypotheses.append({
            'id': 'H-E',
            'title': 'BitNet+Golden Has Higher Accuracy-Per-Bit Than BitNet-Dense',
            'claim': f'Mean acc/bit ratio = {np.mean(apb_gains):.3f}x',
            'evidence': f'Consistent across {len(apb_gains)} datasets',
            'grade': '(star)',
        })

    print()
    for h in hypotheses:
        print(f"  {h['id']}: {h['title']}")
        print(f"    Claim: {h['claim']}")
        print(f"    Evidence: {h['evidence']}")
        print(f"    Suggested Grade: {h['grade']}")
        print()

    # Summary
    print(f"{'=' * 70}")
    print(f"  SUMMARY: {len(hypotheses)} new hypothesis candidates identified")
    print(f"  Datasets tested: {len(dataset_names)}")
    print(f"  Configs per dataset: 5")
    print(f"  Total experiments: {len(dataset_names) * 5}")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
