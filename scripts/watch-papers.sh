#!/usr/bin/env bash
# watch-papers.sh — 프로젝트별 paper_trigger.generator 주기 실행
#
# 동작:
#   - projects.json에서 paper_trigger.enabled=true 인 모든 프로젝트의 generator 호출
#   - generator는 JSON 리포트 출력 (created, skipped 등)
#   - 새 파일 생성 시 로그 + 알림
#
# 각 프로젝트는 자기만의 완성 기준을 generator 스크립트로 정의.
# generator 경로는 projects.json의 `paper_trigger.generator` (NEXUS_ROOT 상대경로).
#
# Usage:
#   ./scripts/watch-papers.sh                # 기본 300초 (5분) 간격
#   INTERVAL=60 ./scripts/watch-papers.sh    # 1분 간격

set -euo pipefail

INTERVAL="${INTERVAL:-300}"
NEXUS_ROOT="${NEXUS_ROOT:-$HOME/Dev/nexus}"
PROJECTS_JSON="${PROJECTS_JSON:-$NEXUS_ROOT/shared/projects.json}"
PAPERS_REPO="${PAPERS_REPO:-$HOME/Dev/papers}"
REGISTER_SCRIPT="$NEXUS_ROOT/scripts/paper-gen/register_paper.py"
AUTO_COMMIT="${AUTO_COMMIT:-1}"           # 1=자동 commit+push, 0=생성만
AUTO_REGISTER="${AUTO_REGISTER:-1}"       # 1=manifest.json 자동 등록
LOG="$HOME/Library/Logs/nexus/watch-papers.log"
mkdir -p "$(dirname "$LOG")"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

if ! command -v jq &>/dev/null; then
    log "[FATAL] jq not found"
    exit 1
fi

if [ ! -f "$PROJECTS_JSON" ]; then
    log "[FATAL] projects registry not found: $PROJECTS_JSON"
    exit 1
fi

log "watch-papers started — interval=${INTERVAL}s"

# 활성화된 generator 목록 표시
log "활성 generator:"
jq -r '.projects | to_entries[]
    | select(.value.paper_trigger.enabled == true)
    | "  [\(.key)] \(.value.paper_trigger.generator) — \(.value.paper_trigger.description // "")"' \
    "$PROJECTS_JSON" | while read -r line; do log "$line"; done

while true; do
    # generator 목록 추출 (프로젝트명 + 스크립트 상대경로)
    while IFS=$'\t' read -r proj_name gen_rel; do
        [ -z "$proj_name" ] && continue
        gen_path="$NEXUS_ROOT/$gen_rel"

        if [ ! -f "$gen_path" ]; then
            log "⚠️ [$proj_name] generator not found: $gen_path"
            continue
        fi

        # 실행 (python 또는 bash 자동 판별)
        REPORT=""
        if [[ "$gen_path" == *.py ]]; then
            REPORT=$(/usr/bin/python3 "$gen_path" 2>>"$LOG") || {
                log "⚠️ [$proj_name] generator failed (python)"
                continue
            }
        elif [[ "$gen_path" == *.sh ]]; then
            REPORT=$(bash "$gen_path" 2>>"$LOG") || {
                log "⚠️ [$proj_name] generator failed (bash)"
                continue
            }
        else
            REPORT=$("$gen_path" 2>>"$LOG") || {
                log "⚠️ [$proj_name] generator failed"
                continue
            }
        fi

        # 리포트 파싱 (JSON 기대)
        CREATED_COUNT=$(echo "$REPORT" | jq -r '.created | length' 2>/dev/null || echo "0")
        if [ "$CREATED_COUNT" -gt 0 ]; then
            CREATED_LIST=$(echo "$REPORT" | jq -r '.created | join(", ")' 2>/dev/null || echo "?")
            OUTPUT_DIR=$(echo "$REPORT" | jq -r '.output_dir' 2>/dev/null || echo "?")
            log "📄 [$proj_name] +$CREATED_COUNT paper(s): $CREATED_LIST"
            log "   → $OUTPUT_DIR"
            if command -v osascript &>/dev/null; then
                osascript -e "display notification \"$proj_name: +$CREATED_COUNT papers ($CREATED_LIST)\" with title \"NEXUS-6 Papers\"" 2>/dev/null || true
            fi

            # ── manifest.json 자동 등록 ──
            if [ "$AUTO_REGISTER" = "1" ] && [ -f "$REGISTER_SCRIPT" ]; then
                echo "$REPORT" | jq -r --arg dir "$OUTPUT_DIR" '.created[] | "\($dir)/\(.).md"' 2>/dev/null | while read -r md; do
                    [ -f "$md" ] || continue
                    RESULT=$(/usr/bin/python3 "$REGISTER_SCRIPT" --file "$md" --repo "$proj_name" --tier 2 2>&1)
                    STATUS=$(echo "$RESULT" | jq -r '.status' 2>/dev/null || echo "error")
                    if [ "$STATUS" = "registered" ]; then
                        ID=$(echo "$RESULT" | jq -r '.entry.id')
                        log "   ✓ manifest 등록: $ID ($(basename "$md"))"
                    elif [ "$STATUS" = "skipped" ]; then
                        log "   - manifest skip: $(basename "$md") (중복)"
                    else
                        log "   ⚠️ manifest 등록 실패: $(basename "$md")"
                    fi
                done
            fi

            # ── papers 리포 자동 commit + push ──
            if [ "$AUTO_COMMIT" = "1" ] && [ -d "$PAPERS_REPO/.git" ]; then
                cd "$PAPERS_REPO" || continue

                # 안전장치: 현재 브랜치 main/master 확인
                BRANCH=$(git branch --show-current 2>/dev/null)
                if [ "$BRANCH" != "main" ] && [ "$BRANCH" != "master" ]; then
                    log "   ⚠️ commit skip: branch=$BRANCH (main/master 아님)"
                    continue
                fi

                # staged 변경 있으면 skip (사용자 작업 중 보호)
                if ! git diff --cached --quiet 2>/dev/null; then
                    log "   ⚠️ commit skip: staged 변경 존재 (사용자 작업 중)"
                    continue
                fi

                # 생성 파일 + manifest.json만 add (다른 수정사항 건드리지 않음)
                REL_DIR="${OUTPUT_DIR#$PAPERS_REPO/}"
                git add "$REL_DIR" manifest.json 2>/dev/null

                if git diff --cached --quiet 2>/dev/null; then
                    log "   - commit skip: staged 변경 없음"
                    continue
                fi

                COMMIT_MSG="auto: [$proj_name] +$CREATED_COUNT papers — $CREATED_LIST

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
                if git commit -m "$COMMIT_MSG" >> "$LOG" 2>&1; then
                    SHA=$(git rev-parse --short HEAD)
                    log "   ✓ committed $SHA"
                    if git push >> "$LOG" 2>&1; then
                        log "   ✓ pushed to origin/$BRANCH"
                    else
                        log "   ⚠️ push 실패 (commit만 됨)"
                    fi
                else
                    log "   ⚠️ commit 실패"
                fi
                cd - > /dev/null || true
            fi
        fi
    done < <(jq -r '.projects | to_entries[]
        | select(.value.paper_trigger.enabled == true)
        | "\(.key)\t\(.value.paper_trigger.generator)"' "$PROJECTS_JSON")

    sleep "$INTERVAL"
done
