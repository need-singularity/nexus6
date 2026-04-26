#!/usr/bin/env bash
# tool/atlas_search.sh — Tier-1 i8 from improvement_ideas_omega_cycle (2026-04-26)
#
# atlas.n6 + atlas.append.*.n6 facts 의 통합 search/browse. self-host 회피
# (bash + grep, no hexa dep — runtime down 시에도 작동).
#
# 309 facts (4-repo absorption + hexa-sim shard) 누적 후 discoverability 향상.
#
# usage:
#   tool/atlas_search.sh <pattern> [--type T] [--grade G] [--source S] [--limit N]
#   tool/atlas_search.sh --list-shards
#   tool/atlas_search.sh --stats
#
# pattern: id / expr / domain 에 대한 grep 패턴 (case-insensitive)
# --type T:    filter by type (P/C/F/L/R/S/X/M/T/E)
# --grade G:   filter by grade prefix (e.g. "11", "10*", "11*REPO_INVARIANT")
# --source S:  filter by source bridge/repo (substring match in source line)
# --limit N:   max results (default 20)
#
# exit codes: 0=match found, 1=usage, 2=no match
# sentinel: __ATLAS_SEARCH__ matched=N total_scanned=K shards=S
# origin: design/hexa_sim/2026-04-26_improvement_ideas_omega_cycle.json axis_i8

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$HOME/core/nexus}"
ATLAS_MAIN="$NEXUS_ROOT/n6/atlas.n6"
ATLAS_SHARDS_GLOB="$NEXUS_ROOT/n6/atlas.append.*.n6"

PATTERN=""
TYPE_FILTER=""
GRADE_FILTER=""
SOURCE_FILTER=""
LIMIT=20
LIST_SHARDS=0
STATS_MODE=0

while [ $# -gt 0 ]; do
    case "$1" in
        --type) TYPE_FILTER="$2"; shift 2 ;;
        --grade) GRADE_FILTER="$2"; shift 2 ;;
        --source) SOURCE_FILTER="$2"; shift 2 ;;
        --limit) LIMIT="$2"; shift 2 ;;
        --list-shards) LIST_SHARDS=1; shift ;;
        --stats) STATS_MODE=1; shift ;;
        --help|-h)
            echo "usage: $0 <pattern> [--type T] [--grade G] [--source S] [--limit N]"
            echo "       $0 --list-shards"
            echo "       $0 --stats"
            echo ""
            echo "examples:"
            echo "  $0 alpha                    # search id/expr/domain for 'alpha'"
            echo "  $0 perfect --type F         # only @F entries matching 'perfect'"
            echo "  $0 . --grade 11             # all [11*] entries"
            echo "  $0 carbon --source pubchem  # carbon entries from pubchem source"
            echo "  $0 --stats                  # type+grade distribution across shards"
            exit 0
            ;;
        --*)
            echo "unknown flag: $1" >&2
            exit 1
            ;;
        *)
            if [ -z "$PATTERN" ]; then PATTERN="$1"; else echo "extra arg: $1" >&2; exit 1; fi
            shift
            ;;
    esac
done

# Build shard list
SHARDS=()
[ -f "$ATLAS_MAIN" ] && SHARDS+=("$ATLAS_MAIN")
for f in $ATLAS_SHARDS_GLOB; do
    [ -f "$f" ] && SHARDS+=("$f")
done

if [ ${#SHARDS[@]} -eq 0 ]; then
    echo "__ATLAS_SEARCH__ FAIL no atlas files found at $NEXUS_ROOT/n6/" >&2
    exit 2
fi

# --list-shards mode
if [ "$LIST_SHARDS" = "1" ]; then
    echo "atlas shards (${#SHARDS[@]} total):"
    for s in "${SHARDS[@]}"; do
        local_lines=$(wc -l < "$s" 2>/dev/null | tr -d ' ')
        local_entries=$({ grep -cE '^@[PCFLRSXMTE] ' "$s" 2>/dev/null || true; } | head -n1)
        local_entries=${local_entries:-0}
        printf "  %6d lines  %4d entries  %s\n" "$local_lines" "$local_entries" "$(basename "$s")"
    done
    echo "__ATLAS_SEARCH__ shards=${#SHARDS[@]}"
    exit 0
fi

# --stats mode
if [ "$STATS_MODE" = "1" ]; then
    echo "atlas stats across ${#SHARDS[@]} shards:"
    echo ""
    echo "TYPE distribution:"
    grep -hE '^@[PCFLRSXMTE] ' "${SHARDS[@]}" 2>/dev/null | awk '{print $1}' | sort | uniq -c | sort -rn
    echo ""
    echo "GRADE distribution (top 20):"
    grep -hoE '\[[0-9.\*\!\?A-Z_+]+\]' "${SHARDS[@]}" 2>/dev/null | sort | uniq -c | sort -rn | head -20
    TOTAL_ENTRIES=$(grep -chE '^@[PCFLRSXMTE] ' "${SHARDS[@]}" 2>/dev/null | awk '{s+=$1}END{print s}')
    echo ""
    echo "__ATLAS_SEARCH__ stats shards=${#SHARDS[@]} total_entries=$TOTAL_ENTRIES"
    exit 0
fi

# Normal search
if [ -z "$PATTERN" ]; then
    echo "usage: $0 <pattern> [filters]" >&2
    echo "       $0 --help" >&2
    exit 1
fi

# Build search regex: match @<TYPE> or trailer line
# Filter: TYPE if set, else any of PCFLRSXMTE
TYPE_RE="[PCFLRSXMTE]"
if [ -n "$TYPE_FILTER" ]; then
    TYPE_RE="${TYPE_FILTER}"
fi

GREP_BASE="grep -inE"
HEADER_PATTERN="^@${TYPE_RE} [^=]*${PATTERN}[^=]*="

MATCHED=0
RESULT_BUF=""
for shard in "${SHARDS[@]}"; do
    while IFS=: read -r line_no line_txt; do
        if [ -z "$line_txt" ]; then continue; fi
        # Apply grade filter
        if [ -n "$GRADE_FILTER" ]; then
            if ! echo "$line_txt" | grep -q "\[${GRADE_FILTER}"; then continue; fi
        fi
        # Apply source filter — check 2-3 lines after for matching source
        if [ -n "$SOURCE_FILTER" ]; then
            CONTEXT=$(awk -v ln="$line_no" -v src="$SOURCE_FILTER" 'NR>=ln && NR<=ln+5 {print}' "$shard" 2>/dev/null)
            if ! echo "$CONTEXT" | grep -qi "$src"; then continue; fi
        fi
        MATCHED=$((MATCHED + 1))
        if [ "$MATCHED" -le "$LIMIT" ]; then
            printf "%s:%d: %s\n" "$(basename "$shard")" "$line_no" "$line_txt"
        fi
        if [ "$MATCHED" -ge "$LIMIT" ]; then break; fi
    done < <($GREP_BASE "$HEADER_PATTERN" "$shard" 2>/dev/null || true)
    if [ "$MATCHED" -ge "$LIMIT" ]; then break; fi
done

TOTAL_LINES=0
for s in "${SHARDS[@]}"; do
    local_lines=$(wc -l < "$s" 2>/dev/null | tr -d ' ')
    TOTAL_LINES=$((TOTAL_LINES + local_lines))
done

if [ "$MATCHED" -eq 0 ]; then
    echo "__ATLAS_SEARCH__ matched=0 total_scanned=$TOTAL_LINES shards=${#SHARDS[@]}"
    exit 2
fi

echo ""
if [ "$MATCHED" -gt "$LIMIT" ]; then
    echo "(showing first $LIMIT of $MATCHED matches; use --limit N for more)"
fi
echo "__ATLAS_SEARCH__ matched=$MATCHED total_scanned=$TOTAL_LINES shards=${#SHARDS[@]}"
exit 0
