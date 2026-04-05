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


_RULE_TEMPLATES = {
    "reuse_dominance": (
        "동일 (tool, args) 호출이 세션 내 반복될 경우 두 번째 호출부터 "
        "결과를 재인용하거나 더 좁은 범위(Grep/offset)로 대체하라."
    ),
    "size_concentration": (
        "Read/Bash 결과가 큰 바이트에 집중되는 경향 확인. 파일 크기 미지 시 "
        "먼저 head 100줄 또는 Grep으로 좁힌 뒤 필요 영역만 offset으로 읽어라."
    ),
    "session_reexploration": (
        "세션 시작 직후 이전 세션에서 이미 열었던 파일을 재Read하는 패턴. "
        "SessionStart에서 메모리/핸드오프 파일을 먼저 확인하고 중복 Read를 피하라."
    ),
}

_counter = {"n": 0}


def translate_to_rule(pattern: dict, source_hypothesis: str) -> dict:
    _counter["n"] += 1
    rid = f"R{_counter['n']}"
    name = pattern.get("name", "unknown")
    text = _RULE_TEMPLATES.get(
        name, f"(템플릿 미등록) 패턴 {name}에 대해 사람 검토 필요."
    )
    consts = pattern.get("constants_matched") or []
    rationale = (
        f"pattern={name} strength={pattern.get('strength', 0):.2f} "
        f"constants={','.join(consts) or '-'}"
    )
    if "note" in pattern:
        rationale += f" note={pattern['note']}"
    return {
        "id": rid,
        "text": text,
        "source": source_hypothesis,
        "rationale": rationale,
    }


def reset_rule_counter():
    _counter["n"] = 0


def render_rules_md(rules: list[dict], date_str: str) -> str:
    if not rules:
        return f"""# 도출 규칙 후보 — {date_str}

**패턴 없음** — 사이클 수렴 실패 또는 min_strength 미달. 가설 재설계 권장.
"""
    body = [f"# 도출 규칙 후보 — {date_str}", ""]
    for r in rules:
        body.append(f"## {r['id']}: (from {r['source']})")
        body.append(r["text"])
        body.append(f"- rationale: `{r['rationale']}`")
        body.append("")
    return "\n".join(body)

def _cli():
    import argparse, datetime, sys
    ap = argparse.ArgumentParser(description="Cycle breakthrough interpreter")
    ap.add_argument("breakthrough_json", help="path to cycle output JSON")
    ap.add_argument(
        "--discovery", default="shared/discovery_log.jsonl",
        help="discovery_log.jsonl path",
    )
    ap.add_argument(
        "--out-dir", default="shared/breakthroughs",
        help="rules md output dir",
    )
    ap.add_argument("--min-strength", type=float, default=0.5)
    args = ap.parse_args()

    bj = Path(args.breakthrough_json)
    if not bj.exists():
        print(f"ERROR: breakthrough JSON not found: {bj}", file=sys.stderr)
        raise SystemExit(2)

    ranked = load_and_rank(bj, Path(args.discovery), args.min_strength)
    try:
        raw = json.loads(bj.read_text(encoding="utf-8"))
        surviving = raw.get("surviving_hypotheses", [])
    except Exception:
        surviving = []
    rules = []
    reset_rule_counter()
    for i, p in enumerate(ranked):
        src = surviving[i] if i < len(surviving) else "H?"
        rules.append(translate_to_rule(p, source_hypothesis=src))

    date_str = datetime.date.today().isoformat()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"claude_efficiency_rules_{date_str}.md"
    out_path.write_text(render_rules_md(rules, date_str), encoding="utf-8")
    print(f"interpreter: wrote {out_path} (rules={len(rules)})")

if __name__ == "__main__":
    _cli()
