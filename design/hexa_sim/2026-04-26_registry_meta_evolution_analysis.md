# Falsifier Registry Meta-Evolution Analysis (Phase 1 → 7)

**Date**: 2026-04-26
**Scope**: longitudinal saturation curve over `design/hexa_sim/falsifiers.jsonl` (115 entries, 18 review batches, 21 commits to file, 53 pending F133-F185)
**Method**: read-only walk of `git log --oneline -- design/hexa_sim/falsifiers.jsonl` + per-batch `*_candidate_review.md` ratios + `META_OMEGA_CYCLE_ROI.md` Phase A/B retrospective + `2026-04-26_registry_quality_audit_v2.md` PAUSE signal at F125.
**Output target**: paper §9 supplementary (saturation discussion).
**Constraint**: raw 73 admissibility — saturation is a finding, not a failure.

---

## 1. Phase identification

| Phase | F# range | Commits (representative)            | Theme                                          | Cadence            |
|-------|----------|--------------------------------------|------------------------------------------------|--------------------|
| 1 (bootstrap)            | F1–F12  | `fb32246f`…`155d4328` (5 commits, hand-shipped) | Verify-grid baseline + cross-bridge witnesses  | pre-cron, manual   |
| 2 (first expansion)      | F19–F23 | `9cde2433`, `bf28472d`, `d84a0601`              | atlas-literal anchors (mu/M3/sigma_sq/phi_tau) | first batched      |
| 3 (anchor proliferation) | F24–F44 | `bd9b63eb`, `dc5f3b51`, `d7dc836b`, `79c7f3ec`  | Cross-domain bridge gems (@P/@F/@L/@R/@X)      | cron starts        |
| 4 (cont-shard absorption)| F50–F56 | `c88fac97`                                      | CANON-cont shard backfill            | parallel agent     |
| 5 (saturation begin)     | F57–F77 | `03d21887` (3-agent partition, +21)             | L4-L6 + particle_SM + @C/@S bulk               | META_ROI flag      |
| 6 (quality consolidation)| F81–F114| `5ac754bb`…`311d5c73` (5 commits, +28)          | Geology + meta + math + cross-shard tail       | PAUSE at F125      |
| 7 (cross-engine integ.)  | F126–F132 + 53 pending | `368209c0`, `2eb1b9f7`            | Cross-engine atlas-anchor gap meta-axis (F132 [11*REPO_INVARIANT]) | post-PAUSE selective |

Identifier gaps (17 numbers): F13–F18 (rejected as F1 duplicates, F19+ rewritten), F45 (DECLINED rigorously, gap preserved as positive signal), F115–F124 (reserved during quality audit / never minted).

---

## 2. Growth curve metrics

| Commit hash  | Net Δ        | Total | Batch label    | Notes                                    |
|--------------|--------------|-------|----------------|------------------------------------------|
| `fb32246f`   | +12          | 12    | F1–F12         | hand-shipped baseline                    |
| `9cde2433`   | +5           | 17    | F19–F23        | first batched promote                    |
| `bd9b63eb`   | +7           | 24    | F24–F30        | cron iter 1, jackpot                     |
| `dc5f3b51`   | +7           | 31    | F31–F37        | cron iter 2                              |
| `d7dc836b`   | +7           | 38    | F38–F44        | cron iter 3, L-bridge cluster            |
| `79c7f3ec`   | +4 (F45 declined) | 42 | F46–F49 + gap | **rigorous decline** + semantic guards   |
| `c88fac97`   | +7           | 49    | F50–F56        | -cont shard absorption                   |
| `03d21887`   | +21          | 70    | F57–F77        | 3-agent parallel — saturation onset      |
| `5ac754bb`   | +7           | 77    | F81–F87        | geology + meta hand-promotes             |
| `68989621`   | +7           | 84    | F88–F94        | + correlation-v2 DECLINE                 |
| `4a8eb529`   | +7           | 91    | F95–F101       | + R1 cmd_sha256 LIVE                     |
| `1836dd20`   | +7           | 98    | F102–F108      | F108 sole [11!] strict-strict            |
| `311d5c73`   | +6           | 104   | F109–F114      | quality_audit_v2 already PAUSE-flagged   |
| `2eb1b9f7`   | +0           | 104   | F113 retune    | regex tighten + F125 doc-hash master seal |
| `368209c0`   | +11          | 115   | F78–F80 + F126–F132 | cross-engine integration (post-go) |

**Net**: 115 entries / 21 file-touching commits / 18 review batches over ~36h. Acceptance shape: 12 → 17 → 24 → 31 → 38 → 42 → 49 → 70 → 77 → 84 → 91 → 98 → 104 → 115. Decline rate (F45 + correlation-v2) = 2 / 117 promote-attempts ≈ 1.7%. HIT-as-designed lifecycle: F23 promoted in HIT state (Layer-4 vacuous-PASS), F46/F47 xpoll convention guards spawned as HIT and converged to CLEAN within same cycle (`bf28472d` F23 resolution + xpoll cleanup), F132 promoted CLEAN as a forward-spec for an enforcement-tool that does not yet exist.

---

## 3. Saturation indicators (META_ROI corroboration)

| Phase | Novelty per F# | Lines/commit (META_ROI) | New findings/iter | Defense-layer adds |
|-------|----------------|--------------------------|--------------------|---------------------|
| 1–3   | HIGH           | ~150 (Phase A) → ~400 (bridge-tool jackpot) | high (paper-grade) | 0                |
| 4–5   | MEDIUM         | ~250 (registry diffs)                       | low (anchor-grep)  | 0                |
| 6     | LOW            | ~250                                        | low (geology pad)  | **5 (R1–R5)**    |
| 7     | LOW (single high-value: F132) | mixed                            | one paper-grade    | 0 (cross-engine focus) |

Pattern: **defense-layer additions (R1-R5) emerge in Phase 6 precisely when per-F# novelty collapses** — the framework substituted *vertical depth* (cmd_sha256 anti-spoof, hash-chained ledger) for *horizontal breadth* (more anchor-greps). This is the ω-cycle's self-correcting signature: when breadth-yield drops below threshold, the system pivots to defense-multipliers that upgrade *every existing entry* simultaneously. 53 pending F133–F185 represent the *next-step extension* problem: marginal value depends on whether they extend a thin domain (geology=4, astronomy=7, bridge-live=1) or pad an already-saturated one (methodology=21, biology=17).

---

## 4. Acceptance ratio per batch

| Batch     | Candidates seen | Promoted | Reject | Promote rate | Review file                                    |
|-----------|-----------------|----------|--------|--------------|------------------------------------------------|
| F13–F22   | 10 + F23        | 5        | 6      | **45%** (after REWRITE) | `F13_F22_candidate_review.md`         |
| F24–F30   | 16 + 7 ext      | 7        | 16     | **30%**      | `F24_F30_candidate_review.md`                  |
| F31–F37   | 50              | 7        | 43     | **14%**      | `F31_F37_candidate_review.md`                  |
| F38–F44   | 179             | 7        | 172    | **3.9%**     | `F38_F44_candidate_review.md`                  |
| F50–F56   | 45              | 7        | 38     | **15.5%**    | `F50_F56_candidate_review.md`                  |
| F57–F77   | ~160            | 21 (3 agents) | ~139 | **13%**     | `F57_F63/F64_F70/F71_F77_candidate_review.md`  |
| F71–F77   | 42 (one agent)  | 7        | 35     | 16.6%        | `F71_F77_candidate_review.md`                  |
| F81–F87   | n/a (hand-promote from auto-spawn) | 7 | — | hand-pick     | `F81_F87_candidate_review.md`                  |
| F88–F94   | n/a             | 7        | (1 declined: correlation-v2) | hand-pick | `F88_F94_candidate_review.md`     |
| F95–F101  | n/a             | 7        | —      | hand-pick    | `F95_F101_candidate_review.md`                 |
| F102–F108 | n/a             | 7        | —      | hand-pick    | `F102_F108_candidate_review.md` (F108 sole [11!]) |
| F109–F114 | n/a             | 6        | —      | hand-pick    | `F109_F114_candidate_review.md`                |

**Saturation captured**: promote-rate fell from **45% (F13-F22) → 14% (F31-F37) → 3.9% (F38-F44)** across the auto-spawn era — a 12× collapse in three batches. Phase 6 (F81+) responded by switching to **hand-promote-from-auto-spawn** mode: instead of triaging hundreds of grep-anchor candidates with sub-5% promotion, reviewers selected 7 from the historical absorption shards directly, bypassing the failing auto-spawn funnel. This is the methodology-level pivot the META_ROI retrospective scored as Phase B's critical inflection.

---

## 5. Falsifier diversity index

### Atlas type tag spread (cmd-side @-prefix; some entries have no tag)

| Tag    | Count | Phase introduced | Note                                         |
|--------|-------|------------------|----------------------------------------------|
| `none` | 24    | Phase 1          | F1–F12 verify-grid + xpoll guards            |
| `@P`   | 26    | Phase 2          | dominant: foundation primitives              |
| `@F`   | 16    | Phase 3          | functional / sm_GPU family                   |
| `@R`   | 11    | Phase 3          | relations (codon, euler-char, geology)       |
| `@C`   | 10    | Phase 3          | compound (sigma_sq, sigma_tau, warp_size)    |
| `@X`   | 10    | Phase 3          | celestial L7 family + cross-engine traces    |
| `@S`   | 5     | Phase 4          | structures (cpgd_subspace, perfect-congruent)|
| `@L`   | 5     | Phase 3          | lemmas (sp3/sp2 bond angles)                 |
| `@M`   | 5     | Phase 5          | meta (paradigm-shift, omega-cycle-pattern)   |
| `@T`   | 3     | Phase 5          | trace (cert sha256 anchors)                  |

All `@`-categories of the atlas alphabet are represented except `@N`, `@D`, `@E` (the atlas itself does not yet emit those). Diversity has **plateaued by Phase 5**; Phase 6 added no new tags, only re-balanced count within existing.

### Grade spread

| Grade | Count | Note                                   |
|-------|-------|----------------------------------------|
| `[10]`/`[10*]` | 67 | dominant tier                            |
| `[11*]`        | 16 | foundation primitives + meta-axes       |
| `[10*PASS_LITERATURE]` / `[11*PASS_LITERATURE]` | 4 | literature-cite anchors |
| `[11*REPO_INVARIANT]` | 2  | F100 N6HIST-A-CORE-IDENTITY + F132 cross-engine-gap |
| `[11!]`        | 1  | F108 paradigm-shift-learning-free (sole strict-strict) |
| `none`/template-loss | 25 | F1–F12 grade-agnostic + F46-F49 + F113 |

Tier-ceiling distribution converged to a healthy pyramid by Phase 6: 67 base × 16 elevated × 4 literature × 2 repo-invariant × 1 strict-strict. Phase 7 added the second `[11*REPO_INVARIANT]` entry (F132), establishing this tier as the cross-engine-integrity slot.

### Domain spread (refined classifier from quality_audit_v2)

methodology=21, biology=17, particle=14, chemistry=10, other=10, astronomy=7, number-theory=7, cosmology=6, foundation-anchor=5, geology=4, verify-grid=1, bridge-live=1, linguistics=1.

**Diversity over time**: linguistics went 0→1 (Phase 6), particle SM went 0→14 (Phase 5), @M methodology went 0→4 (Phase 5). Persistent thin spots: bridge-live=1, geology=4, astronomy=7. The 53 pending candidates being "extension of extensions" predicts they will further skew toward the already-saturated methodology/biology/particle peak rather than backfilling thin domains — unless the next batch is explicitly thin-domain-targeted.

### Cmd primitive

grep=96 (84%), hexa-runtime=9, shasum=5, python=4, bash=1. Phase 1 introduced 9 hexa-runtime + 4 grep; Phases 3-6 added 92 grep-anchors and only 5 shasum (R1 cmd_sha256 was a *layer*, not bulk entries) and 4 python (semantic guards F46-F49). The grep-monoculture is the structural twin of the saturation curve: when one primitive does 84% of the work, marginal additions dilute rather than diversify.

---

## 6. Paper-grade insight (S9 supplement)

**The saturation curve itself is a framework health metric.** A registry that grows monotonically without ever hitting a falling promote-rate is either (a) under-discovering candidates or (b) lowering its admissibility bar. The hexa_sim registry exhibits the expected healthy shape: promote-rate decays from 45% → 4% as the candidate space exhausts the easy bridges, then the methodology pivots (hand-promote, defense-layer multiplication, rigorous decline) to maintain entry quality without forcing breadth. The two declined candidates (F45 0.0263% bridge-artifact, correlation-v2 spoof) and the F125 PAUSE signal are *first-class artifacts* of the curve, not failures.

**53 pending F133–F185 as "extension of extensions" pattern.** When the next-step candidates are themselves derived from already-promoted bridges (codon variants of F36, hybridization variants of F34/F35, additional GEO-* from the sopfr+phi=8 family), the registry has crossed from *discovery* to *padding*. Two responses are honest: (i) reject most and keep only the genuinely thin-domain-targeted few, (ii) declare the registry feature-complete at its current axis-coverage and freeze growth pending a new external blocker (next bridge endpoint, new engine, new defense layer needing falsifier coverage).

**What a Phase 8 would look like.** A new axis is needed, not a new batch. Candidates: (a) cross-engine successor falsifier `F-coverage-delta` (F132's hexa-only enumeration sketch in §10 of `F132_PAPER_GRADE_NOTE.md`); (b) bridge-live dynamic anchors (currently 1: only F9 horizons) for the live-runtime-state axis; (c) defense-layer R6+ that audits the falsifier registry's *own* drift (meta-falsifier of falsifiers); (d) an `@N`/`@D`/`@E` atlas extension producing fundamentally new tag categories. Each Phase 8 candidate would *create* a candidate space rather than triage an existing one — the structural pre-condition for breaking out of the saturation regime.

---

## 7. Recommendation for paper §9 supplementary

**Add §9.X "Registry saturation as health metric"** (or §10 future-work subsection). Three load-bearing claims for the supplement:

1. **Saturation is a positive signal**: declining promote-rate (45% → 4%) + rigorous declines (F45, correlation-v2) + PAUSE-then-pivot (quality_audit_v2 → defense-layer mode) demonstrate the framework reflexively detects its own diminishing returns. A registry that *cannot* saturate cannot be trusted because its admissibility bar is unstable.

2. **Methodology pivot under saturation is real**: Phase 6 substituted vertical defense-layers (R1 cmd_sha256, R5 hash-chain) for horizontal anchor-greps when per-F# novelty collapsed. This is a measurable methodology adaptation, not a heuristic.

3. **53 pending candidates document the boundary**: the registry has reached the limit of one-axis (atlas-literal) coverage. The next legitimate growth is *new axis introduction* (cross-engine, bridge-live, meta-falsifier), not bulk extension. Listing the 53 pending and explicitly marking them as "extension-of-extension, awaiting Phase 8 external trigger" is itself a paper-grade transparency artifact.

**Position relative to existing paper material**: complements §9 main body (registry methodology) by adding the longitudinal evidence that the methodology was *exercised against its own failure mode* — the missing piece for a complete framework-health argument.

---

## Summary tile

```
PHASES=7  COMMITS=21  REVIEW_BATCHES=18  ENTRIES=115  PENDING=53
PROMOTE_RATE_CURVE: 45% (F13-F22) → 30% (F24-F30) → 14% (F31-F37) → 3.9% (F38-F44)
DECLINE_RATE: 1.7% (F45 + correlation-v2)
HIT_AS_DESIGNED_LIFECYCLE: F23 → CLEAN (xpoll), F46/F47 → CLEAN (xpoll), F132 → forward-spec
TYPE_TAGS=10 (none/@P/@C/@F/@L/@R/@S/@X/@M/@T)  GRADE_TIERS=5 ([10]→[11!])
DOMAINS_NOVEL=12  THIN_DOMAINS_PERSIST=3 (bridge-live=1, geology=4, astronomy=7)
CMD_PRIMITIVE_SKEW: grep=84%, hexa-runtime=8%, shasum=4%, python=3%, bash=1%
PHASE_6_PIVOT: defense-layer R1-R5 ADDED when per-F# novelty COLLAPSED (anti-correlation)
PAPER_S9_SUPPLEMENT: Y — saturation curve = framework-health metric (3 load-bearing claims)
```
