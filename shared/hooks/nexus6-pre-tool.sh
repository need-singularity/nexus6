#!/usr/bin/env bash
# mk2 hexa-only pre-tool hook
set +e
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/bootstrap.sh" || exit 0

INPUT=$(cat)
bash "$HOOK_DIR/growth-tick.sh" pre-tool </dev/null >/dev/null 2>&1 &

HEXA="${HOME}/Dev/hexa-lang/target/release/hexa"
HEXA_JSON_FIELD="${HOME}/Dev/nexus6/mk2_hexa/native/json_field.hexa"
HEXA_HOOK="${HOME}/Dev/nexus6/mk2_hexa/native/hook.hexa"

# tool_name 추출
if [ -x "$HEXA" ] && [ -f "$HEXA_JSON_FIELD" ]; then
  TOOL_NAME=$(echo "$INPUT" | "$HEXA" "$HEXA_JSON_FIELD" tool_name 2>/dev/null)
else
  TOOL_NAME=$(echo "$INPUT" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"tool_name"[[:space:]]*:[[:space:]]*"//;s/".*//')
fi

# Agent 도구 → hexa hook agent 모드
if [ "$TOOL_NAME" = "Agent" ]; then
  if [ -x "$HEXA" ] && [ -f "$HEXA_HOOK" ]; then
    RESULT=$(echo "$INPUT" | "$HEXA" "$HEXA_HOOK" agent 2>/dev/null) || true
    [ -n "$RESULT" ] && echo "$RESULT"
  fi
fi

exit 0
