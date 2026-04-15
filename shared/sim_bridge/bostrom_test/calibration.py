#!/usr/bin/env python3
# calibration.py — sanity check Bostrom test pipeline
#
# Generate a urandom "fake-ANU" of same length, run all PRNG comparisons.
# If the pipeline is calibrated correctly, urandom should show a NULL result
# with scores similar to those from real ANU.  Significant divergence between
# urandom and ANU would indicate something unusual in ANU.
#
# Usage: calibration.py <anu_hex_path> <out_json>

import json
import os
import sys
import subprocess
from pathlib import Path

def main():
    if len(sys.argv) < 3:
        print('usage: calibration.py <anu_hex> <out_json>', file=sys.stderr)
        sys.exit(1)
    anu_hex_path = Path(sys.argv[1])
    out_json = Path(sys.argv[2])
    anu_hex = anu_hex_path.read_text().strip()
    n_bytes = len(anu_hex) // 2
    # Build calibration urandom stream of identical length
    cal_hex = os.urandom(n_bytes).hex()
    cal_path = out_json.parent / 'calib_urandom.hex'
    cal_path.write_text(cal_hex)
    cal_csv = out_json.parent / 'calib_compares.csv'
    cal_json = out_json.parent / 'calib_compares.json'
    # Run signature_compare on calibration urandom
    script_dir = Path(__file__).resolve().parent
    cmd = ['/usr/bin/python3', str(script_dir / 'signature_compare.py'),
           str(cal_path), str(cal_csv), str(cal_json)]
    subprocess.run(cmd, check=True)
    # Load both ANU and calibration
    anu_result = json.loads((out_json.parent / out_json.name.replace('calibration', 'compares')).read_text()) if False else None

    # We assume ANU result is in the same folder as prng_compares.json; accept path override
    candidates = list(out_json.parent.glob('*compares*.json'))
    anu_data = None
    for c in candidates:
        if 'calib' in c.name:
            continue
        anu_data = json.loads(c.read_text())
        break

    cal_data = json.loads(cal_json.read_text())
    payload = {
        'n_bytes': n_bytes,
        'anu': anu_data['anu'] if anu_data else None,
        'calibration_urandom': cal_data['anu'],
        'delta': {
            k: (anu_data['anu'][k] - cal_data['anu'][k])
            if anu_data and isinstance(anu_data['anu'].get(k), (int, float)) else None
            for k in ('chi2', 'chi2_p', 'gzip_ratio', 'serial_r')
        } if anu_data else None,
        'suspicion_divergence': {},
    }
    if anu_data:
        for name in anu_data['prngs']:
            a_h = anu_data['prngs'][name]['hist_L2_vs_anu']
            c_h = cal_data['prngs'][name]['hist_L2_vs_anu']
            payload['suspicion_divergence'][name] = {
                'anu_hist_L2': a_h,
                'calib_hist_L2': c_h,
                'delta': a_h - c_h,
            }
    out_json.write_text(json.dumps(payload, indent=2))
    print(f'# wrote {out_json}', file=sys.stderr)

if __name__ == '__main__':
    main()
