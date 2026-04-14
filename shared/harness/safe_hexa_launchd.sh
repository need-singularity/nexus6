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
EXIT_CODE=""
while true; do
  INFO=$(launchctl print gui/$UID_N/$LABEL 2>/dev/null)
  if [ $? -ne 0 ]; then break; fi
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
