# 08 — atlas validate (n6 schema 무결성 검증)

> 작성: 2026-05-06 | 도구: `tooling/atlas-validator/atlas_validate.hexa`
> 데이터 SSOT: `n6/atlas.n6` (read-only — 본 도구는 절대 수정 안함)
> mk2 dispatch: `mk2 atlas validate` 서브커맨드 등록 완료 (2026-05-06,
> 라우터: `mk2_hexa/mk2/src/atlas/validate.hexa` ~120 LOC, subprocess
> pattern; SSOT 룰 엔진은 본 standalone tool 그대로 유지).

---

## 1. 목적

`atlas.n6` 은 nexus 의 가장 큰 KB (14,609 records, 43,387 lines, 2.8MB).
write-time 가드 (`shared/blowup/lib/atlas_guard.hexa.inc` — 3 write site 골화)
는 신규 entry 의 schema 만 검사하나, **read-time / standalone audit** 는
부재였다. 본 도구는 atlas.n6 첫 데이터 보호 레이어로:

- atlas.n6 schema (v1) 정합성 전수 점검
- 중복 id 의 conflicting RHS 검출 (silent corruption 조기 감지)
- CI / pre-commit hook 통합 가능한 deterministic check (LLM 무관)

---

## 2. 사용법

```sh
export HEXA_LOCAL=1     # local exec 강제 (docker 우회)

# 기본: n6/atlas.n6 검증, NDJSON violation + summary stdout
hexa run tooling/atlas-validator/atlas_validate.hexa

# 요약만
hexa run tooling/atlas-validator/atlas_validate.hexa --quiet

# strict — warning 도 fail
hexa run tooling/atlas-validator/atlas_validate.hexa --strict

# 대체 경로
hexa run tooling/atlas-validator/atlas_validate.hexa --path /tmp/atlas_shard.n6
```

### Exit code

| code | 의미 |
|------|------|
| 0 | errors == 0 (warnings 무관, 단 `--strict` 면 warnings == 0 도 필요) |
| 1 | errors > 0 또는 (`--strict` && warnings > 0) |
| 2 | usage error (atlas.n6 부재, awk write 실패 등) |

---

## 3. 검증 룰 (R1..R6 + D1)

각 룰의 위반은 NDJSON 1라인:

```json
{"line":N,"sev":"error|warning","rule":"<id>","id":"<entry_id>","detail":"<reason>"}
```

| 룰 | 등급 | 설명 |
|----|------|------|
| **R1** | warning | type token whitelist (`@P/@C/@L/@F/@R/@S/@X/@?`) — v1 정의. `@E`, `@M`, `@T` 등은 unknown_type 로 warning. |
| **R2** | error | `:: ` separator 필수 |
| **R3** | error/warn | grade bracket `[...]` 필수 (없음 = error). 내부 형식 `<digits>(.<digits>)?[*!?]*` 또는 modifier-extended 가 아니면 warning. |
| **R4** | error | id token 필수 (`[A-Za-z0-9_:.-]+`) |
| **R5** | error | domain non-empty (`::` 와 `[` 사이 텍스트) |
| **R6** | warning | line length < 4096 bytes (UTF-8 byte count) |
| **D1** | warning | duplicate id 의 RHS conflict (같은 id 가 다른 expression 으로 N>1 회 등장) |

### 룰 추가 정책

- 신규 룰은 `_write_main_awk()` 또는 `_write_dup_awk()` 에 라인 추가 + 본 표 1행 추가.
- error/warning 등급은 **policy 결정**: error = 즉시 차단, warning = 보고만.

---

## 4. 출력 스키마

### 4.1 per-violation NDJSON (stdout)

```json
{"line":123,"sev":"error","rule":"R2","id":"foo_id","detail":"missing_::_separator"}
{"line":456,"sev":"warning","rule":"D1","id":"dup_id","detail":"dup_conflict_first@123"}
```

### 4.2 summary line (stdout)

```
__ATLAS_VALIDATE__ {"path":"n6/atlas.n6","total":N,"errors":E,"warnings":W,"unique_ids":U,"dup_ids":D,"dup_conflicts":C,"strict":bool,"duration_ms":T}
```

### 4.3 stderr meta NDJSON

```
NEXUS_ATLAS_VALIDATE {"path":"...","total":N,"errors":E,"warnings":W,"duration_ms":T}
```

---

## 5. 현재 atlas.n6 baseline (2026-05-06)

```
__ATLAS_VALIDATE__ {"path":"n6/atlas.n6","total":14609,"errors":0,"warnings":1508,
                    "unique_ids":13025,"dup_ids":186,"dup_conflicts":1435,
                    "strict":false,"duration_ms":271}
```

### 5.1 warning 분포

| rule | 건수 | 의미 |
|------|------|------|
| D1   | 1,435 | dup id + 다른 RHS — 정상 (BT-snapshot 누적, 같은 id 가 시간차 갱신됨) |
| R3   | 66 | nonstd grade (예: `[N?]`, `[N!]` — N 은 literal "N" 을 grade tier 로 사용 — UFO/MILL/HEXA-CLOAK 류) |
| R1   | 7 | `@E` (Edge/Bridge) — v2 type. 본격 통과는 v2 reader 도입 후 처리. |

### 5.2 error 분포

**0건** — atlas.n6 v1 schema 는 errors-clean (write-time guard 효력).

---

## 6. 함정 / 회피

### 6.1 BSD-awk UTF-8 abort
atlas.n6 line 21924 의 emoji partial byte 는 BSD `/usr/bin/awk` 의 `towc`
변환을 abort 시킨다 (`multibyte conversion failure`). **회피**:
`LANG=C LC_ALL=C awk` prefix — byte-level 처리 모드로 강제.
(GOTCHAS.md §1 / `bsd-awk-utf8-equality-collapse` 카탈로그)

### 6.2 docker-route 환경 차이
`hexa run` 기본은 `docker` 라우팅 (`route=docker reason=mac_safe_landing`).
docker 컨테이너에는 `n6/atlas.n6` 이 mount 되지 않으므로, 본 도구는
**`HEXA_LOCAL=1` 강제**가 필요하다. 운영 환경 (CI 등) 은 wrapper 에서
환경변수 prepend.

### 6.3 grade 형식 spec 모호성
v2 grammar (`design/atlas_v2_grammar.md`) 는 compound grade (`[10*PASS_LITERATURE]`
등) 도 valid 로 취급하나 v1 reader 는 `[\d+(\.\d+)?[*!?]?]` 만 strict OK.
본 validator 는 절충: extended modifier 형식 (`[10*ALPHANUM]`) 도 silent 통과,
완전 비표준 (`[BADGRADE]`) 만 warning.

---

## 7. mk2 dispatch 등록 (완료, 2026-05-06)

본 도구는 이제 두 경로 모두 가용:

- **standalone**: `hexa run tooling/atlas-validator/atlas_validate.hexa [opts]`
  (룰 엔진 SSOT, 356 LOC, R1..R6 + D1)
- **dispatch**: `mk2 atlas validate [path] [--strict] [--quiet]`
  (라우터 `mk2_hexa/mk2/src/atlas/validate.hexa` ~120 LOC, subprocess
  + `__RC=$?` trailer 패턴; sticky resolver env prefix 자동 부착)

등록 결과:
1. `mk2_hexa/mk2/src/atlas/validate.hexa` — 라우터 (subprocess 패턴) 신규.
2. `mk2_hexa/mk2/src/atlas/mod.hexa` — `_SUBCMDS` 4→5, `_help_text` 1줄 추가.
3. `mk2_hexa/mk2/src/main.hexa` — atlas 서브커맨드 enumeration 1줄 갱신.
4. `mk2_hexa/mk2/tests/test_atlas_validate.hexa` — 4 @test (default/nonexistent/strict/help) PASS.
5. smoke: `tooling/smoke/mk2_atlas_smoke.sh` (5 subcmds + 2 help = 7/7 PASS).
6. `docs/mk2/07-atlas-recall.md` § 5 (validate 서브커맨드 입출력 예) 추가.

NDJSON 키:
- standalone: `NEXUS_ATLAS_VALIDATE` (stderr 1라인) + `__ATLAS_VALIDATE__` (stdout 요약)
- dispatch:   `NEXUS_MK2_ATLAS_VALIDATE` (router stderr 1라인, 위에 더해)
  → 두 줄 모두 stderr emit, parent 가 둘 다 수확 가능.

---

## 8. 룰 vs spec 갭

`design/atlas_v2_grammar.md` v2 spec 은 본 validator (v1) 보다 strict —
신규 type (`@M`, `@T`), compound grade, deprecation marker 등. v2 reader
도입 시 본 validator 도 v2 룰 추가 필요 (`R7` deprecation, `R8` lineage 등).

현재 status: **v1 baseline only**. v2 비호환 entry 는 R1 warning 으로 표면화.

### 8.1 R7 (deprecation) 후보 사양 (2026-05-06)

`design/atlas_v2_grammar.md` § 3.5 deprecation marker 가 정식화될 때 추가.

**검출 형식 (예상):**
- `@D <id> :: <domain> [grade] :: <reason>` — 명시적 deprecation entry
- 또는 `@P <id> :: <domain> [grade!?] DEPRECATED::<successor_id>` — inline marker

**룰:**
- R7 (warning): deprecated entry 가 다른 entry 의 `derives_from` / `references` 필드에서 참조됨 → "broken lineage to deprecated"
- R7-strict (error in `--strict`): live grade (`[10*]` 등) 이면서 deprecation marker → "live deprecated entry"

### 8.2 R8 (lineage `@T` trace) 후보 사양

`design/atlas_v2_grammar.md` § 3.4 신규 type `@T trace` (ω-cycle audit lineage).

**검출 형식 (예상):**
- `@T <cycle_id> :: <fact_id> :: <witness_path>` — fact-emission lineage
- `@T` entry 의 `<fact_id>` 가 atlas.n6 안에 존재해야 정합

**룰:**
- R8 (warning): `@T` entry 의 `fact_id` 가 atlas.n6 의 다른 entry id 와 매칭 안 됨 → "orphan trace"
- R8-strict: `@T` 의 `witness_path` 가 디스크에 부재 (`!file_exists`) → "missing witness"

### 8.3 v2 reader 도입 후 작업 (구현 후속)

1. `tooling/atlas-validator/atlas_validate.hexa` 의 awk 룰 엔진에 R7/R8 추가
2. fixtures: `_fixtures/violations_v2.n6` 작성 (의도적 R7/R8 위반)
3. selftest 갱신 (R7/R8 fire 확인)
4. 문서 § 1 룰 표 업데이트 (R1-R8)
5. 갭 카탈로그 `atlas-n6-schema-validator` entry 에 v2 룰 적용 한 줄
