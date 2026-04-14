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
  enforcement_registry.json  하네스 강제 레이어 맵 — 각 H-룰 × layer(prompt/pre_write/pre_bash/lint/permissions) × file:fn:line × action. 공용 17 + 프로젝트별(nexus 4). 조회: jq '.rules[] | select(.id=="H-NOHOOK")' ~/.../enforcement_registry.json

engine (.hexa):
  entry.hexa           dispatcher — prompt|pretool|post|guard|self_check 서브커맨드, sub-modules 호출
  cmd_gate.hexa        smash/free seed 검증 (추상 단독 토큰 REJECT, 컨텍스트 결합 강제)
  prompt_scan.hexa     UserPromptSubmit 대응 — 사용자 발화 패턴 스캔
  pre_tool_guard.hexa  PreToolUse 대응 — Write/Edit/Bash/Agent 공통 guard
  post_bash.hexa       PostToolUse(Bash) — exit 코드 + stderr 수집
  post_edit.hexa       PostToolUse(Write|Edit) — 산출 파일 검증
  lint.hexa            L1 — R1/R14/L0/pitfalls 체커. --staged/--all/--file
  gc.hexa              L1~L3 단일 라우터 — --scan/--drift/--violation/--dead/--rotate/--prompt-gc/--report/--weekly/--cleanup (gc-weekly + cleanup 흡수 2026-04-14)
  autofix.hexa         L2 — mistakes.jsonl 반복 패턴 감지 → 제안만
  bitter-gate.hexa     새 규칙 추가 전 mandatory — dormant 규칙 폐기 우선
  hook_stdin_gate.hexa  hexa binary read_stdin() round-trip 검증 (stale build 회귀 감지)
  global_claude_guard.hexa  ~/.claude/ 외부 설정 오염 감지 (hooks/CLAUDE.md 금지, settings.json 만 허용)
  handoff_write.hexa        세션 handoff MD writer — git delta + JSONL tail + next-actions → memory/handoff-latest.md
  cli_budget_gate.hexa      JSONL usage 합산 → 임계치 시 handoff_write 호출 + systemMessage (config: shared/config/cli_budget.json)
  health.hexa               atlas + nexus 헬스 라우터 — list|atlas|nexus|all (atlas_health/nexus_ensure_running 위임)
  sync.hexa                 sync 라우터 v1 — 9 원본 sync*.hexa 통합 + N/M/T 신규. manifest SSOT: sync_manifest.json (29 태스크)
  verify.hexa               verify 라우터 — v-const|sync-diff|atlas|all 4종 통합 검증 (lint/sync/atlas_health 위임, 본체 read-only)
  errors.hexa               H-ERR-ROUTE/DRAIN/PROMOTE CLI — severity_map 분류 → errors.jsonl 큐. lib: lib/errors.hexa.inc (copy-paste 소스)
  agent_ledger.hexa         H-AGENT-LEDGER — Agent 호출 전후 등록/마감. 동일 area 활성 시 WARN (block X). SSOT: work_registry.jsonl
  git_fresh.hexa            H-GIT-FRESH — 사용자 입력 시 30분 stale 감지 + origin drift alert (prompt_scan 자동). SSOT: .git_fresh_state.json
  session.hexa              session 라우터 — lock|registry|worktree|prompt_gen 4종 위임
    session_lock.hexa         H-SESSION-LOCK — 파일 area(harness/config/blowup/n6/rules/discovery) 기반 advisory lockdir (/tmp/nexus-lock-{area}/). pre_tool_guard Write/Edit 자동 acquire. WARN-only (exit 미전파). 우회: NEXUS_LOCK_OK=1
    session_registry.hexa     H-SESSION-REGISTRY — 세션 수준 manifest + peers 표시. prompt_scan 자동 register/heartbeat. TERM_SESSION_ID 기반 sha1-12 안정 ID. SSOT: session_registry.jsonl. 우회: NEXUS_SESSION_OK=1
    session_worktree.hexa     H-SESSION-WORKTREE — opt-in git worktree 헬퍼 (init/list/status/merge/prune/gc_branches [--dry-run]). 자동 호출 X. 경로: .worktrees/{session_id}/
    session_prompt_gen.hexa   새 세션 이어받기 프롬프트 자동 생성
  broadcast.hexa            H-BROADCAST — shared/ 변경을 타 세션에 전파. post_edit 자동 append + prompt_scan 자동 tail 300s. SSOT: broadcast.jsonl. 우회: NEXUS_BROADCAST_OK=1
  context_gauge.hexa        컨텍스트 게이지 — 50/25 임계 tool-call 카운트, SSOT: gauge_state.json (gitignore). post_bash/post_edit 자동 tick (Track A).
  instinct.hexa             인스팅트 — scan|score|promote|prune|status, SSOT: instincts/{projects,global}/
  harness_audit.hexa        하네스 스코어카드 — 7 카테고리 0-10 (tool/ctx/qg/mem/eval/sec/cost) max total 70. SSOT: harness_score.jsonl. 모드: full|json|summary (default=full)
  observations.jsonl        (log) 매 post_bash/post_edit 자동 append

policy (H-NOHOOK, 2026-04-14):
  rule           hook 신규 금지 — 모든 자동 강제는 entry.hexa 자율 호출
  pre_guard      check_no_hook_file/cmd  Write/Edit/Bash 차단
  post_edit      H-NOHOOK                .claude/settings*.json hooks 키 비어있지 않으면 라우팅
  lint           check_h_nohook          .claude·.git·shared hooks 신규 파일 + settings hooks 검출
  exempt         shared/archive/, /archive/superseded-, /archive/deprecated_, .git/hooks/{commit-msg,pre-commit,post-commit,pre-push} (H-COMMIT), .githooks/{commit-msg,pre-commit}, *.sample
  bypass         NEXUS_HOOK_OK=1 prefix 또는 파일/경로 내 '@allow-hook' 토큰

policy (H-NEXUSPATH, 2026-04-14):
  rule           $NEXUS/$ANIMA/$HEXA_LANG/$N6_ARCH/$AIRGENOME/$VOID/$PAPERS 프로젝트 변수 강제 — $HOME/Dev/<proj> 리터럴 block
  lint           check_devpath           .hexa/.sh/.json/.jsonl/.md 에서 (~|/Users/<u>|/home/<u>|$HOME|$HOME_DIR)/Dev/<proj> 검출 → error
  canonical fb   ${NEXUS:-$HOME/Dev/nexus}  쉘 스크립트 안전 fallback 패턴 (정규식 예외 자동 허용)
  .hexa fb       env("NEXUS") 우선, 실패 시 env("HOME")+"/Dev/nexus" + // @allow-devpath 마커
  bypass         // @allow-devpath 토큰 (plist 문서 예시, archival evidence)

msg_check_rules: HARNESS-LOCK / L0 / N6-JSONPAIR (commit-msg 훅 최종 검증 — pre-commit COMMIT_EDITMSG 는 N-1 msg 라 구조적 오탐 회피)

convention (2026-04-14~ 훅 시스템 대체):
  사용자 입력 후       entry.hexa prompt
  Write|Edit 후        entry.hexa post write_edit
  Bash 후              entry.hexa post bash
  Agent 호출 전        entry.hexa guard <area> <prompt_hash>   → agent_id stdout (complete 시 사용)
  Agent 완료 후        entry.hexa guard complete <agent_id>
  smash|free 실행      shared/harness/exec_validated {mode} "{seed}" {engine} {args} (cmd_gate 적용, bin/ 심링크 가능)
  sync 실행            entry.hexa sync <list|diff|all|id> [flags]       → sync.hexa 위임
  errors 라우팅        entry.hexa errors <route|drain_check|...> ...    → errors.hexa 위임
  agent_ledger 직접    entry.hexa agent_ledger <register|complete|list|gc|dup_check> ...
  broadcast 전파       entry.hexa broadcast <append|tail|gc|list> ...    → broadcast.hexa 위임
  session_lock 조작    entry.hexa session_lock <acquire|release|list|gc|derive> ...
  session_registry     entry.hexa session_registry <register|heartbeat|list|peers> ...
  session_worktree     entry.hexa session_worktree <init|list|status|merge|prune|gc_branches> ...
  session_prompt_gen   entry.hexa session_prompt_gen [args]              → 세션 이어받기 프롬프트
  gauge 게이지         entry.hexa gauge <tick|status|reset>              → context_gauge.hexa 위임 (post_bash/post_edit 자동 tick)
  전 프로젝트 settings.json hooks={} — 자동 훅 없음. 위 호출은 Claude 자율 실행.

logs (append-only):
  lint_log.jsonl       모든 lint 실행 기록
  gc_log.jsonl         gc 스캔 결과
  mistakes.jsonl       실패만 누적 (P1 실수기록)
  autofix_proposals.jsonl  L2 제안
  rules_usage.jsonl    규칙 히트 감사 (bitter-gate 산출)
  errors.jsonl         H-ERR 오류 큐 — severity/source/file/code/msg/status(open|fixed|stale), drain 임계치 10
  work_registry.jsonl  H-AGENT-LEDGER — agent_id/area/prompt_hash/ts_start/ts_end/status(active|done|stale)
  harness_score.jsonl  H-AUDIT — ts/scores{tool_coverage,context_eff,quality_gate,memory,eval,security,cost}/total/flags

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
  hexa gc.hexa --scan                   drift+violation+dead+prompt_gc 전부
  hexa gc.hexa --weekly                 7일 쿨다운 판정 (env HARNESS_GC_WEEKLY_MODE=force|status)
  hexa gc.hexa --cleanup                shared_survey 폐기 후보 (env HARNESS_CLEANUP_MODE=apply|force)
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
  hexa agent_ledger.hexa register <area> <prompt_hash>    Agent 등록 (동일 area 활성 시 stderr WARN)
  hexa agent_ledger.hexa complete <agent_id>              Agent 마감
  hexa agent_ledger.hexa dup_check <area>                 활성 동일 area 수 출력
  hexa agent_ledger.hexa gc                               3600s+ active → stale (gc.hexa --scan 자동 포함)
  hexa agent_ledger.hexa list                             현재 active agent 목록
  hexa harness_audit.hexa [full|json|summary]             스코어카드 실행 — full=JSONL append+요약 / json=stdout JSON / summary=1줄
  hexa context_gauge.hexa <tick|status|reset>             tool-call 누적 카운터 — 첫 50, 이후 25 간격 stderr WARN. SSOT: gauge_state.json

pending:
  hooks-config.json 등록   gc --weekly 주간 체인 (shared/harness/hooks-config-patch.json 참조)
  실제 검증                sandbox 블록 — 사용자 로컬 실행 필요

parent: ../CLAUDE.md → "harness"
