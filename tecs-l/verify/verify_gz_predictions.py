#!/usr/bin/env python3
"""Golden Zone PREDICTIVE Experiments

Critical Rule: All predictions are stated BEFORE measurement.
This script documents the predicted value, then measures, then compares.
Failed predictions are recorded honestly.

Predictions tested here:
  P1: MoE optimal k/N -> 1/e as N grows (test N=64, sweep k)
  P3: Lottery ticket critical density ~ 1/e
  P5: Elias-Bassalygo bound at delta=ln(4/3) -> R=1/3

Deferred (require GPU/HuggingFace):
  P2: Transformer head pruning optimal survival ~ 1/e
  P4: Optimal batch_size/dataset_size in Golden Zone
"""

import numpy as np
import math
import time
import sys

# ═══════════════════════════════════════════════════════════════
# Golden Zone Constants (stated before any measurement)
# ═══════════════════════════════════════════════════════════════
GZ_CENTER = 1 / math.e          # 0.36788...
GZ_UPPER = 0.5                  # Riemann critical line
GZ_LOWER = 0.5 - math.log(4/3) # 0.21227...
GZ_WIDTH = math.log(4/3)        # 0.28768...
TAU_6 = 4
SIGMA_6 = 12

def banner(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def section(title):
    print(f"\n{'─'*70}")
    print(f"  {title}")
    print(f"{'─'*70}")

def grade(predicted, observed, tolerance, label=""):
    """Grade a prediction against observation."""
    error = abs(observed - predicted)
    rel_error = error / max(abs(predicted), 1e-10)
    within = error <= tolerance

    status = "CONFIRMED" if within else (
        "PARTIALLY CONFIRMED" if error <= 2 * tolerance else "REFUTED"
    )
    symbol = {
        "CONFIRMED": "[OK]",
        "PARTIALLY CONFIRMED": "[~~]",
        "REFUTED": "[XX]",
    }[status]

    print(f"\n  {symbol} {label}")
    print(f"    Predicted:  {predicted:.6f}")
    print(f"    Observed:   {observed:.6f}")
    print(f"    Error:      {error:.6f} (rel: {rel_error:.4f})")
    print(f"    Tolerance:  +/- {tolerance:.6f}")
    print(f"    Grade:      {status}")
    return status


# ═══════════════════════════════════════════════════════════════
#  PREDICTION 5: Information-Theoretic Coding Bound
#  (Run first because it's pure math -- instant, no randomness)
# ═══════════════════════════════════════════════════════════════

def binary_entropy(x):
    """H_2(x) = -x*log2(x) - (1-x)*log2(1-x)"""
    if x <= 0 or x >= 1:
        return 0.0
    return -x * math.log2(x) - (1 - x) * math.log2(1 - x)

def johnson_radius(delta):
    """J(delta) = 1/2 - sqrt(delta*(1-delta))"""
    return 0.5 - math.sqrt(delta * (1 - delta))

def elias_bassalygo_bound(delta):
    """R_EB(delta) = 1 - H_2(J(delta))"""
    j = johnson_radius(delta)
    if j <= 0 or j >= 1:
        return None
    return 1 - binary_entropy(j)

def gilbert_varshamov_bound(delta):
    """R_GV(delta) = 1 - H_2(delta)"""
    return 1 - binary_entropy(delta)

def plotkin_bound(delta):
    """R_Plotkin(delta) = 1 - 2*delta for delta <= 1/2"""
    if delta > 0.5:
        return 0
    return 1 - 2 * delta

def run_prediction_5():
    banner("PREDICTION 5: Coding Theory Bounds at delta = ln(4/3)")

    # ── State prediction BEFORE computation ──
    delta = GZ_WIDTH  # ln(4/3) = 0.28768...
    predicted_eb_rate = 1/3  # 0.33333...

    print(f"\n  PRE-REGISTERED PREDICTION:")
    print(f"    delta = ln(4/3) = {delta:.10f}")
    print(f"    Predicted: R_EB(delta) = 1/3 = {predicted_eb_rate:.10f}")
    print(f"    Tolerance: +/- 0.02")

    # ── Compute ──
    section("Computing bounds")

    h2_delta = binary_entropy(delta)
    j_delta = johnson_radius(delta)
    r_gv = gilbert_varshamov_bound(delta)
    r_plotkin = plotkin_bound(delta)
    r_eb = elias_bassalygo_bound(delta)

    print(f"\n  delta         = {delta:.10f}")
    print(f"  H_2(delta)    = {h2_delta:.10f}")
    print(f"  J(delta)      = {j_delta:.10f}")
    print(f"  H_2(J(delta)) = {binary_entropy(j_delta):.10f}")
    print()
    print(f"  Gilbert-Varshamov lower bound:  R_GV  = {r_gv:.10f}")
    print(f"  Plotkin upper bound:            R_Pl  = {r_plotkin:.10f}")
    print(f"  Elias-Bassalygo upper bound:    R_EB  = {r_eb:.10f}")
    print()
    print(f"  GZ predictions for comparison:")
    print(f"    1/3                           = {1/3:.10f}")
    print(f"    1/e                           = {1/math.e:.10f}")
    print(f"    GZ_lower                      = {GZ_LOWER:.10f}")

    # ── Additional: scan delta values to find where R_EB = 1/3 ──
    section("Scanning: at what delta does R_EB = 1/3 exactly?")
    best_delta = None
    best_err = 1.0
    for d_int in range(1, 4999):
        d = d_int / 10000.0
        r = elias_bassalygo_bound(d)
        if r is not None:
            err = abs(r - 1/3)
            if err < best_err:
                best_err = err
                best_delta = d
    print(f"  R_EB = 1/3 occurs at delta = {best_delta:.4f} (error {best_err:.6f})")
    print(f"  Compared to ln(4/3) = {delta:.4f}")
    print(f"  Difference: {abs(best_delta - delta):.4f}")

    # ── Grade ──
    section("GRADING Prediction 5")
    status = grade(predicted_eb_rate, r_eb, 0.02, "R_EB(ln(4/3)) = 1/3?")

    # Also check if any GZ constant appears
    print(f"\n  Bonus checks:")
    print(f"    R_GV = {r_gv:.6f} vs 1/e = {1/math.e:.6f}  (diff={abs(r_gv-1/math.e):.6f})")
    print(f"    R_GV = {r_gv:.6f} vs 1/3 = {1/3:.6f}  (diff={abs(r_gv-1/3):.6f})")
    print(f"    R_EB = {r_eb:.6f} vs 1/e = {1/math.e:.6f}  (diff={abs(r_eb-1/math.e):.6f})")

    return status


# ═══════════════════════════════════════════════════════════════
#  PREDICTION 1: MoE Expert Count Scaling (k/N -> 1/e)
# ═══════════════════════════════════════════════════════════════

class SimpleExpert:
    """Lightweight MLP expert for numpy-only MoE."""
    def __init__(self, input_dim, hidden_dim, output_dim):
        self.W1 = np.random.randn(input_dim, hidden_dim) * 0.05
        self.b1 = np.zeros(hidden_dim)
        self.W2 = np.random.randn(hidden_dim, output_dim) * 0.05
        self.b2 = np.zeros(output_dim)

    def forward(self, x):
        h = np.maximum(0, x @ self.W1 + self.b1)
        return h @ self.W2 + self.b2

    def params(self):
        return [self.W1, self.b1, self.W2, self.b2]


def softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()


def generate_classification_data(n_samples, n_features, n_classes):
    """Generate a nonlinear classification dataset."""
    X = np.random.randn(n_samples, n_features)
    # Use multiple feature combinations for richer patterns
    y = np.zeros(n_samples, dtype=int)
    for c in range(n_classes):
        # Each class defined by a random hyperplane
        w = np.random.RandomState(c + 100).randn(n_features)
        scores = X @ w
        if c == 0:
            class_scores = scores.copy().reshape(-1, 1)
        else:
            class_scores = np.hstack([class_scores, scores.reshape(-1, 1)])
    y = np.argmax(class_scores, axis=1)
    return X, y


def train_moe_topk(n_experts, k, n_features=16, n_classes=8,
                   n_train=1000, n_test=200, n_epochs=30, lr=0.01, seed=42):
    """Train MoE with top-k routing, return test accuracy."""
    rng = np.random.RandomState(seed)
    np.random.seed(seed)

    X_train, y_train = generate_classification_data(n_train, n_features, n_classes)
    X_test, y_test = generate_classification_data(n_test, n_features, n_classes)

    # Create experts
    hidden_dim = 16
    experts = [SimpleExpert(n_features, hidden_dim, n_classes) for _ in range(n_experts)]

    # Router weights
    router_W = rng.randn(n_features, n_experts) * 0.05

    for epoch in range(n_epochs):
        indices = rng.permutation(n_train)
        for idx in indices:
            x = X_train[idx]
            target = y_train[idx]

            # Route: top-k
            scores = x @ router_W
            topk_idx = np.argsort(scores)[-k:]

            # Forward through active experts
            output = np.zeros(n_classes)
            weights = softmax(scores[topk_idx])
            for j, ei in enumerate(topk_idx):
                output += weights[j] * experts[ei].forward(x)

            # Loss
            probs = softmax(output)
            loss = -np.log(probs[target] + 1e-10)

            # Simple gradient-free update (perturbation)
            for ei in topk_idx:
                for param in experts[ei].params():
                    param -= lr * rng.randn(*param.shape) * loss * 0.005

            # Router update
            router_W -= lr * rng.randn(*router_W.shape) * loss * 0.002

    # Test
    correct = 0
    for i in range(n_test):
        x = X_test[i]
        scores = x @ router_W
        topk_idx = np.argsort(scores)[-k:]
        output = np.zeros(n_classes)
        weights = softmax(scores[topk_idx])
        for j, ei in enumerate(topk_idx):
            output += weights[j] * experts[ei].forward(x)
        if np.argmax(output) == y_test[i]:
            correct += 1

    return correct / n_test


def run_prediction_1():
    banner("PREDICTION 1: MoE Optimal k/N -> 1/e")

    # ── State prediction BEFORE measurement ──
    N = 64
    predicted_k_a = round(N / math.e)     # 24 (I = active ratio = 1/e)
    predicted_k_b = round(N * (1 - 1/math.e))  # 40 (I = inactive ratio = 1/e)

    print(f"\n  PRE-REGISTERED PREDICTIONS (N={N} experts):")
    print(f"    P1a: optimal k = N/e = {predicted_k_a} (ratio {predicted_k_a/N:.4f})")
    print(f"         I = k/N = 1/e (active fraction = inhibition)")
    print(f"    P1b: optimal k = N*(1-1/e) = {predicted_k_b} (ratio {predicted_k_b/N:.4f})")
    print(f"         I = (N-k)/N = 1/e (inactive fraction = inhibition)")
    print(f"    Tolerance: +/- 4 experts")

    # ── Sweep ──
    section(f"Sweeping k for N={N} experts (3 seeds each)")

    k_values = list(range(4, 57, 4))  # 4, 8, 12, ..., 56
    n_seeds = 3
    results = {}

    t0 = time.time()
    for k in k_values:
        accs = []
        for seed in range(n_seeds):
            acc = train_moe_topk(
                n_experts=N, k=k, n_features=16, n_classes=8,
                n_train=600, n_test=150, n_epochs=20, lr=0.01, seed=seed*1000+k
            )
            accs.append(acc)
        mean_acc = np.mean(accs)
        std_acc = np.std(accs)
        results[k] = (mean_acc, std_acc)
        ratio = k / N
        bar = "#" * int(mean_acc * 50)
        print(f"    k={k:2d} (k/N={ratio:.3f}) | acc={mean_acc:.4f} +/- {std_acc:.4f} | {bar}")

    elapsed = time.time() - t0
    print(f"\n  Sweep completed in {elapsed:.1f}s")

    # ── Find optimal k ──
    best_k = max(results, key=lambda k: results[k][0])
    best_acc = results[best_k][0]
    best_ratio = best_k / N

    section("Results")
    print(f"  Optimal k  = {best_k}")
    print(f"  Optimal k/N = {best_ratio:.4f}")
    print(f"  Best acc   = {best_acc:.4f}")
    print(f"  1/e        = {1/math.e:.4f}")
    print(f"  1-1/e      = {1-1/math.e:.4f}")

    # ── ASCII chart ──
    section("Accuracy vs k/N")
    max_acc = max(v[0] for v in results.values())
    min_acc = min(v[0] for v in results.values())
    chart_width = 50

    for k in sorted(results.keys()):
        acc = results[k][0]
        if max_acc > min_acc:
            bar_len = int((acc - min_acc) / (max_acc - min_acc) * chart_width)
        else:
            bar_len = chart_width // 2
        marker = " <-- 1/e" if abs(k/N - 1/math.e) < 0.04 else (
            " <-- 1-1/e" if abs(k/N - (1-1/math.e)) < 0.04 else ""
        )
        best_mark = " ***" if k == best_k else ""
        print(f"    k={k:2d} ({k/N:.2f}) |{'#' * bar_len}{' ' * (chart_width - bar_len)}| {acc:.4f}{marker}{best_mark}")

    # ── Grade ──
    section("GRADING Prediction 1")
    status_a = grade(predicted_k_a / N, best_ratio, 4/N, "P1a: k/N = 1/e?")
    status_b = grade(predicted_k_b / N, best_ratio, 4/N, "P1b: k/N = 1-1/e?")

    # Overall
    if "CONFIRMED" in status_a or "CONFIRMED" in status_b:
        overall = "CONFIRMED (at least one sub-prediction)"
    elif "PARTIALLY" in status_a or "PARTIALLY" in status_b:
        overall = "PARTIALLY CONFIRMED"
    else:
        overall = "REFUTED"
    print(f"\n  OVERALL P1: {overall}")
    return overall


# ═══════════════════════════════════════════════════════════════
#  PREDICTION 3: Lottery Ticket Critical Density ~ 1/e
# ═══════════════════════════════════════════════════════════════

def run_prediction_3():
    banner("PREDICTION 3: Lottery Ticket Density ~ 1/e")

    # ── State prediction BEFORE measurement ──
    predicted_density = 1 / math.e  # 0.3679
    print(f"\n  PRE-REGISTERED PREDICTION:")
    print(f"    Critical density = 1/e = {predicted_density:.6f}")
    print(f"    Range: [0.32, 0.42]")
    print(f"    Critical = smallest density where accuracy >= 95% of unpruned")

    # ── Build MLP ──
    section("Training MLP on synthetic MNIST-like data")
    print("  (Using numpy MLP with synthetic 784->300->100->10 architecture)")

    # Reduced MLP for CPU feasibility (same architecture pattern, smaller dims)
    # Original lottery ticket paper uses 784-300-100-10; we use 100-64-32-10
    n_features = 100
    n_hidden1 = 64
    n_hidden2 = 32
    n_classes = 10
    n_train = 1000
    n_test = 200

    np.random.seed(42)

    # Generate structured synthetic data (10 cluster centers)
    centers = np.random.randn(n_classes, n_features) * 2
    X_train = np.zeros((n_train, n_features))
    y_train = np.zeros(n_train, dtype=int)
    for i in range(n_train):
        c = i % n_classes
        X_train[i] = centers[c] + np.random.randn(n_features) * 0.5
        y_train[i] = c

    X_test = np.zeros((n_test, n_features))
    y_test = np.zeros(n_test, dtype=int)
    for i in range(n_test):
        c = i % n_classes
        X_test[i] = centers[c] + np.random.randn(n_features) * 0.5
        y_test[i] = c

    # Normalize
    X_train = X_train / (np.linalg.norm(X_train, axis=1, keepdims=True) + 1e-10)
    X_test = X_test / (np.linalg.norm(X_test, axis=1, keepdims=True) + 1e-10)

    # Initialize MLP weights
    def init_weights():
        W1 = np.random.randn(n_features, n_hidden1) * np.sqrt(2.0 / n_features)
        b1 = np.zeros(n_hidden1)
        W2 = np.random.randn(n_hidden1, n_hidden2) * np.sqrt(2.0 / n_hidden1)
        b2 = np.zeros(n_hidden2)
        W3 = np.random.randn(n_hidden2, n_classes) * np.sqrt(2.0 / n_hidden2)
        b3 = np.zeros(n_classes)
        return [W1, b1, W2, b2, W3, b3]

    def forward_mlp(x, weights, masks=None):
        W1, b1, W2, b2, W3, b3 = weights
        if masks is not None:
            W1 = W1 * masks[0]
            W2 = W2 * masks[1]
            W3 = W3 * masks[2]
        h1 = np.maximum(0, x @ W1 + b1)
        h2 = np.maximum(0, h1 @ W2 + b2)
        out = h2 @ W3 + b3
        return out

    def evaluate(weights, X, y, masks=None):
        correct = 0
        for i in range(len(X)):
            out = forward_mlp(X[i], weights, masks)
            if np.argmax(out) == y[i]:
                correct += 1
        return correct / len(X)

    def train_mlp(weights, X, y, masks=None, n_epochs=15, lr=0.001, batch_size=32):
        """Train with mini-batch SGD using numerical gradient approximation."""
        rng = np.random.RandomState(42)
        for epoch in range(n_epochs):
            indices = rng.permutation(len(X))
            for start in range(0, len(X), batch_size):
                batch_idx = indices[start:start+batch_size]
                x_batch = X[batch_idx]
                y_batch = y[batch_idx]

                # Forward
                W1, b1, W2, b2, W3, b3 = weights
                if masks is not None:
                    mW1, mW2, mW3 = W1 * masks[0], W2 * masks[1], W3 * masks[2]
                else:
                    mW1, mW2, mW3 = W1, W2, W3

                h1 = np.maximum(0, x_batch @ mW1 + b1)
                h2 = np.maximum(0, h1 @ mW2 + b2)
                logits = h2 @ mW3 + b3

                # Softmax + cross-entropy gradient (backprop)
                exp_logits = np.exp(logits - logits.max(axis=1, keepdims=True))
                probs = exp_logits / exp_logits.sum(axis=1, keepdims=True)

                # Output gradient
                dlogits = probs.copy()
                for i, yi in enumerate(y_batch):
                    dlogits[i, yi] -= 1
                dlogits /= len(y_batch)

                # Backprop layer 3
                dW3 = h2.T @ dlogits
                db3 = dlogits.sum(axis=0)
                dh2 = dlogits @ mW3.T

                # ReLU
                dh2 = dh2 * (h2 > 0)

                # Backprop layer 2
                dW2 = h1.T @ dh2
                db2 = dh2.sum(axis=0)
                dh1 = dh2 @ mW2.T

                # ReLU
                dh1 = dh1 * (h1 > 0)

                # Backprop layer 1
                dW1 = x_batch.T @ dh1
                db1 = dh1.sum(axis=0)

                # Apply masks to gradients
                if masks is not None:
                    dW1 *= masks[0]
                    dW2 *= masks[1]
                    dW3 *= masks[2]

                # Update
                weights[0] -= lr * dW1
                weights[1] -= lr * db1
                weights[2] -= lr * dW2
                weights[3] -= lr * db2
                weights[4] -= lr * dW3
                weights[5] -= lr * db3

        return weights

    # ── Initial training (full network) ──
    print("  Training full network...")
    t0 = time.time()
    initial_weights = init_weights()
    # Save initial weights for lottery ticket reset
    saved_init = [w.copy() for w in initial_weights]

    weights = [w.copy() for w in initial_weights]
    weights = train_mlp(weights, X_train, y_train, n_epochs=20, lr=0.002)
    baseline_acc = evaluate(weights, X_test, y_test)
    print(f"  Baseline accuracy (full network): {baseline_acc:.4f}")
    print(f"  Training time: {time.time()-t0:.1f}s")

    total_params = sum(w.size for w in [weights[0], weights[2], weights[4]])
    print(f"  Total weight parameters: {total_params:,}")

    # ── Iterative Magnitude Pruning ──
    section("Iterative Magnitude Pruning")
    print(f"  Protocol: prune 20% of remaining weights per round, reset to init, retrain")
    print(f"  Critical density = smallest density where acc >= {0.95*baseline_acc:.4f} (95% of baseline)")
    print()

    # Masks: start with all ones
    masks = [np.ones_like(weights[0]), np.ones_like(weights[2]), np.ones_like(weights[4])]
    trained_weights = [w.copy() for w in weights]

    prune_fraction = 0.20
    threshold_acc = 0.95 * baseline_acc
    results = []
    critical_density = None

    for round_num in range(20):  # up to 20 rounds
        # Current density
        alive = sum(m.sum() for m in masks)
        density = alive / total_params

        if density < 0.02:
            break

        # Reset to initial weights and retrain with current mask
        current_weights = [w.copy() for w in saved_init]
        current_weights = train_mlp(current_weights, X_train, y_train,
                                     masks=masks, n_epochs=15, lr=0.002)
        acc = evaluate(current_weights, X_test, y_test, masks=masks)

        results.append((density, acc))
        status = "OK" if acc >= threshold_acc else "BELOW"
        bar = "#" * int(acc * 40)
        print(f"    Round {round_num:2d} | density={density:.4f} | acc={acc:.4f} | {bar} | {status}")

        if acc < threshold_acc and critical_density is None:
            # Critical density was the PREVIOUS round
            if round_num > 0:
                critical_density = results[-2][0]
            else:
                critical_density = 1.0

        # Prune: remove 20% of remaining weights (smallest magnitude)
        # Use the retrained weights for magnitude ranking
        all_magnitudes = []
        for wi, mi in zip([current_weights[0], current_weights[2], current_weights[4]], masks):
            alive_vals = np.abs(wi[mi > 0])
            all_magnitudes.extend(alive_vals.tolist())

        if len(all_magnitudes) == 0:
            break

        cutoff = np.percentile(all_magnitudes, prune_fraction * 100)

        for j, (wi, mi) in enumerate(
            zip([current_weights[0], current_weights[2], current_weights[4]], masks)
        ):
            new_mask = mi.copy()
            new_mask[np.abs(wi) <= cutoff] = 0
            masks[j] = new_mask

        trained_weights = current_weights

    # ── Find critical density ──
    if critical_density is None:
        # Never dropped below threshold
        critical_density = results[-1][0] if results else 1.0
        print(f"\n  Note: accuracy never dropped below threshold; "
              f"using last density {critical_density:.4f}")

    # ── ASCII chart ──
    section("Accuracy vs Density")
    if results:
        max_a = max(a for _, a in results)
        min_a = min(a for _, a in results)
        chart_w = 45
        for density, acc in results:
            if max_a > min_a:
                bar_len = int((acc - min_a) / (max_a - min_a) * chart_w)
            else:
                bar_len = chart_w // 2
            gz_mark = " <-- 1/e" if abs(density - 1/math.e) < 0.05 else ""
            crit_mark = " *** CRITICAL" if abs(density - critical_density) < 0.01 else ""
            print(f"    d={density:.3f} |{'#' * bar_len}{' ' * (chart_w - bar_len)}| {acc:.4f}{gz_mark}{crit_mark}")

    # ── Grade ──
    section("GRADING Prediction 3")
    print(f"  Critical density (last above 95% baseline): {critical_density:.4f}")
    status = grade(predicted_density, critical_density, 0.05, "Critical density = 1/e?")

    # Also check if critical density is in GZ
    in_gz = GZ_LOWER <= critical_density <= GZ_UPPER
    print(f"\n  Critical density in Golden Zone [{GZ_LOWER:.4f}, {GZ_UPPER:.4f}]? {'YES' if in_gz else 'NO'}")

    return status


# ═══════════════════════════════════════════════════════════════
#  PREDICTION 1 (smaller scale for speed): N=16,32 first, then N=64
# ═══════════════════════════════════════════════════════════════

def run_prediction_1_multiscale():
    banner("PREDICTION 1: MoE Optimal k/N (Multi-scale)")

    # ── State prediction BEFORE measurement ──
    print(f"\n  PRE-REGISTERED PREDICTION:")
    print(f"    For MoE with N experts, optimal k/N -> 1/e = {1/math.e:.4f}")
    print(f"    Sub-prediction P1a: optimal k/N = 1/e (active = inhibition)")
    print(f"    Sub-prediction P1b: optimal k/N = 1-1/e (inactive = inhibition)")
    print(f"    Tolerance: +/- 0.08")

    all_results = {}

    for N in [8, 16, 32]:
        section(f"N = {N} experts")

        k_values = list(range(1, N, max(1, N // 12)))
        if N not in [v for v in k_values]:
            pass  # Don't include k=N (all experts active)
        n_seeds = 3
        results = {}

        t0 = time.time()
        for k in k_values:
            if k >= N:
                continue
            accs = []
            for seed in range(n_seeds):
                acc = train_moe_topk(
                    n_experts=N, k=k, n_features=16, n_classes=8,
                    n_train=300, n_test=80, n_epochs=10, lr=0.01,
                    seed=seed * 1000 + k + N * 100
                )
                accs.append(acc)
            mean_acc = np.mean(accs)
            results[k] = mean_acc

            ratio = k / N
            bar = "#" * int(mean_acc * 40)
            marker = ""
            if abs(ratio - 1/math.e) < 0.06:
                marker = " <-- 1/e"
            elif abs(ratio - (1 - 1/math.e)) < 0.06:
                marker = " <-- 1-1/e"
            print(f"    k={k:2d} (k/N={ratio:.3f}) | acc={mean_acc:.4f} | {bar}{marker}")

        best_k = max(results, key=lambda k: results[k])
        best_ratio = best_k / N
        all_results[N] = (best_k, best_ratio, results[best_k])
        print(f"  -> Best: k={best_k}, k/N={best_ratio:.4f}, acc={results[best_k]:.4f}")
        print(f"     Elapsed: {time.time()-t0:.1f}s")

    # ── Summary ──
    section("Multi-scale Summary")
    print(f"\n  {'N':>4} | {'Best k':>6} | {'k/N':>6} | {'1/e':>6} | {'1-1/e':>6} | {'Closest':>10}")
    print(f"  {'─'*4}─┼─{'─'*6}─┼─{'─'*6}─┼─{'─'*6}─┼─{'─'*6}─┼─{'─'*10}")
    for N in sorted(all_results.keys()):
        best_k, ratio, acc = all_results[N]
        d_a = abs(ratio - 1/math.e)
        d_b = abs(ratio - (1 - 1/math.e))
        closest = "1/e" if d_a < d_b else "1-1/e"
        print(f"  {N:4d} | {best_k:6d} | {ratio:6.4f} | {1/math.e:6.4f} | {1-1/math.e:6.4f} | {closest:>10}")

    # ── Grade using largest N ──
    largest_N = max(all_results.keys())
    _, best_ratio, _ = all_results[largest_N]
    section(f"GRADING Prediction 1 (N={largest_N})")
    status_a = grade(1/math.e, best_ratio, 0.08, f"P1a: k/N = 1/e at N={largest_N}?")
    status_b = grade(1 - 1/math.e, best_ratio, 0.08, f"P1b: k/N = 1-1/e at N={largest_N}?")

    if "CONFIRMED" in status_a or "CONFIRMED" in status_b:
        overall = "CONFIRMED"
    elif "PARTIALLY" in status_a or "PARTIALLY" in status_b:
        overall = "PARTIALLY CONFIRMED"
    else:
        overall = "REFUTED"
    print(f"\n  OVERALL P1: {overall}")
    return overall


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    banner("GOLDEN ZONE PREDICTIVE EXPERIMENTS")
    print(f"  Date: 2026-03-28")
    print(f"  Goal: Test GZ as a PREDICTIVE theory (not post-hoc)")
    print(f"  GZ constants: center=1/e={1/math.e:.6f}, width=ln(4/3)={math.log(4/3):.6f}")
    print(f"  Predictions stated BEFORE each measurement.")

    results = {}

    # P5 first (instant, pure math)
    results['P5'] = run_prediction_5()

    # P1 (MoE sweep -- computationally moderate)
    results['P1'] = run_prediction_1_multiscale()

    # P3 (Lottery ticket -- moderate)
    results['P3'] = run_prediction_3()

    # ═══ Final Summary ═══
    banner("FINAL RESULTS SUMMARY")
    print(f"\n  {'Prediction':>30} | {'Status':>25}")
    print(f"  {'─'*30}─┼─{'─'*25}")
    for key in ['P1', 'P3', 'P5']:
        labels = {
            'P1': 'MoE k/N -> 1/e',
            'P3': 'Lottery ticket density ~ 1/e',
            'P5': 'R_EB(ln(4/3)) = 1/3',
        }
        print(f"  {labels[key]:>30} | {results[key]:>25}")
    print(f"  {'Transformer head pruning':>30} | {'DEFERRED':>25}")
    print(f"  {'Batch size ratio in GZ':>30} | {'DEFERRED':>25}")

    confirmed = sum(1 for v in results.values() if "CONFIRMED" in v and "PARTIALLY" not in v)
    partial = sum(1 for v in results.values() if "PARTIALLY" in v)
    refuted = sum(1 for v in results.values() if "REFUTED" in v)

    print(f"\n  Score: {confirmed} confirmed, {partial} partial, {refuted} refuted out of 3 tested")
    print(f"\n  Interpretation:")
    if confirmed >= 2:
        print(f"    GZ shows genuine predictive power in multiple domains.")
    elif confirmed + partial >= 2:
        print(f"    GZ shows some predictive signal but needs refinement.")
    else:
        print(f"    GZ fails as a predictive theory in these tests.")
        print(f"    Post-hoc fitting is more likely than genuine prediction.")

    print(f"\n{'='*70}")
    print(f"  END OF PREDICTIVE EXPERIMENTS")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
