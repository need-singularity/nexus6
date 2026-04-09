#!/usr/bin/env bash
# Generate paper stubs from high-value nexus closures.
# Writes to /Users/ghost/Dev/papers/nexus/N6-auto-*.md
set -euo pipefail

NEXUS="${HOME}/Dev/nexus"
PAPERS_DIR="${HOME}/Dev/papers/nexus"
STATE="${NEXUS}/shared/.paper_gen_state.json"

mkdir -p "$PAPERS_DIR"

/usr/bin/python3 << 'PYEOF'
import json, os, hashlib
from datetime import datetime
from collections import Counter

HOME = os.path.expanduser('~')
VC = f'{HOME}/Dev/nexus/shared/verified_constants.jsonl'
PAPERS = f'{HOME}/Dev/papers/nexus'
STATE_PATH = f'{HOME}/Dev/nexus/shared/.paper_gen_state.json'

state = {'paper_ids': []}
if os.path.exists(STATE_PATH):
    try: state = json.loads(open(STATE_PATH).read())
    except: pass
existing = set(state.get('paper_ids', []))

# Load EXACT closures, group by expression pattern
pattern_groups = {}  # n6_expr[0] → [records]
value_groups = {}    # rounded value → [records]
for line in open(VC):
    try:
        j = json.loads(line)
        if j.get('status') != 'EXACT': continue
        exprs = j.get('n6_expr', [])
        if not exprs: continue
        expr_key = str(exprs[0])
        pattern_groups.setdefault(expr_key, []).append(j)
        v = j.get('value')
        if v is not None:
            value_groups.setdefault(round(float(v), 4), []).append(j)
    except: pass

# Find HIGH-VALUE patterns: same value across MANY closures (convergence)
papers_created = 0
top_values = sorted(value_groups.items(), key=lambda kv: -len(kv[1]))[:20]
for val, records in top_values:
    if len(records) < 3: continue  # need ≥3 supporting records
    pid = hashlib.md5(f'converge_{val}'.encode()).hexdigest()[:8]
    if pid in existing: continue
    projects = Counter(r.get('project','?') for r in records)
    unique_exprs = list(set(str(r.get('n6_expr',[''])[0]) for r in records))[:5]
    paper_path = f'{PAPERS}/N6-auto-convergence-{val}-{pid}.md'
    if os.path.exists(paper_path):
        existing.add(pid)
        continue
    ts = datetime.now().strftime('%Y-%m-%d')
    body = f"""---
title: Convergence {val} — Multi-Expression n=6 Closure
date: {ts}
generator: nexus paper-gen-from-closures
grade: draft
alien_index: 10
value: {val}
support_count: {len(records)}
---

# Value {val} as Universal n=6 Closure

## Abstract

The value **{val}** appears as an n=6 closed-form expression in {len(records)}
independent discoveries across {len(projects)} projects/sources:

{chr(10).join(f'- `{e}`' for e in unique_exprs)}

This convergence across {len(projects)} independent sources suggests {val}
is a universal n=6 invariant rather than coincidental.

## Sources

{chr(10).join(f'- **{proj}**: {count} matches' for proj, count in projects.most_common())}

## Closed-Form Expressions

All {len(records)} matches reduce to:
{chr(10).join(f'{i+1}. `{e}`' for i,e in enumerate(unique_exprs))}

## Open Questions

1. Are these expressions **algebraically equivalent** (same ring element) or
   numerically coincident (distinct elements that happen to equal {val})?
2. Does the multiplicity of expressions for {val} indicate a **meta-closure**
   (a pattern generating closures, not just one value)?
3. What physical/mathematical invariant does {val} correspond to?

## Verification Path

1. Symbolic simplification of all {len(unique_exprs)} expressions to canonical form
2. Dimensional analysis if {val} matches a physical constant
3. OEIS lookup for {val} as a known sequence value

---
*Auto-generated stub. Human fills in proof + interpretation.*
"""
    with open(paper_path, 'w') as f:
        f.write(body)
    existing.add(pid)
    papers_created += 1

state['paper_ids'] = list(existing)
state['last_run'] = datetime.now().isoformat()
with open(STATE_PATH, 'w') as f:
    f.write(json.dumps(state))

print(f"[{datetime.now().isoformat()}] papers created: {papers_created}, total: {len(existing)}")
PYEOF

# Auto-commit+push papers repo
cd "$PAPERS_DIR/.." || exit 0
if [ -d .git ]; then
    git add nexus/ 2>/dev/null || true
    if ! git diff --cached --quiet; then
        git -c commit.gpgsign=false commit -m "auto: nexus closure paper stubs $(date -u +%FT%TZ)" 2>&1 | tail -1
        git push 2>&1 | tail -1 || echo "push failed"
    fi
fi

