#!/usr/bin/env bash
# Self-improvement loop: Claude CLI analyzes state + proposes improvements.
# Runs hourly, writes findings to shared/self_improve_log.jsonl.
set -euo pipefail

NEXUS6="${HOME}/Dev/nexus6"
LOG="${NEXUS6}/shared/self_improve_log.jsonl"
CLAUDE_BIN="${HOME}/.local/bin/claude"
[ -x "$CLAUDE_BIN" ] || CLAUDE_BIN="$(which claude 2>/dev/null || echo '')"
[ -x "$CLAUDE_BIN" ] || { echo "claude CLI not found"; exit 0; }

cd "$NEXUS6"
TS=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

# Build context for Claude
CLOSED=$(wc -l < shared/verified_constants.jsonl | tr -d ' ')
TOPO=$(wc -l < shared/cycle/topology.jsonl 2>/dev/null | tr -d ' ' || echo 0)
STUBS=$(ls shared/calc/auto_stubs 2>/dev/null | wc -l | tr -d ' ')
EXACT=$(python3 -c "import json,sys; print(sum(1 for l in open('shared/verified_constants.jsonl') if json.loads(l).get('status')=='EXACT'))")

PROMPT="nexus6 self-improve check @ ${TS}

System state:
- closed: ${CLOSED}
- EXACT: ${EXACT}
- topology: ${TOPO} points
- calc stubs: ${STUBS}

Check: Is the automation pipeline healthy? Are loops adding new closures? If not (saturated), what is the ONE next structural change to make? Answer in <50 words, actionable only."

# Run claude one-shot, capture response
RESPONSE=$(timeout 60 "$CLAUDE_BIN" -p "$PROMPT" --dangerously-skip-permissions 2>/dev/null | tail -20 || echo "(claude timeout)")

# Log to jsonl
python3 -c "
import json,sys
entry = {
    'ts': '${TS}',
    'closed': ${CLOSED},
    'exact': ${EXACT},
    'topology': ${TOPO},
    'stubs': ${STUBS},
    'claude_response': '''${RESPONSE}'''[:500]
}
with open('${LOG}', 'a') as f:
    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
print(f'[${TS}] self-improve logged')
"
