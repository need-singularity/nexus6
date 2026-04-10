#!/usr/bin/env python3
"""Hypothesis 281: Tension as Leading Indicator of Learning

Tests whether per-class tension at epoch t predicts accuracy at epoch t+1.
Records per-digit tension and accuracy every epoch, then computes:
  1. Lag-1 cross-correlation: tension(t) vs accuracy(t+1)
  2. Lag-1 cross-correlation: accuracy(t) vs tension(t+1)
  3. Granger-like analysis: does delta-tension predict delta-accuracy?
"""

import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from scipy import stats
from model_utils import load_mnist
from model_meta_engine import RepulsionFieldEngine

# ─────────────────────────────────────────
# Per-class tension tracker
# ─────────────────────────────────────────
def compute_per_class_tension(model, loader):
    """Compute mean tension per digit class (0-9)."""
    model.eval()
    tension_sums = torch.zeros(10)
    tension_counts = torch.zeros(10)
    correct = torch.zeros(10)
    total = torch.zeros(10)

    with torch.no_grad():
        for X, y in loader:
            X_flat = X.view(X.size(0), -1)

            # Forward through poles to get tension
            out_plus = model.pole_plus(X_flat)
            out_minus = model.pole_minus(X_flat)
            repulsion = out_plus - out_minus
            tension = (repulsion ** 2).sum(dim=-1)  # per-sample tension

            # Full forward for predictions
            output, _ = model(X_flat)
            preds = output.argmax(dim=-1)

            for c in range(10):
                mask = (y == c)
                if mask.sum() > 0:
                    tension_sums[c] += tension[mask].sum().item()
                    tension_counts[c] += mask.sum().item()
                    correct[c] += (preds[mask] == y[mask]).sum().item()
                    total[c] += mask.sum().item()

    per_class_tension = tension_sums / (tension_counts + 1e-8)
    per_class_accuracy = correct / (total + 1e-8)
    return per_class_tension.numpy(), per_class_accuracy.numpy()


def train_one_epoch(model, train_loader, optimizer, criterion, aux_lambda=0.1):
    """Train for one epoch, return average loss."""
    model.train()
    total_loss = 0
    for X, y in train_loader:
        X_flat = X.view(X.size(0), -1)
        optimizer.zero_grad()
        output, aux = model(X_flat)
        loss = criterion(output, y) + aux_lambda * aux
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(train_loader)


def cross_correlation_lag1(x_series, y_series):
    """Compute correlation between x(t) and y(t+1) across all classes.

    x_series: (n_epochs, 10)
    y_series: (n_epochs, 10)
    Returns: per-class correlations and mean.
    """
    n_epochs = x_series.shape[0]
    if n_epochs < 3:
        return np.zeros(10), 0.0, 1.0

    correlations = []
    for c in range(10):
        x = x_series[:-1, c]  # t = 0..T-2
        y = y_series[1:, c]   # t = 1..T-1
        if np.std(x) < 1e-10 or np.std(y) < 1e-10:
            correlations.append(0.0)
        else:
            r, _ = stats.pearsonr(x, y)
            correlations.append(r)

    correlations = np.array(correlations)
    mean_r = np.nanmean(correlations)
    # Fisher z-test for mean correlation
    z_values = np.arctanh(np.clip(correlations, -0.999, 0.999))
    z_mean = np.mean(z_values)
    z_se = np.std(z_values) / np.sqrt(len(z_values))
    p_value = 2 * (1 - stats.norm.cdf(abs(z_mean / (z_se + 1e-10))))
    return correlations, mean_r, p_value


def granger_like_test(tension_series, accuracy_series):
    """Test: does delta-tension(t) predict delta-accuracy(t+1)?

    Simple regression: delta_acc(t+1) = a + b * delta_tension(t) + e
    vs null:           delta_acc(t+1) = a + e
    """
    n_epochs = tension_series.shape[0]
    if n_epochs < 4:
        return {}, 1.0

    results = {}
    f_stats = []
    p_values = []

    for c in range(10):
        dt = np.diff(tension_series[:, c])   # delta tension: T-1 values
        da = np.diff(accuracy_series[:, c])  # delta accuracy: T-1 values

        # lag-1: dt(0..T-3) predicts da(1..T-2)
        x = dt[:-1]
        y = da[1:]

        if len(x) < 3 or np.std(x) < 1e-10:
            results[c] = {'slope': 0, 'r': 0, 'p': 1.0}
            continue

        slope, intercept, r, p, se = stats.linregress(x, y)
        results[c] = {'slope': slope, 'r': r, 'p': p}
        if not np.isnan(p):
            p_values.append(p)

    mean_p = np.mean(p_values) if p_values else 1.0
    return results, mean_p


# ─────────────────────────────────────────
# Main experiment
# ─────────────────────────────────────────
def main():
    print("=" * 70)
    print("H-281: Tension as Leading Indicator of Learning")
    print("=" * 70)

    # 3 independent runs for robustness
    N_RUNS = 3
    N_EPOCHS = 20

    all_runs_tension_acc = []  # (tension->acc correlations per run)
    all_runs_acc_tension = []  # (acc->tension correlations per run)
    all_runs_granger = []

    for run in range(N_RUNS):
        print(f"\n{'─' * 50}")
        print(f"Run {run+1}/{N_RUNS}")
        print(f"{'─' * 50}")

        torch.manual_seed(42 + run)
        np.random.seed(42 + run)

        train_loader, test_loader = load_mnist(batch_size=128)
        model = RepulsionFieldEngine(input_dim=784, hidden_dim=48, output_dim=10)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()

        tension_history = []  # (n_epochs, 10)
        accuracy_history = []  # (n_epochs, 10)

        for epoch in range(N_EPOCHS):
            loss = train_one_epoch(model, train_loader, optimizer, criterion)
            t, a = compute_per_class_tension(model, test_loader)
            tension_history.append(t)
            accuracy_history.append(a)

            if epoch % 5 == 0 or epoch == N_EPOCHS - 1:
                print(f"  Epoch {epoch:2d}: loss={loss:.4f}  "
                      f"mean_tension={t.mean():.4f}  mean_acc={a.mean():.4f}")

        tension_arr = np.array(tension_history)
        accuracy_arr = np.array(accuracy_history)

        # Analysis 1: tension(t) -> accuracy(t+1)
        corr_ta, mean_ta, p_ta = cross_correlation_lag1(tension_arr, accuracy_arr)
        # Analysis 2: accuracy(t) -> tension(t+1)
        corr_at, mean_at, p_at = cross_correlation_lag1(accuracy_arr, tension_arr)
        # Analysis 3: Granger-like
        granger, granger_p = granger_like_test(tension_arr, accuracy_arr)

        all_runs_tension_acc.append((corr_ta, mean_ta, p_ta))
        all_runs_acc_tension.append((corr_at, mean_at, p_at))
        all_runs_granger.append((granger, granger_p))

        print(f"\n  Cross-correlations (lag-1):")
        print(f"    tension(t)->acc(t+1):  mean r = {mean_ta:.4f}  p = {p_ta:.4f}")
        print(f"    acc(t)->tension(t+1):  mean r = {mean_at:.4f}  p = {p_at:.4f}")

    # ─────────────────────────────────────────
    # Summary across runs
    # ─────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SUMMARY ACROSS RUNS")
    print("=" * 70)

    # Per-class detail from last run
    print("\n--- Per-class lag-1 correlations (last run) ---")
    print(f"{'Digit':>6} | {'T->A(t+1)':>10} | {'A->T(t+1)':>10} | {'Granger slope':>14} | {'Granger p':>10}")
    print("-" * 60)
    last_corr_ta = all_runs_tension_acc[-1][0]
    last_corr_at = all_runs_acc_tension[-1][0]
    last_granger = all_runs_granger[-1][0]
    for c in range(10):
        g = last_granger.get(c, {'slope': 0, 'p': 1})
        print(f"  {c:>4} | {last_corr_ta[c]:>10.4f} | {last_corr_at[c]:>10.4f} | "
              f"{g['slope']:>14.6f} | {g['p']:>10.4f}")

    print(f"\n--- Aggregated across {N_RUNS} runs ---")
    mean_ta_all = np.mean([r[1] for r in all_runs_tension_acc])
    mean_at_all = np.mean([r[1] for r in all_runs_acc_tension])
    std_ta = np.std([r[1] for r in all_runs_tension_acc])
    std_at = np.std([r[1] for r in all_runs_acc_tension])

    print(f"  tension(t)->acc(t+1):   mean r = {mean_ta_all:.4f} +/- {std_ta:.4f}")
    print(f"  acc(t)->tension(t+1):   mean r = {mean_at_all:.4f} +/- {std_at:.4f}")

    asymmetry = abs(mean_ta_all) - abs(mean_at_all)
    print(f"\n  Asymmetry (|T->A| - |A->T|) = {asymmetry:.4f}")
    if asymmetry > 0.05:
        print("  >>> TENSION LEADS ACCURACY (H-281 supported)")
    elif asymmetry < -0.05:
        print("  >>> ACCURACY LEADS TENSION (H-281 contradicted)")
    else:
        print("  >>> SYMMETRIC / INCONCLUSIVE")

    # Granger summary
    granger_slopes = []
    granger_ps = []
    for run_g, run_p in all_runs_granger:
        for c in range(10):
            g = run_g.get(c, {'slope': 0, 'p': 1})
            granger_slopes.append(g['slope'])
            if g['p'] < 1.0:
                granger_ps.append(g['p'])

    mean_slope = np.mean(granger_slopes)
    sig_count = sum(1 for p in granger_ps if p < 0.05)
    print(f"\n  Granger-like test:")
    print(f"    Mean slope (delta_T -> delta_A): {mean_slope:.6f}")
    print(f"    Significant classes (p<0.05): {sig_count}/{len(granger_ps)}")

    # ─────────────────────────────────────────
    # ASCII visualization: tension and accuracy trajectories for digit 0 and 1
    # ─────────────────────────────────────────
    print("\n--- Tension & Accuracy trajectories (last run, digits 0,1) ---")
    tension_arr = np.array(tension_history)
    accuracy_arr = np.array(accuracy_history)

    for digit in [0, 1, 4, 9]:
        t_vals = tension_arr[:, digit]
        a_vals = accuracy_arr[:, digit]

        # Normalize for ASCII display
        t_min, t_max = t_vals.min(), t_vals.max()
        a_min, a_max = a_vals.min(), a_vals.max()

        width = 40
        print(f"\n  Digit {digit} - Tension (T) vs Accuracy (A):")
        print(f"  {'Epoch':>5} | {'Tension bar':^20} | {'Accuracy bar':^20} | T_val    | A_val")
        for ep in range(N_EPOCHS):
            t_norm = (t_vals[ep] - t_min) / (t_max - t_min + 1e-10)
            a_norm = (a_vals[ep] - a_min) / (a_max - a_min + 1e-10)
            t_bar = '#' * int(t_norm * 20)
            a_bar = '*' * int(a_norm * 20)
            print(f"  {ep:>5} | {t_bar:<20} | {a_bar:<20} | {t_vals[ep]:.4f} | {a_vals[ep]:.4f}")

    # ─────────────────────────────────────────
    # Final verdict
    # ─────────────────────────────────────────
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)

    if asymmetry > 0.05 and sig_count >= 5:
        verdict = "SUPPORTED"
        grade = "green"
        print("  H-281: SUPPORTED")
        print("  Tension is a leading indicator of accuracy.")
        print(f"  Grade: green (T->A stronger by {asymmetry:.4f}, {sig_count}/30 Granger significant)")
    elif asymmetry > 0.02:
        verdict = "WEAKLY SUPPORTED"
        grade = "orange"
        print("  H-281: WEAKLY SUPPORTED")
        print(f"  Slight asymmetry ({asymmetry:.4f}) but not conclusive.")
        print(f"  Grade: orange")
    elif asymmetry < -0.05:
        verdict = "CONTRADICTED"
        grade = "red"
        print("  H-281: CONTRADICTED")
        print("  Accuracy leads tension, not the other way around.")
    else:
        verdict = "INCONCLUSIVE"
        grade = "yellow"
        print("  H-281: INCONCLUSIVE")
        print("  No clear leading/lagging relationship.")

    print("=" * 70)

    # Return data for doc generation
    return {
        'mean_ta': mean_ta_all, 'std_ta': std_ta,
        'mean_at': mean_at_all, 'std_at': std_at,
        'asymmetry': asymmetry,
        'granger_sig': sig_count, 'granger_total': len(granger_ps),
        'verdict': verdict, 'grade': grade,
    }


if __name__ == '__main__':
    main()
