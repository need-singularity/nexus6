---
schema: nexus/docs/three_stub_impl_landed/ai-native/1
last_updated: 2026-05-02
ssot:
  marker:           state/markers/three_stub_impl_landed.marker
  modules:
    - nexus/modules/kick/claude_kick.hexa
    - nexus/modules/qrng/hardware_qrng.hexa
    - nexus/modules/sim/sim_close_loop.hexa
  mirrors_updated:
    - nexus/core/kick/registry.hexa
    - nexus/core/kick/kick_main.hexa
    - nexus/core/qrng/registry.hexa
    - nexus/core/qrng/qrng_main.hexa
    - nexus/core/sim/registry.hexa
    - nexus/core/sim/sim_main.hexa
  upstream_contracts:
    - nexus/core/kick/source.hexa  (preserved byte-identical)
    - nexus/core/qrng/source.hexa  (preserved byte-identical)
    - nexus/core/sim/source.hexa   (preserved byte-identical)
status: 3 STUB → IMPLEMENTED (mock-default, opt-in live)
related_raws:
  - raw 9    # hexa-only strict
  - raw 10   # honest C3 (caveats inline)
  - raw 99   # nexus kick canonical
  - raw 105  # autonomous kick
  - raw 270  # ai-native readme mandate
  - raw 271  # core+module pattern
  - raw 273  # sentinel attrs
preserved_unchanged:
  - nexus/core/kick/source.hexa  (interface contract)
  - nexus/core/qrng/source.hexa  (interface contract)
  - nexus/core/sim/source.hexa   (interface contract)
  - nexus/core/kick/router.hexa  (router preserved)
  - nexus/core/qrng/router.hexa  (router preserved)
  - nexus/core/sim/router.hexa   (router preserved)
  - nexus/modules/kick/{nexus_kick, mac_kick, dispatch_router}.hexa
  - nexus/modules/qrng/{anu, mock_qrng}.hexa
  - nexus/modules/sim/{sim_agent, sim_substrate}.hexa
  - nexus/tool/kick_dispatch.hexa
  - nexus/tool/hexa_sim_*.hexa  (6 wrapped tools)
migration_count: 0
user_directive: "BG SUBAGENT — 3 nexus STUB → IMPLEMENTED, AI-native, ω-cycle 6-step + silent-land marker"
---

# nexus 3 STUB → IMPLEMENTED landing — 2026-05-02

## TL;DR

Phase A1 nexus triplet (BG previously landed) 의 3 STUB module 을
**mock-default + opt-in live** 패턴으로 IMPLEMENTED.

| Module                                        | Pre status | Post status         | Live opt-in env                    |
|-----------------------------------------------|------------|---------------------|------------------------------------|
| `nexus/modules/kick/claude_kick.hexa`         | STUB       | IMPLEMENTED (T3)    | `NEXUS_KICK_CLAUDE_LIVE=1`         |
| `nexus/modules/qrng/hardware_qrng.hexa`       | STUB       | IMPLEMENTED (T3)    | `NEXUS_QRNG_HW_LIVE=1`             |
| `nexus/modules/sim/sim_close_loop.hexa`       | STUB       | IMPLEMENTED (T2)    | `NEXUS_SIM_CL_LIVE=1`              |

- 3 module selftest **PASS** (mock-mode, no spawn, no cost).
- 3 module byte-identical 2-run **PASS** (cf. SHA table below).
- Upstream 12 selftest (4 core + 4 module per domain × 3) **all PASS**.
- 6 mirror file (registry+main per domain) updated to reflect IMPLEMENTED status.
- Interface contract files (3 source.hexa) **preserved byte-identical**.
- ω-cycle: pre-impl baseline run → impl → selftest PASS → byte-id check → mirror sync → re-verify all → handoff doc + marker (single-pass clean, 0 iter).

## Module pre/post SHA + LOC table

| Module file (basename)     | Pre SHA (short)  | Post SHA (short)  | Pre LOC | Post LOC | Δ LOC  |
|----------------------------|------------------|-------------------|---------|----------|--------|
| `claude_kick.hexa`         | `92f9c8a3…`      | `32a7c33a…`       | 86      | 206      | +120   |
| `hardware_qrng.hexa`       | `d0987c53…`      | `82f65f8d…`       | 75      | 200      | +125   |
| `sim_close_loop.hexa`      | `ccf8d11e…`      | `3df83fea…`       | 79      | 233      | +154   |
| **Total**                  |                  |                   | **240** | **639**  | **+399** |

## Selftest results (3-pass cycle)

### Module-level selftest (all 3 PASS first-run, no iter)

```
[kick/claude_kick] anthropic claude CLI / API kick (T3 IMPLEMENTED mock-default)
[kick/claude_kick] SELFTEST PASS
__KICK_CLAUDE_KICK__ PASS

[qrng/hardware_qrng] local HW QRNG (T3 IMPLEMENTED mock-default)
[qrng/hardware_qrng] SELFTEST PASS
__QRNG_HARDWARE_QRNG__ PASS

[sim/sim_close_loop] EEG↔sim closed-loop (T2 IMPLEMENTED mock-default)
[sim/sim_close_loop] SELFTEST PASS
__SIM_SIM_CLOSE_LOOP__ PASS
```

### Selftest case coverage (per module)

| Module               | Cases       | Description                                                    |
|----------------------|-------------|----------------------------------------------------------------|
| `claude_kick`        | 5           | meta shape / dry-run mock PASS / live no-env FAIL / mock idempotence / empty-topic fallback |
| `hardware_qrng`      | 5           | meta shape / mock determinism (same seed) / mock seed-divergence / live no-env FAIL / n_bytes<1 FAIL |
| `sim_close_loop`     | 5           | meta shape / dry-run mock PASS / mock determinism / seed-divergence / live no-env FAIL |

### Byte-identical 2-run check (all 3 PASS)

```
claude_kick     byte-identical PASS sha=08504c54…
hardware_qrng   byte-identical PASS sha=95d3033e…
sim_close_loop  byte-identical PASS sha=b322d36a…
```

### Upstream cascade (12 contract + 10 module selftest, all PASS post-mirror-sync)

```
KICK CORE:    source PASS  registry PASS  router PASS  kick_main PASS
QRNG CORE:    source PASS  registry PASS  router PASS  qrng_main PASS
SIM CORE:     source PASS  registry PASS  router PASS  sim_main PASS
KICK MOD:     claude_kick PASS  dispatch_router PASS  mac_kick PASS  nexus_kick PASS
QRNG MOD:     anu PASS  hardware_qrng PASS  mock_qrng PASS
SIM MOD:      sim_agent PASS  sim_close_loop PASS  sim_substrate PASS
```

## Mock vs Real path 분기 (3 modules)

### claude_kick — anthropic claude CLI / API kick

| Path | Trigger                                          | Behavior                                                                      |
|------|--------------------------------------------------|-------------------------------------------------------------------------------|
| Mock | `dry_run=1` OR `NEXUS_KICK_CLAUDE_MOCK=1`        | Synthetic witness `/tmp/nexus_kick_claude_mock_<topic>.json` (no spawn)       |
| Live | `NEXUS_KICK_CLAUDE_LIVE=1` + cap + timeout + CLI | `echo <topic> | timeout <S> claude > <witness> 2>&1`; exit code → ok        |

Live path required env (all 4 must be present):
- `NEXUS_KICK_CLAUDE_LIVE=1` — opt-in flag
- `NEXUS_KICK_CAP_USD=<int>`  — per-call upper bound (declarative; not enforced by SDK ledger)
- `NEXUS_KICK_TIMEOUT_S=<int>` — hard timeout for `timeout(1)` wrapper
- `command -v claude` — CLI on PATH (probe at dispatch time)

Cost guard (raw#10): cap is **declarative**. Real $ ledger entry per call is a follow-up cycle (no writer yet). Witness path is the captured CLI stdout dump.

### hardware_qrng — local hardware QRNG (PCIe / USB-serial)

| Path | Trigger                                                                 | Behavior                                                                         |
|------|-------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| Mock | `NEXUS_QRNG_HW_MOCK=1` OR `NEXUS_QRNG_MOCK=1` OR `ANIMA_QRNG_MOCK=1`    | Deterministic LCG (same params as `mock_qrng.hexa`)                              |
| Live | `NEXUS_QRNG_HW_LIVE=1` + device probe                                   | `timeout <S> head -c <n> <dev> | xxd -p` → bytes int array                       |

Device probe order:
1. `/dev/quantis*`         — IDQ Quantis PCIe/USB
2. `/dev/cu.usbmodem*`     — ESP32 / Arduino-class USB CDC
3. `/dev/cu.usbserial*`    — FTDI / generic USB-UART

Live path required env:
- `NEXUS_QRNG_HW_LIVE=1` — opt-in flag
- `NEXUS_QRNG_HW_TIMEOUT_S=<int>` — read timeout (default 5s if unset)

raw#10: vendor claim of `is_quantum=1` is NOT independently verified (no NIST SP 800-90B
in module). Mock fixture is byte-identical to `mock_qrng` for given seed; use `mock_qrng`
directly in CI for path-invariant fixtures.

### sim_close_loop — EEG↔sim closed loop

| Path | Trigger                                          | Behavior                                                                         |
|------|--------------------------------------------------|----------------------------------------------------------------------------------|
| Mock | `dry_run=1` OR `NEXUS_SIM_CL_MOCK=1`             | Synthetic 3-tuple EEG state `[1, seed*10, 16]` → derived sim seed               |
| Live | `NEXUS_SIM_CL_LIVE=1` + EEG log + sim tool       | Read JSON → parse `n_segments`/`total_samples`/`channels_good` → derived seed   |

Live path required env:
- `NEXUS_SIM_CL_LIVE=1` — opt-in flag
- `NEXUS_SIM_CL_EEG_LOG=<path>` — anima-eeg/protocol_log/* JSON (e.g. `state/protocol_log_resting_*.json`)
- `nexus/tool/hexa_sim_verify_grid.hexa` — must exist (re-injection target)

Verified end-to-end on real EEG log (`anima/state/protocol_log_resting_selftest_synth.json`):
- `n_segments` parsed = 1
- `total_samples` parsed = 1250
- `channels_good` parsed = 16

raw#10: "EEG state vector" = coarse 3-tuple, NOT band-power/spectral/channel-wise.
Real closed-loop (alpha/beta/gamma band power × channel × sim event sink) requires
anima-eeg side hook (Phase 5 follow-up). Re-injection today = sim_agent dry-run only;
NO live grid_path mutation.

## Live-path failure mode probe (4 cases verified)

| Module          | Live env set, missing            | Expected fail message                                              |
|-----------------|----------------------------------|---------------------------------------------------------------------|
| `claude_kick`   | LIVE=1, no CAP                   | "NEXUS_KICK_CAP_USD env required (per-call upper bound USD)"        |
| `claude_kick`   | LIVE=1, CAP set, no TIMEOUT      | "NEXUS_KICK_TIMEOUT_S env required (per-call timeout seconds)"      |
| `hardware_qrng` | LIVE=1, no device                | "no device found at /dev/quantis* or /dev/cu.usbmodem* or /dev/cu.usbserial*" |
| `sim_close_loop`| LIVE=1, no EEG log              | "NEXUS_SIM_CL_EEG_LOG env required"                                 |

All fail-closed (`ok=0`); registry contract preserved.

## Mirror sync table (6 files updated to reflect new IMPLEMENTED status)

| Mirror file                          | Edit                                                                          |
|--------------------------------------|--------------------------------------------------------------------------------|
| `core/kick/registry.hexa`            | claude_kick meta `STUB` → `IMPLEMENTED`; dispatch fail msg → "live path gated" |
| `core/kick/kick_main.hexa`           | `_meta_for("claude_kick")` → IMPLEMENTED; stub_sentinel → impl_sentinel 2/2    |
| `core/qrng/registry.hexa`            | hardware_qrng meta `STUB` → `IMPLEMENTED`; dispatch fail msg → "live path gated" |
| `core/qrng/qrng_main.hexa`           | `_meta_for("hardware_qrng")` → IMPLEMENTED; stub_sentinel → impl_sentinel 3/3  |
| `core/sim/registry.hexa`             | sim_close_loop meta `STUB` → `IMPLEMENTED`; dispatch dry-run mock + selftest assertion update |
| `core/sim/sim_main.hexa`             | `_meta_for("sim_close_loop")` → IMPLEMENTED; stub_sentinel → impl_sentinel 1/1 |

## Preserved files (interface contract + sibling modules)

```
nexus/core/kick/source.hexa   — preserved byte-identical
nexus/core/qrng/source.hexa   — preserved byte-identical
nexus/core/sim/source.hexa    — preserved byte-identical
nexus/core/kick/router.hexa   — preserved byte-identical
nexus/core/qrng/router.hexa   — preserved byte-identical
nexus/core/sim/router.hexa    — preserved byte-identical

nexus/modules/kick/{nexus_kick, mac_kick, dispatch_router}.hexa  — preserved
nexus/modules/qrng/{anu, mock_qrng}.hexa                         — preserved
nexus/modules/sim/{sim_agent, sim_substrate}.hexa                — preserved

nexus/tool/kick_dispatch.hexa                                    — preserved (3496 LOC)
nexus/tool/hexa_sim_*.hexa  (6 files)                            — preserved
```

## raw#10 caveats (5)

1. **Mock-default + opt-in live** — 3 module 모두 default 가 mock (no spawn / no cost / no device).
   Live path 은 명시적 env (`NEXUS_KICK_CLAUDE_LIVE=1` / `NEXUS_QRNG_HW_LIVE=1` / `NEXUS_SIM_CL_LIVE=1`)
   필요. Selftest 는 절대 live path 를 통과하지 않음.

2. **claude_kick cost cap is declarative** — `NEXUS_KICK_CAP_USD` env 가 enforced 되는 것은
   "spawn 전 env 존재 검증" 만. 실제 $ ledger entry per call writer 는 follow-up cycle.
   raw 99/105 nexus kick canonical pattern 에 ledger writer 추가 후 cap enforcement 가능.

3. **hardware_qrng vendor 주장의 quantum-ness 는 unverified** — `is_quantum=1` 은 vendor label 만.
   NIST SP 800-90B health test, Min-Entropy estimator, repetition-count health test 모두
   미구현 (informational). 실제 quantum-ness assertion 은 NIST suite + 다중 source 비교 필요.
   ESP32 USB-serial path 는 "true HRNG" 가 아닌 "device-claimed entropy source" 임.

4. **sim_close_loop "EEG state vector" 는 coarse proxy** — 3-tuple `[n_segments, total_samples,
   channels_good]` 만 추출. Spectral analysis (band power per channel × frequency band)
   미구현. Real closed-loop (`.roadmap.sim cond.1`) 은 anima-eeg side band-power emitter
   + sim event sink + bidirectional latency budget 필요.

5. **Mirror sync 는 cosmetic but recommended** — registry/main aggregator 의 inline
   `_meta_for()` 와 `kick_registry_meta()` 는 module impl meta 의 hard-coded duplicate.
   Module impl 만 update 해도 module selftest 는 통과하지만 (registry 가 자기 mirror 만 검사),
   문서/SSOT consistency 를 위해 6 mirror file 도 sync. 모든 status string 이 IMPLEMENTED 로
   reflect 됨. Update 후 12 core + 10 module selftest 모두 PASS 재검증 완료.

## File index (post-impl)

| Path                                                                          | SHA (short)      | LOC |
|-------------------------------------------------------------------------------|------------------|-----|
| `nexus/modules/kick/claude_kick.hexa`                                         | `32a7c33a…`      | 206 |
| `nexus/modules/qrng/hardware_qrng.hexa`                                       | `82f65f8d…`      | 200 |
| `nexus/modules/sim/sim_close_loop.hexa`                                       | `3df83fea…`      | 233 |
| `nexus/core/kick/registry.hexa`                                               | `287f987d…`      | 175 |
| `nexus/core/kick/kick_main.hexa`                                              | `1848a141…`      | 153 |
| `nexus/core/qrng/registry.hexa`                                               | `b960d469…`      | 141 |
| `nexus/core/qrng/qrng_main.hexa`                                              | `8dd6b59b…`      | 147 |
| `nexus/core/sim/registry.hexa`                                                | `8d6edd9e…`      | 134 |
| `nexus/core/sim/sim_main.hexa`                                                | `764bce3b…`      | 122 |
| `nexus/docs/three_stub_impl_landed_2026_05_02.ai.md`                          | (this file)      | -   |
| `nexus/state/markers/three_stub_impl_landed.marker`                           | (sibling)        | -   |

## Next-cycle actionables

1. **claude_kick cost ledger** — add per-call $ ledger writer (jsonl append) so cap is
   enforced not just declared. Tie into raw 99/105 nexus kick canonical orchestrator.
2. **hardware_qrng NIST SP 800-90B** — add Min-Entropy / Repetition-Count health test to
   `qrng_source_collect_hardware_qrng` (sets `nist_pass=1` only on PASS).
3. **sim_close_loop band-power EEG state** — extend parser from coarse 3-tuple to band-power
   matrix (alpha/beta/gamma × channel). Requires anima-eeg side band-power emitter
   (.roadmap.eeg follow-up).
4. **Real closed-loop sim event sink** — sim_close_loop today is dry-injected. Land
   sim → EEG entrainment hook for full bidirectional loop (.roadmap.sim cond.1 verifier).
5. **README.ai.md per-domain update** — tier table status update STUB → IMPLEMENTED for
   the 3 modules (cosmetic; current README.ai.md still says STUB at module table).
