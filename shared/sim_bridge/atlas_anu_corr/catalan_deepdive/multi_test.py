#!/usr/bin/env python3
# multi_test.py - 6 statistical tests between a digit-sequence and a byte-stream
#
# Usage: multi_test.py <digit_file> <hex_file> <label> [max_n=1024]
# Emits TSV to stdout: metric<TAB>value<TAB>p_value<TAB>label<TAB>n
#
# Metrics (6):
#   1. Pearson chi^2 on 4x4 contingency (digits in 4 bins, bytes%10 in 4 bins)
#   2. Mutual Information (MI) on the same 4x4 grid - bit units
#   3. KSG k-NN MI estimator (k=4) on raw values
#   4. FFT cross-spectrum peak amplitude
#   5. Spearman rank correlation (with lag 0)
#   6. Distance correlation (energy distance)
#
# p-values use appropriate null distributions:
#   - chi^2: scipy chi2.sf
#   - MI: parametric (2n*MI ~ chi^2 with (r-1)(c-1) df)
#   - KSG MI: permutation bootstrap (200 perms)
#   - FFT peak: amplitude in random-phase null (parametric exp decay)
#   - Spearman: scipy
#   - dCor: distance-corr permutation bootstrap (200 perms)

import sys, os, math
import numpy as np

def load_digits(path, n_max):
    with open(path) as f:
        s = f.read().strip()
    digits = [int(c) for c in s if c.isdigit()]
    return np.array(digits[:n_max], dtype=np.int64)

def load_hex_bytes(path, n_max):
    with open(path) as f:
        h = f.read().strip()
    # hex to byte list
    bs = []
    for i in range(0, len(h)-1, 2):
        try:
            bs.append(int(h[i:i+2], 16))
        except ValueError:
            pass
    return np.array(bs[:n_max], dtype=np.int64)

def bin4(v):
    # 0-2 -> 0, 3-4 -> 1, 5-6 -> 2, 7-9 -> 3
    if v <= 2: return 0
    if v <= 4: return 1
    if v <= 6: return 2
    return 3

def chi2_test(x, y):
    n = min(len(x), len(y))
    C = np.zeros((4,4), dtype=np.int64)
    for i in range(n):
        C[bin4(x[i]), bin4(y[i])] += 1
    rs = C.sum(axis=1, keepdims=True)
    cs = C.sum(axis=0, keepdims=True)
    E = (rs @ cs) / n
    with np.errstate(divide='ignore', invalid='ignore'):
        chi = np.where(E > 0, (C - E)**2 / E, 0.0).sum()
    # df = (4-1)(4-1) = 9
    from scipy.stats import chi2 as _chi2
    p = _chi2.sf(chi, df=9)
    return float(chi), float(p)

def mi_test(x, y):
    n = min(len(x), len(y))
    C = np.zeros((4,4), dtype=np.float64)
    for i in range(n):
        C[bin4(x[i]), bin4(y[i])] += 1
    P = C / n
    px = P.sum(axis=1, keepdims=True)
    py = P.sum(axis=0, keepdims=True)
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = np.where(P > 0, P / (px @ py), 1.0)
        terms = np.where(P > 0, P * np.log2(ratio), 0.0)
    mi_bits = terms.sum()
    # G-test statistic 2n*ln(2)*mi_bits ~ chi^2 df 9
    G = 2.0 * n * math.log(2) * mi_bits
    from scipy.stats import chi2 as _chi2
    p = _chi2.sf(G, df=9)
    return float(mi_bits), float(p)

def ksg_mi(x, y, k=4):
    # Kraskov-Stögbauer-Grassberger estimator (algorithm 1) for MI.
    from scipy.spatial import cKDTree
    from scipy.special import digamma
    n = min(len(x), len(y))
    xx = x[:n].astype(np.float64) + np.random.uniform(-1e-9, 1e-9, n)  # tie-break
    yy = y[:n].astype(np.float64) + np.random.uniform(-1e-9, 1e-9, n)
    pts = np.column_stack([xx, yy])
    tree = cKDTree(pts)
    dists, _ = tree.query(pts, k=k+1, p=np.inf)  # chebyshev
    eps = dists[:, -1]
    tx = cKDTree(xx.reshape(-1,1))
    ty = cKDTree(yy.reshape(-1,1))
    nx = np.array([len(tx.query_ball_point([xx[i]], r=eps[i]-1e-12, p=np.inf)) - 1 for i in range(n)])
    ny_ = np.array([len(ty.query_ball_point([yy[i]], r=eps[i]-1e-12, p=np.inf)) - 1 for i in range(n)])
    mi = digamma(k) - np.mean(digamma(nx+1) + digamma(ny_+1)) + digamma(n)
    return float(max(0.0, mi))

def ksg_test(x, y, n_perm=200):
    mi_obs = ksg_mi(x, y)
    rng = np.random.default_rng(42)
    n = min(len(x), len(y))
    yp = y[:n].copy()
    count = 0
    mis = []
    for _ in range(n_perm):
        rng.shuffle(yp)
        m = ksg_mi(x[:n], yp)
        mis.append(m)
        if m >= mi_obs:
            count += 1
    p = (count + 1) / (n_perm + 1)
    return mi_obs, float(p)

def fft_peak(x, y, n_perm=200):
    # Empirical permutation-based p-value (no parametric null).
    n = min(len(x), len(y))
    xc = (x[:n] - np.mean(x[:n])).astype(np.float64)
    yc = (y[:n] - np.mean(y[:n])).astype(np.float64)
    Fx = np.fft.rfft(xc)
    Fy = np.fft.rfft(yc)
    cross = Fx * np.conj(Fy)
    amp = np.abs(cross)
    if len(amp) < 2:
        return 0.0, 1.0
    peak_obs = float(np.max(amp[1:]))  # skip DC
    # Permutation: shuffle y, recompute peak
    rng = np.random.default_rng(44)
    yp = yc.copy()
    count = 0
    for _ in range(n_perm):
        rng.shuffle(yp)
        Fyp = np.fft.rfft(yp)
        ap = np.abs(Fx * np.conj(Fyp))
        if np.max(ap[1:]) >= peak_obs:
            count += 1
    p = (count + 1) / (n_perm + 1)
    return peak_obs, float(p)

def spearman_test(x, y):
    from scipy.stats import spearmanr
    n = min(len(x), len(y))
    r, p = spearmanr(x[:n], y[:n])
    return float(r), float(p)

def dcor_test(x, y, n_perm=200):
    # Szekely-Rizzo distance correlation
    n = min(len(x), len(y))
    xx = x[:n].astype(np.float64)
    yy = y[:n].astype(np.float64)
    def dmat(v):
        D = np.abs(v.reshape(-1,1) - v.reshape(1,-1))
        row = D.mean(axis=1, keepdims=True)
        col = D.mean(axis=0, keepdims=True)
        gm = D.mean()
        return D - row - col + gm
    A = dmat(xx)
    B = dmat(yy)
    dcov2 = (A * B).mean()
    dvarx = (A * A).mean()
    dvary = (B * B).mean()
    if dvarx <= 0 or dvary <= 0:
        return 0.0, 1.0
    dcor = math.sqrt(max(0.0, dcov2) / math.sqrt(dvarx * dvary))
    # permutation
    rng = np.random.default_rng(43)
    yp = yy.copy()
    count = 0
    for _ in range(n_perm):
        rng.shuffle(yp)
        Bp = dmat(yp)
        d2 = (A * Bp).mean()
        if d2 >= dcov2:
            count += 1
    p = (count + 1) / (n_perm + 1)
    return float(dcor), float(p)

def main():
    if len(sys.argv) < 4:
        print("USAGE: multi_test.py <digits> <hex> <label> [max_n=1024]", file=sys.stderr)
        sys.exit(1)
    digits_path = sys.argv[1]
    hex_path = sys.argv[2]
    label = sys.argv[3]
    n_max = int(sys.argv[4]) if len(sys.argv) >= 5 else 1024

    x = load_digits(digits_path, n_max)
    yb = load_hex_bytes(hex_path, n_max)
    # y sequence: byte % 10 to align with x in 0..9 range
    y_mod = yb % 10
    # for KSG/FFT/dCor use raw bytes (full 0..255 info)
    n_eff = min(len(x), len(y_mod))
    x = x[:n_eff]
    y10 = y_mod[:n_eff]
    yr = yb[:n_eff]

    print(f"metric\tvalue\tp_value\tlabel\tn")
    c, p = chi2_test(x, y10)
    print(f"chi2_4x4\t{c:.6f}\t{p:.6g}\t{label}\t{n_eff}")

    m, p = mi_test(x, y10)
    print(f"mi_4x4_bits\t{m:.6f}\t{p:.6g}\t{label}\t{n_eff}")

    try:
        m, p = ksg_test(x, yr)
        print(f"ksg_mi_k4\t{m:.6f}\t{p:.6g}\t{label}\t{n_eff}")
    except Exception as ex:
        print(f"ksg_mi_k4\tNaN\t1.0\t{label}\t{n_eff}\t# ERROR {ex}", file=sys.stderr)

    pk, p = fft_peak(x, yr)
    print(f"fft_peak\t{pk:.6f}\t{p:.6g}\t{label}\t{n_eff}")

    r, p = spearman_test(x, yr)
    print(f"spearman\t{r:.6f}\t{p:.6g}\t{label}\t{n_eff}")

    try:
        d, p = dcor_test(x, yr)
        print(f"dcor\t{d:.6f}\t{p:.6g}\t{label}\t{n_eff}")
    except Exception as ex:
        print(f"dcor\tNaN\t1.0\t{label}\t{n_eff}\t# ERROR {ex}", file=sys.stderr)

if __name__ == "__main__":
    main()
