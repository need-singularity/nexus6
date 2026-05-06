#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# tooling/smoke/mk2_atlas_smoke.sh — mk2 atlas dispatcher 7-case smoke
#
# 검증 7 케이스 (5 subcommands + 2 help):
#   1) main --help
#   2) atlas --help
#   3) atlas lookup alpha_inv
#   4) atlas hypothesis --grade=🟥★★★★
#   5) atlas recall 0.231
#   6) atlas distribution --by sector
#   7) atlas validate n6/atlas.n6 --quiet           ← NEW (FU-2 통합)
#
# 환경: HEXA_LOCAL=1 HEXA_RESOLVER_NO_REROUTE=1 강제 (운영 SSOT —
# docs/mk2/07-atlas-recall.md § 운영 가이드).
#
# 출력: 각 케이스마다 PASS/FAIL + duration, 마지막에 7/7 요약.
# Exit: 0 = all PASS, 1 = any FAIL.
# ═══════════════════════════════════════════════════════════

set -u

export HEXA_LOCAL=1
export HEXA_RESOLVER_NO_REROUTE=1
export HEXA_RESOLVER_INHERIT_ENV=1

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$REPO_ROOT" || { echo "cannot cd to repo root: $REPO_ROOT"; exit 1; }

MAIN="mk2_hexa/mk2/src/main.hexa"

CMDS=(
  "--help"
  "atlas --help"
  "atlas lookup alpha_inv"
  "atlas hypothesis --grade=🟥★★★★"
  "atlas recall 0.231"
  "atlas distribution --by sector"
  "atlas validate n6/atlas.n6 --quiet"
)

PASS=0
FAIL=0
N=${#CMDS[@]}

printf "═══ mk2 atlas smoke (%d cases) ═══\n" "$N"

for i in "${!CMDS[@]}"; do
  c="${CMDS[$i]}"
  idx=$((i + 1))
  printf "[%d/%d] hexa run %s %s ... " "$idx" "$N" "$MAIN" "$c"

  # shellcheck disable=SC2086
  start_ns=$(python3 -c 'import time;print(time.time_ns())' 2>/dev/null || echo 0)
  out=$(eval "hexa run $MAIN $c 2>&1")
  rc=$?
  end_ns=$(python3 -c 'import time;print(time.time_ns())' 2>/dev/null || echo 0)
  ms=$(( (end_ns - start_ns) / 1000000 ))

  # all cases expected exit 0 (validate w/o --strict on clean atlas.n6 is errors=0)
  if [ "$rc" -eq 0 ]; then
    printf "PASS (rc=0, %dms)\n" "$ms"
    PASS=$((PASS + 1))
  else
    printf "FAIL (rc=%d, %dms)\n" "$rc" "$ms"
    printf "  --- output ---\n%s\n  ---\n" "$out" | head -20
    FAIL=$((FAIL + 1))
  fi
done

printf "\n═══ summary: %d/%d PASS ═══\n" "$PASS" "$N"
[ "$FAIL" -eq 0 ]
