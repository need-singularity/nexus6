#!/usr/bin/env python3
"""CRITICAL investigation: Why is inter-child tension INVERTED for anomalies?

H287: internal tension for anomalies is 95x HIGHER (AUROC=1.0)
Universality experiment: inter-child tension for anomalies is LOWER (raw AUROC < 0.5)

Hypothesis: "Agreement in confusion"
  - Children trained on normal data -> learn similar "normal manifold"
  - Normal data: children reconstruct differently (diverse pathways) -> HIGH inter-tension
  - Anomaly data: both children fail similarly (off-manifold collapse) -> LOW inter-tension

This experiment records per-sample:
  1. Internal tension of child_a and child_b (A vs G engines within each child)
  2. Inter-tension: |child_a_output - child_b_output|^2
  3. Reconstruction error of each child
  4. Full distribution comparison with ASCII histograms
"""

import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import copy
from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score


# ---------------------------------------------------------------------------
# Model: Autoencoder with internal A/G tension
# ---------------------------------------------------------------------------

class AutoencoderRepulsion(nn.Module):
    """Autoencoder with two internal engines (A and G) producing tension."""
    def __init__(self, input_dim, hidden_dim=64, bottleneck=16):
        super().__init__()
        self.engine_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, bottleneck), nn.ReLU(),
            nn.Linear(bottleneck, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
        )
        self.engine_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, bottleneck), nn.ReLU(),
            nn.Linear(bottleneck, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
        )

    def forward(self, x):
        a = self.engine_a(x)
        g = self.engine_g(x)
        out = (a + g) / 2
        tension = ((a - g) ** 2).mean(dim=-1)
        return out, tension, a, g


def mitosis(parent, scale=0.01):
    c_a = copy.deepcopy(parent)
    c_b = copy.deepcopy(parent)
    with torch.no_grad():
        for p in c_a.parameters():
            p.add_(torch.randn_like(p) * scale)
        for p in c_b.parameters():
            p.add_(torch.randn_like(p) * scale)
    return c_a, c_b


# ---------------------------------------------------------------------------
# ASCII histogram
# ---------------------------------------------------------------------------

def ascii_histogram(values, title="", bins=20, width=50):
    if len(values) == 0:
        print(f"  [{title}] no data")
        return
    values = np.array(values)
    lo, hi = values.min(), values.max()
    if lo == hi:
        hi = lo + 1
    counts, edges = np.histogram(values, bins=bins, range=(lo, hi))
    max_count = max(counts) if max(counts) > 0 else 1
    print(f"\n  {title}")
    print(f"  {'range':>14} {'cnt':>5}  distribution")
    print(f"  {'-'*14} {'-'*5}  {'-'*width}")
    for i, c in enumerate(counts):
        bar_len = int(c / max_count * width)
        label = f"{edges[i]:.4f}-{edges[i+1]:.4f}"
        print(f"  {label:>14} {c:>5}  {'#' * bar_len}")
    print(f"  mean={values.mean():.6f}, std={values.std():.6f}, "
          f"min={values.min():.6f}, max={values.max():.6f}, n={len(values)}")


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
        label = f"{edges[i]:.3f}-{edges[i+1]:.3f}"
        # Overlay: '#' for normal, '=' for anomaly
        line = list(' ' * width)
        for j in range(bar_n):
            line[j] = '#'
        for j in range(bar_a):
            if line[j] == '#':
                line[j] = '*'  # overlap
            else:
                line[j] = '='
        print(f"  {label:>14} {counts_n[i]:>4} {counts_a[i]:>4}  {''.join(line)}")

    print(f"  Normal:  mean={normal_vals.mean():.6f}, std={normal_vals.std():.6f}")
    print(f"  Anomaly: mean={anomaly_vals.mean():.6f}, std={anomaly_vals.std():.6f}")
    ratio = anomaly_vals.mean() / (normal_vals.mean() + 1e-12)
    direction = "HIGHER" if ratio > 1 else "LOWER"
    print(f"  Anomaly/Normal ratio: {ratio:.4f}x ({direction} for anomalies)")


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------

def main():
    np.random.seed(42)
    torch.manual_seed(42)

    print("=" * 72)
    print("TENSION INVERSION INVESTIGATION")
    print("Why is inter-child tension LOWER for anomalies?")
    print("=" * 72)

    # --- Load Breast Cancer ---
    data = load_breast_cancer()
    X, y = data.data, data.target  # 1=benign(normal), 0=malignant(anomaly)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    X_normal = X[y == 1]  # benign
    X_anomaly = X[y == 0]  # malignant

    idx = np.random.permutation(len(X_normal))
    n_train = int(0.7 * len(X_normal))
    X_train = X_normal[idx[:n_train]]
    X_test_n = X_normal[idx[n_train:]]
    X_test = np.vstack([X_test_n, X_anomaly])
    y_test = np.array([0] * len(X_test_n) + [1] * len(X_anomaly))

    print(f"\nDataset: Breast Cancer")
    print(f"  Train (normal only): {len(X_train)}")
    print(f"  Test normal: {len(X_test_n)}, Test anomaly: {len(X_anomaly)}")
    print(f"  Input dim: {X_train.shape[1]}")

    input_dim = X_train.shape[1]
    hidden_dim = 64
    bottleneck = 16

    X_train_t = torch.FloatTensor(X_train)
    X_test_t = torch.FloatTensor(X_test)

    N_TRIALS = 5  # multiple trials for stability

    all_internal_a_normal = []
    all_internal_a_anomaly = []
    all_internal_b_normal = []
    all_internal_b_anomaly = []
    all_inter_normal = []
    all_inter_anomaly = []
    all_recon_a_normal = []
    all_recon_a_anomaly = []
    all_recon_b_normal = []
    all_recon_b_anomaly = []

    auroc_internal_a_list = []
    auroc_internal_b_list = []
    auroc_inter_list = []
    auroc_recon_a_list = []
    auroc_recon_b_list = []
    auroc_recon_avg_list = []

    for trial in range(N_TRIALS):
        torch.manual_seed(trial * 100 + 42)
        np.random.seed(trial * 100 + 42)

        # --- Train parent ---
        parent = AutoencoderRepulsion(input_dim, hidden_dim, bottleneck)
        opt = torch.optim.Adam(parent.parameters(), lr=0.001)
        for ep in range(50):
            parent.train()
            opt.zero_grad()
            out, tension, _, _ = parent(X_train_t)
            loss = F.mse_loss(out, X_train_t)
            loss.backward()
            opt.step()

        # --- Mitosis ---
        child_a, child_b = mitosis(parent, scale=0.01)

        # --- Train children independently (different mini-batches) ---
        opt_a = torch.optim.Adam(child_a.parameters(), lr=0.001)
        opt_b = torch.optim.Adam(child_b.parameters(), lr=0.001)
        for ep in range(30):
            child_a.train()
            child_b.train()
            perm = torch.randperm(len(X_train_t))
            half = len(perm) // 2
            batch_a = X_train_t[perm[:half]]
            batch_b = X_train_t[perm[half:]]

            opt_a.zero_grad()
            out_a, _, _, _ = child_a(batch_a)
            F.mse_loss(out_a, batch_a).backward()
            opt_a.step()

            opt_b.zero_grad()
            out_b, _, _, _ = child_b(batch_b)
            F.mse_loss(out_b, batch_b).backward()
            opt_b.step()

        # --- Evaluate on test set ---
        child_a.eval()
        child_b.eval()
        with torch.no_grad():
            out_a, tension_a, a_a, g_a = child_a(X_test_t)
            out_b, tension_b, a_b, g_b = child_b(X_test_t)

            # Internal tension: |engine_a(x) - engine_g(x)|^2 per sample
            internal_a = tension_a.numpy()  # child_a's A vs G
            internal_b = tension_b.numpy()  # child_b's A vs G

            # Inter-child tension: |child_a_output - child_b_output|^2
            inter_tension = ((out_a - out_b) ** 2).mean(dim=-1).numpy()

            # Reconstruction error per child
            recon_a = ((out_a - X_test_t) ** 2).mean(dim=-1).numpy()
            recon_b = ((out_b - X_test_t) ** 2).mean(dim=-1).numpy()

        normal_mask = y_test == 0
        anomaly_mask = y_test == 1

        # Collect per-trial distributions
        all_internal_a_normal.extend(internal_a[normal_mask])
        all_internal_a_anomaly.extend(internal_a[anomaly_mask])
        all_internal_b_normal.extend(internal_b[normal_mask])
        all_internal_b_anomaly.extend(internal_b[anomaly_mask])
        all_inter_normal.extend(inter_tension[normal_mask])
        all_inter_anomaly.extend(inter_tension[anomaly_mask])
        all_recon_a_normal.extend(recon_a[normal_mask])
        all_recon_a_anomaly.extend(recon_a[anomaly_mask])
        all_recon_b_normal.extend(recon_b[normal_mask])
        all_recon_b_anomaly.extend(recon_b[anomaly_mask])

        # AUROC per trial
        auroc_int_a = roc_auc_score(y_test, internal_a)
        auroc_int_b = roc_auc_score(y_test, internal_b)
        auroc_inter = roc_auc_score(y_test, inter_tension)
        auroc_rec_a = roc_auc_score(y_test, recon_a)
        auroc_rec_b = roc_auc_score(y_test, recon_b)
        auroc_rec_avg = roc_auc_score(y_test, (recon_a + recon_b) / 2)

        auroc_internal_a_list.append(auroc_int_a)
        auroc_internal_b_list.append(auroc_int_b)
        auroc_inter_list.append(auroc_inter)
        auroc_recon_a_list.append(auroc_rec_a)
        auroc_recon_b_list.append(auroc_rec_b)
        auroc_recon_avg_list.append(auroc_rec_avg)

        print(f"\n  Trial {trial+1}/{N_TRIALS}:")
        print(f"    Internal A AUROC: {auroc_int_a:.4f}  |  Internal B AUROC: {auroc_int_b:.4f}")
        print(f"    Inter-child AUROC: {auroc_inter:.4f}  (raw, {'normal>anomaly' if auroc_inter < 0.5 else 'anomaly>normal'})")
        print(f"    Recon A AUROC: {auroc_rec_a:.4f}  |  Recon B AUROC: {auroc_rec_b:.4f}")
        print(f"    Recon avg AUROC: {auroc_rec_avg:.4f}")
        print(f"    Internal A: normal_mean={internal_a[normal_mask].mean():.6f}, anomaly_mean={internal_a[anomaly_mask].mean():.6f}")
        print(f"    Inter-child: normal_mean={inter_tension[normal_mask].mean():.6f}, anomaly_mean={inter_tension[anomaly_mask].mean():.6f}")
        print(f"    Recon A:     normal_mean={recon_a[normal_mask].mean():.6f}, anomaly_mean={recon_a[anomaly_mask].mean():.6f}")

    # ---------------------------------------------------------------------------
    # Aggregate results
    # ---------------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("AGGREGATE RESULTS (all trials combined)")
    print("=" * 72)

    print(f"\n  AUROC Summary (mean +/- std over {N_TRIALS} trials):")
    print(f"  {'Metric':<25} {'Mean':>7} {'Std':>7} {'Direction':<20}")
    print(f"  {'-'*25} {'-'*7} {'-'*7} {'-'*20}")

    metrics = [
        ("Internal A tension", auroc_internal_a_list),
        ("Internal B tension", auroc_internal_b_list),
        ("Inter-child tension", auroc_inter_list),
        ("Recon error A", auroc_recon_a_list),
        ("Recon error B", auroc_recon_b_list),
        ("Recon error avg", auroc_recon_avg_list),
    ]

    for name, vals in metrics:
        m = np.mean(vals)
        s = np.std(vals)
        direction = "anomaly>normal" if m > 0.5 else "normal>anomaly (INVERTED)"
        print(f"  {name:<25} {m:>7.4f} {s:>7.4f} {direction:<20}")

    # --- Distribution comparisons ---
    print("\n" + "=" * 72)
    print("DISTRIBUTION ANALYSIS")
    print("=" * 72)

    dual_histogram(all_internal_a_normal, all_internal_a_anomaly,
                   "Internal Tension (Child A): Normal(#) vs Anomaly(=)")

    dual_histogram(all_internal_b_normal, all_internal_b_anomaly,
                   "Internal Tension (Child B): Normal(#) vs Anomaly(=)")

    dual_histogram(all_inter_normal, all_inter_anomaly,
                   "Inter-Child Tension: Normal(#) vs Anomaly(=)")

    dual_histogram(all_recon_a_normal, all_recon_a_anomaly,
                   "Recon Error (Child A): Normal(#) vs Anomaly(=)")

    dual_histogram(all_recon_b_normal, all_recon_b_anomaly,
                   "Recon Error (Child B): Normal(#) vs Anomaly(=)")

    # --- Key statistics table ---
    print("\n" + "=" * 72)
    print("SUMMARY STATISTICS TABLE")
    print("=" * 72)

    data_pairs = [
        ("Internal tension A", all_internal_a_normal, all_internal_a_anomaly),
        ("Internal tension B", all_internal_b_normal, all_internal_b_anomaly),
        ("Inter-child tension", all_inter_normal, all_inter_anomaly),
        ("Recon error A", all_recon_a_normal, all_recon_a_anomaly),
        ("Recon error B", all_recon_b_normal, all_recon_b_anomaly),
    ]

    print(f"\n  {'Metric':<22} | {'Normal mean':>12} | {'Anomaly mean':>13} | {'Ratio A/N':>10} | {'Direction':>10}")
    print(f"  {'-'*22}-+-{'-'*12}-+-{'-'*13}-+-{'-'*10}-+-{'-'*10}")

    for name, nv, av in data_pairs:
        nm = np.mean(nv)
        am = np.mean(av)
        ratio = am / (nm + 1e-12)
        direction = "A > N" if am > nm else "N > A"
        print(f"  {name:<22} | {nm:>12.6f} | {am:>13.6f} | {ratio:>10.4f}x | {direction:>10}")

    # --- Correlation analysis ---
    print("\n" + "=" * 72)
    print("CORRELATION: Internal tension vs Inter-child tension")
    print("=" * 72)

    int_all = np.array(all_internal_a_normal + all_internal_a_anomaly)
    inter_all = np.array(all_inter_normal + all_inter_anomaly)
    labels_all = np.array([0] * len(all_internal_a_normal) + [1] * len(all_internal_a_anomaly))

    corr = np.corrcoef(int_all, inter_all)[0, 1]
    print(f"\n  Overall correlation (internal_A vs inter_child): {corr:.4f}")

    corr_n = np.corrcoef(all_internal_a_normal, all_inter_normal)[0, 1] if len(all_internal_a_normal) > 2 else 0
    corr_a = np.corrcoef(all_internal_a_anomaly, all_inter_anomaly)[0, 1] if len(all_internal_a_anomaly) > 2 else 0
    print(f"  Normal-only correlation:  {corr_n:.4f}")
    print(f"  Anomaly-only correlation: {corr_a:.4f}")

    # --- Mechanism analysis ---
    print("\n" + "=" * 72)
    print("MECHANISM ANALYSIS: Why is inter-tension inverted?")
    print("=" * 72)

    inter_n_mean = np.mean(all_inter_normal)
    inter_a_mean = np.mean(all_inter_anomaly)
    int_n_mean = np.mean(all_internal_a_normal)
    int_a_mean = np.mean(all_internal_a_anomaly)
    recon_n_mean = np.mean(all_recon_a_normal)
    recon_a_mean = np.mean(all_recon_a_anomaly)

    print(f"""
  OBSERVATION:
    Internal tension:  anomaly/normal = {int_a_mean/(int_n_mean+1e-12):.2f}x  (anomaly {'HIGHER' if int_a_mean > int_n_mean else 'LOWER'})
    Inter-child tension: anomaly/normal = {inter_a_mean/(inter_n_mean+1e-12):.2f}x  (anomaly {'HIGHER' if inter_a_mean > inter_n_mean else 'LOWER'})
    Recon error:       anomaly/normal = {recon_a_mean/(recon_n_mean+1e-12):.2f}x  (anomaly {'HIGHER' if recon_a_mean > recon_n_mean else 'LOWER'})

  HYPOTHESIS TEST: "Agreement in confusion"
    If children trained on normal data learn similar normal manifold:
      - Normal: children diverge (diverse reconstruction paths) -> HIGH inter-tension
      - Anomaly: both children fail similarly (off-manifold collapse) -> LOW inter-tension

    Evidence:""")

    if inter_a_mean < inter_n_mean:
        print(f"""
    CONFIRMED: Inter-child tension is LOWER for anomalies
      Normal inter-tension:  {inter_n_mean:.6f}
      Anomaly inter-tension: {inter_a_mean:.6f}
      Ratio: {inter_a_mean/(inter_n_mean+1e-12):.4f}x

    Interpretation:
      Both children see anomalous input they were NOT trained on.
      Their outputs converge to a similar "default" or "confused" state.
      This is "agreement in confusion" - low disagreement because neither
      child has a meaningful reconstruction strategy for anomalies.

      Meanwhile, for normal data, each child learned slightly different
      reconstruction pathways (due to different mini-batches during training),
      so their outputs DISAGREE more -> higher inter-tension.""")
    else:
        print(f"""
    REJECTED: Inter-child tension is HIGHER for anomalies
      Normal inter-tension:  {inter_n_mean:.6f}
      Anomaly inter-tension: {inter_a_mean:.6f}
      Ratio: {inter_a_mean/(inter_n_mean+1e-12):.4f}x

    Alternative: Both children diverge MORE on anomalies, suggesting
    they develop different failure modes (not agreement in confusion).""")

    # --- Additional test: output magnitude analysis ---
    print("\n" + "=" * 72)
    print("OUTPUT MAGNITUDE ANALYSIS")
    print("  Do both children produce similar magnitude outputs for anomalies?")
    print("=" * 72)

    # Re-run one trial to get raw outputs
    torch.manual_seed(42)
    parent = AutoencoderRepulsion(input_dim, hidden_dim, bottleneck)
    opt = torch.optim.Adam(parent.parameters(), lr=0.001)
    for ep in range(50):
        parent.train()
        opt.zero_grad()
        out, tension, _, _ = parent(X_train_t)
        loss = F.mse_loss(out, X_train_t)
        loss.backward()
        opt.step()

    child_a, child_b = mitosis(parent, scale=0.01)
    opt_a = torch.optim.Adam(child_a.parameters(), lr=0.001)
    opt_b = torch.optim.Adam(child_b.parameters(), lr=0.001)
    for ep in range(30):
        child_a.train()
        child_b.train()
        perm = torch.randperm(len(X_train_t))
        half = len(perm) // 2
        opt_a.zero_grad()
        out_a, _, _, _ = child_a(X_train_t[perm[:half]])
        F.mse_loss(out_a, X_train_t[perm[:half]]).backward()
        opt_a.step()
        opt_b.zero_grad()
        out_b, _, _, _ = child_b(X_train_t[perm[half:]])
        F.mse_loss(out_b, X_train_t[perm[half:]]).backward()
        opt_b.step()

    child_a.eval()
    child_b.eval()
    with torch.no_grad():
        out_a, _, a_a, g_a = child_a(X_test_t)
        out_b, _, a_b, g_b = child_b(X_test_t)

        # Output norm
        norm_a = torch.norm(out_a, dim=-1).numpy()
        norm_b = torch.norm(out_b, dim=-1).numpy()
        norm_diff = np.abs(norm_a - norm_b)

        # Cosine similarity between children outputs
        cos_sim = F.cosine_similarity(out_a, out_b, dim=-1).numpy()

    normal_mask = y_test == 0
    anomaly_mask = y_test == 1

    print(f"\n  Output norm (child A):")
    print(f"    Normal:  {norm_a[normal_mask].mean():.4f} +/- {norm_a[normal_mask].std():.4f}")
    print(f"    Anomaly: {norm_a[anomaly_mask].mean():.4f} +/- {norm_a[anomaly_mask].std():.4f}")

    print(f"\n  Output norm (child B):")
    print(f"    Normal:  {norm_b[normal_mask].mean():.4f} +/- {norm_b[normal_mask].std():.4f}")
    print(f"    Anomaly: {norm_b[anomaly_mask].mean():.4f} +/- {norm_b[anomaly_mask].std():.4f}")

    print(f"\n  Norm difference |A|-|B|:")
    print(f"    Normal:  {norm_diff[normal_mask].mean():.4f} +/- {norm_diff[normal_mask].std():.4f}")
    print(f"    Anomaly: {norm_diff[anomaly_mask].mean():.4f} +/- {norm_diff[anomaly_mask].std():.4f}")

    print(f"\n  Cosine similarity between child outputs:")
    print(f"    Normal:  {cos_sim[normal_mask].mean():.6f} +/- {cos_sim[normal_mask].std():.6f}")
    print(f"    Anomaly: {cos_sim[anomaly_mask].mean():.6f} +/- {cos_sim[anomaly_mask].std():.6f}")

    dual_histogram(cos_sim[normal_mask], cos_sim[anomaly_mask],
                   "Cosine Sim (children outputs): Normal(#) vs Anomaly(=)")

    # --- Engine-level analysis ---
    print("\n" + "=" * 72)
    print("ENGINE-LEVEL ANALYSIS: A vs G outputs within each child")
    print("=" * 72)

    with torch.no_grad():
        # A engines from both children
        cos_a_engines = F.cosine_similarity(a_a, a_b, dim=-1).numpy()
        cos_g_engines = F.cosine_similarity(g_a, g_b, dim=-1).numpy()

    print(f"\n  Cosine sim between child_A.engine_a and child_B.engine_a:")
    print(f"    Normal:  {cos_a_engines[normal_mask].mean():.6f}")
    print(f"    Anomaly: {cos_a_engines[anomaly_mask].mean():.6f}")

    print(f"\n  Cosine sim between child_A.engine_g and child_B.engine_g:")
    print(f"    Normal:  {cos_g_engines[normal_mask].mean():.6f}")
    print(f"    Anomaly: {cos_g_engines[anomaly_mask].mean():.6f}")

    # --- Practical implication ---
    print("\n" + "=" * 72)
    print("PRACTICAL IMPLICATION: Best anomaly score")
    print("=" * 72)

    # Try various combinations
    combos = {
        "Internal A only": np.array(all_internal_a_normal + all_internal_a_anomaly),
        "Internal B only": np.array(all_internal_b_normal + all_internal_b_anomaly),
        "Inter-child only": np.array(all_inter_normal + all_inter_anomaly),
        "Recon A only": np.array(all_recon_a_normal + all_recon_a_anomaly),
        "Recon - Inter": np.array(all_recon_a_normal + all_recon_a_anomaly) - np.array(all_inter_normal + all_inter_anomaly),
        "Internal + Recon": np.array(all_internal_a_normal + all_internal_a_anomaly) + np.array(all_recon_a_normal + all_recon_a_anomaly),
        "Internal - Inter": np.array(all_internal_a_normal + all_internal_a_anomaly) - np.array(all_inter_normal + all_inter_anomaly),
        "Recon / (Inter+eps)": np.array(all_recon_a_normal + all_recon_a_anomaly) / (np.array(all_inter_normal + all_inter_anomaly) + 1e-8),
    }

    labels_combined = np.array([0] * len(all_internal_a_normal) + [1] * len(all_internal_a_anomaly))

    print(f"\n  {'Scoring method':<25} {'AUROC':>7} {'Direction':>12}")
    print(f"  {'-'*25} {'-'*7} {'-'*12}")

    for name, scores in combos.items():
        auroc = roc_auc_score(labels_combined, scores)
        direction = "correct" if auroc > 0.5 else "INVERTED"
        effective = max(auroc, 1 - auroc)
        print(f"  {name:<25} {auroc:>7.4f} {direction:>12}  (effective: {effective:.4f})")

    print("\n" + "=" * 72)
    print("CONCLUSION")
    print("=" * 72)

    inter_inverted = np.mean(auroc_inter_list) < 0.5
    internal_correct = np.mean(auroc_internal_a_list) > 0.5

    if inter_inverted and internal_correct:
        print("""
  CONFIRMED: Tension inversion is real and systematic.

  Internal tension (within each child):
    -> HIGHER for anomalies (correct direction, same as H287)
    -> Each child's A and G engines disagree MORE on unseen anomaly patterns

  Inter-child tension (between children):
    -> LOWER for anomalies (INVERTED direction)
    -> Both children produce SIMILAR outputs for anomalies

  ROOT CAUSE: "Agreement in Confusion"
    Children trained on normal data via mitosis (shared parent + noise):
    1. For NORMAL inputs: each child found slightly different reconstruction
       strategies (different mini-batches -> different local optima)
       -> Their outputs DISAGREE -> HIGH inter-tension
    2. For ANOMALY inputs: neither child has learned to reconstruct these
       -> Both default to a similar "fallback" output (near parent's behavior)
       -> Their outputs AGREE -> LOW inter-tension

  This is NOT a bug -- it's a feature:
    - Internal tension detects "this input is weird" (within-model confusion)
    - Inter-tension detects "both models agree" (between-model agreement)
    - For anomalies: high internal + low inter = "confused but agreeing"
    - Optimal score = Internal_tension - Inter_tension or Internal / Inter
""")
    elif not inter_inverted:
        print("""
  NOT CONFIRMED: Inter-child tension is NOT inverted in this run.
  Both internal and inter-tension are higher for anomalies.
  The inversion may be dataset/hyperparameter dependent.
""")
    else:
        print("""
  PARTIAL: Inter-tension is inverted but internal tension is also inverted.
  This suggests a different mechanism than "agreement in confusion".
""")

    print("=" * 72)
    print("EXPERIMENT COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
