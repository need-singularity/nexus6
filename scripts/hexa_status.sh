#!/bin/bash
# hexa_status.sh — hexa-guard 전체 상태 대시보드
# 모든 tier 의 현황을 한 번에 보여줌.

set -u
NEXUS="${NEXUS:-$HOME/Dev/nexus}"
LOG_DIR="${HOME}/.airgenome"

printf '=== hexa-guard dashboard — %s ===\n\n' "$(date '+%Y-%m-%d %H:%M:%S')"

# 1) agents 상태
printf 'agents\n'
launchctl list 2>/dev/null | awk '
    /com\.airgenome\.(hexa-reflex|hexa-brain|hexa-worker|predictive-throttle|dispatch|probe|ring-sync|menubar|ceiling)/ {
        state = ($1 == "-") ? "idle"    : "run-" $1
        exit_code = $2
        label = $3
        sub(/com\.airgenome\./, "", label)
        printf "  %-20s  %-14s  last_exit=%s\n", label, state, exit_code
    }'

# 2) system vitals
printf '\nsystem\n'
load=$(uptime | sed -E 's/.*load averages?: //')
printf '  load:      %s\n' "$load"
free=$(vm_stat | awk -F: '/Pages free/{gsub(/[. ]/,"",$2); print int($2)*16384/1024/1024}')
printf '  mem free:  %.0f MB\n' "$free"

# 3) reflex 상태
printf '\nreflex (tier1)\n'
active=$(find "$LOG_DIR/hexa_reflex_state" -type f 2>/dev/null | wc -l | tr -d ' ')
printf '  tracked procs: %s\n' "$active"
recent_events=$(tail -30 "$LOG_DIR/hexa_guard.jsonl" 2>/dev/null | \
    jq -c 'select(.tier==1 and (.kind=="escalate" or .kind=="degrade"))' 2>/dev/null | wc -l | tr -d ' ')
printf '  recent 30 events (escalate+degrade): %s\n' "$recent_events"

# 4) brain 최근 판단
printf '\nbrain (tier2)\n'
last_brain=$(tail -1 "$LOG_DIR/hexa_brain.jsonl" 2>/dev/null | jq -r '.output // ""' 2>/dev/null)
if [[ -n "$last_brain" ]] && printf '%s' "$last_brain" | jq -e . >/dev/null 2>&1; then
    status=$(printf '%s' "$last_brain" | jq -r '.status // "?"')
    summary=$(printf '%s' "$last_brain" | jq -r '.summary // ""')
    rec_count=$(printf '%s' "$last_brain" | jq '.recommend | length' 2>/dev/null)
    printf '  status:    %s\n' "$status"
    printf '  summary:   %s\n' "$summary"
    printf '  recommend: %s items\n' "${rec_count:-0}"
else
    printf '  (no brain output yet)\n'
fi

# 5) queue
printf '\nqueue\n'
if [[ -x "$NEXUS/scripts/hexa_actions.sh" ]]; then
    "$NEXUS/scripts/hexa_actions.sh" count | sed 's/^/  /'
fi

# 6) dispatch policy
printf '\ndispatch policy\n'
if [[ -x "$NEXUS/scripts/hexa_dispatch_check.sh" ]]; then
    "$NEXUS/scripts/hexa_dispatch_check.sh" --human 2>/dev/null \
        | grep -E "heavy|compute|gpu|ag6_gate|VIOLATION|✓" | sed 's/^/  /'
fi

# 7) patterns
printf '\npatterns (24h)\n'
if [[ -x "$NEXUS/scripts/hexa_patterns.sh" ]]; then
    "$NEXUS/scripts/hexa_patterns.sh" brain-hint 2>/dev/null | sed 's/^/  /'
fi

# 8) pending queue snapshot
printf '\npending items\n'
if [[ -x "$NEXUS/scripts/hexa_actions.sh" ]]; then
    "$NEXUS/scripts/hexa_actions.sh" list pending 2>/dev/null | head -5 | sed 's/^/  /'
    [[ -z "$(${NEXUS}/scripts/hexa_actions.sh list pending 2>/dev/null)" ]] && printf '  (none)\n'
fi

echo
