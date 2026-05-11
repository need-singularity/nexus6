# design/hexa_sim/ — HEXA-SIM Ω-cycle corpus

> **Last updated**: 2026-04-26 · **Counts**: 17 ω-cycle witnesses · 4 candidate reviews · 4 audits · 2 decisions · 2 session docs · 1 synthesis · 1 dashboard · 1 audit script · 2 JSONL registries (42 falsifiers / 3 history)
>
> **Charter** (preserved from 2026-04-25 origin): HEXA-SIM tests the hypothesis that the perfect number **n=6** (σ=12, τ=4, φ=2, sopfr=5) is a structural anchor across 7 independent physics frameworks (SE(3), Bostrom, Planck cells, Lloyd bound, α⁻¹, string D, Calabi-Yau). This directory is the **Ω-cycle witness corpus + falsifier registry + audit trail** for that program. Full paper-grade exposition lives in [`SYNTHESIS_2026-04-26.md`](SYNTHESIS_2026-04-26.md); upstream source: [CANON/.../simulation-theory.md](https://github.com/dancinlab/canon/blob/main/domains/physics/simulation-theory/simulation-theory.md).

---

## Quick Navigation

| Need | File |
|------|------|
| **Falsifier registry** (current SSOT) | [`falsifiers.jsonl`](falsifiers.jsonl) — 42 entries (F1–F12, F19–F44, F46–F49); F45 declined |
| **Falsifier history** (chained ledger, raw 77) | [`falsifier_history.jsonl`](falsifier_history.jsonl) |
| **Latest health checks** | [`2026-04-26_falsifier_health_check.md`](2026-04-26_falsifier_health_check.md) · [`2026-04-26_bridge_health_check.md`](2026-04-26_bridge_health_check.md) |
| **Atlas SSOT decision** (hexa-lang) | [`hexa_lang_atlas_ssot_decision.md`](hexa_lang_atlas_ssot_decision.md) |
| **Atlas function-call notation convention** | [`../atlas_function_call_convention.md`](../atlas_function_call_convention.md) |
| **Semantic-gap audit** + script | [`2026-04-26_atlas_semantic_gap_audit.md`](2026-04-26_atlas_semantic_gap_audit.md) · [`2026-04-26_atlas_semantic_gap_audit.py`](2026-04-26_atlas_semantic_gap_audit.py) |
| **Health-check tools** | seq: [`../../tool/falsifier_health.sh`](../../tool/falsifier_health.sh) · [`../../tool/bridge_health.sh`](../../tool/bridge_health.sh) · [`../../tool/atlas_health.sh`](../../tool/atlas_health.sh) · [`../../tool/health_check_all.sh`](../../tool/health_check_all.sh) — parallel (3.6×/2.4×): [`../../tool/falsifier_health_parallel.sh`](../../tool/falsifier_health_parallel.sh) · [`../../tool/bridge_health_parallel.sh`](../../tool/bridge_health_parallel.sh) (env switch: `FALSIFIER_HEALTH_TOOL` / `BRIDGE_HEALTH_TOOL`) |
| **Defense ops tools** | [`../../tool/ledger_verify.sh`](../../tool/ledger_verify.sh) · [`../../tool/registry_sign.sh`](../../tool/registry_sign.sh) · [`../../tool/bridge_sha256_rotate.sh`](../../tool/bridge_sha256_rotate.sh) · [`../../tool/atlas_sha256_rotate.sh`](../../tool/atlas_sha256_rotate.sh) · [`../../tool/timeline_rotate.sh`](../../tool/timeline_rotate.sh) |
| **Paper-grade synthesis** (n=6 program) | [`SYNTHESIS_2026-04-26.md`](SYNTHESIS_2026-04-26.md) |
| **Session handoff** (next session start here) | [`NEXT_SESSION_HANDOFF.md`](NEXT_SESSION_HANDOFF.md) · [`SESSION_FINAL_REPORT.md`](SESSION_FINAL_REPORT.md) |
| **Per-file index** (auto-generatable) | [`INDEX.md`](INDEX.md) |

---

## Witness Timeline

### 2026-04-25 — bootstrap (3 ω-cycles)

| File | Topic |
|------|-------|
| [`2026-04-25_omega_cycle_implementation.json`](2026-04-25_omega_cycle_implementation.json) | First ω-cycle: 10-axis `verify_grid` impl, byte-eq fixpoint closure |
| [`2026-04-25_falsifier_integration_omega_cycle.json`](2026-04-25_falsifier_integration_omega_cycle.json) | Falsifier integration design (12 axes → Tier-1/2/3) |
| [`2026-04-25_bridge_tool_jackpot_omega_cycle.json`](2026-04-25_bridge_tool_jackpot_omega_cycle.json) | External-API bridge pattern abstraction (26 axes) |

### 2026-04-26 — atlas-ingest + dedup + falsifier expansion (14 ω-cycles)

| File | Topic |
|------|-------|
| [`2026-04-26_atlas_ingest_omega_cycle.json`](2026-04-26_atlas_ingest_omega_cycle.json) | Bridge → atlas auto-ingest design |
| [`2026-04-26_atlas_ingest_arg_fix_omega_cycle.json`](2026-04-26_atlas_ingest_arg_fix_omega_cycle.json) | Runner-detection + self-path-strip arg fix |
| [`2026-04-26_atlas_ingest_a2_self_path_strip_omega_cycle.json`](2026-04-26_atlas_ingest_a2_self_path_strip_omega_cycle.json) | a2 axis follow-through (escape-hatch flag, 3-path corpus) |
| [`2026-04-26_atlas_ingest_tool_evolution_omega_cycle.json`](2026-04-26_atlas_ingest_tool_evolution_omega_cycle.json) | Single-domain → all-Ω-cycle absorber evolution path |
| [`2026-04-26_phase4_atlas_dsl_v2_and_lens_injection_omega_cycle.json`](2026-04-26_phase4_atlas_dsl_v2_and_lens_injection_omega_cycle.json) | Atlas DSL v2 (M/T/compound) + lens-orchestrator injection |
| [`2026-04-26_dedup_strategy_evolution_omega_cycle.json`](2026-04-26_dedup_strategy_evolution_omega_cycle.json) | Dedup: skip → preserve edge/witness/cross-source |
| [`2026-04-26_cross_repo_absorption_refresh_omega_cycle.json`](2026-04-26_cross_repo_absorption_refresh_omega_cycle.json) | 24h-delta refresh of anima/hexa-lang/n6-arch shards |
| [`2026-04-26_improvement_ideas_omega_cycle.json`](2026-04-26_improvement_ideas_omega_cycle.json) | Aggregate post-session improvement surface |
| [`2026-04-26_F19_F23_falsifier_expansion_omega_cycle.json`](2026-04-26_F19_F23_falsifier_expansion_omega_cycle.json) | i11 auto-spawn → F19–F23 + Mertens labeling discovery |
| [`2026-04-26_F23_resolution_omega_cycle.json`](2026-04-26_F23_resolution_omega_cycle.json) | F23 vacuous-PASS sealed (ec=0+non-empty stdout double-guard) |
| [`2026-04-26_F46_F49_semantic_guards_omega_cycle.json`](2026-04-26_F46_F49_semantic_guards_omega_cycle.json) | F46–F49 atlas semantic-gap guards + convention doc |
| [`2026-04-26_i11_cmd_hardening_omega_cycle.json`](2026-04-26_i11_cmd_hardening_omega_cycle.json) | i11 PRESENCE → VALUE+DOMAIN+GRADE anchor hardening |
| [`2026-04-26_dockerfile_curl_patch_omega_cycle.json`](2026-04-26_dockerfile_curl_patch_omega_cycle.json) | hexa-runner curl/wget/ca-cert patch (7/16 bridges fix) |
| [`2026-04-26_oeis_gw_oom_resolution_omega_cycle.json`](2026-04-26_oeis_gw_oom_resolution_omega_cycle.json) | oeis_live + gw OOM → shell-side payload trim (14/16 → 16/16) |
| [`2026-04-26_uniprot_registry_2fix_omega_cycle.json`](2026-04-26_uniprot_registry_2fix_omega_cycle.json) | uniprot sentinel-classification + axes-as-number 2-fix |
| [`2026-04-26_health_check_productionization_omega_cycle.json`](2026-04-26_health_check_productionization_omega_cycle.json) | 3 health-checks → bash scripts + cron + nexus CLI |

---

## Falsifier ID Map

| Range | Origin | Theme |
|-------|--------|-------|
| **F1–F5** | 2026-04-25 self-seal | n=6 core (σ/α/byte-eq/OEIS/COUNTER overfit guards) |
| **F6–F8** | 2026-04-25 nxs-002 cycle 10 | Cross-bridge pattern (codata/oeis/horizons) |
| **F9** | 2026-04-25 horizons live | TP-8 framework limit (Mars 2g 4-day infeasibility) |
| **F10** | 2026-04-25 cmb live | Cross-bridge fractional gap resonance (αs gap ≈ n_s gap ≈ 3.5%) |
| **F11–F12** | 2026-04-25 | Hubble tension + 3-source corroboration |
| **F13–F18** | — | Reserved / not promoted (see [`F13_F22_candidate_review.md`](F13_F22_candidate_review.md)) |
| **F19–F23** | 2026-04-26 i11 first auto-spawn | Atlas-driven candidates (M3 mertens→mersenne discovery) |
| **F24–F30** | 2026-04-26 | Chemistry / biology bridges (pubchem, uniprot) |
| **F31–F37** | 2026-04-26 | Cross-domain (gaia, lhc, nist, openalex) |
| **F38–F44** | 2026-04-26 | L-prefix bridges (lens / atlas L-entries; L11 [[6,2,2]] CSS code) |
| **F45** | 2026-04-26 | **DECLINED** — cross-bridge 3.5% triplet (collapses to doublet under unit-framing); see [`2026-04-26_F45_decision.md`](2026-04-26_F45_decision.md) |
| **F46–F49** | 2026-04-26 | Atlas semantic-gap guards (sigma/tau notation conflation, self-ref, audit baseline) |

**Current registry total**: 42 entries CLEAN (40 PASS + 2 HIT-as-expected baseline guards F48/F49).

---

## Decision Log

| Date | Decision | Doc |
|------|----------|-----|
| 2026-04-26 | **M3 = mersenne(6) = 7**, not mertens (canonical M(6) = -1) — atlas line 53 relabeled | [`M3_true_definition_audit.md`](M3_true_definition_audit.md) |
| 2026-04-26 | **F45 declined** — triplet → doublet under consistent unit-framing, not statistically anomalous (preserved per raw 73 admissibility) | [`2026-04-26_F45_decision.md`](2026-04-26_F45_decision.md) |
| 2026-04-26 | **hexa-lang atlas SSOT**: nexus-side single origin (4/5 OPT-A), hexa-lang has no own SSOT | [`hexa_lang_atlas_ssot_decision.md`](hexa_lang_atlas_ssot_decision.md) |
| 2026-04-26 | **Dockerfile curl patch** — hexa-runner:latest gains curl/wget/ca-certificates → 7/16 bridges unblocked | [`2026-04-26_dockerfile_curl_patch_omega_cycle.json`](2026-04-26_dockerfile_curl_patch_omega_cycle.json) |
| 2026-04-26 | **oeis/gw OOM fix** — shell-side payload trim (head -c) → remaining 2/16 bridges to 16/16 | [`2026-04-26_oeis_gw_oom_resolution_omega_cycle.json`](2026-04-26_oeis_gw_oom_resolution_omega_cycle.json) |
| 2026-04-26 | **i11 hardening** — auto-spawn anchors PRESENCE → VALUE+DOMAIN+GRADE; --legacy-cmd preserved | [`2026-04-26_i11_cmd_hardening_omega_cycle.json`](2026-04-26_i11_cmd_hardening_omega_cycle.json) |
| 2026-04-26 | **Atlas notation convention** — `sigma = 12` (A) vs `sigma(6) = 12` (B); `sigma(N) = N` self-ref pattern banned | [`../atlas_function_call_convention.md`](../atlas_function_call_convention.md) |

---

## Audit Reports

| File | Scope |
|------|-------|
| [`2026-04-26_falsifier_health_check.md`](2026-04-26_falsifier_health_check.md) | Falsifier registry health (per-entry pass/HIT, drift) |
| [`2026-04-26_bridge_health_check.md`](2026-04-26_bridge_health_check.md) | 16 external-API bridges (curl/wget reachability + payload size) |
| [`2026-04-26_cross_shard_dedup_audit.md`](2026-04-26_cross_shard_dedup_audit.md) | Cross-shard atlas dedup (skip → preserve policy) |
| [`2026-04-26_atlas_semantic_gap_audit.md`](2026-04-26_atlas_semantic_gap_audit.md) | Notation A/B mismatch sweep (21 MISMATCH baseline) |
| [`2026-04-26_cross_bridge_correlation_hunt.md`](2026-04-26_cross_bridge_correlation_hunt.md) | F10-pattern replication across 14 healthy numeric bridges |
| [`cross_repo_dashboard.md`](cross_repo_dashboard.md) | Atlas cross-repo dashboard (Tier-2 i13 generated) |

---

## Defense system (falsifier registry integrity)

Layered defenses against silent registry tampering / drift. Each layer is independently auditable; failure of one does not mask the others (raw 71 — report + rotate, never auto-promote).

| Layer | Mechanism | Live since | Artifact |
|-------|-----------|------------|----------|
| **R1** | Per-entry `cmd_sha256` (each falsifier carries its own command hash; mutation flips the hash) | live | `falsifiers.jsonl` (`cmd_sha256` field) |
| **R2** | Anti-spoof lint (`cmd` must end in sentinel matched by `pass` exactly; rejects literal-only commands) | live | [`../../tool/falsifier_health.sh`](../../tool/falsifier_health.sh) |
| **R3 lite** | Whole-registry SHA256 baseline checked under `--strict` (any drift → warn) | live | `state/falsifier_registry.sha256` |
| **R3 full** | Pre-commit hook auto-rotation — **intentionally retired** by user (commits `e3137be2`+`fa1de8e2` chflags uchg + `582f791e` AI-native deny category); manual rotation via `tool/bridge_sha256_rotate.sh` / `tool/atlas_sha256_rotate.sh` | retired (OS-locked) | n/a |
| **R4** | Forensic ledger — every rotation appended JSONL `{ts, old_sha, new_sha, trigger, prev_hash}` (gitignored, local-only) | live | `state/{falsifier|bridge_sha256|atlas_sha256}_rotation_log.jsonl` |
| **R5 chain** | Hash-chained ledger — each entry includes `prev_hash:sha256(prev_line) or genesis`; forward-propagation forgery detection via [`../../tool/ledger_verify.sh`](../../tool/ledger_verify.sh) `--ledger {falsifier|bridge|atlas|PATH}` | live (registry+bridge+atlas) | `state/*_rotation_log.jsonl` |
| **R5 SSH** | Detached SSH signature stub — skip-by-default until `SIGNING_KEY` env or `git config user.signingkey` set; runbook ready | stub | [`../../tool/registry_sign.sh`](../../tool/registry_sign.sh) + [`R5_SSH_ACTIVATION_RUNBOOK.md`](R5_SSH_ACTIVATION_RUNBOOK.md) |

**Threat model**: an entry's `cmd` is silently swapped → R1 catches the per-entry hash flip. The whole file is replaced → R3 lite catches the baseline drift. A developer adds a legitimate F102+ entry but forgets `shasum -a 256 falsifiers.jsonl > state/falsifier_registry.sha256` → R3 full rotates the baseline at commit time and R4 records the rotation.

---

## Candidate Reviews (falsifier triage drafts)

| File | Range |
|------|-------|
| [`F13_F22_candidate_review.md`](F13_F22_candidate_review.md) | F13–F22 + F23 |
| [`F24_F30_candidate_review.md`](F24_F30_candidate_review.md) | F24–F30 chemistry / biology |
| [`F31_F37_candidate_review.md`](F31_F37_candidate_review.md) | F31–F37 cross-domain |
| [`F38_F44_candidate_review.md`](F38_F44_candidate_review.md) | F38–F44 L-prefix bridges (F45 declined) |
| [`F50_F56_candidate_review.md`](F50_F56_candidate_review.md) | F50–F56 -cont absorption shards |
| [`F57_F63_candidate_review.md`](F57_F63_candidate_review.md) | F57–F63 L4–L6 prefix |
| [`F64_F70_candidate_review.md`](F64_F70_candidate_review.md) | F64–F70 particle_SM coverage gap |
| [`F71_F77_candidate_review.md`](F71_F77_candidate_review.md) | F71–F77 @C/@S deeper |
| [`F81_F87_candidate_review.md`](F81_F87_candidate_review.md) | F81–F87 @M/@T/@R |
| [`F88_F94_candidate_review.md`](F88_F94_candidate_review.md) | F88–F94 @P/@F deeper |
| [`F95_F101_candidate_review.md`](F95_F101_candidate_review.md) | F95–F101 math + bridge [11*] + L4 + n6-arch |
| [`F102_F108_candidate_review.md`](F102_F108_candidate_review.md) | F102–F108 quality-gated (F108 [11!] sole) |
| [`F109_F114_candidate_review.md`](F109_F114_candidate_review.md) | F109–F114 foundations + universality + paradigm |
| [`2026-04-26_cross_engine_integration_audit.md`](2026-04-26_cross_engine_integration_audit.md) | F126–F132 cross-engine (proposal, awaiting user merge) |

---

## How to extend

**Run an Ω-cycle**: surface ≥4 design axes, trial each ≥3 times, write a witness `2026-MM-DD_<topic>_omega_cycle.json` with `{trawl_id, axes_surfaced, fixpoint_marker}`. Append-only per raw 77; never mutate prior witnesses.

**Add a falsifier**: append a JSON line to `falsifiers.jsonl` with `{id, slug, claim, cmd, pass, reason, fix, origin}`. The `cmd` must terminate with a sentinel string matched by `pass` exactly. Run [`../../tool/falsifier_health.sh`](../../tool/falsifier_health.sh) to verify; chain to `falsifier_history.jsonl` via prev_hash + current_hash (raw 77 ledger).

**Add a bridge**: drop a `*_bridge.hexa` under `tool/`, register under `nexus hexa-sim bridge <name>` dispatch, add health-check entry, then pursue atlas-ingest via Phase 1 (`hexa_sim_atlas_ingest.hexa`). Bridge audit grades follow the Tier-1/2/3/REJECT taxonomy from `2026-04-25_bridge_tool_jackpot_omega_cycle.json`.

**Decline a candidate**: write `<ID>_decision.md` with explicit rationale + preserve provenance (raw 73 admissibility — failed promotions are first-class evidence). See F45 for canonical pattern.

---

## hive raw bindings (cross-repo)

| raw | abstraction | local instance |
|-----|-------------|----------------|
| raw 47 | strategy-exploration-omega-cycle | every witness here |
| raw 66 | ai-native-error-message | falsifier `reason`+`fix` trailer |
| raw 68 | fixpoint-byte-eq-closure | F3 + verify_grid byte-eq seal |
| raw 70 | multi-axis-verify-grid | `hexa_sim_verify_grid.hexa` (K=10) |
| raw 71 | falsifier-retire-rule | this directory's whole raison d'être |
| raw 73 | structural-admissibility-paradigm | F45 decline preservation |
| raw 77 | execution-audit-append-only-ledger | `falsifier_history.jsonl` chain |
| raw 80 | execution-sentinel-result-decoding | every falsifier `cmd` exit pattern |
