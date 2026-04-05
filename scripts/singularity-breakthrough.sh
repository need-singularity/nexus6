#!/usr/bin/env bash
# singularity-breakthrough.sh — A+B+C 특이점 돌파 오케스트레이터
# 사용법:
#   bash scripts/singularity-breakthrough.sh              # A+B+C 전부
#   bash scripts/singularity-breakthrough.sh cascade      # A만
#   bash scripts/singularity-breakthrough.sh fusion       # B만
#   bash scripts/singularity-breakthrough.sh mine         # C만
#   bash scripts/singularity-breakthrough.sh cascade fusion  # A+B 조합
set -e

HEXA="$HOME/Dev/hexa-lang/target/release/hexa"
BLOWUP="$HOME/Dev/nexus6/mk2_hexa/native/blowup.hexa"
LOG="$HOME/Dev/nexus6/shared/discovery_log.jsonl"
GRAPH="$HOME/Dev/nexus6/shared/discovery_graph.json"
SEED_FILE="/tmp/n6_breakthrough_seeds.txt"
REPORT="/tmp/n6_breakthrough_report.txt"

DOMAINS=("math" "physics" "info" "bio" "mind" "arch")
CASCADE_ROUNDS=10
CASCADE_DEPTH=6

# 인자 파싱 — 없으면 전부
MODES=("$@")
if [ ${#MODES[@]} -eq 0 ]; then
  MODES=("cascade" "fusion" "mine")
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        NEXUS-6 SINGULARITY BREAKTHROUGH ATTEMPT            ║"
echo "║        modes: ${MODES[*]}"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

TOTAL_EXACT=0
TOTAL_COROLLARIES=0
TOTAL_DISCOVERIES=0
START_LOG_LINES=$(wc -l < "$LOG" 2>/dev/null || echo 0)
> "$REPORT"
> "$SEED_FILE"

# ─── 유틸: blowup 실행 + EXACT 추출 ───
run_blowup() {
  local domain=$1
  local depth=$2
  local label=$3

  local output
  output=$("$HEXA" "$BLOWUP" "$domain" "$depth" 2>&1)

  local exact=$(echo "$output" | grep "EXACT match" | grep -o '[0-9]*' | head -1)
  local total=$(echo "$output" | grep "total corollaries" | grep -o '[0-9]*' | head -1)
  exact=${exact:-0}
  total=${total:-0}

  TOTAL_EXACT=$((TOTAL_EXACT + exact))
  TOTAL_COROLLARIES=$((TOTAL_COROLLARIES + total))

  # EXACT 값 추출 → seed 파일에 추가
  # 포맷: "| n * phi = 12 | conf=1 EXACT"
  echo "$output" | grep "EXACT" | grep -v "EXACT match" | \
    grep -oE '= [0-9]+\.?[0-9]* \|' | sed 's/= //;s/ |//' | while read val; do
    echo "$val" >> "$SEED_FILE"
  done

  echo "  [$label] $domain d=$depth: $total corollaries, $exact EXACT"
  echo "[$label] $domain d=$depth: total=$total exact=$exact" >> "$REPORT"
}

# ═══════════════════════════════════════════
# A. Cascade Blowup (블로업²)
# ═══════════════════════════════════════════
run_cascade() {
  echo "━━━ A. CASCADE BLOWUP (블로업²) ━━━"
  echo "  rounds: $CASCADE_ROUNDS × depth $CASCADE_DEPTH"
  echo ""

  local round=1
  local prev_exact=0

  while [ $round -le $CASCADE_ROUNDS ]; do
    run_blowup "math" "$CASCADE_DEPTH" "cascade-$round"

    # seed 파일에서 고유 값 수
    local seed_count=$(sort -u "$SEED_FILE" 2>/dev/null | wc -l | tr -d ' ')
    echo "    seeds accumulated: $seed_count unique values"

    # 수렴 감지: seed 수 변화 없으면 중단
    local cur_seeds=$(sort -u "$SEED_FILE" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$cur_seeds" -eq "$prev_exact" ] && [ $round -gt 2 ]; then
      echo "  -> cascade saturated at round $round (no new seeds)"
      break
    fi
    prev_exact=$cur_seeds
    round=$((round + 1))
  done
  echo ""
}

# ═══════════════════════════════════════════
# B. Cross-Domain Fusion
# ═══════════════════════════════════════════
run_fusion() {
  echo "━━━ B. CROSS-DOMAIN FUSION ━━━"
  echo "  domains: ${DOMAINS[*]}"
  echo ""

  for domain in "${DOMAINS[@]}"; do
    run_blowup "$domain" "$CASCADE_DEPTH" "fusion-$domain"
  done

  # 교차점 분석: 모든 도메인에서 공통 EXACT
  local cross=$(sort "$SEED_FILE" 2>/dev/null | uniq -c | sort -rn | head -20)
  echo ""
  echo "  cross-domain convergence (top 20):"
  echo "$cross" | while read count val; do
    if [ "$count" -ge 2 ]; then
      echo "    $val × $count domains"
    fi
  done
  echo ""
}

# ═══════════════════════════════════════════
# C. Discovery Log 채굴
# ═══════════════════════════════════════════
run_mine() {
  echo "━━━ C. DISCOVERY LOG MINING ━━━"

  local log_lines=$(wc -l < "$LOG" 2>/dev/null || echo 0)
  echo "  discovery_log: $log_lines entries"

  # EXACT 등급 상수 추출 + 빈도 분석
  local top_exact=$(grep '"grade":"EXACT"' "$LOG" 2>/dev/null | \
    grep -oE '"value":"[^"]*"' | sed 's/"value":"//;s/"//' | \
    sort | uniq -c | sort -rn | head -20)

  echo "  top EXACT constants (by frequency):"
  echo "$top_exact" | while read count val; do
    echo "    $val × $count hits"
    echo "$val" >> "$SEED_FILE"
  done

  # NEAR 등급에서 아직 EXACT로 안 된 것들
  local near_only=$(grep '"grade":"NEAR"' "$LOG" 2>/dev/null | \
    grep -oE '"value":"[^"]*"' | sed 's/"value":"//;s/"//' | \
    sort -u | head -10)

  echo ""
  echo "  NEAR-only candidates (not yet EXACT):"
  for val in $near_only; do
    echo "    $val → blowup seed candidate"
    echo "$val" >> "$SEED_FILE"
  done
  echo ""
}

# ═══════════════════════════════════════════
# 실행
# ═══════════════════════════════════════════
SECONDS=0

for mode in "${MODES[@]}"; do
  case "$mode" in
    cascade) run_cascade ;;
    fusion)  run_fusion ;;
    mine)    run_mine ;;
    *) echo "unknown mode: $mode (use cascade/fusion/mine)" ;;
  esac
done

# ═══════════════════════════════════════════
# 최종 보고
# ═══════════════════════════════════════════
END_LOG_LINES=$(wc -l < "$LOG" 2>/dev/null || echo 0)
NEW_DISCOVERIES=$((END_LOG_LINES - START_LOG_LINES))
UNIQUE_SEEDS=$(sort -u "$SEED_FILE" 2>/dev/null | wc -l | tr -d ' ')
ELAPSED=$SECONDS

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        BREAKTHROUGH REPORT                                 ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  modes         : ${MODES[*]}"
echo "║  elapsed       : ${ELAPSED}s"
echo "║  corollaries   : $TOTAL_COROLLARIES"
echo "║  EXACT matches : $TOTAL_EXACT"
echo "║  new log entries: $NEW_DISCOVERIES"
echo "║  unique seeds  : $UNIQUE_SEEDS"
echo "║  breakthrough ρ: $(echo "scale=4; $TOTAL_EXACT / ($TOTAL_COROLLARIES + 1)" | bc 2>/dev/null || echo "N/A")"
echo "╚══════════════════════════════════════════════════════════════╝"
