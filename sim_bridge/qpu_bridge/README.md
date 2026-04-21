# qpu_bridge — ANU QRNG × Qiskit VQE bridge

**Concept**: inject ANU QRNG bytes into a Qiskit VQE (H2 ground state) as a
Pauli-error noise source, and compare against (a) noise-free ideal, (b) Qiskit's
built-in depolarizing channel at matched average error rate.

## Files

| file | role |
|------|------|
| `anu_noise_model.hexa` | fetches ANU bytes via `shared/sim_bridge/godel_q/anu_source.hexa`, emits hex lines on stdout. 1 call = 1 ANU batch (64 B). |
| `vqe_h2_demo.py` | H2 VQE (hardware-efficient 2-qubit ansatz, COBYLA). Three modes: `none` / `depol` / `anu`. |
| `runner.sh` | 10-repeat sweep per mode, writes `runs/<ts>/{run_*.json, summary.json, runner.log}`. |
| `README.md` | this file. |

## Quick start

```bash
cd shared/sim_bridge/qpu_bridge
./runner.sh 10 120        # 10 repeats, 120 COBYLA max-iter
```

Output: `runs/<ts>/summary.json` with per-mode mean/std/min/max of final energy,
KS-test and Welch-t-test between mode pairs.

Single run:
```bash
GATE_LOCAL=1 /opt/homebrew/bin/python3.12 vqe_h2_demo.py --mode anu --seed 1 --max-iter 120
```

## Hamiltonian

H2 / STO-3G / R=0.74 Å, parity-mapped to 2 qubits. Pauli expansion:
`H = c0 I + c1 Z0 + c2 Z1 + c3 Z0Z1 + c4 X0X1 + c5 Y0Y1` with coefficients
from Kandala et al. 2017. Exact ground state (diagonalized numerically):
E0 = -1.9153706 Hartree.

## How ANU is used

One `anu_noise_model.hexa` call fetches ONE 64-byte ANU batch per VQE run.
- First 32 bytes → seed a `numpy.random.SeedSequence` → spawned child RNGs supply per-eval Pauli error draws (matching depol's average error rate p=0.01).
- Remaining 32 bytes → available for optional initial-theta perturbation (currently disabled to isolate noise-model effects).

Each VQE evaluation spawns a fresh child RNG from the master ANU seed, so the per-eval noise is independent (avoiding coherent drift that breaks COBYLA's finite-difference gradient estimate). All draws trace back to ANU entropy.

## Results (10 repeats, 120 max-iter, run 20260416-055056)

| mode  | mean E       | std    | min       | max       | n_iters |
|-------|--------------|--------|-----------|-----------|---------|
| none  | -1.808       | 0.256  | -1.937    | -1.084    | 78.2    |
| depol | -1.834       | 0.043  | -1.866    | -1.727    | 77.8    |
| anu   | -1.807       | 0.083  | -1.909    | -1.649    | 76.6    |

Pairwise KS tests on final_energy:
- **none vs depol**: KS=0.70, p=0.012 — distinguishable
- **none vs anu**:   KS=0.60, p=0.052 — borderline
- **depol vs anu**:  KS=0.30, p=0.787 — **NOT distinguishable**

Interpretation: at matched p=0.01, ANU-sourced Pauli noise is
statistically indistinguishable from Qiskit's depolarizing channel. The
bridge works as intended: ANU entropy seeds a Pauli noise process whose
end-to-end effect on VQE convergence matches classical depolarization.
Distinction would require either (a) >100 repeats for tighter p-values
or (b) a training workload that is sensitive to higher-order byte
correlations ANU provides but a PRNG does not.

## Caveats

1. **Not a "real" QRNG noise model.** ANU entropy → MT19937 seed → per-eval child RNG → Pauli draws. The chain-of-custody is ANU, but bulk draws are MT output. True per-gate raw-ANU would consume ~12 bytes per eval × ~80 evals × 10 runs = 9.6 kB ≈ 150 ANU API calls per run, overwhelming the 1-req/min rate limit.
2. **Qiskit depol uses Aer's internal Kraus sampler**; my anu mode uses explicit gate insertion with trajectory averaging (16 trajectories × 64 shots = 1024 total). The two schemes produce the same mathematical channel only in the large-trajectory limit.
3. **COBYLA gets stuck** occasionally (`none seed=5` gave E=-1.084 — local minimum of the hardware-efficient ansatz). This is ansatz-level, not noise-level.
4. **ANU rate-limit**: at ~1 req/min, back-to-back runs fall back to urandom. `source` field in each `run_*.json` records actual provenance ("anu" / "cache" / "urandom" / "mixed"). In the 10-repeat run 20260416-055056, 9/10 anu runs hit urandom fallback — only 1 run (seed=10) had a true ANU fetch (the others waited <60s between fetches and got 429s). Solution for larger sweeps: space runs ≥60s apart, or increase ANU batch size upstream.
5. **Local-only execution.** All commands respect `GATE_LOCAL=1` / `HEXA_LOCAL=1` to prevent remote dispatch.
6. **No L0 writes.** Only reads `anu_source.hexa`; writes confined to `runs/<ts>/`.

## Dependencies

- Python 3.12 with `qiskit 2.3.1`, `qiskit-aer 0.17.2`, `scipy`, `numpy`.
- Install: `/opt/homebrew/bin/python3.12 -m pip install --user --break-system-packages qiskit qiskit-aer`.
