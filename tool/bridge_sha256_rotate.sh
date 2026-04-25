#!/usr/bin/env bash
# tool/bridge_sha256_rotate.sh — R5 chain extension to bridge_sha256.tsv (2026-04-26)
#
# Detects bridge .hexa files whose live SHA256 differs from the per-bridge baseline
# in state/bridge_sha256.tsv. For each drift: rotates the TSV row (col 3 sha + col 4
# last_verified_utc) and appends a hash-chained ledger entry to
# state/bridge_sha256_rotation_log.jsonl using the same R5 OPT-D pattern as the
# falsifier registry rotation log (`prev_hash` = sha256(prev_line) | "genesis").
#
# Why a standalone tool (not a pre-commit hook):
#   .githooks/ was retired in commit e3137be2 by the user. R5 chain extension must
#   honour that decision. This tool is invokable by cron, manually, or by any future
#   automation — without resurrecting the deleted hook.
#
# Modes:
#   default                  — scan + rotate any drift; print human summary + sentinel
#   --dry-run                — scan + report drift only; never mutate TSV/ledger
#   --bridge <name>          — scan only the named bridge (e.g. codata)
#   --reason <text>          — record per-rotation reason in ledger (raw 73 admissibility)
#   --quiet                  — sentinel only
#   --json                   — JSON summary on stdout
#
# Sentinel (raw 80, additive only):
#   __BRIDGE_ROTATE__ <PASS|FAIL|EMPTY> scanned=N rotated=K dry_run=<0|1>
#
# Exit:
#   0  all-clean OR rotation completed cleanly OR dry-run reporting drift
#   1  usage / infra error
#
# Compliance:
#   raw 66 — reason+fix trailers on every error path
#   raw 71 — REPORTS+ROTATES baseline only; never modifies bridge .hexa contents
#   raw 73 — minimal: bash 3.2 portable, no python required
#   raw 77 — additive: leaves untouched TSV rows + comment lines verbatim
#   raw 80 — sentinel evolution backward-compat (new tool ⇒ no prior surface to break)
#
# Verify chain integrity afterwards with:
#   bash tool/ledger_verify.sh --ledger bridge

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null)}"
if [ -z "${NEXUS_ROOT}" ] || [ ! -d "${NEXUS_ROOT}" ]; then
    NEXUS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fi

BRIDGE_TSV="${NEXUS_ROOT}/state/bridge_sha256.tsv"
BRIDGE_LOG="${NEXUS_ROOT}/state/bridge_sha256_rotation_log.jsonl"

DRY_RUN=0
QUIET=0
JSON=0
ONLY_BRIDGE=""
REASON=""

while [ "$#" -gt 0 ]; do
    case "${1:-}" in
        --dry-run) DRY_RUN=1; shift ;;
        --quiet)   QUIET=1; shift ;;
        --json)    JSON=1; shift ;;
        --bridge)
            shift
            if [ "$#" -eq 0 ]; then
                echo "bridge_sha256_rotate: --bridge requires a name" >&2
                echo "  reason: missing arg after --bridge" >&2
                echo "  fix: --bridge codata | --bridge oeis | ..." >&2
                exit 1
            fi
            ONLY_BRIDGE="${1}"; shift
            ;;
        --reason)
            shift
            if [ "$#" -eq 0 ]; then
                echo "bridge_sha256_rotate: --reason requires text" >&2
                echo "  reason: missing arg after --reason" >&2
                echo "  fix: --reason 'legitimate edit per commit abc123'" >&2
                exit 1
            fi
            REASON="${1}"; shift
            ;;
        --help|-h)
            sed -n '3,32p' "$0"
            exit 0
            ;;
        "") shift ;;
        *)
            echo "bridge_sha256_rotate: unknown arg '${1}'" >&2
            echo "  reason: only --dry-run|--quiet|--json|--bridge NAME|--reason TEXT|--help supported" >&2
            echo "  fix: re-run with one of the above" >&2
            exit 1
            ;;
    esac
done

if [ ! -f "${BRIDGE_TSV}" ]; then
    [ "${QUIET}" = "0" ] && [ "${JSON}" = "0" ] && {
        echo "bridge_sha256_rotate: no baseline at ${BRIDGE_TSV}"
        echo "  reason: state/bridge_sha256.tsv missing"
        echo "  fix: regenerate baseline first (see header of bridge_sha256.tsv)"
    }
    if [ "${JSON}" = "1" ]; then
        printf '{"sentinel":"__BRIDGE_ROTATE__","status":"EMPTY","scanned":0,"rotated":0,"dry_run":%d}\n' "${DRY_RUN}"
    else
        echo "__BRIDGE_ROTATE__ EMPTY scanned=0 rotated=0 dry_run=${DRY_RUN}"
    fi
    exit 0
fi

sha_tool=""
if command -v shasum >/dev/null 2>&1; then
    sha_tool="shasum -a 256"
elif command -v sha256sum >/dev/null 2>&1; then
    sha_tool="sha256sum"
else
    echo "bridge_sha256_rotate: no sha tool available" >&2
    echo "  reason: neither 'shasum' nor 'sha256sum' on PATH" >&2
    echo "  fix: install coreutils" >&2
    exit 1
fi

scanned=0
rotated=0
status="PASS"

# Iterate non-comment, non-blank rows of the TSV
while IFS=$'\t' read -r name path declared_sha last_ts; do
    # Skip header / comment / blank lines
    case "${name}" in
        ''|'#'*) continue ;;
    esac
    # Optional bridge filter
    if [ -n "${ONLY_BRIDGE}" ] && [ "${name}" != "${ONLY_BRIDGE}" ]; then
        continue
    fi

    scanned=$((scanned + 1))
    abs_path="${NEXUS_ROOT}/${path}"
    if [ ! -f "${abs_path}" ]; then
        [ "${QUIET}" = "0" ] && [ "${JSON}" = "0" ] && {
            echo "  ${name}: SKIP (file missing: ${path})"
        }
        continue
    fi

    live_sha_full=$(${sha_tool} "${abs_path}" 2>/dev/null | awk '{print $1}')
    live_sha=$(printf '%s' "${live_sha_full}" | cut -c1-16)

    if [ "${live_sha}" = "${declared_sha}" ]; then
        [ "${QUIET}" = "0" ] && [ "${JSON}" = "0" ] && {
            echo "  ${name}: clean (sha=${declared_sha})"
        }
        continue
    fi

    # Drift detected
    rotated=$((rotated + 1))
    [ "${QUIET}" = "0" ] && [ "${JSON}" = "0" ] && {
        echo "  ${name}: drift detected"
        echo "    declared: ${declared_sha}"
        echo "    live:     ${live_sha}"
    }

    if [ "${DRY_RUN}" = "1" ]; then
        continue
    fi

    # Rotate TSV row in place
    TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    TMP_TSV="${BRIDGE_TSV}.tmp.$$"
    awk -F'\t' -v OFS='\t' \
        -v rname="${name}" -v rpath="${path}" -v new_sha="${live_sha}" -v ts="${TS}" '
        /^#/ || NF == 0 { print; next }
        $1 == rname && $2 == rpath { $3 = new_sha; $4 = ts; print; next }
        { print }
    ' "${BRIDGE_TSV}" > "${TMP_TSV}"
    if [ ! -s "${TMP_TSV}" ]; then
        echo "bridge_sha256_rotate: TSV rewrite produced empty output for ${name}" >&2
        echo "  reason: awk filter unexpectedly emitted no lines" >&2
        echo "  fix: inspect ${BRIDGE_TSV} and ${TMP_TSV}; do not commit" >&2
        rm -f "${TMP_TSV}"
        status="FAIL"
        continue
    fi
    mv "${TMP_TSV}" "${BRIDGE_TSV}"

    # Append hash-chained ledger entry (R5 OPT-D)
    mkdir -p "$(dirname "${BRIDGE_LOG}")"
    PREV_HASH="genesis"
    if [ -s "${BRIDGE_LOG}" ]; then
        LAST_LINE=$(tail -n 1 "${BRIDGE_LOG}" 2>/dev/null)
        if [ -n "${LAST_LINE}" ]; then
            PREV_HASH=$(printf '%s' "${LAST_LINE}" | ${sha_tool} | awk '{print $1}')
            [ -z "${PREV_HASH}" ] && PREV_HASH="genesis"
        fi
    fi

    # Reason field: included if --reason provided, else "unspecified"
    # raw 73 admissibility — chain entries should record why rotation occurred.
    REASON_FIELD="${REASON:-unspecified}"
    # Escape backslash + double-quote for JSON safety (minimal — raw 73 minimal-deps).
    REASON_ESC=$(printf '%s' "${REASON_FIELD}" | sed 's/\\/\\\\/g; s/"/\\"/g')
    printf '{"ts":"%s","bridge":"%s","old_sha":"%s","new_sha":"%s","trigger":"manual","reason":"%s","prev_hash":"%s"}\n' \
        "${TS}" "${name}" "${declared_sha}" "${live_sha}" "${REASON_ESC}" "${PREV_HASH}" >> "${BRIDGE_LOG}"
done < "${BRIDGE_TSV}"

if [ "${JSON}" = "1" ]; then
    printf '{"sentinel":"__BRIDGE_ROTATE__","status":"%s","scanned":%d,"rotated":%d,"dry_run":%d}\n' \
        "${status}" "${scanned}" "${rotated}" "${DRY_RUN}"
else
    [ "${QUIET}" = "0" ] && {
        echo "bridge_sha256_rotate: scanned=${scanned} rotated=${rotated} dry_run=${DRY_RUN}"
    }
    echo "__BRIDGE_ROTATE__ ${status} scanned=${scanned} rotated=${rotated} dry_run=${DRY_RUN}"
fi

[ "${status}" = "FAIL" ] && exit 1
exit 0
