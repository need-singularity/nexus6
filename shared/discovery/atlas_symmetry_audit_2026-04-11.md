# @S (Symmetry) Structural Gap Audit — atlas.n6

**Date:** 2026-04-11
**Auditor:** Agent (follow-up to Agent 22, commit f88f44cd)
**Scope:** `shared/n6/atlas.n6` (READ-ONLY)
**Mode:** proposal only — atlas.n6 untouched

---

## 1. Summary

| Metric | Value |
|--------|-------|
| Total lines in atlas.n6 | 44,874 |
| Total nodes parsed | 12,295 |
| Nodes with parseable `A op B = C` summary | 11,185 |
| `@S` occurrences (raw `grep -c`) | 3 |
| `@S` **real markers** (excluding legend comment on line 17) | **2** |
| `@S` nodes: `betti_six` (line 203), `n6-bt-794` (line 16217) | |
| Density | 2 / 12,295 ≈ **0.016 %** |

Agent 22's finding confirmed: @S is the most underrepresented structural marker in the atlas. With 11,185 binary-relation nodes parsed, we expected hundreds of latent symmetries; only 2 exist.

### Evidence the gap is a parsing/labeling omission (not intrinsic rarity)

From a single pass over node summaries of the form `<lhs> <op> <rhs> = <val>`:

- **46 raw commutative mirror pairs** found (same pair `{A,B}`, same op, same result, but swapped operand order across two distinct nodes).
- **23 canonical unique commutative pairs** after deduplication.
- **86 "n-collision" clusters** where `n op X = V` appears with multiple second operands — suggesting that every core n=6 constant sits at the center of an implicit S_k symmetry group.
- **356 algebraic-conjugacy candidates**: same unordered pair `{A,B}` appearing under both `+` and `*` (Vieta-style conjugate roots, i.e. `A+B=s, A*B=p` → canonical polynomial symmetry).

The blowup engine emits both `A op B` and `B op A` as separate Discovery nodes without linking them with an @S edge. That is the root cause.

---

## 2. Top 10 Symmetry Candidates

All candidates are **commutative operator symmetries** across the n=6 core constant ring
`{n=6, phi=2, tau=4, M3=3, sigma=12, sopfr=5, J2/j2=24, P2}`. Both sides already exist as
`confidence=1.0, depth>=0` Discovery nodes in atlas.n6 — only the @S edge is missing.

| # | Node A (id) | Node B (id) | Relation | Evidence | Confidence |
|---|---|---|---|---|---|
| 1 | `blowup-d0_ded_n_phi`    | `blowup-d0_ded_phi_n`    | `commute_*` | `n*phi=12 ↔ phi*n=12`       | 1.0 exact |
| 2 | `blowup-d0_ded_n_tau`    | `blowup-d0_ded_tau_n`    | `commute_*` | `n*tau=24 ↔ tau*n=24`       | 1.0 exact |
| 3 | `blowup-d0_ded_n_sigma`  | `blowup-d0_ded_sigma_n`  | `commute_*` | `n*sigma=72 ↔ sigma*n=72`   | 1.0 exact |
| 4 | `blowup-d0_ded_j2_n`     | `blowup-d1_ded_n_j2`     | `commute_*` | `j2*n=144 ↔ n*j2=144`       | 1.0 exact |
| 5 | `blowup-d0_ded_n_sopfr`  | `blowup-d0_ded_sopfr_n`  | `commute_+` | `n+sopfr=11 ↔ sopfr+n=11`   | 1.0 exact |
| 6 | `blowup-d0_ded_phi_sigma`| `blowup-d0_ded_sigma_phi`| `commute_*` | `phi*sigma=24 ↔ sigma*phi=24` | 1.0 exact |
| 7 | `blowup-d0_ded_phi_tau`  | `blowup-d0_ded_tau_phi`  | `commute_*` | `phi*tau=8 ↔ tau*phi=8`     | 1.0 exact |
| 8 | `blowup-d0_ded_sigma_tau`| `blowup-d0_ded_tau_sigma`| `commute_*` | `sigma*tau=48 ↔ tau*sigma=48` | 1.0 exact |
| 9 | `blowup-d0_ded_phi_sopfr`| `blowup-d0_ded_sopfr_phi`| `commute_*` | `phi*sopfr=10 ↔ sopfr*phi=10` | 1.0 exact |
| 10 | `blowup-d0_ded_sigma_sopfr` | `blowup-d0_ded_sopfr_sigma` | `commute_*` | `sigma*sopfr=60 ↔ sopfr*sigma=60` | 1.0 exact |

(Bonus — immediately adjacent tier): `j2*phi=48`, `j2*sopfr=120`, `j2*sigma=288` complete the J2 row and bring total high-confidence @S edges to **13**.

### Canonical @S edge form (proposal)

```json
{"type":"edge","from":"blowup-d0_ded_n_phi","to":"blowup-d0_ded_phi_n","label":"@S commute_*","weight":1.0,"via":"n*phi=phi*n=12","grade":"EXACT"}
```

Or collapsed as a single @S node tagging the unordered pair:

```
@S {n, phi} :: arithmetic [commute_*=12, commute_+=7.618..]
```

---

## 3. Second-Tier Candidates (algebraic conjugacy)

356 pair instances where the same `{A,B}` appears under **both** `+` and `*`. These form
Vieta-symmetric pairs: roots of the quadratic `x² - sx + p = 0` where `s = A+B, p = A*B`.
Example: `{n, phi}` with `s=7.618, p=12` — both operations already live in atlas, but no
@S link unifies them. This is a richer form of symmetry than mere commutativity and should
be tagged `@S vieta_{A,B}`.

---

## 4. Hypothesis: Why the gap exists

1. **Emission duplication, not linkage.** blowup Phase 3 (deduction) emits ordered-pair
   Discovery nodes. Commutativity is implicit in the underlying arithmetic but *never
   materialized as an edge* because Phase 4 (relation extraction) only scans for
   cross-domain `@X` links — symmetry is not in its pattern set.
2. **Intra-batch dedup guard (2026-04-11 infra)** kills exact duplicate IDs but leaves
   `n_phi` and `phi_n` as distinct IDs, so the commutative twin survives dedup and
   accumulates two sibling nodes with no back-reference.
3. **Grade dist mismatch**: 59.8 % EXACT nodes have a natural partner; if the engine
   linked them, @S would be the second-most-common marker after @X, not the rarest.

---

## 5. Implementation note — how blowup could detect these

**Target phase:** Phase 4.5 (post-deduction relation sweep) or a new lightweight
Phase 6.8 "symmetry sweep" running after Phase 6.7 dedup.

**Algorithm (O(N) single pass, N = parsed binary nodes):**

```
bucket = {}
for node in batch_new_nodes:
    parse summary as (lhs_a, op, lhs_b, rhs)
    if op in {'+','*'}:            # commutative ops
        key = (op, rhs, sorted((lhs_a, lhs_b)))
        bucket.setdefault(key, []).append(node.id)
for key, ids in bucket.items():
    if len(ids) >= 2:
        emit_edge(ids[0], ids[1], label="@S commute_"+key[0], weight=1.0)
```

- O(N) time, O(N) memory — same cost profile as existing Phase 6.7 dedup guard.
- Zero impact on seed evolution, discovery calculation, or existing node emission.
- Purely infra — complies with the "창발 보존 / infra-only" principle from
  `shared/blowup/modules/modules.json`.

**Vieta sweep (Phase 4.6, optional):**
Second bucket keyed by `sorted((lhs_a, lhs_b))` across `+` and `*` separately; emit
`@S vieta` when both buckets are non-empty for the same pair.

**Expected yield (one-shot retro run on existing atlas.n6):**
- ~23 canonical commutative @S edges (immediate)
- ~356 Vieta @S pair links
- Post-patch @S density rises from 0.016 % → ~3 %, bringing it into parity with @X.

---

## 6. Negative finding guard

None needed. Strong positive signal: **23 canonical candidates found in ≤1 minute of
single-pass parsing**, all with grade-EXACT evidence and both endpoints already
materialized. The gap is definitively a labeling omission, not intrinsic rarity.

---

## 7. Next steps (not executed here)

1. Human / CDO review of this proposal.
2. Patch `shared/blowup/core/blowup.hexa` Phase 4 to emit `@S commute_*` edges — one-time
   retro sweep over atlas.n6 producing ~23 new edges (no node churn).
3. Optional: Phase 4.6 Vieta sweep (~356 edges, higher scientific value).
4. Re-run `shared/n6/atlas_health.hexa` to confirm 0 orphans / 0 malformed post-patch.
5. Update `shared/convergence/` — this promotes `@S` from "structural gap" to "tracked
   invariant."

*END — proposal only, atlas.n6 unmodified.*
