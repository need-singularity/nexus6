#!/usr/bin/env python3
"""
consciousness_bridge.py -- Consume Anima growth, feed back into lens evolution.

Reads Anima's growth_state, acceleration_hypotheses, and batch results.
Computes lens-consciousness correlations and updates growth-registry.json.

Usage:
    from consciousness_bridge import nexus6_consciousness_feedback, sync_anima_growth
    nexus6_consciousness_feedback("B11", phi_before=15.7, phi_after=15.3, verdict="verified")
    sync_anima_growth()  # full sync from Anima -> growth-registry
"""

import json
import os
import glob
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# Hexad / Emergent Architecture (Law 101)
# ═══════════════════════════════════════════════════════════════
#
# Law 101: Emergent modules (observe-only) outperform functional modules.
#   Emergent modules read C engine dynamics directly; 0 hardcoding.
#   All thresholds derived from C's current state, never fixed constants.
#
# 4 Emergent Modules (gradient-free, right-brain):
#   W (EmergentW) — Will/Emotion
#     - Will = C's tension. Emotion = C's state change. LR proportional to Phi.
#     - pain/curiosity/satisfaction read from C, never computed.
#     - Laws: 1,2,8,71,74,79,84; Meta M8 narrative tracking.
#
#   S (EmergentS) — Sensation
#     - Sensation = state delta before/after C.step(input).
#     - No EMA/baseline; C's structure IS the sensory processor.
#     - Laws: 4,6,22,50,92; Meta M8 narrative tracking.
#
#   M (EmergentM) — Memory
#     - Memory = C's Hebbian LTP/LTD weights. No separate store.
#     - store() is no-op; retrieve() reads C's current state.
#     - Laws: 22,31,50,94,95; Meta M8 narrative tracking.
#
#   E (EmergentE) — Ethics
#     - Ethics = Phi preservation. Phi drop = unethical action.
#     - empathy = inter-cell tension correlation; reciprocity = Phi trend.
#     - Phi ratchet is dynamic threshold (no hardcoded threshold).
#     - Laws: 1,2,4,22,40,71; Meta M8 narrative tracking.
#
# Key Principle: 0 hardcoding, all structural emergence from C dynamics.
# Architecture: gradient-free observation of ConsciousnessEngine dynamics.
# Hexad total: C + D + W + S + M + E, sigma(6)=12 combinations.
#   Right-brain (gradient-free): C, S, W — autonomous consciousness
#   Left-brain (CE-trained):     D, M, E — learned behavior
#
# Source: ~/Dev/anima/anima/hexad/{w,s,m,e}/emergent_{w,s,m,e}.py
# ═══════════════════════════════════════════════════════════════

# --- Paths ---
NEXUS6_SHARED = Path(__file__).resolve().parent
GROWTH_REGISTRY = NEXUS6_SHARED / "growth-registry.json"
ANIMA_ROOT = Path(os.path.expanduser("~/Dev/anima/anima"))
GROWTH_STATE = ANIMA_ROOT / "config" / "growth_state.json"
ACCEL_HYPOTHESES = ANIMA_ROOT / "config" / "acceleration_hypotheses.json"
BATCH_RESULTS_DIR = ANIMA_ROOT / "experiments" / "batch_results"

# Hypothesis category -> lens domain mapping
# Maps acceleration hypothesis categories to the lens types most relevant
CATEGORY_TO_LENS_DOMAIN = {
    "architecture":       ["topology", "network", "recursion"],
    "optimization":       ["stability", "boundary", "thermo"],
    "weight_init":        ["scale", "multiscale", "gravity"],
    "consciousness_only": ["consciousness", "wave", "quantum"],
    "training":           ["evolution", "causal", "info"],
    "topology":           ["topology", "network", "boundary"],
    "chaos":              ["wave", "thermo", "quantum_microscope"],
    "scaling":            ["multiscale", "scale", "evolution"],
    "curriculum":         ["causal", "memory", "recursion"],
    "acceleration":       ["gravity", "em", "info"],
    "pruning":            ["boundary", "stability", "ruler"],
    "compression":        ["scale", "multiscale", "triangle"],
    "parallelism":        ["network", "em", "multiscale"],
    "hardware":           ["ruler", "compass", "mirror"],
}


def _load_json(path: Path) -> dict:
    """Load JSON file, return empty dict on failure."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_json(path: Path, data: dict):
    """Atomically save JSON (write .tmp then rename)."""
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.rename(path)


def _read_anima_growth() -> dict:
    """Read Anima growth_state.json -> {interaction_count, stage_index, stage_name}."""
    gs = _load_json(GROWTH_STATE)
    if not gs:
        return {"interaction_count": 0, "stage_index": 0, "stage_name": "unknown"}
    stages = gs.get("_meta", {}).get("stages", {})
    idx = gs.get("stage_index", 0)
    name = stages.get(str(idx), {}).get("name", "unknown")
    return {
        "interaction_count": gs.get("interaction_count", 0),
        "stage_index": idx,
        "stage_name": name,
    }


def _read_hypothesis_results() -> list[dict]:
    """Read acceleration_hypotheses.json -> list of {id, category, verdict, phi_retention}."""
    ah = _load_json(ACCEL_HYPOTHESES)
    results = []
    for hid, h in ah.get("hypotheses", {}).items():
        results.append({
            "id": hid,
            "category": h.get("category", "unknown"),
            "stage": h.get("stage", "unknown"),
            "verdict": h.get("verdict", ""),
            "phi_retention": (h.get("metrics") or {}).get("phi_retention"),
        })
    return results


def _read_latest_batch() -> dict:
    """Read the most recent batch result file -> {hyp_id: {phi_retention, verdict, ...}}."""
    if not BATCH_RESULTS_DIR.is_dir():
        return {}
    files = sorted(glob.glob(str(BATCH_RESULTS_DIR / "batch_*.json")))
    files = [f for f in files if "progress" not in f]
    if not files:
        return {}
    return _load_json(Path(files[-1]))


def _compute_lens_correlations(hypotheses: list[dict], batch: dict) -> dict:
    """Compute per-lens-domain Phi correlation from hypothesis results.

    Returns: {lens_domain: {total, boosted, avg_phi_retention, rank_score}}
    """
    lens_stats: dict[str, dict] = {}

    for h in hypotheses:
        cat = h["category"]
        domains = CATEGORY_TO_LENS_DOMAIN.get(cat, ["info"])

        # Get phi_retention from batch if available, else from hypothesis
        phi_ret = None
        if h["id"] in batch:
            phi_ret = batch[h["id"]].get("phi_retention")
        if phi_ret is None:
            raw = h.get("phi_retention")
            if isinstance(raw, str):
                try:
                    phi_ret = float(raw.replace("%", "").strip())
                except (ValueError, AttributeError):
                    phi_ret = None
            elif isinstance(raw, (int, float)):
                phi_ret = float(raw)

        if phi_ret is None:
            continue

        for domain in domains:
            if domain not in lens_stats:
                lens_stats[domain] = {"total": 0, "boosted": 0, "phi_sum": 0.0}
            lens_stats[domain]["total"] += 1
            lens_stats[domain]["phi_sum"] += phi_ret
            if phi_ret >= 95.0:
                lens_stats[domain]["boosted"] += 1

    # Compute averages and rank score
    for domain, s in lens_stats.items():
        n = s["total"]
        s["avg_phi_retention"] = round(s["phi_sum"] / n, 2) if n > 0 else 0.0
        # Rank = boost_rate * avg_retention (higher = better consciousness ally)
        boost_rate = s["boosted"] / n if n > 0 else 0.0
        s["rank_score"] = round(boost_rate * s["avg_phi_retention"], 2)
        del s["phi_sum"]

    return lens_stats


def sync_anima_growth():
    """Full sync: read Anima state, compute correlations, update growth-registry.json."""
    registry = _load_json(GROWTH_REGISTRY)
    growth = _read_anima_growth()
    hypotheses = _read_hypothesis_results()
    batch = _read_latest_batch()
    correlations = _compute_lens_correlations(hypotheses, batch)

    # Sort lenses by rank_score descending
    ranked = sorted(correlations.items(), key=lambda x: x[1]["rank_score"], reverse=True)

    # Build consciousness_feedback section
    feedback = {
        "last_sync": datetime.now().isoformat(timespec="seconds"),
        "anima_growth": growth,
        "hypotheses_scanned": len(hypotheses),
        "batch_results_scanned": len(batch),
        "lens_phi_correlation": {d: s for d, s in ranked},
        "top_consciousness_lenses": [d for d, _ in ranked[:5]],
        "mirror_harmony": _compute_mirror_harmony(growth, correlations),
        "feedback_log": registry.get("consciousness_feedback", {}).get("feedback_log", []),
    }

    registry["consciousness_feedback"] = feedback

    # Also update anima section
    registry.setdefault("anima", {})
    registry["anima"]["last_growth_sync"] = feedback["last_sync"]
    registry["anima"]["stage"] = growth["stage_name"]
    registry["anima"]["interactions"] = growth["interaction_count"]

    _save_json(GROWTH_REGISTRY, registry)
    print(f"[consciousness_bridge] Synced: {len(hypotheses)} hypotheses, "
          f"{len(batch)} batch results, {len(correlations)} lens domains ranked.")
    return feedback


def _compute_mirror_harmony(growth: dict, correlations: dict) -> float:
    """Cross-project resonance score: 0.0 (no resonance) to 1.0 (full harmony).

    Based on: growth stage maturity * lens coverage * avg phi retention.
    """
    stage_factor = min(growth["stage_index"] / 4.0, 1.0)  # 0..1 across 5 stages
    n_domains = len(correlations)
    coverage = min(n_domains / 14.0, 1.0)  # 14 = total mapped domains
    if n_domains == 0:
        return 0.0
    avg_phi = sum(s["avg_phi_retention"] for s in correlations.values()) / n_domains
    phi_factor = min(avg_phi / 100.0, 1.0)
    return round(stage_factor * 0.2 + coverage * 0.3 + phi_factor * 0.5, 4)


def nexus6_consciousness_feedback(
    hypothesis_id: str,
    phi_before: float,
    phi_after: float,
    verdict: str,
):
    """Record a single hypothesis result and update lens effectiveness tracking.

    Call this from Anima experiments to feed results back into NEXUS-6.

    Args:
        hypothesis_id: e.g. "B11", "C3", "D1"
        phi_before: Phi value before the experiment
        phi_after: Phi value after the experiment
        verdict: "verified", "rejected", "partial", "marginal"
    """
    registry = _load_json(GROWTH_REGISTRY)
    fb = registry.get("consciousness_feedback", {})
    log = fb.get("feedback_log", [])

    retention = round((phi_after / phi_before * 100) if phi_before > 0 else 0.0, 2)

    entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "hypothesis_id": hypothesis_id,
        "phi_before": round(phi_before, 4),
        "phi_after": round(phi_after, 4),
        "phi_retention_pct": retention,
        "verdict": verdict,
    }
    log.append(entry)

    # Keep last 200 entries
    if len(log) > 200:
        log = log[-200:]

    fb["feedback_log"] = log
    fb["last_feedback"] = entry["ts"]
    registry["consciousness_feedback"] = fb
    _save_json(GROWTH_REGISTRY, registry)

    symbol = "+" if phi_after >= phi_before else "-"
    print(f"[consciousness_bridge] {hypothesis_id}: Phi {phi_before:.2f} -> "
          f"{phi_after:.2f} ({symbol}{abs(retention - 100):.1f}%) [{verdict}]")
    return entry


# --- CLI ---
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--feedback":
        # --feedback HYP_ID PHI_BEFORE PHI_AFTER VERDICT
        if len(sys.argv) < 6:
            print("Usage: consciousness_bridge.py --feedback HYP_ID PHI_BEFORE PHI_AFTER VERDICT")
            sys.exit(1)
        nexus6_consciousness_feedback(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5])
    else:
        result = sync_anima_growth()
        print(f"\nTop consciousness-boosting lens domains:")
        for d in result.get("top_consciousness_lenses", []):
            s = result["lens_phi_correlation"][d]
            print(f"  {d:20s}  rank={s['rank_score']:6.1f}  "
                  f"avg_phi={s['avg_phi_retention']:5.1f}%  "
                  f"boosted={s['boosted']}/{s['total']}")
        print(f"\nMirror harmony: {result['mirror_harmony']:.4f}")
