#!/bin/bash
# Sync shared project descriptions across all repos
# Source of truth: TECS-L/.shared/projects.md
#
# Usage: bash .shared/sync-readmes.sh
# Run from TECS-L repo root

set -e

SHARED="$(cd "$(dirname "$0")" && pwd)/projects.md"
MARKER_START="<!-- SHARED:PROJECTS:START -->"
MARKER_END="<!-- SHARED:PROJECTS:END -->"

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
content = '''$CONTENT'''

with open('$file', 'r') as f:
    lines = f.read()

s = lines.index(start_marker) + len(start_marker)
e = lines.index(end_marker)
new = lines[:s] + '\n' + content + '\n' + lines[e:]

with open('$file', 'w') as f:
    f.write(new)
"
  echo "  SYNCED: $file"
}

commit_and_push() {
  local repo_dir="$1"
  local repo_name="$2"

  cd "$repo_dir"
  if git diff --quiet README.md 2>/dev/null; then
    echo "  No changes"
  else
    git add README.md
    git pull --rebase --quiet 2>/dev/null || true
    git commit -m "Sync project list from TECS-L"
    git push
    echo "  Pushed!"
  fi
  cd - > /dev/null
}

BASE="$(cd "$(dirname "$SHARED")/.." && pwd)"
PARENT="$(cd "$BASE/.." && pwd)"

SHARED_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== [1/3] Loop Lens: actual JSON → projects.json + projects.md ==="
if [ -f "$SHARED_DIR/sync_projects_json.py" ]; then
  /usr/bin/python3 "$SHARED_DIR/sync_projects_json.py" --apply
fi

echo ""
echo "=== [2/3] JSON SSOT → README auto-sync (all repos) ==="
if [ -f "$SHARED_DIR/sync_readme_all.py" ]; then
  /usr/bin/python3 "$SHARED_DIR/sync_readme_all.py" --apply
fi
echo ""

echo "=== [3/3] Syncing project descriptions + commit + push ==="
echo "Source: $SHARED"
echo ""

# TECS-L
echo "[TECS-L]"
sync_file "$BASE/README.md"
commit_and_push "$BASE" "TECS-L"

# Anima
echo "[Anima]"
sync_file "$PARENT/anima/README.md"
commit_and_push "$PARENT/anima" "anima"

# PH Training — removed (merged into TECS-L/tools/ph-training/)

# SEDI
echo "[SEDI]"
sync_file "$PARENT/sedi/README.md"
commit_and_push "$PARENT/sedi" "sedi"

# Golden MoE — removed (now anima sub-project)
# ConsciousLM — removed (now anima sub-project)

# N6 Architecture (formerly Energy Efficiency)
echo "[N6 Architecture]"
sync_file "$PARENT/n6-architecture/README.md"
commit_and_push "$PARENT/n6-architecture" "n6-architecture"

# BrainWire
echo "[BrainWire]"
sync_file "$PARENT/brainwire/README.md"
commit_and_push "$PARENT/brainwire" "brainwire"

# HEXA-LANG
echo "[HEXA-LANG]"
sync_file "$PARENT/hexa-lang/README.md"
commit_and_push "$PARENT/hexa-lang" "hexa-lang"

# Papers
echo "[Papers]"
sync_file "$PARENT/papers/README.md"
commit_and_push "$PARENT/papers" "papers"

echo ""
echo "Done!"
