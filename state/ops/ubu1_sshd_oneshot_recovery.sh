#!/usr/bin/env bash
# ubu1 sshd one-shot recovery — physical/IPMI console only.
#
# 전제: sudo -i 또는 root 쉘. Ubuntu (systemd).
# 사용:  bash ubu1_sshd_oneshot_recovery.sh
#   또는 curl https://<repo>/state/ops/ubu1_sshd_oneshot_recovery.sh | sudo bash
#
# 흐름: 진단 → 빠른복구 → 재검증 → (실패시) 깊은진단. 한 단계에서 success 떨어지면 즉시 종료.
# 모든 출력은 /tmp/ubu1_sshd_recovery.<ts>.log 로 동시 기록.

set -u
TS=$(date +%Y%m%dT%H%M%SZ)
LOG=/tmp/ubu1_sshd_recovery.${TS}.log
exec > >(tee -a "$LOG") 2>&1
echo "### ubu1 sshd oneshot recovery  log=$LOG  host=$(hostname)  started=$(date -u +%FT%TZ)"

step() { echo; echo "━━━ $* ━━━"; }
ok()   { echo "[OK]   $*"; }
warn() { echo "[WARN] $*"; }
fail() { echo "[FAIL] $*"; }

verify_sshd() {
    # 간단 localhost 검증: :22 accept + banner 송신 within 3s.
    # nc 대신 exec 3<>/dev/tcp 를 써서 외부 의존 제거.
    if timeout 3 bash -c 'exec 3<>/dev/tcp/127.0.0.1/22; read -t 2 banner <&3; [[ -n "${banner:-}" ]] && echo "$banner"' 2>/dev/null | grep -q '^SSH-'; then
        return 0
    fi
    return 1
}

# ─────────────────────────────────────────────────────────────
step "Stage 1 — 진단 스냅샷"
echo "## systemctl status ssh/sshd/ssh.socket"
systemctl --no-pager status ssh sshd ssh.socket 2>&1 | head -40 || true
echo
echo "## listening :22 / :2222"
ss -ltnp 2>/dev/null | grep -E ':22(22)?\b' || warn "no listener on :22 or :2222"
echo
echo "## recent ssh journal"
journalctl -u ssh -u sshd -u ssh.socket -n 40 --no-pager 2>&1 | tail -40 || true
echo
echo "## disk"
df -h / /var /run /tmp 2>&1
echo
echo "## uptime / load"
uptime
echo
echo "## tcp connection state from self (loopback)"
if verify_sshd; then
    ok "local :22 banner emit — SSH already healthy, exiting without changes"
    echo "final log: $LOG"
    exit 0
fi
warn "local :22 banner NOT received — proceeding to Stage 2"

# ─────────────────────────────────────────────────────────────
step "Stage 2 — 빠른 복구"

echo "## kill any stuck sshd"
pkill -9 sshd 2>/dev/null && ok "SIGKILL sent" || echo "no sshd pids to kill"
sleep 2
echo
echo "## stop ssh socket + service"
systemctl stop ssh.socket ssh.service sshd.service 2>/dev/null || true
echo
echo "## recreate /run/sshd"
mkdir -p /run/sshd
chmod 0755 /run/sshd
ok "/run/sshd ready"
echo
echo "## sshd -t (config syntax)"
if sshd -t 2>&1; then
    ok "config OK"
else
    fail "sshd config has errors — inspect /etc/ssh/sshd_config"
    echo "## recent /etc/ssh changes"
    ls -lt /etc/ssh/ | head -10
    echo "  → rollback manually and re-run this script"
    exit 2
fi
echo
echo "## reset-failed + start"
systemctl reset-failed ssh ssh.socket sshd 2>/dev/null || true
if systemctl start ssh.service 2>&1; then
    ok "ssh.service started"
else
    fail "systemctl start failed — trying sshd.service"
    systemctl start sshd.service 2>&1 || fail "both ssh.service and sshd.service failed"
fi
sleep 2
echo
echo "## post-restart status"
systemctl --no-pager status ssh --no-pager 2>&1 | head -15
echo
ss -ltnp 2>/dev/null | grep -E ':22\b' || warn "still no listener on :22"

# ─────────────────────────────────────────────────────────────
step "Verify — banner probe"
if verify_sshd; then
    ok "sshd banner emit OK — recovery succeeded"
    echo
    echo "## from Mac try:  ssh ubu1 hostname"
    echo "## log archive:   $LOG"
    exit 0
fi
fail "still no banner after restart — proceeding to Stage 3 (deep diag)"

# ─────────────────────────────────────────────────────────────
step "Stage 3 — 깊은 진단"

echo "## kernel log (OOM / fs errors)"
dmesg -T 2>/dev/null | tail -30 || journalctl -k --no-pager | tail -30
echo
echo "## fd pressure"
cat /proc/sys/fs/file-nr
echo
echo "## AppArmor on sshd"
aa-status 2>/dev/null | grep -i ssh || echo "no apparmor or no ssh profile"
echo
echo "## openssh-server pkg"
dpkg -l openssh-server 2>/dev/null | tail -3
echo
echo "## UseDNS / UsePAM"
grep -E '^UseDNS|^UsePAM' /etc/ssh/sshd_config || echo "both default (likely UseDNS yes + UsePAM yes)"
echo
echo "## systemd-resolved"
systemctl is-active systemd-resolved
echo
echo "## /var/log/journal size"
du -sh /var/log/journal/ 2>/dev/null
echo
echo "## last 10 reboots"
last -x reboot 2>/dev/null | head -10

# ─────────────────────────────────────────────────────────────
step "Stage 4 — 수동 경로 (참고)"
cat <<'EOF'
  # config rollback 가능성 확인:
  ls -lt /etc/ssh/ | head -10

  # AppArmor complain 모드 (profile 이 강제면):
  sudo aa-complain /usr/sbin/sshd
  sudo systemctl restart ssh

  # /var 디스크 100% 인 경우:
  journalctl --vacuum-size=200M
  apt-get clean

  # 디버그 sshd 대체 포트:
  /usr/sbin/sshd -ddd -p 2223 -o PidFile=/run/sshd-debug.pid 2>&1 | tee /tmp/sshd-debug.log
  # Mac: ssh -v -p 2223 aiden@192.168.50.119
  # debug log 의 'banner send' 직전 라인이 실제 hang point.
EOF

echo
fail "자동 복구 실패 — Stage 3 진단 결과를 보고 Stage 4 수동 조치 필요"
echo "final log: $LOG"
exit 3
