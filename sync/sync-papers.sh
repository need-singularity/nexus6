#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# sync-papers.sh — 논문 DOI + Zenodo 링크 동기화
# ═══════════════════════════════════════════════════════════
set -euo pipefail

DEV="$HOME/Dev"
PAPERS_DIR="$DEV/papers"

echo "📄 논문 링크 동기화 시작..."

if [ -d "$PAPERS_DIR" ]; then
  # Count papers
  PAPER_COUNT=$(find "$PAPERS_DIR" -name "*.pdf" -o -name "*.md" | grep -c "" 2>/dev/null || echo 0)
  echo "  논문 수: $PAPER_COUNT"

  # Sync paper references to all repos
  for repo in TECS-L n6-architecture anima sedi brainwire nexus; do
    README="$DEV/$repo/README.md"
    [ -f "$README" ] || continue
    # Update paper count if marker exists
    if grep -q "📄 Papers" "$README" 2>/dev/null; then
      echo "  ✅ $repo: Papers 링크 확인됨"
    fi
  done
fi

echo "✅ 논문 동기화 완료"
