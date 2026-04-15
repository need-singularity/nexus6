#!/usr/bin/env python3
"""Consolidate ANU-sourced byte chunks from all bostrom runs into a single stream.
Dedups by hex content.  Reads config from env vars:
  BOSTROM_OUT_HEX  — output path for concatenated hex string
  BOSTROM_OUT_META — output path for dedup'd meta.jsonl
"""
import glob
import json
import os
import sys

out_hex = os.environ['BOSTROM_OUT_HEX']
out_meta = os.environ['BOSTROM_OUT_META']

metas = sorted(glob.glob('/Users/ghost/Dev/nexus/shared/sim_bridge/bostrom_test/runs/bostrom_*/anu_stream.hex.meta.jsonl'))
seen = set()
chunks = []
rows = []
for m in metas:
    if m == out_meta:
        continue
    if not os.path.exists(m):
        continue
    try:
        for L in open(m):
            L = L.strip()
            if not L:
                continue
            d = json.loads(L)
            src = d.get('src', '')
            h = d.get('hex', '')
            if src in ('anu', 'cache', 'anu_direct') and len(h) >= 128:
                h = h[:128]
                if h in seen:
                    continue
                seen.add(h)
                chunks.append(h)
                rows.append({'i': len(chunks) - 1, 'src': src, 'hex': h, 'from': m})
    except Exception as e:
        print(f'WARN: {m} {e}', file=sys.stderr)
with open(out_hex, 'w') as f:
    f.write(''.join(chunks))
with open(out_meta, 'w') as f:
    for r in rows:
        f.write(json.dumps(r) + '\n')

print(f'[consolidate_impl] unique chunks: {len(chunks)} = {sum(len(c) for c in chunks) // 2} bytes')
by_src = {}
for r in rows:
    by_src[r['src']] = by_src.get(r['src'], 0) + 1
print(f'[consolidate_impl] by source: {by_src}')
