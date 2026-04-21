#!/bin/bash
# scale_runner.sh — 1000-mut scaled demo for godel_q with expanded 7-op space.
# Hard timeout 60min (3600s). All output in scale1k/runs/<ts>/.
#
# SAFETY: no commit, no touches outside scale1k/. Sandbox candidate per run.
#
# Usage: ./scale_runner.sh [N] [mode]
#   N default 1000, cap 1500
#   mode: anu (default) | urandom

set -u

N="${1:-1000}"
MODE="${2:-anu}"
if [ "$N" -gt 1500 ]; then N=1500; fi
if [ "$N" -lt 1 ]; then N=1; fi

TS="$(date +%Y%m%d-%H%M%S)"
BASE="$(cd "$(dirname "$0")" && pwd)"
HEXA="$HOME/Dev/nexus/bin/hexa"

echo "[scale_runner] N=$N mode=$MODE ts=$TS base=$BASE"
echo "[scale_runner] hexa=$HEXA"

export HEXA_LOCAL=1
export HEXA_NO_LAUNCHD=1

# 60min wall
timeout 3600 "$HEXA" run "$BASE/scale_bootstrap.hexa" "$N" "$TS" "$MODE"
RC=$?

LOG="$BASE/runs/$TS/mutations.jsonl"
echo ""
echo "[scale_runner] exit=$RC"
echo "[scale_runner] log=$LOG"

if [ -f "$LOG" ]; then
  echo ""
  echo "--- fixed-point scan ---"
  "$HEXA" run "$BASE/fixed_point_detector.hexa" "$LOG" 10 100
fi
