# atlas_sync_remote — 원격 atlas.n6 동기화

drill/blowup 자동 hetzner/ubu2 라우팅으로 원격에 atlas 적재됨. 로컬 stale 방지용 단방향 pull + diff 도구.

## 호스트 매핑 (검증 2026-04-19)

| host    | 경로                                          | 비고                                 |
|---------|----------------------------------------------|--------------------------------------|
| ubu2    | summer@.../home/summer/Dev/nexus/shared/n6/atlas.n6 | aiden = summer 계정. 1.5MB sync     |
| hetzner | root@.../root/Dev/nexus/shared/n6/atlas.n6          | 18MB+ HOT. drill 주 라우팅           |
| local   | /Users/ghost/Dev/nexus/shared/n6/atlas.n6           | sync 타깃                            |

## 명령 (HEXA_LOCAL=1 필수)

`hexa` resolver 가 default-ON 으로 ubu2/hetzner 원격 dispatch — ssh credentials 가 mac local 에만 있으므로 반드시 로컬 강제.

```
HEXA_LOCAL=1 HEXA_NO_LAUNCHD=1 hexa shared/scripts/atlas_sync_remote.hexa --direction diff --host all
HEXA_LOCAL=1 HEXA_NO_LAUNCHD=1 hexa shared/scripts/atlas_sync_remote.hexa --direction diff --host hetzner
HEXA_LOCAL=1 HEXA_NO_LAUNCHD=1 hexa shared/scripts/atlas_sync_remote.hexa --direction pull --host hetzner
HEXA_LOCAL=1 HEXA_NO_LAUNCHD=1 hexa shared/scripts/atlas_sync_remote.hexa --direction pull --host hetzner --dry-run
```

## 안전 게이트

- pull 전 `atlas.n6.pre_sync_<YYYYMMDD_HHMMSS>` 백업 (cp -p)
- scp 후 `.tmp` 로 받고 SHA256 일치 검증 → mv (atomic)
- mtime 충돌 (local > remote) 감지 시 abort + manual resolve 요구
- push 미구현 (의도적: 단방향만)
- `--host all` 은 diff 만 허용 (pull 은 ambiguous)

## 결과 해석 (stdout-based)

`hexa exit() 미전파` 함정 (memory f-hexa-exit-sentinel) 때문에 exit code 신뢰 불가. stdout sentinel 그렙:

```
... | grep "STATUS *: DIFFERS"     # diff 다름
... | grep "STATUS *: IDENTICAL"   # 동일
... | grep "CONFLICT:"             # pull 거부 (mtime 충돌)
... | grep "PULLED OK"             # pull 성공
... | grep "already in sync"       # skip
```

## 권장 패턴

```
# 1. 매번 drill/blowup 끝나고
HEXA_LOCAL=1 HEXA_NO_LAUNCHD=1 hexa shared/scripts/atlas_sync_remote.hexa --direction diff --host hetzner

# 2. DIFFERS + remote NEWER 출력되면
HEXA_LOCAL=1 HEXA_NO_LAUNCHD=1 hexa shared/scripts/atlas_sync_remote.hexa --direction pull --host hetzner --dry-run
HEXA_LOCAL=1 HEXA_NO_LAUNCHD=1 hexa shared/scripts/atlas_sync_remote.hexa --direction pull --host hetzner

# 3. 사고 시 롤백
mv shared/n6/atlas.n6.pre_sync_<TS> shared/n6/atlas.n6
```

## launchd (선택)

`shared/launchd/com.nexus.atlas-sync.plist` — 15분 주기 diff (pull 안 함).
로그: `shared/logs/atlas-sync.{stdout,stderr}.log`. 변경 감지 시 stdout 에 `STATUS : DIFFERS`.

설치:
```
launchctl load -w shared/launchd/com.nexus.atlas-sync.plist
```
중지:
```
launchctl unload shared/launchd/com.nexus.atlas-sync.plist
```

## 검증 결과 (2026-04-19 첫 실행)

| host    | sha 일치 | size 차이                | mtime advisory                 |
|---------|---------|-------------------------|--------------------------------|
| ubu2    | YES     | 1500993 vs 1500993      | IDENTICAL                      |
| hetzner | NO      | 1500993 vs 18879522     | local NEWER (mtime conflict)   |

→ hetzner 는 mtime 이 더 과거지만 size 12배. drill 파이프라인 타임라인 차이로 추정. 자동 pull 거부 — 수동 검토 필요.

## 함정 (memory ref)

- `f-hexa-real-interpreter-quirks` — `exec("bash", ["-c", ...])` 형태는 stdout 빈 반환 → 단일 문자열 `exec(cmdstr)` 사용 (security warning 무시)
- `reference_hexa_binary` — hexa resolver 가 nexus cwd 에서 자동 원격 dispatch → `HEXA_LOCAL=1` 필수
- `f-hexa-exit-sentinel` — `exit(N)` 가 쉘 $? 에 미전파 → stdout sentinel 그렙으로 결과 판정
- ssh ControlMaster 충돌 시 `rm ~/.ssh/cm/*` 후 재시도

## 미구현 (의도)

- push (mac → remote): 명시 요청 시 추가
- rsync (incremental): 1.5~18MB 규모에 scp 충분
