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
    <key>PATH</key><string>${PATH}</string>
    <key>HOME</key><string>${HOME}</string>
    <key>HEXA_NO_LAUNCHD</key><string>1</string>
  </dict>
</dict>
</plist>
EOF

launchctl bootstrap gui/$UID_N "$PLIST"

tail -F "$OUT" 2>/dev/null &
TAIL_OUT_PID=$!
tail -F "$ERR" >&2 2>/dev/null &
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
# HEXA_STAGE0_RSS_CAP_KB 로 override (default 4GB=4194304 KB).
RSS_CAP_KB="${HEXA_STAGE0_RSS_CAP_KB:-4194304}"
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
    if [ -n "$RSS_KB" ] && [ "$RSS_KB" -gt "$RSS_CAP_KB" ]; then
      echo "safe_hexa_launchd: RSS watchdog — pid=$JOB_PID tree=[$TREE] rss=${RSS_KB}KB > cap=${RSS_CAP_KB}KB → SIGKILL" >&2
      # Kill descendants first so stage0 sees children die, then kill stage0.
      for p in $TREE; do kill -KILL "$p" 2>/dev/null || true; done
      launchctl kill KILL "gui/$UID_N/$LABEL" 2>/dev/null || true
      EXIT_CODE=137  # SIGKILL canonical
      break
    fi
  fi
  EXIT_LINE=$(printf '%s' "$INFO" | awk -F'= ' '/last exit code/ {print $2; exit}')
  if [ -n "$EXIT_LINE" ] && [ "$EXIT_LINE" != "(never exited)" ]; then
    EXIT_CODE=$(printf '%s' "$EXIT_LINE" | tr -dc '0-9-')
    break
  fi
  sleep 0.5
done

# flush tail buffers, then emit any tail-missed bytes from the files
sleep 0.3
[ -n "$TAIL_OUT_PID" ] && kill "$TAIL_OUT_PID" 2>/dev/null
[ -n "$TAIL_ERR_PID" ] && kill "$TAIL_ERR_PID" 2>/dev/null
TAIL_OUT_PID=""
TAIL_ERR_PID=""

exit "${EXIT_CODE:-0}"
