# hexa-lang gaps surfaced by mk2 atlas dispatcher (2026-05-05)

본 문서는 `mk2 atlas <subcmd>` 디스패처 구현 (mk2_hexa/mk2/src/main.hexa,
mk2_hexa/mk2/src/atlas/mod.hexa) 도중 발견된 hexa-lang stdlib/언어 gap
모음. 각 항목은 (1) 모듈 (2) 현재 workaround (3) 제안 stdlib API (4)
예상 임팩트 형식.

---

## module-import-system

- module: dispatch (mk2 main + atlas/mod)
- workaround: `exec("hexa run <path> <args>; echo __RC=$?")` 서브프로세스
  + stdout 마커로 exit code 회수 (~50ms 오버헤드/호출, fork+jit init)
- proposed stdlib API:
    ```hexa
    import "path/to/file.hexa" as M
    let rc: i32 = M.run(args)
    ```
  또는 더 보수적으로 `mod` 키워드 + 동일 패키지 file 트리 자동 발견.
- estimated impact: 호출당 ~50ms 절약 (atlas dispatch 의 dominant cost),
  메모리 공유 (n6/atlas.n6 mmap 재사용), 디스패처 코드 ~30 줄 단순화,
  exit-code-via-stdout-marker hack 제거.

---

## argv-stdlib-helper

- module: main (top-level CLI)
- workaround: `args()` 가 [exe, exe, user_arg_1, user_arg_2, ...] 형태
  (local) → 각 스크립트가 `let user = a[2..]` 슬라이싱을 직접 작성.
  hexa run 모드에 따라 인덱스가 다를 위험 있음 (확인된 mismatch 없음).
- proposed stdlib API:
    ```hexa
    let argv = std::env::user_args()    // 사용자 인자만 반환
    let prog = std::env::program_name() // mk2 / atlas_query / ...
    ```
- estimated impact: 모든 CLI 스크립트 (n6/atlas_query.hexa,
  scripts/atlas_sync_remote.hexa, mk2/main.hexa 등) 의 argv 슬라이싱
  보일러플레이트 제거 + 실행 모드 (local/remote/test) 간 인덱스
  불일치 위험 차단.

---

## subprocess-exit-code-capture

- module: dispatch (any hexa script that shells out to another hexa)
- workaround: shell 명령 끝에 `; echo "__RC=$?"` trailer 부착, parent 가
  `to_string(exec(...)).index_of("__RC=")` 로 추출 후 `to_int`. trailer
  누락 시 보수적으로 1 반환 (silent miss 위험).
- proposed stdlib API:
    ```hexa
    let res = std::process::run("hexa", ["run", path, ...args])
    res.stdout : string
    res.stderr : string
    res.exit_code : i32
    ```
- estimated impact: dispatcher 코드 ~10 줄 (trailer 추출 로직) 제거,
  stdout 데이터 안에 우연히 `__RC=` 가 포함될 때의 falsepositive 차단,
  stderr 와 stdout 분리 캡처 가능 → meta NDJSON 충돌 회피.

---

## structured-error-propagation

- module: dispatch + n6/atlas_query
- workaround: 모듈마다 임의의 NDJSON 키 (`NEXUS_ATLAS_QUERY`,
  `NEXUS_MK2_DISPATCH`, `NEXUS_MK2_ATLAS_DISPATCH`) 를 stderr 에 단일
  라인으로 emit, parent 는 grep 으로 파싱. 중첩 호출 시 키 충돌 위험.
- proposed stdlib API:
    ```hexa
    std::diag::emit("namespace.event", {key: value, ...})
    // 자동으로 nesting depth + parent_namespace 부착
    ```
- estimated impact: 다층 dispatch (mk2 → atlas → lookup → mmap_lookup)
  의 trace 가 자동 정렬, 호출 그래프 재구성 가능, ad-hoc NDJSON 규약
  일관화.

---

## entry-point-vs-library-dual-mode

- module: atlas/mod.hexa
- workaround: `dispatch(argv)` 함수와 top-level CLI 두 모드를 한 파일에
  두려면 `if main { ... }` 가드가 필요한데 hexa 에 없음 → 현재는
  dispatch() 만 정의하고 main.hexa 가 서브프로세스로 호출 (위 gap 1
  과 동일 원인).
- proposed stdlib API:
    ```hexa
    if @is_main {
        exit(dispatch(args()))
    }
    ```
- estimated impact: lookup/hypothesis/recall/distribution 4 모듈이
  CLI 와 라이브러리 두 역할을 동시에 수행 가능 → 통합 단계에서
  module-import 가 도입되면 즉시 in-proc 호출로 전환.

---

## json-stdlib-parser

- module: hypothesis (`mk2_hexa/mk2/src/atlas/hypothesis.hexa`)
- workaround: awk `RS="    }"` 블록 분리 + 라인 단위 정규식
  (`/"id": "[^"]*"/` 등). 4-space indent 의 pretty-printed JSON 형식에
  하드코딩 → schema/format 변경 시 즉시 깨짐. jq 가용해도 다음 항목
  (BSD-awk emoji bug) 회피 위해 awk 함수 사용은 동일 필요.
- proposed stdlib API:
    ```hexa
    fn json_parse(src: string) -> JsonValue
    fn json_load(path: string) -> JsonValue
    // .get("hypotheses").as_array() → [JsonValue]
    // .get("grade").as_string()
    ```
- estimated impact: hypothesis.hexa 코드 ~50% 단축
  (`_write_awk_script` + `_awk_filter` 50줄 → 10줄 in-process),
  호출당 ~30ms 절약 (awk fork + script-write 회피), schema 내성 확보,
  BSD-awk emoji 이슈 자동 해소.

---

## bsd-awk-utf8-equality-collapse

- module: hypothesis (and any awk-based UTF-8 string consumer)
- 현상: macOS BSD awk (`/usr/bin/awk` 20200816) 가 4-byte UTF-8
  코드포인트 (🟥 🟧 🟩 🟦 등) 또는 그 조합 문자열을 `==` 비교 시
  numeric-coerce 하여 *모두 0* 으로 만들어 false-positive equality
  ("모든 emoji 가 모든 emoji 와 같음"). `sprintf`, `substr`,
  sentinel-concat (`"|" s "|"`) 모두 회피 실패. 단 `index()` / `length()`
  는 byte-level 정상 동작.
- workaround: awk 함수
    ```awk
    function streq(a,b){ return length(a)==length(b) && index(a,b)==1 }
    ```
- proposed mitigation:
  - hexa 가 native string equality 만 사용 (awk 미경유) →
    `json-stdlib-parser` 도입 시 자동 해소
  - 또는 hexa stdlib 에 `awk_streq()` SSOT helper 제공
- estimated impact: hypothesis 모듈에서 발견했지만 atlas/* awk
  기반 모듈 모두 잠재 영향. 실측 1시간 디버깅 손실 회피
  (필자 첫 구현이 `==` 사용 → 모든 grade 가 동일 매칭하는 false-positive
  로 멀쩡한 것처럼 동작 → 결과 카운트로만 발견).

---

## arg-vector-shape-uncertainty (already noted as `argv-stdlib-helper`,
   복수 모듈 confirmation)

- 추가 확인 (hypothesis): `args()` = `[exe, exe, user_arg_1, ...]`
  (local mode, HEXA_LOCAL=1) — atlas_query.hexa 와 동일 관습
  (`a[2]` 부터 사용자 인자) 검증됨. dispatcher 가 `atlas hypothesis`
  를 prepend 한 경우를 위해 token-skip 보일러플레이트 추가됨
  (~10 줄). 4 모듈 통합 시 SSOT 가 절실.

---

## subprocess-resolver-env-propagation (NEW — surfaced 2026-05-05 smoke)

- module: dispatch (mk2 main + atlas/mod) — 통합 smoke 도중 발견.
- 현상: 부모가 `exec("hexa run …")` 으로 자식 hexa 를 spawn 할 때
  자식 프로세스의 hexa wrapper 가 `HEXA_RESOLVER_*` env 를 *재해석*
  하면서 docker/remote 라우팅을 다시 시도. 부모 셸에 `HEXA_LOCAL=1`
  과 `HEXA_RESOLVER_NO_REROUTE=1` 둘 다 설정되어 있어야 풀-스택이
  로컬에서 안정 실행됨. 원격 라우터 (ubu1/ubu2) 또는 docker landing
  이 unhealthy 일 때 atlas dispatch 가 30초+ 행함.
- workaround (현재 SSOT):
    ```sh
    HEXA_LOCAL=1 HEXA_RESOLVER_NO_REROUTE=1 hexa run mk2_hexa/mk2/src/main.hexa atlas <subcmd> ...
    ```
  smoke 측정치: env 설정 후 6/6 통과, 1.5s ~ 7.2s 범위.
- proposed stdlib API:
    ```hexa
    let res = std::process::run("hexa", ["run", path, ...args],
                                {env_inherit: false, route: "local"})
    ```
  또는 hexa-resolver 가 `HEXA_PARENT_LOCAL=1` 같은 inherit-once flag 인식.
- estimated impact: nexus 의 모든 self-spawn dispatcher (atlas, n6,
  drill, scripts/atlas_sync_remote 등) 가 unsupervised mode 에서도
  안정. 현재는 운영자가 매번 wrapper 셸에서 env 를 export 해야 함.
- Track 1 (resolver patch, 2026-05-06): `~/.hx/bin/hexa` 에 opt-in
  `HEXA_RESOLVER_INHERIT_ENV=1` 추가 (+11 lines). caller 가 1번만 set
  하면 모든 grandchild resolver 가 short-circuit. 측정: 41.6s → 3.27s
  (5–13×). 상세: `design/hexa_resolver_env_propagation_spec.md` § 1-6.
- Track 2 (mod.hexa sticky, 2026-05-06): `mk2_hexa/mk2/src/atlas/mod.hexa::_exec_module`
  가 자체적으로 `HEXA_LOCAL=${…:-1} HEXA_RESOLVER_NO_REROUTE=${…:-1}
  HEXA_RESOLVER_INHERIT_ENV=${…:-1}` prefix 부착 (+17 lines, 어노테이션
  `@allow-bare-exec @resolver-bypass(reason="…")`). 호출자 fingerprint
  0 — env 미설정 시 sticky 1, override 시 caller 우선. smoke 6/6 PASS,
  duration 1.03–2.79s, 출력 형식 100% 보존. 상세: spec § 7.

---

## hashmap-stdlib (RESOLVED 2026-05-06 — runtime 빌트인 채택)

- module: distribution (`mk2_hexa/mk2/src/atlas/distribution.hexa`)
- 검증 결과 (2026-05-06): hexa 런타임에 **map 리터럴 `#{}` + 빌트인
  메서드** (`m.has(k)`, `m[k]` index assign/read, `m.keys()`,
  `m.values()`) 가 이미 존재. `self/stdlib/map.hexa` 는 편의 래퍼만
  제공하고 핵심 연산은 인터프리터 빌트인. JSON 파서 케이스와 동일 —
  카탈로그 추정과 달리 type-checker 막힘은 없으며 `let mut m = #{}`
  만으로 동작. 참조: `self/stdlib/map.hexa:17`,
  `test/regression/map_has_method.hexa`.
- workaround (이전): 평행배열 `[string] + [i64]` + `_kv_index` 선형
  탐색 헬퍼 정의는 있었으나 distribution.hexa 의 실제 hot path 는
  awk pre-aggregate 후 push-only 였음. 진짜 dominant cost 는 awk
  서브프로세스 (atlas.n6 13k 라인 × 2 패스 = 1.6–2.0s) + `_total_for`
  의 두 번째 awk 스캔.
- 패치 (2026-05-06): 4 axis 모두 `#{}` 맵 리터럴 in-process 집계로
  전환. sector/constant 의 무거운 awk 패스 제거 (`read_file` +
  line iter), grade/ai 의 sed/awk 카운트 파이프라인도 hexa-side
  로 이전 (awk 는 정규식 추출만 담당). `_by_<axis>` 가 out_total
  out-param 으로 1-pass 집계 → `_total_for` 두 번째 스캔 제거.
  Smoke test 결과 동일 (sector rank-1 = `n6atlas`/3,379, grade
  🟥★★★★=1, 🟧★=131, ai top 3 rows, totals
  12413/703/667/14609 모두 보존).
- 측정 (HEXA_LOCAL=1, NDJSON `duration_ms`):
  | axis     | 이전 (ms) | 이후 (ms) | speedup |
  |----------|-----------|-----------|---------|
  | sector   |    1,828  |       57  | 32×     |
  | grade    |      108  |       44  |  2.5×   |
  | ai       |       87  |       41  |  2.1×   |
  | constant |    1,981  |       54  | 37×     |
- pattern (SSOT — 다른 모듈 적용 시 복붙):
    ```hexa
    let mut counts = #{}
    while i < n {
        let key = ...                                  // axis-specific
        let cur = if counts.has(key) { counts[key] } else { 0 }
        counts[key] = cur + 1
        i = i + 1
    }
    // 정렬용 평행 배열로 flatten
    let ks = counts.keys(); let vs = counts.values()
    ```
- 잔여 작업 없음. 카탈로그 Rank 5 closed (= json-stdlib-parser 패턴
  재현: 카탈로그 추정과 달리 빌트인이 이미 충분, 모듈 측 패턴만 갱신).

---

## ns-time-fallback-stdlib (NEW — 5 모듈 중복)

- module: 모든 atlas 모듈 (lookup, hypothesis, recall, distribution, mod)
  + main.hexa + n6/atlas_query.hexa.
- workaround: `_ns_now()` 함수가 5+ 파일에 동일 3-stage 폴백
  (`date +%s%N` → `python3 time.time_ns()` → `date +%s` * 1e9) 으로
  복붙됨. 한 곳을 고치면 5+ 곳 동기화 필요 (drift risk 실증됨 —
  recall.hexa 는 `r < 1` 사용, 다른 모듈은 `r <= 0` 사용 → 룰 위반
  이슈).
- proposed stdlib API: 기존 `time.hexa` (있다면) 또는 새로
    ```hexa
    fn ns_now() -> i64    // monotonic, 3-stage fallback in C runtime
    fn epoch_ns() -> i64  // realtime
    ```
- estimated impact: 5+ 파일 × 12 줄 중복 → 1 builtin 호출. drift 차단.
- lint applied (2026-05-06): `hive_claude_hook_bind/module/hexa_lint_ns_time.hexa` (300+줄, 38 fixtures, sentinel `__BIND_HEXA_LINT_NS_TIME_SELFTEST__ PASS`) blocks new `_?ns_now`/`*ns_clock` defs missing 3-stage SSOT — atlas+n6 7-모듈 e2e ALLOW, single-stage 합성 BLOCK.

---

## Priority (post-cycle action items)

| Rank | Gap | Impact | Cost | ROI | 비고 |
|------|-----|--------|------|-----|------|
| 1 | `json-stdlib-parser` | 매우 높음 (hypothesis 50% 단축, BSD-awk emoji bug 자동 해소, 다수 sister-repo 영향) | **0** (이미 runtime 빌트인 `json_parse` 존재 — stdlib/json_object.hexa 참조) | ★★★★★ | 본 사이클 파일럿 패치 대상 (hypothesis.hexa 재작성). |
| 2 | `subprocess-resolver-env-propagation` | 높음 (모든 self-spawn dispatcher) | 중 (resolver 정책 변경) | ★★★★ | 운영 안정성 직결. workaround 명확. |
| 3 | `hexa-cli-introspection` (NEW) | 높음 (LSP 80% 가치) | 1–3일 | ★★★★ | `hexa --ast --symbols --check`. 데몬/protocol 불필요. 단발 호출로 AI/에디터 둘 다 커버. |
| 4 | `module-import-system` | 매우 높음 (~50ms/call 절감, dispatcher 30줄 단순화) | 큼 (언어 spec 변경) | ★★★ | 호출당 latency dominant. exit-code-via-stdout-marker hack 제거. |
| 5 | `hashmap-stdlib` | 중 (distribution 32–37× 가속, 측정) | **0** (빌트인 `#{}` + `.has`/`.keys`/`.values` 이미 존재) | ★★★ | **RESOLVED 2026-05-06** — distribution.hexa 4 axis 패치 완료. |
| 6 | `hexa-treesitter-grammar` (NEW) | 매우 높음 (모든 에디터 + AI) | 3–5일 | ★★★ | tree-sitter 시드. 일반화된 syntax 카탈로그. |
| 7 | `ns-time-fallback-stdlib` (NEW) | 중 (5+ 파일 drift 차단) | 작 (C runtime 한 함수) | ★★★ | 빠른 실행. |
| 8 | `argv-stdlib-helper` | 중 (모든 CLI 스크립트) | 작 | ★★★ | local/remote shape 통일. |
| 9 | `subprocess-exit-code-capture` | 중 (dispatcher 안전성) | 중 | ★★ | `__RC=` trailer 제거. |
| 10 | `structured-error-propagation` | 중 (tracing) | 중 | ★★ | 다층 호출 trace 자동 정렬. |
| 11 | `hexa-lsp-server` (NEW) | 낮음 (혼자 쓰면 ROI 작음) | 1–3주 | ★ | 풀 LSP. **백로그**. 3번이 80% 가치를 더 싸게 제공. **2026-05-06 분석**: `hexa lsp` JSON-RPC 서버가 이미 존재 (`self/lsp.hexa` 792줄, initialize/semanticTokens 정상; hover/definition/rename 본문 스텁). 보강만 0.5–1일 — `design/hexa_parser_loc_injection_spec.md` § 6 참조. **2026-05-06 land**: hover/definition/rename 본문 채움 + `_dispatch_message`/`run_lsp_from_buffer` 멀티-메시지 처리 + `json_get_string` perf 재작성. lsp.hexa 792→1247줄. ASCII 소스 검증 OK (`/tmp/lsp_verify.hexa` `_ns_now` 사용→정의 점프, rename 3 occurrences). 잔여 갭: `\uXXXX` JSON 디코드 미구현 (박스드로잉/CJK 소스 line/col 어긋남). 자세한 결과는 `hexa_parser_loc_injection_spec.md` § 7.2. **2026-05-06 후속**: `\uXXXX` BMP decode 추가 (lsp.hexa +31, `from_char_code` 1-/2-/3-byte UTF-8). initialize 회귀 0. **STATUS UPDATE 2026-05-06 14:00**: Phase 4-LSP 풀구현 적용 완료. lsp.hexa 823→996 (+173). word_at_position + find_symbol + find_all_occurrences 신규 + handle_definition/hover/rename 본문 채움. `hexa parse` OK, initialize 회귀 0. workspace rename + find_all perf 는 별도 사이클. |
| 12 | `bsd-awk-utf8-equality-collapse` | 낮음 (`json-stdlib-parser` 채택 시 자동 해소) | n/a | n/a | 1번에 흡수. |
| 13 | `entry-point-vs-library-dual-mode` | 낮음 (`module-import-system` 도입 시 의미 있음) | n/a | n/a | 4번에 흡수. |

### 추가 등재 (LSP 대안 트랙)

- **hexa-cli-introspection** (Rank 3): `hexa --ast file.hexa`,
  `hexa --symbols file.hexa`, `hexa --check file.hexa` 3 플래그.
  단발 프로세스 → 데몬/JSON-RPC 불필요. 에디터 (Vim ALE, Emacs
  flycheck) 와 AI 모두 stdout 으로 결과 소비. 비용 1–3일,
  full LSP 의 ~80% 효용. **2026-05-06 Phase 2 완료** — wrapper
  `tooling/hexa-introspect/hexa_introspect.hexa` (877→1417 lines)
  에 6 룰 (HX001 banned-gte / HX002 bare-exec / HX003 silent-catch
  / HX004 awk-utf8-eq / HX005 rc-trailer-missing / HX006 argv-slice-bare)
  작동, atlas 갭 6/6 매핑 검증, atlas 4/5 PASS + n6/atlas_query 진성
  hits 3 검출, `--strict` 시 위반 1+ exit 1.
- **hexa-treesitter-grammar** (Rank 6): `tooling/tree-sitter-hexa/`
  에 grammar.js 시드. 한 번 작성하면 nvim, helix, zed,
  GitHub linguist, AI training set 모두 자동 syntax-aware.
  비용 3–5일. **2026-05-06 wiring**: `nexus check --hexalint`
  도메인으로 통합 — `tool/check_hexalint.hexa` 가 `tooling/hexa-lint/lints_via_treesitter.hexa`
  (tree-sitter CLI shim) 을 호출하여 lints.scm 5 룰 (relop-banned /
  bare-exec / silent-catch / silent-exit / nested-call-exec) AST 매칭.
  CI/manual batch lint, sentinel `__NEXUS_CHECK_HEXA_LINT__`.
  **2026-05-06 후속**: `design/hexa_token_taxonomy_unified_spec.md` —
  highlights.scm capture (18) ↔ LSP semanticTokens (15) 통합 spec,
  SSOT = LSP 표준, cross-editor (VS Code / Neovim / Helix / Zed) 색칠 일관성.
  **2026-05-06 D 트랙 적용**: token taxonomy 코드 변경 5/6 적용 (boolean
  keyword 흡수 / `@function.builtin` SSOT builtins.list / `decorator` 노드
  grammar.js / `@type` 사용자 타입 분리 / `@comment.note` 패턴 확장),
  `tree-sitter test` 12/12 PASS (9 baseline + 3 신규).
- **hexa-lsp-server** (Rank 11): 풀 LSP 서버 (textDocument/...,
  semantic tokens, diagnostics, hover, completion). 비용 1–3주.
  단일 사용자 (혼자) 쓰는 동안 ROI 작아 **백로그**. Rank 3
  채택이 우선.

### 사이클 마무리 (2026-05-05/06)

본 사이클에서 처리:
- ★★★★★ Rank 1 (`json-stdlib-parser`) — hypothesis.hexa 파일럿 패치 시도.
- 카탈로그 정리: 4 NEW 항목 (`subprocess-resolver-env-propagation`,
  `hashmap-stdlib`, `ns-time-fallback-stdlib`, `hexa-cli-introspection`,
  `hexa-treesitter-grammar`, `hexa-lsp-server`).
- smoke 통과: 6/6 (`HEXA_LOCAL=1 HEXA_RESOLVER_NO_REROUTE=1` 환경).

### NEW: `hexa-lint-pre-write-hook` (2026-05-06)

- 갭 ID: `hexa-lint-pre-write-hook`
- 현 상태: **부분 가용** — 7 룰 PreWrite gate 가동 (relop, bare-exec, silent-exit, silent-catch, header-box, bsd-awk-utf8, ns-time).
  manifest: `hive/packages/hive-claude-hook-bus/claude.manifest.hook.json`
  PreToolUse phase chain (no-lineage-citation-pre-write 직후, permission-gate
  직전 구간). 모듈 + sentinel:
  - `hexa_lint_relop` — `>=`/`<=` 사용 금지.
    모듈: `hive/hive-claude-hook-bind/module/hexa_lint_relop.hexa` (240 lines).
    sentinel: `__BIND_HEXA_LINT_RELOP_SELFTEST__ PASS`.
    per-line escape `// @allow-relop-banned`, per-file escape
    `// @allow-relop-banned-file` (head 30 lines), env bypass
    `HIVE_HEXA_LINT_RELOP_DISABLE=1`.
  - `hexa_lint_bare_exec` — `exec(...)` 호출 정책 주석 의무 (NEW 2026-05-06).
    모듈: `hive/hive-claude-hook-bind/module/hexa_lint_bare_exec.hexa` (316 lines).
    sentinel: `__BIND_HEXA_LINT_BARE_EXEC_SELFTEST__ PASS`.
    per-line escape `// @allow-bare-exec` (±5 row neighborhood), per-file
    escape `// @allow-bare-exec-file` (head 30 lines), env bypass
    `HIVE_HEXA_LINT_BARE_EXEC_DISABLE=1`. atlas 5 모듈 (lookup, distribution,
    hypothesis, recall, mod) PASS — 기존 `// @allow-bare-exec` 주석 100% 호환.
  - `hexa_lint_silent_exit` — `exec(...)` rc 무검증 차단 (NEW 2026-05-06,
    patch-mode). 모듈: `hive/hive-claude-hook-bind/module/hexa_lint_silent_exit.hexa`
    (408 lines). sentinel: `__BIND_HEXA_LINT_SILENT_EXIT_SELFTEST__ PASS`.
    rc-inspection tokens: `.code`, `.rc`, `__RC=`, `== 0`, `!= 0`, `< 1`, `> 0`
    (lookahead 8 rows). per-line escape `// @allow-silent-exit` (±5 row),
    per-file escape `// @allow-silent-exit-file` (head 30), env bypass
    `HIVE_HEXA_LINT_SILENT_EXIT_DISABLE=1`. registry/main/manifest 등재는
    `hive/hive-claude-hook-bind/SILENT_EXIT_PATCH.md` 절차로 deferred (bare-exec
    동시 수정 충돌 회피용 patch-mode — 21→22 완료 후 22→23 적용).
  - `hexa_lint_ns_time` — `_?ns_now`/`*ns_clock` 함수 정의시 3-stage fallback
    SSOT 미부착 차단 (NEW 2026-05-06, patch-mode). 모듈:
    `hive/hive-claude-hook-bind/module/hexa_lint_ns_time.hexa` (300+ lines).
    sentinel: `__BIND_HEXA_LINT_NS_TIME_SELFTEST__ PASS` (38 fixtures).
    stage tokens: stage-1 `date +%s%N`, stage-2 `python3` ∧ `time_ns`,
    stage-3 `date +%s` (단독, %N 비-suffix). fn name match: `_?ns_now`
    또는 `*ns_clock` suffix. body lookahead 64 rows (brace-depth 추적).
    per-fn escape `// @allow-incomplete-ns-fallback` (±5 row), per-file
    escape `// @allow-incomplete-ns-fallback-file` (head 30), env bypass
    `HIVE_HEXA_LINT_NS_TIME_DISABLE=1`. atlas+n6 7-모듈 e2e ALLOW
    (atlas_query, hypothesis, distribution, lookup, recall, mod, main),
    single-stage 합성 BLOCK. registry/main/manifest 등재는
    `hive/hive-claude-hook-bind/NS_TIME_PATCH.md` 절차로 deferred
    (chain 26 도달 후 26→27 적용).
- bind aggregate sentinel: `__HIVE_CLAUDE_HOOK_BIND__ PASS handlers=22`.
  Phase 2 hexa-introspect `--check` 트랙 동시 작업 — informational scan
  (CI/manual) 대 real-time enforcement (write 차단) 로 차별화.
- 후속 wiring 후보 룰 (RULES.md §2–§6 미구현분):
  1. ~~`bare-exec-policy`~~ — 완료 (2026-05-06).
  2. `silent-exit-policy` — `// @allow-silent-exit` 없는 비-0 `exit(n)` 차단.
  3. `silent-catch-policy` — `// @allow-silent-catch` 없는 빈 `catch e {}` 차단.
  4. `header-box-required` — atlas/주요 모듈 SSOT 헤더 박스 (`═` 라인) 누락 차단.
  5. `bsd-awk-utf8-equality-required` — awk 스크립트에서 `==` UTF-8 비교 시
     `streq` 헬퍼 미정의 차단.
  6. ~~`ns-time-fallback-required`~~ — 모듈 작성 완료 (2026-05-06,
     patch-mode). 신규 `_?ns_now`/`*ns_clock` 정의의 3-stage fallback 패턴
     SSOT 미부착 차단. 등재는 `NS_TIME_PATCH.md` 절차 (chain 26→27).
- 권장 순서 (남은 룰): 2 → 3 → 4 → 5 (ns-time 은 6번이지만 모듈 단계 완료).
- 패턴: `hexa_lint_relop.hexa` / `hexa_lint_bare_exec.hexa` 를 카피해
  `_hxlr_*` / `_hxbe_*` 헬퍼만 갈아끼우면 90% 재사용. string-literal/comment
  stripper (`_hxXX_strip_comment_and_string`) 는 SSOT 로 별도 추출 권장
  (다음 룰부터 공통 의존). bare-exec 가 신설한 `±5 line neighborhood scan` +
  prefix-disambiguator (`_hxbe_has_line_escape_excl_file`) 도
  silent-exit/catch 룰이 그대로 재사용 가능.

### NEW: `hexa-ast-diff-semantic-refactor` (2026-05-06)

- 갭 ID: `hexa-ast-diff-semantic-refactor`
- 현 상태: **Phase 5a 구현 + dispatch 적용 완료** (2026-05-06) —
  `tooling/hexa-introspect/diff.hexa` (952줄, single-file symbol-hash
  diff) + dispatch patch 적용 (`hexa_introspect.hexa` `--diff` 분기 + bin
  shim mode whitelist). body_hash 정규화 (signature strip + 주석/
  whitespace 제거 + shasum/FNV 폴백), name × kind × sig × body_hash
  4-키 매칭, rename heuristic (body_hash 일치 또는 Jaccard ≥ 0.85). 7개
  pair 검증 ✓ (rename fixture, self-control, atlas 5 모듈 페어). dispatch
  검증 (2026-05-06): `hexa-introspect --diff sample.hexa sample.hexa` →
  7 unchanged; `--diff sample.hexa sample_rename.hexa` → 6 unchanged + 1
  renamed (greet→hail body_hash_match) + 1 added (_clock_ns). **Phase 5b
  구현 완료** (2026-05-06) — `tooling/hexa-introspect/refactor.hexa` (996줄,
  신규 entry-point, 5a `diff.hexa` 와 분리). 4 모드: `--diff-rename`
  (Phase 3 `--refs` 호출처 영향), `--diff-sig` (compat 5종 분류:
  breaking_added_required_param / breaking_removed_param /
  breaking_return_type_change / compatible_added_optional_param /
  compatible_param_renamed), `--apply --dry-run` (NDJSON 변경 plan,
  실제 적용 미수행), `--emit-edit --format=lsp` (LSP `WorkspaceEdit`
  단일 JSON, jq 파싱 ✓). 12개 검증 페어 통과 (sample fixtures 5개 +
  atlas mod×validate 19 변경 + diff.hexa 952줄 self-rename ref_count=4).
  **Phase 5c 구현 완료** (2026-05-06) — `tooling/hexa-introspect/gumtree.hexa`
  (1515줄, 신규 entry-point, 5a/5b 와 분리). 4 모드: `--diff-tree` (GumTree
  3-pass tree-edit: top-down hash + bottom-up dice ≥ 50% + parent-anchored
  type-only update), `--extract` (line range → 새 fn, free_vars = identifier
  set 차분, 타입 i64 디폴트 + caveat), `--inline` (호출처 lexical scan + param
  substitute + last-return unwrap, caveat lexical), `--move` (a → b 추출/삽입,
  b 부재 시 create_file:true, callers grep 하여 import 갱신은 5b workspace
  edit 위임). atlas/lookup self-control 327/327 매칭 false-positive 0,
  rename fixture greet→hail 단일 update 액션, sig fixture body 변경 update
  2건 (PASS 3 leaf 차분 압축). dispatch patch md 분리 (`PHASE5C_DISPATCH_PATCH.md`).
  Phase 5d 후속 (`_descendants` 캐싱, scope tree, alpha-rename, caller-import
  자동 갱신, type widening).
  SSOT: `design/hexa_ast_diff_refactor_spec.md` (5a/5b/5c 구현 결과 § 추가).
  적용된 patch: `tooling/hexa-introspect/archive/PHASE5A_DISPATCH_PATCH.applied.md`.
  tree-sitter 는 body_hash 정확도 보강 (선택), LSP 는 transport
  (5b WorkspaceEdit 호환). hexa-introspect 가 engine SSOT.

### NEW: `atlas-n6-schema-validator` (2026-05-06)

- 갭 ID: `atlas-n6-schema-validator`
- 현 상태: **standalone 도구 가용** — `tooling/atlas-validator/atlas_validate.hexa`
  (356줄, R1..R6 + D1 7 룰). spec md: `docs/mk2/08-atlas-validate.md`.
  baseline (atlas.n6 14,609 records): 0 errors, 1,508 warnings (1,435 D1
  dup-RHS conflict + 66 R3 nonstd grade + 7 R1 unknown @E type), exit 0.
  `--strict` 모드 (warnings 도 fail) 시 exit 1.
- 후속:
  1. ~~`mk2 atlas validate` 서브커맨드 등록~~ **완료 (2026-05-06)** —
     `mk2_hexa/mk2/src/atlas/validate.hexa` (~120 LOC, subprocess 패턴) +
     `mod.hexa` `_SUBCMDS` 4→5 + `_help_text` 1줄; 4 @test PASS, smoke 7/7 PASS.
  2. ~~v2 grammar 룰 추가~~ **R7/R8 적용 (2026-05-06)** — vtypes 에 `D`/`T`/`M`
     v2 type 추가 (R1 unknown_type warning 회피); R7 (`@D` deprecation reason
     누락 검출), R8 (`@T` trace lineage 정합 검출) awk 룰 신규. atlas.n6
     baseline (v2 entry 0) → R7/R8 위반 0, total 14,609 unchanged. 미래 v2
     entry 추가 시 자동 detect. spec: `docs/mk2/08-atlas-validate.md` § 8.1/8.2.
  3. CI hook (pre-push, atlas.n6 변경 시 차단) — `--strict` 사용.
- 함정: BSD-awk UTF-8 abort (atlas.n6 line 21924 emoji partial byte) →
  `LANG=C LC_ALL=C awk` prefix 필수 (GOTCHAS.md §1 응용). docker 라우트
  에서는 atlas.n6 mount 부재 → `HEXA_LOCAL=1` 강제.

### NEW: mk2-atlas-smoke-ci-integration (2026-05-06)

- spec: `design/mk2_atlas_smoke_ci_integration_spec.md`
- 옵션 A (git pre-push) + C (hive hook-bind PostToolUse) 추천
- 현 상태: **옵션 A 적용 완료** — `tooling/smoke/git_pre_push_hook.sh` 작성. 사용자가 `ln -sf ../../tooling/smoke/git_pre_push_hook.sh .git/hooks/pre-push` 으로 활성화. 옵션 C (hook-bind PostToolUse) 후속.

### NEW: hexa-runtime-substring-perf (2026-05-06)

`source.substring(a, b)` 가 매 호출마다 O(n) byte copy → 단일 소스 다중
검색 시 O(n²) 누적. 40KB 파일 (lsp.hexa) 의 `find_all_occurrences("to_string")`
호출 시 30s+ 소요 (단일 매칭 기능적 검증은 작은 파일 OK).

**impact**: hexa-introspect Phase 5b/5c 의 atlas pair scan, lsp.hexa
rename, AST diff body_hash 정규화 등이 큰 파일에서 실용 불가.

**workaround**:
- 작은 파일 (<5KB) 한정 사용
- batch 처리 시 split 후 line-level scan (cache lines once)
- AST 기반 outline 추출 (tree-sitter / introspect --symbols) 후 target line 만 scan

**proposed runtime API**:
- C-side substring view (zero-copy slice, COW on mutation)
- `string.find_all_iter(needle: string) -> iterator<int>` intrinsic (Boyer-Moore)
- `string.byte_at(i: int) -> int` constant-time access (현재 `chars()[i]` 가 O(n))

**estimated effort**: 1–2일 (hexa-lang/self/runtime.c string ops 재작성).
