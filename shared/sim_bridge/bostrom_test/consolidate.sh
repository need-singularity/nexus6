#!/bin/bash
# consolidate.sh — merge all ANU-sourced bytes from different runs into a single stream.
# Usage: consolidate.sh <out_dir>
set -uo pipefail

OUT_DIR="${1:-/Users/ghost/Dev/nexus/shared/sim_bridge/bostrom_test/runs/bostrom_final}"
mkdir -p "$OUT_DIR"

OUT_HEX="$OUT_DIR/anu_stream.hex"
OUT_META="$OUT_DIR/anu_stream.hex.meta.jsonl"

: > "$OUT_HEX"
: > "$OUT_META"

echo "[consolidate] scanning bostrom runs..."
I=0
for META in /Users/ghost/Dev/nexus/shared/sim_bridge/bostrom_test/runs/bostrom_*/anu_stream.hex.meta.jsonl; do
    if [ -s "$META" ]; then
        while IFS= read -r LINE; do
            SRC=$(/usr/bin/python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(d.get('src',''))" "$LINE" 2>/dev/null)
            HEX=$(/usr/bin/python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(d.get('hex',''))" "$LINE" 2>/dev/null)
            # Accept any ANU-provenance source (anu, cache, anu_direct)
            if [ "$SRC" = "anu" ] || [ "$SRC" = "cache" ] || [ "$SRC" = "anu_direct" ]; then
                if [ ${#HEX} -ge 128 ]; then
                    echo -n "${HEX:0:128}" >> "$OUT_HEX"
                    T=$(date +%s)
                    echo "{\"i\":$I,\"t\":$T,\"src\":\"$SRC\",\"hex\":\"${HEX:0:128}\",\"from\":\"$META\"}" >> "$OUT_META"
                    I=$((I + 1))
                fi
            fi
        done < "$META"
    fi
done
BYTES=$(wc -c < "$OUT_HEX" | tr -d ' ')
echo "[consolidate] consolidated $I chunks = $((BYTES / 2)) bytes"
echo "[consolidate] out: $OUT_HEX"
