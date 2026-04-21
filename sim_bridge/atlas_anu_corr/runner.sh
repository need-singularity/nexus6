#!/bin/bash
# runner.sh — atlas.n6 × ANU QRNG 교차상관 실험 자동 실행
#
# 사용: bash runner.sh [stream_bytes=512]
# 출력: runs/<ts>/ 에 constants.tsv, anu_stream.hex, xcorr_*.csv, ks_results.json, summary.md

set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

BYTES="${1:-512}"
TS="$(date +%Y%m%d_%H%M%S)"
RUN="runs/$TS"
mkdir -p "$RUN"

export HEXA_LOCAL=1
HEXA="$HOME/Dev/nexus/bin/hexa"

echo "[1/5] constants extract"
"$HEXA" "$HERE/atlas_constants.hexa" > "$RUN/constants.tsv"
grep -v 'runtime error' "$RUN/constants.tsv" > "$RUN/constants_clean.tsv"
echo "  constants: $(wc -l < "$RUN/constants_clean.tsv")"

echo "[2/5] urandom baseline ($BYTES bytes)"
"$HEXA" "$HERE/null_baseline.hexa" "$RUN/urandom_stream.hex" "$BYTES"

echo "[3/5] ANU fetch ($BYTES bytes, ~$((BYTES / 64)) min)"
"$HEXA" "$HERE/anu_long_stream.hexa" "$RUN/anu_stream.hex" "$BYTES" 2>&1 | tee "$RUN/anu_fetch.log"

echo "[4/5] xcorr (ANU + urandom)"
"$HEXA" "$HERE/xcorr_engine.hexa" "$RUN/constants_clean.tsv" "$RUN/anu_stream.hex" "$RUN/xcorr_anu.csv" anu
"$HEXA" "$HERE/xcorr_engine.hexa" "$RUN/constants_clean.tsv" "$RUN/urandom_stream.hex" "$RUN/xcorr_urandom.csv" urandom

echo "[5/5] analyze"
"$HEXA" "$HERE/analyze.hexa" "$RUN/xcorr_anu.csv" "$RUN/xcorr_urandom.csv" "$RUN/ks_results.json" "$RUN/summary.md"

echo "== DONE =="
echo "  output: $RUN"
cat "$RUN/summary.md"
