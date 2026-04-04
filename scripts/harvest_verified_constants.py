#!/usr/bin/env python3
"""verify_alien10.py 스크립트들의 출력을 파싱 → shared/verified_constants.jsonl 집중 저장.

사용자 원칙: "모든 상수, 수식은 넥서스에서 보관".
각 verify 스크립트가 독자 저장소 역할 하던 문제 해결.

입력: projects.json의 n6-architecture.sections[].verify_scripts
처리: 각 스크립트 subprocess 실행 → [PASS]/[NEAR]/[FAIL] 라인 파싱
출력: ~/Dev/nexus6/shared/verified_constants.jsonl (append-only, 중복 skip)

Usage:
  harvest_verified_constants.py             # 증분 수집
  harvest_verified_constants.py --full      # 전체 재수집 (기존 파일 백업 후 재생성)
  harvest_verified_constants.py --stats     # 현재 저장 통계만
"""

from __future__ import annotations
import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Set, Tuple

NEXUS6_ROOT = Path.home() / "Dev/nexus6"
N6_ARCH_ROOT = Path.home() / "Dev/n6-architecture"
PROJECTS_JSON = NEXUS6_ROOT / "shared/projects.json"
OUT_FILE = NEXUS6_ROOT / "shared/verified_constants.jsonl"

# 두 가지 주요 포맷 지원
# 1) "[PASS] name: expected = actual (formula) -> EXACT"
# 2) "[PASS] NR-01  description"
PATTERN_FULL = re.compile(
    r"\[(PASS|NEAR|FAIL|EXACT)\]\s*([^:]+?):\s*([^=]+?)\s*=\s*([^(]+?)\s*\(([^)]+)\)\s*->\s*(\w+)"
)
PATTERN_SIMPLE = re.compile(
    r"\[(PASS|NEAR|FAIL|EXACT)\]\s*(.+)"
)
# 테이블 포맷: "BT-105a  Description  Exp  Act  PASS"
PATTERN_TABLE = re.compile(
    r"^\s*(\S+)\s+(.+?)\s+(\S+)\s+(\S+)\s+(PASS|NEAR|FAIL|EXACT)\s*$"
)


def parse_line(line: str, source_script: str) -> dict | None:
    m = PATTERN_FULL.search(line)
    if m:
        status, name, expected, actual, formula, grade = m.groups()
        return {
            "status": status.strip(),
            "name": name.strip(),
            "expected": expected.strip(),
            "actual": actual.strip(),
            "formula": formula.strip(),
            "grade": grade.strip(),
            "source": source_script,
        }
    m = PATTERN_SIMPLE.search(line)
    if m:
        status, desc = m.groups()
        return {
            "status": status.strip(),
            "name": desc.strip(),
            "source": source_script,
        }
    m = PATTERN_TABLE.match(line)
    if m:
        tag, desc, expected, actual, status = m.groups()
        # 헤더 라인 skip ("Tag Description Exp Act Result")
        if status.upper() == "RESULT":
            return None
        return {
            "status": status.strip(),
            "name": f"{tag.strip()} {desc.strip()}",
            "expected": expected.strip(),
            "actual": actual.strip(),
            "source": source_script,
        }
    return None


def load_existing() -> set[tuple]:
    """이미 기록된 (source, name) 쌍 로드."""
    seen = set()
    if OUT_FILE.exists():
        with open(OUT_FILE) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    seen.add((obj.get("source"), obj.get("name")))
                except json.JSONDecodeError:
                    continue
    return seen


def harvest_script(script_path: Path, seen: set[tuple], append_fh) -> dict:
    """verify 스크립트 1개 실행 + 파싱 + jsonl 추가."""
    rel = str(script_path.relative_to(N6_ARCH_ROOT))
    stats = {"script": rel, "parsed": 0, "new": 0, "pass": 0, "fail": 0, "near": 0}
    try:
        result = subprocess.run(
            ["python3", str(script_path)],
            capture_output=True, text=True, timeout=60,
            cwd=str(script_path.parent),
        )
    except subprocess.TimeoutExpired:
        stats["error"] = "timeout"
        return stats
    except Exception as e:
        stats["error"] = str(e)
        return stats

    now = datetime.now().isoformat(timespec="seconds")
    for line in result.stdout.splitlines():
        entry = parse_line(line, rel)
        if not entry:
            continue
        stats["parsed"] += 1
        st = entry["status"].upper()
        if st in ("PASS", "EXACT"):
            stats["pass"] += 1
        elif st == "NEAR":
            stats["near"] += 1
        elif st == "FAIL":
            stats["fail"] += 1

        key = (rel, entry["name"])
        if key in seen:
            continue
        entry["ts"] = now
        append_fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        seen.add(key)
        stats["new"] += 1

    return stats


def load_verify_scripts() -> list[Path]:
    with open(PROJECTS_JSON) as f:
        projects = json.load(f)["projects"]
    n6 = projects.get("n6-architecture", {})
    # products.json에서 verify_scripts 추출
    products_json = N6_ARCH_ROOT / n6.get("root_config", "config/products.json")
    if not products_json.exists():
        products_json = N6_ARCH_ROOT / "config/products.json"
    with open(products_json) as f:
        data = json.load(f)
    scripts = []
    for sec in data.get("sections", []):
        for rel in sec.get("verify_scripts", []):
            p = N6_ARCH_ROOT / rel
            if p.exists():
                scripts.append(p)
    return scripts


def cmd_stats():
    if not OUT_FILE.exists():
        print("(empty — run harvester first)")
        return
    total = 0
    by_status = {}
    by_source = {}
    with open(OUT_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                total += 1
                st = obj.get("status", "?")
                by_status[st] = by_status.get(st, 0) + 1
                src = obj.get("source", "?")
                by_source[src] = by_source.get(src, 0) + 1
            except json.JSONDecodeError:
                continue
    print(f"Total verified constants: {total}")
    print(f"By status: {by_status}")
    print(f"Sources: {len(by_source)}")
    for src, n in sorted(by_source.items(), key=lambda x: -x[1])[:15]:
        print(f"  {n:>4}  {src}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--full", action="store_true", help="전체 재수집 (기존 파일 백업)")
    p.add_argument("--stats", action="store_true", help="저장 통계만")
    args = p.parse_args()

    if args.stats:
        cmd_stats()
        return

    if args.full and OUT_FILE.exists():
        backup = OUT_FILE.with_suffix(".jsonl.bak")
        shutil.copy(OUT_FILE, backup)
        OUT_FILE.write_text("")
        print(f"백업: {backup}, 재수집 시작")

    seen = load_existing()
    scripts = load_verify_scripts()
    print(f"Verify scripts: {len(scripts)}, 기존 기록: {len(seen)}")

    total_new = 0
    total_pass = 0
    total_fail = 0
    with open(OUT_FILE, "a") as fh:
        for s in scripts:
            stats = harvest_script(s, seen, fh)
            total_new += stats.get("new", 0)
            total_pass += stats.get("pass", 0)
            total_fail += stats.get("fail", 0)
            marker = "✓" if stats.get("fail", 0) == 0 else "⚠️"
            print(f"  {marker} {stats['script']:50} "
                  f"parsed={stats['parsed']:>4} new={stats['new']:>4} "
                  f"PASS={stats['pass']} FAIL={stats['fail']} NEAR={stats.get('near',0)}")

    print(f"\n수집 완료: +{total_new} new, PASS={total_pass}, FAIL={total_fail}")
    print(f"저장: {OUT_FILE}")


if __name__ == "__main__":
    main()
