#!/bin/bash
# hexa_worker.sh — action queue 자동 실행 (L1.1)
#
# 동작:
#   1) hexa_actions.jsonl 의 pending 항목 스캔
#   2) BLACKLIST 토큰 포함 → 건너뜀 (위험)
#   3) WHITELIST 패턴 매칭 → safe 실행 + 결과 로그 + done 마킹
#   4) 매칭 없음 → 사람 개입 대기 (pending 유지)
#
# 안전 원칙:
#   - 결과가 읽기전용이거나 reversible 한 것만 WHITELIST
#   - 파괴적 동사 (kill/clean/rm/delete/bootout) 있으면 무조건 BLACKLIST
#   - 실행 결과는 40줄로 잘라 로그 (폭주 방지)

set -u

NEXUS="${NEXUS:-$HOME/core/nexus}"
Q="${HOME}/.airgenome/hexa_actions.jsonl"
WORKER_LOG="${HOME}/.airgenome/hexa_worker.jsonl"
ACTIONS_BIN="$NEXUS/scripts/hexa_actions.sh"
mkdir -p "$(dirname "$WORKER_LOG")"
touch "$Q"

now_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }

# WHITELIST: "pattern|command" — rec 에 pattern 포함 시 command 실행
# pattern 은 substring, command 는 bash 로 exec 됨 (rec 자체를 eval 하지 않음)
WHITELIST=(
    "hexa_janitor report|$NEXUS/scripts/hexa_janitor.sh report"
    "hexa_dispatch_check|$NEXUS/scripts/hexa_dispatch_check.sh --human"
    "hexa_patterns|$NEXUS/scripts/hexa_patterns.sh report"
)

# BLACKLIST: 이 토큰이 rec 에 있으면 WHITELIST 매칭돼도 실행 X
BLACKLIST=(
    "clean --yes"
    "rm -rf"
    "SIGKILL"
    " kill "
    "bootout"
    "unload"
    "delete"
    "remove file"
    "--force"
    "--yes"
)

line_num=0
executed=0
while IFS= read -r line; do
    line_num=$((line_num+1))
    [[ -z "$line" ]] && continue

    status=$(printf '%s' "$line" | jq -r '.status // ""' 2>/dev/null)
    [[ "$status" != "pending" ]] && continue

    rec=$(printf '%s' "$line" | jq -r '.rec // ""' 2>/dev/null)
    [[ -z "$rec" ]] && continue

    # Blacklist
    blacklisted=0
    for bad in "${BLACKLIST[@]}"; do
        if [[ "$rec" == *"$bad"* ]]; then
            blacklisted=1
            break
        fi
    done
    if [[ "$blacklisted" == "1" ]]; then
        continue
    fi

    # Whitelist
    matched_cmd=""
    matched_pattern=""
    for entry in "${WHITELIST[@]}"; do
        pattern="${entry%%|*}"
        cmd="${entry#*|}"
        if [[ "$rec" == *"$pattern"* ]]; then
            matched_cmd="$cmd"
            matched_pattern="$pattern"
            break
        fi
    done
    [[ -z "$matched_cmd" ]] && continue

    # Execute (no eval — cmd 는 WHITELIST 하드코딩이라 안전)
    exec_result=$(bash -c "$matched_cmd" 2>&1 | head -40)
    exec_exit=$?

    # Log
    printf '{"ts":"%s","line":%d,"pattern":%s,"cmd":%s,"exit":%d,"result":%s}\n' \
        "$(now_iso)" "$line_num" \
        "$(printf '%s' "$matched_pattern" | jq -Rs .)" \
        "$(printf '%s' "$matched_cmd" | jq -Rs .)" \
        "$exec_exit" \
        "$(printf '%s' "$exec_result" | jq -Rs .)" \
        >> "$WORKER_LOG"

    # Mark done
    "$ACTIONS_BIN" done "$line_num" >/dev/null 2>&1
    executed=$((executed + 1))
done < "$Q"

# Heartbeat (n개 실행됨)
if [[ "$executed" -gt 0 ]]; then
    printf '{"ts":"%s","kind":"heartbeat","executed":%d}\n' \
        "$(now_iso)" "$executed" >> "$WORKER_LOG"
fi

exit 0
