#!/usr/bin/env bash
# PostToolUse:Write|Edit — 편집 후 수치 검증
set +e

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/check-project.sh"
INPUT=$(cat)

bash "$HOOK_DIR/growth-tick.sh" post-edit </dev/null >/dev/null 2>&1 &

HOOK_BIN="$HOME/Dev/nexus6/target/release/nexus6_hook"
if [ -x "$HOOK_BIN" ]; then
  RESULT=$(echo "$INPUT" | "$HOOK_BIN" --mode post-edit 2>/dev/null) || true
  if [ -n "$RESULT" ]; then
    echo "$RESULT"
  else
    bash "$HOOK_DIR/nexus6-banner.sh"
  fi
  exit 0
fi

# Python fallback (handles .rs and extended file types)
RESULT=$(echo "$INPUT" | python3 "$HOOK_DIR/nexus6-engine.py" --mode post-edit 2>/dev/null) || true
if [ -n "$RESULT" ]; then
  echo "$RESULT"
else
  bash "$HOOK_DIR/nexus6-banner.sh"
fi
exit 0
