# nexus raw 1 — Axis A: Kick Optimal (External-Resource-Only Mandate)

**date**: 2026-05-01
**raw entry**: nexus raw 1 (FIRST entry in nexus repo `/Users/ghost/core/nexus/.raw` — bootstrap)
**registry**: `/Users/ghost/core/nexus/state/raw_addition_requests/registry.jsonl` line 1 (new dir+file)
**paired**: hive raw 260 (META) + hive raw 261 (B+C hive specialization)
**user directive**: verbatim 2026-05-01 (preserved character-for-character below)

---

## 1. User directive — verbatim (한 글자 변경 X)

```
A. kick 의 최적 작동 (블로킹 0, 자원은 외부자원사용, hexa 작동은 반드시 외부자원이어야한다)
```

Territory carve-out (verbatim):

```
aa axis A 는 nexus 영역. axis B/C 는 hive 영역.
```

For full 3-axis (A/B/C) directive verbatim see `/Users/ghost/core/hive/docs/raw_260_n_axis_pluggable_2026_05_01.md` § 1.

---

## 2. A-axis core spec (three invariants)

| # | invariant | meaning | falsifier |
|---|-----------|---------|-----------|
| 1 | **블로킹 0** | caller fires kick and returns immediately; no sync await on the fire API itself. await is OPTIONAL separate API. | F-NEXUS-RAW1-2 (blocking_detected_count > 0 over 30d) |
| 2 | **외부 자원** | Mac local CPU / RAM / disk consumption during kick fire body MUST approach 0; actual hexa execution body runs on remote host (ubu1 / ubu2 / hetzner / future host pool member) routed via host_pool_canonical pick. | F-NEXUS-RAW1-3 (external_host_dispatch_rate < 0.99 over 30d) |
| 3 | **hexa 작동 외부 strict** | Mac local `hexa_interp` spawn during kick fire body is BANNED. kick body MUST route through `hive resource exec <host> --command "hexa run <script>"` so hexa_interp spawns on remote host, NOT Mac. | F-NEXUS-RAW1-1 (Mac local hexa_interp spawn detected during kick fire) |

---

## 3. A-modules already-land (mirrored in hive `~/.hive/state/session_models/modules_registry.hxc` axis A section)

25+ modules. Sample (full list in modules_registry.hxc):

| name | path | type | score | grade |
|------|------|------|-------|-------|
| kick_concurrency_lock (**ACTIVE**) | `/Users/ghost/core/hive/tool/kick_concurrency_lock.hexa` | hexa | 9.30 | A |
| nexus_kick_handler (rank=2) | `packages/hive-claude-hook-bus/handlers/nexus_kick.hexa` | hexa | 9.30 | A |
| kick_dispatch (rank=3) | `/Users/ghost/core/nexus/tool/kick_dispatch.hexa` | hexa | 9.05 | A |
| kick_main | `/Users/ghost/core/hive/tool/kick_main.hexa` | hexa | 8.95 | A+ |
| kick_core | `/Users/ghost/core/hive/tool/kick_core.hexa` | hexa | 8.95 | A+ |
| hexa_url_gate | `/Users/ghost/core/hexa-lang/gate/hexa_url.hexa` | hexa | 8.95 | A+ |
| hexa_url_handler | `~/.hx/bin/hexa-url-handler.sh` | bash | 8.85 | B+ |
| oauth_slot_pre_kick_gate | `tool/oauth_slot_pre_kick_gate.hexa` | hexa | 8.85 | B+ |
| hive_kick_canonical_lint | `tool/hive_kick_canonical_lint.hexa` | hexa | 8.95 | A+ |
| nexus_kick_canonical_lint | `tool/nexus_kick_canonical_lint.hexa` | hexa | 8.55 | B+ |
| kick_repair_first_lint | `tool/kick_repair_first_lint.hexa` | hexa | 8.75 | B+ |
| kick_io | `tool/kick_io.hexa` | hexa | 8.45 | B+ |
| kick_health_monitor | `tool/kick_health_monitor.hexa` | hexa | 8.50 | B+ |
| kick_lint | `tool/kick_lint.hexa` | hexa | 8.30 | B |
| launchd_queue_drain | `~/.hive/scripts/kick_queue_drain.sh` | bash+plist | 8.30 | B |
| kick_resolver_bypass_lint | `tool/kick_resolver_bypass_lint.hexa` | hexa | 8.30 | B |
| stuck_kick_chain_reaper | `tool/stuck_kick_chain_reaper.hexa` | hexa | 8.20 | B |
| kick_realtime_emit_lint | `tool/kick_realtime_emit_lint.hexa` | hexa | 8.20 | B |
| ai_cli_autonomous_lint | `tool/ai_cli_kick_autonomous_invocation_lint.hexa` | hexa | 8.10 | B |
| kick_parallel | `nexus/tool/kick_parallel.hexa` | hexa | 8.40 | B |
| cli_run_entry_guard | `nexus/cli/run.hexa` | hexa | 8.05 | B |
| kick_slot_gate | `tool/kick_slot_gate.hexa` | hexa | 7.95 | C+ |
| kick_bench | `nexus/tool/kick_bench.hexa` | hexa | 7.85 | C+ |
| kick_realtime_emit_lint | (etc) | | | |

**modules_per_axis = 25+** ≥ raw 260 invariant `modules_per_axis ≥ 3` ✓

---

## 4. External-resource path SSOT (canonical kick fire flow)

```
caller
  │ nexus kick <topic>     ← canonical CLI (raw 99 single-entry)
  ▼
nexus/cli/run.hexa         ← cli_run_entry_guard (host pin)
  │
  ▼
kick_concurrency_lock      ← active module (9.30) — host pick + lock
  │
  │ host_pool_canonical pick (own 5 SSOT)
  │   → {hetzner, ubu1, ubu2}
  ▼
launchd_queue_drain        ← Mac local enqueue (sub-100ms dispatch act)
  │
  ▼ ssh dispatch
remote host (ubu2)         ← hexa_interp spawns HERE, NOT on Mac
  │
  ▼
hexa run <script>          ← actual kick body executes externally
```

The Mac side participates ONLY in:
1. host pick decision (host_pool_canonical lookup)
2. ssh dispatch act (sub-100ms ssh launch)
3. launchd queue write/drain coordination

The kick **body** (hexa_interp execution) lives on the remote host.

---

## 5. Sanctioned channels

| # | channel | usage |
|---|---------|-------|
| (i) | `nexus kick <topic>` | canonical CLI surface (raw 99 single-entry) |
| (ii) | `hive resource exec <host> --command "hexa run nexus/cli/run.hexa kick run <topic>"` | manual escape-hatch via hive resource (own 8 compliant) |
| (iii) | launchd queue drain | `~/.hive/scripts/kick_queue_drain.sh` + `~/Library/LaunchAgents/dev.hexa-lang.kick-drain.plist` (1m cadence) |

---

## 6. Banned patterns

| ban | reason |
|-----|--------|
| `KICK_LEGACY_LOCAL=1` env flag | Mac local fallback 영구 폐기 per raw 100 alternative-dispatcher 2026-04-29 directive |
| direct `hexa run <script>` on Mac during kick fire (caller-side fork) | bypasses external-resource mandate (invariant 2 + 3) |
| blocking `kick await` where fire API itself waits for completion | violates 블로킹 0 invariant (must be Handle-poll or separate await API) |
| hardcoded host literal in kick fire path (e.g. `ssh ubu2 ...` literal in code) | bypasses host_pool_canonical (own 5 SSOT) |
| hardcoded module path reference (caller imports `kick_dispatch.hexa` directly) | bypasses axis-A core invocation surface (raw 260 pluggable-swap mandate) |

---

## 7. Allowed (carve-outs)

- bootstrap module with `status="WIP"` + `estimate_only=true` score during ramp (e.g. distributed-kick-mesh A10 status=cost-3x-resource)
- raw 91 honest C3 fail-loud when no host available (host_pool returns empty AND no fallback registered) — fail-loud is REQUIRED, NOT silent skip
- explicit user override `--local-execute` flag with disambiguation trailer + canonical citation for trace audit (raw 258 explicit_override carve-out)

---

## 8. Measurement axes

| metric | target | current |
|--------|--------|---------|
| `mac_local_hexa_fire_count_per_kick` | = 0 | 0 (verified via host audit) |
| `external_host_dispatch_rate` | ≥ 0.99 | TBD (30d post-registration measurement) |
| `blocking_detected_count` | = 0 | 0 (verified via kick_lint + stuck_kick_chain_reaper audit) |
| A-axis `active_module_score` | ≥ 9.0 | 9.30 ✓ (kick_concurrency_lock) |
| `modules_per_axis` (axis A) | ≥ 3 | 25+ ✓ |

---

## 9. Falsifiers

| id | trigger | action |
|----|---------|--------|
| F-NEXUS-RAW1-1 | 30d post any kick fire spawns `hexa_interp` on Mac (host_audit / lsof witness) | retire active module, fallback |
| F-NEXUS-RAW1-2 | 30d post `blocking_detected_count > 0` rolling | retire active |
| F-NEXUS-RAW1-3 | 30d post `external_host_dispatch_rate < 0.99` | strengthen, retire conservative module |
| F-NEXUS-RAW1-4 | 30d post any kick fire path code references hardcoded host literal (grep `ssh ubu1\|ssh ubu2\|ssh htz` outside host_pool_canonical) | directionality violation |
| F-NEXUS-RAW1-5 | 30d post any caller code references `tool/kick_<...>.hexa` directly (bypass nexus kick canonical CLI) | pluggable-swap violation |

---

## 10. raw 91 honest C3 disclosures

1. `launchd_queue_drain` Mac-side kick fire dispatch act itself runs on Mac (sub-100ms — host pick + ssh launch); BAN scope is hexa BODY execution, not the dispatch act.
2. `cli_run_entry_guard` score 8.05 includes 0.5 blocking penalty for sync entry path — escape-hatch only via `&` background or `hive resource exec` indirection.
3. `distributed-kick-mesh` A10 estimate score 0.75 status=cost-3x-resource = forward-spec module, not yet active.
4. reverse-ssh fallback chain (KICK_VIA_MAC_REVERSE β architecture) is registered as alternative path per raw 100 — disambiguation trailer required when invoked, NOT silent fallback.
5. raw 240 v2 cycle r25 lock-system R/W active module `kick_concurrency_lock` includes its own selfdog probes — score 9.30 reflects integrated selfdog discipline.

---

## 11. Cross-repo inheritance / orthogonality

| relation | hive raw / own | how nexus raw 1 relates |
|----------|----------------|--------------------------|
| inherit  | raw 260 (N-axis META) | nexus raw 1 = axis A SPECIALIZATION instantiation per territory carve-out |
| inherit  | raw 261 (B+C specialization) | sister specialization in hive territory |
| inherit  | raw 99 (canonical-CLI single-entry) | strengthens raw 99 with kick-fire-non-blocking + external-resource-strict |
| supersede | raw 100 (alternative-dispatcher fallback) | nexus raw 1 retires KICK_LEGACY_LOCAL=1 Mac fallback path |
| consume  | own 5 (host-pool routing SSOT) | kick fire body MUST consume host_pool_canonical |
| compliant | own 8 (cross-host-fix via hive CLI) | sanctioned channel (ii) `hive resource exec` is own 8 compliant |
| inherit  | raw 259 (zero-user-touch) | new-host onboarding for axis A inherits auto_sudo_wrapper + browser_harness_invoke |

---

## 12. Files produced this cycle

| path                                                                 | role                            |
|----------------------------------------------------------------------|---------------------------------|
| `/Users/ghost/core/nexus/.raw`                                        | NEW file — nexus raw 1 entry (line 6) |
| `/Users/ghost/core/nexus/state/raw_addition_requests/registry.jsonl`  | NEW dir+file — nexus raw 1 ledger (line 1) |
| `/Users/ghost/core/nexus/docs/raw_1_axis_A_kick_external_only_2026_05_01.md` | this doc                |

---

## 13. raw 117 5-check status

- genus slug ✓ (`axis-A-nexus-kick-optimal-external-only-mandate`, 5-genus composite per raw 106)
- ≥3 cognitive frameworks ✓ (5 declared: Unix nohup / message queue / host pool / raw 260 META precedent / own 7 R-policy precedent)
- ≥3 realization channels ✓ (5 declared: modules_registry / launchd queue / claude hook / canonical CLI / host_pool_canonical)
- ≥3 counter-examples ✓ (3 declared: explicit user override / Mac diagnostic dry-run / single-host bootstrap)
- ≥5 falsifiers ✓ (F-NEXUS-RAW1-1..5)

ALL PASS.

---

## 14. Follow-up

- 30d window measurement of `mac_local_hexa_fire_count_per_kick = 0` invariant
- distributed-kick-mesh A10 cost-3x-resource analysis (score promotion candidate)
- reverse-ssh β-architecture (KICK_VIA_MAC_REVERSE) disambiguation trailer wiring per raw 258
