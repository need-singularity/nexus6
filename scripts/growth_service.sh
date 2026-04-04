#!/usr/bin/env bash
# NEXUS-6 Growth Service Controller
# Usage: ./scripts/growth_service.sh [start|stop|status|logs]

PLIST="$HOME/Library/LaunchAgents/com.nexus6.growth.plist"
LABEL="com.nexus6.growth"
LOG_FILE="$HOME/Library/Logs/nexus6/growth.log"

case "${1:-}" in
  start)
    echo "[NEXUS-6] Loading growth service..."
    launchctl load "$PLIST" 2>&1
    echo "[NEXUS-6] Service loaded. Runs every 30 minutes."
    launchctl list | grep "$LABEL" && echo "[NEXUS-6] Confirmed running." || echo "[NEXUS-6] Warning: not found in launchctl list."
    ;;
  stop)
    echo "[NEXUS-6] Unloading growth service..."
    launchctl unload "$PLIST" 2>&1
    echo "[NEXUS-6] Service stopped."
    ;;
  status)
    echo "[NEXUS-6] Service status:"
    if launchctl list | grep -q "$LABEL"; then
      launchctl list | grep "$LABEL"
      echo "[NEXUS-6] Status: ACTIVE"
    else
      echo "[NEXUS-6] Status: INACTIVE"
    fi
    if [ -f "$LOG_FILE" ]; then
      echo ""
      echo "[NEXUS-6] Last 5 log lines:"
      tail -5 "$LOG_FILE"
    fi
    ;;
  logs)
    if [ -f "$LOG_FILE" ]; then
      tail -f "$LOG_FILE"
    else
      echo "[NEXUS-6] No log file found at $LOG_FILE"
    fi
    ;;
  *)
    echo "Usage: $0 [start|stop|status|logs]"
    echo ""
    echo "  start   - Load LaunchAgent (runs every 30 min)"
    echo "  stop    - Unload LaunchAgent"
    echo "  status  - Show service status + recent logs"
    echo "  logs    - Tail log file"
    exit 1
    ;;
esac
