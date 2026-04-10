#!/usr/bin/env python3
"""H-CX-58+59 Integration: Tension Magnitude(Lens) + Direction(Confusion Prediction) = Unified Precognition System

H-CX-58: Tension Magnitude → "Will it be right or wrong" (AUC)
H-CX-59: Direction Vector → "What will it be confused with" (Dir→Pred%)
Integration: Magnitude+Direction combination → Stronger precognition?
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.linear_model import LogisticRegression
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data

def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()

    print(f"\n{'='*70}")
    print(f"  Unified Precognition (H-CX-58 + H-CX-59) — {dataset_name.upper()}")
    print(f"{'='*70}")

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

    # Collect all features
    model.eval()
    all_mag, all_dir, all_y, all_pred, all_tension = [], [], [], [], []
    n_cls = len(names)

    with torch.no_grad():
        for x, y in te:
            x_flat = x.view(-1, dim)
            a = model.engine_a(x_flat); g = model.engine_g(x_flat)
            rep = a - g
            mag = torch.sqrt((rep**2).mean(-1))
            d = F.normalize(rep, dim=-1)
            out = model.tension_scale * mag.unsqueeze(-1) * d
            pred = out.argmax(1)
            all_mag.append(mag.numpy())
            all_dir.append(d.numpy())
            all_y.append(y.numpy())
            all_pred.append(pred.numpy())
            all_tension.append(mag.numpy())

    M = np.concatenate(all_mag)
    D = np.concatenate(all_dir)
    Y = np.concatenate(all_y)
    P = np.concatenate(all_pred)
    correct = (P == Y).astype(float)

    # Class mean directions (from correct predictions only)
    class_means = np.zeros((n_cls, D.shape[1]))
    for c in range(n_cls):
        mask = (Y == c) & (P == c)
        if mask.sum() > 0:
            class_means[c] = D[mask].mean(0)
    norms = np.linalg.norm(class_means, axis=1, keepdims=True)
    class_means_n = class_means / np.clip(norms, 1e-8, None)

    # === Feature 1: Magnitude only (H-CX-58) ===
    auc_mag = roc_auc_score(correct, M)
    print(f"\n  [H-CX-58] Magnitude-only AUC: {auc_mag:.4f}")

    # === Feature 2: Direction confidence (H-CX-59) ===
    # cos(direction, predicted_class_mean) as confidence
    dir_conf = np.array([(D[i] * class_means_n[P[i]]).sum() for i in range(len(D))])
    auc_dir = roc_auc_score(correct, dir_conf)
    print(f"  [H-CX-59] Direction-conf AUC: {auc_dir:.4f}")

    # === Feature 3: Direction gap (H-CX-59 extended) ===
    # cos(dir, pred_class) - cos(dir, 2nd_closest_class)
    dir_gap = np.zeros(len(D))
    for i in range(len(D)):
        cosines = [float((D[i] * class_means_n[c]).sum()) for c in range(n_cls)]
        sorted_cos = sorted(cosines, reverse=True)
        dir_gap[i] = sorted_cos[0] - sorted_cos[1]  # gap between top-2
    auc_gap = roc_auc_score(correct, dir_gap)
    print(f"  [H-CX-59] Direction-gap AUC:  {auc_gap:.4f}")

    # === Feature 4: Unified (magnitude + direction) ===
    # Combine: magnitude * direction_confidence
    unified = M * dir_conf
    auc_unified = roc_auc_score(correct, unified)
    print(f"  [Unified] mag * dir_conf AUC: {auc_unified:.4f}")

    # === Feature 5: Unified v2 (magnitude * gap) ===
    unified_v2 = M * dir_gap
    auc_unified_v2 = roc_auc_score(correct, unified_v2)
    print(f"  [Unified] mag * dir_gap AUC:  {auc_unified_v2:.4f}")

    # === Feature 6: Logistic regression on all features ===
    from sklearn.model_selection import cross_val_score
    X_features = np.column_stack([
        (M - M.mean()) / (M.std() + 1e-8),
        (dir_conf - dir_conf.mean()) / (dir_conf.std() + 1e-8),
        (dir_gap - dir_gap.mean()) / (dir_gap.std() + 1e-8),
    ])
    lr = LogisticRegression(max_iter=1000)
    cv_scores = cross_val_score(lr, X_features, correct, cv=5, scoring='roc_auc')
    auc_lr = cv_scores.mean()
    print(f"  [LR 3feat] 5-fold CV AUC:     {auc_lr:.4f} (±{cv_scores.std():.4f})")

    # === Comparison table ===
    methods = [
        ('Magnitude only (H-CX-58)', auc_mag),
        ('Dir confidence (H-CX-59)', auc_dir),
        ('Dir gap (H-CX-59 ext)', auc_gap),
        ('mag * dir_conf', auc_unified),
        ('mag * dir_gap', auc_unified_v2),
        ('LR(mag,conf,gap)', auc_lr),
    ]

    print(f"\n  {'='*55}")
    print(f"  Precognition Method Comparison")
    print(f"  {'='*55}")
    best_auc = max(m[1] for m in methods)
    for name, auc in methods:
        bar = int(auc * 40)
        marker = ' ← BEST' if auc == best_auc else ''
        print(f"  {name:>25} |{'█'*bar}{'░'*(40-bar)}| {auc:.4f}{marker}")

    # === Confusion prediction accuracy ===
    # For wrong samples: does direction predict the actual wrong class?
    wrong_mask = P != Y
    n_wrong = wrong_mask.sum()
    if n_wrong > 0:
        # Predicted confusion class = class with highest cosine to direction
        confusion_correct = 0
        for idx in np.where(wrong_mask)[0]:
            cosines = [(D[idx] * class_means_n[c]).sum() for c in range(n_cls)]
            dir_pred_class = np.argmax(cosines)
            if dir_pred_class == P[idx]:
                confusion_correct += 1

        conf_acc = confusion_correct / n_wrong * 100
        print(f"\n  Confusion class prediction accuracy: {conf_acc:.1f}% ({confusion_correct}/{n_wrong})")

    # === Per-class unified analysis ===
    print(f"\n  Per-class unified precognition:")
    print(f"  {'Class':>7} {'N':>5} {'Acc%':>6} {'mag_AUC':>8} {'dir_AUC':>8} {'uni_AUC':>8}")
    print(f"  {'-'*50}")
    for c in range(n_cls):
        mask = Y == c
        if mask.sum() < 10 or len(np.unique(correct[mask])) < 2:
            continue
        m_auc = roc_auc_score(correct[mask], M[mask])
        d_auc = roc_auc_score(correct[mask], dir_conf[mask])
        u_auc = roc_auc_score(correct[mask], unified[mask])
        acc_c = correct[mask].mean() * 100
        print(f"  {names[c]:>7} {mask.sum():>5} {acc_c:>6.1f} {m_auc:>8.3f} {d_auc:>8.3f} {u_auc:>8.3f}")

    return {
        'mag_auc': auc_mag,
        'dir_auc': auc_dir,
        'gap_auc': auc_gap,
        'unified_auc': auc_unified,
        'unified_v2_auc': auc_unified_v2,
        'lr_auc': auc_lr,
    }

if __name__ == '__main__':
    all_results = {}
    for ds in ['mnist', 'fashion', 'cifar']:
        try:
            all_results[ds] = run_experiment(ds)
        except Exception as e:
            print(f"  {ds} failed: {e}")
            import traceback; traceback.print_exc()

    print(f"\n{'='*70}")
    print(f"  UNIFIED PRECOGNITION CROSS-DATASET SUMMARY")
    print(f"{'='*70}")
    print(f"  {'Method':>25} {'MNIST':>7} {'Fashion':>7} {'CIFAR':>7} {'Mean':>7}")
    print(f"  {'-'*55}")

    methods = ['mag_auc', 'dir_auc', 'gap_auc', 'unified_auc', 'unified_v2_auc', 'lr_auc']
    labels = ['Magnitude (H-CX-58)', 'Dir conf (H-CX-59)', 'Dir gap', 'mag*conf', 'mag*gap', 'LR(3feat)']

    for method, label in zip(methods, labels):
        vals = [all_results[ds].get(method, 0) for ds in ['mnist', 'fashion', 'cifar'] if ds in all_results]
        mean_v = np.mean(vals) if vals else 0
        print(f"  {label:>25}", end='')
        for ds in ['mnist', 'fashion', 'cifar']:
            if ds in all_results:
                print(f" {all_results[ds].get(method, 0):>7.4f}", end='')
            else:
                print(f" {'N/A':>7}", end='')
        print(f" {mean_v:>7.4f}")

    print(f"\n  Key question: Does unified > individual?")
    for ds in all_results:
        r = all_results[ds]
        best_ind = max(r['mag_auc'], r['dir_auc'])
        best_uni = max(r['unified_auc'], r['unified_v2_auc'], r['lr_auc'])
        print(f"  {ds:>10}: best_individual={best_ind:.4f}  best_unified={best_uni:.4f}  "
              f"gain={best_uni-best_ind:+.4f}  {'SYNERGY' if best_uni > best_ind else 'NO SYNERGY'}")