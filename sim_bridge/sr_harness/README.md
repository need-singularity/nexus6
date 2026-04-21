# sr_harness — Stochastic Resonance noise-floor library

Reusable pure-hexa helpers to inject calibrated Gaussian noise into arbitrary
convergence metrics across nexus engines (blowup / anima / growth / n6-calc).

**Status: pre-confirmation. Keep `NEXUS_SR=0` (default) until the σ≈0.1
stochastic-resonance result in variance_sweep is independently replicated.**

## Evidence basis

- `shared/sim_bridge/ouroboros_qrng/variance_sweep/summary.md`
  - σ=0.1 peaks conv_rate at **0.25** vs baseline **0.10** (2.4× lift)
  - n=20 pooled trials, pooled p ≈ 0.022
  - non-monotonic curve with interior peak → classical SR signature
- Not yet independently replicated. Treat as provisional.

## Files

| file | role |
|------|------|
| `sr_inject.hexa`          | core library — `add_sr_noise`, `is_sr_enabled`, `WrappedMetric` |
| `sr_registry.hexa`        | JSONL registry of injection sites (planned/stub/active/confirmed) |
| `demo_ouroboros_sr.hexa`  | σ=0 vs σ=0.1 reproduction demo (n=20 trials, 6 gens) |
| `integration_stub.md`     | survey of 9 candidate injection points, no edits applied |
| `sr_registry.jsonl`       | registry log (created on first `register` call) |
| `README.md`               | this file |

## Quick use

```bash
# self-test (10 Box-Muller samples at σ=0.1)
hexa shared/sim_bridge/sr_harness/sr_inject.hexa self-test

# verify statistics (mean ~0, sd ~σ)
hexa shared/sim_bridge/sr_harness/sr_inject.hexa stats 0.1 10000

# baseline demo (σ=0 vs σ=0.1, 20 trials each, ~30s)
hexa shared/sim_bridge/sr_harness/demo_ouroboros_sr.hexa run 20 6

# env gate check
hexa shared/sim_bridge/sr_harness/sr_inject.hexa enabled       # -> false
NEXUS_SR=1 hexa shared/sim_bridge/sr_harness/sr_inject.hexa enabled   # -> true

# register a planned injection site
hexa shared/sim_bridge/sr_harness/sr_registry.hexa register \
  blowup ouroboros_composite 0.1 7919 \
  shared/blowup/ouroboros/ouroboros_meta.hexa 309 planned
```

## Library API (`sr_inject.hexa`)

```hexa
// additive Gaussian noise — deterministic in (sigma, seed)
fn add_sr_noise(value: float, sigma: float, seed: int) -> float

// env-gated variant — passthrough unless NEXUS_SR=1
fn add_sr_noise_gated(value: float, sigma: float, seed: int) -> float

// clamped (probability-like metrics)
fn add_sr_noise_clamped(value: float, sigma: float, seed: int,
                        lo: float, hi: float) -> float

// env check
fn is_sr_enabled() -> bool

// struct wrapper (hexa stage0 fn-value workaround)
struct WrappedMetric { name: string, sigma: float, base_seed: int, gated: bool }
fn make_wrapped_metric(name: string, sigma: float, base_seed: int) -> WrappedMetric
fn call_wrapped_scalar(w: WrappedMetric, raw: float, seed_offset: int) -> float
```

Box-Muller details: `z = sqrt(-2 ln u1) * cos(2π u2)` with:
- `u1, u2` from an independent LCG (`sr_prng_b`) seeded by `seed*7+11`, `seed*13+29`
- cos via 6-term Taylor polynomial, ln via truncated Mercator series

Math is verbatim with `shared/sim_bridge/ouroboros_qrng/variance_sweep/sweep_runner.hexa`
so σ=0 reproduces the deterministic baseline bit-identically.

## Environment

| var | default | effect |
|-----|---------|--------|
| `NEXUS_SR` | unset / "0" | no-op — all gated calls return value verbatim |
| `NEXUS_SR=1` | (set) | active — Box-Muller noise injected per call |

Accepted true values: `1`, `true`, `TRUE`, `yes`, `on`.

## SR-confirmation checklist

Flip `NEXUS_SR=1` by default only after **all** of:

- [ ] variance_sweep replication run (≥ n=100 trials/σ) shows conv_rate(σ=0.1)
      ≥ 2× baseline with bootstrap 95% CI not crossing 1.0
- [ ] at least 2 independent domains (e.g. blowup + growth) show non-negative
      delta under SR, no regressions
- [ ] σ-curve tails (σ=0.5, σ=1.0) stay below baseline — confirms interior
      peak, rules out monotonic bias
- [ ] registry has ≥ 3 `active` entries with 48h+ soak telemetry
- [ ] p-value < 0.01 (Bonferroni-corrected) on pooled conv_rate delta
- [ ] atlas.n6 `n6-sr-confirmed` node registered with evidence payload
- [ ] CLAUDE.md / project_config update flipping `NEXUS_SR=1` default

Until then: **gated no-op**. Keep the library; keep it dark.

## Safety

- No writes outside `shared/sim_bridge/sr_harness/sr_registry.jsonl`.
- Zero L0 modifications. Zero atlas.n6 writes. Zero external deps.
- `is_sr_enabled()` reads `NEXUS_SR` — one `exec("printenv ...")` per call.
  For hot paths, cache the result in a let binding at engine load.

## Parent

`../CLAUDE.md` → "sim_bridge"
