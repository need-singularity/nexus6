#!/usr/bin/env python3
"""Cross-Universe Repulsion: What happens when two models from completely
different "universes" (training data) are forced into a repulsion field?

Universe M: trained on MNIST (handwritten digits) — 784-dim input
Universe C: trained on CIFAR-10 (real photos) — 3072-dim input

They have NEVER seen each other's data. Completely alien to each other.

We project both into a shared latent space and measure what happens
when their frozen outputs are combined through a learned field transform.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import time
import sys

from model_utils import load_mnist, load_cifar10, count_params


# ─────────────────────────────────────────
# Universe Encoder + Pole (classifier head)
# ─────────────────────────────────────────

class UniverseEncoder(nn.Module):
    """Encodes raw input from one universe into a shared latent space."""
    def __init__(self, input_dim, common_dim=128):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Linear(256, common_dim),
            nn.ReLU(),
        )

    def forward(self, x):
        return self.encoder(x)


class Pole(nn.Module):
    """Classification head from shared latent space."""
    def __init__(self, common_dim=128, output_dim=10):
        super().__init__()
        self.head = nn.Linear(common_dim, output_dim)

    def forward(self, z):
        return self.head(z)


# ─────────────────────────────────────────
# Cross-Universe Repulsion Field
# ─────────────────────────────────────────

class CrossUniverseField(nn.Module):
    """Combines frozen outputs from two poles via a learned field transform.

    The field_transform learns how to combine/repulse the two signals.
    tension_scale controls the strength of the alien pole's contribution.
    """
    def __init__(self, output_dim=10):
        super().__init__()
        # Takes concatenated logits from both poles (2*output_dim) -> output_dim
        self.field_transform = nn.Sequential(
            nn.Linear(output_dim * 2, output_dim * 2),
            nn.Tanh(),
            nn.Linear(output_dim * 2, output_dim),
        )
        # Tension scale: initialized at 1/3 (meta fixed point)
        self.tension_scale = nn.Parameter(torch.tensor(1.0 / 3.0))

    def forward(self, logits_native, logits_alien):
        """
        logits_native: (batch, 10) from the pole trained on THIS data
        logits_alien:  (batch, 10) from the pole trained on ALIEN data
        Both are DETACHED (frozen).
        """
        # Scale alien contribution by learned tension
        scaled_alien = logits_alien * self.tension_scale
        combined = torch.cat([logits_native, scaled_alien], dim=-1)
        out = self.field_transform(combined)

        # Compute tension: cosine distance between the two pole outputs
        with torch.no_grad():
            cos_sim = F.cosine_similarity(logits_native, logits_alien, dim=-1)
            tension = 1.0 - cos_sim  # 0 = identical, 2 = opposite
        return out, tension


# ─────────────────────────────────────────
# Training helpers
# ─────────────────────────────────────────

def train_encoder_pole(encoder, pole, train_loader, test_loader, epochs=10,
                       lr=0.001, flatten=True, label=""):
    """Phase A/B: Train encoder + pole on one universe's data."""
    optimizer = torch.optim.Adam(
        list(encoder.parameters()) + list(pole.parameters()), lr=lr
    )
    criterion = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        encoder.train(); pole.train()
        total_loss = 0
        for X, y in train_loader:
            if flatten:
                X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            z = encoder(X)
            logits = pole(z)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)

        # Eval
        encoder.eval(); pole.eval()
        correct = total = 0
        with torch.no_grad():
            for X, y in test_loader:
                if flatten:
                    X = X.view(X.size(0), -1)
                z = encoder(X)
                logits = pole(z)
                correct += (logits.argmax(1) == y).sum().item()
                total += y.size(0)
        acc = correct / total

        if (epoch + 1) % 2 == 0 or epoch == 0:
            print(f"    [{label}] Epoch {epoch+1:>2}/{epochs}: "
                  f"Loss={avg_loss:.4f}, Acc={acc*100:.1f}%")

    return acc


def train_field(field, encoder_native, pole_native, encoder_alien, pole_alien,
                train_loader, test_loader, epochs=10, lr=0.001,
                flatten_native=True, flatten_alien=True,
                alien_train_loader=None, label=""):
    """Phase C/D: Freeze both poles, train only the field_transform.

    For the alien encoder, we need alien data to produce alien logits.
    We cycle through alien data alongside native data.
    """
    # Freeze encoders and poles
    for p in encoder_native.parameters(): p.requires_grad = False
    for p in pole_native.parameters(): p.requires_grad = False
    for p in encoder_alien.parameters(): p.requires_grad = False
    for p in pole_alien.parameters(): p.requires_grad = False

    # Only field params are trainable
    optimizer = torch.optim.Adam(field.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    encoder_native.eval(); pole_native.eval()
    encoder_alien.eval(); pole_alien.eval()

    # Create a cycling iterator for alien data
    alien_iter = iter(alien_train_loader)

    for epoch in range(epochs):
        field.train()
        total_loss = 0
        total_tension = 0
        n_batches = 0

        alien_iter = iter(alien_train_loader)

        for X_native, y_native in train_loader:
            # Get alien batch (cycle if needed)
            try:
                X_alien, _ = next(alien_iter)
            except StopIteration:
                alien_iter = iter(alien_train_loader)
                X_alien, _ = next(alien_iter)

            if flatten_native:
                X_native_flat = X_native.view(X_native.size(0), -1)
            else:
                X_native_flat = X_native
            if flatten_alien:
                X_alien_flat = X_alien.view(X_alien.size(0), -1)
            else:
                X_alien_flat = X_alien

            # Match batch sizes
            min_batch = min(X_native_flat.size(0), X_alien_flat.size(0))
            X_native_flat = X_native_flat[:min_batch]
            X_alien_flat = X_alien_flat[:min_batch]
            y_native = y_native[:min_batch]

            with torch.no_grad():
                z_native = encoder_native(X_native_flat)
                logits_native = pole_native(z_native)
                z_alien = encoder_alien(X_alien_flat)
                logits_alien = pole_alien(z_alien)

            optimizer.zero_grad()
            out, tension = field(logits_native.detach(), logits_alien.detach())
            loss = criterion(out, y_native)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            total_tension += tension.mean().item()
            n_batches += 1

        avg_loss = total_loss / n_batches
        avg_tension = total_tension / n_batches

        # Eval
        field.eval()
        correct = total = 0
        tensions = []
        alien_iter_test = iter(alien_train_loader)  # use train for alien (no test alignment needed)

        with torch.no_grad():
            for X_native, y_native in test_loader:
                try:
                    X_alien, _ = next(alien_iter_test)
                except StopIteration:
                    alien_iter_test = iter(alien_train_loader)
                    X_alien, _ = next(alien_iter_test)

                if flatten_native:
                    X_native_flat = X_native.view(X_native.size(0), -1)
                else:
                    X_native_flat = X_native
                if flatten_alien:
                    X_alien_flat = X_alien.view(X_alien.size(0), -1)
                else:
                    X_alien_flat = X_alien

                min_batch = min(X_native_flat.size(0), X_alien_flat.size(0))
                X_native_flat = X_native_flat[:min_batch]
                X_alien_flat = X_alien_flat[:min_batch]
                y_native = y_native[:min_batch]

                z_native = encoder_native(X_native_flat)
                logits_native = pole_native(z_native)
                z_alien = encoder_alien(X_alien_flat)
                logits_alien = pole_alien(z_alien)

                out, tension = field(logits_native, logits_alien)
                correct += (out.argmax(1) == y_native).sum().item()
                total += y_native.size(0)
                tensions.append(tension)

        acc = correct / total
        all_tensions = torch.cat(tensions)

        if (epoch + 1) % 2 == 0 or epoch == 0:
            print(f"    [{label}] Epoch {epoch+1:>2}/{epochs}: "
                  f"Loss={avg_loss:.4f}, Acc={acc*100:.1f}%, "
                  f"Tension={avg_tension:.4f}, "
                  f"tau={field.tension_scale.item():.4f}")

    return acc, all_tensions.mean().item(), field.tension_scale.item()


def eval_pole_alone(encoder, pole, test_loader, flatten=True):
    """Evaluate a single encoder+pole (no field)."""
    encoder.eval(); pole.eval()
    correct = total = 0
    with torch.no_grad():
        for X, y in test_loader:
            if flatten:
                X = X.view(X.size(0), -1)
            z = encoder(X)
            logits = pole(z)
            correct += (logits.argmax(1) == y).sum().item()
            total += y.size(0)
    return correct / total


def per_class_tension(field, encoder_native, pole_native, encoder_alien, pole_alien,
                      test_loader, alien_loader, flatten_native=True, flatten_alien=True,
                      n_classes=10):
    """Measure tension per class."""
    encoder_native.eval(); pole_native.eval()
    encoder_alien.eval(); pole_alien.eval()
    field.eval()

    class_tensions = {i: [] for i in range(n_classes)}
    alien_iter = iter(alien_loader)

    with torch.no_grad():
        for X_native, y_native in test_loader:
            try:
                X_alien, _ = next(alien_iter)
            except StopIteration:
                alien_iter = iter(alien_loader)
                X_alien, _ = next(alien_iter)

            if flatten_native:
                X_native_flat = X_native.view(X_native.size(0), -1)
            else:
                X_native_flat = X_native
            if flatten_alien:
                X_alien_flat = X_alien.view(X_alien.size(0), -1)
            else:
                X_alien_flat = X_alien

            min_batch = min(X_native_flat.size(0), X_alien_flat.size(0))
            X_native_flat = X_native_flat[:min_batch]
            X_alien_flat = X_alien_flat[:min_batch]
            y_native = y_native[:min_batch]

            z_n = encoder_native(X_native_flat)
            l_n = pole_native(z_n)
            z_a = encoder_alien(X_alien_flat)
            l_a = pole_alien(z_a)
            _, tension = field(l_n, l_a)

            for i in range(min_batch):
                cls = y_native[i].item()
                if cls < n_classes:
                    class_tensions[cls].append(tension[i].item())

    return {c: np.mean(ts) if ts else 0.0 for c, ts in class_tensions.items()}


# ─────────────────────────────────────────
# Same-Universe Field (both poles from same data)
# ─────────────────────────────────────────

def train_same_universe_field(field, encoder_a, pole_a, encoder_b, pole_b,
                              train_loader, test_loader, epochs=10, lr=0.001,
                              flatten=True, label=""):
    """Both poles trained on same data. Use same data for both during field training."""
    for p in encoder_a.parameters(): p.requires_grad = False
    for p in pole_a.parameters(): p.requires_grad = False
    for p in encoder_b.parameters(): p.requires_grad = False
    for p in pole_b.parameters(): p.requires_grad = False

    optimizer = torch.optim.Adam(field.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    encoder_a.eval(); pole_a.eval()
    encoder_b.eval(); pole_b.eval()

    for epoch in range(epochs):
        field.train()
        total_loss = 0
        total_tension = 0
        n_batches = 0

        for X, y in train_loader:
            if flatten:
                X = X.view(X.size(0), -1)

            with torch.no_grad():
                z_a = encoder_a(X)
                logits_a = pole_a(z_a)
                z_b = encoder_b(X)
                logits_b = pole_b(z_b)

            optimizer.zero_grad()
            out, tension = field(logits_a.detach(), logits_b.detach())
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            total_tension += tension.mean().item()
            n_batches += 1

        avg_loss = total_loss / n_batches
        avg_tension = total_tension / n_batches

        field.eval()
        correct = total = 0
        tensions = []
        with torch.no_grad():
            for X, y in test_loader:
                if flatten:
                    X = X.view(X.size(0), -1)
                z_a = encoder_a(X)
                logits_a = pole_a(z_a)
                z_b = encoder_b(X)
                logits_b = pole_b(z_b)
                out, tension = field(logits_a, logits_b)
                correct += (out.argmax(1) == y).sum().item()
                total += y.size(0)
                tensions.append(tension)

        acc = correct / total
        all_tensions = torch.cat(tensions)

        if (epoch + 1) % 2 == 0 or epoch == 0:
            print(f"    [{label}] Epoch {epoch+1:>2}/{epochs}: "
                  f"Loss={avg_loss:.4f}, Acc={acc*100:.1f}%, "
                  f"Tension={avg_tension:.4f}, "
                  f"tau={field.tension_scale.item():.4f}")

    return acc, all_tensions.mean().item(), field.tension_scale.item()


# ─────────────────────────────────────────
# ASCII Graphs
# ─────────────────────────────────────────

def bar_graph(title, labels, values, width=40, fmt=".4f"):
    """Print a horizontal bar graph."""
    print(f"\n  {title}")
    print(f"  {'─' * (width + 25)}")
    max_val = max(abs(v) for v in values) if values else 1
    for label, val in zip(labels, values):
        bar_len = int(abs(val) / max_val * width) if max_val > 0 else 0
        bar = "█" * bar_len
        print(f"  {label:>12} │ {bar:<{width}} {val:{fmt}}")
    print()


def comparison_graph(title, items, width=50):
    """items: list of (label, value, max_possible)"""
    print(f"\n  {title}")
    print(f"  {'─' * (width + 25)}")
    for label, val, max_p in items:
        bar_len = int(val / max_p * width) if max_p > 0 else 0
        bar = "█" * bar_len
        print(f"  {label:>20} │ {bar:<{width}} {val:.4f}")
    print()


# ═══════════════════════════════════════════
# MAIN EXPERIMENT
# ═══════════════════════════════════════════

def main():
    print("=" * 70)
    print("  CROSS-UNIVERSE REPULSION EXPERIMENT")
    print("  What happens when alien models are forced into a repulsion field?")
    print("=" * 70)

    COMMON_DIM = 128
    OUTPUT_DIM = 10
    EPOCHS_TRAIN = 10
    EPOCHS_FIELD = 10

    # ─────────────────────────────────
    # Load data
    # ─────────────────────────────────
    print("\n[1] Loading data from two universes...")
    t0 = time.time()
    mnist_train, mnist_test = load_mnist(batch_size=128)
    cifar_train, cifar_test = load_cifar10(batch_size=128)
    print(f"    Data loaded in {time.time()-t0:.1f}s")
    print(f"    Universe M (MNIST): 784-dim, 60k train, 10k test")
    print(f"    Universe C (CIFAR): 3072-dim, 50k train, 10k test")

    # ─────────────────────────────────
    # Phase A: Train Universe M
    # ─────────────────────────────────
    print("\n" + "─" * 70)
    print("[2] PHASE A: Training Universe M (MNIST encoder + pole)")
    print("─" * 70)

    encoder_m = UniverseEncoder(784, COMMON_DIM)
    pole_m = Pole(COMMON_DIM, OUTPUT_DIM)
    acc_m = train_encoder_pole(encoder_m, pole_m, mnist_train, mnist_test,
                               epochs=EPOCHS_TRAIN, flatten=True, label="MNIST")
    print(f"    >>> Universe M final accuracy: {acc_m*100:.1f}%")

    # ─────────────────────────────────
    # Phase B: Train Universe C
    # ─────────────────────────────────
    print("\n" + "─" * 70)
    print("[3] PHASE B: Training Universe C (CIFAR encoder + pole)")
    print("─" * 70)

    encoder_c = UniverseEncoder(3072, COMMON_DIM)
    pole_c = Pole(COMMON_DIM, OUTPUT_DIM)
    acc_c = train_encoder_pole(encoder_c, pole_c, cifar_train, cifar_test,
                               epochs=EPOCHS_TRAIN, flatten=True, label="CIFAR")
    print(f"    >>> Universe C final accuracy: {acc_c*100:.1f}%")

    # ─────────────────────────────────
    # Phase A2: Train second MNIST model (for same-universe baseline)
    # ─────────────────────────────────
    print("\n" + "─" * 70)
    print("[4] PHASE A2: Training second MNIST model (same-universe baseline)")
    print("─" * 70)

    encoder_m2 = UniverseEncoder(784, COMMON_DIM)
    pole_m2 = Pole(COMMON_DIM, OUTPUT_DIM)
    acc_m2 = train_encoder_pole(encoder_m2, pole_m2, mnist_train, mnist_test,
                                epochs=EPOCHS_TRAIN, flatten=True, label="MNIST-2")
    print(f"    >>> Universe M2 final accuracy: {acc_m2*100:.1f}%")

    # ─────────────────────────────────
    # Experiment (a): Same-universe baseline
    # ─────────────────────────────────
    print("\n" + "─" * 70)
    print("[5] EXPERIMENT A: Same-Universe Repulsion (MNIST + MNIST)")
    print("    Both poles trained on MNIST. Repulsion field on MNIST.")
    print("─" * 70)

    field_same = CrossUniverseField(OUTPUT_DIM)
    acc_same, tension_same, tau_same = train_same_universe_field(
        field_same, encoder_m, pole_m, encoder_m2, pole_m2,
        mnist_train, mnist_test,
        epochs=EPOCHS_FIELD, flatten=True, label="Same-Univ"
    )
    print(f"    >>> Same-universe: Acc={acc_same*100:.1f}%, "
          f"Tension={tension_same:.4f}, tau={tau_same:.4f}")

    # ─────────────────────────────────
    # Experiment (b): Cross-universe on MNIST
    # ─────────────────────────────────
    print("\n" + "─" * 70)
    print("[6] EXPERIMENT B: Cross-Universe Repulsion (MNIST native + CIFAR alien)")
    print("    Native pole: MNIST. Alien pole: CIFAR. Evaluated on MNIST.")
    print("─" * 70)

    field_cross_m = CrossUniverseField(OUTPUT_DIM)
    acc_cross_m, tension_cross_m, tau_cross_m = train_field(
        field_cross_m, encoder_m, pole_m, encoder_c, pole_c,
        mnist_train, mnist_test,
        epochs=EPOCHS_FIELD, flatten_native=True, flatten_alien=True,
        alien_train_loader=cifar_train, label="Cross-MNIST"
    )
    print(f"    >>> Cross-universe (MNIST): Acc={acc_cross_m*100:.1f}%, "
          f"Tension={tension_cross_m:.4f}, tau={tau_cross_m:.4f}")

    # ─────────────────────────────────
    # Experiment (c): Cross-universe on CIFAR
    # ─────────────────────────────────
    print("\n" + "─" * 70)
    print("[7] EXPERIMENT C: Cross-Universe Repulsion (CIFAR native + MNIST alien)")
    print("    Native pole: CIFAR. Alien pole: MNIST. Evaluated on CIFAR.")
    print("─" * 70)

    field_cross_c = CrossUniverseField(OUTPUT_DIM)
    acc_cross_c, tension_cross_c, tau_cross_c = train_field(
        field_cross_c, encoder_c, pole_c, encoder_m, pole_m,
        cifar_train, cifar_test,
        epochs=EPOCHS_FIELD, flatten_native=True, flatten_alien=True,
        alien_train_loader=mnist_train, label="Cross-CIFAR"
    )
    print(f"    >>> Cross-universe (CIFAR): Acc={acc_cross_c*100:.1f}%, "
          f"Tension={tension_cross_c:.4f}, tau={tau_cross_c:.4f}")

    # ─────────────────────────────────
    # Baselines: pole alone
    # ─────────────────────────────────
    acc_m_alone = eval_pole_alone(encoder_m, pole_m, mnist_test, flatten=True)
    acc_c_alone = eval_pole_alone(encoder_c, pole_c, cifar_test, flatten=True)

    # ─────────────────────────────────
    # Per-class tension analysis
    # ─────────────────────────────────
    print("\n" + "─" * 70)
    print("[8] PER-CLASS TENSION ANALYSIS (on MNIST)")
    print("─" * 70)

    # Same-universe per-class
    pct_same = per_class_tension(
        field_same, encoder_m, pole_m, encoder_m2, pole_m2,
        mnist_test, mnist_train, flatten_native=True, flatten_alien=True
    )

    # Cross-universe per-class
    pct_cross = per_class_tension(
        field_cross_m, encoder_m, pole_m, encoder_c, pole_c,
        mnist_test, cifar_train, flatten_native=True, flatten_alien=True
    )

    mnist_classes = [str(i) for i in range(10)]
    print("\n    Per-class tension (MNIST digits):")
    print(f"    {'Digit':>6} │ {'Same-Univ':>12} │ {'Cross-Univ':>12} │ {'Delta':>12}")
    print(f"    {'─'*6}─┼─{'─'*12}─┼─{'─'*12}─┼─{'─'*12}")
    for i in range(10):
        s = pct_same[i]
        c = pct_cross[i]
        d = c - s
        marker = " <<<" if abs(d) > 0.1 else ""
        print(f"    {i:>6} │ {s:>12.4f} │ {c:>12.4f} │ {d:>+12.4f}{marker}")

    # ═══════════════════════════════════════════
    # RESULTS SUMMARY
    # ═══════════════════════════════════════════

    print("\n" + "=" * 70)
    print("  CROSS-UNIVERSE REPULSION — RESULTS SUMMARY")
    print("=" * 70)

    # Accuracy comparison
    comparison_graph("ACCURACY COMPARISON", [
        ("Pole M alone (MNIST)", acc_m_alone, 1.0),
        ("Same-Univ field (MNIST)", acc_same, 1.0),
        ("Cross-Univ field (MNIST)", acc_cross_m, 1.0),
        ("Pole C alone (CIFAR)", acc_c_alone, 1.0),
        ("Cross-Univ field (CIFAR)", acc_cross_c, 1.0),
    ])

    # Tension comparison
    bar_graph("TENSION COMPARISON (higher = more repulsion)",
              ["Same-Universe", "Cross-Univ(MNIST)", "Cross-Univ(CIFAR)"],
              [tension_same, tension_cross_m, tension_cross_c])

    # Tension scale comparison
    bar_graph("LEARNED TENSION SCALE (tau) — how much the field uses the alien signal",
              ["Same-Universe", "Cross-Univ(MNIST)", "Cross-Univ(CIFAR)"],
              [tau_same, tau_cross_m, tau_cross_c])

    # Key findings
    print("  KEY FINDINGS")
    print("  " + "─" * 50)

    # Q1: Does cross-universe tension exist?
    print(f"\n  Q1: Does cross-universe tension exist?")
    if tension_cross_m > 0.01:
        print(f"      YES. Cross-universe tension = {tension_cross_m:.4f}")
    else:
        print(f"      Minimal. Tension = {tension_cross_m:.4f}")

    # Q2: Higher or lower than same-universe?
    print(f"\n  Q2: Is cross-universe tension higher than same-universe?")
    ratio = tension_cross_m / tension_same if tension_same > 0 else float('inf')
    if tension_cross_m > tension_same:
        print(f"      HIGHER. Cross/Same ratio = {ratio:.2f}x")
        print(f"      Alien models create MORE repulsion.")
    else:
        print(f"      LOWER. Cross/Same ratio = {ratio:.2f}x")
        print(f"      Same-universe models repulse more (they compete on the same territory).")

    # Q3: Does the alien help?
    print(f"\n  Q3: Can an alien model contribute to classification?")
    delta_m = acc_cross_m - acc_m_alone
    delta_c = acc_cross_c - acc_c_alone
    print(f"      MNIST: pole alone = {acc_m_alone*100:.1f}%, "
          f"with alien = {acc_cross_m*100:.1f}% (delta = {delta_m*100:+.1f}%)")
    print(f"      CIFAR: pole alone = {acc_c_alone*100:.1f}%, "
          f"with alien = {acc_cross_c*100:.1f}% (delta = {delta_c*100:+.1f}%)")
    if delta_m > 0:
        print(f"      The alien HELPS on MNIST. Even noise from another universe is useful.")
    elif delta_m < -0.5:
        print(f"      The alien HURTS on MNIST. Foreign signal is destructive.")
    else:
        print(f"      The alien is roughly NEUTRAL on MNIST.")

    # Q4: What did the field learn?
    print(f"\n  Q4: What did the field_transform learn?")
    print(f"      Same-universe tau:  {tau_same:.4f} (started at 0.3333)")
    print(f"      Cross-universe tau: {tau_cross_m:.4f} (MNIST), "
          f"{tau_cross_c:.4f} (CIFAR)")
    if abs(tau_cross_m) < abs(tau_same) * 0.5:
        print(f"      Field SUPPRESSES alien signal (tau shrank).")
        print(f"      The field learned to ignore the entity from another dimension.")
    elif abs(tau_cross_m) > abs(tau_same) * 1.5:
        print(f"      Field AMPLIFIES alien signal (tau grew).")
        print(f"      The alien presence creates a useful tension.")
    else:
        print(f"      Field maintains similar scale for both.")

    # ASCII art: tension landscape
    print(f"\n  TENSION LANDSCAPE (Same vs Cross Universe)")
    print(f"  {'─' * 52}")
    max_t = max(tension_same, tension_cross_m, tension_cross_c, 0.01)
    for label, t in [("Same-Univ   ", tension_same),
                     ("Cross(MNIST)", tension_cross_m),
                     ("Cross(CIFAR)", tension_cross_c)]:
        n_blocks = int(t / max_t * 40)
        print(f"  {label} │{'█' * n_blocks}{'░' * (40 - n_blocks)}│ {t:.4f}")

    print(f"\n  Parameter counts:")
    print(f"    Encoder M: {count_params(encoder_m):,}")
    print(f"    Encoder C: {count_params(encoder_c):,}")
    print(f"    Pole:      {count_params(pole_m):,}")
    print(f"    Field:     {count_params(field_cross_m):,}")

    print("\n" + "=" * 70)
    print("  EXPERIMENT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
