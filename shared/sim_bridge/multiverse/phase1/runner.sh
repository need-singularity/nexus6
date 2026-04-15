#!/bin/bash
# sim_bridge/multiverse/phase1/runner.sh -- Phase 1 pipeline
#
# Steps:
#   1. Build N_TRIAL independent seed files (ANU + urandom head, PRNG full urandom).
#   2. For each trial, run scale_up.hexa × 2 (anu tag, prng tag) × 2 estimators.
#   3. Run ks_trial.hexa per (trial, estimator) -> appended JSONL.
#   4. Run fisher_combine.hexa twice (once per estimator).
#   5. Pool across trials, run single large KS on pool.
#   6. Write summary.md.
#
# Usage:
#   bash runner.sh                               # defaults
#   M=50 T=2000 DIM=144 N_TRIAL=20 bash runner.sh
#   SKIP_ANU=1 bash runner.sh                    # dev mode, both urandom
#
# Time budget: ~60 min. Memory: ~150MB peak.
# Uses /usr/bin/python3 explicitly (avoid ~/.hx/bin/python3 remote wrapper per P8).

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HEXA="${HEXA:-$HOME/Dev/nexus/shared/bin/hexa}"
PY="/usr/bin/python3"
M="${M:-50}"
T="${T:-2000}"
DIM="${DIM:-144}"
N_TRIAL="${N_TRIAL:-20}"

TS="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="$SCRIPT_DIR/../runs/phase1_$TS"
TRIALS_DIR="$RUN_DIR/trials"
mkdir -p "$RUN_DIR" "$TRIALS_DIR"

NEED=$((M * (DIM + T)))
echo "[runner] Phase 1: M=$M T=$T DIM=$DIM N_TRIAL=$N_TRIAL"
echo "[runner] bytes/seed=$NEED  total_bytes=$((NEED * N_TRIAL * 2))"
echo "[runner] run_dir=$RUN_DIR"
START_TIME=$(date +%s)

# ----- ANU cache source -----
ANU_CACHE="$HOME/Dev/nexus/shared/discovery/rng_lab/.anu_cache.bin"
ANU_HEX=""
ANU_LEN_BYTES=0
if [ -f "$ANU_CACHE" ] && [ "${SKIP_ANU:-0}" != "1" ]; then
  ANU_HEX="$(tr -d '\n ' < "$ANU_CACHE")"
  ANU_LEN_BYTES=$((${#ANU_HEX} / 2))
  echo "[runner] ANU cache: $ANU_LEN_BYTES bytes (head-seed only, rest urandom-extended)"
else
  echo "[runner] SKIP_ANU or missing cache -> dev mode (both urandom)"
fi

# ----- 1. Build per-trial seed files -----
SEEDS_DIR="$RUN_DIR/seeds"
mkdir -p "$SEEDS_DIR"
for i in $(seq 0 $((N_TRIAL - 1))); do
  # PRNG: full urandom
  head -c "$NEED" /dev/urandom | od -An -vtu1 | tr -s ' \n' ' ' > "$SEEDS_DIR/trial_${i}_prng.txt"
  # ANU: ANU head + urandom extension
  if [ -n "$ANU_HEX" ]; then
    "$PY" -c "
h = '$ANU_HEX'
decs = [str(int(h[i:i+2], 16)) for i in range(0, len(h), 2)]
import os
if $NEED > len(decs):
    with open('/dev/urandom', 'rb') as f:
        extra = f.read($NEED - len(decs))
    decs.extend(str(b) for b in extra)
print(' '.join(decs[:$NEED]))
" > "$SEEDS_DIR/trial_${i}_anu.txt"
  else
    head -c "$NEED" /dev/urandom | od -An -vtu1 | tr -s ' \n' ' ' > "$SEEDS_DIR/trial_${i}_anu.txt"
  fi
done
echo "[runner] seeds built: $N_TRIAL x 2"

# ----- 2. Run interferometer per trial -----
KS_PLUGIN_JSONL="$RUN_DIR/ks_plugin_trials.jsonl"
KS_KSG_JSONL="$RUN_DIR/ks_ksg_trials.jsonl"
: > "$KS_PLUGIN_JSONL"
: > "$KS_KSG_JSONL"

TRIAL_STATS_JSONL="$RUN_DIR/trial_stats.jsonl"
: > "$TRIAL_STATS_JSONL"

for i in $(seq 0 $((N_TRIAL - 1))); do
  echo "[runner] === trial $i/$((N_TRIAL - 1)) ==="
  for TAG in anu prng; do
    SEED_FILE="$SEEDS_DIR/trial_${i}_${TAG}.txt"
    HEXA_LOCAL=1 "$HEXA" "$SCRIPT_DIR/scale_up.hexa" "$TAG" "$SEED_FILE" "$M" "$T" "$DIM" "$i" "$TRIALS_DIR" >> "$RUN_DIR/scale_up.log" 2>&1
    if [ -f "$TRIALS_DIR/trial_${i}_${TAG}_stats.json" ]; then
      cat "$TRIALS_DIR/trial_${i}_${TAG}_stats.json" >> "$TRIAL_STATS_JSONL"
    fi
  done
  # KS per-trial (both estimators)
  HEXA_LOCAL=1 "$HEXA" "$SCRIPT_DIR/ks_trial.hexa" \
    "$TRIALS_DIR/trial_${i}_anu_plugin.txt" \
    "$TRIALS_DIR/trial_${i}_prng_plugin.txt" \
    "$i" "plugin" "$KS_PLUGIN_JSONL" >> "$RUN_DIR/ks.log" 2>&1
  HEXA_LOCAL=1 "$HEXA" "$SCRIPT_DIR/ks_trial.hexa" \
    "$TRIALS_DIR/trial_${i}_anu_ksg.txt" \
    "$TRIALS_DIR/trial_${i}_prng_ksg.txt" \
    "$i" "ksg" "$KS_KSG_JSONL" >> "$RUN_DIR/ks.log" 2>&1
  ELAPSED=$(($(date +%s) - START_TIME))
  echo "[runner] trial $i done, elapsed=${ELAPSED}s"
done

# ----- 3. Fisher combine -----
echo "[runner] Fisher combining plug-in p-values..."
HEXA_LOCAL=1 "$HEXA" "$SCRIPT_DIR/fisher_combine.hexa" \
  "$KS_PLUGIN_JSONL" "$RUN_DIR/fisher_plugin.json" 2>&1 | tee -a "$RUN_DIR/fisher.log"

echo "[runner] Fisher combining KSG-lite p-values..."
HEXA_LOCAL=1 "$HEXA" "$SCRIPT_DIR/fisher_combine.hexa" \
  "$KS_KSG_JSONL" "$RUN_DIR/fisher_ksg.json" 2>&1 | tee -a "$RUN_DIR/fisher.log"

# ----- 4. Pool across trials + global KS -----
ANU_POOL_PLUGIN="$RUN_DIR/anu_pool_plugin.txt"
PRNG_POOL_PLUGIN="$RUN_DIR/prng_pool_plugin.txt"
ANU_POOL_KSG="$RUN_DIR/anu_pool_ksg.txt"
PRNG_POOL_KSG="$RUN_DIR/prng_pool_ksg.txt"
: > "$ANU_POOL_PLUGIN"; : > "$PRNG_POOL_PLUGIN"; : > "$ANU_POOL_KSG"; : > "$PRNG_POOL_KSG"
for i in $(seq 0 $((N_TRIAL - 1))); do
  [ -f "$TRIALS_DIR/trial_${i}_anu_plugin.txt" ] && cat "$TRIALS_DIR/trial_${i}_anu_plugin.txt" >> "$ANU_POOL_PLUGIN"
  [ -f "$TRIALS_DIR/trial_${i}_prng_plugin.txt" ] && cat "$TRIALS_DIR/trial_${i}_prng_plugin.txt" >> "$PRNG_POOL_PLUGIN"
  [ -f "$TRIALS_DIR/trial_${i}_anu_ksg.txt" ] && cat "$TRIALS_DIR/trial_${i}_anu_ksg.txt" >> "$ANU_POOL_KSG"
  [ -f "$TRIALS_DIR/trial_${i}_prng_ksg.txt" ] && cat "$TRIALS_DIR/trial_${i}_prng_ksg.txt" >> "$PRNG_POOL_KSG"
done

# Pooled KS (reuse ks_trial.hexa, trial_idx=-1)
: > "$RUN_DIR/pooled_ks_plugin.jsonl"; : > "$RUN_DIR/pooled_ks_ksg.jsonl"
HEXA_LOCAL=1 "$HEXA" "$SCRIPT_DIR/ks_trial.hexa" \
  "$ANU_POOL_PLUGIN" "$PRNG_POOL_PLUGIN" -1 "plugin_pooled" "$RUN_DIR/pooled_ks_plugin.jsonl" 2>&1 | tail -3
HEXA_LOCAL=1 "$HEXA" "$SCRIPT_DIR/ks_trial.hexa" \
  "$ANU_POOL_KSG" "$PRNG_POOL_KSG" -1 "ksg_pooled" "$RUN_DIR/pooled_ks_ksg.jsonl" 2>&1 | tail -3

# ----- 5. Build mi_distributions.csv -----
MI_DIST="$RUN_DIR/mi_distributions.csv"
echo "trial,source,estimator,value_scaled" > "$MI_DIST"
for i in $(seq 0 $((N_TRIAL - 1))); do
  for TAG in anu prng; do
    for EST in plugin ksg; do
      f="$TRIALS_DIR/trial_${i}_${TAG}_${EST}.txt"
      if [ -f "$f" ]; then
        awk -v t=$i -v s=$TAG -v e=$EST '{print t","s","e","$1}' "$f" >> "$MI_DIST"
      fi
    done
  done
done
echo "[runner] mi_distributions.csv: $(wc -l < "$MI_DIST") rows"

# ----- 6. Build trials.jsonl -----
TRIALS_JSONL="$RUN_DIR/trials.jsonl"
{
  cat "$KS_PLUGIN_JSONL"
  cat "$KS_KSG_JSONL"
} > "$TRIALS_JSONL"

# ----- 7. Summary -----

# Extract scalar values via /usr/bin/python3
extract() {
  local file="$1"; local key="$2"
  [ ! -f "$file" ] && { echo "NA"; return; }
  "$PY" -c "
import json, sys
try:
    with open('$file') as f: c = f.read()
    if '$file'.endswith('.jsonl'):
        line = c.strip().split('\n')[0] if c.strip() else ''
        d = json.loads(line) if line else {}
    else:
        d = json.loads(c)
    v = d.get('$key', 'NA')
    print(v)
except Exception as e:
    print('NA')
" 2>/dev/null || echo "NA"
}

scaled_f() {
  local v="$1"
  [ "$v" = "NA" ] && { echo "NA"; return; }
  "$PY" -c "print(f'{$v/1000:.4f}')" 2>/dev/null || echo "$v"
}
scaled_f6() {
  local v="$1"
  [ "$v" = "NA" ] && { echo "NA"; return; }
  "$PY" -c "print(f'{$v/1000:.6f}')" 2>/dev/null || echo "$v"
}

FISHER_P_PLUGIN=$(extract "$RUN_DIR/fisher_plugin.json" fisher_p_scaled)
FISHER_P_KSG=$(extract "$RUN_DIR/fisher_ksg.json" fisher_p_scaled)
FISHER_X2_PLUGIN=$(extract "$RUN_DIR/fisher_plugin.json" fisher_X2_scaled)
FISHER_X2_KSG=$(extract "$RUN_DIR/fisher_ksg.json" fisher_X2_scaled)
POOL_P_PLUGIN=$(extract "$RUN_DIR/pooled_ks_plugin.jsonl" p_scaled)
POOL_P_KSG=$(extract "$RUN_DIR/pooled_ks_ksg.jsonl" p_scaled)
POOL_D_PLUGIN=$(extract "$RUN_DIR/pooled_ks_plugin.jsonl" D_scaled)
POOL_D_KSG=$(extract "$RUN_DIR/pooled_ks_ksg.jsonl" D_scaled)
POOL_L_PLUGIN=$(extract "$RUN_DIR/pooled_ks_plugin.jsonl" lambda_scaled)
POOL_L_KSG=$(extract "$RUN_DIR/pooled_ks_ksg.jsonl" lambda_scaled)

FISHER_P_PLUGIN_F=$(scaled_f6 "$FISHER_P_PLUGIN")
FISHER_P_KSG_F=$(scaled_f6 "$FISHER_P_KSG")
POOL_P_PLUGIN_F=$(scaled_f "$POOL_P_PLUGIN")
POOL_P_KSG_F=$(scaled_f "$POOL_P_KSG")
POOL_D_PLUGIN_F=$(scaled_f "$POOL_D_PLUGIN")
POOL_D_KSG_F=$(scaled_f "$POOL_D_KSG")
POOL_L_PLUGIN_F=$(scaled_f "$POOL_L_PLUGIN")
POOL_L_KSG_F=$(scaled_f "$POOL_L_KSG")

BIAS_PLUGIN=$("$PY" -c "print(f'{3/(2*$T):.5f}')" 2>/dev/null)
BIAS_KSG=$("$PY" -c "print(f'{7/(2*$T):.5f}')" 2>/dev/null)
TOTAL_MB=$("$PY" -c "print(f'{$NEED * $N_TRIAL * 2 / 1e6:.2f}')" 2>/dev/null)
FISHER_SENS=$("$PY" -c "print(f'{1/($N_TRIAL**0.5):.3f}')" 2>/dev/null)
FISHER_GAIN=$("$PY" -c "print(f'{$N_TRIAL**0.5:.1f}')" 2>/dev/null)
PAIRS_PER_TRIAL=$((M*(M-1)/2))
PAIRS_TOTAL=$((PAIRS_PER_TRIAL * N_TRIAL))

# Build dist_stats.json
"$PY" - <<PYEOF > "$RUN_DIR/dist_stats.json" 2>"$RUN_DIR/dist_stats.err"
import statistics as S, json, os
def load(p):
    if not os.path.exists(p): return []
    return [int(l.strip()) for l in open(p) if l.strip()]
out = {}
for name in ['anu_pool_plugin','prng_pool_plugin','anu_pool_ksg','prng_pool_ksg']:
    v = load('$RUN_DIR/' + name + '.txt')
    if not v:
        out[name] = {'n': 0}
        continue
    m = S.mean(v); s = S.pstdev(v) if len(v) > 1 else 0
    if s > 0 and len(v) > 2:
        skew = sum(((x-m)/s)**3 for x in v) / len(v)
    else:
        skew = 0
    out[name] = {'n': len(v), 'mean_scaled': round(m,1), 'std_scaled': round(s,1),
                 'skew': round(skew, 4), 'min': min(v), 'max': max(v)}
print(json.dumps(out, indent=2))
PYEOF

DIST_JSON=$(cat "$RUN_DIR/dist_stats.json" 2>/dev/null || echo "{}")

# Build interpretation
INTERP=$("$PY" - <<PYEOF 2>/dev/null
vals = {
    'Fisher(plug-in, N=$N_TRIAL)': $FISHER_P_PLUGIN if '$FISHER_P_PLUGIN' != 'NA' else -1,
    'Fisher(ksg-lite, N=$N_TRIAL)': $FISHER_P_KSG if '$FISHER_P_KSG' != 'NA' else -1,
    'Pooled KS(plug-in)': $POOL_P_PLUGIN if '$POOL_P_PLUGIN' != 'NA' else -1,
    'Pooled KS(ksg-lite)': $POOL_P_KSG if '$POOL_P_KSG' != 'NA' else -1,
}
for name, p in vals.items():
    if p < 0:
        print(f"- {name}: 데이터 누락")
        continue
    pf = p / 1000.0
    if p < 50:
        print(f"- * {name}: p={pf:.4f} < 0.05 -> H0 reject - ANU != PRNG signal")
    elif p < 100:
        print(f"- {name}: p={pf:.4f} < 0.1 -> borderline (alpha=0.1)")
    elif p < 200:
        print(f"- {name}: p={pf:.4f} < 0.2 -> weak trend (not significant)")
    else:
        print(f"- {name}: p={pf:.4f} -> H0 maintain (noise)")
PYEOF
)

# Next phase recommendation
NEXT_PHASE=$("$PY" - <<PYEOF 2>/dev/null
fp = $FISHER_P_PLUGIN if '$FISHER_P_PLUGIN' != 'NA' else -1
pp = $POOL_P_PLUGIN if '$POOL_P_PLUGIN' != 'NA' else -1
fk = $FISHER_P_KSG if '$FISHER_P_KSG' != 'NA' else -1
any_sig = any(0 <= x < 50 for x in [fp, pp, fk])
any_border = any(0 <= x < 200 for x in [fp, pp, fk])
if any_sig:
    print("- * Fisher or pooled KS p<0.05 ANU-PRNG real difference candidate - Phase 2: per-universe full-ANU seeding (multi-call ANU API), true KSG k-NN estimator, Bell-like commutation test.")
elif any_border:
    print("- Weak/borderline. Phase 1.5: N_trial=50~100 (Fisher sensitivity^), or T=10000 M=100+ hetzner.")
else:
    print("- Noise level. Phase 2: dynamic quantile binning (remove static 4-bin artifact), true KSG k-NN, M=200 T=10000 hetzner.")
PYEOF
)

cat > "$RUN_DIR/summary.md" <<EOF
# NEXUS-6 ★18 Quantum Multiverse Interferometer Phase 1 — $TS

## Config
- M=$M universes, T=$T steps, dim=$DIM, N_trial=$N_TRIAL
- pairs/trial = $PAIRS_PER_TRIAL
- total pairs pooled (per source × estimator) = $PAIRS_TOTAL
- bytes/seed = $NEED (${TOTAL_MB} MB total)
- ANU source: $( [ -n "$ANU_HEX" ] && echo "first $ANU_LEN_BYTES bytes ANU QRNG per trial, rest urandom-extended" || echo "(skipped, urandom both)" )
- theoretical finite-sample bias: plug-in 4-bin (B-1)/(2T) = $BIAS_PLUGIN, ksg-lite 8-bin Miller-Madow corrected (residual ~$BIAS_KSG)

## Phase 0 vs Phase 1
| metric | Phase 0 | Phase 1 |
|--------|---------|---------|
| M | 10 | $M |
| T | 200 | $T |
| dim | 64 | $DIM |
| trials | 1 | $N_TRIAL |
| pairs total | 45 | $PAIRS_TOTAL |
| plug-in bias (theor) | 0.0075 | $BIAS_PLUGIN |
| single KS p | 0.218 | $POOL_P_PLUGIN_F (pooled plug-in) |

## Fisher combined p-values (N=$N_TRIAL trial KS p's)
| estimator | Fisher X² (scaled) | df | Fisher p (scaled) | Fisher p |
|-----------|--------------------|----|-------------------|----------|
| plug-in | $FISHER_X2_PLUGIN | $((2*N_TRIAL)) | $FISHER_P_PLUGIN | $FISHER_P_PLUGIN_F |
| ksg-lite | $FISHER_X2_KSG | $((2*N_TRIAL)) | $FISHER_P_KSG | $FISHER_P_KSG_F |

## Pooled KS (single large-sample test on all $PAIRS_TOTAL pairs)
| estimator | D | λ | p (scaled) | p |
|-----------|---|---|------------|---|
| plug-in | $POOL_D_PLUGIN_F | $POOL_L_PLUGIN_F | $POOL_P_PLUGIN | $POOL_P_PLUGIN_F |
| ksg-lite | $POOL_D_KSG_F | $POOL_L_KSG_F | $POOL_P_KSG | $POOL_P_KSG_F |

## Distribution statistics (pooled, scaled ×1000)

\`\`\`json
$DIST_JSON
\`\`\`

## Interpretation
$INTERP

## Next phase recommendation
$NEXT_PHASE

## 출력 파일
- \`trials.jsonl\` — per-trial KS 결과 ($((2*N_TRIAL)) lines: N_trial × 2 estimators)
- \`trial_stats.jsonl\` — per-trial source stats ($((2*N_TRIAL)) lines: N_trial × {anu,prng})
- \`mi_distributions.csv\` — all pairwise MI values (trial,source,estimator,value)
- \`fisher_plugin.json\`, \`fisher_ksg.json\` — Fisher 합성 p-value
- \`pooled_ks_plugin.jsonl\`, \`pooled_ks_ksg.jsonl\` — 풀드 KS 결과
- \`dist_stats.json\` — 풀 분포 통계 (mean/std/skew/min/max)
- \`anu_pool_*.txt\`, \`prng_pool_*.txt\` — 풀드 raw 값
- \`trials/trial_<i>_<tag>_<est>.txt\` — 각 trial MI 벡터
- \`seeds/trial_<i>_<tag>.txt\` — 각 trial seed (debugging/reproducibility)

## 제약 (honest)
- ANU $ANU_LEN_BYTES-byte head-seed only (rate-limit 회피). "ANU vs PRNG" 실질은 "ANU-head+urandom-tail vs urandom-full".
- ksg-lite 는 rank-based 8-bin + Miller-Madow 보정 (참 KSG k-NN 아님). bias 특성은 plug-in 과 다르지만 완전 독립 validation 은 아님.
- N_trial=$N_TRIAL 에서 Fisher 민감도 ~ $FISHER_SENS, single KS 대비 $FISHER_GAIN 배 gain.
- 메모리: 각 trial M × T = $((M*T)) energy samples, 피크 <200MB.

## 실행시간
- 총 elapsed: $(($(date +%s) - START_TIME))s
EOF

echo "[runner] done. summary: $RUN_DIR/summary.md"
cat "$RUN_DIR/summary.md"
