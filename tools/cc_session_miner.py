"""Claude Code 세션 JSONL 마이너 — 로컬 처리만, 외부 API 호출 없음."""
import hashlib
import json
from pathlib import Path
from typing import Iterable

def parse_session(jsonl_path: Path) -> dict:
    """세션 JSONL 한 개 파싱해 tool 결과 지표 반환."""
    tool_call_count = 0
    tool_result_bytes_total = 0
    tool_result_bytes_max = 0
    corrupt_lines = 0
    call_signatures: list[str] = []
    pending_tool_use: dict[str, tuple[str, str]] = {}  # id -> (name, sig)

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                corrupt_lines += 1
                continue

            # assistant tool_use 블록에서 (이름, 인자 해시) 기록
            msg = obj.get("message") or {}
            if msg.get("role") == "assistant":
                content = msg.get("content") or []
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            name = block.get("name", "")
                            inp = json.dumps(block.get("input", {}), sort_keys=True)
                            sig = hashlib.sha1(inp.encode()).hexdigest()[:16]
                            pending_tool_use[block.get("id", "")] = (name, sig)

            tur = obj.get("toolUseResult")
            if tur and isinstance(tur, dict):
                content = tur.get("content", "")
                if isinstance(content, list):
                    content = json.dumps(content)
                size = len(str(content).encode("utf-8"))
                tool_call_count += 1
                tool_result_bytes_total += size
                if size > tool_result_bytes_max:
                    tool_result_bytes_max = size
                tool_id = tur.get("tool_use_id", "")
                if tool_id in pending_tool_use:
                    name, sig = pending_tool_use[tool_id]
                    call_signatures.append(f"{name}:{sig}")

    unique_calls = len(set(call_signatures))
    repeat_rate = 0.0
    if tool_call_count > 0:
        repeat_rate = (tool_call_count - unique_calls) / tool_call_count

    return {
        "tool_call_count": tool_call_count,
        "tool_result_bytes_total": tool_result_bytes_total,
        "tool_result_bytes_max": tool_result_bytes_max,
        "corrupt_lines": corrupt_lines,
        "unique_calls": unique_calls,
        "repeat_rate": repeat_rate,
    }


def aggregate_sessions(paths: Iterable[Path]) -> dict:
    """여러 세션 JSONL을 집계."""
    paths = list(paths)
    per_session = [parse_session(p) for p in paths]
    total_calls = sum(s["tool_call_count"] for s in per_session)
    total_bytes = sum(s["tool_result_bytes_total"] for s in per_session)
    all_result_sizes = _collect_all_result_sizes(paths)
    all_result_sizes.sort()
    n = len(all_result_sizes)
    mean_bytes = total_bytes / total_calls if total_calls else 0
    p95 = all_result_sizes[int(n * 0.95)] if n > 0 else 0
    p50 = all_result_sizes[int(n * 0.5)] if n > 0 else 0
    repeat_rates = [s["repeat_rate"] for s in per_session if s["tool_call_count"] > 0]
    mean_repeat = sum(repeat_rates) / len(repeat_rates) if repeat_rates else 0
    corrupt_total = sum(s["corrupt_lines"] for s in per_session)
    return {
        "session_count": len(paths),
        "total_tool_calls": total_calls,
        "total_tool_result_bytes": total_bytes,
        "mean_tool_result_bytes": mean_bytes,
        "p50_tool_result_bytes": p50,
        "p95_tool_result_bytes": p95,
        "mean_repeat_rate": mean_repeat,
        "corrupt_lines_total": corrupt_total,
    }


def _collect_all_result_sizes(paths: Iterable[Path]) -> list[int]:
    sizes = []
    for p in paths:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                tur = obj.get("toolUseResult")
                if tur and isinstance(tur, dict):
                    c = tur.get("content", "")
                    if isinstance(c, list):
                        c = json.dumps(c)
                    sizes.append(len(str(c).encode("utf-8")))
    return sizes


def render_metrics_md(agg: dict, date_str: str) -> str:
    return f"""# Claude Code 효율 지표 — {date_str}

## 세션 통계 (N={agg['session_count']})
- 총 tool 호출: {agg['total_tool_calls']}
- 총 tool 결과 바이트: {agg['total_tool_result_bytes']}
- 세션당 평균 tool 결과 바이트: {agg['mean_tool_result_bytes']:.1f}
- p50: {agg['p50_tool_result_bytes']}
- p95: {agg['p95_tool_result_bytes']}
- 평균 반복 호출율: {agg['mean_repeat_rate']:.4f}
- 손상 라인 총계: {agg['corrupt_lines_total']}

## 수식
- 비용 성장률 G = total_bytes / total_calls = {agg['mean_tool_result_bytes']:.4f}
- 재사용 손실 L = mean_repeat_rate = {agg['mean_repeat_rate']:.4f}
- 절감 여지 S = 1 - L = {1 - agg['mean_repeat_rate']:.4f}
"""


def render_hypotheses_md(agg: dict, date_str: str) -> str:
    return f"""# 돌파 가설 — {date_str}

## H1: tool 결과 부분 요청으로 누적 바이트 절감
- 관찰: p95={agg['p95_tool_result_bytes']} bytes
- 가설: Read offset/limit, Grep head_limit 기본 강제 → p95 대폭 감소
- 기대: G={agg['mean_tool_result_bytes']:.1f} → G/3

## H2: 동일 tool 반복 호출 제거
- 관찰: 반복율 L={agg['mean_repeat_rate']:.4f}
- 가설: harness 훅에서 (tool,args) 해시 캐싱 → L → 0
- 기대: 절감 여지 S={1 - agg['mean_repeat_rate']:.4f} 실현

## H3: 세션간 재탐색 제거로 시작 토큰 절감
- 관찰: 세션 시작마다 반복 Read 발생 (추정)
- 가설: SessionEnd 훅이 "읽은 파일 목록 + 결정사항" 요약을 다음 세션 주입
- 기대: 세션 첫 20턴 Read 호출 50% 감소
"""


def _cli():
    import argparse, datetime, os
    ap = argparse.ArgumentParser(description="Claude Code session log miner")
    default_proj = os.path.expanduser(
        "~/.claude-claude9/projects/-Users-ghost-Dev-nexus6"
    )
    ap.add_argument("--project", default=default_proj, help="session dir")
    ap.add_argument("--sessions", type=int, default=20, help="recent N sessions")
    ap.add_argument("--out-dir", default="shared/hypotheses/claude_efficiency")
    args = ap.parse_args()

    proj = Path(args.project)
    if not proj.exists():
        print(f"ERROR: project dir not found: {proj}", file=__import__("sys").stderr)
        raise SystemExit(2)

    jsonls = sorted(proj.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    jsonls = jsonls[: args.sessions]
    if not jsonls:
        print(f"ERROR: no .jsonl sessions found in {proj}", file=__import__("sys").stderr)
        raise SystemExit(3)

    agg = aggregate_sessions(jsonls)
    date_str = datetime.date.today().isoformat()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"metrics_{date_str}.md").write_text(
        render_metrics_md(agg, date_str), encoding="utf-8"
    )
    (out_dir / f"hypotheses_{date_str}.md").write_text(
        render_hypotheses_md(agg, date_str), encoding="utf-8"
    )
    print(f"miner: wrote metrics_{date_str}.md, hypotheses_{date_str}.md "
          f"(sessions={len(jsonls)}, calls={agg['total_tool_calls']}, "
          f"corrupt={agg['corrupt_lines_total']})")

if __name__ == "__main__":
    _cli()
