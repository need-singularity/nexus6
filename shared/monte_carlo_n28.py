#!/usr/bin/env python3
"""
몬테카를로 통계 검정: n=6 vs n=28 vs 소수 vs 무작위
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
목적: 두 번째 완전수 n=28의 산술함수로 reality_map.json 타겟을
      매핑하면 n=6과 비교해 얼마나 맞는지 통계 검정.

n=6  상수: sigma=12, tau=4, phi=2, sopfr=5, J2=24, mu=1
n=28 상수: sigma=56, tau=6, phi=12, sopfr=11, J2=576, mu=0

허용 연산 (정수만): a, a+b, a-b, a*b, a//b, a**b, C(a,b)
피연산자: 상수 1~2개 조합

실행: python3 monte_carlo_n28.py
"""

import json
import os
import random
import math
import time
from collections import Counter

# ── 설정 ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REALITY_MAP = os.path.join(SCRIPT_DIR, "reality_map.json")
N_TRIALS = 10_000
RANDOM_RANGE = (1, 30)
RANDOM_SET_SIZE = 7
MAX_EXP = 10
MAX_RESULT = 10_000
SIZE_MATCH_TOLERANCE = 5


def load_integer_targets(path: str) -> list[int]:
    """reality_map.json에서 정수 measured 값만 추출."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    targets = []
    for node in data.get("nodes", []):
        m = node.get("measured")
        if isinstance(m, int):
            targets.append(m)
        elif isinstance(m, float) and m == int(m) and m > 0:
            targets.append(int(m))
    return targets


def comb(a: int, b: int) -> int | None:
    """이항계수 C(a, b). 불가능하면 None."""
    if b < 0 or a < 0 or b > a:
        return None
    try:
        return math.comb(a, b)
    except (ValueError, OverflowError):
        return None


def generate_reachable(constants: list[int]) -> set[int]:
    """상수 1~2개 조합으로 도달 가능한 정수 집합 생성."""
    reachable = set()

    # 단항: 상수 자체
    for a in constants:
        if 0 < a <= MAX_RESULT:
            reachable.add(a)

    # 이항: 모든 순서쌍 (a, b)
    for a in constants:
        for b in constants:
            # a + b
            r = a + b
            if 0 < r <= MAX_RESULT:
                reachable.add(r)

            # a - b
            r = a - b
            if 0 < r <= MAX_RESULT:
                reachable.add(r)

            # a * b
            r = a * b
            if 0 < r <= MAX_RESULT:
                reachable.add(r)

            # a // b (정수 나눗셈, 나머지 0일 때만)
            if b != 0 and a % b == 0:
                r = a // b
                if 0 < r <= MAX_RESULT:
                    reachable.add(r)

            # a ** b (오버플로 방지)
            if 0 < b <= MAX_EXP and a > 0:
                try:
                    r = a ** b
                    if 0 < r <= MAX_RESULT:
                        reachable.add(r)
                except (OverflowError, MemoryError):
                    pass

            # C(a, b) 이항계수
            c = comb(a, b)
            if c is not None and 0 < c <= MAX_RESULT:
                reachable.add(c)

    return reachable


def count_hits(reachable: set[int], targets: list[int]) -> int:
    return sum(1 for t in targets if t in reachable)


def random_constant_set() -> list[int]:
    return [random.randint(*RANDOM_RANGE) for _ in range(RANDOM_SET_SIZE)]


def stats(values: list[float]) -> tuple[float, float]:
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mean = sum(values) / n
    var = sum((x - mean) ** 2 for x in values) / n
    return mean, var ** 0.5


def z_and_p(observed: float, distribution: list[float]) -> tuple[float, float, int]:
    mean, std = stats(distribution)
    if std > 0:
        z = (observed - mean) / std
    else:
        z = float("inf") if observed > mean else 0.0
    count_ge = sum(1 for v in distribution if v >= observed)
    p = count_ge / len(distribution) if distribution else 1.0
    return z, p, count_ge


def print_histogram(values: list[int], markers: dict[int, str] | None = None):
    """텍스트 히스토그램. markers = {value: label}."""
    if markers is None:
        markers = {}
    hist = Counter(values)
    if not hist:
        print("    (데이터 없음)")
        return
    lo, hi = min(hist.keys()), max(hist.keys())
    # 마커가 범위 밖이면 확장
    for mv in markers:
        lo = min(lo, mv)
        hi = max(hi, mv)
    bar_max = max(hist.values()) if hist else 1
    for h in range(lo, hi + 1):
        cnt = hist.get(h, 0)
        bar = "█" * int(cnt / bar_max * 40) if bar_max > 0 else ""
        tag = ""
        if h in markers:
            tag = f" ◀ {markers[h]}"
        print(f"    {h:3d}: {bar} {cnt:,}{tag}")


def analyze_set(name: str, constants: list[int], targets: list[int]):
    """상수 집합 분석 → (reachable, hits, efficiency) 반환."""
    reachable = generate_reachable(constants)
    hits = count_hits(reachable, targets)
    eff = hits / len(reachable) if reachable else 0.0
    return reachable, hits, eff


def main():
    print("━" * 72)
    print("  몬테카를로 통계 검정: n=6 vs n=28 vs 소수 vs 무작위")
    print("  두 번째 완전수 n=28이 자연 상수를 설명하는 능력 비교")
    print("━" * 72)

    # ── 1. 타겟 로드 ──
    targets = load_integer_targets(REALITY_MAP)
    unique_targets = sorted(set(targets))
    print(f"\n[데이터] reality_map.json 정수 measured: {len(targets)}개")
    print(f"[데이터] 고유값 {len(unique_targets)}개: {unique_targets}")

    # ── 2. 4개 상수 집합 정의 ──
    sets = {
        "n=6":  [6, 12, 4, 2, 5, 24, 1],
        "n=28": [28, 56, 6, 12, 11, 576, 0],
        "소수":  [1, 2, 3, 4, 5, 6, 3],   # 작은 정수 대조군
    }

    # mu=0 주의: 0은 상수 자체로는 무효(>0 조건), 연산 피연산자로만 작용
    # 0**b=0 (무효), a**0=1, a+0=a, a-0=a, a*0=0 (무효), a//0 불가, C(a,0)=1
    # → n=28의 mu=0은 사실상 "상수 자체 기여 없음"

    results = {}
    for name, consts in sets.items():
        reachable, hits, eff = analyze_set(name, consts, targets)
        results[name] = {
            "constants": consts,
            "reachable": reachable,
            "hits": hits,
            "efficiency": eff,
        }
        print(f"\n[{name}] 상수: {consts}")
        print(f"  도달가능: {len(reachable)}개")
        print(f"  HIT: {hits} / {len(targets)}")
        print(f"  효율: {eff:.4f}")
        # 타겟 중 맞춘 것
        hit_targets = sorted(t for t in set(targets) if t in reachable)
        miss_targets = sorted(t for t in set(targets) if t not in reachable)
        print(f"  맞춘 타겟: {hit_targets}")
        if miss_targets:
            print(f"  놓친 타겟: {miss_targets}")

    # ── 3. 집합 간 교차 분석 ──
    r6 = results["n=6"]["reachable"]
    r28 = results["n=28"]["reachable"]

    only_n6 = r6 - r28
    only_n28 = r28 - r6
    both = r6 & r28

    # 타겟 기준 교차
    t_set = set(targets)
    hit_only_n6 = sorted(t for t in t_set if t in only_n6)
    hit_only_n28 = sorted(t for t in t_set if t in only_n28)
    hit_both = sorted(t for t in t_set if t in both)

    print("\n" + "=" * 72)
    print("  [교차 분석] n=6 vs n=28 도달가능 집합")
    print("=" * 72)
    print(f"  n=6에만 도달:   {len(only_n6)}개")
    print(f"  n=28에만 도달:  {len(only_n28)}개")
    print(f"  양쪽 모두:      {len(both)}개")
    print(f"\n  타겟 중 n=6에만 맞춘:   {hit_only_n6}")
    print(f"  타겟 중 n=28에만 맞춘:  {hit_only_n28}")
    print(f"  타겟 중 양쪽 모두:      {hit_both}")

    # ── 4. 몬테카를로 시뮬레이션 ──
    print(f"\n[시뮬레이션] {N_TRIALS:,}회 무작위 세트 (각 7개, 1~30)...")
    t0 = time.time()

    trial_hits = []
    trial_sizes = []
    trial_efficiencies = []

    for i in range(N_TRIALS):
        rc = random_constant_set()
        reach = generate_reachable(rc)
        h = count_hits(reach, targets)
        sz = len(reach)
        eff = h / sz if sz > 0 else 0.0

        trial_hits.append(h)
        trial_sizes.append(sz)
        trial_efficiencies.append(eff)

        if (i + 1) % 2000 == 0:
            elapsed = time.time() - t0
            print(f"  ... {i+1:,}/{N_TRIALS:,} ({elapsed:.1f}초)")

    elapsed = time.time() - t0
    print(f"  완료 ({elapsed:.1f}초)")

    # ── 5. 통계 계산 ──
    mean_hit, std_hit = stats([float(x) for x in trial_hits])
    mean_sz, std_sz = stats([float(x) for x in trial_sizes])
    mean_eff, std_eff = stats(trial_efficiencies)

    # 각 집합별 z-score
    stat_results = {}
    for name in ["n=6", "n=28", "소수"]:
        r = results[name]
        z_h, p_h, cnt_h = z_and_p(float(r["hits"]), [float(x) for x in trial_hits])
        z_e, p_e, cnt_e = z_and_p(r["efficiency"], trial_efficiencies)
        stat_results[name] = {
            "z_hit": z_h, "p_hit": p_h,
            "z_eff": z_e, "p_eff": p_e,
        }

    # ── 6. 4종 비교 테이블 ──
    print("\n" + "━" * 72)
    print("  4종 비교 테이블")
    print("━" * 72)

    header = f"  {'집합':8s} {'상수':30s} {'도달':>6s} {'HIT':>5s} {'효율':>8s} {'z(HIT)':>8s} {'z(효율)':>8s} {'p(HIT)':>8s}"
    print(header)
    print("  " + "-" * 100)

    for name in ["n=6", "n=28", "소수"]:
        r = results[name]
        s = stat_results[name]
        cstr = str(r["constants"])
        print(f"  {name:8s} {cstr:30s} {len(r['reachable']):>6d} {r['hits']:>5d} "
              f"{r['efficiency']:>8.4f} {s['z_hit']:>8.2f} {s['z_eff']:>8.2f} {s['p_hit']:>8.4f}")

    # 무작위 행
    print(f"  {'무작위':8s} {'(1~30, 7개)':30s} {mean_sz:>6.0f} {mean_hit:>5.1f} "
          f"{mean_eff:>8.4f} {'0.00':>8s} {'0.00':>8s} {'---':>8s}")

    # ── 7. HIT 분포 히스토그램 ──
    print("\n" + "=" * 72)
    print("  [HIT 분포] 무작위 10,000회 vs 각 집합")
    print("=" * 72)
    markers = {}
    for name in ["n=6", "n=28", "소수"]:
        h = results[name]["hits"]
        markers[h] = markers.get(h, "") + ("+" if markers.get(h) else "") + name
    print_histogram(trial_hits, markers)

    # ── 8. 효율 분포 ──
    print("\n" + "=" * 72)
    print("  [효율 분포 (x100)] 무작위 vs 각 집합")
    print("=" * 72)
    eff_bins = [int(e * 100) for e in trial_efficiencies]
    eff_markers = {}
    for name in ["n=6", "n=28", "소수"]:
        eb = int(results[name]["efficiency"] * 100)
        eff_markers[eb] = eff_markers.get(eb, "") + ("+" if eff_markers.get(eb) else "") + name
    print_histogram(eff_bins, eff_markers)

    # ── 9. n=28 고유 분석 ──
    print("\n" + "=" * 72)
    print("  [n=28 고유 분석]")
    print("=" * 72)

    # n=28 상수 중 n=6과 겹치는 것
    n6c = set(sets["n=6"])
    n28c = set(sets["n=28"])
    overlap_consts = n6c & n28c
    print(f"  상수 겹침: {sorted(overlap_consts)} ({len(overlap_consts)}개)")
    print(f"  n=6에만:   {sorted(n6c - n28c)}")
    print(f"  n=28에만:  {sorted(n28c - n6c)}")

    # n=28 특이사항: mu=0, J2=576 (매우 큼)
    print(f"\n  n=28 특이사항:")
    print(f"    mu(28) = 0: 뫼비우스 함수 0 (28=2^2*7, 제곱인수)")
    print(f"    J2(28) = 576: 매우 큰 값 → 도달가능 집합 팽창")
    print(f"    sigma(28) = 56: n=6의 sigma=12보다 ~5배")
    print(f"    n=28 도달가능 크기: {len(r28)} vs n=6: {len(r6)} "
          f"(비율: {len(r28)/len(r6):.2f}배)")

    # ── 10. 크기 보정 비교 ──
    # n=28은 도달가능이 훨씬 크므로, 효율 비교가 더 공정
    print("\n" + "=" * 72)
    print("  [크기 보정 분석]")
    print("=" * 72)
    for name in ["n=6", "n=28"]:
        r = results[name]
        sz = len(r["reachable"])
        lo_sz = sz - SIZE_MATCH_TOLERANCE
        hi_sz = sz + SIZE_MATCH_TOLERANCE
        matched = [(trial_hits[i], trial_sizes[i])
                    for i in range(N_TRIALS)
                    if lo_sz <= trial_sizes[i] <= hi_sz]
        print(f"\n  [{name}] 도달가능 크기 = {sz}, 매칭 trial = {len(matched)}")
        if len(matched) >= 30:
            matched_hits = [m[0] for m in matched]
            z_m, p_m, cnt_m = z_and_p(float(r["hits"]), [float(x) for x in matched_hits])
            mean_m, std_m = stats([float(x) for x in matched_hits])
            print(f"  매칭 평균 HIT: {mean_m:.2f} (std={std_m:.2f})")
            print(f"  {name} HIT: {r['hits']}")
            print(f"  z-score: {z_m:.2f}, p-value: {p_m:.4f}")
        else:
            print(f"  매칭 부족 ({len(matched)}개) — 도달가능 크기가 무작위 분포에서 드묾")

    # ── 11. 최종 판정 ──
    print("\n" + "━" * 72)
    print("  최종 판정: n=6 vs n=28")
    print("━" * 72)

    r6_res = results["n=6"]
    r28_res = results["n=28"]
    s6 = stat_results["n=6"]
    s28 = stat_results["n=28"]

    print(f"\n  지표               n=6          n=28         우위")
    print(f"  {'─'*60}")
    print(f"  HIT               {r6_res['hits']:>5d}        {r28_res['hits']:>5d}        "
          f"{'n=6' if r6_res['hits'] > r28_res['hits'] else 'n=28' if r28_res['hits'] > r6_res['hits'] else '동률'}")
    print(f"  도달가능 크기       {len(r6):>5d}        {len(r28):>5d}        "
          f"{'n=6 (작음=효율적)' if len(r6) < len(r28) else 'n=28 (작음)'}")
    print(f"  효율 (HIT/도달)    {r6_res['efficiency']:>8.4f}    {r28_res['efficiency']:>8.4f}    "
          f"{'n=6' if r6_res['efficiency'] > r28_res['efficiency'] else 'n=28'}")
    print(f"  z-score (HIT)     {s6['z_hit']:>8.2f}    {s28['z_hit']:>8.2f}    "
          f"{'n=6' if s6['z_hit'] > s28['z_hit'] else 'n=28'}")
    print(f"  z-score (효율)    {s6['z_eff']:>8.2f}    {s28['z_eff']:>8.2f}    "
          f"{'n=6' if s6['z_eff'] > s28['z_eff'] else 'n=28'}")
    print(f"  p-value (HIT)     {s6['p_hit']:>8.4f}    {s28['p_hit']:>8.4f}    "
          f"{'n=6' if s6['p_hit'] < s28['p_hit'] else 'n=28'}")

    # n=6에만 맞추고 n=28은 못 맞추는 타겟
    print(f"\n  n=6에만 HIT (n=28 MISS): {hit_only_n6}")
    print(f"  n=28에만 HIT (n=6 MISS): {hit_only_n28}")
    print(f"  양쪽 모두 HIT:           {hit_both}")

    # 종합 결론
    print(f"\n  {'─'*60}")

    n6_wins = 0
    n28_wins = 0
    if r6_res["hits"] > r28_res["hits"]:
        n6_wins += 1
    elif r28_res["hits"] > r6_res["hits"]:
        n28_wins += 1
    if r6_res["efficiency"] > r28_res["efficiency"]:
        n6_wins += 1
    elif r28_res["efficiency"] > r6_res["efficiency"]:
        n28_wins += 1
    if s6["z_hit"] > s28["z_hit"]:
        n6_wins += 1
    elif s28["z_hit"] > s6["z_hit"]:
        n28_wins += 1
    if s6["z_eff"] > s28["z_eff"]:
        n6_wins += 1
    elif s28["z_eff"] > s6["z_eff"]:
        n28_wins += 1

    print(f"  스코어: n=6 {n6_wins}승 vs n=28 {n28_wins}승 (4개 지표)")

    if n6_wins > n28_wins:
        print(f"\n  결론: n=6이 n=28보다 자연 상수 매핑에서 우수.")
        print(f"  이유: 첫 번째 완전수 n=6의 산술함수(sigma=12, tau=4, phi=2,")
        print(f"        sopfr=5, J2=24, mu=1)가 더 작고 밀도 높은 도달 집합을")
        print(f"        생성하여, 자연에서 관측되는 정수 상수들과 더 효율적으로 일치.")
    elif n28_wins > n6_wins:
        print(f"\n  결론: n=28이 n=6보다 자연 상수 매핑에서 우수 또는 동등.")
        print(f"  완전수의 크기가 클수록 도달가능 집합이 커져 HIT가 많을 수 있으나,")
        print(f"  효율(HIT/도달크기) 비교가 더 공정한 지표.")
    else:
        print(f"\n  결론: n=6과 n=28이 동등 (각 지표에서 엇갈림).")
        print(f"  그러나 n=6의 상수들이 더 작아 '작은 수 편향'과의 분리가")
        print(f"  핵심 과제. 효율 지표 중심으로 판단 필요.")

    print("━" * 72)


if __name__ == "__main__":
    main()
