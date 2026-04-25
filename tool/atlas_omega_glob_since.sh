#!/usr/bin/env bash
# atlas_omega_glob_since.sh — emit only changed/new omega_cycle witness JSONs since
# a given moment. Wrapper that avoids omega_cycle_atlas_ingest re-globbing all
# witnesses every run. Pure bash, no hexa dep. macOS BSD date / Linux GNU date
# both supported (best effort).
#
# Usage:
#   atlas_omega_glob_since.sh                       # default: --since 1.day
#   atlas_omega_glob_since.sh --since 2026-04-26
#   atlas_omega_glob_since.sh --since 1.day
#   atlas_omega_glob_since.sh --since yesterday
#   atlas_omega_glob_since.sh --since-commit <HASH> # git log --since <HASH>
#   atlas_omega_glob_since.sh --since-last-ingest   # state/atlas_ingest_history.jsonl
#   atlas_omega_glob_since.sh --emit-paths          # one path / line (default mode)
#   atlas_omega_glob_since.sh --json                # json summary
#   atlas_omega_glob_since.sh --repo-only nexus     # restrict to one repo
#
# Exit codes:
#   0  PASS — paths emitted (possibly zero, in --json mode always 0 if call sane)
#   1  usage
#   2  no witnesses changed since cutoff (only in non-json mode w/ --strict)
#
# Sentinel (always to stderr at end):
#   __ATLAS_OMEGA_GLOB_SINCE__ since=<ISO> witnesses_total=N changed=C
#
# Spec: improvement_ideas ω-cycle axis i18 (Phase 2 omega_cycle_atlas_ingest
# 매 실행 전체 glob 회피). omega_cycle_atlas_ingest.hexa 는 수정 금지.

set -u
set -o pipefail

# ─── repo paths (mirror omega_cycle_atlas_ingest._repo_paths) ─────────
_repo_paths() {
    cat <<'EOF'
nexus|/Users/ghost/core/nexus/design
n6-architecture|/Users/ghost/core/n6-architecture/design
anima|/Users/ghost/core/anima/design
EOF
}

# ─── option state ──────────────────────────────────────────────────────
SINCE_RAW=""
SINCE_MODE=""        # date | commit | last-ingest
REPO_ONLY=""
EMIT_MODE="paths"    # paths | json
STRICT=0

# ─── arg parse ─────────────────────────────────────────────────────────
_usage() {
    cat <<'EOF'
usage: atlas_omega_glob_since.sh [--since DATE|1.day|yesterday]
                                 [--since-commit HASH]
                                 [--since-last-ingest]
                                 [--emit-paths] [--json]
                                 [--repo-only NAME] [--strict] [--help]

modes (mutually exclusive cutoff):
  --since DATE          YYYY-MM-DD or "N.day" or "yesterday" or "N.hour"
  --since-commit HASH   git log --since HASH (uses commit ts of HASH)
  --since-last-ingest   read state/atlas_ingest_history.jsonl last entry .ts

output modes:
  --emit-paths          one absolute path per line on stdout (default)
  --json                summary JSON to stdout

other:
  --repo-only NAME      restrict to one of: nexus | n6-architecture | anima
  --strict              exit 2 if zero changed witnesses (default: exit 0)

default cutoff if none given: --since 1.day
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --since)
            SINCE_RAW="${2:-}"; SINCE_MODE="date"; shift 2 || { _usage; exit 1; } ;;
        --since-commit)
            SINCE_RAW="${2:-}"; SINCE_MODE="commit"; shift 2 || { _usage; exit 1; } ;;
        --since-last-ingest)
            SINCE_MODE="last-ingest"; shift ;;
        --repo-only)
            REPO_ONLY="${2:-}"; shift 2 || { _usage; exit 1; } ;;
        --emit-paths) EMIT_MODE="paths"; shift ;;
        --json)       EMIT_MODE="json"; shift ;;
        --strict)     STRICT=1; shift ;;
        --help|-h)    _usage; exit 0 ;;
        *)
            echo "atlas_omega_glob_since: unknown arg: $1" >&2
            _usage >&2
            exit 1 ;;
    esac
done

# default
if [ -z "$SINCE_MODE" ]; then
    SINCE_MODE="date"
    SINCE_RAW="1.day"
fi

# ─── date helpers (BSD/GNU best effort) ────────────────────────────────
_to_epoch() {
    # arg: ISO YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ → unix ts (stdout)
    # IMPORTANT: BSD `date -j -f %Y-%m-%d` substitutes *current* HH:MM:SS for
    # missing components — so we always force " 00:00:00" for date-only inputs
    # to anchor at local-tz midnight (matches user mental model).
    local s="$1"
    if [ -z "$s" ]; then echo 0; return; fi
    # strip trailing Z for parser
    local v="${s%Z}"
    # try BSD date first
    if date -j -f "%Y-%m-%dT%H:%M:%S" "$v" +%s 2>/dev/null; then return; fi
    # date-only: force midnight
    if [[ "$v" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        if date -j -f "%Y-%m-%d %H:%M:%S" "$v 00:00:00" +%s 2>/dev/null; then return; fi
    fi
    # try GNU date
    if date -d "$s" +%s 2>/dev/null; then return; fi
    echo 0
}

_now_epoch() { date +%s; }

_resolve_since_epoch() {
    case "$SINCE_MODE" in
        date)
            local raw="$SINCE_RAW"
            # special: N.day / N.hour / yesterday
            if [ "$raw" = "yesterday" ]; then
                if date -v-1d +%s 2>/dev/null; then return; fi
                date -d "yesterday" +%s 2>/dev/null && return
                echo 0; return
            fi
            if [[ "$raw" =~ ^([0-9]+)\.day$ ]]; then
                local n="${BASH_REMATCH[1]}"
                if date -v-${n}d +%s 2>/dev/null; then return; fi
                date -d "${n} days ago" +%s 2>/dev/null && return
                echo 0; return
            fi
            if [[ "$raw" =~ ^([0-9]+)\.hour$ ]]; then
                local n="${BASH_REMATCH[1]}"
                if date -v-${n}H +%s 2>/dev/null; then return; fi
                date -d "${n} hours ago" +%s 2>/dev/null && return
                echo 0; return
            fi
            # plain ISO date
            _to_epoch "$raw"
            ;;
        commit)
            local hash="$SINCE_RAW"
            if [ -z "$hash" ]; then echo 0; return; fi
            # pick first repo that has the hash
            local found=""
            for line in $(_repo_paths); do
                local rdir="${line#*|}"
                local repo_root="${rdir%/design}"
                if [ -d "$repo_root/.git" ]; then
                    if git -C "$repo_root" cat-file -e "$hash^{commit}" 2>/dev/null; then
                        found="$repo_root"
                        break
                    fi
                fi
            done
            if [ -z "$found" ]; then
                echo "atlas_omega_glob_since: commit $hash not found in any repo" >&2
                echo 0; return
            fi
            git -C "$found" show -s --format=%ct "$hash" 2>/dev/null
            ;;
        last-ingest)
            local hist="/Users/ghost/core/nexus/state/atlas_ingest_history.jsonl"
            if [ ! -f "$hist" ]; then
                # graceful fallback: epoch 0 = "all"
                echo "atlas_omega_glob_since: $hist absent → fallback all" >&2
                echo 0
                return
            fi
            # last line .ts (string like "2026-04-25T14:00:15Z")
            local ts
            ts=$(tail -n 1 "$hist" | sed -E 's/.*"ts":"([^"]+)".*/\1/')
            if [ -z "$ts" ] || [ "$ts" = "$(tail -n 1 "$hist")" ]; then
                echo "atlas_omega_glob_since: cannot parse ts in $hist → fallback all" >&2
                echo 0
                return
            fi
            _to_epoch "$ts"
            ;;
        *) echo 0 ;;
    esac
}

# ─── file mtime (BSD/GNU) ──────────────────────────────────────────────
_file_mtime() {
    local f="$1"
    if stat -f %m "$f" 2>/dev/null; then return; fi
    stat -c %Y "$f" 2>/dev/null
}

# ─── main scan ─────────────────────────────────────────────────────────
SINCE_EPOCH=$(_resolve_since_epoch | tail -n 1)
if [ -z "$SINCE_EPOCH" ]; then SINCE_EPOCH=0; fi

# pretty since for sentinel
_since_iso() {
    local e="$1"
    if [ "$e" = "0" ]; then echo "epoch-0-all"; return; fi
    if date -r "$e" -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null; then return; fi
    date -u -d "@$e" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null
}
SINCE_ISO=$(_since_iso "$SINCE_EPOCH")

declare -a ALL_PATHS=()
declare -a CHANGED_PATHS=()
declare -a CHANGED_REPOS=()

for line in $(_repo_paths); do
    name="${line%%|*}"
    rdir="${line#*|}"
    if [ -n "$REPO_ONLY" ] && [ "$REPO_ONLY" != "$name" ]; then continue; fi
    [ -d "$rdir" ] || continue
    while IFS= read -r p; do
        [ -z "$p" ] && continue
        ALL_PATHS+=("$p")
        m=$(_file_mtime "$p")
        [ -z "$m" ] && m=0
        if [ "$m" -ge "$SINCE_EPOCH" ]; then
            CHANGED_PATHS+=("$p")
            CHANGED_REPOS+=("$name")
        fi
    done < <(find "$rdir" -name '*omega_cycle*.json' -type f 2>/dev/null | sort)
done

TOTAL=${#ALL_PATHS[@]}
CHANGED=${#CHANGED_PATHS[@]}

# ─── emit ──────────────────────────────────────────────────────────────
if [ "$EMIT_MODE" = "json" ]; then
    printf '{"since":"%s","since_epoch":%s,"witnesses_total":%d,"changed":%d,"paths":[' \
        "$SINCE_ISO" "$SINCE_EPOCH" "$TOTAL" "$CHANGED"
    first=1
    i=0
    while [ $i -lt $CHANGED ]; do
        if [ $first -eq 1 ]; then first=0; else printf ','; fi
        printf '{"repo":"%s","path":"%s"}' "${CHANGED_REPOS[$i]}" "${CHANGED_PATHS[$i]}"
        i=$((i+1))
    done
    printf ']}\n'
else
    for p in "${CHANGED_PATHS[@]:-}"; do
        [ -n "$p" ] && printf '%s\n' "$p"
    done
fi

# ─── sentinel + exit ───────────────────────────────────────────────────
echo "__ATLAS_OMEGA_GLOB_SINCE__ since=$SINCE_ISO witnesses_total=$TOTAL changed=$CHANGED" >&2

if [ "$CHANGED" -eq 0 ] && [ "$STRICT" -eq 1 ]; then
    exit 2
fi
exit 0
