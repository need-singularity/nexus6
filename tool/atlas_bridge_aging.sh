#!/usr/bin/env bash
# tool/atlas_bridge_aging.sh — Tier-2 i10 from improvement_ideas_omega_cycle (2026-04-26)
#
# 16 bridge tools 의 external API response schema drift monitor.
# 각 bridge 의 canonical URL 호출 → first 500 bytes snapshot → 다음 호출 시 diff.
# self-host 회피 (bash + curl, no hexa dep).
#
# usage:
#   tool/atlas_bridge_aging.sh                     # snapshot all + diff vs prev
#   tool/atlas_bridge_aging.sh --bridge NAME       # single bridge
#   tool/atlas_bridge_aging.sh --baseline          # establish baseline (overwrites snapshots)
#   tool/atlas_bridge_aging.sh --list              # list bridge URLs
#
# exit codes: 0=PASS no drift, 1=usage, 2=drift detected
# sentinel: __ATLAS_BRIDGE_AGING__ checked=N drift=D unchanged=U new_baseline=B
# origin: design/hexa_sim/2026-04-26_improvement_ideas_omega_cycle.json axis_i10

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$HOME/core/nexus}"
SNAPSHOT_DIR="$NEXUS_ROOT/state/bridge_snapshots"
mkdir -p "$SNAPSHOT_DIR" 2>/dev/null

# Bridge URL manifest (canonical reproducible endpoint per bridge)
# format: name|url|comment
BRIDGES=(
    "codata|https://physics.nist.gov/cuu/Constants/Table/allascii.txt|NIST CODATA 2022 constants table"
    "oeis_live|https://oeis.org/A000396/b000396.txt|OEIS perfect numbers b-file"
    "wikipedia|https://en.wikipedia.org/api/rest_v1/page/summary/Perfect_number|Perfect_number summary"
    "gw_observatory|https://gwosc.org/eventapi/jsonfull/GWTC-1-confident/|GWTC-1 confident events"
    "arxiv_realtime|http://export.arxiv.org/api/query?search_query=cat:gr-qc&max_results=1|gr-qc latest"
    "horizons|https://ssd.jpl.nasa.gov/api/horizons.api?format=text&COMMAND=499&CENTER=%27%40399%27&MAKE_EPHEM=YES&EPHEM_TYPE=OBSERVER&START_TIME=%272026-04-26%27&STOP_TIME=%272026-04-27%27&STEP_SIZE=%271d%27&QUANTITIES=%2720%27|JPL Mars ephemeris"
    "cmb_planck|https://en.wikipedia.org/wiki/Planck_(spacecraft)|Planck spacecraft wiki"
    "nanograv|https://arxiv.org/abs/2306.16213|NANOGrav 15-yr GWB paper"
    "simbad|https://simbad.cds.unistra.fr/simbad/sim-id?Ident=Sirius&output.format=ASCII|SIMBAD Sirius"
    "icecube|https://gcn.gsfc.nasa.gov/amon_icecube_gold_bronze_events.html|GCN AMON IceCube alerts"
    "nist_atomic|https://physics.nist.gov/cuu/Constants/Table/allascii.txt|NIST atomic constants (same as codata)"
    "openalex|https://api.openalex.org/works?search=perfect+number&per-page=1|OpenAlex perfect number"
    "gaia|https://gea.esac.esa.int/tap-server/tap/sync?REQUEST=doQuery&LANG=ADQL&FORMAT=csv&QUERY=SELECT+TOP+1+source_id+FROM+gaiadr3.gaia_source|Gaia DR3 single row"
    "lhc_opendata|https://opendata.cern.ch/api/records?type=Dataset&page=1&size=1|CERN OpenData"
    "pubchem|https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/water/property/MolecularFormula/JSON|PubChem water"
    "uniprot|https://rest.uniprot.org/uniprotkb/P68871.json|UniProt HBB"
)

BRIDGE_FILTER=""
BASELINE_MODE=0
LIST_MODE=0

while [ $# -gt 0 ]; do
    case "$1" in
        --bridge) BRIDGE_FILTER="$2"; shift 2 ;;
        --baseline) BASELINE_MODE=1; shift ;;
        --list) LIST_MODE=1; shift ;;
        --help|-h)
            echo "usage: $0 [--bridge NAME] [--baseline] [--list]"
            exit 0
            ;;
        *) echo "unknown: $1" >&2; exit 1 ;;
    esac
done

if [ "$LIST_MODE" = "1" ]; then
    echo "bridge URL manifest (16):"
    for entry in "${BRIDGES[@]}"; do
        IFS='|' read -r name url comment <<< "$entry"
        printf "  %-15s  %s\n" "$name" "$url"
    done
    exit 0
fi

CHECKED=0
DRIFT=0
UNCHANGED=0
NEW_BASELINE=0
SKIPPED=0

echo "bridge aging check (snapshot dir: $SNAPSHOT_DIR)"
echo "─────────────────────────────────────────────────────────────"

for entry in "${BRIDGES[@]}"; do
    IFS='|' read -r name url comment <<< "$entry"
    if [ -n "$BRIDGE_FILTER" ] && [ "$BRIDGE_FILTER" != "$name" ]; then continue; fi
    CHECKED=$((CHECKED + 1))
    snapshot_file="$SNAPSHOT_DIR/${name}.snapshot.bin"
    snapshot_meta="$SNAPSHOT_DIR/${name}.meta.tsv"

    # Fetch first 500 bytes (schema indicator) with timeout
    new_resp=$(curl -sL --max-time 15 "$url" 2>/dev/null | head -c 500 || true)
    if [ -z "$new_resp" ]; then
        printf "  %-15s  ⚠️  fetch FAIL (network/timeout/rate-limit)\n" "$name"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi
    new_sha=$(printf "%s" "$new_resp" | shasum -a 256 | cut -c1-16)

    if [ "$BASELINE_MODE" = "1" ] || [ ! -f "$snapshot_file" ]; then
        # Establish baseline
        printf "%s" "$new_resp" > "$snapshot_file"
        echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)	$new_sha	$url" > "$snapshot_meta"
        printf "  %-15s  📋 baseline ESTABLISHED  sha=%s\n" "$name" "$new_sha"
        NEW_BASELINE=$((NEW_BASELINE + 1))
        continue
    fi

    # Compare with existing
    old_sha=$(awk '{print $2}' "$snapshot_meta" 2>/dev/null | head -1)
    old_ts=$(awk '{print $1}' "$snapshot_meta" 2>/dev/null | head -1)
    if [ "$new_sha" = "$old_sha" ]; then
        printf "  %-15s  ✅ unchanged              sha=%s (since %s)\n" "$name" "$new_sha" "$old_ts"
        UNCHANGED=$((UNCHANGED + 1))
    else
        printf "  %-15s  🔄 DRIFT detected         old=%s new=%s (since %s)\n" "$name" "$old_sha" "$new_sha" "$old_ts"
        DRIFT=$((DRIFT + 1))
        # Save new as drift snapshot but don't overwrite baseline
        cp "$snapshot_file" "${snapshot_file}.prev"
        printf "%s" "$new_resp" > "${snapshot_file}.drift"
        echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)	$new_sha	$url" >> "${snapshot_meta}.drift"
    fi
done

echo "─────────────────────────────────────────────────────────────"
printf "summary: checked=%d  unchanged=%d  drift=%d  new_baseline=%d  fetch_fail=%d\n" \
       "$CHECKED" "$UNCHANGED" "$DRIFT" "$NEW_BASELINE" "$SKIPPED"

if [ "$DRIFT" -gt 0 ]; then
    echo ""
    echo "DRIFT recovery options:"
    echo "  1. inspect *.drift files in $SNAPSHOT_DIR"
    echo "  2. accept new baseline: rm $SNAPSHOT_DIR/*.snapshot.bin && $0 --baseline"
    echo "  3. or per-bridge accept: cp $SNAPSHOT_DIR/<name>.snapshot.bin.drift $SNAPSHOT_DIR/<name>.snapshot.bin"
fi

echo "__ATLAS_BRIDGE_AGING__ checked=$CHECKED drift=$DRIFT unchanged=$UNCHANGED new_baseline=$NEW_BASELINE fetch_fail=$SKIPPED"
[ "$DRIFT" -gt 0 ] && exit 2 || exit 0
