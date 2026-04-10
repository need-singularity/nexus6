#!/usr/bin/env python3
"""RC-5: Multimodal PureField — Cross-modal tension experiment

Hypothesis: PureField engines on different modalities produce cross-modal tension
that improves classification beyond either modality alone.

Setup:
  - Image modality: MNIST 784D flattened pixels
  - Text modality: synthetic one-hot digit name (10D)
  - PureField_image: engine_A(image) vs engine_G(image) -> tension + direction
  - PureField_text:  engine_A(text)  vs engine_G(text)  -> tension + direction
  - Cross-modal tension: |PF_image_output - PF_text_output|^2
  - Final output: gated combination of image + text PureField outputs

Compare:
  1. Image-only PureField
  2. Text-only PureField
  3. Multimodal PureField (gated fusion + cross-modal tension)
  4. Multimodal PureField (simple sum)
  5. Naive concat baseline (no PureField)

3 seeds, 15 epochs each. ASCII bar chart + accuracy table.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torch.utils.data import DataLoader, TensorDataset
from torchvision import datasets, transforms
import time


# ---------------------------------------------------------------------------
# PureField Engine (from model_pure_field.py, adapted per-modality)
# ---------------------------------------------------------------------------

class PureFieldEngine(nn.Module):
    """Pure tension-field engine: output lives in the space between two engines."""

    def __init__(self, input_dim, hidden_dim, output_dim):
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
        return output, tension.squeeze(-1)


# ---------------------------------------------------------------------------
# Model 1: Image-only PureField
# ---------------------------------------------------------------------------

class ImageOnlyPureField(nn.Module):
    def __init__(self, output_dim=10):
        super().__init__()
        self.pf_image = PureFieldEngine(784, 128, output_dim)

    def forward(self, image, text):
        out, tension = self.pf_image(image)
        return out, tension


# ---------------------------------------------------------------------------
# Model 2: Text-only PureField
# ---------------------------------------------------------------------------

class TextOnlyPureField(nn.Module):
    def __init__(self, output_dim=10):
        super().__init__()
        self.pf_text = PureFieldEngine(10, 32, output_dim)

    def forward(self, image, text):
        out, tension = self.pf_text(text)
        return out, tension


# ---------------------------------------------------------------------------
# Model 3: Multimodal PureField (gated fusion + cross-modal tension)
# ---------------------------------------------------------------------------

class MultimodalPureField(nn.Module):
    """Two PureField engines (image + text) with cross-modal tension gating.

    Cross-modal tension = |PF_image_output - PF_text_output|^2
    Gate learns to weight each modality based on cross-modal agreement/disagreement.
    """

    def __init__(self, output_dim=10):
        super().__init__()
        self.pf_image = PureFieldEngine(784, 128, output_dim)
        self.pf_text = PureFieldEngine(10, 32, output_dim)

        # Gate: uses cross-modal tension + individual tensions to weight modalities
        self.gate = nn.Sequential(
            nn.Linear(output_dim * 2 + 2, 16),  # both outputs + 2 tension scalars
            nn.ReLU(),
            nn.Linear(16, 2),
            nn.Softmax(dim=-1),
        )

    def forward(self, image, text):
        out_img, t_img = self.pf_image(image)
        out_txt, t_txt = self.pf_text(text)

        # Cross-modal tension
        cross_tension = ((out_img - out_txt) ** 2).mean(dim=-1)

        # Gate input: both outputs + tension scalars
        gate_input = torch.cat([
            out_img, out_txt,
            t_img.unsqueeze(-1), t_txt.unsqueeze(-1),
        ], dim=-1)
        weights = self.gate(gate_input)  # [batch, 2]

        # Gated combination
        combined = weights[:, 0:1] * out_img + weights[:, 1:2] * out_txt

        # Total tension = intra-modal + cross-modal
        total_tension = t_img + t_txt + cross_tension

        return combined, total_tension, cross_tension, weights


# ---------------------------------------------------------------------------
# Model 4: Multimodal PureField (simple sum, no gate)
# ---------------------------------------------------------------------------

class MultimodalPureFieldSum(nn.Module):
    def __init__(self, output_dim=10):
        super().__init__()
        self.pf_image = PureFieldEngine(784, 128, output_dim)
        self.pf_text = PureFieldEngine(10, 32, output_dim)

    def forward(self, image, text):
        out_img, t_img = self.pf_image(image)
        out_txt, t_txt = self.pf_text(text)
        cross_tension = ((out_img - out_txt) ** 2).mean(dim=-1)
        combined = out_img + out_txt
        total_tension = t_img + t_txt + cross_tension
        return combined, total_tension, cross_tension


# ---------------------------------------------------------------------------
# Model 5: Naive concat baseline (no PureField)
# ---------------------------------------------------------------------------

class NaiveConcatBaseline(nn.Module):
    def __init__(self, output_dim=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(784 + 10, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, output_dim),
        )

    def forward(self, image, text):
        x = torch.cat([image, text], dim=-1)
        return self.net(x), torch.zeros(image.size(0))


# ---------------------------------------------------------------------------
# Data: MNIST + synthetic text (one-hot digit name)
# ---------------------------------------------------------------------------

def load_multimodal_mnist(batch_size=128, noise_rate=0.0, data_dir='data'):
    """Load MNIST with synthetic one-hot text features.

    Args:
        noise_rate: fraction of text labels to corrupt (0.0 = perfect text)
    """
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,)),
    ])
    train_ds = datasets.MNIST(data_dir, train=True, download=True, transform=transform)
    test_ds = datasets.MNIST(data_dir, train=False, transform=transform)

    def make_multimodal(ds, noise_rate=0.0):
        images = []
        texts = []
        labels = []
        for img, label in ds:
            images.append(img.view(-1))
            # One-hot text = digit name encoding
            text = torch.zeros(10)
            if noise_rate > 0 and np.random.random() < noise_rate:
                # Corrupt: random wrong label
                wrong = label
                while wrong == label:
                    wrong = np.random.randint(0, 10)
                text[wrong] = 1.0
            else:
                text[label] = 1.0
            texts.append(text)
            labels.append(label)
        return TensorDataset(
            torch.stack(images),
            torch.stack(texts),
            torch.tensor(labels, dtype=torch.long),
        )

    train_mm = make_multimodal(train_ds, noise_rate=noise_rate)
    test_mm = make_multimodal(test_ds, noise_rate=0.0)  # test always clean

    train_loader = DataLoader(train_mm, batch_size=batch_size, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_mm, batch_size=batch_size, shuffle=False, num_workers=0)
    return train_loader, test_loader


# ---------------------------------------------------------------------------
# Training loop (multimodal)
# ---------------------------------------------------------------------------

def train_multimodal(model, train_loader, test_loader, epochs=15, lr=1e-3,
                     cross_tension_lambda=0.01, verbose=True):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    acc_history = []
    tension_history = []

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        total_cross_t = 0
        n_batches = 0

        for images, texts, labels in train_loader:
            optimizer.zero_grad()
            result = model(images, texts)

            logits = result[0]
            loss = criterion(logits, labels)

            # If cross-modal tension available, add as regularizer
            # (encourage agreement between modalities)
            if len(result) >= 3:
                cross_t = result[2]
                loss = loss + cross_tension_lambda * cross_t.mean()
                total_cross_t += cross_t.mean().item()

            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            n_batches += 1

        # Evaluate
        model.eval()
        correct = total = 0
        eval_tensions = []
        with torch.no_grad():
            for images, texts, labels in test_loader:
                result = model(images, texts)
                logits = result[0]
                correct += (logits.argmax(1) == labels).sum().item()
                total += labels.size(0)
                if len(result) >= 3:
                    eval_tensions.append(result[2].mean().item())

        acc = correct / total
        acc_history.append(acc)
        avg_cross_t = np.mean(eval_tensions) if eval_tensions else 0
        tension_history.append(avg_cross_t)

        if verbose and (epoch == 0 or (epoch + 1) % 5 == 0 or epoch == epochs - 1):
            print(f"    Epoch {epoch+1:>2}/{epochs}: Loss={total_loss/n_batches:.4f}  "
                  f"Acc={acc*100:.2f}%  CrossTension={avg_cross_t:.4f}")

    return acc_history, tension_history


# ---------------------------------------------------------------------------
# ASCII visualization
# ---------------------------------------------------------------------------

def ascii_bar_chart(data, title="", width=40):
    """Horizontal bar chart. data = list of (name, value)."""
    print(f"\n  {title}")
    print(f"  {'=' * (width + 30)}")
    max_val = max(v for _, v in data) if data else 1
    for name, val in data:
        bar_len = int(val / max_val * width)
        bar = '#' * bar_len
        print(f"  {name:<28} {bar} {val:.2f}%")
    print(f"  {'=' * (width + 30)}")


def ascii_tension_evolution(tensions_dict, epochs):
    """ASCII line chart of cross-modal tension over epochs."""
    if not tensions_dict:
        return
    print(f"\n  Cross-Modal Tension Evolution")
    print(f"  {'=' * 60}")
    all_vals = [v for vals in tensions_dict.values() for v in vals if v > 0]
    if not all_vals:
        print("  (no cross-modal tension data)")
        return
    max_t = max(all_vals)
    min_t = min(all_vals)
    height = 10
    for name, vals in tensions_dict.items():
        if not vals or max(vals) == 0:
            continue
        print(f"  [{name}]")
        for row in range(height, -1, -1):
            threshold = min_t + (max_t - min_t) * row / height if max_t > min_t else 0
            line = "  "
            for v in vals:
                line += "*" if v >= threshold else " "
            if row == height:
                line += f"  {max_t:.4f}"
            elif row == 0:
                line += f"  {min_t:.4f}"
            print(line)
        print(f"  {''.join(str(i % 10) for i in range(len(vals)))}")
    print(f"  {'=' * 60}")


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------

def run_experiment(seed, epochs=15, noise_rate=0.0, verbose=True):
    """Run all 5 models with one seed. Returns dict of results."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    if verbose:
        print(f"\n{'='*60}")
        print(f"  Seed={seed}, Epochs={epochs}, TextNoise={noise_rate:.0%}")
        print(f"{'='*60}")

    train_loader, test_loader = load_multimodal_mnist(
        batch_size=128, noise_rate=noise_rate)

    models = {
        "1. Image-only PF":     ImageOnlyPureField(),
        "2. Text-only PF":      TextOnlyPureField(),
        "3. Multimodal Gated":  MultimodalPureField(),
        "4. Multimodal Sum":    MultimodalPureFieldSum(),
        "5. Naive Concat":      NaiveConcatBaseline(),
    }

    results = {}
    tensions = {}

    for name, model in models.items():
        params = sum(p.numel() for p in model.parameters())
        if verbose:
            print(f"\n  --- {name} (params={params:,}) ---")

        acc_hist, tension_hist = train_multimodal(
            model, train_loader, test_loader,
            epochs=epochs, verbose=verbose,
            cross_tension_lambda=0.01,
        )

        results[name] = {
            'acc': acc_hist[-1],
            'acc_history': acc_hist,
            'params': params,
        }
        tensions[name] = tension_hist

    return results, tensions


def main():
    t0 = time.time()

    print("=" * 60)
    print("  RC-5: Multimodal PureField Experiment")
    print("  Image (MNIST 784D) + Text (one-hot 10D)")
    print("  Cross-modal tension: |PF_image - PF_text|^2")
    print("=" * 60)

    seeds = [42, 137, 256]
    epochs = 15

    # ===== Phase 1: Clean text (perfect one-hot) =====
    print("\n" + "#" * 60)
    print("  PHASE 1: Clean text (0% noise)")
    print("#" * 60)

    all_results_clean = {}
    all_tensions_clean = {}

    for seed in seeds:
        results, tensions = run_experiment(seed, epochs=epochs, noise_rate=0.0)
        for name in results:
            if name not in all_results_clean:
                all_results_clean[name] = []
                all_tensions_clean[name] = []
            all_results_clean[name].append(results[name]['acc'])
            all_tensions_clean[name] = tensions[name]  # last seed for chart

    # ===== Phase 2: Noisy text (30% corruption) =====
    print("\n" + "#" * 60)
    print("  PHASE 2: Noisy text (30% corruption)")
    print("#" * 60)

    all_results_noisy = {}
    all_tensions_noisy = {}

    for seed in seeds:
        results, tensions = run_experiment(seed, epochs=epochs, noise_rate=0.3)
        for name in results:
            if name not in all_results_noisy:
                all_results_noisy[name] = []
                all_tensions_noisy[name] = []
            all_results_noisy[name].append(results[name]['acc'])
            all_tensions_noisy[name] = tensions[name]

    # ===== Summary =====
    print("\n" + "=" * 70)
    print("  FINAL RESULTS: Accuracy Comparison (3 seeds)")
    print("=" * 70)

    # Clean text table
    print(f"\n  Phase 1: Clean text (0% noise)")
    print(f"  {'Model':<28} {'Mean':>7} {'Std':>6} {'Runs':>15}")
    print(f"  {'-'*28} {'-'*7} {'-'*6} {'-'*15}")
    chart_data_clean = []
    for name in sorted(all_results_clean.keys()):
        accs = all_results_clean[name]
        mean_acc = np.mean(accs) * 100
        std_acc = np.std(accs) * 100
        runs_str = ", ".join(f"{a*100:.1f}" for a in accs)
        print(f"  {name:<28} {mean_acc:>6.2f}% {std_acc:>5.2f} [{runs_str}]")
        chart_data_clean.append((name, mean_acc))

    ascii_bar_chart(chart_data_clean, "Phase 1: Clean Text Accuracy")

    # Noisy text table
    print(f"\n  Phase 2: Noisy text (30% noise)")
    print(f"  {'Model':<28} {'Mean':>7} {'Std':>6} {'Runs':>15}")
    print(f"  {'-'*28} {'-'*7} {'-'*6} {'-'*15}")
    chart_data_noisy = []
    for name in sorted(all_results_noisy.keys()):
        accs = all_results_noisy[name]
        mean_acc = np.mean(accs) * 100
        std_acc = np.std(accs) * 100
        runs_str = ", ".join(f"{a*100:.1f}" for a in accs)
        print(f"  {name:<28} {mean_acc:>6.2f}% {std_acc:>5.2f} [{runs_str}]")
        chart_data_noisy.append((name, mean_acc))

    ascii_bar_chart(chart_data_noisy, "Phase 2: Noisy Text Accuracy")

    # Cross-modal tension evolution
    ascii_tension_evolution(all_tensions_clean, epochs)

    # ===== Key analysis =====
    print(f"\n  KEY ANALYSIS")
    print(f"  {'=' * 60}")

    # Compare multimodal gated vs image-only
    gated_clean = np.mean(all_results_clean.get("3. Multimodal Gated", [0]))
    img_clean = np.mean(all_results_clean.get("1. Image-only PF", [0]))
    txt_clean = np.mean(all_results_clean.get("2. Text-only PF", [0]))
    gated_noisy = np.mean(all_results_noisy.get("3. Multimodal Gated", [0]))
    img_noisy = np.mean(all_results_noisy.get("1. Image-only PF", [0]))

    print(f"  Multimodal Gated vs Image-only (clean): "
          f"{(gated_clean - img_clean)*100:+.2f}%")
    print(f"  Multimodal Gated vs Image-only (noisy): "
          f"{(gated_noisy - img_noisy)*100:+.2f}%")
    print(f"  Text-only PF accuracy (clean):          "
          f"{txt_clean*100:.2f}%")

    # Robustness: how much does noisy text hurt?
    gated_drop = (gated_clean - gated_noisy) * 100
    img_drop = (img_clean - img_noisy) * 100
    print(f"\n  Robustness (clean - noisy):")
    print(f"    Multimodal Gated drop: {gated_drop:+.2f}%")
    print(f"    Image-only drop:       {img_drop:+.2f}%")
    print(f"    -> Gated {'is' if gated_drop <= img_drop + 0.5 else 'is NOT'} "
          f"robust to text noise")

    # Cross-modal tension interpretation
    clean_tensions = all_tensions_clean.get("3. Multimodal Gated", [])
    noisy_tensions = all_tensions_noisy.get("3. Multimodal Gated", [])
    if clean_tensions and noisy_tensions:
        print(f"\n  Cross-modal tension (final epoch):")
        print(f"    Clean text: {clean_tensions[-1]:.4f}")
        print(f"    Noisy text: {noisy_tensions[-1]:.4f}")
        if noisy_tensions[-1] > 0:
            ratio = noisy_tensions[-1] / max(clean_tensions[-1], 1e-8)
            print(f"    Noisy/Clean ratio: {ratio:.2f}x")
            print(f"    -> Noisy text {'increases' if ratio > 1.2 else 'does not increase'}"
                  f" cross-modal tension")

    print(f"\n  Elapsed: {time.time() - t0:.1f}s")
    print("=" * 60)


if __name__ == '__main__':
    main()
