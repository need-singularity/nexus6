#!/bin/bash
# system-call wrapper
# safe_agent_patch_plists.sh — stamp jetsam-safe keys on airgenome agents
#
# Why: 2026-04-14 OOM — runaway heavy hexa jobs dragged load to 54 and
# memorystatus killed Terminal. macOS can't cap memory from userland,
# but launchd can tag these agents so jetsam picks them *before*
# FOREGROUND apps. Also drops I/O and CPU priority so they never
# contend with user's interactive work.
#
# Keys added:
#   ProcessType    = Background   (jetsam priority band, I/O scheduling)
#   LowPriorityIO  = true         (I/O tier 2)
#   Nice           = 19           (CPU scheduling)
#
# Idempotent: delete-then-add. Does not touch ProgramArguments.
# Caller responsible for launchctl bootout/bootstrap afterward.

set -eu

AGENTS=(dispatch probe predictive-throttle)
DIR="$HOME/Library/LaunchAgents"
PB=/usr/libexec/PlistBuddy

for a in "${AGENTS[@]}"; do
  P="$DIR/com.airgenome.${a}.plist"
  if [ ! -f "$P" ]; then
    echo "[skip] $a — no plist at $P"
    continue
  fi
  $PB -c "Delete :ProcessType" "$P" 2>/dev/null || true
  $PB -c "Add :ProcessType string Background" "$P"
  $PB -c "Delete :LowPriorityIO" "$P" 2>/dev/null || true
  $PB -c "Add :LowPriorityIO bool true" "$P"
  $PB -c "Delete :Nice" "$P" 2>/dev/null || true
  $PB -c "Add :Nice integer 19" "$P"
  echo "[patched] $a"
done
