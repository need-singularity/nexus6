"""
H-TOP-7 / H-GEO-7: Topological Lens/Telescope Verification
=============================================================
R(n) = sigma(n) * phi(n) / (n * tau(n))
Vietoris-Rips beta_0 via union-find, ε-sweep, focal length for perfect numbers.
"""

import numpy as np
from sympy import divisor_sigma, totient, divisor_count
import time

# ─────────────────────────────────────────
# 1. Compute R spectrum for n=1..5000
# ─────────────────────────────────────────
print("=" * 70)
print("H-TOP-7 / H-GEO-7: Topological Optics Verification")
print("=" * 70)
print()
print("## Step 1: Computing R(n) = sigma(n)*phi(n)/(n*tau(n)) for n=1..5000")
print()

N = 5000
t0 = time.time()
R_vals = []
n_vals = []
for n in range(1, N + 1):
    sig = divisor_sigma(n)
    phi = totient(n)
    tau = divisor_count(n)
    r = (sig * phi) / (n * tau)
    R_vals.append(float(r))
    n_vals.append(n)
    if n % 500 == 0:
        elapsed = time.time() - t0
        print(f"  n={n:5d} done  (elapsed {elapsed:.1f}s)")

R_vals = np.array(R_vals)
n_vals = np.array(n_vals)
t1 = time.time()
print(f"\n  Total compute time: {t1-t0:.1f}s")

# Summary stats
print()
print("### R(n) Summary Statistics")
print(f"  min R = {R_vals.min():.6f}  at n={n_vals[np.argmin(R_vals)]}")
print(f"  max R = {R_vals.max():.6f}  at n={n_vals[np.argmax(R_vals)]}")
print(f"  mean  = {R_vals.mean():.6f}")
print(f"  std   = {R_vals.std():.6f}")
print()

# Perfect numbers
perfect = [6, 28, 496]
print("### R at Perfect Numbers")
print()
print("| n   | sigma(n) | phi(n) | tau(n) | R(n)       |")
print("|-----|----------|--------|--------|------------|")
for p in perfect:
    if p <= N:
        r_p = R_vals[p - 1]
        sig = int(divisor_sigma(p))
        phi = int(totient(p))
        tau = int(divisor_count(p))
        print(f"| {p:3d} | {sig:8d} | {phi:6d} | {tau:6d} | {r_p:.8f} |")
print()
print("  Note: For perfect n, sigma(n)=2n, phi(n)=n-1 (if prime-like) → R(n)=2phi(n)/tau(n)")

# ─────────────────────────────────────────
# 2. Union-Find for Vietoris-Rips β₀
# ─────────────────────────────────────────
print()
print("=" * 70)
print("## Step 2: Vietoris-Rips β₀ via Union-Find (1D point cloud)")
print()

def make_union_find(n):
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
    return find, union

def beta0_1d(points, eps):
    """Count connected components for 1D point cloud with VR at epsilon."""
    n = len(points)
    if n == 0:
        return 0
    sorted_idx = np.argsort(points)
    sorted_pts = points[sorted_idx]
    # Map back: sorted_idx[i] is original index of sorted position i
    find, union = make_union_find(n)
    # In 1D, VR: connect i,j if |p_i - p_j| <= eps
    # Efficient: sorted, so only adjacent pairs matter for connectivity
    for i in range(n - 1):
        if sorted_pts[i + 1] - sorted_pts[i] <= eps:
            union(i, i + 1)
    # Count distinct roots
    roots = set(find(i) for i in range(n))
    return len(roots)

# ε sweep for full R spectrum
eps_values = np.linspace(0.001, 0.5, 100)
beta0_full = []
for eps in eps_values:
    b = beta0_1d(R_vals, eps)
    beta0_full.append(b)

beta0_full = np.array(beta0_full)

print("### β₀(ε) for full R spectrum (n=1..5000)")
print()
print("| ε       | β₀    |")
print("|---------|-------|")
# Print every 10th
for i in range(0, len(eps_values), 10):
    print(f"| {eps_values[i]:.4f}  | {beta0_full[i]:5d} |")
print()

# ASCII graph of β₀(ε)
print("### ASCII Graph: β₀(ε) vs ε")
print()
max_b = beta0_full.max()
min_b = beta0_full.min()
height = 20
width = 60
print(f"  β₀ range: [{min_b}, {max_b}]")
print()

# Normalize
b_norm = (beta0_full - min_b) / (max_b - min_b + 1e-12)
# Sample width points
idx_sample = np.linspace(0, len(eps_values) - 1, width).astype(int)
b_sample = b_norm[idx_sample]
eps_sample = eps_values[idx_sample]

graph = [[' '] * width for _ in range(height)]
for col, b in enumerate(b_sample):
    row = height - 1 - int(b * (height - 1))
    row = max(0, min(height - 1, row))
    graph[row][col] = '*'

print(f"  {max_b:5.0f} |", end="")
for col in range(width):
    print(graph[0][col], end="")
print("|")
for row in range(1, height - 1):
    if row == height // 2:
        mid_b = int(min_b + (max_b - min_b) / 2)
        print(f"  {mid_b:5.0f} |", end="")
    else:
        print(f"        |", end="")
    for col in range(width):
        print(graph[row][col], end="")
    print("|")
print(f"  {min_b:5.0f} |", end="")
for col in range(width):
    print(graph[height - 1][col], end="")
print("|")
print(f"        +{'-'*width}+")
print(f"        ε: {eps_values[0]:.3f}{' '*(width-12)}{eps_values[-1]:.3f}")
print()

# Transition points
print("### Transition Points (where β₀ drops significantly)")
print()
print("| ε_from  | ε_to    | β₀_from | β₀_to   | Δβ₀    |")
print("|---------|---------|---------|---------|--------|")
transitions = []
for i in range(1, len(beta0_full)):
    delta = beta0_full[i] - beta0_full[i - 1]
    if delta < -10:  # significant drop
        transitions.append((eps_values[i-1], eps_values[i], beta0_full[i-1], beta0_full[i], delta))
        print(f"| {eps_values[i-1]:.4f}  | {eps_values[i]:.4f}  | {beta0_full[i-1]:7.0f} | {beta0_full[i]:7.0f} | {delta:6.0f} |")

if not transitions:
    # Show all transitions
    for i in range(1, len(beta0_full)):
        delta = beta0_full[i] - beta0_full[i - 1]
        if delta != 0:
            transitions.append((eps_values[i-1], eps_values[i], beta0_full[i-1], beta0_full[i], delta))
    for t in transitions[:20]:
        print(f"| {t[0]:.4f}  | {t[1]:.4f}  | {t[2]:7.0f} | {t[3]:7.0f} | {t[4]:6.0f} |")

# ─────────────────────────────────────────
# 3. ε-sweep around perfect numbers (R near 1)
# ─────────────────────────────────────────
print()
print("=" * 70)
print("## Step 3: ε-sweep for local region R ∈ [0.5, 1.5]")
print()

mask_local = (R_vals >= 0.5) & (R_vals <= 1.5)
R_local = R_vals[mask_local]
n_local = n_vals[mask_local]
print(f"  Points in R ∈ [0.5, 1.5]: {len(R_local)}")
print(f"  n values (first 20): {n_local[:20].tolist()}")
print()

# Find gap structure around R=1
R_sorted_local = np.sort(R_local)
# Find nearest points to 1 from above and below
below_1 = R_sorted_local[R_sorted_local < 1.0]
above_1 = R_sorted_local[R_sorted_local > 1.0]
equal_1 = R_sorted_local[R_sorted_local == 1.0]

print(f"  Points with R < 1.0:  {len(below_1)}")
print(f"  Points with R = 1.0:  {len(equal_1)}")
print(f"  Points with R > 1.0:  {len(above_1)}")
print()
if len(below_1) > 0:
    delta_minus = 1.0 - below_1[-1]
    print(f"  δ⁻ = 1 - max(R<1) = 1 - {below_1[-1]:.8f} = {delta_minus:.8f}")
    print(f"    (nearest approach from below, n where max R<1 occurs)")
    # Find which n gives this
    idx_max_below = np.where(R_vals == below_1[-1])[0]
    if len(idx_max_below) > 0:
        print(f"    n = {n_vals[idx_max_below[0]]}")
if len(above_1) > 0:
    delta_plus = above_1[0] - 1.0
    print(f"  δ⁺ = min(R>1) - 1 = {above_1[0]:.8f} - 1 = {delta_plus:.8f}")
    idx_min_above = np.where(R_vals == above_1[0])[0]
    if len(idx_min_above) > 0:
        print(f"    n = {n_vals[idx_min_above[0]]}")
print()

# β₀(ε) for local region
eps_local = np.linspace(0.0001, 0.3, 200)
beta0_local = []
for eps in eps_local:
    b = beta0_1d(R_local, eps)
    beta0_local.append(b)
beta0_local = np.array(beta0_local)

print("### β₀(ε) for local region R ∈ [0.5, 1.5]")
print()
print("| ε       | β₀    |")
print("|---------|-------|")
for i in range(0, len(eps_local), 20):
    print(f"| {eps_local[i]:.5f} | {beta0_local[i]:5d} |")
print()

# Find ε where gap around R=1 closes
print("### Gap Closing ε")
print()
# The gap closes when the component containing R=1 merges with neighbors
# Approximate: find first ε where β₀ drops to near minimum for local region
b0_min_local = beta0_local[-1]  # at max eps
gap_close_idx = None
for i in range(len(beta0_local)):
    if beta0_local[i] <= b0_min_local * 1.1 + 1:
        gap_close_idx = i
        break

if gap_close_idx is not None:
    print(f"  β₀ stabilizes near minimum ({b0_min_local}) at ε ≈ {eps_local[gap_close_idx]:.5f}")

# More precise: look for the ε where R=1 cluster merges
# R=1 is only for n=perfect (or specific n); find ε where R=1 connects to neighbors
R1_indices = np.where(R_local == 1.0)[0]
print(f"\n  R=1 indices in local array: {R1_indices.tolist()}")
if len(R1_indices) > 0:
    print(f"  R=1 values: n = {n_local[R1_indices].tolist()}")

# Show transition table for local
print()
print("### Local Transition Points")
print()
print("| ε_from  | ε_to    | β₀_from | β₀_to   | Δβ₀    |")
print("|---------|---------|---------|---------|--------|")
local_transitions = []
for i in range(1, len(beta0_local)):
    delta = beta0_local[i] - beta0_local[i - 1]
    if delta < -2:
        local_transitions.append((eps_local[i-1], eps_local[i], beta0_local[i-1], beta0_local[i], delta))
        print(f"| {eps_local[i-1]:.5f} | {eps_local[i]:.5f} | {beta0_local[i-1]:7.0f} | {beta0_local[i]:7.0f} | {delta:6.0f} |")

if not local_transitions:
    for i in range(1, min(len(beta0_local), 50)):
        delta = beta0_local[i] - beta0_local[i-1]
        if delta != 0:
            print(f"| {eps_local[i-1]:.5f} | {eps_local[i]:.5f} | {beta0_local[i-1]:7.0f} | {beta0_local[i]:7.0f} | {delta:6.0f} |")

# ─────────────────────────────────────────
# 4. Focal length for perfect numbers
# ─────────────────────────────────────────
print()
print("=" * 70)
print("## Step 4: Focal Length f = δ⁺ · δ⁻ for Perfect Numbers")
print()
print("| P_k  | R(P_k)     | δ⁻ (below gap)  | δ⁺ (above gap)  | f = δ⁺·δ⁻       |")
print("|------|------------|-----------------|-----------------|-----------------|")

for p in perfect:
    if p > N:
        print(f"| {p:4d} | (n>{N}, skipped) | - | - | - |")
        continue
    r_p = R_vals[p - 1]
    # Find nearest R values to r_p from below and above (excluding r_p itself)
    R_below = R_vals[R_vals < r_p]
    R_above = R_vals[R_vals > r_p]
    if len(R_below) > 0:
        d_minus = r_p - R_below.max()
    else:
        d_minus = float('nan')
    if len(R_above) > 0:
        d_plus = R_above.min() - r_p
    else:
        d_plus = float('nan')
    f = d_minus * d_plus if not (np.isnan(d_minus) or np.isnan(d_plus)) else float('nan')
    print(f"| {p:4d} | {r_p:.8f} | {d_minus:.10f}  | {d_plus:.10f}  | {f:.12f}  |")

print()

# Also compute for all n<=5000, find which have smallest gap product (most "focal")
print("### Top 10 Most Focal Points (smallest f = δ⁺·δ⁻)")
print()
focal_data = []
R_sorted_all = np.sort(R_vals)
for i, (n, r) in enumerate(zip(n_vals, R_vals)):
    idx_sorted = np.searchsorted(R_sorted_all, r)
    if idx_sorted > 0 and idx_sorted < len(R_sorted_all) - 1:
        # Check if r appears multiple times
        r_below_candidates = R_sorted_all[:idx_sorted]
        r_above_candidates = R_sorted_all[idx_sorted+1:]
        # Exclude exact duplicates
        r_below_candidates = r_below_candidates[r_below_candidates < r]
        r_above_candidates = r_above_candidates[r_above_candidates > r]
        if len(r_below_candidates) > 0 and len(r_above_candidates) > 0:
            d_m = r - r_below_candidates[-1]
            d_p = r_above_candidates[0] - r
            f = d_m * d_p
            focal_data.append((n, r, d_m, d_p, f))

focal_data.sort(key=lambda x: x[4])
print("| n    | R(n)       | δ⁻           | δ⁺           | f=δ⁺·δ⁻        |")
print("|------|------------|--------------|--------------|----------------|")
for fd in focal_data[:10]:
    print(f"| {fd[0]:4d} | {fd[1]:.8f} | {fd[2]:.10f} | {fd[3]:.10f} | {fd[4]:.12f} |")

# ─────────────────────────────────────────
# 5. Barcode / Topological Transitions
# ─────────────────────────────────────────
print()
print("=" * 70)
print("## Step 5: Barcode — Birth/Death ε values for β₀ components")
print()

# For the full R spectrum, track when components merge
# Use sorted R values; in 1D VR, component merges happen at gap values
R_sorted = np.sort(R_vals)
gaps = np.diff(R_sorted)
gap_vals = sorted(np.unique(gaps), reverse=True)

print("### Top 20 Largest Gaps (birth ε for component merges)")
print()
print("| Rank | Gap (ε at merge) | R_left       | R_right      |")
print("|------|-----------------|--------------|--------------|")
for rank, g in enumerate(gap_vals[:20], 1):
    idx = np.where(gaps == g)[0][0]
    r_left = R_sorted[idx]
    r_right = R_sorted[idx + 1]
    print(f"| {rank:4d} | {g:.10f}    | {r_left:.8f} | {r_right:.8f} |")

print()

# Cumulative β₀ death sequence: as ε increases from 0, each gap closure kills one component
# Start: β₀ = N = 5000
# Each gap g_k closes at ε = g_k, merging 2 components into 1 (β₀ -= 1)
print("### β₀ Death Sequence (ε threshold for each merge)")
print()
print(f"  Initial β₀ = {len(R_vals)} (each point its own component)")
print(f"  Final β₀   = 1 (all connected)")
print()

# After sorting gaps descending, cumulative death:
gaps_sorted_desc = sorted(gaps, reverse=True)
# At what ε does β₀ reach specific values?
targets = [1000, 500, 100, 50, 10, 5, 2, 1]
current_b0 = len(R_vals)
target_idx = 0
print(f"| β₀ target | ε to reach it  |")
print(f"|-----------|----------------|")
eps_pointer = 0
cumsum = 0
for t_b0 in targets:
    # β₀ starts at N, each gap closure reduces by 1
    # To reach t_b0, need N - t_b0 merges
    # The (N - t_b0)-th largest gap determines the ε
    needed_merges = len(R_vals) - t_b0
    if needed_merges < len(gaps_sorted_desc):
        eps_reach = gaps_sorted_desc[needed_merges - 1]
        print(f"| {t_b0:9d} | {eps_reach:.10f}  |")
    else:
        print(f"| {t_b0:9d} | (beyond range)  |")

# Special: ε to merge R=1 with nearest neighbor
print()
print("### ε to connect R=1 (perfect number) to nearest neighbors")
print()
R1_full = R_vals[R_vals == 1.0]
if len(R1_full) > 0:
    R_below_1 = R_vals[R_vals < 1.0]
    R_above_1 = R_vals[R_vals > 1.0]
    if len(R_below_1) > 0:
        d_m = 1.0 - R_below_1.max()
        print(f"  eps to merge R=1 with nearest below: ε = {d_m:.10f}")
    if len(R_above_1) > 0:
        d_p = R_above_1.min() - 1.0
        print(f"  eps to merge R=1 with nearest above: ε = {d_p:.10f}")
    print()
    print(f"  The R=1 component 'gap width' = δ⁻ + δ⁺ = {d_m + d_p:.10f}")
    print(f"  Focal length f = δ⁻ * δ⁺ = {d_m * d_p:.12f}")

# R=1 specific: which n values achieve exactly R=1?
r1_ns = n_vals[R_vals == 1.0]
print()
print(f"  n values with R(n) = 1 exactly: {r1_ns.tolist()}")
print()
print("  Verify: sigma(n)*phi(n) = n*tau(n) iff n is perfect?")
for n in r1_ns[:10]:
    sig = int(divisor_sigma(n))
    phi_n = int(totient(n))
    tau_n = int(divisor_count(n))
    check = sig * phi_n == n * tau_n
    print(f"    n={n}: sigma*phi={sig*phi_n}, n*tau={n*tau_n}, equal={check}, perfect={sig==2*n}")

# ASCII barcode visualization
print()
print("=" * 70)
print("## ASCII Barcode (persistence diagram sketch)")
print()
print("  Each row = one topological feature (component)")
print("  Born at ε=0, dies at ε = gap to neighbor")
print()
print("  Top 10 most persistent features (largest gaps = longest bars):")
print()
top_gaps = sorted(enumerate(gaps), key=lambda x: -x[1])[:10]
bar_width = 50
eps_max_bar = gaps_sorted_desc[0] * 1.1
print(f"  ε range: [0, {eps_max_bar:.6f}]")
print()
for rank, (idx, g) in enumerate(top_gaps, 1):
    bar_len = int((g / eps_max_bar) * bar_width)
    r_left = R_sorted[idx]
    r_right = R_sorted[idx + 1]
    bar = '#' * bar_len + '.' * (bar_width - bar_len)
    print(f"  {rank:2d} |{bar}| gap={g:.6f} [{r_left:.4f},{r_right:.4f}]")

print()
print("=" * 70)
print("## Summary")
print()

# Find where the R=1 rank is in the gap list
R_sorted_unique = np.sort(np.unique(R_vals))
gaps_unique = np.diff(R_sorted_unique)
gap_at_R1_below = None
gap_at_R1_above = None
for i in range(len(R_sorted_unique) - 1):
    if abs(R_sorted_unique[i] - 1.0) < 1e-9:
        gap_at_R1_above = R_sorted_unique[i+1] - R_sorted_unique[i]
    if abs(R_sorted_unique[i+1] - 1.0) < 1e-9:
        gap_at_R1_below = R_sorted_unique[i+1] - R_sorted_unique[i]

# Rank of gaps
all_gaps_desc = sorted(gaps_unique, reverse=True)
rank_below = None
rank_above = None
if gap_at_R1_below is not None:
    rank_below = all_gaps_desc.index(gap_at_R1_below) + 1 if gap_at_R1_below in all_gaps_desc else None
if gap_at_R1_above is not None:
    rank_above = all_gaps_desc.index(gap_at_R1_above) + 1 if gap_at_R1_above in all_gaps_desc else None

print(f"  R(n)=1 occurs at n = {r1_ns.tolist()}")
if gap_at_R1_below:
    print(f"  Gap below R=1: δ⁻ = {gap_at_R1_below:.10f}  (rank #{rank_below} of {len(all_gaps_desc)} gaps)")
if gap_at_R1_above:
    print(f"  Gap above R=1: δ⁺ = {gap_at_R1_above:.10f}  (rank #{rank_above} of {len(all_gaps_desc)} gaps)")
if gap_at_R1_below and gap_at_R1_above:
    f_val = gap_at_R1_below * gap_at_R1_above
    print(f"  Focal length f = δ⁻ * δ⁺ = {f_val:.12f}")
    print()
    print("  Interpretation:")
    print(f"    - R=1 is topologically 'isolated' with gap product f = {f_val:.6e}")
    print(f"    - This quantifies the 'focus' of the lens at R=1 (perfect numbers)")
    print(f"    - Comparison: if R=1 were a random point, expected gap ~ (range/N)^2")
    expected_random = ((R_vals.max() - R_vals.min()) / N) ** 2
    print(f"    - Expected random f ~ {expected_random:.6e}")
    ratio = f_val / expected_random if expected_random > 0 else float('nan')
    print(f"    - Observed/Expected ratio = {ratio:.2f}x")

print()
print("Script complete.")
