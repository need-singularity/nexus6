#!/usr/bin/env python3
"""
proposal_sweep.py — cross-repo staleness sweep over 6 sister inventories.

Reads state/proposals/inventory.json from each sister repo, computes a per-repo
summary (total / open / stale_count / cross_repo_blocker_count / oldest_open),
and emits a dry-run ASCII table by default.  Optional flags produce a markdown
rollup and/or append a single audit line to tool/roadmap_sync.jsonl.

Read-only.  Never mutates inventories.  Never auto-closes entries.  Human-gated.

Intended cadence: daily 09:00 KST via launchd plist (not yet wired — see nxs
daemon infra rebuild).  Proposed plist Label: com.ghost.nexus.proposal-sweep.

Repo list is hardcoded below as SISTER_REPOS.  The authoritative source of
truth for the sister-repo set is .workspace at each repo root, but we do not
parse it at runtime — update this constant in lockstep if the workspace grows.

Flags:
  --dry-run                    (default)  print ASCII table + top-3 oldest
  --write-rollup               write state/proposals/meta/sweep_YYYYMMDD.md
  --append-audit               append one JSON line to tool/roadmap_sync.jsonl
  --stale-threshold-hours N    staleness cutoff in hours (default 72)

Usage:
  python3 tool/proposal_sweep.py
  python3 tool/proposal_sweep.py --write-rollup --append-audit
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

SISTER_REPOS: list[str] = [
    "/Users/ghost/core/nexus",
    "/Users/ghost/core/anima",
    "/Users/ghost/core/hexa-lang",
    "/Users/ghost/core/airgenome",
    "/Users/ghost/core/n6-architecture",
    "/Users/ghost/core/void",
]

INVENTORY_RELPATH = "state/proposals/inventory.json"

# nexus is the rollup sink for the whole sweep
NEXUS_ROOT = Path("/Users/ghost/core/nexus")
ROLLUP_DIR = NEXUS_ROOT / "state" / "proposals" / "meta"
AUDIT_LOG = NEXUS_ROOT / "tool" / "roadmap_sync.jsonl"

OPEN_STATUSES = frozenset(
    {"in_progress", "pending", "refinement", "debate", "approved"}
)

CROSS_REPO_BLOCKER_CATEGORIES = frozenset(
    {"lang_gap", "infra_gap", "resource_gap", "atlas_gap", "data_gap"}
)

DEFAULT_STALE_HOURS = 72


# --------------------------------------------------------------------------
# Time helpers
# --------------------------------------------------------------------------

def _parse_ts(ts: str | None) -> datetime | None:
    """Parse an ISO-8601 UTC timestamp like '2026-04-22T15:49:12Z'.

    Returns None if the value is missing or unparseable — callers treat
    missing-ts as 'unknown age', not as 'very old'.
    """
    if not ts or not isinstance(ts, str):
        return None
    s = ts.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _age_ts(entry: dict) -> datetime | None:
    """Return the timestamp we'll use to judge this entry's age.

    Prefers in_progress_ts (actively worked), falls back to submitted_ts.
    """
    return _parse_ts(entry.get("in_progress_ts")) or _parse_ts(
        entry.get("submitted_ts")
    )


def _fmt_ts(dt: datetime | None) -> str:
    if dt is None:
        return "-"
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------
# Core logic
# --------------------------------------------------------------------------

def _load_inventory(repo: Path) -> dict | None:
    """Load inventory.json for a repo, or return None if missing/unreadable."""
    f = repo / INVENTORY_RELPATH
    if not f.is_file():
        return None
    try:
        with f.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"warn: could not load {f}: {exc}", file=sys.stderr
        )
        return None


def _is_open(entry: dict) -> bool:
    return entry.get("user_status") in OPEN_STATUSES


def _is_stale(entry: dict, now: datetime, threshold: timedelta) -> bool:
    if not _is_open(entry):
        return False
    age_ts = _age_ts(entry)
    if age_ts is None:
        return False
    return (now - age_ts) > threshold


def _is_cross_repo_blocker(entry: dict) -> bool:
    """Cross-repo blocker detection — matches task-#1 drift convention.

    Either:
      - priority_reason contains the literal 'cross_repo_blocker', OR
      - category is one of the known gap categories AND score_priority < 95
        (drift: should be floor-95 by the CONVENTION in nxs-20260422-008).
    """
    reason = entry.get("priority_reason") or ""
    if isinstance(reason, str) and "cross_repo_blocker" in reason:
        return True
    cat = entry.get("category")
    if cat in CROSS_REPO_BLOCKER_CATEGORIES:
        try:
            score = int(entry.get("score_priority", 0))
        except (TypeError, ValueError):
            score = 0
        if score < 95:
            return True
    return False


def summarize_repo(repo_path: Path, now: datetime, threshold: timedelta) -> dict:
    """Build the per-repo summary dict."""
    repo_name = repo_path.name
    inv = _load_inventory(repo_path)
    if inv is None:
        return {
            "repo": repo_name,
            "total": 0,
            "open": 0,
            "stale_count": 0,
            "cross_repo_blocker_count": 0,
            "oldest_open_ts": None,
            "oldest_open_id": None,
            "missing": True,
            "top_oldest": [],
        }

    entries = inv.get("entries") or []
    total = len(entries)
    open_entries = [e for e in entries if _is_open(e)]
    stale = [e for e in open_entries if _is_stale(e, now, threshold)]
    blockers = [e for e in entries if _is_cross_repo_blocker(e)]

    # Oldest open — key by age_ts ascending; entries with no ts sort last.
    def _sort_key(e: dict) -> tuple[int, datetime]:
        ts = _age_ts(e)
        if ts is None:
            return (1, datetime.max.replace(tzinfo=timezone.utc))
        return (0, ts)

    open_sorted = sorted(open_entries, key=_sort_key)
    top_oldest = [
        {
            "id": e.get("id"),
            "title": (e.get("title") or "")[:80],
            "user_status": e.get("user_status"),
            "age_ts": _fmt_ts(_age_ts(e)),
            "score_priority": e.get("score_priority"),
        }
        for e in open_sorted[:3]
    ]

    oldest = open_sorted[0] if open_sorted else None
    oldest_ts = _age_ts(oldest) if oldest else None

    return {
        "repo": repo_name,
        "total": total,
        "open": len(open_entries),
        "stale_count": len(stale),
        "cross_repo_blocker_count": len(blockers),
        "oldest_open_ts": _fmt_ts(oldest_ts) if oldest_ts else None,
        "oldest_open_id": oldest.get("id") if oldest else None,
        "missing": False,
        "top_oldest": top_oldest,
    }


def global_top_oldest(summaries: list[dict], n: int = 3) -> list[dict]:
    """Flatten all per-repo top_oldest entries and pick the global N oldest."""
    pool: list[tuple[datetime, str, dict]] = []
    for s in summaries:
        for e in s["top_oldest"]:
            ts = _parse_ts(e.get("age_ts"))
            if ts is None:
                continue
            pool.append((ts, s["repo"], e))
    pool.sort(key=lambda x: x[0])
    out = []
    for ts, repo, e in pool[:n]:
        item = dict(e)
        item["repo"] = repo
        out.append(item)
    return out


# --------------------------------------------------------------------------
# Output renderers
# --------------------------------------------------------------------------

_TABLE_HEADERS = [
    "repo",
    "total",
    "open",
    "stale",
    "xrepo_blk",
    "oldest_open_id",
    "oldest_open_ts",
]


def render_table(summaries: list[dict]) -> str:
    rows = [_TABLE_HEADERS]
    for s in summaries:
        rows.append(
            [
                s["repo"] + (" (missing)" if s["missing"] else ""),
                str(s["total"]),
                str(s["open"]),
                str(s["stale_count"]),
                str(s["cross_repo_blocker_count"]),
                str(s["oldest_open_id"] or "-"),
                str(s["oldest_open_ts"] or "-"),
            ]
        )
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    lines = []
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    lines.append(sep)
    for i, row in enumerate(rows):
        cells = " | ".join(row[j].ljust(widths[j]) for j in range(len(row)))
        lines.append("| " + cells + " |")
        if i == 0:
            lines.append(sep)
    lines.append(sep)
    return "\n".join(lines)


def render_top_oldest(top: list[dict]) -> str:
    if not top:
        return "(no open entries across any repo)"
    lines = []
    for i, e in enumerate(top, 1):
        lines.append(
            f"  {i}. [{e['repo']}] {e['id']} ({e['user_status']}, "
            f"p={e.get('score_priority')}) {e['age_ts']}"
        )
        lines.append(f"     {e['title']}")
    return "\n".join(lines)


def render_rollup_markdown(
    summaries: list[dict],
    top_oldest: list[dict],
    now: datetime,
    threshold_hours: int,
) -> str:
    lines: list[str] = []
    stamp = now.strftime("%Y-%m-%d %H:%M:%SZ")
    lines.append(f"# Proposal sweep — {stamp}")
    lines.append("")
    lines.append(f"Stale threshold: {threshold_hours}h")
    lines.append(f"Repos swept: {len(summaries)}")
    lines.append("")
    lines.append("## Summary table")
    lines.append("")
    lines.append("```")
    lines.append(render_table(summaries))
    lines.append("```")
    lines.append("")
    lines.append("## Global top-3 oldest open entries")
    lines.append("")
    lines.append("```")
    lines.append(render_top_oldest(top_oldest))
    lines.append("```")
    lines.append("")
    lines.append("## Per-repo top-3 oldest open")
    lines.append("")
    for s in summaries:
        lines.append(f"### {s['repo']}")
        if s["missing"]:
            lines.append("")
            lines.append("_inventory missing_")
            lines.append("")
            continue
        lines.append("")
        lines.append(
            f"- total={s['total']} open={s['open']} "
            f"stale={s['stale_count']} "
            f"cross_repo_blockers={s['cross_repo_blocker_count']}"
        )
        if not s["top_oldest"]:
            lines.append("- (no open entries)")
        else:
            for e in s["top_oldest"]:
                lines.append(
                    f"- `{e['id']}` `{e['user_status']}` "
                    f"p={e.get('score_priority')} {e['age_ts']} — "
                    f"{e['title']}"
                )
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Side-effects (opt-in only)
# --------------------------------------------------------------------------

def write_rollup(
    summaries: list[dict],
    top_oldest: list[dict],
    now: datetime,
    threshold_hours: int,
) -> Path:
    ROLLUP_DIR.mkdir(parents=True, exist_ok=True)
    date_tag = now.strftime("%Y%m%d")
    out = ROLLUP_DIR / f"sweep_{date_tag}.md"
    md = render_rollup_markdown(summaries, top_oldest, now, threshold_hours)
    out.write_text(md, encoding="utf-8")
    return out


def append_audit(
    summaries: list[dict],
    top_oldest: list[dict],
    now: datetime,
) -> Path:
    per_repo = {
        s["repo"]: {
            "total": s["total"],
            "open": s["open"],
            "stale_count": s["stale_count"],
            "cross_repo_blocker_count": s["cross_repo_blocker_count"],
            "oldest_open_ts": s["oldest_open_ts"],
            "oldest_open_id": s["oldest_open_id"],
            "missing": s["missing"],
        }
        for s in summaries
    }
    global_oldest = top_oldest[0] if top_oldest else None
    line = {
        "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kind": "proposal_sweep",
        "per_repo": per_repo,
        "global_oldest": global_oldest,
    }
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(line, ensure_ascii=False) + "\n")
    return AUDIT_LOG


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="proposal_sweep.py",
        description="Cross-repo proposal staleness sweep (read-only).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="print ASCII table + top-3 oldest (default behaviour)",
    )
    p.add_argument(
        "--write-rollup",
        action="store_true",
        help="write state/proposals/meta/sweep_YYYYMMDD.md",
    )
    p.add_argument(
        "--append-audit",
        action="store_true",
        help="append one JSON summary line to tool/roadmap_sync.jsonl",
    )
    p.add_argument(
        "--stale-threshold-hours",
        type=int,
        default=DEFAULT_STALE_HOURS,
        help=f"staleness cutoff in hours (default {DEFAULT_STALE_HOURS})",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    now = datetime.now(timezone.utc)
    threshold = timedelta(hours=args.stale_threshold_hours)

    summaries = [
        summarize_repo(Path(r), now, threshold) for r in SISTER_REPOS
    ]
    top_oldest = global_top_oldest(summaries, n=3)

    # Dry-run is the default surface.  The --write-rollup / --append-audit
    # flags layer on top (they do not suppress the printed table).
    print(
        f"# proposal_sweep  now={_fmt_ts(now)}  "
        f"stale_threshold={args.stale_threshold_hours}h  "
        f"repos={len(SISTER_REPOS)}"
    )
    print(render_table(summaries))
    print()
    print("top-3 oldest open entries (global):")
    print(render_top_oldest(top_oldest))

    if args.write_rollup:
        out = write_rollup(
            summaries, top_oldest, now, args.stale_threshold_hours
        )
        print(f"# rollup written: {out}")

    if args.append_audit:
        out = append_audit(summaries, top_oldest, now)
        print(f"# audit appended: {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
