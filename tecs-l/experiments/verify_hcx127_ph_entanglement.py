#!/usr/bin/env python3
"""H-CX-127: PH Entanglement
Prediction: Two models trained on DIFFERENT data splits produce correlated confusion matrices.
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/TECS-L')

import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import Subset, DataLoader
from torchvision import datasets, transforms
from model_pure_field import PureFieldEngine


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


def get_confusion_matrix(model, loader):
    model.eval()
    cm = np.zeros((10, 10))
    with torch.no_grad():
        for X, y in loader:
            X = X.view(X.size(0), -1)
            out, _ = model(X)
            preds = out.argmax(dim=1)
            for true, pred in zip(y.numpy(), preds.numpy()):
                cm[true][pred] += 1
    return cm


print("=== H-CX-127: PH Entanglement ===")

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))
])
full_train = datasets.MNIST('data', train=True, download=True, transform=transform)
test_ds = datasets.MNIST('data', train=False, transform=transform)
test_loader = DataLoader(test_ds, batch_size=128, shuffle=False)

n = len(full_train)
indices = torch.randperm(n).tolist()
split1 = Subset(full_train, indices[:n//2])
split2 = Subset(full_train, indices[n//2:])
loader1 = DataLoader(split1, batch_size=128, shuffle=True)
loader2 = DataLoader(split2, batch_size=128, shuffle=True)

print("\nTraining Model 1 (first half)...")
model1 = PureFieldEngine(784, 128, 10)
train_purefield(model1, loader1, epochs=5)

print("\nTraining Model 2 (second half)...")
model2 = PureFieldEngine(784, 128, 10)
train_purefield(model2, loader2, epochs=5)

cm1 = get_confusion_matrix(model1, test_loader)
cm2 = get_confusion_matrix(model2, test_loader)

print("\nConfusion Matrix 1 (diagonal):", np.diag(cm1).astype(int))
print("Confusion Matrix 2 (diagonal):", np.diag(cm2).astype(int))

corr_full = np.corrcoef(cm1.flatten(), cm2.flatten())[0, 1]

mask = ~np.eye(10, dtype=bool)
corr_offdiag = np.corrcoef(cm1[mask], cm2[mask])[0, 1]

print(f"\nCorrelation (full CM): {corr_full:.4f}")
print(f"Correlation (off-diagonal only): {corr_offdiag:.4f}")
print(f"Prediction: correlated confusion matrices")
print(f"Verdict: {'PASS' if corr_offdiag > 0.5 else 'FAIL'} (off-diag corr {'>' if corr_offdiag > 0.5 else '<='} 0.5)")
