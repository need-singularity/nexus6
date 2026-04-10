#!/bin/bash
# sync-nexus-lenses.sh — NEXUS-6 렌즈 수 동기화
# Source of truth: nexus telescope_test.rs assertions
#
# Usage: cd ~/Dev/TECS-L && bash .shared/sync-nexus-lenses.sh
# Run from TECS-L repo root (or anywhere — paths are absolute)

set -e

SHARED_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE="$(cd "$SHARED_DIR/.." && pwd)"
PARENT="$(cd "$BASE/.." && pwd)"
N6_DIR="$PARENT/n6-architecture"
NEXUS_DIR="$N6_DIR/tools/nexus"

echo "=== NEXUS-6 Lens Sync ==="
echo ""

# ──────────────────────────────────────────
# Step 1: Count lenses from source code
# ──────────────────────────────────────────
echo "[1/5] Counting lenses from source..."

if [ ! -d "$NEXUS_DIR/src/telescope" ]; then
  echo "Error: $NEXUS_DIR/src/telescope not found"
  exit 1
fi

# Primary method: extract from telescope_test.rs assertions (ground truth)
TEST_FILE="$NEXUS_DIR/tests/telescope_test.rs"
if [ -f "$TEST_FILE" ]; then
  # Extract total from: assert_eq!(reg.len(), NNN, "...");
  TOTAL=$(grep -oE 'reg\.len\(\),\s*[0-9]+' "$TEST_FILE" | head -1 | grep -oE '[0-9]+$')
  # Extract core count
  CORE=$(grep -oE 'cores\.len\(\),\s*[0-9]+' "$TEST_FILE" | head -1 | grep -oE '[0-9]+$')
  # Extract extended count
  EXTENDED=$(grep -oE 'extended\.len\(\),\s*[0-9]+' "$TEST_FILE" | head -1 | grep -oE '[0-9]+$')
fi

# Fallback: grep entry functions and count vec! items
if [ -z "$TOTAL" ] || [ "$TOTAL" = "0" ]; then
  echo "  Warning: Could not parse test file, counting from source..."
  TOTAL=$(grep -c 'LensEntry {' "$NEXUS_DIR"/src/telescope/*.rs 2>/dev/null || echo "0")
  CORE=22
  EXTENDED=$((TOTAL - CORE))
fi

echo "  Total: $TOTAL lenses (Core: ${CORE:-22}, Extended: ${EXTENDED:-?})"
echo ""

if [ -z "$TOTAL" ] || [ "$TOTAL" = "0" ]; then
  echo "Error: Failed to count lenses"
  exit 1
fi

# ──────────────────────────────────────────
# Step 2: Extract per-module breakdown
# ──────────────────────────────────────────
echo "[2/5] Extracting module breakdown..."

# Parse individual module counts from test assertions
# Format: assert_eq!(entries.len(), NN, "Must have exactly NN xxx lenses");
grep 'entries\.len()' "$TEST_FILE" 2>/dev/null | while IFS= read -r line; do
  count=$(echo "$line" | grep -oE 'entries\.len\(\),\s*[0-9]+' | grep -oE '[0-9]+$')
  desc=$(echo "$line" | grep -oE '"Must have exactly [0-9]+ [^"]*"' | sed 's/"//g')
  if [ -n "$count" ] && [ -n "$desc" ]; then
    echo "  $desc"
  fi
done

# Also get the breakdown comment from registry.rs
REG_COMMENT=$(grep -oE '22 Core.*total\)' "$NEXUS_DIR/src/telescope/registry.rs" 2>/dev/null | head -1)
if [ -n "$REG_COMMENT" ]; then
  echo "  Registry: $REG_COMMENT"
fi
echo ""

# ──────────────────────────────────────────
# Step 3: Update .shared/CLAUDE.md
# ──────────────────────────────────────────
echo "[3/5] Updating .shared/CLAUDE.md..."

CLAUDE_MD="$SHARED_DIR/CLAUDE.md"
CHANGED=0

if [ -f "$CLAUDE_MD" ]; then
  # Use Python for UTF-8 safe regex replacement (heredoc avoids escaping issues)
  RESULT=$(/usr/bin/python3 - "$CLAUDE_MD" "$TOTAL" <<'PYEOF'
import re, sys

claude_md = sys.argv[1]
total = int(sys.argv[2])

with open(claude_md, 'r') as f:
    text = f.read()

original = text
changes = []

# Pattern 1: NEXUS-6 망원경 (NNN종 렌즈)
m = re.search(r'NEXUS-6 망원경 \((\d+)종 렌즈\)', original)
text, n = re.subn(r'NEXUS-6 망원경 \((\d+)종 렌즈\)', f'NEXUS-6 망원경 ({total}종 렌즈)', text)
if n and m: changes.append(f'Header: {m.group(1)} → {total}')

# Pattern 2: NNN종 렌즈 레지스트리
text, n = re.subn(r'(\d+)종 렌즈 레지스트리', f'{total}종 렌즈 레지스트리', text)
if n: changes.append(f'Inline registry ref → {total}')

# Pattern 3: NNN종 레지스트리 (standalone)
text, n = re.subn(r'(\d+)종 레지스트리', f'{total}종 레지스트리', text)
if n: changes.append(f'Registry ref → {total}')

# Pattern 4: NEXUS-6 (NNN종) — dual-stack header
text, n = re.subn(r'NEXUS-6 \((\d+)종\)', f'NEXUS-6 ({total}종)', text)
if n: changes.append(f'Dual-stack ref → {total}')

# Pattern 5: 렌즈 NNN종 구성
text, n = re.subn(r'렌즈 (\d+)종 구성', f'렌즈 {total}종 구성', text)
if n: changes.append(f'Composition ref → {total}')

if text != original:
    with open(claude_md, 'w') as f:
        f.write(text)
    for c in changes:
        print(f'  {c}')
    print('CHANGED')
else:
    print('  Already up to date (no change)')
PYEOF
)

  echo "$RESULT" | grep -v '^CHANGED$'
  if echo "$RESULT" | grep -q 'CHANGED'; then
    CHANGED=1
  fi
else
  echo "  SKIP: $CLAUDE_MD not found"
fi
echo ""

# ──────────────────────────────────────────
# Step 4: Update installed_tools.json
# ──────────────────────────────────────────
echo "[4/5] Updating installed_tools.json..."

TOOLS_JSON="$SHARED_DIR/installed_tools.json"
if [ -f "$TOOLS_JSON" ]; then
  # Update the purpose field for nexus
  OLD_PURPOSE=$(/usr/bin/python3 -c "
import json
with open('$TOOLS_JSON') as f:
    d = json.load(f)
entry = d.get('cli_tools', {}).get('nexus', {})
print(entry.get('purpose', ''))
" 2>/dev/null)

  if [ -n "$OLD_PURPOSE" ]; then
    # Extract old lens count from purpose string
    OLD_LENS_IN_PURPOSE=$(echo "$OLD_PURPOSE" | grep -oE '[0-9]+ lenses' | grep -oE '[0-9]+')
    if [ -z "$OLD_LENS_IN_PURPOSE" ]; then
      OLD_LENS_IN_PURPOSE=$(echo "$OLD_PURPOSE" | grep -oE 'telescope [0-9]+' | grep -oE '[0-9]+')
    fi

    NEW_PURPOSE="NEXUS-6 Discovery Engine — telescope ${TOTAL} lenses + OUROBOROS evolution + graph + verifier"

    if [ "$OLD_PURPOSE" = "$NEW_PURPOSE" ]; then
      echo "  Already up to date (no change)"
    else
      /usr/bin/python3 -c "
import json
with open('$TOOLS_JSON') as f:
    d = json.load(f)
if 'nexus' in d.get('cli_tools', {}):
    d['cli_tools']['nexus']['purpose'] = '$NEW_PURPOSE'
    with open('$TOOLS_JSON', 'w') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    print('  Updated: $NEW_PURPOSE')
else:
    print('  SKIP: no nexus entry in cli_tools')
" 2>/dev/null
      CHANGED=1
    fi
  else
    echo "  SKIP: no nexus entry found"
  fi
else
  echo "  SKIP: $TOOLS_JSON not found"
fi
echo ""

# ──────────────────────────────────────────
# Step 5: Update calculators.json
# ──────────────────────────────────────────
echo "[5/5] Updating calculators.json..."

CALC_JSON="$SHARED_DIR/calculators.json"
if [ -f "$CALC_JSON" ]; then
  /usr/bin/python3 -c "
import json

with open('$CALC_JSON') as f:
    d = json.load(f)

updated = False
for repo_key in d:
    if not isinstance(d[repo_key], list):
        continue
    for entry in d[repo_key]:
        if 'nexus' in entry.get('path', ''):
            old_desc = entry.get('description', '')
            new_desc = 'NEXUS-6 Discovery Engine — ${TOTAL} lenses telescope + OUROBOROS'
            if old_desc != new_desc:
                entry['description'] = new_desc
                updated = True
                print(f'  Updated: {entry[\"name\"]} → {new_desc}')

if updated:
    with open('$CALC_JSON', 'w') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
else:
    print('  No changes needed')
" 2>/dev/null
  # Check if file changed
  if ! git -C "$BASE" diff --quiet "$CALC_JSON" 2>/dev/null; then
    CHANGED=1
  fi
else
  echo "  SKIP: $CALC_JSON not found"
fi
echo ""

# ──────────────────────────────────────────
# Step 6: Git commit (no push)
# ──────────────────────────────────────────
if [ "$CHANGED" = "1" ]; then
  echo "=== Committing changes ==="
  cd "$BASE"
  git add .shared/CLAUDE.md .shared/installed_tools.json .shared/calculators.json 2>/dev/null || true
  if ! git diff --cached --quiet 2>/dev/null; then
    git commit -m "sync: NEXUS-6 lens count → ${TOTAL} (auto-sync)"
    echo "  Committed! (no push — run 'git push' manually)"
  else
    echo "  No staged changes to commit"
  fi
  cd - > /dev/null
else
  echo "=== No changes detected ==="
fi

echo ""
echo "Done! NEXUS-6 lens count: ${TOTAL}"
echo "  Core: ${CORE:-22}"
echo "  Extended: ${EXTENDED:-?}"
echo ""
echo "Next steps:"
echo "  1. cd ~/Dev/TECS-L && git push  (if committed)"
echo "  2. bash .shared/sync-claude-rules.sh  (propagate to all repos)"
