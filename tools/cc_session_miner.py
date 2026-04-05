"""Claude Code 세션 JSONL 마이너 — 로컬 처리만, 외부 API 호출 없음."""
import json
from pathlib import Path

def parse_session(jsonl_path: Path) -> dict:
    """세션 JSONL 한 개 파싱해 tool 결과 지표 반환."""
    tool_call_count = 0
    tool_result_bytes_total = 0
    tool_result_bytes_max = 0
    corrupt_lines = 0

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

    return {
        "tool_call_count": tool_call_count,
        "tool_result_bytes_total": tool_result_bytes_total,
        "tool_result_bytes_max": tool_result_bytes_max,
        "corrupt_lines": corrupt_lines,
    }
