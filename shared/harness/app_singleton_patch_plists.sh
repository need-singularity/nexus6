#!/usr/bin/env bash
# @hexa-first-exempt — plist mass-patch for type=app single-instance enforcement
# app_singleton_patch_plists.sh — ~/Library/LaunchAgents/com.<name>.*.plist 의
# ProgramArguments[0] 가 <dest>/Contents/MacOS/* 로 시작하면 single-instance wrapper 호출로 변경.
#
# 책임:
#   - 글로빙 com.<name>.*.plist 모두 검사
#   - binary 직접 호출(plist[0] == .app/Contents/MacOS/...) 만 patch
#   - hexa run / sh / jq 등 다른 명령은 건드리지 않음
#   - 이미 wrapper 호출이면 skip (idempotent)
#   - lock_name = plist Label (unique 보장)
#
# 사용:
#   app_singleton_patch_plists.sh <project_name> <dest_app_path>
#   app_singleton_patch_plists.sh airgenome /Applications/Airgenome.app

set -u
NAME="${1:-}"
DEST="${2:-}"
[ -z "$NAME" ] || [ -z "$DEST" ] && {
    echo "usage: $0 <project_name> <dest_app_path>" >&2
    exit 2
}

WRAPPER="${NEXUS:-$HOME/Dev/nexus}/shared/harness/app_singleton_launch.sh"
[ -x "$WRAPPER" ] || {
    echo "fatal: wrapper not executable: $WRAPPER" >&2
    exit 2
}

MACOS_PREFIX="$DEST/Contents/MacOS/"
patched=0
skipped=0
for plist in "$HOME/Library/LaunchAgents/com.${NAME}."*.plist; do
    [ -f "$plist" ] || continue
    prog0=$(plutil -extract ProgramArguments.0 raw -o - "$plist" 2>/dev/null || echo "")
    case "$prog0" in
        "$MACOS_PREFIX"*)
            label=$(plutil -extract Label raw -o - "$plist" 2>/dev/null)
            if [ -z "$label" ]; then
                echo "[skip] $plist — Label 추출 실패" >&2
                continue
            fi
            plutil -replace ProgramArguments -json "[\"$WRAPPER\", \"$label\", \"$prog0\"]" "$plist"
            echo "[patched] $(basename "$plist") — lock=$label bin=$prog0"
            patched=$((patched + 1))
            ;;
        "$WRAPPER")
            # 이미 patch 됨 — idempotent skip
            skipped=$((skipped + 1))
            ;;
        *)
            # 다른 명령 (jq, sh, hexa run 등) — 건드리지 않음
            ;;
    esac
done
echo "[summary] patched=$patched already-patched=$skipped"
