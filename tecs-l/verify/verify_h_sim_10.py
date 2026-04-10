#!/usr/bin/env python3
"""H-SIM-10: Tension = Simulation Computational Cost
Verify: correlation between tension and effective computation
(gradient magnitude, activation density) in a simple neural network.
"""
import numpy as np
np.random.seed(42)

# ============================================================
# Simple 2-layer neural network on synthetic digit-like data
# ============================================================

def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))

def softmax(x):
    ex = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return ex / ex.sum(axis=-1, keepdims=True)

def relu(x):
    return np.maximum(0, x)

class SimpleNet:
    def __init__(self, input_dim=64, hidden_dim=32, output_dim=10):
        scale1 = np.sqrt(2.0 / input_dim)
        scale2 = np.sqrt(2.0 / hidden_dim)
        self.W1 = np.random.randn(input_dim, hidden_dim) * scale1
        self.b1 = np.zeros(hidden_dim)
        self.W2 = np.random.randn(hidden_dim, output_dim) * scale2
        self.b2 = np.zeros(output_dim)

    def forward(self, x):
        """Forward pass, return logits and intermediate values."""
        z1 = x @ self.W1 + self.b1
        h1 = relu(z1)
        z2 = h1 @ self.W2 + self.b2
        return z2, h1, z1

    def tension(self, logits):
        """Tension = 1 - (max_prob - second_max_prob).
        High tension = uncertain, low tension = confident."""
        probs = softmax(logits)
        sorted_probs = np.sort(probs, axis=-1)[:, ::-1]
        gap = sorted_probs[:, 0] - sorted_probs[:, 1]
        return 1.0 - gap

    def gradient_magnitude(self, x, labels):
        """Compute per-sample gradient magnitude (proxy for computational cost)."""
        z1 = x @ self.W1 + self.b1
        h1 = relu(z1)
        z2 = h1 @ self.W2 + self.b2
        probs = softmax(z2)

        grad_mags = []
        for i in range(len(x)):
            # Output gradient
            dz2 = probs[i].copy()
            dz2[labels[i]] -= 1.0

            # Gradient through W2
            dW2 = np.outer(h1[i], dz2)

            # Backprop through ReLU
            dh1 = dz2 @ self.W2.T
            dz1 = dh1 * (z1[i] > 0).astype(float)

            # Gradient through W1
            dW1 = np.outer(x[i], dz1)

            # Total gradient magnitude
            total_grad = np.sqrt(np.sum(dW1**2) + np.sum(dW2**2))
            grad_mags.append(total_grad)

        return np.array(grad_mags)

    def activation_density(self, h1):
        """Fraction of non-zero activations per sample (after ReLU)."""
        return np.mean(h1 > 0, axis=1)

    def activation_magnitude(self, h1):
        """Mean activation magnitude per sample."""
        return np.mean(np.abs(h1), axis=1)

# ============================================================
# Generate synthetic data (digit-like: 8x8 patterns)
# ============================================================
print("=" * 70)
print("H-SIM-10: Tension = Simulation Computational Cost")
print("=" * 70)

N = 500  # samples
D = 64   # 8x8 input
C = 10   # classes

# Create clustered data (some classes overlap = high tension)
X = np.zeros((N, D))
y = np.zeros(N, dtype=int)

for i in range(N):
    label = i % C
    y[i] = label
    # Base pattern for this class
    center = np.random.randn(D) * 0.3
    center[label * 6:(label + 1) * 6] += 2.0  # class-specific features
    # Add noise (more noise for some classes = harder = higher tension)
    noise_level = 0.5 + 0.3 * (label % 3)  # classes 0,3,6,9 are easy; 2,5,8 are hard
    X[i] = center + np.random.randn(D) * noise_level

# Normalize
X = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-8)

# ============================================================
# Train briefly so the network has meaningful representations
# ============================================================
net = SimpleNet(D, 32, C)
lr = 0.01

print("\nTraining for 200 steps...")
for step in range(200):
    # Mini-batch
    idx = np.random.choice(N, 64, replace=False)
    xb, yb = X[idx], y[idx]

    z1 = xb @ net.W1 + net.b1
    h1 = relu(z1)
    z2 = h1 @ net.W2 + net.b2
    probs = softmax(z2)

    # Cross-entropy loss
    loss = -np.mean(np.log(probs[range(len(yb)), yb] + 1e-10))

    # Backward
    dz2 = probs.copy()
    dz2[range(len(yb)), yb] -= 1.0
    dz2 /= len(yb)

    dW2 = h1.T @ dz2
    db2 = dz2.sum(axis=0)
    dh1 = dz2 @ net.W2.T
    dz1 = dh1 * (z1 > 0).astype(float)
    dW1 = xb.T @ dz1
    db1 = dz1.sum(axis=0)

    net.W1 -= lr * dW1
    net.b1 -= lr * db1
    net.W2 -= lr * dW2
    net.b2 -= lr * db2

    if step % 50 == 0:
        acc = np.mean(np.argmax(probs, axis=1) == yb)
        print(f"  Step {step:3d}: loss={loss:.4f}, acc={acc:.2%}")

# ============================================================
# PART 1: Compute tension, gradient magnitude, activation density
# ============================================================
print("\n" + "=" * 70)
print("PART 1: Per-sample metrics")
print("=" * 70)

logits, h1_all, z1_all = net.forward(X)
tensions = net.tension(logits)
grad_mags = net.gradient_magnitude(X, y)
act_density = net.activation_density(h1_all)
act_magnitude = net.activation_magnitude(h1_all)

# Predictions
preds = np.argmax(logits, axis=1)
correct = (preds == y)

print(f"\n  Overall accuracy: {correct.mean():.2%}")
print(f"  Mean tension: {tensions.mean():.4f} (std={tensions.std():.4f})")
print(f"  Mean grad magnitude: {grad_mags.mean():.4f} (std={grad_mags.std():.4f})")
print(f"  Mean activation density: {act_density.mean():.4f}")

# ============================================================
# PART 2: Correlations
# ============================================================
print("\n" + "=" * 70)
print("PART 2: Correlations — Tension vs Computational Cost")
print("=" * 70)

def pearson_r(a, b):
    a_m = a - a.mean()
    b_m = b - b.mean()
    return np.sum(a_m * b_m) / (np.sqrt(np.sum(a_m**2) * np.sum(b_m**2)) + 1e-10)

r_tension_grad = pearson_r(tensions, grad_mags)
r_tension_actdensity = pearson_r(tensions, act_density)
r_tension_actmag = pearson_r(tensions, act_magnitude)
r_grad_actdensity = pearson_r(grad_mags, act_density)

print(f"\n  Correlation Matrix:")
print(f"  {'':>20} | {'Tension':>10} | {'GradMag':>10} | {'ActDens':>10} | {'ActMag':>10}")
print(f"  {'-'*20}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")
print(f"  {'Tension':>20} | {'1.0000':>10} | {r_tension_grad:>10.4f} | {r_tension_actdensity:>10.4f} | {r_tension_actmag:>10.4f}")
print(f"  {'Grad Magnitude':>20} | {r_tension_grad:>10.4f} | {'1.0000':>10} | {r_grad_actdensity:>10.4f} | {pearson_r(grad_mags, act_magnitude):>10.4f}")
print(f"  {'Act Density':>20} | {r_tension_actdensity:>10.4f} | {r_grad_actdensity:>10.4f} | {'1.0000':>10} | {pearson_r(act_density, act_magnitude):>10.4f}")

# ============================================================
# PART 3: Tension quintile analysis
# ============================================================
print("\n" + "=" * 70)
print("PART 3: Tension quintile analysis")
print("=" * 70)

quintile_edges = np.percentile(tensions, [0, 20, 40, 60, 80, 100])
print(f"\n  {'Quintile':>10} | {'Tension Range':>18} | {'Mean Grad':>10} | {'Mean ActDens':>12} | {'Accuracy':>10} | {'N':>4}")
print(f"  {'-'*10}-+-{'-'*18}-+-{'-'*10}-+-{'-'*12}-+-{'-'*10}-+-{'-'*4}")

for q in range(5):
    lo, hi = quintile_edges[q], quintile_edges[q+1]
    if q < 4:
        mask = (tensions >= lo) & (tensions < hi)
    else:
        mask = (tensions >= lo) & (tensions <= hi)
    if mask.sum() == 0:
        continue
    mg = grad_mags[mask].mean()
    md = act_density[mask].mean()
    acc = correct[mask].mean()
    print(f"  {'Q'+str(q+1):>10} | {lo:>7.4f} - {hi:>7.4f} | {mg:>10.4f} | {md:>12.4f} | {acc:>10.2%} | {mask.sum():>4}")

# ============================================================
# PART 4: ASCII scatter — Tension vs Gradient Magnitude
# ============================================================
print("\n" + "=" * 70)
print("PART 4: ASCII Scatter — Tension (x) vs Gradient Magnitude (y)")
print("=" * 70)

W, H = 60, 20
canvas = [[' ' for _ in range(W)] for _ in range(H)]

t_min, t_max = tensions.min(), tensions.max()
g_min, g_max = grad_mags.min(), grad_mags.max()

# Sample points to avoid overcrowding
sample_idx = np.random.choice(N, min(200, N), replace=False)
for i in sample_idx:
    tx = int((tensions[i] - t_min) / (t_max - t_min + 1e-10) * (W - 1))
    gy = int((grad_mags[i] - g_min) / (g_max - g_min + 1e-10) * (H - 1))
    gy = H - 1 - gy  # flip y
    tx = max(0, min(W-1, tx))
    gy = max(0, min(H-1, gy))
    canvas[gy][tx] = '#' if canvas[gy][tx] == ' ' else '@'

print(f"\n  Grad Mag ^")
for row in range(H):
    y_val = g_max - (g_max - g_min) * row / (H - 1)
    line = ''.join(canvas[row])
    if row == 0:
        print(f"  {y_val:>6.2f} |{line}|")
    elif row == H-1:
        print(f"  {y_val:>6.2f} |{line}|")
    else:
        print(f"  {y_val:>6.2f} |{line}|")
print(f"         +{'-'*W}+")
print(f"          {t_min:<6.2f}{' '*(W-12)}{t_max:>6.2f}")
print(f"                        Tension -->")
print(f"  r = {r_tension_grad:.4f}")

# ============================================================
# PART 5: Correct vs Incorrect samples
# ============================================================
print("\n" + "=" * 70)
print("PART 5: Correct vs Incorrect — Computational Cost comparison")
print("=" * 70)

print(f"\n  {'Metric':>20} | {'Correct':>10} | {'Incorrect':>10} | {'Ratio':>8}")
print(f"  {'-'*20}-+-{'-'*10}-+-{'-'*10}-+-{'-'*8}")
for name, vals in [("Tension", tensions), ("Grad Magnitude", grad_mags),
                    ("Act Density", act_density), ("Act Magnitude", act_magnitude)]:
    c_val = vals[correct].mean()
    i_val = vals[~correct].mean()
    ratio = i_val / (c_val + 1e-10)
    print(f"  {name:>20} | {c_val:>10.4f} | {i_val:>10.4f} | {ratio:>8.2f}x")

# ============================================================
# PART 6: Phase transition analogy
# ============================================================
print("\n" + "=" * 70)
print("PART 6: Phase Transition — Tension susceptibility")
print("=" * 70)

# Compute tension distribution and its derivative (susceptibility analog)
n_bins = 20
t_hist, t_edges = np.histogram(tensions, bins=n_bins)
t_centers = (t_edges[:-1] + t_edges[1:]) / 2

# Mean gradient at each tension level
grad_at_tension = []
for i in range(n_bins):
    mask = (tensions >= t_edges[i]) & (tensions < t_edges[i+1])
    if mask.sum() > 0:
        grad_at_tension.append(grad_mags[mask].mean())
    else:
        grad_at_tension.append(0)
grad_at_tension = np.array(grad_at_tension)

# Susceptibility = d(grad)/d(tension) ≈ finite difference
susceptibility = np.diff(grad_at_tension) / np.diff(t_centers)

print(f"\n  Tension bin analysis:")
print(f"  {'Tension':>10} | {'Count':>6} | {'Mean Grad':>10} | {'Suscept.':>10}")
print(f"  {'-'*10}-+-{'-'*6}-+-{'-'*10}-+-{'-'*10}")
for i in range(n_bins):
    s = susceptibility[i-1] if i > 0 and i <= len(susceptibility) else 0
    print(f"  {t_centers[i]:>10.4f} | {t_hist[i]:>6} | {grad_at_tension[i]:>10.4f} | {s:>10.4f}")

# Find peak susceptibility
if len(susceptibility) > 0:
    peak_idx = np.argmax(np.abs(susceptibility))
    print(f"\n  Peak susceptibility at tension ≈ {t_centers[peak_idx+1]:.4f}")
    print(f"  Susceptibility value = {susceptibility[peak_idx]:.4f}")
    print(f"  (Analog of H-CX-414 phase transition)")

# ============================================================
# PART 7: ASCII bar chart — gradient by tension quintile
# ============================================================
print("\n" + "=" * 70)
print("PART 7: ASCII Bar Chart — Mean Gradient by Tension Quintile")
print("=" * 70)

print()
for q in range(5):
    lo, hi = quintile_edges[q], quintile_edges[q+1]
    if q < 4:
        mask = (tensions >= lo) & (tensions < hi)
    else:
        mask = (tensions >= lo) & (tensions <= hi)
    if mask.sum() == 0:
        continue
    mg = grad_mags[mask].mean()
    bar = '#' * int(mg / grad_mags.max() * 40)
    print(f"  Q{q+1} ({lo:.3f}-{hi:.3f}) | {bar} {mg:.3f}")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"""
  Core finding: Tension and gradient magnitude (computational cost proxy)
  show correlation r = {r_tension_grad:.4f}

  Interpretation:
    r > 0.3  →  Strong support: high tension = high computational cost
    r > 0.1  →  Moderate support
    r < 0.1  →  Weak/no support

  Tension-Gradient correlation:     r = {r_tension_grad:.4f}
  Tension-Activation density:       r = {r_tension_actdensity:.4f}
  Tension-Activation magnitude:     r = {r_tension_actmag:.4f}

  Incorrect samples have {grad_mags[~correct].mean()/grad_mags[correct].mean():.2f}x gradient magnitude
  vs correct samples (higher tension → more computation needed).

  Simulation analogy:
    Tension = uncertainty in physical system
    Gradient = computational resources to resolve uncertainty
    Phase transition = peak susceptibility = maximum resource demand
    → Universe simulator allocates MORE computation at quantum measurement
       (high tension) events, LESS at classical (low tension) events.
""")
