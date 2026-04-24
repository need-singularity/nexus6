# ubu1 sshd banner-timeout recovery runbook
Date filed: 2026-04-24 (updated 2026-04-24T14:20Z with automation)
Host: ubu1 (192.168.50.119, 32GB, Ubuntu)
Symptom: TCP :22/:2222 accept OK, L7 banner-exchange timeout. Reboot 무효.

## Automation assets (this directory)
- `ubu1_sshd_oneshot_recovery.sh` — Stage 1+2+3 자동화 스크립트. 물리/IPMI 콘솔에서 `sudo bash ubu1_sshd_oneshot_recovery.sh`.
- `ubu1_sshd_selfheal.sh` + `sshd-selfheal.service` + `sshd-selfheal.timer` — **복구 후 설치** 자가치유 watchdog (60초 probe, 120초 hang 시 restart, 4분 hang + 재시작 실패 시 reboot, 1시간 쿨다운). 재발 방지.

## Access method
물리 키보드+모니터 또는 IPMI/BMC web console 로 로컬 로그인 (SSH 불가). 모든 명령은 `sudo -i` 또는 root 쉘에서 실행.

## TL;DR (복구 순서)
1. 물리 콘솔 로그인 → `sudo bash /path/to/ubu1_sshd_oneshot_recovery.sh` (USB 또는 git clone)
2. 스크립트가 stage 1→2→verify→3 까지 자동 진행. 성공 시 exit 0.
3. SSH 복구 확인 후 Mac 에서 `scp ubu1_sshd_selfheal.sh sshd-selfheal.{service,timer} ubu1:/tmp/` → ubu1 에서 install 블록 실행.
4. `sudo systemctl enable --now sshd-selfheal.timer` → 재발 자동 복구.

## Stage 1 — 즉시 진단 (5분)
```
systemctl status ssh sshd ssh.socket 2>&1 | head -40
ss -ltnp | grep -E ':22(22)?\b'
journalctl -u ssh -u ssh.socket -n 80 --no-pager
df -h / /var /run /tmp
```
분기:
- `active (listening)` 인데 journal 에 `Accepted` 없음 → Stage 2.
- `ssh.service: start request repeated too quickly` / `failed` → Stage 2 (full restart).
- `/var` 또는 `/` 100% 사용 → Stage 3 disk 먼저.
- socket 만 active, service inactive → Stage 2 socket reset.

## Stage 2 — 빠른 복구 시도 (10분)
```
pkill -9 sshd; sleep 2
systemctl stop ssh.socket ssh.service 2>/dev/null
mkdir -p /run/sshd && chmod 0755 /run/sshd
sshd -t                          # config 문법 체크, expected: 출력 없음 (rc=0)
systemctl reset-failed ssh ssh.socket
systemctl start ssh.service
systemctl status ssh --no-pager | head -20
ss -ltnp | grep -E ':22\b'
```
분기:
- `sshd -t` 가 에러 출력 → 최근 `/etc/ssh/sshd_config` 변경 rollback (`ls -lt /etc/ssh/`).
- service active 이고 `ss` 에 sshd LISTEN 보임 → Mac 에서 `ssh ubu1 hostname` 테스트. 성공 시 종료.
- 여전히 banner timeout → Stage 3.

## Stage 3 — 깊은 진단
```
dmesg -T | tail -60                                   # OOM, kernel taint, fs error
journalctl -k -b -1 --no-pager | tail -80             # 직전 부팅 kernel log
lsof -n 2>/dev/null | wc -l                           # fd 고갈 여부 (>100k 의심)
cat /proc/sys/fs/file-nr
aa-status 2>/dev/null | grep -i ssh                   # AppArmor profile 상태
dpkg -l openssh-server | tail -3                      # 패키지 무결성
systemctl is-active systemd-resolved
grep -E '^UseDNS|^UsePAM' /etc/ssh/sshd_config
ls -la /var/log/ | head; du -sh /var/log/journal/
```
관찰 포인트:
- dmesg 에 `Out of memory` / `EXT4-fs error` → Stage 4 로 격리 디버그 필수.
- AppArmor `/usr/sbin/sshd` profile complain/disabled 이외면 `aa-complain /usr/sbin/sshd`.
- `UseDNS yes` + `systemd-resolved inactive` → `/etc/ssh/sshd_config` 에 `UseDNS no` 추가 후 Stage 2 재실행.
- `/var/log/journal` 수 GB → `journalctl --vacuum-size=200M`.

## Stage 4 — 회피 (그래도 안 되면)
로컬 콘솔에서 debug sshd 를 대체 포트 2223 으로 foreground 기동:
```
/usr/sbin/sshd -ddd -p 2223 -o PidFile=/run/sshd-debug.pid 2>&1 | tee /tmp/sshd-debug.log
```
Mac 에서 `ssh -v -p 2223 aiden@192.168.50.119` 로 접속 시도. debug log 의 banner send 직전 마지막 라인이 실제 hang point. 확인 후 Ctrl-C 로 debug sshd 종료.

## 복구 후 검증
Mac 에서:
```
ssh ubu1 'hostname; free -m | head -2; systemctl is-active ssh'
```
expected rc=0, `active` 출력.

## 복구 후 nexus 측 조치
필수 (재발 방지):
```
# 1. Mac → ubu1 로 자가치유 패키지 전송
scp state/ops/ubu1_sshd_selfheal.sh state/ops/sshd-selfheal.service state/ops/sshd-selfheal.timer ubu1:/tmp/

# 2. ubu1 에서 설치
ssh ubu1 'sudo install -m 0755 /tmp/ubu1_sshd_selfheal.sh /usr/local/sbin/sshd_selfheal && \
          sudo install -m 0644 /tmp/sshd-selfheal.service /etc/systemd/system/ && \
          sudo install -m 0644 /tmp/sshd-selfheal.timer   /etc/systemd/system/ && \
          sudo systemctl daemon-reload && \
          sudo systemctl enable --now sshd-selfheal.timer && \
          sudo systemctl status sshd-selfheal.timer --no-pager | head -5'

# 3. 검증 (1분 대기 후):
ssh ubu1 'sudo systemctl list-timers sshd-selfheal.timer --no-pager; sudo tail -5 /var/log/sshd_selfheal.log'
```

Optional:
- `~/.ssh/config` 의 `Host ubu ubu1` / `ubu1-d` / `ubu1-ts` / `ubu1-ts-d` entry 재확인 — 변경 불필요 예상.
- `scripts/bin/hexa_remote` FALLBACK_CHAIN (L124) 은 현재 `hetzner ubu2 ubu1 htz` — raw#36 fixpoint (RAM headroom 기준). ubu1 복구 후에도 순서 유지 권장 (128GB > 32GB RAM 우선순위는 SSH 건강과 무관).
- ubu1 이 OOM/disk/AppArmor 등 재발 가능 원인으로 판명되면 `proposal_inbox/` 에 regression ticket 기록.

## 방어 레이어 요약
| 레이어 | 어디서 | 역할 |
|---|---|---|
| Mac hosts-watchdog | `launchd` com.nexus.hosts-watchdog, 5min | 2-axis :22+:2222 probe, 10분 hang 시 macOS notification |
| hexa_remote RAM gate | `scripts/bin/hexa_remote` raw#36 fixpoint | ubu1 SSH OK + RAM<24G 시 hetzner 로 우회 (drill OOM 방지) |
| one-shot recovery | `state/ops/ubu1_sshd_oneshot_recovery.sh` | 물리 콘솔 1-line 복구 (Stage 1+2+3) |
| sshd selfheal (ubu1) | `systemd sshd-selfheal.timer`, 60s | Localhost :22 banner probe, 120s hang → restart, 4min + restart 실패 → reboot |
