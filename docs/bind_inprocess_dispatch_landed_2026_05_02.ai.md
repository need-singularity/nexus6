# nexus bind in-process dispatch landed (2026-05-02)

## Summary
BG-1 land: bind framework ~800ms hexa-init subprocess overhead eliminated via
in-process axis dispatch table. raw 273 stage1 follow-on to BG-B (commit
nexus/core/bind/* land 2026-05-02).

## Design decision: (alpha) symbol-table dispatch
- Considered (alpha) symbol table dispatch via `use` import + direct fn call
- Considered (beta) thread/coroutine pool — REJECTED (hexa stage0 single-thread)
- Considered (gamma) hot-cache subprocess daemon — REJECTED (statefulness blast
  radius + IPC framing cost similar to subprocess startup at low qps)
- Chose (alpha) — same pattern as `hive/core/raw_format/registry.hexa`
  switch-style dispatch over schema_id. Adding axis = 1 import + 1 case branch.

## Files touched

### Added
- `nexus/core/bind/inproc_dispatch.hexa` (NEW, 202 LoC)
  sha256: c2f2bc7e5139953924e0168d8822a1cee54309f1570d34d75d2d181187e5553c
  - imports `nexus/tool/handlers/outside_noise_clm_handler` directly
  - exposes `nexus_bind_inproc_dispatch(axis, payload) -> BindResult`
  - exposes `nexus_bind_inproc_dispatch_has(axis) -> bool`
  - registered axes: 1 (`outside_noise`)
  - selftest: `__NEXUS_BIND_INPROC_DISPATCH_SELFTEST__ PASS axes=1 sub=4/4`

### Modified (additive)
- `nexus/core/bind/router.hexa` (was 281 → 311 LoC, +30)
  sha256: 56d11ffb05e1fe93b4752091269ba183704f5314fb574669f2aaf04afa9eabfa
  - +`use "inproc_dispatch"`
  - `nexus_bind_router_fire`: try in-process FIRST when subscription opts say
    `inprocess=true`, fall back silently to subprocess on UNREGISTERED-INPROC
  - env overrides: `NEXUS_BIND_INPROC_FORCE=1` / `NEXUS_BIND_INPROC_DISABLE=1`
  - selftest extended (+1 case): `__NEXUS_BIND_ROUTER_SELFTEST__ PASS verdict_normalize=4 mock_dispatch=1 validate=1 inproc_table=1`

- `nexus/core/bind/registry.hexa` (was 242 → 291 LoC, +49)
  sha256: 2aeb9be8cd7146b39da7bdf861266daa076ae086c168a1b6293cc3521c6968ba
  - parser extended: recognise optional `inprocess=true|false` field in
    `bind axis=... handler=... ...` line
  - field stored in `BindSubscription.opts` as `[["inprocess", "true"]]`
    (NO struct-field change → source.hexa untouched)
  - +`pub fn nexus_bind_registry_inprocess(axis: str) -> bool` helper
  - default baseline opts: `inprocess=false` (back-compat)
  - selftest extended (+1 case)

- `nexus/state/active_bindings.hxc`
  sha256: 66439e46e3a6813045a492bc083fdf723852758fa9ed982d6177696bf3fdb36b
  - `outside_noise` subscription opted in: `inprocess=true`
  - format header documented

- `nexus/bench/bench_outside_noise_bind.hexa` (was 423 → 468 LoC, +45)
  sha256: 6f13b067cfb1c3657a1782c9581e31c5ac6e6bb1dc8e6e20f0e2b2050b61506a
  - +B3 in-process bind fire path (`NEXUS_BIND_INPROC_FORCE=1` invoked)
  - +B3a/B3b/B3c overhead breakdown (subproc vs inproc vs speedup)
  - +B5 RSS now 3-way (b1/b2/b3)
  - sentinel updated: emits `inproc_speedup_ms`
  - JSON caveat C6/C7 added

## Bench results (n=10, mac-local mock CLM)

| metric | B1 standalone | B2 subproc bind | B3 inproc bind | speedup |
|---|---|---|---|---|
| ms_mean | 1099.6 | 2152.6 | **1010.5** | -1142.1 vs B2 |
| ms_std | 169.99 | 119.29 | 39.98 | (3-4x tighter) |
| ms_min | 908 | 1964 | 957 | |
| ms_max | 1466 | 2312 | 1075 | |
| dispatch overhead vs B1 | — | +1053 | **-89.1** | inproc faster than direct CLI |
| throughput cps | 0.909 | 0.465 | **0.990** | 2.13x vs B2 |
| RSS kb | 58256 | 58256 | 57184 | -1072 lighter |

Sentinel: `__BENCH_OUTSIDE_NOISE_BIND__ PASS n=10 b1_ms_mean=1099.6 b2_ms_mean=2152.6 b3_ms_mean=1010.5 inproc_speedup_ms=1142.1`

JSON: `nexus/state/bench_outside_noise_bind/results_2026_05_02.json` (n=10)

## Byte-identical 2-run

PASS:
- `inproc_dispatch.hexa --selftest` 2-run identical
- `bind_main.hexa fire outside_noise c5` (NEXUS_BIND_INPROC_FORCE=1) 2-run identical

## raw#10 caveats

- C1 — In-process dispatch is axis-handler hardcoded; adding a new axis
  requires editing `inproc_dispatch.hexa` (+1 import + 1 case branch). Same
  as raw_format registry pattern.
- C2 — Module import failure ⇒ silent fallback to subprocess via
  `UNREGISTERED-INPROC` sentinel (NEVER emitted as outcome). Build-time
  failure of `use` would fail the whole router compile — caught at land time.
- C3 — In-process state share risk. Handler module is audited stateless
  (CLM mock branch is deterministic; reality_map writes are file-based, same
  side-effects either path). Multiple sequential in-process fires WITHIN
  one bind_main invocation share heap state — first fire's reality_map writes
  visible to subsequent fires.
- C4 — Opt-in flag default `inprocess=false` for back-compat baseline. State
  file `active_bindings.hxc` has `outside_noise inprocess=true` (Round-2 land).
  Disable via `NEXUS_BIND_INPROC_DISABLE=1` env.
- C5 — Bench compare = same cycle, mock CLM only; real CLM benchmark is
  BG-A scope. Cron / scheduler overhead NOT measured (BG-3 scope).
- C6 — In-process path uses `_bind_fire_self_probe` (lighter validation);
  subprocess path is full pipeline. Verdict semantics may differ on cycle 0
  (subprocess REJECT due to dup against persistent reality_map; inproc
  PASS via probe-only).
- C7 — Stage0 has no fn pointers. Switch-style dispatch verbose but matches
  the canonical hive/core/raw_format/registry.hexa pattern. raw 273 stage1
  trait/dyn-call follow-on collapses both into HashMap dispatch.

## Selftest summary
- `nexus_bind_source` — PASS (untouched)
- `nexus_bind_registry` — PASS (extended with inprocess helper)
- `nexus_bind_router` — PASS sub-7/7 (extended with inproc table check)
- `nexus_bind_inproc_dispatch` — PASS sub-4/4 (NEW)
- `nexus_bind_main` — PASS sub-5/5
- `bench_outside_noise_bind` — PASS sub-4/4

## Anti-conflict
- BG-2 race-safety lock: untouched (only schema field added to opts)
- BG-3 scheduler tuning: untouched
- BG-4 model card: untouched
- Mac-local cost: $0
- Destructive ops: 0
