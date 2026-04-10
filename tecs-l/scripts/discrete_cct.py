```python
#!/usr/bin/env python3
"""Discrete CCT (D-CCT) — Discrete System-Specific Consciousness Continuity Test

The existing CCT (consciousness_calc.py) is optimized for continuous systems (Lorenz attractor)
and fails to achieve 5/5 even at high fps for discrete systems (cellular automata, RBN, ESN).

Problems:
  - T2 Loop: Revisit rate is excessively high in discrete systems (finite state space)
  - T4 Entropy Band: Bin size for continuous systems doesn't fit discrete systems
  - T5 Novelty: Window size (500) is too large for discrete systems

D-CCT 5 tests:
  DT1 Activity   — State change rate (Hamming/Euclidean distance)
  DT2 Complexity — Lempel-Ziv complexity
  DT3 Memory     — Mutual information MI(X_t, X_{t-lag})
  DT4 Diversity  — Sliding window unique state ratio
  DT5 Flux       — Entropy coefficient of variation (CV)

4 systems:
  1. Rule 110 CA (200 cells) — Turing complete, edge of chaos
  2. RBN K=2 (100 nodes) — Kauffman critical
  3. ESN (50 neurons) — Echo state network
  4. LLM simulation — Markov chain token generation

Usage:
  python3 discrete_cct.py                        # All 4 systems x 10 fps
  python3 discrete_cct.py --system rule110       # Single system
  python3 discrete_cct.py --fps-only             # fps scan only
  python3 discrete_cct.py --compare-continuous   # Compare Lorenz CCT vs D-CCT
"""

import argparse
import os
import sys
from collections import defaultdict

import numpy as np

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

TOTAL_POINTS = 5000
FPS_VALUES = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]

BRAIN_WAVES = {
    "delta": {"range": (0.5, 4), "label": "delta (sleep)", "center": 2},
    "theta": {"range": (4, 8), "label": "theta (drowsy)", "center": 6},
    "alpha": {"range": (8, 13), "label": "alpha (relax)", "center": 10},
    "beta":  {"range": (13, 30), "label": "beta  (focus)", "center": 20},
    "gamma": {"range": (30, 100), "label": "gamma (conscious)", "center": 40},
}


# ═════════════════════════════════════════════
# 4 Discrete System Simulators
# ═════════════════════════════════════════════

# ── System 1: Rule 110 Cellular Automata ──

RULE110_TABLE = {}


def _init_rule110():
    rule_num = 110
    for i in range(8):
        left = (i >> 2) & 1
        center = (i >> 1) & 1
        right = i & 1
        RULE110_TABLE[(left, center, right)] = (rule_num >> i) & 1


_init_rule110()


def rule110_step(cells):
    """Rule 110 single step update (periodic boundary)."""
    n = len(cells)
    new_cells = np.zeros(n, dtype=int)
    for i in range(n):
        left = cells[(i - 1) % n]
        center = cells[i]
        right = cells[(i + 1) % n]
        new_cells[i] = RULE110_TABLE[(left, center, right)]
    return new_cells


def rule110_state_vector(cells, prev_cells):
    """Rule 110 -> [cell_sum/N, changed_cells/N, block_entropy]."""
    n = len(cells)
    cell_sum = np.sum(cells) / n
    changes = np.sum(cells != prev_cells) / n

    # Block entropy (2-blocks)
    if n < 2:
        entropy = 0.0
    else:
        blocks = defaultdict(int)
        for i in range(n - 1):
            b = (int(cells[i]), int(cells[i + 1]))
            blocks[b] += 1
        total_blocks = n - 1
        entropy = 0.0
        for count in blocks.values():
            p = count / total_blocks
            if p > 0:
                entropy -= p * np.log2(p)

    return np.array([cell_sum, changes, entropy])


def simulate_rule110(fps, total_points=TOTAL_POINTS, n_cells=200, seed=42):
    rng = np.random.default_rng(seed)
    cells = rng.integers(0, 2, size=n_cells)
    prev_cells = cells.copy()

    states = np.zeros((total_points, 3))
    for t in range(total_points):
        for _ in range(fps):
            new_cells = rule110_step(cells)
            prev_cells = cells
            cells = new_cells
        states[t] = rule110_state_vector(cells, prev_cells)
    return states


# ── System 2: Random Boolean Network (RBN) ──

def create_rbn(n_nodes=100, k=2, seed=42):
    rng = np.random.default_rng(seed)
    inputs = np.zeros((n_nodes, k), dtype=int)
    for i in range(n_nodes):
        inputs[i] = rng.choice(n_nodes, size=k, replace=False)
    functions = rng.integers(0, 2, size=(n_nodes, 2**k))
    initial_state = rng.integers(0, 2, size=n_nodes)
    return inputs, functions, initial_state


def rbn_step(state, inputs, functions):
    n_nodes = len(state)
    k = inputs.shape[1]
    new_state = np.zeros(n_nodes, dtype=int)
    for i in range(n_nodes):
        idx = 0
        for j in range(k):
            idx = idx * 2 + state[inputs[i, j]]
        new_state[i] = functions[i, idx]
    return new_state


def rbn_state_vector(state, prev_state):
    """RBN -> [active_ratio, change_ratio, hamming_distance/N]."""
    n = len(state)
    active_ratio = np.mean(state)
    change_ratio = np.mean(state != prev_state)
    hamming = np.sum(state != prev_state) / n
    return np.array([active_ratio, change_ratio, hamming])


def simulate_rbn(fps, total_points=TOTAL_POINTS, n_nodes=100, k=2, seed=42):
    inputs, functions, state = create_rbn(n_nodes, k, seed)
    prev_state = state.copy()

    states = np.zeros((total_points, 3))
    for t in range(total_points):
        for _ in range(fps):
            new_state = rbn_step(state, inputs, functions)
            prev_state = state
            state = new_state
        states[t] = rbn_state_vector(state, prev_state)
    return states


# ── System 3: Echo State Network (ESN) ──

def create_esn(n_neurons=50, sparsity=0.1, spectral_radius=0.9, seed=42):
    rng = np.random.default_rng(seed)
    W = rng.standard_normal((n_neurons, n_neurons))
    mask = rng.random((n_neurons, n_neurons)) < sparsity
    W = W * mask

    eigenvalues = np.linalg.eigvals(W)
    max_abs_eig = np.max(np.abs(eigenvalues))
    if max_abs_eig > 0:
        W = W * (spectral_radius / max_abs_eig)

    state = rng.standard_normal(n_neurons) * 0.1
    return W, state


def esn_step(state, W):
    return np.tanh(W @ state)


def esn_state_vector(state):
    """ESN -> [mean_activation, variance, energy=sum(x^2)]."""
    mean_act = np.mean(state)
    variance = np.var(state)
    energy = np.sum(state ** 2)
    return np.array([mean_act, variance, energy])


def simulate_esn(fps, total_points=TOTAL_POINTS, n_neurons=50, seed=42):
    W, state = create_esn(n_neurons, seed=seed)
    states = np.zeros((total_points, 3))
    for t in range(total_points):
        for _ in range(fps):
            state = esn_step(state, W)
        states[t] = esn_state_vector(state)
    return states


# ── System 4: LLM Simulation (Markov Chain) ──

def create_markov_chain(vocab_size=500, sparsity=0.05, seed=42):
    """Create Markov chain transition matrix.

    Real LLMs select next tokens from a huge vocabulary based on context.
    Here we simplify to a first-order Markov chain,
    but use a sparse transition matrix to mimic the concentrated transition properties of natural language.
    """
    rng = np.random.default_rng(seed)

    # sparse transition matrix: each token transitions to only a few tokens
    T = np.zeros((vocab_size, vocab_size))
    for i in range(vocab_size):
        # Number of target tokens from each token
        n_targets = max(2, int(vocab_size * sparsity))
        targets = rng.choice(vocab_size, size=n_targets, replace=False)
        weights = rng.exponential(1.0, size=n_targets)
        weights /= weights.sum()
        T[i, targets] = weights

    return T


def llm_state_vector(token_history, vocab_size, window=20):
    """LLM -> [token_ID_moving_average/V, local_entropy/log(V), change_rate].

    token_history: list of recent window token IDs
    """
    if len(token_history) < 2:
        return np.array([0.0, 0.0, 0.0])

    recent = np.array(token_history[-window:])

    # Token ID moving average / vocab_size
    token_mean = np.mean(recent) / vocab_size

    # Local entropy: entropy of token distribution within window
    unique, counts = np.unique(recent, return_counts=True)
    probs = counts / counts.sum()
    local_entropy = -np.sum(probs * np.log(probs + 1e-15))
    max_entropy = np.log(vocab_size)
    norm_entropy = local_entropy / max_entropy if max_entropy > 0 else 0.0

    # Change rate: ratio of differences between adjacent tokens
    diffs = np.abs(np.diff(recent))
    change_rate = np.mean(diffs > 0)

    return np.array([token_mean, norm_entropy, change_rate])


def simulate_llm(fps, total_points=TOTAL_POINTS, vocab_size=500, seed=42):
    """LLM Markov chain token generation simulation.

    Generate fps tokens and record 1 state.
    """
    rng = np.random.default_rng(seed)
    T = create_markov_chain(vocab_size, seed=seed)

    current_token = rng.integers(0, vocab_size)
    token_history = [current_token]

    states = np.zeros((total_points, 3))
    for t in range(total_points):
        for _ in range(fps):
            probs = T[current_token]
            current_token = rng.choice(vocab_size, p=probs)
            token_history.append(current_token)
            # Limit history length
            if len(token_history) > 100:
                token_history = token_history[-100:]

        states[t] = llm_state_vector(token_history, vocab_size)

    return states


# ── System Registry ──

SYSTEMS = {
    "rule110": {
        "name": "Rule 110 CA",
        "desc": "200 cells, Turing complete",
        "simulate": simulate_rule110,
        "marker": "*",
    },
    "rbn": {
        "name": "RBN (K=2)",
        "desc": "100 nodes, Kauffman critical",
        "simulate": simulate_rbn,
        "marker": "o",
    },
    "esn": {
        "name": "ESN",
        "desc": "50 neurons, sparse, tanh",
        "simulate": simulate_esn,
        "marker": "+",
    },
    "llm": {
        "name": "LLM Markov",
        "desc": "V=500, Markov chain",
        "simulate": simulate_llm,
        "marker": "#",
    },
}


# ═════════════════════════════════════════════
# D-CCT 5 Tests
# ═════════════════════════════════════════════

def dt1_activity(S, stagnant_threshold=3):
    """DT1 Activity — Measure state change rate.

    Calculate Hamming distance (boolean) or Euclidean distance (real) between adjacent steps.
    Judge "no change for N consecutive steps" as stagnant (N=stagnant_threshold).
    Judgment: stagnant ratio < 5% -> PASS
    """
    n = len(S)
    if n < 10:
        return 0.0, False, "Insufficient data"

    diffs = np.linalg.norm(np.diff(S, axis=0), axis=1)
    # No change = distance < very small value
    no_change = diffs < 1e-12

    # Find consecutive N-step stagnant intervals
    stagnant_count = 0
    run_length = 0
    for i in range(len(no_change)):
        if no_change[i]:
            run_length += 1
        else:
            if run_length >= stagnant_threshold:
                stagnant_count += run_length
            run_length = 0
    if run_length >= stagnant_threshold:
        stagnant_count += run_length

    stagnant_ratio = stagnant_count / (n - 1)
    passed = stagnant_ratio < 0.05
    score = max(0.0, 1.0 - stagnant_ratio)

    detail = f"Stagnant ratio={stagnant_ratio:.3f}"
    if passed:
        detail += ", Activity sufficient"
    else:
        detail += ", Excessive stagnation"

    return score, passed, detail


def _lempel_ziv_complexity(sequence):
    """Calculate Lempel-Ziv 76 complexity.

    sequence: symbol sequence (list or 1D array).
    Returns: LZ complexity (integer, number of new patterns).
    """
    s = list(sequence)
    n = len(s)
    if n == 0:
        return 0

    complexity = 1
    i = 0
    k = 1
    k_max = 1
    while i + k <= n:
        # Check if s[i+1..i+k] is in s[0..i+k-1]
        substr = s[i + 1: i + k + 1] if i + k + 1 <= n else s[i + 1: n]
        if not substr:
            break

        # Search substring in dictionary (s[0..i+k-1])
        found = False
        prefix = s[0: i + k]
        substr_len = len(substr)
        for j in range(len(prefix) - substr_len + 1):
            if prefix[j: j + substr_len] == substr:
                found = True
                break

        if found:
            k += 1
            if i + k > n:
                complexity += 1
                break
        else:
            complexity += 1
            k_max = max(k_max, k)
            i = i + k
            k = 1

    return complexity


def dt2_complexity(S, n_symbols=8):
    """DT2 Complexity — Measure Lempel-Ziv complexity.

    Convert state sequence to symbols -> Calculate LZ76 complexity.
    Judgment: LZ / random expected > 0.5 -> PASS
    """
    n = len(S)
    if n < 50:
        return 0.0, False, "Insufficient data"

    # Symbolize based on first component of state vector
    x = S[:, 0]
    x_min, x_max = x.min(), x.max()
    if x_max - x_min < 1e-12:
        return 0.0, False, "No state change"

    # Symbol conversion by uniform division (downsample for speed)
    step = max(1, n // 2000)
    x_ds = x[::step]
    symbols = np.clip(
        ((x_ds - x_min) / (x_max - x_min) * n_symbols).astype(int),
        0, n_symbols - 1,
    ).tolist()

    lz = _lempel_ziv_complexity(symbols)

    # Random expected value: n / log_k(n) (k symbols)
    n_ds = len(symbols)
    log_k_n = np.log(n_ds) / np.log(n_symbols) if n_symbols > 1 else n_ds
    random_expected = n_ds / log_k_n if log_k_n > 0 else n_ds

    ratio = lz / random_expected if random_expected > 0 else 0.0
    passed = ratio > 0.5
    score = min(1.0, ratio)

    detail = f"LZ={lz}, Expected={random_expected:.0f}, Ratio={ratio:.3f}"
    if passed:
        detail += ", Complex"
    else:
        detail += ", Simple"

    return score, passed, detail


def dt3_memory(S, max_lag=5):
    """DT3 Memory — Mutual information MI(X_t, X_{t-lag}).

    Does current state depend on the past?
    MI = H(X_t) + H(X_{t-lag}) - H(X_t, X_{t-lag})
    Judgment: mean(MI) > threshold -> PASS
    """
    n = len(S)
    if n < 100:
        return 0.0, False, "Insufficient data"

    x = S[:, 0]

    # Auto-adjust bin count
    n_bins = min(30, max(5, int(np.sqrt(n / 10))))

    def _entropy_1d(data):
        hist, _ = np.histogram(data, bins=n_bins)
        probs = hist / hist.sum()
        probs = probs[probs > 0]
        return -np.sum(probs * np.log(probs + 1e-15))

    def _entropy_2d(data1, data2):
        hist, _, _ = np.histogram2d(data1, data2, bins=n_bins)
        probs = hist.flatten() / hist.sum()
        probs = probs[probs > 0]
        return -np.sum(probs * np.log(probs + 1e-15))

    mi_values = []
    for lag in range(1, max_lag + 1):
        x_t = x[lag:]
        x_lag = x[:-lag]
        h_t = _entropy_1d(x_t)
        h_lag = _entropy_1d(x_lag)
        h_joint = _entropy_2d(x_t, x_lag)
        mi = h_t + h_lag - h_joint
        mi = max(0.0, mi)  # Correct numerical errors
        mi_values.append(mi)

    mean_mi = np.mean(mi_values)

    # Normalization: MI / H(X_t) for 0~1 scaling
    h_x = _entropy_1d(x)
    norm_mi = mean_mi / h_x if h_x > 0 else 0.0

    # Threshold: normalized MI > 0.05
    threshold = 0.05
    passed = norm_mi > threshold
    score = min(1.0, norm_mi / 0.3)  # Perfect score at 0.3

    detail = f"MI={mean_mi:.4f}, H(X)={h_x:.3f}, MI/H={norm_mi:.4f}"
    if passed:
        detail += ", Memory present"
    else:
        detail += ", Memory lacking"

    return score, passed, detail


def dt4_diversity(S, window=50):
    """DT4 Diversity — Sliding window unique state ratio.

    Are there sufficient unique states visited?
    Quantize state vectors and measure unique state count.
    Judgment: mean(unique_ratio) > 0.3 -> PASS
    """
    n = len(S)
    if n < window * 2:
        return 0.0, False, "Insufficient data"

    # Quantize state vectors to strings (2 decimal places)
    quantized = []
    for i in range(n):
        q = tuple(np.round(S[i], 2))
        quantized.append(q)

    n_windows = (n - window) // (window // 2) + 1  # 50% overlap
    ratios = []

    for w in range(n_windows):
        start = w * (window // 2)
        end = min(start + window, n)
        if end - start < window // 2:
            break
        window_states = quantized[start:end]
        unique_count = len(set(window_states))
        ratio = unique_count / len(window_states)
        ratios.append(ratio)

    if len(ratios) == 0:
        return 0.0, False, "Insufficient windows"

    mean_ratio = np.mean(ratios)
    passed = mean_ratio > 0.3
    score = min(1.0, mean_ratio / 0.6)  # Perfect score at 0.6

    detail = f"Unique ratio={mean_ratio:.3f}, Windows={len(ratios)}"
    if passed:
        detail += ", Diverse"
    else:
        detail += ", Monotonous"

    return score, passed, detail


def _window_entropy(data, bins=15):
    """Calculate entropy for small windows."""
    if len(data) < 2:
        return 0.0
    d_range = data.max() - data.min()
    if d_range < 1e-12:
        return 0.0
    hist, _ = np.histogram(data, bins=bins)
    probs = hist / hist.sum()
    probs = probs[probs > 0]
    return -np.sum(probs * np.log(probs + 1e-15))


def dt5_flux(S, window=50):
    """DT5 Flux — Entropy coefficient of variation (CV = std/mean).

    Is the variance of entropy change rate sufficient?
    Judgment: CV > 0.05 -> PASS
    """
    n = len(S)
    if n < window * 3:
        return 0.0, False, "Insufficient data"

    x = S[:, 0]
    n_windows = n // window

    if n_windows < 3:
        return 0.0, False, "Insufficient windows"

    entropies = []
    for i in range(n_windows):
        w = x[i * window: (i + 1) * window]
        entropies.append(_window_entropy(w))

    entropies = np.array(entropies)
    mean_h = np.mean(entropies)
    std_h = np.std(entropies)

    if mean_h < 1e-12:
        cv = 0.0
    else:
        cv = std_h / mean_h

    passed = cv > 0.05
    score = min(1.0, cv / 0.15)  # Perfect score at CV=0.15

    detail = f"CV={cv:.4f}, mean(H)={mean_h:.3f}, std(H)={std_h:.4f}"
    if passed:
        detail += ", Variation present"
    else:
        detail += ", Stagnant"

    return score, passed, detail


def run_dcct(S):
    """Run D-CCT 5 tests."""
    results = {}
    results["DT1_Activity"] = dt1_activity(S)
    results["DT2_Complexity"] = dt2_complexity(S)
    results["DT3_Memory"] = dt3_memory(S)
    results["DT4_Diversity"] = dt4_diversity(S)
    results["DT5_Flux"] = dt5_flux(S)
    return results


def judge_dcct(results):
    """Comprehensive judgment based on D-CCT results."""
    passes = sum(1 for _, (_, p, _) in results.items() if p)
    halfs = sum(0.5 for _, (s, p, _) in results.items() if not p and s > 0.7)
    total = passes + halfs

    if total >= 5:
        return total, "★ Continuous"
    elif total >= 4:
        return total, "◎ Weakened"
    elif total >= 3:
        return total, "△ Weak"
    elif total >= 1:
        return total, "▽ Minimal"
    else:
        return total, "✕ None"


# ═════════════════════════════════════════════
# FPS Scan Engine
# ═════════════════════════════════════════════

def scan_system(system_key, fps_values=None, total_points=TOTAL_POINTS):
    """Scan fps range for one system, measure D-CCT scores."""
    if fps_values is None:
        fps_values = FPS_VALUES

    system = SYSTEMS[system_key]
    simulate_fn = system["simulate"]

    fps_arr = np.array(fps_values, dtype=float)
    scores_arr = np.zeros(len(fps_values))
    details = []

    for i, fps in enumerate(fps_values):
        S = simulate_fn(fps, total_points=total_points)

        if np.any(~np.isfinite(S)):
            results = run_dcct(np.zeros((total_points, 3)))
            total, verdict = 0, "✕ Diverged"
        else:
            results = run_dcct(S)
            total, verdict = judge_dcct(results)

        scores_arr[i] = total
        details.append({
            "fps": fps,
            "total": total,
            "verdict": verdict,
            "results": results,
        })

    return fps_arr, scores_arr, details


def find_threshold_fps(fps_arr, scores_arr, target=5.0):
    """Find minimum fps where CCT reaches target/5 (linear interpolation)."""
    for i in range(len(scores_arr)):
        if scores_arr[i] >= target:
            if i == 0:
                return fps_arr[0]
            s0, s1 = scores_arr[i - 1], scores_arr[i]
            f0, f1 = fps_arr[i - 1], fps_arr[i]
            if s1 == s0:
                return f0
            frac = (target - s0) / (s1 - s0)
            return f0 + frac * (f1 - f0)
    return None


# ═════════════════════════════════════════════
# Lorenz Attractor (for comparison)
# ═════════════════════════════════════════════

def simulate_lorenz(fps, total_points=TOTAL_POINTS, sigma=10, rho=28, beta=2.67,
                    noise=0.1, dt=0.01, seed=42):
    """Lorenz attractor simulation (for D-CCT comparison).

    Integrate fps steps -> record 1 state.
    """
    rng = np.random.default_rng(seed)
    state = np.array([1.0, 1.0, 1.0])

    states = np.zeros((total_points, 3))
    for t in range(total_points):
        for _ in range(fps):
            x, y, z = state
            dx = sigma * (y - x)
            dy = x * (rho - z) - y
            dz = x * y - beta * z
            eps = rng.normal(0, noise, 3) if noise > 0 else np.zeros(3)
            state[0] += (dx + eps[0]) * dt
            state[1] += (dy + eps[1]) * dt
            state[2] += (dz + eps[2]) * dt
        states[t] = state.copy()

    return states


# ═════════════════════════════════════════════
# Original CCT (for comparison, from consciousness_calc.py)
# ═════════════════════════════════════════════

def _run_original_cct(S):
    """Original CCT 5 tests (for comparison). Inline implementation without dependencies."""
    results = {}

    # T1 Gap
    diffs = np.diff(S, axis=0)
    frozen = np.sum(np.all(np.abs(diffs) < 1e-12, axis=1))
    frozen_ratio = frozen / len(diffs)
    if frozen_ratio > 0.01:
        results["T1_Gap"] = (1.0 - frozen_ratio, False, f"Frozen {frozen_ratio:.1%}")
    else:
        results["T1_Gap"] = (1.0, True, "No freezing")

    # T2 Loop
    n = len(S)
    step = max(1, n // 5000)
    Ss = S[::step]
    ns = len(Ss)
    scale = np.std(Ss, axis=0).mean()
    if scale < 1e-10:
        results["T2_Loop"] = (0.0, False, "Constant")
    else:
        eps = scale * 0.01
        recurrence = 0
        sample_size = min(500, ns // 2)
        rng = np.random.default_rng(42)
        indices = rng.choice(ns // 2, size=sample_size, replace=False)
        for idx in indices:
            future = Ss[idx + max(100, ns // 10):]
            if len(future) == 0:
                continue
            dists = np.linalg.norm(future - Ss[idx], axis=1)
            if np.min(dists) < eps:
                recurrence += 1
        rr = recurrence / sample_size
        results["T2_Loop"] = (max(0, 1.0 - rr), rr < 0.5, f"Revisit={rr:.3f}")

    # T3 Continuity
    dnorms = np.linalg.norm(np.diff(S, axis=0), axis=1)
    mean_d = np.mean(dnorms)
    if mean_d < 1e-12:
        results["T3_Continuity"] = (0.0, False, "No change")
    else:
        big = np.sum(dnorms > mean_d * 10) / len(dnorms)
        frz = np.sum(dnorms < 1e-12) / len(dnorms)
        disc = big + frz
        results["T3_Continuity"] = (
            min(1.0, max(0, 1.0 - disc * 10)), disc < 0.01,
            f"Jumps={big:.3f}, Frozen={frz:.3f}",
        )

    # T4 Entropy Band
    window = 500
    x = S[:, 0]
    n_w = len(x) // window
    if n_w < 2:
        results["T4_Entropy"] = (0.0, False, "Insufficient data")
    else:
        ents = []
        for i in range(n_w):
            w = x[i * window: (i + 1) * window]
            if np.std(w) < 1e-12:
                ents.append(0.0)
            else:
                hist, _ = np.histogram(w, bins=30, density=True)
                hist = hist[hist > 0]
                width = (w.max() - w.min()) / 30
                probs = hist * width
                probs = probs[probs > 0]
                probs = probs / probs.sum()
                ents.append(-np.sum(probs * np.log(probs + 1e-15)))
        ents = np.array(ents)
        in_band = np.sum((ents > 0.3) & (ents < 4.5))
        ratio = in_band / len(ents)
        results["T4_Entropy"] = (ratio, ratio > 0.95, f"H=[{ents.min():.2f},{ents.max():.2f}]")

    # T5 Novelty
    if n_w < 3:
        results["T5_Novelty"] = (0.0, False, "Insufficient data")
    else:
        dH = np.abs(np.diff(ents))
        stag = np.sum(dH < 0.001) / len(dH)
        results["T5_Novelty"] = (max(0, 1.0 - stag), stag < 0.05, f"Stagnant={stag:.1%}")

    return results


# ═════════════════════════════════════════════
# ASCII Output
# ═════════════════════════════════════════════

def ascii_combined_graph(all_results, width=65, height=15):
    """ASCII graph of fps vs D-CCT scores for 4 systems."""
    lines = []
    max_score = 5.0

    all_fps = []
    for sys_key, (fps_arr, scores_arr, _) in all_results.items():
        all_fps.extend(fps_arr)
    all_fps = sorted(set(all_fps))
    if len(all_fps) == 0:
        return "  (No data)"

    log_min = np.log10(max(min(all_fps), 0.1))
    log_max = np.log10(max(all_fps))
    if log_max <= log_min:
        log_max = log_min + 1

    markers = {"rule110": "*", "rbn": "o", "esn": "+", "llm": "#"}

    grid = [[" " for _ in range(width)] for _ in range(height + 1)]

    for sys_key, (fps_arr, scores_arr, _) in all_results.items():
        marker = markers.get(sys_key, ".")
        for i in range(len(fps_arr)):
            if fps_arr[i] <= 0:
                continue
            log_f = np.log10(fps_arr[i])
            col = int((log_f - log_min) / (log_max - log_min) * (width - 1))
            col = min(max(col, 0), width - 1)
            row = int(scores_arr[i] / max_score * height)
            row = min(max(row, 0), height)
            grid[row][col] = marker

    # Gamma wave 40Hz line
    gamma_col = int((np.log10(40) - log_min) / (log_max - log_min) * (width - 1))
    gamma_col = min(max(gamma_col, 0), width - 1)
    for row in range(height + 1):
        if grid[row][gamma_col] == " ":
            grid[row][gamma_col] = ":"

    lines.append("")
    lines.append("  D-CCT  * = Rule110  o = RBN  + = ESN  # = LLM  : = 40Hz(gamma)")
    for row in range(height, -1, -1):
        score_val = row / height * max_score
        if row % (height // 5) == 0:
            label = f"  {int(score_val)}|"
        else:
            label = "   |"
        lines.append(f"{label}{''.join(grid[row])}")

    x_axis = "   +" + "-" * width
    lines.append(x_axis)

    tick_fps = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
    tick_str = [" "] * width
    for fps_val in tick_fps:
        log_f = np.log10(fps_val)
        col = int((log_f - log_min) / (log_max - log_min) * (width - 1))
        col = min(max(col, 0), width - 1)
        s = str(fps_val)
        for j, ch in enumerate(s):
            if col + j < width:
                tick_str[col + j] = ch
    lines.append("    " + "".join(tick_str) + "  fps (Hz)")

    return "\n".join(lines)


def print_dcct_comparison_table(all_results):
    """4 systems x D-CCT 5 comparison table."""
    print()
    print(" === D-CCT 5 Test Comparison (fps=highest point) ===")
    print()

    test_keys = ["DT1_Activity", "DT2_Complexity", "DT3_Memory",
                 "DT4_Diversity", "DT5_Flux"]
    test_labels = ["DT1", "DT2", "DT3", "DT4", "DT5"]

    header = f" {'System':<14} |"
    for lbl in test_labels:
        header += f" {lbl:>5} |"
    header += " Peak | Verdict"
    print(header)
    print(" " + "-" * (20 + 8 * len(test_labels) + 18))

    for sys_key, (fps_arr, scores_arr, details) in all_results.items():
        sys_info = SYSTEMS.get(sys_key, {"name": sys_key})
        # Find fps with highest score
        best_idx = np.argmax(scores_arr)
        best_detail = details[best_idx]
        best_results = best_detail["results"]
        best_total = best_detail["total"]
        best_verdict = best_detail["verdict"]
        best_fps = best_detail["fps"]

        row = f" {sys_info['name']:<14} |"
        for key in test_keys:
            score, passed, _ = best_results[key]
            mark = "P" if passed else ("~" if score > 0.7 else "F")
            row += f" {mark}:{score:.2f}|"
        row += f"  {best_total:.1f}/5 | {best_verdict} @{int(best_fps)}Hz"
        print(row)

    print()


def print_fps_comparison_table(all_results):
    """D-CCT score comparison table by fps."""
    print()
    print(" === D-CCT Score Comparison by fps ===")
    print()

    sys_names = {k: SYSTEMS[k]["name"] for k in all_results}

    header = f" {'fps':>6} |"
    for sys_key in all_results:
        header += f" {sys_names[sys_key]:>12} |"
    print(header)
    print(" " + "-" * (10 + 15 * len(all_results)))

    all_fps = sorted(set(
        int(f) for sys_key, (fps_arr, _, _) in all_results.items()
        for f in fps_arr
    ))

    for fps in all_fps:
        row = f" {fps:>6} |"
        for sys_key, (fps_arr, scores_arr, details) in all_results.items():
            idx = None
            for j, f in enumerate(fps_arr):
                if int(f) == fps:
                    idx = j
                    break
            if idx is not None:
                score = scores_arr[idx]
                if score >= 5:
                    mark = "[*]"
                elif score >= 4:
                    mark = "[o]"
                elif score >= 3:
                    mark = "[~]"
                elif score >= 1:
                    mark = "[.]"
                else:
                    mark = "[x]"
                row += f"   {score:>4.1f} {mark}   |"
            else:
                row += f"      -       |"
        print(row)

    print()
    print("  [*]=5/5  [o]=4+  [~]=3  [.]=1~2  [x]=0")
    print()


def print_detail_table(sys_key, details):
    """Detailed D-CCT results by fps for one system."""
    sys_info = SYSTEMS.get(sys_key, {"name": sys_key, "desc": ""})
    print(f" --- {sys_info['name']} ({sys_info['desc']}) ---")
    print(f" {'fps':>6} | {'D-CCT':>5} | {'DT1':>4} | {'DT2':>4} |"
          f" {'DT3':>4} | {'DT4':>4} | {'DT5':>4} | Verdict")
    print(" " + "-" * 70)

    test_keys = ["DT1_Activity", "DT2_Complexity", "DT3_Memory",
                 "DT4_Diversity", "DT5_Flux"]

    for d in details:
        fps = d["fps"]
        total = d["total"]
        r = d["results"]
        marks = []
        for key in test_keys:
            _, passed, _ = r[key]
            marks.append("P" if passed else "F")
        print(f" {fps:>6.0f} | {total:>5.1f} |  {marks[0]}   |  {marks[1]}   |"
              f"  {marks[2]}   |  {marks[3]}   |  {marks[4]}   | {d['verdict']}")

    print()


def print_threshold_analysis(all_results):
    """Threshold fps and gamma wave comparison for each system."""
    print(" === Threshold fps Analysis ===")
    print()

    thresholds = {}
    for sys_key, (fps_arr, scores_arr, _) in all_results.items():
        name = SYSTEMS.get(sys_key, {"name": sys_key})["name"]
        th = find_threshold_fps(fps_arr, scores_arr, target=5.0)
        thresholds[sys_key] = th
        if th is not None:
            ratio = th / 40.0
            print(f"   {name:<14} Threshold fps = {th:>7.1f} Hz  (Gamma ratio {ratio:.2f}x)")
        else:
            th4 = find_threshold_fps(fps_arr, scores_arr, target=4.0)
            if th4 is not None:
                print(f"   {name:<14} 5/5 not reached. 4/5 threshold = {th4:.1f} Hz")
            else:
                print(f"   {name:<14} Threshold fps = Not reached within scan range")

    print()
    print("   --- Gamma Wave (40Hz) Comparison ---")
    print()

    for sys_key, th in thresholds.items():
        name = SYSTEMS.get(sys_key, {"name": sys_key})["name"]
        if th is not None:
            if 30 <= th <= 100:
                print(f"   [!] {name}: Threshold {th:.1f}Hz -> Within gamma band (30-100Hz)!")
            elif th < 30:
                print(f"       {name}: Threshold {th:.1f}Hz -> Below gamma")
            else:
                print(f"       {name}: Threshold {th:.1f}Hz -> Above gamma")
        else:
            print(f"       {name}: 5/5 not reached up to 1000Hz")

    print()


def print_brainwave_mapping(all_results):
    """D-CCT scores by brainwave band."""
    print(" === Brainwave Band Mapping ===")
    print()

    sys_names = {k: SYSTEMS[k]["name"] for k in all_results}

    header = f" {'Band':<20} | {'Hz':>5} |"
    for sys_key in all_results:
        header += f" {sys_names[sys_key]:>12} |"
    print(header)
    print(" " + "-" * (30 + 15 * len(all_results)))

    for wave_name in ["delta", "theta", "alpha", "beta", "gamma"]:
        info = BRAIN_WAVES[wave_name]
        center = info["center"]
        row = f" {info['label']:<20} | {center:>4.0f}  |"

        for sys_key, (fps_arr, scores_arr, _) in all_results.items():
            idx = np.argmin(np.abs(fps_arr - center))
            score = scores_arr[idx]
            if score >= 5:
                mark = "[*]"
            elif score >= 4:
                mark = "[o]"
            elif score >= 3:
                mark = "[~]"
            else:
                mark = " . "
            row += f"   {score:>4.1f} {mark}  |"
        print(row)

    print()


# ═════════════════════════════════════════════
# --compare-continuous: Lorenz CCT vs D-CCT comparison
# ═════════════════════════════════════════════

def run_compare_continuous():
    """Apply both original CCT and D-CCT to Lorenz attractor for comparison."""
    print()
    print("=" * 70)
    print(" Compare: Lorenz Attractor — Original CCT vs D-CCT")
    print("=" * 70)
    print()

    fps_values = [1, 5, 10, 20, 50, 100, 500]
    print(f" fps = {fps_values}")
    print(f" Total points = {TOTAL_POINTS}")
    print()

    cct_keys = ["T1_Gap", "T2_Loop", "T3_Continuity", "T4_Entropy", "T5_Novelty"]
    dcct_keys = ["DT1_Activity", "DT2_Complexity", "DT3_Memory",
                 "DT4_Diversity", "DT5_Flux"]

    print(f" {'fps':>5} | {'CCT':>5} | {'T1':>3} {'T2':>3} {'T3':>3} {'T4':>3} {'T5':>3}"
          f" | {'D-CCT':>5} | {'DT1':>3} {'DT2':>3} {'DT3':>3} {'DT4':>3} {'DT5':>3}")
    print(" " + "-" * 68)

    for fps in fps_values:
        S = simulate_lorenz(fps, total_points=TOTAL_POINTS)

        # Original CCT
        cct_results = _run_original_cct(S)
        cct_passes = sum(1 for k in cct_keys if cct_results[k][1])
        cct_marks = ""
        for k in cct_keys:
            cct_marks += f" {'P':>3}" if cct_results[k][1] else f" {'F':>3}"

        # D-CCT
        dcct_results = run_dcct(S)
        dcct_total, dcct_verdict = judge_dcct(dcct_results)
        dcct_marks = ""
        for k in dcct_keys:
            dcct_marks += f" {'P':>3}" if dcct_results[k][1] else f" {'F':>3}"

        print(f" {fps:>5} | {cct_passes:>3}/5 |{cct_marks}"
              f" | {dcct_total:>3.0f}/5 |{dcct_marks}")

    print()
    print(" CCT  = Original test for continuous systems (consciousness_calc.py)")
    print(" D-CCT = Test specifically for discrete systems (this file)")
    print()
    print(" Interpretation:")
    print("   If both tests show high scores in Lorenz (continuous),")
    print("   it means D-CCT correctly judges continuous systems too.")
    print("   Differences indicate design characteristics of the tests.")
    print()
    print("=" * 70)


# ═════════════════════════════════════════════
# Comprehensive Report
# ═════════════════════════════════════════════

def print_report(all_results):
    """Print comprehensive report."""
    print("=" * 70)
    print(" Discrete CCT (D-CCT) v1.0")
    print(" \"Discrete System-Specific Consciousness Continuity Test\"")
    print("=" * 70)
    print()
    print(" Systems:")
    for sys_key in all_results:
        info = SYSTEMS[sys_key]
        print(f"   {info['marker']}  {info['name']} -- {info['desc']}")
    print()
    print(f" fps = {FPS_VALUES}")
    print(f" Total points = {TOTAL_POINTS}")
    print()
    print(" D-CCT Tests:")
    print("   DT1 Activity   -- State change rate (stagnant ratio < 5%)")
    print("   DT2 Complexity -- Lempel-Ziv complexity (LZ/random > 0.5)")
    print("   DT3 Memory     -- Mutual information MI (MI/H > 0.05)")
    print("   DT4 Diversity  -- Unique state ratio (> 0.3)")
    print("   DT5 Flux       -- Entropy coefficient of variation (CV > 0.05)")
    print()

    # 4 systems x D-CCT 5 comparison table
    print_dcct_comparison_table(all_results)

    # Comparison table by fps
    print_fps_comparison_table(all_results)

    # ASCII graph
    print(" === fps vs D-CCT (4 Systems Overlapped) ===")
    print(ascii_combined_graph(all_results))
    print()

    # Details for each system
    for sys_key, (fps_arr, scores_arr, details) in all_results.items():
        print_detail_table(sys_key, details)

    # Brainwave band mapping
    print_brainwave_mapping(all_results)

    # Threshold fps analysis
    print_threshold_analysis(all_results)

    # Conclusion
    print(" === Conclusion ===")
    print()
    print("   Consciousness continuity thresholds for discrete systems:")
    print()

    any_gamma = False
    for sys_key, (fps_arr, scores_arr, _) in all_results.items():
        name = SYSTEMS[sys_key]["name"]
        th = find_threshold_fps(fps_arr, scores_arr, target=5.0)
        if th is not None and 30 <= th <= 100:
            any_gamma = True
            print(f"   [!] {name}: {th:.0f}Hz -- Within gamma band!")

    if any_gamma:
        print()
        print("   -> Even in discrete systems, ~40Hz (gamma) is the consciousness threshold!")
        print("   -> Minimum synchronization rate of neuron firing (discrete events) = gamma wave")
    else:
        print("   -> No systems matched gamma band. Thresholds depend on system characteristics.")

    print()
    print("   Limitations:")
    print("   - CA/RBN/ESN/Markov are extremely simplified models of the brain")
    print("   - D-CCT thresholds depend on test design (model-dependent)")
    print("   - Mapping between fps and real time is an interpretive choice")
    print()
    print("=" * 70)


# ═════════════════════════════════════════════
# Main
# ═════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Discrete CCT (D-CCT) -- Discrete System-Specific Consciousness Continuity Test",
    )
    parser.add_argument("--system", type=str, default=None,
                        choices=["rule110", "rbn", "esn", "llm"],
                        help="Run only specific system (default: all)")
    parser.add_argument("--fps-only", action="store_true",
                        help="Run fps scan only (skip detailed tests)")
    parser.add_argument("--compare-continuous", action="store_true",
                        help="Compare CCT vs D-CCT on Lorenz attractor")
    parser.add_argument("--total-points", type=int, default=TOTAL_POINTS,
                        help=f"Total state points (default: {TOTAL_POINTS})")

    args = parser.parse_args()

    # --compare-continuous
    if args.compare_continuous:
        run_compare_continuous()
        return

    # System selection
    if args.system:
        systems_to_run = [args.system]
    else:
        systems_to_run = ["rule110", "rbn", "esn", "llm"]

    total_points = args.total_points

    print(f"  Starting D-CCT scan")
    print(f"  Systems: {', '.join(systems_to_run)}")
    print(f"  fps: {FPS_VALUES}")
    print(f"  Total points: {total_points}")
    print()

    all_results = {}
    for sys_key in systems_to_run:
        info = SYSTEMS[sys_key]
        print(f"  [{info['name']}] Scanning...")
        fps_arr, scores_arr, details = scan_system(
            sys_key, fps_values=FPS_VALUES, total_points=total_points,
        )
        all_results[sys_key] = (fps_arr, scores_arr, details)

        th = find_threshold_fps(fps_arr, scores_arr)
        if th is not None:
            print(f"  [{info['name']}] Threshold fps = {th:.1f} Hz")
        else:
            print(f"  [{info['name']}] Threshold fps = Not reached")

    print()

    if args.fps_only:
        # fps scan only
        print_fps_comparison_table(all_results)
        print(" === fps vs D-CCT ===")
        print(ascii_combined_graph(all_results))
        print()
        print_threshold_analysis(all_results)
    else:
        print_report(all_results)


if __name__ == "__main__":
    main()
```