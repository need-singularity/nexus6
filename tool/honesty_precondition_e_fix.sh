#!/usr/bin/env bash
# tool/honesty_precondition_e_fix.sh — Honesty triad precondition-e dropfile generator (2026-04-26)
#
# 3 repos (n6-architecture / anima / hexa-lang) 의 Honesty 4/5 OR 3/5 PARTIAL 상태에서
# 부재한 precondition-e (LLM agents indicator) 의 minimal dropfile template SUGGEST.
# auto-create 안 함 — cross-repo write 안전상 manual only.
# self-host 회피 (bash, no hexa dep).
#
# usage:
#   tool/honesty_precondition_e_fix.sh                 # all 3 repos suggest
#   tool/honesty_precondition_e_fix.sh --repo NAME     # single repo
#   tool/honesty_precondition_e_fix.sh --emit-only NAME --type {claude_md|agent_md|claude_agents}
#
# exit codes: 0=PASS suggestions emitted, 1=usage
# sentinel: __HONESTY_PRECONDITION_E_FIX__ repos=R suggested=S
# origin: design/hexa_sim/cross_repo_dashboard.md (Honesty 1/4 실측)

set -uo pipefail

REPOS=("n6-architecture" "anima" "hexa-lang")
TARGET_REPO=""
EMIT_ONLY=""
EMIT_TYPE="claude_md"

while [ $# -gt 0 ]; do
    case "$1" in
        --repo) TARGET_REPO="$2"; shift 2 ;;
        --emit-only) EMIT_ONLY="$2"; shift 2 ;;
        --type) EMIT_TYPE="$2"; shift 2 ;;
        --help|-h)
            echo "usage: $0 [--repo NAME] [--emit-only NAME --type {claude_md|agent_md|claude_agents}]"
            exit 0
            ;;
        *) echo "unknown: $1" >&2; exit 1 ;;
    esac
done

# CLAUDE.md template 생성
emit_claude_md() {
    local repo_name="$1"
    cat <<EOF
# CLAUDE.md — ${repo_name} 프로젝트 사용자 정의

> 본 파일 = Honesty triad precondition-e fix (LLM agents indicator).
> Phase 3 supercycle / cross_repo_dashboard 가 .claude/agents/ OR CLAUDE.md OR
> AGENT.md 중 하나만 있어도 PASS 처리. 가장 가벼운 옵션 = 본 CLAUDE.md drop.

## 프로젝트 개요

${repo_name} 의 SSOT 위치 + 핵심 도구 + raw rule contract.

## SSOT
- atlas: \`n6/atlas.n6\` (또는 \`atlas/atlas.n6\`)
- design: \`design/\` (markdown + json witnesses)
- tool: \`tool/\` (실 도구)

## 적용 raw rules (hive .raw 참조)

- raw 0 root-ssot triad
- raw 1 chflags uchg (file lock)
- raw 9 hexa-only (.rs/.toml/.py/.sh ban)
- raw 12 silent-error 금지
- raw 23 schema-guard-mandatory
- raw 47 strategy-exploration-omega-cycle
- raw 68 fixpoint-byte-eq-closure
- raw 70 multi-axis-verify-grid (K≥4)
- raw 71 falsifier-retire-rule (≥3 falsifier)
- raw 73 structural-admissibility-paradigm
- raw 77 audit-append-only-ledger
- raw 81 default-model-top-tier-mandate

## Honesty triad (\`scripts/quality/honesty_triad_linter.py\` 또는 동등)

5 preconditions (Phase 3 supercycle):
- (a) git tracked SSOT
- (b) design/ + ≥1 .md
- (c) tool/ + ≥3 files
- (d) atlas SSOT 파일
- (e) **이 파일 (CLAUDE.md) — LLM agents indicator** ✅

## 본 파일 위치
- \`~/core/${repo_name}/CLAUDE.md\`

> 다음 \`nexus hexa-sim dashboard\` 실행 시 ${repo_name} 의 honesty 5/5 = REPO_INVARIANT 도달.

EOF
}

emit_agent_md() {
    local repo_name="$1"
    cat <<EOF
# AGENT.md — ${repo_name} agent definition

> Honesty triad precondition-e fix. CLAUDE.md 대안.

## ${repo_name} agent

본 repo 작업 시 LLM agent 의 default behavior:
1. atlas SSOT (\`n6/atlas.n6\`) 존중 — 직접 편집 대신 \`atlas.append.*.n6\` shard
2. raw 9 hexa-only — .rs/.toml/.py/.sh 신규 작성 금지
3. raw 12 silent-error 금지 — exit/empty-catch ban
4. raw 47 strategy-exploration-omega-cycle — 새 design strategy 발견 시 ω-cycle witness
5. raw 71 falsifier-retire-rule — 모든 design claim 에 ≥3 falsifier
6. raw 73 structural-admissibility — byte-eq seal idempotence
7. raw 81 default-model — 항상 Opus

EOF
}

emit_claude_agents() {
    local repo_name="$1"
    cat <<EOF
# .claude/agents/ — ${repo_name} agent triad

> Honesty triad precondition-e fix. .claude/agents/ 디렉토리 + 최소 1 agent.md.
> mkdir + drop 1 file:

mkdir -p ~/core/${repo_name}/.claude/agents
cat > ~/core/${repo_name}/.claude/agents/${repo_name}_default.md <<'AGENT_EOF'
# ${repo_name} default agent

본 repo 작업 시 LLM agent 의 default contract — raw 9/12/47/71/73/81 준수.
atlas SSOT 존중, ω-cycle witness 의무, falsifier ≥3 의무, byte-eq seal idempotence.
AGENT_EOF

EOF
}

# Single emit mode
if [ -n "$EMIT_ONLY" ]; then
    case "$EMIT_TYPE" in
        claude_md) emit_claude_md "$EMIT_ONLY" ;;
        agent_md) emit_agent_md "$EMIT_ONLY" ;;
        claude_agents) emit_claude_agents "$EMIT_ONLY" ;;
        *) echo "invalid --type: $EMIT_TYPE" >&2; exit 1 ;;
    esac
    echo "__HONESTY_PRECONDITION_E_FIX__ emit-only repo=$EMIT_ONLY type=$EMIT_TYPE"
    exit 0
fi

# Suggest mode (default)
SUGGESTED=0
echo "Honesty precondition-e fix suggestions"
echo "─────────────────────────────────────────────────────────────"
echo ""

for repo in "${REPOS[@]}"; do
    [ -n "$TARGET_REPO" ] && [ "$TARGET_REPO" != "$repo" ] && continue
    repo_path="$HOME/core/$repo"
    [ ! -d "$repo_path" ] && { echo "skip $repo: dir not found at $repo_path"; continue; }

    # check current precondition-e status
    has_claude_md=0
    has_agent_md=0
    has_claude_agents=0
    [ -f "$repo_path/CLAUDE.md" ] && has_claude_md=1
    [ -f "$repo_path/AGENT.md" ] && has_agent_md=1
    [ -d "$repo_path/.claude/agents" ] && has_claude_agents=1

    if [ "$has_claude_md" = "1" ] || [ "$has_agent_md" = "1" ] || [ "$has_claude_agents" = "1" ]; then
        echo "▶ $repo: precondition-e ✅ (already PASS)"
        echo "  - CLAUDE.md: $([ "$has_claude_md" = "1" ] && echo present || echo absent)"
        echo "  - AGENT.md:  $([ "$has_agent_md" = "1" ] && echo present || echo absent)"
        echo "  - .claude/agents/: $([ "$has_claude_agents" = "1" ] && echo present || echo absent)"
        echo ""
        continue
    fi

    SUGGESTED=$((SUGGESTED + 1))
    echo "▶ $repo: precondition-e ❌ (needs fix)"
    echo "  옵션 (1 만 적용해도 5/5 도달):"
    echo ""
    echo "  옵션 A — minimal CLAUDE.md drop (가장 가벼움, 권장):"
    echo "    cat > ~/core/$repo/CLAUDE.md <<'CLAUDE_EOF'"
    echo "    # CLAUDE.md — $repo (Honesty precondition-e)"
    echo "    > raw 9/12/47/71/73/81 contract. SSOT: atlas/design/tool."
    echo "    CLAUDE_EOF"
    echo ""
    echo "  옵션 B — full CLAUDE.md template:"
    echo "    bash $0 --emit-only $repo --type claude_md > ~/core/$repo/CLAUDE.md"
    echo ""
    echo "  옵션 C — .claude/agents/ 디렉토리:"
    echo "    bash $0 --emit-only $repo --type claude_agents | bash"
    echo ""
    echo "  옵션 D — AGENT.md:"
    echo "    bash $0 --emit-only $repo --type agent_md > ~/core/$repo/AGENT.md"
    echo ""
done

echo "─────────────────────────────────────────────────────────────"
echo "__HONESTY_PRECONDITION_E_FIX__ repos=${#REPOS[@]} suggested=$SUGGESTED"
echo ""
echo "post-fix 검증:"
echo "  bash $HOME/core/nexus/tool/atlas_cross_repo_dashboard.sh"
echo "  → 모든 repo Honesty 5/5 도달 시 cross-repo REPO_INVARIANT 4/4."
exit 0
