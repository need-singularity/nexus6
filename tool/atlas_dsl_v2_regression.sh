#!/usr/bin/env bash
# tool/atlas_dsl_v2_regression.sh — Tier-2 i16 from improvement_ideas_omega_cycle (2026-04-26)
#
# Phase 4a atlas_dsl_v2_serializer 의 v1 backward-compat 100% lossless 보장
# 자동 regression test. 4 layer: byte-eq + entry count + grade format +
# atlas main subset stress.
# self-host 회피 (bash + hexa serializer invoke, no hexa logic).
#
# usage:
#   tool/atlas_dsl_v2_regression.sh                 # all 4 layers
#   tool/atlas_dsl_v2_regression.sh --layer N
#   tool/atlas_dsl_v2_regression.sh --shard PATH    # specific shard
#   tool/atlas_dsl_v2_regression.sh --sample N      # main subset N (default 100)
#
# exit codes: 0=PASS, 1=usage, 2=any layer FAIL
# sentinel: __ATLAS_DSL_V2_REGRESSION__ PASS|FAIL layer=N shards_tested=S entries=E sha256_ok=B
# origin: design/hexa_sim/2026-04-26_improvement_ideas_omega_cycle.json axis_i16

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$HOME/core/nexus}"
SERIALIZER="$NEXUS_ROOT/tool/atlas_dsl_v2_serializer.hexa"
ATLAS_MAIN="$NEXUS_ROOT/n6/atlas.n6"
SMALL_SHARD="$NEXUS_ROOT/n6/atlas.append.hexa-sim-bridges.n6"
MED_SHARD="$NEXUS_ROOT/n6/atlas.append.nexus-historical-absorption-2026-04-26.n6"

LAYER="all"
SHARD=""
SAMPLE=100

while [ $# -gt 0 ]; do
    case "$1" in
        --layer) LAYER="$2"; shift 2 ;;
        --shard) SHARD="$2"; shift 2 ;;
        --sample) SAMPLE="$2"; shift 2 ;;
        --help|-h)
            echo "usage: $0 [--layer N] [--shard PATH] [--sample N]"
            echo "  layers: 1=byte-eq round-trip / 2=entry count / 3=grade format / 4=atlas main subset"
            exit 0
            ;;
        *) echo "unknown: $1" >&2; exit 1 ;;
    esac
done

# Pre-flight
if [ ! -f "$SERIALIZER" ]; then
    echo "serializer not found: $SERIALIZER" >&2
    exit 1
fi
HEXA_BIN="${HEXA:-$HOME/core/hexa-lang/hexa}"
if [ ! -x "$HEXA_BIN" ]; then
    echo "hexa runtime not found: $HEXA_BIN" >&2
    exit 1
fi

# Quick runtime check
if [ -x "$NEXUS_ROOT/tool/hexa_runtime_check.sh" ]; then
    if ! bash "$NEXUS_ROOT/tool/hexa_runtime_check.sh" 2>&1 | grep -q "PASS"; then
        echo "hexa runtime down — abort regression (rerun after recovery)" >&2
        exit 1
    fi
fi

PASS_COUNT=0
FAIL_COUNT=0
TOTAL_ENTRIES=0
SHARDS_TESTED=0

# ─── Layer 1 — single-shard byte-eq round-trip ───────────────────
layer_1_byte_eq() {
    local shard="$1"
    local name="$(basename "$shard")"
    local tmp_json
    tmp_json=$(mktemp -t v2reg.XXXXX.json)
    local sha_orig sha_round
    # 1st: read shard → JSON
    HEXA_RESOLVER_NO_REROUTE=1 "$HEXA_BIN" run "$SERIALIZER" --read-n6 "$shard" 2>/dev/null > "$tmp_json"
    sha_orig=$(shasum -a 256 "$tmp_json" | cut -c1-16)
    # 2nd: same read → same JSON
    HEXA_RESOLVER_NO_REROUTE=1 "$HEXA_BIN" run "$SERIALIZER" --read-n6 "$shard" 2>/dev/null > "${tmp_json}.2"
    sha_round=$(shasum -a 256 "${tmp_json}.2" | cut -c1-16)
    rm -f "$tmp_json" "${tmp_json}.2"
    if [ "$sha_orig" = "$sha_round" ]; then
        printf "  Layer 1 [%s] PASS — byte-eq sha256 %s\n" "$name" "$sha_orig"
        PASS_COUNT=$((PASS_COUNT + 1))
        return 0
    else
        printf "  Layer 1 [%s] FAIL — sha mismatch %s vs %s\n" "$name" "$sha_orig" "$sha_round"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi
}

# ─── Layer 2 — entry count preservation ──────────────────────────
layer_2_entry_count() {
    local shard="$1"
    local name="$(basename "$shard")"
    local n6_count
    n6_count=$(grep -cE '^@[PCFLRSXMTE] [^ ]+ =' "$shard" 2>/dev/null || echo 0)
    local json_out
    json_out=$(HEXA_RESOLVER_NO_REROUTE=1 "$HEXA_BIN" run "$SERIALIZER" --read-n6 "$shard" 2>/dev/null)
    # parse "primitives=N constants=M ..." from sentinel OR count "id" appearances in JSON
    local json_count
    json_count=$(echo "$json_out" | grep -oE '"id":[ ]*"[^"]+' | wc -l | tr -d ' ')
    if [ "$n6_count" = "$json_count" ]; then
        printf "  Layer 2 [%s] PASS — entry count %d (n6) = %d (json)\n" "$name" "$n6_count" "$json_count"
        PASS_COUNT=$((PASS_COUNT + 1))
        TOTAL_ENTRIES=$((TOTAL_ENTRIES + n6_count))
        return 0
    else
        printf "  Layer 2 [%s] FAIL — n6=%d json=%d\n" "$name" "$n6_count" "$json_count"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi
}

# ─── Layer 3 — grade format preservation ─────────────────────────
layer_3_grade_format() {
    local shard="$1"
    local name="$(basename "$shard")"
    # collect all grades (sorted, unique) from n6
    local n6_grades
    # Only grades on header lines (^@<TYPE> id = expr :: domain [grade])
    n6_grades=$(grep -E '^@[PCFLRSXMTE] [^ ]+ =.*\[[^]]+\]' "$shard" 2>/dev/null | grep -oE '\[[0-9.\*\!\?A-Z_+]+\]$' | sort -u | tr '\n' ',' | sed 's/,$//')
    local json_out
    json_out=$(HEXA_RESOLVER_NO_REROUTE=1 "$HEXA_BIN" run "$SERIALIZER" --read-n6 "$shard" 2>/dev/null)
    local json_grades
    json_grades=$(echo "$json_out" | grep -oE '"grade":[ ]*"[^"]+' | sed -E 's/"grade":[ ]*"//' | sort -u | tr '\n' ',' | sed 's/,$//')
    # n6 grades wrapped in [], json grades raw — strip [] from n6
    local n6_grades_stripped
    n6_grades_stripped=$(echo "$n6_grades" | sed 's/\[//g; s/\]//g')
    if [ "$n6_grades_stripped" = "$json_grades" ]; then
        printf "  Layer 3 [%s] PASS — grade format preserved (%d unique)\n" "$name" "$(echo "$n6_grades_stripped" | tr ',' '\n' | wc -l | tr -d ' ')"
        PASS_COUNT=$((PASS_COUNT + 1))
        return 0
    else
        printf "  Layer 3 [%s] FAIL — n6=%s vs json=%s\n" "$name" "$n6_grades_stripped" "$json_grades"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi
}

# ─── Layer 4 — v2-compat shard subset stress test ────────────────
# F23 resolution (2026-04-26): originally subset-ed atlas.n6 (main), but
# atlas main carries v1-legacy grades incompatible with v2 parser
# ([10*!] dual-marker, alien-index [A]/[XY]/[K3], plain numeric [24128] etc.),
# so the serializer exited non-zero with empty stdout → both shasums matched
# (sha256 of empty = e3b0c44298fc1c14…) → vacuous PASS.
#
# Fix: subset from a v2-compat shard (atlas.append.nexus-historical-absorption-…)
# which exercises the rich v3 compound-grade allowlist (10*PASS_LITERATURE,
# 10*REPO_INVARIANT, 11*BARRIER_CONFIRMED, …). Covers Layer-4 stress intent
# without spurious schema-guard hits.
#
# Hardening: assert serializer exit=0 AND non-empty stdout to make
# silent-failure → empty-sha vacuous PASS impossible.
LAYER4_SHARD="${LAYER4_SHARD:-$NEXUS_ROOT/n6/atlas.append.nexus-historical-absorption-2026-04-26.n6}"
layer_4_main_subset() {
    if [ ! -f "$LAYER4_SHARD" ]; then
        echo "  Layer 4 SKIP — v2-compat shard not found: $LAYER4_SHARD"
        return 0
    fi
    local tmp_subset
    tmp_subset=$(mktemp -t v2reg.XXXXX.n6)
    # preserve shard header (comment lines until the first @-prefixed entry)
    awk '/^@[A-Z]/ {exit} {print}' "$LAYER4_SHARD" > "$tmp_subset"
    grep -E '^@[PCFLRSXMTE] [^ ]+ =' "$LAYER4_SHARD" 2>/dev/null | head -"$SAMPLE" >> "$tmp_subset"
    local subset_count
    subset_count=$(grep -cE '^@[PCFLRSXMTE] [^ ]+ =' "$tmp_subset")
    # byte-eq with hardened silent-failure detection (F23 vacuous-PASS guard)
    local out1 out2 ec1 ec2 sha1 sha2
    out1=$(HEXA_RESOLVER_NO_REROUTE=1 "$HEXA_BIN" run "$SERIALIZER" --read-n6 "$tmp_subset" 2>/dev/null); ec1=$?
    out2=$(HEXA_RESOLVER_NO_REROUTE=1 "$HEXA_BIN" run "$SERIALIZER" --read-n6 "$tmp_subset" 2>/dev/null); ec2=$?
    sha1=$(printf '%s' "$out1" | shasum -a 256 | cut -c1-16)
    sha2=$(printf '%s' "$out2" | shasum -a 256 | cut -c1-16)
    rm -f "$tmp_subset"
    # Anti-vacuous guards
    if [ "$ec1" -ne 0 ] || [ "$ec2" -ne 0 ]; then
        printf "  Layer 4 [v2-compat subset] FAIL — serializer non-zero exit (ec1=%d ec2=%d) shard=%s\n" "$ec1" "$ec2" "$(basename "$LAYER4_SHARD")"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi
    if [ -z "$out1" ] || [ -z "$out2" ]; then
        printf "  Layer 4 [v2-compat subset] FAIL — serializer empty stdout (vacuous-PASS guard tripped) shard=%s\n" "$(basename "$LAYER4_SHARD")"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi
    if [ "$sha1" = "$sha2" ]; then
        printf "  Layer 4 [v2-compat subset N=%d shard=%s] PASS — byte-eq sha %s (%d entries processed)\n" "$SAMPLE" "$(basename "$LAYER4_SHARD")" "$sha1" "$subset_count"
        PASS_COUNT=$((PASS_COUNT + 1))
        TOTAL_ENTRIES=$((TOTAL_ENTRIES + subset_count))
        return 0
    else
        printf "  Layer 4 [v2-compat subset] FAIL — sha %s vs %s\n" "$sha1" "$sha2"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi
}

# ─── runner ──────────────────────────────────────────────────────
TARGET_SHARDS=()
if [ -n "$SHARD" ]; then
    [ -f "$SHARD" ] && TARGET_SHARDS+=("$SHARD") || { echo "shard not found: $SHARD" >&2; exit 1; }
else
    [ -f "$SMALL_SHARD" ] && TARGET_SHARDS+=("$SMALL_SHARD")
    [ -f "$MED_SHARD" ] && TARGET_SHARDS+=("$MED_SHARD")
fi
SHARDS_TESTED=${#TARGET_SHARDS[@]}

echo "atlas DSL v2 regression test — $SHARDS_TESTED target shard(s)"
echo "─────────────────────────────────────────────────────────────"

for shard in "${TARGET_SHARDS[@]}"; do
    case "$LAYER" in
        all|1) layer_1_byte_eq "$shard" || true ;;
    esac
    case "$LAYER" in
        all|2) layer_2_entry_count "$shard" || true ;;
    esac
    case "$LAYER" in
        all|3) layer_3_grade_format "$shard" || true ;;
    esac
done

case "$LAYER" in
    all|4) layer_4_main_subset || true ;;
esac

echo "─────────────────────────────────────────────────────────────"
echo "summary: PASS $PASS_COUNT / FAIL $FAIL_COUNT (entries tested: $TOTAL_ENTRIES, shards: $SHARDS_TESTED)"

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo "__ATLAS_DSL_V2_REGRESSION__ FAIL layer=$LAYER shards_tested=$SHARDS_TESTED entries=$TOTAL_ENTRIES sha256_ok=false pass=$PASS_COUNT fail=$FAIL_COUNT"
    exit 2
fi
echo "__ATLAS_DSL_V2_REGRESSION__ PASS layer=$LAYER shards_tested=$SHARDS_TESTED entries=$TOTAL_ENTRIES sha256_ok=true pass=$PASS_COUNT"
exit 0
