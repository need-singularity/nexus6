#!/usr/bin/env python3
"""논문 .md 파일을 ~/Dev/papers/manifest.json에 등록.

Usage:
  register_paper.py --id AUTO-ALIEN10-fusion \
                    --file docs/auto-alien10/fusion.md \
                    --repo n6-architecture \
                    --tier 2

또는 YAML frontmatter에서 자동 추출:
  register_paper.py --auto docs/auto-alien10/fusion.md --repo n6-architecture
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

PAPERS_DIR = Path.home() / "Dev/papers"
MANIFEST = PAPERS_DIR / "manifest.json"


def parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        km = re.match(r'^(\w[\w_]*):\s*"?([^"]*)"?\s*$', line.strip())
        if km:
            fm[km.group(1)] = km.group(2).strip()
    return fm


def extract_first_paragraph(text: str) -> str:
    """frontmatter 이후 첫 실제 텍스트 라인."""
    body = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(">") or s.startswith("<!--"):
            continue
        return s[:200]
    return ""


def load_manifest() -> dict:
    with open(MANIFEST) as f:
        return json.load(f)


def save_manifest(data: dict):
    with open(MANIFEST, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def already_registered(manifest: dict, file_path: str) -> bool:
    return any(p.get("file") == file_path for p in manifest.get("papers", []))


def next_auto_id(manifest: dict, prefix: str) -> str:
    """AUTO-<prefix>-<N> 형식 자동 id."""
    existing = [p["id"] for p in manifest.get("papers", []) if p["id"].startswith(f"AUTO-{prefix}-")]
    nums = []
    for eid in existing:
        m = re.search(r"-(\d+)$", eid)
        if m:
            nums.append(int(m.group(1)))
    n = max(nums) + 1 if nums else 1
    return f"AUTO-{prefix}-{n:03d}"


def register(md_path: Path, repo: str, tier: int = 2, id_prefix: str = "ALIEN10", explicit_id: str = None) -> dict:
    # md 파일 경로를 papers/ 기준 상대경로로
    try:
        rel_path = str(md_path.resolve().relative_to(PAPERS_DIR))
    except ValueError:
        raise ValueError(f"file not under {PAPERS_DIR}: {md_path}")

    text = md_path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    title = fm.get("title", md_path.stem)
    # 제목에서 따옴표 제거
    title = title.strip('"\'')

    manifest = load_manifest()
    if already_registered(manifest, rel_path):
        return {"status": "skipped", "reason": "already registered", "file": rel_path}

    entry = {
        "id": explicit_id or next_auto_id(manifest, id_prefix),
        "title": title,
        "repo": repo,
        "file": rel_path,
        "status": "Draft",
        "doi": None,
        "date": fm.get("generated_at") or datetime.now().strftime("%Y-%m-%d"),
        "tier": tier,
        "keywords": [],
        "abstract_first_line": extract_first_paragraph(text),
    }

    manifest.setdefault("papers", []).append(entry)
    manifest.setdefault("metadata", {})["total_papers"] = len(manifest["papers"])
    save_manifest(manifest)
    return {"status": "registered", "entry": entry}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True, help="논문 .md 경로 (papers/ 하위)")
    p.add_argument("--repo", required=True, help="소속 리포 이름 (예: n6-architecture)")
    p.add_argument("--tier", type=int, default=2)
    p.add_argument("--id-prefix", default="ALIEN10", help="AUTO-<PREFIX>-### 형식 id 생성")
    p.add_argument("--id", dest="explicit_id", help="명시적 id (auto 생성 대신)")
    args = p.parse_args()

    md_path = Path(args.file).expanduser().resolve()
    if not md_path.exists():
        print(json.dumps({"status": "error", "reason": f"file not found: {md_path}"}))
        sys.exit(1)

    try:
        result = register(md_path, args.repo, args.tier, args.id_prefix, args.explicit_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"status": "error", "reason": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
