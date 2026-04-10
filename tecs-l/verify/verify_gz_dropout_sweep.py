#!/usr/bin/env python3
"""GZ Offensive Task 3: Dropout Optimality Sweep
Tests optimal dropout ≈ 1/e across datasets. Pure numpy implementation.
"""
import numpy as np
from sklearn.datasets import load_digits, load_wine
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import sys
sys.path.insert(0, "/Users/ghost/Dev/TECS-L")

np.random.seed(42)
GZ_CENTER = 1 / np.e
GZ_UPPER = 0.5
GZ_LOWER = 0.5 - np.log(4 / 3)

DROPOUT_RATES = [0.0, 0.1, 0.2, 0.25, 0.3, 0.35, 0.37, 0.4, 0.45, 0.5, 0.6]
EPOCHS = 100
LR = 0.01
BATCH_SIZE = 64
HIDDEN_DIM = 64


def softmax(x):
    x = x - x.max(axis=1, keepdims=True)
    ex = np.exp(x)
    return ex / ex.sum(axis=1, keepdims=True)


def relu(x):
    return np.maximum(0, x)


def relu_grad(x):
    return (x > 0).astype(float)


def cross_entropy_loss(probs, y):
    n = len(y)
    log_probs = np.log(probs[np.arange(n), y] + 1e-9)
    return -log_probs.mean()


def train_and_eval(X_train, y_train, X_test, y_test, dropout_p, hidden_dim=HIDDEN_DIM):
    in_dim = X_train.shape[1]
    n_classes = len(np.unique(y_train))
    n_train = len(X_train)

    # Xavier init
    rng = np.random.default_rng(42)
    W1 = rng.standard_normal((in_dim, hidden_dim)) * np.sqrt(2.0 / in_dim)
    b1 = np.zeros(hidden_dim)
    W2 = rng.standard_normal((hidden_dim, n_classes)) * np.sqrt(2.0 / hidden_dim)
    b2 = np.zeros(n_classes)

    for epoch in range(EPOCHS):
        # Shuffle
        idx = rng.permutation(n_train)
        X_shuf = X_train[idx]
        y_shuf = y_train[idx]

        for start in range(0, n_train, BATCH_SIZE):
            Xb = X_shuf[start:start + BATCH_SIZE]
            yb = y_shuf[start:start + BATCH_SIZE]
            bs = len(Xb)

            # Forward pass
            z1 = Xb @ W1 + b1          # (bs, hidden)
            a1 = relu(z1)              # (bs, hidden)

            # Inverted dropout
            if dropout_p > 0.0:
                mask = (rng.random((bs, hidden_dim)) > dropout_p).astype(float)
                mask /= (1.0 - dropout_p)
                a1_drop = a1 * mask
            else:
                mask = np.ones((bs, hidden_dim))
                a1_drop = a1

            z2 = a1_drop @ W2 + b2     # (bs, n_classes)
            probs = softmax(z2)        # (bs, n_classes)

            # Backward pass
            dz2 = probs.copy()
            dz2[np.arange(bs), yb] -= 1
            dz2 /= bs

            dW2 = a1_drop.T @ dz2
            db2 = dz2.sum(axis=0)

            da1_drop = dz2 @ W2.T
            da1 = da1_drop * mask
            dz1 = da1 * relu_grad(z1)

            dW1 = Xb.T @ dz1
            db1 = dz1.sum(axis=0)

            # Update
            W1 -= LR * dW1
            b1 -= LR * db1
            W2 -= LR * dW2
            b2 -= LR * db2

    # Evaluate (no dropout)
    z1 = X_test @ W1 + b1
    a1 = relu(z1)
    z2 = a1 @ W2 + b2
    probs = softmax(z2)
    preds = probs.argmax(axis=1)
    acc = (preds == y_test).mean()
    return acc


def run_dataset(name, X, y):
    print(f"\n{'='*55}")
    print(f"Dataset: {name}  (samples={len(X)}, features={X.shape[1]}, classes={len(np.unique(y))})")
    print(f"{'='*55}")

    scaler = StandardScaler()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    results = []
    for p in DROPOUT_RATES:
        acc = train_and_eval(X_train, y_train, X_test, y_test, dropout_p=p)
        results.append((p, acc))

    best_p, best_acc = max(results, key=lambda x: x[1])

    print(f"\n{'Dropout':>10}  {'Accuracy':>10}  {'Best?':>6}")
    print("-" * 35)
    for p, acc in results:
        marker = " <-- BEST" if p == best_p else ""
        in_gz = GZ_LOWER <= p <= GZ_UPPER
        gz_tag = " [GZ]" if in_gz else ""
        print(f"{p:>10.3f}  {acc:>10.4f}{marker}{gz_tag}")

    dist_to_center = abs(best_p - GZ_CENTER)
    in_golden_zone = GZ_LOWER <= best_p <= GZ_UPPER

    print(f"\n  Optimal dropout:  {best_p:.3f}")
    print(f"  Best accuracy:    {best_acc:.4f}")
    print(f"  GZ center (1/e):  {GZ_CENTER:.4f}")
    print(f"  Distance to 1/e:  {dist_to_center:.4f}")
    print(f"  In Golden Zone:   {'YES' if in_golden_zone else 'NO'} [{GZ_LOWER:.4f}, {GZ_UPPER:.4f}]")

    return best_p, best_acc, dist_to_center, in_golden_zone


def main():
    print("=" * 55)
    print("GZ Offensive Task 3: Dropout Optimality Sweep")
    print(f"Golden Zone: [{GZ_LOWER:.4f}, {GZ_UPPER:.4f}]")
    print(f"GZ center (1/e): {GZ_CENTER:.4f}")
    print(f"Epochs: {EPOCHS}, LR: {LR}, Batch: {BATCH_SIZE}, Hidden: {HIDDEN_DIM}")
    print("=" * 55)

    datasets = []

    digits = load_digits()
    datasets.append(("load_digits", digits.data, digits.target))

    wine = load_wine()
    datasets.append(("load_wine", wine.data, wine.target))

    summary = []
    for name, X, y in datasets:
        best_p, best_acc, dist, in_gz = run_dataset(name, X, y)
        summary.append((name, best_p, best_acc, dist, in_gz))

    print("\n" + "=" * 55)
    print("SUMMARY")
    print("=" * 55)
    print(f"\n{'Dataset':>15}  {'Opt.Dropout':>12}  {'Accuracy':>10}  {'Dist 1/e':>10}  {'In GZ':>6}")
    print("-" * 65)
    for name, best_p, best_acc, dist, in_gz in summary:
        print(f"{name:>15}  {best_p:>12.3f}  {best_acc:>10.4f}  {dist:>10.4f}  {'YES' if in_gz else 'NO':>6}")

    optimal_dropouts = [s[1] for s in summary]
    mean_opt = np.mean(optimal_dropouts)
    mean_dist = abs(mean_opt - GZ_CENTER)
    all_in_gz = all(s[4] for s in summary)

    print(f"\n  Mean optimal dropout: {mean_opt:.4f}")
    print(f"  GZ center (1/e):      {GZ_CENTER:.4f}")
    print(f"  Mean distance 1/e:    {mean_dist:.4f}")
    print(f"  All in Golden Zone:   {'YES' if all_in_gz else 'NO'}")

    # Grading
    print("\n" + "=" * 55)
    print("GRADING")
    print("=" * 55)
    if mean_dist < 0.05 and all_in_gz:
        grade = "Strong support (GZ center confirmed)"
        symbol = "GZ-CENTER"
    elif all_in_gz:
        grade = "Moderate support (all optimal in GZ)"
        symbol = "GZ-IN"
    elif any(s[4] for s in summary):
        grade = "Weak support (some optimal in GZ)"
        symbol = "GZ-PARTIAL"
    else:
        grade = "No support (optimal outside GZ)"
        symbol = "GZ-MISS"

    print(f"  Grade: {symbol}")
    print(f"  Interpretation: {grade}")
    print(f"\n  GZ hypothesis: optimal dropout in [{GZ_LOWER:.4f}, {GZ_UPPER:.4f}]")
    for name, best_p, best_acc, dist, in_gz in summary:
        status = "PASS" if in_gz else "FAIL"
        print(f"    {name}: dropout={best_p:.3f} -> {status}")


if __name__ == "__main__":
    main()
