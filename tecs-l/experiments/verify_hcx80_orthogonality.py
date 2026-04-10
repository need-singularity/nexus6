#!/usr/bin/env python3
"""H-CX-80: Orthogonality -> Synergy
Prediction: corr(expert_orthogonality, synergy_gain) > 0.8
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/TECS-L')

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from model_pure_field import PureFieldEngine
from model_utils import load_mnist


def train_purefield(model, train_loader, epochs=5, lr=0.001):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            output, tension = model(X)
            loss = criterion(output, y) + 0.1 * tension.mean()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"  Epoch {epoch+1}/{epochs}: loss={total_loss/len(train_loader):.4f}")


print("=== H-CX-80: Orthogonality -> Synergy ===")
train_loader, test_loader = load_mnist(batch_size=128)
model = PureFieldEngine(784, 128, 10)
train_purefield(model, train_loader, epochs=5)

# Evaluate per-class
model.eval()
class_out_a = {c: [] for c in range(10)}
class_out_g = {c: [] for c in range(10)}
class_combined = {c: [] for c in range(10)}

with torch.no_grad():
    for X, y in test_loader:
        X = X.view(X.size(0), -1)
        out_a = model.engine_a(X)
        out_g = model.engine_g(X)
        combined = out_a - out_g
        for c in range(10):
            mask = (y == c)
            if mask.sum() > 0:
                class_out_a[c].append(out_a[mask])
                class_out_g[c].append(out_g[mask])
                class_combined[c].append(combined[mask])

class_ortho = []
class_synergy = []

for c in range(10):
    a_mean = torch.cat(class_out_a[c]).mean(dim=0)
    g_mean = torch.cat(class_out_g[c]).mean(dim=0)
    comb = torch.cat(class_combined[c])

    cos_sim = F.cosine_similarity(a_mean.unsqueeze(0), g_mean.unsqueeze(0)).item()
    ortho = 1.0 - abs(cos_sim)

    combined_correct = (comb.argmax(dim=1) == c).float().mean().item()
    a_correct = (torch.cat(class_out_a[c]).argmax(dim=1) == c).float().mean().item()
    g_correct = (torch.cat(class_out_g[c]).argmax(dim=1) == c).float().mean().item()
    best_single = max(a_correct, g_correct)
    synergy = combined_correct - best_single

    class_ortho.append(ortho)
    class_synergy.append(synergy)
    print(f"  Class {c}: ortho={ortho:.4f}, synergy={synergy:.4f}")

corr = np.corrcoef(class_ortho, class_synergy)[0, 1]
print(f"\nCorrelation(orthogonality, synergy) = {corr:.4f}")
print(f"Prediction: > 0.8")
print(f"Verdict: {'PASS' if corr > 0.8 else 'FAIL'}")
