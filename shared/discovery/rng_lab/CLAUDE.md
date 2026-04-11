# rng_lab — Phase 0 PoC (NEXUS-6 mini-quantum RNG track)

Purpose: baseline multi-source RNG comparison (ANU QRNG + /dev/urandom + weak LCG) via chi-squared frequency test. Phase 0 is free/non-hardware; real QRNG hardware arrives in later phases.

Usage: `hexa fetch_anu.hexa [info|raw]` fetches 64 ANU bytes (cached 60s, urandom fallback). `hexa bench_chi2.hexa [--n N]` prints TSV with chi2 + PASS/WEAK/FAIL verdict per source (df=255, N≥2560).

Limits: no native HTTP in hexa-lang (curl shell-out). No true QRNG beyond ANU REST, which is rate-limited to 1 req/min and caps at 64 bytes/request — for N>64 the ANU row is ANU-seeded + /dev/urandom-extended (honest label). PoC only, no cryptographic claim; LCG uses bits 16..23 of glibc-style params because NR low-byte has period artifact chi2=0 at N=4096.
