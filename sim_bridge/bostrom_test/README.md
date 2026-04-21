# bostrom_test — Simulation hypothesis PRNG signature test

**Concept**: If we live inside a simulation, the sim-author's PRNG might masquerade as our "quantum RNG". Test: compare long ANU QRNG streams against known PRNG signatures.

## Modules

| file | role |
|------|------|
| `anu_collector.hexa` | ANU QRNG fetcher, 1 req/min compliant, urandom fallback |
| `prng_oracle.py` | Reference PRNG implementations: MT19937, glibc LCG, Xorshift 32/64, PCG-32, ChaCha20, urandom, rdrand-proxy |
| `signature_compare.py` | Metrics: chi2, gzip ratio, serial correlation, byte-histogram L2, FFT L2, k-byte overlap, seed brute-force (1024 seeds × MT/LCG/Xorshift) |
| `analyze.py` | Consolidate → summary.md with verdict |
| `runner.sh` | Full pipeline |

## Run

```bash
cd $NEXUS_ROOT
./shared/sim_bridge/bostrom_test/runner.sh 30 my_run
```

Output → `runs/my_run/`:
- `anu_stream.bin` — raw ANU bytes
- `anu_stream.hex` + `.meta.jsonl` — per-request provenance
- `prng_compares.csv` — full metric table
- `prng_compares.json` — same, structured
- `summary.md` — final verdict

## Verdict rubric

- **NULL**: ANU chi2 p ∈ [0.01, 0.99], all PRNG overlap within expected random bounds, no seed brute-force hit above chance.  → Bostrom *weak* falsification + ANU calibration PASS.
- **HIT**: any metric shows anomalous alignment with a specific PRNG (brute-force ratio > 10× expected OR overlap > 50× expected OR chi2 fail).  → DISCOVERY-grade, cite PRNG name + metric + statistical significance.

## Constraints

- ANU rate limit: 1 req/min strict (65s gap used).
- 30 req × 64 bytes = 1920 bytes ≈ 30 min collection.
- Analysis (brute force 1024 seeds × 3 PRNGs × n bytes): ~5 min.
- Total budget: 40 min wall-clock.

## Limitations (honest)

- Seed brute-force covers only 1024 seeds (vs 2^32 space) — false-negative possible.
- FFT is O(N^2) naive DFT, first 256 samples only.
- ChaCha20 and rdrand: key/seed space effectively unreachable by brute force.
- chi2 p-value uses Wilson-Hilferty approximation (no scipy).
