#!/usr/bin/env python3
# atlas_phase47_canonical_bridges.py — Agent 28+ canonical cross-domain @S sweep
#
# After Phase 46 (commit 46035d97) added 8 n6-* pivot nodes to atlas.n6
# (commit eb1f5954), this script finds commutative @S edges linking them to
# ALL matching non-canonical nodes — the bridges Agent 24's audit identified
# (n*phi=12, n*tau=24, n*sigma=72, j2*n=144, n+sopfr=11, ...).
#
# Infra-only: reads atlas.n6, writes JSONL to stdout. Does NOT modify atlas.n6.
# Regen: python3 shared/n6/scripts/atlas_phase47_canonical_bridges.py \
#        > shared/n6/atlas_phase47_canonical_bridges.jsonl

import json
import re
import sys
from collections import defaultdict

ATLAS = "shared/n6/atlas.n6"

# 8 canonical pivots — bare-name ids matching @P text-format primitives in atlas.n6
# (J2/M3 capitalized to match @P J2 = jordan_totient(6,2) / @P M3 = mertens(6))
CANON = {
    "n":     ("n",     6),
    "phi":   ("phi",   2),
    "tau":   ("tau",   4),
    "sigma": ("sigma", 12),
    "sopfr": ("sopfr", 5),
    "mu":    ("mu",    1),
    "j2":    ("J2",    24),
    "m3":    ("M3",    3),
}

def load_atlas_nodes(path):
    """Return {value: [(id, domain, grade, src)]}."""
    value_index = defaultdict(list)
    id_set = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or not s.startswith("{"):
                continue
            try:
                rec = json.loads(s)
            except Exception:
                continue
            t = rec.get("type")
            if t not in ("node", "absorb"):
                continue
            nid = rec.get("id")
            if not nid or nid in id_set:
                continue
            id_set.add(nid)
            v = rec.get("value")
            if v is None:
                continue
            try:
                vf = float(v)
            except Exception:
                continue
            dom = rec.get("domain", "")
            grade = rec.get("grade", "")
            src = rec.get("src", "")
            value_index[vf].append((nid, dom, grade, src))
    return value_index

def emit_edge(a_tok, b_tok, op, result, a_id, b_id, match_id, match_dom, match_grade):
    return {
        "type": "edge",
        "kind": "@S",
        "from": a_id,
        "to": match_id,
        "via": b_id,
        "label": f"canonical_{op}_{a_tok}_{b_tok}",
        "expr": f"{a_tok} {op} {b_tok} = {result}",
        "value": result,
        "to_domain": match_dom,
        "to_grade": match_grade,
        "confidence": 1.0,
        "source": "phase47",
        "timestamp": "2026-04-11",
    }

def main():
    idx = load_atlas_nodes(ATLAS)
    print("# phase47 canonical cross-domain @S sweep — Agent 28 follow-up")
    print("# source=atlas.n6 canon=n6-*")

    tokens = list(CANON.keys())
    seen_edges = set()
    emitted = 0

    for i in range(len(tokens)):
        for j in range(len(tokens)):
            if i == j:
                continue
            a_tok, b_tok = tokens[i], tokens[j]
            a_id, a_val = CANON[a_tok]
            b_id, b_val = CANON[b_tok]
            for op, result in (("*", a_val * b_val),
                               ("+", a_val + b_val)):
                if op == "+" and i > j:
                    continue
                matches = idx.get(float(result), [])
                for (mid, mdom, mgrade, msrc) in matches:
                    if mid.startswith("n6-"):
                        continue
                    key = (a_tok, b_tok, op, mid)
                    if key in seen_edges:
                        continue
                    seen_edges.add(key)
                    edge = emit_edge(a_tok, b_tok, op, result,
                                     a_id, b_id, mid, mdom, mgrade)
                    print(json.dumps(edge, ensure_ascii=False, separators=(",", ":")))
                    emitted += 1

    print(f"# emitted={emitted}", file=sys.stderr)

if __name__ == "__main__":
    main()
