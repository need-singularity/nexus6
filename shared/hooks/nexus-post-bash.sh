#!/usr/bin/env bash
# mk2 hexa-only hook (Rust/Python 의존 0)
set +e
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/bootstrap.sh" || exit 0

INPUT=$(cat)
bash "$HOOK_DIR/growth-tick.sh" post-bash </dev/null >/dev/null 2>&1 &

HEXA="$HOME/Dev/nexus/shared/scripts/bin/hexa"
HEXA_HOOK="$HOME/Dev/nexus/shared/hooks/hook.hexa"

# mk2 hexa only
RESULT=$(echo "$INPUT" | "$HEXA" "$HEXA_HOOK" post-bash 2>/dev/null) || true
[ -n "$RESULT" ] && echo "$RESULT" || bash "$HOOK_DIR/nexus-banner.sh"
exit 0
