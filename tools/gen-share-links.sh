#!/usr/bin/env bash
# gen-share-links.sh — nexus-projects.json → 공유링크 텍스트 생성
# private 프로젝트는 자동 제외
set -euo pipefail

JSON="${1:-$(dirname "$0")/../shared/config/nexus-projects.json}"

/usr/bin/python3 -c "
import json, sys

with open('$JSON') as f:
    data = json.load(f)

# public_links 헤더
header = ' · '.join(
    f\"{v['emoji']} {v['label']}\" if v.get('emoji') and v['emoji'] not in v['label']
    else v['label']
    for v in data['public_links'].values()
)
print(header)
print()

# public 프로젝트만
for name, p in data['projects'].items():
    if p.get('visibility') == 'private':
        continue
    emoji = p.get('emoji', '')
    desc = p.get('description', '')
    print(f\"{emoji} {name} — {desc}\")
    print()
"
