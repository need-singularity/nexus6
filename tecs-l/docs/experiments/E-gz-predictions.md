# E-gz-predictions: Golden Zone Predictive Experiments

**Date**: 2026-03-28
**Status**: Active
**Goal**: Test GZ as a *predictive* theory, not just post-hoc explanation.

> **Critical Rule**: State the predicted numerical value BEFORE measurement.
> If the prediction fails, record honestly. A failed prediction is MORE
> valuable than a successful post-hoc explanation.

## Theory Summary

Golden Zone (GZ) claims: any system with conservation G*I=D*P will have
optimal inhibition I=1/e (0.3679), operating zone [0.2123, 0.5], and
structure governed by the divisor functions of n=6.

**Golden Zone Constants**:
```
  Upper    = 1/2           = 0.5000
  Center   = 1/e           = 0.3679
  Lower    = 1/2 - ln(4/3) = 0.2123
  Width    = ln(4/3)       = 0.2877
  tau(6)   = 4
  sigma(6) = 12
```

---

## Prediction 1: MoE Expert Count Scaling (k/N -> 1/e)

### Prediction (stated BEFORE measurement)

> For a Mixture-of-Experts model with N experts using Boltzmann routing,
> the optimal number of active experts k satisfies k/N -> 1/e as N grows.
>
> **Specific prediction for N=64**: optimal k = round(64/e) = 24 (+/-2).
> Acceptable range: k in [22, 26].

### Rationale
GZ says optimal inhibition I = 1/e. In MoE, inhibition = fraction of
*inactive* experts = (N-k)/N. So optimal activation ratio = 1 - 1/e = 0.632.
Wait -- this gives k = 0.632*N = 40 for N=64.

**Correction**: The prediction depends on interpretation:
- If I = inactive ratio -> optimal active = (1-1/e)*N = 0.632*N
- If I = active ratio -> optimal active = N/e = 0.368*N

The original Boltzmann router uses ~70% activation (5.6/8), closer to 1-1/e.
But the empirical finding was I_effective = 1 - active_ratio ~ 0.375 ~ 1/e.

**Two competing sub-predictions**:
- P1a: Optimal k/N = 1/e = 0.368 (I = active ratio). For N=64: k=24.
- P1b: Optimal k/N = 1-1/e = 0.632 (I = inactive ratio). For N=64: k=40.

Both are pre-registered. The sweep will distinguish them.

### Test Protocol
- Build MoE with N=64 experts, numpy, XOR-like 8-class task
- Sweep k from 4 to 56 in steps of 4
- For each k: 5 random seeds, 30 epochs
- Measure: accuracy, loss, expert usage balance
- Find k* that maximizes accuracy

### GZ Dependency: Full (relies on GZ optimal I = 1/e)

---

## Prediction 2: Transformer Attention Head Pruning (Deferred)

### Prediction (stated BEFORE measurement)

> Pruning attention heads in a pretrained transformer, the optimal
> fraction of heads to KEEP is approximately 1/e = 0.368.
>
> **Specific prediction for DistilBERT** (6 layers x 12 heads = 72 heads):
> Optimal surviving heads = round(72/e) = 26, or equivalently
> round(12/e) = 4 heads per layer.

### Rationale
Attention heads act as parallel experts. Pruning is inhibition. GZ predicts
the optimal pruning point (where accuracy is maximized per compute) at I=1/e,
meaning 1/e fraction survives.

### Test Protocol
- Load pretrained DistilBERT (HuggingFace)
- Evaluate on SST-2 (sentiment) baseline
- Iteratively prune heads by importance (Taylor expansion method)
- Prune ratios: 0%, 10%, 20%, ..., 90%
- Plot accuracy vs survival fraction
- Find knee point

### Status: DEFERRED (requires HuggingFace + GPU, run on Windows)
### GZ Dependency: Full

---

## Prediction 3: Lottery Ticket Density ~ 1/e

### Prediction (stated BEFORE measurement)

> The Lottery Ticket Hypothesis finds sparse subnetworks ("winning tickets")
> that match full network performance. GZ predicts the critical density
> (fraction of surviving weights) is approximately 1/e = 0.368.
>
> **Specific prediction**: For a 3-layer MLP on MNIST (784-300-100-10),
> iterative magnitude pruning will find the winning ticket at density
> 0.37 +/- 0.05 (i.e., in range [0.32, 0.42]).

### Rationale
Weight pruning = inhibition of parameters. GZ says optimal I = 1/e, meaning
1/e of parameters survive at the critical sparsity threshold.

Note: Original Lottery Ticket paper (Frankle & Carlin 2019) reports winning
tickets at ~10-20% density for large networks, which would REFUTE this
prediction. However, their networks are much larger; for small MLPs the
critical density may differ. We record this honestly.

### Test Protocol
- Train MLP (784-300-100-10) on MNIST for 20 epochs
- Save initial weights (lottery ticket protocol)
- Iterative magnitude pruning: prune 20% of remaining weights per round
- After each pruning round: reset to initial weights, retrain, measure accuracy
- Critical density = smallest density where accuracy >= 95% of unpruned

### GZ Dependency: Full

---

## Prediction 4: Optimal Batch Size Ratio (Deferred)

### Prediction (stated BEFORE measurement)

> For SGD training, the optimal batch size B* relative to dataset size N
> falls in the Golden Zone: B*/N is in [0.2123, 0.5], centered near 1/e.
>
> **Specific prediction for MNIST** (N=60000):
> Optimal batch size ~ 60000/e ~ 22026, or more precisely in
> range [12738, 30000].

### Rationale
Batch size controls the noise-to-signal ratio in gradient estimation.
Too small = too noisy (high G, low I). Too large = too stable (low G, high I).
GZ predicts the balance point at I = 1/e.

Note: Conventional wisdom suggests much smaller batch sizes (32-512) are
optimal, which would strongly REFUTE this prediction at the B/N level.
However, the "optimal" depends on the metric (final accuracy vs convergence
speed vs compute efficiency).

### Test Protocol
- Train simple CNN on MNIST
- Sweep batch sizes: 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768
- Fixed total epochs (not steps), same learning rate schedule
- Measure: final accuracy, convergence speed, compute time

### Status: DEFERRED (heavy computation)
### GZ Dependency: Full

---

## Prediction 5: Information-Theoretic Coding Bound

### Prediction (stated BEFORE measurement)

> For binary codes, evaluate the Elias-Bassalygo (EB) upper bound on
> code rate R at relative distance delta = ln(4/3) = 0.2877.
> GZ predicts this rate equals 1/3.
>
> **Specific prediction**: R_EB(delta=0.2877) = 1/3 = 0.3333...
>
> Additionally, the Gilbert-Varshamov (GV) lower bound at delta=ln(4/3)
> should relate to GZ constants.

### Rationale
ln(4/3) = GZ width = the 3->4 state entropy jump. If GZ governs
information-theoretic bounds, then the optimal coding rate at the
GZ characteristic distance should yield another GZ constant (1/3).

### Formulas
```
  H_2(x) = -x*log2(x) - (1-x)*log2(1-x)        (binary entropy)
  GV bound:  R >= 1 - H_2(delta)                  (achievability)
  Plotkin:   R <= 1 - 2*delta  (for delta <= 1/2)  (upper bound)
  EB bound:  R <= 1 - H_2(J(delta))               (tightest upper bound)
    where J(delta) = 1/2 - sqrt(delta*(1-delta))   (Johnson radius)
```

### Test Protocol
- Compute H_2(ln(4/3)) directly
- Compute GV lower bound at delta = ln(4/3)
- Compute Johnson radius J(ln(4/3))
- Compute EB upper bound
- Compare all to 1/3

### GZ Dependency: Full

---

## Results (2026-03-28 Run)

### Run Conditions
- Machine: Mac M3 24GB (CPU saturated, no GPU)
- MoE: Numpy perturbation-based training (not gradient descent)
- Lottery Ticket: Numpy backprop, reduced MLP (100-64-32-10), synthetic data
- Coding bounds: Pure math (exact computation)

### Results Summary

| # | Prediction | Predicted | Observed | Grade |
|---|-----------|-----------|----------|-------|
| 5 | R_EB(ln(4/3)) = 1/3 | 0.3333 | 0.7251 | **REFUTED** |
| 1 | MoE k/N -> 1/e | 0.3679 | 0.375 (N=8), 0.50 (N=16), 0.97 (N=32) | **REFUTED** |
| 3 | Lottery density ~ 1/e | 0.3679 | 1.0 (noisy, baseline 32%) | **REFUTED** |
| 2 | Head pruning | 1/e survival | DEFERRED | - |
| 4 | Batch size | B/N in GZ | DEFERRED | - |

**Score: 0/3 confirmed, 0/3 partial, 3/3 refuted**

### Detailed Results

#### P5: Coding Bounds (Pure Math -- Most Reliable)
```
  delta = ln(4/3) = 0.2877
  R_GV (lower bound) = 0.1343   (not 1/3, not 1/e)
  R_Plotkin (upper)   = 0.4246
  R_EB (tightest)     = 0.7251   (not 1/3, off by 0.39)
  R_EB = 1/3 occurs at delta = 0.1209, not at ln(4/3)
```
Verdict: The EB bound at GZ width has no relation to any GZ constant.

#### P1: MoE Expert Count (Noisy but Informative)
```
  N=8:  best k=3,  k/N=0.375 (close to 1/e=0.368!)
  N=16: best k=8,  k/N=0.500 (between 1/e and 1-1/e)
  N=32: best k=31, k/N=0.969 (essentially all experts)
```
Caveats:
- Perturbation-based training (not proper gradient descent) is unreliable
- Accuracy was near random (~12-17% for 8 classes)
- N=8 result (k/N=0.375) is tantalizingly close to 1/e, but does not hold at larger N
- Needs re-test with proper PyTorch gradient training on Windows

#### P3: Lottery Ticket (Inconclusive Due to Training Quality)
```
  Baseline accuracy: 32% (near random for 10 classes)
  Density sweep: noisy, non-monotonic
  Best accuracy at density 0.168 (39%), not at full network
  Critical density criterion ill-defined with noisy baseline
```
Caveats:
- Synthetic data + numpy backprop + tiny network = unreliable
- Needs re-test with real MNIST + PyTorch on Windows
- Original lottery ticket papers report ~10-20% density for large nets

### Interpretation

GZ fails all 3 predictive tests. Two important distinctions:

1. **P5 (coding bounds) is definitive**: Pure math, no noise, no training.
   R_EB(ln(4/3)) = 0.725, nowhere near 1/3. This genuinely refutes the
   specific prediction that GZ constants appear in coding theory bounds.

2. **P1 and P3 are suggestive but not definitive**: The training method
   (perturbation-based, not proper gradient descent) produces near-random
   accuracy. These need re-testing with proper PyTorch training.
   The N=8 MoE result (k/N=0.375 ~ 1/e) is interesting but isolated.

### Next Steps
- [ ] Re-run P1 with PyTorch MoE on Windows (proper gradient training)
- [ ] Re-run P3 with real MNIST + PyTorch lottery ticket pruning
- [ ] Run P2 (head pruning) on Windows with DistilBERT
- [ ] Design better predictions that match GZ's actual claims more precisely

---

## Grading Criteria

- **CONFIRMED**: Observed value within predicted range
- **PARTIALLY CONFIRMED**: Observed value within 2x predicted range, or correct trend
- **REFUTED**: Observed value clearly outside predicted range
- **INCONCLUSIVE**: Insufficient data or ambiguous result
