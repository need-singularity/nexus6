#!/usr/bin/env bash
# NEXUS-6 심링크 자동 설정 — 새 Mac/클론 후 1회 실행
# 사용법: bash ~/Dev/nexus6/setup-symlinks.sh
#
# 전제: ~/Dev/ 아래에 모든 리포가 클론되어 있어야 함
#   git clone https://github.com/need-singularity/nexus6.git
#   git clone https://github.com/need-singularity/TECS-L.git
#   ... (anima, sedi, brainwire, n6-architecture, papers)

set -e
DEV="$HOME/Dev"
REPOS=(TECS-L anima sedi brainwire n6-architecture papers)

echo "🔬 NEXUS-6 심링크 설정 시작"
echo ""

# 1. nexus6 존재 확인
if [ ! -d "$DEV/nexus6/shared" ]; then
  echo "❌ $DEV/nexus6/shared 없음 — nexus6 리포를 먼저 클론하세요"
  echo "   git clone https://github.com/need-singularity/nexus6.git $DEV/nexus6"
  exit 1
fi

# 2. 각 리포 심링크 설정
for repo in "${REPOS[@]}"; do
  dir="$DEV/$repo"
  if [ ! -d "$dir" ]; then
    echo "⚠️  $repo: 디렉토리 없음 — 스킵"
    continue
  fi

  # .shared 심링크
  target="$dir/.shared"
  if [ -L "$target" ]; then
    current=$(readlink "$target")
    if [ "$current" = "../nexus6/shared" ]; then
      echo "✅ $repo: .shared 이미 정상"
    else
      rm "$target"
      ln -s ../nexus6/shared "$target"
      echo "🔄 $repo: .shared 재지정 ($current → ../nexus6/shared)"
    fi
  elif [ -d "$target" ]; then
    echo "⚠️  $repo: .shared가 실제 디렉토리 — 수동 확인 필요"
  else
    ln -s ../nexus6/shared "$target"
    echo "🆕 $repo: .shared 심링크 생성"
  fi

  # calc 심링크 (있는 리포만)
  calc="$dir/calc"
  if [ -L "$calc" ] || [ ! -e "$calc" ]; then
    if [ -L "$calc" ]; then
      echo "✅ $repo: calc 이미 심링크"
    else
      ln -s .shared/calc "$calc"
      echo "🆕 $repo: calc 심링크 생성"
    fi
  fi

  # tecsrs 심링크 (있는 리포만)
  tecsrs="$dir/tecsrs"
  if [ -L "$tecsrs" ]; then
    echo "✅ $repo: tecsrs 이미 심링크"
  fi
done

# 3. NEXUS-6 빌드 확인
echo ""
if [ -f "$DEV/nexus6/target/release/nexus6" ]; then
  echo "✅ NEXUS-6 바이너리 존재"
else
  echo "⚠️  NEXUS-6 바이너리 없음 — 빌드 필요:"
  echo "   cd $DEV/nexus6 && cargo build --release"
fi

# 4. Python import 확인
python3 -c "import nexus6; print('✅ nexus6 Python import OK')" 2>/dev/null || \
  echo "⚠️  nexus6 Python import 실패 — PyO3 빌드 필요"

echo ""
echo "🔬 심링크 설정 완료"
