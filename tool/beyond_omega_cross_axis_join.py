#!/usr/bin/env python3
"""
beyond_omega_cross_axis_join.py — nxs-20260425-004 cycle 6

Cycle 3 finding 의 cross-axis isomorphism (axis B ↔ nxs-20260425-002 timeout) 와
cycle 4 finding 의 cross-axis dashboard auto-emit (cmd_omega 진입 시 V3' snapshot)
을 정량화. 세 sources 를 hour-bucket 위에 join:

  1. axis B  — state/ghost_ceiling_trace.jsonl (cycle 5 v4 가 만드는 probe 출력)
  2. axis A  — state/drill_stage_elapsed_history.jsonl (nxs-002 cycle 7 backfill)
  3. axis A snapshot — bisociation/spectra/g_atlas_composite_v3.json (V3' SSOT)

출력:
  - state/beyond_omega_cross_axis_join.json
    {
      "schema": "nexus.beyond_omega.cross_axis_join.v1",
      "hour_buckets": [{"hour_utc": "...", "emits": N, "approaches": N, "stages": N,
                         "smash_elapsed_p50_ms": N, "stage_set": [...]}, ...],
      "isomorphism": {"emit_to_stage_pearson": ...,
                       "approach_at_v3_snapshot": bool, ...},
      "v3_snapshot": {"composite_v3_prime": 0.964689, "ts": 1777109226}
    }
"""
from __future__ import annotations

import json
import re
import statistics
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TRACE = REPO / "state" / "ghost_ceiling_trace.jsonl"
HISTORY = REPO / "state" / "drill_stage_elapsed_history.jsonl"
V3_SNAPSHOT = REPO / "bisociation" / "spectra" / "g_atlas_composite_v3.json"
OUT = REPO / "state" / "beyond_omega_cross_axis_join.json"

# axis B emit 자체는 ts 가 없음. emit 이 발견된 file 안에서 가장 가까운
# NEXUS_DRILL_PROGRESS {"ts":...} 또는 비슷한 ts marker 를 찾아 추정.
# 또는 file mtime 으로 fallback.
TS_RE = re.compile(r'"ts"\s*:\s*(\d{10})')


def _file_estimated_ts(file_path: str) -> int | None:
    p = Path(file_path)
    if not p.exists():
        return None
    try:
        with open(p, "r", errors="replace") as fh:
            for line in fh:
                m = TS_RE.search(line)
                if m:
                    return int(m.group(1))
    except OSError:
        pass
    try:
        return int(p.stat().st_mtime)
    except OSError:
        return None


def _hour_bucket(ts: int) -> str:
    return time.strftime("%Y-%m-%dT%H:00Z", time.gmtime(ts))


def load_axis_b():
    rows = []
    if not TRACE.exists():
        return rows
    with open(TRACE, "r") as fh:
        for line in fh:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = _file_estimated_ts(obj.get("file", ""))
            obj["_estimated_ts"] = ts
            obj["_hour_bucket"] = _hour_bucket(ts) if ts else None
            rows.append(obj)
    return rows


def load_axis_a():
    rows = []
    if not HISTORY.exists():
        return rows
    with open(HISTORY, "r") as fh:
        for line in fh:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = obj.get("ts")
            if ts:
                obj["_hour_bucket"] = _hour_bucket(int(ts))
            rows.append(obj)
    return rows


def load_v3_snapshot():
    if not V3_SNAPSHOT.exists():
        return None
    try:
        with open(V3_SNAPSHOT, "r") as fh:
            d = json.load(fh)
        return {
            "composite_v3_prime": d.get("composite_v3_prime"),
            "composite_v1": d.get("composite_v1"),
            "sff_align": d.get("sff_align"),
            "paper_trigger_passed_v3": d.get("paper_trigger_passed_v3"),
            "ts": d.get("ts"),
            "hour_bucket": _hour_bucket(int(d["ts"])) if d.get("ts") else None,
        }
    except (OSError, json.JSONDecodeError):
        return None


def bucketize(axis_b, axis_a):
    buckets: dict[str, dict] = {}
    for r in axis_b:
        h = r.get("_hour_bucket")
        if not h:
            continue
        b = buckets.setdefault(h, {"hour_utc": h, "emits": 0, "approaches": 0, "stages": 0,
                                    "smash_elapsed_ms": [], "stage_set": set()})
        b["emits"] += 1
        if r.get("payload", {}).get("event") == "ghost_ceiling_approach":
            b["approaches"] += 1
    for r in axis_a:
        h = r.get("_hour_bucket")
        if not h:
            continue
        b = buckets.setdefault(h, {"hour_utc": h, "emits": 0, "approaches": 0, "stages": 0,
                                    "smash_elapsed_ms": [], "stage_set": set()})
        b["stages"] += 1
        b["stage_set"].add(r.get("stage", "?"))
        if r.get("stage") == "smash" and r.get("elapsed_ms"):
            b["smash_elapsed_ms"].append(int(r["elapsed_ms"]))
    out = []
    for h in sorted(buckets):
        b = buckets[h]
        elapsed = b.pop("smash_elapsed_ms")
        b["smash_elapsed_p50_ms"] = int(statistics.median(elapsed)) if elapsed else None
        b["smash_elapsed_max_ms"] = max(elapsed) if elapsed else None
        b["smash_count"] = len(elapsed)
        b["stage_set"] = sorted(b["stage_set"])
        out.append(b)
    return out


def isomorphism_metrics(buckets, v3_snap, axis_b):
    # emits ↔ stages 의 hour-level overlap
    overlap_buckets = [b for b in buckets if b["emits"] > 0 and b["stages"] > 0]
    only_b = [b for b in buckets if b["emits"] > 0 and b["stages"] == 0]
    only_a = [b for b in buckets if b["emits"] == 0 and b["stages"] > 0]
    # approach 발화 시점이 V3' snapshot ts 와 같은 hour 에 떨어지는지
    approach_at_v3_hour = False
    if v3_snap and v3_snap.get("hour_bucket"):
        for r in axis_b:
            if r.get("payload", {}).get("event") == "ghost_ceiling_approach":
                if r.get("_hour_bucket") == v3_snap["hour_bucket"]:
                    approach_at_v3_hour = True
                    break
    # smash p50 max bucket
    smash_buckets = [b for b in buckets if b.get("smash_elapsed_p50_ms")]
    max_smash = max(smash_buckets, key=lambda b: b["smash_elapsed_p50_ms"]) if smash_buckets else None
    return {
        "n_buckets_total": len(buckets),
        "n_buckets_b_and_a_overlap": len(overlap_buckets),
        "n_buckets_b_only": len(only_b),
        "n_buckets_a_only": len(only_a),
        "approach_in_same_hour_as_v3_snapshot": approach_at_v3_hour,
        "smash_p50_global_ms": int(statistics.median(
            [b["smash_elapsed_p50_ms"] for b in smash_buckets])) if smash_buckets else None,
        "smash_max_bucket": (max_smash["hour_utc"], max_smash["smash_elapsed_p50_ms"]) if max_smash else None,
    }


def interpret(iso, v3_snap, axis_b, axis_a):
    parts = []
    if iso["n_buckets_b_and_a_overlap"] == 0:
        parts.append("AXIS_DISJOINT — axis B emits 와 axis A stages 가 동일 hour 에 발생한 적 없음. cross-axis 가 timestamp 차원에서는 분리됨.")
    else:
        parts.append(f"AXIS_OVERLAP — {iso['n_buckets_b_and_a_overlap']} hour 에서 두 axis 동시 발생.")
    if iso["approach_in_same_hour_as_v3_snapshot"]:
        parts.append("APPROACH↔V3_HOUR_MATCH — ghost_ceiling_approach 발화 시점이 V3' snapshot ts 와 같은 hour. dashboard auto-emit hook (cli/run.hexa:4028) 의 cross-axis anchor 가 timestamp 차원에서도 confirm.")
    elif v3_snap:
        parts.append(f"APPROACH↔V3_HOUR_MISMATCH — approach hour 와 V3' snapshot hour ({v3_snap['hour_bucket']}) 가 다름.")
    if iso["smash_p50_global_ms"]:
        parts.append(f"SMASH_P50={iso['smash_p50_global_ms']}ms — cycle 3 의 180s timeout invariant ({180000}ms) 와 비교.")
    return " | ".join(parts)


def main():
    axis_b = load_axis_b()
    axis_a = load_axis_a()
    v3_snap = load_v3_snapshot()
    buckets = bucketize(axis_b, axis_a)
    iso = isomorphism_metrics(buckets, v3_snap, axis_b)
    summary = {
        "schema": "nexus.beyond_omega.cross_axis_join.v1",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_axis_b_rows": len(axis_b),
        "n_axis_a_rows": len(axis_a),
        "v3_snapshot": v3_snap,
        "hour_buckets": buckets,
        "isomorphism": iso,
        "interpretation": interpret(iso, v3_snap, axis_b, axis_a),
    }
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    print(f"⊙ cross_axis_join axis_b={len(axis_b)} axis_a={len(axis_a)} "
          f"buckets={len(buckets)} overlap={iso['n_buckets_b_and_a_overlap']} "
          f"approach@v3={iso['approach_in_same_hour_as_v3_snapshot']}")
    print(f"  out → {OUT.relative_to(REPO)}")
    print(f"  finding → {summary['interpretation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
