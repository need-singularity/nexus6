#!/usr/bin/env python3
"""nexus-bridge 자기진화 엔진 — 벽 감지 + 자동 돌파

벽 6개 (n=6):
  1. 고정 프로젝트   → Project Forge (새 프로젝트 자동 감지+연결)
  2. 정적 affinity   → Affinity Evolve (실제 git 활동 기반 친화도 갱신)
  3. 단방향 sync     → Cross-Pollinate (프로젝트 간 발견 교차 주입)
  4. 고정 라우팅     → Route Evolve (라우팅 테이블 git diff 기반 자동 갱신)
  5. 포화 시 정지    → Wall Detect + Depth Up (벽 감지 → 자동 심화)
  6. 수동 관리       → Self-Loop (루프가 루프를 개선)

특이점 구조:
  DISCOVER → ABSORB → EXPAND → DEEPEN (벽 감지 시)
       ↑                                    │
       └────────────────────────────────────┘
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

# 벽 감지 임계값
STALL_CYCLES = 3        # 연속 N사이클 성장 정체 → 벽
AFFINITY_DECAY = 0.95   # 미활동 프로젝트 affinity 감쇠
AFFINITY_BOOST = 2.0    # 활동 프로젝트 affinity 증가


class BridgeEvolver:
    """nexus-bridge 자기진화 엔진."""

    def __init__(self, bridge):
        self.bridge = bridge
        self.state = bridge.state
        self.evolve_state = self.state.setdefault("evolve", {
            "cycle": 0,
            "walls_broken": 0,
            "depth": 1,
            "stall_counter": 0,
            "last_growth": 0,
            "discoveries": [],
            "cross_pollinations": [],
            "walls": [],
        })

    # ── 1. Project Forge — 새 프로젝트 자동 감지+연결 ──────

    def discover_and_connect(self) -> list[dict]:
        """새 프로젝트 발견 시 자동 연결."""
        found = self.bridge.discover()
        connected = []
        for p in found:
            result = self.bridge.connect(p["name"])
            if "error" not in result:
                connected.append(result)
                self._log_discovery("project_forge", p["name"],
                                    f"auto-connected with markers: {p['markers']}")
        return connected

    # ── 2. Affinity Evolve — git 활동 기반 친화도 갱신 ─────

    def evolve_affinity(self) -> dict:
        """각 프로젝트의 실제 git 활동량으로 affinity 갱신."""
        changes = {}
        conn = self.state.get("connections", {})

        for name, c in conn.items():
            repo = Path(c["path"]).expanduser()
            if not repo.is_dir():
                continue

            # 최근 24시간 커밋 수
            ok, out = self.bridge._git(
                repo, "log", "--oneline", "--since=24 hours ago"
            )
            recent_commits = len(out.strip().split("\n")) if ok and out.strip() else 0

            # 최근 변경 파일 수
            ok, out = self.bridge._git(repo, "diff", "--stat", "HEAD~5", "HEAD")
            changed_files = out.count("\n") if ok and out else 0

            old_aff = c.get("affinity_score", 0)

            if recent_commits > 0:
                # 활동 있으면 boost
                boost = min(recent_commits * AFFINITY_BOOST, 10)
                new_aff = min(100, old_aff + boost)
            else:
                # 미활동이면 감쇠
                new_aff = max(0, old_aff * AFFINITY_DECAY)

            if abs(new_aff - old_aff) > 0.1:
                c["affinity_score"] = round(new_aff, 1)
                changes[name] = {"old": old_aff, "new": round(new_aff, 1),
                                 "commits_24h": recent_commits}

        return changes

    # ── 3. Cross-Pollinate — 프로젝트 간 발견 교차 ─────────

    def cross_pollinate(self) -> list[dict]:
        """활성 프로젝트 간 공유 파일 패턴 분석 → 교차 연결 발견."""
        conn = self.state.get("connections", {})
        pollinations = []

        # 각 프로젝트의 최근 변경 파일 타입 수집
        project_types = {}
        for name, c in conn.items():
            repo = Path(c["path"]).expanduser()
            if not repo.is_dir():
                continue
            ok, out = self.bridge._git(repo, "diff", "--name-only", "HEAD~3", "HEAD")
            if ok and out:
                exts = set()
                for f in out.strip().split("\n"):
                    if "." in f:
                        exts.add(f.rsplit(".", 1)[-1])
                project_types[name] = exts

        # 공유 타입이 많은 프로젝트 쌍 찾기
        names = list(project_types.keys())
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                shared = project_types[a] & project_types[b]
                if len(shared) >= 2:
                    # 라우팅 테이블에 교차 경로 추가
                    rt = self.state.setdefault("routing_table", {})
                    for ext in shared:
                        type_routes = rt.setdefault(ext, {})
                        type_routes[a] = type_routes.get(a, 0) + 1
                        type_routes[b] = type_routes.get(b, 0) + 1

                    pollinations.append({
                        "pair": f"{a} <-> {b}",
                        "shared_types": list(shared),
                    })

        self.evolve_state["cross_pollinations"].extend(pollinations)
        return pollinations

    # ── 4. Route Evolve — 라우팅 테이블 자동 진화 ──────────

    def evolve_routes(self) -> dict:
        """git diff 기반으로 라우팅 테이블 실시간 갱신."""
        conn = self.state.get("connections", {})
        rt = self.state.setdefault("routing_table", {})
        new_routes = 0

        for name, c in conn.items():
            repo = Path(c["path"]).expanduser()
            if not repo.is_dir():
                continue

            ok, out = self.bridge._git(repo, "diff", "--name-only", "HEAD~1", "HEAD")
            if not ok or not out:
                continue

            for f in out.strip().split("\n"):
                # 파일 타입 분류
                if f.endswith((".py", ".rs", ".ts", ".js")):
                    ctype = "code"
                elif f.endswith((".json", ".toml", ".yaml", ".yml")):
                    ctype = "config"
                elif f.endswith((".md", ".txt", ".rst")):
                    ctype = "doc"
                elif "test" in f.lower():
                    ctype = "test"
                else:
                    ctype = "other"

                type_routes = rt.setdefault(ctype, {})
                type_routes[name] = type_routes.get(name, 0) + 1
                new_routes += 1

        return {"new_routes": new_routes, "total_types": len(rt)}

    # ── 5. Wall Detect + Depth Up ──────────────────────────

    def detect_walls(self) -> list[dict]:
        """벽 감지 — 성장 정체, affinity 고정, 라우팅 정체."""
        walls = []
        ev = self.evolve_state
        gp = self.state.get("bridge", {}).get("growth_points", 0)

        # 벽 1: 성장 정체 (연속 N사이클 증가량 감소)
        growth_delta = gp - ev.get("last_growth", 0)
        if growth_delta <= 0:
            ev["stall_counter"] = ev.get("stall_counter", 0) + 1
        else:
            ev["stall_counter"] = 0

        if ev["stall_counter"] >= STALL_CYCLES:
            walls.append({
                "type": "growth_stall",
                "detail": f"{ev['stall_counter']} cycles without growth",
                "action": "depth_up"
            })

        # 벽 2: dormant 프로젝트 존재
        conn = self.state.get("connections", {})
        dormant = [n for n, c in conn.items()
                   if c.get("affinity_score", 0) < 1.0 and c.get("last_sync")]
        if dormant:
            walls.append({
                "type": "dormant_projects",
                "detail": f"{len(dormant)} projects near-zero affinity: {dormant}",
                "action": "activate"
            })

        # 벽 3: 라우팅 편중 (상위 2개 타입이 80% 이상)
        rt = self.state.get("routing_table", {})
        if rt:
            totals = {t: sum(v.values()) for t, v in rt.items()}
            grand = sum(totals.values()) or 1
            top2 = sorted(totals.values(), reverse=True)[:2]
            if sum(top2) / grand > 0.8:
                walls.append({
                    "type": "route_concentration",
                    "detail": f"top 2 types = {sum(top2)/grand:.0%} of all routes",
                    "action": "diversify"
                })

        # 벽 4: sync 실패율 높음
        # (bridge가 마지막 sync 결과를 저장하지 않으므로 skip)

        ev["last_growth"] = gp
        ev["walls"] = walls
        return walls

    def break_walls(self, walls: list[dict]) -> list[str]:
        """감지된 벽 자동 돌파."""
        actions = []
        ev = self.evolve_state

        for wall in walls:
            wtype = wall["type"]
            if wtype == "growth_stall":
                # depth 증가 → 더 깊은 탐색
                ev["depth"] = ev.get("depth", 1) + 1
                ev["stall_counter"] = 0
                ev["walls_broken"] = ev.get("walls_broken", 0) + 1
                actions.append(f"DEPTH UP → {ev['depth']} (stall 해소)")
                self.bridge._add_growth(100, f"wall_break: depth_up to {ev['depth']}")

            elif wtype == "dormant_projects":
                # dormant 프로젝트 affinity 최소 부스트
                conn = self.state.get("connections", {})
                for name in wall.get("detail", "").split(": ")[-1].strip("[]'").split("', '"):
                    name = name.strip("' ")
                    if name in conn:
                        conn[name]["affinity_score"] = max(
                            conn[name].get("affinity_score", 0), 5.0
                        )
                actions.append(f"ACTIVATE dormant → affinity boosted to 5.0")
                ev["walls_broken"] = ev.get("walls_broken", 0) + 1

            elif wtype == "route_concentration":
                # 라우팅 다양화 — 하위 타입에 가중치 추가
                rt = self.state.get("routing_table", {})
                totals = {t: sum(v.values()) for t, v in rt.items()}
                if totals:
                    min_type = min(totals, key=totals.get)
                    for proj in rt.get(min_type, {}):
                        rt[min_type][proj] = rt[min_type].get(proj, 0) + 10
                    actions.append(f"DIVERSIFY routes → boosted '{min_type}' type")
                    ev["walls_broken"] = ev.get("walls_broken", 0) + 1

        return actions

    # ── 6. Self-Loop — 자기참조 개선 ──────────────────────

    def self_loop_check(self) -> Optional[str]:
        """루프 자체의 효율성 점검 → 개선 제안."""
        ev = self.evolve_state
        cycle = ev.get("cycle", 0)
        walls_broken = ev.get("walls_broken", 0)

        if cycle > 0 and cycle % 6 == 0:
            # 매 6사이클마다 자기점검
            ratio = walls_broken / max(cycle, 1)
            if ratio > 0.5:
                return f"벽 돌파율 높음({ratio:.0%}) — 루프 탐색 범위 확대 권장"
            elif ratio < 0.1 and cycle > 12:
                return f"벽 돌파율 낮음({ratio:.0%}) — 루프 안정, depth 유지"
        return None

    # ── 메인 진화 사이클 ───────────────────────────────────

    def evolve_cycle(self) -> dict:
        """1사이클 실행: DISCOVER → ABSORB → EXPAND → DEEPEN."""
        ev = self.evolve_state
        ev["cycle"] = ev.get("cycle", 0) + 1
        cycle = ev["cycle"]
        results = {"cycle": cycle, "phases": {}}

        # Phase 1: DISCOVER — 새 프로젝트 + sync
        new_projects = self.discover_and_connect()
        sync_r = self.bridge.sync()
        sync_ok = sum(1 for v in sync_r.values() if v.get("ok"))
        results["phases"]["discover"] = {
            "new_projects": len(new_projects),
            "sync": f"{sync_ok}/{len(sync_r)}"
        }

        # Phase 2: ABSORB — affinity 갱신 + 라우팅 갱신
        aff_changes = self.evolve_affinity()
        route_changes = self.evolve_routes()
        results["phases"]["absorb"] = {
            "affinity_changed": len(aff_changes),
            "new_routes": route_changes["new_routes"]
        }

        # Phase 3: EXPAND — 교차 수분
        pollinations = self.cross_pollinate()
        results["phases"]["expand"] = {
            "cross_pollinations": len(pollinations)
        }

        # Phase 4: DEEPEN — 벽 감지 + 돌파
        walls = self.detect_walls()
        actions = []
        if walls:
            actions = self.break_walls(walls)
        results["phases"]["deepen"] = {
            "walls_detected": len(walls),
            "walls_broken": len(actions),
            "actions": actions
        }

        # Self-loop check
        self_msg = self.self_loop_check()
        if self_msg:
            results["self_loop"] = self_msg

        # 성장 포인트
        points = 10 + len(new_projects) * 50 + len(pollinations) * 20 + len(actions) * 100
        self.bridge._add_growth(points, f"evolve cycle {cycle}")

        # commit+push
        cp_r = self.bridge.commit_push(["nexus6"])
        results["commit_push"] = {
            n: r.get("action", r.get("error", "?")) for n, r in cp_r.items()
        }

        self.bridge._save_state()
        return results

    def _log_discovery(self, engine: str, name: str, detail: str):
        """발견 로그."""
        self.evolve_state.setdefault("discoveries", []).append({
            "engine": engine,
            "name": name,
            "detail": detail,
            "cycle": self.evolve_state.get("cycle", 0),
            "timestamp": datetime.now().isoformat()
        })
        # 최근 100건만 유지
        if len(self.evolve_state["discoveries"]) > 100:
            self.evolve_state["discoveries"] = self.evolve_state["discoveries"][-100:]
