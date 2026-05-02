---
schema: nexus/docs/bind_framework_outside_noise_landed/v1
last_updated: 2026-05-02
ssot: nexus/docs/bind_framework_outside_noise_subscriber_landed_2026_05_02.ai.md
status: landed
related_specs:
  - hive/spec/dispatch_framework_v1.spec.yaml
related_predecessors:
  - nexus/docs/kick_clm_outside_noise_design_2026_05_02.ai.md
  - nexus/tool/handlers/outside_noise_clm_handler.hexa (predecessor sha 0d57f29b — pre-patch)
related_raws: [91, 92, 117, 264, 267, 270, 271, 272, 273]
related_domains: [bind, kick, atlas_n6, omega_cycle]
---

# nexus side bind framework + outside_noise subscriber landed

## TL;DR

Phase F + Phase B (BG-B) landed: nexus side bind framework (4 core file + 1 module + state ssot) + outside_noise axis dual-path subscriber (handler --bind-fire flag added) + 6-metric micro-benchmark. dispatch_framework_v1.spec.yaml Section 1/2/3 conformant. Mock CLM mode end-to-end PASS; real CLM hand-off remains BG-A scope. Bench measured B3 dispatch overhead ~803ms (bind path adds 1 subprocess fork hop), B5 RSS overhead ~16kb.

## Bind framework — 4 core + 1 module landed

| File | LOC | sha256 (head) | role |
|------|-----|---------------|------|
| `nexus/core/bind/source.hexa` | 253 | `4f3a5f0d` | BindPayload/BindResult/BindSubscription/BindIssue contract structs (mirrors hive Section 1 event_schema) |
| `nexus/core/bind/registry.hexa` | 241 | `19532edd` | active axes registry; reads `state/active_bindings.hxc` declarative SSOT (or built-in baseline fallback) |
| `nexus/core/bind/router.hexa` | 280 | `ec07c29d` | axis → handler dispatch via subprocess exec; verdict normalization (PASS/FAIL/REJECT/DRY-RUN) |
| `nexus/core/bind/bind_main.hexa` | 221 | `c5459dba` | aggregator entry CLI (sub-commands: list / validate / fire / --selftest) |
| `nexus/modules/bind/outside_noise.hexa` | 204 | `1406f77a` | outside_noise axis subscriber wrapper; `pub fn on_outside_noise_axis_fire(payload) -> BindResult` |
| `nexus/modules/bind/README.ai.md` | 89 | `115dcfaa` | architecture + spec conformance map + how-to-add-new-axis |
| `nexus/state/active_bindings.hxc` | 13 | `7d194b35` | declarative SSOT — outside_noise registered axis_loop scope |

Total bind-framework new code: ~1188 LoC (4 core + 1 module + 1 state file + 1 README).

## Handler dual-path patch — additive (CLI preserved + bind-fire added)

| | pre | post |
|---|---|---|
| sha256 | `0d57f29b601a11b4e4e859e698641f0da3e02a6fd1d28d1db37e0f4023a2a480` | `f8f09d1a37e2283123f8a4472438e6fc060950f12b404a0a8f12e9ffff102450` |
| LOC | 590 | 674 |
| Selftest | 7/7 | **9/9** (case 8 + case 9 added) |
| CLI direct | `--cycle N --mock` (unchanged) | `--cycle N --mock` (preserved) |
| bind path | n/a | `--bind-fire --cycle N` (new flag; pipeline identical) |
| Public function | (none for bind) | `pub fn on_outside_noise_axis_fire(payload_cycle_id: str) -> str` (verdict) |

Patch is **additive only** — CLI code path byte-identical for original 7 selftest cases. Cases 8 (`bind axis fire path verdict=PASS`) + 9 (`CLI+bind path candidate generation byte-identical`) verify the new dual-path contract.

## 9-case selftest results (handler)

```
[outside_noise_clm_handler selftest]
  case1 PASS valid candidate cycle=0 honest=true verifier=true
  case2 PASS duplicate detected for cycle=3 (seed=2)
  case3 PASS honest_c3 falsified for cycle=2 (seed=3)
  case4 PASS verifier rejected non-measurable
  case5 PASS .roadmap.atlas_n6 present
  case6 PASS anima_clm_invoke wrapper round-trip (mock mode, _mode tag verified)
  case7 PASS legacy fallback mock intact (graceful-degrade safety net)
  case8 PASS bind axis fire path verdict=PASS event=outside_noise cycle=c1
  case9 PASS CLI+bind path candidate generation byte-identical (deterministic mock cycle=1)
[outside_noise_clm_handler selftest] OK 9/9 PASS (case5 informational, case6 skip-aware)
```

Byte-identical 2-run check (selftest stdout sha): `8bb0db6680479adb` ↔ `8bb0db6680479adb` MATCH.

## Bench results — n=10 (mock CLM mode)

Wall-clock (millisecond, perl Time::HiRes precision):

| Metric | Value | Note |
|--------|-------|------|
| **B1** standalone CLI invoke | mean=**1104.8 ms** ± 201.5 (range 917-1509) | direct `hexa run handler --cycle N --mock` |
| **B2** bind axis fire | mean=**1908.4 ms** ± 233.4 (range 1663-2463) | `hexa run bind_main fire outside_noise cN` (bind_main → router → handler) |
| **B3** dispatch overhead | **803.6 ms** | B2 - B1 = 1 extra subprocess hop (bind_main wrapping router exec wrapping handler exec) |
| **B4** throughput | B1=0.905 cps / B2=0.524 cps | mock pipeline only; real-CLM bound by inference latency |
| **B5** peak RSS | B1=58288 kb / B2=58304 kb / overhead **16 kb** | macOS `/usr/bin/time -l` — bind framework RSS overhead negligible (single hexa process) |
| **B6** validation pipeline (per case approx) | **378 ms** | upper-bound via 9-case selftest mean; real per-validation cost lower since cases 1-7 do not run full pipeline |

bench file sha: `nexus/bench/bench_outside_noise_bind.hexa` (358 LOC, selftest 4/4 PASS).
results.json sha (structural-only, timing-elided): `d9d3e781bfb8f0f7` byte-identical 2-run MATCH.
results path: `nexus/state/bench_outside_noise_bind/results_2026_05_02.json` (821 bytes).

### Bench interpretation

- Bind path adds ~73% latency overhead on top of standalone CLI (1908 vs 1104 ms). This is dominated by the **second `hexa run` startup cost** (router subprocess-exec'ing handler). Stage0 has no in-process dispatch, so each bind_main → router → handler hop forks a fresh hexa process.
- Future optimization: stage1 hexa-lang in-process function dispatch (raw 273 follow-on) could collapse the 800ms overhead to <50ms (single-process call).
- RSS overhead 16kb proves the bind framework itself has no significant memory footprint — the ~58MB RSS is dominated by hexa runtime bootstrap (same baseline both paths).

## Spec conformance — dispatch_framework_v1.spec.yaml

| Section | Implementation |
|---------|----------------|
| 1 event_schema | `BindPayload`/`BindResult`/`BindSubscription`/`BindIssue` in `core/bind/source.hexa` (forward-compat superset of TypedPayload/HandlerResult/Subscription/Issue) |
| 2 handler_contract | `pub fn on_outside_noise_axis_fire(payload_cycle_id: str) -> str` in handler + module wrapper. Default timeout 30s + cost_cap $0.01 USD applied informationally |
| 3 subscription_lifecycle | declarative SSOT `state/active_bindings.hxc` + imperative CLI `bind_main fire` ; drift detection via `bind_main validate <axis>` emitting F-DISPATCH-2 for unregistered axes |
| 4 composition | `axis_loop` scope (sequential default) for outside_noise; parallel/DAG deferred per stage0 limitation (raw#10 C6) |

agent_directive 5-step protocol (CONSULT/TYPE/ATTR/DECL/COMPOSE) all satisfied at land time.

## raw#10 caveats (5-7개)

- **C1 — bind framework new land, 100% spec-yaml-parser equivalence not guaranteed**: hive `dispatch_framework_v1.spec.yaml` is parsed by humans-in-the-loop at this baseline (deferred lint tools `dispatch_handler_signature_lint.hexa` + drift lint per spec C4). The nexus side framework names are aligned but field-by-field schema validation will require future hexa yaml parser.
- **C2 — bind dispatch overhead ~803ms exceeds standalone CLI by 73%**: caused by extra subprocess hop (bind_main → router → handler). Acceptable for ω-cycle scheduling (~1 cycle / 10s typical) but precludes high-frequency dispatch. stage1 in-process dispatch primitive (raw 273 stage1 follow-on) is the path forward.
- **C3 — `state/active_bindings.hxc` write race-safety not yet enforced**: registry reads file without locking; bind_main does not yet implement `add`/`remove` sub-commands (only `list`/`validate`/`fire`). Concurrent edits from cron + interactive could collide. raw#264 audit append-only enforced (no in-place mutation in registered file).
- **C4 — handler dual-path = incremental code complexity**: 84 new LOC (590 → 674) for `--bind-fire` flag + `on_outside_noise_axis_fire` pub function + 2 selftest cases + helper `_bind_fire_self_probe`. Maintained as additive only (zero CLI-direct path mutation). Predecessor preservation (raw 91 C3) honored.
- **C5 — Bench mock mode only — real-CLM benchmarking deferred to BG-A**: B1/B2/B3 measure subprocess + validation pipeline cost only. Real anima Mk.XII v3 CLM inference (mac local 15-30s + HF gated 30-60s) NOT included; will dominate any real-cycle bench by 10-20× over the framework overhead.
- **C6 — B6 validation overhead is upper-bound coarse approximation**: measured by dividing 9-case selftest wallclock by 9, but cases 1-7 do not exercise the full validation pipeline (most run individual unit assertions). Real per-validation cost is lower; precise measurement requires per-case timer instrumentation (deferred).
- **C7 — cron / scheduler integration NOT included per BG-C scope**: bench measures one-shot dispatch only. Cron-driven omega-cycle scheduling (every N minutes) overhead, lockfile contention, and cumulative drift are BG-C responsibility. Bench numbers represent cold-cache single-invocation cost.

## File index (sha-pin)

| Category | File | sha256 (head) | LOC |
|----------|------|---------------|-----|
| core | `nexus/core/bind/source.hexa` | `4f3a5f0d` | 253 |
| core | `nexus/core/bind/registry.hexa` | `19532edd` | 241 |
| core | `nexus/core/bind/router.hexa` | `ec07c29d` | 280 |
| core | `nexus/core/bind/bind_main.hexa` | `c5459dba` | 221 |
| module | `nexus/modules/bind/outside_noise.hexa` | `1406f77a` | 204 |
| module | `nexus/modules/bind/README.ai.md` | `115dcfaa` | (md) |
| state | `nexus/state/active_bindings.hxc` | `7d194b35` | 13 |
| handler-patch | `nexus/tool/handlers/outside_noise_clm_handler.hexa` (post) | `f8f09d1a` | 674 |
| bench | `nexus/bench/bench_outside_noise_bind.hexa` | (see Phase 3) | 358 |
| bench-results | `nexus/state/bench_outside_noise_bind/results_2026_05_02.json` | (timing-elided) | (821 bytes) |
| marker | `nexus/state/markers/bind_framework_outside_noise_landed.marker` | `a83147e4` | 1 |
| handoff (this doc) | `nexus/docs/bind_framework_outside_noise_subscriber_landed_2026_05_02.ai.md` | (auto post-write) | (this) |

## BG scope boundaries (non-collision guarantee)

- **BG-B (this BG)**: nexus side new bind framework (4 core + 1 module) + handler entry path additive (`--bind-fire` flag + `on_outside_noise_axis_fire` pub function) + bench file new
- **BG-A (no-touch)**: handler `_invoke_anima_clm()` internal + real CLM wrapper integration — BG-B did NOT modify these
- **BG-C (no-touch)**: scheduler / cron / kick loop driver — BG-B did NOT modify these

## Status / next step

- **status**: landed — 4 core + 1 module + handler dual-path + bench all PASS
- **selftest aggregate**: 4/4 (source) + 1/1 (registry baseline OR file) + 6/6 (router) + 5/5 (bind_main) + 1/1 (outside_noise module) + **9/9 (handler)** + 4/4 (bench) = **30/30 PASS**
- **byte-identical 2-run**: handler selftest stdout MATCH + mock fire path stdout MATCH + bench results.json structural MATCH
- **next user decision**: BG-A real CLM wire (anima_clm_invoke wrapper bind path call) + BG-C cron / scheduler integration
