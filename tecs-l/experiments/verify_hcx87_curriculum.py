#!/usr/bin/env python3
"""H-CX-87 Verification: PH-guided curriculum — confusion pair priority learning

baseline vs curriculum (confusion pair oversampling) comparison
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from torch.utils.data import DataLoader, WeightedRandomSampler
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data


def get_confusion_pairs(dataset_name):
    """Known confusion pairs from CIFAR/Fashion/MNIST (H-CX-66 results)"""
    if dataset_name == 'cifar':
        return [(3,5), (0,8), (1,9), (2,4)]  # cat-dog, plane-ship, auto-truck, bird-deer
    elif dataset_name == 'fashion':
        return [(2,4), (2,6), (0,6), (5,7)]  # pullover-coat, pullover-shirt, tshirt-shirt, sandal-sneaker
    else:  # mnist
        return [(4,9), (3,5), (7,9), (5,8)]  # known confusion pairs


def train_and_eval(model, dim, tl, te, epochs, name="model"):
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()
    accs = []

    for ep in range(epochs):
        model.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()

        model.eval(); c = t_ = 0
        with torch.no_grad():
            for x, y in te:
                o, _ = model(x.view(-1, dim))
                c += (o.argmax(1)==y).sum().item(); t_ += y.size(0)
        acc = c / t_ * 100
        accs.append(acc)
        if (ep+1) % 5 == 0:
            print(f"    {name} Epoch {ep+1}: acc={acc:.1f}%")

    return accs


def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    conf_pairs = get_confusion_pairs(dataset_name)
    conf_classes = set()
    for a, b in conf_pairs:
        conf_classes.add(a); conf_classes.add(b)

    print(f"\n{'='*70}")
    print(f"  H-CX-87: PH Curriculum — {dataset_name.upper()}")
    print(f"{'='*70}")
    print(f"  Confusion pairs: {[(names[a], names[b]) for a,b in conf_pairs]}")

    # Baseline
    print(f"\n  --- Baseline (uniform sampling) ---")
    torch.manual_seed(42)
    baseline = PureFieldEngine(dim, 128, 10)
    accs_base = train_and_eval(baseline, dim, tl, te, epochs, "Baseline")

    # Curriculum: oversample confusion classes 3x
    print(f"\n  --- Curriculum (confusion 3x oversampling) ---")
    # Create weighted sampler
    train_ds = tl.dataset
    weights = np.ones(len(train_ds))
    for idx in range(len(train_ds)):
        _, label = train_ds[idx]
        if isinstance(label, torch.Tensor): label = label.item()
        if label in conf_classes:
            weights[idx] = 3.0
    sampler = WeightedRandomSampler(weights, num_samples=len(train_ds), replacement=True)
    tl_curriculum = DataLoader(train_ds, batch_size=256, sampler=sampler)

    torch.manual_seed(42)
    curriculum = PureFieldEngine(dim, 128, 10)
    accs_curr = train_and_eval(curriculum, dim, tl_curriculum, te, epochs, "Curriculum")

    # Curriculum v2: weighted loss on confusion pairs
    print(f"\n  --- Curriculum v2 (confusion pair weighted loss) ---")

    class WeightedCE(nn.Module):
        def __init__(self, conf_classes, weight=3.0, n_cls=10):
            super().__init__()
            w = torch.ones(n_cls)
            for c in conf_classes:
                w[c] = weight
            self.ce = nn.CrossEntropyLoss(weight=w)
        def forward(self, x, y):
            return self.ce(x, y)

    torch.manual_seed(42)
    curr_v2 = PureFieldEngine(dim, 128, 10)
    opt_v2 = torch.optim.Adam(curr_v2.parameters(), lr=1e-3)
    wce = WeightedCE(conf_classes, weight=3.0, n_cls=10)
    accs_v2 = []

    for ep in range(epochs):
        curr_v2.train()
        for x, y in tl:
            opt_v2.zero_grad()
            out, t = curr_v2(x.view(-1, dim))
            loss = wce(out, y); loss.backward(); opt_v2.step()

        curr_v2.eval(); c = t_ = 0
        with torch.no_grad():
            for x, y in te:
                o, _ = curr_v2(x.view(-1, dim))
                c += (o.argmax(1)==y).sum().item(); t_ += y.size(0)
        acc = c / t_ * 100
        accs_v2.append(acc)
        if (ep+1) % 5 == 0:
            print(f"    CurrV2 Epoch {ep+1}: acc={acc:.1f}%")

    # Comparison
    print(f"\n  {'='*55}")
    print(f"  {'Epoch':>5} {'Baseline':>10} {'Oversamp':>10} {'WtLoss':>10} {'Best':>10}")
    print(f"  {'-'*45}")
    for ep in range(epochs):
        best = max(accs_base[ep], accs_curr[ep], accs_v2[ep])
        marker = ''
        if best == accs_curr[ep] and best > accs_base[ep]: marker = ' ←OS'
        elif best == accs_v2[ep] and best > accs_base[ep]: marker = ' ←WL'
        print(f"  {ep+1:>5} {accs_base[ep]:>10.1f} {accs_curr[ep]:>10.1f} {accs_v2[ep]:>10.1f} {best:>10.1f}{marker}")

    final_base = accs_base[-1]
    final_curr = accs_curr[-1]
    final_v2 = accs_v2[-1]

    print(f"\n  Final: Base={final_base:.1f}%, Oversamp={final_curr:.1f}% ({final_curr-final_base:+.1f}), "
          f"WtLoss={final_v2:.1f}% ({final_v2-final_base:+.1f})")

    # Convergence speed: epoch to reach 95% of final accuracy
    target_95 = final_base * 0.95
    conv_base = next((i+1 for i, a in enumerate(accs_base) if a >= target_95), epochs)
    conv_curr = next((i+1 for i, a in enumerate(accs_curr) if a >= target_95), epochs)
    conv_v2 = next((i+1 for i, a in enumerate(accs_v2) if a >= target_95), epochs)
    print(f"  Convergence (95% of final): Base=ep{conv_base}, Oversamp=ep{conv_curr}, WtLoss=ep{conv_v2}")
    print(f"  H-CX-87 (faster convergence): {'SUPPORTED' if min(conv_curr, conv_v2) < conv_base else 'REJECTED'}")

    return {
        'base': final_base, 'curr': final_curr, 'v2': final_v2,
        'conv_base': conv_base, 'conv_curr': conv_curr, 'conv_v2': conv_v2,
    }

if __name__ == '__main__':
    for ds in ['mnist', 'fashion', 'cifar']:
        try:
            run_experiment(ds)
        except Exception as e:
            print(f"  {ds} failed: {e}")
            import traceback; traceback.print_exc()