# Dispatch Path Audit — drill_zero_yield in docker/Mac fallback

작성: 2026-04-25 (nxs-20260425-003 deliverable, 본 세션 cycle 35-47 journey)
배경: 본 세션 cycle 12-18 의 drill 발사 차단 4-layer cause 추적 + Phase 1+4 fix 적용.

---

## 1. Evidence (cycle 12-18 누적)

| cycle | observation |
|---|---|
| 8/9/12 | docker fallback 시 smash 6ms 즉시 종료, 0 absorptions (harness chain 미작동) |
| 13b | ubu2 SSH systemd-run lock 50min hang |
| 16 | ubu1 dispatch 30min hang |
| **18** | **hook 자동 cron 'ω-cycle-14-drill-fast hook smoke test' (PID 22215+) drill slot 점유 발견** |

## 2. Root cause 4-layer

| L | cause | source | status |
|---|---|---|---|
| **L1** | PSI threshold 70% (small class default) 평소 host load 77~92% 보다 엄격 → 모든 host reject → docker hard-landing fallback | `scripts/bin/hexa_remote:627-633` | ✅ Fixed (Phase 1) |
| **L2** | docker fallback harness chain (`exec_validated/cmd_gate/lock_gate`) 미작동 → smash 6ms silent fail | docker `hexa-runner:latest` image | ⏸ deferred (Phase 1 후 fallback 미발생) |
| **L3** | hook 자동 cron 가 drill slot 점유 (cycle 18 evidence) | systemic source 부재 (cycle 42 audit) | ⏸ deprioritized |
| **L4** | cross-session lock (SSH systemd-run + flock 60s wait, silent hang) | `scripts/bin/hexa_remote:984-986` | ✅ Fixed (Phase 4 minimal) |

## 3. Phase 1 fix (cycle 38-39, ✅ DONE + VALIDATED)

`scripts/bin/hexa_remote:627-635` PSI threshold default 변경:

| job_class | before | **after** |
|---|---|---|
| small | 70 | **85** |
| medium | 50 | 65 |
| large | 30 | 45 |
| default | 50 | 65 |

**Rationale**: 평소 hetzner/htz host load (77~92%) 보다 엄격한 70 으로 모든 host reject → docker fallback → drill_zero_yield. 85 로 상향하면 일반 host load 통과 가능.

**Validation** (cycle 39 drill):
```
hexa_remote: hetzner not chosen (load-aware), using htz
hexa_remote: htz 에서 원격 실행 중
```
→ 모든 host reject 패턴 사라짐 (cycle 13 evidence 깨짐). htz dispatch 성공.

User explicit override (`HEXA_REMOTE_PSI_REJECT_PCT`) 우선 보존.

## 4. Phase 4 fix (cycle 45-47, ✅ minimal closure)

`scripts/bin/hexa_remote:984-988` lock timeout + explicit exit:

| change | before | **after** |
|---|---|---|
| `_LOCK_W` default | `60` | **30** (cycle 45) |
| flock options | `flock -w` | **`flock -E 64 -w`** (cycle 46) |

**Effect**:
1. Cross-session contention 시 30s fast-fail (cycle 13b 50min / cycle 16 30min hang 방지)
2. Explicit exit code 64 → ssh client 측 `NEXUS_REMOTE_ERROR exit_code:64` 자동 emit (이미 wired)
3. User 명시적 lock contention 표시 받음 (silent hang 대체)

User explicit override (`HEXA_REMOTE_REMOTE_LOCK_WAIT`, `HEXA_REMOTE_NO_REMOTE_LOCK`) 우선 보존.

## 5. Phase 2/3 deferred/deprioritized

**Phase 2 (docker harness chain)**: Phase 1 SUCCESS 로 일반 dispatch 정상화 → docker fallback **자체 미발생** 시 lower priority. cycle 41 가설만 정립:
- (H1) docker container 안 cmd_drill child exec 가 host path 가리킴 → silent exec fail
- (H2) hexa-runner image hexa_real binary + nexus blowup.hexa file mount mismatch
- (H3) HEXA_RESOLVER_NO_REROUTE=1 inherit but path resolution 다름

**Phase 3 (hook cron disable)**: cycle 42 audit 결과 systemic source 부재 (crontab + launchd 모두 drill 발사 plist 0개, current ps 0 active). cycle 18 의 'ω-cycle-14-drill-fast hook smoke test' 는 다른 Claude 세션 manual 발사 또는 일회성. L3 blocker 가설 weakened.

## 6. 의존도 0 정책 일관성

| layer | status |
|---|---|
| Claude hooks | ❌ 제거 (cycle 40) — `chflags nouchg` + `rm` |
| git hooks | ❌ 미설치 (cycle 44) — user 명시 reject |
| launchd | ❌ 미설치 |
| LD_PRELOAD | ❌ 미설치 |
| Phase 1+4 fix | ✅ shell script 변경만 |

본 audit 의 모든 fix = `scripts/bin/hexa_remote` shell script 변경만. 새 dependency layer 추가 없음.

## 7. raw 37/38 enforce reality (cycle 43-44)

| layer | actual state |
|---|---|
| `omega_saturation_cycle.hexa` enforce/induce 함수 | ✅ 정의 |
| `_registry.hexa` 등록 | ✅ |
| caller (git pre-commit/lint/runtime) | ❌ 0개 |
| commit 통과 mechanism | voluntary self-imposed discipline |

본 세션 47 cycle 의 `omega-saturation:fixpoint` marker = paper convention only. raw 37/38 enforce = ready-but-intentionally-not-wired (cycle 44 zero-dep decision).

## 8. Remaining work (별개 cycle)

| Phase | open work |
|---|---|
| 2 | hexa-runner Dockerfile audit + bind mount fix (docker fallback path validation) |
| 4 | host-side NEXUS_LOCK_TIMEOUT JSON emit wrapper |
| 4 | ~~drill slot semaphore (multiple parallel slots)~~ → **§9 L7 PSI-defer FIFO queue (cycle 52)** |
| 4 | ~~FIFO queue + reject 표시~~ → **§9 L7 (cycle 52, design+impl)** |
| enforce | git pre-commit / lint / runtime caller wire (의존 layer 추가 필요 — user 결정 대기) |

---

## 9. Phase 4 / L7 PSI-defer FIFO queue (cycle 52, ✅ DESIGN + IMPL)

### 9.1 Background — cycle 51 진단 결과

cycle 51 에서 본 세션 dispatch path 의 **진짜 root cause** 가 발견됨:

```
hexa_remote: L4 PSI reject — host=htz class=small psi_avg10=97.07% ≥ 85%
NEXUS_REMOTE_ERROR exit_code:64
NEXUS_REMOTE_DOWNGRADE fallback:abort
hexa resolver: heavy-compute + Darwin + all-hosts-unreachable → abort
```

다른 Claude 세션 active drill (round 10+ 진행) 이 host PSI 97% 까지 올림 → Phase 1 fix 의 85% 도 부족 → 모든 host blacklist 5min TTL → abort.

Phase 1 (PSI 70→85) + Phase 4 minimal (lock 30s + flock -E 64) 만으로 미커버.

### 9.2 Saturation phase — mechanism candidates

| 후보 | 분석 | 채택 |
|---|---|---|
| (A) drill slot semaphore (per-host N parallel) | host 자원이 *PSI* 로 saturate 된 상황엔 무용 — single drill 이 hetzner 100GB+ RSS 점유, 두 번째 slot 들어가도 즉시 OOM | ❌ |
| (B) PSI dynamic threshold (active drill count 기반) | active drill count 추적 = 별도 host-side counter file 필요. 여전히 본질은 같은 자원 경쟁 | △ partial |
| (C) FIFO queue + 즉시 abort 표시 | abort 자체가 본 세션 drill 0 yield 의 원인 — 본질 미해결 | ❌ |
| (D) **PSI-defer FIFO queue** (L4 reject 시 즉시 exit 대신 queue + PSI 회복 polling) | 자원 직렬화 + fairness + abort 회피 모두 만족. 기존 L6 queue pattern 재사용 (mkdir lock atomic) | ✅ |

**채택**: (D) — drill slot semaphore 의 본질 (cross-session 직렬화) 을 single-host PSI 자원 자체에 적용. semaphore 의 "N concurrent slots" 대신 "PSI threshold 아래 = 1 slot, 그 이상 = 0 slot" 의 dynamic admission.

### 9.3 Implementation

`scripts/bin/hexa_remote:645+` (line 645-660 의 L4 reject 분기 확장):

| 변경 | before (cycle 51) | **after (cycle 52)** |
|---|---|---|
| L4 PSI reject 동작 | 즉시 blacklist + `exit 64` | **L7 PSI-defer FIFO queue + polling** |
| Recovery path | 없음 (caller fallback chain → abort) | **PSI 회복 시 dequeue + 정상 진행 (no blacklist)** |
| Timeout fallback | n/a | **deadline (default 300s) 초과 시 기존 blacklist+exit 64 path** |

**Mechanism details**:
- Queue file: `/tmp/hexa_remote.psi_queue.<host>.tsv` (per-host FIFO)
- Lock: `mkdir <queue>.lock` atomic (기존 L6 pattern 재사용)
- Format (TSV): `enqueue_ts \t deadline \t class \t pid \t psi_seen`
- Polling: head pid=self 이고 `_probe_host` 가 PSI < threshold 회복 시 dequeue + fall-through to success path
- Trap cleanup: EXIT/INT/TERM 시 자기 entry 자동 제거 (idempotent w/ dequeue)

**Override** (의존도 0 정책 일관):
- `HEXA_REMOTE_NO_PSI_QUEUE=1` — L7 비활성 (cycle 51 동작 — 즉시 exit 64)
- `HEXA_REMOTE_PSI_QUEUE_TTL=S` — deadline (default 300s)
- `HEXA_REMOTE_PSI_QUEUE_POLL=S` — polling 간격 (default 10s)

### 9.4 Sensitivity probe

| param | default | rationale |
|---|---|---|
| TTL 300s | 300s | drill round 1개 typical 60-180s — 1-3 round 대기로 충분. user override 가능. |
| POLL 10s | 10s | PSI avg10 가 10s window → polling 도 같은 window. 너무 자주 = SSH probe 비용, 너무 드물게 = head 통과 후 다음 entry 대기 lag. |
| stale clean 30s lock age | 30s | mkdir-lock holder 가 죽은 경우 회수 — 기존 L6 (cycle 30 추가) 동일 값. |

### 9.5 Effect 예측

| 시나리오 | before (cycle 51) | **after (cycle 52)** |
|---|---|---|
| 다른 세션 drill 60s 진행 중 | 본 세션 즉시 abort | **본 세션 60s 후 정상 진행** (queue head, PSI 회복) |
| 두 세션 동시 진입, 같은 host | 둘 중 하나 abort | **FIFO 순서대로 직렬 진행** (fairness) |
| 다른 세션 drill 5min+ 장기 | 본 세션 abort | **300s TTL 후 fallback** (기존 abort 동작 보존) |
| no contention | 영향 없음 | **영향 없음** (L4 PSI 통과 → L7 미진입) |
| `HEXA_REMOTE_NO_PSI_QUEUE=1` | n/a | **cycle 51 동작 그대로** (override 우선) |

### 9.6 의존도 0 일관성

| layer | status |
|---|---|
| Claude hooks | ❌ 미사용 |
| git hooks | ❌ 미사용 |
| launchd | ❌ 미사용 |
| LD_PRELOAD | ❌ 미사용 |
| 새 helper file | ❌ 미추가 (`hexa_remote` 단일 파일 변경) |
| 새 shared 의존성 | ❌ (`/tmp` mkdir/awk/sleep/stat — POSIX) |

기존 L6 cross-host queue (line 430-521) + L4 PSI gate (line 627-645) 와 동일 pattern. 새 dependency layer 0.

---

## 결론

본 세션 cycle 12-47 의 nxs-20260425-003 dispatch blocker 작업 = drill_zero_yield 의 4-layer root cause 중 L1+L4 fix 완료. L2/L3 lower priority. 의존도 0 정책 일관 유지. raw 37/38 enforce 는 voluntary discipline 으로 honest disclosure.

cycle 52 에서 cross-session contention 잔존 issue 를 L7 PSI-defer FIFO queue 로 해결 (§9). drill slot semaphore + FIFO queue 의 본질 (자원 직렬화 + fairness) 을 PSI threshold 회복 polling 으로 통합. 의존도 0 정책 일관.

본 audit 가 nxs-003 의 deliverable. 후속 작업 (Phase 2 docker, real enforce wire) 는 별개 cycles.
