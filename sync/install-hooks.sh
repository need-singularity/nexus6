#!/usr/bin/env bash
set -euo pipefail
# ═══════════════════════════════════════════════════════════════
# NEXUS-6 Central Hook Installer
# ═══════════════════════════════════════════════════════════════
# 모든 리포의 git hooks + .shared 심링크를 nexus에서 일괄 관리.
# Usage: bash ~/Dev/nexus/sync/install-hooks.sh [--verify] [--force]
#
# 설치 대상:
#   .git/hooks/post-commit  — 커밋 후 sync-all.sh 자동 실행
#   .shared                 — nexus/shared 심링크
#   scripts/lib/            — nexus/lib/ 심링크

NEXUS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NEXUS_SYNC="$NEXUS_ROOT/sync"
NEXUS_STATE="$HOME/.nexus"

# 전체 리포 목록 (n6-architecture는 특수 훅이라 별도 처리)
STANDARD_REPOS=(TECS-L anima sedi brainwire papers nexus)
SPECIAL_REPOS=(n6-architecture)
ALL_REPOS=("${STANDARD_REPOS[@]}" "${SPECIAL_REPOS[@]}")

VERIFY_ONLY=false
FORCE=false
while [ $# -gt 0 ]; do
    case "$1" in
        --verify) VERIFY_ONLY=true; shift ;;
        --force)  FORCE=true; shift ;;
        *)        echo "Unknown: $1"; exit 1 ;;
    esac
done

mkdir -p "$NEXUS_STATE"

ok=0; fail=0; skip=0

log_ok()   { echo "  ✅ $*"; ((ok++)) || true; }
log_fail() { echo "  ❌ $*"; ((fail++)) || true; }
log_skip() { echo "  ⏭️  $*"; ((skip++)) || true; }

# ── 1. Standard post-commit hook (6 repos) ──────────────────────
STANDARD_HOOK='#!/usr/bin/env bash
# NEXUS-6 자동 동기화 (변경 감지 시)
(bash ~/Dev/nexus/sync/sync-all.sh >> ~/.nexus/sync.log 2>&1 &)'

install_standard_hook() {
    local repo="$1"
    local hook="$HOME/Dev/$repo/.git/hooks/post-commit"

    if [ ! -d "$HOME/Dev/$repo/.git" ]; then
        log_fail "$repo: .git 없음"
        return
    fi

    if $VERIFY_ONLY; then
        if [ -f "$hook" ] && grep -q "sync-all.sh" "$hook"; then
            log_ok "$repo: post-commit ✓"
        else
            log_fail "$repo: post-commit 없거나 구버전"
        fi
        return
    fi

    if [ -f "$hook" ] && grep -q "sync-all.sh" "$hook" && ! $FORCE; then
        log_skip "$repo: post-commit 이미 설치됨"
        return
    fi

    echo "$STANDARD_HOOK" > "$hook"
    chmod +x "$hook"
    log_ok "$repo: post-commit 설치 완료"
}

# ── 2. n6-architecture 특수 훅 (빌드+데몬+동기화) ────────────────
install_n6arch_hook() {
    local repo="n6-architecture"
    local hook="$HOME/Dev/$repo/.git/hooks/post-commit"

    if $VERIFY_ONLY; then
        if [ -f "$hook" ] && grep -q "Auto-measure\|Auto-rebuild" "$hook"; then
            log_ok "$repo: post-commit (특수) ✓"
        else
            log_fail "$repo: post-commit 없거나 구버전"
        fi
        return
    fi

    # n6-architecture 훅은 특수 로직 포함 — 존재하면 건드리지 않음
    if [ -f "$hook" ] && ! $FORCE; then
        log_skip "$repo: post-commit 특수 훅 유지"
        return
    fi

    cat > "$hook" << 'HOOK_EOF'
#!/usr/bin/env bash
# NEXUS-6: Auto-measure + Auto-rebuild after every commit

NEXUS_ROOT="/Users/ghost/Dev/n6-architecture/tools/nexus"
NEXUS_STATE="$HOME/.nexus"
CARGO="$HOME/.cargo/bin/cargo"

# 1. Auto-measure
cd "$NEXUS_ROOT/scripts"
bash measure.sh >> "$NEXUS_STATE/metrics-history.jsonl" 2>/dev/null &

# 2. Auto-rebuild if nexus source changed
changed_files=$(git diff --name-only HEAD~1 HEAD 2>/dev/null || echo "")
if echo "$changed_files" | grep -q "tools/nexus/src/"; then
    echo "[post-commit] NEXUS-6 소스 변경 감지 — 자동 재빌드 시작" >> "$NEXUS_STATE/rebuild.log"
    (
        cd "$NEXUS_ROOT"
        $CARGO build --release >> "$NEXUS_STATE/rebuild.log" 2>&1
        PATH="$HOME/.cargo/bin:$PATH" /usr/bin/python3 -m maturin build --release --features python >> "$NEXUS_STATE/rebuild.log" 2>&1
        pip3 install "$NEXUS_ROOT/target/wheels/"nexus-*-cp*-*.whl --force-reinstall >> "$NEXUS_STATE/rebuild.log" 2>&1
        echo "[post-commit] NEXUS-6 재빌드 완료: $(date)" >> "$NEXUS_STATE/rebuild.log"
    ) &
fi

# 3. Restart daemon if running and source changed
if echo "$changed_files" | grep -q "tools/nexus/"; then
    if [[ -f "$NEXUS_STATE/daemon.pid" ]]; then
        pid=$(cat "$NEXUS_STATE/daemon.pid" 2>/dev/null)
        if kill -0 "$pid" 2>/dev/null; then
            echo "[post-commit] 데몬 재시작 (PID $pid)" >> "$NEXUS_STATE/rebuild.log"
            kill "$pid" 2>/dev/null || true
            sleep 1
            nohup bash "$NEXUS_ROOT/scripts/nexus_growth_daemon.sh" \
                --max-cycles 999 --interval 30 --skip-commit \
                >> "$NEXUS_STATE/growth.log" 2>&1 &
            echo $! > "$NEXUS_STATE/daemon.pid"
        fi
    fi
fi

# 4. 전 리포 동기화
(bash ~/Dev/nexus/sync/sync-all.sh >> ~/.nexus/sync.log 2>&1 &)
HOOK_EOF
    chmod +x "$hook"
    log_ok "$repo: post-commit (특수) 설치 완료"
}

# ── 3. .shared 심링크 설치 ────────────────────────────────────────
install_shared_symlink() {
    local repo="$1"
    local target="$HOME/Dev/$repo/.shared"

    if $VERIFY_ONLY; then
        if [ -L "$target" ] && [ -d "$target" ]; then
            log_ok "$repo: .shared → $(readlink "$target")"
        else
            log_fail "$repo: .shared 심링크 깨짐"
        fi
        return
    fi

    if [ -L "$target" ] && [ -d "$target" ] && ! $FORCE; then
        log_skip "$repo: .shared 이미 설정됨"
        return
    fi

    rm -f "$target" 2>/dev/null || true
    ln -s ../nexus/shared "$target"
    log_ok "$repo: .shared → nexus/shared"
}

# ── 4. scripts/lib/growth_common.sh 심링크 ───────────────────────
install_growth_lib() {
    local repo="$1"
    local dir="$HOME/Dev/$repo/scripts/lib"
    local target="$dir/growth_common.sh"

    if [ ! -d "$HOME/Dev/$repo/scripts" ]; then
        log_skip "$repo: scripts/ 없음"
        return
    fi

    if $VERIFY_ONLY; then
        if [ -L "$target" ] && [ -f "$target" ]; then
            log_ok "$repo: growth_common.sh → $(readlink "$target")"
        elif [ ! -e "$target" ]; then
            log_skip "$repo: growth_common.sh 없음 (사용 안 함)"
        else
            log_fail "$repo: growth_common.sh 비정상"
        fi
        return
    fi

    if [ -L "$target" ] && [ -f "$target" ] && ! $FORCE; then
        log_skip "$repo: growth_common.sh 이미 설정됨"
        return
    fi

    mkdir -p "$dir"
    rm -f "$target" 2>/dev/null || true
    ln -s ../../../nexus/lib/growth_common.sh "$target"
    log_ok "$repo: growth_common.sh → nexus/lib/"
}

# ── Execute ────────────────────────────────────────────────────
echo "╔═══════════════════════════════════════════════════════════╗"
if $VERIFY_ONLY; then
    echo "║  NEXUS-6 Hook Verification                               ║"
else
    echo "║  NEXUS-6 Hook Installation                               ║"
fi
echo "╠═══════════════════════════════════════════════════════════╣"

echo "║"
echo "║  [1/3] Git Hooks (post-commit)"
for repo in "${STANDARD_REPOS[@]}"; do
    install_standard_hook "$repo"
done
install_n6arch_hook

echo "║"
echo "║  [2/3] .shared Symlinks"
for repo in "${ALL_REPOS[@]}"; do
    install_shared_symlink "$repo"
done

echo "║"
echo "║  [3/3] Growth Library Symlinks"
for repo in "${ALL_REPOS[@]}"; do
    install_growth_lib "$repo"
done

echo "║"
echo "╠═══════════════════════════════════════════════════════════╣"
echo "║  Results: ✅ $ok  ⏭️ $skip  ❌ $fail"
echo "╚═══════════════════════════════════════════════════════════╝"

if [ $fail -gt 0 ]; then
    exit 1
fi
