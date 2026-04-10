#!/usr/bin/env bash
# 프로젝트 화이트리스트 체크 — 모든 훅에서 source로 호출
# 미등록 프로젝트면 NEXUS_SKIP=1 설정 (exit 대신 플래그)
set +e

NEXUS_SKIP=0
PROJ_JSON="$HOME/Dev/nexus/shared/config/nexus-projects.json"
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)

if [ -z "$REPO_ROOT" ]; then
  NEXUS_SKIP=1
  return 0 2>/dev/null || exit 0
fi

REPO_NAME=$(basename "$REPO_ROOT")

if [ -f "$PROJ_JSON" ]; then
  if ! /usr/bin/python3 -c "
import json, sys
d = json.load(open('$PROJ_JSON'))
names = list(d.get('projects', {}).keys())
sys.exit(0 if '$REPO_NAME' in [n.lower() for n in names] or '$REPO_NAME' in names else 1)
" 2>/dev/null; then
    NEXUS_SKIP=1
    return 0 2>/dev/null || exit 0
  fi
else
  NEXUS_SKIP=1
  return 0 2>/dev/null || exit 0
fi

export NEXUS_SKIP
