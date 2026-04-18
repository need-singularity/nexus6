#!/bin/bash
# benchmark.sh — throughput + quality tests for anu_stream daemon
#
# Produces:
#   - MB/s throughput for 4 KiB, 16 KiB, 64 KiB keystream blocks (file mode)
#   - NIST monobit test (frequency of 1-bits ~ 0.5)
#   - Simple runs test (number of transitions ~ N/2 for random)
#   - RFC 7539 chacha20 self-test result
#
# Exit code: 0 if all quality tests pass, 1 otherwise.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HEXA="${HOME}/Dev/nexus/shared/bin/hexa"
DAEMON="${HERE}/stream_daemon.hexa"
CHACHA="${HERE}/chacha20.hexa"

export HEXA_LOCAL=1

echo "== anu_stream benchmark =="
date

# ---------- 1. RFC 7539 self-test on ChaCha20 ----------
echo
echo "[1/5] ChaCha20 RFC 7539 §2.3.2 self-test..."
CT_OUT=$("$HEXA" "$CHACHA" test 2>&1 || true)
echo "$CT_OUT" | head -2
if echo "$CT_OUT" | grep -q "^PASS rfc7539_block"; then
    KAT_PASS=1
else
    KAT_PASS=0
fi

# ---------- 2. Throughput, 3 sizes ----------
echo
echo "[2/5] Throughput benchmark (file output)..."
TMP_BIN="$(mktemp -t anu_bench.XXXXXX.bin)"
trap "rm -f '$TMP_BIN' '${TMP_BIN}.hex'" EXIT

declare -a SIZES=(4096 16384 65536)
declare -a MBPS

for i in "${!SIZES[@]}"; do
    SZ="${SIZES[$i]}"
    OUT=$("$HEXA" "$DAEMON" file "$SZ" "$TMP_BIN" 2>&1 | tail -1)
    RATE=$(echo "$OUT" | sed -n 's/.*throughput_MBps=\([0-9.e-]*\).*/\1/p')
    echo "  size=${SZ}B  -> $OUT"
    MBPS[$i]="$RATE"
done

# ---------- 3. Quality sample: generate 16 KiB for tests ----------
echo
echo "[3/5] Quality sample: reusing 65536-byte throughput sample..."
# The last throughput iteration (65536 bytes) already produced $TMP_BIN.
SAMPLE_SIZE=$(stat -f '%z' "$TMP_BIN" 2>/dev/null || stat -c '%s' "$TMP_BIN")
echo "  sample bytes=$SAMPLE_SIZE"

# ---------- 4. NIST Monobit test ----------
#   H0: stream is random (expected p1 = 0.5)
#   Statistic: s = (sum_bits - N/2) / sqrt(N/4) ~ N(0,1)
#   |s| < 2.576 at 99% -> pass
echo
echo "[4/5] NIST monobit (frequency) test..."
MONO_STATS=$(/usr/bin/python3 - <<PY
import sys, math
data = open("${TMP_BIN}","rb").read()
n = len(data) * 8
ones = sum(bin(b).count("1") for b in data)
p = ones / n
z = (2*ones - n) / math.sqrt(n)   # (sum(+-1))/sqrt(N)
p_value = math.erfc(abs(z) / math.sqrt(2))
print(f"bits={n} ones={ones} p1={p:.6f} |z|={abs(z):.4f} p_value={p_value:.4f} pass={'YES' if p_value >= 0.01 else 'NO'}")
PY
)
echo "  $MONO_STATS"
MONO_PASS=$(echo "$MONO_STATS" | grep -oE 'pass=(YES|NO)' | tail -1 | cut -d= -f2)

# ---------- 5. Runs test (transitions) ----------
#   Count transitions between adjacent bits. For random: ~N/2.
#   Statistic: z = (transitions - (N-1)/2) / sqrt((N-1)/4)
echo
echo "[5/5] Runs (transitions) test..."
RUNS_STATS=$(/usr/bin/python3 - <<PY
import math
data = open("${TMP_BIN}","rb").read()
bits=[]
for byte in data:
    for i in range(8):
        bits.append((byte >> (7-i)) & 1)
n = len(bits)
# NIST SP 800-22 runs test (prereq: monobit passed, here we run unconditionally)
pi = sum(bits) / n
if abs(pi - 0.5) >= 2.0 / math.sqrt(n):
    print(f"bits={n} prereq_fail |pi-0.5|={abs(pi-0.5):.4f} pass=NO")
else:
    V = 1 + sum(1 for i in range(n-1) if bits[i] != bits[i+1])
    expected = 2*n*pi*(1-pi)
    denom = 2*math.sqrt(2*n)*pi*(1-pi)
    z = abs(V - expected) / denom
    p_value = math.erfc(z)
    print(f"bits={n} V={V} expected={expected:.1f} |z|={z:.4f} p_value={p_value:.4f} pass={'YES' if p_value >= 0.01 else 'NO'}")
PY
)
echo "  $RUNS_STATS"
RUNS_PASS=$(echo "$RUNS_STATS" | grep -oE 'pass=(YES|NO)' | tail -1 | cut -d= -f2)

# ---------- Summary ----------
echo
echo "== SUMMARY =="
echo "  KAT (RFC 7539):     $([ "$KAT_PASS" = "1" ] && echo PASS || echo FAIL)"
echo "  Monobit freq test:  $MONO_PASS"
echo "  Runs transitions:   $RUNS_PASS"
echo "  Throughput (MB/s):"
for i in "${!SIZES[@]}"; do
    printf "    %6d B : %s MB/s\n" "${SIZES[$i]}" "${MBPS[$i]}"
done

ALL_OK=1
[ "$KAT_PASS"  = "1"   ] || ALL_OK=0
[ "$MONO_PASS" = "YES" ] || ALL_OK=0
[ "$RUNS_PASS" = "YES" ] || ALL_OK=0

if [ "$ALL_OK" = "1" ]; then
    echo "  overall: OK"
    exit 0
else
    echo "  overall: FAIL"
    exit 1
fi
