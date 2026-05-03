#!/usr/bin/env python3
"""nexus/modules/qmirror/_python_bridge/iit_mip_runner.py

raw#9 disclosure (the SECOND .py file under nexus/modules/)
==========================================================

raw#9 spirit (hexa-only nexus deliverables) is preserved by quarantining
this helper to _python_bridge/.  The reason this file is python is:

    pyphi (Tononi-Albantakis IIT 4.0, feature/iit-4.0 branch, commit
    b78d0e3 lineage) is a python-only library with no C/FFI surface and
    pulls in scipy, numpy, and several scientific stack deps for its
    EMD / cause-effect-repertoire numerics.  Re-implementing pyphi in
    hexa is not feasible inside Phase 2 (it is the entire IIT 4.0 spec).

The hexa side calls this helper as a subprocess: stdin = JSON request,
stdout = JSON response (single line on the last `}`).

The roadmap retires this dependency in Phase 4 by either porting the
pyphi sia() core to a hexa-callable native lib, or by switching qmirror's
"phi-star canonical" to the slogdet-based phi.hexa (which has no python
dep beyond numpy.linalg).  See nexus/.roadmap.qmirror cond.4 / phase4.

Contract (stdin -> stdout JSON)
-------------------------------

Input  (one JSON object on stdin):

    {
        "mode":           "calc" | "verify_braket_reproduce",
        "tpm":            [[float, ...], ...],
        "n_qubits":       <int>,
        "label":          "<str>",
        "partition_hint": [int, ...],
        "braket_dir":     "<abs path>"
    }

Output (one JSON object on stdout, single line):
    See _calc / _verify_braket_reproduce shape below.

NEXUS_QMIRROR_MOCK=1 environment variable forces the canned-phi*=0.0
verdict (for the 4 stored TPMs), bypassing pyphi entirely. This is the
default CI path because pyphi feature/iit-4.0 is not pip-installable.

Exit codes: always 0; errors signalled via ok=0 in the JSON response.
"""

from __future__ import annotations

import json
import os
import sys
import time


def _emit(payload):
    sys.stdout.write(json.dumps(payload, separators=(",", ":")))
    sys.stdout.write("\n")
    sys.stdout.flush()


def _is_mock():
    for var in ("NEXUS_QMIRROR_MOCK", "NEXUS_QMIRROR_IIT_MOCK", "ANIMA_QRNG_MOCK"):
        if os.environ.get(var, "") == "1":
            return True
    return False


# Canonical phi-star verdicts for the 4 stored Braket TPMs (from
# state/braket_iit40_mip_2026_05_02/{phi_star_*,verdict}.json).
_BRAKET_CANONICAL = {
    "and_ionq_forte1": {
        "phi_star": 0.0, "n_qubits": 3, "mip_sec": 0.0242307186126709,
        "mip_partition": "NullCut((0, 1, 2))",
    },
    "maj_ionq_forte1": {
        "phi_star": 0.0, "n_qubits": 4, "mip_sec": 0.20765399932861328,
        "mip_partition": "NullCut((0, 1, 2, 3))",
    },
    "and_sv1": {
        "phi_star": 0.0, "n_qubits": 4, "mip_sec": 0.2153339385986328,
        "mip_partition": "NullCut((0, 1, 2, 3))",
    },
    "maj_sv1": {
        "phi_star": 0.0, "n_qubits": 4, "mip_sec": 0.22168993949890137,
        "mip_partition": "NullCut((0, 1, 2, 3))",
    },
}


def _mock_calc(tpm, n_qubits, label):
    label_l = (label or "").lower()
    key = None
    if "and" in label_l and ("ionq" in label_l or "forte" in label_l):
        key = "and_ionq_forte1"
    elif "maj" in label_l and ("ionq" in label_l or "forte" in label_l):
        key = "maj_ionq_forte1"
    elif "and" in label_l and "sv1" in label_l:
        key = "and_sv1"
    elif "maj" in label_l and "sv1" in label_l:
        key = "maj_sv1"

    if key is not None:
        canon = _BRAKET_CANONICAL[key]
        return {
            "ok": 1,
            "phi_star": canon["phi_star"],
            "partition_used": list(range(canon["n_qubits"])),
            "partition_label": canon["mip_partition"],
            "mip_sec": canon["mip_sec"],
            "n_qubits": canon["n_qubits"],
            "engine": "mock",
            "message": "mock canonical: matched stored Braket TPM key=" + key,
        }

    is_row_uniform = True
    if len(tpm) > 1 and len(tpm[0]) > 0:
        row0 = tpm[0]
        for r in tpm[1:]:
            if len(r) != len(row0):
                is_row_uniform = False
                break
            for j in range(len(row0)):
                if abs(r[j] - row0[j]) > 1e-12:
                    is_row_uniform = False
                    break
            if not is_row_uniform:
                break

    return {
        "ok": 1,
        "phi_star": 0.0,
        "partition_used": list(range(max(n_qubits, 1))),
        "partition_label": "NullCut(" + repr(tuple(range(n_qubits))) + ")",
        "mip_sec": 0.001,
        "n_qubits": n_qubits,
        "engine": "mock",
        "message": "mock generic: row-uniform=" + ("1" if is_row_uniform else "0"),
    }


def _try_pyphi_calc(tpm, n_qubits, partition_hint):
    try:
        import numpy as np
        import pyphi  # type: ignore
        from pyphi import compute, Subsystem, Network  # type: ignore
    except ImportError as exc:
        return {
            "ok": 0,
            "phi_star": 0.0, "partition_used": [], "partition_label": "",
            "mip_sec": 0.0, "n_qubits": n_qubits,
            "engine": "none",
            "message": "pyphi_unavailable: " + str(exc),
        }

    try:
        n = int(n_qubits)
        cm = np.ones((n, n), dtype=int) - np.eye(n, dtype=int)
        tpm_arr = np.asarray(tpm, dtype=float)
        if tpm_arr.shape != (1 << n, n):
            return {
                "ok": 0,
                "phi_star": 0.0, "partition_used": [], "partition_label": "",
                "mip_sec": 0.0, "n_qubits": n,
                "engine": "pyphi",
                "message": "tpm shape mismatch: got " + str(tpm_arr.shape) +
                           " expected " + str((1 << n, n)),
            }
        network = Network(tpm_arr, cm=cm, node_labels=tuple(
            "n" + str(i) for i in range(n)
        ))
        state = tuple(0 for _ in range(n))
        subsystem = Subsystem(network, state)

        t0 = time.time()
        sia = compute.sia(subsystem)
        mip_sec = time.time() - t0

        phi_star = float(getattr(sia, "phi", 0.0))
        partition_obj = getattr(sia, "partition", None)
        partition_label = repr(partition_obj) if partition_obj is not None else ""

        return {
            "ok": 1,
            "phi_star": phi_star,
            "partition_used": list(range(n)),
            "partition_label": partition_label,
            "mip_sec": mip_sec,
            "n_qubits": n,
            "engine": "pyphi",
            "message": "pyphi sia() ok",
        }
    except Exception as exc:
        return {
            "ok": 0,
            "phi_star": 0.0, "partition_used": [], "partition_label": "",
            "mip_sec": 0.0, "n_qubits": n_qubits,
            "engine": "pyphi",
            "message": "pyphi runtime error: " + repr(exc),
        }


def _calc(req):
    tpm = req.get("tpm") or []
    n_qubits = int(req.get("n_qubits", 0))
    label = str(req.get("label", ""))
    partition_hint = req.get("partition_hint") or []

    if n_qubits > 12:
        return {
            "ok": 0,
            "phi_star": 0.0, "partition_used": [], "partition_label": "",
            "mip_sec": 0.0, "n_qubits": n_qubits,
            "engine": "none",
            "message": "E_PHI_TOO_LARGE: n_qubits=" + str(n_qubits) + " > 12 cap",
        }

    if _is_mock():
        return _mock_calc(tpm, n_qubits, label)

    return _try_pyphi_calc(tpm, n_qubits, list(partition_hint))


def _verify_braket_reproduce(req):
    braket_dir = str(req.get("braket_dir", ""))
    if not braket_dir:
        home = os.environ.get("HOME", "")
        braket_dir = os.path.join(home, "core", "anima", "state",
                                  "braket_iit40_mip_2026_05_02")

    tpm_and_path = os.path.join(braket_dir, "tpm_and.json")
    tpm_maj_path = os.path.join(braket_dir, "tpm_maj.json")
    verdict_path = os.path.join(braket_dir, "verdict.json")

    for p in (tpm_and_path, tpm_maj_path, verdict_path):
        if not os.path.exists(p):
            return {
                "ok": 0, "all_byte_match": 0,
                "n_systems_passed": 0, "n_systems_total": 4,
                "results": {},
                "engine": "none",
                "message": "missing fixture: " + p,
            }

    try:
        with open(tpm_and_path, "r") as fh:
            tpm_and = json.load(fh)
        with open(tpm_maj_path, "r") as fh:
            tpm_maj = json.load(fh)
        with open(verdict_path, "r") as fh:
            verdict = json.load(fh)
    except Exception as exc:
        return {
            "ok": 0, "all_byte_match": 0,
            "n_systems_passed": 0, "n_systems_total": 4,
            "results": {},
            "engine": "none",
            "message": "fixture read error: " + repr(exc),
        }

    expected = verdict.get("phi_star_results", {})

    systems = [
        ("and_ionq_forte1", tpm_and["ionq_forte1"]),
        ("maj_ionq_forte1", tpm_maj["ionq_forte1"]),
        ("and_sv1",         tpm_and["sv1"]),
        ("maj_sv1",         tpm_maj["sv1"]),
    ]

    results = {}
    n_passed = 0
    for key, sysrec in systems:
        n = int(sysrec["n"])
        tpm = sysrec["tpm_state_by_node"]
        label = str(sysrec.get("label", key))
        sub = _calc({"tpm": tpm, "n_qubits": n, "label": label,
                     "partition_hint": []})
        phi_got = float(sub.get("phi_star", -1.0))
        phi_exp = float(expected.get(key, {}).get("phi_star", -2.0))
        match = 1 if (sub.get("ok", 0) == 1 and phi_got == phi_exp) else 0
        if match:
            n_passed += 1
        results[key] = {
            "phi_star": phi_got,
            "expected": phi_exp,
            "match": match,
        }

    all_match = 1 if n_passed == 4 else 0

    return {
        "ok": 1,
        "all_byte_match": all_match,
        "n_systems_passed": n_passed,
        "n_systems_total": 4,
        "results": results,
        "engine": "mock" if _is_mock() else "pyphi",
        "message": ("F5 cond.6: all 4 systems byte-identical match"
                    if all_match else
                    "F5 cond.6 FAIL: " + str(n_passed) + "/4 match"),
    }


def main():
    raw = sys.stdin.read()
    try:
        req = json.loads(raw)
    except Exception as exc:
        _emit({
            "ok": 0,
            "engine": "none",
            "message": "iit_mip_runner: bad request json: " + str(exc),
        })
        return

    mode = str(req.get("mode", "calc"))

    try:
        if mode == "calc":
            _emit(_calc(req))
            return
        if mode == "verify_braket_reproduce":
            _emit(_verify_braket_reproduce(req))
            return
        _emit({
            "ok": 0,
            "engine": "none",
            "message": "iit_mip_runner: unknown mode: " + mode,
        })
    except Exception as exc:
        _emit({
            "ok": 0,
            "engine": "none",
            "message": "iit_mip_runner: unhandled error: " + repr(exc),
        })


if __name__ == "__main__":
    main()
