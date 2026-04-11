#!/usr/bin/env python3
"""atlas_phase6_crossscale.py — Agent 25 Phase 6 cross-scale @X proposal.

Readonly scan of shared/n6/atlas.n6 → JSONL edges on stdout.
Fallback for atlas_phase6_crossscale.hexa (hexa version times out on 44k lines).

Bridge intermediate-scale (material/music/particle/atom/molecule/bio/genetic)
to large-scale (bt/celestial/galactic/cosmological) via shared algebraic n6
src token (phi/tau/n/sigma/sopfr/mu/J2/M3) OR identical literal RHS.
Does NOT modify atlas.n6.
"""
import json
import os
import re
import sys
from pathlib import Path

ATLAS = Path(os.path.expanduser("~/Dev/nexus/shared/n6/atlas.n6"))

INTER = {"material", "music", "particle", "atom", "molecule", "bio", "genetic"}
LARGE = {"bt", "celestial", "galactic", "cosmological"}

NODE_RE = re.compile(r"^@([FRCPX])\s+(.+?)\s*::\s*([A-Za-z0-9_\-]+)\s*\[([^\]]+)\]\s*$")

ALG_TOKENS = ("phi", "tau", "sigma", "sopfr", "J2", "M3", "mu")
# order matters: match "sigma" before "sopfr" — they don't share prefix but
# we still want a stable detection order.


def algebraic_tag(expr: str) -> str:
    """Return pipe-joined sorted set of n6 algebraic tokens in expr, or ''."""
    if not expr:
        return ""
    hits = []
    # word-boundary match so "tauon" doesn't trip "tau"
    for tok in ALG_TOKENS:
        if re.search(rf"\b{tok}\b", expr):
            hits.append(tok)
    if not hits:
        # bare "n" — only if standalone identifier in expr
        if re.search(r"\bn\b", expr):
            hits.append("n")
    if not hits:
        return ""
    return "|".join(sorted(set(hits)))


def parse_node(line: str):
    m = NODE_RE.match(line.strip())
    if not m:
        return None
    kind, id_expr, domain, grade = m.groups()
    if " = " in id_expr:
        nid, _, expr = id_expr.partition(" = ")
        nid = nid.strip()
        expr = expr.strip()
    else:
        nid = id_expr.strip()
        expr = ""
    return kind, nid, expr, domain, grade


def main() -> int:
    if not ATLAS.exists():
        print(json.dumps({"error": f"atlas not found: {ATLAS}"}))
        return 1
    lines = ATLAS.read_text(encoding="utf-8", errors="replace").splitlines()

    large_by_tag: dict[str, list] = {}
    inter_nodes: list = []

    for ln in lines:
        parsed = parse_node(ln)
        if not parsed:
            continue
        _kind, nid, expr, domain, grade = parsed
        if not expr or expr == "misc":
            continue
        tag = algebraic_tag(expr)
        if not tag:
            continue
        if domain in LARGE:
            large_by_tag.setdefault(tag, []).append((nid, domain, expr, grade))
        elif domain in INTER:
            if grade in ("10*", "10", "9"):
                inter_nodes.append((nid, domain, expr, grade, tag))

    # diversity: count intermediate domains that contribute to each tag
    tag_domains: dict[str, set] = {}
    for _nid, dom, _e, _g, tag in inter_nodes:
        tag_domains.setdefault(tag, set()).add(dom)

    results = []
    seen_pairs = set()
    for nid_a, dom_a, expr_a, grade_a, tag in inter_nodes:
        candidates = large_by_tag.get(tag, [])
        for nid_b, dom_b, expr_b, grade_b in candidates:
            key = (nid_a, nid_b)
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            ga_exact = grade_a in ("10*", "10")
            gb_exact = grade_b in ("10*", "10")
            same_src = expr_a.strip() == expr_b.strip()
            diversity = len(tag_domains.get(tag, ()))
            score = (
                (1.0 if ga_exact else 0.0)
                + (1.0 if gb_exact else 0.0)
                + (1.0 if same_src else 0.0)
                + 0.5 * min(diversity, 6) / 6.0
                + 0.5
            )
            if ga_exact and gb_exact:
                conf = 10
            elif gb_exact or ga_exact:
                conf = 9
            else:
                conf = 8
            results.append(
                {
                    "score": round(score, 4),
                    "from": nid_a,
                    "to": nid_b,
                    "src": tag,
                    "value": "=" + expr_a,
                    "value_to": "=" + expr_b,
                    "confidence": conf,
                    "route": f"{dom_a}->{dom_b}",
                    "same_src_label": same_src,
                }
            )

    results.sort(key=lambda r: (-r["score"], r["from"], r["to"]))
    top = results[:200]

    ts = "2026-04-11"
    for r in top:
        print(
            json.dumps(
                {
                    "type": "edge",
                    "kind": "@X",
                    "from": r["from"],
                    "to": r["to"],
                    "label": "cross_scale",
                    "value": r["value"],
                    "value_to": r["value_to"],
                    "src": r["src"],
                    "confidence": r["confidence"],
                    "score": r["score"],
                    "route": r["route"],
                    "same_src_label": r["same_src_label"],
                    "source": "phase6",
                    "timestamp": ts,
                },
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
