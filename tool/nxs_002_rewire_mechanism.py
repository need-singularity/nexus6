#!/usr/bin/env python3
"""nxs_002_rewire_mechanism — Maslov-Sneppen rewire universality probe (Ω-saturation cycle phase8).

cycle 24/32 finding (phase4 ladder, design §14) 의 follow-up:
  C4 Maslov-Sneppen rewire 만 V3' = 0.81659 ± 0.012 (5 seeds 모두 < 0.9) — V3' 의 unique breaker.
  C1/C2/C3 모두 V3' >= 0.92 통과. baseline = 0.92740.

본 tool 이 묻는 hypothesis:
  H1 — V3' break 가 graph "structured backbone" 깸의 결과면, ANY null-model rewire 도 같은 break.
  H2 — universality class = "degree-preserving random rewire" (Maslov-Sneppen + double-edge swap +
       configuration model)
  H3 — 진짜 mechanism = giant component 의 spectral gap 변화. backbone 보존 → V3' 보존.

USAGE:
    python3 nxs_002_rewire_mechanism.py [--quick]

PROBES (5 seeds each, mean ± std):
  A. C4 fraction sweep: frac ∈ {0.01, 0.05, 0.10, 0.20, 0.30, 0.50, 0.70, 1.00}
       — V3' decay curve 측정. transition point (sigmoid?) 발견.
  B. Rewire variants (degree-preserving, frac=0.50):
       B1. Maslov-Sneppen (baseline, cycle 24 reproducer)
       B2. nx double_edge_swap (networkx 표준)
       B3. random pair swap (no degree preservation — null reference)
  C. Random graph null models (replace base atlas):
       C1. Configuration model (preserves degree sequence, similar to ∞ rewire)
       C2. Erdős–Rényi G(n, p) matching avg_deg
       C3. Barabási–Albert preferential attachment (m=2)
       C4. Watts–Strogatz small-world (k=4, p=0.1)
  D. Spectrum diagnostics on each: spectral_gap, low-eig std, giant fraction, n_cc.

OUTPUT:
  state/rewire_universality_phase8.jsonl — per-config record
  stdout: human-readable progress + summary table
"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.expanduser("~/core/nexus/tool"))
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from nxs_002_composite import (
    build_csr_from_blowup, laplacian_eigenvalues, paircorr, unfold,
    composite_aligned, load_eig_jsonl, DEFAULT_ATLAS, DEFAULT_CONST,
)

OUT_PATH = os.path.expanduser("~/core/nexus/state/rewire_universality_phase8.jsonl")

# ---------- V3' core ----------
def sff(eigs, n_tau=200, tau_max=10.0):
    nz = np.array([v for v in eigs if v > 1e-10])
    if len(nz) < 5: return np.array([])
    E = nz / nz.mean()
    taus = np.linspace(0.01, tau_max, n_tau)
    out = np.zeros(n_tau)
    for ti, tau in enumerate(taus):
        z = np.exp(-1j * E * tau).sum()
        out[ti] = (z * np.conjugate(z)).real / len(E)
    return out

def sff_align(a, b):
    if len(a) != len(b) or len(a) == 0: return 0.5
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12: return 0.5
    return float(np.dot(a, b) / (na * nb))

# ---------- Inputs ----------
print("[load] base atlas + constants...", file=sys.stderr)
A_base, n_base = build_csr_from_blowup(DEFAULT_ATLAS)
const_eigs = load_eig_jsonl(DEFAULT_CONST)
sff_const = sff(const_eigs)
R2_const = paircorr(unfold(const_eigs))
deg_base = np.array(A_base.sum(axis=1)).flatten()
m_base = int(deg_base.sum() / 2)
avg_deg_base = float(deg_base.mean())
print(f"[load] n={n_base} m={m_base} avg_deg={avg_deg_base:.3f}", file=sys.stderr)

vals_base = laplacian_eigenvalues(A_base, K=100, sigma=1e-3)
R2_atlas_base = paircorr(unfold(vals_base))
v1_base = composite_aligned(R2_atlas_base, R2_const)["composite_after"]
sff_a_base = sff(vals_base)
sff_align_base = sff_align(sff_a_base, sff_const)
v3p_base = 0.6 * sff_align_base + 0.4 * v1_base
print(f"[base] V1={v1_base:.5f} sff_align={sff_align_base:.5f} V3'={v3p_base:.5f}", file=sys.stderr)

# ---------- Helpers ----------
def edges_unique(A):
    """Return list of (u,v) with u<v from CSR."""
    coo = A.tocoo()
    seen = set(); out = []
    for u, v in zip(coo.row.tolist(), coo.col.tolist()):
        if u >= v: continue
        if (u, v) in seen: continue
        seen.add((u, v)); out.append((u, v))
    return out, seen

def csr_from_edges(edges, n):
    rows = []; cols = []
    for u, v in edges:
        rows.extend([u, v]); cols.extend([v, u])
    if not rows:
        return csr_matrix((n, n))
    A = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    A.sum_duplicates(); A.data[:] = 1.0
    return A

def measure_v3p(A, label, t0):
    n_total = A.shape[0]
    vals = laplacian_eigenvalues(A, K=100, sigma=1e-3)
    R2 = paircorr(unfold(vals))
    v1 = composite_aligned(R2, R2_const)["composite_after"]
    sff_a = sff(vals)
    sa = sff_align(sff_a, sff_const)
    v3p = 0.6 * sa + 0.4 * v1
    n_cc, comp_labels = connected_components(A, directed=False)
    sizes = np.bincount(comp_labels)
    giant_size = int(sizes.max()) if len(sizes) else 0
    nz_eigs = vals[vals > 1e-10]
    spectral_gap = float(nz_eigs[0]) if len(nz_eigs) else 0.0
    low_std = float(nz_eigs[:10].std()) if len(nz_eigs) >= 10 else 0.0
    rec = {
        "label": label, "n_total": n_total, "n_cc": int(n_cc),
        "giant_size": giant_size, "giant_frac": giant_size / max(n_total, 1),
        "v1": round(v1, 5), "sff_align": round(sa, 5), "v3p": round(v3p, 5),
        "spectral_gap": round(spectral_gap, 5), "low10_eig_std": round(low_std, 5),
        "n_eig_nonzero": int((vals > 1e-10).sum()),
        "elapsed_s": round(time.time() - t0, 2),
    }
    print(f"  {label:<55s} V3'={v3p:.4f} V1={v1:.4f} sff={sa:.4f} cc={n_cc} gap={spectral_gap:.4f} t={rec['elapsed_s']}s")
    return rec

# ---------- Rewire variants ----------
def maslov_sneppen(edges_in, seen_in, frac, seed):
    """Degree-preserving double-edge swap (Maslov-Sneppen 1-step):
       (a,b) + (c,d) → (a,d) + (c,b). Keeps degree of every node."""
    rng = np.random.RandomState(seed)
    edges = [list(e) for e in edges_in]
    seen = set(seen_in)
    n_swaps = int(len(edges) * frac)
    done = 0; tries = 0; max_tries = n_swaps * 20
    while done < n_swaps and tries < max_tries:
        tries += 1
        i = rng.randint(0, len(edges)); j = rng.randint(0, len(edges))
        if i == j: continue
        a, b = edges[i]; c, d = edges[j]
        if len({a, b, c, d}) < 4: continue
        new1 = (min(a, d), max(a, d)); new2 = (min(c, b), max(c, b))
        if new1 in seen or new2 in seen: continue
        old1 = (min(a, b), max(a, b)); old2 = (min(c, d), max(c, d))
        seen.discard(old1); seen.discard(old2)
        seen.add(new1); seen.add(new2)
        edges[i] = [new1[0], new1[1]]; edges[j] = [new2[0], new2[1]]
        done += 1
    return [tuple(e) for e in edges], seen, done

def random_rewire_no_degree(edges_in, seen_in, frac, seed, n_nodes):
    """Replace frac of edges with totally random pairs (degree NOT preserved). Vectorized."""
    rng = np.random.RandomState(seed)
    edges = list(edges_in)
    n_target = int(len(edges) * frac)
    idxs = rng.choice(len(edges), size=n_target, replace=False)
    keep_mask = np.ones(len(edges), dtype=bool); keep_mask[idxs] = False
    new_edges = [edges[i] for i in range(len(edges)) if keep_mask[i]]
    new_seen_keys = set()
    for u, v in new_edges:
        new_seen_keys.add(int(u) * n_nodes + int(v))
    # vectorized random pair sampling, oversample
    oversample = int(n_target * 2.0) + 200
    us = rng.randint(0, n_nodes, size=oversample)
    vs = rng.randint(0, n_nodes, size=oversample)
    a = np.minimum(us, vs); b = np.maximum(us, vs)
    mask = a < b
    a = a[mask]; b = b[mask]
    keys = a.astype(np.int64) * n_nodes + b.astype(np.int64)
    # dedupe within candidates
    _, ui = np.unique(keys, return_index=True)
    a = a[ui]; b = b[ui]; keys = keys[ui]
    # filter out collisions with existing edges
    cand_mask = np.array([k not in new_seen_keys for k in keys.tolist()], dtype=bool)
    a = a[cand_mask][:n_target]; b = b[cand_mask][:n_target]
    added = len(a)
    for u, v in zip(a.tolist(), b.tolist()):
        new_edges.append((u, v))
    return new_edges, None, added

def nx_double_edge_swap(edges_in, n, n_swaps, seed):
    """Use networkx's reference impl as cross-check (C-impl friendly)."""
    import networkx as nx
    G = nx.Graph()
    G.add_nodes_from(range(n))
    G.add_edges_from(edges_in)
    try:
        nx.double_edge_swap(G, nswap=n_swaps, max_tries=n_swaps * 20, seed=int(seed))
    except nx.NetworkXAlgorithmError:
        # connectivity may break in disconnected graphs, fall back to undirected swap loop
        pass
    new_edges = [(min(u, v), max(u, v)) for u, v in G.edges()]
    new_seen = set(new_edges)
    return new_edges, new_seen, n_swaps

# ---------- Null model graph generators ----------
def configuration_model_from_degree(deg_seq, seed):
    """Build configuration model preserving exact degree sequence."""
    import networkx as nx
    rng = np.random.RandomState(seed)
    seq = [int(d) for d in deg_seq]
    if sum(seq) % 2 == 1:
        # nudge to even
        seq[int(rng.randint(0, len(seq)))] += 1
    G = nx.configuration_model(seq, seed=int(seed))
    G = nx.Graph(G)  # collapse multi-edges
    G.remove_edges_from(nx.selfloop_edges(G))
    edges = [(min(u, v), max(u, v)) for u, v in G.edges()]
    return edges, len(G)

def er_match_avg_deg(n, avg_deg, seed):
    """Sparse ER G(n, p) with E[deg] = avg_deg. Vectorized sampling."""
    rng = np.random.RandomState(seed)
    m_target = int(n * avg_deg / 2)
    # oversample by 1.3x to account for self-loops + duplicates
    oversample = int(m_target * 1.3) + 100
    us = rng.randint(0, n, size=oversample)
    vs = rng.randint(0, n, size=oversample)
    a = np.minimum(us, vs); b = np.maximum(us, vs)
    mask = a < b  # drop self-loops
    a = a[mask]; b = b[mask]
    # encode and dedupe
    keys = a.astype(np.int64) * n + b.astype(np.int64)
    _, idx = np.unique(keys, return_index=True)
    a = a[idx][:m_target]; b = b[idx][:m_target]
    return list(zip(a.tolist(), b.tolist()))

def ba_graph(n, m_edges_per_step, seed):
    """Barabási–Albert preferential attachment."""
    import networkx as nx
    G = nx.barabasi_albert_graph(n, m_edges_per_step, seed=int(seed))
    return [(min(u, v), max(u, v)) for u, v in G.edges()]

def ws_graph(n, k, p, seed):
    """Watts–Strogatz small-world."""
    import networkx as nx
    G = nx.watts_strogatz_graph(n, k, p, seed=int(seed))
    return [(min(u, v), max(u, v)) for u, v in G.edges()]

# ---------- Probe runners ----------
SEEDS = [2026, 2027, 2028, 2029, 2030]

def run_seeds(label, fn_make_A, n_total):
    """fn_make_A(seed) -> A. Run over SEEDS, return list of records + aggregate."""
    recs = []
    print(f"[probe] {label}")
    for s in SEEDS:
        t0 = time.time()
        A = fn_make_A(s)
        rec = measure_v3p(A, f"{label} s={s}", t0)
        rec["seed"] = s
        recs.append(rec)
        with open(OUT_PATH, "a") as f:
            f.write(json.dumps(rec) + "\n")
    v3ps = [r["v3p"] for r in recs]
    v1s = [r["v1"] for r in recs]
    sas = [r["sff_align"] for r in recs]
    gfs = [r["giant_frac"] for r in recs]
    gaps = [r["spectral_gap"] for r in recs]
    agg = {
        "label": label,
        "v3p_mean": round(float(np.mean(v3ps)), 5),
        "v3p_std": round(float(np.std(v3ps)), 5),
        "v1_mean": round(float(np.mean(v1s)), 5),
        "sff_align_mean": round(float(np.mean(sas)), 5),
        "giant_frac_mean": round(float(np.mean(gfs)), 5),
        "spectral_gap_mean": round(float(np.mean(gaps)), 5),
        "passes_0.9_count": sum(1 for v in v3ps if v >= 0.9),
        "n_seeds": len(SEEDS),
        "n_total": n_total,
    }
    with open(OUT_PATH, "a") as f:
        f.write(json.dumps({"aggregate": agg}) + "\n")
    print(f"  >> mean V3'={agg['v3p_mean']:.4f} ± {agg['v3p_std']:.4f}  passes_0.9={agg['passes_0.9_count']}/{len(SEEDS)}")
    return agg

# ---------- Probe definitions ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="reduce sweep to 3 fractions, 3 seeds")
    args = ap.parse_args()
    global SEEDS
    if args.quick:
        SEEDS = SEEDS[:3]

    # truncate output file for fresh run
    open(OUT_PATH, "w").close()
    with open(OUT_PATH, "a") as f:
        f.write(json.dumps({"baseline": {
            "v1": round(v1_base, 5), "sff_align": round(sff_align_base, 5),
            "v3p": round(v3p_base, 5), "n_base": n_base, "m_base": m_base,
            "avg_deg_base": round(avg_deg_base, 3),
        }}) + "\n")

    base_edges, base_seen = edges_unique(A_base)
    aggregates = []

    # ====== A. C4 fraction sweep ======
    print("\n=== A. Maslov-Sneppen rewire fraction sweep ===")
    fracs = [0.01, 0.05, 0.10, 0.20, 0.30, 0.50, 0.70, 1.00]
    if args.quick: fracs = [0.01, 0.10, 0.50]
    for frac in fracs:
        def make(seed, frac=frac):
            new_edges, _, _ = maslov_sneppen(base_edges, base_seen, frac, seed)
            return csr_from_edges(new_edges, n_base)
        aggregates.append(run_seeds(f"A.MS_frac={frac}", make, n_base))

    # ====== B. Rewire variants at frac=0.50 ======
    print("\n=== B. Rewire variants at frac=0.50 ===")
    target_swaps = int(len(base_edges) * 0.50)
    def make_ms(seed):
        new_edges, _, _ = maslov_sneppen(base_edges, base_seen, 0.50, seed)
        return csr_from_edges(new_edges, n_base)
    aggregates.append(run_seeds("B.MS_frac=0.50_ref", make_ms, n_base))

    def make_nx_swap(seed):
        new_edges, _, _ = nx_double_edge_swap(base_edges, n_base, target_swaps, seed)
        return csr_from_edges(new_edges, n_base)
    aggregates.append(run_seeds("B.nx_double_edge_swap_n=50%", make_nx_swap, n_base))

    def make_no_deg(seed):
        new_edges, _, _ = random_rewire_no_degree(base_edges, base_seen, 0.50, seed, n_base)
        return csr_from_edges(new_edges, n_base)
    aggregates.append(run_seeds("B.random_no_degree_pres_50%", make_no_deg, n_base))

    # ====== C. Random graph null models ======
    print("\n=== C. Random graph null models (replace atlas entirely) ===")
    # configuration model preserves degree sequence (∞-rewire limit)
    def make_config(seed):
        edges, n = configuration_model_from_degree(deg_base, seed)
        return csr_from_edges(edges, n)
    aggregates.append(run_seeds("C.configuration_model", make_config, n_base))

    # ER matching avg_deg
    def make_er(seed):
        edges = er_match_avg_deg(n_base, avg_deg_base, seed)
        return csr_from_edges(edges, n_base)
    aggregates.append(run_seeds(f"C.ER_avg_deg={avg_deg_base:.2f}", make_er, n_base))

    # BA preferential attachment, m=2 (avg_deg ~4 like base)
    def make_ba(seed):
        m_per = max(2, int(round(avg_deg_base / 2)))
        edges = ba_graph(n_base, m_per, seed)
        return csr_from_edges(edges, n_base)
    aggregates.append(run_seeds("C.BA_m=2", make_ba, n_base))

    # WS small-world
    def make_ws(seed):
        edges = ws_graph(n_base, 4, 0.10, seed)
        return csr_from_edges(edges, n_base)
    aggregates.append(run_seeds("C.WS_k=4_p=0.10", make_ws, n_base))

    # ====== Final summary table ======
    print("\n=== Summary (all aggregates) ===")
    print(f"baseline V3' = {v3p_base:.5f}")
    print(f"{'label':<35s} {'V3p_mean':>10s} {'V3p_std':>10s} {'pass/N':>8s} {'giant':>8s} {'gap':>8s}")
    for agg in aggregates:
        print(f"{agg['label']:<35s} {agg['v3p_mean']:>10.5f} {agg['v3p_std']:>10.5f} "
              f"{agg['passes_0.9_count']:>3d}/{agg['n_seeds']:<3d} {agg['giant_frac_mean']:>8.4f} {agg['spectral_gap_mean']:>8.4f}")

    # write summary record
    with open(OUT_PATH, "a") as f:
        f.write(json.dumps({"summary_aggregates": aggregates}) + "\n")
    print(f"\n[done] {len(aggregates)} aggregates written to {OUT_PATH}")

if __name__ == "__main__":
    main()
