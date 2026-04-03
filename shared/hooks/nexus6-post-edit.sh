#!/usr/bin/env bash
HOOK_BIN="$HOME/Dev/nexus6/target/release/nexus6_hook"
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
INPUT=$(cat)

# Try Rust binary — use output if non-empty
if [ -x "$HOOK_BIN" ]; then
    RESULT=$(echo "$INPUT" | "$HOOK_BIN" --mode post-edit 2>/dev/null)
    [ -n "$RESULT" ] && { echo "$RESULT"; exit 0; }
fi

# Python fallback (handles .rs and extended file types)
echo "$INPUT" | python3 "$HOOK_DIR/nexus6-engine.py" --mode post-edit 2>/dev/null
exit 0
