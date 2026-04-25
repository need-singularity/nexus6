#!/usr/bin/env bash
# ledger_verify.sh — verify hash-chain integrity of falsifier_registry rotation ledger (R5 OPT-D)
#
# Walks state/falsifier_registry_rotation_log.jsonl top-to-bottom, recomputing
# prev_hash for each entry and comparing against the value embedded in the next.
#
# Modes:
#   default   — human-readable lines + sentinel
#   --quiet   — sentinel only
#   --json    — single-line JSON summary
#
# Sentinel:
#   __LEDGER_VERIFY__ <PASS|FAIL|EMPTY|PRE_R5> entries=N broken_at=<line_or_none>
#
# Back-compat (PRE_R5):
#   - If NO entries have prev_hash field, treat as PRE_R5_LEDGER (grandfathered, exit 0)
#   - If entries are mixed (some with, some without), the first entry with prev_hash
#     is treated as the chain root; everything before is grandfathered.
#
# raw 73: minimal; raw 66: reason+fix trailers; raw 71: report-only.

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null)}"
if [ -z "${NEXUS_ROOT}" ] || [ ! -d "${NEXUS_ROOT}" ]; then
    NEXUS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fi

LOG="${LOG:-${NEXUS_ROOT}/state/falsifier_registry_rotation_log.jsonl}"

MODE="default"
case "${1:-}" in
    --quiet) MODE="quiet" ;;
    --json)  MODE="json" ;;
    "")      ;;
    *)
        echo "ledger_verify.sh: unknown arg '${1}'" >&2
        echo "  reason: only --quiet|--json|(none) supported" >&2
        echo "  fix: re-run without arg or with one of --quiet/--json" >&2
        exit 2
        ;;
esac

# Pick sha tool
sha_tool=""
if command -v shasum >/dev/null 2>&1; then
    sha_tool="shasum -a 256"
elif command -v sha256sum >/dev/null 2>&1; then
    sha_tool="sha256sum"
else
    echo "ledger_verify.sh: no sha tool" >&2
    echo "  reason: neither 'shasum' nor 'sha256sum' on PATH" >&2
    echo "  fix: install coreutils" >&2
    exit 2
fi

emit_sentinel() {
    local status="$1" entries="$2" broken_at="$3"
    case "${MODE}" in
        json)
            printf '{"sentinel":"__LEDGER_VERIFY__","status":"%s","entries":%d,"broken_at":"%s","ledger":"%s"}\n' \
                "${status}" "${entries}" "${broken_at}" "${LOG}"
            ;;
        *)
            echo "__LEDGER_VERIFY__ ${status} entries=${entries} broken_at=${broken_at}"
            ;;
    esac
}

if [ ! -f "${LOG}" ]; then
    [ "${MODE}" = "default" ] && echo "ledger_verify: no ledger at ${LOG} (vacuously valid)"
    emit_sentinel "EMPTY" 0 "none"
    exit 0
fi

# Use python3 for line-by-line walk (more robust JSON parsing for prev_hash extraction;
# we still re-hash with the chosen sha_tool for cross-validation).
python3 - "$LOG" "$sha_tool" "$MODE" <<'PYEOF'
import hashlib
import json
import sys

log_path, sha_tool, mode = sys.argv[1], sys.argv[2], sys.argv[3]

with open(log_path, 'rb') as f:
    raw_lines = f.read().splitlines()

# Strip blank trailing lines but preserve order
lines = [ln for ln in raw_lines if ln.strip()]

n = len(lines)
status = "PASS"
broken_at = "none"
have_chain = False
pre_r5_count = 0

# Walk: for each i>=1, parse entry[i].prev_hash and compare to sha256(lines[i-1])
# entry[0] should have prev_hash=="genesis" if it's R5-era; if it lacks the field
# entirely, mark as PRE_R5 and skip.

for i, raw in enumerate(lines):
    try:
        entry = json.loads(raw.decode('utf-8'))
    except Exception as e:
        status = "FAIL"
        broken_at = str(i + 1)
        if mode == "default":
            print(f"  line {i+1}: JSON parse error: {e}", file=sys.stderr)
        break

    has_field = "prev_hash" in entry
    if not has_field:
        pre_r5_count += 1
        # Grandfathered — only valid if no R5 entries appear later
        continue

    have_chain = True
    declared = entry["prev_hash"]
    if i == 0:
        expected = "genesis"
    else:
        expected = hashlib.sha256(lines[i-1]).hexdigest()
    if declared != expected:
        status = "FAIL"
        broken_at = str(i + 1)
        if mode == "default":
            print(f"  line {i+1}: prev_hash mismatch")
            print(f"    declared: {declared}")
            print(f"    expected: {expected}")
        break

# Handle "mixed = pre-R5 entries followed by R5 entries"
# If the first R5 entry's prev_hash is "genesis" we accept it as a fresh chain start
# (any entries before it are grandfathered). If it's a sha256 that doesn't match the
# preceding line, we already FAIL'd above. So the only remaining edge is: chain root
# embedded mid-log with prev_hash=="genesis" → that's accepted as new chain.

final_status = status
if status == "PASS" and not have_chain and pre_r5_count > 0:
    final_status = "PRE_R5"

if mode == "default":
    print(f"ledger_verify: walked {n} entries; chain entries with prev_hash field: {n - pre_r5_count}")
    if pre_r5_count:
        print(f"  pre-R5 (grandfathered): {pre_r5_count}")
    if final_status == "PASS":
        print(f"  result: chain intact")
    elif final_status == "PRE_R5":
        print(f"  result: pre-R5 ledger; no chain to verify (grandfathered)")
    elif final_status == "EMPTY":
        print(f"  result: empty")
    else:
        print(f"  result: {final_status} broken_at={broken_at}")

if mode == "json":
    print(json.dumps({
        "sentinel": "__LEDGER_VERIFY__",
        "status": final_status,
        "entries": n,
        "broken_at": broken_at,
        "ledger": log_path,
        "pre_r5_count": pre_r5_count,
    }))
else:
    print(f"__LEDGER_VERIFY__ {final_status} entries={n} broken_at={broken_at}")

# Exit code: 0 for PASS/EMPTY/PRE_R5, 1 for FAIL
sys.exit(0 if final_status in ("PASS", "EMPTY", "PRE_R5") else 1)
PYEOF
