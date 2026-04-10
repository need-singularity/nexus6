#!/usr/bin/env bash
# sync-remote.sh — 양방향 rsync (htz/vast ↔ local)
# Usage: bash sync/sync-remote.sh [push|pull|both] [htz|vast|all]
set -euo pipefail

NEXUS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SHARED="$NEXUS_ROOT/shared"
INFRA="$SHARED/infra_state.json"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

MODE="${1:-both}"
TARGET="${2:-all}"

HOSTS=()
if [[ "$TARGET" == "all" ]]; then
  HOSTS=(hetzner vast)
elif [[ "$TARGET" == "htz" ]]; then
  HOSTS=(hetzner)
elif [[ "$TARGET" == "vast" ]]; then
  HOSTS=(vast)
else
  HOSTS=("$TARGET")
fi

RSYNC_OPTS=(-azP --exclude='.DS_Store' --exclude='SECRET.md' --exclude='.tmp_*' --timeout=30)
RSYNC_DIR_OPTS=("${RSYNC_OPTS[@]}" --delete)

SYNC_FILES=(
  "reality_map_live.json"
  "growth_bus.jsonl"
  "infra_state.json"
  "dse_cross_results.json"
  "n6/docs/"
  "convergence/"
)

for host in "${HOSTS[@]}"; do
  REMOTE="$host:~/Dev/nexus/shared"
  echo "── sync $host ($MODE) ──"

  if [[ "$MODE" == "push" || "$MODE" == "both" ]]; then
    for f in "${SYNC_FILES[@]}"; do
      src="$SHARED/$f"
      [[ -e "$src" ]] || continue
      if [[ "$f" == */ ]]; then
        rsync "${RSYNC_DIR_OPTS[@]}" "$src" "$REMOTE/$f" 2>/dev/null && echo "  ↑ $f" || echo "  ⚠ $f (skip)"
      else
        rsync "${RSYNC_OPTS[@]}" "$src" "$REMOTE/$f" 2>/dev/null && echo "  ↑ $f" || echo "  ⚠ $f (skip)"
      fi
    done
  fi

  if [[ "$MODE" == "pull" || "$MODE" == "both" ]]; then
    for f in "${SYNC_FILES[@]}"; do
      if [[ "$f" == */ ]]; then
        rsync "${RSYNC_DIR_OPTS[@]}" "$REMOTE/$f" "$SHARED/$f" 2>/dev/null && echo "  ↓ $f" || echo "  ⚠ $f (skip)"
      else
        rsync "${RSYNC_OPTS[@]}" "$REMOTE/$f" "$SHARED/$f" 2>/dev/null && echo "  ↓ $f" || echo "  ⚠ $f (skip)"
      fi
    done
  fi

  echo "  ✅ $host done"
done

# infra_state에 last_sync 기록
python3 -c "
import json, os
p='$INFRA'
d=json.load(open(p))
d['last_sync']={'ts':'$TS','mode':'$MODE','targets':'$TARGET'}
tmp=p+'.tmp'
json.dump(d,open(tmp,'w'),ensure_ascii=False,indent=2)
os.replace(tmp,p)
" 2>/dev/null || true

echo "═══ sync-remote done ($TS) ═══"
