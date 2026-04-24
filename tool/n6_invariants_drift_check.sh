#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# n6_invariants_drift_check.sh
#
# Standalone drift checker between nexus's mirror of the n6-architecture
# foundation invariants manifest and the upstream canonical source.
#
#   nexus mirror : $NEXUS_ROOT/config/invariants.json
#                  schema: n6-architecture/invariants/1 (nexus-mirror/1)
#                  shape : summary with .atoms_summary (flat dict of 10 atoms)
#                          + ._mirror_ts + ._upstream + cross_repo_references
#                          + open_followup_r33_plus
#   n6 upstream  : $N6_ROOT/config/invariants.json
#                  schema: n6-architecture/invariants/1
#                  shape : full manifest with .atoms{} per-atom detail,
#                          .declared_ts, .closing_theorem, etc.
#
# Why bash+jq (not hexa):
#   This is a pre-commit-class drift check that must run in minimal
#   environments (fresh clone, no hexa runtime installed, CI, cron). Using
#   bash+jq avoids a runtime dependency for a check whose only job is to read
#   two JSON files and compare 10 scalars.
#
# Key naming convention:
#   Upstream keys in .atoms{} use plain ASCII identifiers: n, sigma, phi, tau,
#   sopfr, mu, meta_fp, J2, M3, P2. Nexus mirror's .atoms_summary uses the
#   SAME ASCII keys (no Greek-letter normalization needed — mirror was
#   deliberately authored with stable ASCII keys). We compare on these 10
#   ASCII keys directly. No Unicode folding, no alias table.
#
# The 10 atoms compared (stable ASCII keys, in inventory order):
#   n, sigma, phi, tau, sopfr, mu, meta_fp, J2, M3, P2
#
# Semantic vs structural drift:
#   STRUCTURAL drift between the two files is BY DESIGN (summary vs full
#   manifest). This script checks SEMANTIC drift only — the 10 atom scalars
#   and the freshness of the mirror relative to upstream mtime.
#
# Flags:
#   --report   Print a table of all 10 atoms on both sides to stdout.
#   --json     Append a single-line JSON record of this run to
#              $NEXUS_ROOT/state/invariants_drift.jsonl (machine history).
#   (default)  Silent on match + fresh. Stderr on drift/stale/parse errors.
#
# Exit codes:
#   0  semantic match AND mirror is fresh (or upstream missing: SKIP)
#   1  semantic drift detected on at least one atom
#   2  stale-only: atoms match but upstream mtime > mirror _mirror_ts
#   3  parse error (malformed JSON, missing .atoms / .atoms_summary, etc.)
#
# Environment overrides:
#   NEXUS_ROOT   default: /Users/ghost/core/nexus
#   N6_ROOT      default: /Users/ghost/core/n6-architecture
#
# Fail-open upstream-missing behavior:
#   If $N6_ROOT/config/invariants.json does not exist, print
#     [SKIP] n6 upstream not present at <path>
#   to stderr and exit 0. This matches the n6-hook pattern: the nexus repo
#   must be usable on machines where n6-architecture is not cloned.
#
# ---------------------------------------------------------------------------
# INSTALL NOTES (all manual, nothing auto-installed):
#
#   1. Make executable (run once):
#        chmod +x /Users/ghost/core/nexus/tool/n6_invariants_drift_check.sh
#
#   2. Wire into pre-commit MANUALLY — NOT auto-installed. Example, append
#      this line to .git/hooks/pre-commit (create the hook if missing and
#      ensure it begins with a #!/usr/bin/env bash shebang):
#        /Users/ghost/core/nexus/tool/n6_invariants_drift_check.sh || exit $?
#
#   3. Optional weekly drift snapshot: run from cron/launchd via the existing
#      hexa_remote_sync slot, e.g.
#        /Users/ghost/core/nexus/tool/n6_invariants_drift_check.sh --json
#      which appends to state/invariants_drift.jsonl for long-horizon audit.
#
# This script does NOT install itself anywhere and does NOT chmod itself.
# ---------------------------------------------------------------------------

set -u

NEXUS_ROOT="${NEXUS_ROOT:-/Users/ghost/core/nexus}"
N6_ROOT="${N6_ROOT:-/Users/ghost/core/n6-architecture}"

MIRROR_PATH="${NEXUS_ROOT}/config/invariants.json"
UPSTREAM_PATH="${N6_ROOT}/config/invariants.json"
JSONL_OUT="${NEXUS_ROOT}/state/invariants_drift.jsonl"

# The 10 atoms to compare (stable ASCII keys, inventory order).
ATOMS=(n sigma phi tau sopfr mu meta_fp J2 M3 P2)

# --- flag parsing -----------------------------------------------------------
OPT_REPORT=0
OPT_JSON=0
for arg in "$@"; do
  case "$arg" in
    --report) OPT_REPORT=1 ;;
    --json)   OPT_JSON=1 ;;
    -h|--help)
      grep -E '^# ' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "[ERR] unknown flag: $arg" >&2
      exit 3
      ;;
  esac
done

# --- dependency check -------------------------------------------------------
if ! command -v jq >/dev/null 2>&1; then
  echo "[ERR] jq not found in PATH — required for n6 invariants drift check" >&2
  exit 3
fi

# --- fail-open if upstream missing -----------------------------------------
if [[ ! -f "$UPSTREAM_PATH" ]]; then
  echo "[SKIP] n6 upstream not present at ${UPSTREAM_PATH}" >&2
  exit 0
fi

# --- mirror must exist (nexus-local invariant) -----------------------------
if [[ ! -f "$MIRROR_PATH" ]]; then
  echo "[ERR] nexus mirror missing at ${MIRROR_PATH}" >&2
  exit 3
fi

# --- JSON sanity ------------------------------------------------------------
if ! jq -e 'type=="object"' "$UPSTREAM_PATH" >/dev/null 2>&1; then
  echo "[ERR] upstream JSON parse failure: ${UPSTREAM_PATH}" >&2
  exit 3
fi
if ! jq -e 'type=="object"' "$MIRROR_PATH" >/dev/null 2>&1; then
  echo "[ERR] mirror JSON parse failure: ${MIRROR_PATH}" >&2
  exit 3
fi
if ! jq -e '.atoms | type=="object"' "$UPSTREAM_PATH" >/dev/null 2>&1; then
  echo "[ERR] upstream missing .atoms object" >&2
  exit 3
fi
if ! jq -e '.atoms_summary | type=="object"' "$MIRROR_PATH" >/dev/null 2>&1; then
  echo "[ERR] mirror missing .atoms_summary object" >&2
  exit 3
fi

# --- atom extraction helpers ------------------------------------------------
# Upstream: .atoms[key].value   (scalar, may be number or string like "1/3")
# Mirror:   .atoms_summary[key] (scalar directly)
# jq -r prints "null" for missing — we treat literal string "null" as absent.
upstream_val() {
  jq -r --arg k "$1" '.atoms[$k].value // "null"' "$UPSTREAM_PATH"
}
mirror_val() {
  jq -r --arg k "$1" '.atoms_summary[$k] // "null"' "$MIRROR_PATH"
}

# --- comparison loop --------------------------------------------------------
DRIFT_COUNT=0
DRIFT_DETAILS=()   # lines of "atom|up|mi"
REPORT_ROWS=()

for atom in "${ATOMS[@]}"; do
  up="$(upstream_val "$atom")"
  mi="$(mirror_val "$atom")"
  REPORT_ROWS+=("${atom}|${up}|${mi}")
  if [[ "$up" != "$mi" ]]; then
    DRIFT_COUNT=$((DRIFT_COUNT + 1))
    DRIFT_DETAILS+=("${atom}|${up}|${mi}")
    echo "[DRIFT] ${atom} upstream=${up} mirror=${mi}" >&2
  fi
done

# --- stale check ------------------------------------------------------------
# Upstream mtime: filesystem stat (epoch seconds, local or UTC — stat -f %m
# returns epoch seconds which is timezone-agnostic).
# Mirror _mirror_ts: ISO-8601 Zulu timestamp — convert to epoch via date(1).
UPSTREAM_MTIME_EPOCH="$(stat -f %m "$UPSTREAM_PATH" 2>/dev/null || stat -c %Y "$UPSTREAM_PATH" 2>/dev/null)"
MIRROR_TS_ISO="$(jq -r '._mirror_ts // ""' "$MIRROR_PATH")"

MIRROR_TS_EPOCH=""
if [[ -n "$MIRROR_TS_ISO" ]]; then
  # macOS date: -j -u -f "<fmt>" "<str>" +%s
  # Linux date: -d "<str>" +%s
  # Strip trailing Z and any fractional seconds for macOS's strict parser.
  clean="${MIRROR_TS_ISO%Z}"
  clean="${clean%%.*}"
  if date -j -u -f "%Y-%m-%dT%H:%M:%S" "$clean" +%s >/dev/null 2>&1; then
    MIRROR_TS_EPOCH="$(date -j -u -f "%Y-%m-%dT%H:%M:%S" "$clean" +%s)"
  elif date -u -d "$MIRROR_TS_ISO" +%s >/dev/null 2>&1; then
    MIRROR_TS_EPOCH="$(date -u -d "$MIRROR_TS_ISO" +%s)"
  fi
fi

STALE=0
STALE_HOURS=0
if [[ -n "$UPSTREAM_MTIME_EPOCH" && -n "$MIRROR_TS_EPOCH" ]]; then
  if (( UPSTREAM_MTIME_EPOCH > MIRROR_TS_EPOCH )); then
    STALE=1
    STALE_HOURS=$(( (UPSTREAM_MTIME_EPOCH - MIRROR_TS_EPOCH) / 3600 ))
    echo "[STALE] mirror older than upstream by ${STALE_HOURS}h" >&2
  fi
fi

# --- --report output --------------------------------------------------------
if (( OPT_REPORT )); then
  printf '%-10s %-8s %-8s %s\n' "atom" "upstream" "mirror" "match"
  printf '%-10s %-8s %-8s %s\n' "----" "--------" "------" "-----"
  for row in "${REPORT_ROWS[@]}"; do
    IFS='|' read -r a u m <<<"$row"
    if [[ "$u" == "$m" ]]; then match="ok"; else match="DRIFT"; fi
    printf '%-10s %-8s %-8s %s\n' "$a" "$u" "$m" "$match"
  done
  echo ""
  echo "upstream_mtime_epoch=${UPSTREAM_MTIME_EPOCH}"
  echo "mirror_ts_iso=${MIRROR_TS_ISO}"
  echo "mirror_ts_epoch=${MIRROR_TS_EPOCH}"
  echo "drift_count=${DRIFT_COUNT}"
  echo "stale=${STALE} stale_hours=${STALE_HOURS}"
fi

# --- --json history append --------------------------------------------------
if (( OPT_JSON )); then
  mkdir -p "$(dirname "$JSONL_OUT")"
  run_ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  # Build atom pairs array with jq for correctness.
  atoms_json="$(
    jq -n \
      --slurpfile up "$UPSTREAM_PATH" \
      --slurpfile mi "$MIRROR_PATH" \
      --argjson atoms "$(printf '%s\n' "${ATOMS[@]}" | jq -R . | jq -s .)" \
      '[ $atoms[] as $k
         | { key: $k,
             upstream: ($up[0].atoms[$k].value // null),
             mirror:   ($mi[0].atoms_summary[$k] // null) }
         | .match = (.upstream == .mirror)
       ]'
  )"
  jq -c -n \
    --arg ts "$run_ts" \
    --arg upstream_path "$UPSTREAM_PATH" \
    --arg mirror_path "$MIRROR_PATH" \
    --argjson upstream_mtime "${UPSTREAM_MTIME_EPOCH:-0}" \
    --arg mirror_ts_iso "$MIRROR_TS_ISO" \
    --argjson mirror_ts_epoch "${MIRROR_TS_EPOCH:-0}" \
    --argjson drift_count "$DRIFT_COUNT" \
    --argjson stale "$STALE" \
    --argjson stale_hours "$STALE_HOURS" \
    --argjson atoms "$atoms_json" \
    '{run_ts:$ts, upstream_path:$upstream_path, mirror_path:$mirror_path,
      upstream_mtime_epoch:$upstream_mtime, mirror_ts_iso:$mirror_ts_iso,
      mirror_ts_epoch:$mirror_ts_epoch, drift_count:$drift_count,
      stale:($stale==1), stale_hours:$stale_hours, atoms:$atoms}' \
    >> "$JSONL_OUT"
fi

# --- final exit code --------------------------------------------------------
if (( DRIFT_COUNT > 0 )); then
  exit 1
fi
if (( STALE == 1 )); then
  exit 2
fi
exit 0
