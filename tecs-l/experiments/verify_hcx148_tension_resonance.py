#!/usr/bin/env python3
"""H-CX-148: Tension Resonance
Prediction: Independently trained models have correlated per-class tension patterns (r > 0.9).
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/TECS-L')

import torch
import torch.nn as nn
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


def get_class_tensions(model, loader):
    model.eval()
    tensions = {c: [] for c in range(10)}
    with torch.no_grad():
        for X, y in loader:
            X = X.view(X.size(0), -1)
            _, tension = model(X)
            for c in range(10):
                mask = (y == c)
                if mask.sum() > 0:
                    tensions[c].append(tension[mask].mean().item())
    return np.array([np.mean(tensions[c]) for c in range(10)])


print("=== H-CX-148: Tension Resonance ===")
train_loader, test_loader = load_mnist(batch_size=128)

print("\nTraining Model 1...")
model1 = PureFieldEngine(784, 128, 10)
train_purefield(model1, train_loader, epochs=5)

print("\nTraining Model 2...")
model2 = PureFieldEngine(784, 128, 10)
train_purefield(model2, train_loader, epochs=5)

t1 = get_class_tensions(model1, test_loader)
t2 = get_class_tensions(model2, test_loader)

print("\nPer-class tensions:")
print("Class:   ", "  ".join(str(c) for c in range(10)))
print("Model 1: ", "  ".join(f"{v:.3f}" for v in t1))
print("Model 2: ", "  ".join(f"{v:.3f}" for v in t2))

corr = np.corrcoef(t1, t2)[0, 1]
print(f"\nCorrelation: {corr:.4f}")
print(f"Prediction: r > 0.9")
print(f"Verdict: {'PASS' if corr > 0.9 else 'FAIL'}")
