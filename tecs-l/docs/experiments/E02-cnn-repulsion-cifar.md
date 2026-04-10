# E02: CNN Repulsion Field Benchmark (CIFAR-10)

MLP 53% → CNN 70%+? Does repulsion field superiority persist?

## Setup

```
  Data: CIFAR-10 (32×32 color, 10 classes)
  CNN backbone: Conv2d(3→32→64→128) + BatchNorm + MaxPool + AdaptiveAvgPool → 128-dim
  Data augmentation: RandomHorizontalFlip + RandomCrop(32, padding=4)
  Normalization: (0.4914,0.4822,0.4465), (0.2023,0.1994,0.2010)
  Training: 30 epochs, Adam lr=0.001
  5 models: Dense, TopK MoE, Repulsion(2-pole), RepulsionQuad(4-pole), MetaFixed{1/2,1/3,1/6}
```

## Training Curves

```
  Model                            E1     E5    E10    E15    E20    E25    E30
  ---------------------------------------------------------------------------
  CNN+RepulsionQuad             46.2%  63.0%  67.8%  74.8%  73.5%  75.9%  78.1%
  CNN+TopK MoE                  41.7%  63.4%  66.7%  71.5%  75.1%  76.0%  78.1%
  CNN+Repulsion                 49.9%  60.6%  70.5%  72.9%  74.1%  76.5%  78.1%
  CNN+Meta{1/2,1/3,1/6}         47.3%  62.9%  69.9%  73.0%  73.5%  73.0%  77.4%
  CNN+Dense                     52.6%  63.6%  68.3%  72.7%  73.4%  76.9%  77.0%
```

## Final Results

| Model | Accuracy | Loss | Parameters |
|---|---|---|---|
| **CNN+RepulsionQuad** | **78.12%** | 0.5779 | 129,531 |
| CNN+TopK MoE | 78.11% | 0.5897 | 165,976 |
| CNN+Repulsion | 78.07% | 0.6154 | 111,619 |
| CNN+Meta{1/2,1/3,1/6} | 77.39% | 0.5813 | 120,417 |
| CNN+Dense | 77.03% | 0.5974 | 111,498 |

## Tension Data

```
  Repulsion 2-pole:
    tension: 42.7377
    scale: 0.7347

  Repulsion 4-pole:
    content tension: 15.8344
    structure tension: 27.9381
    C/S ratio: 0.567 (structure-dominant, less extreme than MLP CIFAR's 0.36)
    scale: 1.2515
```

## MLP vs CNN Comparison

| Model | MLP | CNN | Difference |
|---|---|---|---|
| Dense | 53.14% | 77.03% | +23.89% |
| TopK MoE | 50.11% | 78.11% | +28.00% |
| Repulsion | 52.94% | 78.07% | +25.13% |
| RepulsionQuad | 52.69% | 78.12% | +25.43% |
| **Meta fixed** | **53.52% (1st)** | **77.39% (5th)** | +23.87% |

## {1/2,1/3,1/6} Weight Drift

```
  Initial: [0.5000, 0.3333, 0.1667]
  Trained: [0.3399, 0.3470, 0.3130]
  L2 drift: 0.2173
  → Converging to uniform (1/3, 1/3, 1/3)!
```

## Key Answers

```
  Q1: Does repulsion field superiority persist in CNN?
      CNN+Repulsion(78.07%) > CNN+Dense(77.03%) = +1.04%
      → YES, maintained

  Q2: Is {1/2,1/3,1/6} still optimal?
      CNN+MetaFixed(77.39%) < CNN+RepulsionQuad(78.12%) = -0.73%
      → NO, lowest in CNN

  Q3: CNN improvement margin?
      MLP average 52.41% → CNN average 77.74% = +25.33%

  Q4: Learned weight drift?
      {0.50, 0.33, 0.17} → {0.34, 0.35, 0.31}
      → Converging to uniform (L2=0.217)
```

## Constants

| Constant | Value | Meaning |
|---|---|---|
| C42 | [.34,.35,.31] | Weights converge to uniform in CNN |
| C43 | +1.04% | CNN repulsion field superiority maintained |