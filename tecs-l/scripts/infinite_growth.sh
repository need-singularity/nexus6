#!/usr/bin/env bash
set -euo pipefail
GROWTH_NAME="TECS-L"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOMAIN="number_theory"
MAX_CYCLES=${MAX_CYCLES:-${1:-999}}
INTERVAL=${INTERVAL:-${2:-1800}}

# 공통 라이브러리
COMMON="$HOME/Dev/nexus/scripts/lib/growth_common.sh"
source "$COMMON"

# 프로젝트별 phases
domain_phases() {
    local cycle="$1" load="$2"

    # 1. 수학 아틀라스 상태
    log_info "Phase: 수학 아틀라스 상태"
    local atlas_file="$PROJECT_ROOT/.shared/discovery/math_atlas.json"
    if [ -f "$atlas_file" ]; then
        local atlas_count
        atlas_count=$(/usr/bin/python3 -c "import json; d=json.load(open('$atlas_file')); print(len(d) if isinstance(d,list) else len(d.keys()))" 2>/dev/null || echo "?")
        log_info "  math_atlas.json: ${atlas_count} 항목"
        write_growth_bus "math_atlas" "ok" "count=${atlas_count}"
    else
        log_info "  math_atlas.json 없음"
        write_growth_bus "math_atlas" "skip" "not_found"
    fi

    # 2. 계산기 레지스트리
    log_info "Phase: 계산기 레지스트리"
    local calc_dir="$PROJECT_ROOT/.shared/calc"
    if [ -d "$calc_dir" ]; then
        local calc_count
        calc_count=$(ls "$calc_dir" 2>/dev/null | wc -l | tr -d ' ')
        log_info "  .shared/calc/: ${calc_count}개 파일"
        write_growth_bus "calc_registry" "ok" "count=${calc_count}"
    else
        log_info "  .shared/calc/ 디렉토리 없음"
        write_growth_bus "calc_registry" "skip" "not_found"
    fi

    # 3. DSE 도메인
    log_info "Phase: DSE 도메인"
    local dse_dir="$PROJECT_ROOT/.shared/dse/domains"
    if [ -d "$dse_dir" ]; then
        local dse_count
        dse_count=$(find "$dse_dir" -name '*.toml' 2>/dev/null | wc -l | tr -d ' ')
        log_info "  DSE domains: ${dse_count}개 .toml"
        write_growth_bus "dse_domains" "ok" "count=${dse_count}"
    else
        log_info "  .shared/dse/domains/ 없음"
        write_growth_bus "dse_domains" "skip" "not_found"
    fi

    # 4. Rust tecsrs 빌드
    log_info "Phase: Rust tecsrs 빌드"
    local cargo_toml="$PROJECT_ROOT/.shared/tecsrs/Cargo.toml"
    if [ -f "$cargo_toml" ]; then
        if cargo check --manifest-path "$cargo_toml" 2>/dev/null; then
            log_info "  cargo check: OK"
            write_growth_bus "tecsrs_build" "ok" ""
        else
            log_warn "  cargo check: FAIL"
            write_growth_bus "tecsrs_build" "fail" "cargo_check_error"
        fi
    else
        log_info "  tecsrs/Cargo.toml 없음 — skip"
        write_growth_bus "tecsrs_build" "skip" "no_cargo_toml"
    fi

    # 5. 성장 스캔
    log_info "Phase: 성장 스캔"
    local scan_script="$PROJECT_ROOT/.growth/scan.py"
    if [ -f "$scan_script" ]; then
        /usr/bin/python3 "$scan_script" 2>/dev/null | tail -5 | while IFS= read -r line; do
            log_info "  $line"
        done
        write_growth_bus "growth_scan" "ok" ""
    else
        log_info "  .growth/scan.py 없음 — skip"
        write_growth_bus "growth_scan" "skip" "no_script"
    fi
}

run_growth_loop "domain_phases"
