#!/bin/bash
# runner.sh — Bostrom test orchestrator
#
# Usage: runner.sh [n_requests=30] [tag]
#
# Flow:
#   1. Collect ANU bytes via anu_collector.hexa
#   2. Build PRNG comparison streams (prng_oracle.py)
#   3. Score (signature_compare.py) → CSV + JSON
#   4. Summarize (analyze.py) → summary.md

set -euo pipefail

cd "$(dirname "$0")"
ROOT="$(pwd)"
N_REQ="${1:-30}"
TAG="${2:-bostrom_$(date +%Y%m%d-%H%M%S)}"
RUN_DIR="$ROOT/runs/$TAG"
mkdir -p "$RUN_DIR"

echo "== Bostrom test: $TAG =="
echo "== run_dir: $RUN_DIR =="
echo "== n_req: $N_REQ (≈$((N_REQ * 65 / 60)) min ANU collection) =="

HEX_FILE="$RUN_DIR/anu_stream.hex"
META_FILE="$HEX_FILE.meta.jsonl"

# Step 1: ANU collect
echo "-- Step 1: ANU collection --"
export HEXA_LOCAL=1
export NEXUS_NO_BUDGET_OK=1
export NEXUS_NO_TIMEOUT_OK=1
/Users/ghost/Dev/nexus/bin/hexa "$ROOT/anu_collector.hexa" "$HEX_FILE" "$N_REQ" 65 2>&1 | tee "$RUN_DIR/collect.log"

# Convert hex to binary
HEX=$(tr -d '[:space:]' < "$HEX_FILE")
echo "$HEX" | /usr/bin/python3 -c "import sys; sys.stdout.buffer.write(bytes.fromhex(sys.stdin.read().strip()))" > "$RUN_DIR/anu_stream.bin"
echo "-- ANU stream: $(wc -c < "$RUN_DIR/anu_stream.bin") bytes --"

# Step 2+3: compare
echo "-- Step 2/3: PRNG comparison --"
/usr/bin/python3 "$ROOT/signature_compare.py" \
    "$HEX_FILE" \
    "$RUN_DIR/prng_compares.csv" \
    "$RUN_DIR/prng_compares.json" \
    2>&1 | tee -a "$RUN_DIR/collect.log"

# Step 4: analyze
echo "-- Step 4: analyze --"
/usr/bin/python3 "$ROOT/analyze.py" "$RUN_DIR/prng_compares.json" "$RUN_DIR/summary.md"

echo "== DONE =="
echo "Summary: $RUN_DIR/summary.md"
cat "$RUN_DIR/summary.md"
