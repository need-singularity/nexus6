#!/usr/bin/env python3
"""H-CX-58 Verification: Precognition Lens — Precognition AUC by Tension Interval

Divide tension into quintiles → Measure precognition AUC for each interval
Compare with lens magnification curve using logistic fitting
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, numpy as np
from sklearn.metrics import roc_auc_score
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data

def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()

    print(f"\n{'='*70}")
    print(f"  H-CX-58: Precognition Lens — {dataset_name.upper()}")
    print(f"{'='*70}")

    # Train
    for ep in range(epochs):
        model.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()
        if (ep+1) % 5 == 0:
            model.eval(); correct = total = 0
            with torch.no_grad():
                for x, y in te:
                    o, _ = model(x.view(-1, dim))
                    correct += (o.argmax(1)==y).sum().item(); total += y.size(0)
            print(f"  Epoch {ep+1}: acc={correct/total*100:.1f}%")

    # Collect (tension, correct) pairs
    model.eval()
    tensions, corrects, labels, preds = [], [], [], []
    with torch.no_grad():
        for x, y in te:
            out, t = model(x.view(-1, dim))
            pred = out.argmax(1)
            tensions.extend(t.numpy().tolist())
            corrects.extend((pred == y).numpy().tolist())
            labels.extend(y.numpy().tolist())
            preds.extend(pred.numpy().tolist())

    T = np.array(tensions)
    C = np.array(corrects, dtype=float)
    Y = np.array(labels)
    P = np.array(preds)

    # Overall precognition AUC
    overall_auc = roc_auc_score(C, T)
    print(f"\n  Overall Precognition AUC: {overall_auc:.4f}")
    print(f"  tension_scale: {model.tension_scale.item():.4f}")

    # Quintile analysis
    quintiles = np.percentile(T, [0, 20, 40, 60, 80, 100])
    print(f"\n  {'Quintile':>10} {'T_range':>18} {'N':>6} {'Acc%':>7} {'AUC':>7} {'Correct_T':>10} {'Wrong_T':>10}")
    print(f"  {'-'*70}")

    q_aucs = []
    q_mids = []
    for i in range(5):
        lo, hi = quintiles[i], quintiles[i+1]
        if i == 4:
            mask = (T >= lo) & (T <= hi)
        else:
            mask = (T >= lo) & (T < hi)
        n = mask.sum()
        if n < 10:
            q_aucs.append(0.5)
            q_mids.append((lo+hi)/2)
            continue

        acc = C[mask].mean() * 100
        ct = T[mask][C[mask]==1].mean() if (C[mask]==1).sum() > 0 else 0
        wt = T[mask][C[mask]==0].mean() if (C[mask]==0).sum() > 0 else 0

        # Per-quintile AUC (can we distinguish correct/wrong within this quintile?)
        if len(np.unique(C[mask])) > 1:
            q_auc = roc_auc_score(C[mask], T[mask])
        else:
            q_auc = 0.5
        q_aucs.append(q_auc)
        q_mids.append((lo+hi)/2)

        print(f"  Q{i+1:>8} [{lo:>7.2f},{hi:>7.2f}] {n:>6} {acc:>7.1f} {q_auc:>7.3f} {ct:>10.2f} {wt:>10.2f}")

    # Monotonicity check (lens prediction: AUC increases with tension)
    acc_by_q = []
    for i in range(5):
        lo, hi = quintiles[i], quintiles[i+1]
        mask = (T >= lo) & (T <= hi + (0.001 if i==4 else 0))
        acc_by_q.append(C[mask].mean() * 100 if mask.sum() > 0 else 50)

    print(f"\n  Accuracy by Quintile (lens prediction: monotonic increase):")
    max_acc = max(acc_by_q) if acc_by_q else 100
    for i, a in enumerate(acc_by_q):
        bar = int(a / max_acc * 40)
        print(f"  Q{i+1} |{'█' * bar}{'░' * (40 - bar)}| {a:.1f}%")

    # Monotonicity score
    mono = sum(1 for i in range(4) if acc_by_q[i+1] >= acc_by_q[i]) / 4
    print(f"\n  Monotonicity score: {mono:.2f} (1.0 = perfect lens)")

    # Logistic fit: P(correct) = sigmoid(a + b*T)
    from scipy.optimize import curve_fit
    def logistic(x, a, b):
        return 1 / (1 + np.exp(-(a + b*x)))

    try:
        T_norm = (T - T.mean()) / (T.std() + 1e-8)
        popt, _ = curve_fit(logistic, T_norm, C, p0=[0, 1], maxfev=5000)
        fitted = logistic(T_norm, *popt)
        fit_auc = roc_auc_score(C, fitted)
        print(f"\n  Logistic fit: a={popt[0]:.4f}, b={popt[1]:.4f}")
        print(f"  Logistic AUC: {fit_auc:.4f} (vs raw: {overall_auc:.4f})")
        print(f"  b > 0 confirms lens effect: {'YES' if popt[1] > 0 else 'NO'}")
    except Exception as e:
        print(f"\n  Logistic fit failed: {e}")

    # Per-class AUC (for H-CX-60 cross-reference)
    print(f"\n  Per-class Precognition AUC:")
    print(f"  {'Class':>7} {'N':>5} {'AUC':>7} {'Mean_T':>8} {'Acc%':>7}")
    print(f"  {'-'*40}")
    for c in range(10):
        mask = Y == c
        if mask.sum() < 10 or len(np.unique(C[mask])) < 2:
            continue
        c_auc = roc_auc_score(C[mask], T[mask])
        print(f"  {names[c]:>7} {mask.sum():>5} {c_auc:>7.3f} {T[mask].mean():>8.2f} {C[mask].mean()*100:>7.1f}")

    return overall_auc, mono, model.tension_scale.item()

if __name__ == '__main__':
    results = {}
    for ds in ['mnist', 'fashion', 'cifar']:
        try:
            auc, mono, ts = run_experiment(ds)
            results[ds] = (auc, mono, ts)
        except Exception as e:
            print(f"  {ds} failed: {e}")
            results[ds] = (0, 0, 0)

    print(f"\n{'='*70}")
    print(f"  H-CX-58 SUMMARY")
    print(f"{'='*70}")
    print(f"  {'Dataset':>10} {'AUC':>7} {'Mono':>6} {'t_scale':>8}")
    print(f"  {'-'*35}")
    for ds, (auc, mono, ts) in results.items():
        print(f"  {ds:>10} {auc:>7.4f} {mono:>6.2f} {ts:>8.4f}")

    # Lens prediction: AUC correlates with tension_scale
    aucs = [v[0] for v in results.values()]
    tss = [v[2] for v in results.values()]
    if len(aucs) == 3:
        r = np.corrcoef(aucs, tss)[0, 1]
        print(f"\n  Corr(AUC, tension_scale): {r:.4f}")
        print(f"  H-CX-58 lens prediction (r > 0): {'SUPPORTED' if r > 0 else 'REJECTED'}")