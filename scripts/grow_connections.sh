#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# grow_connections.sh — 미연결 탐색 + 자동 연결
# ═══════════════════════════════════════════════════════════
# BT↔도메인, Atlas↔BT, 렌즈↔도메인 간 누락 연결을 탐지

NEXUS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="${N6_REPO_ROOT:-$HOME/Dev/n6-architecture}"
DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

echo "═══ NEXUS-6 Connection Scanner ═══"
echo "Repo: $REPO_ROOT"
echo ""

# ── 1. BT↔도메인 미연결 ──────────────────────────────────
echo "▶ [1/3] BT↔Domain 연결 스캔..."
ALL_BTS_FILE=$(mktemp)
LINKED_BTS_FILE=$(mktemp)
UNLINKED_FILE=$(mktemp)

grep -oE "BT-[0-9]+" "$REPO_ROOT/docs/breakthrough-theorems.md" 2>/dev/null | sort -u > "$ALL_BTS_FILE" || true
grep -rhoE "BT-[0-9]+" "$REPO_ROOT"/docs/*/hypotheses.md 2>/dev/null | sort -u > "$LINKED_BTS_FILE" || true
comm -23 "$ALL_BTS_FILE" "$LINKED_BTS_FILE" > "$UNLINKED_FILE" 2>/dev/null || true

TOTAL_BTS=$(wc -l < "$ALL_BTS_FILE" | tr -d '[:space:]')
UNLINKED_COUNT=$(wc -l < "$UNLINKED_FILE" | tr -d '[:space:]')
LINKED=$((TOTAL_BTS - UNLINKED_COUNT))

echo "  Total BTs: $TOTAL_BTS"
echo "  Linked: $LINKED"
echo "  Unlinked: $UNLINKED_COUNT"

if [[ "$UNLINKED_COUNT" -gt 0 ]]; then
    echo "  Unlinked: $(cat "$UNLINKED_FILE" | tr '\n' ' ' | head -c 200)"
fi

# ── 2. Atlas↔BT 미연결 ───────────────────────────────────
echo ""
echo "▶ [2/3] Atlas↔BT 연결 스캔..."
ATLAS_BTS_FILE=$(mktemp)
ATLAS_UNLINKED_FILE=$(mktemp)

grep -oE "BT-[0-9]+" "$REPO_ROOT/docs/atlas-constants.md" 2>/dev/null | sort -u > "$ATLAS_BTS_FILE" || true
comm -23 "$ALL_BTS_FILE" "$ATLAS_BTS_FILE" > "$ATLAS_UNLINKED_FILE" 2>/dev/null || true

ATLAS_IN=$(wc -l < "$ATLAS_BTS_FILE" | tr -d '[:space:]')
ATLAS_UNLINKED=$(wc -l < "$ATLAS_UNLINKED_FILE" | tr -d '[:space:]')

echo "  BTs in Atlas: $ATLAS_IN"
echo "  BTs not in Atlas: $ATLAS_UNLINKED"

# ── 3. 도메인별 BT 커버리지 ───────────────────────────────
echo ""
echo "▶ [3/3] Domain coverage..."
NO_BT_DOMAINS=""
NO_BT_COUNT=0
for d in "$REPO_ROOT"/docs/*/; do
    DOMAIN_NAME=$(basename "$d")
    [[ "$DOMAIN_NAME" == "paper" || "$DOMAIN_NAME" == "superpowers" ]] && continue
    if [[ -f "$d/hypotheses.md" ]]; then
        BT_COUNT=$(grep -c "BT-" "$d/hypotheses.md" 2>/dev/null || echo "0")
        if [[ "$BT_COUNT" -eq 0 ]]; then
            NO_BT_DOMAINS="$NO_BT_DOMAINS $DOMAIN_NAME"
            NO_BT_COUNT=$((NO_BT_COUNT + 1))
        fi
    else
        NO_BT_DOMAINS="$NO_BT_DOMAINS ${DOMAIN_NAME}(no-hyp)"
        NO_BT_COUNT=$((NO_BT_COUNT + 1))
    fi
done

if [[ "$NO_BT_COUNT" -gt 0 ]]; then
    echo "  Domains with 0 BT refs ($NO_BT_COUNT):$NO_BT_DOMAINS"
else
    echo "  All domains have BT references ✅"
fi

# ── Summary ───────────────────────────────────────────────
TOTAL_GAPS=$((UNLINKED_COUNT + ATLAS_UNLINKED + NO_BT_COUNT))
echo ""
echo "═══ Connection Summary ═══"
echo "  BT↔Domain unlinked: $UNLINKED_COUNT"
echo "  Atlas↔BT unlinked:  $ATLAS_UNLINKED"
echo "  Zero-BT domains:    $NO_BT_COUNT"
echo "  Total gaps: $TOTAL_GAPS"

# Cleanup
rm -f "$ALL_BTS_FILE" "$LINKED_BTS_FILE" "$UNLINKED_FILE" "$ATLAS_BTS_FILE" "$ATLAS_UNLINKED_FILE"

if [[ "$TOTAL_GAPS" -eq 0 ]]; then
    echo "  ✅ All connections verified — no gaps!"
    exit 0
fi

if $DRY_RUN; then
    echo "  [dry-run] Would connect $TOTAL_GAPS gaps."
    exit 0
fi

echo "  🔗 Gaps found — growth daemon will dispatch connection agents."
exit 0
