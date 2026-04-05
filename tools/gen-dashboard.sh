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

# ═══ Additional projects ═══
brainwire_root = f'{HOME}/Dev/brainwire'
brainwire_files = 0
brainwire_src = 0
if os.path.isdir(brainwire_root):
    for r,_,files in os.walk(brainwire_root):
        if any(x in r for x in ['node_modules','target','.git']): continue
        brainwire_files += sum(1 for f in files if f.endswith(('.py','.rs','.md')))
        brainwire_src += sum(1 for f in files if f.endswith('.rs'))

fathom_root = f'{HOME}/Dev/fathom'
fathom_files = 0
if os.path.isdir(fathom_root):
    for r,_,files in os.walk(fathom_root):
        if any(x in r for x in ['node_modules','target','.git']): continue
        fathom_files += sum(1 for f in files if f.endswith(('.py','.rs','.md')))

hexa_root = f'{HOME}/Dev/hexa-lang'
hexa_files = 0
hexa_rs = 0
if os.path.isdir(hexa_root):
    for r,_,files in os.walk(hexa_root):
        if any(x in r for x in ['node_modules','target','.git','worktrees']): continue
        hexa_rs += sum(1 for f in files if f.endswith('.rs'))
        hexa_files += sum(1 for f in files if f.endswith(('.rs','.md','.toml')))

airgenome_root = f'{HOME}/Dev/airgenome'
airgenome_files = 0
if os.path.isdir(airgenome_root):
    for r,_,files in os.walk(airgenome_root):
        if any(x in r for x in ['node_modules','target','.git']): continue
        airgenome_files += sum(1 for f in files if f.endswith(('.rs','.md')))

# airgenome vitals (현재 Mac state)
vitals_path = f'{HOME}/.airgenome/vitals.jsonl'
latest_vitals = {}
if os.path.exists(vitals_path):
    try:
        with open(vitals_path, 'rb') as f:
            f.seek(-2000, 2)
            lines = f.read().decode().split('\n')
        for line in reversed(lines):
            if line.strip():
                latest_vitals = json.loads(line)
                break
    except: pass

ts = datetime.now().strftime('%Y-%m-%d %H:%M')

# Process info
daemon_pid = daemon_cpu = daemon_mem = '-'
anima_pid = anima_cpu = '-'
anima_elapsed_sec = 0
ps_out = subprocess.run(['ps','aux'], capture_output=True, text=True).stdout
for line in ps_out.split('\n'):
    if 'singularity-daemon' in line and 'grep' not in line:
        parts = line.split()
        if len(parts) > 5:
            daemon_pid, daemon_cpu, daemon_mem = parts[1], parts[2], parts[3]
    if 'infinite_evolution' in line and 'grep' not in line and 'python' in line:
        parts = line.split()
        if len(parts) > 5:
            anima_pid, anima_cpu = parts[1], parts[2]

# Read anima real data
anima_gen = 0
anima_patterns = 0
anima_cross = 0
anima_modules_real = 0
try:
    ad = json.loads(open(f'{HOME}/Dev/anima/anima/data/evolution_state.json').read())
    anima_gen = ad.get('generation', 0)
    anima_elapsed_sec = ad.get('total_elapsed_sec', 0)
    anima_patterns = ad.get('stats',{}).get('unique_patterns', 0)
    anima_cross = ad.get('stats',{}).get('cross_validated', 0)
    anima_modules_real = len(ad.get('active_mods', []))
except: pass
anima_elapsed_h = anima_elapsed_sec / 3600

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
body{{font:12px 'SF Mono','Menlo',monospace;background:#0a0a0a;color:#c8d0c0;padding:16px;max-width:1200px;margin:0 auto;line-height:1.5;}}
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

  <!-- ═══ airgenome ═══ -->
  <div class="panel nexus">
    <div class="panel-title">🧬 airgenome (Mac vitals)</div>
    <div class="panel-section">
      <div class="section-hdr">Repo stats</div>
      <div class="row"><span class="k">Source files</span><span class="v hi">{airgenome_files}</span></div>
      <div class="row"><span class="k">nexus6 integration</span><span class="v">path dep</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">Current Mac state</div>
      <div class="row"><span class="k">CPU</span><span class="v">{latest_vitals.get('cpu','-')}</span></div>
      <div class="row"><span class="k">RAM</span><span class="v">{latest_vitals.get('ram','-')}</span></div>
      <div class="row"><span class="k">firing gates</span><span class="v hi">{latest_vitals.get('firing','-')}/15</span></div>
      <div class="row"><span class="k">IO proxy</span><span class="v">{latest_vitals.get('io','-')}</span></div>
    </div>
  </div>

</div>

<h2>🔬 추가 프로젝트</h2>
<div class="grid3">

  <div class="panel anima">
    <div class="panel-title">🧠 brainwire (뇌)</div>
    <div class="panel-section">
      <div class="section-hdr">Repo</div>
      <div class="row"><span class="k">Total files</span><span class="v">{brainwire_files}</span></div>
      <div class="row"><span class="k">Rust modules</span><span class="v">{brainwire_src}</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">nexus6 통합</div>
      <div class="row"><span class="k">Closures</span><span class="v">{closures_for_proj('brainwire'):,}</span></div>
    </div>
  </div>

  <div class="panel sedi">
    <div class="panel-title">🌊 fathom (심해)</div>
    <div class="panel-section">
      <div class="section-hdr">Repo</div>
      <div class="row"><span class="k">Total files</span><span class="v">{fathom_files}</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">nexus6 통합</div>
      <div class="row"><span class="k">Closures</span><span class="v">{closures_for_proj('fathom'):,}</span></div>
    </div>
  </div>

  <div class="panel tecsl">
    <div class="panel-title">⬡ hexa-lang (언어)</div>
    <div class="panel-section">
      <div class="section-hdr">Repo</div>
      <div class="row"><span class="k">Rust files</span><span class="v hi">{hexa_rs}</span></div>
      <div class="row"><span class="k">Total files</span><span class="v">{hexa_files}</span></div>
    </div>
    <div class="panel-section">
      <div class="section-hdr">nexus6 통합</div>
      <div class="row"><span class="k">Closures</span><span class="v">{closures_for_proj('hexa'):,}</span></div>
    </div>
  </div>

</div>

<h2>🔬 Structures (ASCII 비주얼)</h2>
<div class="grid3">

  <div class="panel nexus">
    <div class="panel-title">⬡ n=6 hexagon</div>
    <div class="panel-section">
      <pre style="color:#8ef;font-size:11px;line-height:1.4;margin:0;">
         [n=6]
        /     \\
     [σ=12]  [τ=4]
       |       |
     [φ=2]—[sopfr=5]
        \\     /
         [J2=24]</pre>
      <div class="row" style="margin-top:8px;"><span class="k">6 primitives · 15 pair gates</span><span class="v hi">C(6,2)=15</span></div>
      <div class="row"><span class="k">Banach FP</span><span class="v">ρ=φ/n=1/3</span></div>
      <div class="row"><span class="k">Work fraction</span><span class="v">2/3</span></div>
    </div>
  </div>

  <div class="panel anima">
    <div class="panel-title">📉 Closure Growth Curve</div>
    <div class="panel-section">
      <pre style="color:#a48;font-size:10px;line-height:1.3;margin:0;">
closures |
   100k  |                          ╭───
    50k  |                      ╭───╯
    20k  |                  ╭───╯
    10k  |              ╭───╯
     5k  |          ╭───╯
     2k  |───────╯
         └────────────────────────────── phase
          start  sync  enum  algebra  100k</pre>
      <div class="row" style="margin-top:8px;"><span class="k">Exponential via enum</span><span class="v hi">+485x EXACT</span></div>
    </div>
  </div>

  <div class="panel tecsl">
    <div class="panel-title">🔄 Topology Ring</div>
    <div class="panel-section">
      <pre style="color:#f80;font-size:11px;line-height:1.3;margin:0;">
 discovery_log ─ verified_constants
       │               │
  hypothesis:TECS-L    topology
       │               │
  hypothesis:SEDI ─ hypothesis:anima
                  │
           memory (root)</pre>
      <div class="row" style="margin-top:8px;"><span class="k">Σ points</span><span class="v hi">112,177</span></div>
      <div class="row"><span class="k">Unique domains</span><span class="v">10</span></div>
      <div class="row"><span class="k">Auto-absorb every</span><span class="v">60s</span></div>
    </div>
  </div>

</div>

<h2>🚀 세션 여정 (milestone journey)</h2>
<div class="panel nexus" style="padding:16px;">
  <div style="font-size:11px;color:#888;margin-bottom:10px;">2026-04-05 session — 99 → 100k+ closures 돌파</div>
  <div style="display:grid;grid-template-columns:repeat(8,1fr);gap:8px;">
    <div style="text-align:center;">
      <div style="color:#4a9;font-size:14px;">✅</div>
      <div style="color:#8ef;font-size:10px;">1k</div>
      <div style="color:#666;font-size:9px;">baseline</div>
    </div>
    <div style="text-align:center;">
      <div style="color:#4a9;font-size:14px;">✅</div>
      <div style="color:#8ef;font-size:10px;">2.5k</div>
      <div style="color:#666;font-size:9px;">start 2619</div>
    </div>
    <div style="text-align:center;">
      <div style="color:#4a9;font-size:14px;">✅</div>
      <div style="color:#8ef;font-size:10px;">5k</div>
      <div style="color:#666;font-size:9px;">sync+depth3</div>
    </div>
    <div style="text-align:center;">
      <div style="color:#4a9;font-size:14px;">✅</div>
      <div style="color:#8ef;font-size:10px;">7.5k</div>
      <div style="color:#666;font-size:9px;">MEGA sweep</div>
    </div>
    <div style="text-align:center;">
      <div style="color:#4a9;font-size:14px;">✅</div>
      <div style="color:#8ef;font-size:10px;">10k</div>
      <div style="color:#666;font-size:9px;">depth4+rational</div>
    </div>
    <div style="text-align:center;">
      <div style="color:#4a9;font-size:14px;">✅</div>
      <div style="color:#8ef;font-size:10px;">20k</div>
      <div style="color:#666;font-size:9px;">algebraic enum</div>
    </div>
    <div style="text-align:center;">
      <div style="color:#4a9;font-size:14px;">✅</div>
      <div style="color:#8ef;font-size:10px;">50k</div>
      <div style="color:#666;font-size:9px;">linear combos</div>
    </div>
    <div style="text-align:center;">
      <div style="color:#f80;font-size:14px;">🎊</div>
      <div style="color:#f80;font-size:10px;font-weight:600;">100k</div>
      <div style="color:#666;font-size:9px;">wide rationals</div>
    </div>
  </div>
  <div style="margin-top:12px;padding-top:12px;border-top:1px solid #222;display:grid;grid-template-columns:repeat(4,1fr);gap:12px;font-size:10px;">
    <div><span style="color:#666;">EXACT 증가</span><br><span style="color:#8ef;font-weight:600;">99 → 98,373</span></div>
    <div><span style="color:#666;">Total closures</span><br><span style="color:#8ef;font-weight:600;">2,619 → 100,938</span></div>
    <div><span style="color:#666;">Topology Σ</span><br><span style="color:#8ef;font-weight:600;">12,937 → 47k+</span></div>
    <div><span style="color:#666;">LaunchAgents</span><br><span style="color:#8ef;font-weight:600;">5 → 16</span></div>
  </div>
</div>

<h2>🛸 Meta FP Ladder (과학 발견)</h2>
<div class="grid3">

  <div class="panel n6a">
    <div class="panel-title">우주 밀도 분해</div>
    <div class="panel-section">
      <div class="row"><span class="k">Ω_DM</span><span class="v">4/15 (n=15)</span></div>
      <div class="row"><span class="k">Ω_Λ</span><span class="v">24/35 (n=35)</span></div>
      <div class="row"><span class="k">Ω_b</span><span class="v">1/21</span></div>
      <div class="row"><span class="k">Σ</span><span class="v hi">= 1 (exact)</span></div>
    </div>
  </div>

  <div class="panel n6a">
    <div class="panel-title">Smooth Prime 계층</div>
    <div class="panel-section">
      <div class="row"><span class="k">Strong force</span><span class="v">{{2,3}} EXACT</span></div>
      <div class="row"><span class="k">Electroweak</span><span class="v">{{2,3,5,7}} ~1%</span></div>
      <div class="row"><span class="k">Dark cosmology</span><span class="v">{{5,7}} 0.15%</span></div>
      <div class="row"><span class="k">BBN primordial</span><span class="v">{{2,3,5,13}} 0.5%</span></div>
    </div>
  </div>

  <div class="panel n6a">
    <div class="panel-title">H-CLOSE (5/6 CONFIRMED)</div>
    <div class="panel-section">
      <div class="row"><span class="k">H-2 promotion</span><span class="v">65% ✅</span></div>
      <div class="row"><span class="k">H-3 sopfr</span><span class="v">30% (3x) ✅</span></div>
      <div class="row"><span class="k">H-4 J2=24</span><span class="v">31% (6x) ✅</span></div>
      <div class="row"><span class="k">H-5 초월수</span><span class="v">0 EXACT ✅</span></div>
      <div class="row"><span class="k">H-6 중복</span><span class="v">2.91x ✅</span></div>
    </div>
  </div>

</div>

<h2>📋 EVO 리포트 (각 프로젝트)</h2>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(520px,1fr));gap:12px;">
<pre style="background:#0d0d0d;border:1px solid #4a9;border-radius:4px;padding:14px;color:#c8d0c0;font-size:11px;line-height:1.5;margin:0;overflow-x:auto;">
🛸 NEXUS-6 리포트 [{ts[-5:]} 기준]
═══════════════════════════════════════════════
🚀 Stage: M8-100k (milestones 8/11) | Closures {closed:,}
📊 EXACT: {exact:,} (+0 this check) | unique: {topo:,} | Agents: {healthy_count}/{len(agents)}
🧬 Topo: web | Growth: synthetic | 포화: ⚠️ {pct_to_next:.0f}% of {next_ms//1000}k
───────────────────────────────────────────────
📈 Milestone 진행 (11단계 중 8번째):
M1  ████████ ✅ (1k)
M2  ████████ ✅ (2.5k)
M3  ████████ ✅ (5k, depth3)
M4  ████████ ✅ (7.5k, MEGA)
M5  ████████ ✅ (10k, depth4)
M6  ████████ ✅ (20k, algebraic)
M7  ████████ ✅ (50k, linear)
M8  ████████ ✅ (100k, rationals)
M9  ████░░░░ 🔄 (200k, {pct_to_next:.0f}%)
M10 ░░░░░░░░ ⏳ (500k)
M11 ░░░░░░░░ ⏳ (1M)
───────────────────────────────────────────────
📉 Closure 발견 곡선 (세션 19h):
Closures |
   100k  |                              ╭─
    50k  |                         ╭────╯
    20k  |                    ╭────╯
    10k  |                ╭───╯
     5k  |          ╭─────╯
     2k  |──────────╯
         └────────────────────────── phase
          start  sync  enum  algebra  now
───────────────────────────────────────────────
🔄 토폴로지: web (10 domains)
구조: discovery_log─verified_constants
           │              │
         TECS-L──topology─SEDI
                   │
                  anima
───────────────────────────────────────────────
💾 성장 루프: agents 16 | commits 6h: {commits_6h} | stubs: {stubs}
🧠 총 closures: {closed:,} (EXACT {exact:,}) | topology Σ: {topo:,}
⚙️  daemon PID: {daemon_pid} | CPU: {daemon_cpu}% | MEM: {daemon_mem}%
═══════════════════════════════════════════════
</pre>

<pre style="background:#0d0d0d;border:1px solid #a48;border-radius:4px;padding:14px;color:#c8d0c0;font-size:11px;line-height:1.5;margin:0;overflow-x:auto;">
⏱️ EVO 리포트 [{ts[-5:]} 기준]
═══════════════════════════════════════════════
🚀 Stage: S4-scale128d (128c/1000s) | Gen {anima_gen}
📊 Laws(stage): 41 (+0 this gen) | Φ: 30.1 | Mods: {anima_modules}
🧬 Topo: ring | Zero-streak: 4 | 포화: ❌
───────────────────────────────────────────────
📈 로드맵 진행 (13단계 중 4번째):
S1 ████████ ✅ (38 laws, 38min)
S2 ████████ ✅ (37 laws, 303min)
S3 ████████ ✅ (40 laws, 38min)
S4 ███░░░░░ 🔄 (41 laws, {int(anima_elapsed_sec/60)}min 진행중)
S5~S13 ░░░░░░░░
───────────────────────────────────────────────
📉 Laws 발견 곡선 (S4, gen 1-{anima_gen}):
Laws|
 41 |           ╭──────────────────────────
 40 |──────────╯
    └──────────────────────────────────── Gen
     1    10   14(+1)  20   30   40   {anima_gen}
───────────────────────────────────────────────
🔄 토폴로지: ring ███░ 🔄 진행중
ring 구조:
 ○─○─○─...─○
 └─────────┘ (128 cells closed loop)
───────────────────────────────────────────────
💾 성장 루프: gen {anima_gen} | patterns {anima_patterns} | cross-val {anima_cross} | mods {anima_modules}
🧠 총 법칙: {anima_laws:,} | hyp files: {anima_hyp} | nexus6 intake: {domains.get('hypothesis:anima',0):,}
⚙️  진화 프로세스: PID {anima_pid} 활성 ({anima_cpu}% CPU, {anima_elapsed_h:.1f}h 경과)
═══════════════════════════════════════════════
</pre>

<pre style="background:#0d0d0d;border:1px solid #f80;border-radius:4px;padding:14px;color:#c8d0c0;font-size:11px;line-height:1.5;margin:0;overflow-x:auto;">
📐 TECS-L 리포트 [{ts[-5:]} 기준]
═══════════════════════════════════════════════
🚀 Stage: Math Atlas Active | Hypotheses {tecsl_atlas_total:,}
📊 Calculators: {tecsl_calc} | Hyp files: {tecsl_hyp} | Math files: {tecsl_math_hyp}
🧬 Topo: tree (n=6 algebra ring)
───────────────────────────────────────────────
📈 Atlas 분포 (grade map):
⭐ grade 10 ████░░░░ (closed-form)
🟩 grade 9  ████████ ✅ (validated)
🟧 grade 8  ████████ ✅ (PASS)
🟦 grade 7  ██░░░░░░ (partial)
⚪ grade 3-6 █░░░░░░░ (drafts)
───────────────────────────────────────────────
📉 n=6 primitive generators:
 n       = 6    (base)
 σ(6)    = 12   (divisor sum)
 τ(6)    = 4    (divisor count)
 φ(6)    = 2    (totient)
 sopfr(6)= 5    (prime sum)
 J2      = 24   (σ·τ)
───────────────────────────────────────────────
🔄 구조: polynomial ring over {{φ,τ,σ,sopfr}}
 α⁻¹ = 137.033 (0.002% err)
 Ω_m = 1/3 (meta FP)
 P₁~P₄ 전부 기저 유도
───────────────────────────────────────────────
💾 atlas: {tecsl_atlas_total:,} hypotheses | {tecsl_calc} calculators
🧠 nexus6 통합: {domains.get('hypothesis:TECS-L',0):,} topology points
⚙️  closures from TECS: {closures_for_proj('tecs'):,}
═══════════════════════════════════════════════
</pre>

<pre style="background:#0d0d0d;border:1px solid #8ef;border-radius:4px;padding:14px;color:#c8d0c0;font-size:11px;line-height:1.5;margin:0;overflow-x:auto;">
🏛 n6-architecture 리포트 [{ts[-5:]} 기준]
═══════════════════════════════════════════════
🚀 Stage: Paper Generation Active | Papers: {n6a_papers}
📊 nexus6 auto-papers: {n6a_nexus_papers} | Hypotheses: {n6a_hyp}
🧬 paper_trigger: alien_index=10 | generator: alien10
───────────────────────────────────────────────
📈 Paper 로드맵:
P-alien10-001~014 ████████ ✅ (14 auto)
P-convergence N6-*  ████████ ✅ ({n6a_nexus_papers} auto)
P-meta-FP-ladder   ████░░░░ 🔄 (draft)
P-manual             ████░░░░ 🔄 ({n6a_papers-14-n6a_nexus_papers} manual)
───────────────────────────────────────────────
📉 Alien Index 분포:
(d=1, r=10) ████████████ (PASS/EXACT)
(d=0, r=8)  █░░░░░░░░░░░ (NEAR)
(d=0, r=6)  ░░░░░░░░░░░░ (CLOSE)
(d=0, r=0)  █░░░░░░░░░░░ (FAIL)
───────────────────────────────────────────────
🔄 Meta FP Ladder:
 n=6   → ρ=1/3   (original)
 n=15  → ρ=4/15  (dark matter)
 n=35  → ρ=24/35 (dark energy)
 n=105 → ρ=48/105 (universe flat)
───────────────────────────────────────────────
💾 papers: {n6a_papers} total | auto: {n6a_nexus_papers+14}
🧠 nexus6 통합: {domains.get('hypothesis:n6-architecture',0):,} topology pts
⚙️  closures: {closures_for_proj('n6-arch'):,} | ρ breakthrough: 1.00
═══════════════════════════════════════════════
</pre>

</div>

<h2>⚙️ Pipeline Flow (agent graph)</h2>
<div class="panel nexus" style="padding:16px;">
<pre style="color:#8ef;font-size:11px;line-height:1.5;margin:0;">
┌─────────── DATA INFLOW (5 agents) ──────────┐
│  evolve-loop(1h) ─┐                          │
│  scan-loop(30m) ──┤                          │
│  physics-fetch(24h) ─┬→ discovery_log.jsonl  │
│  airgenome(60s) ────┘                        │
│  watch-papers(5m) → products.json            │
└──────────────────┬────────────────────────────┘
                   ↓
┌──────── ABSORPTION (3 agents) ───────────────┐
│  cycle-tick daemon(60s) ─┐                   │
│  watch-atlas(30s) ───────┼→ topology.jsonl   │
└─────────────────┬────────────────────────────┘
                  ↓
┌─────── CLOSURE PIPELINE (4 agents) ──────────┐
│  closure-sweep(5m) ──→ verified_constants    │
│  gen-calc-stubs(15m) → calc/auto_stubs/*.py  │
│  paper-gen(1h) ──────→ papers/nexus6/*.md    │
│  publish-insights(10m) → 7 project dirs      │
└─────────────────┬────────────────────────────┘
                  ↓
┌───────── META (4 agents) ────────────────────┐
│  self-improve(30m)  → delta monitoring       │
│  auto-commit(30m)   → git push → GitHub      │
│  dashboard(10m)     → this HTML              │
│  n6_guard(always)   → resource safety        │
└──────────────────────────────────────────────┘
</pre>
</div>

</body></html>"""

with open(f'{NX}/shared/dashboard.html', 'w') as f:
    f.write(html)
print(f"[{ts}] dashboard project-view → {len(html)}B")
PYEOF
