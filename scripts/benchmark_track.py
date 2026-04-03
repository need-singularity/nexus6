#!/usr/bin/env python3
"""NEXUS-6 Benchmark Auto-tracking — run, record, compare, trend.

Runs benchmarks at standard sizes, appends to history, shows trends.

Usage:
  python3 benchmark_track.py          # Run + track
  python3 benchmark_track.py history  # Show history
  python3 benchmark_track.py trend    # Show trend only
"""
import sys, os, json, time
from datetime import datetime
import numpy as np

try:
    import nexus6
except ImportError:
    print("nexus6 not installed"); sys.exit(1)

HISTORY_FILE = os.path.expanduser("~/.nexus6/benchmark_history.jsonl")
os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)

SIZES = [(50, 6), (100, 6), (500, 6)]
RUNS_PER_SIZE = 3


def run_benchmark():
    """Run benchmark at standard sizes, return timing dict."""
    np.random.seed(6)
    results = {}
    for n, d in SIZES:
        data = np.random.randn(n, d).flatten().tolist()
        times = []
        for _ in range(RUNS_PER_SIZE):
            t0 = time.time()
            result = nexus6.scan(data, n, d)
            times.append(time.time() - t0)
        median_ms = sorted(times)[len(times) // 2] * 1000
        lens_count = len(result.lens_names)
        active = sum(1 for nm in result.lens_names if result.get_lens(nm))
        results[f"{n}x{d}"] = {"median_ms": round(median_ms, 1),
                                "lenses": lens_count, "active": active}
    return results


def load_history():
    """Load all historical entries."""
    if not os.path.exists(HISTORY_FILE):
        return []
    entries = []
    with open(HISTORY_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def append_entry(entry):
    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def compare_with_previous(current, history):
    """Compare current run with last entry."""
    if not history:
        print("  (first run, no comparison)")
        return
    prev = history[-1]["results"]
    print(f"\n  {'Size':<10} {'Current':>10} {'Previous':>10} {'Delta':>10} {'Trend':>8}")
    print(f"  {'-'*50}")
    for key in sorted(current.keys()):
        cur_ms = current[key]["median_ms"]
        prev_ms = prev.get(key, {}).get("median_ms", cur_ms)
        delta = cur_ms - prev_ms
        pct = (delta / prev_ms * 100) if prev_ms > 0 else 0
        if abs(pct) < 2:
            trend = "same"
        elif delta < 0:
            trend = f"faster ({pct:+.1f}%)"
        else:
            trend = f"slower ({pct:+.1f}%)"
        print(f"  {key:<10} {cur_ms:>8.1f}ms {prev_ms:>8.1f}ms {delta:>+8.1f}ms  {trend}")


def show_trend(history, limit=10):
    """Show timing trend from history."""
    if not history:
        print("No history yet."); return
    recent = history[-limit:]
    print(f"\nBenchmark trend (last {len(recent)} runs):")
    print(f"  {'Date':<20} ", end="")
    for n, d in SIZES:
        print(f"  {n}x{d:>3}", end="")
    print()
    print(f"  {'-'*50}")
    for entry in recent:
        ts = entry.get("timestamp", "?")[:19]
        print(f"  {ts:<20} ", end="")
        for n, d in SIZES:
            key = f"{n}x{d}"
            ms = entry["results"].get(key, {}).get("median_ms", 0)
            print(f"  {ms:>6.1f}", end="")
        print(" ms")


if __name__ == "__main__":
    history = load_history()

    if len(sys.argv) > 1 and sys.argv[1] == "history":
        show_trend(history, limit=50)
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "trend":
        show_trend(history)
        sys.exit(0)

    print("=== NEXUS-6 Benchmark Auto-tracking ===\n")
    print(f"Sizes: {SIZES}, {RUNS_PER_SIZE} runs each (median)")

    results = run_benchmark()
    for key, r in sorted(results.items()):
        print(f"  {key}: {r['median_ms']:.1f}ms ({r['active']}/{r['lenses']} lenses)")

    entry = {"timestamp": datetime.now().isoformat(), "results": results}
    append_entry(entry)
    print(f"\nSaved to {HISTORY_FILE}")

    compare_with_previous(results, history)
    show_trend(history + [entry])
