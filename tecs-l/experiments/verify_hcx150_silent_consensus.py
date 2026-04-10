#!/usr/bin/env python3
"""H-CX-150: Silent Consensus
Prediction: Expert class centroids converge (cosine similarity > 0.5) without explicit consensus.
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


print("=== H-CX-150: Silent Consensus ===")
train_loader, test_loader = load_mnist(batch_size=128)
model = PureFieldEngine(784, 128, 10)
train_purefield(model, train_loader, epochs=5)

model.eval()
a_by_class = {c: [] for c in range(10)}
g_by_class = {c: [] for c in range(10)}

with torch.no_grad():
    for X, y in test_loader:
        X = X.view(X.size(0), -1)
        out_a = model.engine_a(X)
        out_g = model.engine_g(X)
        for c in range(10):
            mask = (y == c)
            if mask.sum() > 0:
                a_by_class[c].append(out_a[mask])
                g_by_class[c].append(out_g[mask])

print("\nPer-class cosine similarity between engine_a and engine_g centroids:")
similarities = []
for c in range(10):
    a_centroid = torch.cat(a_by_class[c]).mean(dim=0)
    g_centroid = torch.cat(g_by_class[c]).mean(dim=0)
    cos_sim = F.cosine_similarity(a_centroid.unsqueeze(0), g_centroid.unsqueeze(0)).item()
    similarities.append(cos_sim)
    print(f"  Class {c}: cos_sim = {cos_sim:.4f}")

mean_sim = np.mean(similarities)
print(f"\nMean cosine similarity: {mean_sim:.4f}")
print(f"Prediction: > 0.5")
print(f"Verdict: {'PASS' if mean_sim > 0.5 else 'FAIL'}")

# Structural agreement
a_centroids = torch.stack([torch.cat(a_by_class[c]).mean(dim=0) for c in range(10)])
g_centroids = torch.stack([torch.cat(g_by_class[c]).mean(dim=0) for c in range(10)])
a_sim_matrix = F.cosine_similarity(a_centroids.unsqueeze(1), a_centroids.unsqueeze(0), dim=2)
g_sim_matrix = F.cosine_similarity(g_centroids.unsqueeze(1), g_centroids.unsqueeze(0), dim=2)
mask = ~torch.eye(10, dtype=bool)
struct_corr = np.corrcoef(a_sim_matrix[mask].numpy(), g_sim_matrix[mask].numpy())[0, 1]
print(f"Structural correlation (inter-class similarity patterns): {struct_corr:.4f}")
