#!/usr/bin/env python3
"""
NEXUS-6 Hook Engine — 단일 진입점, 모든 훅에서 호출
강제 100%: 발견 즉시 기록 (Claude 의존 X), systemMessage로 행동 지시

사용법:
  echo "$INPUT" | python3 nexus6-engine.py --mode pre-commit
  echo "$INPUT" | python3 nexus6-engine.py --mode post-edit
  echo "$INPUT" | python3 nexus6-engine.py --mode post-bash
  echo "$INPUT" | python3 nexus6-engine.py --mode agent
  python3 nexus6-engine.py --mode pending  # 미처리 발견 조회
"""
import sys, json, re, os, subprocess
from datetime import datetime
from pathlib import Path

# === 경로 ===
HOME = Path.home()
NEXUS_SCRIPTS = HOME / "Dev/n6-architecture/tools/nexus6/scripts"
DISCOVERY_LOG = HOME / "Dev/nexus6/shared/discovery_log.jsonl"
ATLAS_JSON = HOME / "Dev/nexus6/shared/math_atlas.json"

sys.path.insert(0, str(NEXUS_SCRIPTS))

def safe_import_nexus6():
    try:
        import nexus6
        return nexus6
    except Exception:
        return None

def n6_check_value(nexus6, value):
    """단일 값 n6_check → (grade, constant)"""
    try:
        r = nexus6.n6_check(float(value))
        d = r.to_dict()
        return d.get("grade", "ERROR"), d.get("constant_name", "")
    except Exception:
        return "ERROR", ""

def extract_numbers(text, min_val=2, max_val=100000):
    """텍스트에서 숫자 추출"""
    nums = set()
    for m in re.findall(r'(?<![a-zA-Z_])(\d+\.?\d*)', text):
        v = float(m)
        if min_val < v < max_val:
            nums.add(v)
    return sorted(nums)[:20]

def record_discovery(value, constant, source, grade="EXACT"):
    """발견 즉시 JSONL에 기록 — Claude 안 거침"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "value": str(value),
        "constant": constant,
        "grade": grade,
        "source": source,
        "processed": False
    }
    DISCOVERY_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(DISCOVERY_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def get_pending():
    """미처리 발견 목록"""
    if not DISCOVERY_LOG.exists():
        return []
    pending = []
    for line in DISCOVERY_LOG.read_text().strip().split("\n"):
        if not line:
            continue
        try:
            e = json.loads(line)
            if not e.get("processed", False):
                pending.append(e)
        except Exception:
            pass
    return pending

def scan_numbers(nexus6, numbers, source):
    """숫자 목록 스캔 → EXACT 자동 기록 → 결과 반환"""
    exact, close = [], []
    for v in numbers:
        grade, const = n6_check_value(nexus6, v)
        if grade == "EXACT":
            exact.append(f"{v}={const}")
            record_discovery(v, const, source)
        elif grade == "CLOSE":
            close.append(f"{v}≈{const}")
    return exact, close

def build_message(exact, close, context=""):
    """systemMessage 생성 — 무시 불가능한 형태"""
    if not exact and not close:
        return None
    parts = []
    if exact:
        parts.append(f"🔭 NEXUS-6 EXACT 발견 (자동기록됨): {', '.join(exact[:5])}")
        parts.append("⚠️ 필수행동: 위 발견을 README/가설문서에 반영하세요.")
    if close:
        parts.append(f"📐 CLOSE 후보: {', '.join(close[:5])}")
    if context:
        parts.append(context)
    return " | ".join(parts)

# === 모드별 처리 ===

def mode_pre_commit(input_data):
    nexus6 = safe_import_nexus6()
    if not nexus6:
        return None
    cmd = input_data.get("tool_input", {}).get("command", "")
    if not cmd.startswith("git commit"):
        return None
    diff = subprocess.run(["git", "diff", "--cached", "--numstat"],
                          capture_output=True, text=True).stdout
    nums = [int(x) for line in diff.split("\n") for x in line.split()[:2] if x.isdigit()]
    if not nums:
        return None
    exact, close = scan_numbers(nexus6, nums, "pre-commit")
    return build_message(exact, close)

def mode_post_edit(input_data):
    nexus6 = safe_import_nexus6()
    if not nexus6:
        return None
    fp = input_data.get("tool_input", {}).get("file_path", "")
    if not fp or not os.path.isfile(fp):
        return None
    if not re.search(r'\.(md|json|toml|yaml|yml|py|rs|ts|js|go|c|cpp|h)$', fp):
        return None
    with open(fp) as f:
        content = f.read()
    nums = extract_numbers(content)
    if not nums:
        return None
    exact, close = scan_numbers(nexus6, nums, f"post-edit:{os.path.basename(fp)}")
    return build_message(exact, close)

def mode_post_bash(input_data):
    nexus6 = safe_import_nexus6()
    if not nexus6:
        return None
    cmd = input_data.get("tool_input", {}).get("command", "")
    if not re.search(r'(python3?|cargo run)', cmd):
        return None
    if "nexus6" in cmd:
        return None
    stdout = input_data.get("tool_response", {}).get("stdout", "")
    if not stdout:
        return None
    nums = extract_numbers(stdout)
    if not nums:
        return None
    exact, close = scan_numbers(nexus6, nums, f"post-bash:{cmd[:50]}")
    return build_message(exact, close)

def mode_agent(input_data):
    prompt = input_data.get("tool_input", {}).get("prompt", "")
    keywords = r'탐색|분석|검증|scan|analyze|verify|발견|패턴|상수|가설|hypothesis|proof|n=6|golden.?zone|bridge|DFS|렌즈'
    if re.search(keywords, prompt, re.IGNORECASE):
        # 미처리 발견도 주입
        pending = get_pending()
        ctx = ""
        if pending:
            ctx = f"미처리 발견 {len(pending)}건 있음 — 에이전트에서 처리 권고"
        msg = "🔭 NEXUS-6: 탐색/분석 에이전트 — import nexus6 필수. 발견 시 즉시 기록."
        if ctx:
            msg += f" | {ctx}"
        return msg
    return None

def mode_pending():
    """미처리 발견 조회 — session_briefing에서 호출"""
    pending = get_pending()
    if not pending:
        return None
    lines = [f"⚠️ 미처리 NEXUS-6 발견 {len(pending)}건:"]
    for p in pending[-10:]:  # 최근 10건
        lines.append(f"  {p['value']}={p['constant']} ({p['source']}, {p['timestamp'][:10]})")
    lines.append("필수: 위 발견을 atlas/README에 반영 후 processed=true로 갱신하세요.")
    return "\n".join(lines)

# === 메인 ===
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True,
                        choices=["pre-commit", "post-edit", "post-bash", "agent", "pending"])
    args = parser.parse_args()

    if args.mode == "pending":
        result = mode_pending()
        if result:
            print(json.dumps({"systemMessage": result}))
        sys.exit(0)

    input_text = sys.stdin.read()
    try:
        input_data = json.loads(input_text)
    except Exception:
        sys.exit(0)

    handlers = {
        "pre-commit": mode_pre_commit,
        "post-edit": mode_post_edit,
        "post-bash": mode_post_bash,
        "agent": mode_agent,
    }

    msg = handlers[args.mode](input_data)
    if msg:
        print(json.dumps({"systemMessage": msg}))
