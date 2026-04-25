#!/usr/bin/env bash
# tool/bridge_health.sh — bridge registry health check (cron-friendly)
#
# Iterate the 16 registered hexa-sim bridges (mirrored from cli/run.hexa
# _hexa_sim_bridge_dispatch). For each: gtimeout 30 hexa run <bridge> --selftest.
# Classify PASS / FAIL / OFFLINE-FALLBACK based on sentinel + exit code.
# Append timeline JSONL line to state/atlas_health_timeline.jsonl.
#
# usage:
#   tool/bridge_health.sh           # human-readable + sentinel + timeline append
#   tool/bridge_health.sh --quiet   # only sentinel line
#   tool/bridge_health.sh --json    # JSONL summary on stdout (no timeline)
#
# Exit:
#   0 if all PASS
#   76 if any FAIL (raw 23 schema-guard analog)
#   1 on usage
#
# Sentinel (raw 80):
#   __BRIDGE_HEALTH__ <PASS|WARN|FAIL> total=N pass=P fail=F duration_ms=T
#
# Compliance: raw 66 (reason+fix trailers) + raw 71 (report-only) + raw 80
# Origin: design/hexa_sim/2026-04-26_bridge_health_check.md (productionised runner)

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$HOME/core/nexus}"
HEXA_BIN="${HEXA_BIN:-$HOME/core/hexa-lang/hexa}"
TIMELINE="${ATLAS_HEALTH_TIMELINE:-$NEXUS_ROOT/state/atlas_health_timeline.jsonl}"
TIMEOUT_BIN="${TIMEOUT_BIN:-gtimeout}"
TIMEOUT_SECS="${BRIDGE_TIMEOUT:-30}"

QUIET=0
JSON=0

while [ $# -gt 0 ]; do
    case "$1" in
        --quiet) QUIET=1; shift ;;
        --json)  JSON=1; shift ;;
        --help|-h) sed -n '3,28p' "$0"; exit 0 ;;
        *)
            echo "usage error: unknown flag: $1" >&2
            echo "  reason: unrecognised CLI argument" >&2
            echo "  fix:    use --quiet | --json | --help" >&2
            exit 1
            ;;
    esac
done

# 16 bridges in registry order (mirrors _hexa_sim_bridge_dispatch in cli/run.hexa).
# Each entry: "<short-name>:<script-relative-to-NEXUS_ROOT>"
BRIDGES="
codata:tool/codata_bridge.hexa
oeis:tool/oeis_live_bridge.hexa
gw:tool/gw_observatory_bridge.hexa
horizons:tool/horizons_bridge.hexa
arxiv:tool/arxiv_realtime_bridge.hexa
cmb:tool/cmb_planck_bridge.hexa
nanograv:tool/nanograv_pulsar_bridge.hexa
simbad:tool/simbad_bridge.hexa
icecube:tool/icecube_neutrino_bridge.hexa
nist_atomic:tool/nist_atomic_bridge.hexa
wikipedia:tool/wikipedia_summary_bridge.hexa
openalex:tool/openalex_bridge.hexa
gaia:tool/gaia_bridge.hexa
lhc:tool/lhc_opendata_bridge.hexa
pubchem:tool/pubchem_bridge.hexa
uniprot:tool/uniprot_bridge.hexa
"

NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
WALL_START=$(date +%s)
TOTAL=0; PASS=0; FAIL=0; OFFLINE=0

if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
    echo "═══ BRIDGE HEALTH — $NOW (UTC)"
    echo "hexa: $HEXA_BIN  timeout=${TIMEOUT_SECS}s"
fi

# Resolve timeout binary (gtimeout on mac, timeout on linux).
command -v "$TIMEOUT_BIN" >/dev/null 2>&1 || TIMEOUT_BIN=$(command -v timeout || true)

for entry in $BRIDGES; do
    NAME="${entry%%:*}"
    REL="${entry#*:}"
    SCRIPT="$NEXUS_ROOT/$REL"
    TOTAL=$((TOTAL+1))
    if [ ! -f "$SCRIPT" ]; then
        FAIL=$((FAIL+1))
        if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
            printf '  %-12s  FAIL   ec=N/A  reason=script_missing\n' "$NAME"
        fi
        continue
    fi
    T0=$(date +%s)
    if [ -n "$TIMEOUT_BIN" ]; then
        OUT=$(HEXA_RESOLVER_NO_REROUTE=1 "$TIMEOUT_BIN" "$TIMEOUT_SECS" "$HEXA_BIN" run "$SCRIPT" --selftest 2>&1); EC=$?
    else
        OUT=$(HEXA_RESOLVER_NO_REROUTE=1 "$HEXA_BIN" run "$SCRIPT" --selftest 2>&1); EC=$?
    fi
    T1=$(date +%s)
    DUR=$((T1 - T0))
    STATUS="FAIL"
    # Bridge sentinel patterns (heterogeneous across the 16 bridges):
    #   1. "__<NAME>_BRIDGE__ PASS|FAIL ..." (oeis, wikipedia, simbad, openalex, gw, arxiv, uniprot)
    #   2. "[<name>_bridge selftest] OK ..." (codata, horizons, cmb, nanograv, icecube, nist_atomic, gaia, lhc, pubchem)
    if [ "$EC" = "0" ] && printf '%s' "$OUT" | grep -Eq '(__[A-Z_]+(_BRIDGE)?__[[:space:]]+PASS\b|\[[a-z0-9_]+_bridge[^]]*selftest\][[:space:]]+OK\b)'; then
        STATUS="PASS"; PASS=$((PASS+1))
        # OFFLINE-FALLBACK detection: bridge passed but used hardcoded fallback.
        if printf '%s' "$OUT" | grep -Eqi 'fallback|offline|no.?fetch'; then
            OFFLINE=$((OFFLINE+1))
        fi
    else
        FAIL=$((FAIL+1))
    fi
    if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
        printf '  %-12s  %-4s   ec=%-3s  %3ss\n' "$NAME" "$STATUS" "$EC" "$DUR"
    fi
done

WALL_END=$(date +%s)
DURATION_MS=$(( (WALL_END - WALL_START) * 1000 ))

VERDICT="PASS"
EXIT_CODE=0
if [ "$FAIL" -gt 0 ]; then
    VERDICT="FAIL"
    EXIT_CODE=76
fi

JSONL_LINE=$(printf '{"ts":"%s","scope":"bridge_registry","total":%d,"pass":%d,"fail":%d,"offline_fallback":%d,"duration_ms":%d,"checker":"bridge_health.sh"}' \
    "$NOW" "$TOTAL" "$PASS" "$FAIL" "$OFFLINE" "$DURATION_MS")

if [ "$JSON" = "1" ]; then
    printf '%s\n' "$JSONL_LINE"
else
    printf '%s\n' "$JSONL_LINE" >> "$TIMELINE"
fi

if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
    echo "─── summary"
    printf '  total=%d  pass=%d  fail=%d  offline_fallback=%d  wall=%dms\n' "$TOTAL" "$PASS" "$FAIL" "$OFFLINE" "$DURATION_MS"
    if [ "$EXIT_CODE" = "76" ]; then
        echo "  reason: $FAIL bridge(s) failed selftest"
        echo "  fix:    bash $NEXUS_ROOT/tool/bridge_health.sh (verbose); consult design/hexa_sim/2026-04-26_bridge_health_check.md"
    fi
fi

echo "__BRIDGE_HEALTH__ $VERDICT total=$TOTAL pass=$PASS fail=$FAIL duration_ms=$DURATION_MS"
exit $EXIT_CODE
