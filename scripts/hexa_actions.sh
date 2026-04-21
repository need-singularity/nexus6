#!/bin/bash
# hexa_actions.sh — action queue CLI
# brain 이 제안한 recommend 를 큐에 append, 사용자가 list/done/skip.
#
# Storage: ~/.airgenome/hexa_actions.jsonl (JSONL append-only + in-place edit)
#
# Usage:
#   hexa_actions list [pending|done|skip|all]        (default: pending)
#   hexa_actions done <id>
#   hexa_actions skip <id>
#   hexa_actions add <source> <rec> [ttl_hours]      (dedup window, default 1)
#   hexa_actions count

set -u

Q="${HOME}/.airgenome/hexa_actions.jsonl"
mkdir -p "$(dirname "$Q")"
touch "$Q"

now_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }

cmd_list() {
    local filter="${1:-pending}"
    local n=0
    while IFS= read -r line; do
        n=$((n+1))
        [[ -z "$line" ]] && continue
        local status ts src rec
        status=$(printf '%s' "$line" | jq -r '.status // "?"' 2>/dev/null)
        if [[ "$filter" != "all" ]] && [[ "$status" != "$filter" ]]; then continue; fi
        ts=$(printf '%s' "$line" | jq -r '.ts // ""' 2>/dev/null | cut -c1-16)
        src=$(printf '%s' "$line" | jq -r '.source // ""' 2>/dev/null)
        rec=$(printf '%s' "$line" | jq -r '.rec // ""' 2>/dev/null)
        printf '[%d] %s | %-7s | %-6s | %s\n' "$n" "$ts" "$status" "$src" "$rec"
    done < "$Q"
}

cmd_update_status() {
    local target="$1" new_status="$2"
    local ts_now tmp n=0 matched=0
    ts_now=$(now_iso)
    tmp=$(mktemp)
    while IFS= read -r line; do
        n=$((n+1))
        if [[ "$n" == "$target" ]] && [[ -n "$line" ]]; then
            printf '%s' "$line" | jq -c --arg ns "$new_status" --arg ts "$ts_now" \
                '.status=$ns | .resolved_at=$ts' >> "$tmp"
            matched=1
        else
            printf '%s\n' "$line" >> "$tmp"
        fi
    done < "$Q"
    if [[ "$matched" == "1" ]]; then
        mv "$tmp" "$Q"
        printf '[%s] → %s\n' "$target" "$new_status"
    else
        rm -f "$tmp"
        printf 'no entry at index %s\n' "$target" >&2
        return 1
    fi
}

cmd_add() {
    local src="$1" rec="$2" ttl_hours="${3:-1}"
    local ts cutoff
    ts=$(now_iso)
    cutoff=$(date -u -v-"${ttl_hours}"H +%Y-%m-%dT%H:%M:%SZ 2>/dev/null)

    # Dedup: 동일 rec 가 pending 이고 ts>=cutoff 면 스킵
    if [[ -n "$cutoff" ]] && tail -500 "$Q" 2>/dev/null | \
        jq -c --arg r "$rec" --arg cut "$cutoff" \
            'select(.rec==$r and .status=="pending" and .ts>=$cut)' 2>/dev/null | \
        grep -q .; then
        printf 'dup skipped: %s\n' "$rec"
        return 0
    fi

    local id
    id="${ts}-$(printf '%s' "$rec" | md5 -q 2>/dev/null | cut -c1-8)"
    [[ -z "$id" ]] && id="${ts}"

    jq -cn --arg id "$id" --arg ts "$ts" --arg src "$src" --arg rec "$rec" \
        '{id:$id,ts:$ts,source:$src,rec:$rec,status:"pending",resolved_at:null}' \
        >> "$Q"
    printf 'added: %s\n' "$id"
}

cmd_count() {
    local total pending done_n skip_n
    total=$(wc -l < "$Q" | tr -d ' ')
    pending=$(jq -c 'select(.status=="pending")' "$Q" 2>/dev/null | wc -l | tr -d ' ')
    done_n=$(jq -c 'select(.status=="done")'    "$Q" 2>/dev/null | wc -l | tr -d ' ')
    skip_n=$(jq -c 'select(.status=="skip")'    "$Q" 2>/dev/null | wc -l | tr -d ' ')
    printf 'total=%s pending=%s done=%s skip=%s\n' "$total" "$pending" "$done_n" "$skip_n"
}

cmd="${1:-list}"
shift || true

case "$cmd" in
    list)   cmd_list "${1:-pending}" ;;
    done)   cmd_update_status "${1:?id required}" "done" ;;
    skip)   cmd_update_status "${1:?id required}" "skip" ;;
    add)    cmd_add "${1:?source required}" "${2:?rec required}" "${3:-1}" ;;
    count)  cmd_count ;;
    *)
        printf 'usage: hexa_actions {list|done|skip|add|count} [args]\n' >&2
        exit 1
        ;;
esac
