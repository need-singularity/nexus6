#!/bin/bash
# Sync calculator registry tables across all repos
# Source of truth: auto-generated from scan-calculators.py
#
# Usage: bash .shared/scripts/sync-calculators.sh
# Run from TECS-L repo root

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE="$(cd "$SCRIPT_DIR/.." && pwd)"
PARENT="$(cd "$BASE/.." && pwd)"

MARKER_START="<!-- SHARED:CALCULATORS:START -->"
MARKER_END="<!-- SHARED:CALCULATORS:END -->"

echo "=== Calculator Registry Sync ==="
echo ""

# Step 1: Scan all repos
echo "[1/3] Scanning repos..."
CONTENT=$(/usr/bin/python3 "$SCRIPT_DIR/scan-calculators.py" --markdown --save 2>/dev/null)

if [ -z "$CONTENT" ]; then
  echo "Error: scan produced no output"
  exit 1
fi

echo "  Registry saved to .shared/config/calculators.json"
echo ""

# Step 2: Sync to READMEs
sync_file() {
  local file="$1"
  local label="$2"

  echo "[$label]"

  if [ ! -f "$file" ]; then
    echo "  SKIP: $file not found"
    return
  fi

  if ! grep -q "$MARKER_START" "$file"; then
    echo "  SKIP: no markers in $file"
    echo "  Add these markers to README.md:"
    echo "    $MARKER_START"
    echo "    $MARKER_END"
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

content = sys.stdin.read()
new_text = text[:s] + '\n' + content + '\n' + text[e:]

with open('$file', 'w') as f:
    f.write(new_text)
" <<< "$CONTENT"

  echo "  SYNCED: $file"
}

commit_and_push() {
  local repo_dir="$1"
  local repo_name="$2"

  cd "$repo_dir"
  if git diff --quiet README.md 2>/dev/null; then
    echo "  No changes"
  else
    git add README.md .shared/config/calculators.json 2>/dev/null || git add README.md
    git pull --rebase --quiet 2>/dev/null || true
    git commit -m "Sync calculator registry from TECS-L"
    git push
    echo "  Pushed!"
  fi
  cd - > /dev/null
}

echo "[2/3] Syncing README tables..."

# TECS-L
sync_file "$BASE/README.md" "TECS-L"
commit_and_push "$BASE" "TECS-L"

# Anima
sync_file "$PARENT/anima/README.md" "anima"
commit_and_push "$PARENT/anima" "anima"

# SEDI
sync_file "$PARENT/SEDI/README.md" "SEDI"
commit_and_push "$PARENT/SEDI" "SEDI"

# n6-architecture — copy relevant N6 calc files + sync README
N6_CALC="$PARENT/n6-architecture/tools"
if [ -d "$PARENT/n6-architecture" ]; then
  echo "[n6-architecture] Syncing TECS-L calculators..."
  mkdir -p "$N6_CALC"
  # Copy N6-relevant calculators
  for f in egyptian_fraction.py perfect_number_generalizer.py perfect_number_physics.py \
           divisor_field_theory.py n6_uniqueness_tester.py gate_formula_calculator.py \
           tension_calculator.py convergence_analyzer.py validate_calculators.py; do
    [ -f "$BASE/calc/$f" ] && cp "$BASE/calc/$f" "$N6_CALC/"
  done
  echo "  Copied $(ls "$N6_CALC"/*.py 2>/dev/null | wc -l) calculators"
  sync_file "$PARENT/n6-architecture/README.md" "n6-architecture"
  cd "$PARENT/n6-architecture"
  if ! git diff --quiet 2>/dev/null; then
    git add tools/ README.md
    git pull --rebase --quiet 2>/dev/null || true
    git commit -m "sync: TECS-L calculators from shared registry"
    git push
    echo "  Pushed!"
  else
    echo "  No changes"
  fi
  cd - > /dev/null
fi

# ── SEDI → TECS-L 역동기화 ────────────────────────────────────
echo ""
echo "[3/5] Reverse sync: SEDI → TECS-L..."

SEDI_DIR="$PARENT/sedi"
if [ -d "$SEDI_DIR" ]; then
  # SEDI 가설 등급 → TECS-L/.shared/discovery/sedi-grades.json
  SEDI_GRADES="$SEDI_DIR/data/sedi-grades.json"
  if [ -f "$SEDI_GRADES" ]; then
    cp "$SEDI_GRADES" "$SCRIPT_DIR/sedi-grades.json"
    echo "  SEDI grades synced"
  else
    # 자동 생성 시도
    if [ -f "$SEDI_DIR/scripts/auto_grade_n6.py" ]; then
      echo "  Generating SEDI grades..."
      /usr/bin/python3 "$SEDI_DIR/scripts/auto_grade_n6.py" --save 2>/dev/null
      if [ -f "$SEDI_GRADES" ]; then
        cp "$SEDI_GRADES" "$SCRIPT_DIR/sedi-grades.json"
        echo "  SEDI grades generated and synced"
      fi
    else
      echo "  SKIP: no SEDI grades (run auto_grade_n6.py --save)"
    fi
  fi

  # SEDI 검증 상수 → atlas 등록 (scan_math_atlas.py가 처리)
  SEDI_CONSTANTS="$SEDI_DIR/sedi/constants.py"
  if [ -f "$SEDI_CONSTANTS" ]; then
    echo "  SEDI constants available for atlas"
  fi

  # TECS-L 커밋 (SEDI 역동기화분)
  cd "$BASE"
  if ! git diff --quiet .shared/discovery/sedi-grades.json 2>/dev/null; then
    git add .shared/discovery/sedi-grades.json
    git commit -m "sync: SEDI→TECS-L reverse sync (hypothesis grades)"
    git push
    echo "  Pushed SEDI reverse sync!"
  else
    echo "  No SEDI changes"
  fi
  cd - > /dev/null
else
  echo "  SKIP: SEDI repo not found at $SEDI_DIR"
fi

# ── n6 → TECS-L 역동기화 (자동) ──────────────────────────────
echo ""
echo "[4/5] Reverse sync: n6 → TECS-L..."

N6_DIR="$PARENT/n6-architecture"
if [ -d "$N6_DIR" ]; then
  # DSE TOML 역동기화 (n6 → TECS-L)
  N6_TOML="$N6_DIR/tools/universal-dse/domains"
  TECS_TOML="$SCRIPT_DIR/dse/domains"
  if [ -d "$N6_TOML" ]; then
    BEFORE=$(ls "$TECS_TOML"/*.toml 2>/dev/null | wc -l)
    cp "$N6_TOML"/*.toml "$TECS_TOML/" 2>/dev/null
    AFTER=$(ls "$TECS_TOML"/*.toml 2>/dev/null | wc -l)
    echo "  DSE TOML: $BEFORE → $AFTER domains"
  fi

  # Rust 계산기 바이너리 목록 동기화 (n6 tools/ → TECS-L 레지스트리)
  N6_TOOLS=$(find "$N6_DIR/tools" -name "main.rs" -type f 2>/dev/null | wc -l)
  echo "  n6 Rust tools detected: $N6_TOOLS"

  # 상수 역동기화 (n6 atlas → TECS-L)
  if [ -f "$N6_DIR/docs/atlas-constants.md" ]; then
    cp "$N6_DIR/docs/atlas-constants.md" "$SCRIPT_DIR/n6-atlas-constants.md"
    echo "  Atlas constants synced"
  fi

  # TECS-L 커밋 (역동기화분)
  cd "$BASE"
  if ! git diff --quiet .shared/ 2>/dev/null; then
    git add .shared/
    git commit -m "sync: n6→TECS-L reverse sync (DSE domains + atlas)"
    git push
    echo "  Pushed reverse sync!"
  else
    echo "  No reverse changes"
  fi
  cd - > /dev/null
fi

echo ""
echo "[5/5] Done!"
echo ""

# Summary
/usr/bin/python3 "$SCRIPT_DIR/scan-calculators.py" --summary 2>/dev/null
