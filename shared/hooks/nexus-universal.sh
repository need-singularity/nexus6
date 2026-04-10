#!/usr/bin/env bash
# PreToolUse:Agent — 에이전트 컨텍스트 주입
set +e

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/check-project.sh"
INPUT=$(cat)

bash "$HOOK_DIR/growth-tick.sh" agent </dev/null >/dev/null 2>&1 &

HOOK_BIN="$HOME/Dev/nexus/target/release/nexus_hook"
if [ -x "$HOOK_BIN" ]; then
  RESULT=$(echo "$INPUT" | "$HOOK_BIN" --mode agent 2>/dev/null) || true
  if [ -n "$RESULT" ]; then
    echo "$RESULT"
  else
    bash "$HOOK_DIR/nexus-banner.sh"
  fi
  exit 0
fi

# fallback: hexa
source "$HOOK_DIR/ensure-symlinks.sh" 2>/dev/null || true
HEXA="${HOME}/Dev/hexa-lang/target/release/hexa"
RESULT=$(echo "$INPUT" | "$HEXA" "$HOOK_DIR/nexus-engine.hexa" agent 2>/dev/null) || true
if [ -n "$RESULT" ]; then
  echo "$RESULT"
else
  bash "$HOOK_DIR/nexus-banner.sh"
fi
exit 0
