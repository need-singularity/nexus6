#!/usr/bin/env bash
set -euo pipefail
GROWTH_NAME="nexus"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOMAIN="discovery"

# 공통 라이브러리 (shared/config/loop/nexus.json에서 interval/max_cycles 자동 로드)
COMMON="$PROJECT_ROOT/scripts/lib/growth_common.sh"
source "$COMMON"
MAX_CYCLES=${1:-${MAX_CYCLES:-999}}
INTERVAL=${2:-${INTERVAL:-1800}}

# 프로젝트별 phases
domain_phases() {
    local cycle="$1" load="$2"

    # 1. 발견 로그 스캔
    log_info "Phase: 발견 로그 스캔"
    local disc_count=0
    if [ -f "$PROJECT_ROOT/shared/discovery/discovery_log.jsonl" ]; then
        disc_count=$(wc -l < "$PROJECT_ROOT/shared/discovery/discovery_log.jsonl" | tr -d ' ')
    fi
    write_growth_bus "discovery_scan" "ok" "discoveries=$disc_count"

    # 2. 검증 상수 체크
    log_info "Phase: 검증 상수 체크"
    local verified=0
    if [ -f "$PROJECT_ROOT/shared/discovery/verified_constants.jsonl" ]; then
        verified=$(wc -l < "$PROJECT_ROOT/shared/discovery/verified_constants.jsonl" | tr -d ' ')
    fi
    write_growth_bus "verified_check" "ok" "constants=$verified"

    # 3. 렌즈 카운트
    log_info "Phase: 렌즈 카운트"
    local lenses=0
    if [ -f "$PROJECT_ROOT/shared/discovery/discovery_graph.json" ]; then
        lenses=$(/usr/bin/python3 -c "import json; print(len(json.load(open('$PROJECT_ROOT/shared/discovery/discovery_graph.json')).get('nodes',[])))" 2>/dev/null || echo 0)
    fi
    write_growth_bus "lens_count" "ok" "lenses=$lenses"

    # 4. tecs-l 흡수 데이터 체크
    log_info "Phase: TECS-L 흡수 데이터 체크"
    local tecs_verify=0
    if [ -d "$PROJECT_ROOT/tecs-l/verify" ]; then
        tecs_verify=$(find "$PROJECT_ROOT/tecs-l/verify" -name '*.py' | wc -l | tr -d ' ')
    fi
    write_growth_bus "tecs_verify" "ok" "scripts=$tecs_verify"
}

# 실행
run_growth_loop "domain_phases"
