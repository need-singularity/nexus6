# New-Domain ω-Cycle Scout v2 — 4th-5th candidate hunt (post-3 done)

**Date**: 2026-04-26
**Predecessor**: `2026-04-26_new_domain_scout_omega_cycle.md` (commit 3a783e89) shipped 3 candidates → all 3 fired (hexa-lang stdlib #1, anima Mk-XI #2, n6-arch cross-prediction #3)
**Session ω-cycle inventory at scout time**:
- 1 main domain (hexa-sim: 115 falsifiers + 9-cell defense + paper draft v3 / 2207 LoC)
- 3 sibling-domain ω-cycles (stdlib + Mk-XI + n6 cross-prediction)
- 4 cross-engine deeper plans (m3 / m5 / r4 / r10) — already shipped this session
- 46 F# candidates pending user-go
**Method**: read-only `ls`/`find`/`grep` walk + structural density count, no writes outside this doc
**Constraint**: do not displace cross-engine completion or paper-draft polish if both candidates are marginal

---

## Executive

Scout v1 enumerated 13 candidates and ranked 3 as fireable; all 3 fired this session. The honest read of v2: **the hexa-sim sibling-axis surface is now structurally exhausted at HIGH-ROI tier**. Of the 8 v2 candidates, only **2 plausibly clear MEDIUM-HIGH** and they share an unflattering trait — both are *meta-instrumentation of hexa-sim's own infra* (falsifier-registry meta-evolution + bridge-fallback hardening), not genuinely new domains. The remaining 6 are either (a) covered by Phase-A trawls already (self-format Ω-cycle 5-cycle aggregate done 2026-04-25, hive-runtime SIGKILL/anima-sub all touched), (b) bulk-audit anti-pattern targets META_OMEGA_CYCLE_ROI explicitly flags, or (c) zero-density (n6shared has 5 .hexa files; bridge_l1/P_S_projector are conceptual labels not directories). **Saturation point is reached** for "new domain" framing — the productive frontier is *depth on existing sibling-axes* (e.g. promote #2's Mk-XI 5-tuple from snapshot to longitudinal-drift run, or wire #1's 4 stdlib HITs to actual hexa-lang fixes), not breadth into a 4th domain.

---

## 8-candidate matrix

| # | Candidate | Claim density (anchor-able) | Cold-start (40× scout pattern) | Bridge to hexa-sim | Paper-grade? | ROI |
|---|-----------|----------------------------|--------------------------------|--------------------|--------------|-----|
| 1 | n6shared (cross-repo lib) | **5 .hexa total** (n6-arch only; nexus has none) | 1h scout → 40h impl, no payload | weak (no @anchors, no SSOT JSON) | no | **LOW** — empty surface |
| 2 | anima sub-domains (bridge_l1 / P_S projector) | **0 dirs found**; refs are conceptual not code | unknown — pre-impl | n/a | n/a | **LOW** — phantom target |
| 3 | hexa-lang gate enforcement (raw rule registry) | hive/tool ~65 .hexa lints + 4 raw_* | 1h | strong (hive-tool already calls hexa) | yes (raw#66 enforce-layer ladder is publishable) | **MEDIUM** — overlaps active raw#37/38/39/43/45/66 work |
| 4 | n6-arch domains/* (10 dirs / 304 sub / 362 MDs) | 362 claim-bearing MDs (naive grep); ~10% novel | 4-6h (bulk) | medium (CONSTANTS axis only) | no | **LOW** — META_ROI explicitly flags bulk-audit |
| 5 | nexus self-format (1327 violations) | **already done** 2026-04-25 5-cycle aggregate (8 repos audited, lock-in B done) | n/a — exhausted | n/a | done (severity field gap surfaced) | **LOW** — saturation |
| 6 | hexa runtime SIGKILL on Mac (memory pressure) | 4 trawl mentions; OS-level not lang-level | 2h (need to repro under instrumented load) | weak (different layer) | maybe (Plan B spawn-safety story) | **MEDIUM-LOW** — covered by hexa-runner Mac landing (raw 44) |
| 7 | bridge fallback hardening (16 bridges → all OFFLINE-FALLBACK std) | 9 sim_bridge dirs (not 16) / 11 files use API/HTTP / 2 use OFFLINE pattern | 2-3h | **strong** (same bridges hexa-sim depends on) | yes (offline-deterministic-replay is publishable) | **MEDIUM-HIGH** — meta on hexa-sim infra |
| 8 | falsifier registry meta-evolution (F1-F178 directional analysis) | 115 falsifiers + 3 history entries; 18 review MDs (F13-F114 in 7-batch slices) | 2h (already partially in registry_quality_audit_v2) | **strong** (registry IS hexa-sim) | yes (F# saturation pattern is the paper's S9 gap) | **MEDIUM-HIGH** — meta on hexa-sim infra |

**Density-honesty notes**:
- "16 bridges" in prior context is incorrect — actual count is **9** sim_bridge dirs (anu_stream/anu_time/atlas_anu_corr/bostrom_test/godel_q/multiverse/ouroboros_qrng/qpu_bridge/sr_harness). Multiverse is large (1022 files) but mostly result-data, not source.
- "1327 violations" self-format work is already 5-cycle-done (commit cluster 2026-04-25, lock-in B / docs/X.doc convention shipped, severity field gap recorded).
- bridge_l1 / P_S_projector exist in Mk-XI conceptual docs but **not as filesystem entities** — searching `find / -name bridge_l1` returns 0; they would require new code, not scout.

---

## Top-3 ranked

### #1 — Bridge fallback hardening (offline-determinism standard) — ROI: MEDIUM-HIGH
- **Rationale**: 11 of 9 bridges hit external APIs (ANU QRNG primary), only 2 implement OFFLINE-FALLBACK explicitly. Network outage → silent stochasticity → falsifier flake. Standardizing OFFLINE-FALLBACK to a contract (cmd_sha256 of cached payload + freshness window + degraded-mode marker in result JSON) closes a real determinism gap that *currently makes 9 hexa-sim falsifiers non-replayable on offline CI*. Cold-start ~2-3h.
- **Bridge to hexa-sim**: direct — same registry, same cmd_sha256 pattern, drops straight into R1-R5 ledger.
- **Risk**: scope creep into multiverse/ result-data (1022 files); cap at the 9 source dirs.
- **Paper-grade**: yes — "deterministic offline-replay contract for stochastic external-API falsifiers" is a clean methods-paper subsection.

### #2 — Falsifier registry meta-evolution (F1-F178 directional analysis) — ROI: MEDIUM-HIGH
- **Rationale**: 115 falsifiers + 18 7-batch review MDs let you actually *plot the saturation curve* — HIT rate per batch, axis-overlap drift, decline-justification length over time. registry_quality_audit_v2 already gestured at this; promoting it to a longitudinal study with predicted-vs-actual saturation closes META_ROI's "registry approached saturation" observation with numbers, not vibes. Cold-start ~2h (the data is in falsifiers.jsonl and the 18 review MDs).
- **Bridge to hexa-sim**: maximal — this *is* hexa-sim looking at itself.
- **Risk**: navel-gazing; cap output at 1 figure + 1 table + a saturation-prediction falsifier (the registry produces its own meta-falsifier).
- **Paper-grade**: yes — slot into PAPER_S9_LIMITATIONS as a quantified honesty section.

### #3 — hexa-lang gate enforcement (raw rule registry) — ROI: MEDIUM
- **Rationale**: hive/tool/* hosts ~65 lint .hexa + raw_cli_bin + 4 raw81 monitors. raw#66 enforce-layer-ladder is live but the *audit of which raws have which enforcement-layer* (os-level / hive-agent / advisory) has no falsifier coverage. ω-cycle would scrape hive/tool/, classify each by layer, and emit a falsifier per missing layer-coverage cell. Cold-start ~1h.
- **Bridge to hexa-sim**: medium — different domain (hive vs nexus) but same anchor mechanics.
- **Risk**: heavy overlap with active raw#37/38/39/43/45/66 work; would need user-go to avoid stomping in-flight blockers.
- **Paper-grade**: marginal — better as a hive-internal audit than a paper section.

---

## Cross-domain saturation assessment (honest)

7 sub-domains already covered this session: m3 / m5 / r4 / r10 cross-engine + hexa-lang stdlib + anima Mk-XI + n6-arch cross-prediction. The **structural surface** for "sibling-axis ω-cycle" framing is:
- nexus engine axes (m/r/c) — done.
- adjacent-repo paper-anchor axes (n6/anima/hexa-lang) — done.
- cross-engine deeper-integration — done.

What v2 turned up that is *not* already in those 3 buckets:
- **infra-meta** (bridges + falsifier registry) — bucket 4, **genuine**, but it is "hexa-sim looking at itself" rather than a new domain.
- **enforce-layer audit** (hive raws) — bucket 5, **genuine but in-flight conflict** with raw#37+38+39+43+45+66 work.
- everything else — phantom (bridge_l1), exhausted (self-format), or anti-pattern (bulk domain audit).

**Verdict**: "4th new domain" framing is a forced fit. The two MEDIUM-HIGH items (#1 bridge-fallback, #2 registry meta-evolution) are honestly *Phase-C consolidation of hexa-sim*, not new domains. Re-framing them as "hexa-sim depth" is more accurate than "new domain #4".

---

## Striking finding

**The scout itself surfaced one** — `find` against the 9 sim_bridge dirs shows only 2/11 API-hitting bridges implement OFFLINE-FALLBACK explicitly. The remaining 9 fall through to silent stochasticity on network outage, which means **9 hexa-sim falsifiers are formally non-deterministic-replayable on offline CI today**. This is a real gap that the paper draft v3 does not currently caveat in S9_LIMITATIONS — and it is exactly what #1 above would close. The scout's most useful output is *not* a 4th domain recommendation; it is this defect-discovery.

---

## Recommendation (1-line)

**Cross-engine completion + paper-draft S9 update with the 9-bridge offline-determinism caveat first; only then fire #1 (bridge-fallback hardening) as Phase-C depth, not as a 4th new domain — saturation point on "new domain" framing is reached.**
