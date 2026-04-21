#!/bin/bash
# hexa_patterns.sh — hexa_guard.jsonl 의 반복 offender / 패턴 분석 (L3 v1)
#
# 입력: ~/.airgenome/hexa_guard.jsonl
# 출력:
#   hexa_patterns.sh report           # 사람용 요약
#   hexa_patterns.sh json             # 기계용 JSONL 집계
#   hexa_patterns.sh brain-hint       # brain 이 prompt 에 넣기 좋은 1줄 요약
#
# 감지 대상:
#   - 같은 커맨드가 24h 내 N회 이상 reflex 에 걸림 (repeat offender)
#   - 같은 file 반복 degrade/SIGTERM (OOM 패턴 후보)
#
# 향후 확장 (self-tuning):
#   - escalate 간 평균 elapsed → DEGRADE_SEC 조정 힌트
#   - load crisis 빈도 → LOAD_CRIT 조정 힌트

set -u

LOG="${HOME}/.airgenome/hexa_guard.jsonl"
WINDOW_HOURS="${HEXA_PATTERNS_WINDOW_H:-24}"
MIN_REPEAT="${HEXA_PATTERNS_MIN_REPEAT:-3}"

now_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }

cutoff=$(date -u -v-"${WINDOW_HOURS}"H +%Y-%m-%dT%H:%M:%SZ 2>/dev/null)

if [[ ! -f "$LOG" ]] || [[ ! -s "$LOG" ]]; then
    case "${1:-report}" in
        json)       printf '{"ts":"%s","window_h":%d,"events":0,"offenders":[]}\n' "$(now_iso)" "$WINDOW_HOURS" ;;
        brain-hint) printf 'patterns: log empty\n' ;;
        *)          echo "(no guard log)" ;;
    esac
    exit 0
fi

# reflex escalate|degrade 이벤트만 집계 (tier=1, kind in escalate|degrade)
# cmd 필드를 키로 카운트. 파일명만 추출 (hexa $sub <file>).
OFFENDERS_JSON=$(jq -c --arg cut "$cutoff" '
    select(.tier==1 and (.kind=="escalate" or .kind=="degrade") and .ts>=$cut)
    | {
        cmd: (.cmd // ""),
        file: ((.cmd // "") | capture("hexa +\\w+ +(?<f>[^ ]+)").f // ""),
        action: .action,
        elapsed: (.extra.elapsed // 0)
      }' "$LOG" 2>/dev/null | jq -s --argjson min "$MIN_REPEAT" '
    group_by(.file // .cmd)
    | map({
        key: (.[0].file // .[0].cmd),
        count: length,
        actions: [.[].action] | unique,
        max_elapsed: ([.[].elapsed] | max // 0),
        last_sample: .[-1]
      })
    | map(select(.count >= $min))
    | sort_by(-.count)
    ')

OFFENDER_COUNT=$(printf '%s' "$OFFENDERS_JSON" | jq 'length' 2>/dev/null)
OFFENDER_COUNT=${OFFENDER_COUNT:-0}
TOTAL_EVENTS=$(jq -c --arg cut "$cutoff" \
    'select(.tier==1 and (.kind=="escalate" or .kind=="degrade") and .ts>=$cut)' \
    "$LOG" 2>/dev/null | wc -l | tr -d ' ')

# escalate 이벤트 → SIGTERM/SIGKILL 로 평균 elapsed 통계 (self-tune 힌트용)
ESCALATE_STATS=$(jq -c --arg cut "$cutoff" '
    select(.tier==1 and .kind=="escalate" and .action=="SIGTERM" and .ts>=$cut)
    | .extra.elapsed // 0' "$LOG" 2>/dev/null \
    | jq -s '{count: length, avg: (if length==0 then 0 else (add/length|floor) end), max: (max // 0), min: (min // 0)}')

case "${1:-report}" in
    json)
        jq -n --arg ts "$(now_iso)" --argjson w "$WINDOW_HOURS" \
              --argjson total "$TOTAL_EVENTS" --argjson off "$OFFENDERS_JSON" \
              --argjson esc "$ESCALATE_STATS" \
              '{ts:$ts, window_h:$w, events:$total, offenders:$off, escalate_stats:$esc}'
        ;;
    brain-hint)
        if [[ "$OFFENDER_COUNT" == "0" ]]; then
            printf 'patterns: 최근 %dh 반복 offender 없음 (총 %d reflex events)\n' "$WINDOW_HOURS" "$TOTAL_EVENTS"
        else
            printf 'patterns: %dh 내 repeat offenders %d개 — ' "$WINDOW_HOURS" "$OFFENDER_COUNT"
            printf '%s' "$OFFENDERS_JSON" | jq -r '.[] | "\(.key) (x\(.count))"' | paste -sd ", " -
            printf '\n'
        fi
        ;;
    *)
        printf '=== hexa patterns (last %dh) ===\n' "$WINDOW_HOURS"
        printf 'total reflex events: %s\n' "$TOTAL_EVENTS"
        printf 'escalate stats: %s\n' "$ESCALATE_STATS"
        echo
        if [[ "$OFFENDER_COUNT" == "0" ]]; then
            echo "repeat offenders (>= $MIN_REPEAT): none"
        else
            printf 'repeat offenders (>= %s):\n' "$MIN_REPEAT"
            printf '%s' "$OFFENDERS_JSON" | jq -r '.[] | "  [\(.count)x] \(.key)  actions=\(.actions|join(","))  max_elapsed=\(.max_elapsed)s"'
        fi
        ;;
esac
