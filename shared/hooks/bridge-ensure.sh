#!/usr/bin/env bash
# bridge-ensure.sh — 세션 시작 시 nexus-bridge 연결 보장
# nexus-banner.sh에서 호출됨 (SessionStart 시점)
# 조건: 프로젝트가 bridge_state.json에 없으면 자동 connect
# 1세션 1회만 실행 (lockfile 사용)
set +e

BRIDGE_PY="$HOME/Dev/nexus/nexus-bridge.py"
BRIDGE_STATE="$HOME/Dev/nexus/shared/bridge_state.json"

# 프로젝트명 결정 (bootstrap.sh가 이미 REPO_NAME 설정)
PROJECT="${REPO_NAME:-$(basename "$(git rev-parse --show-toplevel 2>/dev/null)")}"
[ -z "$PROJECT" ] && return 0 2>/dev/null && exit 0

# 세션 1회 lockfile — 같은 프로젝트에서 반복 실행 방지
LOCKFILE="/tmp/nexus-bridge-ensured-${PROJECT}"
if [ -f "$LOCKFILE" ]; then
  # lockfile이 6시간 이내면 스킵
  if [ "$(uname)" = "Darwin" ]; then
    LOCK_AGE=$(( $(date +%s) - $(stat -f%m "$LOCKFILE" 2>/dev/null || echo 0) ))
  else
    LOCK_AGE=$(( $(date +%s) - $(stat -c%Y "$LOCKFILE" 2>/dev/null || echo 0) ))
  fi
  [ "$LOCK_AGE" -lt 21600 ] && return 0 2>/dev/null && exit 0
fi

# bridge_state.json이 없으면 스킵 (bridge 미설치)
[ ! -f "$BRIDGE_STATE" ] && return 0 2>/dev/null && exit 0
[ ! -f "$BRIDGE_PY" ] && return 0 2>/dev/null && exit 0

# 현재 프로젝트가 이미 연결되어 있는지 확인 (python3으로 빠르게)
CONNECTED=$(/usr/bin/python3 -c "
import json, sys
try:
    state = json.load(open('$BRIDGE_STATE'))
    conns = state.get('connections', {})
    print('yes' if '$PROJECT' in conns else 'no')
except:
    print('error')
" 2>/dev/null)

# lockfile 생성 (체크 완료 표시)
touch "$LOCKFILE" 2>/dev/null

if [ "$CONNECTED" = "no" ]; then
  # 자동 연결 시도
  RESULT=$(/usr/bin/python3 "$BRIDGE_PY" connect "$PROJECT" 2>/dev/null)
  if [ $? -eq 0 ]; then
    echo "bridge-connect: $PROJECT"
  fi
elif [ "$CONNECTED" = "error" ]; then
  return 0 2>/dev/null && exit 0
fi
# "yes"이면 조용히 종료 — 정상 상태
