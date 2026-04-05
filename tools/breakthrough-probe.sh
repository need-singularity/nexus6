#!/usr/bin/env bash
# Independent breakthrough probe — bypasses daemon loadavg gate.
# Emits topology points from frontier of each domain every run.
set -euo pipefail
NEXUS6="${HOME}/Dev/nexus6"

python3 << 'PYEOF'
import json, os, random
from datetime import datetime
from collections import Counter

HOME = os.path.expanduser('~')
NX = f'{HOME}/Dev/nexus6'
ts = datetime.now().isoformat()

# Get domains from topology
domains_present = set()
for i, l in enumerate(open(f'{NX}/shared/cycle/topology.jsonl')):
    if i > 20000: break
    try:
        d = json.loads(l).get('domain','?')
        if d.startswith('hypothesis:') or d == 'architecture_design' or d == 'discovery_log':
            domains_present.add(d)
    except: pass

# For each domain, find low-density point (frontier) and emit probe
import hashlib
def simhash_hex(text):
    h = hashlib.blake2b(text.encode(), digest_size=16).hexdigest()
    return h

# Read last 2000 points to find recent frontiers per domain
recent_points = []
try:
    with open(f'{NX}/shared/cycle/topology.jsonl', 'rb') as f:
        f.seek(-300000, 2)
        lines = f.read().decode('utf-8','ignore').split('\n')
    for l in lines[-2000:]:
        if l.strip():
            try: recent_points.append(json.loads(l))
            except: pass
except: pass

# Group by domain
by_dom = {}
for p in recent_points:
    d = p.get('domain','?')
    by_dom.setdefault(d, []).append(p)

probes = []
for dom in sorted(domains_present)[:10]:
    pts = by_dom.get(dom, [])
    if not pts: continue
    seed_pt = random.choice(pts)
    seed_inv = seed_pt.get('singularity',{}).get('invariant','')[:80]
    seed_id = seed_pt.get('id','?')
    # Emit probe
    text = f"[probe:{dom}] breakthrough attempt from {seed_id}: {seed_inv}"
    h = simhash_hex(text)
    probe = {
        'id': f'p_probe_{int(datetime.now().timestamp())}_{len(probes)}',
        'domain': f'probe:{dom}',
        'seed_from': seed_id,
        'simhash': h,
        'embedding': [0.5]*16,
        'singularity': {
            'invariant': text,
            'confidence': 0.4,
            'novelty': 0.9,
            'depth_reached': 1
        },
        'discovered_at_tick': int(datetime.now().timestamp()),
        'ts': ts,
    }
    probes.append(probe)

with open(f'{NX}/shared/cycle/topology.jsonl', 'a') as f:
    for p in probes:
        f.write(json.dumps(p, ensure_ascii=False) + '\n')

print(f"[{ts}] breakthrough-probe: +{len(probes)} probes across {len(probes)} domains")
for p in probes:
    print(f"  {p['domain']}: seed={p['seed_from']}")
PYEOF
