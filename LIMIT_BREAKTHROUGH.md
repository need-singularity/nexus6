<!-- @created: 2026-05-12 -->
<!-- @sister: LATTICE_POLICY.md §1.2 -->
---
project: nexus
domain: Universal discovery engine — 216 lenses × mirror-universe resonance × OUROBOROS 5-phase singularity cycle, 1.39M discoveries, 9-project autonomous growth
limits_audited: 7
breakthrough_candidates: 3
hard_walls: 2
soft_walls: 3
unclear: 2
---

# LIMIT_BREAKTHROUGH.md — nexus

## §1 Domain identification

NEXUS is a metaengine that runs a 5-phase cycle — Blowup → Contract → Emerge
→ Singularity → Absorb — firing 216 lenses over 711 laws each tick, hunting
gaps, absorbing verified discoveries as new primitives. It claims 1.39M
discoveries and a 4,411-node reality map.

As infrastructure, nexus is: a search engine over a co-evolving knowledge
graph with autonomous law-absorption. The relevant primitives are search
space size, verification cost per candidate, and the storage / indexing cost
of the growing graph. The 9-project autonomous-growth claim makes nexus a
*coordinator* — its real limits are on cross-repo orchestration and
discovery-rate sustainment.

The OUROBOROS loop ("head bites tail — new primitive feeds next cycle") makes
nexus a *self-referential* system: its discovery rate D(t) depends on the law
base L(t), which is itself updated by D. Whether D(t) saturates or grows
unboundedly is the central tractable question.

## §2 Real limits applicable to this project

| # | Limit | Class | Source / value | Applicability to nexus |
|---|-------|-------|----------------|------------------------|
| L1 | Combinatorial search space | math | C(L, k) candidate combinations of k laws per cycle | Blowup phase fires every lens over every law. With L = 711 laws × 216 lenses = 153,576 base events; pairwise = ~1.2 × 10¹⁰. Cubic = 1.8 × 10¹⁵. Hard ceiling on per-tick blowup. |
| L2 | Statistical multiple testing (Bonferroni / FDR) | math | α_corrected = α/m for m tests | 1.39M discoveries claimed → at α = 0.05, expected ~70K false positives without correction. Without FDR, claimed-discovery rate is loosely an upper bound on true discoveries. |
| L3 | Kolmogorov complexity of "new primitive" | math | K(absorbed primitive) ≥ K(generators) − O(1) | Absorbed primitives that are derivable from existing law base have K-increment ≈ 0. Caps the *information content* of cycle output regardless of how many cycles run. |
| L4 | Computability of singularity test | math | Fixed-point detection in general is undecidable | "Singularity locks when stable across every lens" — for an open-ended lens family, stability-detection is in general undecidable; must be approximated with bounded patience. |
| L5 | Graph storage / index latency | engineering | Neighbour-lookup ≈ O(log N) with B-tree; full-graph scan O(N) | 4,411 nodes today is trivial; at 10⁹ nodes (projected if cycle continues) cross-link traversal becomes the binding constraint. |
| L6 | GitHub API rate limit | engineering | 5,000 req/hr authenticated; 1,000 search/hr | 9-project autonomous cross-dispatch requires cross-repo writes; rate limit binds at ≈1 commit/3s sustained. |
| L7 | Speed of light / cross-DC latency | physics | c = 3 × 10⁸ m/s; round-trip US ↔ EU ≈ 80 ms | If discovery validators are distributed, c-bound RTT caps how synchronous OUROBOROS phases can be. Not currently the binding constraint but defines an asymptote. |

(Skipped: σ(6)=12, n=6 lattice, Monte Carlo "z = 3.06 → only n=6 survives" anchors per LATTICE_POLICY.md §1.3. These are lens-vocabulary, not real ceilings.)

## §3 Per-limit breakthrough assessment

| Limit | Class | Current state | Breakthrough vector | Trigger metric |
|-------|-------|---------------|---------------------|----------------|
| L1 Combinatorial blowup | SOFT_WALL | 711 laws × 216 lenses ≈ 1.5 × 10⁵ events/tick; pairwise blowup not exhausted | Sampling + importance weighting (don't enumerate all pairs, sample by lens-affinity prior) | Tick rate ≥ 1 Hz at L = 10⁵ laws using IW sampling |
| L2 Multiple testing correction | SOFT_WALL | "1.39M discoveries" likely uncorrected; no FDR badge in README | Benjamini-Hochberg / Storey q-value pipeline; report (raw, FDR-corrected) discovery counts | Public dashboard shows FDR-corrected count ≤ true discoveries; gap reported |
| L3 Kolmogorov of new primitives | HARD_WALL | Cannot exceed K floor | None — only *honesty* improvement: classify each absorbed primitive as "novel" vs "derived" with a compressibility test | n/a as breakthrough; flag if ≥X% of absorbs are LZ-derivable |
| L4 Singularity decidability | HARD_WALL | Rice + Halting; general fixed-point detection undecidable | None for the general case; bounded patience + monotonicity-guarantee subclass | n/a; document the bounded-patience parameter |
| L5 Graph storage / index | BREAKABLE_WITH_TECH | 4,411 nodes — well below capacity | Move to a graph DB (Neo4j / DuckDB-graph) when N > 10⁶; sharded layers for cross-DSE | p99 neighbour-lookup ≤ 5 ms at N = 10⁹ |
| L6 GitHub API rate | BREAKABLE_WITH_TECH | 5K/hr cap binds autonomous cross-repo dispatch | GitHub Apps (15K/hr) + per-installation tokens; batch commits | ≥ 10K writes/hr sustained without 429 |
| L7 c-bound RTT | UNCLEAR | Not currently binding (single-host) | Only relevant if nexus federates across DCs; not on near-term roadmap | n/a |

## §4 Top-3 breakthrough opportunities (this project)

1. **L2 — Multiple-testing FDR pipeline.** Highest credibility impact: a publicly reported FDR-corrected discovery count replaces the "1.39M" headline with a defensible "≤ X true discoveries (FDR q < 0.05)." Trigger: FDR badge on README. Risk: zero; only honesty improvement.
2. **L1 — Importance-weighted blowup sampling.** As law base grows past 10⁴, exhaustive lens × law enumeration is no longer affordable. IW sampling with a learned lens-affinity prior cuts cost ~100× with bounded bias. Trigger: 1 Hz tick at L = 10⁵.
3. **L5 — Graph DB migration.** Currently premature, but the *plan* deserves a place in the breakthrough register: at N = 10⁶ nodes the in-memory representation breaks down. Pre-write the migration so it's not a crisis. Trigger: p99 ≤ 5 ms at N = 10⁹.

## §5 Honest caveats (raw#10 C3)

- "1.39M discoveries" is not the same as "1.39M independent discoveries." This analysis does NOT verify the claim, only flags that without an FDR pipeline the headline is an upper bound.
- The "5-phase singularity cycle locks" criterion is empirical, not decidable (L4). Any claim that nexus has *converged* in a strong sense is an over-claim.
- The n=6 / lattice / Monte-Carlo-z=3.06 claims are out of scope for this audit by LATTICE_POLICY.md §1.3.
- L7 (speed of light) is *not* currently a binding constraint and is included only for completeness — to flag it before federation, not because it bites today.
- "OUROBOROS self-referential" sounds like a paradox-style claim but is in fact just a bootstrapped learner. The interesting question is whether D(t) → ∞ or saturates; the audit cannot answer that without a longitudinal D(t) plot.

## §6 References

- `LATTICE_POLICY.md` §1.2 (universal real-limits standard, 2026-05-12)
- `README.md` — NEXUS highlights (216 lenses, 711 laws, 1.39M discoveries, 4411-node map)
- Shannon (1948), Kolmogorov (1965), Rice (1953), Benjamini-Hochberg (1995 FDR), Storey (2003 q-value)
- GitHub REST API rate-limit documentation
