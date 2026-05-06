# tree-sitter-hexa — AI 에이전트 사용 가이드

`tooling/tree-sitter-hexa/` 의 grammar 와 query 셋을 AI 에이전트 (Claude/Cursor/Aider/codex/cline 등) 가 활용해 hexa 코드를 **grep 보다 정확히** 인식하는 방법.

## 사전 요구

```bash
# tree-sitter CLI (이미 시스템에 있음: /opt/homebrew/bin/tree-sitter, v0.26.8)
which tree-sitter

# parser.c 빌드 (한 번만)
cd tooling/tree-sitter-hexa
tree-sitter generate
tree-sitter test    # 9/9 corpus PASS 확인
```

## 1. 함수 outline 추출

```bash
tree-sitter parse mk2_hexa/mk2/src/atlas/lookup.hexa | \
  grep -E "function_declaration"
```

→ 라인+컬럼 정확. grep 으로는 `fn ` 매칭 시 주석/문자열도 잡힘.

## 2. 룰 위반 자동 검출 (`>=` / `<=` 금지)

```bash
tree-sitter query queries/lints.scm mk2_hexa/mk2/src/atlas/lookup.hexa
```

→ `@error.relop-banned` capture 로 위반 위치 출력. CI 또는 pre-commit 에 wiring 가능.

## 3. 베어 exec 검출

```bash
tree-sitter query queries/lints.scm n6/atlas_query.hexa | \
  grep -E "bare-exec"
```

→ `// @allow-bare-exec` 어노테이션 누락된 `exec(...)` 호출 자동 식별.

## 4. 코드 작성 전 구조 파악 (AI 에이전트 워크플로우)

```bash
# 1. 파일 전체 outline
tree-sitter parse <file>.hexa | head -50

# 2. 함수 시그니처만
tree-sitter parse <file>.hexa | grep -A 1 "function_declaration"

# 3. let 선언 (모듈 상단 상수)
tree-sitter parse <file>.hexa | grep "let_declaration"
```

→ Read 로 전체 파일 안 읽고도 구조 파악. 토큰 절약.

## 5. find-references 시뮬레이션

```bash
# `_ns_now` 함수 호출처
tree-sitter query queries/locals.scm <file>.hexa | grep "_ns_now"
```

→ scope/locals 분석 기반. 동일 이름 다른 스코프 구분.

## 6. 수정 영향 범위 파악

```bash
# 어떤 함수가 `exec(...)` 를 호출하는가
tree-sitter query - <file>.hexa <<'EOF'
(function_declaration
  name: (identifier) @fn_name
  body: (block
    (call_expression
      function: (identifier) @callee (#eq? @callee "exec"))))
EOF
```

→ ad-hoc 구조 쿼리. Lint, refactor, audit 모두 같은 메커니즘.

## 7. 멀티파일 일괄 검사

```bash
for f in mk2_hexa/mk2/src/atlas/*.hexa; do
  echo "=== $f ==="
  tree-sitter query queries/lints.scm "$f" 2>&1 | grep -E "error|warning" || echo "clean"
done
```

→ 5 모듈 전체 룰 위반 한 번에.

## 8. JSON 출력 → jq 파이프

```bash
tree-sitter parse --output=json <file>.hexa | \
  jq '.. | select(.type? == "function_declaration") | .name'
```

→ AI 에이전트가 구조화된 데이터로 받음. 텍스트 매칭 휴리스틱 불필요.

## LSP 와 비교

| 측면 | tree-sitter | LSP |
|---|---|---|
| 데몬 | 불필요 (단발 CLI) | 필요 |
| 빌드 | 1회 generate | 서버 작성 |
| 정확도 | 구문 100%, 타입 0% | 구문 + 타입 + 추론 |
| AI 통합 | Bash 호출만 | LSP 클라이언트 필요 |
| 비용 | 시드 3–5일 | 풀 1–3주 |

→ 혼자 쓰는 환경에서는 tree-sitter 가 **80% 가치를 1/10 비용으로** 제공.

## 갭 카탈로그 ref

`design/hexa_lang_gaps_from_atlas.md` Rank 6 (`hexa-treesitter-grammar`) 항목 참조.
