#!/usr/bin/env bash
# tool/atlas_falsifier_auto_spawn.sh — Tier-1 i11 from improvement_ideas_omega_cycle (2026-04-26)
#                                       i11-hardened (2026-04-26): cmd template anchors VALUE+DOMAIN+GRADE
#
# atlas high-grade entries ([10*+] / [11*+]) 에서 falsifier candidate 자동 spawn.
# 각 entry → F<NN> template (claim/cmd/pass/reason/fix/origin) emit.
# falsifiers.jsonl 직접 mutate 안 함 (suggest mode, raw 71 manual escalate).
# self-host 회피 (bash + grep + sed only, no hexa dep).
#
# Evolution: i11 (PRESENCE-only) → i11-hardened (VALUE+DOMAIN+GRADE anchored).
#   - i11 PRESENCE-only:  ^@P n =                 → passes even if value drifts (6→7)
#   - i11-hardened:       ^@P n = 6 :: foundation \[11\*\]  → catches value/domain/grade drift
# Trigger: design/hexa_sim/F13_F22_candidate_review.md — all 10 auto-spawn cmds flagged REWRITE
#   because PRESENCE check is vacuous against silent-drift threats.
# raw 73 admissibility: hardened cmd is the default; --legacy-cmd preserves the old PRESENCE-only
#   template for diagnostic / replay against pre-hardened candidate baselines.
#
# usage:
#   tool/atlas_falsifier_auto_spawn.sh                      # all candidates (hardened cmd)
#   tool/atlas_falsifier_auto_spawn.sh --type T             # filter by @type
#   tool/atlas_falsifier_auto_spawn.sh --grade G            # filter by grade
#   tool/atlas_falsifier_auto_spawn.sh --emit-jsonl         # emit JSONL to state/
#   tool/atlas_falsifier_auto_spawn.sh --limit N
#   tool/atlas_falsifier_auto_spawn.sh --legacy-cmd         # use PRESENCE-only template (pre-hardened)
#
# exit codes: 0=PASS, 1=usage, 2=no candidates
# sentinel: __ATLAS_FALSIFIER_SPAWN__ scanned=N candidates=C suggested=S existing=E mode=<hardened|legacy>
# origin: design/hexa_sim/2026-04-26_improvement_ideas_omega_cycle.json axis_i11
# hardening: design/hexa_sim/2026-04-26_i11_cmd_hardening_omega_cycle.json

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$HOME/core/nexus}"
ATLAS_INDEX="$NEXUS_ROOT/state/atlas_index.tsv"
FALSIFIERS="$NEXUS_ROOT/design/hexa_sim/falsifiers.jsonl"
CANDIDATES_PATH="$NEXUS_ROOT/state/falsifier_candidates.jsonl"
mkdir -p "$NEXUS_ROOT/state" 2>/dev/null

TYPE_FILTER=""
GRADE_FILTER=""
LIMIT=20
EMIT_JSONL=0
LEGACY_CMD=0

while [ $# -gt 0 ]; do
    case "$1" in
        --type) TYPE_FILTER="$2"; shift 2 ;;
        --grade) GRADE_FILTER="$2"; shift 2 ;;
        --limit) LIMIT="$2"; shift 2 ;;
        --emit-jsonl) EMIT_JSONL=1; shift ;;
        --legacy-cmd) LEGACY_CMD=1; shift ;;
        --help|-h)
            echo "usage: $0 [--type T] [--grade G] [--emit-jsonl] [--limit N] [--legacy-cmd]"
            echo "  --type T:        filter by @type (P/C/F/L/R/S/X/M/T/E)"
            echo "  --grade G:       filter by grade (e.g. '11', '10*')"
            echo "  --emit-jsonl:    write candidates to state/falsifier_candidates.jsonl"
            echo "  --limit N:       cap output (default 20)"
            echo "  --legacy-cmd:    emit PRESENCE-only cmd (pre-2026-04-26 template); default = hardened"
            echo ""
            echo "cmd template modes:"
            echo "  hardened (default): grep -qE '^@P mu = mobius\\(6\\) = 1 :: foundation \\[10\\*\\]' …"
            echo "                      anchors VALUE+DOMAIN+GRADE — value drift triggers HIT"
            echo "  legacy:             grep -qE '^@P mu =' …"
            echo "                      PRESENCE only — passes even if value drifts (vacuous)"
            echo "  pass sentinel: <ID_UPPERCASE>_ANCHOR_INTACT (hardened) / PRESENT_<ID>_<TYPE> (legacy)"
            exit 0
            ;;
        *) echo "unknown: $1" >&2; exit 1 ;;
    esac
done

# Pre-flight: index must exist
if [ ! -f "$ATLAS_INDEX" ]; then
    echo "atlas index not found at $ATLAS_INDEX — run: bash tool/atlas_index.sh" >&2
    exit 1
fi

# Step 1: load existing falsifier ids (skip duplicates)
existing_ids=""
if [ -f "$FALSIFIERS" ]; then
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        local_id=$(echo "$line" | sed -nE 's/.*"id":"([^"]+)".*/\1/p')
        local_origin=$(echo "$line" | sed -nE 's/.*"origin":"([^"]+)".*/\1/p')
        # extract atlas id mentioned in origin
        atlas_id=$(echo "$local_origin" | grep -oE '\b[a-zA-Z][a-zA-Z0-9_]+\b' | head -1)
        [ -n "$atlas_id" ] && existing_ids="$existing_ids|$atlas_id|"
    done < "$FALSIFIERS"
fi
EXISTING_COUNT=$({ grep -cE '^\{"id":"F' "$FALSIFIERS" 2>/dev/null || true; } | head -n1)
EXISTING_COUNT=${EXISTING_COUNT:-0}

# Step 2: scan high-grade entries (use atlas_search shard reading)
SCANNED=0
CANDIDATES=0
SUGGESTED=0
NEXT_F=$((EXISTING_COUNT + 1))

# Truncate candidates jsonl if emit mode
[ "$EMIT_JSONL" = "1" ] && > "$CANDIDATES_PATH"

echo "atlas → falsifier auto-spawn candidates"
echo "─────────────────────────────────────────────────────────────"
echo "criteria: high-grade [10*+] or [11*+] entries with re-fetchable cmd"
echo "existing falsifiers: $EXISTING_COUNT (F1..F$EXISTING_COUNT)"
echo ""

# Read atlas index, filter high-grade by re-grepping the source line
while IFS=$'\t' read -r id type line shard; do
    [ "$id" = "id" ] && continue  # skip header
    SCANNED=$((SCANNED + 1))
    # Apply --type filter
    [ -n "$TYPE_FILTER" ] && [ "$type" != "$TYPE_FILTER" ] && continue
    # Read the actual line + extract grade
    full_path="$NEXUS_ROOT/$shard"
    [ ! -f "$full_path" ] && continue
    line_txt=$(sed -n "${line}p" "$full_path" 2>/dev/null)
    [ -z "$line_txt" ] && continue
    grade=$(echo "$line_txt" | sed -nE 's/.*\[([^]]+)\].*$/\1/p')
    # Apply --grade filter (must START with the filter, e.g. "11" matches "11*REPO_INVARIANT")
    if [ -n "$GRADE_FILTER" ]; then
        if ! echo "$grade" | grep -qE "^${GRADE_FILTER}"; then continue; fi
    fi
    # Default high-grade only: must contain '*' (10*+ / 11*+)
    if [ -z "$GRADE_FILTER" ]; then
        if ! echo "$grade" | grep -q '\*'; then continue; fi
    fi
    # Skip if id already mentioned in existing falsifier origin (use -F so ids with . / * stay literal)
    if echo "$existing_ids" | grep -qF "|$id|"; then continue; fi
    CANDIDATES=$((CANDIDATES + 1))
    if [ "$SUGGESTED" -ge "$LIMIT" ]; then continue; fi

    # Build candidate falsifier template
    fid="F${NEXT_F}"
    NEXT_F=$((NEXT_F + 1))
    SUGGESTED=$((SUGGESTED + 1))
    slug=$(echo "$id" | tr '[:upper:]_' '[:lower:]-' | sed 's/[^a-z0-9-]//g')
    expr=$(echo "$line_txt" | sed -nE 's/^@[PCFLRSXMTE] [^ ]+ = (.+) :: .*$/\1/p')
    domain=$(echo "$line_txt" | sed -nE 's/.* :: ([^ ]+) \[.*$/\1/p')
    id_upper=$(echo "$id" | tr '[:lower:]' '[:upper:]')

    # Build cmd template — hardened (default) anchors VALUE+DOMAIN+GRADE; legacy is PRESENCE-only.
    if [ "$LEGACY_CMD" = "1" ]; then
        # Legacy PRESENCE-only template (pre-2026-04-26): vacuous against value drift.
        cmd="grep -qE '^@${type} ${id} =' /Users/ghost/core/nexus/${shard} && echo PRESENT_${id_upper}_${type}"
        pass="PRESENT_${id_upper}_${type}"
        reason="atlas entry @${type} ${id} (current grade [${grade}]) was retired or removed from ${shard} — implies underlying claim '${expr}' no longer holds in domain ${domain}"
    else
        # Hardened template (i11-hardened): regex-escape expr + grade for grep -E full-line anchor.
        # Escape: ( ) [ ] { } . * + ? ^ $ | \  → BRE/ERE metacharacters that must be literal here.
        expr_esc=$(printf '%s' "$expr" | sed 's/[][(){}.*+?^$|\\]/\\&/g')
        grade_esc=$(printf '%s' "$grade" | sed 's/[][(){}.*+?^$|\\]/\\&/g')
        cmd="grep -qE '^@${type} ${id} = ${expr_esc} :: ${domain} \\[${grade_esc}\\]' /Users/ghost/core/nexus/${shard} && echo ${id_upper}_ANCHOR_INTACT"
        pass="${id_upper}_ANCHOR_INTACT"
        reason="atlas entry @${type} ${id} = ${expr} :: ${domain} [${grade}] drifted in value, domain, or grade — anchor break implies the underlying claim no longer holds at the literal it was promoted on"
    fi
    fix="re-verify source (origin shard ${shard} line ${line}); if intentional retirement, update falsifier registry and atlas concurrently — reason=anchor_break fix=audit_origin_then_decide"
    origin="auto-spawn from atlas_index entry ${id} (@${type}, [${grade}], ${shard}:${line})"

    if [ "$EMIT_JSONL" = "1" ]; then
        # JSON-escape: backslashes (\ → \\) then double-quotes (" → \"). cmd carries regex
        # backslashes (e.g. \[ \*) — those must become \\[ \\* in the JSON string so the
        # decoded value is the literal grep pattern. Apply to all fields that can carry meta.
        cmd_j=$(printf '%s' "$cmd"     | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')
        expr_j=$(printf '%s' "$expr"   | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')
        domain_j=$(printf '%s' "$domain" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')
        reason_j=$(printf '%s' "$reason" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')
        fix_j=$(printf '%s' "$fix"     | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')
        origin_j=$(printf '%s' "$origin" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')
        printf '{"id":"%s","slug":"%s","claim":"atlas entry %s = %s remains @%s in %s","cmd":"%s","pass":"%s","reason":"%s","fix":"%s","origin":"%s"}\n' \
            "$fid" "$slug" "$id" "$expr_j" "$type" "$domain_j" "$cmd_j" "$pass" "$reason_j" "$fix_j" "$origin_j" >> "$CANDIDATES_PATH"
    else
        printf "  %s [%s]  @%s %s [%s]\n" "$fid" "$slug" "$type" "$id" "$grade"
        printf "      claim:  atlas entry @%s %s remains in %s\n" "$type" "$id" "$shard"
        printf "      origin: %s:%s\n" "$shard" "$line"
        echo ""
    fi
done < "$ATLAS_INDEX"

echo "─────────────────────────────────────────────────────────────"
if [ "$EMIT_JSONL" = "1" ]; then
    echo "JSONL emitted: $CANDIDATES_PATH"
    echo "  $(wc -l < "$CANDIDATES_PATH" | tr -d ' ') candidates written"
fi
if [ "$LEGACY_CMD" = "1" ]; then
    MODE_TAG="legacy"
else
    MODE_TAG="hardened"
fi
echo "__ATLAS_FALSIFIER_SPAWN__ scanned=$SCANNED candidates=$CANDIDATES suggested=$SUGGESTED existing=$EXISTING_COUNT mode=$MODE_TAG"
echo ""
if [ "$CANDIDATES" -gt "$SUGGESTED" ]; then
    echo "(showing first $SUGGESTED of $CANDIDATES candidates; use --limit N for more)"
fi
echo ""
echo "NOTE: SUGGEST mode 만 — falsifiers.jsonl 직접 mutate 안 함."
echo "  manual merge: review state/falsifier_candidates.jsonl + cat 추가:"
echo "    cat state/falsifier_candidates.jsonl >> design/hexa_sim/falsifiers.jsonl"
echo "  raw 71 정신 (manual escalate, no auto-promote)."
exit 0
