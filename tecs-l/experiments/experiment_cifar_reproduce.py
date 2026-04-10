#!/usr/bin/env python3
"""CIFAR-10 Reproduction of MNIST-only constants (🟨 → 🟩 upgrade attempt).

Reproduce 4 key constants on CIFAR-10 that were previously observed only on MNIST:
  C4b:  tension-accuracy Cohen's d (MNIST: 0.89)
  C10:  labelless 1-NN recognition accuracy (MNIST: 97.61%)
  C17:  direction separation ratio intra/inter cosine sim (MNIST: 2.77x)
  C25:  cross-universe ratio (MNIST→CIFAR: 14.4x) — record only

For each: report MNIST vs CIFAR comparison table + ASCII histogram.
Fast mode: 15 epochs, input_dim=3072, hidden_dim=96.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import time
import sys

sys.path.insert(0, '/Users/ghost/Dev/logout')

from model_utils import (
    load_mnist, load_cifar10, train_and_evaluate, count_params
)
from model_meta_engine import (
    EngineA, EngineE, EngineG, EngineF, RepulsionFieldQuad
)


# ─────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────

def ascii_histogram(values, label, bins=20, width=50):
    """Print ASCII histogram of values."""
    counts, edges = np.histogram(values, bins=bins)
    max_count = max(counts) if max(counts) > 0 else 1
    print(f"\n  {label}")
    print(f"  {'─' * (width + 20)}")
    for i, c in enumerate(counts):
        bar_len = int(c / max_count * width)
        lo, hi = edges[i], edges[i+1]
        print(f"  {lo:>8.3f} | {'█' * bar_len} {c}")
    print()


def collect_fingerprints_and_tensions(model, loader, flatten=True):
    """Collect 20-dim fingerprints, scalar tensions, labels, logits, and per-engine outputs."""
    model.eval()
    all_fp, all_scalars, all_labels, all_logits = [], [], [], []
    all_out_a, all_out_g, all_out_e, all_out_f = [], [], [], []

    with torch.no_grad():
        for X, y in loader:
            if flatten:
                X = X.view(X.size(0), -1)

            out_a = model.engine_a(X)
            out_e = model.engine_e(X)
            out_g = model.engine_g(X)
            out_f = model.engine_f(X)

            repulsion_content = out_a - out_g
            repulsion_structure = out_e - out_f

            fingerprint = torch.cat([repulsion_content, repulsion_structure], dim=-1)
            t_content = (repulsion_content ** 2).sum(dim=-1)
            t_structure = (repulsion_structure ** 2).sum(dim=-1)
            scalars = torch.stack([t_content, t_structure], dim=-1)

            logits, _ = model(X)

            all_fp.append(fingerprint)
            all_scalars.append(scalars)
            all_labels.append(y)
            all_logits.append(logits)
            all_out_a.append(out_a)
            all_out_g.append(out_g)
            all_out_e.append(out_e)
            all_out_f.append(out_f)

    return {
        'fingerprints': torch.cat(all_fp, 0),
        'scalars': torch.cat(all_scalars, 0),
        'labels': torch.cat(all_labels, 0),
        'logits': torch.cat(all_logits, 0),
        'out_a': torch.cat(all_out_a, 0),
        'out_g': torch.cat(all_out_g, 0),
        'out_e': torch.cat(all_out_e, 0),
        'out_f': torch.cat(all_out_f, 0),
    }


def train_model(model, train_loader, test_loader, epochs=15, lr=0.001, flatten=True):
    """Train RepulsionFieldQuad with aux loss."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for X, y in train_loader:
            if flatten:
                X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            logits, aux = model(X)
            loss = criterion(logits, y) + 0.1 * aux
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        if (epoch + 1) % 3 == 0 or epoch == 0:
            model.eval()
            correct = total = 0
            with torch.no_grad():
                for X, y in test_loader:
                    if flatten:
                        X = X.view(X.size(0), -1)
                    logits, _ = model(X)
                    correct += (logits.argmax(1) == y).sum().item()
                    total += y.size(0)
            acc = correct / total
            print(f"    Epoch {epoch+1:>2}/{epochs}: Loss={total_loss/len(train_loader):.4f}, Acc={acc*100:.2f}%")

    # Final accuracy
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for X, y in test_loader:
            if flatten:
                X = X.view(X.size(0), -1)
            logits, _ = model(X)
            correct += (logits.argmax(1) == y).sum().item()
            total += y.size(0)
    return correct / total


# ─────────────────────────────────────────
# C4b: Tension-accuracy Cohen's d
# ─────────────────────────────────────────

def measure_c4b(data, dataset_name):
    """Cohen's d: mean tension of correct vs wrong predictions."""
    logits = data['logits']
    labels = data['labels']
    scalars = data['scalars']

    preds = logits.argmax(dim=1)
    correct_mask = preds == labels
    wrong_mask = ~correct_mask

    # Total tension = geometric mean of two axes
    total_tension = torch.sqrt(scalars[:, 0] * scalars[:, 1] + 1e-8).numpy()

    t_correct = total_tension[correct_mask.numpy()]
    t_wrong = total_tension[wrong_mask.numpy()]

    if len(t_wrong) < 5:
        print(f"  [C4b] {dataset_name}: Too few wrong predictions for Cohen's d")
        return None

    mean_c, mean_w = t_correct.mean(), t_wrong.mean()
    std_pooled = np.sqrt((t_correct.var() * len(t_correct) + t_wrong.var() * len(t_wrong))
                         / (len(t_correct) + len(t_wrong)))

    d = (mean_w - mean_c) / (std_pooled + 1e-8)

    print(f"\n  [C4b] {dataset_name}: Tension-Accuracy Cohen's d")
    print(f"    Correct samples: {len(t_correct):>6}, mean tension: {mean_c:.4f}")
    print(f"    Wrong   samples: {len(t_wrong):>6}, mean tension: {mean_w:.4f}")
    print(f"    Cohen's d = {d:.4f}  {'(STRONG d>0.8)' if d > 0.8 else '(MEDIUM d>0.5)' if d > 0.5 else '(WEAK)'}")

    ascii_histogram(t_correct, f"Correct ({dataset_name})", bins=15)
    ascii_histogram(t_wrong, f"Wrong ({dataset_name})", bins=15)

    return d


# ─────────────────────────────────────────
# C10: Labelless 1-NN recognition
# ─────────────────────────────────────────

def measure_c10(data, dataset_name, n_query=2000):
    """1-NN recognition using tension fingerprints only (no labels at query time)."""
    fp = data['fingerprints']
    labels = data['labels']
    logits = data['logits']

    n = fp.size(0)
    # Use first half as gallery, second half as query (up to n_query)
    half = n // 2
    gallery_fp = fp[:half]
    gallery_labels = labels[:half]
    query_fp = fp[half:half + n_query]
    query_labels = labels[half:half + n_query]
    query_logits = logits[half:half + n_query]

    # 1-NN by L2 distance
    dists = torch.cdist(query_fp, gallery_fp)  # (n_query, half)
    nn_idx = dists.argmin(dim=1)
    nn_labels = gallery_labels[nn_idx]

    labelless_acc = (nn_labels == query_labels).float().mean().item()
    softmax_acc = (query_logits.argmax(1) == query_labels).float().mean().item()

    print(f"\n  [C10] {dataset_name}: Labelless 1-NN Recognition")
    print(f"    Gallery size: {half}, Query size: {len(query_labels)}")
    print(f"    1-NN (tension fingerprint): {labelless_acc*100:.2f}%")
    print(f"    Softmax (classification):   {softmax_acc*100:.2f}%")
    print(f"    Ratio (1-NN / softmax):     {labelless_acc/softmax_acc:.4f}")

    return labelless_acc, softmax_acc


# ─────────────────────────────────────────
# C17: Direction separation ratio
# ─────────────────────────────────────────

def measure_c17(data, dataset_name, n_samples=3000):
    """Intra-class vs inter-class cosine similarity of repulsion vectors."""
    repulsion = data['out_a'][:n_samples] - data['out_g'][:n_samples]  # content axis
    labels = data['labels'][:n_samples]

    # Normalize
    repulsion_norm = F.normalize(repulsion, dim=1)

    intra_sims = []
    inter_sims = []

    classes = labels.unique().tolist()
    for c in classes:
        mask_c = labels == c
        vecs_c = repulsion_norm[mask_c]
        if vecs_c.size(0) < 2:
            continue

        # Intra-class: pairwise cosine sim (sample pairs)
        n_c = min(vecs_c.size(0), 200)
        idx = torch.randperm(vecs_c.size(0))[:n_c]
        vecs_sample = vecs_c[idx]
        sim_matrix = vecs_sample @ vecs_sample.T
        mask_upper = torch.triu(torch.ones(n_c, n_c, dtype=torch.bool), diagonal=1)
        intra_sims.extend(sim_matrix[mask_upper].tolist())

        # Inter-class: compare with random other class samples
        other_mask = labels != c
        other_vecs = repulsion_norm[other_mask]
        n_other = min(other_vecs.size(0), 200)
        idx_other = torch.randperm(other_vecs.size(0))[:n_other]
        inter_sim = (vecs_sample[:50] @ other_vecs[idx_other].T).flatten()
        inter_sims.extend(inter_sim.tolist())

    intra_mean = np.mean(intra_sims)
    inter_mean = np.mean(inter_sims)
    ratio = abs(intra_mean) / (abs(inter_mean) + 1e-8)

    print(f"\n  [C17] {dataset_name}: Direction Separation Ratio")
    print(f"    Intra-class cosine sim: {intra_mean:.4f}")
    print(f"    Inter-class cosine sim: {inter_mean:.4f}")
    print(f"    Separation ratio:       {ratio:.2f}x")

    ascii_histogram(intra_sims[:2000], f"Intra-class cos sim ({dataset_name})", bins=15)
    ascii_histogram(inter_sims[:2000], f"Inter-class cos sim ({dataset_name})", bins=15)

    return ratio, intra_mean, inter_mean


# ─────────────────────────────────────────
# C25: Cross-universe (record only)
# ─────────────────────────────────────────

def measure_c25(mnist_data, cifar_data):
    """Cross-universe: tension magnitude ratio between MNIST and CIFAR models."""
    mnist_tension = torch.sqrt(mnist_data['scalars'][:, 0] * mnist_data['scalars'][:, 1] + 1e-8)
    cifar_tension = torch.sqrt(cifar_data['scalars'][:, 0] * cifar_data['scalars'][:, 1] + 1e-8)

    mnist_mean = mnist_tension.mean().item()
    cifar_mean = cifar_tension.mean().item()
    ratio = max(mnist_mean, cifar_mean) / (min(mnist_mean, cifar_mean) + 1e-8)

    print(f"\n  [C25] Cross-Universe Tension Ratio")
    print(f"    MNIST mean tension:  {mnist_mean:.4f}")
    print(f"    CIFAR mean tension:  {cifar_mean:.4f}")
    print(f"    Ratio (max/min):     {ratio:.2f}x")

    return ratio


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────

def main():
    print("=" * 70)
    print("  CIFAR-10 Reproduction of MNIST-only Constants")
    print("  Goal: Upgrade 🟨 (MNIST-only) → 🟩 (reproduced on CIFAR)")
    print("=" * 70)

    t0 = time.time()

    # ── MNIST ──
    print("\n" + "─" * 70)
    print("  Phase 1: Train RepulsionFieldQuad on MNIST (15 epochs)")
    print("─" * 70)

    mnist_train, mnist_test = load_mnist(batch_size=128, data_dir='/Users/ghost/Dev/logout/data')
    model_mnist = RepulsionFieldQuad(input_dim=784, hidden_dim=48, output_dim=10)
    print(f"  Parameters: {count_params(model_mnist):,}")

    mnist_acc = train_model(model_mnist, mnist_train, mnist_test, epochs=15, flatten=True)
    print(f"  Final MNIST accuracy: {mnist_acc*100:.2f}%")

    print("\n  Collecting MNIST fingerprints...")
    mnist_data = collect_fingerprints_and_tensions(model_mnist, mnist_test, flatten=True)

    # ── CIFAR ──
    print("\n" + "─" * 70)
    print("  Phase 2: Train RepulsionFieldQuad on CIFAR-10 (15 epochs)")
    print("─" * 70)

    cifar_train, cifar_test = load_cifar10(batch_size=128, data_dir='/Users/ghost/Dev/logout/data')
    model_cifar = RepulsionFieldQuad(input_dim=3072, hidden_dim=96, output_dim=10)
    print(f"  Parameters: {count_params(model_cifar):,}")

    cifar_acc = train_model(model_cifar, cifar_train, cifar_test, epochs=15, flatten=True)
    print(f"  Final CIFAR accuracy: {cifar_acc*100:.2f}%")

    print("\n  Collecting CIFAR fingerprints...")
    cifar_data = collect_fingerprints_and_tensions(model_cifar, cifar_test, flatten=True)

    # ── Measurements ──
    print("\n" + "=" * 70)
    print("  Phase 3: Measure Constants")
    print("=" * 70)

    # C4b
    print("\n" + "─" * 70)
    print("  C4b: Tension-Accuracy Cohen's d")
    print("─" * 70)
    d_mnist = measure_c4b(mnist_data, "MNIST")
    d_cifar = measure_c4b(cifar_data, "CIFAR")

    # C10
    print("\n" + "─" * 70)
    print("  C10: Labelless 1-NN Recognition")
    print("─" * 70)
    c10_mnist_acc, c10_mnist_soft = measure_c10(mnist_data, "MNIST")
    c10_cifar_acc, c10_cifar_soft = measure_c10(cifar_data, "CIFAR")

    # C17
    print("\n" + "─" * 70)
    print("  C17: Direction Separation Ratio")
    print("─" * 70)
    c17_mnist_ratio, c17_mnist_intra, c17_mnist_inter = measure_c17(mnist_data, "MNIST")
    c17_cifar_ratio, c17_cifar_intra, c17_cifar_inter = measure_c17(cifar_data, "CIFAR")

    # C25
    print("\n" + "─" * 70)
    print("  C25: Cross-Universe Tension Ratio")
    print("─" * 70)
    c25_ratio = measure_c25(mnist_data, cifar_data)

    # ── Summary ──
    elapsed = time.time() - t0
    print("\n" + "=" * 70)
    print("  SUMMARY: MNIST vs CIFAR Constant Comparison")
    print("=" * 70)

    print(f"""
  ┌──────────┬───────────────────────┬──────────────┬──────────────┬──────────┐
  │ Constant │ Description           │    MNIST     │   CIFAR-10   │ Verdict  │
  ├──────────┼───────────────────────┼──────────────┼──────────────┼──────────┤""")

    # C4b verdict
    c4b_verdict = "REPRODUCED" if d_cifar is not None and d_cifar > 0.5 else "WEAK" if d_cifar is not None and d_cifar > 0.2 else "FAILED"
    d_mnist_str = f"d={d_mnist:.2f}" if d_mnist is not None else "N/A"
    d_cifar_str = f"d={d_cifar:.2f}" if d_cifar is not None else "N/A"
    print(f"  │ C4b      │ Tension-Acc Cohen's d │ {d_mnist_str:>12} │ {d_cifar_str:>12} │ {c4b_verdict:>8} │")

    # C10 verdict
    c10_verdict = "REPRODUCED" if c10_cifar_acc > 0.30 else "WEAK" if c10_cifar_acc > 0.20 else "FAILED"
    print(f"  │ C10      │ Labelless 1-NN acc    │ {c10_mnist_acc*100:>10.2f}%  │ {c10_cifar_acc*100:>10.2f}%  │ {c10_verdict:>8} │")

    # C17 verdict
    c17_verdict = "REPRODUCED" if c17_cifar_ratio > 1.5 else "WEAK" if c17_cifar_ratio > 1.2 else "FAILED"
    print(f"  │ C17      │ Direction sep ratio   │ {c17_mnist_ratio:>10.2f}x  │ {c17_cifar_ratio:>10.2f}x  │ {c17_verdict:>8} │")

    # C25
    print(f"  │ C25      │ Cross-universe ratio  │ {'(reference)':>12} │ {c25_ratio:>10.2f}x  │ RECORDED │")

    print(f"""  └──────────┴───────────────────────┴──────────────┴──────────────┴──────────┘

  Model accuracies: MNIST={mnist_acc*100:.2f}%, CIFAR={cifar_acc*100:.2f}%
  Time elapsed: {elapsed:.1f}s

  Upgrade criteria:
    C4b:  d > 0.5 on CIFAR → 🟩 (medium+ effect size)
    C10:  1-NN > 30% on CIFAR → 🟩 (well above 10% random baseline)
    C17:  ratio > 1.5x on CIFAR → 🟩 (meaningful direction separation)
    C25:  ratio recorded (cross-dataset measurement)
""")

    # ── Per-constant upgrade recommendation ──
    print("  UPGRADE RECOMMENDATIONS:")
    n_upgraded = 0
    for name, verdict in [("C4b", c4b_verdict), ("C10", c10_verdict),
                           ("C17", c17_verdict), ("C25", "RECORDED")]:
        if verdict == "REPRODUCED":
            print(f"    {name}: 🟨 → 🟩  (reproduced on CIFAR)")
            n_upgraded += 1
        elif verdict == "RECORDED":
            print(f"    {name}: 🟨 → 🟨  (cross-dataset, recorded)")
        elif verdict == "WEAK":
            print(f"    {name}: 🟨 → 🟧  (weak reproduction, needs more epochs)")
        else:
            print(f"    {name}: 🟨 stays (not reproduced)")

    print(f"\n  Total upgradeable to 🟩: {n_upgraded}/3")
    print("=" * 70)


if __name__ == "__main__":
    main()
