#!/bin/bash
# Claude Code 효율 특이점 사이클 파이프라인
# 100% 로컬 실행, 외부 API 호출 없음
set -euo pipefail
cd "$(dirname "$0")/.."

DATE=$(date +%Y%m%d)
OUT_DIR="shared/breakthroughs"
mkdir -p "$OUT_DIR"

echo "[1/4] mining Claude Code sessions..."
python3 tools/cc_session_miner.py --sessions 20

echo "[2/4] syncing math atlas..."
if [ -x "shared/sync-math-atlas.sh" ]; then
  bash shared/sync-math-atlas.sh
  sleep 2
else
  echo "WARN: shared/sync-math-atlas.sh not found or not executable, skipping" >&2
fi

echo "[3/4] running nexus6 auto (claude_efficiency) with 30min timeout..."
NEXUS_BIN="${NEXUS_BIN:-nexus6}"
CYCLE_OUT="$OUT_DIR/claude_efficiency_$DATE.json"
if timeout 1800 "$NEXUS_BIN" auto claude_efficiency \
     --meta-cycles 5 --ouroboros-cycles 3 > "$CYCLE_OUT"; then
  echo "cycle done"
else
  rc=$?
  echo "WARN: cycle exit=$rc (timeout=124 or error), continuing with partial output" >&2
fi

echo "[4/4] interpreting breakthrough..."
if [ -s "$CYCLE_OUT" ]; then
  python3 tools/interpret_breakthrough.py "$CYCLE_OUT"
else
  echo "ERROR: cycle output empty, cannot interpret" >&2
  exit 4
fi

echo "done. review: $OUT_DIR/claude_efficiency_rules_$(date +%Y-%m-%d).md"
