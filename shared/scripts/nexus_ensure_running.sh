#!/usr/bin/env bash
# Ensure NEXUS-6 growth daemon is running
# Called from any TECS-L repo via .shared/ symlink
# Safe to call repeatedly (idempotent)
# Silent on success, silent on failure (never blocks caller)

NEXUS_SCRIPTS="/Users/ghost/Dev/n6-architecture/tools/nexus/scripts"
NEXUS_STATE="$HOME/.nexus"

# Quick exit if scripts don't exist
[[ -d "$NEXUS_SCRIPTS" ]] || exit 0

# Quick check: is it already running via PID file?
if [[ -f "$NEXUS_STATE/daemon.pid" ]]; then
    pid=$(cat "$NEXUS_STATE/daemon.pid" 2>/dev/null)
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        exit 0  # Already running
    fi
fi

# Check if a daemon process exists (no PID file but running)
if pgrep -f "nexus_growth_daemon" >/dev/null 2>&1; then
    exit 0  # Running without PID file
fi

# Check last activity — if recent, don't restart
if [[ -f "$NEXUS_STATE/growth_log.jsonl" ]]; then
    last_mod=$(stat -f %m "$NEXUS_STATE/growth_log.jsonl" 2>/dev/null || echo "0")
    now=$(date +%s)
    age=$(( now - last_mod ))
    if [[ $age -lt 3600 ]]; then
        exit 0  # Active within last hour
    fi
fi

# Also check the scripts-local log
if [[ -f "$NEXUS_SCRIPTS/growth_log.jsonl" ]]; then
    last_mod=$(stat -f %m "$NEXUS_SCRIPTS/growth_log.jsonl" 2>/dev/null || echo "0")
    now=$(date +%s)
    age=$(( now - last_mod ))
    if [[ $age -lt 3600 ]]; then
        exit 0  # Active within last hour
    fi
fi

# Not running — delegate to health_check with auto-start
if [[ -f "$NEXUS_SCRIPTS/health_check.sh" ]]; then
    bash "$NEXUS_SCRIPTS/health_check.sh" --start-if-dead --quiet &
fi

exit 0
