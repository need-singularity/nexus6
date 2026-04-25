#!/usr/bin/env bash
# tool/health_check_all.sh — single cron-friendly wrapper
#
# Invoke falsifier_health.sh + bridge_health.sh + atlas_status_all.sh in sequence.
# Aggregate one-line status for cron logs; full detail in
# state/atlas_health_timeline.jsonl (each subcheck appends its own JSONL).
#
# usage:
#   tool/health_check_all.sh           # compact + sentinel + per-subcheck timeline
#   tool/health_check_all.sh --quiet   # only the wrapper sentinel
#
# Exit:
#   0 if all green
#   76 if any subcheck FAIL
#
# Sentinel (raw 80):
#   __HEALTH_CHECK_ALL__ <PASS|FAIL> falsifier=C/T bridge=P/T status=ok|fail
#
# Compliance: raw 66 + raw 71 + raw 80
# Origin: design/hexa_sim/2026-04-26_health_check_productionization_omega_cycle.json

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$HOME/core/nexus}"
TOOL_DIR="$NEXUS_ROOT/tool"

QUIET=0
case "${1:-}" in
    --quiet) QUIET=1 ;;
    --help|-h) sed -n '3,22p' "$0"; exit 0 ;;
    "") ;;
    *)
        echo "usage error: unknown flag: $1" >&2
        echo "  reason: unrecognised CLI argument" >&2
        echo "  fix:    use --quiet | --help" >&2
        exit 1
        ;;
esac

# Run each subcheck quietly (it appends its own timeline + emits its own sentinel).
F_OUT=$(bash "$TOOL_DIR/falsifier_health.sh" --quiet 2>&1); F_EC=$?
F_LINE=$(printf '%s\n' "$F_OUT" | grep '__FALSIFIER_HEALTH__' | tail -1)
F_TOTAL=$(printf '%s' "$F_LINE" | sed -nE 's/.*total=([0-9]+).*/\1/p'); F_TOTAL=${F_TOTAL:-0}
F_CLEAN=$(printf '%s' "$F_LINE" | sed -nE 's/.*clean=([0-9]+).*/\1/p'); F_CLEAN=${F_CLEAN:-0}

B_OUT=$(bash "$TOOL_DIR/bridge_health.sh" --quiet 2>&1); B_EC=$?
B_LINE=$(printf '%s\n' "$B_OUT" | grep '__BRIDGE_HEALTH__' | tail -1)
B_TOTAL=$(printf '%s' "$B_LINE" | sed -nE 's/.*total=([0-9]+).*/\1/p'); B_TOTAL=${B_TOTAL:-0}
B_PASS=$(printf '%s' "$B_LINE" | sed -nE 's/.*pass=([0-9]+).*/\1/p'); B_PASS=${B_PASS:-0}

S_OUT=$(bash "$TOOL_DIR/atlas_status_all.sh" --brief 2>&1); S_EC=$?
S_LINE=$(printf '%s\n' "$S_OUT" | grep '__ATLAS_STATUS_ALL__' | tail -1)
S_STATE="ok"
[ "$S_EC" != "0" ] && S_STATE="fail"

VERDICT="PASS"
EXIT_CODE=0
if [ "$F_EC" != "0" ] || [ "$B_EC" != "0" ] || [ "$S_EC" != "0" ]; then
    VERDICT="FAIL"
    EXIT_CODE=76
fi

if [ "$QUIET" = "0" ]; then
    printf 'F: %d/%d CLEAN | B: %d/%d PASS | S: status_all_%s\n' \
        "$F_CLEAN" "$F_TOTAL" "$B_PASS" "$B_TOTAL" "$S_STATE"
    if [ "$EXIT_CODE" = "76" ]; then
        echo "  reason: subcheck failure (falsifier_ec=$F_EC bridge_ec=$B_EC status_ec=$S_EC)"
        echo "  fix:    bash $TOOL_DIR/falsifier_health.sh ; bash $TOOL_DIR/bridge_health.sh ; bash $TOOL_DIR/atlas_status_all.sh --full"
    fi
fi

echo "__HEALTH_CHECK_ALL__ $VERDICT falsifier=$F_CLEAN/$F_TOTAL bridge=$B_PASS/$B_TOTAL status=$S_STATE"
exit $EXIT_CODE
