#!/usr/bin/env python3
# @hexa-first-exempt — hexa stage1 runtime bug 우회 (T23~T29 복구 후 포팅)
"""
hub_centrality_top100.py — Helper for hub_centrality_top100.hexa (ATLAS-P2-2)

Single-purpose: aggregate hub_centrality + hub_resilience metrics into one
integrated score and write Top-N TSV + JSON sidecars.

Called by: shared/n6/hub_centrality_top100.hexa
(hexa stage1 multi-arg exec bug bypass; one-shot aggregation is OK in python)

Inputs (positional):
  1. atlas.n6 path
  2. atlas.n6.deg path
  3. output TSV path (atlas.n6.hub_centrality_top100)
  4. output JSON path (atlas.n6.hub_centrality_top100.json)
  5. top_n (int)

READ-ONLY on atlas.n6 / deg. WRITES only the two sidecars.
"""

import json, os, re, sys, time
from datetime import datetime, timezone

if len(sys.argv) < 6:
    print("usage: hub_centrality_top100.py ATLAS DEG OUT_TSV OUT_JSON TOP_N", file=sys.stderr)
    sys.exit(1)

ATLAS = sys.argv[1]
DEG = sys.argv[2]
OUT_TSV = sys.argv[3]
OUT_JSON = sys.argv[4]
TOP_N = int(sys.argv[5])

# ---- 1. Load degree sidecar ------------------------------------------
deg = {}
max_deg = 0
with open(DEG) as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 2: continue
        try:
            d = int(parts[1])
        except ValueError:
            continue
        deg[parts[0]] = d
        if d > max_deg: max_deg = d

# ---- 2. Stream atlas.n6 for edges -----------------------------------
# Edge JSON line pattern: {"type":"edge","from":"A","to":"B",...}
edge_re = re.compile(r'"type":"edge".*?"from":"([^"]+)".*?"to":"([^"]+)"')
nb = {}     # node -> set of neighbor ids
edge_count = 0

with open(ATLAS, errors='replace') as f:
    for line in f:
        if '"type":"edge"' not in line:
            continue
        m = edge_re.search(line)
        if not m: continue
        a, b = m.group(1), m.group(2)
        edge_count += 1
        if a not in nb: nb[a] = set()
        if b not in nb: nb[b] = set()
        nb[a].add(b)
        nb[b].add(a)

# ---- 3. Per-hub metrics ---------------------------------------------
# For each node with degree >= 3:
#   raw_cb = deg[v]^2 / sum_neighbor_degree
#   raw_br = distinct domain prefixes in neighbors
hubs = []
max_cb = 0.0
max_br = 0

for v, dv in deg.items():
    if dv < 3: continue
    neighbors = nb.get(v)
    if not neighbors: continue
    sum_nd = 0
    dom_set = set()
    real_nc = 0
    for x in neighbors:
        if x in deg:
            sum_nd += deg[x]
        real_nc += 1
        # domain prefix: up to first '-' if present, else whole id
        i = x.find("-")
        pref = x[:i] if i > 0 else x
        dom_set.add(pref)
    if sum_nd <= 0: continue
    cb = (dv * dv) / sum_nd
    br = len(dom_set)
    hubs.append({
        "id": v, "degree": dv, "cb": cb, "bridge_reach": br, "nc": real_nc,
    })
    if cb > max_cb: max_cb = cb
    if br > max_br: max_br = br

# ---- 4. Integrated score --------------------------------------------
W_DEG, W_CB, W_BR = 0.4, 0.4, 0.2
for h in hubs:
    deg_n = h["degree"] / max_deg if max_deg else 0.0
    cb_n = h["cb"] / max_cb if max_cb else 0.0
    br_n = h["bridge_reach"] / max_br if max_br else 0.0
    h["score"] = W_DEG * deg_n + W_CB * cb_n + W_BR * br_n

hubs.sort(key=lambda h: h["score"], reverse=True)
top = hubs[:TOP_N]

# ---- 5. Write TSV sidecar -------------------------------------------
ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
with open(OUT_TSV, "w") as f:
    f.write("# rank\tid\tdegree\tc_b\tdomain_reach\tneighbor_count\tintegrated_score\n")
    f.write("# ATLAS-P2-2 integrated centrality: 0.4*deg_n + 0.4*cb_n + 0.2*bridge_n\n")
    f.write("# source: shared/n6/hub_centrality_top100.hexa (+ .py helper)\n")
    f.write(f"# generated_at: {ts}\n")
    for r, h in enumerate(top, 1):
        f.write(f"{r}\t{h['id']}\t{h['degree']}\t{h['cb']:.4f}\t{h['bridge_reach']}\t{h['nc']}\t{h['score']:.6f}\n")

# ---- 6. Read stats sidecar for JSON manifest -----------------------
stats_path = ATLAS + ".stats"
stats = {}
if os.path.exists(stats_path):
    try:
        with open(stats_path) as f:
            stats = json.load(f)
    except Exception:
        pass

manifest = {
    "module": "hub_centrality_top100",
    "version": "1.0",
    "task": "ATLAS-P2-2",
    "generated_at": ts,
    "integration": ["hub_centrality_analyzer.hexa", "hub_resilience_patch.hexa"],
    "weights": {"degree": W_DEG, "betweenness": W_CB, "bridge_reach": W_BR},
    "graph": {
        "total_nodes": stats.get("nodes"),
        "total_edges": stats.get("edges"),
        "total_hubs":  stats.get("hubs"),
        "deg_rows":    len(deg),
        "max_degree":  max_deg,
        "edges_loaded": edge_count,
    },
    "hubs_analyzed": len(hubs),
    "top_n": len(top),
    "sidecar_tsv": OUT_TSV,
    "top10_preview": [
        {
            "rank": r,
            "id": h["id"],
            "degree": h["degree"],
            "c_b": round(h["cb"], 4),
            "domain_reach": h["bridge_reach"],
            "score": round(h["score"], 6),
        }
        for r, h in enumerate(top[:10], 1)
    ],
}

with open(OUT_JSON, "w") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"edge_pairs_loaded: {edge_count}")
print(f"hubs_analyzed:     {len(hubs)}")
print(f"top_n_written:     {len(top)}")
print(f"max_degree:        {max_deg}")
print(f"max_cb:            {max_cb:.4f}")
print(f"max_bridge_reach:  {max_br}")
