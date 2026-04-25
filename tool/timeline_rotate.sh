#!/usr/bin/env bash
# tool/timeline_rotate.sh — atlas_health_timeline.jsonl size-threshold rotator (2026-04-26)
#
# Policy B (default): rotate when line count exceeds threshold (default 5000 ≈ 500 KB typical).
# Old file moves to state/atlas_health_timeline.<UTC_ISO>.jsonl.archive, new empty file is touched,
# rotation event logged single-line in state/atlas_health_timeline.rotation.log.
#
# usage:
#   tool/timeline_rotate.sh                  # rotate if over threshold
#   tool/timeline_rotate.sh --check          # dry-run (no FS mutation)
#   tool/timeline_rotate.sh --threshold N    # custom threshold (lines)
#
# sentinel: __TIMELINE_ROTATE__ <ROTATED|SKIPPED|ERROR> threshold=N current=L action=...
# raw 73 admissibility (≤100 lines bash 3.2); raw 80 sentinel; raw 66 reason+fix on error.
# DO NOT auto-run; user invokes (or wires to launchd/cron after review).

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
TIMELINE="$NEXUS_ROOT/state/atlas_health_timeline.jsonl"
ROTATION_LOG="$NEXUS_ROOT/state/atlas_health_timeline.rotation.log"

THRESHOLD=5000
MODE="rotate"

while [ $# -gt 0 ]; do
    case "$1" in
        --check) MODE="check"; shift ;;
        --threshold)
            shift
            if [ $# -eq 0 ] || ! printf '%s' "$1" | grep -qE '^[0-9]+$'; then
                echo "timeline_rotate: --threshold needs positive int (reason: missing/non-numeric; fix: --threshold 5000)" >&2
                echo "__TIMELINE_ROTATE__ ERROR threshold=invalid current=0 action=usage"; exit 1
            fi
            THRESHOLD="$1"; shift ;;
        --help|-h)
            echo "usage: $0 [--check] [--threshold N]  (default N=5000; --check = dry-run)"; exit 0 ;;
        *)
            echo "timeline_rotate: unknown arg '$1' (reason: only --check/--threshold/--help; fix: $0 --help)" >&2
            echo "__TIMELINE_ROTATE__ ERROR threshold=$THRESHOLD current=0 action=unknown_arg"; exit 1 ;;
    esac
done

if [ ! -f "$TIMELINE" ]; then
    echo "timeline_rotate: timeline file not found at $TIMELINE" >&2
    echo "  reason: state/atlas_health_timeline.jsonl missing" >&2
    echo "  fix: run health checks first (falsifier_health.sh / bridge_health.sh) to seed it" >&2
    echo "__TIMELINE_ROTATE__ SKIPPED threshold=$THRESHOLD current=0 action=no_file"
    exit 0
fi

CURRENT=$(wc -l < "$TIMELINE" | tr -d ' ')
[ -z "$CURRENT" ] && CURRENT=0

NOW_ISO=$(date -u +%Y-%m-%dT%H:%M:%SZ)
NOW_FS=$(date -u +%Y%m%dT%H%M%SZ)
ARCHIVE="$NEXUS_ROOT/state/atlas_health_timeline.$NOW_FS.jsonl.archive"

if [ "$CURRENT" -le "$THRESHOLD" ]; then
    echo "timeline_rotate: $CURRENT lines ≤ $THRESHOLD threshold — no rotation needed"
    echo "__TIMELINE_ROTATE__ SKIPPED threshold=$THRESHOLD current=$CURRENT action=under_threshold"
    exit 0
fi

if [ "$MODE" = "check" ]; then
    echo "timeline_rotate: [DRY-RUN] would rotate $CURRENT lines → $ARCHIVE"
    echo "__TIMELINE_ROTATE__ SKIPPED threshold=$THRESHOLD current=$CURRENT action=dry_run_would_rotate"
    exit 0
fi

if ! mv "$TIMELINE" "$ARCHIVE" 2>/dev/null; then
    echo "timeline_rotate: mv failed $TIMELINE → $ARCHIVE" >&2
    echo "  reason: filesystem permission denied or destination exists" >&2
    echo "  fix: check write permission on state/, ensure no archive collision (re-run after 1s)" >&2
    echo "__TIMELINE_ROTATE__ ERROR threshold=$THRESHOLD current=$CURRENT action=mv_failed"
    exit 1
fi

if ! : > "$TIMELINE" 2>/dev/null; then
    echo "timeline_rotate: failed to recreate empty $TIMELINE" >&2
    echo "  reason: cannot truncate-create successor file after archive" >&2
    echo "  fix: manually 'touch $TIMELINE' (archive already moved to $ARCHIVE)" >&2
    echo "__TIMELINE_ROTATE__ ERROR threshold=$THRESHOLD current=$CURRENT action=touch_failed"
    exit 1
fi

ARCHIVE_BASENAME=$(basename "$ARCHIVE")
echo "{\"ts\":\"$NOW_ISO\",\"old_lines\":$CURRENT,\"threshold\":$THRESHOLD,\"archive\":\"$ARCHIVE_BASENAME\"}" >> "$ROTATION_LOG"

echo "timeline_rotate: rotated $CURRENT lines → $ARCHIVE_BASENAME (new empty timeline at $TIMELINE)"
echo "__TIMELINE_ROTATE__ ROTATED threshold=$THRESHOLD current=$CURRENT action=archived archive=$ARCHIVE_BASENAME"
exit 0
