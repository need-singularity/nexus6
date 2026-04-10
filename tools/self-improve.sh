#!/usr/bin/env bash
# Self-improvement loop: Claude CLI analyzes state + proposes improvements.
# Runs hourly, writes findings to shared/self_improve_log.jsonl.
set -euo pipefail

NEXUS="${HOME}/Dev/nexus"
LOG="${NEXUS}/shared/discovery/self_improve_log.jsonl"
CLAUDE_BIN="${HOME}/.local/bin/claude"
[ -x "$CLAUDE_BIN" ] || CLAUDE_BIN="$(which claude 2>/dev/null || echo '')"
[ -x "$CLAUDE_BIN" ] || CLAUDE_BIN=""

cd "$NEXUS"
TS=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

# Build context for Claude
CLOSED=$(wc -l < shared/discovery/verified_constants.jsonl | tr -d ' ')
TOPO=$(wc -l < shared/discovery/cycle/topology.jsonl 2>/dev/null | tr -d ' ' || echo 0)
STUBS=$(ls shared/calc/auto_stubs 2>/dev/null | wc -l | tr -d ' ')
EXACT=$(/usr/bin/python3 -c "import json,sys; print(sum(1 for l in open('shared/discovery/verified_constants.jsonl') if json.loads(l).get('status')=='EXACT'))")

PROMPT="nexus self-improve check @ ${TS}

System state:
- closed: ${CLOSED}
- EXACT: ${EXACT}
- topology: ${TOPO} points
- calc stubs: ${STUBS}

Check: Is the automation pipeline healthy? Are loops adding new closures? If not (saturated), what is the ONE next structural change to make? Answer in <50 words, actionable only."

# Compute delta from previous log entry (lightweight diagnostic)
DELTA_INFO=$(/usr/bin/python3 -c "
import json,os
log='${LOG}'
prev={}
if os.path.exists(log):
    with open(log) as f:
        lines=f.readlines()
    if lines:
        try: prev=json.loads(lines[-1])
        except: pass
if prev:
    d_closed = ${CLOSED} - prev.get('closed',0)
    d_exact = ${EXACT} - prev.get('exact',0)
    d_topo = ${TOPO} - prev.get('topology',0)
    d_stubs = ${STUBS} - prev.get('stubs',0)
    print(f'closed:{d_closed:+d} exact:{d_exact:+d} topo:{d_topo:+d} stubs:{d_stubs:+d}')
else:
    print('first entry')
" 2>/dev/null)

# Determine health
STATUS='healthy'
if [ "${CLOSED}" -eq 35976 ] 2>/dev/null; then STATUS='possibly-saturated'; fi

RESPONSE="delta=${DELTA_INFO} status=${STATUS}"

# Log to jsonl
/usr/bin/python3 -c "
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
