#!/bin/bash
# Block creation/editing of .py, .rs, .sh files (HEXA-FIRST rule)
# + 렌즈/상수/수식/가설/BT/DSE 데이터는 nexus로 유도
# Used as Claude Code PreToolUse hook

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE" ]]; then
  exit 0
fi

NEXUS="$HOME/Dev/nexus"
BASENAME=$(basename "$FILE")

# ─── 데이터 유형별 nexus 유도 (모든 확장자 대상) ───

# 렌즈 → nexus shared/hexa/native/
if [[ "$FILE" =~ lens.*\.(rs|py)$ ]] || [[ "$FILE" =~ telescope/lenses/ ]]; then
  LENS_NAME="${BASENAME%.rs}"
  LENS_NAME="${LENS_NAME%.py}"
  echo "BLOCKED: $FILE — 렌즈는 nexus hexa로 작성. ${NEXUS}/shared/hexa/native/${LENS_NAME}.hexa" >&2
  exit 2
fi

# 상수 데이터 → nexus shared/
if [[ "$FILE" =~ constant ]] && [[ "$FILE" =~ \.(json|jsonl|toml|csv)$ ]] && [[ "$FILE" != *"$NEXUS/shared/"* ]]; then
  echo "BLOCKED: $FILE — 상수 데이터는 nexus에 중앙 관리. ${NEXUS}/shared/n6/n6_constants.jsonl 또는 n6_physics.jsonl" >&2
  exit 2
fi

# 수식/공식 → nexus shared/
if [[ "$FILE" =~ formula ]] && [[ "$FILE" =~ \.(json|jsonl|py|rs)$ ]] && [[ "$FILE" != *"$NEXUS/"* ]]; then
  echo "BLOCKED: $FILE — 수식은 nexus에 중앙 관리. ${NEXUS}/shared/ 또는 shared/hexa/native/" >&2
  exit 2
fi

# 가설 데이터 → nexus shared/
if [[ "$FILE" =~ hypothesis ]] && [[ "$FILE" =~ \.(json|jsonl)$ ]] && [[ "$FILE" != *"$NEXUS/"* ]]; then
  echo "BLOCKED: $FILE — 가설 데이터는 nexus에 중앙 관리. ${NEXUS}/shared/" >&2
  exit 2
fi

# BT(기본정리) → nexus shared/
if [[ "$BASENAME" =~ ^[Bb][Tt][-_] ]] && [[ "$FILE" != *"$NEXUS/"* ]]; then
  echo "BLOCKED: $FILE — BT 데이터는 nexus에 중앙 관리. ${NEXUS}/shared/" >&2
  exit 2
fi

# DSE 도메인 → nexus shared/dse/
if [[ "$FILE" =~ dse/.*\.toml$ ]] && [[ "$FILE" != *"$NEXUS/"* ]]; then
  echo "BLOCKED: $FILE — DSE 도메인은 nexus에 중앙 관리. ${NEXUS}/shared/dse/domains/" >&2
  exit 2
fi

# shared/hooks/ 신규 .sh/.py 작성 금지
if [[ "$FILE" =~ shared/hooks/.*\.(sh|py)$ ]]; then
  if [[ ! -f "$FILE" ]]; then
    echo "BLOCKED: $FILE — shared/hooks/에 새 .sh/.py 작성 금지. .hexa로 작성하세요." >&2
    exit 2
  fi
fi

# ─── HEXA-FIRST: .py/.rs/.sh 신규 작성 금지 ───
if [[ "$FILE" =~ \.(py|rs|sh)$ ]] && [[ ! "$FILE" =~ /src/ ]]; then
  echo "BLOCKED: $FILE — .py/.rs/.sh 신규 작성 금지. .hexa로 작성하세요. (CLAUDE.md 규칙 0)" >&2
  exit 2
fi

exit 0
