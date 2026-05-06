# docs/hexa-lang/ — hexa-lang DSL 룰 SSOT

nexus 내부 DSL `hexa-lang` 작업 시 적용해야 할 룰/관용구/함정의 단일 진실 원천(SSOT).
어떤 AI 에이전트(또는 사람)든 이 디렉토리를 읽으면 동일한 규칙으로 작업할 수 있다.

## 인덱스

- [`RULES.md`](RULES.md) — 핵심 룰 카드 (비교 연산자, stdlib-only, 헤더 컨벤션, 작업 시작 전 체크리스트)
- [`PATTERNS.md`](PATTERNS.md) — 검증된 11개 관용구 (ns clock, mtime, shell escape, NDJSON emit, awk 호출 등)
- [`GOTCHAS.md`](GOTCHAS.md) — 11개 함정과 회피책 (BSD awk UTF-8 collapse, `date +%s%N` literal-N 등)

## AI 에이전트별 로드 방법

- **Claude Code**: `.claude/skills/hexa-rules/SKILL.md` stub 이 자동활성화 → 위 3 파일을 Read.
- **Cursor**: `.cursorrules` 또는 채팅에서 `@docs/hexa-lang/RULES.md` 등으로 attach.
- **Aider**: `aider docs/hexa-lang/RULES.md docs/hexa-lang/PATTERNS.md docs/hexa-lang/GOTCHAS.md` 로 시작.
- **codex / cline / 기타**: 시스템 프롬프트에 "before editing any `.hexa` file, read `docs/hexa-lang/RULES.md`" 추가.
- **사람**: `.hexa` 파일 작업 전 `RULES.md` 의 작업 시작 전 체크리스트(§작업 시작 전 체크리스트) 확인.

## 트리거 조건 (어떤 도구든 동일)

- `.hexa` 파일 작성/수정 (read-only inspect 제외)
- 메시지에 `hexa`, `hexa-lang`, `hexa run` 키워드 등장
- 작업 경로가 `mk2_hexa/`, `n6/`, `hexa-lang/`, `shared/n6/`, `drill/`, `scripts/*.hexa` 안
- 컴파일러/언어 갭 토론

## 관련

- 전체 stdlib 갭 카탈로그: `design/hexa_lang_gaps_from_atlas.md` (다른 에이전트 영역 — 편집 금지, 조회만)
- 검증된 SSOT 모듈: `n6/atlas_query.hexa`, `mk2_hexa/mk2/src/atlas/*.hexa`
