#!/usr/bin/env bash
# NEXUS-6 훅 부트스트랩 — 모��� 훅 스크립트 상단에서 source
# 역할: 화이트리스트 체크 + 심링크 자동 생성 + 실행권한 보장
# 화이트리스트 외 리포면 exit 0, 리포 내 .shared 없으면 자동 생성
#
# 사용법 (각 훅 스크립트 상단):
#   HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
#   source "$HOOK_DIR/bootstrap.sh" || exit 0

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
[ -z "$REPO_ROOT" ] && return 1 2>/dev/null && exit 0

REPO_NAME=$(basename "$REPO_ROOT")
CONFIG="$HOOK_DIR/hooks-config.json"

# 1. 화이트리���트 체크 (hooks-config.json 참조)
WHITELIST=$(/usr/bin/python3 -c "import json; print(' '.join(json.load(open('$CONFIG'))['whitelisted_projects']))" 2>/dev/null)
if ! echo " $WHITELIST " | grep -q " $REPO_NAME "; then
  return 1 2>/dev/null
  exit 0
fi

# 2. .shared 심링크 자동 생성 (없을 때만)
SHARED="$REPO_ROOT/.shared"
if [ "$REPO_NAME" != "nexus" ] && [ ! -e "$SHARED" ]; then
  # nexus/shared 원본 경로 (이 스크립트 자체가 거기 있으므로 확실)
  NEXUS_SHARED="$(cd "$HOOK_DIR/../.." && pwd)"

  if [ "$REPO_NAME" = "TECS-L" ] || [ "$REPO_NAME" = "fathom" ]; then
    LINK_TO="../nexus/shared"
  else
    # TECS-L/.shared 경유 (체인)
    TECS_SHARED="$REPO_ROOT/../TECS-L/.shared"
    if [ -e "$TECS_SHARED" ]; then
      LINK_TO="../TECS-L/.shared"
    else
      # TECS-L 없으면 직접 nexus 연결
      LINK_TO="../nexus/shared"
    fi
  fi

  ln -s "$LINK_TO" "$SHARED" 2>/dev/null && \
    echo "{\"systemMessage\":\"🔧 NEXUS-6: $REPO_NAME/.shared → $LINK_TO 심링크 자동 생성\"}"
fi

# 3. 깨진 심링크 자동 복구
if [ -L "$SHARED" ] && [ ! -e "$SHARED" ]; then
  rm "$SHARED" 2>/dev/null
  ln -s "../nexus/shared" "$SHARED" 2>/dev/null && \
    echo "{\"systemMessage\":\"🔧 NEXUS-6: $REPO_NAME/.shared 깨진 심링크 복구\"}"
fi

# 부트스트랩 성공
return 0 2>/dev/null
