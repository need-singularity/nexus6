# 하네스 — 사용자 가이드

AI 코딩 하네스(Mitchell Hashimoto, Ghostty 2026-02)를 nexus에 이식한 시스템. 규칙 강제 + 실수 누적 + 주기적 청소 + 규칙 자기감사.

## 언제 쓰나

- **매 커밋**: 자동. `.git/hooks/pre-commit` 이 린트 체인을 돌림. 성공하면 아무 출력 없음, 실패하면 커밋 차단 + stderr JSON.
- **매 세션 시작**: 자동. `harness-gc-weekly` 훅이 7일마다 1회 gc 실행. 나머지 세션은 즉시 통과(silent).
- **수동 (아래 명령)**:

## 수동 명령

### 린트 수동 실행

```bash
hexa shared/harness/lint.hexa --staged      # 스테이징된 파일만 (pre-commit이 자동으로 함)
hexa shared/harness/lint.hexa --all         # shared/ 전체
hexa shared/harness/lint.hexa --file 경로    # 특정 파일 하나
```

**종료 코드**: 0 = 통과, 1 = 위반(차단). 그 외는 환경 이슈 (커밋 안 막음).

### 가비지 컬렉션

```bash
hexa shared/harness/gc.hexa --scan          # drift + violation + dead 전부
hexa shared/harness/gc.hexa --drift         # 문서↔실제 경로 불일치만
hexa shared/harness/gc.hexa --violation     # 규칙 위반 grep만
hexa shared/harness/gc.hexa --dead          # 90일 미변경 + 미참조 (느림)
hexa shared/harness/gc.hexa --report        # 최근 로그 5줄
```

### 자동 교정 제안 (L2)

```bash
hexa shared/harness/autofix.hexa --analyze                  # mistakes.jsonl 분석
hexa shared/harness/autofix.hexa --analyze --threshold 5    # 반복 기준 (기본 3)
hexa shared/harness/autofix.hexa --analyze --window 200     # 최근 N줄 (기본 500)
hexa shared/harness/autofix.hexa --report                   # 최근 제안
```

**코드를 자동 수정하지 않음**. 반복 패턴을 찾아 `autofix_proposals.jsonl`에 제안만 적는다. 사용자가 제안을 보고 규칙 개정 또는 파일 수정을 결정.

### 주간 GC (L3)

```bash
hexa shared/harness/gc-weekly.hexa            # 필요하면 실행, 아니면 silent
hexa shared/harness/gc-weekly.hexa --status   # 마지막 실행 / 쿨다운 잔여
hexa shared/harness/gc-weekly.hexa --force    # 쿨다운 무시 강제 실행
```

### Bitter Lesson 게이트

```bash
hexa shared/harness/bitter-gate.hexa --audit             # 규칙별 히트 감사
hexa shared/harness/bitter-gate.hexa --audit --window 500 # 최근 N줄 범위
hexa shared/harness/bitter-gate.hexa --report            # 최근 감사 결과
```

**새 규칙 추가 전 필수**. `status: dormant` 규칙이 나오면 추가보다 폐기를 먼저.

## 결과물 (모두 append-only JSONL)

| 파일 | 누가 쓰나 | 무엇 |
|---|---|---|
| `lint_log.jsonl` | lint.hexa | 모든 린트 실행 (pass/fail 전부) |
| `gc_log.jsonl` | gc.hexa | gc 스캔 결과 |
| `mistakes.jsonl` | lint + gc | **실패만** 누적 (실수 기록) |
| `autofix_proposals.jsonl` | autofix.hexa | L2 제안 |
| `rules_usage.jsonl` | bitter-gate.hexa | 규칙 히트 감사 |

## 원칙

1. **성공은 조용히, 실패는 시끄럽게** — 성공 시 stdout 침묵. 실패 시 stderr JSON + 커밋 차단
2. **자동 수정 금지** — nexus 위반은 대개 의도된 것. 자동 교정 대신 제안+사람 결정
3. **폐기 우선** — 새 규칙 추가 전 bitter-gate로 dormant 규칙부터 제거
4. **AI-native** — 모든 결과물 JSONL, 산문 문서는 이 README와 CLAUDE.md만

## 체크하는 규칙

| 규칙 | 내용 | 어디서 |
|---|---|---|
| R1 | `shared/` 밑에 `.py`/`.sh` 신규 금지 (예외: `shared/scripts/`, `shared/bin/`) | lint + gc |
| R14 | `shared/rules/` `shared/config/` 에 prose `.md` 금지 (CLAUDE.md 제외) | lint + gc |
| L0 | L0 보호 영역 수정 시 커밋 메시지에 `chore(lockdown):` 또는 `L0-approved` 필요 | lint |
| P-PY-HEAVY | `.hexa` 한 파일에 `python3 -c` 10회 초과 시 경고 | lint |
| drift | `CLAUDE.md` 언급 경로가 실제 없으면 경고 | gc |
| dead | 90일 미변경 + 타 파일 참조 0 | gc |

## 자주 하는 실수

### "커밋이 안 되요"

```
❌ harness-lint 위반 — shared/harness/lint_log.jsonl 참조
```

`lint_log.jsonl` 마지막 줄을 보고 `violations[]` 에서 `file`/`rule` 확인. 규칙에 따라 파일 수정.

### "자기 걸로 통과시키고 싶어요"

- R1 예외: `shared/scripts/` 또는 `shared/bin/` 아래로 옮기거나, `.hexa`로 변환
- L0 경고: 커밋 메시지 첫 줄에 `chore(lockdown):` prefix
- R14: `.md` 내용을 `CLAUDE.md`나 JSON으로 변환

### "hexa 바이너리가 안 돌아요"

린트/gc는 `hexa` 바이너리 필요. pre-commit은 exit 1(위반)에만 차단하고 기타 exit 코드(137 등 환경 이슈)는 통과시키니 괜찮다.

## 전체 구조

```
shared/harness/
├── README.md              ← 이 파일 (사용자 가이드)
├── CLAUDE.md              ai 에이전트용 인덱스
├── harness.json           thesis + 매핑
├── pillars.jsonl          3기둥 정의
├── levels.jsonl           설정 레벨
├── principles.jsonl       H1~H8 원칙
├── plan.json              실행 스펙
├── summary.json           총설명 (EN)
├── evolution.json         L1→L2→L3→bitter 그래프
├── convergence.json       구현 상태
├── hooks-config-patch.json  SessionStart 등록 기록
├── lint.hexa              L1 린터
├── gc.hexa                L1 가비지 컬렉터
├── autofix.hexa           L2 자동 교정 제안
├── gc-weekly.hexa         L3 주간 래퍼
├── bitter-gate.hexa       규칙 감사
├── lint_log.jsonl         (append)
├── gc_log.jsonl           (append)
├── mistakes.jsonl         (append, 실패만)
├── autofix_proposals.jsonl (append, 제안)
├── rules_usage.jsonl      (append, 감사)
└── .gc_weekly_cooldown    (unix ts)
```

## 참고

- 원본 강연: Mitchell Hashimoto "AI 코딩 하네스" (Ghostty, 2026-02)
- Sutton "쓴 교훈" (The Bitter Lesson): 모델이 똑똑해질수록 하네스는 더 단순해져야
