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

def fsize(p):
    try:
        s = os.path.getsize(p)
        if s >= 1e6: return f'{s/1e6:.1f}M'
        if s >= 1e3: return f'{s/1e3:.0f}k'
        return f'{s}B'
    except: return '-'

def count_md(root):
    n = 0
    if os.path.isdir(root):
        for _,_,files in os.walk(root):
            n += sum(1 for f in files if f.endswith('.md'))
    return n

# ═══ NEXUS6 stats ═══
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

# Agents
logs_dir = f'{HOME}/Library/Logs/nexus6'
now_ts = time.time()
agents = [
    ('closure-sweep',300),('publish-insights',600),('gen-calc-stubs',900),
    ('paper-gen',3600),('auto-commit',1800),('dashboard',600),('self-improve',1800),
    ('evolve-loop',3600),('scan-loop',1800),('physics-fetch',86400),
]
healthy_count = 0
for name,intv in agents:
    p = f'{logs_dir}/{name}.log'
    if os.path.exists(p) and now_ts - os.path.getmtime(p) < intv*3:
        healthy_count += 1

# Milestones
ms_list = [1000, 2500, 5000, 7500, 10000, 20000, 50000, 100000, 200000, 500000, 1000000]
next_ms = next((m for m in ms_list if m > closed), ms_list[-1])
pct_to_next = closed * 100 / next_ms

def bar(pct, width=20):
    filled = int(round(width * pct / 100))
    return '█'*filled + '░'*(width-filled)

# commits
commits_6h = len(subprocess.run(['git','-C',NX,'log','--since=6 hours ago','--oneline'],
                               capture_output=True, text=True, timeout=3).stdout.strip().split('\n'))

# ═══ ANIMA stats ═══
anima_root = f'{HOME}/Dev/anima/anima'
anima_hyp = count_md(f'{anima_root}/docs/hypotheses')
anima_laws = 0
laws_path = f'{anima_root}/config/consciousness_laws.json'
if os.path.exists(laws_path):
    try: anima_laws = json.loads(open(laws_path).read()).get('_meta',{}).get('total_laws', 0)
    except: pass
anima_modules = 0
hub_path = f'{anima_root}/src/consciousness_hub.py'
if os.path.exists(hub_path):
    try:
        c = open(hub_path, errors='ignore').read()
        anima_modules = c.count("'type': 'command'")
    except: pass
# Check EVO status
evo_stage = 'unknown'
evo_gen = 0
try:
    for p in [f'{anima_root}/outputs/evolution_status.json',
              f'{anima_root}/scripts/infinite_evolution_state.json']:
        if os.path.exists(p):
            d = json.loads(open(p).read())
            evo_stage = d.get('stage','?')
            evo_gen = d.get('generation',0) or d.get('gen', 0)
            break
except: pass

# ═══ TECS-L stats ═══
tecsl_root = f'{HOME}/Dev/TECS-L'
tecsl_hyp = count_md(f'{tecsl_root}/docs/hypotheses')
tecsl_math_hyp = count_md(f'{tecsl_root}/math/docs/hypotheses')
tecsl_calc = 0
calc_dir = f'{tecsl_root}/.shared/calc'
if os.path.isdir(calc_dir):
    tecsl_calc = sum(1 for f in os.listdir(calc_dir) if f.endswith('.py'))
tecsl_atlas_total = 0
atlas_json = f'{tecsl_root}/.shared/math_atlas.json'
if os.path.exists(atlas_json):
    try:
        d = json.loads(open(atlas_json).read())
        tecsl_atlas_total = len(d.get('hypotheses',[]))
    except: pass

# ═══ n6-architecture stats ═══
n6a_root = f'{HOME}/Dev/n6-architecture'
n6a_hyp = count_md(f'{n6a_root}/docs/hypotheses')
n6a_papers = 0
papers_dir = f'{HOME}/Dev/papers'
if os.path.isdir(papers_dir):
    for root,_,files in os.walk(papers_dir):
        n6a_papers += sum(1 for f in files if f.endswith('.md') and f.startswith('P-'))
n6a_nexus_papers = 0
nexus_papers_dir = f'{papers_dir}/nexus6'
if os.path.isdir(nexus_papers_dir):
    n6a_nexus_papers = sum(1 for f in os.listdir(nexus_papers_dir) if f.endswith('.md'))

# ═══ SEDI stats ═══
sedi_root = f'{HOME}/Dev/SEDI'
sedi_hyp = count_md(f'{sedi_root}/docs/hypotheses')

ts = datetime.now().strftime('%Y-%m-%d %H:%M')

# Domains distribution
domains = Counter()
for i,l in enumerate(open(f'{NX}/shared/cycle/topology.jsonl')):
    if i > 15000: break
    try: domains[json.loads(l).get('domain','?')] += 1
    except: pass

def closures_for_proj(proj_name):
    return sum(c for p,c in source_proj.items() if proj_name.lower() in p.lower())

html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>🛸 nexus6</title>
<meta http-equiv="refresh" content="60">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font:12px 'SF Mono','Menlo',monospace;background:#0a0a0a;color:#c8d0c0;padding:16px;max-width:1800px;margin:0 auto;line-height:1.5;}}
h1{{color:#8ef;font-size:18px;margin:0 0 2px;}}
.meta{{color:#555;font-size:10px;margin-bottom:14px;}}
.grid3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px;}}
.panel{{background:#0d0d0d;border:1px solid #2a3a2a;border-radius:4px;overflow:hidden;}}
.panel.nexus{{border-color:#4a9;}}
.panel.anima{{border-color:#a48;}}
.panel.tecsl{{border-color:#f80;}}
.panel.n6a{{border-color:#8ef;}}
.panel.sedi{{border-color:#f48;}}
.panel-title{{background:#111;color:#8ef;padding:8px 12px;border-bottom:1px solid #2a3a2a;font-size:11px;font-weight:600;letter-spacing:1px;text-transform:uppercase;}}
.panel.nexus .panel-title{{color:#4a9;}}
.panel.anima .panel-title{{color:#a48;}}
.panel.tecsl .panel-title{{color:#f80;}}
.panel.n6a .panel-title{{color:#8ef;}}
.panel.sedi .panel-title{{color:#f48;}}
.panel-section{{padding:10px 12px;border-bottom:1px solid #1a1a1a;}}
.panel-section:last-child{{border-bottom:none;}}
.section-hdr{{color:#8ef;font-size:10px;margin-bottom:6px;}}
.section-hdr::before{{content:'■ ';color:#4a9;}}
.row{{display:flex;justify-content:space-between;align-items:baseline;padding:2px 0;font-size:11px;}}
.row .k{{color:#888;}}
.row .v{{color:#c8d0c0;font-weight:500;}}
.row .v.hi{{color:#8ef;}}
.bar-line{{color:#4a9;font-size:11px;letter-spacing:-1px;}}
.bar-label{{color:#666;font-size:10px;}}
h2{{color:#8ef;font-size:13px;margin:20px 0 10px;letter-spacing:1px;text-transform:uppercase;border-bottom:1px solid #222;padding-bottom:6px;}}
.icon{{display:inline-block;width:18px;}}
</style></head><body>
<h1>🛸 nexus6 autonomous ecosystem</h1>
<div class="meta">{ts} · NEXUS + ANIMA + TECS-L + n6-arch + SEDI · auto-refresh 60s</div>

<h2>🎯 Projects</h2>
<div class="grid3">

  <!-- ═══ NEXUS (MAIN) ═══ -->
  <div class="panel nexus">
    <div class="panel-title">🛸 NEXUS-6 (main)</div>
    <div class="panel-section">
      <div class="section-hdr">Closure Progress</div>
      <div class="row"><span class="k">Total Closed</span><span class="v hi">{closed:,}</span></div>
      <div class="row"><span class="k">EXACT</span><span class="v">{exact:,}</span></div>
      <div class="row"><span class="k">다음 마일스톤</span><span class="v">{next_ms//1000}k ({pct_to_next:.0f}%)</span></div>
      <div class="bar-line">{bar(pct_to_next,24)}</div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">Topology & Data</div>
      <div class="row"><span class="k">Σ points</span><span class="v hi">{topo:,}</span></div>
      <div class="row"><span class="k">Discovery log</span><span class="v">{disc:,}</span></div>
      <div class="row"><span class="k">Calc stubs</span><span class="v">{stubs}</span></div>
      <div class="row"><span class="k">VC file size</span><span class="v">{fsize(f'{NX}/shared/verified_constants.jsonl')}</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">Autonomous Pipeline</div>
      <div class="row"><span class="k">Agents</span><span class="v hi">{healthy_count}/{len(agents)} healthy</span></div>
      <div class="row"><span class="k">Commits 6h</span><span class="v">{commits_6h}</span></div>
      <div class="row"><span class="k">Milestones 돌파</span><span class="v">5k·7.5k·10k·20k·50k·100k</span></div>
    </div>
  </div>

  <!-- ═══ ANIMA ═══ -->
  <div class="panel anima">
    <div class="panel-title">🧠 ANIMA (의식)</div>
    <div class="panel-section">
      <div class="section-hdr">Core Metrics</div>
      <div class="row"><span class="k">Laws</span><span class="v hi">{anima_laws:,}</span></div>
      <div class="row"><span class="k">Modules</span><span class="v">{anima_modules}</span></div>
      <div class="row"><span class="k">Hypothesis files</span><span class="v">{anima_hyp}</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">EVO 상태</div>
      <div class="row"><span class="k">Stage</span><span class="v">{evo_stage}</span></div>
      <div class="row"><span class="k">Generation</span><span class="v">{evo_gen}</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">nexus6 통합</div>
      <div class="row"><span class="k">Topology points</span><span class="v">{domains.get('hypothesis:anima',0):,}</span></div>
      <div class="row"><span class="k">Closures from anima</span><span class="v">{closures_for_proj('anima'):,}</span></div>
    </div>
  </div>

  <!-- ═══ TECS-L ═══ -->
  <div class="panel tecsl">
    <div class="panel-title">📐 TECS-L (수학)</div>
    <div class="panel-section">
      <div class="section-hdr">Atlas</div>
      <div class="row"><span class="k">Hypotheses</span><span class="v hi">{tecsl_atlas_total:,}</span></div>
      <div class="row"><span class="k">Calculators</span><span class="v">{tecsl_calc}</span></div>
      <div class="row"><span class="k">Hyp files (docs)</span><span class="v">{tecsl_hyp}</span></div>
      <div class="row"><span class="k">Math hyp files</span><span class="v">{tecsl_math_hyp}</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">nexus6 통합</div>
      <div class="row"><span class="k">Topology points</span><span class="v hi">{domains.get('hypothesis:TECS-L',0):,}</span></div>
      <div class="row"><span class="k">Closures from TECS</span><span class="v">{closures_for_proj('tecs'):,}</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">발견</div>
      <div class="row"><span class="k">BASEL-003</span><span class="v">Bernoulli 분모 ÷6</span></div>
      <div class="row"><span class="k">MUSICIRCLE</span><span class="v">σ(6)=12 음고원</span></div>
      <div class="row"><span class="k">Bott</span><span class="v">φ=σ-τ=8</span></div>
    </div>
  </div>

</div>

<div class="grid3">

  <!-- ═══ n6-architecture ═══ -->
  <div class="panel n6a">
    <div class="panel-title">🏛 n6-architecture</div>
    <div class="panel-section">
      <div class="section-hdr">Papers</div>
      <div class="row"><span class="k">Total papers</span><span class="v hi">{n6a_papers}</span></div>
      <div class="row"><span class="k">nexus6 auto-papers</span><span class="v">{n6a_nexus_papers}</span></div>
      <div class="row"><span class="k">Hypotheses</span><span class="v">{n6a_hyp}</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">nexus6 통합</div>
      <div class="row"><span class="k">Topology points</span><span class="v">{domains.get('hypothesis:n6-architecture',0):,}</span></div>
      <div class="row"><span class="k">Closures</span><span class="v">{closures_for_proj('n6-arch'):,}</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">Alien Index</div>
      <div class="row"><span class="k">Grade 10 threshold</span><span class="v">closed-form</span></div>
      <div class="row"><span class="k">paper_trigger</span><span class="v">alien_index=10</span></div>
    </div>
  </div>

  <!-- ═══ SEDI ═══ -->
  <div class="panel sedi">
    <div class="panel-title">🌌 SEDI (외계)</div>
    <div class="panel-section">
      <div class="section-hdr">Hypotheses</div>
      <div class="row"><span class="k">Hyp files</span><span class="v hi">{sedi_hyp}</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">nexus6 통합</div>
      <div class="row"><span class="k">Topology points</span><span class="v">{domains.get('hypothesis:SEDI',0):,}</span></div>
      <div class="row"><span class="k">Closures</span><span class="v">{closures_for_proj('sedi'):,}</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">대표 발견</div>
      <div class="row"><span class="k">H-CA-001</span><span class="v">Bott Φ_max=σ-τ</span></div>
      <div class="row"><span class="k">H-CX-918</span><span class="v">Clausius R(6)=0</span></div>
    </div>
  </div>

  <!-- ═══ Meta FP Ladder (sci finding) ═══ -->
  <div class="panel n6a">
    <div class="panel-title">🛸 Meta FP Ladder (과학 발견)</div>
    <div class="panel-section">
      <div class="section-hdr">우주 밀도 유리수 분해</div>
      <div class="row"><span class="k">Ω_DM</span><span class="v">4/15 (n=15)</span></div>
      <div class="row"><span class="k">Ω_Λ</span><span class="v">24/35 (n=35)</span></div>
      <div class="row"><span class="k">Ω_b</span><span class="v">1/21</span></div>
      <div class="row"><span class="k">Σ</span><span class="v hi">= 1 (exact)</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">H-CLOSE (5/6 CONFIRMED)</div>
      <div class="row"><span class="k">sopfr dominance</span><span class="v">30% ✅</span></div>
      <div class="row"><span class="k">J2=24 dominance</span><span class="v">31% ✅</span></div>
      <div class="row"><span class="k">초월수 FAIL</span><span class="v">0 EXACT ✅</span></div>
    </div>
  </div>

</div>

</body></html>"""

with open(f'{NX}/shared/dashboard.html', 'w') as f:
    f.write(html)
print(f"[{ts}] dashboard project-view → {len(html)}B")
PYEOF
