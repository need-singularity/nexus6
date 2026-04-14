#!/bin/bash
# @hexa-first-exempt — sys_ shim that dispatches to lib/lock_gate.hexa
# lock_gate.sh — mkdir-atomic advisory lock dispatcher
#
# 실체: shared/harness/lib/lock_gate.hexa (hexa-only 로직)
# 이 shim: hexa exit() 미전파 우회 (f-hexa-exit-sentinel) — stdout 마지막 라인
#          __LOCK_GATE_RC__ N 을 shell exit code 로 번역.
#
# usage (2026-04-14 sh→hexa 포팅 후에도 기존 인터페이스 유지):
#   lock_gate.sh acquire <name> [wait_s=0]   → exit 0 (hold) / 75 (busy) / 2 (usage)
#   lock_gate.sh release <name>              → exit 0
#   lock_gate.sh status [<name>]             → HELD/FREE/list
#   lock_gate.sh gc                          → stale 청소
# bypass: NEXUS_NO_LOCK=1 (호출측 처리, wrapper 는 그대로 실행)
# env: NEXUS_LOCK_ROOT (default /tmp/nexus_locks), NEXUS_LOCK_STRICT=1 (release PID 검증)

HOME_DIR="${HOME:-/Users/ghost}"
NEXUS_ROOT="${NEXUS_ROOT:-$HOME_DIR/Dev/nexus}"
HEXA="$NEXUS_ROOT/shared/bin/hexa"
IMPL="$NEXUS_ROOT/shared/harness/lib/lock_gate.hexa"

if [ ! -x "$HEXA" ] || [ ! -f "$IMPL" ]; then
    echo "lock_gate: 엔진 부재 — $IMPL" >&2
    exit 2
fi

# hexa exit() 미전파 → stdout sentinel 파싱 (마지막 __LOCK_GATE_RC__ N 라인)
out="$("$HEXA" run "$IMPL" "$@" 2>&1)"
# sentinel 외 출력은 투과
body="$(printf '%s' "$out" | grep -v '^__LOCK_GATE_RC__ ')"
rc_line="$(printf '%s' "$out" | grep '^__LOCK_GATE_RC__ ' | tail -1)"
[ -n "$body" ] && printf '%s\n' "$body"

if [ -z "$rc_line" ]; then
    echo "lock_gate: sentinel 부재 — stdout=$out" >&2
    exit 2
fi
exit "${rc_line##__LOCK_GATE_RC__ }"
