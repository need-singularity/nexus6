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
#   tool/falsifier_health.sh --strict  # also verify registry SHA256 against pinned baseline
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
# R1 (cmd_sha256 per-entry): each entry carries a 16-hex SHA256 prefix of its cmd;
#   recomputed at runtime — mismatch → STATUS=TAMPERED (counts as ERROR).
#   Defeats silent-corruption beyond R2 anti-spoof lint (which only catches the
#   exact `echo $TOKEN` pattern; R1 catches printf, conditional-and-echo, etc.).
# Origin: design/hexa_sim/2026-04-26_falsifier_health_check.md (productionised runner)

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$HOME/core/nexus}"
REGISTRY="${FALSIFIER_REGISTRY:-$NEXUS_ROOT/design/hexa_sim/falsifiers.jsonl}"
TIMELINE="${ATLAS_HEALTH_TIMELINE:-$NEXUS_ROOT/state/atlas_health_timeline.jsonl}"
REGISTRY_BASELINE="${FALSIFIER_REGISTRY_BASELINE:-$NEXUS_ROOT/state/falsifier_registry.sha256}"

QUIET=0
JSON=0
STRICT=0

while [ $# -gt 0 ]; do
    case "$1" in
        --quiet)  QUIET=1; shift ;;
        --json)   JSON=1; shift ;;
        --strict) STRICT=1; shift ;;
        --help|-h)
            sed -n '3,30p' "$0"
            exit 0
            ;;
        *)
            echo "usage error: unknown flag: $1" >&2
            echo "  reason: unrecognised CLI argument" >&2
            echo "  fix:    use --quiet | --json | --strict | --help" >&2
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

# R3 lite: optional --strict mode — verify whole-registry SHA256 against pinned baseline.
# Warns (not fails) by default since additive entries (raw 77) legitimately rotate the hash.
if [ "$STRICT" = "1" ]; then
    if [ ! -f "$REGISTRY_BASELINE" ]; then
        echo "warning: --strict requested but baseline not found at $REGISTRY_BASELINE" >&2
        echo "  reason: registry baseline file missing" >&2
        echo "  fix:    sha256sum \"$REGISTRY\" | awk '{print \$1}' > \"$REGISTRY_BASELINE\"" >&2
    else
        BASELINE_HASH=$(awk '{print $1}' "$REGISTRY_BASELINE" 2>/dev/null)
        CURRENT_HASH=$(shasum -a 256 "$REGISTRY" 2>/dev/null | awk '{print $1}')
        [ -z "$CURRENT_HASH" ] && CURRENT_HASH=$(sha256sum "$REGISTRY" 2>/dev/null | awk '{print $1}')
        if [ "$BASELINE_HASH" != "$CURRENT_HASH" ]; then
            echo "warning: registry SHA256 drift vs baseline" >&2
            echo "  baseline: $BASELINE_HASH" >&2
            echo "  current:  $CURRENT_HASH" >&2
            echo "  reason: registry mutated since baseline pin" >&2
            echo "  fix:    audit git log of $REGISTRY; if intended, refresh baseline" >&2
        fi
    fi
fi

# Helper: SHA256 of a string (first 16 hex chars). Tries shasum (BSD) then sha256sum (GNU).
sha256_16() {
    local _h
    _h=$(printf '%s' "$1" | shasum -a 256 2>/dev/null | awk '{print $1}')
    [ -z "$_h" ] && _h=$(printf '%s' "$1" | sha256sum 2>/dev/null | awk '{print $1}')
    printf '%s' "${_h:0:16}"
}

NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
TMP_TSV="$(mktemp -t falsifier_health.XXXXXX)"
trap 'rm -f "$TMP_TSV"' EXIT

if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
    echo "═══ FALSIFIER HEALTH — $NOW (UTC)"
    echo "registry: $REGISTRY"
fi

TOTAL=0; CLEAN=0; HIT=0; ERROR=0; TAMPERED=0
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
print(d.get("cmd_sha256",""))
print(d.get("cmd",""))
' 2>/dev/null) || { ERROR=$((ERROR+1)); TOTAL=$((TOTAL+1)); continue; }
    FID=$(printf '%s\n' "$META" | sed -n '1p')
    SLUG=$(printf '%s\n' "$META" | sed -n '2p')
    PASS_TOKEN=$(printf '%s\n' "$META" | sed -n '3p')
    CMD_SHA256_DECL=$(printf '%s\n' "$META" | sed -n '4p')
    CMD=$(printf '%s\n' "$META" | sed -n '5,$p')
    [ -z "$FID" ] && continue
    TOTAL=$((TOTAL+1))
    # R1 cmd_sha256 verification — recompute hash of cmd; mismatch → TAMPERED
    # Defeats silent-corruption beyond R2 lint (printf, conditional-and-echo, etc.)
    if [ -n "$CMD_SHA256_DECL" ]; then
        CMD_SHA256_LIVE=$(sha256_16 "$CMD")
        if [ "$CMD_SHA256_LIVE" != "$CMD_SHA256_DECL" ]; then
            STATUS="TAMPERED"; TAMPERED=$((TAMPERED+1)); ERROR=$((ERROR+1))
            printf '%s\t%s\t%s\t%s\t%s\n' "$FID" "$SLUG" "$STATUS" "tampered" "0" >>"$TMP_TSV"
            if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
                printf '  %-4s  %-50s  %-8s  reason=cmd_sha256_mismatch  fix=audit_registry_history  declared=%s  live=%s\n' \
                    "$FID" "$SLUG" "$STATUS" "$CMD_SHA256_DECL" "$CMD_SHA256_LIVE"
            fi
            continue
        fi
    fi
    # R2 anti-spoof lint: reject cmds that just `echo $TOKEN` (silent-corruption defense)
    # Pattern: trimmed cmd matches `^echo [A-Z][A-Z0-9_]*$` exactly — that's a spoof signature
    CMD_TRIMMED=$(printf '%s' "$CMD" | tr -d '[:space:]')
    if printf '%s' "$CMD_TRIMMED" | grep -qE '^echo[A-Z][A-Z0-9_]*$'; then
        STATUS="SPOOF"; ERROR=$((ERROR+1))
        printf '%s\t%s\t%s\t%s\t%s\n' "$FID" "$SLUG" "$STATUS" "spoof" "0" >>"$TMP_TSV"
        if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
            printf '  %-4s  %-50s  %-8s  reason=anti_spoof_lint  fix=audit_cmd_origin\n' "$FID" "$SLUG" "$STATUS"
        fi
        continue
    fi
    T0=$(date +%s%N 2>/dev/null || python3 -c 'import time;print(int(time.time()*1e9))')
    OUT=$(eval "$CMD" 2>&1); EC=$?
    T1=$(date +%s%N 2>/dev/null || python3 -c 'import time;print(int(time.time()*1e9))')
    DUR_MS=$(( (T1 - T0) / 1000000 ))
    # Status disambiguation (Ω-cycle 2026-04-26 health_check_status_disambiguation):
    #   ec=0 + sentinel match  → CLEAN  (anchor present, falsifier silent)
    #   ec=0 + no sentinel     → HIT    (cmd ran but expected sentinel absent)
    #   ec=1 + grep-style cmd  → HIT    (grep miss / negated grep hit short-circuited
    #                                    before sentinel echo — falsifier IS firing,
    #                                    NOT a true error). Pattern detected by
    #                                    presence of `grep -q[EF]?` token in CMD.
    #   ec=2                   → ERROR  (grep regex syntax error — true cmd fault)
    #   ec≠0,1,2               → ERROR  (file-not-found, syntax error, OOM, etc.)
    # Heuristic non-trivial (raw 73): ec=1 alone does NOT imply HIT — must also
    # match grep-style cmd pattern. Other ec=1 sources (e.g. `test`/`[`, generic
    # boolean false, bare `[ ! -f ]`) still classify as ERROR until proven safe.
    STATUS="ERROR"
    if [ "$EC" = "0" ]; then
        if [ -n "$PASS_TOKEN" ] && printf '%s' "$OUT" | grep -qF "$PASS_TOKEN"; then
            STATUS="CLEAN"; CLEAN=$((CLEAN+1))
        else
            STATUS="HIT"; HIT=$((HIT+1))
        fi
    elif [ "$EC" = "1" ] && printf '%s' "$CMD" | grep -qE 'grep -q(E|F)?[[:space:]]'; then
        # grep-style HIT-via-shortcircuit (raw 66 reason+fix trailer attached)
        STATUS="HIT"; HIT=$((HIT+1))
    else
        ERROR=$((ERROR+1))
    fi
    printf '%s\t%s\t%s\t%s\t%s\n' "$FID" "$SLUG" "$STATUS" "$EC" "$DUR_MS" >>"$TMP_TSV"
    if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
        if [ "$STATUS" = "HIT" ] && [ "$EC" = "1" ]; then
            printf '  %-4s  %-50s  %-8s  ec=%-3s  %6sms  reason=anchor_grep_miss  fix=audit_atlas_for_drift\n' "$FID" "$SLUG" "$STATUS" "$EC" "$DUR_MS"
        else
            printf '  %-4s  %-50s  %-8s  ec=%-3s  %6sms\n' "$FID" "$SLUG" "$STATUS" "$EC" "$DUR_MS"
        fi
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

JSONL_LINE=$(printf '{"ts":"%s","scope":"falsifier_registry","total":%d,"clean":%d,"hit":%d,"error":%d,"tampered":%d,"duration_ms":%d,"checker":"falsifier_health.sh"}' \
    "$NOW" "$TOTAL" "$CLEAN" "$HIT" "$ERROR" "$TAMPERED" "$DURATION_MS")

if [ "$JSON" = "1" ]; then
    printf '%s\n' "$JSONL_LINE"
else
    printf '%s\n' "$JSONL_LINE" >> "$TIMELINE"
fi

if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
    echo "─── summary"
    printf '  total=%d  clean=%d  hit=%d  error=%d  tampered=%d  wall=%dms\n' "$TOTAL" "$CLEAN" "$HIT" "$ERROR" "$TAMPERED" "$DURATION_MS"
    if [ "$EXIT_CODE" = "76" ]; then
        echo "  reason: $HIT HIT + $ERROR ERROR ($TAMPERED TAMPERED) — see TSV above for per-id breakdown"
        echo "  fix:    re-run failing F# with verbose output; consult design/hexa_sim/falsifiers.jsonl 'fix' field"
    fi
fi

echo "__FALSIFIER_HEALTH__ $VERDICT total=$TOTAL clean=$CLEAN hit=$HIT error=$ERROR tampered=$TAMPERED duration_ms=$DURATION_MS"
exit $EXIT_CODE
