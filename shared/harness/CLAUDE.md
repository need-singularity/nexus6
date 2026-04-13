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

engine (.hexa):
  lint.hexa            L1 — R1/R14/L0/pitfalls 체커. --staged/--all/--file
  gc.hexa              L1 — drift/dead/violation 3종 스캔
  autofix.hexa         L2 — mistakes.jsonl 반복 패턴 감지 → 제안만
  gc-weekly.hexa       L3 — 7일 쿨다운 래퍼 (growth-tick/cron 안전)
  bitter-gate.hexa     새 규칙 추가 전 mandatory — dormant 규칙 폐기 우선
  hook_stdin_gate.hexa  hexa binary read_stdin() round-trip 검증 (stale build 회귀 감지)

logs (append-only):
  lint_log.jsonl       모든 lint 실행 기록
  gc_log.jsonl         gc 스캔 결과
  mistakes.jsonl       실패만 누적 (P1 실수기록)
  autofix_proposals.jsonl  L2 제안
  rules_usage.jsonl    규칙 히트 감사 (bitter-gate 산출)

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

pending:
  hooks-config.json 등록   gc-weekly 주간 체인 (shared/harness/hooks-config-patch.json 참조)
  실제 검증                sandbox 블록 — 사용자 로컬 실행 필요

parent: ../CLAUDE.md → "harness"
