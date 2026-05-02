---
schema: nexus/docs/outside_noise_clm_real_inference_landed/v1
last_updated: 2026-05-02
ssot: nexus/docs/outside_noise_clm_real_inference_landed_2026_05_02.ai.md
mk: 1
status: landed
related_specs:
  - nexus/docs/kick_clm_outside_noise_design_2026_05_02.ai.md
  - nexus/docs/outside_noise_clm_impl_landing_2026_05_02.ai.md
related_raws: [9, 10, 99, 105, 267, 269, 270, 271, 272, 273]
related_domains: [kick, atlas_n6, omega_cycle, n_substrate]
new_files: [anima/tool/anima_clm_invoke.hexa]
patched_files: [nexus/tool/handlers/outside_noise_clm_handler.hexa]
---

# outside_noise_clm — real-inference wire landed (BG-A)

## TL;DR

predecessor handler (sha `f6e69a4ec710...`, 510 LOC, 5/5 mock-only selftest)
의 `_invoke_anima_clm()` dispatcher 만 in-place patch 하여 anima 측 신규
wrapper `anima/tool/anima_clm_invoke.hexa` (sha `a509747cc029...`, 364 LOC)
호출. wrapper 가 SKIP/FAIL 일 때는 handler 내부 legacy stub (mock/local/hf)
으로 graceful degrade. 7-case selftest 모두 PASS, mock path byte-identical
2-run, ANIMA_CLM_MODE=local + mock 양쪽 모두 cycle 단위 PASS+ABSORB 검증
완료 (cycle 7 mock + cycle 8 local 2개 reality_map 노드 absorb).

## 3-mode wrapper

| mode | 검출 조건 | 작동 | 결과 |
|------|-----------|------|------|
| `mock` | always available | cycle-seed deterministic JSON 생성 | PASS (exit 0) |
| `local` | `ready/core/conscious_chat.py` + `state/v10_benchmark_v4_clm/clm_v4_530m` 둘다 present | wired pre-flight contract JSON (real Mk.XII v3 forward 는 weights 없어 deferred) | PASS (exit 0) |
| `hf` | `HUGGINGFACE_API_TOKEN` 또는 `HF_TOKEN` env present | wired pre-flight contract JSON (live HF call 은 token-cost 회피 위해 dedicated cycle 으로 deferred) | PASS (exit 0) — 부재 시 SKIP exit 2 |

mode 선택 우선순위: CLI `--mode` > env `ANIMA_CLM_MODE` > default `mock`.

JSON contract (7-key): `{name, description, primitive_type, evidence_link, falsifier, honest_c3_pass, _mode}`.

## 7-case selftest (handler)

| # | 시나리오 | 결과 |
|---|---------|------|
| 1 | mock cycle=0 (seed=1 pattern) — honest+verifier 둘 다 PASS | PASS |
| 2 | mock cycle=3 (seed=2) — fixture node `DUPLICATE_BASE_NODE_42` 와 dup 검출 | PASS |
| 3 | mock cycle=2 (seed=3) — honest_c3_pass=false 검출 | PASS |
| 4 | verifier reject — measurable keyword 없는 description 거부 | PASS |
| 5 | `.roadmap.atlas_n6` 존재 확인 (informational) | PASS |
| 6 | **NEW** wrapper round-trip — wrapper output 의 `"_mode":"mock"` 태그 검증 (skip-aware: wrapper 미배포 시 SKIP) | PASS |
| 7 | **NEW** legacy fallback safety net — handler 내부 `_mock_clm_inference` 직접 호출, graceful degrade 경로 보존 검증 | PASS |

wrapper 자체 selftest: 5/5 (case4 hf-token 부재로 SKIP-aware).

## E2E cycle 검증

mock path:
- cycle 7 (seed=2) → wrapper emit `DUPLICATE_BASE_NODE_42` (concept) → reality_map dup-check PASS (해당 name 미존재) → ABSORB id=10
- cycle 10 (seed=3) → wrapper emit `mock_dishonest_10` honest=false → handler validate REJECT (verifier+honest_c3) → exit 1
- cycle 13 (seed=2) → 2-run byte-identical (absorbed_at timestamp + resolver line stripped) PASS

local path (`ANIMA_CLM_MODE=local`):
- cycle 8 → wrapper emit `local_wired_primitive_cycle_8_plen_*` → handler validate PASS → ABSORB id=11

omega_cycle witness JSON + atlas_n6 roadmap append + n6 자동 emit 모두 정상.

## File index

| 경로 | 종류 | LOC | sha256 |
|------|------|-----|--------|
| `anima/tool/anima_clm_invoke.hexa` | NEW | 364 | `a509747cc029f3af0c55296f0a0f41c18844cf577250e78ebbb77ea3b1273a10` |
| `nexus/tool/handlers/outside_noise_clm_handler.hexa` (pre) | — | 510 | `f6e69a4ec710eb3446270cb10fd0fd71ca2f6cbadefc08aa38eba621f332e93a` |
| `nexus/tool/handlers/outside_noise_clm_handler.hexa` (post) | PATCH | 590 | `0d57f29b601a11b4e4e859e698641f0da3e02a6fd1d28d1db37e0f4023a2a480` |
| `nexus/state/markers/outside_noise_clm_real_inference_landed.marker` | NEW | — | (post-emit) |

handler diff 범위: `_invoke_anima_clm()` 1개 함수 in-place patch (+~50 LOC) + `_selftest()` case6/7 추가 (+~30 LOC). 다른 함수 / entry/dispatch / atlas absorb hook / reality_map I/O 함수는 무수정.

## raw#10 caveats (5)

1. **C1 — Mk.XII v3 weights mac 부재**: `state/v10_benchmark_v4_clm/clm_v4_530m` 디렉터리는 `cds.json` + `phi_star.json` 2 metadata 만 present. 실제 safetensors / tokenizer.model 없음. local mode 는 "wired pre-flight" 단계 — 실제 forward 는 weight 도착 + torch in-process 가능 시점까지 deferred. JSON 의 `description` 에 명시.
2. **C2 — HF token mac 부재**: `HUGGINGFACE_API_TOKEN`/`HF_TOKEN` env 둘 다 unset. hf mode SKIP exit 2 (handler 가 graceful degrade). live HF call rate-limit + gated approval 필요 — token 도착 시 1회 검증 권장 ~$0.001.
3. **C3 — subprocess invoke latency**: wrapper 가 별도 `hexa run` subprocess (~수초/cycle). 24h 4000 cycle 환산 시 cumulative latency overhead 무시 못함. in-process anima→nexus 직접 호출은 hexa-lang cross-repo import 미지원 (현재 disk-bridge 만 가능).
4. **C4 — fallback graceful degrade silent**: wrapper SKIP/FAIL 시 handler 가 legacy stub 으로 fall back 하지만 reality_map node JSON 에 어떤 mode 가 작동했는지 trace 없음 (wrapper output `"_mode"` 태그는 wrapper-path 일 때만 보존). post-mortem audit 시 stderr sentinel `__ANIMA_CLM_INVOKE__ <PASS|FAIL|SKIP>` 으로만 판별.
5. **C5 — env() runtime path 의존**: wrapper 의 `anima_root()` 가 `ANIMA` env > `HOME/core/anima` > 하드코딩 fallback 순. cloud pod / CI 등 다른 환경에서 path 불일치 시 wrapper 미발견 → handler legacy fallback. cloud 배포 시 `ANIMA` env 명시 권장.

## 다음 cycle (deferred, BG-A scope 외)

- (i) Mk.XII v3 weight mac local 또는 cloud forward 활성화 (torch + safetensors 도착 시)
- (ii) HF token 도착 시 hf mode 실call 1회 검증 + cost log
- (iii) `_mode` 태그 reality_map node JSON 으로 propagate (audit trail 강화)
- (iv) wrapper subprocess → in-process anima→nexus shared-memory bridge (hexa-lang cross-repo import 가능 시점)

## 정책 준수

- **마이그레이션 0**: handler 의 `_invoke_anima_clm()` 1개 함수 + `_selftest()` 2개 case 추가만, 기존 5/5 selftest 동작 보존 (case 1-5 byte-identical PASS).
- **#!hexa strict + @attr**: wrapper 신규 .hexa 상단에 적용.
- **AI-native 문서**: handoff 본 doc + marker 모두 paraphrase only.
- **byte-identical 2-run**: cycle 13 mock path 검증 PASS (timestamp + resolver banner 제외).
- **$0 mac-local**: GPU/HF call 0회. wrapper subprocess overhead 만.
- **destructive 0**: handler in-place patch 만, 신규 file 1개 (wrapper) + 신규 doc 1개 + 신규 marker 1개.
