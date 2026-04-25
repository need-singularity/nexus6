#!/usr/bin/env bash
# tool/raw_enforce.sh — raw 37/38 (omega_saturation_cycle) enforce CLI.
# Created: 2026-04-25 cycle 56 (nxs-20260425-001 raw enforce wire,
# cycle 44 의 zero-dependency policy 일관 — git/Claude/launchd hook 없이
# user 명시 실행 패턴).
#
# Usage:
#   tool/raw_enforce.sh                          # staged files (git diff --cached)
#   tool/raw_enforce.sh path1 path2 ...          # specific files
#   tool/raw_enforce.sh --recent N               # last N commits
#
# Behavior:
#   1. plan-only commit detection (raw 37 plan side):
#      design/, docs/, *handoff*, *audit* 의 saturation/ceiling/sensitivity
#      keyword + impl files (cli/, tool/, scripts/, *.hexa, *.py, state/*.json)
#      0개 → WARN
#   2. retry-past-max detection (raw 38 impl side):
#      최근 commits 의 design-only chain 3+ 누적 → WARN
#
# Exit codes:
#   0 — pass (또는 warn-only mode)
#   1 — violation (HARD enforce mode, default OFF)
#
# Modes:
#   default = WARN only (exit 0 with stderr emit)
#   NEXUS_RAW_ENFORCE_HARD=1 — HARD (violation 시 exit 1)
#   NEXUS_RAW_ENFORCE_OFF=1 — bypass (exit 0 silent)
#
# Zero-dependency policy 일관 (cycle 44):
#   - git hook 미설치 (user 명시 실행)
#   - Claude hook 미설치 (cycle 40 제거)
#   - launchd 미설치
#   - LD_PRELOAD 미설치
#   - 본 tool = bash 만, 외부 의존 없음 (git CLI 만)

set -euo pipefail

if [ "${NEXUS_RAW_ENFORCE_OFF:-0}" = "1" ]; then exit 0; fi

# determine input files
FILES=""
if [ "${1:-}" = "--recent" ]; then
    N="${2:-3}"
    FILES=$(git log -"$N" --name-only --pretty=format: 2>/dev/null | sort -u | grep -v '^$' || true)
elif [ $# -gt 0 ]; then
    FILES="$*"
else
    FILES=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null || true)
    if [ -z "$FILES" ]; then
        # no staged → check working tree changes
        FILES=$(git diff --name-only --diff-filter=ACMR 2>/dev/null || true)
    fi
fi

[ -z "$FILES" ] && { echo "raw_enforce: no files to check (no staged/working tree/cli args)"; exit 0; }

# classify
DESIGN_KW_HITS=""
IMPL_HITS=""
PLAN_KEYWORDS="saturation|ceiling|sensitivity-probe|sensitivity 정밀화|simulation 한계|axiom redesign|fixpoint"

while IFS= read -r f; do
    [ -z "$f" ] && continue
    case "$f" in
        design/*|docs/*|*handoff*|*audit*)
            if [ -f "$f" ] && grep -qiE "$PLAN_KEYWORDS" "$f" 2>/dev/null; then
                DESIGN_KW_HITS="$DESIGN_KW_HITS $f"
            fi
            ;;
        cli/*|tool/*|scripts/*|*.hexa|*.py|state/*.json|state/*.jsonl|n6/*|atlas/*)
            IMPL_HITS="$IMPL_HITS $f"
            ;;
    esac
done <<< "$FILES"

# plan-only commit check (raw 37)
VIOLATION=0
if [ -n "$DESIGN_KW_HITS" ] && [ -z "$IMPL_HITS" ]; then
    VIOLATION=1
    echo "" >&2
    echo "[raw#37 plan side WARN] plan-only commit detected" >&2
    echo "  design files with plan keywords:$DESIGN_KW_HITS" >&2
    echo "  impl files: (none — cli/ tool/ scripts/ *.hexa *.py *.json SSOT 등)" >&2
    echo "  → raw 37 (plan) hit + raw 38 (impl) 같은 cycle 안에 완료 필요." >&2
    echo "  → bypass: NEXUS_RAW_ENFORCE_OFF=1" >&2
    echo "  → 또는 impl files 추가 후 re-stage." >&2
    echo "" >&2
fi

# retry-past-max — recent commit chain (raw 38)
RECENT_DESIGN_ONLY=$(git log -3 --name-only --pretty=format:"%H" 2>/dev/null | awk '
    BEGIN {h=""; design=0; impl=0; chain=0}
    /^[0-9a-f]{7,}$/ {
        if (h != "" && design > 0 && impl == 0) chain++
        else if (h != "" && impl > 0) chain=0
        h=$0; design=0; impl=0; next
    }
    /^design\/|^docs\/|handoff|audit/ {design++}
    /^cli\/|^tool\/|^scripts\/|\.hexa$|\.py$|^state\/.*\.json/ {impl++}
    END {
        if (h != "" && design > 0 && impl == 0) chain++
        print chain
    }' || echo 0)

if [ "${RECENT_DESIGN_ONLY:-0}" -ge 3 ] 2>/dev/null; then
    VIOLATION=1
    echo "[raw#38 impl side WARN] retry-past-max — design-only commit chain ${RECENT_DESIGN_ONLY}+ 누적" >&2
    echo "  → raw 38 (implementation) 같은 cycle 안에 강제. 다음 commit 에 impl files 포함 필수." >&2
    echo "  → bypass: NEXUS_RAW_ENFORCE_OFF=1" >&2
    echo "" >&2
fi

# verdict
if [ "$VIOLATION" -eq 0 ]; then
    [ -n "$DESIGN_KW_HITS" ] && [ -n "$IMPL_HITS" ] && echo "[raw#37/38 PASS] design+impl pair detected (plan kw:$DESIGN_KW_HITS / impl: present)" >&2
    exit 0
fi

# HARD vs WARN
if [ "${NEXUS_RAW_ENFORCE_HARD:-0}" = "1" ]; then
    echo "[raw#37/38 HARD enforce] violation — exit 1" >&2
    exit 1
fi

echo "[raw#37/38 WARN-only mode] (NEXUS_RAW_ENFORCE_HARD=1 으로 hard enforce 활성)" >&2
exit 0
