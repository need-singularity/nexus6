#!/usr/bin/env bash
set +e
# 화이트리스트 — hooks-config.json 참조 (하드코딩 제거)
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_NAME=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null)
WHITELIST=$(python3 -c "import json; print(' '.join(json.load(open('$HOOK_DIR/hooks-config.json'))['whitelisted_projects']))" 2>/dev/null)
echo " $WHITELIST " | grep -q " $REPO_NAME " || exit 0

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
