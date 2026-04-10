#!/usr/bin/env python3
"""Hypothesis 269: Does the repulsion vector A-G have directional meaning?

Experiment: Analyze the direction (sign pattern) of repulsion vectors
in RepulsionFieldQuad. For each test sample, extract out_a and out_g,
compute repulsion = out_a - out_g, and study:
  1. Per-digit direction profiles (mean repulsion vector, sign pattern)
  2. Direction consistency (intra-digit cosine similarity vs inter-digit)
  3. "Who wins" analysis (A-dominance vs G-dominance)
  4. Direction and correctness (correct vs wrong predictions)
  5. Principal direction of repulsion (first PC)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import time

from model_meta_engine import RepulsionFieldQuad
from model_utils import load_mnist, count_params


# ─────────────────────────────────────────
# Hook into RepulsionFieldQuad to extract engine outputs
# ─────────────────────────────────────────

class InstrumentedRepulsionFieldQuad(RepulsionFieldQuad):
    """Wraps RepulsionFieldQuad to expose individual engine outputs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_out_a = None
        self._last_out_g = None
        self._last_out_e = None
        self._last_out_f = None

    def forward(self, x):
        out_a = self.engine_a(x)
        out_e = self.engine_e(x)
        out_g = self.engine_g(x)
        out_f = self.engine_f(x)

        # Store for extraction
        self._last_out_a = out_a.detach()
        self._last_out_g = out_g.detach()
        self._last_out_e = out_e.detach()
        self._last_out_f = out_f.detach()

        # Replicate parent forward logic exactly
        repulsion_content = out_a - out_g
        repulsion_structure = out_e - out_f

        t_content = (repulsion_content ** 2).sum(dim=-1, keepdim=True)
        t_structure = (repulsion_structure ** 2).sum(dim=-1, keepdim=True)

        equilibrium = (out_a + out_e + out_g + out_f) / 4

        combined_repulsion = torch.cat([repulsion_content, repulsion_structure], dim=-1)
        field_direction = self.field_transform(combined_repulsion)

        total_tension = torch.sqrt((t_content * t_structure) + 1e-8)

        output = equilibrium + self.tension_scale * torch.sqrt(total_tension + 1e-8) * field_direction

        self.aux_loss = getattr(self.engine_g, 'entropy_loss', torch.tensor(0.0))

        with torch.no_grad():
            self.tension_content = t_content.mean().item()
            self.tension_structure = t_structure.mean().item()

        return (output, self.aux_loss)


# ─────────────────────────────────────────
# Training
# ─────────────────────────────────────────

def train_model(model, train_loader, epochs=10, lr=0.001):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        correct = 0
        total = 0

        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            logits, aux = model(X)
            loss = criterion(logits, y) + 0.1 * aux
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            correct += (logits.argmax(1) == y).sum().item()
            total += y.size(0)

        acc = correct / total
        avg_loss = total_loss / len(train_loader)
        print(f"  Epoch {epoch+1:>2}/{epochs}: Loss={avg_loss:.4f}, TrainAcc={acc*100:.1f}%")

    return model


# ─────────────────────────────────────────
# Extract engine outputs on test set
# ─────────────────────────────────────────

def extract_outputs(model, test_loader):
    """Run test set through model and collect engine outputs + predictions."""
    model.eval()
    all_out_a = []
    all_out_g = []
    all_out_e = []
    all_out_f = []
    all_labels = []
    all_preds = []

    with torch.no_grad():
        for X, y in test_loader:
            X = X.view(X.size(0), -1)
            logits, _ = model(X)
            preds = logits.argmax(1)

            all_out_a.append(model._last_out_a.cpu())
            all_out_g.append(model._last_out_g.cpu())
            all_out_e.append(model._last_out_e.cpu())
            all_out_f.append(model._last_out_f.cpu())
            all_labels.append(y.cpu())
            all_preds.append(preds.cpu())

    return {
        'out_a': torch.cat(all_out_a),      # (N, 10)
        'out_g': torch.cat(all_out_g),      # (N, 10)
        'out_e': torch.cat(all_out_e),      # (N, 10)
        'out_f': torch.cat(all_out_f),      # (N, 10)
        'labels': torch.cat(all_labels),    # (N,)
        'preds': torch.cat(all_preds),      # (N,)
    }


# ─────────────────────────────────────────
# Analysis functions
# ─────────────────────────────────────────

def analysis_1_direction_profiles(data):
    """Per-digit mean repulsion vector and sign pattern."""
    repulsion = data['out_a'] - data['out_g']  # (N, 10)
    labels = data['labels']

    print("\n" + "=" * 75)
    print("  ANALYSIS 1: Per-Digit Direction Profiles (A-G repulsion)")
    print("=" * 75)

    # Mean repulsion vector per digit
    mean_repulsions = {}
    for d in range(10):
        mask = labels == d
        if mask.sum() == 0:
            continue
        mean_rep = repulsion[mask].mean(dim=0).numpy()
        mean_repulsions[d] = mean_rep

    # Table of mean repulsion values
    print("\n  Mean repulsion vector per digit (A-G, 10 dims):")
    print(f"  {'Digit':>5}", end="")
    for dim in range(10):
        print(f"  {'d'+str(dim):>6}", end="")
    print()
    print("  " + "-" * 71)
    for d in range(10):
        print(f"  {d:>5}", end="")
        for dim in range(10):
            v = mean_repulsions[d][dim]
            print(f"  {v:>+6.2f}", end="")
        print()

    # ASCII heatmap: sign pattern
    print("\n  Sign pattern heatmap (+ = A dominates, - = G dominates, . = near zero):")
    print(f"  {'Digit':>5}", end="")
    for dim in range(10):
        print(f"  d{dim}", end="")
    print()
    print("  " + "-" * 41)
    for d in range(10):
        print(f"  {d:>5}", end="")
        for dim in range(10):
            v = mean_repulsions[d][dim]
            if abs(v) < 0.1:
                ch = "  . "
            elif v > 0:
                ch = "  + " if v < 0.5 else "  ++"
            else:
                ch = "  - " if v > -0.5 else "  --"
            print(ch, end="")
        print()

    return mean_repulsions


def analysis_2_direction_consistency(data, mean_repulsions):
    """Intra-digit vs inter-digit cosine similarity of repulsion vectors."""
    repulsion = data['out_a'] - data['out_g']
    labels = data['labels']

    print("\n" + "=" * 75)
    print("  ANALYSIS 2: Direction Consistency")
    print("=" * 75)

    # Intra-digit: cosine similarity of each sample's repulsion to its digit mean
    intra_sims = {}
    for d in range(10):
        mask = labels == d
        if mask.sum() < 2:
            continue
        reps = repulsion[mask]  # (n_d, 10)
        mean_vec = torch.tensor(mean_repulsions[d]).unsqueeze(0)  # (1, 10)

        # Cosine similarity to mean
        cos = F.cosine_similarity(reps, mean_vec.expand_as(reps), dim=1)
        intra_sims[d] = cos.numpy()

    # Inter-digit: cosine similarity between digit mean vectors
    mean_vecs = torch.tensor(np.stack([mean_repulsions[d] for d in range(10)]))  # (10, 10)

    inter_cos = np.zeros((10, 10))
    for i in range(10):
        for j in range(10):
            inter_cos[i, j] = F.cosine_similarity(
                mean_vecs[i].unsqueeze(0), mean_vecs[j].unsqueeze(0)
            ).item()

    print("\n  Intra-digit consistency (cosine sim to digit mean):")
    print(f"  {'Digit':>5} {'Mean cos':>9} {'Std':>7} {'Min':>7} {'Samples':>8}")
    print("  " + "-" * 40)
    for d in range(10):
        cs = intra_sims[d]
        print(f"  {d:>5} {cs.mean():>9.4f} {cs.std():>7.4f} {cs.min():>7.4f} {len(cs):>8}")

    print("\n  Inter-digit cosine similarity matrix (digit means):")
    print(f"  {'':>5}", end="")
    for j in range(10):
        print(f"  {j:>5}", end="")
    print()
    print("  " + "-" * 58)
    for i in range(10):
        print(f"  {i:>5}", end="")
        for j in range(10):
            v = inter_cos[i, j]
            print(f"  {v:>5.2f}", end="")
        print()

    # Summary stats
    mask_diag = ~np.eye(10, dtype=bool)
    off_diag = inter_cos[mask_diag]
    all_intra = np.concatenate([intra_sims[d] for d in range(10)])
    print(f"\n  Summary:")
    print(f"    Intra-digit mean cosine:  {all_intra.mean():.4f}")
    print(f"    Inter-digit mean cosine:  {off_diag.mean():.4f}")
    print(f"    Separation ratio:         {all_intra.mean() / (abs(off_diag.mean()) + 1e-8):.2f}x")

    return inter_cos


def analysis_3_who_wins(data):
    """A-dominance vs G-dominance per digit."""
    out_a = data['out_a']
    out_g = data['out_g']
    labels = data['labels']
    preds = data['preds']

    print("\n" + "=" * 75)
    print("  ANALYSIS 3: Who Wins (A vs G norm comparison)")
    print("=" * 75)

    norm_a = torch.norm(out_a, dim=1)  # (N,)
    norm_g = torch.norm(out_g, dim=1)  # (N,)
    a_wins = norm_a > norm_g

    correct = preds == labels

    print("\n  Per-digit A-dominance:")
    print(f"  {'Digit':>5} {'A wins%':>8} {'G wins%':>8} {'|A| mean':>9} {'|G| mean':>9} {'Ratio A/G':>10}")
    print("  " + "-" * 55)
    for d in range(10):
        mask = labels == d
        n = mask.sum().item()
        a_win_rate = a_wins[mask].float().mean().item()
        mean_a = norm_a[mask].mean().item()
        mean_g = norm_g[mask].mean().item()
        ratio = mean_a / (mean_g + 1e-8)
        print(f"  {d:>5} {a_win_rate*100:>7.1f}% {(1-a_win_rate)*100:>7.1f}% {mean_a:>9.3f} {mean_g:>9.3f} {ratio:>10.3f}")

    # Correlation with correctness
    a_win_correct = a_wins[correct].float().mean().item()
    a_win_wrong = a_wins[~correct].float().mean().item() if (~correct).sum() > 0 else float('nan')

    print(f"\n  Winner vs correctness:")
    print(f"    A-dominance when CORRECT: {a_win_correct*100:.1f}% ({correct.sum().item()} samples)")
    print(f"    A-dominance when WRONG:   {a_win_wrong*100:.1f}% ({(~correct).sum().item()} samples)")

    return a_wins


def analysis_4_direction_and_correctness(data, mean_repulsions):
    """Compare repulsion direction for correct vs wrong predictions."""
    repulsion = data['out_a'] - data['out_g']
    labels = data['labels']
    preds = data['preds']
    correct = preds == labels

    print("\n" + "=" * 75)
    print("  ANALYSIS 4: Direction and Correctness")
    print("=" * 75)

    # Per-digit: mean repulsion for correct vs wrong
    print("\n  Mean repulsion norm by correctness per digit:")
    print(f"  {'Digit':>5} {'Correct norm':>13} {'Wrong norm':>11} {'Cos(C,W)':>9} {'n_wrong':>8}")
    print("  " + "-" * 50)

    cos_correct_wrong = []
    for d in range(10):
        mask_d = labels == d
        mask_c = mask_d & correct
        mask_w = mask_d & ~correct

        rep_c = repulsion[mask_c]
        rep_w = repulsion[mask_w]

        norm_c = torch.norm(rep_c, dim=1).mean().item() if mask_c.sum() > 0 else 0
        norm_w = torch.norm(rep_w, dim=1).mean().item() if mask_w.sum() > 0 else 0

        if mask_c.sum() > 0 and mask_w.sum() > 0:
            mean_c = rep_c.mean(dim=0).unsqueeze(0)
            mean_w = rep_w.mean(dim=0).unsqueeze(0)
            cos_cw = F.cosine_similarity(mean_c, mean_w).item()
        else:
            cos_cw = float('nan')

        cos_correct_wrong.append(cos_cw)
        print(f"  {d:>5} {norm_c:>13.4f} {norm_w:>11.4f} {cos_cw:>9.4f} {mask_w.sum().item():>8}")

    valid_cos = [c for c in cos_correct_wrong if not np.isnan(c)]
    if valid_cos:
        print(f"\n  Mean cos(correct, wrong) across digits: {np.mean(valid_cos):.4f}")
        print(f"  -> 1.0 = same direction, -1.0 = opposite, 0 = orthogonal")

    # Does repulsion flip for errors?
    print("\n  Direction flip analysis:")
    print("    For each wrong prediction, check if repulsion points away from digit mean")
    flip_count = 0
    total_wrong = 0
    for d in range(10):
        mask_d = labels == d
        mask_w = mask_d & ~correct
        if mask_w.sum() == 0:
            continue
        mean_vec = torch.tensor(mean_repulsions[d]).unsqueeze(0)
        wrong_reps = repulsion[mask_w]
        cos = F.cosine_similarity(wrong_reps, mean_vec.expand_as(wrong_reps), dim=1)
        flip_count += (cos < 0).sum().item()
        total_wrong += mask_w.sum().item()

    if total_wrong > 0:
        print(f"    Wrong samples with flipped direction (cos < 0): {flip_count}/{total_wrong} ({flip_count/total_wrong*100:.1f}%)")
    else:
        print(f"    No wrong predictions to analyze.")


def analysis_5_principal_direction(data):
    """PCA on repulsion vectors: find the principal axis of force."""
    repulsion = data['out_a'] - data['out_g']  # (N, 10)
    labels = data['labels']

    print("\n" + "=" * 75)
    print("  ANALYSIS 5: Principal Direction of Repulsion (PCA)")
    print("=" * 75)

    rep_np = repulsion.numpy()
    # Center
    rep_centered = rep_np - rep_np.mean(axis=0, keepdims=True)

    # SVD for PCA
    U, S, Vt = np.linalg.svd(rep_centered, full_matrices=False)
    explained_var = S ** 2 / (S ** 2).sum()

    print("\n  Explained variance by principal components:")
    cumvar = 0
    for i in range(min(10, len(S))):
        cumvar += explained_var[i]
        bar = "#" * int(explained_var[i] * 50)
        print(f"    PC{i}: {explained_var[i]*100:>5.1f}% (cum: {cumvar*100:>5.1f}%)  {bar}")

    # First PC direction
    pc1 = Vt[0]
    print(f"\n  First principal component (the 'front-to-back' axis):")
    print(f"    PC1 = [", end="")
    for i, v in enumerate(pc1):
        if i > 0:
            print(", ", end="")
        print(f"{v:>+.3f}", end="")
    print("]")

    # Which dimension does PC1 load on most?
    dominant_dim = np.argmax(np.abs(pc1))
    print(f"    Dominant dimension: d{dominant_dim} (loading = {pc1[dominant_dim]:+.3f})")

    # Per-digit projection onto PC1
    projections = rep_centered @ pc1  # (N,)
    print(f"\n  Per-digit projection onto PC1:")
    print(f"  {'Digit':>5} {'Mean proj':>10} {'Std':>8} {'Direction':>10}")
    print("  " + "-" * 35)
    for d in range(10):
        mask = (labels == d).numpy()
        proj_d = projections[mask]
        direction = "--->" if proj_d.mean() > 0 else "<---"
        print(f"  {d:>5} {proj_d.mean():>+10.4f} {proj_d.std():>8.4f} {direction:>10}")

    # Consistency: per-digit PC1 cosine similarity to global PC1
    print(f"\n  Per-digit first PC vs global PC1 (cosine similarity):")
    print(f"  {'Digit':>5} {'cos(PC1_d, PC1_global)':>24} {'Consistent?':>12}")
    print("  " + "-" * 45)
    for d in range(10):
        mask = (labels == d).numpy()
        rep_d = rep_centered[mask]
        if rep_d.shape[0] < 2:
            continue
        _, _, Vt_d = np.linalg.svd(rep_d, full_matrices=False)
        pc1_d = Vt_d[0]
        cos_sim = np.dot(pc1_d, pc1) / (np.linalg.norm(pc1_d) * np.linalg.norm(pc1) + 1e-8)
        consistent = "YES" if abs(cos_sim) > 0.5 else "no"
        print(f"  {d:>5} {cos_sim:>+24.4f} {consistent:>12}")

    return pc1, explained_var


def analysis_structure_repulsion(data):
    """Bonus: brief analysis of E-F (structure axis) repulsion."""
    repulsion_s = data['out_e'] - data['out_f']  # (N, 10)
    repulsion_c = data['out_a'] - data['out_g']  # (N, 10)
    labels = data['labels']

    print("\n" + "=" * 75)
    print("  BONUS: Content (A-G) vs Structure (E-F) axis alignment")
    print("=" * 75)

    # Per-digit cosine between content and structure repulsion
    print(f"\n  Per-digit cosine(A-G, E-F):")
    print(f"  {'Digit':>5} {'cos(content, structure)':>24} {'Relationship':>14}")
    print("  " + "-" * 48)
    for d in range(10):
        mask = labels == d
        rc = repulsion_c[mask]
        rs = repulsion_s[mask]
        cos = F.cosine_similarity(rc, rs, dim=1).mean().item()
        if cos > 0.3:
            rel = "ALIGNED"
        elif cos < -0.3:
            rel = "OPPOSED"
        else:
            rel = "orthogonal"
        print(f"  {d:>5} {cos:>+24.4f} {rel:>14}")

    # Global alignment
    cos_global = F.cosine_similarity(repulsion_c, repulsion_s, dim=1).mean().item()
    print(f"\n  Global content-structure alignment: cos = {cos_global:+.4f}")
    if abs(cos_global) < 0.1:
        print("  -> The two axes are approximately ORTHOGONAL (independent forces)")
    elif cos_global > 0.3:
        print("  -> The two axes are ALIGNED (reinforcing)")
    elif cos_global < -0.3:
        print("  -> The two axes are OPPOSED (competing)")
    else:
        print("  -> Weak relationship")


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────

def main():
    print("=" * 75)
    print("  HYPOTHESIS 269: Does the Repulsion Vector A-G Have Directional Meaning?")
    print("  RepulsionFieldQuad force direction analysis")
    print("=" * 75)

    # Load data
    print("\n[1] Loading MNIST...")
    train_loader, test_loader = load_mnist(batch_size=128)

    # Create instrumented model
    print("[2] Creating InstrumentedRepulsionFieldQuad...")
    model = InstrumentedRepulsionFieldQuad(input_dim=784, hidden_dim=48, output_dim=10)
    n_params = count_params(model)
    print(f"    Parameters: {n_params:,}")

    # Train
    print(f"\n[3] Training for 10 epochs...")
    t0 = time.time()
    model = train_model(model, train_loader, epochs=10, lr=0.001)
    train_time = time.time() - t0
    print(f"    Training time: {train_time:.1f}s")

    # Test accuracy
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for X, y in test_loader:
            X = X.view(X.size(0), -1)
            logits, _ = model(X)
            correct += (logits.argmax(1) == y).sum().item()
            total += y.size(0)
    test_acc = correct / total
    print(f"\n    Test accuracy: {test_acc*100:.2f}%")

    # Extract outputs
    print("\n[4] Extracting engine outputs on test set...")
    data = extract_outputs(model, test_loader)
    print(f"    Samples: {data['labels'].shape[0]}")
    print(f"    Correct: {(data['preds'] == data['labels']).sum().item()}")
    print(f"    Wrong:   {(data['preds'] != data['labels']).sum().item()}")

    # Run analyses
    print("\n[5] Running analyses...")
    mean_repulsions = analysis_1_direction_profiles(data)
    inter_cos = analysis_2_direction_consistency(data, mean_repulsions)
    a_wins = analysis_3_who_wins(data)
    analysis_4_direction_and_correctness(data, mean_repulsions)
    pc1, explained_var = analysis_5_principal_direction(data)
    analysis_structure_repulsion(data)

    # Final summary
    print("\n" + "=" * 75)
    print("  SUMMARY: Hypothesis 269 — Repulsion Vector Direction")
    print("=" * 75)
    print(f"""
  Model:         RepulsionFieldQuad (instrumented)
  Test accuracy:  {test_acc*100:.2f}%
  Parameters:     {n_params:,}

  Key findings:
    1. PC1 explains {explained_var[0]*100:.1f}% of repulsion variance
    2. Dominant PC1 dimension: d{np.argmax(np.abs(pc1))} (loading={pc1[np.argmax(np.abs(pc1))]:+.3f})
    3. Intra-digit consistency vs inter-digit separation measured
    4. Direction flips analyzed for error cases

  Interpretation:
    - If PC1 variance >> others: repulsion has a clear principal axis
    - If intra > inter consistency: direction encodes digit identity
    - If direction flips on errors: repulsion direction = confidence signal
""")


if __name__ == "__main__":
    main()
