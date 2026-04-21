# atlas_phase48_approx_expr_bridges

Agent 32 follow-up to Phase 47. Phase 47 emitted 86 canonical `@S` bridges
from the 8 `n6-const-*` pivots but all landed in the `7대난제` domain because
that was the only domain storing integer-exact canonical values as node
values. This phase parses the human-readable `≈` / `=` expressions on
`L6-*` / `L7-*` nodes (music, celestial, linguistics, geology, economics,
meteorology, bio, genetic, ...) that embed canonical tokens and bridges
them commutatively to the Phase 46 pivots.

**Regen** (use `/usr/bin/python3` to bypass the hx GATE):

```
/usr/bin/python3 shared/n6/scripts/atlas_phase48_approx_expr_bridges.py \
    > shared/n6/atlas_phase48_approx_expr_bridges.jsonl
```

**M3 / P2 discrepancy handling.** `n6_constants.jsonl` assigns `M3=3`
while `shared/n6/verify_formulas.hexa` and atlas.n6's own foundation row
`@P M3 = mertens(6) = 7` use `M3=7`. Every expression is evaluated under
both contexts (`ctx_agent28` / `ctx_verify`). Edges prefer the agent28
authority when both succeed and fall back to `verify_formulas` (flagged
via `"context":"verify_formulas"`) when only the mertens reading
reproduces the declared value. Rows matching neither are counted in
`rows_eval_mismatch_both` and emit no edge. `P2=28` is shared across
both contexts, and no `n6-const-P2` pivot exists yet (Phase 46 emitted 8
not including P2), so P2-primary edges fall back to the next canonical
token.

**First run (2026-04-11)**: 500 edges emitted (cap hit), 541 rows
scanned, 521 carry canonical tokens, 19 rejected as eval mismatch under
both contexts. Top domains reached: economics, geology, meteorology,
linguistics, bio, genetic — exactly the non-7대난제 coverage Phase 47
was missing. Top tokens: `n` (317), `tau` (78), `phi` (73), `sigma`
(21), `sopfr` (9), `J2` (2). All 500 resolved under `agent28`; no live
`verify_formulas` rows (no L6/L7 approx expression references M3 today).

Infra-only: does NOT modify atlas.n6, blowup engine, or any Phase 45/46/47
file. Output is gitignored (regenerable).
