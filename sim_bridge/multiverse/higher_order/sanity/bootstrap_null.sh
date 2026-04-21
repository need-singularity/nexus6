#!/bin/bash
# bootstrap_null.sh — K independent SKIP_ANU=1 runs to build null KS D distribution
# Uses absolute paths and HEXA_LOCAL=1 (learned from prior sanity run)

set -u
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NEXUS_ROOT="/Users/ghost/Dev/nexus"
MULTIVERSE="$NEXUS_ROOT/sim_bridge/multiverse"
HIGHER_ORDER="$MULTIVERSE/higher_order"
HEXA="$NEXUS_ROOT/bin/hexa"
export HEXA_LOCAL=1

K="${K:-10}"
M_BOOT="${M_BOOT:-15}"
T_BOOT="${T_BOOT:-400}"
DIM_BOOT="${DIM_BOOT:-24}"

TS=$(date -u +%Y%m%d_%H%M%S)
OUT_DIR="$SCRIPT_DIR/bootstrap/$TS"
mkdir -p "$OUT_DIR"
LOG="$OUT_DIR/bootstrap.log"
DS_FILE="$OUT_DIR/null_D.json"

: > "$LOG"
echo "# bootstrap K=$K M=$M_BOOT T=$T_BOOT DIM=$DIM_BOOT start=$TS" | tee -a "$LOG"

echo "[" > "$DS_FILE"
START=$(date +%s)
for i in $(seq 1 $K); do
  ITER_DIR="$OUT_DIR/iter_$i"
  mkdir -p "$ITER_DIR/A" "$ITER_DIR/B"
  echo "  iter $i/$K ($(($(date +%s) - START))s elapsed)" | tee -a "$LOG"

  NEED=$((M_BOOT * (DIM_BOOT + T_BOOT)))
  head -c "$NEED" /dev/urandom | od -An -vtu1 | tr -s ' \n' ' ' > "$ITER_DIR/A_seed.txt"
  head -c "$NEED" /dev/urandom | od -An -vtu1 | tr -s ' \n' ' ' > "$ITER_DIR/B_seed.txt"

  HEXA_LOCAL=1 "$HEXA" "$MULTIVERSE/interferometer.hexa" A "$ITER_DIR/A_seed.txt" "$M_BOOT" "$T_BOOT" "$DIM_BOOT" "$ITER_DIR/A" >>"$LOG" 2>&1
  HEXA_LOCAL=1 "$HEXA" "$MULTIVERSE/interferometer.hexa" B "$ITER_DIR/B_seed.txt" "$M_BOOT" "$T_BOOT" "$DIM_BOOT" "$ITER_DIR/B" >>"$LOG" 2>&1

  HEXA_LOCAL=1 "$HEXA" "$HIGHER_ORDER/triple_mi.hexa" "$ITER_DIR/A/trajectories.jsonl" "$ITER_DIR/A/triples.csv" >>"$LOG" 2>&1
  HEXA_LOCAL=1 "$HEXA" "$HIGHER_ORDER/triple_mi.hexa" "$ITER_DIR/B/trajectories.jsonl" "$ITER_DIR/B/triples.csv" >>"$LOG" 2>&1

  tail -n +2 "$ITER_DIR/A/triples.csv" 2>/dev/null | awk -F, '{print $NF}' > "$ITER_DIR/A/triples_vals.txt"
  tail -n +2 "$ITER_DIR/B/triples.csv" 2>/dev/null | awk -F, '{print $NF}' > "$ITER_DIR/B/triples_vals.txt"

  D_PAIR=$(/usr/bin/python3 -c "
import numpy as np
from scipy.stats import ks_2samp
try:
    a = np.loadtxt('$ITER_DIR/A/mi_values.txt')
    b = np.loadtxt('$ITER_DIR/B/mi_values.txt')
    if len(a) < 2 or len(b) < 2:
        print('NaN')
    else:
        print(f'{ks_2samp(a, b).statistic:.4f}')
except Exception as e:
    print('NaN')
" 2>>"$LOG")
  D_TRI=$(/usr/bin/python3 -c "
import numpy as np
from scipy.stats import ks_2samp
try:
    a = np.loadtxt('$ITER_DIR/A/triples_vals.txt')
    b = np.loadtxt('$ITER_DIR/B/triples_vals.txt')
    if len(a) < 2 or len(b) < 2:
        print('NaN')
    else:
        print(f'{ks_2samp(a, b).statistic:.4f}')
except Exception as e:
    print('NaN')
" 2>>"$LOG")

  if [ "$i" -ne 1 ]; then echo "," >> "$DS_FILE"; fi
  printf '  {"iter": %d, "D_pair": "%s", "D_tri": "%s"}' "$i" "$D_PAIR" "$D_TRI" >> "$DS_FILE"
  echo "    D_pair=$D_PAIR  D_tri=$D_TRI" | tee -a "$LOG"
done
echo "" >> "$DS_FILE"
echo "]" >> "$DS_FILE"

TOTAL=$(($(date +%s) - START))
echo "# bootstrap done ${TOTAL}s" | tee -a "$LOG"
cat "$DS_FILE"
