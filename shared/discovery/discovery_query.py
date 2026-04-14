#!/usr/bin/env python3
# @hexa-first-exempt — hexa stage1 runtime lacks sqlite3 bindings
# DISC-P3-1 — hexa-native 쿼리 API via SQLite line index
"""
discovery_query.py — DISC-P3-1

SQLite index (shared/discovery_log.sqlite) built by discovery_infra.hexa --sqlite.
schema: line_index(line_no INTEGER PK, byte_offset INTEGER, ts TEXT, kind TEXT)
indexes: idx_ts(ts), idx_kind(kind)

functions:
  query_by_ts(start_iso, end_iso) -> list[dict]     # [{line_no, byte_offset, ts, kind}]
  query_by_kind(kind)             -> list[dict]
  query_recent(n)                 -> list[dict]     # last n by ts

CLI:
  ts <start> <end>    range query
  kind <k>            kind query
  recent <n>          last n rows by ts
  bench               100 random queries across 3 types, p50/p95/p99 latency (ms)
"""
from __future__ import annotations

import json
import os
import random
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

HOME = os.environ.get("HOME", "/Users/ghost")
NEXUS = os.environ.get("NEXUS", f"{HOME}/Dev/nexus")
DB_PATH = os.environ.get("DISC_SQLITE", f"{NEXUS}/shared/discovery_log.sqlite")


def _rows_to_dicts(rows) -> list[dict]:
    return [
        {"line_no": r[0], "byte_offset": r[1], "ts": r[2], "kind": r[3]}
        for r in rows
    ]


def _connect() -> sqlite3.Connection:
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"{DB_PATH} missing — run 'hexa run shared/harness/discovery_infra.hexa --sqlite' first"
        )
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA query_only = ON")
    return conn


def query_by_ts(start_iso: str, end_iso: str) -> list[dict]:
    """Range query on ts (inclusive start, inclusive end)."""
    with _connect() as c:
        cur = c.execute(
            "SELECT line_no, byte_offset, ts, kind FROM line_index "
            "WHERE ts >= ? AND ts <= ? ORDER BY ts ASC",
            (start_iso, end_iso),
        )
        return _rows_to_dicts(cur.fetchall())


def query_by_kind(kind: str) -> list[dict]:
    with _connect() as c:
        cur = c.execute(
            "SELECT line_no, byte_offset, ts, kind FROM line_index "
            "WHERE kind = ? ORDER BY line_no ASC",
            (kind,),
        )
        return _rows_to_dicts(cur.fetchall())


def query_recent(n: int) -> list[dict]:
    with _connect() as c:
        cur = c.execute(
            "SELECT line_no, byte_offset, ts, kind FROM line_index "
            "ORDER BY ts DESC LIMIT ?",
            (int(n),),
        )
        return _rows_to_dicts(cur.fetchall())


def _pctile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round((pct / 100.0) * (len(s) - 1)))))
    return s[k]


def _sample_universe() -> tuple[list[str], list[str], int]:
    """Pull distinct kinds + ts range + row_count for realistic benchmark inputs."""
    with _connect() as c:
        kinds = [r[0] for r in c.execute("SELECT DISTINCT kind FROM line_index") if r[0]]
        all_ts = [r[0] for r in c.execute("SELECT ts FROM line_index WHERE ts != ''")]
        row_count = c.execute("SELECT COUNT(*) FROM line_index").fetchone()[0]
    return kinds, all_ts, row_count


def bench(iterations: int = 100) -> dict:
    """Run `iterations` random queries across ts/kind/recent; return p50/p95/p99 ms per type."""
    kinds, all_ts, row_count = _sample_universe()
    if not kinds:
        kinds = [""]
    if not all_ts:
        all_ts = [""]
    all_ts_sorted = sorted(all_ts)

    lat_ts: list[float] = []
    lat_kind: list[float] = []
    lat_recent: list[float] = []

    rng = random.Random(42)  # deterministic bench
    for _ in range(iterations):
        # ts range
        if len(all_ts_sorted) >= 2:
            a = rng.randrange(len(all_ts_sorted))
            b = rng.randrange(len(all_ts_sorted))
            lo, hi = sorted((all_ts_sorted[a], all_ts_sorted[b]))
        else:
            lo = hi = all_ts_sorted[0]
        t0 = time.perf_counter()
        query_by_ts(lo, hi)
        lat_ts.append((time.perf_counter() - t0) * 1000.0)

        # kind
        k = rng.choice(kinds)
        t0 = time.perf_counter()
        query_by_kind(k)
        lat_kind.append((time.perf_counter() - t0) * 1000.0)

        # recent
        n = rng.choice([1, 10, 100, 1000])
        t0 = time.perf_counter()
        query_recent(n)
        lat_recent.append((time.perf_counter() - t0) * 1000.0)

    def _summary(vs: list[float]) -> dict:
        return {
            "count": len(vs),
            "p50": round(_pctile(vs, 50.0), 4),
            "p95": round(_pctile(vs, 95.0), 4),
            "p99": round(_pctile(vs, 99.0), 4),
            "mean": round(sum(vs) / len(vs), 4) if vs else 0.0,
            "max": round(max(vs), 4) if vs else 0.0,
        }

    results = {
        "iterations": iterations,
        "row_count": row_count,
        "db_path": DB_PATH,
        "db_size_bytes": os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0,
        "query_ts": _summary(lat_ts),
        "query_kind": _summary(lat_kind),
        "query_recent": _summary(lat_recent),
    }
    overall_p95 = max(
        results["query_ts"]["p95"],
        results["query_kind"]["p95"],
        results["query_recent"]["p95"],
    )
    results["p95_overall_ms"] = round(overall_p95, 4)
    results["p95_overall_met"] = bool(overall_p95 < 50.0)
    return results


def _emit(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(
            "usage:\n"
            "  discovery_query.py ts <start_iso> <end_iso>\n"
            "  discovery_query.py kind <k>\n"
            "  discovery_query.py recent <n>\n"
            "  discovery_query.py bench",
            file=sys.stderr,
        )
        return 2

    cmd = argv[1]
    try:
        if cmd == "ts":
            if len(argv) != 4:
                print("ts requires <start_iso> <end_iso>", file=sys.stderr)
                return 2
            _emit(query_by_ts(argv[2], argv[3]))
        elif cmd == "kind":
            if len(argv) != 3:
                print("kind requires <k>", file=sys.stderr)
                return 2
            _emit(query_by_kind(argv[2]))
        elif cmd == "recent":
            if len(argv) != 3:
                print("recent requires <n>", file=sys.stderr)
                return 2
            _emit(query_recent(int(argv[2])))
        elif cmd == "bench":
            _emit(bench(100))
        else:
            print(f"unknown cmd: {cmd}", file=sys.stderr)
            return 2
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
