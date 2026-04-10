#!/usr/bin/env python3
"""
H-SEDI-EE-5: R-Spectrum Guided Pruning
========================================
Hypothesis: Neurons whose activation "R-spectrum" deviates most from 1
(the balance point, R(6)=1) are least efficient. Pruning them retains
accuracy while reducing compute.

R(n) = sigma(n)*phi(n) / (n*tau(n)) measures arithmetic balance.
We adapt this to neurons: R_neuron = mean_act * std_act / (median_act * count_active)
R ~ 1 means balanced activation. R >> 1 or R << 1 means imbalanced.

Test plan:
  1. Train PureFieldEngine on MNIST
  2. Collect activation statistics per neuron over validation set
  3. Compute R_neuron for each hidden neuron
  4. Prune neurons with |R - 1| largest (most imbalanced)
  5. Compare: accuracy retention at 10%, 20%, 30% pruning rates
  6. Baseline: random pruning at same rates
"""

import sys
sys.path.insert(0, '/Users/ghost/Dev/TECS-L')

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import time
import copy

from model_utils import load_mnist

torch.manual_seed(42)
np.random.seed(42)


# ─── PureField with activation hooks ────────────────────────────────────────

class PureFieldWithStats(nn.Module):
    """PureFieldEngine variant that collects activation statistics."""

    def __init__(self, input_dim=784, hidden_dim=128, output_dim=10):
        super().__init__()
        self.engine_a_fc1 = nn.Linear(input_dim, hidden_dim)
        self.engine_a_fc2 = nn.Linear(hidden_dim, output_dim)
        self.engine_g_fc1 = nn.Linear(input_dim, hidden_dim)
        self.engine_g_fc2 = nn.Linear(hidden_dim, output_dim)
        self.dropout = nn.Dropout(0.3)
        self.hidden_dim = hidden_dim

        # Activation collectors
        self.activations_a = []
        self.activations_g = []
        self.collecting = False

    def forward(self, x):
        h_a = F.relu(self.engine_a_fc1(x))
        if self.collecting:
            self.activations_a.append(h_a.detach())
        h_a = self.dropout(h_a)
        out_a = self.engine_a_fc2(h_a)

        h_g = F.relu(self.engine_g_fc1(x))
        if self.collecting:
            self.activations_g.append(h_g.detach())
        h_g = self.dropout(h_g)
        out_g = self.engine_g_fc2(h_g)

        output = out_a - out_g
        tension = (output ** 2).mean(dim=-1)
        return output, tension

    def start_collecting(self):
        self.collecting = True
        self.activations_a = []
        self.activations_g = []

    def stop_collecting(self):
        self.collecting = False
        acts_a = torch.cat(self.activations_a, dim=0)  # (N, hidden_dim)
        acts_g = torch.cat(self.activations_g, dim=0)
        self.activations_a = []
        self.activations_g = []
        return acts_a, acts_g


# ─── R-spectrum computation ──────────────────────────────────────────────────

def compute_r_spectrum(activations):
    """Compute R_neuron = mean * std / (median * fraction_active) for each neuron.

    R ~ 1 means balanced activation pattern.
    R >> 1 means few very strong activations (spiky).
    R << 1 means uniform weak activations (flat).
    """
    # activations: (N, hidden_dim)
    N = activations.size(0)

    r_values = []
    for j in range(activations.size(1)):
        col = activations[:, j]
        mean_act = col.mean().item()
        std_act = col.std().item()
        median_act = col.median().item()
        fraction_active = (col > 0).float().mean().item()

        # R = mean * std / (|median| * fraction_active)
        denom = (abs(median_act) + 1e-8) * (fraction_active + 1e-8)
        r = (abs(mean_act) * std_act) / denom
        r_values.append(r)

    return np.array(r_values)


def prune_neurons(model, indices_to_prune, engine='a'):
    """Zero out pruned neurons by setting their incoming/outgoing weights to 0."""
    pruned = copy.deepcopy(model)

    if engine == 'a':
        fc1 = pruned.engine_a_fc1
        fc2 = pruned.engine_a_fc2
    else:
        fc1 = pruned.engine_g_fc1
        fc2 = pruned.engine_g_fc2

    with torch.no_grad():
        for idx in indices_to_prune:
            fc1.weight[idx].zero_()
            fc1.bias[idx].zero_()
            fc2.weight[:, idx].zero_()

    return pruned


def evaluate(model, loader):
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for X, y in loader:
            X = X.view(X.size(0), -1)
            out, _ = model(X)
            correct += (out.argmax(1) == y).sum().item()
            total += y.size(0)
    return correct / total


def main():
    print("=" * 70)
    print("  H-SEDI-EE-5: R-Spectrum Guided Pruning")
    print("=" * 70)

    EPOCHS = 10
    PRUNE_RATES = [0.1, 0.2, 0.3, 0.5]

    train_loader, test_loader = load_mnist(batch_size=128)

    # ─── Train model ─────────────────────────────────────────────────────────
    print("\n  [1/4] Training PureFieldWithStats on MNIST...")
    model = PureFieldWithStats(784, 128, 10)
    params = sum(p.numel() for p in model.parameters())
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(EPOCHS):
        model.train()
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            out, _ = model(X)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()

    baseline_acc = evaluate(model, test_loader)
    print(f"    Baseline accuracy: {baseline_acc*100:.2f}%, Params: {params:,}")

    # ─── Collect activations ─────────────────────────────────────────────────
    print("\n  [2/4] Collecting activation statistics...")
    model.eval()
    model.start_collecting()
    with torch.no_grad():
        for X, y in test_loader:
            X = X.view(X.size(0), -1)
            model(X)
    acts_a, acts_g = model.stop_collecting()
    print(f"    Collected activations: A={acts_a.shape}, G={acts_g.shape}")

    # ─── Compute R-spectrum ──────────────────────────────────────────────────
    print("\n  [3/4] Computing R-spectrum...")
    r_a = compute_r_spectrum(acts_a)
    r_g = compute_r_spectrum(acts_g)

    r_combined = np.concatenate([r_a, r_g])
    deviation = np.abs(r_combined - 1.0)  # Distance from balance point

    print(f"    Engine A: R mean={r_a.mean():.4f}, std={r_a.std():.4f}, "
          f"min={r_a.min():.4f}, max={r_a.max():.4f}")
    print(f"    Engine G: R mean={r_g.mean():.4f}, std={r_g.std():.4f}, "
          f"min={r_g.min():.4f}, max={r_g.max():.4f}")

    # R-spectrum distribution (ASCII histogram)
    print("\n    R-spectrum Distribution (Engine A):")
    bins = [0, 0.5, 0.8, 0.9, 1.0, 1.1, 1.2, 1.5, 2.0, 5.0, float('inf')]
    for i in range(len(bins) - 1):
        count = np.sum((r_a >= bins[i]) & (r_a < bins[i+1]))
        bar = '#' * (count * 2)
        label = f"[{bins[i]:.1f}-{bins[i+1]:.1f})" if bins[i+1] != float('inf') else f"[{bins[i]:.1f}+)"
        print(f"      {label:>12}: {bar} ({count})")

    # ─── Pruning experiments ─────────────────────────────────────────────────
    print("\n  [4/4] Pruning experiments...")

    # Sort neurons by deviation from R=1 (most imbalanced first)
    dev_a = np.abs(r_a - 1.0)
    dev_g = np.abs(r_g - 1.0)

    results = {}

    for rate in PRUNE_RATES:
        n_prune = int(model.hidden_dim * rate)

        # R-spectrum pruning: prune most imbalanced neurons
        prune_idx_a = np.argsort(dev_a)[-n_prune:]  # highest deviation
        prune_idx_g = np.argsort(dev_g)[-n_prune:]

        pruned_model = copy.deepcopy(model)
        with torch.no_grad():
            for idx in prune_idx_a:
                pruned_model.engine_a_fc1.weight[idx].zero_()
                pruned_model.engine_a_fc1.bias[idx].zero_()
                pruned_model.engine_a_fc2.weight[:, idx].zero_()
            for idx in prune_idx_g:
                pruned_model.engine_g_fc1.weight[idx].zero_()
                pruned_model.engine_g_fc1.bias[idx].zero_()
                pruned_model.engine_g_fc2.weight[:, idx].zero_()

        r_acc = evaluate(pruned_model, test_loader)

        # Random pruning baseline (average over 5 trials)
        rand_accs = []
        for trial in range(5):
            np.random.seed(trial * 7 + 13)
            rand_idx_a = np.random.choice(model.hidden_dim, n_prune, replace=False)
            rand_idx_g = np.random.choice(model.hidden_dim, n_prune, replace=False)

            rand_model = copy.deepcopy(model)
            with torch.no_grad():
                for idx in rand_idx_a:
                    rand_model.engine_a_fc1.weight[idx].zero_()
                    rand_model.engine_a_fc1.bias[idx].zero_()
                    rand_model.engine_a_fc2.weight[:, idx].zero_()
                for idx in rand_idx_g:
                    rand_model.engine_g_fc1.weight[idx].zero_()
                    rand_model.engine_g_fc1.bias[idx].zero_()
                    rand_model.engine_g_fc2.weight[:, idx].zero_()
            rand_accs.append(evaluate(rand_model, test_loader))

        rand_acc_mean = np.mean(rand_accs)
        rand_acc_std = np.std(rand_accs)

        # Magnitude pruning: prune smallest weight norm neurons
        norms_a = np.array([model.engine_a_fc1.weight[i].norm().item()
                           for i in range(model.hidden_dim)])
        norms_g = np.array([model.engine_g_fc1.weight[i].norm().item()
                           for i in range(model.hidden_dim)])
        mag_idx_a = np.argsort(norms_a)[:n_prune]  # smallest norms
        mag_idx_g = np.argsort(norms_g)[:n_prune]

        mag_model = copy.deepcopy(model)
        with torch.no_grad():
            for idx in mag_idx_a:
                mag_model.engine_a_fc1.weight[idx].zero_()
                mag_model.engine_a_fc1.bias[idx].zero_()
                mag_model.engine_a_fc2.weight[:, idx].zero_()
            for idx in mag_idx_g:
                mag_model.engine_g_fc1.weight[idx].zero_()
                mag_model.engine_g_fc1.bias[idx].zero_()
                mag_model.engine_g_fc2.weight[:, idx].zero_()
        mag_acc = evaluate(mag_model, test_loader)

        results[rate] = {
            'r_acc': r_acc,
            'rand_acc': rand_acc_mean,
            'rand_std': rand_acc_std,
            'mag_acc': mag_acc,
            'n_pruned': n_prune * 2,  # both engines
        }

    # ─── Results ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 90)
    print("  PRUNING RESULTS")
    print("=" * 90)
    print(f"  Baseline (no pruning): {baseline_acc*100:.2f}%")
    print()
    print(f"  {'Prune%':>7} | {'R-Prune':>8} | {'Random':>12} | {'Magnitude':>10} | "
          f"{'R vs Rand':>10} | {'R vs Mag':>10} | {'Neurons Pruned':>14}")
    print("-" * 90)

    for rate in PRUNE_RATES:
        r = results[rate]
        r_vs_rand = (r['r_acc'] - r['rand_acc']) * 100
        r_vs_mag = (r['r_acc'] - r['mag_acc']) * 100
        print(f"  {rate*100:>6.0f}% | {r['r_acc']*100:>7.2f}% | "
              f"{r['rand_acc']*100:>6.2f}%+/-{r['rand_std']*100:.1f} | "
              f"{r['mag_acc']*100:>9.2f}% | {r_vs_rand:>+9.2f}% | "
              f"{r_vs_mag:>+9.2f}% | {r['n_pruned']:>14}")

    # ─── ASCII comparison ────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  ACCURACY RETENTION (higher is better)")
    print("=" * 70)
    for rate in PRUNE_RATES:
        r = results[rate]
        r_bar = '#' * int(r['r_acc'] * 50)
        rand_bar = '-' * int(r['rand_acc'] * 50)
        mag_bar = '=' * int(r['mag_acc'] * 50)
        print(f"  {rate*100:.0f}% pruned:")
        print(f"    R-spec: {r_bar} {r['r_acc']*100:.1f}%")
        print(f"    Random: {rand_bar} {r['rand_acc']*100:.1f}%")
        print(f"    Magnit: {mag_bar} {r['mag_acc']*100:.1f}%")

    # ─── Verdict ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  VERDICT")
    print("=" * 70)

    r_wins = sum(1 for rate in PRUNE_RATES
                 if results[rate]['r_acc'] > results[rate]['rand_acc'])
    r_vs_mag_wins = sum(1 for rate in PRUNE_RATES
                        if results[rate]['r_acc'] > results[rate]['mag_acc'])

    if r_wins >= 3:
        avg_advantage = np.mean([results[r]['r_acc'] - results[r]['rand_acc']
                                 for r in PRUNE_RATES]) * 100
        print(f"  SUPPORTED: R-spectrum pruning outperforms random in {r_wins}/{len(PRUNE_RATES)} rates")
        print(f"  Average advantage over random: {avg_advantage:+.2f}%")
        if r_vs_mag_wins >= 3:
            print(f"  Also beats magnitude pruning in {r_vs_mag_wins}/{len(PRUNE_RATES)} rates")
        else:
            print(f"  But magnitude pruning is competitive ({r_vs_mag_wins}/{len(PRUNE_RATES)} wins)")
    elif r_wins >= 2:
        print(f"  WEAKLY SUPPORTED: R-spectrum beats random in {r_wins}/{len(PRUNE_RATES)} rates")
        print(f"  Mixed results — may depend on pruning rate")
    else:
        print(f"  NOT SUPPORTED: R-spectrum pruning does not consistently beat random")
        print(f"  Wins: {r_wins}/{len(PRUNE_RATES)} vs random, "
              f"{r_vs_mag_wins}/{len(PRUNE_RATES)} vs magnitude")

    print("=" * 70)


if __name__ == '__main__':
    main()
