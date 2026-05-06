# hexa Parser `loc` Injection — Design Spec

| Field | Value |
| --- | --- |
| 작성 | 2026-05-06 |
| 트랙 | B (hexa upstream patch) — 설계 only, 코드 미수정 |
| 소유 | 본 spec 만 |
| 파일럿 | `hexa lsp` initialize 응답 확인 — 정상 |
| 상위 | `design/hexa_lang_gaps_from_atlas.md` Rank 11 |
| 관련 | `design/hexa_cli_introspection_spec.md` (Rank 3 plan) |

---

## § 0. TL;DR

- hexa-lang 의 self-hosted parser (`hexa-lang/self/parser.hexa`, 4610줄) 는 토큰
  단계까지만 line/col 을 보존하고 AST 노드 (`#{ "kind": ..., "name": ... }`) 에는
  좌표를 전혀 전파하지 않는다.
- 결정적 결함: `hexa --ast file.hexa` 출력이 좌표 없는 트리이므로 외부 도구
  (introspect wrapper / LSP 백엔드 / refactor / atlas health) 가 모두 wrapper 텍스트
  스캔으로 회귀.
- **그러나 `hexa lsp` JSON-RPC 서버가 이미 작동 중**이다. `initialize` 응답에서
  `hover/definition/rename/semanticTokens` capability 를 advertise. 다만 정의 분석은
  `handle_definition` 이 `return "null"` 스텁 — 실제 symbol 위치 수신은 미구현이다.
- **권장 경로**: `hexa --ast` 의 native loc 패치 (Phase 4-Native) 보다
  **LSP 보강 + `hexa-introspect` 의 LSP backend shim** 이 비용/효과 우월. native
  parser 패치는 Phase 4-Native 로 백로그 유지.

---

## § 1. 현 상태 (B 트랙 발견 인용)

`atlas_recall_cycle_2026_05_06_retro.md` 사이클에서 발견된 사실 압축:

1. `self/lexer.hexa` (784줄) — `Token { kind, value, line, col }` 으로 line/col 보유.
2. `self/parser.hexa` (4610줄) — recursive-descent. ~135 개의 AST 빌더 site
   (`#{ "kind": "Foo", ... }` map literal 반환) 가 있고, 그 어디에도 `line`/`col`
   필드가 들어있지 않다.
3. `self/ast.hexa` (339줄) — `Stmt`/`Expr`/`FnDecl` 등 struct 정의. struct 필드에
   `line`/`col` 이 없다 (단, `Stmt` 는 자체적으로 28+ 필드. struct 필드 추가 시
   생성자 호출 site 전수 갱신 필요).
4. `self/lsp.hexa` (792줄) — JSON-RPC 서버. initialize/didOpen/didChange/hover/
   definition/semanticTokens/full 핸들 존재. **그러나** `handle_definition`,
   `handle_hover`, `handle_rename` 의 본문은 모두 `word_at_position` 빈 스텁에
   기반 → 실제 `definitionProvider` 응답은 항상 `null`.
5. 외부 wrapper `tooling/hexa-introspect/hexa_introspect.hexa` (Phase 1 완료) 는
   parser AST 가 좌표가 없으므로 `--symbols`/`--diag` 출력을 lexer 토큰 스캔으로
   재구성한다 (Phase 1 우회).

### 결정적 결함의 효과

| 소비자 | 현재 동작 | 손실 |
| --- | --- | --- |
| `hexa --ast file.hexa` | `kind`/`name` 만 print | 위치 정보 0 |
| LSP `definition` | `null` 반환 | go-to-definition 불가 |
| LSP `hover` | keyword/builtin doc 만 | 사용자 정의 심볼 hover 0 |
| `hexa-introspect --symbols` | lexer 토큰 스캔 우회 | parser 의존 0 → fragile |
| atlas health drift | 위치 차분 불가 | 변경 위치 식별 불가 |
| AST diff / refactor (Phase 5) | 불가능 | — |

---

## § 2. parser.hexa decl 빌더 인벤토리

본 절은 `parser.hexa` 의 AST 노드 반환 site 목록이다. 각 site 는
`p_advance()` (시작 토큰 소비) → 본문 → 본문 끝 (`p_expect(...)`) 형식의
**시작-토큰 line/col 을 첫 번째 advance 직전에 캡처**해 두면 확정적이다.

### 2.1 핵심 Decl 빌더 (Phase 4a 1차 대상, 11종)

| 빌더 fn | 라인 | 반환 kind | 시작 토큰 | 비고 |
| --- | --- | --- | --- | --- |
| `parse_let` | 1163 | `LetStmt` / `LetMutStmt` | `let` | + `DestructLetStmt` (1192), `MapDestructLetStmt` (1214) |
| `parse_const` | 1258 | `ConstStmt` | `const` | |
| `parse_static` | 1279 | `StaticStmt` | `static` | |
| `parse_fn_decl` | 1556 | `FnDecl` (1628) | `fn` | + 컨트랙트 inject (1604, 1660, 1668) |
| `parse_struct_decl` | 1825 | `StructDecl` (1858) + `StructField` (1845) | `struct` | type_params 후 fields |
| `parse_enum_decl` | 1868 | `EnumDecl` (1901) + `EnumVariant` (1888) | `enum` | |
| `parse_trait_decl` | 1911 | `TraitDecl` (1947) + 내부 `FnDecl` (1936) | `trait` | |
| `parse_impl_block` | 1957 | `ImplBlock` (1997) + 내부 `FnDecl` (1986) | `impl` | trait_name 분기 |
| `parse_use_decl` | 1506 | `UseStmt` (1512, 1526) | `use` / `import` | StringLit / path 두 분기 |
| `parse_mod_decl` | 1536 | `ModStmt` (1541) | `mod` | |
| `parse_type_alias` | 3584 | `TypeAlias` (3590) | `type` | |

> Phase 4a 패치 패턴: 각 함수 첫 줄 `p_advance()` 바로 앞에서
> `let _start = p_peek()` 으로 토큰 캡처 → 반환 map 에 `"line": _start.line,
> "col": _start.col, "end_line": <last>.line, "end_col": <last>.col` 추가.

### 2.2 보조 Decl 빌더 (Phase 4b 2차, 22종)

| 빌더 fn | 라인 | kind |
| --- | --- | --- |
| `parse_return` | 1300 | `ReturnStmt` |
| `parse_proof_stmt` | 1324 | `ProofStmt` |
| `parse_assert_stmt` | 1339 | `AssertStmt` |
| `parse_resume_stmt` | 1355 | `Resume` |
| `parse_invariant_stmt` | 1371 | `Invariant` |
| `parse_invariant_decl` | 1406 | `InvariantDecl` |
| `parse_for_stmt` | 2012 | `ForStmt` / `ForElseStmt` / `ForDestructStmt` |
| `parse_while_stmt` | 2090 | `WhileStmt` |
| `parse_loop_stmt` | 2110 | `LoopStmt` |
| `parse_try_catch` | 3334 | `TryCatch` |
| `parse_throw_stmt` | 3362 | `ThrowStmt` |
| `parse_panic_stmt` | 3375 | `PanicStmt` |
| `parse_recover_stmt` | 3390 | `RecoverStmt` |
| `parse_drop_stmt` | 3410 | `DropStmt` |
| `parse_spawn_stmt` | 3425 | `SpawnStmt` |
| `parse_scope_stmt` | 3438 | `ScopeStmt` |
| `parse_select_stmt` | 3451 | `SelectStmt` (+`SelectArm`) |
| `parse_async_fn` | 3480 | `AsyncFnDecl` |
| `parse_extern_fn` | 3552 | `ExternFnDecl` |
| `parse_atomic_let` | 3599 | `AtomicLet` |
| `parse_break_stmt` | 3625 | `BreakStmt` |
| `parse_continue_stmt` | 3645 | `ContinueStmt` |
| `parse_do_while_stmt` | 3664 | `DoWhileStmt` |
| `parse_defer_stmt` | 3689 | `DeferStmt` |
| `parse_yield_stmt` | 3757 | `YieldStmt` |
| `parse_comptime_stmt` | 3773 | `ComptimeFnDecl` / `ComptimeConst` / `ComptimeLet` / `ComptimeAssert` / `ComptimeBlock` |
| `parse_intent_stmt` | 3862 | `IntentStmt` (+`IntentField`) |
| `parse_verify_stmt` | 3901 | `VerifyStmt` |
| `parse_generate_stmt` | 3920 | `GenerateFnStmt` / `GenerateStmt` |
| `parse_optimize_stmt` | 3973 | `OptimizeFnStmt` |
| `parse_effect_decl` | 3996 | `EffectDecl` (+`EffectOp`) |
| `parse_pure_fn` | 4039 | `PureFnDecl` |
| `parse_macro_def` | 4062 | `MacroDef` (+`MacroRule`) |
| `parse_derive_decl` | 4116 | `DeriveDecl` |
| `parse_theorem_stmt` | 4143 | `TheoremStmt` |
| `parse_handle_stmt` | 4164 | `HandleWithStmt` (+`EffectHandler`) |
| `parse_with_stmt` | 2376 | `WithStmt` |
| `parse_guard_stmt` | 2339 | `GuardStmt` / `GuardLetStmt` |
| `parse_labeled_loop` | 3716 | (재포장: 라벨 부착) |

### 2.3 Expression 빌더 (Phase 4c 3차, 식별 결과)

| 빌더 fn | 라인 | kind 다중 | 시작 토큰 |
| --- | --- | --- | --- |
| `parse_primary` | 2984 | `IntLit`/`FloatLit`/`BoolLit`/`StringLit`/`CharLit`/`Ident`/`EnumPath`/`StructInit`/`Tuple`/`Array`/`ListComp`/`MapLit`/`MapEntry`/`Wildcard`/`Lambda`/`ComptimeExpr` | `tok = p_peek()` 직접 사용 가능 |
| `parse_postfix` | 2745 | `Call` (2769), `Field` (2792), `Index` (2783, 2849), `Slice` (2823, 2840), `OptField` (2804), `BinOp(as)` (2862) | postfix 시작 = LParen/Dot/LBracket 토큰 |
| `parse_unary` | 2715 | `UnaryOp` (2721, 2733) | `Not`/`Minus`/`BitNot`/`Typeof` |
| `parse_addition` / `parse_multiplication` / `parse_or` / `parse_and` / `parse_pipe` / `parse_null_coal` / `parse_bit_ops` / `parse_comparison` / `parse_bitwise` / `parse_range` | 2436–2697 | `BinOp` (다수), `Range` (2652, 2668) | 좌측 self.left 의 line/col 채택 권장 |
| `parse_expr` (walrus) | 2425 | `WalrusExpr` | left.line 그대로 |

> Expression 노드는 통계적으로 가장 많지만 (~30 site), 코드 작용 시
> __left/right child 의 `line`/`col` 을 조합__ 하면 추가 추적 없이도 부모 좌표
> 추정 가능 (left 시작, right 끝). decl 패치 후 Phase 4c 에서 한 번에 처리.

### 2.4 ContractAssert 합성 노드 (서브-패턴)

`parse_fn_decl` 본체에서 `@contract` 디슈가가 합성하는 노드 (1604/1652/1660/1668)
는 시작 토큰이 없다. 본 fn 의 시작 토큰을 그대로 채택 + `synthetic: true`
플래그를 얹는다.

### 2.5 총계

- map literal `kind` site: ~135 (grep 결과)
- 그 중 **decl/stmt 빌더** (Phase 4a+4b): 33
- **expression 빌더** (Phase 4c): ~30
- **하위 노드** (StructField/EnumVariant/Param/MatchArm/SelectArm/EffectOp/MacroRule/IntentField/MapEntry/FieldInit/Spread/RestPattern/EnumPath in pattern context 등): ~30

---

## § 3. ast.hexa 변경안

현재 `ast.hexa` 는 struct 정의 + 생성자 헬퍼만 보유. parser 가 이를 직접 쓰지
않고 매번 `#{...}` map literal 을 만들기 때문에 **struct 필드 추가는 의미가
없다**. 두 갈래:

### 3.1 옵션 A — Map literal 패턴 (권장)

- `ast.hexa` 에 단일 헬퍼 `fn loc(tok) { return #{"line": tok.line, "col": tok.col} }`
  추가. 또는 4-필드 평탄 합치 헬퍼 `fn with_loc(node, start, end) { ... }`.
- 모든 빌더 site 에서 map literal 끝 줄에 `"line": _start.line, "col": _start.col,
  "end_line": _end.line, "end_col": _end.col` 4 필드를 추가.
- `empty_node()` 에도 `"line": 0, "col": 0, "end_line": 0, "end_col": 0` 추가
  (디폴트).
- 비용: parser.hexa ~135 site 에 4 필드 삽입. mechanical, 후속 grep 가능.

### 3.2 옵션 B — Struct 마이그레이션 (백로그)

- `Stmt`/`Expr`/`FnDecl` 등 13개 struct 에 `line: int, col: int, end_line: int,
  end_col: int` 추가.
- 모든 struct literal `Foo { ... }` 에 4 필드 추가 (수많은 ai_native_pass / mk2
  소비자도 영향). 대규모 ABI 변경.
- 본 사이클 outscope. 옵션 A 먼저 정착 후 후속 사이클에서.

### 3.3 키 명명 표준

| 키 | 의미 | 형식 |
| --- | --- | --- |
| `line` | 시작 라인 (1-base, lexer 와 동일) | int |
| `col`  | 시작 컬럼 (1-base) | int |
| `end_line` | 끝 토큰 라인 | int |
| `end_col`  | 끝 토큰 컬럼 + 길이 | int |

LSP 호환성: LSP 는 0-base 이므로 LSP 직렬화 단계에서 -1 변환.

---

## § 4. 패치 단계

### Phase 4-LSP (권장 우선, 0.5–1일)

1. `hexa-lang/self/lsp.hexa` 의 `handle_definition` / `handle_hover` /
   `handle_rename` 본문에 **lexer-기반 symbol index** 구현. AST 좌표 없이도 lexer
   tokens 로 `Ident` 출현 위치를 모두 모아 word_at_position → 첫 def 매칭으로
   `Location` 반환 가능.
2. `tooling/hexa-introspect/hexa_introspect.hexa` 에 `--lsp-shim` 모드 추가:
   `hexa lsp` 를 sub-process 로 띄우고 JSON-RPC 로 `definition`/`hover` 던져 받은
   결과를 stdout 평문으로 변환.
3. 외부 도구는 `hexa-introspect --symbols` (Phase 1) 그대로 유지하되 좌표가
   필요한 경우 `--lsp-shim` 사용.
4. 이점: parser.hexa 무수정. 4610줄 위험 영역 회피.

### Phase 4-Native (백로그, 3–5일)

1. **Day 1**: `parse_let` / `parse_const` / `parse_static` / `parse_fn_decl` /
   `parse_struct_decl` / `parse_enum_decl` / `parse_use_decl` / `parse_type_alias`
   8 site 패치 (Phase 4a 1차). golden test: `hexa --ast self/lexer.hexa` diff.
2. **Day 2**: `parse_trait_decl` / `parse_impl_block` / `parse_async_fn` /
   `parse_extern_fn` / `parse_pure_fn` / `parse_effect_decl` / `parse_macro_def`
   / `parse_handle_stmt` (Phase 4a 잔여 + decl 합성).
3. **Day 3**: control-flow stmt builder (`for`/`while`/`loop`/`break`/`continue`/
   `defer`/`yield`/`return`/...) ≈ 22 site (Phase 4b).
4. **Day 4**: expression 빌더 (Phase 4c). left-child propagation 패턴.
5. **Day 5**: bootstrap 회귀 — `hexa-lang/self/main.hexa` 자체가 parser 출력에
   의존 (`parse(tokens)` 결과 stmts 의 `kind`/`name` 만 읽음). 추가 필드는
   읽기에 영향 X 이지만 모든 `_check_main_double_invoke` 패턴 등 검증.
6. **Phase 4d**: `tooling/hexa-introspect` Phase 2 — 실 AST 기반 `--symbols`,
   `--ast --json`. wrapper 폐기.

### Phase 4-AST-JSON (병행 가능)

- `hexa --ast file.hexa --json` 추가: 현재 `print_ast` 는 indent 텍스트. JSON
  serializer 추가 시 `loc` 필드까지 그대로 dump → 외부 도구 1-pass 소비 가능.

---

## § 5. 영향 분석

| 항목 | Phase 4-LSP | Phase 4-Native |
| --- | --- | --- |
| parser.hexa 수정 | 0 | ~135 site |
| ast.hexa 수정 | 0 | 1 줄 (헬퍼) |
| lsp.hexa 수정 | ~50 줄 | 동일 + |
| 호환성 위험 | 매우 낮음 (LSP 신규 기능) | 중 (AST 소비자 폭증, 모든 `kind` 분기 코드) |
| Performance | LSP 호출 IPC 1-RTT (≤ 50ms) | 좌표 4필드 추가 (~파싱 time +5%) |
| 출력 크기 | LSP JSON (작음) | `--ast` 출력 ~1.4× |
| AI 도구 (정의 점프) | OK | OK (더 직접적) |
| atlas drift 위치 차분 | 부분적 (LSP definition limited) | 완전 |
| Refactor (Phase 5) | 불가 | 가능 |

---

## § 6. 기존 LSP 와의 관계 (파일럿 결과)

### 6.1 작동 확인

```text
$ printf 'Content-Length: 76\r\n\r\n{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"capabilities":{}}}' | hexa lsp
Content-Length: 538

{"jsonrpc":"2.0","id":1,"result":{"capabilities":{
  "textDocumentSync":1,
  "completionProvider":{"triggerCharacters":[".",":","@"]},
  "hoverProvider":true,
  "definitionProvider":true,
  "renameProvider":true,
  "semanticTokensProvider":{
    "legend":{"tokenTypes":[...,15 종],"tokenModifiers":[...,4 종]},
    "full":true
  }
},"serverInfo":{"name":"hexa-lsp","version":"0.1.0"}}}
__HEXA_RC=0
```

→ **LSP 서버가 살아있다**. JSON-RPC initialize 정상 응답.

### 6.2 지원 메서드 (lsp.hexa run_lsp 디스패치)

| LSP method | 상태 | 좌표 정보 |
| --- | --- | --- |
| `initialize` | OK | n/a |
| `shutdown` / `exit` | OK | n/a |
| `textDocument/didOpen` | 문서 저장 + 빈 diag | n/a |
| `textDocument/didChange` | 문서 갱신 | n/a |
| `textDocument/hover` | **스텁** (`word_at_position` = `""`) | 없음 |
| `textDocument/definition` | **스텁** (`null` 반환) | 없음 |
| `textDocument/semanticTokens/full` | **OK** (lexer 재토큰화 → delta-encoded) | line/col 정확 |
| `textDocument/rename` | 스텁 | 없음 |
| 기타 | method-not-found | — |

### 6.3 결론

- **semantic tokens 는 이미 line/col 정확** — 에디터 syntax highlight 는 즉시 가용.
- **definition/hover/rename 은 본문 미구현** — `word_at_position` 이 `""` 반환
  스텁이므로 모든 응답 `null`.
- ⇒ LSP 가 native `--ast` 를 우회할 능력은 **부분적 (semantic tokens only)**.
  symbol resolution 까지 가려면 lsp.hexa 보강이 필요. 그러나 이 보강은
  parser.hexa 4610줄 패치보다 훨씬 작다 (~50–100 줄, lexer 토큰 인덱스 + 단순
  scope walk).

---

## § 7. 우선순위 결정

| 트랙 | 비용 | 효용 | 권장 |
| --- | --- | --- | --- |
| Phase 4-LSP (lsp.hexa 보강 + introspect shim) | 0.5–1일 | 80% (definition/hover/diagnostics 가용) | ★ **우선** |
| Phase 4-Native (parser.hexa 좌표 주입) | 3–5일 | 100% (`--ast` 까지 좌표) | 백로그 |
| Phase 4-AST-JSON (`--ast --json` only) | 0.5일 | 보조 | Phase 4-Native 와 묶음 |

### 7.1 본 사이클 후속 권고

1. **즉시**: Phase 4-LSP 진행 — `handle_definition` / `handle_hover` /
   `word_at_position` 본문 채우기 + symbol index. `tooling/hexa-introspect/`
   Phase 2 는 LSP-shim 으로.
2. **차후 사이클**: Phase 4-Native 백로그. atlas drift 정밀화, refactor 도구
   요구 발생 시 착수.

### 7.2 Phase 4-LSP 구현 결과 (2026-05-06 land)

> **Status update (2026-05-06 14:00 JST):** Phase 4-LSP 풀구현 적용 완료.
> 디스크 lsp.hexa 823 → 996 (+173줄). `_is_ident_start`/`_is_ident_part`/
> `_line_text` 헬퍼 + `word_at_position` (실구현) + `find_symbol` (top-level
> decl 검색, 모디파이어 strip) + `find_all_occurrences` (string/comment
> 회피, 식별자 boundary 검증) + `handle_definition` (Location JSON) +
> `handle_hover` (사용자 심볼 markdown) + `handle_rename` (WorkspaceEdit
> changes) 모두 본문 채움. `hexa parse self/lsp.hexa` OK. initialize 회귀
> 0 (538-byte capability 응답 동일).

`hexa-lang/self/lsp.hexa` 보강 완료 (792 → 996 줄, Δ+204).

#### 구현 메서드

| 함수 | 줄 위치 | 동작 |
| --- | --- | --- |
| `word_span_at_position` (신규) | 533–574 | line 단위 `index_of("\n")` 로 타깃 행 추출 → 행 내 char 워크. identifier 스팬 (start_col / end_col) + 단어 반환 |
| `word_at_position` (재구현) | 576–579 | 위 헬퍼 래핑. `""` 또는 식별자 |
| `find_symbol` (신규) | 619–676 | `_split_lines` + 라인-prefix decl 매칭 (`fn`/`let`/`const`/`static`/`struct`/`enum`/`trait`/`type`/`effect`/`macro`, 모디파이어 `pub`/`async`/`pure`/`extern`/`comptime` 스트립) |
| `find_all_occurrences` (신규) | 681–737 | 식별자 토큰 출현 위치 전수 (string/comment/char-lit 스킵). rename 용 |
| `handle_definition` (재구현) | 754–763 | `word_at_position` → `find_symbol` → `Location[]` JSON 반환 |
| `handle_hover` (재구현) | 770–793 | keyword/builtin/사용자 심볼 markdown |
| `handle_rename` (재구현) | 802–823 | `find_all_occurrences` 기반 `WorkspaceEdit` JSON |
| `_dispatch_message` (분리) | 1059–1124 | 단일 메시지 디스패치 (init/didOpen/didChange/hover/definition/rename/semanticTokens/full/exit) |
| `run_lsp_from_buffer` (신규) | 1141–1180 | `read_stdin()` 한방 슬럽 → Content-Length 프레임 워크 디스패치. 멀티-메시지 배치 처리 핵심 |
| `run_lsp` (재구현) | 1182–1208 | 버퍼 모드 우선, 빈 stdin → 레거시 readline path |

#### 부수 fix

- `json_get_string` 전면 재작성 (string-level intrinsics 사용). 원
  구현은 char-by-char 루프 + array push + join 으로, lsp.hexa 같은 큰
  파일 안에서 인터프리터 함수-콜 오버헤드가 결합되어 ~3KB 바디 디코드가
  >30s 걸렸음. `replace` chain 으로 `\"`/`\n`/`\r`/`\t`/`\/`/`\\`
  디코드. **남은 갭**: `\uXXXX` 디코드 미구현 → 박스 드로잉 char (예
  `═`=`═`) 가 들어간 소스에서 line/col 어긋남 (verify 시 우회
  fixture 사용).
- `run_lsp` 멀티-메시지 처리 — 원 구현은 `input(N)` (`getline()` 래퍼)
  으로 fixed-byte 가정이 깨져 메시지 경계 정렬 실패. `read_stdin()` 으로
  전체 스트림을 슬럽 후 메모리 워크. 시퀀셜 클라이언트 (printf 파이프 /
  test driver) 회귀 0.

#### 검증 결과

| 케이스 | 결과 |
| --- | --- |
| `initialize` 회귀 (538-byte capability 응답) | OK (regression 0) |
| `tiny.hexa` (2 fn) hover/definition/rename | OK |
| `/tmp/lsp_verify.hexa` (20-line ASCII fixture) | OK — `_ns_now` use→def, hover signature, rename 3 occurrences (def + 2 use) |
| `lookup.hexa` 50-line 발췌 (line 25 `_ns_now` decl) | hover OK ("defined at line 26"), definition OK |
| `lookup.hexa` 풀 (478 line, 14KB) | hover/definition null — `═` (box drawing) 미디코드로 line 카운팅 어긋남 (스펙 § 8 후속) |

#### LSP 응답 예시

`hover` (use site `_ns_now()` at line 13 col 17 of `/tmp/lsp_verify.hexa`):

```json
{
  "contents": {
    "kind": "markdown",
    "value": "**fn** `_ns_now`\n\n```hexa\nfn _ns_now() -> i64 {\n```\n\n_defined at line 4_"
  }
}
```

`definition` (same position):

```json
[{"uri":"file:///tmp/lsp_verify.hexa",
  "range":{"start":{"line":3,"character":3},
           "end":{"line":3,"character":10}}}]
```

`rename` (newName `_ns_clock`, 3 occurrences):

```json
{"changes":{"file:///tmp/lsp_verify.hexa":[
  {"range":{"start":{"line":3,"character":3},"end":{"line":3,"character":10}},"newText":"_ns_clock"},
  {"range":{"start":{"line":13,"character":13},"end":{"line":13,"character":20}},"newText":"_ns_clock"},
  {"range":{"start":{"line":17,"character":13},"end":{"line":17,"character":20}},"newText":"_ns_clock"}
]}}
```

#### ROI 평가 (vs § 7 80% 추정)

| 기능 | 가용? | 비고 |
| --- | --- | --- |
| LSP `definition` (정확한 line/col) | ✅ ASCII 소스 | unicode escape 시 어긋남 |
| LSP `hover` (사용자 심볼 시그니처) | ✅ ASCII 소스 | 동일 제약 |
| LSP `rename` (single-file workspace edit) | ✅ ASCII 소스 | 동일 제약 |
| LSP `semanticTokens/full` | ✅ (기존 유지) | 회귀 0 |
| `\uXXXX` decode | ✅ BMP-only (2026-05-06 land) | `json_get_string` escape parser 에 4-hex → `from_char_code` UTF-8 추가 (lsp.hexa 792→823). surrogate pair 후속 |
| Multi-file workspace mode | ❌ | rename 단일-file 에 한정 |

**결론**: 80% 목표 달성 부분 — ASCII 소스 한정으로 hover/definition/rename
모두 작동. \uXXXX 디코드는 후속 사이클 (Phase 4-LSP++) 에서 추가 권장.
parser.hexa 4610줄 패치 회피라는 핵심 가치는 보존되었음.

---

## § 8. 후속 (Phase 5)

- **AST diffing**: 같은 파일 두 버전의 `--ast --json` diff → 위치-aware change set.
- **Semantic-aware refactor**: `Ident` 노드 정의 site 에서 모든 use site rename.
  Phase 4-Native 좌표 + 후행 scope analysis 필요.
- **atlas health AST trace**: drift 경고 시 변경 노드의 `loc` 를 health timeline
  에 자동 첨부.
- **tree-sitter parity (gaps Rank 6)**: tree-sitter grammar 가 손쉽게 좌표를
  내놓으므로 LSP 가 안정 단계에 진입하면 grammar 외부화도 검토 (cross-editor).

---

## § 9. 부록 — 파일럿 명령

```bash
# LSP 작동 확인 (initialize → exit)
(printf 'Content-Length: 76\r\n\r\n{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"capabilities":{}}}'; \
 sleep 0.5; \
 printf 'Content-Length: 32\r\n\r\n{"jsonrpc":"2.0","method":"exit"}') | timeout 5 hexa lsp

# Decl 빌더 inventory 재현 (parser.hexa 의 모든 kind site)
grep -nE '^\s*"kind":\s*"[A-Z][A-Za-z]+"' /Users/ghost/core/hexa-lang/self/parser.hexa \
  | sed -E 's/.*"kind":\s*"([^"]+)".*/\1/' | sort | uniq -c | sort -rn
```

---

## 변경 이력

| 일자 | 변경 |
| --- | --- |
| 2026-05-06 | 초안 — Phase 4-LSP 우선 권고. Phase 4-Native 백로그. |
| 2026-05-06 | § 7.2 추가 — Phase 4-LSP land. lsp.hexa 792→1247줄. hover/definition/rename 구현 + 검증 (ASCII 소스). \uXXXX 디코드는 후속. |
| 2026-05-06 | 잔여 후속 1/3 완료 — `\uXXXX` BMP decode (`json_get_string`) +31줄 (lsp.hexa 792→823). initialize 회귀 0. workspace rename / find_all_occurrences perf 는 후속. |
