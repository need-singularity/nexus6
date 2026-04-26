#!/bin/bash
# beyond_omega_cycle4_force_approach.sh — nxs-20260425-004 cycle 4
#
# axis B 의 첫 positive measurement: ghost_ceiling_approach emit 의 frequency=1 만들기.
# cycle 3 finding (180s timeout invariant + DISPATCH_TERMINATED) 을 받아 들여,
# expensive cmd_chain/cmd_drill_batch/_omega_invoke_debate 본체는 timeout 으로 차단하고
# dispatch + ghost_ceiling_approach emit 만 stderr 로 capture.
#
# Safety envelope:
#   - GATE_LOCAL=1: hexa_remote 우회 (cycle 2 v3 hetzner SIGTERM chain 회피)
#   - HEXA_REMOTE_NO_REROUTE=1: route fallback chain 단축
#   - NEXUS_DRILL_DEPTH=0: drill 진입 시 즉시 zero-yield
#   - NEXUS_DRILL_BUDGET_S=1: drill budget 1s
#   - NEXUS_DRILL_HISTORY_OFF=1: drill_stage_elapsed_history.jsonl 오염 방지
#   - timeout --kill-after=3s 8s: 본 wrapper 자체에 8s + 3s grace SIGKILL
#
# emit sink: /tmp/nexus_omega_cycle4_forced.{out,err}.log

set -u
SINK_OUT=/tmp/nexus_omega_cycle4_forced.out.log
SINK_ERR=/tmp/nexus_omega_cycle4_forced.err.log
HEXA_REAL="${HEXA_REAL:-/Users/ghost/.hx/bin/hexa_real}"
NEXUS_RUN="${NEXUS_RUN:-/Users/ghost/.hx/packages/nexus/cli/run.hexa}"
[[ -f "$NEXUS_RUN" ]] || NEXUS_RUN="/Users/ghost/core/nexus/cli/run.hexa"

: > "$SINK_OUT"
: > "$SINK_ERR"

if [[ ! -x "$HEXA_REAL" ]]; then
    echo "FATAL: hexa_real not found at $HEXA_REAL" >&2
    exit 2
fi
if [[ ! -f "$NEXUS_RUN" ]]; then
    echo "FATAL: nexus run.hexa not found at $NEXUS_RUN" >&2
    exit 2
fi

# Direct hexa_real invocation bypasses ~/core/nexus/scripts/bin/hexa wrapper
# (which routes to hexa_remote). cmd_omega 진입 → axes 카운트 → dispatch+approach
# emit 발화는 dispatch 본체 (cmd_chain/cmd_drill_batch) 호출 직전에 이루어짐.
START_TS=$(date +%s)
GATE_LOCAL=1 \
HEXA_REMOTE_NO_REROUTE=1 \
HEXA_REMOTE_DISABLE=1 \
NEXUS_DRILL_DEPTH=0 \
NEXUS_DRILL_BUDGET_S=1 \
NEXUS_DRILL_HISTORY_OFF=1 \
timeout --kill-after=3s 6s \
    "$HEXA_REAL" run "$NEXUS_RUN" omega \
        --engines "hexa.real,hexa.real" \
        --variants 2 \
        --seeds "beyond-omega-c4-s1,beyond-omega-c4-s2" \
        --max-rounds 1 \
    > "$SINK_OUT" 2> "$SINK_ERR"
RC=$?
END_TS=$(date +%s)
ELAPSED=$((END_TS - START_TS))

echo "=== cycle 4 forced approach result ==="
echo "rc=$RC elapsed=${ELAPSED}s"
echo "stdout=$SINK_OUT ($(wc -l < "$SINK_OUT") lines)"
echo "stderr=$SINK_ERR ($(wc -l < "$SINK_ERR") lines)"

echo "--- NEXUS_OMEGA emits in stderr ---"
grep "NEXUS_OMEGA " "$SINK_ERR" || echo "(none)"

APPROACH_COUNT=$({ grep -c '"event":"ghost_ceiling_approach"' "$SINK_ERR" 2>/dev/null || true; } | head -n1)
DISPATCH_COUNT=$({ grep -c '"event":"dispatch"' "$SINK_ERR" 2>/dev/null || true; } | head -n1)
COMPLETE_COUNT=$({ grep -c '"event":"complete"' "$SINK_ERR" 2>/dev/null || true; } | head -n1)
APPROACH_COUNT=${APPROACH_COUNT:-0}
DISPATCH_COUNT=${DISPATCH_COUNT:-0}
COMPLETE_COUNT=${COMPLETE_COUNT:-0}
echo "--- counts ---"
echo "dispatch=$DISPATCH_COUNT approach=$APPROACH_COUNT complete=$COMPLETE_COUNT"
