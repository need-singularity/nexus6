# REPRODUCTION_RESULTS — 2026-04-26 self-simulation

**Protocol version**: REPRODUCTION_PROTOCOL.md commit `63e3e44c` (718L, 14 stages)
**Executed**: Stage 1 - Stage 10 (Stage 11-14 are post-mortem / failure modes)
**Wall-clock**: ~78 s (read-only, parallel where supported)
**Date**: 2026-04-26

## 0. Reproducer identity (transparency)

- **Reproducer**: same Claude Code actor that authored PAPER_DRAFT_v4 + REPRODUCTION_PROTOCOL + the falsifier/atlas/bridge registries.
- **Independence**: **NOT independent**. This is a *self-simulation* — a baseline that proves the protocol's commands execute end-to-end and produce the expected sentinels on the canonical machine, **not** that an outside reproducer would obtain the same outputs.
- **Purpose**: smoke-test the protocol before external reproducers attempt it; surface stale sentinels and silent drift.
- **Mutation policy**: read-only. No atlas/falsifier/state file was written during this run.

## 1. Stage results

| Stage | Description | Status | Sentinel observed |
|-------|-------------|--------|-------------------|
| 1 | Repo state + paper present | PASS | HEAD `0c854cbd docs(closure): SESSION_FINAL_SUMMARY_v7`; `design/hexa_sim/PAPER_DRAFT_v4.md` exists; working tree clean |
| 2 | Falsifier registry (count + health + uniqueness) | PASS | `wc -l = 168`; `__FALSIFIER_HEALTH__ PASS total=168 clean=168 hit=0 error=0 tampered=0 duration_ms=8358`; `__UNIQUENESS_CHECK__ PASS total=168 id_dup=0 slug_dup=0 sha_dup=0` |
| 3 | Atlas integrity (per-shard + cross-shard) | PASS | `__ATLAS_HEALTH__ PASS total=16 pass=16 tampered=0`; `__ATLAS_CROSS_SHARD_COLLISION__ PASS shards=16 total=9174 unique=9174 dup=0 conflict=0` |
| 4 | Bridge health (16 bridges, parallel) | PASS | `__BRIDGE_HEALTH__ PASS total=16 pass=16 fail=0 tampered=0 duration_ms=15813` |
| 5 | 4-repo Honesty triad | PASS | `__ATLAS_CROSS_REPO_DASHBOARD__ repos=4 total_atlas_lines=65454 total_facts=28850 honesty_pass=3/4 honesty_5_5=3 honesty_6_6=3 mode=6`; `__HONESTY_QUICK__ mode=6 honesty_5_5=3 honesty_6_6=3 repos=4` |
| 6 | Defense R5 ledger + signature verify | PASS | `__LEDGER_VERIFY__ PASS entries=8 broken_at=none ledger=atlas_sha256_rotation_log.jsonl`; `__LEDGER_VERIFY__ PASS entries=2 broken_at=none ledger=bridge_sha256_rotation_log.jsonl`; `__REGISTRY_SIGN__ VERIFIED` for falsifier+bridge+atlas (identity=nexus@local) |
| 7 | F100 mathematical singularity | PASS | `python3` returns `F100: [1, 6]` — n=6 is the only non-trivial solution to sigma(n)*phi(n) = n*tau(n) in [1,30] (n=1 is the trivial degenerate case included by the inclusive `range(1,31)`) |
| 8 | Cross-domain F36 + F28 | PASS | `F36: True` (2^6 = 4^3 = tau^3 = 64); `F28: True` (J_2 - mu = 24 - 1 = 23) |
| 9 | Multi-decomposition 1728 (F36+F32+F80) | PASS | `1728: True` — 12^3 = sigma(6)^3 = 576*3 = J_2^2 * 6 / 2 = 1728 |
| 10 | F45 honest decline reproduction | PASS | `F45 collapse: True` — \|0.0263 - 0.0350\| * 100 = 0.87 > 0.5, the alpha-CMB collapse is correctly declined |

**Total**: 10 / 10 PASS.

## 2. Drift from §13 expected outcomes table (honest delta)

The protocol §13 table was frozen at an earlier registry snapshot. Current state has *grown* (more axioms / shards / ledger entries) but the structural assertions (clean=total, dup=0, broken_at=none) all still hold. Drift summary:

| Element | §13 expected | 2026-04-26 observed | Reason |
|---------|--------------|---------------------|--------|
| falsifier total | 115 | **168** | +53 axioms added between protocol freeze and 2026-04-26 (post 53-batch) |
| atlas total | 11 | **16** | +5 shards added (16 atlas shards LIVE per current state) |
| atlas tuples | 9165 | **9174** | +9 facts ingested |
| ledger atlas entries | 3 | **8** | +5 R5 rotations recorded |
| ledger bridge entries | 2 | 2 | unchanged |
| Honesty 6/6 repos | 3 | 3 | unchanged (nexus, CANON, anima); hexa-lang remains 5/6 (precondition d gap) |

**No structural regressions**. All deltas are *additive* and the pass conditions (clean=total, conflict=0, broken_at=none) remain satisfied.

## 3. Most striking finding

**F100 singularity reproduces zero-friction**: enumerating sigma(n)*phi(n) == n*tau(n) for n in [1,30] returns exactly `[1, 6]`. n=1 is the trivial degenerate (sigma=phi=tau=1, both sides = 1). n=6 is the only non-trivial solution, matching the paper's claim that the perfect-number / cocktail of three multiplicative functions collapses uniquely at 6 — the same n that drives F36 (codon 64 = 2^6), F32+F80 (1728 = 12^3 = sigma(6)^3), and F28 (J_2(S_6) - mu = 23). The cross-domain anchors all triangulate on n=6 in <1 s of Python.

## 4. External reproducer ready: **Y, with caveats**

- **Y**: every command in stages 1-10 is executable, sentinel-grepable, and produced PASS on the canonical machine. Bash + python3 + (optional) hexa runtime is sufficient. No SSH key needed for the R1+R5 ledger chain (only the *optional* SSH-detached signature requires the reproducer's own key).
- **Caveats**:
  1. Protocol §13 sentinels are **stale** (115 vs 168 falsifiers, etc.). External reproducers MUST be told to expect grown registries; the structural assertions (PASS, clean=total, dup=0) are the durable contract.
  2. The hexa runtime requires `HEXA_RESOLVER_NO_REROUTE=1` on macOS to dodge the sandbox SIGKILL (already documented in §14.1).
  3. Bridge stage took ~16 s wall-clock with all 16 bridges live; a network-isolated reproducer would see `__BRIDGE_HEALTH__ PASS` with fallback counts and that is documented as also PASS.

## 5. Honest caveat (cannot be over-stated)

This run is a **self-simulation by the same actor that wrote the framework, the registries, the protocol, and the expected sentinels**. It proves:

- The commands execute.
- The sentinels match.
- The math (Stages 7-10) is internally consistent.

It does **NOT** prove:

- An independent third party would replicate the registry contents (the actor could have authored sigma/phi/tau code that emits its own expected output).
- The atlas sha256 chain is anchored to anything outside this actor's control.
- The "novel mathematical findings" (F100 etc.) are novel to mathematics rather than novel to this actor's literature search.

True independence requires a reproducer who:
1. clones the four repos at the frozen commit hashes,
2. runs every stage with their own python/bash,
3. cross-checks F75 / F100 against MathOverflow or a CAS (Magma, GAP, SageMath) they did not download from this actor,
4. compares atlas R1 sha256 against an offline copy stamped before this actor saw the paper.

Until that exists, the strongest claim is: **"the protocol is self-consistent and reproducible on the canonical machine."**

## 6. Wall-clock breakdown

| Phase | Seconds |
|-------|---------|
| Stages 1+2 (repo, registry) | ~10 |
| Stage 3 (atlas) | <1 |
| Stage 4 (bridges, parallel) | ~16 |
| Stage 5 (honesty triad) | ~5 |
| Stage 6 (ledger + signatures) | ~3 |
| Stages 7-10 (python math) | <2 |
| **Total** | **~78** |

Hardware: macOS darwin 24.6.0, single laptop. Network: live (all 16 bridges hit live endpoints, no fallback engaged).

## 7. Recommendation

Ship the protocol to external reproducers **after** patching §13 with current sentinels (or, better, replace the literal counts with structural assertions: `total>=N_min` style). The 10-stage core is solid; the only friction point is sentinel staleness, which an external reproducer would (correctly) flag as a fail unless warned.

---
*Generated by Claude Code self-simulation, 2026-04-26. Read-only run, no state mutation.*
