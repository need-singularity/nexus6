I'll translate all Korean text to English in this Python file.

```python
#!/usr/bin/env python3
"""CCT Independence Test — Experiment 14

Analyzes the independence and discriminatory power of 5 CCT tests across
7 presets + 5 counterexample systems (total 12).

Method:
  1. Baseline measurement of 12 systems × 5 CCT tests
  2. Remove each test one by one and judge with 4 → measure verdict changes
  3. Pearson correlation matrix between tests
  4. Consciousness vs non-consciousness discriminatory power ranking
  5. Minimal condition set exploration

Usage:
  python3 cct_independence_test.py
"""

import sys, os

import itertools
import sys

import numpy as np
from scipy import stats as sp_stats

from consciousness_calc import PRESETS, lorenz_simulate, run_cct, judge

# ─────────────────────────────────────────────
# Direct implementation of 5 counterexample systems
# ─────────────────────────────────────────────

def simulate_noise(steps, dt, seed=42):
    """Noise generator + memory: 3D exponential smoothing."""
    rng = np.random.default_rng(seed)
    S = np.zeros((steps, 3))
    alpha = 0.9
    for i in range(1, steps):
        noise = rng.normal(0, 1.0, 3)
        S[i] = alpha * S[i - 1] + (1 - alpha) * noise
    return S


def simulate_weather(steps, dt, seed=42):
    """Weather simulation: Lorenz attractor (σ=10, ρ=28, β=8/3)."""
    rng = np.random.default_rng(seed)
    sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
    noise_strength = 0.05
    S = np.zeros((steps, 3))
    S[0] = [1.0, 1.0, 1.0]
    for i in range(1, steps):
        x, y, z = S[i - 1]
        dx = sigma * (y - x)
        dy = x * (rho - z) - y
        dz = x * y - beta * z
        eps = rng.normal(0, noise_strength, 3)
        S[i, 0] = x + (dx + eps[0]) * dt
        S[i, 1] = y + (dy + eps[1]) * dt
        S[i, 2] = z + (dz + eps[2]) * dt
    return S


def simulate_stock(steps, dt, seed=42):
    """Stock market model: 3D geometric Brownian motion."""
    rng = np.random.default_rng(seed)
    mu = np.array([0.05, 0.02, 0.01])
    sigma_gbm = np.array([0.2, 0.3, 0.15])
    S = np.zeros((steps, 3))
    S[0] = [100.0, 50.0, 20.0]
    corr = np.array([[1.0, 0.3, -0.2],
                      [0.3, 1.0, 0.1],
                      [-0.2, 0.1, 1.0]])
    L = np.linalg.cholesky(corr)
    for i in range(1, steps):
        z = rng.normal(0, 1, 3)
        w = L @ z
        for j in range(3):
            drift = mu[j] * S[i - 1, j] * dt
            diffusion = sigma_gbm[j] * S[i - 1, j] * np.sqrt(dt) * w[j]
            S[i, j] = max(S[i - 1, j] + drift + diffusion, 0.01)
    return S


def simulate_heat(steps, dt, seed=42):
    """Heat diffusion equation: 3 observation points on 1D grid."""
    rng = np.random.default_rng(seed)
    nx = 50
    alpha_heat = 0.1
    dx = 1.0
    T = np.linspace(100, 0, nx)
    obs_points = [10, 25, 40]
    S = np.zeros((steps, 3))
    for i in range(steps):
        for j, p in enumerate(obs_points):
            S[i, j] = T[p]
        source = np.zeros(nx)
        source[15] = 30.0 * np.sin(2 * np.pi * i * dt * 0.1)
        source[35] = 20.0 * np.sin(2 * np.pi * i * dt * 0.07 + 1.0)
        T_new = T.copy()
        for k in range(1, nx - 1):
            laplacian = (T[k + 1] - 2 * T[k] + T[k - 1]) / dx**2
            T_new[k] = T[k] + (alpha_heat * laplacian + source[k]) * dt
            T_new[k] += rng.normal(0, 0.5)
        T_new[0] = 100.0 + 10 * np.sin(2 * np.pi * i * dt * 0.03)
        T_new[-1] = rng.normal(0, 2)
        T = T_new
    return S


def simulate_feedback(steps, dt, seed=42):
    """Simple feedback loop: 3 coupled 1D chaotic maps."""
    rng = np.random.default_rng(seed)
    a, c, d = 3.5, 3.7, 3.3
    b = 0.05
    S = np.zeros((steps, 3))
    S[0] = [0.1, 0.2, 0.3]
    for i in range(1, steps):
        x, y, z = S[i - 1]
        S[i, 0] = np.sin(a * x) + b * rng.normal()
        S[i, 1] = np.sin(c * y + 0.1 * x) + b * rng.normal()
        S[i, 2] = np.sin(d * z + 0.1 * y) + b * rng.normal()
    return S


COUNTEREXAMPLE_SYSTEMS = {
    "cx_noise":    {"simulate": simulate_noise,    "name": "Noise+Memory",       "conscious": False},
    "cx_weather":  {"simulate": simulate_weather,  "name": "Weather Simulation", "conscious": False},
    "cx_stock":    {"simulate": simulate_stock,    "name": "Stock Market",       "conscious": False},
    "cx_heat":     {"simulate": simulate_heat,     "name": "Heat Diffusion",     "conscious": False},
    "cx_feedback": {"simulate": simulate_feedback, "name": "Feedback Loop",      "conscious": False},
}

# Consciousness judgment criterion: judge function's total >= 4 → conscious
CONSCIOUSNESS_THRESHOLD = 4

TEST_KEYS = ["T1_Gap", "T2_Loop", "T3_Continuity", "T4_Entropy", "T5_Novelty"]
TEST_LABELS = {
    "T1_Gap":        "T1 Gap",
    "T2_Loop":       "T2 Loop",
    "T3_Continuity": "T3 Cont.",
    "T4_Entropy":    "T4 Entropy",
    "T5_Novelty":    "T5 Novelty",
}


# ─────────────────────────────────────────────
# Simulation + CCT execution
# ─────────────────────────────────────────────

def run_all_systems(steps=100000, dt=0.01):
    """Run CCT on 7 presets + 5 counterexamples = 12 systems.

    Returns:
        dict: {name: {"results": cct_results, "scores": {key: score},
                       "passes": {key: bool}, "total": float,
                       "verdict": str, "conscious": bool_label}}
    """
    data = {}

    # 7 presets
    for name, preset in PRESETS.items():
        _, S = lorenz_simulate(
            sigma=preset["sigma"], rho=preset["rho"], beta=preset["beta"],
            noise=preset["noise"], gap_ratio=preset["gap_ratio"],
            steps=steps, dt=dt,
        )
        results = run_cct(S, preset["gap_ratio"])
        total, verdict = judge(results)
        data[name] = {
            "results": results,
            "scores": {k: results[k][0] for k in TEST_KEYS},
            "passes": {k: results[k][1] for k in TEST_KEYS},
            "total": total,
            "verdict": verdict,
            "conscious": True,  # Presets are labeled as "consciousness candidates"
            "display": preset["description"],
        }

    # 5 counterexamples
    for key, info in COUNTEREXAMPLE_SYSTEMS.items():
        S = info["simulate"](steps, dt)
        results = run_cct(S, 0.0)
        total, verdict = judge(results)
        data[key] = {
            "results": results,
            "scores": {k: results[k][0] for k in TEST_KEYS},
            "passes": {k: results[k][1] for k in TEST_KEYS},
            "total": total,
            "verdict": verdict,
            "conscious": False,
            "display": info["name"],
        }

    return data


def judge_subset(results, exclude_key):
    """Judge excluding a specific test.

    Same logic as judge() but skips exclude_key.
    Judge with 4 out of 5 tests: scale passing criterion to 4/4.
    """
    passes = 0
    halfs = 0.0
    for k in TEST_KEYS:
        if k == exclude_key:
            continue
        score, passed, _ = results[k]
        if passed:
            passes += 1
        elif score > 0.7:
            halfs += 0.5
    total = passes + halfs

    # 4-test judgment criterion (maintaining ratio from 5 tests)
    if total >= 4:
        return total, "★ Continuous"
    elif total >= 3.2:
        return total, "◎ Weakened"
    elif total >= 2.4:
        return total, "△ Weak"
    elif total >= 0.8:
        return total, "▽ Faint"
    else:
        return total, "✕ None"


# ─────────────────────────────────────────────
# Analysis functions
# ─────────────────────────────────────────────

def removal_impact_analysis(data):
    """Analyze verdict changes when each test is removed.

    Returns:
        impact: dict[test_key] -> list of system names whose verdict changed
        impact_table: dict[test_key][sys_name] -> (original_verdict, new_verdict, changed)
    """
    impact = {k: [] for k in TEST_KEYS}
    impact_table = {k: {} for k in TEST_KEYS}

    for sys_name, sys_data in data.items():
        orig_total = sys_data["total"]
        orig_verdict = sys_data["verdict"]

        for test_key in TEST_KEYS:
            new_total, new_verdict = judge_subset(sys_data["results"], test_key)
            # Verdict change: changed if verdict string differs
            changed = (orig_verdict != new_verdict)
            impact_table[test_key][sys_name] = (orig_verdict, new_verdict, changed)
            if changed:
                impact[test_key].append(sys_name)

    return impact, impact_table


def correlation_matrix(data):
    """Pearson correlation matrix between test scores for 12 systems.

    Returns:
        corr_mat: 5x5 numpy array
        p_mat: 5x5 p-value array
        score_matrix: (12, 5) numpy array
    """
    sys_names = list(data.keys())
    n_sys = len(sys_names)
    score_matrix = np.zeros((n_sys, 5))

    for i, name in enumerate(sys_names):
        for j, key in enumerate(TEST_KEYS):
            score_matrix[i, j] = data[name]["scores"][key]

    corr_mat = np.zeros((5, 5))
    p_mat = np.zeros((5, 5))

    for i in range(5):
        for j in range(5):
            if i == j:
                corr_mat[i, j] = 1.0
                p_mat[i, j] = 0.0
            else:
                r, p = sp_stats.pearsonr(score_matrix[:, i], score_matrix[:, j])
                corr_mat[i, j] = r
                p_mat[i, j] = p

    return corr_mat, p_mat, score_matrix


def discriminatory_power(data):
    """Measure discriminatory power of each test between conscious vs non-conscious.

    Returns:
        power: dict[test_key] -> {"auc": float, "t_stat": float, "p_value": float,
                                   "conscious_mean": float, "nonconscious_mean": float}
    """
    conscious_scores = {k: [] for k in TEST_KEYS}
    nonconscious_scores = {k: [] for k in TEST_KEYS}

    for sys_name, sys_data in data.items():
        target = conscious_scores if sys_data["conscious"] else nonconscious_scores
        for k in TEST_KEYS:
            target[k].append(sys_data["scores"][k])

    power = {}
    for k in TEST_KEYS:
        c = np.array(conscious_scores[k])
        nc = np.array(nonconscious_scores[k])

        c_mean = np.mean(c)
        nc_mean = np.mean(nc)

        # t-test (Welch)
        if len(c) >= 2 and len(nc) >= 2 and np.std(c) + np.std(nc) > 0:
            t_stat, p_value = sp_stats.ttest_ind(c, nc, equal_var=False)
        else:
            t_stat, p_value = 0.0, 1.0

        # Simple AUC: Mann-Whitney U based
        if len(c) > 0 and len(nc) > 0:
            try:
                u_stat, _ = sp_stats.mannwhitneyu(c, nc, alternative='two-sided')
                auc = u_stat / (len(c) * len(nc))
            except ValueError:
                auc = 0.5
        else:
            auc = 0.5

        power[k] = {
            "auc": auc,
            "t_stat": t_stat,
            "p_value": p_value,
            "conscious_mean": c_mean,
            "nonconscious_mean": nc_mean,
            "diff": c_mean - nc_mean,
        }

    return power


def find_minimal_subsets(data):
    """Search for sufficient 2-test combinations.

    "Sufficient" criterion: all conscious systems get 2/2 PASS, all non-conscious < 2/2.
    Also search for more relaxed criterion: combination with maximal separation between conscious and non-conscious.

    Returns:
        results: list of (combo, separation_score, detail)
    """
    results = []

    for size in range(2, 5):
        for combo in itertools.combinations(range(5), size):
            combo_keys = [TEST_KEYS[i] for i in combo]

            # Calculate pass count for each system
            conscious_pass_counts = []
            nonconscious_pass_counts = []

            for sys_name, sys_data in data.items():
                pass_count = sum(1 for k in combo_keys if sys_data["passes"][k])
                if sys_data["conscious"]:
                    conscious_pass_counts.append(pass_count)
                else:
                    nonconscious_pass_counts.append(pass_count)

            c_arr = np.array(conscious_pass_counts)
            nc_arr = np.array(nonconscious_pass_counts)

            # Separation: min conscious pass count - max non-conscious pass count
            c_min = np.min(c_arr) if len(c_arr) > 0 else 0
            nc_max = np.max(nc_arr) if len(nc_arr) > 0 else len(combo_keys)
            separation = c_min - nc_max

            # Mean difference
            mean_diff = np.mean(c_arr) - np.mean(nc_arr)

            combo_labels = "+".join(TEST_LABELS[k] for k in combo_keys)
            perfect = (separation > 0)

            results.append({
                "combo": combo,
                "combo_keys": combo_keys,
                "combo_labels": combo_labels,
                "size": size,
                "separation": separation,
                "mean_diff": mean_diff,
                "perfect": perfect,
                "c_min": c_min,
                "nc_max": nc_max,
                "c_mean": np.mean(c_arr),
                "nc_mean": np.mean(nc_arr),
            })

    results.sort(key=lambda r: (not r["perfect"], -r["separation"], -r["mean_diff"]))
    return results


# ─────────────────────────────────────────────
# ASCII output
# ─────────────────────────────────────────────

def ascii_bar(value, max_width=20, char_fill="█", char_empty="░"):
    """Display 0~1 value as ASCII bar."""
    filled = int(abs(value) * max_width)
    return char_fill * filled + char_empty * (max_width - filled)


def print_header():
    """Print header."""
    print("═" * 75)
    print(" CCT Independence Test — Experiment 14")
    print(" Test independence analysis of 7 presets + 5 counterexamples = 12 systems")
    print("═" * 75)
    print()


def print_baseline(data):
    """Baseline results table."""
    print(" ─── Baseline: 12 systems × 5 tests " + "─" * 39)
    print()
    print(" System                │ T1  │ T2  │ T3  │ T4  │ T5  │Score│ Verdict  │ Type")
    print(" ──────────────────────┼─────┼─────┼─────┼─────┼─────┼─────┼──────────┼──────")

    for sys_name, sys_data in data.items():
        display = sys_data["display"]
        if len(display) > 22:
            display = display[:20] + ".."
        display = f"{display:22s}"

        marks = []
        for k in TEST_KEYS:
            score, passed, _ = sys_data["results"][k]
            if passed:
                marks.append(" ✔ ")
            elif score > 0.7:
                marks.append(" △ ")
            else:
                marks.append(" ✕ ")

        marks_str = "│".join(marks)
        total = sys_data["total"]
        verdict = sys_data["verdict"]
        label = "Conscious" if sys_data["conscious"] else "Counter"
        print(f" {display}│{marks_str}│{total:4.1f}│ {verdict:8s} │ {label}")

    print()


def print_removal_impact(impact, impact_table, data):
    """Test removal impact table."""
    print(" ─── Test Removal Impact Table (5×12) " + "─" * 36)
    print()
    print(" Removed Test  │ Verdict Changes │ Changed Systems")
    print(" ──────────────┼─────────────────┼──────────────────────────────────")

    for k in TEST_KEYS:
        changed = impact[k]
        n_changed = len(changed)
        changed_names = ", ".join(data[s]["display"] for s in changed) if changed else "(none)"
        if len(changed_names) > 35:
            changed_names = changed_names[:33] + ".."
        label = f"{TEST_LABELS[k]:14s}"
        bar = ascii_bar(n_changed / len(data), 10)
        print(f" {label}│ {n_changed:4d}/{len(data):2d}  {bar} │ {changed_names}")

    print()

    # Detailed matrix
    print(" ─── Removal Details (Verdict Changes) " + "─" * 36)
    print()

    sys_names = list(data.keys())
    header = " System                │"
    for k in TEST_KEYS:
        header += f" -{TEST_LABELS[k]:9s}│"
    print(header)
    print(" ──────────────────────┼" + "───────────┼" * 5)

    for sys_name in sys_names:
        display = data[sys_name]["display"]
        if len(display) > 22:
            display = display[:20] + ".."
        display = f"{display:22s}"

        row = f" {display}│"
        for k in TEST_KEYS:
            orig_v, new_v, changed = impact_table[k][sys_name]
            if changed:
                row += f" {orig_v[:2]}→{new_v[:2]}  │"
            else:
                row += "     -     │"
        print(row)

    print()


def print_correlation(corr_mat, p_mat):
    """Print correlation matrix."""
    print(" ─── Pearson Correlation Matrix Between Tests (5×5) " + "─" * 22)
    print()

    # Header
    header = "              │"
    for k in TEST_KEYS:
        header += f" {TEST_LABELS[k]:9s}│"
    print(header)
    print(" ─────────────┼" + "──────────┼" * 5)

    for i, ki in enumerate(TEST_KEYS):
        row = f" {TEST_LABELS[ki]:13s}│"
        for j in range(5):
            r = corr_mat[i, j]
            p = p_mat[i, j]
            sig = "*" if p < 0.05 else " "
            if i == j:
                row += "   1.000  │"
            else:
                row += f" {r:+.3f}{sig}  │"
        print(row)

    print()
    print("  (* = p < 0.05)")
    print()

    # Correlation interpretation
    print(" ─── Correlation Interpretation " + "─" * 42)
    print()
    high_corr = []
    for i in range(5):
        for j in range(i + 1, 5):
            r = corr_mat[i, j]
            if abs(r) > 0.7:
                high_corr.append((TEST_LABELS[TEST_KEYS[i]],
                                  TEST_LABELS[TEST_KEYS[j]], r))

    if high_corr:
        print("  High correlations (|r| > 0.7) — Possible redundancy:")
        for t1, t2, r in high_corr:
            print(f"    {t1} ↔ {t2}: r = {r:+.3f}")
    else:
        print("  No high correlations (|r| > 0.7) — All tests provide independent information")

    low_corr = []
    for i in range(5):
        for j in range(i + 1, 5):
            r = corr_mat[i, j]
            if abs(r) < 0.3:
                low_corr.append((TEST_LABELS[TEST_KEYS[i]],
                                 TEST_LABELS[TEST_KEYS[j]], r))

    if low_corr:
        print()
        print("  Low correlations (|r| < 0.3) — Independent tests:")
        for t1, t2, r in low_corr:
            print(f"    {t1} ↔ {t2}: r = {r:+.3f}")

    print()


def print_discriminatory_power(power):
    """Print discriminatory power ranking."""
    print(" ─── Discriminatory Power Ranking (Conscious vs Non-conscious) " + "─" * 11)
    print()
    print(" Test          │ Conscious Mean │ Non-cons. Mean │  Diff    │ t-statistic │ p-value  │ AUC")
    print(" ──────────────┼────────────────┼────────────────┼──────────┼─────────────┼──────────┼──────")

    # Discriminatory power ranking (by |diff|)
    ranked = sorted(power.items(), key=lambda x: -abs(x[1]["diff"]))

    for k, p in ranked:
        label = f"{TEST_LABELS[k]:14s}"
        print(f" {label}│   {p['conscious_mean']:.3f}        │"
              f"    {p['nonconscious_mean']:.3f}       │"
              f" {p['diff']:+.3f}    │"
              f" {p['t_stat']:+10.3f} │"
              f" {p['p_value']:.4f}   │"
              f" {p['auc']:.3f}")

    print()

    # Visual ranking
    print(" Discriminatory Power ASCII Graph (|mean difference|):")
    print()
    max_diff = max(abs(p["diff"]) for p in power.values())
    for k, p in ranked:
        label = f"{TEST_LABELS[k]:14s}"
        bar_len = int(abs(p["diff"]) / max(max_diff, 0.001) * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)
        sig = "***" if p["p_value"] < 0.001 else ("**" if p["p_value"] < 0.01 else ("*" if p["p_value"] < 0.05 else ""))
        print(f"  {label} {bar} {abs(p['diff']):.3f} {sig}")

    print()


def print_minimal_subsets(subsets, data):
    """Print minimal condition sets."""
    print(" ─── Minimal Condition Set Search " + "─" * 40)
    print()

    # 2-test combinations
    print(" [2-Test Combinations]")
    print()
    print("  Combination                   │ Separation │ Conscious Avg │ Non-cons. Avg │ Perfect Sep.")
    print("  ──────────────────────────────┼────────────┼───────────────┼───────────────┼─────────────")

    combos_2 = [s for s in subsets if s["size"] == 2]
    for s in combos_2[:10]:
        perfect_mark = "  ✔" if s["perfect"] else "  ✕"
        print(f"  {s['combo_labels']:30s}│ {s['separation']:+8.1f}  │"
              f"  {s['c_mean']:8.2f}    │"
              f"   {s['nc_mean']:8.2f}     │{perfect_mark}")

    print()

    # Top 3-test combinations
    print(" [3-Test Combinations (Top 5)]")
    print()
    combos_3 = [s for s in subsets if s["size"] == 3]
    for s in combos_3[:5]:
        perfect_mark = "✔" if s["perfect"] else "✕"
        print(f"  {s['combo_labels']:40s} │ Sep={s['separation']:+.0f}"
              f" │ Cons={s['c_mean']:.2f} │ Counter={s['nc_mean']:.2f} │ {perfect_mark}")

    print()

    # Find optimal combination
    best_perfect = [s for s in subsets if s["perfect"]]
    if best_perfect:
        smallest_perfect = min(best_perfect, key=lambda s: s["size"])
        print(f" ★ Minimal perfect separation set: {smallest_perfect['combo_labels']}")
        print(f"   ({smallest_perfect['size']} tests can perfectly separate conscious/non-conscious)")
        print(f"   Conscious min pass: {smallest_perfect['c_min']}/{smallest_perfect['size']}")
        print(f"   Non-conscious max pass: {smallest_perfect['nc_max']}/{smallest_perfect['size']}")
    else:
        best_sep = subsets[0]
        print(f" ★ No perfect separation possible")
        print(f"   Best: {best_sep['combo_labels']} (separation={best_sep['separation']:+.1f})")
        print(f"   Conscious min: {best_sep['c_min']}, Non-conscious max: {best_sep['nc_max']}")

    print()


def print_summary(data, impact, corr_mat, power, subsets):
    """Comprehensive summary."""
    print(" ═══════════════════════════════════════════════════════════════════════════")
    print(" Comprehensive Summary")
    print(" ═══════════════════════════════════════════════════════════════════════════")
    print()

    # 1. Removal impact summary
    print(" 1) Test Removal Impact (discriminatory power = number of verdict changes):")
    print()
    for k in TEST_KEYS:
        n_changed = len(impact[k])
        rank_bar = "●" * n_changed + "○" * (len(data) - n_changed)
        importance = "High" if n_changed >= 3 else ("Medium" if n_changed >= 1 else "Low")
        print(f"    {TEST_LABELS[k]:14s} {rank_bar} ({n_changed} changes) — {importance}")

    print()

    # 2. Correlation summary
    print(" 2) Inter-test Correlation Summary:")
    redundant = []
    for i in range(5):
        for j in range(i + 1, 5):
            if abs(corr_mat[i, j]) > 0.7:
                redundant.append((TEST_KEYS[i], TEST_KEYS[j], corr_mat[i, j]))

    if redundant:
        for ki, kj, r in redundant:
            print(f"    {TEST_LABELS[ki]} ↔ {TEST_LABELS[kj]}: r={r:+.3f} — Possible redundancy")
    else:
        print("    No high correlations → All tests provide independent information")

    print()

    # 3. Discriminatory power ranking
    ranked = sorted(power.items(), key=lambda x: -abs(x[1]["diff"]))
    print(" 3) Discriminatory Power Ranking (conscious/non-conscious score difference):")
    print()
    for rank, (k, p) in enumerate(ranked, 1):
        sig = "***" if p["p_value"] < 0.001 else ("**" if p["p_value"] < 0.01 else ("*" if p["p_value"] < 0.05 else "n.s."))
        print(f"    {rank}st: {TEST_LABELS[k]:14s} (diff={p['diff']:+.3f}, p={p['p_value']:.4f} {sig})")

    print()

    # 4. Minimal sets
    best_2 = [s for s in subsets if s["size"] == 2]
    best_2_sep = best_2[0] if best_2 else None
    best_perfect = [s for s in subsets if s["perfect"]]

    print(" 4) Minimal Condition Sets:")
    print()
    if best_perfect:
        smallest = min(best_perfect, key=lambda s: s["size"])
        print(f"    ★ Minimal perfect separation: {smallest['combo_labels']} ({smallest['size']} tests)")
        all_same_size = [s for s in best_perfect if s["size"] == smallest["size"]]
        if len(all_same_size) > 1:
            print(f"      Same size alternatives: {len(all_same_size)} combinations")
            for s in all_same_size[:3]:
                print(f"        - {s['combo_labels']}")
    else:
        print(f"    Perfect separation impossible — All 5 tests needed")
        if best_2_sep:
            print(f"    Best 2-test combination: {best_2_sep['combo_labels']}"
                  f" (separation={best_2_sep['separation']:+.1f})")

    print()

    # 5. Conclusion
    most_important = ranked[0][0]
    least_important_impact = min(TEST_KEYS, key=lambda k: len(impact[k]))

    print(" 5) Conclusion:")
    print()
    print(f"    - Most important test: {TEST_LABELS[most_important]}"
          f" (1st in discriminatory power)")
    print(f"    - Least impactful test: {TEST_LABELS[least_important_impact]}"
          f" (minimal changes when removed)")

    if redundant:
        for ki, kj, r in redundant:
            print(f"    - Potential redundancy: {TEST_LABELS[ki]} ↔ {TEST_LABELS[kj]}")
    else:
        print(f"    - No redundant tests: All 5 contribute independently")

    print()
    print("═" * 75)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    steps = 100000
    dt = 0.01

    print_header()
    print(f" Simulation: {steps:,} steps, dt={dt}")
    print(f" Systems: 7 presets + 5 counterexamples = 12 total")
    print()

    # 1. Baseline
    print(" ▶ Simulating 12 systems...", flush=True)
    data = run_all_systems(steps, dt)
    print(f"   Complete: {len(data)} systems")
    print()

    print_baseline(data)

    # 2. Test removal impact
    impact, impact_table = removal_impact_analysis(data)
    print_removal_impact(impact, impact_table, data)

    # 3. Correlation matrix
    corr_mat, p_mat, score_matrix = correlation_matrix(data)
    print_correlation(corr_mat, p_mat)

    # 4. Discriminatory power
    power = discriminatory_power(data)
    print_discriminatory_power(power)

    # 5. Minimal condition sets
    subsets = find_minimal_subsets(data)
    print_minimal_subsets(subsets, data)

    # 6. Summary
    print_summary(data, impact, corr_mat, power, subsets)


if __name__ == "__main__":
    main()
```