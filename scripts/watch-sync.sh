#!/usr/bin/env bash
# watch-sync.sh — git push 감지 → 즉시 sync 트리거
# Usage: ./scripts/watch-sync.sh [--daemon]
# 요구: fswatch (brew install fswatch)

set -euo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$HOME/Dev/nexus}"
LOG="$HOME/Library/Logs/nexus/watch-sync.log"
mkdir -p "$(dirname "$LOG")"

WATCH_DIRS=""
for d in "$HOME"/Dev/*/; do
    [ -d "$d/.git" ] || continue
    WATCH_DIRS="$WATCH_DIRS $d/.git/refs/heads"
done

log() { echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG"; }

log "🔭 Watch-Sync 시작 ($(echo $WATCH_DIRS | wc -w | tr -d ' ')개 프로젝트)"

if ! command -v fswatch &>/dev/null; then
    log "fswatch 없음 — 폴백: 60초 폴링 모드"
    while true; do
        bash "$NEXUS_ROOT/sync/sync-all.sh" >> "$LOG" 2>&1 || true
        sleep 60
    done
else
    fswatch -o $WATCH_DIRS | while read -r _; do
        log "📡 변경 감지 → sync 트리거"
        bash "$NEXUS_ROOT/sync/sync-all.sh" >> "$LOG" 2>&1 || true
        # nexus-bridge notify
        /usr/bin/python3 "$NEXUS_ROOT/nexus-bridge.py" sync 2>/dev/null || true
        log "✅ sync 완료"
    done
fi
