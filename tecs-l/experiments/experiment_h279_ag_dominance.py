Looking at this Python file, I can see it's already entirely in English with no Korean text to translate. The file contains:

1. English docstring describing hypothesis 279
2. All comments are in English
3. All variable names, function names, and string literals are in English
4. All print statements and messages are in English

Since there is no Korean text in this file, I'll return the content unchanged:

```python
#!/usr/bin/env python3
"""Hypothesis 279: A/G Dominance Ratio = Input Complexity Measure
MNIST + CIFAR analysis of Engine A vs G output norm ratios

Tests:
  1. |A|/|G| correlates with per-class accuracy?
  2. Complex CIFAR classes (cat, dog, bird) have higher |A|/|G|?
  3. Simple classes (truck, ship) have lower |A|/|G|?
  4. Cross-dataset consistency?
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import time


class AGTrackerEngine(nn.Module):
    """Engine A(logic) + Engine G(pattern) — includes norm tracking"""
    def __init__(self, input_dim=784, hidden_dim=128, output_dim=10):
        super().__init__()
        self.engine_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim)
        )
        self.engine_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim)
        )
        self.combiner = nn.Linear(input_dim, 2)
        self.a_norms = []
        self.g_norms = []

    def forward(self, x):
        out_a = self.engine_a(x)
        out_g = self.engine_g(x)
        if not self.training:
            self.a_norms.append(out_a.detach().norm(dim=-1))
            self.g_norms.append(out_g.detach().norm(dim=-1))
        balance = F.softmax(self.combiner(x), dim=-1)
        return balance[:, 0:1] * out_a + balance[:, 1:2] * out_g


def train_model(model, train_loader, epochs=10, lr=0.001):
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    for ep in range(epochs):
        model.train()
        total_loss = 0
        correct = total = 0
        for x, y in train_loader:
            x = x.view(x.size(0), -1)
            opt.zero_grad()
            out = model(x)
            loss = criterion(out, y)
            loss.backward()
            opt.step()
            total_loss += loss.item()
            correct += (out.argmax(1) == y).sum().item()
            total += y.size(0)
        if (ep + 1) % 3 == 0 or ep == 0:
            print(f"    Epoch {ep+1:>2}/{epochs}: Loss={total_loss/len(train_loader):.4f}, Acc={correct/total*100:.1f}%")


def analyze_ag(model, test_loader, class_names):
    model.eval()
    model.a_norms = []
    model.g_norms = []
    all_labels = []
    all_preds = []
    with torch.no_grad():
        for x, y in test_loader:
            x = x.view(x.size(0), -1)
            out = model(x)
            all_labels.append(y)
            all_preds.append(out.argmax(dim=-1))
    a_norms = torch.cat(model.a_norms)
    g_norms = torch.cat(model.g_norms)
    labels = torch.cat(all_labels)
    preds = torch.cat(all_preds)
    results = []
    for c in range(len(class_names)):
        mask = (labels == c)
        if mask.sum() == 0:
            continue
        a_mean = a_norms[mask].mean().item()
        g_mean = g_norms[mask].mean().item()
        ratio = a_mean / (g_mean + 1e-8)
        acc = (preds[mask] == labels[mask]).float().mean().item()
        a_wins = (a_norms[mask] > g_norms[mask]).float().mean().item() * 100
        tension = (a_norms[mask] - g_norms[mask]).pow(2).mean().item()
        results.append({
            'class': c, 'name': class_names[c],
            'a_norm': a_mean, 'g_norm': g_mean,
            'ratio': ratio, 'acc': acc,
            'a_wins_pct': a_wins, 'tension': tension,
            'n': int(mask.sum().item()),
        })
    return results


def pearson_corr(xs, ys):
    xs, ys = np.array(xs), np.array(ys)
    if len(xs) < 3:
        return 0.0
    xm, ym = xs.mean(), ys.mean()
    num = np.sum((xs - xm) * (ys - ym))
    den = np.sqrt(np.sum((xs - xm)**2) * np.sum((ys - ym)**2))
    return num / den if den > 1e-12 else 0.0


def spearman_corr(xs, ys):
    """Manual Spearman rank correlation."""
    xs, ys = np.array(xs), np.array(ys)
    n = len(xs)
    rx = np.argsort(np.argsort(xs)).astype(float)
    ry = np.argsort(np.argsort(ys)).astype(float)
    d_sq = np.sum((rx - ry) ** 2)
    return 1 - 6 * d_sq / (n * (n**2 - 1))


def print_table(results, dataset_name):
    print(f"\n{'='*80}")
    print(f"  {dataset_name} -- Per-Class A/G Dominance")
    print(f"{'='*80}")
    print(f"  {'Class':<12} {'|A|':>7} {'|G|':>7} {'|A|/|G|':>8} {'A wins%':>8} {'Acc%':>7} {'Tension':>8} {'N':>6}")
    print(f"  {'-'*12} {'-'*7} {'-'*7} {'-'*8} {'-'*8} {'-'*7} {'-'*8} {'-'*6}")
    for r in sorted(results, key=lambda x: -x['ratio']):
        print(f"  {r['name']:<12} {r['a_norm']:>7.3f} {r['g_norm']:>7.3f} {r['ratio']:>8.3f} {r['a_wins_pct']:>7.1f}% {r['acc']*100:>6.1f}% {r['tension']:>8.3f} {r['n']:>6}")
    total_n = sum(r['n'] for r in results)
    overall_acc = sum(r['acc'] * r['n'] for r in results) / total_n
    print(f"  {'OVERALL':<12} {'':>7} {'':>7} {'':>8} {'':>8} {overall_acc*100:>6.1f}% {'':>8} {total_n:>6}")
    print(f"{'='*80}")


def ascii_scatter(results, dataset_name):
    """ASCII scatter: |A|/|G| (x) vs accuracy (y)"""
    W, H = 55, 16
    xs = [r['ratio'] for r in results]
    ys = [r['acc'] * 100 for r in results]
    names = [r['name'][:5] for r in results]

    x_min, x_max = min(xs) * 0.9, max(xs) * 1.1
    y_min, y_max = min(ys) * 0.95, max(ys) * 1.05
    if x_max - x_min < 0.01:
        x_max = x_min + 1
    if y_max - y_min < 0.1:
        y_max = y_min + 10

    grid = [[' ' for _ in range(W)] for _ in range(H)]
    for x, y, name in zip(xs, ys, names):
        col = int((x - x_min) / (x_max - x_min) * (W - 6))
        row = int((1 - (y - y_min) / (y_max - y_min)) * (H - 1))
        col = max(0, min(W - 6, col))
        row = max(0, min(H - 1, row))
        for j, ch in enumerate(name):
            if col + j < W:
                grid[row][col + j] = ch

    print(f"\n  {dataset_name}: |A|/|G| (x) vs Accuracy% (y)")
    print(f"  {'_'*W}")
    for i, row in enumerate(grid):
        y_val = y_max - i * (y_max - y_min) / (H - 1)
        line = ''.join(row)
        if i == 0 or i == H - 1 or i == H // 2:
            print(f"  {y_val:5.1f}|{line}|")
        else:
            print(f"       |{line}|")
    print(f"  {'_'*6}|{'_'*W}|")
    print(f"       {x_min:<8.2f}{' '*(W//2-8)}{(x_min+x_max)/2:^8.2f}{' '*(W//2-8)}{x_max:>8.2f}")
    print(f"       {'|A|/|G| ratio':^{W}}")


def main():
    from torchvision import datasets, transforms
    from torch.utils.data import DataLoader
    import os

    t0 = time.time()
    data_dir = os.environ.get('DATA_DIR', '/tmp/data')

    print()
    print("=" * 80)
    print("  H-279: A/G Dominance = Complexity Measure")
    print("  Cross-dataset: MNIST + CIFAR-10")
    print("=" * 80)

    MNIST_NAMES = [str(i) for i in range(10)]
    CIFAR_NAMES = ['airplane', 'auto', 'bird', 'cat', 'deer',
                   'dog', 'frog', 'horse', 'ship', 'truck']

    # ─────────────────────────────────────────
    # PART 1: MNIST
    # ─────────────────────────────────────────
    print(f"\n{'='*80}")
    print("  PART 1: MNIST (AGTrackerEngine, 784-dim)")
    print(f"{'='*80}")

    transform_m = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    train_ds = datasets.MNIST(data_dir, train=True, download=True, transform=transform_m)
    test_ds = datasets.MNIST(data_dir, train=False, transform=transform_m)
    train_loader = DataLoader(train_ds, batch_size=128, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=256, num_workers=0)

    model_m = AGTrackerEngine(784, 128, 10)
    print(f"  Params: {sum(p.numel() for p in model_m.parameters()):,}")
    train_model(model_m, train_loader, epochs=10)
    mr = analyze_ag(model_m, test_loader, MNIST_NAMES)
    print_table(mr, "MNIST")

    corr_m = pearson_corr([r['ratio'] for r in mr], [r['acc'] for r in mr])
    print(f"\n  Pearson corr (|A|/|G| vs accuracy): r = {corr_m:+.4f}")
    ascii_scatter(mr, "MNIST")

    # ─────────────────────────────────────────
    # PART 2: CIFAR-10
    # ─────────────────────────────────────────
    print(f"\n{'='*80}")
    print("  PART 2: CIFAR-10 (AGTrackerEngine, 3072-dim flattened)")
    print(f"{'='*80}")

    transform_c = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])
    train_c = datasets.CIFAR10(data_dir, train=True, download=True, transform=transform_c)
    test_c = datasets.CIFAR10(data_dir, train=False, transform=transform_c)
    tl_c = DataLoader(train_c, batch_size=128, shuffle=True, num_workers=0)
    te_c = DataLoader(test_c, batch_size=256, num_workers=0)

    model_c = AGTrackerEngine(3072, 256, 10)
    print(f"  Params: {sum(p.numel() for p in model_c.parameters()):,}")
    train_model(model_c, tl_c, epochs=15)
    cr = analyze_ag(model_c, te_c, CIFAR_NAMES)
    print_table(cr, "CIFAR-10")

    corr_c = pearson_corr([r['ratio'] for r in cr], [r['acc'] for r in cr])
    print(f"\n  Pearson corr (|A|/|G| vs accuracy): r = {corr_c:+.4f}")
    ascii_scatter(cr, "CIFAR-10")

    # ─────────────────────────────────────────
    # HYPOTHESIS TESTS
    # ─────────────────────────────────────────
    print(f"\n{'='*80}")
    print("  HYPOTHESIS TESTS")
    print(f"{'='*80}")

    # Test 1: correlation
    print(f"\n  TEST 1: |A|/|G| correlates with per-class accuracy?")
    print(f"    MNIST: r = {corr_m:+.4f}  {'YES (|r|>0.3)' if abs(corr_m)>0.3 else 'WEAK'}")
    print(f"    CIFAR: r = {corr_c:+.4f}  {'YES (|r|>0.3)' if abs(corr_c)>0.3 else 'WEAK'}")

    # Test 2: Complex vs simple CIFAR classes
    print(f"\n  TEST 2: Complex classes (cat, dog, bird) vs simple (truck, ship, auto, airplane)?")
    cifar_dict = {r['name']: r for r in cr}
    complex_cls = ['cat', 'dog', 'bird']
    simple_cls = ['truck', 'ship', 'auto', 'airplane']

    complex_ratios = [cifar_dict[c]['ratio'] for c in complex_cls if c in cifar_dict]
    simple_ratios = [cifar_dict[c]['ratio'] for c in simple_cls if c in cifar_dict]
    mean_complex = np.mean(complex_ratios) if complex_ratios else 0
    mean_simple = np.mean(simple_ratios) if simple_ratios else 0

    print(f"    Complex mean |A|/|G|: {mean_complex:.4f}")
    for c in complex_cls:
        if c in cifar_dict:
            r = cifar_dict[c]
            print(f"      {c:<12}: |A|/|G|={r['ratio']:.3f}  acc={r['acc']*100:.1f}%")
    print(f"    Simple mean |A|/|G|:  {mean_simple:.4f}")
    for c in simple_cls:
        if c in cifar_dict:
            r = cifar_dict[c]
            print(f"      {c:<12}: |A|/|G|={r['ratio']:.3f}  acc={r['acc']*100:.1f}%")

    if mean_complex > mean_simple:
        print(f"    -> Complex > Simple by {mean_complex-mean_simple:.4f}: SUPPORTS hypothesis")
    else:
        print(f"    -> Simple >= Complex by {mean_simple-mean_complex:.4f}: CONTRADICTS hypothesis")

    # Test 3: ranking
    print(f"\n  TEST 3: Simple classes in bottom |A|/|G|?")
    sorted_c = sorted(cr, key=lambda x: x['ratio'])
    bottom3 = set(r['name'] for r in sorted_c[:3])
    top3 = set(r['name'] for r in sorted_c[-3:])
    bot_str = ', '.join(r['name'] + '(' + '{:.3f}'.format(r['ratio']) + ')' for r in sorted_c[:3])
    top_str = ', '.join(r['name'] + '(' + '{:.3f}'.format(r['ratio']) + ')' for r in sorted_c[-3:])
    print(f"    Bottom 3: {bot_str}")
    print(f"    Top 3:    {top_str}")
    simple_in_bot = len(set(simple_cls) & bottom3)
    complex_in_top = len(set(complex_cls) & top3)
    print(f"    Simple in bottom 3: {simple_in_bot}")
    print(f"    Complex in top 3:   {complex_in_top}")

    # Test 4: cross-dataset consistency
    print(f"\n  TEST 4: Cross-dataset consistency")
    print(f"    MNIST highest |A|/|G|: digit {max(mr, key=lambda x: x['ratio'])['name']}")
    print(f"    MNIST lowest  |A|/|G|: digit {min(mr, key=lambda x: x['ratio'])['name']}")
    print(f"    CIFAR highest |A|/|G|: {max(cr, key=lambda x: x['ratio'])['name']}")
    print(f"    CIFAR lowest  |A|/|G|: {min(cr, key=lambda x: x['ratio'])['name']}")
    same_dir = (corr_m > 0) == (corr_c > 0)
    print(f"    Correlation direction: MNIST={'pos' if corr_m>0 else 'neg'}, CIFAR={'pos' if corr_c>0 else 'neg'}")
    print(f"    Consistent: {'YES' if same_dir else 'NO'}")

    # ─────────────────────────────────────────
    # Compare with prior H-279 data
    # ─────────────────────────────────────────
    print(f"\n  COMPARISON WITH PRIOR DATA (H-279 doc)")
    prior = {'0':1.82, '1':0.31, '2':0.74, '3':1.06, '4':1.33,
             '5':0.98, '6':1.10, '7':0.76, '8':0.41, '9':0.64}
    print(f"  {'Digit':<8} {'Prior':>8} {'Current':>8} {'Delta':>8}")
    print(f"  {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
    pvs, cvs = [], []
    for r in sorted(mr, key=lambda x: x['class']):
        p = prior.get(r['name'], 0)
        pvs.append(p)
        cvs.append(r['ratio'])
        print(f"  {r['name']:<8} {p:>8.3f} {r['ratio']:>8.3f} {r['ratio']-p:>+8.3f}")
    rho = spearman_corr(pvs, cvs)
    print(f"\n  Spearman rank corr (prior vs current): rho = {rho:.4f}")

    # ─────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────
    print(f"\n{'='*80}")
    print(f"  SUMMARY")
    print(f"{'='*80}")
    print(f"  {'Metric':<45} {'MNIST':>12} {'CIFAR':>12}")
    print(f"  {'-'*45} {'-'*12} {'-'*12}")
    print(f"  {'Pearson corr (|A|/|G| vs acc)':<45} {corr_m:>+12.4f} {corr_c:>+12.4f}")
    print(f"  {'Mean |A|/|G|':<45} {np.mean([r['ratio'] for r in mr]):>12.4f} {np.mean([r['ratio'] for r in cr]):>12.4f}")
    print(f"  {'Std |A|/|G|':<45} {np.std([r['ratio'] for r in mr]):>12.4f} {np.std([r['ratio'] for r in cr]):>12.4f}")
    print(f"  {'Max |A|/|G|':<45} {max(r['ratio'] for r in mr):>12.4f} {max(r['ratio'] for r in cr):>12.4f}")
    print(f"  {'Min |A|/|G|':<45} {min(r['ratio'] for r in mr):>12.4f} {min(r['ratio'] for r in cr):>12.4f}")
    tm = sum(r['acc']*r['n'] for r in mr)/sum(r['n'] for r in mr)
    tc = sum(r['acc']*r['n'] for r in cr)/sum(r['n'] for r in cr)
    print(f"  {'Overall accuracy':<45} {tm*100:>11.1f}% {tc*100:>11.1f}%")
    if mean_complex > 0 and mean_simple > 0:
        print(f"  {'CIFAR complex mean |A|/|G|':<45} {'N/A':>12} {mean_complex:>12.4f}")
        print(f"  {'CIFAR simple mean |A|/|G|':<45} {'N/A':>12} {mean_simple:>12.4f}")
        print(f"  {'Complex - Simple gap':<45} {'N/A':>12} {mean_complex-mean_simple:>+12.4f}")
    print(f"  {'Prior rank corr (MNIST)':<45} {rho:>+12.4f} {'N/A':>12}")
    print(f"{'='*80}")

    # ─────────────────────────────────────────
    # Verdict
    # ─────────────────────────────────────────
    supports = 0
    total_tests = 4
    print(f"\n{'='*80}")
    print(f"  VERDICT")
    print(f"{'='*80}")

    if abs(corr_m) > 0.3 or abs(corr_c) > 0.3:
        supports += 1
        print(f"  [PASS] Correlation exists (MNIST r={corr_m:.3f}, CIFAR r={corr_c:.3f})")
    else:
        print(f"  [FAIL] Weak correlation (MNIST r={corr_m:.3f}, CIFAR r={corr_c:.3f})")

    if mean_complex > mean_simple:
        supports += 1
        print(f"  [PASS] Complex CIFAR classes have higher |A|/|G|")
    else:
        print(f"  [FAIL] Complex CIFAR classes do NOT have higher |A|/|G|")

    if simple_in_bot >= 2:
        supports += 1
        print(f"  [PASS] Simple classes cluster at low |A|/|G| ({simple_in_bot}/3 in bottom)")
    else:
        print(f"  [FAIL] Simple classes NOT concentrated at low |A|/|G| ({simple_in_bot}/3)")

    if same_dir:
        supports += 1
        print(f"  [PASS] Cross-dataset correlation direction consistent")
    else:
        print(f"  [FAIL] Cross-dataset correlation direction inconsistent")

    print(f"\n  Score: {supports}/{total_tests}")
    if supports >= 3:
        print(f"  -> STRONG SUPPORT for H-279")
    elif supports >= 2:
        print(f"  -> MODERATE SUPPORT for H-279")
    else:
        print(f"  -> WEAK/NO SUPPORT for H-279")
    print(f"{'='*80}")

    print(f"\n  Time: {time.time()-t0:.1f}s")


if __name__ == '__main__':
    main()
```