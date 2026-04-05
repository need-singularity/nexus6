#!/usr/bin/env python3
"""MATH_ATLAS grade → alien_index (d=0, r) 일회성 마이그레이션.

Input:  shared/math_atlas.json
Output: shared/alien_index_records.jsonl  (한 가설당 한 줄)
"""
import argparse
import json
import sys
import time
from pathlib import Path


def rank_from_grade(g):
    if not g or g.strip() in ("-", "none"):
        return None
    g = g.strip()
    if g.startswith("⬜"):
        return 0
    if g == "⚪":
        return 1
    if g == "🟥":
        return 2
    if g == "🟥★":
        return 3
    if g.startswith("🟥★★"):
        return 4
    if g == "🟦":
        return 5
    if g == "🟧":
        return 6
    if g == "🟧★":
        return 7
    if g.startswith("🟧★★"):
        return 8
    if g == "🟩":
        return 9
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--atlas", default="shared/math_atlas.json")
    ap.add_argument("--out", default="shared/alien_index_records.jsonl")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    atlas_path = Path(args.atlas)
    if not atlas_path.exists():
        print(f"ERROR: atlas not found at {atlas_path}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(atlas_path.read_text())
    hyps = data.get("hypotheses", [])

    now = int(time.time())
    records = []
    stats = {"mapped": 0, "skipped": 0, "by_r": {}}

    for h in hyps:
        hid = h.get("id") or h.get("title", "?")
        grade = h.get("grade", "")
        r = rank_from_grade(grade)
        if r is None:
            stats["skipped"] += 1
            continue
        rec = {
            "id": hid,
            "current": {"d": 0, "r": r},
            "history": [
                {
                    "timestamp_unix": now,
                    "d": 0,
                    "r": r,
                    "reason": f"migration:grade={grade}",
                }
            ],
            "promotion_candidate": r == 10,
            "promoted_from": None,
        }
        records.append(rec)
        stats["mapped"] += 1
        stats["by_r"][r] = stats["by_r"].get(r, 0) + 1

    print(f"Mapped: {stats['mapped']}  Skipped: {stats['skipped']}")
    print("Distribution by r:")
    for r in sorted(stats["by_r"]):
        print(f"  r={r}: {stats['by_r'][r]}")

    if args.dry_run:
        print("(dry-run; no file written)")
        return

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")


if __name__ == "__main__":
    main()
