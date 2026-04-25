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
| 4 | drill slot semaphore (multiple parallel slots) |
| 4 | FIFO queue + reject 표시 |
| enforce | git pre-commit / lint / runtime caller wire (의존 layer 추가 필요 — user 결정 대기) |

---

## 결론

본 세션 cycle 12-47 의 nxs-20260425-003 dispatch blocker 작업 = drill_zero_yield 의 4-layer root cause 중 L1+L4 fix 완료. L2/L3 lower priority. 의존도 0 정책 일관 유지. raw 37/38 enforce 는 voluntary discipline 으로 honest disclosure.

본 audit 가 nxs-003 의 deliverable. 후속 작업 (Phase 2 docker, Phase 4 추가 features, real enforce wire) 는 별개 cycles.
