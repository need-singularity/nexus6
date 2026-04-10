#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# sync-all.sh — NEXUS-6 전체 동기화 (원커맨드)
# ═══════════════════════════════════════════════════════════
# 사용: bash ~/Dev/nexus/sync/sync-all.sh
# 트리거: "넥서스 동기화"
# ═══════════════════════════════════════════════════════════
set -euo pipefail

SYNC_DIR="$(cd "$(dirname "$0")" && pwd)"
NEXUS_ROOT="$(cd "$SYNC_DIR/.." && pwd)"
DEV="$HOME/Dev"
REPOS=(TECS-L n6-architecture anima sedi brainwire papers nexus)

echo "════════════════════════════════════════"
echo "  NEXUS-6 전체 동기화"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "════════════════════════════════════════"

# 0. 심링크 검증 + 복구
echo ""
echo "🔗 [0/7] 심링크 검증..."
for repo in "${REPOS[@]}"; do
  [ "$repo" = "nexus" ] && continue
  LINK="$DEV/$repo/.shared"
  if [ -L "$LINK" ] && [ -d "$LINK" ]; then
    echo "  ✅ $repo"
  elif [ -d "$DEV/$repo" ]; then
    rm -rf "$LINK" 2>/dev/null
    ln -sf ../nexus/shared "$LINK"
    echo "  🔧 $repo (복구됨)"
  fi
done

# 1. CLAUDE.md 전파
echo ""
echo "📋 [1/7] CLAUDE.md 동기화..."
if [ -f "$SYNC_DIR/sync-claude-rules.sh" ]; then
  bash "$SYNC_DIR/sync-claude-rules.sh" 2>/dev/null && echo "  ✅ 완료" || echo "  ⚠️ 스킵"
else
  echo "  ⚠️ sync-claude-rules.sh 없음"
fi

# 2. 수학 아틀라스
echo ""
echo "🗺️ [2/7] Math Atlas 동기화..."
if [ -f "$SYNC_DIR/sync-math-atlas.sh" ]; then
  bash "$SYNC_DIR/sync-math-atlas.sh" 2>/dev/null && echo "  ✅ 완료" || echo "  ⚠️ 스킵"
else
  echo "  ⚠️ sync-math-atlas.sh 없음"
fi

# 3. 계산기 레지스트리
echo ""
echo "🧮 [3/7] 계산기 동기화..."
if [ -f "$SYNC_DIR/sync-calculators.sh" ]; then
  bash "$SYNC_DIR/sync-calculators.sh" 2>/dev/null && echo "  ✅ 완료" || echo "  ⚠️ 스킵"
else
  echo "  ⚠️ sync-calculators.sh 없음"
fi

# 4. README 자동 생성
echo ""
echo "📖 [4/7] README 동기화..."
if [ -f "$SYNC_DIR/sync-readmes.sh" ]; then
  bash "$SYNC_DIR/sync-readmes.sh" 2>/dev/null && echo "  ✅ 완료" || echo "  ⚠️ 스킵"
else
  echo "  ⚠️ sync-readmes.sh 없음"
fi

# 5. 렌즈 수 동기화
echo ""
echo "🔭 [5/7] 렌즈 동기화..."
if [ -f "$SYNC_DIR/sync-nexus-lenses.sh" ]; then
  bash "$SYNC_DIR/sync-nexus-lenses.sh" 2>/dev/null && echo "  ✅ 완료" || echo "  ⚠️ 스킵"
else
  echo "  ⚠️ sync-nexus-lenses.sh 없음"
fi

# 6. 리포간 링크
echo ""
echo "🔗 [6/7] 링크 동기화..."
bash "$SYNC_DIR/sync-links.sh" 2>/dev/null || echo "  ⚠️ 스킵"

# 7. 논문
echo ""
echo "📄 [7/7] 논문 동기화..."
bash "$SYNC_DIR/sync-papers.sh" 2>/dev/null || echo "  ⚠️ 스킵"

# 8. DSE 지도
echo ""
echo "🗺️ [+] DSE 동기화..."
if [ -f "$SYNC_DIR/sync-dse.sh" ]; then
  bash "$SYNC_DIR/sync-dse.sh" 2>/dev/null && echo "  ✅ 완료" || echo "  ⚠️ 스킵"
fi

# 9. 원격 동기화
echo ""
echo "🌐 [+] 원격 동기화 (htz/vast)..."
if [ -f "$SYNC_DIR/sync-remote.sh" ]; then
  bash "$SYNC_DIR/sync-remote.sh" both all 2>/dev/null && echo "  ✅ 완료" || echo "  ⚠️ 스킵 (원격 미연결)"
fi

# Summary
echo ""
echo "════════════════════════════════════════"
echo "  전체 동기화 완료 ✅"
echo ""
echo "  리포: ${#REPOS[@]}개"
echo "  렌즈: $(grep -c 'Box::new' "$NEXUS_ROOT/src/telescope/mod.rs" 2>/dev/null || echo '?')개"
echo "  계산기: $(find "$NEXUS_ROOT/shared/calc" -name '*.py' -o -name '*.rs' 2>/dev/null | wc -l | tr -d ' ')개"
ATLAS="$NEXUS_ROOT/shared/discovery/math_atlas.json"
if [ -f "$ATLAS" ]; then
  echo "  아틀라스: $(/usr/bin/python3 -c "import json;print(len(json.load(open('$ATLAS')).get('entries',{})))" 2>/dev/null || echo '?') 항목"
fi
echo "════════════════════════════════════════"
