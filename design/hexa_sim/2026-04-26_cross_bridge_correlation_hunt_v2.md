# Cross-Bridge Correlation Hunt v2 — 2026-04-26 (rigorous redo)

**Decision: DECLINE.** No candidate survives both the empirical-resampling look-elsewhere correction AND the per-pair mechanism-plausibility check. Side-finding (raw 71): F10 (codata · cmb at "3.5/3.6%") is also weakened — it collapses under consistent rel-to-anchor framing, exactly as the F45 decline doc predicted. F10 stays grandfathered because it pre-dates v2 rigor, but it is no longer claimed as a strong cross-bridge witness.

Origin: Ω-cycle re-hunt requested after F45 decline (`design/hexa_sim/2026-04-26_F45_decision.md`). v2 corrects the three v1 failures: (a) framing inconsistency, (b) wrong baseline (uniform on [0, 0.5] instead of empirical-distribution-aware), (c) atomic-shell post-hoc anchor exemption.

---

## A. Pre-registered methodology (declared BEFORE results)

1. **Unit convention** (single, no mixing):
   `gap = |V − A| / max(|A|, 1)`
   where `V` = bridge-emitted dimensionless or scaled value and `A` = nearest small-integer anchor in `{0, 1, …, 100}`. All gap_pp values use this and only this normalization.

2. **Search space**: 16 healthy bridges in `tool/*_bridge.hexa`. From each, extract canonical/measured dimensionless values from hardcoded fallback constants (`FB_*`, `FALLBACK_*`, `REF_*`). Inclusion rule: anchor must be naturally unambiguous (CODATA α⁻¹→137; n_s→1; H_ion_eV→14). EXCLUDE post-hoc anchor choices (e.g. NANOGrav HD-σ=3.5 with anchor "3 or 4 by literature band"; IceCube Glashow 6.3 PeV with HEXA-SIM-chosen n=6 anchor).

3. **Match criterion**: cross-domain pair within `0.5pp` (Δ ≤ 0.005 abs).

4. **Look-elsewhere correction**: Monte Carlo by **resampling the empirical gap distribution** with replacement (50,000 trials), preserving the domain-assignment vector. Baseline = MC mean. PROMOTE only if observed ≥ 5× expected (Z ≥ 5 for normal-approx) AND a plausible physical mechanism exists.

5. **Domain partition**: `atomic` / `atomic-shell` (separate; per F45 decline §B atomic-shell-regularity argument) / `cosmology` / `chemistry` / `gravitational` / `astronomy`. Same-domain matches do NOT count (F45 decline §B-atomic-shell).

6. **F10 grandfather**: F10 (codata α-gap · cmb n_s-gap) pre-dates this rigor pass. Audit it under v2 framing as a side-finding only.

---

## B. Number table (28 metrics, 6 domains)

Single rule applied: `gap_pp = 100 · |V−A| / max(|A|,1)`.

| bridge | metric | value | anchor | gap_pp | domain |
|---|---|---|---|---|---|
| cmb_planck | Omega_sum | 1.000 | 1 | 0.0000 | cosmology |
| gaia | Proxima_plx_mas | 768.07 | 768 | 0.0091 | astronomy |
| codata | alpha_inverse | 137.0360 | 137 | 0.0263 | atomic |
| gaia | Sirius_plx_mas | 379.21 | 379 | 0.0554 | astronomy |
| pubchem | water_MW | 18.015 | 18 | 0.0833 | chemistry |
| pubchem | graphene_C_AMU | 12.011 | 12 | 0.0917 | chemistry |
| pubchem | benzene_MW_per_C | 13.019 | 13 | 0.1462 | chemistry |
| gaia | Vega_plx_mas | 130.23 | 130 | 0.1769 | astronomy |
| pubchem | methane_MW | 16.043 | 16 | 0.2687 | chemistry |
| simbad | Sirius_RA_deg | 101.287 | 101 | 0.2844 | astronomy |
| nist_atomic | Hartree_eV | 27.2114 | 27 | 0.7829 | atomic |
| gaia | Betelgeuse_plx_mas | 5.95 | 6 | 0.8333 | astronomy |
| gw_observatory | GW150914_m1_Msun | 35.6 | 36 | 1.1111 | gravitational |
| gw_observatory | GW150914_m2_Msun | 30.6 | 31 | 1.2903 | gravitational |
| nist_atomic | He_ion_eV | 24.587 | 25 | 1.6520 | atomic-shell |
| horizons | g_std_ms2 | 9.81 | 10 | 1.9000 | gravitational |
| nist_atomic | C_ion_eV | 11.260 | 11 | 2.3636 | atomic-shell |
| pubchem | hexane_MW_per_C | 14.363 | 14 | 2.5929 | chemistry |
| nist_atomic | H_ion_eV | 13.598 | 14 | 2.8714 | atomic-shell |
| cmb_planck | n_s | 0.965 | 1 | 3.5000 | cosmology |
| nist_atomic | Be_ion_eV | 9.323 | 9 | 3.5889 | atomic-shell |
| nist_atomic | B_ion_eV | 8.298 | 8 | 3.7250 | atomic-shell |
| gaia | Polaris_plx_mas | 7.54 | 8 | 5.7500 | astronomy |
| nist_atomic | Li_ion_eV | 5.392 | 5 | 7.8400 | atomic-shell |
| nanograv | gamma_SMBHB | 4.3333 | 4 | 8.3333 | gravitational |
| cmb_planck | sigma_8 | 0.811 | 1 | 18.9000 | cosmology |
| cmb_planck | Omega_L | 0.685 | 1 | 31.5000 | cosmology |
| cmb_planck | Omega_m | 0.315 | 0 | 31.5000 | cosmology |

**Excluded** (and why): NANOGrav HD-σ (anchor band-uncertain), IceCube Glashow 6.3 PeV (HEXA-SIM-chosen n=6 anchor — design contamination per v1 caveat 2), pulsar count 68 / fermion count 12 / perfect numbers 6,28 (exact integers, no gap), GW150914 z=0.09 (anchor=0 is just the redshift), protein lengths (exact integer counts), TP-8 4.0 days (HEXA-SIM design constant), CMB first_peak_l=220 (exact int), age_Gyr=13.797 (post-hoc anchor 14 vs 13).

---

## C. Pairwise & triplet match counts

Cross-domain pair matches at Δ ≤ 0.5pp: **observed = 46**. Cross-domain triplets: **observed = 41**. Top 5 pairs by tightness (full list in execution log):

| Δpp | left | right | judgement |
|---|---|---|---|
| 0.0091 | cmb_planck.Omega_sum=0.0000 | gaia.Proxima_plx_mas=0.0091 | REJECT (Omega_sum=1 is definitional flat-universe constraint) |
| 0.0156 | pubchem.methane_MW=0.2687 | simbad.Sirius_RA_deg=0.2844 | REJECT (methane MW≈16 by AMU summation; Sirius RA is observational geometry — coincidence) |
| 0.0172 | codata.alpha_inverse=0.0263 | gaia.Proxima_plx_mas=0.0091 | REJECT (no physical mechanism — fine-structure decimal vs distant star parallax) |
| 0.0263 | codata.alpha_inverse=0.0263 | cmb_planck.Omega_sum=0.0000 | REJECT (Omega_sum definitional) |
| 0.0279 | pubchem.water_MW=0.0833 | gaia.Sirius_plx_mas=0.0554 | REJECT (AMU clusters near integer; Sirius parallax = geometry) |

The "best" candidates above all fail mechanism check.

---

## D. Look-elsewhere correction (Monte Carlo)

Method: 50,000 trials, each resampling 28 gaps i.i.d. from the empirical gap distribution (with replacement), preserving the domain-assignment vector. Count cross-domain pair / triplet matches at the same Δ ≤ 0.5pp threshold.

| statistic | observed | MC mean ± std | P(MC ≥ obs) | Z |
|---|---|---|---|---|
| Cross-domain pairs | **46** | **61.38 ± 16.82** | **0.8406** | **−0.91** |
| Cross-domain triplets | **41** | **99.08 ± 68.82** | **0.8416** | **−0.84** |

**Observed match counts are LOWER than the empirical-resampling mean.** The "matches" are not anomalous; they are *fewer* than chance once the genuinely right-skewed gap distribution is used as the baseline. The naive uniform baseline (used in v1) is wrong precisely because most measured constants live close to integer anchors, so a uniform [0, 31.5pp] reference overstates how anomalous a near-zero cluster is.

### F45-band test (gap ≈ 3.5pp, where v1 claimed the headline triplet):

In-band metrics ([3.4, 3.8]pp): cmb_planck.n_s (3.5000), nist_atomic.Be_ion_eV (3.5889), nist_atomic.B_ion_eV (3.7250).

- Observed cross-domain pairs in band: **2** (the cmb·Be and cmb·B pairs; Be·B is same-domain so excluded).
- MC expected band cross-domain pairs: **3.654**.
- P(MC band-pairs ≥ observed): **0.5826**.

The F45 cluster is *less concentrated* than chance — directly confirming the F45 decline doc's §B atomic-shell-regularity argument: Be (3.59) and B (3.73) are both first-row atomic ionizations near 3.5%, and cmb.n_s landing in the same band is statistically ordinary.

---

## E. Decision: DECLINE

Three independent reasons (any one would suffice):

1. **No candidate clears the mechanism filter.** Of 46 pair matches, the top 15 (Δ < 0.1pp) are all rejected as definitional (Omega_sum=1), AMU-clustering (atomic-mass-unit values are all integer-near by construction), or pure numerology (alpha-inverse vs distant-star parallax has no physical link).

2. **Look-elsewhere correction fails the >5× threshold.** Observed pair count (46) is BELOW MC mean (61). Z = −0.9. There is no excess to promote.

3. **F45 band-specific re-test fails too.** The 3.5pp band has 2 observed cross-domain pairs vs MC expectation 3.65; the cluster is less dense than random — confirming F45 decline.

---

## F. F10 grandfather audit (raw 71 — record, do not auto-retire)

Under v2's single-convention framing:
- codata.alpha_inverse gap (rel-to-137): **0.0263pp**
- cmb_planck.n_s gap (rel-to-1): **3.5000pp**
- delta = **3.4737pp** — well outside the 0.5pp pair-match threshold.

F10 collapses under v2 framing. The original F10 claim relied on framing both as "absolute fractional residuals" (codata 0.036 abs, cmb 0.035 abs), which works only if the codata denominator silently switches from 137 to 1. The F45 decline doc §A flagged this as Caveat #4 ("F10 framing fragility"); v2 confirms.

**Recommendation**: F10 stays grandfathered (raw 71 — no auto-retire), but should be annotated in any future hunt doc as "single-pair, framing-fragile" rather than "strong cross-bridge anchor." A future formal F10 falsifier (none currently in `falsifiers.jsonl`) would need to disclose the convention swap as part of the claim.

---

## G. What would unlock a future PROMOTE

A hypothetical F95-revival would need ALL of:

1. **Two values from genuinely independent domains** with a tight gap match (Δ < 0.1pp) AND a stated **physical mechanism** (not merely "both happen to be near integer N"). E.g. a relationship predicted by a theory that touches both domains (running coupling unification, anthropic constraint, etc.).
2. **The mechanism must predate the observation** OR be derivable from established physics — post-hoc fits don't qualify (raw 73).
3. **The match must survive the empirical-resampling baseline at p < 0.01** (Z ≥ 2.5 over MC mean) — not just the naive uniform baseline.
4. **A third independent domain witness** to clear triplet-grade significance (current MC-resampled triplet baseline mean is ~99; a triplet would need to be *tighter* than 0.05pp and have all three mechanisms tied together).

Until all four are present, no cross-bridge correlation in the current 16-bridge pool deserves promotion. The bridges are doing their job (each independently anchored to its primary source); they are not predisposed to numerical resonance with each other beyond chance.

---

## H. Falsifier registry (raw 71 — JSONL ready, do NOT merge here)

No JSONL entry produced — F95 reservation released. If main thread wants a permanent **negative-result witness** (analogous to F45 decline being preserved), append:

```json
{"id":"F95","slug":"cross-bridge-correlation-v2-decline","claim":"v2 cross-bridge hunt found NO promotable correlation: 28 dimensionless gaps across 6 domains, observed 46 cross-domain pair matches at 0.5pp threshold vs MC-empirical-resampling mean 61.4 (Z=-0.91, p=0.84) — i.e. fewer matches than chance. F10 grandfathered but framing-fragile under consistent rel-to-anchor convention","cmd":"test -f /Users/ghost/core/nexus/design/hexa_sim/2026-04-26_cross_bridge_correlation_hunt_v2.md && grep -q 'Decision: DECLINE' /Users/ghost/core/nexus/design/hexa_sim/2026-04-26_cross_bridge_correlation_hunt_v2.md && echo CROSS_BRIDGE_V2_DECLINE_RECORDED","pass":"CROSS_BRIDGE_V2_DECLINE_RECORDED","reason":"v2 decline doc deleted/edited — historical negative-result evidence destroyed, look-elsewhere methodology lost (raw 73 admissibility violation: failed promotions are first-class evidence)","fix":"restore doc from git history (find via `git log --diff-filter=D -- design/hexa_sim/2026-04-26_cross_bridge_correlation_hunt_v2.md`); if intentional retire, append rationale to F45 decision doc and supersede F95 with the new analysis","origin":"design/hexa_sim/2026-04-26_cross_bridge_correlation_hunt_v2.md — Ω-cycle 2026-04-26 cross-bridge re-hunt, MC empirical-resampling baseline (50000 trials), 6-domain partition"}
```

(F95 was reserved by partition for this agent. Up to main thread whether to merge — the doc itself is the primary deliverable; the JSONL is a curator aid.)

---

## I. Replication (raw 73 admissibility)

Re-derive `gap_pp` table from `tool/*_bridge.hexa` fallback constants:

```
codata_bridge.hexa:29     FALLBACK_ALPHA_SCALED=137035999177  → α⁻¹=137.035999177, gap=(0.036/137)·100=0.0263pp
cmb_planck_bridge.hexa:49 FB_NS=965000000                     → n_s=0.965, gap=(0.035/1)·100=3.5000pp
nist_atomic_bridge.hexa:64-66 FIRST_6_IONIZATION_MEV[]        → meV/1000 → eV → gap to nearest int
pubchem_bridge.hexa:45    REF_MW_MILLI=[18015,16043,78114,180156,86178,12011] → /1000 → MW → gap
gaia_bridge.hexa:18-22    parallax mas comments               → gap to nearest int
... (full set in §B)
```

MC code: `/tmp/cross_bridge_v2_baseline.py` (seed 20260426, 50000 trials). Re-run for bit-identical p-values.

---

## Provenance & cross-refs

- v1 doc (retracted-headline): `design/hexa_sim/2026-04-26_cross_bridge_correlation_hunt.md`
- F45 decline (predecessor): `design/hexa_sim/2026-04-26_F45_decision.md`
- Bridges read (read-only): all 16 in `tool/*_bridge.hexa` (ω-cycle session)
- Falsifier registry (not mutated this session): `design/hexa_sim/falsifiers.jsonl` (87 entries; F95 still available)
- ID partition: F88-F94 reserved by parallel agents; F95 reserved for this agent (released — no PROMOTE).

Decision recorded: 2026-04-26.
