#!/usr/bin/env bash
# NEXUS-6 Autonomous Daemon Controller
# Usage: ./scripts/growth_service.sh [start|stop|status|logs]

PLIST="$HOME/Library/LaunchAgents/com.n6.sync.nexus.plist"
LABEL="com.n6.sync.nexus"
LOG_FILE="$HOME/Library/Logs/nexus/daemon.log"
STATUS_FILE="$HOME/.nexus/daemon_status.txt"

case "${1:-status}" in
  start)
    echo "🤖 NEXUS-6 Daemon 시작..."
    launchctl load "$PLIST" 2>/dev/null
    if launchctl list | grep -q "$LABEL"; then
      echo "✅ Daemon 실행 중"
    else
      echo "⚠️ 로드 실패 — plist 확인 필요"
    fi
    ;;
  stop)
    echo "🛑 NEXUS-6 Daemon 중지..."
    launchctl unload "$PLIST" 2>/dev/null
    echo "   중지 완료"
    ;;
  status)
    if launchctl list | grep -q "$LABEL"; then
      echo "✅ Daemon 실행 중"
      launchctl list | grep "$LABEL"
    else
      echo "⏸️  Daemon 중지됨"
    fi
    echo ""
    if [ -f "$STATUS_FILE" ]; then
      echo "📊 마지막 상태:"
      cat "$STATUS_FILE"
    fi
    echo ""
    if [ -f "$HOME/.nexus/last_loop_report.txt" ]; then
      echo "📋 마지막 루프 리포트:"
      cat "$HOME/.nexus/last_loop_report.txt"
    fi
    ;;
  logs)
    if [ -f "$LOG_FILE" ]; then
      tail -f "$LOG_FILE"
    else
      echo "로그 없음: $LOG_FILE"
    fi
    ;;
  *)
    echo "Usage: $0 [start|stop|status|logs]"
    echo ""
    echo "  start   - 자율 데몬 시작 (30분 간격 루프)"
    echo "  stop    - 데몬 중지"
    echo "  status  - 상태 + 마지막 리포트"
    echo "  logs    - 실시간 로그"
    exit 1
    ;;
esac
