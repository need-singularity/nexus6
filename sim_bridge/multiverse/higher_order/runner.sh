#!/bin/bash
# sim_bridge/multiverse/higher_order/runner.sh
#   NEXUS-6 ★18 Multiverse — higher-order MI exploration (3-way, 4-way, TC)
#
# Pairwise MI gave KS p=0.218 (null). Test whether 3-way / 4-way interaction
# information or total correlation is more sensitive to ANU vs PRNG seed source.
#
# Pipeline:
#   1. Build seed files (ANU and PRNG) — same mechanism as Phase 0 runner.sh.
#   2. Run interferometer (existing, parent dir) twice → trajectories.jsonl.
#   3. Run triple_mi / quad_mi / total_correlation on each trajectory set.
#   4. Feed MI values to compare_ks.hexa → KS JSON per statistic.
#   5. Emit summary.md comparing pairwise/3-way/4-way/TC p-values.
#
# Defaults: M=20 T=500 DIM=32, quad sub-sample=1000 if time-constrained.
# Timeout: 30min total (no individual op > 10min).
#
# H-NOBLOCK/H-NOHOOK/H-NOARCHIVE: no hooks, no bak files, no sleeps.

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARENT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
HEXA="${HEXA:-$HOME/Dev/nexus/bin/hexa}"
M="${M:-20}"
T="${T:-500}"
DIM="${DIM:-32}"
QUAD_SUB="${QUAD_SUB:-1000}"    # sub-sample for quad if C(M,4) > this

TS="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="$SCRIPT_DIR/runs/highorder_$TS"
mkdir -p "$RUN_DIR/anu" "$RUN_DIR/prng"

NEED=$((M * (DIM + T)))
echo "[higherorder] config: M=$M T=$T DIM=$DIM bytes_needed=$NEED"
echo "[higherorder] run_dir=$RUN_DIR"

# ----- 1. Seed files -----
PRNG_SEED="$RUN_DIR/prng_seed.txt"
head -c "$NEED" /dev/urandom | od -An -vtu1 | tr -s ' \n' ' ' > "$PRNG_SEED"
echo "[higherorder] prng seed: $(wc -w < "$PRNG_SEED") bytes"

ANU_SEED="$RUN_DIR/anu_seed.txt"
if [ "${SKIP_ANU:-0}" = "1" ]; then
  echo "[higherorder] SKIP_ANU=1 → ANU seed also urandom (dev mode)"
  head -c "$NEED" /dev/urandom | od -An -vtu1 | tr -s ' \n' ' ' > "$ANU_SEED"
else
  ANU_CACHE="$HOME/Dev/nexus/discovery/rng_lab/.anu_cache.bin"
  if [ ! -f "$ANU_CACHE" ]; then
    echo "[higherorder] WARN: no ANU cache — attempting fresh fetch"
    HEXA_LOCAL=1 "$HEXA" "$HOME/Dev/nexus/discovery/rng_lab/fetch_anu.hexa" info >/dev/null 2>&1 || true
  fi
  if [ -f "$ANU_CACHE" ]; then
    ANU_HEX="$(tr -d '\n ' < "$ANU_CACHE")"
    ANU_LEN_BYTES=$((${#ANU_HEX} / 2))
    echo "[higherorder] ANU cache bytes: $ANU_LEN_BYTES"
    /usr/bin/python3 -c "
h = '$ANU_HEX'
decs = [str(int(h[i:i+2], 16)) for i in range(0, len(h), 2)]
if $NEED > len(decs):
    with open('/dev/urandom', 'rb') as f:
        extra = f.read($NEED - len(decs))
    decs.extend(str(b) for b in extra)
print(' '.join(decs[:$NEED]))
" > "$ANU_SEED"
    echo "[higherorder] anu seed: $(wc -w < "$ANU_SEED") bytes (first $ANU_LEN_BYTES ANU, rest urandom)"
  else
    echo "[higherorder] ANU cache missing — fallback urandom"
    head -c "$NEED" /dev/urandom | od -An -vtu1 | tr -s ' \n' ' ' > "$ANU_SEED"
  fi
fi

# ----- 2. Generate trajectories (reuse parent interferometer) -----
echo "[higherorder] generating ANU trajectories..."
HEXA_LOCAL=1 "$HEXA" "$PARENT_DIR/interferometer.hexa" anu "$ANU_SEED" "$M" "$T" "$DIM" "$RUN_DIR/anu" 2>&1 | tail -5

echo "[higherorder] generating PRNG trajectories..."
HEXA_LOCAL=1 "$HEXA" "$PARENT_DIR/interferometer.hexa" prng "$PRNG_SEED" "$M" "$T" "$DIM" "$RUN_DIR/prng" 2>&1 | tail -5

ANU_TRAJ="$RUN_DIR/anu/trajectories.jsonl"
PRNG_TRAJ="$RUN_DIR/prng/trajectories.jsonl"

# ----- 3. Compute higher-order MI per source -----
# 3-way MI
echo "[higherorder] 3-way MI (ANU)..."
HEXA_LOCAL=1 "$HEXA" "$SCRIPT_DIR/triple_mi.hexa" "$ANU_TRAJ" "$RUN_DIR/anu/triples.csv" 2>&1 | tail -3
echo "[higherorder] 3-way MI (PRNG)..."
HEXA_LOCAL=1 "$HEXA" "$SCRIPT_DIR/triple_mi.hexa" "$PRNG_TRAJ" "$RUN_DIR/prng/triples.csv" 2>&1 | tail -3

# 4-way MI (with sub-sample if needed)
QUAD_TOTAL=$((M * (M-1) * (M-2) * (M-3) / 24))
echo "[higherorder] C(M,4) = $QUAD_TOTAL"
if [ "$QUAD_TOTAL" -gt "$QUAD_SUB" ]; then
  QUAD_ARGS="--sub-sample $QUAD_SUB"
  echo "[higherorder] sub-sampling quads to ~$QUAD_SUB"
else
  QUAD_ARGS=""
fi
echo "[higherorder] 4-way MI (ANU)..."
HEXA_LOCAL=1 "$HEXA" "$SCRIPT_DIR/quad_mi.hexa" "$ANU_TRAJ" "$RUN_DIR/anu/quads.csv" $QUAD_ARGS 2>&1 | tail -3
echo "[higherorder] 4-way MI (PRNG)..."
HEXA_LOCAL=1 "$HEXA" "$SCRIPT_DIR/quad_mi.hexa" "$PRNG_TRAJ" "$RUN_DIR/prng/quads.csv" $QUAD_ARGS 2>&1 | tail -3

# Total correlation, k=3 and k=4
echo "[higherorder] TC k=3 (ANU)..."
HEXA_LOCAL=1 "$HEXA" "$SCRIPT_DIR/total_correlation.hexa" "$ANU_TRAJ" "$RUN_DIR/anu/tc_k3.csv" --k 3 2>&1 | tail -3
echo "[higherorder] TC k=3 (PRNG)..."
HEXA_LOCAL=1 "$HEXA" "$SCRIPT_DIR/total_correlation.hexa" "$PRNG_TRAJ" "$RUN_DIR/prng/tc_k3.csv" --k 3 2>&1 | tail -3

echo "[higherorder] TC k=4 (ANU)..."
HEXA_LOCAL=1 "$HEXA" "$SCRIPT_DIR/total_correlation.hexa" "$ANU_TRAJ" "$RUN_DIR/anu/tc_k4.csv" --k 4 --n-samples "$QUAD_SUB" 2>&1 | tail -3
echo "[higherorder] TC k=4 (PRNG)..."
HEXA_LOCAL=1 "$HEXA" "$SCRIPT_DIR/total_correlation.hexa" "$PRNG_TRAJ" "$RUN_DIR/prng/tc_k4.csv" --k 4 --n-samples "$QUAD_SUB" 2>&1 | tail -3

# ----- 4. Extract value columns, run KS -----
# helper: extract last column (I_scaled or TC_scaled) skipping header
extract_vals() {
  local infile="$1"
  local outfile="$2"
  tail -n +2 "$infile" | awk -F, '{ print $NF }' > "$outfile"
}

extract_vals "$RUN_DIR/anu/triples.csv"  "$RUN_DIR/anu/triples_vals.txt"
extract_vals "$RUN_DIR/prng/triples.csv" "$RUN_DIR/prng/triples_vals.txt"
extract_vals "$RUN_DIR/anu/quads.csv"    "$RUN_DIR/anu/quads_vals.txt"
extract_vals "$RUN_DIR/prng/quads.csv"   "$RUN_DIR/prng/quads_vals.txt"
extract_vals "$RUN_DIR/anu/tc_k3.csv"    "$RUN_DIR/anu/tc_k3_vals.txt"
extract_vals "$RUN_DIR/prng/tc_k3.csv"   "$RUN_DIR/prng/tc_k3_vals.txt"
extract_vals "$RUN_DIR/anu/tc_k4.csv"    "$RUN_DIR/anu/tc_k4_vals.txt"
extract_vals "$RUN_DIR/prng/tc_k4.csv"   "$RUN_DIR/prng/tc_k4_vals.txt"

echo "[higherorder] KS triples..."
HEXA_LOCAL=1 "$HEXA" "$PARENT_DIR/compare_ks.hexa" "$RUN_DIR/anu/triples_vals.txt" "$RUN_DIR/prng/triples_vals.txt" "$RUN_DIR/ks_triples.json" 2>&1 | tail -4
echo "[higherorder] KS quads..."
HEXA_LOCAL=1 "$HEXA" "$PARENT_DIR/compare_ks.hexa" "$RUN_DIR/anu/quads_vals.txt" "$RUN_DIR/prng/quads_vals.txt" "$RUN_DIR/ks_quads.json" 2>&1 | tail -4
echo "[higherorder] KS TC k=3..."
HEXA_LOCAL=1 "$HEXA" "$PARENT_DIR/compare_ks.hexa" "$RUN_DIR/anu/tc_k3_vals.txt" "$RUN_DIR/prng/tc_k3_vals.txt" "$RUN_DIR/ks_tc_k3.json" 2>&1 | tail -4
echo "[higherorder] KS TC k=4..."
HEXA_LOCAL=1 "$HEXA" "$PARENT_DIR/compare_ks.hexa" "$RUN_DIR/anu/tc_k4_vals.txt" "$RUN_DIR/prng/tc_k4_vals.txt" "$RUN_DIR/ks_tc_k4.json" 2>&1 | tail -4

# Also run pairwise MI with same M=20 T=500 for direct comparison
echo "[higherorder] pairwise KS (reuse Phase 0 mi_values from interferometer)..."
HEXA_LOCAL=1 "$HEXA" "$PARENT_DIR/compare_ks.hexa" "$RUN_DIR/anu/mi_values.txt" "$RUN_DIR/prng/mi_values.txt" "$RUN_DIR/ks_pairwise.json" 2>&1 | tail -4

# ----- 5. Consolidated ks_results.json + summary.md -----
/usr/bin/python3 - "$RUN_DIR" <<'PYEOF'
import sys, json, os
run_dir = sys.argv[1]

def load(name):
    p = os.path.join(run_dir, name)
    if not os.path.exists(p): return {}
    try:
        with open(p) as f: return json.loads(f.read())
    except Exception: return {}

sources = {
    "pairwise": load("ks_pairwise.json"),
    "triple":   load("ks_triples.json"),
    "quad":     load("ks_quads.json"),
    "tc_k3":    load("ks_tc_k3.json"),
    "tc_k4":    load("ks_tc_k4.json"),
}

merged = {
    "run_dir": run_dir,
    "note": "scaled × 1000, natural log (nats). p_scaled = ×1000 (p=0.050 → 50)",
    "stats": {},
}
for name, d in sources.items():
    if not d:
        merged["stats"][name] = {"status": "missing"}
        continue
    merged["stats"][name] = {
        "anu_n":  d.get("anu_n", "NA"),
        "prng_n": d.get("prng_n", "NA"),
        "anu_mean_scaled":  d.get("anu_mean_scaled", "NA"),
        "prng_mean_scaled": d.get("prng_mean_scaled", "NA"),
        "D_scaled":      d.get("D_scaled", "NA"),
        "lambda_scaled": d.get("lambda_scaled", "NA"),
        "p_scaled":      d.get("p_scaled", "NA"),
    }

with open(os.path.join(run_dir, "ks_results.json"), "w") as f:
    f.write(json.dumps(merged, indent=2))

# Summary.md
lines = []
lines.append(f"# NEXUS-6 star18 Multiverse — higher-order MI run {os.path.basename(run_dir)}")
lines.append("")
lines.append(f"Config: see run dir `{run_dir}`")
lines.append("")
lines.append("## KS 2-sample comparison (ANU vs PRNG)")
lines.append("")
lines.append("| statistic | n_anu | n_prng | mean(anu) | mean(prng) | D | lambda | p-value |")
lines.append("|-----------|-------|--------|-----------|------------|----|--------|---------|")
for name in ["pairwise","triple","quad","tc_k3","tc_k4"]:
    s = merged["stats"][name]
    if s.get("status") == "missing":
        lines.append(f"| {name} | - | - | - | - | - | - | MISSING |")
        continue
    def f(v):
        if v in ("NA", None): return "NA"
        try: return f"{int(v)/1000:.4f}"
        except Exception: return str(v)
    lines.append(f"| {name} | {s['anu_n']} | {s['prng_n']} | {f(s['anu_mean_scaled'])} | {f(s['prng_mean_scaled'])} | {f(s['D_scaled'])} | {f(s['lambda_scaled'])} | {f(s['p_scaled'])} |")

lines.append("")
lines.append("## Interpretation")
lines.append("")

# find smallest p
best = None
best_p = 1001
for name, s in merged["stats"].items():
    p = s.get("p_scaled", "NA")
    if p in ("NA", None): continue
    try:
        pi = int(p)
    except Exception:
        continue
    if pi < best_p:
        best_p = pi
        best = name

if best is None:
    lines.append("- (no valid KS results)")
elif best_p < 50:
    lines.append(f"- **고차 MI 에 신호 있음 checkmark** — `{best}` 에서 p={best_p/1000:.4f} < 0.05.")
elif best_p < 100:
    lines.append(f"- 경계 신호 — `{best}` p={best_p/1000:.4f} (<0.1). 샘플 확대 필요.")
else:
    lines.append(f"- **여전히 null** — 가장 작은 p={best_p/1000:.4f} ({best}). 고차 MI 도 ANU vs PRNG 구분 못함.")

lines.append("")
lines.append("## Caveats")
lines.append("- binary / 3-bin quantization → bias O(bins^k / 2T). null-comparison 이 이를 흡수.")
lines.append("- ANU 64-byte cache, rest urandom 확장 (honest mixing).")
lines.append("- quad / tc_k4 는 sub-sample 된 값일 수 있음 (QUAD_SUB 이하).")

with open(os.path.join(run_dir, "summary.md"), "w") as f:
    f.write("\n".join(lines) + "\n")

print("[higherorder] wrote ks_results.json + summary.md")
PYEOF

echo "[higherorder] done."
echo ""
cat "$RUN_DIR/summary.md"
