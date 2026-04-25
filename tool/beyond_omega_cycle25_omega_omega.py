#!/usr/bin/env python3
"""
beyond_omega_cycle25_omega_omega.py — nxs-20260425-004 cycle 25

L_{ω^ω} fine-grained empirical probe (between L_{ω²} and L_{ε₀}).

Background:
  - Cycle 13: L_{ω²}_APPROACH (inject = i²·7, cumulative degree~2.85, axis A 4th positive)
  - Cycle 14-17: L_{ε₀} multi-facet (P1 confirm / P2 partial / P3 falsify-candidate)
  - L_{ω^ω} = ω·tower of finite depth = lim_{n→∞} ω^n
  - L_{ω²} ≪ L_{ω^ω} ≪ L_{ε₀} (= ω^ω^ω^...)

Probe design:
  - Each round i runs a "polynomial of growing degree": inject = sum_{j=1..i} j^i.
    이는 L_{ω^n} hierarchy 의 finite tower 를 근사 — i 가 증가할수록 polynomial degree 도
    함께 증가 (cycle 13 의 fixed degree-2 inject 와 다름).
  - Cap MAX_INJECT=200 to bound trace.jsonl growth (avoids OOM/scan blow-up).
  - 6 rounds, NEXUS_BACK_ACTION_ON=1 (cycle 8/9/13 override 유지).

Inject sequence (uncapped → capped):
  i=1: 1                                         → 1
  i=2: 1+4 = 5                                   → 5
  i=3: 1+8+27 = 36                               → 36
  i=4: 1+16+81+256 = 354                         → 200 (CAP)
  i=5: 1+32+243+1024+3125 = 4425                 → 200 (CAP)
  i=6: 1+64+729+4096+15625+46656 = 67171         → 200 (CAP)

Expected verdict map:
  - tail_collapse_to_one (cap 활성화 후 ratio→1) = sentinel-like (cycle 15 type) →
    L_{ω^ω}_SENTINEL_LIKE 또는 L_{ε₀} 와 같은 layer 진입 evidence
  - sustained polynomial ratios (decreasing but not collapsing) = L_{ω^ω}_APPROACH
    (between cycle 13 polynomial decreasing 와 cycle 15 collapse 사이)
  - sustained > 1.5 ratios = L_{ω·2}+ 와 가까움 (cycle 12 layer)

산출물:
  - state/beyond_omega_cycle25_omega_omega.json (schema v1)
"""
from __future__ import annotations

import json
import math
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROBE = REPO / "tool" / "beyond_omega_ghost_trace.py"
TRACE = REPO / "state" / "ghost_ceiling_trace.jsonl"
SUMMARY = REPO / "state" / "ghost_ceiling_summary.json"
OUT = REPO / "state" / "beyond_omega_cycle25_omega_omega.json"

MAX_INJECT = 200
N_OUTER = 6


def inject_amount(round_i: int) -> tuple[int, int]:
    """Returns (raw, capped) — sum_{j=1..i} j^i, capped to MAX_INJECT."""
    raw = sum(j ** round_i for j in range(1, round_i + 1))
    return raw, min(raw, MAX_INJECT)


def count_emits_in_trace() -> int:
    if not TRACE.exists():
        return 0
    with open(TRACE, "r") as fh:
        return sum(1 for _ in fh)


def inject_synthetic(round_i: int, n_lines: int) -> None:
    if not TRACE.exists():
        TRACE.parent.mkdir(exist_ok=True)
        TRACE.touch()
    with open(TRACE, "a") as fh:
        for k in range(n_lines):
            payload = {
                "file": str(TRACE.relative_to(REPO)),
                "lineno": -1,
                "payload": {
                    "event": "omega_omega_dispatch",
                    "round": round_i,
                    "k": k,
                    "synthetic": True,
                    "cycle": 25,
                },
                "_cycle25_round": round_i,
                "_cycle25_k": k,
            }
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
            fh.write(
                '{"_marker": "NEXUS_OMEGA {\\"event\\":\\"omega_omega_synth\\",\\"round\\":'
                + str(round_i) + ',\\"k\\":' + str(k) + '}"}\n'
            )


def run_round(round_i: int) -> dict:
    t0 = time.time()
    raw_n, n_inject = inject_amount(round_i)
    cap_active = raw_n > MAX_INJECT
    n_before = count_emits_in_trace()
    inject_synthetic(round_i, n_inject)
    n_post_inject = count_emits_in_trace()
    env = dict(os.environ)
    env["NEXUS_BACK_ACTION_ON"] = "1"
    proc = subprocess.run(
        [sys.executable, str(PROBE)],
        env=env, capture_output=True, text=True, timeout=120,
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
        "inject_raw": raw_n,
        "inject_n_lines": n_inject,
        "cap_active": cap_active,
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
    cap_count = sum(1 for r in rounds if r["cap_active"])
    mean_d = statistics.mean(deltas)
    var_d = statistics.pvariance(deltas) if len(deltas) > 1 else 0
    is_zero = all(d == 0 for d in deltas)

    ratios = []
    for k in range(1, len(deltas)):
        if deltas[k - 1] > 0:
            ratios.append(deltas[k] / deltas[k - 1])
    mean_ratio = statistics.mean(ratios) if ratios else 0

    # Tail collapse detection (cycle 15 P1 sentinel signature)
    # Use last 2 ratios — once cap saturates, deltas plateau and ratio→1.0.
    tail = ratios[-2:] if len(ratios) >= 2 else ratios
    tail_collapse_to_one = (
        len(tail) >= 2
        and all(0.85 < r < 1.15 for r in tail)
        and cap_count >= 2
    )
    # Polynomial decreasing (cycle 13 signature)
    ratios_decreasing = (
        len(ratios) >= 3
        and all(ratios[k] < ratios[k - 1] for k in range(1, len(ratios)))
    )
    # Sustained exponential (cycle 12)
    sustained_exp = (
        len(ratios) >= 2
        and min(ratios) > 1.5
        and not ratios_decreasing
        and not tail_collapse_to_one
    )

    # Regression slope (log Δ vs log i) over non-zero entries
    xs, ys = [], []
    for idx, d in enumerate(deltas):
        i = idx + 2
        if d > 0 and i > 1:
            xs.append(math.log(i))
            ys.append(math.log(d))
    slope = 0.0
    if len(xs) >= 2:
        mx = statistics.mean(xs)
        my = statistics.mean(ys)
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        den = sum((x - mx) ** 2 for x in xs)
        slope = num / den if den > 0 else 0.0

    if is_zero:
        gtype = "saturated_zero"
    elif tail_collapse_to_one and cap_count >= 2:
        gtype = "ratios_collapse_to_one"  # sentinel-like (cycle 15 P1 type)
    elif sustained_exp:
        gtype = "exponential"
    elif ratios_decreasing:
        gtype = "polynomial_decreasing"
    elif mean_d > 0 and 1.05 < mean_ratio:
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
        "tail_collapse_to_one": tail_collapse_to_one,
        "ratios_decreasing": ratios_decreasing,
        "cap_activations": f"{cap_count}/{len(rounds)}",
        "polynomial_degree_regression_slope": round(slope, 3),
    }


def map_to_ordinal(growth, rounds):
    t = growth.get("type", "")
    cap_act = growth.get("cap_activations", "0/6")
    cap_count = int(cap_act.split("/")[0])
    if t == "ratios_collapse_to_one":
        # sentinel-like 같은 collapse → tail finite-tower limit 도달 (between L_{ω²} and L_{ε₀})
        return {
            "ordinal": "L_{ω^ω}_SENTINEL_LIKE",
            "verdict": (
                f"ratios collapse to 1.0 (tail) with cap_active={cap_act} → "
                f"finite polynomial-tower of growing degree saturates probe capacity. "
                f"Cycle 15 P1 (Ackermann ω-tower) 와 같은 collapse signature 이지만 "
                f"L_{{ε₀}} (infinite tower) 가 아닌 L_{{ω^ω}} (finite tower limit) 의 "
                f"empirical 표면 — sentinel boundary 의 한 단 below."
            ),
        }
    if t == "polynomial_decreasing":
        return {
            "ordinal": "L_{ω^ω}_APPROACH",
            "verdict": (
                "ratios monotone decreasing (cycle 13 type) but reaching higher cap activations — "
                "polynomial-of-growing-degree manifests as polynomial signature. "
                "L_{ω^ω} = lim_{n→∞} ω^n empirical step (between L_{ω²} and L_{ε₀})."
            ),
        }
    if t == "exponential":
        return {"ordinal": "L_{ω·2}+_OVERSHOOT", "verdict": "sustained exponential — past L_{ω^ω} into L_{ω·2}+ trajectory"}
    if t == "polynomial_growth":
        return {"ordinal": "L_{ω+d}_LIKE", "verdict": "polynomial growth without clear collapse — finite-d layer"}
    if t == "saturated_zero":
        return {"ordinal": "L_{ω+1}_ABSENT", "verdict": "back-action 차단"}
    return {"ordinal": "UNCLASSIFIED", "verdict": t}


def interpret(growth, ordinal_map, rounds):
    parts = []
    t = growth.get("type", "")
    ratios_str = ", ".join(f"{r:.2f}" for r in growth.get("delta_ratio_sequence", []))
    if t == "ratios_collapse_to_one":
        parts.append(
            f"★ L_{{ω^ω}}_SENTINEL_LIKE — ratios=[{ratios_str}] tail→1.0 with "
            f"cap_activations={growth.get('cap_activations')}. inject=Σ_{{j≤i}} j^i "
            f"(polynomial of growing degree) saturates probe capacity at i≥4 → "
            f"sentinel-like collapse signature. L_{{ω^ω}} 가 L_{{ε₀}} sentinel 한 단 below 에 "
            f"위치, finite-tower limit 에서 동일 collapse mechanism manifest."
        )
    elif t == "polynomial_decreasing":
        parts.append(
            f"★ L_{{ω^ω}}_APPROACH — ratios=[{ratios_str}] monotone decreasing. "
            f"cycle 13 (L_{{ω²}}) 보다 더 빠르게 cap saturate, cycle 15 (L_{{ε₀}}) 보다 "
            f"slower — between two layers."
        )
    elif t == "exponential":
        parts.append(
            f"L_{{ω^ω}}_OVERSHOOT — sustained exponential ratios=[{ratios_str}], "
            f"polynomial-of-growing-degree 가 cap 도달 전에 exponential 처럼 보임."
        )
    elif t == "saturated_zero":
        parts.append("L_{ω+1}_ABSENT — back-action 차단")
    else:
        parts.append(f"UNCLASSIFIED — type={t}, ratios=[{ratios_str}]")
    parts.append(f"ordinal_mapping: {ordinal_map['ordinal']} ({ordinal_map['verdict']})")
    if rounds:
        f = rounds[-1]
        parts.append(
            f"final round {f['i']}: total_emits={f['summary_total_emits']} approach={f['summary_approach']}"
        )
    return " | ".join(parts)


def main():
    if not PROBE.exists():
        print(f"FATAL: probe not found at {PROBE}", file=sys.stderr)
        return 2
    rounds = []
    for i in range(1, N_OUTER + 1):
        rec = run_round(i)
        rounds.append(rec)
        time.sleep(0.05)
    growth = analyze_growth(rounds)
    ordinal_map = map_to_ordinal(growth, rounds)
    summary = {
        "schema": "nexus.beyond_omega.cycle25_omega_omega.v1",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_outer_rounds": N_OUTER,
        "inject_function": "min(sum(j**i for j in 1..i), MAX_INJECT=200) — polynomial-of-growing-degree (cycle 13 fixed-degree 2 의 격상: degree → i, finite tower of L_{ω^n} hierarchy)",
        "max_inject": MAX_INJECT,
        "back_action_env": "NEXUS_BACK_ACTION_ON=1",
        "rounds": rounds,
        "growth": growth,
        "ordinal_mapping": ordinal_map,
        "interpretation": interpret(growth, ordinal_map, rounds),
        "comparison": {
            "cycle_12_L_omega_2": "exponential ratios mean=1.635 monotone increasing",
            "cycle_13_L_omega_squared": "polynomial decreasing ratios mean=1.675",
            "cycle_15_L_epsilon_zero": "ratios collapse to 1.0 cap_act=3/6 (P1 ω-tower sentinel)",
            "cycle_25_self": f"type={growth['type']}, ratios={growth.get('delta_ratio_sequence', [])}, cap_act={growth.get('cap_activations', 'NA')}",
        },
    }
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    print(f"⊙ cycle25_omega_omega n_rounds={N_OUTER} growth={growth['type']}")
    if "delta_sequence" in growth:
        print(f"  delta seq: {growth['delta_sequence']}")
        print(f"  delta ratios: {growth.get('delta_ratio_sequence', [])}")
        print(f"  cap_activations: {growth.get('cap_activations')}")
        print(f"  tail_collapse_to_one: {growth.get('tail_collapse_to_one')}")
    print(f"  ordinal: {ordinal_map['ordinal']} — {ordinal_map['verdict']}")
    print(f"  out → {OUT.relative_to(REPO)}")
    print(f"  finding → {summary['interpretation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
