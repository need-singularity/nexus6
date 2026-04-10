#!/usr/bin/env python3
"""H310 MitosisEngine - Automatic Mitosis During Training

Algorithm:
  1. Train parent on MNIST for 5 epochs
  2. Check trigger: if accuracy improvement < 0.1% for 2 consecutive epochs -> mitosis!
  3. Mitosis: split into 2 children (scale=0.01)
  4. Train children independently for 5 epochs
  5. Reunion: ensemble = average outputs -> becomes new parent
  6. Repeat from step 1 (max 3 mitosis cycles, total ~30 epochs)

Comparison:
  A) MitosisEngine (auto-mitosis + reunion)
  B) Normal training (30 epochs, no mitosis)
  C) Manual mitosis at fixed points (epoch 10, 20)

Self-contained. 3 trials each. Report final accuracy + ASCII learning curves.
"""

import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import copy
from torchvision import datasets, transforms


# ---------------------------------------------------------------------------
# Model: 2-engine classifier with equilibrium
# ---------------------------------------------------------------------------

class DualEngineClassifier(nn.Module):
    """Simple 2-engine model: engine_a + engine_g + equilibrium average."""
    def __init__(self, input_dim=784, hidden_dim=64, output_dim=10):
        super().__init__()
        self.engine_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )
        self.engine_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        a = self.engine_a(x)
        g = self.engine_g(x)
        return (a + g) / 2.0


# ---------------------------------------------------------------------------
# Data: preload as tensors for speed
# ---------------------------------------------------------------------------

def load_data():
    transform = transforms.Compose([transforms.ToTensor()])
    train_ds = datasets.MNIST(root='/tmp/mnist', train=True, download=True, transform=transform)
    test_ds = datasets.MNIST(root='/tmp/mnist', train=False, download=True, transform=transform)

    X_train = train_ds.data[:10000].float().view(-1, 784) / 255.0
    y_train = train_ds.targets[:10000]
    X_test = test_ds.data.float().view(-1, 784) / 255.0
    y_test = test_ds.targets

    return X_train, y_train, X_test, y_test


# ---------------------------------------------------------------------------
# Train/Eval on raw tensors
# ---------------------------------------------------------------------------

BATCH_SIZE = 512

def train_one_epoch(model, X, y, optimizer):
    model.train()
    criterion = nn.CrossEntropyLoss()
    perm = torch.randperm(len(X))
    total_loss = 0.0
    n = 0
    for i in range(0, len(X), BATCH_SIZE):
        idx = perm[i:i+BATCH_SIZE]
        optimizer.zero_grad()
        out = model(X[idx])
        loss = criterion(out, y[idx])
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        n += 1
    return total_loss / n


def evaluate(model, X, y):
    model.eval()
    correct = 0
    with torch.no_grad():
        for i in range(0, len(X), 2048):
            out = model(X[i:i+2048])
            correct += (out.argmax(1) == y[i:i+2048]).sum().item()
    return correct / len(y) * 100.0


def evaluate_ensemble(model_a, model_b, X, y):
    model_a.eval()
    model_b.eval()
    correct = 0
    with torch.no_grad():
        for i in range(0, len(X), 2048):
            batch = X[i:i+2048]
            out = (model_a(batch) + model_b(batch)) / 2.0
            correct += (out.argmax(1) == y[i:i+2048]).sum().item()
    return correct / len(y) * 100.0


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def mitosis(parent, scale=0.01):
    child_a = copy.deepcopy(parent)
    child_b = copy.deepcopy(parent)
    with torch.no_grad():
        for pa, pb in zip(child_a.parameters(), child_b.parameters()):
            noise = torch.randn_like(pa) * scale
            pa.add_(noise)
            pb.add_(-noise)
    return child_a, child_b


def reunion(child_a, child_b):
    parent = copy.deepcopy(child_a)
    with torch.no_grad():
        for pp, pa, pb in zip(parent.parameters(), child_a.parameters(), child_b.parameters()):
            pp.copy_((pa + pb) / 2.0)
    return parent


# ---------------------------------------------------------------------------
# Method A: MitosisEngine (auto-mitosis + reunion)
# ---------------------------------------------------------------------------

def run_mitosis_engine(X_train, y_train, X_test, y_test, seed,
                       max_cycles=3, child_epochs=5, scale=0.01,
                       stall_threshold=0.1, stall_patience=2, max_total_epochs=30):
    torch.manual_seed(seed)
    np.random.seed(seed)

    model = DualEngineClassifier()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    acc_curve = []
    epoch_counter = 0
    mitosis_count = 0
    stall_count = 0
    prev_acc = 0.0

    print(f"    [MitosisEngine] max_cycles={max_cycles}, stall_thresh={stall_threshold}%, patience={stall_patience}")

    while epoch_counter < max_total_epochs:
        # Train parent one epoch
        train_one_epoch(model, X_train, y_train, optimizer)
        epoch_counter += 1
        acc = evaluate(model, X_test, y_test)
        acc_curve.append(acc)

        # Stall detection
        improvement = acc - prev_acc
        if improvement < stall_threshold and epoch_counter > 1:
            stall_count += 1
        else:
            stall_count = 0
        prev_acc = acc

        if epoch_counter % 5 == 0 or epoch_counter == 1:
            print(f"      epoch {epoch_counter:>2}: acc={acc:.2f}% stall={stall_count}/{stall_patience}")

        # Trigger mitosis?
        if stall_count >= stall_patience and mitosis_count < max_cycles:
            print(f"      >>> MITOSIS #{mitosis_count+1} at epoch {epoch_counter} (acc={acc:.2f}%)")
            mitosis_count += 1

            child_a, child_b = mitosis(model, scale=scale)
            opt_a = torch.optim.Adam(child_a.parameters(), lr=1e-3)
            opt_b = torch.optim.Adam(child_b.parameters(), lr=1e-3)

            for ce in range(child_epochs):
                if epoch_counter >= max_total_epochs:
                    break
                train_one_epoch(child_a, X_train, y_train, opt_a)
                train_one_epoch(child_b, X_train, y_train, opt_b)
                epoch_counter += 1
                ens_acc = evaluate_ensemble(child_a, child_b, X_test, y_test)
                acc_curve.append(ens_acc)

                if ce == 0 or ce == child_epochs - 1:
                    print(f"      child ep {ce+1}/{child_epochs}: ensemble={ens_acc:.2f}%")

            # Reunion
            model = reunion(child_a, child_b)
            optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
            reunion_acc = evaluate(model, X_test, y_test)
            prev_acc = reunion_acc
            stall_count = 0
            print(f"      >>> REUNION #{mitosis_count}: acc={reunion_acc:.2f}%")

    final_acc = acc_curve[-1] if acc_curve else 0.0
    print(f"    [MitosisEngine] final={final_acc:.2f}%, mitosis_count={mitosis_count}, epochs={epoch_counter}")
    return final_acc, acc_curve


# ---------------------------------------------------------------------------
# Method B: Normal training (no mitosis)
# ---------------------------------------------------------------------------

def run_normal(X_train, y_train, X_test, y_test, seed, total_epochs=30):
    torch.manual_seed(seed)
    np.random.seed(seed)

    model = DualEngineClassifier()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    acc_curve = []
    for ep in range(total_epochs):
        train_one_epoch(model, X_train, y_train, optimizer)
        acc = evaluate(model, X_test, y_test)
        acc_curve.append(acc)
        if (ep + 1) % 5 == 0 or ep == 0:
            print(f"      epoch {ep+1:>2}: acc={acc:.2f}%")

    final_acc = acc_curve[-1]
    print(f"    [Normal] final={final_acc:.2f}%")
    return final_acc, acc_curve


# ---------------------------------------------------------------------------
# Method C: Manual mitosis at fixed points
# ---------------------------------------------------------------------------

def run_manual_mitosis(X_train, y_train, X_test, y_test, seed,
                       total_epochs=30, mitosis_points=(10, 20),
                       child_epochs=5, scale=0.01):
    torch.manual_seed(seed)
    np.random.seed(seed)

    model = DualEngineClassifier()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    acc_curve = []
    epoch_counter = 0
    mitosis_done = 0

    while epoch_counter < total_epochs:
        if mitosis_done < len(mitosis_points) and epoch_counter == mitosis_points[mitosis_done]:
            print(f"      >>> MANUAL MITOSIS at epoch {epoch_counter}")
            child_a, child_b = mitosis(model, scale=scale)
            opt_a = torch.optim.Adam(child_a.parameters(), lr=1e-3)
            opt_b = torch.optim.Adam(child_b.parameters(), lr=1e-3)

            for ce in range(child_epochs):
                if epoch_counter >= total_epochs:
                    break
                train_one_epoch(child_a, X_train, y_train, opt_a)
                train_one_epoch(child_b, X_train, y_train, opt_b)
                epoch_counter += 1
                ens_acc = evaluate_ensemble(child_a, child_b, X_test, y_test)
                acc_curve.append(ens_acc)

            model = reunion(child_a, child_b)
            optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
            reunion_acc = evaluate(model, X_test, y_test)
            print(f"      >>> REUNION: acc={reunion_acc:.2f}%")
            mitosis_done += 1
        else:
            train_one_epoch(model, X_train, y_train, optimizer)
            epoch_counter += 1
            acc = evaluate(model, X_test, y_test)
            acc_curve.append(acc)
            if epoch_counter % 5 == 0 or epoch_counter == 1:
                print(f"      epoch {epoch_counter:>2}: acc={acc:.2f}%")

    final_acc = acc_curve[-1] if acc_curve else 0.0
    print(f"    [ManualMitosis] final={final_acc:.2f}%, mitosis={mitosis_done}, epochs={epoch_counter}")
    return final_acc, acc_curve


# ---------------------------------------------------------------------------
# ASCII learning curve
# ---------------------------------------------------------------------------

def ascii_learning_curves(curves_dict, height=18, width=55):
    print(f"\n  {'='*70}")
    print(f"  ASCII LEARNING CURVES (accuracy %)")
    print(f"  {'='*70}")

    all_vals = []
    for vals in curves_dict.values():
        all_vals.extend(vals)
    ymin = min(all_vals) - 1
    ymax = max(all_vals) + 1
    if ymax - ymin < 5:
        ymax = ymin + 5

    max_len = max(len(v) for v in curves_dict.values())
    symbols = ['#', 'o', '+']
    labels = list(curves_dict.keys())

    grid = [[' ' for _ in range(width)] for _ in range(height)]

    for mi, (name, vals) in enumerate(curves_dict.items()):
        sym = symbols[mi % len(symbols)]
        for i, v in enumerate(vals):
            col = int(i / max(max_len - 1, 1) * (width - 1))
            row = int((v - ymin) / (ymax - ymin) * (height - 1))
            row = height - 1 - row
            row = max(0, min(height - 1, row))
            col = max(0, min(width - 1, col))
            if grid[row][col] == ' ':
                grid[row][col] = sym
            elif grid[row][col] != sym:
                grid[row][col] = '*'  # overlap

    for ri in range(height):
        yval = ymax - ri * (ymax - ymin) / (height - 1)
        line = ''.join(grid[ri])
        print(f"  {yval:>6.1f} |{line}|")
    print(f"  {'':>6} +{'-'*width}+")
    print(f"  {'':>6}  epoch 1{' '*(width-12)}epoch {max_len}")

    print(f"\n  Legend:")
    for mi, name in enumerate(labels):
        sym = symbols[mi % len(symbols)]
        print(f"    {sym} = {name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 72)
    print("  H310: MitosisEngine - Automatic Mitosis During Training")
    print("=" * 72)
    print()
    print("  Algorithm:")
    print("    1. Train parent on MNIST")
    print("    2. Detect stall (acc improvement < 0.1% for 2 epochs)")
    print("    3. Mitosis: split into 2 children (scale=0.01)")
    print("    4. Train children independently for 5 epochs")
    print("    5. Reunion: average parameters -> new parent")
    print("    6. Repeat (max 3 cycles, ~30 epochs total)")
    print()
    print("  Comparison:")
    print("    A) MitosisEngine (auto-mitosis + reunion)")
    print("    B) Normal training (30 epochs)")
    print("    C) Manual mitosis at fixed points (epoch 10, 20)")
    print()

    print("[1] Loading MNIST (10k train subset, full test)...")
    X_train, y_train, X_test, y_test = load_data()
    print(f"    Train: {len(X_train)}, Test: {len(X_test)}")

    N_TRIALS = 3
    TOTAL_EPOCHS = 30

    results_a, results_b, results_c = [], [], []
    curves_a, curves_b, curves_c = [], [], []

    for trial in range(N_TRIALS):
        seed = trial * 1000 + 42
        print(f"\n{'_'*72}")
        print(f"  Trial {trial+1}/{N_TRIALS} (seed={seed})")
        print(f"{'_'*72}")

        print(f"\n  [A] MitosisEngine:")
        acc_a, curve_a = run_mitosis_engine(
            X_train, y_train, X_test, y_test, seed,
            max_cycles=3, child_epochs=5, scale=0.01,
            stall_threshold=0.1, stall_patience=2, max_total_epochs=TOTAL_EPOCHS
        )
        results_a.append(acc_a)
        curves_a.append(curve_a)

        print(f"\n  [B] Normal Training:")
        acc_b, curve_b = run_normal(
            X_train, y_train, X_test, y_test, seed,
            total_epochs=TOTAL_EPOCHS
        )
        results_b.append(acc_b)
        curves_b.append(curve_b)

        print(f"\n  [C] Manual Mitosis (at epoch 10, 20):")
        acc_c, curve_c = run_manual_mitosis(
            X_train, y_train, X_test, y_test, seed,
            total_epochs=TOTAL_EPOCHS, mitosis_points=(10, 20),
            child_epochs=5, scale=0.01
        )
        results_c.append(acc_c)
        curves_c.append(curve_c)

    # =========================================================================
    # Results
    # =========================================================================
    print("\n" + "=" * 72)
    print("  RESULTS SUMMARY")
    print("=" * 72)

    print(f"\n  Per-Trial Final Accuracy (%):")
    print(f"  {'Trial':>6} | {'MitosisEngine':>14} | {'Normal':>10} | {'ManualMitosis':>14}")
    print(f"  {'-'*6}-+-{'-'*14}-+-{'-'*10}-+-{'-'*14}")
    for t in range(N_TRIALS):
        print(f"  {t+1:>6} | {results_a[t]:>14.2f} | {results_b[t]:>10.2f} | {results_c[t]:>14.2f}")

    mean_a, std_a = np.mean(results_a), np.std(results_a)
    mean_b, std_b = np.mean(results_b), np.std(results_b)
    mean_c, std_c = np.mean(results_c), np.std(results_c)

    print(f"  {'-'*6}-+-{'-'*14}-+-{'-'*10}-+-{'-'*14}")
    print(f"  {'Mean':>6} | {mean_a:>10.2f}+/-{std_a:<3.2f} | {mean_b:>6.2f}+/-{std_b:<3.2f} | {mean_c:>10.2f}+/-{std_c:<3.2f}")

    diff_a = mean_a - mean_b
    diff_c = mean_c - mean_b
    print(f"\n  vs Normal baseline:")
    print(f"    MitosisEngine:  {'+' if diff_a >= 0 else ''}{diff_a:.2f}%")
    print(f"    ManualMitosis:  {'+' if diff_c >= 0 else ''}{diff_c:.2f}%")

    best_name = "MitosisEngine"
    best_val = mean_a
    if mean_b > best_val:
        best_name, best_val = "Normal", mean_b
    if mean_c > best_val:
        best_name, best_val = "ManualMitosis", mean_c
    print(f"\n  Best method: {best_name} ({best_val:.2f}%)")

    # =========================================================================
    # Accuracy comparison bar chart
    # =========================================================================
    print(f"\n  {'='*70}")
    print(f"  ACCURACY COMPARISON TABLE")
    print(f"  {'='*70}")

    methods = [
        ("A) MitosisEngine (auto)", mean_a, std_a),
        ("B) Normal (30 epochs)", mean_b, std_b),
        ("C) Manual (epoch 10,20)", mean_c, std_c),
    ]

    bar_max = max(mean_a, mean_b, mean_c)
    bar_min = min(mean_a, mean_b, mean_c) - 2

    print(f"\n  {'Method':<30} {'Accuracy':>12}  Bar")
    print(f"  {'-'*30} {'-'*12}  {'-'*40}")
    for name, m, s in methods:
        bar_len = int((m - bar_min) / (bar_max - bar_min + 0.01) * 40)
        bar = '#' * max(bar_len, 1)
        marker = " <-- BEST" if m == best_val else ""
        print(f"  {name:<30} {m:>6.2f}+/-{s:<4.2f}  |{bar:<40}|{marker}")

    # =========================================================================
    # ASCII learning curves
    # =========================================================================
    def avg_curves(curves_list):
        max_len = max(len(c) for c in curves_list)
        padded = []
        for c in curves_list:
            p = list(c) + [c[-1]] * (max_len - len(c))
            padded.append(p)
        return [np.mean([p[i] for p in padded]) for i in range(max_len)]

    avg_a = avg_curves(curves_a)
    avg_b = avg_curves(curves_b)
    avg_c = avg_curves(curves_c)

    ascii_learning_curves({
        "MitosisEngine (auto)": avg_a,
        "Normal (30 epochs)": avg_b,
        "ManualMitosis (10,20)": avg_c,
    })

    # =========================================================================
    # Epoch-by-epoch table
    # =========================================================================
    print(f"\n  {'='*70}")
    print(f"  EPOCH-BY-EPOCH ACCURACY (averaged over {N_TRIALS} trials)")
    print(f"  {'='*70}")

    max_len = max(len(avg_a), len(avg_b), len(avg_c))
    print(f"\n  {'Epoch':>6} | {'MitosisEng':>11} | {'Normal':>8} | {'ManualMit':>10}")
    print(f"  {'-'*6}-+-{'-'*11}-+-{'-'*8}-+-{'-'*10}")

    for ep in range(max_len):
        va = f"{avg_a[ep]:.2f}" if ep < len(avg_a) else "---"
        vb = f"{avg_b[ep]:.2f}" if ep < len(avg_b) else "---"
        vc = f"{avg_c[ep]:.2f}" if ep < len(avg_c) else "---"
        if (ep + 1) % 5 == 0 or ep == 0 or ep == max_len - 1:
            print(f"  {ep+1:>6} | {va:>11} | {vb:>8} | {vc:>10}")

    # =========================================================================
    # Verdict
    # =========================================================================
    print(f"\n  {'='*70}")
    print(f"  VERDICT")
    print(f"  {'='*70}")

    print(f"""
  MitosisEngine (auto-mitosis + reunion):
    Mean accuracy: {mean_a:.2f}% +/- {std_a:.2f}%
    vs Normal:     {'+' if diff_a >= 0 else ''}{diff_a:.2f}%

  Normal training (30 epochs):
    Mean accuracy: {mean_b:.2f}% +/- {std_b:.2f}%

  Manual mitosis (epoch 10, 20):
    Mean accuracy: {mean_c:.2f}% +/- {std_c:.2f}%
    vs Normal:     {'+' if diff_c >= 0 else ''}{diff_c:.2f}%

  Winner: {best_name} ({best_val:.2f}%)
""")

    if diff_a > 0.5:
        print("  CONCLUSION: MitosisEngine IMPROVES over normal training.")
        print("  Auto-mitosis at stall points provides meaningful accuracy gains.")
    elif diff_a > -0.5:
        print("  CONCLUSION: MitosisEngine COMPARABLE to normal training.")
        print("  Auto-mitosis neither helps nor hurts significantly.")
    else:
        print("  CONCLUSION: MitosisEngine WORSE than normal training.")
        print("  The mitosis-reunion cycle disrupts learning in this configuration.")

    if diff_a > diff_c + 0.1:
        print("  Auto-mitosis BETTER than manual -> stall detection is valuable.")
    elif diff_c > diff_a + 0.1:
        print("  Manual mitosis BETTER than auto -> fixed schedule outperforms stall detection.")
    else:
        print("  Auto and manual mitosis roughly equivalent.")

    print(f"\n  {'='*70}")
    print(f"  EXPERIMENT COMPLETE")
    print(f"  {'='*70}")


if __name__ == "__main__":
    main()
