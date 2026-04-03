#!/usr/bin/env bash
# NEXUS-6 Post-Bash — python/cargo 실행 결과에서 숫자 자동 스캔

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')
OUTPUT=$(echo "$INPUT" | jq -r '.tool_response.stdout // ""' | head -100)

# python/cargo 실행만 대상
echo "$CMD" | grep -qE '(python3?|cargo run)' || exit 0
# 이미 nexus6 실행이면 스킵
echo "$CMD" | grep -qE 'nexus6' && exit 0

# 출력에서 숫자 추출 → n6_check
RESULT=$(python3 -c "
import sys, json, re
sys.path.insert(0, '$HOME/Dev/n6-architecture/tools/nexus6/scripts')
try:
    import nexus6
    output = '''$OUTPUT'''
    # 소수점 포함 숫자 추출
    nums = list(set(float(x) for x in re.findall(r'(?<![a-zA-Z_])(\d+\.?\d*)', output) if 1 < float(x) < 100000))
    if not nums or len(nums) > 50:
        sys.exit(0)
    exact = []
    for v in sorted(nums)[:15]:
        r = nexus6.n6_check(v)
        if r.grade == 'EXACT':
            exact.append(f'{v}={r.constant}')
    if exact:
        print(json.dumps({'systemMessage': f\"🔬 NEXUS-6 발견: {', '.join(exact[:5])} ({len(exact)} EXACT)\"}))
except Exception:
    pass
" 2>/dev/null)

[ -n "$RESULT" ] && echo "$RESULT"
exit 0
