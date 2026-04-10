#!/usr/bin/env bash
# dispatch.sh — nexus에서 각 프로젝트에 Claude Code CLI 명령 디스패치
#
# 사용법:
#   ./scripts/dispatch.sh <project> <prompt>        # 단일 프로젝트
#   ./scripts/dispatch.sh all <prompt>              # 전 프로젝트
#   ./scripts/dispatch.sh --parallel all <prompt>   # 전 프로젝트 병렬
#
# 예시:
#   ./scripts/dispatch.sh anima "블로업 실행하고 결과 알려줘"
#   ./scripts/dispatch.sh all "cargo test 실행하고 실패 있으면 수정해줘"
#   ./scripts/dispatch.sh hexa-lang "특이점 사이클 돌려줘"
#   ./scripts/dispatch.sh --parallel all "루프 1회 실행"

set -euo pipefail

CLAUDE_BIN="${CLAUDE_BIN:-$HOME/.local/bin/claude}"
LOG_DIR="$HOME/.nexus/dispatch"
mkdir -p "$LOG_DIR"

PROJECTS=(
    "nexus:/Users/ghost/Dev/nexus"
    "anima:/Users/ghost/Dev/anima"
    "TECS-L:/Users/ghost/Dev/TECS-L"
    "n6-architecture:/Users/ghost/Dev/n6-architecture"
    "sedi:/Users/ghost/Dev/sedi"
    "brainwire:/Users/ghost/Dev/brainwire"
    "hexa-lang:/Users/ghost/Dev/hexa-lang"
    "fathom:/Users/ghost/Dev/fathom"
    "papers:/Users/ghost/Dev/papers"
)

ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(ts)] $1"; }

dispatch_one() {
    local name="$1"
    local path="$2"
    local prompt="$3"
    local log_file="$LOG_DIR/${name}_$(date +%Y%m%d_%H%M%S).log"

    if [ ! -d "$path" ]; then
        log "⚠️ $name: 경로 없음 ($path)"
        return 1
    fi

    log "📡 $name: 디스패치 시작"
    log "   prompt: $prompt"

    # Claude Code CLI 실행 (-p = print mode, 비대화형)
    (
        cd "$path"
        "$CLAUDE_BIN" -p "$prompt" \
            --allowedTools "Bash Edit Read Write Grep Glob" \
            --max-budget-usd 0.50 \
            2>&1
    ) | tee "$log_file"

    local rc=${PIPESTATUS[0]}
    if [ "$rc" -eq 0 ]; then
        log "✅ $name: 완료"
    else
        log "⚠️ $name: 종료코드 $rc"
    fi

    # 결과 요약을 growth_bus에 기록
    local bus="$HOME/Dev/nexus/shared/discovery/growth_bus.jsonl"
    printf '{"ts":"%s","repo":"%s","phase":"dispatch","status":"%s","detail":"%s"}\n' \
        "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$name" \
        "$([ $rc -eq 0 ] && echo ok || echo fail)" \
        "$(echo "$prompt" | head -c 100)" >> "$bus" 2>/dev/null || true

    return $rc
}

find_project() {
    local target="$1"
    for entry in "${PROJECTS[@]}"; do
        local name="${entry%%:*}"
        local path="${entry#*:}"
        if [ "$name" = "$target" ]; then
            echo "$path"
            return 0
        fi
    done
    return 1
}

# ── 인자 파싱 ──
PARALLEL=false
if [ "${1:-}" = "--parallel" ] || [ "${1:-}" = "-P" ]; then
    PARALLEL=true
    shift
fi

TARGET="${1:-}"
shift || true
PROMPT="${*:-}"

if [ -z "$TARGET" ] || [ -z "$PROMPT" ]; then
    echo "Usage: $0 [--parallel] <project|all> <prompt>"
    echo ""
    echo "Projects:"
    for entry in "${PROJECTS[@]}"; do
        echo "  ${entry%%:*}"
    done
    echo "  all  (전체)"
    echo ""
    echo "Examples:"
    echo "  $0 anima '블로업 실행'"
    echo "  $0 all 'cargo test'"
    echo "  $0 --parallel all '루프 1회'"
    exit 1
fi

# ── 실행 ──
if [ "$TARGET" = "all" ]; then
    log "🌐 전 프로젝트 디스패치 (parallel=$PARALLEL)"

    if "$PARALLEL"; then
        pids=()
        for entry in "${PROJECTS[@]}"; do
            name="${entry%%:*}"
            path="${entry#*:}"
            dispatch_one "$name" "$path" "$PROMPT" &
            pids+=($!)
        done
        # 전부 대기
        fail=0
        for pid in "${pids[@]}"; do
            wait "$pid" || fail=$((fail + 1))
        done
        log "🌐 완료: $((${#pids[@]} - fail))/${#pids[@]} 성공"
    else
        ok=0
        fail=0
        for entry in "${PROJECTS[@]}"; do
            name="${entry%%:*}"
            path="${entry#*:}"
            if dispatch_one "$name" "$path" "$PROMPT"; then
                ok=$((ok + 1))
            else
                fail=$((fail + 1))
            fi
            echo ""
        done
        log "🌐 완료: $ok/$((ok + fail)) 성공"
    fi
else
    path=$(find_project "$TARGET")
    if [ -z "$path" ]; then
        echo "Unknown project: $TARGET"
        echo "Available: ${PROJECTS[*]%%:*}"
        exit 1
    fi
    dispatch_one "$TARGET" "$path" "$PROMPT"
fi
