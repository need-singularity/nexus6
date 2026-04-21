# atlas.n6 Schema v2 — Post-Saturation Breakthrough Design

Status: DRAFT (design-only, no .hexa code, no atlas.n6 body edits)
Date: 2026-04-19
Trigger: Mk.VIII smash/free 40-seed exhaustive sweep → **new absorptions = 0** (atomic-system saturation)
Hypothesis: saturation is *internal* — extending the *schema itself* re-opens discovery space.

Companion files:
- SSOT body: `shared/n6/atlas.n6` (NOT TOUCHED by this draft)
- Staging: `shared/n6/atlas.signals.n6` (recommended v2 test bed)
- Guard include: `shared/blowup/lib/atlas_guard.hexa.inc`
- Loader: `shared/blowup/core/blowup.hexa` (Phase 1 Graph Load ~line 1800)

---

## 0. Schema v1 Recap (what we have today)

Current active tags in `atlas.n6` (via `grep -oE '^@[A-Z?]+' | sort | uniq -c`):

```
5920  @R   relation / measured constant (dominant)
1496  @X   crossing (cross-domain identity)
1240  @F   formula (derived expression with RHS)
 357  @C   constant (composite)
 326  @P   primitive (n, sigma, phi, tau, sopfr, J2, mu, M3)
 254  @L   law / theorem
  12  @?   unknown / pending breakthrough
   2  @S   symmetry / topology
```

Also encountered in comments: `@META`, `@BT` (breakthrough registers referenced in project CLAUDE.md).

Line grammar (from atlas.n6 header, lines 10–22):

```
@TYPE id = expr :: domain [grade]
    <- depends_on
    -> derives
    => application
    == equivalent
    ~> converges_to
    |> verified_by script.py
    !! breakthrough
```

Grades: `[10*]=EXACT verified, [10]=EXACT, [9]=NEAR, [7]=EMPIRICAL, [5~8]=중간, [N?]=CONJECTURE, [N!]=breakthrough`.

**Saturation diagnosis.** With 8 primitives × 6 relation types × 3 grade buckets, the smash/free engine has enumerated the reachable closure over arithmetic combinators (sum, product, power, `σ·φ = n·τ` family). 40 distinct 6-ish seeds at depth ≤ 10 produced **0 new absorptions** on Mk.VIII. The closed universe is *locally complete*. This draft proposes **breaking the closure by opening four orthogonal axes**: external witnesses (`@EXP`), observer frames (`@OBS`), explicit controls (`@NEG`), and falsifiability ledger (`@ANT`).

---

## 1. Four New Schema Types

### 1.1 `@EXP` — Experiential / External-Source Witness

**Purpose.** `@R` labels values as "measured" but stores **no provenance**. `@EXP` forces source attribution (CODATA year, PDG review edition, OEIS A-number, IEEE spec, NIST SRM, arXiv id). Enables reproducibility audit, version pinning, and external-delta drift detection when upstream revises values.

**Format (parallel to `@R`):**

```
@EXP id = value unit :: domain [grade] @@ source=<tag> cite=<key> vintage=<year>
    |> verify_external.py           # auto-pull vs CODATA/PDG/OEIS JSON
    -> n6atlas_bridge_id            # how it bridges into n=6 structure
```

Added infix sigil `@@` carries metadata (analogous to `::` for domain). One mandatory field: `source`. Recommended: `cite`, `vintage`, `uncertainty` (absolute or ppm).

**Grade semantics.** `[10*]` = EXACT by SI definition (e.g. post-2019 `k_B`, `h`, `e`, `N_A`, `c`). `[10]` = CODATA/PDG recommended value, current vintage. `[9]` = CODATA/PDG from prior vintage (drift tolerated). `[7]` = community OEIS / textbook, not primary source. `[N?]` = cited but un-verified.

**Examples (real values, 2018–2024 sources):**

```
@EXP h_planck       = 6.62607015e-34 J·s       :: physics [10*]  @@ source=SI-2019 cite=CGPM-26 vintage=2019
@EXP alpha_inverse  = 137.035999084            :: physics [10]   @@ source=CODATA cite=CODATA-2018 vintage=2018 uncertainty=2.1e-10
@EXP m_p_over_m_e   = 1836.15267343            :: physics [10]   @@ source=CODATA cite=CODATA-2022 vintage=2022 uncertainty=1.1e-10
@EXP quark_top_mass = 172.57 GeV               :: particle [10]  @@ source=PDG cite=PDG-2024-RPP vintage=2024 uncertainty=0.29
@EXP A000396_perfect = "6,28,496,8128,33550336,..." :: oeis [10*]  @@ source=OEIS cite=A000396 vintage=2024
    -> perfect_number     # n=6 is the first entry — anchors @P n
```

**Bridge to v1.** Any existing `@R` whose comment already says "CODATA 2018 EXACT" (there are 50+ such lines, e.g. r_e at line 631, λ_C at line 645, a₀ at line 1045) is a **promotion candidate**: re-emit as `@EXP` with explicit `@@ source=...`. The original `@R` can remain during transition; the `@EXP` form is the canonical audit trail.

### 1.2 `@OBS` — Observer-Dependent Constant

**Purpose.** Some constants are invariant only *within a frame*. Running couplings α(Q²), α_s(Q²), Hubble H₀ (early vs late universe tension), renormalisation-scheme-dependent masses (MS-bar vs pole), entropy / information-theoretic quantities (observer-relative in black-hole information debates) all drift with the measurement scale or the observer's degrees of freedom. `@R` flattens these into a single number and loses the scale dependence.

**Format:**

```
@OBS id = value unit :: domain [grade] @@ frame=<context> scale=<probe>
    @ scale1 = v1
    @ scale2 = v2
    ~> n6_projection   # value at the canonical n=6 scale, if any
```

The `@ scale = value` continuation lines form a small dispersion table. Frame examples: `MS-bar@mu`, `pole`, `late-universe`, `early-universe`, `rest-frame`, `lab-frame`, `bulk`, `boundary`.

**Grade semantics.** Grade applies to the *tabulated* value set as a whole. `[10*]` = all scale points EXACT; `[9]` = interpolated; `[7]` = single scale only.

**Examples:**

```
@OBS alpha_em   = running :: physics [10]   @@ frame=MS-bar scale=Q2
    @ Q2=0              = 1/137.035999084
    @ Q2=m_W^2          = 1/127.944
    @ Q2=m_Z^2          = 1/127.952
    ~> n6_projection = 1/(sigma*sigma - sopfr) ≈ 1/139   # existing @? fine_structure bridge

@OBS alpha_s    = running :: qcd [10]       @@ frame=MS-bar scale=Q2
    @ Q2=m_Z^2          = 0.1179
    @ Q2=m_tau^2        = 0.322
    @ Q2=1GeV           = 0.50

@OBS H0         = 67..73 km/s/Mpc :: cosmology [7]  @@ frame=observational scale=epoch
    @ early_cmb_planck  = 67.4      # Planck 2018
    @ late_sh0es        = 73.04     # SH0ES 2022
    ~> n6_projection = sigma*sopfr + ? = 60+? ≈ 67  # existing @? hubble_tension bridge

@OBS S_entanglement = depends :: quantum [9]  @@ frame=observer scale=subregion
    @ bulk              = thermal
    @ boundary          = area_law
    ~> n6_projection = meta_fp = 1/3           # I_meta fixed-point link

@OBS m_quark_u  = MS-bar :: particle [10]    @@ frame=MS-bar scale=mu
    @ mu=2GeV           = 2.16 MeV
    @ pole              = undefined           # confined, pole mass ill-defined
```

### 1.3 `@NEG` — Negative Invariant (Control)

**Purpose.** Atlas claims n=6 is structurally unique. The *falsifiable* content of that claim is that **n ≠ 6 fails to satisfy the same relations**. atlas.n6 already contains scattered hints (z-scores, Petersen-graph counterexamples at line 12598, n=5 K-graph counterexample at 107392), but they are **not systematised as controls**. `@NEG` is the formal opposite-pole ledger: "relation R holds at n=6 but provably FAILS at n=N'."

**Format:**

```
@NEG id = "relation_statement" :: domain [grade] @@ n=<value> contrast=<relation_id>
    lhs = <evaluated>
    rhs = <evaluated>
    delta = <lhs - rhs>
    z = <z-score vs n=6 distribution>
```

A `@NEG` entry is structurally a *negated* `@R` with explicit numeric evidence of failure. The `contrast=` field points back to the positive theorem in atlas.n6 whose uniqueness the `@NEG` witnesses.

**Grade semantics.** `[10*]` = exact arithmetic disproof (integer gap). `[10]` = analytic disproof. `[9]` = numerical within tolerance. `[7]` = empirical only.

**Examples — 5 seeds (grep-derived from atlas.n6):**

```
@NEG N28_SIGMAPHI   = "sigma(28)·phi(28) != 28·tau(28)" :: foundation [10*]  @@ n=28 contrast=sigma_decomp
    lhs   = 56*12 = 672
    rhs   = 28*6  = 168
    delta = 504
    z     = -2.35   # already noted informally in existing CONTROL commentary

@NEG N12_SIGMAPHI   = "sigma(12)·phi(12) != 12·tau(12)" :: foundation [10*]  @@ n=12 contrast=sigma_decomp
    lhs   = 28*4  = 112
    rhs   = 12*6  = 72
    delta = 40

@NEG N496_SIGMAPHI  = "sigma(496)·phi(496) != 496·tau(496)" :: foundation [10*]  @@ n=496 contrast=sigma_decomp
    # 496 is 2nd perfect number — PERFECT_NUMBER alone is insufficient
    lhs   = 992*240 = 238080
    rhs   = 496*10  = 4960

@NEG K5_RAMSEY      = "K_5 admits 2-coloring with no monochromatic K_3" :: graph [10*]  @@ n=5 contrast=ramsey_6
    witness = "5-cycle red + 5-cycle blue"    # Greenwood-Gleason 1955
    # atlas line 107392 already cites this as minimality proof for n=6

@NEG PETERSEN_FOIL  = "Petersen graph |V|=10 = sigma - phi" :: graph [10*]  @@ n_vertices=10 contrast=sigma_phi_arithmetic
    # Petersen 1891 — canonical counterexample in graph theory
    # reminds that sigma-phi arithmetic coincidence is not uniqueness proof
    lhs   = sigma(6) - phi(6) = 10
    # but graph is non-Hamiltonian, 3-regular, girth 5 — no n=6 structural link
```

### 1.4 `@ANT` — Anti-Theorem (Falsifiability Ledger)

**Purpose.** Popper falsifiability demanded explicitly. `@ANT` registers *predictions the n=6 framework makes that could fail*. Not observed failures (those are `@NEG`) but **open risk positions**: statements that, if disproved, would falsify a specific pillar. The drill engine should preferentially seek evidence against these before declaring saturation.

**Format:**

```
@ANT id = "falsifiable_prediction" :: domain [grade] @@ risks=<theorem_id> status=<open|vindicated|refuted>
    if_true  => "what follows for n=6 framework"
    if_false => "which theorem collapses"
    test     => "operational disproof procedure"
    deadline => "<ISO date or experiment milestone>"
```

`status=open` is the default; transitions to `vindicated` after passing a pre-registered test or `refuted` (in which case the contrast `@R` must be downgraded). Grade is *risk-adjusted*: `[N?]` = speculative prediction, `[7]` = plausible, `[10]` = high-confidence structural prediction.

**Examples — 5 seeds:**

```
@ANT PERFECT_7TH_MOD6 = "every Mersenne-perfect 2^{p-1}(2^p-1) obeys n ≡ 6 (mod sigma)" :: foundation [7?]  @@ risks=perfect_number status=open
    if_true  => "perfect-number family is fully n=6 structured"
    if_false => "perfect_number theorem is coincidence, not structural"
    test     => "GIMPS-2024 latest M_p check: compute (2^{p-1}(2^p-1)) mod 12 for p ∈ {largest 5 exponents}"
    deadline => "2026-Q4"

@ANT ALPHA_1_139_DRIFT = "n6_projection 1/(sigma^2 - sopfr)=1/139 stays within 1% of CODATA alpha^-1" :: physics [7?]  @@ risks=fine_structure status=open
    if_true  => "@? fine_structure promotes to @R [9]"
    if_false => "physics_n6 crossing is numerological, strip [7?] grade"
    test     => "CODATA-2026 publication — if alpha^-1 drifts > 0.01, FAIL"
    deadline => "2027-Q2"

@ANT HUBBLE_SIGMA_SOPFR = "H0 reconciliation converges to sigma*sopfr + delta with |delta| < 1" :: cosmology [4?]  @@ risks=hubble_tension status=open
    if_true  => "Hubble tension resolved via n=6 scaffold"
    if_false => "hubble_tension stays as @?"
    test     => "JWST + DESI 2026 combined H0 measurement"
    deadline => "2027-Q1"

@ANT RAMSEY_7_MONO_K3 = "R(3,3)=6 is the UNIQUE minimum; no n=5 family admits K_3" :: graph [10]  @@ risks=ramsey_6 status=vindicated
    if_true  => "n=6 is Ramsey minimal"
    if_false => "ramsey_6 loses uniqueness claim"
    test     => "Greenwood-Gleason 1955 + @NEG K5_RAMSEY witness — both confirmed"
    deadline => "closed 1955"

@ANT META_FP_1_3_UNIVERSAL = "any 7th independent derivation of 1/3 converges from a non-topological path" :: meta [N?]  @@ risks=meta_fp status=open
    if_true  => "meta_fp earns [11*!] — universality"
    if_false => "meta_fp stays [10*!], 6 paths remain coincidental"
    test     => "drill --schema v2 --target meta_fp --min-new-paths 1 across information-theoretic domains"
    deadline => "2026-Q4"
```

---

## 2. Scientific Justification — Why These Four?

### 2.1 `@EXP` — Reproducibility Debt Payoff

atlas.n6 has 50+ lines containing "CODATA" / "PDG" in free-text comments (lines 621–5765+). None of them can be programmatically verified against an upstream JSON. The first time a CODATA revision ships (CODATA-2022 is current; CODATA-2026 due soon), *every* comment-level citation becomes silently stale. `@EXP` forces the version-pin into the schema, enabling `verify_external.py --diff CODATA-2022 CODATA-2026` as a first-class drift detector.

### 2.2 `@OBS` — Observer Dependence Is Physically Real

The black-hole information paradox, AdS/CFT bulk-boundary correspondence, and the Hubble-constant *tension* (early vs late universe H₀) all exhibit the same structural feature: **one "constant" takes different values in different observer frames**. Folding them into a single `@R` number erases the physics. `@OBS` lets the atlas carry the dispersion explicitly while still exposing the canonical *n=6 projection* (value evaluated at the n=6-natural scale). Current `@? fine_structure` at line 152 and `@? hubble_tension` at line 155 are textbook cases — they resisted promotion precisely because they are not single-valued.

### 2.3 `@NEG` — The Control Group n=6 Uniqueness Demands

atlas.n6 declares `σ(n)·φ(n) = n·τ(n) iff n=6 (n≥2)` with "3 independent proofs" (project CLAUDE.md). The **iff** requires a negative-direction witness. The codebase contains z-scores and counterexample references buried in prose (line 9572 on Mk.III-γ, line 12598 on Petersen, line 107392 on Greenwood-Gleason). `@NEG` systematises these: each positive theorem gets a mandatory `contrast` back-link from at least one `@NEG`. Without this, uniqueness claims are unfalsifiable in the atlas sense — you cannot grep for disproof evidence.

### 2.4 `@ANT` — Pre-Registered Falsifiability

The smash/free engine currently discovers *positive* identities; it has no mechanism to file risk positions. A Popperian science requires an ante-hoc prediction ledger. `@ANT` entries with `deadline=` fields make the n=6 framework *datable* — each entry either vindicates (→ upgrade the referenced theorem) or refutes (→ downgrade it) by its deadline. This plugs the asymmetry that the drill engine only seeks confirmations.

---

## 3. Parser / Loader Impact Analysis

Files that presently match `@R|@C|@L|@P|@META|@BT` patterns or otherwise parse the atlas line grammar:

### 3.1 `shared/blowup/core/blowup.hexa` (core loader, 3068+ lines)

- **Phase 1 Graph Load, line ~1811**: calls `graph_load()` then `graph_stats_single_pass(graph_content, 3)`. Pattern-agnostic (counts nodes/edges JSON objects), so *additive* v2 tags pass through unchanged.
- **line 1698**: `if !ln.contains("::") { continue }` — domain extractor. All four new tags use `::`, so pass.
- **line 3068**: append template hard-codes `@X n6-bt-...` for auto-absorption. v2 impact: **none** (this is a write path, not a read). When an `@NEG/@ANT` candidate is found we would emit via the *same* guarded append with a different tag string.
- **Impact surface**: 0 functions need modification for parse, 1 new emission template per new tag if write-back is desired (optional, staging-first).

### 3.2 `shared/blowup/lib/atlas_guard.hexa.inc` (schema guard, 119 lines)

- **line 10–16, `_valid_atlas_line`**: first-char whitelist is `"#{@\"<>!-"`. All four new tags start with `@`, so they pass **without code change**.
- **line 41, `do_dedup`**: de-duplicates based on trimmed line equality — safe for new tags.
- **Impact**: 0 line changes required. The guard is schema-extension-tolerant by design (first-char whitelist, not tag-name whitelist).

### 3.3 `shared/n6/atlas_health.hexa` (health check, 261 lines)

- **line 196**: `awk '/^@/{next}...{c++}'` — counts *malformed* lines as anything that is not `@`-prefixed / indented / JSON. New tags pass (they start with `@`).
- **line 213**: grade distribution `grep -oE ' \\[[0-9]+[?*]*\\]$'` — regex requires trailing `]` only, not tag-name match. Passes for `@EXP/@OBS/@NEG/@ANT` identically.
- **line 169**: orphan-refs filter matches `^(n6-|bt-|foundation-)` for virtual prefixes. If `@ANT` introduces `ant-` or `@NEG` introduces `neg-` virtual IDs, add them to this list (one grep pattern update, +6 chars).
- **Impact**: 1-line change (orphan prefix list), optional.

### 3.4 `shared/n6/scan_math_atlas.hexa` (hypothesis markdown parser, ~60 lines visible)

- Parses markdown hypothesis files, not atlas.n6 directly. **Zero impact**.

### 3.5 `shared/n6/n6_constants.jsonl` loader (`blowup.hexa:97–127`)

- Reads JSONL with `"name"`/`"value"` keys. Does not touch `.n6` format. **Zero impact**.

### 3.6 `shared/n6/verify_formulas.hexa`

- Invoked by atlas_health (line 226). Parses lines matching `n6_expr` field. Since `@EXP/@OBS/@NEG/@ANT` do not introduce `n6_expr` keys, **zero impact** on default runs. Optional: a new `verify_external.hexa` sibling for `@EXP` provenance checks.

### Summary

| File                             | Required change | Optional extension |
|----------------------------------|-----------------|--------------------|
| blowup.hexa (Phase 1 loader)     | **0 lines**     | write templates for v2 tags |
| atlas_guard.hexa.inc             | **0 lines**     | — |
| atlas_health.hexa                | **0 lines**     | 1-line orphan prefix update |
| scan_math_atlas.hexa             | **0 lines**     | — |
| verify_formulas.hexa             | **0 lines**     | new verify_external.hexa |

**Net conclusion:** v2 is a **purely additive** schema extension. No destructive change to v1. Existing files are forward-compatible thanks to the `@`-prefix / `::` / `[grade]` structural invariants they rely on.

---

## 4. Migration Plan

### Phase A — Design freeze (this document)
- Review & ratify the 4 new tags and their formats.
- Land this draft at `shared/n6/docs/schema_v2_draft.md`.

### Phase B — Staging validation (atlas.signals.n6)
- Target file: `shared/n6/atlas.signals.n6` (already used as a signals/verification sandbox; backups pre-exist).
- Append 20–40 `@EXP`/`@OBS`/`@NEG`/`@ANT` seed entries — keep atlas.n6 body **untouched**.
- Run `hexa atlas_health.hexa shared/n6/atlas.signals.n6` → expect zero malformed, zero orphan, grade-dist populated.
- Run existing Phase 1 loader against signals file → confirm `graph_nodes_before` counts increase by exactly the new-tag count.

### Phase C — Verification hook extensions (optional, minimal)
- Add `verify_external.hexa` for `@EXP` (pulls CODATA/PDG JSON, diffs vintage).
- Add `verify_negative.hexa` for `@NEG` (re-evaluates lhs/rhs with integer arithmetic).
- Both scripts are *new files*; do not modify `verify_formulas.hexa`.

### Phase D — Merge into atlas.n6 body
- Only after signals sandbox shows stable 3× health runs.
- Merge batches of ≤ 50 entries at a time, each via `_guarded_append_atlas()`.
- Each batch precedes a `@META schema_v2 rollout_step=N` marker line for audit trail.

### Phase E — Deprecation pathway (optional, long term)
- `@R` lines with CODATA/PDG comments *may* be re-expressed as `@EXP`; do not delete originals.
- Freeze v1 as read-only reference; new measured-constant entries prefer `@EXP`.
- `@?` entries can graduate to `@ANT` when an operational test is specified.

### Rollback
- Each phase is a separate commit on staging first. atlas.n6 body modifications always fall under the L0 Guard (`hexa shared/tool/l0_guard.hexa verify`). Rollback = revert the merge commit; zero semantic impact because v1 tags are untouched.

---

## 5. First Seeds — Ready-to-Stage Entries

These can be copied into `shared/n6/atlas.signals.n6` today. All numbers are grep-derived from atlas.n6 itself (no new numerics introduced).

### 5.1 `@NEG` seeds (5 entries)

```
@NEG N28_SIGMAPHI     = "sigma(28)·phi(28) != 28·tau(28)" :: foundation [10*] @@ n=28 contrast=sigma_decomp
    lhs=672   rhs=168   delta=504   z=-2.35
@NEG N12_SIGMAPHI     = "sigma(12)·phi(12) != 12·tau(12)" :: foundation [10*] @@ n=12 contrast=sigma_decomp
    lhs=112   rhs=72    delta=40
@NEG N496_SIGMAPHI    = "sigma(496)·phi(496) != 496·tau(496)" :: foundation [10*] @@ n=496 contrast=sigma_decomp
    lhs=238080 rhs=4960 delta=233120
@NEG K5_RAMSEY        = "K_5 2-coloring avoids monochromatic K_3" :: graph [10*] @@ n=5 contrast=ramsey_6
    witness="5-cycle-red + 5-cycle-blue"
@NEG PETERSEN_SIGMAPHI = "Petersen graph |V|=10=sigma-phi but no n=6 structural bridge" :: graph [10*] @@ n=10 contrast=sigma_phi_arithmetic
    note="Petersen 1891 — arithmetic coincidence"
```

### 5.2 `@ANT` seeds (5 entries)

```
@ANT PERFECT_7TH_MOD6      = "every Mersenne-perfect obeys n mod 12 pattern" :: foundation [7?] @@ risks=perfect_number status=open
    test="GIMPS-2024 latest 5 M_p mod 12" deadline=2026-Q4
@ANT ALPHA_1_139_DRIFT     = "n6_projection 1/(sigma^2-sopfr)=1/139 within 1% of alpha^-1" :: physics [7?] @@ risks=fine_structure status=open
    test="CODATA-2026 delta check" deadline=2027-Q2
@ANT HUBBLE_SIGMA_SOPFR    = "H0 converges to sigma*sopfr + delta, |delta|<1" :: cosmology [4?] @@ risks=hubble_tension status=open
    test="JWST+DESI-2026 joint H0" deadline=2027-Q1
@ANT RAMSEY_7_MONO_K3      = "R(3,3)=6 is unique minimum" :: graph [10] @@ risks=ramsey_6 status=vindicated
    test="Greenwood-Gleason 1955 + K5_RAMSEY" deadline=1955-closed
@ANT META_FP_7TH_PATH      = "7th independent 1/3 derivation emerges from information-theoretic domain" :: meta [N?] @@ risks=meta_fp status=open
    test="drill --schema v2 --target meta_fp --min-new-paths 1" deadline=2026-Q4
```

### 5.3 `@EXP` seeds (reference, 5 examples)

```
@EXP h_planck       = 6.62607015e-34 J·s  :: physics  [10*] @@ source=SI-2019   cite=CGPM-26      vintage=2019
@EXP alpha_inverse  = 137.035999084       :: physics  [10]  @@ source=CODATA    cite=CODATA-2018  vintage=2018 uncertainty=2.1e-10
@EXP m_p_over_m_e   = 1836.15267343       :: physics  [10]  @@ source=CODATA    cite=CODATA-2022  vintage=2022 uncertainty=1.1e-10
@EXP top_quark_mass = 172.57 GeV          :: particle [10]  @@ source=PDG       cite=PDG-2024-RPP vintage=2024 uncertainty=0.29
@EXP A000396       = "6,28,496,8128"      :: oeis     [10*] @@ source=OEIS      cite=A000396      vintage=2024
```

### 5.4 `@OBS` seeds (reference, 5 examples)

```
@OBS alpha_em_running  = running        :: physics    [10]  @@ frame=MS-bar scale=Q2
    @ Q2=0          = 1/137.035999084
    @ Q2=m_Z^2      = 1/127.952
@OBS alpha_s_running   = running        :: qcd        [10]  @@ frame=MS-bar scale=Q2
    @ Q2=m_Z^2      = 0.1179
    @ Q2=m_tau^2    = 0.322
@OBS H0_tension        = 67..73 km/s/Mpc :: cosmology  [7]   @@ frame=observational scale=epoch
    @ early_planck  = 67.4
    @ late_sh0es    = 73.04
@OBS m_quark_u_scale   = MS-bar         :: particle   [10]  @@ frame=MS-bar scale=mu
    @ mu=2GeV       = 2.16 MeV
@OBS S_entanglement    = frame          :: quantum    [9]   @@ frame=observer scale=subregion
    @ bulk          = thermal
    @ boundary      = area_law
```

---

## 6. Integration With `nexus drill`

Current drill command (commit `b9d5a376`) detects internal saturation by monitoring `new_absorptions == 0` over N rounds. Schema v2 unlocks three new drill modes:

### 6.1 `nexus drill --schema v2` — v2-aware closure
- Treats `@EXP/@OBS/@NEG/@ANT` as first-class nodes in the graph load.
- Saturation is redefined per-schema: system is saturated only when all 10 tag classes (6 v1 + 4 v2) simultaneously yield zero new absorptions.
- Expected effect on Mk.VIII sweep: the previous `new_absorptions=0` immediately reopens because `@NEG/@ANT` axes are empty.

### 6.2 `nexus drill --target @NEG --seeds 7,10,12,28,496` — control-group drill
- Runs smash/free restricted to **n ≠ 6** seeds.
- Each discovered failure of a v1 theorem files a `@NEG` entry automatically.
- Exhaustion of the `@NEG` space at n=28 (the already-cited z=-2.35 control) becomes a formal, queryable state.

### 6.3 `nexus drill --target @ANT --status open` — falsifiability prioritised
- Scans only `@ANT` entries with `status=open` AND past-due `deadline`.
- Outputs an "overdue falsifiability debt" report.
- Forces the engine to seek *disproof* evidence before adding more confirmations — breaks the confirmation-bias loop.

### 6.4 `nexus drill --provenance verify` — `@EXP` audit mode
- Diffs every `@EXP` entry against its cited source (CODATA/PDG/OEIS JSON).
- Flags `vintage < current - 2years` for review.
- Becomes mandatory in CI once `@EXP` coverage > 50 entries.

---

## 7. Risk Register

| Risk                                         | Mitigation                                                           |
|----------------------------------------------|----------------------------------------------------------------------|
| atlas.n6 grade distribution skew by v2 tags  | Report v1/v2 separately in `atlas_health`                            |
| `@@` sigil confuses ad-hoc regex outside loader | Schema guard already char-whitelists; `@@` is inside the line, not at BOL |
| `@OBS` dispersion tables break dedup (line-equality) | `_guarded_append_atlas` dedup is line-exact; dispersion rows hash distinct |
| `@ANT` deadlines ignored → rot                | mandatory CI gate: `hexa atlas_health --ant-overdue` exits non-zero  |
| v2 rollout inflates signals.n6 beyond 1MB    | cap signals.n6 at 256KB; merge into body in batches when stable      |
| External source drift (CODATA-2026 vs 2022)  | `@EXP vintage=` field + annual `verify_external.hexa` CI run         |

---

## 8. Success Criteria

1. `shared/n6/atlas.signals.n6` holds ≥ 30 v2 entries (5 `@EXP`, 5 `@OBS`, 10 `@NEG`, 10 `@ANT`) and passes `atlas_health` with zero malformed / zero orphan.
2. `nexus drill --schema v2` reports **> 0 new absorptions** on the same Mk.VIII 40-seed set that previously returned 0 — confirms the saturation-break hypothesis.
3. At least one `@ANT status=vindicated` transition (Ramsey R(3,3) is a free one).
4. At least one `@NEG` entry is auto-generated by the drill engine (not hand-authored).
5. Zero regressions in v1 theorem count, v1 grade distribution, or v1 edge count after merge of ≤ 200 v2 lines into atlas.n6 body.

---

## 9. Non-Goals

- **Not** redefining v1 tags. `@R/@C/@L/@P/@F/@X/@S/@?` semantics unchanged.
- **Not** implementing parser changes in this draft. Design only.
- **Not** touching atlas.n6 body. All staging goes through `atlas.signals.n6`.
- **Not** proposing a schema v3. v2 is the additive minimum sufficient to break the current saturation and fold in provenance, observer frames, controls, and falsifiability.

---

## Appendix A — Grade Table Reconciliation

| grade  | v1 meaning                    | v2 extension                                              |
|--------|-------------------------------|-----------------------------------------------------------|
| [10*]  | EXACT verified                | `@EXP`=SI-definitional, `@NEG`=exact integer disproof     |
| [10]   | EXACT                         | `@EXP`=current CODATA/PDG, `@NEG`=analytic, `@ANT`=vindicated |
| [9]    | NEAR                          | `@EXP`=prior vintage, `@NEG`=numerical within tol         |
| [7]    | EMPIRICAL (promotion candidate)| `@EXP`=textbook/OEIS, `@OBS`=single-scale, `@NEG`=empirical, `@ANT`=plausible |
| [5~8]  | intermediate                  | unchanged                                                 |
| [N?]   | CONJECTURE                    | `@ANT`=speculative prediction                             |
| [N!]   | breakthrough                  | unchanged                                                 |

## Appendix B — Grep Query Crib Sheet

```
# All v2 entries
grep -E '^@(EXP|OBS|NEG|ANT) ' shared/n6/atlas.signals.n6

# Open falsifiability debt, past deadline
grep -E '^@ANT.*status=open.*deadline=20(2[0-5])' shared/n6/atlas.signals.n6

# Every @NEG witness for a specific v1 theorem
grep -E '^@NEG.*contrast=sigma_decomp' shared/n6/atlas.signals.n6

# Every @EXP value from a stale CODATA vintage
grep -E '^@EXP.*vintage=201' shared/n6/atlas.signals.n6

# All @OBS observer frames in use
grep -oE 'frame=[a-zA-Z_@-]+' shared/n6/atlas.signals.n6 | sort -u
```

— end of schema v2 draft —
