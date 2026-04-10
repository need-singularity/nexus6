#!/usr/bin/env python3
"""Time Series Mitosis Anomaly Detection

NEW experiment type: mitosis on time-series data.

Datasets (all synthetic):
  1. Sine: normal = sine + noise, anomaly = sine + sudden spike/shift
  2. ECG-like: normal = periodic bumps, anomaly = irregular spacing

Methods compared:
  - Mitosis inter-tension (parent AE splits into 2, inter-child disagreement)
  - Simple reconstruction error (single AE)
  - Isolation Forest baseline

3 trials, AUROC metric.
"""

import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import copy
from sklearn.metrics import roc_auc_score
from sklearn.ensemble import IsolationForest

# ─── Synthetic Data Generators ───────────────────────────────────────

def generate_sine_data(n_normal=100, n_anomaly=20, length=50, seed=None):
    """Normal: sine + slight noise. Anomaly: sine + subtle spike/shift/freq change."""
    rng = np.random.RandomState(seed)
    t = np.linspace(0, 4 * np.pi, length)

    normals = []
    for _ in range(n_normal):
        freq = 1.0 + rng.randn() * 0.05
        phase = rng.uniform(0, 2 * np.pi)
        noise = rng.randn(length) * 0.15
        s = np.sin(freq * t + phase) + noise
        normals.append(s)

    anomalies = []
    for _ in range(n_anomaly):
        freq = 1.0 + rng.randn() * 0.05
        phase = rng.uniform(0, 2 * np.pi)
        noise = rng.randn(length) * 0.15
        s = np.sin(freq * t + phase) + noise
        # Inject SUBTLE anomaly (harder to detect)
        anom_type = rng.randint(0, 4)
        if anom_type == 0:
            # Small spike (0.5-1.0 amplitude, within noise range overlap)
            pos = rng.randint(10, length - 10)
            s[pos:pos + 2] += rng.choice([-1, 1]) * rng.uniform(0.5, 1.0)
        elif anom_type == 1:
            # Small level shift (0.3-0.7)
            pos = rng.randint(15, length - 10)
            s[pos:] += rng.choice([-1, 1]) * rng.uniform(0.3, 0.7)
        elif anom_type == 2:
            # Frequency change mid-series
            pos = rng.randint(15, 30)
            new_freq = freq * rng.uniform(1.3, 1.8)
            s[pos:] = np.sin(new_freq * t[pos:] + phase) + noise[pos:]
        else:
            # Phase discontinuity
            pos = rng.randint(15, 35)
            s[pos:] = np.sin(freq * t[pos:] + phase + np.pi * 0.5) + noise[pos:]
        anomalies.append(s)

    return np.array(normals), np.array(anomalies)


def generate_ecg_data(n_normal=100, n_anomaly=20, length=50, seed=None):
    """Normal: periodic bumps (heartbeat-like). Anomaly: irregular spacing."""
    rng = np.random.RandomState(seed)

    def make_ecg(length, beat_interval, jitter, rng):
        s = np.zeros(length)
        pos = rng.randint(0, beat_interval)
        while pos < length:
            # QRS-like bump: sharp peak
            width = max(2, int(beat_interval * 0.15))
            for k in range(-width, width + 1):
                idx = pos + k
                if 0 <= idx < length:
                    s[idx] += np.exp(-0.5 * (k / max(width * 0.4, 1)) ** 2)
            # T-wave: smaller bump after QRS
            t_pos = pos + int(beat_interval * 0.35)
            t_width = max(2, int(beat_interval * 0.2))
            for k in range(-t_width, t_width + 1):
                idx = t_pos + k
                if 0 <= idx < length:
                    s[idx] += 0.3 * np.exp(-0.5 * (k / max(t_width * 0.5, 1)) ** 2)
            pos += beat_interval + int(rng.randn() * jitter)
            pos = max(pos, pos)  # ensure forward
        return s + rng.randn(length) * 0.05

    normals = []
    for _ in range(n_normal):
        interval = rng.randint(8, 12)
        s = make_ecg(length, interval, jitter=0.5, rng=rng)
        normals.append(s)

    anomalies = []
    for _ in range(n_anomaly):
        interval = rng.randint(8, 12)
        anom_type = rng.randint(0, 4)
        if anom_type == 0:
            # Moderate jitter (subtle arrhythmia)
            s = make_ecg(length, interval, jitter=2.0, rng=rng)
        elif anom_type == 1:
            # Small extra beat (amplitude 0.6, subtle)
            s = make_ecg(length, interval, jitter=0.8, rng=rng)
            pos = rng.randint(8, length - 8)
            for k in range(-2, 3):
                idx = pos + k
                if 0 <= idx < length:
                    s[idx] += 0.6 * np.exp(-0.5 * (k / 1.0) ** 2)
        elif anom_type == 2:
            # Partial amplitude change (ST elevation-like)
            s = make_ecg(length, interval, jitter=0.5, rng=rng)
            pos = rng.randint(15, length - 15)
            s[pos:pos + 8] += 0.4
        else:
            # Slightly dampened segment (weakened beat)
            s = make_ecg(length, interval, jitter=0.5, rng=rng)
            pos = rng.randint(10, length - 15)
            s[pos:pos + 10] *= 0.5
        anomalies.append(s)

    return np.array(normals), np.array(anomalies)


# ─── Sliding Window Features ─────────────────────────────────────────

def sliding_window_features(series_array, window_size=10):
    """Convert each time series to a set of sliding-window feature vectors.
    Returns (features, series_indices) where series_indices maps each window
    back to its source series."""
    all_windows = []
    all_indices = []
    for i, s in enumerate(series_array):
        n_windows = len(s) - window_size + 1
        for j in range(n_windows):
            all_windows.append(s[j:j + window_size])
            all_indices.append(i)
    return np.array(all_windows), np.array(all_indices)


def series_level_score(window_scores, window_indices, n_series):
    """Aggregate window-level scores to series-level by mean."""
    scores = np.zeros(n_series)
    counts = np.zeros(n_series)
    for sc, idx in zip(window_scores, window_indices):
        scores[idx] += sc
        counts[idx] += 1
    counts = np.maximum(counts, 1)
    return scores / counts


# ─── Models ──────────────────────────────────────────────────────────

class SimpleAE(nn.Module):
    """Simple 2-engine autoencoder with internal tension."""
    def __init__(self, input_dim, hidden_dim=32, latent_dim=8):
        super().__init__()
        # Engine A: encoder path 1
        self.enc_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, latent_dim)
        )
        # Engine G: encoder path 2
        self.enc_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, latent_dim)
        )
        # Shared decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, input_dim)
        )

    def forward(self, x):
        z_a = self.enc_a(x)
        z_g = self.enc_g(x)
        z = (z_a + z_g) / 2  # merge
        recon = self.decoder(z)
        tension = ((z_a - z_g) ** 2).mean(dim=-1)
        return recon, tension


def mitosis(parent, scale=0.01):
    """Split parent into two children with small perturbation."""
    child_a = copy.deepcopy(parent)
    child_b = copy.deepcopy(parent)
    with torch.no_grad():
        for p in child_a.parameters():
            p.add_(torch.randn_like(p) * scale)
        for p in child_b.parameters():
            p.add_(torch.randn_like(p) * scale)
    return child_a, child_b


# ─── Training ────────────────────────────────────────────────────────

def train_ae(model, X_train, epochs=50, lr=1e-3):
    """Train autoencoder on normal data with MSE loss."""
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    model.train()
    for ep in range(epochs):
        perm = torch.randperm(len(X_train))
        for start in range(0, len(X_train), 64):
            batch = X_train[perm[start:start + 64]]
            opt.zero_grad()
            recon, _ = model(batch)
            loss = F.mse_loss(recon, batch)
            loss.backward()
            opt.step()
    return model


def train_child(model, X_train, epochs=30, lr=1e-3):
    """Train a child model independently on a subset."""
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    model.train()
    for ep in range(epochs):
        perm = torch.randperm(len(X_train))
        batch = X_train[perm[:max(len(X_train) // 2, 16)]]
        opt.zero_grad()
        recon, _ = model(batch)
        loss = F.mse_loss(recon, batch)
        loss.backward()
        opt.step()
    return model


# ─── Scoring ─────────────────────────────────────────────────────────

def score_recon(model, X):
    """Reconstruction error per sample."""
    model.eval()
    with torch.no_grad():
        recon, _ = model(X)
        err = ((recon - X) ** 2).mean(dim=-1)
    return err.numpy()


def score_inter_tension(child_a, child_b, X):
    """Inter-child tension: disagreement between split models."""
    child_a.eval()
    child_b.eval()
    with torch.no_grad():
        recon_a, _ = child_a(X)
        recon_b, _ = child_b(X)
        tension = ((recon_a - recon_b) ** 2).mean(dim=-1)
    return tension.numpy()


def score_isolation_forest(X_train_np, X_test_np):
    """Isolation Forest anomaly scores."""
    iso = IsolationForest(n_estimators=100, contamination=0.15, random_state=42)
    iso.fit(X_train_np)
    # decision_function: lower = more anomalous, negate for AUROC
    scores = -iso.decision_function(X_test_np)
    return scores


# ─── Main Experiment ─────────────────────────────────────────────────

def run_experiment(dataset_name, normals, anomalies, window_size=10, n_trials=3):
    """Run full comparison on one dataset."""
    print(f"\n{'=' * 70}")
    print(f"  Dataset: {dataset_name}")
    print(f"  Normal: {len(normals)} series, Anomaly: {len(anomalies)} series")
    print(f"  Series length: {normals.shape[1]}, Window size: {window_size}")
    print(f"{'=' * 70}")

    input_dim = window_size

    results = {
        'inter_tension': [],
        'recon_error': [],
        'combined': [],
        'isolation_forest': [],
    }

    for trial in range(n_trials):
        seed = trial * 100 + 42
        torch.manual_seed(seed)
        np.random.seed(seed)

        # Split normal into train/test
        n_train = int(0.7 * len(normals))
        perm = np.random.permutation(len(normals))
        train_normal = normals[perm[:n_train]]
        test_normal = normals[perm[n_train:]]

        # Build sliding window features
        X_train_win, _ = sliding_window_features(train_normal, window_size)

        test_all = np.vstack([test_normal, anomalies])
        y_labels = np.array([0] * len(test_normal) + [1] * len(anomalies))

        X_test_win, test_win_idx = sliding_window_features(test_all, window_size)
        n_test_series = len(test_all)

        X_train_t = torch.FloatTensor(X_train_win)
        X_test_t = torch.FloatTensor(X_test_win)

        # ── Method 1: Mitosis Inter-Tension ──
        parent = SimpleAE(input_dim, hidden_dim=32, latent_dim=8)
        parent = train_ae(parent, X_train_t, epochs=50)

        child_a, child_b = mitosis(parent, scale=0.01)

        # Train children independently on different subsets
        perm_train = torch.randperm(len(X_train_t))
        half = len(perm_train) // 2
        child_a = train_child(child_a, X_train_t[perm_train[:half]], epochs=30)
        child_b = train_child(child_b, X_train_t[perm_train[half:]], epochs=30)

        win_inter = score_inter_tension(child_a, child_b, X_test_t)
        series_inter = series_level_score(win_inter, test_win_idx, n_test_series)

        # ── Method 2: Simple Reconstruction Error ──
        win_recon = score_recon(parent, X_test_t)
        series_recon = series_level_score(win_recon, test_win_idx, n_test_series)

        # ── Method 3: Isolation Forest ──
        iso_scores = score_isolation_forest(X_train_win, X_test_win)
        series_iso = series_level_score(iso_scores, test_win_idx, n_test_series)

        # ── Combined: recon + inter-tension (normalized) ──
        # Normalize both to [0,1] then average
        def normalize(x):
            mn, mx = x.min(), x.max()
            if mx - mn < 1e-10:
                return np.zeros_like(x)
            return (x - mn) / (mx - mn)

        series_combined = normalize(series_recon) + normalize(series_inter)

        # ── AUROC ──
        auroc_inter = roc_auc_score(y_labels, series_inter)
        auroc_recon = roc_auc_score(y_labels, series_recon)
        auroc_combined = roc_auc_score(y_labels, series_combined)
        auroc_iso = roc_auc_score(y_labels, series_iso)

        results['inter_tension'].append(auroc_inter)
        results['recon_error'].append(auroc_recon)
        results['combined'].append(auroc_combined)
        results['isolation_forest'].append(auroc_iso)

        print(f"\n  Trial {trial + 1}:")
        print(f"    Inter-tension:    AUROC = {auroc_inter:.4f}")
        print(f"    Recon error:      AUROC = {auroc_recon:.4f}")
        print(f"    Combined:         AUROC = {auroc_combined:.4f}")
        print(f"    Isolation Forest: AUROC = {auroc_iso:.4f}")

    # ── Summary ──
    print(f"\n  {'─' * 55}")
    print(f"  Summary ({n_trials} trials):")
    print(f"  {'Method':>20} {'Mean AUROC':>12} {'Std':>8} {'Min':>8} {'Max':>8}")
    print(f"  {'─' * 55}")
    for method, vals in results.items():
        m, s = np.mean(vals), np.std(vals)
        print(f"  {method:>20} {m:>12.4f} {s:>8.4f} {min(vals):>8.4f} {max(vals):>8.4f}")

    # ASCII bar chart
    print(f"\n  AUROC Comparison:")
    for method, vals in results.items():
        m = np.mean(vals)
        bar_len = int(m * 50)
        bar = '#' * bar_len
        print(f"    {method:>20} |{bar:<50}| {m:.4f}")

    # Winner
    means = {k: np.mean(v) for k, v in results.items()}
    winner = max(means, key=means.get)
    print(f"\n  Winner: {winner} (AUROC = {means[winner]:.4f})")

    # Inter-tension vs others
    delta_recon = means['inter_tension'] - means['recon_error']
    delta_iso = means['inter_tension'] - means['isolation_forest']
    print(f"  Inter-tension vs Recon:     {delta_recon:+.4f}")
    print(f"  Inter-tension vs IsoForest: {delta_iso:+.4f}")

    return results


def main():
    print("=" * 70)
    print("  TIME SERIES MITOSIS ANOMALY DETECTION")
    print("  Mitosis inter-tension vs Reconstruction vs Isolation Forest")
    print("=" * 70)

    all_results = {}

    # ── Dataset 1: Sine waves ──
    normals_sine, anomalies_sine = generate_sine_data(
        n_normal=100, n_anomaly=20, length=50, seed=42
    )
    r1 = run_experiment("Sine Wave", normals_sine, anomalies_sine,
                        window_size=10, n_trials=3)
    all_results['sine'] = r1

    # ── Dataset 2: ECG-like ──
    normals_ecg, anomalies_ecg = generate_ecg_data(
        n_normal=100, n_anomaly=20, length=50, seed=42
    )
    r2 = run_experiment("ECG-like", normals_ecg, anomalies_ecg,
                        window_size=10, n_trials=3)
    all_results['ecg'] = r2

    # ── Grand Summary ──
    print(f"\n{'=' * 70}")
    print(f"  GRAND SUMMARY")
    print(f"{'=' * 70}")
    print(f"\n  {'Dataset':>12} {'Method':>20} {'AUROC':>8}")
    print(f"  {'─' * 45}")
    for ds_name, ds_results in all_results.items():
        for method, vals in ds_results.items():
            print(f"  {ds_name:>12} {method:>20} {np.mean(vals):>8.4f}")
        print(f"  {'─' * 45}")

    # Cross-dataset summary for inter-tension
    print(f"\n  Inter-tension AUROC across datasets:")
    for ds_name, ds_results in all_results.items():
        m = np.mean(ds_results['inter_tension'])
        s = np.std(ds_results['inter_tension'])
        bar = '#' * int(m * 50)
        print(f"    {ds_name:>8} |{bar:<50}| {m:.4f} +/- {s:.4f}")

    # Overall verdict
    sine_winner = max(all_results['sine'], key=lambda k: np.mean(all_results['sine'][k]))
    ecg_winner = max(all_results['ecg'], key=lambda k: np.mean(all_results['ecg'][k]))

    print(f"\n  Per-dataset winners:")
    print(f"    Sine: {sine_winner} ({np.mean(all_results['sine'][sine_winner]):.4f})")
    print(f"    ECG:  {ecg_winner} ({np.mean(all_results['ecg'][ecg_winner]):.4f})")

    inter_wins = sum(1 for ds in all_results.values()
                     if np.mean(ds['inter_tension']) == max(np.mean(v) for v in ds.values()))
    print(f"\n  Inter-tension wins: {inter_wins}/{len(all_results)} datasets")

    if inter_wins == len(all_results):
        print("  --> Mitosis inter-tension dominates on ALL time series datasets!")
    elif inter_wins > 0:
        print("  --> Mitosis inter-tension wins on some datasets (domain-dependent)")
    else:
        print("  --> Mitosis inter-tension does NOT outperform baselines on time series")

    print(f"\nDone.")


if __name__ == '__main__':
    main()
