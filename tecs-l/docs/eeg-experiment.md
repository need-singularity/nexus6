# 🧪 EEG Experiment — G=D×P/I Biological Verification

> **Hypothesis:** The Golden Zone model G=D×P/I has a measurable biological correlate in EEG frequency band structure. If G=D×P/I captures something real about brain function, then EEG-derived proxies for D, P, and I should produce G values that respond systematically to cognitive state changes and cluster within the Golden Zone [0.2123, 0.5] for high-performance states.

## Background

TECS-L's core formula G=D×P/I emerged from mathematical analysis of perfect number 6 and has been validated computationally (Golden MoE: MNIST +0.6%, CIFAR +4.8%). The next step is **biological validation** — measuring actual brain signals and testing whether the model's parameters map to real neural dynamics.

EEG (Electroencephalography) measures electrical activity across the scalp at millisecond resolution. Different frequency bands reflect different cognitive processes, providing natural proxies for G=D×P/I parameters.

## Hardware

### OpenBCI All-in-One Biosensing R&D Bundle

| Component | Model | Spec |
|-----------|-------|------|
| Board | Cyton+Daisy | 16-channel, 250Hz, 24-bit ADC, BLE wireless |
| Headset | UltraCortex Mark IV | Pro-Assembled, Medium, 3D-printed, dry electrodes |
| Dry Electrodes | Ag-AgCl Comb (30 pack) | Hair-penetrating, research-grade signal quality |
| Wet Electrodes | Gold Cup x2 | Traditional clinical-grade |
| Reference | Earclip Electrode (0.3m) | Both earlobes, ground/reference |
| EMG/ECG | Snap Cables (1.5m) x2 + Gel Electrodes x2 | Muscle/heart signal capability |
| Heart Rate | Pulse Sensor | PPG-based heart rate monitor |
| Conductive Paste | Ten20 (8 oz jar) | Standard neurodiagnostic paste |
| Power | Lithium battery + charger | Rechargeable, included with Cyton |
| Wireless | USB BLE Dongle | Included with Cyton, plugs into PC |

**Total Cost:** €4,017.90 (Bundle €3,964.95 + Earclip €52.95)
**Ordered:** 2026-03-27 from [shop.openbci.com](https://shop.openbci.com/)

### Connection Diagram

```
  ┌──────────────────────────────────────────────┐
  │           UltraCortex Mark IV                 │
  │                                               │
  │   Fp1  Fp2  F3  F4  F7  F8  C3  C4          │
  │   P3   P4   P7  P8  T7  T8  O1  O2          │
  │        (16 dry comb electrodes)               │
  │              │                                │
  │    ┌─────────┴─────────┐                      │
  │    │  Cyton+Daisy Board │ ← mounted on top    │
  │    │  (16ch, 250Hz)     │                     │
  │    └────────┬──────────┘                      │
  └─────────────│─────────────────────────────────┘
                │ BLE wireless
                ▼
         ┌──────────┐
         │USB Dongle│ → PC (Mac/Windows)
         └──────────┘

  Earclip electrodes → both earlobes (reference/ground)
  Pulse sensor → fingertip (heart rate)
```

## G=D×P/I → EEG Parameter Mapping

### Theoretical Basis

| Parameter | EEG Proxy | Frequency Band | Brain Region | Rationale |
|-----------|-----------|----------------|--------------|-----------|
| **I** (Inhibition) | Frontal Alpha power | 8-12 Hz | Fp1, Fp2, F3, F4 | Alpha reflects cortical inhibition/idling. Higher alpha = more inhibition = higher I |
| **P** (Plasticity) | Global Gamma power | 30-100 Hz | All 16 channels | Gamma bursts correlate with synaptic plasticity, binding, and learning. Higher gamma = more plasticity |
| **D** (Deficit) | Alpha frontal asymmetry | 8-12 Hz | Fp1-Fp2, F3-F4, F7-F8 pairs | Hemispheric asymmetry indicates atypical processing patterns. Greater asymmetry = larger deficit |
| **G** (Genius) | Computed: D×P/I | — | — | Derived from the three EEG proxies |

### Computation

```
  I = mean(relative_alpha_power[Fp1, Fp2, F3, F4])

  P = mean(relative_gamma_power[all 16 channels])

  D = mean(|ln(R) - ln(L)|)  for pairs (Fp1-Fp2, F3-F4, F7-F8)

  G = D × P / I

  Golden Zone check: 0.2123 ≤ G ≤ 0.5000
    Lower = 1/2 - ln(4/3)  (Entropy boundary)
    Upper = 1/2             (Riemann critical line)
```

## 16-Channel Layout (International 10-20 System)

```
            Nasion (nose)
               │
          Fp1  │  Fp2           ← Frontal pole (attention, inhibition)
            \  │  /
       F7 ─ F3 ┼ F4 ─ F8      ← Frontal (executive function)
            │  │  │
       T7 ─ C3 ┼ C4 ─ T8      ← Central/Temporal (motor, language)
            │  │  │
            P3 ┼ P4            ← Parietal (spatial, integration)
           / │ │ │ \
       P7    │ │ │    P8       ← Parietal-temporal
          O1 │ │ │ O2         ← Occipital (visual)
               │
            Inion (back)

  ┌────────────────────────────────────────────┐
  │ Cyton channels (1-8):                      │
  │   Fp1, Fp2, C3, C4, P7, P8, O1, O2       │
  │                                            │
  │ Daisy channels (9-16):                     │
  │   F7, F8, F3, F4, T7, T8, P3, P4          │
  │                                            │
  │ Reference: Earclip (A1, A2 = both earlobes)│
  └────────────────────────────────────────────┘
```

## EEG Frequency Bands

| Band | Range (Hz) | Associated With | G=D×P/I Role |
|------|-----------|-----------------|--------------|
| **Delta** | 0.5 - 4 | Deep sleep, unconscious processing | — |
| **Theta** | 4 - 8 | Drowsiness, meditation, memory encoding | Flow state indicator |
| **Alpha** | 8 - 12 | Relaxation, cortical inhibition, idle | **I (Inhibition)** |
| **Beta** | 13 - 30 | Active thinking, focus, anxiety | Cognitive engagement |
| **Gamma** | 30 - 100 | Higher cognition, binding, insight | **P (Plasticity)** |

## Experiment Protocols

### Protocol 1: Resting State Baseline

```
  Purpose:  Establish individual baseline for all parameters
  Duration: 3 minutes total
  Procedure:
    [0:00-1:00]  Eyes closed, relaxed
    [1:00-2:00]  Eyes open, fixate on cross
    [2:00-3:00]  Eyes closed, relaxed

  Expected:
    Eyes closed → High alpha (I↑) → G↓
    Eyes open   → Alpha suppression (I↓) → G↑
    This is the most basic EEG effect — if we don't see this, hardware has issues.

  Measures:
    - Alpha power (eyes closed vs open)
    - Asymmetry baseline
    - All band powers for normalization
```

### Protocol 2: Cognitive Load (N-back Task)

```
  Purpose:  Measure I change under increasing cognitive demand
  Duration: 4 minutes total
  Procedure:
    [0:00-1:00]  0-back (press for any stimulus)     — minimal load
    [1:00-2:00]  1-back (press if same as previous)  — light load
    [2:00-3:00]  2-back (press if same as 2 ago)     — moderate load
    [3:00-4:00]  3-back (press if same as 3 ago)     — heavy load

  Expected:
    Load↑ → Alpha↓ (I↓) + Beta/Gamma↑ (P↑) → G↑
    If G enters Golden Zone under optimal cognitive load → model validated

  Measures:
    - Alpha suppression per load level
    - Gamma increase per load level
    - G trajectory: does it approach Golden Zone?
```

### Protocol 3: Creative vs Analytical

```
  Purpose:  Measure P (plasticity) difference between creative and analytical states
  Duration: 4 minutes total
  Procedure:
    [0:00-2:00]  Math problem solving (serial subtraction, 7s)
    [2:00-4:00]  Free association / divergent thinking

  Expected:
    Math → Beta dominant, focused
    Creative → Gamma bursts, alpha intermittent (defocused attention)
    P_creative > P_analytical

  Measures:
    - Gamma burst frequency and amplitude
    - Alpha/Beta ratio shift
    - Asymmetry changes (D shift between modes)
```

### Protocol 4: Meditation / Flow State

```
  Purpose:  Test Golden Zone approach during flow states
  Duration: 8 minutes total
  Procedure:
    [0:00-1:00]  Normal resting baseline
    [1:00-6:00]  Focused breathing meditation
    [6:00-8:00]  Post-meditation resting

  Expected:
    Meditation → Theta↑ + Alpha↑ (relaxed attention)
    Experienced meditators may show Gamma bursts during deep states
    G may oscillate near Golden Zone boundaries

  Measures:
    - Theta/Alpha ratio (meditation depth)
    - G time series (does G stabilize near Golden Zone?)
    - Pre vs post comparison
```

### Protocol 5: Savant State Simulation (Future)

```
  Purpose:  Test Savant hypothesis (H-359) — Inhibition release → explosive specialization
  Duration: Variable
  Procedure:
    Baseline → specific domain task → measure I suppression
    Compare I levels between general vs specialized tasks

  Expected (from H-359):
    Savant state → I drops to Golden Zone lower bound (0.2123)
    Domain-specific Gamma explodes → P↑
    G approaches maximum within Golden Zone

  Prerequisites:
    Baseline data from Protocols 1-4 first
```

## Software Pipeline

### Environment Setup

```bash
cd ~/Dev/TECS-L
source eeg_env/bin/activate

# Installed packages:
#   mne 1.11.0       — EEG analysis standard library
#   brainflow 5.21.0 — OpenBCI board communication
#   pylsl 1.18.1     — Lab Streaming Layer protocol
#   scipy 1.17.1     — Signal processing (Welch PSD, filters)
#   matplotlib 3.10.8— Visualization
#   numpy 2.4.3      — Numerical computing
#   pandas 3.0.1     — Data handling
#   pyserial 3.5     — Serial port communication
```

### Data Collection

```bash
# Test without hardware (synthetic data)
python eeg/collect.py --duration 5 --board synthetic --tag test

# Real data collection (after hardware arrives)
python eeg/collect.py --duration 60 --tag resting_eyes_closed
python eeg/collect.py --duration 60 --tag resting_eyes_open
python eeg/collect.py --duration 240 --tag nback_task
python eeg/collect.py --duration 240 --tag creative_vs_analytical
python eeg/collect.py --duration 480 --tag meditation
```

### Analysis

```bash
# Full analysis with brain topomap
python eeg/analyze.py eeg/data/<file>.npy --topomap

# Output:
#   - Band power table (absolute + relative, per channel)
#   - Alpha asymmetry report
#   - G=D×P/I computation + Golden Zone check
#   - Band power heatmap (PNG)
#   - Brain topomap (PNG, with --topomap flag)
#   - Analysis results (JSON)
```

### Output Files

```
eeg/data/
  eeg_YYYYMMDD_HHMMSS_<tag>.npy          Raw numpy (channels × samples)
  eeg_YYYYMMDD_HHMMSS_<tag>.csv          Spreadsheet format
  eeg_YYYYMMDD_HHMMSS_<tag>_meta.json    Recording metadata
  eeg_YYYYMMDD_HHMMSS_<tag>_analysis.json Analysis results (G=D×P/I values)
  eeg_YYYYMMDD_HHMMSS_<tag>_bandpower.png Band power heatmap
  eeg_YYYYMMDD_HHMMSS_<tag>_topomap.png  Brain topomap
```

## Predicted Outcomes & Falsification

### If Model is Correct

```
  1. Resting state:
     - Eyes closed: high I (alpha), low G → below Golden Zone
     - Eyes open: lower I, G shifts upward

  2. Cognitive load:
     - Increasing load → I↓, P↑ → G↑
     - Optimal performance zone = G in Golden Zone

  3. Creative state:
     - Gamma bursts → P spikes
     - G shows intermittent Golden Zone entries during "aha" moments

  4. Meditation:
     - Experienced meditators → G stabilizes near Golden Zone
     - Novices → G fluctuates widely

  5. Cross-individual:
     - High-performing individuals → G closer to Golden Zone center (1/e ≈ 0.368)
```

### Falsification Criteria

```
  The model is WRONG if:
    ✗ G shows no systematic change across cognitive states
    ✗ G values are uniformly distributed (no clustering)
    ✗ No correlation between EEG-derived G and task performance
    ✗ Alpha asymmetry (D) has no relation to individual differences
    ✗ Gamma (P) doesn't change between creative and analytical tasks

  The MAPPING is wrong (but model may be right) if:
    ? Parameters don't map cleanly to single frequency bands
    ? Non-linear combinations work better than D×P/I
    ? Other bands (theta, beta) are better proxies
```

## Related Hypotheses

| # | Hypothesis | Relevance |
|---|-----------|-----------|
| H-019 | Golden MoE Performance | Computational G=D×P/I validation |
| H-172 | G×I=D×P Conservation Law | Conservation should hold in EEG data |
| H-359 | Savant Golden Zone Inhibition | I→lower bound during specialization |
| H-139 | Golden Zone = Edge of Chaos | Langton λ_c mapping to brain criticality |

## Troubleshooting

```
  Serial port not found:
    → ls /dev/tty.usbserial* /dev/cu.usbserial*
    → Specify with --port /dev/tty.usbserialXXXX
    → Try unplugging and replugging USB dongle

  Poor signal quality / high noise:
    → Apply Ten20 paste to electrode contact points
    → Replace spike electrodes with Comb electrodes (Ag-AgCl)
    → Check earclip contact on earlobes
    → Relax jaw and forehead muscles (reduce EMG artifact)
    → Move away from electrical outlets and screens

  Flat line on one or more channels:
    → Electrode not making scalp contact
    → Rotate blue electrode holder to adjust depth
    → Check cable connection to board pin

  Packet loss / dropouts:
    → Move closer to USB dongle (BLE range ~10m)
    → Reduce interference (turn off other BLE devices)
    → Check battery level

  OpenBCI GUI impedance warning:
    → Reposition electrode closer to scalp
    → Add more conductive paste
    → Clean scalp area with alcohol swab first
```
