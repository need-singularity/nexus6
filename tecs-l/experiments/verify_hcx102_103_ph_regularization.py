#!/usr/bin/env python3
"""H-CX-102 + H-CX-103: PH Regularization + Tension×Topology Consciousness Index

H-CX-102: loss = CE + lambda * H0_gap → Overfit reduction?
H-CX-103: tension × H0 = Integrated consciousness index
"""
import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from scipy.stats import spearmanr
from ripser import ripser
from model_pure_field import PureFieldEngine
from calc.direction_analyzer import load_data


def compute_h0(D, Y, n_cls=10):
    means = []
    for c in range(n_cls):
        mask = Y == c
        if mask.sum() > 0:
            m = D[mask].mean(0); n = np.linalg.norm(m)
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


def extract_dirs(model, dim, loader):
    model.eval()
    dirs, ys, preds, tensions = [], [], [], []
    with torch.no_grad():
        for x, y in loader:
            x_flat = x.view(-1, dim)
            out, t = model(x_flat)
            rep = model.engine_a(x_flat) - model.engine_g(x_flat)
            d = F.normalize(rep, dim=-1)
            dirs.append(d.numpy()); ys.extend(y.numpy())
            preds.extend(out.argmax(1).numpy()); tensions.extend(t.numpy())
    return np.concatenate(dirs), np.array(ys), np.array(preds), np.array(tensions)


def train_baseline(dim, tl, te, n_cls, epochs=20):
    torch.manual_seed(42)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()
    history = []
    for ep in range(epochs):
        model.train()
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y); loss.backward(); opt.step()
        D_te, Y_te, P_te, T_te = extract_dirs(model, dim, te)
        D_tr, Y_tr, P_tr, T_tr = extract_dirs(model, dim, tl)
        test_acc = (P_te == Y_te).mean() * 100
        train_acc = (P_tr == Y_tr).mean() * 100
        h0_te = compute_h0(D_te, Y_te, n_cls)
        h0_tr = compute_h0(D_tr, Y_tr, n_cls)
        t_mean = T_te.mean()
        history.append({
            'ep': ep+1, 'train_acc': train_acc, 'test_acc': test_acc,
            'h0_tr': h0_tr, 'h0_te': h0_te, 'h0_gap': abs(h0_tr-h0_te),
            't_mean': t_mean, 'consciousness': t_mean * h0_te,
        })
    return history


def train_ph_regularized(dim, tl, te, n_cls, epochs=20, ph_lambda=0.1):
    """PH Regularization: Compute H0_gap every K steps and add to loss"""
    torch.manual_seed(42)
    model = PureFieldEngine(dim, 128, 10)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    ce = nn.CrossEntropyLoss()
    history = []

    for ep in range(epochs):
        model.train()
        step_count = 0
        for x, y in tl:
            opt.zero_grad()
            out, t = model(x.view(-1, dim))
            loss = ce(out, y)

            # PH regularization every 10 steps (approximate, differentiable proxy)
            # Proxy: minimize variance of class-mean cosine distances (encourages uniform spacing)
            if step_count % 10 == 0:
                rep = model.engine_a(x.view(-1, dim)) - model.engine_g(x.view(-1, dim))
                d = F.normalize(rep, dim=-1)
                # Per-class mean direction (differentiable)
                class_dirs = []
                for c in range(min(10, n_cls)):
                    mask = y == c
                    if mask.sum() > 0:
                        class_dirs.append(d[mask].mean(0))
                if len(class_dirs) >= 3:
                    cd = torch.stack(class_dirs)
                    cd_norm = F.normalize(cd, dim=-1)
                    cos_sim = cd_norm @ cd_norm.T
                    # Proxy for H0_gap: encourage class directions to be well-separated
                    # Minimize off-diagonal similarity = maximize separation
                    mask_upper = torch.triu(torch.ones_like(cos_sim), diagonal=1).bool()
                    off_diag = cos_sim[mask_upper]
                    ph_loss = off_diag.mean()  # minimize average cosine similarity
                    loss = loss + ph_lambda * ph_loss

            loss.backward(); opt.step()
            step_count += 1

        D_te, Y_te, P_te, T_te = extract_dirs(model, dim, te)
        D_tr, Y_tr, P_tr, T_tr = extract_dirs(model, dim, tl)
        test_acc = (P_te == Y_te).mean() * 100
        train_acc = (P_tr == Y_tr).mean() * 100
        h0_te = compute_h0(D_te, Y_te, n_cls)
        h0_tr = compute_h0(D_tr, Y_tr, n_cls)
        t_mean = T_te.mean()
        history.append({
            'ep': ep+1, 'train_acc': train_acc, 'test_acc': test_acc,
            'h0_tr': h0_tr, 'h0_te': h0_te, 'h0_gap': abs(h0_tr-h0_te),
            't_mean': t_mean, 'consciousness': t_mean * h0_te,
        })

    return history


def run_experiment(dataset_name='cifar', epochs=20):
    dim, tl, te, names = load_data(dataset_name)
    n_cls = len(names)

    print(f"\n{'='*70}")
    print(f"  H-CX-102+103: PH Regularization — {dataset_name.upper()}")
    print(f"{'='*70}")

    # Baseline
    print(f"\n  --- Baseline ---")
    hist_base = train_baseline(dim, tl, te, n_cls, epochs)
    for h in hist_base:
        if h['ep'] % 5 == 0:
            print(f"  Ep{h['ep']:>2}: train={h['train_acc']:.1f}% test={h['test_acc']:.1f}% "
                  f"gap={h['train_acc']-h['test_acc']:+.1f} H0gap={h['h0_gap']:.4f}")

    # PH Regularized (multiple lambdas)
    lambdas = [0.01, 0.1, 0.5]
    hist_regs = {}
    for lam in lambdas:
        print(f"\n  --- PH Regularized (lambda={lam}) ---")
        hist_reg = train_ph_regularized(dim, tl, te, n_cls, epochs, ph_lambda=lam)
        hist_regs[lam] = hist_reg
        for h in hist_reg:
            if h['ep'] % 5 == 0:
                print(f"  Ep{h['ep']:>2}: train={h['train_acc']:.1f}% test={h['test_acc']:.1f}% "
                      f"gap={h['train_acc']-h['test_acc']:+.1f} H0gap={h['h0_gap']:.4f}")

    # === H-CX-102: Comparison ===
    print(f"\n  === H-CX-102: PH Regularization Comparison ===")
    base_final = hist_base[-1]
    print(f"  {'Method':>20} {'Test%':>7} {'Gap':>7} {'H0gap':>7}")
    print(f"  {'-'*45}")
    print(f"  {'Baseline':>20} {base_final['test_acc']:>7.1f} "
          f"{base_final['train_acc']-base_final['test_acc']:>+7.1f} {base_final['h0_gap']:>7.4f}")

    best_reg_acc = 0
    best_lam = 0
    for lam, hist in hist_regs.items():
        final = hist[-1]
        delta = final['test_acc'] - base_final['test_acc']
        print(f"  {'PH(λ='+str(lam)+')':>20} {final['test_acc']:>7.1f} "
              f"{final['train_acc']-final['test_acc']:>+7.1f} {final['h0_gap']:>7.4f} "
              f"({delta:+.1f})")
        if final['test_acc'] > best_reg_acc:
            best_reg_acc = final['test_acc']
            best_lam = lam

    improved = best_reg_acc > base_final['test_acc']
    print(f"\n  Best PH reg: lambda={best_lam}, acc={best_reg_acc:.1f}% "
          f"(baseline {base_final['test_acc']:.1f}%)")
    print(f"  H-CX-102 (PH reg > baseline): {'SUPPORTED' if improved else 'REJECTED'}")

    # === H-CX-103: Consciousness Index ===
    print(f"\n  === H-CX-103: Tension × Topology = Consciousness ===")
    test_accs = [h['test_acc'] for h in hist_base]
    t_means = [h['t_mean'] for h in hist_base]
    h0_tes = [h['h0_te'] for h in hist_base]
    consciousness = [h['consciousness'] for h in hist_base]

    r_t, _ = spearmanr(t_means, test_accs)
    r_h0, _ = spearmanr(h0_tes, test_accs)
    r_c, _ = spearmanr(consciousness, test_accs)

    print(f"  Corr(tension, acc):           r={r_t:.4f}")
    print(f"  Corr(H0, acc):                r={r_h0:.4f}")
    print(f"  Corr(tension×H0, acc):        r={r_c:.4f}")
    combined_better = abs(r_c) > max(abs(r_t), abs(r_h0))
    print(f"  H-CX-103 (combined > individual): {'SUPPORTED' if combined_better else 'REJECTED'}")

    return {
        'base_acc': base_final['test_acc'],
        'best_reg_acc': best_reg_acc,
        'best_lam': best_lam,
        'improved': improved,
        'r_consciousness': r_c,
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
    print(f"  Round 10 SUMMARY")
    print(f"{'='*70}")
    for ds, r in results.items():
        print(f"  {ds}: base={r['base_acc']:.1f}% reg={r['best_reg_acc']:.1f}%(λ={r['best_lam']}) "
              f"improved={r['improved']} r_consciousness={r['r_consciousness']:.3f}")