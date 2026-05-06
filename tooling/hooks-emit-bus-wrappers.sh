#!/bin/bash
# tooling/hooks-emit-bus-wrappers.sh — emit bus-form thin wrapper handlers
# from manifest.hook.json PreToolUse hexa-lint-* phases.
#
# Idempotent. Safe to re-run.
# Source: hive-claude-hook-bus/claude.manifest.hook.json (PreToolUse phases)
# Template: hive-claude-hook-bus/handlers/hexa_lint_silent_exit.hexa
# Pattern: subprocess wrapper → hive_claude_hook_bind_main --dispatch PreToolUse <handler>

set -e

HIVE_ROOT="${HIVE_ROOT:-$HOME/core/hive}"
MANIFEST="$HIVE_ROOT/packages/hive-claude-hook-bus/claude.manifest.hook.json"
HANDLERS="$HIVE_ROOT/packages/hive-claude-hook-bus/handlers"
TEMPLATE="$HANDLERS/hexa_lint_silent_exit.hexa"

if [[ ! -f "$MANIFEST" ]]; then
  echo "manifest not found: $MANIFEST" >&2; exit 2
fi
if [[ ! -f "$TEMPLATE" ]]; then
  echo "template not found: $TEMPLATE" >&2; exit 2
fi

# extract hexa-lint-* phase names from PreToolUse
PHASES=$(grep -oE '"name": "hexa-lint-[a-z0-9-]+"' "$MANIFEST" | sed 's/"name": "//; s/"$//' | sort -u)

CREATED=0
SKIPPED=0
for phase in $PHASES; do
  # convert kebab to snake (hexa-lint-foo-bar → hexa_lint_foo_bar)
  handler_key="${phase//-/_}"
  out="$HANDLERS/${handler_key}.hexa"
  if [[ -f "$out" ]]; then
    SKIPPED=$((SKIPPED+1))
    continue
  fi
  # transform template: replace silent_exit with target handler key
  # also rename mktemp tag (hxse_bus → hx<3>_bus) to avoid /tmp collision
  short_tag=$(echo "$handler_key" | sed 's/^hexa_lint_//' | tr -d '_' | head -c 6)
  sed "s/silent_exit/${handler_key#hexa_lint_}/g; s/hxse_bus/hx${short_tag}_bus/g" "$TEMPLATE" > "$out"
  echo "  created: $out"
  CREATED=$((CREATED+1))
done

echo
echo "EMIT_BUS_WRAPPERS created=$CREATED skipped=$SKIPPED total_phases=$(echo $PHASES | wc -w | tr -d ' ')"
