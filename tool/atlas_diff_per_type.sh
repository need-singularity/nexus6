#!/usr/bin/env bash
# tool/atlas_diff_per_type.sh — Tier-2 i9 from improvement_ideas_omega_cycle (2026-04-26)
#
# git commit 별 atlas 변경 → @P/@C/@F/@L/@R/@S/@X/@M/@T/@E type 별 분류 emit.
# PR review 가속화 + atlas 진화 추적.
# self-host 회피 (bash + git, no hexa dep).
#
# usage:
#   tool/atlas_diff_per_type.sh                    # last commit 의 atlas diff
#   tool/atlas_diff_per_type.sh <commit>           # specific commit
#   tool/atlas_diff_per_type.sh --range <A>..<B>   # commit range
#   tool/atlas_diff_per_type.sh --since <date>     # since date (e.g. yesterday, 1.day, 2026-04-25)
#   tool/atlas_diff_per_type.sh --recent N         # last N commits with atlas changes
#
# exit codes: 0=PASS, 1=usage, 2=no atlas changes
# sentinel: __ATLAS_DIFF_PER_TYPE__ commits=N additions=A deletions=D
# origin: design/hexa_sim/2026-04-26_improvement_ideas_omega_cycle.json axis_i9

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$HOME/core/nexus}"

MODE="last"
COMMIT=""
RANGE=""
SINCE=""
RECENT=10

while [ $# -gt 0 ]; do
    case "$1" in
        --range) MODE="range"; RANGE="$2"; shift 2 ;;
        --since) MODE="since"; SINCE="$2"; shift 2 ;;
        --recent) MODE="recent"; RECENT="$2"; shift 2 ;;
        --help|-h)
            echo "usage: $0                          # last commit"
            echo "       $0 <commit>                 # specific commit"
            echo "       $0 --range <A>..<B>         # range"
            echo "       $0 --since <date|N.unit>    # since date"
            echo "       $0 --recent N               # last N atlas-touching commits"
            exit 0
            ;;
        --*) echo "unknown flag: $1" >&2; exit 1 ;;
        *)
            if [ -z "$COMMIT" ]; then MODE="single"; COMMIT="$1"; fi
            shift
            ;;
    esac
done

# Get atlas-affecting commits per mode
get_commits() {
    case "$MODE" in
        last)
            cd "$NEXUS_ROOT" && git log -n 1 --format="%h" -- 'n6/atlas.n6' 'n6/atlas.append.*.n6' 2>/dev/null
            ;;
        single)
            echo "$COMMIT"
            ;;
        range)
            cd "$NEXUS_ROOT" && git log "$RANGE" --format="%h" -- 'n6/atlas.n6' 'n6/atlas.append.*.n6' 2>/dev/null
            ;;
        since)
            cd "$NEXUS_ROOT" && git log --since="$SINCE" --format="%h" -- 'n6/atlas.n6' 'n6/atlas.append.*.n6' 2>/dev/null
            ;;
        recent)
            cd "$NEXUS_ROOT" && git log -n "$RECENT" --format="%h" -- 'n6/atlas.n6' 'n6/atlas.append.*.n6' 2>/dev/null
            ;;
    esac
}

# Classify diff lines by @type for one commit
classify_commit() {
    local commit="$1"
    cd "$NEXUS_ROOT" || return 1
    local subject
    subject=$(git log -n 1 --format="%s" "$commit" 2>/dev/null)
    if [ -z "$subject" ]; then
        echo "  (commit $commit not found)"
        return 1
    fi
    # Per-type counters
    local p_add=0 c_add=0 f_add=0 l_add=0 r_add=0 s_add=0 x_add=0 m_add=0 t_add=0 e_add=0
    local p_del=0 c_del=0 f_del=0 l_del=0 r_del=0 s_del=0 x_del=0 m_del=0 t_del=0 e_del=0
    local total_add=0 total_del=0
    # Use git show with diff filter for atlas files
    while IFS= read -r line; do
        # Match diff '+@<TYPE>' or '-@<TYPE>'
        local sign type
        sign=$(echo "$line" | cut -c1)
        type=$(echo "$line" | sed -nE 's/^[+\-]@([PCFLRSXMTE]) .*/\1/p')
        [ -z "$type" ] && continue
        if [ "$sign" = "+" ]; then
            total_add=$((total_add + 1))
            case "$type" in
                P) p_add=$((p_add + 1)) ;;
                C) c_add=$((c_add + 1)) ;;
                F) f_add=$((f_add + 1)) ;;
                L) l_add=$((l_add + 1)) ;;
                R) r_add=$((r_add + 1)) ;;
                S) s_add=$((s_add + 1)) ;;
                X) x_add=$((x_add + 1)) ;;
                M) m_add=$((m_add + 1)) ;;
                T) t_add=$((t_add + 1)) ;;
                E) e_add=$((e_add + 1)) ;;
            esac
        elif [ "$sign" = "-" ]; then
            total_del=$((total_del + 1))
            case "$type" in
                P) p_del=$((p_del + 1)) ;;
                C) c_del=$((c_del + 1)) ;;
                F) f_del=$((f_del + 1)) ;;
                L) l_del=$((l_del + 1)) ;;
                R) r_del=$((r_del + 1)) ;;
                S) s_del=$((s_del + 1)) ;;
                X) x_del=$((x_del + 1)) ;;
                M) m_del=$((m_del + 1)) ;;
                T) t_del=$((t_del + 1)) ;;
                E) e_del=$((e_del + 1)) ;;
            esac
        fi
    done < <(git show "$commit" -- 'n6/atlas.n6' 'n6/atlas.append.*.n6' 2>/dev/null | grep -E '^[+\-]@[PCFLRSXMTE] ')
    # Emit summary line if any atlas change
    if [ "$total_add" -eq 0 ] && [ "$total_del" -eq 0 ]; then
        return 0
    fi
    # Build per-type breakdown (only non-zero)
    local breakdown=""
    [ "$p_add" -gt 0 ] || [ "$p_del" -gt 0 ] && breakdown+=" P:+$p_add/-$p_del"
    [ "$c_add" -gt 0 ] || [ "$c_del" -gt 0 ] && breakdown+=" C:+$c_add/-$c_del"
    [ "$f_add" -gt 0 ] || [ "$f_del" -gt 0 ] && breakdown+=" F:+$f_add/-$f_del"
    [ "$l_add" -gt 0 ] || [ "$l_del" -gt 0 ] && breakdown+=" L:+$l_add/-$l_del"
    [ "$r_add" -gt 0 ] || [ "$r_del" -gt 0 ] && breakdown+=" R:+$r_add/-$r_del"
    [ "$s_add" -gt 0 ] || [ "$s_del" -gt 0 ] && breakdown+=" S:+$s_add/-$s_del"
    [ "$x_add" -gt 0 ] || [ "$x_del" -gt 0 ] && breakdown+=" X:+$x_add/-$x_del"
    [ "$m_add" -gt 0 ] || [ "$m_del" -gt 0 ] && breakdown+=" M:+$m_add/-$m_del"
    [ "$t_add" -gt 0 ] || [ "$t_del" -gt 0 ] && breakdown+=" T:+$t_add/-$t_del"
    [ "$e_add" -gt 0 ] || [ "$e_del" -gt 0 ] && breakdown+=" E:+$e_add/-$e_del"
    printf "%s  +%d/-%d %s  %s\n" "$commit" "$total_add" "$total_del" "$breakdown" "$subject"
    # Update global counters via stdout (caller parses)
    echo "$total_add $total_del" >&2
}

# Aggregate
COMMITS=$(get_commits)
if [ -z "$COMMITS" ]; then
    echo "__ATLAS_DIFF_PER_TYPE__ commits=0 additions=0 deletions=0 (no atlas changes in scope)"
    exit 2
fi

TOTAL_COMMITS=0
TOTAL_ADD=0
TOTAL_DEL=0
echo "atlas changes by @type per commit (mode=$MODE):"
echo "---"
while IFS= read -r commit; do
    [ -z "$commit" ] && continue
    TOTAL_COMMITS=$((TOTAL_COMMITS + 1))
    # Single call: capture stderr counts to tmp + stdout to terminal
    counts_tmp=$(mktemp -t adpt.XXXXX)
    classify_commit "$commit" 2>"$counts_tmp"
    while IFS= read -r counts; do
        local_add=$(echo "$counts" | cut -d' ' -f1)
        local_del=$(echo "$counts" | cut -d' ' -f2)
        if [ -n "$local_add" ]; then TOTAL_ADD=$((TOTAL_ADD + local_add)); fi
        if [ -n "$local_del" ]; then TOTAL_DEL=$((TOTAL_DEL + local_del)); fi
    done < "$counts_tmp"
    rm -f "$counts_tmp"
done <<< "$COMMITS"
echo "---"
echo "__ATLAS_DIFF_PER_TYPE__ commits=$TOTAL_COMMITS additions=$TOTAL_ADD deletions=$TOTAL_DEL"
exit 0
