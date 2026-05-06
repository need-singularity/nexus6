# mk2 atlas — recall layer (07)

> 데이터: `n6/atlas.n6` + `discovery/math_atlas.json` (수정 금지)
> 코드:  `mk2_hexa/mk2/src/main.hexa`, `mk2_hexa/mk2/src/atlas/{mod,lookup,hypothesis,recall,distribution,validate}.hexa`
> 갭 SSOT: [`design/hexa_lang_gaps_from_atlas.md`](../../design/hexa_lang_gaps_from_atlas.md)

`mk2 atlas <subcmd>` 는 atlas KB 에 대한 5-way recall 레이어다.
top-level dispatcher (`main.hexa`) → atlas router (`atlas/mod.hexa`) →
5 모듈 (lookup/hypothesis/recall/distribution/validate) 순으로 hexa-lang
서브프로세스 호출 체인을 거친다 (현재 hexa-lang `import` 부재로
in-proc 호출 불가).

---

## 빠른 사용법

```sh
# 환경 (운영 안정성을 위해 필수 — gap subprocess-resolver-env-propagation 참조)
export HEXA_LOCAL=1
export HEXA_RESOLVER_NO_REROUTE=1

# top-level help
hexa run mk2_hexa/mk2/src/main.hexa --help
hexa run mk2_hexa/mk2/src/main.hexa atlas --help

# 각 서브커맨드
hexa run mk2_hexa/mk2/src/main.hexa atlas lookup        <constant>
hexa run mk2_hexa/mk2/src/main.hexa atlas hypothesis    <id|--grade=X|--domain=X|--list>
hexa run mk2_hexa/mk2/src/main.hexa atlas recall        <value> [--sector X] [--top=N]
hexa run mk2_hexa/mk2/src/main.hexa atlas distribution  --by <axis>
hexa run mk2_hexa/mk2/src/main.hexa atlas validate      [path] [--strict] [--quiet]
```

`hive` 차원에서는 `nexus.atlas_lookup` 등 4 caps 진입점으로 호출
(`docs/hive/atlas-recall.md` + `hive.json`).

---

## 5 서브커맨드 — 입출력 예

### 1. `atlas lookup <constant>`

물리 상수 / atlas 토큰 prefix 매칭. 3-stage 경로
(bloom → predict → cold mmap, 본 모듈은 `n6/atlas_query.hexa` 의
grep_fallback 단계 래핑).

**입력**: 상수명 또는 prefix (`alpha_inv`, `Omega_m`, `mp_me` 등).

**stdout**:
```
name:     alpha_inv
formula:  sigma^2 - M3 + phi/(sigma*sopfr)
observed: 137.036
n6_value: 137.0333   err=0.002%
AI:       (2,0)      sector=quantum
---
token:    alpha_inv
matches:  2   (stage: grep_fallback)
sectors:  omega_cycle_dedup-strategy-evolution:2
AI tags:  [7]:2
rec_type: @C:2
---
top 5 entries: ...
```

**stderr** NDJSON: `{"stage":"grep_fallback","duration_ms":N,"matches":N,"token":"<query>"}`

---

### 2. `atlas hypothesis <selector>`

`discovery/math_atlas.json` (700 가설, v1.1 schema) 의 가설 메타
조회. 셀렉터 4 종.

**입력 셀렉터**:
- `<id>` — 정확한 가설 ID (예: `SEDI:H-AF-009`)
- `--grade=<X>` — 등급 필터 (예: `--grade=🟥★★★★`, `--grade=🟧`)
- `--domain=<X>` — 도메인 필터 (예: `--domain=AF`, `--domain=COSMO`)
- `--list` — 전체 700 가설 요약

**stdout**: TSV 1줄/가설 — `id\tgrade\tdomain\ttitle`

**stderr** NDJSON: `{"stage":"<mode>","duration_ms":N,"matches":N,"filter":"<label>"}`

**구현 노트** (2026-05-06 파일럿 패치 적용):
hexa-lang runtime 빌트인 `json_parse` 사용. 기존 awk RS 블록 분리
경로 (~80 줄) 제거, BSD-awk UTF-8 emoji equality bug 자동 해소.
in-process 파싱 → awk fork 0회.

---

### 3. `atlas recall <value> [--sector X] [--top=N]`

수치 → n=6 닫힌 대수 best match. 3 단계 후보 누적 + top-k 정렬:
1. 알려진 12개 매핑 (`sin2_theta_W`, `Omega_m`, `alpha_inv`, ...)
2. `euler_ratio(P)` 와 `1−euler_ratio(P)` — P ⊆ {2,3,5,7,11,13,17,19} (256 마스크)
3. Stern-Brocot 직접 search — 분모 ≤ 200 까지 best rational

**입력**:
- `<value>` — float (예: `0.231`, `0.6847`, `137.036`)
- `--sector X` (옵션) — `cosmology|quantum|electroweak|primordial|strong`
  필터 적용 시 stage 2/3 비활성, 알려진 매핑만 평가
- `--top=N` (옵션, default 3) — 상위 N개 출력

**stdout**:
```
value: 0.231 (sector hint: electroweak)
best:  known:sin2_theta_W[electroweak] = 8/35 = 0.231  err=0%   [euler_ratio({2,3,5,7})]
alt 1: rational(den<=200) = 46/199 = 0.231156  err=0.0673913%
alt 2: euler_ratio({2,3,7,11,17,19}) = 5760/24871 = 0.231595  err=0.256927%
```

**stderr** NDJSON: `{"stage":"recall","duration_ms":N,"value":<v>,"best_err":<rel_err>}`

---

### 4. `atlas distribution --by <axis>`

atlas KB 12,413 entry 의 축별 분포 카운팅.

**입력 축**:
- `--by sector` — 섹터별 (n6atlas / bt / discovery / physics / ...)
- `--by ai` — AI 태그별
- `--by grade` — 등급별
- `--by constant` — 상수명별

**stdout**:
```
axis: sector  total: 12,413
rank  key                              count       pct
   1  n6atlas                               3,379  27.2%
   2  bt                                      751  6.1%
   3  discovery                               728  5.9%
   ...
```

**stderr** NDJSON: `{"stage":"distribution","duration_ms":N,"axis":"<axis>","total":N}`

---

### 5. `atlas validate [path] [--strict] [--quiet]`

`n6/atlas.n6` schema 무결성 전수 점검 (R1..R6 + D1 — 7 룰).
실제 룰 엔진은 standalone tool `tooling/atlas-validator/atlas_validate.hexa`
(read-only data audit, 356 줄). 본 서브커맨드는 그것을 서브프로세스
호출하는 라우터 (~120 LOC) 이며 stdout 을 forward, 자체 stderr meta
`NEXUS_MK2_ATLAS_VALIDATE` 1 라인 emit. 룰 정의 / baseline 통계 /
함정은 [`08-atlas-validate.md`](08-atlas-validate.md) 참조.

**입력**:
- `[path]` — 검증 대상 (positional, 기본 `n6/atlas.n6`)
- `--path PATH` — 명시적 경로 (positional 대안)
- `--strict` — warnings 도 fail (rc=1)
- `--quiet` — per-violation NDJSON 억제, summary 만

**stdout** (per-violation, --quiet 미설정 시):
```json
{"line":123,"sev":"error","rule":"R2","id":"foo_id","detail":"missing_::_separator"}
```

**stdout** (summary 라인, 항상 emit):
```
__ATLAS_VALIDATE__ {"path":"n6/atlas.n6","total":14609,"errors":0,"warnings":1508,"unique_ids":13025,"dup_ids":186,"dup_conflicts":1435,"strict":false,"duration_ms":271}
```

**stderr** NDJSON (router meta):
```
NEXUS_MK2_ATLAS_VALIDATE {"stage":"validate","path":"<path>","total":N,"errors":E,"warnings":W,"duration_ms":D}
```

**Exit code**: 0=ok, 1=violations or (--strict && warnings>0), 2=usage error.

---

## NDJSON meta 스키마 (3 계층)

각 호출은 stderr 에 NDJSON 1 줄을 emit (총 3 줄 — main → atlas →
서브모듈). meta 키 prefix 가 계층마다 고유:

```jsonc
// main.hexa (최외곽)
NEXUS_MK2_DISPATCH {"command":"atlas","rc":0,"duration_us":1114362}

// atlas/mod.hexa (라우터)
NEXUS_MK2_ATLAS_DISPATCH {"subcmd":"hypothesis","rc":0,"duration_us":554950}

// 서브모듈 (lookup / hypothesis / recall / distribution / validate)
{"stage":"grade","duration_ms":25,"matches":1,"filter":"--grade=🟥★★★★"}
NEXUS_MK2_ATLAS_VALIDATE {"stage":"validate","path":"n6/atlas.n6","total":14609,"errors":0,"warnings":1508,"duration_ms":271}
```

스키마:
- `command` (main): `--help` | `atlas` | `classify` | `lattice` | `sector`
- `subcmd` (atlas): `--help` | `lookup` | `hypothesis` | `recall` | `distribution` | `validate`
- `rc`: i64, exit code (0=ok, 1=err, 2=usage)
- `duration_us` / `duration_ms`: 정수, 단위 표기 그대로
- 서브모듈별 추가 필드는 위 5 섹션 참조

---

## Smoke 측정치 (2026-05-05/06, 캐시 워밍 후)

> 환경: `HEXA_LOCAL=1 HEXA_RESOLVER_NO_REROUTE=1`,
> macOS Darwin 25.4.0, hexa 0.1.0-dispatch.
> `inner_ms` = 서브모듈 stage 메타. 외곽 `total_ms` 는 dispatch
> chain (main → mod → 서브모듈) 의 fork+JIT init ~50ms × 3 포함.

| # | 호출 | exit | total_ms | inner_ms | 비고 |
|---|------|------|----------|----------|------|
| 1 | `main.hexa --help` | 0 | 1,512 | 0 | top-level help |
| 2 | `atlas --help` | 0 | 1,969 | 0 | atlas router help |
| 3 | `atlas lookup alpha_inv` | 0 | 3,680 | 1,641 | grep_fallback, 2 matches |
| 4 | `atlas hypothesis --grade=🟥★★★★` | 0 | 1,822 | **25** | json_parse path (pilot 적용 후) |
| 5 | `atlas recall 0.231` | 0 | 5,341 | 35 | 269 candidates, top 3 |
| 6 | `atlas distribution --by sector` | 0 | 7,246 | 3,159 | 12,413 entries → 50+ 섹터 |

### 파일럿 패치 효과 (#4 hypothesis)

| metric | 이전 (awk RS) | 이후 (json_parse) | 비율 |
|---|---|---|---|
| inner stage_ms | 430 | 25 | **17.2× 가속** |
| total_ms | 5,465 | 1,822 | **3.0× 가속** |
| 모듈 LOC | ~213 | ~210 | flat (인라인 함수 추가) |
| awk fork / 호출 | 1 | 0 | 제거 |
| /tmp/.awk 파일 작성 | 1/호출 | 0 | 제거 |
| BSD-awk UTF-8 emoji 위험 | 있음 | 없음 | 자동 해소 |

자세한 갭 분석: [`design/hexa_lang_gaps_from_atlas.md`](../../design/hexa_lang_gaps_from_atlas.md)
의 §`json-stdlib-parser` (Rank 1).

---

## 알려진 행동 / 운영 가이드

### 환경 변수 필수

`mk2 atlas` 호출은 dispatcher 가 자식 hexa 를 spawn 하면서 resolver 를
통과한다. 부모 셸에 `HEXA_LOCAL=1` 과 `HEXA_RESOLVER_NO_REROUTE=1` 둘 다
설정되지 않으면 docker landing 또는 ubu1/ubu2 원격으로 라우팅 시도하다
30초+ hang 가능. 이 동작은 갭으로 등록됨
(`design/hexa_lang_gaps_from_atlas.md` §`subprocess-resolver-env-propagation`).

### 호출 비용

- 콜드 스타트 (캐시 미스): ~5–8s
- 워밍 후: ~1.8–7.2s (subprocess 3 단계 fork + JIT init)
- 서브모듈 in-proc 비용 (inner_ms): 18ms ~ 3.2s (모듈별)

dispatcher 오버헤드의 ~80% 는 hexa-lang `module-import-system` 부재
(서브프로세스 fork)에서 발생. 본 갭이 해소되면 호출당 ~150ms 절감
예상 (`design/hexa_lang_gaps_from_atlas.md` Rank 4 참조).

### 데이터 SSOT

- `n6/atlas.n6` — atlas KB 본체 (수정 금지)
- `discovery/math_atlas.json` — 700 가설 (수정 금지)
- `n6/atlas_query.hexa` — lookup 의 3-stage 경로 SSOT (수정 금지)

위 3 파일은 다른 에이전트 소유 — recall layer 는 인터페이스 계약만
신뢰한다.

---

## 참조

- 아키텍처 다이어그램: [`01-architecture.md`](01-architecture.md) §`mk2::atlas`
- atlas 데이터 스키마: [`05-n6-data-atlas.md`](05-n6-data-atlas.md)
- hive 진입점: [`../hive/atlas-recall.md`](../hive/atlas-recall.md)
- 갭 카탈로그: [`../../design/hexa_lang_gaps_from_atlas.md`](../../design/hexa_lang_gaps_from_atlas.md)
