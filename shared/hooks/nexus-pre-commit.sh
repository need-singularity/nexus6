#!/usr/bin/env bash
# PreToolUse:Bash — 커밋 전 수치 스캔
set +e

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/check-project.sh"
INPUT=$(cat)

bash "$HOOK_DIR/growth-tick.sh" pre-commit </dev/null >/dev/null 2>&1 &

HOOK_BIN="$HOME/Dev/nexus/target/release/nexus_hook"
if [ -x "$HOOK_BIN" ]; then
  RESULT=$(echo "$INPUT" | "$HOOK_BIN" --mode pre-commit 2>/dev/null) || true
  if [ -n "$RESULT" ]; then
    echo "$RESULT"
  else
    bash "$HOOK_DIR/nexus-banner.sh"
  fi
  exit 0
fi

# fallback: hexa hook 엔진 (Python 대체)
source "$HOOK_DIR/ensure-symlinks.sh" 2>/dev/null || true
HEXA="${HOME}/Dev/hexa-lang/target/release/hexa"
HEXA_HOOK="${HOME}/Dev/nexus/mk2_hexa/native/hook.hexa"

if [ -x "$HEXA" ] && [ -f "$HEXA_HOOK" ]; then
  RESULT=$(echo "$INPUT" | "$HEXA" "$HEXA_HOOK" pre-commit 2>/dev/null) || true
else
  # hexa 없으면 Python fallback 유지
  RESULT=$(echo "$INPUT" | /usr/bin/python3 "$HOOK_DIR/nexus-engine.py" --mode pre-commit 2>/dev/null) || true
fi
if [ -n "$RESULT" ]; then
  echo "$RESULT"
else
  bash "$HOOK_DIR/nexus-banner.sh"
fi
exit 0
