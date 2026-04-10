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
GROWTH_BUS="$HOME/Dev/nexus/shared/discovery/growth_bus.jsonl"
LOCKFILE="/tmp/n6-growth-${GROWTH_NAME}.lock"

# ── 루프 순서 정의 (shared/loop/{project}.json) ──
LOOP_DEF="$HOME/Dev/nexus/shared/loop/${GROWTH_NAME}.json"
if [ -f "$LOOP_DEF" ]; then
    _loop_interval=$(/usr/bin/python3 -c "import json; print(json.load(open('$LOOP_DEF')).get('interval', 1800))" 2>/dev/null)
    _loop_max=$(/usr/bin/python3 -c "import json; print(json.load(open('$LOOP_DEF')).get('max_cycles', 999))" 2>/dev/null)
    _loop_domain=$(/usr/bin/python3 -c "import json; print(json.load(open('$LOOP_DEF')).get('domain', 'number_theory'))" 2>/dev/null)
    INTERVAL="${INTERVAL:-${_loop_interval:-1800}}"
    MAX_CYCLES="${MAX_CYCLES:-${_loop_max:-999}}"
    DOMAIN="${DOMAIN:-${_loop_domain:-number_theory}}"
    log_info "📋 루프 정의 로드: $LOOP_DEF (interval=${INTERVAL}s, domain=$DOMAIN)"
fi
NEXUS_BIN="${HOME}/.cargo/bin/nexus"
if [ ! -f "$NEXUS_BIN" ]; then
    NEXUS_BIN="${HOME}/Dev/nexus/target/release/nexus"
fi
if [ ! -f "$NEXUS_BIN" ]; then
    NEXUS_BIN="${HOME}/Dev/nexus/target/debug/nexus"
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

    # Size-based rotation: > 1 MB → numbered rotation (.1, .2, … keep max 5)
    local max_bytes=1048576  # 1 MB
    local max_files=5
    local file_size
    file_size=$(stat -f%z "$GROWTH_BUS" 2>/dev/null || stat -c%s "$GROWTH_BUS" 2>/dev/null || echo 0)
    if [ "${file_size:-0}" -gt "$max_bytes" ]; then
        local i=$((max_files - 1))
        while [ "$i" -ge 1 ]; do
            [ -f "${GROWTH_BUS}.$i" ] && mv "${GROWTH_BUS}.$i" "${GROWTH_BUS}.$((i + 1))" 2>/dev/null || true
            i=$((i - 1))
        done
        mv "$GROWTH_BUS" "${GROWTH_BUS}.1" 2>/dev/null || true
        log_info "📋 growth_bus 로테이션 (${file_size}bytes → .1)"
    fi
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
common_nexus_scan() {
    log_info "📡 NEXUS-6 scan"
    if [ -f "$NEXUS_BIN" ]; then
        local domain="${1:-number_theory}"
        NEXUS_ROOT="$HOME/Dev/nexus" "$NEXUS_BIN" scan "$domain" 2>/dev/null | tail -3 | while IFS= read -r line; do
            log_info "  $line"
        done
        write_growth_bus "nexus_scan" "ok" "domain=$domain"
    else
        log_warn "nexus 바이너리 없음"
        write_growth_bus "nexus_scan" "skip" "no_binary"
    fi
}

# ── 공통 Phase: Blowup (창발) ──
common_blowup() {
    log_info "💥 Blowup (창발)"
    if [ -f "$NEXUS_BIN" ]; then
        local domain="${1:-number_theory}"
        # 30초 타임아웃 (macOS 호환: bash 백그라운드 + wait)
        (NEXUS_ROOT="$HOME/Dev/nexus" "$NEXUS_BIN" blowup "$domain" --depth 6 2>/dev/null | grep -E "따름정리|공리 후보|총 창발|깊이" | while IFS= read -r line; do
            log_info "  $line"
        done) &
        local blowup_pid=$!
        (sleep 30 && kill $blowup_pid 2>/dev/null) &
        local timer_pid=$!
        wait $blowup_pid 2>/dev/null
        kill $timer_pid 2>/dev/null || true
        wait $timer_pid 2>/dev/null || true
        write_growth_bus "blowup" "ok" "domain=$domain"
    else
        write_growth_bus "blowup" "skip" "no_binary"
    fi
}

# ── 공통 Phase: 특이점 캐스케이드 ──
common_singularity_cascade() {
    log_info "⚡ Singularity Cascade"
    local scan_file="$HOME/.nexus/last_scan.txt"
    [ ! -f "$scan_file" ] && return

    local reached=$(grep "singularity=" "$scan_file" | cut -d= -f2)
    if [ "$reached" = "REACHED" ]; then
        log_info "  ★ 특이점 도달! 공리를 형제 프로젝트에 전파"

        # 현재 공리 (n=6 상수 + 발견된 메트릭)
        local axiom_file="$GROWTH_DIR/singularity_axioms.json"
        /usr/bin/python3 -c "
import json, os, datetime
axioms = {
    'source': '$GROWTH_NAME',
    'ts': datetime.datetime.utcnow().isoformat() + 'Z',
    'axioms': ['sigma=12', 'phi=2', 'tau=4', 'n=6', 'sopfr=5', 'J2=24'],
    'domain': '$DOMAIN',
}
# scan 결과에서 추가 메트릭
scan = {}
try:
    with open('$scan_file') as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                scan[k] = v
except: pass
axioms['exact_ratio'] = scan.get('exact_ratio', '0')
axioms['convergence'] = scan.get('convergence', '0')

with open('$axiom_file', 'w') as f:
    json.dump(axioms, f, indent=2)

# 형제 프로젝트에 시드로 전파
for d in os.listdir(os.path.expanduser('~/Dev')):
    if d == '$GROWTH_NAME': continue
    seed_dir = os.path.expanduser(f'~/Dev/{d}/.growth')
    if not os.path.isdir(seed_dir): continue
    seed_file = os.path.join(seed_dir, f'cascade_from_{\"$GROWTH_NAME\"}.json')
    with open(seed_file, 'w') as sf:
        json.dump(axioms, sf, indent=2)
print(f'Cascade: axioms seeded to siblings')
" 2>/dev/null | while IFS= read -r line; do
            log_info "  $line"
        done
        write_growth_bus "singularity_cascade" "ok" "reached=true"
    else
        log_info "  특이점 미도달 — 캐스케이드 스킵"
    fi
}

# ── 공통 Phase: 크로스폴리네이션 ──
common_cross_pollinate() {
    log_info "🌸 Cross-Pollination (프로젝트간 창발)"
    local blowup_file="$HOME/.nexus/last_blowup.txt"
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
    local sync_script="$HOME/Dev/nexus/sync/sync-all.sh"
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
    /usr/bin/python3 -c "
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
    local bridge_script="$HOME/Dev/nexus/scripts/growth_bridge.sh"
    if [ -f "$bridge_script" ]; then
        bash "$bridge_script" full 2>/dev/null | tail -3 | while IFS= read -r line; do
            log_info "  $line"
        done
        write_growth_bus "growth_bridge" "ok" ""
    fi
}

# ── 공통 Phase: 공유 Discovery Graph ──
common_shared_graph() {
    log_info "🕸️ Shared Discovery Graph"
    local graph_dir="$HOME/.nexus/shared_graph"
    mkdir -p "$graph_dir"

    # 현재 프로젝트의 발견을 공유 그래프에 추가
    /usr/bin/python3 -c "
import json, os, datetime

graph_file = '$graph_dir/graph.json'
try:
    with open(graph_file) as f: graph = json.load(f)
except: graph = {'nodes': [], 'edges': []}

# 현재 프로젝트 노드
project_node = {
    'id': '$GROWTH_NAME',
    'type': 'project',
    'last_update': datetime.datetime.utcnow().isoformat() + 'Z',
}

# 기존 노드 업데이트 또는 추가
existing = [n for n in graph['nodes'] if n['id'] == '$GROWTH_NAME']
if existing:
    existing[0].update(project_node)
else:
    graph['nodes'].append(project_node)

# scan 결과에서 발견 노드 추가
scan_file = os.path.expanduser('~/.nexus/last_scan.txt')
if os.path.exists(scan_file):
    scan = {}
    with open(scan_file) as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                scan[k] = v

    disc_id = f'scan_{\"$GROWTH_NAME\"}_{scan.get(\"domain\",\"unknown\")}'
    disc_node = {
        'id': disc_id,
        'type': 'scan',
        'domain': scan.get('domain', ''),
        'exact_ratio': scan.get('exact_ratio', '0'),
        'singularity': scan.get('singularity', 'approaching'),
    }
    existing_disc = [n for n in graph['nodes'] if n['id'] == disc_id]
    if existing_disc:
        existing_disc[0].update(disc_node)
    else:
        graph['nodes'].append(disc_node)

    # 프로젝트 → 스캔 엣지
    edge = {'from': '$GROWTH_NAME', 'to': disc_id, 'type': 'scanned'}
    if edge not in graph['edges']:
        graph['edges'].append(edge)

# cross_pollinate 엣지 추가
cp_file = os.path.expanduser('~/Dev/$GROWTH_NAME/.growth/cross_pollinate.jsonl')
if os.path.exists(cp_file):
    with open(cp_file) as f:
        for line in f:
            try:
                ev = json.loads(line)
                edge = {'from': ev.get('from',''), 'to': ev.get('to',''), 'type': 'cross_pollinate'}
                if edge not in graph['edges']:
                    graph['edges'].append(edge)
            except: pass

# 노드/엣지 수 제한 (최근 200)
graph['nodes'] = graph['nodes'][-200:]
graph['edges'] = graph['edges'][-500:]

with open(graph_file, 'w') as f:
    json.dump(graph, f, indent=2)
print(f'Graph: {len(graph[\"nodes\"])} nodes, {len(graph[\"edges\"])} edges')
" 2>/dev/null | while IFS= read -r line; do
        log_info "  $line"
    done
    write_growth_bus "shared_graph" "ok" ""
}

# ── 공통 Phase: 프로젝트간 렌즈 추천 ──
common_lens_recommend() {
    log_info "🔮 Lens recommendation"
    local scan_file="$HOME/.nexus/last_scan.txt"
    [ ! -f "$scan_file" ] && return

    # 현재 프로젝트의 top 렌즈를 형제에게 추천
    /usr/bin/python3 -c "
import json, os, datetime

# scan 결과에서 도메인 추출
domain = 'unknown'
with open('$scan_file') as f:
    for line in f:
        if line.startswith('domain='): domain = line.strip().split('=',1)[1]

rec = {
    'from': '$GROWTH_NAME',
    'domain': domain,
    'ts': datetime.datetime.utcnow().isoformat() + 'Z',
    'recommendation': 'Use SingularityCycleLens + UemergenceLens for this domain',
}

for d in os.listdir(os.path.expanduser('~/Dev')):
    if d == '$GROWTH_NAME': continue
    rec_dir = os.path.expanduser(f'~/Dev/{d}/.growth')
    if not os.path.isdir(rec_dir): continue
    rec_file = os.path.join(rec_dir, 'lens_recommendations.jsonl')
    with open(rec_file, 'a') as f:
        f.write(json.dumps(rec) + '\n')
print('Recommended to siblings')
" 2>/dev/null | while IFS= read -r line; do
        log_info "  $line"
    done
    write_growth_bus "lens_recommend" "ok" ""
}

# ── 공통 Phase: 양방향 렌즈 동기화 ──
common_reverse_lens_sync() {
    log_info "🔄 Reverse lens sync"
    # 프로젝트 고유 렌즈 파일을 nexus에 역동기화
    local lens_dir="$PROJECT_ROOT/src"
    local n6_lens_dir="$HOME/Dev/nexus/src/telescope/lenses"

    [ ! -d "$lens_dir" ] && return
    [ ! -d "$n6_lens_dir" ] && return

    # 프로젝트에 singularity.rs 등 렌즈 가능 파일이 있으면 알림
    local candidates=0
    for f in "$lens_dir"/singularity*.rs "$lens_dir"/*_lens.rs "$lens_dir"/*_scan.rs; do
        [ -f "$f" ] || continue
        local fname=$(basename "$f")
        if [ ! -f "$n6_lens_dir/$fname" ]; then
            log_info "  📋 렌즈 후보: $fname ($GROWTH_NAME)"
            candidates=$((candidates + 1))
        fi
    done

    if [ "$candidates" -gt 0 ]; then
        write_growth_bus "reverse_lens" "found" "candidates=$candidates"
    else
        write_growth_bus "reverse_lens" "skip" "no_candidates"
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
    local dash_file="$HOME/.nexus/dashboard.html"
    local status_file="$HOME/.nexus/daemon_status.txt"
    local loop_report="$HOME/.nexus/last_loop_report.txt"
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
<h2>Growth Bus (last 10)</h2><pre>$(tail -10 "$HOME/Dev/nexus/shared/discovery/growth_bus.jsonl" 2>/dev/null || echo "Empty")</pre>
</body></html>
DASH
}

# ── 공통 Phase: 건강 심박 (Heartbeat) ──
common_heartbeat() {
    local hb_file="$PROJECT_ROOT/.growth/heartbeat"
    date -u '+%Y-%m-%dT%H:%M:%SZ' > "$hb_file"

    # 다른 프로젝트 심박 체크 (30분 초과 = 경고)
    local stale_count=0
    for proj_dir in "$HOME"/Dev/*/; do
        local pname=$(basename "$proj_dir")
        local phb="$proj_dir/.growth/heartbeat"
        [ ! -f "$phb" ] && continue
        local last_beat=$(cat "$phb" 2>/dev/null)
        if [ -n "$last_beat" ]; then
            local now_epoch=$(date +%s)
            local beat_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$last_beat" +%s 2>/dev/null || echo 0)
            local diff=$((now_epoch - beat_epoch))
            if [ "$diff" -gt 3600 ]; then
                log_warn "  $pname: 심박 없음 (${diff}s ago)"
                stale_count=$((stale_count + 1))
            fi
        fi
    done
    if [ "$stale_count" -eq 0 ]; then
        log_info "💓 Heartbeat OK (모든 프로젝트 활성)"
    else
        log_warn "💓 Heartbeat: ${stale_count}개 프로젝트 정체"
    fi
    write_growth_bus "heartbeat" "ok" "stale=$stale_count"
}

# ── 사이클 리포트 ──
common_cycle_report() {
    local cycle="$1"
    local elapsed=""
    local report_file="$GROWTH_DIR/last_cycle_report.txt"
    local shared_report="$HOME/.nexus/project_reports/${GROWTH_NAME}.txt"
    mkdir -p "$HOME/.nexus/project_reports"

    # growth_state에서 정보 수집
    local state_info
    state_info=$(/usr/bin/python3 -c "
import json, os
state_file = '$GROWTH_STATE'
info = {'cycle': $cycle, 'name': '$GROWTH_NAME', 'domain': '${DOMAIN:-unknown}'}
if os.path.exists(state_file):
    try:
        with open(state_file) as f:
            s = json.load(f)
        info['federated_bonus'] = s.get('federated_bonus', 0)
    except: pass
# heartbeat
hb = '$PROJECT_ROOT/.growth/heartbeat'
info['heartbeat'] = open(hb).read().strip()[:16] if os.path.exists(hb) else '?'
# blowup
bf = os.path.expanduser('~/.nexus/last_blowup.txt')
if os.path.exists(bf):
    for line in open(bf):
        if 'total_emergences=' in line:
            info['emergences'] = line.strip().split('=',1)[1]
# scan
sf = os.path.expanduser('~/.nexus/last_scan.txt')
if os.path.exists(sf):
    for line in open(sf):
        if 'singularity=' in line:
            info['singularity'] = line.strip().split('=',1)[1]
        if 'exact_ratio=' in line:
            info['exact_ratio'] = line.strip().split('=',1)[1]
print(json.dumps(info))
" 2>/dev/null || echo '{}')

    local w=55
    local line_sep=$(printf '%0.s─' $(seq 1 $w))
    {
        echo "  ┌${line_sep}┐"
        echo "  │ 📋 ${GROWTH_NAME} Cycle $cycle $(printf '%*s' $((w - 15 - ${#GROWTH_NAME} - ${#cycle})) '')│"
        echo "  ├${line_sep}┤"
        echo "$state_info" | /usr/bin/python3 -c "
import json, sys
info = json.load(sys.stdin)
w = $w
print(f'  │ {\"도메인: \" + info.get(\"domain\",\"?\"):<{w}}│')
print(f'  │ {\"심박: \" + info.get(\"heartbeat\",\"?\"):<{w}}│')
print(f'  │ {\"연방 보너스: \" + str(info.get(\"federated_bonus\",0)):<{w}}│')
print(f'  │ {\"창발: \" + str(info.get(\"emergences\",\"?\")):<{w}}│')
print(f'  │ {\"특이점: \" + info.get(\"singularity\",\"?\"):<{w}}│')
print(f'  │ {\"EXACT ratio: \" + info.get(\"exact_ratio\",\"?\"):<{w}}│')
" 2>/dev/null
        echo "  └${line_sep}┘"
    } | tee "$report_file"

    # 공유 리포트에도 저장 (mega에서 읽을 수 있도록)
    cp "$report_file" "$shared_report" 2>/dev/null || true
    write_growth_bus "cycle_report" "ok" "cycle=$cycle"
}

# ── 공통 Phase: Project DNA 메타데이터 수집 ──
common_project_dna() {
    log_info "🧬 Project DNA scan"
    local bridge_json="$HOME/Dev/nexus/shared/bridge_state.json"
    [ ! -f "$bridge_json" ] && return

    /usr/bin/python3 -c "
import json, os, subprocess, glob
from datetime import datetime, timezone

bridge_file = '$bridge_json'
with open(bridge_file) as f:
    state = json.load(f)

name = '$GROWTH_NAME'
root = '$PROJECT_ROOT'
conn = state.get('connections', {}).get(name, {})

# 1. 모듈 목록
modules = []
if os.path.exists(f'{root}/Cargo.toml'):
    for f_rs in glob.glob(f'{root}/src/**/*.rs', recursive=True):
        mod_name = os.path.splitext(os.path.basename(f_rs))[0]
        if mod_name not in ('mod', 'lib', 'main'):
            modules.append(mod_name)
elif os.path.exists(f'{root}/src'):
    for f_py in glob.glob(f'{root}/src/**/*.py', recursive=True):
        mod_name = os.path.splitext(os.path.basename(f_py))[0]
        if mod_name != '__init__':
            modules.append(mod_name)
conn['modules'] = modules[:50]  # 최대 50개
conn['module_count'] = len(modules)

# 2. 테스트 수
test_count = 0
test_pass = 0
if os.path.exists(f'{root}/Cargo.toml'):
    try:
        r = subprocess.run(['$HOME/.cargo/bin/cargo', 'test', '--manifest-path', f'{root}/Cargo.toml', '--', '--quiet'],
                          capture_output=True, text=True, timeout=30)
        for line in r.stdout.split('\n') + r.stderr.split('\n'):
            if 'passed' in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == 'passed':
                        try: test_pass = int(parts[i-1])
                        except: pass
                    if p == 'failed':
                        try: test_count += int(parts[i-1])
                        except: pass
                test_count += test_pass
    except: pass
conn['test_count'] = test_count
conn['test_pass'] = test_pass

# 3. 언어 / 빌드 시스템
lang = 'unknown'
build = 'none'
if os.path.exists(f'{root}/Cargo.toml'):
    lang = 'rust'
    build = 'cargo'
elif os.path.exists(f'{root}/package.json'):
    lang = 'javascript'
    build = 'npm'
elif os.path.exists(f'{root}/pyproject.toml') or os.path.exists(f'{root}/setup.py'):
    lang = 'python'
    build = 'pip'
elif any(glob.glob(f'{root}/**/*.py', recursive=True)):
    lang = 'python'
    build = 'script'
conn['language'] = lang
conn['build_system'] = build

# 4. 최근 커밋 빈도 (7일)
try:
    r = subprocess.run(['git', '-C', root, 'rev-list', '--count', '--since=7.days', 'HEAD'],
                      capture_output=True, text=True, timeout=10)
    conn['commits_7d'] = int(r.stdout.strip()) if r.stdout.strip() else 0
except:
    conn['commits_7d'] = 0

# 5. 파일 수
try:
    total_files = 0
    for dp, dn, fns in os.walk(root):
        dn[:] = [d for d in dn if d not in ('.git', 'target', 'node_modules', '__pycache__')]
        total_files += len(fns)
    conn['total_files'] = total_files
except:
    conn['total_files'] = 0

conn['dna_updated'] = datetime.now(timezone.utc).isoformat()

state['connections'][name] = conn
with open(bridge_file, 'w') as f:
    json.dump(state, f, indent=2)
    f.write('\n')

print(f'DNA: {lang}/{build} | {len(modules)} modules | {test_pass}/{test_count} tests | {conn.get(\"commits_7d\",0)} commits/7d | {conn.get(\"total_files\",0)} files')
" 2>/dev/null | while IFS= read -r line; do
        log_info "  $line"
    done
    write_growth_bus "project_dna" "ok" "project=$GROWTH_NAME"
}

# ── 공통 Phase: 성장 포인트 연방제 ──
common_federated_growth() {
    log_info "🤝 Federated growth"
    local my_state="$GROWTH_DIR/growth_state.json"
    [ ! -f "$my_state" ] && return

    local my_cycle
    my_cycle=$(/usr/bin/python3 -c "import json; print(json.load(open('$my_state')).get('cycle',0))" 2>/dev/null || echo 0)

    # 내 성장을 형제 프로젝트에 비례 전파 (10% 보너스)
    for proj_dir in "$HOME"/Dev/*/; do
        local pname=$(basename "$proj_dir")
        [ "$pname" = "$GROWTH_NAME" ] && continue
        local pstate="$proj_dir/.growth/growth_state.json"
        [ ! -f "$pstate" ] && continue

        /usr/bin/python3 -c "
import json
f = '$pstate'
try:
    with open(f) as fh: s = json.load(fh)
except: s = {}
bonus = int($my_cycle * 0.1)
s.setdefault('federated_bonus', 0)
s['federated_bonus'] = s.get('federated_bonus', 0) + bonus
s['last_federation_from'] = '$GROWTH_NAME'
with open(f, 'w') as fh: json.dump(s, fh, indent=2); fh.write('\n')
" 2>/dev/null || true
    done
    log_info "  cycle $my_cycle → 형제에 10% 보너스 전파"
    write_growth_bus "federation" "ok" "cycle=$my_cycle"
}

# ── 공통 Phase: Affinity 기반 자동 라우팅 ──
common_auto_route() {
    log_info "🔀 Auto-routing (affinity 기반)"
    local bridge_state="$HOME/Dev/nexus/shared/bridge_state.json"
    [ ! -f "$bridge_state" ] && return

    # blowup 결과가 있으면 최적 프로젝트로 라우팅
    local blowup_file="$HOME/.nexus/last_blowup.txt"
    [ ! -f "$blowup_file" ] && return

    /usr/bin/python3 -c "
import json, os
# bridge_state에서 라우팅 테이블 로드
with open('$bridge_state') as f:
    state = json.load(f)
rt = state.get('routing_table', {})
conns = state.get('connections', {})

# affinity 상위 3개 프로젝트
ranked = sorted(conns.items(), key=lambda x: x[1].get('affinity_score', 0), reverse=True)
top3 = [name for name, info in ranked[:3] if name != '$GROWTH_NAME']

# blowup 결과에서 도메인 추출
domain = ''
with open('$blowup_file') as f:
    for line in f:
        if line.startswith('domain='):
            domain = line.strip().split('=',1)[1]
            break

if top3 and domain:
    for proj in top3:
        route_file = os.path.expanduser(f'~/Dev/{proj}/.growth/routed_from_${GROWTH_NAME}.jsonl')
        os.makedirs(os.path.dirname(route_file), exist_ok=True)
        import datetime
        entry = json.dumps({
            'ts': datetime.datetime.utcnow().isoformat() + 'Z',
            'from': '$GROWTH_NAME',
            'domain': domain,
            'affinity': conns.get(proj, {}).get('affinity_score', 0),
        })
        with open(route_file, 'a') as rf:
            rf.write(entry + '\n')
    print(f'Routed to: {top3}')
" 2>/dev/null | while IFS= read -r line; do
        log_info "  $line"
    done
    write_growth_bus "auto_route" "ok" ""
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

        # bridge_state 백업
        local bridge_json="$HOME/Dev/nexus/shared/bridge_state.json"
        if [ -f "$bridge_json" ]; then
            cp "$bridge_json" "${bridge_json}.bak" 2>/dev/null || true
        fi

        # 부하 체크
        local load_status
        load_status=$(check_load)
        if [ "$load_status" = "STOP" ]; then
            log_warn "과부하 — 60초 대기"
            sleep 60; continue
        fi

        # 디스크 공간 체크
        local free_gb
        free_gb=$(df -g / 2>/dev/null | tail -1 | awk '{print $4}')
        if [ "${free_gb:-99}" -lt 2 ]; then
            log_warn "⚠️ 디스크 부족 (${free_gb}GB) — incremental cache 정리"
            for d in "$HOME"/Dev/*/target/*/incremental; do
                [ -d "$d" ] && rm -rf "$d" 2>/dev/null
            done
            log_info "  cache 정리 완료"
        fi

        # 프로젝트별 phases
        $domain_phases "$cycle" "$load_status"

        # 공통 phases (매 사이클)
        common_nexus_scan "$domain"
        common_blowup "$domain"
        common_singularity_cascade
        common_cross_pollinate
        common_auto_route
        common_growth_bridge
        common_shared_graph
        common_heartbeat
        common_vector_clock 2>/dev/null || true
        common_metric_bus_publish 2>/dev/null || true
        common_resonance_bridge 2>/dev/null || true
        common_update_state "$cycle"
        common_auto_commit "$cycle" "$dry_run"

        # 3 사이클마다 (네트워크 + 실험)
        if [ $((cycle % 3)) -eq 0 ]; then
            common_sync_priority_queue 2>/dev/null || true
            common_cross_test 2>/dev/null || true
            common_live_graph 2>/dev/null || true
            common_growth_timeline 2>/dev/null || true
        fi

        # 6 사이클마다 (DNA + 연결 + 이력 + 연방 + 렌즈 + 실험)
        if [ $((cycle % 6)) -eq 0 ]; then
            common_project_dna
            common_connection_metrics 2>/dev/null || true
            common_growth_history 2>/dev/null || true
            common_auto_actions 2>/dev/null || true
            common_federated_growth
            common_reverse_lens_sync
            common_cross_experiment 2>/dev/null || true
        fi

        # 12 사이클마다 (렌즈 추천)
        if [ $((cycle % 12)) -eq 0 ]; then
            common_lens_recommend
        fi

        # 10 사이클마다 (휴면 활성화)
        if [ $((cycle % 10)) -eq 0 ]; then
            common_seed_dormant
        fi

        # 대시보드 갱신
        common_update_dashboard "$cycle"

        # 사이클 리포트
        common_cycle_report "$cycle"

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

# ── 확장 모듈 로딩 ──
_COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "$_COMMON_DIR/growth_advanced.sh" ] && source "$_COMMON_DIR/growth_advanced.sh"
[ -f "$_COMMON_DIR/growth_network.sh" ] && source "$_COMMON_DIR/growth_network.sh"
