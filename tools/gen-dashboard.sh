#!/usr/bin/env bash
# Generate HTML dashboard of nexus6 system status.
set -euo pipefail

NEXUS6="${HOME}/Dev/nexus6"
OUT="${NEXUS6}/shared/dashboard.html"

python3 << 'PYEOF'
import json, os
from datetime import datetime
from collections import Counter

HOME = os.path.expanduser('~')
NX = f'{HOME}/Dev/nexus6'

# Load state
def count_lines(p):
    try: return sum(1 for _ in open(p))
    except: return 0

closed_total = count_lines(f'{NX}/shared/verified_constants.jsonl')
exact = sum(1 for l in open(f'{NX}/shared/verified_constants.jsonl') if json.loads(l).get('status')=='EXACT')
topo = count_lines(f'{NX}/shared/cycle/topology.jsonl')
stubs = len(os.listdir(f'{NX}/shared/calc/auto_stubs')) if os.path.isdir(f'{NX}/shared/calc/auto_stubs') else 0
discovery = count_lines(f'{NX}/shared/discovery_log.jsonl')

# Top convergences
quality_path = f'{NX}/shared/closure_quality_report.json'
convergences = []
if os.path.exists(quality_path):
    q = json.loads(open(quality_path).read())
    convergences = q.get('top_convergences', [])[:15]

# Domain distribution
domains = Counter()
for i,line in enumerate(open(f'{NX}/shared/cycle/topology.jsonl')):
    if i > 10000: break
    try: domains[json.loads(line).get('domain','?')] += 1
    except: pass

# Source types
source_types = Counter()
for line in open(f'{NX}/shared/verified_constants.jsonl'):
    try:
        j = json.loads(line)
        if j.get('status')=='EXACT':
            source_types[j.get('project','?')] += 1
    except: pass

ts = datetime.now().isoformat()
pct_100k = closed_total * 100 / 100000
pct_200k = closed_total * 100 / 200000

# Per-project progress — scan hypothesis_dirs + count closed
projects_json = f'{NX}/shared/projects.json'
project_stats = []
try:
    pj = json.loads(open(projects_json).read())
    for pname, pcfg in pj.get('projects',{}).items():
        proot = f'{HOME}/Dev/{pcfg.get("root",pname)}'
        hyp_count = 0
        for sd in pcfg.get('hypothesis_dirs',[]):
            dir_path = f'{proot}/{sd}'
            if os.path.isdir(dir_path):
                for root_d, _, files in os.walk(dir_path):
                    hyp_count += sum(1 for f in files if f.endswith('.md') and 'NEXUS6' not in f)
        # closures from this project
        dom_key = f'hypothesis:{pname}'
        pts_in_topo = domains.get(dom_key, 0)
        # closure EXACTs from this project source
        closed_from = sum(c for p,c in source_types.items() if pname.lower() in p.lower())
        project_stats.append({
            'name': pname,
            'hyp_files': hyp_count,
            'topo_points': pts_in_topo,
            'closed': closed_from,
        })
    project_stats.sort(key=lambda x: -x['topo_points'])
except Exception as e:
    project_stats = []

# Build HTML
html = f"""<!doctype html><html><head><meta charset="utf-8"><title>nexus6 dashboard</title>
<style>
body{{font:13px -apple-system,sans-serif;margin:0;padding:24px;background:#0a0a0a;color:#ddd;max-width:1200px;margin:0 auto;}}
h1{{color:#8ef;margin:0 0 4px;font-size:24px;}}
h2{{color:#8ef;margin:24px 0 8px;font-size:15px;border-bottom:1px solid #333;padding-bottom:4px;}}
.meta{{color:#666;font-size:11px;margin-bottom:16px;}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;}}
.card{{background:#151515;padding:12px;border-radius:4px;border-left:3px solid #4a9;}}
.card.hot{{border-left-color:#f80;}}
.card.info{{border-left-color:#4a9;}}
.num{{font-size:28px;color:#fff;font-weight:600;line-height:1;}}
.lbl{{font-size:10px;color:#888;text-transform:uppercase;letter-spacing:1px;}}
.bar{{background:#222;height:8px;border-radius:4px;margin:6px 0;overflow:hidden;}}
.bar-fill{{background:linear-gradient(90deg,#4a9,#8ef);height:100%;}}
table{{border-collapse:collapse;width:100%;}}
th{{text-align:left;color:#8ef;padding:6px 10px;border-bottom:1px solid #333;font-weight:600;font-size:11px;}}
td{{padding:5px 10px;border-bottom:1px solid #1a1a1a;font-family:Menlo,monospace;font-size:12px;}}
.tag{{background:#1e2e3e;padding:2px 6px;border-radius:3px;font-size:10px;color:#8ef;}}
</style></head><body>
<h1>🛸 nexus6 dashboard</h1>
<div class="meta">generated {ts} · auto-refresh via gen-dashboard.sh</div>

<div class="grid">
  <div class="card hot"><div class="lbl">total closed</div><div class="num">{closed_total:,}</div></div>
  <div class="card hot"><div class="lbl">EXACT</div><div class="num">{exact:,}</div></div>
  <div class="card info"><div class="lbl">topology points</div><div class="num">{topo:,}</div></div>
  <div class="card info"><div class="lbl">discovery log</div><div class="num">{discovery:,}</div></div>
  <div class="card info"><div class="lbl">calc stubs</div><div class="num">{stubs:,}</div></div>
  <div class="card"><div class="lbl">100k milestone</div><div class="num">{pct_100k:.1f}%</div><div class="bar"><div class="bar-fill" style="width:{min(pct_100k,100)}%"></div></div></div>
</div>

<h2>🎯 top cross-project convergences (real discoveries)</h2>
<table><tr><th>value</th><th>count</th><th>sources</th></tr>
"""

for c in convergences:
    val = c['value']; cnt = c['count']; srcs = ', '.join(c['sources'][:4])
    html += f"<tr><td><b>{val}</b></td><td>{cnt}x</td><td class='tag'>{srcs}</td></tr>"

html += """</table>

<h2>📦 프로젝트별 진행상황</h2>
<table><tr><th>project</th><th>hyp files</th><th>topo points</th><th>closures</th><th>progress</th></tr>
"""

max_topo = max((p['topo_points'] for p in project_stats), default=1) or 1
for p in project_stats:
    pct = 100 * p['topo_points'] / max_topo if max_topo > 0 else 0
    html += f'<tr><td><b>{p["name"]}</b></td><td>{p["hyp_files"]}</td><td>{p["topo_points"]:,}</td><td>{p["closed"]:,}</td><td style="min-width:140px"><div class="bar"><div class="bar-fill" style="width:{pct:.0f}%"></div></div></td></tr>'

html += """</table>

<h2>📊 topology domains</h2>
<table><tr><th>domain</th><th>points</th><th>pct</th></tr>
"""

total_topo = sum(domains.values()) or 1
for dom, cnt in domains.most_common(15):
    pct = cnt*100/total_topo
    html += f"<tr><td>{dom}</td><td>{cnt:,}</td><td>{pct:.1f}%</td></tr>"

html += """</table>

<h2>📁 source projects (EXACT records)</h2>
<table><tr><th>project</th><th>records</th></tr>
"""

for proj, cnt in source_types.most_common(20):
    html += f"<tr><td>{proj}</td><td>{cnt:,}</td></tr>"

html += """</table>
<div class="meta">nexus6 singularity-recursion · 14 agents · auto-committed to feat/alien-index</div>
</body></html>
"""

out = os.path.expanduser('~/Dev/nexus6/shared/dashboard.html')
with open(out, 'w') as f: f.write(html)
print(f"[{ts}] dashboard → {out}")
print(f"  closed={closed_total:,} EXACT={exact:,} topo={topo:,}")
PYEOF
