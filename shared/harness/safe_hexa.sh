#!/bin/bash
# system-call wrapper
# safe_hexa.sh — hexa runner with jetsam-first kill priority
#
# Why: 2026-04-14 OOM incident — hexa_stage0 8.97GB RSS + load 54 →
# memorystatus jetsam killed Terminal. macOS RLIMIT_DATA via ulimit is
# not enforceable from userland ("Invalid argument"), so we can't cap
# memory directly. Instead we tag the process BACKGROUND QoS so jetsam
# targets it *before* FOREGROUND (Terminal/menubar). Memory can still
# balloon, but Terminal survives — which is the actual goal.
#
# Use: safe_hexa.sh <hexa-args...>     # pass-through to hexa
# Env: SAFE_HEXA_NICE  (default 19)
#      SAFE_HEXA_BG    (default 1; 0 skips taskpolicy)
#      HEXA_BIN        (default $HOME/Dev/hexa-lang/hexa)

set -u

NICE_N="${SAFE_HEXA_NICE:-19}"
USE_BG="${SAFE_HEXA_BG:-1}"
HEXA="${HEXA_BIN:-$HOME/Dev/hexa-lang/hexa}"
TASKPOLICY=/usr/sbin/taskpolicy

if [ "$USE_BG" = "1" ] && [ -x "$TASKPOLICY" ]; then
  exec "$TASKPOLICY" -b -t 2 -l 2 /usr/bin/nice -n "$NICE_N" "$HEXA" "$@"
else
  exec /usr/bin/nice -n "$NICE_N" "$HEXA" "$@"
fi
