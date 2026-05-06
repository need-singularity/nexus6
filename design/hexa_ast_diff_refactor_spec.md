# hexa AST Diff & Semantic-Aware Refactor — Design Spec

| Field | Value |
| --- | --- |
| 작성 | 2026-05-06 |
| 트랙 | B (hexa-introspect Phase 5) — 설계 only, 코드 미수정 |
| 소유 | 본 spec 만 |
| 상위 | `design/hexa_parser_loc_injection_spec.md` § 8 (후속 Phase 5) |
| 자매 | `design/hexa_cli_introspection_spec.md` § 5.5 (AST diff 사용 예) |
| 관련 | `design/hexa_lang_gaps_from_atlas.md` (NEW: hexa-ast-diff-semantic-refactor) |
| 종속 | Phase 1 (`--ast`/`--symbols`) ✓, Phase 2 (`--check`) WIP, Phase 3 (`--refs`/`--hover`) PR 대기, Phase 4-LSP shim WIP |
| 비-종속 | Phase 4-Native (parser.hexa loc 주입) — 본 spec 은 lexer-fallback + LSP shim 만으로도 5a 완성 가능 |

---

## § 0. TL;DR

- **목표**: `hexa-introspect` 에 `--diff`, `--diff-rename`, `--diff-sig` 3 서브커맨드 추가. 텍스트 (line) diff 가 아닌 **semantic-aware AST 차분** 을 NDJSON 으로 emit.
- **5a (단순 diff, 1–2일)**: 두 파일/두 commit 의 symbol 수준 변경 분석. 함수 추가/삭제/이름변경/시그니처변경/모듈이동 5 change-kind.
- **5b (자동 적용, 3–5일)**: rename/sig-change 가 발생했을 때 호출처 (Phase 3 `--refs` 결과) 를 자동 갱신하는 **workspace edit** emit + dry-run.
- **tree-sitter 와의 분담**: tree-sitter 는 **CST (concrete) 비교** — line/col 정확, 식 단위 변경 고감도; introspect 는 **AST (semantic) 비교** — symbol/scope 인식. 본 spec 은 **introspect 가 SSOT**, tree-sitter 는 위치 보강 (hash-anchor) 으로만 활용.
- **LSP 와의 분담**: 본 spec 은 **LSP 응답 형식** (`WorkspaceEdit`, `RenameFile`) 을 채택. 5b 는 LSP `workspace/applyEdit` 메시지 호환 NDJSON 을 emit → 향후 native LSP 승격 시 wrap-only.
- **갭 카탈로그 신규 등재**: `hexa-ast-diff-semantic-refactor` (Rank 14, 본 spec 후속).

---

## § 1. 동기 (Why AST diff?)

### 1.1 텍스트 diff 의 한계 (atlas 사이클 실측)

`mk2_hexa/mk2/src/atlas/` 5 모듈 + `n6/atlas_query.hexa` 의 최근 30일 git log
관찰 결과 dominant 변경 패턴은 다음 5종:

| 패턴 | 빈도 (2026-04-06 ~ 2026-05-06) | git diff 가시성 | 의미 |
| --- | --- | --- | --- |
| 함수 본문 미세 수정 (1–5 lines) | 매우 높음 | 직관적 | 의미 보존, refactor 영향 없음 |
| **함수 이름 변경** (`_ns_now` → `ns_now_safe`) | 중 | line-noise 가득 (호출처 N 군데 동시 변경) | 의미: rename + 모든 use-site fan-out |
| **파라미터 추가/제거** (예: `lookup(id)` → `lookup(id, hint)`) | 중 | def line + 호출처 N 라인 동시 수정 | 의미: 시그니처 변경 → backward-compat? |
| **return type 변경** (`-> string` → `-> Result<string>`) | 낮음 | 1 line def + 호출처 unwrap 패턴 강제 | 의미: ABI 깨짐, 호출처 컴파일 에러 보장 필요 |
| **모듈 분리/병합** (lookup.hexa 일부 → mod.hexa 이전) | 낮음 | 두 파일에 add/remove 페어, **rename 인식 X** | 의미: 동일 함수가 위치만 이동, 호출자 import 갱신 |

git diff 의 문제: **하단 4 패턴 모두 "변경된 라인 N개" 로만 보이고**, 변경의
의도 (rename vs 본문수정 vs 모듈이동) 가 사람에 의해 매번 재구성되어야 한다.

### 1.2 AST diff 의 효용

| 측면 | 텍스트 diff | AST diff |
| --- | --- | --- |
| 단위 | line | symbol (fn/let/struct/...) |
| rename 인식 | X (add+remove 페어) | O (`change_kind: "renamed"`) |
| 시그니처 변경 분리 | X (라인 노이즈) | O (`change_kind: "signature_changed"`) |
| 본문 변경 vs 헤더 변경 | 동등 취급 | 분리 (`body_changed` vs `signature_changed`) |
| 호출처 영향 분석 | 외부 grep 필요 | `--diff-rename` 으로 내장 |
| whitespace/주석 변경 | 노이즈 (false-positive) | 무시 (구조 동일) |
| review 부담 | 라인 N 수에 비례 | symbol K 수에 비례 (보통 K ≪ N) |

### 1.3 atlas 갭 카탈로그 13항목 중 AST diff 로 해소되는 것

| 갭 | AST diff 효용 |
| --- | --- |
| `ns-time-fallback-stdlib` | 5+ 파일에 복붙된 `_ns_now()` SSOT 가 drift 시 즉시 발견 (`--diff a.hexa b.hexa` → fn body hash 비교) |
| `entry-point-vs-library-dual-mode` | `dispatch()` fn 시그니처가 모듈 간 일관성 유지하는지 cross-file 비교 |
| `hexa-cli-introspection` (Rank 3) | 본 spec 이 `--diff` 를 추가해 introspection 패밀리 완성 |
| `hexa-treesitter-grammar` (Rank 6) | 본 spec § 6 에서 tree-sitter 와 분담 명시 → grammar 확립 후 hash-anchor 강화 |
| `hexa-ast-diff-semantic-refactor` (NEW, 본 spec) | spec 자체 |

13항목 중 **5항목** 이 AST diff 와 직접 관련 (다른 8항목은 stdlib/runtime 작업).

---

## § 2. 사용 시나리오 (8개)

각 시나리오는 (1) 트리거 (2) 입력 (3) 출력 (4) 후속 액션 형식.

### 2.1 SC-1: 함수 이름 변경 영향 분석

- **트리거**: `_ns_now` 를 `ns_now_safe` 로 rename 하려는데 호출처 영향 미리 보고 싶다.
- **입력**: `hexa-introspect --diff-rename _ns_now ns_now_safe mk2_hexa/mk2/src/atlas/lookup.hexa`
- **출력** (NDJSON):
  ```json
  {"change_kind":"rename_def","name":"_ns_now","new_name":"ns_now_safe","loc":{"line":26,"col":1}}
  {"change_kind":"rename_call","name":"_ns_now","new_name":"ns_now_safe","loc":{"line":279,"col":17}}
  {"change_kind":"rename_call","name":"_ns_now","new_name":"ns_now_safe","loc":{"line":368,"col":17}}
  ```
- **후속**: `--diff-rename --apply` (5b) 로 자동 적용 또는 IDE workspace edit 으로 dump.

### 2.2 SC-2: 파라미터 추가 호환성 검사

- **트리거**: `lookup(id)` → `lookup(id, hint)` 시그니처 변경. 모든 호출처가 `hint` 인자를 추가했는지 검증.
- **입력**: `hexa-introspect --diff-sig lookup HEAD~3:mk2_hexa/mk2/src/atlas/lookup.hexa lookup.hexa`
- **출력**:
  ```json
  {"change_kind":"signature_changed","name":"lookup",
   "before":{"params":[{"name":"id","type":"string"}],"ret":"Hyp"},
   "after":{"params":[{"name":"id","type":"string"},{"name":"hint","type":"string"}],"ret":"Hyp"},
   "compat":"breaking_added_required_param"}
  {"change_kind":"call_site_outdated","name":"lookup","loc":{"file":"main.hexa","line":42,"col":18},"reason":"missing_arg:hint"}
  ```

### 2.3 SC-3: return type 변경 유닛 검사

- **트리거**: `_ns_now -> i64` 가 `_ns_now -> i64?` (optional) 로 변경됨. 모든 사용처가 unwrap 했는지 검증.
- **입력**: `hexa-introspect --diff-sig _ns_now a.hexa b.hexa`
- **출력**:
  ```json
  {"change_kind":"signature_changed","name":"_ns_now",
   "before":{"ret":"i64"},"after":{"ret":"i64?"},"compat":"breaking_return_widened"}
  {"change_kind":"unwrap_required","loc":{"line":279,"col":17},"hint":"_ns_now() -> _ns_now() ?? 0"}
  ```

### 2.4 SC-4: 모듈 분리/병합 trace

- **트리거**: `lookup.hexa::dispatch` 를 `mod.hexa::dispatch` 로 옮겼다. atlas-validator 가 모듈 export 표면 변경을 감지해야 함.
- **입력**: `hexa-introspect --diff old/atlas/ new/atlas/` (디렉토리 모드, Phase 5b)
- **출력**:
  ```json
  {"change_kind":"moved","name":"dispatch","from":"lookup.hexa:140","to":"mod.hexa:88","body_hash_match":true}
  {"change_kind":"import_outdated","loc":{"file":"main.hexa","line":3},"old":"use atlas::lookup::dispatch","new":"use atlas::mod::dispatch"}
  ```

### 2.5 SC-5: 본문 변경 vs 시그니처 변경 분리 (PR 리뷰)

- **트리거**: PR 에 11 파일 변경. 어느 것이 ABI break 인지 빠르게 식별.
- **입력**: `hexa-introspect --diff $(git diff --name-only main HEAD -- '*.hexa')` (multi-file 모드)
- **출력 요약**:
  ```json
  {"summary":{"total":11,"body_only":7,"signature_changed":2,"renamed":1,"added":1,"removed":0}}
  {"file":"lookup.hexa","change_kind":"signature_changed","name":"lookup",...}
  {"file":"recall.hexa","change_kind":"renamed","old_name":"_recall","new_name":"recall_v2",...}
  ```
  → 리뷰어가 **2 signature_changed + 1 renamed** 만 집중 리뷰. 7 body_only 는 본문 검사로 충분.

### 2.6 SC-6: atlas health drift 위치 차분

- **트리거**: `state/atlas_health_timeline.jsonl` 가 모듈 N 의 변경을 기록했다. 어떤 fn 이 변경되었는지 timeline 에 자동 첨부.
- **입력**: `hexa-introspect --diff $(git show $PREV:lookup.hexa) lookup.hexa --format=health`
- **출력**: atlas timeline 의 `change_kind`/`name` 두 필드가 자동 채워짐. drift event 가 "11 line 변경" 이 아닌 "fn `lookup` body changed (hash a1b2 → c3d4)" 로 기록.

### 2.7 SC-7: hexa-rules drift 검출 (`>=`/`<=` 사용)

- **트리거**: 두 commit 사이에 누군가 `r >= 1` 추가 (hexa-rules 위반).
- **입력**: `hexa-introspect --diff old.hexa new.hexa --check`
- **출력**: AST diff + Phase 2 (`--check`) 룰을 합성. 변경된 fn 본문 안에서만 룰 검사 → 노이즈 최소화.
  ```json
  {"change_kind":"body_changed","name":"recall","loc":{"line":88}}
  {"change_kind":"new_lint_in_diff","name":"recall","code":"HX001-banned-gte","loc":{"line":92,"col":11}}
  ```

### 2.8 SC-8: cross-version compat 매트릭스 (회귀 자동화)

- **트리거**: hexa-lang upstream 이 parser.hexa 를 수정. 모든 atlas 모듈이 여전히 같은 AST 를 산출하는지 검증.
- **입력**: `hexa-introspect --diff $(./bin/hexa@v1.2 --ast f.hexa) $(./bin/hexa@v1.3 --ast f.hexa) --semantic-only`
- **출력**: AST 노드 종류는 같되 `loc` 만 변한 경우 무시 (semantic-only 모드). 실제 의미 변경만 emit.

---

## § 3. AST Diff 알고리즘

### 3.1 후보 알고리즘 비교

| 알고리즘 | 정확도 | 비용 | 구현 난이도 | 권장 |
| --- | --- | --- | --- | --- |
| Tree-edit distance (Zhang-Shasha) | 매우 높음 | O(n²·d) | 매우 높음 (recursive DP) | X (over-engineering) |
| GumTree | 높음 (rename heuristic) | O(n·log n) | 중-상 | 5b 후보 |
| **Symbol-table hash diff (권장)** | 충분 (symbol 단위) | O(n) | 낮음 | **5a 채택** |
| Pure text-line diff (myers) | 낮음 | O(n²) | 낮음 (이미 있음) | X (semantic 0) |

### 3.2 권장: Symbol-table hash diff (5a)

**아이디어**: AST 전체를 비교하지 않는다. `--symbols` 출력 (Phase 1 산출물)
을 두 파일에 대해 받고, **symbol identity** 와 **content hash** 두 키로 매칭.

알고리즘 (의사코드):

```
Sa = symbols(a)          // [{name, kind, sig, body_hash, loc}]
Sb = symbols(b)
match(Sa, Sb):
    by_name = {s.name: s for s in Sb}
    for s in Sa:
        if s.name in by_name:
            t = by_name.pop(s.name)
            if s.sig == t.sig and s.body_hash == t.body_hash:
                emit({change_kind: "unchanged", name: s.name})
            elif s.sig == t.sig:
                emit({change_kind: "body_changed", name: s.name, hash_before: s.body_hash, hash_after: t.body_hash})
            else:
                emit({change_kind: "signature_changed", name: s.name, before: s.sig, after: t.sig})
        else:
            // 후보: rename. body_hash 가 일치하는 것이 Sb 에 있는가?
            cand = find_by_body_hash(by_name, s.body_hash)
            if cand:
                emit({change_kind: "renamed", old_name: s.name, new_name: cand.name})
                by_name.pop(cand.name)
            else:
                emit({change_kind: "removed", name: s.name})
    for t in by_name.values():
        emit({change_kind: "added", name: t.name})
```

**복잡도**: O(n). symbol 수 n.

**body_hash 정의**:
- AST 토큰 stream 의 정렬된 SHA-1 (loc 제외, whitespace/주석 제외).
- 또는 (Phase 4-Native 미도입 시) lexer 토큰 stream + sig fingerprint.
- → tree-sitter 가 들어오면 CST sub-tree 의 canonical-form hash 로 격상 가능 (§ 6).

### 3.3 Rename heuristic 개선 (5a 후속)

`body_hash` 단순 일치는 **본문이 정확히 같은** rename 만 잡는다. 본문이 약간 변한 rename 을 잡으려면:

- **Jaccard similarity** (token bag): 5a 단계에서 임계 0.85 권장. 비용 O(n²) 이지만 보통 atlas 모듈 n < 50 → 실측 < 5ms.
- GumTree (5b 후보): 본문 변경된 rename + 모듈 이동까지 동시에 잡음. 5a 검증 후 도입.

---

## § 4. CLI 인터페이스

### 4.1 5a 서브커맨드

```
# 두 파일 비교 (symbol-level diff)
hexa-introspect --diff <a.hexa> <b.hexa>
hexa-introspect --diff <a.hexa> <b.hexa> --semantic-only   # loc 변경 무시
hexa-introspect --diff <a.hexa> <b.hexa> --include-body    # body diff 까지 emit

# rename 영향 분석 (single-file, 호출처 포함)
hexa-introspect --diff-rename <old> <new> <file.hexa>
hexa-introspect --diff-rename <old> <new> <file.hexa> --workspace   # cross-file (Phase 5b)

# 시그니처 변경 비교
hexa-introspect --diff-sig <fn> <a.hexa> <b.hexa>
hexa-introspect --diff-sig <fn> <a.hexa> <b.hexa> --check-callers <main.hexa>
```

### 4.2 5b 서브커맨드 (자동 적용)

```
# WorkspaceEdit emit (LSP 호환)
hexa-introspect --diff-rename <old> <new> <file.hexa> --emit-edit

# In-place 적용 (dry-run 권장)
hexa-introspect --diff-rename <old> <new> <file.hexa> --apply --dry-run
hexa-introspect --diff-rename <old> <new> <file.hexa> --apply

# 디렉토리 모드 (모듈 분리/병합 trace)
hexa-introspect --diff <old-dir>/ <new-dir>/
```

### 4.3 출력 포맷 옵션

| flag | 의미 | 기본 |
| --- | --- | --- |
| `--format=ndjson` | 한 변경당 1 라인 JSON | ✓ default |
| `--format=json` | 단일 array | — |
| `--format=human` | 사람 읽기용 (rich-rendered) | — |
| `--format=health` | atlas health timeline 호환 | — |
| `--format=lsp` | LSP `WorkspaceEdit` (5b) | — |

### 4.4 exit code

- 0: diff 생성 성공 (변경 있음/없음 무관)
- 1: 파싱 실패 (둘 중 하나라도 unparsable)
- 2: 인자 오류
- 3: `--apply --dry-run` 에서 미적용 변경 검출 (CI gate)

---

## § 5. 출력 스키마

### 5.1 공통 필드

```ts
interface Change {
  change_kind: "added" | "removed" | "renamed" | "moved"
             | "signature_changed" | "body_changed" | "unchanged"
             | "rename_def" | "rename_call"          // --diff-rename 전용
             | "call_site_outdated" | "unwrap_required"  // --diff-sig 전용
             | "import_outdated"
  name: string                     // symbol 이름 (rename: 구이름)
  new_name?: string                // renamed/rename_call 시 신이름
  loc: { file: string, line: int, col: int }
  end_loc?: { file: string, line: int, col: int }
  before?: SigOrBody
  after?: SigOrBody
  body_hash_match?: bool           // moved 일 때
  compat?: "compatible" | "breaking_added_required_param"
         | "breaking_removed_param" | "breaking_return_widened"
         | "breaking_return_narrowed" | "ambiguous"
}
interface SigOrBody {
  params?: { name: string, type: string | null, default?: string }[]
  ret?: string | null
  body_hash?: string                // 16-hex SHA-1 prefix
}
```

### 5.2 5b WorkspaceEdit 출력 (LSP 호환)

```ts
interface WorkspaceEdit {
  // LSP textDocument/workspaceEdit 와 동일 형식
  documentChanges: TextDocumentEdit[]
}
interface TextDocumentEdit {
  textDocument: { uri: string, version?: int }
  edits: { range: { start: Pos, end: Pos }, newText: string }[]
}
```

→ 5b 출력은 LSP 클라이언트가 그대로 소비 가능. nvim/zed/Helix 모두 호환.

---

## § 6. tree-sitter 와의 관계

### 6.1 작업 분담

`tooling/tree-sitter-hexa/` 는 grammar 9/9 test 통과. 본 spec 은 tree-sitter
와 **직교** 하되 **선택적 보강** 으로 활용:

| 책무 | tree-sitter | hexa-introspect | 채택 |
| --- | --- | --- | --- |
| syntax highlight | ★ (highlights.scm) | — | tree-sitter |
| folding/outline | ★ | ★ (`--symbols`) | introspect (semantic 인식) |
| **AST diff (semantic)** | △ (가능하지만 grammar 노드만, scope/type 인식 X) | ★ | **introspect (SSOT)** |
| **CST diff (concrete)** | ★ (loc 정확, parser-version-stable) | △ (4610줄 parser.hexa 의존) | tree-sitter (보조) |
| body_hash 계산 | ★★ (sub-tree canonical-form 자연스러움) | △ (lexer 토큰 stream) | **tree-sitter 우선, introspect 폴백** |
| Phase 4-Native 미완 시 loc 보강 | ★ (이미 정확) | X (parser.hexa 좌표 0) | tree-sitter |

### 6.2 권장 통합 (선택적, 5a 후 5b 단계)

- **5a 본체**: introspect 단독 (`--symbols` 출력 + lexer 토큰).
- **5b 강화**: tree-sitter CLI (`tree-sitter parse --quiet`) 가 가용하면 sub-tree
  canonical hash 를 우선 사용. 미가용 시 lexer fallback.
- **결과**: introspect 가 여전히 SSOT 이지만 정확도가 향상. tree-sitter 의존
  은 optional (CI 에 tree-sitter 미설치 환경에서도 동작).

### 6.3 비-목표 (out of scope)

- tree-sitter incremental 파싱 활용 (introspect 는 1-shot 모델).
- tree-sitter query 로 직접 diff (queries/diff.scm) — semantic 인식 X 이므로 부적합.

---

## § 7. LSP 와의 관계

### 7.1 출력 형식 호환

본 spec § 5.2 의 `WorkspaceEdit` 는 LSP `textDocument/rename` 응답과 동일.
즉:

```
hexa-introspect --diff-rename old new f.hexa --emit-edit --format=lsp
  → LSP textDocument/rename response payload (그대로 client 적용 가능)
```

→ Phase 4-LSP shim (다른 에이전트 진행 중) 이 완료되면, `hexa lsp` 의 `rename`
핸들러가 introspect 를 sub-process 로 호출 → 결과를 그대로 반환할 수 있다.
**lsp.hexa 본문 추가 코드 ≈ 20줄.**

### 7.2 책무 분담

| 메서드 | LSP 단독 | introspect 단독 | 통합 |
| --- | --- | --- | --- |
| `textDocument/rename` | full impl 가능 | `--diff-rename` | **introspect 가 backend, lsp shim** |
| `textDocument/codeAction` (refactor) | full | (Phase 5c) | 백로그 |
| `textDocument/prepareRename` | symbol 위치 검증 | `--refs` (Phase 3) | 통합 |
| AST diff (CI/PR 리뷰) | 비-목적 | **introspect (CLI)** | introspect SSOT |
| atlas health drift | 비-목적 | **introspect (--format=health)** | introspect SSOT |

### 7.3 결정

- LSP 는 **transport** 로만 활용 (rename/refactor 메시지 wrap).
- introspect 는 **engine** SSOT (모든 diff/refactor 로직 보유).
- Phase 5b 의 `--emit-edit --format=lsp` 가 이 둘을 연결.

---

## § 8. Semantic Refactor 대상 (5b 범위)

### 8.1 1차 (5b 본체)

| Refactor | 입력 | 출력 (WorkspaceEdit) | 위험 |
| --- | --- | --- | --- |
| **Rename symbol** (fn/let/const) | `--diff-rename old new file` | def + 모든 use-site | low (Phase 3 `--refs` 결과 직접 활용) |
| **Add parameter** | `--diff-sig fn before after --apply-default <val>` | 모든 호출처에 `<val>` 삽입 | medium (semantic 확인 필요) |
| **Remove unused parameter** | `--diff-sig fn before after` | 호출처에서 해당 인자 제거 | medium (side-effect 있는 인자 식별 필요) |

### 8.2 2차 (5c 후속, 본 spec out)

| Refactor | 비고 |
| --- | --- |
| Extract function | 본문 일부를 새 fn 으로. AST 부분 추출 + 자유변수 분석. |
| Inline function | 호출처에 본문 inlining. |
| Move to module | 모듈 간 fn 이동 + import 갱신. |
| Type widening (i32 → i64) | 사용처 type-check pass 검증. |

### 8.3 안전 보장

- **dry-run default**: `--apply` 없이는 스캔만. CI 에서 사용 시 `--apply --dry-run`.
- **AST round-trip 검증**: 변경 적용 후 `hexa --ast` 가 여전히 파싱 성공함을 검증. 실패 시 rollback.
- **--check 통합**: 변경된 fn 만 `hexa --check` 통과 확인. HX001–HX008 룰 회귀 차단.
- **scope-aware**: rename 이 shadowing 으로 의미 변경시키는 경우 `compat: "ambiguous"` + 거부.

---

## § 9. 비용 추정

### 9.1 단계별

| Phase | 범위 | 공수 | 산출물 |
| --- | --- | --- | --- |
| **5a** | `--diff` (single-file), `--diff-sig`, `--diff-rename` (local), symbol-hash 알고리즘 | **1–2일** | 3 서브커맨드 + 5종 change_kind + ndjson schema |
| **5b** | `--apply`, `--emit-edit --format=lsp`, `--diff-rename --workspace`, 디렉토리 모드 | **3–5일** | WorkspaceEdit 출력 + dry-run 가드 + lsp shim 통합 |
| **5c (백로그)** | extract/inline/move, GumTree 알고리즘 | 5–10일 | 본 spec out |

### 9.2 종속성

- Phase 1 (`--symbols`): **종속 ✓** (이미 완료).
- Phase 2 (`--check`): **선택** (5a 의 `--check` 옵션 통합용).
- Phase 3 (`--refs`/`--hover`): **종속** (5b rename 호출처 갱신).
- Phase 4-LSP shim: **선택** (5b `--format=lsp` 활용).
- Phase 4-Native (parser.hexa loc): **선택** (5a 는 lexer 폴백으로 OK; 5b 는 정확도 향상).
- tree-sitter: **선택** (body_hash 정확도 향상).

→ **5a 는 즉시 가능** (Phase 1 + Phase 2 만 있으면 시작).
→ **5b 는 Phase 3 머지 후** 가용.

### 9.3 측정 기준 (수용 조건)

- 5a `--diff` 가 atlas 5 모듈 (lookup, hypothesis, recall, distribution, mod) 의 직전 30 commit 페어를 처리. cold run < 500ms/페어.
- 5a `--diff-rename _ns_now ns_now_safe lookup.hexa` 가 def 1 + call 2 (line 26/279/368) 모두 검출.
- 5a 가 git diff 라인 수 100 → AST change 수 K, K ≤ 10 인 사이클이 ≥ 80% (semantic 압축 비율).
- 5b `--apply --dry-run` 후 `hexa --check` 가 0 새로운 에러 보고.

---

## § 10. 후속 (Phase 5 이후)

### 10.1 Semantic merge (3-way)

- 두 branch 의 동일 fn 을 의미 단위로 merge. body_changed × body_changed 충돌 시
  symbol-level 충돌 마커 (text-level 보다 좁은 범위).
- 비용 추정: 5–7일. GumTree + 3-way edit script.

### 10.2 AST patch DSL

- `--apply-script` flag: `{change_kind: "rename", old: "_ns_now", new: "ns_now_safe", scope: "workspace"}` 같은 명세파일을 입력 받아 일괄 적용.
- 외부에서 작성 가능한 refactor 스크립트 → 사이클 자동화.

### 10.3 atlas health timeline 자동 첨부

- atlas validator 가 모듈 변경 감지 시 `--diff --format=health` 호출 → timeline 에 `change_kind`/`name` 자동 부착.
- `state/atlas_health_timeline.jsonl` 의 drift event 가 라인 단위에서 symbol 단위로 격상.

### 10.4 PR 리뷰 봇

- `hexa-introspect --diff $(git diff --name-only main HEAD)` 를 PR 코멘트로.
- summary { body_only: 7, signature_changed: 2 } 가 리뷰어 attention 분배 SSOT.

### 10.5 cross-version compat 매트릭스

- hexa-lang 자체 업그레이드 시 nexus 모든 atlas 모듈의 AST 가 의미 보존하는지 회귀 검사 (SC-8).

---

## § 11. 리스크

| 리스크 | 완화 |
| --- | --- |
| Phase 4-Native 미도입 시 loc 부정확 | 5a 는 lexer 토큰 폴백 사용. 5b 의 정확도가 80% 수준 — `--apply` 사용 전 dry-run 권장. |
| body_hash 의존 false-negative (whitespace 정규화 미흡) | 토큰 stream 기반 hash + 주석/공백 strip. tree-sitter 도입 시 sub-tree canonical form. |
| rename heuristic false-positive (다른 fn 의 body 가 우연히 같음) | Jaccard threshold 0.85 + sig 일치 추가 조건. |
| 호출처 grep 의 lexical false-positive | Phase 3 `--refs` 의 AST resolver 결과 사용. resolver 미가용 시 lexical fallback 마커 부착. |
| 자동 적용 시 coverage 파일 손상 | `--apply --dry-run` 기본. 적용 후 `hexa --check` 회귀 검증. |
| LSP shim 미완 → `--emit-edit --format=lsp` 활용 불가 | Phase 4-LSP 머지 대기. 그동안 `--format=ndjson` 로 외부 도구 직접 소비. |

---

## § 12. 결론

**hexa-introspect Phase 5 = AST diff (5a, 1–2일) + semantic refactor (5b, 3–5일)**.
텍스트 diff 로 가시성이 떨어지던 5종 변경 패턴 (rename, sig change, return type
change, module move, body change) 을 symbol 단위로 정형화. tree-sitter 는 보강 (CST/hash
정확도), LSP 는 transport (5b WorkspaceEdit) 으로 분담. introspect 가 engine SSOT.

5a 는 Phase 1 ✓ 만 있으면 즉시 시작 가능. 5b 는 Phase 3 머지 대기. 본 spec
은 코드 미수정, 후속 사이클에서 구현 착수.

---

## 5a 구현 결과 (2026-05-06)

### 산출물

- `tooling/hexa-introspect/diff.hexa` (952줄 — JSON 파서 + body 정규화 +
  shasum/FNV-1a hash 폴백 + symbol-hash 매칭 + Jaccard rename heuristic)
- `tooling/hexa-introspect/PHASE5A_DISPATCH_PATCH.md` (174줄 — Phase 3 머지
  후 hexa_introspect.hexa dispatch 분기 + bin shim mode whitelist 추가)
- `tooling/hexa-introspect/_fixtures/sample_rename.hexa` (rename 검증 fixture)

### body_hash 정규화 룰 (확정)

1. **fn 의 경우**: `_strip_fn_signature(s, kind)` 가 첫 `{` 위치까지 skip
   — name/sig 부분 제외 후 본문만 hash. rename heuristic 활성화 핵심.
2. **주석 제거**: `// ...` 라인 코멘트, `/* ... */` 블록 코멘트 제거.
3. **whitespace collapse**: 연속 space/tab/cr/lf → 단일 space.
4. **string literal 보존**: `"..."` 안의 escape 도 보존 (변경 감지).
5. **hash 함수**: `shasum -a 1` 우선 (16-hex SHA-1 prefix), 부재 시 FNV-1a
   32-bit (8-hex) 폴백. 둘 다 spec § 5.1 SigOrBody.body_hash 와 호환.

### change_kind 분류 (실측 확인)

| change | 트리거 |
| --- | --- |
| `unchanged` | name + kind + sig + body_hash 모두 일치 |
| `body_changed` | name + kind + sig 일치, body_hash 만 다름 |
| `signature_changed` | name + kind 일치, sig 다름 (body 일치 또는 둘 다 다름) |
| `renamed` | name 다르지만 동일 kind 의 후보가 (1) body_hash 일치 또는 (2) Jaccard ≥ 85% |
| `removed` | a 에만 있고 b 의 어떤 후보와도 매칭 안 됨 |
| `added` | b 에만 있는 잔여 항목 |

### 검증 결과

| pair | unchanged | renamed | added | removed | body_changed | signature_changed | total | meta ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sample vs self | 7 | 0 | 0 | 0 | 0 | 0 | 7 | ~5s |
| sample vs sample_rename (`greet`→`hail` + `_clock_ns` 추가) | 6 | **1** (body_hash_match) | 1 | 0 | 0 | 0 | 8 | ~5s |
| atlas/lookup vs atlas/recall | 5 | 0 | 12 | 13 | 4 | 0 | 34 | 12s |
| atlas/hypothesis vs atlas/distribution | 1 | 0 | 25 | 8 | 2 | 1 | 37 | 7s |
| atlas/lookup vs atlas/mod | 1 | 0 | 11 | 19 | 2 | 0 | 33 | 7s |
| atlas/lookup vs SELF (control) | 22 | 0 | 0 | 0 | 0 | 0 | 22 | 25s |
| atlas/recall vs n6/atlas_query | 1 | 0 | 17 | 20 | 0 | 0 | 38 | 10s |

→ rename heuristic 작동 확인 (`greet`→`hail` body_hash_match).
→ control (self-diff) 에서 false-positive rename 0.
→ atlas/recall vs n6/atlas_query 의 1 unchanged 는 양쪽에 복붙된 SSOT
  헬퍼 (`_ns_now` 등) 의 drift 미발생을 검증 — § 1.3 효용 실측 확인.

### 측정 (수용 조건 § 9.3 비교)

- ✓ atlas pair cold run < 13s (서브프로세스 2회 + 서브프로세스 RSS 2GB 캡).
  spec 의 < 500ms 목표는 hexa-runtime 의 fork+JIT init (~50ms × 2 + 본
  scan_decls O(n²) — Rank 4 후속 prefix-rescan 최적화 대기) 한계에 걸려
  미달. **Phase 5b 에서 in-process 병합 필요** (prefix-rescan 정리와 동시).
- ✓ rename fixture 의 def 1 (greet→hail) 검출 — 본 5a 단계는 single-file
  스코프이므로 호출처 (cross-file) 는 5b `--diff-rename --workspace` 영역.
- ✓ 모든 비교 exit 0, NDJSON `change` 키 5종 분류 정확.

### 후속 (Phase 5b 우선순위)

1. `--diff-rename <old> <new> <file>` — Phase 3 `--refs` 결과 활용해 호출처
   포함.
2. `--diff-sig <fn> <a> <b>` — params 비교 + compat 분류
   (`breaking_added_required_param` 등).
3. `--apply --dry-run` / `--emit-edit --format=lsp` — WorkspaceEdit emit.
4. **성능 개선**: scan_decls 의 O(n²) 사이클 제거 (`hexa-cli-introspection`
   Rank 4 후속과 동시) → atlas pair cold < 500ms 목표 달성.
5. 디렉토리 모드 `--diff <a-dir>/ <b-dir>/` — 모듈 분리/병합 trace.

---

## 5b 구현 결과 (2026-05-06)

### 산출물

- `tooling/hexa-introspect/refactor.hexa` (996줄 — 5a `diff.hexa` 와 분리된
  신규 entry-point. 4 mode dispatch + 5a/Phase3 subprocess wrapping +
  sig 파싱 + LSP `WorkspaceEdit` encoder).
- 신규 fixture 4종:
  `_fixtures/sample_calls.hexa` (rename 호출처 검증),
  `_fixtures/sample_sig_a.hexa` / `sample_sig_b.hexa` (breaking_*),
  `_fixtures/sample_sig_c.hexa` / `sample_sig_d.hexa` (compatible_*).

### 신규 vs 확장 결정

5a 의 `diff.hexa` (952줄) 는 read-only 로 보존. 5b 는 별도 파일
`refactor.hexa` 로 작성하여 (1) 5a 와의 충돌 0, (2) Phase 3 patch 영역인
`hexa_introspect.hexa` 와 bin shim 도 read-only, (3) `refactor.hexa` 는
필요 시 `diff.hexa` / `hexa_introspect.hexa` 를 subprocess 로 호출
(NDJSON 회수 → 후처리). entry shape 통일: `--diff*` 시리즈는 `diff.hexa`,
semantic refactor 시리즈는 `refactor.hexa`.

### 4 모드 검증

| 모드 | fixture | 입력 | 핵심 출력 | 결과 |
| --- | --- | --- | --- | --- |
| ① `--diff-rename` | sample_calls.hexa | `greet → hail` | `ref_count=4` (1 decl + 3 calls @ 8/9/12) | ✓ |
| ① `--diff-rename` | diff.hexa (952줄) | `_ns_now → _clock_ns` | `ref_count=4` (decl@69 + calls@482/740/949) | ✓ |
| ① `--diff-rename` | atlas/mod.hexa | `dispatch → dispatch2` | `ref_count=2` (decl@157 + 재귀 call@204) | ✓ |
| ② `--diff-sig` | sig_a vs sig_b | `foo` (i32 → +b: i64) | `breaking_added_required_param` | ✓ |
| ② `--diff-sig` | sig_a vs sig_b | `bar` (x,y → x) | `breaking_removed_param` | ✓ |
| ② `--diff-sig` | sig_a vs sig_b | `baz` (string → i64 ret) | `breaking_return_type_change` | ✓ |
| ② `--diff-sig` | sig_c vs sig_d | `qux` (input → text) | `compatible_param_renamed` | ✓ |
| ② `--diff-sig` | sig_c vs sig_d | `quux` (+b: i64 = 42) | `compatible_added_optional_param` | ✓ |
| ③ `--apply --dry-run` | sample vs sample_rename | rename + 1 added | 2 plan lines, dry_run=true | ✓ |
| ③ `--apply --dry-run` | atlas mod vs validate | 19 changes | 19 plan lines (body/sig/added/removed) | ✓ |
| ④ `--emit-edit --format=lsp` | sample vs sample_rename | 2 changes | 1 documentChange × 2 edits, jq-parseable | ✓ |
| ④ `--emit-edit --format=lsp` | atlas mod vs validate | 19 changes | 1 documentChange × 19 edits, jq-parseable | ✓ |

→ 모든 4 모드 **단발 성공**. exit 0, NDJSON/JSON 정형. 호출처 (Phase 3 `--refs`)
+ symbol diff (Phase 5a) + sig 파싱 + LSP encode 가 sub-process 체인으로 결합.

### compat 분류 정확도

`_classify_sig` 가 5종 + 2 보조 (`unchanged`, `ambiguous`, `breaking_param_type_change`)
를 결정론적으로 판정. params 수 + ret type + (수 동일 시) name/type pair 비교
의 단순 룰. 파싱 실패 (sig 미회수, paren 불균형) 시 `ambiguous` 반환 — false-
positive 회피.

### LSP format 호환

- `documentChanges` 단일 array → `TextDocumentEdit` 1 entry → `edits[]`.
- range 는 0-based (LSP 표준), col=0 보수적 설정 (전체 행 단위 표시).
- `newText` 는 `/* hexa-refactor … */` 주석 형태 (실제 신규 코드는 5b 후속
  full-text-extract 단계에서 b 의 fn 본문을 그대로 복사 — 본 5b 는 LSP
  메시지 포맷 검증 우선).
- `jq '.documentChanges[0].edits | length'` / `.textDocument.uri` 모두 정상
  파싱 — Phase 4-LSP shim 의 rename handler 가 본 출력을 그대로 client 에
  전달 가능.

### 측정

| 페어 | 모드 | cold run | 비고 |
| --- | --- | --- | --- |
| sample_calls (15줄) | ① rename | ~5s | --refs subprocess × 1 |
| sig_a vs sig_b (10줄) | ② sig | ~5s | --symbols × 2 |
| sig_c vs sig_d (8줄) | ② sig | ~6–9s | --symbols × 2 |
| sample vs sample_rename | ③ apply dry-run | ~45s | 5a diff subprocess × 1 (=symbols × 2 + body hash) |
| sample vs sample_rename | ④ lsp | ~10s | 5a diff 재호출 (cache 미사용) |
| atlas mod vs validate | ③ apply dry-run | ~60s | 19 plan lines |
| atlas mod vs validate | ④ lsp | ~10s | 19 edits × 1 doc |
| diff.hexa (952줄) | ① rename | ~109s | scan_decls O(n²) 한계 |

→ atlas pair cold < 500ms 목표는 5a 와 동일하게 **미달**. scan_decls 최적화
(`hexa-cli-introspection` Rank 4 후속) + in-process 병합 (subprocess fork
50ms × N 제거) 가 동시 필요.

### 후속 (Phase 5c — 본 spec out)

1. **GumTree 알고리즘** (§ 3.3): rename + 본문 부분변경 + 모듈이동 동시 검출.
   현 5b 의 body_hash + Jaccard 보다 정확. 비용 O(n·log n).
2. **Extract / Inline / Move** refactor (§ 8.2): AST 부분 추출 + 자유변수 분석.
3. **--apply (실제 적용)**: backup file (`.bak.<ns>`) 작성 + in-place edit +
   AST round-trip 검증 (§ 8.3) + `--check` 회귀 차단.
4. **--diff-rename --workspace**: cwd glob (`*.hexa`) 순회 cross-file scope.
   현 5b 는 single-file. 5b 후속 단계.
5. **5b LSP newText 실 코드**: 현 placeholder 주석 → b 파일의 실 fn 본문
   substring 으로 교체. fn 영역의 byte-range 추출 + 정확한 col 계산 필요.
6. **성능**: in-process 병합 (subprocess 사슬 제거) → atlas pair < 500ms.

---

## 5c 구현 결과 (2026-05-06)

### 산출물

- `tooling/hexa-introspect/gumtree.hexa` (1515줄 — GumTree 3-pass tree-edit +
  4 advanced refactor 모드. 5a/5b 와 분리된 신규 entry-point, 공통 헬퍼는
  의도적으로 self-contained (NS clock / JSON parser / shasum + FNV-1a 폴백 hash))
- `tooling/hexa-introspect/PHASE5C_DISPATCH_PATCH.md` — Phase 3 머지 후 main
  wrapper / bin shim 통합용 patch md.
- 신규 fixture 4개: `_fixtures/{sample_extract.hexa, sample_inline.hexa,
  sample_move_a.hexa, sample_move_b.hexa}`.

### 4 모드 구현 vs 설계

| 모드 | 상태 | 핵심 알고리즘 / 한계 |
| --- | --- | --- |
| `--diff-tree <a> <b>` | **구현 완료** | 3-pass GumTree: ① top-down (type+hash 합성 `kd:nm:sig:body_norm`) ② bottom-up dice ≥ 50% ③ matched 부모의 unmatched children 을 type-만으로 update 매칭 (leaf 차분 압축). emit NDJSON action ∈ {match,update,move,delete,insert}. |
| `--extract <file> <sl> <el> <new>` | **부분 구현** | 자유변수 = identifier-set 차분 (region toks − region-내 declared − reserved). 타입 i64 디폴트 (HM 추론 미구현), capture/escape 추적 미구현, return type 추정 미구현 → caveat 필드 명시. enclosing fn 식별 OK. |
| `--inline <file> <fn>` | **부분 구현** | 호출처 lexical scan (`fn_name(`), param-name lexical substitute (alpha-rename X), 마지막 `return X` 의 X 추출해서 expression-level 인라인. caveat: `lexical_subst;no_alpha_rename;single_return_unwrapped`. |
| `--move <fn> <a> <b>` | **구현 (caller import 갱신은 설계 only)** | a 에서 fn 추출 → b 에 EOF append (b 부재 시 create_file:true emit). 호출처 grep (sibling `*.hexa`) → callers 리스트만 emit. 실제 use/import 라인 추가는 5b workspace edit 으로 위임 (caveat: `caller_import_designed_only`). |

### Tree 표현

- **노드** = 평행 배열 (id/parent/type/label/hash/height/sl/el) JSON 직렬화.
- **type** = `file`(root) | `fn` | `let` | `const` | `type`(struct/enum) | 본문
  내 stmt-line 분류 `return`|`if`|`while`|`for`|`match`|`try`|`catch`|`break`|
  `continue`|`call`|`comment`|`block_open`|`block_close`|`expr`.
- **hash** = `_hash_str(kd:nm:sig:body_norm)` for decls, `_hash_str(stmt_type
  :normalized_line)` for body lines. shasum SHA-1 16-hex prefix 우선, FNV-1a
  32-bit (8-hex) 폴백 — 5a 와 동일 룰.
- **height** = `1` for leaf decls + 모든 stmt-line, `2` for fn (≥ 1 child).
  GumTree 의 `minHeight` 임계값 도입 안 함 — hash 의 4-키 합성으로 leaf 도 안전
  매칭 (ambiguity 회피).

### 검증 결과

| pair | nodes_a | nodes_b | match | update | move | delete | insert | meta ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sample vs self | 12 | 12 | **12** | 0 | 0 | 0 | 0 | ~13s |
| sample vs sample_rename (greet→hail + _clock_ns 추가) | 12 | 15 | 11 | **1** (greet→hail update) | 0 | 0 | **3** (_clock_ns + 2 children) | ~5s |
| sample_sig_a vs sample_sig_b (bar/baz body 변경) | 10 | 10 | 8 | **2** (bar.return, baz.return) | 0 | 0 | 0 | ~5s |
| atlas/lookup vs SELF (control) | 327 | 327 | **327** | 0 | 0 | 0 | 0 | ~57s |
| atlas/lookup vs atlas/recall | 327 | 406 | 30 | 56 | 84 | 157 | 236 | ~91s |

→ self-control 327/327 false-positive 0.
→ rename fixture 의 greet→hail 이 **단일 update 액션** (5a 의 `renamed` 보다
  fine-grained — fn 자체 + 본문 변경 분리).
→ sig fixture 의 body-only 변경이 update 2건 (PASS 3 의 type-only matching
  으로 leaf hash 차분 압축).

### 4 모드 검증 (extract/inline/move)

| 모드 | 입력 | 핵심 출력 |
| --- | --- | --- |
| `--extract sample_extract.hexa 8 10 compute_total` | 함수 `compute(a,b)` 의 line 8..10 추출 | free_vars=[a,b] (sum/prod = region 내 declared 제외) + `extract_def` + `extract_call` plan |
| `--inline sample_inline.hexa double` | `double(x) -> x*2` 인라인 | 호출처 2개 detect (line 11/15), expression-level inline (`return double(10)` → `return 10 * 2`, `let y = double(n)` → `let y = n * 2`) + `inline_remove_def` |
| `--move _safe_token sample_move_a.hexa sample_move_b.hexa` | `_safe_token` 이동 | `move_remove` + `move_insert` + `move_caller_import` (caller=1, intra-file lookup), b 부재 시 `create_file:true` |
| `--move _safe_token mk2/atlas/lookup.hexa mk2/atlas/utility.hexa` | atlas 실 모듈 | lines 44–68 추출 (24 lines), utility.hexa 신규 생성 plan, callers=1 (lookup 자체) |

### 한계 / 후속 (Phase 5d)

- **시간 복잡도**: 본 구현은 `_descendants` (DFS via stack rebuild) +
  `_dice_pct` (O(|desc_a|·|desc_b|)) 으로 atlas pair (~330 노드) 에서 90s.
  Phase 5d 의 _descendants 캐싱 + hexa-runtime O(N²) loc 누적 정리로 < 5s
  로 단축 가능.
- **변수 capture / scope 추적 (extract)**: 진짜 자유변수는 enclosing fn param
  ∪ outer let. 본 구현은 token-set 차분 (어휘 레벨). Phase 5d scope tree.
- **alpha-rename / let-binding (inline)**: side-effect 인자, name shadow 회피
  를 위해 `let _arg_<n> = <expr>` introduce 후 본문 substitute 가 정석. 현
  lexical replace 는 best-effort. Phase 5d.
- **Move 의 caller import 자동 갱신**: hexa 의 `use ./atlas/lookup` 모듈 시스템
  과 호환되는 import-line 패치는 5b `--apply --emit-edit --format=lsp` 의
  workspace edit 으로 위임. 본 5c 는 reference list 만 emit.
- **multi-line stmt** (예: 여러 라인의 `if {...}`): 현재 line-단위 분류기는
  `if {` 와 `}` 를 별개 노드로 → tree depth 평탄. nested block 격상은 hexa AST
  의 substmt loc 노출 후 (Phase 4-Native 후속).
- **type widening** (spec § 8.2 의 4번째 advanced refactor): 본 5c 미구현.
  `--diff-sig` (5b) 결과의 type-pair 변경 → use-site type-check pass 검증을
  하려면 hexa --check 의 type checker 출력이 필요. Phase 5d.

### 측정 (수용 조건 § 9.1 비교)

- ✓ 4 advanced refactor 모드 + GumTree 알고리즘 모두 구현 (spec § 9.1 의
  5–10일 목표 대비 1 사이클 완료, 단순 fixture 한정).
- △ atlas pair < 5s 미달 (현 90s, 5a 와 동일한 hexa-runtime O(N²) scan_decls
  병목 + 본 모듈의 _descendants O(N) per call 누적). 5d 에서 prefix-rescan +
  dice 캐싱으로 단축 예상.
- ✓ self-control 327/327 false-positive 0.
- ✓ 모든 fixture (rename / sig / extract / inline / move) 의도된 출력 emit.

---

## 변경 이력

| 일자 | 변경 |
| --- | --- |
| 2026-05-06 | 초안 — 5a/5b 분리, symbol-hash 알고리즘 채택, tree-sitter/LSP 분담 결정. |
| 2026-05-06 | **Phase 5a 구현 완료** — `diff.hexa` 952줄, body_hash 정규화 룰 확정, 7개 pair 검증 (rename heuristic ✓, self-control ✓). dispatch patch md 분리 (Phase 3 머지 후 적용). |
| 2026-05-06 | **Phase 5b 구현 완료** — `refactor.hexa` 996줄 (신규 entry-point, 5a 와 분리), 4 모드 (`--diff-rename`/`--diff-sig`/`--apply --dry-run`/`--emit-edit --format=lsp`), 12개 검증 페어 통과 (compat 5종 분류 ✓, LSP `WorkspaceEdit` jq-parseable ✓, atlas 페어 19 변경 dry-run ✓). 5c (GumTree, extract/inline/move, 실제 --apply) 백로그. |
| 2026-05-06 | **Phase 5c 구현 완료** — `gumtree.hexa` (1515줄, GumTree 3-pass tree-edit + 4 advanced refactor 모드 `--diff-tree`/`--extract`/`--inline`/`--move`). atlas/lookup 자기-비교 327/327 ✓, rename/sig fixture 의 update 액션 정밀 분리 ✓. 4 fixture 신규. spec § 8.2 의 4 advanced 중 3 (extract/inline/move) 부분 구현, 1 (type widening) 미시작. dispatch patch md 분리. 후속 Phase 5d (descendants 캐싱, scope tree, alpha-rename, caller-import). |
