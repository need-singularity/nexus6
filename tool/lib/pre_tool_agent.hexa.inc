// ═══════════════════════════════════════════════════════════
// lib/pre_tool_agent.hexa.inc — Agent (Task 도구) PreToolUse 가드
// 사용: errors.hexa.inc 패턴 — 소비자 .hexa 상단에 copy-paste.
//       (hexa stage1 native include 미지원. 본 파일은 canonical source.)
//
// 목적: pre_tool_guard.hexa 카테고리 분리 refactor (H-마커 8 혼재 해소).
// 참조 main: shared/tool/pre_tool_guard.hexa
//
// 현재 상태: Agent 전용 가드는 entry.hexa `guard` 서브커맨드(agent_ledger 위임)가 담당.
//            pre_tool_guard 레벨에서는 Agent 차단 룰 없음 — 본 파일은 스텁.
//
// 확장 예정 후보:
//   check_agent_ledger_dup        동일 area 활성 Agent 중복 (H-AGENT-LEDGER WARN)
//   check_agent_context_budget    session 수준 agent spawn 한도
//
// 호출 관례: entry.hexa guard <area> <prompt_hash>  →  agent_ledger.hexa register
// ═══════════════════════════════════════════════════════════

// (placeholder) Agent PreToolUse 가드 — 현재 룰 없음, 빈 문자열 반환
fn check_agent_placeholder(tool: str, arg: str) -> str {
    return ""
}
