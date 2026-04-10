#!/usr/bin/env bash
# Rotating nexus evolve across domains — generates new discoveries periodically.
set -euo pipefail

NEXUS_BIN="${HOME}/.cargo/bin/nexus"
[ -x "$NEXUS_BIN" ] || { echo "nexus binary not found"; exit 0; }

# Rotating domains based on hour-of-day (24-hour rotation)
HOUR=$(date +%H)
DOMAIN_IDX=$((10#$HOUR % 8))
DOMAINS=("physics" "math" "biology" "cosmology" "music" "chemistry" "topology" "consciousness")
DOMAIN="${DOMAINS[$DOMAIN_IDX]}"

cd "${HOME}/Dev/nexus"
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] evolve domain=$DOMAIN (hour=$HOUR)"

# Run evolve with short cycles — don't overload
"$NEXUS_BIN" evolve "$DOMAIN" --max-cycles 3 2>&1 | tail -20 &
PID=$!
( sleep 180; kill -TERM $PID 2>/dev/null ) &
WATCHER=$!
wait $PID 2>/dev/null
kill $WATCHER 2>/dev/null || true
