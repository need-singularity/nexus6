#!/usr/bin/env python3
"""Model F: SL(2,Z) Modular Symmetry Constraint Network

Mathematical Foundation:
  SL(2,Z) is the modular group — the group of 2x2 integer matrices with determinant=1.
  Modular forms follow transformation laws under the action of this group,
  and are deeply connected to core objects in number theory (elliptic curves, Riemann zeta, etc.).

  Block sizes derived from perfect number 6:
    sigma(6) = 12  (sum of divisors)
    tau(6)   = 4   (number of divisors)
    lcm(tau(6), 6) = lcm(4, 6) = 12 = sigma(6)

  Block Symmetry Constraint:
    Partition weight matrices into 12x12 blocks and symmetrize each block:
      W_block = (W + W^T) / 2
    This discretizes the symmetric representation of SL(2,Z),
    reducing the weight space dimension by half for regularization effect.

  Expected Effects:
    - Symmetry constraint prevents overfitting (implicit regularization)
    - Block size 12 matches sigma(6), reflecting perfect number structure
    - Verify structural constraint superiority vs L2 regularization

  Verification:
    Compare Modular Constraint vs Standard Linear vs L2 regularization on MNIST
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import time

from model_utils import (
    SIGMA, TAU, H_TARGET,
    load_mnist, train_and_evaluate, compare_results, count_params,
    DenseModel,
)

# Block size = lcm(tau(6), 6) = lcm(4, 6) = 12 = sigma(6)
BLOCK_SIZE = SIGMA  # 12


# ─────────────────────────────────────────
# ModularConstraintLinear
# ─────────────────────────────────────────
class ModularConstraintLinear(nn.Module):
    """nn.Linear replacement: symmetrize weights by 12x12 blocks.

    Divide weight matrix (out_features x in_features) into 12x12 blocks,
    and apply W_block = (W + W^T) / 2 symmetry constraint to each block.
    Non-square blocks (edges) are used as-is without constraints.
    """

    def __init__(self, in_features, out_features, bias=True):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.weight = nn.Parameter(torch.empty(out_features, in_features))
        if bias:
            self.bias = nn.Parameter(torch.zeros(out_features))
        else:
            self.bias = None
        # Kaiming initialization
        nn.init.kaiming_uniform_(self.weight, a=math.sqrt(5))

    def _symmetrize_blocks(self, W):
        """Symmetrize weights by 12x12 blocks."""
        H, W_dim = W.shape
        result = W.clone()
        # Symmetrize only square blocks (12x12 units)
        n_row_blocks = H // BLOCK_SIZE
        n_col_blocks = W_dim // BLOCK_SIZE
        for i in range(n_row_blocks):
            for j in range(n_col_blocks):
                r_start = i * BLOCK_SIZE
                c_start = j * BLOCK_SIZE
                block = W[r_start:r_start + BLOCK_SIZE, c_start:c_start + BLOCK_SIZE]
                # Symmetrize: (W + W^T) / 2
                sym_block = (block + block.T) / 2
                result[r_start:r_start + BLOCK_SIZE, c_start:c_start + BLOCK_SIZE] = sym_block
        return result

    def forward(self, x):
        W_sym = self._symmetrize_blocks(self.weight)
        return F.linear(x, W_sym, self.bias)


# ─────────────────────────────────────────
# ModularConstraintNet
# ─────────────────────────────────────────
class ModularConstraintNet(nn.Module):
    """Network composed of ModularConstraintLinear layers.

    hidden_dim must be a multiple of 12 (for block symmetry application).
    """

    def __init__(self, input_dim=784, hidden_dim=48, output_dim=10, dropout=0.5):
        super().__init__()
        assert hidden_dim % BLOCK_SIZE == 0, \
            f"hidden_dim={hidden_dim} must be a multiple of {BLOCK_SIZE}."
        self.net = nn.Sequential(
            ModularConstraintLinear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            ModularConstraintLinear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.net(x)


# ─────────────────────────────────────────
# L2 Regularized Model (Comparison)
# ─────────────────────────────────────────
class L2RegularizedModel(nn.Module):
    """Standard Linear + L2 regularization (implemented via weight_decay)."""

    def __init__(self, input_dim=784, hidden_dim=48, output_dim=10, dropout=0.5):
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
# Benchmark
# ─────────────────────────────────────────
def main():
    print("=" * 70)
    print("  Model F: SL(2,Z) Modular Symmetry Constraint Network")
    print("=" * 70)
    print(f"\n  Block size = sigma(6) = {SIGMA}")
    print(f"  lcm(tau(6), 6) = lcm({TAU}, 6) = {BLOCK_SIZE}")
    print(f"  H_target = {H_TARGET:.6f}")
    print()

    # Data
    train_loader, test_loader = load_mnist()

    hidden_dim = 48  # Multiple of 12
    epochs = 10
    lr = 0.001
    results = {}

    # 1. Modular Constraint
    print("[1/3] ModularConstraintNet (hidden=48, block=12)")
    model_mc = ModularConstraintNet(784, hidden_dim, 10)
    t0 = time.time()
    losses_mc, accs_mc = train_and_evaluate(model_mc, train_loader, test_loader,
                                            epochs=epochs, lr=lr)
    elapsed_mc = time.time() - t0
    results['F: Modular Constraint'] = {
        'acc': accs_mc[-1], 'loss': losses_mc[-1],
        'params': count_params(model_mc), 'time': elapsed_mc,
    }

    # 2. Standard Dense (same size)
    print(f"\n[2/3] Standard Dense (hidden={hidden_dim})")
    model_std = DenseModel(784, hidden_dim, 10)
    t0 = time.time()
    losses_std, accs_std = train_and_evaluate(model_std, train_loader, test_loader,
                                              epochs=epochs, lr=lr)
    elapsed_std = time.time() - t0
    results['Baseline: Standard Dense'] = {
        'acc': accs_std[-1], 'loss': losses_std[-1],
        'params': count_params(model_std), 'time': elapsed_std,
    }

    # 3. L2 Regularization (weight_decay=0.01)
    print(f"\n[3/3] L2 Regularized (hidden={hidden_dim}, wd=0.01)")
    model_l2 = L2RegularizedModel(784, hidden_dim, 10)
    opt_l2 = torch.optim.Adam(model_l2.parameters(), lr=lr, weight_decay=0.01)
    t0 = time.time()
    losses_l2, accs_l2 = train_and_evaluate(model_l2, train_loader, test_loader,
                                            epochs=epochs, lr=lr, optimizer=opt_l2)
    elapsed_l2 = time.time() - t0
    results['Baseline: L2 Regularized'] = {
        'acc': accs_l2[-1], 'loss': losses_l2[-1],
        'params': count_params(model_l2), 'time': elapsed_l2,
    }

    # Compare results
    compare_results(results)

    # Symmetric block analysis
    print("\n--- Modular Symmetric Block Analysis ---")
    W = list(model_mc.net[0].parameters())[0].detach()
    H, W_dim = W.shape
    n_row = H // BLOCK_SIZE
    n_col = W_dim // BLOCK_SIZE
    print(f"  Weight size: {H} x {W_dim}")
    print(f"  Number of blocks: {n_row} x {n_col} = {n_row * n_col} square blocks")

    # Measure symmetry (asymmetry degree of original weights)
    asym_norms = []
    for i in range(n_row):
        for j in range(n_col):
            block = W[i*BLOCK_SIZE:(i+1)*BLOCK_SIZE, j*BLOCK_SIZE:(j+1)*BLOCK_SIZE]
            asym = (block - block.T).norm().item()
            asym_norms.append(asym)
    avg_asym = sum(asym_norms) / len(asym_norms) if asym_norms else 0
    print(f"  Average asymmetry norm (after training): {avg_asym:.6f}")
    print(f"  → Symmetrization is applied in forward, so actual output is fully symmetric")


if __name__ == '__main__':
    main()