#!/usr/bin/env python3
"""nexus/modules/qmirror/_python_bridge/phi_runner.py

raw#9 disclosure (the THIRD .py file under nexus/modules/)
=========================================================

raw#9 spirit (hexa-only nexus deliverables) is preserved by quarantining
this helper to _python_bridge/.  The reason this file is python is:

    Hexa has no `slogdet` (signed log-determinant) primitive and no
    matrix-covariance / argsort helpers.  The anima_phi_v3_canonical
    recipe (warmup_probe_real.py:203-253) leans on numpy.linalg.slogdet
    + np.cov + np.argsort.  Re-implementing a numerically-safe slogdet
    in pure hexa is out-of-scope for Phase 2 (LU decomposition + sign
    tracking is itself a project).

The hexa side calls this helper as a subprocess: stdin = JSON request,
stdout = JSON response.

The roadmap retires this dependency in Phase 4 by either porting a
minimal slogdet kernel to a hexa-callable C lib, or by fusing this
runner with the Phase 4 native state-vector kernel from aer_runner.py.
See nexus/.roadmap.qmirror cond.4 / phase4.

Contract (stdin -> stdout JSON)
-------------------------------

Input (one JSON object on stdin):
    {
        "mode":          "phi_measure",
        "X":             [[float, ...], ...],   # (N_calib, D) hidden matrix
        "hid_trunc":     <int>,                 # 0 -> use D // 2
        "k_partitions":  <int>,                 # 0 -> use 8
        "ridge":         <float>,               # default 1e-3
        "seed":          <int>                  # default 42
    }

Output (one JSON object on stdout, single line):
    {
        "ok":                1 | 0,
        "phi_min":           <float>,
        "phi_mean":          <float>,
        "partitions_tested": <int>,
        "hid_trunc_used":    <int>,
        "n_calib":           <int>,
        "ridge":             <float>,
        "seed":              <int>,
        "engine":            "numpy" | "none",
        "message":           "<str>"
    }

Algorithm = verbatim port of warmup_probe_real.compute_phi_star (lines
203-253, anima_phi_v3_canonical).
"""

from __future__ import annotations

import json
import sys


def _emit(payload):
    sys.stdout.write(json.dumps(payload, separators=(",", ":")))
    sys.stdout.write("\n")
    sys.stdout.flush()


try:
    import numpy as np
except ImportError as exc:
    print(json.dumps({
        "ok": 0,
        "phi_min": 0.0, "phi_mean": 0.0, "partitions_tested": 0,
        "hid_trunc_used": 0, "n_calib": 0, "ridge": 0.0, "seed": 0,
        "engine": "none",
        "message": "numpy_unavailable: " + str(exc),
    }))
    sys.exit(0)


def _safe_logdet(C, ridge):
    Cs = C + ridge * np.eye(C.shape[0])
    sign, logdet = np.linalg.slogdet(Cs)
    if sign <= 0:
        return None
    return float(logdet)


def _phi_measure(req):
    X_raw = req.get("X") or []
    hid_trunc = int(req.get("hid_trunc", 0))
    k_partitions = int(req.get("k_partitions", 0))
    ridge = float(req.get("ridge", 1e-3))
    seed = int(req.get("seed", 42))

    if not X_raw:
        return {
            "ok": 0,
            "phi_min": 0.0, "phi_mean": 0.0, "partitions_tested": 0,
            "hid_trunc_used": 0, "n_calib": 0, "ridge": ridge, "seed": seed,
            "engine": "numpy",
            "message": "phi_runner: empty X",
        }

    X = np.asarray(X_raw, dtype=float)
    if X.ndim != 2:
        return {
            "ok": 0,
            "phi_min": 0.0, "phi_mean": 0.0, "partitions_tested": 0,
            "hid_trunc_used": 0, "n_calib": 0, "ridge": ridge, "seed": seed,
            "engine": "numpy",
            "message": "phi_runner: X must be 2D, got " + str(X.shape),
        }

    n_calib, d = X.shape
    if n_calib < 2:
        return {
            "ok": 0,
            "phi_min": 0.0, "phi_mean": 0.0, "partitions_tested": 0,
            "hid_trunc_used": 0, "n_calib": n_calib, "ridge": ridge, "seed": seed,
            "engine": "numpy",
            "message": "phi_runner: need n_calib >= 2",
        }

    if hid_trunc <= 0:
        hid_trunc = max(1, d // 2)
    hid_trunc = min(hid_trunc, d)

    if k_partitions <= 0:
        k_partitions = 8

    half = n_calib // 2
    if half < 1:
        return {
            "ok": 0,
            "phi_min": 0.0, "phi_mean": 0.0, "partitions_tested": 0,
            "hid_trunc_used": hid_trunc, "n_calib": n_calib,
            "ridge": ridge, "seed": seed, "engine": "numpy",
            "message": "phi_runner: half-partition is empty",
        }

    var = X.var(axis=0)
    top_idx = np.argsort(var)[::-1][:hid_trunc]
    Xt = X[:, top_idx]

    C_full = np.cov(Xt.T)
    if Xt.shape[1] == 1:
        C_full = np.array([[float(C_full)]])
    I_full = _safe_logdet(C_full, ridge)
    if I_full is None:
        return {
            "ok": 0,
            "phi_min": 0.0, "phi_mean": 0.0, "partitions_tested": 0,
            "hid_trunc_used": hid_trunc, "n_calib": n_calib,
            "ridge": ridge, "seed": seed, "engine": "numpy",
            "message": "phi_runner: I_full slogdet sign <= 0",
        }

    rng = np.random.default_rng(seed)
    phi_candidates = []
    for _k in range(k_partitions):
        idx = rng.permutation(n_calib)
        s1 = idx[:half]
        s2 = idx[half:]
        if len(s1) < 2 or len(s2) < 2:
            continue
        C1 = np.cov(Xt[s1].T)
        C2 = np.cov(Xt[s2].T)
        if Xt.shape[1] == 1:
            C1 = np.array([[float(C1)]])
            C2 = np.array([[float(C2)]])
        I1 = _safe_logdet(C1, ridge)
        I2 = _safe_logdet(C2, ridge)
        if I1 is None or I2 is None:
            continue
        phi_candidates.append(I_full - (I1 + I2))

    if not phi_candidates:
        return {
            "ok": 0,
            "phi_min": 0.0, "phi_mean": 0.0, "partitions_tested": 0,
            "hid_trunc_used": hid_trunc, "n_calib": n_calib,
            "ridge": ridge, "seed": seed, "engine": "numpy",
            "message": "phi_runner: all K partitions failed slogdet",
        }

    phi_min = float(min(phi_candidates))
    phi_mean = float(sum(phi_candidates) / len(phi_candidates))
    return {
        "ok": 1,
        "phi_min": phi_min, "phi_mean": phi_mean,
        "partitions_tested": len(phi_candidates),
        "hid_trunc_used": hid_trunc, "n_calib": n_calib,
        "ridge": ridge, "seed": seed, "engine": "numpy",
        "message": "phi_runner: ok",
    }


def main():
    raw = sys.stdin.read()
    try:
        req = json.loads(raw)
    except Exception as exc:
        _emit({
            "ok": 0,
            "phi_min": 0.0, "phi_mean": 0.0, "partitions_tested": 0,
            "hid_trunc_used": 0, "n_calib": 0, "ridge": 0.0, "seed": 0,
            "engine": "none",
            "message": "phi_runner: bad request json: " + str(exc),
        })
        return

    mode = str(req.get("mode", "phi_measure"))
    try:
        if mode == "phi_measure":
            _emit(_phi_measure(req))
            return
        _emit({
            "ok": 0,
            "phi_min": 0.0, "phi_mean": 0.0, "partitions_tested": 0,
            "hid_trunc_used": 0, "n_calib": 0, "ridge": 0.0, "seed": 0,
            "engine": "none",
            "message": "phi_runner: unknown mode: " + mode,
        })
    except Exception as exc:
        _emit({
            "ok": 0,
            "phi_min": 0.0, "phi_mean": 0.0, "partitions_tested": 0,
            "hid_trunc_used": 0, "n_calib": 0, "ridge": 0.0, "seed": 0,
            "engine": "none",
            "message": "phi_runner: unhandled error: " + repr(exc),
        })


if __name__ == "__main__":
    main()
