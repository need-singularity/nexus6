#!/usr/bin/env bash
# watch-remote.sh — inotifywait/fswatch 기반 변경 감지 → sync-remote 트리거
# Usage: bash sync/watch-remote.sh [htz|vast|all]
# macOS: fswatch, Linux: inotifywait
set -euo pipefail

SYNC_DIR="$(cd "$(dirname "$0")" && pwd)"
SHARED="$(cd "$SYNC_DIR/../shared" && pwd)"
TARGET="${1:-all}"
DEBOUNCE=5  # 초

WATCH_PATHS=(
  "$SHARED/reality_map_live.json"
  "$SHARED/growth_bus.jsonl"
  "$SHARED/dse_cross_results.json"
  "$SHARED/n6_mirror"
)

echo "[watch-remote] monitoring ${#WATCH_PATHS[@]} paths → sync-remote $TARGET"
echo "[watch-remote] debounce=${DEBOUNCE}s"

if command -v fswatch &>/dev/null; then
  # macOS
  fswatch -o -l "$DEBOUNCE" "${WATCH_PATHS[@]}" | while read -r _; do
    echo "[$(date +%H:%M:%S)] change detected → syncing..."
    bash "$SYNC_DIR/sync-remote.sh" push "$TARGET" 2>&1 | tail -5
  done
elif command -v inotifywait &>/dev/null; then
  # Linux
  while true; do
    inotifywait -r -q -e modify,create,delete "${WATCH_PATHS[@]}" --timeout 60 2>/dev/null || true
    echo "[$(date +%H:%M:%S)] change detected → syncing..."
    bash "$SYNC_DIR/sync-remote.sh" push "$TARGET" 2>&1 | tail -5
    sleep "$DEBOUNCE"
  done
else
  echo "[ERROR] fswatch (macOS) or inotifywait (Linux) 필요"
  exit 1
fi
