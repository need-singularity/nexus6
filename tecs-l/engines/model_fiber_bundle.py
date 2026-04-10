#!/usr/bin/env python3
"""Fiber Bundle Engine — Higher-dimensional information arrives through geometric connections

Mathematical structure:
  E (total space) = B x F (locally)
  B = base space (input → classification)
  F = fiber (higher-dimensional experience space)
  Connection A = how fiber rotates when moving in the base
  Curvature F = dA + A∧A (curvature = tension)
  Holonomy = processing the same input via different paths results in different fiber states

Key insights:
  The fiber contains information not present in training labels.
  The base space handles classification, but the fiber captures "experience"
  — things the model knows but cannot express as labels.

A Priori Latent Space:
  Structure exists in the latent space before learning.
  Eigenvectors of the graph Laplacian provide a priori geometry.
  Unvisited points still have meaning because the structure already exists.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import time

from model_utils import (
    load_mnist, train_and_evaluate, compare_results, count_params,
)
from model_meta_engine import (
    EngineA, EngineG, RepulsionFieldQuad,
)


# ─────────────────────────────────────────
# Fiber Bundle Engine
# ─────────────────────────────────────────

class FiberBundleEngine(nn.Module):
    """Fiber Bundle over Repulsion Field.

    E (total space) = B x F (locally)
    B = base space (input -> classification)
    F = fiber (higher-dimensional experience)
    Connection A = how fiber rotates as you move in B
    Curvature F = dA + A^A (tension = curvature)

    The fiber contains information invisible from the base.
    Classification only uses B. But F influences B through the connection.
    """
    def __init__(self, input_dim=784, hidden_dim=48, output_dim=10, fiber_dim=32):
        super().__init__()
        self.fiber_dim = fiber_dim

        # Base space: two engines (like RepulsionField)
        self.engine_a = EngineA(input_dim, hidden_dim, output_dim)
        self.engine_g = EngineG(input_dim, hidden_dim, output_dim)

        # Fiber: higher dimensional representation
        # The fiber exists at every point in the base
        self.fiber_encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, fiber_dim),
        )

        # Connection: maps base tangent vectors to fiber transformations
        # In our case: the repulsion (base curvature) determines fiber rotation
        self.connection = nn.Sequential(
            nn.Linear(output_dim, fiber_dim),
            nn.Tanh(),
        )

        # Holonomy accumulator: fiber state changes as you "move" through input
        # Different processing paths -> different fiber states
        self.parallel_transport = nn.Linear(fiber_dim, fiber_dim)

        # Curvature -> information leakage from fiber to base
        self.fiber_to_base = nn.Sequential(
            nn.Linear(fiber_dim, output_dim),
            nn.Tanh(),
        )

        # Curvature scale (learned — expect to converge near 1/3)
        self.curvature_scale = nn.Parameter(torch.tensor(1.0 / 3))

        # Monitoring
        self.curvature_magnitude = 0.0
        self.fiber_norm = 0.0
        self.holonomy_angle = 0.0
        self.aux_loss = torch.tensor(0.0)

    def forward(self, x):
        # 1. Base space: two engines compute their outputs
        out_a = self.engine_a(x)
        out_g = self.engine_g(x)

        # 2. Base repulsion (tangent vector in base space)
        repulsion = out_a - out_g

        # 3. Fiber state at this point
        fiber_state = self.fiber_encoder(x)

        # 4. Connection: repulsion determines how fiber rotates
        fiber_rotation = self.connection(repulsion)

        # 5. Parallel transport: apply rotation to fiber state
        transported_fiber = self.parallel_transport(fiber_state + fiber_rotation)

        # 6. Curvature = how much the fiber changed
        curvature = (transported_fiber - fiber_state).pow(2).sum(dim=-1, keepdim=True)

        # 7. Information leakage: curvature > 0 means fiber info enters base
        fiber_info = self.fiber_to_base(transported_fiber)

        # 8. Base output + fiber leakage
        equilibrium = (out_a + out_g) / 2
        output = equilibrium + self.curvature_scale * fiber_info

        # 9. Entropy loss from G engine
        self.aux_loss = getattr(self.engine_g, 'entropy_loss', torch.tensor(0.0))

        # 10. Monitor
        with torch.no_grad():
            self.curvature_magnitude = curvature.mean().item()
            self.fiber_norm = fiber_state.norm(dim=-1).mean().item()
            self.holonomy_angle = F.cosine_similarity(
                fiber_state, transported_fiber, dim=-1
            ).mean().item()

        return (output, self.aux_loss)

    def get_fiber_state(self, x):
        """Extract fiber state without classification — the 'experience' vector."""
        with torch.no_grad():
            fiber_state = self.fiber_encoder(x)
            out_a = self.engine_a(x)
            out_g = self.engine_g(x)
            repulsion = out_a - out_g
            fiber_rotation = self.connection(repulsion)
            transported = self.parallel_transport(fiber_state + fiber_rotation)
            curvature = (transported - fiber_state).pow(2).sum(dim=-1)
        return {
            'fiber_state': fiber_state,
            'transported': transported,
            'curvature': curvature,
            'holonomy': F.cosine_similarity(fiber_state, transported, dim=-1),
        }


# ─────────────────────────────────────────
# A Priori Latent Space
# ─────────────────────────────────────────

class APrioriLatentSpace(nn.Module):
    """A priori latent space: structure exists BEFORE learning.

    The latent space is initialized with mathematical structure (not random).
    Learning = visiting points in a pre-existing landscape.
    Unvisited points still have meaning because the structure was already there.

    Structure source: eigenvalues of a graph Laplacian on a cycle graph,
    giving the space inherent geometry before any data.
    """
    def __init__(self, input_dim=784, latent_dim=32, output_dim=10):
        super().__init__()
        self.latent_dim = latent_dim
        self.output_dim = output_dim
        self.n_regions = 100

        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, latent_dim * 2),  # mu + logvar
        )

        # A PRIORI structure: the latent space has geometry before learning
        L = self._build_laplacian(latent_dim)
        eigenvalues, eigenvectors = torch.linalg.eigh(L)
        self.register_buffer('prior_basis', eigenvectors)
        self.register_buffer('prior_spectrum', eigenvalues)

        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 128),
            nn.ReLU(),
            nn.Linear(128, output_dim),
        )

        # Track which regions have been "visited" during training
        self.register_buffer('visit_counts', torch.zeros(self.n_regions))
        self.register_buffer('visit_centroids', torch.randn(self.n_regions, latent_dim) * 0.1)

    def _build_laplacian(self, n):
        """Build graph Laplacian for a cycle graph — gives the space circular topology."""
        L = torch.zeros(n, n)
        for i in range(n):
            L[i, i] = 2
            L[i, (i + 1) % n] = -1
            L[i, (i - 1) % n] = -1
        return L

    def encode(self, x):
        h = self.encoder(x)
        mu, logvar = h.chunk(2, dim=-1)
        # Project onto prior basis — encoding respects pre-existing structure
        mu_structured = mu @ self.prior_basis
        return mu_structured, logvar

    def reparameterize(self, mu, logvar):
        if self.training:
            std = torch.exp(0.5 * logvar)
            eps = torch.randn_like(std)
            return mu + eps * std
        return mu

    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        output = self.decoder(z)
        kl = -0.5 * (1 + logvar - mu.pow(2) - logvar.exp()).sum(dim=-1).mean()

        # Track visits
        with torch.no_grad():
            self._update_visits(z)

        return output, kl * 0.01

    def _update_visits(self, z):
        """Find nearest centroid for each sample and update visit counts."""
        dists = torch.cdist(z, self.visit_centroids)
        nearest = dists.argmin(dim=1)
        for idx in nearest.unique():
            mask = nearest == idx
            self.visit_counts[idx] += mask.sum().float()
            if mask.sum() > 0:
                self.visit_centroids[idx] = (
                    0.99 * self.visit_centroids[idx] + 0.01 * z[mask].mean(0)
                )

    def get_unvisited_experience(self, n=10):
        """Generate 'experiences' from UNVISITED regions of latent space."""
        least_visited = self.visit_counts.argsort()[:n]
        z_unvisited = self.visit_centroids[least_visited]
        with torch.no_grad():
            outputs = self.decoder(z_unvisited)
        return z_unvisited, outputs, self.visit_counts[least_visited]

    def get_visit_stats(self):
        """Return visit statistics."""
        total = self.visit_counts.sum().item()
        visited = (self.visit_counts > 0).sum().item()
        max_visits = self.visit_counts.max().item()
        min_visits = self.visit_counts.min().item()
        return {
            'total_visits': total,
            'visited_regions': visited,
            'total_regions': self.n_regions,
            'coverage': visited / self.n_regions,
            'max_visits': max_visits,
            'min_visits': min_visits,
            'visit_std': self.visit_counts.std().item(),
        }


# ─────────────────────────────────────────
# Benchmark utilities
# ─────────────────────────────────────────

def ascii_bar(value, max_val, width=40, char='#'):
    """Simple ASCII bar."""
    if max_val == 0:
        return ''
    n = int(value / max_val * width)
    return char * n + '.' * (width - n)


def ascii_line_graph(values, label, width=50, height=8):
    """ASCII line graph."""
    if not values:
        return
    vmin, vmax = min(values), max(values)
    if vmax == vmin:
        vmax = vmin + 1e-8
    print(f"\n  {label}")
    print(f"  {'':>6} {'':>{width}}")
    for row in range(height - 1, -1, -1):
        threshold = vmin + (vmax - vmin) * row / (height - 1)
        line = ''
        for v in values:
            if v >= threshold:
                line += '*'
            else:
                line += ' '
        # Compress if too many points
        if len(line) > width:
            step = len(line) / width
            line = ''.join(line[int(i * step)] for i in range(width))
        if row == height - 1:
            print(f"  {vmax:>6.3f} |{line}")
        elif row == 0:
            print(f"  {vmin:>6.3f} |{line}")
        else:
            print(f"  {'':>6} |{line}")
    print(f"  {'':>6} +{'-' * min(len(values), width)}")
    print(f"  {'':>6}  {'epoch 1':>{min(len(values), width) // 2}}{'epoch ' + str(len(values)):>{min(len(values), width) - min(len(values), width) // 2}}")


def digit_to_ascii(probs, width=7, height=5):
    """Convert output probabilities to a simple ASCII visualization."""
    if probs.dim() == 0:
        return str(probs.item())
    top_val, top_idx = probs.topk(3)
    lines = []
    lines.append(f"  Top predictions:")
    for v, i in zip(top_val, top_idx):
        bar = '#' * int(v.item() * 20)
        lines.append(f"    digit {i.item()}: {v.item():.3f} {bar}")
    return '\n'.join(lines)


# ─────────────────────────────────────────
# Benchmark
# ─────────────────────────────────────────

def main():
    print()
    print("=" * 70)
    print("   logout — Fiber Bundle Engine Benchmark")
    print("   Higher-dimensional information through geometric connections")
    print("=" * 70)

    train_loader, test_loader = load_mnist()
    input_dim, hidden_dim, output_dim = 784, 48, 10
    fiber_dim = 32
    latent_dim = 32
    epochs = 10
    results = {}

    # ══════════════════════════════════════════
    # Part 1: FiberBundleEngine vs RepulsionFieldQuad
    # ══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("  PART 1: FiberBundleEngine vs RepulsionFieldQuad")
    print("=" * 70)

    # -- Baseline: RepulsionFieldQuad --
    print("\n[RepulsionFieldQuad (4-pole baseline)]")
    model_quad = RepulsionFieldQuad(input_dim, hidden_dim, output_dim)
    losses_q, accs_q = train_and_evaluate(
        model_quad, train_loader, test_loader, epochs, aux_lambda=0.01
    )
    results['RepulsionFieldQuad'] = {
        'acc': accs_q[-1], 'loss': losses_q[-1], 'params': count_params(model_quad)
    }

    # -- FiberBundleEngine --
    print("\n[FiberBundleEngine (fiber_dim=32)]")
    model_fb = FiberBundleEngine(input_dim, hidden_dim, output_dim, fiber_dim)

    # Custom training to track fiber metrics per epoch
    optimizer = torch.optim.Adam(model_fb.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    curvatures = []
    fiber_norms = []
    holonomy_angles = []
    fb_losses = []
    fb_accs = []

    for epoch in range(epochs):
        model_fb.train()
        total_loss = 0
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            logits, aux = model_fb(X)
            loss = criterion(logits, y) + 0.01 * aux
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        fb_losses.append(avg_loss)

        # Evaluate
        model_fb.eval()
        correct = total = 0
        with torch.no_grad():
            for X, y in test_loader:
                X = X.view(X.size(0), -1)
                logits, _ = model_fb(X)
                correct += (logits.argmax(1) == y).sum().item()
                total += y.size(0)
        acc = correct / total
        fb_accs.append(acc)

        curvatures.append(model_fb.curvature_magnitude)
        fiber_norms.append(model_fb.fiber_norm)
        holonomy_angles.append(model_fb.holonomy_angle)

        if (epoch + 1) % 2 == 0 or epoch == 0:
            print(f"    Epoch {epoch+1:>2}/{epochs}: Loss={avg_loss:.4f}, Acc={acc*100:.1f}%, "
                  f"Curv={model_fb.curvature_magnitude:.4f}, "
                  f"FiberNorm={model_fb.fiber_norm:.3f}, "
                  f"Holonomy={model_fb.holonomy_angle:.4f}")

    results['FiberBundle'] = {
        'acc': fb_accs[-1], 'loss': fb_losses[-1], 'params': count_params(model_fb)
    }

    print(f"\n  Curvature scale (learned): {model_fb.curvature_scale.item():.4f}")
    print(f"  Expected ~1/3 = 0.3333")

    # Fiber metrics graphs
    ascii_line_graph(curvatures, "Curvature magnitude over training")
    ascii_line_graph(fiber_norms, "Fiber norm over training")
    ascii_line_graph(holonomy_angles, "Holonomy angle (cosine similarity) over training")

    # ══════════════════════════════════════════
    # Part 2: Fiber-only recognition (labelless)
    # ══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("  PART 2: Fiber-Only Recognition (no labels used for matching)")
    print("=" * 70)

    print("\n  Extracting fiber states for test set...")
    model_fb.eval()
    all_fibers = []
    all_labels = []
    with torch.no_grad():
        for X, y in test_loader:
            X = X.view(X.size(0), -1)
            info = model_fb.get_fiber_state(X)
            all_fibers.append(info['fiber_state'])
            all_labels.append(y)

    all_fibers = torch.cat(all_fibers, dim=0)  # (N, fiber_dim)
    all_labels = torch.cat(all_labels, dim=0)  # (N,)

    # k-means on fiber states (simple, 10 clusters for 10 digits)
    print("\n  [k-means on fiber states (k=10)]")
    n_clusters = 10
    # Initialize centroids from random samples
    perm = torch.randperm(all_fibers.size(0))[:n_clusters]
    centroids = all_fibers[perm].clone()

    for iteration in range(50):
        dists = torch.cdist(all_fibers, centroids)
        assignments = dists.argmin(dim=1)
        new_centroids = torch.zeros_like(centroids)
        for k in range(n_clusters):
            mask = assignments == k
            if mask.sum() > 0:
                new_centroids[k] = all_fibers[mask].mean(0)
            else:
                new_centroids[k] = centroids[k]
        if (new_centroids - centroids).norm() < 1e-6:
            break
        centroids = new_centroids

    # Evaluate: majority label per cluster
    cluster_labels = torch.zeros(n_clusters, dtype=torch.long)
    for k in range(n_clusters):
        mask = assignments == k
        if mask.sum() > 0:
            labels_in_cluster = all_labels[mask]
            cluster_labels[k] = labels_in_cluster.mode().values

    predicted = cluster_labels[assignments]
    kmeans_acc = (predicted == all_labels).float().mean().item()
    print(f"  k-means accuracy (fiber states): {kmeans_acc*100:.1f}%")

    # Cluster purity table
    print(f"\n  {'Cluster':>8} {'Majority':>9} {'Size':>6} {'Purity':>8}")
    print(f"  {'-'*35}")
    for k in range(n_clusters):
        mask = assignments == k
        size = mask.sum().item()
        if size > 0:
            purity = (all_labels[mask] == cluster_labels[k]).float().mean().item()
            print(f"  {k:>8} {cluster_labels[k].item():>9} {size:>6} {purity*100:>7.1f}%")

    # 1-NN on fiber states
    print("\n  [1-NN on fiber states]")
    # Use first 5000 as "library", rest as query
    n_lib = 5000
    lib_fibers = all_fibers[:n_lib]
    lib_labels = all_labels[:n_lib]
    query_fibers = all_fibers[n_lib:]
    query_labels = all_labels[n_lib:]

    # Batch 1-NN to avoid memory issues
    correct_1nn = 0
    batch_size = 500
    for i in range(0, query_fibers.size(0), batch_size):
        batch_q = query_fibers[i:i+batch_size]
        dists = torch.cdist(batch_q, lib_fibers)
        nearest = dists.argmin(dim=1)
        pred = lib_labels[nearest]
        correct_1nn += (pred == query_labels[i:i+batch_size]).sum().item()

    nn_acc = correct_1nn / query_fibers.size(0)
    print(f"  1-NN accuracy (fiber states): {nn_acc*100:.1f}%")
    print(f"  (library={n_lib}, queries={query_fibers.size(0)})")

    # ══════════════════════════════════════════
    # Part 3: Holonomy Experiment
    # ══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("  PART 3: Holonomy Experiment")
    print("  Same digit, different paths -> different fiber states?")
    print("=" * 70)

    model_fb.eval()
    # Get a batch of test images
    test_iter = iter(test_loader)
    X_test, y_test = next(test_iter)
    X_test = X_test.view(X_test.size(0), -1)

    # Original fiber states and predictions
    with torch.no_grad():
        logits_orig, _ = model_fb(X_test)
        info_orig = model_fb.get_fiber_state(X_test)
        pred_orig = logits_orig.argmax(1)

    # Add slight noise (different "paths" through the same digit)
    noise_levels = [0.05, 0.1, 0.2, 0.5]
    print(f"\n  {'Noise':>6} {'Base same%':>11} {'Fiber cos':>10} {'Fiber L2':>10} {'Curv diff':>10}")
    print(f"  {'-'*50}")

    for noise in noise_levels:
        X_noisy = X_test + noise * torch.randn_like(X_test)
        with torch.no_grad():
            logits_noisy, _ = model_fb(X_noisy)
            info_noisy = model_fb.get_fiber_state(X_noisy)
            pred_noisy = logits_noisy.argmax(1)

        base_same = (pred_orig == pred_noisy).float().mean().item()
        fiber_cos = F.cosine_similarity(
            info_orig['fiber_state'], info_noisy['fiber_state'], dim=-1
        ).mean().item()
        fiber_l2 = (info_orig['fiber_state'] - info_noisy['fiber_state']).norm(dim=-1).mean().item()
        curv_diff = (info_orig['curvature'] - info_noisy['curvature']).abs().mean().item()

        print(f"  {noise:>6.2f} {base_same*100:>10.1f}% {fiber_cos:>10.4f} {fiber_l2:>10.4f} {curv_diff:>10.4f}")

    print("\n  Holonomy = fiber changes while base stays the same.")
    print("  High 'Base same%' + low 'Fiber cos' = strong holonomy.")

    # ══════════════════════════════════════════
    # Part 4: A Priori Latent Space
    # ══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("  PART 4: A Priori Latent Space")
    print("  Structure exists BEFORE learning")
    print("=" * 70)

    print("\n[APrioriLatentSpace (latent_dim=32)]")
    model_ap = APrioriLatentSpace(input_dim, latent_dim, output_dim)
    losses_ap, accs_ap = train_and_evaluate(
        model_ap, train_loader, test_loader, epochs, aux_lambda=1.0
    )
    results['APrioriLatent'] = {
        'acc': accs_ap[-1], 'loss': losses_ap[-1], 'params': count_params(model_ap)
    }

    # ══════════════════════════════════════════
    # Part 5: Unvisited Experience
    # ══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("  PART 5: Unvisited Experience")
    print("  Outputs from regions the model NEVER visited during training")
    print("=" * 70)

    model_ap.eval()
    z_unvisited, outputs_unvisited, visit_counts = model_ap.get_unvisited_experience(n=10)
    probs = F.softmax(outputs_unvisited, dim=-1)

    print(f"\n  {'Region':>7} {'Visits':>7} {'Top-1':>6} {'Conf':>6} {'Top-3 digits':>20}")
    print(f"  {'-'*50}")
    for i in range(min(10, probs.size(0))):
        top3_val, top3_idx = probs[i].topk(3)
        top3_str = ', '.join(f"{idx.item()}({val.item():.2f})" for val, idx in zip(top3_val, top3_idx))
        print(f"  {i:>7} {visit_counts[i].item():>7.0f} {top3_idx[0].item():>6} {top3_val[0].item():>6.3f} {top3_str:>20}")

    # ASCII art: show top-1 prediction confidence as bar
    print("\n  Unvisited region predictions (confidence bars):")
    for i in range(min(10, probs.size(0))):
        top_val, top_idx = probs[i].topk(1)
        bar = ascii_bar(top_val.item(), 1.0, width=30)
        print(f"    Region {i}: digit {top_idx.item()} [{bar}] {top_val.item():.3f}")

    # ══════════════════════════════════════════
    # Part 6: Visit Map
    # ══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("  PART 6: Visit Map — explored vs unexplored")
    print("=" * 70)

    stats = model_ap.get_visit_stats()
    print(f"\n  Total visits:     {stats['total_visits']:.0f}")
    print(f"  Visited regions:  {stats['visited_regions']}/{stats['total_regions']}")
    print(f"  Coverage:         {stats['coverage']*100:.1f}%")
    print(f"  Max visits:       {stats['max_visits']:.0f}")
    print(f"  Min visits:       {stats['min_visits']:.0f}")
    print(f"  Visit std:        {stats['visit_std']:.1f}")

    # ASCII visit map (10x10 grid)
    print("\n  Visit map (10x10 regions, # = visited, . = unvisited):")
    counts = model_ap.visit_counts.cpu()
    max_count = counts.max().item() if counts.max().item() > 0 else 1
    print(f"  {'':>4}", end='')
    for c in range(10):
        print(f"{c:>4}", end='')
    print()
    for r in range(10):
        print(f"  {r:>3} ", end='')
        for c in range(10):
            idx = r * 10 + c
            v = counts[idx].item()
            if v == 0:
                ch = '  . '
            elif v < max_count * 0.1:
                ch = '  o '
            elif v < max_count * 0.5:
                ch = '  O '
            else:
                ch = '  # '
            print(ch, end='')
        print()

    # Visit distribution histogram (ASCII)
    print("\n  Visit count distribution:")
    buckets = [0, 1, 10, 100, 1000, 10000, 100000, float('inf')]
    bucket_names = ['  0', '1-9', '10-99', '100-999', '1k-9k', '10k-99k', '100k+']
    for i in range(len(buckets) - 1):
        count = ((counts >= buckets[i]) & (counts < buckets[i+1])).sum().item()
        bar = ascii_bar(count, 100, width=30)
        print(f"    {bucket_names[i]:>8}: {count:>3} {bar}")

    # ══════════════════════════════════════════
    # Part 7: Train on 0-7 only, test on 8,9
    # ══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("  PART 7: Never-Seen Digits (train 0-7, test 8-9)")
    print("  Can a priori structure help recognize unseen digits?")
    print("=" * 70)

    # Build filtered loaders
    from torch.utils.data import DataLoader, Subset
    from torchvision import datasets, transforms

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    train_ds = datasets.MNIST('data', train=True, download=True, transform=transform)
    test_ds = datasets.MNIST('data', train=False, transform=transform)

    # Train on 0-7 only
    train_07_idx = [i for i, (_, label) in enumerate(train_ds) if label <= 7]
    train_07_loader = DataLoader(Subset(train_ds, train_07_idx), batch_size=128, shuffle=True)

    # Test on 8-9 only
    test_89_idx = [i for i, (_, label) in enumerate(test_ds) if label >= 8]
    test_89_loader = DataLoader(Subset(test_ds, test_89_idx), batch_size=128, shuffle=False)

    # Also test on 0-7 for reference
    test_07_idx = [i for i, (_, label) in enumerate(test_ds) if label <= 7]
    test_07_loader = DataLoader(Subset(test_ds, test_07_idx), batch_size=128, shuffle=False)

    # A Priori model
    print("\n  [A Priori Latent Space — trained on 0-7]")
    model_apriori = APrioriLatentSpace(input_dim, latent_dim, output_dim)
    train_and_evaluate(model_apriori, train_07_loader, test_07_loader, epochs, aux_lambda=1.0)

    # Random baseline (no prior structure — standard VAE-like)
    print("\n  [Random Latent Space (no prior) — trained on 0-7]")
    model_random = APrioriLatentSpace(input_dim, latent_dim, output_dim)
    # Destroy prior structure by randomizing basis
    with torch.no_grad():
        model_random.prior_basis.copy_(torch.eye(latent_dim))
    train_and_evaluate(model_random, train_07_loader, test_07_loader, epochs, aux_lambda=1.0)

    # Evaluate both on unseen digits 8, 9
    def eval_on_89(model, loader):
        """Evaluate: check if model outputs anything coherent for 8, 9."""
        model.eval()
        all_logits = []
        all_labels = []
        with torch.no_grad():
            for X, y in loader:
                X = X.view(X.size(0), -1)
                out, _ = model(X)
                all_logits.append(out)
                all_labels.append(y)
        logits = torch.cat(all_logits, dim=0)
        labels = torch.cat(all_labels, dim=0)
        probs = F.softmax(logits, dim=-1)
        preds = logits.argmax(1)

        # Since model was trained on 0-7, it will predict 0-7
        # But we can look at the confidence and distribution
        conf_mean = probs.max(dim=1).values.mean().item()
        entropy = -(probs * (probs + 1e-8).log()).sum(dim=-1).mean().item()

        # How concentrated are predictions?
        pred_counts = torch.zeros(10)
        for d in range(10):
            pred_counts[d] = (preds == d).sum().item()
        pred_counts = pred_counts / pred_counts.sum()

        return {
            'confidence': conf_mean,
            'entropy': entropy,
            'pred_distribution': pred_counts,
            'preds': preds,
            'labels': labels,
            'probs': probs,
        }

    res_apriori = eval_on_89(model_apriori, test_89_loader)
    res_random = eval_on_89(model_random, test_89_loader)

    print(f"\n  Unseen digits (8, 9) — output analysis:")
    print(f"\n  {'Metric':>25} {'A Priori':>12} {'Random':>12}")
    print(f"  {'-'*50}")
    print(f"  {'Confidence (mean)':>25} {res_apriori['confidence']:>12.4f} {res_random['confidence']:>12.4f}")
    print(f"  {'Output entropy':>25} {res_apriori['entropy']:>12.4f} {res_random['entropy']:>12.4f}")

    print(f"\n  Prediction distribution on unseen 8, 9:")
    print(f"  {'Digit':>7} {'A Priori':>10} {'Random':>10}")
    print(f"  {'-'*30}")
    for d in range(10):
        print(f"  {d:>7} {res_apriori['pred_distribution'][d].item()*100:>9.1f}% {res_random['pred_distribution'][d].item()*100:>9.1f}%")

    # Key insight: lower confidence / higher entropy on unseen digits =
    # the model "knows" these are different
    print(f"\n  Key insight:")
    if res_apriori['entropy'] > res_random['entropy']:
        print(f"  A Priori has HIGHER entropy on unseen digits ({res_apriori['entropy']:.3f} > {res_random['entropy']:.3f})")
        print(f"  -> The prior structure 'knows' these digits are different from training")
    else:
        print(f"  Random has higher entropy on unseen digits")
        print(f"  -> Prior structure did not help distinguish unseen digits in this run")

    # Also check: does a priori latent space have more distinct representations for 8 vs 9?
    print("\n  Fiber/latent distinction between digit 8 and digit 9:")
    model_apriori.eval()
    model_random.eval()
    z_8_ap, z_9_ap = [], []
    z_8_rn, z_9_rn = [], []
    with torch.no_grad():
        for X, y in test_89_loader:
            X_flat = X.view(X.size(0), -1)
            mu_ap, _ = model_apriori.encode(X_flat)
            mu_rn, _ = model_random.encode(X_flat)
            mask_8 = y == 8
            mask_9 = y == 9
            if mask_8.sum() > 0:
                z_8_ap.append(mu_ap[mask_8])
                z_8_rn.append(mu_rn[mask_8])
            if mask_9.sum() > 0:
                z_9_ap.append(mu_ap[mask_9])
                z_9_rn.append(mu_rn[mask_9])

    z_8_ap = torch.cat(z_8_ap)
    z_9_ap = torch.cat(z_9_ap)
    z_8_rn = torch.cat(z_8_rn)
    z_9_rn = torch.cat(z_9_rn)

    # Distance between class centroids
    dist_ap = (z_8_ap.mean(0) - z_9_ap.mean(0)).norm().item()
    dist_rn = (z_8_rn.mean(0) - z_9_rn.mean(0)).norm().item()

    print(f"  Centroid distance (8 vs 9):")
    print(f"    A Priori: {dist_ap:.4f}")
    print(f"    Random:   {dist_rn:.4f}")
    if dist_ap > dist_rn:
        print(f"  -> A Priori separates unseen digits better (+{(dist_ap/dist_rn - 1)*100:.1f}%)")
    else:
        print(f"  -> Random separates unseen digits better in this run")

    # ══════════════════════════════════════════
    # Final Summary
    # ══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("  FINAL SUMMARY")
    print("=" * 70)

    compare_results(results)

    print("\n  Fiber Bundle Metrics (final epoch):")
    print(f"    Curvature magnitude: {curvatures[-1]:.4f}")
    print(f"    Fiber norm:          {fiber_norms[-1]:.3f}")
    print(f"    Holonomy angle:      {holonomy_angles[-1]:.4f}")
    print(f"    Curvature scale:     {model_fb.curvature_scale.item():.4f} (init=0.3333)")

    print(f"\n  Fiber-only recognition:")
    print(f"    k-means on fiber:    {kmeans_acc*100:.1f}%")
    print(f"    1-NN on fiber:       {nn_acc*100:.1f}%")

    print(f"\n  A Priori Latent Space:")
    print(f"    Coverage:            {stats['coverage']*100:.1f}% ({stats['visited_regions']}/{stats['total_regions']})")
    print(f"    Unseen digit separation (8 vs 9):")
    print(f"      A Priori dist:     {dist_ap:.4f}")
    print(f"      Random dist:       {dist_rn:.4f}")

    # Markdown summary table
    print("\n\n### Results Table (Markdown)\n")
    print("| Model | Accuracy | Params | Notes |")
    print("|-------|----------|--------|-------|")
    for name in ['RepulsionFieldQuad', 'FiberBundle', 'APrioriLatent']:
        r = results[name]
        notes = ''
        if name == 'FiberBundle':
            notes = f'curv={curvatures[-1]:.4f}, holonomy={holonomy_angles[-1]:.4f}'
        elif name == 'APrioriLatent':
            notes = f'coverage={stats["coverage"]*100:.0f}%'
        print(f"| {name} | {r['acc']*100:.2f}% | {r['params']:,} | {notes} |")

    print(f"\n| Experiment | Result |")
    print(f"|------------|--------|")
    print(f"| Fiber k-means | {kmeans_acc*100:.1f}% |")
    print(f"| Fiber 1-NN | {nn_acc*100:.1f}% |")
    print(f"| Unseen 8v9 sep (a priori) | {dist_ap:.4f} |")
    print(f"| Unseen 8v9 sep (random) | {dist_rn:.4f} |")
    print(f"| Latent coverage | {stats['coverage']*100:.0f}% |")

    print()


if __name__ == '__main__':
    main()