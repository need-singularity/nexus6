#!/bin/bash
# @hexa-first-exempt — mkdir-atomic advisory lock for macOS (no flock)
# lock_gate.sh — mkdir-based advisory lock (flock 부재 환경용, macOS)
# usage:
#   lock_gate.sh acquire <name> [wait_seconds=0]   → exit 0 (hold) / 75 (busy)
#   lock_gate.sh release <name>                    → exit 0
#   lock_gate.sh status [<name>]                   → HELD pid=N ts=T / FREE / list
#   lock_gate.sh gc                                → purge stale (600s+ OR dead pid)
# stale: 600s 이상 OR holder PID 죽었으면 자동 청소.
# bypass: NEXUS_NO_LOCK=1 (호출측 처리)

LOCK_ROOT="${NEXUS_LOCK_ROOT:-/tmp/nexus_locks}"
mkdir -p "$LOCK_ROOT"

cmd="$1"
name="$2"
wait_s="${3:-0}"

case "$cmd" in
    acquire)
        if [ -z "$name" ]; then
            echo "usage: lock_gate.sh acquire <name> [wait_s]" >&2
            exit 2
        fi
        lock="$LOCK_ROOT/$name.lock"
        now=$(date +%s)
        deadline=$(( now + wait_s ))
        while true; do
            if mkdir "$lock" 2>/dev/null; then
                echo $$ > "$lock/pid"
                date +%s > "$lock/ts"
                exit 0
            fi
            # stale check: age>600s (absolute timeout) OR age>5s + pid dead
            # age≤5s 구간은 무조건 보호 — bash 서브쉘 race (각 invocation 별 PID) 방지
            if [ -f "$lock/pid" ]; then
                oldpid=$(cat "$lock/pid" 2>/dev/null)
                oldts=$(cat "$lock/ts" 2>/dev/null)
                # cat-cat split race — release 가 사이에 rm -rf 한 경우 빈값.
                # 빈값 stale=age 거대 오판 방지: 짧게 기다리고 재시도.
                if [ -z "$oldpid" ] || [ -z "$oldts" ]; then
                    sleep 0.1
                    continue
                fi
                age=$(( $(date +%s) - oldts ))
                stale=0
                if [ "$age" -gt 600 ]; then
                    stale=1
                elif [ "$age" -gt 5 ] && ! kill -0 "$oldpid" 2>/dev/null; then
                    stale=1
                fi
                if [ "$stale" = "1" ]; then
                    rm -rf "$lock"
                    continue
                fi
            fi
            if [ "$(date +%s)" -ge "$deadline" ]; then
                exit 75
            fi
            sleep 0.5
        done
        ;;
    release)
        if [ -z "$name" ]; then
            echo "usage: lock_gate.sh release <name>" >&2
            exit 2
        fi
        lock="$LOCK_ROOT/$name.lock"
        # 호출자 책임 — name-only release. exec_validated trap EXIT 같은 같은-쉘 패턴
        # 외에 hexa exec() 는 매번 새 bash subshell PID 라 strict 매칭 불가능.
        # NEXUS_LOCK_STRICT=1 명시 시에만 PID 검증.
        if [ -n "$NEXUS_LOCK_STRICT" ]; then
            # TOCTOU window 최소화 — 한 줄로 압축. flock 없이 완전 제거 불가능 (잔존 race).
            [ -d "$lock" ] && [ "$(cat "$lock/pid" 2>/dev/null)" = "$$" ] && rm -rf "$lock"
        else
            rm -rf "$lock"
        fi
        exit 0
        ;;
    status)
        if [ -n "$name" ]; then
            lock="$LOCK_ROOT/$name.lock"
            if [ -d "$lock" ]; then
                echo "HELD pid=$(cat "$lock/pid" 2>/dev/null) ts=$(cat "$lock/ts" 2>/dev/null)"
            else
                echo "FREE"
            fi
        else
            ls -1 "$LOCK_ROOT" 2>/dev/null | sed 's/\.lock$//'
        fi
        ;;
    gc)
        # purge stale
        for lock in "$LOCK_ROOT"/*.lock; do
            [ -d "$lock" ] || continue
            oldpid=$(cat "$lock/pid" 2>/dev/null)
            oldts=$(cat "$lock/ts" 2>/dev/null || echo 0)
            age=$(( $(date +%s) - oldts ))
            if [ "$age" -gt 600 ] || ! kill -0 "$oldpid" 2>/dev/null; then
                rm -rf "$lock"
                echo "purged: $lock"
            fi
        done
        ;;
    *)
        echo "usage: lock_gate.sh {acquire|release|status|gc} [name] [wait_s]" >&2
        exit 2
        ;;
esac
