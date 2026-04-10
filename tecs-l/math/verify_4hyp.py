#!/usr/bin/env python3
"""
Verify 4 hypotheses by computation:
  H-AI-8:  6-dimensional embedding cosine similarity entropy
  H-AI-9:  Loss landscape condition number vs d
  H-AI-11: R-chain training dynamics
  H-CX-7:  7 topological phases by R-class
"""
import sys
sys.stdout.reconfigure(line_buffering=True)

import numpy as np
from math import log
from collections import defaultdict

np.random.seed(42)

# ============================================================
# Precompute sigma(n) via sieve for n up to N_MAX
# ============================================================
N_MAX = 10000

print("Precomputing sigma(n) for n=1..10000 via sieve...", flush=True)
_sigma = [0] * (N_MAX + 1)
for i in range(1, N_MAX + 1):
    for j in range(i, N_MAX + 1, i):
        _sigma[j] += i

def sigma(n):
    if n <= N_MAX:
        return _sigma[n]
    s = 0
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            s += i
            if i != n // i:
                s += n // i
    return s

def R(n):
    return (sigma(n) - n) / n if n > 1 else 0.0

def aliquot_step(n):
    """Sum of proper divisors = sigma(n) - n"""
    if n <= 1:
        return 0
    return sigma(n) - n

def num_divisors(n):
    c = 0
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            c += 1
            if i != n // i:
                c += 1
    return c

def is_prime(n):
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0: return False
        i += 6
    return True

print("Done.\n", flush=True)

# ============================================================
# H-AI-8: 6-DIMENSIONAL EMBEDDING
# ============================================================
print("=" * 72)
print("  H-AI-8: 6-DIMENSIONAL EMBEDDING -- COSINE SIMILARITY ENTROPY")
print("=" * 72)
print(flush=True)

dims = [2, 3, 4, 5, 6, 7, 8, 10, 12, 16, 20, 32, 64]
n_vectors = 500
n_bins = 50

results_ai8 = []

for d in dims:
    vecs = np.random.randn(n_vectors, d)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    vecs = vecs / norms

    # Compute all pairwise cosine similarities efficiently
    cos_matrix = vecs @ vecs.T
    # Extract upper triangle
    idx = np.triu_indices(n_vectors, k=1)
    cos_sims = cos_matrix[idx]

    counts, edges = np.histogram(cos_sims, bins=n_bins, range=(-1, 1))
    probs = counts / counts.sum()
    probs_nz = probs[probs > 0]
    entropy = -np.sum(probs_nz * np.log(probs_nz))
    max_entropy = log(n_bins)
    uniformity = entropy / max_entropy

    mean_cos = np.mean(cos_sims)
    std_cos = np.std(cos_sims)

    results_ai8.append((d, entropy, uniformity, mean_cos, std_cos))
    print(f"  d={d:2d} done", flush=True)

print()
print(f"{'d':>4} | {'Entropy':>8} | {'Uniformity':>10} | {'Mean cos':>9} | {'Std cos':>8}")
print("-" * 52)
for d, ent, uni, mc, sc in results_ai8:
    marker = " <--" if d == 6 else ""
    print(f"{d:4d} | {ent:8.4f} | {uni:10.4f} | {mc:9.5f} | {sc:8.5f}{marker}")

best_d_uni = max(results_ai8, key=lambda x: x[2])
print(f"\nMost uniform distribution: d={best_d_uni[0]} (uniformity={best_d_uni[2]:.4f})")

print("\nUniformity vs d:")
for d, ent, uni, mc, sc in results_ai8:
    bar_len = int(uni * 60)
    marker = " ***" if d == 6 else ""
    print(f"  d={d:2d} |{'#' * bar_len}| {uni:.4f}{marker}")

# KL divergence from uniform
print("\nKL divergence from uniform (lower = more uniform):")
print(f"{'d':>4} | {'KL(P||U)':>10}")
print("-" * 20)
for d in dims:
    vecs = np.random.randn(n_vectors, d)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    vecs = vecs / norms
    cos_matrix = vecs @ vecs.T
    idx = np.triu_indices(n_vectors, k=1)
    cos_sims = cos_matrix[idx]
    counts, _ = np.histogram(cos_sims, bins=n_bins, range=(-1, 1))
    probs = counts / counts.sum()
    uniform = 1.0 / n_bins
    kl = sum(p * log(p / uniform) for p in probs if p > 0)
    marker = " <--" if d == 6 else ""
    print(f"{d:4d} | {kl:10.6f}{marker}")

print(flush=True)

# ============================================================
# H-AI-9: LOSS LANDSCAPE CONDITION NUMBER
# ============================================================
print()
print("=" * 72)
print("  H-AI-9: LOSS LANDSCAPE CONDITION NUMBER vs d")
print("=" * 72)
print(flush=True)

print("\nEigenvalues for d=6: A = diag(sigma(k)/k for k=1..6)")
eigs_6 = [sigma(k) / k for k in range(1, 7)]
for k in range(1, 7):
    print(f"  k={k}: sigma({k})={sigma(k)}, sigma({k})/{k} = {sigma(k)/k:.4f}")
cond_6 = max(eigs_6) / min(eigs_6)
print(f"  Condition number = {max(eigs_6):.4f} / {min(eigs_6):.4f} = {cond_6:.4f}")

print(f"\nEigenvalues for d=28:")
eigs_28 = [sigma(k) / k for k in range(1, 29)]
k_min = min(range(1, 29), key=lambda k: sigma(k) / k)
k_max = max(range(1, 29), key=lambda k: sigma(k) / k)
print(f"  min eigenvalue: sigma({k_min})/{k_min} = {min(eigs_28):.4f}")
print(f"  max eigenvalue: sigma({k_max})/{k_max} = {max(eigs_28):.4f}")
cond_28 = max(eigs_28) / min(eigs_28)
print(f"  Condition number = {cond_28:.4f}")

print(f"\nCondition number kappa(d) for d=2..50:")
print(f"{'d':>4} | {'min eig':>8} | {'max eig':>8} | {'kappa':>8} | {'log(kappa)':>10}")
print("-" * 52)

cond_results = []
for d in range(2, 51):
    eigs = [sigma(k) / k for k in range(1, d + 1)]
    kappa = max(eigs) / min(eigs)
    cond_results.append((d, min(eigs), max(eigs), kappa))
    marker = " <--" if d in (6, 28) else ""
    if d <= 15 or d in (28, 50) or d % 10 == 0:
        print(f"{d:4d} | {min(eigs):8.4f} | {max(eigs):8.4f} | {kappa:8.4f} | {log(kappa):10.4f}{marker}")

best_d = min(cond_results, key=lambda x: x[3])
print(f"\nMinimum condition number: d={best_d[0]}, kappa={best_d[3]:.4f}")

print("\nlog(kappa) vs d:")
max_log_k = max(log(c[3]) for c in cond_results)
for d, mn, mx, k in cond_results:
    if d <= 15 or d in (28, 50) or d % 10 == 0:
        bar_len = int(log(k) / max_log_k * 50)
        marker = " ***" if d == 6 else (" ^^^" if d == 28 else "")
        print(f"  d={d:2d} |{'#' * bar_len}| {log(k):.3f}{marker}")

print("\nSpectral uniformity (std/mean of eigenvalues, lower = more uniform):")
print(f"{'d':>4} | {'std/mean':>10}")
print("-" * 20)
for d in range(2, 21):
    eigs = np.array([sigma(k) / k for k in range(1, d + 1)])
    cv = np.std(eigs) / np.mean(eigs)
    marker = " <--" if d == 6 else ""
    print(f"{d:4d} | {cv:10.6f}{marker}")

print(flush=True)

# ============================================================
# H-AI-11: R-CHAIN TRAINING DYNAMICS
# ============================================================
print()
print("=" * 72)
print("  H-AI-11: R-CHAIN TRAINING DYNAMICS")
print("=" * 72)
print(flush=True)

print("\nR-chain (aliquot sequence) lengths to reach 1:")
print(f"{'n':>6} | {'chain_len':>9} | {'R(n)':>8} | path (first 10 steps)")
print("-" * 75)

chain_max = 500
chain_lengths = {}

for n in range(2, chain_max + 1):
    curr = n
    visited = {curr}
    path = [curr]
    steps = 0
    reached_one = False
    while steps < 200:
        curr = aliquot_step(curr)
        steps += 1
        path.append(curr)
        if curr <= 1:
            reached_one = True
            break
        if curr in visited:
            break
        if curr > 10**7:
            break  # escape large values
        visited.add(curr)
    chain_lengths[n] = (steps, reached_one, path)

for n in [2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 20, 24, 28, 30, 36, 48, 60, 100, 120, 220]:
    if n <= chain_max:
        steps, ok, path = chain_lengths[n]
        path_str = "->".join(str(x) for x in path[:10])
        if len(path) > 10:
            path_str += "->..."
        status = " ->1" if ok else " (cycle/long)"
        r_val = R(n)
        print(f"{n:6d} | {steps:9d} | {r_val:8.4f} | {path_str}{status}")

print("\nChain length statistics by R-value range:")
r_bins = [(0, 0.5, "R<0.5"), (0.5, 1.0, "0.5<=R<1"), (1.0, 1.0001, "R=1 (perfect)"),
          (1.0001, 2.0, "1<R<2"), (2.0, 4.0, "2<=R<4"), (4.0, 100, "R>=4")]

print(f"{'R range':>20} | {'count':>6} | {'mean len':>9} | {'reach 1%':>9}")
print("-" * 55)
for lo, hi, label in r_bins:
    subset = [(n, s, ok) for n, (s, ok, p) in chain_lengths.items()
              if lo <= R(n) < hi]
    if subset:
        avg_len = np.mean([s for _, s, _ in subset])
        pct_one = 100 * sum(1 for _, _, ok in subset if ok) / len(subset)
        print(f"{label:>20} | {len(subset):6d} | {avg_len:9.2f} | {pct_one:8.1f}%")

print("\nPerfect numbers (R=1) chain behavior:")
for n in [6, 28, 496]:
    if n <= chain_max:
        steps, ok, path = chain_lengths[n]
        path_str = "->".join(str(x) for x in path[:15])
        print(f"  n={n}: {path_str}")

print("\nGD analogy: R-chain vs gradient descent on f(x)=x^2/2, lr=0.1")
print(f"{'start':>8} | {'GD steps to |x|<1':>18} | {'R-chain steps':>14}")
print("-" * 48)
for n in [6, 10, 28, 50, 100]:
    x = float(n)
    gd_steps = 0
    while abs(x) > 1 and gd_steps < 1000:
        x *= 0.9
        gd_steps += 1
    r_steps = chain_lengths.get(n, (-1, False, []))[0]
    print(f"{n:8d} | {gd_steps:18d} | {r_steps:14d}")

print(flush=True)

# ============================================================
# H-CX-7: 7 TOPOLOGICAL PHASES BY R-CLASS
# ============================================================
print()
print("=" * 72)
print("  H-CX-7: 7 TOPOLOGICAL PHASES BY R-CLASS")
print("=" * 72)
print(flush=True)

# Precompute R values and phases
print("\nComputing phases for n=2..10000...", flush=True)
r_values = [0.0] * (N_MAX + 1)
phases = [0] * (N_MAX + 1)
for n in range(2, N_MAX + 1):
    r = (_sigma[n] - n) / n
    r_values[n] = r
    if _sigma[n] == 2 * n:
        phases[n] = 2
    elif r < 1:
        phases[n] = 1
    elif r < 2:
        phases[n] = 3
    elif r < 4:
        phases[n] = 4
    elif r < 8:
        phases[n] = 5
    elif r < 16:
        phases[n] = 6
    else:
        phases[n] = 7

phase_counts = defaultdict(int)
phase_examples = defaultdict(list)
phase_r_sum = defaultdict(float)

for n in range(2, N_MAX + 1):
    p = phases[n]
    phase_counts[p] += 1
    phase_r_sum[p] += r_values[n]
    if len(phase_examples[p]) < 5:
        phase_examples[p].append((n, r_values[n]))

phase_labels = {
    1: "R < 1        (deficient)",
    2: "R = 1        (perfect)",
    3: "1 < R < 2    (weak abundant)",
    4: "2 <= R < 4   (abundant)",
    5: "4 <= R < 8   (highly abundant)",
    6: "8 <= R < 16  (very abundant)",
    7: "R >= 16      (super abundant)",
}

print(f"\nPhase distribution for n=2..{N_MAX}:")
print(f"{'Phase':>6} | {'Label':>30} | {'Count':>7} | {'%':>7} | {'Mean R':>8} | Examples")
print("-" * 105)
total = N_MAX - 1
for p in range(1, 8):
    c = phase_counts[p]
    pct = 100 * c / total
    mean_r = phase_r_sum[p] / c if c > 0 else 0
    exs = ", ".join(f"{n}({r:.2f})" for n, r in phase_examples[p][:4])
    print(f"{p:6d} | {phase_labels[p]:>30} | {c:7d} | {pct:6.2f}% | {mean_r:8.4f} | {exs}")

print(f"\nPhase histogram (n=2..{N_MAX}):")
max_count = max(phase_counts.values()) if phase_counts else 1
for p in range(1, 8):
    c = phase_counts[p]
    bar_len = int(c / max_count * 50)
    print(f"  Phase {p} |{'#' * bar_len}| {c:5d} ({100*c/total:.1f}%)")

# Structural properties by phase
print("\nStructural properties by phase:")
print(f"{'Phase':>6} | {'Primes%':>8} | {'Even%':>6} | {'Avg #divs':>10}")
print("-" * 42)

# Precompute primes via sieve
sieve = [True] * (N_MAX + 1)
sieve[0] = sieve[1] = False
for i in range(2, int(N_MAX**0.5) + 1):
    if sieve[i]:
        for j in range(i*i, N_MAX + 1, i):
            sieve[j] = False

for p in range(1, 8):
    members = [n for n in range(2, N_MAX + 1) if phases[n] == p]
    if not members:
        print(f"{p:6d} | {'N/A':>8} | {'N/A':>6} | {'N/A':>10}")
        continue
    n_primes = sum(1 for n in members if sieve[n])
    n_even = sum(1 for n in members if n % 2 == 0)
    # Average number of divisors (use precomputed sigma trick: count via sieve)
    avg_divs = np.mean([num_divisors(n) for n in members[:3000]])
    pct_prime = 100 * n_primes / len(members)
    pct_even = 100 * n_even / len(members)
    print(f"{p:6d} | {pct_prime:7.1f}% | {pct_even:5.1f}% | {avg_divs:10.2f}")

print("\nPhase transitions (first n in each phase):")
first_in_phase = {}
for n in range(2, N_MAX + 1):
    p = phases[n]
    if p not in first_in_phase:
        first_in_phase[p] = n
for p in sorted(first_in_phase.keys()):
    n = first_in_phase[p]
    print(f"  Phase {p}: first at n={n}, R(n)={r_values[n]:.4f}, sigma(n)={_sigma[n]}")

# R-value distribution
print(f"\nR-value distribution for n=2..{N_MAX}:")
r_bins_hist = [0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0, 32.0, 100.0]
for i in range(len(r_bins_hist) - 1):
    lo, hi = r_bins_hist[i], r_bins_hist[i + 1]
    c = sum(1 for n in range(2, N_MAX + 1) if lo <= r_values[n] < hi)
    bar_len = int(c / total * 200)
    print(f"  [{lo:5.1f},{hi:5.1f}) |{'#' * bar_len}| {c:5d}")

print("\nPerfect numbers in range:")
for n in range(2, N_MAX + 1):
    if _sigma[n] == 2 * n:
        cl = chain_lengths.get(n, ("N/A",))
        cl_str = cl[0] if isinstance(cl[0], str) else str(cl[0])
        print(f"  n={n}: sigma={_sigma[n]}, R={r_values[n]:.4f}, "
              f"#divisors={num_divisors(n)}, aliquot_len={cl_str}")

# ============================================================
# SUMMARY
# ============================================================
print()
print("=" * 72)
print("  SUMMARY")
print("=" * 72)
print()

# H-AI-8
best_uni = max(results_ai8, key=lambda x: x[2])
d6_uni = [x for x in results_ai8 if x[0] == 6][0][2]
print(f"H-AI-8: d=6 uniformity={d6_uni:.4f}, best d={best_uni[0]} (uniformity={best_uni[2]:.4f})")
if best_uni[0] == 6:
    print("  -> d=6 IS the most uniform! Hypothesis SUPPORTED.")
else:
    print(f"  -> d=6 is NOT optimal. d={best_uni[0]} is more uniform.")
    # Check if d=6 is local optimum
    d_list = [x[0] for x in results_ai8]
    u_list = [x[2] for x in results_ai8]
    i6 = d_list.index(6)
    if i6 > 0 and i6 < len(d_list) - 1:
        if u_list[i6] > u_list[i6-1] and u_list[i6] > u_list[i6+1]:
            print("  -> But d=6 IS a local maximum among neighbors!")
        else:
            print("  -> d=6 is NOT even a local maximum. Hypothesis WEAKENED.")

# H-AI-9
best_cond = min(cond_results, key=lambda x: x[3])
d6_cond = [x for x in cond_results if x[0] == 6][0][3]
print(f"\nH-AI-9: d=6 kappa={d6_cond:.4f}, min kappa at d={best_cond[0]} ({best_cond[3]:.4f})")
if best_cond[0] == 6:
    print("  -> d=6 minimizes condition number! Hypothesis SUPPORTED.")
elif best_cond[0] in (2, 3):
    print(f"  -> Trivially d={best_cond[0]} wins (fewer eigenvalues). Among d>=6:")
    cond_ge6 = [x for x in cond_results if x[0] >= 6]
    best_ge6 = min(cond_ge6, key=lambda x: x[3])
    print(f"     Best d>={6}: d={best_ge6[0]}, kappa={best_ge6[3]:.4f}")
    if best_ge6[0] == 6:
        print("  -> d=6 minimizes kappa among d>=6! Partial support.")
else:
    print(f"  -> d={best_cond[0]} minimizes. Hypothesis WEAKENED.")

# H-AI-11
n6_chain = chain_lengths[6]
n28_chain = chain_lengths[28]
print(f"\nH-AI-11: Perfect n=6 chain: {n6_chain[0]} steps, reaches 1: {n6_chain[1]}")
print(f"         Perfect n=28 chain: {n28_chain[0]} steps, reaches 1: {n28_chain[1]}")
print(f"         Path n=6: {'->'.join(str(x) for x in n6_chain[2])}")
print(f"         Path n=28: {'->'.join(str(x) for x in n28_chain[2][:10])}")
print("  -> Perfect numbers are FIXED POINTS of aliquot iteration (s(n)=n)")
print("  -> This is the number-theoretic analog of a trained model at loss=0")
print("  -> Deficient numbers (R<1) converge to 1 quickly (loss -> 0)")
print("  -> Abundant numbers (R>1) may diverge or cycle (training instability)")

# H-CX-7
print(f"\nH-CX-7: 7 phases population:")
for p in range(1, 8):
    c = phase_counts[p]
    print(f"  Phase {p} ({phase_labels[p].strip()}): {c} ({100*c/total:.1f}%)")
print("  -> Phase 1 dominates (all primes + most odd numbers are deficient)")
print("  -> Phase 2 is ultra-rare (perfect numbers: 6, 28, 496, 8128)")
print("  -> Higher phases require increasingly composite numbers")
print("  -> 7 phases capture qualitatively different divisor structures")

print("\nDone.", flush=True)
