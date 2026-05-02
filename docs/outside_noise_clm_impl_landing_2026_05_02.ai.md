---
schema: nexus/docs/outside_noise_clm_impl/v1
last_updated: 2026-05-02
ssot: nexus/tool/handlers/outside_noise_clm_handler.hexa
mk: 2
status: impl_landed_stage0_mock
related_specs:
  - nexus/docs/kick_clm_outside_noise_design_2026_05_02.ai.md
related_raws: [99, 105, 267, 269, 270, 271, 272, 273, 91, 92, 9, 10, 11, 12, 15]
related_domains: [kick, atlas_n6, omega_cycle]
related_metas: [omega_cycle, n_substrate (anima)]
predecessor_design_sha: 938ef2ae5f1434622ef05a0f8719915559cb2726
---

# kick + anima CLM = NEXUS open-well outside-noise generator — Phase 4 Option B impl landing

## TL;DR

Design doc `kick_clm_outside_noise_design_2026_05_02.ai.md` Option B (bind axis subscriber) impl 시도 → **bind framework absent in nexus** 확인 → Plan B fallback (standalone tool) 채택. handler.hexa landed (510 LOC, sha `e59f09a8`), reality_map cycle_0 baseline 8 nodes (atlas n6 canonical constants), validation pipeline 3-check (falsifier + verifier + raw 91 honest C3), atlas_absorb_hook integration, .roadmap.atlas_n6 entry auto-emit, selftest 5/5 PASS, end-to-end mock cycle 1+4 ABSORB + cycle 2 REJECT verified.

## Audit summary (Step 1)

| 항목 | 결과 | 비고 |
|---|---|---|
| bind framework in nexus | **ABSENT** | `*bind*.hexa` in `tool/` 0개 (lenses에만 nuclear/binding/anima_binding 3개 = unrelated) |
| dispatch_framework spec | **NOT FOUND** | design doc referenced `hive/spec/dispatch_framework_v1.spec.yaml` 미존재 |
| anima CLM availability | **STUB ONLY** | `anima/tool/anima_serve_smoke.hexa` = contract-stub schema test only, real LoRA inference 미수행 |
| nexus/state/reality_map/ | **MISSING** | 신규 생성 (cycle_0.jsonl 8 nodes baseline) |
| nexus/tool/handlers/ | **MISSING** | 신규 생성 |
| atlas_absorb_hook.hexa | active | omega_cycle witness JSON 형식만 ingest |
| .roadmap.atlas_n6 | active 1-entry | header only (cond.1 unmet) |
| atlas n6 canonical baseline | 8 nodes (≠4411) | `atlas_phase46_canonical_nodes.jsonl` 실측 8 (design doc "4411" 추정 incorrect) |

**결정**: bind framework 부재 → **Option A standalone fallback** (handler.hexa + manual / launchd / future bind 등록 가능 인터페이스 유지)

## Deliverables

### 1. handler.hexa
- path: `nexus/tool/handlers/outside_noise_clm_handler.hexa`
- sha: `e59f09a8e188494f99e00e8d994dc322715b98f7`
- LOC: 510
- 컨벤션: `#!hexa strict` + `@tool` + `@sentinel` + `@usage` + `@resolver-bypass` + `@exit_codes`
- exit codes: 0=PASS+ABSORBED, 1=PASS+REJECTED_VALIDATION, 2=CLM_INFERENCE_FAIL, 3=ABSORB_FAIL
- sentinel: `__OUTSIDE_NOISE_CLM__ <PASS|FAIL|REJECT> cycle=<N> primitive_id=<id> validated=<bool>`

### 2. reality_map baseline
- path: `nexus/state/reality_map/cycle_0.jsonl`
- sha: `0fbb11bf85848d99d0ee9f9d96bcd04431a19844`
- node count: **8** (atlas n6 canonical constants: n, phi, tau, sigma, sopfr, mu, J2, M3)
- format: JSONL (HXC v2 binary 미사용 stage0 — text 형식이 inspectable, future migration 가능)

### 3. Validation pipeline (3-check)

| Check | Mechanism | Threshold |
|---|---|---|
| falsifier (`_falsifier_dup_check`) | name 일치 OR jaccard token similarity | sim ≥ 0.85 = duplicate |
| verifier (`_verifier_empirical`) | description 에 measur\|experiment\|observ\|test\|threshold\|recurring 키워드 1+ | required |
| raw 91 honest C3 (`_raw91_honest_c3`) | candidate JSON 의 `honest_c3_pass` field == true | required |

raw#10: jaccard token similarity = embedding cosine 의 stage0 fallback (real embedding 도입 시 anima embed endpoint 호출 필요).

### 4. atlas_absorb_hook integration
- omega_cycle witness JSON emit: `nexus/design/kick/<cycle>_outside_noise_clm_omega_cycle.json`
- `atlas_absorb_hook.hexa` invoked via `_invoke_atlas_absorb_hook` (env `ATLAS_ABSORB_HOOK_DISABLED=1` 안전망 default — live cycle 시 unset)
- 기존 nexus 도구 0 modification

### 5. .roadmap.atlas_n6 auto-emit
- `_emit_roadmap_entry` appends entry: `{"type":"entry","id":"atlas_n6.<primitive_id>","kind":"entry","title":"<name>","status":"absorbed","substrates":["clm","atlas_n6"],"source":"kick_clm_outside_noise_cycle_<N>","contributes_to":["atlas_n6.cond.1"]}`
- 검증: cycle 1 + cycle 4 mock run 후 2 entries appended (확인됨)

### 6. Dispatcher 통합 plan
- **Plan A (bind)**: bind framework 활성 시 `hive bind add outside_noise_kick --module nexus/tool/handlers/outside_noise_clm_handler.hexa --cadence 1h` — **현 시점 N/A (bind absent)**
- **Plan B (standalone, 채택)**: 
  - 직접 호출: `hexa run nexus/tool/handlers/outside_noise_clm_handler.hexa --cycle <N> [--mock|--hf-fallback]`
  - 자동화 옵션 1: launchd plist (1h cadence) — 후속 작업
  - 자동화 옵션 2: future bind framework land 시 즉시 subscribe 가능 (handler interface 호환)

### 7. selftest (5/5 PASS)

```
[outside_noise_clm_handler selftest]
  case1 PASS valid candidate cycle=0 honest=true verifier=true
  case2 PASS duplicate detected for cycle=3 (seed=2)
  case3 PASS honest_c3 falsified for cycle=2 (seed=3)
  case4 PASS verifier rejected non-measurable
  case5 PASS .roadmap.atlas_n6 present
```

mock seed mapping (deterministic):
- cycle 0 → seed 1 → pattern (PASS)
- cycle 1 → seed 0 → law (PASS)
- cycle 2 → seed 3 → honest_c3=false (REJECT honest_c3)
- cycle 3 → seed 2 → duplicate name (REJECT dup if base contains DUPLICATE_BASE_NODE_42)
- cycle 4 → seed 1 → pattern (PASS, gap-jump from cycle_1)

### 8. End-to-end mock cycle verification

| Cycle | Mode | Expected | Result | Reality_map state |
|---|---|---|---|---|
| 1 | --mock | PASS+ABSORB | `__OUTSIDE_NOISE_CLM__ PASS cycle=1 primitive_id=p_c1_law validated=true` | cycle_1.jsonl 9 nodes |
| 2 | --mock | REJECT (honest_c3) | `__OUTSIDE_NOISE_CLM__ REJECT cycle=2 primitive_id=p_c2_concept validated=false reason=verifier;honest_c3;` exit=1 | cycle_2.jsonl 미생성 |
| 4 | --mock | PASS+ABSORB (gap-jump) | `__OUTSIDE_NOISE_CLM__ PASS cycle=4 primitive_id=p_c4_pattern validated=true` | cycle_4.jsonl 10 nodes (cycle_1 inherit + 1) |

Markers emitted (`state/markers/kick_clm_outside_noise_handler_*.marker`): pass_1, reject_2, pass_4 모두 확인.

### 9. Marker
- pattern: `state/markers/kick_clm_outside_noise_handler_<status>_<cycle>_<unix_ts>.marker`
- final landing: `state/markers/kick_clm_outside_noise_impl_landed.marker` (post-handoff)

## raw#10 caveats (7개)

1. **bind framework absent**: design doc Option B 의 핵심 가정 무효 → standalone fallback (Option A). Future bind land 시 즉시 subscribe 가능한 interface 유지함.
2. **anima CLM mac local 미작동 (real)**: `anima_serve_smoke.hexa` = contract-schema stub only. `_local_clm_inference` 는 deterministic template 반환. 실제 inference 는 (a) anima local LoRA endpoint 구축 OR (b) HF gated path (`HUGGINGFACE_API_TOKEN` 필요) — 둘 다 stage1 후속.
3. **4411 base nodes 가정 incorrect**: design doc 의 4411 base nodes 추정 vs. atlas n6 canonical 실측 8 nodes (`atlas_phase46_canonical_nodes.jsonl`). reality_map cycle_0.jsonl = 8 nodes (canonical only), 추가 phase45/47/48 nodes 통합 시 ~2913 lines (실측), 4411 도달은 미확인 source.
4. **jaccard text similarity = embedding fallback**: `_jaccard_similarity` 는 token-set heuristic. real embedding cosine sim 비교 시 false-positive (semantically distinct but lexically similar) 및 false-negative (paraphrased duplicate) 발생 가능 — anima embed endpoint 도입 시 교체.
5. **honest_c3 self-report = LLM hallucination 위험**: candidate JSON 에 `honest_c3_pass:true` 표기는 LLM 자기 보고 → meta-judgment 필요. 현 단계 별도 cross-validator 미구현.
6. **HXC v2 binary 미사용 (text JSONL 사용)**: design doc 의 HXC v2 binary indexed format 대신 JSONL text. 24h 4000 cycle 시 ~5MB/day acceptable, 30d ~150MB. 압축 마이그레이션은 후속.
7. **무한 cycle 방지 미구현**: matching design doc raw#10 caveat #6. 현 handler 는 cycle 별 1-shot, 99% reject rate 시 deceleration 미적용 — launchd cadence 또는 bind cadence 가 외부 throttle 역할 (1h 권장).

## Cross-link

- design doc: `nexus/docs/kick_clm_outside_noise_design_2026_05_02.ai.md` (sha `938ef2ae`)
- handler: `nexus/tool/handlers/outside_noise_clm_handler.hexa` (sha `e59f09a8`)
- baseline: `nexus/state/reality_map/cycle_0.jsonl` (sha `0fbb11bf`)
- atlas hook: `nexus/tool/atlas_absorb_hook.hexa` (unmodified)
- roadmap: `nexus/.roadmap.atlas_n6` (auto-append on absorb)
- raw 91: honest C3 self-report
- raw 99/105/267/269: kick + bind canonical (bind 부재 raw#267 fallback)

## Status / next step

- **status**: stage0 mock + local-stub end-to-end PASS
- **next gates**:
  - (A) anima CLM real inference path (HF gated 또는 local LoRA endpoint)
  - (B) launchd plist 또는 bind framework land 후 cadence subscribe
  - (C) embedding cosine 도입 (jaccard 교체)
  - (D) 100-cycle measurement + cumulative novelty curve (paper-grade evidence)
- **F-CLM-OUT-1..4 falsifiers**: pre-registered in design doc, live cycle 시 측정
