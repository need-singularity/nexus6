#!/usr/bin/env python3
"""Batch translate Korean to English using Claude API. Hybrid: Opus for .md, Sonnet for .py

Prerequisites:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-...

Usage:
    python3 scripts/translate_to_english.py
"""

import os
import re
import sys
import time
import json
import anthropic
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPUS = "claude-opus-4-20250514"
SONNET = "claude-sonnet-4-20250514"
MAX_WORKERS = 2
MAX_RETRIES = 10
ROOT = Path("/Users/ghost/Dev/TECS-L")
SKIP_FILES = {
    "docs/kaist-eeg-collaboration-proposal.md",
    "CLAUDE.md",  # project instructions — keep bilingual
}
PROGRESS_FILE = ROOT / ".translate_progress.json"

SKIP_DIRS = {".git", ".local", ".claude", "node_modules", "__pycache__", "serve", "math/.claude"}

SYSTEM_PROMPT = """You are a technical translator. Translate ALL Korean text to English in the given file content.

RULES:
1. Translate ALL Korean text to natural English.
2. Keep ALL formatting exactly the same (markdown, code blocks, indentation, emojis, symbols, ASCII art).
3. Do NOT change any: variable names, function names, file paths, URLs, numbers, mathematical expressions, hypothesis IDs (H-CX-xxx), constant names (C1, C48, etc.).
4. For Python files: translate Korean in comments (#), docstrings, and string literals. Do NOT change code logic.
5. For Markdown files: translate all Korean prose, table content, headers, and descriptions.
6. Return ONLY the translated file content. No explanations, no markdown wrapper.
7. If there is no Korean text, return the content unchanged.

Key terminology (use consistently):
- 의식영속성 = Consciousness Continuity
- 골든존 = Golden Zone
- 반발력장 = Repulsion Field
- 장력 = Tension
- 확신 = Confidence
- 분열 = Mitosis/Fission
- 이상탐지 = Anomaly Detection
- 텔레파시 = Telepathy
- 예지 = Precognition
- 혼동 = Confusion
- 위상 = Topology/Phase (context-dependent)
- 완전수 = Perfect Number
- 약수 = Divisor
- 소수 = Prime Number
- 서번트 = Savant
- 교차 도메인 = Cross-domain
- 보편성 = Universality
- 정체성 = Identity
- 과신 = Overconfidence
- 만장일치 = Unanimity
- 차원간 = Cross-dimensional
- 뇌파 = Brainwave
- 돌고래 = Dolphin
- 뇌화학 = Neurochemistry
- 호기심 = Curiosity
- 엔진 = Engine
- 억제 = Inhibition
- 축소사상 = Contraction mapping
- 부동점 = Fixed point
- 메타인지 = Metacognition
- 자기참조 = Self-reference
- 타자 모델링 = Other-modeling
- 공감 = Empathy
- 가중치 = Weight
- 수렴 = Convergence
- 발산 = Divergence
- 약수역수 = Divisor reciprocal
- 오답 = Wrong answer
- 정답 = Correct answer
- 밀집 = Dense
- 희소 = Sparse
- 가설 = Hypothesis
- 대발견 = Major Discovery
- 검증 = Verification
- 반증 = Refuted
- 약화 = Weakened
- 승격 = Upgrade
- 재현 = Reproduction
- 순수 산술 = Pure Arithmetic
- 대통합 = Grand Unification
- 생성 엔진 = Generative Engine
- 잠재 공간 = Latent Space
- 내용 축 = Content Axis
- 구조 축 = Structure Axis
- 거울뉴런 = Mirror Neuron
- 파이버 번들 = Fiber Bundle
- 홀로노미 = Holonomy
- 곡률 = Curvature
- 밑공간 = Base Space
- 심박 = Heartbeat
- 호흡 = Respiration
- 염기 = Base (nucleotide)
- 코돈 = Codon
- 아미노산 = Amino acid
- 뇌신경 = Cranial nerve
- 청각 = Hearing
- 발화율 = Firing rate
- 삼각수 = Triangular number
- 약물 = Drug
- 카페인 = Caffeine
- 알코올 = Alcohol
- 명상 = Meditation
- 양자 = Quantum
- 집단지성 = Collective intelligence
- 교정 = Calibration
- 망각방지 = Forgetting prevention"""


def has_korean(text: str) -> bool:
    return bool(re.search(r'[가-힣]', text))


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"done": [], "failed": []}


def save_progress(progress: dict):
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2, ensure_ascii=False))


def find_files() -> list[Path]:
    """Find all .md and .py files with Korean text."""
    files = []
    for ext in ("*.md", "*.py"):
        for f in ROOT.rglob(ext):
            rel = f.relative_to(ROOT)
            if any(part in SKIP_DIRS for part in rel.parts):
                continue
            if str(rel) in SKIP_FILES:
                continue
            try:
                content = f.read_text(encoding="utf-8")
                if has_korean(content):
                    files.append(f)
            except Exception:
                continue
    return sorted(files)


def pick_model(filepath: Path) -> str:
    """All Opus."""
    return OPUS


def estimate_max_tokens(content: str) -> int:
    """Estimate max_tokens based on content length."""
    # Rough: 1 char ≈ 0.5 tokens for mixed Korean/English
    estimated = int(len(content) * 0.7) + 500
    return min(max(estimated, 2000), 64000)


def translate_file(client: anthropic.Anthropic, filepath: Path) -> tuple[Path, bool, str]:
    """Translate a single file. Returns (path, success, error_msg)."""
    try:
        content = filepath.read_text(encoding="utf-8")
        if not has_korean(content):
            return filepath, True, "no korean"

        file_rel = filepath.relative_to(ROOT)
        model = pick_model(filepath)
        max_tok = estimate_max_tokens(content)

        user_msg = f"File: {file_rel} ({filepath.suffix})\n\n---FILE CONTENT START---\n{content}\n---FILE CONTENT END---"

        for attempt in range(MAX_RETRIES):
            try:
                translated_parts = []
                with client.messages.stream(
                    model=model,
                    max_tokens=max_tok,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_msg}],
                ) as stream:
                    for text in stream.text_stream:
                        translated_parts.append(text)
                translated = "".join(translated_parts)

                # Sanity check
                ratio = len(translated) / len(content) if len(content) > 0 else 1
                if ratio < 0.3 or ratio > 3.0:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(2)
                        continue
                    return filepath, False, f"size ratio {ratio:.2f} suspicious"

                # Verify Korean was actually removed
                if has_korean(translated):
                    korean_remaining = len(re.findall(r'[가-힣]+', translated))
                    # Allow small amount (might be in code comments that are OK)
                    if korean_remaining > 5:
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(2)
                            continue

                filepath.write_text(translated, encoding="utf-8")
                return filepath, True, f"[{model.split('-')[1]}]"

            except anthropic.RateLimitError as e:
                wait = 30 * (attempt + 1)
                print(f"  Rate limited on {file_rel}, waiting {wait}s... (attempt {attempt+1})", flush=True)
                time.sleep(wait)
            except anthropic.APIError as e:
                err_str = str(e)
                if "credit" in err_str.lower() or "billing" in err_str.lower():
                    return filepath, False, f"BILLING: {e}"
                if "overloaded" in err_str.lower():
                    wait = 60 * (attempt + 1)
                    print(f"  Overloaded on {file_rel}, waiting {wait}s... (attempt {attempt+1})", flush=True)
                    time.sleep(wait)
                elif attempt < MAX_RETRIES - 1:
                    time.sleep(10 * (attempt + 1))
                else:
                    return filepath, False, err_str
    except Exception as e:
        return filepath, False, str(e)

    return filepath, False, "max retries exceeded"


def main():
    if not API_KEY:
        print("ERROR: Set ANTHROPIC_API_KEY environment variable")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=API_KEY)
    progress = load_progress()
    done_set = set(progress["done"])

    all_files = find_files()
    todo = [f for f in all_files if str(f.relative_to(ROOT)) not in done_set]

    # Count by model
    opus_count = sum(1 for f in todo if pick_model(f) == OPUS)
    sonnet_count = sum(1 for f in todo if pick_model(f) == SONNET)

    print(f"Total files with Korean: {len(all_files)}")
    print(f"Already done: {len(done_set)}")
    print(f"Remaining: {len(todo)} (Opus: {opus_count}, Sonnet: {sonnet_count})")
    print(f"Workers: {MAX_WORKERS}")
    print(flush=True)

    if not todo:
        print("All done!")
        return

    success_count = 0
    fail_count = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(translate_file, client, f): f for f in todo}

        for i, future in enumerate(as_completed(futures), 1):
            filepath, success, info = future.result()
            rel = filepath.relative_to(ROOT)

            if success:
                success_count += 1
                progress["done"].append(str(rel))
                status = f"OK {info}"
            else:
                fail_count += 1
                progress["failed"].append({"file": str(rel), "error": info})
                status = f"FAIL: {info}"
                # Stop on billing errors
                if "BILLING" in info:
                    print(f"\n!!! BILLING ERROR - stopping !!!")
                    save_progress(progress)
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

            elapsed = time.time() - start_time
            rate = i / elapsed * 60 if elapsed > 0 else 0
            eta_min = (len(todo) - i) / rate if rate > 0 else 0
            print(f"[{i}/{len(todo)}] {status} - {rel}  ({rate:.0f}/min, ETA {eta_min:.0f}min)", flush=True)

            if i % 10 == 0:
                save_progress(progress)

    save_progress(progress)
    elapsed = time.time() - start_time
    print(f"\nDone! Success: {success_count}, Failed: {fail_count}, Time: {elapsed/60:.1f}min")


if __name__ == "__main__":
    main()