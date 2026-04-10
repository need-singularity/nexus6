#!/usr/bin/env bash
# nexus — hx entry point & Mac auto-start installer
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$(readlink "$0" 2>/dev/null || echo "$0")")" && pwd)"
export HOME="${HOME:-$(eval "printenv HOME")}"
export NEXUS_ROOT="${SCRIPT_DIR}"
export PATH="$HOME/.cargo/bin:$HOME/.hx/bin:/usr/local/bin:/usr/bin:/bin"

HEXA="$HOME/Dev/hexa-lang/target/release/hexa"
GUARD_BIN="$HOME/.cargo/bin/n6_guard"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST="$PLIST_DIR/com.nexus.guard.plist"
LOG_DIR="$HOME/Library/Logs/nexus"

red()   { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
dim()   { printf '\033[2m%s\033[0m\n' "$*"; }

cmd_install() {
  green "⬡ nexus install — Mac 자동 시작 설정"
  mkdir -p "$LOG_DIR" "$PLIST_DIR"

  # 1) n6-guard 바이너리 확인
  if [ ! -f "$GUARD_BIN" ]; then
    red "n6_guard 바이너리 없음: $GUARD_BIN"
    dim "  cargo install --path ~/Dev/nexus/guard 또는 수동 복사 필요"
    exit 1
  fi

  # 2) LaunchAgent plist 생성/갱신
  cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nexus.guard</string>

    <key>ProgramArguments</key>
    <array>
        <string>${GUARD_BIN}</string>
        <string>--fg</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>${HOME}/.config/n6-guard-stdout.log</string>

    <key>StandardErrorPath</key>
    <string>${HOME}/.config/n6-guard-stderr.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>HOME</key>
        <string>${HOME}</string>
        <key>PATH</key>
        <string>${HOME}/.cargo/bin:${HOME}/.hx/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>

    <key>ProcessType</key>
    <string>Background</string>

    <key>LowPriorityBackgroundIO</key>
    <true/>
</dict>
</plist>
PLIST

  # 3) LaunchAgent 등록
  local uid
  uid=$(id -u)
  launchctl bootout "gui/$uid/com.nexus.guard" 2>/dev/null || true
  launchctl bootstrap "gui/$uid" "$PLIST"
  green "⬡ LaunchAgent 등록 완료 (RunAtLoad=true)"

  # 4) 상태 확인
  if launchctl print "gui/$uid/com.nexus.guard" >/dev/null 2>&1; then
    green "⬡ n6-guard 실행 중 — Mac 시작 시 자동 기동"
  else
    red "LaunchAgent 등록됐으나 실행 확인 실패 — 로그 확인:"
    dim "  tail -f $HOME/.config/n6-guard-stderr.log"
  fi

  dim ""
  dim "  nexus status   — 상태 확인"
  dim "  nexus start    — 수동 시작"
  dim "  nexus stop     — 정지"
}

cmd_start() {
  local uid; uid=$(id -u)
  if launchctl bootstrap "gui/$uid" "$PLIST" 2>/dev/null; then
    green "⬡ nexus guard 시작"
  else
    dim "이미 실행 중이거나 bootstrap 실패 — status 확인"
    launchctl kickstart -k "gui/$uid/com.nexus.guard" 2>/dev/null && green "⬡ 재시작됨" || red "시작 실패"
  fi
}

cmd_stop() {
  local uid; uid=$(id -u)
  launchctl bootout "gui/$uid/com.nexus.guard" 2>/dev/null && green "⬡ nexus guard 정지" || dim "이미 정지 상태"
}

cmd_status() {
  local uid; uid=$(id -u)
  green "⬡ nexus 상태"
  echo ""
  if launchctl print "gui/$uid/com.nexus.guard" 2>/dev/null | head -5; then
    echo ""
    green "  guard: 실행 중"
  else
    dim "  guard: 정지"
  fi

  # n6-guard 프로세스 확인
  if pgrep -f n6_guard >/dev/null 2>&1; then
    dim "  PID: $(pgrep -f n6_guard | head -1)"
  fi
}

cmd_blowup() {
  shift 2>/dev/null || true
  local seeds
  seeds=$("$HEXA" "$NEXUS_ROOT/mk2_hexa/native/seed_engine.hexa" merge 2>/dev/null || echo "")
  exec "$HEXA" "$NEXUS_ROOT/mk2_hexa/native/blowup.hexa" math "${1:-3}" --no-graph --seeds "$seeds"
}

cmd_directions() {
  exec "$HEXA" "$NEXUS_ROOT/mk2_hexa/native/directions.hexa" "${1:-brief}"
}

usage() {
  echo "nexus — the perfect number engine"
  echo ""
  echo "  nexus install      Mac 자동 시작 설정 (LaunchAgent)"
  echo "  nexus start        수동 시작"
  echo "  nexus stop         정지"
  echo "  nexus status       상태 확인"
  echo "  nexus blowup [N]   블로업 실행"
  echo "  nexus directions   방향 리포트"
  echo ""
}

case "${1:-}" in
  install)    cmd_install ;;
  start)      cmd_start ;;
  stop)       cmd_stop ;;
  status)     cmd_status ;;
  blowup)     shift; cmd_blowup "$@" ;;
  directions) shift; cmd_directions "$@" ;;
  -h|--help)  usage ;;
  *)          usage ;;
esac
