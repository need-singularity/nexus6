#!/bin/bash
# atlas_health.sh — atlas.n6 무결성 헬스체크
# 용도: orphan edges, 중복, 깨진 라인, grade 이상 감지 (readonly)
# 사용: shared/n6/atlas_health.sh [path] [--verbose]
#       path 기본값: shared/n6/atlas.n6

set -eu

ATLAS="${1:-shared/n6/atlas.n6}"
VERBOSE="${2:-}"

if [ ! -f "$ATLAS" ]; then
  echo "error: atlas file not found: $ATLAS" >&2
  echo "usage: $0 [path] [--verbose]" >&2
  exit 1
fi

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

NODE_IDS="$TMPDIR/nodes"
EDGE_REFS="$TMPDIR/edges"

echo "=== atlas.n6 health: $ATLAS ==="
SIZE=$(stat -f "%z" "$ATLAS" 2>/dev/null || stat -c "%s" "$ATLAS" 2>/dev/null)
LINES=$(wc -l < "$ATLAS" | tr -d ' ')
NODES=$(grep -c '"type":"node"' "$ATLAS" || echo 0)
EDGES=$(grep -c '"type":"edge"' "$ATLAS" || echo 0)

printf "  size:          %s bytes (%.1f MB)\n" "$SIZE" "$(echo "scale=1; $SIZE/1048576" | bc)"
printf "  lines:         %s\n" "$LINES"
printf "  nodes:         %s\n" "$NODES"
printf "  edges:         %s\n" "$EDGES"

# Build node ID set
awk -F'"id":"' '/"type":"node"/{split($2,a,"\"");print a[1]}' "$ATLAS" | sort -u > "$NODE_IDS"
NODE_UNIQ=$(wc -l < "$NODE_IDS" | tr -d ' ')
printf "  unique nodes:  %s (dup node IDs: %s)\n" "$NODE_UNIQ" "$((NODES - NODE_UNIQ))"

# Extract edge from/to
awk '/"type":"edge"/ {
  match($0, /"from":"[^"]*"/); if(RSTART>0) print substr($0, RSTART+8, RLENGTH-9)
  match($0, /"to":"[^"]*"/);   if(RSTART>0) print substr($0, RSTART+6, RLENGTH-7)
}' "$ATLAS" | sort -u > "$EDGE_REFS"
REFS_UNIQ=$(wc -l < "$EDGE_REFS" | tr -d ' ')
printf "  unique refs:   %s\n" "$REFS_UNIQ"

# Orphan refs = edge refs not in node set
# 제외: n6-*, bt-*, foundation-* 가상 참조 (@P/@R/@C 유도 체인)
ALL_MISSING="$TMPDIR/missing"
comm -23 "$EDGE_REFS" "$NODE_IDS" > "$ALL_MISSING"
REAL_ORPHANS=$(grep -vE '^(n6-|bt-|foundation-)' "$ALL_MISSING" | wc -l | tr -d ' ')
VIRTUAL_REFS=$(grep -cE '^(n6-|bt-|foundation-)' "$ALL_MISSING" 2>/dev/null || echo 0)
printf "  virtual refs:  %s (n6-/bt-/foundation- 유도 체인)\n" "$VIRTUAL_REFS"
printf "  real orphans:  %s" "$REAL_ORPHANS"
if [ "$REAL_ORPHANS" -gt 0 ]; then
  printf "  ⚠️\n"
  if [ "$VERBOSE" = "--verbose" ]; then
    echo "  --- first 20 real orphans ---"
    grep -vE '^(n6-|bt-|foundation-)' "$ALL_MISSING" | head -20 | sed 's/^/    /'
  fi
else
  printf "  ✓\n"
fi
ORPHANS=$REAL_ORPHANS

# Duplicate data lines (exclude # comments and blanks)
DUP=$(grep -v '^#' "$ATLAS" | grep -v '^$' | sort | uniq -d | wc -l | tr -d ' ')
printf "  dup data lines:%s" "$DUP"
if [ "$DUP" -gt 0 ]; then
  printf "  ⚠️\n"
else
  printf "  ✓\n"
fi

# Malformed lines: not empty, not comment, not indented, not JSON, not @-entry
MAL=$(awk '
  /^$|^#/ { next }
  /^[[:space:]]/ { next }
  /^[{]/ { next }
  /^@/ { next }
  { c++ }
  END { print c+0 }
' "$ATLAS")
printf "  malformed:     %s" "$MAL"
if [ "$MAL" -gt 0 ]; then
  printf "  ⚠️\n"
  if [ "$VERBOSE" = "--verbose" ]; then
    echo "  --- first 10 malformed ---"
    awk '
      /^$|^#/ { next }
      /^[[:space:]]/ { next }
      /^[{]/ { next }
      /^@/ { next }
      { print NR": "$0 }
    ' "$ATLAS" | head -10 | sed 's/^/    /'
  fi
else
  printf "  ✓\n"
fi

# Grade distribution
echo "  grade dist:"
grep -oE '\[[0-9]+\*?\]' "$ATLAS" | sort | uniq -c | sort -rn | head -8 | sed 's/^/    /'

# Exit with warning if any issues found
if [ "$ORPHANS" -gt 0 ] || [ "$DUP" -gt 0 ] || [ "$MAL" -gt 0 ]; then
  exit 1
fi
exit 0
