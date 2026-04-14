#!/usr/bin/env python3
# @hexa-first-exempt — hexa stage1 runtime issues with json.load of multi-MB files + subprocess parsing
# DISC-P3-2 — growth_registry KPI 자동 업데이트
"""
growth_kpi_update.py — DISC-P3-2

5 deterministic KPIs:
  kpi.lens_count           len(shared/config/lens_registry.json['lenses'])
  kpi.edge_count           shared/discovery/cycle/edges.adjacency.meta.json['edge_count']
                           fallback: wc -l shared/discovery/cycle/edges.adjacency.json (estimate)
  kpi.breakthroughs_count  len(shared/discovery/breakthroughs.json['breakthroughs'])
  kpi.atlas_nodes          parse 'unique nodes:' from hexa run shared/n6/atlas_health.hexa
                           fallback: grep -c '^@X' shared/n6/atlas.n6
  kpi.consensus_rate       shared/discovery/lens_p2_3_multi_observer_2026-04-14.json['consensus_rate']
                           fallback: 0.0

CLI:
  --once   compute + atomic update shared/discovery/growth/growth-registry.json
  --dump   compute + print JSON (no write)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HOME = os.environ.get("HOME", "/Users/ghost")
NEXUS = os.environ.get("NEXUS", f"{HOME}/Dev/nexus")

LENS_REGISTRY = f"{NEXUS}/shared/config/lens_registry.json"
EDGES_META = f"{NEXUS}/shared/discovery/cycle/edges.adjacency.meta.json"
EDGES_JSON = f"{NEXUS}/shared/discovery/cycle/edges.adjacency.json"
BREAKTHROUGHS = f"{NEXUS}/shared/discovery/breakthroughs.json"
ATLAS_HEALTH = f"{NEXUS}/shared/n6/atlas_health.hexa"
ATLAS_N6 = f"{NEXUS}/shared/n6/atlas.n6"
HEXA_BIN = f"{NEXUS}/shared/bin/hexa"
LENS_P2_3 = f"{NEXUS}/shared/discovery/lens_p2_3_multi_observer_2026-04-14.json"
LENS_P3_1_GLOB = f"{NEXUS}/shared/discovery/lens_p3_1_*.json"  # future-proof

GROWTH_REGISTRY = f"{NEXUS}/shared/discovery/growth/growth-registry.json"


def _safe_load_json(path: str) -> dict | list | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def kpi_lens_count() -> int:
    d = _safe_load_json(LENS_REGISTRY)
    if isinstance(d, dict):
        lenses = d.get("lenses", [])
        if isinstance(lenses, list):
            return len(lenses)
    return 0


def kpi_edge_count() -> int:
    meta = _safe_load_json(EDGES_META)
    if isinstance(meta, dict):
        v = meta.get("edge_count")
        if isinstance(v, int):
            return v
    # fallback: wc -l edges.adjacency.json as rough estimate
    if os.path.exists(EDGES_JSON):
        try:
            r = subprocess.run(
                ["/usr/bin/wc", "-l", EDGES_JSON],
                capture_output=True, text=True, timeout=30,
            )
            return int(r.stdout.strip().split()[0])
        except Exception:
            return 0
    return 0


def kpi_breakthroughs_count() -> int:
    d = _safe_load_json(BREAKTHROUGHS)
    if isinstance(d, dict):
        bts = d.get("breakthroughs", [])
        if isinstance(bts, list):
            return len(bts)
    # jsonl fallback
    jsonl = BREAKTHROUGHS.replace(".json", ".jsonl")
    if os.path.exists(jsonl):
        try:
            with open(jsonl, "r") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0
    return 0


def kpi_atlas_nodes() -> int:
    # Primary: run hexa atlas_health.hexa
    if os.path.exists(HEXA_BIN) and os.path.exists(ATLAS_HEALTH):
        try:
            r = subprocess.run(
                [HEXA_BIN, "run", ATLAS_HEALTH],
                capture_output=True, text=True, timeout=60,
            )
            for line in r.stdout.splitlines():
                s = line.strip()
                if s.startswith("unique nodes:"):
                    # "unique nodes:  19236 (dup node IDs: 1274)"
                    tok = s.split(":", 1)[1].strip().split()
                    if tok and tok[0].isdigit():
                        return int(tok[0])
        except Exception:
            pass
    # Fallback: grep -c '^@X' atlas.n6
    if os.path.exists(ATLAS_N6):
        try:
            r = subprocess.run(
                ["/usr/bin/grep", "-c", "^@X", ATLAS_N6],
                capture_output=True, text=True, timeout=30,
            )
            s = r.stdout.strip()
            if s.isdigit():
                return int(s)
        except Exception:
            return 0
    return 0


def kpi_consensus_rate() -> float:
    # Prefer lens_p3_1_* if exists, else lens_p2_3
    import glob
    candidates = sorted(glob.glob(LENS_P3_1_GLOB), reverse=True)
    candidates.append(LENS_P2_3)
    for path in candidates:
        d = _safe_load_json(path)
        if isinstance(d, dict):
            # Direct key
            v = d.get("consensus_rate")
            if isinstance(v, (int, float)):
                return float(v)
            # Nested under summary
            summary = d.get("summary", {})
            if isinstance(summary, dict):
                v = summary.get("consensus_rate_mean") or summary.get("consensus_rate")
                if isinstance(v, (int, float)):
                    return float(v)
    return 0.0


def compute_kpis() -> dict:
    return {
        "lens_count": kpi_lens_count(),
        "edge_count": kpi_edge_count(),
        "breakthroughs_count": kpi_breakthroughs_count(),
        "atlas_nodes": kpi_atlas_nodes(),
        "consensus_rate": kpi_consensus_rate(),
    }


def _atomic_write_json(path: str, obj: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", delete=False, dir=os.path.dirname(path),
        prefix=".growth-registry.", suffix=".tmp",
    )
    try:
        json.dump(obj, tmp, indent=2, ensure_ascii=False)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp.close()
        os.replace(tmp.name, path)
    except Exception:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
        raise


def update_registry(path: str, kpis: dict) -> dict:
    """Merge kpis into growth-registry.json preserving prior project blocks."""
    existing = _safe_load_json(path) or {}
    if not isinstance(existing, dict):
        existing = {}

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    kpi_block = {
        "updated": now_iso,
        "source": "shared/harness/growth_kpi_update.py",
        "values": {
            "lens_count": kpis["lens_count"],
            "edge_count": kpis["edge_count"],
            "breakthroughs_count": kpis["breakthroughs_count"],
            "atlas_nodes": kpis["atlas_nodes"],
            "consensus_rate": kpis["consensus_rate"],
        },
    }

    # Preserve previous kpis history as short tail (last 20)
    history = existing.get("_kpi_history", [])
    if not isinstance(history, list):
        history = []
    history.append({
        "ts": now_iso,
        "values": kpi_block["values"],
    })
    history = history[-20:]

    existing["_kpis"] = kpi_block
    existing["_kpi_history"] = history
    existing["_updated"] = now_iso

    _atomic_write_json(path, existing)
    return {"ts": now_iso, "path": path, "kpis": kpi_block["values"], "history_len": len(history)}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Growth KPI updater (DISC-P3-2)")
    p.add_argument("--once", action="store_true", help="compute + atomic update growth-registry.json")
    p.add_argument("--dump", action="store_true", help="compute + print JSON (no write)")
    p.add_argument("--registry", default=GROWTH_REGISTRY)
    ns = p.parse_args(argv[1:])

    if not (ns.once or ns.dump):
        p.print_help()
        return 2

    kpis = compute_kpis()
    out = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kpis": kpis,
    }

    if ns.dump:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    if ns.once:
        log_entry = update_registry(ns.registry, kpis)
        out["update"] = log_entry
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
