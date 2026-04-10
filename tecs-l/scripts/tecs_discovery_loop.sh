#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# TECS-L Infinite Discovery Loop Daemon
# Pattern: nexus growth_daemon.sh (measure→pick→act→validate→record→publish)
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

TECS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS="$TECS_ROOT/scripts"
CONFIG="$TECS_ROOT/config"
LOG_DIR="$CONFIG"
LOG_FILE="$LOG_DIR/loop_daemon.log"
PID_FILE="$LOG_DIR/loop_daemon.pid"

# Defaults (overridable via args)
MAX_CYCLES=${MAX_CYCLES:-6}        # n=6
INTERVAL=${INTERVAL:-300}          # 5 minutes between cycles
DRY_RUN=false

# ── Parse args ──────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --max-cycles) MAX_CYCLES="$2"; shift 2 ;;
        --interval)   INTERVAL="$2"; shift 2 ;;
        --dry-run)    DRY_RUN=true; shift ;;
        --help)
            echo "Usage: tecs_discovery_loop.sh [--max-cycles N] [--interval SECS] [--dry-run]"
            exit 0 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

# ── Safety: PID file ────────────────────────────────────────
if [[ -f "$PID_FILE" ]]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Daemon already running (PID $OLD_PID). Exiting."
        exit 1
    fi
    rm -f "$PID_FILE"
fi
echo $$ > "$PID_FILE"

# ── Graceful shutdown ───────────────────────────────────────
RUNNING=true
cleanup() {
    RUNNING=false
    echo "[$(date -Iseconds)] SIGTERM received, shutting down gracefully..." >> "$LOG_FILE"
    rm -f "$PID_FILE"
}
trap cleanup SIGTERM SIGINT

# ── Logging ─────────────────────────────────────────────────
log() {
    echo "[$(date -Iseconds)] $*" | tee -a "$LOG_FILE"
}

# ── Main loop ───────────────────────────────────────────────
log "═══ TECS-L Discovery Loop starting (max=$MAX_CYCLES, interval=${INTERVAL}s) ═══"

CYCLE=0
CONSECUTIVE_FAIL=0
MAX_FAIL=3

while [[ "$RUNNING" == true ]] && [[ $CYCLE -lt $MAX_CYCLES ]]; do
    CYCLE=$((CYCLE + 1))
    log "── Cycle $CYCLE/$MAX_CYCLES ──"

    # Step 0: WALL-BREAK (auto-evolve on plateau)
    log "Step 0: Wall detection + domain evolution..."

    # 0a: Wall detect + depth adjustment
    WALL_OUT=$(/usr/bin/python3 "$SCRIPTS/tecs_wall.py" 2>&1) || true
    log "Wall: $WALL_OUT"

    # 0b: Domain forge (create new domains from clusters)
    FORGE_OUT=$(/usr/bin/python3 "$SCRIPTS/tecs_forge.py" 2>&1) || true
    log "Forge: $FORGE_OUT"

    # 0c: Domain split (split oversized domains)
    SPLIT_OUT=$(/usr/bin/python3 "$SCRIPTS/tecs_split.py" 2>&1) || true
    log "Split: $SPLIT_OUT"

    # 0d: Keyword absorb (expand classifiers from discoveries)
    ABSORB_OUT=$(/usr/bin/python3 "$SCRIPTS/tecs_absorb.py" 2>&1) || true
    log "Absorb: $ABSORB_OUT"

    # Step 1: MEASURE
    log "Step 1: Measuring domain health..."
    MEASURE_OUT=$(/usr/bin/python3 "$SCRIPTS/tecs_measure.py" 2>&1) || {
        log "MEASURE failed: $MEASURE_OUT"
        CONSECUTIVE_FAIL=$((CONSECUTIVE_FAIL + 1))
        if [[ $CONSECUTIVE_FAIL -ge $MAX_FAIL ]]; then
            log "BRAKE: $MAX_FAIL consecutive failures. Stopping."
            break
        fi
        sleep "$INTERVAL"
        continue
    }
    log "Measure result: $MEASURE_OUT"

    # Extract target domain and mode
    TARGET=$(echo "$MEASURE_OUT" | /usr/bin/python3 -c "import sys,json; print(json.load(sys.stdin)['target_domain'])" 2>/dev/null || echo "N")
    MODE=$(/usr/bin/python3 -c "
import json
with open('$CONFIG/loop_state.json') as f:
    print(json.load(f)['loop']['mode'])
" 2>/dev/null || echo "dfs")
    log "Target: domain=$TARGET, mode=$MODE"

    if [[ "$DRY_RUN" == true ]]; then
        log "[DRY RUN] Would act on domain=$TARGET mode=$MODE"
        sleep "$INTERVAL"
        continue
    fi

    # Step 2: ACT
    log "Step 2: Running discovery action..."
    ACT_OUT=$(/usr/bin/python3 "$SCRIPTS/tecs_act.py" "$TARGET" "$MODE" 2>&1) || {
        log "ACT failed: $ACT_OUT"
        CONSECUTIVE_FAIL=$((CONSECUTIVE_FAIL + 1))
        if [[ $CONSECUTIVE_FAIL -ge $MAX_FAIL ]]; then
            log "BRAKE: $MAX_FAIL consecutive failures. Stopping."
            break
        fi
        sleep "$INTERVAL"
        continue
    }
    log "Act result: $ACT_OUT"

    # Step 3: VALIDATE
    log "Step 3: Cross-validating discoveries..."
    VALIDATE_OUT=$(/usr/bin/python3 "$SCRIPTS/tecs_validate.py" 2>&1) || {
        log "VALIDATE failed: $VALIDATE_OUT"
    }
    log "Validate result: $VALIDATE_OUT"

    # Step 4: RECORD
    log "Step 4: Recording confirmed discoveries..."
    RECORD_OUT=$(/usr/bin/python3 "$SCRIPTS/tecs_record.py" 2>&1) || {
        log "RECORD failed: $RECORD_OUT"
    }
    log "Record result: $RECORD_OUT"

    # Step 4b: Cross-pollinate (inject discoveries across domains)
    log "Step 4b: Cross-pollinating discoveries..."
    POLLINATE_OUT=$(/usr/bin/python3 "$SCRIPTS/tecs_pollinate.py" 2>&1) || true
    log "Pollinate: $POLLINATE_OUT"

    # Step 5: BRIDGE (nexus-bridge sync)
    log "Step 5: Syncing via nexus-bridge..."
    BRIDGE_SCRIPT="$HOME/Dev/nexus/nexus-bridge.py"
    if [[ -f "$BRIDGE_SCRIPT" ]]; then
        BRIDGE_OUT=$(/usr/bin/python3 "$BRIDGE_SCRIPT" sync math-atlas,lenses 2>&1) || {
            log "BRIDGE sync skipped: $BRIDGE_OUT"
        }
        log "Bridge result: $BRIDGE_OUT"
    else
        log "Bridge not found, skipping"
    fi

    # Step 6: PUBLISH (check threshold)
    log "Step 6: Checking publish threshold..."
    PUBLISH_OUT=$(/usr/bin/python3 "$SCRIPTS/tecs_publish.py" 2>&1) || {
        log "PUBLISH failed: $PUBLISH_OUT"
    }
    log "Publish result: $PUBLISH_OUT"

    # Reset failure counter on successful cycle
    CONSECUTIVE_FAIL=0

    # Check if we should stop
    FAILURES=$(/usr/bin/python3 -c "
import json
with open('$CONFIG/loop_state.json') as f:
    print(json.load(f)['loop']['consecutive_failures'])
" 2>/dev/null || echo "0")

    if [[ "$FAILURES" -ge "$MAX_FAIL" ]]; then
        log "BRAKE: $MAX_FAIL consecutive discovery failures. Mode may rotate next cycle."
    fi

    # Report (every cycle)
    /usr/bin/python3 "$SCRIPTS/tecs_report.py" 2>/dev/null | tee -a "$LOG_FILE"

    log "── Cycle $CYCLE complete. Sleeping ${INTERVAL}s ──"
    # Interruptible sleep
    sleep "$INTERVAL" &
    wait $! 2>/dev/null || true
done

log "═══ TECS-L Discovery Loop finished ($CYCLE cycles) ═══"

# Final report
/usr/bin/python3 "$SCRIPTS/tecs_report.py" 2>/dev/null | tee -a "$LOG_FILE"

rm -f "$PID_FILE"
