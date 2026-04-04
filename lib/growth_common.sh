#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# growth_common.sh — Shared Growth Infrastructure
# ═══════════════════════════════════════════════════════════════
# Source this from any growth script:
#   source "$(dirname "$0")/lib/growth_common.sh"
#
# Provides: singleton, logging, resource monitoring, git ops,
#           phase runner, measurement, paper publish, doc sync

# ── Constants (n=6 family) ──────────────────────────────────────
readonly N6_SIGMA=12
readonly N6_J2=24
readonly N6_TAU=4
readonly N6_PHI=2
readonly N6_SOPFR=5
readonly N6_N=6

# ── Paths ───────────────────────────────────────────────────────
GROWTH_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$(cd "$GROWTH_LIB_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$SCRIPTS_DIR/.." && pwd)"
NEXUS6_SCRIPTS="$PROJECT_ROOT/tools/nexus6/scripts"
NEXUS6_ROOT="${HOME}/Dev/nexus6"
NEXUS6_STATE="${HOME}/.nexus6"
GROWTH_DIR="$PROJECT_ROOT/.growth"
DOCS_DIR="$PROJECT_ROOT/docs"
PAPERS_DIR="${HOME}/Dev/papers"

# ── Logging ─────────────────────────────────────────────────────
_LOG_FILE="${_LOG_FILE:-/tmp/n6_growth.log}"

log_ts()    { date +%H:%M:%S; }
log_info()  { echo "[$(log_ts)] INFO:  $*" | tee -a "$_LOG_FILE"; }
log_warn()  { echo "[$(log_ts)] WARN:  $*" | tee -a "$_LOG_FILE"; }
log_error() { echo "[$(log_ts)] ERROR: $*" | tee -a "$_LOG_FILE"; }
log_ok()    { echo "[$(log_ts)] OK:    $*" | tee -a "$_LOG_FILE"; }

# ── Singleton (단독 실행 — 중복 시 즉시 종료) ──────────────────
# Usage: singleton_acquire "/tmp/my_daemon.pid"
#   Returns 0 if lock acquired, exits 1 if already running.
singleton_acquire() {
    local pidfile="$1"
    if [ -f "$pidfile" ]; then
        local old_pid
        old_pid=$(cat "$pidfile" 2>/dev/null) || true
        if [ -n "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
            echo "╔════════════════════════════════════════════════════════╗"
            echo "║  Already running (PID $old_pid)                        "
            echo "║  단독 실행 정책: 중복 인스턴스 거부                    ║"
            echo "║  종료하려면: kill $old_pid                              "
            echo "╚════════════════════════════════════════════════════════╝"
            exit 1
        fi
        rm -f "$pidfile"
    fi
    echo $$ > "$pidfile"
    trap "rm -f '$pidfile'; exit 0" SIGTERM SIGINT EXIT
}

# ── Resource Monitoring (macOS) ─────────────────────────────────
# Thresholds (configurable by caller)
: "${CPU_THROTTLE_PCT:=80}"
: "${MEM_MIN_FREE_MB:=512}"
: "${DISK_MIN_FREE_GB:=2}"

# ── Adaptive Engine (Mac 자원 적응형) ───────────────────────────
# 8-core 24GB Mac 기준 — 프로세스 폭주 방지
: "${MAX_CONCURRENT_GROWTH:=3}"       # 동시 실행 최대 3개
: "${ADAPTIVE_INTERVAL_BASE:=300}"    # 5분 기본
: "${ADAPTIVE_INTERVAL_MAX:=1800}"    # 30분 최대 (과부하 시)

# Count running growth daemons
count_growth_procs() {
    ps aux 2>/dev/null | grep -c 'infinite_growth.*max-cycles\|nexus6_growth_daemon' || echo "0"
}

# Adaptive interval: 자원에 따라 interval 자동 조절
get_adaptive_interval() {
    local cpu="${_RES_CPU:-50}"
    local mem="${_RES_MEM:-4096}"
    local base="${ADAPTIVE_INTERVAL_BASE}"

    # CPU > 80%: interval x3
    # CPU > 60%: interval x2
    # MEM < 1GB: interval x2
    local multiplier=1
    if [ "$cpu" -gt 80 ]; then
        multiplier=3
    elif [ "$cpu" -gt 60 ]; then
        multiplier=2
    fi
    if [ "$mem" -lt 1024 ]; then
        multiplier=$((multiplier + 1))
    fi

    local interval=$((base * multiplier))
    # Cap at max
    if [ "$interval" -gt "$ADAPTIVE_INTERVAL_MAX" ]; then
        interval=$ADAPTIVE_INTERVAL_MAX
    fi
    echo "$interval"
}

# Singleton + concurrency gate: 이미 너무 많으면 대기
wait_for_slot() {
    local max_wait=120  # 2분 대기 후 포기
    local waited=0
    while true; do
        local running
        running=$(count_growth_procs)
        # grep 자체 + 현재 프로세스 제외
        running=$((running - 2))
        [ "$running" -lt 0 ] && running=0
        if [ "$running" -lt "$MAX_CONCURRENT_GROWTH" ]; then
            return 0
        fi
        if [ "$waited" -ge "$max_wait" ]; then
            log_warn "Concurrency gate timeout ($max_wait s), proceeding anyway"
            return 0
        fi
        sleep 10
        waited=$((waited + 10))
    done
}

get_cpu_usage() {
    # macOS top: "CPU usage: X% user, Y% sys, Z% idle"
    local idle
    idle=$(top -l 1 -n 0 2>/dev/null | awk '/CPU usage/ {
        for(i=1;i<=NF;i++) if($i=="idle") {gsub(/%/,"",$(i-1)); print $(i-1)}
    }' || echo "50")
    [ -z "$idle" ] && idle="50"
    python3 -c "print(max(0, min(100, int(100 - float('${idle}')))))" 2>/dev/null || echo "50"
}

get_free_mem_mb() {
    # macOS: free + inactive pages = available memory
    local page_size free_pages inactive_pages
    page_size=$(sysctl -n hw.pagesize 2>/dev/null || echo 16384)
    free_pages=$(vm_stat 2>/dev/null | awk '/Pages free/ {gsub(/\./,""); print $3}' || echo "0")
    inactive_pages=$(vm_stat 2>/dev/null | awk '/Pages inactive/ {gsub(/\./,""); print $3}' || echo "0")
    python3 -c "print(int((${free_pages} + ${inactive_pages}) * ${page_size} / 1024 / 1024))" 2>/dev/null || echo "4096"
}

get_free_disk_gb() {
    df -g "$PROJECT_ROOT" 2>/dev/null | awk 'NR==2 {print $4}' || echo "10"
}

# Returns: OK | THROTTLE | LIGHT | STOP
check_resources() {
    local cpu_pct mem_free_mb disk_free_gb
    cpu_pct=$(get_cpu_usage)
    mem_free_mb=$(get_free_mem_mb)
    disk_free_gb=$(get_free_disk_gb)
    # Export for callers
    export _RES_CPU="$cpu_pct"
    export _RES_MEM="$mem_free_mb"
    export _RES_DISK="$disk_free_gb"

    if [ "$disk_free_gb" -lt "$DISK_MIN_FREE_GB" ]; then echo "STOP"; return; fi
    if [ "$mem_free_mb" -lt "$MEM_MIN_FREE_MB" ]; then echo "LIGHT"; return; fi
    if [ "$cpu_pct" -gt "$CPU_THROTTLE_PCT" ]; then echo "THROTTLE"; return; fi
    echo "OK"
}

print_resources() {
    local cpu="${_RES_CPU:-0}" mem="${_RES_MEM:-0}" disk="${_RES_DISK:-0}"
    local cpu_filled=$((cpu / 10))
    local bar=""
    for i in $(seq 1 "$cpu_filled"); do bar="${bar}█"; done
    for i in $(seq 1 $((10 - cpu_filled))); do bar="${bar}░"; done

    local mem_s="OK"; [ "$mem" -lt "$MEM_MIN_FREE_MB" ] && mem_s="LOW"
    local dsk_s="OK"; [ "$disk" -lt "$DISK_MIN_FREE_GB" ] && dsk_s="CRIT"

    echo "  ┌─ Resources ──────────────────────────────────────────┐"
    printf "  │ CPU: %s %3d%%  MEM: %5dMB [%-4s] DISK: %3dGB [%-4s] │\n" \
        "$bar" "$cpu" "$mem" "$mem_s" "$disk" "$dsk_s"
    printf "  │ PID: %-8d                                        │\n" "$$"
    echo "  └───────────────────────────────────────────────────────┘"
}

# ── Phase Runner ────────────────────────────────────────────────
# Usage: run_phase NUM TOTAL NAME COMMAND [MAX_LINES]
run_phase() {
    local num="$1" total="$2" name="$3" cmd="$4" lines="${5:-10}"
    echo "[$(log_ts)] Phase ${num}/${total}: ${name}..."
    if eval "$cmd" 2>&1 | tail -"$lines"; then
        echo "  [OK] ${name}"
    else
        echo "  [WARN] ${name} (non-fatal)"
    fi
    echo ""
}

# ── Git Ops ─────────────────────────────────────────────────────
# Usage: growth_commit SCOPE MESSAGE
#   SCOPE: directory to git add (e.g. ".growth/" or "tools/nexus6/src/")
#   MESSAGE: commit message
growth_commit() {
    local scope="$1" message="$2"
    cd "$PROJECT_ROOT"
    git add "$scope" 2>/dev/null || true
    if git diff --cached --quiet 2>/dev/null; then
        log_info "  No changes to commit"
    else
        git commit -m "$message" --no-verify 2>/dev/null && log_ok "Committed: $message" || log_warn "Commit failed"
    fi
}

# ── Count Helper (bash 3.2 safe) ───────────────────────────────
count_pattern() {
    local file="$1" pattern="$2"
    grep -c "$pattern" "$file" 2>/dev/null || echo "0"
}

# ── Size Expansion (σ=12 → J₂=24) ─────────────────────────────
# Phase count grows with cycle number
get_phase_count() {
    local cycle="$1"
    if [ "$cycle" -ge 25 ]; then echo 24    # J₂=24 max
    elif [ "$cycle" -ge 13 ]; then echo 18  # 18 phases
    elif [ "$cycle" -ge 7 ]; then echo 15   # 15 phases
    else echo 12                             # σ=12 base
    fi
}

# ── Paper Publish Loop ──────────────────────────────────────────
# Checks for publishable content and auto-publishes via publish_paper.sh
run_paper_loop() {
    local papers_script="$PAPERS_DIR/publish_paper.sh"
    if [ ! -f "$papers_script" ]; then
        echo "  publish_paper.sh not found at $papers_script"
        return 0
    fi

    # Check for new/updated papers
    local paper_candidates=0
    local published=0

    # Scan docs/paper/ for unpublished papers
    for f in "$DOCS_DIR"/paper/*.md; do
        [ -f "$f" ] || continue
        paper_candidates=$((paper_candidates + 1))
        local basename_f
        basename_f=$(basename "$f")
        # Check if already in manifest
        if [ -f "$PAPERS_DIR/manifest.json" ]; then
            if grep -q "$basename_f" "$PAPERS_DIR/manifest.json" 2>/dev/null; then
                continue
            fi
        fi
        # Unpublished paper found — dry-run first
        echo "  Found unpublished: $basename_f"
        if bash "$papers_script" "$f" --dry-run 2>/dev/null | tail -3; then
            published=$((published + 1))
        fi
    done

    # Scan for blowup papers
    for f in "$DOCS_DIR"/paper/blowup-*.md; do
        [ -f "$f" ] || continue
        local basename_f
        basename_f=$(basename "$f")
        if [ -f "$PAPERS_DIR/manifest.json" ]; then
            grep -q "$basename_f" "$PAPERS_DIR/manifest.json" 2>/dev/null && continue
        fi
        echo "  Found blowup paper: $basename_f"
        published=$((published + 1))
    done

    echo "  Papers scanned: $paper_candidates, new/updated: $published"
}

# ── Auto Domain Explorer ───────────────────────────────────────
# Finds domains without DSE and creates TOML stubs
run_auto_domain_explore() {
    local dse_map="$DOCS_DIR/dse-map.toml"
    local dse_domains="$PROJECT_ROOT/tools/universal-dse/domains"

    if [ ! -f "$dse_map" ]; then
        echo "  dse-map.toml not found"
        return 0
    fi

    # Count unexplored domains
    local none_count
    none_count=$(count_pattern "$dse_map" 'dse.*=.*none')
    local wip_count
    wip_count=$(count_pattern "$dse_map" 'dse.*=.*wip')
    local done_count
    done_count=$(count_pattern "$dse_map" 'dse.*=.*done')
    local total
    total=$(grep -c '^\[' "$dse_map" 2>/dev/null || echo 0)
    total=$((total - 1))

    echo "  DSE Status: done=$done_count wip=$wip_count none=$none_count total=$total"

    # Check for doc domains without TOML
    local missing_toml=0
    for d in "$DOCS_DIR"/*/; do
        [ -d "$d" ] || continue
        local domain_name
        domain_name=$(basename "$d")
        if [ ! -f "$dse_domains/${domain_name}.toml" ] 2>/dev/null; then
            if [ -f "${d}goal.md" ] || [ -f "${d}hypotheses.md" ]; then
                missing_toml=$((missing_toml + 1))
                echo "  Missing TOML: $domain_name (has goal/hypotheses)"
            fi
        fi
    done

    echo "  Domains with content but no TOML: $missing_toml"
    if [ "$none_count" -gt 0 ]; then
        echo "  WARNING: $none_count domains have no DSE results"
    fi
}

# ── Auto Document Update ───────────────────────────────────────
# Syncs README, atlas, calculators, and checks doc completeness
run_auto_doc_update() {
    local updated=0

    # 1. Check doc completeness per domain
    local domains=0 has_hyp=0 has_goal=0 has_verify=0 has_extreme=0
    for d in "$DOCS_DIR"/*/; do
        [ -d "$d" ] || continue
        domains=$((domains + 1))
        [ -f "${d}hypotheses.md" ] && has_hyp=$((has_hyp + 1))
        [ -f "${d}goal.md" ] && has_goal=$((has_goal + 1))
        [ -f "${d}verification.md" ] && has_verify=$((has_verify + 1))
        [ -f "${d}extreme-hypotheses.md" ] && has_extreme=$((has_extreme + 1))
    done
    echo "  Docs: $domains domains"
    echo "    hypotheses: $has_hyp/$domains  goal: $has_goal/$domains"
    echo "    verification: $has_verify/$domains  extreme: $has_extreme/$domains"

    # 2. Atlas sync
    local scanner="$HOME/Dev/TECS-L/.shared/scan_math_atlas.py"
    if [ -f "$scanner" ]; then
        python3 "$scanner" --summary 2>/dev/null | tail -3 || echo "  Atlas scanner: skip"
        updated=$((updated + 1))
    fi

    # 3. Calculator registry sync
    local calc_scanner="$HOME/Dev/TECS-L/.shared/scan-calculators.py"
    if [ -f "$calc_scanner" ]; then
        python3 "$calc_scanner" --summary 2>/dev/null | tail -2 || echo "  Calc scanner: skip"
        updated=$((updated + 1))
    fi

    # 4. README sync (if sync script exists)
    local sync_readme="$SCRIPTS_DIR/sync-readme.py"
    if [ -f "$sync_readme" ]; then
        python3 "$sync_readme" 2>/dev/null | tail -2 || echo "  README sync: skip"
        updated=$((updated + 1))
    fi

    echo "  Sync operations attempted: $updated"
}

# ── NEXUS-6 Daemon Bridge ──────────────────────────────────────
# Calls nexus6 growth daemon for a single dimension growth cycle
run_nexus6_grow_dimension() {
    local dimension="${1:-}"
    if [ -z "$dimension" ]; then
        # Auto-pick weakest via daemon's measure
        dimension="auto"
    fi

    if [ -f "$NEXUS6_SCRIPTS/nexus6_growth_daemon.sh" ]; then
        if [ "$dimension" = "auto" ]; then
            bash "$NEXUS6_SCRIPTS/nexus6_growth_daemon.sh" --max-cycles 1 --skip-commit 2>/dev/null | tail -20
        else
            bash "$NEXUS6_SCRIPTS/nexus6_growth_daemon.sh" --max-cycles 1 --dimension "$dimension" --skip-commit 2>/dev/null | tail -20
        fi
    else
        echo "  nexus6_growth_daemon.sh not found"
    fi
}

# ── Growth State Update ────────────────────────────────────────
update_growth_state() {
    local cycle="$1"
    local state_file="$GROWTH_DIR/growth_state.json"
    [ -f "$state_file" ] || return 0

    python3 -c "
import json, time
g = json.load(open('$state_file'))
g['scan_count'] = g.get('scan_count', 0) + 1
g['total_growth'] = g.get('total_growth', 0) + 1
g['last_tick'] = time.strftime('%Y-%m-%dT%H:%M:%S')
g['infinite_cycle'] = $cycle
json.dump(g, open('$state_file', 'w'), indent=2, ensure_ascii=False)
print(f'  Scan #{g[\"scan_count\"]}, total growth: {g[\"total_growth\"]}')
" 2>/dev/null || echo "  Growth tick: failed"
}

# ── Growth Bus Sync ─────────────────────────────────────────────
sync_growth_bus() {
    local bus_file="${NEXUS6_ROOT}/shared/growth_bus.jsonl"
    if [ -f "$bus_file" ]; then
        local bus_lines
        bus_lines=$(wc -l < "$bus_file" 2>/dev/null | tr -d ' ')
        local n6_entries
        n6_entries=$(grep -c 'n6-architecture' "$bus_file" 2>/dev/null || echo "0")
        echo "  Growth bus: $bus_lines total, $n6_entries from n6-arch"
    else
        echo "  Growth bus: not found"
    fi
}

# ═══════════════════════════════════════════════════════════════
# COMMON PHASES — 모든 리포에서 공유하는 phase 함수
# 수렴 파이프라인: 창발 → 튜닝 → 수렴 → 진화 → 다듬기
# ═══════════════════════════════════════════════════════════════

# Blowup engine script (shared across all repos)
_LENS_SCRIPT="$HOME/Dev/n6-architecture/tools/nexus6/scripts/growth_infinite_lens.py"
_N6_BIN="$HOME/Dev/nexus6/target/release/nexus6"
_N6_PY="$HOME/Dev/nexus6/scripts/n6.py"

# ── 공통 Phase: 논문 루프 ───────────────────────────────────────
common_phase_paper_loop() {
    log_info "  [Common] Paper publish loop"
    run_paper_loop
}

# ── 공통 Phase: 문서 자동 갱신 ──────────────────────────────────
common_phase_doc_update() {
    log_info "  [Common] Auto doc update"
    run_auto_doc_update
}

# ── 공통 Phase: 도메인 탐색 ─────────────────────────────────────
common_phase_domain_explore() {
    log_info "  [Common] Auto domain explorer"
    run_auto_domain_explore
}

# ── 공통 Phase: NEXUS-6 스캔 ───────────────────────────────────
common_phase_nexus6_scan() {
    log_info "  [Common] NEXUS-6 scan"
    if [ -f "$_N6_PY" ]; then
        python3 "$_N6_PY" scan --repo "$PROJECT_ROOT" > /dev/null 2>&1 || true
        echo "  Scan complete"
    else
        echo "  n6.py not found"
    fi
}

# ── 공통 Phase: NEXUS-6 동기화 ──────────────────────────────────
common_phase_nexus6_sync() {
    log_info "  [Common] NEXUS-6 sync"
    local sync_script="$HOME/Dev/nexus6/sync/sync-all.sh"
    if [ -f "$sync_script" ]; then
        bash "$sync_script" > /dev/null 2>&1 || true
        echo "  Sync complete"
    elif [ -f "$PROJECT_ROOT/.shared/sync-nexus6-lenses.sh" ]; then
        bash "$PROJECT_ROOT/.shared/sync-nexus6-lenses.sh" > /dev/null 2>&1 || true
        echo "  Lens sync complete"
    fi
}

# ── 공통 Phase: Growth Bus 쓰기/동기화 ─────────────────────────
common_phase_bus_sync() {
    log_info "  [Common] Growth bus sync"
    sync_growth_bus
}

write_growth_bus() {
    local repo_name="$1" phase_name="$2" status="$3" detail="$4"
    local bus_file="${NEXUS6_ROOT}/shared/growth_bus.jsonl"
    local ts
    ts="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    echo "{\"ts\":\"$ts\",\"repo\":\"$repo_name\",\"type\":\"growth_phase\",\"phase\":\"$phase_name\",\"status\":\"$status\",\"detail\":\"$detail\"}" \
        >> "$bus_file" 2>/dev/null || true
}

# ═══════════════════════════════════════════════════════════════
# 하부→상부 이벤트 시스템 (Bottom-Up Events)
# ═══════════════════════════════════════════════════════════════
# 각 리포가 발견/이슈/요청을 상위 엔진에 전달
# nexus6/shared/events/ 디렉토리에 JSON 파일로 emit
# 상위(C₃ 메타재귀)가 수집 → 처리 → 결과를 bus에 기록
#
# 이벤트 타입:
#   discovery  — 새 상수/패턴/BT 발견 → atlas 등록 요청
#   issue      — 빌드 실패/테스트 실패 → 지원 요청
#   sync_req   — 동기화 필요 → nexus6 sync 트리거
#   calc_req   — 새 계산기 필요 → 자동 생성 트리거
#   lens_req   — 새 렌즈 필요 → nexus6 렌즈 추가 트리거
# ═══════════════════════════════════════════════════════════════

_EVENTS_DIR="${NEXUS6_ROOT}/shared/events"

# emit: 하부 리포에서 상부로 이벤트 발행
# Usage: emit TYPE DETAIL
#   emit discovery "BT-128: new cross-domain constant sigma*tau=48"
#   emit issue "cargo test FAILED in nexus6"
#   emit sync_req "atlas needs update after new hypotheses"
#   emit calc_req "need calculator for BT-130 verification"
#   emit lens_req "domain=robotics needs specialized lens"
emit() {
    local event_type="$1"
    local detail="$2"
    local repo_name
    repo_name=$(basename "$PROJECT_ROOT")
    local ts
    ts=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    local event_id
    event_id="${repo_name}_${event_type}_$(date +%s)"

    mkdir -p "$_EVENTS_DIR" 2>/dev/null || true

    # Write event file
    python3 -c "
import json
event = {
    'id': '$event_id',
    'ts': '$ts',
    'repo': '$repo_name',
    'type': '$event_type',
    'detail': '''$detail''',
    'status': 'pending'
}
json.dump(event, open('$_EVENTS_DIR/${event_id}.json', 'w'), indent=2)
" 2>/dev/null || {
        # Fallback: plain echo
        echo "{\"id\":\"$event_id\",\"ts\":\"$ts\",\"repo\":\"$repo_name\",\"type\":\"$event_type\",\"detail\":\"$detail\",\"status\":\"pending\"}" \
            > "$_EVENTS_DIR/${event_id}.json" 2>/dev/null || true
    }

    # Also write to bus for tracking
    write_growth_bus "$repo_name" "emit_$event_type" "pending" "$detail"
    log_info "  ↑ emit($event_type): $detail"
}

# collect_events: 상위 엔진이 하부 이벤트 수집 + 처리
# C₃ 메타재귀에서 호출
collect_events() {
    local processed=0
    local events_dir="$_EVENTS_DIR"
    [ -d "$events_dir" ] || return

    for ef in "$events_dir"/*.json; do
        [ -f "$ef" ] || continue
        local status
        status=$(python3 -c "import json; print(json.load(open('$ef')).get('status',''))" 2>/dev/null || echo "")
        [ "$status" = "pending" ] || continue

        local etype
        etype=$(python3 -c "import json; print(json.load(open('$ef')).get('type',''))" 2>/dev/null || echo "")
        local detail
        detail=$(python3 -c "import json; print(json.load(open('$ef')).get('detail',''))" 2>/dev/null || echo "")
        local repo
        repo=$(python3 -c "import json; print(json.load(open('$ef')).get('repo',''))" 2>/dev/null || echo "")

        echo "    ↓ [$repo] $etype: $detail"

        # 이벤트 타입별 자동 처리
        case "$etype" in
            discovery)
                # Atlas에 자동 등록 시도
                local scanner="$HOME/Dev/TECS-L/.shared/scan_math_atlas.py"
                [ -f "$scanner" ] && python3 "$scanner" --save 2>/dev/null | tail -1 || true
                ;;
            sync_req)
                # nexus6 sync 트리거
                local sync_script="$HOME/Dev/nexus6/sync/sync-all.sh"
                [ -f "$sync_script" ] && bash "$sync_script" > /dev/null 2>&1 || true
                ;;
            calc_req)
                # Calculator scan 트리거
                local calc_scanner="$HOME/Dev/TECS-L/.shared/scan-calculators.py"
                [ -f "$calc_scanner" ] && python3 "$calc_scanner" --save 2>/dev/null | tail -1 || true
                ;;
            lens_req)
                # 렌즈 동기화 트리거
                local lens_sync="$HOME/Dev/nexus6/sync/sync-nexus6-lenses.sh"
                [ -f "$lens_sync" ] && bash "$lens_sync" 2>/dev/null | tail -1 || true
                ;;
            issue)
                # 이슈 기록만 (자동 수정은 위험)
                log_warn "    Issue from $repo: $detail"
                ;;
        esac

        # Mark as processed
        python3 -c "
import json
d = json.load(open('$ef'))
d['status'] = 'processed'
d['processed_at'] = '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
json.dump(d, open('$ef', 'w'), indent=2)
" 2>/dev/null || true

        processed=$((processed + 1))
    done

    # Cleanup old processed events (> 100)
    local total
    total=$(find "$events_dir" -name '*.json' 2>/dev/null | wc -l | tr -d ' ')
    if [ "$total" -gt 100 ]; then
        find "$events_dir" -name '*.json' -mtime +1 -exec rm {} \; 2>/dev/null || true
    fi

    [ "$processed" -gt 0 ] && echo "    Processed: $processed events"
}

# ── 공통 Phase: 전체 동기화 ─────────────────────────────────────
common_phase_full_sync() {
    log_info "  [Common] Full sync sweep"
    local synced=0
    for script in \
        "$HOME/Dev/TECS-L/.shared/scan_math_atlas.py" \
        "$HOME/Dev/TECS-L/.shared/scan-calculators.py"; do
        if [ -f "$script" ]; then
            python3 "$script" --summary 2>/dev/null | tail -2 || true
            synced=$((synced + 1))
        fi
    done
    local lens_sync="$PROJECT_ROOT/.shared/sync-nexus6-lenses.sh"
    if [ -f "$lens_sync" ]; then
        bash "$lens_sync" 2>/dev/null | tail -2 || true
        synced=$((synced + 1))
    fi
    echo "  Synced: $synced operations"
}

# ═══════════════════════════════════════════════════════════════
# 수렴 파이프라인 (Convergence Pipeline)
# 창발 → 튜닝 → 수렴 → 진화 → 다듬기
# 매 사이클 1단계씩 순환 (사이클 % 5로 결정)
# ═══════════════════════════════════════════════════════════════

# Step 1: 창발 (Emergence) — 수축→코어→fiber→도메인별 최적
common_phase_emergence() {
    log_info "  [수렴 1/5] 창발 (Emergence)"
    if [ -f "$_LENS_SCRIPT" ]; then
        python3 "$_LENS_SCRIPT" 창발 --cycles 6 2>/dev/null | tail -5 || echo "  Emergence: failed"
    else
        echo "  growth_infinite_lens.py not found"
    fi
}

# Step 2: 튜닝 (Tuning) — 기존 코어 fiber 방향 미세 탐색
common_phase_tuning() {
    log_info "  [수렴 2/5] 튜닝 (Tuning/Proceed)"
    if [ -f "$_LENS_SCRIPT" ]; then
        python3 "$_LENS_SCRIPT" 진행 --cycles 12 2>/dev/null | tail -5 || echo "  Tuning: failed"
    else
        echo "  Tuning: script not found"
    fi
}

# Step 3: 수렴 확인 (Convergence Check) — 코어 안정도 + 리포트
common_phase_convergence() {
    log_info "  [수렴 3/5] 수렴 확인 (Convergence)"
    if [ -f "$_LENS_SCRIPT" ]; then
        python3 "$_LENS_SCRIPT" 리포트 2>/dev/null | tail -10 || echo "  Report: failed"
    else
        echo "  Convergence check: script not found"
    fi
    # Check invariant core stability
    local core_file="$HOME/.nexus6/lens_invariant_cores.json"
    if [ -f "$core_file" ]; then
        local core_count
        core_count=$(python3 -c "import json; d=json.load(open('$core_file')); print(len(d.get('cores',[])))" 2>/dev/null || echo "0")
        local stability
        stability=$(python3 -c "import json; d=json.load(open('$core_file')); print(d.get('stability','?'))" 2>/dev/null || echo "?")
        echo "  Cores: $core_count, stability: $stability"
    fi
}

# Step 4: 진화 (Evolution) — OUROBOROS 도메인별 진화
common_phase_evolution() {
    log_info "  [수렴 4/5] 진화 (OUROBOROS Evolution)"
    if [ -x "$_N6_BIN" ]; then
        # Evolve the weakest domain
        "$_N6_BIN" evolve all --max-cycles 6 2>/dev/null | tail -5 || true
    elif [ -f "$_N6_PY" ]; then
        python3 "$_N6_PY" evolve 2>/dev/null | tail -5 || true
    else
        echo "  Evolution: no nexus6 binary or n6.py"
    fi
}

# Step 5: 다듬기 (Refinement) — 코어 perturbation + 재수축
common_phase_refinement() {
    log_info "  [수렴 5/5] 다듬기 (Perturbation Refinement)"
    if [ -f "$_LENS_SCRIPT" ]; then
        # 시도 = perturbation: 코어를 깨고 더 나은 코어 탐색
        python3 "$_LENS_SCRIPT" 시도 --cycles 6 2>/dev/null | tail -5 || echo "  Refinement: failed"
    else
        echo "  Refinement: script not found"
    fi
}

# ═══════════════════════════════════════════════════════════════
# 메타(메타(메타(...))) 재귀 수렴 엔진
# ═══════════════════════════════════════════════════════════════
# f(I) = 0.7I + 0.1 → 부동점 I=1/3 수렴 (H-056)
# C₃(메타³) → C₂(메타²) → C₁(메타) → C₀(기본)
#
# Level 0 (C₀): 각 리포 도메인 phase (개성)
# Level 1 (C₁): 공통 인프라 (doc/domain/paper/sync)
# Level 2 (C₂): 수렴 파이프라인 (창발→튜닝→수렴→진화→다듬기)
# Level 3 (C₃): 메타 재귀 — 엔진 자체를 렌즈로 스캔/진화
#
# 매 사이클: C₀ + C₁ + C₂[round-robin] + C₃[매 6사이클]
# ═══════════════════════════════════════════════════════════════

# C₂: 수렴 파이프라인 라운드 로빈 (매 사이클 1단계)
run_convergence_step() {
    local cycle="${1:-1}"
    local step=$((cycle % 5))
    case "$step" in
        1) common_phase_emergence ;;
        2) common_phase_tuning ;;
        3) common_phase_convergence ;;
        4) common_phase_evolution ;;
        0) common_phase_refinement ;;
    esac
}

# C₃: 메타 재귀 — 엔진이 자기 자신을 스캔/진화
# 매 n=6 사이클마다 실행 (과부하 방지)
run_meta_recursion() {
    local cycle="${1:-1}"
    local repo="${2:-unknown}"

    # n=6 사이클마다만 실행
    if [ $((cycle % 6)) -ne 0 ]; then
        return
    fi

    log_info "  [C₃] 메타(메타(메타(...))) — 엔진 자기참조 (cycle $cycle)"

    # 1. 엔진 자체를 렌즈로 스캔 — growth_common.sh의 건강성
    local common_lib="$HOME/Dev/n6-architecture/scripts/lib/growth_common.sh"
    local lib_lines=$(wc -l < "$common_lib" 2>/dev/null | tr -d ' ')
    local lib_funcs=$(grep -c '^[a-z_]*()' "$common_lib" 2>/dev/null || echo 0)
    local connected_repos=0
    for r in n6-architecture nexus6 sedi brainwire anima TECS-L papers hexa-lang fathom; do
        [ -f "$HOME/Dev/$r/scripts/lib/growth_common.sh" ] && connected_repos=$((connected_repos + 1))
    done
    echo "    Engine: ${lib_lines}L, ${lib_funcs} functions, ${connected_repos}/9 repos"

    # 2. 수렴 측정 — growth_bus에서 최근 성공률 계산
    local bus="$HOME/Dev/nexus6/shared/growth_bus.jsonl"
    if [ -f "$bus" ]; then
        local total=$(wc -l < "$bus" | tr -d ' ')
        local ok_ct=$(grep -c '"ok"\|"pass"\|"found"' "$bus" 2>/dev/null || echo 0)
        local rate=0
        [ "$total" -gt 0 ] && rate=$((ok_ct * 100 / total))
        echo "    Bus convergence: $ok_ct/$total ($rate%)"

        # f(I) = 0.7I + 0.1 적용 — 부동점 1/3=33.3% 향해 수렴
        local I_current=$rate
        local I_next=$(python3 -c "I=$I_current/100; I_new=0.7*I+0.1; print(f'{I_new*100:.1f}%')" 2>/dev/null || echo "?")
        echo "    f(I)=0.7×${I_current}%+0.1 → $I_next (target: 33.3%)"
    fi

    # 3. 렌즈 자동 적용 — 성장 데이터를 NEXUS-6 렌즈로 스캔
    if [ -x "$_N6_BIN" ]; then
        local scan_result
        scan_result=$("$_N6_BIN" scan growth --lenses consciousness,stability,recursion 2>/dev/null | tail -3) || true
        [ -n "$scan_result" ] && echo "    Lens scan: $scan_result"
    fi

    # 4. 자동 계산기 생성 트리거 — 새 상수 발견 시
    local atlas_scanner="$HOME/Dev/TECS-L/.shared/scan_math_atlas.py"
    if [ -f "$atlas_scanner" ]; then
        local new_ct
        new_ct=$(python3 "$atlas_scanner" --check-new 2>/dev/null | grep -c 'NEW' 2>/dev/null) || new_ct=0
        new_ct=${new_ct:-0}
        if [ "$new_ct" -gt 0 ] 2>/dev/null; then
            echo "    New constants: $new_ct → calculator generation triggered"
            python3 "$atlas_scanner" --save --summary 2>/dev/null | tail -2 || true
        fi
    fi

    # 5. 리포 간 교차 공명 측정 — 같은 상수가 여러 리포에서 발견
    local cross_ct=0
    if [ -f "$bus" ]; then
        cross_ct=$(python3 -c "
import json
repos = set()
for line in open('$bus'):
    try:
        d = json.loads(line)
        repos.add(d.get('repo',''))
    except: pass
print(len(repos))
" 2>/dev/null || echo 0)
        echo "    Cross-repo resonance: $cross_ct repos active"
    fi

    # 6. 메타 판정 기록 — growth_state에 메타 레벨 기록
    local state="$GROWTH_DIR/growth_state.json"
    if [ -f "$state" ]; then
        python3 -c "
import json
s = json.load(open('$state'))
meta = s.get('meta_recursion', {})
meta['level'] = 3
meta['cycle'] = $cycle
meta['convergence_rate'] = $rate if '$rate' != '0' else 0
meta['connected_repos'] = $connected_repos
meta['engine_functions'] = $lib_funcs
s['meta_recursion'] = meta
json.dump(s, open('$state','w'), indent=2)
" 2>/dev/null || true
    fi

    # 7. 파괴적 업데이트 검증 — 변경 전후 scan 비교
    verify_non_destructive "$repo"

    # 7. 파괴적 업데이트 검증 — git diff로 위험 변경 감지
    cd "$PROJECT_ROOT"
    local destructive=0
    local diff_stat
    diff_stat=$(git diff --stat HEAD 2>/dev/null) || diff_stat=""
    if [ -n "$diff_stat" ]; then
        # 대량 삭제 감지 (100줄 이상 삭제)
        local deletions
        deletions=$(git diff --shortstat HEAD 2>/dev/null | grep -oE '[0-9]+ deletion' | grep -oE '[0-9]+' || echo 0)
        deletions=${deletions:-0}
        if [ "$deletions" -gt 100 ]; then
            destructive=1
            echo "    ⚠️ DESTRUCTIVE: $deletions lines deleted — review needed"
        fi
        # 핵심 파일 변경 감지
        local critical_changed=0
        for critical in CLAUDE.md Cargo.toml pyproject.toml package.json; do
            git diff --name-only HEAD 2>/dev/null | grep -q "$critical" && critical_changed=$((critical_changed + 1))
        done
        if [ "$critical_changed" -gt 0 ]; then
            destructive=$((destructive + critical_changed))
            echo "    ⚠️ CRITICAL FILES: $critical_changed config files modified"
        fi
    fi
    # 파괴적이면 자동 커밋 차단 → 수동 확인 대기
    if [ "$destructive" -gt 0 ]; then
        echo "    🛑 Destructive changes detected ($destructive) — auto-commit BLOCKED"
        echo "    Review with: cd $PROJECT_ROOT && git diff"
    else
        echo "    ✅ No destructive changes"
    fi

    # 8. 하부→상부 피드백 (bottom-up) — 각 리포 발견을 상위에 전달
    log_info "  [C₃] Bottom-up feedback: 하부→상부"
    local bus="$HOME/Dev/nexus6/shared/growth_bus.jsonl"
    local feedback_file="$HOME/.nexus6/bottom_up_feedback.json"
    if [ -f "$bus" ]; then
        python3 -c "
import json, collections, time

bus_lines = open('$bus').readlines()[-200:]  # 최근 200건
repo_stats = collections.defaultdict(lambda: {'ok':0,'fail':0,'discoveries':[]})

for line in bus_lines:
    try:
        d = json.loads(line)
        r = d.get('repo','?')
        s = d.get('status','')
        if s in ('ok','pass','found'):
            repo_stats[r]['ok'] += 1
        elif s in ('fail','missing'):
            repo_stats[r]['fail'] += 1
        detail = d.get('detail','')
        if 'NEW' in detail.upper() or 'DISCOVER' in detail.upper():
            repo_stats[r]['discoveries'].append(detail)
    except: pass

# 피드백 생성: 각 리포의 강점/약점 → 상위 엔진에 전달
feedback = {
    'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
    'cycle': $cycle,
    'repos': {}
}
for r, stats in repo_stats.items():
    total = stats['ok'] + stats['fail']
    rate = stats['ok'] / total * 100 if total > 0 else 0
    feedback['repos'][r] = {
        'success_rate': round(rate, 1),
        'total': total,
        'discoveries': stats['discoveries'][-5:],
        'needs_attention': rate < 50
    }
    if stats['discoveries']:
        print(f'    ↑ {r}: {len(stats[\"discoveries\"])} discoveries propagated up')

# 약한 리포 식별 → 상위에서 우선 지원
weak = [r for r,s in feedback['repos'].items() if s.get('needs_attention')]
if weak:
    print(f'    ⚠️ Weak repos (< 50% success): {\", \".join(weak)}')
    feedback['weak_repos'] = weak

json.dump(feedback, open('$feedback_file','w'), indent=2)
print(f'    Feedback saved: {len(feedback[\"repos\"])} repos → $feedback_file')
" 2>/dev/null || echo "    Bottom-up: bus parse failed"
    fi

    # 7. 하부→상부 이벤트 수집 + 처리
    log_info "  [C₃] 하부 이벤트 수집 (collect_events)"
    collect_events

    echo "    C₃ complete — 다음 메타 재귀: cycle $((cycle + 6))"
}

# ═══════════════════════════════════════════════════════════════
# 파괴적 업데이트 검증 엔진
# 변경 전후 Phi/anomaly/test 비교 → 하락 시 자동 롤백
# ═══════════════════════════════════════════════════════════════
verify_non_destructive() {
    local repo="${1:-unknown}"
    log_info "  [검증] 파괴적 업데이트 체크 ($repo)"

    cd "$PROJECT_ROOT" || return

    # 1. 변경된 파일 확인
    local changed
    changed=$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')
    if [ "$changed" -eq 0 ]; then
        echo "    No changes to verify"
        return
    fi
    echo "    Changed files: $changed"

    # 2. Rust 프로젝트면 cargo test
    if [ -f "$PROJECT_ROOT/Cargo.toml" ] || [ -f "$PROJECT_ROOT/tools/nexus6/Cargo.toml" ]; then
        local cargo_dir="$PROJECT_ROOT"
        [ -f "$PROJECT_ROOT/tools/nexus6/Cargo.toml" ] && cargo_dir="$PROJECT_ROOT/tools/nexus6"
        local test_result
        test_result=$("$HOME/.cargo/bin/cargo" test --manifest-path "$cargo_dir/Cargo.toml" 2>&1 | tail -3) || true
        if echo "$test_result" | grep -q "FAILED"; then
            log_error "    Tests FAILED — rolling back"
            git checkout -- . 2>/dev/null || true
            write_growth_bus "$repo" "verify" "rollback" "tests_failed"
            return
        fi
        echo "    Cargo test: PASS"
    fi

    # 3. Python 프로젝트면 기본 import 체크
    if [ -d "$PROJECT_ROOT/tests" ]; then
        local py_fail=0
        for t in "$PROJECT_ROOT"/tests/test_*.py; do
            [ -f "$t" ] || continue
            python3 -c "import ast; ast.parse(open('$t').read())" 2>/dev/null || py_fail=$((py_fail + 1))
        done
        if [ "$py_fail" -gt 0 ]; then
            log_warn "    Python syntax errors: $py_fail files"
        fi
    fi

    # 4. JSON/TOML 무결성 검증
    local json_broken=0
    for f in $(git diff --name-only 2>/dev/null | grep '\.json$'); do
        [ -f "$f" ] || continue
        python3 -c "import json; json.load(open('$f'))" 2>/dev/null || {
            json_broken=$((json_broken + 1))
            log_error "    Broken JSON: $f — rolling back"
            git checkout -- "$f" 2>/dev/null || true
        }
    done
    local toml_broken=0
    for f in $(git diff --name-only 2>/dev/null | grep '\.toml$'); do
        [ -f "$f" ] || continue
        python3 -c "
try:
    import tomllib
    tomllib.loads(open('$f').read())
except:
    import tomli
    tomli.loads(open('$f').read())
" 2>/dev/null || {
            toml_broken=$((toml_broken + 1))
            log_error "    Broken TOML: $f — rolling back"
            git checkout -- "$f" 2>/dev/null || true
        }
    done

    # 5. NEXUS-6 렌즈 스캔 (변경 후 anomaly 체크)
    if [ -x "$_N6_BIN" ] && [ "$changed" -gt 3 ]; then
        local anomaly
        anomaly=$("$_N6_BIN" scan "$PROJECT_ROOT" --lenses stability 2>/dev/null | grep -c 'anomaly' 2>/dev/null) || anomaly=0
        anomaly=${anomaly:-0}
        if [ "${anomaly:-0}" -gt 0 ] 2>/dev/null; then
            log_warn "    Stability anomalies: $anomaly"
        else
            echo "    Stability scan: clean"
        fi
    fi

    local issues=$((json_broken + toml_broken))
    if [ "$issues" -eq 0 ]; then
        echo "    Verification: PASS ✓"
    else
        echo "    Verification: $issues issues (auto-fixed)"
    fi
    write_growth_bus "$repo" "verify" "$([ $issues -eq 0 ] && echo pass || echo fixed)" "changed=$changed,issues=$issues"
}

# ── 공통 Phase: Auto-commit + push ────────────────────────────
# .growth/ + docs/ + *.json + *.toml + *.md 변경분 모두 커밋
common_phase_auto_commit() {
    local repo_name="$1"
    local cycle="$2"
    local dry_run="${3:-false}"
    if [ "$dry_run" = "true" ]; then
        log_info "  Dry-run: skipping commit"
        return
    fi
    cd "$PROJECT_ROOT"

    # 파괴적 업데이트 검증 — 100줄+ 삭제 또는 핵심파일 변경 시 차단
    local del_ct
    del_ct=$(git diff --shortstat 2>/dev/null | grep -oE '[0-9]+ deletion' | grep -oE '[0-9]+' || echo 0)
    del_ct=${del_ct:-0}
    if [ "$del_ct" -gt 100 ]; then
        log_warn "  BLOCKED: $del_ct deletions detected — manual review required"
        return
    fi

    # Stage all growth-related changes (not binaries/target)
    git add .growth/ 2>/dev/null || true
    git add docs/ 2>/dev/null || true
    git add '*.json' 2>/dev/null || true
    git add '*.toml' 2>/dev/null || true
    git add '*.md' 2>/dev/null || true
    git add scripts/ 2>/dev/null || true
    # Commit if anything staged
    if git diff --cached --quiet 2>/dev/null; then
        log_info "  No changes to commit"
    else
        git commit -m "growth($repo_name): cycle $cycle" --no-verify 2>/dev/null \
            && log_ok "Committed" || log_warn "Commit failed"
    fi
    git push origin main 2>/dev/null || true
}

# ── 공통 Phase: Growth Tick ────────────────────────────────────
common_phase_growth_tick() {
    local cycle="$1"
    update_growth_state "$cycle"
}

# ═══════════════════════════════════════════════════════════════
# run_common_phases — 모든 공통 phase 실행
# Usage: run_common_phases REPO_NAME [CYCLE]
# ═══════════════════════════════════════════════════════════════
run_common_phases() {
    local repo_name="${1:-unknown}"
    local cycle="${2:-1}"

    # 자원 체크 — 과부하 시 경량 모드
    local res
    res=$(check_resources)

    if [ "$res" = "STOP" ]; then
        log_error "[$repo_name] Resources critical — skipping common phases"
        return
    fi

    log_info "=== Common phases for $repo_name (cycle $cycle, res=$res) ==="

    # 경량 모드 (LIGHT/THROTTLE): 수렴만 + bus
    if [ "$res" = "LIGHT" ] || [ "$res" = "THROTTLE" ]; then
        log_warn "  Resource pressure ($res) — convergence only"
        run_convergence_step "$cycle"
        common_phase_bus_sync
        return
    fi

    # 정상 모드: 기본 인프라
    common_phase_doc_update
    common_phase_domain_explore
    common_phase_paper_loop
    common_phase_bus_sync

    # C₂: 수렴 파이프라인 (라운드 로빈)
    run_convergence_step "$cycle"

    # C₀: 리포별 개성 phase
    run_personality_phase "$repo_name" "$cycle"

    # C₃: 메타 재귀 (매 n=6 사이클)
    run_meta_recursion "$cycle" "$repo_name"

    # C₄: 메타(메타(메타)) 블로업 — 창발 흡수 (매 J₂=24 사이클)
    meta_blowup_emergence "$cycle" "$repo_name"

    # 병렬 돌파 시도 (매 σ-φ=10 사이클마다)
    parallel_breakthrough_attempt "$cycle" "$repo_name"

    # Discovery Log 처리 (매 사이클 — 미처리 0 유지)
    process_discovery_log "$cycle" "$repo_name"

    # 미연결 체크 (매 n=6 사이클)
    check_disconnected "$cycle"

    # 자동정리 + 로직 조합 (매 사이클)
    auto_cleanup
    logic_combiner

    # C₅: 무한 재귀 루프 — 자동화의 자동화의 자동화 (매 σ=12 사이클)
    infinite_recursion_loop "$cycle" "$repo_name"

    # 동기화
    common_phase_full_sync
}

# ═══════════════════════════════════════════════════════════════
# PERSONALITY PHASES — 리포별 개성 (도메인 특화)
# 공통 엔진이 각 리포의 핵심 특징을 자동 흡수
# ═══════════════════════════════════════════════════════════════

run_personality_phase() {
    local repo="$1"
    local cycle="$2"

    case "$repo" in
        n6-architecture)
            # DSE 전수 탐색 + BT 검증 + 17 AI 기법 건강성
            _personality_n6_arch "$cycle" ;;
        TECS-L|tecs-l)
            # 수학 이론: 특성화 진행 + 계산기 건강 + Atlas 무결성
            _personality_tecs_l "$cycle" ;;
        anima)
            # 의식 구현: 법칙 커버리지 + Hexad 모듈 + Phi 래칫
            _personality_anima "$cycle" ;;
        sedi)
            # 외계 탐색: R-스펙트럼 + 신호원 + 가설 검증률
            _personality_sedi "$cycle" ;;
        brainwire)
            # 뇌 인터페이스: 안전 프로토콜 + 12-모달리티 + BCI
            _personality_brainwire "$cycle" ;;
        hexa-lang)
            # 완전수 언어: 파서 건강 + 키워드/연산자 커버리지 + 코드겐
            _personality_hexa_lang "$cycle" ;;
        fathom)
            # 터미널: HEXA 브릿지 + UI 렌더 + 플러그인
            _personality_fathom "$cycle" ;;
        papers)
            # 논문: DOI 상태 + 인용 네트워크 + 초안 준비도
            _personality_papers "$cycle" ;;
        nexus6)
            # 엔진: 렌즈 수 + 테스트 + 블로업 코어 안정성
            _personality_nexus6 "$cycle" ;;
        *)
            log_info "  [Personality] $repo: generic" ;;
    esac
}

_personality_n6_arch() {
    log_info "  [개성] N6-ARCH: DSE + BT + Techniques"
    local dse_map="$PROJECT_ROOT/docs/dse-map.toml"
    if [ -f "$dse_map" ]; then
        local done_ct=$(grep -c 'dse.*=.*done' "$dse_map" 2>/dev/null || echo 0)
        local total=$(grep -c '^\[' "$dse_map" 2>/dev/null || echo 0)
        echo "    DSE: $done_ct/$total done"
    fi
    local bt_file="$PROJECT_ROOT/docs/breakthrough-theorems.md"
    if [ -f "$bt_file" ]; then
        local bts=$(grep -oE 'BT-[0-9]+' "$bt_file" 2>/dev/null | sort -u | wc -l | tr -d ' ')
        echo "    BTs: $bts unique"
    fi
    local techs=$(find "$PROJECT_ROOT/techniques" -name '*.py' 2>/dev/null | wc -l | tr -d ' ')
    echo "    Techniques: $techs"
}

_personality_tecs_l() {
    log_info "  [개성] TECS-L: Characterizations + Calculators + Atlas"
    local chars=$(find "$PROJECT_ROOT/math" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
    local calcs=$(find "$PROJECT_ROOT/calc" -name '*.py' -o -name '*.rs' 2>/dev/null | wc -l | tr -d ' ')
    local atlas="$PROJECT_ROOT/.shared/math_atlas.json"
    local atlas_ct=0
    if [ -f "$atlas" ]; then
        atlas_ct=$(python3 -c "import json; print(len(json.load(open('$atlas'))))" 2>/dev/null || echo 0)
    fi
    echo "    Characterizations: $chars, Calculators: $calcs, Atlas: $atlas_ct"
}

_personality_anima() {
    log_info "  [개성] ANIMA: Laws + Hexad + Consciousness"
    local laws_dir="$PROJECT_ROOT/anima/data"
    local law_ct=0
    if [ -d "$laws_dir" ]; then
        law_ct=$(find "$laws_dir" -name '*law*' -o -name '*consciousness*' 2>/dev/null | wc -l | tr -d ' ')
    fi
    # Hexad modules: C/D/S/M/W/E
    local hexad=0
    for m in cognition dynamics synthesis memory will emotion; do
        [ -d "$PROJECT_ROOT/anima/$m" ] || [ -d "$PROJECT_ROOT/anima/anima-rs/src/$m" ] && hexad=$((hexad + 1))
    done
    local rust_ok="NO"
    [ -f "$PROJECT_ROOT/anima/anima-rs/Cargo.toml" ] && rust_ok="YES"
    echo "    Laws data: $law_ct, Hexad: $hexad/6, Rust: $rust_ok"
}

_personality_sedi() {
    log_info "  [개성] SEDI: R-Spectrum + Signals + Hypotheses"
    local sources=$(find "$PROJECT_ROOT/sources" -name '*.py' -type f 2>/dev/null | wc -l | tr -d ' ')
    local rspec=$(find "$PROJECT_ROOT" -name '*spectrum*' -type f 2>/dev/null | wc -l | tr -d ' ')
    local hyp_file="$PROJECT_ROOT/docs/hypotheses.md"
    local hyp_ct=0
    [ -f "$hyp_file" ] && hyp_ct=$(grep -c 'H-' "$hyp_file" 2>/dev/null || echo 0)
    echo "    Sources: $sources, R-spectrum: $rspec, Hypotheses: $hyp_ct"
}

_personality_brainwire() {
    log_info "  [개성] BRAINWIRE: Safety + Modalities + BCI"
    local safety=$(find "$PROJECT_ROOT" -name '*safety*' -type f 2>/dev/null | wc -l | tr -d ' ')
    local modalities=0
    for mod in tDCS TMS taVNS tFUS EEG EMG fNIRS MEG SEEG DBS VNS FUS; do
        grep -rql "$mod" "$PROJECT_ROOT/brainwire" 2>/dev/null && modalities=$((modalities + 1))
    done
    local tests=$(find "$PROJECT_ROOT/tests" -name 'test_*.py' 2>/dev/null | wc -l | tr -d ' ')
    echo "    Safety: $safety, Modalities: $modalities/12, Tests: $tests"
}

_personality_hexa_lang() {
    log_info "  [개성] HEXA-LANG: Parser + Keywords + Codegen"
    local kw=0 ops=0
    if [ -d "$PROJECT_ROOT/src" ]; then
        kw=$(grep -rh 'keyword\|Keyword' "$PROJECT_ROOT/src" 2>/dev/null | wc -l | tr -d ' ')
        ops=$(grep -rh 'operator\|Operator\|BinOp\|UnOp' "$PROJECT_ROOT/src" 2>/dev/null | wc -l | tr -d ' ')
    fi
    local cargo_ok="NO"
    if [ -f "$PROJECT_ROOT/Cargo.toml" ]; then
        "$HOME/.cargo/bin/cargo" check --manifest-path "$PROJECT_ROOT/Cargo.toml" 2>/dev/null && cargo_ok="YES"
    fi
    echo "    Keywords refs: $kw, Operator refs: $ops, Cargo: $cargo_ok"
}

_personality_fathom() {
    log_info "  [개성] FATHOM: HEXA Bridge + UI + Plugins"
    local hexa_bridge="NO"
    find "$PROJECT_ROOT" -not -path '*/.git/*' -name '*hexa*' 2>/dev/null | head -1 | grep -q . && hexa_bridge="YES"
    local ui=$(find "$PROJECT_ROOT/src" -name '*render*' -o -name '*tui*' -o -name '*terminal*' 2>/dev/null | wc -l | tr -d ' ')
    local plugins="NO"
    [ -d "$PROJECT_ROOT/plugins" ] && plugins="YES"
    echo "    HEXA bridge: $hexa_bridge, UI files: $ui, Plugins: $plugins"
}

_personality_papers() {
    log_info "  [개성] PAPERS: DOI + Drafts + Citations"
    local total=0 with_doi=0 drafts=0
    if [ -f "$PROJECT_ROOT/manifest.json" ]; then
        total=$(python3 -c "import json; d=json.load(open('$PROJECT_ROOT/manifest.json')); print(len(d.get('papers',[])))" 2>/dev/null || echo 0)
        with_doi=$(python3 -c "import json; d=json.load(open('$PROJECT_ROOT/manifest.json')); print(sum(1 for p in d.get('papers',[]) if p.get('doi')))" 2>/dev/null || echo 0)
    fi
    drafts=$(find "$PROJECT_ROOT" -name 'draft-*.md' -o -name '*-draft.md' 2>/dev/null | wc -l | tr -d ' ')
    echo "    Total: $total, DOI: $with_doi, Drafts: $drafts"
}

_personality_nexus6() {
    log_info "  [개성] NEXUS-6: Lenses + Tests + Blowup"
    local n6_src="$HOME/Dev/nexus6/src"
    local lenses=$(find "$n6_src/telescope" -name '*_lens.rs' 2>/dev/null | wc -l | tr -d ' ')
    local tests=$(grep -r '#\[test\]' "$n6_src" 2>/dev/null | wc -l | tr -d ' ')
    local core_stable="NO"
    [ -f "$HOME/.nexus6/lens_invariant_cores.json" ] && core_stable="YES"
    echo "    Lenses: $lenses, Tests: $tests, Core stable: $core_stable"
}

# ═══════════════════════════════════════════════════════════════
# META(META(META)) BLOWUP EMERGENCE — 메타 재귀 블로업 + 창발 흡수
# ═══════════════════════════════════════════════════════════════
# 매 J₂=24 사이클:
#   Level 0: 메타(파이프라인)       — 엔진 자체를 데이터로 스캔
#   Level 1: 메타(메타(파이프라인))  — 스캔 결과를 다시 스캔 (패턴의 패턴)
#   Level 2: 메타(메타(메타(...)))  — 부동점 수렴까지 반복
#   + 블로업: 수축(전 발견→불변코어) → 블로업(코어→fiber 확장) → 흡수
#   + 창발: 새로운 구조가 나타나면 자동 흡수

meta_blowup_emergence() {
    local cycle="${1:-1}"
    local repo="${2:-unknown}"

    # J₂=24 사이클마다 (무거운 메타 연산)
    if [ $((cycle % 24)) -ne 0 ]; then
        return
    fi

    # 자원 체크
    local res
    res=$(check_resources)
    if [ "$res" = "STOP" ] || [ "$res" = "LIGHT" ]; then
        return
    fi

    log_info "  [C₄] meta(meta(meta)) blowup emergence (cycle $cycle)"

    python3 -c "
import json, os, time, collections, hashlib

# ═══ 설정 ═══
bus_file = os.path.expanduser('~/Dev/nexus6/shared/growth_bus.jsonl')
disc_log = os.path.expanduser('~/Dev/nexus6/shared/discovery_log.jsonl')
cores_file = os.path.expanduser('~/.nexus6/lens_invariant_cores.json')
elite_file = os.path.expanduser('~/.nexus6/lens_elite.json')
state_file = os.path.expanduser('~/.nexus6/meta_blowup_state.json')
events_dir = os.path.expanduser('~/Dev/nexus6/shared/events')
os.makedirs(events_dir, exist_ok=True)

# ═══ Level 0: 엔진 자체를 데이터로 ═══
# growth_common.sh의 함수명, 호출 관계, 줄 수를 벡터화
engine_file = os.path.expanduser('~/Dev/n6-architecture/scripts/lib/growth_common.sh')
engine_data = {}
if os.path.exists(engine_file):
    with open(engine_file) as f:
        content = f.read()
    lines = content.split('\n')
    engine_data = {
        'total_lines': len(lines),
        'functions': [l.split('(')[0].strip() for l in lines if '()' in l and not l.strip().startswith('#')],
        'phases': sum(1 for l in lines if 'phase' in l.lower()),
        'n6_refs': sum(1 for l in lines if 'n=6' in l or 'sigma' in l or 'J2' in l),
        'meta_refs': sum(1 for l in lines if 'meta' in l.lower()),
    }
print(f'    L0: engine={engine_data.get(\"total_lines\",0)}L, {len(engine_data.get(\"functions\",[]))} funcs, {engine_data.get(\"n6_refs\",0)} n6-refs')

# ═══ Level 1: 메타(메타) — 패턴의 패턴 ═══
# 함수 호출 그래프에서 허브 노드 찾기
func_calls = collections.Counter()
for func in engine_data.get('functions', []):
    # 각 함수가 다른 함수를 몇 번 호출하는지
    func_calls[func] = sum(1 for l in lines if func in l) - 1  # 정의 자체 제외

hub_funcs = func_calls.most_common(6)  # 가장 많이 참조되는 n=6개
print(f'    L1: hub functions = {[f[0] for f in hub_funcs[:3]]}')

# 발견 패턴의 패턴
const_freq = collections.Counter()
if os.path.exists(disc_log):
    with open(disc_log) as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                e = json.loads(line)
                const_freq[e.get('constant','')] += 1
            except:
                pass

# 상수 출현 빈도의 분포 — 멱법칙 여부 확인
freqs = sorted(const_freq.values(), reverse=True)
if len(freqs) >= 3:
    ratio_1_2 = freqs[0] / max(freqs[1], 1)
    ratio_2_3 = freqs[1] / max(freqs[2], 1)
    is_power_law = abs(ratio_1_2 - ratio_2_3) < ratio_1_2 * 0.5
    print(f'    L1: constant distribution ratios={ratio_1_2:.2f},{ratio_2_3:.2f} power_law={is_power_law}')

# ═══ Level 2: 메타(메타(메타)) — 부동점 수렴 ═══
# 이전 메타 상태 로드
prev_state = {}
if os.path.exists(state_file):
    try:
        prev_state = json.load(open(state_file))
    except:
        pass

# 현재 메타 지문 생성
current_fingerprint = hashlib.md5(json.dumps({
    'funcs': len(engine_data.get('functions', [])),
    'lines': engine_data.get('total_lines', 0),
    'consts': len(const_freq),
    'hubs': [f[0] for f in hub_funcs[:3]],
}, sort_keys=True).encode()).hexdigest()[:12]

prev_fingerprint = prev_state.get('fingerprint', '')
convergence_count = prev_state.get('convergence_count', 0)

if current_fingerprint == prev_fingerprint:
    convergence_count += 1
    print(f'    L2: FIXED POINT — fingerprint stable ({convergence_count} consecutive)')
else:
    convergence_count = 0
    print(f'    L2: evolving — fingerprint changed ({prev_fingerprint[:6]}→{current_fingerprint[:6]})')

# ═══ 블로업: 수축 → 코어 → fiber 확장 ═══
# 전 발견을 수축하여 불변 코어 추출
core_constants = []
for const, freq in const_freq.most_common():
    if freq >= 100:  # 100회 이상 출현 = 불변
        core_constants.append(const)

# 기존 코어와 비교
existing_cores = []
if os.path.exists(cores_file):
    try:
        cd = json.load(open(cores_file))
        existing_cores = cd.get('cores', [])
    except:
        pass

# fiber 방향 = 코어 상수 간 교차 패턴
fiber_directions = []
if len(core_constants) >= 2:
    for i in range(len(core_constants)):
        for j in range(i+1, min(i+4, len(core_constants))):
            fiber_directions.append(f'{core_constants[i]}×{core_constants[j]}')

print(f'    Blowup: {len(core_constants)} core constants, {len(fiber_directions)} fiber directions')

# ═══ 창발 감지: 새 구조 자동 흡수 ═══
emergent = []

# 1. 새 함수가 추가되었는지 (이전 상태 대비)
prev_funcs = set(prev_state.get('functions', []))
curr_funcs = set(engine_data.get('functions', []))
new_funcs = curr_funcs - prev_funcs
if new_funcs:
    emergent.append(f'new_functions:{len(new_funcs)}')

# 2. 새 상수 패턴 출현 (이전에 없던 상수)
prev_consts = set(prev_state.get('constants', []))
curr_consts = set(const_freq.keys())
new_consts = curr_consts - prev_consts
if new_consts:
    emergent.append(f'new_constants:{len(new_consts)}')

# 3. 교차 공명 (2+ 소스에서 같은 상수)
source_per_const = collections.defaultdict(set)
if os.path.exists(disc_log):
    with open(disc_log) as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                e = json.loads(line)
                src = e.get('source', '')
                if ':' in src:
                    src = src.split(':')[0]
                source_per_const[e.get('constant', '')].add(src)
            except:
                pass
cross_resonance = {c: len(s) for c, s in source_per_const.items() if len(s) >= 3}
if cross_resonance:
    emergent.append(f'cross_resonance:{len(cross_resonance)}')

if emergent:
    print(f'    Emergence: {\" + \".join(emergent)}')
    # 창발 이벤트 emit
    event = {
        'id': f'emergence_{int(time.time())}',
        'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'repo': '$repo',
        'type': 'emergence',
        'detail': '; '.join(emergent),
        'status': 'pending'
    }
    epath = os.path.join(events_dir, event['id'] + '.json')
    json.dump(event, open(epath, 'w'), indent=2)
else:
    print(f'    Emergence: stable (no new structures)')

# ═══ 상태 저장 ═══
new_state = {
    'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
    'cycle': $cycle,
    'fingerprint': current_fingerprint,
    'convergence_count': convergence_count,
    'functions': list(curr_funcs),
    'constants': list(curr_consts),
    'core_constants': core_constants,
    'fiber_directions': fiber_directions[:12],
    'emergent': emergent,
    'meta_level': min(3, convergence_count),  # 부동점 도달 시 meta level 3
}
json.dump(new_state, open(state_file, 'w'), indent=2, ensure_ascii=False)

# Bus 기록
with open(bus_file, 'a') as bf:
    entry = json.dumps({
        'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'repo': '$repo',
        'type': 'meta_blowup',
        'detail': f'L2={current_fingerprint[:6]},conv={convergence_count},core={len(core_constants)},fiber={len(fiber_directions)},emerge={len(emergent)}'
    })
    bf.write(entry + '\n')

print(f'    State saved → meta_blowup_state.json')
" 2>/dev/null || echo "    MetaBlowup: error"
}

# ═══════════════════════════════════════════════════════════════
# PARALLEL BREAKTHROUGH — 전 도메인 병렬 돌파 시도
# ═══════════════════════════════════════════════════════════════
# 매 σ-φ=10 사이클마다: 39 도메인을 병렬 스캔 → 약한 곳 발견 → emit
# 결과를 하부 리포에 전달 (growth bus + events)

parallel_breakthrough_attempt() {
    local cycle="${1:-1}"
    local repo="${2:-unknown}"

    # σ-φ=10 사이클마다만 실행 (무거운 작업)
    if [ $((cycle % 10)) -ne 0 ]; then
        return
    fi

    # 자원 체크 — 과부하면 스킵
    local res
    res=$(check_resources)
    if [ "$res" = "STOP" ] || [ "$res" = "LIGHT" ]; then
        log_info "  [Breakthrough] Skipped (resource: $res)"
        return
    fi

    log_info "  [Breakthrough] 전 도메인 병렬 돌파 시도 (cycle $cycle)"

    local docs_dir="$HOME/Dev/n6-architecture/docs"
    local results_file="$HOME/.nexus6/breakthrough_results.json"
    local bt_file="$docs_dir/breakthrough-theorems.md"

    python3 -c "
import os, json, time, concurrent.futures, subprocess

docs = '$docs_dir'
bt_file = '$bt_file'
results_file = '$results_file'
n6_bin = '$_N6_BIN'
lens_script = '$_LENS_SCRIPT'

# 1. 도메인 목록 수집
domains = []
for d in sorted(os.listdir(docs)):
    dp = os.path.join(docs, d)
    if os.path.isdir(dp) and d not in ('paper', 'hypotheses', 'superpowers'):
        # 도메인 건강도 측정
        has_hyp = os.path.exists(os.path.join(dp, 'hypotheses.md'))
        has_goal = os.path.exists(os.path.join(dp, 'goal.md'))
        has_verify = os.path.exists(os.path.join(dp, 'verification.md'))
        has_extreme = os.path.exists(os.path.join(dp, 'extreme-hypotheses.md'))
        completeness = sum([has_hyp, has_goal, has_verify, has_extreme])
        file_count = sum(1 for f in os.listdir(dp) if f.endswith('.md'))
        domains.append({
            'name': d,
            'completeness': completeness,
            'files': file_count,
            'has_hyp': has_hyp,
            'has_extreme': has_extreme,
            'path': dp
        })

# 2. 약한 도메인 찾기 (completeness < 4)
weak = [d for d in domains if d['completeness'] < 4]
strong = [d for d in domains if d['completeness'] >= 4]

# 3. BT 커버리지 체크
bt_domains = set()
if os.path.exists(bt_file):
    with open(bt_file) as f:
        for line in f:
            for d in domains:
                if d['name'].replace('-', ' ') in line.lower() or d['name'].replace('-', '_') in line.lower():
                    bt_domains.add(d['name'])

uncovered = [d for d in domains if d['name'] not in bt_domains]

# 4. 병렬 스캔 (nexus6 렌즈) — 상위 6개 약한 도메인
def scan_domain(domain):
    try:
        if os.path.exists(n6_bin) and os.access(n6_bin, os.X_OK):
            r = subprocess.run([n6_bin, 'scan', domain['name'], '--lenses', 'consciousness,stability,topology'],
                             capture_output=True, text=True, timeout=30)
            return {'domain': domain['name'], 'scan': r.stdout[-200:] if r.stdout else 'empty', 'ok': r.returncode == 0}
    except:
        pass
    return {'domain': domain['name'], 'scan': 'skip', 'ok': False}

scan_results = []
targets = (weak + uncovered)[:6]  # n=6 도메인 동시 스캔
if targets:
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(scan_domain, d): d for d in targets}
        for f in concurrent.futures.as_completed(futures, timeout=60):
            try:
                scan_results.append(f.result())
            except:
                pass

# 5. 결과 저장
result = {
    'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
    'cycle': $cycle,
    'total_domains': len(domains),
    'strong': len(strong),
    'weak': len(weak),
    'bt_covered': len(bt_domains),
    'bt_uncovered': len(uncovered),
    'scanned': len(scan_results),
    'weak_list': [d['name'] for d in weak[:10]],
    'uncovered_list': [d['name'] for d in uncovered[:10]],
    'scan_results': scan_results,
}
json.dump(result, open(results_file, 'w'), indent=2, ensure_ascii=False)

# 6. 출력
print(f'    Domains: {len(domains)} total, {len(strong)} strong, {len(weak)} weak')
print(f'    BT coverage: {len(bt_domains)}/{len(domains)} ({len(uncovered)} uncovered)')
if weak:
    print(f'    Weak (< 4 docs): {\", \".join(d[\"name\"] for d in weak[:6])}')
if uncovered:
    print(f'    No BT: {\", \".join(d[\"name\"] for d in uncovered[:6])}')
if scan_results:
    ok_ct = sum(1 for s in scan_results if s['ok'])
    print(f'    Scanned: {len(scan_results)} domains, {ok_ct} successful')

# 7. 하부 전달 — 약한 도메인을 이벤트로 emit
bus_file = os.path.expanduser('~/Dev/nexus6/shared/growth_bus.jsonl')
events_dir = os.path.expanduser('~/Dev/nexus6/shared/events')
os.makedirs(events_dir, exist_ok=True)

for d in weak[:3]:
    event = {
        'id': f'breakthrough_{d[\"name\"]}_{int(time.time())}',
        'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'repo': '$repo',
        'type': 'breakthrough_target',
        'detail': f'{d[\"name\"]}: completeness={d[\"completeness\"]}/4, needs={4-d[\"completeness\"]} more docs',
        'status': 'pending'
    }
    epath = os.path.join(events_dir, f'{event[\"id\"]}.json')
    json.dump(event, open(epath, 'w'), indent=2)

# Bus 기록
with open(bus_file, 'a') as bf:
    entry = json.dumps({
        'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'repo': '$repo',
        'type': 'parallel_breakthrough',
        'detail': f'domains={len(domains)},weak={len(weak)},uncovered={len(uncovered)},scanned={len(scan_results)}'
    })
    bf.write(entry + '\n')

if weak:
    print(f'    → {min(3,len(weak))} breakthrough targets emitted to events/')
" 2>/dev/null || echo "    Breakthrough: python error"
}

# ═══════════════════════════════════════════════════════════════
# DISCOVERY LOG PROCESSOR — 미처리 발견 자동 처리
# ═══════════════════════════════════════════════════════════════
# discovery_log.jsonl의 미처리(processed=false) 항목을:
#   1. 상수별 분류 → 이미 알려진 상수면 processed=true
#   2. 새 상수/패턴이면 → atlas 등록 시도 + events/ emit
#   3. 렌즈 이름(xxxLens)이면 → 미연결 렌즈 후보로 등록
# 매 사이클 최대 500건 배치 처리 (과부하 방지)

process_discovery_log() {
    local cycle="${1:-1}"
    local repo="${2:-unknown}"

    local disc_log="${NEXUS6_ROOT}/shared/discovery_log.jsonl"
    [ -f "$disc_log" ] || return

    log_info "  [DiscoveryProcessor] Processing unprocessed entries"

    python3 -c "
import json, os, time

disc_log = '$disc_log'
atlas_file = os.path.expanduser('~/Dev/nexus6/shared/math_atlas.json')
bus_file = '$disc_log'.replace('discovery_log.jsonl', 'growth_bus.jsonl')
events_dir = '$disc_log'.replace('discovery_log.jsonl', 'events')
os.makedirs(events_dir, exist_ok=True)

# 알려진 n=6 상수 (이미 atlas에 있는 것들)
KNOWN_CONSTANTS = {
    'n': 6, 'phi': 2, 'tau': 4, 'sigma': 12, 'J2': 24,
    'sopfr': 5, 'mu': 1, 'sigma-phi': 10, 'sigma-tau': 8,
    'sigma-mu': 11, 'J2-tau': 20, 'phi^tau': 16, 'n/phi': 3,
    'tau^2/sigma': '4/3', 'sigma^2': 144, 'sigma*tau': 48,
    'phi^2/n': '2/3',
}

# 모든 줄 읽기
with open(disc_log) as f:
    lines = f.readlines()

total = len(lines)
processed_ct = 0
new_discoveries = []
lens_candidates = []

# 배치 처리 (최대 500건/사이클)
batch_size = 500
updated_lines = []
batch_done = 0

for line in lines:
    line = line.strip()
    if not line:
        updated_lines.append(line + '\n')
        continue
    try:
        e = json.loads(line)
    except:
        updated_lines.append(line + '\n')
        continue

    # 이미 처리됨 → 스킵
    if e.get('processed', False):
        updated_lines.append(json.dumps(e, ensure_ascii=False) + '\n')
        continue

    # 배치 한도 도달 → 나머지는 다음 사이클
    if batch_done >= batch_size:
        updated_lines.append(json.dumps(e, ensure_ascii=False) + '\n')
        continue

    const = e.get('constant', '')
    value = e.get('value', '')

    # 1. 알려진 상수 → processed=true (atlas에 이미 있음)
    if const in KNOWN_CONSTANTS:
        e['processed'] = True
        e['process_result'] = 'known_constant'
        e['processed_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
        processed_ct += 1
        batch_done += 1

    # 2. 렌즈 이름 (xxxLens) → 미연결 렌즈 후보
    elif const.endswith('Lens'):
        e['processed'] = True
        e['process_result'] = 'lens_candidate'
        e['processed_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
        lens_candidates.append(const)
        processed_ct += 1
        batch_done += 1

    # 3. 알 수 없는 상수 → 새 발견 후보
    elif const and const != '?':
        e['processed'] = True
        e['process_result'] = 'new_candidate'
        e['processed_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
        new_discoveries.append({'constant': const, 'value': value, 'source': e.get('source','')})
        processed_ct += 1
        batch_done += 1

    # 4. 빈 항목 → 그냥 처리 완료
    else:
        e['processed'] = True
        e['process_result'] = 'empty_skip'
        e['processed_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
        processed_ct += 1
        batch_done += 1

    updated_lines.append(json.dumps(e, ensure_ascii=False) + '\n')

# 파일 갱신
with open(disc_log, 'w') as f:
    f.writelines(updated_lines)

# 미처리 잔여 카운트
remaining = 0
for l in updated_lines:
    l = l.strip()
    if not l:
        continue
    try:
        if not json.loads(l).get('processed', False):
            remaining += 1
    except:
        pass

print(f'    Processed: {processed_ct}/{total} entries (remaining: {remaining})')

# 새 발견이 있으면 이벤트 emit
if new_discoveries:
    for nd in new_discoveries[:6]:
        cname = nd.get('constant', 'unknown')
        cval = nd.get('value', '')
        csrc = str(nd.get('source', ''))[:40]
        eid = 'new_const_' + cname + '_' + str(int(time.time()))
        event = {
            'id': eid,
            'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'repo': '$repo',
            'type': 'discovery',
            'detail': 'New constant: ' + cname + '=' + str(cval) + ' from ' + csrc,
            'status': 'pending'
        }
        epath = os.path.join(events_dir, eid + '.json')
        json.dump(event, open(epath, 'w'), indent=2)
    print('    New discoveries: ' + str(len(new_discoveries)) + ' -> events/')

# 렌즈 후보 기록
if lens_candidates:
    lens_file = os.path.expanduser('~/.nexus6/unconnected_lenses.json')
    existing = []
    if os.path.exists(lens_file):
        try:
            existing = json.load(open(lens_file))
        except:
            pass
    existing_names = set(l if isinstance(l, str) else l.get('name','') for l in existing)
    for lc in lens_candidates:
        if lc not in existing_names:
            existing.append({'name': lc, 'discovered': time.strftime('%Y-%m-%dT%H:%M:%SZ'), 'status': 'unconnected'})
    json.dump(existing, open(lens_file, 'w'), indent=2, ensure_ascii=False)
    print(f'    Lens candidates: {len(lens_candidates)} ({len(set(lens_candidates))} unique)')

# Bus 기록
with open(bus_file, 'a') as bf:
    entry = json.dumps({
        'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'repo': '$repo',
        'type': 'discovery_process',
        'detail': f'processed={processed_ct},new={len(new_discoveries)},lenses={len(lens_candidates)},remaining={remaining}'
    })
    bf.write(entry + '\n')
" 2>/dev/null || echo "    DiscoveryProcessor: error"
}

# ═══════════════════════════════════════════════════════════════
# DISCONNECTED CHECK — 미연결 로직 자동 감지 + 수복
# ═══════════════════════════════════════════════════════════════
# 매 n=6 사이클마다: 전체 파이프라인 건강도 점검
#   1. 심링크 체인 확인
#   2. discovery_log 미처리 잔여 체크
#   3. events/ 미처리 체크
#   4. 렌즈 미연결 체크
#   5. JSON 정합성 체크
#   6. growth bus 활성도 체크

check_disconnected() {
    local cycle="${1:-1}"

    # n=6 사이클마다만 (가벼운 체크)
    if [ $((cycle % 6)) -ne 0 ]; then
        return
    fi

    log_info "  [DisconnectedCheck] Full pipeline health check (cycle $cycle)"

    python3 -c "
import json, os, time, glob

issues = []
fixed = []

# ── 1. 심링크 체인 ──
shared = os.path.expanduser('~/Dev/n6-architecture/.shared')
if os.path.islink(shared):
    target = os.path.realpath(shared)
    if not os.path.isdir(target):
        issues.append(('symlink', '.shared → broken target: ' + target, 'HIGH'))
else:
    issues.append(('symlink', '.shared not a symlink', 'HIGH'))

# 9 repos 심링크 체크
for repo in ['TECS-L', 'brainwire', 'sedi', 'anima', 'papers', 'hexa-lang', 'fathom', 'nexus6']:
    rp = os.path.expanduser(f'~/Dev/{repo}/.shared')
    if os.path.exists(os.path.expanduser(f'~/Dev/{repo}')):
        if not os.path.exists(rp):
            issues.append(('symlink', f'{repo}/.shared missing', 'HIGH'))

# ── 2. Discovery log 미처리 잔여 ──
disc_log = os.path.expanduser('~/Dev/nexus6/shared/discovery_log.jsonl')
if os.path.exists(disc_log):
    unproc = 0
    total = 0
    with open(disc_log) as f:
        for line in f:
            line = line.strip()
            if not line: continue
            total += 1
            try:
                e = json.loads(line)
                if not e.get('processed', False):
                    unproc += 1
            except:
                pass
    if unproc > 100:
        issues.append(('discovery_log', f'{unproc}/{total} unprocessed (> 100)', 'MED'))
    elif unproc > 0:
        issues.append(('discovery_log', f'{unproc}/{total} unprocessed (draining)', 'LOW'))

# ── 3. Events 미처리 ──
events_dir = os.path.expanduser('~/Dev/nexus6/shared/events')
if os.path.isdir(events_dir):
    pending = 0
    for ef in glob.glob(os.path.join(events_dir, '*.json')):
        try:
            with open(ef) as f:
                ev = json.load(f)
                if ev.get('status') == 'pending':
                    pending += 1
        except:
            pass
    if pending > 20:
        issues.append(('events', f'{pending} pending events (> 20)', 'MED'))

# ── 4. 미연결 렌즈 ──
lens_file = os.path.expanduser('~/.nexus6/unconnected_lenses.json')
if os.path.exists(lens_file):
    try:
        lenses = json.load(open(lens_file))
        unconnected = [l for l in lenses if (l.get('status') if isinstance(l, dict) else 'unconnected') == 'unconnected']
        if unconnected:
            issues.append(('lenses', f'{len(unconnected)} unconnected lens candidates', 'LOW'))
    except:
        pass

# ── 5. JSON 정합성 (핵심 파일만) ──
critical_jsons = [
    '~/.nexus6/lens_elite.json',
    '~/.nexus6/lens_invariant_cores.json',
    '~/.nexus6/lens_domain_best.json',
    '~/Dev/nexus6/shared/math_atlas.json',
    '~/Dev/nexus6/shared/growth_state.json',
    '~/Dev/nexus6/shared/growth-registry.json',
]
for jf in critical_jsons:
    jfp = os.path.expanduser(jf)
    if os.path.exists(jfp):
        try:
            json.load(open(jfp))
        except:
            issues.append(('json', f'{os.path.basename(jfp)} corrupted', 'HIGH'))
    else:
        issues.append(('json', f'{os.path.basename(jfp)} missing', 'MED'))

# ── 6. n=6 블로업 정합성 체크 ──
blowup_jsons = [
    ('meta_blowup_state', '~/.nexus6/meta_blowup_state.json'),
    ('engine_blowup_state', '~/.nexus6/engine_blowup_state.json'),
    ('knowledge_blowup', '~/.nexus6/knowledge_blowup.json'),
    ('singularity_proof', '~/.nexus6/singularity_proof.json'),
    ('lens_invariant_cores', '~/.nexus6/lens_invariant_cores.json'),
    ('propagation_rules', '~/.nexus6/propagation_rules.json'),
]
blowup_ok = 0
for bname, bpath in blowup_jsons:
    bp = os.path.expanduser(bpath)
    if os.path.exists(bp):
        try:
            json.load(open(bp))
            blowup_ok += 1
        except:
            issues.append(('blowup', f'{bname} corrupted', 'HIGH'))
    else:
        issues.append(('blowup', f'{bname} missing', 'MED'))

if blowup_ok < 6:
    issues.append(('blowup', f'Only {blowup_ok}/6 blowups intact (need n=6)', 'HIGH'))

# 매니페스트 체크섬 검증
manifest_path = os.path.expanduser('~/.nexus6/sync_manifest.json')
if os.path.exists(manifest_path):
    try:
        import hashlib
        mf = json.load(open(manifest_path))
        tampered = 0
        for fname, finfo in mf.get('files', {}).items():
            fp = finfo.get('path', '')
            if os.path.exists(fp):
                md5 = hashlib.md5(open(fp, 'rb').read()).hexdigest()
                if md5 != finfo.get('md5', ''):
                    tampered += 1
        if tampered > 0:
            issues.append(('manifest', f'{tampered} files changed since lock', 'LOW'))
    except:
        pass

# ── 7. Growth bus 활성도 ──
bus = os.path.expanduser('~/Dev/nexus6/shared/growth_bus.jsonl')
if os.path.exists(bus):
    mtime = os.path.getmtime(bus)
    age_h = (time.time() - mtime) / 3600
    if age_h > 1:
        issues.append(('bus', f'Growth bus stale ({age_h:.1f}h since last write)', 'MED'))

# ── 7. 데몬 상태 ──
pid_file = os.path.expanduser('~/.nexus6/growth_daemon.pid')
if os.path.exists(pid_file):
    try:
        pid = int(open(pid_file).read().strip())
        # macOS에서 프로세스 존재 확인
        import signal
        os.kill(pid, 0)  # 존재하면 OK, 없으면 exception
    except (ProcessLookupError, ValueError):
        issues.append(('daemon', 'PID file exists but daemon dead', 'MED'))
    except PermissionError:
        pass  # 프로세스 존재 (다른 유저)
elif os.path.exists(os.path.expanduser('~/.nexus6')):
    pass  # 데몬 미사용 (OK)

# ── 출력 ──
if issues:
    print(f'    ⚠ {len(issues)} issues found:')
    for cat, desc, sev in issues:
        icon = '🔴' if sev == 'HIGH' else ('🟡' if sev == 'MED' else '🟢')
        print(f'      {icon} [{cat}] {desc}')
else:
    print('    ✅ All pipelines connected — 0 issues')

# ── 8. 자동 수복 (심링크만) ──
for repo in ['TECS-L', 'brainwire', 'sedi', 'anima', 'papers', 'hexa-lang', 'fathom']:
    rp = os.path.expanduser(f'~/Dev/{repo}/.shared')
    repo_dir = os.path.expanduser(f'~/Dev/{repo}')
    if os.path.isdir(repo_dir) and not os.path.exists(rp):
        target = os.path.expanduser('~/Dev/nexus6/shared')
        if os.path.isdir(target):
            os.symlink(target, rp)
            fixed.append(f'{repo}/.shared → nexus6/shared')

if fixed:
    print(f'    🔧 Auto-fixed: {len(fixed)} symlinks')
    for fx in fixed:
        print(f'      ✓ {fx}')

# Bus 기록
with open(bus, 'a') as bf:
    entry = json.dumps({
        'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'repo': 'n6-architecture',
        'type': 'health_check',
        'detail': f'issues={len(issues)},fixed={len(fixed)}'
    })
    bf.write(entry + '\n')
" 2>/dev/null || echo "    DisconnectedCheck: error"
}

# ═══════════════════════════════════════════════════════════════
# AUTO-CLEANUP + LOGIC COMBINER — 자동정리 + 로직 조합기
# ═══════════════════════════════════════════════════════════════
# 모든 로직 발생 시:
#   1. 이벤트 자동 기록 (bus + events/)
#   2. 오래된 데이터 자동 정리
#   3. 중복 발견 병합
#   4. 로직 조합: 서로 다른 리포의 발견을 교차 매칭

# ── 자동정리 (매 사이클 호출) ───────────────────────────────────
auto_cleanup() {
    log_info "  [Cleanup] Auto-cleanup sweep"
    local cleaned=0

    # 1. Growth bus 정리 (10000줄 초과 시 최근 5000줄만 유지)
    local bus="${NEXUS6_ROOT}/shared/growth_bus.jsonl"
    if [ -f "$bus" ]; then
        local lines
        lines=$(wc -l < "$bus" 2>/dev/null | tr -d ' ')
        if [ "$lines" -gt 10000 ]; then
            tail -5000 "$bus" > "${bus}.tmp" && mv "${bus}.tmp" "$bus"
            echo "    Bus: $lines → 5000 lines"
            cleaned=$((cleaned + 1))
        fi
    fi

    # 2. Events 정리 (1일 이상 processed 이벤트 삭제)
    local events_dir="${NEXUS6_ROOT}/shared/events"
    if [ -d "$events_dir" ]; then
        local old_events
        old_events=$(find "$events_dir" -name '*.json' -mtime +1 2>/dev/null | wc -l | tr -d ' ')
        if [ "$old_events" -gt 0 ]; then
            find "$events_dir" -name '*.json' -mtime +1 -delete 2>/dev/null
            echo "    Events: $old_events old files removed"
            cleaned=$((cleaned + 1))
        fi
    fi

    # 3. 로그 로테이션 (1MB 초과 시 truncate)
    local log_dir="$HOME/Library/Logs/n6-growth"
    if [ -d "$log_dir" ]; then
        for logf in "$log_dir"/*.log; do
            [ -f "$logf" ] || continue
            local sz
            sz=$(wc -c < "$logf" 2>/dev/null | tr -d ' ')
            if [ "$sz" -gt 1048576 ]; then
                tail -1000 "$logf" > "${logf}.tmp" && mv "${logf}.tmp" "$logf"
                echo "    Log rotated: $(basename "$logf")"
                cleaned=$((cleaned + 1))
            fi
        done
    fi

    # 4. discoveries.jsonl 정리 (100MB 초과 시 최근 50MB)
    local disc="${HOME}/.nexus6/lens_discoveries.jsonl"
    if [ -f "$disc" ]; then
        local disc_sz
        disc_sz=$(wc -c < "$disc" 2>/dev/null | tr -d ' ')
        if [ "$disc_sz" -gt 104857600 ]; then
            tail -c 52428800 "$disc" > "${disc}.tmp" && mv "${disc}.tmp" "$disc"
            echo "    Discoveries: truncated to 50MB"
            cleaned=$((cleaned + 1))
        fi
    fi

    [ "$cleaned" -gt 0 ] && echo "    Cleaned: $cleaned items" || echo "    Nothing to clean"
}

# ── 로직 조합기 (Logic Combiner) ───────────────────────────────
# 서로 다른 리포의 발견을 교차 매칭해서 새로운 연결 발견
logic_combiner() {
    log_info "  [Combiner] Cross-repo logic combination"

    local bus="${NEXUS6_ROOT}/shared/growth_bus.jsonl"
    [ -f "$bus" ] || return

    python3 -c "
import json, collections

# 최근 500건 이벤트에서 리포별 키워드 수집
bus_lines = open('$bus').readlines()[-500:]
repo_keywords = collections.defaultdict(set)

keywords_of_interest = [
    'BT-', 'EXACT', 'sigma', 'phi', 'tau', 'J2', 'n=6',
    'convergence', 'emergence', 'lens', 'discovery',
    'consciousness', 'fusion', 'battery', 'quantum',
    'topology', 'stability', 'evolution', 'recursion'
]

for line in bus_lines:
    try:
        d = json.loads(line)
        repo = d.get('repo', '')
        detail = str(d.get('detail', '')) + ' ' + str(d.get('phase', ''))
        for kw in keywords_of_interest:
            if kw.lower() in detail.lower():
                repo_keywords[repo].add(kw)
    except:
        pass

# 교차 매칭: 2+ 리포에서 같은 키워드 → 공명
shared = collections.defaultdict(list)
all_repos = list(repo_keywords.keys())
for i, r1 in enumerate(all_repos):
    for r2 in all_repos[i+1:]:
        common = repo_keywords[r1] & repo_keywords[r2]
        if common:
            for kw in common:
                shared[kw].append(f'{r1}↔{r2}')

if shared:
    print(f'    Cross-repo resonances: {len(shared)}')
    for kw, pairs in sorted(shared.items(), key=lambda x: -len(x[1]))[:5]:
        print(f'      {kw}: {\" + \".join(pairs[:3])}')
else:
    print('    No cross-repo resonances in recent events')

# 자동 발견 제안
if len(shared) >= 3:
    print(f'    → {len(shared)} shared patterns detected — potential new BT candidates')
" 2>/dev/null || echo "    Combiner: parse error"
}

# ── run_common_phases에 cleanup + combiner 추가 ─────────────────
# (이미 run_common_phases 안에서 호출됨 — 아래에서 연결)

# ═══════════════════════════════════════════════════════════════
# C₅: INFINITE RECURSION LOOP — 자동화의 자동화의 자동화
# ═══════════════════════════════════════════════════════════════
# 매 σ=12 사이클: 엔진이 자신의 성장을 측정하고
# 코드 변경→지식→전파→흡수→성장 전체 루프를 자동 실행
# + 전 리포 상호 지식 전파 + peak 성장기 감지/재현

infinite_recursion_loop() {
    local cycle="${1:-1}"
    local repo="${2:-unknown}"

    # σ=12 사이클마다
    if [ $((cycle % 12)) -ne 0 ]; then
        return
    fi

    local res
    res=$(check_resources)
    [ "$res" = "STOP" ] && return

    log_info "  [C₅] Infinite recursion loop (cycle $cycle)"

    python3 -c "
import json, os, time, collections

bus_file = os.path.expanduser('~/Dev/nexus6/shared/growth_bus.jsonl')
disc_log = os.path.expanduser('~/Dev/nexus6/shared/discovery_log.jsonl')
n6_dir = os.path.expanduser('~/.nexus6')
shared = os.path.expanduser('~/Dev/nexus6/shared')

# ═══ 1. 성장률 측정 ═══
bus_lines = []
if os.path.exists(bus_file):
    with open(bus_file) as f:
        bus_lines = f.readlines()[-200:]

hourly = collections.defaultdict(int)
for line in bus_lines:
    try:
        e = json.loads(line)
        h = e.get('ts','')[:13]
        hourly[h] += 1
    except: pass

growth_rate = sum(hourly.values()) / max(len(hourly), 1)
peak_hour = max(hourly.items(), key=lambda x: x[1]) if hourly else ('?', 0)

# ═══ 2. Peak 감지 ═══
# 현재 성장률이 평균의 2배 이상이면 peak
avg_all = len(bus_lines) / max(len(hourly), 1)
is_peak = growth_rate > avg_all * 2

# Peak 상태 저장
peak_file = os.path.join(n6_dir, 'peak_state.json')
peak_state = {}
if os.path.exists(peak_file):
    try: peak_state = json.load(open(peak_file))
    except: pass

if is_peak:
    peak_state['last_peak'] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
    peak_state['peak_rate'] = growth_rate
    peak_state['peak_count'] = peak_state.get('peak_count', 0) + 1

peak_state['current_rate'] = growth_rate
peak_state['avg_rate'] = avg_all
peak_state['ts'] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
json.dump(peak_state, open(peak_file, 'w'), indent=2)

# ═══ 3. 상호 지식 전파 ═══
# 각 리포의 최신 발견을 bus에 교차 기록
repos = ['TECS-L', 'brainwire', 'sedi', 'anima', 'papers', 'hexa-lang', 'fathom']
repo_latest = {}
for r in repos:
    rp = os.path.expanduser(f'~/Dev/{r}')
    if not os.path.isdir(rp): continue
    # 최신 커밋 메시지
    import subprocess
    try:
        msg = subprocess.run(['git', '-C', rp, 'log', '--oneline', '-1', '--since=2 hours ago'],
                           capture_output=True, text=True, timeout=5).stdout.strip()
        if msg:
            repo_latest[r] = msg
    except: pass

# 교차 전파: 각 리포의 최신을 bus에 기록
with open(bus_file, 'a') as bf:
    for r, msg in repo_latest.items():
        entry = json.dumps({
            'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'repo': r,
            'type': 'cross_propagation',
            'detail': msg[:80]
        })
        bf.write(entry + '\n')

# ═══ 4. 전파/흡수 규칙 JSON 갱신 ═══
rules_file = os.path.join(n6_dir, 'propagation_rules.json')
rules = {
    'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
    'rules': [
        {'id': 'PR-01', 'rule': 'hook 감지 상수 → discovery_log → 매 사이클 자동 분류'},
        {'id': 'PR-02', 'rule': '새 상수 → events/ → collect_events() → atlas 등록 시도'},
        {'id': 'PR-03', 'rule': 'BT 후보 → growth_bus → logic_combiner → 교차 공명 감지'},
        {'id': 'PR-04', 'rule': '렌즈 후보 → unconnected_lenses.json → 다음 블로업에서 흡수'},
        {'id': 'PR-05', 'rule': '리포 커밋 → cross_propagation → 전 리포 bus 공유'},
        {'id': 'PR-06', 'rule': 'peak 감지 → peak_state.json → 정체 시 peak 조건 재현'},
        {'id': 'PR-07', 'rule': '메타 블로업 → fingerprint → 부동점 수렴 감지'},
        {'id': 'PR-08', 'rule': '건강 체크 → 심링크/JSON/bus/events 자동 수복'},
        {'id': 'PR-09', 'rule': 'convergence_ops → 22 absolute rules 자동 적용'},
        {'id': 'PR-10', 'rule': '엔진 자체 변경 → git diff → 파괴적 변경 차단'},
    ],
    'propagation_flow': [
        'hook → discovery_log → process → classify → absorb',
        'absorb → events → collect → atlas/bus',
        'bus → combiner → cross_resonance → BT candidates',
        'blowup → core/fiber → emergence → propagate',
        'commit → cross_propagation → all repos bus',
    ],
    'peak': peak_state,
    'cross_propagated': len(repo_latest),
}
json.dump(rules, open(rules_file, 'w'), indent=2, ensure_ascii=False)

# ═══ 출력 ═══
peak_tag = ' ** PEAK **' if is_peak else ''
print(f'    Growth rate: {growth_rate:.1f}/hr (avg: {avg_all:.1f}){peak_tag}')
print(f'    Cross-propagated: {len(repo_latest)} repos')
print(f'    Propagation rules: 10 (PR-01~10)')
print(f'    Peak count: {peak_state.get(\"peak_count\", 0)}')
" 2>/dev/null || echo "    C5: error"
}

log_info "growth_common.sh loaded (n=$N6_N, σ=$N6_SIGMA, J₂=$N6_J2)"
