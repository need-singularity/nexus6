#!/bin/bash
# system-call wrapper
# safe_hexa_launchd.sh — run hexa via launchd for REAL jetsam protection
#
# Why: 2026-04-14 verification — taskpolicy -b (safe_hexa.sh) only sets
# PRIO_DARWIN_BG (CPU/IO scheduling). It does NOT touch jetsam priority,
# which stays at 180 — same as Terminal. Under OOM, jetsam picks targets
# by jetsam_priority, so Terminal is just as likely to die.
#
# Launchd-managed processes with ProcessType=Background get jetsam
# priority 40 (BACKGROUND_OPPORTUNISTIC). Under memory pressure jetsam
# kills priority-40 long before priority-180 (Terminal/menubar). This
# is the only way to actually protect Terminal from runaway hexa.
#
# Use: safe_hexa_launchd.sh <hexa-args...>
# Env: HEXA_BIN  (default $HOME/Dev/hexa-lang/hexa)
#
# Tradeoff vs safe_hexa.sh:
#   + real jetsam protection (priority 40 vs 180)
#   - ~100ms launchd boot overhead
#   - no stdin (launchd has no controlling tty)
#   - exit code via launchctl print poll
# Use for long/heavy hexa jobs, not interactive REPL.

set -u

HEXA="${HEXA_BIN:-$HOME/Dev/hexa-lang/hexa}"
UID_N=$(id -u)
LABEL="user.safe_hexa.$$.$(date +%s)"
PLIST=$(mktemp -t safe_hexa.XXXXXX).plist
OUT=$(mktemp -t safe_hexa.out.XXXXXX)
ERR=$(mktemp -t safe_hexa.err.XXXXXX)
TAIL_OUT_PID=""
TAIL_ERR_PID=""

cleanup() {
  [ -n "$TAIL_OUT_PID" ] && kill "$TAIL_OUT_PID" 2>/dev/null || true
  [ -n "$TAIL_ERR_PID" ] && kill "$TAIL_ERR_PID" 2>/dev/null || true
  launchctl bootout gui/$UID_N/$LABEL 2>/dev/null || true
  rm -f "$PLIST" "$OUT" "$ERR"
}
trap cleanup EXIT INT TERM

xml_escape() {
  printf '%s' "$1" | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g'
}

ARGS_XML="    <string>$(xml_escape "$HEXA")</string>"
for a in "$@"; do
  ARGS_XML+=$'\n'"    <string>$(xml_escape "$a")</string>"
done

# Env allowlist: PATH/HOME/HEXA_NO_LAUNCHD (always) + any var whose name
# matches the hook/tooling prefixes below. Without this, launchd's explicit
# EnvironmentVariables dict drops everything not listed — observed 2026-04-21:
# airgenome hooks could not see HOOK_EVENT_JSON, AIRGENOME_HOOK_ROOT, etc.
ENV_XML="    <key>PATH</key><string>$(xml_escape "${PATH}")</string>
    <key>HOME</key><string>$(xml_escape "${HOME}")</string>
    <key>HEXA_NO_LAUNCHD</key><string>1</string>"
while IFS='=' read -r k v; do
  case "$k" in
    HEXA_NO_LAUNCHD|PATH|HOME) continue ;;
    HOOK_*|AIRGENOME_*|CLAUDE_*|HEXA_*|NEXUS_*)
      ENV_XML+="
    <key>$(xml_escape "$k")</key><string>$(xml_escape "$v")</string>"
      ;;
  esac
done < <(env)

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
${ARGS_XML}
  </array>
  <key>WorkingDirectory</key><string>$(pwd)</string>
  <key>ProcessType</key><string>Background</string>
  <key>LowPriorityIO</key><true/>
  <key>Nice</key><integer>19</integer>
  <key>RunAtLoad</key><true/>
  <!-- 2026-04-18 WindowServer panic 재발 방지: hexa_stage0 RSS 4GB 하드캡.
       Mac 16GB 중 12GB 를 WindowServer/Terminal/user 에 보장. 초과 시 jetsam
       이 해당 job(priority=40)부터 reclaim. -->
  <key>SoftResourceLimits</key>
  <dict>
    <key>ResidentSetSize</key><integer>4294967296</integer>
  </dict>
  <key>HardResourceLimits</key>
  <dict>
    <key>ResidentSetSize</key><integer>4294967296</integer>
  </dict>
  <key>StandardOutPath</key><string>${OUT}</string>
  <key>StandardErrorPath</key><string>${ERR}</string>
  <key>EnvironmentVariables</key>
  <dict>
${ENV_XML}
  </dict>
</dict>
</plist>
EOF

launchctl bootstrap gui/$UID_N "$PLIST"

# -s 0.1 : poll every 100ms so short-lived jobs (hook handlers, <1s) don't
# exit before the default 1s tail-poll cycle, which silently drops their
# stdout. Observed 2026-04-21 with airgenome hook dispatch — 137-byte JSON
# responses from user_prompt.hexa were lost because the child completed in
# <500ms and tail never polled.
tail -F -s 0.1 "$OUT" 2>/dev/null &
TAIL_OUT_PID=$!
tail -F -s 0.1 "$ERR" >&2 2>/dev/null &
TAIL_ERR_PID=$!

# Poll until job actually exits. We can't trust state== "running" because
# launchd reports "waiting"/"spawn scheduled" before fork; treating those
# as "done" would cleanup → bootout → kill the job before it ever ran.
# Authoritative signal: `last exit code` flips from "(never exited)" to a
# number, OR launchctl print returns nonzero (job was reaped).
#
# 2026-04-18 panic 재발 후 RSS watchdog 통합:
# macOS 15.6 커널이 setrlimit(RLIMIT_AS) 와 ulimit -v 모두 EINVAL 거부.
# launchd ResidentSetSize cap 은 best-effort — 단독 프로세스 폭주 시 enforcement 실패.
# → parent polling watchdog 이 유일한 hard cap 수단.
#
# RSS cap precedence (2026-04-21 B1):
#   NEXUS_RSS_CAP_MB    (MB, nexus-prefix, preferred)  >
#   HEXA_STAGE0_RSS_CAP_KB (KB, legacy alias, back-compat) >
#   default 4194304 KB (4GB)
if [ -n "${NEXUS_RSS_CAP_MB:-}" ]; then
  RSS_CAP_KB="$((NEXUS_RSS_CAP_MB * 1024))"
else
  RSS_CAP_KB="${HEXA_STAGE0_RSS_CAP_KB:-4194304}"
fi
# B2: 2-phase graceful drain — SIGTERM at warn_ratio, SIGKILL after grace_sec.
#   NEXUS_RSS_WARN_RATIO  (default 0.90) — ratio (0-1) of cap to trigger SIGTERM
#   NEXUS_RSS_GRACE_SEC   (default 5)    — seconds between SIGTERM and SIGKILL
# B3: child fanout advisory — warn when descendant count exceeds threshold.
#   NEXUS_MAX_CHILD       (default 16, 0=disabled) — descendant count threshold
RSS_WARN_RATIO="${NEXUS_RSS_WARN_RATIO:-0.90}"
RSS_GRACE_SEC="${NEXUS_RSS_GRACE_SEC:-5}"
MAX_CHILD="${NEXUS_MAX_CHILD:-16}"
# Compute warn threshold (KB) via awk — bash can't do float math.
RSS_WARN_KB="$(awk -v c="$RSS_CAP_KB" -v r="$RSS_WARN_RATIO" 'BEGIN{printf "%d", c*r}')"
SIGTERM_SENT=0
SIGTERM_TS=0
FANOUT_WARNED=0
EXIT_CODE=""

# pid_tree <root> — echo root pid + all descendants (DFS, ps-based). macOS 호환.
pid_tree() {
  local root="$1" frontier next pid parent
  frontier="$root"
  printf '%s\n' "$root"
  # Walk up to 8 generations to avoid runaway; stage0 child depth is usually ≤3.
  for _ in 1 2 3 4 5 6 7 8; do
    next=""
    # 1 pass over full ps table per generation (cheap: hundreds of rows).
    while IFS= read -r line; do
      pid=$(printf '%s' "$line" | awk '{print $1}')
      parent=$(printf '%s' "$line" | awk '{print $2}')
      case " $frontier " in
        *" $parent "*)
          printf '%s\n' "$pid"
          next="$next $pid" ;;
      esac
    done < <(ps -Ao pid=,ppid= 2>/dev/null)
    [ -z "$next" ] && break
    frontier="$next"
  done
}

# sum_rss_kb <pid...> — echo total RSS (KB) of given pids. Missing pids skipped.
sum_rss_kb() {
  local pids="$*"
  [ -z "$pids" ] && { echo 0; return; }
  # -p accepts comma-separated list; build it from space-separated input.
  local csv
  csv=$(printf '%s' "$pids" | tr ' \n' ',,' | sed 's/,,*/,/g; s/^,//; s/,$//')
  ps -o rss= -p "$csv" 2>/dev/null | awk '{s+=$1} END {print s+0}'
}

while true; do
  INFO=$(launchctl print gui/$UID_N/$LABEL 2>/dev/null)
  if [ $? -ne 0 ]; then break; fi
  # RSS watchdog — pid from launchctl print, RSS = job pid + all descendants.
  #
  # awk regex tolerance (2026-04-18 91306 incident post-mortem):
  #   launchctl print emits `\tpid = NNN` on its own line when state=running.
  #   Old regex `/^[[:space:]]*pid = /` only matched single-space after `=`; a
  #   future launchd reformat to `pid  =  NNN` or `pid=NNN` would silently drop
  #   watchdog. New regex: `/^[[:space:]]*pid[[:space:]]*=/` tolerates any
  #   whitespace around `=` and pulls first numeric field. Does NOT match
  #   `pid-local`/`pidfile`/`pid-forwarding` (char after `pid` must be space
  #   or `=`). sed fallback preserved for parity debugging.
  #
  # Descendant aggregation (2026-04-18 post-mortem):
  #   Even though ProgramArguments invokes hexa_stage0.real directly (not the
  #   shell shim), stage0.real itself shells out clang/flatten/cc during
  #   codegen. 91306 incident: JOB_PID's RSS was small (stage0 awaiting child)
  #   while descendant clang ate 13GB. ps rss of JOB_PID alone missed this.
  #   Fix: sum RSS across pid tree (pid + descendants via ppid walk).
  JOB_PID=$(printf '%s' "$INFO" | awk '/^[[:space:]]*pid[[:space:]]*=/ {for (i=1;i<=NF;i++) if ($i ~ /^[0-9]+$/) {print $i; exit}}')
  if [ -n "$JOB_PID" ] && [ "$JOB_PID" != "0" ]; then
    TREE=$(pid_tree "$JOB_PID" | tr '\n' ' ')
    RSS_KB=$(sum_rss_kb $TREE)
    # B3: fanout advisory — count descendants (excluding root JOB_PID) and warn once.
    if [ "$MAX_CHILD" != "0" ] && [ "$FANOUT_WARNED" = "0" ]; then
      _child_count=$(printf '%s\n' $TREE | grep -v "^${JOB_PID}$" 2>/dev/null | wc -l | tr -d ' ')
      if [ -n "$_child_count" ] && [ "$_child_count" -gt "$MAX_CHILD" ]; then
        printf 'NEXUS_FANOUT_WARN {"children":%s,"max":%s}\n' "$_child_count" "$MAX_CHILD" >&2
        FANOUT_WARNED=1
      fi
    fi
    if [ -n "$RSS_KB" ] && [ "$RSS_KB" -gt "$RSS_CAP_KB" ]; then
      # B2 phase 2: SIGKILL (either grace expired, or SIGTERM not-yet-sent but cap already blown).
      _grace_exceeded="false"
      if [ "$SIGTERM_SENT" = "1" ]; then
        _now=$(date +%s)
        _elapsed=$((_now - SIGTERM_TS))
        if [ "$_elapsed" -ge "$RSS_GRACE_SEC" ]; then
          _grace_exceeded="true"
        else
          # within grace window — keep polling; do NOT SIGKILL yet.
          sleep 0.5
          continue
        fi
      fi
      echo "safe_hexa_launchd: RSS watchdog — pid=$JOB_PID tree=[$TREE] rss=${RSS_KB}KB > cap=${RSS_CAP_KB}KB → SIGKILL" >&2
      printf 'NEXUS_RSS_KILL {"rss_kb":%s,"cap_kb":%s,"grace_exceeded":%s}\n' "$RSS_KB" "$RSS_CAP_KB" "$_grace_exceeded" >&2
      # Kill descendants first so stage0 sees children die, then kill stage0.
      for p in $TREE; do kill -KILL "$p" 2>/dev/null || true; done
      launchctl kill KILL "gui/$UID_N/$LABEL" 2>/dev/null || true
      EXIT_CODE=137  # SIGKILL canonical
      break
    elif [ -n "$RSS_KB" ] && [ "$RSS_KB" -gt "$RSS_WARN_KB" ] && [ "$SIGTERM_SENT" = "0" ]; then
      # B2 phase 1: SIGTERM at warn threshold, start grace countdown.
      echo "safe_hexa_launchd: RSS warn — pid=$JOB_PID rss=${RSS_KB}KB > warn=${RSS_WARN_KB}KB (cap=${RSS_CAP_KB}KB) → SIGTERM (grace ${RSS_GRACE_SEC}s)" >&2
      printf 'NEXUS_RSS_WARN {"rss_kb":%s,"cap_kb":%s,"action":"SIGTERM","grace_sec":%s}\n' "$RSS_KB" "$RSS_CAP_KB" "$RSS_GRACE_SEC" >&2
      for p in $TREE; do kill -TERM "$p" 2>/dev/null || true; done
      SIGTERM_SENT=1
      SIGTERM_TS=$(date +%s)
    fi
  fi
  EXIT_LINE=$(printf '%s' "$INFO" | awk -F'= ' '/last exit code/ {print $2; exit}')
  if [ -n "$EXIT_LINE" ] && [ "$EXIT_LINE" != "(never exited)" ]; then
    EXIT_CODE=$(printf '%s' "$EXIT_LINE" | tr -dc '0-9-')
    break
  fi
  sleep 0.5
done

# Give tails one full poll interval to flush then kill. tail -s 0.1 = 100ms poll.
sleep 0.3
[ -n "$TAIL_OUT_PID" ] && kill "$TAIL_OUT_PID" 2>/dev/null
[ -n "$TAIL_ERR_PID" ] && kill "$TAIL_ERR_PID" 2>/dev/null
TAIL_OUT_PID=""
TAIL_ERR_PID=""

# Defensive re-emit: if the child's entire lifecycle fit inside a single tail
# poll window, tail may have streamed zero bytes even after -s 0.1 + 0.3s
# flush sleep. We can't tell what tail emitted vs missed without an offset
# tracker, so we compare sizes: if tail appears to have missed everything
# (common for hook handlers returning ~100 bytes in <200ms), emit from file.
# The heuristic is a size threshold (<4096 bytes) — for larger outputs we
# accept tail as the streaming path and skip re-emit.
if [ -r "$OUT" ]; then
  OUT_SZ=$(wc -c <"$OUT" 2>/dev/null | tr -d ' ')
  if [ -n "$OUT_SZ" ] && [ "$OUT_SZ" -gt 0 ] && [ "$OUT_SZ" -lt 4096 ]; then
    cat "$OUT" 2>/dev/null || true
  fi
fi
if [ -r "$ERR" ]; then
  ERR_SZ=$(wc -c <"$ERR" 2>/dev/null | tr -d ' ')
  if [ -n "$ERR_SZ" ] && [ "$ERR_SZ" -gt 0 ] && [ "$ERR_SZ" -lt 4096 ]; then
    cat "$ERR" >&2 2>/dev/null || true
  fi
fi

exit "${EXIT_CODE:-0}"
