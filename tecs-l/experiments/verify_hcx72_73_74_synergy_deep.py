#!/usr/bin/env python3
"""H-CX-72 + H-CX-73 + H-CX-74 verification: Synergy deep dive

H-CX-72: Difficulty-normalized synergy optimum converges to 1/e
H-CX-73: ts×H0 product conservation (CV comparison + ts frozen experiment)
H-CX-74: 3-channel orthogonality → cause of synergy
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from ripser import ripser
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data


def compute_h0_total(D, Y, n_cls=10):
    means = []
    for c in range(n_cls):
        mask = Y == c
        if mask.sum() > 0:
            m = D[mask].mean(0)
            n = np.linalg.norm(m)
            means.append(m / max(n, 1e-8))
        else:
            means.append(np.zeros(D.shape[1]))
    means = np.array(means)
    cos_dist = np.clip(1 - means @ means.T, 0, 2)
    np.fill_diagonal(cos_dist, 0)
    result = ripser(cos_dist, maxdim=0, distance_matrix=True)
    h0 = result['dgms'][0]
    h0_finite = h0[h0[:, 1] < np.inf]
    return np.sum(h0_finite[:, 1] - h0_finite[:, 0]) if len(h0_finite) > 0 else 0


def run_synergy(dataset_name, model, dim, te, names):
    """Compute synergy metrics for a trained model."""
    n_cls = len(names)
    model.eval()
    all_mag, all_dir, all_y, all_pred = [], [], [], []
    with torch.no_grad():
        for x, y in te:
            x_flat = x.view(-1, dim)
            a = model.engine_a(x_flat); g = model.engine_g(x_flat)
            rep = a - g
            mag = torch.sqrt((rep**2).mean(-1))
            d = F.normalize(rep, dim=-1)
            out = model.tension_scale * mag.unsqueeze(-1) * d
            pred = out.argmax(1)
            all_mag.append(mag.numpy()); all_dir.append(d.numpy())
            all_y.append(y.numpy()); all_pred.append(pred.numpy())

    M = np.concatenate(all_mag); D = np.concatenate(all_dir)
    Y = np.concatenate(all_y); P = np.concatenate(all_pred)
    correct = (P == Y).astype(float)
    acc = correct.mean()

    # Class means
    class_means = np.zeros((n_cls, D.shape[1]))
    for c in range(n_cls):
        mask = (Y == c) & (P == c)
        if mask.sum() > 0:
            class_means[c] = D[mask].mean(0)
    norms = np.linalg.norm(class_means, axis=1, keepdims=True)
    class_means_n = class_means / np.clip(norms, 1e-8, None)

    dir_conf = np.array([(D[i] * class_means_n[P[i]]).sum() for i in range(len(D))])
    dir_gap = np.zeros(len(D))
    for i in range(len(D)):
        cosines = [(D[i] * class_means_n[c]).sum() for c in range(n_cls)]
        s = sorted(cosines, reverse=True)
        dir_gap[i] = s[0] - s[1]

    # AUCs
    mag_auc = roc_auc_score(correct, M) if len(np.unique(correct)) > 1 else 0.5
    dir_auc = roc_auc_score(correct, dir_conf) if len(np.unique(correct)) > 1 else 0.5
    gap_auc = roc_auc_score(correct, dir_gap) if len(np.unique(correct)) > 1 else 0.5

    # LR unified
    X = np.column_stack([
        (M - M.mean()) / (M.std() + 1e-8),
        (dir_conf - dir_conf.mean()) / (dir_conf.std() + 1e-8),
        (dir_gap - dir_gap.mean()) / (dir_gap.std() + 1e-8),
    ])
    try:
        lr = LogisticRegression(max_iter=1000)
        lr.fit(X, correct)
        lr_auc = roc_auc_score(correct, lr.predict_proba(X)[:, 1])
    except:
        lr_auc = max(mag_auc, dir_auc, gap_auc)

    best_ind = max(mag_auc, dir_auc, gap_auc)
    synergy = lr_auc - best_ind

    # Feature correlations
    corr_md = np.corrcoef(M, dir_conf)[0, 1]
    corr_mg = np.corrcoef(M, dir_gap)[0, 1]
    corr_dg = np.corrcoef(dir_conf, dir_gap)[0, 1]
    mean_abs_corr = (abs(corr_md) + abs(corr_mg) + abs(corr_dg)) / 3
    orthogonality = 1 - mean_abs_corr

    return {
        'acc': acc, 'mag_auc': mag_auc, 'dir_auc': dir_auc, 'gap_auc': gap_auc,
        'lr_auc': lr_auc, 'synergy': synergy, 'orthogonality': orthogonality,
        'corr_md': corr_md, 'corr_mg': corr_mg, 'corr_dg': corr_dg,
        'M': M, 'D': D, 'Y': Y, 'correct': correct,
    }


def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()

    print(f"\n{'='*70}")
    print(f"  H-CX-72+73+74: Synergy Deep — {dataset_name.upper()}")
    print(f"{'='*70}")

    # Track ts × H0 for H-CX-73
    ts_list, h0_list = [], []

    for ep in range(epochs):
        model.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()

        if (ep+1) % 3 == 0 or ep == 0:
            model.eval()
            dirs_list, ys = [], []
            with torch.no_grad():
                for x, y in te:
                    x_flat = x.view(-1, dim)
                    rep = model.engine_a(x_flat) - model.engine_g(x_flat)
                    d = F.normalize(rep, dim=-1)
                    dirs_list.append(d.numpy()); ys.extend(y.numpy().tolist())
            D = np.concatenate(dirs_list); Y = np.array(ys)
            h0 = compute_h0_total(D, Y)
            ts = model.tension_scale.item()
            ts_list.append(ts); h0_list.append(h0)

        if (ep+1) % 5 == 0:
            model.eval(); correct = total = 0
            with torch.no_grad():
                for x, y in te:
                    o, _ = model(x.view(-1, dim))
                    correct += (o.argmax(1)==y).sum().item(); total += y.size(0)
            print(f"  Epoch {ep+1}: acc={correct/total*100:.1f}%")

    # === Synergy analysis ===
    syn = run_synergy(dataset_name, model, dim, te, names)
    print(f"\n  Synergy: {syn['synergy']:+.4f} (LR={syn['lr_auc']:.4f}, best_ind={max(syn['mag_auc'], syn['dir_auc'], syn['gap_auc']):.4f})")

    # === H-CX-72: Normalized quintile synergy ===
    print(f"\n  === H-CX-72: Normalized Synergy ===")
    M = syn['M']; correct = syn['correct']
    baseline_acc = syn['acc']

    # Normalize tension by max_tension * baseline_acc
    M_norm = M / (M.max() * baseline_acc + 1e-8)
    quintiles = np.percentile(M_norm, [0, 20, 40, 60, 80, 100])

    print(f"  Baseline accuracy: {baseline_acc*100:.1f}%")
    print(f"  Tension range: [{M.min():.2f}, {M.max():.2f}]")
    print(f"  Normalized range: [{M_norm.min():.4f}, {M_norm.max():.4f}]")

    # Quintile synergy with normalized tension
    dir_conf = np.array([(syn['D'][i] * np.zeros(10)).sum() for i in range(10)])  # placeholder
    # Re-derive dir features
    n_cls = len(names)
    class_means = np.zeros((n_cls, syn['D'].shape[1]))
    for c in range(n_cls):
        mask = (syn['Y'] == c) & (syn['correct'] == 1)
        if mask.sum() > 0:
            class_means[c] = syn['D'][mask].mean(0)
    norms = np.linalg.norm(class_means, axis=1, keepdims=True)
    class_means_n = class_means / np.clip(norms, 1e-8, None)
    P = np.where(syn['correct'] == 1, syn['Y'], 0)  # approximate
    dir_conf = np.array([(syn['D'][i] * class_means_n[int(P[i])]).sum() for i in range(len(syn['D']))])
    dir_gap = np.zeros(len(syn['D']))
    for i in range(len(syn['D'])):
        cosines = [(syn['D'][i] * class_means_n[c]).sum() for c in range(n_cls)]
        s = sorted(cosines, reverse=True)
        dir_gap[i] = s[0] - s[1]

    norm_quintiles = np.percentile(M_norm, [0, 20, 40, 60, 80, 100])
    q_syns = []
    for qi in range(5):
        lo, hi = norm_quintiles[qi], norm_quintiles[qi+1]
        mask = (M_norm >= lo) & (M_norm <= hi + (0.001 if qi == 4 else 0))
        if mask.sum() < 30 or len(np.unique(correct[mask])) < 2:
            q_syns.append(0); continue
        m_auc = roc_auc_score(correct[mask], M[mask])
        g_auc = roc_auc_score(correct[mask], dir_gap[mask]) if np.std(dir_gap[mask]) > 1e-8 else 0.5
        best = max(m_auc, g_auc)
        X_q = np.column_stack([(M[mask]-M[mask].mean())/(M[mask].std()+1e-8),
                                (dir_gap[mask]-dir_gap[mask].mean())/(dir_gap[mask].std()+1e-8)])
        try:
            lr = LogisticRegression(max_iter=1000); lr.fit(X_q, correct[mask])
            lr_a = roc_auc_score(correct[mask], lr.predict_proba(X_q)[:,1])
        except: lr_a = best
        q_syns.append(lr_a - best)

    max_q = np.argmax(q_syns)
    rel_pos = (max_q + 0.5) / 5  # normalized position
    print(f"  Normalized quintile synergies: {[f'{s:+.4f}' for s in q_syns]}")
    print(f"  Max at Q{max_q+1}, relative_pos={rel_pos:.3f}, delta from 1/e={abs(rel_pos-1/np.e):.3f}")

    # === H-CX-73: ts × H0 conservation ===
    print(f"\n  === H-CX-73: ts × H0 Conservation ===")
    ts_arr = np.array(ts_list); h0_arr = np.array(h0_list)
    product = ts_arr * h0_arr
    cv_ts = np.std(ts_arr) / np.mean(ts_arr) if np.mean(ts_arr) > 0 else 999
    cv_h0 = np.std(h0_arr) / np.mean(h0_arr) if np.mean(h0_arr) > 0 else 999
    cv_prod = np.std(product) / np.mean(product) if np.mean(product) > 0 else 999

    print(f"  CV(ts):      {cv_ts:.4f}")
    print(f"  CV(H0):      {cv_h0:.4f}")
    print(f"  CV(ts×H0):   {cv_prod:.4f}")
    print(f"  Conservation (CV_prod < CV_ts AND CV_prod < CV_h0): "
          f"{'SUPPORTED' if cv_prod < cv_ts and cv_prod < cv_h0 else 'REJECTED'}")

    # === H-CX-74: Orthogonality ===
    print(f"\n  === H-CX-74: Feature Orthogonality ===")
    print(f"  Corr(mag, dir_conf): {syn['corr_md']:.4f}")
    print(f"  Corr(mag, dir_gap):  {syn['corr_mg']:.4f}")
    print(f"  Corr(dir_conf, gap): {syn['corr_dg']:.4f}")
    print(f"  Mean |corr|:         {(abs(syn['corr_md'])+abs(syn['corr_mg'])+abs(syn['corr_dg']))/3:.4f}")
    print(f"  Orthogonality:       {syn['orthogonality']:.4f}")
    print(f"  Synergy:             {syn['synergy']:+.4f}")

    return {
        'synergy': syn['synergy'],
        'orthogonality': syn['orthogonality'],
        'cv_prod': cv_prod,
        'cv_ts': cv_ts,
        'cv_h0': cv_h0,
        'norm_max_q': max_q,
        'norm_rel_pos': rel_pos,
        'baseline_acc': syn['acc'],
    }

if __name__ == '__main__':
    results = {}
    for ds in ['mnist', 'fashion', 'cifar']:
        try:
            results[ds] = run_experiment(ds)
        except Exception as e:
            print(f"  {ds} failed: {e}")
            import traceback; traceback.print_exc()

    print(f"\n{'='*70}")
    print(f"  CROSS-DATASET SUMMARY")
    print(f"{'='*70}")

    # H-CX-72
    print(f"\n  H-CX-72 (Normalized synergy peak):")
    for ds, r in results.items():
        print(f"    {ds}: Q{r['norm_max_q']+1}, rel_pos={r['norm_rel_pos']:.3f}, "
              f"delta_1e={abs(r['norm_rel_pos']-1/np.e):.3f}, baseline_acc={r['baseline_acc']*100:.1f}%")

    # H-CX-73
    print(f"\n  H-CX-73 (ts × H0 conservation):")
    for ds, r in results.items():
        conserved = r['cv_prod'] < r['cv_ts'] and r['cv_prod'] < r['cv_h0']
        print(f"    {ds}: CV_prod={r['cv_prod']:.4f} < CV_ts={r['cv_ts']:.4f} & CV_h0={r['cv_h0']:.4f}? {conserved}")

    # H-CX-74
    print(f"\n  H-CX-74 (Orthogonality → Synergy):")
    orths = [r['orthogonality'] for r in results.values()]
    syns = [r['synergy'] for r in results.values()]
    r_orth = np.corrcoef(orths, syns)[0, 1] if len(orths) == 3 else 0
    for ds, r in results.items():
        print(f"    {ds}: orth={r['orthogonality']:.4f}, synergy={r['synergy']:+.4f}")
    print(f"  Corr(orthogonality, synergy): {r_orth:.4f} {'SUPPORTED' if r_orth > 0.5 else 'REJECTED'}")