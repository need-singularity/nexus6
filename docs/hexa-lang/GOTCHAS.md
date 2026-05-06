# hexa-lang 함정 모음 — 회피책 SSOT

각 항목: (1) 증상 (2) 근본원인 (3) 회피책. 무시 시 silent false-positive 위험.

---

## 1. BSD awk UTF-8 `==` 비교 collapse (macOS)

**증상**: macOS `/usr/bin/awk` (20200816) 에서 4-byte UTF-8 emoji
(🟥 🟧 🟩 🟦 등) 또는 그 조합 문자열을 `==` 로 비교하면 *모두 0 으로
numeric-coerce* → 모든 emoji 가 모든 emoji 와 같다고 판정. `sprintf`,
`substr`, sentinel-concat (`"|" s "|"`) 도 회피 실패.

**근본원인**: BSD awk 의 string→number 폴백이 invalid byte 시퀀스를
0 으로 변환. 동시에 `==` 가 numeric context 로 강등.

**회피**: byte-level `length` + `index` 결합 — `length()` 와 `index()` 는
정상 동작.

```awk
function streq(a,b){ return length(a)==length(b) && index(a,b)==1 }
# 사용: if(streq(grade, FILT)) ...   ← `==` 절대 직접 사용 금지
```

**카탈로그**: `bsd-awk-utf8-equality-collapse` (design/hexa_lang_gaps_from_atlas.md).

---

## 2. `date +%s%N` literal-N exit-0 (BSD)

**증상**: macOS `date(1)` 는 `%N` 미지원이지만 에러를 내지 않고 `1746...N`
형태 (literal `N` 포함) 를 stdout 으로 emit, exit code 0. `to_int` 가
silent fail → 0 → 모든 duration 이 collapse.

**근본원인**: BSD date 는 unknown format spec 을 verbatim 출력.

**회피**: `_ns_now()` 3-stage fallback — `PATTERNS.md §1`. `raw.contains("N")`
체크가 핵심 sentinel.

---

## 3. `args()` shape 불확실 (HEXA_LOCAL=1)

**증상**: `args()[0]` 이 사용자 인자가 아님. local mode 에서
`[exe, exe, user_arg_1, ...]` (exe 가 두 번 등장).

**근본원인**: hexa-lang 의 launcher wrapping (확정 갭, 카탈로그
`argv-stdlib-helper`).

**회피**: 항상 `a[2]` 부터 사용자 인자로 간주.

```hexa
let a = args()
let mut cmd = "<default>"
if len(a) > 2 { cmd = a[2] }
let user_args = if len(a) > 3 { a[3..] } else { [] }
```

dispatcher 가 token 을 prepend 하는 경우 (예: `mk2 atlas hypothesis`)
는 token-skip 보일러플레이트 추가 필요 (~10줄).

---

## 4. 비교 연산자 `>=` / `<=` 거부

**증상**: `>=` 또는 `<=` 사용 시 컴파일/lint 거부 (모듈 정책).

**회피**: `<` / `>` + 인접 정수 변환.
- `n >= 1`  →  `n > 0`
- `n <= 0`  →  `n < 1`
- `x >= y`  →  `x > y - 1` (정수) 또는 `!(x < y)` (실수)

모든 atlas 모듈 헤더에 `// 규칙: hexa >=/<= 금지` 명시.

---

## 5. 빈 `catch e {}` lint 거부

**증상**: `try { foo() } catch e {}` 처럼 에러 swallow 시 lint 거부.

**회피**: 라인 끝에 `// @allow-silent-catch` 명시 — 의도임을 선언.

```hexa
try { r = to_int(raw) } catch e {}  // @allow-silent-catch
```

대안 (선호): catch 블록에서 `eprintln("module: <ctx>: " + to_string(e))`
또는 sentinel 값 (예: `r = -1`) 설정.

---

## 6. 베어 `exec()` lint 거부

**증상**: 정책 주석 없는 `exec("…")` 호출 시 lint 거부.

**회피**: `// @allow-bare-exec` 주석 부착. 의도가 strict 일 때만 사용 — 가능하면
fixed-arg 헬퍼로 캡슐화.

```hexa
let raw = to_string(exec("date +%s%N 2>/dev/null")).trim()  // @allow-bare-exec
```

---

## 7. 비-0 `exit()` 묵시 종료

**증상**: `exit(1)` 등 사용 시 사용자 메시지 누락 가능성을 lint 가 경고.

**회피**: `// @allow-silent-exit` 주석 (usage 메시지 println 직후 사용).

```hexa
println("usage: ...")
exit(1)  // @allow-silent-exit
```

---

## 8. 모듈 import 부재 → 서브프로세스 50ms

**증상**: 다른 `.hexa` 모듈 호출 시 fork+JIT init 으로 호출당 ~50ms.

**회피**: 동일 프로세스 내 함수로 구조 변경이 가능하면 그렇게.
필수 분리 시 `PATTERNS.md §5` (subprocess + `__RC=` marker) 적용.

dispatcher 가 atlas 류 모듈 4개를 라우팅할 때, hot path 를 합치는
대신 명시적으로 1-call latency budget (~50ms × N) 을 인식.

---

## 9. JSON 파서 부재 → schema 변경 깨짐

**증상**: awk `RS="    }"` 패턴은 4-space-indent pretty JSON 에 hardcode.
컴팩트 JSON / indent 변경 시 즉시 깨짐.

**회피**:
- 데이터 파일 (`discovery/math_atlas.json` 등) 의 indent 정책을 모듈
  헤더에 명시 ("입력은 4-space-indent pretty JSON").
- 가능하면 `jq` 우회 (단 BSD-awk 함정과 무관 — jq 는 emoji 안전).
- 장기: `json_parse()` stdlib 도입 시 awk 우회 일괄 제거.

---

## 10. NDJSON 키 충돌 (중첩 dispatch)

**증상**: parent 가 grep 으로 stderr NDJSON 파싱 시, child 가 같은 키
prefix 를 emit 하면 충돌.

**회피**: 모듈마다 고유 prefix 사용 — `NEXUS_<MODULE>_<EVENT>`. 카탈로그
유지: `NEXUS_ATLAS_QUERY`, `NEXUS_MK2_DISPATCH`,
`NEXUS_MK2_ATLAS_DISPATCH`. 새 모듈 추가 시 SSOT 표 갱신.

---

## 11. `read_file` / `write_file` 권한 silent fail

**증상**: `/tmp/...` 외 경로 또는 다른 사용자 소유 파일 쓰기 시 try/catch
가 swallow → 후속 `exec` 가 빈 출력.

**회피**: write 직후 `if !file_exists(path) { return false }` sentinel.
`PATTERNS.md §10` 의 `write_file → exec` 패턴 참조.
