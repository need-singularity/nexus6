#!/bin/bash
# runner.sh — ★19 64-tick boundary deep-dive experiment driver
#
# Runs:
#   1. bufsize_sweep: 32/64/128/256 × 500 ticks urandom
#   2. multi_source: urandom vs anu_then_urandom at bufsize=64 × 300 ticks
#   3. long_run: 3000 ticks urandom at bufsize=64
# Then aggregates into summary.md.

set -u
NEXUS_ROOT="${NEXUS_ROOT:-$HOME/Dev/nexus}"
cd "$NEXUS_ROOT" || exit 1

TS="$(date +%s)"
BASE="$NEXUS_ROOT/sim_bridge/anu_time/experiments/runs/64tick_deepdive_${TS}"
mkdir -p "$BASE"

echo "[dd] base=$BASE"

HEXA="HEXA_LOCAL=1 NEXUS_NO_BUDGET_OK=1 hexa"

run_sweep() {
    local bsz=$1
    local ticks=$2
    local src=$3
    local label=$4
    local dir="$BASE/$label"
    mkdir -p "$dir"
    echo "[dd] sweep bsz=$bsz ticks=$ticks src=$src → $label"
    HEXA_LOCAL=1 NEXUS_NO_BUDGET_OK=1 timeout 240s \
        hexa shared/sim_bridge/anu_time/experiments/boundary_sweep.hexa "$bsz" "$ticks" "$dir" "$src" \
        >"$dir/stdout.log" 2>&1
    local rc=$?
    echo "[dd] exit=$rc $label"
    # analysis
    HEXA_LOCAL=1 hexa shared/sim_bridge/anu_time/experiments/analyze_extras.hexa "$dir" \
        >"$dir/extras_stdout.txt" 2>&1
}

# ─── 1. buffer-size sweep (urandom only for speed + controlled cost) ───
run_sweep 32  500 urandom sweep_bsz32
run_sweep 64  500 urandom sweep_bsz64
run_sweep 128 500 urandom sweep_bsz128
run_sweep 256 500 urandom sweep_bsz256

# ─── 2. multi-source at bsz=64 ───
run_sweep 64 300 urandom          multi_urandom
run_sweep 64 200 anu_then_urandom multi_anu

# ─── 3. long run ───
run_sweep 64 3000 urandom long_3000

# ─── 4. aggregate ───
echo "[dd] aggregating summary"
/usr/bin/python3 <<PYEOF > "$BASE/summary.md"
import json, os, sys
base = "$BASE"
runs = ["sweep_bsz32","sweep_bsz64","sweep_bsz128","sweep_bsz256",
        "multi_urandom","multi_anu","long_3000"]
rows=[]
for r in runs:
    p=os.path.join(base,r,"extras.json")
    if not os.path.exists(p):
        rows.append({"run":r,"_error":"no extras.json"})
        continue
    try:
        rows.append({"run":r, **json.load(open(p))})
    except Exception as e:
        rows.append({"run":r,"_error":str(e)})

def row_cells(r):
    return [
        r["run"],
        str(r.get("bufsize","?")),
        str(r.get("n","?")),
        str(r.get("n_slow","?")),
        str(r.get("slow_period_gcd","?")),
        str(r.get("slow_gap_mean","?")),
        str(r.get("slow_gap_std","?")),
        str(r.get("slow_dt_mean_ns","?")),
        str(r.get("slow_dt_std_ns","?")),
        str(r.get("frac_slow_on_refresh_flag","?")),
        str(r.get("diff_L1_refreshed_mean","?")),
        str(r.get("diff_L1_normal_mean","?")),
        str(r.get("verdict_period_eq_bufsize","?")),
    ]

print("# ★19 ANU-Time 64-tick Boundary Deep-Dive — Summary")
print()
print(f"base={base}")
print()
print("## Per-run stats")
print()
print("| run | bufsize | n | n_slow | period_gcd | gap_mean | gap_std | slow_dt_mean_ns | slow_dt_std | frac_on_refresh | diff_ref | diff_norm | period==bufsize? |")
print("|-----|---------|---|--------|-----------|----------|---------|-----------------|-------------|-----------------|----------|-----------|------------------|")
for r in rows:
    if "_error" in r:
        print(f"| {r['run']} | ERR | {r['_error']} | | | | | | | | | | |")
        continue
    print("| " + " | ".join(row_cells(r)) + " |")

print()
print("## Slow-tick taus (first 20)")
print()
for r in rows:
    if "_error" in r: continue
    print(f"- **{r['run']}** (bsz={r.get('bufsize')}): taus={r.get('slow_taus_head')}  gaps={r.get('slow_gaps_head')}")

print()
print("## Sources per run")
for r in rows:
    if "_error" in r: continue
    print(f"- {r['run']}: {r.get('sources')}")

# Histogram of period==bufsize verdicts
verdicts=[r.get("verdict_period_eq_bufsize",None) for r in rows if "_error" not in r]
true_count = sum(1 for v in verdicts if v is True)
print()
print("## ASCII histogram: slow-tick period == bufsize?")
print()
print("```")
for r in rows:
    if "_error" in r: continue
    mark = "TRUE " if r.get("verdict_period_eq_bufsize") else "FALSE"
    bar = "#"*min(40, int(r.get("n_slow",0)))
    print(f"{r['run']:14s} bsz={r.get('bufsize'):>4} period={r.get('slow_period_gcd',0):>4} [{mark}] |{bar}")
print("```")

print()
# Verdict
print("## Verdict")
print()
if true_count >= 4:
    print("**CONCLUSION: 64-tick = artifact** — slow-tick period tracks internal byte buffer size exactly.")
elif true_count == 0:
    print("**CONCLUSION: 64-tick = feature** — slow-tick stays at 64 regardless of bufsize → possible ANU/quantum signature.")
else:
    print(f"**CONCLUSION: mixed** — {true_count}/{len(verdicts)} runs show period==bufsize. Weak artifact evidence.")
PYEOF

echo "[dd] summary at $BASE/summary.md"
cat "$BASE/summary.md"
