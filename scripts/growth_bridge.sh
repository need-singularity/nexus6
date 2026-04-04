#!/usr/bin/env bash
set -euo pipefail
# ═══════════════════════════════════════════════════════════════
# Growth Bridge — 자기 성장하는 프로젝트 간 동기화 브릿지
# ═══════════════════════════════════════════════════════════════
#
# 기능:
#   1. absorbed/ 데이터를 스캔하고 소화(digest)
#   2. 프로젝트 간 가치 있는 발견물을 라우팅
#   3. 브릿지 자체가 성장 (처리량 → 라우팅 정확도 향상)
#
# Usage:
#   ./growth_bridge.sh                  # 전체 사이클 1회
#   ./growth_bridge.sh --scan           # 스캔만 (absorbed 현황)
#   ./growth_bridge.sh --digest         # 소화만 (absorbed → digested)
#   ./growth_bridge.sh --status         # 브릿지 상태 출력
#   ./growth_bridge.sh --grow           # 브릿지 자체 성장 tick

NEXUS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BRIDGE_STATE="$NEXUS_ROOT/shared/bridge_state.json"
GROWTH_BUS="$NEXUS_ROOT/shared/growth_bus.jsonl"

log() { echo "[$(date +%H:%M:%S)] BRIDGE: $*"; }
now_iso() { date -u +"%Y-%m-%dT%H:%M:%S"; }

# ── 전체 로직: Python으로 통합 (bash associative array 호환 문제 회피) ──

do_scan() {
  log "Scanning all project .growth/absorbed/ directories..."
  python3 -c "
import json, os, glob

BRIDGE = '$BRIDGE_STATE'
HOME = os.path.expanduser('~')
state = json.load(open(BRIDGE))
total = 0

for name, conn in state['connections'].items():
    absorbed_dir = os.path.join(conn['path'], '.growth', 'absorbed')
    if os.path.isdir(absorbed_dir):
        count = len(os.listdir(absorbed_dir))
        conn['absorbed_count'] = count
        total += count
        print(f'  {name}: {count} absorbed files')
    else:
        print(f'  {name}: no .growth/absorbed/')

json.dump(state, open(BRIDGE, 'w'), indent=2, ensure_ascii=False)
print(f'Total absorbed across all projects: {total}')
"
}

do_digest() {
  log "Digesting absorbed data..."
  python3 << 'PYEOF'
import json, os, glob
from collections import Counter
from datetime import datetime

BRIDGE = os.environ["BRIDGE_STATE"]
state = json.load(open(BRIDGE))
routing = state.get("routing_table", {})
total_digested = 0
growth_earned = 0

for proj_name, conn in state["connections"].items():
    absorbed_dir = os.path.join(conn["path"], ".growth", "absorbed")
    if not os.path.isdir(absorbed_dir):
        continue

    files = glob.glob(os.path.join(absorbed_dir, "*.json"))
    type_counter = Counter()
    high_value = []

    for f in files:
        try:
            data = json.load(open(f))
            grade = data.get("value_grade", "low")
            score = data.get("n6_score", 0)
            source = data.get("absorbed_from", "")

            # Classify by content type
            sl = source.lower()
            if "skill" in sl:
                type_counter["skill"] += 1
            elif "test" in sl or "spec" in sl:
                type_counter["test"] += 1
            elif "config" in sl or "toml" in sl:
                type_counter["config"] += 1
            elif any(sl.endswith(ext) for ext in [".rs", ".py", ".ts", ".js"]):
                type_counter["code"] += 1
            elif "log" in sl:
                type_counter["log"] += 1
            else:
                type_counter["other"] += 1

            if grade in ("critical", "high") and score > 20:
                high_value.append(os.path.basename(f))
                growth_earned += 2
            else:
                growth_earned += 1

            total_digested += 1
        except Exception:
            continue

    conn["digested_count"] = len(files)
    conn["valuable_types"] = [t for t, _ in type_counter.most_common(5)]
    conn["last_sync"] = datetime.utcnow().isoformat()

    if files:
        conn["affinity_score"] = round(len(high_value) / len(files) * 100, 1)

    for content_type, count in type_counter.items():
        if content_type not in routing:
            routing[content_type] = {}
        routing[content_type][proj_name] = count

# Bridge self-growth
bridge = state["bridge"]
bridge["total_processed"] += total_digested
bridge["total_routed"] += len([v for v in routing.values() if v])
bridge["growth_points"] += growth_earned
bridge["cycle"] += 1
bridge["health"] = min(200.0, bridge["health"] + growth_earned * 0.1)

# Stage evolution
gp = bridge["growth_points"]
thresholds = state["stage_thresholds"]
for stage_name in ["forest", "tree", "sapling", "sprout", "seedling"]:
    if gp >= thresholds[stage_name]:
        if bridge["stage"] != stage_name:
            state.setdefault("growth_log", []).append({
                "event": f"stage_up: {bridge['stage']} → {stage_name}",
                "at_points": gp,
                "timestamp": datetime.utcnow().isoformat()
            })
            bridge["stage"] = stage_name
        break

state["routing_table"] = routing
json.dump(state, open(BRIDGE, "w"), indent=2, ensure_ascii=False)

print(f"  Digested: {total_digested} files")
print(f"  Growth earned: +{growth_earned} points (total: {bridge['growth_points']})")
print(f"  Bridge stage: {bridge['stage']}")
print(f"  Routing types: {list(routing.keys())}")
PYEOF
  log "Digest complete."
}

do_grow() {
  log "Bridge self-growth tick..."
  python3 -c "
import json
s = json.load(open('$BRIDGE_STATE'))
b = s['bridge']
event = json.dumps({
  'source': 'growth_bridge',
  'timestamp': '$(now_iso)',
  'bridge_stage': b['stage'],
  'growth_points': b['growth_points'],
  'connections': len(s['connections']),
  'total_processed': b['total_processed'],
  'health': b['health']
})
print(event)
" >> "$GROWTH_BUS"
  log "Emitted bridge status to growth_bus"

  # Trigger anima growth tick if connected
  local tick_script="$NEXUS_ROOT/shared/hooks/growth-tick.sh"
  if [ -f "$tick_script" ]; then
    bash "$tick_script" "bridge-sync" >/dev/null 2>&1 &
    log "Triggered anima growth tick"
  fi
}

do_status() {
  python3 << 'PYEOF'
import json, os
BRIDGE = os.environ["BRIDGE_STATE"]
s = json.load(open(BRIDGE))
b = s["bridge"]

print("═══════════════════════════════════════════")
print(f"  Growth Bridge — {b['stage']} (cycle {b['cycle']})")
print("═══════════════════════════════════════════")
print(f"  Health:     {b['health']:.1f}")
print(f"  Points:     {b['growth_points']}")
print(f"  Processed:  {b['total_processed']}")
print(f"  Routed:     {b['total_routed']}")
print()
print("  Connections:")
for name, c in s["connections"].items():
    alive = "●" if os.path.isdir(c["path"]) else "○"
    print(f"    {alive} {name:20s} absorbed={c['absorbed_count']:4d}  digested={c['digested_count']:4d}  affinity={c['affinity_score']:.1f}%")
    if c["valuable_types"]:
        print(f"      → types: {', '.join(c['valuable_types'])}")
print()
if s.get("routing_table"):
    print("  Routing Table:")
    for ctype, routes in s["routing_table"].items():
        targets = ", ".join(f"{k}({v})" for k, v in sorted(routes.items(), key=lambda x: -x[1]))
        print(f"    {ctype:10s} → {targets}")
print()
if s.get("growth_log"):
    print("  Growth Log:")
    for entry in s["growth_log"][-5:]:
        print(f"    [{entry.get('timestamp','')}] {entry.get('event','')}")
print("═══════════════════════════════════════════")
PYEOF
}

# ── Main ─────────────────────────────────────────────────────
export NEXUS_ROOT BRIDGE_STATE GROWTH_BUS

case "${1:-full}" in
  --scan)   do_scan ;;
  --digest) do_digest ;;
  --grow)   do_grow ;;
  --status) do_status ;;
  full|*)
    do_scan
    do_digest
    do_grow
    do_status
    ;;
esac
