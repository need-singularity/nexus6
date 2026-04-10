======================================================================
  C4 Individual Sample Verification
  Tension-Accuracy Correlation: Per-Digit vs Per-Sample
======================================================================

[1/5] Loading MNIST...

[2/5] Training RepulsionFieldQuad (10 epochs)...
  Parameters: 972,516
  Epoch  1/10: Loss=0.3133, TrainAcc=90.9%
  Epoch  2/10: Loss=0.1508, TrainAcc=95.6%
  Epoch  3/10: Loss=0.1167, TrainAcc=96.5%
  Epoch  4/10: Loss=0.0991, TrainAcc=97.1%
  Epoch  5/10: Loss=0.0832, TrainAcc=97.4%
  Epoch  6/10: Loss=0.0739, TrainAcc=97.7%
  Epoch  7/10: Loss=0.0652, TrainAcc=97.9%
  Epoch  8/10: Loss=0.0620, TrainAcc=98.1%
  Epoch  9/10: Loss=0.0566, TrainAcc=98.2%
  Epoch 10/10: Loss=0.0520, TrainAcc=98.4%

[3/5] Collecting per-sample tension for 10,000 test samples...
  Total samples: 10000
  Correct: 9760 (97.6%)
  Tension range: [21.2282, 953.9556]
  Tension mean=199.3949, std=92.2540

[4/5] Per-digit analysis (reproducing C4)...

### Per-Digit Summary (C4 original level)
  Digit     N    Acc%   MeanTens    StdTens
  ----- ----- ------- ---------- ----------
      0   980   98.98   190.4143    82.2143
      1  1135   99.56   182.6465    82.9322
      2  1032   96.51   198.3639    98.2158
      3  1010   98.42   217.3298   112.2924
      4   982   97.56   222.9907    84.0781
      5   892   97.20   276.2696   124.2996
      6   958   96.87   191.9387    67.6999
      7  1028   96.89   186.3803    68.7699
      8   974   96.92   151.4812    54.3251
      9  1009   96.83   185.7248    76.7453

  Per-digit correlation (N=10): r = -0.0107
  C4 claimed: r = +0.43

[5/5] Per-sample analysis (ecological fallacy test)...

### Point-Biserial Correlation
  Per-sample (N=10000):  r = +0.1344
  Per-digit  (N=10):     r = -0.0107
  Ratio (sample/digit):  -12.61

### Bootstrap CI (1000 resamples)
  Bootstrap mean: r = +0.1343
  95% CI: [+0.1191, +0.1502]

### Logistic Regression: P(correct) = sigmoid(a + b*tension)
  Intercept (a): +2.6608
  Slope (b):     +0.2074
  Direction:     higher tension -> more correct

### AUC (tension alone predicting correctness)
  AUC = 0.7839
  Interpretation: better than chance
  (0.5 = random, 1.0 = perfect, <0.5 = inverted relationship)

### Cohen's d (effect size)
  Correct samples:   mean=201.3398, std=92.0866, N=9760
  Incorrect samples: mean=120.3007, std=57.9325, N=240
  Cohen's d = +0.8864
  Effect size: large

### Distribution Overlap
  Overlap coefficient = 0.5846
  (1.0 = identical distributions, 0.0 = no overlap)

### Tension Distribution: Correct vs Incorrect
  [CORRECT] N=9760, mean=201.3398, std=92.0866
    21.23-  83.41 | ##### (480)
    83.41- 145.59 | ############################## (2509)
   145.59- 207.77 | ################################### (2865)
   207.77- 269.96 | ######################## (1969)
   269.96- 332.14 | ############# (1068)
   332.14- 394.32 | ###### (492)
   394.32- 456.50 | ## (229)
   456.50- 518.68 |  (76)
   518.68- 580.86 |  (41)
   580.86- 643.05 |  (24)
   643.05- 705.23 |  (4)
   705.23- 767.41 |  (1)
   767.41- 829.59 |  (0)
   829.59- 891.77 |  (1)
   891.77- 953.96 |  (1)

  [INCORRECT] N=240, mean=120.3007, std=57.9325
    21.30-  44.56 | ########## (14)
    44.56-  67.82 | ##################### (30)
    67.82-  91.08 | ########################## (37)
    91.08- 114.34 | ################################### (48)
   114.34- 137.61 | ######################### (35)
   137.61- 160.87 | ################## (25)
   160.87- 184.13 | ############# (18)
   184.13- 207.39 | ########## (14)
   207.39- 230.65 | ##### (7)
   230.65- 253.91 | ### (5)
   253.91- 277.17 | ## (3)
   277.17- 300.44 | # (2)
   300.44- 323.70 |  (1)
   323.70- 346.96 |  (0)
   346.96- 370.22 |  (1)

### Within-Digit Correlations
  (Is tension correlated with correctness WITHIN each digit?)
  Digit     N   r_within   MeanT_corr   MeanT_incorr        d
  ----- ----- ---------- ------------ -------------- --------
      0   980    +0.1133     191.3599        98.6908  +1.1333
      1  1135    +0.0136     182.7213       165.7378  +0.2046
      2  1032    +0.1175     200.5584       137.6500  +0.6444
      3  1010    +0.1230     219.0824       108.4457  +0.9918
      4   982    +0.1233     224.6319       157.4829  +0.8040
      5   892    +0.1971     280.4290       132.0204  +1.2165
      6   958    +0.1835     194.1725       122.8378  +1.0708
      7  1028    +0.2033     188.8860       108.3929  +1.1943
      8   974    +0.1805     153.2291        96.4820  +1.0609
      9  1009    +0.1994     188.4939       101.1807  +1.1599

  Mean within-digit r = +0.1454
  Between-digit r     = -0.0107
  Overall per-sample r = +0.1344

======================================================================
  ECOLOGICAL FALLACY DIAGNOSIS
======================================================================
  Per-digit r (C4 original, N=10):     -0.0107
  Per-sample r (this test, N=10000):  +0.1344
  Bootstrap 95% CI:                     [+0.1191, +0.1502]
  Mean within-digit r:                  +0.1454
  AUC:                                  0.7839
  Cohen's d:                            +0.8864 (large)

  VERDICT:
  -> Direction REVERSED at individual level!
  -> C4 is REVERSED (Simpson's paradox)
  -> Within-digit r = +0.1454 shows GENUINE per-sample effect

  Elapsed: 346.2s
======================================================================