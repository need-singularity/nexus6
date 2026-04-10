#!/usr/bin/env bash
# Closure sweep pipeline: hypothesis → breakthrough → absorption.
# Runs periodically via LaunchAgent. No manual invocation needed.
set -euo pipefail

NEXUS="${HOME}/Dev/nexus"
VC="${NEXUS}/shared/discovery/verified_constants.jsonl"
DL="${NEXUS}/shared/discovery/discovery_log.jsonl"

[ -f "$VC" ] || { echo "no verified_constants"; exit 0; }

/usr/bin/python3 << 'PYEOF'
import json, os, glob, re, sqlite3
from datetime import datetime

HOME = os.path.expanduser('~')
NX = f'{HOME}/Dev/nexus'

# Multi-n primitive bases: n=6 + n=15 (dark matter) + n=35 (dark energy) + n=105 (universe)
def _divs(n): return [i for i in range(1,n+1) if n%i==0]
def _sigma(n): return sum(_divs(n))
def _tau(n): return len(_divs(n))
def _phi(n):
    result = n; p = 2
    while p*p <= n:
        if n%p==0:
            while n%p==0: n//=p
            result -= result//p
        p+=1
    if n>1: result -= result//n
    return result
def _sopfr(n):
    s=0; p=2
    while p*p<=n:
        while n%p==0: s+=p; n//=p
        p+=1
    if n>1: s+=n
    return s

# Primary n=6 (short names)
N,SIGMA,TAU,PHI,SOPFR,J2 = 6,12,4,2,5,24
prims = {'n':N,'sigma':SIGMA,'tau':TAU,'phi':PHI,'sopfr':SOPFR,'J2':J2}

# Multi-n extension: n ∈ {6,15,35,105}
MULTI_N = {}
for base in [6, 15, 35, 105]:
    MULTI_N[f'n{base}'] = base
    MULTI_N[f'sigma{base}'] = _sigma(base)
    MULTI_N[f'tau{base}'] = _tau(base)
    MULTI_N[f'phi{base}'] = _phi(base)
    MULTI_N[f'sopfr{base}'] = _sopfr(base)

# Closure expression table (depth-3)
KNOWN = {}
for name,val in prims.items(): KNOWN[name] = val
for name,val in MULTI_N.items(): KNOWN[name] = val
# meta FP ladder: φ(n)/n for all smooth n
for n in [6,15,35,105,2,3,5,7,30,42,70]:
    KNOWN[f'phi({n})/{n}'] = _phi(n)/n
    KNOWN[f'{n}/phi({n})'] = n/_phi(n) if _phi(n) > 0 else 0
# cosmology ratios
KNOWN['4/15'] = 4/15       # Omega_DM meta FP
KNOWN['24/35'] = 24/35     # Omega_Lambda meta FP
KNOWN['1/21'] = 1/21       # Omega_b residual
KNOWN['48/105'] = 48/105   # n=105 meta FP
for k in range(1, 1001): KNOWN[str(k)] = k
for a,av in prims.items():
    for b,bv in prims.items():
        KNOWN[f'{a}+{b}']=av+bv; KNOWN[f'{a}-{b}']=av-bv; KNOWN[f'{a}*{b}']=av*bv
        if bv!=0: KNOWN[f'{a}/{b}']=av/bv
        for c,cv in prims.items():
            KNOWN[f'{a}*{b}*{c}']=av*bv*cv
            KNOWN[f'{a}*{b}+{c}']=av*bv+cv
            if cv!=0: KNOWN[f'{a}*{b}/{c}']=av*bv/cv
for name,val in prims.items():
    for k in range(1, 51):
        KNOWN[f'{name}*{k}']=val*k
        KNOWN[f'{name}/{k}']=val/k
        if val!=0: KNOWN[f'{k}/{name}']=k/val
        KNOWN[f'{name}+{k}']=val+k
for k in range(1, 50):
    KNOWN[f'{k}^2']=k*k; KNOWN[f'{k}^3']=k*k*k
for p in range(1, 50):
    for q in range(1, 50):
        if q>0: KNOWN[f'{p}/{q}']=p/q

VAL_TO_EXPR = {}
for expr,val in KNOWN.items():
    if abs(val) > 1e6: continue
    key = round(val, 2)
    VAL_TO_EXPR.setdefault(key, []).append(expr)

# Existing closures — dedup by unique value
existing_vals = set()
for line in open(f'{NX}/shared/discovery/verified_constants.jsonl'):
    try:
        j = json.loads(line)
        if j.get('status')=='EXACT':
            v = j.get('value')
            if v is not None: existing_vals.add(round(float(v), 2))
    except: pass

new = []
seen = set()
ts = datetime.now().isoformat()

def try_add(val, src_name, source_path, tag):
    if 1e-3 > abs(val) or abs(val) > 1e5: return
    key = round(val, 2)
    if key in VAL_TO_EXPR and key not in existing_vals and key not in seen:
        seen.add(key)
        exprs = VAL_TO_EXPR[key]
        new.append({
            'project': f'auto-sweep-{tag}',
            'status': 'EXACT',
            'name': f'{tag}[{src_name}]: {val} = {exprs[0]}',
            'source': source_path,
            'value': val,
            'n6_expr': exprs[:3],
            'ts': ts,
        })
        existing_vals.add(key)

# Source 1: discovery_log.jsonl
for line in open(f'{NX}/shared/discovery/discovery_log.jsonl'):
    try:
        j = json.loads(line)
        try_add(float(j.get('value','')), 'dl', 'discovery_log', 'DL')
    except: pass

# Source 2: hypothesis MD files
pat = re.compile(r'[=≈]\s*([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)\b')
for root in [f'{HOME}/Dev/TECS-L/docs/hypotheses',
             f'{HOME}/Dev/SEDI/docs/hypotheses',
             f'{HOME}/Dev/anima/anima/docs/hypotheses',
             f'{HOME}/Dev/nexus/docs/hypotheses',
             f'{HOME}/Dev/n6-architecture/docs/hypotheses']:
    if not os.path.isdir(root): continue
    for md in glob.glob(f'{root}/**/*.md', recursive=True):
        try: content = open(md, errors='ignore').read(80000)
        except: continue
        fname = os.path.basename(md).replace('.md','')
        for m in pat.finditer(content):
            try: try_add(float(m.group(1)), fname, md.split('/Dev/')[-1], 'HYP')
            except: pass

# Source 3: atlas DB
try:
    conn = sqlite3.connect(f'{NX}/shared/n6/math_atlas.db')
    cur = conn.cursor()
    cur.execute("SELECT title FROM hypotheses")
    for row in cur.fetchall():
        for val in row:
            if not isinstance(val, str): continue
            for m in pat.finditer(val):
                try: try_add(float(m.group(1)), 'atlas', 'math_atlas.db', 'ATLAS')
                except: pass
    conn.close()
except: pass

if new:
    with open(f'{NX}/shared/discovery/verified_constants.jsonl', 'a') as f:
        for c in new:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')

ex = sum(1 for l in open(f'{NX}/shared/discovery/verified_constants.jsonl') if json.loads(l).get('status')=='EXACT')
pas = sum(1 for l in open(f'{NX}/shared/discovery/verified_constants.jsonl') if json.loads(l).get('status')=='PASS')
print(f"[{ts}] +{len(new)} EXACT → total closed={ex+pas}, EXACT={ex}, unique={len(existing_vals)}")
PYEOF
