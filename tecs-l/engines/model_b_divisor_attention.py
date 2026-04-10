#!/usr/bin/env python3
"""Model B: Divisor Reciprocal Attention — Fixed weights {1/2, 1/3, 1/6} multi-head

Mathematical Basis:
  Proper divisor reciprocals of perfect number 6: {1/1, 1/2, 1/3, 1/6}
  When normalized: {1/2, 1/3, 1/6} (sum=1, natural probability distribution)

  Hypothesis 098: 6 is the unique perfect number with σ_{-1}(n)=2.
  Proper divisor reciprocal sum = 1 is a property unique to 6 among perfect numbers.

  Using this distribution as fixed weights for 3-head attention:
    Head 1 (1/2): coarse — large hidden_dim, captures overall outline
    Head 2 (1/3): medium — medium hidden_dim, captures patterns
    Head 3 (1/6): fine   — small hidden_dim, captures fine details

  Comparison target: softmax learned weights 3-head (same structure, only weights learned)

  Key question: How does nature's given {1/2, 1/3, 1/6} perform compared to
  learned weights?
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from model_utils import (
    DenseModel, load_mnist, train_and_evaluate, compare_results, count_params,
    DIVISOR_RECIPROCALS,
)

INPUT_DIM = 784
OUTPUT_DIM = 10
EPOCHS = 10


class DivisorAttentionModel(nn.Module):
    """3-head attention with fixed weights {1/2, 1/3, 1/6}.

    Each head has different hidden_dim:
      head 0 (w=1/2): hidden = base_dim     (coarse, widest representation)
      head 1 (w=1/3): hidden = base_dim*2//3 (medium)
      head 2 (w=1/6): hidden = base_dim//3   (fine, narrowest representation)
    """

    def __init__(self, input_dim, base_dim, output_dim, fixed_weights=None):
        super().__init__()
        self.fixed_weights = fixed_weights or DIVISOR_RECIPROCALS  # [1/2, 1/3, 1/6]
        self.n_heads = len(self.fixed_weights)

        # Hidden_dim for each head: coarse > medium > fine
        head_dims = [
            base_dim,           # coarse: 1/2 weight
            max(1, base_dim * 2 // 3),  # medium: 1/3 weight
            max(1, base_dim // 3),      # fine:   1/6 weight
        ]
        self.head_dims = head_dims

        self.heads = nn.ModuleList()
        for dim in head_dims:
            self.heads.append(nn.Sequential(
                nn.Linear(input_dim, dim),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(dim, output_dim),
            ))

        w = torch.tensor(self.fixed_weights, dtype=torch.float32)
        self.register_buffer('weights', w)

    def forward(self, x):
        outputs = torch.stack([head(x) for head in self.heads], dim=0)  # [3, B, out]
        w = self.weights.view(-1, 1, 1)  # [3, 1, 1]
        return (w * outputs).sum(dim=0)  # [B, out]


class LearnedAttentionModel(nn.Module):
    """3-head attention with learnable softmax weights (baseline)."""

    def __init__(self, input_dim, base_dim, output_dim):
        super().__init__()
        self.n_heads = 3

        head_dims = [
            base_dim,
            max(1, base_dim * 2 // 3),
            max(1, base_dim // 3),
        ]
        self.head_dims = head_dims

        self.heads = nn.ModuleList()
        for dim in head_dims:
            self.heads.append(nn.Sequential(
                nn.Linear(input_dim, dim),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(dim, output_dim),
            ))

        # Learnable weights (probability distribution after softmax)
        self.weight_logits = nn.Parameter(torch.zeros(3))

    def forward(self, x):
        outputs = torch.stack([head(x) for head in self.heads], dim=0)  # [3, B, out]
        w = F.softmax(self.weight_logits, dim=0).view(-1, 1, 1)  # [3, 1, 1]
        return (w * outputs).sum(dim=0)

    def get_learned_weights(self):
        return F.softmax(self.weight_logits, dim=0).detach().cpu().tolist()


def main():
    print("=" * 70)
    print("  Model B: Divisor Reciprocal Attention — Fixed {1/2, 1/3, 1/6} vs Learned weights")
    print("  Proper divisor reciprocals of perfect number 6: The unique natural probability distribution with sum=1")
    print("=" * 70)

    train_loader, test_loader = load_mnist()

    BASE_DIM = 128

    models = {
        'Divisor Attn (1/2,1/3,1/6)': DivisorAttentionModel(INPUT_DIM, BASE_DIM, OUTPUT_DIM),
        'Learned Attn (softmax 3h)': LearnedAttentionModel(INPUT_DIM, BASE_DIM, OUTPUT_DIM),
        'Dense baseline': DenseModel(INPUT_DIM, BASE_DIM, OUTPUT_DIM),
    }

    results = {}
    for name, model in models.items():
        params = count_params(model)
        print(f"\n── {name} (params={params:,}) ──")
        losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs=EPOCHS)
        results[name] = {
            'acc': accs[-1],
            'loss': losses[-1],
            'params': params,
        }

    compare_results(results)

    # ── Learned weight analysis ──
    learned_model = models['Learned Attn (softmax 3h)']
    learned_w = learned_model.get_learned_weights()

    print("\n── Weight Comparison ──")
    print(f"  {'Head':<8} {'Divisor Recip(fixed)':>14} {'Learned Weight':>14} {'Diff':>10}")
    print("  " + "-" * 50)
    target_w = DIVISOR_RECIPROCALS
    total_diff = 0
    for i, (tw, lw) in enumerate(zip(target_w, learned_w)):
        labels = ['coarse', 'medium', 'fine']
        diff = abs(tw - lw)
        total_diff += diff
        print(f"  {labels[i]:<8} {tw:>14.4f} {lw:>14.4f} {diff:>10.4f}")
    print(f"  {'Total Diff':<8} {'':>14} {'':>14} {total_diff:>10.4f}")

    print(f"\n  Fixed weights: {[f'{w:.4f}' for w in target_w]}")
    print(f"  Learned weights: {[f'{w:.4f}' for w in learned_w]}")

    if total_diff < 0.15:
        print("  → Learning converged to divisor reciprocal distribution! (diff < 15%)")
    elif total_diff < 0.3:
        print("  → Partial similarity observed (diff < 30%)")
    else:
        print("  → Learned weights converged to different distribution from divisor reciprocals")


if __name__ == '__main__':
    main()