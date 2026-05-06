---
schema: nexus/docs/check/ai-native/1
last_updated: 2026-05-05
ssot:
  entry:           engine/nexus_cli.hexa  cmd_check
  router:          tool/check_router.hexa
  backends:
    - tool/check_physics.hexa
  spec:            engine/nexus_cli_spec.json#subcmds_check.check
  recursive_spec:  n6/docs/meta_atlas_recursive.md
  witness_log:     n6/atlas.append.check-*.n6
  wrapper_patch:   bin/nexus-cli  HEXA_LOCAL=1 force-local for "check"
audience: AI + operator
---

# nexus check — multi-domain verification

## Canonical CLI

```sh
nexus check [domain flags] [sub flags] [--quiet] [--json]
```

분야 옵션은 다중 OR 결합. 미지정 시 `--all`.

## Why

수학/물리/의식/Φ/현상학/법칙/무결성/메타 등 13 분야 검증을 단일 진입점으로. 각 분야 backend 가 sentinel 로 결과를 보고하면 router 가 집계해 메타 sentinel 출력. 분야 매트릭스는 `core, module, ai-native doc` 재귀 3-tier 와 Tarski strict hierarchy (`n6/docs/meta_atlas_recursive.md`) 를 준수.

## Domain matrix (14)

| 옵션 | 분야 | 출처 / 상태 |
|---|---|---|
| `--math` | 수학 | invariants_drift, absolute, hyperarithmetic (stub) |
| `--physics` | 물리 | dimensional + conservation 자체구현, anchor/codata/planck/lorentz wrap ✅ |
| `--bio` | 바이오 | stub |
| `--sim` | 시뮬 | sim_bridge/anu_time/, stub |
| `--qrng` | 양자난수 | ANU 분포, stub |
| `--brain` | 뇌 | ~/core/hexa-brain 외부, stub |
| `--consciousness` | 의식 | ANIMA AN11 11-axis 흡수 예정 |
| `--phi` | Φ/IIT | ANIMA phi_holo/phi_iit 흡수 예정 |
| `--learning` | 학습 정합성 | ANIMA corpus_4gate 흡수 예정 |
| `--phenomenology` | 현상학 | ANIMA EEG cross-substrate 흡수 예정 |
| `--law` | 법칙/수렴 | ANIMA consciousness_laws 흡수 예정 |
| `--integrity` | 무결성 | ANIMA cert_gate/nexus_gate 흡수 예정 |
| `--meta` | 메타 | n6 honesty_triad + atlas_drift, stub |
| `--hexalint` | hexa-lint | tree-sitter-hexa lints.scm AST 룰 (relop/exec/catch/exit) ✅ |

ANIMA 흡수 정책: 정적 검증 ~15-18개 → `tool/check_<domain>.hexa` 로 이관 (별도 PR).

## Sub-flag matrix (분야 내 세부)

```
--dimensional    물리 — 차원 분석 (SI 7-axis)
--conservation   물리 — energy/momentum/angular-L 보존 (0.1% ppm 임계)
--anchor         물리 — empirical_anchor χ² (n_s, m_π, M_chirp, α⁻¹)
--codata         물리 — CODATA NIST live fetch
--planck         물리 — Planck 2018 6-parameter
--lorentz        물리/시뮬 — 64-site light-cone causality
--invariants     수학/메타 — n6 10-atom drift
--honesty        메타 — honesty_triad C1~C5
--drift          메타 — atlas_drift
--all-physics    physics 내 세부 전체 (네트워크 포함)
```

## Dispatch chain

```
nexus check <opts>
  → bin/nexus-cli  (HEXA_LOCAL=1 forced for "check")
  → engine/nexus_cli.hexa  cmd_check
      ↳ pack args into HEXA_ARGV
      ↳ exec hexa run tool/check_router.hexa
  → tool/check_router.hexa
      ↳ select domains (multi-OR; default --all)
      ↳ filter forwarding sub-flags
      ↳ for each domain:
          file_exists check_<domain>.hexa? → SKIP if not
          else: exec backend with HEXA_ARGV=<sub_flags>
                parse __NEXUS_CHECK_<DOMAIN>__ sentinel
      ↳ aggregate
  → backend (e.g., tool/check_physics.hexa)
      ↳ run dimensional / conservation
      ↳ wrap anchor/codata/planck/lorentz (existing tools)
      ↳ emit __NEXUS_CHECK_PHYS__ <PASS|FAIL> dim=... cons=...
  → router emits __NEXUS_CHECK__ <PASS|FAIL> dom1=... dom2=...
```

## Sentinel

```
__NEXUS_CHECK__ <PASS|FAIL> math=<R> physics=<R> bio=<R> sim=<R> qrng=<R> brain=<R> consciousness=<R> phi=<R> learning=<R> phenomenology=<R> law=<R> integrity=<R> meta=<R>
```
- `R ∈ {PASS, FAIL, SKIP}` per domain
- 백엔드 자체 sentinel: `__NEXUS_CHECK_PHYS__ <PASS|FAIL> dim=<R> cons=<R> anchor=<R> codata=<R> planck=<R> lorentz=<R>`
- exit `0`=PASS, `1`=usage/IO, `2`=verify FAIL

## Recursive 3-tier compliance

`n6/docs/meta_atlas_recursive.md` 의 Tarski strict hierarchy 매핑:

| Tier | 위치 | 역할 |
|---|---|---|
| **core** (Level 0) | `engine/nexus_cli.hexa` `cmd_check` | dispatcher, audit_log, atlas.n6 witness 입구 |
| **module** | `tool/check_router.hexa` + `tool/check_<domain>.hexa` | 분야 fan-out + 백엔드 검증 로직 |
| **ai-native doc** | 본 문서 (`docs/nexus_check.ai.md`) | AI/operator 가독 spec |

재귀 layer 매핑:
- **Level 0 (atlas.n6)**: 검증 결과 witness 가 `atlas.append.check-*.n6` 으로 append 가능 (현재 미wire, 차후)
- **Level 1 (meta_atlas.n6)**: 분야별 PASS율·횟수가 메타엔트리 후보 (`@M CHECK_PASS_RATIO_PHYSICS = ...`)
- **Level 2+ (meta²_atlas+)**: deferred (자동화 미정)

각 layer 는 strict 하위만 언급 — Russell 회피, Tarski hierarchy 보존.

## Examples

```sh
nexus check                              # 전체 분야
nexus check --physics                    # 물리 분야 전체
nexus check --physics --conservation     # 물리 내 보존만
nexus check --math --physics             # 두 분야
nexus check --physics --all-physics      # 물리 내 세부 전체 (네트워크 포함)
nexus check --quiet                      # sentinel 만 stdout
```

## Falsifiers

1. router 가 새 도메인 추가 → spec.json `domain_flags` 동기화 누락 → spec_drift_lint
2. 백엔드 sentinel 형식 (`__NEXUS_CHECK_<DOMAIN>__`) 미준수 → router 가 FAIL 보고
3. exit code 0 인데 sentinel FAIL (또는 그 반대) → contract_violation
4. ANIMA 정적 자산 이관 시 출처 attribution 누락 → migration_provenance
5. nested hexa exec 가 원격 라우팅 → backend hexa not found → 반드시 HEXA_LOCAL=1
6. backend 추가 시 ai-native doc 의 Domain matrix / Dispatch chain 갱신 누락 → doc_drift

## Migration policy

- 분야 backend 미존재 → router 가 SKIP graceful 처리, 종합 PASS 영향 없음
- ANIMA 정적 자산 이관 (별도 PR): consciousness/phi/learning/phenomenology/law/integrity 6 분야 backend wire
- hexa-brain 외부 sibling (별도 PR): `_sibling("hexa-brain", "tool/...")` 패턴
- 신규 분야 추가 시 동시 갱신 필수: spec.json + router DOMAINS[] + 본 문서 Domain matrix

## Idempotency

- selftest (dimensional/conservation 자체구현) 은 결정론 — 같은 입력 = 같은 출력
- 네트워크 wrap (codata/planck) 은 외부 서비스 응답 의존 — `--no-fetch` 옵션은 backend 가 보유

## See also

- `n6/docs/meta_atlas_recursive.md` (재귀 spec SSOT)
- `engine/nexus_cli_spec.json#subcmds_check.check` (subcommand spec)
- `tool/empirical_anchor.hexa`, `tool/codata_bridge.hexa`, `tool/cmb_planck_bridge.hexa` (재사용 자산)
- `lib/n6_honesty/honesty_triad.hexa` (sentinel 규약 모범)
- `docs/nexus_kick_mk2.ai.md` (ai-native doc 형식 참조)
