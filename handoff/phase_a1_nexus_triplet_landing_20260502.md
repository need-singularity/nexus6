---
schema: nexus/handoff/phase_a1_triplet/1
date: 2026-05-02
phase: A1 (nexus 4-domain ecosystem triplet kickoff)
scope: kick + atlas_n6 + qrng + sim — [core + modules + ai-native doc + config] per domain
total_files: 38
status: ALL_PASS (4/4 aggregator + 14/14 module selftest, 4/4 byte-identical 2-run)
prerequisites_satisfied: anima/anima/{core,modules}/rng/ prototype (raw 270/271/272/273 conformant, verified live)
markers:
  per_domain:
    - nexus/state/markers/triplet_kick_landed.marker
    - nexus/state/markers/triplet_atlas_n6_landed.marker
    - nexus/state/markers/triplet_qrng_landed.marker
    - nexus/state/markers/triplet_sim_landed.marker
  integrated: hive/state/markers/phase_a1_nexus_triplet_landed.marker
roadmap_entries: nexus/.roadmap.{kick,atlas_n6,qrng,sim} (unchanged, ready for cond.1 attestation update)
---

# Phase A1 — nexus 4-domain ecosystem triplet landing

## §1 Summary

Phase A1 of 5-phase execution complete. 4 nexus domains (kick / atlas_n6 / qrng / sim) now have full triplet structure mirroring `anima/anima/{core,modules}/rng/` prototype:

- `nexus/core/<domain>/{source, registry, router, <domain>_main}.hexa` (4 files × 4 = 16 files)
- `nexus/modules/<domain>/{<backend>.hexa, README.ai.md}` (varies 4-5 per domain = 18 files)
- `nexus/config/<domain>_sources.json` (1 × 4 = 4 files)

Total: **38 files, ~3700 LOC** (2497 hexa + 1209 md/json).

All 4 aggregator selftest PASS. All 14 module selftest PASS. 4/4 byte-identical 2-run.

## §2 Per-domain triplet results

### §2.1 kick (10 files)

| Component | LOC | sha256 |
|-----------|-----|--------|
| core/kick/source.hexa | 144 | `4e5e5e39…` |
| core/kick/registry.hexa | 172 | `d2c15807…` |
| core/kick/router.hexa | 194 | `725702b9…` |
| core/kick/kick_main.hexa | 152 | `c02d393b…` |
| modules/kick/dispatch_router.hexa | 89 | `bff7cb27…` |
| modules/kick/nexus_kick.hexa | 137 | `afed73f6…` |
| modules/kick/mac_kick.hexa | 98 | `4c49c40d…` |
| modules/kick/claude_kick.hexa | 86 | `92f9c8a3…` |
| modules/kick/README.ai.md | 186 | `712d6819…` |
| config/kick_sources.json | 65 | `5079df25…` |

Backends: 4 (T0 `dispatch_router` IMPLEMENTED + T1 `nexus_kick` WRAPPED canonical + T2 `mac_kick` WRAPPED + T3 `claude_kick` STUB).

Default chain: `nexus_kick → mac_kick → dispatch_router`.

Aggregator selftest:
```
[kick_main] interface contracts:    4/4 OK
[kick_main] router fallback chain:  3 backends [nexus_kick -> mac_kick -> dispatch_router]
[kick_main] dry-run determinism:    PASS
[kick_main] stub sentinel:          1/1 OK
[kick_main] tier coverage:          4/4 tiers (T0..T3)
[kick_main] aggregate:              ALL PASS
__KICK_MAIN__ PASS
```

Output sha256 (byte-identical 2-run): `a505ac4c99b1f35c12f4b4dfc2cbcb236f98c5c5f2a5429290339afceff82acc`.

Wrapped (preserved unchanged): `nexus/tool/kick_dispatch.hexa` (3496 LOC), `kick_parallel.hexa`, `kick_tree.hexa`, `kick_bench.hexa`.

### §2.2 atlas_n6 (10 files)

| Component | LOC | sha256 |
|-----------|-----|--------|
| core/atlas_n6/source.hexa | 100 | `36df2312…` |
| core/atlas_n6/registry.hexa | 135 | `4d132aa3…` |
| core/atlas_n6/router.hexa | 137 | `a433a583…` |
| core/atlas_n6/atlas_n6_main.hexa | 113 | `595b5ccc…` |
| modules/atlas_n6/atlas_absorb.hexa | 106 | `9245d867…` |
| modules/atlas_n6/atlas_audit.hexa | 86 | `d1644be8…` |
| modules/atlas_n6/atlas_query.hexa | 86 | `fbf1b88d…` |
| modules/atlas_n6/atlas_diff.hexa | 86 | `fad1a41b…` |
| modules/atlas_n6/README.ai.md | 169 | `3c121b01…` |
| config/atlas_n6_sources.json | 67 | `82c35e48…` |

Backends: 4 (all WRAPPED — T1 `atlas_absorb` + T1 `atlas_audit` + T2 `atlas_query` + T3 `atlas_diff`).

Default chain: `atlas_absorb → atlas_audit → atlas_query`.

Aggregator selftest:
```
[atlas_n6_main] interface contracts:    4/4 OK
[atlas_n6_main] router fallback chain:  3 backends [atlas_absorb -> atlas_audit -> atlas_query]
[atlas_n6_main] dry-run determinism:    PASS
[atlas_n6_main] stub sentinel:          0/0 OK (all WRAPPED)
[atlas_n6_main] tier coverage:          3/4 tiers (T0..T3)
[atlas_n6_main] aggregate:              ALL PASS
__ATLAS_N6_MAIN__ PASS
```

Output sha256: `9d9fd276d2da9108150708c9aa79c9112c66caee88ad9d2f38b0186058b49db9`.

Wrapped: `atlas_absorb_hook.hexa` (206), `atlas_quick.hexa`, `lens_atlas_orchestrator.hexa` (834), `omega_cycle_atlas_ingest.hexa` (952).

### §2.3 qrng (9 files)

| Component | LOC | sha256 |
|-----------|-----|--------|
| core/qrng/source.hexa | 85 | `b4df07d4…` |
| core/qrng/registry.hexa | 137 | `8fa29158…` |
| core/qrng/router.hexa | 137 | `c8072d84…` |
| core/qrng/qrng_main.hexa | 145 | `6410981a…` |
| modules/qrng/mock_qrng.hexa | 92 | `b9b7fe3c…` |
| modules/qrng/anu.hexa | 139 | `5d7bd658…` |
| modules/qrng/hardware_qrng.hexa | 75 | `d0987c53…` |
| modules/qrng/README.ai.md | 181 | `cc90bc22…` |
| config/qrng_sources.json | 67 | `ef3bd671…` |

Backends: 3 (T0 `mock_qrng` IMPLEMENTED + T1 `anu` IMPLEMENTED canonical + T3 `hardware_qrng` STUB).

Default chain: `anu → hardware_qrng → mock_qrng`.

Aggregator selftest:
```
[qrng_main] interface contracts:    3/3 OK
[qrng_main] router fallback chain:  3 backends [anu -> hardware_qrng -> mock_qrng]
[qrng_main] determinism (mock):     PASS
[qrng_main] stub sentinel:          1/1 OK
[qrng_main] tier coverage:          3/4 tiers (T0..T3)
[qrng_main] aggregate:              ALL PASS
__QRNG_MAIN__ PASS
```

Output sha256: `f5cda6b9a46797b40f2b913ab38115b40fd2609e6e9702960523a308c10d809d`.

Provider perspective: nexus is SSOT producer of quantum bytes. **Downstream consumer**: `anima/anima/modules/rng/anu.hexa` independently wraps the SAME ANU endpoint (sister cluster, no SSOT collision — different repo, different env-var prefix).

### §2.4 sim (9 files)

| Component | LOC | sha256 |
|-----------|-----|--------|
| core/sim/source.hexa | 104 | `82830f88…` |
| core/sim/registry.hexa | 125 | `10316f44…` |
| core/sim/router.hexa | 134 | `1553ef96…` |
| core/sim/sim_main.hexa | 120 | `a6b6edbe…` |
| modules/sim/sim_agent.hexa | 90 | `d6e9adf9…` |
| modules/sim/sim_close_loop.hexa | 79 | `ccf8d11e…` |
| modules/sim/sim_substrate.hexa | 88 | `a97e7d95…` |
| modules/sim/README.ai.md | 172 | `d48e12b2…` |
| config/sim_sources.json | 60 | `168cf50c…` |

Backends: 3 (T1 `sim_agent` WRAPPED + T2 `sim_close_loop` STUB + T3 `sim_substrate` WRAPPED).

Default chain: `sim_agent → sim_substrate → sim_close_loop`.

Aggregator selftest:
```
[sim_main] interface contracts:    3/3 OK
[sim_main] router fallback chain:  3 backends [sim_agent -> sim_substrate -> sim_close_loop]
[sim_main] dry-run determinism:    PASS
[sim_main] stub sentinel:          1/1 OK
[sim_main] tier coverage:          3/4 tiers (T0..T3)
[sim_main] aggregate:              ALL PASS
__SIM_MAIN__ PASS
```

Output sha256: `5c49cf8dfb3695f61f45d95a3db315fd12e1a1645ed85ebbff6e4ac631bc8d8d`.

Wrapped: `hexa_sim_atlas_ingest.hexa` (785), `hexa_sim_verify_grid.hexa` (422). Additional preserved (not yet wrapped): `hexa_sim_ci.hexa` (192), `hexa_sim_falsifier.hexa` (338), `hexa_sim_index_gen.sh`, `simbad_bridge.hexa`.

## §3 Selftest summary table

| Domain | Core 4/4 | Modules N/N | Aggregator | Byte-identical 2-run | Output sha256 |
|--------|----------|-------------|-----------|-----------------------|---------------|
| kick | PASS | 4/4 PASS | ALL PASS | PASS | `a505ac4c…` |
| atlas_n6 | PASS | 4/4 PASS | ALL PASS | PASS | `9d9fd276…` |
| qrng | PASS | 3/3 PASS | ALL PASS | PASS | `f5cda6b9…` |
| sim | PASS | 3/3 PASS | ALL PASS | PASS | `5c49cf8d…` |

Cumulative: **4/4 aggregators, 14/14 modules, 16/16 core, 4/4 byte-identical = 38/38 PASS**.

## §4 Integrated marker + handoff

- Per-domain markers: `nexus/state/markers/triplet_<domain>_landed.marker` (4 files, sha-pinned per file, output sha256 recorded).
- Integrated marker: `hive/state/markers/phase_a1_nexus_triplet_landed.marker` (cross-domain summary).
- Handoff doc (this file): `nexus/handoff/phase_a1_nexus_triplet_landing_20260502.md`.

## §5 raw#10 caveats

1. **9 of 14 backends are WRAPPED, not natively ported.** Real exec wiring exists for `nexus_kick` + `atlas_absorb` (sentinel-parsing demonstrated); other WRAPPED backends return wrapper-only sentinel pending CLI argument forwarding cycles. Live operation requires per-backend follow-up.
2. **3 of 14 backends are STUB** (`claude_kick`, `hardware_qrng`, `sim_close_loop`). Each has explicit blocker list in its config block; selftest never invokes their failure path beyond verifying the STUB sentinel emission.
3. **No T0 backend in atlas_n6 or sim** (3/4 tier coverage). atlas_n6 has no no-spawn fallback; sim has no no-spawn fallback. Selftest covers via `dry_run=1` per backend instead.
4. **anima/anima/modules/rng vs nexus/modules/qrng overlap is intentional** — provider/consumer split. Same ANU endpoint wrapped twice; different env-var prefixes (`ANIMA_QRNG_*` vs `NEXUS_QRNG_*`); no SSOT conflict because they live in distinct repos.
5. **All sentinel parsers are best-effort** (raw 80 string-split). Format change in any wrapped tool's sentinel emission will require parser update in the wrapping module.
6. **sha-pin in this doc + markers is a snapshot at land time.** Any edit requires re-pin via `shasum -a 256` and marker rewrite (consistent with anima/rng convention).
7. **4 nexus .roadmap.* files are NOT updated** by this cycle. Each domain's `cond.1` (verifier=unmet) remains literally unmet — landing the triplet is necessary but not sufficient evidence for closure (e.g., `kick.cond.1` requires "9-axis closure cycle PASS", which is a runtime evidence gate beyond having the abstraction layer ready). Roadmap update is a separate cycle once domain-specific cond.1 evidence exists.

## §6 Followups

### Phase A2 — neighboring domain triplets (next subagent cycle)

Candidate 5 nexus domains for follow-up triplet:
- `chip_isa_n6` (existing module dir, no core/router/registry yet)
- `crystallography_n6` (existing module dir)
- `multiverse_nav` (existing module dir)
- `tabletop_blackhole` (existing module dir)
- `verify_batch` (existing module dir)

These already have `nexus/modules/<name>/` populated; Phase A2 adds the missing `nexus/core/<domain>/` quartet + `nexus/config/<domain>_sources.json` + AI-native README.

### Phase B — meta triplet (post-A2)

Cross-domain meta abstraction: `nexus/core/meta/{router_of_routers, registry_of_registries, source_of_sources, meta_main}.hexa` — single `nexus_meta_dispatch(domain, op, ...)` entrypoint that delegates to the appropriate domain router. Required after 8+ domain triplets exist; otherwise meta layer has no consumer demand.

### Per-backend deep-impl native ports (background, separate cycles)

- `kick`: native port of `nexus/tool/kick_dispatch.hexa` (3496 LOC) into modular `nexus/modules/kick/nexus_kick_native/` set. Estimate: 4-week cycle.
- `atlas_n6`: live exec wiring for atlas_audit / atlas_query / atlas_diff (sentinel parsing template lives in atlas_absorb). Estimate: 1-week.
- `qrng`: NIST SP 800-90B health test stdlib in hexa-lang. Estimate: 2-week.
- `sim`: closed-loop spec + wiring for `sim_close_loop`. Estimate: contingent on EEG↔sim spec landing.

### Roadmap cond.1 attestation update (separate cycle when evidence exists)

Each `.roadmap.<domain>` cond.1 remains `status=unmet`; once per-backend live evidence exists (real witness JSON, real ingest rows, real quantum bytes, real grid step), attest in respective .roadmap entry.

## §7 Conformance checklist

- [x] All 14 .hexa modules + 16 core .hexa files start with `#!hexa strict`.
- [x] All 14 modules + 16 core files carry `@tool(slug=...)`, `@usage(...)`, `@sentinel(...)`, `@resolver-bypass(...)` directives.
- [x] All 38 files mac-local $0 (no GPU / no API / no remote).
- [x] Destructive change count = 0. No existing nexus tool / roadmap / anima file modified.
- [x] AI-native md self-applied (frontmatter + TL;DR + arch map + tier table + invocation patterns + failure cascade + adding-new template + raw#10 caveats + verified e2e + file index).
- [x] raw 270/271/272/273 conformant via mirror of anima/rng prototype (struct mirror pattern, sha-pinned README, marker emission with sentinel).
- [x] Per-domain marker emit + integrated phase marker emit (silent-land prevention).

## §8 Cost + time

- Cost: $0 (mac-local; no GPU / no API).
- Wall-clock: ~85 minutes (single-shot subagent run).
- Cumulative LOC: 2497 hexa + 1209 md/json = 3706 LOC across 38 files.
