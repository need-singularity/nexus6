#!/bin/bash
# hexa_dispatch_check.sh — mac 에서 dispatch 정책 위반 감지 (L2)
#
# 정책 소스: $NEXUS/shared/dispatch_state.json (modules/dispatch.hexa 산출)
# 규칙 (AG6): heavy/compute/gpu 가 ubu 또는 htz 로 가야 하는 상황에
#           mac 에서 heavy hexa 작업 실행 중이면 위반.
#
# 출력:
#   JSONL 한 줄 → stdout (brain 이 파싱 용이하게)
#   { ts, policy: {heavy, compute, gpu}, mac_heavy_procs: [{pid,cpu,cmd}...],
#     violation: bool, reason: "..." }
#
# exit 0 = clean, 1 = violation detected (아직 실제 전가는 안 함)
#
# Usage:
#   hexa_dispatch_check.sh              # report JSON + exit code
#   hexa_dispatch_check.sh --human      # 사람용 요약

set -u

NEXUS="${NEXUS:-$HOME/Dev/nexus}"
DISPATCH="$NEXUS/shared/dispatch_state.json"
HUMAN=0
[[ "${1:-}" == "--human" ]] && HUMAN=1

now_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }

if [[ ! -f "$DISPATCH" ]]; then
    if [[ "$HUMAN" == "1" ]]; then
        echo "dispatch_state.json 없음 — policy 판단 불가"
    else
        printf '{"ts":"%s","error":"dispatch_state_missing","violation":false}\n' "$(now_iso)"
    fi
    exit 0
fi

HEAVY=$(jq -r '.selection.heavy // ""' "$DISPATCH" 2>/dev/null)
COMPUTE=$(jq -r '.selection.compute // ""' "$DISPATCH" 2>/dev/null)
GPU=$(jq -r '.selection.gpu // ""' "$DISPATCH" 2>/dev/null)
AG6_GATE=$(jq -r '.ag6_gate // ""' "$DISPATCH" 2>/dev/null)

# Mac 에서 실행 중인 heavy hexa 후보 (CPU > 50% + 특정 서브커맨드)
# heavy = build, bench. compute = parse, run, check.
MAC_HEAVY_JSON=$(ps -eo pid=,pcpu=,command= 2>/dev/null | awk '
    BEGIN { first=1; printf "[" }
    ($2+0 > 50) && ($0 ~ /\/hexa-lang\/hexa[[:space:]]+(build|bench|parse|run|check)/) {
        # 명령 뒤 경로만 추출 (cmd 의 1~3번째 토큰)
        cmd = ""
        for (i=3; i<=NF && i<=6; i++) cmd = cmd (i>3?" ":"") $i
        gsub(/"/, "\\\"", cmd)
        if (!first) printf ","
        printf "{\"pid\":%s,\"cpu\":%s,\"cmd\":\"%s\"}", $1, $2, cmd
        first = 0
    }
    END { printf "]" }')

# 위반 판단
VIOLATION="false"
REASON="no heavy mac procs OR policy allows mac"
PROC_COUNT=$(printf '%s' "$MAC_HEAVY_JSON" | jq 'length' 2>/dev/null)
PROC_COUNT=${PROC_COUNT:-0}

if [[ "$PROC_COUNT" -gt 0 ]] && [[ "$HEAVY" != "mac" ]] && [[ -n "$HEAVY" ]]; then
    VIOLATION="true"
    REASON="mac 에서 heavy proc $PROC_COUNT 개 실행 중인데 정책은 heavy=$HEAVY"
fi

# 출력
if [[ "$HUMAN" == "1" ]]; then
    echo "=== dispatch policy ==="
    echo "  heavy:   $HEAVY"
    echo "  compute: $COMPUTE"
    echo "  gpu:     $GPU"
    echo "  ag6_gate: $AG6_GATE"
    echo
    echo "=== mac heavy proc ($PROC_COUNT) ==="
    printf '%s' "$MAC_HEAVY_JSON" | jq -r '.[]? | "  PID \(.pid) cpu=\(.cpu) : \(.cmd)"' 2>/dev/null
    echo
    if [[ "$VIOLATION" == "true" ]]; then
        echo "⚠️  VIOLATION: $REASON"
    else
        echo "✓ clean"
    fi
else
    printf '{"ts":"%s","policy":{"heavy":"%s","compute":"%s","gpu":"%s","ag6_gate":"%s"},"mac_heavy_procs":%s,"violation":%s,"reason":"%s"}\n' \
        "$(now_iso)" "$HEAVY" "$COMPUTE" "$GPU" "$AG6_GATE" "$MAC_HEAVY_JSON" "$VIOLATION" "$REASON"
fi

[[ "$VIOLATION" == "true" ]] && exit 1 || exit 0
