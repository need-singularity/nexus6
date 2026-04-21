#!/bin/bash
# collect_long_anu.sh - fetch GOAL bytes from ANU QRNG, respecting 1 req/min.
# Writes hex (no newline) to OUT; appends each 64B block on success, logs progress.
#
# Usage: collect_long_anu.sh <out_hex> [goal_bytes=1024]
#
# Rate-limit: ANU allows ~1 req/min. On "limited to 1 requests per minute" we wait 65s.
# We parse JSON only; plain-text error responses are treated as MISS without extra delay.

set -u
OUT="${1:?out hex path}"
GOAL="${2:-1024}"
LOG="${OUT%.hex}.log"

CUR_HEX=""
if [ -f "$OUT" ]; then
    CUR_HEX="$(tr -d '\n' < "$OUT")"
fi
CUR_BYTES=$(( ${#CUR_HEX} / 2 ))
echo "[$(date +%H:%M:%S)] start goal=${GOAL}B current=${CUR_BYTES}B out=$OUT" | tee -a "$LOG"

# seed cache from existing ANU cache if present & we have 0 bytes
if [ $CUR_BYTES -lt 64 ] && [ -f "$HOME/Dev/nexus/discovery/rng_lab/.anu_cache.bin" ]; then
    SEED="$(cat "$HOME/Dev/nexus/discovery/rng_lab/.anu_cache.bin" 2>/dev/null)"
    if [ ${#SEED} -ge 128 ]; then
        CUR_HEX="${SEED:0:128}"
        CUR_BYTES=$(( ${#CUR_HEX} / 2 ))
        printf '%s' "$CUR_HEX" > "$OUT"
        echo "[$(date +%H:%M:%S)] SEED from anu_cache bytes=$CUR_BYTES" | tee -a "$LOG"
    fi
fi

MAX_MINUTES=55
T_DEADLINE=$(( $(date +%s) + MAX_MINUTES * 60 ))

while [ $CUR_BYTES -lt $GOAL ]; do
    NOW=$(date +%s)
    [ $NOW -gt $T_DEADLINE ] && { echo "[$(date +%H:%M:%S)] DEADLINE partial=$CUR_BYTES" | tee -a "$LOG"; break; }

    T0=$NOW
    RAW=$(curl -s --max-time 15 'https://qrng.anu.edu.au/API/jsonI.php?length=64&type=uint8' 2>/dev/null)
    # Must start with '{' else it's the rate-limit error page
    FIRST_CHAR="${RAW:0:1}"
    if [ "$FIRST_CHAR" != "{" ]; then
        # Rate-limit - wait long enough to cross minute boundary (80s)
        echo "[$(date +%H:%M:%S)] RATE-LIMIT msg=${RAW:0:80}... wait 80s" | tee -a "$LOG"
        sleep 80
        continue
    fi

    HEX=$(printf '%s' "$RAW" | /usr/bin/python3 -c "
import sys,json
try:
    d=json.loads(sys.stdin.read())
    if d.get('success') and d.get('data'):
        print(''.join(f'{b:02x}' for b in d['data'][:64]))
    else:
        print('')
except Exception:
    print('')
")
    if [ ${#HEX} -ge 128 ]; then
        CUR_HEX="$CUR_HEX${HEX:0:128}"
        CUR_BYTES=$(( ${#CUR_HEX} / 2 ))
        printf '%s' "$CUR_HEX" > "$OUT"
        echo "[$(date +%H:%M:%S)] OK bytes=${CUR_BYTES}/${GOAL}" | tee -a "$LOG"
    else
        echo "[$(date +%H:%M:%S)] PARSE_MISS raw=${#RAW}c" | tee -a "$LOG"
    fi

    [ $CUR_BYTES -ge $GOAL ] && break
    # rate-limit: 75s since request start (clock-window margin)
    ELAP=$(( $(date +%s) - T0 ))
    WAIT=$(( 75 - ELAP ))
    [ $WAIT -gt 0 ] && sleep $WAIT
done
echo "[$(date +%H:%M:%S)] DONE bytes=$CUR_BYTES" | tee -a "$LOG"
