#!/usr/bin/env bash
# tool/atlas_cross_repo_dashboard.sh — Tier-2 i13 from improvement_ideas_omega_cycle (2026-04-26)
#
# 4-repo (nexus + n6-architecture + anima + hexa-lang) atlas state 통합 status dashboard
# (markdown emit). Honesty triad 5 preconditions per-repo + atlas size + last commit.
# self-host 회피 (bash + git, no hexa dep).
#
# usage: tool/atlas_cross_repo_dashboard.sh [--out PATH] [--md|--text]
#   --out PATH  emit to file (default: stdout)
#   --md        markdown format (default)
#   --text      plain text
#
# exit codes: 0=PASS, 1=usage
# sentinel: __ATLAS_CROSS_REPO_DASHBOARD__ repos=R total_atlas_lines=L total_facts=F
# origin: design/hexa_sim/2026-04-26_improvement_ideas_omega_cycle.json axis_i13

set -uo pipefail

OUTPUT=""
FORMAT="md"

while [ $# -gt 0 ]; do
    case "$1" in
        --out) OUTPUT="$2"; shift 2 ;;
        --md) FORMAT="md"; shift ;;
        --text) FORMAT="text"; shift ;;
        --help|-h)
            echo "usage: $0 [--out PATH] [--md|--text]"
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
check_precondition_b() {                                                                       # design dir exists
    if [ -d "$1/design" ] && [ "$(find "$1/design" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')" -gt 0 ]; then echo PASS; else echo FAIL; fi
}
check_precondition_c() {                                                                       # tool/ ≥3 files
    if [ -d "$1/tool" ] && [ "$(find "$1/tool" -maxdepth 1 -type f 2>/dev/null | wc -l | tr -d ' ')" -ge 3 ]; then echo PASS; else echo FAIL; fi
}
check_precondition_d() {                                                                       # atlas SSOT
    [ -f "$1/$2" ] && echo PASS || echo FAIL
}
check_precondition_e() {                                                                       # LLM agents (.claude/agents/ or CLAUDE.md or AGENT.md)
    if [ -d "$1/.claude/agents" ] || [ -f "$1/CLAUDE.md" ] || [ -f "$1/AGENT.md" ]; then echo PASS; else echo FAIL; fi
}

emit() { if [ -n "$OUTPUT" ]; then echo "$1" >> "$OUTPUT"; else echo "$1"; fi; }

# Reset output file
[ -n "$OUTPUT" ] && > "$OUTPUT"

now_iso=$(date -u +%Y-%m-%dT%H:%M:%SZ)

if [ "$FORMAT" = "md" ]; then
    emit "# Cross-Repo Atlas Dashboard"
    emit ""
    emit "> generated: \`$now_iso\` (UTC) by \`tool/atlas_cross_repo_dashboard.sh\` (Tier-2 i13)"
    emit ""
    emit "## Repo health table"
    emit ""
    emit "| Repo | Atlas | Lines | Entries | Last Commit | Honesty 5/5 |"
    emit "|------|-------|------:|--------:|-------------|------------:|"
fi

TOTAL_REPOS=0
TOTAL_LINES=0
TOTAL_FACTS=0
TOTAL_HONESTY=0

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

    # Honesty 5/5
    pa=$(check_precondition_a "$path")
    pb=$(check_precondition_b "$path")
    pc=$(check_precondition_c "$path")
    pd=$(check_precondition_d "$path" "$atlas_rel")
    pe=$(check_precondition_e "$path")
    pass_count=0
    [ "$pa" = "PASS" ] && pass_count=$((pass_count + 1))
    [ "$pb" = "PASS" ] && pass_count=$((pass_count + 1))
    [ "$pc" = "PASS" ] && pass_count=$((pass_count + 1))
    [ "$pd" = "PASS" ] && pass_count=$((pass_count + 1))
    [ "$pe" = "PASS" ] && pass_count=$((pass_count + 1))
    [ "$pass_count" = "5" ] && TOTAL_HONESTY=$((TOTAL_HONESTY + 1))

    if [ "$FORMAT" = "md" ]; then
        atlas_display="\`$atlas_rel\`"
        if [ ! -f "$atlas_path" ]; then atlas_display="(missing)"; fi
        emit "| **$name** | $atlas_display | $lines | $entries | \`$last_commit_short\` $last_commit_ts | $pass_count/5 |"
    else
        emit "$name  atlas=$atlas_rel  lines=$lines  entries=$entries  last=$last_commit_short@$last_commit_ts  honesty=$pass_count/5 (a=$pa b=$pb c=$pc d=$pd e=$pe)"
    fi
done

if [ "$FORMAT" = "md" ]; then
    emit ""
    emit "## Aggregate"
    emit ""
    emit "- **repos checked**: $TOTAL_REPOS"
    emit "- **total atlas lines** (cumulative): $TOTAL_LINES"
    emit "- **total atlas facts** (cumulative): $TOTAL_FACTS"
    emit "- **honesty 5/5 (REPO_INVARIANT)**: $TOTAL_HONESTY/$TOTAL_REPOS"
    emit ""
    emit "## Honesty preconditions (per Phase 3 supercycle)"
    emit ""
    emit "1. **(a)** SSOT exists + git tracked (\`.git/HEAD\` 존재)"
    emit "2. **(b)** \`design/\` dir 존재 + ≥1 .md"
    emit "3. **(c)** \`tool/\` dir + ≥3 files"
    emit "4. **(d)** atlas SSOT 파일 존재"
    emit "5. **(e)** LLM agents indicator (\`.claude/agents/\` OR \`CLAUDE.md\` OR \`AGENT.md\`)"
    emit ""
    emit "5/5 PASS = \`REPO_INVARIANT\` (Honesty triad portable to other repos)."
    emit "≤4/5 = \`PARTIAL\` (precondition gap 명시 필요)."
    emit ""
    emit "## Improvements"
    emit ""
    emit "- 본 dashboard 는 \`tool/atlas_cross_repo_dashboard.sh\`"
    emit "- regenerate: \`bash tool/atlas_cross_repo_dashboard.sh --out design/hexa_sim/cross_repo_dashboard.md\`"
    emit "- 수동 cron: \`crontab -e\` 에 daily entry 등록 OR git pre-push hook"
fi

emit ""
emit "__ATLAS_CROSS_REPO_DASHBOARD__ repos=$TOTAL_REPOS total_atlas_lines=$TOTAL_LINES total_facts=$TOTAL_FACTS honesty_pass=$TOTAL_HONESTY/$TOTAL_REPOS"
exit 0
