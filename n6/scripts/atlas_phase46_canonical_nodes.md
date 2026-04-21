# atlas_phase46_canonical_nodes.py — canonical constant node proposal

## Purpose

Emit a PROPOSAL JSONL of 8 canonical constant nodes (`n6-const-n`, `n6-const-phi`, `n6-const-tau`, `n6-const-sigma`, `n6-const-sopfr`, `n6-const-mu`, `n6-const-j2`, `n6-const-m3`) with values sourced from `shared/n6/n6_constants.jsonl`. Read-only on `shared/n6/atlas.n6`; integration is a user decision.

## Why it exists (Agent 26 blind-spot analysis)

Agent 24 (commit `4df029d`, audit 2026-04-11) identified top @S symmetry gaps — `n*phi=12`, `n*tau=24`, `n*sigma=72`, `j2*n=144`, `n+sopfr=11`, plus 23 material/bio/music cross-scale bridges — all of which pivot on canonical constant nodes. Agent 26 (commit `4740026`) built Phase 4.5 commute sweep (`atlas_phase45_symmetry.hexa`) and emitted 1427 @S edges, **all within the blowup-d* subgraph**. Zero cross-domain edges surfaced because `atlas.n6` has **no** canonical constant nodes: `grep '"n6-const-' atlas.n6 → 0`. Tokens like `n`, `phi`, `sigma` exist only as operand substrings inside `blowup-d*_ded_*` node summaries; they are never first-class graph pivots. Phase 4.5 cannot bridge n6-const-* ↔ MUS-* / ASTRO-* / L7-* because one endpoint is missing.

## Manual integration path (NOT done automatically)

```bash
# 1. regenerate proposal
python3 shared/n6/scripts/atlas_phase46_canonical_nodes.py \
  > shared/n6/atlas_phase46_canonical_nodes.jsonl

# 2. human review (8 lines + 4 comment headers)
less shared/n6/atlas_phase46_canonical_nodes.jsonl

# 3. user decision — if approved, append to atlas.n6:
cat shared/n6/atlas_phase46_canonical_nodes.jsonl >> shared/n6/atlas.n6

# 4. re-run Phase 4.5 commute sweep to pick up new bridges:
hexa shared/n6/scripts/atlas_phase45_symmetry.hexa \
  > shared/n6/atlas_phase45_symmetry.jsonl
```

## Expected impact

After integration, Phase 4.5 should discover the 5 primary cross-domain commute pairs from Agent 24's audit (`n*phi=12`, `n*tau=24`, `n*sigma=72`, `j2*n=144`, `n+sopfr=11`) plus the 23 material/bio/music canonical bridges — approximately **28 new cross-domain @S edges**, up from the current 0. The proposal itself is infra-only and regenerable; output is git-ignored (see `.gitignore` under the existing phase45/phase6 block).

## Values (from n6_constants.jsonl, NOT classical math defaults)

| token | value | definition |
|-------|-------|------------|
| n     | 6     | foundation primitive |
| phi   | 2     | `euler_totient(6)` — NOT golden ratio 1.618 |
| tau   | 4     | `divisor_count(6)` — NOT 2π |
| sigma | 12    | `divisor_sum(6) = 1+2+3+6` |
| sopfr | 5     | `sum_prime_factors(6) = 2+3` |
| mu    | 1     | `mobius(6)` |
| j2    | 24    | `jordan_totient(6,2)` |
| m3    | 3     | `mertens(6)` per `n6_constants.jsonl`; note `atlas.n6` DSL `@P M3` says 7 — unresolved conflict, `n6_constants.jsonl` wins per Agent 28 rules |
