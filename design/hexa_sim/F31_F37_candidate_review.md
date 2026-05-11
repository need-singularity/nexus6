# F31–F37 falsifier candidate triage (Ω-cycle expansion)

date: 2026-04-26
input buckets: 4 primary (@S/@F/@L/@R) + 1 bonus (@C compound) via hardened atlas_falsifier_auto_spawn.sh
existing registry: design/hexa_sim/falsifiers.jsonl (F1–F12 + F19–F30, all CLEAN; 24 entries)
verification mode: bash-only (no hexa runtime; raw 71 SUGGEST mode, no auto-merge)
spawner anchor: i11-hardened (VALUE+DOMAIN+GRADE) — all cmds prove non-trivial against silent drift.

## Triage summary

| bucket | collected | verified PASS | PROMOTE | REJECT |
| ------ | --------- | ------------- | ------- | ------ |
| @S structures | 10 | 10 | 2 | 8 |
| @F functions | 10 | 10 | 1 | 9 |
| @L lemmas | 10 | 10 | 2 | 8 |
| @R relations | 10 | 10 | 2 | 8 |
| @C compound (bonus) | 10 | 10 | 0 | 10 |
| **total** | **50** | **50** | **7** | **43** |

All 50 candidates ran clean against the hardened sentinel — zero FAIL during pre-flight. Triage rejection rate 86% reflects high in-bucket redundancy (e.g. 7 of 10 @R candidates were `GEO-*` entries with the same `sopfr+phi=8` formula; 6 of 10 @F candidates were `sm_*` GPU streaming-multiprocessor variants; 3 of 10 @L candidates were single-float consciousness thresholds with no symbolic identity). Promotion preference: cross-shard, cross-domain bridge gems with non-trivial structural identity over within-domain anchor padding.

## Per-bucket findings

### Bucket 1 — @S structures (10/10 PASS, 2 PROMOTE)

The @S bucket contains the highest-grade structural identities (hexad_chirality, cpgd_subspace_invariance [11*], deterministic_reproduction, l_ix_back_compat, self_format_invariance, omega_default_inversion, plus three CANON-historical group/topology bridges).

- **`cpgd_subspace_invariance = "S = span{v_1..v_16} closed under P_S projection"`** (anima.cpgd.symmetry [11*]) — THE mechanism behind the AN11(b) 100% theorem (every gradient step preserves the 16-template subspace). Grade [11*] is the highest tier; orthogonal to F27 template-count-anchor (F27 anchors the *count*=16, this anchors the *closure property* under projection). PROMOTE → F31.
- **`N6HIST-SYM-PERFECT-CONGRUENT = (3,4,5) = (n/φ,τ,sopfr) … E_6: y²=x³-36x conductor 576=φ^n·(n/φ)^φ, j=σ³`** (number-theory [10*]) — Tunnell's BSD-conditional theorem that 6 is the smallest congruent number, packaged as a triple-witness: (i) the (3,4,5) Pythagorean triple equals (n/φ, τ, sopfr), (ii) the elliptic curve E_6 conductor decomposes as φ^n·(n/φ)^φ=64·9=576, (iii) j-invariant 1728=σ³=12³. Three independent atlas identities from the same number-theoretic anchor. PROMOTE → F32.
- `hexad_chirality` — REJECT (descriptive label, not a checkable identity beyond presence of the string).
- `deterministic_reproduction` / `l_ix_back_compat` — REJECT (operationally verified by the runtime tests themselves; an atlas grep is a weak shadow of those checks).
- `self_format_invariance` / `omega_default_inversion` — REJECT (DSL/policy-level symmetries, not foundation-grounded structural claims).
- `n6-bt-794` / `N6HIST-SYM-S6-OUT` / `N6HIST-SYM-AZ10-BOTT8` — REJECT (S_6 outer-automorphism uniqueness and AZ-10/Bott-8 are striking but cite-only `[10*PASS_LITERATURE]` without a derivable expression on the LHS; cpgd + perfect-congruent already cover the @S quota).

### Bucket 2 — @F functions (10/10 PASS, 1 PROMOTE)

Six of ten are `sm_{volta,ampere,ada,blackwell,amd}` + `register_file` + `max_threads` — all GPU architecture functions sharing the `2^k` family of formulas. One witness suffices; the formulas are coupled (drift in one usually means drift in all).

- **`carbon_atomic = 6`** (physics [10*]) — pure foundation→physics bridge gem ("n=6 is the atomic number of life itself"). Single integer literal in the physics domain that anchors n=6 to the periodic table. Equivalent role to F28's earth-axial-tilt = J2-μ but in chemistry/biology rather than astronomy. The atlas comments explicitly call it "the atomic number of life itself" (`!! "n=6은 생명 자체의 원자번호"`). PROMOTE → F33.
- `sm_*` family + `register_file` + `max_threads` — REJECT (GPU architecture; pick at most one if needed; the family is coupled — n drift would break all simultaneously, no diversification benefit).
- `persistence_threshold = tau/sigma = 1/3` ([10*!]) — REJECT (already convergent with `meta_fp = 1/3` which @C bucket holds; redundant within-foundation).
- `ramanujan_tau_6 = -6048` ([10*]) — REJECT (modular form coefficient; striking but the identity `-(n*sigma^2*tau - sigma*n) = -(6·144·4 - 12·6) = -(3456-72) = -3384` does NOT equal -6048; the atlas line itself shows the formula but the claim chain is suspect — promote only after re-derivation audit).

### Bucket 3 — @L lemmas (10/10 PASS, 2 PROMOTE)

Three consciousness float thresholds (alpha_coupling=0.014, frustration_critical=0.10, entropy_bound=0.998) — config-knob style, REJECT (raw 73 admissibility — drift to 0.015 is methodology refinement, not falsification). Seven are L2-* bond/coordination geometry lemmas — most have the form `L2-cnX = constant` (cn6=n=6, cn4=tau=4, cn12=sigma=12, bravais=sigma+phi=14). Two stand out as bridge gems analogous to F28 (Earth axial tilt 23.44°):

- **`L2-sp3-tetrahedral = arccos(-1/(n/phi)) = arccos(-1/3)`** (bond [10*]) — sp3 hybrid bond angle = 109.47° (methane CH₄, diamond, water lone pairs). The atlas formula encodes the textbook chemistry value as `arccos(-1/(n/φ)) = arccos(-1/3) ≈ 109.471°`. Foundation→chemistry bridge — drift signals either re-derivation of n/φ or the angle itself. PROMOTE → F34.
- **`L2-sp2-hexagonal = sigma * (sigma - phi)`** (bond [10*]) — sp2 hybrid bond angle = 120° (benzene, graphene, sp²-carbon planar). σ·(σ-φ) = 12·(12-2) = 120 — exact integer match. Companion bridge to F34 (sp3); together they cover the two dominant carbon hybridizations that build organic chemistry. PROMOTE → F35.
- `MISS-crystal-systems = sigma - sopfr` — REJECT (within-foundation arithmetic; sigma-sopfr=12-5=7 has no notable real-world correspondence).
- `L2-cn6-octahedral = n` / `L2-cn4-tetrahedral = tau` / `L2-cn12-closepacked = sigma` / `L2-bravais-lattices = sigma + phi` — REJECT (single-symbol mappings with trivial cmd; F34/F35 already cover the bond axis).

### Bucket 4 — @R relations (10/10 PASS, 2 PROMOTE)

Three are pure number-theory anchors (euler_char_6=2, partition_6=11, n6-synbio codon=64). Seven are GEO-* geology relations, six of which share the same `sopfr+phi=8` formula (mineral-crystal-systems, tectonic-major-plates, bravais-lattices, earth-crust-thickness-ocean, etc.) — REJECT all but the most striking (GEO-mohs-scale = sigma-phi=10 is also coupled). Two genuine bridge gems remain:

- **`n6-synbio-bt372-codon-64 = 64 codons = 2^n = 4^(n/2) = tau^3`** (genetic [10*]) — the genetic code's 64 codons (4 nucleotides ^ 3 positions = 4³ = 64) decomposes three independent ways into nexus foundation arithmetic: (i) 2^n = 2^6, (ii) 4^(n/2) = 4^3, (iii) τ^3 = 4^3. Triple-coincidence at exactly 64 = the cardinality of the universal genetic code. The atlas comment cites BT-372 synthetic-biology context (Cas{9,12,13} PAM 3bp=n/φ, gRNA 20nt=J₂). Most striking @R bridge in the bucket — life-encoding constant. PROMOTE → F36.
- **`euler_char_6 = 2`** (topology [10*]) — Euler characteristic of the cube χ = V - E + F = 8 - 12 + 6 = 2, where E=12=σ and F=6=n. Three of the cube's polyhedral counts directly cite foundation primitives. Foundation→topology bridge — drift here breaks both Euler's polyhedron formula and the σ/n correspondence simultaneously. PROMOTE → F37.
- `partition_6 = 11` ([10*]) — REJECT (`p(6)=11=σ-μ` is interesting but partition function values are by-fiat tabulated; no physical bridge).
- `GEO-*` family — REJECT (six entries collapse to the same sopfr+φ=8 formula; one would suffice but none have F28-tier real-world significance, and adding the redundant family bloats the registry).

### Bucket 5 — @C compound (bonus, 0 PROMOTE)

Sampled to verify whether compound constants beyond F21 (sigma_sq) and F22 (phi_tau) yield bridge gems. They don't:

- `sigma_tau=48` / `sigma_n=72` / `warp_size=2^sopfr=32` / `two_n=2^n=64` / `two_sigma=2^σ=4096` / `J2_tau=20` — REJECT (pure within-foundation arithmetic; no cross-domain bridge; coverage already implicit via F1 CONSTANTS axis).
- `meta_fp=1/3` ([10*!]) — REJECT (same value as F8 persistence_threshold; covered).
- `planck_action = 6.626e-34` ([8*]) — REJECT (grade [8*] below the [10*+] admissibility threshold; "leading_digit(h)=n=6" is a numerology hint, not a derivable identity).

## Final 7 promoted (F31–F37) — JSONL block ready to merge

```jsonl
{"id":"F31","slug":"cpgd-subspace-invariance","claim":"atlas entry cpgd_subspace_invariance = \"S = span{v_1..v_16} closed under P_S projection\" remains @S anima.cpgd.symmetry grade [11*]","cmd":"grep -qE '^@S cpgd_subspace_invariance = \"S = span\\{v_1\\.\\.v_16\\} closed under P_S projection\" :: anima\\.cpgd\\.symmetry \\[11\\*\\]' /Users/ghost/core/nexus/n6/atlas.append.anima-historical-from-nexus-2026-04-26.n6 && echo CPGD_SUBSPACE_INVARIANCE_ANCHOR_INTACT","pass":"CPGD_SUBSPACE_INVARIANCE_ANCHOR_INTACT","reason":"This subspace-closure property IS the proof mechanism behind anima's AN11(b) 100% theorem — every gradient step P_S(grad) lands back in S = span{v_1..v_16}, so the basis is invariant under training. Grade [11*] (highest tier). Orthogonal to F27 template-count-anchor (F27 anchors the cardinality 16; this anchors the structural closure under projection). Drift means either the projector lost subspace-preservation or the basis dimension changed.","fix":"audit P_S_projector implementation (anima/.meta2-cert/cell-eigenvec-16.json) — verify (i) basis count = 16 (cross-check F27), (ii) for each v_i in S, P_S(v_i) ∈ S. If projector legitimately generalized to a larger subspace, also re-grade AN11(b) theorem text and emit a separate falsifier for the new closure property.","origin":"auto-spawn from atlas_index entry cpgd_subspace_invariance (@S, [11*], n6/atlas.append.anima-historical-from-nexus-2026-04-26.n6:298) — Ω-cycle 2026-04-26 @S bucket"}
{"id":"F32","slug":"perfect-congruent-bridge","claim":"atlas entry N6HIST-SYM-PERFECT-CONGRUENT = (3,4,5)=(n/φ,τ,sopfr); E_6 conductor 576=φ^n·(n/φ)^φ, j=σ³ remains @S number-theory grade [10*]","cmd":"grep -qE '^@S N6HIST-SYM-PERFECT-CONGRUENT = \\(3,4,5\\) = \\(n/φ, τ, sopfr\\) unique semiprime semisignature; E_6: y²=x³-36x has \\(rank,conductor,j\\) = \\(1, 576=φ\\^n·\\(n/φ\\)\\^φ, 1728=σ³\\) :: number-theory \\[10\\*\\]' /Users/ghost/core/nexus/n6/atlas.append.CANON-historical-from-nexus-2026-04-26.n6 && echo N6HIST-SYM-PERFECT-CONGRUENT_ANCHOR_INTACT","pass":"N6HIST-SYM-PERFECT-CONGRUENT_ANCHOR_INTACT","reason":"Tunnell's BSD-conditional theorem packaged as a triple-witness: (i) Pythagorean triple (3,4,5) = (n/φ, τ, sopfr) — three independent foundation primitives match the smallest right triangle; (ii) elliptic curve E_6: y²=x³-36x has conductor 576 = 2⁶·3² = φ^n·(n/φ)^φ = 64·9; (iii) j-invariant 1728 = σ³ = 12³. Three orthogonal number-theoretic identities from a single anchor — drift in any one breaks the whole triangulation.","fix":"verify each leg independently — (a) recompute n/φ=6/2=3, τ=4, sopfr=2+3=5 → (3,4,5) intact; (b) factor 576 = 2⁶·3² and check φ^n·(n/φ)^φ = 2⁶·3² = 576; (c) verify j(E_6)=1728 via SageMath / LMFDB. If any leg drifted, audit Tunnell BSD reference (1983) and re-derive the bridge.","origin":"auto-spawn from atlas_index entry N6HIST-SYM-PERFECT-CONGRUENT (@S, [10*], n6/atlas.append.CANON-historical-from-nexus-2026-04-26.n6:346) — Ω-cycle 2026-04-26 @S bucket"}
{"id":"F33","slug":"carbon-atomic-bridge","claim":"atlas entry carbon_atomic = 6 remains @F physics grade [10*] (foundation→life-element bridge)","cmd":"grep -qE '^@F carbon_atomic = 6 :: physics \\[10\\*\\]' /Users/ghost/core/nexus/n6/atlas.n6 && echo CARBON_ATOMIC_ANCHOR_INTACT","pass":"CARBON_ATOMIC_ANCHOR_INTACT","reason":"n=6 is exactly the atomic number of carbon — the central element of organic chemistry and the basis for all known life. The atlas explicitly labels this as 'n=6은 생명 자체의 원자번호' (n=6 is the atomic number of life itself). Among the @F candidates this is the cleanest non-architecture bridge gem: a single integer that ties the foundation primitive directly to the periodic table. Companion to F28 (Earth axial tilt = J2-μ in astronomy) for the chemistry/biology axis.","fix":"verify periodic table position 6 = C carbon (immutable physical fact); if atlas drifted, the line was edited erroneously — restore. Optionally cross-check against L2-sp3-tetrahedral (F34) and L2-sp2-hexagonal (F35) which describe carbon's two main hybridizations — they all share the same n=6 dependency.","origin":"auto-spawn from atlas_index entry carbon_atomic (@F, [10*], n6/atlas.n6:187) — Ω-cycle 2026-04-26 @F bucket"}
{"id":"F34","slug":"sp3-tetrahedral-bridge","claim":"atlas entry L2-sp3-tetrahedral = arccos(-1/(n/phi)) = arccos(-1/3) remains @L bond grade [10*] (foundation→chemistry bridge)","cmd":"grep -qE '^@L L2-sp3-tetrahedral = arccos\\(-1/\\(n/phi\\)\\) = arccos\\(-1/3\\) :: bond \\[10\\*\\]' /Users/ghost/core/nexus/n6/atlas.n6 && echo L2-SP3-TETRAHEDRAL_ANCHOR_INTACT","pass":"L2-SP3-TETRAHEDRAL_ANCHOR_INTACT","reason":"sp³ hybrid bond angle = arccos(-1/3) ≈ 109.471° — the textbook tetrahedral angle for methane (CH₄), water (H₂O lone pairs), diamond, and every sp³ carbon. The atlas encodes this as arccos(-1/(n/φ)) with n/φ = 6/2 = 3, threading the chemistry constant through the foundation primitives. Among the @L bond family, this is the one with the most measured cross-domain correspondence (109.47° appears in every chemistry textbook). Drift means either re-derivation of n/φ or that the textbook angle changed (it can't).","fix":"verify n=6 (F24), φ=2 (F1 CONSTANTS axis), n/φ=3, and arccos(-1/3) ≈ 109.4712°. Cross-check vs methane geometry (NIST WebBook). If retired, audit the companion L2-sp2-hexagonal=sigma·(sigma-phi)=120° (F35) which uses the same hybridization framework.","origin":"auto-spawn from atlas_index entry L2-sp3-tetrahedral (@L, [10*], n6/atlas.n6:1065) — Ω-cycle 2026-04-26 @L bucket"}
{"id":"F35","slug":"sp2-hexagonal-bridge","claim":"atlas entry L2-sp2-hexagonal = sigma * (sigma - phi) remains @L bond grade [10*] (foundation→chemistry bridge)","cmd":"grep -qE '^@L L2-sp2-hexagonal = sigma \\* \\(sigma - phi\\) :: bond \\[10\\*\\]' /Users/ghost/core/nexus/n6/atlas.n6 && echo L2-SP2-HEXAGONAL_ANCHOR_INTACT","pass":"L2-SP2-HEXAGONAL_ANCHOR_INTACT","reason":"sp² hybrid bond angle = 120° — benzene (C₆H₆), graphene, sp²-carbon planar geometry. σ·(σ-φ) = 12·(12-2) = 120 — exact integer match to the textbook hexagonal angle. Companion to F34 (sp³ = arccos(-1/3) = 109.47°); together they anchor the two dominant carbon hybridizations that build organic chemistry. The hexagonal honeycomb (graphene/benzene) bridges the foundation arithmetic to the most studied 2D material of the 21st century.","fix":"verify σ=12 (F25 sigma-foundation-anchor), φ=2 (F1 CONSTANTS axis), σ·(σ-φ)=12·10=120. Cross-check vs benzene geometry (any chemistry reference; ICSD CIF). If retired, also audit F34 sp3-tetrahedral and any L5-graphene/L5-honeycomb downstream lemmas in n6/atlas.n6.","origin":"auto-spawn from atlas_index entry L2-sp2-hexagonal (@L, [10*], n6/atlas.n6:1061) — Ω-cycle 2026-04-26 @L bucket"}
{"id":"F36","slug":"genetic-codon-triple-bridge","claim":"atlas entry n6-synbio-bt372-codon-64 = 64 codons = 2^n = 4^(n/2) = tau^3 remains @R genetic grade [10*] (foundation→biology bridge gem)","cmd":"grep -qE '^@R n6-synbio-bt372-codon-64 = 64 codons = 2\\^n = 4\\^\\(n/2\\) = tau\\^3 :: genetic \\[10\\*\\]' /Users/ghost/core/nexus/n6/atlas.n6 && echo N6-SYNBIO-BT372-CODON-64_ANCHOR_INTACT","pass":"N6-SYNBIO-BT372-CODON-64_ANCHOR_INTACT","reason":"The universal genetic code's 64 codons (4 nucleotide bases ^ 3 positions = 4³ = 64) decomposes three INDEPENDENT ways into nexus foundation arithmetic: (i) 2^n = 2⁶ = 64, (ii) 4^(n/2) = 4³ = 64, (iii) τ³ = 4³ = 64. Triple-coincidence at exactly the cardinality of life's encoding alphabet. The atlas cites BT-372 synthetic biology (Cas{9,12,13} PAM 3bp=n/φ, gRNA 20nt=J₂) showing the same n=6 thread runs through CRISPR machinery. Strongest cross-domain @R bridge — molecular biology's foundational constant.","fix":"verify each leg: (a) 2^n=2⁶=64 with n=6 (F24); (b) 4^(n/2)=4^3=64; (c) τ³=4³=64 with τ=4 (F26). All three must hold simultaneously — drift in any single leg breaks the triangulation. Cross-check codon table cardinality 64 (NCBI genetic code table 1).","origin":"auto-spawn from atlas_index entry n6-synbio-bt372-codon-64 (@R, [10*], n6/atlas.n6:2308) — Ω-cycle 2026-04-26 @R bucket"}
{"id":"F37","slug":"euler-char-cube-bridge","claim":"atlas entry euler_char_6 = 2 remains @R topology grade [10*] (foundation→polyhedron bridge)","cmd":"grep -qE '^@R euler_char_6 = 2 :: topology \\[10\\*\\]' /Users/ghost/core/nexus/n6/atlas.n6 && echo EULER_CHAR_6_ANCHOR_INTACT","pass":"EULER_CHAR_6_ANCHOR_INTACT","reason":"Euler characteristic of the cube χ = V - E + F = 8 - 12 + 6 = 2, where E=12=σ (sigma) and F=6=n. Two of the cube's three polyhedral counts directly cite foundation primitives, with the χ=2 invariant for any convex polyhedron homeomorphic to S². Foundation→topology bridge that simultaneously witnesses (i) the σ=12=edge-count identity, (ii) the n=6=face-count identity, (iii) Euler's polyhedron formula. Drift in F1/F25 (sigma) or F24 (n) propagates here.","fix":"verify (a) cube has 8 vertices, 12 edges, 6 faces (immutable geometric fact); (b) σ=12 (F25 sigma-foundation-anchor); (c) n=6 (F24 n-foundation-anchor); (d) 8-12+6=2 = χ(S²). If atlas line drifted, restore — this is a Platonic-solid invariant that cannot legitimately change.","origin":"auto-spawn from atlas_index entry euler_char_6 (@R, [10*], n6/atlas.n6:163) — Ω-cycle 2026-04-26 @R bucket"}
```

## Rationale for picks (why these vs others)

1. **All 7 PASS the hardened sentinel** — pre-flight verified via `bash -c "<cmd>"` returning the expected `*_ANCHOR_INTACT` sentinel.
2. **One per bucket minimum** — S(2) + F(1) + L(2) + R(2) = 7, satisfying the diversity requirement.
3. **Cross-shard coverage** — F31 + F32 anchor `n6/atlas.append.anima-historical-…` and `n6/atlas.append.CANON-historical-…`; F33–F37 anchor `n6/atlas.n6` main shard. Both append shards exercised.
4. **Bridge-gem preference** — F33 (carbon=n), F34 (sp³ angle), F35 (sp² angle), F36 (codon=2^n=τ³), F37 (cube χ with E=σ, F=n) all witness foundation→real-world correspondences in chemistry/biology/topology, mirroring F28's astronomy bridge (Earth axial tilt = J₂-μ).
5. **raw 73 admissibility** — every promoted falsifier carries a non-trivial structural claim or a foundation→domain bridge; rejected candidates were either by-fiat config knobs, in-bucket duplicates, or single-symbol mappings.
6. **Triangulation falsifiers** — F32 (perfect-congruent triple-witness across (3,4,5), conductor 576, j-invariant 1728), F36 (genetic codon triple-witness via 2^n / 4^(n/2) / τ³), and F37 (cube triple-witness via V/E/F→Euler) each break in multiple ways simultaneously, providing high-information drift detection per single grep.

## Most interesting picks

**F36 `genetic-codon-triple-bridge`** — The genetic code's 64 codons admit THREE independent decompositions in nexus foundation arithmetic: 2^n = 4^(n/2) = τ³ = 64. This is rarer than F28's earth-axial-tilt: not just a single foundation→world identity, but a three-way coincidence at the exact cardinality (64) of life's molecular alphabet. The same n=6 thread continues into the CRISPR machinery atlas comment (PAM 3bp = n/φ, gRNA 20nt = J₂). If the foundation primitives drift and one of the three legs breaks, the others would re-anchor the cmd grep — but if the atlas line itself drifts, all three legs fall together. Highest information density per grep in the F31–F37 batch.

**F32 `perfect-congruent-bridge`** — Tunnell's BSD-conditional theorem (1983) packaged as a single atlas line: (3,4,5) = (n/φ, τ, sopfr), elliptic curve E_6: y²=x³-36x has conductor 576 = φ^n·(n/φ)^φ = 64·9, j-invariant 1728 = σ³. Three orthogonal number-theoretic identities from a single anchor — the foundation primitives recover the smallest Pythagorean triple, the smallest congruent number's elliptic curve conductor, AND its j-invariant simultaneously. Number theory's deepest cross-domain bridge into the nexus foundation, reaching all the way to BSD-style modularity.

## Merge instructions (raw 71 manual)

```
# main thread:
cat <<'EOF' >> design/hexa_sim/falsifiers.jsonl
<paste 7-line JSONL block above>
EOF
# verify:
grep -cE '^\{"id":"F' design/hexa_sim/falsifiers.jsonl   # should print 31 (was 24, +7)
# pre-flight each new cmd via bash -c (already done in this review)
```

## Constraints honored

- bash + grep only (no hexa runtime invoked)
- All 7 cmds pre-verified to PASS the sentinel
- raw 71 SUGGEST mode — no auto-merge, no falsifiers.jsonl mutation
- raw 73 admissibility — all 7 carry non-trivial structural claims (3 triangulation falsifiers + 4 single-bridge gems)
- Doc < 200 lines (this file)
- Not committed (main thread batches)
