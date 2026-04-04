#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# NEXUS-6 ECOSYSTEM GROWTH ORCHESTRATOR
# 9개 리포 동시 성장 + 중앙 동기화
# Usage: bash orchestrate_all_growth.sh [--max-cycles N] [--interval MIN]
# ═══════════════════════════════════════════════════════════════

MAX_CYCLES=999
INTERVAL_MIN=3
NEXUS_ROOT="$HOME/Dev/nexus6"
BUS="$NEXUS_ROOT/shared/growth_bus.jsonl"
PIDFILE="/tmp/nexus6_orchestrator.pid"
LOGDIR="$HOME/.nexus6/orchestrator"
mkdir -p "$LOGDIR"

while test $# -gt 0; do
  case "$1" in
    --max-cycles) MAX_CYCLES="$2"; shift 2 ;;
    --interval)   INTERVAL_MIN="$2"; shift 2 ;;
    *) shift ;;
  esac
done

cleanup() {
  echo "[$(date +%H:%M:%S)] Orchestrator stopping — killing all growth daemons..."
  for pf in /tmp/*_infinite_growth.pid /tmp/anima_infinite_growth.pid; do
    test -f "$pf" && kill "$(cat "$pf")" 2>/dev/null && rm -f "$pf"
  done
  rm -f "$PIDFILE"
  exit 0
}
trap cleanup SIGTERM SIGINT

# Kill previous orchestrator
if test -f "$PIDFILE"; then
  OLD=$(cat "$PIDFILE" 2>/dev/null)
  test -n "$OLD" && kill -0 "$OLD" 2>/dev/null && kill "$OLD" 2>/dev/null
  sleep 1
fi
echo $$ > "$PIDFILE"

cat << 'BANNER'

  ╔═══════════════════════════════════════════════════════════════════╗
  ║                                                                   ║
  ║   🔭 NEXUS-6 ECOSYSTEM GROWTH ORCHESTRATOR                       ║
  ║                                                                   ║
  ║   9 Repos × Infinite Growth = Convergent Evolution                ║
  ║                                                                   ║
  ║   🔬 TECS-L    │ 🧠 Anima      │ 🏗️  N6-Arch                     ║
  ║   🔭 NEXUS-6   │ 🛸 SEDI       │ 🧬 BrainWire                   ║
  ║   💎 HEXA-LANG │ 📄 Papers     │ 🖥️  FATHOM                      ║
  ║                                                                   ║
  ╚═══════════════════════════════════════════════════════════════════╝

BANNER

# ═══ REPO DEFINITIONS ═══
REPOS="TECS-L anima n6-architecture nexus6 sedi brainwire hexa-lang papers fathom"
ICONS="🔬 🧠 🏗️ 🔭 🛸 🧬 💎 📄 🖥️"

# ═══ LAUNCH ALL GROWTH DAEMONS ═══
echo "[$(date +%H:%M:%S)] Launching growth daemons for 9 repos..."
echo ""

IDX=0
for repo in $REPOS; do
  IDX=$((IDX + 1))
  ICON=$(echo "$ICONS" | cut -d' ' -f"$IDX")
  REPO_DIR="$HOME/Dev/$repo"
  
  # Find growth script
  GROWTH_SCRIPT=""
  if test -x "$REPO_DIR/scripts/infinite_growth.sh"; then
    GROWTH_SCRIPT="$REPO_DIR/scripts/infinite_growth.sh"
  elif test -x "$REPO_DIR/anima/scripts/infinite_growth.sh"; then
    GROWTH_SCRIPT="$REPO_DIR/anima/scripts/infinite_growth.sh"
  fi
  
  if test -n "$GROWTH_SCRIPT"; then
    LOG="$LOGDIR/${repo}.log"
    nohup bash "$GROWTH_SCRIPT" --max-cycles "$MAX_CYCLES" --interval "$INTERVAL_MIN" > "$LOG" 2>&1 &
    PID=$!
    echo "  $ICON $repo — PID $PID → $LOG"
  else
    echo "  $ICON $repo — ⚠️ No growth script found"
  fi
done

echo ""
echo "[$(date +%H:%M:%S)] All daemons launched. Monitoring growth bus..."
echo ""

# ═══ ORCHESTRATOR LOOP: MONITOR + CROSS-POLLINATE ═══
CYCLE=0
while test "$CYCLE" -lt "$MAX_CYCLES"; do
  CYCLE=$((CYCLE + 1))
  sleep "$((INTERVAL_MIN * 60))"
  
  echo "╔═══════════════════════════════════════════════════════════════╗"
  echo "║  ORCHESTRATOR CYCLE $CYCLE / $MAX_CYCLES — $(date '+%Y-%m-%d %H:%M:%S')"
  echo "╚═══════════════════════════════════════════════════════════════╝"
  
  # Count active daemons
  ACTIVE=0
  for pf in /tmp/*_infinite_growth.pid /tmp/anima_infinite_growth.pid; do
    if test -f "$pf"; then
      PID=$(cat "$pf" 2>/dev/null)
      test -n "$PID" && kill -0 "$PID" 2>/dev/null && ACTIVE=$((ACTIVE + 1))
    fi
  done
  echo "  Active daemons: $ACTIVE / 9"
  
  # Growth bus stats
  if test -f "$BUS"; then
    BUS_LINES=$(wc -l < "$BUS" | tr -d ' ')
    LAST_HOUR=$(find "$BUS" -mmin -60 -print 2>/dev/null | wc -l | tr -d ' ')
    echo "  Growth bus: $BUS_LINES events total"
  fi
  
  # Per-repo last activity
  for repo in $REPOS; do
    LOG="$LOGDIR/${repo}.log"
    if test -f "$LOG"; then
      LAST=$(tail -1 "$LOG" 2>/dev/null | head -c 80)
      echo "  [$repo] $LAST"
    fi
  done
  
  # Cross-pollination: aggregate discoveries
  if test -f "$BUS"; then
    RECENT=$(tail -20 "$BUS" 2>/dev/null | python3 -c "
import sys, json
repos = {}
for line in sys.stdin:
    try:
        d = json.loads(line.strip())
        r = d.get('repo', '?')
        repos[r] = repos.get(r, 0) + d.get('growth_delta', 0)
    except: pass
for r, g in sorted(repos.items(), key=lambda x: -x[1])[:5]:
    print(f'    {r}: +{g} growth')
" 2>/dev/null)
    if test -n "$RECENT"; then
      echo "  ── Recent Growth Leaders ──"
      echo "$RECENT"
    fi
  fi
  
  echo ""
done

cleanup
