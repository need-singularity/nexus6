#!/usr/bin/env bash
# Growth Scan Hook — nexus6_hook Rust 바이너리로 디스패치
# UserPromptSubmit 훅에서 호출. 30분 쿨다운 내장.
set +e

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/check-project.sh"
INPUT=$(cat)

# growth-tick in background — suppress all output to prevent stdout corruption
bash "$HOOK_DIR/growth-tick.sh" growth-scan </dev/null >/dev/null 2>&1 &

HOOK_BIN="$HOME/Dev/nexus6/target/release/nexus6_hook"
if [ -x "$HOOK_BIN" ]; then
  RESULT=$(echo "$INPUT" | "$HOOK_BIN" --mode growth-scan 2>/dev/null) || true
  if [ -n "$RESULT" ]; then
    echo "$RESULT"
  else
    bash "$HOOK_DIR/nexus6-banner.sh"
  fi
else
  bash "$HOOK_DIR/nexus6-banner.sh"
fi
exit 0
