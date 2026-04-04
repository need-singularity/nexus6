#!/usr/bin/env python3
"""모든 프로젝트의 verify 스크립트 출력을 파싱 → shared/verified_constants.jsonl 중앙 저장.

사용자 원칙: "모든 상수, 수식은 넥서스에서 보관".

projects.json의 각 프로젝트에 선언된 verify_harvest 설정 기반으로 동작:
  - script_source="products_json": n6-architecture 방식 (products.json에서 경로 추출)
  - script_source="glob": 다른 프로젝트 (scripts_glob으로 스크립트 파일 검색)

파싱 가능한 출력 포맷 (자동 감지):
  1) "[PASS] name: expected = actual (formula) -> EXACT"
  2) "[PASS] name description"
  3) "tag description exp act PASS" (테이블)

Usage:
  harvest_verified_constants.py                # 모든 프로젝트 증분 수집
  harvest_verified_constants.py --project X    # 특정 프로젝트만
  harvest_verified_constants.py --full         # 전체 재수집
  harvest_verified_constants.py --stats        # 저장 통계
"""

from __future__ import annotations
import argparse
import glob
import json
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Set, Tuple

NEXUS6_ROOT = Path.home() / "Dev/nexus6"
PROJECTS_JSON = NEXUS6_ROOT / "shared/projects.json"
OUT_FILE = NEXUS6_ROOT / "shared/verified_constants.jsonl"

PATTERN_FULL = re.compile(
    r"\[(PASS|NEAR|FAIL|EXACT)\]\s*([^:]+?):\s*([^=]+?)\s*=\s*([^(]+?)\s*\(([^)]+)\)\s*->\s*(\w+)"
)
PATTERN_SIMPLE = re.compile(
    r"\[(PASS|NEAR|FAIL|EXACT)\]\s*(.+)"
)
PATTERN_TABLE = re.compile(
    r"^\s*(\S+)\s+(.+?)\s+(\S+)\s+(\S+)\s+(PASS|NEAR|FAIL|EXACT)\s*$"
)


def parse_line(line: str, source_script: str, project: str) -> Optional[dict]:
    m = PATTERN_FULL.search(line)
    if m:
        status, name, expected, actual, formula, grade = m.groups()
        return {
            "project": project,
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
            "project": project,
            "status": status.strip(),
            "name": desc.strip(),
            "source": source_script,
        }
    m = PATTERN_TABLE.match(line)
    if m:
        tag, desc, expected, actual, status = m.groups()
        if status.upper() == "RESULT":
            return None
        return {
            "project": project,
            "status": status.strip(),
            "name": f"{tag.strip()} {desc.strip()}",
            "expected": expected.strip(),
            "actual": actual.strip(),
            "source": source_script,
        }
    return None


def load_existing() -> Set[Tuple]:
    seen = set()
    if OUT_FILE.exists():
        with open(OUT_FILE) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    seen.add((obj.get("project"), obj.get("source"), obj.get("name")))
                except json.JSONDecodeError:
                    continue
    return seen


def jq_path(obj, path: str):
    if not path or path == ".":
        return [obj] if isinstance(obj, dict) else obj
    tokens = re.findall(r"\.\w+|\[\]", path)
    current = [obj]
    for tok in tokens:
        new = []
        if tok == "[]":
            for x in current:
                if isinstance(x, list):
                    new.extend(x)
        else:
            field = tok[1:]
            for x in current:
                if isinstance(x, dict) and field in x:
                    new.append(x[field])
        current = new
    return current


def find_scripts_for_project(project_name: str, project_cfg: dict, dev_dir: Path) -> List[Path]:
    """projects.json의 verify_harvest 설정으로 스크립트 경로 찾기."""
    cfg = project_cfg.get("verify_harvest", {})
    if not cfg.get("enabled", False):
        return []

    root = dev_dir / project_cfg["root"]
    source_type = cfg.get("script_source", "glob")

    if source_type == "products_json":
        pj = root / cfg.get("products_json", "config/products.json")
        if not pj.exists():
            return []
        with open(pj) as f:
            data = json.load(f)
        path_expr = cfg.get("products_path", ".sections[].verify_scripts[]")
        # 이중 배열 처리: .sections[].verify_scripts[] → sections 각각의 verify_scripts 리스트 평탄화
        # jq_path로 한 번에 처리 안되니 단계적 처리
        results = []
        # .sections[] 부분만 먼저
        sections_part = path_expr.rsplit(".", 1)[0]  # ".sections[]"
        field_part = path_expr.rsplit(".", 1)[1].rstrip("[]")  # "verify_scripts"
        sections = jq_path(data, sections_part)
        for sec in sections:
            if isinstance(sec, dict):
                for rel in sec.get(field_part, []):
                    p = root / rel
                    if p.exists():
                        results.append(p)
        return results

    elif source_type == "glob":
        pattern = str(root / cfg.get("scripts_glob", "**/verify_*.py"))
        return [Path(p) for p in sorted(glob.glob(pattern, recursive=True))]

    return []


def run_script(script_path: Path, project: str, project_root: Path) -> dict:
    """스크립트 실행 + 파싱 (I/O only, 중복 체크/쓰기는 호출자). 병렬 실행 안전."""
    rel = str(script_path.relative_to(project_root))
    result_data = {"script": rel, "project": project, "entries": [],
                   "parsed": 0, "pass": 0, "fail": 0, "near": 0}
    try:
        result = subprocess.run(
            ["python3", str(script_path)],
            capture_output=True, text=True, timeout=60,
            cwd=str(script_path.parent),
        )
    except subprocess.TimeoutExpired:
        result_data["error"] = "timeout"
        return result_data
    except Exception as e:
        result_data["error"] = str(e)
        return result_data

    for line in result.stdout.splitlines():
        entry = parse_line(line, rel, project)
        if not entry:
            continue
        result_data["parsed"] += 1
        st = entry["status"].upper()
        if st in ("PASS", "EXACT"):
            result_data["pass"] += 1
        elif st == "NEAR":
            result_data["near"] += 1
        elif st == "FAIL":
            result_data["fail"] += 1
        result_data["entries"].append(entry)
    return result_data


def cmd_stats():
    if not OUT_FILE.exists():
        print("(empty — run harvester first)")
        return
    total = 0
    by_project = {}
    by_status = {}
    with open(OUT_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                total += 1
                proj = obj.get("project", "?")
                by_project[proj] = by_project.get(proj, 0) + 1
                st = obj.get("status", "?")
                by_status[st] = by_status.get(st, 0) + 1
            except json.JSONDecodeError:
                continue
    print(f"Total: {total}")
    print(f"By status: {by_status}")
    print(f"By project:")
    for p, n in sorted(by_project.items(), key=lambda x: -x[1]):
        print(f"  {n:>6}  {p}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", help="특정 프로젝트만")
    p.add_argument("--full", action="store_true")
    p.add_argument("--stats", action="store_true")
    p.add_argument("--workers", type=int, default=8, help="병렬 subprocess 수")
    p.add_argument("--max-per-project", type=int, default=0, help="프로젝트당 스크립트 최대수 (0=무제한)")
    args = p.parse_args()

    if args.stats:
        cmd_stats()
        return

    if args.full and OUT_FILE.exists():
        backup = OUT_FILE.with_suffix(".jsonl.bak")
        shutil.copy(OUT_FILE, backup)
        OUT_FILE.write_text("")
        print(f"백업: {backup}, 재수집")

    with open(PROJECTS_JSON) as f:
        data = json.load(f)
    projects = data["projects"]
    dev_dir = Path(data.get("dev_dir", "~/Dev").replace("~", str(Path.home())))

    seen = load_existing()
    print(f"기존 기록: {len(seen)}\n")

    total_new = 0
    total_pass = 0
    total_fail = 0
    any_enabled = False
    now = datetime.now().isoformat(timespec="seconds")

    with open(OUT_FILE, "a") as fh:
        # 1단계: 모든 스크립트 병렬 실행
        all_tasks = []  # (script_path, project, project_root)
        for pname, pcfg in projects.items():
            if args.project and args.project != pname:
                continue
            scripts = find_scripts_for_project(pname, pcfg, dev_dir)
            if not scripts:
                continue
            if args.max_per_project > 0:
                scripts = scripts[: args.max_per_project]
            any_enabled = True
            project_root = dev_dir / pcfg["root"]
            print(f"[{pname}] {len(scripts)} scripts 큐잉")
            for s in scripts:
                all_tasks.append((s, pname, project_root))

        if not any_enabled:
            print("⚠️  projects.json에 verify_harvest.enabled=true 인 프로젝트 없음")
            return

        print(f"\n병렬 실행: {len(all_tasks)} scripts × {args.workers} workers\n")
        completed = 0
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = {ex.submit(run_script, s, p, r): (s, p, r) for s, p, r in all_tasks}
            for fut in as_completed(futures):
                completed += 1
                data = fut.result()
                # 중복 체크 + 쓰기는 메인 스레드에서 (seen 공유)
                rel = data["script"]
                proj = data["project"]
                new_count = 0
                for entry in data.get("entries", []):
                    key = (proj, rel, entry["name"])
                    if key in seen:
                        continue
                    entry["ts"] = now
                    fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    seen.add(key)
                    new_count += 1
                total_new += new_count
                total_pass += data.get("pass", 0)
                total_fail += data.get("fail", 0)
                if completed % 20 == 0 or new_count > 0 or data.get("fail", 0) > 0:
                    marker = "⚠️" if data.get("fail", 0) > 0 else "✓"
                    print(f"  [{completed:>3}/{len(all_tasks)}] {marker} [{proj}] {rel[:55]:55} "
                          f"parsed={data['parsed']:>4} new={new_count:>4} FAIL={data['fail']}")

    print(f"\n+{total_new} new, PASS={total_pass}, FAIL={total_fail}")
    print(f"저장: {OUT_FILE}")


if __name__ == "__main__":
    main()
