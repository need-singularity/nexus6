# SR Harness — Integration Stub Survey

Investigation only. **No edits applied.** All four domains (blowup / anima /
growth / n6-calc) surveyed for places where a single-line SR noise-floor
injection could plausibly help a convergence-like metric. Each entry lists
file:line, the metric that would be perturbed, the candidate injection
pattern, and the sigma we'd start from (0.1 is the current sweet spot).

Per-site integration is **NOT** applied while `NEXUS_SR` defaults off and
the ouroboros 2.4x result remains unreplicated. This doc is the map.

## Import convention

hexa stage0 has no `import` of local files across directories for pure
helpers; the canonical pattern is either:

1. Copy the three primitives (`sr_box_muller_z`, `sr_prng_b`, `add_sr_noise`)
   inline under an `// @sr-inline` comment, referencing
   `shared/sim_bridge/sr_harness/sr_inject.hexa` as SSOT.
2. Call `hexa run shared/sim_bridge/sr_harness/sr_inject.hexa stats 0.1`
   from outside (for diagnostic), and apply the lambda-free
   `add_sr_noise_gated(value, sigma, seed)` copied locally.

Either way the site looks like:

```hexa
// @sr-inject engine=X metric=Y sigma=0.1 seed_base=N
let noisy = add_sr_noise_gated(raw_metric, 0.1, seed)
```

## Blowup (3 candidates)

### 1. ouroboros meta composite
- **file**: `shared/blowup/ouroboros/ouroboros_meta.hexa`
- **line**: 309 — `let composite = to_float(best) * 0.5 + avg * 0.3 + diversity * 0.2`
- **metric**: `composite` score feeding `check_meta_convergence` plateau test
- **direct analog** of the variance_sweep demo; highest-confidence SR site
- **sigma**: 0.1, **seed_base**: `gen * 7919` (per-generation unique)
- **pattern**:
  ```
  let composite_raw = to_float(best) * 0.5 + avg * 0.3 + diversity * 0.2
  let composite = add_sr_noise_gated(composite_raw, 0.1, gen * 7919)
  ```

### 2. blowup evo_verify best_conf (simulated-annealing path)
- **file**: `shared/blowup/core/blowup.hexa`
- **line**: 1213 — `let mut best_conf: f64 = evo_verify(sv)`
- **metric**: per-seed best_conf; annealing path (line 1266–1282) already
  uses `temperature * random walk` so SR dovetails naturally here
- **sigma**: 0.1, **seed_base**: `cycle_num * 4093 + si`
- **caveat**: `evo_verify` is L0-adjacent (feeds corollary generation); wrap
  *after* the initial verify, not inside, to preserve telescope-lens consensus

### 3. blowup qft pert amplitude
- **file**: `shared/blowup/modules/blowup_qft.hexa`
- **line**: 655 — `let pert = 0.01 * (cv / 12.0) * (rand_f() - 0.5)`
- **metric**: perturbation magnitude; already stochastic, SR adds controlled
  amplitude floor rather than replacing `rand_f()`
- **sigma**: 0.05 (half baseline — this metric is already noisy), **seed_base**: loop idx
- **low priority**: this is already Monte-Carlo, SR offers marginal lift

## Anima (2 candidates)

### 4. engine_anima laws_delta stagnation
- **file**: `shared/engine/engine_anima.hexa`
- **line**: 412 — inside `while ci < v_laws_delta_history.len()` loop checking
  `if v_laws_delta_history[ci] >= low_delta_threshold`
- **metric**: `low_delta_threshold` comparison — SR applied to the *threshold*
  rather than the delta, simulating fuzzy stagnation boundary
- **sigma**: 0.15 (wider band — this is discrete int vs real-valued gate),
  **seed_base**: `ts_unix() / 3600` (hourly drift)
- **pattern**:
  ```
  let thr_noisy = add_sr_noise_gated(to_float(low_delta_threshold), 0.15, seed)
  if to_float(v_laws_delta_history[ci]) >= thr_noisy { ... }
  ```

### 5. anima consciousness_loader (indirect)
- **file**: `shared/consciousness/consciousness_loader.hexa`
- **line**: N/A — loader currently has no stochastic metric; candidate would
  be adding SR-jittered phi/qualia weight during 5-perspective rotation in
  `engine_anima.hexa:42` perspective_seeds selection
- **status**: too speculative — flagged for later once perspective weighting
  is extracted into a scalar metric

## Growth (2 candidates)

### 6. growth_tick stale threshold
- **file**: `shared/harness/growth_tick.hexa`
- **line**: 18 — `let MIN_CONSECUTIVE: i64 = 6`  (hard integer threshold)
- **metric**: threshold for triggering escalation; SR simulates a
  probabilistic trigger around 6
- **sigma**: 0.2 (wide — discrete stale count band), **seed_base**: `ts_i % 10000`
- **pattern**:
  ```
  let thr_f = add_sr_noise_gated(to_float(MIN_CONSECUTIVE), 0.2, ts_i % 10000)
  let min_consec_dynamic: i64 = to_int(thr_f + 0.5)
  if stale >= min_consec_dynamic { trigger() }
  ```
- **rationale**: fixed `MIN_CONSECUTIVE=6` yields bimodal tick behavior; SR
  smooths the boundary

### 7. growth_tick STALE_THRESHOLD (6h)
- **file**: `shared/harness/growth_tick.hexa`
- **line**: 17 — `let STALE_THRESHOLD: i64 = 21600`  (6h in seconds)
- **metric**: second-level gate — perturb as fraction
- **sigma**: 0.05 (5% of 6h = 18min jitter), **seed_base**: `ts_i / 3600`
- **low priority**: operational-risk — SR jitter on time gates may cause
  missed launchd cycles; keep disabled until stability verified

## N6-calc (2 candidates)

### 8. hub_growth_strategy _score_node priority
- **file**: `shared/n6/hub_growth_strategy.hexa`
- **line**: 489 — `let _sc = _score_node(_nid)` (integer priority score)
- **metric**: priority score for promotion candidate ranking
- **sigma**: 0.1, **seed_base**: hash of `_nid` (stable per-node)
- **pattern**:
  ```
  let _sc_raw = _score_node(_nid)
  let _sc = to_int(add_sr_noise_gated(to_float(_sc_raw), 0.1 * to_float(_sc_raw), seed))
  ```
- **caveat**: multiplicative sigma (0.1 * score) not additive — otherwise
  top-tier nodes get relatively tiny jitter. May require per-site sigma policy.

### 9. n6_conf / evo_verify inner score (downstream of #2)
- **file**: `shared/blowup/core/blowup.hexa`
- **line**: 1193 — `return n6_conf(value)` inside `evo_verify`
- **metric**: n6_conf score — wrapping here affects *all* evo_verify callers
- **status**: **do not wire** — too broad, breaks determinism assumption of
  corollary telescope consensus. Covered instead via site #2.

## Summary

- **candidates identified**: 7 actionable + 2 flagged (too broad/speculative)
- **top priority**: #1 (ouroboros_meta composite) — direct analog of demo
- **caution**: #3, #7, #9 (operational risk or over-broad)
- **required gate**: all sites use `add_sr_noise_gated` → no-op until
  `NEXUS_SR=1` is set globally
- **registration**: run `sr_registry.hexa register <engine> <metric> <sigma>
  <seed_base> <file> <line> planned` for each site before wiring
