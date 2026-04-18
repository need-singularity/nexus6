#!/bin/bash
# replication_runner.sh — focused SR replication at higher n
#
# Tests: σ=0.1 peak vs baseline σ=0 at n≥50 per σ.
# Targets Fisher p<0.05 one-sided if SR is real.
#
# Usage:
#   SIGMAS_CSV="0,0.05,0.1,0.2" TRIALS=50 bash replication_runner.sh
#
# Output: runs/<ts>/stats.json + summary.md

set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

HEXA=/Users/ghost/Dev/nexus/shared/bin/hexa
export HEXA_LOCAL=1

SIGMAS_CSV="${SIGMAS_CSV:-0,0.05,0.1,0.2,0.3}"
TRIALS="${TRIALS:-50}"
GENS="${GENS:-6}"

IFS=',' read -ra SIGMAS <<< "$SIGMAS_CSV"

TS=$(date -u +%Y%m%d_%H%M%S)
OUT_DIR="$ROOT/runs/rep_$TS"
mkdir -p "$OUT_DIR"
LOG="$OUT_DIR/sweep.log"
STATS="$OUT_DIR/stats.json"

: > "$LOG"
echo "# replication start $TS" | tee -a "$LOG"
echo "# sigmas: ${SIGMAS[*]} trials=$TRIALS gens=$GENS" | tee -a "$LOG"

TOTAL=$(( ${#SIGMAS[@]} * TRIALS ))
START=$(date +%s)
IDX=0
for SIGMA in "${SIGMAS[@]}"; do
  for T in $(seq 0 $((TRIALS - 1))); do
    IDX=$((IDX+1))
    nice -n 19 "$HEXA" sweep_runner.hexa run "$T" "$SIGMA" "$GENS" 2>>"$LOG" | grep "^FINAL " >> "$LOG" || true
  done
  echo "  σ=$SIGMA done $IDX/$TOTAL $(($(date +%s) - START))s" | tee -a "$LOG"
done

echo "# done total=$(($(date +%s) - START))s" | tee -a "$LOG"

# Parse stats
python3 - "$LOG" "$STATS" "$OUT_DIR/summary.md" <<'PYEOF'
import sys, re, json
from collections import defaultdict

log, stats_path, summary_path = sys.argv[1], sys.argv[2], sys.argv[3]

rx = re.compile(r"FINAL TRIAL=(\d+) SIGMA=([\d.]+) GENS=(\d+) CONV=(\w+) BEST_YIELD=([-\d.]+) BEST_COMP=([-\d.]+) CYCLE_CONV=([-\d]+) RHO=([-\d.]+)")

by_sigma = defaultdict(list)
with open(log) as f:
    for ln in f:
        m = rx.search(ln)
        if not m: continue
        trial, sigma, gens, conv, yld, comp, cycle, rho = m.groups()
        by_sigma[float(sigma)].append({
            "trial": int(trial),
            "conv": conv == "true",
            "yield": float(yld),
            "comp": float(comp),
            "cycle": int(cycle),
            "rho": float(rho),
        })

rows = []
for sigma in sorted(by_sigma):
    recs = by_sigma[sigma]
    n = len(recs)
    conv_n = sum(1 for r in recs if r["conv"])
    cycles_conv = [r["cycle"] for r in recs if r["conv"]]
    rows.append({
        "sigma": sigma,
        "n": n,
        "conv": conv_n,
        "conv_rate": round(conv_n/n, 4) if n else 0,
        "mean_cycle": round(sum(cycles_conv)/len(cycles_conv), 4) if cycles_conv else -1,
        "mean_comp": round(sum(r["comp"] for r in recs)/n, 4) if n else 0,
        "std_comp": 0.0,
        "mean_yield": round(sum(r["yield"] for r in recs)/n, 4) if n else 0,
    })

with open(stats_path, "w") as f:
    json.dump(rows, f, indent=2)

# Fisher test vs σ=0 baseline
try:
    from scipy.stats import fisher_exact
    base = next((r for r in rows if r["sigma"] == 0.0), None)
    tests = []
    if base:
        b_k, b_n = base["conv"], base["n"]
        for r in rows:
            if r["sigma"] == 0.0: continue
            k, n = r["conv"], r["n"]
            _, p1 = fisher_exact([[k, n-k], [b_k, b_n-b_k]], alternative="greater")
            _, p2 = fisher_exact([[k, n-k], [b_k, b_n-b_k]], alternative="two-sided")
            tests.append({"sigma": r["sigma"], "k_vs_base": f"{k}/{n} vs {b_k}/{b_n}",
                          "fisher_one_sided": round(p1, 4),
                          "fisher_two_sided": round(p2, 4)})
except ImportError:
    tests = [{"error": "scipy not available"}]

# Write summary
lines = [f"# SR Replication — {log.split('/')[-2]}", "",
         "| σ | n | conv | rate | p_fisher_1s(vs σ=0) |",
         "|---|---|------|------|---------------------|"]
test_map = {t["sigma"]: t["fisher_one_sided"] for t in tests if "sigma" in t}
for r in rows:
    p = test_map.get(r["sigma"], "—")
    lines.append(f"| {r['sigma']} | {r['n']} | {r['conv']} | {r['conv_rate']} | {p} |")
lines.append("")
lines.append("## Fisher exact details")
for t in tests:
    lines.append(f"- {t}")
with open(summary_path, "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"rows: {len(rows)}")
print(f"tests: {tests}")
PYEOF
echo ""
cat "$OUT_DIR/summary.md"
