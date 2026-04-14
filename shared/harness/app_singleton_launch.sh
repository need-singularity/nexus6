#!/usr/bin/env bash
# @hexa-first-exempt — single-instance gate for type=app launchd ProgramArguments
# app_singleton_launch.sh — type=app 프로젝트 단일 실행 강제
#
# 책임:
#   - mkdir-atomic lock 으로 race window 차단
#   - 같은 binary 이미 살아있으면 silent exit 0 (launchd ThrottleInterval 로 backoff)
#   - lock 의 PID 가 죽었으면 stale 처리 후 lock 가져가 exec
#   - exec 로 wrapper PID 가 그대로 binary PID 차지 → kill -0 검사가 binary 생사를 직접 봄
#
# 사용 (launchd plist ProgramArguments):
#   <string>$HOME/Dev/nexus/shared/harness/app_singleton_launch.sh</string> // @allow-devpath (plist 문서 예시)
#   <string><lock_name></string>
#   <string><binary_absolute_path></string>

set -u
NAME="${1:-}"
BIN="${2:-}"
[ -z "$NAME" ] || [ -z "$BIN" ] && {
    echo "usage: $0 <name> <binary>" >&2
    exit 2
}
[ -x "$BIN" ] || {
    echo "fatal: not executable: $BIN" >&2
    exit 2
}

LOCK_DIR="/tmp/app_singleton_${NAME}.lock"

# 1차 — atomic mkdir 시도
if mkdir "$LOCK_DIR" 2>/dev/null; then
    echo $$ > "$LOCK_DIR/pid"
    exec "$BIN"
fi

# 2차 — 기존 lock 검사 (race window: pid 파일이 아직 안 써졌으면 0.2s 대기)
oldpid=$(cat "$LOCK_DIR/pid" 2>/dev/null)
if [ -z "$oldpid" ]; then
    sleep 0.2
    oldpid=$(cat "$LOCK_DIR/pid" 2>/dev/null)
fi
if [ -n "$oldpid" ] && kill -0 "$oldpid" 2>/dev/null; then
    # 이미 살아있음 — silent exit (launchd ThrottleInterval 후 재시도)
    exit 0
fi

# stale — 정리 후 한 번 더 시도
rm -rf "$LOCK_DIR"
if mkdir "$LOCK_DIR" 2>/dev/null; then
    echo $$ > "$LOCK_DIR/pid"
    exec "$BIN"
fi
# 그 사이 다른 wrapper 가 가져갔으면 silent exit
exit 0
