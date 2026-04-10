#!/usr/bin/env python3
"""Experiment: Repulsion Field on Time Series Classification

Synthetic time series dataset:
  - 3 classes: sine wave, square wave, sawtooth wave
  - 100 samples per class, length 50, with noise
  - Flattened to 50-dim input

Compare:
  1. Dense MLP (baseline)
  2. RepulsionField (pole+ vs pole-, tension-modulated output)

Key question: Does tension carry information in time series?
  - Hypothesis: different waveform shapes produce different tension signatures
  - Sine = smooth = low tension, Square = sharp = high tension
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import time


# ─── Synthetic Data Generation ───

def generate_timeseries(n_per_class=100, seq_len=50, noise_std=0.15, seed=42):
    """Generate 3 classes of time series: sine, square, sawtooth."""
    rng = np.random.RandomState(seed)
    X_all, y_all = [], []
    t = np.linspace(0, 2 * np.pi, seq_len)

    for i in range(n_per_class):
        freq = rng.uniform(0.8, 1.5)

        # Class 0: sine wave
        sine = np.sin(freq * t)
        sine += rng.randn(seq_len) * noise_std
        X_all.append(sine)
        y_all.append(0)

        # Class 1: square wave
        square = np.sign(np.sin(freq * t))
        square += rng.randn(seq_len) * noise_std
        X_all.append(square)
        y_all.append(1)

        # Class 2: sawtooth wave
        sawtooth = 2 * ((freq * t / (2 * np.pi)) % 1) - 1
        sawtooth += rng.randn(seq_len) * noise_std
        X_all.append(sawtooth)
        y_all.append(2)

    X = np.array(X_all, dtype=np.float32)
    y = np.array(y_all, dtype=np.int64)

    # Shuffle
    idx = rng.permutation(len(y))
    X, y = X[idx], y[idx]

    # Split 80/20
    split = int(0.8 * len(y))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    train_dataset = torch.utils.data.TensorDataset(
        torch.from_numpy(X_train), torch.from_numpy(y_train))
    test_dataset = torch.utils.data.TensorDataset(
        torch.from_numpy(X_test), torch.from_numpy(y_test))

    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=32, shuffle=True)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=64, shuffle=False)

    return train_loader, test_loader


# ─── Models ───

class DenseMLP(nn.Module):
    """Simple dense MLP baseline."""
    def __init__(self, input_dim=50, hidden_dim=48, output_dim=3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )
        self.tension_magnitude = 0.0

    def forward(self, x):
        return self.net(x)


class PoleNet(nn.Module):
    """A single pole: small MLP expert."""
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.net(x)


class RepulsionField(nn.Module):
    """Two-pole repulsion field for time series.

    pole+ and pole- produce competing outputs.
    Output = equilibrium + tension_scale * sqrt(tension) * field_direction

    Tension = ||pole+ - pole-||^2 per sample.
    """
    def __init__(self, input_dim=50, hidden_dim=48, output_dim=3):
        super().__init__()
        self.pole_plus = PoleNet(input_dim, hidden_dim, output_dim)
        self.pole_minus = PoleNet(input_dim, hidden_dim, output_dim)

        self.field_transform = nn.Sequential(
            nn.Linear(output_dim, output_dim),
            nn.Tanh(),
        )

        # tension scale init = 1/3 (meta fixed point)
        self.tension_scale = nn.Parameter(torch.tensor(1/3))

        self.tension_magnitude = 0.0
        self.per_sample_tension = None  # for analysis

    def forward(self, x):
        out_plus = self.pole_plus(x)
        out_minus = self.pole_minus(x)

        repulsion = out_plus - out_minus
        tension = (repulsion ** 2).sum(dim=-1, keepdim=True)
        equilibrium = (out_plus + out_minus) / 2
        field_direction = self.field_transform(repulsion)
        output = equilibrium + self.tension_scale * torch.sqrt(tension + 1e-8) * field_direction

        with torch.no_grad():
            self.tension_magnitude = tension.mean().item()
            self.per_sample_tension = tension.squeeze(-1)

        return output


# ─── Training ───

def train_model(model, train_loader, test_loader, epochs=30, lr=0.003):
    """Train and return epoch-wise metrics."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    history = {'train_loss': [], 'test_acc': [], 'tension': []}

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        n_batches = 0
        for X, y in train_loader:
            optimizer.zero_grad()
            out = model(X)
            loss = F.cross_entropy(out, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            n_batches += 1

        # Evaluate
        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for X, y in test_loader:
                out = model(X)
                preds = out.argmax(1)
                correct += (preds == y).sum().item()
                total += y.size(0)

        acc = correct / total
        avg_loss = total_loss / n_batches
        history['train_loss'].append(avg_loss)
        history['test_acc'].append(acc)
        history['tension'].append(getattr(model, 'tension_magnitude', 0.0))

    return history


def count_params(model):
    return sum(p.numel() for p in model.parameters())


# ─── Tension Analysis ───

def analyze_tension_per_class(model, test_loader, class_names):
    """Measure tension per class to see if it carries waveform information."""
    model.eval()
    class_tensions = {i: [] for i in range(len(class_names))}

    with torch.no_grad():
        for X, y in test_loader:
            _ = model(X)
            if model.per_sample_tension is not None:
                tensions = model.per_sample_tension.cpu().numpy()
                labels = y.cpu().numpy()
                for t_val, lbl in zip(tensions, labels):
                    class_tensions[lbl].append(t_val)

    return {i: np.array(v) for i, v in class_tensions.items()}


# ─── Main ───

def main():
    print()
    print("=" * 70)
    print("   Experiment: Repulsion Field on Time Series Classification")
    print("   Synthetic: sine / square / sawtooth (50-dim, 3 classes)")
    print("=" * 70)

    CLASS_NAMES = ['sine', 'square', 'sawtooth']
    INPUT_DIM = 50
    HIDDEN_DIM = 48
    OUTPUT_DIM = 3
    EPOCHS = 40
    N_TRIALS = 5

    all_results = {'dense': [], 'repulsion': []}

    for trial in range(N_TRIALS):
        seed = 42 + trial * 17
        train_loader, test_loader = generate_timeseries(
            n_per_class=100, seq_len=INPUT_DIM, noise_std=0.15, seed=seed)

        torch.manual_seed(seed)
        dense = DenseMLP(INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM)
        hist_dense = train_model(dense, train_loader, test_loader, EPOCHS)

        torch.manual_seed(seed)
        repulsion = RepulsionField(INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM)
        hist_repulsion = train_model(repulsion, train_loader, test_loader, EPOCHS)

        all_results['dense'].append({
            'acc': hist_dense['test_acc'][-1],
            'history': hist_dense,
            'params': count_params(dense),
        })
        all_results['repulsion'].append({
            'acc': hist_repulsion['test_acc'][-1],
            'history': hist_repulsion,
            'params': count_params(repulsion),
            'model': repulsion,
            'test_loader': test_loader,
        })

        print(f"  Trial {trial+1}/{N_TRIALS}: Dense={hist_dense['test_acc'][-1]*100:.1f}%  "
              f"Repulsion={hist_repulsion['test_acc'][-1]*100:.1f}%  "
              f"tension={hist_repulsion['tension'][-1]:.4f}")

    # ─── Summary ───
    print()
    print("=" * 70)
    print("   RESULTS SUMMARY")
    print("=" * 70)

    for key, label in [('dense', 'Dense MLP'), ('repulsion', 'RepulsionField')]:
        accs = [r['acc'] for r in all_results[key]]
        params = all_results[key][0]['params']
        print(f"  {label:<20} acc={np.mean(accs)*100:.2f}% +/- {np.std(accs)*100:.2f}%  "
              f"params={params:,}")

    dense_mean = np.mean([r['acc'] for r in all_results['dense']])
    repul_mean = np.mean([r['acc'] for r in all_results['repulsion']])
    delta = (repul_mean - dense_mean) * 100
    print(f"\n  Delta (Repulsion - Dense): {'+' if delta >= 0 else ''}{delta:.2f}%")

    # ─── Learning Curves (best trial) ───
    best_trial = max(range(N_TRIALS), key=lambda i: all_results['repulsion'][i]['acc'])
    print(f"\n  Learning Curves (best trial = {best_trial+1}):")
    print(f"  {'Epoch':<8} {'Dense':>10} {'Repulsion':>12} {'Tension':>12}")
    print("  " + "-" * 44)
    hd = all_results['dense'][best_trial]['history']
    hr = all_results['repulsion'][best_trial]['history']
    for ep in [0, 4, 9, 14, 19, 24, 29, 34, 39]:
        if ep < EPOCHS:
            print(f"  {ep+1:<8} {hd['test_acc'][ep]*100:>9.1f}% {hr['test_acc'][ep]*100:>11.1f}% "
                  f"{hr['tension'][ep]:>11.4f}")

    # ─── Tension Per Class Analysis ───
    print(f"\n{'='*70}")
    print("   TENSION ANALYSIS: Does tension carry waveform information?")
    print(f"{'='*70}")

    # Use last trial's repulsion model
    last_model = all_results['repulsion'][-1]['model']
    last_loader = all_results['repulsion'][-1]['test_loader']
    class_tensions = analyze_tension_per_class(last_model, last_loader, CLASS_NAMES)

    print(f"\n  {'Class':<12} {'Mean':>10} {'Std':>10} {'Min':>10} {'Max':>10} {'N':>6}")
    print("  " + "-" * 52)
    means = []
    for i, name in enumerate(CLASS_NAMES):
        t = class_tensions[i]
        if len(t) > 0:
            means.append(np.mean(t))
            print(f"  {name:<12} {np.mean(t):>10.4f} {np.std(t):>10.4f} "
                  f"{np.min(t):>10.4f} {np.max(t):>10.4f} {len(t):>6}")
        else:
            means.append(0)
            print(f"  {name:<12} {'(no data)':>10}")

    # Tension separation metric
    if len(means) == 3 and all(m > 0 for m in means):
        tension_range = max(means) - min(means)
        tension_cv = np.std(means) / np.mean(means) if np.mean(means) > 0 else 0
        print(f"\n  Tension range across classes:  {tension_range:.4f}")
        print(f"  Tension CV across classes:     {tension_cv:.4f}")

        # Sort classes by tension
        sorted_classes = sorted(enumerate(CLASS_NAMES), key=lambda x: means[x[0]])
        print(f"\n  Tension ordering (low -> high):")
        for idx, name in sorted_classes:
            print(f"    {name}: {means[idx]:.4f}")

        if tension_cv > 0.1:
            print(f"\n  -> Tension SEPARATES classes (CV={tension_cv:.2f} > 0.1)")
            print(f"     Tension carries waveform shape information!")
        else:
            print(f"\n  -> Tension does NOT separate classes well (CV={tension_cv:.2f})")

    # ─── ASCII Tension Histogram ───
    print(f"\n  Tension Distribution per Class (ASCII):")
    max_tension = max(np.max(class_tensions[i]) for i in range(3) if len(class_tensions[i]) > 0)
    n_bins = 10
    bins = np.linspace(0, max_tension * 1.01, n_bins + 1)

    for i, name in enumerate(CLASS_NAMES):
        t = class_tensions[i]
        if len(t) == 0:
            continue
        hist, _ = np.histogram(t, bins=bins)
        max_count = max(hist) if max(hist) > 0 else 1
        print(f"\n  {name}:")
        for b in range(n_bins):
            bar_len = int(30 * hist[b] / max_count)
            lo = bins[b]
            hi = bins[b+1]
            print(f"    [{lo:6.2f}-{hi:6.2f}] {'#' * bar_len} ({hist[b]})")

    # ─── Tension Evolution Over Training ───
    print(f"\n{'='*70}")
    print("   TENSION EVOLUTION OVER TRAINING")
    print(f"{'='*70}")
    tensions_over_time = hr['tension']
    print(f"\n  Epoch  1: tension = {tensions_over_time[0]:.6f}")
    print(f"  Epoch 10: tension = {tensions_over_time[min(9, EPOCHS-1)]:.6f}")
    print(f"  Epoch 20: tension = {tensions_over_time[min(19, EPOCHS-1)]:.6f}")
    print(f"  Epoch 30: tension = {tensions_over_time[min(29, EPOCHS-1)]:.6f}")
    print(f"  Epoch 40: tension = {tensions_over_time[min(39, EPOCHS-1)]:.6f}")

    t_start = tensions_over_time[0]
    t_end = tensions_over_time[-1]
    if t_start > 0:
        ratio = t_end / t_start
        print(f"\n  Tension ratio (end/start): {ratio:.2f}x")
        if ratio > 1.5:
            print(f"  -> Tension GREW during training (poles diverged)")
        elif ratio < 0.67:
            print(f"  -> Tension SHRANK during training (poles converged)")
        else:
            print(f"  -> Tension stayed STABLE during training")

    # ─── Final Verdict ───
    print(f"\n{'='*70}")
    print("   VERDICT")
    print(f"{'='*70}")

    if delta > 1.0:
        print(f"  RepulsionField BEATS Dense by +{delta:.2f}%")
    elif delta > -1.0:
        print(f"  RepulsionField is COMPARABLE to Dense ({delta:+.2f}%)")
    else:
        print(f"  Dense BEATS RepulsionField by {-delta:.2f}%")

    if tension_cv > 0.1:
        print(f"  Tension CARRIES waveform information (CV={tension_cv:.2f})")
        print(f"  -> Different wave shapes produce different tension levels")
        print(f"  -> This suggests tension encodes input complexity/sharpness")
    else:
        print(f"  Tension does NOT strongly separate classes (CV={tension_cv:.2f})")

    param_dense = all_results['dense'][0]['params']
    param_repul = all_results['repulsion'][0]['params']
    print(f"\n  Parameters: Dense={param_dense:,}  Repulsion={param_repul:,} "
          f"(+{param_repul - param_dense:,}, {(param_repul - param_dense)/param_dense*100:+.1f}%)")
    print()


if __name__ == '__main__':
    main()
