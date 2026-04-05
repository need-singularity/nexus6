#!/usr/bin/env bash
set +e
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/bootstrap.sh" || exit 0

INPUT=$(cat)
bash "$HOOK_DIR/growth-tick.sh" pre-tool </dev/null >/dev/null 2>&1 &

# Agent 도구일 때만 --mode agent 호출 — hexa로 JSON 필드 추출
HEXA="${HOME}/Dev/hexa-lang/target/release/hexa"
HEXA_JSON_FIELD="${HOME}/Dev/nexus6/mk2_hexa/native/json_field.hexa"

if [ -x "$HEXA" ] && [ -f "$HEXA_JSON_FIELD" ]; then
  TOOL_NAME=$(echo "$INPUT" | "$HEXA" "$HEXA_JSON_FIELD" tool_name 2>/dev/null)
else
  # hexa 없으면 grep 기반 fallback
  TOOL_NAME=$(echo "$INPUT" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"tool_name"[[:space:]]*:[[:space:]]*"//;s/".*//')
fi

if [ "$TOOL_NAME" = "Agent" ]; then
  HOOK_BIN="$HOME/Dev/nexus6/target/release/nexus6_hook"
  if [ -x "$HOOK_BIN" ]; then
    RESULT=$(echo "$INPUT" | "$HOOK_BIN" --mode agent 2>/dev/null) || true
    [ -n "$RESULT" ] && echo "$RESULT"
    exit 0
  fi
  # Python 엔진 fallback (hexa hook.hexa 우선)
  HEXA_HOOK="${HOME}/Dev/nexus6/mk2_hexa/native/hook.hexa"
  if [ -x "$HEXA" ] && [ -f "$HEXA_HOOK" ]; then
    RESULT=$(echo "$INPUT" | "$HEXA" "$HEXA_HOOK" agent 2>/dev/null) || true
  else
    RESULT=$(echo "$INPUT" | python3 "$HOOK_DIR/nexus6-engine.py" --mode agent 2>/dev/null) || true
  fi
  [ -n "$RESULT" ] && echo "$RESULT"
  exit 0
fi

# Agent 이외 도구 — 배너만 (PreToolUse에서 stdout 없음)
exit 0
