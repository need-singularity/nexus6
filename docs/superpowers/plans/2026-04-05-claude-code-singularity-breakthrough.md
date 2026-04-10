# Claude Code 효율 특이점 돌파 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Claude Code CLI 세션 로그를 nexus 특이점 사이클 메타 도메인 `claude_efficiency`에 돌려, 입력 토큰 절감 + 세션간 지식 공유 돌파 패턴을 CLAUDE.md 규칙 후보로 번역하는 로컬 파이프라인 구축.

**Architecture:** 5개 컴포넌트 단방향 파이프라인. Python 마이너가 세션 JSONL → 지표/가설 `.md` 생성 → watch-atlas 자동 스캔 → nexus auto 사이클 → 해석기가 규칙 후보 `.md` 출력 → 사람이 CLAUDE.md에 수동 병합. 외부 API 호출 0건, 표준 라이브러리만 사용.

**Tech Stack:** Python 3 (stdlib만: `json`, `pathlib`, `hashlib`, `argparse`, `collections`), Bash, 기존 nexus CLI, 기존 watch-atlas 인프라.

**Spec**: `docs/superpowers/specs/2026-04-05-claude-code-singularity-breakthrough-design.md`

---

## File Structure

**신규**:
- `tools/cc_session_miner.py` — 세션 JSONL 파서 + 지표/가설 .md 생성 (C1)
- `tools/interpret_breakthrough.py` — 사이클 결과 → 규칙 후보 번역 (C4)
- `tools/run_cc_breakthrough.sh` — 전 파이프라인 래퍼 (C3)
- `tools/tests/__init__.py`
- `tools/tests/test_cc_session_miner.py` — unittest
- `tools/tests/test_interpret_breakthrough.py` — unittest
- `tools/tests/fixtures/sample_session.jsonl` — 정상 JSONL 픽스처
- `tools/tests/fixtures/corrupt_session.jsonl` — 손상 라인 포함 픽스처
- `tools/tests/fixtures/sample_breakthrough.json` — 사이클 결과 픽스처
- `tools/tests/fixtures/sample_discovery.jsonl` — discovery_log 픽스처
- `shared/hypotheses/claude_efficiency/.gitkeep`
- `shared/breakthroughs/.gitkeep`

**수정**:
- `shared/config/projects.json` — `claude_efficiency` 엔트리 추가 (C2)

---

### Task 1: 디렉토리 뼈대 + .gitkeep 배치

**Files:**
- Create: `shared/hypotheses/claude_efficiency/.gitkeep`
- Create: `shared/breakthroughs/.gitkeep`
- Create: `tools/tests/__init__.py`
- Create: `tools/tests/fixtures/.gitkeep`

- [ ] **Step 1: 디렉토리 생성**

```bash
mkdir -p shared/hypotheses/claude_efficiency
mkdir -p shared/breakthroughs
mkdir -p tools/tests/fixtures
touch shared/hypotheses/claude_efficiency/.gitkeep
touch shared/breakthroughs/.gitkeep
touch tools/tests/fixtures/.gitkeep
touch tools/tests/__init__.py
```

- [ ] **Step 2: 확인**

```bash
ls shared/hypotheses/claude_efficiency/ shared/breakthroughs/ tools/tests/
```
Expected: `.gitkeep` 파일들 + `__init__.py` 보임

- [ ] **Step 3: Commit**

```bash
git add shared/hypotheses/claude_efficiency/.gitkeep shared/breakthroughs/.gitkeep tools/tests/__init__.py tools/tests/fixtures/.gitkeep
git commit -m "chore: scaffold dirs for claude_efficiency cycle pipeline"
```

---

### Task 2: JSONL 픽스처 작성

**Files:**
- Create: `tools/tests/fixtures/sample_session.jsonl`
- Create: `tools/tests/fixtures/corrupt_session.jsonl`

Claude Code 세션 JSONL은 한 라인당 하나의 메시지 이벤트. 우리가 관심있는 최소 스키마:
- `type`: "user" | "assistant" | ...
- `timestamp`: ISO8601
- `message.content[]`: assistant의 경우 tool_use 블록 포함
- `toolUseResult`: 별도 tool 결과 이벤트

실제 세션 샘플을 단순화한 픽스처를 만든다.

- [ ] **Step 1: sample_session.jsonl 작성**

`tools/tests/fixtures/sample_session.jsonl` 내용:
```jsonl
{"type":"user","timestamp":"2026-04-05T10:00:00Z","message":{"role":"user","content":"read foo.py"}}
{"type":"assistant","timestamp":"2026-04-05T10:00:05Z","message":{"role":"assistant","content":[{"type":"tool_use","id":"t1","name":"Read","input":{"file_path":"/repo/foo.py"}}]}}
{"type":"user","timestamp":"2026-04-05T10:00:06Z","toolUseResult":{"tool_use_id":"t1","content":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"}}
{"type":"assistant","timestamp":"2026-04-05T10:00:10Z","message":{"role":"assistant","content":[{"type":"tool_use","id":"t2","name":"Read","input":{"file_path":"/repo/foo.py"}}]}}
{"type":"user","timestamp":"2026-04-05T10:00:11Z","toolUseResult":{"tool_use_id":"t2","content":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"}}
{"type":"assistant","timestamp":"2026-04-05T10:00:15Z","message":{"role":"assistant","content":[{"type":"tool_use","id":"t3","name":"Grep","input":{"pattern":"foo"}}]}}
{"type":"user","timestamp":"2026-04-05T10:00:16Z","toolUseResult":{"tool_use_id":"t3","content":"match1\nmatch2"}}
```

5개 tool 호출: Read(foo.py) 2회 반복, Grep 1회. 반복율 = 1/3 (중복 1, 총 3).

- [ ] **Step 2: corrupt_session.jsonl 작성**

`tools/tests/fixtures/corrupt_session.jsonl` 내용:
```jsonl
{"type":"user","timestamp":"2026-04-05T10:00:00Z","message":{"role":"user","content":"hi"}}
{this is not valid json
{"type":"assistant","timestamp":"2026-04-05T10:00:05Z","message":{"role":"assistant","content":[{"type":"tool_use","id":"t1","name":"Read","input":{"file_path":"/repo/bar.py"}}]}}
{"type":"user","timestamp":"2026-04-05T10:00:06Z","toolUseResult":{"tool_use_id":"t1","content":"BBBB"}}
```

1 손상 라인 + 3 정상 라인.

- [ ] **Step 3: Commit**

```bash
git add tools/tests/fixtures/sample_session.jsonl tools/tests/fixtures/corrupt_session.jsonl
git commit -m "test: add session JSONL fixtures for miner tests"
```

---

### Task 3: 마이너 — 세션 파싱 + 크기 집계 (TDD)

**Files:**
- Create: `tools/cc_session_miner.py`
- Create: `tools/tests/test_cc_session_miner.py`

- [ ] **Step 1: 실패 테스트 작성**

`tools/tests/test_cc_session_miner.py`:
```python
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cc_session_miner import parse_session

FIX = Path(__file__).parent / "fixtures"

class TestParseSession(unittest.TestCase):
    def test_parses_sample_session(self):
        result = parse_session(FIX / "sample_session.jsonl")
        # 3 tool calls, tool result bytes summed
        self.assertEqual(result["tool_call_count"], 3)
        # First result: 32 chars, second: 32, third: "match1\nmatch2" = 13
        self.assertEqual(result["tool_result_bytes_total"], 32 + 32 + 13)
        self.assertEqual(result["tool_result_bytes_max"], 32)

    def test_skips_corrupt_lines(self):
        result = parse_session(FIX / "corrupt_session.jsonl")
        # 1 tool call survives
        self.assertEqual(result["tool_call_count"], 1)
        self.assertEqual(result["corrupt_lines"], 1)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
python3 -m unittest tools.tests.test_cc_session_miner -v
```
Expected: FAIL (ModuleNotFoundError: cc_session_miner)

- [ ] **Step 3: 최소 구현**

`tools/cc_session_miner.py`:
```python
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
                    # content가 블록 리스트인 경우
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
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
python3 -m unittest tools.tests.test_cc_session_miner -v
```
Expected: 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tools/cc_session_miner.py tools/tests/test_cc_session_miner.py
git commit -m "feat(miner): parse session JSONL + aggregate tool result sizes"
```

---

### Task 4: 마이너 — 반복 호출율 계산 (TDD)

**Files:**
- Modify: `tools/cc_session_miner.py`
- Modify: `tools/tests/test_cc_session_miner.py`

반복 호출 = 같은 세션 내 동일 `(tool_name, input_hash)` 재등장.

- [ ] **Step 1: 실패 테스트 추가**

`tools/tests/test_cc_session_miner.py` 끝에 메서드 추가:
```python
    def test_repeat_call_rate(self):
        result = parse_session(FIX / "sample_session.jsonl")
        # 3 calls, 2 unique (Read foo.py, Grep foo) → repeat rate = (3-2)/3 = 1/3
        self.assertEqual(result["unique_calls"], 2)
        self.assertAlmostEqual(result["repeat_rate"], 1/3, places=5)
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
python3 -m unittest tools.tests.test_cc_session_miner.TestParseSession.test_repeat_call_rate -v
```
Expected: FAIL (KeyError: 'unique_calls')

- [ ] **Step 3: 구현 추가**

`tools/cc_session_miner.py`의 `parse_session`을 다음으로 교체:
```python
import hashlib

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
```

- [ ] **Step 4: 전 테스트 통과 확인**

```bash
python3 -m unittest tools.tests.test_cc_session_miner -v
```
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tools/cc_session_miner.py tools/tests/test_cc_session_miner.py
git commit -m "feat(miner): compute repeat call rate from tool_use signatures"
```

---

### Task 5: 마이너 — 다중 세션 집계 + CLI (TDD)

**Files:**
- Modify: `tools/cc_session_miner.py`
- Modify: `tools/tests/test_cc_session_miner.py`

여러 세션 JSONL을 디렉토리에서 찾아 mtime 기준 최근 N개만 집계.

- [ ] **Step 1: 실패 테스트 추가**

`tools/tests/test_cc_session_miner.py` 끝에:
```python
    def test_aggregate_sessions(self):
        from cc_session_miner import aggregate_sessions
        # 픽스처 2개 (sample, corrupt)를 모두 사용
        result = aggregate_sessions([FIX / "sample_session.jsonl", FIX / "corrupt_session.jsonl"])
        # sample: 3 calls, corrupt: 1 call → 4 total
        self.assertEqual(result["total_tool_calls"], 4)
        self.assertEqual(result["session_count"], 2)
        self.assertIn("mean_tool_result_bytes", result)
        self.assertIn("p95_tool_result_bytes", result)
```

- [ ] **Step 2: 실패 확인**

```bash
python3 -m unittest tools.tests.test_cc_session_miner.TestParseSession.test_aggregate_sessions -v
```
Expected: FAIL (ImportError: aggregate_sessions)

- [ ] **Step 3: 구현**

`tools/cc_session_miner.py` 끝에 추가:
```python
from typing import Iterable

def aggregate_sessions(paths: Iterable[Path]) -> dict:
    """여러 세션 JSONL을 집계."""
    paths = list(paths)
    per_session = [parse_session(p) for p in paths]
    total_calls = sum(s["tool_call_count"] for s in per_session)
    total_bytes = sum(s["tool_result_bytes_total"] for s in per_session)
    # per-result sizes를 재수집하기 위해 다시 스캔 (p95 위해)
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
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
python3 -m unittest tools.tests.test_cc_session_miner -v
```
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tools/cc_session_miner.py tools/tests/test_cc_session_miner.py
git commit -m "feat(miner): aggregate metrics across sessions with p50/p95"
```

---

### Task 6: 마이너 — metrics.md + hypotheses.md 출력 (TDD)

**Files:**
- Modify: `tools/cc_session_miner.py`
- Modify: `tools/tests/test_cc_session_miner.py`

- [ ] **Step 1: 실패 테스트 추가**

`tools/tests/test_cc_session_miner.py` 끝에:
```python
    def test_render_metrics_md(self):
        from cc_session_miner import render_metrics_md, render_hypotheses_md
        agg = {
            "session_count": 2, "total_tool_calls": 4,
            "total_tool_result_bytes": 109, "mean_tool_result_bytes": 27.25,
            "p50_tool_result_bytes": 32, "p95_tool_result_bytes": 32,
            "mean_repeat_rate": 0.167, "corrupt_lines_total": 1,
        }
        md = render_metrics_md(agg, date_str="2026-04-05")
        self.assertIn("# Claude Code 효율 지표", md)
        self.assertIn("2026-04-05", md)
        self.assertIn("p95", md)
        self.assertIn("세션당", md)
        # 수식 섹션 (atlas 스캔용)
        self.assertIn("##", md)
        self.assertIn("=", md)  # 수식은 = 포함

        hyp = render_hypotheses_md(agg, date_str="2026-04-05")
        self.assertIn("# 돌파 가설", hyp)
        self.assertIn("H1", hyp)
```

- [ ] **Step 2: 실패 확인**

```bash
python3 -m unittest tools.tests.test_cc_session_miner.TestParseSession.test_render_metrics_md -v
```
Expected: FAIL (ImportError)

- [ ] **Step 3: 구현**

`tools/cc_session_miner.py` 끝에 추가:
```python
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
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
python3 -m unittest tools.tests.test_cc_session_miner -v
```
Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tools/cc_session_miner.py tools/tests/test_cc_session_miner.py
git commit -m "feat(miner): render metrics.md + hypotheses.md for atlas scan"
```

---

### Task 7: 마이너 — CLI entry point

**Files:**
- Modify: `tools/cc_session_miner.py`

- [ ] **Step 1: CLI 추가**

`tools/cc_session_miner.py` 끝에 추가:
```python
def _cli():
    import argparse, datetime, os
    ap = argparse.ArgumentParser(description="Claude Code session log miner")
    default_proj = os.path.expanduser(
        "~/.claude-claude9/projects/-Users-ghost-Dev-nexus"
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
```

- [ ] **Step 2: 실제 실행으로 스모크 테스트**

```bash
python3 tools/cc_session_miner.py --sessions 5
```
Expected: `miner: wrote metrics_2026-04-05.md, hypotheses_2026-04-05.md (sessions=5, calls=..., corrupt=...)` — 에러 없이 완료

- [ ] **Step 3: 출력 확인**

```bash
ls shared/hypotheses/claude_efficiency/ && head -20 shared/hypotheses/claude_efficiency/metrics_*.md
```
Expected: 두 .md 파일 생성됨, 지표 섹션 보임

- [ ] **Step 4: Commit**

```bash
git add tools/cc_session_miner.py
git commit -m "feat(miner): add CLI entry point with session glob + output write"
```

---

### Task 8: projects.json에 claude_efficiency 엔트리 추가

**Files:**
- Modify: `shared/config/projects.json`

- [ ] **Step 1: 엔트리 추가**

기존 `projects` 딕셔너리에 `claude_efficiency` 키를 추가 (Edit 도구 사용). 기존 엔트리 예시(TECS-L)를 참고해 구조 맞춤:

`shared/config/projects.json`의 `"projects": { ... }` 블록 끝에 추가할 내용:
```json
    "claude_efficiency": {
      "root": "nexus",
      "role": "meta-harness-optimizer",
      "hypothesis_dirs": [
        "shared/hypotheses/claude_efficiency"
      ],
      "constant_dirs": [],
      "description": "Claude Code CLI 효율 메타 사이클 — 로컬 세션 로그 기반 토큰 절감 + 세션간 지식 공유 돌파"
    }
```

(기존 엔트리의 끝 `}` 뒤에 `,`를 추가하고 위 블록 삽입)

- [ ] **Step 2: JSON 유효성 확인**

```bash
python3 -c "import json; d=json.load(open('shared/config/projects.json')); print('OK:', 'claude_efficiency' in d['projects'])"
```
Expected: `OK: True`

- [ ] **Step 3: watch-atlas kickstart**

```bash
launchctl kickstart -k "gui/$(id -u)/com.nexus.watch-atlas" 2>/dev/null || echo "watch-atlas not running (OK for dev)"
```

- [ ] **Step 4: Commit**

```bash
git add shared/config/projects.json
git commit -m "feat(projects): register claude_efficiency domain for atlas scan"
```

---

### Task 9: 해석기 픽스처 작성

**Files:**
- Create: `tools/tests/fixtures/sample_breakthrough.json`
- Create: `tools/tests/fixtures/sample_discovery.jsonl`

- [ ] **Step 1: breakthrough JSON 픽스처**

`tools/tests/fixtures/sample_breakthrough.json`:
```json
{
  "domain": "claude_efficiency",
  "cycles_run": 5,
  "converged_patterns": [
    {"name": "reuse_dominance", "strength": 0.82, "constants_matched": ["1/3"]},
    {"name": "size_concentration", "strength": 0.71, "constants_matched": ["phi/6"]},
    {"name": "noise", "strength": 0.12, "constants_matched": []}
  ],
  "surviving_hypotheses": ["H1", "H2"],
  "discovery_log_refs": [0, 1]
}
```

- [ ] **Step 2: discovery_log 픽스처**

`tools/tests/fixtures/sample_discovery.jsonl`:
```jsonl
{"pattern":"reuse_dominance","source":"H1","value":0.333,"constant":"1/3","note":"tool repeat rate matches meta fixed point"}
{"pattern":"size_concentration","source":"H2","value":0.262,"constant":"phi/6","note":"p95 byte concentration"}
```

- [ ] **Step 3: Commit**

```bash
git add tools/tests/fixtures/sample_breakthrough.json tools/tests/fixtures/sample_discovery.jsonl
git commit -m "test: add breakthrough + discovery_log fixtures"
```

---

### Task 10: 해석기 — 로드 + 랭킹 (TDD)

**Files:**
- Create: `tools/interpret_breakthrough.py`
- Create: `tools/tests/test_interpret_breakthrough.py`

- [ ] **Step 1: 실패 테스트**

`tools/tests/test_interpret_breakthrough.py`:
```python
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from interpret_breakthrough import load_and_rank

FIX = Path(__file__).parent / "fixtures"

class TestInterpret(unittest.TestCase):
    def test_load_and_rank(self):
        result = load_and_rank(
            FIX / "sample_breakthrough.json",
            FIX / "sample_discovery.jsonl",
            min_strength=0.5,
        )
        # 3 patterns total, 2 above 0.5
        self.assertEqual(len(result), 2)
        # sorted by strength desc
        self.assertEqual(result[0]["name"], "reuse_dominance")
        self.assertGreater(result[0]["strength"], result[1]["strength"])
        # discovery note가 연결됨
        self.assertIn("note", result[0])

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 실패 확인**

```bash
python3 -m unittest tools.tests.test_interpret_breakthrough -v
```
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: 구현**

`tools/interpret_breakthrough.py`:
```python
"""사이클 결과 JSON + discovery_log → 규칙 후보 md. 로컬만."""
import json
from pathlib import Path

def load_and_rank(
    breakthrough_json: Path, discovery_log: Path, min_strength: float = 0.5
) -> list[dict]:
    data = json.loads(Path(breakthrough_json).read_text(encoding="utf-8"))
    patterns = data.get("converged_patterns", [])
    # discovery_log 로드 (선택)
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
```

- [ ] **Step 4: 통과 확인**

```bash
python3 -m unittest tools.tests.test_interpret_breakthrough -v
```
Expected: 1 test PASS

- [ ] **Step 5: Commit**

```bash
git add tools/interpret_breakthrough.py tools/tests/test_interpret_breakthrough.py
git commit -m "feat(interpreter): load + rank breakthrough patterns by strength"
```

---

### Task 11: 해석기 — 규칙 템플릿 번역 (TDD)

**Files:**
- Modify: `tools/interpret_breakthrough.py`
- Modify: `tools/tests/test_interpret_breakthrough.py`

- [ ] **Step 1: 실패 테스트 추가**

`tools/tests/test_interpret_breakthrough.py`에 메서드 추가:
```python
    def test_translate_to_rule(self):
        from interpret_breakthrough import translate_to_rule
        pattern = {
            "name": "reuse_dominance", "strength": 0.82,
            "constants_matched": ["1/3"],
            "note": "tool repeat rate matches meta fixed point",
        }
        rule = translate_to_rule(pattern, source_hypothesis="H1")
        self.assertIn("R", rule["id"])
        self.assertIn("reuse_dominance", rule["rationale"])
        self.assertIn("0.82", rule["rationale"])
        self.assertIn("H1", rule["source"])
        self.assertTrue(len(rule["text"]) > 10)

    def test_translate_unknown_pattern_fallback(self):
        from interpret_breakthrough import translate_to_rule
        pattern = {"name": "unknown_xyz", "strength": 0.6, "constants_matched": []}
        rule = translate_to_rule(pattern, source_hypothesis="H?")
        self.assertIn("unknown_xyz", rule["text"])
```

- [ ] **Step 2: 실패 확인**

```bash
python3 -m unittest tools.tests.test_interpret_breakthrough -v
```
Expected: FAIL (ImportError)

- [ ] **Step 3: 구현**

`tools/interpret_breakthrough.py` 끝에 추가:
```python
# 패턴명 → 규칙 텍스트 템플릿 (로컬 매핑, LLM 호출 없음)
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
```

- [ ] **Step 4: 테스트 격리를 위해 setUp 추가**

`tools/tests/test_interpret_breakthrough.py`의 `TestInterpret` 클래스 안에 추가:
```python
    def setUp(self):
        from interpret_breakthrough import reset_rule_counter
        reset_rule_counter()
```

- [ ] **Step 5: 통과 확인**

```bash
python3 -m unittest tools.tests.test_interpret_breakthrough -v
```
Expected: 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add tools/interpret_breakthrough.py tools/tests/test_interpret_breakthrough.py
git commit -m "feat(interpreter): translate patterns to CLAUDE.md rule candidates"
```

---

### Task 12: 해석기 — rules.md 렌더 + CLI

**Files:**
- Modify: `tools/interpret_breakthrough.py`
- Modify: `tools/tests/test_interpret_breakthrough.py`

- [ ] **Step 1: 실패 테스트 추가**

`tools/tests/test_interpret_breakthrough.py`에 추가:
```python
    def test_render_rules_md_and_empty(self):
        from interpret_breakthrough import render_rules_md
        rules = [
            {"id": "R1", "text": "foo", "source": "H1", "rationale": "x"},
            {"id": "R2", "text": "bar", "source": "H2", "rationale": "y"},
        ]
        md = render_rules_md(rules, date_str="2026-04-05")
        self.assertIn("# 도출 규칙 후보", md)
        self.assertIn("R1", md)
        self.assertIn("foo", md)

        empty_md = render_rules_md([], date_str="2026-04-05")
        self.assertIn("패턴 없음", empty_md)
```

- [ ] **Step 2: 실패 확인**

```bash
python3 -m unittest tools.tests.test_interpret_breakthrough -v
```
Expected: FAIL (ImportError: render_rules_md)

- [ ] **Step 3: 구현**

`tools/interpret_breakthrough.py` 끝에 추가:
```python
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
        "--discovery", default="shared/discovery/discovery_log.jsonl",
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
    # H 매핑: surviving_hypotheses 순서대로 배정 (없으면 H?)
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
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
python3 -m unittest tools.tests.test_interpret_breakthrough -v
```
Expected: 4 tests PASS

- [ ] **Step 5: CLI 스모크**

```bash
python3 tools/interpret_breakthrough.py tools/tests/fixtures/sample_breakthrough.json --discovery tools/tests/fixtures/sample_discovery.jsonl --out-dir /tmp/test_rules
cat /tmp/test_rules/claude_efficiency_rules_*.md
```
Expected: `interpreter: wrote ...` + 규칙 후보 md 내용 출력

- [ ] **Step 6: Commit**

```bash
git add tools/interpret_breakthrough.py tools/tests/test_interpret_breakthrough.py
git commit -m "feat(interpreter): render rules.md + add CLI entry point"
```

---

### Task 13: 파이프라인 래퍼 스크립트

**Files:**
- Create: `tools/run_cc_breakthrough.sh`

- [ ] **Step 1: 스크립트 작성**

`tools/run_cc_breakthrough.sh`:
```bash
#!/bin/bash
# Claude Code 효율 특이점 사이클 파이프라인
# 100% 로컬 실행, 외부 API 호출 없음
set -euo pipefail
cd "$(dirname "$0")/.."

DATE=$(date +%Y%m%d)
OUT_DIR="shared/breakthroughs"
mkdir -p "$OUT_DIR"

echo "[1/4] mining Claude Code sessions..."
python3 tools/cc_session_miner.py --sessions 20

echo "[2/4] syncing math atlas..."
if [ -x "shared/scripts/sync-math-atlas.sh" ]; then
  bash shared/scripts/sync-math-atlas.sh
  sleep 2
else
  echo "WARN: shared/scripts/sync-math-atlas.sh not found or not executable, skipping" >&2
fi

echo "[3/4] running nexus auto (claude_efficiency) with 30min timeout..."
NEXUS_BIN="${NEXUS_BIN:-nexus}"
CYCLE_OUT="$OUT_DIR/claude_efficiency_$DATE.json"
if timeout 1800 "$NEXUS_BIN" auto claude_efficiency \
     --meta-cycles 5 --ouroboros-cycles 3 > "$CYCLE_OUT"; then
  echo "cycle done"
else
  rc=$?
  echo "WARN: cycle exit=$rc (timeout=124 or error), continuing with partial output" >&2
fi

echo "[4/4] interpreting breakthrough..."
if [ -s "$CYCLE_OUT" ]; then
  python3 tools/interpret_breakthrough.py "$CYCLE_OUT"
else
  echo "ERROR: cycle output empty, cannot interpret" >&2
  exit 4
fi

echo "done. review: $OUT_DIR/claude_efficiency_rules_$(date +%Y-%m-%d).md"
```

- [ ] **Step 2: 실행 권한**

```bash
chmod +x tools/run_cc_breakthrough.sh
```

- [ ] **Step 3: 문법 체크 (실제 실행은 수동 스모크)**

```bash
bash -n tools/run_cc_breakthrough.sh && echo "syntax OK"
```
Expected: `syntax OK`

- [ ] **Step 4: Commit**

```bash
git add tools/run_cc_breakthrough.sh
git commit -m "feat: add pipeline wrapper for claude_efficiency breakthrough cycle"
```

---

### Task 14: 전 파이프라인 수동 스모크 + 결과 보고

**Files:**
- None (manual verification)

- [ ] **Step 1: 파이프라인 실행 (백그라운드)**

```bash
bash tools/run_cc_breakthrough.sh 2>&1 | tee /tmp/cc_breakthrough_run.log
```

(`nexus auto`가 수 분~수십 분 걸릴 수 있으므로 사용자가 `run_in_background: true`로 호출 권장. 이 플랜에서는 포그라운드로 1회 수동 확인)

- [ ] **Step 2: 산출물 확인**

```bash
ls -la shared/hypotheses/claude_efficiency/ shared/breakthroughs/
```
Expected: `metrics_*.md`, `hypotheses_*.md`, `claude_efficiency_*.json`, `claude_efficiency_rules_*.md` 모두 존재

- [ ] **Step 3: 규칙 후보 검토**

```bash
cat shared/breakthroughs/claude_efficiency_rules_*.md
```
판정:
- 규칙 후보 3개 이상 + 사람이 납득 가능 → **성공**. 사람이 CLAUDE.md에 병합 여부 결정
- 0개 또는 모두 "패턴 없음" → 가설 재설계 필요. Task 6의 `render_hypotheses_md`에 돌파 가설 추가 후 사이클 재실행

- [ ] **Step 4: 돌파 여부 기록**

사람이 판단한 결과를 짧게 커밋 메시지에 남긴다 (자동 병합 금지):
```bash
# 결과가 있으면 산출물을 git에 포함
git add shared/breakthroughs/claude_efficiency_rules_*.md shared/hypotheses/claude_efficiency/*.md 2>/dev/null || true
git commit -m "data: record claude_efficiency cycle run $(date +%Y-%m-%d)" || echo "nothing to commit"
```

---

## Self-Review Checklist

**Spec coverage**: Phase 1~3 + 3(a) CLAUDE.md 규칙 도출 → 모두 태스크 있음 (C1 Task 3-7, C2 Task 8, C3 Task 13, C4 Task 10-12, C5는 Task 14 Step 3 사람 병합). ✅

**Placeholder scan**: "TBD/TODO/fill in" 없음. 모든 코드 블록 완전. ✅

**Type consistency**: `parse_session`, `aggregate_sessions`, `render_metrics_md`, `render_hypotheses_md`, `load_and_rank`, `translate_to_rule`, `render_rules_md`, `reset_rule_counter` — 정의 후 일관 사용. ✅

**No external API**: 모든 컴포넌트 `json`/`pathlib`/`hashlib`/`argparse`만 import. ✅

**Idempotent**: miner/interpreter는 날짜 기반 파일명, 같은 날 재실행 시 덮어쓰기 (OK). ✅
