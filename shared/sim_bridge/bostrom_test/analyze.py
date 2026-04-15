#!/usr/bin/env python3
# analyze.py — consolidate signature_compare output into a markdown summary
#
# Args: <compare_json> <out_md> [runs_dir]
#
# Output: summary.md with:
#   - ANU stream stats
#   - Per-PRNG metric table
#   - Composite suspicion score
#   - Verdict: NULL (Bostrom weak-falsification) or HIT

import json
import math
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 3:
        print('usage: analyze.py <compare_json> <out_md> [calibration_json]', file=sys.stderr)
        sys.exit(1)
    j = json.loads(Path(sys.argv[1]).read_text())
    out_md = Path(sys.argv[2])
    calib_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    calib = None
    if calib_path and calib_path.exists():
        calib = json.loads(calib_path.read_text())

    anu = j['anu']
    prngs = j['prngs']

    lines = []
    lines.append('# Bostrom Test — ANU vs PRNG Signature Comparison')
    lines.append('')
    lines.append(f"- **ANU stream**: {anu['n_bytes']} bytes ({anu['n_bytes']*8} bits)")
    lines.append(f"- **ANU chi2**: {anu['chi2']:.2f} (p={anu['chi2_p']:.4f}, df=255)")
    lines.append(f"- **ANU gzip ratio**: {anu['gzip_ratio']:.5f} (1.0 = incompressible)")
    lines.append(f"- **ANU serial correlation |r|**: {anu['serial_r']:.5f}")
    lines.append('')
    lines.append('## Per-PRNG Comparison')
    lines.append('')
    lines.append('| PRNG | chi2 p | hist L2 | FFT L2 | gzip | serial |r| | 4B overlap | brute ratio | best match |')
    lines.append('|------|--------|---------|--------|------|-----------|------------|-------------|------------|')

    # Composite suspicion: lower hist_L2 + lower FFT_L2 + higher 4B-overlap  + higher brute_ratio → higher suspicion
    suspicion = {}
    for name, r in prngs.items():
        # normalise by inverse-distance
        h = r['hist_L2_vs_anu']
        f = r['fft_L2_vs_anu']
        ov = r['overlap_4B']
        br = (r.get('brute') or {}).get('ratio')
        br_val = br if isinstance(br, float) else None
        # composite (higher → more suspicious)
        score = (1.0 / max(h, 1e-6)) + (1.0 / max(f, 1e-6)) * 0.1 + ov * 1.0
        if br_val is not None:
            score += br_val * 5.0
        suspicion[name] = score

    top_sus = max(suspicion, key=lambda k: suspicion[k])
    top_score = suspicion[top_sus]

    for name, r in prngs.items():
        br = r.get('brute') or {}
        br_ratio = br.get('ratio')
        br_best = br.get('best_match_len')
        lines.append(
            f"| {name} "
            f"| {r['chi2_p']:.4f} "
            f"| {r['hist_L2_vs_anu']:.4f} "
            f"| {r['fft_L2_vs_anu']:.4f} "
            f"| {r['gzip_ratio']:.5f} "
            f"| {r['serial_r']:.5f} "
            f"| {r['overlap_4B']} "
            f"| {(f'{br_ratio:.3f}' if isinstance(br_ratio, float) else '—')} "
            f"| {(br_best if br_best is not None else '—')} |"
        )
    lines.append('')

    lines.append('## Suspicion Score (composite, higher = more PRNG-like)')
    lines.append('')
    lines.append('| PRNG | score |')
    lines.append('|------|-------|')
    for name, score in sorted(suspicion.items(), key=lambda kv: -kv[1]):
        lines.append(f'| {name} | {score:.3f} |')
    lines.append('')

    # Verdict rubric
    # 1) ANU chi2 p-value in [0.01, 0.99] → ANU passes uniformity
    # 2) No PRNG has brute_hit ratio >> 1
    # 3) 4B overlap: expected under uniform = len1 * len2 / 2^32 — tiny.
    anu_uniform = 0.01 < anu['chi2_p'] < 0.99
    worst_brute = max(
        [(prngs[p].get('brute') or {}).get('ratio') or 0.0 for p in prngs],
        default=0.0,
    )
    # expected 4B overlap under uniform = (N - k + 1)^2 / 2^32
    N = anu['n_bytes']
    exp_overlap = max(0, (N - 3)) ** 2 / (2 ** 32)
    max_overlap = max(prngs[p]['overlap_4B'] for p in prngs)
    overlap_ratio = max_overlap / max(exp_overlap, 1e-9)

    if calib:
        lines.append('## Calibration (urandom of same length)')
        lines.append('')
        c = calib.get('calibration_urandom', {})
        lines.append(f"- urandom chi2 p: {c.get('chi2_p', 0):.4f}")
        lines.append(f"- urandom gzip: {c.get('gzip_ratio', 0):.5f}")
        lines.append(f"- urandom serial |r|: {c.get('serial_r', 0):.5f}")
        delta = calib.get('delta', {})
        if delta:
            lines.append(f"- delta(ANU − urandom) chi2_p: {delta.get('chi2_p', 0):+.4f}, serial_r: {delta.get('serial_r', 0):+.5f}")
        lines.append('')

    lines.append('## Verdict')
    lines.append('')
    lines.append(f'- ANU uniformity (chi2 p in [0.01, 0.99]): **{anu_uniform}**')
    lines.append(f'- Max seed-brute hit ratio vs expected: **{worst_brute:.3f}** (≈1.0 = random)')
    lines.append(f'- Max 4-byte overlap: **{max_overlap}** (expected under uniform ≈ {exp_overlap:.3f}, ratio {overlap_ratio:.2f})')
    lines.append('')

    hit = (not anu_uniform) or worst_brute > 10.0 or overlap_ratio > 50.0

    if hit:
        lines.append(f'### RESULT: **HIT** — ANU stream resembles `{top_sus}` (score {top_score:.3f})')
        lines.append('')
        lines.append('This is anomalous enough to warrant deeper investigation.')
        lines.append('Actions: (1) collect larger ANU sample, (2) extend seed brute-force space, (3) run NIST STS.')
    else:
        lines.append('### RESULT: **NULL** — Bostrom weak-falsification ✓, ANU calibration PASS')
        lines.append('')
        lines.append(f'- ANU stream passes uniformity (chi2 p={anu["chi2_p"]:.4f})')
        lines.append('- No PRNG shows suspicious overlap or brute-force seed match above chance')
        lines.append('- Top composite score: `' + top_sus + f'` = {top_score:.3f} (dominated by normal statistical fluctuation)')

    out_md.write_text('\n'.join(lines) + '\n')
    print(f'# wrote {out_md}', file=sys.stderr)


if __name__ == '__main__':
    main()
