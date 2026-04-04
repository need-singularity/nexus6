#!/usr/bin/env python3
"""nexus-bridge CLI — 프로젝트 간 연결다리 중앙 관리

Usage:
  python3 nexus-bridge.py status              # 전체 상태
  python3 nexus-bridge.py discover            # 새 프로젝트 감지
  python3 nexus-bridge.py connect <name>      # 프로젝트 연결
  python3 nexus-bridge.py disconnect <name>   # 프로젝트 연결 해제
  python3 nexus-bridge.py sync                # 전체 동기화
  python3 nexus-bridge.py sync lenses,readmes # 부분 동기화
  python3 nexus-bridge.py health              # 건강 점검
  python3 nexus-bridge.py list                # 연결된 프로젝트 목록
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "nexus-bridge"))
from bridge import NexusBridge


def fmt_stage(stage: str) -> str:
    icons = {
        "seedling": "\U0001f331", "sprout": "\U0001f33f",
        "sapling": "\U0001f333", "tree": "\U0001f332",
        "forest": "\U0001f3d4\ufe0f",
    }
    return f"{icons.get(stage, '')} {stage}"


def cmd_status(bridge: NexusBridge):
    s = bridge.status()
    print("=" * 50)
    print(f"  NEXUS-BRIDGE {fmt_stage(s['stage'])}")
    print(f"  Growth: {s['growth_points']:,} pts | Health: {s['health']:.0f}%")
    print(f"  Connections: {s['active']} active / {s['dormant']} dormant")
    print("=" * 50)

    if s["projects"]:
        print(f"\n  {'Project':<18} {'Affinity':>8} {'Absorbed':>10} {'Last Sync'}")
        print(f"  {'-'*18} {'-'*8} {'-'*10} {'-'*20}")
        for name, p in sorted(s["projects"].items(),
                              key=lambda x: x[1]["affinity"], reverse=True):
            sync = (p["last_sync"] or "never")[:19]
            print(f"  {name:<18} {p['affinity']:>7.1f} {p['absorbed']:>10,} {sync}")
    print()


def cmd_discover(bridge: NexusBridge):
    found = bridge.discover()
    if not found:
        print("  새 프로젝트 없음 (모두 연결됨)")
        return

    print(f"  {len(found)}개 새 프로젝트 발견:\n")
    for i, p in enumerate(found, 1):
        markers = ", ".join(p["markers"])
        print(f"  {i}. {p['name']:<20} [{markers}]")
        print(f"     {p['path']}")

    print(f"\n  연결하려면: python3 nexus-bridge.py connect <name>")


def cmd_connect(bridge: NexusBridge, args: list[str]):
    if not args:
        print("  사용법: nexus-bridge.py connect <name> [--desc 'description']")
        return

    name = args[0]
    desc = ""
    if "--desc" in args:
        idx = args.index("--desc")
        if idx + 1 < len(args):
            desc = args[idx + 1]

    result = bridge.connect(name, description=desc)
    if "error" in result:
        print(f"  ERROR: {result['error']}")
    else:
        print(f"  {result['action'].upper()}: {result['name']} -> {result['path']}")


def cmd_disconnect(bridge: NexusBridge, args: list[str]):
    if not args:
        print("  사용법: nexus-bridge.py disconnect <name>")
        return

    result = bridge.disconnect(args[0])
    if "error" in result:
        print(f"  ERROR: {result['error']}")
    else:
        print(f"  DISCONNECTED: {result['name']}")


def cmd_sync(bridge: NexusBridge, args: list[str]):
    import time

    targets = None
    parallel = True
    filtered_args = []
    for a in args:
        if a == "--seq":
            parallel = False
        else:
            filtered_args.append(a)

    if filtered_args:
        targets = filtered_args[0].split(",")

    mode = "parallel" if parallel else "sequential"
    label = ", ".join(targets) if targets else "ALL"
    print(f"  Syncing: {label} ({mode})...")

    t0 = time.monotonic()
    results = bridge.sync(targets, parallel=parallel)
    elapsed = time.monotonic() - t0

    for name, r in sorted(results.items()):
        icon = "ok" if r.get("ok") else "FAIL"
        t = f" {r['elapsed']}s" if r.get("elapsed") else ""
        detail = r.get("error") or r.get("warn") or ""
        err = f" ({detail[:60]})" if not r.get("ok") and detail else ""
        print(f"  [{icon}] {name}{t}{err}")

    ok = sum(1 for v in results.values() if v.get("ok"))
    print(f"\n  {ok}/{len(results)} 완료 ({elapsed:.1f}s)")


def cmd_health(bridge: NexusBridge):
    issues = bridge.health_check()
    if not issues:
        print("  모든 연결 정상")
        return

    print(f"  {len(issues)}개 문제 발견:\n")
    for iss in issues:
        print(f"  - {iss['project']}: {iss['issue']}")
        if "path" in iss:
            print(f"    path: {iss['path']}")


def cmd_list(bridge: NexusBridge):
    conn = bridge.state.get("connections", {})
    if not conn:
        print("  연결된 프로젝트 없음")
        return

    print(f"  연결된 프로젝트 ({len(conn)}개):\n")
    for name, c in sorted(conn.items()):
        path = c.get("path", "?")
        score = c.get("affinity_score", 0)
        print(f"  {name:<18} aff={score:.1f}  {path}")


def cmd_notify(bridge: NexusBridge, args: list[str]):
    """External event notification — for loop daemons and other tools."""
    if len(args) < 2:
        print("  Usage: nexus-bridge.py notify <source> <event> [count]")
        print("  Events: discovery, sync, error")
        return

    source = args[0]
    event = args[1]
    count = int(args[2]) if len(args) > 2 else 1

    growth_cfg = bridge.config["growth"]
    points_map = {
        "discovery": growth_cfg["points_per_discovery"],
        "sync": growth_cfg["points_per_sync"],
        "error": -5,
    }

    points = points_map.get(event, 1) * count
    bridge._add_growth(points, f"{source}: {event} x{count}")

    # Update connection stats if source is a known project
    conn = bridge.state.get("connections", {})
    if source in conn:
        if event == "discovery":
            conn[source]["absorbed_count"] = conn[source].get("absorbed_count", 0) + count
        conn[source]["last_sync"] = datetime.now().isoformat()

    bridge._save_state()

    stage = bridge.state["bridge"]["stage"]
    gp = bridge.state["bridge"]["growth_points"]
    print(f"  [{source}] {event} x{count} → +{points} pts (total: {gp}, stage: {stage})")


def cmd_report(bridge: NexusBridge):
    """극가속 스타일 리포트 출력."""
    import subprocess

    s = bridge.status()
    state = bridge.state
    b = state.get("bridge", {})
    conn = state.get("connections", {})
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # git 정보
    r = subprocess.run(["git", "log", "--oneline", "-1"], capture_output=True, text=True,
                       cwd=str(bridge.nexus_root))
    last_commit = r.stdout.strip()[:60] if r.stdout else "?"

    r2 = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True,
                        cwd=str(bridge.nexus_root))
    dirty = len([l for l in r2.stdout.strip().split("\n") if l]) if r2.stdout.strip() else 0

    # 성장 진행 바
    thresholds = sorted(bridge.config["growth"]["stage_thresholds"].items(), key=lambda x: x[1])
    gp = b.get("growth_points", 0)
    current_stage = b.get("stage", "seedling")
    stage_bar = ""
    for name, thresh in thresholds:
        if gp >= thresh:
            stage_bar += f"  {name} {'█' * 8} ✅"
        else:
            filled = min(8, int(8 * gp / thresh)) if thresh > 0 else 0
            stage_bar += f"  {name} {'█' * filled}{'░' * (8 - filled)} 🔄"
            break
        stage_bar += "\n"

    # 프로젝트별 affinity 바
    proj_bars = ""
    for name, p in sorted(s["projects"].items(), key=lambda x: x[1]["affinity"], reverse=True):
        aff = p["affinity"]
        bar_len = int(aff / 10)
        bar = "━" * bar_len + "░" * (10 - bar_len)
        sync_ago = ""
        if p["last_sync"] and p["last_sync"] != "never":
            try:
                last = datetime.fromisoformat(p["last_sync"])
                delta = datetime.now() - last
                if delta.total_seconds() < 3600:
                    sync_ago = f"{int(delta.total_seconds()/60)}m ago"
                else:
                    sync_ago = f"{int(delta.total_seconds()/3600)}h ago"
            except Exception:
                sync_ago = ""
        proj_bars += f"  │  {name:<16} {bar} {aff:>5.1f}  {p['absorbed']:>5,}  {sync_ago}\n"

    # 라우팅 요약
    rt = state.get("routing_table", {})
    total_routed = sum(sum(v.values()) for v in rt.values())
    top_types = sorted(rt.items(), key=lambda x: sum(x[1].values()), reverse=True)[:3]
    route_summary = ", ".join(f"{t}({sum(v.values())})" for t, v in top_types)

    # 건강
    issues = bridge.health_check()
    health_str = "✅ 전원 정상" if not issues else f"⚠️ {len(issues)}건 문제"

    print(f"""┌─────────────────────────────────────────────────────────────┐
│  NEXUS-BRIDGE 리포트 — {now:<36}│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ■ 브릿지 상태 {fmt_stage(current_stage):<43}│
│  Growth: {gp:>6,} pts | Health: {b.get('health',0):.0f}% | Cycle: {b.get('cycle',0):<11}│
│  Connections: {s['active']} active / {s['dormant']} dormant | Routes: {total_routed:,}       │
│  ───────────────────────────────────────────────────────────│
│  📈 성장 로드맵:                                              │
{stage_bar}│                                                             │
│  ■ 프로젝트 연결 ({s['total_connections']}개)                                     │
│  {'Project':<18} {'Affinity':>10} {'Absorbed':>7}  {'Sync':<8}│
│  ───────────────────────────────────────────────────────────│
{proj_bars}│  ───────────────────────────────────────────────────────────│
│  ■ 라우팅 Top: {route_summary:<44}│
│  Total: {total_routed:,} items across {len(rt)} types                          │
│                                                             │
│  ■ 건강 체크: {health_str:<45}│
│  ■ Git: {last_commit:<52}│
│  ■ Dirty: {dirty} files                                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘""")


def cmd_commit_push(bridge: NexusBridge, args: list[str]):
    """변경 있는 프로젝트 commit + push."""
    projects = args if args else None
    msg = None

    # --msg 옵션
    if "--msg" in (args or []):
        idx = args.index("--msg")
        if idx + 1 < len(args):
            msg = args[idx + 1]
            projects = [a for a in args if a != "--msg" and a != msg] or None

    label = ", ".join(projects) if projects else "ALL"
    print(f"  Commit+Push: {label}...")

    results = bridge.commit_push(projects, msg)
    for name, r in sorted(results.items()):
        if r.get("ok"):
            action = r.get("action", "done")
            icon = "ok" if action != "clean" else "--"
            print(f"  [{icon}] {name}: {action}")
        else:
            print(f"  [FAIL] {name}: {r.get('error', '?')}")

    pushed = sum(1 for v in results.values() if v.get("action") == "pushed")
    clean = sum(1 for v in results.values() if v.get("action") == "clean")
    print(f"\n  {pushed} pushed, {clean} clean, {len(results) - pushed - clean} failed")


def cmd_loop(bridge: NexusBridge, args: list[str]):
    """sync → commit → push 반복 루프."""
    interval = int(args[0]) if args else 300
    print(f"  nexus-bridge loop 시작 (매 {interval}초)")
    print(f"  Ctrl+C로 중지\n")
    try:
        bridge.loop(interval=interval)
    except KeyboardInterrupt:
        print("\n  loop 중지됨")


def main():
    bridge = NexusBridge()

    if len(sys.argv) < 2:
        cmd_status(bridge)
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "status": lambda: cmd_status(bridge),
        "discover": lambda: cmd_discover(bridge),
        "connect": lambda: cmd_connect(bridge, args),
        "disconnect": lambda: cmd_disconnect(bridge, args),
        "sync": lambda: cmd_sync(bridge, args),
        "health": lambda: cmd_health(bridge),
        "list": lambda: cmd_list(bridge),
        "notify": lambda: cmd_notify(bridge, args),
        "report": lambda: cmd_report(bridge),
        "commit-push": lambda: cmd_commit_push(bridge, args),
        "cp": lambda: cmd_commit_push(bridge, args),
        "loop": lambda: cmd_loop(bridge, args),
    }

    if cmd in commands:
        commands[cmd]()
    else:
        print(f"  Unknown command: {cmd}")
        print(f"  Available: {', '.join(commands.keys())}")


if __name__ == "__main__":
    main()
