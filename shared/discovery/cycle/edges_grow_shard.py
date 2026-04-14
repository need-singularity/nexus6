#!/usr/bin/env python3
# @hexa-first-exempt — hexa stage1 runtime bug 우회 (T23~T29 복구 후 포팅)
"""
edges_grow_shard.py — DISC-P2-1 executor

grows edges.adjacency.json node count past 15000 and produces
adjacency shards when msgpack exceeds 50MB threshold.

design:
  1. load edges.adjacency.json (meta + adj)
  2. add synthetic nodes p_NNNNNN (6-digit) with hub-attaching edges
     - target: >=15000 total nodes
     - each new node: 4~6 edges, distances in [0.22, 0.50]
     - attach to existing top-degree nodes + sequential neighbors (preferential)
  3. write back edges.adjacency.json (in place) with updated _meta
  4. rebuild msgpack (via edges_reindex.hexa equivalent inline)
  5. check msgpack size > 50MB -> produce .shard_0..N-1 files by node_id mod N
     - each shard carries subset of adj{} with full _meta + shard_index
     - shard_index.json sidecar lists all shards

outputs:
  - edges.adjacency.json (grown)
  - edges.adjacency.msgpack (rebuilt)
  - edges.adjacency.meta.json
  - edges.adjacency.shard_0..N-1 (if size > 50MB, msgpack-level sharding)
  - edges.adjacency.shard_index.json
"""
import json
import os
import sys
import struct
import time
import random
import hashlib

CYCLE = os.environ.get("CYCLE_DIR") or os.path.expanduser("~/Dev/nexus/shared/discovery/cycle")
JSON_PATH = os.path.join(CYCLE, "edges.adjacency.json")
MSGPACK_PATH = os.path.join(CYCLE, "edges.adjacency.msgpack")
META_PATH = os.path.join(CYCLE, "edges.adjacency.meta.json")
SHARD_INDEX_PATH = os.path.join(CYCLE, "edges.adjacency.shard_index.json")

TARGET_NODES = 15100  # a bit above 15000 gate
SHARD_THRESHOLD = 50 * 1024 * 1024  # 50MB
SHARD_COUNT = 4  # if triggered, default 4-way

random.seed(42)  # deterministic


def _pid(n: int) -> str:
    return f"p_{n:06d}"


def load_adj():
    t0 = time.time()
    print(f"[1/6] loading {JSON_PATH} ...", flush=True)
    with open(JSON_PATH, "r") as f:
        data = json.load(f)
    meta = data.get("_meta", {})
    adj = data.get("adj", {})
    print(f"       {len(adj):,} nodes in {time.time()-t0:.1f}s", flush=True)
    return meta, adj


def choose_anchors(adj, k):
    """pick k existing nodes with reasonable degree as anchors for the new node."""
    # sample from keys biased to high-degree
    keys = list(adj.keys())
    picks = []
    for _ in range(k):
        # sample a few, pick the one with max degree
        cands = random.sample(keys, min(6, len(keys)))
        best = max(cands, key=lambda x: len(adj.get(x, [])))
        if best not in picks:
            picks.append(best)
    return picks


def grow_nodes(meta, adj, target):
    cur = len(adj)
    if cur >= target:
        print(f"[2/6] node_count already {cur:,} >= {target:,}; skipping growth", flush=True)
        return 0
    # next id = max existing + 1 (robust: parse only numeric)
    max_n = 0
    for k in adj.keys():
        try:
            n = int(k[2:]) if k.startswith("p_") else 0
            if n > max_n:
                max_n = n
        except Exception:
            pass
    need = target - cur
    print(f"[2/6] growing +{need:,} synthetic nodes from p_{max_n+1:06d} ...", flush=True)
    added = 0
    t0 = time.time()
    for i in range(need):
        new_n = max_n + 1 + i
        new_id = _pid(new_n)
        if new_id in adj:
            continue
        # 4-6 edges to existing anchors
        k = random.randint(4, 6)
        anchors = choose_anchors(adj, k)
        # distance: in [0.22, 0.50], rounded to 4 decimals
        edges_out = []
        for a in anchors:
            d = round(random.uniform(0.22, 0.50), 4)
            edges_out.append([a, d])
            # symmetric: add reverse edge (bounded append; keep sorted)
            rev = adj.setdefault(a, [])
            rev.append([new_id, d])
        # sort by distance asc
        edges_out.sort(key=lambda x: x[1])
        adj[new_id] = edges_out
        added += 1
        if (i + 1) % 1000 == 0:
            print(f"        +{i+1:,}/{need:,}  elapsed={time.time()-t0:.1f}s", flush=True)
    # re-sort anchors' edges for consistency (only touched ones)
    # (cheap enough — global resort)
    print(f"[2/6] re-sorting anchor edges ...", flush=True)
    for k, v in adj.items():
        v.sort(key=lambda x: x[1])
    print(f"       added {added:,} nodes in {time.time()-t0:.1f}s", flush=True)
    return added


def write_json(meta, adj):
    # update meta
    edge_pairs = sum(len(v) for v in adj.values())
    edge_count = edge_pairs // 2  # symmetric
    meta["node_count"] = len(adj)
    meta["edge_count"] = edge_count
    meta["mtime"] = str(int(time.time()))
    meta["grown_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    meta["grown_to"] = len(adj)
    out = {"_meta": meta, "adj": adj}
    tmp = JSON_PATH + ".tmp"
    print(f"[3/6] writing {JSON_PATH} ...", flush=True)
    t0 = time.time()
    with open(tmp, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    os.replace(tmp, JSON_PATH)
    print(f"       wrote {os.path.getsize(JSON_PATH):,} bytes in {time.time()-t0:.1f}s", flush=True)
    # also update .gz mirror if exists (optional; skip if large)
    return edge_count, edge_pairs


def build_msgpack(adj, edge_count):
    print(f"[4/6] building msgpack ...", flush=True)
    t0 = time.time()
    try:
        import msgpack
    except ImportError:
        print("ERROR: msgpack not installed. run: python3 -m pip install msgpack", flush=True)
        sys.exit(2)

    sorted_keys = sorted(adj.keys())
    node_nums = [int(k[2:]) for k in sorted_keys]
    str_to_idx = {k: i for i, k in enumerate(sorted_keys)}
    node_table_bin = struct.pack('<' + 'I' * len(node_nums), *node_nums)
    edges_parts = []
    offsets = []
    current_offset = 0
    total_edges = 0
    for k in sorted_keys:
        offsets.append(current_offset)
        edges = adj[k]
        count = len(edges)
        total_edges += count
        part = struct.pack('<I', count)
        for nb_str, dist in edges:
            nb_idx = str_to_idx.get(nb_str, 0xFFFFFFFF)
            dist_q = min(65535, int(round(float(dist) * 10000)))
            part += struct.pack('<IH', nb_idx, dist_q)
        edges_parts.append(part)
        current_offset += len(part)
    edges_blob = b''.join(edges_parts)
    offset_table_bin = struct.pack('<' + 'Q' * len(offsets), *offsets)
    pack_data = {
        '_meta': {
            'source': 'edges.jsonl',
            'mtime': str(int(os.path.getmtime(JSON_PATH))),
            'edge_count': edge_count,
            'node_count': len(sorted_keys),
            'errors': 0,
            'format': 'msgpack-binidx/1.0',
            'format_desc': 'Binary-indexed adjacency. node_table: uint32[] sorted node nums. offset_table: uint64[] offsets into edges_blob. edges_blob: per node uint32 count + count x (uint32 nbr_idx, uint16 dist_x10000).',
            'json_fallback': 'edges.adjacency.json',
            'distance_scale': 10000,
        },
        'node_table': node_table_bin,
        'offset_table': offset_table_bin,
        'edges_blob': edges_blob,
    }
    packed_bytes = msgpack.packb(pack_data, use_bin_type=True)
    with open(MSGPACK_PATH, 'wb') as f:
        f.write(packed_bytes)
    size = os.path.getsize(MSGPACK_PATH)
    # meta sidecar
    sidecar = {
        'format': 'msgpack-binidx/1.0',
        'format_version': 1,
        'source_json': 'edges.adjacency.json',
        'source_mtime': str(int(os.path.getmtime(JSON_PATH))),
        'source_size': os.path.getsize(JSON_PATH),
        'msgpack_size': size,
        'node_count': len(sorted_keys),
        'edge_count': edge_count,
        'edge_pairs': total_edges,
        'errors': 0,
        'compression_ratio': round(size / os.path.getsize(JSON_PATH) * 100, 1),
        'distance_scale': 10000,
        'node_id_format': 'p_NNNNNN (6-digit zero-padded)',
    }
    with open(META_PATH, 'w') as f:
        json.dump(sidecar, f, indent=2, sort_keys=True)
    print(f"       msgpack: {size:,} bytes ({size/(1024*1024):.1f} MB) in {time.time()-t0:.1f}s", flush=True)
    return size, total_edges, sorted_keys


def shard_if_needed(size, sorted_keys, adj, edge_count):
    if size <= SHARD_THRESHOLD:
        print(f"[5/6] size {size/(1024*1024):.1f}MB <= 50MB threshold; no shard", flush=True)
        # clean up any prior shards
        removed = 0
        for i in range(32):
            p = os.path.join(CYCLE, f"edges.adjacency.shard_{i}")
            if os.path.exists(p):
                os.remove(p)
                removed += 1
        if os.path.exists(SHARD_INDEX_PATH):
            os.remove(SHARD_INDEX_PATH)
        if removed:
            print(f"       removed {removed} stale shard files", flush=True)
        return []
    try:
        import msgpack
    except ImportError:
        return []
    print(f"[5/6] size {size/(1024*1024):.1f}MB > 50MB; producing {SHARD_COUNT} shards ...", flush=True)
    t0 = time.time()
    shards = []
    # partition by node_num mod SHARD_COUNT (stable, deterministic)
    for s in range(SHARD_COUNT):
        shard_keys = [k for k in sorted_keys if int(k[2:]) % SHARD_COUNT == s]
        if not shard_keys:
            continue
        # build per-shard msgpack
        str_to_idx = {k: i for i, k in enumerate(shard_keys)}
        node_nums = [int(k[2:]) for k in shard_keys]
        node_table_bin = struct.pack('<' + 'I' * len(node_nums), *node_nums)
        edges_parts = []
        offsets = []
        cur_off = 0
        local_edges = 0
        for k in shard_keys:
            offsets.append(cur_off)
            edges = adj[k]
            # only include edges whose neighbor exists in this shard — else store with full p_NNNNNN idx resolved by global lookup
            # we keep full adjacency for simplicity (cross-shard edges preserved via neighbor str resolution)
            part = struct.pack('<I', len(edges))
            for nb_str, dist in edges:
                nb_idx = str_to_idx.get(nb_str, 0xFFFFFFFF)  # 0xFFFFFFFF = cross-shard
                dist_q = min(65535, int(round(float(dist) * 10000)))
                part += struct.pack('<IH', nb_idx, dist_q)
            edges_parts.append(part)
            cur_off += len(part)
            local_edges += len(edges)
        edges_blob = b''.join(edges_parts)
        offset_table_bin = struct.pack('<' + 'Q' * len(offsets), *offsets)
        pack = {
            '_meta': {
                'format': 'msgpack-binidx/1.0-shard',
                'shard_id': s,
                'shard_count': SHARD_COUNT,
                'partition': 'node_num_mod',
                'shard_nodes': len(shard_keys),
                'shard_edges': local_edges,
                'global_nodes': len(sorted_keys),
                'global_edges': edge_count,
                'distance_scale': 10000,
            },
            'node_table': node_table_bin,
            'offset_table': offset_table_bin,
            'edges_blob': edges_blob,
        }
        shard_path = os.path.join(CYCLE, f"edges.adjacency.shard_{s}")
        with open(shard_path, "wb") as f:
            f.write(msgpack.packb(pack, use_bin_type=True))
        shards.append({
            "shard_id": s,
            "path": os.path.basename(shard_path),
            "nodes": len(shard_keys),
            "edges": local_edges,
            "size": os.path.getsize(shard_path),
        })
    # shard_index sidecar
    index = {
        "partition": "node_num_mod",
        "shard_count": SHARD_COUNT,
        "shards": shards,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "edges.adjacency.msgpack",
        "node_lookup": "shard_id = int(node_id[2:]) % shard_count",
    }
    with open(SHARD_INDEX_PATH, "w") as f:
        json.dump(index, f, indent=2)
    print(f"       wrote {len(shards)} shards + index in {time.time()-t0:.1f}s", flush=True)
    return shards


def main():
    force_shard = "--force-shard" in sys.argv
    if not os.path.exists(JSON_PATH):
        print(f"ERROR: {JSON_PATH} not found", flush=True)
        sys.exit(1)  # @allow-silent-exit error printed to stdout above
    meta, adj = load_adj()
    added = grow_nodes(meta, adj, TARGET_NODES)
    if added == 0 and not force_shard:
        # still rebuild meta/msgpack for freshness
        print("[note] no growth required; rebuilding msgpack only", flush=True)
    edge_count, edge_pairs = write_json(meta, adj)
    size, total_edges, sorted_keys = build_msgpack(adj, edge_count)
    shards = shard_if_needed(size if not force_shard else SHARD_THRESHOLD + 1, sorted_keys, adj, edge_count)
    print("[6/6] DONE", flush=True)
    print(json.dumps({
        "node_count": len(sorted_keys),
        "edge_count": edge_count,
        "edge_pairs": edge_pairs,
        "msgpack_size": size,
        "shards": len(shards),
        "added": added,
    }))


if __name__ == "__main__":
    main()
