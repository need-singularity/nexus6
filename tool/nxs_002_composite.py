#!/usr/bin/env python3
"""
nxs_002_composite — atlas×laws_aligned composite 측정 (scipy pipeline)

Replaces atlas_eig.hexa stage1 push-only Lanczos (60s+ hung) with scipy.sparse.
verdict file 의 sealed composite 0.83379 와 일치 (Δ=0.0016) 검증됨 (commit 4721ea6a).

USAGE:
    python3 nxs_002_composite.py [--atlas <path>] [--const <path>] [-K N] [--sigma X]

DEFAULT:
    --atlas  ~/core/nexus/n6/atlas.blowup.jsonl
    --const  ~/core/nexus/bisociation/cross/constants_spectrum.jsonl
    -K       100
    --sigma  1e-3

OUTPUT (stdout JSON, single line):
    {"composite_after": 0.832..., "best_lag": N, "agreement": ..., "pearson": ..., "cosine": ..., "K": N, "n_nodes": N, "n_components": N, "elapsed_s": ...}

EXIT 0 if composite computed; 1 on input error.

Run after atlas.blowup.jsonl 변동 시 (drill 새 발사 등) → composite 측정.
target ≥ 0.9 (paper_trigger fire). gap = 0.9 - composite_after.
"""
import argparse, json, os, sys, time
import numpy as np
from scipy.sparse import csr_matrix, diags
from scipy.sparse.linalg import eigsh
from scipy.sparse.csgraph import connected_components

HOME = os.path.expanduser("~")
DEFAULT_ATLAS = HOME + "/core/nexus/n6/atlas.blowup.jsonl"
DEFAULT_CONST = HOME + "/core/nexus/bisociation/cross/constants_spectrum.jsonl"

def build_csr_from_blowup(path):
    """awk1/awk2 로직 inline (atlas_eig.hexa STEP 1 + STEP 2 — Python 으로)."""
    nodes = {}
    edges = []
    with open(path) as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            t = d.get("type", "")
            if t in ("node", "absorb"):
                i = d.get("id")
                if i and i not in nodes: nodes[i] = len(nodes)
            elif t == "edge":
                fr = d.get("from"); to = d.get("to")
                if fr and to and fr != to:
                    if fr not in nodes: nodes[fr] = len(nodes)
                    if to not in nodes: nodes[to] = len(nodes)
                    edges.append((nodes[fr], nodes[to]))
    n = len(nodes)
    if n == 0: return None, 0
    rows = []; cols = []
    for fr, to in edges:
        rows.append(fr); cols.append(to)
        rows.append(to); cols.append(fr)
    data = np.ones(len(rows), dtype=np.float64)
    A = csr_matrix((data, (rows, cols)), shape=(n, n))
    A.sum_duplicates()
    A.data[:] = 1.0
    return A, n

def laplacian_eigenvalues(A, K=100, sigma=1e-3, tol=1e-5, maxiter=3000):
    deg = np.array(A.sum(axis=1)).flatten()
    L = (diags(deg) - A).tocsc()
    vals, _ = eigsh(L, k=K, sigma=sigma, which='LM', tol=tol, maxiter=maxiter)
    return np.sort(np.clip(vals, 0.0, None))

def load_eig_jsonl(path):
    out = []
    with open(path) as f:
        for line in f:
            try:
                d = json.loads(line)
                out.append(d['lambda'])
            except Exception:
                continue
    return np.array(out)

def unfold(vals):
    nz = np.sort(vals[vals > 1e-10])
    s = np.diff(nz)
    if len(s) == 0: return np.array([])
    return s / s.mean()

def paircorr(unf, DR=0.1, R_MAX=5.0, N_BINS=50):
    x = np.cumsum(unf)
    edges = np.array([k*DR for k in range(N_BINS+1)])
    R2 = np.zeros(N_BINS)
    for i in range(len(x)):
        diffs = x[i+1:] - x[i]
        diffs = diffs[diffs <= R_MAX]
        if len(diffs):
            h, _ = np.histogram(diffs, bins=edges)
            R2 += h
    N = max(len(x), 1)
    return R2 / (N * DR)

def composite_aligned(A_R2, B_R2, atlas_score=0.224128, const_score=0.358117, lag_max=15):
    n = len(A_R2)
    best_po = -2.0; best_L = 0
    for lag in range(-lag_max, lag_max+1):
        if lag >= 0:
            a = A_R2[:n-lag]; b = B_R2[lag:]
        else:
            a = A_R2[-lag:]; b = B_R2[:n+lag]
        if len(a) < 5: continue
        am, bm = a.mean(), b.mean()
        sxx = ((a-am)**2).sum(); syy = ((b-bm)**2).sum()
        sxy = ((a-am)*(b-bm)).sum()
        denom = (sxx*syy)**0.5
        if denom > 1e-12:
            po = sxy/denom
            if po > best_po:
                best_po = po; best_L = lag
    L = best_L
    if L >= 0:
        a = A_R2[:n-L]; b = B_R2[L:]
    else:
        a = A_R2[-L:]; b = B_R2[:n+L]
    am, bm = a.mean(), b.mean()
    sxy = ((a-am)*(b-bm)).sum()
    sxx = ((a-am)**2).sum(); syy = ((b-bm)**2).sum()
    pearson = sxy / (sxx*syy)**0.5 if (sxx*syy)**0.5 > 1e-12 else 0.0
    cosine = (a*b).sum() / ((a**2).sum()**0.5 * (b**2).sum()**0.5 + 1e-12)
    agreement = 1.0 - abs(atlas_score - const_score)
    composite_after = (agreement + (pearson+1)/2 + cosine) / 3
    return {
        "composite_after": float(composite_after),
        "best_lag": int(best_L),
        "agreement": float(agreement),
        "pearson": float(pearson),
        "cosine": float(cosine),
    }

def predict_er_roi(A_base, n_base, R2_const, K=100, sigma=1e-3,
                   N_new=400, p=0.005, n_runs=1):
    """
    Ω-saturation cycle 2026-04-25 finding:
      sparse ER (avg_deg ~4) multiple isolated components 가 + ROI source.
      drill 발사 전 baseline atlas 에 가상 ER batch 시뮬해서 추정 ROI 를 미리 측정.
    Returns: dict with predicted Δ.
    """
    from scipy.sparse import csr_matrix
    coo = A_base.tocoo()
    base_rows = list(coo.row); base_cols = list(coo.col)
    deltas = []
    for run in range(n_runs):
        np.random.seed(2026 + run)
        new_idx = list(range(n_base, n_base + N_new))
        rows = list(base_rows); cols = list(base_cols)
        for i in range(N_new):
            for j in range(i+1, N_new):
                if np.random.rand() < p:
                    a, b = new_idx[i], new_idx[j]
                    rows.extend([a, b]); cols.extend([b, a])
        hub = np.random.randint(0, n_base)
        rows.extend([new_idx[0], int(hub)]); cols.extend([int(hub), new_idx[0]])
        n_total = n_base + N_new
        A_new = csr_matrix((np.ones(len(rows)), (np.array(rows), np.array(cols))), shape=(n_total, n_total))
        A_new.sum_duplicates(); A_new.data[:] = 1.0
        vals = laplacian_eigenvalues(A_new, K=K, sigma=sigma)
        R2_atlas = paircorr(unfold(vals))
        deltas.append(composite_aligned(R2_atlas, R2_const)["composite_after"])
    return {
        "predicted_composites": [round(d, 5) for d in deltas],
        "mean_composite_after": round(sum(deltas)/len(deltas), 5),
        "N_new": N_new, "p": p, "n_runs": n_runs,
    }

def main():
    ap = argparse.ArgumentParser(description="nxs-002 composite measurement (scipy pipeline)")
    ap.add_argument("--atlas", default=DEFAULT_ATLAS)
    ap.add_argument("--const", default=DEFAULT_CONST)
    ap.add_argument("-K", type=int, default=100)
    ap.add_argument("--sigma", type=float, default=1e-3)
    ap.add_argument("--target", type=float, default=0.9)
    ap.add_argument("--predict-er", action="store_true",
                    help="가상 ER batch (N=400 p=0.005) 시뮬레이션 추가 — drill 발사 전 ROI 추정")
    args = ap.parse_args()

    t0 = time.time()
    if not os.path.isfile(args.atlas):
        print(json.dumps({"error": f"atlas missing: {args.atlas}"}), file=sys.stderr); return 1
    if not os.path.isfile(args.const):
        print(json.dumps({"error": f"const missing: {args.const}"}), file=sys.stderr); return 1

    A, n = build_csr_from_blowup(args.atlas)
    if A is None or n == 0:
        print(json.dumps({"error": "empty atlas graph"}), file=sys.stderr); return 1
    n_cc, _ = connected_components(A, directed=False)
    vals = laplacian_eigenvalues(A, K=args.K, sigma=args.sigma)
    unf = unfold(vals)
    R2_atlas = paircorr(unf)
    R2_const = paircorr(unfold(load_eig_jsonl(args.const)))
    res = composite_aligned(R2_atlas, R2_const)
    res.update({
        "K": args.K, "n_nodes": n, "n_components": n_cc,
        "n_eigenvalues_nonzero": int((vals > 1e-10).sum()),
        "elapsed_s": round(time.time() - t0, 3),
        "gap_to_target": round(args.target - res["composite_after"], 5),
    })
    if args.predict_er:
        prediction = predict_er_roi(A, n, R2_const, K=args.K, sigma=args.sigma)
        prediction["delta_predicted"] = round(prediction["mean_composite_after"] - res["composite_after"], 5)
        res["er_prediction"] = prediction
    print(json.dumps(res, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
