#!/usr/bin/env bash
# 프로젝트 화이트리스트 체크 — 모든 훅에서 source로 호출
# 등록된 프로젝트가 아니면 exit 0 (조용히 종료)
set +e

PROJ_JSON="$HOME/Dev/nexus6/shared/nexus6-projects.json"
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)

if [ -z "$REPO_ROOT" ]; then
  exit 0
fi

REPO_NAME=$(basename "$REPO_ROOT")

if [ -f "$PROJ_JSON" ]; then
  if ! python3 -c "
import json, sys
d = json.load(open('$PROJ_JSON'))
names = list(d.get('projects', {}).keys())
sys.exit(0 if '$REPO_NAME' in [n.lower() for n in names] or '$REPO_NAME' in names else 1)
" 2>/dev/null; then
    exit 0
  fi
else
  exit 0
fi
