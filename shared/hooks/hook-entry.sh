#!/usr/bin/env bash
set +e

MODE="${1:-}"
TARGET="${2:-}"
shift 2 >/dev/null || true

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_FILE="/tmp/nexus-hook-failed"

json_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

emit_block() {
  local msg
  msg="$(json_escape "$1")"
  printf '{"decision":"block","reason":"%s"}\n' "$msg"
}

emit_message() {
  local msg
  msg="$(json_escape "$1")"
  printf '{"systemMessage":"%s"}\n' "$msg"
}

find_hexa() {
  local cand
  for cand in \
    "$HOOK_DIR/../bin/hexa" \
    "$HOME/Dev/hexa-lang/hexa" \
    "$HOME/Dev/nexus/shared/scripts/bin/hexa" \
    "$HOME/.hx/bin/hexa" \
    "$HOME/Dev/hexa-lang/target/release/hexa" \
    "$HOME/Dev/hexa-lang/target/release/hexa-bin-actual"
  do
    [ -x "$cand" ] && { printf '%s\n' "$cand"; return 0; }
  done
  return 1
}

if [ "$MODE" = "guard" ]; then
  if [ -s "$STATE_FILE" ]; then
    MSG="$(cat "$STATE_FILE" 2>/dev/null)"
    emit_block "hook error 감지: $MSG. shared hook 복구 전 작업 중단."
  fi
  exit 0
fi

if [ -z "$TARGET" ]; then
  exit 0
fi

HEXA="$(find_hexa)"
if [ -z "$HEXA" ]; then
  printf '%s\n' "resolver missing for $(basename "$TARGET")" > "$STATE_FILE"
  case "$MODE" in
    pretool) emit_block "hook resolver 없음: $(basename "$TARGET")" ;;
    *) emit_message "hook resolver 없음: $(basename "$TARGET")" ;;
  esac
  exit 0
fi

TMP_IN="$(mktemp /tmp/nexus-hook-in.XXXXXX)"
TMP_OUT="$(mktemp /tmp/nexus-hook-out.XXXXXX)"
TMP_ERR="$(mktemp /tmp/nexus-hook-err.XXXXXX)"
cat > "$TMP_IN"

"$HEXA" "$TARGET" "$@" < "$TMP_IN" > "$TMP_OUT" 2> "$TMP_ERR"
STATUS=$?

if [ "$STATUS" -eq 0 ]; then
  rm -f "$STATE_FILE"
  cat "$TMP_OUT"
else
  ERR="$(tr '\n' ' ' < "$TMP_ERR" | sed 's/  */ /g' | cut -c1-240)"
  MSG="$(basename "$TARGET") exit=$STATUS ${ERR:-no-stderr}"
  printf '%s\n' "$MSG" > "$STATE_FILE"
  case "$MODE" in
    pretool) emit_block "hook 실패: $MSG" ;;
    *) emit_message "hook 실패 감지: $MSG" ;;
  esac
fi

rm -f "$TMP_IN" "$TMP_OUT" "$TMP_ERR"
exit 0
