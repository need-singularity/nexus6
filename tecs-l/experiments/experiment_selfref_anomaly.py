#!/usr/bin/env python3
"""Self-Referential Anomaly Detection

Concept: Feed the model's own tension back as additional input features.
- Round 1: model sees x -> produces tension T1
- Round 2: model sees [x, T1] -> produces tension T2
- Round 3: model sees [x, T1, T2] -> produces tension T3

Key insight: Models must be trained WITH self-referential loop active,
so they learn to use the tension feedback. Training on zero-padded inputs
then testing with tension feedback is meaningless.

Architecture:
  - Base autoencoder: 30-dim input -> reconstruct 30-dim
  - Tension processor: separate small net that takes [T_prev] -> modulates hidden
  - During training: run 3-round self-ref loop, backprop through all rounds
  - Score at each round = reconstruction_error per sample

Dataset: Breast Cancer (sklearn), 30 features
5 trials, AUROC per round, ASCII graph.
"""

import sys
import os
import copy
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score


# ── Model ──────────────────────────────────────────────

class SelfRefAutoencoder(nn.Module):
    """Autoencoder with self-referential tension feedback.

    Round 1: encode(x) -> decode -> recon_err T1
    Round 2: encode(x, modulated by T1) -> decode -> recon_err T2
    Round 3: encode(x, modulated by T1,T2) -> decode -> recon_err T3

    The tension_gate modulates the hidden representation based on
    previous tension values, allowing the model to "pay more attention"
    to samples it found difficult.
    """

    def __init__(self, input_dim=30, hidden_dim=64, latent_dim=16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, latent_dim),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
        )
        # Tension gate: takes up to 2 previous tensions -> modulates latent
        self.tension_gate = nn.Sequential(
            nn.Linear(2, latent_dim),
            nn.Sigmoid(),  # Multiplicative gating
        )

    def forward_one_round(self, x, prev_tensions):
        """Single forward pass with tension conditioning.

        Args:
            x: (N, 30) input features
            prev_tensions: (N, 2) previous tension values [T_{r-1}, T_{r-2}]
                          zeros if no previous tensions
        Returns:
            recon: (N, 30) reconstruction
            tension: (N,) per-sample reconstruction error
        """
        z = self.encoder(x)
        # Modulate latent by tension gate
        gate = self.tension_gate(prev_tensions)
        z_modulated = z * gate
        recon = self.decoder(z_modulated)
        tension = ((recon - x) ** 2).mean(dim=-1)
        return recon, tension

    def forward_selfref(self, x, n_rounds=3):
        """Full self-referential forward pass.

        Returns list of tensions [T1, T2, T3].
        """
        N = x.shape[0]
        tensions = []
        prev_t = torch.zeros(N, 2, device=x.device)

        for r in range(n_rounds):
            recon, t = self.forward_one_round(x, prev_t)
            tensions.append(t)
            # Shift tension history
            if r == 0:
                prev_t = torch.stack([t, torch.zeros_like(t)], dim=1)
            else:
                prev_t = torch.stack([t, tensions[r - 1]], dim=1)

        return tensions


def mitosis(parent, noise_scale=0.02):
    """Split parent into two children with perturbations."""
    child_a = copy.deepcopy(parent)
    child_b = copy.deepcopy(parent)
    with torch.no_grad():
        for p in child_a.parameters():
            p.add_(torch.randn_like(p) * noise_scale)
        for p in child_b.parameters():
            p.add_(torch.randn_like(p) * noise_scale)
    return child_a, child_b


# ── Training ───────────────────────────────────────────

def train_selfref(model, X_train, epochs, n_rounds=3, lr=1e-3):
    """Train with self-referential loop active.

    Loss = sum of reconstruction errors across all rounds.
    This teaches the model to USE tension feedback.
    """
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    losses = []
    for ep in range(epochs):
        model.train()
        opt.zero_grad()
        tensions = model.forward_selfref(X_train, n_rounds=n_rounds)
        # Loss = mean tension across all rounds (encourages all rounds to reconstruct well)
        loss = sum(t.mean() for t in tensions) / n_rounds
        loss.backward()
        opt.step()
        losses.append(loss.item())
    return losses


# ── Inter-Model Scoring ────────────────────────────────

def inter_selfref_scores(model_a, model_b, X_test, n_rounds=3):
    """Compute per-round anomaly scores using inter-model tension.

    For each round r:
      score_r = |tension_a_r - tension_b_r| + (tension_a_r + tension_b_r) / 2

    The inter-model disagreement on "how difficult" a sample is
    should be higher for anomalies.
    """
    model_a.eval()
    model_b.eval()
    with torch.no_grad():
        tensions_a = model_a.forward_selfref(X_test, n_rounds=n_rounds)
        tensions_b = model_b.forward_selfref(X_test, n_rounds=n_rounds)

    scores = []
    for r in range(n_rounds):
        ta = tensions_a[r]
        tb = tensions_b[r]
        # Combined: average recon error + inter-model disagreement
        avg_recon = (ta + tb) / 2.0
        disagree = (ta - tb).abs()
        score = avg_recon + disagree
        scores.append(score.numpy())

    return scores


# ── Also test single-model (no mitosis) scores ────────

def single_model_scores(model, X_test, n_rounds=3):
    """Anomaly scores from a single model's self-referential loop."""
    model.eval()
    with torch.no_grad():
        tensions = model.forward_selfref(X_test, n_rounds=n_rounds)
    return [t.numpy() for t in tensions]


# ── Baseline: same architecture, no self-ref ──────────

def train_baseline(model, X_train, epochs, lr=1e-3):
    """Train WITHOUT self-referential loop (always zero tension input)."""
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    N = X_train.shape[0]
    prev_t = torch.zeros(N, 2)
    for ep in range(epochs):
        model.train()
        opt.zero_grad()
        recon, tension = model.forward_one_round(X_train, prev_t)
        loss = tension.mean()
        loss.backward()
        opt.step()
    return model


def baseline_scores(model_a, model_b, X_test):
    """Single-round scores (no self-ref)."""
    model_a.eval()
    model_b.eval()
    N = X_test.shape[0]
    prev_t = torch.zeros(N, 2)
    with torch.no_grad():
        _, ta = model_a.forward_one_round(X_test, prev_t)
        _, tb = model_b.forward_one_round(X_test, prev_t)
    score = (ta + tb) / 2.0 + (ta - tb).abs()
    return score.numpy()


# ── Main Experiment ────────────────────────────────────

def run_experiment():
    print("=" * 70)
    print("  SELF-REFERENTIAL ANOMALY DETECTION")
    print("  Train WITH self-ref loop -> does iterative tension improve AUROC?")
    print("=" * 70)

    data = load_breast_cancer()
    X_raw, y = data.data, data.target

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    X_normal = X_scaled[y == 1]
    X_anomaly = X_scaled[y == 0]

    print(f"\nDataset: Breast Cancer (30 features)")
    print(f"  Normal (benign):   {len(X_normal)}")
    print(f"  Anomaly (malign):  {len(X_anomaly)}")
    print(f"\nArchitecture:")
    print(f"  - SelfRefAutoencoder: enc(30->64->16) + tension_gate(2->16) + dec(16->64->30)")
    print(f"  - Tension gate: sigmoid modulation of latent by previous tensions")
    print(f"  - Training: 3-round self-ref loop, backprop through all rounds")
    print(f"  - Parent: 50 epochs, Children: 30 epochs each after mitosis")
    print(f"  - Score = avg_recon_error + inter_model_disagreement")

    N_TRIALS = 5
    N_ROUNDS = 3

    # Storage
    selfref_aurocs = {r: [] for r in range(1, N_ROUNDS + 1)}
    baseline_aurocs = []
    single_aurocs = {r: [] for r in range(1, N_ROUNDS + 1)}

    detail_last = None

    for trial in range(N_TRIALS):
        seed = trial * 7 + 42
        torch.manual_seed(seed)
        np.random.seed(seed)

        # Split
        idx = np.random.permutation(len(X_normal))
        n_train = int(0.7 * len(X_normal))
        X_train_np = X_normal[idx[:n_train]]
        X_test_normal_np = X_normal[idx[n_train:]]

        X_test_np = np.vstack([X_test_normal_np, X_anomaly])
        y_test = np.array([0] * len(X_test_normal_np) + [1] * len(X_anomaly))

        X_train_t = torch.FloatTensor(X_train_np)
        X_test_t = torch.FloatTensor(X_test_np)

        # ── Self-Referential Model ──
        parent_sr = SelfRefAutoencoder(input_dim=30, hidden_dim=64, latent_dim=16)
        train_selfref(parent_sr, X_train_t, epochs=50, n_rounds=N_ROUNDS)

        child_a, child_b = mitosis(parent_sr, noise_scale=0.02)
        train_selfref(child_a, X_train_t, epochs=30, n_rounds=N_ROUNDS)
        train_selfref(child_b, X_train_t, epochs=30, n_rounds=N_ROUNDS)

        scores_sr = inter_selfref_scores(child_a, child_b, X_test_t, n_rounds=N_ROUNDS)

        # Also get single-model scores (parent only, no mitosis)
        scores_single = single_model_scores(parent_sr, X_test_t, n_rounds=N_ROUNDS)

        # ── Baseline (no self-ref) ──
        torch.manual_seed(seed)  # Same init
        parent_bl = SelfRefAutoencoder(input_dim=30, hidden_dim=64, latent_dim=16)
        train_baseline(parent_bl, X_train_t, epochs=50)

        child_bl_a, child_bl_b = mitosis(parent_bl, noise_scale=0.02)
        train_baseline(child_bl_a, X_train_t, epochs=30)
        train_baseline(child_bl_b, X_train_t, epochs=30)

        bl_score = baseline_scores(child_bl_a, child_bl_b, X_test_t)
        bl_auc = roc_auc_score(y_test, bl_score)
        baseline_aurocs.append(bl_auc)

        # Compute AUROCs
        aucs_sr = []
        aucs_single = []
        for r in range(N_ROUNDS):
            auc_sr = roc_auc_score(y_test, scores_sr[r])
            selfref_aurocs[r + 1].append(auc_sr)
            aucs_sr.append(auc_sr)

            auc_s = roc_auc_score(y_test, scores_single[r])
            single_aurocs[r + 1].append(auc_s)
            aucs_single.append(auc_s)

        n_normal_test = len(X_test_normal_np)
        if trial == N_TRIALS - 1:
            detail_last = (scores_sr, scores_single, bl_score, n_normal_test, y_test)

        print(f"\n  Trial {trial + 1}:")
        print(f"    Baseline (no self-ref):  {bl_auc:.4f}")
        print(f"    Self-ref T1={aucs_sr[0]:.4f}  T2={aucs_sr[1]:.4f}  T3={aucs_sr[2]:.4f}"
              f"  delta(T3-T1)={aucs_sr[2] - aucs_sr[0]:+.4f}")
        print(f"    Single   T1={aucs_single[0]:.4f}  T2={aucs_single[1]:.4f}  T3={aucs_single[2]:.4f}")

    # ── Results Table ──────────────────────────────────

    print("\n" + "=" * 70)
    print("  RESULTS SUMMARY")
    print("=" * 70)

    bl_mean = np.mean(baseline_aurocs)
    bl_std = np.std(baseline_aurocs)

    print(f"\n{'Method':<22} {'Mean AUROC':<14} {'Std':<10} {'Trials'}")
    print("-" * 70)
    print(f"  {'Baseline (no SR)':<20} {bl_mean:<14.4f} {bl_std:<10.4f} "
          f"{'  '.join(f'{v:.4f}' for v in baseline_aurocs)}")

    means_sr = {}
    stds_sr = {}
    means_s = {}
    stds_s = {}
    for r in range(1, N_ROUNDS + 1):
        means_sr[r] = np.mean(selfref_aurocs[r])
        stds_sr[r] = np.std(selfref_aurocs[r])
        means_s[r] = np.mean(single_aurocs[r])
        stds_s[r] = np.std(single_aurocs[r])

        print(f"  {'SR+Mitosis T' + str(r):<20} {means_sr[r]:<14.4f} {stds_sr[r]:<10.4f} "
              f"{'  '.join(f'{v:.4f}' for v in selfref_aurocs[r])}")

    print()
    for r in range(1, N_ROUNDS + 1):
        print(f"  {'Single T' + str(r):<20} {means_s[r]:<14.4f} {stds_s[r]:<10.4f} "
              f"{'  '.join(f'{v:.4f}' for v in single_aurocs[r])}")

    # ── Deltas ─────────────────────────────────────────

    print(f"\n  Key Comparisons:")
    d_sr_bl = means_sr[3] - bl_mean
    d_sr_t3_t1 = means_sr[3] - means_sr[1]
    d_s_t3_t1 = means_s[3] - means_s[1]
    print(f"    SR T3 vs Baseline:    {d_sr_bl:+.4f}")
    print(f"    SR T3 vs SR T1:       {d_sr_t3_t1:+.4f}")
    print(f"    Single T3 vs T1:      {d_s_t3_t1:+.4f}")

    # ── ASCII Bar Chart ────────────────────────────────

    print("\n" + "=" * 70)
    print("  ASCII: AUROC Comparison")
    print("=" * 70)

    all_means = [bl_mean] + [means_sr[r] for r in range(1, 4)] + [means_s[r] for r in range(1, 4)]
    all_stds_list = [bl_std] + [stds_sr[r] for r in range(1, 4)] + [stds_s[r] for r in range(1, 4)]
    labels = ["Baseline", "SR+Mit T1", "SR+Mit T2", "SR+Mit T3",
              "Single T1", "Single T2", "Single T3"]

    lo = max(0.4, min(m - s for m, s in zip(all_means, all_stds_list)) - 0.03)
    hi = min(1.0, max(m + s for m, s in zip(all_means, all_stds_list)) + 0.03)
    span = hi - lo
    BAR_W = 45

    for i, (label, m, s) in enumerate(zip(labels, all_means, all_stds_list)):
        bar_len = int((m - lo) / span * BAR_W) if span > 0 else 20
        bar_len = max(1, min(BAR_W, bar_len))
        err_hi = int((m + s - lo) / span * BAR_W)
        err_hi = min(BAR_W, err_hi)

        bar = '█' * bar_len + '░' * max(0, err_hi - bar_len)
        pad = ' ' * max(0, BAR_W - len(bar))
        marker = " <--" if label == "SR+Mit T3" else ""
        print(f"  {label:<12}|{bar}{pad}| {m:.4f}{marker}")

    print(f"  {'':>12}+{'─' * BAR_W}+")
    print(f"  {'':>12} {lo:.2f}{' ' * (BAR_W - 8)}{hi:.2f}")

    # ── Per-Trial Trajectory ───────────────────────────

    print("\n" + "=" * 70)
    print("  TRAJECTORY: Self-Ref+Mitosis AUROC per trial")
    print("=" * 70)

    for trial in range(N_TRIALS):
        bl = baseline_aurocs[trial]
        vals = [selfref_aurocs[r][trial] for r in range(1, 4)]
        arrows = []
        for i in range(1, 3):
            d = vals[i] - vals[i - 1]
            if d > 0.003:
                arrows.append("^")
            elif d < -0.003:
                arrows.append("v")
            else:
                arrows.append("=")
        net = vals[2] - vals[0]
        vs_bl = vals[2] - bl
        print(f"  Trial {trial + 1}: BL={bl:.4f} | T1={vals[0]:.4f} {arrows[0]} "
              f"T2={vals[1]:.4f} {arrows[1]} T3={vals[2]:.4f} "
              f" net={net:+.4f}  vs_BL={vs_bl:+.4f}")

    # ── Tension Statistics ─────────────────────────────

    print("\n" + "=" * 70)
    print("  TENSION STATISTICS (last trial)")
    print("=" * 70)

    scores_sr, scores_single, bl_score, n_normal_test, y_test = detail_last

    print(f"\n  Self-Ref + Mitosis:")
    print(f"  {'Round':<8} {'Normal':<20} {'Anomaly':<20} {'Sep (sigma)':<14} {'Ratio'}")
    print("  " + "-" * 68)
    for r in range(N_ROUNDS):
        t = scores_sr[r]
        tn = t[:n_normal_test]
        ta = t[n_normal_test:]
        sep = (np.mean(ta) - np.mean(tn)) / (np.std(tn) + 1e-8)
        ratio = np.mean(ta) / (np.mean(tn) + 1e-8)
        print(f"  T{r + 1:<5} {np.mean(tn):.6f}+/-{np.std(tn):.4f}  "
              f"{np.mean(ta):.6f}+/-{np.std(ta):.4f}  {sep:>8.2f}        {ratio:.2f}x")

    # Separation trend
    seps = []
    for r in range(N_ROUNDS):
        t = scores_sr[r]
        tn = t[:n_normal_test]
        ta = t[n_normal_test:]
        seps.append((np.mean(ta) - np.mean(tn)) / (np.std(tn) + 1e-8))

    print(f"\n  Separation trend: {' -> '.join(f'{s:.2f}' for s in seps)} sigma")
    if seps[-1] > seps[0]:
        print(f"  Self-ref INCREASES class separation by {seps[-1] - seps[0]:.2f} sigma")
    else:
        print(f"  Self-ref decreases class separation by {seps[0] - seps[-1]:.2f} sigma")

    # ── Histogram ──────────────────────────────────────

    print("\n" + "=" * 70)
    print("  HISTOGRAM: Score distributions (last trial)")
    print("=" * 70)

    for rnd, label in [(0, "T1 (Self-Ref+Mitosis)"), (2, "T3 (Self-Ref+Mitosis)")]:
        t = scores_sr[rnd]
        tn = t[:n_normal_test]
        ta = t[n_normal_test:]

        all_t = np.concatenate([tn, ta])
        bins = np.linspace(np.percentile(all_t, 1), np.percentile(all_t, 99), 11)
        h_n, _ = np.histogram(tn, bins=bins)
        h_a, _ = np.histogram(ta, bins=bins)

        max_h = max(max(h_n), max(h_a), 1)
        scale = 30.0 / max_h

        print(f"\n  {label}:")
        for i in range(len(bins) - 1):
            bn = int(h_n[i] * scale)
            ba = int(h_a[i] * scale)
            print(f"  {bins[i]:8.4f} |{'N' * bn}{'A' * ba}")
        print(f"  {bins[-1]:8.4f} |")

    # ── Final Verdict ──────────────────────────────────

    print("\n" + "=" * 70)
    print("  FINAL VERDICT")
    print("=" * 70)

    # Does self-ref improve over baseline?
    if d_sr_bl > 0.005:
        print(f"  [1] Self-ref+Mitosis T3 vs Baseline: BETTER by {d_sr_bl:+.4f} AUROC")
    elif d_sr_bl < -0.005:
        print(f"  [1] Self-ref+Mitosis T3 vs Baseline: WORSE by {d_sr_bl:+.4f} AUROC")
    else:
        print(f"  [1] Self-ref+Mitosis T3 vs Baseline: SIMILAR ({d_sr_bl:+.4f} AUROC)")

    # Does iteration improve within self-ref?
    if d_sr_t3_t1 > 0.003:
        print(f"  [2] Self-ref T3 vs T1: IMPROVES by {d_sr_t3_t1:+.4f} (iteration helps)")
    elif d_sr_t3_t1 < -0.003:
        print(f"  [2] Self-ref T3 vs T1: DEGRADES by {d_sr_t3_t1:+.4f} (iteration hurts)")
    else:
        print(f"  [2] Self-ref T3 vs T1: STABLE ({d_sr_t3_t1:+.4f}, iteration is neutral)")

    # Count improvements
    improved_vs_bl = sum(1 for t in range(N_TRIALS)
                         if selfref_aurocs[3][t] > baseline_aurocs[t] + 0.001)
    improved_t3_t1 = sum(1 for t in range(N_TRIALS)
                         if selfref_aurocs[3][t] > selfref_aurocs[1][t] + 0.001)
    print(f"\n  T3 beats Baseline: {improved_vs_bl}/{N_TRIALS} trials")
    print(f"  T3 beats T1:       {improved_t3_t1}/{N_TRIALS} trials")
    print("=" * 70)


if __name__ == "__main__":
    run_experiment()
