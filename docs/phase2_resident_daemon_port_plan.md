# Phase 2 Resident Daemon Port Plan

status: design-only (코드 수정 없음)
date: 2026-04-21
design SSOT: `shared/design/engine_daemon_design.md` §2~4
Phase 1 구현: `cli/scripts/nexus_drilld.hexa` (exec-based MVP)
Phase 2 후보 파편: `shared/drill/daemon_main.hexa` (orphan, untracked)

---

## 설계 문서 요약 (§2~4)

### §2 blowup_daemon REPL 기본 구조
- `on_boot()` 에서 atlas.n6 / lens registry / engine registry / ouroboros 를 1 회 로드 후 READY 송신.
- main loop 는 stdin 한 줄 수신 → `parse(line)` → `state.reset_round()` → `dispatch(cmd, seed, depth, flags)` → `OK\t<round_new>\t<metrics_json>` 또는 `ERR\t<reason>` 송신.
- stdin protocol: 라인 단위 TAB-separated (`<cmd>\t<seed>\t<depth>\t<flags_json>\n`), cmd ∈ {smash, free, absolute, meta, hyper, resonance, ping, quit}.
- lifetime: idle 600 s 자발적 BYE, SIGTERM graceful flush, SIGKILL stale-lock GC, max lifetime 12 h.

### §3 Bootstrap / control plane
- 명령: `nexus daemon {start|status|stop|tail}`.
- 주소: REQ FIFO `/tmp/nexus_blowup.sock`, RET FIFO `/tmp/nexus_blowup.ret.sock`, PID `/tmp/nexus_blowup.pid`, atlas lock `shared/n6/.atlas.lock`.
- client 는 daemon alive + `NEXUS_DRILL_DAEMON=1` 일 때만 FIFO, 아니면 exec fallback. READY 미수신이면 500 ms backoff × 10.

### §4 State isolation
- 매 라운드 reset: `salt, jitter, rng_seed, partial_graph_delta, lens_consensus_buf, ouroboros.cycle_counter, timer_accumulator`.
- boot 유지: atlas 읽기 캐시, lens registry, engine registry, stdlib symbol table.
- concurrency: single-writer atlas.n6, 내부 큐로 다중 client 직렬화, 라운드별 graph delta batch flush.

---

## Phase 1 → Phase 2 변경 범위

| 축 | Phase 1 현재 | Phase 2 목표 |
|---|---|---|
| dispatch | `exec("hexa run cli/run.hexa drill ...")` (per-req cold start) | in-process `import drill_orchestrator` + 함수 직접 호출 |
| state | 매 요청 새 `hexa run` = 항상 fresh, leak 없음 | resident process → `state.reset_round()` 로 명시적 리셋 |
| atlas | read-only stat (size/mtime 확인만) | in-memory 읽기 캐시 + single-writer flush |
| stage coverage | drill 전체 chain exec | smash / free / absolute / meta / hyper / resonance 6 stage 개별 op |
| FIFO 프로토콜 | NDJSON `{"op":"drill","seed":"...","max_rounds":N,"reply":"<path>"}` | backward compat 유지 + 신규 op `{"op":"smash"|"free"|...}` 추가 |
| reply 채널 | per-request reply-FIFO (client 가 경로 생성) | 유지 (다중 client 응답 섞임 차단 목적). design §3.2 단일 ret FIFO 는 Phase 3 승격 |
| round_new id | stdout "ROUND " 라인 grep | `_round_id_from(ts_ms, seed)` = `r_<ts>_<prefix>_<djb2_hex6>` (daemon_main.hexa 참조) |

backward compat 원칙: 기존 `{"op":"drill","seed":...,"max_rounds":...}` 는 내부적으로 rounds 만큼 smash→...→resonance 체인을 in-proc 호출한다. Phase 1 client 가 재컴파일 없이 동작해야 한다.

---

## daemon_main.hexa 통합 vs 삭제 결정

**결정: 부분 흡수 후 원본 삭제 (통합)**

근거:
- `daemon_main.hexa` 가 가진 재사용 가치 있는 로직:
  - NDJSON `_get_str` / `_get_int` / `_get_bool` 파서 (Phase 1 nexus_drilld 의 `_json_str` / `_json_int` 보다 bool 지원 추가).
  - `_round_id_from()` + `_djb2_hex6()` 안정적 round id 생성.
  - AI-native error channels (`NEXUS_ENGINE_WARN/ERROR/DEAD/CRASH` stderr 프로토콜).
  - E14 LRU `e14_skip` 분기 + `cache_hit=true` 응답 스키마.
- 하지만 daemon_main.hexa 는 "cold invocation per request" 모델 (bash daemon 이 pipe 로 호출) — Phase 2 resident 모델과 프로세스 경계가 다르다. loop/lifecycle 은 재사용 불가.
- 따라서 `_get_str/_get_int/_get_bool/_round_id_from/_djb2_hex6/_emit_err` 6 함수만 `nexus_drilld.hexa` 로 흡수, 나머지 (main body, read_stdin 루프) 는 폐기.
- 흡수 후 `shared/drill/daemon_main.hexa` 는 Phase 2 병합 커밋에서 `git rm` (orphan → 정상 이력 종결).

---

## 단계별 포팅 순서 (reversible)

각 Step 은 독립 커밋 + `NEXUS_DRILL_DAEMON=0` 에서 회귀 zero 를 유지한다.

**Step 1: 파서/유틸 흡수 (no-behavior change)**
- `nexus_drilld.hexa` 에 `_get_bool`, `_round_id_from`, `_djb2_hex6`, `_emit_ndjson_err` 추가 (daemon_main.hexa 에서 이식).
- 기존 `_json_str/_json_int` 는 유지 (callsite 변경 없음).
- 회귀 테스트: Phase 1 ping/drill 가 동일 응답.

**Step 2: in-process dispatch 스켈레톤 (smash only)**
- `nexus_drilld.hexa` 에 `_handle_smash(seed, depth, flags)` 추가.
- body 는 `hexa run cli/blowup/core/blowup.hexa math <depth> --no-graph --seeds <seed>` 를 exec — 즉 **여전히 exec 이지만 drill chain 전체가 아니라 stage 단위**.
- FIFO 신규 op: `{"op":"smash","seed":"...","depth":3,"flags":{...},"reply":"..."}`.
- 이 Step 까지는 cold start 이점이 아직 없다 (exec). 다만 stage 단위 dispatch 경로를 검증.

**Step 3: state.reset_round() 도입 + resident cache scaffolding**
- daemon 내부 전역: `mut g_salt`, `mut g_jitter`, `mut g_rng_seed`, `mut g_partial_graph_delta`, `mut g_lens_consensus_buf`, `mut g_ouroboros_cycle`, `mut g_timer_acc` (§4.1 전체).
- `_reset_round(seed)` 함수 추가: 위 변수들을 seed hash 로 재파생.
- 각 op handler 진입 시 `_reset_round(seed)` 호출.
- atlas / lens / engine registry 는 boot 시 1 회 로드 (§4.2) — Phase 2 는 hash/size 만 캐싱, 본문 로드는 Step 5 로 이월.

**Step 4: byte-identity state-leak 테스트**
- 신규 테스트 `test/test_daemon_reset.hexa`:
  - seed A → seed B → seed A 순서로 smash 3 회 호출.
  - 1회차 A response 와 3회차 A response 가 canonical JSON 비교로 **byte-identical**.
- 실패 시 §4.1 reset target 에 누락된 변수가 있는지 조사.

**Step 5: 나머지 5 stage (free, absolute, meta, hyper, resonance)**
- stage 별 `_handle_<cmd>()` 를 Step 2 패턴으로 추가.
- drill chain op `{"op":"drill","max_rounds":N}` 는 내부적으로 6 stage in-order dispatch 로 구현 → backward compat 확보.

**Step 6: atlas single-writer + write batching**
- daemon 프로세스가 `shared/n6/.atlas.lock` 을 hold.
- stage 내부 graph delta 는 `g_partial_graph_delta` 에 누적 → round 종료 시 1 회 flush.
- 다른 hexa 프로세스가 atlas.n6 write 시도 시 감지 + refuse.

**Step 7: timeout + idle exit + max-lifetime hard cut**
- per-cmd hard timeout 180 s (§5 risk table) → `ERR\ttimeout`.
- idle 600 s → BYE + exit 0 (§2.4).
- boot 후 12 h 도달 시 self-exit (launchd 가 재기동 — Phase 3 에서 plist).

**Step 8: bench + flag default 유지**
- `shared/reports/daemon_speedup.md` 벤치 (§6 기댓값과 비교).
- `NEXUS_DRILL_DAEMON` 은 여전히 default **off** — Phase 4 rollout 에서 opt-in.

**Step 9: daemon_main.hexa 제거 커밋**
- Step 1~8 이 모두 merge 된 후 `git rm shared/drill/daemon_main.hexa` 를 별도 커밋.
- 커밋 메시지: `refactor(drill): remove orphan daemon_main.hexa — absorbed into nexus_drilld (Phase 2)`.

---

## 위험 요소

- **state leak (long-running)**: §4.1 reset 목록이 불완전하면 seed 간 결과 오염. → Step 4 byte-identity 테스트로 게이트.
- **FIFO backlog**: 다중 drill client 가 동시에 밀어넣으면 daemon 내부 큐가 팽창. → depth-1 blocking read 유지 + per-cmd 180 s timeout + log backpressure 알림.
- **atlas write 경합**: daemon 바깥에서 atlas.n6 를 여전히 쓰는 경로가 남아 있으면 손상. → Step 6 전에 `grep -rn "shared/n6/atlas.n6" cli/ shared/` 로 writer inventory 확인 필수.
- **stale lock (SIGKILL)**: pid liveness 체크 후 정리 로직 필요 (§3.2). `kill -9` 테스트 필수.
- **hexa interpreter의 state 누수**: hexa 자체가 일부 전역 심볼 테이블을 공유할 수 있음 — Step 3 reset 만으로 부족할 수 있다. byte-identity 실패 시 hexa upstream 이슈로 격상.
- **max 12 h drift**: 누적 allocation 의 GC 가 불완전 → OOM. launchd 재기동이 방어선.
- **FIFO EOF/SIGPIPE**: client crash 시 daemon block → `O_NONBLOCK` + SIGPIPE 핸들러 (§5 risk table).
- **prot ocol 혼선**: Phase 1 `{"op":"drill"}` 와 Phase 2 `{"op":"smash"}` 공존 — drill op 가 내부에서 6 stage 를 호출하도록 강제해 schema 파편화 방지.

---

## 테스트 계획

- **unit (in-proc dispatch)**:
  - `test/test_daemon_parse.hexa` — `_get_str/_get_int/_get_bool` 파서 round-trip.
  - `test/test_daemon_round_id.hexa` — `_round_id_from` 결정성 (same ts+seed → same id).
- **integration (FIFO round-trip)**:
  - `test/test_daemon_fifo.hexa` — daemon 기동 → ping → smash × 3 → quit → exit code 0.
  - backward compat: `{"op":"drill","max_rounds":2}` 가 Phase 1 client 동일 응답 스키마 반환.
- **state isolation (byte-identity)**:
  - `test/test_daemon_reset.hexa` — seed A → B → A, A₁ ≡ A₃ canonical JSON.
- **stress (1000 req sustained)**:
  - `test/stress_daemon_1k.hexa` — 1000 req 순차, wall-time 분산 p50/p95/p99, mem RSS drift < 10 % 최종 - 초기.
- **kill & recover**:
  - `kill -9 $(cat /tmp/nexus_drilld.pid)` → 재기동 시 stale lock GC 확인.
- **feature flag off 회귀**:
  - `NEXUS_DRILL_DAEMON=0` 에서 `nexus drill --seed X --max-rounds 1` 가 Phase 1 이전과 완전 동일 출력.

---

## 롤백 절차

단일 Step 롤백:
- `git revert <step-commit>` — 각 Step 이 독립 커밋이므로 안전.
- Step 6 (atlas single-writer) 롤백 시 `.atlas.lock` 수동 `rm` 필요.

전체 Phase 2 롤백:
- `NEXUS_DRILL_DAEMON=0` 설정 → drill client 가 즉시 exec fallback.
- `kill -TERM $(cat /tmp/nexus_drilld.pid)` → idle 600 s 대기 없이 graceful exit.
- `git revert` 범위: Step 1~9 의 merge commit 한 방에 revert 가능 (daemon 파일 1개 + run.hexa router branch 만 영향).
- atlas.n6 포맷 무변경 → 데이터 호환 영구 보장 (§9.3).

롤백 안전 불변식:
- Phase 2 의 어떤 Step 도 atlas.n6 스키마를 바꾸지 않는다.
- Phase 2 의 어떤 Step 도 Phase 1 FIFO protocol 필드를 **제거** 하지 않는다 (추가만 허용).
- `NEXUS_DRILL_DAEMON` default 는 Phase 2 전 구간에서 **off**.
