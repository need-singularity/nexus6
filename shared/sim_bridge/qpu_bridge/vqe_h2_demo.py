#!/usr/bin/env python3
"""vqe_h2_demo.py — H2 VQE with three noise modes.

Three modes (selected by --mode):
  none    : ideal simulator
  depol   : Qiskit depolarizing noise, p=0.01 on 1q + p=0.01 on 2q gates
  anu     : same *average* Pauli-error rate as depol, but error samples and
            parameter perturbations drawn from ANU QRNG bytes via
            anu_noise_model.hexa. No Qiskit NoiseModel — we inject noise by
            (i) probabilistically applying X/Y/Z after each gate in a
            noisy copy of the ansatz, and (ii) perturbing ansatz params
            each iter with ANU-seeded gaussian.

H2 Hamiltonian (STO-3G, R=0.74 Å, frozen core, parity-mapped to 2 qubits).
Coefficients from  Kandala et al. 2017 (also widely in Qiskit textbooks):
  H = c_0 I + c_1 Z_0 + c_2 Z_1 + c_3 Z_0 Z_1 + c_4 X_0 X_1 + c_5 Y_0 Y_1

  c_0 = -1.0523732,  c_1 = 0.39793742,  c_2 = -0.39793742,
  c_3 = -0.01128010, c_4 = 0.18093119,  c_5 = 0.18093119
  (exact ground-state E0 = -1.9153706, verified numerically from H matrix)

Ansatz: 2-qubit hardware-efficient  R_y(θ0)·R_z(θ1) ⊗ R_y(θ2)·R_z(θ3)
        then CNOT(0,1), then R_y(θ4)·R_z(θ5) ⊗ R_y(θ6)·R_z(θ7).
        θ ∈ R^8.  COBYLA optimizer (gradient-free — finite-diff free).
Measurement: for each Pauli term we rotate + measure in Z-basis,
shots=1024 per iter.

Artifacts: writes one JSON per run to <outdir>/run_<mode>_<seed>.json
with keys: mode, seed, final_energy, n_iters, curve (list of energies),
source ("anu" / "urandom" / "mixed" / "ideal").
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from scipy.optimize import minimize

# ─────────────────────────── constants ────────────────────────────
HOME = os.environ["HOME"]
NEXUS = os.path.join(HOME, "Dev", "nexus")
HEXA_BIN = os.path.join(NEXUS, "shared", "bin", "hexa")
ANU_HEXA = os.path.join(NEXUS, "shared", "sim_bridge", "qpu_bridge", "anu_noise_model.hexa")

# H2 / STO-3G / R=0.74 Hamiltonian (2-qubit parity-mapped)
H2_COEFFS = {
    "I":  -1.0523732,
    "Z0":  0.39793742,
    "Z1": -0.39793742,
    "ZZ": -0.01128010,
    "XX":  0.18093119,
    "YY":  0.18093119,
}
EXACT_E0 = -1.9153706  # numerically diagonalized ground state

# target Pauli error rate (same for depol and anu modes)
P_ERR = 0.01
N_SHOTS = 1024
N_QUBITS = 2
N_PARAMS = 8


# ─────────────────────────── anu bytes ────────────────────────────
class AnuStream:
    """Byte pool fetched from anu_noise_model.hexa.  Feeds floats [0,1).

    Strategy to minimize ANU API consumption:
      • ONE call to anu_noise_model.hexa requesting a small number of
        bytes (n_calls × bpi, capped at 64 by default) — this fits in a
        single ANU 64-byte batch.
      • First 32 of those bytes seed a local Mersenne-Twister RNG via
        numpy.random.default_rng(entropy=bytes), used for the bulk of
        per-gate Pauli error draws.
      • Remaining bytes are consumed directly by .floats() / .gaussian()
        for parameter perturbation (high-value low-volume use).

    This way the randomness PROVENANCE is genuinely ANU (seed is ANU,
    which makes the full MT stream deterministic in ANU) while the
    BYTE-COUNT stays within a single ANU batch.
    """

    def __init__(self, n_calls: int = 1, bytes_per_iter: int = 64, raw_bytes: bytes | None = None):
        self.n_calls = n_calls
        self.bpi = bytes_per_iter
        self.pool: bytearray = bytearray()
        self.source = "unknown"
        if raw_bytes is not None:
            self.pool.extend(raw_bytes)
            self.source = "injected"
        else:
            self._refill(n_calls)
        # seed a deterministic RNG from the first 32 bytes
        seed_bytes = bytes(self.pool[:32]) if len(self.pool) >= 32 else bytes(self.pool) + os.urandom(32 - len(self.pool))
        self._seed_entropy = list(np.frombuffer(seed_bytes, dtype=np.uint32))
        # master seed sequence; per-eval spawn gives independent streams
        self._master_seq = np.random.SeedSequence(self._seed_entropy)
        self._spawn_counter = 0
        self.rng = np.random.default_rng(self._master_seq)
        # retain remaining bytes for parameter perturbation
        self.reserve = bytearray(self.pool[32:])

    def new_eval_rng(self) -> np.random.Generator:
        """Spawn an independent child RNG for a fresh VQE energy eval.

        Each spawn is derived from the original ANU seed (chain-of-custody
        preserved) but produces an independent deterministic stream.
        COBYLA's finite-difference needs independent noise per evaluation
        to avoid coherent drift.
        """
        child = self._master_seq.spawn(1)[0]
        self._spawn_counter += 1
        return np.random.default_rng(child)

    def _refill(self, n_calls: int) -> None:
        # cap request so one ANU 64-byte batch suffices
        total_bytes = min(n_calls * self.bpi, 64)
        cmd = [HEXA_BIN, ANU_HEXA, "1", str(total_bytes)]
        env = dict(os.environ)
        env["HEXA_LOCAL"] = "1"
        try:
            out = subprocess.run(
                cmd, env=env, capture_output=True, text=True, timeout=30
            )
        except subprocess.TimeoutExpired:
            # fallback to urandom — still honest via source label
            self.pool.extend(os.urandom(total_bytes))
            self.source = "urandom"
            return
        stdout = out.stdout
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                if "source=" in line:
                    self.source = line.split("source=", 1)[1].split()[0]
                continue
            try:
                self.pool.extend(bytes.fromhex(line))
            except ValueError:
                continue
        if len(self.pool) < total_bytes:
            self.pool.extend(os.urandom(total_bytes - len(self.pool)))
            if self.source == "anu":
                self.source = "mixed"
            elif self.source == "unknown":
                self.source = "urandom"

    def floats(self, n: int) -> np.ndarray:
        """Uniform [0,1) draws.  Uses ANU-seeded MT (not raw bytes).

        The seed itself came from ANU bytes; the MT output is
        deterministic-in-ANU. This keeps per-gate draws cheap while
        preserving the chain of custody from the ANU API.
        """
        return self.rng.random(n)

    def gaussian(self, n: int, sigma: float = 1.0) -> np.ndarray:
        """Gaussian draws for ansatz-parameter perturbation.

        Consumes the reserve (raw ANU bytes beyond the 32 used to seed
        the MT) via Box-Muller.  Falls back to MT when reserve empty.
        """
        if len(self.reserve) >= n * 2:
            u = np.frombuffer(bytes(self.reserve[:n * 2]), dtype=np.uint8).astype(np.float64) / 256.0
            self.reserve = self.reserve[n * 2:]
            u = np.clip(u, 1e-6, 1.0 - 1e-6)
            m = n
            u1, u2 = u[:m], u[m:]
            r = np.sqrt(-2.0 * np.log(u1))
            z = r * np.cos(2 * np.pi * u2)
            return z * sigma
        return self.rng.normal(0.0, sigma, n)


# ─────────────────────────── ansatz ───────────────────────────────
def ansatz(theta: np.ndarray) -> QuantumCircuit:
    qc = QuantumCircuit(N_QUBITS)
    qc.ry(theta[0], 0); qc.rz(theta[1], 0)
    qc.ry(theta[2], 1); qc.rz(theta[3], 1)
    qc.cx(0, 1)
    qc.ry(theta[4], 0); qc.rz(theta[5], 0)
    qc.ry(theta[6], 1); qc.rz(theta[7], 1)
    return qc


def inject_anu_pauli(qc: QuantumCircuit, rng: np.random.Generator, p_err: float) -> QuantumCircuit:
    """Copy qc and after each gate, with prob p_err apply a random X/Y/Z
    on the affected qubit(s), sampled from an ANU-derived RNG stream."""
    out = QuantumCircuit(N_QUBITS)
    for instr in qc.data:
        gate = instr.operation
        qargs = instr.qubits
        out.append(gate, qargs)
        for q in qargs:
            draw_gate = rng.random()
            if draw_gate < p_err:
                idx = int(rng.random() * 3) % 3
                qidx = qc.find_bit(q).index
                if idx == 0:
                    out.x(qidx)
                elif idx == 1:
                    out.y(qidx)
                else:
                    out.z(qidx)
    return out


# ─────────────────────────── measurement ───────────────────────────
def _counts_to_probs(counts: dict, shots: int) -> dict:
    return {k: v / shots for k, v in counts.items()}


def _expect_z0z1(probs: dict) -> float:
    # Z0 Z1 eigenvalue of |q1 q0> is (-1)^(q0 + q1) because qiskit bitstring
    # is little-endian "q1q0".
    e = 0.0
    for bits, p in probs.items():
        q0 = int(bits[-1]); q1 = int(bits[-2]) if len(bits) > 1 else 0
        e += p * ((-1) ** (q0 ^ q1))  # actually Z0 Z1 = (-1)^(q0 + q1) mod 2
    return e


def _expect_single_z(probs: dict, qubit: int) -> float:
    e = 0.0
    for bits, p in probs.items():
        bit = int(bits[-(qubit + 1)])
        e += p * ((-1) ** bit)
    return e


def energy_h2(
    theta: np.ndarray,
    sim: AerSimulator,
    noise_model: NoiseModel | None = None,
    anu: AnuStream | None = None,
    p_err: float = 0.0,
    shots: int = N_SHOTS,
) -> float:
    """Evaluate <H> on the ansatz.

    If anu supplied and p_err > 0, we inject ANU-sampled Pauli errors
    per gate on a cloned circuit (no Qiskit NoiseModel used).  A fresh
    child RNG is spawned from the ANU seed for each evaluation to avoid
    coherent drift during COBYLA's finite-difference search.
    Otherwise if noise_model is given, Aer handles noise.
    """
    base = ansatz(theta)
    eval_rng = anu.new_eval_rng() if (anu is not None and p_err > 0) else None

    # Number of independent Pauli-error trajectories to sample for anu mode.
    # Each trajectory runs SHOTS_PER_TRAJ shots with a single sampled error
    # pattern.  Total shots kept constant; this approximates averaging over
    # the Pauli channel (matching what Qiskit's NoiseModel does internally
    # for the depol mode).  16 balances variance vs wall time.
    ANU_TRAJECTORIES = 16
    if eval_rng is not None:
        shots_per_traj = max(1, shots // ANU_TRAJECTORIES)
        n_traj = ANU_TRAJECTORIES
    else:
        shots_per_traj = shots
        n_traj = 1

    def _build(prep_rotation):
        """Return a list of circuits, each with a fresh inject_anu_pauli."""
        circs = []
        for _ in range(n_traj):
            c = base.copy()
            if eval_rng is not None:
                c = inject_anu_pauli(c, eval_rng, p_err)
            if prep_rotation == "X":
                c.h(0); c.h(1)
            elif prep_rotation == "Y":
                c.sdg(0); c.h(0); c.sdg(1); c.h(1)
            c.measure_all()
            circs.append(c)
        return circs

    circuits_by_basis = {
        "Z": _build("Z"),
        "X": _build("X"),
        "Y": _build("Y"),
    }

    probs_all = {}
    for name, circs in circuits_by_basis.items():
        # Skip transpile for simple 2-qubit circuits with basic gates;
        # Aer accepts them directly. Transpile is the dominant cost with
        # many trajectories.
        if noise_model is not None:
            result = sim.run(circs, shots=shots_per_traj, noise_model=noise_model).result()
        else:
            result = sim.run(circs, shots=shots_per_traj).result()
        merged = {}
        total_shots = 0
        for i in range(len(circs)):
            counts = result.get_counts(i)
            for k, v in counts.items():
                merged[k] = merged.get(k, 0) + v
            total_shots += shots_per_traj
        probs_all[name] = _counts_to_probs(merged, total_shots)

    e_z0 = _expect_single_z(probs_all["Z"], 0)
    e_z1 = _expect_single_z(probs_all["Z"], 1)
    e_zz = _expect_z0z1(probs_all["Z"])
    e_xx = _expect_z0z1(probs_all["X"])
    e_yy = _expect_z0z1(probs_all["Y"])

    E = (
        H2_COEFFS["I"]
        + H2_COEFFS["Z0"] * e_z0
        + H2_COEFFS["Z1"] * e_z1
        + H2_COEFFS["ZZ"] * e_zz
        + H2_COEFFS["XX"] * e_xx
        + H2_COEFFS["YY"] * e_yy
    )
    return float(E)


# ─────────────────────────── optimizer ─────────────────────────────
def run_vqe(
    mode: str,
    seed: int,
    max_iter: int = 80,
    outdir: Path | None = None,
) -> dict:
    rng = np.random.default_rng(seed)
    theta0 = rng.uniform(-np.pi, np.pi, N_PARAMS)

    # NOTE: we deliberately do NOT pin seed_simulator so that Aer's internal
    # shot/depol sampling produces fresh stochastic draws per eval — this
    # matches what a "real" QPU observes and means depol mode has shot noise
    # comparable to anu mode (otherwise seeded Aer gives zero variance and
    # COBYLA sees a noise-free biased Hamiltonian, which is not the fair
    # comparison the task asks for).  Reproducibility is still controlled at
    # the ANU/theta-init level via `seed`.
    sim = AerSimulator()
    noise_model = None
    anu = None
    source = "ideal"

    if mode == "depol":
        noise_model = NoiseModel()
        e1 = depolarizing_error(P_ERR, 1)
        e2 = depolarizing_error(P_ERR, 2)
        noise_model.add_all_qubit_quantum_error(e1, ["ry", "rz", "h", "sdg", "x", "y", "z"])
        noise_model.add_all_qubit_quantum_error(e2, ["cx"])
        source = "depol"
    elif mode == "anu":
        # Single 64-byte ANU fetch.  32 bytes seed the MT used for per-gate
        # Pauli-error draws (matching depol mode's average error rate).  The
        # remaining 32 bytes seed a separate stream available for the
        # initial-theta perturbation (intentionally disabled here so the
        # comparison isolates NOISE-MODEL effects, not initial-condition
        # effects — theta0 comes from the same seeded numpy.default_rng as
        # mode=none/depol).
        anu = AnuStream(n_calls=1, bytes_per_iter=64)
        source = anu.source
    elif mode == "none":
        source = "ideal"
    else:
        raise ValueError(f"unknown mode {mode!r}")

    curve: List[float] = []
    t0 = time.time()

    def objective(th: np.ndarray) -> float:
        E = energy_h2(th, sim, noise_model=noise_model, anu=anu, p_err=P_ERR if mode == "anu" else 0.0)
        curve.append(E)
        return E

    result = minimize(
        objective,
        theta0,
        method="COBYLA",
        options={"maxiter": max_iter, "rhobeg": 0.5, "disp": False, "catol": 1e-4},
    )

    elapsed = time.time() - t0
    final_energy = float(result.fun)
    n_iters = int(result.nfev)
    rec = {
        "mode": mode,
        "seed": int(seed),
        "final_energy": final_energy,
        "n_iters": n_iters,
        "error_vs_exact": final_energy - EXACT_E0,
        "elapsed_sec": round(elapsed, 2),
        "curve": [round(v, 6) for v in curve],
        "source": source,
        "shots": N_SHOTS,
        "max_iter": max_iter,
        "p_err": P_ERR if mode != "none" else 0.0,
    }
    if outdir is not None:
        outdir.mkdir(parents=True, exist_ok=True)
        path = outdir / f"run_{mode}_{seed}.json"
        path.write_text(json.dumps(rec, indent=2))
        rec["_path"] = str(path)
    return rec


# ─────────────────────────── cli ───────────────────────────────────
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["none", "depol", "anu"], required=True)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--max-iter", type=int, default=80)
    p.add_argument("--outdir", default=str(Path(__file__).resolve().parent / "runs"))
    args = p.parse_args()

    rec = run_vqe(
        mode=args.mode,
        seed=args.seed,
        max_iter=args.max_iter,
        outdir=Path(args.outdir),
    )
    # print a one-line summary then full JSON
    print(
        f"[vqe] mode={rec['mode']} seed={rec['seed']} "
        f"final_E={rec['final_energy']:+.6f} "
        f"err_vs_exact={rec['error_vs_exact']:+.6f} "
        f"nfev={rec['n_iters']} source={rec['source']} "
        f"elapsed={rec['elapsed_sec']}s"
    )
    print(json.dumps({k: v for k, v in rec.items() if k != "curve"}, indent=2))


if __name__ == "__main__":
    main()
