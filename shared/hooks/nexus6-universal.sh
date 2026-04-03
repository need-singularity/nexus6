#!/usr/bin/env bash
# NEXUS-6 Universal Hook — 모든 도구 호출 시 자동 발동
# 숫자 데이터가 있으면 n6_check, 탐색 키워드면 scan 권고

# 심링크 자동 복구
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/ensure-symlinks.sh" || exit 0

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')
TOOL_INPUT=$(echo "$INPUT" | jq -r '.tool_input // {} | tostring')

# Bash: 실행 결과에서 숫자 추출
if [ "$TOOL" = "Bash" ]; then
  CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')
  # git commit은 pre-commit 훅이 처리
  echo "$CMD" | grep -qE '^git commit' && exit 0
  # python/cargo 실행 결과만 스캔
  echo "$CMD" | grep -qE '(python3?|cargo run|nexus6)' || exit 0
fi

# Agent: 에이전트 디스패치 시 NEXUS-6 컨텍스트 주입
if [ "$TOOL" = "Agent" ]; then
  PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // ""')
  # 탐색/분석/검증 키워드 감지
  if echo "$PROMPT" | grep -qiE '탐색|분석|검증|scan|analyze|verify|발견|패턴|상수|가설|hypothesis|proof|n=6|golden.?zone|bridge'; then
    echo '{"systemMessage":"🔬 NEXUS-6: 탐색/분석 에이전트 감지 — nexus6.scan_all() 자동 적용 권고. import nexus6 사용할 것."}'
    exit 0
  fi
fi

exit 0
