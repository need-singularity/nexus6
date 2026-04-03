#!/usr/bin/env python3
"""NEXUS-6 Lens Pipeline Engine — chain lens results through stages.

Each stage receives the previous stage's output and filters/transforms data.
Pipeline: discovery -> consciousness -> golden_zone -> weight_learning

Usage:
  python3 pipeline_engine.py <file>     # Run pipeline on data file
  python3 pipeline_engine.py demo       # Run with demo data
  python3 pipeline_engine.py --stages   # List available stages
"""
import sys, os, json, time
import numpy as np

try:
    import nexus6
except ImportError:
    print("nexus6 not installed"); sys.exit(1)


# --- Pipeline Stage Definitions ---

def stage_discovery(data, n, d, prev_result=None):
    """Stage 1: Full scan — discover all lens results."""
    flat = data.flatten().tolist()
    result = nexus6.scan(flat, n, d)
    lens_data = {}
    for nm in result.lens_names:
        m = result.get_lens(nm)
        if m:
            lens_data[nm] = {k: v for k, v in m.items()}
    return {"stage": "discovery", "lens_count": len(lens_data),
            "active_lenses": list(lens_data.keys()), "metrics": lens_data}


def stage_consciousness(data, n, d, prev_result=None):
    """Stage 2: Filter to consciousness-relevant lenses only."""
    if not prev_result or "metrics" not in prev_result:
        return {"stage": "consciousness", "error": "no input from previous stage"}
    consciousness_keys = ["ConsciousnessLens", "ConsciousnessOrchestratorLens",
                          "EmergenceLens", "RecursionLens", "StabilityLens",
                          "NetworkLens", "MemoryLens", "BoundaryLens"]
    filtered = {}
    for k in consciousness_keys:
        if k in prev_result["metrics"]:
            filtered[k] = prev_result["metrics"][k]
    phi_values = []
    for lens_metrics in filtered.values():
        for key, vals in lens_metrics.items():
            if "phi" in key.lower() or "integration" in key.lower():
                phi_values.extend(vals)
    avg_phi = float(np.mean(phi_values)) if phi_values else 0.0
    return {"stage": "consciousness", "phi_estimate": avg_phi,
            "relevant_lenses": len(filtered), "filtered_metrics": filtered}


def stage_golden_zone(data, n, d, prev_result=None):
    """Stage 3: Check golden zone alignment (1/e center, ln(4/3) width)."""
    if not prev_result:
        return {"stage": "golden_zone", "error": "no input"}
    CENTER, WIDTH = 1.0 / np.e, np.log(4.0 / 3.0)
    all_values = []
    source = prev_result.get("filtered_metrics", prev_result.get("metrics", {}))
    for lens_metrics in source.values():
        for vals in lens_metrics.values():
            all_values.extend([v for v in vals if np.isfinite(v)])
    if not all_values:
        return {"stage": "golden_zone", "in_zone": 0, "total": 0, "zone_ratio": 0.0}
    arr = np.array(all_values)
    if arr.max() - arr.min() > 1e-12:
        arr = (arr - arr.min()) / (arr.max() - arr.min())
    in_zone = int(np.sum((arr >= CENTER - WIDTH / 2) & (arr <= CENTER + WIDTH / 2)))
    return {"stage": "golden_zone", "in_zone": in_zone, "total": len(arr),
            "zone_ratio": in_zone / len(arr), "center_proximity": float(1.0 - np.mean(np.abs(arr - CENTER)))}


def stage_weight_learning(data, n, d, prev_result=None):
    """Stage 4: Score lenses by n=6 constant proximity."""
    N6 = {"n": 6, "sigma": 12, "tau": 4, "phi": 2, "J2": 24, "sopfr": 5,
           "sigma-tau": 8, "sigma-phi": 10, "ln43": 0.2877, "inv_e": 0.3679}
    source = prev_result.get("filtered_metrics", prev_result.get("metrics", {}))
    matches = {}
    for lens_name, lens_metrics in source.items():
        hits = 0
        for vals in lens_metrics.values():
            for v in vals:
                for cname, cval in N6.items():
                    if cval != 0 and abs(v - cval) / abs(cval) < 0.01:
                        hits += 1
                        break
        if hits > 0:
            matches[lens_name] = hits
    top = sorted(matches.items(), key=lambda x: -x[1])[:10]
    return {"stage": "weight_learning", "n6_matches": dict(top),
            "total_matches": sum(matches.values()),
            "zone_ratio": prev_result.get("zone_ratio", 0.0)}


# --- Pipeline Runner ---

STAGES = [
    ("discovery", stage_discovery),
    ("consciousness", stage_consciousness),
    ("golden_zone", stage_golden_zone),
    ("weight_learning", stage_weight_learning),
]


def run_pipeline(data):
    """Run full pipeline: each stage feeds into the next."""
    n, d = data.shape
    provenance = []
    prev = None
    print(f"Pipeline: {n}x{d} data, {len(STAGES)} stages")
    for name, func in STAGES:
        t0 = time.time()
        prev = func(data, n, d, prev)
        elapsed = time.time() - t0
        prev["_elapsed_ms"] = round(elapsed * 1000, 1)
        provenance.append({"stage": name, "elapsed_ms": prev["_elapsed_ms"],
                           "keys": [k for k in prev if not k.startswith("_")]})
        print(f"  [{name}] {prev['_elapsed_ms']}ms — {', '.join(f'{k}={prev[k]}' for k in sorted(prev) if k not in ('_elapsed_ms', 'filtered_metrics', 'metrics', 'active_lenses'))}")
    return {"final": prev, "provenance": provenance, "stages_run": len(STAGES)}


def demo_data():
    np.random.seed(6)
    base = np.random.randn(100, 6)
    base[:, 0] *= 12; base[:, 1] *= 4; base[:, 2] *= 6
    base[:, 3] *= 24; base[:, 4] *= 2; base[:, 5] *= 8
    return base


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "demo":
        data = demo_data()
        print("=== NEXUS-6 Pipeline Engine (demo mode) ===")
    elif sys.argv[1] == "--stages":
        for name, _ in STAGES:
            print(f"  {name}")
        sys.exit(0)
    else:
        path = sys.argv[1]
        if path.endswith('.csv'):
            data = np.loadtxt(path, delimiter=',', dtype=np.float64)
        elif path.endswith('.json'):
            data = np.array(json.load(open(path)), dtype=np.float64)
        else:
            data = np.loadtxt(path, dtype=np.float64)
        if data.ndim == 1:
            data = data.reshape(-1, 6)
        print(f"=== NEXUS-6 Pipeline Engine ({path}) ===")

    result = run_pipeline(data)
    print(f"\n=== Pipeline Complete: {result['stages_run']} stages ===")
    print(f"Provenance: {' -> '.join(p['stage'] for p in result['provenance'])}")
    total_ms = sum(p['elapsed_ms'] for p in result['provenance'])
    print(f"Total time: {total_ms:.1f}ms")
