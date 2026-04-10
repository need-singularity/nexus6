#!/usr/bin/env bash
# nexus-daemon.sh — LaunchAgent에서 호출하는 자율 데몬 래퍼
set -euo pipefail

export NEXUS_ROOT="/Users/ghost/Dev/nexus"
export PATH="$HOME/.cargo/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
export HOME="${HOME:-/Users/ghost}"

LOG_DIR="$HOME/Library/Logs/nexus"
mkdir -p "$LOG_DIR"

BINARY="$NEXUS_ROOT/target/release/nexus"

# release 빌드가 없으면 debug 사용
if [ ! -f "$BINARY" ]; then
    BINARY="$NEXUS_ROOT/target/debug/nexus"
fi

if [ ! -f "$BINARY" ]; then
    echo "$(date): nexus 바이너리 없음 — cargo build 필요" >> "$LOG_DIR/daemon.log"
    exit 1
fi

exec "$BINARY" daemon --interval 30 "$@" >> "$LOG_DIR/daemon.log" 2>&1
