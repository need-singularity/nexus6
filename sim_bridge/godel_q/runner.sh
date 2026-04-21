#!/bin/bash
# runner.sh — 100-mutation demo for godel_q bootstrap.
# Hard timeout 30min (1800s). All output goes to runs/<ts>/.
#
# SAFETY: does NOT commit, does NOT touch anything outside sim_bridge/godel_q/.
# Sandbox candidate lives under runs/<ts>/candidate.hexa.
#
# Usage: ./runner.sh [N]  (default N=100)

set -u

N="${1:-100}"
if [ "$N" -gt 100 ]; then N=100; fi
if [ "$N" -lt 1 ]; then N=1; fi

TS="$(date +%Y%m%d-%H%M%S)"
BASE="$(cd "$(dirname "$0")" && pwd)"
HEXA="$HOME/Dev/nexus/bin/hexa"

echo "[runner] N=$N ts=$TS base=$BASE"
echo "[runner] hexa=$HEXA"

export HEXA_LOCAL=1
export HEXA_NO_LAUNCHD=1

# Hard 30-min wall (mutation cost ~1s/iter observed; 100 iters ≈ 2-5 min)
timeout 1800 "$HEXA" run "$BASE/bootstrap.hexa" "$N" "$TS"
RC=$?

echo ""
echo "[runner] exit=$RC"
echo "[runner] log=$BASE/runs/$TS/mutations.jsonl"
