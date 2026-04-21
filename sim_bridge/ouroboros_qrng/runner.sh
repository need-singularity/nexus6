#!/bin/bash
# runner.sh — ouroboros × QRNG robustness experiment
#
# Usage:
#   bash runner.sh [n_trials=15] [gens=15] [qrng_hex_path]
#
# SAFETY:
#   - calls ouroboros_shadow.hexa (L0-safe replica); NEVER touches
#     shared/blowup/ouroboros/ouroboros_meta.hexa
#   - no backups, no hooks, no cron
#   - no mutation of atlas.n6 (shadow does not read it)
#
# If no qrng_hex_path given, the runner picks the most recent
# ouroboros_qrng/runs/*/anu_stream.hex (>= 256 bytes = 512 hex chars).
# Falls back to /dev/urandom (label "urandom" instead of "anu") if none.

set -u
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
NTRIALS="${1:-15}"
GENS="${2:-15}"
QRNG_HEX="${3:-}"

TS="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="$HERE/runs/$TS"
mkdir -p "$RUN_DIR"

export HEXA_LOCAL=1
HEXA="$HOME/Dev/nexus/shared/bin/hexa"
SHADOW="$HERE/ouroboros_shadow.hexa"

echo "[runner] ts=$TS trials=$NTRIALS gens=$GENS"
echo "[runner] run_dir=$RUN_DIR"

# ─── resolve QRNG hex path ───
if [ -z "$QRNG_HEX" ]; then
    for cand in $(ls -t "$HERE"/runs/*/anu_stream.hex 2>/dev/null); do
        SZ=$(wc -c < "$cand" | tr -d ' ')
        if [ "$SZ" -ge 512 ]; then
            QRNG_HEX="$cand"
            echo "[runner] using ANU stream: $cand (${SZ} hex chars)"
            break
        fi
    done
fi

if [ -z "$QRNG_HEX" ] || [ ! -f "$QRNG_HEX" ]; then
    echo "[runner] WARN: no ANU stream >= 256B. Using /dev/urandom fallback (label=urandom)."
    head -c 512 /dev/urandom | od -An -vtx1 | tr -d ' \n' > "$RUN_DIR/urandom_stream.hex"
    QRNG_HEX="$RUN_DIR/urandom_stream.hex"
    QRNG_LABEL="urandom"
else
    QRNG_LABEL="anu"
fi

# snapshot stream into run dir
cp "$QRNG_HEX" "$RUN_DIR/qrng_stream.hex"
QRNG_HEX="$RUN_DIR/qrng_stream.hex"
echo "[runner] QRNG source: $QRNG_LABEL  ($(wc -c < "$QRNG_HEX" | tr -d ' ') hex chars = $(( $(wc -c < "$QRNG_HEX" | tr -d ' ') / 2 )) bytes)"

# ─── run det trials (serial; each trial ~0.3s) ───
DET_LOG="$RUN_DIR/det.log"
echo "[runner] deterministic trials → $DET_LOG"
: > "$DET_LOG"
for ((t=0; t<NTRIALS; t++)); do
    "$HEXA" "$SHADOW" det $t $GENS >> "$DET_LOG" 2>&1 || echo "# det trial $t FAILED" >> "$DET_LOG"
    printf "\n" >> "$DET_LOG"  # hexa's final println omits trailing \n; enforce separator
done
echo "[runner] det done: $(grep -c 'FINAL' "$DET_LOG") finals"

# ─── run qrng trials ───
QRNG_LOG="$RUN_DIR/qrng.log"
echo "[runner] qrng trials ($QRNG_LABEL) → $QRNG_LOG"
: > "$QRNG_LOG"
for ((t=0; t<NTRIALS; t++)); do
    "$HEXA" "$SHADOW" qrng $t $GENS "$QRNG_HEX" >> "$QRNG_LOG" 2>&1 || echo "# qrng trial $t FAILED" >> "$QRNG_LOG"
    printf "\n" >> "$QRNG_LOG"
done
echo "[runner] qrng done: $(grep -c 'FINAL' "$QRNG_LOG") finals"

# ─── analyse ───
echo "[runner] analysing..."
"$HEXA" "$HERE/comparison.hexa" "$DET_LOG" "$QRNG_LOG" "$QRNG_LABEL" "$RUN_DIR/summary.md" "$RUN_DIR/stats.json"

echo "[runner] DONE → $RUN_DIR"
echo ""
cat "$RUN_DIR/summary.md"
