#!/bin/bash
# hexa_reflex.sh — tier1 반사 가드 (launchd 10초 주기)
#
# Why: 2026-04-14 load=70, PID 6745 hexa parse runaway 36분 incident.
# predictive_throttle 은 aggregate 예측 CPU 로만 판단 → 단일 runaway 사각지대.
#
# 동작:
#   1) vm.loadavg 1m 읽음
#   2) ps 로 hexa parse|run|check|build|bench 또는 hexa_stage0 중 CPU>50% 후보 수집
#   3) CPU>=90% 가 60s 지속 → taskpolicy -b + nice 19 강등
#      (load>20 일 때는 30s 로 단축)
#   4) 300s 지속 → SIGTERM (load>20 시 150s)
#   5) SIGTERM 후 10s 안 죽으면 SIGKILL
#   6) 상태는 ~/.airgenome/hexa_reflex_state/<PID>.{first,degraded,termed}
#   7) 이벤트는 ~/.airgenome/hexa_guard.jsonl 에 JSONL append
#
# 환경변수로 임계값 조정 가능:
#   HEXA_REFLEX_LOAD_CRIT, HEXA_REFLEX_CPU_PCT, HEXA_REFLEX_DEGRADE_SEC,
#   HEXA_REFLEX_KILL_SEC, HEXA_REFLEX_FORCE_KILL_SEC

set -u

STATE_DIR="${HOME}/.airgenome/hexa_reflex_state"
LOG="${HOME}/.airgenome/hexa_guard.jsonl"
mkdir -p "$STATE_DIR" "$(dirname "$LOG")"

LOAD_CRIT="${HEXA_REFLEX_LOAD_CRIT:-20}"
CPU_THRESH="${HEXA_REFLEX_CPU_PCT:-90}"
DEGRADE_SEC="${HEXA_REFLEX_DEGRADE_SEC:-60}"
KILL_SEC="${HEXA_REFLEX_KILL_SEC:-300}"
FORCE_KILL_SEC="${HEXA_REFLEX_FORCE_KILL_SEC:-10}"

TASKPOLICY=/usr/sbin/taskpolicy
NOW=$(date +%s)
NOW_ISO=$(date -u +%Y-%m-%dT%H:%M:%SZ)

emit() {
    local kind="$1" pid="$2" cpu="$3" etime="$4" action="$5" reason="$6" extra="${7:-{\}}"
    # 커맨드 추출 (proc 이 아직 살아있을 때만, 죽은 뒤엔 빈문자열)
    local cmd=""
    if [[ "$pid" != "0" ]]; then
        cmd=$(ps -p "$pid" -o command= 2>/dev/null | head -c 200 | sed 's/"/\\"/g; s/\\/\\\\/g')
    fi
    printf '{"ts":"%s","tier":1,"kind":"%s","pid":%s,"cpu":%s,"etime":%s,"action":"%s","reason":"%s","cmd":"%s","extra":%s}\n' \
        "$NOW_ISO" "$kind" "$pid" "$cpu" "$etime" "$action" "$reason" "$cmd" "$extra" >> "$LOG"
}

# 1) load avg 1m 정수부
LOAD_1M=$(sysctl -n vm.loadavg 2>/dev/null | awk '{print $2}')
LOAD_1M_INT=${LOAD_1M%%.*}
LOAD_1M_INT=${LOAD_1M_INT:-0}

LOAD_CRISIS=0
[[ "$LOAD_1M_INT" -gt "$LOAD_CRIT" ]] && LOAD_CRISIS=1

EFF_DEGRADE_SEC="$DEGRADE_SEC"
EFF_KILL_SEC="$KILL_SEC"
if [[ "$LOAD_CRISIS" -eq 1 ]]; then
    EFF_DEGRADE_SEC=$((DEGRADE_SEC / 2))
    EFF_KILL_SEC=$((KILL_SEC / 2))
fi

# 2) 후보 수집 (CPU > 50% 이고 hexa 관련)
# macOS ps 는 etimes 없음 → etime 파싱 (DD-HH:MM:SS / HH:MM:SS / MM:SS)
CANDIDATES=$(ps -eo pid=,pcpu=,etime=,command= \
  | awk '
      function parse_etime(s,   parts, n, dhms, d, h, m, sec) {
          d=0; h=0; m=0; sec=0
          n = split(s, parts, "-")
          if (n == 2) { d = parts[1]; s = parts[2] }
          n = split(s, dhms, ":")
          if (n == 3)      { h = dhms[1]; m = dhms[2]; sec = dhms[3] }
          else if (n == 2) { m = dhms[1]; sec = dhms[2] }
          else             { sec = dhms[1] }
          return d*86400 + h*3600 + m*60 + sec
      }
      ($2+0 > 50) &&
      (($0 ~ /\/hexa-lang\/hexa[[:space:]]+(parse|run|check|build|bench)/) || ($0 ~ /hexa_stage0/)) {
          et = parse_etime($3)
          printf "%d %d %d\n", $1, $2, et
      }')

# 3) 후보별 상태 갱신 및 액션
if [[ -n "$CANDIDATES" ]]; then
while read -r PID CPU ETIME; do
    [[ -z "${PID:-}" ]] && continue

    FIRST_FILE="$STATE_DIR/${PID}.first"
    DEGRADED_FILE="$STATE_DIR/${PID}.degraded"
    TERMED_FILE="$STATE_DIR/${PID}.termed"

    if [[ "$CPU" -ge "$CPU_THRESH" ]]; then
        if [[ ! -f "$FIRST_FILE" ]]; then
            printf '%s' "$NOW" > "$FIRST_FILE"
            ELAPSED=0
        else
            FIRST_TS=$(cat "$FIRST_FILE")
            ELAPSED=$((NOW - FIRST_TS))
        fi
    else
        [[ -f "$FIRST_FILE" ]] && rm -f "$FIRST_FILE"
        ELAPSED=0
    fi

    # 이미 SIGTERM 후 대기 중
    if [[ -f "$TERMED_FILE" ]]; then
        TERM_TS=$(cat "$TERMED_FILE")
        SINCE_TERM=$((NOW - TERM_TS))
        if [[ "$SINCE_TERM" -ge "$FORCE_KILL_SEC" ]] && kill -0 "$PID" 2>/dev/null; then
            if kill -KILL "$PID" 2>/dev/null; then
                emit "escalate" "$PID" "$CPU" "$ETIME" "SIGKILL" "SIGTERM_unresponsive" \
                    "{\"load\":$LOAD_1M_INT,\"since_term\":$SINCE_TERM}"
            fi
        fi
        continue
    fi

    # SIGTERM 단계
    if [[ "$ELAPSED" -ge "$EFF_KILL_SEC" ]] && [[ "$ELAPSED" -gt 0 ]]; then
        if kill -TERM "$PID" 2>/dev/null; then
            printf '%s' "$NOW" > "$TERMED_FILE"
            emit "escalate" "$PID" "$CPU" "$ETIME" "SIGTERM" "runaway_sustained" \
                "{\"load\":$LOAD_1M_INT,\"elapsed\":$ELAPSED,\"eff_kill_sec\":$EFF_KILL_SEC}"
        fi
        continue
    fi

    # 강등 단계
    if [[ "$ELAPSED" -ge "$EFF_DEGRADE_SEC" ]] && [[ ! -f "$DEGRADED_FILE" ]]; then
        if [[ -x "$TASKPOLICY" ]] && "$TASKPOLICY" -b -t 2 -l 2 -p "$PID" 2>/dev/null; then
            renice 19 -p "$PID" >/dev/null 2>&1
            printf '%s' "$NOW" > "$DEGRADED_FILE"
            emit "degrade" "$PID" "$CPU" "$ETIME" "taskpolicy_b+nice19" "runaway_detected" \
                "{\"load\":$LOAD_1M_INT,\"elapsed\":$ELAPSED,\"eff_degrade_sec\":$EFF_DEGRADE_SEC}"
        fi
    fi
done <<< "$CANDIDATES"
fi

# 4) GC — 죽은 PID 상태파일 정리
for f in "$STATE_DIR"/*; do
    [[ -e "$f" ]] || continue
    fname=$(basename "$f")
    pid="${fname%%.*}"
    [[ -z "$pid" ]] && continue
    if ! kill -0 "$pid" 2>/dev/null; then
        rm -f "$f"
    fi
done

# 5) Heartbeat (매 ~60s)
if [[ $((NOW % 60)) -lt 10 ]]; then
    CAND_COUNT=0
    [[ -n "$CANDIDATES" ]] && CAND_COUNT=$(printf '%s\n' "$CANDIDATES" | grep -c .)
    emit "heartbeat" "0" "0" "0" "none" "periodic" \
        "{\"load\":$LOAD_1M_INT,\"load_crisis\":$LOAD_CRISIS,\"candidates\":$CAND_COUNT}"
fi

exit 0
