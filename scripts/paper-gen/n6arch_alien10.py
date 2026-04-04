#!/usr/bin/env python3
"""n6-architecture alien_index=10 섹션 → 논문 스켈레톤 자동 생성

입력: ~/Dev/n6-architecture/config/products.json
출력: ~/Dev/papers/docs/auto-alien10/<section_id>.md (없는 것만)

트리거 기준: section.alien_index >= 10 && section.ceiling == true
각 섹션마다 기존 논문이 없으면 스켈레톤 생성. 내용은 draft — 사람이 분석/서사 추가.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

HOME = Path.home()
PRODUCTS_JSON = HOME / "Dev/n6-architecture/config/products.json"
OUTPUT_DIR = HOME / "Dev/papers/docs/auto-alien10"
THRESHOLD = 10


def load_sections():
    if not PRODUCTS_JSON.exists():
        print(f"[ERROR] {PRODUCTS_JSON} not found", file=sys.stderr)
        sys.exit(1)
    with open(PRODUCTS_JSON) as f:
        data = json.load(f)
    return data.get("sections", [])


def render_paper(section: dict) -> str:
    """섹션 데이터 → 마크다운 논문 스켈레톤."""
    sid = section["id"]
    title = section["title"]
    heading = section.get("heading", title)
    icon = section.get("icon", "🛸")
    now = datetime.now().strftime("%Y-%m-%d")

    products = section.get("products", [])
    domains = section.get("domains", [])
    tools = section.get("tools", [])

    bt_pct = section.get("bt_exact_pct", "?")
    bt_count = section.get("bt_count", "?")
    ind_pct = section.get("industry_pct", "?")
    ind_detail = section.get("industry_detail", "")
    exp_pct = section.get("experiment_pct", "?")
    exp_detail = section.get("experiment_detail", "")
    tp_count = section.get("tp_count", "?")
    disc_count = section.get("discovery_count", "?")
    phys_count = section.get("physics_limit_count", "?")
    mk_count = section.get("mk_count", "?")
    cross_dse = section.get("cross_dse_domains", "?")
    summary_extra = section.get("summary_extra", "")

    lines = [
        "---",
        f"title: \"{heading} — 외계인지수 10 (물리 한계 도달)\"",
        f"section_id: {sid}",
        f"alien_index: {section.get('alien_index', 10)}",
        f"ceiling: true",
        f"status: draft",
        f"generated_by: n6arch_alien10.py",
        f"generated_at: {now}",
        f"source: n6-architecture/config/products.json",
        "---",
        "",
        f"# {icon} {heading} — 외계인지수 10",
        "",
        "> **상태**: 물리적 한계 도달 — 이론·실험·양산 전 단계 완료",
        "> **자동 생성된 스켈레톤** — 분석/서사는 사람이 채움",
        "",
        "## 0. Abstract",
        "",
        "<!-- TODO: 1~2문단 요약. 주요 발견, 산업 영향, 검증 상태 -->",
        "",
        "## 1. 발견 현황 (Summary)",
        "",
        "| 지표 | 값 |",
        "|---|---|",
        f"| BT EXACT | {bt_pct}% ({bt_count}건) |",
        f"| 산업 검증 | {ind_pct}% ({ind_detail}) |",
        f"| 실험 검증 | {exp_pct}% ({exp_detail}) |",
        f"| 물리 한계 정리 | {phys_count}개 |",
        f"| TP (정리/명제) | {tp_count}개 |",
        f"| Discovery | {disc_count}건 |",
        f"| Mk 진화 단계 | {mk_count}단 |",
        f"| Cross-DSE 도메인 | {cross_dse}개 |",
    ]
    if summary_extra:
        lines.append(f"| 추가 | {summary_extra} |")

    lines += [
        "",
        "## 2. 완성 제품 목록",
        "",
    ]
    if products:
        lines.append("| # | 제품 | UFO | ver | 설명 | 링크 |")
        lines.append("|---|---|---|---|---|---|")
        for i, p in enumerate(products, 1):
            pname = p.get("name", "?")
            ufo = p.get("ufo", "?")
            ver = p.get("ver", "?")
            desc = (p.get("description") or "").replace("|", "\\|")
            links = p.get("links", [])
            link_md = ", ".join(f"[{l.get('label','링크')}]({l.get('path','')})" for l in links) if links else "-"
            lines.append(f"| {i} | {pname} | {ufo} | {ver} | {desc} | {link_md} |")
    else:
        lines.append("(제품 목록 없음)")

    lines += [
        "",
        "## 3. 도메인 · 도구",
        "",
        f"**도메인**: {', '.join(domains) if domains else '-'}",
        "",
        f"**도구**: {', '.join(tools) if tools else '-'}",
        "",
        "## 4. 핵심 발견 (BT/TP/Discovery)",
        "",
        "<!-- TODO: 이 섹션의 대표 BT·정리·Discovery 3~7개 상세 -->",
        "",
        "## 5. 물리적 한계 도달 근거",
        "",
        f"- **Alien Index 10**: {heading}은(는) 현재 물리 법칙 하에서 추가 발전이 불가능",
        f"- **Ceiling 확인**: {phys_count}개 불가능성 정리로 상한선 수학적 증명",
        f"- **검증 완료**: 이론·실험·양산 모든 단계의 검증 통과",
        "",
        "<!-- TODO: 구체적인 ceiling 논거 (수식/정리 인용) -->",
        "",
        "## 6. Mk 진화 체크포인트",
        "",
        "<!-- TODO: Mk.I~V 각 단계 요약 링크 -->",
        "",
        "## 7. 산업·사회적 영향",
        "",
        "<!-- TODO: 이 기술이 상용화될 때 미치는 영향 -->",
        "",
        "## 8. 참고 문헌",
        "",
        "<!-- TODO: 주요 인용 (BT 논문, DSE 리포트, 원전 계산기 등) -->",
        "",
        "---",
        "",
        f"*Auto-generated from `n6-architecture/config/products.json` at {now}. Edit freely — regeneration will skip existing files.*",
        "",
    ]
    return "\n".join(lines)


def main():
    sections = load_sections()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    created = []
    skipped = []
    ignored = []

    for sec in sections:
        sid = sec.get("id")
        alien = sec.get("alien_index", 0)
        ceiling = sec.get("ceiling", False)
        if not sid:
            continue
        if alien < THRESHOLD or not ceiling:
            ignored.append((sid, alien, ceiling))
            continue

        out_path = OUTPUT_DIR / f"{sid}.md"
        if out_path.exists():
            skipped.append(sid)
            continue

        content = render_paper(sec)
        out_path.write_text(content, encoding="utf-8")
        created.append(sid)

    # JSON report for watcher
    report = {
        "threshold": THRESHOLD,
        "output_dir": str(OUTPUT_DIR),
        "created": created,
        "skipped_existing": skipped,
        "ignored_below_threshold": [s[0] for s in ignored],
        "timestamp": datetime.now().isoformat(),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
