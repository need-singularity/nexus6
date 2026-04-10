#!/usr/bin/env python3
"""Model G: Shannon Entropy Normalized MoE

Mathematical Basis:
  The divisor reciprocal distribution {1/2, 1/3, 1/6} of perfect number 6 forms a probability distribution with sum=1.
  Shannon entropy of this distribution:
    H_target = -(1/2)ln(1/2) - (1/3)ln(1/3) - (1/6)ln(1/6)
             = (1/2)ln(2) + (1/3)ln(3) + (1/6)ln(6)
             ≈ 0.8675

  Amazing relationship:
    e^(6 * H_target) = e^(6 * 0.8675) = e^(5.205)
                     ≈ 182.0 ... (actual calculation)

    More precisely:
    6 * H_target = 6 * [ln(2)/2 + ln(3)/3 + ln(6)/6]
                 = 3*ln(2) + 2*ln(3) + ln(6)
                 = 3*ln(2) + 2*ln(3) + ln(2) + ln(3)
                 = 4*ln(2) + 3*ln(3)
    e^(4*ln(2) + 3*ln(3)) = 2^4 * 3^3 = 16 * 27 = 432

    432 = sigma(6)^3 / tau(6) = 12^3 / 4 = 1728 / 4 = 432

  Therefore: e^(6 * H_target) = 432 = sigma(6)^3 / tau(6)
  From perfect number's divisor structure to entropy, connected in one equation.

  MoE gating design:
    For softmax gating weight distribution of 6 experts (perfect number 6),
    Add normalization loss to converge Shannon entropy to H_target:
      entropy_loss = (H(weights) - H_target)^2

    This makes gating converge to the "optimal non-uniform distribution" specified by
    perfect number structure, neither uniform (H=ln6) nor single expert focused (H=0).

  Validation:
    Compare Shannon MoE vs Top-K MoE vs Boltzmann MoE on MNIST
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import time

from model_utils import (
    SIGMA, TAU, H_TARGET, DIVISOR_RECIPROCALS,
    Expert, BaseMoE, TopKGate, BoltzmannGate,
    load_mnist, train_and_evaluate, compare_results, count_params,
)

N_EXPERTS = 6  # Perfect number 6


# ─────────────────────────────────────────
# ShannonEntropyGate
# ─────────────────────────────────────────
class ShannonEntropyGate(nn.Module):
    """Softmax gating + Shannon entropy normalization.

    Returns loss to match gating weight entropy to H_target.
    H_target = H({1/2, 1/3, 1/6}) ≈ 0.8675

    Returns:
        (weights, entropy_loss): Gating weights and entropy normalization loss
    """

    def __init__(self, input_dim, n_experts, h_target=H_TARGET):
        super().__init__()
        self.gate = nn.Linear(input_dim, n_experts)
        self.h_target = h_target
        self.n_experts = n_experts

    def forward(self, x):
        scores = self.gate(x)
        weights = F.softmax(scores, dim=-1)  # (batch, n_experts)

        # Shannon entropy: H = -sum(p * ln(p))
        # Clamp for numerical stability
        log_weights = torch.log(weights.clamp(min=1e-8))
        entropy = -(weights * log_weights).sum(dim=-1)  # (batch,)

        # Entropy normalization loss: batch average
        entropy_loss = ((entropy - self.h_target) ** 2).mean()

        return weights, entropy_loss


# ─────────────────────────────────────────
# ShannonEntropyMoE
# ─────────────────────────────────────────
class ShannonEntropyMoE(nn.Module):
    """Shannon entropy normalized MoE.

    6 experts, forward() returns (logits, aux_loss) tuple compatible
    with model_utils.train_and_evaluate's tuple output handling.
    """

    def __init__(self, input_dim=784, hidden_dim=64, output_dim=10,
                 n_experts=N_EXPERTS):
        super().__init__()
        self.experts = nn.ModuleList([
            Expert(input_dim, hidden_dim, output_dim)
            for _ in range(n_experts)
        ])
        self.gate = ShannonEntropyGate(input_dim, n_experts)
        self.n_experts = n_experts
        self.expert_usage = torch.zeros(n_experts)
        self.active_counts = []

    def forward(self, x):
        weights, entropy_loss = self.gate(x)
        outputs = torch.stack([e(x) for e in self.experts], dim=1)
        logits = (weights.unsqueeze(-1) * outputs).sum(dim=1)

        # Track metrics
        with torch.no_grad():
            active = (weights > 0.01).float().sum(dim=-1).mean().item()
            self.active_counts.append(active)
            self.expert_usage += (weights > 0.01).float().sum(dim=0).mean(dim=0).cpu()

        return logits, entropy_loss

    def get_metrics(self):
        usage = self.expert_usage / max(self.expert_usage.sum().item(), 1)
        avg_active = np.mean(self.active_counts) if self.active_counts else 0
        return {
            'avg_active': avg_active,
            'active_ratio': avg_active / self.n_experts if self.n_experts > 0 else 0,
            'I_effective': 1 - avg_active / self.n_experts if self.n_experts > 0 else 0,
            'usage_std': usage.std().item(),
            'usage_dist': usage.tolist(),
        }

    def reset_metrics(self):
        self.expert_usage = torch.zeros(self.n_experts)
        self.active_counts = []


# ─────────────────────────────────────────
# Benchmark
# ─────────────────────────────────────────
def main():
    print("=" * 70)
    print("  Model G: Shannon Entropy Normalized MoE")
    print("=" * 70)

    # Mathematical verification output
    h_target = H_TARGET
    exp_6h = math.exp(6 * h_target)
    sigma_cubed_over_tau = SIGMA ** 3 / TAU
    print(f"\n  H_target = H({{1/2, 1/3, 1/6}}) = {h_target:.6f}")
    print(f"  e^(6 * H_target) = {exp_6h:.1f}")
    print(f"  sigma(6)^3 / tau(6) = {SIGMA}^3 / {TAU} = {sigma_cubed_over_tau:.0f}")
    print(f"  Match: {abs(exp_6h - sigma_cubed_over_tau) < 0.01}")
    print(f"  Divisor reciprocal distribution: {DIVISOR_RECIPROCALS}")
    print()

    # Data
    train_loader, test_loader = load_mnist()

    hidden_dim = 64
    epochs = 10
    lr = 0.001
    aux_lambda = 0.1
    results = {}

    # 1. Shannon Entropy MoE
    print(f"[1/3] Shannon Entropy MoE (experts={N_EXPERTS}, aux_lambda={aux_lambda})")
    model_shannon = ShannonEntropyMoE(784, hidden_dim, 10, N_EXPERTS)
    t0 = time.time()
    losses_sh, accs_sh = train_and_evaluate(
        model_shannon, train_loader, test_loader,
        epochs=epochs, lr=lr, aux_lambda=aux_lambda,
    )
    elapsed_sh = time.time() - t0
    metrics_sh = model_shannon.get_metrics()
    results['G: Shannon Entropy MoE'] = {
        'acc': accs_sh[-1], 'loss': losses_sh[-1],
        'params': count_params(model_shannon), 'time': elapsed_sh,
    }

    # 2. Top-K MoE
    print(f"\n[2/3] Top-K MoE (experts={N_EXPERTS}, k=2)")
    gate_topk = TopKGate(784, N_EXPERTS, k=2)
    model_topk = BaseMoE(784, hidden_dim, 10, N_EXPERTS, gate_topk)
    t0 = time.time()
    losses_tk, accs_tk = train_and_evaluate(
        model_topk, train_loader, test_loader,
        epochs=epochs, lr=lr,
    )
    elapsed_tk = time.time() - t0
    metrics_tk = model_topk.get_metrics()
    results['Baseline: Top-K MoE'] = {
        'acc': accs_tk[-1], 'loss': losses_tk[-1],
        'params': count_params(model_topk), 'time': elapsed_tk,
    }

    # 3. Boltzmann MoE
    print(f"\n[3/3] Boltzmann MoE (experts={N_EXPERTS}, T=e)")
    gate_boltz = BoltzmannGate(784, N_EXPERTS, temperature=np.e)
    model_boltz = BaseMoE(784, hidden_dim, 10, N_EXPERTS, gate_boltz)
    t0 = time.time()
    losses_bz, accs_bz = train_and_evaluate(
        model_boltz, train_loader, test_loader,
        epochs=epochs, lr=lr,
    )
    elapsed_bz = time.time() - t0
    metrics_bz = model_boltz.get_metrics()
    results['Baseline: Boltzmann MoE'] = {
        'acc': accs_bz[-1], 'loss': losses_bz[-1],
        'params': count_params(model_boltz), 'time': elapsed_bz,
    }

    # Compare results
    compare_results(results)

    # Entropy and Expert analysis
    print("\n--- Shannon MoE Expert Analysis ---")
    print(f"  Average active Experts: {metrics_sh['avg_active']:.2f} / {N_EXPERTS}")
    print(f"  Active ratio: {metrics_sh['active_ratio']:.3f}")
    print(f"  I_effective: {metrics_sh['I_effective']:.3f}")
    print(f"  Usage distribution: {['%.3f' % u for u in metrics_sh['usage_dist']]}")

    # Final gating entropy measurement
    model_shannon.eval()
    sample_x, _ = next(iter(test_loader))
    sample_x = sample_x.view(sample_x.size(0), -1)
    with torch.no_grad():
        weights, ent_loss = model_shannon.gate(sample_x)
        log_w = torch.log(weights.clamp(min=1e-8))
        entropy = -(weights * log_w).sum(dim=-1).mean().item()
    print(f"\n  Final gating entropy: {entropy:.4f}")
    print(f"  Target H_target:      {H_TARGET:.4f}")
    print(f"  Error:                {abs(entropy - H_TARGET):.4f}")
    print(f"  Uniform entropy ln(6): {math.log(6):.4f}")

    print("\n--- Top-K MoE Expert Analysis ---")
    print(f"  Average active Experts: {metrics_tk['avg_active']:.2f} / {N_EXPERTS}")
    print(f"  I_effective: {metrics_tk['I_effective']:.3f}")

    print("\n--- Boltzmann MoE Expert Analysis ---")
    print(f"  Average active Experts: {metrics_bz['avg_active']:.2f} / {N_EXPERTS}")
    print(f"  I_effective: {metrics_bz['I_effective']:.3f}")


if __name__ == '__main__':
    main()