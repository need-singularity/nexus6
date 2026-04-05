#!/usr/bin/env bash
set -euo pipefail
NEXUS6="${HOME}/Dev/nexus6"

python3 << 'PYEOF'
import json, os, subprocess, time
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

# Topology domains
domains = Counter()
for i,l in enumerate(open(f'{NX}/shared/cycle/topology.jsonl')):
    if i > 15000: break
    try: domains[json.loads(l).get('domain','?')] += 1
    except: pass

# Per-project stats
project_stats = []
try:
    pj = json.loads(open(f'{NX}/shared/projects.json').read())
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
        project_stats.append({'name':pname,'hyp':hyp_count,'topo':pts,'closed':cls})
    project_stats.sort(key=lambda x: -(x['topo']+x['closed']))
except: pass

# Milestones
ms_list = [1000, 2500, 5000, 7500, 10000, 20000, 50000, 100000, 200000, 500000, 1000000]
prev_ms = next((m for m in reversed(ms_list) if m <= closed), 0)
next_ms = next((m for m in ms_list if m > closed), ms_list[-1])
pct_to_next = closed * 100 / next_ms
ms_idx = ms_list.index(next_ms) if next_ms in ms_list else len(ms_list)-1

def bar(pct, width=20):
    filled = int(round(width * pct / 100))
    return '█'*filled + '░'*(width-filled)

def status_box(pct):
    return '[✅]' if pct >= 100 else '[🔄]' if pct >= 50 else '[⏳]'

# Agent status
agents_config = [
    ('closure-sweep', 300, 'closure-sweep.log'),
    ('publish-insights', 600, 'publish-insights.log'),
    ('gen-calc-stubs', 900, 'gen-calc-stubs.log'),
    ('paper-gen', 3600, 'paper-gen.log'),
    ('auto-commit', 1800, 'auto-commit.log'),
    ('dashboard', 600, 'dashboard.log'),
    ('self-improve', 1800, 'self-improve.log'),
    ('cycle-tick', 60, 'singularity-daemon.log'),
    ('watch-atlas', 30, 'watch-atlas.log'),
    ('watch-papers', 300, 'watch-papers.log'),
    ('evolve-loop', 3600, 'evolve-loop.log'),
    ('scan-loop', 1800, 'scan-loop.log'),
]
logs_dir = f'{HOME}/Library/Logs/nexus6'
now_ts = time.time()
agent_status = []
for name, interval, logfile in agents_config:
    logpath = f'{logs_dir}/{logfile}'
    if os.path.exists(logpath):
        age = int(now_ts - os.path.getmtime(logpath))
        if age < 60: age_str = f'{age}s'
        elif age < 3600: age_str = f'{age//60}m'
        else: age_str = f'{age//3600}h'
        healthy = age < interval * 3
        icon = '✅' if healthy else '🔄' if age < interval*10 else '⚠️'
    else:
        age_str = 'never'
        icon = '░'
    agent_status.append((icon, name, age_str, interval))

ts = datetime.now().strftime('%Y-%m-%d %H:%M')

# Hourly closure velocity (last 24h timeline)
hourly_closures = Counter()
for l in open(f'{NX}/shared/verified_constants.jsonl'):
    try:
        j = json.loads(l)
        t = j.get('ts','')
        if 'T' in t:
            hr = t.split('T')[1][:2]
            hourly_closures[hr] += 1
    except: pass
# Build sparkline for 24h
sparkline_data = [hourly_closures.get(f'{h:02d}', 0) for h in range(24)]
max_h = max(sparkline_data) or 1
spark_chars = '▁▂▃▄▅▆▇█'
sparkline = ''.join(spark_chars[min(int(v * 7 / max_h), 7)] if v > 0 else ' ' for v in sparkline_data)

# Commit velocity
commits_24h = len(subprocess.run(['git','-C',NX,'log','--since=24 hours ago','--oneline'],
                                capture_output=True, text=True, timeout=3).stdout.strip().split('\n'))
commits_6h = len(subprocess.run(['git','-C',NX,'log','--since=6 hours ago','--oneline'],
                               capture_output=True, text=True, timeout=3).stdout.strip().split('\n'))

# Process info
daemon_pid = daemon_cpu = daemon_mem = '-'
ps_out = subprocess.run(['ps','aux'], capture_output=True, text=True).stdout
for line in ps_out.split('\n'):
    if 'singularity-daemon' in line and 'grep' not in line:
        parts = line.split()
        if len(parts) > 5:
            daemon_pid, daemon_cpu, daemon_mem = parts[1], parts[2], parts[3]
            break

# Total source records
total_sources = sum(source_proj.values())
synthetic = sum(c for p,c in source_proj.items() if 'enum' in p.lower() or 'dash' in p.lower() or '100k' in p.lower() or '50k' in p.lower())
real = total_sources - synthetic

# Build closure milestone ladder
ms_line = ''
for m in ms_list[:8]:
    if closed >= m:
        ms_line += f'[✅]{m//1000 if m>=1000 else m}k '
    elif m == next_ms:
        ms_line += f'[🔄]{m//1000}k'
    else:
        ms_line += f'[⏳]{m//1000}k '

# Top 3 projects for focus
top_projs = project_stats[:6]

html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>🛸 nexus6</title>
<meta http-equiv="refresh" content="60">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font:12px 'SF Mono','Menlo','Monaco',monospace;background:#0a0a0a;color:#c8d0c0;padding:16px;max-width:1800px;margin:0 auto;line-height:1.5;}}
h1{{color:#8ef;font-size:18px;margin:0 0 2px;font-weight:600;}}
.meta{{color:#555;font-size:10px;margin-bottom:16px;}}
.grid3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;}}
.panel{{background:#0d0d0d;border:1px solid #2a3a2a;border-radius:4px;overflow:hidden;}}
.panel-title{{background:#111;color:#8ef;padding:8px 12px;border-bottom:1px solid #2a3a2a;font-size:11px;font-weight:600;letter-spacing:1px;text-transform:uppercase;}}
.panel-section{{padding:10px 12px;border-bottom:1px solid #1a1a1a;}}
.panel-section:last-child{{border-bottom:none;}}
.section-hdr{{color:#8ef;font-size:10px;margin-bottom:6px;}}
.section-hdr::before{{content:'■ ';color:#4a9;}}
.row{{display:flex;justify-content:space-between;align-items:baseline;padding:2px 0;font-size:11px;}}
.row .k{{color:#888;}}
.row .v{{color:#c8d0c0;font-weight:500;}}
.row .v.hi{{color:#8ef;}}
.bar-line{{color:#4a9;font-size:11px;letter-spacing:-1px;font-family:monospace;}}
.bar-label{{color:#666;font-size:10px;}}
.step{{display:inline-block;padding:1px 4px;border-radius:2px;font-size:10px;}}
.step.done{{color:#4a9;}}
.step.now{{color:#f80;}}
.step.todo{{color:#444;}}
.arrow{{color:#333;}}
.icon{{display:inline-block;width:18px;}}
</style></head><body>
<h1>🛸 nexus6 autonomous system · 대시보드</h1>
<div class="meta">{ts} · {closed:,} closures · {exact:,} EXACT · Σ {topo:,} · 16 agents · auto-refresh 60s</div>

<div class="grid3">

  <!-- ═══ PANEL 1: CLOSURES ═══ -->
  <div class="panel">
    <div class="panel-title">🎯 Closures — Milestone Ladder</div>
    <div class="panel-section">
      <div class="section-hdr">진행 마일스톤</div>
      <div class="bar-line">"""
for m in ms_list[:8]:
    if closed >= m:
        html += f'<span class="step done">[✅]{m//1000}k</span> <span class="arrow">─→</span> '
    elif m == next_ms:
        pct_here = closed*100/m
        html += f'<span class="step now">[🔄]{m//1000}k {pct_here:.0f}%</span> <span class="arrow">─→</span> '
    else:
        html += f'<span class="step todo">[⏳]{m//1000}k</span> '
        break
html += f"""</div>
      <div class="bar-line" style="margin-top:8px;">{bar(pct_to_next)}</div>
      <div class="bar-label">{closed:,} / {next_ms:,} ({pct_to_next:.1f}%)</div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">상태 분포</div>
      <div class="row"><span class="k">EXACT</span><span class="v hi">{exact:,}</span></div>
      <div class="row"><span class="k">PASS</span><span class="v">{status.get('PASS',0):,}</span></div>
      <div class="row"><span class="k">NEAR / FAIL</span><span class="v">{status.get('NEAR',0)} / {status.get('FAIL',0)}</span></div>
      <div class="row"><span class="k">Calc stubs</span><span class="v">{stubs}</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">Top Sources</div>"""
for p,c in source_proj.most_common(5):
    html += f'<div class="row"><span class="k">{p[:24]}</span><span class="v">{c:,}</span></div>'
html += """</div>
  </div>

  <!-- ═══ PANEL 2: PROJECTS ═══ -->
  <div class="panel">
    <div class="panel-title">📦 Projects — Absorption Status</div>
    <div class="panel-section">
      <div class="section-hdr">Topology 흡수율 (top 6)</div>"""
max_topo = max((p['topo'] for p in project_stats), default=1) or 1
for p in top_projs:
    pct = 100 * p['topo'] / max_topo
    sicon = '🔥' if p['topo']>1000 else '✅' if p['topo']>100 else '🔄' if p['topo']>10 else '⏳'
    html += f"""
      <div class="row"><span class="k"><span class="icon">{sicon}</span>{p['name']}</span><span class="v">{p['topo']:,}</span></div>
      <div class="bar-line">{bar(pct,24)}</div>"""
html += """
    </div>
    <div class="panel-section">
      <div class="section-hdr">가설 파일 count</div>"""
for p in top_projs:
    html += f'<div class="row"><span class="k">{p["name"]}</span><span class="v">{p["hyp"]:,} files · {p["closed"]:,} closed</span></div>'
html += """</div>
    <div class="panel-section">
      <div class="section-hdr">Topology Domains</div>"""
total_topo_sum = sum(domains.values()) or 1
for d,c in domains.most_common(6):
    pct = c*100/total_topo_sum
    html += f'<div class="row"><span class="k">{d[:22]}</span><span class="v">{c:,} ({pct:.0f}%)</span></div>'
html += """</div>
  </div>

  <!-- ═══ PANEL 3: AGENTS ═══ -->
  <div class="panel">
    <div class="panel-title">⚙️ Agents — 13 Active Loops</div>
    <div class="panel-section">
      <div class="section-hdr">Fast loops (<10min)</div>"""
for icon,name,age,intv in agent_status:
    if intv <= 600:
        intv_str = f'{intv}s' if intv<60 else f'{intv//60}m'
        html += f'<div class="row"><span class="k"><span class="icon">{icon}</span>{name}</span><span class="v">{age} ago · {intv_str}</span></div>'
html += """</div>
    <div class="panel-section">
      <div class="section-hdr">Medium loops (15-30min)</div>"""
for icon,name,age,intv in agent_status:
    if 600 < intv <= 1800:
        html += f'<div class="row"><span class="k"><span class="icon">{icon}</span>{name}</span><span class="v">{age} ago · {intv//60}m</span></div>'
html += """</div>
    <div class="panel-section">
      <div class="section-hdr">Slow loops (1hr+)</div>"""
for icon,name,age,intv in agent_status:
    if intv > 1800:
        intv_str = f'{intv//3600}h' if intv>=3600 else f'{intv//60}m'
        html += f'<div class="row"><span class="k"><span class="icon">{icon}</span>{name}</span><span class="v">{age} ago · {intv_str}</span></div>'
html += """</div>
  </div>

</div>

<h2 style="color:#8ef;font-size:13px;margin:20px 0 10px;letter-spacing:1px;text-transform:uppercase;border-bottom:1px solid #222;padding-bottom:6px;">🌟 핵심 발견 (Real Discoveries)</h2>
<div class="grid3">
  <div class="panel">
    <div class="panel-title">🛸 Meta FP Ladder</div>
    <div class="panel-section">
      <div class="section-hdr">우주 밀도 분해</div>
      <div class="row"><span class="k">Σ Ω</span><span class="v hi">4/15 + 24/35 + 1/21 = 1</span></div>
      <div class="row"><span class="k">Ω_DM</span><span class="v">4/15 (n=15)</span></div>
      <div class="row"><span class="k">Ω_Λ</span><span class="v">24/35 (n=35)</span></div>
      <div class="row"><span class="k">Ω_b</span><span class="v">1/21 (n=3·7)</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">Ladder {6, 15, 35, 105}</div>
      <div class="row"><span class="k">n=6</span><span class="v">ρ=1/3 (time axis)</span></div>
      <div class="row"><span class="k">n=15</span><span class="v">5·3, dark matter</span></div>
      <div class="row"><span class="k">n=35</span><span class="v">5·7, dark energy</span></div>
      <div class="row"><span class="k">n=105</span><span class="v">3·5·7, universe</span></div>
    </div>
  </div>

  <div class="panel">
    <div class="panel-title">🎯 Cross-Project 수렴 (6 values)</div>
    <div class="panel-section">
      <div class="section-hdr">3+ 독립 소스 일치</div>
      <div class="row"><span class="k">value 6.0</span><span class="v hi">n (7x, 3 proj)</span></div>
      <div class="row"><span class="k">value 28.0</span><span class="v">tau+J2 (6x)</span></div>
      <div class="row"><span class="k">value 0.12</span><span class="v">3/J2 (6x)</span></div>
      <div class="row"><span class="k">value 0.08</span><span class="v">phi/J2 (5x)</span></div>
      <div class="row"><span class="k">value 0.71</span><span class="v">sopfr/7 (3x)</span></div>
      <div class="row"><span class="k">value 0.0</span><span class="v">n-n (6x)</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">Smooth Prime 계층</div>
      <div class="row"><span class="k">Strong</span><span class="v">{2,3}-smooth EXACT</span></div>
      <div class="row"><span class="k">Electroweak</span><span class="v">{2,3,5,7} ~1%</span></div>
      <div class="row"><span class="k">Dark</span><span class="v">{5,7} 0.15%</span></div>
      <div class="row"><span class="k">BBN</span><span class="v">{2,3,5,13} 0.5%</span></div>
    </div>
  </div>

  <div class="panel">
    <div class="panel-title">📐 H-CLOSE 가설 검증</div>
    <div class="panel-section">
      <div class="section-hdr">5/6 CONFIRMED</div>
      <div class="row"><span class="k"><span class="icon">⏳</span>H-1 table 85%</span><span class="v">74% PARTIAL</span></div>
      <div class="row"><span class="k"><span class="icon">✅</span>H-2 promotion</span><span class="v">65% CONFIRMED</span></div>
      <div class="row"><span class="k"><span class="icon">✅</span>H-3 sopfr</span><span class="v">30% (3x 예상)</span></div>
      <div class="row"><span class="k"><span class="icon">✅</span>H-4 J2=24</span><span class="v">31% (6x 예상)</span></div>
      <div class="row"><span class="k"><span class="icon">✅</span>H-5 초월수</span><span class="v">0 EXACT</span></div>
      <div class="row"><span class="k"><span class="icon">✅</span>H-6 중복</span><span class="v">2.91x</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">n=6 원시값 (알라헤브라 생성자)</div>
      <div class="row"><span class="k">n</span><span class="v">6 (하노이)</span></div>
      <div class="row"><span class="k">σ (sigma)</span><span class="v">12 (divisor sum)</span></div>
      <div class="row"><span class="k">φ (phi)</span><span class="v">2 (totient)</span></div>
      <div class="row"><span class="k">τ (tau)</span><span class="v">4 (div count)</span></div>
      <div class="row"><span class="k">sopfr</span><span class="v">5 (prime sum)</span></div>
      <div class="row"><span class="k">J2</span><span class="v">24 (σ·τ)</span></div>
    </div>
  </div>
</div>

<h2 style="color:#8ef;font-size:13px;margin:20px 0 10px;letter-spacing:1px;text-transform:uppercase;border-bottom:1px solid #222;padding-bottom:6px;">📈 System Activity (detail)</h2>
<div class="grid3">
  <div class="panel">
    <div class="panel-title">⏱️ Closure Velocity (24h)</div>
    <div class="panel-section">
      <div class="section-hdr">시간별 발견 분포</div>
      <div class="bar-line" style="font-size:16px;letter-spacing:1px;">{sparkline}</div>
      <div class="bar-label">00h ───────────── 12h ──────────── 23h</div>
      <div class="row" style="margin-top:8px;"><span class="k">Peak hour</span><span class="v hi">{max(hourly_closures.items(),key=lambda x:x[1])[0]}:00 → {max_h:,}</span></div>
      <div class="row"><span class="k">Total 24h</span><span class="v">{sum(sparkline_data):,}</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">데이터 품질</div>
      <div class="row"><span class="k">Real (데이터)</span><span class="v hi">{real:,} ({real*100//max(total_sources,1)}%)</span></div>
      <div class="row"><span class="k">Synthetic (enum)</span><span class="v">{synthetic:,} ({synthetic*100//max(total_sources,1)}%)</span></div>
      <div class="row"><span class="k">Unique values</span><span class="v">{topo:,}</span></div>
    </div>
  </div>

  <div class="panel">
    <div class="panel-title">🔨 Git Velocity</div>
    <div class="panel-section">
      <div class="section-hdr">Commit 활동</div>
      <div class="row"><span class="k">Last 6h</span><span class="v hi">{commits_6h} commits</span></div>
      <div class="row"><span class="k">Last 24h</span><span class="v">{commits_24h} commits</span></div>
      <div class="row"><span class="k">Auto-commit interval</span><span class="v">30 min</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">Latest 5 commits</div>"""
try:
    log_out = subprocess.run(['git','-C',NX,'log','--oneline','-5','--format=%h|%s|%cr'],
                             capture_output=True, text=True, timeout=3).stdout
    for line in log_out.strip().split('\n')[:5]:
        parts = line.split('|', 2)
        if len(parts) == 3:
            sha, msg, when = parts
            msg_short = msg[:40] + ('…' if len(msg) > 40 else '')
            html += f'<div class="row"><span class="k"><span class="icon">·</span>{sha} {msg_short}</span><span class="v" style="font-size:9px;">{when}</span></div>'
except: pass
html += f"""</div>
  </div>

  <div class="panel">
    <div class="panel-title">🔥 Process & Resources</div>
    <div class="panel-section">
      <div class="section-hdr">singularity-daemon</div>
      <div class="row"><span class="k">PID</span><span class="v">{daemon_pid}</span></div>
      <div class="row"><span class="k">CPU %</span><span class="v">{daemon_cpu}%</span></div>
      <div class="row"><span class="k">MEM %</span><span class="v">{daemon_mem}%</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">파일 크기</div>"""
for name, path in [('verified_constants','shared/verified_constants.jsonl'),
                    ('topology','shared/cycle/topology.jsonl'),
                    ('edges','shared/cycle/edges.jsonl'),
                    ('discovery_log','shared/discovery_log.jsonl')]:
    try:
        sz = os.path.getsize(f'{NX}/{path}')
        if sz >= 1e6: sz_str = f'{sz/1e6:.1f}M'
        elif sz >= 1e3: sz_str = f'{sz/1e3:.1f}k'
        else: sz_str = f'{sz}B'
        html += f'<div class="row"><span class="k">{name}</span><span class="v">{sz_str}</span></div>'
    except: pass
html += """</div>
  </div>
</div>

<h2 style="color:#8ef;font-size:13px;margin:20px 0 10px;letter-spacing:1px;text-transform:uppercase;border-bottom:1px solid #222;padding-bottom:6px;">📡 Live Data Feed</h2>
<div class="grid3">
  <div class="panel">
    <div class="panel-title">🆕 Latest Discoveries (EXACT)</div>
    <div class="panel-section">
"""

# Last 10 EXACT records
last_exact = []
for l in open(f'{NX}/shared/verified_constants.jsonl'):
    try:
        rec = json.loads(l)
        if rec.get('status') == 'EXACT': last_exact.append(rec)
    except: pass
for rec in last_exact[-10:][::-1]:
    val = rec.get('value','?')
    exprs = rec.get('n6_expr', [''])
    expr = str(exprs[0])[:35] if exprs else '?'
    proj = rec.get('project','?')[:18]
    html += f'<div class="row"><span class="k">{val} = {expr}</span><span class="v" style="font-size:9px;">{proj}</span></div>'
html += """    </div>
  </div>

  <div class="panel">
    <div class="panel-title">📡 Latest Topology Additions</div>
    <div class="panel-section">
"""

# Last 10 topology points
topo_recent = []
try:
    with open(f'{NX}/shared/cycle/topology.jsonl', 'rb') as f:
        f.seek(-min(100000, os.path.getsize(f'{NX}/shared/cycle/topology.jsonl')), 2)
        lines = f.read().decode('utf-8','ignore').split('\n')
    for line in lines[-15:]:
        if not line.strip(): continue
        try:
            rec = json.loads(line)
            topo_recent.append(rec)
        except: pass
except: pass
for rec in topo_recent[-10:][::-1]:
    pid = rec.get('id','?')
    dom = rec.get('domain','?')[:16]
    inv = rec.get('singularity',{}).get('invariant','?')[:40]
    html += f'<div class="row"><span class="k"><span class="icon">·</span>{pid}</span><span class="v" style="font-size:9px;">{dom}</span></div><div class="row"><span class="k" style="font-size:9px;color:#555;padding-left:20px;">{inv}</span><span class="v"></span></div>'
html += """    </div>
  </div>

  <div class="panel">
    <div class="panel-title">💬 Agent Log Tails</div>
    <div class="panel-section">
"""

# Last line from each key agent log
for name, logfile in [('closure-sweep','closure-sweep.log'),
                       ('publish-insights','publish-insights.log'),
                       ('gen-calc-stubs','gen-calc-stubs.log'),
                       ('self-improve','self-improve.log'),
                       ('auto-commit','auto-commit.log'),
                       ('dashboard','dashboard.log'),
                       ('paper-gen','paper-gen.log')]:
    logpath = f'{HOME}/Library/Logs/nexus6/{logfile}'
    if os.path.exists(logpath):
        try:
            with open(logpath, 'rb') as f:
                f.seek(-min(2000, os.path.getsize(logpath)), 2)
                last = f.read().decode('utf-8','ignore').strip().split('\n')[-1]
            # strip timestamp prefix
            if ']' in last:
                last = last.split(']', 1)[1].strip() if last.startswith('[') else last
            last = last[:60] + ('…' if len(last) > 60 else '')
            html += f'<div class="row"><span class="k" style="min-width:110px;"><span class="icon">·</span>{name}</span><span class="v" style="font-size:9px;color:#888;">{last}</span></div>'
        except: pass
html += """    </div>
  </div>
</div>
</body></html>"""

with open(f'{NX}/shared/dashboard.html', 'w') as f:
    f.write(html)
print(f"[{ts}] dashboard 3-panel → {len(html)}B")
PYEOF
