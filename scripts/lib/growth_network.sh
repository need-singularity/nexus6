#!/usr/bin/env bash
# growth_network.sh — 네트워크/분산 관련 growth 함수들
# growth_common.sh가 먼저 로드되어 있다고 가정
# (log_info, log_warn, write_growth_bus, GROWTH_NAME, PROJECT_ROOT, GROWTH_DIR 등)

# ── #8: 벡터 클럭 ──

common_vector_clock() {
    log_info "🕐 Vector clock update"
    python3 -c "
import json, os, datetime

vc_file = os.path.expanduser('~/.nexus6/vector_clock.json')
try:
    with open(vc_file) as f: vc = json.load(f)
except: vc = {}

# 자기 카운터 증가
vc['$GROWTH_NAME'] = vc.get('$GROWTH_NAME', 0) + 1

# 형제 프로젝트의 벡터 클럭 병합 (max 전략)
for d in os.listdir(os.path.expanduser('~/Dev')):
    if d == '$GROWTH_NAME': continue
    peer_vc = os.path.expanduser(f'~/Dev/{d}/.growth/vector_clock.json')
    if os.path.exists(peer_vc):
        try:
            with open(peer_vc) as f: peer = json.load(f)
            for k, v in peer.items():
                vc[k] = max(vc.get(k, 0), v)
        except: pass

# 저장 (중앙 + 로컬)
with open(vc_file, 'w') as f:
    json.dump(vc, f, indent=2)

local_vc = os.path.expanduser(f'$GROWTH_DIR/vector_clock.json')
with open(local_vc, 'w') as f:
    json.dump(vc, f, indent=2)

total = sum(vc.values())
print(f'VC: {len(vc)} projects, total={total}, self={vc.get(\"$GROWTH_NAME\",0)}')
" 2>/dev/null | while IFS= read -r line; do
        log_info "  $line"
    done
    write_growth_bus "vector_clock" "ok" ""
}

# ── #12: 메트릭 버스 (파일 기반 pub/sub) ──

common_metric_bus_publish() {
    log_info "📡 Metric bus publish"
    local bus_dir="$HOME/.nexus6/metric_bus"
    mkdir -p "$bus_dir"

    # 현재 프로젝트 메트릭을 버스에 발행
    python3 -c "
import json, os, datetime

bus_dir = '$bus_dir'
ts = datetime.datetime.utcnow().isoformat() + 'Z'

metrics = {
    'source': '$GROWTH_NAME',
    'ts': ts,
    'type': 'metrics',
}

# growth_state에서 메트릭 수집
state_file = '$GROWTH_DIR/growth_state.json'
if os.path.exists(state_file):
    with open(state_file) as f:
        state = json.load(f)
    metrics['cycle'] = state.get('cycle', 0)
    metrics['federated_bonus'] = state.get('federated_bonus', 0)

# scan 결과
scan_file = os.path.expanduser('~/.nexus6/last_scan.txt')
if os.path.exists(scan_file):
    with open(scan_file) as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                try: metrics[k] = float(v)
                except: metrics[k] = v

# 버스 파일에 발행
bus_file = os.path.join(bus_dir, f'{\"$GROWTH_NAME\"}.json')
with open(bus_file, 'w') as f:
    json.dump(metrics, f, indent=2)

# 타임라인 (모든 프로젝트 최신 메트릭)
timeline = []
for f in os.listdir(bus_dir):
    if f.endswith('.json'):
        try:
            with open(os.path.join(bus_dir, f)) as fh:
                timeline.append(json.load(fh))
        except: pass
timeline.sort(key=lambda x: x.get('ts',''), reverse=True)

timeline_file = os.path.join(bus_dir, '_timeline.json')
with open(timeline_file, 'w') as f:
    json.dump(timeline, f, indent=2)

print(f'Published to bus ({len(timeline)} sources)')
" 2>/dev/null | while IFS= read -r line; do
        log_info "  $line"
    done
    write_growth_bus "metric_bus" "ok" ""
}

# ── #15: 브릿지 라이브 그래프 (HTML) ──

common_live_graph() {
    log_info "📊 Live graph update"
    local graph_file="$HOME/.nexus6/shared_graph/graph.json"
    local html_file="$HOME/.nexus6/live_graph.html"

    [ ! -f "$graph_file" ] && return

    python3 -c "
import json, os

with open('$graph_file') as f:
    graph = json.load(f)

nodes = graph.get('nodes', [])
edges = graph.get('edges', [])

# 버스 타임라인도 로드
bus_timeline = []
bus_file = os.path.expanduser('~/.nexus6/metric_bus/_timeline.json')
if os.path.exists(bus_file):
    with open(bus_file) as f:
        bus_timeline = json.load(f)

html = '''<!DOCTYPE html>
<html><head><meta charset=\"utf-8\"><meta http-equiv=\"refresh\" content=\"30\">
<title>NEXUS-6 Live Graph</title>
<style>
body { background: #0a0a0a; color: #0f0; font-family: monospace; padding: 20px; }
h1 { color: #0ff; }
.graph { display: flex; flex-wrap: wrap; gap: 10px; }
.node { background: #111; border: 2px solid #333; padding: 10px; border-radius: 8px; min-width: 150px; }
.node.project { border-color: #0f0; }
.node.scan { border-color: #ff0; }
.node.singularity { border-color: #f00; animation: pulse 1s infinite; }
@keyframes pulse { 50% { border-color: #ff0; } }
.edge-list { margin-top: 15px; }
.edge { color: #888; font-size: 12px; }
.metric { color: #0ff; margin: 2px 0; font-size: 12px; }
.ts { color: #555; font-size: 10px; }
table { border-collapse: collapse; margin-top: 15px; }
td, th { border: 1px solid #333; padding: 5px 10px; text-align: left; }
th { color: #ff0; }
</style></head>
<body>
<h1>NEXUS-6 Live Graph</h1>
<p class=\"ts\">Nodes: ''' + str(len(nodes)) + ''' | Edges: ''' + str(len(edges)) + '''</p>

<div class=\"graph\">'''

for node in nodes:
    ntype = node.get('type', 'project')
    cls = ntype
    if node.get('singularity') == 'REACHED':
        cls = 'singularity'
    html += f'''
<div class=\"node {cls}\">
  <strong>{node.get('id','?')}</strong><br>
  <span class=\"ts\">type: {ntype}</span>'''
    if 'exact_ratio' in node:
        html += f'<br><span class=\"metric\">exact: {node[\"exact_ratio\"]}</span>'
    if 'last_update' in node:
        html += f'<br><span class=\"ts\">{node[\"last_update\"][:16]}</span>'
    html += '</div>'

html += '</div><div class=\"edge-list\"><h2>Edges</h2>'
for edge in edges[-20:]:
    html += f'<div class=\"edge\">{edge.get(\"from\",\"?\")} → {edge.get(\"to\",\"?\")} [{edge.get(\"type\",\"\")}]</div>'

html += '</div>'

# 메트릭 버스 테이블
if bus_timeline:
    html += '<h2>Metric Bus</h2><table><tr><th>Source</th><th>Cycle</th><th>Domain</th><th>Singularity</th><th>Time</th></tr>'
    for m in bus_timeline[:10]:
        html += f'<tr><td>{m.get(\"source\",\"?\")}</td><td>{m.get(\"cycle\",\"?\")}</td><td>{m.get(\"domain\",\"?\")}</td><td>{m.get(\"singularity\",\"?\")}</td><td class=\"ts\">{m.get(\"ts\",\"?\")[:16]}</td></tr>'
    html += '</table>'

html += '</body></html>'

with open('$html_file', 'w') as f:
    f.write(html)
print(f'Live graph: {len(nodes)} nodes, {len(edges)} edges')
" 2>/dev/null | while IFS= read -r line; do
        log_info "  $line"
    done
    write_growth_bus "live_graph" "ok" ""
}

# ── #9: 성장 추이 타임라인 (HTML) ──

common_growth_timeline() {
    log_info "📈 Growth timeline"
    local bus_file="$HOME/Dev/nexus6/shared/growth_bus.jsonl"
    local html_file="$HOME/.nexus6/timeline.html"
    [ ! -f "$bus_file" ] && return

    python3 -c "
import json, os
from collections import defaultdict

bus_file = '$bus_file'
events = []
with open(bus_file) as f:
    for line in f:
        try:
            ev = json.loads(line)
            events.append(ev)
        except: pass

# 프로젝트별 이벤트 수 시계열 (시간별)
by_hour = defaultdict(lambda: defaultdict(int))
for ev in events[-5000:]:  # 최근 5000개만
    ts = ev.get('ts', '')[:13]  # YYYY-MM-DDTHH
    repo = ev.get('repo', 'unknown')
    by_hour[ts][repo] += 1

hours = sorted(by_hour.keys())[-48:]  # 최근 48시간
repos = sorted(set(r for h in hours for r in by_hour[h]))

# HTML
html = '''<!DOCTYPE html>
<html><head><meta charset=\"utf-8\"><meta http-equiv=\"refresh\" content=\"60\">
<title>NEXUS-6 Growth Timeline</title>
<style>
body{background:#0a0a0a;color:#0f0;font-family:monospace;padding:20px}
h1{color:#0ff}
table{border-collapse:collapse;margin-top:10px}
td,th{border:1px solid #333;padding:3px 8px;text-align:center;font-size:11px}
th{color:#ff0}
.hot{background:#030}
.cold{background:#111}
</style></head>
<body><h1>Growth Timeline (last 48h)</h1>
<table><tr><th>Hour</th>'''

for r in repos:
    html += f'<th>{r[:8]}</th>'
html += '</tr>'

for h in hours:
    html += f'<tr><td>{h[5:]}</td>'
    for r in repos:
        v = by_hour[h].get(r, 0)
        cls = 'hot' if v > 0 else 'cold'
        html += f'<td class=\"{cls}\">{v if v > 0 else \"\"}</td>'
    html += '</tr>'

html += '</table></body></html>'

with open('$html_file', 'w') as f:
    f.write(html)
print(f'Timeline: {len(hours)} hours, {len(repos)} repos')
" 2>/dev/null | while IFS= read -r line; do
        log_info "  $line"
    done
    write_growth_bus "timeline" "ok" ""
}

# ── growth_network.sh loaded ──
