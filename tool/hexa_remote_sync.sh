#!/bin/bash
# hexa_remote_sync.sh — fswatch daemon that mirrors local airgenome+nexus to ubu.
#
# Purpose: hexa_remote dispatch (shared/scripts/bin/hexa_remote) currently
# rsyncs the project root on every invocation, costing 0.1~0.5 s per call.
# This daemon keeps the remote tree warm so dispatch can set
# HEXA_REMOTE_NO_SYNC=1 and skip rsync entirely.
#
# Watched roots (exclude rules mirror hexa_remote so the live tree matches):
#   /Users/ghost/Dev/airgenome  → ubu:airgenome/
#     exclude: archive/v1/, data/, __pycache__/, .git/, *.log, .DS_Store
#   /Users/ghost/core/nexus      → ubu:Dev/nexus/
#     exclude: .git/, *.log, .DS_Store, .runtime/, shared/blowup/lens/
#
# Behaviour:
#   - Initial 1× rsync of both roots at startup (cold cache warmer).
#   - fswatch --batch-marker --latency 0.3 → coalesce bursts to ~300 ms.
#   - Per batch: parse changed paths, decide which root(s) need sync, rsync.
#   - rsync / ssh failures log to stderr and continue (daemon never dies).
#
# Manual install (after review):
#   cp /Users/ghost/core/nexus/tool/com.airgenome.hexa_remote_sync.plist \
#      ~/Library/LaunchAgents/
#   launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.airgenome.hexa_remote_sync.plist
#   launchctl enable     gui/$UID/com.airgenome.hexa_remote_sync
#   launchctl kickstart -k gui/$UID/com.airgenome.hexa_remote_sync
# Uninstall:
#   launchctl bootout gui/$UID/com.airgenome.hexa_remote_sync
#   rm ~/Library/LaunchAgents/com.airgenome.hexa_remote_sync.plist

set -u
# Intentionally NOT -e: rsync/ssh transient failures are logged and swallowed;
# any stray non-zero inside the `while read` subshell must not kill fswatch
# (previous -eu deployment hit inefficient-respawn under launchd).

HOST="${HEXA_REMOTE_HOST:-ubu}"
LATENCY="${HEXA_REMOTE_SYNC_LATENCY:-0.3}"

AIRGENOME_LOCAL="/Users/ghost/Dev/airgenome"
AIRGENOME_REMOTE="airgenome/"
AIRGENOME_EXCLUDES=(
  --exclude=archive/v1/
  --exclude=data/
  --exclude=__pycache__/
  --exclude=.git/
  --exclude='*.log'
  --exclude=.DS_Store
)

NEXUS_LOCAL="/Users/ghost/core/nexus"
NEXUS_REMOTE="Dev/nexus/"
NEXUS_EXCLUDES=(
  --exclude=.git/
  --exclude='*.log'
  --exclude=.DS_Store
  --exclude=.runtime/
  --exclude=shared/blowup/lens/
)

log()  { printf '[hexa_remote_sync] %s\n' "$*"; }
warn() { printf '[hexa_remote_sync] WARN %s\n' "$*" >&2; }

if ! command -v fswatch >/dev/null 2>&1; then
  printf '[hexa_remote_sync] FATAL fswatch not found in PATH (%s)\n' "$PATH" >&2
  printf '[hexa_remote_sync] install: brew install fswatch\n' >&2
  exit 1
fi

[ -d "$AIRGENOME_LOCAL" ] || { warn "airgenome dir missing: $AIRGENOME_LOCAL"; }
[ -d "$NEXUS_LOCAL" ]     || { warn "nexus dir missing: $NEXUS_LOCAL"; }

sync_airgenome() {
  [ -d "$AIRGENOME_LOCAL" ] || return 0
  rsync -aH "${AIRGENOME_EXCLUDES[@]}" \
    "$AIRGENOME_LOCAL/" "$HOST:$AIRGENOME_REMOTE" >/dev/null 2>&1 \
    || warn "rsync airgenome → $HOST failed (continuing)"
}

sync_nexus() {
  [ -d "$NEXUS_LOCAL" ] || return 0
  rsync -aH "${NEXUS_EXCLUDES[@]}" \
    "$NEXUS_LOCAL/" "$HOST:$NEXUS_REMOTE" >/dev/null 2>&1 \
    || warn "rsync nexus → $HOST failed (continuing)"
}

# Cold-start: warm both remote trees once so dispatch can immediately use
# HEXA_REMOTE_NO_SYNC=1 even on the very first call after daemon boot.
log "initial sync → $HOST"
sync_airgenome
sync_nexus
log "initial sync done; entering fswatch loop (latency=${LATENCY}s)"

# fswatch -0 emits NUL-terminated paths; --batch-marker NOOP separates bursts.
# We read NUL-delimited tokens; the literal string "NOOP" (default marker)
# signals "batch boundary — flush now". This collapses an N-file save into
# a single rsync pair instead of N rsyncs.
WATCH_DIRS=()
[ -d "$AIRGENOME_LOCAL" ] && WATCH_DIRS+=("$AIRGENOME_LOCAL")
[ -d "$NEXUS_LOCAL" ]     && WATCH_DIRS+=("$NEXUS_LOCAL")

if [ ${#WATCH_DIRS[@]} -eq 0 ]; then
  warn "no watch directories exist; idling"
  while :; do sleep 3600; done
fi

log "fswatch starting with dirs: ${WATCH_DIRS[*]}"
fswatch -0 --batch-marker --latency "$LATENCY" "${WATCH_DIRS[@]}" 2>&1 \
  | while IFS= read -r -d '' path; do
      # Decide which roots changed in this batch. Accumulate flags and flush
      # on the NOOP marker.
      if [ "$path" = "NOOP" ]; then
        if [ "${need_air:-0}" = "1" ]; then sync_airgenome; fi
        if [ "${need_nex:-0}" = "1" ]; then sync_nexus; fi
        need_air=0
        need_nex=0
        continue
      fi
      case "$path" in
        "$AIRGENOME_LOCAL"/*)
          # Skip noisy excluded paths early (fswatch still emits them).
          case "$path" in
            "$AIRGENOME_LOCAL"/archive/v1/*) ;;
            "$AIRGENOME_LOCAL"/data/*) ;;
            "$AIRGENOME_LOCAL"/.git/*) ;;
            *__pycache__*) ;;
            *.log) ;;
            *.DS_Store) ;;
            *) need_air=1 ;;
          esac
          ;;
        "$NEXUS_LOCAL"/*)
          case "$path" in
            "$NEXUS_LOCAL"/.git/*) ;;
            "$NEXUS_LOCAL"/.runtime/*) ;;
            "$NEXUS_LOCAL"/cli/blowup/lens/*) ;;
            *.log) ;;
            *.DS_Store) ;;
            *) need_nex=1 ;;
          esac
          ;;
      esac
    done

# fswatch should never exit; if it does, launchd KeepAlive will re-spawn us.
warn "fswatch exited; daemon will be restarted by launchd"
exit 1
