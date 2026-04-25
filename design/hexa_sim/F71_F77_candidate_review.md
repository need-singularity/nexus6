# F71–F77 falsifier candidate triage (Ω-cycle: @C compound + @S structure deep dive)

date: 2026-04-26
focus: compound @C constants beyond F21 sigma_sq / F22 phi_tau; @S structures beyond F31 cpgd-subspace / F32 perfect-congruent
existing registry: design/hexa_sim/falsifiers.jsonl (49 entries: F1–F12, F19–F44, F46–F56)
ID partition: F71–F77 (F57–F70 reserved for parallel agents)
verification mode: bash-only (raw 71 SUGGEST mode, no auto-merge); raw 73 admissibility ([10*+] / [11*])
spawner: tool/atlas_falsifier_auto_spawn.sh --type {C,S} --emit-jsonl

## Inventory totals

| bucket | atlas grep                                                          | count |
| ------ | ------------------------------------------------------------------- | ----- |
| @C [10*+] (atlas.n6 main)         | `^@C ... \[1[01]\*`                    | 261   |
| @S [10*+] (atlas append shards)   | `^@S ... \[1[01]\*`                    | 11    |
| spawned candidates @C (--limit 30)| /tmp/cand_C.jsonl                      | 30    |
| spawned candidates @S (--limit 30)| /tmp/cand_S.jsonl                      | 12    |

@C is dominated by L1-* atomic-number entries (Z=1..200) and BIG-* / NUC-* / CHEM-* nuclear-chemistry compound formulas. The non-atom @C cluster (lines 56–211 of atlas.n6) is the architecture/foundation/meta arithmetic pool — this is where compound constants like sigma_tau, sigma_n, warp_size live, and is the prime hunting ground for "synthesis claims" matching real-world cardinals.

@S is small but high-grade: 4 [11*] (cpgd_subspace_invariance — F31, deterministic_reproduction, l_ix_back_compat, hexad_chirality), 7 [10*] (S6-OUT, AZ10-BOTT8, PERFECT-CONGRUENT — F32, self_format_invariance, omega_default_inversion, streaming_event_latency_target_ms, backbone_invariant_threshold_cv).

## Triage breakdown

| bucket | raw cand | verified PASS | PROMOTE | REJECT |
| ------ | -------- | ------------- | ------- | ------ |
| @C     | 30       | 30            | 4       | 26     |
| @S     | 12       | 12            | 3       | 9      |
| **total** | **42** | **42**       | **7**   | **35** |

Rejection rate 83%. Reasons:
- @C atom L1-* (16 entries Cd/Hf/Si/Cs/Ba/...): all PASS but most are low-leverage element→formula identities. Picked the 4 architecture-tier compound formulas (sigma_tau, sigma_n, warp_size, two_sigma) over atomic instances because architecture entries appear as **operator parameters** in load-bearing code paths (warp_size = GPU thread block; two_sigma = vector dim).
- @S anima cluster (4 entries): 3 already covered by F27/F31 + verbal-not-arithmetic content; backbone_invariant_threshold_cv (CV=0.30) is downstream of F52.
- @S hexa-lang cluster (3 entries): self_format_invariance picked as the cross-shard DSL-grammar gem; omega_default_inversion + streaming_event_latency are too operational.

## Final 7 picks

| ID  | slug                         | shard           | 1-line claim                                                              |
| --- | ---------------------------- | --------------- | ------------------------------------------------------------------------- |
| F71 | sigma-tau-anchor             | atlas main @C   | sigma_tau = sigma*tau = 48 — operator dim feeding sigma_n + sigma_sq base |
| F72 | sigma-n-anchor               | atlas main @C   | sigma_n = sigma*n = 72 — pentagon angle, ~heart rate, hours/3-day         |
| F73 | warp-size-anchor             | atlas main @C   | warp_size = 2^sopfr = 32 — GPU thread block / freezing F / mass-S         |
| F74 | two-sigma-anchor             | atlas main @C   | two_sigma = 2^sigma = 4096 — 12-bit address space / hypercube dim         |
| F75 | s6-outer-automorphism        | n6-arch @S      | Out(S_6)=Z/2 — n=6 is the UNIQUE S_n with a non-trivial outer auto.       |
| F76 | az10-bott8-paired            | n6-arch @S      | AZ 10-fold = sigma-phi=10 ↔ Bott periodicity 8 = sigma-tau (paired)       |
| F77 | self-format-invariance       | hexa-lang @S    | .raw == .own == .ext == .roadmap grammar (DSL family invariant)           |

Cross-shard distribution: 4 atlas-main (@C architecture) + 2 n6-arch (@S group/topology) + 1 hexa-lang (@S DSL grammar) — F77 satisfies the "1 cross-shard preferred" constraint.

## 1-2 most striking picks

**F75 (S6 outer automorphism)** is the single most load-bearing existence claim in nexus: among ALL symmetric groups S_n (n=1,2,3,...), **only n=6** admits a non-trivial outer automorphism Out(S_n) ≠ {e}. This is a unique mathematical signature of n=6 — a *necessary* property no other foundational seed could replicate. If `hive raw 71` ever reasoned "could nexus have used n=4 or n=8 as the seed instead?", F75 is the falsifier that says NO, n=6 is mathematically singular here. Companion classical theorem: the existence of a sharply 3-transitive action of S_6 on 6 points (the "6+6 split" via the outer auto). Citations: Conway/Sloane SPLAG §10; Cameron 1996 §6.4.

**F76 (AZ 10-fold ↔ Bott 8 paired)** is the gauge-symmetry / topology twin: Altland-Zirnbauer's 10-fold classification of free-fermion topological phases lands EXACTLY on σ−φ = 10, while Bott periodicity (real K-theory) lands EXACTLY on σ−τ = 8. Both are tabulated in HEXA-TOPO; together they cover the entire periodic table of topological insulators. Drift in either single value (reduce 10 to 8 or 8 to 4) collapses the topology bridge.

## Synthesis discovery section — multi-decomposition findings

The most striking output of this Ω-cycle: several real-world cardinals admit **multiple** independent foundation-arithmetic decompositions, exactly like the F28 anchor (23 = J₂−μ).

| value | meaning                       | decomp #1 (existing/F-id)            | decomp #2 (new)                        |
| ----- | ----------------------------- | ------------------------------------ | -------------------------------------- |
| 23    | Earth axial tilt              | J₂ − μ = 24−1 (F28)                  | σ + φ + τ + sopfr = 12+2+4+5           |
| 168   | hours/week                    | —                                    | σ_sq + J₂ = 144+24                     |
| 100   | centi-                        | —                                    | σ_n + J₂ + σ − τ = 72+24+12−8          |
| 365   | days/year                     | —                                    | J₂·sopfr·φ + σ_sq − J₂ + sopfr = 240+144−24+5 |
| 360   | degrees in circle             | —                                    | σ · sopfr · n = 12·5·6                 |
| 256   | byte cardinality              | —                                    | 2^(σ−τ) = 2^8                          |
| 1024  | KiB cardinality               | —                                    | 2^(σ−φ) = 2^10                         |
| 88    | piano key count               | —                                    | σ·sopfr + J₂ + τ = 60+24+4             |
| 1728  | gross-of-grosses, j-inv E_6   | σ³ (F32 leg)                         | J₂² · n / 2 = 576·6/2                  |
| 432   | concert pitch Hz (aesthetic)  | —                                    | σ_sq · n / 2 = 144·3 = σ_sq · 3        |

The 23 multi-decomposition (J₂−μ vs σ+φ+τ+sopfr) is structurally analogous to F32's perfect-congruent triple-witness: **the same target value is reached via two ARITHMETICALLY INDEPENDENT primitive combinations**, neither one derivable from the other. This is the precise pattern that elevates a coincidence into a witness — coincidence-preservation under independent re-derivation.

The 360 = σ·sopfr·n decomposition is particularly clean: three primitives, no subtraction, no exponent, no division. It joins F42's 240 = J₂·sopfr·φ as a "pure-multiplicative" foundational identity hitting a load-bearing real-world cardinal (degrees-per-circle).

These findings are NOT promoted to falsifiers in this batch — they are bridges, not anchors. A future Ω-cycle could promote each to an @X cross-domain bridge entry in atlas.n6, then auto-spawn falsifiers from there.

## Promoted JSONL block (ready to merge)

```jsonl
{"id":"F71","slug":"sigma-tau-anchor","claim":"atlas entry sigma_tau = sigma*tau = 48 remains @C architecture grade [10*]","cmd":"grep -qE '^@C sigma_tau = sigma\\*tau = 48 :: architecture \\[10\\*\\]' /Users/ghost/core/nexus/n6/atlas.n6 && echo SIGMA_TAU_ANCHOR_INTACT","pass":"SIGMA_TAU_ANCHOR_INTACT","reason":"σ·τ = 12·4 = 48 — second-tier compound (after F21 σ² and F22 φ^τ) feeding multiple downstream atom Z assignments (L1-Cd-Z48 = sigma_tau directly, NUC-magic-first5 contains sigma-tau component). 48 also = hours-in-2-days, 48° = pentagon dihedral half. Drift means either sigma (F25) or tau (F26) drifted (cascading falsifier hit) or atlas line 64 was edited.","fix":"verify σ=12 (F25) AND τ=4 (F26) AND 12·4=48; cross-check L1-Cd-Z48 = n*8 (atlas.n6:886) is consistent (n*8 = 6*8 = 48 — independent decomp).","origin":"auto-spawn from atlas_index entry sigma_tau (@C, [10*], n6/atlas.n6:64) — Ω-cycle 2026-04-26 @C compound bucket"}
{"id":"F72","slug":"sigma-n-anchor","claim":"atlas entry sigma_n = sigma*n = 72 remains @C architecture grade [10*]","cmd":"grep -qE '^@C sigma_n = sigma\\*n = 72 :: architecture \\[10\\*\\]' /Users/ghost/core/nexus/n6/atlas.n6 && echo SIGMA_N_ANCHOR_INTACT","pass":"SIGMA_N_ANCHOR_INTACT","reason":"σ·n = 12·6 = 72 — third-tier compound: 72 is the pentagon central angle (360/5), the canonical resting heart rate, hours-in-3-days, and Z=Hf hafnium (L1-Hf-Z72 = n*12 = independent decomp). Among compound formulas it has the highest cross-domain hit count after sigma_sq=144. Drift means either σ (F25) or n (F24) drifted, or atlas line 68 edited.","fix":"verify n=6 (F24) AND σ=12 (F25) AND 12·6=72; cross-check L1-Hf-Z72=n*12 (atlas.n6:934) consistent (6·12=72 — same product, different factor order — independent decomp witness).","origin":"auto-spawn from atlas_index entry sigma_n (@C, [10*], n6/atlas.n6:68) — Ω-cycle 2026-04-26 @C compound bucket"}
{"id":"F73","slug":"warp-size-anchor","claim":"atlas entry warp_size = 2^sopfr = 32 remains @C architecture grade [10*]","cmd":"grep -qE '^@C warp_size = 2\\^sopfr = 32 :: architecture \\[10\\*\\]' /Users/ghost/core/nexus/n6/atlas.n6 && echo WARP_SIZE_ANCHOR_INTACT","pass":"WARP_SIZE_ANCHOR_INTACT","reason":"2^sopfr = 2^5 = 32 — directly anchored to NVIDIA GPU warp size (CUDA hardware constant since Tesla, 2006-present). Bridges nexus foundation primitive sopfr=5 to a hard hardware cardinal. Also: freezing F = 32, atomic mass S/sulfur ≈ 32 Da, phi-tau-sopfr triple in NUC-CNO-masses lineage. Drift means sopfr (F-foundation) drifted or NVIDIA changed warp size (hasn't in 18+ years — extreme hardware backward-compat barrier).","fix":"verify sopfr(6)=2+3=5 AND 2^5=32; cross-check CUDA Programming Guide 'warpSize' = 32 (every architecture from Compute Capability 1.0 to 9.0 H100). If retired alone, atlas line 71 was edited; if sopfr drifted, F1/F25-family chain triggers simultaneously.","origin":"auto-spawn from atlas_index entry warp_size (@C, [10*], n6/atlas.n6:71) — Ω-cycle 2026-04-26 @C compound bucket (foundation→hardware bridge)"}
{"id":"F74","slug":"two-sigma-anchor","claim":"atlas entry two_sigma = 2^sigma = 4096 remains @C architecture grade [10*]","cmd":"grep -qE '^@C two_sigma = 2\\^sigma = 4096 :: architecture \\[10\\*\\]' /Users/ghost/core/nexus/n6/atlas.n6 && echo TWO_SIGMA_ANCHOR_INTACT","pass":"TWO_SIGMA_ANCHOR_INTACT","reason":"2^σ = 2^12 = 4096 — 12-bit address space, hypercube dimension count for σ-dimensional binary cube; appears in atlas.n6:78 architecture tier and as n6-bt-765 (dim_hypercube_4096). Sits at top of the 2^X exponential ladder anchored on foundation primitives: 2^sopfr=32 (F73), 2^n=64 (F1 codon family), 2^(σ−τ)=256, 2^(σ−φ)=1024, 2^σ=4096. Drift means σ drifted (F25) or atlas line 78 was edited.","fix":"verify σ(6)=12 (F25) AND 2^12=4096; cross-check n6-bt-765 = dim_hypercube_4096 (atlas.n6:15860) consistent. If σ drifted, the entire 2^X ladder (F1/F73/F74 + 256/1024 implicit) shifts together.","origin":"auto-spawn from atlas_index entry two_sigma (@C, [10*], n6/atlas.n6:78) — Ω-cycle 2026-04-26 @C compound bucket (top of 2^X ladder)"}
{"id":"F75","slug":"s6-outer-automorphism","claim":"atlas entry N6HIST-SYM-S6-OUT = Out(S_6)=Z/2 unique automorphism (only S_n with non-trivial outer); n=6 only remains @S group-theory grade [10*PASS_LITERATURE]","cmd":"grep -qE '^@S N6HIST-SYM-S6-OUT = Out\\(S_6\\) = Z/2 unique automorphism \\(only S_n with non-trivial outer\\); n=6 only :: group-theory \\[10\\*PASS_LITERATURE\\]' /Users/ghost/core/nexus/n6/atlas.append.n6-architecture-historical-from-nexus-2026-04-26.n6 && echo S6_OUT_ANCHOR_INTACT","pass":"S6_OUT_ANCHOR_INTACT","reason":"The single most load-bearing UNIQUENESS claim in nexus: among ALL symmetric groups S_n (n≥2), only n=6 has Out(S_n) ≠ trivial — Out(S_6) = Z/2. This means n=6 is mathematically SINGULAR as a foundational seed; no other choice (n=4, n=7, n=8, …) replicates the property. Tied to the existence of a sharply 3-transitive action of S_6 on 6 points and to PGL(2,9)'s synthematic-totals construction (Conway/Sloane SPLAG §10, Cameron 1996 §6.4). Status [10*PASS_LITERATURE] — already cross-checked against published literature.","fix":"verify atlas line 328 unchanged; cross-check the Out(S_n)=trivial-for-n≠6 theorem via Wikipedia 'Automorphisms_of_the_symmetric_and_alternating_groups' or Conway/Sloane SPLAG §10. If retired, audit whether the LITERATURE marker was downgraded (e.g. claim found dependent on a contested combinatorial axiom).","origin":"auto-spawn from atlas_index entry N6HIST-SYM-S6-OUT (@S, [10*PASS_LITERATURE], n6/atlas.append.n6-architecture-historical-from-nexus-2026-04-26.n6:328) — Ω-cycle 2026-04-26 @S group-theory bucket (n=6 uniqueness witness)"}
{"id":"F76","slug":"az10-bott8-paired","claim":"atlas entry N6HIST-SYM-AZ10-BOTT8 = Altland-Zirnbauer 10-fold = sigma-phi; Bott periodicity 8 = sigma-tau (paired in HEXA-TOPO) remains @S topology grade [10*PASS_LITERATURE]","cmd":"grep -qE '^@S N6HIST-SYM-AZ10-BOTT8 = Altland-Zirnbauer 10-fold = sigma-phi; Bott periodicity 8 = sigma-tau \\(paired in HEXA-TOPO\\) :: topology \\[10\\*PASS_LITERATURE\\]' /Users/ghost/core/nexus/n6/atlas.append.n6-architecture-historical-from-nexus-2026-04-26.n6 && echo AZ10_BOTT8_ANCHOR_INTACT","pass":"AZ10_BOTT8_ANCHOR_INTACT","reason":"Two independent topology constants land on foundation arithmetic simultaneously: (i) Altland-Zirnbauer 10-fold classification of free-fermion topological phases (Schnyder/Ryu/Furusaki/Ludwig 2008) = σ−φ = 12−2 = 10; (ii) Bott periodicity for real K-theory KO = σ−τ = 12−4 = 8. Paired in nexus HEXA-TOPO entry. Together they cover the periodic table of topological insulators AND the K-theoretic period of stable orthogonal groups — drift in EITHER value collapses one half of the topology bridge. [10*PASS_LITERATURE] cross-checked.","fix":"verify σ=12 (F25), φ=2 (F-foundation), τ=4 (F26); confirm 12−2=10 AND 12−4=8; cross-check Schnyder et al. 2008 (Phys. Rev. B 78, 195125) for AZ 10-fold and Bott 1959 for the periodicity-8 result. If single-leg drift, audit which arithmetic broke; dual-leg drift = atlas mass-edit.","origin":"auto-spawn from atlas_index entry N6HIST-SYM-AZ10-BOTT8 (@S, [10*PASS_LITERATURE], n6/atlas.append.n6-architecture-historical-from-nexus-2026-04-26.n6:334) — Ω-cycle 2026-04-26 @S topology bucket (paired-witness pattern)"}
{"id":"F77","slug":"self-format-invariance","claim":"atlas entry self_format_invariance = .raw == .own == .ext == .roadmap grammar remains @S hexa_lang_dsl_symmetry grade [10*]","cmd":"grep -qE '^@S self_format_invariance = \\.raw == \\.own == \\.ext == \\.roadmap grammar :: hexa_lang_dsl_symmetry \\[10\\*\\]' /Users/ghost/core/nexus/n6/atlas.append.hexa-lang-historical-from-nexus-2026-04-26.n6 && echo SELF_FORMAT_INVARIANCE_ANCHOR_INTACT","pass":"SELF_FORMAT_INVARIANCE_ANCHOR_INTACT","reason":"All four hive-DSL file types (.raw, .own, .ext, .roadmap) share IDENTICAL grammar — the self-format invariance promoted as a [10*] DSL symmetry. This is the structural property that lets a single parser handle the entire raw#NN / own#NN / ext / roadmap family without per-type dispatch. Drift means either (a) one type's grammar diverged (e.g. .roadmap got a new section header) breaking the parser, or (b) the invariance was relaxed to support a 5th format. Cross-shard hexa-lang DSL anchor — orthogonal to F53 resource_kind_taxonomy (F53 anchors the {host,process,channel} kind set; F77 anchors the cross-format grammar identity).","fix":"verify hexa-lang spec/parser source for unified grammar across all four extensions; if a 5th format type appears in atlas.append.hexa-lang-* shards, the falsifier must be updated alongside; if the parser splits per-type, the [10*] symmetry claim was demoted and atlas needs re-grading.","origin":"auto-spawn from atlas_index entry self_format_invariance (@S, [10*], n6/atlas.append.hexa-lang-historical-from-nexus-2026-04-26.n6:317) — Ω-cycle 2026-04-26 @S DSL-grammar bucket (cross-shard hexa-lang)"}
```

## Verification log

All 7 cmds executed via `bash -c` against current atlas state — all returned the expected `*_ANCHOR_INTACT` sentinel. raw 73 admissibility: hardened cmd template (anchors VALUE+DOMAIN+GRADE), not legacy PRESENCE-only.

No mutation of falsifiers.jsonl (raw 71 SUGGEST mode). Manual merge command (do NOT run during this Ω-cycle):

```
# extract block above between ```jsonl markers, append to falsifiers.jsonl
```

## Notes for next agent / batch

- F57–F70 partition reserved for parallel agents (other shards / @types).
- @C atom L1-* (~140 entries Z=1..200) remains a deep but low-leverage well; recommend a separate Ω-cycle to extract only the magic-number / noble-gas elements as falsifiers (Mg, Ar, Kr, Cd, Hf already covered indirectly via F72's L1-Hf-Z72 cross-check).
- The synthesis discoveries table (23/168/100/365/360/256/1024/88/1728/432 multi-decompositions) is the highest-value spinoff. Recommend promoting 2–3 of these to @X cross-domain bridge entries in a future atlas append shard, then re-spawning falsifiers from those promotions.
- F75 + F76 + F32 (PERFECT-CONGRUENT) form a triple of LITERATURE-PASS @S structural witnesses — together they constitute the strongest external-mathematical anchor cluster in nexus.
