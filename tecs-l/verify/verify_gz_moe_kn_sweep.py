#!/usr/bin/env python3
"""GZ Offensive Task 2: MoE k/N Ratio Sweep (numpy-only, lightweight)
Tests optimal k/N convergence to 1/e across expert counts.

Uses a pure numpy softmax regression MoE to avoid PyTorch segfaults
under heavy CPU load. Each "expert" is a 784->10 linear softmax.
"""
import numpy as np
import sys, struct, gzip, os, urllib.request

np.random.seed(42)

GZ_CENTER = 1.0 / np.e   # 0.3679
GZ_UPPER  = 0.5
GZ_LOWER  = 0.5 - np.log(4.0 / 3.0)  # 0.2123

EPOCHS     = 3
BATCH_SIZE = 128
N_TRAIN    = 6000
LR         = 0.05

# ---------------------------------------------------------------------------
# MNIST loader (tiny binary reader, no torchvision)
# ---------------------------------------------------------------------------
MNIST_URL = "https://storage.googleapis.com/cvdf-datasets/mnist/"
MNIST_FILES = {
    "train-images": "train-images-idx3-ubyte.gz",
    "train-labels": "train-labels-idx1-ubyte.gz",
    "test-images":  "t10k-images-idx3-ubyte.gz",
    "test-labels":  "t10k-labels-idx1-ubyte.gz",
}

def _download(url, dest):
    if not os.path.exists(dest):
        print(f"  Downloading {os.path.basename(dest)} ...", end=" ", flush=True)
        urllib.request.urlretrieve(url, dest)
        print("done")

def _read_images(path):
    with gzip.open(path, "rb") as f:
        magic, n, rows, cols = struct.unpack(">IIII", f.read(16))
        data = np.frombuffer(f.read(), dtype=np.uint8)
    return data.reshape(n, rows * cols).astype(np.float32) / 255.0

def _read_labels(path):
    with gzip.open(path, "rb") as f:
        magic, n = struct.unpack(">II", f.read(8))
        data = np.frombuffer(f.read(), dtype=np.uint8)
    return data.astype(np.int32)

def load_mnist(cache_dir="/tmp/mnist_gz"):
    os.makedirs(cache_dir, exist_ok=True)
    paths = {}
    for key, fname in MNIST_FILES.items():
        dest = os.path.join(cache_dir, fname)
        try:
            _download(MNIST_URL + fname, dest)
        except Exception:
            # Try alternate mirror
            alt = "http://yann.lecun.com/exdb/mnist/" + fname
            _download(alt, dest)
        paths[key] = dest

    X_tr = _read_images(paths["train-images"])
    y_tr = _read_labels(paths["train-labels"])
    X_te = _read_images(paths["test-images"])
    y_te = _read_labels(paths["test-labels"])
    return X_tr, y_tr, X_te, y_te

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def softmax(x):
    x = x - x.max(axis=1, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=1, keepdims=True)

def one_hot(y, n=10):
    oh = np.zeros((len(y), n), dtype=np.float32)
    oh[np.arange(len(y)), y] = 1.0
    return oh

def cross_entropy(probs, labels):
    return -np.log(probs[np.arange(len(labels)), labels] + 1e-9).mean()

# ---------------------------------------------------------------------------
# Expert: 784 -> 10 linear softmax, trained with SGD
# ---------------------------------------------------------------------------
class LinearExpert:
    def __init__(self, rng):
        self.W = rng.randn(784, 10).astype(np.float32) * 0.01
        self.b = np.zeros(10, dtype=np.float32)

    def forward(self, X):
        return softmax(X @ self.W + self.b)

    def grad_step(self, X, y_oh, lr):
        probs = self.forward(X)
        dL    = (probs - y_oh) / len(X)           # (B, 10)
        self.W -= lr * (X.T @ dL)
        self.b -= lr * dL.sum(axis=0)
        return cross_entropy(probs, y_oh.argmax(axis=1))

# ---------------------------------------------------------------------------
# TopK MoE (numpy)
# ---------------------------------------------------------------------------
class NumpyTopKMoE:
    """Gate = linear 784->N + top-k selection; combine weighted expert outputs."""

    def __init__(self, n_experts, k, rng):
        self.n = n_experts
        self.k = k
        self.experts = [LinearExpert(rng) for _ in range(n_experts)]
        self.Wg = rng.randn(784, n_experts).astype(np.float32) * 0.01
        self.bg = np.zeros(n_experts, dtype=np.float32)

    def _gate(self, X):
        """Returns gate weights (B, k) and indices (B, k)."""
        logits = X @ self.Wg + self.bg          # (B, N)
        idx    = np.argsort(-logits, axis=1)[:, :self.k]   # (B, k) top-k indices
        # gather logits for top-k
        B      = X.shape[0]
        topk_l = logits[np.arange(B)[:, None], idx]        # (B, k)
        topk_l = topk_l - topk_l.max(axis=1, keepdims=True)
        topk_e = np.exp(topk_l)
        w      = topk_e / topk_e.sum(axis=1, keepdims=True)  # (B, k) softmax weights
        return w, idx

    def forward(self, X):
        w, idx = self._gate(X)   # (B,k), (B,k)
        B      = X.shape[0]
        out    = np.zeros((B, 10), dtype=np.float32)
        for j in range(self.k):
            ej_idx = idx[:, j]   # which expert for each sample at position j
            wj     = w[:, j:j+1] # (B,1)
            # Batch each unique expert
            for e_id in np.unique(ej_idx):
                mask  = ej_idx == e_id
                e_out = self.experts[e_id].forward(X[mask])   # (m, 10)
                out[mask] += wj[mask] * e_out
        return out   # raw weighted sum (not normalized to probs)

    def train_step(self, X, y, lr):
        """Simple alternating: train gate + each selected expert independently."""
        w, idx = self._gate(X)
        B      = X.shape[0]
        y_oh   = one_hot(y)

        # Train each expert on the samples routed to it (by top-1 route)
        top1   = idx[:, 0]
        total_loss = 0.0
        for e_id in range(self.n):
            mask = top1 == e_id
            if mask.sum() == 0:
                continue
            total_loss += self.experts[e_id].grad_step(X[mask], y_oh[mask], lr)

        # Train gate: minimize CE of weighted output
        probs = softmax(self.forward(X))    # (B,10)
        dL    = (probs - y_oh) / B          # (B,10)
        # Gate gradient via logits: simplified (treat gate as independent linear)
        gate_logits = X @ self.Wg + self.bg   # (B,N)
        # Surrogate: push top-1 expert outputs toward labels
        # dL_gate[b, top1[b]] = CE gradient sign
        dL_gate = np.zeros_like(gate_logits)
        for b in range(B):
            dL_gate[b, top1[b]] = (probs[b] - y_oh[b]).sum()
        dL_gate /= B
        self.Wg -= lr * (X.T @ dL_gate)
        self.bg -= lr * dL_gate.sum(axis=0)

        return total_loss / max(1, len(np.unique(top1)))

    def accuracy(self, X, y):
        probs = softmax(self.forward(X))
        return (probs.argmax(axis=1) == y).mean()

# ---------------------------------------------------------------------------
# Train & Eval
# ---------------------------------------------------------------------------
def train_and_eval(n_experts, k, X_tr, y_tr, X_te, y_te):
    rng   = np.random.RandomState(42)
    model = NumpyTopKMoE(n_experts, k, rng)
    n     = len(X_tr)
    for epoch in range(EPOCHS):
        perm = np.random.permutation(n)
        for start in range(0, n, BATCH_SIZE):
            bi  = perm[start:start + BATCH_SIZE]
            model.train_step(X_tr[bi], y_tr[bi], LR)
    acc = model.accuracy(X_te, y_te)
    return float(acc)

# ---------------------------------------------------------------------------
# Main sweep
# ---------------------------------------------------------------------------
def in_gz(r):
    return GZ_LOWER <= r <= GZ_UPPER

def main():
    print("=" * 60)
    print("MoE k/N Ratio Sweep — 1/e = {:.4f}".format(GZ_CENTER))
    print("GZ = [{:.4f}, {:.4f}]".format(GZ_LOWER, GZ_UPPER))
    print("Epochs={}, BatchSize={}, N_train={}".format(EPOCHS, BATCH_SIZE, N_TRAIN))
    print("=" * 60)

    print("\nLoading MNIST ...")
    X_tr_full, y_tr_full, X_te, y_te = load_mnist()
    X_tr = X_tr_full[:N_TRAIN]
    y_tr = y_tr_full[:N_TRAIN]
    print(f"  Train: {X_tr.shape}, Test: {X_te.shape}")

    expert_counts  = [8, 16]
    optimal_ratios = []

    for N in expert_counts:
        print(f"\n--- N = {N} experts ---")
        print(f"{'k':>4}  {'k/N':>7}  {'acc':>7}  {'in_GZ':>6}")
        print("-" * 32)

        best_acc   = -1.0
        best_ratio = None

        for k in range(1, N // 2 + 1):
            acc   = train_and_eval(N, k, X_tr, y_tr, X_te, y_te)
            ratio = k / N
            gz    = "YES" if in_gz(ratio) else "no"
            print(f"{k:>4}  {ratio:>7.4f}  {acc:>7.4f}  {gz:>6}")
            if acc > best_acc:
                best_acc   = acc
                best_ratio = ratio

        optimal_ratios.append(best_ratio)
        dist = abs(best_ratio - GZ_CENTER)
        print(f"  => Optimal k/N = {best_ratio:.4f}  dist to 1/e = {dist:.4f}  best_acc = {best_acc:.4f}")

    mean_ratio = float(np.mean(optimal_ratios))
    dist_mean  = abs(mean_ratio - GZ_CENTER)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for N, r in zip(expert_counts, optimal_ratios):
        flag = "IN GZ" if in_gz(r) else "outside GZ"
        print(f"  N={N:>2}: optimal k/N = {r:.4f}  [{flag}]")
    print(f"\n  Mean optimal k/N = {mean_ratio:.4f}")
    print(f"  1/e              = {GZ_CENTER:.4f}")
    print(f"  Distance         = {dist_mean:.4f}")

    if dist_mean < 0.05:
        grade = "STRONG (dist < 0.05)"
    elif dist_mean < 0.10:
        grade = "MODERATE (dist < 0.10)"
    else:
        grade = "WEAK (dist >= 0.10)"

    print(f"\n  Grade: {grade}")
    print("=" * 60)


if __name__ == "__main__":
    main()
