#!/usr/bin/env python3
"""
H-CX-412: PH Persistence = Generalization Lifespan
Test: Correlation between persistence diagram statistics and test accuracy
      across 5 network variants
"""
import numpy as np
from sklearn.datasets import fetch_openml
from sklearn.preprocessing import OneHotEncoder
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

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
        self.hidden_dim = hidden_dim

    def forward(self, X):
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

# --- Persistence Diagram computation ---
def compute_persistence_diagram(weight_matrix, max_points=80):
    """Compute approximate persistence diagram from weight matrix.
    Returns list of (birth, death) pairs for H0 features."""
    W = weight_matrix
    n = min(W.shape[0], max_points)
    W_sub = W[:n]

    # Pairwise distances
    dists = np.sqrt(((W_sub[:, None, :] - W_sub[None, :, :]) ** 2).sum(axis=2))

    # Single-linkage clustering to get H0 persistence
    # Track when components merge (birth=0, death=merge distance)
    parent = list(range(n))
    rank = [0] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx == ry:
            return False
        if rank[rx] < rank[ry]:
            rx, ry = ry, rx
        parent[ry] = rx
        if rank[rx] == rank[ry]:
            rank[rx] += 1
        return True

    # Sort edges by distance
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            edges.append((dists[i, j], i, j))
    edges.sort()

    # Build persistence diagram
    persistence = []
    for dist, i, j in edges:
        if union(i, j):
            persistence.append((0.0, dist))  # birth=0, death=merge distance

    return persistence

def persistence_stats(diagram):
    """Compute statistics from persistence diagram."""
    if not diagram:
        return {'mean_pers': 0, 'max_pers': 0, 'std_pers': 0,
                'total_pers': 0, 'n_features': 0, 'entropy': 0}

    lifetimes = [d - b for b, d in diagram]
    lifetimes = np.array(lifetimes)

    total = lifetimes.sum()
    probs = lifetimes / (total + 1e-10)
    entropy = -np.sum(probs * np.log(probs + 1e-10))

    return {
        'mean_pers': np.mean(lifetimes),
        'max_pers': np.max(lifetimes),
        'std_pers': np.std(lifetimes),
        'total_pers': total,
        'n_features': len(lifetimes),
        'entropy': entropy,
        'median_pers': np.median(lifetimes),
        'q90_pers': np.percentile(lifetimes, 90),
    }

# --- Load data ---
print("Loading MNIST...")
mnist = fetch_openml('mnist_784', version=1, as_frame=False, parser='auto')
X_all, y_all = mnist.data / 255.0, mnist.target.astype(int)

n_train = 3000
n_test = 1000
idx = np.random.permutation(len(X_all))
X_train, y_train = X_all[idx[:n_train]], y_all[idx[:n_train]]
X_test, y_test = X_all[idx[n_train:n_train+n_test]], y_all[idx[n_train:n_train+n_test]]

enc = OneHotEncoder(sparse_output=False, categories=[range(10)])
Y_train = enc.fit_transform(y_train.reshape(-1, 1))

# --- 5 Network Variants ---
variants = [
    {'name': 'Tiny-16',    'hidden': 16,  'lr': 0.05, 'epochs': 8},
    {'name': 'Small-32',   'hidden': 32,  'lr': 0.1,  'epochs': 8},
    {'name': 'Medium-64',  'hidden': 64,  'lr': 0.1,  'epochs': 8},
    {'name': 'Large-128',  'hidden': 128, 'lr': 0.1,  'epochs': 8},
    {'name': 'Wide-256',   'hidden': 256, 'lr': 0.05, 'epochs': 8},
]

batch_size = 128
all_results = []

for vi, var in enumerate(variants):
    print(f"\n=== Variant {vi+1}: {var['name']} (hidden={var['hidden']}, lr={var['lr']}) ===")
    nn = SimpleNN(784, var['hidden'], 10)

    for epoch in range(var['epochs']):
        perm = np.random.permutation(n_train)
        total_loss = 0
        nb = 0
        for i in range(0, n_train, batch_size):
            bi = perm[i:i+batch_size]
            loss = nn.train_step(X_train[bi], Y_train[bi], lr=var['lr'])
            total_loss += loss
            nb += 1

        if epoch % 2 == 1 or epoch == var['epochs'] - 1:
            train_acc = nn.accuracy(X_train, y_train)
            test_acc = nn.accuracy(X_test, y_test)
            print(f"  Epoch {epoch+1}: loss={total_loss/nb:.4f}, train={train_acc:.4f}, test={test_acc:.4f}")

    # Final metrics
    train_acc = nn.accuracy(X_train, y_train)
    test_acc = nn.accuracy(X_test, y_test)
    gen_gap = train_acc - test_acc

    # Persistence diagram
    pd_w1 = compute_persistence_diagram(nn.W1)
    pd_w2 = compute_persistence_diagram(nn.W2)

    stats_w1 = persistence_stats(pd_w1)
    stats_w2 = persistence_stats(pd_w2)

    result = {
        'name': var['name'],
        'hidden': var['hidden'],
        'train_acc': train_acc,
        'test_acc': test_acc,
        'gen_gap': gen_gap,
        'w1_mean_pers': stats_w1['mean_pers'],
        'w1_max_pers': stats_w1['max_pers'],
        'w1_std_pers': stats_w1['std_pers'],
        'w1_entropy': stats_w1['entropy'],
        'w1_total_pers': stats_w1['total_pers'],
        'w1_median_pers': stats_w1['median_pers'],
        'w1_q90_pers': stats_w1['q90_pers'],
        'w2_mean_pers': stats_w2['mean_pers'],
        'w2_max_pers': stats_w2['max_pers'],
        'w2_entropy': stats_w2['entropy'],
    }
    all_results.append(result)
    print(f"  W1 PH: mean_pers={stats_w1['mean_pers']:.4f}, max={stats_w1['max_pers']:.4f}, entropy={stats_w1['entropy']:.4f}")
    print(f"  W2 PH: mean_pers={stats_w2['mean_pers']:.4f}, max={stats_w2['max_pers']:.4f}, entropy={stats_w2['entropy']:.4f}")

# --- Analysis ---
print("\n" + "=" * 80)
print("=== Comprehensive Results Table ===")
print("=" * 80)

header = f"{'Variant':<12} {'Hidden':<8} {'TrainAcc':<10} {'TestAcc':<10} {'GenGap':<10} {'W1_MeanP':<10} {'W1_MaxP':<10} {'W1_Entropy':<12}"
print(header)
print("-" * len(header))
for r in all_results:
    print(f"{r['name']:<12} {r['hidden']:<8} {r['train_acc']:<10.4f} {r['test_acc']:<10.4f} {r['gen_gap']:<10.4f} {r['w1_mean_pers']:<10.4f} {r['w1_max_pers']:<10.4f} {r['w1_entropy']:<12.4f}")

# Correlations
test_accs = [r['test_acc'] for r in all_results]
gen_gaps = [r['gen_gap'] for r in all_results]
mean_pers = [r['w1_mean_pers'] for r in all_results]
max_pers = [r['w1_max_pers'] for r in all_results]
entropies = [r['w1_entropy'] for r in all_results]
median_pers = [r['w1_median_pers'] for r in all_results]
q90_pers = [r['w1_q90_pers'] for r in all_results]

print("\n=== Correlation Analysis ===")
print(f"\n  {'Metric':<25} {'vs TestAcc':<15} {'vs GenGap':<15}")
print(f"  {'-'*55}")

metrics = {
    'W1 Mean Persistence': mean_pers,
    'W1 Max Persistence': max_pers,
    'W1 PH Entropy': entropies,
    'W1 Median Persistence': median_pers,
    'W1 90th Percentile': q90_pers,
}

for name, vals in metrics.items():
    r_acc = np.corrcoef(vals, test_accs)[0, 1]
    r_gap = np.corrcoef(vals, gen_gaps)[0, 1]
    print(f"  {name:<25} r={r_acc:+.4f}      r={r_gap:+.4f}")

# Death/Birth ratio analysis
print("\n=== Death/Birth Ratio Analysis ===")
for r in all_results:
    if r['w1_mean_pers'] > 0:
        ratio = r['w1_max_pers'] / r['w1_mean_pers']
    else:
        ratio = 0
    print(f"  {r['name']:<12}: max/mean = {ratio:.4f}, test_acc = {r['test_acc']:.4f}")

# ASCII Graph: Test Accuracy vs Mean Persistence
print("\n--- ASCII Scatter: Test Accuracy vs W1 Mean Persistence ---")
# Normalize to grid
height = 10
width = 40

min_p, max_p = min(mean_pers), max(mean_pers)
min_a, max_a = min(test_accs), max(test_accs)

grid = [[' ' for _ in range(width + 1)] for _ in range(height + 1)]

for i, r in enumerate(all_results):
    x = int((r['w1_mean_pers'] - min_p) / (max_p - min_p + 1e-10) * width)
    y = int((r['test_acc'] - min_a) / (max_a - min_a + 1e-10) * height)
    x = min(x, width)
    y = min(y, height)
    grid[y][x] = str(i + 1)

for row in range(height, -1, -1):
    acc_val = min_a + (max_a - min_a) * row / height
    line = f"  {acc_val:.3f} |"
    line += ''.join(grid[row])
    print(line)
print(f"         +{'─' * (width + 1)}")
print(f"          {min_p:.3f}" + " " * (width - 10) + f"{max_p:.3f}")
print(f"          W1 Mean Persistence →")
for i, r in enumerate(all_results):
    print(f"  {i+1} = {r['name']}")

# ASCII Graph: Persistence Distribution for each variant
print("\n--- Persistence Distribution (W1) by Variant ---")
print(f"  {'Variant':<12} | Distribution (normalized)")
print(f"  {'-'*60}")

for r in all_results:
    bar_len = int(r['w1_mean_pers'] * 20 / (max(mean_pers) + 1e-10))
    bar = '#' * bar_len + '.' * (20 - bar_len)
    q90_mark = int(r['w1_q90_pers'] * 20 / (max(q90_pers) + 1e-10))
    line = list(bar)
    if q90_mark < 20:
        line[q90_mark] = '|'
    print(f"  {r['name']:<12} | {''.join(line)} mean={r['w1_mean_pers']:.3f} acc={r['test_acc']:.3f}")

# Rank correlation (Spearman)
def spearman_r(x, y):
    n = len(x)
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    d = rx - ry
    return 1 - 6 * np.sum(d ** 2) / (n * (n ** 2 - 1))

print("\n=== Spearman Rank Correlations ===")
sp_mean = spearman_r(mean_pers, test_accs)
sp_max = spearman_r(max_pers, test_accs)
sp_ent = spearman_r(entropies, test_accs)
sp_q90 = spearman_r(q90_pers, test_accs)

print(f"  W1 Mean Persistence vs TestAcc: rho = {sp_mean:+.4f}")
print(f"  W1 Max Persistence vs TestAcc:  rho = {sp_max:+.4f}")
print(f"  W1 PH Entropy vs TestAcc:       rho = {sp_ent:+.4f}")
print(f"  W1 90th Pctl vs TestAcc:        rho = {sp_q90:+.4f}")

# Key finding
print("\n=== KEY FINDINGS ===")
best_corr_name = max(metrics.keys(), key=lambda k: abs(np.corrcoef(metrics[k], test_accs)[0, 1]))
best_corr_val = np.corrcoef(metrics[best_corr_name], test_accs)[0, 1]
print(f"  Strongest correlate with test accuracy: {best_corr_name} (r={best_corr_val:+.4f})")

gap_corr_name = max(metrics.keys(), key=lambda k: abs(np.corrcoef(metrics[k], gen_gaps)[0, 1]))
gap_corr_val = np.corrcoef(metrics[gap_corr_name], gen_gaps)[0, 1]
print(f"  Strongest correlate with gen gap:       {gap_corr_name} (r={gap_corr_val:+.4f})")

print("\n=== DONE ===")
