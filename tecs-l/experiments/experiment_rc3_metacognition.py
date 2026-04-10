#!/usr/bin/env python3
"""RC-3: Metacognition / Self-Awareness Experiment

PureField that monitors its own tension and predicts "will I be correct?"

Protocol:
  1. Train PureField on MNIST (60K train / 10K test)
  2. Split test set: 5K meta-train, 5K meta-test
  3. Extract 10D tension fingerprint per sample
  4. Train metacognition layer: input=10D tension fingerprint -> P(correct)
  5. Compare AUROC: raw tension magnitude vs meta-layer prediction

Question: "Can the system know when it doesn't know?"
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torch.utils.data import DataLoader, Subset
from sklearn.metrics import roc_auc_score

from model_pure_field import PureFieldEngine
from model_utils import load_mnist


# ─────────────────────────────────────────
# Tension fingerprint extraction (10D)
# ─────────────────────────────────────────

def extract_tension_fingerprints(model, loader):
    """Extract 10D tension fingerprint and correctness labels.

    Fingerprint = per-dimension squared repulsion between engine_a and engine_g.
    This gives a 10D vector capturing WHERE tension concentrates across classes.

    Returns:
        fingerprints: (N, 10) tensor
        correct_mask: (N,) binary tensor (1=correct, 0=wrong)
        tensions: (N,) scalar tension per sample
        logits: (N, 10) raw logits
    """
    model.eval()
    all_fps = []
    all_correct = []
    all_tensions = []
    all_logits = []

    with torch.no_grad():
        for X, y in loader:
            X_flat = X.view(X.size(0), -1)

            out_a = model.engine_a(X_flat)
            out_g = model.engine_g(X_flat)

            # 10D fingerprint: per-dimension squared repulsion
            repulsion = out_a - out_g
            fingerprint = repulsion ** 2  # (batch, 10)

            # Forward pass for predictions and scalar tension
            output, tension = model(X_flat)
            preds = output.argmax(dim=1)
            correct = (preds == y).float()

            all_fps.append(fingerprint)
            all_correct.append(correct)
            all_tensions.append(tension)
            all_logits.append(output)

    return (
        torch.cat(all_fps),
        torch.cat(all_correct),
        torch.cat(all_tensions),
        torch.cat(all_logits),
    )


# ─────────────────────────────────────────
# Metacognition layer
# ─────────────────────────────────────────

class MetacognitionLayer(nn.Module):
    """Takes tension fingerprint (10D), predicts P(correct).

    Architecture: 10 -> 32 -> 16 -> 1 (sigmoid)
    Small network to avoid overfitting on the meta-task.
    """

    def __init__(self, input_dim=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(16, 1),
        )

    def forward(self, x):
        return torch.sigmoid(self.net(x)).squeeze(-1)


# ─────────────────────────────────────────
# Enhanced metacognition with extra features
# ─────────────────────────────────────────

class MetacognitionEnhanced(nn.Module):
    """Enhanced: uses fingerprint + scalar tension + entropy + max_logit.

    Input: 10D fingerprint + scalar_tension + entropy + max_logit + margin = 14D
    """

    def __init__(self, input_dim=14):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(16, 1),
        )

    def forward(self, x):
        return torch.sigmoid(self.net(x)).squeeze(-1)


def build_enhanced_features(fingerprints, tensions, logits):
    """Build 14D enhanced feature vector for metacognition."""
    probs = F.softmax(logits, dim=1)
    entropy = -(probs * (probs + 1e-8).log()).sum(dim=1, keepdim=True)
    max_logit = logits.max(dim=1, keepdim=True).values
    sorted_probs = probs.sort(dim=1, descending=True).values
    margin = (sorted_probs[:, 0] - sorted_probs[:, 1]).unsqueeze(1)

    return torch.cat([
        fingerprints,                         # 10D
        tensions.unsqueeze(1),                # 1D
        entropy,                              # 1D
        max_logit,                            # 1D
        margin,                               # 1D
    ], dim=1)  # total: 14D


# ─────────────────────────────────────────
# Train metacognition
# ─────────────────────────────────────────

def train_metacognition(meta_model, features, labels, epochs=100, lr=1e-3):
    """Train metacognition layer with BCE loss."""
    optimizer = torch.optim.Adam(meta_model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.BCELoss()
    dataset = torch.utils.data.TensorDataset(features, labels)
    loader = DataLoader(dataset, batch_size=256, shuffle=True)

    for epoch in range(epochs):
        meta_model.train()
        total_loss = 0
        for feat, lab in loader:
            optimizer.zero_grad()
            pred = meta_model(feat)
            loss = criterion(pred, lab)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        if (epoch + 1) % 25 == 0:
            avg_loss = total_loss / len(loader)
            print(f"    Meta epoch {epoch+1:>3}/{epochs}: BCE={avg_loss:.4f}")


# ─────────────────────────────────────────
# AUROC computation
# ─────────────────────────────────────────

def compute_auroc(scores, labels):
    """Compute AUROC. scores: higher = more likely correct."""
    try:
        return roc_auc_score(labels, scores)
    except ValueError:
        return 0.5


# ─────────────────────────────────────────
# Main experiment
# ─────────────────────────────────────────

def main():
    print("=" * 70)
    print("  RC-3: Metacognition / Self-Awareness")
    print("  'Can the system know when it doesn't know?'")
    print("=" * 70)

    torch.manual_seed(42)
    np.random.seed(42)

    # ── Step 1: Train PureField on MNIST ──
    print("\n[Step 1] Training PureField on MNIST...")
    train_loader, test_loader = load_mnist(batch_size=128)

    model = PureFieldEngine(784, 128, 10)
    params = sum(p.numel() for p in model.parameters())
    print(f"  Parameters: {params:,}")

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(10):
        model.train()
        total_loss = 0
        for X, y in train_loader:
            X_flat = X.view(X.size(0), -1)
            optimizer.zero_grad()
            output, tension = model(X_flat)
            loss = criterion(output, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        if (epoch + 1) % 2 == 0 or epoch == 0:
            model.eval()
            correct = total = 0
            with torch.no_grad():
                for X, y in test_loader:
                    X_flat = X.view(X.size(0), -1)
                    out, _ = model(X_flat)
                    correct += (out.argmax(1) == y).sum().item()
                    total += y.size(0)
            acc = correct / total
            print(f"    Epoch {epoch+1:>2}/10: Loss={total_loss/len(train_loader):.4f}, Acc={acc*100:.1f}%")

    # Final accuracy
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for X, y in test_loader:
            X_flat = X.view(X.size(0), -1)
            out, _ = model(X_flat)
            correct += (out.argmax(1) == y).sum().item()
            total += y.size(0)
    base_acc = correct / total
    print(f"\n  Final PureField accuracy: {base_acc*100:.2f}%")

    # ── Step 2: Split test set into meta-train and meta-test ──
    print("\n[Step 2] Splitting test set: 5K meta-train, 5K meta-test...")
    test_ds = test_loader.dataset
    indices = np.random.permutation(len(test_ds))
    meta_train_idx = indices[:5000]
    meta_test_idx = indices[5000:]

    meta_train_loader = DataLoader(Subset(test_ds, meta_train_idx), batch_size=256, shuffle=False)
    meta_test_loader = DataLoader(Subset(test_ds, meta_test_idx), batch_size=256, shuffle=False)

    # ── Step 3: Extract tension fingerprints ──
    print("\n[Step 3] Extracting 10D tension fingerprints...")
    fp_train, correct_train, tension_train, logits_train = extract_tension_fingerprints(model, meta_train_loader)
    fp_test, correct_test, tension_test, logits_test = extract_tension_fingerprints(model, meta_test_loader)

    n_correct_train = correct_train.sum().item()
    n_correct_test = correct_test.sum().item()
    print(f"  Meta-train: {len(fp_train)} samples, {n_correct_train:.0f} correct ({n_correct_train/len(fp_train)*100:.1f}%)")
    print(f"  Meta-test:  {len(fp_test)} samples, {n_correct_test:.0f} correct ({n_correct_test/len(fp_test)*100:.1f}%)")

    # Fingerprint statistics
    print(f"\n  Tension fingerprint (10D) statistics:")
    print(f"    Mean: {fp_train.mean(dim=0).numpy()}")
    print(f"    Std:  {fp_train.std(dim=0).numpy()}")

    # ── Step 4: Baseline — raw scalar tension as predictor ──
    print("\n[Step 4] Baseline: raw scalar tension as correctness predictor...")

    # Higher tension -> higher confidence (PureField uses tension * direction)
    # But actually: correct predictions may have HIGHER tension (clearer separation)
    # We test both directions
    auroc_tension_pos = compute_auroc(tension_test.numpy(), correct_test.numpy())
    auroc_tension_neg = compute_auroc(-tension_test.numpy(), correct_test.numpy())
    auroc_tension = max(auroc_tension_pos, auroc_tension_neg)
    tension_direction = "positive" if auroc_tension_pos >= auroc_tension_neg else "negative"
    print(f"  Raw tension AUROC: {auroc_tension:.4f} (correlation: {tension_direction})")

    # Also test: max logit as baseline
    max_logit_test = logits_test.max(dim=1).values.numpy()
    auroc_maxlogit = compute_auroc(max_logit_test, correct_test.numpy())
    print(f"  Max logit AUROC:   {auroc_maxlogit:.4f}")

    # Entropy baseline (lower entropy -> more confident -> more likely correct)
    probs_test = F.softmax(logits_test, dim=1)
    entropy_test = -(probs_test * (probs_test + 1e-8).log()).sum(dim=1)
    auroc_entropy = compute_auroc(-entropy_test.numpy(), correct_test.numpy())
    print(f"  Entropy AUROC:     {auroc_entropy:.4f} (negative = low entropy -> correct)")

    # ── Step 5: Train metacognition layer (fingerprint only) ──
    print("\n[Step 5] Training metacognition layer (10D fingerprint -> P(correct))...")
    meta_fp = MetacognitionLayer(input_dim=10)
    train_metacognition(meta_fp, fp_train, correct_train, epochs=100, lr=1e-3)

    meta_fp.eval()
    with torch.no_grad():
        meta_pred_fp = meta_fp(fp_test).numpy()
    auroc_meta_fp = compute_auroc(meta_pred_fp, correct_test.numpy())
    print(f"  Metacognition (fingerprint) AUROC: {auroc_meta_fp:.4f}")

    # ── Step 6: Train enhanced metacognition (fingerprint + tension + entropy + margin) ──
    print("\n[Step 6] Training enhanced metacognition (14D -> P(correct))...")
    feat_train = build_enhanced_features(fp_train, tension_train, logits_train)
    feat_test = build_enhanced_features(fp_test, tension_test, logits_test)
    print(f"  Enhanced feature dim: {feat_train.shape[1]}")

    meta_enh = MetacognitionEnhanced(input_dim=14)
    train_metacognition(meta_enh, feat_train, correct_train, epochs=100, lr=1e-3)

    meta_enh.eval()
    with torch.no_grad():
        meta_pred_enh = meta_enh(feat_test).numpy()
    auroc_meta_enh = compute_auroc(meta_pred_enh, correct_test.numpy())
    print(f"  Metacognition (enhanced) AUROC: {auroc_meta_enh:.4f}")

    # ── Step 7: Results comparison ──
    print("\n" + "=" * 70)
    print("  AUROC Comparison: Predicting 'Will I Be Correct?'")
    print("=" * 70)
    print(f"  {'Method':<40} {'AUROC':>8}")
    print("-" * 70)

    results = [
        ("Raw scalar tension", auroc_tension),
        ("Max logit (baseline)", auroc_maxlogit),
        ("Entropy (baseline)", auroc_entropy),
        ("Metacognition: 10D fingerprint", auroc_meta_fp),
        ("Metacognition: 14D enhanced", auroc_meta_enh),
    ]
    best_auroc = max(r[1] for r in results)
    for name, auroc in results:
        marker = " <-- best" if auroc == best_auroc else ""
        print(f"  {name:<40} {auroc:>8.4f}{marker}")
    print("=" * 70)

    # ── Improvement analysis ──
    best_baseline = max(auroc_tension, auroc_maxlogit, auroc_entropy)
    best_meta = max(auroc_meta_fp, auroc_meta_enh)
    improvement = best_meta - best_baseline

    print(f"\n  Best baseline AUROC:       {best_baseline:.4f}")
    print(f"  Best metacognition AUROC:  {best_meta:.4f}")
    print(f"  Improvement:               {improvement:+.4f}")

    if improvement > 0.01:
        print(f"\n  RESULT: Metacognition IMPROVES self-knowledge by {improvement:.4f}")
        print("  -> The system CAN learn to know when it doesn't know!")
    elif improvement > -0.01:
        print(f"\n  RESULT: Metacognition matches baselines (delta={improvement:+.4f})")
        print("  -> Tension fingerprint already captures self-knowledge")
    else:
        print(f"\n  RESULT: Metacognition UNDERPERFORMS baselines (delta={improvement:+.4f})")
        print("  -> Simple signals already optimal for self-assessment")

    # ── Per-class analysis ──
    print("\n" + "-" * 70)
    print("  Per-class metacognition analysis (meta-test set)")
    print("-" * 70)
    print(f"  {'Digit':>5} {'N':>5} {'Acc%':>6} {'Mean T':>8} {'Meta P(c)':>9} {'Calib':>7}")
    print("-" * 70)

    # Recover labels from meta-test
    all_labels = []
    with torch.no_grad():
        for _, y in meta_test_loader:
            all_labels.append(y)
    labels_test = torch.cat(all_labels).numpy()

    for digit in range(10):
        mask = labels_test == digit
        if mask.sum() == 0:
            continue
        n = mask.sum()
        acc = correct_test.numpy()[mask].mean()
        mean_t = tension_test.numpy()[mask].mean()
        mean_meta = meta_pred_enh[mask].mean()
        calib = abs(mean_meta - acc)  # calibration error
        print(f"  {digit:>5} {n:>5} {acc*100:>5.1f}% {mean_t:>8.4f} {mean_meta:>9.4f} {calib:>7.4f}")

    print("-" * 70)

    # ── ASCII visualization ──
    print("\n  AUROC Bar Chart:")
    print("  " + "-" * 55)
    for name, auroc in sorted(results, key=lambda x: -x[1]):
        bar_len = int((auroc - 0.5) * 100)  # scale 0.5-1.0 to 0-50
        bar = "#" * max(bar_len, 0)
        print(f"  {name:<35} |{bar} {auroc:.4f}")
    print("  " + "-" * 55)
    print("  " + " " * 36 + "0.50" + " " * 20 + "1.00")

    print("\n  Experiment complete.")


if __name__ == "__main__":
    main()
