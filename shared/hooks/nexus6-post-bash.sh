#!/usr/bin/env bash
set +e
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/bootstrap.sh" || exit 0

INPUT=$(cat)
bash "$HOOK_DIR/growth-tick.sh" post-bash </dev/null >/dev/null 2>&1 &

HOOK_BIN="$HOME/Dev/nexus6/target/release/nexus6_hook"
if [ -x "$HOOK_BIN" ]; then
  RESULT=$(echo "$INPUT" | "$HOOK_BIN" --mode post-bash 2>/dev/null) || true
  [ -n "$RESULT" ] && echo "$RESULT" || bash "$HOOK_DIR/nexus6-banner.sh"
  exit 0
fi
source "$HOOK_DIR/ensure-symlinks.sh" 2>/dev/null || true
RESULT=$(echo "$INPUT" | python3 "$HOOK_DIR/nexus6-engine.py" --mode post-bash 2>/dev/null) || true
[ -n "$RESULT" ] && echo "$RESULT" || bash "$HOOK_DIR/nexus6-banner.sh"
exit 0
