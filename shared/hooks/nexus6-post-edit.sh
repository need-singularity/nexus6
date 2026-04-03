#!/usr/bin/env bash
# NEXUS-6 Post-Edit Gate — 설계 문서 수정 후 n6_check 자동 실행
# .shared/hooks/ → 전 리포 git 배포

# 심링크 자동 복구
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/ensure-symlinks.sh" || exit 0

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_response.filePath // ""')

[ -z "$FILE" ] || [ ! -f "$FILE" ] && exit 0

# 설계/config 파일만 (코드 파일 스킵)
echo "$FILE" | grep -qE '\.(md|toml|json|yaml|yml)$' || exit 0

RESULT=$(python3 -c "
import sys, json, re
sys.path.insert(0, '$HOME/Dev/n6-architecture/tools/nexus6/scripts')
try:
    import nexus6
    with open('$FILE', 'r') as f:
        content = f.read()
    nums = list(set(int(x) for x in re.findall(r'\b(\d{2,})\b', content) if 2 <= int(x) <= 100000))
    if not nums:
        sys.exit(0)
    exact, none = [], []
    for v in sorted(nums)[:20]:
        r = nexus6.n6_check(float(v))
        if r.grade == 'EXACT':
            exact.append(f'{v}={r.constant}')
        elif r.grade == 'NONE' and v > 5:
            none.append(str(v))
    total = len(exact) + len(none)
    if total == 0:
        sys.exit(0)
    ratio = len(exact) / total if total > 0 else 0
    msg = f'n6 {len(exact)}/{total} EXACT ({ratio:.0%})'
    if none:
        msg += f' | NONE: {\",\".join(none[:5])}'
    print(json.dumps({'systemMessage': f'🔬 NEXUS-6: {msg}'}))
except Exception:
    pass
" 2>/dev/null)

[ -n "$RESULT" ] && echo "$RESULT"
exit 0
