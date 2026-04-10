#!/usr/bin/env python3
"""H-CX-27 Verification: tension_scale = ln(4) convergence — Multiple datasets + initial values + long-term training

Previous results:
  - MNIST: 1.3887 (ln(4) error 0.2%)
  - Fashion: 1.4415 (4.0%)
  - CIFAR: 1.3393 (3.4%)
  - Only converges to ln(4) with init=0.3, converges elsewhere with small/large init

Additional verification:
  1. MNIST with various init (0.01~5.0), 50 epochs (long-term training)
  2. Long-term training on Fashion/CIFAR as well
  3. Confirm existence of convergence point independent of init
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

np.random.seed(42)
torch.manual_seed(42)

LN4 = math.log(4)  # 1.38629...

print("=" * 70)
print(f"H-CX-27 Verification: tension_scale → ln(4) = {LN4:.5f}")
print("=" * 70)

# ─────────────────────────────────────────
# PureFieldEngine (inline)
# ─────────────────────────────────────────

class PureFieldEngine(nn.Module):
    def __init__(self, input_dim=784, hidden_dim=128, output_dim=10, init_ts=1.0):
        super().__init__()
        self.engine_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.engine_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.tension_scale = nn.Parameter(torch.tensor(float(init_ts)))

    def forward(self, x):
        out_a = self.engine_a(x)
        out_g = self.engine_g(x)
        repulsion = out_a - out_g
        tension = (repulsion ** 2).mean(dim=-1, keepdim=True)
        direction = F.normalize(repulsion, dim=-1)
        output = self.tension_scale * torch.sqrt(tension + 1e-8) * direction
        return output, tension.squeeze(-1)


# ─────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────

from torchvision import datasets, transforms

def load_dataset(name):
    transform = transforms.Compose([transforms.ToTensor(), transforms.Lambda(lambda x: x.view(-1))])
    if name == "MNIST":
        train = datasets.MNIST(root='/tmp/data', train=True, download=True, transform=transform)
        test = datasets.MNIST(root='/tmp/data', train=False, download=True, transform=transform)
    elif name == "FashionMNIST":
        train = datasets.FashionMNIST(root='/tmp/data', train=True, download=True, transform=transform)
        test = datasets.FashionMNIST(root='/tmp/data', train=False, download=True, transform=transform)
    return train, test


def train_and_track(dataset_name, init_ts, n_epochs, seed=42):
    """Train and track tension_scale over epochs."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    train_ds, test_ds = load_dataset(dataset_name)
    train_loader = torch.utils.data.DataLoader(train_ds, batch_size=256, shuffle=True)

    model = PureFieldEngine(784, 128, 10, init_ts=init_ts)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    ts_history = [init_ts]

    for epoch in range(n_epochs):
        model.train()
        for x_batch, y_batch in train_loader:
            output, tension = model(x_batch)
            loss = F.cross_entropy(output, y_batch)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        ts_history.append(model.tension_scale.item())

    final_ts = model.tension_scale.item()
    return final_ts, ts_history


# ─────────────────────────────────────────
# Experiment 1: Various init, long-term training (MNIST, 50 epochs)
# ─────────────────────────────────────────

print("\n" + "─" * 70)
print("Experiment 1: MNIST — Various init, 50 epochs")
print("─" * 70)

inits = [0.01, 0.05, 0.10, 0.30, 0.50, 1.00, 1.39, 2.00, 3.00, 5.00]
n_epochs_long = 50

results_mnist = []

print(f"\n  {'init':>6} | {'final_ts':>10} | {'ln(4) error':>10} | {'converged?':>6} | History")
print(f"  {'─'*6}─┼─{'─'*10}─┼─{'─'*10}─┼─{'─'*6}─┼─{'─'*30}")

for init_val in inits:
    final_ts, history = train_and_track("MNIST", init_val, n_epochs_long)
    error_pct = abs(final_ts - LN4) / LN4 * 100
    converged = error_pct < 5.0

    # Compact history (every 10 epochs)
    brief = [f"{history[i]:.2f}" for i in range(0, len(history), 10)]

    results_mnist.append({
        "init": init_val,
        "final": final_ts,
        "error": error_pct,
        "converged": converged,
        "history": history,
    })

    conv_mark = "YES" if converged else "no"
    print(f"  {init_val:>6.2f} | {final_ts:>10.4f} | {error_pct:>9.1f}% | {conv_mark:>6} | {' -> '.join(brief)}")

# ─────────────────────────────────────────
# Experiment 2: Fashion-MNIST, 50 epochs
# ─────────────────────────────────────────

print("\n" + "─" * 70)
print("Experiment 2: FashionMNIST — Various init, 50 epochs")
print("─" * 70)

inits_fashion = [0.10, 0.30, 0.50, 1.00, 1.39, 2.00]
results_fashion = []

print(f"\n  {'init':>6} | {'final_ts':>10} | {'ln(4) error':>10} | {'converged?':>6}")
print(f"  {'─'*6}─┼─{'─'*10}─┼─{'─'*10}─┼─{'─'*6}")

for init_val in inits_fashion:
    final_ts, history = train_and_track("FashionMNIST", init_val, n_epochs_long)
    error_pct = abs(final_ts - LN4) / LN4 * 100
    converged = error_pct < 5.0
    conv_mark = "YES" if converged else "no"

    results_fashion.append({
        "init": init_val,
        "final": final_ts,
        "error": error_pct,
        "converged": converged,
    })
    print(f"  {init_val:>6.2f} | {final_ts:>10.4f} | {error_pct:>9.1f}% | {conv_mark:>6}")

# ─────────────────────────────────────────
# Experiment 3: Convergence path analysis (MNIST, multiple seeds)
# ─────────────────────────────────────────

print("\n" + "─" * 70)
print("Experiment 3: MNIST init=1.0, 5 seeds (50 epochs)")
print("─" * 70)

seeds = [42, 123, 456, 789, 1024]
multi_seed_finals = []

for seed in seeds:
    final_ts, history = train_and_track("MNIST", 1.0, n_epochs_long, seed=seed)
    multi_seed_finals.append(final_ts)
    error_pct = abs(final_ts - LN4) / LN4 * 100
    print(f"  seed={seed}: final={final_ts:.4f}, ln(4) error={error_pct:.1f}%")

mean_final = np.mean(multi_seed_finals)
std_final = np.std(multi_seed_finals)
mean_error = abs(mean_final - LN4) / LN4 * 100
print(f"\n  Average: {mean_final:.4f} +/- {std_final:.4f}")
print(f"  ln(4) error: {mean_error:.1f}%")

# ─────────────────────────────────────────
# ASCII graph: tension_scale convergence path
# ─────────────────────────────────────────

print("\n" + "─" * 70)
print("4. ASCII convergence path (MNIST, 50ep)")
print("─" * 70)

# Convergence paths for 3 representative inits
representative = [r for r in results_mnist if r["init"] in [0.01, 0.30, 1.39, 5.00]]

print(f"\n  tension_scale vs epoch:")
print(f"  ln(4) = {LN4:.4f} (dotted line position)")

height = 18
width = 50
y_min = 0.0
y_max = max(max(r["history"]) for r in representative) * 1.1

grid = [['.' for _ in range(width)] for _ in range(height)]

# ln(4) reference line
ln4_y = int((1 - (LN4 - y_min) / (y_max - y_min)) * (height - 1))
ln4_y = max(0, min(height - 1, ln4_y))
for x in range(width):
    grid[ln4_y][x] = '-'

symbols = ['o', 'x', '+', '*']
for idx, r in enumerate(representative):
    hist = r["history"]
    sym = symbols[idx % len(symbols)]
    for ep in range(0, len(hist), max(1, len(hist) // width)):
        x = int(ep / len(hist) * (width - 1))
        y = int((1 - (hist[ep] - y_min) / (y_max - y_min + 1e-10)) * (height - 1))
        x = max(0, min(width - 1, x))
        y = max(0, min(height - 1, y))
        grid[y][x] = sym

print(f"    {y_max:.1f} ^")
for row in grid:
    print(f"         |{''.join(row)}")
print(f"    {y_min:.1f} +{'─' * width}> epoch")
print(f"         0         10        20        30        40        50")

# Legend
for idx, r in enumerate(representative):
    sym = symbols[idx % len(symbols)]
    print(f"    {sym} = init={r['init']}")
print(f"    - = ln(4) = {LN4:.4f}")

# ─────────────────────────────────────────
# 5. Convergence basin analysis
# ─────────────────────────────────────────

print("\n" + "─" * 70)
print("5. Convergence basin analysis")
print("─" * 70)

# Distribution of final_ts for all MNIST results
all_finals = [r["final"] for r in results_mnist]

print(f"\n  MNIST overall final tension_scale distribution:")
print(f"    min  = {min(all_finals):.4f}")
print(f"    max  = {max(all_finals):.4f}")
print(f"    mean = {np.mean(all_finals):.4f}")
print(f"    std  = {np.std(all_finals):.4f}")
print(f"    ln(4) = {LN4:.4f}")

# Convergence determination
converged_count = sum(1 for r in results_mnist if r["converged"])
print(f"\n  ln(4) convergence (error <5%): {converged_count}/{len(results_mnist)}")

# Convergence by init range
print(f"\n  Convergence by init range:")
ranges = [(0, 0.1), (0.1, 0.5), (0.5, 1.5), (1.5, 3.0), (3.0, 10.0)]
for lo, hi in ranges:
    subset = [r for r in results_mnist if lo <= r["init"] < hi]
    if subset:
        conv = sum(1 for r in subset if r["converged"])
        avg = np.mean([r["final"] for r in subset])
        print(f"    init [{lo:.1f}, {hi:.1f}): {conv}/{len(subset)} converged, average final={avg:.4f}")

# ─────────────────────────────────────────
# 6. Conclusion
# ─────────────────────────────────────────

print("\n" + "=" * 70)
print("Conclusion")
print("=" * 70)

# Summary
mnist_conv = sum(1 for r in results_mnist if r["converged"])
fashion_conv = sum(1 for r in results_fashion if r["converged"])

print(f"\n  MNIST ln(4) convergence:   {mnist_conv}/{len(results_mnist)} (50ep)")
print(f"  Fashion ln(4) convergence: {fashion_conv}/{len(results_fashion)} (50ep)")
print(f"  Multi-seed average:        {mean_final:.4f} +/- {std_final:.4f} (init=1.0)")
print(f"  ln(4) = {LN4:.4f}")

# Initial value dependency determination
all_close = all(r["converged"] for r in results_mnist)
some_close = any(r["converged"] for r in results_mnist)

if all_close:
    init_verdict = "Convergence independent of initial value — universal attractor"
elif some_close:
    converged_inits = [r["init"] for r in results_mnist if r["converged"]]
    init_verdict = f"Initial value bias — convergence only near init={converged_inits}"
else:
    init_verdict = "ln(4) convergence rejected — no convergence with any init (50ep)"

print(f"\n  Initial value verdict: {init_verdict}")

# Overall verdict
if all_close and fashion_conv == len(results_fashion):
    verdict = "Strong support — ln(4) is a universal attractor"
elif some_close:
    verdict = "Weakened support — convergence only with specific init, lacks universality"
else:
    verdict = "Rejected — ln(4) convergence is coincidental"

print(f"  Overall verdict: {verdict}")

print(f"\n  ⚠️ Limitations:")
print(f"    - 50 epochs may not be sufficient (100ep+ needed?)")
print(f"    - Optimizer (Adam) dependency not verified")
print(f"    - Learning rate dependency not verified")
print(f"    - Possibility of multiple minima in loss landscape")
print("=" * 70)