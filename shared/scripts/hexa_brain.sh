#!/bin/bash
# hexa_brain.sh — tier2 AI 판단 (launchd 5분 주기)
#
# Why: tier1 reflex 는 결정론적 방어. tier2 는 claude -p 로 상황 판단 + 개선 제안.
# - 자원 최적화 (idle 계정 활용 제안)
# - 패턴 학습 (반복 runaway → 근본원인 조사 권장)
# - 장기 전략 (load 추세 분석)

set -u

LOG_DIR="${HOME}/.airgenome"
GUARD_LOG="${LOG_DIR}/hexa_guard.jsonl"
BRAIN_LOG="${LOG_DIR}/hexa_brain.jsonl"
mkdir -p "$LOG_DIR"

CLAUDE_BIN="${HEXA_BRAIN_CLAUDE:-$HOME/.local/bin/claude}"
CL_BIN="${NEXUS:-$HOME/Dev/nexus}/shared/bin/cl"
PROMPT_FILE="${NEXUS:-$HOME/Dev/nexus}/shared/harness/hexa_brain_prompt.md"
EFFORT="${HEXA_BRAIN_EFFORT:-low}"

now_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }

# Vitals 수집 (lightweight — sample 1회)
LOAD=$(uptime 2>/dev/null | sed -E 's/.*load averages?: //')
TOP_PROCS=$(ps -eo pid=,pcpu=,%mem=,etime=,command= 2>/dev/null | sort -k2 -rn | head -6)
MEM_STATS=$(vm_stat 2>/dev/null | head -8)
RECENT_REFLEX=$(tail -25 "$GUARD_LOG" 2>/dev/null)
[[ -z "$RECENT_REFLEX" ]] && RECENT_REFLEX="(no reflex events yet)"
CL_STATUS=$("$CL_BIN" u 2>/dev/null)
[[ -z "$CL_STATUS" ]] && CL_STATUS="(cl unavailable)"

# reflex 추적 중인 PID 수
REFLEX_ACTIVE=0
[[ -d "$LOG_DIR/hexa_reflex_state" ]] && \
    REFLEX_ACTIVE=$(find "$LOG_DIR/hexa_reflex_state" -type f 2>/dev/null | wc -l | tr -d ' ')

# PROMPT 조립
PAYLOAD=$(cat <<EOF
## Vitals snapshot (UTC $(now_iso))

### load/cpu
$LOAD

### memory (vm_stat)
$MEM_STATS

### top 5 CPU processes
$TOP_PROCS

### reflex state (active=$REFLEX_ACTIVE)
$RECENT_REFLEX

### claude account utilization
$CL_STATUS

---

위 데이터로 hexa_brain_prompt.md 지침에 따라 JSON 1줄 출력.
EOF
)

# claude 호출 — 안전 모드 (도구 전부 비허용)
SYS_PROMPT=""
[[ -f "$PROMPT_FILE" ]] && SYS_PROMPT=$(cat "$PROMPT_FILE")

if [[ -z "$SYS_PROMPT" ]]; then
    SYS_PROMPT="airgenome hexa-brain — vitals 보고 JSON 1줄 상태판단 출력."
fi

# --disallowedTools 로 모든 도구 차단 — 순수 판단만
# NOTE: --disallowedTools 는 variadic → 마지막 positional prompt 삼킴. 콤마 구분 + stdin 으로 prompt.
RESULT=$(printf '%s' "$PAYLOAD" | "$CLAUDE_BIN" -p --effort "$EFFORT" \
    --append-system-prompt "$SYS_PROMPT" \
    --disallowedTools "Bash,Edit,Write,Read,Glob,Grep,Task,WebFetch,WebSearch" \
    2>&1)

CLAUDE_EXIT=$?

# JSONL 기록 — RESULT 를 안전하게 인코딩
RESULT_JSON=$(printf '%s' "$RESULT" | jq -Rs . 2>/dev/null)
[[ -z "$RESULT_JSON" ]] && RESULT_JSON='"(encoding_error)"'

printf '{"ts":"%s","tier":2,"exit":%d,"effort":"%s","output":%s}\n' \
    "$(now_iso)" "$CLAUDE_EXIT" "$EFFORT" "$RESULT_JSON" >> "$BRAIN_LOG"

# brain 출력이 유효한 JSON 한 줄이면 guard.jsonl 에도 merge (tier1 과 조인하기 쉽게)
if printf '%s' "$RESULT" | tail -1 | jq -e . >/dev/null 2>&1; then
    BRAIN_JSON=$(printf '%s' "$RESULT" | tail -1)
    printf '{"ts":"%s","tier":2,"brain":%s}\n' "$(now_iso)" "$BRAIN_JSON" >> "$GUARD_LOG"

    # recommend 를 action queue 에 append (1h TTL dedup)
    ACTIONS_BIN="${NEXUS:-$HOME/Dev/nexus}/shared/scripts/hexa_actions.sh"
    if [[ -x "$ACTIONS_BIN" ]]; then
        printf '%s' "$BRAIN_JSON" | jq -r '.recommend[]? // empty' 2>/dev/null | \
        while IFS= read -r rec; do
            [[ -z "$rec" ]] && continue
            "$ACTIONS_BIN" add brain "$rec" 1 >/dev/null 2>&1 || true
        done
    fi
fi

exit 0
