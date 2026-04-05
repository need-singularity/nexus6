#!/usr/bin/env bash
# Rotating nexus6 evolve across domains — generates new discoveries periodically.
set -euo pipefail

NEXUS6_BIN="${HOME}/.cargo/bin/nexus6"
[ -x "$NEXUS6_BIN" ] || { echo "nexus6 binary not found"; exit 0; }

# Rotating domains based on hour-of-day (24-hour rotation)
HOUR=$(date +%H)
DOMAIN_IDX=$((10#$HOUR % 8))
DOMAINS=("physics" "math" "biology" "cosmology" "music" "chemistry" "topology" "consciousness")
DOMAIN="${DOMAINS[$DOMAIN_IDX]}"

cd "${HOME}/Dev/nexus6"
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] evolve domain=$DOMAIN (hour=$HOUR)"

# Run evolve with short cycles — don't overload
timeout 180 "$NEXUS6_BIN" evolve "$DOMAIN" --max-cycles 3 2>&1 | tail -20 || echo "(timeout or error)"
