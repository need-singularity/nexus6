#!/bin/bash
# Sync shared work rules across all repo CLAUDE.md files
# Source of truth: TECS-L/.shared/shared_work_rules.md
#
# Usage: bash .shared/sync-claude-rules.sh
# Run from TECS-L repo root

set -e

SHARED_DIR="$(cd "$(dirname "$0")" && pwd)"
SHARED="$SHARED_DIR/shared_work_rules.md"
MARKER_START="<!-- SHARED:WORK_RULES:START -->"
MARKER_END="<!-- SHARED:WORK_RULES:END -->"

if [ ! -f "$SHARED" ]; then
  echo "Error: $SHARED not found"
  exit 1
fi

CONTENT=$(cat "$SHARED")

sync_file() {
  local file="$1"

  if [ ! -f "$file" ]; then
    echo "  SKIP: $file not found"
    return
  fi

  if ! grep -q "$MARKER_START" "$file"; then
    echo "  SKIP: $file has no markers"
    return
  fi

  /usr/bin/python3 -c "
import sys
start_marker = '$MARKER_START'
end_marker = '$MARKER_END'

with open('$file', 'r') as f:
    text = f.read()

s = text.index(start_marker) + len(start_marker)
e = text.index(end_marker)

with open('$SHARED', 'r') as f:
    content = f.read()

new = text[:s] + '\n' + content + text[e:]

with open('$file', 'w') as f:
    f.write(new)
"
  echo "  SYNCED: $file"
}

commit_and_push() {
  local repo_dir="$1"
  local repo_name="$2"

  cd "$repo_dir"
  if git diff --quiet CLAUDE.md 2>/dev/null; then
    echo "  No changes"
  else
    git add CLAUDE.md
    git pull --rebase --quiet 2>/dev/null || true
    git commit -m "Sync shared work rules from TECS-L"
    git push
    echo "  Pushed!"
  fi
  cd - > /dev/null
}

BASE="$(cd "$SHARED_DIR/.." && pwd)"
PARENT="$(cd "$BASE/.." && pwd)"

echo "=== Syncing shared work rules ==="
echo "Source: $SHARED"
echo ""

for repo in TECS-L anima sedi n6-architecture brainwire papers; do
  if [ "$repo" = "TECS-L" ]; then
    repo_dir="$BASE"
  else
    repo_dir="$PARENT/$repo"
  fi
  echo "[$repo]"
  sync_file "$repo_dir/CLAUDE.md"
  commit_and_push "$repo_dir" "$repo"
done

echo ""
echo "Done!"
