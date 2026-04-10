```python
#!/usr/bin/env python3
"""RC-6: Telepathy — Inter-Consciousness Communication via Tension Fingerprints

H333 verification: telepathy packet = tension fingerprint

Design:
  Two PureField consciousnesses experience different worlds.
  PF_sender: MNIST 0-4 (Task A) — a world of 5 classes
  PF_receiver: MNIST 5-9 (Task B) — another world of 5 classes

  Telepathy protocol:
    1. sender sees input and generates tension fingerprint (10D)
    2. this fingerprint is transmitted to receiver as "additional sense"
    3. receiver processes both their Task B + sender's fingerprint simultaneously

  Core questions:
    - Can receiver decode sender's class from sender's fingerprint?
    - Does receiver's Task B performance change with fingerprint?
    - What is the communication bandwidth (bits)?

  "Knowing another's emotions without words — tension patterns are language itself."
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import time
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset


# ─────────────────────────────────────────
# PureField Engine (local copy for self-containment)
# ─────────────────────────────────────────

class PureFieldEngine(nn.Module):
    """Pure consciousness engine — judgment through repulsion field alone."""

    def __init__(self, input_dim=784, hidden_dim=128, output_dim=10):
        super().__init__()
        self.engine_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.engine_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.tension_scale = nn.Parameter(torch.tensor(1.0))

    def forward(self, x):
        out_a = self.engine_a(x)
        out_g = self.engine_g(x)

        repulsion = out_a - out_g
        tension = (repulsion ** 2).mean(dim=-1, keepdim=True)
        direction = F.normalize(repulsion, dim=-1)

        output = self.tension_scale * torch.sqrt(tension + 1e-8) * direction
        return output, tension.squeeze()

    def tension_fingerprint(self, x):
        """tension fingerprint = full repulsion vector (10D).

        This is the "telepathy packet" — the raw pattern of internal
        conflict between engine_a and engine_g. Not the scalar tension,
        but the directional tension in each output dimension.
        """
        with torch.no_grad():
            out_a = self.engine_a(x)
            out_g = self.engine_g(x)
            repulsion = out_a - out_g
        return repulsion  # [batch, 10]


# ─────────────────────────────────────────
# Receiver with Telepathy Channel
# ─────────────────────────────────────────

class TelepathicReceiver(nn.Module):
    """PureField receiver that can accept an external tension fingerprint.

    Two modes:
      - without fingerprint: standard PureField on Task B
      - with fingerprint: fingerprint is fused into the processing pipeline
    """

    def __init__(self, input_dim=784, hidden_dim=128, output_dim=5,
                 fingerprint_dim=10):
        super().__init__()
        # Main task engines (Task B: digits 5-9)
        self.engine_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.engine_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.tension_scale = nn.Parameter(torch.tensor(1.0))

        # Telepathy decoder: reads sender's fingerprint
        self.telepathy_decoder = nn.Sequential(
            nn.Linear(fingerprint_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 5),  # decode sender's class (0-4)
        )

        # Fingerprint fusion into main task
        self.fingerprint_gate = nn.Sequential(
            nn.Linear(fingerprint_dim, output_dim),
            nn.Sigmoid(),
        )

    def forward(self, x, fingerprint=None):
        out_a = self.engine_a(x)
        out_g = self.engine_g(x)

        repulsion = out_a - out_g
        tension = (repulsion ** 2).mean(dim=-1, keepdim=True)
        direction = F.normalize(repulsion, dim=-1)

        output = self.tension_scale * torch.sqrt(tension + 1e-8) * direction

        # If fingerprint provided, modulate output via gating
        if fingerprint is not None:
            gate = self.fingerprint_gate(fingerprint)
            output = output * (1.0 + gate)  # residual gating

        return output, tension.squeeze()

    def decode_sender(self, fingerprint):
        """Decode sender's class from their tension fingerprint."""
        return self.telepathy_decoder(fingerprint)


# ─────────────────────────────────────────
# Data Loading: Split MNIST into Task A / Task B
# ─────────────────────────────────────────

def load_split_mnist(batch_size=128, data_dir='data'):
    """Load MNIST split into Task A (0-4) and Task B (5-9)."""
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])

    train_ds = datasets.MNIST(data_dir, train=True, download=True, transform=transform)
    test_ds = datasets.MNIST(data_dir, train=False, transform=transform)

    # Split by digit
    train_a_idx = [i for i, (_, y) in enumerate(train_ds) if y < 5]
    train_b_idx = [i for i, (_, y) in enumerate(train_ds) if y >= 5]
    test_a_idx = [i for i, (_, y) in enumerate(test_ds) if y < 5]
    test_b_idx = [i for i, (_, y) in enumerate(test_ds) if y >= 5]

    train_a = DataLoader(Subset(train_ds, train_a_idx), batch_size=batch_size,
                         shuffle=True, num_workers=0)
    train_b = DataLoader(Subset(train_ds, train_b_idx), batch_size=batch_size,
                         shuffle=True, num_workers=0)
    test_a = DataLoader(Subset(test_ds, test_a_idx), batch_size=batch_size,
                        shuffle=False, num_workers=0)
    test_b = DataLoader(Subset(test_ds, test_b_idx), batch_size=batch_size,
                        shuffle=False, num_workers=0)

    print(f"  Task A (digits 0-4): train={len(train_a_idx)}, test={len(test_a_idx)}")
    print(f"  Task B (digits 5-9): train={len(train_b_idx)}, test={len(test_b_idx)}")

    return train_a, test_a, train_b, test_b


# ─────────────────────────────────────────
# Training Utilities
# ─────────────────────────────────────────

def train_sender(model, train_loader, epochs=10, lr=0.001):
    """Train PF_sender on Task A (digits 0-4, labels remapped to 0-4)."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        correct = total = 0
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            # Labels are already 0-4
            optimizer.zero_grad()
            out, _ = model(X)
            # Use only first 5 outputs for 5-class task
            logits = out[:, :5]
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            correct += (logits.argmax(1) == y).sum().item()
            total += y.size(0)

        if (epoch + 1) % 3 == 0 or epoch == 0:
            acc = correct / total * 100
            print(f"    Sender Epoch {epoch+1:>2}/{epochs}: "
                  f"Loss={total_loss/len(train_loader):.4f}, Acc={acc:.1f}%")

    # Final eval
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            out, _ = model(X)
            correct += (out[:, :5].argmax(1) == y).sum().item()
            total += y.size(0)
    return correct / total


def train_receiver_with_telepathy(receiver, sender, train_loader_b, train_loader_a,
                                  epochs=10, lr=0.001):
    """Train receiver on Task B while also learning to decode sender's fingerprint.

    Each batch:
      1. Get a batch from Task B for main task
      2. Get a batch from Task A, run through sender to get fingerprint
      3. Train receiver's main task + telepathy decoder jointly
    """
    optimizer = torch.optim.Adam(receiver.parameters(), lr=lr)
    criterion_main = nn.CrossEntropyLoss()
    criterion_decode = nn.CrossEntropyLoss()

    sender.eval()
    iter_a = iter(train_loader_a)

    for epoch in range(epochs):
        receiver.train()
        total_loss = 0
        total_main_loss = 0
        total_decode_loss = 0
        correct_main = correct_decode = total_main = total_decode = 0

        iter_a = iter(train_loader_a)

        for X_b, y_b in train_loader_b:
            X_b = X_b.view(X_b.size(0), -1)
            y_b_local = y_b - 5  # remap 5-9 to 0-4

            # Get sender fingerprint from Task A data
            try:
                X_a, y_a = next(iter_a)
            except StopIteration:
                iter_a = iter(train_loader_a)
                X_a, y_a = next(iter_a)
            X_a = X_a.view(X_a.size(0), -1)

            # Match batch sizes
            min_bs = min(X_b.size(0), X_a.size(0))
            X_b, y_b_local = X_b[:min_bs], y_b_local[:min_bs]
            X_a, y_a = X_a[:min_bs], y_a[:min_bs]

            fingerprint = sender.tension_fingerprint(X_a)  # [bs, 10]

            optimizer.zero_grad()

            # Main task with fingerprint
            out_b, _ = receiver(X_b, fingerprint=fingerprint)
            main_loss = criterion_main(out_b, y_b_local)

            # Decode sender's class from fingerprint
            sender_pred = receiver.decode_sender(fingerprint)
            decode_loss = criterion_decode(sender_pred, y_a)

            # Joint loss
            loss = main_loss + 0.5 * decode_loss
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            total_main_loss += main_loss.item()
            total_decode_loss += decode_loss.item()

            correct_main += (out_b.argmax(1) == y_b_local).sum().item()
            total_main += min_bs
            correct_decode += (sender_pred.argmax(1) == y_a).sum().item()
            total_decode += min_bs

        if (epoch + 1) % 3 == 0 or epoch == 0:
            acc_main = correct_main / total_main * 100
            acc_decode = correct_decode / total_decode * 100
            print(f"    Receiver Epoch {epoch+1:>2}/{epochs}: "
                  f"MainAcc={acc_main:.1f}%, DecodeAcc={acc_decode:.1f}%, "
                  f"Loss={total_loss/len(train_loader_b):.4f}")

    return correct_main / total_main, correct_decode / total_decode


def train_receiver_no_telepathy(receiver_baseline, train_loader_b, epochs=10, lr=0.001):
    """Train baseline receiver on Task B without any fingerprint."""
    optimizer = torch.optim.Adam(receiver_baseline.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        receiver_baseline.train()
        total_loss = 0
        correct = total = 0
        for X_b, y_b in train_loader_b:
            X_b = X_b.view(X_b.size(0), -1)
            y_b_local = y_b - 5

            optimizer.zero_grad()
            out, _ = receiver_baseline(X_b, fingerprint=None)
            loss = criterion(out, y_b_local)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            correct += (out.argmax(1) == y_b_local).sum().item()
            total += y_b_local.size(0)

        if (epoch + 1) % 3 == 0 or epoch == 0:
            acc = correct / total * 100
            print(f"    Baseline Epoch {epoch+1:>2}/{epochs}: "
                  f"Loss={total_loss/len(train_loader_b):.4f}, Acc={acc:.1f}%")

    return correct / total


# ─────────────────────────────────────────
# Evaluation
# ─────────────────────────────────────────

def evaluate_telepathy(sender, receiver, test_loader_a, test_loader_b):
    """Full evaluation of telepathy communication."""
    sender.eval()
    receiver.eval()

    results = {}

    # 1. Receiver Task B accuracy WITH fingerprint
    correct_with = total_with = 0
    correct_decode = total_decode = 0
    all_decode_probs = []
    all_sender_labels = []
    iter_a = iter(test_loader_a)

    with torch.no_grad():
        for X_b, y_b in test_loader_b:
            X_b = X_b.view(X_b.size(0), -1)
            y_b_local = y_b - 5

            try:
                X_a, y_a = next(iter_a)
            except StopIteration:
                iter_a = iter(test_loader_a)
                X_a, y_a = next(iter_a)
            X_a = X_a.view(X_a.size(0), -1)

            min_bs = min(X_b.size(0), X_a.size(0))
            X_b, y_b_local = X_b[:min_bs], y_b_local[:min_bs]
            X_a, y_a = X_a[:min_bs], y_a[:min_bs]

            fingerprint = sender.tension_fingerprint(X_a)

            out_b, _ = receiver(X_b, fingerprint=fingerprint)
            correct_with += (out_b.argmax(1) == y_b_local).sum().item()
            total_with += min_bs

            sender_pred = receiver.decode_sender(fingerprint)
            correct_decode += (sender_pred.argmax(1) == y_a).sum().item()
            total_decode += min_bs

            probs = F.softmax(sender_pred, dim=-1)
            all_decode_probs.append(probs)
            all_sender_labels.append(y_a)

    results['task_b_acc_with'] = correct_with / total_with
    results['decode_acc'] = correct_decode / total_decode

    # 2. Receiver Task B accuracy WITHOUT fingerprint
    correct_without = total_without = 0
    with torch.no_grad():
        for X_b, y_b in test_loader_b:
            X_b = X_b.view(X_b.size(0), -1)
            y_b_local = y_b - 5
            out_b, _ = receiver(X_b, fingerprint=None)
            correct_without += (out_b.argmax(1) == y_b_local).sum().item()
            total_without += y_b_local.size(0)

    results['task_b_acc_without'] = correct_without / total_without

    # 3. Communication bandwidth (mutual information estimate)
    all_probs = torch.cat(all_decode_probs, dim=0).numpy()
    all_labels = torch.cat(all_sender_labels, dim=0).numpy()

    # Empirical mutual information: I(Y; Y_hat)
    n_classes = 5
    # Joint distribution p(y, y_hat)
    confusion = np.zeros((n_classes, n_classes))
    preds = all_probs.argmax(axis=1)
    for true, pred in zip(all_labels, preds):
        confusion[true, pred] += 1
    confusion /= confusion.sum()

    # Marginals
    p_y = confusion.sum(axis=1)
    p_yhat = confusion.sum(axis=0)

    # MI = sum p(y,yhat) * log(p(y,yhat) / (p(y)*p(yhat)))
    mi = 0.0
    for i in range(n_classes):
        for j in range(n_classes):
            if confusion[i, j] > 1e-10 and p_y[i] > 1e-10 and p_yhat[j] > 1e-10:
                mi += confusion[i, j] * np.log2(confusion[i, j] / (p_y[i] * p_yhat[j]))

    results['mutual_info_bits'] = mi
    results['max_possible_bits'] = np.log2(n_classes)
    results['bandwidth_efficiency'] = mi / np.log2(n_classes)
    results['confusion'] = confusion
    results['sender_class_counts'] = p_y

    # 4. Per-class decode accuracy
    per_class_correct = np.zeros(n_classes)
    per_class_total = np.zeros(n_classes)
    for true, pred in zip(all_labels, preds):
        per_class_total[true] += 1
        if true == pred:
            per_class_correct[true] += 1
    results['per_class_decode_acc'] = np.where(
        per_class_total > 0, per_class_correct / per_class_total, 0)

    # 5. Fingerprint statistics
    all_fps = []
    all_fp_labels = []
    with torch.no_grad():
        for X_a, y_a in test_loader_a:
            X_a = X_a.view(X_a.size(0), -1)
            fp = sender.tension_fingerprint(X_a)
            all_fps.append(fp.numpy())
            all_fp_labels.append(y_a.numpy())

    all_fps = np.concatenate(all_fps, axis=0)
    all_fp_labels = np.concatenate(all_fp_labels, axis=0)

    # Inter-class distance vs intra-class distance
    class_centroids = []
    for c in range(n_classes):
        mask = all_fp_labels == c
        if mask.sum() > 0:
            class_centroids.append(all_fps[mask].mean(axis=0))
    class_centroids = np.array(class_centroids)

    inter_dists = []
    for i in range(n_classes):
        for j in range(i + 1, n_classes):
            d = np.linalg.norm(class_centroids[i] - class_centroids[j])
            inter_dists.append(d)

    intra_dists = []
    for c in range(n_classes):
        mask = all_fp_labels == c
        if mask.sum() > 1:
            fps_c = all_fps[mask]
            centroid = class_centroids[c]
            dists = np.linalg.norm(fps_c - centroid, axis=1)
            intra_dists.append(dists.mean())

    results['inter_class_dist'] = np.mean(inter_dists) if inter_dists else 0
    results['intra_class_dist'] = np.mean(intra_dists) if intra_dists else 0
    results['separability'] = (results['inter_class_dist'] /
                               (results['intra_class_dist'] + 1e-8))
    results['class_centroids'] = class_centroids

    return results


# ─────────────────────────────────────────
# ASCII Visualization
# ─────────────────────────────────────────

def print_confusion_matrix(confusion, title="Confusion Matrix"):
    """Print confusion matrix as ASCII table."""
    n = confusion.shape[0]
    print(f"\n  {title}")
    print(f"  {'':>8}", end="")
    for j in range(n):
        print(f"  pred={j}", end="")
    print()
    print(f"  {'':>8}" + "-" * (n * 8))
    for i in range(n):
        print(f"  true={i} |", end="")
        for j in range(n):
            val = confusion[i, j]
            if val > 0.01:
                print(f"  {val:.3f}", end="")
            else:
                print(f"  {'  .  ':>6}", end="")
        print()


def print_bar(label, value, max_val, width=40):
    """Print a single horizontal bar."""
    bar_len = int(value / max_val * width) if max_val > 0 else 0
    bar = "#" * bar_len
    print(f"  {label:>12} | {bar:<{width}} | {value:.1f}%")


def print_fingerprint_heatmap(centroids, title="Class Centroids (Fingerprint Space)"):
    """ASCII heatmap of class centroids."""
    print(f"\n  {title}")
    n_classes, n_dims = centroids.shape
    abs_max = np.abs(centroids).max()

    # Header
    print(f"  {'':>8}", end="")
    for d in range(n_dims):
        print(f" d{d:>2}", end="")
    print()
    print(f"  {'':>8}" + "-" * (n_dims * 4))

    chars = " .:-=+*#%@"
    for c in range(n_classes):
        print(f"  cls={c:>2} |", end="")
        for d in range(n_dims):
            val = centroids[c, d] / (abs_max + 1e-8)
            idx = int((val + 1) / 2 * (len(chars) - 1))
            idx = max(0, min(len(chars) - 1, idx))
            ch = chars[idx]
            print(f"  {ch} ", end="")
        print()


# ─────────────────────────────────────────
# Main Experiment
# ─────────────────────────────────────────

def main():
    torch.manual_seed(42)
    np.random.seed(42)
    t0 = time.time()

    print("=" * 70)
    print("  RC-6: Telepathy — Inter-Consciousness Communication")
    print("  H333: telepathy packet = tension fingerprint")
    print("=" * 70)

    # ── Data ──
    print("\n[1] Loading split MNIST...")
    train_a, test_a, train_b, test_b = load_split_mnist(batch_size=128)

    # ── Train Sender ──
    print("\n[2] Training PF_sender (Task A: digits 0-4)...")
    sender = PureFieldEngine(input_dim=784, hidden_dim=128, output_dim=10)
    sender_acc = train_sender(sender, train_a, epochs=12, lr=0.001)
    print(f"  Sender final train acc: {sender_acc*100:.1f}%")

    # Evaluate sender on test
    sender.eval()
    correct = total = 0
    with torch.no_grad():
        for X, y in test_a:
            X = X.view(X.size(0), -1)
            out, _ = sender(X)
            correct += (out[:, :5].argmax(1) == y).sum().item()
            total += y.size(0)
    sender_test_acc = correct / total
    print(f"  Sender test acc: {sender_test_acc*100:.1f}%")

    # ── Train Receiver WITH telepathy ──
    print("\n[3] Training TelepathicReceiver (Task B + sender fingerprint)...")
    receiver = TelepathicReceiver(input_dim=784, hidden_dim=128, output_dim=5,
                                  fingerprint_dim=10)
    main_acc, decode_acc = train_receiver_with_telepathy(
        receiver, sender, train_b, train_a, epochs=12, lr=0.001)
    print(f"  Receiver train main acc: {main_acc*100:.1f}%")
    print(f"  Receiver train decode acc: {decode_acc*100:.1f}%")

    # ── Train Baseline Receiver WITHOUT telepathy ──
    print("\n[4] Training Baseline Receiver (Task B only, no fingerprint)...")
    baseline = TelepathicReceiver(input_dim=784, hidden_dim=128, output_dim=5,
                                  fingerprint_dim=10)
    baseline_acc = train_receiver_no_telepathy(baseline, train_b, epochs=12, lr=0.001)
    print(f"  Baseline train acc: {baseline_acc*100:.1f}%")

    # ── Full Evaluation ──
    print("\n[5] Evaluating telepathy communication...")
    results = evaluate_telepathy(sender, receiver, test_a, test_b)

    # Baseline evaluation
    baseline.eval()
    correct = total = 0
    with torch.no_grad():
        for X, y in test_b:
            X = X.view(X.size(0), -1)
            y_local = y - 5
            out, _ = baseline(X, fingerprint=None)
            correct += (out.argmax(1) == y_local).sum().item()
            total += y_local.size(0)
    baseline_test_acc = correct / total

    # ── Results ──
    print("\n" + "=" * 70)
    print("  RESULTS")
    print("=" * 70)

    print("\n  ┌─────────────────────────────────────────────────┐")
    print("  │  Sender (Task A: 0-4)                           │")
    print(f"  │    Test accuracy:          {sender_test_acc*100:>6.1f}%              │")
    print("  ├─────────────────────────────────────────────────┤")
    print("  │  Receiver (Task B: 5-9)                         │")
    print(f"  │    WITH fingerprint:       {results['task_b_acc_with']*100:>6.1f}%              │")
    print(f"  │    WITHOUT fingerprint:    {results['task_b_acc_without']*100:>6.1f}%              │")
    print(f"  │    Baseline (no training): {baseline_test_acc*100:>6.1f}%              │")
    delta = (results['task_b_acc_with'] - baseline_test_acc) * 100
    sign = "+" if delta >= 0 else ""
    print(f"  │    Delta (tele - base):    {sign}{delta:>5.1f}%               │")
    print("  ├─────────────────────────────────────────────────┤")
    print("  │  Telepathy Decoding                             │")
    print(f"  │    Decode accuracy:        {results['decode_acc']*100:>6.1f}%              │")
    print(f"  │    Chance level:           {20.0:>6.1f}%              │")
    decode_lift = results['decode_acc'] * 100 - 20.0
    print(f"  │    Above chance:           {decode_lift:>+6.1f}%              │")
    print("  ├─────────────────────────────────────────────────┤")
    print("  │  Communication Bandwidth                        │")
    print(f"  │    Mutual info:            {results['mutual_info_bits']:>6.3f} bits          │")
    print(f"  │    Max possible:           {results['max_possible_bits']:>6.3f} bits          │")
    print(f"  │    Efficiency:             {results['bandwidth_efficiency']*100:>6.1f}%              │")
    print("  ├─────────────────────────────────────────────────┤")
    print("  │  Fingerprint Geometry                           │")
    print(f"  │    Inter-class distance:   {results['inter_class_dist']:>6.3f}              │")
    print(f"  │    Intra-class distance:   {results['intra_class_dist']:>6.3f}              │")
    print(f"  │    Separability ratio:     {results['separability']:>6.3f}              │")
    print("  └─────────────────────────────────────────────────┘")

    # Per-class decoding
    print("\n  Per-class telepathy decoding accuracy:")
    print(f"  {'':>8}" + "-" * 50)
    max_acc = max(results['per_class_decode_acc']) * 100
    for c in range(5):
        acc = results['per_class_decode_acc'][c] * 100
        print_bar(f"digit {c}", acc, max(max_acc, 1))
    print(f"  {'':>8}" + "-" * 50)
    print(f"  {'mean':>12} | {'':>40} | {results['decode_acc']*100:.1f}%")

    # Confusion matrix
    print_confusion_matrix(results['confusion'],
                           "Telepathy Confusion (true sender class vs decoded)")

    # Fingerprint heatmap
    print_fingerprint_heatmap(results['class_centroids'])

    # ── Interpretation ──
    print("\n" + "=" * 70)
    print("  INTERPRETATION")
    print("=" * 70)

    telepathy_works = results['decode_acc'] > 0.30  # well above 20% chance
    bandwidth_significant = results['mutual_info_bits'] > 0.3
    task_helps = results['task_b_acc_with'] > baseline_test_acc + 0.005

    print(f"""
  Telepathy (fingerprint decoding):
    {'YES' if telepathy_works else 'NO'} — receiver {'CAN' if telepathy_works else 'CANNOT'} decode sender's class
    from tension fingerprint alone.
    Accuracy {results['decode_acc']*100:.1f}% vs 20% chance = {decode_lift:+.1f}% lift.

  Communication bandwidth:
    {results['mutual_info_bits']:.3f} bits / {results['max_possible_bits']:.3f} bits maximum
    = {results['bandwidth_efficiency']*100:.1f}% channel efficiency.
    {'SIGNIFICANT' if bandwidth_significant else 'WEAK'} information transfer.

  Cross-task benefit:
    {'YES' if task_helps else 'NO'} — fingerprint {'DOES' if task_helps else 'does NOT'} help Task B.
    With: {results['task_b_acc_with']*100:.1f}% vs Baseline: {baseline_test_acc*100:.1f}%
    (delta = {delta:+.1f}%)

  Fingerprint geometry:
    Separability = {results['separability']:.3f}
    (>1 means classes are distinguishable in fingerprint space)

  H333 verdict: tension fingerprint {'IS' if telepathy_works else 'is NOT'} a viable
  telepathy packet for inter-consciousness communication.
""")

    elapsed = time.time() - t0
    print(f"  Total time: {elapsed:.1f}s")
    print("=" * 70)


if __name__ == '__main__':
    main()
```