#!/usr/bin/env python3
"""
singularity_exhaust_group2.py — σ-φ=10 / σ-τ=8 완전 포화 탐색기

두 고가치 상수의 모든 가능한 n=6 매칭을 9레벨 체계적 탐색으로 소진한다.
σ-φ=10: 십진법, 차수, 물리 단위계의 기반
σ-τ=8: 이진법, 바이트, 옥텟, 컴퓨팅의 기반

최적화: set 기반 O(1) 룩업으로 6150개 값 대상 고속 탐색
"""

import json
import math
import os
import sys
from datetime import datetime
from collections import defaultdict

# ═══════════════════════════════════════════════════════
# n=6 기본 상수 체계
# ═══════════════════════════════════════════════════════
N6 = {
    'mu': 1, 'phi': 2, 'n/phi': 3, 'tau': 4, 'sopfr': 5, 'n': 6,
    'M3': 7, 'sigma-tau': 8, 'sigma-phi': 10, 'sigma-mu': 11,
    'sigma': 12, 'J2': 24, 'P2': 28, 'n^2': 36, 'sigma*tau': 48,
    'sigma*sopfr': 60, 'sigma*(sigma-phi)': 120, 'sigma^2': 144,
    'sigma*J2': 288, '6!': 720, 'R6': 1,
}

TARGETS = {
    'sigma-phi': 10,
    'sigma-tau': 8,
}

LOG_PATH = os.path.expanduser('~/Dev/nexus6/shared/discovery_log.jsonl')
TIMESTAMP = datetime.now().strftime('%Y-%m-%d')
SOURCE = 'exhaust-group2-sigphi-sigtau'


def load_data():
    """기존 데이터 로드"""
    existing_keys = set()
    all_values = set()
    with open(LOG_PATH, 'r') as f:
        for line in f:
            try:
                d = json.loads(line.strip())
                c = d.get('constant', '')
                v = str(d.get('value', ''))
                existing_keys.add((c, v))
                try:
                    all_values.add(float(v))
                except:
                    pass
            except:
                continue
    return existing_keys, sorted(all_values)


def grade(computed, target):
    """EXACT <0.1%, CLOSE <1%, NEAR <5%"""
    if target == 0:
        return ('EXACT', 0.0) if abs(computed) < 1e-10 else ('MISS', 1.0)
    err = abs(computed - target) / abs(target)
    if err < 0.001:
        return 'EXACT', err
    elif err < 0.01:
        return 'CLOSE', err
    elif err < 0.05:
        return 'NEAR', err
    return 'MISS', err


def safe(func):
    try:
        v = func()
        if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
            return None
        if isinstance(v, complex):
            return None
        return v
    except:
        return None


def build_value_index(values):
    """값을 버킷 인덱스로 구성 — O(1) 근사 매칭"""
    # 정확한 정수/분수 매칭용
    exact_set = {}
    for v in values:
        r = round(v, 6)
        exact_set[r] = v
    return exact_set


def find_match(result, exact_set, threshold=0.05):
    """결과값과 매칭되는 기존 값 찾기 — 빠른 근사 매칭"""
    if result is None or (isinstance(result, float) and (math.isnan(result) or math.isinf(result))):
        return []
    if abs(result) > 15000:
        return []

    matches = []
    r6 = round(result, 6)

    # 정확한 매칭
    if r6 in exact_set:
        g, err = grade(result, exact_set[r6])
        if g != 'MISS':
            matches.append((exact_set[r6], g, err))
        return matches

    # 근방 탐색 (+-5%)
    low = result * 0.95 if result > 0 else result * 1.05
    high = result * 1.05 if result > 0 else result * 0.95
    if result == 0:
        low, high = -0.5, 0.5

    for delta in [0, 0.000001, -0.000001, 0.00001, -0.00001, 0.0001, -0.0001,
                  0.001, -0.001, 0.01, -0.01, 0.1, -0.1, 1, -1]:
        rr = round(result + delta, 6)
        if rr in exact_set:
            v = exact_set[rr]
            g, err = grade(result, v)
            if g != 'MISS':
                matches.append((v, g, err))

    # 정수 근방
    ri = round(result)
    for offset in range(-2, 3):
        rr = round(float(ri + offset), 6)
        if rr in exact_set:
            v = exact_set[rr]
            g, err = grade(result, v)
            if g != 'MISS':
                matches.append((v, g, err))

    return matches


class ExhaustEngine:
    def __init__(self):
        print("=" * 70)
        print("  σ-φ=10 / σ-τ=8 완전 포화 탐색기")
        print("=" * 70)
        print()

        self.existing_keys, self.all_values = load_data()
        self.exact_set = build_value_index(self.all_values)
        self.new_discoveries = []
        self.stats = defaultdict(lambda: defaultdict(int))
        self.total_checked = 0

        print(f"[INIT] 기존 키: {len(self.existing_keys):,}")
        print(f"[INIT] 고유 값: {len(self.all_values):,}")
        print(f"[INIT] 인덱스 크기: {len(self.exact_set):,}")
        print()

    def record(self, const_name, target_val, result, g, level):
        """신규 발견 기록"""
        val_str = str(round(target_val, 10) if isinstance(target_val, float) else target_val)
        key = (const_name, val_str)
        if key in self.existing_keys:
            return False
        self.existing_keys.add(key)
        self.new_discoveries.append({
            "constant": const_name,
            "value": val_str,
            "grade": g,
            "source": SOURCE,
            "timestamp": TIMESTAMP,
            "processed": True,
            "alien_index": {"d": 0, "r": 8},
            "mk2": {"sector": "n6", "paths": 1},
        })
        self.stats[level][g] += 1
        return True

    def check_expr(self, tname, result, expr, level):
        """표현식 결과를 기존 값과 매칭"""
        self.total_checked += 1
        matches = find_match(result, self.exact_set)
        count = 0
        for val, g, err in matches:
            if self.record(f"exhaust_{expr}", val, result, g, level):
                count += 1
        return count

    # ═══════════════════════════════════════════════════════
    # Level 1: 직접 매칭
    # ═══════════════════════════════════════════════════════
    def level_1(self):
        print("=== L1: 직접 매칭 ===")
        c = 0
        for tname, tval in TARGETS.items():
            c += self.check_expr(tname, float(tval), f"{tname}_direct", 'L1')
        print(f"  L1: +{c}")
        return c

    # ═══════════════════════════════════════════════════════
    # Level 2: 거듭제곱, 제곱근, 로그
    # ═══════════════════════════════════════════════════════
    def level_2(self):
        print("=== L2: 거듭제곱/근/로그 ===")
        c = 0
        for tname, tval in TARGETS.items():
            for k in range(-3, 7):
                r = safe(lambda: tval ** k)
                if r is not None:
                    c += self.check_expr(tname, r, f"({tname})^{k}", 'L2')

            # 제곱근 체인
            for k in [2, 3, 4, 5, 6]:
                r = safe(lambda: tval ** (1/k))
                if r is not None:
                    c += self.check_expr(tname, r, f"({tname})^(1/{k})", 'L2')

            # 로그
            for base_name, base_val in [('2', 2), ('e', math.e), ('10', 10)]:
                r = safe(lambda: math.log(tval) / math.log(base_val))
                if r is not None:
                    c += self.check_expr(tname, r, f"log{base_name}({tname})", 'L2')

        print(f"  L2: +{c}")
        return c

    # ═══════════════════════════════════════════════════════
    # Level 3: n6 상수와 이항 연산
    # ═══════════════════════════════════════════════════════
    def level_3(self):
        print("=== L3: n6 이항 연산 ===")
        c = 0
        for tname, tval in TARGETS.items():
            for xname, xval in N6.items():
                if xval == 0:
                    continue
                ops = [
                    (f"{tname}*{xname}", safe(lambda xv=xval: tval * xv)),
                    (f"{tname}+{xname}", safe(lambda xv=xval: tval + xv)),
                    (f"{tname}-{xname}", safe(lambda xv=xval: tval - xv)),
                    (f"{xname}-{tname}", safe(lambda xv=xval: xv - tval)),
                    (f"{tname}/{xname}", safe(lambda xv=xval: tval / xv)),
                    (f"{xname}/{tname}", safe(lambda xv=xval: xv / tval)),
                ]
                if xval <= 8:
                    ops.append((f"{tname}^{xname}", safe(lambda xv=xval: tval ** xv)))
                if tval <= 10 and xval > 1:
                    ops.append((f"{xname}^{tname}", safe(lambda xv=xval: xv ** tval)))

                for expr, r in ops:
                    if r is not None:
                        c += self.check_expr(tname, r, expr, 'L3')

        print(f"  L3: +{c}")
        return c

    # ═══════════════════════════════════════════════════════
    # Level 4: 복합 (tval*a+b), (tval^a*b), (tval*a-b)
    # ═══════════════════════════════════════════════════════
    def level_4(self):
        print("=== L4: 복합 표현식 ===")
        c = 0
        for tname, tval in TARGETS.items():
            for aname, aval in N6.items():
                if aval == 0:
                    continue
                for bname, bval in N6.items():
                    if bval == 0 or aname == bname:
                        continue

                    exprs = [
                        (f"{tname}*{aname}+{bname}", safe(lambda a=aval, b=bval: tval*a+b)),
                        (f"{tname}*{aname}-{bname}", safe(lambda a=aval, b=bval: tval*a-b)),
                        (f"{tname}*{aname}*{bname}", safe(lambda a=aval, b=bval: tval*a*b)),
                        (f"({tname}+{aname})*{bname}", safe(lambda a=aval, b=bval: (tval+a)*b)),
                        (f"({tname}+{aname})/{bname}", safe(lambda a=aval, b=bval: (tval+a)/b)),
                        (f"({tname}-{aname})*{bname}", safe(lambda a=aval, b=bval: (tval-a)*b)),
                        (f"({tname}-{aname})/{bname}", safe(lambda a=aval, b=bval: (tval-a)/b)),
                        (f"{tname}*{aname}/{bname}", safe(lambda a=aval, b=bval: tval*a/b)),
                        (f"({aname}+{bname})/{tname}", safe(lambda a=aval, b=bval: (a+b)/tval)),
                        (f"({aname}*{bname})/{tname}", safe(lambda a=aval, b=bval: (a*b)/tval)),
                        (f"({aname}*{bname})*{tname}", safe(lambda a=aval, b=bval: a*b*tval)),
                        (f"{tname}/({aname}*{bname})", safe(lambda a=aval, b=bval: tval/(a*b))),
                    ]

                    if aval <= 5:
                        exprs.append((f"{tname}^{aname}*{bname}", safe(lambda a=aval, b=bval: (tval**a)*b)))
                        exprs.append((f"{tname}^{aname}+{bname}", safe(lambda a=aval, b=bval: (tval**a)+b)))
                        exprs.append((f"{tname}^{aname}-{bname}", safe(lambda a=aval, b=bval: (tval**a)-b)))
                        exprs.append((f"{tname}^{aname}/{bname}", safe(lambda a=aval, b=bval: (tval**a)/b)))

                    for expr, r in exprs:
                        if r is not None:
                            c += self.check_expr(tname, r, expr, 'L4')

        print(f"  L4: +{c}")
        return c

    # ═══════════════════════════════════════════════════════
    # Level 5: σ-φ × σ-τ 교차
    # ═══════════════════════════════════════════════════════
    def level_5(self):
        print("=== L5: σ-φ × σ-τ 교차 ===")
        c = 0
        sp, st = 10, 8

        # 기본 교차
        base_cross = {
            "(σ-φ)*(σ-τ)": sp*st, "(σ-φ)+(σ-τ)": sp+st,
            "(σ-φ)-(σ-τ)": sp-st, "(σ-φ)/(σ-τ)": sp/st,
            "(σ-τ)/(σ-φ)": st/sp,
            "(σ-φ)^2+(σ-τ)^2": sp**2+st**2,
            "(σ-φ)^2-(σ-τ)^2": sp**2-st**2,
            "(σ-φ)^2*(σ-τ)": sp**2*st,
            "(σ-φ)*(σ-τ)^2": sp*st**2,
            "((σ-φ)+(σ-τ))^2": (sp+st)**2,
            "((σ-φ)-(σ-τ))^2": (sp-st)**2,
            "((σ-φ)*(σ-τ))^(1/2)": math.sqrt(sp*st),
            "(σ-φ)^(σ-τ)": sp**st,
            "(σ-τ)^(σ-φ)": st**sp,
            "(σ-φ)!/(σ-τ)!": math.factorial(sp)//math.factorial(st),
            "ln(σ-φ)*ln(σ-τ)": math.log(sp)*math.log(st),
            "(σ-φ)^3+(σ-τ)^3": sp**3+st**3,
            "(σ-φ)^3-(σ-τ)^3": sp**3-st**3,
            "(σ-φ)^2/(σ-τ)": sp**2/st,
            "(σ-τ)^2/(σ-φ)": st**2/sp,
            "((σ-φ)^2+(σ-τ)^2)^(1/2)": math.sqrt(sp**2+st**2),
        }

        for expr, r in base_cross.items():
            c += self.check_expr('cross_sigphi_sigtau', r, expr, 'L5')

        # n6 상수와 교차 확장
        for xname, xval in N6.items():
            if xval == 0:
                continue
            cross_ext = {
                f"(σ-φ)*(σ-τ)*{xname}": sp*st*xval,
                f"(σ-φ)*(σ-τ)/{xname}": sp*st/xval,
                f"(σ-φ)*(σ-τ)+{xname}": sp*st+xval,
                f"(σ-φ)*(σ-τ)-{xname}": sp*st-xval,
                f"((σ-φ)+(σ-τ))*{xname}": (sp+st)*xval,
                f"((σ-φ)+(σ-τ))/{xname}": (sp+st)/xval,
                f"((σ-φ)-(σ-τ))*{xname}": (sp-st)*xval,
                f"((σ-φ)-(σ-τ))/{xname}": (sp-st)/xval,
                f"(σ-φ)*(σ-τ)^2/{xname}": sp*st**2/xval,
                f"(σ-φ)^2*(σ-τ)/{xname}": sp**2*st/xval,
            }
            for expr, r in cross_ext.items():
                if abs(r) <= 15000:
                    c += self.check_expr('cross_sigphi_sigtau', r, expr, 'L5')

        print(f"  L5: +{c}")
        return c

    # ═══════════════════════════════════════════════════════
    # Level 6: 3항 n6 조합
    # ═══════════════════════════════════════════════════════
    def level_6(self):
        print("=== L6: n6 3항 조합 ===")
        c = 0
        for tname, tval in TARGETS.items():
            for aname, aval in N6.items():
                if aval == 0:
                    continue
                for bname, bval in N6.items():
                    if bval == 0 or aname == bname:
                        continue

                    exprs = [
                        (f"{tname}*{aname}/{bname}", safe(lambda a=aval, b=bval: tval*a/b)),
                        (f"({tname}+{aname})/{bname}", safe(lambda a=aval, b=bval: (tval+a)/b)),
                        (f"({tname}-{aname})/{bname}", safe(lambda a=aval, b=bval: (tval-a)/b)),
                        (f"{aname}/({tname}*{bname})", safe(lambda a=aval, b=bval: a/(tval*b))),
                        (f"({aname}-{bname})*{tname}", safe(lambda a=aval, b=bval: (a-b)*tval)),
                        (f"({aname}+{bname})*{tname}", safe(lambda a=aval, b=bval: (a+b)*tval)),
                        (f"({aname}+{bname})/{tname}", safe(lambda a=aval, b=bval: (a+b)/tval)),
                        (f"({aname}-{bname})/{tname}", safe(lambda a=aval, b=bval: (a-b)/tval)),
                        (f"({aname}^{bname})/{tname}", safe(lambda a=aval, b=bval: (a**b)/tval) if bval <= 4 else None),
                    ]

                    for expr, r in exprs:
                        if r is not None:
                            c += self.check_expr(tname, r, expr, 'L6')

        print(f"  L6: +{c}")
        return c

    # ═══════════════════════════════════════════════════════
    # Level 7: 초월함수
    # ═══════════════════════════════════════════════════════
    def level_7(self):
        print("=== L7: 초월함수 ===")
        c = 0
        golden = (1 + math.sqrt(5)) / 2

        for tname, tval in TARGETS.items():
            exprs = {
                f"pi*{tname}": math.pi * tval,
                f"pi/{tname}": math.pi / tval,
                f"{tname}/pi": tval / math.pi,
                f"pi^2*{tname}": math.pi**2 * tval,
                f"pi^2/{tname}": math.pi**2 / tval,
                f"2*pi*{tname}": 2*math.pi*tval,
                f"e*{tname}": math.e * tval,
                f"e/{tname}": math.e / tval,
                f"{tname}/e": tval / math.e,
                f"e^{tname}": safe(lambda: math.e**tval),
                f"ln({tname})": math.log(tval),
                f"log10({tname})": math.log10(tval),
                f"log2({tname})": math.log2(tval),
                f"sin(pi/{tname})": math.sin(math.pi/tval),
                f"cos(pi/{tname})": math.cos(math.pi/tval),
                f"tan(pi/{tname})": safe(lambda: math.tan(math.pi/tval)),
                f"sin(2*pi/{tname})": math.sin(2*math.pi/tval),
                f"cos(2*pi/{tname})": math.cos(2*math.pi/tval),
                f"golden*{tname}": golden * tval,
                f"{tname}/golden": tval / golden,
                f"golden^{tname}": safe(lambda: golden**tval),
                f"sqrt({tname})": math.sqrt(tval),
                f"ln(2)*{tname}": math.log(2)*tval,
                f"ln(4/3)*{tname}": math.log(4/3)*tval,
                f"1/e*{tname}": (1/math.e)*tval,
                f"pi*e*{tname}": math.pi*math.e*tval,
            }

            # n6 상수와 초월 조합
            for xname, xval in N6.items():
                if xval <= 0:
                    continue
                exprs[f"ln({tname})*{xname}"] = math.log(tval) * xval
                exprs[f"pi*{tname}*{xname}"] = math.pi * tval * xval
                exprs[f"pi*{tname}/{xname}"] = math.pi * tval / xval
                exprs[f"e^({tname}/{xname})"] = safe(lambda xv=xval: math.e**(tval/xv))
                exprs[f"{tname}^(1/{xname})"] = safe(lambda xv=xval: tval**(1/xv))
                exprs[f"ln({xname})*{tname}"] = math.log(xval) * tval if xval > 0 else None
                exprs[f"sqrt({tname}*{xname})"] = math.sqrt(tval * xval)
                exprs[f"sqrt({tname}/{xname})"] = math.sqrt(tval / xval)
                exprs[f"sqrt({xname}/{tname})"] = math.sqrt(xval / tval)

            for expr, r in exprs.items():
                if r is not None and not (isinstance(r, float) and (math.isnan(r) or math.isinf(r))):
                    c += self.check_expr(tname, r, expr, 'L7')

        print(f"  L7: +{c}")
        return c

    # ═══════════════════════════════════════════════════════
    # Level 8: 10의 거듭제곱 특수 (σ-φ=10)
    # ═══════════════════════════════════════════════════════
    def level_8(self):
        print("=== L8: 10^n 특수 탐색 ===")
        c = 0

        # 모든 값에서 10^k 패턴 확인
        for v in self.all_values:
            if v <= 0:
                continue
            log10v = safe(lambda: math.log10(v))
            if log10v is None:
                continue

            # 정확한 10^k
            if abs(log10v - round(log10v)) < 0.001:
                k = int(round(log10v))
                if -6 <= k <= 12:
                    c += self.record(f"exhaust_(σ-φ)^{k}_value={v}", v, 10**k, 'EXACT', 'L8')

            # a * 10^k (a = n6 상수)
            for k in range(-4, 8):
                pk = 10**k
                a = v / pk
                for xname, xval in N6.items():
                    if xval == 0:
                        continue
                    g, err = grade(a, xval)
                    if g != 'MISS':
                        c += self.record(
                            f"exhaust_{xname}*(σ-φ)^{k}_value={v}",
                            v, xval * pk, g, 'L8')

        # 10^k / n6, 10^k * n6
        for k in range(1, 7):
            pk = 10**k
            for xname, xval in N6.items():
                if xval == 0:
                    continue
                for op, r in [('*', pk*xval), ('/', pk/xval)]:
                    c += self.check_expr('sigma-phi', r, f"(σ-φ)^{k}{op}{xname}", 'L8')

        # 10^k ± n6
        for k in range(1, 5):
            pk = 10**k
            for xname, xval in N6.items():
                for r, op in [(pk+xval, '+'), (pk-xval, '-')]:
                    c += self.check_expr('sigma-phi', r, f"(σ-φ)^{k}{op}{xname}", 'L8')

        print(f"  L8: +{c}")
        return c

    # ═══════════════════════════════════════════════════════
    # Level 9: 8=2^3 바이너리/옥텟 (σ-τ=8)
    # ═══════════════════════════════════════════════════════
    def level_9(self):
        print("=== L9: 2^3 바이너리/옥텟 ===")
        c = 0

        # 모든 값에서 8^k, 2^k 패턴
        for v in self.all_values:
            if v <= 0:
                continue

            # 8^k
            log8v = safe(lambda: math.log(v) / math.log(8))
            if log8v is not None and abs(log8v - round(log8v)) < 0.001:
                k = int(round(log8v))
                if -3 <= k <= 8:
                    c += self.record(f"exhaust_(σ-τ)^{k}_value={v}", v, 8**k, 'EXACT', 'L9')

            # 2^k (8=2^3 이므로)
            log2v = safe(lambda: math.log2(v))
            if log2v is not None and abs(log2v - round(log2v)) < 0.001:
                k = int(round(log2v))
                if 0 <= k <= 20:
                    if k % 3 == 0:
                        c += self.record(
                            f"exhaust_2^{k}=(σ-τ)^{k//3}_value={v}",
                            v, 2**k, 'EXACT', 'L9')
                    else:
                        c += self.record(
                            f"exhaust_2^{k}_binary_value={v}",
                            v, 2**k, 'EXACT', 'L9')

            # a * 8^k
            for k in range(-2, 5):
                pk = 8**k
                a = v / pk
                for xname, xval in N6.items():
                    if xval == 0:
                        continue
                    g, err = grade(a, xval)
                    if g != 'MISS':
                        c += self.record(
                            f"exhaust_{xname}*(σ-τ)^{k}_value={v}",
                            v, xval * pk, g, 'L9')

            # 8 나누어 떨어지는 값
            if v == int(v) and int(v) % 8 == 0:
                q = int(v) // 8
                for xname, xval in N6.items():
                    if xval == 0:
                        continue
                    g, err = grade(q, xval)
                    if g != 'MISS':
                        c += self.record(
                            f"exhaust_(σ-τ)*{xname}_value={v}",
                            v, 8*xval, g, 'L9')

        # 8^k * n6 / n6
        for k in range(1, 5):
            pk = 8**k
            for aname, aval in N6.items():
                if aval == 0:
                    continue
                for bname, bval in N6.items():
                    if bval == 0 or aname == bname:
                        continue
                    r = pk * aval / bval
                    if abs(r) <= 15000:
                        c += self.check_expr('sigma-tau', r,
                                             f"(σ-τ)^{k}*{aname}/{bname}", 'L9')

        print(f"  L9: +{c}")
        return c

    # ═══════════════════════════════════════════════════════
    # 역방향: 모든 값에서 10, 8 표현 가능성
    # ═══════════════════════════════════════════════════════
    def reverse_scan(self):
        print("=== REV: 역방향 전수 스캔 ===")
        c = 0

        for v in self.all_values:
            if v == 0:
                continue

            for tname, tval in TARGETS.items():
                # v / tval → n6?
                ratio = safe(lambda: v / tval)
                if ratio is not None:
                    for xname, xval in N6.items():
                        if xval == 0:
                            continue
                        g, err = grade(ratio, xval)
                        if g != 'MISS':
                            c += self.record(
                                f"exhaust_{tname}*{xname}_rev={v}",
                                v, tval * xval, g, 'REV')

                # v - tval → n6?
                diff = v - tval
                for xname, xval in N6.items():
                    g, err = grade(diff, xval)
                    if g != 'MISS':
                        c += self.record(
                            f"exhaust_{tname}+{xname}_rev={v}",
                            v, tval + xval, g, 'REV')

                # v + tval → n6 매칭?
                sm = v + tval
                for xname, xval in N6.items():
                    g, err = grade(sm, xval)
                    if g != 'MISS':
                        c += self.record(
                            f"exhaust_{xname}-{tname}_rev={v}",
                            v, xval - tval, g, 'REV')

                # v * tval → n6?
                prod = v * tval
                for xname, xval in N6.items():
                    if xval == 0:
                        continue
                    g, err = grade(prod, xval)
                    if g != 'MISS':
                        c += self.record(
                            f"exhaust_{xname}/{tname}_rev={v}",
                            v, xval / tval, g, 'REV')

                # log_tval(v) → n6?
                if v > 0 and tval > 1:
                    lv = safe(lambda: math.log(v) / math.log(tval))
                    if lv is not None:
                        for xname, xval in N6.items():
                            if xval == 0:
                                continue
                            g, err = grade(lv, xval)
                            if g != 'MISS':
                                r = safe(lambda xv=xval: tval ** xv)
                                if r is not None:
                                    c += self.record(
                                        f"exhaust_{tname}^{xname}_rev={v}",
                                        v, r, g, 'REV')

        print(f"  REV: +{c}")
        return c

    def run(self):
        iteration = 0
        while True:
            iteration += 1
            print(f"\n{'='*70}")
            print(f"  반복 #{iteration}")
            print(f"{'='*70}")

            prev = len(self.new_discoveries)

            self.level_1()
            self.level_2()
            self.level_3()
            self.level_4()
            self.level_5()
            self.level_6()
            self.level_7()
            self.level_8()
            self.level_9()
            self.reverse_scan()

            new_count = len(self.new_discoveries) - prev
            new_exact = sum(1 for d in self.new_discoveries[prev:]
                           if d['grade'] == 'EXACT')

            print(f"\n  반복 #{iteration}: +{new_count} 발견 ({new_exact} EXACT)")

            if new_exact == 0:
                print(f"\n  포화 도달! EXACT 신규 0 — 탐색 종료")
                break
            if iteration >= 3:
                print(f"\n  최대 반복 도달")
                break

        self.save()
        self.summary()

    def save(self):
        if not self.new_discoveries:
            print("\n[저장] 신규 없음")
            return
        with open(LOG_PATH, 'a') as f:
            for entry in self.new_discoveries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        print(f"\n[저장] {len(self.new_discoveries):,} 엔트리 → discovery_log.jsonl")

    def summary(self):
        print()
        print("=" * 70)
        print("  최종 요약")
        print("=" * 70)

        total_exact = total_close = total_near = 0
        print(f"\n  {'레벨':<8} {'EXACT':>8} {'CLOSE':>8} {'NEAR':>8} {'합계':>8}")
        print(f"  {'-'*44}")

        for level in ['L1','L2','L3','L4','L5','L6','L7','L8','L9','REV']:
            s = self.stats[level]
            ex, cl, nr = s.get('EXACT',0), s.get('CLOSE',0), s.get('NEAR',0)
            total_exact += ex; total_close += cl; total_near += nr
            t = ex+cl+nr
            if t > 0:
                print(f"  {level:<8} {ex:>8} {cl:>8} {nr:>8} {t:>8}")

        print(f"  {'-'*44}")
        grand = total_exact + total_close + total_near
        print(f"  {'합계':<8} {total_exact:>8} {total_close:>8} {total_near:>8} {grand:>8}")
        print()
        print(f"  전체 검사: {self.total_checked:,}")
        print(f"  신규 발견: {grand:,}")
        if grand > 0:
            print(f"  EXACT 비율: {total_exact/grand*100:.1f}%")

        # 상수별
        sp = sum(1 for d in self.new_discoveries if 'sigma-phi' in d['constant'])
        st = sum(1 for d in self.new_discoveries if 'sigma-tau' in d['constant'])
        cr = sum(1 for d in self.new_discoveries if 'cross' in d['constant'])
        print(f"\n  σ-φ 관련: {sp:,}")
        print(f"  σ-τ 관련: {st:,}")
        print(f"  교차: {cr:,}")

        # EXACT 샘플
        exacts = [d for d in self.new_discoveries if d['grade'] == 'EXACT']
        if exacts:
            print(f"\n  EXACT 샘플 (상위 30/{len(exacts)}):")
            for d in exacts[:30]:
                print(f"    {d['constant']}: {d['value']}")

        print()
        print("=" * 70)
        print(f"  포화 탐색 완료. {grand:,} 신규 발견.")
        print("=" * 70)


if __name__ == '__main__':
    engine = ExhaustEngine()
    engine.run()
