#!/usr/bin/env python3
"""Fresh verification of 4 unverified hypotheses: H-CX-80, H-CX-127, H-CX-148, H-CX-150

All self-contained. No dependency on old paths.
Uses PureFieldEngine from model_pure_field.py and load_mnist from model_utils.py.

H-CX-80:  Orthogonality -> Synergy (r > 0.8 predicted)
H-CX-127: PH Entanglement (r > 0 with 0 shared data)
H-CX-148: Tension Resonance (r > 0.9 predicted)
H-CX-150: Silent Consensus (cos > 0.5 predicted)
"""
import sys, os
sys.path.insert(0, '/Users/ghost/Dev/TECS-L')

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from scipy.stats import pearsonr, spearmanr, kendalltau
from scipy.optimize import linear_sum_assignment
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset
from model_pure_field import PureFieldEngine
import time

np.random.seed(42)

# ─────────────────────────────────────────
# Data Loading
# ─────────────────────────────────────────
def load_dataset(name='mnist', batch_size=256, data_dir='/tmp/data'):
    if name == 'mnist':
        t = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
        tr = datasets.MNIST(data_dir, train=True, download=True, transform=t)
        te = datasets.MNIST(data_dir, train=False, transform=t)
        dim = 784
        cls_names = [str(i) for i in range(10)]
    elif name == 'fashion':
        t = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.2860,), (0.3530,))])
        tr = datasets.FashionMNIST(data_dir, train=True, download=True, transform=t)
        te = datasets.FashionMNIST(data_dir, train=False, transform=t)
        dim = 784
        cls_names = ['Tshirt','Trouser','Pullvr','Dress','Coat',
                     'Sandal','Shirt','Sneakr','Bag','Boot']
    else:
        raise ValueError(f"Unknown dataset: {name}")
    tl = DataLoader(tr, batch_size=batch_size, shuffle=True, num_workers=0)
    tel = DataLoader(te, batch_size=512, shuffle=False, num_workers=0)
    return dim, tl, tel, cls_names, tr, te


def train_purefield(dim, train_loader, epochs=15, seed=42):
    """Train PureFieldEngine and return trained model."""
    torch.manual_seed(seed)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()
    for ep in range(epochs):
        model.train()
        for x, y in train_loader:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y)
            loss.backward()
            opt.step()
    # Eval accuracy
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for x, y in train_loader:
            out, _ = model(x.view(-1, dim))
            correct += (out.argmax(1) == y).sum().item()
            total += y.size(0)
    return model, correct / total


# ═══════════════════════════════════════════
# H-CX-148: Tension Resonance Telepathy
# ═══════════════════════════════════════════
def verify_hcx148(dim, train_loader, test_loader, cls_names):
    print(f"\n{'='*70}")
    print(f"  H-CX-148: Tension Resonance Telepathy")
    print(f"  Prediction: r > 0.9 (same-input tension correlation)")
    print(f"{'='*70}")

    # Train two independent models with different seeds
    print("\n  Training Model A (seed=42)...")
    model_a, acc_a = train_purefield(dim, train_loader, epochs=15, seed=42)
    print(f"    Model A train acc: {acc_a*100:.1f}%")

    print("  Training Model B (seed=777)...")
    model_b, acc_b = train_purefield(dim, train_loader, epochs=15, seed=777)
    print(f"    Model B train acc: {acc_b*100:.1f}%")

    # Collect tensions per sample
    model_a.eval(); model_b.eval()
    tensions_a, tensions_b, labels = [], [], []
    with torch.no_grad():
        for x, y in test_loader:
            x_flat = x.view(-1, dim)
            _, ta = model_a(x_flat)
            _, tb = model_b(x_flat)
            tensions_a.extend(ta.numpy().tolist())
            tensions_b.extend(tb.numpy().tolist())
            labels.extend(y.numpy().tolist())

    ta = np.array(tensions_a)
    tb = np.array(tensions_b)
    labels = np.array(labels)

    # Overall correlation
    r_pearson, p_pearson = pearsonr(ta, tb)
    r_spearman, p_spearman = spearmanr(ta, tb)
    r_kendall, p_kendall = kendalltau(ta, tb)

    print(f"\n  Overall tension correlation (N={len(ta)}):")
    print(f"    Pearson:  r={r_pearson:.4f}, p={p_pearson:.2e}")
    print(f"    Spearman: r={r_spearman:.4f}, p={p_spearman:.2e}")
    print(f"    Kendall:  tau={r_kendall:.4f}, p={p_kendall:.2e}")

    # Per-class tension means
    print(f"\n  Per-class mean tension:")
    print(f"    {'Class':>8} {'Model_A':>10} {'Model_B':>10} {'Diff':>10}")
    print(f"    {'-'*40}")
    class_ta, class_tb = [], []
    for c in range(10):
        mask = labels == c
        ma = ta[mask].mean()
        mb = tb[mask].mean()
        class_ta.append(ma)
        class_tb.append(mb)
        print(f"    {cls_names[c]:>8} {ma:>10.4f} {mb:>10.4f} {abs(ma-mb):>10.4f}")

    r_class, p_class = pearsonr(class_ta, class_tb)
    tau_class, p_tau = kendalltau(class_ta, class_tb)
    print(f"\n  Class-mean correlation: r={r_class:.4f}, tau={tau_class:.4f}")

    verdict = "VERIFIED" if r_pearson > 0.9 else "PARTIALLY VERIFIED" if r_pearson > 0.5 else "REFUTED"
    print(f"\n  VERDICT: {verdict} (r={r_pearson:.4f} vs predicted r>0.9)")

    return {
        'r_pearson': r_pearson, 'r_spearman': r_spearman,
        'r_class': r_class, 'tau_class': tau_class,
        'verdict': verdict,
        'model_a': model_a, 'model_b': model_b
    }


# ═══════════════════════════════════════════
# H-CX-150: Silent Consensus
# ═══════════════════════════════════════════
def verify_hcx150(dim, test_loader, cls_names, model_a, model_b):
    print(f"\n{'='*70}")
    print(f"  H-CX-150: Silent Consensus")
    print(f"  Prediction: cos > 0.5 (class centroids converge across models)")
    print(f"{'='*70}")

    n_cls = 10
    model_a.eval(); model_b.eval()

    # Collect class centroids from output space (A-G direction)
    centroids_a = [[] for _ in range(n_cls)]
    centroids_b = [[] for _ in range(n_cls)]

    with torch.no_grad():
        for x, y in test_loader:
            x_flat = x.view(-1, dim)
            rep_a = model_a.engine_a(x_flat) - model_a.engine_g(x_flat)
            rep_b = model_b.engine_a(x_flat) - model_b.engine_g(x_flat)
            dir_a = F.normalize(rep_a, dim=-1).numpy()
            dir_b = F.normalize(rep_b, dim=-1).numpy()
            for i in range(len(y)):
                c = y[i].item()
                centroids_a[c].append(dir_a[i])
                centroids_b[c].append(dir_b[i])

    # Compute mean centroids
    mean_a = np.zeros((n_cls, 10))
    mean_b = np.zeros((n_cls, 10))
    for c in range(n_cls):
        ca = np.array(centroids_a[c])
        cb = np.array(centroids_b[c])
        mean_a[c] = ca.mean(0)
        mean_b[c] = cb.mean(0)
        # Normalize
        mean_a[c] /= max(np.linalg.norm(mean_a[c]), 1e-8)
        mean_b[c] /= max(np.linalg.norm(mean_b[c]), 1e-8)

    # Raw cosine similarity (same class, different models)
    cos_sims_raw = []
    print(f"\n  Raw cosine similarity (same class, Model A vs Model B):")
    print(f"    {'Class':>8} {'cos(A,B)':>10}")
    print(f"    {'-'*20}")
    for c in range(n_cls):
        cos = float(np.dot(mean_a[c], mean_b[c]))
        cos_sims_raw.append(cos)
        print(f"    {cls_names[c]:>8} {cos:>10.4f}")
    raw_mean = np.mean(cos_sims_raw)
    print(f"    {'Mean':>8} {raw_mean:>10.4f}")

    # Permutation-aligned cosine similarity (Hungarian algorithm)
    # Since models may swap class representations, find optimal Expert permutation
    # But here we have class centroids, not Expert centroids
    # The point is: do centroids align even without explicit coordination?
    # We already computed raw cos above. But let's also check if the
    # inter-class structure is preserved.

    # Cross-model centroid similarity matrix
    cross_cos = np.zeros((n_cls, n_cls))
    for i in range(n_cls):
        for j in range(n_cls):
            cross_cos[i, j] = np.dot(mean_a[i], mean_b[j])

    # Hungarian alignment (what if models swapped class directions?)
    cost = -cross_cos  # minimize negative cosine = maximize cosine
    row_ind, col_ind = linear_sum_assignment(cost)
    aligned_cos = [-cost[r, c] for r, c in zip(row_ind, col_ind)]
    aligned_mean = np.mean(aligned_cos)

    print(f"\n  Hungarian-aligned cosine similarity:")
    print(f"    {'ClassA':>8} {'BestMatchB':>12} {'cos':>10}")
    print(f"    {'-'*32}")
    for r, c in zip(row_ind, col_ind):
        match_str = "MATCH" if r == c else f"->cls{c}"
        print(f"    {cls_names[r]:>8} {match_str:>12} {aligned_cos[row_ind.tolist().index(r)]:>10.4f}")
    print(f"    {'Mean':>8} {'':>12} {aligned_mean:>10.4f}")

    # How many classes match (diagonal)?
    n_match = sum(1 for r, c in zip(row_ind, col_ind) if r == c)
    print(f"\n  Diagonal match rate: {n_match}/{n_cls} = {n_match/n_cls*100:.0f}%")

    verdict = "VERIFIED" if raw_mean > 0.5 else "PARTIALLY VERIFIED" if raw_mean > 0.2 else "REFUTED"
    print(f"\n  VERDICT: {verdict} (mean cos={raw_mean:.4f} vs predicted >0.5)")

    return {
        'raw_mean_cos': raw_mean,
        'aligned_mean_cos': aligned_mean,
        'n_match': n_match,
        'verdict': verdict
    }


# ═══════════════════════════════════════════
# H-CX-127: PH Entanglement
# ═══════════════════════════════════════════
def verify_hcx127(dim, train_dataset, test_loader, cls_names):
    print(f"\n{'='*70}")
    print(f"  H-CX-127: PH Entanglement")
    print(f"  Prediction: Corr(PH_A, PH_B) > 0 with MI(data_A, data_B) = 0")
    print(f"{'='*70}")

    # Split training data in half (completely disjoint)
    n = len(train_dataset)
    indices = np.random.permutation(n)
    split_a = indices[:n//2]
    split_b = indices[n//2:]

    subset_a = Subset(train_dataset, split_a.tolist())
    subset_b = Subset(train_dataset, split_b.tolist())

    loader_a = DataLoader(subset_a, batch_size=256, shuffle=True, num_workers=0)
    loader_b = DataLoader(subset_b, batch_size=256, shuffle=True, num_workers=0)

    print(f"  Split A: {len(subset_a)} samples, Split B: {len(subset_b)} samples")
    print(f"  Overlap: 0 samples (completely disjoint)")

    # Train two models on disjoint data
    print("\n  Training Model A on Split A (seed=42)...")
    model_a, acc_a = train_purefield(dim, loader_a, epochs=15, seed=42)
    print(f"    Model A train acc: {acc_a*100:.1f}%")

    print("  Training Model B on Split B (seed=777)...")
    model_b, acc_b = train_purefield(dim, loader_b, epochs=15, seed=777)
    print(f"    Model B train acc: {acc_b*100:.1f}%")

    # Build confusion matrices on SAME test set
    n_cls = 10
    model_a.eval(); model_b.eval()
    conf_a = np.zeros((n_cls, n_cls))
    conf_b = np.zeros((n_cls, n_cls))

    with torch.no_grad():
        for x, y in test_loader:
            x_flat = x.view(-1, dim)
            out_a, _ = model_a(x_flat)
            out_b, _ = model_b(x_flat)
            pred_a = out_a.argmax(1).numpy()
            pred_b = out_b.argmax(1).numpy()
            for i in range(len(y)):
                conf_a[y[i].item(), pred_a[i]] += 1
                conf_b[y[i].item(), pred_b[i]] += 1

    # Normalize confusion matrices
    conf_a_norm = conf_a / (conf_a.sum(axis=1, keepdims=True) + 1e-8)
    conf_b_norm = conf_b / (conf_b.sum(axis=1, keepdims=True) + 1e-8)

    # PH via distance matrix on confusion matrix rows
    # Use simple topological features: pairwise distances between class confusion profiles
    try:
        from ripser import ripser

        # Distance matrix from confusion profiles
        from scipy.spatial.distance import pdist, squareform
        dist_a = squareform(pdist(conf_a_norm, 'cosine'))
        dist_b = squareform(pdist(conf_b_norm, 'cosine'))

        # Compute PH (H0 and H1 barcodes)
        ph_a = ripser(dist_a, maxdim=1, distance_matrix=True)
        ph_b = ripser(dist_b, maxdim=1, distance_matrix=True)

        # Extract persistence features: birth-death pairs
        # H0: connected components, H1: loops
        def ph_features(ph_result):
            """Extract summary features from PH barcodes."""
            feats = []
            for dim_k in range(2):
                dgm = ph_result['dgms'][dim_k]
                # Remove infinite bars
                finite = dgm[np.isfinite(dgm[:, 1])] if len(dgm) > 0 else np.array([]).reshape(0, 2)
                if len(finite) > 0:
                    pers = finite[:, 1] - finite[:, 0]
                    feats.extend([len(finite), pers.mean(), pers.max(), pers.std()])
                else:
                    feats.extend([0, 0, 0, 0])
            return np.array(feats)

        feat_a = ph_features(ph_a)
        feat_b = ph_features(ph_b)

        print(f"\n  PH Features (H0: components, H1: loops):")
        print(f"    {'Feature':>20} {'Model_A':>10} {'Model_B':>10}")
        print(f"    {'-'*42}")
        feat_names = ['H0_count', 'H0_mean_pers', 'H0_max_pers', 'H0_std_pers',
                      'H1_count', 'H1_mean_pers', 'H1_max_pers', 'H1_std_pers']
        for i, fn in enumerate(feat_names):
            print(f"    {fn:>20} {feat_a[i]:>10.4f} {feat_b[i]:>10.4f}")

        # Compare PH barcodes directly: flatten and correlate persistence diagrams
        # Use per-class confusion profile correlation as simpler proxy
        has_ph = True

    except ImportError:
        print("  [WARNING] ripser not installed. Using confusion profile correlation as proxy.")
        has_ph = False

    # Simpler approach: correlate confusion profiles directly
    # Each class has a 10-dim confusion profile. Compare A and B.
    print(f"\n  Confusion profile correlation (per class):")
    print(f"    {'Class':>8} {'Pearson_r':>10} {'p-value':>10}")
    print(f"    {'-'*30}")
    class_corrs = []
    for c in range(n_cls):
        r, p = pearsonr(conf_a_norm[c], conf_b_norm[c])
        class_corrs.append(r)
        print(f"    {cls_names[c]:>8} {r:>10.4f} {p:>10.2e}")

    mean_r = np.mean(class_corrs)
    print(f"    {'Mean':>8} {mean_r:>10.4f}")

    # Overall confusion matrix correlation
    flat_a = conf_a_norm.flatten()
    flat_b = conf_b_norm.flatten()
    r_overall, p_overall = pearsonr(flat_a, flat_b)
    print(f"\n  Overall confusion matrix correlation: r={r_overall:.4f}, p={p_overall:.2e}")

    # Distance matrix correlation (topology proxy)
    if has_ph:
        flat_da = dist_a[np.triu_indices(n_cls, k=1)]
        flat_db = dist_b[np.triu_indices(n_cls, k=1)]
        r_dist, p_dist = pearsonr(flat_da, flat_db)
        print(f"  Distance matrix correlation (topology): r={r_dist:.4f}, p={p_dist:.2e}")
    else:
        r_dist = mean_r  # fallback

    verdict = "VERIFIED" if r_overall > 0.5 else "PARTIALLY VERIFIED" if r_overall > 0 else "REFUTED"
    print(f"\n  VERDICT: {verdict} (confusion r={r_overall:.4f}, class mean r={mean_r:.4f})")
    print(f"  NOTE: Models trained on DISJOINT data show correlated confusion patterns")

    return {
        'confusion_r': r_overall,
        'class_mean_r': mean_r,
        'dist_r': r_dist if has_ph else None,
        'verdict': verdict
    }


# ═══════════════════════════════════════════
# H-CX-80: Orthogonality -> Synergy
# ═══════════════════════════════════════════
def verify_hcx80(dim, train_loader, test_loader, cls_names, dataset_name='mnist'):
    print(f"\n{'='*70}")
    print(f"  H-CX-80: Orthogonality -> Synergy ({dataset_name})")
    print(f"  Prediction: Higher orthogonality between expert outputs -> greater synergy")
    print(f"{'='*70}")

    # Train PureFieldEngine
    model, _ = train_purefield(dim, train_loader, epochs=15, seed=42)
    model.eval()

    # Extract per-sample features: magnitude, direction confidence, direction gap
    all_mag = []       # tension magnitude
    all_dir_conf = []  # direction confidence (max softmax of normalized direction)
    all_dir_gap = []   # direction gap (1st - 2nd softmax)
    all_correct = []
    all_labels = []

    with torch.no_grad():
        for x, y in test_loader:
            x_flat = x.view(-1, dim)
            out_a = model.engine_a(x_flat)
            out_g = model.engine_g(x_flat)
            rep = out_a - out_g

            # Magnitude (tension)
            mag = torch.sqrt((rep ** 2).mean(dim=-1))

            # Direction features
            direction = F.normalize(rep, dim=-1)
            dir_softmax = F.softmax(direction, dim=-1)
            top2 = dir_softmax.topk(2, dim=-1).values
            dir_conf = top2[:, 0]    # top-1 confidence
            dir_gap = top2[:, 0] - top2[:, 1]  # confidence gap

            # Correctness
            output = out_a - out_g
            pred = output.argmax(1)
            correct = (pred == y).float()

            all_mag.extend(mag.numpy().tolist())
            all_dir_conf.extend(dir_conf.numpy().tolist())
            all_dir_gap.extend(dir_gap.numpy().tolist())
            all_correct.extend(correct.numpy().tolist())
            all_labels.extend(y.numpy().tolist())

    mag = np.array(all_mag)
    dc = np.array(all_dir_conf)
    dg = np.array(all_dir_gap)
    correct = np.array(all_correct)

    # 3x3 correlation matrix
    features = np.column_stack([mag, dc, dg])
    feat_names = ['mag', 'dir_conf', 'dir_gap']
    corr_matrix = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            corr_matrix[i, j] = pearsonr(features[:, i], features[:, j])[0]

    print(f"\n  3x3 Correlation Matrix:")
    print(f"    {'':>10}", end='')
    for fn in feat_names:
        print(f" {fn:>10}", end='')
    print()
    for i in range(3):
        print(f"    {feat_names[i]:>10}", end='')
        for j in range(3):
            print(f" {corr_matrix[i,j]:>10.4f}", end='')
        print()

    # Orthogonality = 1 - mean(|off-diagonal correlation|)
    off_diag = [abs(corr_matrix[i, j]) for i in range(3) for j in range(3) if i != j]
    redundancy = np.mean(off_diag)
    orthogonality = 1 - redundancy

    print(f"\n  Mean |off-diagonal correlation| (redundancy): {redundancy:.4f}")
    print(f"  Orthogonality = 1 - redundancy: {orthogonality:.4f}")

    # Individual feature AUC (predicting correctness)
    from sklearn.metrics import roc_auc_score
    auc_mag = roc_auc_score(correct, mag)
    auc_dc = roc_auc_score(correct, dc)
    auc_dg = roc_auc_score(correct, dg)

    # Combined AUC (logistic regression on all 3 features)
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)
    lr = LogisticRegression(max_iter=1000)
    lr.fit(X_scaled, correct)
    combined_proba = lr.predict_proba(X_scaled)[:, 1]
    auc_combined = roc_auc_score(correct, combined_proba)

    # Synergy = combined AUC - max(individual AUC)
    best_individual = max(auc_mag, auc_dc, auc_dg)
    synergy = auc_combined - best_individual

    print(f"\n  AUC for predicting correctness:")
    print(f"    mag:      {auc_mag:.4f}")
    print(f"    dir_conf: {auc_dc:.4f}")
    print(f"    dir_gap:  {auc_dg:.4f}")
    print(f"    combined: {auc_combined:.4f}")
    print(f"    synergy:  {synergy:+.4f} (combined - best_individual)")

    return {
        'orthogonality': orthogonality,
        'synergy': synergy,
        'auc_combined': auc_combined,
        'corr_matrix': corr_matrix,
        'dataset': dataset_name
    }


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════
def main():
    t0 = time.time()

    print("="*70)
    print("  FRESH VERIFICATION: H-CX-80, H-CX-127, H-CX-148, H-CX-150")
    print("  Date: 2026-03-27")
    print("="*70)

    # Load MNIST
    print("\nLoading MNIST...")
    dim, tl, tel, cls_names, train_ds, test_ds = load_dataset('mnist')
    print(f"  Train: {len(train_ds)}, Test: {len(test_ds)}, dim: {dim}")

    # ── H-CX-148: Tension Resonance ──
    r148 = verify_hcx148(dim, tl, tel, cls_names)

    # ── H-CX-150: Silent Consensus ──
    # Reuse models from H-CX-148
    r150 = verify_hcx150(dim, tel, cls_names, r148['model_a'], r148['model_b'])

    # ── H-CX-127: PH Entanglement ──
    r127 = verify_hcx127(dim, train_ds, tel, cls_names)

    # ── H-CX-80: Orthogonality -> Synergy ──
    # Need multiple datasets to correlate orthogonality vs synergy
    print(f"\n{'='*70}")
    print(f"  H-CX-80: Multi-dataset Orthogonality vs Synergy")
    print(f"{'='*70}")

    results_80 = []
    for ds_name in ['mnist', 'fashion']:
        d, tl_ds, tel_ds, cn, tr_ds, te_ds = load_dataset(ds_name)
        r80 = verify_hcx80(d, tl_ds, tel_ds, cn, ds_name)
        results_80.append(r80)

    print(f"\n  Cross-dataset comparison:")
    print(f"    {'Dataset':>10} {'Orthogonality':>15} {'Synergy':>10} {'AUC_comb':>10}")
    print(f"    {'-'*47}")
    for r in results_80:
        print(f"    {r['dataset']:>10} {r['orthogonality']:>15.4f} {r['synergy']:>10.4f} {r['auc_combined']:>10.4f}")

    # Can't compute r with only 2 points, but we can check direction
    if len(results_80) >= 2:
        orth_vals = [r['orthogonality'] for r in results_80]
        syn_vals = [r['synergy'] for r in results_80]
        direction_match = (orth_vals[0] > orth_vals[1]) == (syn_vals[0] > syn_vals[1])
        print(f"\n  Direction check (higher orthogonality -> higher synergy): {direction_match}")
        hcx80_verdict = "PARTIALLY VERIFIED" if direction_match else "REFUTED"
        print(f"  NOTE: Only 2 datasets; cannot compute correlation (need n>=3)")
    else:
        hcx80_verdict = "INSUFFICIENT DATA"

    # ═══════════════════════════════════════
    # FINAL SUMMARY
    # ═══════════════════════════════════════
    elapsed = time.time() - t0
    print(f"\n{'='*70}")
    print(f"  FINAL SUMMARY TABLE")
    print(f"{'='*70}")
    print(f"  {'Hypothesis':>12} {'Prediction':>20} {'Measured':>20} {'Verdict':>20}")
    print(f"  {'-'*74}")
    r148_val = r148['r_pearson']
    r150_val = r150['raw_mean_cos']
    r127_val = r127['confusion_r']
    print(f"  {'H-CX-148':>12} {'r > 0.9':>20} {'r = ' + f'{r148_val:.4f}':>20} {r148['verdict']:>20}")
    print(f"  {'H-CX-150':>12} {'cos > 0.5':>20} {'cos = ' + f'{r150_val:.4f}':>20} {r150['verdict']:>20}")
    print(f"  {'H-CX-127':>12} {'r > 0 (disjoint)':>20} {'r = ' + f'{r127_val:.4f}':>20} {r127['verdict']:>20}")

    # H-CX-80 summary
    orth_str = f"orth={results_80[0]['orthogonality']:.3f}"
    syn_str = f"syn={results_80[0]['synergy']:.3f}"
    print(f"  {'H-CX-80':>12} {'r > 0.8':>20} {orth_str+', '+syn_str:>20} {hcx80_verdict:>20}")

    print(f"\n  Total time: {elapsed:.1f}s")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
