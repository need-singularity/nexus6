# hexa-introspect Phase 3 — `--refs` / `--hover` 설계 (2026-05-06)

본 문서는 `hexa_introspect.hexa` 에 Phase 3 두 모드(`--refs`, `--hover`)
를 추가하기 위한 단일 진실원이다. spec: `design/hexa_cli_introspection_spec.md`
§ 2.4, § 2.5. 본 문서가 정한 시그너처/스키마는 PHASE3_PATCH.md 에 그대로
재료로 들어간다.

## 0. 동시 작업 가드

- Phase 2 (`--check`) 는 다른 에이전트가 같은 파일 (`hexa_introspect.hexa`) 에서
  진행 중. 본 임무 시작 직후 mtime 갱신이 관찰됨 (07:51).
- 정책에 따라 `hexa_introspect.hexa` 직접 수정은 보류, **patch 파일**만
  PHASE3_PATCH.md 에 기록한다. Phase 2 머지 직후, 별도 에이전트(혹은 본인)가
  patch 를 적용한다.
- 본 설계는 Phase 2 의 dispatch 분기 (`mode == "--check"`) 와 자연스럽게
  맞물리도록 dispatch 부분만 추가하는 형태로 작성한다. Phase 2 가 도입할
  scanner 헬퍼 (string/comment guard 등) 는 재사용한다.

## 1. 인터페이스

### 1.1 `--refs <file.hexa> <symbol>`
- 입력: 파일 경로 + 식별자 (단일 단어, `[A-Za-z_][A-Za-z0-9_]*`).
- 동작: scanner 1패스 → 식별자 토큰 위치를 모두 수집. 문자열/코멘트는 제외.
- 출력: NDJSON, 1줄/참조.
  ```json
  {"name":"_ns_now","loc":{"line":34,"col":15},"end_loc":{"line":34,"col":21},"context":"  let t = _ns_now()","kind":"call","file":"...lookup.hexa"}
  ```
- 분류 규칙 (`kind`):
  - `decl`  — 토큰 직전이 decl 키워드 (`fn|let|const|static|struct|enum|trait|impl|type`)
    + brace_depth==0 + (선택적 `pub` / `mut` 사이공백) 인 경우.
  - `call`  — 토큰 다음 비공백 char 이 `(` 인 경우. (decl 분류가 우선)
  - `reference` — 그 외 모든 등장. (rvalue read, lvalue write, type 인용 등)
- spec § 2.4 의 `role: "def"|"read"|"write"|"call"|"lexical"` 와는 명세 차이가
  존재 — 본 임무 지시문(컨텍스트)이 `decl|call|reference` 3분류를 명시했으므로
  본 doc 가 SSOT. spec.md 는 Phase 3 검증 섹션에 "structural fallback: 3-bucket"
  을 명기하는 식으로 정합 (§5 참조).

### 1.2 `--hover <file.hexa> <line>:<col>`
- 입력: 파일 + `<line>:<col>` (1-based).
- 동작:
  1. 위치를 포함하는 식별자 토큰 추출 (없으면 `{}` exit 0).
  2. scan_decls 결과에서 `name == 토큰` 인 첫 항목을 picking.
  3. 해당 항목을 단일 JSON object 로 직렬화.
- 출력 (예):
  ```json
  {"name":"_ns_now","kind":"fn","sig":"fn _ns_now() -> i64","type":"i64","loc":{"line":26,"col":1},"end_loc":{"line":41,"col":2},"visibility":"priv","doc":null,"file":"...lookup.hexa"}
  ```
- 토큰은 있으나 decl 표에 없으면 → `{"name":"<token>","kind":null,...}` 가 아니라
  spec § 2.5 가 허용하는 모든-필드 채우기는 부담이므로 **`{}` 반환**으로 단순화.
  Phase 3.5 에서 cross-file resolve 도입 시 hover 응답을 확장한다.

## 2. 구현 위치

`hexa_introspect.hexa` 내 신규 추가:
1. `fn _is_decl_kw(w: string) -> bool` — `_kw_to_kind(w) != ""` 또는 `w == "pub"`.
2. `fn scan_refs(src: string, target: string) -> [string]` — scanner 의 string/
   comment/brace state 를 그대로 복제하면서, 식별자 토큰이 `target` 과 일치할 때
   `#{ name, line, col, end_line, end_col, kind, context }` 를 누적.
3. `fn refs_to_ndjson(file, refs) -> string` — 1줄/참조, NDJSON.
4. `fn pick_token_at(src, line_starts, line, col) -> #{name, ...}|null` — 위치
   기반 토큰 추출 (substring(line_start..line_end) 에서 col 포함하는 word
   확장).
5. `fn hover_to_json(file, decl|null) -> string` — 단일 object 또는 `{}`.
6. dispatch 분기 추가:
   ```hexa
   if mode == "--refs" {
       if len(a) < 5 { _usage(); exit(1) }
       let target = a[4]
       let refs = scan_refs(src, target)
       println(refs_to_ndjson(file, refs))
       _emit_meta("refs", ms, refs.len(), file); exit(0)
   }
   if mode == "--hover" {
       if len(a) < 5 { _usage(); exit(1) }
       let lc = a[4]      // "L:C"
       let parts = lc.split(":")
       if parts.len() < 2 { _usage(); exit(1) }
       let line = to_int(parts[0]); let col = to_int(parts[1])
       let line_starts = _build_line_starts(src)
       let tok = pick_token_at(src, line_starts, line, col)
       if tok == null { println("{}"); exit(0) }
       // decls 표에서 첫 매칭 찾기
       let mut hit = null
       let mut i = 0
       while i < decls.len() {
           let d = decls[i]
           if to_string(d.name) == to_string(tok.name) { hit = d; break }
           i = i + 1
       }
       println(hover_to_json(file, hit))
       _emit_meta("hover", ms, if hit == null { 0 } else { 1 }, file); exit(0)
   }
   ```

## 3. 스캐너 재사용

`scan_refs` 는 `scan_decls` 와 같은 state machine 을 사용한다. 차이점:
- decl 누적 대신, **모든** 식별자 토큰을 검사하고 `target` 과 일치 시 push.
- `brace_depth==0` 제약 없음 (참조는 어디서든).
- `kind` 결정 휴리스틱:
  ```
  decl_keyword_seen_just_before = ( 토큰 직전 비공백 토큰 in
       {fn,let,const,static,struct,enum,trait,impl,type,use,import}
       또는 (pub <kw>) ) AND brace_depth==0 AT 토큰 시작
  → decl
  else {
      next_non_ws = src 의 토큰_end 이후 첫 비공백 char
      if next_non_ws == "(" → call
      else                  → reference
  }
  ```
- `context` 는 `line_starts[line] .. (next \n)` 의 substring 을 trim.
  string-join 비용을 줄이기 위해 line_starts 룩업 후 한 번에 substring.

## 4. 메모리/성능

- `scan_decls` 는 30KB 파일 한 번 — 20–40ms. `scan_refs` 도 같은 차수 (state
  machine 동일, push 횟수만 다름). 60KB 파일에서 100ms 이하 목표.
- `bin/hexa-introspect` 의 `HEXA_MEM_CAP_MB=2048` 설정은 그대로 유효 — Phase 3
  에서 메모리 추가 사용은 미미 (refs 배열 + line context 문자열).
- bin shim 은 case 문 확장만 필요 (PHASE3_PATCH.md § 4 참조).

## 5. spec 정합

- `design/hexa_cli_introspection_spec.md` § 2.4 의 `role` 라벨이 `def/read/write/call/
  lexical` 5종으로 정의됨. Phase 3 single-file 구현은 lexical scan 만 가능 —
  `read` vs `write` 구분(LHS 인지 RHS 인지) 은 AST 레벨 정보가 필요. 따라서
  **Phase 3 는 3-bucket (decl|call|reference)** 로 좁힘. spec.md § 10 검증 섹션과
  § 6 비교표를 갱신하면서 본 좁힘을 명시.
- spec § 2.5 `Hover` 의 `def_loc` 필드는 single-file 모드에선 자기 자신과 동일
  → `loc/end_loc` 로 충분. Phase 3.5 에서 cross-file 시 `def_loc` 부활.
- 비교표 (§6): Phase 3 완료 시 LSP **70% → 80%** 도달 (refs/hover 가 LSP 의
  핵심 navigate 표면 절반 차지). spec.md § 6 후미에 "Phase 3 (single-file
  refs/hover) 완료 시 LSP 80% 효과" 행을 추가.

## 6. 검증 (patch 적용 직후 가능)

```
# 1) refs — _ns_now 의 def + 2 호출 = 3 줄
hexa-introspect --refs mk2_hexa/mk2/src/atlas/lookup.hexa _ns_now \
  | jq -c '{l:.loc.line,k:.kind}' | sort -u

# 2) hover — fn 정의 라인
hexa-introspect --hover mk2_hexa/mk2/src/atlas/lookup.hexa 26:1 \
  | jq '{name,kind,sig}'   # → fn _ns_now() -> i64

# 3) hover 빈 위치
hexa-introspect --hover mk2_hexa/mk2/src/atlas/lookup.hexa 999:1
# → "{}"
```

기대 출력:
- `--refs _ns_now lookup.hexa`: NDJSON 3+ 줄 (decl=1, call=2 — 라인 26/279/368).
- `--hover 26:1`: `{"name":"_ns_now","kind":"fn","sig":"fn _ns_now() -> i64","type":"i64",...}`.
- `--hover 999:1`: `{}` exit 0.

## 7. 후속 (Phase 3.5 / 4)

- **Phase 3.5** (workspace): `--refs --workspace <symbol>` — `find ... -name
  '*.hexa'` 글롭 + 파일별 `scan_refs` 병렬, NDJSON 누적. 캐시는
  `state/hexa_refs_cache.ndjson` (mtime-keyed).
- **Phase 4** (native parser.hexa loc): hexa 컴파일러 본체에 line/col 정보
  유지 — 그러면 본 wrapper 의 state machine 을 폐기하고 컴파일러 직렬화로
  교체. 현 wrapper 는 그때까지 SSOT.

## 8. 소유 및 충돌 회피

- 이 doc 가 신규 (소유 충돌 0).
- `PHASE3_PATCH.md` 도 신규.
- `hexa_introspect.hexa` 직접 수정은 Phase 2 머지 후, 별도 작업으로.
- `design/hexa_cli_introspection_spec.md` § 6 / § 10 만 갱신 (Phase 3 행 추가).
- `design/hexa_lang_gaps_from_atlas.md` 는 Phase 2 가 갱신 중 — **본 임무에서
  건드리지 않음**.
