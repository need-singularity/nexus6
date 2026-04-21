# rng_lab — findings log

## Setup

- hexa-lang binary: `$HEXA_LANG/hexa`
- Python helper: `/usr/bin/python3` (chi2 reducer at `/tmp/rng_lab_chi2.py`, auto-regenerated)
- Sources: ANU QRNG REST (`https://qrng.anu.edu.au/API/jsonI.php`), `/dev/urandom`, software LCG (glibc-style, s = 1103515245·s + 12345 mod 2^31, emit bits 16..23)
- Cache: `.anu_cache.bin` (TTL 60 s, matches ANU rate limit)
- Chi² thresholds (df=255): PASS < 293, WEAK 293..330, FAIL ≥ 330

## Results

### 2026-04-11 first runs (macOS darwin 24.6, N=4096 and N=16384)

| date       | N     | urandom chi² | anu chi² | lcg chi² | notes |
|------------|-------|--------------|----------|----------|-------|
| 2026-04-11 | 4096  | 230.75       | 258.62   | 0.00     | NR-LCG period artifact on low byte (dropped) |
| 2026-04-11 | 4096  | 239.50       | 287.88   | 243.25   | after switching to glibc-LCG high byte — all PASS |
| 2026-04-11 | 16384 | 214.09       | 264.75   | 235.16   | all PASS, converging toward ~255 (ideal) |

ANU REST returned rate-limit text ("limited to 1 requests per minute") on every probe during testing → fetch_anu.hexa correctly fell back to /dev/urandom; ANU row above is effectively urandom-extended (honest Phase 0 limit).

## Next

- Phase 0.1: add runs test (monobit + bit-transition) to catch LCG bias chi² misses
- Phase 0.2: swap the "weak" baseline to ANSI C `rand()` low byte to actually FAIL the test and validate the pipeline's detection
- Phase 0.3: when ANU is reachable, fetch 1024 bytes over 16 minutes and compare *real* ANU chi² vs urandom
- Phase 1: integrate entropy source choice into `shared/blowup/seed/seed_engine.hexa` (not yet — requires L0 approval)
- Phase 2: investigate paid `quantumnumbers.anu.edu.au` or local hardware RNG (RDRAND via `/usr/bin/python3 -c 'import secrets'` is NOT RDRAND on macOS arm64 — needs a C shim)
