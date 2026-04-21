#!/bin/bash
# sim_bridge/multiverse/runner.sh -- ★18 Quantum Multiverse Interferometer pipeline
#
# Steps:
#   1. Build 2 seed files (one from ANU QRNG via fetch_anu, one from /dev/urandom).
#   2. Run interferometer twice (tag=anu, tag=prng), producing per-run MI values.
#   3. Run compare_ks on the two mi_values.txt files → KS test JSON.
#   4. Write summary.md into the run directory.
#
# Usage:
#   bash runner.sh                 # defaults M=10 T=200 dim=64
#   M=6 T=100 DIM=32 bash runner.sh
#   SKIP_ANU=1 bash runner.sh      # dev loop: only urandom as both sources
#
# H-NOBLOCK: 짧은 파이프라인, sleep/loop 무. H-NOHOOK/H-NOARCHIVE 준수.

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HEXA="${HEXA:-$HOME/Dev/nexus/shared/bin/hexa}"
M="${M:-10}"
T="${T:-200}"
DIM="${DIM:-64}"

TS="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="$SCRIPT_DIR/runs/$TS"
mkdir -p "$RUN_DIR/anu" "$RUN_DIR/prng"

# bytes needed per source: M * (DIM + T)
NEED=$((M * (DIM + T)))
echo "[runner] config: M=$M T=$T DIM=$DIM bytes_needed=$NEED"
echo "[runner] run_dir=$RUN_DIR"

# ----- 1. Seed files -----
# PRNG: urandom decimal space-separated
PRNG_SEED="$RUN_DIR/prng_seed.txt"
head -c "$NEED" /dev/urandom | od -An -vtu1 | tr -s ' \n' ' ' > "$PRNG_SEED"
echo "[runner] prng seed: $(wc -w < "$PRNG_SEED") bytes"

# ANU: cached hex from fetch_anu, extend via urandom if need > 64
ANU_SEED="$RUN_DIR/anu_seed.txt"
if [ "${SKIP_ANU:-0}" = "1" ]; then
  echo "[runner] SKIP_ANU=1 → ANU seed also urandom (dev mode)"
  head -c "$NEED" /dev/urandom | od -An -vtu1 | tr -s ' \n' ' ' > "$ANU_SEED"
else
  # use cached ANU bytes (fetch_anu writes 64-byte hex to .anu_cache.bin)
  ANU_CACHE="$HOME/Dev/nexus/shared/discovery/rng_lab/.anu_cache.bin"
  if [ ! -f "$ANU_CACHE" ]; then
    echo "[runner] WARN: no ANU cache — attempting fresh fetch"
    HEXA_LOCAL=1 "$HEXA" "$HOME/Dev/nexus/shared/discovery/rng_lab/fetch_anu.hexa" info >/dev/null 2>&1 || true
  fi
  if [ -f "$ANU_CACHE" ]; then
    ANU_HEX="$(tr -d '\n ' < "$ANU_CACHE")"
    ANU_LEN_HEX=${#ANU_HEX}
    ANU_LEN_BYTES=$((ANU_LEN_HEX / 2))
    echo "[runner] ANU cache bytes: $ANU_LEN_BYTES"
    # write hex head, then decimals from urandom as extension (space-separated decimals)
    # interferometer auto-detects hex vs decimal; to mix we convert ANU hex → decimals first.
    python3 -c "
h = '$ANU_HEX'
decs = [str(int(h[i:i+2], 16)) for i in range(0, len(h), 2)]
import os
if $NEED > len(decs):
    with open('/dev/urandom', 'rb') as f:
        extra = f.read($NEED - len(decs))
    decs.extend(str(b) for b in extra)
print(' '.join(decs[:$NEED]))
" > "$ANU_SEED"
    echo "[runner] anu seed: $(wc -w < "$ANU_SEED") bytes (first $ANU_LEN_BYTES from ANU, rest urandom-extended — honest)"
  else
    echo "[runner] ANU cache missing and fetch failed — fallback urandom"
    head -c "$NEED" /dev/urandom | od -An -vtu1 | tr -s ' \n' ' ' > "$ANU_SEED"
  fi
fi

# ----- 2. Run interferometer per source -----
echo "[runner] running interferometer on ANU seed..."
HEXA_LOCAL=1 "$HEXA" "$SCRIPT_DIR/interferometer.hexa" anu "$ANU_SEED" "$M" "$T" "$DIM" "$RUN_DIR/anu" 2>&1 | tee "$RUN_DIR/anu/stdout.log"

echo "[runner] running interferometer on PRNG seed..."
HEXA_LOCAL=1 "$HEXA" "$SCRIPT_DIR/interferometer.hexa" prng "$PRNG_SEED" "$M" "$T" "$DIM" "$RUN_DIR/prng" 2>&1 | tee "$RUN_DIR/prng/stdout.log"

# ----- 3. KS compare -----
echo "[runner] KS 2-sample test..."
HEXA_LOCAL=1 "$HEXA" "$SCRIPT_DIR/compare_ks.hexa" "$RUN_DIR/anu/mi_values.txt" "$RUN_DIR/prng/mi_values.txt" "$RUN_DIR/ks_result.json" 2>&1 | tee "$RUN_DIR/ks_stdout.log"

# ----- 4. Summary -----
ANU_STATS=$(cat "$RUN_DIR/anu/stats.json" 2>/dev/null || echo "{}")
PRNG_STATS=$(cat "$RUN_DIR/prng/stats.json" 2>/dev/null || echo "{}")
KS_JSON=$(cat "$RUN_DIR/ks_result.json" 2>/dev/null || echo "{}")

# extract scaled values via simple grep
get_field() {
  local json="$1"
  local field="$2"
  echo "$json" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('$field', 'NA'))" 2>/dev/null || echo "NA"
}

ANU_MEAN=$(get_field "$ANU_STATS" "mi_mean_scaled")
ANU_STD=$(get_field "$ANU_STATS" "mi_std_scaled")
PRNG_MEAN=$(get_field "$PRNG_STATS" "mi_mean_scaled")
PRNG_STD=$(get_field "$PRNG_STATS" "mi_std_scaled")
D_S=$(get_field "$KS_JSON" "D_scaled")
P_S=$(get_field "$KS_JSON" "p_scaled")
LAMBDA_S=$(get_field "$KS_JSON" "lambda_scaled")

# p-value interpretation
INTERP="H0 유지 (ANU ≡ PRNG 같은 분포)"
if [ "$P_S" != "NA" ] && [ "$P_S" -lt "50" ] 2>/dev/null; then
  INTERP="★ H0 기각 (p<0.05): ANU 분포가 PRNG 분포와 유의하게 다름 — 숨은 구조 또는 substrate 시그널"
elif [ "$P_S" != "NA" ] && [ "$P_S" -lt "100" ] 2>/dev/null; then
  INTERP="경계 (p<0.1): 샘플 확대 필요"
fi

# float-ify scaled values for readability (÷ 1000)
scaled_to_float() {
  local s="$1"
  if [ "$s" = "NA" ]; then echo "NA"; return; fi
  python3 -c "print(f'{$s/1000:.4f}')" 2>/dev/null || echo "$s"
}
ANU_MEAN_F=$(scaled_to_float "$ANU_MEAN")
ANU_STD_F=$(scaled_to_float "$ANU_STD")
PRNG_MEAN_F=$(scaled_to_float "$PRNG_MEAN")
PRNG_STD_F=$(scaled_to_float "$PRNG_STD")
D_F=$(scaled_to_float "$D_S")
LAMBDA_F=$(scaled_to_float "$LAMBDA_S")
P_F=$(scaled_to_float "$P_S")

cat > "$RUN_DIR/summary.md" <<EOF
# NEXUS-6 ★18 Quantum Multiverse Interferometer — run $TS

## Config
- M=$M universes, T=$T steps, dim=$DIM (latent), pairs=$((M*(M-1)/2))
- bytes_per_source = $NEED
- ANU source: $( [ "${SKIP_ANU:-0}" = "1" ] && echo "(skipped, urandom used)" || echo "first 64 bytes ANU QRNG, rest urandom-extended" )
- run_dir: $RUN_DIR

## MI 결과 (pairwise, nats)
| source | pairs | mean | std |
|--------|-------|------|-----|
| ANU    | $((M*(M-1)/2)) | $ANU_MEAN_F | $ANU_STD_F |
| PRNG   | $((M*(M-1)/2)) | $PRNG_MEAN_F | $PRNG_STD_F |

## KS 2-sample
- D = $D_F
- λ = $LAMBDA_F
- p-value ≈ $P_F

**해석**: $INTERP

## 발견
$(
  if [ "$P_S" != "NA" ]; then
    if [ "$P_S" -lt "50" ] 2>/dev/null; then
      echo "- ★ ANU QRNG 로 시드된 우주 쌍의 MI 분포가 PRNG 분포와 통계적으로 다름 (p=$P_F). 양자 숨은 상관 or null baseline bias 확인 필요."
    elif [ "$P_S" -lt "200" ] 2>/dev/null; then
      echo "- 경계 신호 (p=$P_F): M/T 증가 후 재검토 권장."
    else
      echo "- Phase 0 MVP 에선 ANU vs PRNG MI 분포 통계적 차이 없음 (p=$P_F > 0.2). null ≡ 양자, 이는 Bell-like 불평등 없이는 예상대로."
    fi
  fi
  # 최대 MI pair 찾기
  if [ -f "$RUN_DIR/anu/mi_values.txt" ]; then
    MAX_ANU=$(sort -n "$RUN_DIR/anu/mi_values.txt" | tail -1)
    MAX_ANU_F=$(scaled_to_float "$MAX_ANU")
    echo "- ANU 최대 MI pair = $MAX_ANU_F nats (4-bin plug-in, finite-sample bias 포함)"
  fi
)

## 출력 파일
- \`anu/trajectories.jsonl\` : M 우주 energy 시계열 (ANU seed)
- \`prng/trajectories.jsonl\` : M 우주 energy 시계열 (PRNG seed)
- \`anu/mi_matrix.csv\` \`prng/mi_matrix.csv\` : M×M symmetric MI matrices (scaled ×1000)
- \`anu/mi_values.txt\` \`prng/mi_values.txt\` : flat pairwise MI values
- \`ks_result.json\` : KS 통계량 + p-value

## 주의사항 (honest)
- 4-bin histogram plug-in MI estimator → O((B-1)/(2T)) bias. T=$T 에 약 $(python3 -c "print(f'{3/(2*$T)*1000:.0f}')") (×1000).
- ANU 한번 호출당 64 바이트 제한 → 부족분은 urandom 확장 (label 유지).
- bin 경계 [0,75,150,225,inf] 는 mini_world 출력 실측 기반 고정값. 추후 동적 quantile 로 개선 여지.
EOF

echo "[runner] done. summary: $RUN_DIR/summary.md"
cat "$RUN_DIR/summary.md"
