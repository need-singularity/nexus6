#!/bin/bash
# hexa_tuner.sh — 패턴 통계 기반 reflex 임계값 자동 조정 (L3 완성)
#
# 동작:
#   1) hexa_patterns.sh json → escalate_stats (count/avg/max/min elapsed)
#   2) 샘플 충분하면 DEGRADE_SEC = avg*0.3, KILL_SEC = avg*0.9 (clamp)
#   3) ~/.airgenome/hexa_tune.json 갱신
#   4) reflex.sh 는 env 안 쓰면 이 파일의 값 사용
#
# 매일 4:17 am 실행 (launchd StartCalendarInterval)
#
# 안전:
#   - MIN_SAMPLES 미달 시 applied=false (기본값 유지)
#   - clamp: DEGRADE 30~180s, KILL 120~600s
#   - env var 가 우선. tune 은 env 없을 때만 적용.

set -u

NEXUS="${NEXUS:-$HOME/core/nexus}"
PATTERNS="$NEXUS/scripts/hexa_patterns.sh"
TUNE_FILE="${HOME}/.airgenome/hexa_tune.json"
TUNE_LOG="${HOME}/.airgenome/hexa_tuner.jsonl"
MIN_SAMPLES="${HEXA_TUNER_MIN_SAMPLES:-5}"

mkdir -p "$(dirname "$TUNE_FILE")"
now_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }

if [[ ! -x "$PATTERNS" ]]; then
    echo "patterns 스크립트 없음: $PATTERNS" >&2
    exit 1
fi

STATS_JSON=$("$PATTERNS" json 2>/dev/null)
SAMPLES=$(printf '%s' "$STATS_JSON" | jq '.escalate_stats.count // 0' 2>/dev/null)
AVG=$(printf '%s' "$STATS_JSON" | jq '.escalate_stats.avg // 0' 2>/dev/null)
MAX=$(printf '%s' "$STATS_JSON" | jq '.escalate_stats.max // 0' 2>/dev/null)
MIN=$(printf '%s' "$STATS_JSON" | jq '.escalate_stats.min // 0' 2>/dev/null)

SAMPLES=${SAMPLES:-0}
AVG=${AVG:-0}

# confidence
if (( SAMPLES < MIN_SAMPLES )); then
    CONF="insufficient"
elif (( SAMPLES < 15 )); then
    CONF="low"
elif (( SAMPLES < 50 )); then
    CONF="medium"
else
    CONF="high"
fi

if [[ "$CONF" == "insufficient" ]]; then
    NEW_DEG=60
    NEW_KILL=300
    APPLIED=false
    REASON="samples=$SAMPLES (min=$MIN_SAMPLES) — defaults 유지"
else
    NEW_DEG=$(( AVG * 30 / 100 ))
    NEW_KILL=$(( AVG * 90 / 100 ))
    # Clamp
    (( NEW_DEG < 30 )) && NEW_DEG=30
    (( NEW_DEG > 180 )) && NEW_DEG=180
    (( NEW_KILL < 120 )) && NEW_KILL=120
    (( NEW_KILL > 600 )) && NEW_KILL=600
    APPLIED=true
    REASON="avg_elapsed=${AVG}s (samples=$SAMPLES,conf=$CONF) → deg=${NEW_DEG}s kill=${NEW_KILL}s"
fi

jq -n --arg ts "$(now_iso)" --argjson samples "$SAMPLES" \
      --argjson avg "$AVG" --argjson max "$MAX" --argjson min "$MIN" \
      --argjson deg "$NEW_DEG" --argjson kill "$NEW_KILL" \
      --arg conf "$CONF" --argjson applied "$APPLIED" --arg reason "$REASON" \
      '{ts:$ts, samples:$samples, avg_elapsed:$avg, max_elapsed:$max, min_elapsed:$min,
        DEGRADE_SEC:$deg, KILL_SEC:$kill, confidence:$conf, applied:$applied, reason:$reason}' \
    > "$TUNE_FILE"

# 감사 로그
cat "$TUNE_FILE" | jq -c . >> "$TUNE_LOG"

# 요약
jq -c '{samples,confidence,DEGRADE_SEC,KILL_SEC,applied,reason}' "$TUNE_FILE"
