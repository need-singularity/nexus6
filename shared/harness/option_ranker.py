#!/usr/bin/env python3
# @hexa-first-exempt — JSONL tail + multi-pattern regex scoring. hexa 에 regex 라이브러리 부재로 Python 유지.
# option_ranker.py — extract A/B/C or 1/2/3 options from last assistant message, score by rubric, pick top.
#
# Called by option_gate.hexa (UserPromptSubmit hook). Stays out of the way when:
#   - transcript has no recent options
#   - trigger doesn't match a known pick intent
#
# Contract:
#   argv[1] = normalized prompt trigger (e.g. "go", "a", "2", "keep")
#   argv[2] = absolute path to the session transcript JSONL
# stdout  = context-injection block wrapped in <user-prompt-submit-hook>...</user-prompt-submit-hook>
#           OR empty when nothing to inject (silent pass)
# exit 0  always (hook should never block)
#
# Scoring rubric (higher = preferred):
#   +6  근본 원인 / root cause keywords
#   +5  pitfall-closing reference (VP-\d+, VD-\d+, VC-\d+)
#   +4  concrete file path / line number (src/*, .hexa, .m, .c, :123)
#   +4  AI-native keywords (ml, probabilistic, adaptive, self-*, auto-*)
#   +3  small / reversible patch (작은, patch, single, small)
#   +2  reversible / rollback hint
#   -5  "ask user" / 알려주면 / 물어봐 — defers decision
#   -3  log-first / dump-first / 먼저 로그 / 먼저 확인
#   -3  investigate-only / 조사 / 알아보 / TBD
#   -2  defer / 나중 / 보류
#
# Trigger handling:
#   - "go" / "keep" / "가자" → pick rank 1
#   - "a"/"b"/... or "1"/"2"/... → pick that labeled option if it exists, else rank 1

import json
import os
import re
import sys


ROOT_CAUSE_PAT = re.compile(
    r"(근본\s*원인|root[-\s]*cause|원인\s*해결|구조적|root[-\s]*fix|fix.*root|structural)",
    re.IGNORECASE,
)
PITFALL_PAT = re.compile(r"\b(V[PDC]-\d+|pitfall|함정)\b", re.IGNORECASE)
CONCRETE_PAT = re.compile(
    r"(src/[\w./-]+|[\w-]+\.(?:hexa|m|c|h|py|sh|json|ts|tsx|js)|:\d{1,5}\b|line\s*\d+)",
    re.IGNORECASE,
)
AI_NATIVE_PAT = re.compile(
    r"(ai[-\s]*native|\bml\b|probabilistic|adaptive|self[-\s]\w+|auto[-\s]\w+|heuristic|learned|neural|embedding|scoring|ranker|rubric)",
    re.IGNORECASE,
)
SMALL_PAT = re.compile(r"(작은|small\s+patch|single[-\s]file|single[-\s]line|minimal|trivial|one[-\s]liner|단일)", re.IGNORECASE)
REVERSIBLE_PAT = re.compile(r"(reversible|rollback|되돌릴|revert)", re.IGNORECASE)

ASK_USER_PAT = re.compile(r"(알려주(면|세요)|물어보|확인\s*요청|ask\s+user|user\s+confirm|please\s+provide)", re.IGNORECASE)
LOG_FIRST_PAT = re.compile(r"(먼저\s*로그|log[-\s]*first|dump[-\s]*first|먼저\s*확인|디버그\s*출력|trace[-\s]*first)", re.IGNORECASE)
INVESTIGATE_PAT = re.compile(r"(investigate\s+only|조사만|알아보|TBD|나중에\s*결정|defer\s+decision)", re.IGNORECASE)
DEFER_PAT = re.compile(r"(defer|나중|보류|postpone|later)", re.IGNORECASE)


def read_last_assistant_text(transcript_path: str) -> str:
    """Tail the JSONL transcript and return the text of the most recent assistant message."""
    try:
        size = os.path.getsize(transcript_path)
    except OSError:
        return ""
    # Read last ~2 MB — enough for a few recent turns
    read_from = max(0, size - 2 * 1024 * 1024)
    try:
        with open(transcript_path, "rb") as fh:
            fh.seek(read_from)
            blob = fh.read().decode("utf-8", errors="replace")
    except OSError:
        return ""
    lines = blob.splitlines()
    last_text = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = rec.get("message") or {}
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content")
        parts = []
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text":
                    parts.append(c.get("text", ""))
        joined = "\n".join(p for p in parts if p)
        if joined.strip():
            last_text = joined
    return last_text


OPTION_PATTERNS = [
    # - **A**: body   /   - **A** — body
    re.compile(
        r"^\s*(?:[-*]\s+)?\*\*([A-Ea-e])\*\*\s*[:\-–—)]\s*(.+?)(?=\n\s*(?:[-*]\s+)?\*\*[A-Ea-e]\*\*\s*[:\-–—)]|\n\s*(?:[-*]\s+)?\*\*\d+\*\*\s*[:\-–—)]|\n\s*다음|\n\s*어느|\n\s*추천|\n{2,}|\Z)",
        re.MULTILINE | re.DOTALL,
    ),
    # - A: body    - A) body
    re.compile(
        r"^\s*[-*]\s+([A-Ea-e])\s*[:\)]\s*(.+?)(?=\n\s*[-*]\s+[A-Ea-e]\s*[:\)]|\n\s*[-*]\s+\d+\s*[:\)]|\n\s*다음|\n\s*어느|\n\s*추천|\n{2,}|\Z)",
        re.MULTILINE | re.DOTALL,
    ),
    # 1. body  /  2. body
    re.compile(
        r"^\s*(\d+)\.\s+(.+?)(?=\n\s*\d+\.\s+|\n\s*다음|\n\s*어느|\n\s*추천|\n{2,}|\Z)",
        re.MULTILINE | re.DOTALL,
    ),
    # - 1) body
    re.compile(
        r"^\s*[-*]\s+(\d+)\s*[:\)]\s*(.+?)(?=\n\s*[-*]\s+\d+\s*[:\)]|\n{2,}|\Z)",
        re.MULTILINE | re.DOTALL,
    ),
]


def extract_options(asst_text: str):
    """Return a list of (label, text) tuples, picking the pattern with the most matches."""
    best = []
    for pat in OPTION_PATTERNS:
        matches = pat.findall(asst_text)
        cleaned = []
        for label, body in matches:
            body = body.strip()
            if not body:
                continue
            cleaned.append((label.upper(), body))
        if len(cleaned) > len(best):
            best = cleaned
    # Deduplicate by label (keep first occurrence — closer to top = newer in transcript order)
    seen = set()
    deduped = []
    for lab, body in best:
        if lab in seen:
            continue
        seen.add(lab)
        deduped.append((lab, body))
    return deduped


def score_option(text: str) -> tuple[int, list[str]]:
    score = 0
    reasons = []

    def add(delta: int, label: str):
        nonlocal score
        score += delta
        reasons.append(f"{'+' if delta >= 0 else ''}{delta} {label}")

    if ROOT_CAUSE_PAT.search(text):
        add(6, "root-cause")
    if PITFALL_PAT.search(text):
        add(5, "pitfall-closing")
    if CONCRETE_PAT.search(text):
        add(4, "concrete-file")
    if AI_NATIVE_PAT.search(text):
        add(4, "ai-native")
    if SMALL_PAT.search(text):
        add(3, "small-patch")
    if REVERSIBLE_PAT.search(text):
        add(2, "reversible")

    if ASK_USER_PAT.search(text):
        add(-5, "ask-user")
    if LOG_FIRST_PAT.search(text):
        add(-3, "log-first")
    if INVESTIGATE_PAT.search(text):
        add(-3, "investigate-only")
    if DEFER_PAT.search(text):
        add(-2, "defer")

    return score, reasons


AUTO_GO_TRIGGERS = {"go", "가자", "keep", "keep going", "keep going no talking", "ㄱㄱ"}
LETTER_TRIGGERS = set("abcde")
NUMBER_TRIGGERS = set("12345")
KOREAN_ORDINALS = {
    "첫번째": "1",
    "첫 번째": "1",
    "일번": "1",
    "두번째": "2",
    "두 번째": "2",
    "이번": "2",
    "세번째": "3",
    "세 번째": "3",
    "삼번": "3",
    "네번째": "4",
    "다섯번째": "5",
}


def interpret_trigger(raw: str):
    """Return ('auto', None) | ('letter', 'A'..'E') | ('number', '1'..'5') | (None, None)"""
    t = raw.strip().lower()
    if not t:
        return (None, None)
    if t in AUTO_GO_TRIGGERS or t.startswith("go "):
        return ("auto", None)
    # single letter
    if len(t) == 1 and t in LETTER_TRIGGERS:
        return ("letter", t.upper())
    if len(t) == 1 and t in NUMBER_TRIGGERS:
        return ("number", t)
    if t in KOREAN_ORDINALS:
        return ("number", KOREAN_ORDINALS[t])
    # prefix forms like "A로 가자", "2로 해", "option A"
    m = re.match(r"^(?:option\s+)?([a-eA-E])\b", t)
    if m:
        return ("letter", m.group(1).upper())
    m = re.match(r"^([1-5])\s*(?:번|로)?\b", t)
    if m:
        return ("number", m.group(1))
    return (None, None)


LETTER_TO_NUM = {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"}
NUM_TO_LETTER = {v: k for k, v in LETTER_TO_NUM.items()}


def pick(ranked, kind, key):
    if not ranked:
        return None
    if kind == "auto":
        return ranked[0]
    # Build label set to detect labeling style
    labels = {r["label"] for r in ranked}
    use_letters = bool(labels & set(LETTER_TO_NUM.keys()))
    use_numbers = bool(labels & set(NUM_TO_LETTER.keys()))
    if kind == "letter":
        target = key
        if not use_letters and use_numbers:
            target = LETTER_TO_NUM.get(key, key)
        for row in ranked:
            if row["label"] == target:
                return row
    if kind == "number":
        target = key
        if not use_numbers and use_letters:
            target = NUM_TO_LETTER.get(key, key)
        for row in ranked:
            if row["label"] == target:
                return row
    # No direct match — fall back to rank 1
    return ranked[0]


def main():
    if len(sys.argv) < 3:
        return
    raw_trigger = sys.argv[1]
    transcript = sys.argv[2]

    kind, key = interpret_trigger(raw_trigger)
    if kind is None:
        return
    if not os.path.isfile(transcript):
        return

    asst = read_last_assistant_text(transcript)
    if not asst:
        return

    opts = extract_options(asst)
    if len(opts) < 2:
        return  # need at least two options to be worth auto-picking

    # Score + sort by score desc, then by original position
    ranked = []
    for idx, (label, text) in enumerate(opts):
        score, reasons = score_option(text)
        ranked.append(
            {
                "label": label,
                "text": text,
                "score": score,
                "reasons": reasons,
                "order": idx,
            }
        )
    ranked.sort(key=lambda r: (-r["score"], r["order"]))

    chosen = pick(ranked, kind, key)
    if not chosen:
        return

    # Compact body
    body = chosen["text"].strip()
    if len(body) > 600:
        body = body[:600] + " …"

    reason_line = ", ".join(chosen["reasons"]) if chosen["reasons"] else "no-signal"
    rank_preview = " | ".join(f"{r['label']}={r['score']}" for r in ranked[:5])

    print("<user-prompt-submit-hook>")
    print(f"[OPTION-GATE] SELECTED: {chosen['label']} (score={chosen['score']})")
    print(f"  why: {reason_line}")
    print(f"  ranks: {rank_preview}")
    print("")
    print("강제:")
    print("  1. 확인 질문 금지 — 즉시 실행")
    print("  2. 다른 옵션 언급 금지")
    print("  3. 루트 원인 해결 우선, 피할 수 없으면 명시")
    print("")
    print("선택된 액션:")
    print(body)
    print("</user-prompt-submit-hook>")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Hooks must never block — swallow errors
        pass
