#!/usr/bin/env python3
"""
beyond_omega_cycle23_meta_chain_analysis.py

Cycle 23 = meta-cycle: self-correction chain quantitative analysis.

Reads inventory.json entry `nxs-20260425-004` and extracts every
`cycle_N_finding_2026_04_25` block. For each cycle we derive:
  - cycle_id (int)
  - axis ("B" empirical / "A" transfinite / "theoretical" / "instrumentation")
  - verdict_type (confirm / falsify / partial / inconclusive / structural / baseline)
  - falsified_by (list of subsequent cycle ids that falsify this claim)
  - anchor_to_data (cycle_id list — earlier cycles cited as empirical anchor)
  - star_rating (number of leading "★" in `result`)

Then computes:
  - false_positive_ratio = #cycles falsified by later cycle / #total cycles
  - axis_crossing_count (B → A transition count when traversing in cycle order)
  - sentinel_discovery_rate_per_cycle = #sentinel commits / #cycles
  - mean_cycles_between_falsifications
  - chain_branching_factor (multi-facet groups like 15-17 P1/P2/P3)
  - fixed_points = claims confirmed by ≥2 subsequent cycles

Writes JSON to state/beyond_omega_cycle23_meta_chain_analysis.json.

No probe execution; pure data analysis. Cycle 23 = meta-cycle = cycle 5
"measurement back-action" applied second-order to the chain itself.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict

REPO = Path(__file__).resolve().parent.parent
INVENTORY = REPO / "state" / "proposals" / "inventory.json"
OUT_PATH = REPO / "state" / "beyond_omega_cycle23_meta_chain_analysis.json"

ENTRY_ID = "nxs-20260425-004"

# ----- helpers --------------------------------------------------------------

def load_entry():
    with INVENTORY.open() as f:
        inv = json.load(f)
    for ent in inv.get("entries", []):
        if ent.get("id") == ENTRY_ID:
            return ent
    raise SystemExit(f"entry {ENTRY_ID} not found in {INVENTORY}")


def cycle_blocks(entry):
    """Return [(cycle_id, block_dict), ...] sorted by cycle id."""
    pat = re.compile(r"^cycle_(\d+)(?:_first)?_finding_2026_04_25$")
    out = []
    for k, v in entry.items():
        m = pat.match(k)
        if not m:
            continue
        out.append((int(m.group(1)), k, v))
    out.sort(key=lambda t: t[0])
    return out


def classify_axis(block) -> str:
    axis_field = block.get("axis", "") or ""
    al = axis_field.lower()
    if "axis a" in al or "★ axis a" in al:
        return "A"
    if "axis b" in al:
        return "B"
    if "instrumentation" in al or "scaffolding" in al:
        return "instrumentation"
    if "theoretical" in al:
        return "theoretical"
    # Fallback heuristics.
    if "tool" in block and ("transfinite" in str(block.get("tool", "")).lower()
                             or "epsilon" in str(block.get("tool", "")).lower()
                             or "omega_one" in str(block.get("tool", "")).lower()):
        return "theoretical"
    return "B"  # cycles 1-6 default


def classify_verdict(block) -> str:
    """confirm / falsify / partial / inconclusive / structural / baseline / instrumentation"""
    result = (block.get("result", "") or "").upper()
    cycle_status = (block.get("cycle_1_first_finding_2026_04_25", {})
                    .get("status", "") if isinstance(block.get("cycle_1_first_finding_2026_04_25"), dict)
                    else "")
    if "BASELINE_ZERO" in result:
        return "baseline"
    if "STRUCTURAL_SENTINEL" in result or "STRUCTURAL" in result and "SENTINEL" in result:
        return "structural"
    if "INCONCLUSIVE" in result:
        return "inconclusive"
    if "PARTIAL" in result or "PARTIAL_ACCESS" in result or "FALSIFY_CANDIDATE" in result:
        return "partial"
    if "CONFIRM" in result or "REACHED" in result or "APPROACH_OBSERVED" in result \
       or "LINEAR" in result or "POLYNOMIAL" in result or "APPROACH" in result \
       or "MAPPING_TABLE" in result or "OVERLAP" in result \
       or "BACK-ACTION" in result or "BACK_ACTION" in result \
       or "DISPATCH_ONLY" in result or "DISPATCH_TERMINATED" in result \
       or "REGISTERED" in result or "COMMITTED" in result:
        return "confirm"
    return "other"


def find_falsified_by(cycle_id, block, all_blocks_idx) -> list[int]:
    """Scan forward in chain for claims falsifying this one.

    Heuristics:
      - block self-tags 'FALSIFIED by cycle N' anywhere -> N
      - 'self_correction_chain' field of later cycles mentioning '[false-positive]'
        adjacent to this cycle id
      - explicit `cycle_N_predicted_next_step` lineage
    """
    falsifier_ids: set[int] = set()
    blob = json.dumps(block, ensure_ascii=False)
    for m in re.finditer(r"FALSIFIED by cycle (\d+)", blob):
        falsifier_ids.add(int(m.group(1)))

    # cross-cycle scan: any later cycle's chain string flags this cycle as false-positive
    for cid_other, _key, b_other in all_blocks_idx:
        if cid_other <= cycle_id:
            continue
        chain_str = b_other.get("self_correction_chain_updated") \
                    or b_other.get("self_correction_chain", "") or ""
        if not chain_str:
            continue
        # look for pattern "cycle <cycle_id> ... [false-positive]" OR
        # "cycle <cycle_id> ... FALSIFIED"
        pat = re.compile(rf"cycle\s*{cycle_id}\b[^→]*?\[?false[-_ ]?positive\]?",
                         re.IGNORECASE)
        if pat.search(chain_str):
            falsifier_ids.add(cid_other)
    return sorted(falsifier_ids)


def find_anchors(block) -> list[int]:
    """Cycle ids cited as empirical anchor (anchor_to_data, key_finding text)."""
    anchors: set[int] = set()
    if isinstance(block.get("anchor_to_data"), dict):
        for k in block["anchor_to_data"].keys():
            m = re.match(r"cycle_(\d+)_anchor", k)
            if m:
                anchors.add(int(m.group(1)))
    blob = json.dumps(block, ensure_ascii=False)
    for m in re.finditer(r"cycle\s*(\d+)\s*(?:confirmed|anchor|first positive|empirical|implied|prediction|baseline|finding)",
                         blob, re.IGNORECASE):
        anchors.add(int(m.group(1)))
    return sorted(anchors)


def star_count(block) -> int:
    result = block.get("result", "") or ""
    key = block.get("key_finding_★", "") or block.get("key_finding_★★", "") or ""
    s = result + " " + key
    # count leading-style ★ in result
    m = re.match(r"^(★+)", result.strip())
    raw = len(m.group(1)) if m else 0
    # also count any ★ tokens — pick max
    tokens = s.count("★")
    return max(raw, min(tokens, 2))


# ----- main analysis --------------------------------------------------------

def main():
    entry = load_entry()
    blocks = cycle_blocks(entry)  # [(cid, key, block), ...]

    rows = []
    sentinel_targets = []
    for cid, key, block in blocks:
        axis = classify_axis(block)
        verdict = classify_verdict(block)
        falsified_by = find_falsified_by(cid, block, blocks)
        anchors = find_anchors(block)
        stars = star_count(block)
        result = block.get("result", "")

        # detect sentinel claims (any L_{...}_SENTINEL_* / STRUCTURAL_SENTINEL / ε₀/ω₁ etc.)
        is_sentinel_commit = False
        for tok in ("SENTINEL_COMMITTED", "SENTINEL_CONFIRM", "STRUCTURAL_SENTINEL"):
            if tok in str(result):
                is_sentinel_commit = True
        if is_sentinel_commit:
            # extract ordinal tag
            m = re.search(r"L_\{([^}]+)\}", str(result))
            sentinel_targets.append({"cycle": cid,
                                     "ordinal": m.group(1) if m else "?",
                                     "verdict": verdict})

        rows.append({
            "cycle_id": cid,
            "block_key": key,
            "axis": axis,
            "verdict_type": verdict,
            "falsified_by": falsified_by,
            "anchor_to_data": anchors,
            "star_rating": stars,
            "result_head": (result[:120] if isinstance(result, str) else str(result)[:120]),
        })

    # statistics ------------------------------------------------------------
    n_total = len(rows)
    n_falsified = sum(1 for r in rows if r["falsified_by"])
    fp_ratio = round(n_falsified / n_total, 4) if n_total else 0.0

    # axis distribution + crossings
    axes_seq = [r["axis"] for r in rows]
    axis_dist = dict(Counter(axes_seq))
    axis_crossings_b_to_a = sum(
        1 for prev, cur in zip(axes_seq, axes_seq[1:])
        if prev == "B" and cur == "A"
    )

    # sentinel discovery rate
    n_sentinel = len(sentinel_targets)
    sentinel_rate = round(n_sentinel / n_total, 4) if n_total else 0.0

    # mean cycles between falsifications (gap from claim cycle to first falsifier)
    gaps = []
    for r in rows:
        if r["falsified_by"]:
            gaps.append(min(r["falsified_by"]) - r["cycle_id"])
    mean_gap = round(sum(gaps) / len(gaps), 4) if gaps else None

    # chain branching factor — adjacent cycles that probe same target with different facets
    # cycles 15/16/17 all probe L_{ε₀} via P1/P2/P3 = branching cluster
    # cycles 18/19 probe L_{Γ₀} & L_{ω₁^CK} (separate); count via shared sentinel substring in result
    target_clusters = defaultdict(list)
    for r in rows:
        result = r["result_head"]
        m = re.search(r"L_\{([^}]+)\}", result)
        if m:
            target_clusters[m.group(1)].append(r["cycle_id"])
    branching = {tgt: cids for tgt, cids in target_clusters.items() if len(cids) >= 2}
    branching_factor = round(
        sum(len(v) for v in branching.values()) / len(branching), 4
    ) if branching else 0.0

    # fixed points: cycles cited as anchor by ≥2 later cycles
    anchor_refcount = Counter()
    for r in rows:
        for a in r["anchor_to_data"]:
            if a < r["cycle_id"]:
                anchor_refcount[a] += 1
    fixed_points = sorted([cid for cid, n in anchor_refcount.items() if n >= 2])

    # convergence test: false-positive count over rolling windows of 5 cycles
    rolling_fp = []
    if n_total >= 5:
        for i in range(0, n_total - 4):
            window = rows[i:i + 5]
            wfp = sum(1 for r in window if r["falsified_by"])
            rolling_fp.append({"window_start_cycle": window[0]["cycle_id"],
                               "window_end_cycle": window[-1]["cycle_id"],
                               "fp_count": wfp})

    converging = None
    if rolling_fp:
        first = rolling_fp[0]["fp_count"]
        last = rolling_fp[-1]["fp_count"]
        if last < first:
            converging = "convergent"
        elif last > first:
            converging = "diverging"
        else:
            converging = "stable"

    # axis dominance verdict
    dominant_axis = max(axis_dist.items(), key=lambda kv: kv[1])[0] if axis_dist else None

    # epistemic-stable ordinal level: highest sentinel that is anchor for ≥2 later cycles
    # sentinels: collect ordinal of sentinels, then check anchor refcount of their cycle
    sentinel_anchor_refcount = []
    for s in sentinel_targets:
        refcount = anchor_refcount.get(s["cycle"], 0)
        sentinel_anchor_refcount.append({"cycle": s["cycle"],
                                         "ordinal": s["ordinal"],
                                         "anchor_refcount": refcount})
    epistemic_stable = None
    stable_candidates = [s for s in sentinel_anchor_refcount if s["anchor_refcount"] >= 2]
    if stable_candidates:
        # pick latest cycle (highest ordinal in chain order)
        epistemic_stable = max(stable_candidates, key=lambda s: s["cycle"])

    # meta-finding
    meta_finding = {
        "chain_status": converging,
        "rationale": (
            "rolling 5-cycle false-positive window shrinks from "
            f"{rolling_fp[0]['fp_count'] if rolling_fp else '?'} (cycles "
            f"{rolling_fp[0]['window_start_cycle'] if rolling_fp else '?'}-"
            f"{rolling_fp[0]['window_end_cycle'] if rolling_fp else '?'}) to "
            f"{rolling_fp[-1]['fp_count'] if rolling_fp else '?'} (cycles "
            f"{rolling_fp[-1]['window_start_cycle'] if rolling_fp else '?'}-"
            f"{rolling_fp[-1]['window_end_cycle'] if rolling_fp else '?'})."
        ),
        "dominant_axis": dominant_axis,
        "axis_distribution": axis_dist,
        "epistemic_stable_ordinal": epistemic_stable,
    }

    out = {
        "schema": "nexus.beyond_omega.cycle23_meta_chain_analysis.v1",
        "generated_ts": "2026-04-25T13:45:00Z",
        "entry_id": ENTRY_ID,
        "n_total_cycles": n_total,
        "per_cycle_rows": rows,
        "statistics": {
            "false_positive_count": n_falsified,
            "false_positive_ratio": fp_ratio,
            "axis_distribution": axis_dist,
            "axis_crossings_b_to_a": axis_crossings_b_to_a,
            "sentinel_discovery_count": n_sentinel,
            "sentinel_discovery_rate_per_cycle": sentinel_rate,
            "mean_cycles_between_falsification": mean_gap,
            "branching_clusters": branching,
            "branching_factor": branching_factor,
            "fixed_points": fixed_points,
            "anchor_refcount": dict(anchor_refcount),
            "rolling_5cycle_fp": rolling_fp,
        },
        "sentinel_targets": sentinel_targets,
        "meta_finding": meta_finding,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    # console summary -------------------------------------------------------
    print(f"[cycle23-meta] cycles analyzed: {n_total}")
    print(f"[cycle23-meta] false-positive ratio: {fp_ratio} ({n_falsified}/{n_total})")
    print(f"[cycle23-meta] axis distribution: {axis_dist}")
    print(f"[cycle23-meta] B→A crossings: {axis_crossings_b_to_a}")
    print(f"[cycle23-meta] sentinel discovery rate: {sentinel_rate} ({n_sentinel}/{n_total})")
    print(f"[cycle23-meta] mean cycles to falsification: {mean_gap}")
    print(f"[cycle23-meta] branching clusters: {branching}")
    print(f"[cycle23-meta] fixed points (≥2 anchors): {fixed_points}")
    print(f"[cycle23-meta] meta verdict: {meta_finding['chain_status']} | "
          f"dominant axis: {dominant_axis} | epistemic stable: {epistemic_stable}")
    print(f"[cycle23-meta] wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
