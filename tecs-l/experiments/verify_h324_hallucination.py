#!/usr/bin/env python3
"""Hypothesis 324 verification: LLM hallucination detection — head group tension in toy transformer

Method:
1. Train small transformer (2-layer, 4-head) on simple fact data
2. Split attention heads into A/G groups
3. Measure head group tension difference between true vs false sentences
4. Calculate AUROC
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math

np.random.seed(42)
torch.manual_seed(42)

print("=" * 70)
print("Hypothesis 324 Verification: LLM Hallucination Detection — Toy Transformer Head Tension")
print("=" * 70)

# ─────────────────────────────────────────
# 1. Toy Transformer Implementation
# ─────────────────────────────────────────

class ToyMultiHeadAttention(nn.Module):
    """4-head attention with per-head output extraction."""
    def __init__(self, d_model=64, n_heads=4):
        super().__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads

        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)

    def forward(self, x, return_per_head=False):
        B, T, D = x.shape
        Q = self.W_q(x).view(B, T, self.n_heads, self.d_k).transpose(1, 2)
        K = self.W_k(x).view(B, T, self.n_heads, self.d_k).transpose(1, 2)
        V = self.W_v(x).view(B, T, self.n_heads, self.d_k).transpose(1, 2)

        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)
        attn = F.softmax(scores, dim=-1)
        context = torch.matmul(attn, V)  # (B, n_heads, T, d_k)

        if return_per_head:
            # Return per-head outputs before combining
            per_head = context  # (B, n_heads, T, d_k)
            combined = context.transpose(1, 2).contiguous().view(B, T, D)
            return self.W_o(combined), per_head

        combined = context.transpose(1, 2).contiguous().view(B, T, D)
        return self.W_o(combined), None


class ToyTransformer(nn.Module):
    """2-layer transformer for sequence classification."""
    def __init__(self, vocab_size=100, d_model=64, n_heads=4, n_classes=2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_enc = nn.Parameter(torch.randn(1, 32, d_model) * 0.02)
        self.attn1 = ToyMultiHeadAttention(d_model, n_heads)
        self.ff1 = nn.Sequential(nn.Linear(d_model, 128), nn.ReLU(), nn.Linear(128, d_model))
        self.attn2 = ToyMultiHeadAttention(d_model, n_heads)
        self.ff2 = nn.Sequential(nn.Linear(d_model, 128), nn.ReLU(), nn.Linear(128, d_model))
        self.classifier = nn.Linear(d_model, n_classes)
        self.n_heads = n_heads

    def forward(self, x, return_tension=False):
        B, T = x.shape
        h = self.embedding(x) + self.pos_enc[:, :T, :]

        h1, _ = self.attn1(h)
        h = h + h1
        h = h + self.ff1(h)

        h2, per_head = self.attn2(h, return_per_head=True)
        h = h + h2
        h = h + self.ff2(h)

        # Pool: mean over sequence
        pooled = h.mean(dim=1)  # (B, d_model)
        logits = self.classifier(pooled)

        if return_tension and per_head is not None:
            # Split heads into A group (0,1) and G group (2,3)
            head_A = per_head[:, :self.n_heads//2, :, :]  # (B, 2, T, d_k)
            head_G = per_head[:, self.n_heads//2:, :, :]  # (B, 2, T, d_k)

            # Mean over heads in each group, then over sequence
            mean_A = head_A.mean(dim=1).mean(dim=1)  # (B, d_k)
            mean_G = head_G.mean(dim=1).mean(dim=1)  # (B, d_k)

            # Tension = ||A - G||^2 / d_k
            tension = ((mean_A - mean_G) ** 2).mean(dim=-1)  # (B,)
            return logits, tension

        return logits, None


# ─────────────────────────────────────────
# 2. True/False Dataset Generation
# ─────────────────────────────────────────

print("\n" + "─" * 70)
print("1. Toy True/False Dataset Generation")
print("─" * 70)

vocab_size = 100
seq_len = 16
n_train = 2000
n_test = 500

# Pattern-based true/false generation
# "True": Specific token patterns are consistent (A→B, C→D etc)
# "False": Patterns are violated (A→D, C→B etc)

# Rule: token i*10 followed by token i*10+1 is true, i*10+5 is false
def generate_data(n_samples):
    data = []
    labels = []
    for _ in range(n_samples):
        seq = np.random.randint(0, vocab_size, size=seq_len)
        is_true = np.random.random() > 0.5

        # Insert rules at 3~5 positions
        n_rules = np.random.randint(3, 6)
        positions = np.random.choice(seq_len - 1, size=min(n_rules, seq_len - 1), replace=False)

        for pos in positions:
            base = np.random.randint(0, 9) * 10  # 0, 10, 20, ..., 80
            seq[pos] = base
            if is_true:
                seq[pos + 1] = base + 1  # Rule compliant
            else:
                seq[pos + 1] = base + 5  # Rule violation

        data.append(seq)
        labels.append(1 if is_true else 0)

    return torch.tensor(np.array(data), dtype=torch.long), torch.tensor(labels, dtype=torch.long)

train_x, train_y = generate_data(n_train)
test_x, test_y = generate_data(n_test)

print(f"  Train: {n_train} (true: {(train_y==1).sum().item()}, false: {(train_y==0).sum().item()})")
print(f"  Test: {n_test} (true: {(test_y==1).sum().item()}, false: {(test_y==0).sum().item()})")

# ─────────────────────────────────────────
# 3. Model Training
# ─────────────────────────────────────────

print("\n" + "─" * 70)
print("2. Toy Transformer Training")
print("─" * 70)

model = ToyTransformer(vocab_size=vocab_size, d_model=64, n_heads=4, n_classes=2)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
criterion = nn.CrossEntropyLoss()

batch_size = 64
n_epochs = 30

for epoch in range(n_epochs):
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    indices = torch.randperm(n_train)
    for i in range(0, n_train, batch_size):
        idx = indices[i:i+batch_size]
        x_batch = train_x[idx]
        y_batch = train_y[idx]

        logits, _ = model(x_batch)
        loss = criterion(logits, y_batch)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * len(idx)
        correct += (logits.argmax(dim=-1) == y_batch).sum().item()
        total += len(idx)

    if (epoch + 1) % 10 == 0:
        acc = correct / total * 100
        print(f"  Epoch {epoch+1:3d}: loss={total_loss/total:.4f}, acc={acc:.1f}%")

# Test accuracy
model.eval()
with torch.no_grad():
    logits, _ = model(test_x)
    test_acc = (logits.argmax(dim=-1) == test_y).float().mean().item() * 100
    print(f"\n  Test accuracy: {test_acc:.1f}%")

# ─────────────────────────────────────────
# 4. Head Group Tension Measurement
# ─────────────────────────────────────────

print("\n" + "─" * 70)
print("3. Head Group Tension Measurement")
print("─" * 70)

model.eval()
with torch.no_grad():
    _, tensions = model(test_x, return_tension=True)

tensions_np = tensions.numpy()
labels_np = test_y.numpy()

true_tensions = tensions_np[labels_np == 1]
false_tensions = tensions_np[labels_np == 0]

print(f"\n  True sentence tension: mean={np.mean(true_tensions):.6f} +/- {np.std(true_tensions):.6f}")
print(f"  False sentence tension: mean={np.mean(false_tensions):.6f} +/- {np.std(false_tensions):.6f}")
print(f"  Ratio (true/false):  {np.mean(true_tensions)/(np.mean(false_tensions)+1e-10):.3f}")

# Cohen's d
pooled_std = np.sqrt((np.var(true_tensions) + np.var(false_tensions)) / 2)
cohen_d = (np.mean(true_tensions) - np.mean(false_tensions)) / (pooled_std + 1e-10)
print(f"  Cohen's d:         {cohen_d:+.3f}")

# ─────────────────────────────────────────
# 5. AUROC Calculation (distinguish true/false with tension)
# ─────────────────────────────────────────

print("\n" + "─" * 70)
print("4. AUROC — Hallucination (false) detection with tension")
print("─" * 70)

# Simple AUROC calculation
def compute_auroc(scores, labels):
    """AUROC: higher scores mean positive(1)."""
    sorted_idx = np.argsort(-scores)
    sorted_labels = labels[sorted_idx]

    tp = 0
    fp = 0
    n_pos = np.sum(labels == 1)
    n_neg = np.sum(labels == 0)

    tpr_list = [0]
    fpr_list = [0]

    for label in sorted_labels:
        if label == 1:
            tp += 1
        else:
            fp += 1
        tpr_list.append(tp / max(n_pos, 1))
        fpr_list.append(fp / max(n_neg, 1))

    # Trapezoidal rule
    auroc = 0
    for i in range(1, len(fpr_list)):
        auroc += (fpr_list[i] - fpr_list[i-1]) * (tpr_list[i] + tpr_list[i-1]) / 2

    return auroc, tpr_list, fpr_list

# Hypothesis: high tension = true (real knowledge), low tension = false (hallucination)
auroc_high, tpr1, fpr1 = compute_auroc(tensions_np, labels_np)
# Test opposite direction too
auroc_low, tpr2, fpr2 = compute_auroc(-tensions_np, labels_np)

best_auroc = max(auroc_high, auroc_low)
direction = "high tension = true" if auroc_high >= auroc_low else "low tension = true"

print(f"\n  AUROC (high tension → true): {auroc_high:.4f}")
print(f"  AUROC (low tension → true): {auroc_low:.4f}")
print(f"  Best direction: {direction}")
print(f"  Best AUROC: {best_auroc:.4f}")

# ─────────────────────────────────────────
# 6. Correct/Wrong Answer Tension Analysis
# ─────────────────────────────────────────

print("\n" + "─" * 70)
print("5. Correct/Wrong answer tension (H313 reproduction)")
print("─" * 70)

with torch.no_grad():
    logits, tensions_all = model(test_x, return_tension=True)
    preds = logits.argmax(dim=-1).numpy()

correct_mask = preds == labels_np
wrong_mask = ~correct_mask

correct_tensions = tensions_np[correct_mask]
wrong_tensions = tensions_np[wrong_mask]

print(f"\n  Correct answer tension: mean={np.mean(correct_tensions):.6f} +/- {np.std(correct_tensions):.6f} (n={len(correct_tensions)})")
if len(wrong_tensions) > 0:
    print(f"  Wrong answer tension: mean={np.mean(wrong_tensions):.6f} +/- {np.std(wrong_tensions):.6f} (n={len(wrong_tensions)})")
    ratio_cw = np.mean(correct_tensions) / (np.mean(wrong_tensions) + 1e-10)
    print(f"  Ratio (correct/wrong): {ratio_cw:.3f}")
else:
    print(f"  Wrong answer: None (all correct)")
    ratio_cw = float('inf')

# ─────────────────────────────────────────
# 7. Rejection Mechanism Test (H314)
# ─────────────────────────────────────────

print("\n" + "─" * 70)
print("6. Rejection Mechanism (H314) — Accuracy when rejecting low tension")
print("─" * 70)

reject_ratios = [0.05, 0.10, 0.20, 0.30, 0.50, 0.70, 0.90]

print(f"\n  {'Reject %':>8} | {'Remain':>6} | {'Accuracy':>8} | {'Improve':>8} | Bar")
print(f"  {'─'*8}─┼─{'─'*6}─┼─{'─'*8}─┼─{'─'*8}─┼─{'─'*30}")

base_acc = np.mean(correct_mask) * 100

for ratio in reject_ratios:
    threshold = np.percentile(tensions_np, ratio * 100)
    keep_mask = tensions_np >= threshold
    if np.sum(keep_mask) == 0:
        continue
    kept_correct = np.sum(correct_mask[keep_mask])
    kept_total = np.sum(keep_mask)
    kept_acc = kept_correct / kept_total * 100
    improvement = kept_acc - base_acc

    bar_len = int(max(0, improvement) * 5)
    bar = "#" * min(bar_len, 30)
    print(f"  {ratio:>7.0%} | {kept_total:>6d} | {kept_acc:>7.1f}% | {improvement:>+7.2f}% | {bar}")

# ─────────────────────────────────────────
# 8. ASCII Graph: Tension Distribution
# ─────────────────────────────────────────

print("\n" + "─" * 70)
print("7. Tension Distribution (True vs False)")
print("─" * 70)

all_min = min(tensions_np.min(), 0)
all_max = tensions_np.max()
n_bins = 20
bin_edges = np.linspace(all_min, all_max, n_bins + 1)

true_hist, _ = np.histogram(true_tensions, bins=bin_edges)
false_hist, _ = np.histogram(false_tensions, bins=bin_edges)

max_count = max(true_hist.max(), false_hist.max())

print(f"\n  True(T) vs False(F) tension distribution:")
print(f"  {'bin':>12} | T  F")
for i in range(n_bins):
    lo, hi = bin_edges[i], bin_edges[i+1]
    t_bar = "#" * int(true_hist[i] / max(max_count, 1) * 25)
    f_bar = "." * int(false_hist[i] / max(max_count, 1) * 25)
    print(f"  {lo:>5.4f}-{hi:<5.4f} | {t_bar}")
    if f_bar:
        print(f"  {'':>12} | {f_bar}")

# ─────────────────────────────────────────
# 9. Conclusion
# ─────────────────────────────────────────

print("\n" + "=" * 70)
print("Conclusion")
print("=" * 70)

print(f"\n  Model accuracy:     {test_acc:.1f}%")
print(f"  True/False tension difference: Cohen's d = {cohen_d:+.3f}")
print(f"  Hallucination detection AUROC: {best_auroc:.4f}")
print(f"  Direction:            {direction}")

if best_auroc > 0.80:
    verdict = "Strong support — hallucination detection with head tension is practical"
elif best_auroc > 0.65:
    verdict = "Weak support — signal exists but insufficient for standalone detection"
elif best_auroc > 0.55:
    verdict = "Very weak signal — structure exists but nearly random level"
else:
    verdict = "Not supported — random level"

print(f"  Verdict: {verdict}")
print(f"\n  H313 reproduction (correct vs wrong):")
print(f"    Correct tension > Wrong tension? {'Yes' if ratio_cw > 1 else 'No'} (ratio={ratio_cw:.3f})")
print(f"\n  H314 reproduction (rejection → accuracy):")
print(f"    Accuracy improvement at 10% rejection? See table above")

print(f"\n  ⚠️ Limitations:")
print(f"    - Toy model (64-dim, 4-head) → Scale difference from real LLMs")
print(f"    - Pattern-based synthetic data → Different from real facts/hallucinations")
print(f"    - Arbitrary head split (head 0,1 vs 2,3)")
print(f"    - Real verification requires real LLM + TruthfulQA")
print("=" * 70)