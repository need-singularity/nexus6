#!/usr/bin/env bash
# NEXUS-6 심링크 자동 복구 — 모든 훅에서 source로 호출
# source .shared/hooks/ensure-symlinks.sh

# 현재 리포 루트 찾기
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO_ROOT" ]; then
  return 0 2>/dev/null
  exit 0
fi

SHARED="$REPO_ROOT/.shared"
NEXUS_SHARED="$REPO_ROOT/../nexus6/shared"

# .shared 심링크 체크 + 자동 복구
if [ ! -L "$SHARED" ] && [ ! -d "$SHARED" ]; then
  # 심링크 없음 — 자동 생성 시도
  if [ -d "$NEXUS_SHARED" ]; then
    ln -s ../nexus6/shared "$SHARED" 2>/dev/null
  else
    return 1 2>/dev/null
    exit 1
  fi
elif [ -L "$SHARED" ] && [ ! -e "$SHARED" ]; then
  # 심링크는 있는데 깨짐 (대상 없음)
  rm "$SHARED" 2>/dev/null
  if [ -d "$NEXUS_SHARED" ]; then
    ln -s ../nexus6/shared "$SHARED" 2>/dev/null
  else
    return 1 2>/dev/null
    exit 1
  fi
fi
