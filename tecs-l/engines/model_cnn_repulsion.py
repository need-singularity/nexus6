#!/usr/bin/env python3
"""CNN-based Repulsion Field — CIFAR-10

Building repulsion field architecture on top of CNN feature extraction
to overcome the limitations of MLP (flatten 3072-dim).

Key question: Is the repulsion field advantage observed in MLP maintained in CNN?
              Do {1/2, 1/3, 1/6} weights still win in CNN?

Architecture:
  SharedCNNBackbone (3x32x32 → 128-dim)
       │
       ├─→ CNN+Dense (baseline)
       ├─→ CNN+TopK MoE
       ├─→ CNN+RepulsionField (2-pole: A vs G)
       ├─→ CNN+RepulsionQuad (4-pole: A|G × E|F)
       └─→ CNN+MetaFixed {1/2, 1/3, 1/6}

MLP baseline best: 53.52% (benchmark_cifar.py)
CNN target: 70%+
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import time

from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from model_utils import (
    Expert, TopKGate, BaseMoE,
    compare_results, count_params,
    SIGMA, TAU, PHI, DIVISOR_RECIPROCALS, H_TARGET
)


# ─────────────────────────────────────────
# Shared CNN Backbone
# ─────────────────────────────────────────

class SharedCNNBackbone(nn.Module):
    """Shared CNN feature extractor: 3x32x32 → 128-dim.

    All CNN models share this backbone.
    Conv layers extract features while preserving spatial structure,
    and MLP heads classify using various strategies on top of those features.
    """
    def __init__(self, feature_dim=128):
        super().__init__()
        self.feature_dim = feature_dim
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),           # 32x16x16
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),           # 64x8x8
            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2),           # 128x4x4
            nn.AdaptiveAvgPool2d(1),   # 128x1x1
            nn.Flatten(),              # 128
        )

    def forward(self, x):
        return self.features(x)  # (batch, 128)


# ─────────────────────────────────────────
# MLP Head (Expert for CNN features)
# ─────────────────────────────────────────

class MLPHead(nn.Module):
    """MLP classification head on top of CNN features."""
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.3):
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
# 1. CNN + Dense (baseline)
# ─────────────────────────────────────────

class CNNDense(nn.Module):
    """CNN backbone + single dense head. Baseline."""
    def __init__(self, feature_dim=128, hidden_dim=128, output_dim=10):
        super().__init__()
        self.backbone = SharedCNNBackbone(feature_dim)
        self.head = MLPHead(feature_dim, hidden_dim, output_dim)

    def forward(self, x):
        feat = self.backbone(x)
        return self.head(feat)


# ─────────────────────────────────────────
# 2. CNN + TopK MoE
# ─────────────────────────────────────────

class CNNTopKMoE(nn.Module):
    """CNN backbone + Top-K MoE head."""
    def __init__(self, feature_dim=128, hidden_dim=64, output_dim=10,
                 n_experts=8, k=2):
        super().__init__()
        self.backbone = SharedCNNBackbone(feature_dim)
        self.experts = nn.ModuleList([
            MLPHead(feature_dim, hidden_dim, output_dim, dropout=0.3)
            for _ in range(n_experts)
        ])
        self.gate = TopKGate(feature_dim, n_experts, k)
        self.n_experts = n_experts

    def forward(self, x):
        feat = self.backbone(x)
        weights = self.gate(feat)
        outputs = torch.stack([e(feat) for e in self.experts], dim=1)
        return (weights.unsqueeze(-1) * outputs).sum(dim=1)


# ─────────────────────────────────────────
# 3. CNN + RepulsionField (2-pole)
# ─────────────────────────────────────────

class CNNRepulsionField(nn.Module):
    """CNN backbone + Repulsion Field (2-pole: A vs G).

    Shared CNN → 128-dim features
    Engine+ (MLP head A): Generation (excitation)
    Engine- (MLP head G): Calibration (inhibition)
    Output = equilibrium + tension × direction

    High tension = engines repelling strongly = difficult input
    Low tension = engines in agreement = easy input
    """
    def __init__(self, feature_dim=128, hidden_dim=64, output_dim=10):
        super().__init__()
        self.backbone = SharedCNNBackbone(feature_dim)

        # Two poles: same structure, different initialization → repulsion
        self.pole_plus = MLPHead(feature_dim, hidden_dim, output_dim, dropout=0.3)
        self.pole_minus = MLPHead(feature_dim, hidden_dim, output_dim, dropout=0.3)

        # Repulsion → output direction
        self.field_transform = nn.Sequential(
            nn.Linear(output_dim, output_dim),
            nn.Tanh(),
        )

        # Tension scale (learnable, initial value 1/3 = meta fixed point)
        self.tension_scale = nn.Parameter(torch.tensor(1/3))

        self.tension_magnitude = 0.0

    def forward(self, x):
        feat = self.backbone(x)

        out_plus = self.pole_plus(feat)
        out_minus = self.pole_minus(feat)

        # Repulsion = difference between the two
        repulsion = out_plus - out_minus
        tension = (repulsion ** 2).sum(dim=-1, keepdim=True)

        # Equilibrium + tension×direction
        equilibrium = (out_plus + out_minus) / 2
        field_direction = self.field_transform(repulsion)
        output = equilibrium + self.tension_scale * torch.sqrt(tension + 1e-8) * field_direction

        with torch.no_grad():
            self.tension_magnitude = tension.mean().item()

        return output


# ─────────────────────────────────────────
# 4. CNN + RepulsionQuad (4-pole)
# ─────────────────────────────────────────

class CNNRepulsionQuad(nn.Module):
    """CNN backbone + 4-pole repulsion field.

    Axis 1: Content (A vs G) — Generation ←repulsion→ Calibration
    Axis 2: Structure (E vs F) — Exploration ←repulsion→ Constraint

      A ←────→ G
      ↑         ↑
      │  field  │
      │ center  │
      ↓         ↓
      E ←────→ F
    """
    def __init__(self, feature_dim=128, hidden_dim=64, output_dim=10):
        super().__init__()
        self.backbone = SharedCNNBackbone(feature_dim)

        # 4 poles
        self.head_a = MLPHead(feature_dim, hidden_dim, output_dim, dropout=0.3)
        self.head_e = MLPHead(feature_dim, hidden_dim, output_dim, dropout=0.3)
        self.head_g = MLPHead(feature_dim, hidden_dim, output_dim, dropout=0.3)
        self.head_f = MLPHead(feature_dim, hidden_dim, output_dim, dropout=0.3)

        # 2-axis repulsion → output direction
        self.field_transform = nn.Sequential(
            nn.Linear(output_dim * 2, output_dim),
            nn.Tanh(),
        )
        self.tension_scale = nn.Parameter(torch.tensor(1/3))

        self.tension_content = 0.0
        self.tension_structure = 0.0

    def forward(self, x):
        feat = self.backbone(x)

        out_a = self.head_a(feat)
        out_e = self.head_e(feat)
        out_g = self.head_g(feat)
        out_f = self.head_f(feat)

        # Axis 1: Content repulsion (A vs G)
        repulsion_content = out_a - out_g
        # Axis 2: Structure repulsion (E vs F)
        repulsion_structure = out_e - out_f

        t_content = (repulsion_content ** 2).sum(dim=-1, keepdim=True)
        t_structure = (repulsion_structure ** 2).sum(dim=-1, keepdim=True)

        # 4-pole equilibrium
        equilibrium = (out_a + out_e + out_g + out_f) / 4

        # Combine 2-axis repulsion
        combined_repulsion = torch.cat([repulsion_content, repulsion_structure], dim=-1)
        field_direction = self.field_transform(combined_repulsion)

        # Total tension = geometric mean
        total_tension = torch.sqrt((t_content * t_structure) + 1e-8)
        output = equilibrium + self.tension_scale * torch.sqrt(total_tension + 1e-8) * field_direction

        with torch.no_grad():
            self.tension_content = t_content.mean().item()
            self.tension_structure = t_structure.mean().item()

        return output


# ─────────────────────────────────────────
# 5. CNN + MetaFixed {1/2, 1/3, 1/6}
# ─────────────────────────────────────────

class CNNMetaFixed(nn.Module):
    """CNN backbone + {1/2, 1/3, 1/6} weighted combination.

    Combines 3 MLP heads with divisor reciprocals of perfect number 6.
    Learnable weights, but initialized to {1/2, 1/3, 1/6}.
    """
    def __init__(self, feature_dim=128, hidden_dim=64, output_dim=10):
        super().__init__()
        self.backbone = SharedCNNBackbone(feature_dim)

        # 3 heads
        self.head_a = MLPHead(feature_dim, hidden_dim, output_dim, dropout=0.3)
        self.head_b = MLPHead(feature_dim, hidden_dim, output_dim, dropout=0.3)
        self.head_c = MLPHead(feature_dim, hidden_dim, output_dim, dropout=0.3)

        # Divisor reciprocal weights (learnable)
        init_weights = torch.tensor(DIVISOR_RECIPROCALS, dtype=torch.float)  # [1/2, 1/3, 1/6]
        self.weights = nn.Parameter(init_weights)

    def forward(self, x):
        feat = self.backbone(x)

        out_a = self.head_a(feat)
        out_b = self.head_b(feat)
        out_c = self.head_c(feat)

        # Normalize with softmax (ensures sum=1)
        w = F.softmax(self.weights, dim=0)
        output = w[0] * out_a + w[1] * out_b + w[2] * out_c

        return output

    def get_weights(self):
        """Return current learned weights."""
        with torch.no_grad():
            return F.softmax(self.weights, dim=0).cpu().numpy()


# ─────────────────────────────────────────
# CIFAR-10 data loader (with augmentation)
# ─────────────────────────────────────────

def load_cifar10_augmented(batch_size=128, data_dir='data'):
    """CIFAR-10 with proper data augmentation."""
    train_transform = transforms.Compose([
        transforms.RandomHorizontalFlip(),
        transforms.RandomCrop(32, padding=4),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])
    test_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])
    train_ds = datasets.CIFAR10(data_dir, train=True, download=True, transform=train_transform)
    test_ds = datasets.CIFAR10(data_dir, train=False, transform=test_transform)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=2)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=2)
    return train_loader, test_loader


# ─────────────────────────────────────────
# Training loop (for CNN — no flatten)
# ─────────────────────────────────────────

def train_cnn(model, train_loader, test_loader, epochs=30, lr=0.001, verbose=True):
    """Train CNN model. flatten=False."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    train_losses = []
    test_accs = []

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for X, y in train_loader:
            optimizer.zero_grad()
            out = model(X)

            if isinstance(out, tuple):
                logits, aux = out
                loss = criterion(logits, y) + 0.01 * aux
            else:
                logits = out
                loss = criterion(logits, y)

            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        train_losses.append(avg_loss)

        model.eval()
        correct = total = 0
        with torch.no_grad():
            for X, y in test_loader:
                out = model(X)
                if isinstance(out, tuple):
                    out = out[0]
                correct += (out.argmax(1) == y).sum().item()
                total += y.size(0)
        acc = correct / total
        test_accs.append(acc)

        if verbose and ((epoch + 1) % 5 == 0 or epoch == 0):
            print(f"    Epoch {epoch+1:>2}/{epochs}: Loss={avg_loss:.4f}, Acc={acc*100:.1f}%")

    return train_losses, test_accs


# ─────────────────────────────────────────
# Benchmark
# ─────────────────────────────────────────

# MLP baseline results (benchmark_cifar.py, flatten 3072-dim)
MLP_RESULTS = {
    'MLP Dense':            53.14,
    'MLP Top-K MoE':        50.11,
    'MLP Repulsion (A|G)':  52.94,
    'MLP Repulsion Quad':   52.69,
    'MLP Meta fixed':       53.52,
    'MLP SelfRef Field':    52.06,
}


def main():
    print()
    print("=" * 70)
    print("   logout — CNN Repulsion Field Benchmark (CIFAR-10)")
    print("   MLP 53% → CNN 70%+? Is repulsion field advantage maintained?")
    print("=" * 70)

    train_loader, test_loader = load_cifar10_augmented()
    epochs = 30
    lr = 0.001
    results = {}
    tension_data = {}

    # ── 1. CNN + Dense (baseline) ──
    print("\n[1/5] CNN + Dense (baseline)")
    model = CNNDense()
    losses, accs = train_cnn(model, train_loader, test_loader, epochs, lr)
    results['CNN+Dense'] = {
        'acc': accs[-1], 'loss': losses[-1],
        'params': count_params(model),
        'accs': accs, 'losses': losses,
    }

    # ── 2. CNN + TopK MoE ──
    print("\n[2/5] CNN + TopK MoE (8 experts, k=2)")
    model = CNNTopKMoE()
    losses, accs = train_cnn(model, train_loader, test_loader, epochs, lr)
    results['CNN+TopK MoE'] = {
        'acc': accs[-1], 'loss': losses[-1],
        'params': count_params(model),
        'accs': accs, 'losses': losses,
    }

    # ── 3. CNN + RepulsionField (2-pole) ──
    print("\n[3/5] CNN + RepulsionField (2-pole: A vs G)")
    model = CNNRepulsionField()
    losses, accs = train_cnn(model, train_loader, test_loader, epochs, lr)
    results['CNN+Repulsion'] = {
        'acc': accs[-1], 'loss': losses[-1],
        'params': count_params(model),
        'accs': accs, 'losses': losses,
    }
    tension_data['Repulsion 2-pole'] = {
        'tension': model.tension_magnitude,
        'scale': model.tension_scale.item(),
    }
    print(f"    Tension: {model.tension_magnitude:.4f}, Scale: {model.tension_scale.item():.4f}")

    # ── 4. CNN + RepulsionQuad (4-pole) ──
    print("\n[4/5] CNN + RepulsionQuad (4-pole: A|G x E|F)")
    model = CNNRepulsionQuad()
    losses, accs = train_cnn(model, train_loader, test_loader, epochs, lr)
    results['CNN+RepulsionQuad'] = {
        'acc': accs[-1], 'loss': losses[-1],
        'params': count_params(model),
        'accs': accs, 'losses': losses,
    }
    tension_data['Repulsion 4-pole'] = {
        'tension_content': model.tension_content,
        'tension_structure': model.tension_structure,
        'scale': model.tension_scale.item(),
    }
    print(f"    Content tension: {model.tension_content:.4f}")
    print(f"    Structure tension: {model.tension_structure:.4f}")
    print(f"    Scale: {model.tension_scale.item():.4f}")

    # ── 5. CNN + MetaFixed {1/2, 1/3, 1/6} ──
    print("\n[5/5] CNN + MetaFixed {{1/2, 1/3, 1/6}}")
    model = CNNMetaFixed()
    losses, accs = train_cnn(model, train_loader, test_loader, epochs, lr)
    results['CNN+Meta{1/2,1/3,1/6}'] = {
        'acc': accs[-1], 'loss': losses[-1],
        'params': count_params(model),
        'accs': accs, 'losses': losses,
    }
    learned_w = model.get_weights()
    print(f"    Learned weights: [{learned_w[0]:.4f}, {learned_w[1]:.4f}, {learned_w[2]:.4f}]")
    print(f"    Init was:        [0.5000, 0.3333, 0.1667]")

    # ─────────────────────────────────────────
    # Results table
    # ─────────────────────────────────────────
    print("\n")
    print("=" * 75)
    print("   CNN CIFAR-10 Results (30 epochs, lr=0.001, Adam)")
    print("=" * 75)
    print(f"  {'Model':<28} {'Acc':>8} {'Loss':>8} {'Params':>10}")
    print("-" * 75)

    best_acc = max(r['acc'] for r in results.values())
    for name, r in sorted(results.items(), key=lambda x: -x[1]['acc']):
        marker = ' <-- best' if r['acc'] == best_acc else ''
        print(f"  {name:<28} {r['acc']*100:>7.2f}% {r['loss']:>8.4f} {r['params']:>10,}{marker}")
    print("=" * 75)

    # ─────────────────────────────────────────
    # Tension data
    # ─────────────────────────────────────────
    print("\n")
    print("=" * 60)
    print("   Tension Data (Repulsion Models)")
    print("=" * 60)
    for name, td in tension_data.items():
        print(f"\n  {name}:")
        for k, v in td.items():
            print(f"    {k}: {v:.4f}")
    print()

    # ─────────────────────────────────────────
    # MLP vs CNN comparison
    # ─────────────────────────────────────────
    print("=" * 75)
    print("   MLP vs CNN Comparison (CIFAR-10)")
    print("=" * 75)
    print(f"  {'Model':<28} {'MLP':>8} {'CNN':>8} {'Delta':>8}")
    print("-" * 75)

    comparisons = [
        ('Dense',       'MLP Dense',           'CNN+Dense'),
        ('TopK MoE',    'MLP Top-K MoE',       'CNN+TopK MoE'),
        ('Repulsion',   'MLP Repulsion (A|G)',  'CNN+Repulsion'),
        ('RepulsionQ',  'MLP Repulsion Quad',   'CNN+RepulsionQuad'),
        ('Meta fixed',  'MLP Meta fixed',       'CNN+Meta{1/2,1/3,1/6}'),
    ]
    for label, mlp_key, cnn_key in comparisons:
        mlp_acc = MLP_RESULTS.get(mlp_key, 0)
        cnn_acc = results[cnn_key]['acc'] * 100
        delta = cnn_acc - mlp_acc
        print(f"  {label:<28} {mlp_acc:>7.2f}% {cnn_acc:>7.2f}% {delta:>+7.2f}%")
    print("=" * 75)

    # ─────────────────────────────────────────
    # Key question answers
    # ─────────────────────────────────────────
    print("\n")
    print("-" * 70)
    print("  KEY QUESTIONS")
    print("-" * 70)

    cnn_dense_acc = results['CNN+Dense']['acc']
    cnn_repulsion_acc = results['CNN+Repulsion']['acc']
    cnn_quad_acc = results['CNN+RepulsionQuad']['acc']
    cnn_meta_acc = results['CNN+Meta{1/2,1/3,1/6}']['acc']
    cnn_topk_acc = results['CNN+TopK MoE']['acc']

    # Q1: Does repulsion field advantage persist with CNN?
    rep_vs_dense = (cnn_repulsion_acc - cnn_dense_acc) * 100
    print(f"\n  Q1: Repulsion field advantage with CNN?")
    print(f"      CNN+Repulsion vs CNN+Dense: {rep_vs_dense:+.2f}%")
    print(f"      {'YES - advantage persists' if rep_vs_dense > 0 else 'NO - CNN equalizes'}")

    # Q2: Does {1/2, 1/3, 1/6} still win?
    meta_vs_all = cnn_meta_acc - max(cnn_dense_acc, cnn_topk_acc, cnn_repulsion_acc, cnn_quad_acc)
    print(f"\n  Q2: Does {{1/2, 1/3, 1/6}} still win?")
    print(f"      CNN+Meta vs best other: {meta_vs_all*100:+.2f}%")
    if cnn_meta_acc == best_acc:
        print(f"      YES - {{1/2, 1/3, 1/6}} is still the best!")
    else:
        best_name = max(results.items(), key=lambda x: x[1]['acc'])[0]
        print(f"      NO - {best_name} wins")

    # Q3: CNN improvement over MLP
    avg_mlp = np.mean(list(MLP_RESULTS.values()))
    avg_cnn = np.mean([r['acc'] * 100 for r in results.values()])
    print(f"\n  Q3: CNN improvement over MLP?")
    print(f"      MLP average: {avg_mlp:.2f}%")
    print(f"      CNN average: {avg_cnn:.2f}%")
    print(f"      Average improvement: {avg_cnn - avg_mlp:+.2f}%")

    # Q4: Learned weights drift
    print(f"\n  Q4: Do learned weights stay near {{1/2, 1/3, 1/6}}?")
    print(f"      Init:    [0.5000, 0.3333, 0.1667]")
    print(f"      Learned: [{learned_w[0]:.4f}, {learned_w[1]:.4f}, {learned_w[2]:.4f}]")
    drift = np.sqrt(sum((a - b) ** 2 for a, b in
                        zip(learned_w, [0.5, 1/3, 1/6])))
    print(f"      L2 drift: {drift:.4f}")
    print(f"      {'Stable (drift < 0.1)' if drift < 0.1 else 'Significant drift'}")

    # ─────────────────────────────────────────
    # Training curves (ASCII)
    # ─────────────────────────────────────────
    print("\n")
    print("=" * 70)
    print("   Training Curves (accuracy at epochs 1, 5, 10, 15, 20, 25, 30)")
    print("=" * 70)
    checkpoints = [0, 4, 9, 14, 19, 24, 29]
    print(f"  {'Model':<28}", end="")
    for cp in checkpoints:
        print(f" {'E'+str(cp+1):>6}", end="")
    print()
    print("-" * 75)
    for name, r in sorted(results.items(), key=lambda x: -x[1]['acc']):
        print(f"  {name:<28}", end="")
        for cp in checkpoints:
            if cp < len(r['accs']):
                print(f" {r['accs'][cp]*100:>5.1f}%", end="")
            else:
                print(f"    N/A", end="")
        print()
    print("=" * 70)
    print()


if __name__ == '__main__':
    main()