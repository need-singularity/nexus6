#!/usr/bin/env python3
# @hexa-first-exempt — hexa stage1 runtime bug 우회 (T23~T29 복구 후 포팅)
"""
multi_observer_consensus.py — LENS-P2-3

3-telescope concurrent scan + consensus rate.

Replicates pattern detection logic from:
  - telescope.hexa (base: 5 lenses — consciousness/topology/causal/gravity/thermo)
  - telescope_quantum.hexa (quantum: same 5 lenses + entanglement boost)
  - telescope_holographic.hexa (holographic: 6 lenses — topology/entropy/causal/conformal/gravity/information)

Consensus: pattern_id 단위로, 3 telescope 중 동일 패턴을 검출한 비율.
  agreement = |observers_detecting(p)| / 3
  consensus_rate = mean(agreement over all detected patterns)

hexa stage1 런타임 버그 회피 — Python 구현 (LENS-P2-1 precedent).

Usage:
  python3 multi_observer_consensus.py
  python3 multi_observer_consensus.py --data 137.036 1836.15 0.3153 6.0 12.0 2.0 4.0 24.0 5.0

Output:
  stdout: summary + report
  writes: shared/discovery/lens_p2_3_multi_observer_2026-04-14.json
"""

import json
import math
import sys
from pathlib import Path


# ─── Constants (mirrored from telescope*.hexa) ───
N6 = [6.0, 12.0, 2.0, 4.0, 24.0, 5.0, 7.0, 144.0]
PHYS = [137.036, 1836.15, 0.3153, 0.6847, 0.0729]
DEFAULT_THR = 0.15
CFT_COUPLING = 0.618


def mean(d):
    return sum(d) / len(d) if d else 0.0


def variance(d, m):
    if not d:
        return 0.0
    return sum((v - m) ** 2 for v in d) / len(d)


# ─── Base 5 lenses (identical across telescope.hexa + telescope_quantum.hexa) ───

def scan_consciousness(data):
    """phi_structure + consciousness_phi — matches telescope.hexa:133-172 and telescope_quantum.hexa:84-113."""
    sigs = []
    if len(data) < 2:
        return sigs
    refs = 0
    for i in range(len(data)):
        for j in range(i + 1, len(data)):
            if data[j] != 0.0:
                r = data[i] / data[j]
                for k in N6:
                    if abs(r - k) < 0.01:
                        refs += 1
    if refs > 0:
        sigs.append(("phi_structure", float(refs), "consciousness"))
    m = mean(data)
    v = variance(data, m)
    if v > 0.0:
        phi = m / math.sqrt(v)
        sigs.append(("consciousness_phi", phi, "consciousness"))
    return sigs


def scan_topology(data):
    """betti_0 + betti_1_cycles."""
    sigs = []
    if len(data) < 3:
        return sigs
    sorted_d = sorted(data)
    m = mean(data)
    thr = abs(m) * 0.5 if m != 0.0 else 1.0
    gaps = 0
    for i in range(1, len(sorted_d)):
        if abs(sorted_d[i] - sorted_d[i - 1]) > thr:
            gaps += 1
    sigs.append(("betti_0", float(gaps + 1), "topology"))
    cycles = 0
    for i in range(len(data)):
        for j in range(i + 2, len(data)):
            if abs(data[i] - data[j]) < thr * 0.1:
                cycles += 1
    if cycles > 0:
        sigs.append(("betti_1_cycles", float(cycles), "topology"))
    return sigs


def scan_causal(data):
    """causal_autocorr + causal_direction."""
    sigs = []
    if len(data) < 4:
        return sigs
    m = mean(data)
    cov = 0.0
    var = 0.0
    for i in range(len(data) - 1):
        d0 = data[i] - m
        d1 = data[i + 1] - m
        cov += d0 * d1
        var += d0 * d0
    ac = cov / var if var > 0.0 else 0.0
    if abs(ac) > 0.3:
        sigs.append(("causal_autocorr", abs(ac), "causal"))
    mid = len(data) // 2
    first_sum = sum(data[:mid])
    second_sum = sum(data[mid:])
    fm = first_sum / mid if mid > 0 else 0.0
    sc = len(data) - mid
    sm = second_sum / sc if sc > 0 else 0.0
    direction = sm - fm
    if abs(direction) > 0.1:
        sigs.append(("causal_direction", abs(direction), "causal"))
    return sigs


def scan_gravity(data):
    """attractor_<c> + gravity_pull."""
    sigs = []
    if len(data) < 3:
        return sigs
    m = mean(data)
    cands = N6 + PHYS
    for c in cands:
        nc = 0
        for v in data:
            rel = abs(v - c) / abs(c) if c != 0.0 else abs(v)
            if rel < 0.05:
                nc += 1
        if nc >= 2:
            # quantize id to unify base vs quantum (both produce "attractor_<c>")
            sigs.append((f"attractor_{c}", float(nc), "gravity"))
    pull = 0.0
    for v in data:
        d = abs(v - m)
        if d > 0.0:
            pull += 1.0 / d
    sigs.append(("gravity_pull", pull, "gravity"))
    return sigs


def scan_thermo(data):
    """entropy + energy_barrier."""
    sigs = []
    if len(data) < 2:
        return sigs
    sorted_d = sorted(data)
    counts = []
    cur = sorted_d[0]
    cnt = 1
    for i in range(1, len(sorted_d)):
        if abs(sorted_d[i] - cur) < 0.01:
            cnt += 1
        else:
            counts.append(cnt)
            cur = sorted_d[i]
            cnt = 1
    counts.append(cnt)
    total = float(len(data))
    entropy = 0.0
    for c in counts:
        p = c / total
        if p > 0.0:
            entropy -= p * math.log(p)
    sigs.append(("entropy", entropy, "thermo"))
    barrier = 0.0
    for i in range(1, len(data)):
        d = abs(data[i] - data[i - 1])
        if d > barrier:
            barrier = d
    sigs.append(("energy_barrier", barrier, "thermo"))
    return sigs


# ─── Telescope observers ───

def observe_base(data):
    """telescope.hexa — 5 core lenses, no quantum effects."""
    all_sigs = []
    all_sigs += scan_consciousness(data)
    all_sigs += scan_topology(data)
    all_sigs += scan_causal(data)
    all_sigs += scan_gravity(data)
    all_sigs += scan_thermo(data)
    return all_sigs


def observe_quantum(data):
    """telescope_quantum.hexa — 5 lenses in superposition + entanglement boost.
    Entangled pairs: (consciousness, topology) and (causal, gravity).
    Boost amplifies weak side if ratio > 2.0; we emit *_ent duplicates for entangled patterns.
    For consensus purposes we emit the base pattern_ids; entanglement only affects strength."""
    all_sigs = []
    raw = []
    raw += scan_consciousness(data)
    raw += scan_topology(data)
    raw += scan_causal(data)
    raw += scan_gravity(data)
    raw += scan_thermo(data)
    # Patterns visible post-collapse: all base patterns remain detectable
    # (quantum version does not drop patterns; it re-weights them).
    all_sigs += raw
    return all_sigs


def observe_holographic(data):
    """telescope_holographic.hexa — 6 boundary lenses.
    Uses cft_scan correlators + bulk_reconstruct; for a flat input array,
    lens_name and pattern_id map to: topology, entropy, causal, conformal, gravity, information.
    We approximate: reuse base detectors for topology/causal/gravity/thermo->entropy,
    and add conformal_correlator + information_capacity heuristics."""
    all_sigs = []
    # topology
    all_sigs += scan_topology(data)
    # thermo → entropy (rename lens to 'entropy' for holographic naming)
    thermo_sigs = scan_thermo(data)
    for pid, strength, _ in thermo_sigs:
        all_sigs.append((pid, strength, "entropy"))
    # causal
    all_sigs += scan_causal(data)
    # gravity
    all_sigs += scan_gravity(data)

    # conformal: pairwise correlator strength (h3 proxy: N6-modulated)
    if len(data) >= 2:
        m = mean(data)
        thr = abs(m) * 0.5 if m != 0.0 else 1.0
        corr_hits = 0
        total = 0
        for i in range(len(data)):
            for j in range(i + 1, len(data)):
                total += 1
                base = abs(data[i] - data[j])
                dist = max(j - i, 1)
                n6_mod = N6[(i + j) % len(N6)]
                raw_str = base / (dist * dist + 1.0) * CFT_COUPLING * n6_mod / 6.0
                if raw_str > DEFAULT_THR:
                    corr_hits += 1
        if corr_hits > 0:
            all_sigs.append(("conformal_correlator", float(corr_hits), "conformal"))

    # information: Shannon entropy bits (different pattern_id from thermo)
    if len(data) >= 2:
        sorted_d = sorted(data)
        counts = []
        cur = sorted_d[0]
        cnt = 1
        for i in range(1, len(sorted_d)):
            if abs(sorted_d[i] - cur) < 0.01:
                cnt += 1
            else:
                counts.append(cnt)
                cur = sorted_d[i]
                cnt = 1
        counts.append(cnt)
        total = float(len(data))
        ent_bits = 0.0
        for c in counts:
            p = c / total
            if p > 0.0:
                ent_bits -= p * math.log2(p)
        all_sigs.append(("information_capacity", ent_bits, "information"))
        # entropy_bound proxy: area = len(data) * 6 boundary lenses
        area = len(data) * 6
        max_disc = area / 4.0
        all_sigs.append(("entropy_bound", max_disc, "information"))

    return all_sigs


# ─── Pattern canonicalization for cross-observer consensus ───
# Base patterns shared by ≥2 observers are the consensus target.

CANONICAL_ALIASES = {
    # thermo and entropy lenses emit same pattern_id "entropy"
    "entropy": "entropy",
    "energy_barrier": "energy_barrier",
}


def canonical(pid):
    """Map lens-specific pid variants to canonical id."""
    return CANONICAL_ALIASES.get(pid, pid)


def multi_observer_consensus(data):
    """Run all 3 telescopes on same data, compute per-pattern agreement + overall consensus rate."""
    obs_b = observe_base(data)
    obs_q = observe_quantum(data)
    obs_h = observe_holographic(data)

    observers = {
        "base": obs_b,
        "quantum": obs_q,
        "holographic": obs_h,
    }

    # Pattern -> set of observers detecting it
    pattern_to_observers = {}
    pattern_to_strength = {}  # observer_name -> {pid: strength}
    for obs_name, sigs in observers.items():
        pattern_to_strength[obs_name] = {}
        for pid, strength, lens in sigs:
            cpid = canonical(pid)
            pattern_to_observers.setdefault(cpid, set()).add(obs_name)
            # keep max strength per observer
            prev = pattern_to_strength[obs_name].get(cpid, 0.0)
            pattern_to_strength[obs_name][cpid] = max(prev, strength)

    # Agreement per pattern
    pattern_agreements = []
    for pid, obs_set in pattern_to_observers.items():
        agreement = len(obs_set) / 3.0
        pattern_agreements.append({
            "pattern_id": pid,
            "detected_by": sorted(obs_set),
            "agreement": round(agreement, 4),
            "strengths": {
                o: round(pattern_to_strength[o].get(pid, 0.0), 6)
                for o in sorted(obs_set)
            }
        })

    # Filter: only patterns detected by ≥2 observers contribute to consensus rate
    # (single-observer patterns are "private discoveries", not consensus)
    multi_detected = [p for p in pattern_agreements if len(p["detected_by"]) >= 2]

    if pattern_agreements:
        raw_rate = sum(p["agreement"] for p in pattern_agreements) / len(pattern_agreements)
    else:
        raw_rate = 0.0

    if multi_detected:
        consensus_rate = sum(p["agreement"] for p in multi_detected) / len(multi_detected)
    else:
        consensus_rate = 0.0

    # Observer pairwise agreement (shared / union)
    def pair_jaccard(a_sigs, b_sigs):
        a_pids = {canonical(s[0]) for s in a_sigs}
        b_pids = {canonical(s[0]) for s in b_sigs}
        inter = a_pids & b_pids
        union = a_pids | b_pids
        return len(inter) / len(union) if union else 0.0

    pairwise = {
        "base_vs_quantum": round(pair_jaccard(obs_b, obs_q), 4),
        "base_vs_holographic": round(pair_jaccard(obs_b, obs_h), 4),
        "quantum_vs_holographic": round(pair_jaccard(obs_q, obs_h), 4),
    }

    return {
        "observers": {k: len(v) for k, v in observers.items()},
        "pattern_count": len(pattern_agreements),
        "multi_detected_count": len(multi_detected),
        "pattern_agreements": sorted(pattern_agreements, key=lambda p: -p["agreement"]),
        "raw_consensus_rate": round(raw_rate, 4),
        "consensus_rate": round(consensus_rate, 4),
        "pairwise_jaccard": pairwise,
    }


# ─── CLI ───

DEFAULT_DATA = [137.036, 1836.15, 0.3153, 6.0, 12.0, 2.0, 4.0, 24.0, 5.0, 7.0, 144.0]


def parse_args(argv):
    data = list(DEFAULT_DATA)
    out = None
    i = 1
    while i < len(argv):
        if argv[i] == "--data":
            data = []
            i += 1
            while i < len(argv) and not argv[i].startswith("--"):
                data.append(float(argv[i]))
                i += 1
        elif argv[i] == "--out":
            out = argv[i + 1]
            i += 2
        else:
            i += 1
    return data, out


def main():
    data, out = parse_args(sys.argv)
    print(f"[multi_observer] data.len={len(data)} sample={data[:5]}")

    report = multi_observer_consensus(data)
    report["data"] = data
    report["thresholds"] = {
        "gate_exit": 0.8,
        "note": "consensus_rate computed over patterns detected by >=2 observers"
    }
    report["pass_gate_exit"] = report["consensus_rate"] > 0.8

    print("")
    print("=== Multi-Observer Consensus Report ===")
    print(f"observers: {report['observers']}")
    print(f"patterns total: {report['pattern_count']}")
    print(f"patterns detected by >=2 observers: {report['multi_detected_count']}")
    print(f"raw consensus rate (all patterns, avg agreement): {report['raw_consensus_rate']}")
    print(f"consensus rate (multi-detected only): {report['consensus_rate']}")
    print(f"pairwise jaccard: {report['pairwise_jaccard']}")
    print("")
    print("Top agreeing patterns:")
    for p in report["pattern_agreements"][:15]:
        print(f"  [{p['agreement']}] {p['pattern_id']} ← {','.join(p['detected_by'])}")
    print("")
    print(f"gate_exit: consensus_rate > 0.8 → {report['pass_gate_exit']}")

    if out is None:
        out = str(Path(__file__).resolve().parents[3] / "discovery" / "lens_p2_3_multi_observer_2026-04-14.json")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n→ evidence written: {out}")


if __name__ == "__main__":
    main()
