#!/usr/bin/env python3
"""drill engine axiom redesign 2.0 — anti-hub +0.018 limit 깨기 (Ω-saturation cycle 58+).

USAGE:
    python3 nxs_002_axiom_probe2.py [--quick] [--seeds N] [--v3prime-export PATH]

baseline (cycle 21 검증, atlas 21320 nodes K=100):
  composite_v1 = 0.83221, sff_align = 0.99086, V3' = 0.92740

cycle 21~33 finding (probe.py):
  C1 anti-hub N=800 p=0.005 = MAX  v1=0.85008 (Δ +0.018, 27% of 0.067 gap), V3' = 0.93617 ★
  C2 block 2x200 = +0.0033 only
  C3 cap = -0.023 ~ -0.085
  C4 rewire = -0.057 ~ -0.083
  C6 hub-decompose K=10/50 = -0.011 ~ -0.032

남은 73% gap (0.067 - 0.018 = 0.049) 의 axiom mechanism 미발견 → 본 cycle 58+:

axiom 후보 (각각 atlas 위에 simulate):
  C7  community-modular ER: K sub-community (각 size m, internal p_in, cross p_out)
       hypothesis: ER giant+singletons 의 modular variant — multi-giant 병렬 invariance
  C8  hyperbolic / power-law: BA preferential-attachment (m edges per new node)
       hypothesis: γ ≈ 3 degree exponent 가 const spectrum random-matrix 에 더 가까움
  C9  scale-free + assortative: BA 위에 degree-degree assortative rewire
       hypothesis: assortativity (high-deg ~ high-deg) 가 hub-leaf wiring 손상
  C10 clustering injection: random triangle close (high-clustering ER)
       hypothesis: triangle 가 spectral gap 을 줄여 const semi-circle 와 align
  C11 hub-decompose v2 (precision): top-K 만 (K<8) 분해 + per-replica edge cap
       hypothesis: cycle 21 의 K=10/50 over-decompose, K=2~4 sweet spot 가능
  C12 anti-hub + community 조합 (C1 + C7): isolated multi-modular
       hypothesis: C1 의 isolated giant + C7 의 multi-community 의 nested layering

각 후보:
  - 5 seeds (default) for variance characterization
  - composite_v1 (paircorr) 측정
  - V3' actual = 0.6 * sff_align + 0.4 * v1 측정 (probe.py 는 v1 only — 본 probe 는 SFF 도)
  - paper_trigger (V3' >= 0.9) check

OUTPUT (stdout):
  human-readable rankings table + JSON one-line summary 마지막

OPTION:
  --v3prime-export PATH  axiom 별 V3' actual measurements 를 JSON 으로 저장
"""
import sys, os, json, time, argparse
sys.path.insert(0, os.path.expanduser("~/core/nexus/tool"))
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from nxs_002_composite import (
    build_csr_from_blowup, laplacian_eigenvalues, paircorr, unfold,
    composite_aligned, load_eig_jsonl, DEFAULT_ATLAS, DEFAULT_CONST,
)

# ─── SFF (Spectral Form Factor) — Python 포팅 of nxs_002_omega_metrics.hexa ───
def sff(eigs_pos_sorted, n_tau=50, tau_max=10.0):
    n = len(eigs_pos_sorted)
    if n < 5: return np.array([])
    mn = float(np.mean(eigs_pos_sorted))
    if mn <= 0: return np.array([])
    E = eigs_pos_sorted / mn
    taus = np.linspace(0.01, tau_max, n_tau)
    out = np.zeros(n_tau)
    for t, tau in enumerate(taus):
        cs = float(np.sum(np.cos(-E * tau)))
        ss = float(np.sum(np.sin(-E * tau)))
        out[t] = (cs * cs + ss * ss) / n
    return out

def sff_align(a, b):
    if len(a) != len(b) or len(a) == 0: return 0.5
    na = float(np.linalg.norm(a)); nb = float(np.linalg.norm(b))
    if na < 1e-12 or nb < 1e-12: return 0.5
    return float(np.dot(a, b) / (na * nb))

# ─── Setup baseline ───
print(f"# nxs_002_axiom_probe2.py — cycle 58+ axiom 2.0 sweep (anti-hub +0.018 깨기)")
t0 = time.time()
A_base, n_base = build_csr_from_blowup(DEFAULT_ATLAS)
const_eigs = load_eig_jsonl(DEFAULT_CONST)
const_pos = np.sort(const_eigs[const_eigs > 1e-10])
R2_const = paircorr(unfold(const_eigs))
sff_const = sff(const_pos)

vals_base = laplacian_eigenvalues(A_base, K=100, sigma=1e-3)
base_v1 = composite_aligned(paircorr(unfold(vals_base)), R2_const)["composite_after"]
base_pos = np.sort(vals_base[vals_base > 1e-10])
base_sff = sff(base_pos)
base_sff_align = sff_align(base_sff, sff_const)
base_v3p = 0.6 * base_sff_align + 0.4 * base_v1

deg_base = np.array(A_base.sum(axis=1)).flatten()
top_hubs = set(np.argsort(-deg_base)[:8].tolist())
print(f"# baseline n={n_base} v1={base_v1:.5f} sff_align={base_sff_align:.5f} V3'={base_v3p:.5f}")
print(f"# hubs(top-8)={sorted(top_hubs)} setup_t={time.time()-t0:.2f}s")
print(f"# C1 reference (probe.py cycle 21): v1=0.85008 V3'=0.93617 (Δv1=+0.01787 Δv3p=+0.00877)")
print()

def coo_lists(A):
    coo = A.tocoo()
    return list(coo.row), list(coo.col)

def measure_axiom(A_new, label, t_start):
    """Returns dict with v1, sff_align, V3', n_cc, elapsed."""
    n_total = A_new.shape[0]
    vals = laplacian_eigenvalues(A_new, K=100, sigma=1e-3)
    R2 = paircorr(unfold(vals))
    res_v1 = composite_aligned(R2, R2_const)
    pos = np.sort(vals[vals > 1e-10])
    s = sff(pos)
    sa = sff_align(s, sff_const)
    v1 = res_v1["composite_after"]
    v3p = 0.6 * sa + 0.4 * v1
    n_cc, _ = connected_components(A_new, directed=False)
    return {
        "label": label, "v1": v1, "sff_align": sa, "v3p": v3p,
        "n_cc": int(n_cc), "n_total": int(n_total),
        "elapsed_s": round(time.time() - t_start, 2),
    }

# ─── C7 community-modular ER ──────────────────────────────────────
def c7_community(K_comm, comm_size, p_in, p_out, seed=2026):
    """K communities of size comm_size, internal p_in, inter-community p_out."""
    rows, cols = coo_lists(A_base)
    rng = np.random.RandomState(seed)
    cur = n_base
    comms = []
    for _ in range(K_comm):
        comms.append(list(range(cur, cur + comm_size)))
        cur += comm_size
    # internal edges
    for c in comms:
        for i in range(len(c)):
            for j in range(i+1, len(c)):
                if rng.rand() < p_in:
                    rows.extend([c[i], c[j]]); cols.extend([c[j], c[i]])
    # cross-community edges (sparse)
    if p_out > 0:
        for ka in range(K_comm):
            for kb in range(ka+1, K_comm):
                for ai in comms[ka]:
                    for bj in comms[kb]:
                        if rng.rand() < p_out:
                            rows.extend([ai, bj]); cols.extend([bj, ai])
    A_new = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(cur, cur))
    A_new.sum_duplicates(); A_new.data[:] = 1.0
    return A_new

# ─── C8 hyperbolic / BA preferential-attachment ──────────────────
def c8_ba(N_new, m_attach, seed=2026):
    """Barabási-Albert: each new node attaches to m existing nodes with prob ∝ deg.
    Anti-hub policy honored: never connect to base top_hubs."""
    rng = np.random.RandomState(seed)
    rows, cols = coo_lists(A_base)
    new_idx = list(range(n_base, n_base + N_new))
    # bootstrap: first m new nodes form a clique
    boot = new_idx[:m_attach]
    for i in range(len(boot)):
        for j in range(i+1, len(boot)):
            rows.extend([boot[i], boot[j]]); cols.extend([boot[j], boot[i]])
    # degree among new nodes only (anti-hub policy: skip base hubs)
    deg_new = {idx: 0 for idx in new_idx}
    for i in range(len(boot)):
        deg_new[boot[i]] = m_attach - 1
    for k in range(m_attach, N_new):
        node = new_idx[k]
        existing = [x for x in new_idx[:k]]
        weights = np.array([deg_new[x] + 1 for x in existing], dtype=np.float64)
        weights /= weights.sum()
        targets = rng.choice(len(existing), size=min(m_attach, len(existing)), replace=False, p=weights)
        for ti in targets:
            t_node = existing[int(ti)]
            rows.extend([node, t_node]); cols.extend([t_node, node])
            deg_new[t_node] += 1
        deg_new[node] = m_attach
    n_total = n_base + N_new
    A_new = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n_total, n_total))
    A_new.sum_duplicates(); A_new.data[:] = 1.0
    return A_new

# ─── C9 scale-free + assortative ─────────────────────────────────
def c9_assortative_ba(N_new, m_attach, n_swaps=None, seed=2026):
    """C8 BA + Maslov-Sneppen-style assortative rewiring (swap if increases degree similarity)."""
    A_ba = c8_ba(N_new, m_attach, seed=seed)
    # extract new-node-only edges to rewire (don't touch base graph)
    rng = np.random.RandomState(seed + 100)
    coo = A_ba.tocoo()
    base_edges = []
    new_edges = []
    seen_new = set()
    for u, v in zip(coo.row.tolist(), coo.col.tolist()):
        if u >= v: continue
        if u >= n_base and v >= n_base:
            key = (u, v)
            if key in seen_new: continue
            seen_new.add(key); new_edges.append([u, v])
        else:
            base_edges.append([u, v])
    deg = np.array(A_ba.sum(axis=1)).flatten()
    if n_swaps is None: n_swaps = int(len(new_edges) * 0.5)
    for _ in range(n_swaps):
        if len(new_edges) < 2: break
        i = rng.randint(0, len(new_edges)); j = rng.randint(0, len(new_edges))
        if i == j: continue
        a, b = new_edges[i]; c, d = new_edges[j]
        if len(set([a, b, c, d])) < 4: continue
        # current similarity
        cur = abs(deg[a]-deg[b]) + abs(deg[c]-deg[d])
        # swap to (a,d), (c,b)
        new1 = (min(a, d), max(a, d)); new2 = (min(c, b), max(c, b))
        if new1 in seen_new or new2 in seen_new: continue
        new_sim = abs(deg[a]-deg[d]) + abs(deg[c]-deg[b])
        if new_sim < cur:  # more assortative if smaller diff
            seen_new.discard((a, b)); seen_new.discard((c, d))
            seen_new.add(new1); seen_new.add(new2)
            new_edges[i] = [new1[0], new1[1]]; new_edges[j] = [new2[0], new2[1]]
    rows, cols = [], []
    for u, v in base_edges + new_edges:
        rows.extend([u, v]); cols.extend([v, u])
    n_total = A_ba.shape[0]
    A_new = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n_total, n_total))
    A_new.sum_duplicates(); A_new.data[:] = 1.0
    return A_new

# ─── C10 clustering coefficient injection (triangle close) ───────
def c10_triangle_close(N_new, p_er, n_triangles, seed=2026):
    """C1 anti-hub + extra triangle edges (close u-v-w open triplets to triangles)."""
    rng = np.random.RandomState(seed)
    rows, cols = coo_lists(A_base)
    new_idx = list(range(n_base, n_base + N_new))
    # underlying ER among new nodes
    for i in range(N_new):
        for j in range(i+1, N_new):
            if rng.rand() < p_er:
                rows.extend([new_idx[i], new_idx[j]]); cols.extend([new_idx[j], new_idx[i]])
    # build adj of new only
    adj = {x: set() for x in new_idx}
    seen = set()
    for u, v in zip(rows, cols):
        if u >= n_base and v >= n_base and u < v:
            adj[u].add(v); adj[v].add(u); seen.add((u, v))
    # close triangles: pick random open triplet u-v-w (v common)
    triangles_added = 0
    attempts = 0
    while triangles_added < n_triangles and attempts < n_triangles * 10:
        attempts += 1
        v = new_idx[rng.randint(0, N_new)]
        nbrs = list(adj[v])
        if len(nbrs) < 2: continue
        u = nbrs[rng.randint(0, len(nbrs))]
        w = nbrs[rng.randint(0, len(nbrs))]
        if u == w: continue
        a, b = (u, w) if u < w else (w, u)
        if (a, b) in seen: continue
        seen.add((a, b)); adj[a].add(b); adj[b].add(a)
        rows.extend([a, b]); cols.extend([b, a])
        triangles_added += 1
    n_total = n_base + N_new
    A_new = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n_total, n_total))
    A_new.sum_duplicates(); A_new.data[:] = 1.0
    return A_new

# ─── C11 hub-decompose v2 (precision: small K) ───────────────────
def c11_hub_decompose_v2(K_split=2, top_n=None, edge_cap=None, seed=2026):
    """Smaller K split + per-replica edge cap. top_n controls how many hubs to split."""
    rng = np.random.RandomState(seed)
    coo = A_base.tocoo()
    edges = list(zip(coo.row.tolist(), coo.col.tolist()))
    hubs_list = sorted(top_hubs)[:top_n] if top_n else sorted(top_hubs)
    hubs_set = set(hubs_list)
    hub_to_replicas = {}
    cur = n_base
    for h in hubs_list:
        hub_to_replicas[h] = list(range(cur, cur + K_split))
        cur += K_split
    n_total = cur
    rows, cols = [], []
    seen = set()
    rep_deg = {r: 0 for h in hubs_list for r in hub_to_replicas[h]}
    for u, v in edges:
        if u >= v: continue
        ru = u; rv = v
        if u in hubs_set:
            # pick replica with capacity
            reps = hub_to_replicas[u]
            if edge_cap:
                avail = [r for r in reps if rep_deg[r] < edge_cap]
                ru = avail[rng.randint(0, len(avail))] if avail else reps[rng.randint(0, len(reps))]
            else:
                ru = reps[rng.randint(0, len(reps))]
        if v in hubs_set:
            reps = hub_to_replicas[v]
            if edge_cap:
                avail = [r for r in reps if rep_deg[r] < edge_cap]
                rv = avail[rng.randint(0, len(avail))] if avail else reps[rng.randint(0, len(reps))]
            else:
                rv = reps[rng.randint(0, len(reps))]
        key = (min(ru, rv), max(ru, rv))
        if key in seen: continue
        seen.add(key)
        if ru in rep_deg: rep_deg[ru] += 1
        if rv in rep_deg: rep_deg[rv] += 1
        rows.extend([ru, rv]); cols.extend([rv, ru])
    A_new = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n_total, n_total))
    A_new.sum_duplicates(); A_new.data[:] = 1.0
    return A_new

# ─── C12 anti-hub + community combo ──────────────────────────────
def c12_antihub_community(N_anti, p_anti, K_comm, comm_size, p_in, seed=2026):
    """C1 anti-hub batch + C7 isolated community batch (zero cross-edges, zero base anchor)."""
    rng = np.random.RandomState(seed)
    rows, cols = coo_lists(A_base)
    cur = n_base
    # anti-hub batch (isolated ER)
    anti_idx = list(range(cur, cur + N_anti))
    cur += N_anti
    for i in range(N_anti):
        for j in range(i+1, N_anti):
            if rng.rand() < p_anti:
                rows.extend([anti_idx[i], anti_idx[j]]); cols.extend([anti_idx[j], anti_idx[i]])
    # multi-community batch (also isolated)
    for _ in range(K_comm):
        c = list(range(cur, cur + comm_size))
        cur += comm_size
        for i in range(comm_size):
            for j in range(i+1, comm_size):
                if rng.rand() < p_in:
                    rows.extend([c[i], c[j]]); cols.extend([c[j], c[i]])
    n_total = cur
    A_new = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n_total, n_total))
    A_new.sum_duplicates(); A_new.data[:] = 1.0
    return A_new

# ─── PROBE LIST ──────────────────────────────────────────────────
ap = argparse.ArgumentParser()
ap.add_argument("--quick", action="store_true", help="fewer seeds (1)")
ap.add_argument("--seeds", type=int, default=3, help="seeds per axiom (default 3)")
ap.add_argument("--v3prime-export", default=None)
args = ap.parse_args()
N_SEEDS = 1 if args.quick else args.seeds

probes = [
    # C7 community variants — sweet at K=2 m=400 p_in=0.020 (avg_deg=8 internal)?
    ("C7 community K=2  m=400 p_in=0.020 p_out=0.0   ", lambda s: c7_community(2, 400, 0.020, 0.0,    seed=s)),
    ("C7 community K=4  m=200 p_in=0.020 p_out=0.0   ", lambda s: c7_community(4, 200, 0.020, 0.0,    seed=s)),
    ("C7 community K=2  m=400 p_in=0.020 p_out=0.0001", lambda s: c7_community(2, 400, 0.020, 0.0001, seed=s)),
    ("C7 community K=8  m=100 p_in=0.040 p_out=0.0   ", lambda s: c7_community(8, 100, 0.040, 0.0,    seed=s)),
    # C8 BA scale-free
    ("C8 BA  N=800  m=2 (avg_deg=4 SF)               ", lambda s: c8_ba(800, 2, seed=s)),
    ("C8 BA  N=800  m=3 (avg_deg=6 SF)               ", lambda s: c8_ba(800, 3, seed=s)),
    ("C8 BA  N=1600 m=2                              ", lambda s: c8_ba(1600, 2, seed=s)),
    # C9 assortative-rewired BA
    ("C9 assort-BA N=800 m=2 (50% swaps)             ", lambda s: c9_assortative_ba(800, 2, seed=s)),
    # C10 triangle injection
    ("C10 anti-hub+triangles N=800 p=0.005 +200 tri  ", lambda s: c10_triangle_close(800, 0.005, 200, seed=s)),
    ("C10 anti-hub+triangles N=800 p=0.005 +800 tri  ", lambda s: c10_triangle_close(800, 0.005, 800, seed=s)),
    # C11 hub-decompose v2
    ("C11 hub-decomp K=2 top=4                       ", lambda s: c11_hub_decompose_v2(2, top_n=4, seed=s)),
    ("C11 hub-decomp K=2 top=8                       ", lambda s: c11_hub_decompose_v2(2, top_n=8, seed=s)),
    ("C11 hub-decomp K=4 top=8 cap=500               ", lambda s: c11_hub_decompose_v2(4, top_n=8, edge_cap=500, seed=s)),
    # C12 anti-hub + community
    ("C12 antihub+comm N_a=800 p=0.005 K=2 m=200     ", lambda s: c12_antihub_community(800, 0.005, 2, 200, 0.020, seed=s)),
    ("C12 antihub+comm N_a=400 p=0.010 K=4 m=200     ", lambda s: c12_antihub_community(400, 0.010, 4, 200, 0.020, seed=s)),
]

results = []
for label, fn in probes:
    measurements = []
    for si in range(N_SEEDS):
        seed = 2026 + si
        t_s = time.time()
        try:
            A_new = fn(seed)
            m = measure_axiom(A_new, label, t_s)
            m["seed"] = seed
            measurements.append(m)
        except Exception as e:
            print(f"{label}  seed={seed}  ERROR: {type(e).__name__}: {e}")
    if not measurements: continue
    v1s = [m["v1"] for m in measurements]
    v3ps = [m["v3p"] for m in measurements]
    sas = [m["sff_align"] for m in measurements]
    summary = {
        "label": label,
        "v1_mean": float(np.mean(v1s)), "v1_std": float(np.std(v1s)),
        "sff_mean": float(np.mean(sas)), "sff_std": float(np.std(sas)),
        "v3p_mean": float(np.mean(v3ps)), "v3p_std": float(np.std(v3ps)),
        "dv1": float(np.mean(v1s) - base_v1),
        "dv3p": float(np.mean(v3ps) - base_v3p),
        "n_seeds": len(measurements),
        "n_cc": measurements[0]["n_cc"],
        "n_total": measurements[0]["n_total"],
        "trigger_v3p": bool(np.mean(v3ps) >= 0.9),
    }
    results.append(summary)
    print(f"{label}  v1={summary['v1_mean']:.5f}±{summary['v1_std']:.5f}  "
          f"sff={summary['sff_mean']:.5f}  V3'={summary['v3p_mean']:.5f}±{summary['v3p_std']:.5f}  "
          f"Δv1={summary['dv1']:+.5f}  Δv3p={summary['dv3p']:+.5f}  "
          f"{'✅' if summary['trigger_v3p'] else '❌'}  cc={summary['n_cc']}")

# ─── RANKINGS ────────────────────────────────────────────────────
print()
print("=" * 92)
print("# RANKINGS (sorted by Δv1 vs baseline 0.83221)")
print(f"# C1 anti-hub reference (probe.py): Δv1=+0.01787  Δv3p=+0.00877")
print("=" * 92)
results_sorted = sorted(results, key=lambda r: -r["dv1"])
for i, r in enumerate(results_sorted, 1):
    beat_c1 = "★ BEATS C1" if r["dv1"] > 0.01787 else ("~C1" if r["dv1"] > 0.015 else "")
    print(f"  #{i:2d}  Δv1={r['dv1']:+.5f}  Δv3p={r['dv3p']:+.5f}  {r['label']}  {beat_c1}")

print()
print("# RANKINGS (sorted by V3' actual)")
results_sorted_v3p = sorted(results, key=lambda r: -r["v3p_mean"])
for i, r in enumerate(results_sorted_v3p, 1):
    beat_c1_v3p = "★ BEATS C1 V3'" if r["v3p_mean"] > 0.93617 else ""
    print(f"  #{i:2d}  V3'={r['v3p_mean']:.5f}  v1={r['v1_mean']:.5f}  sff={r['sff_mean']:.5f}  {r['label']}  {beat_c1_v3p}")

# ─── EXPORT ──────────────────────────────────────────────────────
if args.v3prime_export:
    payload = {
        "schema": "nxs_002_axiom_probe2.v1",
        "ts": int(time.time()),
        "baseline": {"v1": base_v1, "sff_align": base_sff_align, "v3p": base_v3p, "n_nodes": n_base},
        "c1_reference": {"v1": 0.85008, "v3p": 0.93617, "dv1": 0.01787, "dv3p": 0.00877},
        "n_seeds_per_axiom": N_SEEDS,
        "results": results,
    }
    with open(args.v3prime_export, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\n# exported: {args.v3prime_export}")

print()
print(f"# total elapsed: {time.time()-t0:.1f}s")
