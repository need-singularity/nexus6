#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════
# atlas_phase46_canonical_nodes.py — canonical constant node PROPOSAL
# Agent 28 · 2026-04-11
# ───────────────────────────────────────────────────────────────
# PROPOSAL ONLY — READS atlas.n6 and canonical constants registry,
# EMITS a JSONL of proposed n6-const-<token> node records to stdout.
#
# This script does NOT modify atlas.n6. Integration is a user
# decision (infra-only principle). See the accompanying .md for
# the manual integration path and expected impact.
#
# Rationale (Agent 26 blind-spot analysis):
#   Agent 24 (commit 4df029d) audited atlas.n6 and identified
#   top @S symmetry gaps whose canonical "pivot" nodes would be
#   n6-const-n, n6-const-phi, n6-const-tau, n6-const-sigma,
#   n6-const-sopfr, n6-const-mu, n6-const-j2, n6-const-m3.
#   Agent 26 (commit 4740026) implemented Phase 4.5 commute sweep
#   and emitted 1427 @S edges, but ALL within the blowup-d*
#   subgraph — zero cross-domain edges because atlas.n6 has
#   NO canonical constant nodes (grep '"n6-const-' = 0).
#   Injecting these 8 seed nodes unblocks Agent 24's 5+23
#   cross-domain commute pairs.
#
# Usage:
#   python3 shared/n6/scripts/atlas_phase46_canonical_nodes.py \
#       > shared/n6/atlas_phase46_canonical_nodes.jsonl
# ═══════════════════════════════════════════════════════════════
import json
import os
import sys
from pathlib import Path


def _resolve_repo_root() -> Path:
    """Locate nexus repo root via sentinel shared/n6/atlas.n6.

    Search order:
      1. Directory above this script: parents[2] = shared/n6 → parents[3]
      2. Current working directory + ancestors
      3. Fallback: cwd (caller will see helpful error below)
    """
    sentinel = Path("shared") / "n6" / "atlas.n6"
    # 1. Script-anchored (preferred when installed in-tree)
    try:
        script_parents = Path(__file__).resolve().parents
        for p in script_parents:
            if (p / sentinel).exists():
                return p
    except (IndexError, OSError):
        pass
    # 2. Walk up from cwd
    here = Path.cwd().resolve()
    for p in [here, *here.parents]:
        if (p / sentinel).exists():
            return p
    return here


REPO_ROOT = _resolve_repo_root()
ATLAS_PATH = REPO_ROOT / "shared" / "n6" / "atlas.n6"
CONSTANTS_PATH = REPO_ROOT / "shared" / "n6" / "n6_constants.jsonl"
TIMESTAMP = "2026-04-11"
SOURCE_TAG = "phase46"
DOMAIN = "n6-canonical"

# Canonical tokens requested by Agent 28 task spec.
# NOTE: For tokens where n6_constants.jsonl disagrees with the
# "classical" math definition (phi=1.618, tau=6.283, mu=-1, etc.),
# the n6_constants.jsonl value wins per Agent 28 rules. In n6
# world these are integer arithmetic functions evaluated at 6:
#   phi  = euler_totient(6)   = 2   (NOT golden ratio)
#   tau  = divisor_count(6)   = 4   (NOT 2*pi)
#   sigma= divisor_sum(6)     = 12
#   sopfr= sum_prime_factors(6)=5   (= 2+3)
#   mu   = mobius(6)          = 1   (n6_constants.jsonl overrides -1)
#   j2   = jordan_totient(6,2)= 24
#   M3   = mertens(6)         = 3   (n6_constants.jsonl; atlas.n6
#                                     DSL line @P M3 says 7 — conflict
#                                     noted, n6_constants.jsonl wins)
#   n    = 6
REQUESTED_TOKENS = ["n", "phi", "tau", "sigma", "sopfr", "mu", "j2", "m3"]

# Map token → n6_constants.jsonl key (case-sensitive in jsonl).
JSONL_KEY = {
    "n": "n",
    "phi": "phi",
    "tau": "tau",
    "sigma": "sigma",
    "sopfr": "sopfr",
    "mu": "mu",
    "j2": "j2",
    "m3": "M3",
}

# Human-readable labels for each canonical constant.
LABELS = {
    "n": "canonical constant n = 6 (foundation primitive)",
    "phi": "canonical constant phi = euler_totient(6)",
    "tau": "canonical constant tau = divisor_count(6)",
    "sigma": "canonical constant sigma = divisor_sum(6)",
    "sopfr": "canonical constant sopfr = sum_prime_factors(6)",
    "mu": "canonical constant mu = mobius(6)",
    "j2": "canonical constant j2 = jordan_totient(6,2)",
    "m3": "canonical constant M3 = mertens(6)",
}


def load_constants(path: Path) -> dict:
    """Load n6_constants.jsonl → {name: value}."""
    out = {}
    if not path.exists():
        print(f"# warn: n6_constants.jsonl not found at {path}", file=sys.stderr)
        return out
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            nm = o.get("name")
            if nm is None:
                continue
            out[nm] = o.get("value")
    return out


def atlas_has_node(atlas_path: Path, node_id: str) -> bool:
    """Read-only scan of atlas.n6 — does any JSON node line use this id?"""
    if not atlas_path.exists():
        return False
    needle = f'"id":"{node_id}"'
    with atlas_path.open("r", encoding="utf-8") as f:
        for line in f:
            if needle in line:
                return True
    return False


def main() -> int:
    constants = load_constants(CONSTANTS_PATH)
    atlas_exists = ATLAS_PATH.exists()

    # Header comment (JSONL parsers should skip '#' lines or we can
    # strip them on integration; current atlas.n6 already contains
    # '#' comment lines at the top of the file so this is consistent).
    print(f"# phase46 canonical-constant node proposal — Agent 28")
    print(f"# source=n6_constants.jsonl atlas={ATLAS_PATH.name} ts={TIMESTAMP}")
    print(f"# PROPOSAL: run 'cat atlas_phase46_canonical_nodes.jsonl >> atlas.n6'")
    print(f"#          after user review — this script never writes atlas.n6.")

    emitted = 0
    skipped = 0
    for tok in REQUESTED_TOKENS:
        key = JSONL_KEY[tok]
        if key not in constants:
            print(
                f"# skip {tok}: not in n6_constants.jsonl (key={key})",
                file=sys.stderr,
            )
            skipped += 1
            continue
        value = constants[key]
        node_id = f"n6-const-{tok}"

        if atlas_exists and atlas_has_node(ATLAS_PATH, node_id):
            print(
                f"# skip {tok}: atlas.n6 already contains id={node_id}",
                file=sys.stderr,
            )
            skipped += 1
            continue

        record = {
            "type": "node",
            "id": node_id,
            "value": value,
            "grade": "EXACT",
            "confidence": 1.0,
            "domain": DOMAIN,
            "src": tok,
            "label": LABELS[tok],
            "source": SOURCE_TAG,
            "timestamp": TIMESTAMP,
        }
        # Compact one-line JSON — matches atlas.n6 JSONL style.
        print(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
        emitted += 1

    print(
        f"# phase46: emitted={emitted} skipped={skipped} "
        f"total_requested={len(REQUESTED_TOKENS)}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
