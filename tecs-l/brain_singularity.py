#!/usr/bin/env python3
"""Brain Atypical Structure Statistical Simulator - Statistical Singularity Detection"""

import argparse
import os
from datetime import datetime

import numpy as np
from scipy import stats
from scipy.signal import argrelextrema


RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
LOG_FILE = os.path.join(RESULTS_DIR, "log.md")
SINGULARITY_FILE = os.path.join(RESULTS_DIR, "singularities.md")


def genius_score(deficit, plasticity, inhibition):
    """Genius = Deficit × Plasticity / Inhibition"""
    return deficit * plasticity / inhibition


def simulate_population(n_samples, seed=42):
    """Generate population based on normal distribution"""
    rng = np.random.default_rng(seed)
    deficits = rng.beta(2, 5, n_samples).clip(0.01, 0.99)
    plasticities = rng.beta(5, 2, n_samples).clip(0.01, 0.99)
    inhibitions = rng.beta(5, 2, n_samples).clip(0.05, 0.99)
    scores = genius_score(deficits, plasticities, inhibitions)
    return scores


def find_critical_points(n_points=1000):
    """Deficit continuous change → critical point (2nd derivative peak) detection"""
    deficits = np.linspace(0.01, 0.99, n_points)
    plasticity_mean = 0.7
    inhibition_base = 0.8

    inhibitions = inhibition_base * np.exp(-3 * deficits**2)
    scores = genius_score(deficits, plasticity_mean, inhibitions)

    d1 = np.gradient(scores, deficits)
    d2 = np.gradient(d1, deficits)

    peaks = argrelextrema(np.abs(d2), np.greater, order=20)[0]

    return deficits, scores, d2, peaks


def ascii_chart(deficits, scores, user_deficit, user_score, critical_indices, width=60, height=20):
    """Terminal ASCII chart"""
    min_s, max_s = scores.min(), scores.max()
    if max_s == min_s:
        max_s = min_s + 1

    chart = [[' ' for _ in range(width)] for _ in range(height)]

    for i in range(width):
        idx = int(i / width * len(scores))
        y = int((scores[idx] - min_s) / (max_s - min_s) * (height - 1))
        y = height - 1 - y
        chart[y][i] = '·'

    for ci in critical_indices:
        x = int(ci / len(deficits) * width)
        x = min(x, width - 1)
        for row in range(height):
            if chart[row][x] == ' ':
                chart[row][x] = '│'

    ux = int(user_deficit / 0.99 * (width - 1))
    ux = min(ux, width - 1)
    uy = int((user_score - min_s) / (max_s - min_s) * (height - 1))
    uy = height - 1 - uy
    uy = max(0, min(uy, height - 1))
    chart[uy][ux] = '★'

    lines = []
    for i, row in enumerate(chart):
        if i == 0:
            label = f"  {max_s:6.2f} ┤"
        elif i == height - 1:
            label = f"  {min_s:6.2f} ┤"
        elif i == height // 2:
            mid = (max_s + min_s) / 2
            label = f"  {mid:6.2f} ┤"
        else:
            label = "         │"
        lines.append(label + ''.join(row))
    lines.append("         └" + "─" * width)
    lines.append(f"         Deficit: 0.0{' ' * (width - 10)}1.0")
    lines.append("")
    lines.append("  · Ability Curve   │ Critical Point   ★ Input Value Position")

    return '\n'.join(lines)


def ensure_results_dir():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write("# Simulation Log\n\n")
            f.write("All execution results are accumulated in chronological order.\n\n")
            f.write("---\n\n")
    if not os.path.exists(SINGULARITY_FILE):
        with open(SINGULARITY_FILE, 'w', encoding='utf-8') as f:
            f.write("# ⚡ Statistical Singularity Log\n\n")
            f.write("Only singularities with Z-Score > 2.0σ are recorded separately.\n\n")
            f.write("---\n\n")


def append_to_log(d, p, i, score, z, percentile, phase, phase_icon, crit_low, crit_high, is_singular, chart_text, pop_mean, pop_std, n_samples):
    """Append each execution result to log.md"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    singular_tag = " `⚡ Singularity`" if is_singular else ""

    entry = f"""## [{now}]{singular_tag}

| Parameter | Value |
|---|---|
| Deficit | {d:.2f} |
| Plasticity | {p:.2f} |
| Inhibition | {i:.2f} |

| Result | Value |
|---|---|
| Genius Score | {score:.2f} |
| Z-Score | {z:.2f}σ |
| Percentile | Top {percentile:.2f}% |
| Phase | {phase_icon} {phase} |
| Critical Point Range | Deficit {crit_low:.2f} ~ {crit_high:.2f} |

<details>
<summary>Ability Curve</summary>

```
{chart_text}
```

</details>

Population: n={n_samples:,} / Mean={pop_mean:.2f} / σ={pop_std:.2f}

---

"""
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(entry)


def append_to_singularities(d, p, i, score, z, percentile, phase):
    """Record singularities separately in singularities.md"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Singularity grade determination
    if abs(z) > 5:
        grade = "🔴 Extreme Singularity"
    elif abs(z) > 3:
        grade = "🟠 Strong Singularity"
    else:
        grade = "🟡 Singularity"

    entry = f"""## {grade} [{now}]

- **Genius Score: {score:.2f}** | **Z-Score: {z:.2f}σ** | Top {percentile:.4f}%
- Deficit={d:.2f} / Plasticity={p:.2f} / Inhibition={i:.2f}
- Phase: {phase}

---

"""
    with open(SINGULARITY_FILE, 'a', encoding='utf-8') as f:
        f.write(entry)


def run_single(d, p, i, pop_scores, curve_d, curve_s, critical_idx, crit_low, crit_high, verbose=True):
    """Single parameter analysis + recording. Returns result dict."""
    score = genius_score(d, p, i)
    z = (score - pop_scores.mean()) / pop_scores.std()
    percentile = (1 - stats.norm.cdf(z)) * 100

    if d < crit_low:
        phase = "Normal Range (Insufficient Compensation Motivation)"
        phase_icon = "○"
    elif d > crit_high + 0.1:
        phase = "Excessive Deficit (Beyond Compensation Limit)"
        phase_icon = "▼"
    else:
        phase = "Within Critical Point (Compensatory Genius Zone)"
        phase_icon = "⚡"

    is_singular = abs(z) > 2.0

    if verbose:
        chart_text = ascii_chart(curve_d, curve_s, d, score, critical_idx)
        print()
        print("═" * 50)
        print("   Brain Atypical Structure Singularity Analysis")
        print("═" * 50)
        print()
        print(f"  Input Parameters:")
        print(f"    Deficit     = {d:.2f}")
        print(f"    Plasticity  = {p:.2f}")
        print(f"    Inhibition  = {i:.2f}")
        print()
        print("─" * 50)
        print(f"  Genius Score: {score:.2f}")
        print(f"  Z-Score: {z:.2f}σ  {'⚡ Statistical Singularity!' if is_singular else '○ Normal Range'}")
        print(f"  Percentile: Top {percentile:.2f}%")
        print("─" * 50)
        print(f"  Critical Point Range: Deficit {crit_low:.2f} ~ {crit_high:.2f}")
        print(f"  Phase Determination: {phase_icon} {phase}")
        print("─" * 50)
        print()
        print("  [ Ability Curve (Deficit vs Genius Score) ]")
        print()
        print(chart_text)
        print()
        print("─" * 50)
        print(f"  Population Statistics (n={len(pop_scores):,})")
        print(f"    Mean: {pop_scores.mean():.2f}")
        print(f"    Standard Deviation: {pop_scores.std():.2f}")
        print(f"    Min/Max: {pop_scores.min():.2f} / {pop_scores.max():.2f}")
        print("═" * 50)

        append_to_log(d, p, i, score, z, percentile, phase, phase_icon,
                      crit_low, crit_high, is_singular, chart_text,
                      pop_scores.mean(), pop_scores.std(), len(pop_scores))

    return {
        'd': d, 'p': p, 'i': i,
        'score': score, 'z': z, 'percentile': percentile,
        'phase': phase, 'phase_icon': phase_icon,
        'is_singular': is_singular,
    }


def run_grid_scan(d_steps, p_steps, i_steps, n_samples):
    """3D parameter grid scan"""
    deficits = np.linspace(0.05, 0.95, d_steps)
    plasticities = np.linspace(0.1, 0.95, p_steps)
    inhibitions = np.linspace(0.05, 0.95, i_steps)

    total = d_steps * p_steps * i_steps
    print()
    print("═" * 60)
    print("   Mass Grid Scan")
    print("═" * 60)
    print(f"  D: {d_steps} steps × P: {p_steps} steps × I: {i_steps} steps = {total:,} combinations")
    print(f"  Population Sample: {n_samples:,}")
    print("─" * 60)

    pop_scores = simulate_population(n_samples)
    pop_mean = pop_scores.mean()
    pop_std = pop_scores.std()

    curve_d, curve_s, d2, critical_idx = find_critical_points()
    if len(critical_idx) > 0:
        crit_low = curve_d[critical_idx[0]]
        crit_high = curve_d[critical_idx[-1]] if len(critical_idx) > 1 else crit_low + 0.15
    else:
        crit_low, crit_high = 0.5, 0.7

    # Calculate entire grid at once with vectorized operations
    D, P, I = np.meshgrid(deficits, plasticities, inhibitions, indexing='ij')
    scores = genius_score(D, P, I)
    z_scores = (scores - pop_mean) / pop_std

    # Singularity mask
    singular_mask = np.abs(z_scores) > 2.0
    n_singular = singular_mask.sum()
    n_strong = (np.abs(z_scores) > 3.0).sum()
    n_extreme = (np.abs(z_scores) > 5.0).sum()

    print(f"\n  Scan Complete!")
    print(f"  ─────────────────────────────────")
    print(f"  Total Combinations:       {total:>8,}")
    print(f"  🟡 Singularities (>2σ):   {n_singular:>8,} ({n_singular/total*100:.1f}%)")
    print(f"  🟠 Strong        (>3σ):   {n_strong:>8,} ({n_strong/total*100:.1f}%)")
    print(f"  🔴 Extreme       (>5σ):   {n_extreme:>8,} ({n_extreme/total*100:.1f}%)")
    print(f"  ─────────────────────────────────")

    # Singularity boundary analysis: threshold values per axis
    print(f"\n  [ Singularity Boundary Analysis ]")
    print()

    # Deficit axis: singularity ratio change
    print(f"  Singularity Ratio by Deficit:")
    for di, dv in enumerate(deficits):
        slice_singular = singular_mask[di, :, :].sum()
        slice_total = p_steps * i_steps
        ratio = slice_singular / slice_total * 100
        bar = "█" * int(ratio / 2) + "░" * (50 - int(ratio / 2))
        print(f"    D={dv:.2f} │{bar}│ {ratio:5.1f}%")

    # Inhibition axis: singularity ratio change
    print(f"\n  Singularity Ratio by Inhibition:")
    for ii, iv in enumerate(inhibitions):
        slice_singular = singular_mask[:, :, ii].sum()
        slice_total = d_steps * p_steps
        ratio = slice_singular / slice_total * 100
        bar = "█" * int(ratio / 2) + "░" * (50 - int(ratio / 2))
        print(f"    I={iv:.2f} │{bar}│ {ratio:5.1f}%")

    # Top 10 singularities
    print(f"\n  [ Top 10 Extreme Singularities ]")
    print(f"  {'Rank':>4} │ {'Deficit':>7} │ {'Plastic':>7} │ {'Inhibit':>7} │ {'Score':>8} │ {'Z-Score':>8} │ Grade")
    print(f"  {'─'*4}─┼─{'─'*7}─┼─{'─'*7}─┼─{'─'*7}─┼─{'─'*8}─┼─{'─'*8}─┼─{'─'*10}")

    flat_idx = np.argsort(z_scores.ravel())[::-1][:10]
    for rank, fi in enumerate(flat_idx, 1):
        di, pi, ii = np.unravel_index(fi, z_scores.shape)
        dv, pv, iv = deficits[di], plasticities[pi], inhibitions[ii]
        sv = scores[di, pi, ii]
        zv = z_scores[di, pi, ii]
        if abs(zv) > 5:
            grade = "🔴 Extreme"
        elif abs(zv) > 3:
            grade = "🟠 Strong"
        else:
            grade = "🟡"
        print(f"  {rank:>4} │ {dv:>7.2f} │ {pv:>7.2f} │ {iv:>7.2f} │ {sv:>8.2f} │ {zv:>7.2f}σ │ {grade}")

    print()
    print("═" * 60)

    # Save results to scan_report.md
    ensure_results_dir()
    scan_file = os.path.join(RESULTS_DIR, "scan_report.md")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(scan_file, 'a', encoding='utf-8') as f:
        f.write(f"# Grid Scan Report [{now}]\n\n")
        f.write(f"- Grid: D={d_steps} × P={p_steps} × I={i_steps} = **{total:,}** combinations\n")
        f.write(f"- Population: n={n_samples:,} / Mean={pop_mean:.2f} / σ={pop_std:.2f}\n\n")
        f.write(f"## Singularity Statistics\n\n")
        f.write(f"| Grade | Criterion | Count | Ratio |\n")
        f.write(f"|---|---|---|---|\n")
        f.write(f"| 🟡 Singularity | >2σ | {n_singular:,} | {n_singular/total*100:.1f}% |\n")
        f.write(f"| 🟠 Strong Singularity | >3σ | {n_strong:,} | {n_strong/total*100:.1f}% |\n")
        f.write(f"| 🔴 Extreme Singularity | >5σ | {n_extreme:,} | {n_extreme/total*100:.1f}% |\n\n")

        f.write(f"## Top 10 Extreme Singularities\n\n")
        f.write(f"| Rank | Deficit | Plasticity | Inhibition | Score | Z-Score | Grade |\n")
        f.write(f"|---|---|---|---|---|---|---|\n")
        for rank, fi in enumerate(flat_idx, 1):
            di, pi, ii = np.unravel_index(fi, z_scores.shape)
            dv, pv, iv = deficits[di], plasticities[pi], inhibitions[ii]
            sv = scores[di, pi, ii]
            zv = z_scores[di, pi, ii]
            grade = "🔴" if abs(zv) > 5 else ("🟠" if abs(zv) > 3 else "🟡")
            f.write(f"| {rank} | {dv:.2f} | {pv:.2f} | {iv:.2f} | {sv:.2f} | {zv:.2f}σ | {grade} |\n")

        f.write(f"\n## Singularity Ratio by Deficit\n\n")
        f.write(f"| Deficit | Singularity Count | Ratio |\n")
        f.write(f"|---|---|---|\n")
        for di, dv in enumerate(deficits):
            cnt = singular_mask[di, :, :].sum()
            f.write(f"| {dv:.2f} | {cnt} | {cnt/(p_steps*i_steps)*100:.1f}% |\n")

        f.write(f"\n## Singularity Ratio by Inhibition\n\n")
        f.write(f"| Inhibition | Singularity Count | Ratio |\n")
        f.write(f"|---|---|---|\n")
        for ii, iv in enumerate(inhibitions):
            cnt = singular_mask[:, :, ii].sum()
            f.write(f"| {iv:.2f} | {cnt} | {cnt/(d_steps*p_steps)*100:.1f}% |\n")

        f.write(f"\n---\n\n")

    print(f"  📁 Scan Report → results/scan_report.md")
    print()

    # Also record singularities in singularities.md (Top 10 only)
    for fi in flat_idx:
        di, pi, ii = np.unravel_index(fi, z_scores.shape)
        dv, pv, iv = deficits[di], plasticities[pi], inhibitions[ii]
        sv = scores[di, pi, ii]
        zv = z_scores[di, pi, ii]
        pctile = (1 - stats.norm.cdf(zv)) * 100
        if dv < crit_low:
            phase = "Normal Range"
        elif dv > crit_high + 0.1:
            phase = "Excessive Deficit"
        else:
            phase = "Within Critical Point"
        append_to_singularities(dv, pv, iv, sv, zv, pctile, phase)


def main():
    parser = argparse.ArgumentParser(description="Brain Atypical Structure Statistical Simulator")
    parser.add_argument('--deficit', type=float, default=0.7, help="Structural deficit degree (0.0~1.0)")
    parser.add_argument('--plasticity', type=float, default=0.8, help="Neuroplasticity coefficient (0.0~1.0)")
    parser.add_argument('--inhibition', type=float, default=0.15, help="Frontal lobe inhibition level (0.01~1.0)")
    parser.add_argument('--samples', type=int, default=10000, help="Simulation sample count")
    parser.add_argument('--scan', action='store_true', help="Grid scan mode")
    parser.add_argument('--grid', type=int, default=20, help="Grid resolution (steps per axis, default 20)")
    args = parser.parse_args()

    ensure_results_dir()

    if args.scan:
        run_grid_scan(args.grid, args.grid, args.grid, args.samples)
        return

    d = np.clip(args.deficit, 0.0, 1.0)
    p = np.clip(args.plasticity, 0.0, 1.0)
    i = np.clip(args.inhibition, 0.01, 1.0)

    pop_scores = simulate_population(args.samples)
    curve_d, curve_s, d2, critical_idx = find_critical_points()

    if len(critical_idx) > 0:
        crit_low = curve_d[critical_idx[0]]
        crit_high = curve_d[critical_idx[-1]] if len(critical_idx) > 1 else crit_low + 0.15
    else:
        crit_low, crit_high = 0.5, 0.7

    result = run_single(d, p, i, pop_scores, curve_d, curve_s, critical_idx, crit_low, crit_high)

    if result['is_singular']:
        append_to_singularities(d, p, i, result['score'], result['z'], result['percentile'], result['phase'])
        print(f"\n  📁 Singularity Record → results/singularities.md")

    print(f"  📁 Full Log → results/log.md")
    print()


if __name__ == '__main__':
    main()