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
    }

    if cmd in commands:
        commands[cmd]()
    else:
        print(f"  Unknown command: {cmd}")
        print(f"  Available: {', '.join(commands.keys())}")


if __name__ == "__main__":
    main()
