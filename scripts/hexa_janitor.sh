#!/bin/bash
# hexa_janitor.sh — 유휴 자원 보고 (옵션: 정리)
#
# Why: Mac 에 claude 세션/프로세스가 누적되어 자원 낭비.
#   - idle claude 프로세스 (0 CPU, 장시간 sleep)
#   - 대용량 ~/.claude-claudeN/projects 캐시
#
# Usage:
#   hexa_janitor report          # 기본. 정리 대상 나열 only
#   hexa_janitor clean --yes     # 실제 정리 (확인 필요)

set -u

MIN_IDLE_HOURS="${HEXA_JANITOR_IDLE_HOURS:-4}"
ACTION="${1:-report}"
CONFIRM="${2:-}"

echo "=== idle claude processes (etime >= ${MIN_IDLE_HOURS}h, pcpu<0.5, STAT~S) ==="
IDLE_PIDS=$(ps -eo pid=,stat=,pcpu=,etime=,command= | awk -v min_h="$MIN_IDLE_HOURS" '
    function etime_hours(s,   parts, n, dhms, d, h) {
        d=0; h=0
        n = split(s, parts, "-")
        if (n == 2) { d = parts[1]; s = parts[2] }
        n = split(s, dhms, ":")
        if (n == 3) { h = dhms[1] } else { h = 0 }
        return d*24 + h
    }
    /claude --effort/ && $3+0 < 0.5 && $2 ~ /^S/ {
        h = etime_hours($4)
        if (h >= min_h) {
            printf "%s\t%s\t%s\t%s\n", $1, $2, $4, $3
        }
    }')

if [[ -z "$IDLE_PIDS" ]]; then
    printf '  (none)\n'
else
    printf '%s\n' "$IDLE_PIDS" | awk -F'\t' '{printf "  PID %s  STAT %s  etime %s  cpu %s%%\n", $1, $2, $3, $4}'
fi

echo
echo "=== claude project state (>200M 먼저) ==="
du -sh "$HOME"/.claude-claude*/projects 2>/dev/null | awk '
    { sub(/M$/, "M", $1); size=$1
      # "538M" 파싱
      n = size + 0
      unit = substr(size, length(size))
      if (unit == "G") n *= 1024
      if (n >= 200) printf "  %s  %s\n", $1, $2
    }'

if [[ "$ACTION" == "report" ]]; then
    echo
    echo "clean 실행: hexa_janitor clean --yes"
    exit 0
fi

if [[ "$ACTION" != "clean" ]]; then
    printf 'usage: hexa_janitor {report|clean --yes}\n' >&2
    exit 1
fi

if [[ "$CONFIRM" != "--yes" ]]; then
    printf 'clean 실행하려면 --yes 필요\n' >&2
    exit 1
fi

# 실제 정리
killed=0
if [[ -n "$IDLE_PIDS" ]]; then
    printf '%s\n' "$IDLE_PIDS" | awk -F'\t' '{print $1}' | while read -r pid; do
        [[ -z "$pid" ]] && continue
        if kill -TERM "$pid" 2>/dev/null; then
            printf '  SIGTERM PID %s\n' "$pid"
        fi
    done
    killed=1
fi

if [[ "$killed" == "0" ]]; then
    echo "(아무 것도 정리 안 됨)"
fi

echo "완료."
