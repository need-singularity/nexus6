#!/bin/bash
# hexa_offload.sh — mac heavy hexa 작업을 target host 로 전가 (L2 완성)
#
# 기본 dry-run. --execute 명시해야 실제 전가.
# 안전: 원격 실행 성공 확인 후에만 mac SIGTERM. 실패 시 mac proc 유지.
#
# Usage:
#   hexa_offload.sh <pid>                       # dry-run (기본)
#   hexa_offload.sh <pid> --target ubu          # 타겟 지정
#   hexa_offload.sh <pid> --execute             # 실제 전가
#
# 로그: ~/.airgenome/hexa_offload.jsonl

set -u

NEXUS="${NEXUS:-$HOME/Dev/nexus}"
DISPATCH="$NEXUS/dispatch_state.json"
LOG="${HOME}/.airgenome/hexa_offload.jsonl"
mkdir -p "$(dirname "$LOG")"

now_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }

# target alias 매핑 (dispatch_state 의 htz → ssh config 의 hetzner)
resolve_target() {
    case "$1" in
        htz) printf 'hetzner' ;;
        *)   printf '%s' "$1" ;;
    esac
}

# 인자 파싱
PID=""
TARGET=""
EXECUTE=0
while (( $# > 0 )); do
    case "$1" in
        --target)  TARGET="${2:?}"; shift 2 ;;
        --execute) EXECUTE=1; shift ;;
        -h|--help)
            sed -n '2,15p' "$0"
            exit 0 ;;
        -*) echo "unknown flag: $1" >&2; exit 1 ;;
        *)  [[ -z "$PID" ]] && PID="$1"; shift ;;
    esac
done

if [[ -z "$PID" ]]; then
    echo "usage: hexa_offload.sh <pid> [--target <host>] [--execute]" >&2
    exit 1
fi

# 1) mac PID 정보 수집
CMD=$(ps -p "$PID" -o command= 2>/dev/null | awk '{$1=$1; print}')
if [[ -z "$CMD" ]]; then
    echo "PID $PID 없음 (이미 종료?)" >&2
    exit 1
fi

# cwd — lsof 로 추출 (mac)
CWD=$(lsof -a -p "$PID" -d cwd -Fn 2>/dev/null | awk '/^n/{print substr($0,2); exit}')

# hexa command 가 맞는지 검증
if [[ "$CMD" != *"/hexa-lang/hexa "* ]] && [[ "$CMD" != *"hexa_stage0"* ]]; then
    echo "PID $PID 는 hexa proc 아님: $CMD" >&2
    exit 1
fi

# 2) 타겟 결정
if [[ -z "$TARGET" ]]; then
    TARGET=$(jq -r '.selection.heavy // ""' "$DISPATCH" 2>/dev/null)
    [[ -z "$TARGET" ]] || [[ "$TARGET" == "null" ]] || [[ "$TARGET" == "mac" ]] && TARGET="ubu"
fi
SSH_TARGET=$(resolve_target "$TARGET")

# 3) ssh preflight
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "$SSH_TARGET" "echo ok" >/dev/null 2>&1; then
    echo "ssh $SSH_TARGET preflight 실패 — 키/네트워크 확인" >&2
    exit 2
fi

# 4) 원격에서 같은 hexa 바이너리 + 경로 존재하는지 사전 확인
REMOTE_HEXA_PATH=$(printf '%s' "$CMD" | awk '{print $1}')
if ! ssh "$SSH_TARGET" "test -x '$REMOTE_HEXA_PATH' && test -d '${CWD:-/tmp}'" 2>/dev/null; then
    echo "원격 ($SSH_TARGET) 에서 hexa bin 또는 cwd 없음:" >&2
    echo "  hexa: $REMOTE_HEXA_PATH" >&2
    echo "  cwd:  ${CWD:-?}" >&2
    echo "경로 동기화 or --execute 보류" >&2
    REMOTE_OK=0
else
    REMOTE_OK=1
fi

# 5) dry-run 출력
cat <<EOF
=== offload plan ===
source PID:    $PID
cmd:           $CMD
mac cwd:       ${CWD:-(unknown)}
target host:   $TARGET  (ssh: $SSH_TARGET)
remote ready:  $([ "$REMOTE_OK" == "1" ] && echo yes || echo no)

remote cmd (if --execute):
  cd ${CWD:-/tmp} && nohup $CMD > /tmp/offload_$PID.out 2>&1 &
then on mac:
  kill -TERM $PID

EOF

if [[ "$EXECUTE" == "0" ]]; then
    echo "dry-run only — 실제 실행하려면 --execute 추가"
    exit 0
fi

# === 실제 실행 ===
if [[ "$REMOTE_OK" != "1" ]]; then
    echo "원격 준비 안됨 — 중단" >&2
    exit 3
fi

REMOTE_OUT="/tmp/offload_${PID}_$(date +%s).out"
# 원격 백그라운드 실행
ssh "$SSH_TARGET" "cd '${CWD:-/tmp}' && nohup $CMD > '$REMOTE_OUT' 2>&1 & disown; echo \$!"
SSH_EXIT=$?

if [[ "$SSH_EXIT" != "0" ]]; then
    echo "원격 실행 실패 (ssh exit=$SSH_EXIT) — mac proc 유지" >&2
    printf '{"ts":"%s","pid":%s,"target":"%s","status":"remote_start_failed","exit":%d}\n' \
        "$(now_iso)" "$PID" "$SSH_TARGET" "$SSH_EXIT" >> "$LOG"
    exit 4
fi

# 원격 프로세스 확인 (5초 대기)
sleep 3
if ! ssh "$SSH_TARGET" "pgrep -f \"$(printf '%s' "$CMD" | awk '{print $NF}')\"" >/dev/null 2>&1; then  # @allow-pkill-f (원격 원자성 검증 — 로컬 kill 아님)
    echo "원격 proc 확인 실패 — mac proc 유지 (수동 확인 필요)" >&2
    printf '{"ts":"%s","pid":%s,"target":"%s","status":"remote_verify_failed"}\n' \
        "$(now_iso)" "$PID" "$SSH_TARGET" >> "$LOG"
    exit 5
fi

# mac SIGTERM
if kill -TERM "$PID" 2>/dev/null; then
    printf '{"ts":"%s","pid":%s,"target":"%s","cmd":%s,"remote_out":"%s","status":"offloaded"}\n' \
        "$(now_iso)" "$PID" "$SSH_TARGET" \
        "$(printf '%s' "$CMD" | jq -Rs .)" "$REMOTE_OUT" >> "$LOG"
    echo "✓ offloaded PID $PID → $SSH_TARGET (remote out: $REMOTE_OUT)"
else
    echo "⚠ 원격 실행됨 but mac SIGTERM 실패 — 두 곳에서 실행 중일 수도" >&2
    exit 6
fi
