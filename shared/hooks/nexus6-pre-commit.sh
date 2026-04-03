#!/usr/bin/env bash
# NEXUS-6 Pre-Commit Gate — git commit 시 자동 스캔
# .shared/hooks/ → 전 리포 git 배포

# 심링크 자동 복구
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/ensure-symlinks.sh" || exit 0

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

if ! echo "$CMD" | grep -qE '^git commit'; then
  exit 0
fi

RESULT=$(python3 -c "
import sys, json
sys.path.insert(0, '$HOME/Dev/n6-architecture/tools/nexus6/scripts')
try:
    import nexus6
    import subprocess
    diff = subprocess.run(['git', 'diff', '--cached', '--numstat'], capture_output=True, text=True).stdout
    nums = [int(x) for line in diff.split('\n') for x in line.split()[:2] if x.isdigit()]
    if not nums:
        print(json.dumps({'ok': True, 'msg': 'no numeric data'}))
        sys.exit(0)
    result = nexus6.analyze(nums, len(nums), 1)
    ratio = result.get('n6_exact_ratio', 0)
    active = result.get('active_lenses', 0)
    consensus = result.get('consensus', [])
    print(json.dumps({
        'systemMessage': f'🔬 NEXUS-6 pre-commit: n6={ratio:.1%}, {active} lenses, {len(consensus)} consensus'
    }))
except Exception as e:
    print(json.dumps({'systemMessage': f'⚠️ NEXUS-6: scan skipped ({e})'}))
" 2>/dev/null)

[ -n "$RESULT" ] && echo "$RESULT"
exit 0
