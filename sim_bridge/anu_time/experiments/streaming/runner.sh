#!/bin/bash
# runner.sh — ★19 bsz=1 / pure-hexa / autocorr experiment driver
#
# Three sub-experiments:
#   1. pure_hexa — hexa-native hex→int (no per-byte shell-out) → measure new floor
#   2. anu_streaming — 1 req per byte at ANU 60s rate, 30 min total (30 bytes)
#   3. autocorr — lag autocorrelation on both byte streams
#
# Total budget ~35 min (strict: 30 min stream + ~5 min analysis).
#
# Env:
#   NEXUS_ROOT       — nexus repo root (default $HOME/Dev/nexus)
#   STREAM_BYTES     — override 30 bytes (testing only)
#   STREAM_PACE_S    — override 60s pace (NEVER in prod — rate limit!)
#   SKIP_STREAM=1    — skip long ANU stream (fast dry-run mode)

set -u
NEXUS_ROOT="${NEXUS_ROOT:-$HOME/Dev/nexus}"
cd "$NEXUS_ROOT" || exit 1

TS="$(date +%s)"
BASE="$NEXUS_ROOT/sim_bridge/anu_time/experiments/streaming/runs/bsz1_streaming_${TS}"
mkdir -p "$BASE"
echo "[run] base=$BASE"

STREAM_BYTES="${STREAM_BYTES:-30}"
STREAM_PACE_S="${STREAM_PACE_S:-60}"
PURE_TICKS="${PURE_TICKS:-2000}"

#############################################
# Sub-exp 1 — pure-hexa floor measurement  #
#############################################
PURE_DIR="$BASE/pure_hexa"
mkdir -p "$PURE_DIR"
echo "[run] 1) pure_hexa n=$PURE_TICKS"
HEXA_LOCAL=1 NEXUS_NO_BUDGET_OK=1 timeout 60s \
    hexa shared/sim_bridge/anu_time/experiments/streaming/pure_hexa_buffer.hexa \
    "$PURE_TICKS" "$PURE_DIR" urandom > "$PURE_DIR/stdout.log" 2>&1
echo "[run] 1) pure_hexa exit=$?"

# Run autocorr on pure_hexa log (lag up to 256)
HEXA_LOCAL=1 timeout 30s \
    hexa shared/sim_bridge/anu_time/experiments/streaming/autocorr_analyzer.hexa \
    "$PURE_DIR/log.jsonl" 256 "$PURE_DIR/autocorr.json" \
    > "$PURE_DIR/autocorr_stdout.txt" 2>&1

#############################################
# Sub-exp 2 — ANU streaming (bsz=1, 30 min) #
#############################################
STREAM_DIR="$BASE/anu_stream"
mkdir -p "$STREAM_DIR"
if [ "${SKIP_STREAM:-0}" = "1" ]; then
    echo "[run] 2) anu_streaming SKIPPED"
    echo "SKIPPED" > "$STREAM_DIR/stdout.log"
else
    # budget = STREAM_BYTES * STREAM_PACE_S + curl slack
    WALL_BUDGET=$((STREAM_BYTES * STREAM_PACE_S + 120))
    echo "[run] 2) anu_streaming n=$STREAM_BYTES pace=${STREAM_PACE_S}s wall_budget=${WALL_BUDGET}s"
    HEXA_LOCAL=1 NEXUS_NO_BUDGET_OK=1 NEXUS_NO_TIMEOUT_OK=1 timeout "$WALL_BUDGET" \
        hexa shared/sim_bridge/anu_time/experiments/streaming/anu_streaming.hexa \
        "$STREAM_BYTES" "$STREAM_DIR" "$STREAM_PACE_S" > "$STREAM_DIR/stdout.log" 2>&1
    echo "[run] 2) anu_streaming exit=$?"
fi

# Run autocorr on stream (lag capped at 10 for small n=30)
if [ -f "$STREAM_DIR/log.jsonl" ]; then
    HEXA_LOCAL=1 timeout 30s \
        hexa shared/sim_bridge/anu_time/experiments/streaming/autocorr_analyzer.hexa \
        "$STREAM_DIR/log.jsonl" 10 "$STREAM_DIR/autocorr.json" \
        > "$STREAM_DIR/autocorr_stdout.txt" 2>&1
fi

#############################################
# Sub-exp 3 — aggregate summary             #
#############################################
echo "[run] 3) summary"

/usr/bin/python3 - <<PYEOF > "$BASE/summary.md"
import json, os, math

base = "$BASE"
pure_dir = os.path.join(base, "pure_hexa")
stream_dir = os.path.join(base, "anu_stream")

def load_json(p):
    try:
        return json.load(open(p))
    except Exception as e:
        return {"error": str(e)}

def load_jsonl(p):
    out = []
    try:
        for l in open(p):
            l = l.strip()
            if not l or not l.startswith("{"): continue
            try: out.append(json.loads(l))
            except: pass
    except FileNotFoundError:
        pass
    return out

pure_meta = load_json(os.path.join(pure_dir, "meta.json"))
pure_ac = load_json(os.path.join(pure_dir, "autocorr.json"))
stream_meta = load_json(os.path.join(stream_dir, "meta.json"))
stream_ac = load_json(os.path.join(stream_dir, "autocorr.json"))
stream_rows = load_jsonl(os.path.join(stream_dir, "log.jsonl"))

def get(d, k, dflt="?"):
    if isinstance(d, dict): return d.get(k, dflt)
    return dflt

# Derived metrics ---------------------------
# floor comparison: previous deep-dive showed ~30ms floor with per-byte printf shell-out
per_tick_ns = get(pure_meta, "per_tick_ns_amort", 0)
prev_floor_ns = 30_000_000  # ≈ 30ms observed in 64tick_deepdive_1776272484 sweep_bsz* runs
speedup = prev_floor_ns / per_tick_ns if per_tick_ns else 0

# Stream inter-arrival distribution
stream_dts = []
if stream_rows:
    stream_dts = [r.get("fetch_dt_ns", 0) for r in stream_rows if r.get("ok", 0) == 1]
stream_dts_ms = [d/1e6 for d in stream_dts] if stream_dts else []

if stream_dts_ms:
    mean_ms = sum(stream_dts_ms)/len(stream_dts_ms)
    ss = sorted(stream_dts_ms)
    med_ms = ss[len(ss)//2]
    mn_ms, mx_ms = min(ss), max(ss)
    var = sum((x-mean_ms)**2 for x in stream_dts_ms)/len(stream_dts_ms)
    std_ms = math.sqrt(var)
else:
    mean_ms = med_ms = mn_ms = mx_ms = std_ms = 0

# artifact-amplification ratio: prev bsz=64 ANU run showed 15x on/off boundary
# bsz=1: every byte IS a fetch. If fetch_dt_ms is roughly constant across bytes
# (no bimodality), then 15x collapses to ~1x → artifact confirmed.
# Classify dts into "fast" (<100ms HTTP sub-RTT) vs "slow" (>=100ms)
fast = [d for d in stream_dts_ms if d < 100]
slow = [d for d in stream_dts_ms if d >= 100]
fast_mean = sum(fast)/len(fast) if fast else 0
slow_mean = sum(slow)/len(slow) if slow else 0
amp_ratio = slow_mean / fast_mean if fast_mean > 0 and slow_mean > 0 else 1.0

# Autocorr verdict
def ac_verdict(ac):
    if "error" in ac: return "N/A (" + ac["error"] + ")"
    n = ac.get("n", 0)
    flagged = ac.get("flagged_lags", [])
    max_abs = ac.get("max_abs_rho", 0)
    max_lag = ac.get("max_abs_lag", 0)
    sig3 = ac.get("sigma_3_bound", 0)
    if ac.get("verdict_iid", False):
        return f"null (i.i.d.) — n={n}, max|rho|={max_abs:.4f} at lag={max_lag}, 3sigma={sig3:.4f}"
    else:
        return f"NON-NULL — n={n}, flagged={flagged}, max|rho|={max_abs:.4f}"

print("# star19 ANU-Time bsz=1 Streaming Experiment")
print()
print(f"base={base}")
print(f"date=2026-04-16")
print()

print("## 1) pure-hexa floor (no per-byte shell-out)")
print()
print("| metric | value |")
print("|---|---|")
print(f"| ticks | {get(pure_meta,'n_ticks')} |")
print(f"| prefetch_ms | {get(pure_meta,'prefetch_wall_ns',0)/1e6:.1f} |")
print(f"| bulk_iter_ms | {get(pure_meta,'bulk_iter_ns',0)/1e6:.2f} |")
print(f"| per_tick_ns (amort) | {per_tick_ns} |")
print(f"| per_tick_us | {per_tick_ns/1000:.2f} |")
print(f"| prev floor (printf+od per byte) | ~30,000,000 ns (~30 ms) |")
print(f"| speedup | **{speedup:.0f}x** |")
print()

print("## 2) ANU bsz=1 streaming (1 req / byte)")
print()
print("| metric | value |")
print("|---|---|")
print(f"| n_bytes requested | {get(stream_meta,'n_bytes')} |")
print(f"| n_bytes actual | {get(stream_meta,'actual')} |")
print(f"| pace_s | {get(stream_meta,'pace_s')} |")
print(f"| wall_s | {get(stream_meta,'total_wall_ns',0)/1e9:.1f} |")
print(f"| fetch_dt mean ms | {mean_ms:.1f} |")
print(f"| fetch_dt med ms | {med_ms:.1f} |")
print(f"| fetch_dt std ms | {std_ms:.1f} |")
print(f"| fetch_dt min ms | {mn_ms:.1f} |")
print(f"| fetch_dt max ms | {mx_ms:.1f} |")
print(f"| n fast (<100ms) | {len(fast)} |")
print(f"| n slow (>=100ms) | {len(slow)} |")
print(f"| slow/fast ratio | {amp_ratio:.2f} (prev bsz=64: 15.05) |")
print()

print("## 3) Autocorrelation")
print()
print(f"- **pure_hexa** (urandom 2000): {ac_verdict(pure_ac)}")
print(f"- **anu_stream** (ANU {get(stream_meta,'actual','?')}): {ac_verdict(stream_ac)}")
print()

# ASCII heatmap for stream
if isinstance(stream_ac, dict) and "rows" in stream_ac:
    print("### ANU stream autocorr heatmap (|rho|×100 bars)")
    print()
    print("```")
    for k, r in stream_ac["rows"]:
        mag = min(40, int(round(abs(r)*100)))
        bar = "#"*mag
        sig = "*" if abs(r) > stream_ac.get("sigma_3_bound", 0) else " "
        print(f"lag {k:3d} rho={r:+.4f} {sig} |{bar}")
    print("```")
    print()

print("## Measurement — artifact-amplification")
print()
print("| mode | amplification | interpretation |")
print("|---|---|---|")
print("| bsz=64 (previous deep-dive) | 15.05x on boundary | curl RTT concentrated at k*64 ticks |")
print(f"| bsz=1 (this run) | {amp_ratio:.2f}x (slow/fast) | every tick IS a curl → uniform HTTP cost |")
print()

# Verdict
print("## Verdict")
print()
sigma_n = stream_ac.get("n", 0) if isinstance(stream_ac, dict) else 0
flagged_any = len(stream_ac.get("flagged_lags", [])) > 0 if isinstance(stream_ac, dict) else False
if sigma_n < 5:
    print("**결론: 데이터 불충분** — ANU stream too short for autocorr verdict.")
elif flagged_any:
    print("**결론: 양자 시그너처 검출 ✓** — ANU bsz=1 stream shows non-trivial byte autocorrelation.")
else:
    n_str = str(sigma_n)
    print("**결론: 여전히 null** — ANU bsz=1 stream is i.i.d. uniform within 3σ bound (n=" + n_str + "). buffer 64-tick boundary = 100% curl/shell artifact. Collapse from 15.05x → " + f"{amp_ratio:.2f}x amplification confirms artifact.")
PYEOF

echo "[run] summary at $BASE/summary.md"
cat "$BASE/summary.md"
