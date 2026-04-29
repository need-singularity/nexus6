#!/usr/bin/env bash
# sim_bridge/weave/runner.sh — protein cage / polyhedral self-assembly
# pipeline driver (cycle 24+).
#
# Usage:
#   bash runner.sh                 # default: cage MVP (t=1000) + Bayesian audit
#   bash runner.sh --extended      # cage MVP t=100000 (longer plateau exploration)
#   bash runner.sh --audit-only    # Bayesian audit only
#   bash runner.sh --cage-only     # cage MVP only
#
# Output:
#   runs/cage_assembly_events.jsonl       (raw 77 schema, append-only)
#   runs/polyhedral_cage_audit_events.jsonl

set -uo pipefail

cd "$(dirname "$0")"

MODE="${1:-default}"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "=== sim_bridge/weave/runner.sh ts=$TS mode=$MODE ==="

case "$MODE" in
  --extended)
    python3 cage_assembly_simulation.py --t-end 100000
    python3 polyhedral_cage_bayesian_audit.py
    ;;
  --audit-only)
    python3 polyhedral_cage_bayesian_audit.py
    ;;
  --cage-only)
    python3 cage_assembly_simulation.py
    ;;
  *)
    echo "[step 1] cage assembly ODE (Zlotnick 2003 4-state, T=1 60-subunit)"
    python3 cage_assembly_simulation.py
    echo ""
    echo "[step 2] polyhedral cage Bayesian audit (Caspar-Klug n=34)"
    python3 polyhedral_cage_bayesian_audit.py
    ;;
esac

echo "=== runner.sh DONE ==="
