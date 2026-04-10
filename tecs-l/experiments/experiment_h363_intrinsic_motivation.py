#!/opt/homebrew/bin/python3
"""H363: Intrinsic Motivation via Tension Delta (|dT|)

Hypothesis: tension change |dT| acts as intrinsic reward signal.
- Unseen classes (5-9) produce HIGHER curiosity (|dT|) than seen classes (0-4)
- Curiosity-driven active learning outperforms random selection
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms
from model_pure_field import PureFieldEngine

torch.manual_seed(42)
np.random.seed(42)

# ── Data ──
transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
train_full = datasets.MNIST('data', train=True, download=True, transform=transform)
test_full = datasets.MNIST('data', train=False, transform=transform)

# Split: seen=0-4, unseen=5-9
seen_classes = set(range(5))
seen_train_idx = [i for i, (_, y) in enumerate(train_full) if y in seen_classes]
seen_test_idx = [i for i, (_, y) in enumerate(test_full) if y in seen_classes]
all_test_idx = list(range(len(test_full)))

seen_train = Subset(train_full, seen_train_idx)
seen_test = Subset(test_full, seen_test_idx)
train_loader = DataLoader(seen_train, batch_size=128, shuffle=True)
seen_test_loader = DataLoader(seen_test, batch_size=256, shuffle=False)
all_test_loader = DataLoader(test_full, batch_size=256, shuffle=False)

print("=" * 65)
print("  H363: Intrinsic Motivation via Tension Delta")
print("=" * 65)
print(f"  Train set: {len(seen_train)} samples (digits 0-4 only)")
print(f"  Test set:  {len(test_full)} samples (all digits 0-9)")

# ── Part 1: Train on 0-4, measure curiosity on 0-9 ──
print("\n" + "-" * 65)
print("  PART 1: Train on digits 0-4, measure curiosity on all digits")
print("-" * 65)

model = PureFieldEngine(784, 128, 10)
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

for epoch in range(15):
    model.train()
    total_loss, correct, total = 0.0, 0, 0
    for X, y in train_loader:
        X = X.view(X.size(0), -1)
        optimizer.zero_grad()
        out, tension = model(X)
        loss = criterion(out, y) + 0.1 * tension.mean()
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        correct += (out.argmax(1) == y).sum().item()
        total += y.size(0)
    if (epoch + 1) % 3 == 0 or epoch == 0:
        print(f"    Epoch {epoch+1:>2}/15: Loss={total_loss/len(train_loader):.4f}, "
              f"TrainAcc={correct/total*100:.1f}%")

# Evaluate on seen test
model.eval()
correct, total = 0, 0
with torch.no_grad():
    for X, y in seen_test_loader:
        X = X.view(X.size(0), -1)
        out, _ = model(X)
        correct += (out.argmax(1) == y).sum().item()
        total += y.size(0)
print(f"\n  Seen-class test accuracy (0-4): {correct/total*100:.1f}%")

# ── Measure per-class tension and curiosity ──
print("\n  Measuring per-class tension and curiosity (|dT|)...")

class_tensions = {c: [] for c in range(10)}
class_curiosity = {c: [] for c in range(10)}
class_pred_error = {c: [] for c in range(10)}

model.eval()
prev_tension = {}  # per-class running tension for delta

with torch.no_grad():
    for X, y in all_test_loader:
        X_flat = X.view(X.size(0), -1)
        out, tension = model(X_flat)
        probs = F.softmax(out, dim=-1)
        pred_err = 1.0 - probs.max(dim=-1).values  # prediction uncertainty

        for i in range(len(y)):
            c = y[i].item()
            t = tension[i].item()
            class_tensions[c].append(t)
            class_pred_error[c].append(pred_err[i].item())

# Compute curiosity = |dT| as std of tension within class (proxy for tension variability)
# Also compute: mean tension difference from class baseline
# Better: curiosity = |T_sample - T_class_mean_seen| averaged
seen_mean_tension = np.mean([np.mean(class_tensions[c]) for c in range(5)])

for c in range(10):
    ts = np.array(class_tensions[c])
    # Curiosity = |mean_tension_class - seen_baseline| + std(tension)
    class_curiosity[c] = abs(np.mean(ts) - seen_mean_tension) + np.std(ts)

# Print table
print("\n  Per-class Tension & Curiosity Table:")
print("  " + "-" * 61)
print(f"  {'Class':>5} | {'Type':>6} | {'Tension':>10} | {'Curiosity':>10} | {'PredErr':>10}")
print("  " + "-" * 61)
seen_curiosities = []
unseen_curiosities = []
for c in range(10):
    t_mean = np.mean(class_tensions[c])
    t_std = np.std(class_tensions[c])
    cur = class_curiosity[c]
    pe = np.mean(class_pred_error[c])
    ctype = "SEEN" if c < 5 else "UNSEEN"
    print(f"  {c:>5} | {ctype:>6} | {t_mean:>10.4f} | {cur:>10.4f} | {pe:>10.4f}")
    if c < 5:
        seen_curiosities.append(cur)
    else:
        unseen_curiosities.append(cur)

print("  " + "-" * 61)
mean_seen_cur = np.mean(seen_curiosities)
mean_unseen_cur = np.mean(unseen_curiosities)
print(f"  {'SEEN avg':>14} | {np.mean([np.mean(class_tensions[c]) for c in range(5)]):>10.4f} "
      f"| {mean_seen_cur:>10.4f} | {np.mean([np.mean(class_pred_error[c]) for c in range(5)]):>10.4f}")
print(f"  {'UNSEEN avg':>14} | {np.mean([np.mean(class_tensions[c]) for c in range(5,10)]):>10.4f} "
      f"| {mean_unseen_cur:>10.4f} | {np.mean([np.mean(class_pred_error[c]) for c in range(5,10)]):>10.4f}")
ratio = mean_unseen_cur / (mean_seen_cur + 1e-8)
print(f"\n  Curiosity ratio (unseen/seen): {ratio:.2f}x")
print(f"  Hypothesis (unseen > seen):    {'CONFIRMED' if ratio > 1.0 else 'REJECTED'}")

# ASCII bar chart
print("\n  Per-class Curiosity Bar Chart:")
max_cur = max(class_curiosity.values())
for c in range(10):
    bar_len = int(40 * class_curiosity[c] / (max_cur + 1e-8))
    label = "S" if c < 5 else "U"
    print(f"    {c} [{label}] |{'#' * bar_len:<40}| {class_curiosity[c]:.4f}")

# ── Part 2: Active Learning Comparison ──
print("\n" + "-" * 65)
print("  PART 2: Active Learning — Curiosity vs Random Selection")
print("-" * 65)

# Pool: all training data (0-9)
all_train_idx = list(range(len(train_full)))
budget_per_round = 200
n_rounds = 15
n_trials = 3

def train_model_on_indices(indices, epochs=5):
    """Train a fresh model on given indices, return test accuracy on all 10 classes."""
    m = PureFieldEngine(784, 128, 10)
    opt = torch.optim.Adam(m.parameters(), lr=0.001)
    crit = nn.CrossEntropyLoss()
    loader = DataLoader(Subset(train_full, indices), batch_size=64, shuffle=True)
    for _ in range(epochs):
        m.train()
        for X, y in loader:
            X = X.view(X.size(0), -1)
            opt.zero_grad()
            out, tension = m(X)
            loss = crit(out, y) + 0.1 * tension.mean()
            loss.backward()
            opt.step()
    m.eval()
    correct = total = 0
    with torch.no_grad():
        for X, y in all_test_loader:
            X = X.view(X.size(0), -1)
            out, _ = m(X)
            correct += (out.argmax(1) == y).sum().item()
            total += y.size(0)
    return m, correct / total

def get_curiosity_scores(m, pool_indices):
    """Compute |dT| curiosity for each sample in pool."""
    m.eval()
    scores = []
    loader = DataLoader(Subset(train_full, pool_indices), batch_size=256, shuffle=False)
    with torch.no_grad():
        for X, _ in loader:
            X = X.view(X.size(0), -1)
            _, tension = m(X)
            scores.extend(tension.cpu().numpy().tolist())
    return np.array(scores)

random_curves = []
curiosity_curves = []

for trial in range(n_trials):
    print(f"\n  Trial {trial+1}/{n_trials}...")
    seed_offset = trial * 1000
    rng = np.random.RandomState(42 + trial)

    # Initial seed: 200 random samples
    pool = list(range(len(train_full)))
    rng.shuffle(pool)
    seed_idx = pool[:budget_per_round]
    pool_random = pool[budget_per_round:]
    pool_curiosity = list(pool_random)
    selected_random = list(seed_idx)
    selected_curiosity = list(seed_idx)

    rand_accs = []
    cur_accs = []

    for rnd in range(n_rounds):
        # Train both
        _, acc_r = train_model_on_indices(selected_random, epochs=5)
        m_c, acc_c = train_model_on_indices(selected_curiosity, epochs=5)
        rand_accs.append(acc_r)
        cur_accs.append(acc_c)

        # Select next batch
        # Random
        if len(pool_random) >= budget_per_round:
            new_random = pool_random[:budget_per_round]
            pool_random = pool_random[budget_per_round:]
        else:
            new_random = pool_random
            pool_random = []
        selected_random.extend(new_random)

        # Curiosity-driven
        if len(pool_curiosity) >= budget_per_round:
            scores = get_curiosity_scores(m_c, pool_curiosity)
            top_idx = np.argsort(-scores)[:budget_per_round]
            new_curiosity = [pool_curiosity[i] for i in top_idx]
            pool_curiosity = [pool_curiosity[i] for i in range(len(pool_curiosity))
                              if i not in set(top_idx)]
        else:
            new_curiosity = pool_curiosity
            pool_curiosity = []
        selected_curiosity.extend(new_curiosity)

        n_samples = len(selected_random)
        if (rnd + 1) % 3 == 0 or rnd == 0:
            print(f"    Round {rnd+1:>2}: samples={n_samples:>5}, "
                  f"Random={acc_r*100:.1f}%, Curiosity={acc_c*100:.1f}%, "
                  f"delta={((acc_c-acc_r)*100):+.1f}%")

    random_curves.append(rand_accs)
    curiosity_curves.append(cur_accs)

# Average curves
rand_avg = np.mean(random_curves, axis=0)
cur_avg = np.mean(curiosity_curves, axis=0)
rand_std = np.std(random_curves, axis=0)
cur_std = np.std(curiosity_curves, axis=0)

# Full table
print("\n  Active Learning Results (averaged over 3 trials):")
print("  " + "-" * 65)
print(f"  {'Round':>5} | {'Samples':>7} | {'Random':>10} | {'Curiosity':>10} | {'Delta':>8}")
print("  " + "-" * 65)
for rnd in range(n_rounds):
    n_s = (rnd + 1) * budget_per_round + budget_per_round
    print(f"  {rnd+1:>5} | {n_s:>7} | {rand_avg[rnd]*100:>9.1f}% | "
          f"{cur_avg[rnd]*100:>9.1f}% | {(cur_avg[rnd]-rand_avg[rnd])*100:>+7.1f}%")
print("  " + "-" * 65)

final_delta = (cur_avg[-1] - rand_avg[-1]) * 100
print(f"\n  Final accuracy: Random={rand_avg[-1]*100:.1f}%, Curiosity={cur_avg[-1]*100:.1f}%")
print(f"  Improvement:    {final_delta:+.1f}%")

# ASCII learning curve
print("\n  Learning Curve (R=Random, C=Curiosity):")
max_acc = max(max(rand_avg), max(cur_avg))
min_acc = min(min(rand_avg), min(cur_avg))
height = 15
for row in range(height, -1, -1):
    acc_val = min_acc + (max_acc - min_acc) * row / height
    line = f"  {acc_val*100:>5.1f}% |"
    for rnd in range(n_rounds):
        r_row = int((rand_avg[rnd] - min_acc) / (max_acc - min_acc + 1e-8) * height)
        c_row = int((cur_avg[rnd] - min_acc) / (max_acc - min_acc + 1e-8) * height)
        if r_row == row and c_row == row:
            line += " X"
        elif r_row == row:
            line += " R"
        elif c_row == row:
            line += " C"
        else:
            line += " ."
    print(line)
print(f"         +{'--' * n_rounds}")
print(f"          {''.join(f'{i+1:>2}' for i in range(n_rounds))}  (round)")

# ── Summary ──
print("\n" + "=" * 65)
print("  H363 SUMMARY")
print("=" * 65)
print(f"  1. Curiosity ratio (unseen/seen): {ratio:.2f}x")
print(f"     -> Unseen classes {'DO' if ratio > 1.0 else 'do NOT'} trigger higher curiosity")
print(f"  2. Active learning improvement:   {final_delta:+.1f}%")
print(f"     -> Curiosity-driven selection {'IS' if final_delta > 0 else 'is NOT'} better than random")
print(f"  3. Hypothesis H363:               {'SUPPORTED' if ratio > 1.0 and final_delta > 0 else 'PARTIALLY SUPPORTED' if ratio > 1.0 or final_delta > 0 else 'REJECTED'}")
print("=" * 65)
