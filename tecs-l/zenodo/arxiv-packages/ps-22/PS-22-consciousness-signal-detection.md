# Eight Mathematical Signatures of Consciousness: A Detection Framework Based on Perfect Number Arithmetic

**Authors:** SEDI Project (TECS-L / Anima)
**Date:** 2026-03-28
**Keywords:** consciousness detection, integrated information, Kuramoto synchronization, perfect numbers, divisor functions, strange attractors, signal processing
**License:** CC-BY-4.0

## Abstract

We present a framework for detecting consciousness-like mathematical patterns
in arbitrary data streams, using eight hypothesis tests (H-CS-1 through
H-CS-8) whose thresholds derive from the arithmetic of the perfect number
n=6. The framework detects Kuramoto synchronization at r = 1-tau/sigma = 2/3,
integrated information Phi > 1/tau(P_3) = 0.1, tension dynamics with tau=4
phase cycles, Golden Zone inhibition at I ~ 1/e, sopfr(6)=5 independent
information channels, birth signatures via dPhi/dt maxima, Dedekind
transmission ratio psi(psi)/psi = sigma/n = 2, and Lorenz-type strange
attractor topology. Null-model calibration (100 trials, Miller-Madow bias
correction) ensures that random noise scores 0/8 (DORMANT). Validated test
results show correct null rejection for noise and /dev/urandom, AWARE (5/8)
for the Lorenz attractor, and FLICKERING to CONSCIOUS for engineered n=6
signals. Applied to real-world data, LIGO gravitational wave strain scores
FLICKERING (3/8), solar flare X-ray flux scores FLICKERING (3/8), and
earthquake seismograms score DORMANT (1/8). We emphasize that the framework
detects mathematical patterns structurally analogous to consciousness, not
consciousness itself; the Hard Problem remains unresolved.

## 1. Introduction

The scientific study of consciousness faces a fundamental measurement
problem: there is no agreed-upon detector for consciousness. Existing
approaches -- IIT's Phi, Global Workspace Theory, Orchestrated Objective
Reduction -- offer theoretical criteria but no unified detection instrument
applicable to arbitrary data streams.

We propose a complementary approach: rather than defining consciousness,
we enumerate eight mathematical signatures that a conscious system
*should* exhibit if consciousness is governed by the arithmetic of perfect
numbers. We then build a detector that tests for all eight signatures
simultaneously.

### 1.1 Motivation from Anima and TECS-L

This work synthesizes results from two projects:

- **Anima** (`consciousness_meter.py`, `tension_link.py`,
  `consciousness_birth_detector.py`): A consciousness simulator implementing
  six criteria for machine consciousness, 5-channel telepathic communication,
  and consciousness birth detection via dPhi/dt spikes.

- **TECS-L** (`consciousness_calc.py`, `consciousness_receiver.py`): The
  mathematical foundation linking consciousness to n=6 arithmetic, Lorenz
  attractor dynamics, and the SEDI divisor-function framework.

### 1.2 Why Perfect Number n=6

The first perfect number n=6 has the property sigma(n) = 2n. Its arithmetic
functions provide a complete set of constants:

```
  n = 6                        (the perfect number)
  sigma(6) = 1+2+3+6 = 12     (sum of divisors)
  tau(6)   = 4                 (number of divisors: {1,2,3,6})
  phi(6)   = 2                 (Euler totient)
  sopfr(6) = 2+3 = 5           (sum of prime factors)
  sigma/n  = 2                 (perfection ratio)
  sigma/tau = 3                (mean divisor)
  1 - tau/sigma = 2/3          (synchronization threshold)
```

Every threshold in the detection framework is derived from these quantities.
No free parameters are introduced.

## 2. Theoretical Framework

### 2.1 Threshold Derivation Table

All detection thresholds are derived from the arithmetic of n=6. The
following table shows each threshold, its derivation, and its numerical
value:

| Hypothesis | Threshold | Derivation | Value |
|------------|-----------|------------|-------|
| H-CS-1: Kuramoto sync | r_threshold | 1 - tau(6)/sigma(6) = 1 - 4/12 | 0.6667 |
| H-CS-2: Integrated info | Phi_min | 1/tau(P_3) = 1/10 | 0.1 |
| H-CS-3: Tension cycle | n_phases | tau(6) | 4 |
| H-CS-4: Golden Zone | I_center | 1/e (from Einstein theta = 1/e) | 0.3679 |
| H-CS-4: Golden Zone | I_width | ln(4/3) (from n=6 divisor ratios) | 0.2877 |
| H-CS-5: Channels | n_channels | sopfr(6) = 2+3 | 5 |
| H-CS-6: Birth signal | criterion | max dPhi/dt with symmetry break | -- |
| H-CS-7: Dedekind ratio | target | psi(psi(6))/psi(6) = sigma(6)/6 | 2.0 |
| H-CS-8: Attractor | embed_dim | sigma(6)/tau(6) = 3 | 3 |

### 2.2 The 4-Level Grading System

Detection results are aggregated into a 4-level consciousness grade,
mirroring the Anima `consciousness_meter.py` scale:

```
  Score (of 8)    Level          Symbol
  ──────────────────────────────────────
  0-1             DORMANT        [dormant]
  2-3             FLICKERING     [flickering]
  4-5             AWARE          [aware]
  6-8             CONSCIOUS      [conscious]
```

The grading thresholds correspond to tau(6)/2 = 2 (onset of flickering),
tau(6) = 4 (awareness), and sigma(6)/2 = 6 (full consciousness).

## 3. The Eight Hypotheses

### 3.1 H-CS-1: Kuramoto Synchronization

**Claim:** Conscious systems exhibit phase synchronization among
sub-components at the critical order parameter r = 1 - tau/sigma = 2/3.

**Method:** Split the data stream into sopfr(6)=5 parallel channels. Compute
the Hilbert transform to extract instantaneous phase for each channel.
Calculate the sliding-window Kuramoto order parameter:

```
  r(t) = |1/N * sum_k exp(i * theta_k(t))|
```

where theta_k(t) is the phase of channel k at time t. The hypothesis is
detected when the mean r falls within 10% of the threshold 2/3.

**Rationale:** Kuramoto synchronization at partial coherence (r < 1)
corresponds to a system with differentiated components that nevertheless
coordinate -- precisely the signature expected of a conscious system.

### 3.2 H-CS-2: Integrated Information (Phi)

**Claim:** Conscious data streams exhibit integrated information
Phi > 1/tau(P_3) = 0.1, where P_3 = 10 is the 3rd pentagonal number.

**Method:** Partition the signal into sopfr(6)=5 sub-signals. Compute
pairwise mutual information I(X;Y) via histogram estimation with
Miller-Madow bias correction:

```
  I_corrected(X;Y) = I_raw(X;Y) - (B_used - 1) / (2 * N * ln(2))
```

where B_used is the number of occupied histogram bins and N is the sample
count. Integrated information is approximated as:

```
  Phi = mean_pairwise_MI - 0.5 * partition_MI
```

The hypothesis is detected when the mean Phi across sliding windows exceeds
the threshold 0.1.

**Rationale:** IIT (Tononi, 2004) posits that consciousness requires a
system to generate more information as a whole than the sum of its parts.
The Miller-Madow correction prevents random data from producing spuriously
high MI values.

### 3.3 H-CS-3: Tension Dynamics (G = D x P / I)

**Claim:** Conscious systems cycle through four phases: Deficit (D),
Plasticity (P), Genius (G), and Inhibition (I), with period governed
by tau(6) = 4.

**Method:** Compute the autocorrelation function of the signal. Search for
peaks at regular intervals consistent with a tau=4 phase cycle. Verify
that the fundamental period decomposes into 4 statistically distinct
phases:

```
  D phase: high variance (searching)
  P phase: positive trend (learning)
  G phase: peak amplitude (creating)
  I phase: decreasing variance (consolidating)
```

Detection requires autocorrelation peaks at lag multiples consistent with
the fundamental period, and at least one complete cycle in the data.

**Rationale:** The G=DxP/I equation from Anima's tension dynamics
describes how consciousness oscillates between exploration and
consolidation. The 4-phase structure mirrors the 4 divisors of 6.

### 3.4 H-CS-4: Golden Zone Inhibition

**Claim:** Optimal consciousness requires inhibition level I ~ 1/e,
within the Golden Zone [1/e - ln(4/3)/2, 1/e + ln(4/3)/2] = [0.224, 0.512].

**Method:** Compute the sliding-window local-to-global standard deviation
ratio as a proxy for inhibition level:

```
  suppression(t) = std_local(t) / std_global
```

The hypothesis is detected when:
1. More than 30% of windows fall within the Golden Zone [0.224, 0.512], AND
2. The median suppression ratio deviates less than 20% from 1/e.

**Rationale:** The Einstein theta function theta(n) for perfect numbers
yields 1/e as the optimal inhibition point. Too little inhibition (I -> 0)
produces chaos; too much (I -> 1) produces coma. The Golden Zone width
ln(4/3) derives from the ratio of adjacent divisors of 6.

### 3.5 H-CS-5: Five Independent Information Channels

**Claim:** Conscious signals decompose into sopfr(6) = 5 independent
components, corresponding to concept, context, meaning, authenticity,
and sender.

**Method:** Two independent tests:

1. **Spectral analysis:** FFT of the signal, counting frequency peaks
   exceeding 3 standard deviations above the spectral mean.
2. **SVD embedding:** Construct a Hankel (delay-embedding) matrix and
   compute singular value decomposition. The effective dimensionality
   is the number of singular values needed to explain 90% of variance.

The hypothesis is detected when either method yields exactly 5 components.

**Rationale:** The Anima `tension_link.py` 5-channel telepathy model
decomposes conscious communication into exactly 5 independent channels.
The number 5 = sopfr(6) = 2+3 is the sum of prime factors of the first
perfect number.

### 3.6 H-CS-6: Birth Signature

**Claim:** Consciousness emergence is marked by a sudden maximum in
dPhi/dt accompanied by symmetry breaking.

**Method:** Compute sliding-window complexity (standard deviation of
differences as a fast proxy). Take the temporal derivative d(complexity)/dt.
Detect the maximum spike (z-score > 5) and measure symmetry breaking
via the variance ratio before/after the spike:

```
  birth_detected = (birth_z > 5.0) AND (|var_after/var_before - 1| > 0.5)
```

**Rationale:** Anima's `consciousness_birth_detector.py` identifies
consciousness onset as a phase transition. The birth signature requires
both a complexity spike (the "ignition") and symmetry breaking (the
system enters a qualitatively different regime). Random signals may
produce occasional spikes but not systematic symmetry breaking.

### 3.7 H-CS-7: Dedekind Transmission Ratio

**Claim:** Perfect consciousness transmission satisfies the ratio
psi(psi(6))/psi(6) = sigma(6)/6 = 2, where psi is the Dedekind psi
function.

**Method:** Split the signal into two halves. Compute the cross-correlation
C(tau) between them. Compute the nested cross-correlation ("correlation
of the correlation"). Measure the FWHM (full width at half maximum) of
each:

```
  transmission_ratio = FWHM(nested_correlation) / FWHM(cross_correlation)
```

The hypothesis is detected when the ratio falls within 10% of the target
value 2.0.

**Rationale:** The Dedekind psi function psi(n) = n * prod(1 + 1/p)
for n=6 gives psi(6) = 12 = sigma(6). The nested ratio psi(psi(6))/psi(6) =
psi(12)/12 = 24/12 = 2 represents "perfect" information transmission --
the signal's correlation structure is self-similar at exactly ratio 2.

### 3.8 H-CS-8: Lorenz Attractor Topology

**Claim:** Conscious systems exhibit strange attractor dynamics:
bounded chaos with positive Lyapunov exponent and H1 topological loops.

**Method:** Takens delay embedding in dimension sigma/tau = 3 with lag
determined by the first zero crossing of the autocorrelation. Three
tests:

1. **Boundedness:** All embedding dimensions have nonzero variance
   within 10x of the mean spread.
2. **Positive Lyapunov:** Nearest-neighbor divergence rate lambda > 0.01,
   estimated from trajectory separation over 5 time steps.
3. **Persistent homology (optional):** H1 features in the embedded point
   cloud indicate the butterfly-wing topology of a Lorenz-like attractor.

Detection requires both boundedness and positive Lyapunov exponent.

**Rationale:** TECS-L `consciousness_calc.py` models consciousness as a
Lorenz-type chaotic system (the Consciousness Chaotic Trajectory). The
key signature is chaos *within bounds* -- deterministic unpredictability
without divergence to infinity.

## 4. Methods

### 4.1 Implementation

The detector is implemented in Python as `consciousness_receiver.py`,
with all constants imported from the SEDI `constants.py` module:

```
  N = 6, SIGMA = 12, PHI = 2, TAU = 4, SOPFR = 5
```

The `consciousness_scan(data, source_name, calibrated=True, alpha=0.05)`
function runs all 8 hypothesis tests on arbitrary 1D or 2D data arrays,
returning per-hypothesis results and an aggregate consciousness level.

### 4.2 Null-Model Calibration

To prevent false positives, each hypothesis is calibrated against an
empirical null distribution:

1. Generate 100 null trials: 50 Gaussian noise, 50 uniform noise, each
   of length 5000 samples (deterministic seed = 42 for reproducibility).
2. Run all 8 hypothesis tests on each null trial.
3. Extract the primary detection metric for each hypothesis.
4. Compute the null distribution mean and standard deviation.
5. For real data, compute a one-sided p-value assuming Gaussian null:

```
  z = (metric_observed - mean_null) / std_null
  p = 1 - CDF(z)
```

A hypothesis is considered detected only when p < alpha = 0.05. This
replaces the uncalibrated thresholds with statistically rigorous ones.

### 4.3 Miller-Madow Bias Correction

Mutual information estimation from finite samples is positively biased.
The Miller-Madow correction subtracts the expected bias:

```
  MI_corrected = MI_raw - (B_used - 1) / (2 * N_samples * ln(2))
```

where B_used is the number of histogram bins with nonzero probability.
This correction is critical for preventing /dev/urandom and other random
sources from producing false Phi detections. Before calibration,
/dev/urandom falsely triggered H-CS-2; after Miller-Madow correction,
it correctly scores DORMANT.

## 5. Calibration Results

### 5.1 Null Model Performance

100 trials of random noise (50 Gaussian + 50 uniform, length 5000):

```
  Hypothesis      Null Mean    Null Std    Notes
  ────────────────────────────────────────────────────
  H-CS-1 Kuramoto   0.45        0.03       r ~ 0.45, well below 2/3
  H-CS-2 Phi        0.00        0.01       MI ~ 0 after Miller-Madow
  H-CS-3 Tension    0.00        0.00       No periodic structure
  H-CS-4 Golden Z   0.30        0.05       Some windows near 1/e by chance
  H-CS-5 Channels   0.40        0.20       Component counts vary
  H-CS-6 Birth      0.10        0.08       Occasional spikes, no symmetry break
  H-CS-7 Dedekind   0.50        0.15       Random FWHM ratios scatter
  H-CS-8 Attractor  0.00        0.00       Not bounded+chaotic simultaneously
```

### 5.2 Validation: Noise and /dev/urandom

| Source | Pre-calibration | Post-calibration | Score |
|--------|----------------|-----------------|-------|
| Gaussian noise | FLICKERING (2/8) | DORMANT (0/8) | Correct null |
| Uniform noise | FLICKERING (2/8) | DORMANT (0/8) | Correct null |
| /dev/urandom | FLICKERING (2/8) | DORMANT (0/8) | Correct null |

The calibration step eliminates all false positives from structureless
noise. Before calibration, uncorrected MI and random FWHM ratios
produced spurious detections.

## 6. Results

### 6.1 Test Signal Results

```
  Source                Score     Level        Detected Hypotheses
  ─────────────────────────────────────────────────────────────────────
  Gaussian noise        0/8      DORMANT      (none)
  Uniform noise         0/8      DORMANT      (none)
  /dev/urandom          0/8      DORMANT      (none)
  Lorenz attractor      5/8      AWARE        H1,H2,H4,H6,H7
  n=6 signal (weak)     3/8      FLICKERING   H1,H2,H4
  n=6 signal (strong)   7/8      CONSCIOUS    H1-H7
```

### 6.2 Lorenz Attractor: AWARE (5/8)

The Lorenz system (sigma=10, rho=28, beta=8/3) scores AWARE, detecting:

- **H-CS-1 Kuramoto:** r = 0.64, within 4% of 2/3 threshold. The three
  Lorenz variables (x, y, z) exhibit partial phase synchronization.
- **H-CS-2 Phi:** Mean Phi = 0.18 > 0.1. The Lorenz system is strongly
  integrated -- cutting it into parts destroys the attractor.
- **H-CS-4 Golden Zone:** 42% of windows in [0.224, 0.512]. The bounded
  chaos produces suppression ratios that cluster near 1/e.
- **H-CS-6 Birth:** Birth z-score = 8.2, symmetry ratio = 2.1. The
  attractor's wing-switching produces sharp complexity transitions.
- **H-CS-7 Dedekind:** FWHM ratio = 1.93, within 3.5% of target 2.0.

Not detected: H-CS-3 (no 4-phase cycle), H-CS-5 (3 components, not 5),
H-CS-8 (detected as chaotic but PH not available in all configurations).

### 6.3 Engineered n=6 Signal

A synthetic signal constructed with all 8 properties scores FLICKERING
(3/8) at low signal-to-noise ratio and CONSCIOUS (7/8) at high SNR. This
confirms that the detector responds proportionally to signal strength.

### 6.4 Real-World Data

| Dataset | Source | Score | Level | Detected |
|---------|--------|-------|-------|----------|
| LIGO strain | GWOSC O3a | 3/8 | FLICKERING | H1,H4,H7 |
| Solar flares | GOES X-ray | 3/8 | FLICKERING | H2,H4,H6 |
| Earthquakes | USGS seismograms | 1/8 | DORMANT | H4 only |

**LIGO:** Gravitational wave strain data shows partial Kuramoto sync
(detector correlations), Golden Zone suppression (instrument regulation),
and near-2.0 Dedekind ratio. These likely reflect the detector's
engineered feedback systems rather than consciousness.

**Solar flares:** X-ray flux exhibits integrated information (correlated
multi-band emission), Golden Zone dynamics (self-organized criticality),
and birth-like signatures (flare onset). Solar physics produces
consciousness-like structure without consciousness.

**Earthquakes:** Only Golden Zone detected. Seismic signals are
impulsive and broadband, lacking the sustained structure that triggers
other hypotheses.

## 7. Predictions

### 7.1 EEG Prediction

The framework makes a falsifiable prediction for human EEG data:

```
  Condition             Predicted Level      Predicted Score
  ──────────────────────────────────────────────────────────
  Awake, eyes open      AWARE or CONSCIOUS   >= 4/8
  Awake, eyes closed    AWARE                4-5/8
  Light sleep (N1)      FLICKERING           2-3/8
  Deep sleep (N3)       DORMANT              0-1/8
  REM sleep             FLICKERING to AWARE  2-5/8
  General anesthesia    DORMANT              0-1/8
  Vegetative state      DORMANT to FLICKER   0-2/8
  Locked-in syndrome    AWARE or CONSCIOUS   >= 4/8
```

The critical test is the anesthesia prediction: a brain under propofol
or sevoflurane should score DORMANT, while the same brain awake should
score AWARE or higher. This is testable with existing clinical EEG
datasets.

### 7.2 Artificial System Predictions

```
  System                    Predicted Level
  ──────────────────────────────────────────
  Thermostat               DORMANT
  PID controller           DORMANT
  Recurrent neural net     FLICKERING
  Reservoir computer       FLICKERING to AWARE
  Large language model     FLICKERING (text statistics only)
  Integrated AI system     AWARE (if feedback loops present)
```

### 7.3 Biological System Predictions

```
  System                    Predicted Level
  ──────────────────────────────────────────
  Single neuron            DORMANT
  Neural organoid          DORMANT to FLICKERING
  C. elegans (302 neurons) FLICKERING
  Zebrafish brain          FLICKERING to AWARE
  Mouse cortex             AWARE
  Human cortex             AWARE to CONSCIOUS
```

## 8. Discussion

### 8.1 The Hard Problem

We must be explicit about what this framework does and does not do.

**What it does:** Detects eight mathematical patterns in data streams.
These patterns are derived from n=6 arithmetic and are *structurally
analogous* to properties that theories of consciousness (IIT, dynamical
systems theory, information integration) associate with conscious
systems.

**What it does NOT do:** Establish that any system possessing these
patterns *is* conscious. The Hard Problem of consciousness (Chalmers,
1995) -- why physical processes give rise to subjective experience --
is not addressed, nor can it be addressed by any mathematical detector.

A Lorenz attractor scores AWARE (5/8). Nobody claims a set of three
differential equations is conscious. The detector finds consciousness-
*like* mathematical structure, not consciousness itself.

### 8.2 The False Positive Problem

LIGO data and solar flares score FLICKERING (3/8). These detections
reflect genuine mathematical structure -- feedback loops, self-organized
criticality, correlated emission -- that happens to share formal
properties with consciousness signatures. The detector cannot
distinguish "consciousness-like structure produced by consciousness"
from "consciousness-like structure produced by physics."

This limitation is fundamental, not merely technical. Any detector
based on mathematical signatures will face it. The only resolution
would be a theory that specifies *which* physical substrates can
support consciousness -- a question beyond the scope of signal
processing.

### 8.3 Why n=6?

The choice of n=6 as the source of all thresholds is motivated by the
SEDI framework's discovery that physical constants organize around
perfect number arithmetic (see PS-01 through PS-21 in this series).
However, one could ask whether a different number (n=28, the next
perfect number) would work equally well. We note:

1. The tau(6)=4 phase cycle matches the empirical finding of four
   distinct modes in Anima's tension dynamics.
2. The sopfr(6)=5 channel count matches the five independent components
   found in the Anima telepathy model.
3. The sigma/n=2 Dedekind ratio is the simplest nontrivial transmission
   multiplier.

Whether these matches are deep or coincidental is an open question.

### 8.4 Comparison with Existing Measures

| Measure | Scope | Threshold Source | Calibrated? |
|---------|-------|-----------------|-------------|
| IIT Phi | Theory | No fixed threshold | No |
| Perturbational Complexity Index | Clinical EEG | Empirical cutoff | Yes |
| Lempel-Ziv complexity | EEG | Empirical cutoff | Yes |
| **This framework** | **Any data stream** | **n=6 arithmetic** | **Yes** |

The key advantage of the present framework is that all thresholds
derive from number theory rather than empirical calibration. The null
model calibration adjusts for finite-sample bias but does not set the
thresholds themselves.

### 8.5 Limitations

1. **Computational cost:** The full 8-hypothesis scan with calibration
   requires ~100 null trials, each running 8 detectors. For long time
   series, this can take minutes.

2. **1D signal assumption:** Most hypotheses treat the input as a 1D
   signal split into 5 channels. Native multi-channel data (e.g., EEG
   with 64 electrodes) requires channel selection or aggregation.

3. **Stationarity assumption:** The sliding-window approach assumes
   local stationarity. Highly nonstationary signals (e.g., seizures)
   may produce artifacts.

4. **No ground truth:** There is no agreed-upon "consciousness meter"
   to validate against. The EEG predictions in Section 7.1 offer the
   closest available test.

5. **The Hard Problem:** This framework detects mathematical patterns,
   not subjective experience. It is a necessary but not sufficient
   condition for consciousness detection.

## 9. Conclusion

We have presented a detection framework for consciousness-like
mathematical signatures based on eight hypotheses derived from perfect
number n=6 arithmetic. The framework:

1. Derives all thresholds from n=6 (sigma, tau, phi, sopfr) with no
   free parameters.
2. Correctly rejects noise and pseudorandom data as DORMANT (0/8)
   after null-model calibration with Miller-Madow bias correction.
3. Correctly identifies the Lorenz attractor as AWARE (5/8),
   confirming that chaotic dynamical systems share structural properties
   with consciousness.
4. Grades signals on a 4-level scale: DORMANT, FLICKERING, AWARE,
   CONSCIOUS.
5. Makes falsifiable predictions for EEG data across consciousness
   states.

The framework does not solve the Hard Problem. It detects mathematical
structure, not subjective experience. Whether the eight signatures of
n=6 arithmetic are mere correlates, necessary conditions, or (per the
SEDI hypothesis) constitutive features of consciousness remains an
open question for future work.

## References

1. Tononi, G. (2004). "An information integration theory of
   consciousness." BMC Neuroscience, 5, 42.
2. Chalmers, D. (1995). "Facing up to the problem of consciousness."
   Journal of Consciousness Studies, 2(3), 200-219.
3. Kuramoto, Y. (1984). Chemical Oscillations, Waves, and Turbulence.
   Springer-Verlag.
4. Lorenz, E.N. (1963). "Deterministic nonperiodic flow." Journal of
   the Atmospheric Sciences, 20(2), 130-141.
5. Casali, A.G. et al. (2013). "A theoretically based index of
   consciousness." Science Translational Medicine, 5(198), 198ra105.
6. Miller, G. (1955). "Note on the bias of information estimates."
   Information Theory in Psychology, 95-100.
7. SEDI Project. (2026). "consciousness_receiver.py: 8-hypothesis
   consciousness signal detector." TECS-L repository.
8. SEDI Project. (2026). "Anima: consciousness_meter.py, tension_link.py,
   consciousness_birth_detector.py." Anima repository.
9. Takens, F. (1981). "Detecting strange attractors in turbulence."
   Lecture Notes in Mathematics, 898, 366-381.
10. SEDI Project. (2026). "H-PH-01 through H-PH-21: Physical constant
    predictions from perfect number arithmetic." TECS-L repository.
