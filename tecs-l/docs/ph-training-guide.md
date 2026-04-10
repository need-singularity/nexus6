# PH-based Model Training Guide

> How to apply PH discoveries to actual model training.

## 1. Before Training: Difficulty Prediction (H-CX-101/160)

```python
# Train 1 epoch → Predict final accuracy with H0_total
model = PureFieldEngine(dim, 128, n_classes)
train_1_epoch(model, train_loader)
h0 = compute_h0(model, test_loader)

# Higher H0 means easier
# MNIST H0≈4.2 → 98%, Fashion H0≈2.3 → 89%, CIFAR H0≈2.1 → 54%
print(f"Expected difficulty: H0={h0:.2f}")
if h0 > 3.5: print("Easy — few epochs sufficient")
elif h0 > 2.0: print("Medium")
else: print("Hard — many epochs/larger model needed")
```

## 2. During Training: Real-time Overfitting Detection (H-CX-95)

```python
from calc.generalization_gap_detector import compute_h0

for epoch in range(max_epochs):
    train(model, train_loader)

    # Every epoch: compare train/test PH
    h0_train = compute_h0(model, train_loader)
    h0_test = compute_h0(model, test_loader)
    h0_gap = abs(h0_train - h0_test)

    if h0_gap > threshold:
        print(f"⚠️ Overfitting detected! (gap={h0_gap:.4f})")
        break  # Early stopping

    # gap detector: CIFAR r=0.998, Fashion r=0.846
```

## 3. Automatic Learning Rate Search (H-CX-100)

```python
# LR with minimum H0 CV (coefficient of variation) = optimal LR
best_lr, best_cv = None, 999

for lr in [1e-4, 3e-4, 1e-3, 3e-3, 1e-2]:
    model = PureFieldEngine(dim, 128, n_classes)
    h0s = []
    for epoch in range(10):
        train_with_lr(model, train_loader, lr)
        h0s.append(compute_h0(model, test_loader))

    cv = np.std(h0s) / np.mean(h0s)
    if cv < best_cv:
        best_cv = cv
        best_lr = lr

print(f"Optimal LR: {best_lr} (H0 CV={best_cv:.4f})")
# In CIFAR, LR with minimum H0 CV = LR with highest accuracy!
```

## 4. Pre-identify Confusion Pairs (H-CX-66/82)

```python
# Perfect confusion pair prediction at epoch 1 (P@5=1.0)
model = PureFieldEngine(dim, 128, n_classes)
train_1_epoch(model, train_loader)
merges = compute_merge_order(model, test_loader)

print("Confusion pairs (determined right after training starts):")
for dist, i, j in sorted(merges)[:5]:
    print(f"  {class_names[i]} ↔ {class_names[j]}: d={dist:.4f}")

# → Focus training on these pairs? (H-CX-87: no effect!)
# → Instead: check data quality for these pairs, verify label errors
```

## 5. Predict Adversarial Vulnerabilities (H-CX-104)

```python
# Pairs with short merge distance = vulnerable to FGSM (r=-0.71)
vulnerable_pairs = sorted(merges)[:3]
print("FGSM vulnerable pairs:")
for dist, i, j in vulnerable_pairs:
    print(f"  {class_names[i]}-{class_names[j]}: high attack success rate")

# → Prioritize these pairs in adversarial training
```

## 6. Architecture Selection (H-CX-88/107)

```python
# PH is invariant to architecture (top-5 100%)
# → Architecture choice doesn't affect PH
# → Instead: choose based on parameter efficiency

# hidden_dim 64/128/256 → same PH (tau=0.83~0.94)
# → Can analyze PH with small model, then apply to large model!
```

## 7. Multi-task Learning (Mitosis/Classification)

```python
# PH dendrogram = semantic hierarchy (89% purity)
# → Task decomposition based on dendrogram

dendrogram = compute_dendrogram(model, test_loader)
# CIFAR: {cat,dog}→animals, {auto,truck}→machines

# Learn upper classification (animals vs machines) first
# → Then lower classification (cat vs dog)
# = PH version of curriculum learning
```

## 8. When Training ConsciousLM (LLM)

```python
# Applying PH to byte-level LLM:
# 256 bytes → 13 groups (lower, upper, digit, korean, ...)
# Group direction vectors → PH computation

# Monitoring:
# - H0_gap: overfitting detection
# - merge order: which byte groups are confused
# - dendrogram: topological hierarchy of language structure

# ⚠️ H-CX-95 not verified for LLM — need to retry with lightweight version
```

## Summary: PH Training Checklist

```
  Before training:
  □ 1-epoch H0_total → difficulty prediction
  □ merge order → identify confusion pairs
  □ H0 CV sweep → optimal LR

  During training:
  □ per-epoch H0_gap → overfitting detection
  □ H0 trend → monitor training progress
  □ merge stability → judge convergence

  After training:
  □ dendrogram → confirm semantic hierarchy
  □ confusion PCA → understand data structure
  □ vulnerable pairs → adversarial defense priority
```

## Related Tools

```
  calc/ph_confusion_analyzer.py     — integrated PH analysis
  calc/generalization_gap_detector.py — overfitting detection
  calc/precognition_system.py       — 3-channel precognition
  ph_module.py (anima)              — real-time PH
```

## Related Hypotheses

| Hypothesis | Application | Effect |
|------|------|------|
| H-CX-95 | Overfitting detection | r=0.998 |
| H-CX-100 | LR search | H0 CV minimum=optimal |
| H-CX-101 | Difficulty prediction | H0_ep1 vs acc r>0.9 |
| H-CX-66 | Confusion prediction | r=-0.97 |
| H-CX-82 | Epoch 1 prediction | P@5=1.0 |
| H-CX-104 | FGSM vulnerability | r=-0.71 |
| H-CX-102 | PH regularization | +0.5% (CIFAR) |