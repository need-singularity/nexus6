#!/usr/bin/env python3
"""Bundle Query — projects.json의 bundles 스키마를 읽어 통계/쿼리 제공.

선언적 Bundle 메타스키마 소비자:
  - 각 프로젝트의 묶음 단위(sections/products/hypotheses/lenses...)를 로드
  - 통계: 총 개수, grade 분포, 완성(max_grade 도달) 개수
  - 쿼리: top-N, 완성된 것만, 도메인별 필터

Usage:
  bundle_query.py                           # 전체 요약 테이블
  bundle_query.py --project n6-architecture # 특정 프로젝트만
  bundle_query.py --bundle sections          # 특정 묶음만
  bundle_query.py --top 10                   # grade 상위 10개
  bundle_query.py --completed                # 완성된 것만 (grade==max)
  bundle_query.py --json                     # JSON 출력
"""

import argparse
import glob
import json
import re
import sys
from pathlib import Path

NEXUS6_ROOT = Path.home() / "Dev/nexus6"
PROJECTS_JSON = NEXUS6_ROOT / "shared/projects.json"


def load_projects():
    with open(PROJECTS_JSON) as f:
        data = json.load(f)
    dev_dir = Path(data.get("dev_dir", "~/Dev").replace("~", str(Path.home())))
    return data["projects"], dev_dir


def jq_path(obj, path: str):
    """매우 단순한 jq-like path: '.sections[]', '.sections[].products[]'
    Returns list of items.
    """
    if not path or path == ".":
        return [obj] if isinstance(obj, dict) else obj
    # ['.sections', '[]', '.products', '[]']
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


def parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        km = re.match(r'^(\w[\w_-]*):\s*"?([^"]*)"?\s*$', line.strip())
        if km:
            fm[km.group(1)] = km.group(2).strip()
    return fm


def normalize_grade(value, grade_map=None):
    """Grade를 숫자로. 이모지→grade_map 사용."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        if grade_map and value in grade_map:
            return float(grade_map[value])
        # 첫 문자가 grade_map에 있는지
        if grade_map and value and value[0] in grade_map:
            return float(grade_map[value[0]])
        try:
            return float(value)
        except ValueError:
            return None
    return None


def load_bundle_items(project_name, project_cfg, bundle_name, bundle_cfg, dev_dir):
    """Bundle의 실제 아이템들을 로드."""
    fmt = bundle_cfg.get("format")
    root = dev_dir / project_cfg["root"]
    items = []

    if fmt == "json":
        src = root / bundle_cfg["source"]
        if not src.exists():
            return []
        with open(src) as f:
            data = json.load(f)
        items = jq_path(data, bundle_cfg.get("path", "."))

    elif fmt == "jsonl":
        src = root / bundle_cfg["source"]
        if not src.exists():
            return []
        with open(src) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        items.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

    elif fmt == "files":
        glob_pat = str(root / bundle_cfg["source_glob"])
        files = sorted(glob.glob(glob_pat, recursive=True))
        key_mode = bundle_cfg.get("key_from_path", "basename")
        grade_field = bundle_cfg.get("grade_field")
        grade_map = bundle_cfg.get("grade_map")
        grade_source = bundle_cfg.get("grade_source", "frontmatter")
        for fp in files:
            path_obj = Path(fp)
            if key_mode == "basename":
                key = path_obj.stem
            else:
                key = str(path_obj.relative_to(root))
            entry = {"_file": str(path_obj), "_key": key}
            if grade_field:
                try:
                    text = path_obj.read_text(encoding="utf-8", errors="ignore")
                    # frontmatter 먼저
                    if grade_source in ("frontmatter", "auto"):
                        fm = parse_frontmatter(text)
                        if grade_field in fm:
                            entry[grade_field] = fm[grade_field]
                    # inline **Grade: X** 또는 **n6 Grade: X** 패턴
                    if grade_field not in entry and grade_source in ("inline", "auto"):
                        m = re.search(
                            r"\*\*(?:n6\s+)?" + re.escape(grade_field.title()) + r":\s*([^\s*]+)",
                            text, re.IGNORECASE,
                        )
                        if m:
                            entry[grade_field] = m.group(1).strip()
                except Exception:
                    pass
            items.append(entry)

    elif fmt == "grep":
        src = root / bundle_cfg["source_file"]
        pattern = bundle_cfg.get("pattern", "")
        if src.exists() and pattern:
            try:
                text = src.read_text(encoding="utf-8", errors="ignore")
                matches = re.findall(pattern, text)
                # grep mode는 개수만 리턴 (placeholder items)
                items = [{"_match": i} for i in range(len(matches))]
            except Exception:
                pass

    return items


def summarize_bundle(items, bundle_cfg):
    """아이템 리스트 → 통계."""
    total = len(items)
    grade_field = bundle_cfg.get("grade_field")
    max_grade = bundle_cfg.get("max_grade")
    grade_map = bundle_cfg.get("grade_map")
    completion_flag = bundle_cfg.get("completion_flag")

    stats = {"total": total, "with_grade": 0, "completed": 0, "grade_dist": {}}

    if not grade_field:
        return stats

    for item in items:
        if not isinstance(item, dict):
            continue
        # completion flag
        if completion_flag and item.get(completion_flag):
            stats["completed"] += 1
            continue
        g = normalize_grade(item.get(grade_field), grade_map)
        if g is None:
            continue
        stats["with_grade"] += 1
        key = int(g) if g == int(g) else round(g, 1)
        stats["grade_dist"][key] = stats["grade_dist"].get(key, 0) + 1
        if max_grade is not None and g >= max_grade:
            stats["completed"] += 1

    return stats


def format_table(rows, headers):
    """간단한 ASCII 테이블."""
    if not rows:
        return "(no data)"
    widths = [len(h) for h in headers]
    for row in rows:
        for i, c in enumerate(row):
            widths[i] = max(widths[i], len(str(c)))
    sep = "+".join("-" * (w + 2) for w in widths)
    lines = ["+" + sep + "+"]
    lines.append("|" + "|".join(f" {h:<{widths[i]}} " for i, h in enumerate(headers)) + "|")
    lines.append("+" + sep + "+")
    for row in rows:
        lines.append("|" + "|".join(f" {str(c):<{widths[i]}} " for i, c in enumerate(row)) + "|")
    lines.append("+" + sep + "+")
    return "\n".join(lines)


def cmd_summary(projects, dev_dir, args):
    """전체 요약 테이블."""
    rows = []
    total_all = {"items": 0, "completed": 0}
    for pname, pcfg in projects.items():
        bundles = pcfg.get("bundles", {})
        if not bundles:
            continue
        for bname, bcfg in bundles.items():
            if args.project and args.project != pname:
                continue
            if args.bundle and args.bundle != bname:
                continue
            items = load_bundle_items(pname, pcfg, bname, bcfg, dev_dir)
            stats = summarize_bundle(items, bcfg)
            max_g = bcfg.get("max_grade", "-")
            rows.append([
                pname,
                bname,
                stats["total"],
                stats["completed"],
                f"{stats['completed']}/{stats['total']}" + (f" (max={max_g})" if max_g != "-" else ""),
            ])
            total_all["items"] += stats["total"]
            total_all["completed"] += stats["completed"]

    if args.json:
        print(json.dumps({"rows": rows, "total": total_all}, ensure_ascii=False, indent=2))
        return
    print(format_table(rows, ["project", "bundle", "total", "completed", "progress"]))
    print(f"\nTOTAL: {total_all['items']} items, {total_all['completed']} completed")


def cmd_top(projects, dev_dir, args):
    """Grade 상위 N개."""
    all_items = []
    for pname, pcfg in projects.items():
        bundles = pcfg.get("bundles", {})
        for bname, bcfg in bundles.items():
            if args.project and args.project != pname:
                continue
            if args.bundle and args.bundle != bname:
                continue
            if not bcfg.get("grade_field"):
                continue
            items = load_bundle_items(pname, pcfg, bname, bcfg, dev_dir)
            grade_field = bcfg["grade_field"]
            grade_map = bcfg.get("grade_map")
            label_field = bcfg.get("label_field", bcfg.get("key", "_key"))
            for item in items:
                if not isinstance(item, dict):
                    continue
                g = normalize_grade(item.get(grade_field), grade_map)
                if g is None:
                    continue
                label = item.get(label_field) or item.get("_key") or "?"
                all_items.append({
                    "project": pname, "bundle": bname,
                    "grade": g, "label": str(label)[:60],
                })
    all_items.sort(key=lambda x: -x["grade"])
    top = all_items[: args.top]
    if args.json:
        print(json.dumps(top, ensure_ascii=False, indent=2))
        return
    rows = [[x["project"], x["bundle"], x["grade"], x["label"]] for x in top]
    print(format_table(rows, ["project", "bundle", "grade", "label"]))


def cmd_completed(projects, dev_dir, args):
    """완성된 것만."""
    rows = []
    for pname, pcfg in projects.items():
        bundles = pcfg.get("bundles", {})
        for bname, bcfg in bundles.items():
            if args.project and args.project != pname:
                continue
            if args.bundle and args.bundle != bname:
                continue
            items = load_bundle_items(pname, pcfg, bname, bcfg, dev_dir)
            max_g = bcfg.get("max_grade")
            grade_field = bcfg.get("grade_field")
            grade_map = bcfg.get("grade_map")
            comp_flag = bcfg.get("completion_flag")
            label_field = bcfg.get("label_field", bcfg.get("key", "_key"))
            for item in items:
                if not isinstance(item, dict):
                    continue
                completed = False
                if comp_flag and item.get(comp_flag):
                    completed = True
                elif grade_field and max_g is not None:
                    g = normalize_grade(item.get(grade_field), grade_map)
                    if g is not None and g >= max_g:
                        completed = True
                if completed:
                    label = item.get(label_field) or item.get("_key") or "?"
                    rows.append([pname, bname, str(label)[:70]])
    if args.json:
        print(json.dumps({"completed": rows}, ensure_ascii=False, indent=2))
        return
    print(format_table(rows, ["project", "bundle", "label"]))
    print(f"\nTotal completed: {len(rows)}")


def cmd_breakthrough(projects, dev_dir, args):
    """돌파(grade>=threshold) 전수조사."""
    threshold = args.threshold
    by_project = {}
    total = 0
    for pname, pcfg in projects.items():
        bundles = pcfg.get("bundles", {})
        for bname, bcfg in bundles.items():
            if args.project and args.project != pname:
                continue
            if args.bundle and args.bundle != bname:
                continue
            if not bcfg.get("grade_field"):
                continue
            items = load_bundle_items(pname, pcfg, bname, bcfg, dev_dir)
            grade_field = bcfg["grade_field"]
            grade_map = bcfg.get("grade_map")
            label_field = bcfg.get("label_field", bcfg.get("key", "_key"))
            verify_field = bcfg.get("verify_field")
            comp_flag = bcfg.get("completion_flag")
            for item in items:
                if not isinstance(item, dict):
                    continue
                g = normalize_grade(item.get(grade_field), grade_map)
                # completion_flag도 돌파로 인정
                is_complete_flag = comp_flag and item.get(comp_flag)
                if g is None and not is_complete_flag:
                    continue
                if not is_complete_flag and (g is None or g < threshold):
                    continue
                label = item.get(label_field) or item.get("_key") or "?"
                has_verify = bool(verify_field and item.get(verify_field))
                by_project.setdefault(pname, {}).setdefault(bname, []).append({
                    "label": str(label)[:60],
                    "grade": g if g is not None else "flag",
                    "verify": has_verify,
                })
                total += 1

    if args.json:
        print(json.dumps({"threshold": threshold, "total": total, "by_project": by_project},
                         ensure_ascii=False, indent=2))
        return

    print(f"\n🛸 돌파 전수조사 (grade >= {threshold})\n")
    for pname, bundles in by_project.items():
        for bname, items in bundles.items():
            print(f"── [{pname}] {bname} — {len(items)}개 ──")
            rows = [[i["grade"], "✓" if i["verify"] else "·", i["label"]] for i in items]
            print(format_table(rows, ["grade", "V", "label"]))
            print()
    print(f"TOTAL 돌파: {total}")


def cmd_audit(projects, dev_dir, args):
    """전수조사 상세 — 돌파 + verify 커버리지 + 프로젝트 통계."""
    threshold = args.threshold
    summary_rows = []
    gap_items = []
    total_break = 0
    total_break_verified = 0

    for pname, pcfg in projects.items():
        bundles = pcfg.get("bundles", {})
        for bname, bcfg in bundles.items():
            if args.project and args.project != pname:
                continue
            items = load_bundle_items(pname, pcfg, bname, bcfg, dev_dir)
            grade_field = bcfg.get("grade_field")
            grade_map = bcfg.get("grade_map")
            verify_field = bcfg.get("verify_field")
            comp_flag = bcfg.get("completion_flag")
            label_field = bcfg.get("label_field", bcfg.get("key", "_key"))
            criterion = bcfg.get("completion_criterion", "-")
            has_verify_rule = bool(bcfg.get("verify_rule"))

            n_total = len(items)
            n_break = 0
            n_verified = 0
            for item in items:
                if not isinstance(item, dict):
                    continue
                g = normalize_grade(item.get(grade_field), grade_map) if grade_field else None
                is_break = False
                if comp_flag and item.get(comp_flag):
                    is_break = True
                elif g is not None and g >= threshold:
                    is_break = True
                if is_break:
                    n_break += 1
                    has_v = bool(verify_field and item.get(verify_field))
                    if has_v:
                        n_verified += 1
                    else:
                        label = item.get(label_field) or item.get("_key") or "?"
                        gap_items.append([pname, bname, str(label)[:60], g if g is not None else "flag"])

            summary_rows.append([
                pname, bname, n_total, n_break, n_verified,
                criterion, "✓" if has_verify_rule else "·",
            ])
            total_break += n_break
            total_break_verified += n_verified

    if args.json:
        print(json.dumps({
            "threshold": threshold,
            "summary": summary_rows,
            "verify_gap": gap_items,
            "total_breakthrough": total_break,
            "total_verified": total_break_verified,
            "coverage_pct": round(100 * total_break_verified / total_break, 1) if total_break else 0,
        }, ensure_ascii=False, indent=2))
        return

    print(f"\n전수조사 (돌파 임계: grade >= {threshold})\n")
    print(format_table(summary_rows,
        ["project", "bundle", "total", "돌파", "verified", "criterion", "rule"]))
    print(f"\n돌파 총합: {total_break}  |  verified: {total_break_verified}  "
          f"|  coverage: {round(100*total_break_verified/total_break,1) if total_break else 0}%")

    if gap_items:
        print(f"\n⚠️  verify 누락 돌파 항목 ({len(gap_items)}개) — 규칙상 1단계 강등 대상:\n")
        print(format_table(gap_items[:30], ["project", "bundle", "label", "grade"]))
        if len(gap_items) > 30:
            print(f"... (+{len(gap_items)-30} more)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", help="프로젝트 필터")
    p.add_argument("--bundle", help="묶음 필터")
    p.add_argument("--top", type=int, default=0, help="grade 상위 N개")
    p.add_argument("--completed", action="store_true", help="완성된 것만")
    p.add_argument("--breakthrough", action="store_true", help="돌파(grade>=10) 전수조사")
    p.add_argument("--audit", action="store_true", help="전수조사 상세 (돌파 + verify gap)")
    p.add_argument("--threshold", type=float, default=10.0, help="돌파 임계값 (기본 10)")
    p.add_argument("--json", action="store_true", help="JSON 출력")
    args = p.parse_args()

    projects, dev_dir = load_projects()

    if args.audit:
        cmd_audit(projects, dev_dir, args)
    elif args.breakthrough:
        cmd_breakthrough(projects, dev_dir, args)
    elif args.top > 0:
        cmd_top(projects, dev_dir, args)
    elif args.completed:
        cmd_completed(projects, dev_dir, args)
    else:
        cmd_summary(projects, dev_dir, args)


if __name__ == "__main__":
    main()
