# harness/ — Hashimoto AI 코딩 하네스 (nexus 이식)

ssot:
  harness.json         thesis + nexus 매핑
  pillars.jsonl        P1 map / P2 auto_enforce / P3 garbage_collect
  levels.jsonl         L1 setup 1~2h / GIGO
  principles.jsonl     H1~H8 (성공 조용/실패 시끄럽게 포함)
  plan.json            실행 스펙 (approved)
  summary.json         총설명 (EN)
  evolution.json       L1→L2→L3→bitter 진화 그래프
  convergence.json     구현 상태 추적
  severity_map.json    H-ERR-ROUTE 분류 SSOT — block/defer/warn (73 lint_rule + 10 gc_kind + 17 exit_signal + 14 source_default)

engine (.hexa):
  entry.hexa           dispatcher — prompt|pretool|post|guard|self_check 서브커맨드, sub-modules 호출
  cmd_gate.hexa        smash/free seed 검증 (추상 단독 토큰 REJECT, 컨텍스트 결합 강제)
  prompt_scan.hexa     UserPromptSubmit 대응 — 사용자 발화 패턴 스캔
  pre_tool_guard.hexa  PreToolUse 대응 — Write/Edit/Bash/Agent 공통 guard
  post_bash.hexa       PostToolUse(Bash) — exit 코드 + stderr 수집
  post_edit.hexa       PostToolUse(Write|Edit) — 산출 파일 검증
  lint.hexa            L1 — R1/R14/L0/pitfalls 체커. --staged/--all/--file
  gc.hexa              L1 — drift/dead/violation 3종 스캔
  autofix.hexa         L2 — mistakes.jsonl 반복 패턴 감지 → 제안만
  gc-weekly.hexa       L3 — 7일 쿨다운 래퍼 (growth-tick/cron 안전)
  bitter-gate.hexa     새 규칙 추가 전 mandatory — dormant 규칙 폐기 우선
  hook_stdin_gate.hexa  hexa binary read_stdin() round-trip 검증 (stale build 회귀 감지)
  global_claude_guard.hexa  ~/.claude/ 외부 설정 오염 감지 (hooks/CLAUDE.md 금지, settings.json 만 허용)
  handoff_write.hexa        세션 handoff MD writer — git delta + JSONL tail + next-actions → memory/handoff-latest.md
  cli_budget_gate.hexa      JSONL usage 합산 → 임계치 시 handoff_write 호출 + systemMessage (config: shared/config/cli_budget.json)
  session_prompt_gen.hexa   새 세션 이어받기 프롬프트 자동 생성
  health.hexa               atlas + nexus 헬스 라우터 — list|atlas|nexus|all (atlas_health/nexus_ensure_running 위임)
  sync.hexa                 sync 라우터 v1 — 9 원본 sync*.hexa 통합 + N/M/T 신규. manifest SSOT: sync_manifest.json (29 태스크)
  errors.hexa               H-ERR-ROUTE/DRAIN/PROMOTE CLI — severity_map 분류 → errors.jsonl 큐. lib: lib/errors.hexa.inc (copy-paste 소스)

convention (2026-04-14~ 훅 시스템 대체):
  사용자 입력 후       entry.hexa prompt
  Write|Edit 후        entry.hexa post write_edit
  Bash 후              entry.hexa post bash
  Agent 호출 전        entry.hexa guard
  smash|free 실행      shared/harness/exec_validated {mode} "{seed}" {engine} {args} (cmd_gate 적용, bin/ 심링크 가능)
  전 프로젝트 settings.json hooks={} — 자동 훅 없음. 위 호출은 Claude 자율 실행.

logs (append-only):
  lint_log.jsonl       모든 lint 실행 기록
  gc_log.jsonl         gc 스캔 결과
  mistakes.jsonl       실패만 누적 (P1 실수기록)
  autofix_proposals.jsonl  L2 제안
  rules_usage.jsonl    규칙 히트 감사 (bitter-gate 산출)
  errors.jsonl         H-ERR 오류 큐 — severity/source/file/code/msg/status(open|fixed|stale), drain 임계치 10

cooldown:
  .gc_weekly_cooldown  unix ts — 7일 제한

hook:
  .git/hooks/pre-commit  lint 체인 (30s 타임아웃, exit 1만 차단)

principle:
  Sutton bitter lesson   모델 똑똑해질수록 하네스 단순해져야
  deletion-first         새 규칙 추가 전 bitter-gate --audit 로 dormant 폐기
  silent-success         성공 무출력, 실패만 stderr + mistakes 기록
  ai-native              모든 산출물 JSONL

entrypoints:
  hexa lint.hexa --staged               매 커밋 자동
  hexa gc.hexa --scan                   수동 또는 gc-weekly 경유
  hexa gc-weekly.hexa                   쿨다운 자동 판정
  hexa autofix.hexa --analyze           mistakes 누적 후 수동
  hexa bitter-gate.hexa --audit         새 규칙 추가 전 mandatory
  hexa hook_stdin_gate.hexa             hexa binary 회귀 감지 (실패 시 mistakes.jsonl + stderr, 성공 무출력)
  hexa global_claude_guard.hexa         ~/.claude/ 오염 감지 (CLAUDE.md/hooks/* 발견 시 mistakes.jsonl + stderr)
  hexa handoff_write.hexa <reason>      수동 handoff 저장 (reason ∈ commit|checkpoint|handoff|emergency|manual)
  hexa cli_budget_gate.hexa             세션 usage 임계치 감지 (UserPromptSubmit 자동 실행, cooldown 상태 파일로 중복 방지)
  hexa health.hexa all                  atlas + nexus 종합 헬스 (cron 30분 주기 권장 — com.nexus.health)
  hexa sync.hexa list|diff|all|<id>     sync 라우터 — list(29태스크)/diff(drift)/all(active)/단일(id) [--dry-run] [--no-git]
  hexa errors.hexa route <src> <file> <line> <code> [msg]  오류 라우팅 (severity_map 분류)
  hexa errors.hexa drain_check [N=10]   큐 임계치 체크 (prompt_scan 자동 호출, 우회=NEXUS_DRAIN_OK=1)
  hexa errors.hexa count_open|promote|mark_fixed <key>    통계/승격/완료 처리

pending:
  hooks-config.json 등록   gc-weekly 주간 체인 (shared/harness/hooks-config-patch.json 참조)
  실제 검증                sandbox 블록 — 사용자 로컬 실행 필요

parent: ../CLAUDE.md → "harness"
