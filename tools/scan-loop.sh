#!/usr/bin/env bash
# Rotating nexus scan across domains — light exploration.
set -euo pipefail

NEXUS_BIN="${HOME}/.cargo/bin/nexus"
[ -x "$NEXUS_BIN" ] || exit 0

MINUTE=$(date +%M)
IDX=$((10#$MINUTE % 6))
DOMAINS=("particle" "cosmology" "geometry" "algebra" "number-theory" "statistics")
DOMAIN="${DOMAINS[$IDX]}"

cd "${HOME}/Dev/nexus"
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] scan domain=$DOMAIN"
# macOS-compatible timeout via background + kill
"$NEXUS_BIN" scan "$DOMAIN" 2>&1 | tail -15 &
PID=$!
( sleep 120; kill -TERM $PID 2>/dev/null ) &
WATCHER=$!
wait $PID 2>/dev/null
kill $WATCHER 2>/dev/null || true
