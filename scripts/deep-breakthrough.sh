#!/usr/bin/env bash
# deep-breakthrough.sh — 깊은 탐색: corollary → seed 피드백 루프
# 매 회차 blowup 결과에서 새 EXACT 값을 seed에 주입 → saturation 탈출
set -e

HEXA="$HOME/Dev/hexa-lang/target/release/hexa"
BLOWUP="$HOME/Dev/nexus6/mk2_hexa/native/blowup.hexa"
SEED_ENGINE="$HOME/Dev/nexus6/mk2_hexa/native/seed_engine.hexa"

ROUNDS=${1:-10}
DEPTH=${2:-6}
DOMAINS=("math" "physics")

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  DEEP BREAKTHROUGH — corollary→seed 피드백 루프          ║"
echo "║  rounds=$ROUNDS depth=$DEPTH domains=${DOMAINS[*]}       "
echo "╚═══════════════════════════════════════════════════════════╝"

# 초기 seed = seed_engine merge
SEEDS=$("$HEXA" "$SEED_ENGINE" merge 2>/dev/null)
SEED_COUNT=$(echo "$SEEDS" | tr '|' '\n' | wc -l | tr -d ' ')
echo "  initial seeds: $SEED_COUNT values"
echo ""

TOTAL_EXACT=0
TOTAL_COR=0
ALL_SEEDS="$SEEDS"
START=$(date +%s)

r=1
while [ $r -le $ROUNDS ]; do
  # 도메인 순환
  di=$(( (r - 1) % ${#DOMAINS[@]} ))
  domain="${DOMAINS[$di]}"

  t0=$(date +%s)
  out=$("$HEXA" "$BLOWUP" "$domain" "$DEPTH" --no-graph --seeds "$ALL_SEEDS" 2>&1)
  t1=$(date +%s)
  elapsed=$((t1 - t0))

  exact=$(echo "$out" | grep "EXACT match" | grep -oE '[0-9]+' | head -1)
  total=$(echo "$out" | grep "total corollaries" | grep -oE '[0-9]+' | head -1)
  pool=$(echo "$out" | grep "final pool" | grep -oE '[0-9]+' | head -1)
  exact=${exact:-0}; total=${total:-0}; pool=${pool:-?}

  TOTAL_EXACT=$((TOTAL_EXACT + exact))
  TOTAL_COR=$((TOTAL_COR + total))

  # 새 EXACT AXIOM 값 추출 → seed에 추가
  new_vals=$(echo "$out" | grep "EXACT \[AXIOM\]" | grep -oE '= [0-9]+\.?[0-9]* ' | sed 's/= //' | sort -u)
  added=0
  for v in $new_vals; do
    if ! echo "$ALL_SEEDS" | tr '|' '\n' | grep -qx "$v"; then
      ALL_SEEDS="${ALL_SEEDS}|${v}"
      added=$((added + 1))
    fi
  done

  # 새 NEAR 값도 추가 (탐색 범위 확장)
  new_near=$(echo "$out" | grep "NEAR \[AXIOM\]" | grep -oE '= [0-9]+\.?[0-9]* ' | sed 's/= //' | sort -u)
  for v in $new_near; do
    if ! echo "$ALL_SEEDS" | tr '|' '\n' | grep -qx "$v"; then
      ALL_SEEDS="${ALL_SEEDS}|${v}"
      added=$((added + 1))
    fi
  done

  cur_seeds=$(echo "$ALL_SEEDS" | tr '|' '\n' | sort -u | wc -l | tr -d ' ')

  printf "  [%2d] %-8s %4d cor %3d EXACT pool=%s +%d new seeds (%d total) [%ds]\n" \
    "$r" "$domain" "$total" "$exact" "$pool" "$added" "$cur_seeds" "$elapsed"

  # cap seeds at 50 to avoid blowup
  if [ "$cur_seeds" -gt 50 ]; then
    ALL_SEEDS=$(echo "$ALL_SEEDS" | tr '|' '\n' | sort -u | head -50 | tr '\n' '|' | sed 's/|$//')
  fi

  r=$((r + 1))
done

END=$(date +%s)
ELAPSED=$((END - START))
FINAL_SEEDS=$(echo "$ALL_SEEDS" | tr '|' '\n' | sort -u | wc -l | tr -d ' ')
RHO=$(echo "scale=4; $TOTAL_EXACT / ($TOTAL_COR + 1)" | bc 2>/dev/null || echo "?")

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  RESULT: ${ELAPSED}s | ${TOTAL_COR} cor | ${TOTAL_EXACT} EXACT | ρ=$RHO"
echo "║  seeds: $SEED_COUNT → $FINAL_SEEDS (피드백 성장)"
echo "║  새 발견 seed:"
echo "$ALL_SEEDS" | tr '|' '\n' | sort -u | tail -10 | while read v; do
  echo "║    $v"
done
echo "╚═══════════════════════════════════════════════════════════╝"
