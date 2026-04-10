======================================================================
  CROSS-UNIVERSE REPULSION EXPERIMENT
  What happens when alien models are forced into a repulsion field?
======================================================================

[1] Loading data from two universes...
    Data loaded in 1.0s
    Universe M (MNIST): 784-dim, 60k train, 10k test
    Universe C (CIFAR): 3072-dim, 50k train, 10k test

──────────────────────────────────────────────────────────────────────
[2] PHASE A: Training Universe M (MNIST encoder + pole)
──────────────────────────────────────────────────────────────────────
    [MNIST] Epoch  1/10: Loss=0.2710, Acc=95.9%
    [MNIST] Epoch  2/10: Loss=0.1037, Acc=97.3%
    [MNIST] Epoch  4/10: Loss=0.0486, Acc=97.1%
    [MNIST] Epoch  6/10: Loss=0.0319, Acc=97.6%
    [MNIST] Epoch  8/10: Loss=0.0240, Acc=97.8%
    [MNIST] Epoch 10/10: Loss=0.0180, Acc=98.0%
    >>> Universe M final accuracy: 98.0%

──────────────────────────────────────────────────────────────────────
[3] PHASE B: Training Universe C (CIFAR encoder + pole)
──────────────────────────────────────────────────────────────────────
    [CIFAR] Epoch  1/10: Loss=1.6401, Acc=47.1%
    [CIFAR] Epoch  2/10: Loss=1.4228, Acc=49.8%
    [CIFAR] Epoch  4/10: Loss=1.2333, Acc=51.7%
    [CIFAR] Epoch  6/10: Loss=1.0834, Acc=53.8%
    [CIFAR] Epoch  8/10: Loss=0.9594, Acc=54.4%
    [CIFAR] Epoch 10/10: Loss=0.8506, Acc=53.9%
    >>> Universe C final accuracy: 53.9%

──────────────────────────────────────────────────────────────────────
[4] PHASE A2: Training second MNIST model (same-universe baseline)
──────────────────────────────────────────────────────────────────────
    [MNIST-2] Epoch  1/10: Loss=0.2650, Acc=96.0%
    [MNIST-2] Epoch  2/10: Loss=0.1004, Acc=97.2%
    [MNIST-2] Epoch  4/10: Loss=0.0499, Acc=98.0%
    [MNIST-2] Epoch  6/10: Loss=0.0322, Acc=97.7%
    [MNIST-2] Epoch  8/10: Loss=0.0237, Acc=97.8%
    [MNIST-2] Epoch 10/10: Loss=0.0171, Acc=97.7%
    >>> Universe M2 final accuracy: 97.7%

──────────────────────────────────────────────────────────────────────
[5] EXPERIMENT A: Same-Universe Repulsion (MNIST + MNIST)
    Both poles trained on MNIST. Repulsion field on MNIST.
──────────────────────────────────────────────────────────────────────
    [Same-Univ] Epoch  1/10: Loss=0.5411, Acc=97.6%, Tension=0.0607, tau=0.5301
    [Same-Univ] Epoch  2/10: Loss=0.0772, Acc=97.9%, Tension=0.0607, tau=0.5949
    [Same-Univ] Epoch  4/10: Loss=0.0283, Acc=98.0%, Tension=0.0607, tau=0.6469
    [Same-Univ] Epoch  6/10: Loss=0.0175, Acc=98.1%, Tension=0.0607, tau=0.6721
    [Same-Univ] Epoch  8/10: Loss=0.0125, Acc=98.1%, Tension=0.0607, tau=0.6668
    [Same-Univ] Epoch 10/10: Loss=0.0098, Acc=98.1%, Tension=0.0607, tau=0.6571
    >>> Same-universe: Acc=98.1%, Tension=0.0602, tau=0.6571

──────────────────────────────────────────────────────────────────────
[6] EXPERIMENT B: Cross-Universe Repulsion (MNIST native + CIFAR alien)
    Native pole: MNIST. Alien pole: CIFAR. Evaluated on MNIST.
──────────────────────────────────────────────────────────────────────
    [Cross-MNIST] Epoch  1/10: Loss=0.6085, Acc=97.2%, Tension=0.8646, tau=0.1258
    [Cross-MNIST] Epoch  2/10: Loss=0.0898, Acc=97.6%, Tension=0.8649, tau=0.0725
    [Cross-MNIST] Epoch  4/10: Loss=0.0355, Acc=97.9%, Tension=0.8652, tau=0.0426
    [Cross-MNIST] Epoch  6/10: Loss=0.0239, Acc=97.9%, Tension=0.8664, tau=0.0256
    [Cross-MNIST] Epoch  8/10: Loss=0.0185, Acc=97.9%, Tension=0.8676, tau=0.0207
    [Cross-MNIST] Epoch 10/10: Loss=0.0153, Acc=97.9%, Tension=0.8643, tau=0.0111
    >>> Cross-universe (MNIST): Acc=97.9%, Tension=0.8677, tau=0.0111

──────────────────────────────────────────────────────────────────────
[7] EXPERIMENT C: Cross-Universe Repulsion (CIFAR native + MNIST alien)
    Native pole: CIFAR. Alien pole: MNIST. Evaluated on CIFAR.
──────────────────────────────────────────────────────────────────────
    [Cross-CIFAR] Epoch  1/10: Loss=1.3969, Acc=51.9%, Tension=0.8664, tau=0.0766
    [Cross-CIFAR] Epoch  2/10: Loss=0.9038, Acc=53.8%, Tension=0.8658, tau=0.0218
    [Cross-CIFAR] Epoch  4/10: Loss=0.7673, Acc=54.1%, Tension=0.8674, tau=-0.0052
    [Cross-CIFAR] Epoch  6/10: Loss=0.7466, Acc=54.1%, Tension=0.8665, tau=0.0031
    [Cross-CIFAR] Epoch  8/10: Loss=0.7375, Acc=53.8%, Tension=0.8655, tau=-0.0056
    [Cross-CIFAR] Epoch 10/10: Loss=0.7319, Acc=54.1%, Tension=0.8666, tau=0.0023
    >>> Cross-universe (CIFAR): Acc=54.1%, Tension=0.8660, tau=0.0023

──────────────────────────────────────────────────────────────────────
[8] PER-CLASS TENSION ANALYSIS (on MNIST)
──────────────────────────────────────────────────────────────────────

    Per-class tension (MNIST digits):
     Digit │    Same-Univ │   Cross-Univ │        Delta
    ───────┼──────────────┼──────────────┼─────────────
         0 │       0.8671 │       0.8703 │      +0.0033
         1 │       0.8184 │       1.0359 │      +0.2175 <<<
         2 │       0.8162 │       0.8300 │      +0.0138
         3 │       0.7503 │       0.7805 │      +0.0303
         4 │       0.8603 │       0.8736 │      +0.0132
         5 │       0.8423 │       0.8352 │      -0.0071
         6 │       0.9386 │       0.9093 │      -0.0293
         7 │       0.7248 │       0.8434 │      +0.1187 <<<
         8 │       0.7400 │       0.8536 │      +0.1136 <<<
         9 │       0.7489 │       0.8021 │      +0.0532

======================================================================
  CROSS-UNIVERSE REPULSION — RESULTS SUMMARY
======================================================================

  ACCURACY COMPARISON
  ───────────────────────────────────────────────────────────────────────────
  Pole M alone (MNIST) │ ████████████████████████████████████████████████   0.9795
  Same-Univ field (MNIST) │ █████████████████████████████████████████████████  0.9810
  Cross-Univ field (MNIST) │ ████████████████████████████████████████████████   0.9793
  Pole C alone (CIFAR) │ ██████████████████████████                         0.5391
  Cross-Univ field (CIFAR) │ ███████████████████████████                        0.5408


  TENSION COMPARISON (higher = more repulsion)
  ─────────────────────────────────────────────────────────────────
  Same-Universe │ ██                                       0.0602
  Cross-Univ(MNIST) │ ████████████████████████████████████████ 0.8677
  Cross-Univ(CIFAR) │ ███████████████████████████████████████  0.8660


  LEARNED TENSION SCALE (tau) — how much the field uses the alien signal
  ─────────────────────────────────────────────────────────────────
  Same-Universe │ ████████████████████████████████████████ 0.6571
  Cross-Univ(MNIST) │                                          0.0111
  Cross-Univ(CIFAR) │                                          0.0023

  KEY FINDINGS
  ──────────────────────────────────────────────────

  Q1: Does cross-universe tension exist?
      YES. Cross-universe tension = 0.8677

  Q2: Is cross-universe tension higher than same-universe?
      HIGHER. Cross/Same ratio = 14.42x
      Alien models create MORE repulsion.

  Q3: Can an alien model contribute to classification?
      MNIST: pole alone = 98.0%, with alien = 97.9% (delta = -0.0%)
      CIFAR: pole alone = 53.9%, with alien = 54.1% (delta = +0.2%)
      The alien is roughly NEUTRAL on MNIST.

  Q4: What did the field_transform learn?
      Same-universe tau:  0.6571 (started at 0.3333)
      Cross-universe tau: 0.0111 (MNIST), 0.0023 (CIFAR)
      Field SUPPRESSES alien signal (tau shrank).
      The field learned to ignore the entity from another dimension.

  TENSION LANDSCAPE (Same vs Cross Universe)
  ────────────────────────────────────────────────────
  Same-Univ    │██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ 0.0602
  Cross(MNIST) │████████████████████████████████████████│ 0.8677
  Cross(CIFAR) │███████████████████████████████████████░│ 0.8660

  Parameter counts:
    Encoder M: 233,856
    Encoder C: 819,584
    Pole:      1,290
    Field:     631

======================================================================
  EXPERIMENT COMPLETE
======================================================================