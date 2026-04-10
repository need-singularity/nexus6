#!/bin/bash
# compose.sh — blowup core + modules 조립 wrapper
# 현재 각 모듈(field/holographic/quantum/string/toe)은 독립 entry point.
# hexa import 미지원이므로 exec chain 방식으로 조립.
#
# 사용:
#   compose.sh <domain> [depth] [--modules m1,m2,...] [--dfs N] [--skip-core]
#
# 예:
#   compose.sh math 3                           # core만
#   compose.sh math 3 --modules field,quantum   # core + field + quantum
#   compose.sh math 3 --modules string --dfs 3  # core(+DFS) + string
#   compose.sh physics 3 --modules toe --skip-core  # 모듈만
#
# 순서: core → modules (core의 atlas.n6 기록이 모듈의 입력이 됨)
# 각 모듈은 atlas.n6를 읽어 추가 돌파 생성. 조립 = 동일 atlas SSOT 경유 I/O 연쇄.

set -eu

NEXUS_DIR="${NEXUS_DIR:-$HOME/Dev/nexus}"
HEXA_BIN="${HEXA_BIN:-$HOME/Dev/hexa-lang/target/release/hexa}"
BLOWUP_CORE="$NEXUS_DIR/shared/blowup/core/blowup.hexa"
MODULES_DIR="$NEXUS_DIR/shared/blowup/modules"

if [ $# -lt 1 ]; then
  cat <<EOF
compose.sh — blowup 조립 wrapper

usage: compose.sh <domain> [depth] [--modules m1,m2,...] [--dfs N] [--skip-core] [--fast]

modules (cumulative): field, holographic, quantum, string, toe
  - field        : Discovery Field / Gauge Filter / Symmetry Breaking (Mk.III)
  - holographic  : boundary/bulk 이중화 경유
  - quantum      : 중첩 seed 파동함수 evolution
  - string       : 끈 이론 진동 모드 seed 전파
  - toe          : Theory of Everything 전 도메인 통합

examples:
  compose.sh math 3
  compose.sh math 3 --modules field,quantum --dfs 3
  compose.sh 7대난제 3 --modules toe --fast
EOF
  exit 1
fi

DOMAIN="$1"; shift
DEPTH="3"
MODULES=""
DFS_DEPTH="0"
SKIP_CORE="0"
FAST_FLAG=""

while [ $# -gt 0 ]; do
  case "$1" in
    --modules)    MODULES="$2"; shift 2 ;;
    --dfs)        DFS_DEPTH="$2"; shift 2 ;;
    --skip-core)  SKIP_CORE="1"; shift ;;
    --fast)       FAST_FLAG="--fast"; shift ;;
    -*)           echo "unknown flag: $1" >&2; exit 1 ;;
    *)            DEPTH="$1"; shift ;;
  esac
done

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  blowup compose: $DOMAIN (depth=$DEPTH, modules=[$MODULES], dfs=$DFS_DEPTH)"
echo "╚══════════════════════════════════════════════════════════════╝"

# 1) Core blowup (with optional DFS)
if [ "$SKIP_CORE" = "0" ]; then
  echo ""
  echo "--- STAGE 1: core blowup.hexa ---"
  CORE_ARGS="$DOMAIN $DEPTH $FAST_FLAG"
  if [ "$DFS_DEPTH" != "0" ]; then
    CORE_ARGS="$CORE_ARGS --dfs $DFS_DEPTH"
  fi
  "$HEXA_BIN" "$BLOWUP_CORE" $CORE_ARGS 2>&1 || echo "  [core] exit non-zero, continuing"
fi

# 2) Modules chain (순차 실행 — atlas.n6 기록 누적)
if [ -n "$MODULES" ]; then
  IFS=',' read -ra MOD_ARR <<< "$MODULES"
  for m in "${MOD_ARR[@]}"; do
    m_trim="$(echo "$m" | tr -d ' ')"
    mod_path="$MODULES_DIR/blowup_${m_trim}.hexa"
    if [ ! -f "$mod_path" ]; then
      echo ""
      echo "--- STAGE: $m_trim SKIP (모듈 없음: $mod_path)"
      continue
    fi
    echo ""
    echo "--- STAGE: blowup_${m_trim}.hexa ---"
    # 메모리 제한 2GB, 비상시 SIGKILL 방지
    ulimit -v 2097152 2>/dev/null || true
    "$HEXA_BIN" "$mod_path" 2>&1 || echo "  [$m_trim] exit non-zero, continuing chain"
  done
fi

# 3) 조립 완료 보고 + health
echo ""
echo "--- compose complete ---"
if [ -x "$NEXUS_DIR/shared/n6/atlas_health.sh" ]; then
  "$NEXUS_DIR/shared/n6/atlas_health.sh" "$NEXUS_DIR/shared/n6/atlas.n6" 2>&1 | grep -E "^(===|  (nodes|edges|real|dup|malformed))" || true
fi
