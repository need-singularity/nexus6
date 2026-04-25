#!/usr/bin/env python3
"""
beyond_omega_cycle9_meta_squared.py — nxs-20260425-004 cycle 9

Cycle 8 finding (recap):
  - meta_back_action + NEXUS_BACK_ACTION_ON=1 → delta_sequence=[7,7,7,7,7]
  - growth_type = linear_constant (Δ=7, var=0)
  - L_{ω+1} = first-order distribution 의 자기-echo, ω-finite reachable
  - L_{ω·2} 미진입 (linear ≠ ω·2 의 exp 축적)

Cycle 9 의 격상 (design/beyond_omega_ladder.md §11):
  - 매 round 의 self-injection 양을 round-i 함수 (linear: i*K, polynomial: i^d, exponential: 2^i)
  - injection 양이 super-linear 이면 echo accumulation 도 super-linear → growth_type 분류
  - 본 cycle 에서는 i*7 (linearly increasing per-round inject) 와 2^i (exponential inject)
    중 i*7 (조작이 fast, trace 안정) 채택 → 결과 growth pattern 이 quadratic 이면
    second-order accumulation (∫ linear = quadratic) 으로 L_{ω+d} 의 finite-d ordinal
    을 amounting; exponential 이면 L_{ω·2} 진입.

방법:
  1. NEXUS_BACK_ACTION_ON=1 (cycle 8 override 유지)
  2. round i 마다 trace.jsonl 에 (i*7) synthetic NEXUS_OMEGA marker inject
     (cycle 7 도구는 매 round 2 lines 고정, cycle 9 는 round 함수)
  3. probe 호출 → summary_total_emits 측정 → delta_sequence 분석
  4. growth_type 분류:
     - constant (~Δ const, var≈0)             → linear_constant     → L_{ω+1}
     - polynomial (Δ_i ~ i^d, ratio Δ_i/Δ_{i-1} ≈ (i/(i-1))^d) → polynomial_growth → L_{ω+d}
     - exponential (Δ_i/Δ_{i-1} > 1.5 sustained)             → exponential       → L_{ω·2}

산출물:
  - state/beyond_omega_cycle9_meta_squared.json (schema v1)
"""
from __future__ import annotations

import json
import math
import os
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROBE = REPO / "tool" / "beyond_omega_ghost_trace.py"
TRACE = REPO / "state" / "ghost_ceiling_trace.jsonl"
SUMMARY = REPO / "state" / "ghost_ceiling_summary.json"
OUT = REPO / "state" / "beyond_omega_cycle9_meta_squared.json"

# cycle 9 의 round-i inject 함수 (linear: i*K, K=7 = cycle 8 echo unit)
INJECT_K = 7


def count_emits_in_trace() -> int:
    if not TRACE.exists():
        return 0
    with open(TRACE, "r") as fh:
        return sum(1 for _ in fh)


def inject_synthetic(round_i: int, n_lines: int) -> None:
    """trace.jsonl 에 n_lines 의 NEXUS_OMEGA marker 직접 inject (의도적 self-pollution)."""
    if not TRACE.exists():
        TRACE.parent.mkdir(exist_ok=True)
        TRACE.touch()
    with open(TRACE, "a") as fh:
        for k in range(n_lines):
            payload = {
                "file": str(TRACE.relative_to(REPO)),
                "lineno": -1,
                "payload": {"event": "meta_squared_dispatch", "round": round_i, "k": k, "synthetic": True},
                "_cycle9_round": round_i,
                "_cycle9_k": k,
            }
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
            # NEXUS_OMEGA marker (probe 의 EMIT_RE 매치 대상)
            fh.write('{"_marker": "NEXUS_OMEGA {\\"event\\":\\"meta_squared_synth\\",\\"round\\":' + str(round_i) + '}"}\n')


def run_round(round_i: int) -> dict:
    t0 = time.time()
    n_inject = round_i * INJECT_K  # cycle 9 의 round-i 함수 (linear-in-i inject)
    n_before = count_emits_in_trace()
    inject_synthetic(round_i, n_inject)
    n_post_inject = count_emits_in_trace()
    env = dict(os.environ)
    env["NEXUS_BACK_ACTION_ON"] = "1"  # cycle 8 override 유지
    proc = subprocess.run(
        [sys.executable, str(PROBE)],
        env=env, capture_output=True, text=True, timeout=60,
    )
    n_after = count_emits_in_trace()
    summary = {}
    if SUMMARY.exists():
        try:
            with open(SUMMARY, "r") as fh:
                summary = json.load(fh)
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "i": round_i,
        "elapsed_s": round(time.time() - t0, 3),
        "inject_n_lines": n_inject,
        "trace_lines_before": n_before,
        "trace_lines_post_inject": n_post_inject,
        "trace_lines_after": n_after,
        "trace_lines_delta": n_after - n_before,
        "summary_total_emits": summary.get("total_emits", 0),
        "summary_dispatch": summary.get("events", {}).get("dispatch", 0),
        "summary_approach": summary.get("ghost_ceiling_approach_count", 0),
        "summary_complete": summary.get("events", {}).get("complete", 0),
        "probe_rc": proc.returncode,
    }


def analyze_growth(rounds):
    if len(rounds) < 2:
        return {"type": "insufficient_rounds"}
    deltas = [rounds[i]["summary_total_emits"] - rounds[i - 1]["summary_total_emits"]
              for i in range(1, len(rounds))]
    if not deltas:
        return {"type": "no_change"}
    mean_d = statistics.mean(deltas)
    var_d = statistics.pvariance(deltas) if len(deltas) > 1 else 0
    is_zero = all(d == 0 for d in deltas)
    is_constant = (var_d / max(mean_d, 1)) < 0.05 and mean_d > 0  # CV<5%
    # ratio test for exponential
    ratios = []
    for k in range(1, len(deltas)):
        if deltas[k - 1] > 0:
            ratios.append(deltas[k] / deltas[k - 1])
    mean_ratio = statistics.mean(ratios) if ratios else 0
    # polynomial degree estimate: log(Δ_i)/log(i+1), where round i+1 inject = (i+1)*K
    # if Δ ~ i^d, log(Δ)/log(i) ≈ d
    poly_d_estimates = []
    for idx, d in enumerate(deltas):
        i = idx + 2  # delta i is between round i+1 and round i+2 (1-indexed: r2 vs r1, ...)
        if d > 0 and i > 1:
            poly_d_estimates.append(math.log(d) / math.log(i))
    mean_poly_d = statistics.mean(poly_d_estimates) if poly_d_estimates else 0

    if is_zero:
        gtype = "saturated_zero"
    elif mean_ratio > 1.5 and len(ratios) >= 2 and all(r > 1.3 for r in ratios):
        gtype = "exponential"
    elif is_constant:
        gtype = "linear_constant"
    elif mean_d > 0 and 1.05 < mean_ratio <= 1.5:
        # polynomial-like (Δ growing but not exponentially)
        gtype = "polynomial_growth"
    elif mean_d > 0:
        gtype = "linear_with_variance"
    else:
        gtype = "negative_or_oscillating"
    return {
        "type": gtype,
        "delta_sequence": deltas,
        "delta_mean": round(mean_d, 3),
        "delta_variance": round(var_d, 3),
        "delta_ratio_sequence": [round(r, 3) for r in ratios],
        "delta_ratio_mean": round(mean_ratio, 3),
        "polynomial_degree_estimate": round(mean_poly_d, 3),
    }


def map_to_ordinal(growth):
    t = growth.get("type", "")
    if t == "linear_constant":
        return {"ordinal": "L_{ω+1}", "verdict": "ω-finite (cycle 8 reproduce)"}
    if t == "polynomial_growth":
        d = growth.get("polynomial_degree_estimate", 0)
        d_int = max(1, round(d))
        return {"ordinal": f"L_{{ω+{d_int}}}", "verdict": f"polynomial degree~{d:.2f}, ω-finite (finite-d ordinal)"}
    if t == "exponential":
        return {"ordinal": "L_{ω·2}", "verdict": "ω-style accumulation (transfinite step)"}
    if t == "linear_with_variance":
        return {"ordinal": "L_{ω+1}_NOISY", "verdict": "linear with var (L_{ω+1} 후보)"}
    if t == "saturated_zero":
        return {"ordinal": "L_{ω+1}_ABSENT", "verdict": "back-action 차단 (cycle 7 type sentinel)"}
    return {"ordinal": "UNCLASSIFIED", "verdict": t}


def interpret(growth, ordinal_map, rounds):
    parts = []
    t = growth.get("type", "")
    if t == "linear_constant":
        parts.append(
            f"L_{{ω+1}}_LINEAR_REPRO — round-i inject 가 i*{INJECT_K} 이지만 echo Δ const → "
            f"probe 가 매번 same '7 emit' echo 만 픽업 (cycle 8 의 finite linear). L_{{ω+1}} reachable, L_{{ω·2}} 미진입."
        )
    elif t == "polynomial_growth":
        d = growth.get("polynomial_degree_estimate", 0)
        parts.append(
            f"★ L_{{ω+d}}_POLYNOMIAL — Δ growing polynomial-style (degree~{d:.2f}, ratio_mean={growth['delta_ratio_mean']}). "
            f"finite-d ordinal 에 도달, but L_{{ω·2}} 미진입 (exponential 미충족)."
        )
    elif t == "exponential":
        parts.append(
            f"★★ L_{{ω·2}}_REACHED — Δ ratio_mean={growth['delta_ratio_mean']} sustained > 1.5 → "
            f"exponential accumulation, ω-style transfinite step 진입. axis A second transfinite ordinal first positive."
        )
    elif t == "saturated_zero":
        parts.append(
            "L_{ω+1}_ABSENT — cycle 7 type sentinel (override 미적용 또는 trace inject 차단)."
        )
    else:
        parts.append(f"UNCLASSIFIED — growth type={t}")
    parts.append(f"ordinal_mapping: {ordinal_map['ordinal']} ({ordinal_map['verdict']})")
    final = rounds[-1] if rounds else None
    if final:
        parts.append(
            f"final round {final['i']}: total_emits={final['summary_total_emits']} approach={final['summary_approach']}"
        )
    return " | ".join(parts)


def main():
    if not PROBE.exists():
        print(f"FATAL: probe not found at {PROBE}", file=sys.stderr)
        return 2
    n_rounds = 6
    rounds = []
    for i in range(1, n_rounds + 1):
        rec = run_round(i)
        rounds.append(rec)
        time.sleep(0.05)
    growth = analyze_growth(rounds)
    ordinal_map = map_to_ordinal(growth)
    summary = {
        "schema": "nexus.beyond_omega.cycle9_meta_squared.v1",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_rounds": n_rounds,
        "inject_function": f"round_i * {INJECT_K} (linear-in-i super-cycle8 inject)",
        "back_action_env": "NEXUS_BACK_ACTION_ON=1",
        "rounds": rounds,
        "growth": growth,
        "ordinal_mapping": ordinal_map,
        "interpretation": interpret(growth, ordinal_map, rounds),
    }
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    print(f"⊙ cycle9_meta_squared n_rounds={n_rounds} growth={growth['type']}")
    if "delta_sequence" in growth:
        print(f"  delta seq: {growth['delta_sequence']}")
        print(f"  delta ratios: {growth.get('delta_ratio_sequence', [])}")
    print(f"  ordinal: {ordinal_map['ordinal']} — {ordinal_map['verdict']}")
    print(f"  out → {OUT.relative_to(REPO)}")
    print(f"  finding → {summary['interpretation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
