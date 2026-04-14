#!/usr/bin/env python3
# @hexa-first-exempt — hexa stage1 runtime bug 우회 (T23~T29 복구 후 포팅)
"""
reality_map_merge_v9.py — DISC-P2-4 executor

merges reality_map_v8.3.json + reality_map.patches.merged.jsonl +
reality_map_extension_t8.jsonl + reality_map_t12_expansion.jsonl +
_v94_new_nodes.json into reality_map_v9.json with dedup by node id.

design:
  1. load v8.3 as base
  2. index existing nodes by id -> set
  3. stream each patch/extension source, accumulate unique additions
  4. normalize new nodes to the base schema (fill missing defaults)
  5. recompute _meta.nodes_count, _meta.node_count, _meta.grade_stats, origin_stats, etc.
  6. bump version to "9.0", add changelog entry with source totals
  7. write reality_map_v9.json atomically
  8. also produce merge_manifest with counts per source
"""
import json
import os
import sys
import time

DISC = os.environ.get("DISC_DIR") or os.path.expanduser("~/Dev/nexus/shared/discovery")
V83 = os.path.join(DISC, "reality_map_v8.3.json")
PATCHES = os.path.join(DISC, "reality_map.patches.merged.jsonl")
EXT_T8 = os.path.join(DISC, "reality_map_extension_t8.jsonl")
EXT_T12 = os.path.join(DISC, "reality_map_t12_expansion.jsonl")
V94 = os.path.join(DISC, "_v94_new_nodes.json")
DST = os.path.join(DISC, "reality_map_v9.json")
MANIFEST = os.path.join(DISC, "reality_map_v9_merge_manifest.json")


def load_jsonl(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except Exception:
                continue
            if "_comment" in obj and len(obj) == 1:
                continue  # skip comment-only rows
            if "id" not in obj:
                continue
            rows.append(obj)
    return rows


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def normalize(node, default_level="L_unknown"):
    n = dict(node)
    n.setdefault("level", default_level)
    n.setdefault("claim", n.get("claim", ""))
    n.setdefault("grade", "EMPIRICAL")
    n.setdefault("causal", "EMPIRICAL")
    n.setdefault("thread", n.get("thread", "misc"))
    n.setdefault("origin", n.get("origin", "natural"))
    return n


def main():
    base = load_json(V83)
    if not base:
        print("ERROR: reality_map_v8.3.json not found", file=sys.stderr)
        sys.exit(1)
    meta = dict(base.get("_meta", {}))
    nodes = list(base.get("nodes", []))
    existing_ids = {n.get("id") for n in nodes if n.get("id")}

    counts = {"base_v8.3": len(nodes)}
    added_by_src = {}

    sources = [
        ("patches_merged", PATCHES, load_jsonl),
        ("extension_t8", EXT_T8, load_jsonl),
        ("t12_expansion", EXT_T12, load_jsonl),
        ("_v94_new_nodes", V94, lambda p: load_json(p) or []),
    ]

    for name, path, loader in sources:
        rows = loader(path)
        added = 0
        for r in rows:
            rid = r.get("id")
            if not rid or rid in existing_ids:
                continue
            nodes.append(normalize(r))
            existing_ids.add(rid)
            added += 1
        added_by_src[name] = {"loaded": len(rows), "added": added}

    # recompute stats
    grade_stats = {}
    origin_stats = {}
    levels = set()
    for n in nodes:
        g = n.get("grade", "EMPIRICAL")
        grade_stats[g] = grade_stats.get(g, 0) + 1
        o = n.get("origin", "natural")
        origin_stats[o] = origin_stats.get(o, 0) + 1
        lvl = n.get("level")
        if lvl:
            levels.add(lvl)

    # update meta
    meta["version"] = "9.0"
    meta["date"] = time.strftime("%Y-%m-%d", time.gmtime())
    meta["node_count"] = len(nodes)
    meta["nodes_count"] = len(nodes)
    meta["grade_stats"] = grade_stats
    meta["origin_stats"] = origin_stats
    meta["levels"] = sorted(levels)
    meta.setdefault("changelog", []).append({
        "version": "9.0",
        "date": meta["date"],
        "change": "v8.3 + merged patches + extensions (t8/t12) + _v94_new_nodes",
        "added_by_source": added_by_src,
        "total_before": counts["base_v8.3"],
        "total_after": len(nodes),
        "delta": len(nodes) - counts["base_v8.3"],
        "generator": "reality_map_merge_v9.py",
    })

    out = {"_meta": meta, "nodes": nodes}
    # preserve edge lists if present in base
    if "edges" in base:
        out["edges"] = base["edges"]
    tmp = DST + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    os.replace(tmp, DST)

    # manifest
    manifest = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "reality_map_v8.3.json + patches/extensions/v94",
        "target": "reality_map_v9.json",
        "version": "9.0",
        "total_nodes": len(nodes),
        "added_by_source": added_by_src,
        "grade_stats": grade_stats,
        "origin_stats": origin_stats,
        "level_count": len(levels),
        "re_merge_cycle": "periodic (call this script; dedup by id guarantees idempotency)",
    }
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(json.dumps({
        "total_nodes": len(nodes),
        "delta_from_v8.3": len(nodes) - counts["base_v8.3"],
        "added_by_source": added_by_src,
        "grade_stats": grade_stats,
        "output": DST,
        "manifest": MANIFEST,
    }, indent=2))


if __name__ == "__main__":
    main()
