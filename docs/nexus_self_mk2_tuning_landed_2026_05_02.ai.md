---
schema: nexus/docs/nexus_self_mk2_tuning/v1
last_updated: 2026-05-02
ssot: nexus/docs/nexus_self_mk2_tuning_landed_2026_05_02.ai.md
mk: 2
status: landed
related_specs: []
related_predecessors:
  - nexus/.roadmap.kick
  - nexus/.roadmap.atlas_n6
  - nexus/.roadmap.qrng
  - nexus/.roadmap.sim
  - nexus/.roadmap.omega_cycle
  - nexus/.roadmap.substrate_bridge
  - nexus/handoff/phase_a1_nexus_triplet_landing_20260502.md
related_raws: [15, 91, 92, 99, 105, 117, 264, 267, 269, 270, 271, 272, 273]
related_domains: [bind, outside_noise_clm, scheduler, publishing, kick, atlas_n6, omega_cycle]
new_files:
  - nexus/.roadmap.bind
  - nexus/.roadmap.outside_noise_clm
  - nexus/.roadmap.scheduler
  - nexus/.roadmap.publishing
patched_files: []
policy: additive_only_no_migration
cost: $0_mac_local
destructive: 0
---

# nexus self mk2 tuning — domain audit + 4 new roadmap SSOT landing (2026-05-02)

## TL;DR

nexus 자체 mk2 SSOT tuning. 기존 6개 .roadmap.* (kick / atlas_n6 / qrng / sim / omega_cycle / substrate_bridge) 보존 + 신규 4개 domain candidate roadmap 추가 (.roadmap.bind / .roadmap.outside_noise_clm / .roadmap.scheduler / .roadmap.publishing). 모든 신규 파일은 기존 mk2 schema (header line + entry lines) 동일 follow. 마이그레이션 0건, in-place 변경 0건, additive only. raw 270 triplet plan 별도 §3 에 기재 (next-cycle).

## §1 Phase 1 — directory audit

### §1.1 Top-level structure (relevant subset)

| Dir | 용도 | 도메인 후보 |
|-----|------|---------|
| `core/` | 5 subdomain (atlas_n6, bind, kick, qrng, sim) — triplet 2nd component | bind 신규 인식 |
| `modules/` | 14 module (atlas_n6, bind, chip_isa_n6, chip_rtl_gen, crystallography_n6, fusion_ledger, honesty_monitor, kick, mc_integrate, multiverse_nav, qrng, sim, tabletop_blackhole, verify_batch) | bind 신규 |
| `tool/` | 3667 entries (handlers/ + scheduler + bench helpers + atlas_*) | scheduler 신규, publishing (papers_cross_repo_lint) 신규 |
| `launchd/` | 3 plist (outside_noise_clm + atlas-absorb-sweeper) + 2 install/uninstall | scheduler 신규 |
| `bench/` | 25 bench files — bench_outside_noise_{bind,clm_modes,scheduler}.hexa | bind/scheduler/outside_noise_clm 모두 인식 |
| `docs/` | 52 entry — bind 2 ai.md + outside_noise 4 ai.md + akida + paradigm | 4 신규 후보 모두 핸드오프 존재 |
| `papers/` | 15 entry — canonical_n6_invariants {md,pdf,zenodo_meta}.* | publishing 신규 |
| `state/markers/` | bind_framework_outside_noise_landed.marker / bind_inprocess_dispatch_landed.marker / outside_noise_clm_scheduler_landed.marker / triplet_*.marker × 4 | 모두 attestation 기존 |
| `n6/` | 541 atlas append shards — akida × 12+ | substrate_bridge 보강 후보 (현 cycle 미land) |

### §1.2 Existing 6 .roadmap.* (pre-tuning baseline)

| 파일 | kind | perspective | goal | cond.1 | size |
|------|------|-------------|------|--------|------|
| `.roadmap.kick` | domain | provider | ω-cycle 6-step orchestration | unmet | 518 B |
| `.roadmap.atlas_n6` | domain | provider | n6 architecture atlas + paradigm convergence | unmet | 10962 B (47 entries) |
| `.roadmap.qrng` | domain | provider | production QRNG service | unmet | 502 B |
| `.roadmap.sim` | domain | provider | virtual universe sim agent runtime | unmet | 500 B |
| `.roadmap.omega_cycle` | meta | provider | ω-cycle 6-step + atlas convergence (kick + atlas_n6) | unmet | 538 B |
| `.roadmap.substrate_bridge` | meta | provider | quantum + virtual + n6 substrate convergence (qrng + sim + atlas_n6) | unmet | 569 B |

**Untouched**: 6/6 pre-existing files preserved (additive policy).

## §2 Phase 2 — 4 new domain candidate roadmap landed

### §2.1 .roadmap.bind (NEW — provider, consumers=anima+hive)

- **goal**: axis subscriber + dispatch framework (subprocess + in-process)
- **cond.1**: core/bind 5-file framework stable + ≥1 axis subscriber + dual-path verified — **MET** (verified via 2 ai.md handoffs + 2 markers)
- **cond.2**: ≥3 axis subscribers (currently 1 outside_noise) — **UNMET** (need 2 more candidates: e.g. atlas_emit, sim_tick)
- **landed entries**: bind.framework_v1 + bind.inproc_dispatch
- **upstream evidence**:
  - `nexus/core/bind/{source,registry,router,inproc_dispatch,bind_main}.hexa` (5 files)
  - `nexus/modules/bind/{outside_noise.hexa,README.ai.md}` (2 files)
  - `nexus/state/active_bindings.hxc` (declarative SSOT)
  - `nexus/docs/bind_framework_outside_noise_subscriber_landed_2026_05_02.ai.md`
  - `nexus/docs/bind_inprocess_dispatch_landed_2026_05_02.ai.md`

### §2.2 .roadmap.outside_noise_clm (NEW — provider, consumer=anima)

- **goal**: ω-cycle outside-noise CLM primitive injector (handler + scheduler + bind subscriber + 3-mode wrapper)
- **cond.1**: handler 9-case selftest PASS + 3-mode wrapper + 1+ real-CLM cycle absorbed — **MET**
- **cond.2**: launchd auto-cycle ≥100 cycles continuous + atlas absorption — **PARTIAL** (~9 fired markers; launchd not bootstrapped persistently)
- **landed entries**: handler_landed + real_inference_wrapper + scheduler_stage0
- **upstream evidence**:
  - `nexus/tool/handlers/outside_noise_clm_handler.hexa` (510→674 LOC, 9/9 selftest)
  - `nexus/tool/outside_noise_scheduler.hexa` (346 LOC)
  - 4 ai.md handoffs in `nexus/docs/`
  - 1 marker (`outside_noise_clm_scheduler_landed.marker`) + ~20 fire/skip markers

### §2.3 .roadmap.scheduler (NEW — provider, consumers=anima+hive)

- **goal**: launchd-driven periodic invocation framework (mac-native, low-overhead, watchdog+lock)
- **cond.1**: ≥1 launchd plist deployed + scheduler.hexa pattern + 6-axis bench (B1..B6) — **MET**
- **cond.2**: ≥2 distinct schedulers (outside_noise + atlas-absorb-sweeper = 2) — **MET**
- **cond.3**: linux/cron parity — **UNMET** (mac-only currently)
- **landed entries**: outside_noise_landed + atlas_absorb_sweeper (predecessor)
- **upstream evidence**:
  - `nexus/launchd/com.nexus.outside_noise_clm.plist` (87 LOC)
  - `nexus/launchd/install_outside_noise_clm.hexa` (155 LOC)
  - `nexus/launchd/uninstall_outside_noise_clm.hexa` (156 LOC)
  - `nexus/launchd/dev.hexa-lang.atlas-absorb-sweeper.plist` (predecessor pattern)
  - `nexus/bench/bench_outside_noise_scheduler.hexa` (450 LOC)

### §2.4 .roadmap.publishing (NEW — provider, consumers=anima+hive)

- **goal**: papers + canonical n6 invariants + zenodo deposit + cross-repo publish lint
- **cond.1**: papers/canonical_n6_invariants.md PASS + zenodo cache + cross-repo lint exempt list — **PARTIAL** (3 zenodo n6 shards in grandfather exempt list pending atlas auto-absorb)
- **landed entries**: canonical_n6 + cross_repo_lint
- **upstream evidence**:
  - `nexus/papers/canonical_n6_invariants.{md,pdf}`
  - `nexus/papers/canonical_n6_invariants_zenodo_meta.json`
  - `nexus/.papers-cross-repo-lint-exempt` (own 9 grandfather list)

### §2.5 Domain candidates considered but NOT landed this cycle

| Candidate | 이유 deferred |
|-----------|------------|
| `.roadmap.akida` | nexus side substrate provider 후보. anima 측에 `.roadmap.akida` consumer 이미 존재. nexus side `core/akida/` 미존재 (`AKIDA_OMEGA_CYCLE_LAYERS.md` design only) — 현 land 부족. next cycle 시 `core/akida/` triplet 또는 modules/akida/ 생성 후 land. |
| `.roadmap.honesty_monitor` | `modules/honesty_monitor/` exists but no recent 2026-05-02 cycle artifact. raw 91 deterministic verifier domain. defer to dedicated cycle. |
| `.roadmap.multiverse_nav` | `modules/multiverse_nav/` exists, state/ subdir 보유. domain SSOT 명확하지 않음. defer. |
| `.roadmap.fusion_ledger` | `modules/fusion_ledger/` exists with data/. domain SSOT scope 미정. defer. |
| `.roadmap.chip_*` (isa_n6, rtl_gen) | n6 architecture sub-domain. atlas_n6 흡수 가능성 — 별도 domain 분리 신중. defer. |

## §3 Phase 3 — raw 270 triplet plan (next-cycle)

`raw 270` = nexus core/ + modules/ + ai-native doc + config triplet structure (anima `anima/{core,modules}/rng/` prototype 시작). Phase A1 (commit `5ea618e8`) 이미 4 domain (kick / atlas_n6 / qrng / sim) triplet land 완료 (38 files / 4/4 selftest PASS).

### §3.1 현 triplet status

| Domain | core/{source,registry,router,*_main}.hexa | modules/<backend>.hexa | config/*_sources.json | ai.md | marker |
|--------|-------------------------------------------|------------------------|----------------------|-------|--------|
| kick | 4/4 | 4 | 1 | yes | yes |
| atlas_n6 | 4/4 | 4 | 1 | yes | yes |
| qrng | 4/4 | 4 | 1 | yes | yes |
| sim | 4/4 | 4 | 1 | yes | yes |
| **bind** | 5/4 (+inproc_dispatch.hexa) | 1 (outside_noise) | **0** (no bind_sources.json) | yes (bind_framework + inproc) | yes (2) |
| **outside_noise_clm** | 0 (handler in tool/handlers/, NOT core/) | – | – | yes (4) | yes (1+~20 fire) |
| **scheduler** | 0 (scheduler.hexa in tool/, plist in launchd/) | – | – | yes (1) | yes (1) |
| **publishing** | 0 (papers_cross_repo_lint.hexa in tool/, papers in papers/) | – | – | – | – |

### §3.2 raw 270 triplet plan — 4 신규 도메인 적용 후보

**Option A — bind triplet 보완 (작은 gap, $0)**:
- `nexus/core/bind/{source,registry,router,bind_main}.hexa` 이미 존재 (5/4 — inproc_dispatch.hexa 추가)
- `nexus/modules/bind/` 1 backend (outside_noise.hexa) — 추가 axis subscriber 필요 (atlas_emit, sim_tick 등)
- `nexus/config/bind_sources.json` — **MISSING** → 추가 land 필요 (active_bindings.hxc 가 SSOT 이지만 config-style 미정렬)
- 결정: `bind_sources.json` 추가가 raw 270 triplet 완성 핵심. bind axis 카탈로그 (axis_id + handler_path + opts) JSON-formal SSOT.

**Option B — outside_noise_clm triplet 분리 (mid gap, $0)**:
- `nexus/core/outside_noise_clm/{source,registry,router,outside_noise_clm_main}.hexa` (4 새 파일) — handler 의 source/registry/router layer 분리.
- `nexus/modules/outside_noise_clm/{handler_clm.hexa,handler_local.hexa,handler_mock.hexa}.hexa` (3 backend) — 3-mode wrapper 의 backend split.
- `nexus/config/outside_noise_clm_sources.json` — mode catalog (mock/local/hf + endpoint paths).
- 결정: handler 가 이미 1 file 에 통합되어 있어 triplet 분리는 over-engineering 위험. **defer to next cycle**, current handler 가 cond.1 만족하므로 triplet 강제 X.

**Option C — scheduler triplet 신규 (large gap, $0)**:
- `nexus/core/scheduler/{source,registry,router,scheduler_main}.hexa` — launchd plist + cron 추상화 layer.
- `nexus/modules/scheduler/{launchd_plist.hexa,cron_crontab.hexa,daemon_loop.hexa}.hexa` (3 backend) — mac+linux+headless 추상화.
- `nexus/config/scheduler_sources.json` — plist catalog.
- 결정: cond.3 (linux parity) 해결 시 동시 진행 권장. 현재는 mac-only 상태에서 추상화 over-engineering 위험. **defer to linux parity cycle**.

**Option D — publishing triplet 신규 (small gap, $0)**:
- `nexus/core/publishing/{source,registry,router,publishing_main}.hexa` — papers + zenodo + cross-repo abstraction.
- `nexus/modules/publishing/{paper_md.hexa,zenodo_deposit.hexa,cross_repo_lint.hexa}.hexa` (3 backend).
- `nexus/config/publishing_sources.json` — paper catalog.
- 결정: `papers_cross_repo_lint.hexa` 가 tool/ 에 이미 존재 + own 9 grandfather list 가 SSOT 역할. triplet 분리 가치 LOW — **defer**.

### §3.3 next-cycle 추천 priority

| 우선 | Action | 비용 | 효과 |
|---|---|---|---|
| 1 | **Option A**: `nexus/config/bind_sources.json` 추가 (raw 270 conformance 완성, 200 LoC est.) | $0 mac-local | bind triplet 6/6 → bind.cond.1 attestation 강화 |
| 2 | bind.cond.2 — 2 추가 axis subscriber (atlas_emit + sim_tick) | $0 mac-local | bind framework usage 다양화 |
| 3 | scheduler.cond.3 — linux/cron parity (cron_crontab.hexa wrapper) | $0 mac-local | mac-only 제약 해소 |
| 4 | outside_noise_clm.cond.2 — launchd persistent bootstrap (사용자 GUI session 필요) | $0 mac-local | 100+ cycle 자동 사이클링 |
| 5 | (defer) `.roadmap.akida` — `core/akida/` triplet land 시 추가 | $0-low | nexus side substrate provider |

## §4 raw 15 honest

1. **scope-limit**: 4 신규 .roadmap.* 만 land. core/ + modules/ + config/ triplet 보완 (raw 270) 은 §3 에서 plan only, 본 cycle 미실행 (gold-plate 회피).
2. **selftest 미실행**: 본 작업은 SSOT JSON metadata 만 land. 신규 도메인 cond.* verifier 명령은 evidence path 만 등록, 실제 PASS 검증은 외부 (handoff doc + marker 의 predecessor evidence 인용).
3. **byte-identical 미보장**: roadmap JSON 1-line schema 는 stable이지만 본 작업 산출은 metadata 신규 추가 (re-run determinism unaffected — 1회 land 만).
4. **추가 도메인 5 deferred**: §2.5 의 akida / honesty_monitor / multiverse_nav / fusion_ledger / chip_* — domain SSOT scope/land state 불명확하여 별도 cycle 권장.
5. **bind.cond.2 met=false**: 1/3 axis 만 등록. 신규 axis 후보 (atlas_emit / sim_tick) 는 design 단계 미land.
6. **outside_noise_clm.cond.2 partial**: ~9 fired markers 기록되었으나 launchd plist 가 사용자 GUI session 에 bootstrap 미보장 → 100+ continuous 미달.
7. **scheduler.cond.3 unmet**: launchd-only (mac native). headless linux 사용 시 cron wrapper 필요.
8. **publishing.cond.1 partial**: 3 zenodo n6 shards 가 own 9 grandfather exempt 에 잔존 (atlas auto-absorb 대기).
9. **atlas_n6 entry duplication 미정정**: 기존 .roadmap.atlas_n6 47 entries 중 다수 DUPLICATE_BASE_NODE_42 / wrapped_mock_primitive_cycle_* 중복. 본 cycle 미정정 (additive policy).
10. **omega_cycle / substrate_bridge cross-domain 미확장**: 신규 4 도메인 (bind / outside_noise_clm / scheduler / publishing) 가 omega_cycle 또는 substrate_bridge meta domain 의 `domains_spanned` 에 추가될 수 있으나 본 cycle 보존 (additive policy 우선).
11. **publishing.cond.1 verifier `papers_cross_repo_lint.hexa` 미실행 검증**: 산출물 path 인용만, 실제 PASS 보장 no.
12. **markers for 4 신규 cond 미생성**: 신규 cond.* attestation 별 marker 아직 없음. cond.* met 인 경우 evidence path 인용 only (handoff doc + 기존 markers 만 인용).
13. **cost = $0 mac-local**: 외부 LLM/GPU 호출 0건. SSOT JSON 4 file write only.
14. **destructive = 0**: 기존 6 roadmap 파일 변경 0건. 4 신규 파일만 추가.
15. **BR-NO-USER-VERBATIM**: 사용자 prompt 직인용 없음. 작업 의도 일반화하여 재기술.

## §5 Marker

`nexus/state/markers/nexus_self_mk2_tuning_landed.marker`

## §6 Friendly note (per task convention)

본 cycle 은 SSOT metadata 만 land — 신규 코드 zero, 마이그레이션 zero. 4 신규 도메인의 cond.* status 는 기존 landed 산출물의 attestation 인용 (provider perspective). next cycle 추천은 §3.3 priority list 참조 (Option A: bind_sources.json 추가가 cost/effort/effect 균형 ratio 최선).
