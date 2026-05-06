# calc/hbio_verify/

hexa-bio 4-verb (WEAVE/NANOBOT/RIBOZYME/VIROCAPSID) deterministic verification — nexus check pattern.

## 자매 verifier (nexus calc/)

- `alm_verify/`     — LLM corpus 검증 (21 entries)
- `clm_verify/`     — Φ-monotonicity (13 entries)
- `hsscb_verify/`   — hexa-sscb mk1 device-level (10 entries)
- `anima_verify/`   — anima philosophy + consciousness (9 entries)
- `hbio_verify/`    — hexa-bio 4-verb molecular (11 entries) ← NEW
- `auto_stubs/`     — n=6 lattice formula stubs (140 entries)

## circular-trap-free contract

| Component | Source |
|---|---|
| target | atlas anchor (HBIO-*) or manifest target field |
| formula | atlas anchor (n6-master-identity / Bayes / Hill / Eigen-Hammes) |
| input | atlas HBIO-* anchors (axis-M unit=/anchor=/cite=) + hexa-bio _python_bridge/module/ |

P1/P2/P3 (hive/spec/no_self_referential_verification) + LLM-judge-prohibited (hive/spec/no_llm_judge_in_deterministic_verification) 준수.

## 11 verifiers (G_VALIDITY)

| id | hyp summary | atlas anchor |
|---|---|---|
| hbio_weave_T1_vertex_count | sigma(6)=12 cage vertex | HBIO-weave-T1-vertex-count |
| hbio_weave_posterior_threshold | Bayesian posterior >= 0.95 | HBIO-weave-posterior-runtime |
| hbio_nanobot_work_per_cycle_floor | work >= 10 kT Brownian floor | HBIO-nanobot-work-per-cycle-kT |
| hbio_nanobot_J2_speedup | J2=24 pose speedup >= 10x | HBIO-nanobot-J2-speedup |
| hbio_nanobot_corpus_log_bf_n60 | log10_BF >= 3.0 Jeffreys decisive | HBIO-nanobot-corpus-log-bf-n60 |
| hbio_nanobot_collision_overlap | Jaccard < 0.5 sister-axis non-collision | HBIO-nanobot-collision-overlap |
| hbio_ribozyme_catalytic_core_nt | active site nt = sigma(6)=12 | HBIO-ribozyme-catalytic-core-nt |
| hbio_ribozyme_diffusion_margin | margin >= 1 order vs Eigen-Hammes 1e9 | HBIO-ribozyme-margin-orders |
| hbio_ribozyme_corpus_log_bf_n30 | log10_BF >= 5.0 ceiling decisive | HBIO-ribozyme-corpus-log-bf-n30 |
| hbio_c2_matrix_pass | 16/16 cell PASS (in-silico) | HBIO-c2-matrix-pass |
| hbio_lean4_sorry_count | 4 modules zero sorry | HBIO-lean4-sorry-count |

각 entry 5+ falsifier (raw#10 honest C3 정합).

## raw#91 HONEST C3 — IN-SILICO ONLY

C2 matrix 16/16 PASS = simulator+metadata internal-consistency only. **NOT** therapeutic / clinical / regulatory / immunogenic / pharmacokinetic / efficacy progress. C3+ (wet-lab → IND → phase I) explicitly out-of-repo per cross-cutting Require (R6).

## drift markers / open items

- F-NB-2-c [10*FAIL] honest-negative — corpus IS source-class biased (pre_2000 textbook log_bf=+2.65 vs post_2000 experimental -0.99)
- F-TP5-c/d PENDING (deadline 2026-07-28)
- F-NB-4-cuboctahedron PENDING (deadline 2026-07-28, GATE-26-1)
- F-VIROCAPSID-2-LIVE-PDB PENDING (long-horizon 2027-04-28)
- F-CL-FORMAL-2/3/4 PLACEHOLDER PROVEN (real-semantics cycle 30+)

## 운용

stub 자동 생성: `hexa run calc/hbio_verify/generator.hexa --emit` (deferred — alm/anima 패턴 차용 가능)

aggregate 실행: `hexa run calc/hbio_verify/run_all.hexa` (deferred 또는 hexa-sscb 의 atlas_anchors.py 패턴 차용)

nexus check 통합: `nexus check --bio` (기존 wrapper_landed) 또는 `nexus check` 전수 → check_bio.hexa 가 hbio_verify run_all 호출 (Stage C 강화).
