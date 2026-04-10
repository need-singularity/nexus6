#!/usr/bin/env python3
"""H359 Verification: Savant = Inhibition Release at Golden Zone Lower Bound

Inducing savant characteristics through dropout asymmetry after mitosis:
- child_savant: dropout=0.21 (Golden Zone lower bound), learns only digits 0-4
- child_normal: dropout=0.37 (Golden Zone center), learns all
- Savant Index = max(class_tension) / min(class_tension)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import copy
import math
from model_pure_field import PureFieldEngine
from model_utils import load_mnist
from torch.utils.data import DataLoader, Subset

GOLDEN_LOWER = 0.5 - math.log(4/3)  # 0.2123
GOLDEN_CENTER = 1/math.e              # 0.3679

def set_dropout(model, p):
    """Change p for all Dropout layers."""
    for m in model.modules():
        if isinstance(m, nn.Dropout):
            m.p = p

def filter_dataset(dataset, classes):
    """Create Subset containing only specific classes."""
    indices = [i for i, (_, y) in enumerate(dataset) if y in classes]
    return Subset(dataset, indices)

def train_model(model, loader, epochs=15, lr=0.001):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    for ep in range(epochs):
        model.train()
        for X, y in loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            logits, _ = model(X)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
    return model

def measure_per_class_tension(model, test_loader):
    """Measure average tension per class."""
    class_tensions = {i: [] for i in range(10)}
    class_correct = {i: 0 for i in range(10)}
    class_total = {i: 0 for i in range(10)}

    model.eval()
    with torch.no_grad():
        for X, y in test_loader:
            X = X.view(X.size(0), -1)
            logits, tension = model(X)
            pred = logits.argmax(1)
            for i in range(len(y)):
                c = y[i].item()
                class_tensions[c].append(tension[i].item())
                class_total[c] += 1
                if pred[i].item() == c:
                    class_correct[c] += 1

    results = {}
    for c in range(10):
        if class_tensions[c]:
            results[c] = {
                'mean_tension': np.mean(class_tensions[c]),
                'std_tension': np.std(class_tensions[c]),
                'accuracy': class_correct[c] / max(class_total[c], 1),
                'n': class_total[c],
            }
    return results

def compute_savant_index(results):
    tensions = [r['mean_tension'] for r in results.values()]
    if min(tensions) < 1e-8:
        return float('inf')
    return max(tensions) / min(tensions)

if __name__ == '__main__':
    print("=" * 65)
    print(f"  H359: Savant = Inhibition Release at Golden Zone Lower Bound")
    print(f"  I_min = {GOLDEN_LOWER:.4f}, I_center = {GOLDEN_CENTER:.4f}")
    print(f"  Predicted amplification ratio = {GOLDEN_CENTER/GOLDEN_LOWER:.4f} ≈ √3 = {math.sqrt(3):.4f}")
    print("=" * 65)

    # Data preparation
    train_loader, test_loader = load_mnist(batch_size=128)
    train_ds = train_loader.dataset

    # Domain separation
    domain_a = set(range(5))   # digits 0-4
    domain_b = set(range(5, 10))  # digits 5-9

    train_a = filter_dataset(train_ds, domain_a)
    loader_a = DataLoader(train_a, batch_size=128, shuffle=True)

    # Dropout sweep: 0.1, 0.21(Golden lower), 0.30, 0.37(Golden center), 0.50
    dropouts = [0.10, GOLDEN_LOWER, 0.30, GOLDEN_CENTER, 0.50]

    print(f"\n  Phase 1: Parent training (full MNIST, dropout=0.3, 15ep)")
    parent = PureFieldEngine(784, 128, 10)
    parent = train_model(parent, train_loader, epochs=15)

    parent_results = measure_per_class_tension(parent, test_loader)
    parent_si = compute_savant_index(parent_results)
    print(f"  Parent SI = {parent_si:.2f}")

    print(f"\n  Phase 2: Dropout sweep — training only domain 0-4, 20ep")
    print(f"  {'dropout':>8} {'SI':>8} {'Acc(0-4)':>10} {'Acc(5-9)':>10} {'T(0-4)':>10} {'T(5-9)':>10}")
    print(f"  {'─'*8} {'─'*8} {'─'*10} {'─'*10} {'─'*10} {'─'*10}")

    all_results = {}
    for dp in dropouts:
        child = copy.deepcopy(parent)
        set_dropout(child, dp)
        child = train_model(child, loader_a, epochs=20, lr=0.001)

        results = measure_per_class_tension(child, test_loader)
        si = compute_savant_index(results)

        acc_a = np.mean([results[c]['accuracy'] for c in range(5)])
        acc_b = np.mean([results[c]['accuracy'] for c in range(5, 10)])
        t_a = np.mean([results[c]['mean_tension'] for c in range(5)])
        t_b = np.mean([results[c]['mean_tension'] for c in range(5, 10)])

        marker = " ← Golden lower" if abs(dp - GOLDEN_LOWER) < 0.01 else \
                 " ← Golden center" if abs(dp - GOLDEN_CENTER) < 0.01 else ""

        print(f"  {dp:>8.4f} {si:>8.2f} {acc_a*100:>9.1f}% {acc_b*100:>9.1f}% {t_a:>10.1f} {t_b:>10.1f}{marker}")
        all_results[dp] = {'si': si, 'acc_a': acc_a, 'acc_b': acc_b, 't_a': t_a, 't_b': t_b, 'details': results}

    # Per-class detail for golden lower
    gl_results = all_results[GOLDEN_LOWER]['details']
    print(f"\n  === dropout={GOLDEN_LOWER:.4f} (Golden Zone lower bound) Per-class ===")
    print(f"  {'Digit':>5} {'Tension':>10} {'Acc':>8} {'Bar'}")
    print(f"  {'─'*5} {'─'*10} {'─'*8} {'─'*30}")
    max_t = max(r['mean_tension'] for r in gl_results.values())
    for c in range(10):
        r = gl_results[c]
        bar_len = int(r['mean_tension'] / max_t * 30)
        domain = "★" if c < 5 else " "
        print(f"  {c:>5} {r['mean_tension']:>10.1f} {r['accuracy']*100:>7.1f}% {domain}{'█' * bar_len}")

    # SI comparison
    print(f"\n  === Savant Index Comparison ===")
    print(f"  Parent (full training, dp=0.3):  SI = {parent_si:.2f}")
    for dp in dropouts:
        r = all_results[dp]
        marker = " ← Golden lower" if abs(dp - GOLDEN_LOWER) < 0.01 else \
                 " ← Golden center" if abs(dp - GOLDEN_CENTER) < 0.01 else ""
        bar = "█" * int(r['si'])
        print(f"  child (dp={dp:.4f}): SI = {r['si']:>6.2f} {bar}{marker}")

    # √3 verification
    si_lower = all_results[GOLDEN_LOWER]['si']
    si_center = all_results[GOLDEN_CENTER]['si']
    if si_center > 0.01:
        ratio = si_lower / si_center
        print(f"\n  SI(lower)/SI(center) = {si_lower:.2f}/{si_center:.2f} = {ratio:.4f}")
        print(f"  √3 = {math.sqrt(3):.4f}")
        print(f"  Error = {abs(ratio - math.sqrt(3))/math.sqrt(3)*100:.1f}%")

    print(f"\n  Conclusion:")
    if si_lower > 3:
        print(f"  ✅ dropout={GOLDEN_LOWER:.4f} has SI={si_lower:.1f} > 3 → Savant confirmed!")
    else:
        print(f"  ❌ SI={si_lower:.1f} < 3 → Savant not achieved (needs longer training?)")