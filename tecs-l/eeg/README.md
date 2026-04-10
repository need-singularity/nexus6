# EEG Experiment Environment — TECS-L G=D×P/I Verification

## Hardware

| Item | Model | Status |
|------|-------|--------|
| Biosensing Board | Cyton+Daisy 16ch | Ordered (OpenBCI All-in-One R&D Bundle) |
| Headset | UltraCortex Mark IV (Medium, Pro-Assembled, 16ch) | Ordered |
| Reference Electrode | Earclip Electrode (0.3m) | Ordered |
| Dry Electrodes | EEG Comb Electrodes (30 pack) | Bundle included |
| Wet Electrodes | Gold Cup Electrodes x2 | Bundle included |
| Conductive Paste | Ten20 | Bundle included |
| EMG/ECG | Snap Electrode Cables (1.5m) x2 + Gel Electrodes x2 | Bundle included |
| Heart Rate | Pulse Sensor | Bundle included |
| Power | Lithium battery + charger | Bundle included |
| Wireless | USB BLE Dongle | Bundle included |

**Order:** OpenBCI Shop, €4,017.90 (Bundle €3,964.95 + Earclip €52.95)

## Software Environment

```bash
# Python venv
source eeg_env/bin/activate

# Installed packages
# mne 1.11.0        — EEG analysis standard library
# brainflow 5.21.0  — Board communication API
# pylsl 1.18.1      — Lab Streaming Layer
# scipy 1.17.1      — Signal processing
# matplotlib 3.10.8 — Visualization
# numpy 2.4.3       — Numerical computing
# pandas 3.0.1      — Data handling
# pyserial 3.5      — Serial port communication
```

## Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `collect.py` | EEG data collection | `python eeg/collect.py --duration 60 --tag resting_eyes_closed` |
| `analyze.py` | Band power + G=D×P/I mapping | `python eeg/analyze.py eeg/data/<file>.npy --topomap` |

## Quick Start (After Hardware Arrives)

```bash
# 0. Activate environment
cd ~/Dev/TECS-L
source eeg_env/bin/activate

# 1. Hardware setup
#    - Insert battery into Cyton+Daisy board
#    - Mount board on UltraCortex headset top slot
#    - Plug USB dongle into Mac
#    - Put on headset, adjust electrode positions
#    - Attach earclip electrodes to both earlobes

# 2. Verify connection
python eeg/collect.py --duration 5 --tag connection_test

# 3. Collect resting state EEG
python eeg/collect.py --duration 60 --tag resting_eyes_closed
python eeg/collect.py --duration 60 --tag resting_eyes_open

# 4. Analyze
python eeg/analyze.py eeg/data/eeg_*_resting_eyes_closed.npy --topomap
python eeg/analyze.py eeg/data/eeg_*_resting_eyes_open.npy --topomap

# 5. Test without hardware (synthetic mode)
python eeg/collect.py --duration 5 --board synthetic --tag test
python eeg/analyze.py eeg/data/eeg_*_test.npy
```

## G=D×P/I EEG Mapping

```
Parameter       EEG Proxy                    Brain Region
─────────────────────────────────────────────────────────
I (Inhibition)  Frontal Alpha power (8-12Hz) Fp1, Fp2, F3, F4
P (Plasticity)  Global Gamma power (30-100Hz) All channels
D (Deficit)     Alpha asymmetry |ln(R)-ln(L)| Frontal pairs (Fp1-Fp2, F3-F4, F7-F8)
G (Genius)      D × P / I                    Computed

Golden Zone: [0.2123, 0.5000]
  Lower = 1/2 - ln(4/3)  (Entropy boundary)
  Upper = 1/2             (Riemann critical line)
```

## Frequency Bands

| Band | Range (Hz) | Associated With |
|------|-----------|-----------------|
| Delta | 0.5-4 | Deep sleep, unconscious |
| Theta | 4-8 | Drowsiness, meditation, memory |
| Alpha | 8-12 | Relaxation, inhibition, idle |
| Beta | 13-30 | Active thinking, focus |
| Gamma | 30-100 | Higher cognition, binding, plasticity |

## 16-Channel Layout (10-20 System)

```
        Fp1   Fp2          Frontal pole
          \   /
     F7 - F3 - F4 - F8    Frontal
          |   |
     T7 - C3 - C4 - T8    Central / Temporal
          |   |
          P3 - P4          Parietal
         / | | \
     P7         P8         Parietal-temporal
        O1   O2            Occipital

Cyton (1-8):  Fp1, Fp2, C3, C4, P7, P8, O1, O2
Daisy (9-16): F7, F8, F3, F4, T7, T8, P3, P4
Reference:    Earclip (both earlobes)
```

## Experiment Protocols (Planned)

### Protocol 1: Resting State Baseline
- Eyes closed 60s → Eyes open 60s → Eyes closed 60s
- Measure: Alpha power change, asymmetry baseline

### Protocol 2: Cognitive Load (N-back)
- 0-back → 1-back → 2-back → 3-back (60s each)
- Measure: Beta/Gamma increase, Alpha suppression = I change

### Protocol 3: Creative vs Analytical
- Math problem solving 120s → Free association 120s
- Measure: Gamma pattern difference = P proxy

### Protocol 4: Meditation / Flow State
- Normal → Focused breathing 300s → Post
- Measure: Alpha/Theta ratio, Golden Zone approach

## Data Storage

```
eeg/data/                          (gitignored)
  eeg_YYYYMMDD_HHMMSS_<tag>.npy   Raw numpy array (channels x samples)
  eeg_YYYYMMDD_HHMMSS_<tag>.csv   Spreadsheet format
  eeg_YYYYMMDD_HHMMSS_<tag>_meta.json          Metadata
  eeg_YYYYMMDD_HHMMSS_<tag>_analysis.json      Analysis results
  eeg_YYYYMMDD_HHMMSS_<tag>_bandpower.png      Band power heatmap
  eeg_YYYYMMDD_HHMMSS_<tag>_topomap.png        Brain topomap
```

## Troubleshooting

```
Serial port not found:
  → ls /dev/tty.usbserial* /dev/cu.usbserial*
  → Specify with --port /dev/tty.usbserialXXXX

Poor signal quality:
  → Apply Ten20 paste to electrodes
  → Replace spike electrodes with Comb electrodes
  → Check earclip contact
  → Reduce muscle tension (relax jaw, forehead)

High impedance warning in OpenBCI GUI:
  → Reposition electrode closer to scalp
  → Add more conductive paste
  → Clean scalp with alcohol swab
```
