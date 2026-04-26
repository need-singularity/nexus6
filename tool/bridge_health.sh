#!/usr/bin/env bash
# tool/bridge_health.sh — bridge registry health check (cron-friendly)
#
# Iterate the 16 registered hexa-sim bridges (mirrored from cli/run.hexa
# _hexa_sim_bridge_dispatch). For each: gtimeout 30 hexa run <bridge> --selftest.
# Classify PASS / FAIL / OFFLINE-FALLBACK / TAMPERED based on sentinel + exit code.
# Append timeline JSONL line to state/atlas_health_timeline.jsonl.
#
# usage:
#   tool/bridge_health.sh                       # human-readable + sentinel + timeline append
#   tool/bridge_health.sh --quiet               # only sentinel line
#   tool/bridge_health.sh --json                # JSONL summary on stdout (no timeline)
#   tool/bridge_health.sh --strict              # also verify each bridge file SHA256 vs pinned baseline
#   tool/bridge_health.sh --fingerprint-check   # after each PASS, schema-fingerprint via bridge_helper
#   tool/bridge_health.sh -F                    # short form of --fingerprint-check
#   tool/bridge_health.sh --anomaly-check       # after sweep, hexa run bridge_anomaly.hexa (CLI-only)
#   tool/bridge_health.sh -A                    # short form of --anomaly-check
#   tool/bridge_health.sh --no-history          # skip per-bridge TSV append (testing)
#
# Exit:
#   0 if all PASS
#   76 if any FAIL/TAMPERED (raw 23 schema-guard analog)
#   1 on usage
#
# Sentinel (raw 80):
#   __BRIDGE_HEALTH__ <PASS|WARN|FAIL> total=N pass=P fail=F tampered=K duration_ms=T
#
# Compliance: raw 66 (reason+fix trailers) + raw 71 (report-only) + raw 80
#             + raw 77 (audit-append-only over baseline TSV)
# R1 (bridge_sha256 per-bridge): each bridge file is hashed at runtime and compared
#   against state/bridge_sha256.tsv pinned baseline — mismatch → STATUS=TAMPERED.
#   Defeats silent .hexa rewrite (e.g. selftest sentinel injected into mutated body).
#   Bridges face higher attack risk than falsifiers because external API selftest
#   paths could be subverted. Propagated from falsifier_health.sh R1 (Ω-cycle).
# ω-bridge-7 (2026-04-26): --fingerprint-check opt-in flag.
#   After each bridge PASSES selftest, optionally invoke
#     bash tool/bridge_helper.sh fingerprint-check <bridge> <url>
#   to detect upstream JSON schema drift (top-level key set change). Emits a
#   per-sweep tally line:
#     __BRIDGE_FINGERPRINT__ checked=N matched=M drift=D non_json=NJ baseline_recorded=BR
#   Default OFF (backward compat). Drift events are also printed individually.
#   URL lookup table is hardcoded below (BRIDGE_FP_URLS) — one canonical fetch
#   URL per registered bridge. Non-JSON bridges (text/HTML/CSV) yield NON_JSON
#   and are tallied in non_json (expected for ~half of the registry).
#   See state/omega_bridge_7_health_integration.json.
# Origin: design/hexa_sim/2026-04-26_bridge_health_check.md (productionised runner)
#         design/hexa_sim/2026-04-26_bridge_health_R1_propagation_omega_cycle.json

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$HOME/core/nexus}"
# HEXA_BIN container-context resolution (ω-bridge-8 fix):
#   On host (Mac): default is the wrapper at $HOME/core/hexa-lang/hexa which
#     routes through the resolver/build/hexa.real (Mach-O).
#   Inside Linux container (hexa-runner): the wrapper would exec the Mach-O
#     hexa.real → "Exec format error". The container ships a native ELF
#     dispatcher at /usr/local/bin/hexa — prefer it when container markers
#     are present (/.dockerenv exists, or HEXA_IN_CONTAINER=1, or the host
#     wrapper path is absent while the container path exists).
#   Override always wins via explicit HEXA_BIN env var.
_default_hexa_bin="$HOME/core/hexa-lang/hexa"
if [ -z "${HEXA_BIN:-}" ]; then
    if [ -f /.dockerenv ] || [ "${HEXA_IN_CONTAINER:-0}" = "1" ]; then
        [ -x /usr/local/bin/hexa ] && _default_hexa_bin=/usr/local/bin/hexa
    elif [ ! -x "$_default_hexa_bin" ] && [ -x /usr/local/bin/hexa ]; then
        _default_hexa_bin=/usr/local/bin/hexa
    fi
fi
HEXA_BIN="${HEXA_BIN:-$_default_hexa_bin}"
TIMELINE="${ATLAS_HEALTH_TIMELINE:-$NEXUS_ROOT/state/atlas_health_timeline.jsonl}"
BRIDGE_SHA_TSV="${BRIDGE_SHA_TSV:-$NEXUS_ROOT/state/bridge_sha256.tsv}"
BRIDGE_HISTORY_TSV="${BRIDGE_HISTORY_TSV:-$NEXUS_ROOT/state/bridge_health_history.tsv}"
TIMEOUT_BIN="${TIMEOUT_BIN:-gtimeout}"
TIMEOUT_SECS="${BRIDGE_TIMEOUT:-30}"

QUIET=0
JSON=0
STRICT=0
FP_CHECK=0
ANOMALY_CHECK=0
NO_HISTORY=0

while [ $# -gt 0 ]; do
    case "$1" in
        --quiet)  QUIET=1; shift ;;
        --json)   JSON=1; shift ;;
        --strict) STRICT=1; shift ;;
        --fingerprint-check|-F) FP_CHECK=1; shift ;;
        --anomaly-check|-A) ANOMALY_CHECK=1; shift ;;
        --no-history)           NO_HISTORY=1; shift ;;
        --help|-h) sed -n '3,47p' "$0"; exit 0 ;;
        *)
            echo "usage error: unknown flag: $1" >&2
            echo "  reason: unrecognised CLI argument" >&2
            echo "  fix:    use --quiet | --json | --strict | --fingerprint-check | --anomaly-check | --no-history | --help" >&2
            exit 1
            ;;
    esac
done

BRIDGE_HELPER="${BRIDGE_HELPER:-$NEXUS_ROOT/tool/bridge_helper.sh}"

# ω-bridge-7 URL table — one canonical fetch URL per registered bridge.
# Used only when --fingerprint-check is set. Bridges whose canonical URLs are
# not JSON (text / HTML / CSV / ASCII / XML-Atom) will return NON_JSON_BODY
# from bridge_helper fingerprint-check and be tallied separately. That is
# expected: drift detection is a JSON-only signal by design (see ω-bridge-6).
BRIDGE_FP_URLS="
codata|https://physics.nist.gov/cuu/Constants/Table/allascii.txt
oeis|https://oeis.org/A000396/b000396.txt
gw|https://gwosc.org/eventapi/jsonfull/allevents/
horizons|https://ssd.jpl.nasa.gov/api/horizons.api?format=text&COMMAND=499&CENTER=%27%40399%27
arxiv|https://export.arxiv.org/api/query?search_query=cat:gr-qc&start=0&max_results=5&sortBy=submittedDate&sortOrder=descending
cmb|https://en.wikipedia.org/wiki/Planck_(spacecraft)
nanograv|https://arxiv.org/abs/2306.16213
simbad|https://simbad.cds.unistra.fr/simbad/sim-id?Ident=Sirius&output.format=ASCII
icecube|https://gcn.gsfc.nasa.gov/amon_icecube_gold_bronze_events.html
nist_atomic|https://physics.nist.gov/cuu/Constants/Table/allascii.txt
wikipedia|https://en.wikipedia.org/api/rest_v1/page/summary/Perfect_number
openalex|https://api.openalex.org/works?search=perfect+number&per-page=3&mailto=noreply@local
gaia|https://gea.esac.esa.int/tap-server/tap/sync?REQUEST=doQuery&LANG=ADQL&FORMAT=csv&QUERY=SELECT+TOP+1+source_id+FROM+gaiadr3.gaia_source
lhc|https://opendata.cern.ch/api/records/?type=Dataset&page=1&size=2
pubchem|https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/water/property/MolecularFormula,MolecularWeight,CanonicalSMILES,InChI/JSON
uniprot|https://rest.uniprot.org/uniprotkb/P68871.json
"

fp_url_for() {
    local _name="$1"
    printf '%s\n' "$BRIDGE_FP_URLS" | awk -F'|' -v n="$_name" '$1==n {print $2; exit}'
}

# ω-bridge-15: append a per-bridge-per-sweep row to BRIDGE_HISTORY_TSV.
# Schema:  ts<TAB>bridge<TAB>status<TAB>duration_ms<TAB>ec  (raw 77 append-only).
# Honoured by tool/bridge_anomaly.hexa as the canonical history input.
# No-op when --no-history is set or when BRIDGE_HISTORY_TSV is unwritable.
append_history_row() {
    local _ts="$1" _name="$2" _status="$3" _dur_ms="$4" _ec="$5"
    [ "$NO_HISTORY" = "1" ] && return 0
    [ -z "$_ts" ] || [ -z "$_name" ] && return 0
    # Single atomic append. Tab-separated. printf is shell-builtin so no exec fan-out.
    printf '%s\t%s\t%s\t%s\t%s\n' "$_ts" "$_name" "$_status" "$_dur_ms" "$_ec" \
        >> "$BRIDGE_HISTORY_TSV" 2>/dev/null || return 0
}

# Helper: SHA256 of a file (first 16 hex chars). Tries shasum (BSD) then sha256sum (GNU).
sha256_file_16() {
    local _h
    _h=$(shasum -a 256 "$1" 2>/dev/null | awk '{print $1}')
    [ -z "$_h" ] && _h=$(sha256sum "$1" 2>/dev/null | awk '{print $1}')
    printf '%s' "${_h:0:16}"
}

# Lookup declared sha256_16 for a given bridge name from baseline TSV.
# Returns empty string if name absent or TSV missing.
declared_sha_for() {
    local _name="$1"
    [ -f "$BRIDGE_SHA_TSV" ] || { printf ''; return; }
    awk -v n="$_name" -F '\t' '!/^#/ && $1==n {print $3; exit}' "$BRIDGE_SHA_TSV"
}

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
TOTAL=0; PASS=0; FAIL=0; OFFLINE=0; TAMPERED=0
# ω-bridge-7 fingerprint tally
FP_CHECKED=0; FP_MATCHED=0; FP_DRIFT=0; FP_NON_JSON=0; FP_BASELINE=0; FP_FETCH_FAIL=0
FP_DRIFT_LINES=""

if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
    echo "═══ BRIDGE HEALTH — $NOW (UTC)"
    echo "hexa: $HEXA_BIN  timeout=${TIMEOUT_SECS}s  baseline=$BRIDGE_SHA_TSV"
fi

# R1 strict baseline check — warn (not fail) if TSV missing (raw 71 report-only)
if [ "$STRICT" = "1" ] && [ ! -f "$BRIDGE_SHA_TSV" ]; then
    echo "warning: --strict requested but bridge_sha256.tsv not found at $BRIDGE_SHA_TSV" >&2
    echo "  reason: bridge SHA256 baseline file missing" >&2
    echo "  fix:    regenerate via tool/bridge_sha256_pin.py or restore from git history" >&2
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
            printf '  %-12s  FAIL       ec=N/A  reason=script_missing  fix=restore_from_git\n' "$NAME"
        fi
        append_history_row "$NOW" "$NAME" "FAIL" "0" "NA"
        continue
    fi
    # R1 bridge_sha256 verification — recompute hash of bridge file; mismatch → TAMPERED
    # Defeats silent .hexa rewrite (sentinel-injection into mutated body).
    # Skipped only if no baseline entry exists for this bridge (raw 71 report-only).
    SHA_DECL=$(declared_sha_for "$NAME")
    if [ -n "$SHA_DECL" ]; then
        SHA_LIVE=$(sha256_file_16 "$SCRIPT")
        if [ "$SHA_LIVE" != "$SHA_DECL" ]; then
            STATUS="TAMPERED"; TAMPERED=$((TAMPERED+1)); FAIL=$((FAIL+1))
            if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
                printf '  %-12s  %-9s  ec=N/A  reason=bridge_sha256_mismatch  fix=audit_git_log_or_refresh_baseline  declared=%s  live=%s\n' \
                    "$NAME" "$STATUS" "$SHA_DECL" "$SHA_LIVE"
            fi
            append_history_row "$NOW" "$NAME" "TAMPERED" "0" "NA"
            continue
        fi
    fi
    T0=$(date +%s)
    if [ -n "$TIMEOUT_BIN" ]; then
        OUT=$(HEXA_RESOLVER_NO_REROUTE=1 "$TIMEOUT_BIN" "$TIMEOUT_SECS" "$HEXA_BIN" run "$SCRIPT" --selftest 2>&1); EC=$?
    else
        OUT=$(HEXA_RESOLVER_NO_REROUTE=1 "$HEXA_BIN" run "$SCRIPT" --selftest 2>&1); EC=$?
    fi
    T1=$(date +%s)
    DUR=$((T1 - T0))
    # Status disambiguation (Ω-cycle 2026-04-26 health_check_status_disambiguation):
    #   ec=0 + sentinel match           → PASS
    #   ec=0 + sentinel match + fb str  → PASS + OFFLINE-FALLBACK counter
    #   ec=0 + no sentinel              → FAIL (selftest silently dropped sentinel)
    #   ec≠0 + fallback hint in OUT     → OFFLINE-FALLBACK (bridge degraded but ran)
    #   ec≠0 + no fallback              → FAIL (true error: hexa runtime / network / parse)
    # Bridges have heterogeneous sentinel formats — both __NAME_BRIDGE__ PASS and
    # [name_bridge selftest] OK accepted (raw 73 admissibility).
    STATUS="FAIL"
    if [ "$EC" = "0" ] && printf '%s' "$OUT" | grep -Eq '(__[A-Z_]+(_BRIDGE)?__[[:space:]]+PASS\b|\[[a-z0-9_]+_bridge[^]]*selftest\][[:space:]]+OK\b)'; then
        STATUS="PASS"; PASS=$((PASS+1))
        # OFFLINE-FALLBACK detection: bridge passed but used hardcoded fallback.
        if printf '%s' "$OUT" | grep -Eqi 'fallback|offline|no.?fetch'; then
            OFFLINE=$((OFFLINE+1))
        fi
    elif [ "$EC" != "0" ] && printf '%s' "$OUT" | grep -Eqi 'fallback|offline|no.?fetch'; then
        # ec≠0 but bridge engaged offline fallback path — degraded, not failed
        STATUS="OFFLINE"; OFFLINE=$((OFFLINE+1)); FAIL=$((FAIL+1))
    else
        FAIL=$((FAIL+1))
    fi
    if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
        if [ "$STATUS" = "FAIL" ]; then
            printf '  %-12s  %-9s  ec=%-3s  %3ss  reason=selftest_failed  fix=run_verbose_then_check_design\n' "$NAME" "$STATUS" "$EC" "$DUR"
        else
            printf '  %-12s  %-9s  ec=%-3s  %3ss\n' "$NAME" "$STATUS" "$EC" "$DUR"
        fi
    fi
    # ω-bridge-15: per-bridge history row (raw 77 append-only). DUR is integer seconds
    # from date +%s; multiply to get ms-grain matching the schema. Coarse but
    # consistent with existing wall timing (see L210).
    append_history_row "$NOW" "$NAME" "$STATUS" "$((DUR * 1000))" "$EC"

    # ω-bridge-7 fingerprint-check (opt-in, only after PASS, only if URL registered)
    if [ "$FP_CHECK" = "1" ] && [ "$STATUS" = "PASS" ]; then
        FP_URL=$(fp_url_for "$NAME")
        if [ -z "$FP_URL" ]; then
            if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
                printf '    └─ fp:        SKIP       reason=no_url_registered\n'
            fi
        elif [ ! -x "$BRIDGE_HELPER" ] && [ ! -f "$BRIDGE_HELPER" ]; then
            if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
                printf '    └─ fp:        SKIP       reason=helper_missing path=%s\n' "$BRIDGE_HELPER"
            fi
        else
            # BRIDGE_FP_TTL lets ops force long cache (e.g. 86400 for cached-only
            # validation runs); default 3600 matches bridge_helper default.
            FP_TTL="${BRIDGE_FP_TTL:-3600}"
            FP_OUT=$(bash "$BRIDGE_HELPER" fingerprint-check "$NAME" "$FP_URL" "$FP_TTL" 1 2>/dev/null)
            FP_EC=$?
            FP_CHECKED=$((FP_CHECKED+1))
            case "$FP_OUT" in
                BASELINE_RECORDED*)
                    FP_BASELINE=$((FP_BASELINE+1))
                    FP_TAG="BASELINE"
                    ;;
                MATCH*)
                    FP_MATCHED=$((FP_MATCHED+1))
                    FP_TAG="MATCH"
                    ;;
                DRIFT_DETECTED*)
                    FP_DRIFT=$((FP_DRIFT+1))
                    FP_TAG="DRIFT"
                    FP_DRIFT_LINES="${FP_DRIFT_LINES}__BRIDGE_FINGERPRINT_DRIFT__ bridge=${NAME} ${FP_OUT#DRIFT_DETECTED }
"
                    ;;
                NON_JSON_BODY*)
                    FP_NON_JSON=$((FP_NON_JSON+1))
                    FP_TAG="NON_JSON"
                    ;;
                FETCH_FAIL*)
                    FP_FETCH_FAIL=$((FP_FETCH_FAIL+1))
                    FP_TAG="FETCH_FAIL"
                    ;;
                *)
                    FP_TAG="UNKNOWN(ec=$FP_EC)"
                    ;;
            esac
            if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
                printf '    └─ fp:        %-10s %s\n' "$FP_TAG" "$FP_OUT"
            fi
        fi
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

JSONL_LINE=$(printf '{"ts":"%s","scope":"bridge_registry","total":%d,"pass":%d,"fail":%d,"offline_fallback":%d,"tampered":%d,"duration_ms":%d,"checker":"bridge_health.sh"}' \
    "$NOW" "$TOTAL" "$PASS" "$FAIL" "$OFFLINE" "$TAMPERED" "$DURATION_MS")

if [ "$JSON" = "1" ]; then
    printf '%s\n' "$JSONL_LINE"
else
    printf '%s\n' "$JSONL_LINE" >> "$TIMELINE"
fi

if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
    echo "─── summary"
    printf '  total=%d  pass=%d  fail=%d  offline_fallback=%d  tampered=%d  wall=%dms\n' \
        "$TOTAL" "$PASS" "$FAIL" "$OFFLINE" "$TAMPERED" "$DURATION_MS"
    if [ "$FP_CHECK" = "1" ]; then
        printf '  fp:  checked=%d matched=%d drift=%d non_json=%d baseline_recorded=%d fetch_fail=%d\n' \
            "$FP_CHECKED" "$FP_MATCHED" "$FP_DRIFT" "$FP_NON_JSON" "$FP_BASELINE" "$FP_FETCH_FAIL"
    fi
    if [ "$EXIT_CODE" = "76" ]; then
        echo "  reason: $FAIL bridge(s) failed selftest ($TAMPERED tampered)"
        echo "  fix:    bash $NEXUS_ROOT/tool/bridge_health.sh (verbose); consult design/hexa_sim/2026-04-26_bridge_health_check.md"
        if [ "$TAMPERED" -gt 0 ]; then
            echo "  fix:    audit git log of mutated bridge(s); if intended, refresh $BRIDGE_SHA_TSV"
        fi
    fi
fi

# ω-bridge-7: per-drift sentinel lines (one per drift event, for log-grepping)
if [ "$FP_CHECK" = "1" ] && [ -n "$FP_DRIFT_LINES" ]; then
    printf '%s' "$FP_DRIFT_LINES"
fi

echo "__BRIDGE_HEALTH__ $VERDICT total=$TOTAL pass=$PASS fail=$FAIL tampered=$TAMPERED duration_ms=$DURATION_MS"
if [ "$FP_CHECK" = "1" ]; then
    echo "__BRIDGE_FINGERPRINT__ checked=$FP_CHECKED matched=$FP_MATCHED drift=$FP_DRIFT non_json=$FP_NON_JSON baseline_recorded=$FP_BASELINE"
fi

# ω-bridge-15: opt-in anomaly check (CLI-only inter-call into hexa runtime).
# Reads BRIDGE_HISTORY_TSV (now appended above) and emits __BRIDGE_ANOMALY__.
# Failure here is non-fatal (raw 71 report-only) — main exit code is preserved.
# ω-bridge-16: capture analyzer stdout, re-emit, and append a parsed sibling
# JSONL line to $TIMELINE (scope=bridge_anomaly) so time-series tooling can
# join health + anomaly without re-parsing per-bridge sentinels. Suppressed
# under --json (consistent with the bridge_registry JSONL gate at L341-343).
if [ "$ANOMALY_CHECK" = "1" ]; then
    if [ -x "$HEXA_BIN" ] || [ -f "$HEXA_BIN" ]; then
        ANOMALY_OUT=$(HEXA_ARGV="--quiet --history $BRIDGE_HISTORY_TSV" \
            HEXA_RESOLVER_NO_REROUTE=1 \
            "$HEXA_BIN" run "$NEXUS_ROOT/tool/bridge_anomaly.hexa" 2>/dev/null) || ANOMALY_OUT=""
        if [ -n "$ANOMALY_OUT" ]; then
            printf '%s\n' "$ANOMALY_OUT"
            ANOMALY_LINE=$(printf '%s\n' "$ANOMALY_OUT" | grep '^__BRIDGE_ANOMALY__' | head -1)
            if [ -n "$ANOMALY_LINE" ] && [ "$JSON" = "0" ]; then
                # Sentinel format (raw 80, fixed positional after verdict):
                #   __BRIDGE_ANOMALY__ <verdict> bridges=B samples=N flagged=F window=W mult=M [reason=... path=...]
                read -r A_VERDICT A_BRIDGES A_SAMPLES A_FLAGGED A_WINDOW A_MULT <<EOF_PARSE
$(printf '%s' "$ANOMALY_LINE" | awk '{
    v=$2
    sub(/^[^=]*=/,"",$3); b=$3
    sub(/^[^=]*=/,"",$4); s=$4
    sub(/^[^=]*=/,"",$5); f=$5
    sub(/^[^=]*=/,"",$6); w=$6
    sub(/^[^=]*=/,"",$7); m=$7
    print v, b, s, f, w, m
}')
EOF_PARSE
                printf '{"ts":"%s","scope":"bridge_anomaly","verdict":"%s","bridges":%s,"samples":%s,"flagged":%s,"window":%s,"multiplier":%s,"checker":"bridge_anomaly.hexa"}\n' \
                    "$NOW" "${A_VERDICT:-UNKNOWN}" "${A_BRIDGES:-0}" "${A_SAMPLES:-0}" "${A_FLAGGED:-0}" "${A_WINDOW:-0}" "${A_MULT:-0}" \
                    >> "$TIMELINE"
            fi
        fi
    else
        echo "__BRIDGE_ANOMALY__ SKIP reason=hexa_bin_missing path=$HEXA_BIN" >&2
    fi
fi

exit $EXIT_CODE
