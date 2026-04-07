#!/usr/bin/env python3
"""n=6 현실 지도 검증기 -- 출처 기반 바텀업 검증"""
import json, math, sys
from fractions import Fraction

# n=6 기본 상수
n=6; sigma=12; tau=4; phi=2; sopfr=5; J2=24; mu=1

import os as _os
_dir = _os.path.dirname(_os.path.abspath(__file__))
_path = _os.path.join(_dir, "reality_map.json")
with open(_path, encoding="utf-8") as f:
    data = json.load(f)

nodes = [x for x in data["nodes"] if not x.get("_comment")]

# 집계
total = len(nodes)
by_grade = {"EXACT": 0, "CLOSE": 0, "MISS": 0}
by_causal = {"STRUCTURAL": 0, "CAUSAL": 0, "EMPIRICAL": 0, "CONVENTION": 0}
by_level = {}
by_thread = {}
fails = []

print(f"\n{'='*70}")
print(f"  n=6 현실 지도 검증 -- {total} 노드")
print(f"{'='*70}\n")

for node in nodes:
    nid = node["id"]
    grade = node["grade"]
    causal = node.get("causal", "?")
    level = node["level"]
    thread = node.get("thread", "none")
    expr = node.get("verify", "true")

    # expr 평가
    try:
        ok = eval(expr)
    except Exception as e:
        ok = False
        fails.append((nid, f"eval 오류: {e}"))

    if not ok and grade != "MISS":
        fails.append((nid, f"expr 실패: {expr}"))

    # 집계
    by_grade[grade] = by_grade.get(grade, 0) + 1
    by_causal[causal] = by_causal.get(causal, 0) + 1
    by_level[level] = by_level.get(level, 0) + 1
    by_thread[thread] = by_thread.get(thread, 0) + 1

    # 출력
    icon = {"EXACT": "O", "CLOSE": "~", "MISS": "X"}[grade]
    err = node.get("error_pct", "")
    err_str = f" ({err}%)" if err else ""
    src = node["source"][:40]
    print(f"  [{icon}] {grade:5s} {nid:40s} {node['claim'][:30]:30s} {src}{err_str}")

# 요약
print(f"\n{'='*70}")
print(f"  등급별 집계")
print(f"{'='*70}")
for g, c in sorted(by_grade.items()):
    bar = "#" * c
    pct = 100 * c / total
    print(f"    {g:10s} {c:3d} ({pct:5.1f}%) {bar}")

print(f"\n  인과 유형별")
for g, c in sorted(by_causal.items()):
    bar = "#" * c
    print(f"    {g:12s} {c:3d} {bar}")

print(f"\n  레벨별")
for g, c in sorted(by_level.items()):
    bar = "#" * c
    print(f"    {g:15s} {c:3d} {bar}")

print(f"\n  상수 실(thread)별")
for g, c in sorted(by_thread.items(), key=lambda x: -x[1]):
    if g != "none" and g != "mixed":
        bar = "#" * c
        print(f"    {g:18s} {c:3d} {bar}")

# MISS 분석
miss_nodes = [x for x in nodes if x["grade"] == "MISS"]
print(f"\n{'='*70}")
print(f"  MISS 상세 ({len(miss_nodes)}건) -- 정직한 불일치")
print(f"{'='*70}")
for m in miss_nodes:
    print(f"    {m['id']}: {m['claim']}")
    print(f"      측정값: {m['measured']}, 출처: {m['source'][:50]}")
    print(f"      n6 시도: {m['n6_expr']}")
    print(f"      이유: {m.get('cause', 'N/A')[:80]}")
    print()

# eval 실패
if fails:
    print(f"\n  eval 실패 ({len(fails)}건):")
    for fid, msg in fails:
        print(f"    {fid}: {msg}")

# 최종 스코어
exact = by_grade.get("EXACT", 0)
close = by_grade.get("CLOSE", 0)
miss = by_grade.get("MISS", 0)
structural = by_causal.get("STRUCTURAL", 0)
causal_count = by_causal.get("CAUSAL", 0)

print(f"\n{'='*70}")
print(f"  최종 결과")
print(f"{'='*70}")
print(f"    전체 노드:     {total}")
print(f"    EXACT:         {exact} ({100*exact/total:.1f}%)")
print(f"    CLOSE:         {close} ({100*close/total:.1f}%)")
print(f"    MISS:          {miss} ({100*miss/total:.1f}%)")
print(f"    ---")
print(f"    STRUCTURAL:    {structural} (수학/군론 증명)")
print(f"    CAUSAL:        {causal_count} (물리 법칙 유도)")
print(f"    EMPIRICAL:     {by_causal.get('EMPIRICAL', 0)} (측정 일치, 인과 불명)")
print(f"    CONVENTION:    {by_causal.get('CONVENTION', 0)} (인간 관례)")
print(f"    ---")
print(f"    증거력 있는 EXACT: {exact - by_causal.get('CONVENTION', 0)} / {total - by_causal.get('CONVENTION', 0)} (관례 제외)")
print(f"{'='*70}\n")
