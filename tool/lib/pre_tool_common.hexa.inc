// ═══════════════════════════════════════════════════════════
// lib/pre_tool_common.hexa.inc — pre_tool_guard 공용 헬퍼
// 사용: errors.hexa.inc 패턴 — 소비자 .hexa 상단에 copy-paste.
//       (hexa stage1 native include 미지원. 본 파일은 canonical source.)
//
// 목적: pre_tool_guard.hexa 카테고리 분리 refactor (H-마커 8 혼재 해소).
// 참조 main: shared/tool/pre_tool_guard.hexa
// 형제 inc: pre_tool_write.hexa.inc / pre_tool_bash.hexa.inc / pre_tool_agent.hexa.inc
//
// 공통 가드 상수 / 헬퍼:
//   _guard_noname_v_match(s) — H-NONAME-V 버전 suffix 탐지
// ═══════════════════════════════════════════════════════════

// H-NONAME-V 버전 suffix 매칭 — basename stem 또는 dir segment 에 대해
// 반환: 매칭된 suffix (e.g. "_v2"), 없으면 ""
fn _guard_noname_v_match(s: str) -> str {
    if s.len() == 0 { return "" }
    let suffixes = [
        "_v1", "_v2", "_v3", "_v4", "_v5", "_v6", "_v7", "_v8", "_v9",
        "_v10", "_v11", "_v12", "_v13", "_v14", "_v15",
        "_V1", "_V2", "_V3", "_V4", "_V5",
        "_mk1", "_mk2", "_mk3", "_mk4", "_mk5", "_mk6", "_mk7", "_mk8", "_mk9",
        "_Mk1", "_Mk2", "_Mk3", "_Mk4", "_Mk5", "_Mk6", "_Mk7", "_Mk8", "_Mk9",
        "_MK1", "_MK2", "_MK3",
        ".v1", ".v2", ".v3", ".v4", ".v5", ".v6", ".v7", ".v8", ".v9",
        ".V1", ".V2", ".V3",
        ".mk1", ".mk2", ".mk3", ".mk4", ".mk5",
        ".Mk1", ".Mk2", ".Mk3", ".Mk4", ".Mk5",
        "_Mk.II", "_Mk.III", "_Mk.IV", "_Mk.V", "_Mk.VI", "_Mk.VII", "_Mk.VIII", "_Mk.IX", "_Mk.X",
        "_mk.II", "_mk.III", "_mk.IV", "_mk.V", "_mk.VI", "_mk.VII",
        "_new", "_final", "_copy", "-new", "-final", "-copy",
        " copy", " (1)", " (2)", " (3)", " (4)", " (5)", " (6)", " (7)", " (8)", " (9)",
        " copy 2", " copy 3", " copy 4", " copy 5"
    ]
    for sfx in suffixes {
        if s.ends_with(sfx) { return sfx }
    }
    return ""
}
