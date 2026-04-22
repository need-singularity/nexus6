#!/bin/bash
# runner.sh — σ sweep driver (8 σ × 20 trials = 160 runs)
#
# L0 safety: runs ouroboros_shadow dynamics (no atlas writes), nice 19.
# Anti-blocking: each run ≤ a few seconds; no background sleeps.
#
# Usage:
#   ./runner.sh                 # full sweep
#   ./runner.sh quick           # 4 σ × 5 trials (smoke)

set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

HEXA=/Users/ghost/Dev/nexus/bin/hexa
# Force local exec so write_file/read_file target local FS (avoid remote dispatch
# which would write to ubu1/hetzner and lose the log/stats for analyze).
export HEXA_LOCAL=1
MODE="${1:-full}"

TS=$(date -u +%Y%m%d_%H%M%S)
OUT_DIR="$ROOT/runs/$TS"
mkdir -p "$OUT_DIR"

LOG="$OUT_DIR/sweep.log"
STATS="$OUT_DIR/stats.json"
SUMMARY_MD="$OUT_DIR/summary.md"

if [ "$MODE" = "quick" ]; then
  SIGMAS=(0 0.01 0.1 1.0)
  TRIALS=5
else
  SIGMAS=(0 0.001 0.01 0.05 0.1 0.5 1.0 2.0)
  TRIALS=20
fi
GENS=6

: > "$LOG"
echo "# sweep start: $TS"  | tee -a "$LOG"
echo "# sigmas: ${SIGMAS[*]}"  | tee -a "$LOG"
echo "# trials per sigma: $TRIALS"  | tee -a "$LOG"
echo "# gens: $GENS"  | tee -a "$LOG"
echo ""  | tee -a "$LOG"

START=$(date +%s)
TOTAL_RUNS=$(( ${#SIGMAS[@]} * TRIALS ))
RUN_IDX=0

for SIGMA in "${SIGMAS[@]}"; do
  for T in $(seq 0 $((TRIALS - 1))); do
    RUN_IDX=$((RUN_IDX + 1))
    nice -n 19 "$HEXA" sweep_runner.hexa run "$T" "$SIGMA" "$GENS" \
      2>&1 | tee -a "$LOG" > /dev/null
    # status every 20 runs
    if [ $((RUN_IDX % 20)) -eq 0 ]; then
      NOW=$(date +%s)
      EL=$((NOW - START))
      echo "  progress: $RUN_IDX / $TOTAL_RUNS  (elapsed ${EL}s)"
    fi
  done
done

END=$(date +%s)
echo "" | tee -a "$LOG"
echo "# sweep done: $((END - START))s total" | tee -a "$LOG"

# analyze
echo ""
echo "=== analyze ==="
nice -n 19 "$HEXA" analyze_curve.hexa run "$LOG" "$STATS" "$SUMMARY_MD"

echo ""
echo "outputs:"
echo "  log:     $LOG"
echo "  stats:   $STATS"
echo "  summary: $SUMMARY_MD"
