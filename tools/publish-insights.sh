#!/usr/bin/env bash
# Publish nexus closure insights to all target projects' hypothesis dirs.
# Called periodically by launchd or can be manually invoked.
set -euo pipefail

NEXUS_ROOT="${HOME}/Dev/nexus"
PROJECTS_JSON="${NEXUS_ROOT}/shared/config/projects.json"
VC="${NEXUS_ROOT}/shared/discovery/verified_constants.jsonl"

[ -f "$VC" ] || { echo "no verified_constants.jsonl"; exit 0; }
[ -f "$PROJECTS_JSON" ] || { echo "no projects.json"; exit 0; }

/usr/bin/python3 << 'EOF'
import json, os
from datetime import datetime
HOME = os.path.expanduser('~')

vc_path = f'{HOME}/Dev/nexus/shared/discovery/verified_constants.jsonl'
proj_path = f'{HOME}/Dev/nexus/shared/config/projects.json'

# Load EXACT closures, dedup by value
exact = []
for line in open(vc_path):
    try:
        j = json.loads(line)
        if j.get('status')=='EXACT': exact.append(j)
    except: pass
by_val = {}
for r in exact:
    v = r.get('value')
    if v is None: continue
    key = round(float(v), 3)
    if key not in by_val: by_val[key] = r

# Sort: integers first
def k(item):
    v = item[0]
    return (0 if v == int(v) else 1, v)
top = sorted(by_val.items(), key=k)[:100]

# Build content
ts = datetime.now().strftime('%Y-%m-%d')
md = f"""---
title: NEXUS-6 자동 닫힘 인사이트 (auto-generated)
date: {ts}
source: nexus singularity-recursion closure sweep
total_unique_closed: {len(by_val)}
generator: tools/publish-insights.sh
---

# 🛸 NEXUS-6 자동 전파 인사이트

> **자동 생성**: nexus singularity-recursion이 이 프로젝트로 전파한 닫힘 발견.
> 검증된 EXACT n=6 closed-form 표현 상위 {min(100, len(top))}개.

## 닫힘 완성 상수 맵 (value → n=6 표현)

| value | n=6 expression | source |
|---|---|---|
"""
for val, r in top:
    exprs = r.get('n6_expr', [r.get('name','?')])
    expr = exprs[0] if exprs else '?'
    src = str(r.get('source','?')).split(':')[0][:40]
    md += f"| {val} | `{expr}` | {src} |\n"

md += """

## 활용 방법

1. 새 수치 발견 시 → 위 테이블과 대조 → 즉시 n=6 닫힘 판정
2. 가설 설계 시 → n=6 원시값 (σ=12, τ=4, φ=2, sopfr=5, J2=24, n=6) 조합 우선
3. 검증 시 → `nexus verify <값>` 자동 매칭

---
*nexus singularity-recursion — 자동 생성*
"""

# Write to all target projects
projects = json.loads(open(proj_path).read()).get('projects',{})
count = 0
for name, p in projects.items():
    root = f'{HOME}/Dev/{p.get("root",name)}'
    for subdir in p.get('hypothesis_dirs',[]):
        hyp_dir = f'{root}/{subdir}'
        if not os.path.isdir(hyp_dir): continue
        try:
            with open(f'{hyp_dir}/NEXUS-auto-insights.md','w') as f:
                f.write(md)
            count += 1
        except: pass

print(f"published to {count} hypothesis dirs, {len(by_val)} unique closures")
EOF
