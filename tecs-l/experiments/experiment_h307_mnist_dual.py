#!/usr/bin/env python3
"""H307 Dual Mechanism Reproduction on MNIST

Key question: Does the dual tension mechanism (internal vs inter) reproduce on MNIST?
  - Inter-child tension: anomaly HIGHER than normal? (normal direction)
  - Internal tension: anomaly LOWER than normal? (inverted direction)

Setup:
  - MNIST digit 0 = normal, digit 1 = anomaly
  - Train parent autoencoder (2-engine, MSE) on digit 0 only, 10 epochs
  - Mitosis N=2, train children independently 10 epochs
  - Measure per-sample: internal tension (A vs G within child), inter tension
    (child_a vs child_b output), recon error
  - 3 trials, AUROC + ASCII histograms
"""

import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import copy
from sklearn.metrics import roc_auc_score
from torchvision import datasets, transforms


# ---------------------------------------------------------------------------
# Model: 2-engine autoencoder with internal A/G tension
# ---------------------------------------------------------------------------

class DualEngineAutoencoder(nn.Module):
    """Autoencoder with two internal engines (A and G) producing tension.
    Input: 784 (28x28 flattened MNIST)
    """
    def __init__(self, input_dim=784, hidden_dim=128, bottleneck=32):
        super().__init__()
        # Engine A: encoder-decoder path
        self.engine_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, bottleneck), nn.ReLU(),
            nn.Linear(bottleneck, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, input_dim), nn.Sigmoid(),
        )
        # Engine G: encoder-decoder path (different initialization)
        self.engine_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, bottleneck), nn.ReLU(),
            nn.Linear(bottleneck, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, input_dim), nn.Sigmoid(),
        )

    def forward(self, x):
        a = self.engine_a(x)
        g = self.engine_g(x)
        out = (a + g) / 2
        tension = ((a - g) ** 2).mean(dim=-1)  # internal tension per sample
        return out, tension, a, g


def mitosis(parent, scale=0.01):
    """Split parent into two children with small random perturbation."""
    c_a = copy.deepcopy(parent)
    c_b = copy.deepcopy(parent)
    with torch.no_grad():
        for p in c_a.parameters():
            p.add_(torch.randn_like(p) * scale)
        for p in c_b.parameters():
            p.add_(torch.randn_like(p) * scale)
    return c_a, c_b


# ---------------------------------------------------------------------------
# ASCII visualization
# ---------------------------------------------------------------------------

def dual_histogram(normal_vals, anomaly_vals, title="", bins=15, width=40):
    """Side-by-side comparison histogram."""
    normal_vals = np.array(normal_vals)
    anomaly_vals = np.array(anomaly_vals)
    all_vals = np.concatenate([normal_vals, anomaly_vals])
    lo, hi = all_vals.min(), all_vals.max()
    if lo == hi:
        hi = lo + 1

    counts_n, edges = np.histogram(normal_vals, bins=bins, range=(lo, hi))
    counts_a, _ = np.histogram(anomaly_vals, bins=bins, range=(lo, hi))
    max_count = max(max(counts_n), max(counts_a), 1)

    print(f"\n  {title}")
    print(f"  {'range':>14} {'N':>4} {'A':>4}  Normal(#) vs Anomaly(=)")
    print(f"  {'-'*14} {'-'*4} {'-'*4}  {'-'*width}")
    for i in range(len(counts_n)):
        bar_n = int(counts_n[i] / max_count * width)
        bar_a = int(counts_a[i] / max_count * width)
        label = f"{edges[i]:.4f}-{edges[i+1]:.4f}"
        line = list(' ' * width)
        for j in range(bar_n):
            line[j] = '#'
        for j in range(bar_a):
            if line[j] == '#':
                line[j] = '*'
            else:
                line[j] = '='
        print(f"  {label:>14} {counts_n[i]:>4} {counts_a[i]:>4}  {''.join(line)}")

    print(f"  Normal:  mean={normal_vals.mean():.6f}, std={normal_vals.std():.6f}, n={len(normal_vals)}")
    print(f"  Anomaly: mean={anomaly_vals.mean():.6f}, std={anomaly_vals.std():.6f}, n={len(anomaly_vals)}")
    ratio = anomaly_vals.mean() / (normal_vals.mean() + 1e-12)
    direction = "HIGHER" if ratio > 1 else "LOWER"
    print(f"  Anomaly/Normal ratio: {ratio:.4f}x ({direction} for anomalies)")


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------

def main():
    print("=" * 72)
    print("H307 DUAL MECHANISM REPRODUCTION ON MNIST")
    print("  digit 0 = normal, digit 1 = anomaly")
    print("  Question: Does MNIST show the dual mechanism?")
    print("    Inter: anomaly higher (normal direction)?")
    print("    Internal: anomaly lower (inverted)?")
    print("=" * 72)

    # --- Load MNIST ---
    transform = transforms.Compose([transforms.ToTensor()])
    train_dataset = datasets.MNIST(root='/tmp/mnist', train=True, download=True, transform=transform)
    test_dataset = datasets.MNIST(root='/tmp/mnist', train=False, download=True, transform=transform)

    # Extract digit 0 (normal) and digit 1 (anomaly)
    train_data = train_dataset.data.float() / 255.0
    train_labels = train_dataset.targets
    test_data = test_dataset.data.float() / 255.0
    test_labels = test_dataset.targets

    # Flatten 28x28 -> 784
    train_data = train_data.view(-1, 784)
    test_data = test_data.view(-1, 784)

    # Training: digit 0 only
    train_mask_0 = train_labels == 0
    X_train = train_data[train_mask_0]

    # Test: digit 0 (normal) + digit 1 (anomaly)
    test_mask_0 = test_labels == 0
    test_mask_1 = test_labels == 1
    X_test_normal = test_data[test_mask_0]
    X_test_anomaly = test_data[test_mask_1]
    X_test = torch.cat([X_test_normal, X_test_anomaly], dim=0)
    y_test = np.array([0] * len(X_test_normal) + [1] * len(X_test_anomaly))

    print(f"\n  Dataset: MNIST")
    print(f"  Train (digit 0 only): {len(X_train)}")
    print(f"  Test normal (digit 0): {len(X_test_normal)}")
    print(f"  Test anomaly (digit 1): {len(X_test_anomaly)}")
    print(f"  Input dim: 784")

    N_TRIALS = 3
    PARENT_EPOCHS = 10
    CHILD_EPOCHS = 10
    BATCH_SIZE = 256

    # Accumulators across trials
    all_internal_a_normal, all_internal_a_anomaly = [], []
    all_internal_b_normal, all_internal_b_anomaly = [], []
    all_inter_normal, all_inter_anomaly = [], []
    all_recon_normal, all_recon_anomaly = [], []

    auroc_internal_a_list = []
    auroc_internal_b_list = []
    auroc_inter_list = []
    auroc_recon_list = []
    auroc_internal_avg_list = []

    for trial in range(N_TRIALS):
        torch.manual_seed(trial * 1000 + 42)
        np.random.seed(trial * 1000 + 42)

        print(f"\n{'_'*72}")
        print(f"  Trial {trial+1}/{N_TRIALS}")
        print(f"{'_'*72}")

        # === 1. Train parent autoencoder ===
        parent = DualEngineAutoencoder(784, 128, 32)
        opt = torch.optim.Adam(parent.parameters(), lr=1e-3)

        for ep in range(PARENT_EPOCHS):
            parent.train()
            perm = torch.randperm(len(X_train))
            epoch_loss = 0.0
            n_batches = 0
            for i in range(0, len(X_train), BATCH_SIZE):
                batch = X_train[perm[i:i+BATCH_SIZE]]
                opt.zero_grad()
                out, tension, _, _ = parent(batch)
                loss = F.mse_loss(out, batch)
                loss.backward()
                opt.step()
                epoch_loss += loss.item()
                n_batches += 1
            if ep == 0 or ep == PARENT_EPOCHS - 1:
                print(f"    Parent epoch {ep+1}/{PARENT_EPOCHS}: loss={epoch_loss/n_batches:.6f}")

        # === 2. Mitosis ===
        child_a, child_b = mitosis(parent, scale=0.01)

        # === 3. Train children independently ===
        opt_a = torch.optim.Adam(child_a.parameters(), lr=1e-3)
        opt_b = torch.optim.Adam(child_b.parameters(), lr=1e-3)

        for ep in range(CHILD_EPOCHS):
            child_a.train()
            child_b.train()
            perm = torch.randperm(len(X_train))
            half = len(perm) // 2

            # Child A gets first half, Child B gets second half
            for i in range(0, half, BATCH_SIZE):
                batch_a = X_train[perm[i:min(i+BATCH_SIZE, half)]]
                opt_a.zero_grad()
                out_a, _, _, _ = child_a(batch_a)
                F.mse_loss(out_a, batch_a).backward()
                opt_a.step()

            for i in range(half, len(perm), BATCH_SIZE):
                batch_b = X_train[perm[i:min(i+BATCH_SIZE, len(perm))]]
                opt_b.zero_grad()
                out_b, _, _, _ = child_b(batch_b)
                F.mse_loss(out_b, batch_b).backward()
                opt_b.step()

            if ep == 0 or ep == CHILD_EPOCHS - 1:
                child_a.eval(); child_b.eval()
                with torch.no_grad():
                    la = F.mse_loss(child_a(X_train[:500])[0], X_train[:500]).item()
                    lb = F.mse_loss(child_b(X_train[:500])[0], X_train[:500]).item()
                print(f"    Child epoch {ep+1}/{CHILD_EPOCHS}: A_loss={la:.6f}, B_loss={lb:.6f}")

        # === 4. Evaluate on test set ===
        child_a.eval()
        child_b.eval()
        with torch.no_grad():
            # Process in batches to avoid memory issues
            all_out_a, all_tension_a = [], []
            all_out_b, all_tension_b = [], []

            for i in range(0, len(X_test), BATCH_SIZE):
                batch = X_test[i:i+BATCH_SIZE]
                out_a, t_a, a_a, g_a = child_a(batch)
                out_b, t_b, a_b, g_b = child_b(batch)
                all_out_a.append(out_a)
                all_tension_a.append(t_a)
                all_out_b.append(out_b)
                all_tension_b.append(t_b)

            out_a = torch.cat(all_out_a, dim=0)
            tension_a = torch.cat(all_tension_a, dim=0)
            out_b = torch.cat(all_out_b, dim=0)
            tension_b = torch.cat(all_tension_b, dim=0)

            # Internal tension: |engine_a(x) - engine_g(x)|^2 per sample (within each child)
            internal_a = tension_a.numpy()
            internal_b = tension_b.numpy()

            # Inter-child tension: |child_a_output(x) - child_b_output(x)|^2
            inter_tension = ((out_a - out_b) ** 2).mean(dim=-1).numpy()

            # Reconstruction error (average of both children)
            recon_err = (((out_a - X_test) ** 2).mean(dim=-1).numpy() +
                         ((out_b - X_test) ** 2).mean(dim=-1).numpy()) / 2

        normal_mask = y_test == 0
        anomaly_mask = y_test == 1

        # Collect per-trial distributions
        all_internal_a_normal.extend(internal_a[normal_mask])
        all_internal_a_anomaly.extend(internal_a[anomaly_mask])
        all_internal_b_normal.extend(internal_b[normal_mask])
        all_internal_b_anomaly.extend(internal_b[anomaly_mask])
        all_inter_normal.extend(inter_tension[normal_mask])
        all_inter_anomaly.extend(inter_tension[anomaly_mask])
        all_recon_normal.extend(recon_err[normal_mask])
        all_recon_anomaly.extend(recon_err[anomaly_mask])

        # AUROC per trial
        auroc_int_a = roc_auc_score(y_test, internal_a)
        auroc_int_b = roc_auc_score(y_test, internal_b)
        auroc_int_avg = roc_auc_score(y_test, (internal_a + internal_b) / 2)
        auroc_inter = roc_auc_score(y_test, inter_tension)
        auroc_recon = roc_auc_score(y_test, recon_err)

        auroc_internal_a_list.append(auroc_int_a)
        auroc_internal_b_list.append(auroc_int_b)
        auroc_internal_avg_list.append(auroc_int_avg)
        auroc_inter_list.append(auroc_inter)
        auroc_recon_list.append(auroc_recon)

        int_a_dir = "anomaly>normal" if auroc_int_a > 0.5 else "normal>anomaly(INV)"
        int_b_dir = "anomaly>normal" if auroc_int_b > 0.5 else "normal>anomaly(INV)"
        inter_dir = "anomaly>normal" if auroc_inter > 0.5 else "normal>anomaly(INV)"

        print(f"\n    --- Per-sample statistics ---")
        print(f"    Internal A:  normal={internal_a[normal_mask].mean():.6f}, anomaly={internal_a[anomaly_mask].mean():.6f}, AUROC={auroc_int_a:.4f} [{int_a_dir}]")
        print(f"    Internal B:  normal={internal_b[normal_mask].mean():.6f}, anomaly={internal_b[anomaly_mask].mean():.6f}, AUROC={auroc_int_b:.4f} [{int_b_dir}]")
        print(f"    Inter-child: normal={inter_tension[normal_mask].mean():.6f}, anomaly={inter_tension[anomaly_mask].mean():.6f}, AUROC={auroc_inter:.4f} [{inter_dir}]")
        print(f"    Recon error: normal={recon_err[normal_mask].mean():.6f}, anomaly={recon_err[anomaly_mask].mean():.6f}, AUROC={auroc_recon:.4f}")

    # =========================================================================
    # Aggregate results
    # =========================================================================
    print("\n" + "=" * 72)
    print("AGGREGATE RESULTS (all trials)")
    print("=" * 72)

    print(f"\n  AUROC Summary (mean +/- std over {N_TRIALS} trials):")
    print(f"  {'Metric':<25} {'Mean':>7} {'Std':>7} {'Direction':<25}")
    print(f"  {'-'*25} {'-'*7} {'-'*7} {'-'*25}")

    metrics = [
        ("Internal A tension", auroc_internal_a_list),
        ("Internal B tension", auroc_internal_b_list),
        ("Internal avg tension", auroc_internal_avg_list),
        ("Inter-child tension", auroc_inter_list),
        ("Recon error (avg)", auroc_recon_list),
    ]

    for name, vals in metrics:
        m = np.mean(vals)
        s = np.std(vals)
        if m > 0.5:
            direction = "anomaly > normal"
        else:
            direction = "normal > anomaly (INVERTED)"
        print(f"  {name:<25} {m:>7.4f} {s:>7.4f} {direction:<25}")

    # --- Distribution histograms ---
    print("\n" + "=" * 72)
    print("DISTRIBUTION ANALYSIS")
    print("=" * 72)

    dual_histogram(all_internal_a_normal, all_internal_a_anomaly,
                   "Internal Tension (Child A): Normal(#) vs Anomaly(=)")
    dual_histogram(all_internal_b_normal, all_internal_b_anomaly,
                   "Internal Tension (Child B): Normal(#) vs Anomaly(=)")
    dual_histogram(all_inter_normal, all_inter_anomaly,
                   "Inter-Child Tension: Normal(#) vs Anomaly(=)")
    dual_histogram(all_recon_normal, all_recon_anomaly,
                   "Recon Error (avg): Normal(#) vs Anomaly(=)")

    # --- Summary statistics table ---
    print("\n" + "=" * 72)
    print("SUMMARY STATISTICS TABLE")
    print("=" * 72)

    data_pairs = [
        ("Internal tension A", all_internal_a_normal, all_internal_a_anomaly),
        ("Internal tension B", all_internal_b_normal, all_internal_b_anomaly),
        ("Inter-child tension", all_inter_normal, all_inter_anomaly),
        ("Recon error (avg)", all_recon_normal, all_recon_anomaly),
    ]

    print(f"\n  {'Metric':<22} | {'Normal mean':>12} | {'Anomaly mean':>13} | {'Ratio A/N':>10} | {'Direction':>10}")
    print(f"  {'-'*22}-+-{'-'*12}-+-{'-'*13}-+-{'-'*10}-+-{'-'*10}")

    for name, nv, av in data_pairs:
        nm = np.mean(nv)
        am = np.mean(av)
        ratio = am / (nm + 1e-12)
        direction = "A > N" if am > nm else "N > A"
        print(f"  {name:<22} | {nm:>12.6f} | {am:>13.6f} | {ratio:>10.4f}x | {direction:>10}")

    # --- Combination scoring ---
    print("\n" + "=" * 72)
    print("COMBINATION SCORING: Can we combine internal + inter for better AUROC?")
    print("=" * 72)

    int_all = np.array(all_internal_a_normal + all_internal_a_anomaly)
    inter_all = np.array(all_inter_normal + all_inter_anomaly)
    recon_all = np.array(all_recon_normal + all_recon_anomaly)
    labels_all = np.array([0] * len(all_internal_a_normal) + [1] * len(all_internal_a_anomaly))

    combos = {
        "Internal A only": int_all,
        "Inter-child only": inter_all,
        "Recon only": recon_all,
        "Internal - Inter": int_all - inter_all,
        "Internal + Recon": int_all + recon_all,
        "Recon - Inter": recon_all - inter_all,
        "Internal / (Inter+eps)": int_all / (inter_all + 1e-8),
        "(Internal+Recon)/(Inter+eps)": (int_all + recon_all) / (inter_all + 1e-8),
    }

    print(f"\n  {'Scoring method':<30} {'AUROC':>7} {'Eff.AUROC':>10} {'Direction':>12}")
    print(f"  {'-'*30} {'-'*7} {'-'*10} {'-'*12}")

    for name, scores in combos.items():
        auroc = roc_auc_score(labels_all, scores)
        effective = max(auroc, 1 - auroc)
        direction = "correct" if auroc > 0.5 else "INVERTED"
        print(f"  {name:<30} {auroc:>7.4f} {effective:>10.4f} {direction:>12}")

    # --- Correlation ---
    print("\n" + "=" * 72)
    print("CORRELATION: Internal vs Inter-child tension")
    print("=" * 72)

    corr_overall = np.corrcoef(int_all, inter_all)[0, 1]
    corr_n = np.corrcoef(all_internal_a_normal, all_inter_normal)[0, 1]
    corr_a = np.corrcoef(all_internal_a_anomaly, all_inter_anomaly)[0, 1]
    print(f"\n  Overall:      r = {corr_overall:.4f}")
    print(f"  Normal only:  r = {corr_n:.4f}")
    print(f"  Anomaly only: r = {corr_a:.4f}")

    # --- Final verdict ---
    print("\n" + "=" * 72)
    print("VERDICT: Does MNIST show the H307 dual mechanism?")
    print("=" * 72)

    inter_mean_auroc = np.mean(auroc_inter_list)
    internal_mean_auroc = np.mean(auroc_internal_a_list)

    inter_direction = "anomaly > normal" if inter_mean_auroc > 0.5 else "normal > anomaly (INVERTED)"
    internal_direction = "anomaly > normal" if internal_mean_auroc > 0.5 else "normal > anomaly (INVERTED)"

    inter_n_mean = np.mean(all_inter_normal)
    inter_a_mean = np.mean(all_inter_anomaly)
    int_n_mean = np.mean(all_internal_a_normal)
    int_a_mean = np.mean(all_internal_a_anomaly)

    print(f"""
  Inter-child tension:
    Direction: {inter_direction}
    Mean AUROC: {inter_mean_auroc:.4f}
    Normal mean: {inter_n_mean:.6f}, Anomaly mean: {inter_a_mean:.6f}
    Ratio (anomaly/normal): {inter_a_mean/(inter_n_mean+1e-12):.4f}x

  Internal tension:
    Direction: {internal_direction}
    Mean AUROC: {internal_mean_auroc:.4f}
    Normal mean: {int_n_mean:.6f}, Anomaly mean: {int_a_mean:.6f}
    Ratio (anomaly/normal): {int_a_mean/(int_n_mean+1e-12):.4f}x
""")

    # Check if dual mechanism matches expectation
    inter_normal_dir = inter_mean_auroc > 0.5  # anomaly higher = normal direction
    internal_inverted = internal_mean_auroc < 0.5  # anomaly lower = inverted

    if inter_normal_dir and internal_inverted:
        print("  RESULT: FULL DUAL MECHANISM CONFIRMED on MNIST!")
        print("    Inter-child: anomaly HIGHER (normal direction)")
        print("    Internal:    anomaly LOWER  (inverted direction)")
        print("    -> Same dual mechanism as breast cancer / other datasets")
    elif inter_normal_dir and not internal_inverted:
        print("  RESULT: PARTIAL - Both tensions higher for anomaly")
        print("    Inter-child: anomaly HIGHER (normal direction)")
        print("    Internal:    anomaly HIGHER (normal direction)")
        print("    -> No inversion; both tensions detect anomalies in same direction")
    elif not inter_normal_dir and internal_inverted:
        print("  RESULT: OPPOSITE DUAL - directions swapped from breast cancer")
        print("    Inter-child: anomaly LOWER  (inverted)")
        print("    Internal:    anomaly LOWER  (inverted)")
        print("    -> Different from breast cancer pattern")
    elif not inter_normal_dir and not internal_inverted:
        print("  RESULT: REVERSED DUAL MECHANISM on MNIST!")
        print("    Inter-child: anomaly LOWER  (inverted direction)")
        print("    Internal:    anomaly HIGHER (normal direction)")
        print("    -> Mirror image of breast cancer! Same dual mechanism, opposite assignment")
        print("    -> This is the 'agreement in confusion' pattern from breast cancer")

    print(f"""
  Summary ASCII comparison:

  Breast Cancer (H307 original):
    Inter-child:  Normal ======== > Anomaly ====    (INVERTED)
    Internal:     Normal ====     < Anomaly ======== (NORMAL)

  MNIST (this experiment):
    Inter-child:  Normal {'====' if not inter_normal_dir else '========'} {'>' if not inter_normal_dir else '<'} Anomaly {'========' if not inter_normal_dir else '===='} ({'INVERTED' if not inter_normal_dir else 'NORMAL'})
    Internal:     Normal {'========' if internal_inverted else '===='} {'>' if internal_inverted else '<'} Anomaly {'====' if internal_inverted else '========'} ({'INVERTED' if internal_inverted else 'NORMAL'})
""")

    print("=" * 72)
    print("EXPERIMENT COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
