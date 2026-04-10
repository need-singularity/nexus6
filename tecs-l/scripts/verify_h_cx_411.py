#!/usr/bin/env python3
"""
H-CX-411: PH Bottleneck = Information Bottleneck
Test: Correlation between MI compression and H0 decrease during training
"""
import numpy as np
from sklearn.datasets import fetch_openml
from sklearn.preprocessing import OneHotEncoder
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# --- Minimal neural network ---
def softmax(x):
    e = np.exp(x - x.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)

def relu(x):
    return np.maximum(0, x)

class SimpleNN:
    def __init__(self, input_dim, hidden_dim, output_dim):
        self.W1 = np.random.randn(input_dim, hidden_dim) * np.sqrt(2.0 / input_dim)
        self.b1 = np.zeros(hidden_dim)
        self.W2 = np.random.randn(hidden_dim, output_dim) * np.sqrt(2.0 / hidden_dim)
        self.b2 = np.zeros(output_dim)

    def forward(self, X):
        self.X = X
        self.z1 = X @ self.W1 + self.b1
        self.a1 = relu(self.z1)
        self.z2 = self.a1 @ self.W2 + self.b2
        self.a2 = softmax(self.z2)
        return self.a2

    def train_step(self, X, Y, lr=0.01):
        m = X.shape[0]
        out = self.forward(X)
        dz2 = out - Y
        dW2 = self.a1.T @ dz2 / m
        db2 = dz2.mean(axis=0)
        da1 = dz2 @ self.W2.T
        dz1 = da1 * (self.z1 > 0).astype(float)
        dW1 = X.T @ dz1 / m
        db1 = dz1.mean(axis=0)
        self.W1 -= lr * dW1
        self.b1 -= lr * db1
        self.W2 -= lr * dW2
        self.b2 -= lr * db2
        loss = -np.mean(np.log(np.clip(out[Y.astype(bool)], 1e-10, 1)))
        return loss

    def accuracy(self, X, y):
        pred = self.forward(X).argmax(axis=1)
        return np.mean(pred == y)

    def get_hidden(self, X):
        z1 = X @ self.W1 + self.b1
        return relu(z1)

# --- Mutual Information estimation (binned) ---
def estimate_mi_binned(X, T, n_bins=20):
    """Estimate MI(X;T) using binning on hidden activations."""
    # Discretize T (hidden activations) into bins
    # Use PCA-like: project T to 1D for binning
    if T.shape[1] > 1:
        # Use variance-weighted sum
        t_var = T.var(axis=0) + 1e-10
        t_proj = (T * t_var).sum(axis=1)
    else:
        t_proj = T.ravel()

    # Discretize X: use first principal component or pixel sum
    x_proj = X.sum(axis=1)  # simple feature

    # Bin both
    x_bins = np.digitize(x_proj, np.linspace(x_proj.min(), x_proj.max(), n_bins + 1)[1:-1])
    t_bins = np.digitize(t_proj, np.linspace(t_proj.min(), t_proj.max(), n_bins + 1)[1:-1])

    # Joint and marginal distributions
    n = len(x_bins)
    joint = np.zeros((n_bins, n_bins))
    for i in range(n):
        joint[x_bins[i] % n_bins, t_bins[i] % n_bins] += 1
    joint /= joint.sum()

    px = joint.sum(axis=1)
    pt = joint.sum(axis=0)

    mi = 0
    for i in range(n_bins):
        for j in range(n_bins):
            if joint[i, j] > 1e-10 and px[i] > 1e-10 and pt[j] > 1e-10:
                mi += joint[i, j] * np.log(joint[i, j] / (px[i] * pt[j]))
    return mi

def estimate_mi_ty(T, Y, n_bins=20):
    """Estimate MI(T;Y) using binning."""
    if T.shape[1] > 1:
        t_var = T.var(axis=0) + 1e-10
        t_proj = (T * t_var).sum(axis=1)
    else:
        t_proj = T.ravel()

    t_bins = np.digitize(t_proj, np.linspace(t_proj.min(), t_proj.max(), n_bins + 1)[1:-1])
    n = len(t_bins)
    n_classes = int(Y.max()) + 1

    joint = np.zeros((n_bins, n_classes))
    for i in range(n):
        joint[t_bins[i] % n_bins, int(Y[i])] += 1
    joint /= joint.sum()

    pt = joint.sum(axis=1)
    py = joint.sum(axis=0)

    mi = 0
    for i in range(n_bins):
        for j in range(n_classes):
            if joint[i, j] > 1e-10 and pt[i] > 1e-10 and py[j] > 1e-10:
                mi += joint[i, j] * np.log(joint[i, j] / (pt[i] * py[j]))
    return mi

# --- PH computation ---
def compute_h0(weight_matrix, thresholds=None):
    W = weight_matrix
    n = min(W.shape[0], 64)
    W_sub = W[:n]
    dists = np.sqrt(((W_sub[:, None, :] - W_sub[None, :, :]) ** 2).sum(axis=2))

    if thresholds is None:
        flat = dists[np.triu_indices(n, k=1)]
        thresholds = np.linspace(np.percentile(flat, 5), np.percentile(flat, 95), 10)

    h0_counts = []
    for eps in thresholds:
        adj = dists < eps
        visited = np.zeros(n, dtype=bool)
        components = 0
        for i in range(n):
            if not visited[i]:
                components += 1
                stack = [i]
                while stack:
                    node = stack.pop()
                    if visited[node]:
                        continue
                    visited[node] = True
                    neighbors = np.where(adj[node] & ~visited)[0]
                    stack.extend(neighbors.tolist())
        h0_counts.append(components)
    return thresholds, np.array(h0_counts)

# --- Load data ---
print("Loading MNIST...")
mnist = fetch_openml('mnist_784', version=1, as_frame=False, parser='auto')
X_all, y_all = mnist.data / 255.0, mnist.target.astype(int)

n_train = 3000
n_test = 500
idx = np.random.permutation(len(X_all))
X_train, y_train = X_all[idx[:n_train]], y_all[idx[:n_train]]
X_test, y_test = X_all[idx[n_train:n_train+n_test]], y_all[idx[n_train:n_train+n_test]]

enc = OneHotEncoder(sparse_output=False, categories=[range(10)])
Y_train = enc.fit_transform(y_train.reshape(-1, 1))

# --- Train and measure ---
hidden = 64
nn = SimpleNN(784, hidden, 10)
fixed_thresholds = None  # will be set from first epoch
n_epochs = 10
batch_size = 128

# Sample for MI estimation
mi_sample_idx = np.random.choice(n_train, 500, replace=False)
X_mi = X_train[mi_sample_idx]
y_mi = y_train[mi_sample_idx]

results = []
print(f"\n{'Epoch':<8} {'Loss':<10} {'Acc':<8} {'MI(X;T)':<10} {'MI(T;Y)':<10} {'H0_mean':<10} {'H0_sum':<10}")
print("-" * 66)

for epoch in range(n_epochs):
    # Measure before training in epoch 0
    T_hidden = nn.get_hidden(X_mi)
    mi_xt = estimate_mi_binned(X_mi, T_hidden)
    mi_ty = estimate_mi_ty(T_hidden, y_mi)
    thresholds_out, h0 = compute_h0(nn.W1, fixed_thresholds)
    if fixed_thresholds is None:
        fixed_thresholds = thresholds_out  # fix for comparability
    acc = nn.accuracy(X_test, y_test)

    results.append({
        'epoch': epoch,
        'mi_xt': mi_xt,
        'mi_ty': mi_ty,
        'h0_mean': h0.mean(),
        'h0_sum': h0.sum(),
        'acc': acc,
        'h0': h0.copy(),
        'thresholds': thresholds_out,
    })

    # Train one epoch
    perm = np.random.permutation(n_train)
    total_loss = 0
    nb = 0
    for i in range(0, n_train, batch_size):
        bi = perm[i:i+batch_size]
        loss = nn.train_step(X_train[bi], Y_train[bi], lr=0.1)
        total_loss += loss
        nb += 1

    print(f"  {epoch:<6} {total_loss/nb:<10.4f} {acc:<8.4f} {mi_xt:<10.4f} {mi_ty:<10.4f} {h0.mean():<10.2f} {h0.sum():<10d}")

# Final measurement
T_hidden = nn.get_hidden(X_mi)
mi_xt = estimate_mi_binned(X_mi, T_hidden)
mi_ty = estimate_mi_ty(T_hidden, y_mi)
_, h0 = compute_h0(nn.W1, fixed_thresholds)
acc = nn.accuracy(X_test, y_test)
results.append({'epoch': n_epochs, 'mi_xt': mi_xt, 'mi_ty': mi_ty, 'h0_mean': h0.mean(), 'h0_sum': h0.sum(), 'acc': acc, 'h0': h0.copy(), 'thresholds': fixed_thresholds})
print(f"  {n_epochs:<6} {'--':<10} {acc:<8.4f} {mi_xt:<10.4f} {mi_ty:<10.4f} {h0.mean():<10.2f} {h0.sum():<10d}")

# --- Correlation Analysis ---
print("\n" + "=" * 60)
print("=== Correlation Analysis ===")
print("=" * 60)

mi_xt_vals = [r['mi_xt'] for r in results]
mi_ty_vals = [r['mi_ty'] for r in results]
h0_mean_vals = [r['h0_mean'] for r in results]
h0_sum_vals = [r['h0_sum'] for r in results]
acc_vals = [r['acc'] for r in results]

# Correlations
corr_xt_h0 = np.corrcoef(mi_xt_vals, h0_mean_vals)[0, 1]
corr_ty_h0 = np.corrcoef(mi_ty_vals, h0_mean_vals)[0, 1]
corr_xt_acc = np.corrcoef(mi_xt_vals, acc_vals)[0, 1]
corr_ty_acc = np.corrcoef(mi_ty_vals, acc_vals)[0, 1]
corr_h0_acc = np.corrcoef(h0_mean_vals, acc_vals)[0, 1]

# Delta correlations (epoch-to-epoch changes)
d_mi_xt = np.diff(mi_xt_vals)
d_mi_ty = np.diff(mi_ty_vals)
d_h0 = np.diff(h0_mean_vals)

corr_delta_xt_h0 = np.corrcoef(d_mi_xt, d_h0)[0, 1] if len(d_mi_xt) > 1 else 0
corr_delta_ty_h0 = np.corrcoef(d_mi_ty, d_h0)[0, 1] if len(d_mi_ty) > 1 else 0

print(f"\n  Pearson Correlations (level):")
print(f"    MI(X;T) vs H0_mean:  r = {corr_xt_h0:.4f}")
print(f"    MI(T;Y) vs H0_mean:  r = {corr_ty_h0:.4f}")
print(f"    MI(X;T) vs Accuracy: r = {corr_xt_acc:.4f}")
print(f"    MI(T;Y) vs Accuracy: r = {corr_ty_acc:.4f}")
print(f"    H0_mean vs Accuracy: r = {corr_h0_acc:.4f}")

print(f"\n  Pearson Correlations (delta, epoch-to-epoch changes):")
print(f"    dMI(X;T) vs dH0: r = {corr_delta_xt_h0:.4f}")
print(f"    dMI(T;Y) vs dH0: r = {corr_delta_ty_h0:.4f}")

# IB phases detection
print(f"\n--- Information Bottleneck Phase Detection ---")
# Phase 1: fitting (MI(T;Y) increases)
# Phase 2: compression (MI(X;T) decreases)
fitting_epochs = sum(1 for d in d_mi_ty if d > 0)
compress_epochs = sum(1 for d in d_mi_xt if d < 0)
print(f"  Fitting epochs (dMI(T;Y)>0):      {fitting_epochs}/{len(d_mi_ty)}")
print(f"  Compression epochs (dMI(X;T)<0):   {compress_epochs}/{len(d_mi_xt)}")

# H0 decrease epochs
h0_decrease_epochs = sum(1 for d in d_h0 if d < 0)
print(f"  H0 decrease epochs:                {h0_decrease_epochs}/{len(d_h0)}")

# Co-occurrence: compression AND h0 decrease
co_occur = sum(1 for i in range(len(d_mi_xt)) if d_mi_xt[i] < 0 and d_h0[i] < 0)
print(f"  Co-occurrence (compress + H0 drop): {co_occur}/{len(d_mi_xt)}")

# ASCII Graph: MI and H0 over epochs
print("\n--- ASCII Graph: MI(X;T), MI(T;Y), H0_mean over epochs ---")

# Normalize all to 0-1 for display
def normalize(vals):
    mn, mx = min(vals), max(vals)
    if mx - mn < 1e-10:
        return [0.5] * len(vals)
    return [(v - mn) / (mx - mn) for v in vals]

n_mi_xt = normalize(mi_xt_vals)
n_mi_ty = normalize(mi_ty_vals)
n_h0 = normalize(h0_mean_vals)

height = 10
print(f"  1.0 |")
for row in range(height, -1, -1):
    level = row / height
    line = f"  {level:.1f} |"
    for ep in range(len(results)):
        c = " "
        if abs(n_mi_xt[ep] - level) < 0.06:
            c = "X"
        if abs(n_mi_ty[ep] - level) < 0.06:
            c = "Y" if c == " " else "*"
        if abs(n_h0[ep] - level) < 0.06:
            c = "H" if c == " " else "#"
        line += f" {c} "
    print(line)
print(f"      +{'---' * len(results)}")
ep_labels = "".join(f" {r['epoch']:<2}" for r in results)
print(f"       {ep_labels}")
print(f"  X=MI(X;T)  Y=MI(T;Y)  H=H0_mean  *=X+Y overlap  #=overlap with H")

# H0 at different thresholds
print("\n--- H0 Barcode at Different Thresholds (epoch 0 vs final) ---")
print(f"  {'Threshold':<12}", end="")
for t in fixed_thresholds:
    print(f" {t:5.1f}", end="")
print()
print(f"  {'Epoch 0':<12}", end="")
for v in results[0]['h0']:
    print(f" {v:5d}", end="")
print()
print(f"  {'Final':<12}", end="")
for v in results[-1]['h0']:
    print(f" {v:5d}", end="")
print()
print(f"  {'Delta':<12}", end="")
for v0, vf in zip(results[0]['h0'], results[-1]['h0']):
    print(f" {vf-v0:+5d}", end="")
print()

print("\n=== DONE ===")
