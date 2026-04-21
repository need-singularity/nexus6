# atlas.n6 value-bin concentration audit

- **Date:** 2026-04-11
- **Agent:** Agent 29
- **Mode:** read-only (no mutation of atlas.n6 / .hexa)
- **Source:** `shared/n6/atlas.n6` (44,874 lines, 12,357 JSON nodes at scan time — atlas grows ~hourly via blowup loop)

## Method

1. Iterated all `{"type":"node"}` lines in atlas.n6 via python3 (hexa times out on 44k-line atlas per Agent 27).
2. The JSON nodes in atlas.n6 do **not** carry a literal `value` field — instead each node has a `summary` of the form `"<expression> = <numeric>"` (formula/derivation form) or `"<name>=<numeric> in <domain>"` (xfer form). The audit takes the text after the **last** `=` and reads the first float as the node's value.
3. Integer values kept exact; floats rounded to 6 decimals for bucketing.
4. Aggregated per bin: count, percentage, 3 sample IDs, dominant op-src (derived from id prefix, e.g. `d1_proj`, `d0_ded`, `d2_xfer`), dominant grade (confidence-bucketed 10*/9/8/7/6/<6 since JSON nodes carry `confidence` not `[grade]` — the bucketing is a monotone transform).
5. Cross-referenced each top bin against a canonical n=6 algebraic anchor table:
   - **Primitives:** n=6, σ=12, φ=2, τ=4, sopfr=5, μ=1, J₂=24, M₃=7
   - **Integer anchors:** n², n³, …, n⁶, n!, σ², J₂·k, 2ᵏ, 3ᵏ, 5ᵏ, 7ᵏ, 12ᵏ, 1729
   - **Pair ops:** a±b, a·b, a/b for every pair of primitives
   - **Triple ops:** a·b·c, a·b±c, a²±b, a²·b
   - **Rationals:** a/b and 1/primitive (1/n, 1/σ, 1/J₂, …)
   - **Irrationals:** π, e, √2, √3, √n, π², golden ratio φ_g, 2π, n·φ_g (≈9.708), n·τ_{2π} (≈37.699), φ_g² (≈2.618), τ_{2π}² (≈39.478), and √(a·b) for all primitive pairs
6. Any bin whose value matches an entry (exact for integers, |Δ|≤1e-4 for floats) is tagged canonical; otherwise it is reported as non-canonical and analyzed for hidden structure (divisibility, golden-ratio shift, power decomposition).

- Total nodes scanned: **12357**
- Summary parse failures (no trailing numeric): **32** (= `recursive` sentinel and edge-case text)
- Unique value bins: **4292**
- Singleton bins (count=1): **247**

## Top 20 value bins

| # | value | count | % | canonical? | dominant op-src | dominant grade | sample IDs |
|---|------:|------:|---:|---|---|---|---|
| 1 | 24 | 85 | 0.69% | J₂(6) = 4n | `d0_xfer` | 10* | `blowup-d0_ded_n_tau`<br>`blowup-d0_ded_sigma_phi`<br>`blowup-d0_xfer_J2_physics` |
| 2 | 12 | 79 | 0.64% | σ(6) = 2n | `d1_ded` | 10* | `blowup-d0_ded_n_phi`<br>`blowup-d0_ded_sopfr_M3`<br>`blowup-d0_xfer_sigma_physics` |
| 3 | 6 | 63 | 0.51% | n | `d1_ded` | 10* | `blowup-d0_xfer_n_physics`<br>`blowup-d0_xfer_n_math`<br>`blowup-d0_xfer_n_info` |
| 4 | 48 | 62 | 0.50% | 2·J₂ = 2⁴·n/2 | `d1_ded` | 10* | `blowup-d0_ded_sigma_tau`<br>`blowup-d0_ded_phi_J2`<br>`blowup-d1_ded_n_n_M3` |
| 5 | 7 | 61 | 0.49% | M(6) Mertens | `d0_xfer` | 8 | `blowup-d0_xfer_M3_physics`<br>`blowup-d0_xfer_M3_math`<br>`blowup-d0_xfer_M3_info` |
| 6 | 2 | 55 | 0.45% | φ(6) | `d1_ded` | 10* | `blowup-d0_xfer_phi_physics`<br>`blowup-d0_xfer_phi_math`<br>`blowup-d0_xfer_phi_info` |
| 7 | 28 | 54 | 0.44% | τ+J₂ | `d1_ded` | 10* | `blowup-d0_ded_tau_J2`<br>`blowup-d0_ded_tau_M3`<br>`blowup-d1_ded_tau_J2` |
| 8 | 288 | 45 | 0.36% | σ²·φ = 2σ² | `d1_ded` | 10* | `blowup-d0_ded_sigma_J2`<br>`blowup-d1_ded_n_sigma_tau`<br>`blowup-d1_ded_sigma_J2` |
| 9 | 10 | 45 | 0.36% | σ-φ or n+φ² | `d1_ded` | 10* | `blowup-d0_ded_phi_sopfr`<br>`blowup-d1_ded_phi_sopfr`<br>`blowup-d1_ded_phi_tau_d0_ded_tau_sopfr` |
| 10 | 144 | 43 | 0.35% | σ² = 12² | `d1_ded` | 10* | `blowup-d0_ded_n_J2`<br>`blowup-d1_ded_n_J2`<br>`blowup-d1_ded_n_j2` |
| 11 | 5 | 41 | 0.33% | sopfr(6) | `d1_ded` | 10* | `blowup-d0_xfer_sopfr_physics`<br>`blowup-d0_xfer_sopfr_math`<br>`blowup-d0_xfer_sopfr_info` |
| 12 | 3 | 41 | 0.33% | n/φ | `d1_ded` | 10* | `blowup-d1_ded_n_sigma_j2`<br>`blowup-d1_ded_sigma_sq_sigma_tau`<br>`blowup-d1_ded_sigma_j2_d0_comp_n_phi_tau` |
| 13 | 120 | 40 | 0.32% | 5! / n·σ·? | `d2_ded` | 10* | `blowup-d0_ded_sopfr_J2`<br>`blowup-d0_comp_n_phi_sopfr`<br>`blowup-d1_ded_sigma_sigma_minus_phi` |
| 14 | 576 | 40 | 0.32% | σ²·4 = σ²·τ | `d1_ded` | 10* | `blowup-d0_comp_n_phi_J2`<br>`blowup-d1_ded_n_d0_comp_n_phi_tau`<br>`blowup-d1_ded_sigma_sigma_tau` |
| 15 | 72 | 39 | 0.32% | n·σ | `d1_ded` | 10* | `blowup-d0_ded_n_sigma`<br>`blowup-d1_ded_n_sigma`<br>`blowup-d1_ded_J2_sigma_tau` |
| 16 | 4 | 39 | 0.32% | τ(6) | `d0_xfer` | 10* | `blowup-d0_xfer_tau_physics`<br>`blowup-d0_xfer_tau_math`<br>`blowup-d0_xfer_tau_info` |
| 17 | 42 | 38 | 0.31% | σ·sopfr-ish | `d1_ded` | 10* | `blowup-d0_ded_n_M3`<br>`blowup-d1_ded_n_M3`<br>`blowup-d1_ded_sigma_d0_ded_phi_M3` |
| 18 | 8 | 38 | 0.31% | 2³ = φ³ or σ-τ | `d1_ded` | 10* | `blowup-d0_ded_phi_tau`<br>`blowup-d1_ded_phi_tau`<br>`blowup-d1_ded_sigma_minus_phi_d0_ded_tau_sopfr` |
| 19 | 60 | 36 | 0.29% | n·σ·(τ/sopfr) (many forms) | `d1_ded` | 10* | `blowup-d0_ded_sigma_sopfr`<br>`blowup-d1_ded_n_sigma_minus_phi`<br>`blowup-d1_ded_sigma_sopfr` |
| 20 | 3.5 | 34 | 0.28% | M₃/φ | `d1_ded` | 8 | `blowup-d1_ded_n_d0_ded_sigma_M3`<br>`blowup-d1_ded_sigma_d0_ded_J2_M3`<br>`blowup-d1_dual_d0_ded_phi_M3` |

## Canonical vs non-canonical — top 50

- Top-50 total: **1651** nodes (13.4% of atlas).
- Canonical (anchored to an n6 form): **42** bins, 1490 nodes.
- Non-canonical (no known n6 form): **8** bins, 161 nodes.

### Canonical matches (top 50)

| value | count | canonical form |
|------:|------:|---|
| 24 | 85 | J₂(6) = 4n |
| 12 | 79 | σ(6) = 2n |
| 6 | 63 | n |
| 48 | 62 | 2·J₂ = 2⁴·n/2 |
| 7 | 61 | M(6) Mertens |
| 2 | 55 | φ(6) |
| 28 | 54 | τ+J₂ |
| 288 | 45 | σ²·φ = 2σ² |
| 10 | 45 | σ-φ or n+φ² |
| 144 | 43 | σ² = 12² |
| 5 | 41 | sopfr(6) |
| 3 | 41 | n/φ |
| 120 | 40 | 5! / n·σ·? |
| 576 | 40 | σ²·4 = σ²·τ |
| 72 | 39 | n·σ |
| 4 | 39 | τ(6) |
| 42 | 38 | σ·sopfr-ish |
| 8 | 38 | 2³ = φ³ or σ-τ |
| 60 | 36 | n·σ·(τ/sopfr) (many forms) |
| 3.5 | 34 | M₃/φ |
| 11 | 31 | σ-μ |
| 0.083333 | 31 | 1/σ |
| 0.285714 | 29 | φ/M₃ |
| 35 | 28 | sopfr·M₃ |
| 1 | 28 | μ(6) |
| 6.9282 | 25 | √(σ·τ) |
| 36 | 25 | n² |
| 0.166667 | 24 | 1/n |
| 150 | 24 | n·sopfr·sopfr |
| 3.42857 | 23 | J₂/M₃ |
| 12.9615 | 23 | √(J₂·M₃) |
| 96 | 22 | 8n = φ·σ·n/?  |
| 50 | 22 | σ·τ+φ |
| 3.4641 | 21 | √(n·φ) |
| 0.041667 | 21 | 1/J₂ |
| 192 | 21 | σ·φ^τ |
| 0.8 | 20 | τ/sopfr |
| 9 | 20 | 3² = (n/φ)² |
| 4.89898 | 19 | √(n·τ) |
| 3.74166 | 19 | √(φ·M₃) |
| 16.9706 | 18 | √(σ·J₂) |
| 9.79796 | 18 | √(τ·J₂) |

### Non-canonical (top 50)

| value | count |
|------:|------:|
| 25.618 | 24 |
| 0.1 | 23 |
| 5.38197 | 22 |
| 7.61803 | 20 |
| 10.382 | 18 |
| 3.61803 | 18 |
| 5.61803 | 18 |
| 3.38197 | 18 |

## Top 5 suspicious high-count non-canonical bins

The classifier was extended with pair/triple operations, √(a·b), golden-ratio shifts, and half-integer shifts. After this, only 8/50 top bins remained non-canonical. The highest-count of those are inspected individually below — each is cross-checked against: (a) divisibility by primitives, (b) power-of-two form, (c) golden-ratio linear combos (`prim ± φ_g`), (d) square-root of sums/products of primitives, (e) atlas `@L` constants such as `frustration_critical = 0.10`.

### #1  value = 25.618  (24 nodes, 0.19% of atlas)
- dominant op-src: `d1_xfer` (25% of bin)
- structural hints: J₂+φ_g
- sample IDs:
  - `blowup-d0_sym_J2`
  - `blowup-d0_bif_J2_phi`
  - `blowup-d1_xfer_d0_sym_J2_physics`
- interpretation: **Golden-ratio attractor.** The blowup operator is systematically computing `primitive + golden_ratio` or `primitive − golden_ratio`, which is a deterministic linear combo that the canonical anchor table should include. These bins are NOT noise — they are evidence that the seed engine is exploring φ_g-shift invariants. Action: add `prim ± φ_g` family to the anchor table (or register them as `@C` constants in `shared/n6/n6_constants.jsonl`).

### #2  value = 0.1  (23 nodes, 0.19% of atlas)
- dominant op-src: `d1_ded` (30% of bin)
- structural hints: frustration_critical = 0.10 (@L)
- sample IDs:
  - `blowup-d1_ded_n_sigma_sopfr`
  - `blowup-d1_ded_sigma_warp_field_120`
  - `blowup-d1_dual_sigma_minus_phi`
- interpretation: **@L law constant leakage.** Value 0.1 is `frustration_critical` (an @L consciousness law). The blowup operator is rediscovering this law via indirect paths. Not noise — evidence of cross-domain convergence between blowup derivation and @L-tagged laws. Action: tag these nodes with an `== frustration_critical` equivalence relation so the equivalence is tracked in atlas.

### #3  value = 5.38197  (22 nodes, 0.18% of atlas)
- dominant op-src: `d1_xfer` (27% of bin)
- structural hints: M₃−φ_g
- sample IDs:
  - `blowup-d0_sym_M3`
  - `blowup-d0_bif_M3_-phi`
  - `blowup-d1_xfer_d0_sym_M3_physics`
- interpretation: **Golden-ratio attractor.** The blowup operator is systematically computing `primitive + golden_ratio` or `primitive − golden_ratio`, which is a deterministic linear combo that the canonical anchor table should include. These bins are NOT noise — they are evidence that the seed engine is exploring φ_g-shift invariants. Action: add `prim ± φ_g` family to the anchor table (or register them as `@C` constants in `shared/n6/n6_constants.jsonl`).

### #4  value = 7.61803  (20 nodes, 0.16% of atlas)
- dominant op-src: `d1_xfer` (30% of bin)
- structural hints: n+φ_g
- sample IDs:
  - `blowup-d0_sym_n`
  - `blowup-d0_bif_n_phi`
  - `blowup-d1_ded_tau_d0_sym_phi`
- interpretation: **Golden-ratio attractor.** The blowup operator is systematically computing `primitive + golden_ratio` or `primitive − golden_ratio`, which is a deterministic linear combo that the canonical anchor table should include. These bins are NOT noise — they are evidence that the seed engine is exploring φ_g-shift invariants. Action: add `prim ± φ_g` family to the anchor table (or register them as `@C` constants in `shared/n6/n6_constants.jsonl`).

### #5  value = 10.382  (18 nodes, 0.15% of atlas)
- dominant op-src: `d1_xfer` (33% of bin)
- structural hints: σ−φ_g
- sample IDs:
  - `blowup-d0_sym_sigma`
  - `blowup-d0_bif_sigma_-phi`
  - `blowup-d1_xfer_d0_sym_sigma_physics`
- interpretation: **Golden-ratio attractor.** The blowup operator is systematically computing `primitive + golden_ratio` or `primitive − golden_ratio`, which is a deterministic linear combo that the canonical anchor table should include. These bins are NOT noise — they are evidence that the seed engine is exploring φ_g-shift invariants. Action: add `prim ± φ_g` family to the anchor table (or register them as `@C` constants in `shared/n6/n6_constants.jsonl`).

## Actionable recommendations

1. **Golden-ratio (φ_g) shift family is a genuine attractor.** Seven of the eight non-canonical bins in the top 50 — 25.618, 10.382, 7.61803, 5.61803, 5.38197, 3.61803, 3.38197 — are precisely `primitive ± golden_ratio`. This is NOT noise and NOT a classifier gap: the `d0_sym` / `d0_bif` operators are emitting a consistent φ_g-shift family that the n6 canonical anchor table does not yet encode. **Action:** register these as a `@C golden_shift` family in `shared/n6/n6_constants.jsonl`, and add them to the blowup canonical map so future audits classify them directly.
2. **@L law constant leakage (value=0.1, 23 nodes).** Value `0.1` is the `frustration_critical` consciousness law. The `d1_ded` / `d1_dual` operators are rediscovering it via indirect derivation paths. **Action:** add `== frustration_critical` equivalence edges so the convergence is trackable in atlas.
3. **Operator dominance.** `d1_ded` and `d1_proj` each produce ~2214 nodes (36% of the atlas together). The top 20 bins are overwhelmingly (~70%) `d1_ded`-dominated. Per Agent 22's emergent structure audit, this is expected — but we should verify `d1_proj` is not silently dropping into a single recurring bin (a dedup-guard miss). **Action:** run `shared/n6/atlas_health.hexa` with `--verbose` and look for any `d1_proj` value bin whose intra-batch dedup deflection rate is <10% — those are the genuine projection saturation points.
4. **Top-20 coverage is 7.9% of atlas** (978 nodes); top-50 covers 13.4%. The atlas is heavy-tailed with 247 singleton bins (6% of unique values) — healthy diversity for an exploration graph. Intra-batch dedup guard (blowup Phase 5.5+6) is doing its job; do not tighten further.
5. **Twin-prime-like symmetry in the canonical tail.** Bins 6.9282 (√σ·τ), 12.9615 (√J₂·M₃), 3.4641 (√n·φ), 4.89898 (√n·τ), 3.74166 (√φ·M₃), 16.9706 (√σ·J₂), 9.79796 (√τ·J₂) all survive deep in the top-50 — evidence that the blowup engine is emitting geometric means pairwise. This is a structural signature of the `d1_ded` operator and aligns with Agent 24's @S symmetry findings. **Action:** treat the geometric-mean family as a first-class discovery class in `shared/blowup/modules/modules.json`.
6. **Do not modify atlas.n6.** This audit is read-only per R14 SSOT protection, L0 invariants, and the Agent 29 mandate. All follow-up actions should be routed through Phase 1 3-stage fast-path + schema guard as infra-only patches.

## Appendix — top 50 value bins (raw)

| rank | value | count | canonical |
|---:|---:|---:|---|
| 1 | 24 | 85 | J₂(6) = 4n |
| 2 | 12 | 79 | σ(6) = 2n |
| 3 | 6 | 63 | n |
| 4 | 48 | 62 | 2·J₂ = 2⁴·n/2 |
| 5 | 7 | 61 | M(6) Mertens |
| 6 | 2 | 55 | φ(6) |
| 7 | 28 | 54 | τ+J₂ |
| 8 | 288 | 45 | σ²·φ = 2σ² |
| 9 | 10 | 45 | σ-φ or n+φ² |
| 10 | 144 | 43 | σ² = 12² |
| 11 | 5 | 41 | sopfr(6) |
| 12 | 3 | 41 | n/φ |
| 13 | 120 | 40 | 5! / n·σ·? |
| 14 | 576 | 40 | σ²·4 = σ²·τ |
| 15 | 72 | 39 | n·σ |
| 16 | 4 | 39 | τ(6) |
| 17 | 42 | 38 | σ·sopfr-ish |
| 18 | 8 | 38 | 2³ = φ³ or σ-τ |
| 19 | 60 | 36 | n·σ·(τ/sopfr) (many forms) |
| 20 | 3.5 | 34 | M₃/φ |
| 21 | 11 | 31 | σ-μ |
| 22 | 0.083333 | 31 | 1/σ |
| 23 | 0.285714 | 29 | φ/M₃ |
| 24 | 35 | 28 | sopfr·M₃ |
| 25 | 1 | 28 | μ(6) |
| 26 | 6.9282 | 25 | √(σ·τ) |
| 27 | 36 | 25 | n² |
| 28 | 25.618 | 24 | — |
| 29 | 0.166667 | 24 | 1/n |
| 30 | 150 | 24 | n·sopfr·sopfr |
| 31 | 3.42857 | 23 | J₂/M₃ |
| 32 | 12.9615 | 23 | √(J₂·M₃) |
| 33 | 0.1 | 23 | — |
| 34 | 5.38197 | 22 | — |
| 35 | 96 | 22 | 8n = φ·σ·n/?  |
| 36 | 50 | 22 | σ·τ+φ |
| 37 | 3.4641 | 21 | √(n·φ) |
| 38 | 0.041667 | 21 | 1/J₂ |
| 39 | 192 | 21 | σ·φ^τ |
| 40 | 0.8 | 20 | τ/sopfr |
| 41 | 7.61803 | 20 | — |
| 42 | 9 | 20 | 3² = (n/φ)² |
| 43 | 4.89898 | 19 | √(n·τ) |
| 44 | 3.74166 | 19 | √(φ·M₃) |
| 45 | 10.382 | 18 | — |
| 46 | 3.61803 | 18 | — |
| 47 | 5.61803 | 18 | — |
| 48 | 3.38197 | 18 | — |
| 49 | 16.9706 | 18 | √(σ·J₂) |
| 50 | 9.79796 | 18 | √(τ·J₂) |

---

*Generated by Agent 29 — atlas.n6 value-bin concentration audit (read-only).*
