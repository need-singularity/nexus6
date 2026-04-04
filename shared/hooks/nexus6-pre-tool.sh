#!/usr/bin/env bash
set +e
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/bootstrap.sh" || exit 0

INPUT=$(cat)
bash "$HOOK_DIR/growth-tick.sh" pre-tool </dev/null >/dev/null 2>&1 &

# Agent 도구일 때만 --mode agent 호출
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null)

if [ "$TOOL_NAME" = "Agent" ]; then
  HOOK_BIN="$HOME/Dev/nexus6/target/release/nexus6_hook"
  if [ -x "$HOOK_BIN" ]; then
    RESULT=$(echo "$INPUT" | "$HOOK_BIN" --mode agent 2>/dev/null) || true
    [ -n "$RESULT" ] && echo "$RESULT"
    exit 0
  fi
  RESULT=$(echo "$INPUT" | python3 "$HOOK_DIR/nexus6-engine.py" --mode agent 2>/dev/null) || true
  [ -n "$RESULT" ] && echo "$RESULT"
  exit 0
fi

# Agent 이외 도구 — 배너만 (PreToolUse에서 stdout 없음)
exit 0
