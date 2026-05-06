# hexa Token Taxonomy — Unified Spec (tree-sitter ↔ LSP)

Author: nexus design track
Date: 2026-05-06
Status: design only (no code changes)
Scope: `tooling/tree-sitter-hexa/queries/highlights.scm` ↔ `hexa-lang/self/lsp.hexa`
Related: `design/hexa_lang_gaps_from_atlas.md` Rank 6 (hexa-treesitter-grammar),
`design/hexa_cli_introspection_spec.md` (sibling SSOT pattern)

---

## § 1. Motivation — cross-editor 색칠 일관성

hexa 소스를 색칠하는 두 개의 독립 엔진이 존재한다.

1. **tree-sitter (D 트랙)**
   `tooling/tree-sitter-hexa/queries/highlights.scm` (67줄, capture 13종)
   소비자: Neovim (nvim-treesitter), Helix, Zed, GitHub linguist,
   AI 학습 셋 (정적 syntax tree).
2. **LSP semanticTokens (B/5 트랙)**
   `hexa-lang/self/lsp.hexa` `get_semantic_token_types()` (token type 15종),
   `get_semantic_token_modifiers()` (modifier 4종), `semantic_tokenize()`
   (lexer 재실행).
   소비자: VS Code (semantic highlighting), JetBrains LSP, helix LSP
   layer (treesitter 위에 덧칠), neovim native LSP.

두 엔진은 같은 파일을 다른 카탈로그로 분류한다. 사용자 한 명이 동일
hexa 파일을 VS Code 에서 보면 LSP 색칠, Neovim 에서는 tree-sitter 색칠을
받는다. 카탈로그가 분리되어 있으면 같은 토큰이 다른 색이 되거나
(예: 함수 호출 = "function" vs "@function.call"), 한쪽에만 있는 카테고리
(예: "decorator", "string.escape") 를 잃는다.

본 spec 은 두 카탈로그를 단일 SSOT (canonical taxonomy) 로 정렬해
**같은 토큰은 모든 에디터에서 같은 의미 클래스를 받는다** 를 보장하는
설계 룰이다.

---

## § 2. 현 카탈로그 추출 (read-only)

### 2.1 tree-sitter highlights.scm — capture name 인벤토리

`tooling/tree-sitter-hexa/queries/highlights.scm` 에서 사용된 capture (13종):

| # | capture | 매칭 노드 | 의미 |
|---|---------|----------|------|
|  1 | `@keyword` | `fn`, `let`, `mut`, `return`, `if`, `else`, `while`, `for`, `in`, `try`, `catch` | 예약어 |
|  2 | `@type.builtin` | `(primitive_type)` | int, string, bool 등 내장 타입 |
|  3 | `@function` | `function_declaration name` | 함수 선언명 |
|  4 | `@variable.parameter` | `parameter name` | 파라미터 |
|  5 | `@variable` | `let_declaration name` | 로컬 바인딩 |
|  6 | `@function.call` | `call_expression function: identifier` | bare 호출 |
|  7 | `@function.method` | `call_expression function: member_expression.property` | 메서드 호출 |
|  8 | `@property` | `member_expression property` | 필드 접근 |
|  9 | `@number` | `(integer_literal)` | 정수 |
| 10 | `@number.float` | `(float_literal)` | 부동소수점 |
| 11 | `@boolean` | `(boolean_literal)` | true/false |
| 12 | `@string` | `(string_literal)` | 문자열 |
| 13 | `@string.escape` | `(escape_sequence)` | `\n`, `\"` 등 |
| 14 | `@operator` | `+ - * / % == != < > <= >= && \|\| ! = ->` | 연산자 |
| 15 | `@punctuation.bracket` | `()` `{}` `[]` | 괄호류 |
| 16 | `@punctuation.delimiter` | `,` `:` `.` | 구분자 |
| 17 | `@comment.note` | `(line_comment)` `#match? "@allow-"` | 프로젝트 어노테이션 |
| 18 | `@comment` | `(line_comment)` | 일반 주석 |

총 18 capture (13 unique base + 5 dotted refinement). `@comment.note` 는
hexa 특수 어노테이션 (`// @allow-bare-exec`, `// @allow-silent-catch`,
`// @allow-silent-exit`) 마킹 용도.

### 2.2 LSP semanticTokens — token type / modifier 인벤토리

`hexa-lang/self/lsp.hexa:126-153` legend:

**tokenTypes (15종, index = id)**:

| id | type | semantic_tokenize 사용 위치 |
|----|------|----------------------------|
|  0 | namespace | (legend 만 — emit 안 함) |
|  1 | type | line 268 (대문자 시작 식별자) |
|  2 | class | (emit 안 함) |
|  3 | enum | (emit 안 함) |
|  4 | struct | (emit 안 함) |
|  5 | parameter | (emit 안 함; 단순 lexer 라 결정 불가) |
|  6 | variable | line 278 (다른 분류 안 맞을 때) |
|  7 | property | (emit 안 함) |
|  8 | function | line 263 (builtin), line 276 (식별자 + `(`) |
|  9 | keyword | line 258, 260 (`true`/`false` + 키워드) |
| 10 | comment | line 206, 236 (line/block) |
| 11 | string | line 324, 337, 363, 385 (string + char) |
| 12 | number | line 302 |
| 13 | operator | line 400~426 (모든 연산자) |
| 14 | decorator | line 397 (`@<ident>`) |

**tokenModifiers (4종, bitmask)**:

| bit | modifier | 사용 |
|-----|----------|------|
| 0 | declaration | (emit 안 함) |
| 1 | definition | (emit 안 함) |
| 2 | readonly | (emit 안 함) |
| 3 | defaultLibrary | line 263 (builtin function 한정) |

LSP legend 에는 15+4 가 선언되어 있으나, 실제 emit 되는 type 은 8종
(type, variable, function, keyword, comment, string, number, operator,
decorator) + modifier 1종 (defaultLibrary). 나머지는 future-reserved.

---

## § 3. 매핑표 — 양방향 변환 룰

base 의미 → tree-sitter capture / LSP type id 양방향 매핑:

| canonical 의미 | tree-sitter capture | LSP type id | LSP type | 양쪽 매칭? |
|---------------|--------------------|--------------|----------|------------|
| 키워드 | `@keyword` | 9 | keyword | yes |
| 내장 타입 | `@type.builtin` | 1 + mod=defaultLibrary | type+defLib | partial (LSP 에선 modifier 로 표현) |
| 사용자 타입 | (없음) | 1 | type | tree-sitter 누락 |
| 함수 선언 | `@function` | 8 + mod=declaration | function+decl | partial (LSP 미사용 modifier) |
| 함수 호출 | `@function.call` | 8 | function | yes (의미 동일, dotted vs flat) |
| 메서드 호출 | `@function.method` | 8 | function | tree-sitter 가 더 세분화 |
| builtin 함수 | (없음 — 모두 `@function.call`) | 8 + mod=defaultLibrary | function+defLib | LSP 가 더 세분화 |
| 파라미터 | `@variable.parameter` | 5 | parameter | yes |
| 로컬 변수 | `@variable` | 6 | variable | yes |
| 프로퍼티 | `@property` | 7 | property | yes (LSP 는 emit 안 함) |
| 정수 리터럴 | `@number` | 12 | number | yes |
| 부동소수점 | `@number.float` | 12 | number | tree-sitter 가 더 세분화 |
| 불리언 | `@boolean` | 9 (keyword 로 분류) | keyword | **충돌** (의미 다름) |
| 문자열 | `@string` | 11 | string | yes |
| 문자 (`'x'`) | (없음) | 11 | string | LSP 가 더 포함 (char→string) |
| 이스케이프 시퀀스 | `@string.escape` | (없음) | (없음) | tree-sitter only |
| 연산자 | `@operator` | 13 | operator | yes |
| 괄호 | `@punctuation.bracket` | (skip) | (없음) | tree-sitter only |
| 구분자 | `@punctuation.delimiter` | (skip) | (없음) | tree-sitter only |
| 라인 주석 | `@comment` | 10 | comment | yes |
| 어노테이션 (`// @allow-…`) | `@comment.note` | 10 (general comment) | comment | tree-sitter 가 더 세분화 |
| 데코레이터 (`@<ident>`) | (없음 — grammar 에 노드 없음) | 14 | decorator | LSP only |
| namespace | (없음) | 0 | namespace | 양쪽 미사용 |
| class / enum / struct | (없음) | 2/3/4 | class/enum/struct | 양쪽 미사용 |

---

## § 4. 통합 카탈로그 — canonical 이름 결정

### 4.1 이름 충돌 / 갭 분류

- **이름 충돌 1건**: `boolean`. tree-sitter 는 `@boolean` (별도 카테고리),
  LSP 는 type id 9 = `keyword` 로 흡수. 시각적으로 색이 다를 수밖에 없음.
- **tree-sitter only (4)**: `@string.escape`, `@punctuation.bracket`,
  `@punctuation.delimiter`, `@comment.note`. LSP 는 punctuation 을
  의도적으로 skip (LSP 표준에 punctuation token 없음).
- **LSP only (1)**: `decorator` (`@<ident>` 어노테이션). tree-sitter
  grammar.js 에 decorator 노드 미정의.
- **세분화 비대칭 (4)**:
  - `@number.float` vs LSP `number`: tree-sitter 세분화
  - `@function.method` vs LSP `function`: tree-sitter 세분화
  - LSP `function + defaultLibrary` vs tree-sitter `@function.call`: LSP 세분화
  - LSP `type + defaultLibrary` vs tree-sitter `@type.builtin`: 표현 방식 차이

### 4.2 SSOT 결정 — **LSP 표준이 SSOT**, tree-sitter 가 따라간다

근거:
1. LSP semantic token types 는 Microsoft 의 lingua franca 표준
   (https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#semanticTokenTypes).
   VS Code, JetBrains, Neovim native LSP 가 동일한 enum 으로 소비.
2. tree-sitter capture name 은 nvim-treesitter convention 이지만,
   에디터마다 ("zed", "helix") theme mapping 이 갈린다. 즉 LSP 가
   더 좁은 표준이고 tree-sitter 는 더 너른 컨벤션이다.
3. hexa-lang LSP 가 이미 LSP 15종 type + 4종 modifier legend 를
   선언했고, semantic_tokenize() 가 그 위에 동작한다. 변경 비용은
   tree-sitter 쪽이 낮다 (`.scm` 만 갱신).

**SSOT 룰**:
- canonical 토큰 이름 = LSP semanticTokenTypes 의 base.
- 세분화는 LSP modifier (declaration / definition / readonly /
  defaultLibrary) 로 1차 표현, 부족하면 tree-sitter dotted suffix 로
  2차 표현.
- punctuation / bracket / escape 는 tree-sitter only (LSP 는 skip 유지).
- decorator 는 양쪽 모두 emit (tree-sitter 노드 추가 필요).
- boolean 은 양쪽 모두 keyword 로 통합 (충돌 해소).

### 4.3 canonical token 카탈로그 (15 + extensions)

| canonical name | LSP id | tree-sitter capture (권장) | 비고 |
|----------------|--------|----------------------------|------|
| namespace | 0 | `@namespace` | 모듈 시스템 정착 후 |
| type | 1 | `@type` | 사용자 타입 |
| type (builtin) | 1 + mod 3 | `@type.builtin` | LSP modifier 로 1차 |
| class | 2 | `@type.class` | reserved |
| enum | 3 | `@type.enum` | reserved |
| struct | 4 | `@type` (struct 는 LSP 표준 type) | hexa `struct` |
| parameter | 5 | `@variable.parameter` | yes |
| variable | 6 | `@variable` | yes |
| variable (readonly) | 6 + mod 2 | `@variable` (let 는 readonly) | mut 만 mod 2 빼기 |
| property | 7 | `@property` | yes |
| function | 8 | `@function` | 선언 + 호출 통합 |
| function (declaration) | 8 + mod 0 | `@function` (선언 위치) | LSP modifier 1차 |
| function (defaultLibrary) | 8 + mod 3 | `@function.builtin` | builtin 한정 |
| function (method) | 8 | `@function.method` | tree-sitter 만 분리 |
| keyword | 9 | `@keyword` | boolean 흡수 |
| comment | 10 | `@comment` | yes |
| comment (annotation) | 10 | `@comment.note` | tree-sitter 만 분리 |
| string | 11 | `@string` | char 포함 |
| string (escape) | 11 | `@string.escape` | tree-sitter 만 분리 |
| number | 12 | `@number` | float 포함 |
| operator | 13 | `@operator` | yes |
| decorator | 14 | `@attribute` | tree-sitter 추가 필요 |
| (없음) | — | `@punctuation.bracket` | tree-sitter only (LSP skip) |
| (없음) | — | `@punctuation.delimiter` | tree-sitter only (LSP skip) |
| (없음) | — | `@boolean` | **삭제** — `@keyword` 로 흡수 |

---

## § 5. tree-sitter 측 변경 권장

`tooling/tree-sitter-hexa/queries/highlights.scm` 갱신 권장 (이번 spec 외
별도 D 트랙 작업).

> **D 트랙 적용 결과 (2026-05-06)** — 5/6 적용, 1/6 보류 (사유 명시):
> 1. boolean → keyword 흡수 — **APPLIED** (highlights.scm `(boolean_literal) @keyword`).
> 2. builtin function 별도 capture — **APPLIED** (`@function.builtin` predicate
>    + SSOT `tooling/tree-sitter-hexa/queries/builtins.list`, 16 항목).
> 3. decorator 노드 추가 — **APPLIED** (grammar.js `decorator: $ =>
>    seq('@', $.identifier)`, `function_declaration` 앞에 `repeat($.decorator)`;
>    실 hexa 파일 `mk2_hexa/mk2/tests/test_*.hexa` 의 `@test` 를 정상 파싱).
> 4. type vs type.builtin 분리 — **APPLIED** (`@type.builtin` 유지 + parameter/
>    let/return/array 위치의 (identifier) 를 `@type` 로 캡처).
> 5. let 의 readonly 표시 — **DEFERRED** (`let` vs `let mut` 를 grammar 에서
>    분리하면 기존 corpus 9개 트리 모양 변경 → 회귀. LSP modifier 로 표현
>    하는 편이 호환성 안전. § 6.4 와 함께 추후 처리).
> 6. `@comment.note` 패턴 일반화 — **APPLIED** (`@(allow-|nohot|hot|deprecated)`).
>
> 회귀 가드: `tree-sitter test` 12/12 PASS (기존 9 + 신규 3: boolean,
> single decorator, multi-decorator). `parser.c` 는 generate 산출물로
> 자동 갱신.

1. **boolean → keyword 흡수**:
   ```
   (boolean_literal) @keyword     ; was @boolean
   ```
2. **builtin function 별도 capture** (LSP 의 defaultLibrary 와 정렬):
   - grammar.js 에 builtin 식별자 리스트 (`println`, `len`, `to_string` …)
     매칭. `(call_expression function: (identifier) @function.builtin
     (#match? @function.builtin "^(println|len|to_string|…)$"))`.
   - LSP 의 `get_builtins()` (line 184) 와 동일 리스트 — 두 곳에서
     하드코딩하지 않도록 별도 SSOT (`tooling/tree-sitter-hexa/queries/builtins.list`)
     로 추출 권장.
3. **decorator 노드 추가**:
   - grammar.js 에 `decorator: $ => seq("@", $.identifier)` 추가 후
     `(decorator) @attribute` capture.
4. **type vs type.builtin 분리**:
   - `(primitive_type) @type.builtin` 유지.
   - 사용자 정의 타입 (Pascal case identifier 가 type 위치에 등장) 은
     `(type_identifier) @type` 추가.
5. **let 바인딩의 readonly 표시** (선택):
   - `let mut x` vs `let x` 를 grammar 에서 분리해서 `@variable` 와
     `@constant` 로 마킹. LSP 의 modifier `readonly` 와 동치.
6. **`@comment.note` 매칭 패턴 일반화**:
   - 현재 `@allow-` prefix 만. `@nohot`, `@hot`, `@deprecated` 등도 포함
     하도록 `(#match? @comment.note "@(allow-|nohot|hot|deprecated)")` 로
     확장. (어노테이션 카탈로그는 `design/method_gap_pattern.md` 와 함께
     관리 — 별도 SSOT 권장.)

---

## § 6. LSP 측 변경 권장

`hexa-lang/self/lsp.hexa` `semantic_tokenize()` 갱신 권장:

1. **builtin 분류 modifier 보정**:
   현재 line 263 은 `modifiers: 8` (= `1 << 3`, defaultLibrary).
   매직 넘버 8 을 `MOD_DEFAULT_LIBRARY = 8` 상수로 빼서 SSOT 명시.
2. **type+defaultLibrary modifier**:
   primitive type 식별자 (`int`, `bool`, `string`) 를 만나면
   `type_type=1, modifiers=8` 로 emit. 현재는 식별자 분류만 — 타입
   문맥에서 emit 안 함. 대문자 시작 식별자만 type 으로 봄 (line 268)
   — 이는 hexa 컨벤션과 다름 (hexa 는 lowercase primitive).
3. **decorator 매칭 강화**:
   현재 `@<ident>` 만 잡음 (line 387). hexa 의 `// @allow-…` 는 LSP 측
   에서 일반 comment 로 분류 (id 10) — tree-sitter 의 `@comment.note`
   와 어긋남. **권장**: `// @<ident>-…` 패턴을 `comment` 그대로 두되
   modifier 로 별도 표시 또는 별도 token type 추가 (LSP 표준 외).
   안전한 선택은 일반 comment 로 일관 유지 (tree-sitter 도 `@comment.note`
   를 dotted refinement 로 — base 색은 comment 와 동일).
4. **let 의 readonly modifier**:
   `let` 바인딩은 `MOD_READONLY = 4`, `let mut` 는 modifier 0. 현재는
   semantic_tokenize 가 lexer 레벨이라 `let mut` 컨텍스트를 못 봄 —
   parser 단으로 끌어올리거나 lookahead 추가.
5. **method call detection**:
   현재 `식별자 + (` 만 보고 함수로 분류 (line 275). `member_expression`
   에서 메서드 호출이면 modifier 없이 그대로 8 (function). LSP 표준에는
   `method` 토큰이 없어 이 정도가 한계 — 참고로 LSP 3.17 token type 24
   에 `method` 가 있으나 현재 legend 에 미포함. 향후 추가 검토 (legend
   에 `method` 추가 후 tree-sitter `@function.method` 와 정렬).
6. **boolean → keyword 통합**:
   현재 `true`/`false` → token_type 9 (keyword). tree-sitter 측 변경
   (§5.1) 으로 양쪽 일치. 변경 불필요.

---

## § 7. hexa 특수 어노테이션 처리

hexa 프로젝트 컨벤션:
- `// @allow-bare-exec` — bare-exec 린트 면제
- `// @allow-silent-catch` — silent catch 린트 면제
- `// @allow-silent-exit` — silent exit 린트 면제
- (확장 후보) `// @nohot`, `// @hot`, `// @deprecated`

이들은 일반 주석이지만 **시각적으로 구분되어야 한다** (린터가 무엇을
면제하는지 즉시 보이도록).

### 처리 룰 (canonical)
- LSP: `comment` (id 10) 로 emit, modifier 0 유지. hexa-lang LSP 가
  자체 token type 추가하면 LSP 표준에서 벗어나 VS Code 에서 색이 빠짐
  (legend 에 없는 id 는 client 가 무시).
- tree-sitter: `@comment.note` 로 dotted refinement.
  `nvim-treesitter` 와 helix 는 `@comment.note` 를 `@comment` 와 다르게
  highlight 하도록 설정 가능.
- VS Code: LSP 만 봄 → `comment` 색으로 통일됨 (별도 색 안 됨).
  대안: tree-sitter 기반 보조 highlighter 활성화 (vscode-tree-sitter
  extension) — 그럼 `@comment.note` 도 색이 분리됨.

**결론**: 어노테이션 시각 분리는 tree-sitter only 이며, VS Code 에서
원하는 사용자는 vscode-tree-sitter extension 을 별도 설치한다.

---

## § 8. 우선순위 — LSP 표준이 SSOT

§4.2 결정 재확인:
1. **canonical name** = LSP semanticTokenTypes (base 15종).
2. **수정 비용 비교**:
   - tree-sitter `.scm` 갱신: 낮음 (텍스트만, 67줄).
   - LSP `lsp.hexa` 변경: 중 (`semantic_tokenize` 800줄, lexer 재진입).
   - LSP legend 변경: 매우 위험 (호환성 — 이미 client 들이 id 캐시).
3. **기존 호환**:
   - LSP legend 의 id (0~14) 는 절대 reorder 금지. 추가는 append-only.
   - tree-sitter capture 는 client (theme) 가 fallback 룰로 조회 —
     기존 capture 를 제거하기 보다 추가/세분화가 안전.

---

## § 9. 검증 방법

`nexus check --token-taxonomy` (또는 `--hexalint` subcommand 확장) 으로
양방향 정합성 검증:

### 9.1 Static check
1. **highlights.scm 파싱**: `tree-sitter query` 로 dump → capture name
   set 추출.
2. **lsp.hexa legend 추출**: `get_semantic_token_types()` 의 array
   리터럴 파싱 → name set.
3. **mapping table** (§4.3) 와 비교, 누락/잉여 capture report.

예 (sentinel 형식):
```
__NEXUS_CHECK_TOKEN_TAXONOMY__: PASS captures=18 lsp_types=15 mismatches=0
```
또는
```
__NEXUS_CHECK_TOKEN_TAXONOMY__: FAIL mismatches=3
  - tree-sitter @boolean has no LSP equivalent (resolve: → @keyword)
  - LSP decorator id=14 has no tree-sitter capture
  - tree-sitter @comment.note unmapped to LSP modifier
```

### 9.2 Runtime check (cross-editor smoke)
fixture 한 개 (`fixtures/token_taxonomy_smoke.hexa`) 에 모든 카테고리
요소 포함 (keyword, type, function, parameter, variable, property,
number, string, escape, boolean, operator, comment, annotation,
decorator). 출력 비교:
- VS Code: `Developer: Inspect Editor Tokens and Scopes` 로 각 토큰의
  semantic token type 확인.
- Neovim: `:Inspect` 로 capture name 확인.
- Helix: `:select-syntax` (또는 inspect-syntax-tree).
- Zed: theme inspector.

각 토큰의 base meaning 이 일치하면 PASS.

### 9.3 CI 통합
- `tests/test_token_taxonomy_drift.hexa` (신규, runtime test)
  → `nexus check --token-taxonomy` 호출, sentinel grep, exit code 채택.
- atlas timeline 에 `token_taxonomy_check` 도메인 항목 추가 (추후
  `state/atlas_health_timeline.jsonl` 에 자동 기록).

---

## § 10. 후속

1. **D 트랙 (별도 작업)**: §5 의 `highlights.scm` 갱신 — boolean 흡수,
   builtin 분리, decorator 노드 grammar.js 추가, `@comment.note` 패턴
   확장.
2. **5/B 트랙 (별도 작업)**: §6 의 `lsp.hexa` 갱신 — magic number
   상수화, builtin defaultLibrary modifier, let readonly modifier,
   method 토큰 검토.
3. **검증 도구 (Y 트랙)**: §9.1 의 `nexus check --token-taxonomy`
   subcommand. tree-sitter CLI shim 활용 (이미 `--hexalint` 가 사용 중).
4. **문서 동기화**: 본 spec 을 `tooling/tree-sitter-hexa/README.md`
   (D 트랙 SSOT) 와 `hexa-lang/self/lsp.hexa` header comment (5b 트랙)
   에서 cross-reference.
5. **gap catalog 갱신**: `design/hexa_lang_gaps_from_atlas.md` Rank 6
   항목에 본 spec 1줄 추가 (이번 sweep 에서 처리).
6. **확장 후보**: 미래에 `module`, `import`, `trait` 등 hexa 키워드가
   늘어나면 § 4.3 의 namespace, class 칸을 활성화. LSP 표준에 새
   token type 추가 제안은 신중히 (호환성 깨짐).

---

## 부록 A. 카탈로그 차이 요약 (1-pager)

```
tree-sitter capture (18, base 13)        LSP token type (15)
─────────────────────────────────────    ─────────────────────────
@keyword                  ←→ keyword (9)
@type.builtin             ←→ type+defLib (1+mod3)
(none)                    ←→ namespace (0)        [양쪽 미사용]
(none)                    ←→ class/enum/struct (2/3/4)
@function                 ←→ function+decl (8+mod0)
@function.call            ←→ function (8)
@function.method          ←→ function (8)         [LSP 세분화 X]
(none)                    ←→ function+defLib (8+mod3) [LSP 세분화]
@variable                 ←→ variable (6)
@variable.parameter       ←→ parameter (5)
@property                 ←→ property (7)
@number                   ←→ number (12)
@number.float             ←→ number (12)          [LSP 세분화 X]
@boolean                  ←→ keyword (9)          [충돌 — 통합 권장]
@string                   ←→ string (11)
@string.escape            ←→ (없음)               [tree-sitter only]
@operator                 ←→ operator (13)
@punctuation.bracket      ←→ (skip)               [tree-sitter only]
@punctuation.delimiter    ←→ (skip)               [tree-sitter only]
@comment                  ←→ comment (10)
@comment.note             ←→ comment (10)         [tree-sitter 세분화]
(none — grammar 추가 필요) ←→ decorator (14)      [LSP only]
```

총 매핑 충돌 1개 (boolean), tree-sitter only 4개, LSP only 1개,
세분화 비대칭 4개. canonical SSOT = LSP base 15종.
