```python
#!/usr/bin/env python3
"""Brain Profile × CCT Consciousness Continuity Analyzer

Adds CCT (Consciousness Continuity Test) evaluation to the 9 brain profiles from brain_analyzer.py.
Maps each profile's Inhibition (I) to Lorenz parameters to measure consciousness continuity.

Usage:
  python3 brain_cct_analyzer.py          # Comparison table
  python3 brain_cct_analyzer.py --all    # Comparison table + details
  python3 brain_cct_analyzer.py --profile einstein
"""

import argparse
import sys

import numpy as np
from scipy import stats


# ─────────────────────────────────────────────
# 9 Brain Profiles (copied directly from brain_analyzer.py, not imported)
# ─────────────────────────────────────────────

PROFILES = {
    'normal':     {'D': 0.10, 'P': 0.60, 'I': 0.60, 'name': 'Normal'},
    'einstein':   {'D': 0.50, 'P': 0.90, 'I': 0.40, 'name': 'Einstein (estimated)'},
    'savant':     {'D': 0.70, 'P': 0.85, 'I': 0.35, 'name': 'Savant (estimated)'},
    'epilepsy':   {'D': 0.60, 'P': 0.70, 'I': 0.15, 'name': 'Epilepsy patient (estimated)'},
    'meditation': {'D': 0.30, 'P': 0.80, 'I': 0.36, 'name': 'Meditator (estimated)'},
    'child':      {'D': 0.20, 'P': 0.95, 'I': 0.50, 'name': 'Child'},
    'elderly':    {'D': 0.15, 'P': 0.30, 'I': 0.70, 'name': 'Elderly'},
    'acquired':   {'D': 0.60, 'P': 0.70, 'I': 0.30, 'name': 'Acquired savant (estimated)'},
    'sylvian':    {'D': 0.40, 'P': 0.85, 'I': 0.40, 'name': 'Partial Sylvian fissure absence'},
}

# Golden Zone boundaries
GOLDEN_LO = 0.2123   # 1/2 - ln(4/3)
GOLDEN_HI = 0.5000   # Riemann critical line


# ─────────────────────────────────────────────
# I → Lorenz parameter mapping
# ─────────────────────────────────────────────

def inhibition_to_lorenz(I):
    """Map Inhibition value to Lorenz simulator parameters.

    Low I → high sigma, high rho, high noise → chaotic tendency
    High I → low sigma, gap generation → stopped/stable tendency
    """
    sigma = 10.0 * (1.0 - I)
    rho = 28.0 * (1.0 - I / 2.0)
    beta = 2.67
    noise = 0.3 * (1.0 - I)
    gap_ratio = max(0.0, (I - 0.5) * 2.0)
    return {
        'sigma': sigma,
        'rho': rho,
        'beta': beta,
        'noise': noise,
        'gap_ratio': gap_ratio,
    }


# ─────────────────────────────────────────────
# Lorenz Simulator (ported from consciousness_calc.py)
# ─────────────────────────────────────────────

def lorenz_simulate(sigma, rho, beta, noise, gap_ratio, steps, dt, seed=42):
    """Extended Lorenz simulator."""
    rng = np.random.default_rng(seed)
    t = np.arange(steps) * dt
    S = np.zeros((steps, 3))
    S[0] = [1.0, 1.0, 1.0]

    active = np.ones(steps, dtype=bool)
    if gap_ratio > 0:
        n_gap = int(steps * gap_ratio)
        gap_indices = rng.choice(steps, size=n_gap, replace=False)
        active[gap_indices] = False

    for i in range(1, steps):
        if not active[i]:
            S[i] = S[i - 1]
            continue

        x, y, z = S[i - 1]
        dx = sigma * (y - x)
        dy = x * (rho - z) - y
        dz = x * y - beta * z

        eps = rng.normal(0, noise, 3) if noise > 0 else np.zeros(3)

        S[i, 0] = x + (dx + eps[0]) * dt
        S[i, 1] = y + (dy + eps[1]) * dt
        S[i, 2] = z + (dz + eps[2]) * dt

    return t, S


# ─────────────────────────────────────────────
# CCT 5 Tests (ported from consciousness_calc.py)
# ─────────────────────────────────────────────

def compute_entropy(data, bins=30):
    """Shannon entropy of 1D data."""
    hist, _ = np.histogram(data, bins=bins, density=True)
    hist = hist[hist > 0]
    width = (data.max() - data.min()) / bins if data.max() > data.min() else 1
    probs = hist * width
    probs = probs[probs > 0]
    if len(probs) == 0:
        return 0.0
    probs = probs / probs.sum()
    return -np.sum(probs * np.log(probs + 1e-15))


def test_gap(S, gap_ratio):
    """T1 Gap Test: Check for existence of stop intervals."""
    if gap_ratio >= 1.0:
        return 0.0, False, "gap=1.0, fully stopped"
    if gap_ratio > 0:
        return 1.0 - gap_ratio, False, f"gap={gap_ratio:.2f}, stop intervals exist"

    diffs = np.diff(S, axis=0)
    frozen = np.sum(np.all(np.abs(diffs) < 1e-12, axis=1))
    frozen_ratio = frozen / len(diffs)

    if frozen_ratio > 0.01:
        return 1.0 - frozen_ratio, False, f"stop ratio {frozen_ratio:.1%}"

    return 1.0, True, "gap=0, no stop intervals"


def test_loop(S, threshold=0.5):
    """T2 Loop Test: Check for exact trajectory repetition."""
    n = len(S)
    if n < 100:
        return 0.0, False, "insufficient data"

    step = max(1, n // 5000)
    Ss = S[::step]
    ns = len(Ss)

    if np.std(Ss) < 1e-10:
        return 0.0, False, "no state change (constant)"

    scale = np.std(Ss, axis=0).mean()
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

    recurrence_ratio = recurrence / sample_size
    passed = recurrence_ratio < threshold
    score = max(0, 1.0 - recurrence_ratio)

    detail = f"revisit rate={recurrence_ratio:.3f}"
    if passed:
        detail += ", aperiodic"
    else:
        detail += ", periodic repetition detected"

    return score, passed, detail


def test_continuity(S, threshold=0.01):
    """T3 Continuity Test: Check connectivity between adjacent steps."""
    diffs = np.linalg.norm(np.diff(S, axis=0), axis=1)
    n = len(diffs)

    if n < 10:
        return 0.0, False, "insufficient data"

    mean_diff = np.mean(diffs)
    if mean_diff < 1e-12:
        return 0.0, False, "no state change"

    big_jumps = np.sum(diffs > mean_diff * 10)
    frozen = np.sum(diffs < 1e-12)

    jump_ratio = big_jumps / n
    frozen_ratio = frozen / n
    disconnect_ratio = jump_ratio + frozen_ratio

    passed = disconnect_ratio < threshold
    score = max(0, 1.0 - disconnect_ratio * 10)
    score = min(1.0, score)

    detail = f"jumps={jump_ratio:.3f}, stops={frozen_ratio:.3f}"
    if passed:
        detail += ", connection maintained"
    else:
        detail += ", disconnection detected"

    return score, passed, detail


def test_entropy_band(S, window=500, h_min=0.3, h_max=4.5):
    """T4 Entropy Band Test: Check if H(t) stays within band."""
    x = S[:, 0]
    n = len(x)
    n_windows = n // window

    if n_windows < 2:
        return 0.0, False, "insufficient data"

    entropies = []
    for i in range(n_windows):
        w = x[i * window:(i + 1) * window]
        if np.std(w) < 1e-12:
            entropies.append(0.0)
        else:
            entropies.append(compute_entropy(w))

    entropies = np.array(entropies)
    in_band = np.sum((entropies > h_min) & (entropies < h_max))
    ratio = in_band / len(entropies)

    h_range_str = f"H=[{entropies.min():.2f},{entropies.max():.2f}]"
    passed = ratio > 0.95
    score = ratio

    if passed:
        detail = f"{h_range_str}, within band"
    else:
        detail = f"{h_range_str}, out of band {1 - ratio:.1%}"

    return score, passed, detail


def test_novelty(S, window=500, threshold=0.001):
    """T5 Novelty Test: dH/dt != 0 (entropy stagnation ratio)."""
    x = S[:, 0]
    n = len(x)
    n_windows = n // window

    if n_windows < 3:
        return 0.0, False, "insufficient data"

    entropies = []
    for i in range(n_windows):
        w = x[i * window:(i + 1) * window]
        if np.std(w) < 1e-12:
            entropies.append(0.0)
        else:
            entropies.append(compute_entropy(w))

    entropies = np.array(entropies)
    dH = np.abs(np.diff(entropies))

    stagnant = np.sum(dH < threshold)
    stagnant_ratio = stagnant / len(dH) if len(dH) > 0 else 1.0

    passed = stagnant_ratio < 0.05
    score = max(0, 1.0 - stagnant_ratio)

    detail = f"stagnant intervals {stagnant_ratio:.1%}"

    return score, passed, detail


def run_cct(S, gap_ratio):
    """Run CCT 5 tests."""
    results = {}
    results["T1_Gap"] = test_gap(S, gap_ratio)
    results["T2_Loop"] = test_loop(S)
    results["T3_Continuity"] = test_continuity(S)
    results["T4_Entropy"] = test_entropy_band(S)
    results["T5_Novelty"] = test_novelty(S)
    return results


def judge(results):
    """Make comprehensive judgment based on CCT results."""
    passes = sum(1 for _, (_, p, _) in results.items() if p)
    halfs = sum(0.5 for _, (s, p, _) in results.items() if not p and s > 0.7)
    total = passes + halfs

    if total >= 5:
        return total, "continuous"
    elif total >= 4:
        return total, "weakened"
    elif total >= 3:
        return total, "weak"
    elif total >= 1:
        return total, "faint"
    else:
        return total, "none"


def judge_symbol(total):
    """Total score → symbol."""
    if total >= 5:
        return "\u2605"   # ★
    elif total >= 4:
        return "\u25ce"   # ◎
    elif total >= 3:
        return "\u25b3"   # △
    elif total >= 1:
        return "\u25bd"   # ▽
    else:
        return "\u2715"   # ✕


# ─────────────────────────────────────────────
# Genius Score & Z-Score Calculation
# ─────────────────────────────────────────────

def compute_genius(D, P, I):
    """Genius Score and Z-Score."""
    G = D * P / I

    rng = np.random.default_rng(42)
    pop_d = rng.beta(2, 5, 50000).clip(0.01, 0.99)
    pop_p = rng.beta(5, 2, 50000).clip(0.01, 0.99)
    pop_i = rng.beta(5, 2, 50000).clip(0.05, 0.99)
    pop_g = pop_d * pop_p / pop_i

    z = (G - pop_g.mean()) / pop_g.std()
    return G, z


def consciousness_icon(I):
    """Hypothesis 166 consciousness judgment icon."""
    if GOLDEN_LO <= I <= GOLDEN_HI:
        return "\U0001f9e0"  # 🧠
    elif I < GOLDEN_LO:
        return "\u26a1"      # ⚡
    else:
        return "\u26a0\ufe0f"  # ⚠️


# ─────────────────────────────────────────────
# Single Profile Detailed Output
# ─────────────────────────────────────────────

def print_profile_detail(key, prof, cct_results, lorenz_params, G, z):
    """Print single profile details."""
    D, P, I = prof['D'], prof['P'], prof['I']
    total, verdict = judge(cct_results)
    sym = judge_symbol(total)

    print()
    print(f"  {'=' * 60}")
    print(f"  Profile: {prof['name']} ({key})")
    print(f"  {'=' * 60}")
    print(f"  Input:")
    print(f"    Deficit     = {D:.2f}")
    print(f"    Plasticity  = {P:.2f}")
    print(f"    Inhibition  = {I:.2f}")
    print(f"  {'─' * 60}")
    print(f"  Genius Score:")
    print(f"    G = D*P/I = {G:.2f}")
    print(f"    Z-Score   = {z:.2f}\u03c3")

    in_golden = GOLDEN_LO <= I <= GOLDEN_HI
    zone = "\U0001f3af Golden Zone!" if in_golden else ("\u26a1 Below Golden Zone" if I < GOLDEN_LO else "\u25cb Outside Golden Zone")
    print(f"    Golden Zone = {zone}")
    print(f"  {'─' * 60}")
    print(f"  Lorenz Mapping (I={I:.2f}):")
    print(f"    \u03c3={lorenz_params['sigma']:.1f}  "
          f"\u03c1={lorenz_params['rho']:.1f}  "
          f"\u03b2={lorenz_params['beta']:.2f}  "
          f"noise={lorenz_params['noise']:.2f}  "
          f"gap={lorenz_params['gap_ratio']:.2f}")
    print(f"  {'─' * 60}")
    print(f"  CCT Judgment:")

    labels = {
        "T1_Gap":        "T1 Gap       ",
        "T2_Loop":       "T2 Loop      ",
        "T3_Continuity": "T3 Continuity",
        "T4_Entropy":    "T4 Entropy   ",
        "T5_Novelty":    "T5 Novelty   ",
    }

    for tkey, label in labels.items():
        score, passed, detail = cct_results[tkey]
        mark = "\u2714" if passed else ("\u25b3" if score > 0.7 else "\u2715")
        status = "PASS" if passed else "FAIL"
        print(f"    {label} | {mark} {status} | {score:.3f} | {detail}")

    print(f"  {'─' * 60}")
    print(f"  Total: {int(total)}/5  {sym} {verdict}")
    print(f"  {'=' * 60}")


# ─────────────────────────────────────────────
# ASCII Graph: G vs CCT Correlation
# ─────────────────────────────────────────────

def ascii_scatter(profiles_data, width=50, height=12):
    """G (Genius) vs CCT (Consciousness Continuity) ASCII scatter plot."""
    gs = [d['G'] for d in profiles_data]
    ccts = [d['cct_total'] for d in profiles_data]
    names = [d['key'][:4] for d in profiles_data]

    g_min, g_max = min(gs) - 0.1, max(gs) + 0.1
    c_min, c_max = 0, 5.5

    lines = []
    lines.append(f"    CCT")
    lines.append(f"  5.0|" + " " * width + "|")

    grid = [[' ' for _ in range(width)] for _ in range(height)]

    for i, (g, c, nm) in enumerate(zip(gs, ccts, names)):
        col = int((g - g_min) / (g_max - g_min) * (width - 1))
        row = int(c / c_max * (height - 1))
        col = max(0, min(width - 1, col))
        row = max(0, min(height - 1, row))
        ch = nm[0].upper()
        grid[row][col] = ch

    for row in range(height - 1, -1, -1):
        y_val = c_max * row / (height - 1)
        lines.append(f"  {y_val:3.1f}|{''.join(grid[row])}|")

    lines.append(f"     +{'-' * width}+")
    g_labels = f"  {g_min:.1f}" + " " * (width - 8) + f"{g_max:.1f}"
    lines.append(f"      {g_labels}")
    lines.append(f"      {'G (Genius Score)':^{width}}")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# Full Comparison Table
# ─────────────────────────────────────────────

def run_all(show_detail=False, steps=50000, dt=0.01):
    """Compare all 9 profiles."""
    print()
    print("=" * 90)
    print("   Brain CCT Analyzer v1.0")
    print("   Brain Profile x Consciousness Continuity (CCT) Integrated Analysis")
    print("=" * 90)

    profiles_data = []

    for key, prof in PROFILES.items():
        D, P, I = prof['D'], prof['P'], prof['I']
        G, z = compute_genius(D, P, I)
        lp = inhibition_to_lorenz(I)

        _, S = lorenz_simulate(
            sigma=lp['sigma'], rho=lp['rho'], beta=lp['beta'],
            noise=lp['noise'], gap_ratio=lp['gap_ratio'],
            steps=steps, dt=dt,
        )

        cct_results = run_cct(S, lp['gap_ratio'])
        total, verdict = judge(cct_results)

        in_golden = GOLDEN_LO <= I <= GOLDEN_HI
        icon = consciousness_icon(I)

        profiles_data.append({
            'key': key,
            'prof': prof,
            'D': D, 'P': P, 'I': I,
            'G': G, 'z': z,
            'lorenz': lp,
            'cct_results': cct_results,
            'cct_total': total,
            'verdict': verdict,
            'in_golden': in_golden,
            'icon': icon,
        })

        if show_detail:
            print_profile_detail(key, prof, cct_results, lp, G, z)

    # ─── Comparison Table ───
    print()
    hdr =  " Profile          |  D   |  P   |  I    |   G    |    Z     | Mind | CCT | Contin."
    sep =  " ----------------+------+------+-------+--------+----------+------+-----+--------"
    print(hdr)
    print(sep)

    for d in profiles_data:
        name_disp = f"{d['prof']['name'][:14]:14s}"
        sym = judge_symbol(d['cct_total'])
        cct_str = f"{int(d['cct_total'])}/5"
        z_str = f"{d['z']:+.2f}\u03c3"
        print(f" {name_disp}  | {d['D']:.2f} | {d['P']:.2f} | {d['I']:.2f}  | {d['G']:6.2f} | {z_str:>8s} | {d['icon']:>3s}  | {cct_str} | {sym} {d['verdict']}")

    print(sep)
    print()

    # ─── ASCII Scatter Plot: G vs CCT ───
    print(" --- G (Genius) vs CCT (Continuity) Correlation " + "-" * 40)
    print(ascii_scatter(profiles_data))
    print()

    # ─── Key Findings ───
    print(" --- Key Findings " + "-" * 55)

    # 1) Golden Zone vs CCT
    golden_ccts = [d['cct_total'] for d in profiles_data if d['in_golden']]
    non_golden_ccts = [d['cct_total'] for d in profiles_data if not d['in_golden']]

    golden_mean = np.mean(golden_ccts) if golden_ccts else 0
    non_golden_mean = np.mean(non_golden_ccts) if non_golden_ccts else 0

    print()
    print(f"  [1] Golden Zone vs CCT Score:")
    print(f"      Within Golden Zone avg CCT = {golden_mean:.1f}/5  (N={len(golden_ccts)})")
    print(f"      Outside Golden Zone avg CCT = {non_golden_mean:.1f}/5  (N={len(non_golden_ccts)})")
    if golden_mean > non_golden_mean:
        print(f"      --> Profiles within Golden Zone have higher CCT scores (+{golden_mean - non_golden_mean:.1f})")
    else:
        print(f"      --> No difference or reversed")

    # 2) G vs CCT correlation
    gs = np.array([d['G'] for d in profiles_data])
    ccts = np.array([d['cct_total'] for d in profiles_data])

    if len(gs) > 2:
        corr, p_val = stats.pearsonr(gs, ccts)
        print()
        print(f"  [2] G (Genius) vs CCT Correlation:")
        print(f"      Pearson r = {corr:.3f}  (p = {p_val:.4f})")
        if corr > 0.5:
            print(f"      --> Strong positive correlation: Higher genius correlates with higher consciousness continuity")
        elif corr > 0.2:
            print(f"      --> Weak positive correlation")
        elif corr > -0.2:
            print(f"      --> No correlation")
        else:
            print(f"      --> Negative correlation")

    # 3) Consciousness judgment (Hypothesis 166) vs CCT agreement
    print()
    print(f"  [3] Consciousness Judgment (H-166) vs CCT Agreement:")

    match_count = 0
    for d in profiles_data:
        h166_conscious = d['in_golden']  # H-166: Golden Zone = conscious
        cct_conscious = d['cct_total'] >= 4  # CCT: 4+ = conscious
        matched = (h166_conscious == cct_conscious)
        if matched:
            match_count += 1
        mark = "\u2714" if matched else "\u2715"
        pname = d['prof']['name'][:12]
        h166_label = 'Y' if h166_conscious else 'N'
        cct_label = 'Y' if cct_conscious else 'N'
        print(f"      {pname:12s}  H166={h166_label}  CCT={cct_label}  {mark}")

    match_ratio = match_count / len(profiles_data)
    print(f"      Agreement: {match_count}/{len(profiles_data)} ({match_ratio:.0%})")

    # 4) Highest/Lowest
    print()
    best = max(profiles_data, key=lambda d: d['cct_total'])
    worst = min(profiles_data, key=lambda d: d['cct_total'])
    print(f"  [4] Highest CCT: {best['prof']['name']} ({int(best['cct_total'])}/5)")
    print(f"      Lowest CCT: {worst['prof']['name']} ({int(worst['cct_total'])}/5)")

    print()
    print("=" * 90)


# ─────────────────────────────────────────────
# Single Profile Execution
# ─────────────────────────────────────────────

def run_single(key, steps=50000, dt=0.01):
    """Analyze single profile."""
    if key not in PROFILES:
        print(f"  [Error] Unknown profile: {key}")
        print(f"  Available: {', '.join(PROFILES.keys())}")
        sys.exit(1)

    prof = PROFILES[key]
    D, P, I = prof['D'], prof['P'], prof['I']
    G, z = compute_genius(D, P, I)
    lp = inhibition_to_lorenz(I)

    _, S = lorenz_simulate(
        sigma=lp['sigma'], rho=lp['rho'], beta=lp['beta'],
        noise=lp['noise'], gap_ratio=lp['gap_ratio'],
        steps=steps, dt=dt,
    )

    cct_results = run_cct(S, lp['gap_ratio'])

    print()
    print("=" * 65)
    print("   Brain CCT Analyzer v1.0")
    print("=" * 65)

    print_profile_detail(key, prof, cct_results, lp, G, z)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Brain Profile x CCT Consciousness Continuity Analyzer",
    )
    parser.add_argument('--profile', type=str, default=None,
                        choices=list(PROFILES.keys()),
                        help="Analyze single profile")
    parser.add_argument('--all', action='store_true',
                        help="Full comparison table + profile details")
    parser.add_argument('--steps', type=int, default=50000,
                        help="Simulation steps (default: 50000)")
    parser.add_argument('--dt', type=float, default=0.01,
                        help="Time interval (default: 0.01)")
    args = parser.parse_args()

    if args.profile:
        run_single(args.profile, steps=args.steps, dt=args.dt)
    elif args.all:
        run_all(show_detail=True, steps=args.steps, dt=args.dt)
    else:
        # Run without arguments → comparison table only (no details)
        run_all(show_detail=False, steps=args.steps, dt=args.dt)


if __name__ == '__main__':
    main()
```