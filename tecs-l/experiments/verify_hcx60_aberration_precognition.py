```python
#!/usr/bin/env python3
"""H-CX-60 Verification: Aberration Precognition — 5 Seidel Aberration Mapping Measurements"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from sklearn.metrics import roc_auc_score
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data

def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()

    print(f"\n{'='*70}")
    print(f"  H-CX-60: Aberration Precognition — {dataset_name.upper()}")
    print(f"{'='*70}")

    # Collect per-epoch stats for distortion analysis
    epoch_aucs = []

    for ep in range(epochs):
        model.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()

        # Per-epoch precognition AUC
        model.eval()
        tensions, corrects, ys = [], [], []
        with torch.no_grad():
            for x, y in te:
                out, t = model(x.view(-1, dim))
                pred = out.argmax(1)
                tensions.extend(t.numpy().tolist())
                corrects.extend((pred == y).numpy().tolist())
                ys.extend(y.numpy().tolist())
        T = np.array(tensions); C = np.array(corrects, dtype=float); Y = np.array(ys)
        if len(np.unique(C)) > 1:
            ep_auc = roc_auc_score(C, T)
        else:
            ep_auc = 0.5
        epoch_aucs.append(ep_auc)
        if (ep+1) % 5 == 0:
            acc = C.mean() * 100
            print(f"  Epoch {ep+1}: acc={acc:.1f}%  precog_AUC={ep_auc:.4f}")

    # Final detailed analysis
    model.eval()
    tensions, corrects, labels, preds, dirs, mags = [], [], [], [], [], []
    with torch.no_grad():
        for x, y in te:
            x_flat = x.view(-1, dim)
            a = model.engine_a(x_flat); g = model.engine_g(x_flat)
            rep = a - g
            mag = torch.sqrt((rep**2).mean(-1))
            d = F.normalize(rep, dim=-1)
            out = model.tension_scale * mag.unsqueeze(-1) * d
            pred = out.argmax(1)
            tensions.extend(mag.numpy().tolist())
            corrects.extend((pred == y).numpy().tolist())
            labels.extend(y.numpy().tolist())
            preds.extend(pred.numpy().tolist())
            dirs.append(d.numpy()); mags.append(mag.numpy())

    T = np.array(tensions); C = np.array(corrects, dtype=float)
    Y = np.array(labels); P = np.array(preds)
    D = np.concatenate(dirs); M = np.concatenate(mags)

    # === ABERRATION 1: Chromatic (per-class AUC variance) ===
    print(f"\n  === Aberration 1: Chromatic (per-class AUC) ===")
    class_aucs = []
    for c in range(10):
        mask = Y == c
        if mask.sum() > 10 and len(np.unique(C[mask])) > 1:
            c_auc = roc_auc_score(C[mask], T[mask])
        else:
            c_auc = 0.5
        class_aucs.append(c_auc)
        bar = int(c_auc * 40)
        print(f"  {names[c]:>7} |{'█'*bar}{'░'*(40-bar)}| {c_auc:.3f}")

    chrom_var = np.var(class_aucs)
    print(f"  Chromatic aberration (AUC variance): {chrom_var:.6f}")

    # === ABERRATION 2: Spherical (mid-tension uncertainty) ===
    print(f"\n  === Aberration 2: Spherical (tension quintile accuracy) ===")
    quintiles = np.percentile(T, [0, 20, 40, 60, 80, 100])
    q_accs = []
    for i in range(5):
        lo, hi = quintiles[i], quintiles[i+1]
        mask = (T >= lo) & (T <= hi + (0.001 if i == 4 else 0))
        acc = C[mask].mean() * 100 if mask.sum() > 0 else 50
        q_accs.append(acc)
        bar = int(acc / 100 * 40)
        print(f"  Q{i+1} [{lo:>6.1f},{hi:>6.1f}] |{'█'*bar}{'░'*(40-bar)}| {acc:.1f}%")

    # U-shape check: middle quintile should have lowest accuracy
    mid_is_lowest = q_accs[2] == min(q_accs)
    print(f"  Spherical aberration (mid-Q lowest): {mid_is_lowest}")

    # === ABERRATION 3: Astigmatic (direction std vs magnitude std asymmetry) ===
    print(f"\n  === Aberration 3: Astigmatic (dir_std vs mag_std) ===")
    for c in range(10):
        mask = Y == c
        if mask.sum() < 10: continue
        dir_std = D[mask].std(0).mean()
        mag_std = M[mask].std()
        ratio = dir_std / (mag_std + 1e-8)
        bar_d = int(min(dir_std * 100, 20))
        bar_m = int(min(mag_std * 10, 20))
        print(f"  {names[c]:>7} dir_std={dir_std:.4f}{'▓'*bar_d} mag_std={mag_std:.4f}{'█'*bar_m} ratio={ratio:.3f}")

    # === ABERRATION 4: Coma (overconfidence vs underconfidence asymmetry) ===
    print(f"\n  === Aberration 4: Coma (over/under confidence) ===")
    median_t = np.median(T)
    high_wrong = ((T > median_t) & (C == 0)).sum()  # overconfident wrong
    low_correct = ((T < median_t) & (C == 1)).sum()  # underconfident correct
    high_correct = ((T > median_t) & (C == 1)).sum()
    low_wrong = ((T < median_t) & (C == 0)).sum()

    print(f"  High tension + Wrong (overconfident):    {high_wrong}")
    print(f"  Low tension + Correct (underconfident):  {low_correct}")
    print(f"  High tension + Correct (ideal):          {high_correct}")
    print(f"  Low tension + Wrong (expected):           {low_wrong}")
    coma_ratio = high_wrong / (low_correct + 1) if low_correct > 0 else float('inf')
    print(f"  Coma ratio (over/under): {coma_ratio:.3f}")
    print(f"  Asymmetry: {'YES (coma present)' if abs(coma_ratio - 1) > 0.2 else 'symmetric (no coma)'}")

    # === ABERRATION 5: Distortion (epoch-wise AUC trajectory) ===
    print(f"\n  === Aberration 5: Distortion (epoch AUC trajectory) ===")
    max_auc = max(epoch_aucs) if epoch_aucs else 1
    for i, auc in enumerate(epoch_aucs):
        bar = int(auc / max_auc * 40) if max_auc > 0 else 0
        marker = ' ←peak' if auc == max_auc else ''
        print(f"  ep{i+1:>2} |{'█'*bar}{'░'*(40-bar)}| {auc:.4f}{marker}")

    # Distortion = non-monotonicity
    reversals = sum(1 for i in range(len(epoch_aucs)-1) if epoch_aucs[i+1] < epoch_aucs[i])
    print(f"  Reversals: {reversals}/{len(epoch_aucs)-1}")
    print(f"  Distortion level: {'HIGH' if reversals > 3 else 'MODERATE' if reversals > 1 else 'LOW'}")

    # === SUMMARY ===
    print(f"\n  === H-CX-60 Aberration Summary ({dataset_name.upper()}) ===")
    print(f"  | Aberration   | Metric              | Value              |")
    print(f"  |--------------|---------------------|--------------------|")
    print(f"  | Chromatic    | AUC variance        | {chrom_var:.6f}          |")
    print(f"  | Spherical    | Mid-Q lowest        | {mid_is_lowest}              |")
    print(f"  | Astigmatic   | dir/mag ratio range | measured above     |")
    print(f"  | Coma         | over/under ratio    | {coma_ratio:.3f}             |")
    print(f"  | Distortion   | reversals           | {reversals}/{len(epoch_aucs)-1}               |")

    return chrom_var, coma_ratio, reversals

if __name__ == '__main__':
    for ds in ['mnist', 'fashion', 'cifar']:
        try:
            run_experiment(ds)
        except Exception as e:
            print(f"  {ds} failed: {e}")
```