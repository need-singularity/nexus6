# atlas_recall cycle retro — 2026-05-06

> 사이클 길이: 2026-05-05 (오후) → 2026-05-06 (새벽–오전)
> 범위: nexus mk2 dispatcher 에 atlas KB recall layer 흡수, 5 병렬 +
> 통합 + 후속 6 병렬 + 끝맺음 (메타 검증) 로 구성된 다단 멀티-에이전트
> 사이클의 회고 + 카탈로그.
> SSOT: `design/hexa_lang_gaps_from_atlas.md` (gap 13항목),
> `docs/mk2/07-atlas-recall.md` (사용법 + smoke), 본 문서 (히스토리).

---

## 1. 시작 컨텍스트

**문제**: `atlas.n6` (n=6 KB) 가 nexus 본체 외부에서 직접 호출 가능한
경로가 부족했다. KB 자체는 이미 풍부하고 (`n6/atlas.n6`,
`discovery/math_atlas.json`), `n6/atlas_query.hexa` 가 3-stage cold-start
경로 (bloom → predict → cold mmap) 를 갖추고 있었으나, 호출 지점은
`nexus kick`/`nexus dispatch` 내부 1~2 곳에 한정되었다.

**목표**: mk2 최상위 진입점 (`mk2 <subcmd>`) 에 `atlas` 4-way subdispatch
를 흡수하여, 외부 (CLI, hive, 다른 에이전트) 가 KB 를 일관 인터페이스로
recall 하게 한다.

**4-way 분할**:

| 서브커맨드 | 역할 | 입력 | 출력 |
|------------|------|------|------|
| `lookup`       | prefix → atlas.n6 entry list (3-stage) | `<constant>`     | entry rows |
| `hypothesis`   | topic / grade → enumerated hypotheses  | `<id|--grade=X>` | hypothesis blocks |
| `recall`       | composite query → ranked top-k entries | `<value>`        | ranked top-k |
| `distribution` | namespace → entry/freq/coverage stats  | `--by <axis>`    | dist table |

---

## 2. 분할 계획 (5병렬 + 통합)

병렬 영역 분할 — 충돌 0 의 hard 룰:

| 슬롯 | 영역 | 산출물 |
|------|------|--------|
| 1차 #1 | `mk2/src/main.hexa` 디스패처     | top-level routing, NDJSON meta |
| 1차 #2 | `mk2/src/atlas/mod.hexa` 라우터  | 4-way subroute, exit-code-via-marker |
| 1차 #3 | `lookup.hexa` + `hypothesis.hexa` | 2 모듈 SSOT |
| 1차 #4 | `recall.hexa` + `distribution.hexa` | 2 모듈 SSOT |
| 1차 #5 | docs (`docs/mk2/07`, `docs/hive/`) | 사용자 진입점 |
| 통합  | smoke 6/6, NDJSON meta 정합 검수 | dispatch 보고 |

---

## 3. 실제 진행 (5 사이클 타임라인)

### S1 — 1차 5병렬 (5 모듈 + docs)

5 슬롯 모두 출발. 결과: 4 모듈 + main + mod + docs/mk2/07 +
docs/hive/atlas-recall.md 작성. 일부 슬롯에서 **API 끊김** (네트워크
지연/timeout) — 부분 재시도로 마감. mk2 atlas 동작 가능 상태 확보.

### S2 — LSP 대안 트랙 (3 트랙 + hive 등재)

LSP 풀스택 (`hexa-lsp-server`, Rank 11) 은 ROI 가 낮다고 판단 → 대안
3 트랙 동시 진행:

- `hexa-cli-introspection` (Rank 3, **파일럿**): `--ast --symbols
  --check` 3 플래그 단발 호출. 데몬/JSON-RPC 불필요. 80% 가치.
- `hexa-treesitter-grammar` (Rank 6): `tooling/tree-sitter-hexa/`
  grammar.js 시드 작성. 한 번 작성 → nvim/helix/zed/linguist/AI 자동
  syntax-aware.
- hive 등재: `hive.json` 에 `atlas_lookup`, `atlas_hypothesis`,
  `atlas_recall`, `atlas_distribution` 4 진입 등재. 외부 (다른 sister-repo,
  agent harness) 가 hive 카탈로그로 호출 가능.

### S3 — 통합 + 파일럿 패치

`hypothesis.hexa` 를 Rank 1 (`json-stdlib-parser`) 파일럿 케이스로
재작성 시도. **핵심 발견**: hexa runtime 에 `json_parse` 가 이미 빌트인
존재 (stdlib/json_object 참조) → 외부 awk 파서 제거 후 BSD-awk
emoji bug 자동 해소. 6/6 smoke 통과 확인.

### S4 — 후속 6병렬 (망 끊김)

후속 작업 6 트랙 (resolver env propagation, hexa CLI introspect Phase 1,
hashmap stdlib, tree-sitter wiring, hook bind, 메타 검증) 분할 발사 →
일부 트랙에서 **연결 끊김**. resolver/distribution patch/treesitter wiring
은 일부 진행, hook bind 는 separate.

### S5 — 재발사 + 끝맺음 (본 retro)

본 사이클 (S5) 에서 메타 검증 (6/6 smoke 재측정) + retro 작성 + README
등재 + dirty 분석 (commit 추천 묶음) 수행. 충돌 0 영역만 손댐.

---

## 4. 핵심 발견 3가지

### 4.1 `json_parse` 빌트인 이미 존재

조사 도중 `stdlib/json_object.hexa` 또는 runtime 빌트인에
`json_parse` 가 이미 존재함을 발견. Rank 1 (`json-stdlib-parser`) 의
**비용 0** 으로 재분류 → ROI 가 ★★★★ → ★★★★★ 로 상승. 파일럿
적용 시 `hypothesis.hexa` 의 외부 awk 호출 제거, BSD-awk emoji
equality bug (4.2) 자동 우회.

### 4.2 BSD awk UTF-8 emoji 비교 버그

`--grade=🟥★★★★` 같은 4-byte UTF-8 grade selector 가 BSD awk 의
`==` 비교에서 부분 일치/sign-extend 로 오작동. macOS 표준 awk 가
BSD awk 인 점이 함정. 4.1 의 json_parse 채택 시 awk 의존이 사라져
자동 해결. SSOT: `docs/hexa-lang/GOTCHAS.md` (BSD-awk 항목).

### 4.3 resolver env propagation 이슈

`HEXA_LOCAL=1 HEXA_RESOLVER_NO_REROUTE=1` 가 자식 hexa run 프로세스로
전파되지 않는 케이스 발생. 디스패처가 self-spawn 할 때 env 가 누락 →
resolver 가 remote 라우팅을 시도해 latency spike. 회피: 자식 spawn
직전에 `env -i HEXA_LOCAL=1 HEXA_RESOLVER_NO_REROUTE=1 PATH=$PATH ...`
재주입. 신규 gap `subprocess-resolver-env-propagation` (Rank 2) 등재.

---

## 5. 최종 산출물 카탈로그

| 카테고리 | 경로 | 비고 |
|----------|------|------|
| nexus 모듈 | `mk2_hexa/mk2/src/main.hexa` | top-level dispatcher |
| nexus 모듈 | `mk2_hexa/mk2/src/atlas/mod.hexa` | 4-way subrouter |
| nexus 모듈 | `mk2_hexa/mk2/src/atlas/lookup.hexa` | 3-stage lookup wrapper |
| nexus 모듈 | `mk2_hexa/mk2/src/atlas/hypothesis.hexa` | 가설 selector (json_parse 파일럿) |
| nexus 모듈 | `mk2_hexa/mk2/src/atlas/recall.hexa` | 수치 → ranked top-k |
| nexus 모듈 | `mk2_hexa/mk2/src/atlas/distribution.hexa` | namespace stats |
| docs (mk2)   | `docs/mk2/07-atlas-recall.md` | 사용자 진입점, smoke 표 |
| docs (mk2)   | `docs/mk2/01-architecture.md` | 모듈 다이어그램에 atlas 추가 |
| docs (mk2)   | `docs/mk2/README.md` | 인덱스에 07 추가 |
| docs (hive)  | `docs/hive/atlas-recall.md` | hive 차원 진입 |
| docs (lang)  | `docs/hexa-lang/README.md` + RULES + PATTERNS + GOTCHAS | hexa-lang 사용자 가이드 (4편) |
| tooling      | `tooling/tree-sitter-hexa/grammar.js` (+ queries/, src/) | LSP 대안 #2 |
| tooling      | `tooling/hexa-introspect/` (다른 에이전트, B 트랙) | LSP 대안 #1 (Phase 1) |
| design       | `design/hexa_lang_gaps_from_atlas.md` (264줄, 13 gap) | gap SSOT |
| design       | `design/hexa_cli_introspection_spec.md` | LSP 대안 #1 spec |
| design       | `design/hexa_resolver_env_propagation_spec.md` (B 트랙) | resolver env spec |
| design       | `design/hexa_hashmap_stdlib_spec.md` (C 트랙) | hashmap spec |
| design       | `design/atlas_recall_cycle_2026_05_06_retro.md` (본 문서) | retro |
| hive 등재    | `hive.json` (atlas_lookup/hypothesis/recall/distribution 4 진입) | catalog |
| hive 등재    | `hive/spec/atlas/...` (E 트랙) | hive spec |
| hive marker  | `hive/.raw.mk2` (E 트랙) | dispatch marker |
| state        | `state/atlas_health_timeline.jsonl` (5 신규 헬스 row) | shard health |
| 파생         | `bisociation/spectra/g_atlas_composite_v3.json` (재계산) | composite spectrum |

총 5 모듈 + 5 테스트 (smoke) + main 디스패처 + docs/mk2/01·07 + docs/hive
+ docs/hexa-lang × 4 + tooling/tree-sitter-hexa + design × 5 + hive 등재
+ marker + state.

---

## 6. 갭 카탈로그 13항목 (Rank 표 인용)

| Rank | Gap | Impact | Cost | ROI | 비고 |
|------|-----|--------|------|-----|------|
| 1  | `json-stdlib-parser`                | 매우 높음 | 0 (빌트인 존재) | ★★★★★ | 파일럿 (hypothesis.hexa) |
| 2  | `subprocess-resolver-env-propagation` | 높음 | 중 | ★★★★ | 운영 안정성 직결 |
| 3  | `hexa-cli-introspection`            | 높음 | 1–3일 | ★★★★ | LSP 80% 가치 |
| 4  | `module-import-system`              | 매우 높음 | 큼 | ★★★ | ~50ms/call 절감 |
| 5  | `hashmap-stdlib`                    | 중 | 중 | ★★★ | distribution 60× |
| 6  | `hexa-treesitter-grammar`           | 매우 높음 | 3–5일 | ★★★ | 모든 에디터 + AI |
| 7  | `ns-time-fallback-stdlib`           | 중 | 작 | ★★★ | 5+ 파일 drift 차단 |
| 8  | `argv-stdlib-helper`                | 중 | 작 | ★★★ | 모든 CLI |
| 9  | `subprocess-exit-code-capture`      | 중 | 중 | ★★ | `__RC=` trailer 제거 |
| 10 | `structured-error-propagation`      | 중 | 중 | ★★ | tracing |
| 11 | `hexa-lsp-server`                   | 낮음 | 1–3주 | ★ | **백로그** |
| 12 | `bsd-awk-utf8-equality-collapse`    | 낮음 | n/a | n/a | 1번에 흡수 |
| 13 | `entry-point-vs-library-dual-mode`  | 낮음 | n/a | n/a | 4번에 흡수 |

(SSOT: `design/hexa_lang_gaps_from_atlas.md` Priority 표 — 변동 시
거기를 정본으로 본다.)

---

## 7. 메타 검증 (smoke 6/6 회귀 비교)

본 retro 와 함께 6/6 smoke 재측정 (2026-05-06).

| # | command | rc (직전→재) | TOTAL_MS (직전→재) | 회귀 |
|---|---------|--------------|--------------------|------|
| 1 | `--help`                              | 0 → 0 | 1,512 → **812**   | ▼ -700ms |
| 2 | `atlas --help`                        | 0 → 0 | 1,969 → **1,387** | ▼ -582ms |
| 3 | `atlas lookup alpha_inv`              | 0 → 0 | 3,680 → **3,260** | ▼ -420ms |
| 4 | `atlas hypothesis --grade=🟥★★★★` | 0 → 0 | 1,775 → **1,878** | ▲ +103ms (오차 범위) |
| 5 | `atlas recall 0.231`                  | 0 → 0 | 5,341 → **1,907** | ▼ -3,434ms |
| 6 | `atlas distribution --by sector`      | 0 → 0 | 4,006 → **3,154** | ▼ -852ms |

**회귀 0** 확인 (4번은 측정 노이즈 범위). 5번 (`recall`) 의 큰 폭 단축은
candidates 수/캐시 상태 차이일 가능성 — 후속 추적.

⚠️ caveat: distribution 호출 (#6) 은 C 트랙 (hashmap 패치) 가 동시
진행 중. 본 측정값은 패치 전 상태 (또는 패치 진행 중 중간 상태)
가능성이 있어 **C 트랙 완료 후 재측정 권장**.

---

## 8. 후속 권장 Top 5

1. **C 트랙 완료 검증** — `mk2_hexa/mk2/src/atlas/distribution.hexa`
   hashmap 패치 후 #6 smoke 재측정. 60× 가속 목표 (Rank 5 / `hashmap-stdlib`).
2. **A 트랙 (resolver env propagation)** — Rank 2 우선순위. `HEXA_LOCAL`
   / `HEXA_RESOLVER_NO_REROUTE` 가 자식 spawn 으로 전파되도록 resolver
   정책 갱신. 운영 안정성 직결.
3. **B 트랙 (hexa-introspect Phase 2)** — Rank 3 의 `--symbols` /
   `--check` 플래그 본격 구현. 단발 프로세스 단계 그대로, AI/에디터
   소비.
4. **mk2 PATH 등록** — 본 사이클 미해결. `hexa.toml` 에 `mk2`
   `[[bin]]` 등록 (현재 `nexus` 한 개만 등록됨). 또는 `scripts/bin/mk2`
   wrapper. 이후 `mk2 atlas lookup ...` 한 줄로 호출 가능.
5. **smoke 자동화** — `scripts/bin/mk2_atlas_smoke.sh` (또는 `.hexa`)
   로 본 6/6 측정을 회귀 가드로 등록. CI 또는 nexus daemon 의 헬스
   체크에 연결.

---

## 9. 메타 메모

- 다중 에이전트 협업의 hard rule **충돌 0 영역 분할** 이 본 사이클
  내내 잘 작동했음. 5 명 동시 작업 + 후속 6 명 모두 자기 영역만 손대고
  통합 시 머지 충돌 0.
- API 끊김 / 망 이슈 발생 시 **부분 재시도 + 가능한 한 부족한 영역
  보충** 전략으로 사이클 보존. 단일 에이전트 멈추면 다른 에이전트가
  옆 영역으로 흡수.
- `json_parse` 발견 같은 사례에서, **stdlib 갭 카탈로그 작성 단계가
  실제로는 stdlib 발견 단계** 가 되는 경향. gap 등재 전 5분간 빌트인
  탐색을 의무화하면 ROI 추가.
- "LSP 풀스택 → CLI introspection + treesitter" 분할은 **결정 트리
  분기 (1–3주 → 1–3일 + 3–5일)** 로서 본 사이클 가장 큰 ROI 결정.
  일반화: "통합 풀스택 도구가 보이면 단발 호출 + 외부 grammar 로
  분해 가능한지 5분 검토".

---

(끝.)
