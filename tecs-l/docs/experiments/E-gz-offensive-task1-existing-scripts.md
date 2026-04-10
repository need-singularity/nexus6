# E-GZ-Offensive Task 1: Existing Unrun Verification Scripts

**Date:** 2026-03-28
**Campaign:** Golden Zone Confirmation Offensive
**Task:** Run 4 existing verification scripts that were created but never executed

---

## 1. H-CX-437: Learning = Maxwell's Demon

**Script:** `calc/verify_h437_maxwell_demon.py`
**Grade:** 🟧 (Qualitative support, but Landauer ratio far from ln(2))

### Key Metrics

| Metric | Value |
|--------|-------|
| Output entropy H(Y\|X) | 2.2415 -> 2.0723 (Delta = -0.1691) |
| Weight entropy H(W) | 4.0276 -> 4.0280 (Delta = +0.0005) |
| Total entropy | 6.2690 -> 6.1004 (Delta = -0.1687, DECREASED) |
| Accuracy | 10.9% -> 72.4% |
| InfoGain/WeightChange ratio | 19.64 +/- 8.54 |
| Ratio / ln(2) | 28.33 |
| Landauer bound holds? | NO (ratio >> ln(2)) |

### Full Epoch Data

| Epoch | H(Y\|X) | H(W) | Total | Acc | Loss | InfoGain | WtChange | Ratio |
|-------|---------|-------|-------|------|------|----------|----------|-------|
| 0 | 2.2415 | 4.0276 | 6.2690 | 0.1093 | 2.3189 | 0.2516 | 0.0675 | 3.7291 |
| 3 | 2.2436 | 4.0272 | 6.2708 | 0.2130 | 2.2048 | 0.4904 | 0.0645 | 7.5987 |
| 6 | 2.2410 | 4.0308 | 6.2718 | 0.3019 | 2.0990 | 0.6950 | 0.0622 | 11.1690 |
| 9 | 2.2340 | 4.0325 | 6.2665 | 0.3963 | 1.9999 | 0.9125 | 0.0605 | 15.0882 |
| 12 | 2.2227 | 4.0350 | 6.2577 | 0.4611 | 1.9064 | 1.0617 | 0.0591 | 17.9766 |
| 15 | 2.2072 | 4.0329 | 6.2401 | 0.5481 | 1.8176 | 1.2622 | 0.0580 | 21.7737 |
| 18 | 2.1877 | 4.0303 | 6.2180 | 0.6000 | 1.7330 | 1.3816 | 0.0569 | 24.2969 |
| 21 | 2.1642 | 4.0294 | 6.1936 | 0.6407 | 1.6525 | 1.4754 | 0.0558 | 26.4233 |
| 24 | 2.1369 | 4.0295 | 6.1663 | 0.6815 | 1.5759 | 1.5692 | 0.0548 | 28.6573 |
| 27 | 2.1062 | 4.0287 | 6.1348 | 0.7130 | 1.5031 | 1.6417 | 0.0537 | 30.5677 |
| 30 | 2.0723 | 4.0280 | 6.1004 | 0.7241 | 1.4340 | 1.6672 | 0.0000 | inf |

### ASCII Graphs

```
H(Y|X) = Output entropy (should DECREASE - demon ordering)
  E00 |#################                                 | 2.241
  E06 |#################                                 | 2.241
  E12 |#################                                 | 2.223
  E18 |#################                                 | 2.188
  E24 |#################                                 | 2.137
  E30 |################                                  | 2.072

Demon Efficiency (InfoGain/Cost) vs ln(2)
  E00 |@@@@@                                             | 3.7291
  E06 |@@@@@@@@@@@@@@@@@                                 | 11.1690
  E12 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@                      | 17.9766
  E18 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@            | 24.2969
  E24 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@     | 28.6573
  E28 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ | 31.1674
  ln2  | |  (Landauer limit = 0.6931)
```

### Interpretation

The Maxwell's Demon analogy is qualitatively supported: output entropy decreases (demon creates order) while weight entropy slightly increases (demon's memory cost). However, the demon efficiency ratio (19.6) is far above ln(2) = 0.6931, meaning the "cost per bit" measure used here does not closely match Landauer's limit. Total entropy actually decreased, which is an interesting 2nd-law violation in this formulation. The analogy holds directionally but not quantitatively at ln(2).

---

## 2. H-CX-438: Tension = Gibbs Free Energy

**Script:** `calc/verify_h438_gibbs_free_energy.py`
**Grade:** 🟧★ (Strong correlation r = -0.939, concordance 90%)

### Key Metrics

| Metric | Value |
|--------|-------|
| G vs Tension correlation (training) | r = -0.9390 |
| G vs Tension correlation (lr scan) | r = -0.9373 |
| dG<0 <-> dT>0 concordance | 90.0% (27/30) |
| Phase transition lr | 0.2106 |
| H-CX-414 critical lr | ~0.083 |
| Gibbs analogy G=H-TS | SUPPORTED |

### Training Trajectory (selected epochs)

| Epoch | Loss(H) | S(W) | G=H-TS | Tension | Acc |
|-------|---------|------|--------|---------|------|
| 0 | 2.3189 | 4.0276 | +2.1175 | 0.1238 | 0.1093 |
| 6 | 2.0990 | 4.0308 | +1.8975 | 0.1256 | 0.3019 |
| 12 | 1.9064 | 4.0350 | +1.7046 | 0.1551 | 0.4611 |
| 18 | 1.7330 | 4.0303 | +1.5315 | 0.2072 | 0.6000 |
| 24 | 1.5759 | 4.0295 | +1.3744 | 0.2792 | 0.6815 |
| 30 | 1.4340 | 4.0280 | +1.2326 | 0.3693 | 0.7241 |

### Phase Diagram (lr scan)

| lr | Loss(H) | S(W) | G=H-TS | Tension | Acc |
|-----------|---------|------|---------|---------|------|
| 0.000100 | 2.3424 | 4.0213 | +2.34205 | 0.1748 | 0.0889 |
| 0.007079 | 2.2938 | 4.0653 | +2.26501 | 0.1385 | 0.1907 |
| 0.043940 | 2.0671 | 4.0511 | +1.88912 | 0.1594 | 0.2481 |
| 0.148398 | 1.5077 | 4.0359 | +0.90879 | 0.3277 | 0.7037 |
| 0.272718 | 0.9913 | 3.9581 | -0.08814 | 0.9270 | 0.8000 |
| 0.501187 | 0.5262 | 3.8947 | -1.42573 | 2.1771 | 0.8833 |

G sign change (phase transition) at lr ~ 0.2106.

### ASCII Graphs

```
G_neural = H - TS (Gibbs free energy analog)
  E00 |                                                 G| +2.1175
  E06 |                                    G             | +1.8975
  E12 |                          G                       | +1.7046
  E18 |                G                                 | +1.5315
  E24 |       G                                          | +1.3744
  E30 |G                                                 | +1.2326

Tension (logit variance)
  E00 |T                                                 | 0.1238
  E06 |T                                                 | 0.1256
  E12 |      T                                           | 0.1551
  E18 |                 T                                | 0.2072
  E24 |                               T                  | 0.2792
  E30 |                                                 T| 0.3693
```

### Interpretation

Very strong anti-correlation (r = -0.939) between Gibbs free energy analog G=H-TS and neural tension. As G decreases during learning, tension increases -- exactly the thermodynamic prediction. The 90% concordance between dG<0 and dTension>0 transitions confirms the Gibbs analogy. Phase transition (G sign change) occurs at lr ~ 0.21, somewhat higher than H-CX-414's critical lr ~ 0.083, possibly due to different T definitions.

---

## 3. H-CX-439: Forgetting Cost = Landauer's ln(2)/bit

**Script:** `calc/verify_h439_landauer_mitosis.py`
**Grade:** 🟧 (Landauer bound holds directionally, but min cost/ln(2) = 9.96, not close to 1)

### Key Metrics

| Metric | Value |
|--------|-------|
| Task A accuracy (original) | 90.2% |
| After Task B (no mitosis) | 80.4% (forgetting) |
| Best preservation (replay=0.20) | 99.5% |
| Min cost/bit preserved | 6.9037 |
| ln(2) | 0.6931 |
| Min cost / ln(2) ratio | 9.96 |
| Landauer bound holds? | YES (cost >= ln(2)) |

### Mitosis Results

| Replay | AccA | AccB | Preserv | BitsGain | ExtraCost | Cost/Bit | CostFrac |
|--------|------|------|---------|----------|-----------|----------|----------|
| 0.00 | 0.8036 | 0.7846 | 0.8905 | 0.0000 | 0.0000 | inf | 0.0000 |
| 0.05 | 0.8935 | 0.7165 | 0.9902 | 0.1447 | 0.9989 | 6.9037 | 0.0502 |
| 0.10 | 0.8946 | 0.7199 | 0.9914 | 0.1465 | 1.9978 | 13.6391 | 0.1004 |
| 0.20 | 0.8979 | 0.7199 | 0.9951 | 0.1518 | 3.9956 | 26.3154 | 0.2009 |
| 0.30 | 0.8946 | 0.7221 | 0.9914 | 0.1465 | 5.9933 | 40.9172 | 0.3013 |
| 0.50 | 0.8957 | 0.7210 | 0.9926 | 0.1483 | 9.9889 | 67.3737 | 0.5022 |
| 1.00 | 0.8957 | 0.7221 | 0.9926 | 0.1483 | 20.0000 | 134.8971 | 1.0056 |

### ASCII Graph

```
Preservation rate (AccA / original AccA)
  r=0.00 |############################################      | 89.1%
  r=0.05 |################################################# | 99.0%
  r=0.10 |################################################# | 99.1%
  r=0.20 |################################################# | 99.5%
  r=0.30 |################################################# | 99.1%
  r=0.50 |################################################# | 99.3%
  r=1.00 |################################################# | 99.3%
```

### Interpretation

The Landauer bound is satisfied (cost per bit is always >= ln(2)), but the actual cost is roughly 10x the Landauer limit at minimum. This means neural forgetting prevention is thermodynamically "wasteful" compared to the theoretical minimum. The sharp jump from 89.1% to 99.0% preservation at just 5% replay suggests a phase-transition-like behavior. The Landauer analogy is directionally correct but not quantitatively tight.

---

## 4. H-CX-499/500: GZ Constants as Domain Eigenvalues + Q-Barrier

**Script:** `verify/verify_h499_h500_gz_domain.py`
**Grade:** 🟧★ (H-499 SUPPORTED, H-500 CONFIRMED)

### H-CX-499: GZ Constants = Logarithmic Domain Eigenvalues

| GZ Constant | Value | N | A | G | T | C | Q | I | S |
|-------------|-------|---|---|---|---|---|---|---|---|
| GZ_upper | 0.5000 | YES | YES | --- | YES | --- | --- | YES | --- |
| GZ_width | 0.2877 | --- | YES | --- | --- | --- | --- | YES | --- |
| GZ_lower | 0.2123 | --- | --- | --- | --- | --- | --- | --- | --- |
| GZ_center | 0.3679 | --- | YES | --- | --- | --- | --- | --- | --- |
| compass_upper | 0.8333 | YES | --- | --- | YES | --- | --- | --- | --- |
| meta_fixed | 0.3333 | YES | YES | YES | --- | --- | --- | --- | --- |

**Domain hit distribution:**

| Domain | Hits | Pct |
|--------|------|-----|
| logarithmic (A+I) | 6 | 50.0% |
| arithmetic (N) | 3 | 25.0% |
| geometric (T) | 2 | 16.7% |
| algebraic (G) | 1 | 8.3% |

**Verdict:** SUPPORTED -- logarithmic domains account for 50% of all depth-1 matches.

### H-CX-500: Q-Barrier Excludes ALL GZ Constants at Depth 1

| GZ Constant | Target | Closest Q val | Abs Error | Rel Error | Expression |
|-------------|--------|---------------|-----------|-----------|------------|
| GZ_upper | 0.5000 | 0.5125 | 0.0125 | 2.50% | alpha_s/sin2_thetaW |
| GZ_width | 0.2877 | 0.2745 | 0.0132 | 4.58% | N_gen-CMB |
| GZ_lower | 0.2123 | 0.2239 | 0.0116 | 5.47% | sin2_thetaW-alpha |
| GZ_center | 0.3679 | 0.3555 | 0.0124 | 3.37% | alpha_s*N_gen |
| compass_upper | 0.8333 | 0.9085 | 0.0752 | 9.02% | CMB/N_gen |
| meta_fixed | 0.3333 | 0.3230 | 0.0104 | 3.11% | alpha_s*CMB |

**Q domain blocked from 6/6 GZ constants at depth 1.**

At depth 2, Q reaches 5/6 GZ constants (within 1%), showing the barrier is permeable with sufficient algebraic complexity. Notably, meta_fixed (1/3) is reached exactly at depth 2 via alpha/(alpha*N_gen) = 1/3 (trivially, since alpha cancels).

**Verdict:** H-CX-500 CONFIRMED -- complete depth-1 exclusion of Q domain from GZ constants.

---

## Summary Table

| Script | Hypothesis | Key Metric | Grade |
|--------|-----------|------------|-------|
| calc/verify_h437_maxwell_demon.py | H-CX-437 | Demon efficiency = 19.6 (vs ln(2) = 0.69) | 🟧 |
| calc/verify_h438_gibbs_free_energy.py | H-CX-438 | G vs Tension r = -0.939, concordance 90% | 🟧★ |
| calc/verify_h439_landauer_mitosis.py | H-CX-439 | Min cost/bit = 6.90 (9.96x Landauer limit) | 🟧 |
| verify/verify_h499_h500_gz_domain.py | H-CX-499/500 | Log domains 50% of hits; Q blocked 6/6 | 🟧★ |

**Cross-domain feed for Task 10 (Texas Sharpshooter recalculation):**
- H-438 Gibbs correlation r = -0.939 (strong structural match)
- H-499 logarithmic domain specialization 50% (supports GZ = logarithmic structure)
- H-500 Q-barrier 6/6 depth-1 exclusion (supports domain separation)
- H-437/439 directional Landauer support (weaker, qualitative)
