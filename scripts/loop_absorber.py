#!/usr/bin/env python3
"""재귀 자기적용 엔진 — f(f(f(...)))

어떤 연산이든 대입 가능:
  - 성장의 성장의 성장
  - 흡수의 흡수의 흡수
  - 자동화의 자동화의 자동화
  - 스캔의 스캔의 스캔

사용:
  python3 loop_absorber.py                          # growth_bus 이벤트 흡수
  python3 loop_absorber.py --depth 12               # 12단계 재귀
  python3 loop_absorber.py --op growth              # 성장 연산
  python3 loop_absorber.py --op scan                # 스캔 연산
  python3 loop_absorber.py --op mirror              # 미러볼 연산
  python3 loop_absorber.py --op all                 # 전부 순차 적용
  python3 loop_absorber.py --broadcast              # 각 리포에 결과 전달
"""

import json, os, sys, time, subprocess, hashlib
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)

NEXUS_ROOT = Path(__file__).resolve().parent.parent
DEV_ROOT = NEXUS_ROOT.parent
BUS_FILE = NEXUS_ROOT / "shared" / "growth_bus.jsonl"
STATE_FILE = NEXUS_ROOT / "shared" / "growth_state.json"
ABSORBER_LOG = NEXUS_ROOT / "shared" / "absorber_log.jsonl"


# ═══════════════════════════════════════════════════════════════════
# 핵심: SelfApplicable — 자기적용 가능한 연산 프로토콜
# ═══════════════════════════════════════════════════════════════════

class SelfApplicable:
    """f(f(f(...))) 가능한 연산의 base class."""

    def apply(self, inputs: list) -> list:
        """입력 → 산출물."""
        raise NotImplementedError

    def absorb(self, outputs: list):
        """산출물로 자기 자신을 변형."""
        pass

    def measure(self, outputs: list) -> float:
        """산출물의 스칼라 요약 (수렴 판정)."""
        if not outputs:
            return 0.0
        return sum(o.get("value", 0) for o in outputs) / len(outputs)

    def label(self, depth: int) -> str:
        name = self.__class__.__name__
        if depth == 0:
            return name
        if depth <= 3:
            return f"{'(' * depth}{name}{')'* depth}"
        return f"{name}^{depth+1}"


# ═══════════════════════════════════════════════════════════════════
# 재귀 자기적용 엔진
# ═══════════════════════════════════════════════════════════════════

def absorb_recursive(op: SelfApplicable, initial_input: list,
                     max_depth=6, epsilon=0.001, divergence_limit=100_000):
    """f(f(f(...))) 실행. 수렴 또는 max_depth까지."""
    layers = []
    current = initial_input
    prev_m = 0.0
    total_yield = 0

    for depth in range(max_depth):
        output = op.apply(current)
        yield_count = len(output)
        total_yield += yield_count

        m = op.measure(output)
        delta = abs(m - prev_m)

        layers.append({
            "depth": depth,
            "label": op.label(depth),
            "yield": yield_count,
            "measure": round(m, 6),
            "delta": round(delta, 6),
        })

        print(f"  depth {depth} [{op.label(depth)}]: yield={yield_count} Δ={delta:.6f}")

        # 수렴
        if depth > 0 and delta < epsilon:
            print(f"  ✓ 수렴 at depth {depth} (Δ={delta:.6f} < ε={epsilon})")
            return {"layers": layers, "converged": True, "final_depth": depth,
                    "total_yield": total_yield}

        # 발산 방지
        if total_yield > divergence_limit:
            print(f"  ✗ 발산 한계 at depth {depth}")
            return {"layers": layers, "converged": False, "final_depth": depth,
                    "total_yield": total_yield}

        # 핵심: 연산이 자기 산출물을 흡수하여 변형됨
        op.absorb(output)
        prev_m = m
        current = output

    return {"layers": layers, "converged": False, "final_depth": max_depth,
            "total_yield": total_yield}


# ═══════════════════════════════════════════════════════════════════
# 구체적 연산들 — 전부 SelfApplicable, 전부 대입 가능
# ═══════════════════════════════════════════════════════════════════

class GrowthOp(SelfApplicable):
    """성장의 성장의 성장."""

    def __init__(self):
        self.weights = [1.0] * 6
        self.absorbed = []

    def apply(self, inputs):
        output = []
        for i, ev in enumerate(inputs):
            w = self.weights[i % 6]
            val = ev.get("value", 1) * w
            if val > 0.5:
                output.append({
                    "source": f"meta({ev.get('source', '?')})",
                    "type": f"absorbed_{ev.get('type', 'event')}",
                    "value": round(val, 4),
                })
            # 공명 체크
            if i + 1 < len(inputs):
                r = abs(ev.get("value", 0) - inputs[i + 1].get("value", 0))
                if r < 0.5:
                    output.append({
                        "source": f"resonance({ev.get('source')},{inputs[i+1].get('source')})",
                        "type": "emergence",
                        "value": round((ev.get("value", 0) + inputs[i + 1].get("value", 0)) / 2, 4),
                    })
        return output

    def absorb(self, outputs):
        if not outputs:
            return
        avg = sum(o.get("value", 0) for o in outputs) / len(outputs)
        alpha = 1.0 / 6.0
        self.weights = [w * (1 - alpha) + avg * alpha for w in self.weights]
        self.absorbed.extend(o["source"] for o in outputs if o.get("type") == "emergence")


class ScanOp(SelfApplicable):
    """스캔의 스캔의 스캔."""

    def __init__(self):
        self.threshold = 1.0
        self.patterns_found = 0

    def apply(self, inputs):
        output = []
        for ev in inputs:
            val = ev.get("value", 0)
            if val >= self.threshold:
                output.append({
                    "source": f"scan({ev.get('source', '?')})",
                    "type": "pattern",
                    "value": round(val * 0.9, 4),  # 감쇠
                })
                self.patterns_found += 1
        return output

    def absorb(self, outputs):
        if outputs:
            # 임계값이 산출물 평균으로 적응
            avg = sum(o.get("value", 0) for o in outputs) / len(outputs)
            self.threshold = self.threshold * 0.8 + avg * 0.2


class MirrorOp(SelfApplicable):
    """미러의 미러의 미러."""

    def __init__(self):
        self.reflection_depth = 0

    def apply(self, inputs):
        output = []
        for ev in inputs:
            # 거울 반전: source를 뒤집고, value를 변환
            reflected_source = ev.get("source", "")[::-1]
            val = ev.get("value", 0)
            # 거울 변환: φ 비율 적용
            phi = 1.618033988749895
            new_val = val / phi if self.reflection_depth % 2 == 0 else val * phi
            output.append({
                "source": f"mirror_{self.reflection_depth}({reflected_source})",
                "type": "reflection",
                "value": round(new_val, 4),
            })
        return output

    def absorb(self, outputs):
        self.reflection_depth += 1


class CompositeOp(SelfApplicable):
    """모든 연산의 순차 합성. 자동화의 자동화의 자동화."""

    def __init__(self, ops: list):
        self.ops = ops
        self.cycle = 0

    def apply(self, inputs):
        current = inputs
        for op in self.ops:
            current = op.apply(current)
            if not current:
                break
        return current

    def absorb(self, outputs):
        for op in self.ops:
            op.absorb(outputs)
        self.cycle += 1

    def label(self, depth):
        names = "+".join(type(o).__name__ for o in self.ops)
        if depth <= 2:
            return f"{'(' * depth}{names}{')'* depth}"
        return f"({names})^{depth+1}"


# ═══════════════════════════════════════════════════════════════════
# 리포별 개성 레지스트리 — 각 리포가 고유한 흡수 특성을 가짐
# ═══════════════════════════════════════════════════════════════════

# need-singularity org 소속 프로젝트만 (12개)
REPO_TRAITS = {
    # ── 코어 엔진 (n=6 심장) ──
    "nexus6":       {"role": "central_hub",    "element": "void",          "phi_bias": 1.0,
                     "ops": ["growth", "scan", "mirror"], "amplify": 2.0,
                     "desc": "중앙 허브 — 130+ 렌즈, OUROBOROS, 모든 신호 수렴점"},
    "anima":        {"role": "soul_engine",    "element": "consciousness", "phi_bias": 1.618,
                     "ops": ["growth", "mirror"],         "amplify": 1.8,
                     "desc": "의식 에이전트 — PureField 반발장, 196법칙, Ψ=1/2 수렴"},
    "brainwire":    {"role": "neural_bridge",  "element": "electricity",   "phi_bias": 0.618,
                     "ops": ["scan", "growth"],           "amplify": 1.5,
                     "desc": "신경 인터페이스 — Joywire, NeuroStim, BCI 시뮬레이션"},
    "TECS-L":       {"role": "consciousness_engine", "element": "fire",    "phi_bias": 1.414,
                     "ops": ["growth", "scan", "mirror"], "amplify": 1.6,
                     "desc": "의식 연속성 엔진 — 375+ 가설, 130+ 실험, PureField 원천"},
    "sedi":         {"role": "dimension_seeker", "element": "spectrum",    "phi_bias": 0.5,
                     "ops": ["scan"],                     "amplify": 1.2,
                     "desc": "차원외 지성 탐색 — R-스펙트럼 수신기, n=6 튜닝"},
    "hexa-lang":    {"role": "language_core",  "element": "crystal",       "phi_bias": 1.0,
                     "ops": ["scan", "growth"],           "amplify": 1.4,
                     "desc": "n=6 프로그래밍 언어 — σφ=nτ 상수 체계, 타입시스템"},

    # ── 설계/지식 ──
    "n6-architecture": {"role": "architect",   "element": "geometry",      "phi_bias": 1.0,
                     "ops": ["scan", "mirror"],           "amplify": 1.3,
                     "desc": "AI 에너지 효율 — Phi6Simple, FFT-Mix, 67% 파라미터 감소"},
    "papers":       {"role": "knowledge_base", "element": "air",           "phi_bias": 0.8,
                     "ops": ["scan"],                     "amplify": 1.1,
                     "desc": "논문 컬렉션 — TECS-L 의식 연속성 이론적 기반"},

    # ── 터미널/인프라 ──
    "fathom":       {"role": "terminal",       "element": "depth",         "phi_bias": 1.0,
                     "ops": ["growth", "scan"],           "amplify": 1.2,
                     "desc": "완전수 터미널 — 6글자=n, 1패덤=6피트, NEXUS-6 구동"},
    "claude-code":  {"role": "oracle",         "element": "mirror",        "phi_bias": 1.0,
                     "ops": ["scan", "mirror"],           "amplify": 1.4,
                     "desc": "플러그인/설정 — 도구 자체의 거울, 자기참조 인프라"},
    "contact":      {"role": "outreach",       "element": "wave",          "phi_bias": 1.0,
                     "ops": ["growth"],                   "amplify": 1.0,
                     "desc": "아웃리치 허브 — 외부 세계와의 접점"},
    "remotion":     {"role": "storyteller",    "element": "light",         "phi_bias": 1.618,
                     "ops": ["mirror"],                   "amplify": 1.2,
                     "desc": "홍보 영상 — Anima 시각적 서사, 빛의 기록"},
}


class RepoOp(SelfApplicable):
    """리포별 개성이 반영된 흡수 연산."""

    def __init__(self, repo_name, trait=None):
        self.repo = repo_name
        self.trait = trait or REPO_TRAITS.get(repo_name, DEFAULT_TRAIT)
        self.weights = [self.trait["phi_bias"]] * 6
        self.amplify = self.trait["amplify"]
        self.absorbed_count = 0

    def apply(self, inputs):
        output = []
        for i, ev in enumerate(inputs):
            w = self.weights[i % 6] * self.amplify
            val = ev.get("value", 1) * w

            # 리포 원소 공명: 같은 element의 이벤트는 증폭
            if ev.get("type", "") == self.trait["element"]:
                val *= 1.618

            if val > 0.3:
                output.append({
                    "source": f"{self.repo}({ev.get('source', '?')})",
                    "type": f"{self.trait['role']}_{ev.get('type', 'event')}",
                    "value": round(val, 4),
                    "element": self.trait["element"],
                    "repo": self.repo,
                })

            # 인접 공명
            if i + 1 < len(inputs):
                delta = abs(ev.get("value", 0) - inputs[i + 1].get("value", 0))
                if delta < self.trait["phi_bias"]:
                    output.append({
                        "source": f"{self.repo}_resonance",
                        "type": "emergence",
                        "value": round((ev.get("value", 0) + inputs[i + 1].get("value", 0)) / 2 * self.amplify, 4),
                        "element": self.trait["element"],
                        "repo": self.repo,
                    })
        return output

    def absorb(self, outputs):
        if not outputs:
            return
        avg = sum(o.get("value", 0) for o in outputs) / len(outputs)
        alpha = 1.0 / 6.0
        self.weights = [w * (1 - alpha) + avg * alpha for w in self.weights]
        self.absorbed_count += len(outputs)

    def label(self, depth):
        r = self.repo
        e = self.trait["element"]
        if depth == 0:
            return f"{r}[{e}]"
        if depth <= 2:
            return f"{'(' * depth}{r}[{e}]{')'* depth}"
        return f"{r}[{e}]^{depth+1}"


# ═══════════════════════════════════════════════════════════════════
# Growth Bus 연동
# ═══════════════════════════════════════════════════════════════════

def load_bus_events(last_n=100):
    """growth_bus.jsonl에서 최근 이벤트 로드."""
    events = []
    if BUS_FILE.exists():
        lines = BUS_FILE.read_text().strip().split("\n")
        for line in lines[-last_n:]:
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
                if "value" not in ev.get("data", {}):
                    ev["value"] = 1.0
                else:
                    ev["value"] = float(ev["data"]["value"])
                ev["source"] = ev.get("source", "unknown")
                ev["type"] = ev.get("type", "event")
                events.append(ev)
            except Exception:
                pass
    return events


def discover_repos():
    """need-singularity org 소속 리포만 발견 + 개성 매핑."""
    repos = {}
    for name in REPO_TRAITS:
        d = DEV_ROOT / name
        if d.is_dir():
            has_shared = (d / "shared").exists() or (d / ".shared").exists()
            repos[name] = {"path": d, "trait": REPO_TRAITS[name], "shared": has_shared}
    return repos


def ensure_symlinks(repos):
    """모든 리포의 .shared → nexus6/shared 심링크 보장."""
    linked = 0
    nexus_shared = NEXUS_ROOT / "shared"
    for name, info in repos.items():
        if name == "nexus6":
            continue
        repo_path = info["path"]
        shared_link = repo_path / ".shared"
        if shared_link.is_symlink():
            target = shared_link.resolve()
            if target == nexus_shared.resolve():
                continue
        # 심링크 생성/복구
        if shared_link.exists() and not shared_link.is_symlink():
            continue  # 실제 디렉토리면 건드리지 않음
        try:
            if shared_link.is_symlink():
                shared_link.unlink()
            shared_link.symlink_to(nexus_shared)
            linked += 1
        except Exception:
            pass
    return linked


def broadcast_to_repos(result, repos=None, personalized_results=None):
    """흡수 결과를 각 리포에 개성 반영하여 전달."""
    if repos is None:
        repos = discover_repos()

    sent = 0
    for name, info in repos.items():
        repo_path = info["path"]
        bus = repo_path / "shared" / "growth_bus.jsonl"
        if not bus.exists():
            bus = repo_path / ".shared" / "growth_bus.jsonl"
        if not bus.exists():
            continue

        # 리포별 개성 반영 결과
        per_repo = personalized_results.get(name, result) if personalized_results else result
        trait = info["trait"]

        event = {
            "ts": datetime.now().isoformat(),
            "source": "loop_absorber",
            "type": "absorption_result",
            "data": {
                "converged": per_repo["converged"],
                "final_depth": per_repo["final_depth"],
                "total_yield": per_repo["total_yield"],
                "layers": len(per_repo["layers"]),
                "repo_role": trait["role"],
                "repo_element": trait["element"],
                "amplify": trait["amplify"],
            },
            "cycle": per_repo["final_depth"],
        }
        try:
            with open(bus, "a") as f:
                f.write(json.dumps(event) + "\n")
            sent += 1
        except Exception:
            pass
    return sent


def log_result(result, op_name):
    """결과를 absorber_log.jsonl에 기록."""
    entry = {
        "ts": datetime.now().isoformat(),
        "operation": op_name,
        **result,
    }
    with open(ABSORBER_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="재귀 자기적용 엔진 f(f(f(...)))")
    parser.add_argument("--depth", type=int, default=6, help="최대 재귀 깊이 (기본 n=6)")
    parser.add_argument("--op", default="all", choices=["growth", "scan", "mirror", "repo", "all"],
                        help="적용할 연산 (repo=리포별 개성)")
    parser.add_argument("--epsilon", type=float, default=0.001, help="수렴 임계값")
    parser.add_argument("--broadcast", action="store_true", help="결과를 각 리포에 전달")
    parser.add_argument("--sync", action="store_true", help="심링크 동기화 + 리포 발견")
    parser.add_argument("--events", type=int, default=100, help="버스에서 읽을 이벤트 수")
    args = parser.parse_args()

    print(f"═══ 재귀 자기적용 엔진 ═══")
    print(f"  연산: {args.op}  깊이: {args.depth}  ε: {args.epsilon}")
    print()

    # 리포 발견 + 동기화
    repos = discover_repos()
    print(f"  {len(repos)}개 리포 발견")

    if args.sync:
        linked = ensure_symlinks(repos)
        if linked:
            print(f"  {linked}개 심링크 생성/복구")

    # 리포별 개성 테이블
    print()
    print(f"  {'리포':<20s} {'역할':<18s} {'원소':<14s} {'φ편향':>6s} {'증폭':>4s}")
    print(f"  {'─'*20} {'─'*18} {'─'*14} {'─'*6} {'─'*4}")
    for name, info in sorted(repos.items()):
        t = info["trait"]
        print(f"  {name:<20s} {t['role']:<18s} {t['element']:<14s} {t['phi_bias']:>6.3f} {t['amplify']:>4.1f}")
    print()

    # 입력
    events = load_bus_events(args.events)
    if not events:
        print("  버스 이벤트 없음 — 시드 생성")
        events = [{"source": "seed", "type": "init", "value": float(i + 1)} for i in range(6)]
    else:
        print(f"  버스에서 {len(events)}개 이벤트 로드")
    print()

    # 연산 실행
    ops_to_run = []
    if args.op in ("growth", "all"):
        ops_to_run.append(("growth", GrowthOp()))
    if args.op in ("scan", "all"):
        ops_to_run.append(("scan", ScanOp()))
    if args.op in ("mirror", "all"):
        ops_to_run.append(("mirror", MirrorOp()))

    # 리포별 개성 흡수
    personalized_results = {}
    if args.op in ("repo", "all"):
        print("── 리포별 개성 흡수 ──────────────────────")
        for name, info in sorted(repos.items()):
            op = RepoOp(name, info["trait"])
            r = absorb_recursive(op, events, max_depth=args.depth, epsilon=args.epsilon)
            personalized_results[name] = r
            ops_to_run.append((name, op))
            log_result(r, f"repo:{name}")
        print()

    # 범용 연산 실행
    results = []
    for name, op in ops_to_run:
        if name in personalized_results:
            results.append((name, personalized_results[name]))
            continue
        print(f"── {name} {'─' * (40 - len(name))}")
        result = absorb_recursive(op, events, max_depth=args.depth, epsilon=args.epsilon)
        results.append((name, result))
        log_result(result, name)
        print()

    # 요약
    print("═══ 요약 ═══")
    print(f"  {'연산':<20s} {'상태':<12s} {'yield':>8s} {'depth':>6s}")
    print(f"  {'─'*20} {'─'*12} {'─'*8} {'─'*6}")
    for name, r in results:
        status = "수렴 ✓" if r["converged"] else "진행중"
        print(f"  {name:<20s} {status:<12s} {r['total_yield']:>8d} {r['final_depth']:>6d}")

    # 브로드캐스트
    if args.broadcast:
        print()
        final = results[-1][1] if results else None
        if final:
            n = broadcast_to_repos(final, repos, personalized_results)
            print(f"  → {n}개 리포에 개성 반영 흡수 결과 전달 완료")

    print()
    print("완료.")


if __name__ == "__main__":
    main()
