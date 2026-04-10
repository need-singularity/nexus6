#!/usr/bin/env python3
"""Generative Engine — VAE of Repulsion Field Latent Space

Extending the repulsion field architecture as a generative model.
Key insight: "The field between engines" is the generative latent space.

Two axes:
  Content axis (A vs G) = Meaning (what to generate)
  Structure axis (E vs F) = Context (how to generate)

Tension controls generative creativity:
  Low tension (0.1)     → Safe, average, boring generation
  Medium tension (~1/e) → Balanced, meaningful generation (Golden Zone)
  High tension (>1.0)   → Wild, novel, possibly incoherent

Mathematical basis:
  - Latent space = Equilibrium points of repulsion field
  - VAE's KL divergence = Information-theoretic cost of tension
  - Reconstruction loss = How well the field reflects reality
  - Tension adjustment = Exploration vs exploitation tradeoff
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math

from model_utils import (
    Expert, SIGMA, TAU, DIVISOR_RECIPROCALS, H_TARGET,
    load_mnist, count_params,
)


# ─────────────────────────────────────────
# ASCII Art Rendering
# ─────────────────────────────────────────

def tensor_to_ascii(tensor_28x28, width=14, height=14):
    """Convert 28x28 tensor to ASCII art.

    Downsample using 2x2 average pooling.
    Map brightness to characters.
    """
    chars = ' .:-=+*#%@'
    img = tensor_28x28.detach().cpu().squeeze()
    if img.dim() == 1:
        img = img.view(28, 28)

    # Normalize to 0-1 range
    vmin, vmax = img.min(), img.max()
    if vmax - vmin > 1e-6:
        img = (img - vmin) / (vmax - vmin)
    else:
        img = torch.zeros_like(img)

    # Downsample with 2x2 average pooling
    img_4d = img.unsqueeze(0).unsqueeze(0)
    pooled = F.avg_pool2d(img_4d, kernel_size=2).squeeze()  # (14, 14)

    lines = []
    for row in range(pooled.size(0)):
        line = ''
        for col in range(pooled.size(1)):
            val = pooled[row, col].item()
            idx = int(val * (len(chars) - 1))
            idx = max(0, min(len(chars) - 1, idx))
            line += chars[idx]
        lines.append(line)
    return '\n'.join(lines)


def show_ascii_grid(tensors, labels=None, width=14, height=14, cols=5):
    """Display multiple images as ASCII grid."""
    if labels is None:
        labels = [f'[{i}]' for i in range(len(tensors))]

    ascii_images = [tensor_to_ascii(t, width, height).split('\n') for t in tensors]

    # Output by columns
    for row_start in range(0, len(ascii_images), cols):
        row_end = min(row_start + cols, len(ascii_images))
        batch = ascii_images[row_start:row_end]
        batch_labels = labels[row_start:row_end]

        # Label row
        label_line = '  '.join(f'{l:^{width}}' for l in batch_labels)
        print(f'  {label_line}')

        # Image rows
        for line_idx in range(height):
            parts = []
            for img_lines in batch:
                if line_idx < len(img_lines):
                    parts.append(img_lines[line_idx])
                else:
                    parts.append(' ' * width)
            print(f'  {"  ".join(parts)}')
        print()


# ─────────────────────────────────────────
# Engine Encoder (Lightweight Version)
# ─────────────────────────────────────────

class EngineEncoder(nn.Module):
    """Single engine encoder.

    Latent space mapping reflecting engine characteristics.
    Outputs mu and logvar for VAE reparameterization.
    """
    def __init__(self, input_dim, latent_dim, engine_type='A'):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
        )
        self.mu = nn.Linear(64, latent_dim)
        self.logvar = nn.Linear(64, latent_dim)
        self.engine_type = engine_type

    def forward(self, x):
        h = self.encoder(x)
        return self.mu(h), self.logvar(h), h


# ─────────────────────────────────────────
# RepulsionFieldVAE
# ─────────────────────────────────────────

class RepulsionFieldVAE(nn.Module):
    """Variational Autoencoder with repulsion field latent space.

    4 engines form repulsion fields in latent space:
      Content axis: A(generate) ←repulsion→ G(calibrate) = meaning vector
      Structure axis: E(explore) ←repulsion→ F(constrain) = context vector

    Tension determines generation sharpness:
      High tension = Sharp and confident generation
      Low tension = Blurry and average generation
    """

    def __init__(self, input_dim=784, latent_dim=16):
        super().__init__()
        self.input_dim = input_dim
        self.latent_dim = latent_dim

        # Shared encoder
        self.shared_encoder = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
        )

        # 4 engine encoders (branch from shared encoder output)
        self.engine_a_enc = EngineEncoder(128, latent_dim, 'A')  # Generate
        self.engine_g_enc = EngineEncoder(128, latent_dim, 'G')  # Calibrate
        self.engine_e_enc = EngineEncoder(128, latent_dim, 'E')  # Explore
        self.engine_f_enc = EngineEncoder(128, latent_dim, 'F')  # Constrain

        # Repulsion force → latent distribution mapping
        self.content_mu = nn.Linear(latent_dim, latent_dim)
        self.content_logvar = nn.Linear(latent_dim, latent_dim)
        self.structure_mu = nn.Linear(latent_dim, latent_dim)
        self.structure_logvar = nn.Linear(latent_dim, latent_dim)

        # Decoder: latent_dim*2 (content + structure) → image
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim * 2, 128),
            nn.ReLU(),
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Linear(256, input_dim),
            nn.Sigmoid(),
        )

        # Tension scale (learnable, initial value 1/3 = meta fixed point)
        self.tension_scale = nn.Parameter(torch.tensor(1 / 3))

        # Monitoring
        self.tension_content = 0.0
        self.tension_structure = 0.0

    def encode(self, x):
        """Encode input to latent space.

        Returns:
            mu_content, logvar_content: Content axis distribution
            mu_structure, logvar_structure: Structure axis distribution
            tension_content, tension_structure: Tension of each axis
        """
        h = self.shared_encoder(x)

        # Latent representations of 4 engines
        mu_a, logvar_a, _ = self.engine_a_enc(h)
        mu_g, logvar_g, _ = self.engine_g_enc(h)
        mu_e, logvar_e, _ = self.engine_e_enc(h)
        mu_f, logvar_f, _ = self.engine_f_enc(h)

        # Repulsion force = difference between two engine mus (meaning vector)
        repulsion_content = mu_a - mu_g      # Content axis repulsion
        repulsion_structure = mu_e - mu_f    # Structure axis repulsion

        # Tension = magnitude of repulsion
        t_content = (repulsion_content ** 2).sum(dim=-1, keepdim=True)
        t_structure = (repulsion_structure ** 2).sum(dim=-1, keepdim=True)

        # Equilibrium of repulsion force → mu of latent distribution
        # Equilibrium = average of two poles, repulsion force provides direction
        content_eq = (mu_a + mu_g) / 2
        structure_eq = (mu_e + mu_f) / 2

        mu_content = self.content_mu(content_eq + self.tension_scale * repulsion_content)
        logvar_content = self.content_logvar(content_eq)
        mu_structure = self.structure_mu(structure_eq + self.tension_scale * repulsion_structure)
        logvar_structure = self.structure_logvar(structure_eq)

        return (mu_content, logvar_content,
                mu_structure, logvar_structure,
                t_content, t_structure)

    def reparameterize(self, mu, logvar):
        """Reparameterization trick."""
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z, tension=None):
        """Decode latent vector to image.

        Args:
            z: (batch, latent_dim*2) latent vector
            tension: Tension scale. If None, use default.
        """
        out = self.decoder(z)

        if tension is not None:
            # High tension makes output sharper (increased contrast)
            # Reapply sigmoid to maintain 0-1 range
            sharpness = 1.0 + tension * 2.0
            out = torch.sigmoid((out - 0.5) * sharpness)

        return out

    def forward(self, x):
        """Forward pass: encoding → reparameterization → decoding."""
        (mu_c, logvar_c, mu_s, logvar_s,
         t_content, t_structure) = self.encode(x)

        z_content = self.reparameterize(mu_c, logvar_c)
        z_structure = self.reparameterize(mu_s, logvar_s)
        z = torch.cat([z_content, z_structure], dim=-1)

        recon = self.decode(z)

        # Monitoring
        with torch.no_grad():
            self.tension_content = t_content.mean().item()
            self.tension_structure = t_structure.mean().item()

        return recon, mu_c, logvar_c, mu_s, logvar_s

    def generate(self, n_samples=1, tension_level=None, device='cpu'):
        """Generate new images.

        Args:
            n_samples: Number of images to generate
            tension_level: Tension level (None=default, float=specified)
            device: Device
        """
        z = torch.randn(n_samples, self.latent_dim * 2, device=device)

        if tension_level is not None:
            # Scale latent vector proportionally to tension
            z = z * tension_level

        return self.decode(z, tension=tension_level)

    def interpolate(self, x1, x2, steps=7, axis='content'):
        """Interpolate between two inputs.

        Args:
            x1, x2: Input images (batch=1)
            steps: Number of interpolation steps
            axis: 'content' (content axis) or 'structure' (structure axis)
        """
        (mu_c1, _, mu_s1, _, _, _) = self.encode(x1)
        (mu_c2, _, mu_s2, _, _, _) = self.encode(x2)

        results = []
        for i in range(steps):
            alpha = i / (steps - 1)

            if axis == 'content':
                # Interpolate content only, fix structure to x1
                mu_c = (1 - alpha) * mu_c1 + alpha * mu_c2
                mu_s = mu_s1
            elif axis == 'structure':
                # Interpolate structure only, fix content to x1
                mu_c = mu_c1
                mu_s = (1 - alpha) * mu_s1 + alpha * mu_s2
            else:
                # Interpolate both axes simultaneously
                mu_c = (1 - alpha) * mu_c1 + alpha * mu_c2
                mu_s = (1 - alpha) * mu_s1 + alpha * mu_s2

            z = torch.cat([mu_c, mu_s], dim=-1)
            recon = self.decode(z)
            results.append(recon)

        return results


# ─────────────────────────────────────────
# VAE Loss Function
# ─────────────────────────────────────────

def vae_loss(recon, target, mu_c, logvar_c, mu_s, logvar_s, beta=1.0):
    """VAE loss = reconstruction loss + beta * KL divergence.

    Args:
        recon: Reconstructed image
        target: Original image
        mu_c, logvar_c: Content axis distribution parameters
        mu_s, logvar_s: Structure axis distribution parameters
        beta: KL weight (beta-VAE)
    """
    # Reconstruction loss: Binary Cross Entropy
    recon_loss = F.binary_cross_entropy(recon, target, reduction='sum')

    # KL divergence: content + structure
    kl_content = -0.5 * torch.sum(1 + logvar_c - mu_c.pow(2) - logvar_c.exp())
    kl_structure = -0.5 * torch.sum(1 + logvar_s - mu_s.pow(2) - logvar_s.exp())

    kl = kl_content + kl_structure

    return recon_loss + beta * kl, recon_loss, kl


# ─────────────────────────────────────────
# Training Loop
# ─────────────────────────────────────────

def train_vae(model, train_loader, epochs=20, lr=1e-3, beta=1.0, verbose=True):
    """Train VAE.

    Beta schedule: Linear increase from 0 to target value over first 5 epochs.
    (KL annealing — focus on reconstruction initially)
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    history = {
        'total_loss': [], 'recon_loss': [], 'kl_loss': [],
        'tension_content': [], 'tension_structure': [],
    }

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        total_recon = 0
        total_kl = 0
        n_samples = 0

        # KL annealing: linear increase over 5 epochs
        beta_current = min(beta, beta * (epoch + 1) / 5)

        for X, _ in train_loader:
            X = X.view(X.size(0), -1)
            # Inverse MNIST normalization: (x - 0.1307) / 0.3081 → x
            # Need 0-1 range to compare with sigmoid output
            X_target = X * 0.3081 + 0.1307
            X_target = X_target.clamp(0, 1)

            optimizer.zero_grad()
            recon, mu_c, logvar_c, mu_s, logvar_s = model(X)

            loss, recon_l, kl_l = vae_loss(
                recon, X_target, mu_c, logvar_c, mu_s, logvar_s, beta_current
            )

            loss.backward()
            optimizer.step()

            batch_size = X.size(0)
            total_loss += loss.item()
            total_recon += recon_l.item()
            total_kl += kl_l.item()
            n_samples += batch_size

        avg_loss = total_loss / n_samples
        avg_recon = total_recon / n_samples
        avg_kl = total_kl / n_samples

        history['total_loss'].append(avg_loss)
        history['recon_loss'].append(avg_recon)
        history['kl_loss'].append(avg_kl)
        history['tension_content'].append(model.tension_content)
        history['tension_structure'].append(model.tension_structure)

        if verbose and ((epoch + 1) % 2 == 0 or epoch == 0):
            print(f'    Epoch {epoch+1:>2}/{epochs}: '
                  f'Loss={avg_loss:.2f}  Recon={avg_recon:.2f}  KL={avg_kl:.2f}  '
                  f'beta={beta_current:.3f}  '
                  f'T_c={model.tension_content:.2f}  T_s={model.tension_structure:.2f}')

    return history


# ─────────────────────────────────────────
# Simple Classifier (for evaluating generation)
# ─────────────────────────────────────────

class SimpleClassifier(nn.Module):
    """Simple classifier to identify digits in generated images."""
    def __init__(self, input_dim=784, hidden_dim=128, output_dim=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.net(x)


def train_classifier(model, train_loader, epochs=5):
    """Train classifier."""
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            loss = criterion(model(X), y)
            loss.backward()
            optimizer.step()

    model.eval()
    return model


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────

def main():
    print()
    print('=' * 65)
    print('   logout -- RepulsionFieldVAE: Generative Engine')
    print('   The field between engines IS the generative space')
    print('=' * 65)

    # ── Load data ──
    print('\n[1] Loading MNIST...')
    train_loader, test_loader = load_mnist(batch_size=128)

    # ── Create model ──
    latent_dim = 16
    model = RepulsionFieldVAE(input_dim=784, latent_dim=latent_dim)
    n_params = count_params(model)
    print(f'    RepulsionFieldVAE: {n_params:,} parameters')
    print(f'    Latent dim: {latent_dim} x 2 axes = {latent_dim * 2} total')
    print(f'    Content axis: A(generate) <-repulsion-> G(correct)')
    print(f'    Structure axis: E(explore) <-repulsion-> F(constrain)')

    # ── Training ──
    print(f'\n[2] Training (20 epochs, KL annealing)...')
    history = train_vae(model, train_loader, epochs=20, lr=1e-3, beta=1.0)

    print(f'\n    Final: Recon={history["recon_loss"][-1]:.2f}  '
          f'KL={history["kl_loss"][-1]:.2f}')
    print(f'    Tension scale (learned): {model.tension_scale.item():.4f} '
          f'(init=1/3={1/3:.4f})')

    # ── Reconstruction quality ──
    print(f'\n[3] Reconstruction quality...')
    model.eval()

    test_iter = iter(test_loader)
    X_test, y_test = next(test_iter)
    X_flat = X_test.view(X_test.size(0), -1)
    X_target = X_flat * 0.3081 + 0.1307
    X_target = X_target.clamp(0, 1)

    with torch.no_grad():
        recon, _, _, _, _ = model(X_flat)

    # Display 5 samples
    n_show = 5
    print('\n    Original:')
    show_ascii_grid(
        [X_target[i].view(28, 28) for i in range(n_show)],
        [f'y={y_test[i].item()}' for i in range(n_show)],
        cols=n_show,
    )
    print('    Reconstructed:')
    show_ascii_grid(
        [recon[i].view(28, 28) for i in range(n_show)],
        [f'y={y_test[i].item()}' for i in range(n_show)],
        cols=n_show,
    )

    # ── Tension-controlled generation ──
    print(f'\n[4] Tension-controlled generation...')
    tension_levels = [0.1, 0.3, 1 / math.e, 0.7, 1.5]
    tension_labels = ['T=0.1', 'T=0.3', f'T=1/e', 'T=0.7', 'T=1.5']

    print('    Low tension  = safe, average, boring')
    print('    1/e tension  = golden zone (balanced, meaningful)')
    print('    High tension = wild, novel, possibly incoherent')
    print()

    for t_val, t_label in zip(tension_levels, tension_labels):
        with torch.no_grad():
            generated = model.generate(n_samples=5, tension_level=t_val)
        print(f'    {t_label} (tension={t_val:.4f}):')
        show_ascii_grid(
            [generated[i].view(28, 28) for i in range(5)],
            [f'#{i+1}' for i in range(5)],
            cols=5,
        )

    # ── Semantic axis exploration (content interpolation) ──
    print(f'\n[5] Content axis exploration (meaning morphing)...')
    print('    Interpolating CONTENT while keeping STRUCTURE fixed')
    print('    This shows how one concept becomes another\n')

    # Find two different digits (3 and 8)
    digit_a, digit_b = 3, 8
    idx_a = idx_b = None
    for i in range(len(y_test)):
        if y_test[i].item() == digit_a and idx_a is None:
            idx_a = i
        if y_test[i].item() == digit_b and idx_b is None:
            idx_b = i
        if idx_a is not None and idx_b is not None:
            break

    if idx_a is not None and idx_b is not None:
        x1 = X_flat[idx_a:idx_a + 1]
        x2 = X_flat[idx_b:idx_b + 1]

        with torch.no_grad():
            interp = model.interpolate(x1, x2, steps=7, axis='content')

        print(f'    {digit_a} --> {digit_b} (content axis, 7 steps):')
        labels = [f'{digit_a}'] + [f'{i+1}/5' for i in range(5)] + [f'{digit_b}']
        show_ascii_grid(
            [img.view(28, 28) for img in interp],
            labels,
            cols=7,
        )

    # ── Context axis exploration (structure interpolation) ──
    print(f'\n[6] Structure axis exploration (style morphing)...')
    print('    Interpolating STRUCTURE while keeping CONTENT fixed')
    print('    Same digit, different handwriting style\n')

    # Find 2 samples of same digit with different styles
    target_digit = 7
    indices = [i for i in range(len(y_test)) if y_test[i].item() == target_digit]

    if len(indices) >= 2:
        # Select two most different samples (based on L2 distance)
        idx1 = indices[0]
        max_dist = 0
        idx2 = indices[1]
        for j in indices[1:min(len(indices), 50)]:
            dist = (X_flat[idx1] - X_flat[j]).pow(2).sum().item()
            if dist > max_dist:
                max_dist = dist
                idx2 = j

        x1 = X_flat[idx1:idx1 + 1]
        x2 = X_flat[idx2:idx2 + 1]

        with torch.no_grad():
            interp = model.interpolate(x1, x2, steps=7, axis='structure')

        print(f'    Digit {target_digit}, style A --> style B (structure axis, 7 steps):')
        labels = ['A'] + [f'{i+1}/5' for i in range(5)] + ['B']
        show_ascii_grid(
            [img.view(28, 28) for img in interp],
            labels,
            cols=7,
        )

    # ── Dreaming mode ──
    print(f'\n[7] Dreaming mode (random latent sampling)...')
    print('    No input -- the engine imagines\n')

    # Train classifier (for evaluating generation results)
    print('    Training classifier for dream analysis...')
    classifier = SimpleClassifier()
    classifier = train_classifier(classifier, train_loader, epochs=5)

    dream_tensions = [0.3, 1 / math.e, 0.8]
    dream_labels_t = ['calm', 'golden', 'vivid']

    for t_val, t_name in zip(dream_tensions, dream_labels_t):
        n_dreams = 100
        with torch.no_grad():
            dreams = model.generate(n_samples=n_dreams, tension_level=t_val)
            logits = classifier(dreams)
            predicted = logits.argmax(dim=-1)

        # Calculate distribution
        counts = torch.zeros(10)
        for d in range(10):
            counts[d] = (predicted == d).sum().item()

        # Display top 5
        show_dreams = model.generate(n_samples=5, tension_level=t_val)
        print(f'    Dream ({t_name}, T={t_val:.3f}):')
        show_ascii_grid(
            [show_dreams[i].view(28, 28) for i in range(5)],
            [f'#{i+1}' for i in range(5)],
            cols=5,
        )

        # Distribution bar chart
        max_count = counts.max().item()
        print(f'    Digit distribution (n={n_dreams}):')
        for d in range(10):
            bar_len = int(counts[d].item() / max(max_count, 1) * 20)
            bar = '#' * bar_len
            print(f'      {d}: {bar:<20} ({int(counts[d].item()):>3})')
        print()

    # ── Latent space analysis ──
    print(f'\n[8] Latent space analysis...')
    print('    Encoding full test set...\n')

    model.eval()
    all_mu_c = []
    all_mu_s = []
    all_tension_c = []
    all_tension_s = []
    all_labels = []

    with torch.no_grad():
        for X_batch, y_batch in test_loader:
            X_batch = X_batch.view(X_batch.size(0), -1)
            mu_c, _, mu_s, _, t_c, t_s = model.encode(X_batch)
            all_mu_c.append(mu_c)
            all_mu_s.append(mu_s)
            all_tension_c.append(t_c)
            all_tension_s.append(t_s)
            all_labels.append(y_batch)

    all_mu_c = torch.cat(all_mu_c, dim=0)
    all_mu_s = torch.cat(all_mu_s, dim=0)
    all_tension_c = torch.cat(all_tension_c, dim=0).squeeze()
    all_tension_s = torch.cat(all_tension_s, dim=0).squeeze()
    all_labels = torch.cat(all_labels, dim=0)

    # Per-digit average tension
    print('    Per-digit average tension:')
    print(f'    {"Digit":>5}  {"T_content":>10}  {"T_structure":>12}  {"Total":>8}')
    print(f'    {"-"*5}  {"-"*10}  {"-"*12}  {"-"*8}')

    digit_tensions = {}
    for d in range(10):
        mask = all_labels == d
        tc = all_tension_c[mask].mean().item()
        ts = all_tension_s[mask].mean().item()
        total = tc + ts
        digit_tensions[d] = (tc, ts, total)
        print(f'    {d:>5}  {tc:>10.2f}  {ts:>12.2f}  {total:>8.2f}')

    # Highest/lowest tension digits
    sorted_by_total = sorted(digit_tensions.items(), key=lambda x: x[1][2])
    print(f'\n    Lowest tension  (easiest): digit {sorted_by_total[0][0]} '
          f'(T={sorted_by_total[0][1][2]:.2f})')
    print(f'    Highest tension (hardest): digit {sorted_by_total[-1][0]} '
          f'(T={sorted_by_total[-1][1][2]:.2f})')

    # Inter-digit latent space distances (content vs structure)
    print(f'\n    Inter-digit distances (content axis):')
    centroids_c = torch.zeros(10, latent_dim)
    centroids_s = torch.zeros(10, latent_dim)
    for d in range(10):
        mask = all_labels == d
        centroids_c[d] = all_mu_c[mask].mean(dim=0)
        centroids_s[d] = all_mu_s[mask].mean(dim=0)

    # Closest/farthest digit pairs (content axis)
    min_dist_c = float('inf')
    max_dist_c = 0
    closest_c = (0, 0)
    farthest_c = (0, 0)

    for i in range(10):
        for j in range(i + 1, 10):
            dist = (centroids_c[i] - centroids_c[j]).pow(2).sum().sqrt().item()
            if dist < min_dist_c:
                min_dist_c = dist
                closest_c = (i, j)
            if dist > max_dist_c:
                max_dist_c = dist
                farthest_c = (i, j)

    print(f'    Closest  (content): {closest_c[0]} <-> {closest_c[1]}  '
          f'(dist={min_dist_c:.2f})')
    print(f'    Farthest (content): {farthest_c[0]} <-> {farthest_c[1]}  '
          f'(dist={max_dist_c:.2f})')

    # Structure axis
    min_dist_s = float('inf')
    max_dist_s = 0
    closest_s = (0, 0)
    farthest_s = (0, 0)

    for i in range(10):
        for j in range(i + 1, 10):
            dist = (centroids_s[i] - centroids_s[j]).pow(2).sum().sqrt().item()
            if dist < min_dist_s:
                min_dist_s = dist
                closest_s = (i, j)
            if dist > max_dist_s:
                max_dist_s = dist
                farthest_s = (i, j)

    print(f'    Closest  (structure): {closest_s[0]} <-> {closest_s[1]}  '
          f'(dist={min_dist_s:.2f})')
    print(f'    Farthest (structure): {farthest_s[0]} <-> {farthest_s[1]}  '
          f'(dist={max_dist_s:.2f})')

    # ── Training curve ──
    print(f'\n[9] Training curve (ASCII):')
    recon_losses = history['recon_loss']
    kl_losses = history['kl_loss']

    max_val = max(recon_losses)
    chart_height = 10
    chart_width = len(recon_losses)

    print(f'\n    Reconstruction loss:')
    for row in range(chart_height, 0, -1):
        threshold = max_val * row / chart_height
        line = '    '
        if row == chart_height:
            line += f'{max_val:>6.1f} |'
        elif row == 1:
            line += f'{max_val/chart_height:>6.1f} |'
        else:
            line += '       |'
        for epoch in range(chart_width):
            if recon_losses[epoch] >= threshold:
                line += '#'
            else:
                line += ' '
        print(line)
    print(f'       +{"=" * chart_width}')
    print(f'        {"Epoch 1":<{chart_width//2}}{"Epoch " + str(chart_width):>{chart_width//2}}')

    # ── Summary ──
    print(f'\n{"=" * 65}')
    print(f'   Summary')
    print(f'{"=" * 65}')
    print(f'   Parameters:          {n_params:,}')
    print(f'   Final recon loss:    {history["recon_loss"][-1]:.2f}')
    print(f'   Final KL loss:       {history["kl_loss"][-1]:.2f}')
    print(f'   Tension scale:       {model.tension_scale.item():.4f} (1/3={1/3:.4f})')
    print(f'   Content tension:     {history["tension_content"][-1]:.2f}')
    print(f'   Structure tension:   {history["tension_structure"][-1]:.2f}')
    print(f'')
    print(f'   Key insight: the repulsion field between engines')
    print(f'   forms a structured latent space where:')
    print(f'     Content axis (A vs G) = WHAT to generate')
    print(f'     Structure axis (E vs F) = HOW to generate it')
    print(f'     Tension = creativity control')
    print(f'{"=" * 65}')
    print()


if __name__ == '__main__':
    main()