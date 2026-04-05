#!/usr/bin/env bash
# auto-breakthrough.sh — 조건부 자동 돌파
# 5분 루프에서 호출. 새 데이터가 쌓였을 때만 실행.
#
# 발동 조건 (하나라도 충족 시):
#   1. discovery_log가 이전 체크 대비 100건+ 증가
#   2. math_atlas가 변경됨 (md5 비교)
#   3. 마지막 돌파 후 1시간+ 경과 + 새 discovery 10건+
#
# 사용: bash scripts/auto-breakthrough.sh [--force]
set -e

HEXA="$HOME/Dev/hexa-lang/target/release/hexa"
STATE_FILE="/tmp/n6_auto_breakthrough_state.json"
LOG="$HOME/Dev/nexus6/shared/discovery_log.jsonl"
ATLAS="$HOME/Dev/nexus6/shared/math_atlas.json"

# 상태 파일 초기화
if [ ! -f "$STATE_FILE" ]; then
  echo '{"last_log_count":0,"last_atlas_md5":"","last_run":0}' > "$STATE_FILE"
fi

# 현재 상태
CUR_LOG_COUNT=$(wc -l < "$LOG" 2>/dev/null | tr -d ' ' || echo 0)
CUR_ATLAS_MD5=$(md5 -q "$ATLAS" 2>/dev/null || echo "none")
CUR_TIME=$(date +%s)

# 이전 상태 로드
PREV_LOG_COUNT=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('last_log_count',0))" 2>/dev/null || echo 0)
PREV_ATLAS_MD5=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('last_atlas_md5',''))" 2>/dev/null || echo "")
PREV_RUN=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('last_run',0))" 2>/dev/null || echo 0)

LOG_DELTA=$((CUR_LOG_COUNT - PREV_LOG_COUNT))
TIME_DELTA=$((CUR_TIME - PREV_RUN))
FORCE="${1:-}"

# 발동 조건 체크
TRIGGER=""
if [ "$FORCE" = "--force" ]; then
  TRIGGER="forced"
elif [ "$LOG_DELTA" -ge 100 ]; then
  TRIGGER="log_growth(+${LOG_DELTA})"
elif [ "$CUR_ATLAS_MD5" != "$PREV_ATLAS_MD5" ] && [ "$PREV_ATLAS_MD5" != "" ]; then
  TRIGGER="atlas_changed"
elif [ "$TIME_DELTA" -ge 3600 ] && [ "$LOG_DELTA" -ge 10 ]; then
  TRIGGER="hourly(+${LOG_DELTA})"
fi

if [ -z "$TRIGGER" ]; then
  # 조건 미충족 — 스킵
  exit 0
fi

# 돌파 실행!
echo ""
echo "⚡ AUTO-BREAKTHROUGH triggered: $TRIGGER"
echo "  log: $PREV_LOG_COUNT → $CUR_LOG_COUNT (+$LOG_DELTA)"
echo "  time since last: ${TIME_DELTA}s"

# 시스템 메트릭 수집
bash "$HOME/Dev/nexus6/scripts/collect-live.sh" 2>/dev/null

# real_breakthrough surprise 스캔 (경량)
echo ""
RESULT=$("$HEXA" "$HOME/Dev/nexus6/mk2_hexa/native/real_breakthrough.hexa" surprise 2>&1 | tail -20) || true
echo "$RESULT"

# seed_engine으로 동적 seed 확인
SEEDS=$("$HEXA" "$HOME/Dev/nexus6/mk2_hexa/native/seed_engine.hexa" merge 2>/dev/null) || true
SEED_COUNT=$(echo "$SEEDS" | tr '|' '\n' | wc -l | tr -d ' ')
echo "  dynamic seeds: $SEED_COUNT"

# 상태 갱신
python3 -c "
import json
state = {'last_log_count': $CUR_LOG_COUNT, 'last_atlas_md5': '$CUR_ATLAS_MD5', 'last_run': $CUR_TIME}
json.dump(state, open('$STATE_FILE', 'w'))
" 2>/dev/null

echo "  state saved → next check in ~5min"
