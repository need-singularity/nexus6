# M3 true-definition audit — Ω-cycle (2026-04-26)

**Trigger**: F20 falsifier discovery (`design/hexa_sim/2026-04-26_F19_F23_falsifier_expansion_omega_cycle.json`) — atlas line 53 labels `M3 = mertens(6) = 7` but canonical Mertens M(6) = -1.

**Scope**: read-only, bash + Read only, no atlas mutation.

---

## 1. Verification of discovery

Atlas source: `/Users/ghost/core/nexus/n6/atlas.n6:53`

```
@P M3 = mertens(6) = 7 :: foundation [10*]
  => "메르텐스 함수값"
```

Canonical Mertens function: M(n) = Σ_{k=1..n} μ(k).

| k | μ(k) | partial sum |
|---|------|-------------|
| 1 | 1    | 1           |
| 2 | -1   | 0           |
| 3 | -1   | -1          |
| 4 | 0    | -1          |
| 5 | -1   | -2          |
| 6 | 1    | **-1**      |

Result: **M(6) = -1**, not 7. The `mertens(6)` parenthetical on line 53 is mislabelled — confirmed.

(Side note: μ(6) on line 51 is given as `mu = mobius(6) = 1`, which IS canonical — μ(6)=μ(2·3)=(-1)^2=1. So the atlas's mobius is right; only mertens is wrong.)

## 2. Internal consistency check (M3=7 dependents)

| line | identity | eval w/ M3=7 | holds? |
|------|----------|-------------|--------|
| `atlas.n6:174` | `C(7,2) = 21 = sigma + n + M3 - tau` | 12+6+7-4 = 21 | YES |
| `atlas.n6:234` | `B_6 = 1/42 == 1/(n*M3)` | 1/(6·7) = 1/42 | YES |
| `atlas.n6:860` | `L1-Br-Z35 = M3*sopfr` (Br Z=35) | 7·5 = 35 | YES |
| `atlas.n6:1927` | `L3-alkene-ethylene-mw = 28 = tau*M3` (C2H4 mw=28) | 4·7 = 28 | YES |
| `atlas.n6:3665` | `MET-co2-current-ppm = P2*sigma+M3*sigma` | 28·12 + 7·12 = 420 (ppm-ish) | YES (formula dim ok) |
| `atlas.n6:3693` | `MET-earth-effective-temp = sigma*J2-J2-M3-phi` | 12·24-24-7-2 = 255 (K, exact) | YES |
| `atlas.n6:4038` | `ECON-bis-member-cb = P2*phi+M3` | 28·2+7 = 63 | YES |
| `atlas.n6:5485` | `L6-civil-bridge-lrfd = 1.75 = M3/tau` | 7/4 = 1.75 | YES |
| `atlas.n6:7297` | `L9-bbn-np-ratio = 1/M3 = mu/M3` | 1/7 ≈ 0.143 | YES (BBN n/p) |
| `atlas.n6:7498-7556` | 9 blowup discovery edges (`n+M3=13`, `tau*M3=28`, `sopfr+M3=12`, `J2+M3=31`, …) | all only consistent with M3=7 | YES |

`M3=7` is **load-bearing across 20+ atlas identities**. Substituting M3=-1 (canonical mertens) would break all of them. The value is fixed; only the *name* is wrong.

## 3. Candidate functions giving 7 at n=6

| candidate | f(6) | notes |
|-----------|------|-------|
| `next_prime(6)` | **7** | OEIS A151800; very natural successor function |
| `2*tau(6) - 1` | 2·4-1 = **7** | tau-derived, integer |
| `sigma(6) - sopfr(6)` | 12-5 = **7** | already named in jsonl as `sigma_minus_sopfr=7` (line 7 of `n6_constants.jsonl`) |
| `n + 1` | **7** | trivial successor |
| `Lucas L(4)` | **7** | Lucas seq 2,1,3,4,7,11; L(4)=7 (off-index) |
| `M(7)` (canonical Mertens at 7) | -2 | no |
| `\|M(k)\|` summed up to 6 | varies | doesn't give 7 cleanly |
| `index of next zero of M after k=6` | M(k) zeros: k=2,39,40,58,…; not 7 | no |
| `7th squarefree number` | A005117(7)=10 | no |
| Bell B_4 | 15 | no |
| π(7) (prime-counting at 7) | 4 | no |

## 4. Evidence search — what the corpus actually says

### 4a. Smoking gun: documented historical conflict

`/Users/ghost/core/nexus/n6/scripts/atlas_phase48_approx_expr_bridges.md:18-23` (Agent 32, 2026-04-11):

> **M3 / P2 discrepancy handling.** `n6_constants.jsonl` assigns `M3=3`
> while `shared/n6/verify_formulas.hexa` and atlas.n6's own foundation row
> `@P M3 = mertens(6) = 7` use `M3=7`.

`/Users/ghost/core/nexus/n6/scripts/atlas_phase46_canonical_nodes.md:44`:

> | m3 | 3 | `mertens(6)` per `n6_constants.jsonl`; note `atlas.n6` DSL `@P M3` says 7 — unresolved conflict, `n6_constants.jsonl` wins per Agent 28 rules |

So at one point the corpus had **three** competing values: 3 (n6_constants), 7 (atlas DSL, verify_formulas), -1 (canonical mertens). The .md docs are now stale — `/Users/ghost/core/nexus/n6/n6_constants.jsonl:3` currently says `{"name":"M3","value":7}`, so 7 won post-2026-04-11.

Note: M(6)=-1 doesn't equal 3 either, so the original `M3=3` was ALSO not canonical mertens. This corroborates that "mertens" has been a misnomer label at every stage — the corpus author was inventing an `M_k(n)` family and naming it after Mertens for atmosphere, never literal Σμ.

### 4b. No programmatic definition exists

Searched `/Users/ghost/core/nexus/n6/scripts/`, `/Users/ghost/core/nexus/n6/verify_formulas.hexa`, `/Users/ghost/core/nexus/n6/verify_n6_formula.hexa`, `/Users/ghost/core/n6-architecture/`: **no `def mertens` / `fn mertens` / `mertens(...)` implementation exists** anywhere. The label is asserted in atlas only.

### 4c. P2/P3/P4 family hint

`n6_constants.jsonl:13,17,18`: `P2=28`, `P3=496`, `P4=8128` — these are **perfect numbers** (2nd, 3rd, 4th). So `P_k` = k-th perfect number is a real indexed family in the corpus.

If `P_k` = k-th perfect number, by analogy `M_k` should be a k-indexed family too. M3=7 fits **`M_k = k-th Mersenne prime`** perfectly:

| k | M_k (Mersenne prime, 2^p - 1 with p prime) |
|---|---|
| M_1 | 3 (= 2^2 - 1) |
| M_2 | 7 (= 2^3 - 1) |
| M_3 | 31 (= 2^5 - 1) |

Hmm — M_2 = 7, not M_3. But `n6_constants.jsonl` once said `M3=3`, which IS Mersenne M_1. And `M3=7` IS Mersenne M_2. So if the family is "Mersenne primes" with off-by-one indexing (or 0-indexed: M_0=3, M_1=7, M_2=31), the atlas usage M3=7 corresponds to **the 2nd Mersenne prime** (or 1st by 0-index).

**Cross-check with the @F P2 entry**: `P2=28` = 2nd perfect number. Perfect numbers are Mersenne-derived: P_k = 2^(p-1)·(2^p − 1) where M_k = 2^p − 1 is the k-th Mersenne prime. So P_2 = 28 corresponds to the 2nd Mersenne prime, which is **7**. So **M3 (in the atlas) = the Mersenne prime that generates P2 = 28**.

This is a much stronger hypothesis than "next_prime(6)": the atlas is using Mersenne-perfect pairing, and the "3" in `M3` is **probably an off-by-one or a "Mersenne #3" old naming** (some OEIS / textbooks list 3,7,31,127,… as M_1..M_4 and others list 7,31,127,… or use the Mersenne exponent p ∈ {2,3,5,7,…}, where M_3 = 2^3-1 = 7 if the index IS the exponent).

**Most likely**: `M3` = `2^3 - 1 = 7` = **Mersenne number with exponent 3**. The "3" in M3 is the *exponent*, not the *position in the Mersenne-prime list*. Then `mertens(6)` is a typo/mislabel for `mersenne(3)`. (`mertens` and `mersenne` differ by 2 letters; both are 19th-century number-theorists.)

This also reconciles the historical `M3=3`: if someone read M3 as "M_3 = third Mersenne prime" (= 31) but wrote 3 by typo or by reading "M3" as "the value 3", that's a separate error — but the *current* M3=7 = 2^3 - 1 is internally clean.

## 5. Best-guess definition

**HIGH-confidence inference**: `M3 = 2^3 − 1 = 7` = **Mersenne number with exponent 3** (notation `M_p = 2^p − 1`, standard OEIS A001348).

Confidence basis:
- exact value match (7)
- the corpus has a parallel `P_k` perfect-number family, and Mersenne ↔ perfect is the textbook pairing (`P2 = 28 = 2^(3-1)·(2^3-1) = 4·7`)
- the mislabel `mertens` ↔ `mersenne` is a plausible 2-letter slip / 한국어 transliteration confusion (메르센 vs 메르텐스)
- no `def mertens` exists in code; the label was never anchored to an implementation
- M_p = 7 is canonical and integer-clean, unlike "next_prime(6)" which is incidental

Alternative LOW-confidence: `next_prime(6) = 7`. Cleaner if you reject the Mersenne-family hypothesis, but doesn't explain the "3" in `M3`.

## 6. Recommended atlas action

**OPT-A (recommended)**: update `atlas.n6:53` parenthetical:

```
@P M3 = mersenne(3) = 2^3 - 1 = 7 :: foundation [10*]
  => "Mersenne 수 (지수 3) — 2번째 Mersenne prime; P2=28의 생성 인자"
```

Also update the docstring on line 28 (meta-closure list comment) to reflect `M3` as Mersenne, not Mertens.

This is non-breaking (value unchanged, all 20+ dependents intact) and resolves the labeling truthfully.

**OPT-B** (leave + comment): acceptable fallback if Mersenne hypothesis is rejected — but leaves the falsifier F20 perpetually red on the surface label.

**OPT-C** (rename M3 → M3_atlas): unnecessary churn; 50+ atlas references would need rewrites and the symbol is well-established.

## 7. Falsifier follow-up

F20 (`design/hexa_sim/falsifiers.jsonl`) currently asserts `M3 = mertens(6) = 7`. After OPT-A:

- **Retire F20 as currently written** (false claim by the literal label).
- **Replace with F20'**: `M3 = mersenne(3) = 2^3 − 1 = 7` — passes trivially, becomes a structural-admissibility witness rather than a discovery probe.
- Add **F20-meta** (Tier-2 historical): "atlas line 53 was previously mislabelled `mertens(6)` — verify rename to `mersenne(3)` was committed and no stale `mertens` references remain in code/docs (n6/scripts/atlas_phase46_canonical_nodes.md:44, atlas_phase48_approx_expr_bridges.md:18-23 are stale and should be updated).".

---

## File path index

- `/Users/ghost/core/nexus/n6/atlas.n6` (lines 25-54, 174, 234, 860, 1927, 3665, 3693, 4038, 4163, 5485, 7297, 7498-7556)
- `/Users/ghost/core/nexus/n6/n6_constants.jsonl:3,28,32,33,37`
- `/Users/ghost/core/nexus/n6/scripts/atlas_phase46_canonical_nodes.md:44` (stale — references defunct `M3=3`)
- `/Users/ghost/core/nexus/n6/scripts/atlas_phase48_approx_expr_bridges.md:18-23` (stale — historical conflict log)
- `/Users/ghost/core/nexus/n6/scripts/atlas_phase48_approx_expr_bridges.hexa:65,146` (sets `M3:7` programmatically, comment "M3=7 from atlas @P authority, post 2026-04-11 fix")
- `/Users/ghost/core/nexus/design/hexa_sim/2026-04-26_F19_F23_falsifier_expansion_omega_cycle.json:29-33,75,86` (F20 source)
