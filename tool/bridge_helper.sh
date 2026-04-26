#!/usr/bin/env bash
# tool/bridge_helper.sh — shared rate-limit + retry + filesystem-cache shim for nexus bridges.
#
# ω-bridge-2 cycle (2026-04-26): addresses /Users/ghost/core/anima/state/omega_bridge_baseline.json
# findings F4 (no rate-limit handling), F5 (no response cache), F6 (no retry logic).
#
# Drop-in protocol (called from a hexa bridge via exec(...)):
#   bash tool/bridge_helper.sh fetch <bridge_name> <url> [<ttl_sec>] [<min_interval_sec>]
#     - bridge_name      : short id (e.g. "codata", "pubchem"); used for cache key + lockfile
#     - url              : full URL to fetch
#     - ttl_sec          : cache TTL in seconds (default 3600 = 1 hour)
#     - min_interval_sec : polite minimum spacing between LIVE calls per-bridge (default 1)
#
#   On stdout: the response body, identical to `curl -s --max-time N <url>`.
#   On stderr: nothing on success; one diagnostic line on persistent failure.
#   Exit:      0 on success (cache hit OR live fetch ok), 1 on persistent failure.
#
# Behaviour:
#   1. Cache lookup: if $CACHE_DIR/<bridge>_<sha1(url)>.body exists AND age < ttl → emit + exit 0.
#   2. Lock-file rate-limit: if last-live-call timestamp < min_interval_sec ago → sleep delta.
#   3. Live fetch via curl with -w '\n%{http_code}' so we capture body + status:
#        - 2xx : write body to cache, emit body, exit 0.
#        - 429 / 5xx : retry with exponential backoff (1s, 2s, 4s; up to 3 attempts).
#        - 4xx (other than 429): no retry (deterministic), emit body, exit 1.
#        - empty body / curl error: retry as transient.
#   4. After all retries exhausted: emit empty body + diag on stderr + exit 1.
#      (Caller can keep its own fallback path — bridges already have hardcoded fallbacks.)
#
# Env overrides (test affordances):
#   BRIDGE_HELPER_CACHE_DIR        : cache root (default $NEXUS_ROOT/state/bridge_cache)
#   BRIDGE_HELPER_DISABLE          : if "1", bypass cache + retry + rate-limit (raw curl)
#   BRIDGE_HELPER_FORCE_FAIL       : if "1", skip live curl entirely (synthetic 429-style)
#   BRIDGE_HELPER_MAX_RETRY        : override retry count (default 3)
#   BRIDGE_HELPER_MAX_TIME         : per-request curl --max-time (default 12)
#   BRIDGE_HELPER_VERBOSE          : if "1", emit diagnostic trace to stderr
#   BRIDGE_HELPER_UA               : if set, passed to curl as `-A "$BRIDGE_HELPER_UA"` (polite User-Agent)
#   BRIDGE_HELPER_HEADERS          : if set, multi-line newline-separated; each non-empty line passed as `-H "$line"`
#                                    (e.g. "accept: application/json", "Authorization: Bearer ...")
#   BRIDGE_HELPER_TIMEOUT          : if set, passed as `--max-time "$BRIDGE_HELPER_TIMEOUT"` (overrides MAX_TIME for caller-scoped tightening)
#   BRIDGE_HELPER_CACHE_GC_AGE_S   : age threshold in seconds for cache-gc deletion (default 7200 = 2h)
#   BRIDGE_HELPER_CACHE_MAX_BYTES  : max total cache dir size in bytes (default 50000000 = 50 MB)
#   BRIDGE_HELPER_GC_PROBABILITY   : probabilistic gc trigger frequency on fetch (1 in N; default 100)
#                                    set to 0 to disable; set to 1 to gc every fetch (test mode)
#   BRIDGE_HELPER_AUTH             : if set, full Authorization header value (e.g. "Bearer xyz").
#                                    Passed to curl via --header @<tempfile> (no argv leak).
#                                    Cache key includes sha1(auth)[0:8] so distinct tokens get
#                                    distinct cache entries. Tempfile is mode 0600 and removed
#                                    on EXIT trap. Verbose logs redact this value.
#
# ω-bridge-4 (2026-04-26): UA / extra-headers / per-call-timeout pass-through restored
#   for the 8 bridges that lost them in the ω-bridge-3 sweep (cmb/nanograv/icecube/arxiv/
#   openalex/lhc previously sent polite-UA; wikipedia/uniprot previously sent Accept).
#   Default behaviour unchanged when env vars unset (backward-compat with the 16 already
#   migrated bridges). See state/omega_bridge_4_header_passthrough.json.
#
# ω-bridge-5 (2026-04-26): cache-gc subcommand + probabilistic GC + size-limit eviction.
#   Addresses monotonic cache growth: stale entries (older than TTL) were bypassed on read
#   but never deleted. cache-gc deletes .body/.meta files older than CACHE_GC_AGE_S, then
#   enforces CACHE_MAX_BYTES by evicting oldest-first. fetch invokes cache-gc inline with
#   1/GC_PROBABILITY probability (default 1/100 → ~1% overhead). See
#   state/omega_bridge_5_cache_gc.json.
#
# ω-bridge-12 (2026-04-26): per-bridge config table — replaces scattered per-bridge
#   env exports with a single tracked TSV at state/bridge_config.tsv.
#   Columns: bridge<TAB>ttl_s<TAB>min_interval_s<TAB>ua<TAB>accept   ('-' = unset)
#   New env: BRIDGE_HELPER_CONFIG_FILE (override path; default $NEXUS_ROOT/state/bridge_config.tsv).
#   Precedence chain (per-field):
#     ttl / min_interval : CLI arg > config-file row > compiled default (3600 / 1)
#     ua                 : BRIDGE_HELPER_UA env > config-file ua > unset
#     accept             : BRIDGE_HELPER_HEADERS env > "accept: <config-row-accept>" > unset
#   Backward-compat: when config file absent OR bridge row missing, behaviour is
#   identical to ω-bridge-11. Per-bridge .hexa callers are unchanged. The config
#   table is opt-in via the loader function — explicit args still win, so today's
#   hardcoded TTLs in the .hexa files keep working until a future cycle simplifies
#   them. See state/omega_bridge_12_config_table.json.
#
# ω-bridge-11 (2026-04-26): secrets / API-key support.
#   New env: BRIDGE_HELPER_AUTH (full Authorization header value, e.g. "Bearer eyJ…").
#   When set:
#     - written to a mode-0600 tempfile and passed to curl via `--header @<tempfile>`
#       (no token in argv ⇒ ps-safe; trap on EXIT scrubs the tempfile)
#     - cache key incorporates sha1(auth)[0:8] so distinct tokens get distinct cache
#       entries (no cross-tenant cache poisoning) without exposing the raw token in
#       the filename
#     - any verbose log line containing the raw auth string is scrubbed and replaced
#       with "Authorization: <REDACTED>"
#   When unset: behaviour identical to ω-bridge-6 (zero-overhead backward-compat).
#   See state/omega_bridge_11_secrets.json.
#
# ω-bridge-6 (2026-04-26): JSON schema-drift detection.
#   Addresses latent regression risk for the 9 silently-PASS bridges in
#   state/omega_bridge_baseline.json: when an upstream API renames/removes/retypes a
#   top-level field, the curl fetch still returns 2xx and the bridge silently produces
#   malformed downstream output. This cycle adds a cheap deterministic fingerprint:
#       sha1( join("|", sort(top_level_keys(json_body))) )
#   stored per-bridge in state/bridge_schema_fingerprint.tsv (bridge \t fp \t iso_ts).
#   New subcommand:
#       fingerprint-check <bridge> <url> [<ttl>] [<min_interval>]
#         - On first run for a bridge → records baseline + emits "BASELINE_RECORDED <fp>"
#         - On subsequent runs → "MATCH <fp>"  (exit 0)
#                              or "DRIFT_DETECTED bridge=B expected=A actual=B" (exit 1)
#                              and writes a candidate row (does NOT overwrite baseline).
#         - On non-JSON / parse failure → "NON_JSON_BODY <bridge>" (exit 2)
#   Algorithm prefers `jq` (jq '. | keys'); if jq absent, falls back to grep over body for
#   /"<word>"\s*:/ then sort -u then sha1. Top-level only (cheap; doesn't catch nested
#   type changes — see omega_bridge_6_schema_drift.json for known limits).
#
# Compliance: raw 66 (reason+fix on diags), raw 71 (report-only diagnostics on stderr,
#             body unchanged on stdout), raw 73 (deterministic 4xx no-retry).

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$HOME/core/nexus}"
CACHE_DIR="${BRIDGE_HELPER_CACHE_DIR:-$NEXUS_ROOT/state/bridge_cache}"
MAX_RETRY="${BRIDGE_HELPER_MAX_RETRY:-3}"
MAX_TIME="${BRIDGE_HELPER_MAX_TIME:-12}"
VERBOSE="${BRIDGE_HELPER_VERBOSE:-0}"
CACHE_GC_AGE_S="${BRIDGE_HELPER_CACHE_GC_AGE_S:-7200}"
CACHE_MAX_BYTES="${BRIDGE_HELPER_CACHE_MAX_BYTES:-50000000}"
GC_PROBABILITY="${BRIDGE_HELPER_GC_PROBABILITY:-100}"
SCHEMA_FP_TSV="${BRIDGE_HELPER_SCHEMA_FP_TSV:-$NEXUS_ROOT/state/bridge_schema_fingerprint.tsv}"
# ω-bridge-12: per-bridge config table (TTL / min_interval / UA / accept). See header.
CONFIG_FILE="${BRIDGE_HELPER_CONFIG_FILE:-$NEXUS_ROOT/state/bridge_config.tsv}"

_log() {
    if [ "$VERBOSE" = "1" ]; then
        local msg="$*"
        # ω-bridge-11: redact the AUTH value if it appears verbatim in the log line.
        if [ -n "${BRIDGE_HELPER_AUTH:-}" ]; then
            # bash parameter substitution — replace all literal occurrences with REDACTED token.
            msg="${msg//${BRIDGE_HELPER_AUTH}/<REDACTED>}"
            # Also normalize "Authorization: <REDACTED>" form when the header label is present.
            msg="${msg//Authorization: <REDACTED>/Authorization: <REDACTED>}"
        fi
        echo "[bridge_helper] $msg" >&2
    fi
    return 0
}

_auth_hash() {
    # ω-bridge-11: short stable hash of the auth value (first 8 hex of sha1).
    # Empty input ⇒ empty output (so cache key is unchanged when AUTH unset).
    [ -z "${1:-}" ] && return 0
    printf '%s' "$1" | shasum -a 1 2>/dev/null | awk '{print substr($1,1,8)}'
}

_url_hash() {
    # short stable hash of URL (first 16 hex of sha1)
    printf '%s' "$1" | shasum -a 1 2>/dev/null | awk '{print substr($1,1,16)}'
}

_now_epoch() { date +%s; }

# ω-bridge-12: lookup per-bridge config row from $CONFIG_FILE.
# Sets globals: CFG_TTL CFG_MIN_INT CFG_UA CFG_ACCEPT (empty when absent or '-').
# Silent no-op when config file missing or no row matches the bridge name.
_load_bridge_config() {
    CFG_TTL=""; CFG_MIN_INT=""; CFG_UA=""; CFG_ACCEPT=""
    local bridge_name="${1:-}"
    [ -z "$bridge_name" ] && return 0
    [ -f "$CONFIG_FILE" ] || return 0
    # awk: skip comments + blanks, match column 1 exactly, emit TAB-separated fields.
    local row
    row=$(awk -F'\t' -v b="$bridge_name" '
        /^[[:space:]]*#/ {next}
        NF == 0 {next}
        $1 == b { printf "%s\t%s\t%s\t%s", $2, $3, $4, $5; exit }
    ' "$CONFIG_FILE" 2>/dev/null)
    [ -z "$row" ] && return 0
    # parse the 4 TAB-separated fields
    IFS=$'\t' read -r CFG_TTL CFG_MIN_INT CFG_UA CFG_ACCEPT <<< "$row"
    # treat literal '-' as unset
    [ "$CFG_TTL" = "-" ] && CFG_TTL=""
    [ "$CFG_MIN_INT" = "-" ] && CFG_MIN_INT=""
    [ "$CFG_UA" = "-" ] && CFG_UA=""
    [ "$CFG_ACCEPT" = "-" ] && CFG_ACCEPT=""
    _log "config: bridge=$bridge_name ttl=${CFG_TTL:-<unset>} min_int=${CFG_MIN_INT:-<unset>} ua=${CFG_UA:-<unset>} accept=${CFG_ACCEPT:-<unset>} (source=$CONFIG_FILE)"
    return 0
}

cmd_fetch() {
    local bridge="$1"
    local url="$2"
    # ω-bridge-12: precedence — CLI arg > config-file row > compiled default.
    # Capture whether caller passed an explicit ttl/min_interval (positional 3/4).
    local cli_ttl="${3:-}"
    local cli_min_interval="${4:-}"
    _load_bridge_config "$bridge"
    local ttl="${cli_ttl:-${CFG_TTL:-3600}}"
    local min_interval="${cli_min_interval:-${CFG_MIN_INT:-1}}"
    if [ -n "$cli_ttl" ]; then
        _log "ttl source=CLI val=$ttl"
    elif [ -n "$CFG_TTL" ]; then
        _log "ttl source=CONFIG val=$ttl"
    else
        _log "ttl source=DEFAULT val=$ttl"
    fi
    if [ -n "$cli_min_interval" ]; then
        _log "min_interval source=CLI val=$min_interval"
    elif [ -n "$CFG_MIN_INT" ]; then
        _log "min_interval source=CONFIG val=$min_interval"
    else
        _log "min_interval source=DEFAULT val=$min_interval"
    fi

    if [ -z "$bridge" ] || [ -z "$url" ]; then
        echo "bridge_helper: usage: fetch <bridge> <url> [ttl_sec] [min_interval_sec]" >&2
        echo "  reason: missing required arg" >&2
        echo "  fix:    bash tool/bridge_helper.sh fetch codata https://example.com 3600 1" >&2
        return 1
    fi

    # ω-bridge-4: assemble caller-supplied extras (UA / headers / per-call timeout) once.
    # Empty arrays ⇒ no behavioural change; backward-compat with ω-bridge-3 callers.
    # ω-bridge-12: fall back to config-table UA/accept when env vars unset.
    local -a extra_args=()
    local effective_ua="${BRIDGE_HELPER_UA:-}"
    local ua_source=""
    if [ -n "$effective_ua" ]; then
        ua_source="ENV"
    elif [ -n "${CFG_UA:-}" ]; then
        effective_ua="$CFG_UA"
        ua_source="CONFIG"
    fi
    if [ -n "$effective_ua" ]; then
        extra_args+=(-A "$effective_ua")
        _log "UA set (source=$ua_source): $effective_ua"
    fi
    if [ -n "${BRIDGE_HELPER_HEADERS:-}" ]; then
        while IFS= read -r hdr; do
            [ -n "$hdr" ] && extra_args+=(-H "$hdr") && _log "header set (source=ENV): $hdr"
        done <<< "$BRIDGE_HELPER_HEADERS"
    elif [ -n "${CFG_ACCEPT:-}" ]; then
        # config-table accept value → synthesize "accept: <value>" header.
        extra_args+=(-H "accept: $CFG_ACCEPT")
        _log "header set (source=CONFIG): accept: $CFG_ACCEPT"
    fi
    local effective_max_time="$MAX_TIME"
    if [ -n "${BRIDGE_HELPER_TIMEOUT:-}" ]; then
        effective_max_time="$BRIDGE_HELPER_TIMEOUT"
        _log "timeout override: $effective_max_time"
    fi

    # ω-bridge-11: if BRIDGE_HELPER_AUTH set, write to mode-0600 tempfile and pass via
    #   curl --header @<file>. This keeps the secret out of argv (ps-safe) and out of
    #   any error log curl might emit (curl uses the file content as the header value
    #   without echoing the path back). The tempfile is removed on EXIT.
    local _auth_tmp=""
    if [ -n "${BRIDGE_HELPER_AUTH:-}" ]; then
        _auth_tmp=$(mktemp 2>/dev/null) || _auth_tmp="/tmp/bridge_helper_auth_$$_${RANDOM}.tmp"
        # Mode 0600 — owner-only — defence in depth against multi-user systems.
        chmod 600 "$_auth_tmp" 2>/dev/null
        # curl --header @<file> reads the file content as the header value (single header).
        printf 'Authorization: %s' "$BRIDGE_HELPER_AUTH" > "$_auth_tmp"
        # Trap EXIT to scrub on any return path (success / 4xx / persistent fail).
        # shellcheck disable=SC2064  # intentional early-expansion of $_auth_tmp
        trap "rm -f '$_auth_tmp' 2>/dev/null" EXIT
        extra_args+=(--header "@$_auth_tmp")
        _log "AUTH header configured via tempfile (value redacted)"
    fi

    # bypass mode = raw passthrough (preserves legacy single-attempt behaviour for debug)
    if [ "${BRIDGE_HELPER_DISABLE:-0}" = "1" ]; then
        _log "DISABLE=1, raw curl passthrough"
        curl -s --max-time "$effective_max_time" ${extra_args[@]+"${extra_args[@]}"} "$url" 2>/dev/null
        return $?
    fi

    mkdir -p "$CACHE_DIR" 2>/dev/null

    # ω-bridge-5: probabilistic inline cache GC (default 1/100; silent side-effect).
    _maybe_gc_trigger

    local hash; hash=$(_url_hash "$url")
    # ω-bridge-11: when AUTH is set, append sha1(auth)[0:8] to the cache key so different
    # tokens yield different cached bodies (no cross-tenant leakage), without putting the
    # raw token in any filename. Auth-unset path: key unchanged ⇒ backward compatible.
    local auth_suffix=""
    if [ -n "${BRIDGE_HELPER_AUTH:-}" ]; then
        local _ah; _ah=$(_auth_hash "$BRIDGE_HELPER_AUTH")
        [ -n "$_ah" ] && auth_suffix="_a${_ah}"
    fi
    local cache_body="$CACHE_DIR/${bridge}_${hash}${auth_suffix}.body"
    local cache_meta="$CACHE_DIR/${bridge}_${hash}${auth_suffix}.meta"
    local lock_file="$CACHE_DIR/${bridge}.lastcall"

    # 1. Cache check
    if [ -f "$cache_body" ]; then
        local age
        local mtime
        mtime=$(stat -f %m "$cache_body" 2>/dev/null || stat -c %Y "$cache_body" 2>/dev/null)
        if [ -n "$mtime" ]; then
            age=$(( $(_now_epoch) - mtime ))
            if [ "$age" -lt "$ttl" ]; then
                _log "CACHE HIT bridge=$bridge age=${age}s ttl=${ttl}s url=$url"
                cat "$cache_body"
                return 0
            fi
            _log "CACHE STALE bridge=$bridge age=${age}s ttl=${ttl}s — refetching"
        fi
    else
        _log "CACHE MISS bridge=$bridge url=$url"
    fi

    # 2. Polite minimum interval between live calls per bridge
    if [ -f "$lock_file" ]; then
        local last
        last=$(cat "$lock_file" 2>/dev/null)
        if [ -n "$last" ]; then
            local since=$(( $(_now_epoch) - last ))
            if [ "$since" -lt "$min_interval" ]; then
                local sleep_for=$(( min_interval - since ))
                _log "RATE-LIMIT sleep=${sleep_for}s (last=${since}s ago, min=${min_interval}s)"
                sleep "$sleep_for"
            fi
        fi
    fi

    # synthetic-fail mode for retry validation (doesn't hit network)
    if [ "${BRIDGE_HELPER_FORCE_FAIL:-0}" = "1" ]; then
        _log "FORCE_FAIL=1 — simulating persistent 429"
        local attempt=1
        local delay=1
        while [ "$attempt" -le "$MAX_RETRY" ]; do
            _log "synthetic-429 attempt=$attempt; sleep=${delay}s"
            sleep "$delay"
            delay=$(( delay * 2 ))
            attempt=$(( attempt + 1 ))
        done
        echo "bridge_helper: synthetic-429 persistent fail after $MAX_RETRY attempts (FORCE_FAIL=1)" >&2
        echo "  reason: BRIDGE_HELPER_FORCE_FAIL=1 simulating sustained rate-limit" >&2
        echo "  fix:    unset BRIDGE_HELPER_FORCE_FAIL" >&2
        return 1
    fi

    # 3. Retry loop
    local attempt=1
    local delay=1
    local body=""
    local http_code=""
    local tmp_out
    tmp_out=$(mktemp 2>/dev/null) || tmp_out="/tmp/bridge_helper_$$_${RANDOM}.tmp"

    while [ "$attempt" -le "$MAX_RETRY" ]; do
        echo "$(_now_epoch)" > "$lock_file" 2>/dev/null
        # write body to tmp file; capture http_code separately so the stdout body stays clean
        http_code=$(curl -sS -o "$tmp_out" -w '%{http_code}' --max-time "$effective_max_time" ${extra_args[@]+"${extra_args[@]}"} "$url" 2>/dev/null)
        local curl_ec=$?
        body=$(cat "$tmp_out" 2>/dev/null)
        _log "attempt=$attempt curl_ec=$curl_ec http_code=$http_code body_bytes=${#body}"

        # Success path
        if [ "$curl_ec" = "0" ] && [ -n "$http_code" ]; then
            local code_class="${http_code:0:1}"
            if [ "$code_class" = "2" ] && [ -n "$body" ]; then
                # cache write
                printf '%s' "$body" > "$cache_body"
                printf 'ts=%s\nurl=%s\nhttp_code=%s\nttl=%s\nbridge=%s\n' \
                    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$url" "$http_code" "$ttl" "$bridge" \
                    > "$cache_meta"
                rm -f "$tmp_out" 2>/dev/null
                printf '%s' "$body"
                return 0
            fi
            # 4xx (non-429) = deterministic, no retry
            if [ "$code_class" = "4" ] && [ "$http_code" != "429" ]; then
                rm -f "$tmp_out" 2>/dev/null
                echo "bridge_helper: $bridge $url -> HTTP $http_code (deterministic 4xx — no retry)" >&2
                echo "  reason: client-side error, retry would not help" >&2
                echo "  fix:    inspect URL/path; consider falling back" >&2
                printf '%s' "$body"
                return 1
            fi
            # 429 + 5xx → backoff retry below
        fi

        if [ "$attempt" -lt "$MAX_RETRY" ]; then
            _log "retrying after ${delay}s (http_code=$http_code, ec=$curl_ec)"
            sleep "$delay"
            delay=$(( delay * 2 ))
        fi
        attempt=$(( attempt + 1 ))
    done

    rm -f "$tmp_out" 2>/dev/null
    echo "bridge_helper: $bridge $url -> persistent fail after $MAX_RETRY attempts (last http_code=$http_code)" >&2
    echo "  reason: 429 / 5xx / network error sustained across exponential backoff" >&2
    echo "  fix:    bridge should engage hardcoded fallback path; check upstream API status" >&2
    return 1
}

_file_mtime() {
    # cross-platform mtime in epoch seconds
    stat -f %m "$1" 2>/dev/null || stat -c %Y "$1" 2>/dev/null
}

_file_size() {
    stat -f %z "$1" 2>/dev/null || stat -c %s "$1" 2>/dev/null
}

cmd_cache_gc() {
    # Sweep $CACHE_DIR: delete .body (and matching .meta) older than CACHE_GC_AGE_S,
    # then enforce CACHE_MAX_BYTES by oldest-first eviction.
    # Emits TSV summary to stdout: scanned\tkept\tdeleted\tbytes_freed
    local age_s="${1:-$CACHE_GC_AGE_S}"
    local max_bytes="${2:-$CACHE_MAX_BYTES}"

    if [ ! -d "$CACHE_DIR" ]; then
        printf 'scanned=0\tkept=0\tdeleted=0\tbytes_freed=0\n'
        _log "cache-gc: no cache dir at $CACHE_DIR"
        return 0
    fi

    local now scanned=0 kept=0 deleted=0 bytes_freed=0
    now=$(_now_epoch)

    # Phase A: age-based eviction (single-pass, race-safe via stat-then-rm; if file
    # vanishes between stat and rm, rm -f silently no-ops).
    local f mtime size age
    for f in "$CACHE_DIR"/*.body; do
        [ -f "$f" ] || continue
        scanned=$(( scanned + 1 ))
        mtime=$(_file_mtime "$f")
        if [ -z "$mtime" ]; then
            kept=$(( kept + 1 ))
            continue
        fi
        age=$(( now - mtime ))
        if [ "$age" -ge "$age_s" ]; then
            size=$(_file_size "$f")
            [ -z "$size" ] && size=0
            rm -f "$f" 2>/dev/null
            rm -f "${f%.body}.meta" 2>/dev/null
            deleted=$(( deleted + 1 ))
            bytes_freed=$(( bytes_freed + size ))
            _log "cache-gc: deleted (age=${age}s ≥ ${age_s}s) $f"
        else
            kept=$(( kept + 1 ))
        fi
    done

    # Phase B: size-limit eviction. Compute total size of remaining .body files.
    if [ "$max_bytes" -gt 0 ]; then
        local total=0
        for f in "$CACHE_DIR"/*.body; do
            [ -f "$f" ] || continue
            size=$(_file_size "$f")
            [ -z "$size" ] && size=0
            total=$(( total + size ))
        done
        if [ "$total" -gt "$max_bytes" ]; then
            _log "cache-gc: size $total > limit $max_bytes — oldest-first eviction"
            # build "<mtime> <size> <path>" list, sort numeric ascending by mtime
            local sorted_list
            sorted_list=$(
                for f in "$CACHE_DIR"/*.body; do
                    [ -f "$f" ] || continue
                    mtime=$(_file_mtime "$f")
                    size=$(_file_size "$f")
                    [ -z "$mtime" ] && mtime=0
                    [ -z "$size" ] && size=0
                    printf '%s\t%s\t%s\n' "$mtime" "$size" "$f"
                done | sort -n
            )
            # iterate eldest first; delete until under limit
            while IFS=$'\t' read -r mtime size f; do
                [ "$total" -le "$max_bytes" ] && break
                [ -z "$f" ] && continue
                rm -f "$f" 2>/dev/null
                rm -f "${f%.body}.meta" 2>/dev/null
                deleted=$(( deleted + 1 ))
                bytes_freed=$(( bytes_freed + size ))
                total=$(( total - size ))
                kept=$(( kept - 1 ))
                _log "cache-gc: size-evicted (mtime=$mtime size=$size) $f"
            done <<< "$sorted_list"
        fi
    fi

    printf 'scanned=%d\tkept=%d\tdeleted=%d\tbytes_freed=%d\n' \
        "$scanned" "$kept" "$deleted" "$bytes_freed"
    return 0
}

_maybe_gc_trigger() {
    # Probabilistic inline cache-gc — silent (stdout suppressed; verbose still goes to stderr).
    # Disabled when GC_PROBABILITY=0. Triggers when ($RANDOM % N) == 0.
    [ "$GC_PROBABILITY" = "0" ] && return 0
    [ "$GC_PROBABILITY" -le "0" ] 2>/dev/null && return 0
    if [ "$(( RANDOM % GC_PROBABILITY ))" = "0" ]; then
        _log "probabilistic-gc fired (1/$GC_PROBABILITY)"
        cmd_cache_gc "$CACHE_GC_AGE_S" "$CACHE_MAX_BYTES" >/dev/null 2>&1 || true
    fi
    return 0
}

cmd_cache_clear() {
    local bridge="${1:-}"
    if [ -z "$bridge" ]; then
        echo "bridge_helper: cache-clear requires <bridge_name> (or 'all')" >&2
        return 1
    fi
    if [ "$bridge" = "all" ]; then
        rm -rf "$CACHE_DIR" 2>/dev/null
        echo "bridge_helper: cleared all cache at $CACHE_DIR" >&2
    else
        rm -f "$CACHE_DIR/${bridge}_"*.body "$CACHE_DIR/${bridge}_"*.meta "$CACHE_DIR/${bridge}.lastcall" 2>/dev/null
        echo "bridge_helper: cleared cache for bridge=$bridge" >&2
    fi
    return 0
}

cmd_cache_stat() {
    if [ ! -d "$CACHE_DIR" ]; then
        echo "bridge_helper: no cache dir at $CACHE_DIR" >&2
        return 0
    fi
    local n_body
    n_body=$(ls -1 "$CACHE_DIR"/*.body 2>/dev/null | wc -l | tr -d ' ')
    local n_lock
    n_lock=$(ls -1 "$CACHE_DIR"/*.lastcall 2>/dev/null | wc -l | tr -d ' ')
    echo "bridge_helper: cache_dir=$CACHE_DIR cached_responses=$n_body bridges_with_lock=$n_lock" >&2
    return 0
}

_compute_schema_fingerprint() {
    # Reads JSON body from $1 (file path). Emits sha1 of sorted top-level keys joined by '|'.
    # Empty string on parse failure (caller treats as NON_JSON).
    local body_file="$1"
    [ -f "$body_file" ] || { printf ''; return 1; }
    local size
    size=$(_file_size "$body_file")
    [ -z "$size" ] || [ "$size" -le 0 ] && { printf ''; return 1; }

    local keys=""
    if command -v jq >/dev/null 2>&1; then
        # jq: only valid for top-level object; arrays/scalars → use synthetic marker
        local first_byte
        first_byte=$(head -c 1 "$body_file" 2>/dev/null)
        if [ "$first_byte" = "{" ]; then
            keys=$(jq -r 'keys | sort | join("|")' "$body_file" 2>/dev/null)
        elif [ "$first_byte" = "[" ]; then
            # array: fingerprint the keys of the first element if it's an object
            keys=$(jq -r '(.[0] // {}) | if type == "object" then "__array__:" + (keys | sort | join("|")) else "__array_of_" + type + "__" end' "$body_file" 2>/dev/null)
        else
            # scalar / non-JSON
            printf ''
            return 1
        fi
    else
        # grep fallback: extract /"<word>"\s*:/ matches near the start of the body.
        # Crude — picks up nested keys too — but deterministic and catches gross drift.
        keys=$(grep -oE '"[A-Za-z_][A-Za-z0-9_]*"[[:space:]]*:' "$body_file" 2>/dev/null \
            | sed -E 's/"([^"]+)".*/\1/' | sort -u | tr '\n' '|' | sed 's/|$//')
    fi

    if [ -z "$keys" ]; then
        printf ''
        return 1
    fi
    printf '%s' "$keys" | shasum -a 1 2>/dev/null | awk '{print substr($1,1,16)}'
    return 0
}

_lookup_baseline_fp() {
    # Reads baseline fp for bridge $1 from $SCHEMA_FP_TSV. Emits fp on stdout (empty if none).
    local bridge="$1"
    [ -f "$SCHEMA_FP_TSV" ] || return 0
    awk -F'\t' -v b="$bridge" '$1 == b && $2 !~ /^candidate:/ {print $2; exit}' "$SCHEMA_FP_TSV" 2>/dev/null
    return 0
}

_record_baseline_fp() {
    # Append baseline row for bridge $1, fp $2.
    local bridge="$1" fp="$2"
    local ts; ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    mkdir -p "$(dirname "$SCHEMA_FP_TSV")" 2>/dev/null
    printf '%s\t%s\t%s\n' "$bridge" "$fp" "$ts" >> "$SCHEMA_FP_TSV"
    return 0
}

_record_candidate_fp() {
    # Append candidate (drift) row for operator-approved rotation. Tagged with prefix.
    local bridge="$1" fp="$2"
    local ts; ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    mkdir -p "$(dirname "$SCHEMA_FP_TSV")" 2>/dev/null
    printf '%s\tcandidate:%s\t%s\n' "$bridge" "$fp" "$ts" >> "$SCHEMA_FP_TSV"
    return 0
}

cmd_fingerprint_check() {
    # fingerprint-check <bridge> <url> [<ttl>] [<min_interval>]
    # Wraps cmd_fetch via a tmp body file so we can fingerprint without polluting stdout.
    # Stdout: status line; Stderr: diagnostics. Body itself is NOT echoed.
    local bridge="${1:-}"
    local url="${2:-}"
    local ttl="${3:-3600}"
    local min_interval="${4:-1}"

    if [ -z "$bridge" ] || [ -z "$url" ]; then
        echo "bridge_helper: usage: fingerprint-check <bridge> <url> [ttl] [min_interval]" >&2
        echo "  reason: missing required arg" >&2
        echo "  fix:    bash tool/bridge_helper.sh fingerprint-check codata https://... 3600 1" >&2
        return 2
    fi

    local tmp_body
    tmp_body=$(mktemp 2>/dev/null) || tmp_body="/tmp/bridge_helper_fp_$$_${RANDOM}.tmp"

    # cmd_fetch emits body to stdout — capture into tmp file
    if ! cmd_fetch "$bridge" "$url" "$ttl" "$min_interval" > "$tmp_body" 2>/dev/null; then
        rm -f "$tmp_body" 2>/dev/null
        echo "FETCH_FAIL bridge=$bridge url=$url"
        echo "bridge_helper: fingerprint-check fetch failed for $bridge" >&2
        echo "  reason: cmd_fetch returned non-zero (network/4xx/persistent fail)" >&2
        echo "  fix:    inspect bridge cache + upstream API status" >&2
        return 2
    fi

    local actual_fp
    actual_fp=$(_compute_schema_fingerprint "$tmp_body")
    rm -f "$tmp_body" 2>/dev/null

    if [ -z "$actual_fp" ]; then
        echo "NON_JSON_BODY bridge=$bridge"
        echo "bridge_helper: fingerprint-check: body is not parseable JSON for $bridge" >&2
        echo "  reason: top-level is scalar / empty / not JSON object-or-array" >&2
        echo "  fix:    use this bridge with text-based monitoring instead of fingerprint-check" >&2
        return 2
    fi

    local baseline_fp
    baseline_fp=$(_lookup_baseline_fp "$bridge")

    if [ -z "$baseline_fp" ]; then
        _record_baseline_fp "$bridge" "$actual_fp"
        echo "BASELINE_RECORDED bridge=$bridge fp=$actual_fp"
        return 0
    fi

    if [ "$actual_fp" = "$baseline_fp" ]; then
        echo "MATCH bridge=$bridge fp=$actual_fp"
        return 0
    fi

    _record_candidate_fp "$bridge" "$actual_fp"
    # to stderr per design (drift = actionable signal for ops)
    echo "DRIFT_DETECTED bridge=$bridge expected=$baseline_fp actual=$actual_fp" >&2
    echo "bridge_helper: schema drift on bridge=$bridge" >&2
    echo "  reason: top-level field set changed since baseline (rename/add/remove)" >&2
    echo "  fix:    inspect upstream API; if intentional, manually rotate baseline in $SCHEMA_FP_TSV" >&2
    # also emit a DRIFT line on stdout so callers piping stdout still see status
    echo "DRIFT_DETECTED bridge=$bridge expected=$baseline_fp actual=$actual_fp"
    return 1
}

case "${1:-}" in
    fetch)
        shift
        cmd_fetch "$@"
        ;;
    cache-clear)
        shift
        cmd_cache_clear "$@"
        ;;
    cache-stat)
        cmd_cache_stat
        ;;
    cache-gc)
        shift
        cmd_cache_gc "$@"
        ;;
    fingerprint-check)
        shift
        cmd_fingerprint_check "$@"
        ;;
    --help|-h|"")
        sed -n '3,75p' "$0"
        exit 0
        ;;
    *)
        echo "bridge_helper: unknown subcommand: $1" >&2
        echo "  reason: not in {fetch, cache-clear, cache-stat, cache-gc, fingerprint-check, --help}" >&2
        echo "  fix:    bash tool/bridge_helper.sh --help" >&2
        exit 1
        ;;
esac
