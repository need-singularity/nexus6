# hexa-rules — 즉석 룰 카드

> **DSL**: hexa-lang (nexus 내부)
> **컴파일러**: `hexa run <file.hexa> [args...]` (위치: `~/.hx/bin/hexa`)
> **확장자**: `.hexa`
> **SSOT 레퍼런스**: `n6/atlas_query.hexa`, `mk2_hexa/mk2/src/atlas/*.hexa`

---

## 사용 시점 (auto-invoke)

다음 중 하나라도 해당하면 본 룰을 즉시 적용한다 (어떤 AI 에이전트든):

- 사용자가 `.hexa` 파일을 작성/수정 요청 (read-only inspect 는 제외)
- 사용자 메시지에 `hexa`, `hexa-lang`, `hexa run` 키워드 등장
- 작업 경로가 `mk2_hexa/`, `n6/`, `hexa-lang/`, `shared/n6/`, `drill/`, `scripts/*.hexa` 안
- 컴파일러/언어 갭 토론 (예: "stdlib JSON 파서가 없어서…")

---

## 핵심 룰 (위반 시 컴파일/논리 오류)

1. **비교 연산자**: `>=` / `<=` **사용 금지** — `<` / `>` 만 사용.
   - 모든 atlas 모듈 헤더에 명시: `// 규칙: hexa >=/<= 금지 — <` / `>` 만 사용.`
   - 회피: `n < 1` 대신 `n <= 0` 쓰지 말 것. `if x < 1` / `if x > 0` 으로 표현.

2. **stdlib only**: Rust, python, jq 등 외부 의존 금지가 기본 (`exec()` 호출은 허용되나 정책 주석 필수).

3. **`exec()` 호출 정책**: 베어 `exec("...")` 는 lint 가 거부. 라인 끝에
   `// @allow-bare-exec` 주석을 붙여 명시적으로 허용한다.

4. **`try/catch` silent swallow**: `try { ... } catch e {}` 빈 catch 도 lint
   거부. 라인 끝에 `// @allow-silent-catch` 명시.

5. **`exit(n)` (n != 0)**: 묵시적 종료는 `// @allow-silent-exit` 주석으로
   명시 (CLI 사용성 메시지 출력 후 사용 한정).

6. **`args()` shape**: local mode (`HEXA_LOCAL=1`) 에서 `[exe, exe, user_arg_1, ...]`.
   사용자 인자는 `a[2]` 부터 시작한다. (`argv-stdlib-helper` 갭 — 참조: `design/hexa_lang_gaps_from_atlas.md`)

7. **모듈 시스템 부재**: `import` / `mod` 미지원. 다른 `.hexa` 호출은
   `exec("hexa run <path> -- <args>; echo __RC=$?")` + stdout 마커 패턴.
   부모는 `to_string(exec(...)).index_of("__RC=")` 로 exit code 회수.

8. **JSON 파서 부재**: `json_parse()` 없음. awk `RS="    }"` (4-space-indent
   pretty JSON) 블록 분리 + 라인 정규식이 표준 우회. (BSD-awk emoji 함정 주의 — `GOTCHAS.md`)

9. **HashMap 부재**: 평행 배열 `let keys: [string] = []; let vals: [i64] = []`
   + `index_of` 선형 탐색이 표준 우회.

10. **ns clock**: `date +%s%N` 은 macOS BSD `date(1)` 미지원 (literal `…N` 출력).
    3-stage fallback 필수 — `PATTERNS.md` 의 `_ns_now()` SSOT 복붙.

---

## 헤더 주석 컨벤션 (모듈 SSOT)

모든 `.hexa` 모듈은 `═` 박스 헤더로 다음을 명시:

```hexa
// ═══════════════════════════════════════════════════════════
// <path/to/module.hexa> — <한 줄 책임>
//
// 배경: <왜 이 모듈이 존재하는가>
// 설계: <핵심 알고리즘/3-stage/...>
// 인터페이스: fn run(args: [string]) -> i32  (0=ok, 1=err)
// stdout: <포맷>
// stderr: NDJSON {"stage":..., "duration_ms":N, ...}
// 규칙: hexa >=/<= 금지 — < / > 만 사용. stdlib only.
// 편집 금지: <다른 에이전트 소유 파일 목록>
// ═══════════════════════════════════════════════════════════
```

`stderr` 메타 NDJSON 키는 모듈마다 고유 prefix:
- `NEXUS_ATLAS_QUERY {...}` — `n6/atlas_query.hexa`
- `NEXUS_MK2_DISPATCH {...}` — `mk2_hexa/mk2/src/main.hexa`
- `NEXUS_MK2_ATLAS_DISPATCH {...}` — `mk2_hexa/mk2/src/atlas/mod.hexa`

---

## 관용구 / 갭 / 함정 (요약 — 상세는 자매 파일)

- 자주 쓰는 패턴 (ns-time, mtime, shell-escape, awk 호출, NDJSON emit, bucket parse): `PATTERNS.md`
- 함정 (BSD awk emoji 비교, exec 권한, args shape, RS multi-byte): `GOTCHAS.md`

---

## 현재 stdlib 갭 (확인된 우회 필요 항목)

| 갭 | 우회법 (현재 SSOT) | 카탈로그 |
|---|---|---|
| `import` / module system | `exec("hexa run …; echo __RC=$?")` + stdout marker | `module-import-system` |
| 사용자 argv 헬퍼 | `let user = args(); use a[2..]` | `argv-stdlib-helper` |
| subprocess exit code | `__RC=` trailer in stdout | `subprocess-exit-code-capture` |
| 구조화 에러 전파 | ad-hoc NDJSON `NEXUS_<NS>_<EVENT>` to stderr | `structured-error-propagation` |
| `if @is_main` | 별도 main.hexa 가 dispatch() 를 서브프로세스 호출 | `entry-point-vs-library-dual-mode` |
| JSON 파서 | awk `RS="    }"` 블록 + 라인 정규식 | `json-stdlib-parser` |
| HashMap | 평행배열 `[string]+[i64]` + 선형 탐색 | (미카탈로그) |
| ns clock | 3-stage fallback (`%s%N` → python3 → `%s`*1e9) | (확장 카탈로그 필요) |
| hex 파싱 | awk `hx["0"]=0; hx["1"]=1; …; hx["f"]=15` 룩업 | (`atlas_query.hexa:91-95`) |
| BSD-awk UTF-8 `==` | `length(a)==length(b) && index(a,b)==1` (streq) | `bsd-awk-utf8-equality-collapse` |

전체 카탈로그: `design/hexa_lang_gaps_from_atlas.md` (편집 금지 — 다른 에이전트 영역).

---

## 작업 시작 전 체크리스트

1. 대상 파일이 `mk2_hexa/`, `n6/`, `design/`, `docs/mk2/`, `hexa-lang/` 등
   다른 에이전트 소유 영역인가? → **직접 수정 금지**, 인터페이스 계약만 신뢰.
2. 헤더 박스 주석에 "편집 금지" 목록이 있나? → 그대로 따른다.
3. 비교 연산자에 `>=` / `<=` 가 있나? → `<` / `>` 로 즉시 교체.
4. 새 `exec()` / 빈 `catch` / 비-0 `exit()` 추가 시 정책 주석 부착.
5. 신규 `_ns_now()` 가 필요하면 `PATTERNS.md` SSOT 그대로 복붙 (3-stage 누락 금지).
6. 신규 awk 스크립트가 UTF-8 비교를 한다면 `streq` 함수 정의 + 사용.

---

## 검증

작성/수정 후:

```sh
hexa run <file.hexa> --help          # smoke
hexa run <file.hexa> <typical-args>  # 1-shot
```

stderr 의 NDJSON 메타가 1줄로 emit 되는지, exit code 가 의도한 값인지 확인.
