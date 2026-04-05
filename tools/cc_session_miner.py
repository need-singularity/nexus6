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
            if tur:
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
                if tur:
                    c = tur.get("content", "")
                    if isinstance(c, list):
                        c = json.dumps(c)
                    sizes.append(len(str(c).encode("utf-8")))
    return sizes
