#!/usr/bin/env bash
# Growth Scan Hook — nexus6_hook Rust 바이너리로 디스패치
# UserPromptSubmit 훅에서 호출. 30분 쿨다운 내장.

HOOK_BIN="$HOME/Dev/nexus6/target/release/nexus6_hook"

if [ -x "$HOOK_BIN" ]; then
  cat | "$HOOK_BIN" --mode growth-scan
else
  exit 0
fi
