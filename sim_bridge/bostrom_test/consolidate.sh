#!/bin/bash
# consolidate.sh — merge all ANU-sourced bytes from different bostrom_test runs,
# dedup, write a single stream. Usage: consolidate.sh <out_dir>

set -uo pipefail

OUT_DIR="${1:-/Users/ghost/Dev/nexus/sim_bridge/bostrom_test/runs/bostrom_final}"
mkdir -p "$OUT_DIR"
OUT_HEX="$OUT_DIR/anu_stream.hex"
OUT_META="$OUT_DIR/anu_stream.hex.meta.jsonl"

: > "$OUT_HEX"
: > "$OUT_META"

echo "[consolidate] scanning bostrom runs..."
export BOSTROM_OUT_HEX="$OUT_HEX"
export BOSTROM_OUT_META="$OUT_META"
/usr/bin/python3 /Users/ghost/Dev/nexus/sim_bridge/bostrom_test/consolidate_impl.py
BYTES=$(wc -c < "$OUT_HEX" | tr -d ' ')
echo "[consolidate] total hex chars: $BYTES = $((BYTES / 2)) bytes"
echo "[consolidate] out: $OUT_HEX"
