#!/usr/bin/env bash
# ubu1_sshd_selfheal.sh — local sshd liveness probe + auto-restart.
#
# deployed AT /usr/local/sbin/sshd_selfheal on ubu1, invoked by systemd timer every 60s.
# Defense against 2026-04-24 class failure (TCP accept OK, banner never sent).
#
# Logic:
#   1. Probe 127.0.0.1:22 — within 3s must receive "SSH-2.0-..." banner.
#   2. On failure, increment /run/sshd_selfheal.streak. At streak ≥ 2 (=2x60s=120s hang):
#        a. systemctl restart ssh (or sshd)
#        b. If still failing after restart, log escalation + reboot once per hour max.
#   3. On success, reset streak to 0.
#
# State files:
#   /run/sshd_selfheal.streak      — integer streak counter (tmpfs, resets on reboot)
#   /run/sshd_selfheal.last_reboot — epoch of last self-reboot (rate-limit 3600s)
#   /var/log/sshd_selfheal.log     — action log (rotated by logrotate/journal)
#
# Install:
#   sudo install -m 0755 ubu1_sshd_selfheal.sh /usr/local/sbin/sshd_selfheal
#   sudo install -m 0644 sshd-selfheal.service /etc/systemd/system/
#   sudo install -m 0644 sshd-selfheal.timer   /etc/systemd/system/
#   sudo systemctl daemon-reload
#   sudo systemctl enable --now sshd-selfheal.timer

set -u

STREAK_FILE=/run/sshd_selfheal.streak
REBOOT_TS_FILE=/run/sshd_selfheal.last_reboot
LOG=/var/log/sshd_selfheal.log
THRESHOLD=2          # consecutive failures before restart
REBOOT_AFTER=4       # consecutive failures AFTER restart attempt before reboot
REBOOT_COOLDOWN=3600 # seconds; never reboot more than once per hour

mkdir -p "$(dirname "$LOG")"
now() { date -u +%FT%TZ; }
log() { echo "$(now) $*" >> "$LOG"; }

probe() {
    # /dev/tcp is bash builtin — no extra deps. Banner must start with "SSH-".
    timeout 3 bash -c '
        exec 3<>/dev/tcp/127.0.0.1/22 2>/dev/null || exit 1
        read -t 2 banner <&3 2>/dev/null
        [[ "${banner:-}" == SSH-* ]]
    '
}

read_int() {
    [[ -f "$1" ]] && cat "$1" 2>/dev/null | tr -dc 0-9 || echo 0
}

if probe; then
    # healthy
    prev=$(read_int "$STREAK_FILE")
    if [[ "$prev" -gt 0 ]]; then
        log "recovered from streak=$prev"
    fi
    echo 0 > "$STREAK_FILE"
    exit 0
fi

# unhealthy
streak=$(read_int "$STREAK_FILE")
streak=$((streak + 1))
echo "$streak" > "$STREAK_FILE"
log "probe FAIL streak=$streak"

if [[ "$streak" -lt "$THRESHOLD" ]]; then
    exit 0
fi

# at or beyond threshold — try service restart first
if [[ "$streak" -eq "$THRESHOLD" ]]; then
    log "threshold=$THRESHOLD hit — systemctl restart ssh"
    if systemctl restart ssh 2>>"$LOG"; then
        log "  restart OK"
    elif systemctl restart sshd 2>>"$LOG"; then
        log "  restart sshd OK (ssh unit missing)"
    else
        log "  restart FAILED — both ssh.service and sshd.service"
    fi
    # give sshd 3s to come up; next tick will re-probe
    sleep 3
    exit 0
fi

# streak > THRESHOLD — restart didn't fix it
if [[ "$streak" -lt "$REBOOT_AFTER" ]]; then
    log "post-restart streak=$streak, waiting more (reboot threshold=$REBOOT_AFTER)"
    exit 0
fi

# escalation: consider reboot
last_reboot=$(read_int "$REBOOT_TS_FILE")
now_epoch=$(date +%s)
age=$((now_epoch - last_reboot))
if [[ "$age" -lt "$REBOOT_COOLDOWN" ]]; then
    log "escalation blocked — last self-reboot was ${age}s ago (cooldown=${REBOOT_COOLDOWN}s)"
    exit 0
fi

log "ESCALATION: streak=$streak, restart did not recover — initiating rebooted"
echo "$now_epoch" > "$REBOOT_TS_FILE"
# Use systemctl reboot -i to bypass "logged-in users block" only if needed.
systemctl reboot 2>>"$LOG" || shutdown -r +1 "sshd selfheal escalation" 2>>"$LOG"
exit 0
