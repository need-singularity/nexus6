# hexa CLI Introspection — Design Spec (2026-05-05)

본 spec 은 hexa-lang 에 LSP 서버 대신 **CLI introspection 서브커맨드**
(`hexa --ast / --symbols / --check / --refs / --hover`) 를 추가하는
설계안이다. AI 에이전트와 외부 도구가 `bash` 호출만으로 hexa 코드의
구조 정보를 받는다. 목표는 **LSP 의 80% 효과를 1/10 비용으로**.

---

## 1. Motivation

- nexus 의 hexa 사용자는 사실상 1–3명 (본인 + 에이전트 fleet) →
  LSP 서버의 데몬/프로토콜/멀티에디터 이점이 거의 없다.
- 반면 AI 에이전트(Claude Code, mk2 dispatch, gh runner) 는 이미
  `bash → stdout JSON` 패턴으로 동작 — 표준 stdout/JSON 만 있으면
  introspection 을 즉시 소비할 수 있다.
- LSP (jsonrpc, didOpen/didChange, capabilities, textDocumentSync,
  push diagnostics) 의 비용은 1–3주. CLI introspection 은 1–3일.
- 컴파일러 내부의 AST/symbol table 은 이미 빌드 파이프라인에 존재 —
  flag 하나로 직렬화만 추가하면 된다.

> "wristwatch-class introspection" — 데몬 없는, 호출-당-1회 read.

---

## 2. Commands (전체 5종)

각 커맨드는 stdout 으로 정형 출력, stderr 로 progress/log,
exit code 로 성공/실패 (lint 룰 위반 시 0 으로도, --check 에서만 비제로).

### 2.1 `hexa --ast <file.hexa>`

- **출력**: 단일 JSON object (Program node)
- **목적**: 구조 분석, refactor 도구, AI 에이전트 코드 이해
- **스키마 (TS-style)**:
  ```ts
  interface AstOutput {
    type: "Program"
    file: string                  // absolute path
    body: AstNode[]               // top-level decls
    errors: ParseError[]          // recover-mode 시에도 best-effort 반환
  }
  interface AstNode {
    kind: "FnDecl" | "LetDecl" | "ConstDecl" | "ImportDecl"
        | "ExprStmt" | "IfStmt" | "ReturnStmt" | "MatchExpr" | ...
    loc: { start: Pos, end: Pos }
    // kind-specific fields (children/operator/literal/...)
    [k: string]: any
  }
  interface Pos { line: number /* 1-based */, col: number /* 1-based */, offset: number }
  interface ParseError { loc: Pos, message: string, severity: "error" | "warning" }
  ```
- **failure mode**: parse 실패 시에도 partial AST + errors[] 반환, exit 0.
  완전 unreadable file 만 exit 2.

### 2.2 `hexa --symbols <file.hexa>`

- **출력**: JSON array of symbol entries
- **목적**: outline/grep, AI 에이전트가 함수 시그니처만 빠르게 스캔
- **스키마**:
  ```ts
  interface Symbol {
    name: string
    kind: "fn" | "let" | "const" | "import" | "type" | "param"
    loc: Pos
    end_loc: Pos                  // for fold range
    type: string | null           // best-effort, null if 추론 실패
    visibility: "pub" | "priv"
    parent: string | null         // enclosing fn/module name
    doc: string | null            // 직전 `//` 또는 `///` 코멘트
  }
  ```
- 출력 순서는 source order (line ascending) 유지.

### 2.3 `hexa --check <file.hexa>` ← Phase 2 완료 (2026-05-06)

- **출력**: NDJSON (line-delimited JSON), 한 진단당 1줄
- **목적**: lint + atlas-갭 룰 자동 검출
- **wrapper**: `tooling/hexa-introspect/hexa_introspect.hexa` (Phase 1+2,
  877→1417 lines, +540 lines for Phase 2 룰 엔진).
- **스키마 (실측 한 줄)**:
  ```ts
  interface Diagnostic {
    rule: string                  // "HX001"
    severity: "error" | "warning" | "hint"
    loc: { line: number, col: number }   // 1-based
    msg: string
    file: string
  }
  ```
  (초기 spec 의 `end_loc` / `code` / `fix` 필드는 Phase 3 (`--refs --hover`)
  단계에서 위치 기반 lookup 도입과 함께 추가 예정. Phase 2 는 single-point
  진단으로 시작하여 NDJSON 라인 1개당 1진단을 보장.)
- **stderr meta**: `NEXUS_HEXA_INTROSPECT {"stage":"check","ms":N,"violations":N,"file":"..."}`.
- **exit code**: 기본 0 (정보성). `--strict` 옵션 시 위반 1+ → exit 1.
- **룰 (Phase 2 = 6 룰 작동, atlas 갭 8/13 중 6/6 매핑 커버)**:
  - `HX001-banned-gte` (error): `>=` / `<=` 사용 — `>` `<` 만 허용. escape `// @allow-banned-gte` (호환: `@allow-relop-banned`).
  - `HX002-bare-exec` (error): 정책 주석 없는 `exec(...)` 호출. multi-line exec 의 경우 매칭 `)` 라인까지의 어느 라인이라도 escape 인식. escape `// @allow-bare-exec`.
  - `HX003-silent-catch` (warning): 빈 `catch e {}` / `catch _ {}` (단일 라인). escape `// @allow-silent-catch`.
  - `HX004-awk-utf8-eq` (warning): 라인의 코멘트 외부 영역에 `==` + non-ASCII 바이트 + 인접 ±10 라인의 `awk` 토큰. BSD-awk UTF-8 collapse 휴리스틱. escape `// @allow-awk-utf8-eq`.
  - `HX005-rc-trailer-missing` (hint): `exec("hexa run ...")` + 5-라인 lookahead (함수 경계 `}`/`fn` 인식) 안에 `__RC=` 부재. escape `// @allow-rc-trailer-missing`.
  - `HX006-argv-slice-bare` (hint): `args()[N]` 직접 인덱스. escape `// @allow-argv-slice-bare`.
- **per-file escape**: head 30 라인의 `// @allow-<rule-suffix>-file` 가 해당 룰을 파일 전체에서 무력화.
- **거짓-양성 감소 장치**:
  1. `_strip_comment_keep_string` — HX004/HX005 의 `==` / `hexa run` 검출 시 `//` 코멘트 영역 제외 (한국어 주석 false-positive 차단).
  2. `_strip_line` — HX001/HX002/HX003/HX006 은 string/comment 모두 제거된 active code 위에서만 매칭.
  3. multi-line exec: HX002 가 paren-depth 추적으로 매칭 `)` 라인까지 escape 검색.
  4. 함수 경계 인식: HX005 가 column-1 `}` 또는 새 `fn`/`pub fn` 시작에서 lookahead 종료.
- **검증 결과 (2026-05-06)**:
  - violations 픽스처 (`tooling/hexa-introspect/_fixtures/violations.hexa`):
    **7 hits / 6 룰** (HX001×2 + HX002×1 + HX003×1 + HX004×1 + HX005×1 + HX006×1) — 모든 룰 fire.
  - atlas 5 모듈 (`mk2_hexa/mk2/src/atlas/*.hexa`):
    - `lookup.hexa`: 0 violations PASS
    - `recall.hexa`: 0 violations PASS
    - `distribution.hexa`: 0 violations PASS
    - `hypothesis.hexa`: 0 violations PASS
    - `mod.hexa`: **2 HX001 violations** (line 83, 87 — 진성 `r <= 0` 사용; ns clock 3-stage fallback 패턴이 RULES.md §1 위반. 본 wrapper 의 룰 거짓-양성이 아닌 atlas dispatcher SSOT 의 미수정 잔존 hit).
  - `n6/atlas_query.hexa`: **3 violations** (HX001×2 line 56/60 — `r <= 0`; HX005×1 line 163 — `let _ = exec("hexa run ...")` 의도적 RC-drop; per-line escape 권장).
  - 자기 점검 (wrapper 자신을 `--check`): **0 violations PASS**.
- **NDJSON 출력 예 (1줄 = 1위반)**:
  ```
  {"rule":"HX001","severity":"error","loc":{"line":56,"col":10},"msg":"`<=` is banned in hexa-lang; use `<` only (per-line escape: `// @allow-banned-gte`)","file":"n6/atlas_query.hexa"}
  ```

### 2.4 `hexa --refs <file.hexa> <symbol>`

- **출력**: JSON array of locations
- **스키마**:
  ```ts
  interface Ref {
    file: string
    loc: Pos
    end_loc: Pos
    role: "def" | "read" | "write" | "call"
    context: string               // 해당 라인 텍스트 (trim)
  }
  ```
- **scope**: 단일 파일. 다중 파일은 Phase 3.5 (workspace mode) 로 미룸.
- **fallback**: AST resolver 가 못 찾으면 lexical grep 으로 회복하고
  `role: "lexical"` 마커.

### 2.5 `hexa --hover <file.hexa> <line>:<col>`

- **출력**: 단일 JSON object
- **스키마**:
  ```ts
  interface Hover {
    symbol: string | null
    kind: Symbol["kind"] | null
    type: string | null
    signature: string | null      // "fn lookup(id: string) -> Hyp"
    doc: string | null
    def_loc: { file: string, loc: Pos } | null
  }
  ```
- 1-based line/col. 위치에 심볼 없으면 모든 필드 null + exit 0.

---

## 3. Phases

| Phase | Scope                                  | 예상 공수 | 산출물 |
|-------|----------------------------------------|-----------|--------|
| 1     | `--ast`, `--symbols`                   | 1일       | 컴파일러 내부 AST/symbol-table 직렬화 hook |
| 2     | `--check`                              | 0.5–1일   | 룰 엔진 (HX001–HX008) + NDJSON emitter |
| 3     | `--refs`, `--hover` (single-file)      | 1–2일     | 위치 기반 lookup, lexical fallback |
| 3.5   | workspace 모드 (`--refs --workspace`)  | +1일      | 파일 글롭 + 캐시 (`~/.cache/hexa/index/`) |

Phase 1 은 단독으로도 outline/AI-에이전트 활용에 충분. Phase 2 가 가장
ROI 가 높음 (atlas 갭 룰들이 즉시 생산성 회복).

---

## 4. JSON 스키마 (정식)

루트 디렉토리 `hexa-lang/schema/` 에 다음 파일 배치 제안:

- `ast.schema.json` — Draft-07
- `symbol.schema.json`
- `diagnostic.schema.json`
- `ref.schema.json`
- `hover.schema.json`

스키마 파일은 컴파일러 release artifact 와 함께 배포되어 외부 도구
(jq, ajv, zod) 가 검증/타입 생성 가능. CI 에서 fixture 출력 ↔ 스키마
일치를 검사한다.

`Pos` 는 모든 스키마 공통:
```json
{ "line": {"type":"integer","minimum":1},
  "col":  {"type":"integer","minimum":1},
  "offset": {"type":"integer","minimum":0} }
```

---

## 5. 사용 예 (AI 에이전트 / Bash)

### 5.1 함수만 빠르게 스캔
```bash
hexa --symbols mk2_hexa/mk2/src/atlas/lookup.hexa \
  | jq '.[] | select(.kind=="fn") | {name, type, line: .loc.line}'
```

### 5.2 lint 위반만 추출 (CI gate)
```bash
hexa --check n6/atlas_query.hexa \
  | jq -c 'select(.severity=="error")' \
  | tee state/atlas_check.ndjson
test -s state/atlas_check.ndjson && exit 1 || exit 0
```

### 5.3 외부 호출자 탐색 (워크스페이스)
```bash
for f in $(rg -l --type-add 'hexa:*.hexa' -t hexa ''); do
  hexa --refs "$f" dispatch | jq -c --arg f "$f" '. + {file:$f}'
done | jq -s '.[] | select(.role=="call")'
```

### 5.4 AI 에이전트 hover (커서 위치 → 타입)
```bash
hexa --hover mk2_hexa/mk2/src/main.hexa 42:18 \
  | jq -r '"\(.signature // "<unknown>") :: \(.doc // "")"'
```

### 5.5 AST diff (PR 리뷰)
```bash
diff <(git show HEAD~1:n6/atlas_query.hexa | hexa --ast /dev/stdin | jq -S .) \
     <(hexa --ast n6/atlas_query.hexa | jq -S .)
```

---

## 6. LSP vs CLI introspection 비교표

| 측면            | LSP server                         | CLI introspection                        |
|-----------------|------------------------------------|------------------------------------------|
| 구현 비용       | 1–3주 (jsonrpc, sync, capability)  | 1–3일 (flag + 직렬화)                    |
| 런타임 모델     | 데몬 (process per editor session)  | 호출-당-1회 read, stateless              |
| 멀티에디터      | 자동 (VSCode/nvim/Helix)           | 각 에디터가 bash 래퍼 작성 (1줄)         |
| AI 에이전트     | jsonrpc client 필요                | `bash → stdout JSON` 즉시                |
| didChange 지연  | <50ms (메모리 캐시)                | 100–400ms (cold parse)                   |
| 점진 파싱       | 가능                               | 전체 파일 재파싱 (small file 에 OK)      |
| 워크스페이스 인덱스 | 자동                            | Phase 3.5 캐시                           |
| 디버깅 가능성   | 양방향 프로토콜, 추적 어려움       | bash 한 줄 재현, `>` 로 fixture 저장     |
| 의존성          | LSP 라이브러리, jsonrpc            | stdout + JSON 만                         |
| 80/20           | 100% 효과 / 100% 비용              | **80% 효과 / 10% 비용** ✓                |

**핵심 1줄**: LSP 는 다중 에디터 데몬 비용을 감수하고, CLI 는
호출-당-1회 stdout 으로 같은 정보를 1/10 비용에 노출한다.

### 6.1 Phase 별 LSP 효과 누적치 (2026-05-06 기준)

| Phase 완료 시점        | LSP 효과 누적 | 근거                                                              |
|------------------------|---------------|-------------------------------------------------------------------|
| Phase 1 (`--ast`/`--symbols`) | 50%       | outline + AST 표면 = LSP documentSymbol/foldingRange 핵심 절반    |
| Phase 2 (`--check`)    | 70%           | + diagnostics push (HX001–HX008) = LSP textDocument/diagnostic   |
| Phase 3 (`--refs`/`--hover`) **적용 완료 2026-05-06** | **80%**   | + navigate (definition / references) + hover signature/type     |
| Phase 5a (`--diff`) **적용 완료 2026-05-06** | **80%** (보강) | + symbol-table hash diff = LSP rename/refactor preview 기초 (workspace/symbol 와 직교) |
| Phase 3.5 (workspace)  | 90%           | + workspace symbol / cross-file refs (LSP workspace/symbol)      |
| Phase 4 (native loc)   | 95%           | + AST-precise loc → wrapper 폐기, 컴파일러 직접 직렬화           |

Phase 3 (single-file `--refs`/`--hover`) 은 LSP 의 navigate/hover 두 핵심
인터랙션을 흉내내며, 컴파일러 본체 패치 없이 wrapper 안에서 토큰 단위
스캐너를 재사용한다. tooling/hexa-introspect/PHASE3_DESIGN.md 가 SSOT.

Phase 5a (`--diff`) 는 두 .hexa 파일의 symbol 테이블을 hash 단위로
비교하여 `unchanged|added|removed|renamed|signature_changed|body_changed`
의 6 변경 유형을 NDJSON 으로 emit. LSP 의 rename/refactor 시각화 기초로
재활용 가능 (Phase 5b 에서 `--diff-rename` / `--diff-sig` / `--apply` 로
확장). dispatch SSOT: `hexa-introspect --diff a.hexa b.hexa` (subprocess
로 sibling `tooling/hexa-introspect/diff.hexa` 위임).

---

## 7. design/hexa_lang_gaps_from_atlas.md 갭 매핑

| Atlas gap                              | CLI introspection 효과                            | 룰 코드      | 상태 (2026-05-06) |
|----------------------------------------|---------------------------------------------------|--------------|-------------------|
| module-import-system                   | `--symbols` 로 외부 모듈의 export 표면 미리 확인  | (info)       | Phase 1 작동      |
| argv-stdlib-helper                     | `args()[2..]` 누락 자동 검출                      | HX006        | **검증 완료**     |
| subprocess-exit-code-capture           | `__RC=$?` trailer 누락 자동 검출                  | HX005        | **검증 완료**     |
| structured-error-propagation           | NDJSON namespace prefix 누락 lint                 | HX007        | Phase 2.5 (보류)  |
| entry-point-vs-library-dual-mode       | `@is_main` guard 패턴 미사용 hint                 | HX009 (계획) | Phase 2.5 (보류)  |
| json-stdlib-parser                     | awk fallback 사용처 표시 (transitional warn)      | HX010 (계획) | Phase 2.5 (보류)  |
| bsd-awk-utf8-equality-collapse         | awk 내부 `==` 다바이트 비교 위험 lint             | HX004        | **검증 완료**     |
| arg-vector-shape-uncertainty           | (= argv-stdlib-helper)                            | HX006        | **검증 완료**     |
| hexa-rules R1 (`>=`/`<=` ban)          | `>=`/`<=` 토큰 자동 검출                          | HX001        | **검증 완료**     |
| hexa-rules R3 (bare `exec()` policy)   | 정책 주석 없는 `exec(...)` 자동 검출              | HX002        | **검증 완료**     |
| hexa-rules R4 (silent catch)           | 빈 `catch e {}` 자동 검출                          | HX003        | **검증 완료**     |

해결되는 갭은 없다 (CLI 는 stdlib 추가가 아님). 그러나 **8개 갭 중 6개가
CLI 룰로 자동 검출/완화** 되어 인적 review 부담이 사라진다 (Phase 2 완료
2026-05-06: HX001/002/003/004/005/006 모두 작동). 나머지 2개
(module-import, json-parser) 는 stdlib 작업이 본질이며 CLI 로는 사용
패턴만 가시화한다.

---

## 8. 비-목표 (out of scope)

- 자동 완성 (completion) — 인터랙티브 stateful 이 본질, CLI 로 흉내내기
  비효율
- 코드 액션 (code action) — `--check` 의 `fix` 필드로 일부 대체
- 실시간 diagnostic streaming — 호출 모델이 1-shot
- multi-file workspace symbol — Phase 3.5 까지 미룸
- formatter — 별도 `hexa fmt` 가 더 자연스러움

---

## 9. 후속

- 충분히 사용되면 LSP 서버로 승격 가능: CLI 출력을 LSP 메시지로 wrap
  (textDocument/documentSymbol = `--symbols` 출력 그대로 매핑).
- tree-sitter grammar 와는 직교: tree-sitter 는 syntax highlight 전용,
  CLI 는 semantic 정보 (type, scope, 룰) 담당.
- nexus 외부 (R4 kick, mk2 dispatch) 의 AI 에이전트 prompt template 에
  `hexa --symbols` 를 표준 read-tool 로 등록 (jq pipe SSOT).
- `--check` 룰 set 은 hexa-rules skill 의 SSOT 와 동기화 — 룰 추가 시
  양쪽 동시 갱신 (CI 에서 룰 코드 ↔ skill 문서 cross-check).

---

## 10. 검증 (수용 기준)

Phase 1 완료 조건:
- `hexa --ast n6/atlas_query.hexa | jq '.body | length'` → 0 이상 정수
- `hexa --symbols n6/atlas_query.hexa | jq 'length'` → 1 이상
- 둘 다 ajv 로 스키마 통과

Phase 2 완료 조건:
- HX001–HX008 fixture 파일 (`hexa-lang/test/lint/HX0NN.hexa`) 각 1개
- `hexa --check fixture | jq -c 'select(.code=="HX0NN")'` 정확 1줄

**Phase 2 검증 (2026-05-06)** — 6/6 룰 작동:
- 6 룰 (HX001–HX006) wrapper 구현 완료 — `tooling/hexa-introspect/hexa_introspect.hexa` (877→1417 lines).
- 단일 fixture (`tooling/hexa-introspect/_fixtures/violations.hexa`, 6 violation patterns) 에서 7 hits / 6 룰 정확 검출.
- atlas 5 모듈 4/5 PASS (lookup, recall, distribution, hypothesis = 0 violations; mod.hexa 는 진성 HX001 hit 2개).
- n6/atlas_query.hexa 3 violations (HX001×2 진성 + HX005×1 진성).
- wrapper 자기 점검 0 violations PASS.
- HX007 (ndjson-key-clash) / HX008 (cmp-ns-time) 은 Phase 2.5 로 이연 (룰 패턴이 다중-라인 의존성을 요구하여 본 wrapper 의 단일-라인 스캐너로는 정밀도가 낮음 — 컴파일러 본체 패치가 ROI 우위).

Phase 3 완료 조건:
- `hexa --refs lookup.hexa lookup_id` 가 def + 호출자 1+ 반환
- `hexa --hover lookup.hexa <fn 본문 line>` 이 enclosing fn signature 반환

### 10.1 Phase 3 진행 (2026-05-06)

- 설계 / patch SSOT: `tooling/hexa-introspect/PHASE3_DESIGN.md`,
  `tooling/hexa-introspect/archive/PHASE3_PATCH.applied.md` (적용 후
  archive 됨).
- 동시 작업 가드: Phase 2 (`--check`) 가 같은 `hexa_introspect.hexa` 에
  진행 중 (mtime 흔들림 관찰). Phase 3 직접 머지는 Phase 2 완료 후 — **완료**.
- single-file 분류는 spec § 2.4 의 5종 (`def/read/write/call/lexical`)
  대신 **3-bucket (`decl|call|reference`)** 로 좁힘 — AST resolver 없이
  토큰 휴리스틱만 사용. read/write 구분은 Phase 4 (native loc) 시점에
  AST 도입과 함께 부활.
- 검증 fixture: `mk2_hexa/mk2/src/atlas/lookup.hexa` 의 `_ns_now`
  (line 26 정의 + line 279/368 호출, 총 3 ref 기대).

**Phase 3 적용 완료 (2026-05-06)**:
- `hexa_introspect.hexa` 1733 lines (5-mode dispatch: `--ast` / `--symbols`
  / `--check` / `--refs` / `--hover`).
- bin shim (`bin/hexa-introspect`) mode whitelist 5종 + min-argc 분기 처리.
- `--refs` NDJSON 정상, `--hover <line>:<col>` JSON 정상 (decl 키워드
  fallback 동작).
- LSP 효과 70 → **80%** (navigate + hover 추가).

### 10.2 Phase 5a 진행 (2026-05-06)

- 설계 SSOT: `design/hexa_ast_diff_refactor_spec.md` § 3.2 (symbol-table
  hash diff), `tooling/hexa-introspect/archive/PHASE5A_DISPATCH_PATCH.applied.md`.
- 알고리즘 SSOT: `tooling/hexa-introspect/diff.hexa` (952 lines, 독립
  entry-point 로도 `hexa run diff.hexa --diff a b` 호출 가능).
- dispatch 분기: `hexa_introspect.hexa` 의 `--ast/--symbols/--check/
  --refs/--hover` 5분기에 `--diff` 추가 → **6-mode**. wrapper 는 dispatch
  만 담당, 알고리즘은 sibling subprocess 로 위임.
- 검증 (2026-05-06):
  - `hexa-introspect --diff sample.hexa sample.hexa` → 7 unchanged,
    exit 0 (자기 동등성).
  - `hexa-introspect --diff sample.hexa sample_rename.hexa` → 6 unchanged
    + 1 renamed (greet → hail, `body_hash_match`) + 1 added (`_clock_ns`),
    exit 0.
- LSP 효과 보강: navigate/hover (Phase 3) + diff (Phase 5a) = LSP rename/
  refactor preview 의 기초 layer. workspace 단계 (Phase 3.5) 에서 cross-
  file 확장.

### 10.3 Phase 4-LSP 트랙 (보류)

- 컴파일러 본체에 `loc{file,line,col}` 직접 주입 → wrapper scanner 폐기.
- 의존: `design/hexa_parser_loc_injection_spec.md` (Token → AST 의 line/col
  보존 패치).
- 우선순위: Phase 3.5 (workspace) 가 ROI 우위 → 4-LSP 는 그 이후.

---

## 11. 리스크

- **AST 직렬화 부담**: 컴파일러 내부 표현이 자주 변하면 JSON 스키마도
  요동. 완화: `ast.schema.json` 을 SemVer + `ast_version` 필드.
- **--check 룰 거짓양성**: HX002 (bare-exec) 가 너무 공격적이면 noise.
  완화: `// hexa-allow: HX002` 라인 주석 + 프로젝트 `hexa.toml` deny/allow.
- **성능**: 큰 파일 (>5k lines) 의 cold parse. 완화: Phase 3.5 캐시 +
  파일 mtime 기반 invalidation.
- **에이전트 의존**: `bash → jq` 가 SSOT 가 되면 jq 부재 환경에서 깨짐.
  완화: `--check --format=human` 등 fallback format 제공.

---

## 12. 결론

LSP 는 다중 에디터/협업 환경에서 압도적이지만, nexus 의 사용 패턴은
**1-shot bash + AI 에이전트** 가 dominant. CLI introspection 은 같은
semantic 정보를 1/10 비용으로 노출하면서, 동시에 atlas 디스패처 도중
발견된 6/8 갭을 lint 룰로 자동 검출한다. Phase 1 (1일) 만으로도 outline
+ AI 에이전트 활용가치 임계점을 통과한다.
