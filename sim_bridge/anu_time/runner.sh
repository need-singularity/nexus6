#!/bin/bash
# runner.sh — ★19 ANU-Time demo runner
#
# Usage: ./runner.sh [max_ticks] [run_label]
#   max_ticks default 300 (aim ~5min with ANU cache 60s TTL)
#   run_label default auto-timestamped
#
# 출력: shared/sim_bridge/anu_time/runs/<label>/{log.jsonl,meta.json,report.txt}

set -u
NEXUS_ROOT="${NEXUS_ROOT:-$HOME/Dev/nexus}"
cd "$NEXUS_ROOT" || exit 1

MAX_TICKS="${1:-300}"
LABEL="${2:-run_$(date +%s)}"
RUN_DIR="$NEXUS_ROOT/shared/sim_bridge/anu_time/runs/$LABEL"

mkdir -p "$RUN_DIR"

echo "[runner] label=$LABEL max_ticks=$MAX_TICKS run_dir=$RUN_DIR"

# universe 실행 (HEXA_LOCAL=1 필수 → Mac 로컬, write_file Mac 경유)
# timeout 안전장치: max_ticks * 3초 또는 최대 10분
BUDGET=$((MAX_TICKS * 3))
if [ "$BUDGET" -gt 600 ]; then BUDGET=600; fi

HEXA_LOCAL=1 NEXUS_NO_BUDGET_OK=1 \
    timeout "${BUDGET}s" hexa shared/sim_bridge/anu_time/universe.hexa "$MAX_TICKS" "$RUN_DIR" \
    2>&1 | tee "$RUN_DIR/universe.stdout"

UEXIT=${PIPESTATUS[0]}
echo "[runner] universe exit=$UEXIT"

# 분석
echo ""
echo "────────────────────────────────────────────────────"
echo "[runner] running analyze…"
echo "────────────────────────────────────────────────────"
HEXA_LOCAL=1 hexa shared/sim_bridge/anu_time/analyze.hexa "$RUN_DIR" \
    2>&1 | tee "$RUN_DIR/report.txt"

echo ""
echo "[runner] artifacts:"
ls -la "$RUN_DIR"
