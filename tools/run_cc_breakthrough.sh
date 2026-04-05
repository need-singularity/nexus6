#!/bin/bash
# Claude Code 효율 특이점 사이클 파이프라인
# 100% 로컬 실행, 외부 API 호출 없음
set -euo pipefail
cd "$(dirname "$0")/.."

DATE=$(date +%Y%m%d)
OUT_DIR="shared/breakthroughs"
mkdir -p "$OUT_DIR"

echo "[1/4] mining Claude Code sessions..."
python3 tools/cc_session_miner.py --sessions 20

echo "[2/4] syncing math atlas..."
if [ -x "shared/sync-math-atlas.sh" ]; then
  bash shared/sync-math-atlas.sh
  sleep 2
else
  echo "WARN: shared/sync-math-atlas.sh not found or not executable, skipping" >&2
fi

echo "[3/4] running nexus6 auto (claude_efficiency) with 30min timeout..."
NEXUS_BIN="${NEXUS_BIN:-nexus6}"
CYCLE_OUT="$OUT_DIR/claude_efficiency_$DATE.json"
# timeout 명령 선택: gtimeout(GNU coreutils) > timeout > 없으면 그대로 실행
if command -v gtimeout >/dev/null 2>&1; then
  TIMEOUT_CMD="gtimeout 1800"
elif command -v timeout >/dev/null 2>&1; then
  TIMEOUT_CMD="timeout 1800"
else
  TIMEOUT_CMD=""
  echo "WARN: no timeout cmd available (install coreutils for gtimeout), running unbounded" >&2
fi
if $TIMEOUT_CMD "$NEXUS_BIN" auto claude_efficiency \
     --meta-cycles 5 --ouroboros-cycles 3 > "$CYCLE_OUT"; then
  echo "cycle done"
else
  rc=$?
  echo "WARN: cycle exit=$rc (timeout=124 or error), continuing with partial output" >&2
fi

echo "[4/4] interpreting breakthrough..."
if [ -s "$CYCLE_OUT" ]; then
  # nexus6 auto는 텍스트를 출력하므로 interpreter용 JSON으로 변환
  # 유효 JSON 아니면 stub JSON으로 감쌈 (현재 도메인 전용 렌즈 없을 시 패턴 0개)
  if ! python3 -c "import json,sys; json.load(open('$CYCLE_OUT'))" 2>/dev/null; then
    TEXT_OUT="${CYCLE_OUT%.json}.txt"
    mv "$CYCLE_OUT" "$TEXT_OUT"
    python3 -c "
import json, re, sys
text = open('$TEXT_OUT').read()
# discovery 카운트 추출
m = re.search(r'Total discoveries:\s*(\d+)', text)
disc = int(m.group(1)) if m else 0
m = re.search(r'Meta-cycles completed:\s*(\d+)', text)
cycles = int(m.group(1)) if m else 0
stub = {
    'domain': 'claude_efficiency',
    'cycles_run': cycles,
    'converged_patterns': [],
    'surviving_hypotheses': [],
    'discovery_log_refs': [],
    '_note': f'synthesized from nexus6 auto text output ({disc} discoveries, no claude_efficiency-specific lenses yet)',
}
json.dump(stub, open('$CYCLE_OUT','w'), indent=2)
print(f'synthesized stub JSON: {disc} discoveries, {cycles} cycles')
"
  fi
  python3 tools/interpret_breakthrough.py "$CYCLE_OUT"
else
  echo "ERROR: cycle output empty, cannot interpret" >&2
  exit 4
fi

echo "done. review: $OUT_DIR/claude_efficiency_rules_$(date +%Y-%m-%d).md"
