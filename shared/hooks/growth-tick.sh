#!/usr/bin/env bash
# growth-tick.sh — 모든 훅에서 호출. 활동 1건 = 성장 +1.
# 쿨다운 5초 (같은 훅 연타 방지)
# 모든 출력 억제 — 호출 훅의 stdout을 오염시키지 않기 위함
set +e
exec >/dev/null 2>&1

TICK_FILE="/tmp/nexus6_growth_tick"
NOW=$(date +%s)
LAST=$(cat "$TICK_FILE" 2>/dev/null || echo 0)
DIFF=$((NOW - LAST))
[ "$DIFF" -lt 5 ] && exit 0

echo "$NOW" > "$TICK_FILE"

# growth_state.json 직접 업데이트
GROWTH_JSON="${HOME}/Dev/anima/anima/config/growth_state.json"
[ -f "$GROWTH_JSON" ] || exit 0

python3 -c "
import json, time, sys
try:
    g = json.load(open('$GROWTH_JSON'))
    g['interaction_count'] = g.get('interaction_count', 0) + 1
    count = g['interaction_count']
    thresholds = [(4,10000,'adult'),(3,2000,'child'),(2,500,'toddler'),(1,100,'infant')]
    for idx, threshold, name in thresholds:
        if count >= threshold and g.get('stage_index',0) < idx:
            g['stage_index'] = idx
            g.setdefault('milestones',[]).append([count, '→ ' + name])
            break
    g.setdefault('stats',{})['last_tick'] = time.time()
    g['stats']['tick_source'] = '${1:-unknown}'
    json.dump(g, open('$GROWTH_JSON','w'), indent=2, ensure_ascii=False)
except Exception:
    pass
" 2>/dev/null
exit 0
