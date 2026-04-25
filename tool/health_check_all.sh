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
# Sentinel (raw 80 — additive only):
#   __HEALTH_CHECK_ALL__ <PASS|FAIL> falsifier=C/T bridge=P/T tampered=Ft+Bt status=ok|fail ledger=<status>(N) bridge_ledger=<status>(N)
#   (Ft = falsifier tampered count, Bt = bridge tampered count — R1 propagation;
#    ledger = R5 falsifier-registry hash-chain status (PASS|FAIL|EMPTY|PRE_R5) with entry count;
#    bridge_ledger = R5 bridge_sha256 hash-chain status — chain extension Ω-cycle 2026-04-26)
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
# FALSIFIER_HEALTH_TOOL env (default = parallel; set to falsifier_health.sh for legacy
# sequential fallback) — Ω-cycle 2026-04-26 falsifier_health_parallelize.
FALSIFIER_HEALTH_TOOL="${FALSIFIER_HEALTH_TOOL:-falsifier_health_parallel.sh}"
if [ ! -f "$TOOL_DIR/$FALSIFIER_HEALTH_TOOL" ]; then
    # Safety: fall back to sequential if requested tool missing
    FALSIFIER_HEALTH_TOOL="falsifier_health.sh"
fi
F_OUT=$(bash "$TOOL_DIR/$FALSIFIER_HEALTH_TOOL" --quiet 2>&1); F_EC=$?
F_LINE=$(printf '%s\n' "$F_OUT" | grep '__FALSIFIER_HEALTH__' | tail -1)
F_TOTAL=$(printf '%s' "$F_LINE" | sed -nE 's/.*total=([0-9]+).*/\1/p'); F_TOTAL=${F_TOTAL:-0}
F_CLEAN=$(printf '%s' "$F_LINE" | sed -nE 's/.*clean=([0-9]+).*/\1/p'); F_CLEAN=${F_CLEAN:-0}
F_TAMP=$(printf '%s' "$F_LINE"  | sed -nE 's/.*tampered=([0-9]+).*/\1/p'); F_TAMP=${F_TAMP:-0}

B_OUT=$(bash "$TOOL_DIR/bridge_health.sh" --quiet 2>&1); B_EC=$?
B_LINE=$(printf '%s\n' "$B_OUT" | grep '__BRIDGE_HEALTH__' | tail -1)
B_TOTAL=$(printf '%s' "$B_LINE" | sed -nE 's/.*total=([0-9]+).*/\1/p'); B_TOTAL=${B_TOTAL:-0}
B_PASS=$(printf '%s' "$B_LINE" | sed -nE 's/.*pass=([0-9]+).*/\1/p'); B_PASS=${B_PASS:-0}
B_TAMP=$(printf '%s' "$B_LINE" | sed -nE 's/.*tampered=([0-9]+).*/\1/p'); B_TAMP=${B_TAMP:-0}
TAMP_TOTAL=$((F_TAMP + B_TAMP))

S_OUT=$(bash "$TOOL_DIR/atlas_status_all.sh" --brief 2>&1); S_EC=$?
S_LINE=$(printf '%s\n' "$S_OUT" | grep '__ATLAS_STATUS_ALL__' | tail -1)
S_STATE="ok"
[ "$S_EC" != "0" ] && S_STATE="fail"

# 4th subcheck: R5 ledger_verify (hash-chain integrity of falsifier rotation ledger)
L_STATUS="MISSING"; L_ENTRIES=0; L_EC=0
if [ -f "$TOOL_DIR/ledger_verify.sh" ]; then
    L_OUT=$(bash "$TOOL_DIR/ledger_verify.sh" --quiet 2>&1); L_EC=$?
    L_LINE=$(printf '%s\n' "$L_OUT" | grep '__LEDGER_VERIFY__' | tail -1)
    L_STATUS=$(printf '%s' "$L_LINE" | awk '{print $2}')
    [ -z "$L_STATUS" ] && L_STATUS="UNKNOWN"
    L_ENTRIES=$(printf '%s' "$L_LINE" | sed -nE 's/.*entries=([0-9]+).*/\1/p')
    [ -z "$L_ENTRIES" ] && L_ENTRIES=0
fi

# 5th subcheck: R5 bridge_ledger_verify (chain extension to bridge_sha256 — Ω-cycle 2026-04-26)
BL_STATUS="MISSING"; BL_ENTRIES=0; BL_EC=0
if [ -f "$TOOL_DIR/ledger_verify.sh" ]; then
    BL_OUT=$(bash "$TOOL_DIR/ledger_verify.sh" --ledger bridge --quiet 2>&1); BL_EC=$?
    BL_LINE=$(printf '%s\n' "$BL_OUT" | grep '__LEDGER_VERIFY__' | tail -1)
    BL_STATUS=$(printf '%s' "$BL_LINE" | awk '{print $2}')
    [ -z "$BL_STATUS" ] && BL_STATUS="UNKNOWN"
    BL_ENTRIES=$(printf '%s' "$BL_LINE" | sed -nE 's/.*entries=([0-9]+).*/\1/p')
    [ -z "$BL_ENTRIES" ] && BL_ENTRIES=0
fi

VERDICT="PASS"
EXIT_CODE=0
if [ "$F_EC" != "0" ] || [ "$B_EC" != "0" ] || [ "$S_EC" != "0" ] || [ "$L_EC" != "0" ] || [ "$BL_EC" != "0" ]; then
    VERDICT="FAIL"
    EXIT_CODE=76
fi

if [ "$QUIET" = "0" ]; then
    printf 'F: %d/%d CLEAN | B: %d/%d PASS | tampered=%d (F=%d B=%d) | S: status_all_%s | L: %s(%d) | BL: %s(%d)\n' \
        "$F_CLEAN" "$F_TOTAL" "$B_PASS" "$B_TOTAL" "$TAMP_TOTAL" "$F_TAMP" "$B_TAMP" "$S_STATE" "$L_STATUS" "$L_ENTRIES" "$BL_STATUS" "$BL_ENTRIES"
    if [ "$EXIT_CODE" = "76" ]; then
        echo "  reason: subcheck failure (falsifier_ec=$F_EC bridge_ec=$B_EC status_ec=$S_EC ledger_ec=$L_EC bridge_ledger_ec=$BL_EC tampered=$TAMP_TOTAL)"
        echo "  fix:    bash $TOOL_DIR/falsifier_health.sh ; bash $TOOL_DIR/bridge_health.sh ; bash $TOOL_DIR/atlas_status_all.sh --full ; bash $TOOL_DIR/ledger_verify.sh ; bash $TOOL_DIR/ledger_verify.sh --ledger bridge"
        if [ "$TAMP_TOTAL" -gt 0 ]; then
            echo "  fix:    R1 tamper detected — audit git log of mutated files; refresh baseline if intended"
        fi
        if [ "$L_EC" != "0" ]; then
            echo "  fix:    R5 ledger chain broken — see ledger_verify output for broken_at line; investigate prev_hash mismatch"
        fi
        if [ "$BL_EC" != "0" ]; then
            echo "  fix:    R5 bridge ledger chain broken — investigate state/bridge_sha256_rotation_log.jsonl prev_hash mismatch"
        fi
    fi
fi

echo "__HEALTH_CHECK_ALL__ $VERDICT falsifier=$F_CLEAN/$F_TOTAL bridge=$B_PASS/$B_TOTAL tampered=$TAMP_TOTAL status=$S_STATE ledger=$L_STATUS($L_ENTRIES) bridge_ledger=$BL_STATUS($BL_ENTRIES)"
exit $EXIT_CODE
