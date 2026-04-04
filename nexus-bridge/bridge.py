#!/usr/bin/env python3
"""nexus-bridge 코어 엔진 — 프로젝트 간 연결다리 관리

기능:
  - 프로젝트 자동 감지 (~/Dev 스캔)
  - 연결 상태 관리 (bridge_state.json 호환)
  - 동기화 오케스트레이션 (sync/ 스크립트 호출)
  - 성장 시스템 (포인트 기반 스테이지)
"""

import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional


class NexusBridge:
    """프로젝트 간 연결다리 중앙 관리자."""

    def __init__(self, nexus_root: Optional[str] = None):
        self.nexus_root = Path(nexus_root or os.environ.get(
            "NEXUS_ROOT", Path(__file__).parent.parent
        ))
        self.config = self._load_config()
        self.dev_root = Path(self.config["dev_root"]).expanduser()
        self.state_path = self.nexus_root / self.config["state_file"]
        self.projects_path = self.nexus_root / self.config["projects_file"]
        self.sync_dir = self.nexus_root / self.config["sync_dir"]
        self.state = self._load_state()

    def _load_config(self) -> dict:
        config_path = Path(__file__).parent / "config.json"
        with open(config_path) as f:
            return json.load(f)

    def _load_state(self) -> dict:
        if self.state_path.exists():
            with open(self.state_path) as f:
                return json.load(f)
        return {
            "_meta": {
                "description": "nexus-bridge — project connection state",
                "version": "0.1.0",
                "created": datetime.now().isoformat()
            },
            "bridge": {
                "stage": "seedling",
                "cycle": 0,
                "health": 100.0,
                "total_processed": 0,
                "total_routed": 0,
                "growth_points": 0
            },
            "connections": {},
            "routing_table": {},
            "growth_log": [],
            "stage_thresholds": self.config["growth"]["stage_thresholds"]
        }

    def _save_state(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    # ── 프로젝트 감지 ──────────────────────────────────

    def discover(self) -> list[dict]:
        """~/Dev 아래 새 프로젝트 자동 감지."""
        cfg = self.config["auto_discover"]
        if not cfg["enabled"]:
            return []

        known = set(self.state.get("connections", {}).keys())
        # projects.json에 있는 것도 known
        if self.projects_path.exists():
            with open(self.projects_path) as f:
                pj = json.load(f)
            known.update(pj.get("projects", {}).keys())
        # ignore 목록
        ignored = set(cfg.get("ignore_projects", []))

        discovered = []
        for scan_path in cfg["scan_paths"]:
            scan_dir = Path(scan_path).expanduser()
            if not scan_dir.is_dir():
                continue
            for entry in sorted(scan_dir.iterdir()):
                if not entry.is_dir():
                    continue
                name = entry.name
                if name.startswith(".") or name in cfg["ignore_patterns"]:
                    continue
                if name in known or name in ignored:
                    continue
                # 마커 파일 확인
                has_marker = any(
                    (entry / m).exists() for m in cfg["markers"]
                )
                if has_marker:
                    discovered.append({
                        "name": name,
                        "path": str(entry),
                        "markers": [
                            m for m in cfg["markers"]
                            if (entry / m).exists()
                        ]
                    })
        return discovered

    def connect(self, name: str, path: Optional[str] = None,
                description: str = "") -> dict:
        """프로젝트를 nexus-bridge에 연결."""
        if path is None:
            path = str(self.dev_root / name)

        proj_path = Path(path)
        if not proj_path.is_dir():
            return {"error": f"경로 없음: {path}"}

        # state에 연결 추가
        conn = self.state.setdefault("connections", {})
        now = datetime.now().isoformat()

        if name in conn:
            conn[name]["path"] = path
            conn[name]["last_sync"] = now
            action = "updated"
        else:
            conn[name] = {
                "path": path,
                "absorbed_count": 0,
                "digested_count": 0,
                "last_sync": now,
                "affinity_score": 0.0,
                "valuable_types": []
            }
            action = "connected"

        # projects.json에도 등록
        self._register_project(name, path, description)

        # 성장 포인트
        self._add_growth(self.config["growth"]["points_per_discovery"],
                         f"{action}: {name}")

        # 심링크 설정
        self._ensure_symlink(name, proj_path)

        self._save_state()
        return {"action": action, "name": name, "path": path}

    def disconnect(self, name: str) -> dict:
        """프로젝트 연결 해제 (상태만 제거, 파일 삭제 안 함)."""
        conn = self.state.get("connections", {})
        if name not in conn:
            return {"error": f"연결 없음: {name}"}

        del conn[name]
        self._save_state()
        return {"action": "disconnected", "name": name}

    def _register_project(self, name: str, path: str, description: str = ""):
        """nexus6-projects.json에 프로젝트 등록."""
        if self.projects_path.exists():
            with open(self.projects_path) as f:
                pj = json.load(f)
        else:
            pj = {"_meta": {"description": "NEXUS-6 프로젝트 목록", "updated": ""}, "projects": {}}

        if name not in pj["projects"]:
            pj["projects"][name] = {
                "path": f"~/Dev/{name}",
                "description": description or f"Auto-discovered project: {name}"
            }
            pj["_meta"]["updated"] = datetime.now().strftime("%Y-%m-%d")
            with open(self.projects_path, "w") as f:
                json.dump(pj, f, indent=2, ensure_ascii=False)

    def _ensure_symlink(self, name: str, proj_path: Path):
        """프로젝트에 .shared 심링크 설정."""
        if name == "nexus6":
            return
        shared_link = proj_path / ".shared"
        target = Path("../nexus6/shared")
        if shared_link.is_symlink() or shared_link.exists():
            return  # 이미 있음
        try:
            shared_link.symlink_to(target)
        except OSError:
            pass  # 권한 등 문제 시 무시

    def _verify_symlinks(self):
        """모든 연결된 프로젝트의 .shared 심링크 확인/복구."""
        for name, conn in self.state.get("connections", {}).items():
            if name == "nexus6":
                continue
            proj_path = Path(conn.get("path", "")).expanduser()
            if proj_path.is_dir():
                self._ensure_symlink(name, proj_path)

    # ── 동기화 ──────────────────────────────────────────

    # 동기화 스크립트 매핑 (순서 = 의존성 그룹)
    SYNC_MAP = {
        "claude-rules": "sync-claude-rules.sh",
        "math-atlas": "sync-math-atlas.sh",
        "calculators": "sync-calculators.sh",
        "readmes": "sync-readmes.sh",
        "lenses": "sync-nexus6-lenses.sh",
        "links": "sync-links.sh",
        "papers": "sync-papers.sh",
        "dse": "sync-dse.sh",
    }

    # 병렬 실행 가능한 독립 그룹 (의존성 없는 것끼리 묶음)
    PARALLEL_GROUPS = [
        # group 1: 독립 스크립트 (동시 실행)
        ["claude-rules", "math-atlas", "calculators", "lenses", "dse", "papers"],
        # group 2: group 1 결과에 의존
        ["readmes", "links"],
    ]

    def _resolve_script(self, script_name: str) -> Optional[Path]:
        """스크립트 경로 해석 — shared/ 우선, sync/ 폴백."""
        # shared/에 원본이 있으면 거기서 실행 (경로 문제 회피)
        shared_script = self.nexus_root / "shared" / script_name
        if shared_script.exists():
            return shared_script
        sync_script = self.sync_dir / script_name
        if sync_script.exists():
            return sync_script
        return None

    def _run_script(self, name: str, script_name: str) -> tuple[str, dict]:
        """단일 스크립트 실행 (ThreadPoolExecutor용)."""
        script = self._resolve_script(script_name)
        if script is None:
            return name, {"ok": False, "error": f"{script_name} not found"}
        try:
            import time as _time
            t0 = _time.monotonic()
            r = subprocess.run(
                ["bash", str(script)],
                capture_output=True, text=True, timeout=60
            )
            elapsed = round(_time.monotonic() - t0, 2)
            return name, {
                "ok": r.returncode == 0,
                "elapsed": elapsed,
                "warn": r.stderr.strip()[-200:] if r.returncode != 0 and r.stderr else None
            }
        except subprocess.TimeoutExpired:
            return name, {"ok": False, "error": "timeout"}

    def sync(self, targets: Optional[list[str]] = None,
             parallel: bool = True) -> dict:
        """동기화 실행. 기본 병렬. targets=None이면 전체."""
        results = {}

        if targets is None:
            if not parallel:
                # 기존 방식: sync-all.sh 단일 호출
                script = self._resolve_script("sync-all.sh") or self.sync_dir / "sync-all.sh"
                if script.exists():
                    r = subprocess.run(
                        ["bash", str(script)],
                        capture_output=True, text=True, timeout=120
                    )
                    results["all"] = {
                        "ok": r.returncode == 0,
                        "output": r.stdout[-500:] if r.stdout else ""
                    }
                else:
                    results["all"] = {"ok": False, "error": "sync-all.sh not found"}
            else:
                # 병렬 실행: 그룹별로 동시 실행
                # 먼저 심링크 검증 (sync-all.sh의 step 0)
                self._verify_symlinks()

                for group in self.PARALLEL_GROUPS:
                    with ThreadPoolExecutor(max_workers=len(group)) as pool:
                        futures = {
                            pool.submit(
                                self._run_script, t, self.SYNC_MAP[t]
                            ): t for t in group if t in self.SYNC_MAP
                        }
                        for future in as_completed(futures):
                            name, result = future.result()
                            results[name] = result
        else:
            # 지정된 타겟만 병렬 실행
            jobs = []
            for t in targets:
                script_name = self.SYNC_MAP.get(t, f"sync-{t}.sh")
                jobs.append((t, script_name))

            with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
                futures = {
                    pool.submit(self._run_script, t, sn): t
                    for t, sn in jobs
                }
                for future in as_completed(futures):
                    name, result = future.result()
                    results[name] = result

        # 성장
        ok_count = sum(1 for v in results.values() if v.get("ok"))
        self._add_growth(
            ok_count * self.config["growth"]["points_per_sync"],
            f"sync: {ok_count}/{len(results)}"
        )
        self._save_state()
        return results

    # ── 상태 조회 ───────────────────────────────────────

    def status(self) -> dict:
        """전체 브릿지 상태 반환."""
        bridge = self.state.get("bridge", {})
        connections = self.state.get("connections", {})

        active = {k: v for k, v in connections.items() if v.get("last_sync")}
        dormant = {k: v for k, v in connections.items() if not v.get("last_sync")}

        return {
            "stage": bridge.get("stage", "seedling"),
            "growth_points": bridge.get("growth_points", 0),
            "health": bridge.get("health", 0),
            "total_connections": len(connections),
            "active": len(active),
            "dormant": len(dormant),
            "projects": {
                name: {
                    "affinity": c.get("affinity_score", 0),
                    "last_sync": c.get("last_sync"),
                    "absorbed": c.get("absorbed_count", 0),
                }
                for name, c in connections.items()
            }
        }

    def health_check(self) -> list[dict]:
        """연결 건강 상태 점검."""
        issues = []
        for name, conn in self.state.get("connections", {}).items():
            path = Path(conn.get("path", "")).expanduser()
            if not path.is_dir():
                issues.append({"project": name, "issue": "path_missing", "path": str(path)})
                continue
            shared = path / ".shared"
            if name != "nexus6" and not shared.exists():
                issues.append({"project": name, "issue": "no_symlink"})
        return issues

    # ── 성장 시스템 ────────────────────────────────────

    def _add_growth(self, points: int, event: str):
        bridge = self.state.setdefault("bridge", {})
        bridge["growth_points"] = bridge.get("growth_points", 0) + points

        # 스테이지 체크
        thresholds = self.config["growth"]["stage_thresholds"]
        current = bridge.get("stage", "seedling")
        gp = bridge["growth_points"]

        stages = sorted(thresholds.items(), key=lambda x: x[1], reverse=True)
        for stage_name, threshold in stages:
            if gp >= threshold:
                if stage_name != current:
                    bridge["stage"] = stage_name
                    log = self.state.setdefault("growth_log", [])
                    log.append({
                        "event": f"stage_up: {current} -> {stage_name}",
                        "at_points": gp,
                        "timestamp": datetime.now().isoformat()
                    })
                break

    # ── Commit & Push ───────────────────────────────────

    def _git(self, repo_path: Path, *args) -> tuple[bool, str]:
        """git 명령 실행."""
        r = subprocess.run(
            ["git", *args],
            cwd=str(repo_path),
            capture_output=True, text=True, timeout=30
        )
        return r.returncode == 0, r.stdout.strip() or r.stderr.strip()

    def commit_push(self, projects: Optional[list[str]] = None,
                    message: Optional[str] = None) -> dict:
        """연결된 프로젝트들의 변경사항 commit + push.
        projects=None이면 변경 있는 모든 프로젝트 대상."""
        targets = projects or list(self.state.get("connections", {}).keys())
        results = {}

        for name in targets:
            conn = self.state.get("connections", {}).get(name)
            if not conn:
                results[name] = {"ok": False, "error": "not connected"}
                continue

            repo = Path(conn["path"]).expanduser()
            if not repo.is_dir():
                results[name] = {"ok": False, "error": "path missing"}
                continue

            # 변경사항 확인
            ok, diff = self._git(repo, "status", "--porcelain")
            if not ok or not diff:
                results[name] = {"ok": True, "action": "clean"}
                continue

            # stage all changes
            self._git(repo, "add", "-A")

            # commit
            msg = message or f"sync: nexus-bridge auto-commit ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
            ok, out = self._git(repo, "commit", "-m", msg)
            if not ok:
                results[name] = {"ok": False, "error": f"commit: {out[:100]}"}
                continue

            # push
            ok, out = self._git(repo, "push")
            if ok:
                results[name] = {"ok": True, "action": "pushed"}
                self._add_growth(self.config["growth"]["points_per_sync"],
                                 f"push: {name}")
            else:
                results[name] = {"ok": False, "error": f"push: {out[:100]}"}

        self._save_state()
        return results

    def loop(self, interval: int = 300) -> None:
        """sync → commit → push 루프. interval=초 (기본 5분)."""
        import time as _time
        cycle = 0
        while True:
            cycle += 1
            now = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{now}] cycle {cycle}")

            # 1. sync
            print("  sync...", end=" ", flush=True)
            sync_r = self.sync()
            ok = sum(1 for v in sync_r.values() if v.get("ok"))
            print(f"{ok}/{len(sync_r)}")

            # 2. commit + push (nexus6 자체)
            print("  commit+push...", end=" ", flush=True)
            cp_r = self.commit_push(["nexus6"])
            for n, r in cp_r.items():
                action = r.get("action", r.get("error", "?"))
                print(f"{n}={action}")

            # 3. 상태
            s = self.status()
            print(f"  bridge: {s['growth_points']:,} pts | {s['active']} active")

            print(f"  next in {interval}s...")
            _time.sleep(interval)

    # ── 라우팅 ──────────────────────────────────────────

    def route(self, content_type: str, source: str) -> Optional[str]:
        """콘텐츠 타입에 따라 최적 대상 프로젝트 추천."""
        routing = self.state.get("routing_table", {})
        type_routes = routing.get(content_type, {})
        if not type_routes:
            return None

        # 소스 제외, 가장 많이 라우팅된 대상
        candidates = {k: v for k, v in type_routes.items() if k != source}
        if not candidates:
            return None
        return max(candidates, key=candidates.get)
