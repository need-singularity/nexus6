#!/usr/bin/env python3
"""Identity-Conditioned Dreaming Experiment

Does identity change what you dream?

If two models have different identities but the same generative architecture,
do they dream different things?

Design:
  1. Train a RepulsionFieldVAE on MNIST (20 epochs) -- shared "brain structure"
  2. Train two TemporalContinuityEngines with different seeds -> two identity_vectors
  3. Inject each identity into the VAE decoder via latent-space bias:
       z_conditioned = z + scale * identity_projection(identity_vector)
  4. Dream with same random seeds but different identities
  5. Compare: ASCII grids, digit distributions, pixel differences, classification
  6. Interpolate between identities and show morphing dreams

Core idea:
  The VAE is the shared biological substrate (brain anatomy).
  The identity_vector is "who you are" -- shaped by experience.
  Same brain + different identity = different dreams?
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import time

from model_utils import load_mnist, count_params
from model_generative_engine import (
    RepulsionFieldVAE, vae_loss, train_vae,
    SimpleClassifier, train_classifier,
    tensor_to_ascii, show_ascii_grid,
)
from model_temporal_engine import TemporalContinuityEngine


# ─────────────────────────────────────────
# Identity Projection Layer
# ─────────────────────────────────────────

class IdentityProjection(nn.Module):
    """Projects an identity vector into the VAE latent space.

    identity_vector (state_dim=32) -> latent_dim*2 (content + structure)

    This is the bridge between "who you are" and "what you dream".
    """
    def __init__(self, identity_dim=32, latent_dim=16):
        super().__init__()
        self.proj = nn.Sequential(
            nn.Linear(identity_dim, 64),
            nn.Tanh(),
            nn.Linear(64, latent_dim * 2),
            nn.Tanh(),
        )

    def forward(self, identity):
        return self.proj(identity)


# ─────────────────────────────────────────
# Identity-Conditioned Dreaming
# ─────────────────────────────────────────

def condition_latent(z, identity_vector, projection, scale=0.5):
    """Add identity bias to latent vector.

    z_conditioned = z + scale * projection(identity_vector)

    Args:
        z: (batch, latent_dim*2) latent noise
        identity_vector: (1, state_dim) identity from TemporalContinuityEngine
        projection: IdentityProjection layer
        scale: how strongly identity influences the dream
    """
    identity_bias = projection(identity_vector)  # (1, latent_dim*2)
    identity_bias = identity_bias.expand(z.size(0), -1)
    return z + scale * identity_bias


def dream_with_identity(vae, projection, identity_vector, z_noise,
                        scale=0.5, tension=None):
    """Generate dreams conditioned on a specific identity.

    Same noise + different identity = different dream.
    """
    z_conditioned = condition_latent(z_noise, identity_vector, projection, scale)
    return vae.decode(z_conditioned, tension=tension)


# ─────────────────────────────────────────
# Build Identity Vectors
# ─────────────────────────────────────────

def build_identity(train_loader, seed, state_dim=32, epochs=3, label=""):
    """Train a TemporalContinuityEngine to develop an identity.

    Different seeds -> different weight initialization -> different identity_vectors.
    We only need a few epochs to develop a distinct identity.
    """
    torch.manual_seed(seed)
    np.random.seed(seed)

    engine = TemporalContinuityEngine(
        input_dim=784, hidden_dim=48, output_dim=10,
        state_dim=state_dim, n_self_ref_steps=3,
        contraction_coeff=0.7, identity_momentum=0.95,  # faster identity formation
    )

    optimizer = torch.optim.Adam(engine.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()

    print(f"    Training {label} (seed={seed})...")
    for epoch in range(epochs):
        engine.train()
        total_loss = 0
        n_batches = 0
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            out, aux = engine(X)
            loss = criterion(out, y) + 0.01 * aux
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            n_batches += 1
        avg = total_loss / n_batches
        if epoch == 0 or epoch == epochs - 1:
            print(f"      Epoch {epoch+1}/{epochs}: loss={avg:.4f}")

    identity = engine.identity_vector.detach().clone()  # (1, state_dim)
    print(f"      Identity norm: {identity.norm().item():.4f}")
    print(f"      Identity hash: {identity.sum().item():.6f}")  # quick fingerprint
    return identity, engine


def train_identity_projection(vae, projection, train_loader, epochs=5, scale=0.5):
    """Fine-tune the projection layer so identity conditioning works well.

    We train projection to reconstruct training images when given:
      z = encode(x) + scale * projection(random_identity)

    The projection must learn to add meaningful bias without destroying quality.
    """
    # Use a fixed random identity for training (projection just needs to be functional)
    dummy_id = torch.randn(1, 32) * 0.1

    optimizer = torch.optim.Adam(projection.parameters(), lr=1e-3)

    print("    Fine-tuning identity projection layer...")
    for epoch in range(epochs):
        total_loss = 0
        n_samples = 0
        for X, _ in train_loader:
            X = X.view(X.size(0), -1)
            X_target = X * 0.3081 + 0.1307
            X_target = X_target.clamp(0, 1)

            # Encode
            with torch.no_grad():
                mu_c, logvar_c, mu_s, logvar_s, _, _ = vae.encode(X)
                z_content = mu_c  # use mean (no sampling) for stability
                z_structure = mu_s
                z = torch.cat([z_content, z_structure], dim=-1)

            # Add identity conditioning
            z_cond = condition_latent(z, dummy_id, projection, scale)

            # Decode (only projection is trainable)
            recon = vae.decode(z_cond)

            loss = F.binary_cross_entropy(recon, X_target, reduction='sum')

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            n_samples += X.size(0)

        if epoch == 0 or epoch == epochs - 1:
            print(f"      Epoch {epoch+1}/{epochs}: recon_loss={total_loss/n_samples:.2f}")


# ─────────────────────────────────────────
# Analysis Functions
# ─────────────────────────────────────────

def classify_dreams(dreams, classifier):
    """Classify a batch of dream images."""
    with torch.no_grad():
        logits = classifier(dreams)
        return logits.argmax(dim=-1)


def digit_distribution(predictions, n_digits=10):
    """Count digit occurrences."""
    counts = torch.zeros(n_digits)
    for d in range(n_digits):
        counts[d] = (predictions == d).sum().item()
    return counts


def pixel_difference(dreams_a, dreams_b):
    """Mean absolute pixel difference between two dream sets."""
    return (dreams_a - dreams_b).abs().mean().item()


def distribution_divergence(dist_a, dist_b):
    """Jensen-Shannon divergence between two distributions."""
    p = dist_a / dist_a.sum()
    q = dist_b / dist_b.sum()
    m = 0.5 * (p + q)

    # Avoid log(0)
    eps = 1e-8
    p = p + eps
    q = q + eps
    m = m + eps

    kl_pm = (p * (p / m).log()).sum().item()
    kl_qm = (q * (q / m).log()).sum().item()
    return 0.5 * (kl_pm + kl_qm)


def print_distribution_table(distributions, labels, n_digits=10):
    """Print a comparison table of digit distributions."""
    # Header
    header = f"  {'Digit':>5}"
    for label in labels:
        header += f"  {label:>8}"
    print(header)
    print("  " + "-" * (7 + 10 * len(labels)))

    for d in range(n_digits):
        row = f"  {d:>5}"
        for dist in distributions:
            count = int(dist[d].item())
            pct = dist[d].item() / max(dist.sum().item(), 1) * 100
            row += f"  {count:>3}({pct:>3.0f}%)"
        print(row)

    # Totals
    row = f"  {'Total':>5}"
    for dist in distributions:
        row += f"  {int(dist.sum().item()):>8}"
    print(row)


def print_bar_chart(distribution, label, bar_width=30):
    """Print a horizontal bar chart of digit distribution."""
    total = max(distribution.sum().item(), 1)
    max_count = max(distribution.max().item(), 1)

    print(f"\n  {label} (n={int(total)}):")
    for d in range(10):
        count = distribution[d].item()
        pct = count / total * 100
        bar_len = int(count / max_count * bar_width)
        bar = "#" * bar_len
        print(f"    {d}: {bar:<{bar_width}} {int(count):>3} ({pct:>4.1f}%)")


def ascii_difference_grid(dreams_a, dreams_b, labels_a, labels_b, n_show=5):
    """Show pixel-wise difference between two dream sets."""
    chars = ' .:-=+*#%@'
    diffs = (dreams_a[:n_show] - dreams_b[:n_show]).abs()

    print(f"  Pixel difference: {labels_a} vs {labels_b}")
    diff_imgs = [diffs[i].view(28, 28) for i in range(n_show)]
    diff_labels = [f"|A-B|#{i}" for i in range(n_show)]
    show_ascii_grid(diff_imgs, diff_labels, cols=n_show)

    avg_diff = diffs.mean().item()
    max_diff = diffs.max().item()
    print(f"  Mean |diff|: {avg_diff:.4f}   Max |diff|: {max_diff:.4f}")


# ─────────────────────────────────────────
# Main Experiment
# ─────────────────────────────────────────

def main():
    print()
    print("=" * 70)
    print("   Identity-Conditioned Dreaming Experiment")
    print("   Does identity change what you dream?")
    print("=" * 70)

    t_start = time.time()

    # ── 1. Load data ──
    print("\n[1] Loading MNIST...")
    train_loader, test_loader = load_mnist(batch_size=128)

    # ── 2. Train shared brain (RepulsionFieldVAE) ──
    print("\n[2] Training shared brain (RepulsionFieldVAE, 20 epochs)...")
    torch.manual_seed(42)
    vae = RepulsionFieldVAE(input_dim=784, latent_dim=16)
    print(f"    Parameters: {count_params(vae):,}")
    history = train_vae(vae, train_loader, epochs=20, lr=1e-3, beta=1.0)
    print(f"    Final: Recon={history['recon_loss'][-1]:.2f}  KL={history['kl_loss'][-1]:.2f}")
    vae.eval()

    # Quick sanity check: can VAE reconstruct?
    test_iter = iter(test_loader)
    X_test, y_test = next(test_iter)
    X_flat = X_test.view(X_test.size(0), -1)
    X_target = (X_flat * 0.3081 + 0.1307).clamp(0, 1)

    with torch.no_grad():
        recon, _, _, _, _ = vae(X_flat)

    print("\n    Reconstruction sanity check:")
    print("    Original:")
    show_ascii_grid(
        [X_target[i].view(28, 28) for i in range(5)],
        [f"y={y_test[i].item()}" for i in range(5)],
        cols=5,
    )
    print("    Reconstructed:")
    show_ascii_grid(
        [recon[i].view(28, 28) for i in range(5)],
        [f"y={y_test[i].item()}" for i in range(5)],
        cols=5,
    )

    # ── 3. Build two different identities ──
    print("\n[3] Building two identities (Alpha and Beta)...")
    identity_alpha, engine_alpha = build_identity(
        train_loader, seed=7, state_dim=32, epochs=3, label="Alpha"
    )
    identity_beta, engine_beta = build_identity(
        train_loader, seed=1337, state_dim=32, epochs=3, label="Beta"
    )

    # Identity analysis
    cos_sim = F.cosine_similarity(identity_alpha, identity_beta).item()
    l2_dist = (identity_alpha - identity_beta).norm().item()
    print(f"\n    Identity comparison:")
    print(f"      Cosine similarity:  {cos_sim:.4f}")
    print(f"      L2 distance:        {l2_dist:.4f}")
    print(f"      Alpha norm:         {identity_alpha.norm().item():.4f}")
    print(f"      Beta norm:          {identity_beta.norm().item():.4f}")

    if abs(cos_sim) > 0.95:
        print("      WARNING: Identities are very similar. Dreams may look alike.")
    else:
        print("      Identities are distinct. Dreams should differ.")

    # ── 4. Identity projection layer ──
    print("\n[4] Training identity projection layer...")
    projection = IdentityProjection(identity_dim=32, latent_dim=16)

    # Freeze VAE, only train projection
    for p in vae.parameters():
        p.requires_grad = False

    train_identity_projection(vae, projection, train_loader, epochs=5, scale=0.5)

    for p in vae.parameters():
        p.requires_grad = True

    projection.eval()

    # ── 5. Train classifier for dream analysis ──
    print("\n[5] Training digit classifier for dream analysis...")
    classifier = SimpleClassifier()
    classifier = train_classifier(classifier, train_loader, epochs=5)
    classifier.eval()

    # Evaluate classifier
    correct = 0
    total = 0
    with torch.no_grad():
        for X_b, y_b in test_loader:
            X_b = X_b.view(X_b.size(0), -1)
            preds = classifier(X_b).argmax(dim=-1)
            correct += (preds == y_b).sum().item()
            total += y_b.size(0)
    print(f"    Classifier accuracy: {correct/total*100:.1f}%")

    # ══════════════════════════════════════════
    # EXPERIMENT: Dream with different identities
    # ══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("   EXPERIMENT: Same Brain, Different Identity, Different Dreams?")
    print("=" * 70)

    # Fixed latent noise -- same "dream seeds" for all identities
    n_dreams = 200
    n_show = 8
    dream_scale = 0.5
    dream_tension = 1 / math.e  # golden zone

    torch.manual_seed(999)
    z_noise = torch.randn(n_dreams, 16 * 2)

    # Zero identity (no conditioning)
    identity_zero = torch.zeros(1, 32)
    # Random identity
    torch.manual_seed(12345)
    identity_random = torch.randn(1, 32) * 0.1

    identities = {
        "Alpha":  identity_alpha,
        "Beta":   identity_beta,
        "Zero":   identity_zero,
        "Random": identity_random,
    }

    # ── 6. Generate dreams ──
    print(f"\n[6] Dreaming (n={n_dreams}, tension=1/e, scale={dream_scale})...")

    all_dreams = {}
    all_predictions = {}
    all_distributions = {}

    for name, identity in identities.items():
        with torch.no_grad():
            dreams = dream_with_identity(
                vae, projection, identity, z_noise,
                scale=dream_scale, tension=dream_tension,
            )
            preds = classify_dreams(dreams, classifier)
            dist = digit_distribution(preds)

        all_dreams[name] = dreams
        all_predictions[name] = preds
        all_distributions[name] = dist
        print(f"    {name:>6}: generated {n_dreams} dreams")

    # ── 7. Visual comparison ──
    print("\n" + "-" * 70)
    print("  [7] Visual Comparison: Same seed, different identity")
    print("-" * 70)

    for name in identities:
        print(f"\n    {name} dreams:")
        show_ascii_grid(
            [all_dreams[name][i].view(28, 28) for i in range(n_show)],
            [f"#{i}" for i in range(n_show)],
            cols=n_show,
        )

    # ── 8. Digit distributions ──
    print("\n" + "-" * 70)
    print("  [8] Digit Distribution per Identity")
    print("-" * 70)

    dist_list = [all_distributions[name] for name in identities]
    dist_labels = list(identities.keys())
    print()
    print_distribution_table(dist_list, dist_labels)

    for name in identities:
        print_bar_chart(all_distributions[name], f"{name} Identity")

    # ── 9. Pixel-level differences ──
    print("\n" + "-" * 70)
    print("  [9] Pixel-Level Differences Between Identities")
    print("-" * 70)

    pairs = [
        ("Alpha", "Beta"),
        ("Alpha", "Zero"),
        ("Beta", "Zero"),
        ("Alpha", "Random"),
    ]

    print("\n  Pairwise mean |pixel difference|:")
    print(f"  {'Pair':<20} {'Mean |diff|':>12} {'Max |diff|':>12}")
    print("  " + "-" * 46)

    for name_a, name_b in pairs:
        diff = pixel_difference(all_dreams[name_a], all_dreams[name_b])
        max_diff = (all_dreams[name_a] - all_dreams[name_b]).abs().max().item()
        print(f"  {name_a + ' vs ' + name_b:<20} {diff:>12.6f} {max_diff:>12.6f}")

    # Visual diff for Alpha vs Beta
    print("\n    Alpha vs Beta difference maps (bright = more different):")
    ascii_difference_grid(
        all_dreams["Alpha"], all_dreams["Beta"],
        "Alpha", "Beta", n_show=5,
    )

    # ── 10. Distribution divergence ──
    print("\n" + "-" * 70)
    print("  [10] Distribution Divergence (Jensen-Shannon)")
    print("-" * 70)

    print(f"\n  {'Pair':<20} {'JS Divergence':>14}")
    print("  " + "-" * 36)

    all_names = list(identities.keys())
    for i in range(len(all_names)):
        for j in range(i + 1, len(all_names)):
            na, nb = all_names[i], all_names[j]
            js = distribution_divergence(all_distributions[na], all_distributions[nb])
            print(f"  {na + ' vs ' + nb:<20} {js:>14.6f}")

    # ── 11. Per-identity digit preference ──
    print("\n" + "-" * 70)
    print("  [11] Identity-Specific Digit Preferences")
    print("-" * 70)

    for name in identities:
        dist = all_distributions[name]
        total = dist.sum().item()
        if total == 0:
            continue

        probs = dist / total
        top3_vals, top3_idx = probs.topk(3)
        bot3_vals, bot3_idx = probs.topk(3, largest=False)

        print(f"\n    {name}:")
        print(f"      Most dreamed:  ", end="")
        for v, i in zip(top3_vals, top3_idx):
            print(f"digit {i.item()} ({v.item()*100:.1f}%)  ", end="")
        print()
        print(f"      Least dreamed: ", end="")
        for v, i in zip(bot3_vals, bot3_idx):
            print(f"digit {i.item()} ({v.item()*100:.1f}%)  ", end="")
        print()

    # ── 12. Same-digit comparison across identities ──
    print("\n" + "-" * 70)
    print("  [12] Same Dream Seed: How Identity Changes a Single Dream")
    print("-" * 70)

    # Pick 4 interesting seeds and show them across all identities
    seed_indices = [0, 7, 15, 42]
    for seed_idx in seed_indices:
        print(f"\n    Dream seed #{seed_idx}:")
        imgs = [all_dreams[name][seed_idx].view(28, 28) for name in identities]
        pred_labels = []
        for name in identities:
            p = all_predictions[name][seed_idx].item()
            pred_labels.append(f"{name}->d{p}")
        show_ascii_grid(imgs, pred_labels, cols=len(identities))

    # ══════════════════════════════════════════
    # 13. Identity Interpolation
    # ══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("   [13] Identity Interpolation: Alpha --> Beta")
    print("   Morphing between two identities, same dream seed")
    print("=" * 70)

    n_interp_steps = 7
    # Use a few different noise seeds
    interp_seeds = [0, 7, 15]

    for seed_idx in interp_seeds:
        z_single = z_noise[seed_idx:seed_idx+1]  # (1, 32)

        interp_imgs = []
        interp_labels = []

        for step in range(n_interp_steps):
            alpha = step / (n_interp_steps - 1)
            blended_identity = (1 - alpha) * identity_alpha + alpha * identity_beta

            with torch.no_grad():
                dream = dream_with_identity(
                    vae, projection, blended_identity, z_single,
                    scale=dream_scale, tension=dream_tension,
                )
                pred = classify_dreams(dream, classifier)

            interp_imgs.append(dream[0].view(28, 28))
            if step == 0:
                interp_labels.append(f"A(d{pred[0].item()})")
            elif step == n_interp_steps - 1:
                interp_labels.append(f"B(d{pred[0].item()})")
            else:
                interp_labels.append(f"{alpha:.1f}(d{pred[0].item()})")

        print(f"\n    Seed #{seed_idx}: Alpha ---> Beta")
        show_ascii_grid(interp_imgs, interp_labels, cols=n_interp_steps)

    # ── 14. Tension x Identity interaction ──
    print("\n" + "=" * 70)
    print("   [14] Tension x Identity: Does tension amplify identity effects?")
    print("=" * 70)

    tensions = [0.1, 0.3, 1/math.e, 0.7, 1.5]
    tension_names = ["0.1", "0.3", "1/e", "0.7", "1.5"]

    z_fixed = z_noise[:50]  # use 50 dreams

    print(f"\n  Mean pixel diff (Alpha vs Beta) at each tension level:")
    print(f"  {'Tension':>8} {'Pixel Diff':>12} {'JS Div':>12}")
    print("  " + "-" * 34)

    tension_diffs = []
    tension_js = []

    for t_val, t_name in zip(tensions, tension_names):
        with torch.no_grad():
            d_alpha = dream_with_identity(
                vae, projection, identity_alpha, z_fixed,
                scale=dream_scale, tension=t_val,
            )
            d_beta = dream_with_identity(
                vae, projection, identity_beta, z_fixed,
                scale=dream_scale, tension=t_val,
            )

            pred_a = classify_dreams(d_alpha, classifier)
            pred_b = classify_dreams(d_beta, classifier)

        px_diff = pixel_difference(d_alpha, d_beta)
        dist_a = digit_distribution(pred_a)
        dist_b = digit_distribution(pred_b)
        js = distribution_divergence(dist_a, dist_b)

        tension_diffs.append(px_diff)
        tension_js.append(js)

        print(f"  {t_name:>8} {px_diff:>12.6f} {js:>12.6f}")

    # ASCII chart: tension vs pixel difference
    print("\n  Tension vs Identity Effect (pixel difference):")
    max_diff = max(tension_diffs) if tension_diffs else 1
    for i, (t_name, diff) in enumerate(zip(tension_names, tension_diffs)):
        bar_len = int(diff / max(max_diff, 1e-8) * 40)
        bar = "#" * bar_len
        print(f"    T={t_name:>4}: {bar:<40} {diff:.6f}")

    # ── 15. Identity scale experiment ──
    print("\n" + "=" * 70)
    print("   [15] Identity Scale: How much identity is needed to change dreams?")
    print("=" * 70)

    scales = [0.0, 0.1, 0.2, 0.5, 1.0, 2.0]
    z_fixed_scale = z_noise[:50]

    print(f"\n  Pixel diff (Alpha vs Zero) at each identity scale:")
    print(f"  {'Scale':>8} {'Pixel Diff':>12} {'JS Div':>12}")
    print("  " + "-" * 34)

    for sc in scales:
        with torch.no_grad():
            d_alpha_sc = dream_with_identity(
                vae, projection, identity_alpha, z_fixed_scale,
                scale=sc, tension=dream_tension,
            )
            d_zero_sc = dream_with_identity(
                vae, projection, identity_zero, z_fixed_scale,
                scale=sc, tension=dream_tension,
            )
            pred_a = classify_dreams(d_alpha_sc, classifier)
            pred_z = classify_dreams(d_zero_sc, classifier)

        px_diff = pixel_difference(d_alpha_sc, d_zero_sc)
        js = distribution_divergence(
            digit_distribution(pred_a), digit_distribution(pred_z)
        )
        print(f"  {sc:>8.1f} {px_diff:>12.6f} {js:>12.6f}")

    # ── 16. Show scale effect visually ──
    print("\n  Visual: same seed, Alpha identity at different scales:")
    z_one = z_noise[0:1]
    scale_imgs = []
    scale_labels = []

    for sc in [0.0, 0.1, 0.5, 1.0, 2.0]:
        with torch.no_grad():
            d = dream_with_identity(
                vae, projection, identity_alpha, z_one,
                scale=sc, tension=dream_tension,
            )
            pred = classify_dreams(d, classifier)
        scale_imgs.append(d[0].view(28, 28))
        scale_labels.append(f"s={sc}(d{pred[0].item()})")

    show_ascii_grid(scale_imgs, scale_labels, cols=5)

    # ══════════════════════════════════════════
    # Summary
    # ══════════════════════════════════════════

    elapsed = time.time() - t_start

    print("\n" + "=" * 70)
    print("   SUMMARY: Identity-Conditioned Dreaming")
    print("=" * 70)

    # Key metrics
    alpha_beta_px = pixel_difference(all_dreams["Alpha"], all_dreams["Beta"])
    alpha_zero_px = pixel_difference(all_dreams["Alpha"], all_dreams["Zero"])
    beta_zero_px = pixel_difference(all_dreams["Beta"], all_dreams["Zero"])

    ab_js = distribution_divergence(all_distributions["Alpha"], all_distributions["Beta"])
    az_js = distribution_divergence(all_distributions["Alpha"], all_distributions["Zero"])

    print(f"""
  Shared brain:          RepulsionFieldVAE ({count_params(vae):,} params)
  Identity source:       TemporalContinuityEngine (state_dim=32)
  Dream noise seeds:     {n_dreams}
  Dream tension:         1/e (golden zone)
  Identity scale:        {dream_scale}

  Identity similarity:
    Cosine(Alpha, Beta):   {cos_sim:.4f}
    L2(Alpha, Beta):       {l2_dist:.4f}

  Dream differences:
    Pixel |Alpha - Beta|:  {alpha_beta_px:.6f}
    Pixel |Alpha - Zero|:  {alpha_zero_px:.6f}
    Pixel |Beta  - Zero|:  {beta_zero_px:.6f}

  Distribution divergence (JS):
    Alpha vs Beta:         {ab_js:.6f}
    Alpha vs Zero:         {az_js:.6f}

  Key finding:""")

    if alpha_beta_px > 0.001:
        print("    YES -- identity changes what you dream.")
        print("    Same brain structure + different identity = different dreams.")
        if ab_js > 0.01:
            print("    The effect is strong enough to shift digit preferences.")
        else:
            print("    The effect is subtle (pixel-level) but does not shift digit class.")
    else:
        print("    NO significant difference detected.")
        print("    Identity conditioning may need stronger projection or more training.")

    print(f"""
  Interpretation:
    The VAE is like shared human brain anatomy.
    The identity_vector is shaped by each individual's experience.
    Even with the same "dream seed" (latent noise), different identities
    produce different dreams -- just as two people with similar brains
    but different life histories dream differently.

  Time elapsed: {elapsed:.1f}s
""")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
