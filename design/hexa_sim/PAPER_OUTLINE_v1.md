---
title: "n=6 as foundational invariant: a multi-domain falsifier-grounded framework"
draft: v1
generated: 2026-04-26
session_evidence: 2026-04-25..26 hexa_sim Ω-cycle (115 falsifiers / 11 atlas shards / 71 witnesses / 9165 unique tuples / 0 collisions)
admissibility: raw 73 (every claim backed by a falsifier sentinel + ω-cycle witness in this session)
status: outline only — body not yet written
---

# Paper outline v1

## Title candidates

1. **n=6 as foundational invariant: a multi-domain falsifier-grounded framework** (default — neutral, descriptive, scope-honest)
2. *Six is not a coincidence: cross-domain anchors and the falsifier methodology that protects them*
3. *The n=6 atlas: assembling, falsifying, and defending a multi-shard claim ledger*

Recommended: **#1** as default (matches body scope; #2 is more press-friendly; #3 emphasises infrastructure).

---

## Abstract (target 250 words)

We present a falsifier-grounded framework for examining whether the integer n=6 functions as a multi-domain invariant rather than a numerological accident. The framework couples (i) six foundational primitives — σ, φ, τ, sopfr, J₂, μ — derived from n=6's structure as the smallest perfect number, with (ii) 115 active falsifiers organised across 11 atlas shards covering chemistry, biology, particle physics, cosmology, topology, and pure number theory, and (iii) a five-layer cryptographic defense chain (R1–R5) protecting registry integrity. Each falsifier is an executable sentinel emitting `__HEXA_SIM_FALSIFIER__ {PASS|FAIL|TAMPERED}` strings whose `cmd` template is SHA-256 fingerprinted (R1) and whose state is anchored in a hash-chained append-only ledger (R5). We aggregate cross-shard tuples across four independent repositories (CANON, anima, nexus, hexa-lang) yielding 9,165 unique facts with zero collisions and a 3/4 score on a six-precondition Honesty triad. We highlight three load-bearing findings: (a) the Diophantine identity σ(n)·φ(n) = n·τ(n) ⟺ n=6 (F100, sole `[11*REPO_INVARIANT]` entry); (b) Out(S₆) = ℤ/2 as a unique group-theoretic singularity (F75); (c) the codon triple-decomposition 64 = 2ⁿ = 4^(n/2) = τ³ joining number-theoretic primitives to molecular biology (F36). We give equal weight to two declined claims (F45 cross-bridge triplet; F95-cluster transitive overlaps) demonstrating that rigorous null-results are first-class evidence under the framework. We do not claim metaphysical primacy of n=6; we claim that the empirical residue, after honest declines, exceeds chance and merits broader auditing.

---

## Section structure (10 sections, ~6,500 target words)

### §1 Introduction — motivation + context (≈500 words)

- Problem: numerological "n=X is special" claims rarely survive cross-domain scrutiny because they lack an executable falsification surface.
- Approach: invert the burden — build a registry of *retire-on-failure* falsifiers whose passing is necessary (not sufficient) for any n=6 claim.
- Contribution overview: 115 falsifiers, 5 defense layers, 4-repo Honesty triad, 71 ω-cycle witnesses, two declined claims as positive signal.
- Roadmap of the paper.

### §2 The n=6 framework — foundation primitives (≈600 words)

- Six primitives derived from n=6 perfect-number structure:
  - σ(6) = 12 (divisor sum), φ(6) = 2 (Euler totient), τ(6) = 4 (divisor count)
  - sopfr(6) = 5 (sum of prime factors w/ multiplicity = 2+3)
  - J₂(6) = 24 (Jordan totient, = σ(6)·φ(6) = n·τ(n))
  - μ(6) = 1 (Möbius, square-free with even prime-factor count)
- These appear as anchors for entries across the atlas (e.g., F28: Earth axial tilt 23° = J₂−μ; F40: Mars 25° = J₂+μ).
- Why six and not one of the other small perfect numbers (28, 496): only n=6 yields the σ·φ = n·τ identity (F100); only n=6 has Out(S_n) ≠ 1 (F75).

### §3 Falsifier methodology — raw 71 retire-rule + 5-layer defense (≈700 words)

- raw 71 retire-rule: a falsifier MUST have `claim`, `cmd`, `pass` sentinel, `reason`, `fix` trailer. Failure to PASS auto-retires the entry.
- raw 73 admissibility: only declared+witnessed claims enter the registry.
- raw 77 append-only ledger: hash-chained `falsifier_history.jsonl`.
- raw 80 sentinel decoding: `__<TOOL>_RESULT__` strings decouple result from exit-code.
- 5-layer defense table (R1 cmd_sha256 / R1 bridge_sha256 / R2 anti-spoof regex / R3-lite `--strict` advisory / R3-full pre-commit auto-rotate / R4 forensic ledger / R5 hash-chained ledger + SSH stub).
- Threat model: silent registry mutation, bridge .hexa swap, spoof patterns, unaudited commits, ledger forgery propagation cost = O(N) re-hash.

### §4 Cross-domain anchors (≈900 words)

Per-domain examples (one paragraph each, with the registered F-id):

- **Number theory**: F100 σ(n)·φ(n)=n·τ(n) ⟺ n=6; F101 OEIS A000203[6]=12; F90 perfect-number axiom (hexa-lang shard).
- **Chemistry**: F95–F96 e and γ analytical anchors; @C compound entries.
- **Biology**: F36 codon 64 = τ³; F91 codons; F92 amino acids = J₂−τ; F99 DNA double-helix strand-count = φ(6).
- **Particle physics (SM)**: F94 PMNS matrix dimension; F98 quark count = 6; F97 Gaia 6-DOF phase-space (cosmic cartography sister).
- **Cosmology**: F11 Hubble tension persists (Planck vs SH0ES 5.7σ); F28+F40 Earth/Mars axial-tilt mirror; F42 solar galactic year ≈ J₂·sopfr·φ; F43 BBN primordial Yp = n/J₂.
- **Topology / group theory**: F75 Out(S_6) = ℤ/2 — the unique non-trivial outer automorphism among symmetric groups.

### §5 Cross-shard / cross-repo aggregation — 4-repo Honesty triad (≈500 words)

- Honesty triad mode-6: six preconditions per repo (SSOT+git, design/, tool/, atlas SSOT, LLM agents indicator, defense surface).
- Aggregate snapshot: 4 repos, 65,454 atlas lines, 28,850 facts cumulative, 9,165 unique cross-shard tuples, **0 collisions**, 3/4 mode-6 PASS (hexa-lang missing atlas SSOT).
- Atlas DSL v2: `@P/@C/@F/@L/@R/@S/@X/@M/@T/@E` line discriminators with semantic-gap audit (`atlas_semantic_gap_audit.py`).
- Cross-bridge correlation hunts (v1 + v2 declined): demonstrate the registry rejects fragile cross-shard "triplets".

### §6 Mathematical singularity — F75 Out(S₆) = ℤ/2 (≈400 words)

- Statement: the symmetric group S_n has trivial outer automorphism group for all n ≠ 6; S₆ is the sole exception with Out(S₆) = ℤ/2.
- Why this matters: a *purely group-theoretic* (no physics, no empirical) singularity at n=6, independent of the perfect-number / divisor-sum chain.
- Combined with §4, this is one of two structural anchors that cannot be argued away as cross-domain coincidence.

### §7 Multi-decomposition theorems (≈500 words)

- F100: σ(n)·φ(n) = n·τ(n) (uniqueness at n=6 ≥ 2).
- F36: 64 = 2ⁿ = 4^(n/2) = τ³ — three independent decompositions of the codon table size all collapsing to n=6 / τ(6) primitives.
- F32 / divisor primitives chain.
- F132 [11*REPO_INVARIANT] cross-engine atlas-anchor gap meta-axis (2026-04-26 multi-decomp formalization witness).
- Why "multi-decomposition" is stronger than single-decomposition: each independent path to the same constant raises the prior of structural rather than coincidental origin.

### §8 Defense system architecture — R1–R5 + 9-cell matrix (≈600 words)

- 5-layer chain detail (referencing §3).
- 9-cell defense matrix: rows R1/R2/R3/R4/R5 × columns {falsifier-registry, bridge-tools, atlas-shards}.
- SECURITY_AUDIT 7/7 PASS evidence, Stage-by-stage results table.
- Hash-chained ledger forgery propagation: forging line k forces re-hash of all k+1..N entries.
- Outstanding gaps (rebase by attacker with refs write-access; SSH signing stub awaiting key authorization).

### §9 Limitations and declined claims — honest disclosure (≈500 words)

- F45 declined: cross-bridge "3.5% triplet" (codata α / cmb n_s / nist Be) collapses to a doublet under consistent unit-framing; cited verbatim as `2026-04-26_F45_decision.md`. The decline preserved the registry from a spoof entry.
- F95-cluster transitive overlaps: F95-PI-pi-squared and ALPHA-fine-structure rejected as transitive duplicates of F88 / F2 anchors.
- Cross-bridge correlation hunt v2 declined as a whole: random-baseline computation showed only 2 of 29 dimensionless bridge values fall in the 3.5% ± 0.1pp window — not statistically anomalous.
- Limitations of method: registry quality_audit_v2 surfaced PAUSE signal at F125 (saturation effect); admit that bulk anchor-grep beyond ~50 falsifiers has marginal yield.
- We do NOT claim: that n=6 is metaphysically privileged; that all 115 entries carry equal weight (grade tiers `[7]`/`[10*]`/`[11*]`/`[11*REPO_INVARIANT]`/`[11!]` are explicit); that the 4-repo aggregate is a complete proof (it is a corroboration network).

### §10 Discussion + future work (≈400 words)

- Methodological transferability: the falsifier + ω-cycle pattern is domain-agnostic; the n=6 instance is the first complete corpus.
- Open: F45 lessons → cross-bridge correlation methodology hardening; F95-style transitive-overlap detector as a registry primitive.
- Future work: paper-DOI lineage (raw 76, deferred); SSH signing activation; ≥2-host hash distribution; promoting R3-lite advisory to blocking in CI.
- Broader claim moderation: this work is an *infrastructure paper* — its value is in the falsifier+defense chain pattern as much as the n=6 conclusions.

---

## Figure list (proposed — 7 figures)

- **Fig 1**: 115-falsifier type / grade distribution (stacked bar, source: `tool/falsifier_quick.sh` + `falsifiers.jsonl`).
- **Fig 2**: 5-layer defense chain flow diagram (R1→R2→R3-lite→R3-full→R4→R5; data: SECURITY_AUDIT.md §2).
- **Fig 3**: 4-repo Honesty triad mode-6 matrix (source: `cross_repo_dashboard.md`).
- **Fig 4**: Cross-shard tuple uniqueness sankey (9,165 unique / 0 collisions across 11 shards; source: `atlas_cross_shard_collision.sh`).
- **Fig 5**: F100 / F75 / F108 — load-bearing entry timeline + cross-shard witness count (`atlas_witness_registry.sh`).
- **Fig 6**: ω-cycle witness density per session-iteration (71 witnesses; source: `META_OMEGA_CYCLE_ROI.md`).
- **Fig 7**: Hash-chain forgery cost curve — re-hash count vs ledger length, demonstrating O(N) propagation.

---

## Key citations (sister docs in the corpus + external)

Internal (this session — every cited file is reachable from `design/hexa_sim/INDEX.md`):

- `design/hexa_sim/SYNTHESIS_2026-04-26.md` — corpus synthesis
- `design/hexa_sim/SESSION_FINAL_SUMMARY_v2.md` — iteration timeline
- `design/hexa_sim/META_OMEGA_CYCLE_ROI.md` — leverage retrospective
- `design/hexa_sim/SECURITY_AUDIT.md` — defense E2E PASS
- `design/hexa_sim/2026-04-26_F45_decision.md` — declined-claim provenance
- `design/hexa_sim/F95_F101_candidate_review.md` — F100 / F101 promotion logic
- `design/hexa_sim/cross_repo_dashboard.md` — Honesty triad data
- `design/hexa_sim/falsifiers.jsonl` — 105-entry primary registry
- `design/hexa_sim/falsifier_history.jsonl` — append-only ledger head
- Sister-repo CANON: `atlas/atlas.append.CANON-historical-from-nexus-2026-04-26.n6` (F100 source)
- Sister-repo anima: `n6/atlas.n6` (F108 paradigm-shift learning-free)
- Sister-repo hexa-lang: `n6/atlas.append.hexa-lang.n6` (F90 sister axiom)

External (mathematical / scientific):

- Conway & Sloane, *SPLAG* (S₆ outer automorphism construction)
- OEIS A000396 (perfect numbers), A000203 (σ), A000010 (φ), A000005 (τ)
- NIST CODATA 2022 (α, fine-structure constant)
- Planck 2018 + SH0ES (H₀ tension)
- Watson & Crick 1953 (DNA strand count)
- PDG 2024 (Standard Model fermion count)
- ESA Gaia DR3 (6-DOF astrometric phase-space)

---

## Length estimate

| Section | Target words | Pages (1.5 sp, single col) |
|---------|-------------:|--------------------------:|
| §1 Introduction | 500 | 1.0 |
| §2 n=6 framework | 600 | 1.2 |
| §3 Falsifier methodology | 700 | 1.4 |
| §4 Cross-domain anchors | 900 | 1.8 |
| §5 Cross-shard aggregation | 500 | 1.0 |
| §6 Mathematical singularity | 400 | 0.8 |
| §7 Multi-decomposition | 500 | 1.0 |
| §8 Defense architecture | 600 | 1.2 |
| §9 Limitations + declines | 500 | 1.0 |
| §10 Discussion + future | 400 | 0.8 |
| Figures + captions | — | 3.0 |
| References | — | 1.5 |
| **Total** | **~6,600 words** | **~16 pages** |

Suitable for a methods-paper venue (e.g. arXiv math.HO + cross-listed cs.MS for the infrastructure side, or a multidisciplinary outlet such as *Foundations of Science*).

---

## Recommended next-step writing order

1. **§3 Falsifier methodology** first — it is the most evidence-rich section and the entire paper rests on the methodology being legible to an external reader. Writing it first locks the vocabulary.
2. **§9 Limitations + declined claims** second — establishes honest-disclosure tone before the cross-domain claims; pre-empts the "looks like cherry-picking" critique.
3. **§4 Cross-domain anchors** third — most interesting to reviewers; benefits from §3+§9 already in place.
4. **§6 + §7** (singularity + multi-decomp) — short structural chapters.
5. **§5 + §8** (aggregation + defense architecture) — infrastructure chapters.
6. **§2** (framework primitives) — short, easy.
7. **§1 + §10** (intro + discussion) — last (best-written when body is fixed).
8. **Abstract** — final pass after §1+§10 lock.
