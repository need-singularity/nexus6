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
#   BRIDGE_HELPER_CACHE_DIR   : cache root (default $NEXUS_ROOT/state/bridge_cache)
#   BRIDGE_HELPER_DISABLE     : if "1", bypass cache + retry + rate-limit (raw curl)
#   BRIDGE_HELPER_FORCE_FAIL  : if "1", skip live curl entirely (synthetic 429-style)
#   BRIDGE_HELPER_MAX_RETRY   : override retry count (default 3)
#   BRIDGE_HELPER_MAX_TIME    : per-request curl --max-time (default 12)
#   BRIDGE_HELPER_VERBOSE     : if "1", emit diagnostic trace to stderr
#
# Compliance: raw 66 (reason+fix on diags), raw 71 (report-only diagnostics on stderr,
#             body unchanged on stdout), raw 73 (deterministic 4xx no-retry).

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$HOME/core/nexus}"
CACHE_DIR="${BRIDGE_HELPER_CACHE_DIR:-$NEXUS_ROOT/state/bridge_cache}"
MAX_RETRY="${BRIDGE_HELPER_MAX_RETRY:-3}"
MAX_TIME="${BRIDGE_HELPER_MAX_TIME:-12}"
VERBOSE="${BRIDGE_HELPER_VERBOSE:-0}"

_log() {
    [ "$VERBOSE" = "1" ] && echo "[bridge_helper] $*" >&2
    return 0
}

_url_hash() {
    # short stable hash of URL (first 16 hex of sha1)
    printf '%s' "$1" | shasum -a 1 2>/dev/null | awk '{print substr($1,1,16)}'
}

_now_epoch() { date +%s; }

cmd_fetch() {
    local bridge="$1"
    local url="$2"
    local ttl="${3:-3600}"
    local min_interval="${4:-1}"

    if [ -z "$bridge" ] || [ -z "$url" ]; then
        echo "bridge_helper: usage: fetch <bridge> <url> [ttl_sec] [min_interval_sec]" >&2
        echo "  reason: missing required arg" >&2
        echo "  fix:    bash tool/bridge_helper.sh fetch codata https://example.com 3600 1" >&2
        return 1
    fi

    # bypass mode = raw passthrough (preserves legacy single-attempt behaviour for debug)
    if [ "${BRIDGE_HELPER_DISABLE:-0}" = "1" ]; then
        _log "DISABLE=1, raw curl passthrough"
        curl -s --max-time "$MAX_TIME" "$url" 2>/dev/null
        return $?
    fi

    mkdir -p "$CACHE_DIR" 2>/dev/null
    local hash; hash=$(_url_hash "$url")
    local cache_body="$CACHE_DIR/${bridge}_${hash}.body"
    local cache_meta="$CACHE_DIR/${bridge}_${hash}.meta"
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
        http_code=$(curl -sS -o "$tmp_out" -w '%{http_code}' --max-time "$MAX_TIME" "$url" 2>/dev/null)
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
    --help|-h|"")
        sed -n '3,50p' "$0"
        exit 0
        ;;
    *)
        echo "bridge_helper: unknown subcommand: $1" >&2
        echo "  reason: not in {fetch, cache-clear, cache-stat, --help}" >&2
        echo "  fix:    bash tool/bridge_helper.sh --help" >&2
        exit 1
        ;;
esac
