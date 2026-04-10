#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# sync-links.sh — 리포간 GitHub 링크 + README 배지 동기화
# ═══════════════════════════════════════════════════════════
set -euo pipefail

REPOS=(TECS-L n6-architecture anima sedi brainwire papers nexus)
BASE="https://github.com/need-singularity"
DEV="$HOME/Dev"

echo "🔗 리포간 링크 동기화 시작..."

for repo in "${REPOS[@]}"; do
  README="$DEV/$repo/README.md"
  [ -f "$README" ] || continue

  # Update cross-repo links
  for target in "${REPOS[@]}"; do
    [ "$repo" = "$target" ] && continue
    # Ensure link exists (don't overwrite, just verify)
    if ! grep -q "$BASE/$target" "$README" 2>/dev/null; then
      echo "  ⚠️  $repo/README.md: $target 링크 누락"
    fi
  done
done

echo "✅ 링크 동기화 완료"
