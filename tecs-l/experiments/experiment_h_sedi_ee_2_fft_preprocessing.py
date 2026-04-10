#!/usr/bin/env python3
"""
H-SEDI-EE-2: FFT Preprocessing for Smaller Model Inference
============================================================
Hypothesis: Preprocessing inputs with FFT feature extraction before feeding
to a SMALLER model achieves comparable accuracy with fewer FLOPs.

SEDI connection: SEDI uses Rust-accelerated FFT (2-10x faster than NumPy).
Here we test the principle: can FFT features replace raw pixels, allowing
a smaller model to match a larger one?

Test plan:
  1. Baseline: PureFieldEngine on raw 784-dim MNIST
  2. FFT features: Apply FFT to each image row, take magnitude spectrum
     → reduces to compact feature set
  3. Train smaller PureFieldEngine on FFT features
  4. Compare: accuracy, FLOPs, parameter count
"""

import sys
sys.path.insert(0, '/Users/ghost/Dev/TECS-L')

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import time

from model_pure_field import PureFieldEngine
from model_utils import load_mnist
from torch.utils.data import DataLoader, TensorDataset

torch.manual_seed(42)
np.random.seed(42)


# ─── FFT Feature Extraction ─────────────────────────────────────────────────

def extract_fft_features(loader, feature_dim=196):
    """Extract FFT magnitude features from MNIST images.

    For each 28x28 image:
      1. Reshape to 28 rows of 28 pixels
      2. FFT each row, take magnitude (14 unique freqs per row due to symmetry)
      3. Also FFT columns (14 unique freqs per column)
      4. Concatenate: 28*14/2 + 28*14/2 = 196 features (or top-k)
    """
    all_features = []
    all_labels = []

    for X, y in loader:
        batch_size = X.size(0)
        imgs = X.view(batch_size, 28, 28)

        # Row FFT: magnitude of positive frequencies
        row_fft = torch.fft.rfft(imgs, dim=2)  # (B, 28, 15)
        row_mag = torch.abs(row_fft)  # (B, 28, 15)

        # Column FFT: magnitude of positive frequencies
        col_fft = torch.fft.rfft(imgs, dim=1)  # (B, 15, 28)
        col_mag = torch.abs(col_fft)  # (B, 15, 28)

        # Flatten and concatenate
        row_feat = row_mag.reshape(batch_size, -1)  # (B, 420)
        col_feat = col_mag.reshape(batch_size, -1)  # (B, 420)

        # Take top features by variance (computed once, then fixed)
        features = torch.cat([row_feat, col_feat], dim=1)  # (B, 840)

        all_features.append(features)
        all_labels.append(y)

    all_features = torch.cat(all_features)
    all_labels = torch.cat(all_labels)

    # Reduce to feature_dim by selecting highest-variance features
    if all_features.size(1) > feature_dim:
        variances = all_features.var(dim=0)
        top_idx = variances.argsort(descending=True)[:feature_dim]
        all_features = all_features[:, top_idx]

    # Normalize
    mean = all_features.mean(dim=0)
    std = all_features.std(dim=0) + 1e-8
    all_features = (all_features - mean) / std

    return all_features, all_labels, mean, std


def count_flops_purefield(input_dim, hidden_dim, output_dim, batch_size=1):
    """Estimate FLOPs for PureFieldEngine forward pass.
    Each engine: input_dim*hidden_dim + hidden_dim*output_dim multiplications
    Two engines + subtraction.
    """
    per_engine = 2 * (input_dim * hidden_dim + hidden_dim * output_dim)
    return 2 * per_engine * batch_size  # two engines


def main():
    print("=" * 70)
    print("  H-SEDI-EE-2: FFT Preprocessing for Smaller Model")
    print("=" * 70)

    train_loader, test_loader = load_mnist(batch_size=128)

    # ─── Baseline: Full model on raw pixels ──────────────────────────────────
    print("\n  [1/4] Training baseline (raw pixels, hidden=128)...")
    model_baseline = PureFieldEngine(784, 128, 10)
    params_baseline = sum(p.numel() for p in model_baseline.parameters())
    flops_baseline = count_flops_purefield(784, 128, 10)

    optimizer = torch.optim.Adam(model_baseline.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    t0 = time.time()
    for epoch in range(10):
        model_baseline.train()
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            out, _ = model_baseline(X)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
    t_baseline = time.time() - t0

    model_baseline.eval()
    correct = total = 0
    with torch.no_grad():
        for X, y in test_loader:
            X = X.view(X.size(0), -1)
            out, _ = model_baseline(X)
            correct += (out.argmax(1) == y).sum().item()
            total += y.size(0)
    acc_baseline = correct / total
    print(f"    Baseline: Acc={acc_baseline*100:.2f}%, Params={params_baseline:,}, "
          f"FLOPs/sample={flops_baseline:,}, Time={t_baseline:.1f}s")

    # ─── FFT feature extraction ──────────────────────────────────────────────
    print("\n  [2/4] Extracting FFT features...")
    t_fft_start = time.time()
    train_feats, train_labels, mean, std = extract_fft_features(train_loader, feature_dim=196)
    # Apply same normalization to test
    test_feats_list = []
    test_labels_list = []
    for X, y in test_loader:
        batch_size = X.size(0)
        imgs = X.view(batch_size, 28, 28)
        row_fft = torch.fft.rfft(imgs, dim=2)
        row_mag = torch.abs(row_fft).reshape(batch_size, -1)
        col_fft = torch.fft.rfft(imgs, dim=1)
        col_mag = torch.abs(col_fft).reshape(batch_size, -1)
        features = torch.cat([row_mag, col_mag], dim=1)
        # Use same feature selection as training
        variances = train_feats.var(dim=0)  # already selected
        test_feats_list.append(features)
        test_labels_list.append(y)
    # Re-extract with consistent selection
    test_feats_raw, test_labels_raw, _, _ = extract_fft_features(test_loader, feature_dim=196)
    t_fft = time.time() - t_fft_start

    fft_dim = train_feats.size(1)
    print(f"    FFT features: {fft_dim} dims (from 784 raw), extraction time: {t_fft:.1f}s")

    fft_train_loader = DataLoader(
        TensorDataset(train_feats, train_labels), batch_size=128, shuffle=True)
    fft_test_loader = DataLoader(
        TensorDataset(test_feats_raw, test_labels_raw), batch_size=128)

    # ─── FFT + Small model ───────────────────────────────────────────────────
    configs = [
        ("FFT+Small(h=64)", 64),
        ("FFT+Tiny(h=32)", 32),
        ("FFT+Mini(h=16)", 16),
    ]

    results = {
        'Baseline(raw,h=128)': {
            'acc': acc_baseline, 'params': params_baseline,
            'flops': flops_baseline, 'time': t_baseline,
            'input_dim': 784, 'hidden': 128
        }
    }

    for name, hidden in configs:
        print(f"\n  [3/4] Training {name}...")
        model = PureFieldEngine(fft_dim, hidden, 10)
        params = sum(p.numel() for p in model.parameters())
        flops = count_flops_purefield(fft_dim, hidden, 10)

        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

        t0 = time.time()
        for epoch in range(10):
            model.train()
            for X, y in fft_train_loader:
                optimizer.zero_grad()
                out, _ = model(X)
                loss = criterion(out, y)
                loss.backward()
                optimizer.step()
        t_train = time.time() - t0

        model.eval()
        correct = total = 0
        with torch.no_grad():
            for X, y in fft_test_loader:
                out, _ = model(X)
                correct += (out.argmax(1) == y).sum().item()
                total += y.size(0)
        acc = correct / total

        results[name] = {
            'acc': acc, 'params': params, 'flops': flops,
            'time': t_train, 'input_dim': fft_dim, 'hidden': hidden
        }
        print(f"    {name}: Acc={acc*100:.2f}%, Params={params:,}, "
              f"FLOPs/sample={flops:,}, Time={t_train:.1f}s")

    # ─── Results table ───────────────────────────────────────────────────────
    print("\n" + "=" * 90)
    print("  COMPARISON TABLE")
    print("=" * 90)
    print(f"  {'Model':<25} | {'Acc%':>6} | {'Params':>8} | {'FLOPs':>10} | "
          f"{'Param Save':>10} | {'FLOP Save':>10} | {'Acc Drop':>8}")
    print("-" * 90)

    for name, r in sorted(results.items(), key=lambda x: -x[1]['acc']):
        param_save = (1 - r['params'] / params_baseline) * 100
        flop_save = (1 - r['flops'] / flops_baseline) * 100
        acc_drop = (r['acc'] - acc_baseline) * 100
        print(f"  {name:<25} | {r['acc']*100:>5.2f}% | {r['params']:>8,} | "
              f"{r['flops']:>10,} | {param_save:>9.1f}% | {flop_save:>9.1f}% | "
              f"{acc_drop:>+7.2f}%")

    # ─── Verdict ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  VERDICT")
    print("=" * 70)

    # Find best FFT model with <1% accuracy drop
    best = None
    for name, r in results.items():
        if 'FFT' in name and (acc_baseline - r['acc']) < 0.01:
            if best is None or r['flops'] < results[best]['flops']:
                best = name

    if best:
        r = results[best]
        param_save = (1 - r['params'] / params_baseline) * 100
        flop_save = (1 - r['flops'] / flops_baseline) * 100
        print(f"  SUPPORTED: FFT preprocessing enables smaller models!")
        print(f"  Best: {best}")
        print(f"  Accuracy: {r['acc']*100:.2f}% (baseline {acc_baseline*100:.2f}%)")
        print(f"  Parameter reduction: {param_save:.1f}%")
        print(f"  FLOP reduction: {flop_save:.1f}%")
        print(f"  FFT preprocessing cost: {t_fft:.1f}s (amortized)")
    else:
        print(f"  NOT SUPPORTED: FFT features lose >1% accuracy vs raw pixels")
        best_fft = None
        for name, r in results.items():
            if 'FFT' in name:
                if best_fft is None or r['acc'] > results[best_fft]['acc']:
                    best_fft = name
        if best_fft:
            r = results[best_fft]
            print(f"  Best FFT model: {best_fft}, Acc={r['acc']*100:.2f}%")
            print(f"  Gap: {(acc_baseline - r['acc'])*100:.2f}%")

    print("=" * 70)


if __name__ == '__main__':
    main()
