#!/usr/bin/env bash
# NEXUS-6 자동 기록 — EXACT 발견 시 Claude 안 거치고 직접 기록
# 다른 훅에서 호출: source "$HOOK_DIR/nexus6-auto-record.sh" "$VALUE" "$CONSTANT" "$SOURCE"

VALUE="$1"
CONSTANT="$2"
SOURCE="$3"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
DISCOVERY_LOG="$HOME/Dev/nexus6/shared/discovery_log.jsonl"

# JSONL로 직접 기록 (Claude 의존 없음)
python3 -c "
import json, os
entry = {
    'timestamp': '$TIMESTAMP',
    'value': '$VALUE',
    'constant': '$CONSTANT',
    'source': '$SOURCE',
    'auto': True
}
with open('$DISCOVERY_LOG', 'a') as f:
    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
" 2>/dev/null
