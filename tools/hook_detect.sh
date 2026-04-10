#!/bin/bash
# hook_detect.sh — PostToolUse 훅: 상수/수식 자동 감지 마이크로사이클
#
# 설치: settings.json → hooks.PostToolUse에 추가
# {
#   "hooks": {
#     "PostToolUse": [{
#       "matcher": "Bash",
#       "command": "bash ~/Dev/nexus/tools/hook_detect.sh"
#     }]
#   }
# }
#
# 아키텍처 (3단계 게이트 + nexus detect 위임):
#   Gate 1: bash regex — 숫자 패턴 없으면 즉시 exit (0.1ms, 99% 여기서 종료)
#   Gate 2: 노이즈 필터 — 파일 크기/버전/진행률 제거
#   Gate 3: nexus detect — Rust 엔진으로 상수 매칭 + 메타 수렴 검사
#
# 마이크로사이클 (재귀성장):
#   Loop 1 (자기수정): --promote → 반복 출현 상수 자동 승격
#   Loop 2 (메타보상): --adaptive → 소스별 발견율 학습
#   Loop 3 (자기확장): 발견 축적 → blowup 시드 자동 주입

set -euo pipefail

OUTPUT="${TOOL_OUTPUT:-}"

# ── Gate 1: 숫자 패턴 존재 여부 (bash 내장, <0.1ms) ──
[[ "$OUTPUT" =~ [0-9]+\.[0-9]{3,} ]] || exit 0

# ── Gate 2: 노이즈 라인 제거 ──
CLEANED=$(echo "$OUTPUT" | grep -vE \
  'bytes|[KMG]B|version|progress|%|ETA|speed|https?://|\.tar|\.zip|node_modules|target/|Compiling|Downloading|warning\[' \
  2>/dev/null || true)

# 정리 후 숫자 없으면 종료
[[ "$CLEANED" =~ [0-9]+\.[0-9]{3,} ]] || exit 0

# ── Gate 3: nexus detect (Rust 엔진 위임) ──
NEXUS="${HOME}/Dev/nexus/target/release/nexus"

if [ ! -x "$NEXUS" ]; then
  # 바이너리 없으면 조용히 종료
  exit 0
fi

RESULT=$(echo "$CLEANED" | "$NEXUS" detect --min-matches 2 --adaptive --promote 2>/dev/null)

if [ -n "$RESULT" ]; then
  # ── Loop 3: 자기확장 — 임계 축적 감지 시 blowup 시드 자동 주입 ──
  DISCO_PATH="${HOME}/Dev/nexus/shared/discovered_constants.jsonl"
  if [ -f "$DISCO_PATH" ]; then
    DISCO_COUNT=$(wc -l < "$DISCO_PATH" 2>/dev/null || echo 0)
    DISCO_COUNT=$(echo "$DISCO_COUNT" | tr -d ' ')

    # 10건 이상 미처리 발견 축적 시 알림
    if [ "$DISCO_COUNT" -ge 10 ]; then
      echo "🌱 발견 ${DISCO_COUNT}건 축적 — nexus blowup --seed 권장"
    fi
  fi
fi
