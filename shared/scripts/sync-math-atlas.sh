#!/bin/bash
# Sync math atlas across all repos
# Scans TECS-L, anima, SEDI hypothesis files → builds unified atlas
# Then injects summary into README files via markers
#
# Usage: bash .shared/scripts/sync-math-atlas.sh
# Run from TECS-L repo root

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE="$(cd "$SCRIPT_DIR/.." && pwd)"
PARENT="$(cd "$BASE/.." && pwd)"

echo "=== Math Atlas Sync ==="
echo ""

# Step 1: Build atlas
echo "[1/3] Building atlas..."
/usr/bin/python3 "$SCRIPT_DIR/scan_math_atlas.py" --save --summary

echo ""

# Step 2: Generate README summary and sync to READMEs
echo "[2/3] Syncing README markers..."
SUMMARY=$(/usr/bin/python3 "$SCRIPT_DIR/scan_math_atlas.py" --readme-summary)

sync_readme() {
  local file="$1"
  local label="$2"
  local MARKER_START="<!-- SHARED:ATLAS:START -->"
  local MARKER_END="<!-- SHARED:ATLAS:END -->"

  echo "[$label]"
  if [ ! -f "$file" ]; then
    echo "  SKIP: $file not found"
    return
  fi
  if ! grep -q "$MARKER_START" "$file"; then
    echo "  SKIP: no markers in $file"
    return
  fi

  /usr/bin/python3 -c "
import sys
start = '$MARKER_START'
end = '$MARKER_END'
with open('$file', 'r') as f:
    text = f.read()
s = text.index(start) + len(start)
e = text.index(end)
content = sys.stdin.read()
new = text[:s] + '\n' + content + '\n' + text[e:]
with open('$file', 'w') as f:
    f.write(new)
" <<< "$SUMMARY"
  echo "  SYNCED: $file"
}

sync_readme "$BASE/README.md" "TECS-L"
sync_readme "$PARENT/anima/README.md" "anima"
sync_readme "$PARENT/SEDI/README.md" "SEDI"

echo ""

# Step 3: Commit generated files
echo "[3/3] Committing..."
cd "$BASE"
ATLAS_FILES=".shared/discovery/math_atlas.json .shared/n6/math_atlas.db .shared/n6/math_atlas.dot"

if git diff --quiet $ATLAS_FILES 2>/dev/null && \
   git diff --cached --quiet $ATLAS_FILES 2>/dev/null; then
    echo "  No changes"
else
    git add $ATLAS_FILES
    git commit -m "Update math atlas ($(date +%Y-%m-%d))"
    echo "  Committed!"
fi

echo ""
echo "Done!"
