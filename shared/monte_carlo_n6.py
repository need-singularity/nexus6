#!/usr/bin/env python3
"""
몬테카를로 통계 검정: n=6 상수 집합 vs 무작위 정수 집합
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
목적: {6,12,4,2,5,24,1}이 자연 상수(reality_map.json)를
      설명하는 능력이 무작위 집합보다 유의하게 높은지 검정.

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
from itertools import combinations_with_replacement, permutations

# ── 설정 ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REALITY_MAP = os.path.join(SCRIPT_DIR, "reality_map.json")
N_TRIALS = 10_000
RANDOM_RANGE = (1, 30)
RANDOM_SET_SIZE = 7
MAX_EXP = 10  # a**b에서 b 상한 (오버플로 방지)
MAX_RESULT = 10_000  # 결과 범위 제한


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


def count_hits(constants: list[int], targets: list[int]) -> int:
    """targets 중 constants로 도달 가능한 수의 개수."""
    reachable = generate_reachable(constants)
    return sum(1 for t in targets if t in reachable)


def random_constant_set() -> list[int]:
    """1~30 범위에서 7개 무작위 정수 (중복 허용)."""
    return [random.randint(*RANDOM_RANGE) for _ in range(RANDOM_SET_SIZE)]


def main():
    print("━" * 60)
    print("  몬테카를로 통계 검정: n=6 상수 vs 무작위 정수 집합")
    print("━" * 60)

    # 1. 타겟 로드
    targets = load_integer_targets(REALITY_MAP)
    unique_targets = sorted(set(targets))
    print(f"\n[데이터] reality_map.json 정수 measured: {len(targets)}개")
    print(f"[데이터] 고유값 {len(unique_targets)}개: {unique_targets}")

    # 2. n=6 상수 HIT
    n6_constants = [6, 12, 4, 2, 5, 24, 1]
    n6_reachable = generate_reachable(n6_constants)
    n6_hits = count_hits(n6_constants, targets)

    print(f"\n[n=6 상수] {n6_constants}")
    print(f"[n=6 도달가능] {len(n6_reachable)}개 정수")
    print(f"[n=6 도달가능 목록 (타겟 범위)] "
          f"{sorted(v for v in n6_reachable if v in set(unique_targets))}")
    print(f"[n=6 HIT] {n6_hits} / {len(targets)}")

    # 미스 분석
    misses = [t for t in targets if t not in n6_reachable]
    if misses:
        print(f"[n=6 MISS] {sorted(set(misses))}")

    # 3. 몬테카를로 시뮬레이션
    print(f"\n[시뮬레이션] {N_TRIALS:,}회 무작위 세트 (각 7개, 1~30)...")
    t0 = time.time()

    random_hits = []
    for i in range(N_TRIALS):
        rc = random_constant_set()
        h = count_hits(rc, targets)
        random_hits.append(h)
        if (i + 1) % 2000 == 0:
            elapsed = time.time() - t0
            print(f"  ... {i+1:,}/{N_TRIALS:,} ({elapsed:.1f}초)")

    elapsed = time.time() - t0
    print(f"  완료 ({elapsed:.1f}초)")

    # 4. 통계
    mean_rh = sum(random_hits) / len(random_hits)
    var_rh = sum((x - mean_rh) ** 2 for x in random_hits) / len(random_hits)
    std_rh = var_rh ** 0.5

    if std_rh > 0:
        z_score = (n6_hits - mean_rh) / std_rh
    else:
        z_score = float("inf") if n6_hits > mean_rh else 0.0

    # p-value: 무작위에서 n6_hits 이상 나올 확률 (단측)
    count_ge = sum(1 for h in random_hits if h >= n6_hits)
    p_value = count_ge / N_TRIALS

    # 5. 출력
    print("\n" + "=" * 60)
    print("  결과 요약")
    print("=" * 60)
    print(f"  타겟 수:           {len(targets)}개 (정수 measured)")
    print(f"  n=6 HIT:           {n6_hits} / {len(targets)}  "
          f"({n6_hits/len(targets)*100:.1f}%)")
    print(f"  무작위 평균 HIT:   {mean_rh:.2f} / {len(targets)}  "
          f"(std={std_rh:.2f})")
    print(f"  무작위 최대 HIT:   {max(random_hits)}")
    print(f"  z-score:           {z_score:.2f}")
    print(f"  p-value:           {p_value:.4f}  "
          f"(무작위 >= n6 비율, {N_TRIALS:,}회 중 {count_ge:,}회)")

    # 히스토그램 (텍스트)
    print("\n  [무작위 HIT 분포]")
    from collections import Counter
    hist = Counter(random_hits)
    max_h = max(hist.keys())
    min_h = min(hist.keys())
    bar_max = max(hist.values())
    for h in range(min_h, max_h + 1):
        cnt = hist.get(h, 0)
        bar = "█" * int(cnt / bar_max * 40) if bar_max > 0 else ""
        marker = " ◀ n=6" if h == n6_hits else ""
        print(f"    {h:3d}: {bar} {cnt:,}{marker}")
    if n6_hits > max_h:
        print(f"    {n6_hits:3d}: ◀◀◀ n=6 (분포 밖!)")

    print()
    if p_value < 0.01:
        conclusion = f"유의 (p={p_value:.4f} < 0.01, z={z_score:.2f})"
        print(f"  결론: ★ 통계적으로 매우 유의 ★")
    elif p_value < 0.05:
        conclusion = f"유의 (p={p_value:.4f} < 0.05, z={z_score:.2f})"
        print(f"  결론: ★ 통계적으로 유의 ★")
    else:
        conclusion = f"비유의 (p={p_value:.4f} >= 0.05, z={z_score:.2f})"
        print(f"  결론: 통계적으로 비유의 (무작위와 구분 불가)")

    print(f"  {conclusion}")
    print("=" * 60)

    # 6. 도달가능 집합 크기 비교
    random_reachable_sizes = []
    for _ in range(min(1000, N_TRIALS)):
        rc = random_constant_set()
        random_reachable_sizes.append(len(generate_reachable(rc)))
    mean_rs = sum(random_reachable_sizes) / len(random_reachable_sizes)
    print(f"\n  [참고] n=6 도달가능 집합 크기: {len(n6_reachable)}")
    print(f"  [참고] 무작위 도달가능 평균:   {mean_rs:.1f}")
    print(f"  → 도달가능 크기 차이가 HIT 차이를 설명하는지 확인 필요")

    # 도달가능 크기 보정 비교
    n6_efficiency = n6_hits / len(n6_reachable) if len(n6_reachable) > 0 else 0
    # 무작위 효율: 각 trial의 hits/reachable_size
    print(f"  [참고] n=6 효율 (HIT/도달가능): {n6_efficiency:.4f}")


if __name__ == "__main__":
    main()
