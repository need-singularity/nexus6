# CLAUDE.md — NEXUS-6 중앙 허브

## 🔴 절대 규칙

- **HEXA-FIRST**: 모든 코드는 `.hexa`로 작성.
- **하드코딩 금지**: 상수/도메인/키워드를 코드에 나열 금지 → `shared/*.jsonl`에서 동적 로드.
- **경로**: `exec("printenv HOME")` + 상대경로. 절대경로 하드코딩 금지.
- **NEXUS-6 연동**: 돌파 시 `blowup.hexa <domain> 3 --no-graph`, 발견 → `shared/growth_bus.jsonl`.
- **백그라운드 필수**: 10초+ 명령은 `run_in_background: true`. 대화 차단 금지.
- **서버 직접 수정 금지**: 로컬 리포 → git commit → 배포 스크립트.

## 프로젝트 개요

NEXUS-6 = 전 리포 공유 발견 엔진 + 인프라 허브.
엔진: `mk2_hexa/native/*.hexa` (hexa-lang 컴파일러).
심링크: 모든 리포의 `.shared/` → `nexus/shared/`.

## 참조 링크

| 항목 | 파일 | 내용 |
|------|------|------|
| 규칙 | `shared/absolute_rules.json` | R1~R8 + NX1~3 절대 규칙 |
| 보호 | `shared/core-lockdown.json` | L0 코어 22개 잠금 |
| 수렴 | `shared/convergence/nexus.json` | CDO 수렴 상태 |
| 할일 | `shared/todo/nexus.json` | 우선순위별 TODO |
| 명령 | `shared/core.json` → `commands` | 14종 명령 매핑 |
| 코어 | `shared/core.json` | 시스템맵 + 폴더 구조 |
| 렌즈 | `shared/lens_registry.json` | 1022종 망원경 레지스트리 |
| API | `shared/CLAUDE.md` | NEXUS-6 상세 사용법 |
| 문법 | `shared/hexa_grammar.jsonl` | hexa-lang 전체 문법 + pitfalls |

## hexa-lang 실수 방지 (상위 5)

P1: 세미콜론 금지 / P2: `exec("단일 문자열")` / P3: Error→`to_string()` 래핑 / P4: `#{}` Map 내장 사용 / P5: `printenv HOME` + 상대경로. 상세: `shared/hexa_grammar.jsonl` pitfalls 섹션.

## 할일

- "todo", "할일" → `hexa-bin-actual todo.hexa nexus` 실행 후 마크다운 표로 출력.
- "전체 할일" → `hexa-bin-actual todo.hexa` (전 프로젝트).

## 특이점 사이클

> 블로업→수축→창발→특이점→흡수 5단계. 엔진: `mk2_hexa/native/blowup.hexa` (7-phase).

| 키워드 | 실행 |
|--------|------|
| "블로업" | `hexa blowup.hexa <domain> 3 --no-graph --seeds "$(hexa seed_engine.hexa merge)"` |
| "돌파" | `hexa breakthrough.hexa` (1회 자동: gap→mine→blowup) |
| "연속돌파", "수렴" | `hexa breakthrough.hexa --converge` |
| "방향", "다음" | `hexa directions.hexa report` |
| "전체 리포트" | `hexa command_router.hexa "전체 리포트"` |
| "anima 상태" | `hexa anima_status.hexa` |

## 리소스 보호

n6-guard 태스크 스케줄러 관리. `~/.config/n6-guard.toml` 준수. 동시 실행 max 2 (burst 4).

## 메모리 네이밍

`{type}-{kebab-topic}.md` — f(feedback) / p(project) / r(reference) / u(user) / h(history YYYYMMDD).
