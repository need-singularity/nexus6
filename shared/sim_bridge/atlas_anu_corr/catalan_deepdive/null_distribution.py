#!/usr/bin/env python3
# null_distribution.py - run N_TRIALS urandom x catalan multi_test iterations
# plus one ANU x catalan, emit aggregated CSV.
#
# Usage: null_distribution.py <run_dir> <catalan_digits> [n_trials=30] [max_n=1024]
#
# Outputs in run_dir:
#   null_trials/urandom_<i>.hex   - trial streams (1024B each)
#   null_trials/urandom_<i>.tsv   - per-trial 6-metric results
#   null_dist.csv                 - aggregated: trial,metric,value,p_value
#   if anu_long.hex present:
#     anu_test.tsv                - single ANU trial
#   all_tests.csv                 - combined CSV for downstream analysis

import os, sys, subprocess
import numpy as np

def main():
    if len(sys.argv) < 3:
        print("USAGE: null_distribution.py <run_dir> <catalan_digits> [n_trials=30] [max_n=1024]", file=sys.stderr)
        sys.exit(1)
    run_dir = sys.argv[1]
    digits = sys.argv[2]
    n_trials = int(sys.argv[3]) if len(sys.argv) >= 4 else 30
    max_n = int(sys.argv[4]) if len(sys.argv) >= 5 else 1024

    trials_dir = os.path.join(run_dir, 'null_trials')
    os.makedirs(trials_dir, exist_ok=True)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    multi_test = os.path.join(script_dir, 'multi_test.py')

    all_rows = []  # (trial_id, metric, value, p_value, label, n)

    # Run N urandom trials
    rng = np.random.default_rng(12345)
    for i in range(n_trials):
        hex_path = os.path.join(trials_dir, f'urandom_{i:02d}.hex')
        tsv_path = os.path.join(trials_dir, f'urandom_{i:02d}.tsv')
        if not os.path.exists(hex_path):
            # generate max_n bytes
            bs = rng.integers(0, 256, size=max_n, dtype=np.int64)
            hex_str = ''.join(f'{int(b):02x}' for b in bs)
            with open(hex_path, 'w') as f:
                f.write(hex_str)
        # call multi_test
        if not os.path.exists(tsv_path) or os.path.getsize(tsv_path) < 100:
            r = subprocess.run(['/usr/bin/python3', multi_test, digits, hex_path,
                                f'urandom_{i:02d}', str(max_n)],
                               capture_output=True, text=True, timeout=120)
            with open(tsv_path, 'w') as f:
                f.write(r.stdout)
            if r.returncode != 0:
                print(f'trial {i} ERROR: {r.stderr}', file=sys.stderr)
        # parse
        with open(tsv_path) as f:
            lines = f.read().splitlines()
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split('\t')
            if len(parts) >= 5:
                metric, value, p, label, n = parts[:5]
                all_rows.append((f'urandom_{i:02d}', metric, value, p, label, n))
        print(f'[null] trial {i+1}/{n_trials} done', file=sys.stderr)

    # ANU trial (if available)
    anu_path = os.path.join(run_dir, 'anu_long.hex')
    if os.path.exists(anu_path):
        with open(anu_path) as f:
            anu_hex = f.read().strip()
        anu_bytes = len(anu_hex) // 2
        if anu_bytes >= 64:
            tsv_path = os.path.join(run_dir, 'anu_test.tsv')
            r = subprocess.run(['/usr/bin/python3', multi_test, digits, anu_path,
                                'anu', str(min(max_n, anu_bytes))],
                               capture_output=True, text=True, timeout=120)
            with open(tsv_path, 'w') as f:
                f.write(r.stdout)
            with open(tsv_path) as f:
                lines = f.read().splitlines()
            for line in lines[1:]:
                if not line.strip():
                    continue
                parts = line.split('\t')
                if len(parts) >= 5:
                    metric, value, p, label, n = parts[:5]
                    all_rows.append(('anu', metric, value, p, label, n))
            print(f'[anu] bytes={anu_bytes} done', file=sys.stderr)
        else:
            print(f'[anu] SKIP — only {anu_bytes}B available', file=sys.stderr)

    # write aggregated CSV
    out_csv = os.path.join(run_dir, 'all_tests.csv')
    with open(out_csv, 'w') as f:
        f.write('trial,metric,value,p_value,label,n\n')
        for row in all_rows:
            f.write(','.join(str(r) for r in row) + '\n')
    print(f'# wrote {out_csv} rows={len(all_rows)}', file=sys.stderr)

if __name__ == "__main__":
    main()
