#!/usr/bin/env bash
# tool/atlas_index.sh — Tier-1 i1 from improvement_ideas_omega_cycle (2026-04-26)
#
# atlas.n6 + atlas.append.*.n6 의 id → (line_no, type, shard) 인덱스 빌드.
# state/atlas_index.tsv (TSV) 으로 emit.
# atlas-ingest 도구의 _check_dup_in_atlas (현 grep O(file_size)) 가속용.
# 309 fact 누적 후 dedup grep 폭증 회피 (총 atlas 65,450 lines).
# self-host 회피 (bash + grep, no hexa dep).
#
# usage:
#   tool/atlas_index.sh                       # build full index
#   tool/atlas_index.sh --lookup <id>         # query single id
#   tool/atlas_index.sh --stats               # index stats
#   tool/atlas_index.sh --refresh             # rebuild
#
# exit codes: 0=PASS, 1=usage, 2=lookup miss
# sentinel: __ATLAS_INDEX__ entries=N shards=S build_ms=M index=<path>
# origin: design/hexa_sim/2026-04-26_improvement_ideas_omega_cycle.json axis_i1

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$HOME/core/nexus}"
ATLAS_MAIN="$NEXUS_ROOT/n6/atlas.n6"
ATLAS_SHARDS_GLOB="$NEXUS_ROOT/n6/atlas.append.*.n6"
INDEX_PATH="$NEXUS_ROOT/state/atlas_index.tsv"
mkdir -p "$NEXUS_ROOT/state" 2>/dev/null

MODE="build"
LOOKUP_ID=""

while [ $# -gt 0 ]; do
    case "$1" in
        --lookup) MODE="lookup"; LOOKUP_ID="$2"; shift 2 ;;
        --stats) MODE="stats"; shift ;;
        --refresh) MODE="build"; shift ;;
        --help|-h)
            echo "usage: $0                       # build/refresh index"
            echo "       $0 --lookup <id>         # single id query"
            echo "       $0 --stats               # index stats"
            exit 0
            ;;
        *) echo "unknown: $1" >&2; exit 1 ;;
    esac
done

build_index() {
    local start_ms
    start_ms=$(date +%s%N 2>/dev/null | cut -c1-13 || date +%s000)

    # Header
    echo -e "id\ttype\tline\tshard" > "$INDEX_PATH"

    local shards=()
    [ -f "$ATLAS_MAIN" ] && shards+=("$ATLAS_MAIN")
    for f in $ATLAS_SHARDS_GLOB; do
        [ -f "$f" ] && shards+=("$f")
    done

    local total_entries=0
    for shard in "${shards[@]}"; do
        local rel_shard
        rel_shard="${shard#$NEXUS_ROOT/}"
        # grep all @<TYPE> entries with line numbers + extract id
        while IFS=: read -r line_no line_txt; do
            [ -z "$line_txt" ] && continue
            local type id
            type=$(echo "$line_txt" | sed -nE 's/^@([PCFLRSXMTE]) .*/\1/p')
            id=$(echo "$line_txt" | sed -nE 's/^@[PCFLRSXMTE] ([^ ]+) =.*/\1/p')
            [ -z "$id" ] && continue
            printf "%s\t%s\t%s\t%s\n" "$id" "$type" "$line_no" "$rel_shard" >> "$INDEX_PATH"
            total_entries=$((total_entries + 1))
        done < <(grep -nE '^@[PCFLRSXMTE] [^ ]+ =' "$shard" 2>/dev/null)
    done

    local end_ms
    end_ms=$(date +%s%N 2>/dev/null | cut -c1-13 || date +%s000)
    local build_ms=$((end_ms - start_ms))

    echo "atlas index built:"
    echo "  entries: $total_entries"
    echo "  shards:  ${#shards[@]}"
    echo "  path:    $INDEX_PATH"
    echo "  size:    $(wc -c < "$INDEX_PATH" | tr -d ' ') bytes"
    echo "  time:    ${build_ms} ms"
    echo "__ATLAS_INDEX__ entries=$total_entries shards=${#shards[@]} build_ms=$build_ms index=$INDEX_PATH"
}

lookup_id() {
    if [ ! -f "$INDEX_PATH" ]; then
        echo "index not built — run: $0  (no args)" >&2
        return 1
    fi
    local matches
    matches=$(awk -F'\t' -v id="$LOOKUP_ID" '$1==id {print}' "$INDEX_PATH")
    if [ -z "$matches" ]; then
        echo "__ATLAS_INDEX__ FAIL id='$LOOKUP_ID' status=NOT_FOUND"
        return 2
    fi
    echo "$matches" | while IFS=$'\t' read -r id type line shard; do
        printf "  @%s  id=%s  shard=%s  line=%s\n" "$type" "$id" "$shard" "$line"
    done
    local match_count
    match_count=$(echo "$matches" | wc -l | tr -d ' ')
    echo "__ATLAS_INDEX__ id=$LOOKUP_ID matches=$match_count"
    return 0
}

stats_index() {
    if [ ! -f "$INDEX_PATH" ]; then
        echo "index not built — run: $0" >&2
        return 1
    fi
    local total
    total=$(($(wc -l < "$INDEX_PATH") - 1))  # minus header
    echo "atlas index stats:"
    echo "  total entries: $total"
    echo ""
    echo "  per-type distribution:"
    tail -n +2 "$INDEX_PATH" | awk -F'\t' '{print $2}' | sort | uniq -c | sort -rn | sed 's/^/    /'
    echo ""
    echo "  per-shard distribution:"
    tail -n +2 "$INDEX_PATH" | awk -F'\t' '{print $4}' | sort | uniq -c | sort -rn | sed 's/^/    /'
    echo "  index size: $(wc -c < "$INDEX_PATH" | tr -d ' ') bytes"
    echo "__ATLAS_INDEX__ total=$total path=$INDEX_PATH"
}

case "$MODE" in
    build) build_index ;;
    lookup) lookup_id ;;
    stats) stats_index ;;
esac
