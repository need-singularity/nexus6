"""사이클 결과 JSON + discovery_log → 규칙 후보 md. 로컬만."""
import json
from pathlib import Path


def load_and_rank(
    breakthrough_json: Path, discovery_log: Path, min_strength: float = 0.5
) -> list[dict]:
    data = json.loads(Path(breakthrough_json).read_text(encoding="utf-8"))
    patterns = data.get("converged_patterns", [])
    notes_by_pattern: dict[str, str] = {}
    if Path(discovery_log).exists():
        for line in Path(discovery_log).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            pname = rec.get("pattern")
            if pname and "note" in rec:
                notes_by_pattern[pname] = rec["note"]
    filtered = [p for p in patterns if p.get("strength", 0) >= min_strength]
    filtered.sort(key=lambda p: p.get("strength", 0), reverse=True)
    for p in filtered:
        if p["name"] in notes_by_pattern:
            p["note"] = notes_by_pattern[p["name"]]
    return filtered
