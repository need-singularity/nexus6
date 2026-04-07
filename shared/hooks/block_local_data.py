#!/usr/bin/env python3
"""
공용 PreToolUse hook: 데이터 파일(.jsonl, constants, discovery 등)을
개별 프로젝트 안에 생성/수정하려는 시도를 차단.
→ 모든 데이터는 ~/Dev/nexus/shared/ 에 저장해야 함.

사용법 (각 프로젝트 .claude/settings.local.json):
  "command": "python3 ~/Dev/nexus/shared/hooks/block_local_data.py \"$TOOL_NAME\""
"""
import sys
import json
import os
import re

NEXUS_SHARED = os.path.expanduser("~/Dev/nexus/shared")

# 차단 대상: 데이터/상수/로그 파일 패턴
BLOCKED_PATTERNS = [
    r'\.jsonl$',                    # 모든 JSONL
    r'discovered_constants',
    r'discovery_log',
    r'growth_bus',
    r'verified_constants',
    r'n6_constants',
    r'n6_knowledge',
    r'alien_index_records',
    r'growth_strategies',
    r'scan_priority',
    r'bt_domains',
    r'bt_keywords',
    r'custom_lenses',
    r'unfold_base',
]

# 예외: 허용 경로
ALLOWED_PATTERNS = [
    r'/nexus/shared/',              # nexus 중앙 저장소
    r'/nexus/mk2_hexa/',            # nexus 엔진 코드
    r'hexa_grammar\.jsonl',         # 문법 참조 (읽기 전용 심링크)
    r'package\.json',
    r'tsconfig\.json',
]

def main():
    tool_input = json.loads(sys.stdin.read())
    tool_name = sys.argv[1] if len(sys.argv) > 1 else ""

    if tool_name not in ("Write", "Edit"):
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    # 허용 패턴 체크
    for pattern in ALLOWED_PATTERNS:
        if re.search(pattern, file_path):
            sys.exit(0)

    # 차단 패턴 검사
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, file_path):
            print(
                f"❌ 데이터 파일을 프로젝트 안에 저장하지 마세요!\n"
                f"\n"
                f"  시도: {file_path}\n"
                f"  이유: 상수/수식/발견/로그 데이터는 nexus 중앙 저장소에만 보관\n"
                f"\n"
                f"  올바른 경로: ~/Dev/nexus/shared/ 아래에 저장\n"
                f"  예시:\n"
                f"    ~/Dev/nexus/shared/discovered_constants.jsonl\n"
                f"    ~/Dev/nexus/shared/discovery_log.jsonl\n"
                f"    ~/Dev/nexus/shared/growth_bus.jsonl\n"
                f"    ~/Dev/nexus/shared/n6_constants.jsonl\n"
                f"\n"
                f"  규칙: 프로젝트 데이터 → nexus/shared/ (유일한 진실의 원천)\n"
                f"  참조: 각 프로젝트에서 읽기만 하려면 심링크 사용",
                file=sys.stderr
            )
            sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
