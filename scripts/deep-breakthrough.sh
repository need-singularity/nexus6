#!/usr/bin/env bash
# deep-breakthrough.sh — 깊은 탐색: corollary → seed 피드백 루프
# 매 회차 blowup 결과에서 새 EXACT 값을 seed에 주입 → saturation 탈출
set -e

HEXA="$HOME/Dev/hexa-lang/target/release/hexa"
BLOWUP="$HOME/Dev/nexus6/mk2_hexa/native/blowup.hexa"
SEED_ENGINE="$HOME/Dev/nexus6/mk2_hexa/native/seed_engine.hexa"

ROUNDS=${1:-10}
DEPTH=${2:-6}
POOL_CAP=${3:-48}
DOMAINS=("math" "physics")

# 부동소수점 근사 중복 체크: 정수로 반올림한 값이 이미 있으면 중복
is_dup_seed() {
  local val="$1"
  local seeds="$2"
  # 완전 일치 체크
  if echo "$seeds" | tr '|' '\n' | grep -qx "$val"; then
    return 0
  fi
  # 부동소수점 근사 체크: 정수 근사값 비교
  local rounded
  rounded=$(printf "%.0f" "$val" 2>/dev/null) || return 1
  # 기존 seed들 중 같은 정수 근사값이 있는지 확인
  while IFS= read -r existing; do
    [ -z "$existing" ] && continue
    local existing_rounded
    existing_rounded=$(printf "%.0f" "$existing" 2>/dev/null) || continue
    if [ "$rounded" = "$existing_rounded" ]; then
      # 정수 근사가 같으면 — 차이가 0.001 미만인지 추가 확인
      local diff
      diff=$(echo "scale=10; d=$val - $existing; if (d < 0) -d else d" | bc 2>/dev/null) || continue
      local is_close
      is_close=$(echo "$diff < 0.001" | bc 2>/dev/null) || continue
      if [ "$is_close" = "1" ]; then
        return 0
      fi
    fi
  done <<< "$(echo "$seeds" | tr '|' '\n')"
  return 1
}

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  DEEP BREAKTHROUGH — corollary→seed 피드백 루프          ║"
echo "║  rounds=$ROUNDS depth=$DEPTH pool_cap=$POOL_CAP domains=${DOMAINS[*]}       "
echo "╚═══════════════════════════════════════════════════════════╝"

# 초기 seed = seed_engine merge (부동소수점 중복 제거)
RAW_SEEDS=$("$HEXA" "$SEED_ENGINE" merge 2>/dev/null)
# 정수 근사값 기준 중복 제거: 5.999999999999999 vs 6 → 6만 남김
ALL_SEEDS=""
while IFS= read -r sv; do
  [ -z "$sv" ] && continue
  if [ -z "$ALL_SEEDS" ]; then
    ALL_SEEDS="$sv"
  elif ! is_dup_seed "$sv" "$ALL_SEEDS"; then
    ALL_SEEDS="${ALL_SEEDS}|${sv}"
  fi
done <<< "$(echo "$RAW_SEEDS" | tr '|' '\n' | sort -u)"
SEED_COUNT=$(echo "$ALL_SEEDS" | tr '|' '\n' | wc -l | tr -d ' ')
RAW_COUNT=$(echo "$RAW_SEEDS" | tr '|' '\n' | wc -l | tr -d ' ')
echo "  initial seeds: $SEED_COUNT values (raw $RAW_COUNT, deduped)"
echo ""

TOTAL_EXACT=0
TOTAL_COR=0
START=$(date +%s)

# saturation 감지용 변수
prev_total=""
prev_exact=""
sat_count=0

r=1
while [ $r -le $ROUNDS ]; do
  # 도메인 순환
  di=$(( (r - 1) % ${#DOMAINS[@]} ))
  domain="${DOMAINS[$di]}"

  t0=$(date +%s)
  out=$("$HEXA" "$BLOWUP" "$domain" "$DEPTH" --no-graph --seeds "$ALL_SEEDS" --pool-cap "$POOL_CAP" 2>&1)
  t1=$(date +%s)
  elapsed=$((t1 - t0))

  exact=$(echo "$out" | grep "EXACT match" | grep -oE '[0-9]+' | head -1)
  total=$(echo "$out" | grep "total corollaries" | grep -oE '[0-9]+' | head -1)
  pool=$(echo "$out" | grep "final pool" | grep -oE '[0-9]+' | head -1)
  exact=${exact:-0}; total=${total:-0}; pool=${pool:-?}

  TOTAL_EXACT=$((TOTAL_EXACT + exact))
  TOTAL_COR=$((TOTAL_COR + total))

  # saturation 감지: 2연속 동일 결과면 depth +1 (cap=6)
  if [ "$total" = "$prev_total" ] && [ "$exact" = "$prev_exact" ]; then
    sat_count=$((sat_count + 1))
    if [ $sat_count -ge 2 ] && [ $DEPTH -lt 6 ]; then
      DEPTH=$((DEPTH + 1))
      sat_count=0
      echo "  ⚡ saturation 감지 — depth 상승: $((DEPTH - 1)) → $DEPTH"
    fi
  else
    sat_count=0
  fi
  prev_total=$total
  prev_exact=$exact

  # 새 EXACT AXIOM 값 추출 → seed에 추가
  # 개선된 정규식: 소수점 긴 값, 과학 표기법도 포함
  new_vals=$(echo "$out" | grep "EXACT \[AXIOM\]" | grep -oE '= [0-9]+\.?[0-9]*([eE][+-]?[0-9]+)?' | sed 's/= //' | sort -u)
  added=0
  for v in $new_vals; do
    if ! is_dup_seed "$v" "$ALL_SEEDS"; then
      ALL_SEEDS="${ALL_SEEDS}|${v}"
      added=$((added + 1))
    fi
  done

  # 새 NEAR 값도 추가 (탐색 범위 확장)
  new_near=$(echo "$out" | grep "NEAR \[AXIOM\]" | grep -oE '= [0-9]+\.?[0-9]*([eE][+-]?[0-9]+)?' | sed 's/= //' | sort -u)
  for v in $new_near; do
    if ! is_dup_seed "$v" "$ALL_SEEDS"; then
      ALL_SEEDS="${ALL_SEEDS}|${v}"
      added=$((added + 1))
    fi
  done

  cur_seeds=$(echo "$ALL_SEEDS" | tr '|' '\n' | sort -u | wc -l | tr -d ' ')

  printf "  [%2d] %-8s %4d cor %3d EXACT pool=%s +%d new seeds (%d total) d=%d [%ds]\n" \
    "$r" "$domain" "$total" "$exact" "$pool" "$added" "$cur_seeds" "$DEPTH" "$elapsed"

  # cap seeds at 80 to avoid blowup (raised from 50)
  if [ "$cur_seeds" -gt 80 ]; then
    ALL_SEEDS=$(echo "$ALL_SEEDS" | tr '|' '\n' | sort -u | head -80 | tr '\n' '|' | sed 's/|$//')
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
