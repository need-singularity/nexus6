#!/usr/bin/env bash
# watch-atlas.sh — 가설 .md 파일 변경 감지 → Math Atlas 자동 재빌드
#
# 동작:
#   - 각 리포의 docs/hypotheses/ 디렉토리를 INTERVAL초마다 폴링
#   - 마지막 스캔 이후 수정/생성된 .md 파일 발견 시 scan_math_atlas.py 실행
#   - 커밋 없이 .md만 만들어도 atlas가 갱신됨 (watch-sync.sh는 git push만 감지)
#
# Usage:
#   ./scripts/watch-atlas.sh                # 기본 30초 간격
#   INTERVAL=10 ./scripts/watch-atlas.sh    # 10초 간격

set -euo pipefail

INTERVAL="${INTERVAL:-30}"
NEXUS_ROOT="${NEXUS_ROOT:-$HOME/Dev/nexus}"
PROJECTS_JSON="${PROJECTS_JSON:-$NEXUS_ROOT/shared/projects.json}"
SCAN_SCRIPT="$NEXUS_ROOT/shared/scan_math_atlas.py"
SYNC_SCRIPT="$NEXUS_ROOT/shared/sync-math-atlas.sh"
STAMP_FILE="$HOME/.config/n6-watch-atlas.stamp"
LOG="$HOME/Library/Logs/nexus/watch-atlas.log"
mkdir -p "$(dirname "$LOG")" "$(dirname "$STAMP_FILE")"

if ! command -v jq &>/dev/null; then
    echo "[FATAL] jq not found — install via 'brew install jq'" >&2
    exit 1
fi

if [ ! -f "$PROJECTS_JSON" ]; then
    echo "[FATAL] projects registry not found: $PROJECTS_JSON" >&2
    exit 1
fi

# projects.json의 dev_dir + 각 project.root + hypothesis_dirs를 전개
DEV="$(jq -r '.dev_dir' "$PROJECTS_JSON" | sed "s|^~|$HOME|")"
WATCH_DIRS=()
while IFS= read -r rel; do
    [ -n "$rel" ] && WATCH_DIRS+=("$DEV/$rel")
done < <(jq -r '.projects | to_entries[] as $p
    | $p.value.hypothesis_dirs[]
    | "\($p.value.root)/\(.)"' "$PROJECTS_JSON")

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

# 초기 stamp 파일 없으면 현재 시각으로 생성
if [ ! -f "$STAMP_FILE" ]; then
    touch "$STAMP_FILE"
    log "init stamp: $STAMP_FILE"
fi

# 실제 존재하는 디렉토리만 필터링
EXISTING=()
for d in "${WATCH_DIRS[@]}"; do
    [ -d "$d" ] && EXISTING+=("$d")
done

if [ ${#EXISTING[@]} -eq 0 ]; then
    log "no hypothesis directories found — exiting"
    exit 0
fi

log "watch-atlas started — interval=${INTERVAL}s, dirs=${#EXISTING[@]}"
for d in "${EXISTING[@]}"; do log "  watching: $d"; done

while true; do
    # stamp 이후 수정된 .md 파일 검색
    CHANGED=$(find "${EXISTING[@]}" -name "*.md" -type f -newer "$STAMP_FILE" 2>/dev/null | head -20)

    if [ -n "$CHANGED" ]; then
        CHANGE_COUNT=$(echo "$CHANGED" | wc -l | tr -d ' ')
        log "📡 $CHANGE_COUNT .md file(s) changed → running scan_math_atlas.py"
        echo "$CHANGED" | head -5 | while read -r f; do log "   $f"; done

        # Atlas 재빌드 + README 동기화 (sync-math-atlas.sh가 둘 다 수행)
        RUN_OK=false
        if [ -f "$SYNC_SCRIPT" ] && bash "$SYNC_SCRIPT" >> "$LOG" 2>&1; then
            RUN_OK=true
        elif /usr/bin/python3 "$SCAN_SCRIPT" --save --summary >> "$LOG" 2>&1; then
            # 폴백: sync-math-atlas.sh 없거나 실패 시 scan만
            RUN_OK=true
        fi

        if [ "$RUN_OK" = true ]; then
            ATLAS="$NEXUS_ROOT/shared/math_atlas.json"
            if [ -f "$ATLAS" ]; then
                # stats.*.total 합산으로 총 항목 수 계산
                ENTRIES=$(/usr/bin/python3 -c "import json;d=json.load(open('$ATLAS'));s=d.get('stats',{});print(sum(v.get('total',0) for v in s.values()) if isinstance(s,dict) else '?')" 2>/dev/null || echo '?')
                log "✅ atlas+readme synced — $ENTRIES hypotheses"
            fi
            # macOS 알림
            if command -v osascript &>/dev/null; then
                osascript -e "display notification \"Math Atlas 갱신 (+$CHANGE_COUNT files)\" with title \"NEXUS-6 Atlas\"" 2>/dev/null || true
            fi
        else
            log "⚠️ atlas sync 실패"
        fi

        # stamp 갱신
        touch "$STAMP_FILE"
    fi

    sleep "$INTERVAL"
done
