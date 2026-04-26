#!/usr/bin/env bash
# tool/atlas_provenance.sh — Tier-2 i15 from improvement_ideas_omega_cycle (2026-04-26)
#
# 각 atlas fact (id) 의 git commit hash provenance 추적.
# atlas.n6 + atlas.append.*.n6 의 entry id → 그 entry 가 처음 추가된 commit + 마지막 수정된 commit.
# self-host 회피 (bash + git, no hexa dep).
#
# usage:
#   tool/atlas_provenance.sh <id>             # single id provenance
#   tool/atlas_provenance.sh --bulk <pattern> # bulk grep + per-match provenance
#   tool/atlas_provenance.sh --shard <name>   # all entries in one shard
#
# exit codes: 0=found, 1=usage, 2=not found
# sentinel: __ATLAS_PROVENANCE__ id=<id> first=<hash> last=<hash> shard=<file>
# origin: design/hexa_sim/2026-04-26_improvement_ideas_omega_cycle.json axis_i15

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$HOME/core/nexus}"
ATLAS_MAIN="$NEXUS_ROOT/n6/atlas.n6"
ATLAS_SHARDS_GLOB="$NEXUS_ROOT/n6/atlas.append.*.n6"

MODE="single"
PATTERN=""
SHARD_NAME=""
LIMIT=20

while [ $# -gt 0 ]; do
    case "$1" in
        --bulk) MODE="bulk"; PATTERN="$2"; shift 2 ;;
        --shard) MODE="shard"; SHARD_NAME="$2"; shift 2 ;;
        --limit) LIMIT="$2"; shift 2 ;;
        --help|-h)
            echo "usage: $0 <id>               # single id"
            echo "       $0 --bulk <pattern>   # all entries matching pattern"
            echo "       $0 --shard <name>     # all entries in one shard"
            echo "       $0 --limit N          # cap bulk/shard results"
            echo "exit: 0=found / 1=usage / 2=not found"
            exit 0
            ;;
        --*) echo "unknown flag: $1" >&2; exit 1 ;;
        *)
            if [ -z "$PATTERN" ]; then PATTERN="$1"; fi
            shift
            ;;
    esac
done

# Find which file + line contains an id (returns "shard:line" or empty)
locate_id() {
    local id="$1"
    grep -lnE "^@[PCFLRSXMTE] ${id} =" "$ATLAS_MAIN" $ATLAS_SHARDS_GLOB 2>/dev/null | head -1
}

# Get git first-commit + last-commit + last-author for a file
provenance_for_id() {
    local id="$1"
    local shard
    shard=$(locate_id "$id")
    if [ -z "$shard" ]; then
        echo "__ATLAS_PROVENANCE__ FAIL id=$id reason=\"not found in any shard\""
        return 2
    fi
    local rel_shard="${shard#$NEXUS_ROOT/}"
    local line
    line=$(grep -nE "^@[PCFLRSXMTE] ${id} =" "$shard" 2>/dev/null | head -1 | cut -d: -f1)
    # git log -L: track line history
    local first_hash last_hash last_author last_ts
    first_hash=$(cd "$NEXUS_ROOT" && git log --reverse --format="%h" -- "$rel_shard" 2>/dev/null | head -1)
    last_hash=$(cd "$NEXUS_ROOT" && git log -n 1 --format="%h" -- "$rel_shard" 2>/dev/null)
    last_author=$(cd "$NEXUS_ROOT" && git log -n 1 --format="%an" -- "$rel_shard" 2>/dev/null)
    last_ts=$(cd "$NEXUS_ROOT" && git log -n 1 --format="%ai" -- "$rel_shard" 2>/dev/null)
    echo "id=$id"
    echo "  shard=$rel_shard line=$line"
    echo "  first_commit=$first_hash"
    echo "  last_commit=$last_hash by $last_author at $last_ts"
    echo "__ATLAS_PROVENANCE__ id=$id first=$first_hash last=$last_hash shard=$(basename "$shard")"
    return 0
}

# Bulk mode
bulk_provenance() {
    local pat="$1"
    local matched=0
    for shard in "$ATLAS_MAIN" $ATLAS_SHARDS_GLOB; do
        [ -f "$shard" ] || continue
        while IFS=: read -r line_no line_txt; do
            [ -z "$line_txt" ] && continue
            # extract id (between "@<TYPE> " and " =")
            local id
            id=$(echo "$line_txt" | sed -nE 's/^@[PCFLRSXMTE] ([^ ]+) =.*/\1/p')
            [ -z "$id" ] && continue
            matched=$((matched + 1))
            if [ "$matched" -le "$LIMIT" ]; then
                provenance_for_id "$id" | head -4
                echo "---"
            fi
            if [ "$matched" -ge "$LIMIT" ]; then break; fi
        done < <(grep -inE "^@[PCFLRSXMTE] [^ ]*${pat}[^ ]* =" "$shard" 2>/dev/null)
        if [ "$matched" -ge "$LIMIT" ]; then break; fi
    done
    echo "__ATLAS_PROVENANCE__ bulk pattern='$pat' matched=$matched limit=$LIMIT"
    [ "$matched" -gt 0 ] && return 0 || return 2
}

# Shard mode (all entries in one shard)
shard_provenance() {
    local name="$1"
    local shard
    if [ -f "$NEXUS_ROOT/n6/$name" ]; then
        shard="$NEXUS_ROOT/n6/$name"
    elif [ -f "$NEXUS_ROOT/n6/atlas.append.${name}.n6" ]; then
        shard="$NEXUS_ROOT/n6/atlas.append.${name}.n6"
    else
        echo "__ATLAS_PROVENANCE__ FAIL shard='$name' reason=\"not found at $NEXUS_ROOT/n6/$name nor with atlas.append. prefix\""
        return 2
    fi
    local rel_shard="${shard#$NEXUS_ROOT/}"
    local total
    total=$({ grep -cE '^@[PCFLRSXMTE] ' "$shard" 2>/dev/null || true; } | head -n1)
    total=${total:-0}
    local first_hash last_hash last_author last_ts
    first_hash=$(cd "$NEXUS_ROOT" && git log --reverse --format="%h" -- "$rel_shard" 2>/dev/null | head -1)
    last_hash=$(cd "$NEXUS_ROOT" && git log -n 1 --format="%h" -- "$rel_shard" 2>/dev/null)
    last_author=$(cd "$NEXUS_ROOT" && git log -n 1 --format="%an" -- "$rel_shard" 2>/dev/null)
    last_ts=$(cd "$NEXUS_ROOT" && git log -n 1 --format="%ai" -- "$rel_shard" 2>/dev/null)
    echo "shard=$rel_shard"
    echo "  total_entries=$total"
    echo "  first_commit=$first_hash"
    echo "  last_commit=$last_hash by $last_author at $last_ts"
    echo "__ATLAS_PROVENANCE__ shard=$(basename "$shard") total=$total first=$first_hash last=$last_hash"
    return 0
}

# Dispatch
case "$MODE" in
    single)
        if [ -z "$PATTERN" ]; then echo "usage: $0 <id>" >&2; exit 1; fi
        provenance_for_id "$PATTERN"
        ;;
    bulk)
        if [ -z "$PATTERN" ]; then echo "usage: $0 --bulk <pattern>" >&2; exit 1; fi
        bulk_provenance "$PATTERN"
        ;;
    shard)
        if [ -z "$SHARD_NAME" ]; then echo "usage: $0 --shard <name>" >&2; exit 1; fi
        shard_provenance "$SHARD_NAME"
        ;;
esac
