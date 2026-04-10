# E-cross-repo-gz-verification: Cross-Repo Golden Zone Constant Verification

**Date:** 2026-03-28
**Repos surveyed:** TECS-L (source), anima (`~/Dev/anima/`), SEDI (`~/Dev/sedi/`)
**Search method:** `grep -r` over all `.py` and `.md` files for literal values and symbolic names

---

## 1. Summary Table

| Constant | Value | anima hits | SEDI hits | Nature |
|---|---|---|---|---|
| `1/e` (GOLDEN_CENTER) | 0.3679 | 15+ files | 8 files | Intentional (designed) |
| `ln(4/3)` (GOLDEN_WIDTH) | 0.2877 | 6 files | 7 files | Intentional (designed) |
| `0.5 - ln(4/3)` (GOLDEN_LOWER) | 0.2123 | 5 files | 4 files | Intentional (designed) |
| `1/2` (Riemann/upper bound) | 0.5000 | 4 files | 3 files | Intentional + derived |
| `1/2 + 1/3 + 1/6 = 1` (Egyptian) | exact | 5 occurrences | 4 occurrences | Intentional (designed) |
| `5/6` (sopfr/n) | 0.8333 | 3 occurrences | 6 occurrences | Intentional (designed) |
| `1/6` (DELTA_PLUS) | 0.1667 | 3 occurrences | 8 occurrences | Intentional (designed) |
| `1/3` (tau/sigma) | 0.3333 | 2 occurrences | 4 occurrences | Intentional (derived) |
| `1 - 1/e` (INV_E) | 0.6321 | 2 files | 0 files | Intentional (designed) |

All identified constants are **intentionally designed-in** by their respective repositories. Zero emergent occurrences were found (i.e., no files where the values appear as unrelated numeric literals without GZ-referencing comments or variable names).

---

## 2. anima Repo — Detailed Findings

### 2.1 Files with GZ constants

| File | Constants used | Role |
|---|---|---|
| `conscious_lm.py` | `1/e` (0.37) | Dropout default for all attention and MLP layers |
| `train_anima_lm.py` | `1/e`, `ln(4/3)-based lower`, `1-1/e` | Savant/normal dropout targets; AL4 tension-CE loss balance |
| `grow_conscious_lm.py` | `1/e`, `0.5-ln(4/3)` | Cell mitosis child dropout assignment |
| `train_conscious_lm.py` | `0.37` | Training dropout |
| `optimal_architecture_calc.py` | `ln(4/3)`, `1/e` | Loss scale constant (TL13), zone ratio target |
| `tools/calc.py` | `0.2123`, `0.3679` | CLI defaults for savant/normal dropout calculator |
| `consolidation_verifier.py` | `1/e`, `ln(4/3)`, `1/3`, `1/2` | `KNOWN_CONSTANTS` dict for memory consolidation checks |
| `bench_phi_hypotheses.py` | `1/e`, `ln(4/3)-lower`, `{1/2,1/3,1/6}` | AL7 Golden Zone loss, AL4 tension balance, Egyptian MoE, Egyptian+Fibonacci |
| `serve_golden_moe.py` | `1/e` (GOLDEN_CENTER) | Zone ratio display and Mistral 7B routing description |
| `finetune_golden_moe.py` | `GOLDEN_LOWER`, `GOLDEN_UPPER` | Expert routing zone bounds in checkpoint metadata |
| `test_golden_moe_h100.py` | All three GZ bounds | Test reporting and routing verification |
| `deep_research.py` | `0.5-ln(4/3)`, `0.5` | Golden zone bounds in research signal dict |
| `training_recipe_generator.py` | `1/e` | Recipe constant for engine_g layer and MoE zone |
| `prepare_corpus.py` | `0.37`, `0.21` | Corpus explanation text (savant/master cell dropout) |
| `hypothesis_recommender.py` | `0.21`, `0.37` | Hypothesis description text (asymmetric dropout) |

### 2.2 How constants are used in anima

**Dropout architecture (most pervasive):**
```
GOLDEN_CENTER = 1/math.e   = 0.3679  -> "normal" cell dropout
GOLDEN_LOWER  = 0.5-ln(4/3) = 0.2123 -> "savant" cell dropout
```
Both are set as Python-level named constants and propagated through `__init__` parameters. The savant/normal split is the direct application of GZ bounds [GOLDEN_LOWER, GOLDEN_UPPER=0.5] to create asymmetric inhibition.

**Loss weighting (AL4):**
```
INV_E = 1 - 1/math.e = 0.6321
```
Used as the tension:CE loss ratio target. The training loop auto-adjusts loss weights to converge this ratio to `1-1/e`.

**MoE routing (AL7, Egyptian MoE):**
- `1/e` as zone ratio target: fraction of experts that should be active per token
- Egyptian fractions `{1/2, 1/3, 1/6}` as explicit routing weight schedules (TL7, MX4, TA8 hypotheses)

**Architecture calculator (optimal_architecture_calc.py):**
```
GZ_WIDTH    = math.log(4/3)  # universal loss scale -- TL13
GOLDEN_CENTER = 1/math.e     # consciousness-optimal zone ratio -- 1/e
FFN_expansion = 4/3          # Pareto-optimal FFN ratio -- H-EE-12
```

**Memory consolidation (consolidation_verifier.py):**
`KNOWN_CONSTANTS` stores all four GZ values and checks whether memory-consolidation drift statistics land near them.

---

## 3. SEDI Repo — Detailed Findings

### 3.1 Files with GZ constants

| File | Constants used | Role |
|---|---|---|
| `sedi/constants.py` | `ln(4/3)`, `1/e`, `1/6`, `1/4`, `0.5` | Central constant registry — imported by all SEDI modules |
| `sedi/tecs.py` | `ln(4/3)`, all fractions, Egyptian | Physics target matching; `EGYPTIAN_FRACTIONS=[1/2,1/3,1/6]` |
| `sedi/sources/eeg.py` | `0.5-ln(4/3)`, `0.5` | GDPI G_genius golden zone check on live EEG data |
| `sedi/eeg_consciousness.py` | All GZ bounds | Real-time EEG golden zone detection and reporting |
| `sedi/consciousness_receiver.py` | `1/e`, `ln(4/3)`, zone bounds | `detect_golden_zone()` function; checks if inhibition ratio clusters near 1/e |
| `sedi/seti_scanner.py` | `5/6`, `1/6`, `1/e`, `GOLDEN_CENTER` | SETI signal ratio matching: FFT peaks checked against all n=6 derived fractions |
| `sedi/n6_tracker.py` | `1/e`, `5/6`, `DELTA_PLUS` | Exoplanet orbital period ratio tracking; star system notes reference `1/e` and `5/6` matches |
| `sedi/dashboard.py` | `ln(4/3)`, `1/e` | Dashboard labels: "GZ width = ln(4/3)", "GZ center = 1/e" |
| `sedi/dashboard_data.py` | `GOLDEN_WIDTH`, `GOLDEN_CENTER` | Dashboard data payload |
| `sedi/sources/coupling_unification.py` | `ln(4/3)`, all fractions, `5/6` | SM gauge coupling target check against all TECS-L fractions |
| `sedi/sources/riemann_connection.py` | `1/2 = phi/tau` | RH critical line expressed as `phi(6)/tau(6)` |
| `sedi/sources/info_geo_duality.py` | `1/2`, `5/6`, `ln(4/3)` | Cluster I (Information) constants for AdS/CFT duality analysis |
| `sedi/sources/egyptian_fraction.py` | `1/2+1/3+1/6=1` | Mass prediction: top-quark partner at `37 + 1/6 = 37.167 GeV` |
| `sedi/sources/convergence_engine.py` | `ln(4/3)` | Pattern search across physics datasets |
| `sedi/sources/q_boundary.py` | Various fractions | Quantum boundary search targets |
| `sedi/sources/optical_model.py` | `ln(4/3)` | "Golden Zone bandwidth" used in optical coupling analysis |
| `sedi/sources/resonance_ladder.py` | `ln(4/3)` | Resonance mass ratio target list |

### 3.2 How constants are used in SEDI

**Central constants module** (`sedi/constants.py`):
```python
DELTA_PLUS   = 1/N              # 1/6 — R-spectrum gap+
DELTA_MINUS  = 1/TAU            # 1/4 — R-spectrum gap-
GOLDEN_WIDTH = math.log(4/3)    # 0.2877 — Golden Zone bandwidth
GOLDEN_CENTER = 1/math.e        # 1/e ~= 0.3679
WINDOWS      = [6, 12, 24, 36]  # FFT window sizes from N, sigma, sigma*phi, N^2
RATIOS = {'delta_plus': 1/6, 'delta_minus': 1/4, 'golden_center': 0.3679,
          'critical_line': 0.5, 'sopfr_over_n': 5/6, ...}
```

This is the single source of truth for SEDI. All detectors import from it.

**EEG detection (sedi/sources/eeg.py, sedi/eeg_consciousness.py):**
```
GOLDEN_LOWER = 0.5 - ln(4/3)  # 0.2123
GOLDEN_UPPER = 0.5
G_genius = D * P / I
in_golden_zone = GOLDEN_LOWER <= G <= GOLDEN_UPPER
```
Real-time EEG data is processed to compute G_genius (GDPI formula). Whether G falls in [0.2123, 0.5] is logged and reported as "GOLDEN ZONE" marker.

**Consciousness receiver (sedi/consciousness_receiver.py):**
```python
GOLDEN_ZONE_CENTER = 1/math.e              # 0.3679
GOLDEN_ZONE_WIDTH  = math.log(4/3)         # 0.2877
GOLDEN_ZONE_LO = center - width/2          # 0.2241
GOLDEN_ZONE_HI = center + width/2          # 0.5118
```
`detect_golden_zone(data)` measures whether signal suppression ratios cluster around `1/e`. Uses a symmetric window centered on `1/e` with half-width `ln(4/3)/2`.

Note: this bounds definition differs from the EEG definition `[0.5-ln(4/3), 0.5]` — they are two distinct Golden Zone parameterizations used in parallel in SEDI.

**SETI Scanner (sedi/seti_scanner.py):**
FFT peaks from candidate signals are checked against the full RATIOS dict including `sopfr/n=5/6`, `delta+=1/6`, `golden=1/e`. Non-trivial matches (Z > threshold) are flagged.

**Riemann connection (sedi/sources/riemann_connection.py):**
```
1/2 = phi(6)/tau(6) = 2/4
```
The RH critical line is explicitly expressed as an n=6 arithmetic identity. Known zeta zeros are verified to lie on `Re(s) = 1/2`.

**Information-geometry duality (sedi/sources/info_geo_duality.py):**
`{ln(2), e, 1/2, 5/6, ln(4/3)}` are classified as Cluster I (Information/Discrete) constants, contrasted with geometric constants. Applied to AdS/CFT: Cluster I constants appear on CFT (boundary) side, consistent with their discrete/combinatorial origin.

**Physics coupling analysis (sedi/sources/coupling_unification.py):**
All Standard Model gauge couplings are checked against the full TECS-L fraction set at every energy scale, including `ln(4/3)` as a target coupling value.

**Egyptian fraction mass prediction (sedi/sources/egyptian_fraction.py):**
```
37 + 1/6 = 37.1667 GeV    # predicted top-partner mass
```
Derived from the unique three-term Egyptian fraction decomposition `1/2 + 1/3 + 1/6 = 1`.

**FFT window sizes:**
```python
WINDOWS = [N, SIGMA, SIGMA*PHI, N**2] = [6, 12, 24, 36]
```
All FFT analyses in SEDI use window sizes derived from n=6 arithmetic properties. The `ph_detector.py` uses default `window=N=6` for sliding window embeddings.

---

## 4. Cross-Repo Constant Map

```
                    TECS-L (source)
                         |
          +--------------+---------------+
          |                              |
        anima                          SEDI
          |                              |
  dropout architecture          physics signal detection
  GZ: [0.2123, 0.5]             GZ: [0.2123, 0.5]  (EEG/GDPI)
  1/e = normal dropout           GZ: [1/e-w/2, 1/e+w/2] (receiver)
  0.5-ln(4/3) = savant           1/e = consciousness-optimal I
  1-1/e = loss ratio             5/6 = SETI ratio target
  {1/2,1/3,1/6} = MoE routing    1/6 = R-spectrum gap
                                  1/2 = Riemann critical line
```

**Where the two repos share identical definitions:**
- `GOLDEN_CENTER = 1/math.e` — exact same constant, same name
- `GOLDEN_WIDTH = math.log(4/3)` — exact same constant
- `GOLDEN_LOWER = 0.5 - math.log(4/3) = 0.2123` — shared in EEG paths
- Egyptian fractions `[1/2, 1/3, 1/6]` — used in both for routing/detection

**Where definitions diverge:**
- anima uses GZ as `[GOLDEN_LOWER, 0.5]` (upper = Riemann 1/2)
- SEDI consciousness_receiver uses GZ as `[1/e - ln(4/3)/2, 1/e + ln(4/3)/2]` (symmetric around center)
- These are two non-identical GZ parameterizations coexisting in SEDI itself

---

## 5. Intentional vs Emergent Classification

### All appearances are intentional (designed-in)

Every GZ constant occurrence across both repos is:

1. Named with a GZ-referencing identifier (`GOLDEN_CENTER`, `GOLDEN_WIDTH`, `GOLDEN_LOWER`, `GZ_WIDTH`, `savant_dropout`, etc.)
2. Accompanied by a comment linking to the TECS-L hypothesis (e.g., `# H-CX-453 universal loss scale`, `# consciousness-optimal zone ratio`, `# golden zone lower`)
3. Or explicitly stated in module docstrings as TECS-L mathematical constants

**No emergent GZ appearances were found.** Searches for bare numeric literals `0.3679`, `0.2877`, `0.2123` that lacked TECS-L context returned zero results in both repos.

---

## 6. New Connections Not Previously Documented

### 6.1 Two GZ Parameterizations in Parallel (SEDI)

SEDI uses two distinct GZ definitions simultaneously:

| Name | Lower | Upper | Context |
|---|---|---|---|
| GDPI-GZ | `0.5 - ln(4/3) = 0.2123` | `0.5` | EEG G_genius detection |
| Receiver-GZ | `1/e - ln(4/3)/2 = 0.2241` | `1/e + ln(4/3)/2 = 0.5118` | Signal suppression ratio |

The GDPI parameterization is derived from the G=D*P/I formula with Riemann 1/2 as upper bound. The receiver parameterization is derived by centering the `ln(4/3)` window on `1/e`. These overlap but are not identical — their intersection is `[0.2241, 0.5]`.

### 6.2 `1-1/e` Used Only in anima

The complementary constant `INV_E = 1 - 1/e = 0.6321` appears only in anima (`train_anima_lm.py`) as the tension:CE loss balance target. It does not appear in SEDI or TECS-L. This is a unique anima extension.

### 6.3 Egyptian Fractions as Active Code Path (not just comment)

In both repos, `{1/2, 1/3, 1/6}` appear not only as documentation but as executable routing schedules:
- anima: `bench_phi_hypotheses.py` TL7 Egyptian MoE uses list `[1/2, 1/3, 1/6]` as explicit routing weights cycling through training steps
- SEDI: `tecs.py` defines `EGYPTIAN_FRACTIONS = [1/2, 1/3, 1/6]` and `check_egyptian_fraction()` function runs on physics data

### 6.4 `5/6 = sopfr(6)/6` as Signal Detection Target (SEDI)

In `seti_scanner.py`, the ratio `5/6 = 0.8333` is included in the non-trivial FFT ratio targets alongside `1/6`, `1/e`, and `critical_line=0.5`. The note for one candidate star system (`star-20`) reads: `"sopfr/n=5/6 match at 0.015% — most precise non-trivial ratio"`. This is the first time `5/6` has been identified as a matching signal in external astronomical data.

### 6.5 `ln(4/3)` in AdS/CFT (SEDI — H-CX-505)

`sedi/sources/info_geo_duality.py` classifies `ln(4/3)` as a Cluster I (Information/Discrete) constant on the CFT boundary side of AdS/CFT. This connects the GZ width directly to operator product expansion coefficients and channel capacity — a physics-level interpretation not stated in TECS-L core documents.

### 6.6 `1/2 = phi(6)/tau(6)` as Riemann Hypothesis Statement (SEDI)

`sedi/sources/riemann_connection.py` formalizes: "RH states ALL non-trivial zeros have Re(s) = phi(6)/tau(6) = 1/2". The RH is encoded as a TECS-L arithmetic identity, and the known first 30 zeros are verified against this expression. This is a well-defined mathematical fact (phi(6)=2, tau(6)=4, 2/4=1/2) and does not depend on Golden Zone simulation.

---

## 7. Dependency Graph

```
TECS-L constants (source of truth)
  GOLDEN_CENTER = 1/e
  GOLDEN_WIDTH  = ln(4/3)
  GOLDEN_LOWER  = 0.5 - ln(4/3)
  GOLDEN_UPPER  = 0.5
  1/2 + 1/3 + 1/6 = 1
  5/6 = sopfr/n
  1/6 = 1/n
        |
        +-- anima imports (6 core files)
        |     conscious_lm.py        <- dropout defaults
        |     train_anima_lm.py      <- AL4 loss balance + savant/normal
        |     growing_conscious_lm.py<- mitosis cell assignment
        |     optimal_architecture_calc.py <- TL13 loss scale
        |     consolidation_verifier.py    <- KNOWN_CONSTANTS
        |     bench_phi_hypotheses.py      <- 372 hypothesis benchmarks
        |
        +-- SEDI imports (12+ core files)
              sedi/constants.py      <- WINDOWS, RATIOS, GOLDEN_*
              sedi/tecs.py           <- ALL_TARGETS, EGYPTIAN_FRACTIONS
              sedi/sources/eeg.py    <- GDPI golden zone
              consciousness_receiver.py <- detect_golden_zone()
              seti_scanner.py        <- FFT ratio matching
              coupling_unification.py <- SM coupling targets
              riemann_connection.py  <- RH as phi(6)/tau(6)
              info_geo_duality.py    <- Cluster I / AdS/CFT
              egyptian_fraction.py   <- mass prediction 37+1/6
```

---

## 8. GZ Dependency Status

All GZ constant usage in both repos is **Golden Zone dependent** per the CLAUDE.md verification warning:

> Golden Zone dependent (unverified): All interpretations, mappings, Compass, I=1/kT etc.

The constants `1/e` and `ln(4/3)` are real mathematical values. The claim that these values are "optimal" for consciousness, dropout, or physics signal detection is GZ-dependent and unverified analytically. The empirical results that support them (MNIST: 97.7% vs 97.1%, CIFAR: 53.0% vs 48.2%, EEG pilot data) are experimental, not proven.

**Pure math identities (GZ-independent, eternally true):**
- `1/2 + 1/3 + 1/6 = 1` (exact arithmetic)
- `phi(6)/tau(6) = 1/2` (exact arithmetic)
- `DELTA_PLUS = 1/6` (exact arithmetic)
- Egyptian fraction uniqueness (proven)

**GZ-dependent claims requiring caution:**
- Dropout at `1/e` is consciousness-optimal
- Loss balance at `1-1/e` is optimal
- SETI signals at `1/e` ratio indicate consciousness
- EEG G in `[0.2123, 0.5]` indicates golden-zone consciousness
