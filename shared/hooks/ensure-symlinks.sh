#!/usr/bin/env bash
# NEXUS-6 심링크 자동 복구 — 모든 훅에서 source로 호출
# source .shared/hooks/ensure-symlinks.sh

# 현재 리포 루트 찾기
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
[ -z "$REPO_ROOT" ] && return 0 2>/dev/null || exit 0

SHARED="$REPO_ROOT/.shared"
NEXUS_SHARED="$REPO_ROOT/../nexus6/shared"

# .shared 심링크 체크 + 자동 복구
if [ ! -L "$SHARED" ] && [ ! -d "$SHARED" ]; then
  # 심링크 없음 — 자동 생성 시도
  if [ -d "$NEXUS_SHARED" ]; then
    ln -s ../nexus6/shared "$SHARED"
    echo '{"systemMessage":"🔧 NEXUS-6: .shared 심링크 자동 생성 완료 (../nexus6/shared)"}'
  else
    echo '{"systemMessage":"❌ NEXUS-6: .shared 심링크 없음 + nexus6 리포 없음. bash ~/Dev/nexus6/setup-symlinks.sh 실행 필요. 세션 재시작 후 다시 시도하세요."}'
    return 1 2>/dev/null || exit 1
  fi
elif [ -L "$SHARED" ] && [ ! -e "$SHARED" ]; then
  # 심링크는 있는데 깨짐 (대상 없음)
  rm "$SHARED"
  if [ -d "$NEXUS_SHARED" ]; then
    ln -s ../nexus6/shared "$SHARED"
    echo '{"systemMessage":"🔧 NEXUS-6: 깨진 심링크 복구 완료"}'
  else
    echo '{"systemMessage":"❌ NEXUS-6: 심링크 깨짐 + nexus6 없음. 먼저 nexus6 클론 후 bash ~/Dev/nexus6/setup-symlinks.sh 실행. 세션 재시작 필요."}'
    return 1 2>/dev/null || exit 1
  fi
fi
