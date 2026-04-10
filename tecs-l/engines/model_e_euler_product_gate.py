#!/usr/bin/env python3
"""Model E: Euler Product p=2,3 Truncated Gate (EulerProductGate)

Mathematical Basis:
  Euler product representation of Riemann zeta function:
    zeta(s) = prod_{p prime} 1/(1 - p^{-s})

  Truncating at p=2,3:
    zeta_{2,3}(s) = 1/(1-2^{-s}) * 1/(1-3^{-s})

  Discovery in hypothesis 092: Golden Zone model = zeta Euler product p=2,3 truncation
    G = D * P / I  <-->  zeta_{2,3} structure

  This truncation generates 6 states via product of two prime factors:
    p=2: {0, 1}      (binary classification, 2 states)
    p=3: {0, 1, 2}   (ternary classification, 3 states)
    Total: 2 x 3 = 6  (= perfect number 6 Experts)

  Gating Design — EulerProductGate:
    Stage 1 (p=2): sigmoid(W_2 @ x + b_2)
      -> Binary gate [alpha, 1-alpha]
      -> "Basic on/off decision"

    Stage 2 (p=3): softmax(W_3 @ x + b_3)
      -> Ternary distribution [beta_0, beta_1, beta_2]
      -> "Fine-grained routing"

    Final weights (6 Experts):
      w_{i,j} = gate_2[i] * gate_3[j]
      where i in {0,1}, j in {0,1,2}

    This precisely reflects the multiplicative structure of Euler product:
      zeta_{2,3} = (Stage 1) * (Stage 2)

  Expert layout:
    Expert 0: (0,0) = (1-alpha) * beta_0
    Expert 1: (0,1) = (1-alpha) * beta_1
    Expert 2: (0,2) = (1-alpha) * beta_2
    Expert 3: (1,0) = alpha * beta_0
    Expert 4: (1,1) = alpha * beta_1
    Expert 5: (1,2) = alpha * beta_2

  Key questions:
  Is 2-stage hierarchical gating more efficient than flat Top-K or Boltzmann?
  Does the multiplicative independence structure of Euler product promote Expert differentiation?
"""

import sys
import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model_utils import (
    load_mnist, train_and_evaluate, compare_results, count_params,
    Expert, BaseMoE, TopKGate, BoltzmannGate,
)


# ─────────────────────────────────────────
# Euler Product Constants
# ─────────────────────────────────────────
P_BINARY = 2   # First prime
P_TERNARY = 3  # Second prime
N_EXPERTS = P_BINARY * P_TERNARY  # = 6 (perfect number!)


# ─────────────────────────────────────────
# EulerProductGate
# ─────────────────────────────────────────
class EulerProductGate(nn.Module):
    """2-stage hierarchical gate based on Euler product p=2,3 truncation.

    Stage 1: sigmoid (binary, p=2) -> alpha in [0,1]
    Stage 2: softmax (ternary, p=3) -> beta in simplex(3)
    Final:   w[i,j] = gate_2[i] * gate_3[j], i=0..1, j=0..2
    """
    def __init__(self, input_dim, temperature=1.0):
        super().__init__()
        # p=2 binary gate
        self.linear_2 = nn.Linear(input_dim, 1)
        # p=3 ternary gate
        self.linear_3 = nn.Linear(input_dim, P_TERNARY)
        self.temperature = temperature

    def forward(self, x):
        # Stage 1: p=2 binary classification
        alpha = torch.sigmoid(self.linear_2(x))  # (batch, 1), [0,1]
        gate_2 = torch.cat([1 - alpha, alpha], dim=-1)  # (batch, 2)

        # Stage 2: p=3 ternary classification
        gate_3 = F.softmax(self.linear_3(x) / self.temperature, dim=-1)  # (batch, 3)

        # Euler product: generate 6 Expert weights via outer product
        # w[i,j] = gate_2[i] * gate_3[j]
        # gate_2: (batch, 2, 1), gate_3: (batch, 1, 3)
        weights = gate_2.unsqueeze(-1) * gate_3.unsqueeze(-2)  # (batch, 2, 3)
        weights = weights.reshape(x.size(0), N_EXPERTS)  # (batch, 6)

        return weights


# ─────────────────────────────────────────
# Euler Product MoE
# ─────────────────────────────────────────
class EulerProductMoE(nn.Module):
    """MoE model based on Euler product gate.

    Routes to 6 Experts hierarchically in 2x3 structure.
    """
    def __init__(self, input_dim=784, hidden_dim=128, output_dim=10, temperature=1.0):
        super().__init__()
        self.experts = nn.ModuleList([
            Expert(input_dim, hidden_dim, output_dim)
            for _ in range(N_EXPERTS)
        ])
        self.gate = EulerProductGate(input_dim, temperature=temperature)
        self.n_experts = N_EXPERTS

        # Metric tracking
        self.expert_usage = torch.zeros(N_EXPERTS)
        self.active_counts = []
        self.binary_entropy_history = []
        self.ternary_entropy_history = []

    def forward(self, x):
        weights = self.gate(x)  # (batch, 6)
        outputs = torch.stack([e(x) for e in self.experts], dim=1)  # (batch, 6, output_dim)
        result = (weights.unsqueeze(-1) * outputs).sum(dim=1)  # (batch, output_dim)

        with torch.no_grad():
            active = (weights > 0.01).float().sum(dim=-1).mean().item()
            self.active_counts.append(active)
            self.expert_usage += (weights > 0.01).float().sum(dim=0).mean(dim=0).cpu()

            # Analyze 2x3 structure
            w_2d = weights.reshape(-1, P_BINARY, P_TERNARY)
            binary_probs = w_2d.sum(dim=-1)  # (batch, 2)
            ternary_probs = w_2d.sum(dim=-2)  # (batch, 3)

            # Shannon entropy
            def entropy(p):
                p = p.clamp(min=1e-8)
                return -(p * p.log()).sum(dim=-1).mean().item()

            self.binary_entropy_history.append(entropy(binary_probs))
            self.ternary_entropy_history.append(entropy(ternary_probs))

        return result

    def get_metrics(self):
        usage = self.expert_usage / max(self.expert_usage.sum().item(), 1)
        avg_active = np.mean(self.active_counts) if self.active_counts else 0
        avg_h2 = np.mean(self.binary_entropy_history) if self.binary_entropy_history else 0
        avg_h3 = np.mean(self.ternary_entropy_history) if self.ternary_entropy_history else 0
        return {
            'avg_active': avg_active,
            'active_ratio': avg_active / self.n_experts,
            'I_effective': 1 - avg_active / self.n_experts,
            'usage_std': usage.std().item(),
            'binary_entropy': avg_h2,
            'ternary_entropy': avg_h3,
            'usage_per_expert': usage.tolist(),
        }

    def reset_metrics(self):
        self.expert_usage = torch.zeros(self.n_experts)
        self.active_counts = []
        self.binary_entropy_history = []
        self.ternary_entropy_history = []


# ─────────────────────────────────────────
# Benchmark
# ─────────────────────────────────────────
def main():
    print("=" * 70)
    print("  Model E: Euler Product p=2,3 Truncated Gate")
    print("=" * 70)

    # Explain Euler product structure
    print("\n[Euler Product Structure]")
    print(f"  zeta_{{2,3}}(s) = 1/(1-2^{{-s}}) * 1/(1-3^{{-s}})")
    print(f"  p=2 binary gate: sigmoid -> [alpha, 1-alpha]")
    print(f"  p=3 ternary gate: softmax -> [beta_0, beta_1, beta_2]")
    print(f"  Number of Experts: {P_BINARY} x {P_TERNARY} = {N_EXPERTS} (perfect number 6)")
    print(f"\n  Expert layout (2x3):")
    print(f"          j=0       j=1       j=2")
    print(f"  i=0  [(1-a)*b0  (1-a)*b1  (1-a)*b2]")
    print(f"  i=1  [  a*b0      a*b1      a*b2  ]")

    # Load data
    print("\n[Loading Data]")
    train_loader, test_loader = load_mnist()

    # Define models
    INPUT_DIM = 784
    HIDDEN_DIM = 128
    OUTPUT_DIM = 10
    EPOCHS = 10

    # Euler product MoE
    euler_model = EulerProductMoE(INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM)

    # Top-K(6, k=2) MoE (comparison)
    topk_gate = TopKGate(INPUT_DIM, N_EXPERTS, k=2)
    topk_model = BaseMoE(INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM, N_EXPERTS, topk_gate)

    # Boltzmann(6) MoE (comparison)
    boltz_gate = BoltzmannGate(INPUT_DIM, N_EXPERTS)
    boltz_model = BaseMoE(INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM, N_EXPERTS, boltz_gate)

    models = {
        'EulerProduct (2x3)': euler_model,
        'Top-K (6, k=2)': topk_model,
        'Boltzmann (6)': boltz_model,
    }

    results = {}
    for name, model in models.items():
        print(f"\n{'─' * 50}")
        print(f"  Training: {name}")
        print(f"  Parameters: {count_params(model):,}")
        print(f"{'─' * 50}")

        if hasattr(model, 'reset_metrics'):
            model.reset_metrics()

        losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs=EPOCHS)
        results[name] = {
            'acc': accs[-1],
            'loss': losses[-1],
            'params': count_params(model),
        }

        # Collect metrics
        if hasattr(model, 'get_metrics'):
            metrics = model.get_metrics()
            results[name].update(metrics)

    compare_results(results)

    # Analyze Euler product structure
    print("\n[Euler Product Gate Analysis]")
    euler_metrics = euler_model.get_metrics()
    print(f"  Average active Experts: {euler_metrics['avg_active']:.2f} / {N_EXPERTS}")
    print(f"  Active ratio:          {euler_metrics['active_ratio']:.4f}")
    print(f"  I_effective:           {euler_metrics['I_effective']:.4f}")
    print(f"  Binary entropy:        {euler_metrics['binary_entropy']:.4f}  (max={np.log(2):.4f})")
    print(f"  Ternary entropy:       {euler_metrics['ternary_entropy']:.4f}  (max={np.log(3):.4f})")

    # Expert usage (2x3 grid)
    usage = euler_metrics['usage_per_expert']
    print(f"\n  Expert usage (2x3 grid):")
    print(f"          j=0      j=1      j=2")
    for i in range(P_BINARY):
        row = [usage[i * P_TERNARY + j] for j in range(P_TERNARY)]
        print(f"  i={i}  [{' '.join(f'{v:7.4f}' for v in row)}]")

    # Top-K metrics
    print(f"\n[Top-K Gate Analysis]")
    topk_metrics = topk_model.get_metrics()
    print(f"  Average active Experts: {topk_metrics['avg_active']:.2f} / {N_EXPERTS}")
    print(f"  I_effective:           {topk_metrics['I_effective']:.4f}")

    # Boltzmann metrics
    print(f"\n[Boltzmann Gate Analysis]")
    boltz_metrics = boltz_model.get_metrics()
    print(f"  Average active Experts: {boltz_metrics['avg_active']:.2f} / {N_EXPERTS}")
    print(f"  I_effective:           {boltz_metrics['I_effective']:.4f}")

    # Conclusion
    print("\n[Conclusion]")
    best = max(results, key=lambda k: results[k]['acc'])
    print(f"  Best performance: {best} ({results[best]['acc']*100:.2f}%)")

    euler_acc = results['EulerProduct (2x3)']['acc']
    topk_acc = results['Top-K (6, k=2)']['acc']
    boltz_acc = results['Boltzmann (6)']['acc']
    print(f"  EulerProduct vs Top-K:     {(euler_acc - topk_acc)*100:+.2f}%p")
    print(f"  EulerProduct vs Boltzmann: {(euler_acc - boltz_acc)*100:+.2f}%p")

    if euler_metrics['I_effective'] > 0.2 and euler_metrics['I_effective'] < 0.5:
        print(f"  I_effective = {euler_metrics['I_effective']:.4f} -> Near Golden Zone!")
    else:
        print(f"  I_effective = {euler_metrics['I_effective']:.4f} -> Outside Golden Zone")


if __name__ == '__main__':
    main()