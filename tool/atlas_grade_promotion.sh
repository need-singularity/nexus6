#!/usr/bin/env bash
# tool/atlas_grade_promotion.sh — Tier-2 i6 from improvement_ideas_omega_cycle (2026-04-26)
#
# atlas [7] (heuristic) entry 들 중 cross-source 추가된 것 → [10*] 승급 SUGGEST mode.
# auto-modify 안 함 (raw 71 falsifier-retire-rule + 안전성).
# self-host 회피 (bash + grep, no hexa dep).
#
# 검사 기준:
#   1. id 가 2+ shards 에 등장 → cross-source 첫 신호 (SUGGEST [10*])
#   2. id 가 @X (crossing) members 에 인용 → corroborated (SUGGEST [10*])
#   3. 같은 domain 의 다른 [10*+] entry 와 sibling 관계 → context-promote
#
# usage:
#   tool/atlas_grade_promotion.sh             # all suggestions
#   tool/atlas_grade_promotion.sh --apply     # NOT IMPLEMENTED — safety-blocked
#   tool/atlas_grade_promotion.sh --limit N   # cap
#
# exit codes: 0=PASS (suggestions emitted), 1=usage, 2=no [7] entries
# sentinel: __ATLAS_GRADE_PROMOTE__ scanned=N candidates=C suggested=S
# origin: design/hexa_sim/2026-04-26_improvement_ideas_omega_cycle.json axis_i6

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$HOME/core/nexus}"
ATLAS_MAIN="$NEXUS_ROOT/n6/atlas.n6"
ATLAS_SHARDS_GLOB="$NEXUS_ROOT/n6/atlas.append.*.n6"

LIMIT=20
APPLY=0

while [ $# -gt 0 ]; do
    case "$1" in
        --apply)
            APPLY=1
            echo "ERROR: --apply is intentionally NOT IMPLEMENTED" >&2
            echo "  reason: raw 71 falsifier-retire-rule + safety. Auto-modify of grade is dangerous." >&2
            echo "  workaround: manually update each suggested entry after review." >&2
            exit 1
            ;;
        --limit) LIMIT="$2"; shift 2 ;;
        --help|-h)
            echo "usage: $0 [--limit N]"
            echo "  --limit N   cap suggestions (default 20)"
            echo ""
            echo "criteria for promotion suggestion:"
            echo "  (a) id appears in 2+ shards (cross-source)"
            echo "  (b) id cited in @X crossing members"
            echo ""
            echo "NOTE: --apply is safety-blocked. Suggestions only."
            exit 0
            ;;
        *) echo "unknown: $1" >&2; exit 1 ;;
    esac
done

# Build shard list
SHARDS=()
[ -f "$ATLAS_MAIN" ] && SHARDS+=("$ATLAS_MAIN")
for f in $ATLAS_SHARDS_GLOB; do
    [ -f "$f" ] && SHARDS+=("$f")
done

# Step 1: collect all [7] grade entries
declare -a SEVEN_ENTRIES=()
TOTAL_SEVEN=0
for shard in "${SHARDS[@]}"; do
    while IFS=: read -r line_no line_txt; do
        [ -z "$line_txt" ] && continue
        # extract id and confirm grade is exactly [7] (not [7+token])
        local_id=$(echo "$line_txt" | sed -nE 's/^@[PCFLRSXMTE] ([^ ]+) =.*/\1/p')
        local_grade=$(echo "$line_txt" | sed -nE 's/.*\[([^]]+)\].*$/\1/p')
        [ -z "$local_id" ] && continue
        # match grade exactly "7" or "7*" or "7?" or "7!" (no compound token)
        if echo "$local_grade" | grep -qE '^7[\*\!\?]?$'; then
            SEVEN_ENTRIES+=("$shard|$line_no|$local_id|$local_grade")
            TOTAL_SEVEN=$((TOTAL_SEVEN + 1))
        fi
    done < <(grep -nE '^@[PCFLRSXMTE] [^ ]+ =.*\[7' "$shard" 2>/dev/null)
done

if [ "$TOTAL_SEVEN" -eq 0 ]; then
    echo "__ATLAS_GRADE_PROMOTE__ scanned=0 candidates=0 suggested=0 (no [7] entries found)"
    exit 2
fi

# Step 2: for each [7] entry, count cross-source presence
echo "atlas [7] grade promotion candidates"
echo "─────────────────────────────────────────────────────────────"
echo "criteria: id 가 2+ shards 등장 OR @X members 에 인용"
echo ""

CANDIDATES=0
SUGGESTED=0
for entry in "${SEVEN_ENTRIES[@]}"; do
    IFS='|' read -r shard line_no id grade <<< "$entry"
    # count shards containing this id (any grade)
    shard_count=0
    for s in "${SHARDS[@]}"; do
        if grep -qE "^@[PCFLRSXMTE] ${id} =" "$s" 2>/dev/null; then
            shard_count=$((shard_count + 1))
        fi
    done
    # count @X crossings citing this id (in <- members)
    cx_count=0
    for s in "${SHARDS[@]}"; do
        # @X members 형식: "  <- a, b, c" or "<- id1 id2"
        cx_lines=$(grep -nE "^\s*<-.*${id}" "$s" 2>/dev/null | wc -l | tr -d ' ')
        cx_count=$((cx_count + cx_lines))
    done
    # decision
    suggest=0
    reason=""
    if [ "$shard_count" -ge 2 ]; then
        suggest=1
        reason="cross-shard (in $shard_count shards)"
    fi
    if [ "$cx_count" -ge 1 ]; then
        suggest=1
        if [ -n "$reason" ]; then reason="$reason + "; fi
        reason="${reason}@X-cited (×$cx_count)"
    fi
    if [ "$suggest" = "1" ]; then
        CANDIDATES=$((CANDIDATES + 1))
        if [ "$SUGGESTED" -lt "$LIMIT" ]; then
            printf "  [SUGGEST [10*]]  %s\n" "$id"
            printf "      current: [%s] in %s:%d\n" "$grade" "$(basename "$shard")" "$line_no"
            printf "      reason : %s\n" "$reason"
            echo ""
            SUGGESTED=$((SUGGESTED + 1))
        fi
    fi
done

if [ "$CANDIDATES" -gt "$SUGGESTED" ]; then
    echo "  (showing first $SUGGESTED of $CANDIDATES suggestions; use --limit N for more)"
fi
echo "─────────────────────────────────────────────────────────────"
echo "__ATLAS_GRADE_PROMOTE__ scanned=$TOTAL_SEVEN candidates=$CANDIDATES suggested=$SUGGESTED"
echo ""
echo "NOTE: 본 도구는 SUGGEST mode 만. 실 grade 변경은 manual:"
echo "  1. 각 entry 검토 (origin / source 확인)"
echo "  2. atlas main 또는 shard 의 [7] → [10*] manual edit"
echo "  3. raw 71 falsifier-retire-rule 위배 회피 (auto-promote 안 됨)"
exit 0
