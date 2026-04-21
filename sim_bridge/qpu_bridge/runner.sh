#!/bin/bash
# runner.sh — QPU bridge demo: 10× VQE per noise mode, summary + KS test.
#
# Usage: ./runner.sh [repeats=10] [max_iter=50]
#
# Output:
#   runs/<ts>/run_<mode>_<seed>.json   per repeat
#   runs/<ts>/summary.json             mean/std/ks_test across modes
#   runs/<ts>/runner.log               combined log

set -u
REPEATS="${1:-10}"
MAX_ITER="${2:-50}"

if [ "$REPEATS" -gt 50 ]; then REPEATS=50; fi
if [ "$REPEATS" -lt 1 ]; then REPEATS=1; fi

BASE="$(cd "$(dirname "$0")" && pwd)"
TS="$(date +%Y%m%d-%H%M%S)"
OUTDIR="$BASE/runs/$TS"
mkdir -p "$OUTDIR"

PYBIN="/opt/homebrew/bin/python3.12"
export HEXA_LOCAL=1
export GATE_LOCAL=1

echo "[runner] ts=$TS repeats=$REPEATS max_iter=$MAX_ITER" | tee "$OUTDIR/runner.log"
echo "[runner] outdir=$OUTDIR" | tee -a "$OUTDIR/runner.log"
echo "[runner] python=$PYBIN" | tee -a "$OUTDIR/runner.log"

# Hard wall: each run ~10-15s → 3*10*15 = 450s worst, cap 30min
for MODE in none depol anu; do
    for SEED in $(seq 1 "$REPEATS"); do
        echo "[runner] mode=$MODE seed=$SEED" | tee -a "$OUTDIR/runner.log"
        timeout 120 "$PYBIN" "$BASE/vqe_h2_demo.py" \
            --mode "$MODE" --seed "$SEED" \
            --max-iter "$MAX_ITER" --outdir "$OUTDIR" \
            >>"$OUTDIR/runner.log" 2>&1
        RC=$?
        echo "[runner]   exit=$RC" | tee -a "$OUTDIR/runner.log"
        if [ "$RC" -ne 0 ]; then
            echo "[runner] WARN: run failed — continuing" | tee -a "$OUTDIR/runner.log"
        fi
    done
done

echo "[runner] aggregating…" | tee -a "$OUTDIR/runner.log"

"$PYBIN" - <<PYEOF | tee -a "$OUTDIR/runner.log"
import json, glob, os, sys
from pathlib import Path
import numpy as np
from scipy.stats import ks_2samp, ttest_ind

outdir = Path("$OUTDIR")
records = {"none": [], "depol": [], "anu": []}
for path in sorted(outdir.glob("run_*.json")):
    try:
        rec = json.loads(path.read_text())
    except Exception:
        continue
    mode = rec.get("mode")
    if mode in records:
        records[mode].append(rec)

summary = {"ts": "$TS", "repeats": $REPEATS, "max_iter": $MAX_ITER, "modes": {}}
for mode, recs in records.items():
    if not recs:
        summary["modes"][mode] = {"n": 0}
        continue
    energies = np.array([r["final_energy"] for r in recs])
    niters = np.array([r["n_iters"] for r in recs])
    errs = np.array([r["error_vs_exact"] for r in recs])
    sources = sorted(set(r.get("source", "?") for r in recs))
    summary["modes"][mode] = {
        "n": len(recs),
        "mean_energy": float(np.mean(energies)),
        "std_energy": float(np.std(energies, ddof=1)) if len(energies) > 1 else 0.0,
        "min_energy": float(np.min(energies)),
        "max_energy": float(np.max(energies)),
        "mean_err_vs_exact": float(np.mean(errs)),
        "std_err_vs_exact": float(np.std(errs, ddof=1)) if len(errs) > 1 else 0.0,
        "mean_niters": float(np.mean(niters)),
        "sources": sources,
    }

# pairwise KS tests
pairs = [("none", "depol"), ("none", "anu"), ("depol", "anu")]
summary["ks_tests"] = {}
summary["t_tests"] = {}
for a, b in pairs:
    ea = np.array([r["final_energy"] for r in records[a]])
    eb = np.array([r["final_energy"] for r in records[b]])
    if len(ea) >= 2 and len(eb) >= 2:
        ks = ks_2samp(ea, eb)
        tt = ttest_ind(ea, eb, equal_var=False)
        summary["ks_tests"][f"{a}_vs_{b}"] = {
            "statistic": float(ks.statistic),
            "pvalue": float(ks.pvalue),
        }
        summary["t_tests"][f"{a}_vs_{b}"] = {
            "statistic": float(tt.statistic),
            "pvalue": float(tt.pvalue),
        }

sp = outdir / "summary.json"
sp.write_text(json.dumps(summary, indent=2))
print(f"[summary] wrote {sp}")
print(json.dumps(summary, indent=2))
PYEOF

echo "[runner] done. artifacts in $OUTDIR" | tee -a "$OUTDIR/runner.log"
ls -la "$OUTDIR" | tee -a "$OUTDIR/runner.log"
