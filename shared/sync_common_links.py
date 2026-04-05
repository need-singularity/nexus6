#!/usr/bin/env python3
"""
sync_common_links.py — projects.json의 common_links → projects.md 자동 렌더링

- common_links 배열에서 public=true 항목만 출력
- private_repos 필드는 절대 노출 금지 (하드 가드)
- projects.md의 <!-- AUTO:COMMON_LINKS:START/END --> 마커 사이 교체

사용법:
  python3 .shared/sync_common_links.py           # dry-run
  python3 .shared/sync_common_links.py --apply   # 실제 적용
"""
import argparse
import json
import sys
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parent
PROJECTS_JSON = SHARED_DIR / "projects.json"
PROJECTS_MD = SHARED_DIR / "projects.md"
MARKER_START = "<!-- AUTO:COMMON_LINKS:START -->"
MARKER_END = "<!-- AUTO:COMMON_LINKS:END -->"


def render_links(links):
    """public=true 링크만 · 구분자로 연결 (markdown bold)"""
    parts = []
    for link in links:
        if not link.get("public", False):
            continue  # private 가드
        label = link["label"]
        url = link["url"]
        parts.append(f"**[{label}]({url})**")
    return " · ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    data = json.loads(PROJECTS_JSON.read_text(encoding="utf-8"))

    # 하드 가드: private_repos는 절대 렌더링 안 함
    if "private_repos" in data:
        exposure = data["private_repos"].get("_exposure", "")
        if exposure != "never":
            print("⚠️  private_repos._exposure != 'never' — 차단", file=sys.stderr)
            sys.exit(2)

    links = data.get("common_links", [])
    new_line = render_links(links)

    md = PROJECTS_MD.read_text(encoding="utf-8")
    if MARKER_START not in md or MARKER_END not in md:
        print("Error: 마커 없음 (AUTO:COMMON_LINKS)", file=sys.stderr)
        sys.exit(1)

    s = md.index(MARKER_START) + len(MARKER_START)
    e = md.index(MARKER_END)
    new_md = md[:s] + "\n" + new_line + "\n" + md[e:]

    if new_md == md:
        print("  OK: 변경 없음")
        return

    print(f"  새 링크 라인 ({len([l for l in links if l.get('public')])}개 공개):")
    print(f"    {new_line[:120]}...")

    if args.apply:
        PROJECTS_MD.write_text(new_md, encoding="utf-8")
        print("  ✅ projects.md 갱신")
    else:
        print("  ℹ️  dry-run — --apply로 적용")


if __name__ == "__main__":
    main()
