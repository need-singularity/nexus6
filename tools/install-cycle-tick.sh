#!/usr/bin/env bash
# Install/uninstall/status for com.nexus6.cycle-tick LaunchAgent.
set -euo pipefail

LABEL="com.nexus6.cycle-tick"
SRC_PLIST="$(cd "$(dirname "$0")/.." && pwd)/launchd/${LABEL}.plist"
DST_PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
UID_SELF="$(id -u)"

case "${1:-status}" in
  install)
    mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs/nexus6"
    cp "$SRC_PLIST" "$DST_PLIST"
    launchctl bootstrap "gui/${UID_SELF}" "$DST_PLIST" 2>/dev/null || \
      launchctl load -w "$DST_PLIST"
    echo "installed: ${LABEL}"
    ;;
  uninstall)
    launchctl bootout "gui/${UID_SELF}/${LABEL}" 2>/dev/null || \
      launchctl unload -w "$DST_PLIST" 2>/dev/null || true
    rm -f "$DST_PLIST"
    echo "uninstalled: ${LABEL}"
    ;;
  halt)
    mkdir -p "$(pwd)/shared/cycle" && touch "$(pwd)/shared/cycle/halt"
    echo "halt flag set"
    ;;
  resume)
    rm -f "$(pwd)/shared/cycle/halt"
    echo "halt flag cleared"
    ;;
  status)
    launchctl list | grep "${LABEL}" || echo "not loaded"
    ;;
  *)
    echo "usage: $0 {install|uninstall|halt|resume|status}" >&2
    exit 1
    ;;
esac
