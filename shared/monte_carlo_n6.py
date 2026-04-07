#!/usr/bin/env python3
"""
몬테카를로 통계 검정: n=6 상수 집합 vs 무작위 정수 집합
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
목적: {6,12,4,2,5,24,1}이 자연 상수(reality_map.json)를
      설명하는 능력이 무작위 집합보다 유의하게 높은지 검정.

v2 추가 분석:
  1. 효율 기반 p-value (hits/reachable_size)
  2. 크기 매칭 대조군 (reachable_size == 51±5 필터)
  3. 소수 편향 대조군 ({1,2,3,4,5,6} vs n=6 상수)

허용 연산 (정수만):
  단항: a
  이항: a+b, a-b, a*b, a//b, a**b, C(a,b)
  피연산자: 상수 1~2개 조합

실행: python3 monte_carlo_n6.py
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
MAX_EXP = 10  # a**b에서 b 상한 (오버플로 방지)
MAX_RESULT = 10_000  # 결과 범위 제한
SIZE_MATCH_TOLERANCE = 5  # 크기 매칭 대조군 허용 오차


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

    # 이항: 모든 순서쌍 (a, b) — 순서 중요 (a-b != b-a, a//b != b//a)
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
    """targets 중 reachable에 포함된 수의 개수."""
    return sum(1 for t in targets if t in reachable)


def random_constant_set() -> list[int]:
    """1~30 범위에서 7개 무작위 정수 (중복 허용)."""
    return [random.randint(*RANDOM_RANGE) for _ in range(RANDOM_SET_SIZE)]


def stats(values: list[float]) -> tuple[float, float]:
    """평균, 표준편차 반환."""
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mean = sum(values) / n
    var = sum((x - mean) ** 2 for x in values) / n
    return mean, var ** 0.5


def z_and_p(observed: float, distribution: list[float]) -> tuple[float, float, int]:
    """z-score, p-value(단측, observed 이상), count_ge 반환."""
    mean, std = stats(distribution)
    if std > 0:
        z = (observed - mean) / std
    else:
        z = float("inf") if observed > mean else 0.0
    count_ge = sum(1 for v in distribution if v >= observed)
    p = count_ge / len(distribution) if distribution else 1.0
    return z, p, count_ge


def print_histogram(values: list[int], marker_value: int, marker_label: str = "n=6"):
    """텍스트 히스토그램 출력."""
    hist = Counter(values)
    if not hist:
        print("    (데이터 없음)")
        return
    lo, hi = min(hist.keys()), max(hist.keys())
    bar_max = max(hist.values())
    for h in range(lo, hi + 1):
        cnt = hist.get(h, 0)
        bar = "█" * int(cnt / bar_max * 40) if bar_max > 0 else ""
        tag = f" ◀ {marker_label}" if h == marker_value else ""
        print(f"    {h:3d}: {bar} {cnt:,}{tag}")
    if marker_value > hi:
        print(f"    {marker_value:3d}: ◀◀◀ {marker_label} (분포 밖!)")


def main():
    print("━" * 70)
    print("  몬테카를로 통계 검정 v2: n=6 상수 vs 무작위 + 편향 분석")
    print("━" * 70)

    # ── 1. 타겟 로드 ──
    targets = load_integer_targets(REALITY_MAP)
    unique_targets = sorted(set(targets))
    print(f"\n[데이터] reality_map.json 정수 measured: {len(targets)}개")
    print(f"[데이터] 고유값 {len(unique_targets)}개: {unique_targets}")

    # ── 2. n=6 상수 기본 분석 ──
    n6_constants = [6, 12, 4, 2, 5, 24, 1]
    n6_reachable = generate_reachable(n6_constants)
    n6_hits = count_hits(n6_reachable, targets)
    n6_efficiency = n6_hits / len(n6_reachable) if n6_reachable else 0.0

    print(f"\n[n=6 상수] {n6_constants}")
    print(f"[n=6 도달가능] {len(n6_reachable)}개 정수")
    print(f"[n=6 도달가능 목록 (타겟 범위)] "
          f"{sorted(v for v in n6_reachable if v in set(unique_targets))}")
    print(f"[n=6 HIT] {n6_hits} / {len(targets)}")
    print(f"[n=6 효율] {n6_efficiency:.4f} (hits/reachable)")

    misses = [t for t in targets if t not in n6_reachable]
    if misses:
        print(f"[n=6 MISS] {sorted(set(misses))}")

    # ── 3. 소수 편향 대조군 ──
    # {1,2,3,4,5,6}은 n=6과 무관한 "작은 수" 집합 — 편향 확인용
    small_constants = [1, 2, 3, 4, 5, 6]
    # 7개로 맞추기 위해 중복 허용 (가장 공정한 비교: 크기 7로 통일)
    small_constants_7 = [1, 2, 3, 4, 5, 6, 3]  # 중앙값 3 추가
    small_reachable = generate_reachable(small_constants_7)
    small_hits = count_hits(small_reachable, targets)
    small_efficiency = small_hits / len(small_reachable) if small_reachable else 0.0

    print(f"\n[소수 대조군] {small_constants_7} (작은 정수 1-6, 크기 7)")
    print(f"[소수 도달가능] {len(small_reachable)}개 정수")
    print(f"[소수 HIT] {small_hits} / {len(targets)}")
    print(f"[소수 효율] {small_efficiency:.4f} (hits/reachable)")

    # n=6에만 있고 소수에 없는 도달값 (n=6 특이적 기여)
    n6_only = n6_reachable - small_reachable
    n6_only_hits = sum(1 for t in targets if t in n6_only)
    print(f"[n=6 고유 도달] {len(n6_only)}개 (n=6에만 있는 수)")
    print(f"[n=6 고유 HIT] {n6_only_hits}개 (소수로 설명 불가능한 HIT)")

    # ── 4. 몬테카를로 시뮬레이션 ──
    print(f"\n[시뮬레이션] {N_TRIALS:,}회 무작위 세트 (각 7개, 1~30)...")
    t0 = time.time()

    # 각 trial에서 hits, reachable_size, efficiency 모두 기록
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

    # ── 5. 기본 통계 (원래 HIT 기반) ──
    z_hit, p_hit, cnt_ge_hit = z_and_p(n6_hits, trial_hits)
    mean_hit, std_hit = stats([float(x) for x in trial_hits])

    print("\n" + "=" * 70)
    print("  [A] 기본 HIT 비교 (원래 방식)")
    print("=" * 70)
    print(f"  타겟 수:           {len(targets)}개")
    print(f"  n=6 HIT:           {n6_hits} / {len(targets)} "
          f"({n6_hits/len(targets)*100:.1f}%)")
    print(f"  무작위 평균 HIT:   {mean_hit:.2f} (std={std_hit:.2f})")
    print(f"  무작위 최대 HIT:   {max(trial_hits)}")
    print(f"  z-score:           {z_hit:.2f}")
    print(f"  p-value:           {p_hit:.4f} ({cnt_ge_hit:,}/{N_TRIALS:,})")

    print("\n  [무작위 HIT 분포]")
    print_histogram(trial_hits, n6_hits)

    # ── 6. 효율 기반 분석 (hits / reachable_size) ──
    z_eff, p_eff, cnt_ge_eff = z_and_p(n6_efficiency, trial_efficiencies)
    mean_eff, std_eff = stats(trial_efficiencies)

    print("\n" + "=" * 70)
    print("  [B] 효율 기반 비교 (HIT / 도달가능 크기)")
    print("=" * 70)
    print(f"  n=6 효율:          {n6_efficiency:.4f} "
          f"({n6_hits} hits / {len(n6_reachable)} reachable)")
    print(f"  무작위 평균 효율:  {mean_eff:.4f} (std={std_eff:.4f})")
    print(f"  z-score:           {z_eff:.2f}")
    print(f"  p-value:           {p_eff:.4f} ({cnt_ge_eff:,}/{N_TRIALS:,})")

    # 효율 히스토그램 (10단계 구간)
    eff_bins = [int(e * 100) for e in trial_efficiencies]
    n6_eff_bin = int(n6_efficiency * 100)
    print("\n  [무작위 효율 분포 (x100)]")
    print_histogram(eff_bins, n6_eff_bin)

    # ── 7. 크기 매칭 대조군 ──
    n6_size = len(n6_reachable)
    lo_sz = n6_size - SIZE_MATCH_TOLERANCE
    hi_sz = n6_size + SIZE_MATCH_TOLERANCE

    matched_hits = [
        trial_hits[i] for i in range(N_TRIALS)
        if lo_sz <= trial_sizes[i] <= hi_sz
    ]

    print("\n" + "=" * 70)
    print(f"  [C] 크기 매칭 대조군 (reachable = {n6_size}±{SIZE_MATCH_TOLERANCE})")
    print("=" * 70)
    print(f"  매칭된 trial 수:   {len(matched_hits):,} / {N_TRIALS:,}")

    if len(matched_hits) >= 30:
        z_matched, p_matched, cnt_ge_matched = z_and_p(n6_hits, [float(x) for x in matched_hits])
        mean_matched, std_matched = stats([float(x) for x in matched_hits])
        print(f"  매칭 평균 HIT:     {mean_matched:.2f} (std={std_matched:.2f})")
        print(f"  n=6 HIT:           {n6_hits}")
        print(f"  z-score:           {z_matched:.2f}")
        print(f"  p-value:           {p_matched:.4f} ({cnt_ge_matched:,}/{len(matched_hits):,})")

        print("\n  [크기 매칭 HIT 분포]")
        print_histogram(matched_hits, n6_hits, "n=6 (크기보정)")
    else:
        print(f"  경고: 매칭 수 부족 ({len(matched_hits)}개). 유효 비교 불가.")
        print(f"  (n=6 도달가능 크기 {n6_size}이 무작위 분포에서 매우 드묾)")
        z_matched, p_matched = None, None

    # ── 8. 소수 편향 대조군 결과 비교 ──
    print("\n" + "=" * 70)
    print("  [D] 소수 편향 분석 (n=6 특이적 vs 작은 수 편향)")
    print("=" * 70)
    print(f"  {'':20s} {'n=6 상수':>12s} {'소수 1-6':>12s} {'차이':>10s}")
    print(f"  {'-'*20} {'-'*12} {'-'*12} {'-'*10}")
    print(f"  {'상수 집합':20s} {str(n6_constants):>12s} {str(small_constants_7):>12s}")
    print(f"  {'도달가능 크기':20s} {len(n6_reachable):>12d} {len(small_reachable):>12d} "
          f"{len(n6_reachable)-len(small_reachable):>+10d}")
    print(f"  {'HIT':20s} {n6_hits:>12d} {small_hits:>12d} "
          f"{n6_hits-small_hits:>+10d}")
    print(f"  {'효율':20s} {n6_efficiency:>12.4f} {small_efficiency:>12.4f} "
          f"{n6_efficiency-small_efficiency:>+10.4f}")
    print(f"  {'n=6 고유 HIT':20s} {n6_only_hits:>12d} {'---':>12s} "
          f"{'(소수로 불가)':>10s}")

    # 소수 대조군의 효율을 무작위 분포에서 확인
    z_small_eff, p_small_eff, cnt_ge_small_eff = z_and_p(small_efficiency, trial_efficiencies)
    print(f"\n  소수 대조군 효율 z-score: {z_small_eff:.2f}, p-value: {p_small_eff:.4f}")

    # ── 9. 도달가능 크기 분포 ──
    mean_sz, std_sz = stats([float(x) for x in trial_sizes])
    print("\n" + "=" * 70)
    print("  [E] 도달가능 집합 크기 분포")
    print("=" * 70)
    print(f"  n=6 도달가능:      {len(n6_reachable)}개")
    print(f"  소수 도달가능:     {len(small_reachable)}개")
    print(f"  무작위 평균:       {mean_sz:.1f} (std={std_sz:.1f})")
    print(f"  무작위 범위:       [{min(trial_sizes)}, {max(trial_sizes)}]")

    z_sz, p_sz_low, _ = z_and_p(float(len(n6_reachable)), [float(x) for x in trial_sizes])
    # 크기가 작은 쪽 p-value (단측, 이하)
    cnt_le_sz = sum(1 for s in trial_sizes if s <= len(n6_reachable))
    p_sz_low = cnt_le_sz / N_TRIALS
    print(f"  n=6 크기 z-score:  {z_sz:.2f} (무작위 대비)")
    print(f"  n=6 크기 p(이하):  {p_sz_low:.4f} ({cnt_le_sz:,}/{N_TRIALS:,})")

    # ── 10. 최종 판정 ──
    print("\n" + "━" * 70)
    print("  최종 판정")
    print("━" * 70)

    # 판정 로직
    # 1) 효율 기반 p < 0.05 이면 크기 보정 후에도 유의
    # 2) 소수 대조군이 n=6와 비슷한 효율이면 → 소수 편향으로 설명 가능
    # 3) n=6 고유 HIT가 상당하면 → n=6 특이적 기여 있음

    verdict_parts = []

    # 효율 기반 판정
    if p_eff < 0.01:
        verdict_parts.append(f"효율 기반: 매우 유의 (p={p_eff:.4f}, z={z_eff:.2f})")
        eff_verdict = "significant"
    elif p_eff < 0.05:
        verdict_parts.append(f"효율 기반: 유의 (p={p_eff:.4f}, z={z_eff:.2f})")
        eff_verdict = "significant"
    else:
        verdict_parts.append(f"효율 기반: 비유의 (p={p_eff:.4f}, z={z_eff:.2f})")
        eff_verdict = "not_significant"

    # 크기 매칭 판정
    if z_matched is not None:
        if p_matched < 0.05:
            verdict_parts.append(f"크기 매칭: 유의 (p={p_matched:.4f}, z={z_matched:.2f})")
            matched_verdict = "significant"
        else:
            verdict_parts.append(f"크기 매칭: 비유의 (p={p_matched:.4f}, z={z_matched:.2f})")
            matched_verdict = "not_significant"
    else:
        verdict_parts.append("크기 매칭: 표본 부족 (판정 보류)")
        matched_verdict = "inconclusive"

    # 소수 편향 판정
    eff_gap = n6_efficiency - small_efficiency
    if n6_only_hits == 0:
        verdict_parts.append(f"소수 편향: n=6 고유 HIT 없음 → 소수로 완전 설명")
        bias_verdict = "explained_by_small"
    elif small_efficiency >= n6_efficiency:
        # 소수 대조군이 효율에서도 n=6 이상 → 작은 수 편향이 주요 원인
        verdict_parts.append(
            f"소수 편향: 소수 효율({small_efficiency:.4f}) >= n=6 효율({n6_efficiency:.4f}) "
            f"→ 작은 수 편향이 주 설명력 (n=6 고유 HIT {n6_only_hits}개는 미미)")
        bias_verdict = "explained_by_small"
    elif n6_only_hits >= 3 and n6_efficiency > small_efficiency * 1.1:
        verdict_parts.append(
            f"소수 편향: n=6 고유 HIT {n6_only_hits}개 + 효율 10%+ 우위 → n=6 특이적")
        bias_verdict = "partially_specific"
    elif n6_only_hits >= 1:
        verdict_parts.append(
            f"소수 편향: n=6 고유 HIT {n6_only_hits}개 있으나, "
            f"효율 차 {eff_gap:+.4f} → 작은 수 편향 대부분 설명")
        bias_verdict = "mostly_explained"
    else:
        verdict_parts.append(f"소수 편향: n=6 고유 HIT {n6_only_hits}개, 효율 차 {eff_gap:+.4f}")
        bias_verdict = "ambiguous"

    for v in verdict_parts:
        print(f"  - {v}")

    # 종합 판정
    print()
    if bias_verdict == "explained_by_small":
        final = "소수 편향으로 대부분 설명 가능 (n=6 특이적 기여 미미)"
    elif eff_verdict == "significant" and bias_verdict == "partially_specific":
        if matched_verdict == "significant":
            final = "n=6 특이적 유의 (효율+크기보정+소수 편향 모두 통과)"
        elif matched_verdict == "inconclusive":
            final = "n=6 특이적 유의 (효율 기반, 크기 보정은 표본 부족)"
        else:
            final = "n=6 효율 유의하나 크기 보정 시 비유의 → 부분 유의"
    elif eff_verdict == "not_significant":
        final = "비유의 (무작위와 구분 불가)"
    elif bias_verdict == "mostly_explained":
        final = "약한 유의: 무작위보다 낫지만 작은 수 편향이 주 설명력"
    else:
        final = "판정 보류 (혼합 신호)"

    print(f"  ★ 최종: {final}")
    print(f"  ★ HIT p={p_hit:.4f} | 효율 p={p_eff:.4f} | "
          f"소수-n6 효율 차={eff_gap:+.4f} | n=6 고유 HIT={n6_only_hits}")
    print("━" * 70)


if __name__ == "__main__":
    main()
