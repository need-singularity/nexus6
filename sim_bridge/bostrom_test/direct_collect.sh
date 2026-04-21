#!/bin/bash
# direct_collect.sh — bash direct ANU collection, parallel alternative to hexa collector
# Usage: direct_collect.sh <out_hex> <n_req> [gap_sec=70]

set -uo pipefail

OUT="$1"
N="$2"
GAP="${3:-70}"
META="$OUT.meta.jsonl"

: > "$OUT"
: > "$META"

echo "# direct collect: n=$N gap=${GAP}s"
i=0
fail_count=0
while [ "$i" -lt "$N" ]; do
    HEX=$(curl -s --max-time 10 'https://qrng.anu.edu.au/API/jsonI.php?length=64&type=uint8' 2>/dev/null | /usr/bin/python3 -c "import sys,json
try:
    d=json.load(sys.stdin)
    if d.get('success'):
        print(''.join(f'{b:02x}' for b in d.get('data',[])[:64]))
except:
    pass" 2>/dev/null)
    if [ -n "$HEX" ] && [ ${#HEX} -ge 128 ]; then
        HEX="${HEX:0:128}"
        T=$(date +%s)
        echo -n "$HEX" >> "$OUT"
        echo "{\"i\":$i,\"t\":$T,\"src\":\"anu_direct\",\"hex\":\"$HEX\"}" >> "$META"
        echo "OK req=$i t=$T"
        fail_count=0
        i=$((i + 1))
        sleep "$GAP"
    else
        fail_count=$((fail_count + 1))
        echo "FAIL req=$i attempt=$fail_count"
        if [ "$fail_count" -ge 10 ]; then
            echo "10 consecutive fails — giving up"
            break
        fi
        sleep "$GAP"
    fi
done
echo "# done: reqs=$i"
