#!/usr/bin/env python3
"""H-281: Tension Temporal Causation — Tension as Leading Indicator of Learning

Hypothesis: per-digit tension at epoch t predicts accuracy improvement at epoch t+1.
If tension is a leading indicator, lag-1 cross-correlation(tension, accuracy) should be
significantly higher than lag-0.

Method:
  1. Train RepulsionFieldQuad on MNIST for 15 epochs
  2. Each epoch: record per-digit mean tension AND per-digit accuracy (test set)
  3. Compute cross-correlation between tension(t) and accuracy(t+k) for k=0,1,2,3
  4. Report per-digit and overall results
"""

import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from collections import defaultdict

from model_meta_engine import RepulsionFieldQuad
from model_utils import load_mnist

# ─────────────────────────────────────────
# Config
# ─────────────────────────────────────────
EPOCHS = 15
LR = 0.001
BATCH_SIZE = 128
DEVICE = 'cpu'

def main():
    print("=" * 75)
    print("  H-281: Tension Temporal Causation Experiment")
    print("  Does tension(t) predict accuracy(t+1)?")
    print("=" * 75)

    # Load data
    train_loader, test_loader = load_mnist(batch_size=BATCH_SIZE, data_dir='/Users/ghost/Dev/logout/data')

    # Model
    model = RepulsionFieldQuad(input_dim=784, hidden_dim=48, output_dim=10)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.CrossEntropyLoss()

    n_params = sum(p.numel() for p in model.parameters())
    print(f"\n  Model: RepulsionFieldQuad | Params: {n_params:,}")
    print(f"  Epochs: {EPOCHS} | LR: {LR} | Batch: {BATCH_SIZE}")
    print()

    # Storage: [epoch][digit] = value
    tension_history = defaultdict(lambda: defaultdict(list))  # digit -> list of tensions per epoch
    accuracy_history = defaultdict(lambda: defaultdict(list))  # digit -> list of accuracies per epoch

    # Per-digit tension and accuracy arrays: shape (10, EPOCHS)
    digit_tensions = np.zeros((10, EPOCHS))
    digit_accuracies = np.zeros((10, EPOCHS))
    epoch_losses = []

    for epoch in range(EPOCHS):
        # ─── Train ───
        model.train()
        total_loss = 0
        n_batches = 0
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            out, aux_loss = model(X)
            loss = criterion(out, y) + 0.1 * aux_loss
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            n_batches += 1
        avg_loss = total_loss / n_batches
        epoch_losses.append(avg_loss)

        # ─── Evaluate: per-digit tension and accuracy ───
        model.eval()
        digit_tension_accum = defaultdict(list)
        digit_correct = defaultdict(int)
        digit_total = defaultdict(int)

        with torch.no_grad():
            for X, y in test_loader:
                X_flat = X.view(X.size(0), -1)
                out, _ = model(X_flat)
                preds = out.argmax(dim=1)

                # Per-sample tension (use total_tension proxy from content + structure)
                # Re-run forward to capture per-sample tension
                out_a = model.engine_a(X_flat)
                out_e = model.engine_e(X_flat)
                out_g = model.engine_g(X_flat)
                out_f = model.engine_f(X_flat)

                repulsion_content = out_a - out_g
                repulsion_structure = out_e - out_f
                t_content = (repulsion_content ** 2).sum(dim=-1)
                t_structure = (repulsion_structure ** 2).sum(dim=-1)
                total_tension = torch.sqrt(t_content * t_structure + 1e-8)

                for i in range(len(y)):
                    d = y[i].item()
                    digit_tension_accum[d].append(total_tension[i].item())
                    digit_correct[d] += (preds[i] == y[i]).item()
                    digit_total[d] += 1

        for d in range(10):
            t_mean = np.mean(digit_tension_accum[d]) if digit_tension_accum[d] else 0
            acc = digit_correct[d] / digit_total[d] if digit_total[d] > 0 else 0
            digit_tensions[d, epoch] = t_mean
            digit_accuracies[d, epoch] = acc

        overall_acc = sum(digit_correct.values()) / sum(digit_total.values())
        print(f"  Epoch {epoch+1:>2}/{EPOCHS}: Loss={avg_loss:.4f}  Acc={overall_acc*100:.1f}%  "
              f"T_content={model.tension_content:.4f}  T_struct={model.tension_structure:.4f}")

    # ─────────────────────────────────────────
    # Analysis: Cross-correlation with lags
    # ─────────────────────────────────────────
    print("\n" + "=" * 75)
    print("  RESULTS")
    print("=" * 75)

    # Print tension trajectory
    print("\n  Per-digit Mean Tension (epochs 1-15):")
    print("  " + "-" * 71)
    header = "  Digit |" + "".join(f" E{e+1:>2}" for e in range(EPOCHS)) + " |"
    print(header)
    print("  " + "-" * 71)
    for d in range(10):
        row = f"    {d}   |"
        for e in range(EPOCHS):
            row += f" {digit_tensions[d, e]:>4.1f}"
        row += " |"
        print(row)
    print("  " + "-" * 71)

    # Print accuracy trajectory
    print("\n  Per-digit Accuracy % (epochs 1-15):")
    print("  " + "-" * 71)
    header = "  Digit |" + "".join(f" E{e+1:>2}" for e in range(EPOCHS)) + " |"
    print(header)
    print("  " + "-" * 71)
    for d in range(10):
        row = f"    {d}   |"
        for e in range(EPOCHS):
            row += f" {digit_accuracies[d, e]*100:>4.1f}"
        row += " |"
        print(row)
    print("  " + "-" * 71)

    # Cross-correlation analysis
    print("\n  Cross-Correlation: tension(t) vs accuracy(t+lag)")
    print("  " + "-" * 55)
    print(f"  {'Digit':>5} | {'Lag-0':>7} | {'Lag-1':>7} | {'Lag-2':>7} | {'Lag-3':>7} | {'Best Lag':>8}")
    print("  " + "-" * 55)

    lag_results = {}
    for d in range(10):
        t_series = digit_tensions[d, :]
        a_series = digit_accuracies[d, :]

        correlations = {}
        for lag in range(4):
            if lag == 0:
                t_seg = t_series
                a_seg = a_series
            else:
                t_seg = t_series[:-lag]
                a_seg = a_series[lag:]

            if len(t_seg) < 3:
                correlations[lag] = 0.0
                continue

            # Pearson correlation
            t_std = np.std(t_seg)
            a_std = np.std(a_seg)
            if t_std < 1e-10 or a_std < 1e-10:
                correlations[lag] = 0.0
            else:
                correlations[lag] = np.corrcoef(t_seg, a_seg)[0, 1]

        best_lag = max(correlations, key=lambda k: abs(correlations[k]))
        lag_results[d] = correlations

        print(f"    {d:>3}   | {correlations[0]:>+7.4f} | {correlations[1]:>+7.4f} | "
              f"{correlations[2]:>+7.4f} | {correlations[3]:>+7.4f} | {best_lag:>5}")

    print("  " + "-" * 55)

    # Overall (mean across digits)
    mean_corrs = {}
    for lag in range(4):
        vals = [lag_results[d][lag] for d in range(10)]
        mean_corrs[lag] = np.mean(vals)

    best_overall = max(mean_corrs, key=lambda k: abs(mean_corrs[k]))
    print(f"  {'Mean':>5} | {mean_corrs[0]:>+7.4f} | {mean_corrs[1]:>+7.4f} | "
          f"{mean_corrs[2]:>+7.4f} | {mean_corrs[3]:>+7.4f} | {best_overall:>5}")
    print("  " + "-" * 55)

    # ─── Delta analysis: tension change vs accuracy change ───
    print("\n  Delta Analysis: delta_tension(t) vs delta_accuracy(t+lag)")
    print("  (Change in tension predicts change in accuracy?)")
    print("  " + "-" * 55)
    print(f"  {'Digit':>5} | {'Lag-0':>7} | {'Lag-1':>7} | {'Lag-2':>7} | {'Lag-3':>7} | {'Best Lag':>8}")
    print("  " + "-" * 55)

    delta_lag_results = {}
    for d in range(10):
        dt = np.diff(digit_tensions[d, :])   # length EPOCHS-1
        da = np.diff(digit_accuracies[d, :]) # length EPOCHS-1

        correlations = {}
        for lag in range(4):
            if lag == 0:
                dt_seg = dt
                da_seg = da
            else:
                dt_seg = dt[:-lag]
                da_seg = da[lag:]

            if len(dt_seg) < 3:
                correlations[lag] = 0.0
                continue

            dt_std = np.std(dt_seg)
            da_std = np.std(da_seg)
            if dt_std < 1e-10 or da_std < 1e-10:
                correlations[lag] = 0.0
            else:
                correlations[lag] = np.corrcoef(dt_seg, da_seg)[0, 1]

        best_lag = max(correlations, key=lambda k: abs(correlations[k]))
        delta_lag_results[d] = correlations

        print(f"    {d:>3}   | {correlations[0]:>+7.4f} | {correlations[1]:>+7.4f} | "
              f"{correlations[2]:>+7.4f} | {correlations[3]:>+7.4f} | {best_lag:>5}")

    print("  " + "-" * 55)

    # Delta overall
    delta_mean_corrs = {}
    for lag in range(4):
        vals = [delta_lag_results[d][lag] for d in range(10)]
        delta_mean_corrs[lag] = np.mean(vals)

    delta_best = max(delta_mean_corrs, key=lambda k: abs(delta_mean_corrs[k]))
    print(f"  {'Mean':>5} | {delta_mean_corrs[0]:>+7.4f} | {delta_mean_corrs[1]:>+7.4f} | "
          f"{delta_mean_corrs[2]:>+7.4f} | {delta_mean_corrs[3]:>+7.4f} | {delta_best:>5}")
    print("  " + "-" * 55)

    # ─── ASCII visualization: tension vs accuracy for selected digits ───
    print("\n  ASCII: Tension (T) and Accuracy (A) trajectories")
    print("  (Normalized to [0,1] range for comparison)")
    for d in [0, 3, 8]:  # sample digits
        t_norm = digit_tensions[d, :]
        a_norm = digit_accuracies[d, :]
        t_min, t_max = t_norm.min(), t_norm.max()
        a_min, a_max = a_norm.min(), a_norm.max()
        if t_max - t_min > 1e-10:
            t_norm = (t_norm - t_min) / (t_max - t_min)
        else:
            t_norm = np.zeros_like(t_norm)
        if a_max - a_min > 1e-10:
            a_norm = (a_norm - a_min) / (a_max - a_min)
        else:
            a_norm = np.ones_like(a_norm)

        print(f"\n  Digit {d} (T_range=[{t_min:.2f},{t_max:.2f}], A_range=[{a_min*100:.1f}%,{a_max*100:.1f}%]):")
        HEIGHT = 10
        for row in range(HEIGHT, -1, -1):
            level = row / HEIGHT
            line = f"  {level:>4.1f} |"
            for e in range(EPOCHS):
                t_here = abs(t_norm[e] - level) < 0.05 + 0.5/HEIGHT
                a_here = abs(a_norm[e] - level) < 0.05 + 0.5/HEIGHT
                if t_here and a_here:
                    line += " X"  # both
                elif t_here:
                    line += " T"
                elif a_here:
                    line += " A"
                else:
                    line += " ."
            line += " |"
            print(line)
        print(f"       +" + "--" * EPOCHS + "-+")
        print(f"        " + "".join(f"{e+1:>2}" for e in range(EPOCHS)))
        print(f"        T=tension  A=accuracy  X=both")

    # ─── Final verdict ───
    print("\n" + "=" * 75)
    print("  VERDICT: Is tension a leading indicator?")
    print("=" * 75)

    # Check if lag-1 has stronger correlation than lag-0 on average
    abs_lag0 = abs(mean_corrs[0])
    abs_lag1 = abs(mean_corrs[1])
    abs_lag0_delta = abs(delta_mean_corrs[0])
    abs_lag1_delta = abs(delta_mean_corrs[1])

    print(f"\n  Level Analysis (raw tension vs accuracy):")
    print(f"    |corr(lag=0)| = {abs_lag0:.4f}")
    print(f"    |corr(lag=1)| = {abs_lag1:.4f}")
    if abs_lag1 > abs_lag0:
        print(f"    --> Lag-1 > Lag-0: tension LEADS accuracy by ~1 epoch")
    else:
        print(f"    --> Lag-0 >= Lag-1: tension is CONCURRENT, not leading")

    print(f"\n  Delta Analysis (tension change vs accuracy change):")
    print(f"    |corr(lag=0)| = {abs_lag0_delta:.4f}")
    print(f"    |corr(lag=1)| = {abs_lag1_delta:.4f}")
    if abs_lag1_delta > abs_lag0_delta:
        print(f"    --> Delta lag-1 > lag-0: tension CHANGE leads accuracy CHANGE")
    else:
        print(f"    --> Delta lag-0 >= lag-1: concurrent changes, no lead")

    # Count how many digits show lag-1 > lag-0
    n_leading_level = sum(1 for d in range(10) if abs(lag_results[d][1]) > abs(lag_results[d][0]))
    n_leading_delta = sum(1 for d in range(10) if abs(delta_lag_results[d][1]) > abs(delta_lag_results[d][0]))
    print(f"\n  Digits where |lag-1| > |lag-0| (level): {n_leading_level}/10")
    print(f"  Digits where |lag-1| > |lag-0| (delta): {n_leading_delta}/10")

    if n_leading_level >= 7 or n_leading_delta >= 7:
        print("\n  CONCLUSION: STRONG evidence that tension is a leading indicator")
    elif n_leading_level >= 5 or n_leading_delta >= 5:
        print("\n  CONCLUSION: MODERATE evidence that tension is a leading indicator")
    else:
        print("\n  CONCLUSION: WEAK/NO evidence that tension is a leading indicator")

    # Sign analysis
    n_positive_lag1 = sum(1 for d in range(10) if lag_results[d][1] > 0)
    n_negative_lag1 = sum(1 for d in range(10) if lag_results[d][1] < 0)
    print(f"\n  Lag-1 sign: {n_positive_lag1} positive, {n_negative_lag1} negative")
    if n_positive_lag1 >= 7:
        print("  --> Higher tension predicts HIGHER accuracy (tension = constructive struggle)")
    elif n_negative_lag1 >= 7:
        print("  --> Higher tension predicts LOWER accuracy (tension = destructive conflict)")
    else:
        print("  --> Mixed signs: tension effect is digit-dependent")

    print("\n" + "=" * 75)
    print("  Experiment complete.")
    print("=" * 75)


if __name__ == '__main__':
    main()
