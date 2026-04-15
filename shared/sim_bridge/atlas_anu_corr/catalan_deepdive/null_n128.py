#!/usr/bin/env python3
# null_n128.py - 30 urandom trials at n=128 bytes to match current ANU sample size.
# Writes all_tests_n128.csv in run_dir.

import os, sys, subprocess
import numpy as np

def main():
    if len(sys.argv) < 3:
        print("USAGE: null_n128.py <run_dir> <digits_path>", file=sys.stderr)
        sys.exit(1)
    run_dir = sys.argv[1]
    digits = sys.argv[2]
    n_bytes = int(sys.argv[3]) if len(sys.argv) >= 4 else 128
    n_trials = int(sys.argv[4]) if len(sys.argv) >= 5 else 30

    trials_dir = os.path.join(run_dir, f'null_trials_n{n_bytes}')
    os.makedirs(trials_dir, exist_ok=True)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    multi_test = os.path.join(script_dir, 'multi_test.py')

    rng = np.random.default_rng(67890)  # different seed to avoid correlation with n=1024 trials
    all_rows = []
    for i in range(n_trials):
        hex_path = os.path.join(trials_dir, f'urandom_{i:02d}.hex')
        tsv_path = os.path.join(trials_dir, f'urandom_{i:02d}.tsv')
        if not os.path.exists(hex_path):
            bs = rng.integers(0, 256, size=n_bytes, dtype=np.int64)
            with open(hex_path, 'w') as f:
                f.write(''.join(f'{int(b):02x}' for b in bs))
        if not os.path.exists(tsv_path) or os.path.getsize(tsv_path) < 50:
            r = subprocess.run(['/usr/bin/python3', multi_test, digits, hex_path,
                                f'urandom_n{n_bytes}_{i:02d}', str(n_bytes)],
                               capture_output=True, text=True, timeout=60)
            with open(tsv_path, 'w') as f:
                f.write(r.stdout)
        with open(tsv_path) as f:
            for line in f.read().splitlines()[1:]:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 5:
                        m, v, p, lab, n = parts[:5]
                        all_rows.append((f'urandom_n{n_bytes}_{i:02d}', m, v, p, lab, n))
        print(f'[null n={n_bytes}] trial {i+1}/{n_trials} done', file=sys.stderr)

    # Also include ANU row (from anu_long.hex at current size)
    anu_path = os.path.join(run_dir, 'anu_long.hex')
    if os.path.exists(anu_path):
        with open(anu_path) as f:
            anu_hex = f.read().strip()
        ab = len(anu_hex) // 2
        if ab >= n_bytes:
            # truncate to n_bytes
            tmp_path = os.path.join(run_dir, f'anu_{n_bytes}.hex')
            with open(tmp_path, 'w') as f:
                f.write(anu_hex[:n_bytes*2])
            tsv_path = os.path.join(run_dir, f'anu_test_n{n_bytes}.tsv')
            r = subprocess.run(['/usr/bin/python3', multi_test, digits, tmp_path,
                                f'anu_n{n_bytes}', str(n_bytes)],
                               capture_output=True, text=True, timeout=60)
            with open(tsv_path, 'w') as f:
                f.write(r.stdout)
            with open(tsv_path) as f:
                for line in f.read().splitlines()[1:]:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 5:
                            m, v, p, lab, n = parts[:5]
                            all_rows.append(('anu', m, v, p, lab, n))
            print(f'[anu @ n={n_bytes}] done', file=sys.stderr)

    out_csv = os.path.join(run_dir, f'all_tests_n{n_bytes}.csv')
    with open(out_csv, 'w') as f:
        f.write('trial,metric,value,p_value,label,n\n')
        for row in all_rows:
            f.write(','.join(str(r) for r in row) + '\n')
    print(f'# wrote {out_csv} rows={len(all_rows)}', file=sys.stderr)

if __name__ == "__main__":
    main()
