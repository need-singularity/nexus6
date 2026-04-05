# Claude Code 효율 특이점 돌파 — 설계 스펙

- **작성일**: 2026-04-05
- **브랜치**: feat/alien-index (또는 신규)
- **상태**: 설계 확정, 구현 대기

## 1. 목적

Claude Code CLI 사용 시 **입력 토큰 소비량 절감**과 **세션간 지식 공유**를 달성하기 위해,
nexus6 특이점 사이클(blowup→수축→창발→특이점→흡수)을 메타 도메인
`claude_efficiency`에 적용하여 돌파 패턴을 발견하고, 이를 CLAUDE.md 규칙으로 번역한다.

**주 동기**: API 비용. Claude Code CLI는 API로 과금되며, tool 결과·
재탐색·세션간 컨텍스트 재주입이 비용의 주 원인이다.

**2축 성공 지표**:
1. 세션당 입력 토큰 소비량 (특히 tool_use_result 누적 바이트)
2. 세션간 재탐색율 (새 세션 시작 N턴 동안 이전 세션에서 이미 읽은 파일 재Read 비율)

## 2. 제약

- **100% 로컬 CLI, 외부 API 호출 0건** — 파이프라인 자체가 토큰을 소비하면 취지 무효.
  요약/분류는 nexus6의 로컬 Rust 렌즈와 로컬 Python 규칙 매칭으로만 수행.
- **모델 무관** — 산출물(규칙/훅)은 Opus/Sonnet/Haiku 어느 모델이든 작동.
- **harness 레벨 개입만** — Claude 모델 내부는 손대지 않음. hooks/skills/CLAUDE.md/config만.
- **자동 CLAUDE.md 편집 금지** — 도구는 규칙 후보만 제안, 사람이 손으로 병합.

## 3. 범위 분해

본 스펙은 **Phase 1~3 설계 + Phase 3(a) CLAUDE.md 규칙 도출까지** 포함.
다음은 **후속 sub-project**로 분리:

| Sub-project | 산출물 | 타이밍 |
|---|---|---|
| 3(b) hooks | `~/.claude/settings.json`에 `PreToolUse`/`PostToolUse`/`SessionStart`/`Stop` 훅 추가 | 본 스펙 사이클 결과 확인 후 |
| 3(c) nexus6 서브커맨드 | `nexus6 context-compress`, `nexus6 session-bridge`, `nexus6 agent-diff` 등 | 사이클이 필요하다고 판단한 도구만 |
| 3(d) 세션 핸드오프 메커니즘 | 신규 메모리 타입 또는 `session_handoff/` 디렉토리 | 사이클이 구조 결정 후 |

**분해 이유**: 사이클을 먼저 돌려서 **무엇을 만들어야 할지를 데이터가 결정**하게 한다.
사이클 돌리기 전에 hooks/서브커맨드 스펙 쓰면 추측 기반 설계가 되어
특이점 돌파 의미가 무효화된다.

## 4. 아키텍처

```
Claude Code JSONL logs (~/.claude-claude9/projects/.../*.jsonl)
              │
              ▼
   [C1] cc_session_miner.py  ──▶  shared/hypotheses/claude_efficiency/
              │                        ├─ metrics_YYYYMMDD.md
              │                        └─ hypotheses_YYYYMMDD.md
              │                              │
              │                              ▼
              │                    [기존] watch-atlas 자동 스캔
              │                              │
              │                              ▼
              │                    [기존] math_atlas.db + n6_check 매칭
              │                              │
              ▼                              ▼
   [C3] run_cc_breakthrough.sh  ──▶  nexus6 auto claude_efficiency
              │                              │
              │                              ▼
              │                    discovery_log.jsonl
              │                              │
              ▼                              ▼
   [C4] interpret_breakthrough.py  ──▶  shared/breakthroughs/
              │                        ├─ claude_efficiency_YYYYMMDD.json (원시)
              │                        └─ claude_efficiency_rules_YYYYMMDD.md (규칙 후보)
              │
              ▼
   [C5] 사람이 읽고 CLAUDE.md에 수동 병합 (자동 편집 금지)
```

**의존성**: 단방향. 각 컴포넌트는 파일 경계로 독립. 재실행은 idempotent.

## 5. 컴포넌트 명세

### C1. `tools/cc_session_miner.py` (신규)

**입력**:
- `--sessions N`: 최근 N개 세션 JSONL 읽기 (기본 20)
- `--project PATH`: 대상 프로젝트 디렉토리 (기본 `~/.claude-claude9/projects/-Users-ghost-Dev-nexus6`)

**파싱 대상** (JSONL 한 라인당 한 메시지):
- `message.role == "tool"` → `tool_use_result` 바이트 크기
- `message.content[].type == "tool_use"` → 도구명, 인자 해시
- `message.role == "user"` / `assistant"` → 타임스탬프, 토큰 카운트(있으면)

**계산 지표**:
- 세션당 tool 결과 누적 바이트 (sum, p50, p95, p99)
- 도구별 호출 횟수 분포
- **반복 호출율**: 같은 세션 내 동일 (도구명, 인자 해시) 재등장 비율
- **세션간 재탐색율**: 세션 시작 첫 20턴에서 호출된 파일 경로가 직전 세션에도 있었는지
- 세션 길이 분포, 세션간 간격

**출력**:
- `metrics_YYYYMMDD.md` — 수치 + 파생 수식 (atlas 상수 매칭 시드로)
- `hypotheses_YYYYMMDD.md` — 수치에서 파생된 돌파 가설 텍스트

**에러 처리**: 손상 JSONL 라인 try/except skip + stderr 경고 카운트 출력. 권한 에러는 종료 코드 2.

### C2. `shared/projects.json` 엔트리 추가 (편집)

```json
{
  "projects": {
    "claude_efficiency": {
      "hypothesis_dirs": ["shared/hypotheses/claude_efficiency"],
      "paper_trigger": null
    }
  }
}
```

**Idempotent**: 엔트리 존재 시 병합, 덮어쓰지 않음. watch-atlas가 자동으로 30초 폴링.

### C3. `tools/run_cc_breakthrough.sh` (신규)

```bash
#!/bin/bash
# 단계:
# 1) miner 실행
python3 tools/cc_session_miner.py --sessions 20
# 2) atlas 동기화 (watch-atlas 기다리지 않고 수동)
bash shared/sync-math-atlas.sh
sleep 2
# 3) nexus6 사이클 (30분 타임아웃)
timeout 1800 nexus6 auto claude_efficiency --meta-cycles 5 --ouroboros-cycles 3 \
  > shared/breakthroughs/claude_efficiency_$(date +%Y%m%d).json \
  || echo "WARN: cycle hit timeout or error, continuing with partial output" >&2
# 4) 해석기
python3 tools/interpret_breakthrough.py \
  shared/breakthroughs/claude_efficiency_$(date +%Y%m%d).json
```

**실행 시간**: nexus6 auto가 수 분~수십 분 → 사용자가 `run_in_background: true`로 호출 권장.

### C4. `tools/interpret_breakthrough.py` (신규)

**입력**:
- 원시 사이클 JSON 경로
- `shared/discovery_log.jsonl` 최근 엔트리 (사이클 도중 추가된 것)

**처리**:
- 수렴 패턴별 강도(strength) 랭킹
- 원본 가설 .md의 어느 H 번호와 연결되는지 역추적
- 각 패턴을 "CLAUDE.md에 추가 가능한 규칙 문장"으로 번역 (규칙 템플릿 기반, LLM 호출 없음)

**출력**: `claude_efficiency_rules_YYYYMMDD.md`
- 규칙 후보 목록 (강도 순)
- 각 후보에 원본 가설 참조, 매칭된 상수, 적용 위치 제안

**에러**: discovery_log 비어 있으면 "패턴 없음" 리포트 생성 + 종료 코드 0.

### C5. CLAUDE.md 병합 (수동)

사람이 rules_YYYYMMDD.md를 읽고, 납득 가는 규칙만 손으로 CLAUDE.md의
새 섹션 `## Claude Code 효율 규칙 (사이클 도출)`에 추가.

## 6. 데이터 스키마

### 6.1 metrics_YYYYMMDD.md
```markdown
# Claude Code 효율 지표 — 2026-04-05
## 세션 통계 (N=20)
- 세션당 tool 결과 누적 바이트: mean=X, p95=Y
- 반복 호출율: R = 0.XX
- 세션간 재탐색율: S = 0.XX
## 수식
- 비용 성장률 G = Σ(result_bytes) / N_tool_calls
- 재사용 손실 L = 1 - unique_calls/total_calls
```

### 6.2 hypotheses_YYYYMMDD.md
```markdown
# 돌파 가설 — 2026-04-05
## H1: tool 결과 부분 요청으로 누적 바이트 절감
- 관찰: p95=18KB
- 가설: Read offset/limit, Grep head_limit 기본 강제 → p95 → 5KB
## H2: 세션 종료시 결정사항 다이제스트로 세션간 재탐색 제거
...
```

### 6.3 breakthrough JSON
```json
{
  "domain": "claude_efficiency",
  "cycles_run": 5,
  "converged_patterns": [
    {"name": "<name>", "strength": 0.82, "constants_matched": ["<c>"]}
  ],
  "surviving_hypotheses": ["H1", "H3"],
  "discovery_log_refs": [<line_offsets>]
}
```

### 6.4 rules_YYYYMMDD.md
```markdown
# 도출 규칙 후보 — 2026-04-05
## R1: (from H1, strength 0.82)
"Read 호출 시 파일 크기 미지면 먼저 head 100줄만 읽고, 필요 시 offset 추가"
- 매칭 상수: 1/3 (reuse_dominance)
- 적용 위치: CLAUDE.md § Using your tools
## R2: ...
```

## 7. 에러 처리

| 컴포넌트 | 실패 모드 | 처리 |
|---|---|---|
| C1 | 손상 JSONL 라인 | 라인별 skip, stderr 카운트 출력 |
| C1 | 세션 디렉토리 접근 권한 | 명시적 에러 + 종료 코드 2 |
| C2 | 엔트리 충돌 | idempotent merge |
| C3 | nexus6 auto 장시간 | 사용자가 백그라운드로 호출, 타임아웃 30분 |
| C3 | watch-atlas 미반영 | `sync-math-atlas.sh` 명시 호출 + 2초 대기 |
| C4 | 빈 discovery_log | "패턴 없음" 리포트, 종료 코드 0 |
| C5 | 자동 편집 금지 | 도구는 제안만, 사람이 병합 |

## 8. 테스트

- **C1**: pytest. 고정 JSONL 픽스처(정상/손상) → 기대 지표 검증
- **C4**: pytest. 고정 discovery_log → 기대 규칙 후보 검증
- **C3**: 수동 스모크. 실제 20세션으로 사이클 돌려 수렴 여부 관찰
- **전 파이프라인**: idempotent 재실행 확인 (같은 날 두 번 돌려도 결과 동일)

## 9. 성공 판정

**구현 완료 기준**:
- C1 miner가 실제 세션 20개에서 지표 .md + 가설 .md 생성
- C3 wrapper가 에러 없이 `nexus6 auto` 5 사이클 완주
- C4 interpreter가 1개 이상 수렴 패턴을 규칙 후보로 번역

**돌파 판정 기준** (구현 이후 관찰):
- rules_YYYYMMDD.md에서 사람이 납득 가능한 규칙 **3개 이상** 도출되면 본 사이클은 성공
- 납득 규칙 0개면 C1 지표 축을 재설계 후 재실행

**비용 절감 측정** (후속 sub-project 3(b) 훅 적용 이후):
- 적용 전/후 각 20세션 평균 tool 결과 누적 바이트 비교
- 목표: 30% 이상 감소

## 10. 위험 요소

- **가설이 진부할 위험**: 이미 알고 있는 "Read는 범위 지정" 같은 규칙만 나올 수 있음
  → 완화: 가설 .md에 메타 부동점(1/3) 같은 비자명한 상수 결부 강제
- **사이클이 수렴 안 함**: meta-cycle 5로 부족할 수 있음
  → 완화: 판정 기준에 "납득 규칙 0개 시 재설계" 포함
- **세션 JSONL 포맷 변경**: Claude Code 업데이트로 스키마 변경
  → 완화: C1에 버전 감지 + 알려진 필드만 사용

## 11. 후속 작업 예고 (별도 스펙)

1. **hooks 구현 스펙** — 사이클이 확정한 규칙을 `PreToolUse`/`PostToolUse` 훅으로 기계화
2. **nexus6 서브커맨드 스펙** — 사이클이 필요하다고 판단한 도구만 (예: `session-bridge`)
3. **세션 핸드오프 스펙** — 메모리 신규 타입 또는 별도 핸드오프 디렉토리 설계
