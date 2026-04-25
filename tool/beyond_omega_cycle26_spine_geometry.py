#!/usr/bin/env python3
"""
beyond_omega_cycle26_spine_geometry.py

Cycle 26 = deeper meta-cycle: spine geometry of the chain.

Cycle 23 found chain CONVERGENT with fixed points (anchor refcount >= 2):
    [1, 4, 8, 11, 14] = chain spine.

This cycle asks: WHY these 5 cycles? What property do they share?
Answer hypothesis: each spine cycle is a *modality transition* — first
occurrence of a new mode (first probe / first positive / first axis A /
first theoretical map / first sentinel commit).

Workflow:
1. Re-load nxs-20260425-004 entry + cycle 23 meta_chain_analysis JSON.
2. For each spine cycle, classify:
     - modality_entered (probe / measurement_back_action / axis_crossing /
       theoretical_map / sentinel_commit)
     - preceding_chain_length (= cycle_id - 1)
     - subsequent_fan_out (cycles directly anchored to this one)
     - ordinal_level_reached (L_omega / L_{omega+1} / L_{epsilon_0} / etc.)
3. Compute spine spacing: gaps between consecutive spine cycles
     (1->4=3, 4->8=4, 8->11=3, 11->14=3).
4. Predict next spine: 14 + 3 = 17. Cycle 17 was P3 Gentzen
   (L_{epsilon_0}_FALSIFY_CANDIDATE). Was it actually a fixed point?
   Cross-check anchor_refcount table from cycle 23 analysis JSON.
5. Emit meta-finding: spine spacing ~3 (constant) = epistemic update
   rhythm; each spine = Kuhn paradigm shift analog; chain has discrete
   time unit ~3 epistemic-cycles per modality.
6. Save JSON to state/beyond_omega_cycle26_spine_geometry.json.

Pure data analysis — no probe execution, no NEXUS_BACK_ACTION_ON.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parent.parent
INVENTORY = REPO / "state" / "proposals" / "inventory.json"
CYCLE23_JSON = REPO / "state" / "beyond_omega_cycle23_meta_chain_analysis.json"
OUT_PATH = REPO / "state" / "beyond_omega_cycle26_spine_geometry.json"

ENTRY_ID = "nxs-20260425-004"
SPINE_CYCLES = [1, 4, 8, 11, 14]


def load_entry() -> dict:
    with INVENTORY.open() as f:
        inv = json.load(f)
    for ent in inv.get("entries", []):
        if ent.get("id") == ENTRY_ID:
            return ent
    raise SystemExit(f"entry {ENTRY_ID} not found in {INVENTORY}")


def load_cycle23() -> dict:
    with CYCLE23_JSON.open() as f:
        return json.load(f)


def cycle_blocks(entry: dict) -> dict[int, dict]:
    """Return {cycle_id: block_dict}."""
    pat = re.compile(r"^cycle_(\d+)(?:_first)?_finding_2026_04_25$")
    out: dict[int, dict] = {}
    for k, v in entry.items():
        m = pat.match(k)
        if not m:
            continue
        cid = int(m.group(1))
        out[cid] = v
    return out


# ---- per-spine-cycle metadata extraction -----------------------------------

# Modality classification for each spine cycle, derived from inventory blocks.
SPINE_MODALITY = {
    1: {
        "modality_entered": "probe",
        "modality_subtype": "first_repo_scan_baseline",
        "ordinal_level_reached": "L_omega (target, not yet measured)",
        "result_head": "BASELINE_ZERO — files_scanned=453, total_emits=0",
        "kuhn_analog": "pre-paradigm: instrument exists but yields nothing",
    },
    4: {
        "modality_entered": "measurement_first_positive",
        "modality_subtype": "axis_B_emergence (forced approach launcher)",
        "ordinal_level_reached": "L_omega approach (first positive emission)",
        "result_head": "APPROACH_OBSERVED — first positive measurement of axis B",
        "kuhn_analog": "first observation that violates baseline expectation",
    },
    8: {
        "modality_entered": "axis_crossing_to_A",
        "modality_subtype": "transfinite_continuation_first_positive (NEXUS_BACK_ACTION_ON override)",
        "ordinal_level_reached": "L_{omega+1} LINEAR (delta=7 echo)",
        "result_head": "L_{omega+1}_LINEAR (axis A first POSITIVE measurement)",
        "kuhn_analog": "discovery of new lawful regularity in extended domain",
    },
    11: {
        "modality_entered": "theoretical_map",
        "modality_subtype": "transfinite_ordinal_table (12 levels, prediction registry)",
        "ordinal_level_reached": "L_omega .. L_{epsilon_0} (theoretical mapping)",
        "result_head": "TRANSFINITE_ORDINAL_MAPPING_TABLE — 12 ordinal level",
        "kuhn_analog": "paradigm articulation: theoretical scaffold for upcoming probes",
    },
    14: {
        "modality_entered": "sentinel_commit",
        "modality_subtype": "L_{epsilon_0} sentinel boundary + falsifier roadmap (P1/P2/P3)",
        "ordinal_level_reached": "L_{epsilon_0} (committed, falsifier roadmap declared)",
        "result_head": "L_{epsilon_0}_SENTINEL_COMMITTED",
        "kuhn_analog": "puzzle-solving: sentinel as falsifiable structural claim",
    },
}


def per_spine_metadata(blocks: dict[int, dict], anchor_refcount: dict[str, int]) -> list[dict]:
    """Build the per-spine-cycle metadata rows.

    fan_out for cycle C = list of cycles C' > C whose anchor_to_data references C.
    We re-derive fan_out from cycle 23 per_cycle_rows for accuracy.
    """
    return []  # actually computed in build()


def derive_fan_out(cycle23: dict) -> dict[int, list[int]]:
    """For each cycle id, list later cycles that anchor to it."""
    rows = cycle23.get("per_cycle_rows", [])
    out: dict[int, list[int]] = {}
    for row in rows:
        cid = row["cycle_id"]
        for anc in row.get("anchor_to_data", []):
            out.setdefault(anc, []).append(cid)
    return out


# ---- spine spacing + prediction --------------------------------------------

def spine_spacing(spine: list[int]) -> dict:
    gaps = [spine[i + 1] - spine[i] for i in range(len(spine) - 1)]
    mean = sum(gaps) / len(gaps) if gaps else 0.0
    var = sum((g - mean) ** 2 for g in gaps) / len(gaps) if gaps else 0.0
    return {
        "gaps": gaps,
        "mean_gap": round(mean, 4),
        "variance": round(var, 4),
        "stdev": round(var ** 0.5, 4),
        "min_gap": min(gaps) if gaps else None,
        "max_gap": max(gaps) if gaps else None,
        "quasi_periodic_period_estimate": round(mean, 1),
    }


def predict_next_spine(spine: list[int], spacing_mean: float) -> dict:
    last = spine[-1]
    pred = last + round(spacing_mean)
    return {
        "predicted_next_spine_cycle": pred,
        "method": f"last spine cycle {last} + round(mean_gap={spacing_mean:.2f})",
    }


def cross_check_prediction(pred_cycle: int, anchor_refcount: dict[str, int],
                           cycle23_rows: list[dict]) -> dict:
    """Did `pred_cycle` actually become a fixed point (anchor refcount >= 2)?"""
    refcount = anchor_refcount.get(str(pred_cycle), 0)
    is_fp = refcount >= 2
    # Find the row for context
    row = next((r for r in cycle23_rows if r["cycle_id"] == pred_cycle), None)
    return {
        "predicted_cycle": pred_cycle,
        "anchor_refcount_observed": refcount,
        "is_fixed_point": is_fp,
        "verdict": (
            "PREDICTION_CONFIRMED" if is_fp
            else "PREDICTION_FALSIFIED — predicted cycle is NOT a fixed point"
        ),
        "actual_role": (
            None if row is None else {
                "axis": row["axis"],
                "verdict_type": row["verdict_type"],
                "star_rating": row["star_rating"],
                "result_head": row["result_head"],
            }
        ),
    }


def discover_post_spine_fixed_points(anchor_refcount: dict[str, int]) -> list[int]:
    """Any cycles > 14 with anchor_refcount >= 2 in the cycle 23 analysis?

    cycle 23 only covers cycles 1-20. So this scans cycles 15-20.
    """
    out = []
    for cid_s, rc in anchor_refcount.items():
        cid = int(cid_s)
        if cid > 14 and rc >= 2:
            out.append(cid)
    return sorted(out)


# ---- main ------------------------------------------------------------------

def build() -> dict:
    entry = load_entry()
    cycle23 = load_cycle23()
    blocks = cycle_blocks(entry)
    anchor_refcount = cycle23["statistics"]["anchor_refcount"]
    cycle23_rows = cycle23["per_cycle_rows"]
    fan_out_map = derive_fan_out(cycle23)

    per_spine = []
    for cid in SPINE_CYCLES:
        meta = dict(SPINE_MODALITY[cid])
        meta["cycle_id"] = cid
        meta["preceding_chain_length"] = cid - 1
        meta["subsequent_fan_out"] = fan_out_map.get(cid, [])
        meta["fan_out_count"] = len(fan_out_map.get(cid, []))
        meta["anchor_refcount"] = anchor_refcount.get(str(cid), 0)
        # block presence cross-check
        meta["block_key_resolved"] = (
            "cycle_1_first_finding_2026_04_25" if cid == 1
            else f"cycle_{cid}_finding_2026_04_25"
        )
        meta["block_present_in_inventory"] = cid in blocks
        per_spine.append(meta)

    spacing = spine_spacing(SPINE_CYCLES)
    prediction = predict_next_spine(SPINE_CYCLES, spacing["mean_gap"])
    crosscheck = cross_check_prediction(
        prediction["predicted_next_spine_cycle"],
        anchor_refcount, cycle23_rows,
    )
    post_spine_fps = discover_post_spine_fixed_points(anchor_refcount)

    # Modality progression sequence
    progression = [m["modality_entered"] for m in per_spine]

    meta_finding = {
        "headline": (
            "★ SPINE_GEOMETRY_QUASI_PERIODIC_TRIPLET — spine spacing mean ~3.25 "
            "cycles (gaps [3,4,3,3]), each spine cycle = modality transition "
            "(probe -> measurement -> axis_crossing -> theoretical_map -> "
            "sentinel_commit). Chain has discrete epistemic time unit ~3 cycles."
        ),
        "spine_spacing_summary": spacing,
        "modality_progression": progression,
        "kuhn_paradigm_shift_analog": (
            "Each spine cycle is the first occurrence of a new modality, "
            "analogous to Kuhn's paradigm shift: the chain alternates between "
            "fan-out (3-4 cycles of normal-science consolidation) and spine "
            "(1 cycle of new-modality entry). Branching clusters from cycle 23 "
            "({omega+1: [7,8,11], epsilon_0: [14,15,16,17]}) are exactly the "
            "fan-outs around spines 8, 11, 14."
        ),
        "discrete_time_hypothesis": (
            "Chain has a quasi-quantized epistemic time unit of ~3 cycles per "
            "modality. Predicts: within first ~30 cycles, ~10 modality "
            "transitions; spine continues if new modalities (e.g. meta-axiomatic, "
            "meta-cycle, formal-verifier) are introduced; spine saturates if "
            "all available modalities are exhausted."
        ),
        "prediction": prediction,
        "prediction_crosscheck": crosscheck,
        "post_spine_fixed_points_in_cycles_15_20": post_spine_fps,
        "post_spine_interpretation": (
            "cycle 23 anchor_refcount table covers cycles 1-20. Beyond cycle 14 "
            "the only spine extension candidates are cycles {15-20} with "
            "anchor_refcount >= 2. Observation: " + (
                f"NONE — confirms post-cycle-14 chain entered fan-out phase "
                f"(P1/P2/P3 falsifiers all anchored to cycle 14 itself, not "
                f"to each other)."
                if not post_spine_fps else
                f"{post_spine_fps} are post-spine fixed points — spine "
                f"extends beyond cycle 14."
            )
        ),
    }

    return {
        "schema": "nexus.beyond_omega.cycle26_spine_geometry.v1",
        "generated_ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "entry_id": ENTRY_ID,
        "spine_cycles": SPINE_CYCLES,
        "n_spine": len(SPINE_CYCLES),
        "per_spine_metadata": per_spine,
        "spine_spacing": spacing,
        "next_spine_prediction": prediction,
        "next_spine_crosscheck": crosscheck,
        "post_spine_fixed_points_observed": post_spine_fps,
        "modality_progression": progression,
        "meta_finding": meta_finding,
        "anchor_refcount_full": anchor_refcount,
        "scope_note": (
            "Pure data analysis. No probe execution, no NEXUS_BACK_ACTION_ON. "
            "Inputs: state/proposals/inventory.json (entry nxs-20260425-004 "
            "cycle_*_finding_2026_04_25 blocks) + "
            "state/beyond_omega_cycle23_meta_chain_analysis.json."
        ),
    }


def main() -> int:
    out = build()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {OUT_PATH}")
    print(f"spine_cycles = {out['spine_cycles']}")
    print(f"spine gaps = {out['spine_spacing']['gaps']} mean={out['spine_spacing']['mean_gap']}")
    print(f"predicted next spine = {out['next_spine_prediction']['predicted_next_spine_cycle']}")
    print(f"crosscheck verdict = {out['next_spine_crosscheck']['verdict']}")
    print(f"post-spine fixed points (cycles 15-20) = {out['post_spine_fixed_points_observed']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
