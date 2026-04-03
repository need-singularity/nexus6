#!/usr/bin/env bash
# NEXUS-6 hooks를 전 리포 .claude/settings.json에 동기화
# .shared/hooks/ 스크립트는 심링크로 자동 공유됨
# 이 스크립트는 .claude/settings.json의 hooks 섹션만 머지

HOOK_CONFIG='{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .shared/hooks/nexus6-pre-commit.sh",
            "if": "Bash(git commit*)",
            "timeout": 15,
            "statusMessage": "🔬 NEXUS-6 pre-commit scan..."
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash .shared/hooks/nexus6-post-edit.sh",
            "timeout": 10,
            "statusMessage": "🔬 NEXUS-6 n6_check..."
          }
        ]
      }
    ]
  }
}'

REPOS=(
  "$HOME/Dev/TECS-L"
  "$HOME/Dev/anima"
  "$HOME/Dev/sedi"
  "$HOME/Dev/n6-architecture"
  "$HOME/Dev/brainwire"
  "$HOME/Dev/papers"
  "$HOME/Dev/nexus6"
)

for repo in "${REPOS[@]}"; do
  if [ ! -d "$repo" ]; then
    echo "⏭️  $repo (not found)"
    continue
  fi

  settings="$repo/.claude/settings.json"
  mkdir -p "$repo/.claude"

  if [ -f "$settings" ]; then
    # 기존 설정에 hooks 머지
    MERGED=$(jq -s '.[0] * .[1]' "$settings" <(echo "$HOOK_CONFIG"))
    echo "$MERGED" | jq '.' > "$settings.tmp" && mv "$settings.tmp" "$settings"
    echo "✅ $repo (merged)"
  else
    # 새로 생성
    echo "$HOOK_CONFIG" | jq '.' > "$settings"
    echo "✅ $repo (created)"
  fi
done

echo ""
echo "🔬 NEXUS-6 hooks synced to ${#REPOS[@]} repos"
echo "   Scripts: .shared/hooks/nexus6-{pre-commit,post-edit}.sh"
echo "   Config:  .claude/settings.json (git tracked)"
