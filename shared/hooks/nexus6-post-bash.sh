#!/usr/bin/env bash
# PostToolUse:Bash — 실행 결과 스캔
set +e

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
INPUT=$(cat)

bash "$HOOK_DIR/growth-tick.sh" post-bash </dev/null >/dev/null 2>&1 &

HOOK_BIN="$HOME/Dev/nexus6/target/release/nexus6_hook"
if [ -x "$HOOK_BIN" ]; then
  echo "$INPUT" | "$HOOK_BIN" --mode post-bash 2>/dev/null || true
  exit 0
fi

# fallback: Python
source "$HOOK_DIR/ensure-symlinks.sh" 2>/dev/null || true
echo "$INPUT" | python3 "$HOOK_DIR/nexus6-engine.py" --mode post-bash 2>/dev/null || true
exit 0
