#!/usr/bin/env python3
# @hexa-first-exempt — subprocess orchestration + JSONL atomic append + 72h windowing cleanest in Python
# ═══════════════════════════════════════════════════════════
# atlas_drift_monitor.py — ATLAS-P3-3 drift < 1% 3-day monitor
#
# Runs shared/n6/miss_to_exact_tracker.hexa (READ-ONLY), parses the
# transition-rate block, and tracks drift_pct over time.
#
# Drift metric:
#   drift_pct := HYPOTHESIS rate (unverified claims = drift from EXACT consensus)
#
#   Rationale: MISS (6.67%) represents un-graded nodes (engineering debt,
#   not conceptual drift). HYPOTHESIS (0.508%) represents active
#   unverified assertions that must converge or be rejected — this is
#   the true "drift" from the atlas's verified EXACT core.
#
# Modes:
#   --sample       run tracker once, append {ts, drift_pct, source} to log
#   --check-3day   read last 72h of samples, assert all drift_pct < 1%,
#                  emit verdict JSON
#   --now          --sample + --check-3day, summary output
#
# Log: shared/discovery/atlas_drift_log.jsonl (append-only, atomic)
# ═══════════════════════════════════════════════════════════

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path


NEXUS = Path(os.environ.get("NEXUS", "/Users/ghost/Dev/nexus"))
TRACKER = NEXUS / "shared" / "n6" / "miss_to_exact_tracker.hexa"
HEXA_BIN = NEXUS / "shared" / "bin" / "hexa"
LOG_PATH = NEXUS / "shared" / "discovery" / "atlas_drift_log.jsonl"
DRIFT_THRESHOLD_PCT = 1.0
WINDOW_HOURS = 72


def _run_tracker():
    """Invoke miss_to_exact_tracker.hexa and capture stdout."""
    cp = subprocess.run(
        [str(HEXA_BIN), str(TRACKER)],
        capture_output=True, text=True, timeout=120, cwd=str(NEXUS),
    )
    if cp.returncode != 0:
        raise RuntimeError(f"tracker exit {cp.returncode}: {cp.stderr[:500]}")
    return cp.stdout


RATE_PATTERNS = {
    "exact_pct": r"EXACT rate:\s+([\d.]+)%",
    "partial_pct": r"PARTIAL rate:\s+([\d.]+)%",
    "hypothesis_pct": r"HYPOTHESIS rate:\s+([\d.]+)%",
    "miss_pct": r"MISS rate:\s+([\d.]+)%",
}
NODE_PATTERNS = {
    "total_all": r"Total nodes \(text \+ JSON\):\s+(\d+)",
    "miss": r"MISS \(ungraded/unknown\):\s+(\d+)",
    "hypothesis": r"HYPOTHESIS \[N\?\] \+ low:\s+(\d+)",
    "exact": r"EXACT\s+\[N\*\] \+ high-conf:\s+(\d+)",
    "partial": r"PARTIAL\s+\[N\] \+ \[N!\] \+ mid:\s+(\d+)",
}


def _parse_tracker(out: str):
    rates = {}
    for k, pat in RATE_PATTERNS.items():
        m = re.search(pat, out)
        if m:
            rates[k] = float(m.group(1))
    counts = {}
    for k, pat in NODE_PATTERNS.items():
        m = re.search(pat, out)
        if m:
            counts[k] = int(m.group(1))
    return rates, counts


def _atomic_append_jsonl(path: Path, record: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False) + "\n"
    # append is atomic at O_APPEND level on POSIX for small lines
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


def sample() -> dict:
    out = _run_tracker()
    rates, counts = _parse_tracker(out)
    if "hypothesis_pct" not in rates:
        raise RuntimeError(f"failed to parse HYPOTHESIS rate from tracker output:\n{out[:500]}")
    drift_pct = rates["hypothesis_pct"]
    record = {
        "ts": time.time(),
        "iso": datetime.now(timezone.utc).isoformat(),
        "drift_pct": drift_pct,
        "source": "miss_to_exact_tracker.hexa",
        "metric": "HYPOTHESIS_rate (pct of nodes with [N?] grade or confidence<0.5)",
        "rates": rates,
        "counts": counts,
        "tool": "atlas_drift_monitor.py",
    }
    _atomic_append_jsonl(LOG_PATH, record)
    return record


def _read_samples():
    if not LOG_PATH.exists():
        return []
    out = []
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
    return out


def check_3day() -> dict:
    samples = _read_samples()
    now = time.time()
    cutoff = now - WINDOW_HOURS * 3600
    window = [s for s in samples if isinstance(s.get("ts"), (int, float)) and s["ts"] >= cutoff]

    sample_count = len(window)
    drifts = [s["drift_pct"] for s in window if isinstance(s.get("drift_pct"), (int, float))]
    if drifts:
        max_drift = max(drifts)
        avg_drift = sum(drifts) / len(drifts)
        min_drift = min(drifts)
    else:
        max_drift = avg_drift = min_drift = None

    all_under = (drifts and all(d < DRIFT_THRESHOLD_PCT for d in drifts))

    # Determine if the sample span actually covers 72h
    if window:
        span_hours = (max(s["ts"] for s in window) - min(s["ts"] for s in window)) / 3600.0
    else:
        span_hours = 0.0
    span_ok = span_hours >= (WINDOW_HOURS - 1)  # 1h tolerance

    verdict_fields = {
        "threshold_pct": DRIFT_THRESHOLD_PCT,
        "window_hours": WINDOW_HOURS,
        "log_path": str(LOG_PATH.relative_to(NEXUS)),
        "sample_count_in_window": sample_count,
        "span_hours": round(span_hours, 3),
        "span_meets_window": bool(span_ok),
        "max_drift_pct": max_drift,
        "avg_drift_pct": round(avg_drift, 5) if avg_drift is not None else None,
        "min_drift_pct": min_drift,
        "all_samples_under_threshold": bool(all_under),
        # True verdict requires BOTH conditions
        "verdict_3day_drift_under_threshold": bool(all_under and span_ok),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

    # If window is not yet 72h, report the current status so the user
    # can see what's needed for a passing verdict.
    if not span_ok:
        missing_hours = round(WINDOW_HOURS - span_hours, 2)
        verdict_fields["note"] = (
            f"Insufficient sample history: need {missing_hours}h more "
            f"of samples at ≥hourly cadence for a 72h verdict. "
            f"All current samples are {'under' if all_under else 'NOT under'} {DRIFT_THRESHOLD_PCT}%."
        )
    return verdict_fields


def now_mode() -> dict:
    rec = sample()
    verdict = check_3day()
    return {
        "current_sample": rec,
        "verdict": verdict,
    }


def main():
    p = argparse.ArgumentParser(description="ATLAS-P3-3 drift<1% 3-day monitor")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--sample", action="store_true", help="run one sample and append to log")
    g.add_argument("--check-3day", action="store_true", help="check last 72h of samples")
    g.add_argument("--now", action="store_true", help="sample + check-3day summary")
    args = p.parse_args()

    try:
        if args.sample:
            rec = sample()
            print(json.dumps(rec, indent=2))
        elif args.check_3day:
            v = check_3day()
            print(json.dumps(v, indent=2))
            sys.exit(0 if v.get("verdict_3day_drift_under_threshold") else 1)
        elif args.now:
            out = now_mode()
            print(json.dumps(out, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e), "type": type(e).__name__}, indent=2), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
