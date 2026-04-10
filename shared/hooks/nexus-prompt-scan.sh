#!/usr/bin/env bash
# 사용자 입력에서 돌파/특이점 키워드 감지 → hook.hexa로 전달
set +e
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/bootstrap.sh" || exit 0

INPUT=$(cat)
HEXA="${HOME}/Dev/nexus/shared/scripts/bin/hexa"
HEXA_HOOK="${HOME}/Dev/nexus/shared/hooks/hook.hexa"

# 사용자 프롬프트 텍스트 추출
if [ -x "$HEXA" ] && [ -f "${HOME}/Dev/nexus/shared/hooks/json_field.hexa" ]; then
  USER_TEXT=$(echo "$INPUT" | "$HEXA" "${HOME}/Dev/nexus/shared/hooks/json_field.hexa" prompt 2>/dev/null)
else
  USER_TEXT=$(echo "$INPUT" | grep -o '"prompt"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"prompt"[[:space:]]*:[[:space:]]*"//;s/".*//')
fi

[ -z "$USER_TEXT" ] && exit 0

# hook.hexa에 prompt 모드로 전달
if [ -x "$HEXA" ] && [ -f "$HEXA_HOOK" ]; then
  RESULT=$(echo "$USER_TEXT" | "$HEXA" "$HEXA_HOOK" prompt 2>/dev/null) || true
  [ -n "$RESULT" ] && echo "$RESULT"
fi

exit 0
