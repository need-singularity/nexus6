======================================================================
   MITOSIS EXPERIMENT
   One engine splits into two, diversity emerges
======================================================================

======================================================================
  PHASE 1: Train Parent (EngineA, 5 epochs)
======================================================================
  Parameters: 467,460
    Epoch 1/5: Loss=0.3702, Acc=94.5%
    Epoch 2/5: Loss=0.1991, Acc=95.7%
    Epoch 3/5: Loss=0.1659, Acc=96.4%
    Epoch 4/5: Loss=0.1455, Acc=96.2%
    Epoch 5/5: Loss=0.1329, Acc=96.7%

  Parent final accuracy: 96.67%

======================================================================
  PHASE 2: Mitosis — Split + Mutation
======================================================================

  Mutation scale = 0.001
    Cosine similarity:  0.999735
    Tension at birth:   0.0184
    Child A accuracy:   96.67%
    Child B accuracy:   96.64%
    Acc drop (child B): 0.03%

  Mutation scale = 0.01
    Cosine similarity:  0.972392
    Tension at birth:   1.8674
    Child A accuracy:   96.67%
    Child B accuracy:   96.59%
    Acc drop (child B): 0.08%

  Mutation scale = 0.1
    Cosine similarity:  0.375403
    Tension at birth:   143.1483
    Child A accuracy:   96.67%
    Child B accuracy:   76.82%
    Acc drop (child B): 19.85%

  Phase 2 Summary: Mitosis
  | Mutation | Cos Sim  | Tension  | Acc A% | Acc B% | B Drop% |
  |----------|----------|----------|--------|--------|---------|
  | 0.001    | 0.999735 | 0.0184   | 96.7   | 96.6   | 0.0     |
  | 0.01     | 0.972392 | 1.8674   | 96.7   | 96.6   | 0.1     |
  | 0.1      | 0.375403 | 143.1483 | 96.7   | 76.8   | 19.9    |

======================================================================
  PHASE 3: Divergence — Independent Training (10 epochs)
  Using mutation_scale=0.01
======================================================================
    Epoch  1/10: CosSim=0.9293  Tension=25.61  AccA=96.7%  AccB=96.9%
    Epoch  2/10: CosSim=0.8996  Tension=93.72  AccA=97.1%  AccB=97.0%
    Epoch  3/10: CosSim=0.8744  Tension=63.46  AccA=96.9%  AccB=97.1%
    Epoch  4/10: CosSim=0.8630  Tension=72.99  AccA=97.2%  AccB=97.0%
    Epoch  5/10: CosSim=0.8588  Tension=54.81  AccA=97.2%  AccB=96.9%
    Epoch  6/10: CosSim=0.8531  Tension=93.43  AccA=97.0%  AccB=97.3%
    Epoch  7/10: CosSim=0.8492  Tension=116.74  AccA=97.1%  AccB=97.4%
    Epoch  8/10: CosSim=0.8452  Tension=139.14  AccA=97.2%  AccB=97.5%
    Epoch  9/10: CosSim=0.8419  Tension=118.62  AccA=97.5%  AccB=97.2%
    Epoch 10/10: CosSim=0.8398  Tension=135.41  AccA=97.2%  AccB=97.3%

  Phase 3 Summary: Divergence Curve
  | Epoch | Cos Sim | Tension | Acc A% | Acc B% |
  |-------|---------|---------|--------|--------|
  | 1     | 0.9293  | 25.61   | 96.7   | 96.9   |
  | 2     | 0.8996  | 93.72   | 97.1   | 97.0   |
  | 3     | 0.8744  | 63.46   | 96.9   | 97.1   |
  | 4     | 0.8630  | 72.99   | 97.2   | 97.0   |
  | 5     | 0.8588  | 54.81   | 97.2   | 96.9   |
  | 6     | 0.8531  | 93.43   | 97.0   | 97.3   |
  | 7     | 0.8492  | 116.74  | 97.1   | 97.4   |
  | 8     | 0.8452  | 139.14  | 97.2   | 97.5   |
  | 9     | 0.8419  | 118.62  | 97.5   | 97.2   |
  | 10    | 0.8398  | 135.41  | 97.2   | 97.3   |

  Cosine Similarity Decay (params)
         |
  0.9293 |#         
  0.9194 |#         
  0.9094 |#         
  0.8995 |##        
  0.8896 |##        
  0.8796 |##        
  0.8697 |###       
  0.8597 |####      
  0.8498 |######    
  0.8398 |##########
         +----------
          0123456789

  Tension Growth
         |
   139.1 |       #  
   126.5 |       # #
   113.9 |      ####
   101.3 |      ####
    88.7 | #   #####
    76.1 | #   #####
    63.5 | ### #####
    50.8 | #########
    38.2 | #########
    25.6 |##########
         +----------
          0123456789

  Child A Accuracy
         |
  0.9747 |        # 
  0.9738 |        # 
  0.9730 |        # 
  0.9721 |       ## 
  0.9713 |   ##  ###
  0.9704 | # ## ####
  0.9696 | # #######
  0.9687 | #########
  0.9679 | #########
  0.9670 |##########
         +----------
          0123456789

  Child B Accuracy
         |
  0.9755 |       #  
  0.9748 |       #  
  0.9741 |       #  
  0.9734 |      ##  
  0.9727 |     ### #
  0.9720 |     #####
  0.9713 |     #####
  0.9706 |  #  #####
  0.9699 | ### #####
  0.9692 |##########
         +----------
          0123456789

======================================================================
  PHASE 4: Repulsion Field from Split Children
======================================================================
  Trainable field params: 111
    Field Epoch 1/5: Loss=0.0406, Acc=97.5%
    Field Epoch 2/5: Loss=0.0407, Acc=97.5%
    Field Epoch 3/5: Loss=0.0408, Acc=97.5%
    Field Epoch 4/5: Loss=0.0412, Acc=97.5%
    Field Epoch 5/5: Loss=0.0393, Acc=97.5%

  Training Designed RepulsionField (A vs G, 20 epochs)...
    Epoch  1/20: Loss=0.3325, Acc=94.6%
    Epoch  2/20: Loss=0.1664, Acc=95.9%
    Epoch  4/20: Loss=0.1139, Acc=96.7%
    Epoch  6/20: Loss=0.0918, Acc=97.2%
    Epoch  8/20: Loss=0.0777, Acc=97.3%
    Epoch 10/20: Loss=0.0653, Acc=97.6%
    Epoch 12/20: Loss=0.0594, Acc=97.6%
    Epoch 14/20: Loss=0.0526, Acc=97.3%
    Epoch 16/20: Loss=0.0479, Acc=97.6%
    Epoch 18/20: Loss=0.0413, Acc=97.4%
    Epoch 20/20: Loss=0.0423, Acc=97.6%

  Phase 4 Summary: Split Field vs Designed Field
  |      Model      | Accuracy% |          Note           |
  |-----------------|-----------|-------------------------|
  | Parent (5 ep)   | 96.67     | Before split            |
  | Child A (15 ep) | 97.18     | After divergence        |
  | Child B (15 ep) | 97.30     | After divergence        |
  | Split Field     | 97.49     | Children frozen + field |
  | Designed Field  | 97.60     | A vs G, 20 epochs       |

======================================================================
  PHASE 5: Reunion — Average Weights
======================================================================
  Parent accuracy:    96.67%
  Child A accuracy:   97.18%
  Child B accuracy:   97.30%
  Merged accuracy:    97.49%
  Merged vs Parent:   +0.82%
  Merged vs Best:     +0.19%
  --> Reunion IMPROVES on parent!

======================================================================
  PHASE 6: Multiple Splits (2, 4, 8 children)
======================================================================

  N=2 splits:
    Individual: 97.1% / 97.1%
    Best single:    97.14%
    Majority vote:  97.00%
    Soft ensemble:  97.41%
    Vote vs Best:   -0.14%

  N=4 splits:
    Individual: 97.1% / 97.2% / 97.2% / 97.2%
    Best single:    97.24%
    Majority vote:  97.31%
    Soft ensemble:  97.52%
    Vote vs Best:   +0.07%

  N=8 splits:
    Individual: 97.1% / 97.3% / 97.2% / 97.1% / 97.2% / 97.1% / 97.2% / 97.2%
    Best single:    97.28%
    Majority vote:  97.46%
    Soft ensemble:  97.52%
    Vote vs Best:   +0.18%

  Phase 6 Summary: Multiple Splits
  | N Splits | Best Single% | Vote% | Ensemble% | Vote-Best% |
  |----------|--------------|-------|-----------|------------|
  | 2        | 97.1         | 97.0  | 97.4      | -0.1       |
  | 4        | 97.2         | 97.3  | 97.5      | +0.1       |
  | 8        | 97.3         | 97.5  | 97.5      | +0.2       |

  Accuracy vs Strategy:
            N=4ens |################################################ 97.5%
            N=8ens |################################################ 97.5%
           N=8vote |################################################ 97.5%
            N=2ens |################################################ 97.4%
           N=4vote |################################################ 97.3%
           N=2vote |################################################ 97.0%
            Parent |################################################ 96.7%

======================================================================
  PHASE 7: Recognition — Can Child A Predict Child B's Output?
======================================================================
  Training stranger engine (EngineG, 15 epochs)...
  Stranger accuracy: 97.3%

  Training predictor: Child A -> Child B (former self)...
    Final MSE: 11.158943
  Training predictor: Child A -> Stranger (EngineG)...
    Final MSE: 18.457300
  Random baseline MSE: 100.386780

  Recognition ratio (stranger/sibling MSE): 1.65x
  Sibling recognition MSE:  11.158943
  Stranger recognition MSE: 18.457300
  --> Child A recognizes Child B as 'former self' (much easier to predict)

  Sibling R^2:  0.8888 (88.9%)
  Stranger R^2: 0.8161 (81.6%)
  Cross-dim recognition (C8 benchmark): 94.3%

  Sibling Prediction Loss (A->B)
         |
   172.5 |#                   
   154.6 |#                   
   136.7 |#                   
   118.8 |##                  
   100.9 |###                 
    83.0 |###                 
    65.1 |####                
    47.2 |#####               
    29.3 |########            
    11.4 |####################
         +--------------------
          01234567890123456789

  Stranger Prediction Loss (A->Stranger)
         |
   106.2 |#                   
    96.5 |#                   
    86.8 |#                   
    77.0 |##                  
    67.3 |##                  
    57.6 |###                 
    47.8 |####                
    38.1 |#####               
    28.4 |#######             
    18.6 |####################
         +--------------------
          01234567890123456789

======================================================================
  FINAL SUMMARY: MITOSIS EXPERIMENT
======================================================================

  Phase 1 - Parent:           96.67% (5 epochs)
  Phase 2 - Mutation effect:  scale=0.01 -> cos_sim=0.9724
  Phase 3 - After divergence: A=97.2%, B=97.3%
            Cos similarity:   0.8398 (was ~1.0)
            Tension growth:   25.61 -> 135.41
  Phase 4 - Split field:      97.49%
            Designed field:   97.60%
            Split vs Design:  -0.11%
  Phase 5 - Reunion (avg):    97.49%
            vs Parent:        +0.82%
  Phase 6 - Multi-split best: N=8 ensemble=97.5%
  Phase 7 - Recognition:      sibling=88.9% vs stranger=81.6%
            Ratio:            1.65x

  KEY INSIGHTS:
  --------------------------------------------------
  [ ] Designed field still better than split field
      -> Different architectures create richer tension
  [!] Reunion improves on parent
      -> Divergence found complementary features
  [!] Strong sibling recognition
      -> Shared origin leaves lasting structural imprint
  [!] Ensemble > any single child
      -> Mitosis creates genuine diversity

  ==================================================
  Mitosis experiment complete.
  ==================================================
