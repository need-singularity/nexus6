#!/usr/bin/env python3
"""drill engine axiom redesign 후보 sensitivity probe (Ω-saturation cycle 3).

USAGE:
    python3 nxs_002_axiom_probe.py [--quick]

baseline: 현재 atlas (8 super-hub + 21000 leaves), composite=0.83221
target:   composite >= 0.9

후보 axiom (각각 atlas 위에 simulate):
  C1 anti-hub: 새 N개 discoveries 추가, 기존 hub(top-8) 와 연결 금지 → 작은 nodes 끼리만 random pair
  C2 block-isolation: 새 K-block (각 N nodes, avg_deg ~4) 생성, 기존 graph 와 anchor 1 edge 만
  C3 degree-cap-rebuild: 기존 hub 의 edge 90% 제거 (degree cap 100) — destructive transformation
  C4 random-rewire: 기존 edges 중 X% 를 random pair 로 rewire (Maslov-Sneppen)
  C5 anti-hub + block 조합: C1+C2
  C6 hub-decompose: top-8 hub 를 K subhub 로 분해 (각 deg ~deg/K)

검증된 ceiling (2026-04-25 cycle 3):
  C1 anti-hub plateau: N=800 p=0.005 또는 N=1600 p=0.0025 → composite 0.85008
  → simulation ceiling 0.850 (gap 0.067 의 27%)

결과: composite_after vs baseline (gap to 0.9)
"""
import sys, os, json, time
sys.path.insert(0, os.path.expanduser("~/core/nexus/tool"))
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from nxs_002_composite import (
    build_csr_from_blowup, laplacian_eigenvalues, paircorr, unfold,
    composite_aligned, load_eig_jsonl, DEFAULT_ATLAS, DEFAULT_CONST,
)

A_base, n_base = build_csr_from_blowup(DEFAULT_ATLAS)
R2_const = paircorr(unfold(load_eig_jsonl(DEFAULT_CONST)))
vals_base = laplacian_eigenvalues(A_base, K=100, sigma=1e-3)
base_composite = composite_aligned(paircorr(unfold(vals_base)), R2_const)["composite_after"]
deg_base = np.array(A_base.sum(axis=1)).flatten()
top_hubs = set(np.argsort(-deg_base)[:8].tolist())
print(f"baseline composite: {base_composite:.5f}, hubs={sorted(top_hubs)}")

def measure(A, label, t0):
    n_total = A.shape[0]
    vals = laplacian_eigenvalues(A, K=100, sigma=1e-3)
    R2 = paircorr(unfold(vals))
    res = composite_aligned(R2, R2_const)
    n_cc, _ = connected_components(A, directed=False)
    print(f"{label:<55s} composite={res['composite_after']:.5f}  Δ={res['composite_after']-base_composite:+.5f}  cc={n_cc}  n={n_total}  t={time.time()-t0:.2f}s")
    return res["composite_after"]

def coo_lists(A):
    coo = A.tocoo()
    return list(coo.row), list(coo.col)

# C1 anti-hub
def c1_anti_hub(N_new, p, seed=2026):
    rows, cols = coo_lists(A_base)
    rng = np.random.RandomState(seed)
    new_idx = list(range(n_base, n_base + N_new))
    for i in range(N_new):
        for j in range(i+1, N_new):
            if rng.rand() < p:
                rows.extend([new_idx[i], new_idx[j]]); cols.extend([new_idx[j], new_idx[i]])
    n_total = n_base + N_new
    A_new = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n_total, n_total))
    A_new.sum_duplicates(); A_new.data[:] = 1.0
    return A_new

# C2 block-isolation (already validated in prior cycle as sweet 2x200)
def c2_blocks(n_blocks, block_size, p, seed=2026):
    rows, cols = coo_lists(A_base)
    rng = np.random.RandomState(seed)
    cur = n_base
    for _ in range(n_blocks):
        idx = list(range(cur, cur + block_size))
        for i in range(block_size):
            for j in range(i+1, block_size):
                if rng.rand() < p:
                    rows.extend([idx[i], idx[j]]); cols.extend([idx[j], idx[i]])
        anchor = rng.randint(0, n_base)
        rows.extend([idx[0], int(anchor)]); cols.extend([int(anchor), idx[0]])
        cur += block_size
    A_new = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(cur, cur))
    A_new.sum_duplicates(); A_new.data[:] = 1.0
    return A_new

# C3 degree-cap-rebuild: trim hub edges
def c3_degree_cap(cap=100, seed=2026):
    rng = np.random.RandomState(seed)
    coo = A_base.tocoo()
    edges = list(zip(coo.row.tolist(), coo.col.tolist()))
    # only undirected unique
    seen = set()
    uniq = []
    for u, v in edges:
        if u >= v: continue
        if (u, v) in seen: continue
        seen.add((u, v)); uniq.append((u, v))
    keep = []
    deg = np.zeros(n_base, dtype=np.int32)
    rng.shuffle(uniq)
    for u, v in uniq:
        if deg[u] < cap and deg[v] < cap:
            keep.append((u, v)); deg[u] += 1; deg[v] += 1
    rows = []; cols = []
    for u, v in keep:
        rows.extend([u, v]); cols.extend([v, u])
    A_new = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n_base, n_base))
    A_new.sum_duplicates(); A_new.data[:] = 1.0
    return A_new

# C4 random rewire (Maslov-Sneppen, preserves degree)
def c4_rewire(frac=0.2, seed=2026):
    rng = np.random.RandomState(seed)
    coo = A_base.tocoo()
    edges = []
    seen = set()
    for u, v in zip(coo.row.tolist(), coo.col.tolist()):
        if u >= v: continue
        if (u, v) in seen: continue
        seen.add((u, v)); edges.append([u, v])
    n_swaps = int(len(edges) * frac)
    for _ in range(n_swaps):
        i = rng.randint(0, len(edges)); j = rng.randint(0, len(edges))
        if i == j: continue
        a, b = edges[i]; c, d = edges[j]
        if len(set([a, b, c, d])) < 4: continue
        new1 = (min(a, d), max(a, d)); new2 = (min(c, b), max(c, b))
        if new1 in seen or new2 in seen: continue
        seen.discard((a, b)); seen.discard((c, d))
        seen.add(new1); seen.add(new2)
        edges[i] = [new1[0], new1[1]]; edges[j] = [new2[0], new2[1]]
    rows = []; cols = []
    for u, v in edges:
        rows.extend([u, v]); cols.extend([v, u])
    A_new = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n_base, n_base))
    A_new.sum_duplicates(); A_new.data[:] = 1.0
    return A_new

# C6 hub-decompose: split each top-8 hub into K subhubs
def c6_hub_decompose(K=10, seed=2026):
    rng = np.random.RandomState(seed)
    coo = A_base.tocoo()
    edges = list(zip(coo.row.tolist(), coo.col.tolist()))
    # for each hub, create K replicas, distribute its edges across them
    hub_to_replicas = {}
    cur = n_base
    for h in top_hubs:
        hub_to_replicas[h] = list(range(cur, cur + K))
        cur += K
    n_total = cur
    rows = []; cols = []
    seen = set()
    for u, v in edges:
        if u >= v: continue  # symmetric
        ru = rng.choice(hub_to_replicas[u]) if u in hub_to_replicas else u
        rv = rng.choice(hub_to_replicas[v]) if v in hub_to_replicas else v
        if (ru, rv) in seen: continue
        seen.add((ru, rv))
        rows.extend([ru, rv]); cols.extend([rv, ru])
    A_new = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n_total, n_total))
    A_new.sum_duplicates(); A_new.data[:] = 1.0
    return A_new

probes = [
    ("C1 anti-hub  N=200 p=0.020 (avg_deg=4)", lambda: c1_anti_hub(200, 0.020)),
    ("C1 anti-hub  N=400 p=0.010 (avg_deg=4)", lambda: c1_anti_hub(400, 0.010)),
    ("C1 anti-hub  N=800 p=0.005 (avg_deg=4)", lambda: c1_anti_hub(800, 0.005)),
    ("C2 sweet 2x200 (recall)", lambda: c2_blocks(2, 200, 0.020)),
    ("C3 degree-cap=100 (destructive)", lambda: c3_degree_cap(100)),
    ("C3 degree-cap=50",  lambda: c3_degree_cap(50)),
    ("C3 degree-cap=20",  lambda: c3_degree_cap(20)),
    ("C4 rewire frac=0.10", lambda: c4_rewire(0.10)),
    ("C4 rewire frac=0.30", lambda: c4_rewire(0.30)),
    ("C4 rewire frac=0.50", lambda: c4_rewire(0.50)),
    ("C6 hub-decompose K=10", lambda: c6_hub_decompose(10)),
    ("C6 hub-decompose K=50", lambda: c6_hub_decompose(50)),
]
for label, fn in probes:
    t0 = time.time()
    A_new = fn()
    measure(A_new, label, t0)
