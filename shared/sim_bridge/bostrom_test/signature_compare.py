#!/usr/bin/env python3
# signature_compare.py — compare ANU byte stream against PRNG reference streams
#
# Metrics:
#  1. Birthday / substring overlap (common 32-bit substrings)
#  2. Chi-square byte frequency (each stream; compare to uniform)
#  3. Byte frequency KS distance between ANU and each PRNG
#  4. FFT spectrum L2 distance
#  5. gzip compression ratio (complexity proxy)
#  6. Spectral test for LCG (serial pair distribution deviation)
#  7. Seed brute-force: for MT19937 / glibc_lcg / xorshift32 — try N seeds,
#     look for ANY 8-byte contiguous substring match (birthday argument).
#
# Input: hex string file (ANU stream).  Args: <anu_hex_path> <out_csv> <out_json>

import gzip
import json
import math
import os
import struct
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / 'prng_oracle.py'

PRNGS = ['mt19937', 'glibc_lcg', 'xorshift32', 'xorshift64', 'pcg32', 'chacha20', 'urandom']


def gen_prng(name, n_bytes, seed=12345):
    r = subprocess.run(['/usr/bin/python3', str(SCRIPT), name, str(n_bytes), str(seed)],
                       capture_output=True, text=True, check=True)
    return bytes.fromhex(r.stdout.strip())


# ─── metrics ───

def chi_square_uniform(data: bytes) -> tuple[float, float]:
    """chi-square test for uniform byte distribution, returns (chi2, dof)."""
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    expected = len(data) / 256.0
    chi2 = sum((c - expected) ** 2 / expected for c in counts)
    return chi2, 255


def chi2_to_p(chi2: float, dof: int) -> float:
    """Approximation via Wilson-Hilferty transform (no scipy)."""
    if dof <= 0:
        return 1.0
    # Z = ((chi2/dof)^(1/3) - (1 - 2/(9*dof))) / sqrt(2/(9*dof))
    x = (chi2 / dof) ** (1 / 3)
    mu = 1 - 2 / (9 * dof)
    sigma = math.sqrt(2 / (9 * dof))
    z = (x - mu) / sigma
    # upper-tail p from z via erfc
    p = 0.5 * math.erfc(z / math.sqrt(2))
    return max(min(p, 1.0), 0.0)


def byte_histogram(data: bytes) -> list[int]:
    h = [0] * 256
    for b in data:
        h[b] += 1
    return h


def hist_l2(a: bytes, b: bytes) -> float:
    ha, hb = byte_histogram(a), byte_histogram(b)
    na = sum(ha) or 1
    nb = sum(hb) or 1
    return math.sqrt(sum(((ai / na) - (bi / nb)) ** 2 for ai, bi in zip(ha, hb)))


def gzip_ratio(data: bytes) -> float:
    """Compressed / raw ratio. Closer to 1.0 means less compressible (more random)."""
    if not data:
        return 1.0
    compressed = gzip.compress(data, compresslevel=9)
    return len(compressed) / len(data)


def fft_l2(a: bytes, b: bytes) -> float:
    """Crude DFT magnitude comparison (bucket by low-freq)."""
    # Downsample to first 256 samples for a naive O(N^2) DFT
    m = min(256, len(a), len(b))
    def amps(x):
        out = []
        for k in range(m // 2):
            s_r = 0.0
            s_i = 0.0
            for t in range(m):
                ang = -2 * math.pi * k * t / m
                s_r += (x[t] - 127.5) * math.cos(ang)
                s_i += (x[t] - 127.5) * math.sin(ang)
            out.append(math.sqrt(s_r * s_r + s_i * s_i))
        return out
    A, B = amps(a[:m]), amps(b[:m])
    na = sum(A) or 1
    nb = sum(B) or 1
    return math.sqrt(sum(((ai / na) - (bi / nb)) ** 2 for ai, bi in zip(A, B)))


def substring_overlap(anu: bytes, prng: bytes, k: int = 4) -> int:
    """count of common k-byte windows."""
    a_set = {anu[i:i+k] for i in range(len(anu) - k + 1)}
    count = 0
    for i in range(len(prng) - k + 1):
        if prng[i:i+k] in a_set:
            count += 1
    return count


def spectral_lcg_test(data: bytes) -> float:
    """
    Serial correlation coefficient.  LCG outputs show visible structure
    when consecutive pairs are plotted.  Returns |r| close to 0 for
    uniform, higher for LCG-like streams.
    """
    n = len(data) - 1
    if n < 2:
        return 0.0
    s1 = sum(data[i] * data[i+1] for i in range(n))
    s2 = sum(data[i] for i in range(n))
    s3 = sum(data[i+1] for i in range(n))
    s4 = sum(data[i]*data[i] for i in range(n))
    s5 = sum(data[i+1]*data[i+1] for i in range(n))
    num = n * s1 - s2 * s3
    den = math.sqrt(max(1e-9, (n * s4 - s2*s2) * (n * s5 - s3*s3)))
    return abs(num / den) if den > 0 else 0.0


# ─── seed brute force ───

def seed_brute_force(anu: bytes, prng_name: str, n_seeds: int = 2048, window: int = 6) -> dict:
    """Try n_seeds seeds of prng_name; compute max contiguous-match length
    between ANU first bytes and PRNG output (for each seed), and count
    how many seeds produce a match >= window bytes somewhere in ANU."""
    best_match = 0
    best_seed = -1
    hits_ge_window = 0
    # Build ANU hash index for window-byte rolling lookup
    anu_windows = {anu[i:i+window] for i in range(len(anu) - window + 1)}
    # Limit search for speed — a real brute force of 2^32 is out of scope.
    for seed in range(1, n_seeds + 1):
        try:
            stream = gen_prng(prng_name, len(anu), seed=seed)
        except Exception:
            continue
        # scan for matching window
        found = False
        for i in range(len(stream) - window + 1):
            if stream[i:i+window] in anu_windows:
                hits_ge_window += 1
                found = True
                # measure max contiguous extension
                j = window
                while (i + j) < len(stream) and (anu.find(stream[i:i+j+1]) >= 0):
                    j += 1
                if j > best_match:
                    best_match = j
                    best_seed = seed
                break
        # also count: expected random hits = len(stream) * (len(anu)/256^window)
    # p-value: expected E hits under null
    expected_E = n_seeds * max(1, len(anu) - window + 1) * max(1, len(anu) - window + 1) / (256 ** window)
    return {
        'n_seeds': n_seeds,
        'window': window,
        'hits_ge_window': hits_ge_window,
        'expected_hits': expected_E,
        'ratio': hits_ge_window / max(expected_E, 1e-9),
        'best_match_len': best_match,
        'best_seed': best_seed,
    }


# ─── main ───

def main():
    if len(sys.argv) < 4:
        print('usage: signature_compare.py <anu_hex> <out_csv> <out_json> [src_filter=all]', file=sys.stderr)
        sys.exit(1)
    anu_hex_path = Path(sys.argv[1])
    out_csv = Path(sys.argv[2])
    out_json = Path(sys.argv[3])
    src_filter = sys.argv[4] if len(sys.argv) > 4 else 'all'

    # load hex either from full hex file, or from meta.jsonl when filtering by source
    if src_filter != 'all':
        meta_path = anu_hex_path.with_suffix(anu_hex_path.suffix + '.meta.jsonl')
        if not meta_path.exists():
            meta_path = Path(str(anu_hex_path) + '.meta.jsonl')
        lines = meta_path.read_text().strip().splitlines()
        chunks = []
        for ln in lines:
            if not ln.strip():
                continue
            d = json.loads(ln)
            if d.get('src') == src_filter or (src_filter == 'anu_all' and d.get('src') in ('anu', 'cache')):
                chunks.append(d['hex'])
        anu_hex = ''.join(chunks)
    else:
        anu_hex = anu_hex_path.read_text().strip()

    # strip any whitespace/newlines
    anu_hex = ''.join(anu_hex.split())
    if len(anu_hex) < 128:
        print(f'ERROR: insufficient hex data ({len(anu_hex)//2} bytes, need >=64 for src_filter={src_filter})', file=sys.stderr)
        sys.exit(2)
    anu = bytes.fromhex(anu_hex)
    n = len(anu)
    print(f'# loaded ANU stream: {n} bytes ({n*8} bits)', file=sys.stderr)

    # ANU self metrics
    anu_chi2, anu_dof = chi_square_uniform(anu)
    anu_p = chi2_to_p(anu_chi2, anu_dof)
    anu_gzip = gzip_ratio(anu)
    anu_serial = spectral_lcg_test(anu)

    rows = []
    rows.append(['stream', 'chi2', 'chi2_p', 'gzip_ratio', 'serial_r',
                 'hist_L2_vs_anu', 'fft_L2_vs_anu', 'overlap_4B',
                 'brute_hits', 'brute_expected', 'brute_ratio',
                 'brute_best_match', 'brute_best_seed'])
    rows.append([
        'ANU', f'{anu_chi2:.3f}', f'{anu_p:.6f}', f'{anu_gzip:.5f}',
        f'{anu_serial:.5f}', '0.0', '0.0', '0', '—', '—', '—', '—', '—',
    ])

    prng_results = {}
    for name in PRNGS:
        print(f'# evaluating PRNG: {name}', file=sys.stderr)
        stream = gen_prng(name, n)
        chi2, dof = chi_square_uniform(stream)
        p = chi2_to_p(chi2, dof)
        gz = gzip_ratio(stream)
        sr = spectral_lcg_test(stream)
        h_l2 = hist_l2(anu, stream)
        f_l2 = fft_l2(anu, stream)
        ov = substring_overlap(anu, stream, k=4)

        # seed brute force only for cheap PRNGs
        if name in ('glibc_lcg', 'xorshift32', 'mt19937'):
            brute = seed_brute_force(anu, name, n_seeds=1024, window=6)
        else:
            brute = {'hits_ge_window': None, 'expected_hits': None, 'ratio': None,
                     'best_match_len': None, 'best_seed': None}

        prng_results[name] = {
            'chi2': chi2, 'chi2_p': p, 'gzip_ratio': gz, 'serial_r': sr,
            'hist_L2_vs_anu': h_l2, 'fft_L2_vs_anu': f_l2, 'overlap_4B': ov,
            'brute': brute,
        }
        rows.append([
            name, f'{chi2:.3f}', f'{p:.6f}', f'{gz:.5f}', f'{sr:.5f}',
            f'{h_l2:.6f}', f'{f_l2:.6f}', str(ov),
            str(brute.get('hits_ge_window')), f"{brute.get('expected_hits')}" if brute.get('expected_hits') is not None else '—',
            f"{brute.get('ratio'):.3f}" if isinstance(brute.get('ratio'), float) else '—',
            str(brute.get('best_match_len')),
            str(brute.get('best_seed')),
        ])

    # write CSV
    out_csv.write_text('\n'.join(','.join(r) for r in rows) + '\n')

    # write JSON
    payload = {
        'anu': {
            'n_bytes': n,
            'chi2': anu_chi2, 'chi2_p': anu_p,
            'gzip_ratio': anu_gzip, 'serial_r': anu_serial,
        },
        'prngs': prng_results,
    }
    out_json.write_text(json.dumps(payload, indent=2))
    print(f'# wrote {out_csv} and {out_json}', file=sys.stderr)


if __name__ == '__main__':
    main()
