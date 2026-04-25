# Atlas Function-Call Convention

**Status**: normative · **Born**: 2026-04-26 · **Trigger**: 21 MISMATCH in atlas_semantic_gap_audit (xpoll-* sigma/tau + MILL-DFS23 p)

## Two notations conflated

Atlas entries that look like `<id> = <expr>` use one of two **incompatible** notations whenever a number-theoretic function appears on the right-hand side:

- **Notation A (shorthand value)** — `sigma = 12`
  Reads as: "σ at the implicit `n=6` anchor evaluates to 12." The function name is a **label only**; the number on the right is the *result* at the canonical anchor. Used when the entry is anchored to the n6 foundation and the argument never varies.

- **Notation B (explicit function call)** — `sigma(6) = 12`
  Reads as: "σ(6) = 12." Standard mathematical function-application: the parenthesised number is the **argument**, the value on the right is `f(arg)`. Used when the argument differs from 6 or when the anchor must be made explicit.

Both encode the same fact (σ at n=6 yields 12), but B is self-describing and A relies on the reader knowing the n=6 default.

## How to distinguish

| Signal | Notation A | Notation B |
|---|---|---|
| RHS shape | bare number / number+unit | full `func(arg) = result` triple |
| Args appear? | no | yes, in parentheses |
| Anchor implicit? | yes (n=6) | no (explicit) |
| Example | `sigma = 12` | `sigma(6) = 12` |

A fully-formed Notation-B entry **always** carries both an argument inside the parens and a separately-stated result.

## Wrong patterns to avoid

- `sigma(VALUE) = VALUE` where the number inside the parens equals the number on the right is **suspicious**. The author almost certainly meant Notation A (`sigma = VALUE`) but mistyped it as B by parenthesising the result. Examples surfaced by the 2026-04-26 audit:
  - `xpoll-sigma-music = sigma(12) = 12평균율 반음` — meant `sigma = 12` (i.e. σ(6) = 12, the count is 12); the `(12)` was misread as the σ-argument. Canonical σ(12) = 28, so the entry as written is mathematically wrong.
  - `xpoll-tau-chemistry = tau(4) = 4 quantum numbers` — meant `tau = 4`; canonical τ(4) = 3.
- `func(N) = result` where `func` collides with another standard alias. Example: `MILL-DFS23-12 = p(6) = 11`; `p` is overloaded (prime vs partition). The intended meaning was `partition(6) = 11`, but `p(6)` gets read as 6th prime = 13. **Disambiguate by spelling the function name out.**
- Notation A used when the argument is **not** 6. Always promote to Notation B in that case — `sigma(8) = 15` cannot be written `sigma = 15` because the anchor differs.

## Past offenders

The 2026-04-26 audit (`design/hexa_sim/2026-04-26_atlas_semantic_gap_audit.md`, 21 MISMATCH) catalogued every known case at the time of doc creation:

- 9 `xpoll-sigma-*` entries with `sigma(12) = 12` → meant Notation A
- 11 `xpoll-tau-*` entries with `tau(4) = 4` → meant Notation A
- 1 `MILL-DFS23-12-p6-11-double-decomp` with `p(6) = 11` → meant `partition(6) = 11`

These are tracked separately for cleanup (see queued ω-cycle); the convention doc and the F46–F49 guards exist to prevent **new** instances regardless of cleanup timing.

## Future enforcement

Three layers, in order of rigor:

1. **F46 / F47 / F48 falsifiers** (`design/hexa_sim/falsifiers.jsonl`) — guard against the specific malformed patterns at audit time. F46 = xpoll-sigma `func(N)=N`; F47 = xpoll-tau `func(N)=N`; F48 = atlas-wide `func(N)=N` count pinned to current baseline.
2. **F49 falsifier** — invokes the audit script and PASSes only if MISMATCH count stays at-or-below baseline (21). Catches **any** new semantic gap, not just the patterns above.
3. **Audit script as cron** — `2026-04-26_atlas_semantic_gap_audit.py` is re-runnable; promote to nexus cron daily so drift surfaces in <24h.

When in doubt: prefer **Notation B with explicit argument**. Notation A is only safe at the n=6 anchor.
