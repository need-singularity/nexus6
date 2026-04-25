#!/usr/bin/env bash
# tool/atlas_cross_repo_dashboard.sh — Tier-2 i13 from improvement_ideas_omega_cycle (2026-04-26)
#
# 4-repo (nexus + n6-architecture + anima + hexa-lang) atlas state 통합 status dashboard
# (markdown emit). Honesty triad 6 preconditions per-repo + atlas size + last commit.
# self-host 회피 (bash + git, no hexa dep).
#
# usage: tool/atlas_cross_repo_dashboard.sh [--out PATH] [--md|--text] [--legacy-5]
#   --out PATH   emit to file (default: stdout)
#   --md         markdown format (default)
#   --text       plain text
#   --legacy-5   keep N/5 honesty score (drop precondition (f) defense surface). default: N/6
#
# exit codes: 0=PASS, 1=usage
# sentinel: __ATLAS_CROSS_REPO_DASHBOARD__ repos=R total_atlas_lines=L total_facts=F honesty_pass=N/R honesty_5_5=X honesty_6_6=Y mode=6|legacy5
# origin: design/hexa_sim/2026-04-26_improvement_ideas_omega_cycle.json axis_i13
# extension: design/hexa_sim/2026-04-26_precondition_f_defense_surface_omega_cycle.json (raw 80 backward-compat)

set -uo pipefail

OUTPUT=""
FORMAT="md"
MODE="6"   # default: include precondition (f). --legacy-5 sets MODE=5.

while [ $# -gt 0 ]; do
    case "$1" in
        --out) OUTPUT="$2"; shift 2 ;;
        --md) FORMAT="md"; shift ;;
        --text) FORMAT="text"; shift ;;
        --legacy-5) MODE="5"; shift ;;
        --help|-h)
            echo "usage: $0 [--out PATH] [--md|--text] [--legacy-5]"
            exit 0
            ;;
        *) echo "unknown: $1" >&2; exit 1 ;;
    esac
done

# Repo registry: name | path | atlas_relpath | honesty_check_path
REPOS=(
    "nexus|$HOME/core/nexus|n6/atlas.n6|.claude/agents"
    "n6-architecture|$HOME/core/n6-architecture|atlas/atlas.n6|.claude/agents"
    "anima|$HOME/core/anima|n6/atlas.n6|.claude/agents"
    "hexa-lang|$HOME/core/hexa-lang|n6/atlas.n6|.claude/agents"
)

# 5 Honesty preconditions (per Phase 3 supercycle)
check_precondition_a() { [ -d "$1" ] && [ -f "$1/.git/HEAD" ] && echo PASS || echo FAIL; }   # SSOT exists + git
check_precondition_b() {                                                                       # design corpus (generous: design/ OR docs/ OR papers/ OR reports/, 어디든 ≥1 .md)
    for sub in design docs papers reports; do
        if [ -d "$1/$sub" ] && [ "$(find "$1/$sub" -maxdepth 3 -name "*.md" 2>/dev/null | wc -l | tr -d ' ')" -gt 0 ]; then
            echo PASS; return
        fi
    done
    echo FAIL
}
check_precondition_c() {                                                                       # tool/ ≥3 files (generous: tool/ OR scripts/ OR bin/)
    for sub in tool scripts bin; do
        if [ -d "$1/$sub" ] && [ "$(find "$1/$sub" -maxdepth 2 -type f 2>/dev/null | wc -l | tr -d ' ')" -ge 3 ]; then
            echo PASS; return
        fi
    done
    echo FAIL
}
check_precondition_d() {                                                                       # atlas SSOT (generous: spec'd path OR alternates)
    [ -f "$1/$2" ] && echo PASS && return
    # alternates: n6/atlas.n6, atlas/atlas.n6, atlas.n6
    for alt in n6/atlas.n6 atlas/atlas.n6 atlas.n6; do
        [ -f "$1/$alt" ] && echo PASS && return
    done
    echo FAIL
}
check_precondition_e() {                                                                       # LLM agents (.claude/agents/ or CLAUDE.md or AGENT.md)
    if [ -d "$1/.claude/agents" ] || [ -f "$1/CLAUDE.md" ] || [ -f "$1/AGENT.md" ]; then echo PASS; else echo FAIL; fi
}
check_precondition_f() {                                                                       # defense surface declared (canonical security/threat surface, ≥1 of 8 paths)
    # raw 73 admissibility: non-trivial — surveys 8 canonical paths covering top-level / doc / docs / design / state / tool conventions.
    # PASS criteria: ANY of:
    #   1) <repo>/SECURITY*  (top-level SECURITY.md / SECURITY_AUDIT.md / etc, glob)
    #   2) <repo>/doc/security/*    (hexa-lang pattern)
    #   3) <repo>/docs/security/*
    #   4) <repo>/design/security/*
    #   5) <repo>/design/SECURITY_AUDIT.md
    #   6) <repo>/design/hexa_sim/SECURITY_AUDIT.md  (nexus pattern)
    #   7) <repo>/state/security_*.json             (anima pattern)
    #   8) <repo>/tool/security_*                    (nexus tool/security_scan.hexa pattern)
    local r="$1"
    # 1) top-level SECURITY*
    for f in "$r"/SECURITY*; do [ -e "$f" ] && echo PASS && return; done
    # 2-4) doc/security, docs/security, design/security dirs with ≥1 file
    for sub in doc/security docs/security design/security; do
        if [ -d "$r/$sub" ] && [ "$(find "$r/$sub" -maxdepth 2 -type f 2>/dev/null | wc -l | tr -d ' ')" -gt 0 ]; then
            echo PASS; return
        fi
    done
    # 5) design/SECURITY_AUDIT.md
    [ -f "$r/design/SECURITY_AUDIT.md" ] && echo PASS && return
    # 6) design/hexa_sim/SECURITY_AUDIT.md  (nexus)
    [ -f "$r/design/hexa_sim/SECURITY_AUDIT.md" ] && echo PASS && return
    # 7) state/security_*.json
    for f in "$r"/state/security_*.json; do [ -e "$f" ] && echo PASS && return; done
    # 8) tool/security_*
    for f in "$r"/tool/security_*; do [ -e "$f" ] && echo PASS && return; done
    echo FAIL
}

emit() { if [ -n "$OUTPUT" ]; then echo "$1" >> "$OUTPUT"; else echo "$1"; fi; }

# Reset output file
[ -n "$OUTPUT" ] && > "$OUTPUT"

now_iso=$(date -u +%Y-%m-%dT%H:%M:%SZ)

DENOM="$MODE"   # 5 (legacy) or 6 (default with precondition (f))

if [ "$FORMAT" = "md" ]; then
    emit "# Cross-Repo Atlas Dashboard"
    emit ""
    emit "> generated: \`$now_iso\` (UTC) by \`tool/atlas_cross_repo_dashboard.sh\` (Tier-2 i13, mode=$MODE)"
    emit ""
    emit "## Repo health table"
    emit ""
    emit "| Repo | Atlas | Lines | Entries | Last Commit | Honesty $DENOM/$DENOM |"
    emit "|------|-------|------:|--------:|-------------|------------:|"
fi

TOTAL_REPOS=0
TOTAL_LINES=0
TOTAL_FACTS=0
TOTAL_HONESTY=0       # full-pass count (N/DENOM)
TOTAL_HONESTY_5_5=0   # always tracked: how many repos hit 5/5 (legacy axis)
TOTAL_HONESTY_6_6=0   # always tracked: how many repos hit 6/6 (extended axis)

for entry in "${REPOS[@]}"; do
    IFS='|' read -r name path atlas_rel _ <<< "$entry"
    if [ ! -d "$path" ]; then continue; fi
    TOTAL_REPOS=$((TOTAL_REPOS + 1))

    atlas_path="$path/$atlas_rel"
    lines=0
    entries=0
    last_commit_short=""
    last_commit_ts=""
    if [ -f "$atlas_path" ]; then
        lines=$(wc -l < "$atlas_path" | tr -d ' ')
        entries=$(grep -cE '^@[PCFLRSXMTE] ' "$atlas_path" 2>/dev/null || echo 0)
        last_commit_short=$(cd "$path" && git log -n 1 --format="%h" -- "$atlas_rel" 2>/dev/null)
        last_commit_ts=$(cd "$path" && git log -n 1 --format="%ai" -- "$atlas_rel" 2>/dev/null | cut -c1-16)
    fi
    TOTAL_LINES=$((TOTAL_LINES + lines))
    TOTAL_FACTS=$((TOTAL_FACTS + entries))

    # Honesty preconditions (a..e always; f added unless --legacy-5)
    pa=$(check_precondition_a "$path")
    pb=$(check_precondition_b "$path")
    pc=$(check_precondition_c "$path")
    pd=$(check_precondition_d "$path" "$atlas_rel")
    pe=$(check_precondition_e "$path")
    pf=$(check_precondition_f "$path")
    pass_5=0
    [ "$pa" = "PASS" ] && pass_5=$((pass_5 + 1))
    [ "$pb" = "PASS" ] && pass_5=$((pass_5 + 1))
    [ "$pc" = "PASS" ] && pass_5=$((pass_5 + 1))
    [ "$pd" = "PASS" ] && pass_5=$((pass_5 + 1))
    [ "$pe" = "PASS" ] && pass_5=$((pass_5 + 1))
    pass_6=$pass_5
    [ "$pf" = "PASS" ] && pass_6=$((pass_6 + 1))

    [ "$pass_5" = "5" ] && TOTAL_HONESTY_5_5=$((TOTAL_HONESTY_5_5 + 1))
    [ "$pass_6" = "6" ] && TOTAL_HONESTY_6_6=$((TOTAL_HONESTY_6_6 + 1))

    if [ "$MODE" = "5" ]; then
        pass_count=$pass_5
        [ "$pass_count" = "5" ] && TOTAL_HONESTY=$((TOTAL_HONESTY + 1))
    else
        pass_count=$pass_6
        [ "$pass_count" = "6" ] && TOTAL_HONESTY=$((TOTAL_HONESTY + 1))
    fi

    if [ "$FORMAT" = "md" ]; then
        atlas_display="\`$atlas_rel\`"
        if [ ! -f "$atlas_path" ]; then atlas_display="(missing)"; fi
        emit "| **$name** | $atlas_display | $lines | $entries | \`$last_commit_short\` $last_commit_ts | $pass_count/$DENOM |"
    else
        if [ "$MODE" = "5" ]; then
            emit "$name  atlas=$atlas_rel  lines=$lines  entries=$entries  last=$last_commit_short@$last_commit_ts  honesty=$pass_count/5 (a=$pa b=$pb c=$pc d=$pd e=$pe)"
        else
            emit "$name  atlas=$atlas_rel  lines=$lines  entries=$entries  last=$last_commit_short@$last_commit_ts  honesty=$pass_count/6 (a=$pa b=$pb c=$pc d=$pd e=$pe f=$pf)"
        fi
    fi
done

if [ "$FORMAT" = "md" ]; then
    emit ""
    emit "## Aggregate"
    emit ""
    emit "- **repos checked**: $TOTAL_REPOS"
    emit "- **total atlas lines** (cumulative): $TOTAL_LINES"
    emit "- **total atlas facts** (cumulative): $TOTAL_FACTS"
    emit "- **honesty $DENOM/$DENOM (REPO_INVARIANT, mode=$MODE)**: $TOTAL_HONESTY/$TOTAL_REPOS"
    emit "- **honesty 5/5 (legacy axis, always tracked)**: $TOTAL_HONESTY_5_5/$TOTAL_REPOS"
    emit "- **honesty 6/6 (extended axis, always tracked)**: $TOTAL_HONESTY_6_6/$TOTAL_REPOS"
    emit ""
    emit "## Honesty preconditions"
    emit ""
    emit "1. **(a)** SSOT exists + git tracked (\`.git/HEAD\` 존재)"
    emit "2. **(b)** \`design/\` dir 존재 + ≥1 .md"
    emit "3. **(c)** \`tool/\` dir + ≥3 files"
    emit "4. **(d)** atlas SSOT 파일 존재"
    emit "5. **(e)** LLM agents indicator (\`.claude/agents/\` OR \`CLAUDE.md\` OR \`AGENT.md\`)"
    emit "6. **(f)** defense surface declared — ANY of 8 canonical paths: \`SECURITY*\` (top-level) / \`doc/security/*\` / \`docs/security/*\` / \`design/security/*\` / \`design/SECURITY_AUDIT.md\` / \`design/hexa_sim/SECURITY_AUDIT.md\` / \`state/security_*.json\` / \`tool/security_*\`"
    emit ""
    emit "6/6 PASS = \`REPO_INVARIANT_EXTENDED\` (Honesty triad + defense surface)."
    emit "5/5 PASS (mode=6 → 5/6) = \`REPO_INVARIANT\` legacy (defense surface absent)."
    emit "≤4/$DENOM = \`PARTIAL\` (precondition gap 명시 필요)."
    emit ""
    emit "## Improvements"
    emit ""
    emit "- 본 dashboard 는 \`tool/atlas_cross_repo_dashboard.sh\`"
    emit "- regenerate (mode=6, default): \`bash tool/atlas_cross_repo_dashboard.sh --out design/hexa_sim/cross_repo_dashboard.md\`"
    emit "- regenerate (mode=5, legacy): \`bash tool/atlas_cross_repo_dashboard.sh --legacy-5 --out design/hexa_sim/cross_repo_dashboard_legacy5.md\`"
    emit "- 수동 cron: \`crontab -e\` 에 daily entry 등록 OR git pre-push hook"
fi

emit ""
emit "__ATLAS_CROSS_REPO_DASHBOARD__ repos=$TOTAL_REPOS total_atlas_lines=$TOTAL_LINES total_facts=$TOTAL_FACTS honesty_pass=$TOTAL_HONESTY/$TOTAL_REPOS honesty_5_5=$TOTAL_HONESTY_5_5 honesty_6_6=$TOTAL_HONESTY_6_6 mode=$MODE"
# raw 66 trailer: reason=cross-repo honesty audit; fix=if FAIL, populate missing precondition (atlas SSOT, LLM agents indicator, or defense surface canonical path).
exit 0
