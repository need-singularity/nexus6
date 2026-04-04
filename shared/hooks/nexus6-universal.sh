#!/usr/bin/env bash
# PreToolUse:Agent — 에이전트 컨텍스트 주입
set +e

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
INPUT=$(cat)

bash "$HOOK_DIR/growth-tick.sh" agent </dev/null >/dev/null 2>&1 &

HOOK_BIN="$HOME/Dev/nexus6/target/release/nexus6_hook"
if [ -x "$HOOK_BIN" ]; then
  echo "$INPUT" | "$HOOK_BIN" --mode agent 2>/dev/null || true
  exit 0
fi

# fallback: Python
source "$HOOK_DIR/ensure-symlinks.sh" 2>/dev/null || true
echo "$INPUT" | python3 "$HOOK_DIR/nexus6-engine.py" --mode agent 2>/dev/null || true
exit 0
