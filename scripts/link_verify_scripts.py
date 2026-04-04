#!/usr/bin/env python3
"""n6-architecture/config/products.json의 각 section에 verify_scripts 자동 연결.

각 section.domains의 docs/<domain>/verify_alien10.py를 찾아 연결.
기존 verify_scripts 필드 있으면 병합.

Usage:
  link_verify_scripts.py               # dry-run (변경사항만 출력)
  link_verify_scripts.py --apply       # products.json 실제 수정
"""

import argparse
import json
from pathlib import Path

N6_ROOT = Path.home() / "Dev/n6-architecture"
PRODUCTS_JSON = N6_ROOT / "config/products.json"
DOCS_DIR = N6_ROOT / "docs"


def find_verify_scripts_for_section(section: dict) -> list[str]:
    scripts = []
    for domain in section.get("domains", []):
        candidate = DOCS_DIR / domain / "verify_alien10.py"
        if candidate.exists():
            scripts.append(f"docs/{domain}/verify_alien10.py")
    return scripts


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()

    with open(PRODUCTS_JSON) as f:
        data = json.load(f)

    changes = []
    for sec in data.get("sections", []):
        sid = sec.get("id")
        found = find_verify_scripts_for_section(sec)
        existing = sec.get("verify_scripts", [])
        new_entries = [s for s in found if s not in existing]
        if new_entries:
            merged = existing + new_entries
            changes.append({
                "section": sid,
                "added": new_entries,
                "final": merged,
            })
            if args.apply:
                sec["verify_scripts"] = merged

    print(f"{'APPLIED' if args.apply else 'DRY-RUN'}: {len(changes)} sections updated")
    for c in changes:
        print(f"  [{c['section']}] +{len(c['added'])}: {', '.join(c['added'])}")

    # 연결 안된 섹션
    missing = [sec["id"] for sec in data.get("sections", [])
               if not sec.get("verify_scripts")
               and not find_verify_scripts_for_section(sec)
               and sec.get("alien_index", 0) >= 10]
    if missing:
        print(f"\n⚠️  alien_index>=10인데 verify_alien10.py 없는 섹션 ({len(missing)}):")
        for m in missing:
            print(f"  - {m}")

    if args.apply:
        with open(PRODUCTS_JSON, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"\n✓ {PRODUCTS_JSON} 저장")


if __name__ == "__main__":
    main()
