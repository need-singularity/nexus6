#!/usr/bin/env python3
# bonferroni_panel.py - final multi-testing correction panel.
# Reads all_tests.csv (trial,metric,value,p_value,label,n),
# builds per-metric null distributions from 30 urandom trials,
# compares the ANU trial against empirical null, applies Bonferroni + BH-FDR.
#
# Usage: bonferroni_panel.py <run_dir>
#
# Writes:
#   verdict.md    - final verdict + tables
#   summary.json  - machine-readable

import os, sys, json, math
import numpy as np

def main():
    if len(sys.argv) < 2:
        print("USAGE: bonferroni_panel.py <run_dir>", file=sys.stderr)
        sys.exit(1)
    run_dir = sys.argv[1]
    csv = os.path.join(run_dir, 'all_tests.csv')
    if not os.path.exists(csv):
        print(f"missing {csv}", file=sys.stderr)
        sys.exit(1)

    # parse
    rows = []
    with open(csv) as f:
        next(f)
        for line in f:
            parts = line.strip().split(',')
            if len(parts) < 6:
                continue
            trial, metric, value, pv, label, n = parts[:6]
            try:
                v = float(value)
                p = float(pv)
                rows.append((trial, metric, v, p, label, int(n)))
            except Exception:
                continue

    # group by metric
    metrics = sorted(set(r[1] for r in rows))
    anu_rows = [r for r in rows if r[0] == 'anu']
    null_by_metric = {m: [] for m in metrics}
    for r in rows:
        if r[0].startswith('urandom'):
            null_by_metric[r[1]].append(r)

    # Build summary table
    summary = {
        'metrics': [],
        'n_trials_null': len(set(r[0] for r in rows if r[0].startswith('urandom'))),
        'has_anu': len(anu_rows) > 0,
        'anu_n_bytes': anu_rows[0][5] if anu_rows else 0,
    }

    # For each metric:
    #   compute empirical p-value of ANU value vs null distribution
    #   (one-sided for test statistics where larger => more departure from independence)
    # Metrics where "larger |value|" indicates dependence:
    #   chi2_4x4, mi_4x4_bits, ksg_mi_k4, fft_peak, dcor: one-sided (value >= obs)
    #   spearman: two-sided (|value|)
    one_sided = {'chi2_4x4', 'mi_4x4_bits', 'ksg_mi_k4', 'fft_peak', 'dcor'}

    lines_table = []
    p_parametric_anu = []
    p_empirical_anu = []

    for m in metrics:
        nulls = null_by_metric.get(m, [])
        null_vals = np.array([r[2] for r in nulls], dtype=np.float64)
        null_ps = np.array([r[3] for r in nulls], dtype=np.float64)

        anu = [r for r in anu_rows if r[1] == m]
        if not anu:
            continue
        av = anu[0][2]
        ap = anu[0][3]

        # empirical p: fraction of null values at least as extreme
        if len(null_vals) == 0:
            p_emp = float('nan')
        else:
            if m == 'spearman':
                p_emp = float((np.sum(np.abs(null_vals) >= abs(av)) + 1) / (len(null_vals) + 1))
            else:
                p_emp = float((np.sum(null_vals >= av) + 1) / (len(null_vals) + 1))

        # z-score vs null
        if len(null_vals) > 1 and np.std(null_vals) > 0:
            z = float((av - np.mean(null_vals)) / np.std(null_vals))
        else:
            z = 0.0

        p_parametric_anu.append(ap)
        p_empirical_anu.append(p_emp)

        summary['metrics'].append({
            'metric': m,
            'anu_value': av,
            'anu_p_parametric': ap,
            'anu_p_empirical': p_emp,
            'z_vs_null': z,
            'null_mean': float(np.mean(null_vals)) if len(null_vals) else float('nan'),
            'null_std': float(np.std(null_vals)) if len(null_vals) else float('nan'),
            'null_n': len(null_vals),
        })
        lines_table.append((m, av, ap, p_emp, z))

    # Bonferroni: 6 metrics only (on ANU). alpha_bonf = 0.05 / 6 = 0.00833
    K = len(lines_table)
    alpha_bonf = 0.05 / max(K, 1)

    # Also consider the TRUE multi-testing scope: 6 metrics × 30 null trials = 180 tests.
    # But the trials themselves are NULL — they represent the null distribution sampling,
    # not separate hypotheses. So the number of simultaneous hypotheses on ANU is 6.
    # For completeness also compute BH-FDR over the 6 ANU p-values.

    def bh_fdr(ps, alpha=0.05):
        n = len(ps)
        order = np.argsort(ps)
        sorted_ps = np.array(ps)[order]
        passed = np.zeros(n, dtype=bool)
        last_k = -1
        for k in range(n):
            if sorted_ps[k] <= (k+1) / n * alpha:
                last_k = k
        if last_k >= 0:
            for k in range(last_k+1):
                passed[order[k]] = True
        return passed

    ps_emp = np.array([t[3] for t in lines_table])
    ps_par = np.array([t[2] for t in lines_table])
    bh_emp = bh_fdr(ps_emp, 0.05)
    bh_par = bh_fdr(ps_par, 0.05)
    bonf_emp = ps_emp < alpha_bonf
    bonf_par = ps_par < alpha_bonf

    # Also count weak (single-test p<0.05)
    weak_emp = ps_emp < 0.05
    weak_par = ps_par < 0.05

    summary['alpha_bonferroni'] = alpha_bonf
    summary['n_metrics'] = K
    summary['bonferroni_pass_empirical'] = [bool(x) for x in bonf_emp]
    summary['bonferroni_pass_parametric'] = [bool(x) for x in bonf_par]
    summary['bh_fdr_pass_empirical'] = [bool(x) for x in bh_emp]
    summary['bh_fdr_pass_parametric'] = [bool(x) for x in bh_par]

    # Verdict logic
    n_bonf_emp = int(bonf_emp.sum())
    n_bh_emp = int(bh_emp.sum())
    n_weak_emp = int(weak_emp.sum())

    if n_bonf_emp >= 1:
        verdict = "DISCOVERY"
    elif n_bh_emp >= 1:
        verdict = "STRONG SIGNAL"
    elif n_weak_emp >= 1:
        verdict = "WEAK HIT (single-test only)"
    else:
        verdict = "NULL"
    summary['verdict'] = verdict

    # Write summary.json
    with open(os.path.join(run_dir, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)

    # Write verdict.md
    md = []
    md.append('# Catalan x ANU QRNG deep-dive verdict\n')
    md.append(f'run_dir: `{run_dir}`')
    md.append(f'null_trials (urandom): {summary["n_trials_null"]}')
    md.append(f'anu_bytes: {summary["anu_n_bytes"]}')
    md.append(f'metrics_tested: {K}')
    md.append(f'alpha_bonferroni (0.05/K): {alpha_bonf:.6f}\n')
    md.append('## Per-metric results (ANU vs 30 urandom null)\n')
    md.append('| metric | ANU value | p (parametric) | p (empirical) | z vs null | Bonf(emp) | BH(emp) |')
    md.append('|---|---|---|---|---|---|---|')
    for i, (m, av, ap, pe, z) in enumerate(lines_table):
        be = 'PASS' if bonf_emp[i] else '-'
        bh = 'PASS' if bh_emp[i] else '-'
        md.append(f'| {m} | {av:.4g} | {ap:.4g} | {pe:.4g} | {z:+.2f} | {be} | {bh} |')
    md.append('\n## Summary counts\n')
    md.append(f'- Bonferroni (emp p < {alpha_bonf:.4f}): **{n_bonf_emp}/{K}**')
    md.append(f'- BH-FDR 0.05 (emp): **{n_bh_emp}/{K}**')
    md.append(f'- Single-test p<0.05 (emp): {n_weak_emp}/{K}')
    md.append('')
    md.append('## Verdict\n')
    md.append(f'**{verdict}**')
    md.append('')
    if verdict == "DISCOVERY":
        md.append('At least one metric passes Bonferroni correction on empirical null distribution.')
        md.append('This survives the most conservative multiple-testing adjustment.')
    elif verdict == "STRONG SIGNAL":
        md.append('At least one metric passes Benjamini-Hochberg FDR 0.05 but not Bonferroni.')
        md.append('Suggestive but not definitive - recommend 4x sample expansion.')
    elif verdict.startswith("WEAK"):
        md.append('Single-test p<0.05 but does not survive multiple-testing correction.')
        md.append('**Consistent with multi-test artifact** - no discovery claim.')
    else:
        md.append('No metric departs from urandom null distribution.')
        md.append('**Catalan x ANU digits are independent.** First-run signal was noise.')

    with open(os.path.join(run_dir, 'verdict.md'), 'w') as f:
        f.write('\n'.join(md) + '\n')
    print(verdict)

if __name__ == "__main__":
    main()
