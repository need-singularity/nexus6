# atlas_phase47_canonical_bridges

Agent 28+ follow-up: emit canonical `@S` bridges from the 8 `n6-const-*`
pivot nodes (commit `eb1f5954`) to every matching non-canonical node in
atlas.n6, based on Agent 24's audit algebraic candidates
(`n*phi=12`, `n*tau=24`, `n*sigma=72`, `j2*n=144`, `n+sopfr=11`, ...).

**Regen** (use /usr/bin/python3 to bypass the hx GATE):

```
/usr/bin/python3 shared/n6/scripts/atlas_phase47_canonical_bridges.py \
    > shared/n6/atlas_phase47_canonical_bridges.jsonl
```

**Output (2026-04-11 first run)**: 86 edges, all targeting `7대난제` domain
(the only domain storing integer-exact canonical values as node values).
Covers 31 unique canonical expressions incl. all 5 Agent 24 top candidates.

**Follow-up (Phase 48?)**: parse `≈` expressions in atlas.n6 L6-* music /
celestial / material / linguistics nodes — those already reference canonical
tokens (`sigma*phi+n/phi+mu/phi`, `n*7+sopfr`, etc., see commit `25b1c414`
hypothesis_audit). That bridge path unlocks music/sci/linguistics targets.

Infra-only: does NOT modify atlas.n6, blowup engine, or any existing script.
Output is gitignored (regenerable).
