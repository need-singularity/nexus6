#!/usr/bin/env bash
# Auto-generate calc/ verification stubs from recent EXACT closures.
# Runs periodically alongside closure-sweep.
set -euo pipefail

NEXUS="${HOME}/Dev/nexus"
VC="${NEXUS}/shared/verified_constants.jsonl"
CALC_DIR="${NEXUS}/shared/calc"
STUBS_DIR="${CALC_DIR}/auto_stubs"
STATE="${NEXUS}/shared/.calc_stubs_state.json"

[ -f "$VC" ] || exit 0
mkdir -p "$STUBS_DIR"

/usr/bin/python3 << 'PYEOF'
import json, os, hashlib
from datetime import datetime

HOME = os.path.expanduser('~')
VC = f'{HOME}/Dev/nexus/shared/verified_constants.jsonl'
STUBS = f'{HOME}/Dev/nexus/shared/calc/auto_stubs'
STATE_PATH = f'{HOME}/Dev/nexus/shared/.calc_stubs_state.json'

# Load state: which closures already have stubs
state = {'generated_ids': []}
if os.path.exists(STATE_PATH):
    try: state = json.loads(open(STATE_PATH).read())
    except: pass
generated = set(state.get('generated_ids', []))

# Find EXACT closures not yet stubbed — UNIQUE values only, 우선 cosmology/physics관련
candidates = []
seen_vals = set()
for line in open(VC):
    try:
        j = json.loads(line)
        if j.get('status') != 'EXACT': continue
        v = j.get('value')
        if v is None: continue
        vkey = round(float(v), 4)
        if vkey in seen_vals: continue
        seen_vals.add(vkey)
        # Hash for stable stub ID
        expr = str(j.get('n6_expr', [''])[0]) if j.get('n6_expr') else ''
        cid = hashlib.md5(f'{v}|{expr}'.encode()).hexdigest()[:10]
        if cid in generated: continue
        candidates.append((cid, v, expr, j.get('name','')))
    except: pass

# Only generate N new per run (cap)
MAX_PER_RUN = 20
created = 0
for cid, val, expr, name in candidates[:MAX_PER_RUN]:
    stub_path = f'{STUBS}/verify_{cid}.py'
    if os.path.exists(stub_path):
        generated.add(cid)
        continue
    body = f'''#!/usr/bin/env python3
"""
AUTO-GENERATED stub from nexus closure-sweep.

Closure: {val} = {expr}
Full: {name[:120]}

Human task: verify the expression algebraically. Mark as VERIFIED or REJECTED.
"""
# n=6 primitives
n, sigma, tau, phi, sopfr, J2 = 6, 12, 4, 2, 5, 24

# Multi-n primitives (from meta FP ladder)
# n=15: sigma=24, phi=8, tau=4, sopfr=8
# n=35: sigma=48, phi=24, tau=4, sopfr=12
# n=105: sigma=192, phi=48, tau=8, sopfr=15

target = {val}
claimed_expr = {repr(expr)}

# TODO: compute expected from claimed_expr
# expected = eval(claimed_expr)  # only if safe

# TODO: assert abs(expected - target) < 1e-6, f"FAIL: got expected-{{target}}"
print(f"stub: target={{target}}, claim={{claimed_expr}}")
print(f"status: STUB (human verification needed)")
'''
    with open(stub_path, 'w') as f:
        f.write(body)
    generated.add(cid)
    created += 1

state['generated_ids'] = list(generated)
state['last_run'] = datetime.now().isoformat()
with open(STATE_PATH, 'w') as f:
    f.write(json.dumps(state))

print(f"[{datetime.now().isoformat()}] created {created} stubs, total={len(generated)}")
PYEOF
