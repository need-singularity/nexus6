#!/usr/bin/env bash
set -euo pipefail
NEXUS6="${HOME}/Dev/nexus6"

python3 << 'PYEOF'
import json, os
from datetime import datetime
from collections import Counter

HOME = os.path.expanduser('~')
NX = f'{HOME}/Dev/nexus6'

def cnt(p):
    try: return sum(1 for _ in open(p))
    except: return 0

closed = cnt(f'{NX}/shared/verified_constants.jsonl')
topo = cnt(f'{NX}/shared/cycle/topology.jsonl')
disc = cnt(f'{NX}/shared/discovery_log.jsonl')
stubs = len(os.listdir(f'{NX}/shared/calc/auto_stubs')) if os.path.isdir(f'{NX}/shared/calc/auto_stubs') else 0

status = Counter()
source_proj = Counter()
for l in open(f'{NX}/shared/verified_constants.jsonl'):
    try:
        j = json.loads(l)
        status[j.get('status','?')] += 1
        source_proj[j.get('project','?')] += 1
    except: pass
exact = status.get('EXACT', 0)

# Domains
domains = Counter()
for i,l in enumerate(open(f'{NX}/shared/cycle/topology.jsonl')):
    if i > 15000: break
    try: domains[json.loads(l).get('domain','?')] += 1
    except: pass

# Per-project stats
projects_json = f'{NX}/shared/projects.json'
project_stats = []
try:
    pj = json.loads(open(projects_json).read())
    for pname, pcfg in pj.get('projects',{}).items():
        proot = f'{HOME}/Dev/{pcfg.get("root",pname)}'
        hyp_count = 0
        for sd in pcfg.get('hypothesis_dirs',[]):
            dp = f'{proot}/{sd}'
            if os.path.isdir(dp):
                for _,_,files in os.walk(dp):
                    hyp_count += sum(1 for f in files if f.endswith('.md') and 'NEXUS6' not in f)
        dom_key = f'hypothesis:{pname}'
        pts = domains.get(dom_key, 0)
        cls = sum(c for p,c in source_proj.items() if pname.lower() in p.lower())
        project_stats.append({
            'name': pname, 'hyp': hyp_count, 'topo': pts, 'closed': cls
        })
    project_stats.sort(key=lambda x: -(x['topo']+x['closed']))
except: pass

# Milestone
milestones = [1000, 2500, 5000, 7500, 10000, 20000, 50000, 100000, 200000, 500000, 1000000]
next_ms = next((m for m in milestones if m > closed), milestones[-1])
pct_ms = closed * 100 / next_ms
bar_fill = int(pct_ms / 5)  # 20 cells

ts = datetime.now().strftime('%Y-%m-%d %H:%M')
max_topo = max((p['topo'] for p in project_stats), default=1) or 1

def status_icon(p):
    if p['topo'] > 1000: return '🔥'
    if p['topo'] > 100: return '✅'
    if p['topo'] > 10: return '🔄'
    if p['closed'] > 10: return '⏳'
    return '░'

html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>🛸 nexus6 dashboard</title>
<meta http-equiv="refresh" content="60">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font:13px -apple-system,BlinkMacSystemFont,sans-serif;background:#0a0a0a;color:#ddd;padding:20px;max-width:1400px;margin:0 auto;}}
h1{{color:#8ef;font-size:22px;margin:0 0 4px;}}
.meta{{color:#555;font-size:10px;margin-bottom:20px;}}
.hero{{background:linear-gradient(135deg,#1a2e3e,#0d1419);padding:20px;border-radius:8px;margin-bottom:20px;border:1px solid #253648;}}
.hero-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:16px;}}
.stat{{text-align:left;}}
.stat-num{{font-size:28px;color:#8ef;font-weight:700;line-height:1;}}
.stat-lbl{{font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1.5px;margin-top:4px;}}
.milestone-bar{{margin-top:14px;background:#0d1419;border-radius:4px;padding:3px;border:1px solid #253648;}}
.mbar{{height:10px;background:linear-gradient(90deg,#4a9,#8ef,#4a9);border-radius:2px;}}
h2{{color:#8ef;font-size:13px;margin:28px 0 12px;border-bottom:1px solid #222;padding-bottom:6px;letter-spacing:1px;text-transform:uppercase;}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;}}
.card{{background:#111;padding:14px;border-radius:6px;border-left:3px solid #333;transition:border-color .2s;}}
.card.hot{{border-left-color:#f80;}}
.card.ok{{border-left-color:#4a9;}}
.card.active{{border-left-color:#8ef;}}
.card.idle{{border-left-color:#444;}}
.card-hdr{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:10px;}}
.card-name{{font-size:14px;font-weight:600;color:#fff;}}
.card-icon{{font-size:16px;}}
.card-metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;}}
.metric{{font-size:10px;}}
.metric-num{{font-size:16px;color:#8ef;font-weight:600;display:block;}}
.metric-lbl{{color:#555;text-transform:uppercase;letter-spacing:1px;font-size:9px;}}
.prog{{margin-top:10px;background:#1a1a1a;height:4px;border-radius:2px;overflow:hidden;}}
.prog-fill{{height:100%;background:linear-gradient(90deg,#4a9,#8ef);}}
table{{width:100%;border-collapse:collapse;}}
th,td{{padding:5px 10px;text-align:left;border-bottom:1px solid #1a1a1a;font-size:11px;}}
th{{color:#8ef;text-transform:uppercase;letter-spacing:1px;font-weight:600;font-size:9px;}}
td.num{{font-family:Menlo,monospace;color:#8ef;text-align:right;}}
.tag{{display:inline-block;background:#1e2e3e;padding:2px 6px;border-radius:3px;font-size:9px;color:#8ef;font-family:Menlo,monospace;}}
</style></head><body>
<h1>🛸 nexus6 autonomous system</h1>
<div class="meta">last refresh {ts} · auto-reload 60s · 16 LaunchAgents</div>

<div class="hero">
  <div class="hero-grid">
    <div class="stat"><div class="stat-num">{closed:,}</div><div class="stat-lbl">Total Closed</div></div>
    <div class="stat"><div class="stat-num">{exact:,}</div><div class="stat-lbl">EXACT</div></div>
    <div class="stat"><div class="stat-num">{topo:,}</div><div class="stat-lbl">Topology Σ</div></div>
    <div class="stat"><div class="stat-num">{disc:,}</div><div class="stat-lbl">Discovery Log</div></div>
    <div class="stat"><div class="stat-num">{stubs}</div><div class="stat-lbl">Calc Stubs</div></div>
    <div class="stat"><div class="stat-num">{pct_ms:.0f}%</div><div class="stat-lbl">→{next_ms//1000}k</div></div>
  </div>
  <div class="milestone-bar"><div class="mbar" style="width:{min(pct_ms,100):.1f}%"></div></div>
</div>

<h2>📦 프로젝트별 진행상황</h2>
<div class="grid">
"""

for p in project_stats:
    name = p['name']
    pts = p['topo']; cls = p['closed']; hyp = p['hyp']
    icon = status_icon(p)
    prog = 100 * pts / max_topo if max_topo > 0 else 0
    css_class = 'hot' if pts > 1000 else 'active' if pts > 100 else 'ok' if cls > 10 else 'idle'
    html += f"""  <div class="card {css_class}">
    <div class="card-hdr"><span class="card-name">{name}</span><span class="card-icon">{icon}</span></div>
    <div class="card-metrics">
      <div class="metric"><span class="metric-num">{hyp:,}</span><span class="metric-lbl">hyp files</span></div>
      <div class="metric"><span class="metric-num">{pts:,}</span><span class="metric-lbl">topo pts</span></div>
      <div class="metric"><span class="metric-num">{cls:,}</span><span class="metric-lbl">closures</span></div>
    </div>
    <div class="prog"><div class="prog-fill" style="width:{prog:.0f}%"></div></div>
  </div>
"""

html += """</div>

<h2>📊 Topology Domains</h2>
<table><tr><th>domain</th><th>points</th><th>%</th></tr>
"""
total_topo_sum = sum(domains.values()) or 1
for d,c in domains.most_common(10):
    pct = c*100/total_topo_sum
    html += f'<tr><td><span class="tag">{d}</span></td><td class="num">{c:,}</td><td class="num">{pct:.1f}%</td></tr>'

html += """</table>

<h2>⚙️ Agent Health</h2>
<div class="grid">
"""

# Check each agent's last-run log mtime
import time
agents_config = [
    ('closure-sweep', 300, 'closure-sweep.log'),
    ('publish-insights', 600, 'publish-insights.log'),
    ('gen-calc-stubs', 900, 'gen-calc-stubs.log'),
    ('paper-gen', 3600, 'paper-gen.log'),
    ('auto-commit', 1800, 'auto-commit.log'),
    ('dashboard', 600, 'dashboard.log'),
    ('self-improve', 1800, 'self-improve.log'),
    ('evolve-loop', 3600, 'evolve-loop.log'),
    ('scan-loop', 1800, 'scan-loop.log'),
    ('physics-fetch', 86400, 'physics-fetch.log'),
    ('cycle-tick', 60, 'singularity-daemon.log'),
    ('watch-atlas', 30, 'watch-atlas.log'),
    ('watch-papers', 300, 'watch-papers.log'),
]
logs_dir = f'{HOME}/Library/Logs/nexus6'
now_ts = time.time()
for name, interval, logfile in agents_config:
    logpath = f'{logs_dir}/{logfile}'
    if os.path.exists(logpath):
        mtime = os.path.getmtime(logpath)
        age_sec = int(now_ts - mtime)
        if age_sec < 60: age_str = f'{age_sec}s'
        elif age_sec < 3600: age_str = f'{age_sec//60}m'
        else: age_str = f'{age_sec//3600}h'
        healthy = age_sec < interval * 3  # within 3x expected interval
        icon = '🟢' if healthy else '🟡' if age_sec < interval * 10 else '🔴'
        css = 'ok' if healthy else 'idle'
    else:
        age_str = 'never'
        icon = '⚪'
        css = 'idle'
    html += f"""  <div class="card {css}">
    <div class="card-hdr"><span class="card-name">{name}</span><span class="card-icon">{icon}</span></div>
    <div class="card-metrics">
      <div class="metric"><span class="metric-num">{age_str}</span><span class="metric-lbl">last run</span></div>
      <div class="metric"><span class="metric-num">{interval//60 if interval>=60 else interval}{'m' if interval>=60 else 's'}</span><span class="metric-lbl">interval</span></div>
      <div class="metric"><span class="metric-num">{'OK' if healthy else 'LAG'}</span><span class="metric-lbl">status</span></div>
    </div>
  </div>
"""

html += """</div>
</body></html>"""

out = f'{NX}/shared/dashboard.html'
with open(out, 'w') as f: f.write(html)
print(f"[{ts}] dashboard → {out} ({len(html)}B)")
print(f"  closed={closed:,} exact={exact:,} topo={topo:,} projects={len(project_stats)}")
PYEOF
