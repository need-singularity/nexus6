```python
#!/usr/bin/env python3
"""C56 Verification: CNN CIFAR tension-accuracy Cohen's d measurement
At baseline accuracy 78%, what is d? (Prediction: d=0.55)
2-point fitting d = 1.30*acc - 0.46 → Verify 3rd point"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch
import torch.nn as nn
import numpy as np
from model_utils import count_params

# CNN + RepulsionQuad (implement directly if cannot import from model_cnn_repulsion.py)
class SimpleCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(),
            nn.AdaptiveAvgPool2d(1), nn.Flatten(),
        )
        self.head_a = nn.Linear(128, 10)
        self.head_g = nn.Linear(128, 10)
        self.field = nn.Sequential(nn.Linear(10, 10), nn.Tanh())
        self.scale = nn.Parameter(torch.tensor(1/3))
    def forward(self, x):
        feat = self.features(x)
        out_a = self.head_a(feat)
        out_g = self.head_g(feat)
        rep = out_a - out_g
        tension = (rep**2).sum(-1, keepdim=True)
        eq = (out_a + out_g) / 2
        direction = self.field(rep)
        output = eq + self.scale * torch.sqrt(tension + 1e-8) * direction
        return output, tension.squeeze(-1)

def main():
    from torchvision import datasets, transforms
    from torch.utils.data import DataLoader
    print("="*60)
    print("  C56 Verification: CNN CIFAR Cohen's d")
    print("  Predicted d=0.55 from linear fit")
    print("="*60)
    t0 = time.time()

    transform_train = transforms.Compose([
        transforms.RandomHorizontalFlip(),
        transforms.RandomCrop(32, padding=4),
        transforms.ToTensor(),
        transforms.Normalize((0.4914,0.4822,0.4465),(0.2023,0.1994,0.2010))
    ])
    transform_test = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914,0.4822,0.4465),(0.2023,0.1994,0.2010))
    ])
    train_data = datasets.CIFAR10('./data', train=True, download=True, transform=transform_train)
    test_data = datasets.CIFAR10('./data', train=False, transform=transform_test)
    train_loader = DataLoader(train_data, batch_size=128, shuffle=True)
    test_loader = DataLoader(test_data, batch_size=256)

    model = SimpleCNN()
    print(f"  Params: {count_params(model):,}")
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    print("\n[1] Training CNN (30 epochs)...")
    for ep in range(30):
        model.train()
        for X, y in train_loader:
            optimizer.zero_grad()
            out, _ = model(X)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
        if (ep+1) % 5 == 0:
            model.eval()
            correct = total = 0
            with torch.no_grad():
                for X, y in test_loader:
                    out, _ = model(X)
                    correct += (out.argmax(1)==y).sum().item()
                    total += y.size(0)
            print(f"    Epoch {ep+1}: {correct/total*100:.1f}%")

    print("\n[2] Collecting per-sample tension...")
    model.eval()
    all_t, all_c = [], []
    with torch.no_grad():
        for X, y in test_loader:
            out, tension = model(X)
            correct = (out.argmax(1)==y).float()
            all_t.append(tension.cpu().numpy())
            all_c.append(correct.cpu().numpy())
    tensions = np.concatenate(all_t)
    corrects = np.concatenate(all_c)

    t_corr = tensions[corrects==1]
    t_wrong = tensions[corrects==0]
    acc = corrects.mean()

    n1, n2 = len(t_corr), len(t_wrong)
    pooled = np.sqrt(((n1-1)*t_corr.var(ddof=1)+(n2-1)*t_wrong.var(ddof=1))/(n1+n2-2))
    d = (t_corr.mean()-t_wrong.mean())/pooled if pooled>0 else 0

    print(f"\n[3] Results")
    print(f"  CNN CIFAR accuracy: {acc*100:.2f}%")
    print(f"  Correct tension: {t_corr.mean():.4f} (n={n1})")
    print(f"  Wrong tension:   {t_wrong.mean():.4f} (n={n2})")
    print(f"  Cohen's d = {d:.4f}")
    print()

    # Compare prediction
    predicted_d = 1.2955 * acc - 0.4595
    print(f"  Predicted d (linear fit): {predicted_d:.4f}")
    print(f"  Actual d:                 {d:.4f}")
    print(f"  Difference:               {abs(d-predicted_d):.4f}")
    print()

    # C56 Verification
    print(f"  3-point validation:")
    print(f"    MNIST (98%): d=0.81 (measured)")
    print(f"    MLP CIFAR (54%): d=0.24 (measured)")
    print(f"    CNN CIFAR ({acc*100:.0f}%): d={d:.2f} (this experiment)")
    print(f"    Prediction: d={predicted_d:.2f}")
    print(f"    Match: {'YES' if abs(d-predicted_d)<0.15 else 'NO'}")
    print(f"\n  Elapsed: {time.time()-t0:.1f}s")
    print("="*60)

if __name__ == '__main__':
    main()
```