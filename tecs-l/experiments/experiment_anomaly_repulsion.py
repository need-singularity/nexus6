#!/usr/bin/env python3
"""Experiment: Repulsion Field for ANOMALY DETECTION

Hypothesis: High tension = anomaly (engines disagree strongly on unusual inputs).

Setup:
  - Generate normal data (2 clusters via make_blobs, input_dim=20)
  - Generate outlier data (uniform random in expanded range)
  - Train RepulsionField on normal data only (autoencoder-style reconstruction)
  - At test time, measure tension for normal vs anomaly samples
  - If tension is higher for anomalies -> repulsion field is a natural anomaly detector

Metric: AUROC using tension as anomaly score.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.datasets import make_blobs
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split


# ─────────────────────────────────────────
# Repulsion Field Engine (self-contained)
# ─────────────────────────────────────────

class PoleNetwork(nn.Module):
    """One pole of the repulsion field."""
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.net(x)


class RepulsionFieldAutoencoder(nn.Module):
    """Repulsion field for reconstruction (anomaly detection).

    Two poles (engines) process input independently.
    Tension = squared difference between pole outputs.
    Final reconstruction = equilibrium + field_transform(repulsion).

    On normal data: poles learn to agree -> low tension.
    On anomalies: poles disagree -> high tension.
    """
    def __init__(self, input_dim=20, hidden_dim=64, latent_dim=32):
        super().__init__()
        # Two poles with different initializations (they will diverge in behavior)
        self.pole_plus = PoleNetwork(input_dim, hidden_dim, latent_dim)
        self.pole_minus = PoleNetwork(input_dim, hidden_dim, latent_dim)

        # Field transform: converts repulsion direction into reconstruction signal
        self.field_transform = nn.Sequential(
            nn.Linear(latent_dim, latent_dim),
            nn.Tanh(),
        )

        # Decoder: from latent back to input space
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
        )

        # Tension scale (learnable, initialized to 1/3 per project convention)
        self.tension_scale = nn.Parameter(torch.tensor(1.0 / 3.0))

        # Repulsion regularizer weight
        self.repulsion_weight = 0.1

    def forward(self, x):
        out_plus = self.pole_plus(x)
        out_minus = self.pole_minus(x)

        # Core repulsion field computation
        repulsion = out_plus - out_minus
        tension = (repulsion ** 2).sum(dim=-1, keepdim=True)  # scalar per sample

        equilibrium = (out_plus + out_minus) / 2.0
        field_direction = self.field_transform(repulsion)
        latent = equilibrium + self.tension_scale * torch.sqrt(tension + 1e-8) * field_direction

        # Decode
        reconstruction = self.decoder(latent)

        return reconstruction, tension.squeeze(-1)

    def compute_loss(self, x):
        recon, tension = self.forward(x)
        recon_loss = nn.functional.mse_loss(recon, x)

        # KEY INSIGHT: For anomaly detection, we MINIMIZE tension on normal data.
        # Both poles should AGREE on normal inputs (low tension).
        # On unseen anomalies, poles will naturally disagree (high tension).
        # This is the "consensus = normality" principle.
        tension_reg = tension.mean()

        total_loss = recon_loss + self.repulsion_weight * tension_reg
        return total_loss, recon_loss.item(), tension.mean().item()


# ─────────────────────────────────────────
# Data Generation
# ─────────────────────────────────────────

def generate_data(n_normal=500, n_anomaly=50, input_dim=20, random_state=42):
    """Generate normal (2 clusters) + anomaly (uniform outliers) data."""
    np.random.seed(random_state)

    # Normal data: 2 tight clusters
    X_normal, _ = make_blobs(
        n_samples=n_normal,
        n_features=input_dim,
        centers=2,
        cluster_std=1.0,
        random_state=random_state,
    )

    # Anomalies: uniform random in expanded range
    data_min = X_normal.min(axis=0) - 3.0
    data_max = X_normal.max(axis=0) + 3.0
    X_anomaly = np.random.uniform(data_min, data_max, size=(n_anomaly * 5, input_dim))

    # Keep only points that are far from normal cluster centers
    from sklearn.neighbors import NearestNeighbors
    nn_model = NearestNeighbors(n_neighbors=5)
    nn_model.fit(X_normal)
    distances, _ = nn_model.kneighbors(X_anomaly)
    mean_dist = distances.mean(axis=1)

    # Select the most outlier-like points
    threshold = np.percentile(mean_dist, 80)
    far_mask = mean_dist >= threshold
    X_anomaly = X_anomaly[far_mask][:n_anomaly]

    print(f"Data generated:")
    print(f"  Normal samples:  {X_normal.shape[0]}")
    print(f"  Anomaly samples: {X_anomaly.shape[0]}")
    print(f"  Input dimension: {input_dim}")

    return X_normal.astype(np.float32), X_anomaly.astype(np.float32)


# ─────────────────────────────────────────
# Training
# ─────────────────────────────────────────

def train_model(model, X_train, epochs=100, batch_size=64, lr=1e-3):
    """Train repulsion field on normal data only."""
    optimizer = optim.Adam(model.parameters(), lr=lr)
    dataset = torch.utils.data.TensorDataset(torch.from_numpy(X_train))
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        epoch_recon = 0.0
        epoch_tension = 0.0
        n_batches = 0

        for (batch_x,) in loader:
            optimizer.zero_grad()
            loss, recon_loss, tension = model.compute_loss(batch_x)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            epoch_recon += recon_loss
            epoch_tension += tension
            n_batches += 1

        if (epoch + 1) % 20 == 0:
            avg_loss = epoch_loss / n_batches
            avg_recon = epoch_recon / n_batches
            avg_tension = epoch_tension / n_batches
            print(f"  Epoch {epoch+1:3d}/{epochs}: "
                  f"loss={avg_loss:.4f}  recon={avg_recon:.4f}  tension={avg_tension:.4f}")

    return model


# ─────────────────────────────────────────
# Evaluation
# ─────────────────────────────────────────

def evaluate_anomaly_detection(model, X_normal_test, X_anomaly):
    """Compute tension scores and AUROC."""
    model.eval()
    with torch.no_grad():
        # Normal test samples
        x_normal = torch.from_numpy(X_normal_test)
        _, tension_normal = model.forward(x_normal)
        tension_normal = tension_normal.numpy()

        # Anomaly samples
        x_anomaly = torch.from_numpy(X_anomaly)
        _, tension_anomaly = model.forward(x_anomaly)
        tension_anomaly = tension_anomaly.numpy()

    # Also compute reconstruction error as a secondary score
    with torch.no_grad():
        recon_normal, _ = model.forward(x_normal)
        recon_error_normal = ((recon_normal.numpy() - X_normal_test) ** 2).mean(axis=1)

        recon_anomaly, _ = model.forward(x_anomaly)
        recon_error_anomaly = ((recon_anomaly.numpy() - X_anomaly) ** 2).mean(axis=1)

    # Labels: 0=normal, 1=anomaly
    y_true = np.concatenate([
        np.zeros(len(tension_normal)),
        np.ones(len(tension_anomaly)),
    ])

    # AUROC with tension as score
    scores_tension = np.concatenate([tension_normal, tension_anomaly])
    auroc_tension = roc_auc_score(y_true, scores_tension)

    # AUROC with reconstruction error as score
    scores_recon = np.concatenate([recon_error_normal, recon_error_anomaly])
    auroc_recon = roc_auc_score(y_true, scores_recon)

    # Combined score: tension * recon_error
    scores_combined = scores_tension * scores_recon
    auroc_combined = roc_auc_score(y_true, scores_combined)

    return {
        'auroc_tension': auroc_tension,
        'auroc_recon': auroc_recon,
        'auroc_combined': auroc_combined,
        'tension_normal_mean': tension_normal.mean(),
        'tension_normal_std': tension_normal.std(),
        'tension_anomaly_mean': tension_anomaly.mean(),
        'tension_anomaly_std': tension_anomaly.std(),
        'recon_normal_mean': recon_error_normal.mean(),
        'recon_anomaly_mean': recon_error_anomaly.mean(),
        'tension_ratio': tension_anomaly.mean() / (tension_normal.mean() + 1e-8),
    }


def print_results(results):
    """Print formatted results."""
    print("\n" + "=" * 60)
    print("  REPULSION FIELD ANOMALY DETECTION RESULTS")
    print("=" * 60)

    print(f"\n  Tension (normal):   {results['tension_normal_mean']:.4f} +/- {results['tension_normal_std']:.4f}")
    print(f"  Tension (anomaly):  {results['tension_anomaly_mean']:.4f} +/- {results['tension_anomaly_std']:.4f}")
    print(f"  Tension ratio:      {results['tension_ratio']:.2f}x")

    print(f"\n  Recon error (normal):  {results['recon_normal_mean']:.4f}")
    print(f"  Recon error (anomaly): {results['recon_anomaly_mean']:.4f}")

    print(f"\n  AUROC (tension only):      {results['auroc_tension']:.4f}")
    print(f"  AUROC (recon error only):  {results['auroc_recon']:.4f}")
    print(f"  AUROC (combined):          {results['auroc_combined']:.4f}")

    # Verdict
    print("\n" + "-" * 60)
    if results['auroc_tension'] >= 0.80:
        verdict = "STRONG SUPPORT"
    elif results['auroc_tension'] >= 0.65:
        verdict = "MODERATE SUPPORT"
    elif results['auroc_tension'] >= 0.55:
        verdict = "WEAK SUPPORT"
    else:
        verdict = "NOT SUPPORTED"

    print(f"  Hypothesis verdict: {verdict}")
    print(f"  (High tension = anomaly)")

    if results['auroc_tension'] > results['auroc_recon']:
        print(f"  Tension BEATS reconstruction error as anomaly score!")
    elif results['auroc_tension'] > 0.5:
        print(f"  Tension is a valid anomaly signal (but recon error is stronger).")
    else:
        print(f"  Tension does not discriminate anomalies.")

    print("-" * 60)


# ─────────────────────────────────────────
# Multiple Seeds for Robustness
# ─────────────────────────────────────────

def run_multiple_seeds(n_seeds=5):
    """Run experiment with multiple random seeds for robustness."""
    all_results = []

    for seed in range(n_seeds):
        print(f"\n{'='*60}")
        print(f"  SEED {seed}")
        print(f"{'='*60}")

        torch.manual_seed(seed)
        np.random.seed(seed)

        # Generate data
        X_normal, X_anomaly = generate_data(
            n_normal=500, n_anomaly=50, input_dim=20, random_state=seed
        )

        # Train/test split on normal data
        X_train, X_test = train_test_split(X_normal, test_size=0.3, random_state=seed)

        # Build and train model
        model = RepulsionFieldAutoencoder(input_dim=20, hidden_dim=64, latent_dim=32)
        print(f"\nTraining on {X_train.shape[0]} normal samples...")
        train_model(model, X_train, epochs=100, batch_size=64, lr=1e-3)

        # Evaluate
        results = evaluate_anomaly_detection(model, X_test, X_anomaly)
        all_results.append(results)
        print_results(results)

    # Summary across seeds
    print("\n\n" + "=" * 60)
    print("  SUMMARY ACROSS ALL SEEDS")
    print("=" * 60)

    for key in ['auroc_tension', 'auroc_recon', 'auroc_combined', 'tension_ratio']:
        values = [r[key] for r in all_results]
        mean_val = np.mean(values)
        std_val = np.std(values)
        print(f"  {key:25s}: {mean_val:.4f} +/- {std_val:.4f}")

    avg_auroc = np.mean([r['auroc_tension'] for r in all_results])
    print(f"\n  Overall AUROC (tension): {avg_auroc:.4f}")

    if avg_auroc >= 0.80:
        print("  >>> HYPOTHESIS STRONGLY SUPPORTED: Repulsion field tension is a natural anomaly detector.")
    elif avg_auroc >= 0.65:
        print("  >>> HYPOTHESIS MODERATELY SUPPORTED: Tension carries anomaly signal.")
    elif avg_auroc >= 0.55:
        print("  >>> HYPOTHESIS WEAKLY SUPPORTED: Marginal anomaly detection capability.")
    else:
        print("  >>> HYPOTHESIS NOT SUPPORTED: Tension does not reliably detect anomalies.")

    return all_results


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────

if __name__ == '__main__':
    print("Repulsion Field Anomaly Detection Experiment")
    print("Hypothesis: High tension = anomaly (engines disagree on unusual inputs)")
    print()
    results = run_multiple_seeds(n_seeds=5)
