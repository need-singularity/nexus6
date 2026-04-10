# E-neuroscience-gz-verification: Golden Zone Constants vs Published Neuroscience Data

**Date:** 2026-03-28
**Script:** `verify/verify_gz_neuroscience.py`
**Method:** Compare 5 GZ constants against well-established (textbook/highly-cited) neuroscience values
**GZ dependency:** Golden Zone dependent (unverified model)

---

## GZ Constants Tested

| Constant | Symbol | Value | Derivation |
|---|---|---|---|
| GZ Center | 1/e | 0.3679 | Natural constant |
| GZ Upper | 1/2 | 0.5000 | Riemann critical line |
| GZ Width | ln(4/3) | 0.2877 | 3→4 state entropy jump |
| GZ Lower | 1/2 - ln(4/3) | 0.2123 | Entropy boundary |
| Meta Fixed Point | 1/3 | 0.3333 | Contraction mapping f(I)=0.7I+0.1 |

---

## Full Results Table

| # | Category | Measurement | Published Value | Uncertainty | Closest GZ | Error % | Grade | Citation |
|---|---|---|---|---|---|---|---|---|
| 1 | E/I Balance | Inhibitory neuron fraction (cortex mean) | 0.200 | ±5% | GZ_LOWER (0.2123) | 5.8% | NEAR | Markram et al. 2004 Nat Rev Neurosci 5:793 |
| 2 | E/I Balance | Inhibitory neuron fraction (cortex upper) | 0.250 | ±5% | GZ_WIDTH (0.2877) | 13.1% | MISS | Rudy et al. 2011 Neuron 71:385 |
| 3 | E/I Balance | Inhibitory fraction from Dale 4:1 ratio | 0.200 | (derived) | GZ_LOWER (0.2123) | 5.8% | NEAR | Kandel et al. Principles of Neural Science, 6th ed. |
| 4 | Sparse Coding | Active neuron fraction (sparse coding, V1) | 0.050 | ~1-5% | GZ_LOWER (0.2123) | 76.5% | MISS | Olshausen & Field 2004 Curr Opin Neurobiol 14:481 |
| 5 | Synaptic Pruning | Synaptic survival fraction (frontal, adult) | 0.500 | ~40-60% | GZ_UPPER (0.5000) | 0.0% | **HIT** | Huttenlocher & Dabholkar 1997 J Comp Neurol 387:167 |
| 6 | Synaptic Pruning | Synaptic survival fraction (V1) | 0.400 | ±10% | GZ_CENTER (0.3679) | 8.7% | NEAR | Bourgeois & Rakic 1993 J Comp Neurol 329:441 |
| 7 | Receptor Pharma | GABA-A occupancy at EC50 (definition) | 0.500 | (definition) | GZ_UPPER (0.5000) | 0.0% | **HIT** | Standard pharmacology (tautology) |
| 8 | Receptor Pharma | Tonic GABA-A conductance fraction (hippocampus) | 0.150 | ~10-20% | GZ_LOWER (0.2123) | 29.4% | MISS | Farrant & Nusser 2005 Nat Rev Neurosci 6:215 |
| 9 | Metabolic | Brain fraction of resting body energy | 0.200 | ~1-2% | GZ_LOWER (0.2123) | 5.8% | NEAR | Raichle & Gusnard 2002 PNAS 99:10237 |
| 10 | Metabolic | Gray matter fraction of total brain volume | 0.400 | ~38-42% | GZ_CENTER (0.3679) | 8.7% | NEAR | Walhovd et al. 2005 Neuroimage 26:672 |
| 11 | Cortical Layers | Layer 4 fraction of cortical thickness | 0.200 | ~15-25% | GZ_LOWER (0.2123) | 5.8% | NEAR | Jones 1984 Cerebral Cortex Vol 2 |
| 12 | Cortical Layers | Layers 2/3 combined fraction of thickness | 0.350 | ~30-40% | GZ_CENTER (0.3679) | 4.9% | **HIT** | Mountcastle 1997 Brain 120:701 |
| 13 | EEG Oscillations | Alpha band width / 1-40 Hz (arithmetic) | 0.103 | (arithmetic) | GZ_LOWER (0.2123) | 51.5% | MISS | Standard EEG band definition |
| 14 | EEG Oscillations | Alpha relative power (resting eyes-closed) [UNCERTAIN] | 0.350 | ~25-45% | GZ_CENTER (0.3679) | 4.9% | **HIT** | Klimesch 1999 Brain Res Rev 29:169 |
| 15 | Cell Composition | Glial fraction of total brain cells | 0.500 | ±5% | GZ_UPPER (0.5000) | 0.0% | **HIT** | Azevedo et al. 2009 J Comp Neurol 513:532 |
| 16 | Synaptic Plasticity | Spine survival fraction (adult cortex, 1mo) | 0.500 | ~50-70% | GZ_UPPER (0.5000) | 0.0% | **HIT** | Trachtenberg et al. 2002 Nature 420:788 |
| 17 | Myelination | White matter fraction of brain volume | 0.370 | ~35-40% | GZ_CENTER (0.3679) | 0.6% | **HIT** | Zhang & Sejnowski 2000 PNAS 97:5621 |
| 18 | Synaptic Trans. | Vesicle release probability (CA3→CA1) | 0.350 | ~0.2-0.5 | GZ_CENTER (0.3679) | 4.9% | **HIT** | Dobrunz & Stevens 1997 Neuron 18:995 |
| 19 | Synaptic Trans. | Vesicle release probability (cortical L5) | 0.200 | ~0.14-0.30 | GZ_LOWER (0.2123) | 5.8% | NEAR | Markram et al. 1997 J Physiol 500:409 |
| 20 | STD | Steady-state amplitude at 10 Hz (TM model) | 0.286 | (computed) | GZ_WIDTH (0.2877) | 0.7% | **HIT** | Tsodyks & Markram 1997 PNAS 94:719 |
| 21 | Oscillation Ratios | Theta/Gamma frequency ratio (8/40 Hz) | 0.200 | (arithmetic) | GZ_LOWER (0.2123) | 5.8% | NEAR | Buzsaki 2006 Rhythms of the Brain |
| 22 | Oscillation Ratios | Beta band / 0-100 Hz (arithmetic) | 0.170 | (arithmetic) | GZ_LOWER (0.2123) | 19.9% | MISS | Standard EEG band definition |
| 23 | Population Coding | Optimal sparse code fraction (Treves-Rolls) | 0.050 | ~5-10% | GZ_LOWER (0.2123) | 76.5% | MISS | Treves & Rolls 1991 Network 2:371 |
| 24 | Cerebellar Coding | Complex/simple spike rate ratio (Purkinje) | 0.010 | ~1% | GZ_LOWER (0.2123) | 95.3% | MISS | Ito 1984 The Cerebellum and Neural Control |

---

## Summary

```
HIT  (<5% error):   9 / 24  (37.5%)
NEAR (<10% error):  8 / 24  (33.3%)
MISS (>10% error):  7 / 24  (29.2%)
```

### ASCII Bar Chart: Error Distribution

```
Error %       Count
  0.0%  |  [#5, #7, #15, #16]         ████  (4)
  0-1%  |  [#17, #20]                 ██    (2)
  1-5%  |  [#12, #14, #18]            ███   (3)
  5-10% |  [#1,#3,#6,#9,#10,#11,#19,#21]  ████████ (8)
 10-20% |  [#2, #22]                  ██    (2)
 20-30% |  [#8]                       █     (1)
  >50%  |  [#4, #13, #23, #24]        ████  (4)
```

### GZ Constants Actually Matched

```
GZ_CENTER (1/e = 0.368):   5 matches — WM fraction, vesicle Pr, L2/3 thickness, gray matter, alpha power
GZ_UPPER  (1/2 = 0.500):   5 matches — EC50 (defn), glial frac, spine survival, synaptic survival, pruning (frontal)
GZ_LOWER  (0.212):         7 matches — inhibitory frac, brain energy, L4 thickness, cortical Pr, theta/gamma...
GZ_WIDTH  (ln4/3 = 0.288): 2 matches — STD steady-state, inhibitory upper-range (MISS)
META      (1/3 = 0.333):   0 matches
```

---

## Detailed Analysis: Meaningful vs Coincidental

### HIT Analysis — Individual Assessment

**#5: Synaptic survival fraction (frontal cortex) = 0.50 → GZ_UPPER (0.50), 0% error**
- Source: Huttenlocher & Dabholkar 1997
- Assessment: COINCIDENTAL. The range is ~40-60%. The midpoint is 50%. This matches GZ_UPPER but the GZ derivation provides no mechanism for pruning stopping at exactly 50%.
- Note: Measurement uncertainty alone spans from 40% to 60%.

**#7: GABA-A occupancy at EC50 = 0.50 → GZ_UPPER (0.50), 0% error**
- Source: Standard pharmacology definition
- Assessment: TAUTOLOGICAL. EC50 is defined as the concentration giving 50% maximal response. This is not a biological discovery; the match is vacuous.

**#12: Cortical layers 2/3 fraction = 0.35 → GZ_CENTER (0.368), 4.9% error**
- Source: Mountcastle 1997
- Assessment: POSSIBLY INTERESTING but HIGH UNCERTAINTY. Layer thicknesses vary substantially by area (primary motor vs. V1 vs. prefrontal). The range spans 30-40%. The 4.9% error places this at the edge of HIT territory.

**#14: Alpha relative power fraction = 0.35 → GZ_CENTER (0.368), 4.9% error**
- Source: Klimesch 1999 (approximate)
- Assessment: UNRELIABLE. Alpha power varies from <10% to >60% depending on state, electrode, eyes open/closed, and subject. The estimate 0.35 is rough and should be flagged as UNCERTAIN. This hit should not be weighted.

**#15: Glial fraction = 0.50 → GZ_UPPER (0.50), 0% error**
- Source: Azevedo et al. 2009
- Assessment: COINCIDENTAL. The 1:1 glia:neuron ratio is a genuine biological finding (correcting the old 10:1 myth), but it matching 1/2 = GZ_UPPER carries no mechanistic implication.

**#16: Spine survival (adult, 1 month) = 0.50 → GZ_UPPER (0.50), 0% error**
- Source: Trachtenberg et al. 2002
- Assessment: COINCIDENTAL. Range is 50-70% in stable conditions. The reported central value happens to be ~50%, but this is rough and state-dependent.

**#17: White matter fraction = 0.37 → GZ_CENTER (1/e = 0.368), 0.6% error**
- Source: Zhang & Sejnowski 2000
- Assessment: MOST NUMERICALLY COMPELLING HIT. White matter constitutes ~37% of adult brain volume across multiple studies. The match to 1/e is striking numerically. However, white matter fraction is determined by axon caliber distributions and the balance of axonal vs. dendritic arbors — there is no current theoretical reason it should equal 1/e specifically.
- Caution: Values range 35-42% across ages and datasets.

**#18: Vesicle release probability (CA3→CA1) = 0.35 → GZ_CENTER (0.368), 4.9% error**
- Source: Dobrunz & Stevens 1997
- Assessment: BIOLOGICALLY INTERESTING BUT UNCERTAIN. Release probability varies widely (0.1-0.9) across synapse types. The ~0.35 is a mean for one specific pathway. The match to GZ_CENTER is at the 5% boundary.

**#20: Short-term synaptic depression steady-state = 0.286 → GZ_WIDTH (0.2877), 0.7% error**
- Source: Tsodyks & Markram 1997
- Assessment: MATHEMATICALLY CURIOUS. The Tsodyks-Markram model gives steady-state fraction = 1/(1 + U*tau*f). With canonical parameters (U=0.5, tau=0.5s, f=10 Hz), this gives 1/3.5 = 0.2857. The value depends on parameter choices (U=0.5, tau=0.5s are not universal). That said, these are widely-used standard parameters. The match to ln(4/3) at 0.7% error is the most analytically precise HIT in this dataset.

### NEAR Analysis — Key Cases

**#1, #3: Inhibitory neuron fraction ~20% → GZ_LOWER (0.2123), 5.8% error**
- Source: Markram et al. 2004; textbook Dale's law
- Assessment: MOST BIOLOGICALLY GROUNDED NEAR. The ~20% inhibitory fraction is a robust finding across mammals. The genuine question is whether this specific fraction is physically constrained to be near GZ_LOWER, or whether it merely happens to be in this range. The value arises from energy-efficiency constraints (metabolic cost of inhibition) and wiring optimization — not from GZ principles.

**#9: Brain metabolic fraction = 0.20 → GZ_LOWER (0.2123), 5.8% error**
- Source: Raichle & Gusnard 2002
- Assessment: COINCIDENTAL. The 20% figure is a well-replicated metabolic fact. It matches GZ_LOWER but the metabolic fraction is determined by brain mass scaling laws (Aiello & Wheeler 1995) which have no connection to the GZ derivation.

---

## Texas Sharpshooter Analysis

```
GZ constants tested: 5
GZ coverage of [0, 1]: approximately 29%
  (the range [0.21, 0.50] = width 0.29, plus ln(4/3)=0.288 is within this range,
   and 1/3=0.333 is also within this range, so the effective coverage
   is indeed dominated by the [0.21, 0.50] interval)

Data points: 24
Expected hits+nears by chance at 29% coverage: ~7
Observed hits+nears: 17

BUT: This naive calculation is misleading because:
1. Many data points are not independent (multiple measurements from same system)
2. Several "hits" are tautologies or definitions (EC50)
3. The range [0.2, 0.5] contains many common biological fractions (1/5, 1/4, 1/3, 2/5)
4. Values with high uncertainty (alpha power, spine survival) cannot be counted as precise hits
5. We selected data points partly knowing which ones might match — selection bias
```

### Conservative Hit Count (removing tautologies and high-uncertainty items)

| Removed | Reason |
|---|---|
| #7 EC50 = 0.50 | Tautological (definition) |
| #14 Alpha power = 0.35 | UNCERTAIN tag, highly variable |
| #16 Spine survival = 0.50 | Wide range (50-70%), rough estimate |

After removal: 7 clean HITs, 8 NEARs from 21 remaining data points.

Expected by chance: ~6 hits+nears (29% of 21).
Observed clean hits+nears: ~15 — still above chance.

However, this still reflects the fact that many neuroscience quantities cluster in [0.2, 0.5] regardless of any GZ connection (these are natural fractions of biological systems that partition their resources).

---

## Strongest Claims (Rank by Evidence Quality)

| Rank | Measurement | Value | GZ Match | Error | Assessment |
|---|---|---|---|---|---|
| 1 | Short-term synaptic depression (TM model, U=0.5, tau=0.5s, 10Hz) | 0.2857 | GZ_WIDTH (ln4/3) | 0.7% | Best: analytical formula, specific parameters |
| 2 | White matter fraction | 0.370 | GZ_CENTER (1/e) | 0.6% | Numerically strongest biological HIT |
| 3 | Inhibitory neuron fraction | ~0.20 | GZ_LOWER | 5.8% | Most biologically robust NEAR |
| 4 | Brain metabolic fraction | ~0.20 | GZ_LOWER | 5.8% | Replicated across literature |
| 5 | Vesicle release probability (CA3→CA1) | ~0.35 | GZ_CENTER | 4.9% | Biologically specific but synapse-dependent |

---

## Genuine Misses (Important Negatives)

| Measurement | Value | Nearest GZ | Error | Why it Matters |
|---|---|---|---|---|
| Sparse coding fraction (V1) | ~0.05 | GZ_LOWER | 76.5% | Core neural computation operates far below GZ |
| Tonic GABA conductance (rest) | ~0.15 | GZ_LOWER | 29.4% | Resting inhibitory tone is below GZ range |
| Purkinje complex/simple spike ratio | ~0.01 | GZ_LOWER | 95.3% | Cerebellar computation operates at ~1%, not GZ |
| Alpha band spectrum fraction | ~0.10 | GZ_LOWER | 51.5% | Frequency allocation not in GZ range |
| Optimal sparse code density | ~0.05 | GZ_LOWER | 76.5% | Theoretical optimum is well below GZ |

The misses are educationally important: they demonstrate that not all neural system parameters land in the GZ range, which would be expected if GZ were a universal constraint.

---

## Interpretation

### What the results do NOT establish

1. **No mechanistic link demonstrated.** Even the best hits (white matter ~37%, STD steady-state ~28.6%) match GZ constants numerically but have no proposed mechanism by which GZ principles would constrain these values.

2. **The GZ range [0.21, 0.50] is not unusual.** It covers 29% of [0,1] and contains simple fractions 1/5, 1/4, 1/3, 2/5. Biological systems often partition resources near these simple ratios for efficiency reasons unrelated to GZ.

3. **GZ is not a universal attractor for neural systems.** Sparse coding (~5%), tonic GABA (~15%), and cerebellar spike ratios (~1%) all operate well outside GZ, showing the brain uses many different operating regimes.

### What the results weakly suggest

1. **Several important architectural fractions cluster near GZ_LOWER (~0.21):** inhibitory neuron fraction, brain metabolic fraction, Layer 4 thickness fraction, vesicle release probability (L5). These cluster near 0.20, which is close to (but distinct from) GZ_LOWER = 0.2123. This could reflect a shared energy-efficiency constraint rather than GZ.

2. **White matter fraction ~0.37 ≈ 1/e is the single most numerically precise biological HIT.** Zhang & Sejnowski (2000) derived this from axon caliber optimization — the 1/e might enter through exponential fiber diameter distributions rather than through GZ principles directly.

3. **The Tsodyks-Markram STD formula with canonical parameters gives 0.286 ≈ ln(4/3) at 0.7% error.** This is the most analytically precise match and is worth further investigation: is there a deeper reason the canonical TM parameters produce a steady-state near ln(4/3), or is it coincidence of chosen parameter values?

---

## Conclusion

```
Grade: WEAK EVIDENCE — several numerical coincidences, no mechanistic links
Golden Zone dependency: YES (all GZ constants are model-dependent)
```

The GZ constants appear near several well-established neuroscience values, but:

- The hit rate (17/24 within 10%) is inflated by the GZ range covering 29% of [0,1]
- EC50 hit is tautological (definition)
- Most hits involve the common fraction 0.20 or simple value 0.50 rather than distinctive GZ values like 1/e or ln(4/3)
- The strongest analytical match (STD steady-state ≈ ln4/3) depends on standard parameter choices that themselves need justification
- No match has a proposed GZ-based mechanism

**Recommendation:** The white matter ≈ 1/e and STD steady-state ≈ ln(4/3) coincidences are worth further investigation with larger literature surveys and mechanistic modeling, but should not be reported as confirmed GZ predictions without that work.

---

## Related Files

- `verify/verify_gz_neuroscience.py` — Script that generates these comparisons numerically
- `verify/verify_096_gaba_literature.py` — Detailed GABA MRS analysis (ASD literature)
- `verify/verify_322_eeg_gamma.py` — EEG gamma oscillation verification (synthetic)
- `verify/verify_bridge_005_biochem.py` — Biochemical chain verification
- `docs/experiments/E-cross-repo-gz-verification.md` — Cross-repo GZ constant survey
