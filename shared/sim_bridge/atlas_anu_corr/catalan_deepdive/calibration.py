#!/usr/bin/env python3
# calibration.py - treat each of 50 urandom trials as "pretend ANU" and apply
# the full 6-metric empirical test (each vs the other 49).
# This calibrates: how many pretend-ANUs pass >=1 single-metric p<0.05,
# how many pass Bonferroni, how many pass BH-FDR.
# If ANU's hit rate matches urandom's hit rate, it's null.

import os, sys, json
import numpy as np

def main():
    run_dir = sys.argv[1]
    trials_dir = os.path.join(run_dir, 'null_trials_n128')
    # load all 50 trial tsv
    data = {}  # trial_id -> metric -> (value, p)
    for fn in sorted(os.listdir(trials_dir)):
        if not fn.endswith('.tsv'):
            continue
        tid = fn.replace('.tsv', '')
        data[tid] = {}
        with open(os.path.join(trials_dir, fn)) as f:
            for line in f.read().splitlines()[1:]:
                if not line.strip():
                    continue
                parts = line.split('\t')
                if len(parts) >= 3:
                    m, v, p = parts[0], float(parts[1]), float(parts[2])
                    data[tid][m] = (v, p)
    trial_ids = sorted(data.keys())
    metrics = list(next(iter(data.values())).keys())
    print(f'n_trials={len(trial_ids)} metrics={metrics}', file=sys.stderr)

    # For each trial as "pretend ANU", compute empirical p against the other 49
    pretend_hits = []  # list of dicts
    for i, anu_id in enumerate(trial_ids):
        null_ids = [t for t in trial_ids if t != anu_id]
        anu_vals = data[anu_id]
        per_metric = {}
        for m in metrics:
            av = anu_vals[m][0]
            null_vals = np.array([data[t][m][0] for t in null_ids])
            # one-sided: value >= obs (except spearman: |value| >= |obs|)
            if m == 'spearman':
                p_emp = float((np.sum(np.abs(null_vals) >= abs(av)) + 1) / (len(null_vals) + 1))
            else:
                p_emp = float((np.sum(null_vals >= av) + 1) / (len(null_vals) + 1))
            per_metric[m] = p_emp
        pretend_hits.append(per_metric)

    # Count calibration: how many pretend-ANUs would fire WEAK (>=1 p<0.05), BH, Bonf
    weak_count = 0  # >=1 single-test p<0.05
    two_plus = 0    # >=2 single-test p<0.05
    bh_count = 0
    bonf_count = 0
    alpha_bonf = 0.05 / len(metrics)
    for ph in pretend_hits:
        ps = list(ph.values())
        weaks = sum(1 for p in ps if p < 0.05)
        if weaks >= 1: weak_count += 1
        if weaks >= 2: two_plus += 1
        if any(p < alpha_bonf for p in ps): bonf_count += 1
        # BH
        from numpy import argsort, array
        sorted_ps = sorted(ps)
        passed_bh = False
        for k, p in enumerate(sorted_ps):
            if p <= (k+1)/len(ps) * 0.05:
                passed_bh = True
        if passed_bh: bh_count += 1

    n = len(trial_ids)
    print(json.dumps({
        'n_pretend_anu': n,
        'weak_rate_>=1_single': weak_count / n,
        'weak_rate_>=2_single': two_plus / n,
        'bh_fdr_rate': bh_count / n,
        'bonferroni_rate': bonf_count / n,
        'weak_hits_count': weak_count,
        'bh_hits_count': bh_count,
        'bonferroni_hits_count': bonf_count,
    }, indent=2))

if __name__ == "__main__":
    main()
