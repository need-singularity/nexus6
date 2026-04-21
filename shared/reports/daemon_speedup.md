# Phase 2 Daemon Speedup — §6 Expected vs Observed

**SSOT**: `~/core/nexus/docs/phase2_resident_daemon_port_plan.md` §6
**Harness**: `~/core/nexus/test/bench_daemon.hexa`
**Status**: scaffolded (Step 8) — bench execution pending htz runner.

---

## 기대값 (design §6)

| 축                | Phase 1 (exec-per-req) | Phase 2 (daemon FIFO) | 개선           |
| ----------------- | ---------------------- | --------------------- | -------------- |
| cold start        | ~12 s (매 req)         | ~12 s (boot 1회)      | 100% (amort.)  |
| per-req wall      | ~12 s                  | 3–10 ms               | >1000×         |
| memory drift      | 0 (fresh proc)         | <10% over 1000 req    | N/A (bounded)  |
| daemon overhead   | 0                      | ~50 MB RSS            | acceptable     |

기준:
- Phase 1 cold = hexa interpreter boot + n6 atlas load + engine_registry.json
  parse — 매 request 마다 지불.
- Phase 2 per-req = FIFO write + daemon dispatch + blowup.hexa exec (Step 2
  MVP). Step 5 in-proc dispatch 가 떨어지면 1–3 ms 까지 내려갈 것으로 예상.
- memory drift bound = round-scoped global reset (§4.1) + atlas
  single-writer (§4.2) 으로 per-round steady-state.

---

## 실측 (pending — Mac hexa run hook 재귀 hang, htz 에서 실행 예정)

| Mode            | iters | wall total (ms) | p50 (ms) | p95 (ms) | p99 (ms) | cold boot (ms) |
| --------------- | ----- | --------------- | -------- | -------- | -------- | -------------- |
| Phase 1 exec    | ?     | ?               | ?        | ?        | ?        | 0 (per-req)    |
| Phase 2 daemon  | ?     | ?               | ?        | ?        | ?        | ?              |

**Mac 환경 제약**: `hexa run` 이 현재 hook 재귀 (L1 pre-commit → hexa parse →
hook re-entry) 로 hang. htz (Linux) 환경에서 실행 필요.

**표본 크기**: 기본 iters=10 (quick sanity) / 권장 iters=100 (p99 의미
있으려면). 1000 req stress 는 memory drift 관측용.

---

## 실행 방법

```sh
# default (iters=10)
cd ~/core/nexus && hexa run test/bench_daemon.hexa

# explicit iters (htz 실측용)
NEXUS_DRILL_DAEMON=1 hexa run test/bench_daemon.hexa 100

# 출력 — 2 NDJSON lines on stdout:
#   {"phase":1,"iters":100,"boot_ms":0,"per_req_ms":{...},"wall_total_ms":...}
#   {"phase":2,"iters":100,"boot_ms":12034,"per_req_ms":{...},"wall_total_ms":...}
```

결과는 위 "실측" 표에 수기 입력. (자동 fill-in 은 Step 9 rollout 에서.)

---

## 정책 (Phase 4 rollout 전 유지)

- `NEXUS_DRILL_DAEMON` **default off** — nexus drill 은 여전히 Phase 1 exec
  경로를 탄다.
- opt-in: `NEXUS_DRILL_DAEMON=1 nexus drill …` 시에만 daemon FIFO 경유.
- Phase 3 launchd/systemd 통합 + Phase 4 rollout 이 끝나야 default on.
- 사유: Step 8 기준 in-proc dispatch 미완 (Step 5 follow-up), byte-identity
  guard (`test_daemon_reset.hexa`) 는 vacuous PASS — 진짜 state-leak 검증은
  Step 5 이후.

---

## 진행 체크리스트

- [x] Step 8 bench harness 작성 (`test/bench_daemon.hexa`)
- [x] Step 8 report template (`shared/reports/daemon_speedup.md`)
- [ ] htz 에서 iters=100 실측 → 표 fill-in
- [ ] iters=1000 memory drift 측정 (RSS sampling, 별도 harness)
- [ ] Step 9 rollout: default off → opt-in 문서화 + `nexus drill` wrapper
