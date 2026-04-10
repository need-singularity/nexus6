#!/usr/bin/env python3
"""H-CX-64 + H-CX-69 verification: Topological precognition lens + Topological acceleration

H-CX-64: dH0/dep (decay rate) predicts precognition AUC
H-CX-69: H0_total ≈ a - b·ln(ep), b ≈ (1/3)·H0_total(0)
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from sklearn.metrics import roc_auc_score
from scipy.optimize import curve_fit
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


def run_experiment(dataset_name='mnist', epochs=15):
    dim, tl, te, names = load_data(dataset_name)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()

    print(f"\n{'='*70}")
    print(f"  H-CX-64 + H-CX-69: Topo Dynamics — {dataset_name.upper()}")
    print(f"{'='*70}")

    epochs_list, h0_totals, t_scales, precog_aucs, accs = [], [], [], [], []

    for ep in range(epochs):
        model.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()

        model.eval()
        dirs_list, ys, tensions, corrects = [], [], [], []
        with torch.no_grad():
            for x, y in te:
                x_flat = x.view(-1, dim)
                a = model.engine_a(x_flat); g = model.engine_g(x_flat)
                rep = a - g
                mag = torch.sqrt((rep**2).mean(-1))
                d = F.normalize(rep, dim=-1)
                out = model.tension_scale * mag.unsqueeze(-1) * d
                pred = out.argmax(1)
                dirs_list.append(d.numpy())
                ys.extend(y.numpy().tolist())
                tensions.extend(mag.numpy().tolist())
                corrects.extend((pred == y).numpy().tolist())

        D = np.concatenate(dirs_list); Y = np.array(ys)
        T = np.array(tensions); C = np.array(corrects, dtype=float)
        acc = C.mean() * 100
        auc = roc_auc_score(C, T) if len(np.unique(C)) > 1 else 0.5
        h0t = compute_h0_total(D, Y)
        ts = model.tension_scale.item()

        epochs_list.append(ep + 1)
        h0_totals.append(h0t)
        t_scales.append(ts)
        precog_aucs.append(auc)
        accs.append(acc)

        if (ep+1) % 3 == 0 or ep == 0:
            print(f"  Ep {ep+1:>2}: acc={acc:.1f}%  AUC={auc:.4f}  H0={h0t:.4f}  ts={ts:.4f}")

    ep_arr = np.array(epochs_list, dtype=float)
    h0_arr = np.array(h0_totals)
    ts_arr = np.array(t_scales)
    auc_arr = np.array(precog_aucs)

    # === H-CX-64: dH0/dep vs AUC ===
    print(f"\n  === H-CX-64: dH0/dep vs Precog AUC ===")

    # Linear slope of H0_total
    slope_h0 = np.polyfit(ep_arr, h0_arr, 1)[0]
    slope_ts = np.polyfit(ep_arr, ts_arr, 1)[0]
    print(f"  H0_total slope (dH0/dep): {slope_h0:.6f}")
    print(f"  tension_scale slope:       {slope_ts:.6f}")

    # Composite: dH0/dep × tension_scale_final
    composite = abs(slope_h0) * ts_arr[-1]
    print(f"  Composite (|dH0/dep| × ts_final): {composite:.6f}")

    # Epoch-level correlations
    r_h0_auc = np.corrcoef(h0_arr, auc_arr)[0, 1]
    r_ts_auc = np.corrcoef(ts_arr, auc_arr)[0, 1]
    product = h0_arr * ts_arr
    r_prod_auc = np.corrcoef(product, auc_arr)[0, 1] if np.std(product) > 1e-10 else 0
    print(f"  Corr(H0_total, AUC):        {r_h0_auc:>7.4f}")
    print(f"  Corr(tension_scale, AUC):   {r_ts_auc:>7.4f}")
    print(f"  Corr(H0*ts, AUC):           {r_prod_auc:>7.4f}")

    # === H-CX-69: H0_total = a - b*ln(ep) ===
    print(f"\n  === H-CX-69: H0_total logarithmic fit ===")

    def log_model(x, a, b):
        return a - b * np.log(x)

    try:
        popt, _ = curve_fit(log_model, ep_arr, h0_arr, p0=[h0_arr[0], 0.1])
        a_fit, b_fit = popt
        h0_pred = log_model(ep_arr, *popt)
        ss_res = np.sum((h0_arr - h0_pred) ** 2)
        ss_tot = np.sum((h0_arr - h0_arr.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        print(f"  Fit: H0_total = {a_fit:.4f} - {b_fit:.4f} * ln(ep)")
        print(f"  R² = {r2:.4f}")
        print(f"  b / H0_total(1) = {b_fit / h0_arr[0]:.4f}  (H-CX-69 predicts ~1/3 = 0.333)")
        ratio_13 = b_fit / h0_arr[0]
        print(f"  Delta from 1/3: {abs(ratio_13 - 1/3):.4f}")

        # Also fit tension_scale
        popt_ts, _ = curve_fit(log_model, ep_arr, -ts_arr, p0=[-ts_arr[0], 0.1])
        # ts = c + d*ln(ep)
        def log_grow(x, c, d):
            return c + d * np.log(x)
        popt_ts2, _ = curve_fit(log_grow, ep_arr, ts_arr, p0=[ts_arr[0], 0.1])
        ts_pred = log_grow(ep_arr, *popt_ts2)
        ss_res_ts = np.sum((ts_arr - ts_pred) ** 2)
        ss_tot_ts = np.sum((ts_arr - ts_arr.mean()) ** 2)
        r2_ts = 1 - ss_res_ts / ss_tot_ts if ss_tot_ts > 0 else 0
        print(f"\n  tension_scale fit: ts = {popt_ts2[0]:.4f} + {popt_ts2[1]:.4f} * ln(ep)")
        print(f"  R² = {r2_ts:.4f}")
        print(f"  d / ts(1) = {popt_ts2[1] / ts_arr[0]:.4f}  (H320 predicts ~1/3)")

    except Exception as e:
        print(f"  Fit failed: {e}")
        r2 = 0; ratio_13 = 0

    # Product conservation: ts * H0_total ≈ const?
    product = ts_arr * h0_arr
    prod_cv = np.std(product) / np.mean(product) if np.mean(product) > 0 else 999
    print(f"\n  ts × H0_total conservation:")
    print(f"  {'Epoch':>5} {'ts':>8} {'H0':>8} {'product':>8}")
    print(f"  {'-'*32}")
    for i in range(0, len(ep_arr), 3):
        print(f"  {int(ep_arr[i]):>5} {ts_arr[i]:>8.4f} {h0_arr[i]:>8.4f} {product[i]:>8.4f}")
    print(f"  Product CV: {prod_cv:.4f} ({'CONSERVED' if prod_cv < 0.1 else 'WEAK' if prod_cv < 0.2 else 'NOT CONSERVED'})")

    # ASCII trajectory
    print(f"\n  H0_total + log fit:")
    max_h0 = max(h0_arr)
    for i, (ep, h0) in enumerate(zip(ep_arr, h0_arr)):
        bar = int(h0 / max_h0 * 40)
        fit_val = log_model(ep, a_fit, b_fit) if r2 > 0 else 0
        fit_bar = int(fit_val / max_h0 * 40) if r2 > 0 else 0
        print(f"  ep{int(ep):>2} |{'█'*bar}{'░'*(40-bar)}| {h0:.4f}  fit={fit_val:.4f}")

    return {
        'slope_h0': slope_h0,
        'r2_log': r2,
        'ratio_13': ratio_13 if r2 > 0 else 0,
        'prod_cv': prod_cv,
        'r_h0_auc': r_h0_auc,
        'final_auc': auc_arr[-1],
        'final_ts': ts_arr[-1],
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
    print(f"  {'Dataset':>10} {'dH0/dep':>8} {'R2_log':>7} {'b/H0(1)':>8} {'prod_CV':>8} {'r(H0,AUC)':>10}")
    print(f"  {'-'*55}")
    for ds, r in results.items():
        print(f"  {ds:>10} {r['slope_h0']:>8.5f} {r['r2_log']:>7.4f} {r['ratio_13']:>8.4f} "
              f"{r['prod_cv']:>8.4f} {r['r_h0_auc']:>10.4f}")

    print(f"\n  H-CX-64: dH0/dep predicts AUC? ", end='')
    slopes = [abs(r['slope_h0']) for r in results.values()]
    aucs = [r['final_auc'] for r in results.values()]
    r_cross = np.corrcoef(slopes, aucs)[0, 1]
    print(f"cross-dataset r={r_cross:.4f} {'SUPPORTED' if r_cross > 0.5 else 'REJECTED'}")

    print(f"  H-CX-69: H0 = a - b*ln(ep)?  ", end='')
    r2s = [r['r2_log'] for r in results.values()]
    print(f"mean R²={np.mean(r2s):.4f} {'SUPPORTED' if np.mean(r2s) > 0.9 else 'PARTIAL' if np.mean(r2s) > 0.7 else 'REJECTED'}")

    print(f"  H-CX-69: b/H0(1) ≈ 1/3?     ", end='')
    ratios = [r['ratio_13'] for r in results.values()]
    print(f"mean={np.mean(ratios):.4f} delta={abs(np.mean(ratios)-1/3):.4f}")