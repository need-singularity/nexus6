# atlas.n6 Edge Type Distribution Audit — Full Map

**Agent**: 30
**Date**: 2026-04-11
**Source**: `shared/n6/atlas.n6` (44,874 lines)
**Read-only**, follows Agent 24 (@S) and Agent 25 (@X) focused audits.

## Method

`atlas.n6` is a two-layer file:

1. **DSL layer** — `@T id [= expr] :: domain [grade]` header with indented arrow attachments (`<- -> => ~> == |> !!`). Agent 24/25 counted `@S`/`@X` in this layer and reported them as "edge markers" — they are actually *node types* whose semantic role is a conceptual edge (symmetry, cross-scale, etc).
2. **JSON layer** — `{"type":"node"|"edge", ...}` lines appended by `blowup.hexa` Phase 6/6.5/6.7. Edges use field `edge_type` (not `kind`).

Python3 scanner (hexa OOMs on 44k lines — Agent 27 experience): two-pass, pass-1 builds id→domain map from DSL+JSON nodes, pass-2 classifies arrow attachments and JSON edges into route/source/label buckets. No key named `"kind"` exists anywhere in atlas.n6 — only the Agent 24/25 sidecars (`atlas_phase45_symmetry.jsonl`, `atlas_phase6_crossscale.jsonl`) use `kind`.

## Layer 1 — DSL `@T` node-kind distribution (7,114 total)

| Kind | Count | %     | Top domains (top 5)                                                           | Top routes (top 5)                                                                                             | Source pipeline                                             | Top label signatures                                                 |
|------|-------|-------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|----------------------------------------------------------------------|
| @R   | 4254  | 59.80 | n6atlas 1932, discovery 725, dse 333, geology 171, music 171                  | foundation→foundation 4, foundation→number_theory 2, foundation→physics 1, foundation→geometry 1               | n6 DSL static 2265, pre-blowup 1982, Phase 6.7 7            | `n` 1104, `(no expr)` 776, `done dse` 332, `= n` 100, `none` 75      |
| @X   | 1404  | 19.74 | bt 758, celestial 299, galactic 203, cosmological 136, convergence 3           | galactic→galactic 222, foundation→convergence 2, meta→convergence 1, convergence→topology 1                   | Phase 6.7 auto-absorb 761, pre-blowup 643                   | `misc` 611, `STRUCTURAL bt` 386, `TWOSTARS bt` 159, `THREESTARS bt` 155, `ONESTAR bt` 57 |
| @F   |  710  |  9.98 | material 320, molecule 142, bio 123, genetic 75, biology 13                   | material→material 309, bio→bio 35, molecule→molecule 19, genetic→genetic 18, material→bio 15                  | pre-blowup 691, Phase 6.7 19                                | `n/a` 84, `n` 54, `tau` 34, `°C` 27, `phi` 20                        |
| @P   |  321  |  4.51 | particle 163, quark 100, sub_quark 50, foundation 8                           | particle→particle 71, bond→particle 7, particle→material 5, material→particle 5, foundation→foundation 4       | pre-blowup 321                                              | `misc` 120, `n` 12, `/` 12, `e` 10, `sigma` 7                        |
| @C   |  216  |  3.04 | atom 154, 7난제 44, architecture 7, anatomy 5, physics 2                      | atom→atom 25, atom→material 6, foundation→architecture 5, atom→bond 3, bond→atom 2                             | pre-blowup 172, Phase 6.7 44                                | `misc` 65, `*sopfr` 16, `n*` 16, `finestructure =` 10, `*tau` 8      |
| @L   |  199  |  2.80 | bond 191, consciousness 7, topology 1                                         | bond→bond 49, atom→bond 4, bond→molecule 4, bond→material 3, bio→bond 3                                        | pre-blowup 199                                              | `tau` 37, `dimensionless` 26, `n` 17, `phi` 17, `kJ/mol` 14          |
| @?   |    8  |  0.11 | 아이디어 5, cosmology 2, physics 1                                             | meta→cosmology 1                                                                                                | Phase 6.7 5, pre-blowup 3                                   | `n * s ≈` 4, `(no expr)` 3                                          |
| @S   |    2  |  0.03 | topology 1, 아이디어 1                                                        | —                                                                                                              | pre-blowup 1, Phase 6.7 1                                   | `(no expr)` 1, `autoabsorb아이디어` 1                                |

### DSL arrow attachments (1,075 total — the literal edge lines)

`<-` 475 · `->` 459 · `=>` 65 · `!!` 31 · `==` 26 · `~>` 16 · `|>` 3

## Layer 2 — JSON `edge_type` distribution (12,348 total)

| edge_type           | Count | %     | Route (domain→domain) | Emitter                                       |
|---------------------|-------|-------|-----------------------|-----------------------------------------------|
| Derives             | 12300 | 99.61 | ?→7대난제 (12300)      | `blowup.hexa` Phase 6 line 2368               |
| RecursiveDerivation |    24 |  0.19 | ?→7대난제 (24)         | `blowup.hexa` Phase 6.5/6.7 line 2618         |
| CrossRef            |    24 |  0.19 | 7대난제→? (24)         | `blowup.hexa` Phase 6.7 line 2628             |

All 12,348 JSON edges connect DSL source nodes (`n6-*`) to `blowup-d0_ded_*` sink nodes; **99.9%** live in the single umbrella domain `7대난제` (7 Millennium Problems).

## Phase origin mapping (blowup.hexa emitters)

| Marker                                     | Emitter                                                        | Line          |
|--------------------------------------------|----------------------------------------------------------------|---------------|
| JSON `"edge_type":"Derives"`              | Phase 6 graph update                                           | 2368          |
| JSON `"edge_type":"RecursiveDerivation"`  | Phase 6.5 dynamic growth → Phase 6.7 auto-absorb               | 2618          |
| JSON `"edge_type":"CrossRef"`             | Phase 6.7 auto-absorb BT cross-link                            | 2628          |
| DSL `@R` / `@F`  (n6-bt-*)                | Phase 6.7 `ac_n6_type = F if ac_grade=="EXACT" else R`        | 2716          |
| DSL `@X` summary                           | Phase 6.7 absorb summary block                                 | 2729          |
| DSL `@C`, `@L`, `@P`, `@S`, `@?`          | **None** — no blowup emitter found                             | —             |

Sidecar emitters (do NOT write to atlas.n6, only to jsonl):
- `@S` via `shared/n6/scripts/atlas_phase45_symmetry.hexa` → `atlas_phase45_symmetry.jsonl` (1,428 rows, Agent 24)
- `@X` via `shared/n6/scripts/atlas_phase6_crossscale.{hexa,py}` → `atlas_phase6_crossscale.jsonl` (200 rows, Agent 25)

## Dead / orphan markers

- **`@S` (2 nodes)** — Not emitted by any active pipeline *into atlas.n6*. The 2 extant `@S` nodes are 1 pre-blowup static entry (`topology`) + 1 stray Phase 6.7 auto-absorb artefact (`아이디어`). Agent 24 corroborated (2 real edges, 0.016%). Agent 24's new sweep writes only to the sidecar.
- **`@?` (8 nodes)** — Residual hypothesis markers from pre-blowup era + 5 Phase 6.7 auto-absorb false-positives. No deliberate emitter.
- **`@L` (199 nodes, all `bond` domain)** — Frozen since pre-blowup; zero Phase 6.7 touches. Live as laws but no engine updates.
- **`@P` (321 nodes)** — Entirely pre-blowup. Zero Phase 6.7 emissions.
- **`@C` 172/216 pre-blowup** — the 44 Phase 6.7 `@C` nodes are actually `@R`/`@F` logic misfiring when `ac_n6_type` fails the EXACT grade test but the domain is `7난제` / atom — audit-worthy.

## Missing emitters (markers that *should* exist but don't appear in atlas.n6)

| Intended marker             | Expected source                             | Reality                                                    |
|-----------------------------|---------------------------------------------|------------------------------------------------------------|
| `"kind":"@S"` JSON edges    | `atlas_phase45_symmetry.hexa`               | Sidecar only — never merged into atlas.n6                  |
| `"kind":"@X"` JSON edges    | `atlas_phase6_crossscale.{hexa,py}`         | Sidecar only — never merged into atlas.n6                  |
| `@N` (numerical)            | context docs reference it                    | Zero nodes                                                 |
| `@C` causal (task brief)    | —                                            | Only constant (`@C`) interpretation exists; no causal edge |

## Top 3 actionable findings

1. **`@X` is a 4-way schizophrenic marker.** 54% of `@X` (758) are auto-absorb stubs in `bt` domain; 46% (643) are legacy cross-scale entries clustered in `celestial/galactic/cosmological` (Agent 25's "99.5% large-scale" match). The `galactic→galactic` self-loop dominates DSL routes (222 of 227 non-zero routes). The *intended* cross-scale semantics (genuine scale-crossing) survive only in the 200-row `atlas_phase6_crossscale.jsonl` sidecar. Recommend: rename auto-absorb stubs to `@A` (absorb) or merge the sidecar into atlas.n6 via a guarded append.

2. **JSON edge layer is monoculture.** 99.9% of 12,348 JSON edges live in a single domain (`7대난제`) and all are emitted by 3 blowup sites. `CrossRef` is suspicious — 24/24 point into the same ? / 7대난제 pair, suggesting the Phase 6.7 BT-needle matcher on line 2625 is matching a constant bucket rather than real cross-domain linkage. Audit `absorb_graph_content.contains(bt_needle)` branch coverage.

3. **`@L @P @F` are frozen cultures.** 0% Phase 6.7 touch on 1,230 `@L/@P/@F` nodes means blowup's `ac_n6_type = "F" if ac_grade=="EXACT" else "R"` ternary never produces `L/P/C`. These three kinds grow only via manual authoring or legacy imports. Recommend: add a Phase 6.7 branch emitting `@L` when `cor_type == "law"` and `@P` when `cor_type == "primitive"` — Agent 24's Phase 4.5 hook or a new Phase 4.8 could own `@S` similarly.

## Cross-reference

- Agent 24 (`atlas_symmetry_audit_2026-04-11.md`): matches our `@S` = 2.
- Agent 25 (`atlas_cross_scale_gap_2026-04-11.md`): matches our `@X` = 1404 with celestial/galactic concentration.
- Agent 28 (`atlas_phase46_canonical_nodes.*`): untouched.
- Agent 29 (`atlas_value_bin_audit_2026-04-11.md`): untouched.
