#!/usr/bin/env python3
"""Model D: Perfect number 6's divisor graph G(6) based topological network

Mathematical basis:
  From the divisor set {1, 2, 3, 6} of perfect number 6, defining edges by divisor relation (a|b),
  we obtain the divisor graph G(6).

  Vertices: {1, 2, 3, 6}  (tau(6) = 4)
  Edges:   1-2, 1-3, 1-6, 2-6, 3-6  (all pairs where a|b)
  Non-edges: 2-3  (2∤3, 3∤2)

  Adjacency matrix A:
        1  2  3  6
    1 [ 0  1  1  1 ]
    2 [ 1  0  0  1 ]
    3 [ 1  0  0  1 ]
    6 [ 1  1  1  0 ]

  Degree matrix D = diag(3, 2, 2, 3)
  Laplacian L = D - A:
        [ 3 -1 -1 -1 ]
        [-1  2  0 -1 ]
        [-1  0  2 -1 ]
        [-1 -1 -1  3 ]

  Eigenvalues: {0, 2, 4, 4}
  - 0: Connectivity (one component)
  - 2: Fiedler value (algebraic connectivity) = phi(6)
  - 4: Multiplicity 2 (symmetry of vertices 2,3 = 2 and 3 are prime factors of 6)

  Network design:
  - 4 layers (tau(6) = 4)
  - Use adjacency matrix A as mask → sparse connection
  - Use non-zero eigenvalues {2, 4, 4} as skip-connection weights
    (normalized: lambda_i / sum(lambda_i) = {0.2, 0.4, 0.4})
  - No connection between 2-3 → information separation between prime factor layers

  Key questions:
  Does the topological structure of G(6) provide structural advantages to network performance?
  Does the absence of edge 2-3 have a regularization effect?
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
    DenseModel, TAU,
)


# ─────────────────────────────────────────
# G(6) graph constants
# ─────────────────────────────────────────
# Adjacency matrix (vertex order: 1, 2, 3, 6)
ADJ_MATRIX = torch.tensor([
    [0, 1, 1, 1],
    [1, 0, 0, 1],
    [1, 0, 0, 1],
    [1, 1, 1, 0],
], dtype=torch.float32)

# Laplacian eigenvalues
LAPLACIAN_EIGENVALUES = [0, 2, 4, 4]  # Exact values
# Non-zero eigenvalues → skip-connection weights (normalized)
NONZERO_EIGENVALUES = [2, 4, 4]
SKIP_WEIGHTS = [v / sum(NONZERO_EIGENVALUES) for v in NONZERO_EIGENVALUES]
# = [0.2, 0.4, 0.4]

NUM_LAYERS = TAU  # = 4 (tau(6))


# ─────────────────────────────────────────
# G(6) Topology Layer
# ─────────────────────────────────────────
class G6Layer(nn.Module):
    """Layer implementing sparse connection with adjacency matrix mask.

    Divides dim dimension into NUM_LAYERS blocks,
    allowing connections only between blocks where (i,j)=1 in adjacency matrix.
    """
    def __init__(self, dim, dropout=0.3):
        super().__init__()
        self.dim = dim
        self.block_size = dim // NUM_LAYERS
        self.linear = nn.Linear(dim, dim)
        self.bn = nn.BatchNorm1d(dim)
        self.dropout = nn.Dropout(dropout)

        # Create mask based on adjacency matrix (+ self connections)
        mask = torch.zeros(dim, dim)
        identity = torch.eye(NUM_LAYERS)
        full_adj = ADJ_MATRIX + identity  # Include self connections
        for i in range(NUM_LAYERS):
            for j in range(NUM_LAYERS):
                if full_adj[i, j] > 0:
                    r_start = i * self.block_size
                    r_end = min((i + 1) * self.block_size, dim)
                    c_start = j * self.block_size
                    c_end = min((j + 1) * self.block_size, dim)
                    mask[r_start:r_end, c_start:c_end] = 1.0
        self.register_buffer('mask', mask)

    def forward(self, x):
        # Apply mask to weights
        with torch.no_grad():
            self.linear.weight.data *= self.mask
        out = self.linear(x)
        out = self.bn(out)
        out = F.relu(out)
        out = self.dropout(out)
        return out


# ─────────────────────────────────────────
# G(6) Topology Network
# ─────────────────────────────────────────
class G6TopologyNet(nn.Module):
    """Network following the divisor graph topology of perfect number 6.

    - 4 layers (tau(6) = 4)
    - Each layer has sparse connection with adjacency matrix mask
    - Skip-connection based on Laplacian eigenvalues
    """
    def __init__(self, input_dim=784, hidden_dim=256, output_dim=10, dropout=0.3):
        super().__init__()
        # Adjust hidden_dim to be multiple of NUM_LAYERS
        self.hidden_dim = (hidden_dim // NUM_LAYERS) * NUM_LAYERS

        self.input_proj = nn.Linear(input_dim, self.hidden_dim)
        self.input_bn = nn.BatchNorm1d(self.hidden_dim)

        # 4 G(6) layers
        self.layers = nn.ModuleList([
            G6Layer(self.hidden_dim, dropout=dropout)
            for _ in range(NUM_LAYERS)
        ])

        # skip-connection weights (based on Laplacian eigenvalues, learnable)
        self.skip_weights = nn.Parameter(
            torch.tensor(SKIP_WEIGHTS, dtype=torch.float32)
        )

        self.output_proj = nn.Linear(self.hidden_dim, output_dim)

    def forward(self, x):
        h = F.relu(self.input_bn(self.input_proj(x)))

        # Store layer outputs (for skip-connection)
        layer_outputs = [h]  # layer 0 = input projection

        for i, layer in enumerate(self.layers):
            h = layer(h)
            layer_outputs.append(h)

        # skip-connection: combine intermediate layer outputs with non-zero eigenvalue weights
        # layer_outputs[1] (layer 0 output) * w[0]=0.2
        # layer_outputs[2] (layer 1 output) * w[1]=0.4
        # layer_outputs[3] (layer 2 output) * w[2]=0.4
        # layer_outputs[4] (layer 3 output) = added to final output
        skip_weights = F.softmax(self.skip_weights, dim=0)
        skip_sum = torch.zeros_like(h)
        for i, w in enumerate(skip_weights):
            skip_sum = skip_sum + w * layer_outputs[i + 1]

        # Final output = last layer + skip sum
        final = layer_outputs[-1] + skip_sum

        return self.output_proj(final)


# ─────────────────────────────────────────
# ResNet-style Skip (for comparison)
# ─────────────────────────────────────────
class ResNetStyleNet(nn.Module):
    """ResNet-style network with uniform skip-connections (comparison baseline)."""
    def __init__(self, input_dim=784, hidden_dim=256, output_dim=10, dropout=0.3):
        super().__init__()
        self.hidden_dim = (hidden_dim // NUM_LAYERS) * NUM_LAYERS
        self.input_proj = nn.Linear(input_dim, self.hidden_dim)
        self.input_bn = nn.BatchNorm1d(self.hidden_dim)

        self.layers = nn.ModuleList()
        self.bns = nn.ModuleList()
        for _ in range(NUM_LAYERS):
            self.layers.append(nn.Linear(self.hidden_dim, self.hidden_dim))
            self.bns.append(nn.BatchNorm1d(self.hidden_dim))

        self.dropout = nn.Dropout(dropout)
        self.output_proj = nn.Linear(self.hidden_dim, output_dim)

    def forward(self, x):
        h = F.relu(self.input_bn(self.input_proj(x)))
        for layer, bn in zip(self.layers, self.bns):
            residual = h
            h = F.relu(bn(layer(h)))
            h = self.dropout(h)
            h = h + residual  # Uniform skip-connection (weight = 1)
        return self.output_proj(h)


# ─────────────────────────────────────────
# Benchmark
# ─────────────────────────────────────────
def main():
    print("=" * 70)
    print("  Model D: G(6) Divisor Graph Topological Network")
    print("=" * 70)

    # Print G(6) graph information
    print("\n[G(6) Divisor Graph Structure]")
    print(f"  Vertices: {{1, 2, 3, 6}} (tau(6) = {NUM_LAYERS})")
    print(f"  Edges:   1-2, 1-3, 1-6, 2-6, 3-6  (no 2-3)")
    print(f"  Laplacian eigenvalues: {LAPLACIAN_EIGENVALUES}")
    print(f"  Skip weights (normalized): {[round(w, 2) for w in SKIP_WEIGHTS]}")
    print(f"  Adjacency matrix:")
    labels = ['1', '2', '3', '6']
    print(f"      {' '.join(f'{l:>3}' for l in labels)}")
    for i, label in enumerate(labels):
        row = ADJ_MATRIX[i].int().tolist()
        print(f"  {label}  {' '.join(f'{v:>3}' for v in row)}")

    # Load data
    print("\n[Data Loading]")
    train_loader, test_loader = load_mnist()

    # Model definition
    INPUT_DIM = 784
    HIDDEN_DIM = 256
    OUTPUT_DIM = 10
    EPOCHS = 10

    models = {
        'G(6) Topology': G6TopologyNet(INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM),
        'Dense (baseline)': DenseModel(INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM),
        'ResNet-style Skip': ResNetStyleNet(INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM),
    }

    results = {}
    for name, model in models.items():
        print(f"\n{'─' * 50}")
        print(f"  Training: {name}")
        print(f"  Parameters: {count_params(model):,}")
        print(f"{'─' * 50}")

        losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs=EPOCHS)
        results[name] = {
            'acc': accs[-1],
            'loss': losses[-1],
            'params': count_params(model),
        }

    compare_results(results)

    # G(6) topology analysis
    print("\n[G(6) Topology Analysis]")
    g6_model = models['G(6) Topology']
    skip_w = F.softmax(g6_model.skip_weights, dim=0).detach().numpy()
    print(f"  Learned skip weights: {[round(float(w), 4) for w in skip_w]}")
    print(f"  Initial values (eigenvalue-based): {[round(w, 4) for w in SKIP_WEIGHTS]}")
    print(f"  Fiedler value (algebraic connectivity): {LAPLACIAN_EIGENVALUES[1]}")
    print(f"  Eigenvalue multiplicity: lambda=4 x2 (prime factors 2,3 symmetry)")

    # Mask sparsity analysis
    total_params_in_mask = 0
    active_params = 0
    for layer in g6_model.layers:
        m = layer.mask
        total_params_in_mask += m.numel()
        active_params += m.sum().item()
    sparsity = 1 - active_params / total_params_in_mask
    print(f"  Mask sparsity: {sparsity:.1%} (non-edge 2-3 blocked)")

    print("\n[Conclusion]")
    best = max(results, key=lambda k: results[k]['acc'])
    print(f"  Best performance: {best} ({results[best]['acc']*100:.2f}%)")
    if best == 'G(6) Topology':
        print("  -> G(6) topological structure provides performance advantage")
    else:
        g6_acc = results['G(6) Topology']['acc']
        best_acc = results[best]['acc']
        diff = (best_acc - g6_acc) * 100
        print(f"  -> Difference from G(6): {diff:+.2f}%p")


if __name__ == '__main__':
    main()