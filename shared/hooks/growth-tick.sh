#!/usr/bin/env bash
# growth-tick.sh — 모든 훅에서 호출. 활동 1건 = 성장 +1.
# 쿨다운 5초 (같은 훅 연타 방지)
# 모든 출력 억제 — 호출 훅의 stdout을 오염시키지 않기 위함
set +e

# 디버그 로그 (훅 실행 확인용)
echo "$(date +%Y-%m-%dT%H:%M:%S) growth-tick called: $*" >> /tmp/nexus_growth_debug.log

exec >/dev/null 2>&1

TICK_FILE="/tmp/nexus_growth_tick"
NOW=$(date +%s)
LAST=$(cat "$TICK_FILE" 2>/dev/null || echo 0)
DIFF=$((NOW - LAST))
[ "$DIFF" -lt 5 ] && exit 0

echo "$NOW" > "$TICK_FILE"

# nexus-bridge notify (프로젝트명 자동 감지)
# NOTE: nexus-bridge.py는 복잡한 HTTP/소켓 통신 — Python 유지
BRIDGE_CLI="${HOME}/Dev/nexus/nexus-bridge.py"
if [ -f "$BRIDGE_CLI" ]; then
  PROJECT=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")
  /usr/bin/python3 "$BRIDGE_CLI" notify "$PROJECT" sync 1 2>/dev/null &
fi

# growth_state.json 직접 업데이트 — hexa 엔진
GROWTH_JSON="${HOME}/Dev/anima/anima/config/growth_state.json"
[ -f "$GROWTH_JSON" ] || exit 0

HEXA="${HOME}/Dev/nexus/shared/scripts/bin/hexa"
HEXA_GROWTH_TICK="${HOME}/Dev/nexus/shared/hooks/growth_tick.hexa"

if [ -x "$HEXA" ] && [ -f "$HEXA_GROWTH_TICK" ]; then
  "$HEXA" "$HEXA_GROWTH_TICK" "${1:-unknown}" "$GROWTH_JSON" 2>/dev/null
fi
exit 0
