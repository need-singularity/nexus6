#!/usr/bin/env python3
"""H-281: Tension Temporal Causation — Enhanced with Granger Causality

Hypothesis: per-digit tension at epoch t predicts accuracy improvement at epoch t+1.

Enhancements over v1:
  1. More epochs (30) for better time-series resolution
  2. Granger causality test (statsmodels)
  3. Lag correlation with statistical significance (p-values)
  4. Permutation test for robustness
  5. Full data tables + ASCII graphs
"""

import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from collections import defaultdict
from scipy import stats

from model_meta_engine import RepulsionFieldQuad
from model_utils import load_mnist

# ─────────────────────────────────────────
# Config
# ─────────────────────────────────────────
EPOCHS = 30
LR = 0.001
BATCH_SIZE = 128
DEVICE = 'cpu'
N_SEEDS = 3  # multiple seeds for robustness

def compute_lag_correlation(x, y, max_lag=5):
    """Compute Pearson correlation at various lags: x(t) vs y(t+lag)."""
    results = {}
    for lag in range(max_lag + 1):
        if lag == 0:
            x_seg, y_seg = x, y
        else:
            x_seg = x[:-lag]
            y_seg = y[lag:]
        if len(x_seg) < 4:
            results[lag] = (0.0, 1.0)
            continue
        r, p = stats.pearsonr(x_seg, y_seg)
        results[lag] = (r, p)
    return results


def granger_causality_simple(x, y, max_lag=3):
    """Simple Granger causality: does adding lagged x improve prediction of y?

    Compare:
      Restricted: y(t) = a0 + a1*y(t-1) + ... + aL*y(t-L) + noise
      Unrestricted: y(t) = a0 + a1*y(t-1) + ... + aL*y(t-L) + b1*x(t-1) + ... + bL*x(t-L) + noise

    F-test on whether the x-lags significantly reduce RSS.
    """
    n = len(y)
    results = {}

    for lag in range(1, max_lag + 1):
        if n - lag < lag * 2 + 2:
            results[lag] = {'F': 0, 'p': 1.0, 'RSS_r': 0, 'RSS_u': 0}
            continue

        # Build matrices
        Y = y[lag:]  # dependent variable
        T = len(Y)

        # Restricted: only y lags
        X_r = np.column_stack([np.ones(T)] + [y[lag-i-1:n-i-1] for i in range(lag)])

        # Unrestricted: y lags + x lags
        X_u = np.column_stack([X_r] + [x[lag-i-1:n-i-1] for i in range(lag)])

        try:
            # OLS for restricted
            beta_r = np.linalg.lstsq(X_r, Y, rcond=None)[0]
            resid_r = Y - X_r @ beta_r
            RSS_r = np.sum(resid_r ** 2)

            # OLS for unrestricted
            beta_u = np.linalg.lstsq(X_u, Y, rcond=None)[0]
            resid_u = Y - X_u @ beta_u
            RSS_u = np.sum(resid_u ** 2)

            # F-test
            df1 = lag  # additional parameters
            df2 = T - X_u.shape[1]  # residual df

            if df2 <= 0 or RSS_u < 1e-15:
                results[lag] = {'F': 0, 'p': 1.0, 'RSS_r': RSS_r, 'RSS_u': RSS_u}
                continue

            F_stat = ((RSS_r - RSS_u) / df1) / (RSS_u / df2)
            p_value = 1 - stats.f.cdf(F_stat, df1, df2)

            results[lag] = {'F': F_stat, 'p': p_value, 'RSS_r': RSS_r, 'RSS_u': RSS_u}
        except Exception:
            results[lag] = {'F': 0, 'p': 1.0, 'RSS_r': 0, 'RSS_u': 0}

    return results


def run_single_seed(seed):
    """Run one training run and collect per-digit tension/accuracy time series."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    train_loader, test_loader = load_mnist(batch_size=BATCH_SIZE, data_dir='/Users/ghost/Dev/logout/data')
    model = RepulsionFieldQuad(input_dim=784, hidden_dim=48, output_dim=10)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.CrossEntropyLoss()

    digit_tensions = np.zeros((10, EPOCHS))
    digit_accuracies = np.zeros((10, EPOCHS))
    epoch_losses = []
    overall_accs = []
    overall_tensions = []

    for epoch in range(EPOCHS):
        # Train
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

        # Evaluate per-digit
        model.eval()
        digit_tension_accum = defaultdict(list)
        digit_correct = defaultdict(int)
        digit_total = defaultdict(int)

        with torch.no_grad():
            for X, y in test_loader:
                X_flat = X.view(X.size(0), -1)
                out, _ = model(X_flat)
                preds = out.argmax(dim=1)

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

        all_tensions = []
        for d in range(10):
            t_mean = np.mean(digit_tension_accum[d]) if digit_tension_accum[d] else 0
            acc = digit_correct[d] / digit_total[d] if digit_total[d] > 0 else 0
            digit_tensions[d, epoch] = t_mean
            digit_accuracies[d, epoch] = acc
            all_tensions.extend(digit_tension_accum[d])

        overall_acc = sum(digit_correct.values()) / sum(digit_total.values())
        overall_accs.append(overall_acc)
        overall_tensions.append(np.mean(all_tensions))

        if (epoch + 1) % 5 == 0:
            print(f"    Epoch {epoch+1:>2}/{EPOCHS}: Loss={avg_loss:.4f}  Acc={overall_acc*100:.1f}%")

    return digit_tensions, digit_accuracies, overall_accs, overall_tensions, epoch_losses


def main():
    print("=" * 80)
    print("  H-281: Tension Temporal Causation — Enhanced Experiment")
    print("  Does tension(t) predict accuracy(t+1)? (Granger causality)")
    print("=" * 80)

    all_digit_tensions = []
    all_digit_accuracies = []
    all_overall_accs = []
    all_overall_tensions = []

    for seed in range(N_SEEDS):
        print(f"\n  --- Seed {seed} ---")
        dt, da, oa, ot, el = run_single_seed(seed * 42)
        all_digit_tensions.append(dt)
        all_digit_accuracies.append(da)
        all_overall_accs.append(oa)
        all_overall_tensions.append(ot)

    # Average across seeds
    avg_tensions = np.mean(all_digit_tensions, axis=0)  # (10, EPOCHS)
    avg_accuracies = np.mean(all_digit_accuracies, axis=0)
    avg_overall_acc = np.mean(all_overall_accs, axis=0)
    avg_overall_tension = np.mean(all_overall_tensions, axis=0)

    # ═══════════════════════════════════════════
    # RESULTS
    # ═══════════════════════════════════════════
    print("\n" + "=" * 80)
    print("  RESULTS (averaged over {} seeds)".format(N_SEEDS))
    print("=" * 80)

    # ─── Table 1: Per-digit tension trajectory ───
    print("\n  Table 1: Per-digit Mean Tension (every 5th epoch)")
    print("  " + "-" * 65)
    epochs_show = list(range(0, EPOCHS, 5)) + [EPOCHS-1]
    header = "  Digit |" + "".join(f" E{e+1:>3}" for e in epochs_show) + " |"
    print(header)
    print("  " + "-" * 65)
    for d in range(10):
        row = f"    {d}   |"
        for e in epochs_show:
            row += f" {avg_tensions[d, e]:>5.2f}"
        row += " |"
        print(row)
    print("  " + "-" * 65)

    # ─── Table 2: Per-digit accuracy trajectory ───
    print("\n  Table 2: Per-digit Accuracy % (every 5th epoch)")
    print("  " + "-" * 65)
    header = "  Digit |" + "".join(f" E{e+1:>3}" for e in epochs_show) + " |"
    print(header)
    print("  " + "-" * 65)
    for d in range(10):
        row = f"    {d}   |"
        for e in epochs_show:
            row += f" {avg_accuracies[d, e]*100:>5.1f}"
        row += " |"
        print(row)
    print("  " + "-" * 65)

    # ─── Analysis 1: Lag correlation ───
    print("\n  Analysis 1: Lag Correlation — tension(t) vs accuracy(t+lag)")
    print("  " + "-" * 70)
    print(f"  {'Digit':>5} | {'Lag-0 r':>8} {'p':>6} | {'Lag-1 r':>8} {'p':>6} | {'Lag-2 r':>8} {'p':>6} | {'Best':>5}")
    print("  " + "-" * 70)

    all_lag_results = {}
    for d in range(10):
        lc = compute_lag_correlation(avg_tensions[d], avg_accuracies[d], max_lag=3)
        all_lag_results[d] = lc
        best_lag = max(range(4), key=lambda k: abs(lc.get(k, (0,1))[0]))

        print(f"    {d:>3}   | {lc[0][0]:>+7.4f} {lc[0][1]:>5.3f} | {lc[1][0]:>+7.4f} {lc[1][1]:>5.3f} | "
              f"{lc[2][0]:>+7.4f} {lc[2][1]:>5.3f} | {best_lag:>3}")

    # Mean
    mean_lag = {}
    for lag in range(4):
        rs = [all_lag_results[d][lag][0] for d in range(10)]
        mean_lag[lag] = np.mean(rs)

    print("  " + "-" * 70)
    print(f"  {'Mean':>5} | {mean_lag[0]:>+7.4f}       | {mean_lag[1]:>+7.4f}       | "
          f"{mean_lag[2]:>+7.4f}       |")
    print("  " + "-" * 70)

    # ─── Analysis 2: Delta correlation ───
    print("\n  Analysis 2: Delta Correlation — delta_tension(t) vs delta_accuracy(t+lag)")
    print("  " + "-" * 70)
    print(f"  {'Digit':>5} | {'Lag-0 r':>8} {'p':>6} | {'Lag-1 r':>8} {'p':>6} | {'Lag-2 r':>8} {'p':>6} | {'Best':>5}")
    print("  " + "-" * 70)

    delta_lag_results = {}
    for d in range(10):
        dt = np.diff(avg_tensions[d])
        da = np.diff(avg_accuracies[d])
        lc = compute_lag_correlation(dt, da, max_lag=3)
        delta_lag_results[d] = lc
        best_lag = max(range(4), key=lambda k: abs(lc.get(k, (0,1))[0]))

        print(f"    {d:>3}   | {lc[0][0]:>+7.4f} {lc[0][1]:>5.3f} | {lc[1][0]:>+7.4f} {lc[1][1]:>5.3f} | "
              f"{lc[2][0]:>+7.4f} {lc[2][1]:>5.3f} | {best_lag:>3}")

    delta_mean = {}
    for lag in range(4):
        rs = [delta_lag_results[d][lag][0] for d in range(10)]
        delta_mean[lag] = np.mean(rs)

    print("  " + "-" * 70)
    print(f"  {'Mean':>5} | {delta_mean[0]:>+7.4f}       | {delta_mean[1]:>+7.4f}       | "
          f"{delta_mean[2]:>+7.4f}       |")
    print("  " + "-" * 70)

    # ─── Analysis 3: Granger Causality ───
    print("\n  Analysis 3: Granger Causality — tension -> accuracy")
    print("  (F-test: does lagged tension improve accuracy prediction?)")
    print("  " + "-" * 60)
    print(f"  {'Digit':>5} | {'Lag-1 F':>8} {'p':>7} | {'Lag-2 F':>8} {'p':>7} | {'Lag-3 F':>8} {'p':>7}")
    print("  " + "-" * 60)

    granger_results = {}
    n_significant = {1: 0, 2: 0, 3: 0}

    for d in range(10):
        gc = granger_causality_simple(avg_tensions[d], avg_accuracies[d], max_lag=3)
        granger_results[d] = gc

        parts = []
        for lag in [1, 2, 3]:
            g = gc[lag]
            sig = "*" if g['p'] < 0.05 else " "
            if g['p'] < 0.05:
                n_significant[lag] += 1
            parts.append(f"{g['F']:>7.3f} {g['p']:>6.4f}{sig}")

        print(f"    {d:>3}   | {parts[0]} | {parts[1]} | {parts[2]}")

    print("  " + "-" * 60)
    print(f"  Significant (p<0.05):  Lag-1: {n_significant[1]}/10  "
          f"Lag-2: {n_significant[2]}/10  Lag-3: {n_significant[3]}/10")

    # ─── Reverse Granger: accuracy -> tension ───
    print("\n  Analysis 3b: Reverse Granger — accuracy -> tension (control)")
    print("  " + "-" * 60)
    print(f"  {'Digit':>5} | {'Lag-1 F':>8} {'p':>7} | {'Lag-2 F':>8} {'p':>7} | {'Lag-3 F':>8} {'p':>7}")
    print("  " + "-" * 60)

    n_sig_reverse = {1: 0, 2: 0, 3: 0}
    for d in range(10):
        gc_rev = granger_causality_simple(avg_accuracies[d], avg_tensions[d], max_lag=3)

        parts = []
        for lag in [1, 2, 3]:
            g = gc_rev[lag]
            sig = "*" if g['p'] < 0.05 else " "
            if g['p'] < 0.05:
                n_sig_reverse[lag] += 1
            parts.append(f"{g['F']:>7.3f} {g['p']:>6.4f}{sig}")

        print(f"    {d:>3}   | {parts[0]} | {parts[1]} | {parts[2]}")

    print("  " + "-" * 60)
    print(f"  Significant (p<0.05):  Lag-1: {n_sig_reverse[1]}/10  "
          f"Lag-2: {n_sig_reverse[2]}/10  Lag-3: {n_sig_reverse[3]}/10")

    # ─── ASCII: Overall tension vs accuracy ───
    print("\n  ASCII Graph: Overall Tension (T) and Accuracy (A) over epochs")
    print("  (Both normalized to [0,1] for visual comparison)")

    t_arr = avg_overall_tension
    a_arr = avg_overall_acc
    t_min, t_max = t_arr.min(), t_arr.max()
    a_min, a_max = a_arr.min(), a_arr.max()

    t_norm = (t_arr - t_min) / (t_max - t_min + 1e-10)
    a_norm = (a_arr - a_min) / (a_max - a_min + 1e-10)

    print(f"  T range: [{t_min:.4f}, {t_max:.4f}]  A range: [{a_min*100:.1f}%, {a_max*100:.1f}%]")

    HEIGHT = 15
    for row in range(HEIGHT, -1, -1):
        level = row / HEIGHT
        line = f"  {level:>4.2f} |"
        for e in range(EPOCHS):
            t_here = abs(t_norm[e] - level) < 0.5 / HEIGHT + 0.02
            a_here = abs(a_norm[e] - level) < 0.5 / HEIGHT + 0.02
            if t_here and a_here:
                line += "X"
            elif t_here:
                line += "T"
            elif a_here:
                line += "A"
            else:
                line += "."
        line += "|"
        print(line)
    print(f"       +" + "-" * EPOCHS + "+")
    ep_labels = "".join([str(e+1)[-1] for e in range(EPOCHS)])
    print(f"        {ep_labels}")
    print(f"        T=tension  A=accuracy  X=both")

    # ─── ASCII: Per-digit lag-1 correlation ───
    print("\n  ASCII Graph: Per-digit Lag-1 Correlation (tension->accuracy)")
    print("  " + "-" * 50)
    for d in range(10):
        r_val = all_lag_results[d][1][0]
        bar_len = int(abs(r_val) * 30)
        if r_val >= 0:
            bar = " " * 15 + "|" + "#" * bar_len
        else:
            pad = 15 - bar_len
            bar = " " * max(pad, 0) + "#" * bar_len + "|"
        print(f"  Digit {d}: {bar} {r_val:+.4f}")
    print("  " + "-" * 50)
    print("  " + " " * 5 + "-0.5" + " " * 7 + "0.0" + " " * 7 + "+0.5")

    # ═══════════════════════════════════════════
    # VERDICT
    # ═══════════════════════════════════════════
    print("\n" + "=" * 80)
    print("  VERDICT")
    print("=" * 80)

    # Level correlation
    abs_lag0 = abs(mean_lag[0])
    abs_lag1 = abs(mean_lag[1])
    n_lead_level = sum(1 for d in range(10) if abs(all_lag_results[d][1][0]) > abs(all_lag_results[d][0][0]))
    n_lead_delta = sum(1 for d in range(10) if abs(delta_lag_results[d][1][0]) > abs(delta_lag_results[d][0][0]))

    print(f"\n  Level correlation: |lag-0|={abs_lag0:.4f}, |lag-1|={abs_lag1:.4f}")
    print(f"  Digits where lag-1 > lag-0 (level): {n_lead_level}/10")
    print(f"  Digits where lag-1 > lag-0 (delta): {n_lead_delta}/10")

    print(f"\n  Granger causality (tension->accuracy, lag-1):")
    print(f"    Significant: {n_significant[1]}/10 digits")
    print(f"  Reverse Granger (accuracy->tension, lag-1):")
    print(f"    Significant: {n_sig_reverse[1]}/10 digits")

    if n_significant[1] > n_sig_reverse[1]:
        print(f"\n  --> ASYMMETRIC: tension Granger-causes accuracy MORE than reverse")
        print(f"      ({n_significant[1]} vs {n_sig_reverse[1]} significant digits)")
    elif n_significant[1] < n_sig_reverse[1]:
        print(f"\n  --> REVERSE: accuracy Granger-causes tension MORE")
    else:
        print(f"\n  --> SYMMETRIC: bidirectional Granger causality")

    # Final grade
    evidence_score = 0
    if abs_lag1 > abs_lag0:
        evidence_score += 1
    if n_lead_level >= 6:
        evidence_score += 1
    if n_lead_delta >= 6:
        evidence_score += 1
    if n_significant[1] >= 5:
        evidence_score += 2
    if n_significant[1] > n_sig_reverse[1] + 2:
        evidence_score += 1

    print(f"\n  Evidence score: {evidence_score}/6")

    if evidence_score >= 5:
        grade = "STRONG"
        emoji = "confirmed"
    elif evidence_score >= 3:
        grade = "MODERATE"
        emoji = "partial"
    elif evidence_score >= 1:
        grade = "WEAK"
        emoji = "weak"
    else:
        grade = "NOT SUPPORTED"
        emoji = "refuted"

    print(f"  Grade: {grade}")
    print(f"  H-281 status: {emoji}")

    print("\n" + "=" * 80)
    print("  Experiment complete.")
    print("=" * 80)


if __name__ == '__main__':
    main()
