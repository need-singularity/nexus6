#!/usr/bin/env bash
# tool/falsifier_health.sh — falsifier registry health check (cron-friendly)
#
# Iterate F1..F30 from design/hexa_sim/falsifiers.jsonl, time + execute each cmd,
# classify CLEAN (sentinel + ec=0) / HIT (no sentinel, ec=0) / ERROR (ec!=0).
# Append timeline JSONL line to state/atlas_health_timeline.jsonl.
#
# usage:
#   tool/falsifier_health.sh           # human-readable + sentinel + timeline append
#   tool/falsifier_health.sh --quiet   # only sentinel line on stdout
#   tool/falsifier_health.sh --json    # JSONL summary on stdout (no timeline append)
#
# Exit:
#   0 if all CLEAN
#   76 if any HIT/ERROR (raw 23 schema-guard analog)
#   1 on usage / registry-missing
#
# Sentinel (raw 80):
#   __FALSIFIER_HEALTH__ <PASS|WARN|FAIL> total=N clean=C hit=H error=E duration_ms=T
#
# Compliance: raw 66 (reason+fix trailers) + raw 71 (report-only, never auto-mutate)
#             + raw 77 (read-only over registry) + raw 80 (sentinel)
# Origin: design/hexa_sim/2026-04-26_falsifier_health_check.md (productionised runner)

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$HOME/core/nexus}"
REGISTRY="${FALSIFIER_REGISTRY:-$NEXUS_ROOT/design/hexa_sim/falsifiers.jsonl}"
TIMELINE="${ATLAS_HEALTH_TIMELINE:-$NEXUS_ROOT/state/atlas_health_timeline.jsonl}"

QUIET=0
JSON=0

while [ $# -gt 0 ]; do
    case "$1" in
        --quiet) QUIET=1; shift ;;
        --json)  JSON=1; shift ;;
        --help|-h)
            sed -n '3,30p' "$0"
            exit 0
            ;;
        *)
            echo "usage error: unknown flag: $1" >&2
            echo "  reason: unrecognised CLI argument" >&2
            echo "  fix:    use --quiet | --json | --help" >&2
            exit 1
            ;;
    esac
done

if [ ! -f "$REGISTRY" ]; then
    echo "error: falsifier registry not found at $REGISTRY" >&2
    echo "  reason: FALSIFIER_REGISTRY env or default path missing" >&2
    echo "  fix:    set FALSIFIER_REGISTRY=/path/to/falsifiers.jsonl" >&2
    exit 1
fi

NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
TMP_TSV="$(mktemp -t falsifier_health.XXXXXX)"
trap 'rm -f "$TMP_TSV"' EXIT

if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
    echo "═══ FALSIFIER HEALTH — $NOW (UTC)"
    echo "registry: $REGISTRY"
fi

TOTAL=0; CLEAN=0; HIT=0; ERROR=0
WALL_START=$(date +%s)

# Iterate registry. Per memory feedback_hexa_sim_falsifier_parser_quirks.md,
# extract cmd safely with python3 (sed regex patterns are fragile).
while IFS= read -r line; do
    [ -z "$line" ] && continue
    # extract id, slug, cmd, pass via python3 — single invocation per line
    META=$(printf '%s' "$line" | python3 -c '
import json, sys
d = json.loads(sys.stdin.read())
print(d.get("id",""))
print(d.get("slug",""))
print(d.get("pass",""))
print(d.get("cmd",""))
' 2>/dev/null) || { ERROR=$((ERROR+1)); TOTAL=$((TOTAL+1)); continue; }
    FID=$(printf '%s\n' "$META" | sed -n '1p')
    SLUG=$(printf '%s\n' "$META" | sed -n '2p')
    PASS_TOKEN=$(printf '%s\n' "$META" | sed -n '3p')
    CMD=$(printf '%s\n' "$META" | sed -n '4,$p')
    [ -z "$FID" ] && continue
    TOTAL=$((TOTAL+1))
    T0=$(date +%s%N 2>/dev/null || python3 -c 'import time;print(int(time.time()*1e9))')
    OUT=$(eval "$CMD" 2>&1); EC=$?
    T1=$(date +%s%N 2>/dev/null || python3 -c 'import time;print(int(time.time()*1e9))')
    DUR_MS=$(( (T1 - T0) / 1000000 ))
    STATUS="ERROR"
    if [ "$EC" = "0" ]; then
        if [ -n "$PASS_TOKEN" ] && printf '%s' "$OUT" | grep -qF "$PASS_TOKEN"; then
            STATUS="CLEAN"; CLEAN=$((CLEAN+1))
        else
            STATUS="HIT"; HIT=$((HIT+1))
        fi
    else
        ERROR=$((ERROR+1))
    fi
    printf '%s\t%s\t%s\t%s\t%s\n' "$FID" "$SLUG" "$STATUS" "$EC" "$DUR_MS" >>"$TMP_TSV"
    if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
        printf '  %-4s  %-50s  %-5s  ec=%-3s  %6sms\n' "$FID" "$SLUG" "$STATUS" "$EC" "$DUR_MS"
    fi
done < "$REGISTRY"

WALL_END=$(date +%s)
DURATION_MS=$(( (WALL_END - WALL_START) * 1000 ))

VERDICT="PASS"
EXIT_CODE=0
if [ "$ERROR" -gt 0 ] || [ "$HIT" -gt 0 ]; then
    VERDICT="FAIL"
    EXIT_CODE=76
fi

JSONL_LINE=$(printf '{"ts":"%s","scope":"falsifier_registry","total":%d,"clean":%d,"hit":%d,"error":%d,"duration_ms":%d,"checker":"falsifier_health.sh"}' \
    "$NOW" "$TOTAL" "$CLEAN" "$HIT" "$ERROR" "$DURATION_MS")

if [ "$JSON" = "1" ]; then
    printf '%s\n' "$JSONL_LINE"
else
    printf '%s\n' "$JSONL_LINE" >> "$TIMELINE"
fi

if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
    echo "─── summary"
    printf '  total=%d  clean=%d  hit=%d  error=%d  wall=%dms\n' "$TOTAL" "$CLEAN" "$HIT" "$ERROR" "$DURATION_MS"
    if [ "$EXIT_CODE" = "76" ]; then
        echo "  reason: $HIT HIT + $ERROR ERROR — see TSV above for per-id breakdown"
        echo "  fix:    re-run failing F# with verbose output; consult design/hexa_sim/falsifiers.jsonl 'fix' field"
    fi
fi

echo "__FALSIFIER_HEALTH__ $VERDICT total=$TOTAL clean=$CLEAN hit=$HIT error=$ERROR duration_ms=$DURATION_MS"
exit $EXIT_CODE
