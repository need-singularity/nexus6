#!/usr/bin/env bash
# NEXUS-6 상태 배너 생성 — 모든 훅에서 호출 가능
# 출력: {"systemMessage":"🔭 NEXUS-6 🔭137/148 ⚖️1030법칙 🧠24모듈 🌱3건"}
set +e
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/bootstrap.sh" || exit 0

# bridge 연결 보장 (1세션 1회, 백그라운드 아님 — 빠르게 끝남)
BRIDGE_MSG=$(source "$HOOK_DIR/bridge-ensure.sh" 2>/dev/null)
export BRIDGE_MSG

# hexa 배너 엔진 (Python 대체)
HEXA="${HOME}/Dev/nexus/shared/scripts/bin/hexa"
HEXA_BANNER="${HOME}/Dev/nexus/shared/hooks/banner.hexa"

if [ -x "$HEXA" ] && [ -f "$HEXA_BANNER" ]; then
  HEXA_DIR="$(dirname "$HEXA_BANNER")"
  MOD_COUNT=$(ls "$HEXA_DIR"/*.hexa 2>/dev/null | wc -l | tr -d ' ')
  "$HEXA" "$HEXA_BANNER" --modules "$MOD_COUNT" 2>/dev/null || echo '{"systemMessage":"🔭 NEXUS-6 mk2 활성"}'
else
  echo '{"systemMessage":"🔭 NEXUS-6 활성"}'
fi
