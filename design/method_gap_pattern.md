# Cross-BT Method-Gap Pattern

> Deployed 2026-04-25 from CANON session.
> Source: `reports/sessions/omega-meta-prediction-cross-bt-method-gap-2026-04-25.md` + `omega-meta-prediction-bt541-method-gap-2026-04-25.md`.

## The pattern

For each unresolved Millennium-grade conjecture analyzed in the CANON session, a **method gap** structure was identified — a region where the conjecture lives that is unreachable by complementary technique families (Family A construction-side + Family B rigidity-side).

## 6/6 coverage

| BT | Family A (construction) | Family B (rigidity) | Method gap | Topology |
|---|---|---|---|---|
| 541 RH | Explicit / numerical | Operator-theoretic (Hilbert-Pólya) | operator-instantiation absent | single-family |
| 542 P=NP | Specific algorithms | 4-barrier lower bounds | barrier intersection ∩ NP | between-families |
| 543 YM | Lattice numerics | Continuum axioms | bridge empty | between-families |
| 544 NS R1 | Convex integration | CET 1994 / Onsager | strip (α_BV, 1/3) | between-families |
| 545 Hodge | Explicit cycles | Counterexamples | explicit↔general rational | between-families |
| 546 BSD | Heegner rank≤1 | Rank≥2 partial | rank ≥ 2 unconditional | between-families |

## Common-pattern statement

> Method gaps are **products of incomplete technique-pair coverage** — each unsolved conjecture has a Family A (construction-side, populating part of the answer-space) and a Family B (rigidity-side, retiring part); the conjecture lives in the gap between their reach-images.

## Application to future sessions

When attacking an open conjecture:
1. Identify Family A and Family B.
2. Locate where each technique exhausts.
3. The gap is where the conjecture genuinely lives.
4. Closing the gap requires technique that bridges A↔B, not technique inside A or B.

## Lineage
Verdict: PATTERN_STRONGLY_GENERAL (5/6 + BT-541 caveat). See parent reports for full justification.
