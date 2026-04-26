# New-Domain ω-Cycle Scout — read-only inventory across 4 repos

**Date**: 2026-04-26
**Scope**: nexus / n6-architecture / anima / hexa-lang
**Method**: read-only `ls`/`find`/`grep` walk + structural density count
**Companion**: META_OMEGA_CYCLE_ROI.md (recommends paper-draft as next axis)
**Constraint**: identify candidates, do **not** displace META_ROI's recommendation

---

## Executive

Of the four repos, three host falsifier-able claim densities comparable to or exceeding hexa-sim's pre-cycle 0 baseline. **n6-architecture/theory** dominates raw claim count (113 prediction-hexas + 23 proof MDs + 98 catalog entries) but its claims are largely *number-theoretic identities already self-verified by their own .hexa harnesses* — low marginal value of an ω-cycle wrapper. **hexa-lang/stdlib + gate** offers the highest-leverage low-cost target: 1156 stdlib LoC + reserved-word + gate-enforcement surface with ~zero existing falsifier coverage, and direct cross-link to hexa-sim's anchor-grep methodology. **anima-engines** has 164 phi-engine .hexa files but they are *narrative/descriptive scaffolds* without measurement contracts — high cold-start cost. Net: hexa-lang stdlib is the only domain where a hexa-sim-pattern ω-cycle would close a real gap; n6 and anima are better served by their *existing* in-repo verifier patterns than by a sibling registry. **The honest read is paper-draft remains the higher-ROI axis** — the scout exists for cron-pattern continuity, not because a comparable target was found.

---

## Per-repo candidate inventory

| Repo | Domain | Claim density (raw) | Anchor-able pattern | Bridge to hexa-sim | Cold-start | ROI estimate |
|------|--------|---------------------|---------------------|--------------------|------------|--------------|
| **nexus** | meta_engine (m3-m9 axes) | 4 dossiers + 14 cycle JSONs | `@P/@C/@F` mature (m3 anchor workflow already done) | direct (same repo) | low (2-4h) | **already saturating** — METADESM ω-cycle done this session |
| **nexus** | roadmap_engine (r2-r8) | 4 dossiers + 9 cycle JSONs | structural; Bayesian ETA / MCTS rollout | direct | low | already saturating |
| **nexus** | cross_engine | 4 cycles + 2 audit MDs | meta-axis; couples m/r/c | direct | done | exhausted this session |
| **n6-arch** | theory/predictions | 113 verify_*.hexa + 98 catalog | self-verifying hexas (each prints PASS/FAIL) | weak — different anchor vocab (constants vs grep-anchors) | medium (need adapter) | **medium-low** — duplicates existing harness; risk of wrapper without finding |
| **n6-arch** | theory/proofs | 23 MDs + breakthrough index | natural-language theorems | weak — claims aren't grep-anchored | high (formalization) | low — better fit for Lean4 (already in repo) |
| **n6-arch** | domains/* (304 dirs) | 362 MDs claim-bearing | each domain has CLAUDE.md+verify.hexa SSOT | medium — could spot-audit drift | medium-high (304 targets) | medium — bulk audit, low per-axis insight |
| **anima** | anima-engines/*_phi.hexa | 164 files | descriptive scaffolds; few invariants | weak — no @anchors, mostly TODO ports | high (need contracts first) | low — scaffolds-not-claims problem |
| **anima** | anima-physics | 50 .hexa files | hardware-bridge oriented; some `fn` density (29/26/19) | weak | medium | medium-low — hardware claims are real but un-anchored |
| **anima** | Mk-XI verdict protocol | 7 docs + 5-tuple PASS predicate | already pre-registered (V0/V1/V2/V3/V_pairrank) | medium — frozen predicates ARE falsifiers | low (~2h adapter) | **medium-high** — pre-reg locks ground truth, ω-cycle could surface drift |
| **anima** | anima-hexad/CDESM | 6 modules (c/d/w/s/m/e) + bridges | Phi-channel laws (Law 22/60/71) | weak — currently descriptor only | high | low |
| **hexa-lang** | stdlib (math/collections/string/...) | 68 .hexa, 1156 LoC, 37 fn | `fn` signatures + reserved-word interaction | **strong** — same lang, same anchor mechanics | low (~1h adapter) | **HIGH** — zero existing falsifier coverage; reserved-word silent-void hazard documented but not enforced |
| **hexa-lang** | gate enforcement | 17 hooks (cmd_gate, lint, post_*, prompt_scan) | enforcement registry JSON | strong | low | **medium-high** — enforcement gaps are real bugs (slot phantom, etc.) |
| **hexa-lang** | grammar.jsonl | 402 entries (spec+pitfalls+autofix) | grammar invariants; pitfalls are pre-falsifiers | strong | low-medium | medium — grammar drift detection |
| **hexa-lang** | doc/* (ai-native, breakthroughs) | 30+ .md ecosystems claims | mostly aspirational | weak | high | low — claim-density disguised as content-density |

**Note on density honesty**: "362 claim-bearing MDs" in n6 reflects naive grep of `claim|invariant|theorem|prediction`; actual *novel* falsifier-able claims (not already covered by in-repo verify.hexa) is likely <10% of that.

---

## Top-3 ranked candidates

### #1 — **hexa-lang/stdlib + gate (silent-void & enforcement gaps)** — ROI: HIGH
- **Rationale**: HEXA_RESERVED.md documents the *silent-void hazard* (1b) where `let spawn = "..."` collapses to void with no exit code. This is a class of real bugs with **zero current falsifier coverage**. Each reserved word in groups Concurrency/Memory/Effects (~20 tokens) becomes one falsifier: "var named X must hard-fail or compile-warn". Cold-start ~1h (the adapter just calls `hexa run` on tiny templates and asserts non-zero exit). Bridge to hexa-sim is direct (same `cmd_sha256` pattern). Falsifier-able count estimate: 20-40 (silent-void candidates) + 10-20 (enforcement registry assertions) + 10-15 (stdlib `fn` signature stability — args/return types frozen). **Total ~40-75 plausible falsifiers, ~half acceptance rate expected** = comparable to hexa-sim early-Phase-B yield.
- **Audience value**: paper-grade — "silent-void hazard taxonomy in a self-hosted lang" is publishable as a tooling note.
- **Risk**: overlap with existing `gate/lint.hexa` work; check before firing.

### #2 — **anima/Mk-XI 5-tuple PASS verdict drift** — ROI: MEDIUM-HIGH
- **Rationale**: Mk-XI verdict protocol (raw#12 frozen) pre-registers 5 axes (V0 max_cosine>0.5, V1 phi_mip>=0.55, V2 SMA_lift>=+0.20, V3 CPS>=3.0, V_pairrank>=0.50). These are **already falsifiers** by construction — frozen predicates with state SSOT paths. An ω-cycle would (a) snapshot current SSOT values, (b) build 5+1 falsifiers that re-run the predicates, (c) lock to cmd_sha256 to prevent post-hoc threshold drift. Cold-start ~2-3h (need to confirm SSOT JSONs are present and re-runnable). Bridge to hexa-sim is medium — different anchor vocab (numerical thresholds vs grep-anchors) but same registry shape would work.
- **Audience value**: HIGH — Mk-XI is the load-bearing claim of anima; defense-layer for it is the highest-leverage anima axis.
- **Risk**: V3 metric was already FALSIFIED (commit c369b375); the predicate set may be in flux. Verify raw#12 still frozen before firing.

### #3 — **n6-architecture/theory cross-prediction triangulation audit** — ROI: MEDIUM
- **Rationale**: 113 verify_*.hexa each self-prints PASS/FAIL but there is **no cross-prediction registry** that detects (a) two predictions claiming contradictory derivations of the same constant, (b) silent SSOT drift (e.g. sigma=12 hardcoded in some, derived in others), or (c) verify-hexas that print PASS on stdout but exit 0 on assertion failure. Cold-start 3-4h (need to scrape all 113, build claim->derivation map, check coverage). Bridge to hexa-sim is medium — would feed into hexa-sim's CONSTANTS axis directly.
- **Audience value**: medium — surfaces a real drift detection gap; not paper-grade alone.
- **Risk**: 113 files is a lot of bulk; quality_audit_v2 PAUSE pattern likely to fire mid-cycle. Constrain scope to the 8 base_constants from `_catalog.json` to stay disciplined.

**Excluded from top-3 (and why)**:
- n6-arch/domains (304 dirs): bulk-audit risk; META_ROI explicitly flags this anti-pattern.
- anima-engines/*_phi.hexa (164): scaffolds-not-claims; cold-start cost dominates.
- nexus meta/roadmap engines: already saturated this session.

---

## Recommendation (1-line)

**Paper-draft remains the correct next axis** (per META_ROI's Phase A>B finding); the 3 candidates above are stockpile-only — fire #1 (hexa-lang stdlib silent-void) only if a future session needs cron-cadence restart with a real blocker, not as displacement of the paper.
