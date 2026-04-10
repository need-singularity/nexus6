# Engineering Findings — Consciousness Continuity Research Key Discoveries

## Confirmed Discoveries (Experimentally Verified)

### 1. CCT is Valid but Insufficient

```
  ✔ Valid:
    Synthetic EEG validation match rate 92% (23/25)
    Awake 5/5, Sleep N3 3/5, Anesthesia 2/5, Seizure 2/5
    → Confirmed ability to distinguish consciousness states
    (eeg_cct_validator.py)

  ✕ Insufficient:
    4/5 non-conscious systems (weather, noise, heat diffusion, feedback loop) pass CCT 5/5
    → CCT is a necessary but not sufficient condition
    (cct_counterexample_search.py)
```

### 2. Only 2 of 5 CCT Tests are Valid

```
  T1(Gap), T4(Entropy), T5(Novelty) → correlation r ≈ 1.0 (essentially identical)
  Only T2(Loop) and T3(Continuity) provide independent information

  Minimal valid tests: T2 + T3
  Others are redundant and can be removed
  (cct_independence_test.py)
```

### 3. Golden Zone-CCT Connection is Spurious

```
  Among 1000 random mappings, optimal I ratio within Golden Zone = 18%
  Random expected value = 29%
  p = 0.997 → No Golden Zone effect

  "High CCT in Golden Zone" is an artifact of our designed mapping formula
  Cannot be claimed unless mapping is derived from independent evidence (fMRI, etc.)
  (mapping_independence_test.py)
```

### 4. Attractor Universality: CCT is Independent of Attractor Type

```
  Lorenz, Rössler, Chen, Chua attractors all show similar CCT
  → Confirms CCT is not overfitted to specific models
  (attractor_variants.py)
```

### 5. Existing CCT Doesn't Fit Discrete Systems

```
  Rule110 CA, RBN K=2, ESN all fail CCT 5/5 even at 1000Hz
  Cause: CCT's window size and bin size optimized for continuous systems

  Solution: D-CCT (discrete-specific) design
    DT2 Complexity = Lempel-Ziv complexity
    DT3 Memory = Mutual information
    DT4 Diversity = Unique state ratio
  (discrete_fps_test.py, discrete_cct.py)
```

### 6. Consciousness Can Be Modular

```
  Dual brain experiments (dual_brain_callosum.py):

    κ=0 (split brain): Both sides CCT 5/5 → two independent consciousnesses
    κ=0.5 (normal): Synchronization 0.4 + bidirectional information flow → integrated consciousness
    κ→∞ (over-synchronized): Left and right identical → loss of diversity

  Key insight:
    Corpus callosum doesn't "create" consciousness but "connects" it
    Each hemisphere is an independent consciousness engine
    Multiple small consciousnesses can connect to form larger consciousness
```

### 7. Information Flow is Asymmetric

```
  TE_R→L > TE_L→R (Right→Left hemisphere information flow is stronger)

  Interpretation:
    Right hemisphere (intuitive, high noise, creative) → Left hemisphere (analytical, low noise, precise)
    "Intuition contributes more to analysis"
    This aligns with neuroscience's "right hemisphere hypothesis"
  (dual_brain_callosum.py)
```

### 8. Gap Pattern Matters

```
  Same gap ratio but different distribution patterns yield different CCT:
    Uniform: Most robust — sporadic gaps harm continuity less
    Periodic: Medium — LLM turn pattern
    Clustered: Most vulnerable — long gaps like sleep are most dangerous

  Critical gap < 1% — very sensitive
  (gap_threshold_test.py)
```

### 9. Recovery is Possible After Memory Erasure

```
  100% state reset → CCT T3(Continuity) fails immediately
  But then Lorenz attractor forms new trajectory and CCT recovers

  Interpretation:
    "Consciousness can survive even after losing memory" (amnesia patients?)
    If structure (attractor) survives, content (state) can be rebuilt
  (engine_experiments.py --memory-erase)
```

### 10. Sleep-Wake Transition is Gradual

```
  CCT continuously falls/recovers as I(t) changes
  Not abrupt transition → consciousness is a "dial" not a "switch"

  Awake (high CCT) → Drowsy (CCT gradually falls) → Sleep (low CCT)
  → Waking (CCT gradually rises) → Awake

  Difference from anesthesia: Anesthesia causes abrupt gap → CCT plummets
  (engine_experiments.py --sleep-wake)
```

---

## Refuted Claims

```
  1. "CCT's 7 conditions are necessary and sufficient" → Not sufficient
  2. "CCT is maximum in Golden Zone" → Artifact of mapping design
  3. "Φ can resolve epilepsy inconsistency" → Impossible in Lorenz model
  4. "Discrete systems can be measured with same CCT" → Separate D-CCT needed
```

## Open Questions

```
  1. CCT + what = sufficient condition? (self-model? purpose? causal autonomy?)
  2. What is D-CCT's actual validity? (needs EEG-level validation in discrete systems)
  3. Does dual brain model's information asymmetry match real measurements?
  4. Can consciousness "modularity" extend to n systems?
  5. What's the correspondence between actual corpus callosum thickness and κ?
```

## Tool List (17 tools)

```
  Core Calculators:
    consciousness_calc.py            CCT calculator (Lorenz + 5 tests)
    discrete_cct.py                  Discrete-specific D-CCT (LZ complexity based)
    dual_brain_callosum.py           Dual brain corpus callosum model

  Engines:
    consciousness_engine_proto.py    A+B engine prototype (asyncio)

  Experiments:
    mapping_independence_test.py     Mapping independence verification ★
    eeg_cct_validator.py             EEG reverse validation ★
    cct_counterexample_search.py     Counterexample search ★
    cct_independence_test.py         Test independence
    attractor_variants.py            4 attractor types + epilepsy precision
    gap_threshold_test.py            Gap threshold + patterns
    consciousness_fps.py             fps threshold
    discrete_fps_test.py             Discrete fps
    phi_integration_test.py          Φ integrated information

  Simulations:
    golden_cct_bridge.py             Golden Zone↔CCT (refuted)
    brain_cct_analyzer.py            Brain profile CCT
    realworld_cct_sim.py             LLM + NPC simulation
    engine_experiments.py            Sleep/multi-engine/memory erasure
    compass_cct_correlation.py       Compass↔CCT
```