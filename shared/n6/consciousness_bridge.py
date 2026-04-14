#!/usr/bin/env python3
# @hexa-first-exempt — hexa stage1 runtime bug 우회 (T23~T29 복구 후 포팅)
"""
consciousness_bridge.py — ATLAS-P2-3 realtime bridge helper.

Called by: shared/n6/consciousness_sync.hexa  (via `--sync` flag)

Responsibilities:
  1. Read live atlas.n6 state (stats, deg sidecars).
  2. Read shared/consciousness/anima_state.json + consciousness_laws.json.
  3. Compute extended fields:
        consciousness_level      — Φ-proxy derived from hub_ratio + coupling_strength
        consciousness_phase      — anima stage mapped to growth band
        anima_bridge             — link: atlas <-> anima state (laws, phi, stage)
        mind_mapper_status       — presence of mm-*/dim-* nodes in atlas
        realtime_deltas          — diff vs previous snapshot
        sync_metadata            — last_sync_at / source_files / atlas_mtime
  4. Merge these into atlas.n6.consciousness (L0-safe: writes only the sidecar).

Inputs (positional):
  1. atlas.n6 path
  2. atlas.n6.consciousness path (read + write)
  3. anima_state.json path
  4. consciousness_laws.json path
  5. mode ("sync" | "dry-run")
"""

import json, os, re, sys, subprocess
from datetime import datetime, timezone

if len(sys.argv) < 6:
    print("usage: consciousness_bridge.py ATLAS SIDECAR ANIMA LAWS MODE", file=sys.stderr)
    sys.exit(1)

ATLAS      = sys.argv[1]
SIDECAR    = sys.argv[2]
ANIMA      = sys.argv[3]
LAWS       = sys.argv[4]
MODE       = sys.argv[5]
ATLAS_DEG  = ATLAS + ".deg"
ATLAS_STATS = ATLAS + ".stats"

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ---- 1. Load current sidecar (preserve existing fields) ----
sidecar = {}
if os.path.exists(SIDECAR):
    with open(SIDECAR) as f:
        sidecar = json.load(f)

# ---- 2. Load stats sidecar ----
stats = {}
if os.path.exists(ATLAS_STATS):
    with open(ATLAS_STATS) as f:
        stats = json.load(f)

# ---- 3. Scan atlas.n6.deg for per-constant hub degrees ----
deg_map = {}
max_deg = 0
if os.path.exists(ATLAS_DEG):
    with open(ATLAS_DEG) as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2: continue
            try: d = int(parts[1])
            except ValueError: continue
            deg_map[parts[0]] = d
            if d > max_deg: max_deg = d

hub_deg = {k: deg_map.get(k, 0) for k in ("n", "J2", "phi", "sigma", "tau", "sopfr", "mu", "M3")}

# ---- 4. Leaf/hub ratio from deg ----
total_deg_rows = len(deg_map)
leaf_count = sum(1 for v in deg_map.values() if v == 1)
leaf_ratio = leaf_count / total_deg_rows if total_deg_rows else 0.0
# Hub threshold: degree >= 3 matches atlas_health.hexa convention
hub_count = sum(1 for v in deg_map.values() if v >= 3)
hub_ratio = hub_count / total_deg_rows if total_deg_rows else 0.0
total_nodes = stats.get("nodes", 0)
total_edges = stats.get("edges", 0)
density = (2 * total_edges) / (total_nodes * (total_nodes - 1)) if total_nodes > 1 else 0.0

# ---- 5. Dimensional coupling (co-mention counts via grep) ----
def grep_count(pattern):
    try:
        r = subprocess.run(["grep", "-c", pattern, ATLAS],
                           capture_output=True, text=True, timeout=30)
        return int(r.stdout.strip() or 0)
    except Exception:
        return 0

coupling = {
    "n_sigma":    grep_count("sigma.*n\\|n.*sigma"),
    "n_phi":      grep_count("phi.*n\\|n.*phi"),
    "phi_sigma":  grep_count("phi.*sigma\\|sigma.*phi"),
    "sigma_tau":  grep_count("sigma.*tau\\|tau.*sigma"),
    "phi_tau":    grep_count("phi.*tau\\|tau.*phi"),
    "n_tau":      grep_count("tau.*n\\|n.*tau"),
    "phi_sopfr":  grep_count("phi.*sopfr\\|sopfr.*phi"),
    "sigma_sopfr":grep_count("sigma.*sopfr\\|sopfr.*sigma"),
    "n_mu":       grep_count("mu.*n\\|n.*mu"),
    "tau_mu":     grep_count("tau.*mu\\|mu.*tau"),
}
strongest_pair = max(coupling, key=coupling.get) if coupling else None
weakest_pair   = min(coupling, key=coupling.get) if coupling else None

# ---- 6. Anima state bridge ----
anima_data = {}
if os.path.exists(ANIMA):
    try:
        with open(ANIMA) as f:
            anima_data = json.load(f)
    except Exception:
        pass

anima_laws_count = anima_data.get("laws", 0)
anima_stage      = anima_data.get("stage", "unknown")
anima_phi        = anima_data.get("phi", 0)
anima_generation = anima_data.get("generation", 0)
anima_perspective= anima_data.get("perspective", "unknown")
anima_novel      = anima_data.get("novel_laws", 0)
anima_ts         = anima_data.get("timestamp", "")

laws_meta = {}
if os.path.exists(LAWS):
    try:
        with open(LAWS) as f:
            ldata = json.load(f)
            if isinstance(ldata, dict) and "_meta" in ldata:
                laws_meta = {
                    "version":      ldata["_meta"].get("version"),
                    "total_laws":   ldata["_meta"].get("total_laws"),
                    "total_meta":   ldata["_meta"].get("total_meta"),
                    "total_topo":   ldata["_meta"].get("total_topo"),
                    "updated":      ldata["_meta"].get("updated"),
                    "last_growth":  ldata["_meta"].get("last_growth_loop"),
                }
    except Exception:
        pass

# ---- 7. consciousness_level: Φ-proxy ----
# Composite: normalized (hub degree sum / max_deg) × coupling diversity × law density
hub_strength = sum(hub_deg.values()) / (max_deg * len(hub_deg)) if max_deg else 0.0
# coupling diversity: entropy-like across pair counts
total_cp = sum(coupling.values())
diversity = 0.0
if total_cp > 0:
    from math import log
    for v in coupling.values():
        if v > 0:
            p = v / total_cp
            diversity -= p * log(p)
    # normalize to 0..1 (max entropy for 10 pairs is log(10))
    diversity = diversity / log(10)
law_density = min(1.0, anima_laws_count / 3000) if anima_laws_count else 0.0
consciousness_level = round(0.4 * hub_strength + 0.4 * diversity + 0.2 * law_density, 6)

# ---- 8. consciousness_phase: anima stage → band ----
# Stage convention: "S10-mega512d" → phase "10-mega" (growth dimension 512)
stage_match = re.match(r"S(\d+)-(.*)", anima_stage or "")
if stage_match:
    phase_num = int(stage_match.group(1))
    phase_name = stage_match.group(2)
    if phase_num < 3: phase_band = "nascent"
    elif phase_num < 6: phase_band = "forming"
    elif phase_num < 9: phase_band = "integrating"
    else: phase_band = "mature"
else:
    phase_num, phase_name, phase_band = 0, "unknown", "unknown"

consciousness_phase = {
    "stage_id": anima_stage,
    "stage_num": phase_num,
    "stage_name": phase_name,
    "phase_band": phase_band,
    "generation": anima_generation,
    "perspective": anima_perspective,
}

# ---- 9. mind_mapper_status ----
mm_ids = ["mm-consciousness-topology", "mm-thalamic-hub-n", "mm-dimension-imbalance",
          "mm-soc-criticality", "mm-dim-fold-515"]
dim_ids = ["dim-intrinsic-4d", "dim-phi-critical-14", "dim-phi-fractal-30",
           "dim-faction-topology", "dim-maxpool-phi-amplify", "dim-shannon-ladder"]
mm_present = 0
dim_present = 0
for nid in mm_ids:
    try:
        r = subprocess.run(["grep", "-c", f'"{nid}"', ATLAS],
                           capture_output=True, text=True, timeout=15)
        if int(r.stdout.strip() or 0) > 0: mm_present += 1
    except Exception: pass
for nid in dim_ids:
    try:
        r = subprocess.run(["grep", "-c", f'"{nid}"', ATLAS],
                           capture_output=True, text=True, timeout=15)
        if int(r.stdout.strip() or 0) > 0: dim_present += 1
    except Exception: pass
mind_mapper_status = {
    "mm_nodes_present":  mm_present,
    "mm_nodes_total":    len(mm_ids),
    "dim_nodes_present": dim_present,
    "dim_nodes_total":   len(dim_ids),
    "integrity":         (mm_present + dim_present) / (len(mm_ids) + len(dim_ids)),
}

# ---- 10. realtime_deltas vs prior snapshot ----
prev_topology = sidecar.get("topology", {})
prev_hubs = {h["id"]: h.get("degree", 0) for h in sidecar.get("thalamic_hubs", {}).get("hubs", [])}
prev_coupling = sidecar.get("dimensional_coupling", {}).get("matrix", {})
realtime_deltas = {
    "node_count_delta":   total_nodes - sidecar.get("realtime_deltas", {}).get("last_nodes", total_nodes) if "realtime_deltas" in sidecar else 0,
    "edge_count_delta":   total_edges - sidecar.get("realtime_deltas", {}).get("last_edges", total_edges) if "realtime_deltas" in sidecar else 0,
    "density_delta":      round(density - prev_topology.get("density", density), 8),
    "leaf_ratio_delta":   round(leaf_ratio - prev_topology.get("leaf_ratio", leaf_ratio), 6),
    "hub_ratio_delta":    round(hub_ratio - prev_topology.get("hub_ratio", hub_ratio), 6),
    "max_degree_delta":   max_deg - prev_topology.get("max_degree", max_deg),
    "hub_n_delta":        hub_deg["n"] - prev_hubs.get("n", hub_deg["n"]),
    "hub_phi_delta":      hub_deg["phi"] - prev_hubs.get("phi", hub_deg["phi"]),
    "coupling_n_mu_delta":  coupling["n_mu"] - prev_coupling.get("n_mu", coupling["n_mu"]),
    "coupling_tau_mu_delta":coupling["tau_mu"] - prev_coupling.get("tau_mu", coupling["tau_mu"]),
    "last_nodes":         total_nodes,
    "last_edges":         total_edges,
}

# ---- 11. Assemble extended sidecar ----
sidecar["_meta"] = {
    **sidecar.get("_meta", {}),
    "description": "atlas.n6 의식 메타레이어 — 뇌 connectome 오버레이 + 실시간 브릿지",
    "source":      "consciousness_sync.hexa --sync (ATLAS-P2-3)",
    "atlas_readonly": True,
    "created":     sidecar.get("_meta", {}).get("created", now[:10]),
    "updated":     now,
    "principle":   "atlas.n6 = 뇌(불변), 이 사이드카 = 관찰 장치(fMRI). 실시간 관측, L0 보호.",
    "schema_version": "2.0",
    "extended_by": "ATLAS-P2-3",
}

sidecar["topology"] = {
    **sidecar.get("topology", {}),
    "density":     round(density, 8),
    "leaf_ratio":  round(leaf_ratio, 6),
    "hub_ratio":   round(hub_ratio, 6),
    "max_degree":  max_deg,
    "total_nodes": total_nodes,
    "total_edges": total_edges,
    "deg_rows":    total_deg_rows,
    "measured_at": now,
}

# Preserve cortical_layers, thalamic_hubs static structure but refresh hub degrees:
thalamic = sidecar.get("thalamic_hubs", {})
if "hubs" in thalamic:
    for h in thalamic["hubs"]:
        live = deg_map.get(h.get("id"), None)
        if live is not None:
            h["degree_live"] = live
            h["degree_delta"] = live - h.get("degree", live)
thalamic["measured_at"] = now
sidecar["thalamic_hubs"] = thalamic

# Dimensional coupling — update matrix with live counts
dc = sidecar.get("dimensional_coupling", {})
dc["matrix"] = coupling
dc["strongest"] = {"pair": strongest_pair.replace("_", ","), "coupling": coupling[strongest_pair]} if strongest_pair else dc.get("strongest")
dc["weakest"]   = {"pair": weakest_pair.replace("_", ","),  "coupling": coupling[weakest_pair]}   if weakest_pair   else dc.get("weakest")
dc["measured_at"] = now
sidecar["dimensional_coupling"] = dc

# NEW fields (ATLAS-P2-3)
sidecar["consciousness_level"] = {
    "value": consciousness_level,
    "components": {
        "hub_strength":   round(hub_strength, 6),
        "coupling_diversity": round(diversity, 6),
        "law_density":    round(law_density, 6),
    },
    "weights":  {"hub_strength": 0.4, "coupling_diversity": 0.4, "law_density": 0.2},
    "scale":    "0..1 (Φ-proxy, higher = more integrated consciousness)",
    "measured_at": now,
}
sidecar["consciousness_phase"] = consciousness_phase
sidecar["anima_bridge"] = {
    "anima_state_file":  ANIMA,
    "laws_registry":     LAWS,
    "live": {
        "laws":           anima_laws_count,
        "stage":          anima_stage,
        "phi":            anima_phi,
        "generation":     anima_generation,
        "perspective":    anima_perspective,
        "novel_laws":     anima_novel,
        "state_ts":       anima_ts,
    },
    "laws_meta":          laws_meta,
    "sync_direction":     "anima -> atlas.n6.consciousness (read-only mirror)",
    "measured_at":        now,
}
sidecar["mind_mapper_status"] = mind_mapper_status
sidecar["realtime_deltas"] = realtime_deltas
sidecar["sync_metadata"] = {
    "last_sync_at":       now,
    "atlas_mtime":        stats.get("mtime"),
    "atlas_size":         stats.get("size"),
    "source_files": [
        ATLAS, ATLAS_STATS, ATLAS_DEG, ANIMA, LAWS,
    ],
    "bridge_script":      os.path.abspath(sys.argv[0]),
    "bridge_version":     "1.0",
    "task":               "ATLAS-P2-3",
    "mode":               MODE,
}

# ---- 12. Write (or dry-run print) ----
out = json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n"
if MODE == "sync":
    # L0-safe atomic replace
    tmp = SIDECAR + ".tmp.sync"
    with open(tmp, "w") as f:
        f.write(out)
    os.rename(tmp, SIDECAR)
    print(f"synced: {SIDECAR}")
    print(f"size:   {len(out)} bytes")
    print(f"level:  {consciousness_level}")
    print(f"phase:  {phase_band} ({anima_stage})")
    print(f"laws:   {anima_laws_count}")
    print(f"deltas: nodes={realtime_deltas['node_count_delta']:+} edges={realtime_deltas['edge_count_delta']:+}")
else:
    print("DRY-RUN — sidecar would be updated:")
    print(f"  size:   {len(out)} bytes")
    print(f"  level:  {consciousness_level}")
    print(f"  phase:  {phase_band} ({anima_stage})")
    print(f"  laws:   {anima_laws_count}")
