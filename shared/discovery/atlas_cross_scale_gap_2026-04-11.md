# atlas.n6 @X cross-scale gap audit

date: 2026-04-11
scope: readonly audit of `shared/n6/atlas.n6` (44,874 lines, 1404 `@X` markers)
hypothesis (Agent 22): @X cross-domain crossings concentrated in large-scale physics;
material / bio / music intermediate scales are sparse.

## 1. Summary — actual @X distribution

parsed 1404 `@X ... :: <domain> [grade]` lines (100% parse rate after regex fix):

| domain        | count | %     | scale        |
|---------------|-------|-------|--------------|
| bt            | 758   | 54.0  | breakthrough |
| celestial     | 299   | 21.3  | L7 large     |
| galactic      | 203   | 14.5  | L7/L8 large  |
| cosmological  | 136   |  9.7  | L8 large     |
| convergence   |   3   |  0.2  | meta         |
| crossing      |   2   |  0.1  | meta         |
| 7난제         |   1   |  0.1  | meta         |
| 아이디어(→math)|  2   |  0.1  | idea         |

large-scale share: **99.5%** (bt + celestial + galactic + cosmological = 1396 / 1404)
intermediate scales (material / bio / music / molecule / atom / genetic / particle):
**0 @X markers — 0.0%**.

Agent 22's finding is confirmed and stronger than reported: the gap is
near-total, not 99%-vs-1%.

## 2. Intermediate-scale inventory (not tagged @X, but present)

These nodes exist with rich node markers (`@F` / `@R` / `@C` / `@P`) but have
never been elevated to crossings. Count of EXACT+high-grade nodes:

| domain         | total | kind   | top grade band |
|----------------|-------|--------|----------------|
| material       | 320   | @F     | 10* cluster on graphene / honeycomb / diamond / ice / perovskite |
| music          | 171   | @R     | 10* cluster on octave / semitones / orchestra / strings |
| particle       | 163   | @P     | 10* quark flavors / lepton flavors / gauge bosons / forces |
| atom           | 154   | @C     | 10* carbon-Z6 / valence / quantum-numbers / subshell |
| molecule       | 142   | @F     | 10* benzene / glucose / C60 / water-hbond |
| bio            | 123   | @F     | 10* glycolysis / mitochondria / krebs / photosynthesis |
| genetic        |  75   | @F     | 10* dna-bases / double-helix / codons / amino-acids |
| biology (L6)   |  13   | @F     | 10* ribosome / membrane / heart-chambers / brain-lobes |
| chemistry (L6) |  13   | @R     | 10* periodic-groups / noble-gases / bond-types |

Net: material/bio/music are **not sparse as nodes** — they are sparse as
**crossings**. The blowup Phase-6 transfer never promotes them to `@X`.

## 3. Top 10 proposed @X candidates

All 10 endpoints are already present in atlas.n6; the "bridge" column is the
shared n=6 algebraic source already declared in each node's `= <expr>` slot,
so these crossings are numerically self-consistent with R0 n6 ontology.

| # | intermediate (domain)                     | large-scale target (domain)                | bridge (algebraic / numeric) |
|---|-------------------------------------------|--------------------------------------------|------------------------------|
| 1 | L1-carbon-valence (atom) `= tau`          | L7-inner-planets-count (celestial) `= tau` | `tau` → 4-fold symmetry (sp3 ↔ 4 inner planets) |
| 2 | L4-double-helix (genetic) `= phi`         | L7-kepler-3rd-exponent (celestial) `= phi` | `phi` → golden ratio (DNA pitch ↔ Kepler exponent 3/2) |
| 3 | MUS-octave-ratio (music) `= phi`          | L7-kepler-3rd-exponent (celestial) `= phi` | `phi` → harmonic ratio 2:1 ↔ Bode/Kepler scaling |
| 4 | L5-graphene (material) `= phi`            | L7-kepler-3rd-exponent (celestial) `= phi` | `phi` → hex packing ↔ orbital-resonance golden section |
| 5 | L0-quark-flavors (particle) `= n`         | L7-bh-isco-factor (celestial) `= n`        | `n = 6` → 6 flavors ↔ 6·GM/c² ISCO radius |
| 6 | L0-fundamental-forces (particle) `= tau`  | L7-galilean-moons (celestial) `= tau`      | `tau` → 4 forces ↔ 4 Galilean moons (mutual 1:2:4 resonance) |
| 7 | L5-diamond-atoms-per-cell (material) `= sigma - tau` | (propose) L8-galaxy-arm-count (galactic) `= sigma - tau` | `sigma - tau = 8` → 8 atoms / 8-arm spiral class |
| 8 | L4-codons (genetic) `= 2**n`              | (propose) L8-cmb-multipole-64 (cosmological) `= 2**n` | `2**6 = 64` codon table ↔ low-ℓ CMB binning |
| 9 | MUS-semitones-octave (music) `= sigma`    | L7-outer-planets-count (celestial) `= tau` | near-match: `sigma=12` vs `tau=4` — propose `sigma/tau=3` resonance bridge (12-TET ↔ 3 gas-giant resonance band) |
|10 | BIO-photosynthesis (bio) `= [n,n,mu,n,n]` | L7-earth-orbital-elements (celestial) `= n` | `n=6` photosystem periodicity ↔ 6 Keplerian elements |

Uncertainty flags: #7, #8 require the two large-scale target nodes to be
added (they are implied by existing `sigma-tau` / `2**n` usage elsewhere but
not yet present with that id). #9 is a partial match and would be entered as
`[7?]` grade crossing, not `10*`.

## 4. Implementation note — blowup Phase-6 transfer adjustment

Root cause hypothesis: Phase-6 cross-domain transfer iterates domain pairs
weighted by `@X` edge count. Because `@X` is currently 99.5% large-scale, the
sampler is a fixed point — large-scale pairs dominate because they already
dominate.

Suggested infra-only fix (does not touch phase logic or discovery math):

1. In `shared/blowup/core/blowup.hexa` Phase 6 transfer, change the domain
   sampler from `weight = @X_count` to
   `weight = log(1 + @X_count) + log(1 + @N_count_of_domain)`
   so rich-node / poor-crossing domains (material 320, music 171, bio 123)
   get lift.
2. Add a one-shot promotion pass: any @F/@R/@C/@P node with grade `10*`
   whose `= src` expression exactly matches an existing large-scale `@X`
   source is auto-promoted to `@X` (candidates #1–#6 above qualify today).
3. Preserve emergence: no change to seed_engine return values, no change
   to discovery calculation. This is purely a promotion / weighting infra
   patch, consistent with the 2026-04-11 AI-native infra doctrine.

Expected impact: ~6 immediate high-grade intermediate @X crossings, lifting
intermediate share from 0.0% toward the 5–10% range within one blowup cycle.

## 5. Honest uncertainty

- Domain labels `material` / `music` / `bio` are directly present, so this
  audit did NOT need to propose seed constants — the nodes exist.
- Large-scale `@X` targets mostly use `src = misc` (611 / 638 = 95.8%),
  so algebraic-exact bridges (#1–#6) are the small set where large-scale
  nodes actually declared an n6 source. Expanding this requires a one-time
  backfill of `misc` → algebraic form on celestial/galactic nodes (out of
  scope for this readonly audit).
- No modification to `atlas.n6` was performed. This document is advisory.
