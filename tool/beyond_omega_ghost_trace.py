#!/usr/bin/env python3
"""
beyond_omega_ghost_trace.py — nxs-20260425-004 (originally -003) ghost trace probe

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


# cycle 3 (2026-04-25): per-emit termination context capture.
# dispatch≠complete anomaly 의 (a) SIGTERM / (b) buffering / (c) launcher capture
# 셋 중 어느 것이 사실인지 falsify 하려면 emit 직후 file tail 에 SIGTERM/rc=143/
# external_fallback/timeout 등의 marker 가 있는지 확인해야 함.
TERM_MARKERS = (
    "rc=143",
    "SIGTERM",
    "Terminated",
    "retry exhausted",
    "external_fallback",
    "fallback 신호",
    "kill-after",
    "blacklisted",
    "round 1, smash",
)


def scan_one(path: Path):
    out = []
    lines: list[str] = []
    try:
        with open(path, "r", errors="replace") as fh:
            lines = fh.readlines()
    except OSError:
        return out
    for lineno, line in enumerate(lines, 1):
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
            rel = str(path)
        # tail context: emit 이후 마지막 5 lines, 그리고 termination marker hit
        tail = [l.rstrip() for l in lines[lineno:lineno + 5]]
        last_tail = [l.rstrip() for l in lines[-5:]]
        markers_hit = sorted({mk for mk in TERM_MARKERS for l in lines[lineno:] if mk in l})
        out.append({
            "file": rel,
            "lineno": lineno,
            "payload": payload,
            "post_emit_tail": tail,
            "file_last_5_lines": last_tail,
            "termination_markers_after_emit": markers_hit,
            "lines_after_emit": len(lines) - lineno,
        })
    return out


def summarize(rows):
    by_event: dict[str, int] = {}
    by_path: dict[str, int] = {}
    by_axes: dict[str, int] = {}
    by_marker: dict[str, int] = {}
    ghost_approach = []
    dispatches_with_marker = 0
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
        markers = r.get("termination_markers_after_emit", [])
        if ev == "dispatch" and markers:
            dispatches_with_marker += 1
        for mk in markers:
            by_marker[mk] = by_marker.get(mk, 0) + 1
    return {
        "total_emits": len(rows),
        "events": by_event,
        "paths": by_path,
        "axes_distribution": by_axes,
        "termination_markers_total": by_marker,
        "dispatches_followed_by_termination_marker": dispatches_with_marker,
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
        "schema": "nexus.beyond_omega.ghost_trace.v3",
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
    sigterm = sum(
        1 for r in rows
        if r["payload"].get("event") == "dispatch"
        and any(mk in r.get("termination_markers_after_emit", [])
                for mk in ("rc=143", "SIGTERM", "Terminated", "retry exhausted", "external_fallback", "fallback 신호"))
    )
    if n == 0:
        finding = "BASELINE_ZERO — scan dirs 안에 NEXUS_OMEGA emit 0 건."
    elif approach == 0 and dispatch > complete:
        sig_pct = round(100 * sigterm / dispatch, 1) if dispatch else 0.0
        finding = (
            f"DISPATCH_TERMINATED — dispatch={dispatch} complete={complete} approach=0. "
            f"dispatch 의 {sigterm}/{dispatch} ({sig_pct}%) 는 emit 후 SIGTERM/rc=143/"
            f"external_fallback marker 가 나타남. cycle 2 의 dispatch≠complete anomaly 의 "
            f"가설 (a) SIGTERM/timeout 가 STRONGLY supported. ghost ceiling 의 두 번째 "
            f"sentinel-ness layer = 'dispatch 너머는 process 종료로 진입'."
        )
    elif approach == 0:
        finding = f"DISPATCH_COMPLETE_BALANCED — dispatch={dispatch} complete={complete} approach=0."
    else:
        finding = (
            f"APPROACH_OBSERVED — approach={approach} dispatch={dispatch} complete={complete}."
        )
    return {
        "current_finding": finding,
        "approach_to_dispatch_ratio": (approach / dispatch) if dispatch else None,
        "complete_to_dispatch_ratio": (complete / dispatch) if dispatch else None,
        "dispatch_terminated_count": sigterm,
        "dispatch_terminated_ratio": (sigterm / dispatch) if dispatch else None,
    }


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
