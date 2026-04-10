#!/usr/bin/env python3
"""Hypothesis 325 verification: Fisher information geometry and tension manifolds

Method:
1. Train PureFieldEngine on MNIST + Fashion-MNIST
2. Collect class-specific tension fingerprints (10-dimensional)
3. Calculate empirical Fisher information matrix for each class
4. Measure correlation coefficient between tr(F_k) vs mean_tension_k
5. Prediction: r > +0.7
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

np.random.seed(42)
torch.manual_seed(42)

print("=" * 70)
print("Hypothesis 325 verification: Correlation between Fisher information and tension")
print("=" * 70)

# ─────────────────────────────────────────
# 1. Define PureFieldEngine (inline)
# ─────────────────────────────────────────

class PureFieldEngine(nn.Module):
    def __init__(self, input_dim=784, hidden_dim=128, output_dim=10):
        super().__init__()
        self.engine_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.engine_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.tension_scale = nn.Parameter(torch.tensor(1.0))

    def forward(self, x):
        out_a = self.engine_a(x)
        out_g = self.engine_g(x)
        repulsion = out_a - out_g
        tension = (repulsion ** 2).mean(dim=-1, keepdim=True)
        direction = F.normalize(repulsion, dim=-1)
        output = self.tension_scale * torch.sqrt(tension + 1e-8) * direction
        return output, tension.squeeze(-1), repulsion

    def get_fingerprint(self, x):
        """Per-class tension fingerprint (10-dimensional)."""
        out_a = self.engine_a(x)
        out_g = self.engine_g(x)
        repulsion = out_a - out_g
        # Square of each output dimension = per-class tension
        per_class_tension = repulsion ** 2  # (B, 10)
        return per_class_tension


# ─────────────────────────────────────────
# 2. Data loading + training
# ─────────────────────────────────────────

from torchvision import datasets, transforms

def run_experiment(dataset_name):
    print(f"\n{'='*60}")
    print(f"  Dataset: {dataset_name}")
    print(f"{'='*60}")

    transform = transforms.Compose([transforms.ToTensor(), transforms.Lambda(lambda x: x.view(-1))])

    if dataset_name == "MNIST":
        train_ds = datasets.MNIST(root='/tmp/data', train=True, download=True, transform=transform)
        test_ds = datasets.MNIST(root='/tmp/data', train=False, download=True, transform=transform)
        class_names = [str(i) for i in range(10)]
    elif dataset_name == "FashionMNIST":
        train_ds = datasets.FashionMNIST(root='/tmp/data', train=True, download=True, transform=transform)
        test_ds = datasets.FashionMNIST(root='/tmp/data', train=False, download=True, transform=transform)
        class_names = ["T-shirt", "Trouser", "Pullover", "Dress", "Coat",
                       "Sandal", "Shirt", "Sneaker", "Bag", "Boot"]

    train_loader = torch.utils.data.DataLoader(train_ds, batch_size=256, shuffle=True)
    test_loader = torch.utils.data.DataLoader(test_ds, batch_size=256, shuffle=False)

    # Training
    model = PureFieldEngine(784, 128, 10)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    print(f"\n  Starting training (15 epochs)...")
    for epoch in range(15):
        model.train()
        total_loss = 0
        correct = 0
        total = 0

        for x_batch, y_batch in train_loader:
            output, tension, _ = model(x_batch)
            loss = F.cross_entropy(output, y_batch)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * len(x_batch)
            correct += (output.argmax(dim=-1) == y_batch).sum().item()
            total += len(x_batch)

        if (epoch + 1) % 5 == 0:
            acc = correct / total * 100
            print(f"    Epoch {epoch+1}: loss={total_loss/total:.4f}, acc={acc:.1f}%")

    # Test accuracy
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for x_batch, y_batch in test_loader:
            output, _, _ = model(x_batch)
            correct += (output.argmax(dim=-1) == y_batch).sum().item()
            total += len(x_batch)
    test_acc = correct / total * 100
    print(f"  Test accuracy: {test_acc:.1f}%")

    # ─────────────────────────────────────────
    # 3. Collect fingerprints + tension by class
    # ─────────────────────────────────────────

    print(f"\n  Collecting fingerprints...")
    model.eval()

    all_fingerprints = []
    all_tensions = []
    all_labels = []

    with torch.no_grad():
        for x_batch, y_batch in test_loader:
            fp = model.get_fingerprint(x_batch)  # (B, 10)
            _, tension, _ = model(x_batch)  # (B,)
            all_fingerprints.append(fp.numpy())
            all_tensions.append(tension.numpy())
            all_labels.append(y_batch.numpy())

    fps = np.concatenate(all_fingerprints)  # (N, 10)
    tensions = np.concatenate(all_tensions)  # (N,)
    labels = np.concatenate(all_labels)  # (N,)

    # Per-class statistics
    n_classes = 10
    class_mean_tension = np.zeros(n_classes)
    class_mean_fp = np.zeros((n_classes, n_classes))
    class_counts = np.zeros(n_classes)

    for k in range(n_classes):
        mask = labels == k
        class_counts[k] = np.sum(mask)
        class_mean_tension[k] = np.mean(tensions[mask])
        class_mean_fp[k] = np.mean(fps[mask], axis=0)

    print(f"\n  Mean tension by class:")
    print(f"  {'Class':>10} | {'Count':>6} | {'Mean T':>10} | Bar")
    print(f"  {'─'*10}─┼─{'─'*6}─┼─{'─'*10}─┼─{'─'*30}")
    max_t = np.max(class_mean_tension)
    for k in range(n_classes):
        bar_len = int(class_mean_tension[k] / max_t * 30)
        bar = "#" * bar_len
        print(f"  {class_names[k]:>10} | {int(class_counts[k]):>6} | {class_mean_tension[k]:>10.4f} | {bar}")

    # ─────────────────────────────────────────
    # 4. Calculate empirical Fisher information matrix
    # ─────────────────────────────────────────

    print(f"\n  Calculating Fisher information matrices...")

    class_fisher_trace = np.zeros(n_classes)
    class_fisher_det = np.zeros(n_classes)

    for k in range(n_classes):
        mask = labels == k
        fps_k = fps[mask]  # (n_k, 10)

        if len(fps_k) < 20:
            continue

        # Empirical Fisher: proportional to diagonal sum of inverse of fingerprint covariance
        # Fisher ≈ inverse of fingerprint variance (univariate approximation)
        # More precisely: trace of covariance matrix inverse

        # Method 1: per-dimension variance → Fisher ≈ 1/var
        var_k = np.var(fps_k, axis=0) + 1e-10  # (10,)
        fisher_per_dim = 1.0 / var_k  # high Fisher = narrow distribution = confidence
        class_fisher_trace[k] = np.sum(fisher_per_dim)

        # Method 2: full covariance matrix
        cov_k = np.cov(fps_k.T)  # (10, 10)
        try:
            inv_cov = np.linalg.inv(cov_k + np.eye(10) * 1e-6)
            class_fisher_det[k] = np.log(np.linalg.det(inv_cov + np.eye(10) * 1e-10) + 1e-10)
        except:
            class_fisher_det[k] = 0

    print(f"\n  Fisher trace vs tension by class:")
    print(f"  {'Class':>10} | {'Mean T':>10} | {'F trace':>12} | {'log|F|':>10}")
    print(f"  {'─'*10}─┼─{'─'*10}─┼─{'─'*12}─┼─{'─'*10}")
    for k in range(n_classes):
        print(f"  {class_names[k]:>10} | {class_mean_tension[k]:>10.4f} | {class_fisher_trace[k]:>12.1f} | {class_fisher_det[k]:>10.2f}")

    # ─────────────────────────────────────────
    # 5. Correlation
    # ─────────────────────────────────────────

    # Pearson correlation: tension vs Fisher trace
    r_trace = np.corrcoef(class_mean_tension, class_fisher_trace)[0, 1]
    r_det = np.corrcoef(class_mean_tension, class_fisher_det)[0, 1]

    print(f"\n  Correlation coefficients:")
    print(f"    r(tension, Fisher trace) = {r_trace:+.4f}")
    print(f"    r(tension, log|F|)       = {r_det:+.4f}")

    # Spearman rank correlation (manual implementation)
    def spearman_r(x, y):
        n = len(x)
        rank_x = np.argsort(np.argsort(x)).astype(float)
        rank_y = np.argsort(np.argsort(y)).astype(float)
        d = rank_x - rank_y
        return 1 - 6 * np.sum(d**2) / (n * (n**2 - 1))

    rho_trace = spearman_r(class_mean_tension, class_fisher_trace)
    rho_det = spearman_r(class_mean_tension, class_fisher_det)

    print(f"    rho(tension, Fisher trace) = {rho_trace:+.4f} (Spearman)")
    print(f"    rho(tension, log|F|)       = {rho_det:+.4f} (Spearman)")

    # ─────────────────────────────────────────
    # 6. ASCII scatter plot
    # ─────────────────────────────────────────

    print(f"\n  Fisher trace vs Mean Tension (scatter plot):")
    t_min, t_max = class_mean_tension.min(), class_mean_tension.max()
    f_min, f_max = class_fisher_trace.min(), class_fisher_trace.max()

    height = 15
    width = 40
    grid = [['.' for _ in range(width)] for _ in range(height)]

    for k in range(n_classes):
        x_pos = int((class_mean_tension[k] - t_min) / (t_max - t_min + 1e-10) * (width - 1))
        y_pos = int((class_fisher_trace[k] - f_min) / (f_max - f_min + 1e-10) * (height - 1))
        y_pos = height - 1 - y_pos  # flip y
        x_pos = max(0, min(width - 1, x_pos))
        y_pos = max(0, min(height - 1, y_pos))
        label = class_names[k][0]  # first letter
        grid[y_pos][x_pos] = label

    print(f"    Fisher ^")
    for row in grid:
        print(f"    {''.join(row)}")
    print(f"    {'─' * width}> Tension")

    return {
        "dataset": dataset_name,
        "test_acc": test_acc,
        "r_trace": r_trace,
        "r_det": r_det,
        "rho_trace": rho_trace,
        "rho_det": rho_det,
        "class_tensions": class_mean_tension,
        "class_fisher": class_fisher_trace,
        "tension_scale": model.tension_scale.item(),
    }


# ─────────────────────────────────────────
# Execute
# ─────────────────────────────────────────

results = []
for ds in ["MNIST", "FashionMNIST"]:
    r = run_experiment(ds)
    results.append(r)

# ─────────────────────────────────────────
# Overall conclusion
# ─────────────────────────────────────────

print("\n" + "=" * 70)
print("Overall Conclusion")
print("=" * 70)

print(f"\n  {'Dataset':>12} | {'Acc':>6} | {'r(T,F)':>8} | {'rho(T,F)':>10} | {'ts':>6}")
print(f"  {'─'*12}─┼─{'─'*6}─┼─{'─'*8}─┼─{'─'*10}─┼─{'─'*6}")
for r in results:
    print(f"  {r['dataset']:>12} | {r['test_acc']:>5.1f}% | {r['r_trace']:>+8.4f} | {r['rho_trace']:>+10.4f} | {r['tension_scale']:>6.3f}")

avg_r = np.mean([r['r_trace'] for r in results])
avg_rho = np.mean([r['rho_trace'] for r in results])

print(f"\n  Average Pearson r:  {avg_r:+.4f}")
print(f"  Average Spearman rho: {avg_rho:+.4f}")

print(f"\n  Hypothesis 325 prediction: r > +0.7 (Fisher proportional to tension)")

if avg_r > 0.7:
    verdict = "Strong support — Fisher information proportional to tension"
elif avg_r > 0.3:
    verdict = "Partial support — positive correlation exists but weaker than predicted"
elif avg_r > 0:
    verdict = "Weak support — slight positive correlation"
elif avg_r > -0.3:
    verdict = "Not supported — no significant correlation"
else:
    verdict = "Refuted — negative correlation (opposite of prediction)"

print(f"  Verdict: {verdict}")

print(f"\n  ⚠️ Note:")
print(f"    - Fisher = 1/var approximation (assumes normal distribution)")
print(f"    - Fingerprint distribution may be non-normal")
print(f"    - 1000 samples in 10 dimensions = stable estimation possible")
print(f"    - Causal direction uncertain (F→T? T→F? Common cause?)")
print("=" * 70)