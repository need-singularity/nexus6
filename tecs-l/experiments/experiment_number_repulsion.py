#!/usr/bin/env python3
"""NUMBER THEORY / ARITHMETIC — Repulsion Field Experiment

Classify numbers 1-1000 by mathematical properties:
  Class 0: Prime numbers
  Class 1: Perfect squares
  Class 2: Fibonacci numbers
  Class 3: Powers of 2
  Class 4: Other

Features per number n:
  - n / 1000 (normalized)
  - n mod 2, n mod 3, n mod 6 (divisibility patterns)
  - digit sum (normalized)
  - tau(n) = number of divisors (normalized)
  - is_even (0/1)
  - last digit / 9
  - log(n) / log(1000)
  - sum of proper divisors / n (abundancy-like)

Pure Python + numpy. No external ML libraries.
"""

import numpy as np
import time
import math

np.random.seed(42)

# ─────────────────────────────────────────
# Number Theory Helpers
# ─────────────────────────────────────────

def is_prime(n):
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def count_divisors(n):
    if n <= 0:
        return 0
    count = 0
    for i in range(1, int(math.isqrt(n)) + 1):
        if n % i == 0:
            count += 2 if i != n // i else 1
    return count


def sum_proper_divisors(n):
    if n <= 1:
        return 0
    s = 1
    for i in range(2, int(math.isqrt(n)) + 1):
        if n % i == 0:
            s += i
            if i != n // i:
                s += n // i
    return s


def digit_sum(n):
    return sum(int(d) for d in str(n))


def make_fibonacci_set(limit):
    fibs = set()
    a, b = 1, 1
    while a <= limit:
        fibs.add(a)
        a, b = b, a + b
    return fibs


def make_powers_of_2_set(limit):
    pows = set()
    p = 1
    while p <= limit:
        pows.add(p)
        p *= 2
    return pows


def make_perfect_squares_set(limit):
    squares = set()
    i = 1
    while i * i <= limit:
        squares.add(i * i)
        i += 1
    return squares


# ─────────────────────────────────────────
# Dataset Generation
# ─────────────────────────────────────────

def generate_dataset(N=1000):
    """Generate features and labels for numbers 1..N."""
    fibs = make_fibonacci_set(N)
    pow2s = make_powers_of_2_set(N)
    squares = make_perfect_squares_set(N)

    X = []
    y = []
    class_names = {0: 'Prime', 1: 'PerfSquare', 2: 'Fibonacci', 3: 'Pow2', 4: 'Other'}

    for n in range(1, N + 1):
        # Label (priority: Pow2 > Fib > PerfSquare > Prime > Other)
        if n in pow2s:
            label = 3
        elif n in fibs:
            label = 2
        elif n in squares:
            label = 1
        elif is_prime(n):
            label = 0
        else:
            label = 4

        # Features (10-dim)
        tau_n = count_divisors(n)
        spd = sum_proper_divisors(n)
        features = [
            n / N,                              # normalized n
            (n % 2) / 1.0,                      # mod 2
            (n % 3) / 2.0,                      # mod 3 normalized
            (n % 6) / 5.0,                      # mod 6 normalized
            digit_sum(n) / 36.0,                # digit sum normalized (max ~27 for 999)
            tau_n / 30.0,                        # divisor count normalized
            1.0 if n % 2 == 0 else 0.0,         # is_even
            (n % 10) / 9.0,                      # last digit normalized
            math.log(max(n, 1)) / math.log(N),  # log normalized
            spd / max(n, 1),                     # abundancy-like ratio
        ]
        X.append(features)
        y.append(label)

    X = np.array(X, dtype=np.float64)
    y = np.array(y, dtype=np.int64)

    # Standardize features
    mean = X.mean(axis=0)
    std = X.std(axis=0) + 1e-8
    X = (X - mean) / std

    return X, y, class_names


# ─────────────────────────────────────────
# Activation Functions (numpy)
# ─────────────────────────────────────────

def relu(x):
    return np.maximum(0, x)


def relu_grad(x):
    return (x > 0).astype(np.float64)


def softmax(x):
    ex = np.exp(x - x.max(axis=1, keepdims=True))
    return ex / ex.sum(axis=1, keepdims=True)


def tanh(x):
    return np.tanh(x)


def tanh_grad(x):
    return 1 - np.tanh(x) ** 2


# ─────────────────────────────────────────
# Dense Baseline (2-layer MLP)
# ─────────────────────────────────────────

class DenseBaseline:
    def __init__(self, input_dim, hidden_dim, output_dim):
        scale1 = np.sqrt(2.0 / input_dim)
        scale2 = np.sqrt(2.0 / hidden_dim)
        self.W1 = np.random.randn(input_dim, hidden_dim) * scale1
        self.b1 = np.zeros(hidden_dim)
        self.W2 = np.random.randn(hidden_dim, output_dim) * scale2
        self.b2 = np.zeros(output_dim)

    def forward(self, X):
        self.X = X
        self.z1 = X @ self.W1 + self.b1
        self.a1 = relu(self.z1)
        self.z2 = self.a1 @ self.W2 + self.b2
        self.probs = softmax(self.z2)
        return self.probs

    def backward(self, y, lr=0.01):
        m = y.shape[0]
        # Output gradient (cross-entropy + softmax)
        dz2 = self.probs.copy()
        dz2[np.arange(m), y] -= 1
        dz2 /= m

        dW2 = self.a1.T @ dz2
        db2 = dz2.sum(axis=0)

        da1 = dz2 @ self.W2.T
        dz1 = da1 * relu_grad(self.z1)

        dW1 = self.X.T @ dz1
        db1 = dz1.sum(axis=0)

        # Gradient clipping
        for g in [dW1, db1, dW2, db2]:
            np.clip(g, -5.0, 5.0, out=g)

        self.W2 -= lr * dW2
        self.b2 -= lr * db2
        self.W1 -= lr * dW1
        self.b1 -= lr * db1

    def predict(self, X):
        z1 = X @ self.W1 + self.b1
        a1 = relu(z1)
        z2 = a1 @ self.W2 + self.b2
        probs = softmax(z2)
        return probs.argmax(axis=1)

    def param_count(self):
        return self.W1.size + self.b1.size + self.W2.size + self.b2.size


# ─────────────────────────────────────────
# Repulsion Field (two-pole with tension)
# ─────────────────────────────────────────

class RepulsionField:
    """Two-pole repulsion field for classification.

    pole+ and pole- are separate MLPs.
    output = equilibrium + tension_scale * sqrt(tension) * field_direction
    tension = ||pole+ - pole-||^2

    tension_scale initialized to 1/3 (meta fixed point from CLAUDE.md).
    """
    def __init__(self, input_dim, hidden_dim, output_dim):
        scale1 = np.sqrt(2.0 / input_dim)
        scale2 = np.sqrt(2.0 / hidden_dim)
        scalef = np.sqrt(2.0 / output_dim)

        # Pole +
        self.Wp1 = np.random.randn(input_dim, hidden_dim) * scale1
        self.bp1 = np.zeros(hidden_dim)
        self.Wp2 = np.random.randn(hidden_dim, output_dim) * scale2
        self.bp2 = np.zeros(output_dim)

        # Pole -
        self.Wm1 = np.random.randn(input_dim, hidden_dim) * scale1
        self.bm1 = np.zeros(hidden_dim)
        self.Wm2 = np.random.randn(hidden_dim, output_dim) * scale2
        self.bm2 = np.zeros(output_dim)

        # Field transform (output_dim -> output_dim with tanh)
        self.Wf = np.random.randn(output_dim, output_dim) * scalef
        self.bf = np.zeros(output_dim)

        # Tension scale = 1/3 (meta fixed point)
        self.tension_scale = 1.0 / 3.0

        # Storage for analysis
        self.per_sample_tension = None
        self.tension_magnitude = 0.0

    def forward(self, X):
        self.X = X
        m = X.shape[0]

        # Pole +
        self.zp1 = X @ self.Wp1 + self.bp1
        self.ap1 = relu(self.zp1)
        self.out_plus = self.ap1 @ self.Wp2 + self.bp2

        # Pole -
        self.zm1 = X @ self.Wm1 + self.bm1
        self.am1 = relu(self.zm1)
        self.out_minus = self.am1 @ self.Wm2 + self.bm2

        # Repulsion and tension
        self.repulsion = self.out_plus - self.out_minus
        self.tension = (self.repulsion ** 2).sum(axis=1, keepdims=True)  # (m, 1)
        self.equilibrium = (self.out_plus + self.out_minus) / 2.0

        # Field direction (tanh transform)
        self.field_pre = self.repulsion @ self.Wf + self.bf
        self.field_dir = tanh(self.field_pre)

        # Output
        self.sqrt_tension = np.sqrt(self.tension + 1e-8)  # (m, 1)
        self.output = self.equilibrium + self.tension_scale * self.sqrt_tension * self.field_dir

        self.probs = softmax(self.output)

        # Store tension for analysis
        self.per_sample_tension = self.tension.squeeze(1)
        self.tension_magnitude = float(self.tension.mean())

        return self.probs

    def backward(self, y, lr=0.01):
        m = y.shape[0]

        # dL/d(output) via cross-entropy + softmax
        d_out = self.probs.copy()
        d_out[np.arange(m), y] -= 1
        d_out /= m

        # output = eq + ts * sqrt_t * field_dir
        # d_eq
        d_eq = d_out

        # d_field_dir
        d_field_dir = d_out * self.tension_scale * self.sqrt_tension

        # d_sqrt_tension
        d_sqrt_t = (d_out * self.tension_scale * self.field_dir).sum(axis=1, keepdims=True)

        # d(field_pre) via tanh
        d_field_pre = d_field_dir * tanh_grad(self.field_pre)
        dWf = self.repulsion.T @ d_field_pre
        dbf = d_field_pre.sum(axis=0)

        # d(repulsion) from field transform
        d_repulsion_from_field = d_field_pre @ self.Wf.T

        # d(tension) from sqrt
        # sqrt_tension = sqrt(tension + eps)
        # d(tension) = d(sqrt_t) / (2 * sqrt_tension)
        d_tension = d_sqrt_t / (2.0 * self.sqrt_tension + 1e-8)  # (m, 1)

        # tension = sum(repulsion^2, axis=1) -> d(repulsion) from tension
        d_repulsion_from_tension = 2.0 * self.repulsion * d_tension

        # Total d(repulsion)
        d_repulsion = d_repulsion_from_field + d_repulsion_from_tension

        # d(out_plus) and d(out_minus)
        # eq = (plus + minus) / 2
        # repulsion = plus - minus
        d_out_plus = d_eq * 0.5 + d_repulsion
        d_out_minus = d_eq * 0.5 - d_repulsion

        # Backprop through pole+ MLP
        dWp2 = self.ap1.T @ d_out_plus
        dbp2 = d_out_plus.sum(axis=0)
        dap1 = d_out_plus @ self.Wp2.T
        dzp1 = dap1 * relu_grad(self.zp1)
        dWp1 = self.X.T @ dzp1
        dbp1 = dzp1.sum(axis=0)

        # Backprop through pole- MLP
        dWm2 = self.am1.T @ d_out_minus
        dbm2 = d_out_minus.sum(axis=0)
        dam1 = d_out_minus @ self.Wm2.T
        dzm1 = dam1 * relu_grad(self.zm1)
        dWm1 = self.X.T @ dzm1
        dbm1 = dzm1.sum(axis=0)

        # Gradient clipping
        for g in [dWp1, dbp1, dWp2, dbp2, dWm1, dbm1, dWm2, dbm2, dWf, dbf]:
            np.clip(g, -5.0, 5.0, out=g)

        # Update
        self.Wp1 -= lr * dWp1
        self.bp1 -= lr * dbp1
        self.Wp2 -= lr * dWp2
        self.bp2 -= lr * dbp2
        self.Wm1 -= lr * dWm1
        self.bm1 -= lr * dbm1
        self.Wm2 -= lr * dWm2
        self.bm2 -= lr * dbm2
        self.Wf  -= lr * dWf
        self.bf  -= lr * dbf

    def predict(self, X):
        # Forward pass without storing gradients
        zp1 = X @ self.Wp1 + self.bp1
        ap1 = relu(zp1)
        out_plus = ap1 @ self.Wp2 + self.bp2

        zm1 = X @ self.Wm1 + self.bm1
        am1 = relu(zm1)
        out_minus = am1 @ self.Wm2 + self.bm2

        repulsion = out_plus - out_minus
        tension = (repulsion ** 2).sum(axis=1, keepdims=True)
        equilibrium = (out_plus + out_minus) / 2.0

        field_pre = repulsion @ self.Wf + self.bf
        field_dir = tanh(field_pre)
        sqrt_t = np.sqrt(tension + 1e-8)

        output = equilibrium + self.tension_scale * sqrt_t * field_dir
        probs = softmax(output)

        self.per_sample_tension = tension.squeeze(1)
        self.tension_magnitude = float(tension.mean())

        return probs.argmax(axis=1)

    def get_tension_for(self, X):
        """Get per-sample tension without classification."""
        zp1 = X @ self.Wp1 + self.bp1
        ap1 = relu(zp1)
        out_plus = ap1 @ self.Wp2 + self.bp2

        zm1 = X @ self.Wm1 + self.bm1
        am1 = relu(zm1)
        out_minus = am1 @ self.Wm2 + self.bm2

        repulsion = out_plus - out_minus
        tension = (repulsion ** 2).sum(axis=1)
        return tension

    def param_count(self):
        total = 0
        for arr in [self.Wp1, self.bp1, self.Wp2, self.bp2,
                     self.Wm1, self.bm1, self.Wm2, self.bm2,
                     self.Wf, self.bf]:
            total += arr.size
        return total


# ─────────────────────────────────────────
# Training
# ─────────────────────────────────────────

def train_model(model, X_train, y_train, X_val, y_val,
                epochs=200, lr=0.01, batch_size=64, verbose=False):
    """Train a model (Dense or Repulsion), return best val accuracy."""
    n = X_train.shape[0]
    best_acc = 0.0
    best_epoch = 0

    for epoch in range(epochs):
        # Shuffle
        idx = np.random.permutation(n)
        X_shuf = X_train[idx]
        y_shuf = y_train[idx]

        # Mini-batch training
        for start in range(0, n, batch_size):
            end = min(start + batch_size, n)
            Xb = X_shuf[start:end]
            yb = y_shuf[start:end]
            model.forward(Xb)
            model.backward(yb, lr=lr)

        # Evaluate
        preds = model.predict(X_val)
        acc = (preds == y_val).mean()
        if acc > best_acc:
            best_acc = acc
            best_epoch = epoch

        if verbose and (epoch + 1) % 50 == 0:
            print(f"    epoch {epoch+1:3d}: val_acc={acc:.4f} (best={best_acc:.4f} @ {best_epoch})")

    return best_acc, best_epoch


# ─────────────────────────────────────────
# Cross-Validation
# ─────────────────────────────────────────

def stratified_kfold(y, n_folds=5, seed=42):
    """Simple stratified k-fold split."""
    rng = np.random.RandomState(seed)
    classes = np.unique(y)
    fold_indices = [[] for _ in range(n_folds)]

    for c in classes:
        idx = np.where(y == c)[0]
        rng.shuffle(idx)
        splits = np.array_split(idx, n_folds)
        for f in range(n_folds):
            fold_indices[f].extend(splits[f].tolist())

    # Shuffle within each fold
    for f in range(n_folds):
        rng.shuffle(fold_indices[f])

    folds = []
    all_idx = np.arange(len(y))
    for f in range(n_folds):
        val_idx = np.array(fold_indices[f])
        train_idx = np.setdiff1d(all_idx, val_idx)
        folds.append((train_idx, val_idx))

    return folds


def run_experiment(X, y, class_names, hidden_dim=64, epochs=200, lr=0.01,
                   n_folds=5, seeds=[42, 123, 777]):
    """Run full CV comparison: Dense vs RepulsionField."""

    n_classes = len(np.unique(y))
    input_dim = X.shape[1]

    print(f"\n{'='*65}")
    print(f"  NUMBER THEORY REPULSION FIELD EXPERIMENT")
    print(f"  {X.shape[0]} numbers, {input_dim} features, {n_classes} classes")
    print(f"  hidden_dim={hidden_dim}, epochs={epochs}, {n_folds}-fold x {len(seeds)} seeds")
    print(f"{'='*65}")

    # Class distribution
    print(f"\n  --- Class Distribution ---")
    for c in sorted(class_names.keys()):
        count = (y == c).sum()
        print(f"    Class {c} ({class_names[c]:>12s}): {count:4d} samples ({count/len(y)*100:5.1f}%)")

    dense_accs = []
    repul_accs = []
    tension_by_class = {c: [] for c in range(n_classes)}
    tension_overall = []

    for seed in seeds:
        folds = stratified_kfold(y, n_folds=n_folds, seed=seed)

        for fold_i, (train_idx, val_idx) in enumerate(folds):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            # Dense baseline
            np.random.seed(seed + fold_i)
            dense = DenseBaseline(input_dim, hidden_dim, n_classes)
            acc_d, _ = train_model(dense, X_train, y_train, X_val, y_val,
                                   epochs=epochs, lr=lr)
            dense_accs.append(acc_d)

            # Repulsion field
            np.random.seed(seed + fold_i)
            repul = RepulsionField(input_dim, hidden_dim, n_classes)
            acc_r, _ = train_model(repul, X_train, y_train, X_val, y_val,
                                   epochs=epochs, lr=lr)
            repul_accs.append(acc_r)

            # Tension analysis on validation set
            repul.predict(X_val)  # triggers tension computation
            tension_overall.append(repul.tension_magnitude)

            t_vals = repul.per_sample_tension
            for c in range(n_classes):
                mask = y_val == c
                if mask.any():
                    tension_by_class[c].append(float(t_vals[mask].mean()))

        print(f"    seed {seed} done  |  Dense={np.mean(dense_accs[-n_folds:])*100:.1f}%  Repulsion={np.mean(repul_accs[-n_folds:])*100:.1f}%")

    # ─── Results ───
    dense_arr = np.array(dense_accs)
    repul_arr = np.array(repul_accs)
    d_mean = dense_arr.mean() * 100
    d_std = dense_arr.std() * 100
    r_mean = repul_arr.mean() * 100
    r_std = repul_arr.std() * 100
    delta = r_mean - d_mean

    print(f"\n{'='*65}")
    print(f"  ACCURACY RESULTS ({n_folds}-fold x {len(seeds)} seeds = {len(dense_accs)} runs)")
    print(f"{'='*65}")
    print(f"  Dense:        {d_mean:6.2f} +/- {d_std:.2f}%")
    print(f"  Repulsion:    {r_mean:6.2f} +/- {r_std:.2f}%")
    print(f"  Delta:        {delta:+.2f}%  {'<-- Repulsion wins' if delta > 0 else '<-- Dense wins' if delta < 0 else '(tie)'}")

    # Param count
    d_params = DenseBaseline(input_dim, hidden_dim, n_classes).param_count()
    r_params = RepulsionField(input_dim, hidden_dim, n_classes).param_count()
    print(f"  Params:       Dense={d_params:,}  Repulsion={r_params:,} ({r_params/d_params:.1f}x)")

    # ─── Tension Analysis ───
    print(f"\n{'='*65}")
    print(f"  TENSION ANALYSIS — Which number classes produce highest tension?")
    print(f"{'='*65}")

    class_tension_means = {}
    for c in sorted(tension_by_class.keys()):
        vals = tension_by_class[c]
        if vals:
            m = np.mean(vals)
            s = np.std(vals)
            class_tension_means[c] = m
            print(f"    Class {c} ({class_names[c]:>12s}): tension = {m:.4f} +/- {s:.4f}")

    if class_tension_means:
        max_c = max(class_tension_means, key=class_tension_means.get)
        min_c = min(class_tension_means, key=class_tension_means.get)
        print(f"\n    Highest tension: Class {max_c} ({class_names[max_c]}) = {class_tension_means[max_c]:.4f}")
        print(f"    Lowest tension:  Class {min_c} ({class_names[min_c]}) = {class_tension_means[min_c]:.4f}")
        if class_tension_means[min_c] > 0:
            ratio = class_tension_means[max_c] / class_tension_means[min_c]
            print(f"    Ratio (max/min): {ratio:.2f}x")

    # ─── ASCII Bar Charts ───
    print(f"\n  --- Accuracy Comparison ---")
    bar_w = 40
    for label, val in [("Dense", d_mean), ("Repulsion", r_mean)]:
        bar_len = int(val / 100 * bar_w)
        bar = '#' * bar_len + '.' * (bar_w - bar_len)
        print(f"    {label:>12s} |{bar}| {val:.2f}%")

    print(f"\n  --- Tension by Class (normalized bar) ---")
    if class_tension_means:
        max_t = max(class_tension_means.values())
        if max_t > 0:
            for c in sorted(class_tension_means.keys()):
                t = class_tension_means[c]
                bar_len = int(t / max_t * bar_w)
                bar = '#' * bar_len + '.' * (bar_w - bar_len)
                print(f"    {class_names[c]:>12s} |{bar}| {t:.4f}")

    # ─── Per-class accuracy breakdown ───
    print(f"\n  --- Per-Class Accuracy (final fold, last seed) ---")
    # Re-run one final time for per-class breakdown
    np.random.seed(777)
    folds = stratified_kfold(y, n_folds=5, seed=777)
    train_idx, val_idx = folds[0]
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]

    np.random.seed(777)
    dense_final = DenseBaseline(input_dim, hidden_dim, n_classes)
    train_model(dense_final, X_train, y_train, X_val, y_val, epochs=epochs, lr=lr)
    d_preds = dense_final.predict(X_val)

    np.random.seed(777)
    repul_final = RepulsionField(input_dim, hidden_dim, n_classes)
    train_model(repul_final, X_train, y_train, X_val, y_val, epochs=epochs, lr=lr)
    r_preds = repul_final.predict(X_val)

    print(f"    {'Class':>12s}  {'Dense':>8s}  {'Repulsion':>10s}  {'Count':>6s}")
    print(f"    {'-'*42}")
    for c in sorted(class_names.keys()):
        mask = y_val == c
        count = mask.sum()
        if count > 0:
            d_acc = (d_preds[mask] == c).mean() * 100
            r_acc = (r_preds[mask] == c).mean() * 100
            marker = " <--" if abs(r_acc - d_acc) > 5 else ""
            print(f"    {class_names[c]:>12s}  {d_acc:7.1f}%  {r_acc:9.1f}%  {count:5d}{marker}")

    # ─── Confusion Analysis ───
    print(f"\n  --- Confusion: Most confused pairs (Repulsion) ---")
    from collections import Counter
    confused = Counter()
    for true, pred in zip(y_val, r_preds):
        if true != pred:
            confused[(class_names[true], class_names[pred])] += 1
    for (true_name, pred_name), count in confused.most_common(5):
        print(f"    {true_name:>12s} -> {pred_name:<12s}: {count} errors")

    # ─── Specific Number Analysis ───
    print(f"\n  --- Tension for Notable Numbers ---")
    notable = {
        6: "perfect number",
        28: "perfect number",
        496: "perfect number",
        1: "unity",
        2: "prime+pow2+fib",
        7: "prime",
        12: "highly composite",
        60: "highly composite",
        100: "perfect square",
        137: "fine structure prime",
        256: "power of 2",
        512: "power of 2",
        233: "fibonacci prime",
        997: "largest 3-digit prime",
    }

    repul_final.predict(X)  # full dataset
    all_tension = repul_final.per_sample_tension

    print(f"    {'Number':>8s}  {'Class':>12s}  {'Tension':>10s}  {'Note'}")
    print(f"    {'-'*55}")
    for n in sorted(notable.keys()):
        idx = n - 1  # 0-indexed
        t = all_tension[idx]
        c = y[idx]
        print(f"    {n:>8d}  {class_names[c]:>12s}  {t:10.4f}  {notable[n]}")

    # ─── Summary ───
    print(f"\n{'='*65}")
    print(f"  CONCLUSION")
    print(f"{'='*65}")
    print(f"  Does tension distinguish mathematical structure?")
    if class_tension_means:
        vals = list(class_tension_means.values())
        cv = np.std(vals) / (np.mean(vals) + 1e-8)
        print(f"  Tension CV across classes: {cv:.3f}  (>0.3 = YES, meaningful variation)")
        if cv > 0.3:
            print(f"  -> YES: Tension varies significantly across number classes.")
            print(f"     The repulsion field 'feels' different mathematical structures differently.")
        else:
            print(f"  -> WEAK: Tension variation across classes is moderate.")
            print(f"     Mathematical structure creates some but not strong tension differences.")

    print(f"\n  Accuracy winner: {'Repulsion' if delta > 0 else 'Dense'} ({delta:+.2f}%)")
    print(f"  Average tension: {np.mean(tension_overall):.4f}")
    print(f"{'='*65}")

    return {
        'dense_mean': d_mean,
        'repul_mean': r_mean,
        'delta': delta,
        'tension_by_class': class_tension_means,
        'tension_avg': np.mean(tension_overall),
    }


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────

def main():
    t0 = time.time()

    X, y, class_names = generate_dataset(1000)
    print(f"  Dataset: {X.shape[0]} numbers, {X.shape[1]} features")

    results = run_experiment(
        X, y, class_names,
        hidden_dim=64,
        epochs=200,
        lr=0.005,
        n_folds=5,
        seeds=[42, 123, 777],
    )

    elapsed = time.time() - t0
    print(f"\n  Total time: {elapsed:.1f}s")


if __name__ == '__main__':
    main()
