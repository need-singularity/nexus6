#!/usr/bin/env python3
"""
beyond_omega_ghost_trace.py — nxs-20260425-003 cycle 1 first probe

L_ω 는 design/abstraction_ceiling.md §4-5 에서 "GHOST CEILING, 도달 불가 sentinel"
로 확정. "L_ω 너머" 의 첫 empirical 객체 = ghost ceiling 의 internal anatomy.

본 도구는 ghost ceiling 의 첫 측정 가능한 표면인 NEXUS_OMEGA emit
(cli/run.hexa:4065, 4073) 의 historical occurrence 를 repo-wide 로 스캔한다.

emit 종류:
  - {"event":"dispatch","axes":N,"path":"chain|debate|batch|drill",...}
  - {"event":"ghost_ceiling_approach","reason":"all_3_L3_axes_active",...} (axes>=3)
  - {"event":"complete","path":...,"rc":...}

cycle 1 finding 후보:
  - approach_count == 0 → L_ω 도달 시도가 한 번도 없었음 (baseline)
  - approach_count > 0 → 빈도/맥락 분포 = ghost ceiling structure 의 첫 측정값

raw#37/#38 enforce: design (design/beyond_omega_ladder.md) + impl (본 도구) pair.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EMIT_RE = re.compile(r'NEXUS_OMEGA\s+(\{[^\n]*\})')
SCAN_DIRS = [
    REPO / "logs",
    REPO / "state",
    REPO / ".runtime",
    REPO / "config" / "loop" / "logs",
]
# cycle 2 (2026-04-25): /tmp 가 omega launcher 의 실제 sink (com.nexus.omega-metrics.plist
# 의 stderr/stdout 경로 + statusline v2-v5 logs). state/, logs/ 가 아닌 외부 경로.
EXTRA_GLOBS = [
    "/tmp/nexus_omega_*.log",
    "/tmp/nexus_omega_*.out.log",
    "/tmp/nexus_omega_*.err.log",
    str(Path.home() / "Library" / "Logs" / "nexus" / "*.log"),
]
SCAN_EXTS = {".log", ".jsonl", ".json", ".txt", ".out", ".err"}
SKIP_NAMES = {".git", "node_modules", "__pycache__"}
MAX_FILE_BYTES = 200 * 1024 * 1024  # 200 MB cap per file


def iter_files():
    import glob as _glob
    for root in SCAN_DIRS:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_NAMES]
            for fn in filenames:
                p = Path(dirpath) / fn
                if p.suffix.lower() not in SCAN_EXTS and not p.name.endswith((".log.gz",)):
                    continue
                try:
                    if p.stat().st_size > MAX_FILE_BYTES:
                        continue
                except OSError:
                    continue
                yield p
    seen: set[str] = set()
    for pat in EXTRA_GLOBS:
        for hit in _glob.glob(pat):
            if hit in seen:
                continue
            seen.add(hit)
            p = Path(hit)
            try:
                if not p.is_file() or p.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield p


def scan_one(path: Path):
    out = []
    try:
        with open(path, "r", errors="replace") as fh:
            for lineno, line in enumerate(fh, 1):
                if "NEXUS_OMEGA" not in line:
                    continue
                m = EMIT_RE.search(line)
                if not m:
                    continue
                raw = m.group(1)
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    payload = {"_unparsed": raw}
                try:
                    rel = str(path.relative_to(REPO))
                except ValueError:
                    rel = str(path)  # external sink (/tmp, ~/Library/Logs, …)
                out.append({
                    "file": rel,
                    "lineno": lineno,
                    "payload": payload,
                })
    except OSError:
        pass
    return out


def summarize(rows):
    by_event: dict[str, int] = {}
    by_path: dict[str, int] = {}
    by_axes: dict[str, int] = {}
    ghost_approach = []
    for r in rows:
        p = r["payload"]
        ev = str(p.get("event", "_unknown"))
        by_event[ev] = by_event.get(ev, 0) + 1
        if "path" in p:
            by_path[str(p["path"])] = by_path.get(str(p["path"]), 0) + 1
        if "axes" in p:
            by_axes[str(p["axes"])] = by_axes.get(str(p["axes"]), 0) + 1
        if ev == "ghost_ceiling_approach":
            ghost_approach.append(r)
    return {
        "total_emits": len(rows),
        "events": by_event,
        "paths": by_path,
        "axes_distribution": by_axes,
        "ghost_ceiling_approach_count": by_event.get("ghost_ceiling_approach", 0),
        "ghost_ceiling_approach_samples": ghost_approach[:10],
    }


def main(argv):
    out_dir = REPO / "state"
    out_dir.mkdir(exist_ok=True)
    trace_path = out_dir / "ghost_ceiling_trace.jsonl"
    summary_path = out_dir / "ghost_ceiling_summary.json"

    t0 = time.time()
    rows = []
    files_scanned = 0
    for fp in iter_files():
        files_scanned += 1
        rows.extend(scan_one(fp))

    with open(trace_path, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    summary = {
        "schema": "nexus.beyond_omega.ghost_trace.v2",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repo": str(REPO),
        "scan_dirs_existing": [str(d.relative_to(REPO)) for d in SCAN_DIRS if d.exists()],
        "extra_globs": EXTRA_GLOBS,
        "files_scanned": files_scanned,
        "elapsed_s": round(time.time() - t0, 3),
        **summarize(rows),
        "interpretation": _interpret(rows),
    }
    with open(summary_path, "w") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    print(f"⊙ ghost_trace files_scanned={files_scanned} emits={len(rows)} "
          f"approach={summary['ghost_ceiling_approach_count']} "
          f"elapsed={summary['elapsed_s']}s")
    print(f"  trace   → {trace_path.relative_to(REPO)}")
    print(f"  summary → {summary_path.relative_to(REPO)}")
    print(f"  finding → {summary['interpretation']['current_finding']}")
    return 0


def _interpret(rows):
    n = len(rows)
    approach = sum(1 for r in rows if r["payload"].get("event") == "ghost_ceiling_approach")
    dispatch = sum(1 for r in rows if r["payload"].get("event") == "dispatch")
    complete = sum(1 for r in rows if r["payload"].get("event") == "complete")
    if n == 0:
        finding = (
            "BASELINE_ZERO — scan dirs 안에 NEXUS_OMEGA emit 0 건. "
            "ghost ceiling 의 첫 empirical 표면 = '관측 부재' 자체."
        )
    elif approach == 0:
        finding = (
            f"DISPATCH_ONLY — dispatch={dispatch} complete={complete} approach=0. "
            f"omega 호출은 발생했으나 모두 단축 경로 (axes<3) — L_ω 근접 신호 발화 0 건. "
            f"ghost ceiling 은 'invocation 은 있으나 approach 는 없는' 상태."
            + (
                f" 또한 dispatch({dispatch}) > complete({complete}) — 호출이 종료까지 trace 되지 않음 "
                f"(SIGTERM/timeout/buffering 의심)."
                if dispatch > complete else ""
            )
        )
    else:
        finding = (
            f"APPROACH_OBSERVED — approach={approach} dispatch={dispatch} complete={complete}. "
            f"ghost ceiling structure 의 첫 frequency 측정값 확보."
        )
    return {
        "current_finding": finding,
        "approach_to_dispatch_ratio": (approach / dispatch) if dispatch else None,
        "complete_to_dispatch_ratio": (complete / dispatch) if dispatch else None,
    }


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
