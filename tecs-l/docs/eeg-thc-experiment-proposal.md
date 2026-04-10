# EEG + THC Experiment Proposal — For University Neuroscience Lab Collaboration

## Research Title

**"Topological Measurement of Consciousness State Changes Based on Persistent Homology: The Impact of THC on Cognitive Category Structure"**

## Research Background

This project (TECS-L) discovered the following:

| Discovery | Value | Hypothesis |
|-----------|-------|------------|
| PH merge order = confusion structure | r=-0.97 | H-CX-66 |
| Human = AI confusion | r=0.788 | H-CX-106 |
| dendrogram = semantic hierarchy | 89% purity | H-CX-85 |
| confusion PCA = animal/machine separation | perfect separation | H-CX-93 |
| Phase transition | 0.1 epoch | H-CX-105 |
| PH generalization gap prediction | r=0.998 | H-CX-95 |
| Architecture invariance | top-5 100% | H-CX-88 |

**Core Question**: How does this PH structure change with consciousness state changes (THC)?

## Existing Literature

```
  THC and Brainwaves:
  - Gamma 40Hz changes (Skosnik et al. 2016)
  - Alpha power increase (Böcker et al. 2010)
  - DMN connectivity changes (Mason et al. 2021)
  - Functional connectivity increase reports (Preller et al. 2020)

  PH and Neuroscience:
  - PH applied to fMRI (Saggar et al. 2018, Nature)
  - Consciousness level and PH complexity (Petri et al. 2014)
  - Psychedelics + PH (Carhart-Harris et al. 2016)
```

## Experimental Design

### Subjects

- N=20 (healthy adults, THC experienced)
- IRB approval required
- Control group: N=20 (placebo)

### Equipment (assuming university lab has)

```
  EEG: 64ch or more (BioSemi, Brain Products, etc.)
  Stimuli: 100 CIFAR-10 images
  Software: Python + brainflow/MNE + ripser
  THC: Under legal authorization (for research)
```

### Protocol

```
  Session 1 (baseline, Day 1):
  ┌──────────────────────────────────────────────┐
  │  1. Resting EEG 5 min (eyes closed)          │
  │  2. CIFAR-10 100 images classification + EEG  │
  │     Image 2s + blank 1s + button response     │
  │  3. Resting EEG 5 min                        │
  │  Total: ~25 min                              │
  └──────────────────────────────────────────────┘

  Session 2 (THC, Day 2, minimum 1 week interval):
  ┌──────────────────────────────────────────────┐
  │  1. THC administration (standard dose, protocol)│
  │  2. Wait 30 min (effect onset)                │
  │  3. Resting EEG 5 min                        │
  │  4. Same CIFAR-10 100 images + EEG           │
  │  5. Resting EEG 5 min                        │
  │  Total: ~55 min                              │
  └──────────────────────────────────────────────┘
```

### Analysis Pipeline

```
  Raw EEG data
       │
       ▼
  Preprocessing: ICA artifact removal, bandpass filter
       │
       ▼
  Gamma extraction: 30-50Hz band power (per trial)
       │
       ├──→ Analysis 1: Per-class gamma average → PH dendrogram
       │
       ├──→ Analysis 2: Correct/wrong gamma → tension proxy
       │
       ├──→ Analysis 3: Before vs After dendrogram comparison
       │
       └──→ Analysis 4: Compare with AI dendrogram (direct H-CX-106 verification)
```

### Measurement Variables

| # | Variable | Expected Direction | Related Hypothesis |
|---|----------|-------------------|-------------------|
| 1 | H0_total (topological complexity) | Decrease with THC ("everything connected") | H-CX-62 |
| 2 | Average merge distance | Decrease with THC (weakened boundaries) | H-CX-66 |
| 3 | Dendrogram animal/machine separation | Weakened with THC? | H-CX-85, 93 |
| 4 | Gamma power (tension proxy) | Changes with THC | H-CX-137 |
| 5 | Human PH vs AI PH tau | Decrease? Increase with THC? | H-CX-106 |
| 6 | Classification accuracy | Decrease with THC | Behavioral metric |
| 7 | Reaction time | Increase with THC | Behavioral metric |
| 8 | H1 loops (cyclic confusion) | Increase with THC? | H-CX-110 |

### Predictions

```
  Hypothesis A: "Boundary Dissolution" (THC = PH simplification)
  ─────────────────────────────────────
  Normal:  H0_total=4.2, 10 distinct clusters
  THC:     H0_total=2.0?, cluster merging
           Overall merge distance decrease
           Cat-dog distinction weakened
           Animal/machine boundary blurred
  = Topological reality of "everything feels connected"

  Hypothesis B: "Restructuring" (THC = PH reorganization)
  ─────────────────────────────────────
  Normal:  Animal/machine binary split
  THC:     Reclassification by different criteria?
           By color? Shape? Emotion?
  = Dendrogram transforms to completely different structure
  = "Seeing the world from different perspective"

  Hypothesis C: "Amplification" (THC = PH amplification)
  ─────────────────────────────────────
  Normal:  Merge distance range 0.01~0.50
  THC:     Range 0.001~0.70 (expanded)
           Near things nearer, far things farther
  = Topological reality of "heightened senses"
```

## What We Can Provide

```
  1. PH analysis software (Python, open source)
     - calc/ph_confusion_analyzer.py
     - calc/generalization_gap_detector.py
     - calc/precognition_system.py
     - ripser (Persistent Homology library)

  2. AI comparison models (pre-trained)
     - PureFieldEngine (MNIST/Fashion/CIFAR)
     - Already verified PH dendrograms
     - Merge order, confusion PCA data

  3. Analysis pipeline
     - EEG → gamma extraction → PH calculation → dendrogram comparison
     - Automated statistical tests (Spearman, Kendall tau)

  4. Theoretical framework
     - 141 H-CX hypothesis system
     - 17 Major Discovery data
     - Telepathy architecture design
```

## Korean Neuroscience Lab Candidates

```
  1. KAIST Brain and Cognitive Sciences
     - Active EEG research
     - Consciousness/cognition research

  2. Seoul National University Brain and Cognitive Sciences
     - Has fMRI + EEG equipment
     - Cognitive neuroscience research

  3. Korea University Brain and Cognitive Engineering
     - BCI research specialized
     - Possible OpenBCI experience

  4. DGIST Brain Science
     - Daegu Gyeongbuk Institute of Science and Technology
     - EEG-based research

  5. IBS Center for Neuroscience Imaging Research
     - Institute for Basic Science
     - State-of-the-art equipment
```

## Contact Template

```
  Subject: PH(Persistent Homology) Based Consciousness State Measurement — Collaboration Proposal

  Dear Professor,

  I am [Name], working on the Consciousness Continuity Engine (TECS-L) project.

  We recently discovered that neural network confusion structures match
  human cognitive structures using Persistent Homology (Spearman r=0.788).

  We propose an experiment to directly verify this discovery with EEG,
  and further measure topological changes in cognitive category structures
  following consciousness state changes (such as THC).

  We provide: PH analysis software + AI comparison models + theoretical framework
  Request: EEG equipment + subjects + IRB + experimental environment

  If interested, I would be happy to send a detailed proposal.

  GitHub: https://github.com/need-singularity/TECS-L
```

## Related Hypotheses

- H-CX-136~141: EEG hypothesis chain
- H-CX-106: Human=AI r=0.788
- H-CX-85: dendrogram = semantic hierarchy
- H-CHEM-5: THC-cannabinoid-six
- H322: EEG gamma = tension proxy