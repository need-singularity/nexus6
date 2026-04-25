#!/usr/bin/env bash
# tool/falsifier_health_parallel.sh — parallel falsifier registry health check
#
# Drop-in equivalent of tool/falsifier_health.sh, but uses python3
# concurrent.futures.ProcessPoolExecutor to fan out cmd execution across
# N workers (default = cpu_count()). Aggregates results in main process,
# emits IDENTICAL sentinel + timeline JSONL to sequential version.
#
# usage:
#   tool/falsifier_health_parallel.sh           # human + sentinel + timeline append
#   tool/falsifier_health_parallel.sh --quiet   # only sentinel line on stdout
#   tool/falsifier_health_parallel.sh --json    # JSONL summary on stdout
#   tool/falsifier_health_parallel.sh --strict  # also verify registry SHA256
#   tool/falsifier_health_parallel.sh -j 8      # worker count (default cpu_count)
#
# Exit:
#   0 if all CLEAN
#   76 if any HIT/ERROR (raw 23 schema-guard analog)
#   1 on usage / registry-missing
#
# Sentinel (raw 80 — IDENTICAL to falsifier_health.sh):
#   __FALSIFIER_HEALTH__ <PASS|WARN|FAIL> total=N clean=C hit=H error=E tampered=T duration_ms=DD
#
# Compliance: raw 66 (reason+fix trailers) + raw 71 (report-only) +
#             raw 73 (admissibility — output equivalent to sequential) +
#             raw 77 (read-only registry) + raw 80 (sentinel format unchanged)
# Origin: design/hexa_sim/2026-04-26_falsifier_health_parallelize_omega_cycle.json

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$HOME/core/nexus}"
REGISTRY="${FALSIFIER_REGISTRY:-$NEXUS_ROOT/design/hexa_sim/falsifiers.jsonl}"
TIMELINE="${ATLAS_HEALTH_TIMELINE:-$NEXUS_ROOT/state/atlas_health_timeline.jsonl}"
REGISTRY_BASELINE="${FALSIFIER_REGISTRY_BASELINE:-$NEXUS_ROOT/state/falsifier_registry.sha256}"

QUIET=0
JSON=0
STRICT=0
JOBS=0   # 0 → python picks cpu_count()

while [ $# -gt 0 ]; do
    case "$1" in
        --quiet)  QUIET=1; shift ;;
        --json)   JSON=1; shift ;;
        --strict) STRICT=1; shift ;;
        -j)
            shift
            JOBS="${1:-0}"
            shift || true
            ;;
        -j*)
            JOBS="${1#-j}"
            shift
            ;;
        --jobs=*)
            JOBS="${1#--jobs=}"
            shift
            ;;
        --help|-h)
            sed -n '3,30p' "$0"
            exit 0
            ;;
        *)
            echo "usage error: unknown flag: $1" >&2
            echo "  reason: unrecognised CLI argument" >&2
            echo "  fix:    use --quiet | --json | --strict | -j N | --help" >&2
            exit 1
            ;;
    esac
done

if [ ! -f "$REGISTRY" ]; then
    echo "error: falsifier registry not found at $REGISTRY" >&2
    echo "  reason: FALSIFIER_REGISTRY env or default path missing" >&2
    echo "  fix:    set FALSIFIER_REGISTRY=/path/to/falsifiers.jsonl" >&2
    exit 1
fi

# R3 lite: optional --strict — same as sequential
if [ "$STRICT" = "1" ]; then
    if [ ! -f "$REGISTRY_BASELINE" ]; then
        echo "warning: --strict requested but baseline not found at $REGISTRY_BASELINE" >&2
        echo "  reason: registry baseline file missing" >&2
        echo "  fix:    sha256sum \"$REGISTRY\" | awk '{print \$1}' > \"$REGISTRY_BASELINE\"" >&2
    else
        BASELINE_HASH=$(awk '{print $1}' "$REGISTRY_BASELINE" 2>/dev/null)
        CURRENT_HASH=$(shasum -a 256 "$REGISTRY" 2>/dev/null | awk '{print $1}')
        [ -z "$CURRENT_HASH" ] && CURRENT_HASH=$(sha256sum "$REGISTRY" 2>/dev/null | awk '{print $1}')
        if [ "$BASELINE_HASH" != "$CURRENT_HASH" ]; then
            echo "warning: registry SHA256 drift vs baseline" >&2
            echo "  baseline: $BASELINE_HASH" >&2
            echo "  current:  $CURRENT_HASH" >&2
            echo "  reason: registry mutated since baseline pin" >&2
            echo "  fix:    audit git log of $REGISTRY; if intended, refresh baseline" >&2
        fi
    fi
fi

NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)

if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
    echo "═══ FALSIFIER HEALTH (parallel) — $NOW (UTC)"
    echo "registry: $REGISTRY"
fi

# Hand off to python worker. ProcessPoolExecutor needs a real importable
# module path (cannot fork from a heredoc <stdin> source), so we materialise
# the worker to a temp .py file and exec it.
WORKER_PY="$(mktemp -t falsifier_health_worker.XXXXXX).py"
trap 'rm -f "$WORKER_PY"' EXIT

cat >"$WORKER_PY" <<'PYEOF'
import concurrent.futures
import hashlib
import json
import os
import re
import subprocess
import sys
import time

REGISTRY = os.environ["REGISTRY"]
JOBS_ENV = int(os.environ.get("JOBS", "0") or 0)

# Match sequential R2 anti-spoof regex: ^echo[A-Z][A-Z0-9_]*$ (after whitespace strip).
SPOOF_RE = re.compile(r"^echo[A-Z][A-Z0-9_]*$")
# Match sequential grep-style HIT detector: 'grep -q[E|F]?<space>'
GREP_HIT_RE = re.compile(r"grep -q[EF]?\s")

def sha256_16(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]

def classify(entry):
    """Return (fid, slug, status, ec, dur_ms, extra) for a single registry entry."""
    try:
        d = json.loads(entry)
    except Exception:
        return ("", "", "ERROR", "parse", 0, "json_parse_fail")
    fid = d.get("id", "")
    slug = d.get("slug", "")
    pass_token = d.get("pass", "")
    cmd_sha256_decl = d.get("cmd_sha256", "")
    cmd = d.get("cmd", "")
    if not fid:
        return ("", "", "SKIP", "noid", 0, "missing_id")
    # R1 cmd_sha256 verification
    if cmd_sha256_decl:
        live = sha256_16(cmd)
        if live != cmd_sha256_decl:
            return (fid, slug, "TAMPERED", "tampered", 0,
                    f"declared={cmd_sha256_decl} live={live}")
    # R2 anti-spoof lint
    cmd_trimmed = re.sub(r"\s+", "", cmd)
    if SPOOF_RE.match(cmd_trimmed):
        return (fid, slug, "SPOOF", "spoof", 0, "anti_spoof_lint")
    # eval cmd
    t0 = time.monotonic_ns()
    try:
        proc = subprocess.run(
            ["bash", "-c", cmd],
            capture_output=True,
            text=True,
            timeout=120,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        ec = proc.returncode
    except subprocess.TimeoutExpired:
        return (fid, slug, "ERROR", "timeout", 120000, "subprocess_timeout")
    except Exception as exc:
        return (fid, slug, "ERROR", "exc", 0, f"subprocess_exc={exc}")
    t1 = time.monotonic_ns()
    dur_ms = (t1 - t0) // 1_000_000
    # Status disambiguation (mirrors sequential)
    if ec == 0:
        if pass_token and pass_token in out:
            return (fid, slug, "CLEAN", str(ec), dur_ms, "")
        return (fid, slug, "HIT", str(ec), dur_ms, "")
    if ec == 1 and GREP_HIT_RE.search(cmd):
        return (fid, slug, "HIT", str(ec), dur_ms, "anchor_grep_miss")
    return (fid, slug, "ERROR", str(ec), dur_ms, "")

def main():
    with open(REGISTRY, "r") as fh:
        entries = [ln for ln in (l.rstrip("\n") for l in fh) if ln]
    workers = JOBS_ENV if JOBS_ENV > 0 else (os.cpu_count() or 4)
    wall_t0 = time.monotonic_ns()
    results = [None] * len(entries)
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(classify, e): i for i, e in enumerate(entries)}
        for fut in concurrent.futures.as_completed(futs):
            idx = futs[fut]
            try:
                results[idx] = fut.result()
            except Exception as exc:
                results[idx] = ("", "", "ERROR", "future", 0, f"future_exc={exc}")
    wall_t1 = time.monotonic_ns()
    wall_ms = (wall_t1 - wall_t0) // 1_000_000
    total = clean = hit = error = tampered = 0
    for r in results:
        if r is None:
            continue
        fid, slug, status, ec, dur_ms, extra = r
        if status == "SKIP":
            continue
        total += 1
        if status == "CLEAN":
            clean += 1
        elif status == "HIT":
            hit += 1
        elif status == "TAMPERED":
            tampered += 1
            error += 1
        else:
            # ERROR or SPOOF
            error += 1
        sys.stdout.write(f"{fid}\t{slug}\t{status}\t{ec}\t{dur_ms}\t{extra}\n")
    sys.stdout.write(f"__SUMMARY__\t{total}\t{clean}\t{hit}\t{error}\t{tampered}\t{wall_ms}\n")

if __name__ == "__main__":
    main()
PYEOF

WORKER_OUT=$(REGISTRY="$REGISTRY" JOBS="$JOBS" python3 "$WORKER_PY")
WORKER_EC=$?

if [ "$WORKER_EC" != "0" ]; then
    echo "error: parallel worker failed (ec=$WORKER_EC)" >&2
    echo "  reason: python3 worker subprocess crashed" >&2
    echo "  fix:    re-run sequential tool/falsifier_health.sh; check python3 stderr" >&2
    exit 1
fi

# Parse worker output: per-entry rows + final __SUMMARY__ row
SUMMARY_LINE=$(printf '%s\n' "$WORKER_OUT" | grep '^__SUMMARY__' | tail -1)
TOTAL=$(printf '%s' "$SUMMARY_LINE" | awk -F'\t' '{print $2}')
CLEAN=$(printf '%s' "$SUMMARY_LINE" | awk -F'\t' '{print $3}')
HIT=$(printf '%s'   "$SUMMARY_LINE" | awk -F'\t' '{print $4}')
ERROR=$(printf '%s' "$SUMMARY_LINE" | awk -F'\t' '{print $5}')
TAMPERED=$(printf '%s' "$SUMMARY_LINE" | awk -F'\t' '{print $6}')
DURATION_MS=$(printf '%s' "$SUMMARY_LINE" | awk -F'\t' '{print $7}')

if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
    # Render per-entry rows in original FID order (numeric on F# prefix)
    printf '%s\n' "$WORKER_OUT" \
        | grep -v '^__SUMMARY__' \
        | awk -F'\t' '{n=$1; gsub(/[^0-9]/,"",n); printf "%06d\t%s\n", n+0, $0}' \
        | sort -n \
        | cut -f2- \
        | while IFS=$'\t' read -r FID SLUG STATUS EC DUR EXTRA; do
            if [ "$STATUS" = "TAMPERED" ]; then
                printf '  %-4s  %-50s  %-8s  reason=cmd_sha256_mismatch  fix=audit_registry_history  %s\n' \
                    "$FID" "$SLUG" "$STATUS" "$EXTRA"
            elif [ "$STATUS" = "SPOOF" ]; then
                printf '  %-4s  %-50s  %-8s  reason=anti_spoof_lint  fix=audit_cmd_origin\n' \
                    "$FID" "$SLUG" "$STATUS"
            elif [ "$STATUS" = "HIT" ] && [ "$EC" = "1" ]; then
                printf '  %-4s  %-50s  %-8s  ec=%-3s  %6sms  reason=anchor_grep_miss  fix=audit_atlas_for_drift\n' \
                    "$FID" "$SLUG" "$STATUS" "$EC" "$DUR"
            else
                printf '  %-4s  %-50s  %-8s  ec=%-3s  %6sms\n' \
                    "$FID" "$SLUG" "$STATUS" "$EC" "$DUR"
            fi
        done
fi

VERDICT="PASS"
EXIT_CODE=0
if [ "$ERROR" -gt 0 ] || [ "$HIT" -gt 0 ]; then
    VERDICT="FAIL"
    EXIT_CODE=76
fi

JSONL_LINE=$(printf '{"ts":"%s","scope":"falsifier_registry","total":%d,"clean":%d,"hit":%d,"error":%d,"tampered":%d,"duration_ms":%d,"checker":"falsifier_health_parallel.sh"}' \
    "$NOW" "$TOTAL" "$CLEAN" "$HIT" "$ERROR" "$TAMPERED" "$DURATION_MS")

if [ "$JSON" = "1" ]; then
    printf '%s\n' "$JSONL_LINE"
else
    printf '%s\n' "$JSONL_LINE" >> "$TIMELINE"
fi

if [ "$QUIET" = "0" ] && [ "$JSON" = "0" ]; then
    echo "─── summary"
    printf '  total=%d  clean=%d  hit=%d  error=%d  tampered=%d  wall=%dms\n' \
        "$TOTAL" "$CLEAN" "$HIT" "$ERROR" "$TAMPERED" "$DURATION_MS"
    if [ "$EXIT_CODE" = "76" ]; then
        echo "  reason: $HIT HIT + $ERROR ERROR ($TAMPERED TAMPERED) — see TSV above for per-id breakdown"
        echo "  fix:    re-run failing F# with verbose output; consult design/hexa_sim/falsifiers.jsonl 'fix' field"
    fi
fi

echo "__FALSIFIER_HEALTH__ $VERDICT total=$TOTAL clean=$CLEAN hit=$HIT error=$ERROR tampered=$TAMPERED duration_ms=$DURATION_MS"
exit $EXIT_CODE
