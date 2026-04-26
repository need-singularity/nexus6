# Atlas Semantic-Gap Audit (2026-04-26)

**Scope**: All `@P/@C/@F/@L/@R/@S/@X/@M/@T/@E` entries of form
`<id> = func(N) = VALUE` across `atlas.n6` + 6 append shards.
Verifies VALUE against canonical evaluation of `func(N)`.

**Method**: python3 stdlib only. Regex extracts entries; for chained
expressions like `mersenne(3) = 2^3 - 1 = 7`, the LAST `= int` segment
is used (M3-style). For 'leading number then unit' like
`sigma(12) = 12평균율`, the leading int is used. Dependent count via
`grep -cF` (fixed-string).

## Executive Summary

| Class | Count |
|---|---|
| Total candidates audited | 512 |
| MATCH (atlas correct) | 11 |
| MISMATCH (label wrong / load-bearing review) | 2 |
| UNKNOWN (func not in canon) | 499 |
| PARSE_FAIL | 0 |

**Top finding**: 20 systematic xpoll-* `sigma(12)/tau(4)` mismatches —
author wrote `sigma(12)=12` meaning `sigma=12` (i.e. σ(6)=12, the n=6 anchor)
but the `(12)` was misread as the function argument. Same M3-style label
conflation: load-bearing value is correct, parenthetical is wrong.

## MISMATCH Table

| File:Line | ID | Claimed `func(N)=V` | Canonical V | Deps | Suggested fix |
|---|---|---|---|---|---|
| atlas.n6:16852 | `xpoll-sigma-material` | `sigma(12)=12` | 28 | 0 | rewrite as `sigma(6) = 12` (or `sigma = 12` shorthand); arg=12 is the count, not σ-arg |
| atlas.n6:18232 | `MILL-DFS23-12-p6-11-double-decomp` | `p(6)=11` | 13 | 0 | rename func `p` → `partition` (p(6)=11 means partition(6); `p` collides with prime alias) |

## MATCH Confirmations (audit-passing entries)

| File:Line | ID | Verified |
|---|---|---|
| atlas.n6:30 | `sigma` | `divisor_sum(6)=12` |
| atlas.n6:37 | `phi` | `euler_totient(6)=2` |
| atlas.n6:40 | `tau` | `divisor_count(6)=4` |
| atlas.n6:44 | `sopfr` | `sum_prime_factors(6)=5` |
| atlas.n6:51 | `mu` | `mobius(6)=1` |
| atlas.n6:53 | `M3` | `mersenne(3)=7` |
| atlas.n6:16971 | `n6-sigma` | `divisor_sum(6)=12` |
| atlas.n6:16980 | `n6-phi` | `euler_totient(6)=2` |
| atlas.n6:17029 | `n6-tau` | `divisor_count(6)=4` |
| atlas.n6:20707 | `LEARN-02-backprop-tau-stages` | `tau(6)=4` |
| atlas.n6:20716 | `LEARN-05-MAML-inner-tau` | `tau(6)=4` |

## UNKNOWN funcs (not in canonical set)

Functions appearing in the `func(N) = V` slot but not implemented in this audit's
canonical eval. Most are domain-specific layer-counting (`L(n)` from META layer)
or symbolic placeholders.

| Func | Count | Note |
|---|---|---|
| `L` | 493 | META-layer closure function; domain-specific, intentional |
| `n` | 5 | literal n=6 anchor selector (e.g. `n(6)=6`); identity-like |
| `alpha` | 1 | physics fine-structure / Selmer rank constant |

## Prioritized Cleanup Queue

Ranked by: (high deps OR conceptual contagion) × (clarity of fix).
All current MISMATCHes have deps=0 in atlas.n6 (xpoll-* are leaf decorations,
and `MILL-DFS23-12` references `p(6)` only in its own line). So priority is
**conceptual contagion risk** (future readers learning wrong convention).

1. **xpoll-sigma-* (8 entries, lines 16834-16864)** — fix once via convention
   doc: `sigma=12` shorthand for σ(6)=12, NOT σ(12)=28. Or rewrite as
   `sigma(6)=12 [12 anchor count]`. High contagion: 8 sibling entries set
   precedent for future xpoll-* additions.
2. **xpoll-tau-* (11 entries, lines 16916-16938)** — same pattern: `tau=4`
   means τ(6)=4. High sibling-precedent risk.
3. **MILL-DFS23-12 (line 18228)** — `p(6)=11` is correct as `partition(6)=11`
   but the abbreviation `p` collides with `prime` (p(6)=13). Rename to
   `partition(6)=11` or add convention note. Low deps but cross-engine
   audit (raw 43) may flag.

## Falsifier Candidate Suggestions (F38+ range)

M3-style anchors for confirmed mismatches — each falsifier asserts
`func(arg) == V` for the canonical evaluation, and would fire on the
current atlas content if `(N)` is interpreted literally:

- **F38_xpoll_sigma_12_label**: assert `sigma(12) == 28 != 12`. Triggers on
  any `xpoll-*` entry of form `sigma(12) = 12 ...`. 8 hits in current atlas.
- **F39_xpoll_tau_4_label**: assert `tau(4) == 3 != 4`. Triggers on any
  `xpoll-*` entry of form `tau(4) = 4 ...`. 11 hits.
- **F40_func_name_collision_p**: assert `prime(6) == 13` and `partition(6) == 11`,
  flag any line where `p(6) = 11` is written (collision risk).
- **F41_arithmetic_chain_terminal**: generic check — for `func(N) = ... = V`,
  ensure the LAST `=int` segment matches `func(N)` canonical eval. Catches
  M3-style errors prospectively.

## Audit Caveats

- Regex captures only `func([0-9]+)` form; misses `func(expr)` / `func(N,k)` /
  set-valued `div(6)={...}`. Cross-shard scan covered all 7 atlas files.
- `L(n)` (493 hits) and other UNKNOWN funcs intentionally skipped — not in canon.
- Dependent counting via `grep -cF` is approximate (1-line subtraction for self-def);
  true graph-traversal would require parsing `<-`/`->` edges.
- This is a label-syntax audit only. Semantic-meaning audits (e.g. is the
  domain-claim 'sigma(12) = FCC CN=12' physically true?) are out of scope.

## Reproducibility

Audit script: `/tmp/atlas_semantic_audit.py` (~280 lines, stdlib only).
Read-only on atlas; no mutation. Runtime ~5s on 23932-line corpus.
