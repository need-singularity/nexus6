#!/usr/bin/env bash
# growth_common.sh — 전 프로젝트 공통 성장 루프 인프라
# 사용: source "$(dirname "$0")/lib/growth_common.sh" 또는 심링크
# 요구: GROWTH_NAME (프로젝트 이름), PROJECT_ROOT (프로젝트 경로)

# ── 프로젝트 자동 감지 ──
if [ -z "${PROJECT_ROOT:-}" ]; then
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
fi
if [ -z "${GROWTH_NAME:-}" ]; then
    GROWTH_NAME="$(basename "$PROJECT_ROOT")"
fi

GROWTH_DIR="${PROJECT_ROOT}/.growth"
GROWTH_STATE="${GROWTH_DIR}/growth_state.json"
GROWTH_LOG="${GROWTH_DIR}/growth.log"
GROWTH_BUS="$HOME/Dev/nexus6/shared/growth_bus.jsonl"
LOCKFILE="/tmp/n6-growth-${GROWTH_NAME}.lock"
NEXUS6_BIN="${HOME}/.cargo/bin/nexus6"
if [ ! -f "$NEXUS6_BIN" ]; then
    NEXUS6_BIN="${HOME}/Dev/nexus6/target/release/nexus6"
fi
if [ ! -f "$NEXUS6_BIN" ]; then
    NEXUS6_BIN="${HOME}/Dev/nexus6/target/debug/nexus6"
fi

mkdir -p "$GROWTH_DIR"
mkdir -p "$(dirname "$GROWTH_BUS")" 2>/dev/null || true

# ── 로깅 ──
log_info()  { local m="[$(date '+%H:%M:%S')] [${GROWTH_NAME}] $1"; echo "$m"; echo "$m" >> "$GROWTH_LOG"; }
log_warn()  { local m="[$(date '+%H:%M:%S')] [${GROWTH_NAME}] WARN: $1"; echo "$m"; echo "$m" >> "$GROWTH_LOG"; }
log_error() { local m="[$(date '+%H:%M:%S')] [${GROWTH_NAME}] ERROR: $1"; echo "$m" >&2; echo "$m" >> "$GROWTH_LOG"; }

# ── 성장 버스 기록 ──
write_growth_bus() {
    local phase="$1" status="$2" detail="${3:-}"
    local ts
    ts="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf '{"ts":"%s","repo":"%s","phase":"%s","status":"%s","detail":"%s"}\n' \
        "$ts" "$GROWTH_NAME" "$phase" "$status" "$detail" >> "$GROWTH_BUS" 2>/dev/null || true
}

# ── 중복실행 방지 (mkdir 기반, macOS/Linux 호환) ──
acquire_lock() {
    # stale lock 정리 (파일이든 디렉토리든)
    if [ -e "$LOCKFILE" ]; then
        local old_pid
        old_pid=$(cat "$LOCKFILE/pid" 2>/dev/null || cat "$LOCKFILE" 2>/dev/null || echo "")
        old_pid=$(echo "$old_pid" | tr -d '[:space:]')
        if [ -n "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
            log_error "이미 실행 중 (PID $old_pid, lock: $LOCKFILE) — 종료"
            exit 0
        else
            rm -rf "$LOCKFILE" 2>/dev/null || true
        fi
    fi
    if ! mkdir "$LOCKFILE" 2>/dev/null; then
        log_error "Lock 획득 실패 ($LOCKFILE) — 종료"
        exit 0
    fi
    echo $$ > "$LOCKFILE/pid"
    log_info "Lock 획득: $GROWTH_NAME (PID $$)"
}

release_lock() {
    rm -rf "$LOCKFILE" 2>/dev/null || true
}

# ── 시스템 부하 체크 ──
check_load() {
    local load
    load=$(sysctl -n vm.loadavg 2>/dev/null | tr -d '{}' | awk '{print $1}')
    load="${load:-0}"
    if [ "$(echo "$load > 20" | bc 2>/dev/null)" = "1" ]; then
        echo "STOP"
    elif [ "$(echo "$load > 10" | bc 2>/dev/null)" = "1" ]; then
        echo "LIGHT"
    else
        echo "OK"
    fi
}

# ── 공통 Phase: NEXUS-6 스캔 ──
common_nexus6_scan() {
    log_info "📡 NEXUS-6 scan"
    if [ -f "$NEXUS6_BIN" ]; then
        local domain="${1:-number_theory}"
        NEXUS6_ROOT="$HOME/Dev/nexus6" "$NEXUS6_BIN" scan "$domain" 2>/dev/null | tail -3 | while IFS= read -r line; do
            log_info "  $line"
        done
        write_growth_bus "nexus6_scan" "ok" "domain=$domain"
    else
        log_warn "nexus6 바이너리 없음"
        write_growth_bus "nexus6_scan" "skip" "no_binary"
    fi
}

# ── 공통 Phase: Blowup (창발) ──
common_blowup() {
    log_info "💥 Blowup (창발)"
    if [ -f "$NEXUS6_BIN" ]; then
        local domain="${1:-number_theory}"
        NEXUS6_ROOT="$HOME/Dev/nexus6" "$NEXUS6_BIN" blowup "$domain" --depth 6 2>/dev/null | grep -E "따름정리|공리 후보|총 창발|깊이" | while IFS= read -r line; do
            log_info "  $line"
        done
        write_growth_bus "blowup" "ok" "domain=$domain"
    else
        write_growth_bus "blowup" "skip" "no_binary"
    fi
}

# ── 공통 Phase: 크로스폴리네이션 ──
common_cross_pollinate() {
    log_info "🌸 Cross-Pollination (프로젝트간 창발)"
    local blowup_file="$HOME/.nexus6/last_blowup.txt"
    if [ -f "$blowup_file" ]; then
        local emergences
        emergences=$(grep "total_emergences=" "$blowup_file" | cut -d= -f2)
        if [ "${emergences:-0}" -gt 0 ]; then
            # 다른 프로젝트에 blowup 결과 전파
            for proj_dir in "$HOME"/Dev/*/; do
                local proj_name
                proj_name=$(basename "$proj_dir")
                [ "$proj_name" = "$GROWTH_NAME" ] && continue
                [ ! -d "$proj_dir/.growth" ] && continue
                # 발견 이벤트 기록
                local ts
                ts=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
                printf '{"ts":"%s","from":"%s","to":"%s","emergences":%s,"type":"cross_pollinate"}\n' \
                    "$ts" "$GROWTH_NAME" "$proj_name" "${emergences}" >> "$proj_dir/.growth/cross_pollinate.jsonl" 2>/dev/null || true
            done
            log_info "  ${emergences}개 창발 → 프로젝트들에 전파"
            write_growth_bus "cross_pollinate" "ok" "emergences=$emergences"
        else
            log_info "  창발 없음 — skip"
        fi
    else
        log_info "  blowup 결과 없음 — skip"
    fi
}

# ── 공통 Phase: 동기화 ──
common_sync() {
    log_info "🔄 Sync"
    local sync_script="$HOME/Dev/nexus6/sync/sync-all.sh"
    if [ -f "$sync_script" ]; then
        bash "$sync_script" 2>/dev/null | tail -3 | while IFS= read -r line; do
            log_info "  $line"
        done
        write_growth_bus "sync" "ok" ""
    else
        write_growth_bus "sync" "skip" "no_script"
    fi
}

# ── 공통 Phase: 성장 상태 업데이트 ──
common_update_state() {
    local cycle="$1"
    python3 -c "
import json, os
from datetime import datetime, timezone
f = '$GROWTH_STATE'
try:
    with open(f) as fh: s = json.load(fh)
except: s = {}
s['name'] = '$GROWTH_NAME'
s['cycle'] = $cycle
s['last_run'] = datetime.now(timezone.utc).isoformat()
with open(f, 'w') as fh: json.dump(s, fh, indent=2); fh.write('\n')
" 2>/dev/null || true
    write_growth_bus "state_update" "ok" "cycle=$cycle"
}

# ── 공통 Phase: 자동 커밋 ──
common_auto_commit() {
    local cycle="$1" dry_run="${2:-false}"
    cd "$PROJECT_ROOT"
    local changed
    changed=$(git diff --stat HEAD 2>/dev/null | wc -l | tr -d ' ')
    if [ "${changed:-0}" -gt 0 ]; then
        if [ "$dry_run" = "true" ]; then
            log_info "📦 Dry-run: ${changed} files changed, skip commit"
            return
        fi
        git add .growth/ 2>/dev/null || true
        git add -A 2>/dev/null || true
        git commit -m "growth(${GROWTH_NAME}): cycle ${cycle} auto" 2>/dev/null || true
        git push origin main 2>/dev/null || true
        log_info "📦 Committed cycle $cycle"
        write_growth_bus "commit" "ok" "cycle=$cycle"
    else
        log_info "📦 No changes"
        write_growth_bus "commit" "skip" "clean"
    fi
}

# ── 공통 Phase: growth_bridge 호출 ──
common_growth_bridge() {
    local bridge_script="$HOME/Dev/nexus6/scripts/growth_bridge.sh"
    if [ -f "$bridge_script" ]; then
        bash "$bridge_script" full 2>/dev/null | tail -3 | while IFS= read -r line; do
            log_info "  $line"
        done
        write_growth_bus "growth_bridge" "ok" ""
    fi
}

# ── 공통 Phase: 휴면 프로젝트 활성화 ──
common_seed_dormant() {
    log_info "🌱 Dormant project seeding"
    for proj_dir in "$HOME"/Dev/*/; do
        local proj_name
        proj_name=$(basename "$proj_dir")
        [ ! -d "$proj_dir" ] && continue
        [ ! -d "$proj_dir/.git" ] && continue
        # .growth 디렉토리가 없으면 초기화
        if [ ! -d "$proj_dir/.growth" ]; then
            mkdir -p "$proj_dir/.growth/absorbed"
            echo '{"name":"'"$proj_name"'","cycle":0,"seeded_by":"'"$GROWTH_NAME"'","seeded_at":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'"}' > "$proj_dir/.growth/growth_state.json"
            log_info "  $proj_name: .growth 초기화"
            write_growth_bus "seed_dormant" "ok" "project=$proj_name"
        fi
        # absorbed/ 가 비어있으면 시드 데이터 생성
        local absorbed_count
        absorbed_count=$(ls "$proj_dir/.growth/absorbed/" 2>/dev/null | wc -l | tr -d ' ')
        if [ "${absorbed_count:-0}" -eq 0 ] && [ -d "$proj_dir/src" ] || [ -d "$proj_dir/scripts" ]; then
            # 프로젝트 파일 요약을 absorbed에 기록
            local ts
            ts=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
            local file_count
            file_count=$(find "$proj_dir" -not -path '*/.git/*' -not -path '*/target/*' -not -path '*/node_modules/*' -type f 2>/dev/null | wc -l | tr -d ' ')
            echo "{\"ts\":\"$ts\",\"project\":\"$proj_name\",\"files\":$file_count,\"seeded_by\":\"$GROWTH_NAME\"}" > "$proj_dir/.growth/absorbed/seed_${GROWTH_NAME}.json" 2>/dev/null || true
            log_info "  $proj_name: 시드 데이터 생성 (files=$file_count)"
        fi
    done
}

# ── 공통 Phase: 대시보드 HTML 갱신 ──
common_update_dashboard() {
    local cycle="$1"
    local dash_file="$HOME/.nexus6/dashboard.html"
    local status_file="$HOME/.nexus6/daemon_status.txt"
    local loop_report="$HOME/.nexus6/last_loop_report.txt"
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S')

    cat > "$dash_file" <<DASH
<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta http-equiv="refresh" content="60">
<title>NEXUS-6 Dashboard</title>
<style>body{background:#0a0a0a;color:#0f0;font-family:monospace;padding:20px}
pre{background:#111;padding:15px;border:1px solid #333;overflow-x:auto}
h1{color:#0ff}h2{color:#ff0}.ts{color:#888}</style></head>
<body><h1>NEXUS-6 Dashboard</h1>
<p class="ts">Updated: ${ts} | Project: ${GROWTH_NAME} | Cycle: ${cycle}</p>
<h2>Daemon Status</h2><pre>$(cat "$status_file" 2>/dev/null || echo "No daemon running")</pre>
<h2>Last Loop Report</h2><pre>$(cat "$loop_report" 2>/dev/null || echo "No report yet")</pre>
<h2>Growth Bus (last 10)</h2><pre>$(tail -10 "$HOME/Dev/nexus6/shared/growth_bus.jsonl" 2>/dev/null || echo "Empty")</pre>
</body></html>
DASH
}

# ── 메인 루프 래퍼 ──
# 사용법: run_growth_loop <domain_phases_func> [args...]
# domain_phases_func: 프로젝트별 phase 함수 (각 프로젝트에서 정의)
run_growth_loop() {
    local domain_phases="$1"
    local max_cycles="${MAX_CYCLES:-999}"
    local interval="${INTERVAL:-1800}"
    local dry_run="${DRY_RUN:-false}"
    local domain="${DOMAIN:-number_theory}"

    acquire_lock
    trap 'log_info "Shutdown..."; release_lock; exit 0' INT TERM

    log_info "=== ${GROWTH_NAME} Growth Loop ==="
    log_info "    cycles=$max_cycles interval=${interval}s domain=$domain"

    local cycle=0
    while [ "$cycle" -lt "$max_cycles" ]; do
        cycle=$((cycle + 1))
        log_info "━━━ Cycle $cycle/$max_cycles ━━━"

        # 부하 체크
        local load_status
        load_status=$(check_load)
        if [ "$load_status" = "STOP" ]; then
            log_warn "과부하 — 60초 대기"
            sleep 60; continue
        fi

        # 프로젝트별 phases
        $domain_phases "$cycle" "$load_status"

        # 공통 phases
        common_nexus6_scan "$domain"
        common_blowup "$domain"
        common_cross_pollinate
        common_growth_bridge
        common_update_state "$cycle"
        common_auto_commit "$cycle" "$dry_run"

        # 10 사이클마다 휴면 프로젝트 활성화
        if [ $((cycle % 10)) -eq 0 ]; then
            common_seed_dormant
        fi

        # 대시보드 갱신
        common_update_dashboard "$cycle"

        if [ "$cycle" -lt "$max_cycles" ]; then
            log_info "💤 ${interval}s 대기..."
            sleep "$interval" &
            local spid=$!
            trap 'log_info "Shutdown..."; kill $spid 2>/dev/null; release_lock; exit 0' INT TERM
            wait "$spid" 2>/dev/null || true
        fi
    done

    log_info "=== ${GROWTH_NAME} Growth 완료 ($cycle cycles) ==="
    release_lock
}
