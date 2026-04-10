#!/usr/bin/env python3
"""H-CX-26 Verification: Tension = Calibrated Probability (Calibration)

Calibration comparison of softmax probability vs tension-based probability.
Expected Calibration Error (ECE) measurement + Reliability diagram output.

Comparison on 2 datasets: MNIST + Fashion-MNIST.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from model_pure_field import PureFieldEngine
from model_utils import load_mnist

def load_fashion(batch_size=128, data_dir='data'):
    from torchvision import datasets, transforms
    from torch.utils.data import DataLoader
    transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.2860,), (0.3530,))])
    train_ds = datasets.FashionMNIST(data_dir, train=True, download=True, transform=transform)
    test_ds = datasets.FashionMNIST(data_dir, train=False, transform=transform)
    return DataLoader(train_ds, batch_size=batch_size, shuffle=True), DataLoader(test_ds, batch_size=batch_size, shuffle=False)

def train_model(model, train_loader, epochs=15, lr=0.001):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    for epoch in range(epochs):
        model.train()
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            logits, tension = model(X)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
    return model

def collect_predictions(model, test_loader):
    """Collect softmax probs, tensions, predictions, and labels."""
    all_softmax_conf = []
    all_tension = []
    all_pred = []
    all_label = []
    all_correct = []

    model.eval()
    with torch.no_grad():
        for X, y in test_loader:
            X = X.view(X.size(0), -1)
            logits, tension = model(X)

            softmax_probs = F.softmax(logits, dim=-1)
            max_prob, pred = softmax_probs.max(dim=-1)
            correct = (pred == y).float()

            all_softmax_conf.append(max_prob.numpy())
            all_tension.append(tension.numpy())
            all_pred.append(pred.numpy())
            all_label.append(y.numpy())
            all_correct.append(correct.numpy())

    return {
        'softmax_conf': np.concatenate(all_softmax_conf),
        'tension': np.concatenate(all_tension),
        'pred': np.concatenate(all_pred),
        'label': np.concatenate(all_label),
        'correct': np.concatenate(all_correct),
    }

def compute_ece(confidences, accuracies, n_bins=15):
    """Expected Calibration Error."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    bin_data = []
    for i in range(n_bins):
        lo, hi = bin_boundaries[i], bin_boundaries[i+1]
        mask = (confidences >= lo) & (confidences < hi)
        if mask.sum() == 0:
            bin_data.append((lo, hi, 0, 0, 0))
            continue
        bin_acc = accuracies[mask].mean()
        bin_conf = confidences[mask].mean()
        bin_count = mask.sum()
        ece += (bin_count / len(confidences)) * abs(bin_acc - bin_conf)
        bin_data.append((lo, hi, bin_acc, bin_conf, bin_count))
    return ece, bin_data

def tension_to_confidence(tension, method='sigmoid'):
    """Convert tension to confidence score in [0,1]."""
    t = tension.copy()
    # Normalize to [0,1] using percentile-based scaling
    p5, p95 = np.percentile(t, 5), np.percentile(t, 95)
    t_norm = np.clip((t - p5) / (p95 - p5 + 1e-8), 0, 1)
    return t_norm

def print_reliability_diagram(bin_data, title):
    """ASCII reliability diagram."""
    print(f"\n  === {title} ===")
    print(f"  {'Bin':>10} {'Count':>6} {'Acc':>6} {'Conf':>6} {'|Gap|':>6}")
    print(f"  {'─'*10} {'─'*6} {'─'*6} {'─'*6} {'─'*6}")
    for lo, hi, acc, conf, count in bin_data:
        if count == 0:
            continue
        gap = abs(acc - conf)
        bar_acc = '█' * int(acc * 20) if acc > 0 else ''
        bar_conf = '░' * int(conf * 20) if conf > 0 else ''
        print(f"  [{lo:.2f},{hi:.2f}) {count:>6} {acc:>5.3f} {conf:>5.3f} {gap:>5.3f}  {bar_acc}")
        print(f"  {'':>10} {'':>6} {'':>6} {'':>6} {'':>6}  {bar_conf}")

def ascii_calibration_plot(bin_data, title):
    """ASCII calibration curve: acc vs conf."""
    print(f"\n  {title}")
    print(f"  Accuracy")
    print(f"  1.0 |", end="")

    # Build grid
    rows = 10
    cols = 15
    grid = [[' ' for _ in range(cols)] for _ in range(rows)]

    # Perfect calibration diagonal
    for i in range(min(rows, cols)):
        r = rows - 1 - i
        c = int(i * cols / rows)
        if 0 <= r < rows and 0 <= c < cols:
            grid[r][c] = '·'

    # Plot actual points
    for lo, hi, acc, conf, count in bin_data:
        if count == 0:
            continue
        mid_conf = (lo + hi) / 2
        c = min(int(mid_conf * cols), cols - 1)
        r = rows - 1 - min(int(acc * rows), rows - 1)
        if 0 <= r < rows and 0 <= c < cols:
            grid[r][c] = '●'

    for r in range(rows):
        val = 1.0 - r * (1.0 / rows)
        line = ''.join(grid[r])
        print(f"  {val:.1f} |{line}|")
    print(f"  0.0 +{'─' * cols}+")
    print(f"       0.0{' ' * (cols - 6)}1.0")
    print(f"            Confidence")

def run_experiment(dataset_name, train_loader, test_loader, n_trials=3):
    """Run calibration experiment for one dataset."""
    print(f"\n{'='*60}")
    print(f"  H-CX-26 Verification: {dataset_name}")
    print(f"{'='*60}")

    all_ece_softmax = []
    all_ece_tension = []

    for trial in range(n_trials):
        model = PureFieldEngine(784, 128, 10)
        model = train_model(model, train_loader, epochs=15)
        data = collect_predictions(model, test_loader)

        acc = data['correct'].mean()
        print(f"\n  Trial {trial+1}: Accuracy = {acc*100:.2f}%")
        print(f"    tension: mean={data['tension'].mean():.4f}, std={data['tension'].std():.4f}")
        print(f"    tension: min={data['tension'].min():.4f}, max={data['tension'].max():.4f}")
        print(f"    softmax_conf: mean={data['softmax_conf'].mean():.4f}")

        # ECE for softmax
        ece_sm, bins_sm = compute_ece(data['softmax_conf'], data['correct'])
        all_ece_softmax.append(ece_sm)

        # ECE for tension-based confidence
        tension_conf = tension_to_confidence(data['tension'])
        ece_t, bins_t = compute_ece(tension_conf, data['correct'])
        all_ece_tension.append(ece_t)

        print(f"    ECE(softmax)  = {ece_sm:.4f}")
        print(f"    ECE(tension)  = {ece_t:.4f}")
        print(f"    Winner: {'TENSION' if ece_t < ece_sm else 'SOFTMAX'} (lower=better)")

        if trial == n_trials - 1:  # Last trial: print diagrams
            print_reliability_diagram(bins_sm, f"{dataset_name} Softmax Calibration")
            print_reliability_diagram(bins_t, f"{dataset_name} Tension Calibration")
            ascii_calibration_plot(bins_sm, f"{dataset_name} Softmax")
            ascii_calibration_plot(bins_t, f"{dataset_name} Tension")

    # Per-class analysis
    print(f"\n  --- {dataset_name} Per-class tension statistics (last trial) ---")
    print(f"  {'Class':>5} {'N':>5} {'Acc':>6} {'T_mean':>8} {'T_std':>8} {'SM_conf':>8}")
    for c in range(10):
        mask = data['label'] == c
        if mask.sum() == 0:
            continue
        c_acc = data['correct'][mask].mean()
        c_t = data['tension'][mask].mean()
        c_t_std = data['tension'][mask].std()
        c_sm = data['softmax_conf'][mask].mean()
        print(f"  {c:>5} {mask.sum():>5} {c_acc:>5.3f} {c_t:>8.4f} {c_t_std:>8.4f} {c_sm:>8.4f}")

    # Correlation: tension vs correctness
    from scipy import stats as sp_stats
    r_sm, p_sm = sp_stats.pointbiserialr(data['correct'], data['softmax_conf'])
    r_t, p_t = sp_stats.pointbiserialr(data['correct'], data['tension'])
    print(f"\n  Correlation with correctness:")
    print(f"    softmax_conf: r={r_sm:.4f}, p={p_sm:.2e}")
    print(f"    tension:      r={r_t:.4f}, p={p_t:.2e}")

    return {
        'ece_softmax': np.mean(all_ece_softmax),
        'ece_tension': np.mean(all_ece_tension),
        'ece_softmax_std': np.std(all_ece_softmax),
        'ece_tension_std': np.std(all_ece_tension),
    }

if __name__ == '__main__':
    print("=" * 60)
    print("  H-CX-26: tension = calibrated probability")
    print("  softmax ECE vs tension ECE comparison")
    print("=" * 60)

    results = {}

    # MNIST
    train_loader, test_loader = load_mnist(batch_size=128)
    results['MNIST'] = run_experiment('MNIST', train_loader, test_loader, n_trials=3)

    # Fashion-MNIST
    train_loader, test_loader = load_fashion(batch_size=128)
    results['Fashion'] = run_experiment('Fashion-MNIST', train_loader, test_loader, n_trials=3)

    # Summary
    print(f"\n{'='*60}")
    print(f"  === FINAL SUMMARY ===")
    print(f"{'='*60}")
    print(f"  {'Dataset':>12} {'ECE(softmax)':>14} {'ECE(tension)':>14} {'Winner':>10}")
    print(f"  {'─'*12} {'─'*14} {'─'*14} {'─'*10}")
    for name, r in results.items():
        winner = 'TENSION' if r['ece_tension'] < r['ece_softmax'] else 'SOFTMAX'
        print(f"  {name:>12} {r['ece_softmax']:.4f}±{r['ece_softmax_std']:.4f} {r['ece_tension']:.4f}±{r['ece_tension_std']:.4f} {winner:>10}")

    print(f"\n  Interpretation:")
    print(f"    ECE(tension) < ECE(softmax) → Tension is better calibrated probability")
    print(f"    ECE(tension) > ECE(softmax) → softmax is better calibrated")
    print(f"    H-CX-26 confirmation condition: ECE(tension) < ECE(softmax) in 2+ datasets")