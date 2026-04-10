#!/usr/bin/env python3
"""H-CX-59 Verification: Directional Precognition — Measure if wrong answer direction vectors point to confusion class"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data

def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()

    print(f"\n{'='*70}")
    print(f"  H-CX-59: Directional Precognition — {dataset_name.upper()}")
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

    # Extract directions
    model.eval()
    all_dir, all_mag, all_y, all_pred = [], [], [], []
    with torch.no_grad():
        for x, y in te:
            x_flat = x.view(-1, dim)
            a = model.engine_a(x_flat)
            g = model.engine_g(x_flat)
            rep = a - g
            mag = torch.sqrt((rep**2).mean(-1))
            d = F.normalize(rep, dim=-1)
            out = model.tension_scale * mag.unsqueeze(-1) * d
            all_dir.append(d.numpy()); all_mag.append(mag.numpy())
            all_y.append(y.numpy()); all_pred.append(out.argmax(1).numpy())

    D = np.concatenate(all_dir); M = np.concatenate(all_mag)
    Y = np.concatenate(all_y); P = np.concatenate(all_pred)

    # Compute class mean directions
    n_cls = len(names)
    class_means = np.zeros((n_cls, D.shape[1]))
    for c in range(n_cls):
        mask = (Y == c) & (P == c)  # correctly classified
        if mask.sum() > 0:
            class_means[c] = D[mask].mean(0)
    # Normalize
    norms = np.linalg.norm(class_means, axis=1, keepdims=True)
    class_means_n = class_means / np.clip(norms, 1e-8, None)

    # Analyze wrong predictions
    wrong_mask = P != Y
    n_wrong = wrong_mask.sum()
    print(f"\n  Total wrong: {n_wrong} / {len(Y)} ({n_wrong/len(Y)*100:.1f}%)")

    # For each wrong sample: does direction point to predicted class?
    dir_points_to_pred = 0
    dir_points_to_true = 0
    cos_to_pred_list = []
    cos_to_true_list = []
    confusion_pairs = {}

    for idx in np.where(wrong_mask)[0]:
        d = D[idx]
        true_c = Y[idx]
        pred_c = P[idx]

        # Cosine to true class mean
        cos_true = (d * class_means_n[true_c]).sum()
        cos_pred = (d * class_means_n[pred_c]).sum()
        cos_to_pred_list.append(cos_pred)
        cos_to_true_list.append(cos_true)

        if cos_pred > cos_true:
            dir_points_to_pred += 1
        else:
            dir_points_to_true += 1

        pair = (min(true_c, pred_c), max(true_c, pred_c))
        confusion_pairs[pair] = confusion_pairs.get(pair, 0) + 1

    pct_pred = dir_points_to_pred / n_wrong * 100 if n_wrong > 0 else 0
    pct_true = dir_points_to_true / n_wrong * 100 if n_wrong > 0 else 0

    print(f"\n  Direction points to PREDICTED class: {dir_points_to_pred} ({pct_pred:.1f}%)")
    print(f"  Direction points to TRUE class:      {dir_points_to_true} ({pct_true:.1f}%)")
    print(f"  Mean cos(dir, pred_class): {np.mean(cos_to_pred_list):.4f}")
    print(f"  Mean cos(dir, true_class): {np.mean(cos_to_true_list):.4f}")

    # H-CX-59 prediction: direction should point to predicted (wrong) class
    print(f"\n  H-CX-59 prediction (>50% points to pred): {'SUPPORTED' if pct_pred > 50 else 'REJECTED'}")

    # Top confusion pairs
    sorted_pairs = sorted(confusion_pairs.items(), key=lambda x: -x[1])
    print(f"\n  Top confusion pairs (direction-predicted):")
    print(f"  {'Pair':>15} {'Count':>7} {'%':>7}")
    print(f"  {'-'*30}")
    for (a, b), cnt in sorted_pairs[:10]:
        print(f"  {names[a]:>6}-{names[b]:<6} {cnt:>7} {cnt/n_wrong*100:>7.1f}")

    # Per-class direction accuracy
    print(f"\n  Per-class: direction → predicted class rate:")
    print(f"  {'Class':>7} {'N_wrong':>8} {'Dir→Pred%':>10} {'cos(pred)':>10} {'cos(true)':>10}")
    print(f"  {'-'*50}")
    for c in range(n_cls):
        w_mask = (Y == c) & wrong_mask
        if w_mask.sum() == 0:
            continue
        d_pred = 0
        cp_list, ct_list = [], []
        for idx in np.where(w_mask)[0]:
            d = D[idx]
            cos_t = (d * class_means_n[Y[idx]]).sum()
            cos_p = (d * class_means_n[P[idx]]).sum()
            cp_list.append(cos_p); ct_list.append(cos_t)
            if cos_p > cos_t: d_pred += 1
        pct = d_pred / w_mask.sum() * 100
        print(f"  {names[c]:>7} {w_mask.sum():>8} {pct:>10.1f} {np.mean(cp_list):>10.3f} {np.mean(ct_list):>10.3f}")

    # Gap analysis: cos(pred) - cos(true) correlates with confidence?
    gaps = np.array(cos_to_pred_list) - np.array(cos_to_true_list)
    wrong_mags = M[wrong_mask]
    if len(gaps) > 10:
        r = np.corrcoef(gaps, wrong_mags)[0, 1]
        print(f"\n  Corr(direction_gap, magnitude): {r:.4f}")
        print(f"  Larger gap = more confident wrong → {'YES' if r > 0 else 'NO'}")

    return pct_pred, np.mean(cos_to_pred_list), np.mean(cos_to_true_list)

if __name__ == '__main__':
    results = {}
    for ds in ['mnist', 'fashion', 'cifar']:
        try:
            pct, cp, ct = run_experiment(ds)
            results[ds] = (pct, cp, ct)
        except Exception as e:
            print(f"  {ds} failed: {e}")

    print(f"\n{'='*70}")
    print(f"  H-CX-59 SUMMARY")
    print(f"{'='*70}")
    print(f"  {'Dataset':>10} {'Dir→Pred%':>10} {'cos(pred)':>10} {'cos(true)':>10}")
    print(f"  {'-'*45}")
    for ds, (pct, cp, ct) in results.items():
        print(f"  {ds:>10} {pct:>10.1f} {cp:>10.4f} {ct:>10.4f}")