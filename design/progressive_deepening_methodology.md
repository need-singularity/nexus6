# Progressive Deepening Methodology

> Deployed 2026-04-25 from CANON session.
> Source: `reports/sessions/omega-meta-synthesis-progressive-deepening-pattern-2026-04-25.md` + `omega-meta-cumulative-session-methodology-2026-04-25.md`.

## When to apply

When a sketch / lemma / construction returns OBSTRUCTION_DOCUMENTED, apply progressive deepening rather than retracting or retrying with cosmetic changes.

## 5-pattern elements

1. **Obstruction identification**: name the specific step / inequality / construction that fails.
2. **Honest documentation**: record as OBSTRUCTION_DOCUMENTED, with verdict-grade table.
3. **Structural reframe**: choose a structurally different framework (not parameter permutation).
4. **Sanity check**: verify new framework against a known regime before extending.
5. **Cumulative learning**: each level's failure constrains the next level's design.

## 8-step omega-cycle workflow

1. Define the problem space.
2. Pre-register falsifiers BEFORE generating candidates.
3. Generate candidates from heterogeneous families.
4. Validate with native-paired discriminators.
5. On OBSTRUCTION: progressive deepening (5-pattern above).
6. On cross-evidence: localize obstruction (e.g., 3-pillar pattern).
7. On meta-claim drift: cross-cell entries refine.
8. Maintain honesty triad (promotion-counter / write-barrier / no-fabrication).

## Portable statement

> When a proof attempt fails, localize the obstruction to a specific step, document at face value, reframe at the structurally different ingredient implicated, sanity-check the new framework against a known regime, and let cumulative diagnosis map the problem's difficulty even when no positive bound emerges.

## R1 L1→L4 case study (NS Onsager-Hölder)

| Level | Framework | Obstruction | Sanity check |
|---|---|---|---|
| L1 | BV-2019 schematic | inequality form wrong (μ_q missing) | — |
| L2 | μ_q-tracked BV | building block wrong (L²-class) | α_BV: PASSES |
| L3 | BCV-2021 reframe | template missing temporal-singular leg | α_BCV: FAILS (deeper) |
| L4 | CET 1994 contradiction | regime mismatch (strip unreachable) | regime: FAILS |

## Anti-patterns

- Retrying same approach with cosmetic changes (not progressive).
- Declaring INCONCLUSIVE when obstruction is identifiable.
- Abandoning after L1 (insufficient deepening).

## Application targets

- Any sketch returning OBSTRUCTION_DOCUMENTED.
- Cross-BT lower-bound problems.
- Theoretical-CS complexity barriers (4-barrier stacking confirms pattern).
