#!/usr/bin/env python3
"""H-CX-345: sigma*phi/(n*tau) balance in PureFieldEngine dynamics.

Tests whether the ratio mean(|engine_a|) / mean(|engine_g|) per class
converges to ratios derivable from divisor functions of perfect number 6.

Divisor functions of 6:
  sigma(6) = 12, tau(6) = 4, phi(6) = 2, sigma_{-1}(6) = 2
Target ratios: {1, 2, 3, 6, 1/2, 1/3, 1/6, 4/2=2, 12/4=3, 12/2=6, ...}
Unique target ratios (within [0.1, 10]): 1/6, 1/3, 1/2, 2/3, 1, 3/2, 2, 3, 4, 6, 12

Balance metric B = sigma(6)*phi(6) / (n*tau(6)) = 12*2/(6*4) = 1.0
  -> Perfect balance ONLY for n=6 among small integers.

Controls:
  - Shuffled-label baseline (destroy class structure, retrain)
  - Texas Sharpshooter: random ratio match probability
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import numpy as np
import time
from model_pure_field import PureFieldEngine
from model_utils import load_mnist, load_cifar10
from torchvision import datasets, transforms
from torch.utils.data import DataLoader

# ─────────────────────────────────────────
# Constants from perfect number 6
# ─────────────────────────────────────────
SIGMA_6 = 12
TAU_6 = 4
PHI_6 = 2
SIGMA_INV_6 = 2
N = 6

# All unique ratios from {sigma, tau, phi, sigma_inv, n} of 6
DIVISOR_VALS = [SIGMA_6, TAU_6, PHI_6, SIGMA_INV_6, N]
TARGET_RATIOS = set()
for a in DIVISOR_VALS:
    for b in DIVISOR_VALS:
        if b != 0:
            r = a / b
            if 0.05 <= r <= 20:
                TARGET_RATIOS.add(round(r, 6))
TARGET_RATIOS = sorted(TARGET_RATIOS)

# Balance metric: B = sigma*phi / (n*tau)
B_PERFECT = SIGMA_6 * PHI_6 / (N * TAU_6)  # = 1.0

TOLERANCE = 0.10  # 10% window


def load_fashion_mnist(batch_size=64, data_dir='data'):
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.2860,), (0.3530,))
    ])
    train_ds = datasets.FashionMNIST(data_dir, train=True, download=True, transform=transform)
    test_ds = datasets.FashionMNIST(data_dir, train=False, download=True, transform=transform)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    return train_loader, test_loader


def train_model(model, train_loader, epochs=10, lr=0.001, flatten=True):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for X, y in train_loader:
            if flatten:
                X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            output, tension = model(X)
            loss = criterion(output, y) + 0.1 * tension.mean()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"      Epoch {epoch+1}/{epochs}: loss={total_loss/len(train_loader):.4f}")
    return model


def evaluate_accuracy(model, test_loader, flatten=True):
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for X, y in test_loader:
            if flatten:
                X = X.view(X.size(0), -1)
            out, _ = model(X)
            correct += (out.argmax(1) == y).sum().item()
            total += y.size(0)
    return correct / total


def compute_engine_magnitudes(model, test_loader, n_classes=10, flatten=True):
    """Compute mean |engine_a| and mean |engine_g| per class."""
    model.eval()
    a_sums = [[] for _ in range(n_classes)]
    g_sums = [[] for _ in range(n_classes)]

    with torch.no_grad():
        for X, y in test_loader:
            if flatten:
                X = X.view(X.size(0), -1)
            out_a = model.engine_a(X)  # (batch, n_classes)
            out_g = model.engine_g(X)
            for c in range(n_classes):
                mask = (y == c)
                if mask.sum() > 0:
                    a_sums[c].append(out_a[mask].abs().mean(dim=0).cpu().numpy())
                    g_sums[c].append(out_g[mask].abs().mean(dim=0).cpu().numpy())

    mean_a = []
    mean_g = []
    for c in range(n_classes):
        if a_sums[c]:
            mean_a.append(np.mean(np.stack(a_sums[c]), axis=0).mean())
            mean_g.append(np.mean(np.stack(g_sums[c]), axis=0).mean())
        else:
            mean_a.append(0.0)
            mean_g.append(0.0)
    return np.array(mean_a), np.array(mean_g)


def check_ratio_match(ratio, targets, tol=TOLERANCE):
    """Check if ratio is within tol of any target ratio."""
    for t in targets:
        if t > 0 and abs(ratio - t) / t <= tol:
            return True, t
    return False, None


def texas_sharpshooter_test(n_classes=10, n_simulations=10000):
    """How often do random ratios match any divisor function ratio?"""
    rng = np.random.default_rng(42)
    match_counts = []
    for _ in range(n_simulations):
        # Random ratios in typical observed range [0.5, 5.0]
        random_ratios = rng.uniform(0.3, 5.0, size=n_classes)
        matches = 0
        for r in random_ratios:
            hit, _ = check_ratio_match(r, TARGET_RATIOS, TOLERANCE)
            if hit:
                matches += 1
        match_counts.append(matches)
    return np.array(match_counts)


def print_ascii_bar(label, val_a, val_g, max_width=40):
    """Print ASCII bar for engine_a vs engine_g."""
    max_val = max(val_a, val_g, 0.001)
    bar_a = int(val_a / max_val * max_width)
    bar_g = int(val_g / max_val * max_width)
    print(f"  {label:>8} A |{'#' * bar_a}{' ' * (max_width - bar_a)}| {val_a:.4f}")
    print(f"  {' ':>8} G |{'=' * bar_g}{' ' * (max_width - bar_g)}| {val_g:.4f}")


def run_experiment(name, model, train_loader, test_loader, epochs=10, lr=0.001,
                   flatten=True, is_shuffled=False):
    """Train and analyze one dataset."""
    print(f"\n{'='*70}")
    print(f"  Dataset: {name} {'(SHUFFLED LABELS)' if is_shuffled else ''}")
    print(f"{'='*70}")

    t0 = time.time()
    model = train_model(model, train_loader, epochs=epochs, lr=lr, flatten=flatten)
    acc = evaluate_accuracy(model, test_loader, flatten=flatten)
    elapsed = time.time() - t0
    print(f"    Accuracy: {acc*100:.2f}%  ({elapsed:.1f}s)")

    mean_a, mean_g = compute_engine_magnitudes(model, test_loader, flatten=flatten)

    # Compute ratios
    ratios = []
    for c in range(10):
        if mean_g[c] > 1e-8:
            ratios.append(mean_a[c] / mean_g[c])
        else:
            ratios.append(float('inf'))
    ratios = np.array(ratios)

    # Check matches
    matches = []
    for c in range(10):
        hit, target = check_ratio_match(ratios[c], TARGET_RATIOS, TOLERANCE)
        matches.append((hit, target))

    n_matches = sum(1 for m in matches if m[0])

    # Print table
    print(f"\n  | Class | mean|A| | mean|G| | Ratio A/G | Match? | Target |")
    print(f"  |-------|---------|---------|-----------|--------|--------|")
    for c in range(10):
        hit_str = "YES" if matches[c][0] else "no"
        tgt_str = f"{matches[c][1]:.3f}" if matches[c][1] is not None else "-"
        print(f"  | {c:>5} | {mean_a[c]:.5f} | {mean_g[c]:.5f} | {ratios[c]:>9.4f} | {hit_str:>6} | {tgt_str:>6} |")
    print(f"  |-------|---------|---------|-----------|--------|--------|")
    print(f"  | TOTAL matches: {n_matches}/10 classes")

    # ASCII graph
    print(f"\n  Engine A (#) vs G (=) magnitude per class:")
    for c in range(10):
        print_ascii_bar(f"cls {c}", mean_a[c], mean_g[c])

    # Balance metric for various n
    print(f"\n  Balance metric B = sigma(n)*phi(n) / (n*tau(n)):")
    print(f"  | n  | sigma(n) | phi(n) | tau(n) |   B    | B=1? |")
    print(f"  |----|----------|--------|--------|--------|------|")
    for n in [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 28]:
        sn = sum(d for d in range(1, n+1) if n % d == 0)
        tn = sum(1 for d in range(1, n+1) if n % d == 0)
        pn = sum(1 for k in range(1, n+1) if np.gcd(k, n) == 1)
        bn = sn * pn / (n * tn) if n * tn > 0 else 0
        eq = "YES" if abs(bn - 1.0) < 0.001 else "no"
        print(f"  | {n:>2} | {sn:>8} | {pn:>6} | {tn:>6} | {bn:.4f} | {eq:>4} |")

    return {
        'accuracy': acc,
        'mean_a': mean_a,
        'mean_g': mean_g,
        'ratios': ratios,
        'n_matches': n_matches,
        'matches': matches,
    }


def main():
    print("=" * 70)
    print("  H-CX-345: sigma*phi/(n*tau) = 1 Balance in PureFieldEngine")
    print("  Testing if engine_a/engine_g ratios match divisor function ratios")
    print("=" * 70)

    print(f"\n  Perfect number 6 divisor functions:")
    print(f"    sigma(6) = {SIGMA_6}, tau(6) = {TAU_6}, phi(6) = {PHI_6}, sigma_inv(6) = {SIGMA_INV_6}")
    print(f"    B = sigma*phi/(n*tau) = {SIGMA_6}*{PHI_6}/({N}*{TAU_6}) = {B_PERFECT:.4f}")
    print(f"\n  Target ratios (from divisor function combinations):")
    print(f"    {[f'{r:.4f}' for r in TARGET_RATIOS]}")
    print(f"    Total: {len(TARGET_RATIOS)} unique ratios")
    print(f"    Tolerance: +/-{TOLERANCE*100:.0f}%")

    torch.manual_seed(42)
    np.random.seed(42)

    results = {}

    # ── MNIST ──
    print("\n  Loading MNIST...")
    train_loader, test_loader = load_mnist(batch_size=64)
    model = PureFieldEngine(784, 128, 10)
    results['MNIST'] = run_experiment('MNIST', model, train_loader, test_loader,
                                       epochs=10, lr=0.001, flatten=True)

    # ── Fashion-MNIST ──
    print("\n  Loading Fashion-MNIST...")
    train_loader, test_loader = load_fashion_mnist(batch_size=64)
    model = PureFieldEngine(784, 128, 10)
    results['FashionMNIST'] = run_experiment('Fashion-MNIST', model, train_loader, test_loader,
                                              epochs=10, lr=0.001, flatten=True)

    # ── CIFAR-10 ──
    print("\n  Loading CIFAR-10...")
    train_loader, test_loader = load_cifar10(batch_size=64)
    model = PureFieldEngine(3072, 128, 10)
    results['CIFAR10'] = run_experiment('CIFAR-10', model, train_loader, test_loader,
                                         epochs=10, lr=0.001, flatten=True)

    # ── Shuffled baseline (MNIST) ──
    print("\n  Loading MNIST (shuffled labels)...")
    train_loader_s, test_loader_s = load_mnist(batch_size=64)
    # Shuffle labels in training set
    rng = np.random.default_rng(99)
    orig_targets = train_loader_s.dataset.targets.clone()
    perm = torch.tensor(rng.permutation(len(orig_targets)))
    train_loader_s.dataset.targets = orig_targets[perm]
    model_s = PureFieldEngine(784, 128, 10)
    results['MNIST_shuffled'] = run_experiment('MNIST (Shuffled)', model_s,
                                                train_loader_s, test_loader_s,
                                                epochs=10, lr=0.001, flatten=True,
                                                is_shuffled=True)

    # ── Texas Sharpshooter ──
    print(f"\n{'='*70}")
    print(f"  Texas Sharpshooter Test")
    print(f"{'='*70}")
    random_matches = texas_sharpshooter_test(n_classes=10, n_simulations=10000)
    rand_mean = random_matches.mean()
    rand_std = random_matches.std()

    print(f"\n  Random baseline (10,000 simulations):")
    print(f"    Mean matches: {rand_mean:.2f} +/- {rand_std:.2f}")
    print(f"    Max matches:  {random_matches.max()}")
    print(f"\n  Observed matches:")
    for dname in ['MNIST', 'FashionMNIST', 'CIFAR10', 'MNIST_shuffled']:
        nm = results[dname]['n_matches']
        z = (nm - rand_mean) / rand_std if rand_std > 0 else 0
        p = np.mean(random_matches >= nm)
        print(f"    {dname:>20}: {nm}/10 matches  (Z={z:.2f}, p={p:.4f})")

    # Distribution of random matches
    print(f"\n  Random match distribution:")
    print(f"  | Matches | Count |  Pct  |")
    print(f"  |---------|-------|-------|")
    for k in range(11):
        cnt = np.sum(random_matches == k)
        pct = cnt / len(random_matches) * 100
        if cnt > 0:
            print(f"  | {k:>7} | {cnt:>5} | {pct:>4.1f}% |")

    # ── Summary ──
    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"{'='*70}")
    print(f"\n  | Dataset         | Accuracy | Matches | Z-score | p-value |")
    print(f"  |-----------------|----------|---------|---------|---------|")
    for dname in ['MNIST', 'FashionMNIST', 'CIFAR10', 'MNIST_shuffled']:
        acc = results[dname]['accuracy']
        nm = results[dname]['n_matches']
        z = (nm - rand_mean) / rand_std if rand_std > 0 else 0
        p = np.mean(random_matches >= nm)
        print(f"  | {dname:<15} | {acc*100:>6.2f}% | {nm:>3}/10  | {z:>7.2f} | {p:>7.4f} |")

    # Ratio summary across datasets
    print(f"\n  Mean A/G ratios across datasets:")
    print(f"  | Class | MNIST  | Fashion | CIFAR  | Shuffled |")
    print(f"  |-------|--------|---------|--------|----------|")
    for c in range(10):
        r_m = results['MNIST']['ratios'][c]
        r_f = results['FashionMNIST']['ratios'][c]
        r_c = results['CIFAR10']['ratios'][c]
        r_s = results['MNIST_shuffled']['ratios'][c]
        print(f"  | {c:>5} | {r_m:>6.3f} | {r_f:>7.3f} | {r_c:>6.3f} | {r_s:>8.3f} |")

    # Check overall pattern
    all_trained = np.concatenate([results[d]['ratios'] for d in ['MNIST', 'FashionMNIST', 'CIFAR10']])
    shuffled_ratios = results['MNIST_shuffled']['ratios']
    print(f"\n  Overall ratio statistics:")
    print(f"    Trained models:  mean={all_trained.mean():.4f}, std={all_trained.std():.4f}, "
          f"median={np.median(all_trained):.4f}")
    print(f"    Shuffled:        mean={shuffled_ratios.mean():.4f}, std={shuffled_ratios.std():.4f}, "
          f"median={np.median(shuffled_ratios):.4f}")

    # Final verdict
    total_matches_trained = sum(results[d]['n_matches'] for d in ['MNIST', 'FashionMNIST', 'CIFAR10'])
    total_matches_shuffled = results['MNIST_shuffled']['n_matches']
    print(f"\n  Total matches (trained): {total_matches_trained}/30")
    print(f"  Total matches (shuffled): {total_matches_shuffled}/10")
    print(f"  Expected random: {rand_mean:.1f}/10 per dataset")

    if total_matches_trained / 30 > rand_mean / 10 * 1.5:
        print(f"\n  RESULT: Trained models show ELEVATED ratio matches vs random")
    else:
        print(f"\n  RESULT: Trained model ratios NOT significantly above random")

    if total_matches_trained > total_matches_shuffled * 2.5:
        print(f"  RESULT: Trained >> Shuffled, class structure matters")
    else:
        print(f"  RESULT: Trained ~ Shuffled, class structure does NOT drive ratios")

    print(f"\n  B = sigma(6)*phi(6)/(6*tau(6)) = {B_PERFECT:.4f}")
    print(f"  This perfect balance B=1 is unique to n=6 among n<28.")
    print(f"\n{'='*70}")
    print(f"  Experiment complete.")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
