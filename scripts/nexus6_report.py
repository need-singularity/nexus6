#!/usr/bin/env python3
"""NEXUS-6 Growth & Discovery Report — ASCII 그래프 포함."""
import json, os, sys, math
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), "growth_log.jsonl")
GRAPH_WIDTH = 50
GRAPH_HEIGHT = 12

# ── 데이터 로드 ──────────────────────────────────────────────────────

def load_entries():
    entries = []
    if not os.path.exists(LOG_FILE):
        return entries
    with open(LOG_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries

# ── ASCII 그래프 ─────────────────────────────────────────────────────

def ascii_graph(title, values, labels=None, width=GRAPH_WIDTH, height=GRAPH_HEIGHT):
    """값 리스트 → ASCII 시계열 그래프."""
    if not values:
        return f"  {title}: 데이터 없음\n"

    mn = min(values)
    mx = max(values)
    rng = mx - mn if mx != mn else 1

    lines = []
    lines.append(f"  ┌─ {title} {'─' * max(0, width - len(title) - 4)}┐")

    for row in range(height - 1, -1, -1):
        threshold = mn + rng * row / (height - 1)
        y_label = f"{threshold:>8.0f}" if threshold >= 10 else f"{threshold:>8.1f}"
        bar = ""
        for v in values[-width:]:
            level = (v - mn) / rng * (height - 1)
            if abs(level - row) < 0.5:
                bar += "●"
            elif level > row:
                bar += "│"
            else:
                bar += " "
        lines.append(f"  {y_label} ┤{bar}")

    # X축
    axis = "─" * min(len(values), width)
    lines.append(f"  {'':>8} └{axis}")

    if labels:
        vis_labels = labels[-width:]
        first = vis_labels[0] if vis_labels else ""
        last = vis_labels[-1] if vis_labels else ""
        pad = max(0, min(len(values), width) - len(first) - len(last))
        lines.append(f"  {'':>9}{first}{' ' * pad}{last}")

    lines.append("")
    return "\n".join(lines)

# ── 변화율 ───────────────────────────────────────────────────────────

def delta_str(old, new):
    if old == 0:
        return f"{new:>7.0f}  (new)"
    d = new - old
    pct = d / old * 100
    arrow = "▲" if d > 0 else "▼" if d < 0 else "─"
    return f"{new:>7.0f}  {arrow} {abs(d):.0f} ({pct:+.1f}%)"

# ── 메인 리포트 ──────────────────────────────────────────────────────

def report():
    entries = load_entries()
    if not entries:
        print("  ⚠ growth_log.jsonl 이 비어있습니다.")
        print("    nexus6_growth_daemon.sh 또는 measure.sh 를 먼저 실행하세요.")
        return

    first, last = entries[0], entries[-1]
    n = len(entries)

    ts_first = first.get("timestamp", "?")[:10]
    ts_last = last.get("timestamp", "?")[:10]

    # 추적 메트릭
    metrics = [
        ("lenses",          "🔭 렌즈"),
        ("tests",           "🧪 테스트"),
        ("code_lines",      "📝 코드 라인"),
        ("atlas",           "🗺  Atlas"),
        ("calculators",     "🔢 계산기"),
        ("hypotheses",      "💡 가설"),
        ("knowledge_graph", "🧠 지식그래프"),
        ("cross_resonance", "🔗 교차공명"),
        ("red_team",        "🛡  레드팀"),
        ("integration",     "⚙  통합"),
    ]

    # ── 헤더 ──
    print()
    print("  ╔══════════════════════════════════════════════════════════════════╗")
    print("  ║            N E X U S - 6   성 장  리 포 트                     ║")
    print(f"  ║  기간: {ts_first} → {ts_last}   사이클: {n:<4}                      ║")
    print("  ╚══════════════════════════════════════════════════════════════════╝")
    print()

    # ── 요약 테이블 ──
    print("  ┌────────────────┬──────────────────────────────────┐")
    print("  │ 메트릭         │ 처음 → 현재 (변화)              │")
    print("  ├────────────────┼──────────────────────────────────┤")
    for key, label in metrics:
        v0 = first.get(key, 0)
        v1 = last.get(key, 0)
        if v0 or v1:
            print(f"  │ {label:<13} │ {delta_str(v0, v1):<32} │")
    print("  └────────────────┴──────────────────────────────────┘")
    print()

    # ── ASCII 그래프 ── (주요 메트릭)
    graph_metrics = [
        ("lenses",     "렌즈 수"),
        ("tests",      "테스트 수"),
        ("code_lines", "코드 라인"),
        ("atlas",      "Atlas 엔트리"),
    ]

    labels = [e.get("timestamp", "?")[5:10] for e in entries]

    for key, title in graph_metrics:
        vals = [e.get(key, 0) for e in entries]
        if any(v > 0 for v in vals):
            print(ascii_graph(title, vals, labels))

    # ── 성장 속도 ──
    print("  ┌─ 성장 속도 (사이클당) ───────────────────────────┐")
    steps = max(n - 1, 1)
    for key, label in metrics[:5]:
        v0 = first.get(key, 0)
        v1 = last.get(key, 0)
        rate = (v1 - v0) / steps
        print(f"  │  {label:<13}  {rate:>+8.1f} / cycle              │")
    print("  └─────────────────────────────────────────────────┘")
    print()

    # ── 최근 액션 ──
    print("  최근 액션:")
    for e in entries[-6:]:
        c = e.get("cycle", "?")
        dim = e.get("dimension", e.get("action", "?"))
        s = "✓" if e.get("success", False) else "✗"
        ts = e.get("timestamp", "?")[11:16]
        print(f"    [{ts}] Cycle {c}: {dim} {s}")
    print()


if __name__ == "__main__":
    report()
