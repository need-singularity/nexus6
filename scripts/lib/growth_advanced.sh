#!/usr/bin/env bash
# growth_advanced.sh — 고급 성장 함수 (growth_common.sh에서 source됨)
# 이 파일의 함수들은 growth_common.sh의 log_info, log_warn, write_growth_bus,
# GROWTH_NAME, PROJECT_ROOT, GROWTH_DIR, NEXUS6_BIN 등이 이미 정의되어 있다고 가정합니다.

# ── #1: 렌즈 공명 브릿지 ──
common_resonance_bridge() {
    log_info "🔗 Resonance Bridge"
    local mirror_file="$HOME/.nexus6/last_mirror.json"
    [ ! -f "$mirror_file" ] && return

    python3 -c "
import json, os, datetime

with open('$mirror_file') as f:
    mirror = json.load(f)

resonance = {
    'source': '$GROWTH_NAME',
    'ts': datetime.datetime.utcnow().isoformat() + 'Z',
    'harmony': mirror.get('harmony', 0),
    'eigenvalue': mirror.get('eigenvalue', 0),
}

for d in os.listdir(os.path.expanduser('~/Dev')):
    if d == '$GROWTH_NAME': continue
    target = os.path.expanduser(f'~/Dev/{d}/.growth')
    if not os.path.isdir(target): continue
    rf = os.path.join(target, 'resonance_bridge.jsonl')
    with open(rf, 'a') as f:
        f.write(json.dumps(resonance) + '\n')
print(f'Resonance bridged (harmony={mirror.get(\"harmony\",0):.1f})')
" 2>/dev/null | while IFS= read -r line; do
        log_info "  $line"
    done
    write_growth_bus "resonance_bridge" "ok" ""
}

# ── #6: 크로스 도메인 실험 ──
common_cross_experiment() {
    log_info "🧪 Cross-domain experiment"
    if [ ! -f "$NEXUS6_BIN" ]; then return; fi

    # 형제 프로젝트의 도메인으로 실험 실행
    local domains=""
    for proj_dir in "$HOME"/Dev/*/; do
        local pname=$(basename "$proj_dir")
        [ "$pname" = "$GROWTH_NAME" ] && continue
        local pstate="$proj_dir/.growth/growth_state.json"
        [ ! -f "$pstate" ] && continue
        # growth_state에서 도메인 추출 시도
        local pdomain
        pdomain=$(python3 -c "import json; print(json.load(open('$pstate')).get('domain',''))" 2>/dev/null || echo "")
        [ -z "$pdomain" ] && continue
        domains="$domains $pdomain"
    done

    if [ -n "$domains" ]; then
        local count=0
        for dom in $domains; do
            NEXUS6_ROOT="$HOME/Dev/nexus6" "$NEXUS6_BIN" scan "$dom" 2>/dev/null | grep -E "exact_ratio|singularity" | head -2 | while IFS= read -r line; do
                log_info "  [$dom] $line"
            done
            count=$((count + 1))
            [ "$count" -ge 3 ] && break  # 최대 3개 도메인
        done
        write_growth_bus "cross_experiment" "ok" "domains=$count"
    fi
}

# ── #13: 동기화 우선순위 큐 ──
common_sync_priority_queue() {
    log_info "📊 Sync priority queue"
    python3 -c "
import json, os, datetime

bridge_file = os.path.expanduser('~/Dev/nexus6/shared/bridge_state.json')
if not os.path.exists(bridge_file):
    print('No bridge state')
    exit(0)

with open(bridge_file) as f:
    state = json.load(f)

conns = state.get('connections', {})

# 우선순위 계산: affinity * (1 + 변경 빈도) * (1 + 최근도)
priorities = []
now = datetime.datetime.utcnow()
for name, info in conns.items():
    affinity = info.get('affinity_score', 0)
    absorbed = info.get('absorbed_count', 0)
    last_sync_str = info.get('last_sync', '')

    # 최근도 보너스
    recency = 1.0
    if last_sync_str:
        try:
            last = datetime.datetime.fromisoformat(last_sync_str.replace('Z',''))
            hours_ago = (now - last).total_seconds() / 3600
            recency = 1.0 + min(hours_ago / 24, 2.0)  # 오래될수록 우선
        except: pass

    score = affinity * (1 + absorbed / 1000) * recency
    priorities.append((name, score, affinity, absorbed))

priorities.sort(key=lambda x: -x[1])

# 우선순위 큐 저장
queue_file = os.path.expanduser('~/.nexus6/sync_priority.json')
queue = [{'project': p[0], 'priority': round(p[1], 1), 'affinity': p[2], 'absorbed': p[3]} for p in priorities]
with open(queue_file, 'w') as f:
    json.dump(queue, f, indent=2)

for p in priorities[:5]:
    print(f'  {p[0]:20s} priority={p[1]:>8.1f} aff={p[2]:.0f}%')
" 2>/dev/null | while IFS= read -r line; do
        log_info "$line"
    done
    write_growth_bus "sync_priority" "ok" ""
}

# ── #14: 크로스 프로젝트 테스트 ──
common_cross_test() {
    log_info "🧬 Cross-project test"
    local shared_dir="$HOME/Dev/TECS-L/.shared"
    [ ! -d "$shared_dir" ] && return

    # .shared 변경 감지
    local shared_hash_file="$GROWTH_DIR/.shared_hash"
    local current_hash
    current_hash=$(find "$shared_dir" -type f -newer "$shared_hash_file" 2>/dev/null | wc -l | tr -d ' ')

    if [ "${current_hash:-0}" -gt 0 ]; then
        log_info "  .shared 변경 감지 (${current_hash} files) → 테스트 실행"

        # Cargo.toml이 있는 프로젝트만 테스트
        if [ -f "$PROJECT_ROOT/Cargo.toml" ]; then
            local test_result
            test_result=$("$HOME/.cargo/bin/cargo" test --manifest-path "$PROJECT_ROOT/Cargo.toml" -- --quiet 2>&1 | tail -1)
            log_info "  $GROWTH_NAME: $test_result"
            write_growth_bus "cross_test" "ok" "result=$test_result"
        fi

        # 해시 갱신
        touch "$shared_hash_file"
    else
        log_info "  .shared 변경 없음 — 스킵"
    fi
}

# ── growth_advanced.sh loaded ──
